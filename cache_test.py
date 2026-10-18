"""Problem 4: run the vendor desk agent with and without prompt caching and record every model call.

    python cache_test.py

Setups (same agent, same documents, same prompt text):
- cache:    only the handbook is reused from the cache. The handbook is sent first as its own
            message with a cache breakpoint; the instructions after it open with a fresh request ID
            on every call, so nothing past the handbook ever matches an earlier call.
- no_cache: no cache breakpoint at all, and the request ID sits in the same block as the handbook,
            so nothing is reused.

Every model call is saved to output/cache_test.json with its setup, document, the token counts
the API reported, and dollar cost from data/prices.json. Normal per-run logging (usage_log.json,
audit_trail.json, trap_calls.json) still happens through agent.run().

Note: output/cache_test.* were produced before Problem 6 added the defenses. agent.run() now has all
defenses on by default, so re-running this script uses the defended agent (one extra tool, so about
10,487 cached tokens per call instead of 10,484, and slightly different costs).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic_ai.messages import ModelResponse

import tools
from agent import MODEL_NAME, run

ROOT = Path(__file__).resolve().parent
DOCS = sorted((ROOT / "data" / "practice_docs").iterdir())
KEY = {k["file"]: k for k in json.loads((ROOT / "data" / "practice_key.json").read_text(encoding="utf-8"))}
OUT = tools.OUTPUT_DIR / "cache_test.json"


def call_record(setup: str, document: str, number: int, response: ModelResponse) -> dict:
    u = response.usage
    cached, written = u.cache_read_tokens or 0, u.cache_write_tokens or 0
    uncached = u.input_tokens - cached - written
    return {
        "setup": setup,
        "document": document,
        "call": number,
        "model": response.model_name,
        "input_tokens": u.input_tokens,
        "cached_input_tokens": cached,
        "cache_write_tokens": written,
        "uncached_input_tokens": uncached,
        "output_tokens": u.output_tokens,
        "reasoning_tokens": (u.details or {}).get("reasoning_tokens", 0),
        "cost_usd": tools.price_tokens(uncached, cached, written, u.output_tokens, MODEL_NAME),
    }


def summarize(calls: list[dict], runs: list[dict]) -> dict:
    total = lambda field: sum(c[field] for c in calls)  # noqa: E731
    cost = sum(c["cost_usd"]["total"] for c in calls)
    return {
        "documents": len(runs),
        "model_calls": len(calls),
        "input_tokens": total("input_tokens"),
        "cached_input_tokens": total("cached_input_tokens"),
        "cache_write_tokens": total("cache_write_tokens"),
        "uncached_input_tokens": total("uncached_input_tokens"),
        "output_tokens": total("output_tokens"),
        "reasoning_tokens": total("reasoning_tokens"),
        "cost_usd": {
            part: round(sum(c["cost_usd"][part] for c in calls), 8)
            for part in ("uncached_input", "cached_input", "cache_write", "output", "total")
        },
        "cost_per_document_usd": round(cost / len(runs), 8),
        "decisions_matching_practice_key": sum(r["matches_key"] for r in runs),
    }


def main() -> None:
    traps_before = len(json.loads(tools.TRAP_CALLS_PATH.read_text(encoding="utf-8"))) if tools.TRAP_CALLS_PATH.exists() else 0
    calls: list[dict] = []
    runs: list[dict] = []
    for setup in ("cache", "no_cache"):
        for doc in DOCS:
            document = str(doc.relative_to(ROOT))
            answer, messages = run(document, no_cache=setup == "no_cache")
            responses = [m for m in messages if isinstance(m, ModelResponse)]
            calls += [call_record(setup, document, i, r) for i, r in enumerate(responses, 1)]
            runs.append({"setup": setup, "document": document, "decision": answer.decision,
                         "matches_key": answer.decision == KEY[doc.name]["decision"]})
            print(f"{setup:9} {doc.name:30} {len(responses)} calls  {answer.decision}")

    report = {
        "generated": tools.now(),
        "model": MODEL_NAME,
        "prices_per_1m": json.loads(tools.PRICES_PATH.read_text(encoding="utf-8"))[MODEL_NAME],
        "summary": {s: summarize([c for c in calls if c["setup"] == s], [r for r in runs if r["setup"] == s])
                    for s in ("cache", "no_cache")},
        "trap_calls_during_test": len(json.loads(tools.TRAP_CALLS_PATH.read_text(encoding="utf-8"))) - traps_before,
        "runs": runs,
        "calls": calls,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print("trap calls during test:", report["trap_calls_during_test"])


if __name__ == "__main__":
    main()
