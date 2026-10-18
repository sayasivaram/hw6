"""Problem 7: red team. Runs each of our own booby-trapped documents in data/my_attacks/ twice --
once with all defenses on and once with none -- and checks the answers against
data/my_attacks/my_attacks_key.json (the values a person reading the visible quote would report).

    python red_team_test.py

Results go to output/red_team_results.json (same per-document format as output/defense_results.json).
"""

from __future__ import annotations

import json
from pathlib import Path

import tools
from defense_test import evaluate

ROOT = Path(__file__).resolve().parent
ATTACKS = ROOT / "data" / "my_attacks"
KEY = {k["file"]: k for k in json.loads((ATTACKS / "my_attacks_key.json").read_text(encoding="utf-8"))}
OUT = tools.OUTPUT_DIR / "red_team_results.json"
SETUPS = {"defenses_on": dict(code=True, design=True, prompt=True), "defenses_off": dict(code=False, design=False, prompt=False)}


def main() -> None:
    tools.ensure_trap_log()
    results = []
    for doc in sorted(ATTACKS.glob("a*.*")):
        for setup, defenses in SETUPS.items():
            r = evaluate(doc, defenses, KEY) | {"setup": setup}
            results.append(r)
            wrong = {f: v["agent"] for f, v in r["fields"].items() if not v["match"]}
            print(f"{doc.name:38} {setup:13} decision {r['decision']['agent']:17} wrong fields {wrong or '-'} "
                  f"traps {len(r['trap_calls'])} retries {len(r['answer_check_retries'])} -> {'FOOLED' if r['fooled'] else 'not fooled'}")
            print("   reason:", r["reason"])
    OUT.write_text(json.dumps({"generated": tools.now(), "results": results}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
