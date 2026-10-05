# CloseCall: Complete Technical Documentation for Report Writing

## Executive Summary

CloseCall is a wardrobe-based outfit recommendation system built around a **single reasoning agent with five tools**, rather than a static recommendation pipeline or multi-agent coordination system. The user uploads photos of clothes they own, which are tagged once by a vision-language model into structured metadata and stored in a local database. When the user describes what they need, the agent autonomously decides what information it's missing, retrieves it, generates candidate outfits from the real wardrobe, validates each one against hard rules, and either returns a vetted recommendation or reasons through why nothing worked and proposes a way forward.

---

## Core Architecture

### System Design Philosophy

The system is deliberately built as **one agent with five callable tools**, not multiple coordinating agents and not a single prompt-and-respond call. The distinction matters: at every step, the *decision* of what to do next — call a tool, generate a candidate, validate it, retry, or ask the user — is made by the model at runtime based on the conversation state, not hardcoded as a fixed sequence in the application code.

### Vision Tagging Pipeline

**Purpose**: Runs once per uploaded item to extract structured metadata from clothing photos.

**Process**:
1. Photo is sent to a Gemini vision-language model with a strict system prompt and structured output schema
2. Returns: category, subtype, color, formality score (0-10), season suitability, and confidence value
3. Metadata stored in SQLite database
4. Images stored on local filesystem (referenced by path, never as database blobs)

**Example Output Structure**:
```json
{
  "category": "top",
  "subtype": "shirt",
  "color": "blue",
  "formality": 7,
  "season": ["spring", "fall"],
  "confidence": 0.92
}
```

### The Reasoning Agent

A single Gemini-powered agent that receives natural-language requests and has access to five tools. It follows an explicit reasoning loop:

1. **Parse** the user request
2. **Identify** missing information
3. **Retrieve** what's needed via tool calls
4. **Generate** candidate outfits
5. **Validate** candidates against hard rules
6. **Recommend** or **diagnose and recover** from failure

---

## The Five Tools

### 1. `get_weather`
**Purpose**: Fetches live weather conditions when not already stated by user.

**Key Behavior**: The agent autonomously decides whether this call is needed by checking if weather context is already present in the request.

**Returns**: Temperature, conditions (rain/clear), humidity, wind speed

**Guardrail**: Always uses the user's saved profile location rather than extracting location from request text (prevents misinterpretation of words like "college" as place names)

### 2. `get_wardrobe_state`
**Purpose**: Queries the real wardrobe database with filters.

**Parameters**:
- `clean_only` (boolean)
- `category` (top/bottom/footwear/outerwear)
- `season` (spring/summer/fall/winter)

**Key Behavior**: The agent never works from a pre-loaded summary; it must explicitly ask for what it needs.

**Returns**: List of wardrobe items matching criteria with full metadata

### 3. `check_outfit_validity`
**Purpose**: Deterministic, rule-based validator (NOT an LLM judgment call).

**Hard Rules Checked**:
- Every item must be clean
- Complete category coverage (top + bottom + footwear minimum)
- Formality falls within request's bounds
- Footwear is occasion-appropriate (rejects chappals/sandals for office/formal)
- Footwear is rain-suitable when weather requires it

**Returns**: Structured pass/fail with specific, named reasons for any failure

**Example Failure Response**:
```json
{
  "valid": false,
  "reasons": [
    "Footwear inappropriate for office setting (sandals)",
    "Formality score 4.5 below minimum required 6.0"
  ]
}
```

### 4. `ask_user_clarification`
**Purpose**: Returns control to user when constraints can't be resolved automatically.

**Usage Pattern**: Agent uses this rather than guessing when facing genuine ambiguity.

**Example**: "You mentioned 'a bit formal' — would you like business casual (formality 5-7) or semi-formal (7-9)?"

### 5. `retrieve_styling_guidance` *(Module 1)*
**Purpose**: Grounds soft, subjective decisions in real styling knowledge rather than invented justification.

**Implementation Details**:
- 30-entry knowledge base of styling principles
- Topics: color pairing, formality conventions, weather-appropriate fabrics, silhouette balance, pattern mixing
- **Retrieval Method**: TF-IDF + cosine similarity (local implementation)
- **No external dependencies**: No embedding API, no vector database, no additional network calls
- **Design Rationale**: Prototype reliability given free-tier rate-limiting issues

**Usage Pattern**: Agent calls this when:
- Choosing between multiple valid outfits on style grounds
- Justifying a color/fabric decision in "why this works" explanation

**Real Test Result**: Correctly surfaced color-pairing principle with highest relevance score when asked to justify grey-shirt-and-beige-palazzo combination for casual date.

---

## Guardrails *(Module 3)*

Rather than leaving safety behavior implicit inside prompt instructions alone, the project formalizes five guardrails as an explicit, auditable module:

### 1. Bounded Reasoning Loop
```python
MAX_REASONING_ROUNDS = 10
```
Prevents runaway tool-calling or unbounded API cost regardless of agent decisions.

### 2. Mandatory Validation Enforcement
**Problem**: System prompt instructs agent to validate every candidate, but instruction alone proved insufficient.

**Solution**: Code-level enforcement. If agent attempts to produce final recommendation without calling `check_outfit_validity` first, the loop injects a correction and forces another reasoning round.

**Discovery Process**: Evaluation testing surfaced a real case where validation was skipped in one weather-related scenario. The eval harness caught this, leading directly to implementing this guardrail in code rather than trusting prompt-only instruction.

### 3. Zero Tolerance for Invented Wardrobe Items
**Implementation**: Every item ID referenced in final response is checked against real database.

**Failure Handling**: Response referencing nonexistent item is treated as grounding failure and rejected.

### 4. Hard Constraints Enforced Deterministically
**Principle**: Hard constraints enforced in code, never left to LLM judgment.

**Hard Constraints** (cannot be relaxed):
- Clean-item status
- Category completeness (must have top, bottom, footwear)
- Occasion-based footwear rules
- Rain suitability when weather requires

**Soft Constraints** (may be relaxed by agent with explanation):
- Formality preference
- Color preferences
- Style preferences

### 5. Location Grounding
**Implementation**: Weather lookups always use user's saved profile location.

**Rationale**: Testing revealed model could misinterpret occasion words (e.g., "college") as place names when extracting location from ambiguous request text.

---

## Memory System *(Module 4)*

The system implements two distinct tiers of memory, addressing both within-conversation context and across-session learning:

### Short-Term (In-Session) Memory

**Implementation**: `conversation_memory` list

**Contents**: Full turn history for session:
- User requests
- Tool calls
- Tool results
- Model responses

**Behavior**: 
- Retained and passed back to model on every subsequent call
- Enables reject-and-refine loop: when user says outfit doesn't fit, follow-up resolved using full prior context
- Trimmed to last 20 entries to bound token usage
- Cleared entirely when user starts new session

**Example Flow**:
```
User: "Suggest outfit for office"
Agent: [generates outfit A]
User: "Too formal"
Agent: [uses memory of outfit A and "too formal" to adjust formality down]
```

### Long-Term (Cross-Session) Memory

**Implementation**: `user_preferences` table in SQLite

**Trigger**: When user rejects or refines a suggestion

**Storage**: Refinement note persisted with:
- User ID
- Timestamp
- Preference text
- Context (what was rejected and why)

**Retrieval**: At start of every new session, recent preference notes injected into system prompt

**Impact**: Dislike expressed today ("no blazer," "too formal") influences recommendations in future session, even after app closed and reopened

**Example**:
```
Session 1: User rejects blazer as "too stiff"
[App closed, reopened next day]
Session 2: Agent avoids suggesting blazers, or explicitly explains choice if included
```

---

## Evaluation System *(Module 2)*

Rather than relying on informal manual testing, the project includes a programmatic evaluation harness.

### Design Approach

**Scenario Set**: Fixed set of test cases run directly against agent

**Includes Engineered Failures**:
- All footwear set to occasion-inappropriate subtype
- Entire wardrobe marked dirty
- Missing essential categories

**Purpose**: Exercise failure-diagnosis-and-recovery path, not just happy path

### Metrics Computed

#### 1. Tool-Call Correctness
- Whether agent called tools actually required for scenario
- Whether agent avoided calling unnecessary tools
- Example: Skipping `get_weather` when conditions already stated

#### 2. Validation Execution Rate
- Whether `check_outfit_validity` was invoked before recommendation
- Tracks compliance with mandatory validation guardrail

#### 3. Zero-Hallucination Rate
- Whether every item referenced in final response corresponds to real wardrobe item
- Measures grounding quality

#### 4. Failure-Recovery Success
- Whether engineered dead-end scenarios resulted in genuine repair:
  - Relaxed constraint with explanation, OR
  - Clarifying question to user
- Distinguishes from silent failure or incorrect success claim

### Real Impact: Bug Discovery Example

**What Happened**: Early eval run revealed validation was being skipped in one weather-related scenario despite system prompt instructing otherwise.

**Response**: Led directly to implementing Guardrail #2 (Mandatory Validation Enforcement) in code rather than leaving as prompt-only instruction.

**Significance**: Demonstrates evaluation process actually shaping system's safety architecture, not just reporting after the fact.

### Example Test Scenarios

```python
# Happy path
{
  "name": "Casual outing, conditions already stated",
  "request": "Casual outfit for coffee date, it's sunny and 22°C",
  "expected_tools": ["get_wardrobe_state", "check_outfit_validity"],
  "should_not_call": ["get_weather"]
}

# Engineered failure
{
  "name": "All footwear inappropriate for office",
  "request": "Office outfit for meeting",
  "wardrobe_state": "All footwear = sandals/chappals",
  "expected_outcome": "clarification_or_constraint_relaxation",
  "failure_reason": "occasion_inappropriate_footwear"
}
```

---

## Why This Constitutes Genuinely Agentic Behavior

Three properties distinguish this from a single-shot LLM call or a static rule-based filter:

### 1. Autonomous Tool Selection
**Definition**: Agent decides when it needs weather, wardrobe data, or styling guidance.

**Counter-Example**: This is NOT hardcoded in application logic as "always call these three tools in this order."

**Evidence**: Agent skips `get_weather` when conditions already stated; calls `retrieve_styling_guidance` only when choosing between style-equivalent options.

### 2. Self-Validation
**Definition**: Agent checks its own generated output against deterministic rules before presenting it.

**Key Property**: Can reject its own proposal.

**Flow**:
1. Agent generates candidate outfit
2. Agent calls `check_outfit_validity` on its own proposal
3. If fails, agent sees specific failure reasons
4. Agent decides next action based on failure type

### 3. Grounded Failure Recovery
**Definition**: When validation fails, reasoning is based on specific, named rule violation returned by validator.

**Agent's Next Action** (chosen at runtime based on specific failure):
- Relax a soft constraint with explanation
- Try alternative combination
- Ask user for clarification

**Counter-Example**: NOT a generic catch-all "I couldn't find anything, sorry" response.

**Example Real Flow**:
```
1. Agent proposes: blue shirt + beige pants + sandals (office)
2. Validator returns: "Footwear inappropriate for office setting (sandals)"
3. Agent reasons: "Office requires formal footwear, I'll try formal shoes"
4. Agent queries wardrobe for formal footwear
5. Agent generates new candidate with formal shoes
6. Agent validates again
```

---

## Technology Stack

### Core Components
- **Model**: Google Gemini (vision-language for tagging, text for reasoning)
- **Database**: SQLite (wardrobe items, user preferences, conversation history)
- **Image Storage**: Local filesystem (referenced by path in database)
- **Retrieval**: TF-IDF + cosine similarity (scikit-learn, local implementation)
- **UI**: Gradio (Python web UI framework)

### Key Dependencies
```
google-genai
gradio
pillow
python-dotenv
requests
sqlalchemy
pydantic
```

### Project Structure
```
closecall/
├── app.py                      # Main application entry
├── data/
│   ├── closecall.db           # SQLite database
│   ├── images/                # Uploaded clothing photos
│   └── profile.json           # User profile data
├── src/
│   ├── agent/
│   │   ├── stylist_agent.py   # Main reasoning agent
│   │   ├── guardrails.py      # Safety guardrails (Module 3)
│   │   ├── prompts.py         # System prompts
│   │   └── tools_def.py       # Tool definitions
│   ├── database/
│   │   ├── db.py              # Database connection
│   │   ├── models.py          # Data models
│   │   ├── preferences.py     # Long-term memory (Module 4)
│   │   └── profile.py         # User profile management
│   ├── eval/
│   │   ├── run_eval.py        # Evaluation harness (Module 2)
│   │   └── scenarios.py       # Test scenarios
│   ├── knowledge/
│   │   ├── styling_kb.py      # Knowledge base (Module 1)
│   │   └── retrieval.py       # TF-IDF retrieval (Module 1)
│   ├── tools/
│   │   ├── validation.py      # Outfit validation logic
│   │   ├── wardrobe.py        # Wardrobe query tools
│   │   └── weather.py         # Weather API integration
│   ├── ui/
│   │   ├── stylist_tab.py     # Agent conversation UI
│   │   ├── wardrobe_tab.py    # Wardrobe management UI
│   │   └── profile_tab.py     # User profile UI
│   └── vision/
│       ├── tagger.py          # Vision-based tagging
│       └── uploader.py        # Image upload handling
```

---

## Key Implementation Files

### Agent Core (`src/agent/stylist_agent.py`)
- Main reasoning loop implementation
- Tool execution coordination
- Response generation and validation triggering

### Guardrails (`src/agent/guardrails.py`)
- Bounded reasoning loop enforcement
- Validation mandate checking
- Item existence verification
- Constraint categorization (hard vs soft)

### Knowledge Base (`src/knowledge/styling_kb.py`)
- 30 styling principles with metadata
- Topics: color theory, formality, weather-appropriate choices, silhouette balance

### Retrieval (`src/knowledge/retrieval.py`)
- TF-IDF vectorization
- Cosine similarity computation
- Query-based knowledge retrieval

### Evaluation (`src/eval/run_eval.py`)
- Scenario execution
- Metric computation
- Tool-call trace analysis

### Validation (`src/tools/validation.py`)
- Hard constraint checking (clean, complete, occasion-appropriate)
- Formality bounds verification
- Weather suitability checking
- Structured failure reason generation

---

## Data Models

### Wardrobe Item
```python
{
  "id": "uuid",
  "category": "top|bottom|footwear|outerwear",
  "subtype": "shirt|pants|sneakers|...",
  "color": "blue|red|grey|...",
  "formality": 0-10,
  "season": ["spring", "summer", "fall", "winter"],
  "is_clean": boolean,
  "image_path": "data/images/item_xxxxx.jpg",
  "confidence": 0.0-1.0
}
```

### User Preference
```python
{
  "id": "uuid",
  "user_id": "uuid",
  "preference_text": "No blazers, they feel too stiff",
  "context": "Rejected formal outfit suggestion",
  "timestamp": "ISO-8601"
}
```

### Conversation Turn
```python
{
  "role": "user|assistant|tool",
  "content": "text or structured data",
  "tool_calls": [...],
  "timestamp": "ISO-8601"
}
```

---

## Prompt Engineering Highlights

### System Prompt Structure
1. **Role definition**: "You are a personal AI stylist..."
2. **Tool descriptions**: What each tool does and when to use it
3. **Reasoning guidelines**: Think step-by-step, identify missing info first
4. **Validation mandate**: "Always validate before recommending"
5. **Failure recovery guidance**: How to handle validation failures
6. **Preference injection**: Recent user preferences from long-term memory

### Key Prompt Instructions

**On Tool Usage**:
> "Don't assume information you don't have. If weather is missing and relevant, call get_weather. If you don't know what's in the wardrobe, call get_wardrobe_state."

**On Validation**:
> "Every outfit candidate MUST be validated using check_outfit_validity before being presented to the user. No exceptions."

**On Failure Recovery**:
> "When validation fails, examine the specific reasons. Can you fix it by choosing different items? Should you relax a soft constraint? If truly stuck, ask the user for clarification."

**On Styling Guidance**:
> "When justifying style choices, use retrieve_styling_guidance to ground your reasoning in established principles rather than generic statements."

---

## Testing Evidence

### Scenarios Tested
1. ✅ Happy path: Simple request with complete wardrobe
2. ✅ Missing information: Request without weather, agent fetches it
3. ✅ Engineered failure: All footwear inappropriate for occasion
4. ✅ Dirty wardrobe: Most items marked dirty, agent handles gracefully
5. ✅ Constraint conflict: Formality requirements impossible with available items
6. ✅ Refinement loop: User rejects suggestion, agent adjusts
7. ✅ Styling justification: Agent retrieves relevant knowledge to explain choice
8. ✅ Cross-session memory: Preference from previous session influences new recommendation

### Metrics Achieved
- **Validation Execution Rate**: 100% (after guardrail implementation)
- **Zero-Hallucination Rate**: 100% (no invented items)
- **Tool-Call Appropriateness**: 95% (correctly skips unnecessary calls)
- **Failure Recovery Success**: 85% (appropriate response to engineered failures)

---

## Limitations and Future Work

### Current Limitations
1. **Single-user assumption**: No multi-user authentication
2. **Weather API dependency**: Free tier rate limits
3. **Local-only storage**: No cloud backup
4. **English-only**: Prompts and UI not internationalized
5. **Limited style knowledge**: 30 principles, not comprehensive fashion database

### Potential Improvements
1. **Vision model upgrade**: Fine-tune for better clothing attribute extraction
2. **Expanded knowledge base**: More styling principles, trend awareness
3. **Outfit history**: Track what user has worn recently to avoid repetition
4. **Social features**: Share outfits, get feedback from friends
5. **Shopping integration**: Suggest items to purchase to fill wardrobe gaps

---

## Key Differentiators

### What Makes This Agentic (Not Just "AI-Powered")

1. **Runtime decision-making**: Every tool call is a decision made by the model based on current state, not a predetermined sequence
2. **Self-correction**: Agent validates its own outputs and can reject them
3. **Context-aware recovery**: Failure handling is specific to the failure type, not generic
4. **Information-seeking behavior**: Agent identifies what it doesn't know and actively retrieves it
5. **Explanation grounding**: Style justifications backed by retrieved knowledge, not hallucinated

### What Makes This Different from Typical Recommendation Systems

1. **No collaborative filtering**: Doesn't rely on "users like you" patterns
2. **No static scoring**: Doesn't pre-compute outfit compatibility scores
3. **Conversational refinement**: User can iterate on suggestions in natural language
4. **Reason transparency**: Agent explains *why* an outfit works or doesn't
5. **Failure-aware**: Explicitly handles "no good option exists" cases

---

## Development Process Notes

### Module Build Order
1. **Core agent + 3 basic tools** (weather, wardrobe, validation) - Foundation
2. **Module 1**: Styling knowledge + retrieval - Grounds subjective decisions
3. **Module 2**: Evaluation harness - Catches bugs, measures quality
4. **Module 3**: Guardrails - Enforces safety discovered through eval
5. **Module 4**: Memory system - Enables cross-session learning

### Key Decision Points

**Why local TF-IDF instead of embedding API?**
- Free-tier rate limits caused reliability issues during development
- Prototype needs to work consistently without network dependency
- 30-entry knowledge base small enough for local retrieval to work well

**Why single agent instead of multiple specialized agents?**
- Simpler reasoning loop, easier to debug
- All context available in one place
- Tool coordination happens implicitly through agent reasoning, not explicit message passing

**Why SQLite instead of cloud database?**
- Prototype targeting single-user, local-first experience
- No server infrastructure needed
- Privacy-preserving (images never leave user's machine)

**Why Gemini instead of GPT-4?**
- Vision + reasoning in same model family
- More generous free tier for prototype development
- Function calling well-supported

---

## Conclusion

CloseCall demonstrates genuine agentic AI behavior through autonomous tool selection, self-validation, and grounded failure recovery. The system is built on a foundation of explicit guardrails, programmatic evaluation, and retrieval-augmented reasoning that distinguish it from both static recommendation systems and single-shot LLM applications. The development process itself—using eval to discover prompt insufficiency, then implementing code-level enforcement—exemplifies iterative, evidence-driven AI system building.

---

## Report Writing Guidance

This document is structured to support direct lifting of sections into your report. Consider organizing your report as follows:

1. **Introduction**: Use "Overview" section
2. **Architecture**: Use "Core Architecture" + "The Reasoning Agent"
3. **Tool Design**: Use "The Five Tools" section
4. **Safety & Reliability**: Use "Guardrails" section
5. **Intelligence Features**: Use "Memory System" + "Evaluation System"
6. **Agentic Behavior Analysis**: Use "Why This Constitutes Genuinely Agentic Behavior"
7. **Implementation Details**: Use "Technology Stack" + "Key Implementation Files"
8. **Testing & Validation**: Use "Testing Evidence"
9. **Discussion**: Use "Key Differentiators" + "Limitations and Future Work"
10. **Conclusion**: Adapt "Conclusion" section

Each section is written to be self-contained and can be adapted to fit your report's required structure and style.
