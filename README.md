# CloseCall — AI Personal Stylist

An agentic AI outfit recommender that reasons over your real wardrobe. Built as a Foundations of Agentic AI mini project.

---

## What it does

You describe what you need in plain language — *"casual office outfit, it's raining"* — and CloseCall:

1. Fetches live weather if you haven't stated it
2. Queries your wardrobe database for matching items
3. Generates 2–3 candidate outfit combinations
4. Validates each one against hard rules (clean, complete, occasion-appropriate footwear, rain suitability)
5. Returns vetted recommendations with a reasoning explanation — or diagnoses why nothing worked

The key design: every recommendation is validated by code before it reaches you. The agent cannot recommend an outfit it hasn't checked.

---

## Demo

![Home screen](data/images/item_d66a1785.jpg)

Run locally at `http://localhost:7860` — also accessible on your phone via the Wi-Fi IP printed at startup.

---

## Architecture

Single reasoning agent with five tools:

| Tool | Purpose |
|---|---|
| `get_weather` | Live weather from OpenWeatherMap |
| `get_wardrobe_state` | Query wardrobe DB with filters |
| `check_outfit_validity` | Deterministic rule-based validator |
| `retrieve_styling_guidance` | TF-IDF retrieval over 30-entry styling knowledge base |
| `ask_user_clarification` | Returns control to user when constraints can't be resolved |

The agent decides which tools to call and in what order at runtime. Tool calls are not hardcoded.

---

## Setup

### 1. Clone

```bash
git clone https://github.com/Meekio/closecall.git
cd closecall
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_key_here          # https://aistudio.google.com
OPENWEATHER_API_KEY=your_key_here     # https://openweathermap.org/api
DEFAULT_LOCATION=Chennai              # Your city
```

Both APIs have free tiers sufficient for this project.

### 4. Run

```bash
python app.py
```

Open `http://localhost:7860` in your browser.

---

## Project structure

```
closecall/
├── app.py                        # Entry point, Gradio app
├── requirements.txt
├── data/
│   ├── closecall.db              # SQLite wardrobe database
│   ├── images/                   # Uploaded clothing photos
│   └── profile.json              # User profile and location
└── src/
    ├── agent/
    │   ├── stylist_agent.py      # Reasoning loop, tool dispatch
    │   ├── guardrails.py         # Safety guardrails
    │   ├── prompts.py            # System prompt
    │   └── tools_def.py          # Tool function definitions
    ├── database/
    │   ├── db.py                 # DB connection and queries
    │   ├── models.py             # SQLAlchemy models
    │   ├── preferences.py        # Long-term user memory
    │   └── profile.py            # Profile management
    ├── eval/
    │   ├── run_eval.py           # Evaluation harness
    │   └── scenarios.py          # 8 fixed test scenarios
    ├── knowledge/
    │   ├── styling_kb.py         # 30-entry styling knowledge base
    │   └── retrieval.py          # Local TF-IDF retrieval
    ├── tools/
    │   ├── validation.py         # Outfit validation logic
    │   ├── wardrobe.py           # Wardrobe query tools
    │   └── weather.py            # OpenWeatherMap integration
    ├── ui/                       # Gradio tab builders
    └── vision/
        ├── tagger.py             # Gemini vision tagging
        └── uploader.py           # Image upload and storage
```

---

## Running the evaluation harness

```bash
python -m src.eval.run_eval
```

Runs 8 fixed scenarios including engineered failures (all footwear set to chappal, entire wardrobe marked dirty) and writes results to `eval_results.json`.

---

## Guardrails

Five explicit guardrails enforced in code, not just prompt:

1. **Bounded reasoning loop** — max 10 rounds, no runaway tool-calling
2. **Mandatory validation** — agent cannot return a recommendation without calling `check_outfit_validity` first
3. **Zero hallucination enforcement** — every item ID in the response is checked against the real database
4. **Hard vs soft constraints** — clean status, category completeness, and footwear rules are enforced deterministically; formality and colour preferences are soft
5. **Location grounding** — weather lookups always use the saved profile location, never text extracted from the request

---

## Tech stack

| Component | Technology |
|---|---|
| Reasoning model | Google Gemini 1.5 Flash |
| Vision tagging | Google Gemini 1.5 Flash |
| Agent SDK | `google-genai` (native function calling) |
| UI | Gradio |
| Database | SQLite + SQLAlchemy |
| Knowledge retrieval | Local TF-IDF (no external embedding API) |
| Weather | OpenWeatherMap API |
| Language | Python 3.12 |

---

## Memory

**Short-term:** Full conversation history passed back to the model on every turn within a session. Enables reject-and-refine — say "not that, try something without jeans" and the agent updates without starting over.

**Long-term:** Refinement notes persisted to `user_preferences` table in SQLite. Injected into the system prompt at session start so past preferences ("no blazers") influence future recommendations automatically.
