# Homework 6 — Campus Customs Vendor Desk Agent

An agent that reads a vendor document (HTML quote, PDF quote, or `.eml` email), applies the rules in `data/shop_handbook.md`, and returns vendor, SKU, unit price, lead time, minimum order, a decision (`recommend` / `do_not_recommend`), and a one-sentence reason. It uses **`gpt-6-luna` through Portkey only**.

## How to run the agent (from a fresh clone)

Everything the agent needs is in the repo: the handbook, prices, practice key, the 12 practice documents, the 10 exam documents, and our two attack files are all in `data/`. The only thing you add is your own Portkey key; the repo never contains one.

```bash
git clone https://github.com/sayasivaram/hw6-campus-customs.git
cd hw6-campus-customs
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then set PORTKEY_API_KEY=<your Portkey key> in .env
.venv/bin/python agent.py --doc data/exam_docs/e01_quote.html
```

Python 3.11+ is required (developed on 3.14). The model is fixed to `gpt-6-luna`; the agent refuses to start if `PORTKEY_MODEL` names anything else. `.env` is listed in `.gitignore`, so it's never committed.

## Run the agent

```bash
.venv/bin/python agent.py --doc data/exam_docs/e01_quote.html               # final agent, all defenses on
.venv/bin/python agent.py --doc data/exam_docs/e01_quote.html --no-defenses # same agent, no defenses
```

To switch off one defense level, use `--no-code-defenses`, `--no-design-defenses`, or `--no-prompt-defenses`. `--no-cache` turns off handbook caching.

Every run appends to `output/usage_log.json` (tokens and dollars), `output/audit_trail.json` (every tool call and the final answer), and, only if a document took over the agent, `output/trap_calls.json`. `send_email` and `approve_payment` are trap tools: they never send or pay anything.

## Reproduce the results

| Script | Problem | Writes |
|---|---|---|
| `cache_test.py` | 4 — caching | `output/cache_test.json` |
| `attack_test.py` | 5 — attacks | `output/attack_results.json` |
| `defense_test.py` | 6 — defenses | `output/defense_results.json` |
| `red_team_test.py` | 7 — red team | `output/red_team_results.json` |
| `run_exam.py` | 8 — exam | `output/exam_results.json` |
| `build_report.py` | 9 — results page | `output/hw6_report.html` |

Write-ups are in `output/*.md`. The field-by-field and safety documentation is in `output/harness.md`. The prompt log is `AI_prompts.md`. Model wording varies between runs, so reason text and token counts will differ slightly on a rerun.
