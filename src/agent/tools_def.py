"""
LangChain Tool definitions that wrap the CloseCall tool functions.
These are passed to the LangChain agent executor.
"""

import json
from langchain_core.tools import tool

from src.tools.weather import get_weather as _get_weather
from src.tools.wardrobe import get_wardrobe_state as _get_wardrobe_state
from src.tools.validation import check_outfit_validity as _check_outfit_validity


@tool
def get_weather(location: str = "") -> str:
    """
    Fetch current weather for a city or location.
    Use this when weather context is needed to recommend an appropriate outfit.

    Args:
        location: City name (e.g. "Mumbai", "Delhi"). Leave empty to use the default location.

    Returns:
        JSON string with weather data including condition, temperature, and is_raining flag.
    """
    result = _get_weather(location or None)
    return json.dumps(result, indent=2)


@tool
def get_wardrobe_state(filters: str = "{}") -> str:
    """
    Query the user's wardrobe database for items matching the specified filters.
    Always call this before generating outfit candidates.

    Args:
        filters: A JSON string with optional filter keys:
                   "status"        - "clean" or "dirty"
                   "category"      - "top", "bottom", "one_piece", "footwear", "outerwear"
                   "categories"    - list of categories e.g. ["top", "bottom", "footwear"]
                   "min_formality" - integer 1-5
                   "max_formality" - integer 1-5
                   "rain_suitable" - true or false
                   "season"        - "summer", "winter", "monsoon", "spring", "all-season"

    Returns:
        JSON string with a list of matching wardrobe items and their metadata.
    """
    try:
        filter_dict = json.loads(filters) if filters.strip() else {}
    except json.JSONDecodeError:
        filter_dict = {}

    result = _get_wardrobe_state(user_id="default_user", filters=filter_dict)
    return json.dumps(result, indent=2)


@tool
def check_outfit_validity(outfit_json: str, constraints_json: str = "{}") -> str:
    """
    Validate a candidate outfit against the current request constraints.
    Call this for EVERY candidate outfit before recommending it.

    Args:
        outfit_json:      JSON string — a list of wardrobe item dicts (from get_wardrobe_state).
        constraints_json: JSON string — constraint dict with keys:
                            "occasion"      - e.g. "office", "casual", "party"
                            "is_raining"    - true/false
                            "min_formality" - integer 1-5
                            "max_formality" - integer 1-5

    Returns:
        JSON string with validation result: valid (bool), passed list, failed list, diagnosis.
    """
    try:
        outfit = json.loads(outfit_json)
    except (json.JSONDecodeError, TypeError):
        outfit = []

    try:
        constraints = json.loads(constraints_json)
    except (json.JSONDecodeError, TypeError):
        constraints = {}

    result = _check_outfit_validity(outfit=outfit, constraints=constraints)
    return json.dumps(result, indent=2)


@tool
def ask_user_clarification(question: str) -> str:
    """
    Ask the user a targeted clarifying question when the agent cannot automatically
    resolve a missing or conflicting constraint.

    Use this when:
    - No outfit satisfies all hard constraints and no soft constraint can be relaxed.
    - Critical information is missing (e.g. preferred formality, specific occasion details).

    Args:
        question: The clarifying question to ask the user.

    Returns:
        A string indicating the question has been surfaced to the user.
    """
    # This tool surfaces the question — the Gradio UI captures the return value
    # and presents it as the agent's response, prompting the user to reply.
    return f"CLARIFICATION_NEEDED: {question}"


# Exported list for the agent executor
ALL_TOOLS = [get_weather, get_wardrobe_state, check_outfit_validity, ask_user_clarification]
