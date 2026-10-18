"""Problem 8: run the final defended vendor desk agent on every exam document.

    python run_exam.py

Uses the agent exactly as `python agent.py --doc ...` runs it by default: gpt-6-luna through
Portkey, all three defense levels on (code, design, prompt), only the handbook cached. Writes
output/exam_results.json with one entry per file in data/exam_docs/. Normal per-run logging
(usage_log.json, audit_trail.json, trap_calls.json) still happens through agent.run().
"""

from __future__ import annotations

import json
from pathlib import Path

import tools
from agent import build_usage, run

ROOT = Path(__file__).resolve().parent
EXAM_DIR = ROOT / "data" / "exam_docs"
OUT = tools.OUTPUT_DIR / "exam_results.json"


def main() -> None:
    tools.ensure_trap_log()
    entries = []
    for doc in sorted(p for p in EXAM_DIR.iterdir() if p.is_file() and not p.name.startswith(".")):
        document = str(doc.relative_to(ROOT))
        traps_before = len(json.loads(tools.TRAP_CALLS_PATH.read_text(encoding="utf-8")))
        answer, messages = run(document)  # all defenses on
        traps = json.loads(tools.TRAP_CALLS_PATH.read_text(encoding="utf-8"))[traps_before:]
        usage = build_usage(document, messages)
        entries.append({
            "file": doc.name,
            "vendor": answer.vendor,
            "sku": answer.sku,
            "unit_price": answer.unit_price,
            "lead_time_days": answer.lead_time_days,
            "min_order": answer.min_order,
            "decision": answer.decision,
            "reason": answer.reason,
            "trap_tool_called": bool(traps),
            "input_tokens": usage.input_tokens,
            "cached_tokens": usage.cached_input_tokens,
            "output_tokens": usage.output_tokens,
            "cost_usd": usage.cost_usd["total"],
        })
        e = entries[-1]
        print(f"{e['file']:20} {e['vendor']!s:28} {e['sku']!s:10} {e['unit_price']!s:>7} {e['lead_time_days']!s:>4} "
              f"{e['min_order']!s:>5} {e['decision']:17} trap={e['trap_tool_called']} ${e['cost_usd']:.6f}")
    OUT.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"total ${sum(e['cost_usd'] for e in entries):.6f} for {len(entries)} documents")


if __name__ == "__main__":
    main()
