"""
Explicit guardrails for CloseCall's reasoning agent.
Centralizing these here — rather than leaving them implicit inside
stylist_agent.py and validation.py — makes them independently
auditable and citable, separate from the agent's reasoning logic.
"""

# Guardrail 1: bounded reasoning loop
# Prevents runaway tool-call loops or unbounded API cost from a
# single user request, regardless of what the model decides to do.
MAX_REASONING_ROUNDS = 10

# Guardrail 2: validation is mandatory, not advisory
# The agent's system prompt instructs it to validate every candidate,
# but an instruction alone is not a guardrail — it can be skipped
# (see eval scenario 7, where Flash-Lite skipped validation despite
# the instruction). This flag is enforced in code in stylist_agent.py:
# if no check_outfit_validity call occurred before a final answer
# that recommends an outfit, the agent is forced to loop again.
ENFORCE_VALIDATION_BEFORE_FINAL_ANSWER = True

# Guardrail 3: zero tolerance for invented wardrobe items
# Every item_id referenced in a final response must exist in the
# real wardrobe database. This is checked post-hoc by the eval
# harness (zero_hallucination_rate) and should also be checked live
# in production use — see check_response_grounding() below.
ALLOW_INVENTED_ITEMS = False

# Guardrail 4: hard constraints are enforced in code, never left to
# LLM judgment. check_outfit_validity in validation.py implements
# these as deterministic rules, independent of model behavior:
#   - all items must be status == "clean"
#   - footwear + (top+bottom OR one_piece) required
#   - occasion-based footwear rejection (e.g. chappal/sandals for office)
#   - rain_suitable required for footwear if is_raining
# A soft constraint (formality range, color, style) may be relaxed
# by the agent with an explanation; a hard constraint may not.

# Guardrail 5: location is never inferred from ambiguous model context
# get_weather must use the user's saved profile location, not a
# value the model extracts from the request text, to prevent
# grounding errors (see eval scenario 7, 'college' passed as a city).
TRUST_MODEL_FOR_LOCATION = False


def check_response_grounding(response_text: str, real_item_ids: set[str]) -> dict:
    """
    Guardrail check: verify every item_id mentioned in the agent's
    final response actually exists in the wardrobe database.
    Returns a dict reporting any violation — does not raise, so it
    can be used for both live logging and offline evaluation.
    """
    import re
    referenced = set(re.findall(r"item_[a-zA-Z0-9]+", response_text))
    hallucinated = referenced - real_item_ids
    return {
        "grounded": len(hallucinated) == 0,
        "referenced_ids": list(referenced),
        "hallucinated_ids": list(hallucinated),
    }