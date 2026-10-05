"""
Evaluation harness for CloseCall's agentic reasoning loop.
Runs fixed scenarios, captures real tool-call traces, computes
metrics, and writes a results table for the report.
"""

import re
import json
from datetime import datetime

from src.agent.stylist_agent import get_agent, reset_agent
from src.database.db import get_all_items
from src.eval.scenarios import SCENARIOS


def _extract_item_ids(text: str) -> set[str]:
    return set(re.findall(r"item_[a-f0-9]+", text))


def run_scenario(scenario: dict) -> dict:
    if scenario.get("setup"):
        scenario["setup"]()

    reset_agent()
    agent = get_agent()

    try:
        response = agent.chat(scenario["request"])
        error = None
    except Exception as exc:
        response = ""
        error = str(exc)

    tool_calls = agent.last_tool_calls

    if scenario.get("teardown"):
        scenario["teardown"]()

    tools_called = [tc["tool"] for tc in tool_calls]
    validity_results = [
        tc["result"] for tc in tool_calls if tc["tool"] == "check_outfit_validity"
    ]
    any_validation_failed = any(
        isinstance(r, dict) and r.get("valid") is False for r in validity_results
    )
    any_validation_passed = any(
        isinstance(r, dict) and r.get("valid") is True for r in validity_results
    )

    real_item_ids = {item["item_id"] for item in get_all_items()}
    referenced_ids = _extract_item_ids(response)
    hallucinated_ids = referenced_ids - real_item_ids

    correct_tool_use = True
    if "expect_no_call" in scenario and scenario["expect_no_call"] in tools_called:
        correct_tool_use = False
    for expected in scenario.get("expect_tool_calls", []):
        if expected not in tools_called:
            correct_tool_use = False

    recovered_from_failure = None
    if scenario.get("expect_validation_failure"):
        recovered_from_failure = any_validation_failed and (
            any_validation_passed or "CLARIFICATION_NEEDED" in response
        )

    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "request": scenario["request"],
        "error": error,
        "tools_called": tools_called,
        "validation_ran": len(validity_results) > 0,
        "any_validation_failed": any_validation_failed,
        "any_validation_passed": any_validation_passed,
        "hallucinated_ids": list(hallucinated_ids),
        "correct_tool_use": correct_tool_use,
        "recovered_from_failure": recovered_from_failure,
        "final_response_preview": response[:200],
    }


def run_all() -> list[dict]:
    return [run_scenario(s) for s in SCENARIOS]


def summarize(results: list[dict]) -> dict:
    n = len(results)
    return {
        "total_scenarios": n,
        "tool_call_correctness_rate": sum(r["correct_tool_use"] for r in results) / n,
        "validation_executed_rate": sum(r["validation_ran"] for r in results) / n,
        "zero_hallucination_rate": sum(len(r["hallucinated_ids"]) == 0 for r in results) / n,
        "failure_cases_recovered": [
            r["id"] for r in results if r.get("recovered_from_failure") is True
        ],
        "errors": [r["id"] for r in results if r["error"]],
    }


def write_report(results: list[dict], summary: dict, path: str = "eval_results.json"):
    with open(path, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "results": results, "summary": summary}, f, indent=2)
    print(f"\n Results written to {path}\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    results = run_all()
    summary = summarize(results)
    write_report(results, summary)