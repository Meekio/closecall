# CloseCall — AI Personal Stylist
## Foundations of Agentic AI Mini Project

## Project Overview

**CloseCall** is an agentic AI personal stylist that recommends outfits from a user's own wardrobe.

The user uploads photos of their clothes, and the system automatically identifies and stores useful information about each item. The user can then make a natural-language request such as:

> "I need a casual outfit for office today and it's raining."

The agent understands the request, checks the user's wardrobe, fetches weather information when required, generates suitable outfit combinations, validates them against the user's constraints, and recommends 2–3 complete outfits with reasons.

The key focus of the project is **reasoning, tool use, validation, failure handling, and adaptation** rather than simply filtering clothes.

---

# 1. Problem

Deciding what to wear requires repeatedly considering:

- What clothes the user owns
- Which clothes are clean
- Weather conditions
- Occasion
- Formality
- Personal style
- User preferences

Existing wardrobe/fashion applications often focus on cataloging clothes or recommending clothes to buy. CloseCall instead focuses on **using the user's existing wardrobe intelligently**.

The main problem is therefore:

> **How can an AI system reason over a user's actual wardrobe and current context to recommend a practical outfit, validate the recommendation, and adapt when the recommendation does not work?**

---

# 2. Objective

Build a single-agent AI system that:

- Understands a user's wardrobe from uploaded images
- Extracts structured clothing information
- Accepts natural-language requests
- Understands occasion, mood, style, weather, and preferences
- Retrieves relevant wardrobe items
- Generates complete outfit combinations
- Validates its own suggestions
- Explains why an outfit was selected
- Handles situations where no perfect outfit exists
- Asks targeted clarification questions when required
- Adapts to user feedback within the same session

---

# 3. Core Features

### 3.1 Wardrobe Upload and Auto-Tagging

Users upload images of individual clothing items.

The vision model extracts:

- Category
- Subtype
- Color
- Formality
- Season
- Rain suitability
- Clean/dirty status
- Confidence

Example:

```text
Image → Gemini 3.7 Flash

Type: top
Subtype: t-shirt
Color: black
Formality: 2
Season: summer
Rain suitable: false
Status: clean
Confidence: 0.94
```

---

### 3.2 Natural-Language Requests

The user does not need to fill out multiple forms.

They can simply describe what they need:

> "I need something casual for office today and it's raining."

The agent extracts the relevant constraints:

```text
Occasion: Office
Style/Mood: Casual
Weather: Rainy
```

---

### 3.3 Automatic Weather Fetching

If the user does not provide weather information, the agent can decide that it needs weather data and call:

```text
get_weather()
```

The weather information is then used while generating and validating outfits.

---

### 3.4 Multiple Outfit Options

The agent generates **2–3 complete outfit options** rather than returning only one item or incomplete combinations.

Possible structure:

```text
Outfit 1:
T-shirt + Jeans + Sneakers + Jacket

Outfit 2:
Shirt + Trousers + Formal Shoes

Outfit 3:
Kurti + Palazzo + Flats
```

The exact combinations depend on the user's available wardrobe and request.

---

### 3.5 Self-Validation

Every candidate outfit is checked before it is shown to the user.

The validation considers:

- Occasion
- Weather
- Formality
- Clean/dirty status
- Required clothing categories
- Footwear compatibility
- Rain suitability

---

### 3.6 Failure Diagnosis and Repair

If no outfit satisfies all constraints, the agent should not simply return:

> "No outfit found."

Instead, it should identify the reason.

Example:

> "You don't currently have a fully formal outfit because your only clean formal shirt does not have a suitable formal bottom. I can suggest the closest smart-casual alternative."

The agent may:

1. Identify the failed constraint
2. Determine whether a soft constraint can be relaxed
3. Regenerate alternatives
4. Explain the trade-off
5. Ask the user a clarification question if necessary

---

### 3.7 Feedback Adaptation

If the user rejects an outfit, the rejection becomes part of the current session's constraints.

Example:

```text
Agent:
"Black shirt + jeans + sneakers"

User:
"I don't want to wear jeans."

Agent:
Updates constraint
↓
Queries wardrobe again
↓
Generates alternatives
```

The agent should not restart the entire interaction from scratch.

---

### 3.8 Manual Tag Correction

The user can correct incorrect vision tags and update:

- Item category
- Color
- Formality
- Clean/dirty status
- Other metadata where required

---

# 4. Wardrobe Data Model

Each wardrobe item should contain structured metadata.

Example:

```json
{
  "item_id": "item_001",
  "category": "top",
  "subtype": "t-shirt",
  "color": "black",
  "formality": 2,
  "season": ["summer", "all-season"],
  "rain_suitable": false,
  "status": "clean",
  "image_path": "..."
}
```

### Supported Categories

```text
top
bottom
one_piece
footwear
outerwear
```

### Supported Subtypes

```text
t-shirt
shirt
kurti
jeans
trousers
leggings
palazzo
sneakers
formal_shoes
flats
sandals
chappal
jacket
```

---

# 5. Vision Tagging

## Approach

Do **not** train a custom vision model for the prototype.

Use a pretrained **Gemini 3.7 Flash** with a carefully designed system prompt and structured output.

The vision pipeline runs **once per wardrobe upload** and stores the resulting metadata in the database.

### Vision Prompt

```text
You catalog clothing for a wardrobe app.

You see ONE photo of ONE item.

Return only JSON matching the provided schema.

Do not guess. If unsure, use "unknown" and set a low confidence.

Formality:
1 = loungewear
3 = smart casual
5 = formal.
```

### Important

Use Gemini's structured output / response schema so that the model is restricted to valid enum values instead of returning arbitrary text.

---

# 6. Agent Tools

The agent has access to the following tools.

## 6.1 get_weather()

Fetches current or forecast weather when weather information is missing or needs to be obtained.

```text
get_weather(location)
```

---

## 6.2 get_wardrobe_state()

Queries the wardrobe database for items matching the agent's requirements.

Possible filters:

- Clean items
- Category
- Season
- Formality
- Weather suitability
- User preferences

```text
get_wardrobe_state(user_id, filters)
```

---

## 6.3 check_outfit_validity()

Validates a candidate outfit against the current constraints.

Checks:

- Occasion
- Weather
- Formality
- Category completeness
- Footwear compatibility
- Rain suitability
- Clean/dirty status

```text
check_outfit_validity(outfit, constraints)
```

---

## 6.4 ask_user_clarification()

Used when the agent cannot resolve missing or conflicting constraints automatically.

Example:

> "You don't have formal footwear that is suitable for this request. Would you like me to suggest a smart-casual alternative?"

```text
ask_user_clarification(question)
```

---

# 7. Outfit Rules

The LLM should only propose outfits using **actual item IDs returned from the wardrobe database**.

It must not invent clothing items.

## Basic Outfit Templates

### Template 1

```text
top + bottom + footwear
```

### Template 2

```text
top + bottom + footwear + outerwear
```

### Template 3

```text
kurti + bottom + footwear
```

### Template 4

```text
one_piece + footwear
```

Outerwear is optional, but can become important when weather conditions require it and an appropriate item exists.

---

# 8. Footwear Rules

Footwear mismatches should be handled through hard validation rules rather than relying only on the LLM.

### Office / Formal

- Chappal → reject
- Sandals → reject for formal
- Sneakers → allowed for casual office
- Formal shoes → allowed for formal office

### Rain

Reject items where:

```text
rain_suitable = false
```

The footwear must also be compatible with the occasion.

### Example Failure Case

Suppose:

```text
Occasion = Office
Formality = Formal
Weather = Rain
Clean footwear = Chappal only
```

The candidate should fail validation.

The agent should diagnose:

> "No available footwear meets the current office/formality constraints."

It can then:

- Relax a soft constraint
- Suggest the closest alternative
- Ask the user whether a less formal option is acceptable

This is an intentional **failure-handling demonstration**.

---

# 9. Agentic Behaviour

The project is agentic because the LLM is responsible for deciding what actions are needed.

### The agent should be able to:

- Detect missing information
- Decide when weather information is required
- Select the appropriate tool
- Query the wardrobe based on the current request
- Generate candidate outfits
- Validate its own suggestions
- Diagnose why an outfit failed
- Repair the solution by changing soft constraints
- Ask for clarification when automatic resolution is not possible
- Incorporate user feedback and retry

### Not considered agentic

The following are supporting pipeline components:

- Vision tagging
- Database
- UI
- Image storage

The agentic behaviour comes from the **decision-making and tool-calling loop**.

---

# 10. Core Reasoning Algorithm

```text
INPUT:
    user request
    user_id

1. PARSE REQUEST
   Extract:
      occasion
      mood
      style
      weather
      preferences

   Separate:
      hard constraints
      soft constraints

2. FILL MISSING INFORMATION

   IF weather is not provided:
       call get_weather(location)

3. RETRIEVE WARDROBE

   call get_wardrobe_state(
       user_id,
       relevant filters
   )

   Prefer:
      clean items
      season-appropriate items
      items matching the required formality

4. GENERATE CANDIDATES

   Generate 2–3 complete outfit combinations
   using only wardrobe item IDs.

5. VALIDATE

   FOR each candidate:
       call check_outfit_validity()

6. IF VALID OUTFITS EXIST

   Rank candidates according to
   soft-constraint compatibility.

   Return:
      outfit
      explanation
      relevant context

7. IF ALL OUTFITS FAIL

   Diagnose the failure:

      missing category?
      unsuitable weather?
      all suitable items dirty?
      formality conflict?
      footwear conflict?

   IF a soft constraint can be relaxed:
       relax the constraint
       regenerate candidates
       explain the trade-off

   ELSE:
       call ask_user_clarification()

8. USER FEEDBACK

   IF the user rejects an outfit:
       update session constraints
       return to Step 3
       keep the existing session state
```

---

# 11. Recommendation Logic

The recommendation should not be based on a single fixed score alone.

First, **hard constraints** are used for validation.

Examples:

```text
Hard constraints:
- Required category must exist
- Item must be clean
- Formality must not violate the request
- Rain suitability must hold when required
- Footwear must be acceptable for the occasion
```

Then **soft constraints** can be used to rank valid candidates.

Examples:

```text
Soft constraints:
- Preferred color
- Preferred style
- Mood
- Color compatibility
- Personal preference
```

This allows the agent to reason about trade-offs instead of treating every preference as equally strict.

---

# 12. Example End-to-End Scenario

### User

> "I need a casual outfit for office today and it's raining."

### Agent

**Step 1 — Parse**

```text
Occasion: Office
Style: Casual
Weather: Rain
```

**Step 2 — Retrieve wardrobe**

The agent queries for:

```text
Clean
Office-compatible
Casual
Rain-suitable
```

**Step 3 — Generate**

```text
Candidate 1:
T-shirt + Jeans + Sneakers + Jacket

Candidate 2:
Shirt + Trousers + Sneakers + Jacket

Candidate 3:
Kurti + Pants + Flats + Jacket
```

**Step 4 — Validate**

Each candidate is checked against the constraints.

**Step 5 — Recommend**

The agent returns the valid options with reasons.

Example:

> **Option 1:** T-shirt + Jeans + Sneakers + Jacket  
> Suitable because it matches the casual requirement, remains appropriate for the office context, and the jacket provides better protection for rainy weather.

---

# 13. Failure Scenario

### User

> "Give me a formal office outfit for a rainy day."

Suppose the wardrobe contains:

```text
Formal shirt → clean
Formal trousers → dirty
Chappal → clean
Sneakers → clean
```

The agent should not simply say:

> "No outfit found."

Instead:

```text
Formal shirt
      +
Formal trousers
      ↓
Rejected — trousers are dirty

Formal shirt
      +
Sneakers
      ↓
Rejected — footwear does not satisfy formal requirement

Formal shirt
      +
Chappal
      ↓
Rejected — footwear incompatible with formal office
```

The agent diagnoses the problem and responds with a useful alternative or clarification.

---

# 14. Technology Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangChain |
| Reasoning LLM | Gemini 3.7 Flash |
| Vision tagging | Gemini 3.7 Flash |
| Tool calling | Gemini function calling / LangChain tools |
| Weather | OpenWeatherMap API |
| Database | SQLite / Supabase PostgreSQL |
| Image storage | Free-tier storage such as Supabase, Firebase, or Cloudinary |
| Frontend | Gradio |
| Backend | Gradio |
| Language | Python |

### Model Selection

**Primary model: `gemini-3.7-flash`**

Use Gemini 3.7 Flash for the complete prototype:

- Wardrobe image tagging
- Reasoning agent
- Function/tool calling
- Outfit generation
- Failure diagnosis and adaptation

Using one model keeps the prototype simple and avoids unnecessary model-switching complexity.

**Fallback:** If free-tier usage becomes a constraint during development, Gemini 3.5 Flash-Lite can be used for one-time wardrobe tagging while keeping Gemini 3.7 Flash for the reasoning agent.

Do not use Gemini 3.8 Flash for this prototype because the project prioritizes predictable free-tier availability over using the newest model.

### Prototype Principle

Keep the implementation simple and use free-tier services wherever possible.

The prototype should be a **mobile-accessible web application through Gradio**, rather than a native mobile application. Native mobile development can be treated as future work.

---

# 15. Data Flow

```text
User
 │
 ├── Upload wardrobe image
 │        │
 │        ▼
 │   Gemini 3.7 Flash
 │        │
 │        ▼
 │   Structured metadata
 │        │
 │        ▼
 │   Wardrobe Database
 │
 └── Natural-language request
          │
          ▼
    Reasoning Agent
          │
          ├── get_weather()
          │
          ├── get_wardrobe_state()
          │
          ├── Generate candidates
          │
          └── check_outfit_validity()
                    │
                    ▼
              Valid outfit?
               /       \
             Yes        No
              │          │
              ▼          ▼
        Recommend     Diagnose
                         │
                  ┌──────┴──────┐
                  ▼             ▼
               Repair        Ask user
                  │
                  └──────► Retry
```

---

# 16. Image Storage

Images should not be stored directly inside the metadata database.

Store:

```text
Database:
item metadata + image URL/path
```

Use a free-tier storage provider such as:

- Supabase Storage
- Firebase Storage
- Cloudinary

The prototype should avoid paid subscriptions.

---

# 17. RAG

RAG is **not required** for the prototype.

The wardrobe is structured data:

```text
category
color
formality
season
status
rain_suitable
```

Retrieving wardrobe items is therefore a **database query**, not document retrieval.

Do not describe the project as a RAG system.

Embedding-based style matching can be considered future work.

---

# 18. Future Enhancements

- Calendar integration for automatic occasion detection
- Longer-term user memory
- Personalized style learning
- Native mobile application
- Custom-trained vision model
- More advanced visual similarity search
- Social/outfit-sharing features
- Multi-agent orchestration
- More sophisticated recommendation/ranking models

---

# 19. Novelty

The primary novelty is not clothing classification.

The focus is on the **agent's reasoning and adaptation**.

A conventional wardrobe filter might do:

```text
Request
   ↓
Filter clothes
   ↓
Return result
```

CloseCall instead performs:

```text
Understand request
      ↓
Identify missing information
      ↓
Use tools
      ↓
Generate candidates
      ↓
Validate
      ↓
Diagnose failure
      ↓
Repair / Relax constraint / Ask
      ↓
Recommend
      ↓
Adapt to feedback
```

The key contribution is therefore:

> **Validate → Diagnose → Repair → Adapt**

rather than simply returning "no results."

---

# 20. Prototype Test Cases

### Test Case 1 — Happy Path

```text
Request:
Casual office outfit
Weather:
Rainy
```

Expected:

- Weather checked
- Suitable wardrobe retrieved
- 2–3 outfits generated
- Candidates validated
- Best options returned with reasoning

---

### Test Case 2 — Missing Formal Outfit

```text
Request:
Formal office outfit
```

Expected:

- Agent detects lack of a complete formal combination
- Diagnoses the missing/invalid item
- Suggests the closest alternative or asks for clarification

---

### Test Case 3 — Chappal Failure

```text
Request:
Formal office outfit
Clean footwear:
Chappal only
```

Expected:

- Candidate rejected
- Footwear conflict diagnosed
- Agent proposes an alternative or asks whether the user wants to relax the formality constraint

---

### Test Case 4 — User Rejection

```text
Agent:
Shirt + Jeans + Sneakers

User:
"I don't want jeans."
```

Expected:

- Agent updates the session constraint
- Queries wardrobe again
- Generates an alternative without jeans
- Does not restart the entire session

---

# 21. Scope

## In Scope

- Single-user wardrobe
- Image-based wardrobe upload
- Automatic vision tagging
- Natural-language outfit requests
- Weather tool
- Wardrobe database
- Outfit generation
- Outfit validation
- Failure diagnosis
- Constraint relaxation
- Clarification questions
- One-session feedback adaptation

## Future Work

- Native mobile application
- Calendar integration
- Long-term memory
- Multi-user/social functionality
- Custom-trained vision models
- Multi-agent architecture
- Advanced personalization

---

# 22. Project Summary

**CloseCall** is a personal stylist that recommends outfits from clothes the user already owns.

Its core technical contribution is an agentic reasoning loop where the system:

**understands → gathers information → generates → validates → diagnoses → adapts → recommends.**

The system is intentionally designed as a **single tool-calling agent** rather than a multi-agent system, keeping the prototype simple while demonstrating the essential principles of agentic AI.
