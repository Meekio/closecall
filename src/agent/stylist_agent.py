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


# ─── Tool function implementations passed to Gemini ──────────────────────────

def get_weather(location: str = "") -> dict:
    """
    Fetch current weather for a city or location.
    Use this when weather context is needed to recommend an appropriate outfit.
    location: City name e.g. 'Mumbai', 'Delhi'. Leave empty for default location.
    Returns JSON with weather data including condition, temperature, and is_raining flag.
    """
    return _get_weather(location or None)


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


# All tools exported for Gemini
_ALL_TOOL_FUNCTIONS = [
    get_weather,
    get_wardrobe_state,
    check_outfit_validity,
    ask_user_clarification,
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
    """

    MAX_ROUNDS = 10

    def __init__(self, user_id: str = "default_user") -> None:
        self.user_id = user_id
        self._history: list[genai_types.Content] = []
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)

    def _system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def chat(self, user_message: str) -> str:
        """Send a message and return the agent's text response."""

        # Append user message to history
        self._history.append(
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

        for _round in range(self.MAX_ROUNDS):
            print(f"\n--- Agent round {_round} ---")
            response = self._client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=self._history,
                config=gen_config,
            )

            candidate = response.candidates[0]
            content = candidate.content   # Content(role="model", parts=[...])

            # Add model turn to history
            self._history.append(content)

            # Check if there are function calls to execute
            function_calls = [
                p.function_call
                for p in content.parts
                if p.function_call is not None
            ]

            if not function_calls:
                # No tool calls — extract final text
                text_parts = [
                    p.text for p in content.parts
                    if hasattr(p, "text") and p.text
                ]
                response_text = "\n".join(text_parts).strip()
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
            self._history.append(
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
        if len(self._history) > 20:
            self._history = self._history[-20:]

        return response_text

    def reset_session(self) -> None:
        self._history = []


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
