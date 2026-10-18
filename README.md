# Homework 6 — Campus Customs Vendor Desk Agent

An agent that reads a vendor document (HTML quote, PDF quote, or `.eml` email), applies the rules in `data/shop_handbook.md`, and returns vendor, SKU, unit price, lead time, minimum order, a decision (`recommend` / `do_not_recommend`), and a one-sentence reason. It uses **`gpt-6-luna` through Portkey only**.

## How to run the agent (from a fresh clone)

Everything the agent needs is in the repo: the handbook, prices, practice key, the 12 practice documents, the 10 exam documents, and our two attack files are all in `data/`. The only thing you add is your own Portkey key; the repo never contains one.

```bash
git clone https://github.com/sayasivaram/hw6.git
cd hw6
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

## What's in `output/`

| File | Problem | What it is |
|---|---|---|
| `handbook_estimate.md` | 2 | Handbook token count and cost estimate |
| `harness.md` | 3, 6 | Every field in `models.py` and why, one line per tool, and the Safety section |
| `usage_log.json`, `audit_trail.json`, `trap_calls.json` | 3 | Per-run logs written by `agent.py` |
| `cache_test.json`, `cache_test.md` | 4 | Every model call with and without the cached handbook, and the analysis |
| `attack_results.json`, `attack_results.md` | 5 | The agent vs. the 12 practice documents |
| `defense_results.json`, `defense_results.md` | 6 | Before and after defenses, per layer, with tokens and dollars |
| `red_team.md` | 7 | Our two attack files in `data/my_attacks/` and what they did |
| `exam_results.json` | 8 | The final defended agent on the 10 exam documents |
| `hw6_report.html` | 9 | The results dashboard: one self-contained file, double-click to open |

Write-ups are in `output/*.md`. The field-by-field and safety documentation is in `output/harness.md`. The prompt log is `AI_prompts.md`. Model wording varies between runs, so reason text and token counts will differ slightly on a rerun.
