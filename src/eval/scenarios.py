"""
Fixed evaluation scenarios for CloseCall's agentic reasoning loop.
Each scenario optionally has setup/teardown to manipulate DB state
(e.g. forcing a genuine failure case) before/after the request runs.
"""

from src.database.db import get_session
from src.database.models import WardrobeItem


def _set_all_footwear_subtype(subtype: str):
    with get_session() as session:
        session.query(WardrobeItem).filter_by(category='footwear').update({"subtype": subtype})


def _restore_footwear():
    # Adjust to your actual seed values if different
    with get_session() as session:
        session.query(WardrobeItem).filter_by(
            category='footwear', item_id='item_45a66a29'
        ).update({"subtype": "flats"})


def _mark_all_dirty():
    with get_session() as session:
        session.query(WardrobeItem).update({"status": "dirty"})


def _restore_all_clean():
    with get_session() as session:
        session.query(WardrobeItem).update({"status": "clean"})


SCENARIOS = [
    {
        "id": "S1",
        "name": "Happy path — casual request, no weather stated",
        "request": "I need a casual outfit for college today.",
        "setup": None, "teardown": None,
        "expect_tool_calls": ["get_weather", "get_wardrobe_state", "check_outfit_validity"],
    },
    {
        "id": "S2",
        "name": "Weather already stated — should skip get_weather",
        "request": "I need a casual outfit, it's sunny and 28 degrees.",
        "setup": None, "teardown": None,
        "expect_tool_calls": ["get_wardrobe_state", "check_outfit_validity"],
        "expect_no_call": "get_weather",
    },
    {
        "id": "S3",
        "name": "Formal office request against real wardrobe",
        "request": "I need a formal outfit for an important office meeting.",
        "setup": None, "teardown": None,
        "expect_tool_calls": ["get_wardrobe_state", "check_outfit_validity"],
    },
    {
        "id": "S4",
        "name": "Forced footwear failure — only chappals available, office request",
        "request": "I need an outfit for work today.",
        "setup": lambda: _set_all_footwear_subtype("chappal"),
        "teardown": _restore_footwear,
        "expect_tool_calls": ["get_wardrobe_state", "check_outfit_validity"],
        "expect_validation_failure": True,
    },
    {
        "id": "S5",
        "name": "Forced total failure — entire wardrobe marked dirty",
        "request": "I need a casual outfit for today.",
        "setup": _mark_all_dirty,
        "teardown": _restore_all_clean,
        "expect_tool_calls": ["get_wardrobe_state"],
        "expect_clarification_or_explained_failure": True,
    },
    {
        "id": "S6",
        "name": "Style/color judgment — should trigger retrieval tool",
        "request": "I have a casual date tonight, suggest something stylish.",
        "setup": None, "teardown": None,
        "expect_tool_calls": ["get_wardrobe_state", "check_outfit_validity"],
    },
    {
        "id": "S7",
        "name": "Rainy weather stated explicitly",
        "request": "It's raining heavily, I need an outfit for college.",
        "setup": None, "teardown": None,
        "expect_tool_calls": ["get_wardrobe_state", "check_outfit_validity"],
    },
    {
        "id": "S8",
        "name": "Ambiguous occasion — vague request",
        "request": "What should I wear?",
        "setup": None, "teardown": None,
        "expect_tool_calls": ["get_wardrobe_state"],
    },
]