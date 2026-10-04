"""
check_outfit_validity tool.

Hard-rule validator that checks a candidate outfit against the current
request constraints before the agent shows it to the user.
"""

from __future__ import annotations

import json
from typing import Any


# ─── Footwear compatibility rules ────────────────────────────────────────────

# (occasion_keyword, min_formality) → rejected footwear subtypes
_FOOTWEAR_REJECTION_RULES: list[tuple[set[str], int, set[str]]] = [
    # Formal office: chappal and sandals are never acceptable
    ({"formal", "office"}, 4, {"chappal", "sandals"}),
    # Any office: chappal rejected
    ({"office"}, 1, {"chappal"}),
]

# Subtypes that are not rain-suitable by default
_NOT_RAIN_SUITABLE_FOOTWEAR = {"formal_shoes", "sneakers", "flats", "chappal", "sandals"}

# Required categories for a complete outfit (at minimum)
_REQUIRED_CATEGORIES = {"top", "bottom", "footwear"}   # one_piece can replace top+bottom
_ONE_PIECE_CATEGORIES = {"one_piece"}


def check_outfit_validity(
    outfit: list[dict] | str,
    constraints: dict | str,
) -> dict:
    """
    Validate a candidate outfit against the current request constraints.

    Args:
        outfit:      List of wardrobe item dicts (as returned by get_wardrobe_state).
                     May also be a JSON string.
        constraints: Dict of request constraints:
                       occasion      str   e.g. "office", "casual", "formal"
                       is_raining    bool
                       min_formality int   1–5
                       max_formality int   1–5

    Returns:
        dict with:
            valid         bool
            passed        list[str]   rules that passed
            failed        list[str]   rules that failed (with reasons)
            diagnosis     str         human-readable summary
    """
    # Parse JSON strings (LLM may pass these as strings)
    if isinstance(outfit, str):
        try:
            outfit = json.loads(outfit)
        except (json.JSONDecodeError, TypeError):
            outfit = []

    if isinstance(constraints, str):
        try:
            constraints = json.loads(constraints)
        except (json.JSONDecodeError, TypeError):
            constraints = {}

    outfit = outfit or []
    constraints = constraints or {}

    passed: list[str] = []
    failed: list[str] = []

    # ── 1. All items must be clean ────────────────────────────────────────────
    dirty = [
        f"{i.get('color','')} {i.get('subtype','')} [{i.get('item_id','')}]"
        for i in outfit
        if i.get("status", "clean") == "dirty"
    ]
    if dirty:
        failed.append(f"Dirty items in outfit: {', '.join(dirty)}")
    else:
        passed.append("All items are clean")

    # ── 2. Category completeness ──────────────────────────────────────────────
    cats = {i.get("category", "") for i in outfit}
    has_one_piece = "one_piece" in cats
    has_top = "top" in cats
    has_bottom = "bottom" in cats
    has_footwear = "footwear" in cats

    if not has_footwear:
        failed.append("No footwear in outfit")
    else:
        passed.append("Footwear present")

    if not has_one_piece and not (has_top and has_bottom):
        failed.append("Outfit is incomplete: needs either a one_piece or both a top and a bottom")
    else:
        passed.append("Outfit has complete top/bottom coverage")

    # ── 3. Formality range ────────────────────────────────────────────────────
    min_f = constraints.get("min_formality")
    max_f = constraints.get("max_formality")

    if min_f is not None or max_f is not None:
        for item in outfit:
            f = item.get("formality", 3)
            label = f"{item.get('color','')} {item.get('subtype','')} [{item.get('item_id','')}]"
            if min_f is not None and f < min_f:
                failed.append(
                    f"{label} is too casual (formality {f}, need ≥{min_f})"
                )
            elif max_f is not None and f > max_f:
                failed.append(
                    f"{label} is too formal (formality {f}, need ≤{max_f})"
                )
            else:
                passed.append(f"{label} formality OK ({f})")

    # ── 4. Rain suitability ───────────────────────────────────────────────────
    is_raining = constraints.get("is_raining", False)
    if is_raining:
        for item in outfit:
            label = f"{item.get('color','')} {item.get('subtype','')} [{item.get('item_id','')}]"
            if not item.get("rain_suitable", False):
                # Footwear: hard fail
                if item.get("category") == "footwear":
                    failed.append(
                        f"Footwear {label} is not rain-suitable"
                    )
                # Tops/bottoms: soft warning only (outer layer may protect)
                else:
                    passed.append(
                        f"{label} is not rain-resistant but may be protected by outerwear"
                    )
            else:
                passed.append(f"{label} is rain-suitable")

    # ── 5. Footwear / occasion compatibility ──────────────────────────────────
    occasion = (constraints.get("occasion") or "").lower()
    footwear_items = [i for i in outfit if i.get("category") == "footwear"]

    for item in footwear_items:
        subtype = (item.get("subtype") or "").lower()
        formality = item.get("formality", 3)
        label = f"{item.get('color','')} {subtype} [{item.get('item_id','')}]"

        rejected = False
        for occ_keywords, min_occ_f, rejected_subtypes in _FOOTWEAR_REJECTION_RULES:
            occ_match = any(kw in occasion for kw in occ_keywords)
            if occ_match and subtype in rejected_subtypes:
                failed.append(
                    f"Footwear {label} is not appropriate for {occasion} ('{subtype}' not allowed)"
                )
                rejected = True
                break

        if not rejected:
            passed.append(f"Footwear {label} is acceptable for occasion")

    # ── 6. Build diagnosis ────────────────────────────────────────────────────
    valid = len(failed) == 0

    if valid:
        diagnosis = "Outfit passes all validation checks."
    else:
        diagnosis = "Outfit failed validation. Issues: " + "; ".join(failed)

    return {
        "valid": valid,
        "passed": passed,
        "failed": failed,
        "diagnosis": diagnosis,
    }
