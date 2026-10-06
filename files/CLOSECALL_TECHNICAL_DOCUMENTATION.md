# CloseCall — Complete Technical Documentation

---

## Table of Contents

1. [What CloseCall Is](#1-what-closecall-is)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Configuration](#4-configuration)
5. [Entry Point — app.py](#5-entry-point--apppy)
6. [Database Layer](#6-database-layer)
7. [Vision Pipeline](#7-vision-pipeline)
8. [The AI Agent](#8-the-ai-agent)
9. [The Five Tools](#9-the-five-tools)
10. [Guardrails](#10-guardrails)
11. [Memory System](#11-memory-system)
12. [Knowledge Base and Retrieval](#12-knowledge-base-and-retrieval)
13. [Evaluation Framework](#13-evaluation-framework)
14. [UI Layer](#14-ui-layer)
15. [Data Flow — End to End](#15-data-flow--end-to-end)
16. [How to Run and Verify Each System](#16-how-to-run-and-verify-each-system)
17. [Key Design Decisions](#17-key-design-decisions)
18. [Known Issues and Limitations](#18-known-issues-and-limitations)

---

## 1. What CloseCall Is

CloseCall is a **local-first AI personal stylist** desktop/mobile web app. The user photographs their clothes, and the app builds a digital wardrobe from those photos using a Gemini vision model to automatically tag each item. When the user describes what they need — "office outfit for today," "casual date night," "it's raining and I have college" — a Gemini reasoning agent autonomously figures out what it needs to know (weather, what's clean in the wardrobe, styling rules), generates outfit combinations using only the user's real items, validates each combination against hard rules, and returns a recommendation with an explanation.

**What makes it genuinely agentic:** the agent is not a chatbot that wraps a static recommendation function. Every step — deciding whether to fetch weather, how to filter the wardrobe, whether to call a styling retriever, how to recover when all candidates fail validation — is a runtime decision made by the model based on the current conversation state. The application code does not dictate the sequence of tool calls. It only enforces limits (max rounds, mandatory validation check).

**What it is not:** a multi-agent system, a RAG chatbot over clothing data, a collaborative filtering recommender, or a rule-based outfit generator. There is one agent, five tools, and one Gemini model family powering both vision tagging and the reasoning loop.

---

## 2. Tech Stack

Every dependency is listed in `requirements.txt`. There are seven:

```
google-genai
gradio
sqlalchemy
requests
pillow
python-dotenv
pydantic
```

Here is what each one does and where it is used:

### `google-genai`
**What it is:** Google's official Python SDK for the Gemini API. This is `google.genai`, the current-generation SDK (not the deprecated `google.generativeai`).

**How it is used — two distinct places:**

1. **Vision tagging** (`src/vision/tagger.py`): A `genai.Client` sends a clothing image as raw bytes alongside a system prompt, and Gemini returns a JSON object with category, subtype, color, formality, season, rain suitability, status, and confidence. The response is parsed by a Pydantic model.

2. **Reasoning agent** (`src/agent/stylist_agent.py`): The same `genai.Client` is used with `generate_content()` to run the agentic loop. Tool functions (regular Python callables) are passed directly in `GenerateContentConfig(tools=[...])`. The SDK serializes their signatures and docstrings into Gemini's function-call format automatically. Automatic function calling is **disabled** — the agent handles the tool-call loop manually for full control.

**Why this SDK and not LangChain:** LangChain Google integration (`langchain-google-genai`) was hanging on this environment's network stack during development. A `tools_def.py` file exists with LangChain `@tool` decorators from the original plan, but it is never imported by the live agent. The direct SDK is what runs.

**Current model setting** (in `.env`):
```
GEMINI_MODEL=gemini-1.5-flash
GEMINI_VISION_MODEL=gemini-1.5-flash
```
Update both to a current 3.x model (e.g. `gemini-3.5-flash-lite`) before running, as 1.x and 2.x are deprecated. See `.env.example` for reference.

### `gradio`
**What it is:** A Python library for building web UIs declaratively. It renders a `gr.Blocks` layout as a full web app accessible in the browser, with zero JavaScript required.

**How it is used:** The entire CloseCall UI is built with Gradio Blocks (`app.py`, `src/ui/`). Components like `gr.Textbox`, `gr.Button`, `gr.HTML`, `gr.Image`, `gr.Slider`, `gr.CheckboxGroup`, `gr.Chatbot`, `gr.State`, and `gr.Tabs` are composed into a four-tab app. Event wiring uses `.click()`, `.change()`, `.submit()`, and `.then()` chains. Cross-tab navigation is handled by updating `gr.Tabs(selected=...)` and toggling `gr.Column(visible=...)`.

**How it serves the app:** `app.launch(server_name="0.0.0.0", server_port=7860)` makes it accessible on both `localhost:7860` and the local network IP (e.g. `192.168.x.x:7860`), which is how it can be tested from a phone on the same Wi-Fi.

### `sqlalchemy`
**What it is:** A Python ORM (Object-Relational Mapper) and SQL toolkit. Used here for the declarative ORM layer.

**How it is used:** One ORM model (`WardrobeItem`) is defined in `src/database/models.py`. `src/database/db.py` creates the engine, session factory, and all CRUD helpers. Every database read/write in the application goes through these helpers — no raw SQL queries for the wardrobe table. The engine uses `check_same_thread=False` because Gradio handles requests in multiple threads.

**The preferences table is a notable exception:** it uses raw `sqlite3` (Python's standard library), not SQLAlchemy. This is because the preferences table was added later as a simple key-value store and does not need ORM mapping.

### `requests`
**What it is:** The standard Python HTTP client library.

**How it is used:** Only in `src/tools/weather.py`. Makes a single GET request to `https://api.openweathermap.org/data/2.5/weather` with the user's location and API key. Has an 8-second timeout. Returns a structured dict with `temperature_c`, `condition`, `is_raining`, `humidity_pct`, `wind_kph`.

### `pillow`
**What it is:** Python Imaging Library fork. Used for image manipulation.

**How it is used:** In `src/vision/uploader.py`. When a user uploads an image via the Gradio file uploader, Gradio delivers it as a `PIL.Image` object. Pillow converts it to RGB (handling RGBA PNGs that would otherwise fail on JPEG save), saves it to disk at quality 90, and re-encodes it to bytes for the tagger. Without Pillow, format conversion and byte-level access wouldn't be possible.

### `python-dotenv`
**What it is:** Loads `.env` files into `os.environ`.

**How it is used:** Called once in `src/config.py` as `load_dotenv(_root / ".env")`. This makes all keys in `.env` available as environment variables before the rest of the app reads them.

### `pydantic`
**What it is:** A Python data validation library. Defines schemas as classes and validates data against them at instantiation.

**How it is used:** In `src/vision/tagger.py`, the `ClothingTag` class is a Pydantic `BaseModel` with typed fields and validators. When Gemini returns a JSON response for a clothing image, it is parsed into `ClothingTag(**data)`. Pydantic enforces that `category` is one of five valid values, `formality` is between 1 and 5, `confidence` is between 0.0 and 1.0, and `status` defaults to `"clean"` if the model returns anything invalid. This means the tagger can never insert garbage into the database — invalid data is caught and rejected at the schema boundary.

---

## 3. Project Structure

```
closecall/
├── .env                        # API keys and config (not committed)
├── .env.example                # Template showing all keys
├── app.py                      # Entry point — run: python app.py
├── requirements.txt            # All dependencies
│
├── data/
│   ├── closecall.db            # SQLite database (wardrobe items + preferences)
│   ├── images/                 # Uploaded clothing photos (item_XXXXXXXX.jpg)
│   └── profile.json            # User profile (name, email, location, style notes)
│
└── src/
    ├── config.py               # Reads .env, exposes config singleton
    │
    ├── agent/
    │   ├── stylist_agent.py    # The AI agent — reasoning loop, tool dispatch, memory
    │   ├── prompts.py          # System prompt with reasoning protocol and output format
    │   ├── guardrails.py       # Named guardrail constants and grounding checker
    │   └── tools_def.py        # Legacy LangChain @tool definitions (not used at runtime)
    │
    ├── database/
    │   ├── models.py           # WardrobeItem SQLAlchemy ORM model
    │   ├── db.py               # Engine, session factory, CRUD helpers
    │   ├── preferences.py      # Cross-session preference memory (SQLite)
    │   └── profile.py          # User profile read/write (JSON file)
    │
    ├── eval/
    │   ├── scenarios.py        # 8 fixed test scenarios with setup/teardown
    │   └── run_eval.py         # Eval harness — runs scenarios, computes metrics
    │
    ├── knowledge/
    │   ├── styling_kb.py       # 30 static styling guidance entries
    │   └── retrieval.py        # TF-IDF + cosine similarity retriever
    │
    ├── tools/
    │   ├── weather.py          # get_weather — OpenWeatherMap API
    │   ├── wardrobe.py         # get_wardrobe_state — queries DB with filters
    │   └── validation.py       # check_outfit_validity — deterministic hard-rule checker
    │
    ├── ui/
    │   ├── styles.py           # APP_CSS — all Gradio custom CSS
    │   ├── home_tab.py         # Home tab (hero, chips, weather widget, stats)
    │   ├── wardrobe_tab.py     # Wardrobe grid, filter chips, search
    │   ├── add_clothes_tab.py  # Upload + vision tag + result card
    │   ├── outfits_tab.py      # Main agent interaction tab
    │   ├── item_detail_tab.py  # Edit/delete individual wardrobe items
    │   ├── profile_tab.py      # User profile, stats, saved preferences
    │   └── stylist_tab.py      # Legacy chat UI (not mounted in live app)
    │
    └── vision/
        ├── tagger.py           # VisionTagger class — sends image to Gemini
        └── uploader.py         # upload_from_pil / upload_from_path pipeline
```

---

## 4. Configuration

### `src/config.py`

All configuration lives in a single `Config` class. It is instantiated once at module level as `config` and imported everywhere.

```python
class Config:
    GEMINI_API_KEY: str          # Required — from GEMINI_API_KEY env var
    OPENWEATHER_API_KEY: str     # Optional — falls back to mock weather if empty
    DEFAULT_LOCATION: str        # Default: "Mumbai" — used when profile has no location
    DATABASE_URL: str            # sqlite:///./data/closecall.db
    IMAGE_STORAGE_PATH: Path     # ./data/images
    GEMINI_MODEL: str            # default: "gemini-2.0-flash" (update via .env)
    GEMINI_VISION_MODEL: str     # default: "gemini-2.0-flash" (update via .env)
```

`config.validate()` is called at startup in `app.py`. If `GEMINI_API_KEY` is empty, it raises `EnvironmentError` with a message pointing to `.env.example`. The app will not start without a valid key.

### `.env` (do not commit this file)

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_VISION_MODEL=gemini-3.5-flash-lite
OPENWEATHER_API_KEY=your_key_here
DEFAULT_LOCATION=Chennai
DATABASE_URL=sqlite:///./data/closecall.db
IMAGE_STORAGE_PATH=./data/images
```

The model names must be updated to current 3.x series. `gemini-1.5-flash` and `gemini-2.x-flash` are deprecated. On the free tier, `gemini-3.5-flash-lite` gives ~500 free requests/day and is multimodal (handles images), making it suitable for both vision tagging and the reasoning agent.

---

## 5. Entry Point — `app.py`

Run the application with:
```bash
python app.py
```

**Startup sequence:**
1. `config.validate()` — checks that `GEMINI_API_KEY` is set. Exits with a helpful message if not.
2. `init_db()` — creates the `wardrobe_items` table (via SQLAlchemy `Base.metadata.create_all`) and the `user_preferences` table (via raw `sqlite3`). Safe to call on an existing database — it is a no-op if tables already exist.
3. The local Wi-Fi IP is detected using a UDP socket trick (`socket.connect("8.8.8.8")`) and printed alongside the localhost address. This gives a LAN address so the app can be tested on a phone.
4. `build_app()` constructs the Gradio Blocks layout and `.launch()` is called with `server_name="0.0.0.0"`.

**`build_app()` — Gradio layout:**

The layout is a `gr.Blocks` with a single `gr.Tabs` containing four tabs:

| Tab | ID | What it contains |
|---|---|---|
| Home | `tab-home` | Hero, request box, quick chips, weather, wardrobe count |
| Wardrobe | `tab-wardrobe` | Three sub-views (grid / add / detail) toggled by visibility |
| Outfits | `tab-outfits` | Main agent interaction (View A: input, View B: results) |
| Profile | `tab-profile` | Profile editor, stats, saved preferences |

A shared `gr.State("prefill_request_state")` carries text typed on the Home tab into the Outfits tab's input box when the user clicks "Get outfit suggestions." This is cross-tab wiring — it works because all components are defined inside the same `gr.Blocks` context and state is mutated then read by `prefill_state.change`.

The Wardrobe tab uses three `gr.Column` blocks with `visible=True/False` toggling to simulate sub-navigation (grid view, add view, detail/edit view) without actually switching tabs.

**Note on inner builder functions:** `app.py` defines `_build_home_inner`, `_build_wardrobe_inner`, and `_build_add_inner` as local functions inside `build_app()`. These are the versions that actually run. The equivalent standalone files in `src/ui/home_tab.py`, `src/ui/wardrobe_tab.py`, and `src/ui/add_clothes_tab.py` are cleaner modular versions designed to be called with injected nav callbacks — they are the reference implementations. In practice, `app.py`'s inner builders are the live code because they handle the cross-tab state wiring directly.

---

## 6. Database Layer

### `src/database/models.py` — `WardrobeItem`

The single SQLAlchemy model. Maps to the `wardrobe_items` table.

| Column | Type | Description |
|---|---|---|
| `item_id` | String (PK) | Auto-generated `item_{8-char-hex}`, e.g. `item_3af8ae9b` |
| `user_id` | String (indexed) | Always `"default_user"` in current prototype |
| `category` | String | `top` / `bottom` / `one_piece` / `footwear` / `outerwear` |
| `subtype` | String | `t-shirt` / `jeans` / `sneakers` / `formal_shoes` / `kurti` / `blazer` / etc. |
| `color` | String | Primary color name, e.g. `"navy"`, `"beige"` |
| `formality` | Integer (1–5) | 1=loungewear, 2=casual, 3=smart casual, 4=business casual, 5=formal |
| `season` | JSON | List, e.g. `["summer", "all-season"]` |
| `rain_suitable` | Boolean | True if item can be worn in rain |
| `status` | String | `"clean"` or `"dirty"` |
| `confidence` | Float | Gemini's tagging confidence (0.0–1.0) |
| `image_path` | Text | Absolute path to the stored image file |
| `label` | Text | Optional user-supplied name override |
| `created_at` / `updated_at` | DateTime | UTC timestamps |

`to_dict()` returns a plain Python dict. This is used everywhere instead of passing ORM objects across module boundaries, which avoids SQLAlchemy session scope errors in Gradio's threaded environment.

### `src/database/db.py` — Engine and CRUD

The SQLite file path is resolved to an absolute path at module load time. The SQLAlchemy engine is created once with `check_same_thread=False`.

**CRUD functions:**

```python
init_db()                          # Creates tables — called at startup
add_item(item_data: dict) -> dict  # Inserts a new WardrobeItem
get_item(item_id: str)             # Returns ORM object or None
get_item_dict(item_id: str)        # Returns dict or None
update_item(item_id, updates)      # Updates fields, returns updated dict
delete_item(item_id: str) -> bool  # Deletes item, returns success
get_all_items(user_id)             # Returns list of all item dicts
get_items_by_category(user_id, category) # Returns list filtered by category
query_items(user_id, filters: dict)  # Full flexible filtered query
```

**`query_items` filters** (used by the agent via `get_wardrobe_state`):

| Filter key | Type | Behavior |
|---|---|---|
| `status` | str | SQL `WHERE status = ?` |
| `category` | str | SQL `WHERE category = ?` |
| `categories` | list | SQL `WHERE category IN (...)` |
| `min_formality` | int | SQL `WHERE formality >= ?` |
| `max_formality` | int | SQL `WHERE formality <= ?` |
| `rain_suitable` | bool | SQL `WHERE rain_suitable = ?` |
| `season` | str | **Post-query Python filter** — checks if string appears in the JSON list |

The `season` filter is done in Python after the SQL query, not in SQL, because `season` is stored as a JSON list in a TEXT column and SQLite cannot efficiently filter inside it.

**`get_session()`** is a context manager that yields a SQLAlchemy `Session`, commits on success, rolls back on exception.

**`get_connection()`** returns a raw `sqlite3.Connection` — used only by `preferences.py`.

### `src/database/preferences.py` — Cross-Session Memory Store

Uses raw `sqlite3`, not SQLAlchemy. Creates the `user_preferences` table on first call.

```python
init_preferences_table()                          # Creates table if not exists
add_preference_note(user_id: str, note: str)      # Inserts a preference note
get_recent_preferences(user_id, limit=5) -> list  # Returns last N notes
```

The notes are short strings like `"No blazers"` or `"I prefer more casual options"`. They are written when the user submits a refinement in the Outfits tab, and read at the start of every `agent.chat()` call to inject into the system prompt.

### `src/database/profile.py` — User Profile

Profile data is stored as a JSON file at `data/profile.json`, not in the database. This keeps it human-readable and easy to edit.

```python
_DEFAULTS = {
    "name": "Your Name",
    "email": "user@example.com",
    "location": "Mumbai",
    "style_notes": "",
}

load_profile() -> dict   # Merges file data over defaults
save_profile(data: dict) # Updates only known keys and writes back
```

The current live profile (`data/profile.json`) has `"location": "Chennai"`. This location is what the weather tool always uses — the agent is not allowed to extract a location from the user's request text (see Guardrail 5).

---

## 7. Vision Pipeline

When a user uploads a clothing photo, two things happen: the image is saved to disk, and Gemini analyzes it to extract structured metadata.

### `src/vision/tagger.py` — `VisionTagger`

**`ClothingTag` (Pydantic model):**

```python
class ClothingTag(BaseModel):
    category: str        # top | bottom | one_piece | footwear | outerwear
    subtype: str         # t-shirt | jeans | sneakers | formal_shoes | ...
    color: str           # primary color name
    formality: int       # 1–5, validated ge=1 le=5
    season: list[str]    # subset of [summer, winter, monsoon, spring, all-season]
    rain_suitable: bool
    status: str          # always "clean" — validator rejects anything else
    confidence: float    # 0.0–1.0
```

Validators:
- `category` must be one of five exact values. Any other value raises `ValueError`.
- `status` defaults to `"clean"` if the model returns something else (defensive).

**System prompt sent to Gemini for tagging:**
The tagger sends a strict system prompt saying "return ONLY a valid JSON object, no markdown, no explanation." It provides exact allowed values for each field and a formality guide (1=pyjamas, 5=suit jacket). This is important because JSON-only output is easier to parse than markdown-wrapped output.

**`tag_image_bytes(image_bytes, mime_type)`:**
Sends two `Part` objects to Gemini: the system prompt text and the raw image bytes. The response text is parsed by `_parse_response()`, which strips markdown code fences if present (some model versions wrap JSON in triple backticks), then JSON-parses the result into a `ClothingTag`.

**Module-level singleton:**
```python
_tagger: Optional[VisionTagger] = None
def get_tagger() -> VisionTagger: ...
```

### `src/vision/uploader.py` — Upload Handlers

Two entry points:

**`upload_from_pil(pil_image, user_id, label, original_filename) -> dict`**
This is what the Gradio UI uses. Gradio delivers uploaded images as PIL objects.

Steps:
1. Generates `item_id = f"item_{uuid.uuid4().hex[:8]}"`.
2. Converts to RGB if needed (handles RGBA PNGs — JPEG does not support transparency).
3. Saves to `data/images/{item_id}.jpg` at quality 90.
4. Re-encodes to bytes buffer and passes to `tagger.tag_image_bytes()`.
5. Assembles `item_data` dict combining all tag fields plus `item_id`, `user_id`, `label`, `image_path`.
6. Calls `db.add_item(item_data)` to persist to SQLite.
7. Returns the item dict.

**`upload_from_path(image_path, user_id, label) -> dict`**
Same flow but for local file paths. Used in scripts and testing. Copies the file to storage, then calls `tagger.tag_image()` (file path version).

---

## 8. The AI Agent

`src/agent/stylist_agent.py` is the core intelligence of the app.

### How It Works — The Reasoning Loop

The `StylistAgent` class implements a **manual agentic loop** using the `google.genai` SDK directly. Gradio's "Get outfits →" button eventually calls `agent.chat(user_message)`, which runs this loop:

```
1. Append user message to conversation_memory
2. Set up GenerateContentConfig with:
      - system_instruction (SYSTEM_PROMPT + injected preferences)
      - tools = all 5 Python functions
      - temperature = 0.3
      - automatic_function_calling = DISABLED
3. Loop up to MAX_REASONING_ROUNDS (10) times:
   a. Call Gemini with full conversation_memory
   b. Append the model's response Content to conversation_memory
   c. If response contains function_call parts:
        - Execute each function via _TOOL_MAP
        - Append results as Content(role="user", parts=[FunctionResponse...])
        - Print tool name, args, and result to console (visible in terminal)
        - Track call in last_tool_calls (for eval)
        - Continue loop
   d. If response has no function calls:
        - Check validation guardrail (see Guardrail 2)
        - If guardrail fires → inject a correction message, continue loop
        - Otherwise → extract text, break
4. Trim conversation_memory to last 20 Content objects
5. Return final text
```

**Why `automatic_function_calling=disabled`:**
With auto-calling on, the SDK executes tools internally and the app loses visibility into what was called, with what arguments, and what was returned. Manual loop gives full control and lets the eval harness read `agent.last_tool_calls` after each turn.

**Why `temperature=0.3`:**
Low temperature makes the agent's tool-calling behavior more deterministic and consistent across runs. A higher temperature would cause the agent to sometimes skip tools or deviate from the output format.

### System Prompt (`src/agent/prompts.py`)

The system prompt (`SYSTEM_PROMPT`) is the agent's complete behavioral specification. Key sections:

**Reasoning protocol (8 steps):**
1. Parse the request — extract occasion, style, weather, preferences.
2. If weather is unknown → call `get_weather`.
3. Call `get_wardrobe_state` with appropriate filters.
4. Generate 2–3 candidate combinations using only real `item_ids` from the wardrobe query.
4b. For color/style decisions → call `retrieve_styling_guidance`.
5. Call `check_outfit_validity` on every candidate.
6. If valid outfits exist → rank by soft constraints → recommend.
7. If all fail → diagnose failure → relax a soft constraint and retry → if still failing → call `ask_user_clarification`.
8. If user rejects → update constraints, re-query, regenerate (do NOT restart).

**Outfit templates:**
- A: top + bottom + footwear
- B: top + bottom + footwear + outerwear
- C: one_piece + footwear
- D: one_piece + footwear + outerwear

**Hard constraints (never violate):**
- All items must be `status == "clean"`
- Outfit needs footwear + (top + bottom) OR one_piece
- No chappal/sandals for office or formal occasions
- If raining: footwear must be `rain_suitable = true`

**Soft constraints (can be relaxed with explanation):**
- Formality level, season match, color, mood

**Output format:** strictly mandated markdown. The Outfits tab's regex parser depends on this exact format:
```
### Outfit 1: [Title]
- **[Color Item name]** — item_id
*Why this works:* [explanation]
```

Any deviation breaks the card renderer.

### Memory Injection

`_system_prompt()` is called at the start of each `chat()` call. It reads `get_recent_preferences(user_id)` and appends a `## KNOWN USER PREFERENCES` block to `SYSTEM_PROMPT` if there are any saved preferences. This means what the user dislikes today will be present in the system prompt tomorrow.

### Module-Level Singleton

```python
_agent_instance: Optional[StylistAgent] = None

def get_agent(user_id: str = "default_user") -> StylistAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = StylistAgent(user_id)
    return _agent_instance

def reset_agent():
    if _agent_instance:
        _agent_instance.reset_session()
```

`reset_session()` clears `conversation_memory` and `last_tool_calls`. It is called when the user clicks "← New request" in the Outfits tab.

---

## 9. The Five Tools

The tools are the agent's hands. They are regular Python functions defined in `stylist_agent.py` (wrappers around the actual implementations in `src/tools/` and `src/knowledge/`). They are passed directly to `GenerateContentConfig(tools=[...])` — the SDK reads their signatures and docstrings to generate the function-call schema for Gemini.

### Tool 1: `get_weather`

**Defined in:** `stylist_agent.py` (wrapper) → `src/tools/weather.py` (implementation)

**What it does:** Fetches live weather for the user's location from OpenWeatherMap.

**Important — guardrail enforcement:** The wrapper **ignores the `location` parameter the model provides**. It always reads `load_profile()["location"]` instead. This prevents the model from guessing locations from ambiguous words in the request (e.g., treating "college" as a city name).

**When the agent calls it:** When the user's request does not already contain weather information. The agent is instructed to skip this call if the user says "it's sunny" or "it's raining today."

**Returns:**
```json
{
  "location": "Chennai",
  "temperature_c": 32.1,
  "condition": "Rain",
  "description": "moderate rain",
  "is_raining": true,
  "humidity_pct": 88,
  "wind_kph": 14.4
}
```

**Fallback:** If `OPENWEATHER_API_KEY` is not set, returns mock weather: `28°C, Clouds, is_raining=False`. The agent can still reason and recommend — it just won't know the real weather.

### Tool 2: `get_wardrobe_state`

**Defined in:** `stylist_agent.py` (wrapper) → `src/tools/wardrobe.py` → `src/database/db.query_items()`

**What it does:** Queries the SQLite wardrobe database with filters and returns a list of matching items.

**Supported filters:**
```json
{
  "status": "clean",
  "category": "top",
  "categories": ["top", "bottom", "footwear"],
  "min_formality": 3,
  "max_formality": 5,
  "rain_suitable": true,
  "season": "monsoon"
}
```

**Type normalization:** The wrapper normalizes types the LLM might get wrong — `"true"` (string) → `True` (bool), `"3"` (string) → `3` (int). This prevents silent filter failures.

**Returns:**
```json
{
  "items": [
    {
      "item_id": "item_3af8ae9b",
      "category": "top",
      "subtype": "shirt",
      "color": "navy",
      "formality": 4,
      "season": ["all-season"],
      "rain_suitable": false,
      "status": "clean",
      ...
    }
  ],
  "total_count": 12,
  "filters_used": {"status": "clean", "min_formality": 3}
}
```

**The agent never sees the full wardrobe by default.** It must ask for what it needs. This mirrors how a real human thinks ("I need to look in my wardrobe for formal clothes") and keeps the context window tighter.

### Tool 3: `check_outfit_validity`

**Defined in:** `stylist_agent.py` (wrapper) → `src/tools/validation.py`

**What it does:** Deterministic, rule-based validation of a candidate outfit. Not an LLM judgment — actual Python code checking hard rules.

**Inputs:** A list of wardrobe item dicts (the candidate outfit) and a constraints dict from the current request.

**Five checks performed:**

1. **All items clean:** Any item with `status == "dirty"` is a hard fail.
2. **Category completeness:** The outfit must have footwear AND either (top + bottom) or one_piece.
3. **Formality range:** If `min_formality` or `max_formality` in constraints, every item must fall within the range.
4. **Rain suitability:** If `is_raining = true`, footwear must have `rain_suitable = true` (hard fail). Non-footwear items get a soft warning (may be protected by outerwear).
5. **Footwear/occasion rules:** Chappal and sandals are rejected for office and formal occasions. Chappal alone is rejected for any office occasion.

**Returns:**
```json
{
  "valid": false,
  "passed": ["All items are clean", "Footwear present"],
  "failed": ["Footwear navy chappal [item_45a66a29] is not appropriate for office ('chappal' not allowed)"],
  "diagnosis": "Outfit failed validation. Issues: Footwear navy chappal [item_45a66a29] is not appropriate for office..."
}
```

The `diagnosis` field is what the agent reads when deciding its next step: relax a soft constraint, try different items, or ask for clarification.

### Tool 4: `ask_user_clarification`

**Defined in:** `stylist_agent.py`

**What it does:** Returns a `"CLARIFICATION_NEEDED: {question}"` string. This is the agent's way of giving up gracefully — when it genuinely cannot resolve constraints automatically (e.g. no valid footwear exists for the occasion at all), it surfaces a specific question to the user.

**Example output:**
```
CLARIFICATION_NEEDED: All formal footwear in your wardrobe is currently dirty. 
Could you mark some footwear as clean, or would you like a smart casual option instead?
```

The Outfits tab renders this as a regular response (no special handling) — the user reads the question and can reply in the request box.

### Tool 5: `retrieve_styling_guidance`

**Defined in:** `stylist_agent.py` (wrapper) → `src/knowledge/retrieval.py`

**What it does:** Performs TF-IDF similarity search over the 30-entry styling knowledge base and returns the top 3 most relevant styling principles.

**When the agent calls it:** When choosing between multiple style-equivalent valid outfits, or when explaining a color/fabric choice. This grounds the "Why this works" explanation in actual styling principles rather than generic reasoning the model invents.

**Returns:**
```json
{
  "guidance": [
    {
      "text": "Pairing a bold or bright top with a neutral bottom balances visual weight...",
      "category": "color",
      "relevance": 0.4231
    },
    ...
  ]
}
```

---

## 10. Guardrails

`src/agent/guardrails.py` centralizes all safety behavior as named, documented constants. The key design principle: **guardrails are enforced in code, not just instructed in prompts.** A prompt instruction alone can be ignored by the model. A code-level check cannot.

### Guardrail 1: Bounded Reasoning Loop

```python
MAX_REASONING_ROUNDS = 10
```

The `chat()` loop in `stylist_agent.py` runs at most 10 rounds regardless of what the model decides to do. This prevents infinite tool-call loops and bounds the maximum API cost of a single user request. If the model hasn't returned a final text response in 10 rounds, the last text in the history is returned.

### Guardrail 2: Mandatory Validation Before Final Answer

```python
ENFORCE_VALIDATION_BEFORE_FINAL_ANSWER = True
```

**Why this exists:** The system prompt instructs the agent to call `check_outfit_validity` for every candidate. But during evaluation testing, one scenario (S7 — rainy weather) showed that the model skipped validation and produced a final recommendation directly. The prompt instruction was not enough.

**How it is enforced in code** (`stylist_agent.py`):
```python
if (
    ENFORCE_VALIDATION_BEFORE_FINAL_ANSWER
    and looks_like_recommendation      # response contains "item_"
    and not validity_was_called        # no check_outfit_validity this turn
    and _round < MAX_REASONING_ROUNDS - 1
):
    # Inject a forced follow-up and continue the loop
    conversation_memory.append(Content(role="user", parts=[
        Part.from_text("You must call check_outfit_validity on your candidate outfit 
                        before giving a final answer. Please validate it now.")
    ]))
    continue
```

This means the loop never accepts a response that contains `item_` IDs without having called the validator first. The validation guardrail is the only place a programmatic message is injected mid-conversation.

**A terminal printout of `⚠️ VALIDATION GUARD` appears when this fires.**

### Guardrail 3: Zero Tolerance for Invented Items

```python
ALLOW_INVENTED_ITEMS = False
```

`check_response_grounding(response_text, real_item_ids)` in `guardrails.py` extracts all `item_XXXXXXXX` patterns from the agent's response with regex, diffs them against the real database IDs, and returns a dict:

```json
{
  "grounded": true,
  "referenced_ids": ["item_3af8ae9b", "item_45a66a29"],
  "hallucinated_ids": []
}
```

This is called by the eval harness after every scenario run. In a production system, it should also be called live and the response rejected if `hallucinated_ids` is non-empty.

### Guardrail 4: Hard Constraints in Code, Not LLM Judgment

Hard constraints (clean status, category completeness, rain footwear, occasion footwear rules) are all implemented as deterministic Python in `validation.py`. The agent cannot override or relax them — it only receives `valid: false` with a `diagnosis` and must reason about what to do next.

Soft constraints (formality preference, color preference, mood) are evaluated as SQL filters in `query_items` and can be relaxed by the agent when no outfit passes.

### Guardrail 5: Location Grounding

```python
TRUST_MODEL_FOR_LOCATION = False
```

The `get_weather` tool function in `stylist_agent.py` always ignores the `location` parameter passed by the model and reads from the profile:

```python
def get_weather(location: str = "") -> dict:
    from src.database.profile import load_profile
    profile = load_profile()
    trusted_location = profile.get("location", "Chennai")
    return _get_weather(trusted_location)  # model's location param ignored
```

**Why:** During testing, when a user said "outfit for college today," the model passed `"college"` as the location to `get_weather`, which caused an API error. The location must come from a trusted source (the profile), not from model inference over the request text.

---

## 11. Memory System

The app has two completely separate memory systems. They serve different purposes and are implemented in different places.

### Short-Term Memory — In-Session (`conversation_memory`)

**Where:** `StylistAgent.conversation_memory: list[genai_types.Content]`

**What it contains:** The full turn history for the current session: every user message, every model response, every tool call, every tool result — in Gemini's native `Content` format. This is what gets passed back to `generate_content()` on every loop iteration, making Gemini aware of the full context.

**How it enables refinement:** When the user says "change the footwear" after seeing outfit recommendations, the agent's next call has the entire prior conversation — including the wardrobe query results and the specific outfit that was rejected — in its memory. It does not start from scratch.

**Trimming:** After each `chat()` call, the list is trimmed to the last 20 `Content` objects. This prevents token usage from growing unboundedly across a long session. A `Content` object can be a single message or a tool call/result pair.

**Clearing:** `reset_session()` sets `conversation_memory = []`. This is called when the user clicks "← New request" in the Outfits tab.

### Long-Term Memory — Cross-Session (`user_preferences` table)

**Where:** `src/database/preferences.py`, table `user_preferences` in `data/closecall.db`

**What triggers a write:** When the user submits a refinement request in the Outfits tab (e.g., chips like "More casual" or the free-text refinement box), `add_preference_note(user_id, refinement_text)` is called before forwarding the message to the agent. The note is stored permanently.

**What triggers a read:** At the start of every `_system_prompt()` call, which is called inside every `chat()`. The 5 most recent notes are appended to the system prompt as:
```
## KNOWN USER PREFERENCES (from past sessions)
- No blazers
- I prefer more casual options
- Different footwear please
```

**Effect:** A preference expressed today — "no blazers" — is present in the system prompt during the next session, even after the app is closed and reopened. The agent avoids blazers or explicitly explains its choice if one is included.

**No expiry:** Preference notes accumulate indefinitely. Only the 5 most recent are injected into the prompt. Older ones remain in the database but have no effect on the agent unless the limit is increased.

---

## 12. Knowledge Base and Retrieval

### `src/knowledge/styling_kb.py` — 30 Styling Principles

A static list of 30 styling guidance entries, grouped into 5 categories:

| Category | Entries | Example |
|---|---|---|
| `color` | 8 | "Pairing a bold top with a neutral bottom balances visual weight" |
| `formality` | 7 | "Closed-toe footwear is appropriate for office; sandals generally are not" |
| `weather` | 7 | "In rain, synthetic fabrics and closed footwear are preferable to suede or canvas" |
| `silhouette` | 4 | "Loose top + fitted bottom creates a proportioned silhouette" |
| `pattern` | 4 | "A patterned item is best paired with solid, neutral-colored separates" |

Each entry is `{"id": "color_01", "category": "color", "text": "..."}`.

### `src/knowledge/retrieval.py` — TF-IDF Retriever

A pure-Python TF-IDF implementation with no external ML dependencies.

**How it works:**

1. **Index build time** (when the module is first imported):
   - Tokenizes each knowledge base entry's text using `re.findall(r"[a-z]+", text.lower())`.
   - Computes document frequency (DF) per term across all 30 documents.
   - Computes IDF for each term: `log((1 + N) / (1 + df)) + 1`.
   - Pre-computes a TF-IDF weight vector for each of the 30 documents.

2. **Query time** (`query(text, top_k=3)`):
   - Tokenizes the query string the same way.
   - Computes a TF-IDF vector for the query.
   - Computes cosine similarity between the query vector and all 30 document vectors.
   - Returns the top-k results sorted by score, with the score included.

**Why TF-IDF instead of an embedding API:** Embedding APIs have rate limits on the free tier. During development this caused reliability issues. 30 documents is small enough that TF-IDF gives perfectly adequate retrieval quality (the corpus is narrowly scoped to styling topics), and it works entirely offline with no network call.

The index is built at module load time:
```python
_index = _TfidfIndex(STYLING_KB)
```
Building it for 30 short documents takes negligible time.

`retrieve_styling_guidance(query, top_k=3)` is the public function used by the agent tool wrapper.

---

## 13. Evaluation Framework

The eval framework tests the agent's behavior against a set of fixed scenarios, including ones with engineered failure conditions, to measure correctness and safety properties.

### How to Run the Eval

```bash
python -m src.eval.run_eval
```

Or directly:
```bash
python src/eval/run_eval.py
```

Results are written to `eval_results.json` in the project root. The terminal shows a summary table.

**Important:** The eval manipulates real database state (marks items dirty, changes footwear subtype). Every scenario with a `setup` function has a matching `teardown` that restores the database. If the eval crashes mid-run, run it again or manually restore via the item detail UI.

### `src/eval/scenarios.py` — The 8 Scenarios

| ID | Name | What it tests | Setup/Teardown |
|---|---|---|---|
| S1 | Happy path — casual college | Full flow: weather + wardrobe + validation | None |
| S2 | Weather already stated | Agent should skip `get_weather` | None |
| S3 | Formal office request | Formality filtering + formal footwear rules | None |
| S4 | Forced footwear failure | All footwear subtype set to `"chappal"`, office request | Sets chappal; restores `item_45a66a29` to flats |
| S5 | Entire wardrobe dirty | Graceful failure — no clean items available | Marks all dirty; restores all to clean |
| S6 | Casual date — style judgment | Should call `retrieve_styling_guidance` | None |
| S7 | Rainy weather explicitly stated | Rain-suitable footwear check | None |
| S8 | Vague "What should I wear?" | Ambiguous occasion handling | None |

**How S4 and S5 work as tests:** The `setup` function directly modifies the database using `get_session()` and `session.query(WardrobeItem).update(...)`. This creates a genuine failure condition — the validation tool will actually return `valid: false` because the database really contains chappal or dirty items. The agent must then recover. After the scenario runs, `teardown` restores the original values.

### `src/eval/run_eval.py` — The Harness

**`run_scenario(scenario) -> dict`:**

1. Runs `scenario["setup"]()` if defined.
2. Calls `reset_agent()` then `agent.chat(scenario["request"])`.
3. Reads `agent.last_tool_calls` (tracked during the reasoning loop).
4. Runs `scenario["teardown"]()` if defined.
5. Computes results:
   - `tools_called`: list of tool names called this turn.
   - `validation_ran`: whether `check_outfit_validity` was called at all.
   - `any_validation_failed/passed`: whether any call returned `valid: false/true`.
   - `hallucinated_ids`: item IDs in the response not found in the real database (via `check_response_grounding`).
   - `correct_tool_use`: checks that all `expect_tool_calls` were called and no `expect_no_call` tool was called.
   - `recovered_from_failure`: for scenarios with `expect_validation_failure`, checks that a fail occurred AND the agent subsequently either passed a validation OR asked for clarification.
6. Returns a dict with all results plus `final_response_preview` (first 200 chars).

**`summarize(results) -> dict`:**

Four aggregate metrics:

| Metric | Definition |
|---|---|
| `tool_call_correctness_rate` | Fraction of scenarios where expected tools were called and no forbidden tools were called |
| `validation_executed_rate` | Fraction of scenarios where `check_outfit_validity` ran at least once |
| `zero_hallucination_rate` | Fraction of scenarios where the response referenced no invented item IDs |
| `failure_cases_recovered` | List of scenario IDs where engineered failure was gracefully recovered |

**`write_report(results, summary, path="eval_results.json")`:**
Writes a timestamped JSON file with the full per-scenario results and aggregate summary.

### What the Eval Discovered (and Changed)

The most important outcome of the eval was catching that Guardrail 2 was needed. In an early run, scenario S7 (rainy weather) showed `validation_ran: false` — the model had produced a final recommendation without calling `check_outfit_validity`. The prompt said "you MUST validate every candidate" but the model didn't comply in that scenario. This finding directly caused the `ENFORCE_VALIDATION_BEFORE_FINAL_ANSWER` check to be added as code in `stylist_agent.py`. After that, `validation_executed_rate` reached 100%.

---

## 14. UI Layer

### `src/ui/styles.py` — `APP_CSS`

~500 lines of CSS injected into the Gradio Blocks via `gr.Blocks(css=APP_CSS)`.

**Design tokens:**
- Background: `#FAF9F7` (warm off-white)
- Accent/primary: `#7C5CFC` (violet)
- Primary text: `#1A1A1A`
- Border: `#E8E5E0`

**Responsive behavior:**
- Below 640px (mobile): tab navigation collapses to a **fixed bottom nav bar** (iOS-style), giving full screen to content.
- Above 640px (desktop): sticky top nav.
- Wardrobe grid: 4 columns → 3 → 2 → 1 as screen narrows.
- Outfit grid: `auto-fit minmax(320px, 1fr)` → single column on mobile.

**Key CSS classes:**
- `.cc-item-card` — wardrobe item card (image + name + formality + badge)
- `.cc-outfit-card` — outfit recommendation card (violet border for best match)
- `.cc-outfit-best` — first outfit highlighted
- `.cc-badge-clean` / `.cc-badge-dirty` — green/red status pills
- `.cc-why-box` — green "Why this works" explanation box
- `.cc-fail-box` — amber "couldn't find" fallback box
- `.cc-error-box` — error message box
- `.cc-confidence-bar` / `.cc-confidence-fill` — CSS progress bar for tagger confidence
- `.cc-agent-steps` — the processing checklist in the Outfits tab
- `.cc-chip` — quick-action chip buttons

### Home Tab (`src/ui/home_tab.py`)

Hero section with a heading and request textbox. "Get outfit suggestions →" button. Five quick-pick chips (Work, Casual, Date Night, College, Travel) that pre-fill the textbox. A weather widget showing current conditions and temperature for the user's location. A wardrobe count stat ("17 items").

Clicking a chip fills the request box. Submitting the request fires `on_request_fn`, which is the cross-tab nav callback wired in `app.py` to switch to the Outfits tab.

### Wardrobe Tab (`src/ui/wardrobe_tab.py`)

Header + "Add clothes" button. Search textbox (live filter on `.change`). Six category filter chips (All / Tops / Bottoms / One-pieces / Footwear / Outerwear). Responsive HTML grid rendered by `_grid()`.

Each `cc-item-card` contains:
- The clothing image as a base64 data URL (read from disk, encoded inline — no server needed)
- Item name (from `label` field if set, otherwise "Blue T-Shirt" style from color + subtype)
- Formality label ("Smart casual", "Business casual", etc.)
- Clean/Dirty badge

Items are grouped by category with section headers showing the count.

Below the grid: a dropdown item picker + "Edit tags →" button that switches to the item detail view.

### Add Clothes Tab (`src/ui/add_clothes_tab.py`)

Two-column desktop layout: left = upload panel, right = result card.

**Upload panel:**
- `gr.Image(type="pil")` — Gradio handles file upload and delivers a PIL Image
- Optional label textbox
- "Analyze →" button
- A step checklist with 5 stages: Uploading image → Reading photo → Identifying item → Extracting details → Saving to wardrobe

**Processing stages** use a `.click().then()` chain:
- `.click` fires `on_analyze_start` immediately — shows the "Analyzing…" checklist.
- `.then` fires `handle_tag` — calls `upload_from_pil`, updates checklist to done, renders the result card.

**Result card** shows: category, subtype, color, formality, season list, rain suitability, status, and a CSS confidence bar (green if ≥ 0.85, yellow if ≥ 0.65, red below).

### Outfits Tab (`src/ui/outfits_tab.py`)

The most complex tab. Two `gr.Column` blocks toggled by visibility.

**View A — Request:**
- Request textbox + "Get outfits →" button
- "↺ Start over" button (clears agent session)
- Agent processing checklist (`_thinking_html`) — shows 6 steps with ✓/…/○ icons
- Error box for wardrobe-empty or API errors

**View B — Results:**
- Weather context line ("Clouds · 32°C · 🌧 Rainy")
- Outfit cards HTML (rendered by `_outfit_card_html`)
- Three action buttons: "← New request", "Try another →", "Change something", "Looks good ✓"
- Inline refinement row (hidden until "Change something")

**Key functions:**

`_parse_outfits(text) -> list[dict]`:
Regex-based parser for the agent's markdown output. Finds `### Outfit N: title` headings, extracts item bullets (`- **name** — item_id`), "Why this works" sections, and "Styling guidance" sections. Returns a list of up to 3 outfit dicts. Falls back gracefully if the format is different than expected.

`_outfit_card_html(outfit, idx, is_best, is_raining)`:
Builds a `cc-outfit-card` HTML block. First outfit gets violet `cc-outfit-best` border. Shows item list with item name + item_id in monospace. Renders the "Why this works" green box. Renders an optional purple "Styling guidance" box if the agent included retrieved principles.

`on_send_execute(request, history)`:
1. Checks if wardrobe is empty → shows error if so.
2. Fetches weather context for the context line.
3. Calls `agent.chat(request)`.
4. Checks if the response is a failure message (`_is_failure_response`).
5. If failure → renders failure HTML (amber box with agent's explanation).
6. If success → parses outfits, renders cards, switches to View B.

**Inline refinement:**
6 quick chips (More formal, More casual, Different colour, No blazer, Different footwear, Show more options) each map to a specific prompt string. A free-text box allows custom refinements. Submitting a refinement calls `add_preference_note` to persist it, then `agent.chat(refinement_text)` to get updated outfits inline — without leaving the results view.

"Try another →" calls `agent.chat("Show me different outfit options.")` inline. Because `conversation_memory` is intact, the agent knows what was shown before and offers different combinations.

"Looks good ✓" shows a static confirmation banner. "← New request" resets the agent and switches back to View A.

**Prefill wiring:**
When the user types a request on the Home tab and clicks "Get outfit suggestions →", `app.py` writes the text into `prefill_request_state` (a `gr.State`) and switches to the Outfits tab. The Outfits tab's `prefill_state.change` event handler reads this value and pre-fills the request textbox.

### Profile Tab (`src/ui/profile_tab.py`)

Avatar area (user icon + name + email from profile). Stats row: total items, clean items, saved preferences count. Inline edit form: name, email, location, style notes. "Save" writes via `save_profile()`. Saved preferences section shows the last 5 notes. Profile settings menu rows (Wardrobe, Calendar "coming soon", About).

### Item Detail Tab (`src/ui/item_detail_tab.py`)

Edit form for a single wardrobe item. Dropdown to pick from all items (shows name + status). Image display (base64 inlined). Category and subtype dropdowns. Color textbox. Formality slider (1–5) with a live label that updates as you drag: "3 · Smart Casual". Season checkboxes (5 options). Clean/Dirty radio. Save and Delete buttons. `handle_save` calls `db.update_item`. `handle_delete` calls `db.delete_item`. Returns `item_id_state` for use by the parent.

### `src/ui/stylist_tab.py` — Legacy Chat UI (not mounted)

A simpler, earlier `gr.Chatbot`-based interface from before the Outfits tab was built. Still present but **never mounted in `app.py`**. It imports `get_agent` and `reset_agent` and provides basic chat with 4 sample request buttons. Can be used as a simpler test harness if needed.

---

## 15. Data Flow — End to End

### Adding a Clothing Item

```
User drags a photo into the upload panel (Add Clothes tab)
  → Gradio delivers PIL.Image to handle_tag()
  → uploader.upload_from_pil(pil_image)
      → PIL converts to RGB, saves to data/images/item_XXXXXXXX.jpg
      → PIL re-encodes to bytes buffer
      → tagger.VisionTagger.tag_image_bytes(bytes, "image/jpeg")
          → genai.Client.generate_content(
                model=GEMINI_VISION_MODEL,
                parts=[system_prompt_text, image_bytes]
            )
          → Parse JSON response → ClothingTag (Pydantic validated)
      → db.add_item({item_id, category, subtype, color, formality,
                     season, rain_suitable, status, confidence, image_path})
          → SQLAlchemy INSERT into wardrobe_items
  → Result card rendered in UI
```

### Getting Outfit Recommendations

```
User types "I need an office outfit for today" and clicks "Get outfits →"
  → on_send_execute(request, history)
      → get_all_items() → check wardrobe is not empty
      → get_weather(profile location) → weather context line
      → agent.chat("I need an office outfit for today")
          
          [Round 0]
          → Gemini receives: system_prompt + conversation_memory + user message
          → Gemini returns: function_call get_weather(location="Chennai")
          → get_weather("") → reads profile → _get_weather("Chennai")
              → OpenWeatherMap API → {temp: 32°C, condition: "Rain", is_raining: true}
          → Append tool result to conversation_memory, continue loop
          
          [Round 1]
          → Gemini returns: function_call get_wardrobe_state(filters='{"status":"clean","min_formality":3}')
          → query_items(user_id="default_user", filters={...})
              → SQLAlchemy query → list of 9 clean items with formality >= 3
          → Append results, continue loop
          
          [Round 2]
          → Gemini returns: function_call retrieve_styling_guidance("office outfit with rain")
          → _TfidfIndex.query(...) → top 3 styling principles for weather + formality
          → Append results, continue loop
          
          [Round 3]
          → Gemini generates candidate outfits using only returned item_ids
          → Gemini returns: function_call check_outfit_validity(
                outfit_json='[{item_3af8ae9b navy shirt...}, ...]',
                constraints_json='{"occasion":"office","is_raining":true}'
            )
          → validation.check_outfit_validity(outfit, constraints)
              → Check 1: all clean ✓
              → Check 2: has top + bottom + footwear ✓
              → Check 3: formality all >= 3 ✓
              → Check 4: is_raining=true → footwear rain_suitable=true? ✗ (flats)
          → Returns {valid: false, failed: ["Footwear not rain-suitable"]}
          → Append result, continue loop
          
          [Round 4]
          → Gemini re-queries wardrobe for rain_suitable footwear
          → [another query round]
          
          [Round 5]
          → Gemini validates new candidate → passes
          
          [Round 6]
          → Gemini returns final text response with outfit recommendations
          → Guardrail check: contains "item_" AND validity_was_called → accept
          → Trim conversation_memory to last 20 Content objects
          → Return response text
      
      → _parse_outfits(response) → list of outfit dicts
      → _cards_html(outfits, is_raining=True) → HTML string
      → Render outfit cards, switch to View B
```

### Refinement Loop

```
User clicks "Change something" → "No blazer" chip
  → add_preference_note("default_user", "No blazer") → SQLite INSERT
  → agent.chat("I don't want to wear a blazer.")
      → conversation_memory still has previous context
      → Agent re-queries wardrobe excluding blazers, validates, returns new outfits
  → Update outfit cards HTML in place (stay on View B)
```

### Next Session

```
User opens app again
  → init_db() (no-op, tables exist)
  → New StylistAgent(), conversation_memory = []
  → First agent.chat() call:
      → _system_prompt() calls get_recent_preferences()
      → SQLite returns ["No blazer", "More casual", ...]
      → Appended to SYSTEM_PROMPT as ## KNOWN USER PREFERENCES
      → Agent is aware of past preferences from the very first message
```

---

## 16. How to Run and Verify Each System

### Run the App

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in .env
cp .env.example .env
# Edit .env: set GEMINI_API_KEY, update GEMINI_MODEL to a 3.x model

# Run
python app.py
```

Open `http://localhost:7860` in a browser.

### Verify Vision Tagging

1. Go to the Wardrobe tab → "Add clothes".
2. Upload any clothing photo.
3. Click "Analyze →".
4. The step checklist should progress through all 5 stages and the result card should appear with category, color, formality, etc.
5. To verify in the database: `sqlite3 data/closecall.db "SELECT item_id, category, subtype, color, formality FROM wardrobe_items ORDER BY created_at DESC LIMIT 3;"`

### Verify the Agent / Tool Calls

1. Make sure there are items in the wardrobe (add them first or check existing ones).
2. Go to the Outfits tab, type "I need a casual outfit for college today", click "Get outfits →".
3. **Watch the terminal** — every tool call is printed:
   ```
   --- Agent round 0 ---
   🔧 TOOL CALL  [round 0]: get_weather({'location': ''})
   ✅ TOOL RESULT [get_weather]: {'location': 'Chennai', ...}
   --- Agent round 1 ---
   🔧 TOOL CALL  [round 1]: get_wardrobe_state({'filters': '{"status":"clean"}'})
   ✅ TOOL RESULT [get_wardrobe_state]: {'items': [...], 'total_count': 17}
   ...
   💬 FINAL TEXT at round 4 (1247 chars)
   ```
4. The UI shows the agent processing checklist in real time, then the outfit cards.

### Verify Guardrail 2 (Validation Enforcement)

If the model tries to skip validation, you will see this in the terminal:
```
⚠️  VALIDATION GUARD: Final response contains item_ids but no validation ran. Forcing validation check.
```
This is printed inside the `chat()` loop in `stylist_agent.py` whenever Guardrail 2 fires. It means the loop injected a correction and continued — the final response the user sees will have been through validation.

### Verify Cross-Session Memory

1. Go to Outfits, get outfit suggestions.
2. Click "Change something" → click any chip (e.g. "No blazer").
3. Go to Profile tab → scroll to "Saved preferences" — "No blazer" should appear.
4. Close the app, reopen, go to Outfits, get a new suggestion.
5. The agent's first response should account for the preference (or you can verify it's in the system prompt by adding a print statement to `_system_prompt()` in `stylist_agent.py`).

### Verify the Knowledge Retrieval

Open a Python shell:
```python
from src.knowledge.retrieval import retrieve_styling_guidance
results = retrieve_styling_guidance("pairing grey shirt with black trousers for office", top_k=3)
for r in results:
    print(f"[{r['score']:.3f}] [{r['category']}] {r['text'][:80]}")
```
Expected: top results will be from `formality` and `color` categories, with relevance scores around 0.2–0.5.

### Run the Evaluation

```bash
python -m src.eval.run_eval
```

The eval:
1. Runs all 8 scenarios in order.
2. Prints each tool call trace to the terminal as it runs.
3. Writes `eval_results.json` with per-scenario results and aggregate metrics.
4. Prints the summary table at the end:
   ```json
   {
     "total_scenarios": 8,
     "tool_call_correctness_rate": 0.875,
     "validation_executed_rate": 1.0,
     "zero_hallucination_rate": 1.0,
     "failure_cases_recovered": ["S4"],
     "errors": []
   }
   ```

**What each metric means:**
- `tool_call_correctness_rate`: Did the agent call the right tools and avoid forbidden ones? (1.0 = perfect)
- `validation_executed_rate`: Did `check_outfit_validity` run in every scenario? (1.0 = Guardrail 2 is working)
- `zero_hallucination_rate`: Did every item_id in the response exist in the real database? (1.0 = no invented items)
- `failure_cases_recovered`: Which engineered-failure scenarios ended in graceful recovery?

---

## 17. Key Design Decisions

### One Agent, Five Tools — Not Multi-Agent

All reasoning is done by a single Gemini model instance with five callable tools. Multi-agent architectures (where a planner delegates to sub-agents) were considered but rejected because:
- A single agent has access to the full context at every step — no message passing needed.
- Simpler to debug: one set of tool traces, one reasoning loop.
- For this problem scope (outfit recommendation), multi-agent would add coordination overhead with no benefit.

### Direct `google.genai` SDK — Not LangChain

The live agent uses `google.genai` directly. `tools_def.py` with LangChain `@tool` decorators exists as a legacy artifact. LangChain's Google integration (`langchain-google-genai`) was hanging on this environment during development. The direct SDK gives full control over the tool-call loop, which is what makes the guardrail enforcement possible.

### Manual Tool-Call Loop — Not Automatic Function Calling

`automatic_function_calling=disabled` is set explicitly. With auto-calling:
- The app cannot inspect what tools were called (needed for eval).
- Guardrail 2 (forced validation) cannot be injected between rounds.
- Error handling per tool is not possible.

The manual loop trades a few lines of code for complete observability and control.

### TF-IDF — Not Embedding API

The knowledge retrieval uses a pure-Python TF-IDF implementation. Embedding APIs (like `gemini-embedding-001`) would give better semantic retrieval but add network calls and rate-limit exposure. For a 30-entry knowledge base of narrowly-scoped styling text, TF-IDF retrieval quality is sufficient. The trade-off is documented in `retrieval.py`.

### SQLite — Not a Cloud Database

Local SQLite is appropriate for a single-user, local-first prototype. No server infrastructure, no authentication, no internet required for the database. Images never leave the user's machine. The schema is multi-user ready (every row has `user_id`) but only `"default_user"` is used.

### Profile as JSON File — Not a Database Table

User profile (name, email, location, style notes) is stored in `data/profile.json`. This keeps it human-readable and editable without a database client. The profile is small and rarely changes, so a flat JSON file is appropriate.

### Pydantic for Vision Output Validation

Gemini is instructed to return JSON only. Pydantic validates the schema before anything reaches the database. Invalid categories, out-of-range formality values, and bad status strings are all caught at the boundary. This means the database always contains valid, structured data regardless of what the vision model returns.

---

## 18. Known Issues and Limitations

### `tools_def.py` is a Dead File

`src/agent/tools_def.py` imports `from langchain_core.tools import tool`. If LangChain is not installed, importing this file raises `ImportError`. The live agent never imports it, but any script that does `from src.agent.tools_def import ALL_TOOLS` will fail if LangChain is not in the environment. This file should either be removed or have its import made conditional.

### `profile_tab.py` Has a Bug in the Preferences Section

`src/ui/profile_tab.py` calls `get_preference_notes()` in the `_prefs_html` function. This function does not exist in `preferences.py` — the correct function name is `get_recent_preferences()`. This raises a `NameError` at runtime when the preferences section of the profile tab is rendered. The fix is a one-line rename in `profile_tab.py`.

### Model Names Are Out of Date in Config

`src/config.py` defaults to `gemini-2.0-flash`. The `.env` file currently sets `gemini-1.5-flash`. Both are deprecated. Update `.env` to a current `3.x` model:
```
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_VISION_MODEL=gemini-3.5-flash-lite
```
`gemini-3.5-flash-lite` is multimodal, available on the free API tier, and gives ~500 requests/day.

### Eval S4 Teardown Is Fragile

`_restore_footwear()` in `scenarios.py` only restores `item_45a66a29` to `"flats"`. If the real wardrobe has different footwear items or `item_45a66a29` doesn't exist, the teardown silently does nothing and the database is left with all footwear as `"chappal"`. The teardown should restore all footwear subtypes, not just one specific item.

### Season Filter is Post-Query

The `season` filter in `query_items` is done in Python after fetching all items (because `season` is stored as a JSON list in a TEXT column). For large wardrobes this is inefficient. For the current prototype scale (tens of items) it has no practical impact.

### No Real Authentication

The app is single-user with `user_id = "default_user"` hardcoded everywhere. Running on a LAN (port 7860, `server_name="0.0.0.0"`) means anyone on the same network can access it. This is fine for local personal use but is not production-ready.

### Preference Notes Accumulate Without Limit

Notes written to `user_preferences` are never deleted. The `get_recent_preferences(limit=5)` cap means only 5 are injected into the prompt, but the table grows forever. For a real app, old notes should be pruned or the user should be able to clear them.

### `stylist_tab.py` Is Never Mounted

`src/ui/stylist_tab.py` is a fully functional chat UI but is not imported or used anywhere in `app.py`. It can be removed or re-added as a debug/developer tab.

---

*Last updated to reflect: Gemini 3.x model migration requirement, manual tool-call loop architecture, guardrail enforcement details, eval framework operation, cross-session memory implementation, and all current UI tabs as built.*
