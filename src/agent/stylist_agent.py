"""
CloseCall Reasoning Agent.

Uses the google.genai SDK directly (same transport as the vision tagger)
with native function/tool calling, bypassing langchain-google-genai which
hangs on this environment's network stack.

Maintains per-session conversation history for feedback adaptation.
"""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types as genai_types

from src.config import config
from src.agent.prompts import SYSTEM_PROMPT
from src.tools.weather import get_weather as _get_weather
from src.tools.wardrobe import get_wardrobe_state as _get_wardrobe_state
from src.tools.validation import check_outfit_validity as _check_outfit_validity
from src.knowledge.retrieval import retrieve_styling_guidance as _retrieve_styling_guidance
from src.agent.guardrails import MAX_REASONING_ROUNDS, ENFORCE_VALIDATION_BEFORE_FINAL_ANSWER


# ─── Tool function implementations passed to Gemini ──────────────────────────

def get_weather(location: str = "") -> dict:
    """
    Fetch current weather for the user's location.
    Use this when weather context is needed to recommend an appropriate outfit.
    location: Optional override location. If empty, uses user's profile location.
    Returns JSON with weather data including condition, temperature, and is_raining flag.
    """
    # Always use profile location, ignore model's guessed location parameter
    from src.database.profile import load_profile
    profile = load_profile()
    trusted_location = profile.get("location", "Chennai")  # ignore model-provided value
    return _get_weather(trusted_location)


def get_wardrobe_state(filters: str = "{}") -> dict:
    """
    Query the user's wardrobe database for items matching the specified filters.
    Always call this before generating outfit candidates.
    filters: JSON string with optional keys: status, category, categories,
             min_formality, max_formality, rain_suitable, season.
    Returns list of matching wardrobe items with their metadata.
    """
    try:
        filter_dict = json.loads(filters) if filters.strip() else {}
    except json.JSONDecodeError:
        filter_dict = {}
    return _get_wardrobe_state(user_id="default_user", filters=filter_dict)


def check_outfit_validity(outfit_json: str, constraints_json: str = "{}") -> dict:
    """
    Validate a candidate outfit against the current request constraints.
    Call this for EVERY candidate outfit before recommending it.
    outfit_json: JSON list of wardrobe item dicts from get_wardrobe_state.
    constraints_json: JSON dict with keys: occasion, is_raining, min_formality, max_formality.
    Returns validation result with valid bool, passed list, failed list, diagnosis.
    """
    try:
        outfit = json.loads(outfit_json)
    except (json.JSONDecodeError, TypeError):
        outfit = []
    try:
        constraints = json.loads(constraints_json)
    except (json.JSONDecodeError, TypeError):
        constraints = {}
    return _check_outfit_validity(outfit=outfit, constraints=constraints)


def ask_user_clarification(question: str) -> str:
    """
    Ask the user a clarifying question when the agent cannot automatically
    resolve a missing or conflicting constraint.
    question: The clarifying question to ask the user.
    """
    return f"CLARIFICATION_NEEDED: {question}"


def retrieve_styling_guidance(query: str) -> dict:
    """
    Retrieve relevant styling principles (color pairing, formality
    conventions, weather-appropriate fabric choices, silhouette
    balance) to justify a style or color decision.
    Call this when choosing between multiple valid outfits on style
    grounds, or when explaining a color/fabric choice in your reasoning.
    query: a short description of the styling decision, e.g.
           'pairing grey t-shirt with black trousers for office'.
    Returns the top matching guidance snippets with relevance scores.
    """
    results = _retrieve_styling_guidance(query, top_k=3)
    return {"guidance": [{"text": r["text"], "category": r["category"], "relevance": r["score"]} for r in results]}

# All tools exported for Gemini
_ALL_TOOL_FUNCTIONS = [
    get_weather,
    get_wardrobe_state,
    check_outfit_validity,
    ask_user_clarification,
    retrieve_styling_guidance,
]

# Map name → function for dispatch
_TOOL_MAP = {fn.__name__: fn for fn in _ALL_TOOL_FUNCTIONS}


# ─── Agent class ──────────────────────────────────────────────────────────────

class StylistAgent:
    """
    Agentic reasoning loop using Gemini native function calling.

    On each chat() call:
    1. Builds messages from session history + new user turn.
    2. Calls Gemini with tool definitions.
    3. If Gemini returns a function call, executes it and feeds the result back.
    4. Repeats until Gemini returns a final text response (max 10 rounds).
    5. Stores the turn in history.
    
    Memory: maintains short-term conversational memory (self.conversation_memory)
    scoped to a single session. This includes the full turn history — user
    requests, tool calls, tool results, and model responses — so that
    follow-up requests (e.g. outfit rejection + refinement) are resolved
    using prior context rather than treated as independent queries.
    Memory is trimmed to the last 20 Content objects to bound token usage,
    and is cleared entirely via reset_session() when the user starts a new
    styling conversation from scratch.
    """

    def __init__(self, user_id: str = "default_user") -> None:
        self.user_id = user_id
        self.conversation_memory: list[genai_types.Content] = []  # renamed from self._history
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.last_tool_calls: list[dict] = []  # Track tool calls for eval

    def _system_prompt(self) -> str:
        from src.database.preferences import get_recent_preferences
        prefs = get_recent_preferences(self.user_id)
        if prefs:
            pref_block = "\n\n## KNOWN USER PREFERENCES (from past sessions)\n" + \
                         "\n".join(f"- {p}" for p in prefs)
            return SYSTEM_PROMPT + pref_block
        return SYSTEM_PROMPT

    def chat(self, user_message: str) -> str:
        """Send a message and return the agent's text response."""

        # Reset tool call tracking for this chat turn
        self.last_tool_calls = []

        # Append user message to history
        self.conversation_memory.append(
            genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=user_message)],
            )
        )

        system_instruction = self._system_prompt()

        gen_config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=_ALL_TOOL_FUNCTIONS,
            temperature=0.3,
            automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(
                disable=True   # we handle the loop manually for full control
            ),
        )

        response_text = ""

        for _round in range(MAX_REASONING_ROUNDS):
            print(f"\n--- Agent round {_round} ---")
            response = self._client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=self.conversation_memory,
                config=gen_config,
            )

            candidate = response.candidates[0]
            content = candidate.content   # Content(role="model", parts=[...])

            # Add model turn to history
            self.conversation_memory.append(content)

            # Check if there are function calls to execute
            function_calls = [
                p.function_call
                for p in content.parts
                if p.function_call is not None
            ]

            if not function_calls:
                # No tool calls — extract final text and check validation requirement
                validity_was_called = any(
                    tc["tool"] == "check_outfit_validity" for tc in self.last_tool_calls
                )
                text_parts = [
                    p.text for p in content.parts if hasattr(p, "text") and p.text
                ]
                response_text = "\n".join(text_parts).strip()
                looks_like_recommendation = "item_" in response_text
                
                if (
                    ENFORCE_VALIDATION_BEFORE_FINAL_ANSWER
                    and looks_like_recommendation
                    and not validity_was_called
                    and _round < MAX_REASONING_ROUNDS - 1
                ):
                    # Guardrail 2: Force validation before accepting final answer
                    print(f"⚠️  VALIDATION GUARD: Final response contains item_ids but no validation ran. Forcing validation check.")
                    self.conversation_memory.append(
                        genai_types.Content(
                            role="user",
                            parts=[genai_types.Part.from_text(
                                text="You must call check_outfit_validity on your candidate outfit before giving a final answer. Please validate it now."
                            )],
                        )
                    )
                    continue  # loop again instead of accepting this as final
                
                print(f"💬 FINAL TEXT at round {_round} ({len(response_text)} chars)")
                break

            # Execute all function calls and collect results
            tool_result_parts = []
            for fc in function_calls:
                fn = _TOOL_MAP.get(fc.name)
                if fn is None:
                    result = {"error": f"Unknown tool: {fc.name}"}
                else:
                    try:
                        kwargs = dict(fc.args) if fc.args else {}
                        print(f"🔧 TOOL CALL  [round {_round}]: {fc.name}({kwargs})")
                        result = fn(**kwargs)
                        print(f"✅ TOOL RESULT [{fc.name}]: {result}")
                        
                        # Track for eval harness
                        self.last_tool_calls.append({
                            "round": _round,
                            "tool": fc.name,
                            "args": kwargs,
                            "result": result,
                        })
                    except Exception as exc:
                        result = {"error": str(exc)}
                        print(f"❌ TOOL ERROR  [{fc.name}]: {exc}")

                tool_result_parts.append(
                    genai_types.Part.from_function_response(
                        name=fc.name,
                        response=result if isinstance(result, dict) else {"result": str(result)},
                    )
                )

            # Feed tool results back as a "user" turn (Gemini's expected format)
            self.conversation_memory.append(
                genai_types.Content(
                    role="user",
                    parts=tool_result_parts,
                )
            )

        else:
            response_text = "I've completed my analysis but couldn't produce a final response. Please try again."

        if not response_text:
            response_text = "I couldn't generate a response. Please try again."

        # Trim history to last 20 Content objects to avoid token overflow
        if len(self.conversation_memory) > 20:
            self.conversation_memory = self.conversation_memory[-20:]

        return response_text

    def reset_session(self) -> None:
        self.conversation_memory = []


# ─── Module-level singleton ───────────────────────────────────────────────────

_agent_instance: StylistAgent | None = None


def get_agent(user_id: str = "default_user") -> StylistAgent:
    global _agent_instance
    if _agent_instance is None or _agent_instance.user_id != user_id:
        _agent_instance = StylistAgent(user_id=user_id)
    return _agent_instance


def reset_agent() -> None:
    global _agent_instance
    if _agent_instance:
        _agent_instance.reset_session()
