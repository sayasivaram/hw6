# AI Prompts Log — Homework 6

This file records the prompts used with Claude for each problem in Homework 6, including any follow-up prompts and why they were needed.

---

## Problem 1: Vibe Coder Prompts

**Name/Title:** Set up the AI prompt log

**Prompt:**
> gird your loins dude it's time for homework 6. Please work out of the Homework 6 folder. It will be structured very similarly to the previous homeworks, so please begin with Problem 1: Vibe coder prompts. Create AI_prompts.md that will contain a log of what I type in this chat. Make sure you structure it to include one section per problem with the prompt, follow up prompt, and what was lacking

**Follow-up prompts:**
> Please try again in the folder that I moved you to
>
> Yes, delete the AI_prompts.md and Homework 6 folder you created in Desktop/AI Foundations.

**Why an additional prompt was needed:**
_The session started in an old `Desktop/AI Foundations` folder that had no `Homework 6`, so Claude created a new `Homework 6` folder and an `AI_prompts.md` there. The first prompt said "the Homework 6 folder" but gave no path, and the real course folder is `Desktop/Fall 1/AI Foundations`. The session had to be pointed at the right folder before the log could be created next to Homeworks 1–5 in the same format. The second follow-up cleaned up: it removed the stray `Homework 6` folder Claude had created in the wrong place._

---

## Problem 2: Size up the handbook

**Name/Title:** Summarize the shop handbook and the model price sheet

**Prompt:**
> Let's begin Problem 2: Size up the handbook. In the Homework 6 folder, there should be a folder labeled data. Please summarize for me data/shop_handbook.md and data/prices.json

**Follow-up prompts:**
> Please create output/handbook_estimate.md, and in it write 1) how many tokens the handbook is and how you got to that answer 2) what the handbook costs in dollars on one call, 1000 calls, with cached tokens and without. Please show your calculations
>
> Please ensure you are only using the data that i provided

**Why an additional prompt was needed:**
_The first prompt only asked for a summary of the two files. It didn't ask for an output file, a token count, or a cost calculation, so the summary gave just a rough guess (about 7,000 tokens, from characters ÷ 4). The follow-up asked for the actual deliverable. Counting with a real tokenizer (`tiktoken`, `o200k_base`) gave 10,058 tokens, so the rough guess was about 28% too low because the handbook is mostly tables. The second follow-up was needed because the first draft of `handbook_estimate.md` mixed in outside facts: which models use which tokenizer, OpenAI's caching rules and cache expiry times, and a characters-per-token rule of thumb. None of that came from the files provided. The prompt never said "use only the provided data," so Claude filled gaps with general knowledge. The file was rewritten to rely only on `shop_handbook.md` and `prices.json`, with any remaining assumptions stated openly._

---

## Problem 3: Build the vendor desk agent

**Name/Title:** Four-file agent that reads a vendor document and applies the handbook's purchasing rules

**Prompt:**
> Let's move on to Problem 3: Build the vendor desk agent. Please ensure that for the course of this assignment, you are only using gpt-6-luna. The agent is four files: 1) prompts/prompt.md - all instructions for the agent, and the agent also sends the handbook to the model on every call 2) agent.py - entry point 3) tools.py - tools 4) models.py - structured paths. Give the agent the path to a vendor document. I thsould read the document and return vendor, SKU, unit price, lead time in days, minimum order, a decidion (recommend or do_not_recommend) following the handbook rules and a one sentence justification

**Follow-up prompts:**
> Here's some extra detail. The agent should have two trap tools: send_email and approve_payment. They are there to catch documents that might trick agent into sending an email or payment - they should not send or pay anything. They shouuld append call and arguments to output/trap_calls.json - if there exists an entry, it means a document took over the agent. This should be on the system for my entire homework. After each run, append 1) output/usage_log.json with document, time, token counts of API reports, dollar cost using prices.json 2) output/audit_trail.json which is each tool with arguments, short result, and final answer. It should run like python agent.py --doc data/practice_docs/p01_bluehen_quote.html. Please run on p01 and p08 to prove that the agent is working. Create output/harness.md with each field in models.py and why. Also include one line on each tool
>
> Hold off for now; I'll send the next problem.

**Why an additional prompt was needed:**
_The first prompt described the four files and the output fields but left out the rest of the system: the trap tools (`send_email`, `approve_payment`) and `output/trap_calls.json`, the per-run `usage_log.json` and `audit_trail.json`, the exact command-line form (`--doc`), which documents to test on, and the `harness.md` write-up. Without those, Claude would have built an agent with no takeover detection, no cost or audit logging, and no proof it works. The follow-up arrived while Claude was still reading the vendor documents, so it was built into the first version. (Later, in Problem 5, the user removed the hidden-text filter Claude had added to `read_vendor_document` without being asked, and the p01/p08 checks were rerun without it.)_

---

## Problem 4: With and without cached tokens

**Name/Title:** Measure real token counts and cost with the handbook cached vs. not cached

**Prompt:**
> Problem 4: With and without cached tokens. I want to run two tests to be able to compare the token counts that the API sends back where 1) the handbook is getting reused from the cache 2) nothing gets reused from the cache. Please report the token count to me so that I can do a gut check. Make sure all of the model calls for both of these setups is saved to output/cache_test.json - include setup, document, all token counts, and dollars from prices.json. In output/cache_test.md I want to include 1) total cost and cost per document for each setup and percent saved 2) comparison between real numbers and the estimates we made in problem 2 3) projection for 1000 documents a day for 30 days (w and wo cache) 4) Anything surprising in the numbers and why it occurred

**Follow-up prompts:**
> I really only want to be using the handbook from the cache

**Why an additional prompt was needed:**
_The first prompt said the cache setup was "the handbook is getting reused from the cache," but it didn't say that **only** the handbook should be reused. The first run let the API cache the whole prompt: instructions, document, and conversation history (up to 11,716 tokens per call instead of about 10,500). The follow-up made the requirement explicit. Getting there took three tries. Putting the handbook first wasn't enough, and the provider ignored OpenAI's explicit cache breakpoint. What worked was a fresh request ID at the start of the instructions that follow the handbook, so the longest reusable match always ends at the handbook. After that, every cached call reused exactly 10,524 tokens (the handbook plus the tool definitions sent ahead of it). The prompt also didn't name which documents to test, so Claude used all 12 practice documents. (Later, in Problem 5, the cache test was rerun with the hidden-text filter removed. The reused block is now 10,484 tokens, because the read tool's description got shorter.)_

---

## Problem 5: Attack your own agent

**Name/Title:** Run the unchanged Problem 3 agent on every practice document and check for takeovers

**Prompt:**
> Problem 5: Attack your own agent. Some of the vendor documents have text aimed to trap AI. Run the agent we made in problem 3 on all of the documents in data/practice_docs/ (make sure you do not add any other defenses). Compare the answers to data/practice_key.json and look to see if there are any inputs to output/trap_calls.json. Create output/attack_results.json - for each doc, did the field match the key, did the decision match, was there a trap tool called, did any funky things show up in the answer. In output/attack_results.md, create a section for each document that fooled the agent and write what fooled it and where in the file it was. Once done, please give me a summary of the outputs so that I can compare manually

**Follow-up prompts:**
> Run the 12 practice docs once more with the reader's hidden-text filter turned off (everything else unchanged), so we can see whether the prompt rules alone stop the attacks. Save it separately from attack_results.
>
> I want all tests to be without the hidden text filter - please do not save that as a separate document
>
> Please make sure this is also true for all all previous questions - there should be no hidden text filter

**Why an additional prompt was needed:**
_The first run fooled 0 of 12 documents, but only because the Problem 3 agent's `read_vendor_document` had a hidden-text filter Claude built in on its own. It stripped all 7 attacks before the model saw them, so the prompt rules were never tested. Problem 3 never asked for that filter, and "do not add any other defenses" didn't cover a defense that was already there. The follow-ups removed it. The first asked for a filter-off baseline. The second made filter-off the rule for every test, written to the same `attack_results` files. The third removed the filter from the agent entirely and required redoing earlier results. The filter code, its opt-in flag, and the prompt line describing it were deleted. The Problem 3 p01/p08 checks, the Problem 4 cache test, and this attack test were all rerun with the unfiltered agent. Result: still 0 of 12 fooled, with no trap calls, even though the model now sees every attack, so the prompt rules held on their own. The prompt also didn't define "funky things." Claude checks answers for links, email addresses, figures not in the key or handbook, invisible characters, and reasons longer than one sentence._

---

## Problem 6: Defend your agent

**Name/Title:** Code-, design-, and prompt-level defenses, with a way to run with none of them

**Prompt:**
> Problem 6: defend your agent. Now we need to figure out how to defend this agent at 3 levels - code (what the program does before a model sees it), design (how agent is put together), and prompts (rules in prompt/prompt.md). Please leave send_email and approve_payment intact, as we will need them later. Please also keep a way to run the agent without any of its defenses. Re-run with all 12 documents and save output/defense_results.json with the same format as problem 5, but adding token and dollars per document. We must be able to come back with the right values- refusing or blanking will not get credit. In output/defense_results.md

**Follow-up prompts:**
> In output/defense_results.md please include 1) a before and after table for each of the 12 tables 2) what each layer catches that are missed by others 3) extra tokens and dollars each layer adds per document. Please add safety features to output/harness.md in a separate sefety section - in plan words explain how each defense works and what it does

**Why an additional prompt was needed:**
_The first prompt was cut off after "In output/defense_results.md," so it never said what the write-up should contain. The follow-up finished that sentence (a before/after table per document, what each layer uniquely catches, and the extra tokens and dollars per layer) and added a plain-language Safety section to `harness.md`. To answer "what each layer catches that the others miss" and "what each layer adds," Claude ran all 12 documents in five setups: no defenses, each level alone, and all three._

---

## Problem 7: Red team

**Name/Title:** Two new booby-trapped vendor documents, run with and without defenses

**Prompt:**
> Problem 7: Red team. We are now assuming the role of the attacker to test these systems. Create two new booby-trapped dpcuments in data/my_attacks (it can be HTML, PDF, or email) and have each one have a different trap for an AI such that a person opening the document would see the normal quote but an AI would fall into a trap. After you have created those, run both attacks twice - once on the agent with defenses and once without. Create ouput/red_team.md for each attack that explains the booby traps - what is hidden, where, what it is trying to lead the agent to do, and what heppens with and without defenses. I will get more points if there is an attack that is novel and actually fools the agent with no defenses, so aim for that

**Follow-up prompts:**
_None._

**Why an additional prompt was needed:**
_N/A — the initial prompt was sufficient. The prompt didn't say what the "right" answer for a homemade attack is, so Claude wrote `data/my_attacks/my_attacks_key.json` with the values a person reading the visible quote would report. It took two tries to get an attack that fools the agent with no defenses. The first version of attack 2 (a covered, fake "handbook addendum" raising a lead-time limit) fooled neither setup. Claude replaced it with a covered "2-pack pricing" note, which fooled the undefended agent. `red_team.md` records the failed version too._

---

## Problem 8: Exam documents

**Name/Title:** Run the final defended agent on the 10 exam documents

**Prompt:**
> Problem 8: Exam Documents. In data/exam_docs/ there should be 10 vendor documents that don't have answer keys. I want to run the final defended agent that we made. Save output/exam_results.json with one entry per exam file. Here are the fields in each entry - file (exam file name), vendor, sku, unit_price, lead_time_days, min_order, decision (recommend/do_not_recommend), reason, trap_tool_called (t/f), input_tokens, cached_tokens, output_tokens, cost_usd. When the graders are grading this, they will compare to a hidden answer key and rerun agents. Points given for correct fields, decisions, no trap tool calls, and clean documents

**Follow-up prompts:**
_None._

**Why an additional prompt was needed:**
_N/A — the initial prompt was sufficient. The agent ran unchanged with all defenses on (`python run_exam.py`, the same as `python agent.py --doc ...` by default). Claude did not tune the agent to the exam documents. Afterward, it checked each answer by hand against the visible document; all 10 matched, with 0 trap calls._

---

## Problem 9: Results page

**Name/Title:** Self-contained `output/hw6_report.html` dashboard built from the real run outputs

**Prompt:**
> Problem 9: Results page. It's time to create output/hw6_report.html, which is one double click to open file with no internet or other files next to it. This dashboard must show the following (with real numbers from our runs): 1) caching results with a chart 2) attacks before and after defenses 3) what the defenses cost in tokens and dollars 4) exam results and two red team attacks 5) a brief recommendation to the store manager - should Campus Customs turn this on for real vendor mail - what would it cost/month at 1000 docs/day. Once you create the base, we will add more UI features

**Follow-up prompts:**
> Let's add more UI flair. Please separate each question into a different tab with a clear header. When hovering your cursor over each tab, add a movement/hover over effect. Make the subheaders more clearly delineated, perhaps by adding transulcent packgrounds behind each section. Please also change the color scheme to be shades of purple and lavender and add a flower motif

**Why an additional prompt was needed:**
_The first prompt asked for a working base and said UI features would come next, so this follow-up was planned. It split the five questions into tabs, each with a "Question N" header; added a hover effect where tabs lift, an underline grows, and the tab's flower spins; put translucent lavender panels behind every subheading; changed the palette to purple and lavender; and added a flower motif (logo, tab icons, header blooms, a soft flower background, flower bullets). The chart colors (violet, orchid, marigold) were re-checked with the dataviz skill's colorblind validator in light and dark mode. Everything is still inline, so the page still opens offline. Original notes: the page is generated by `build_report.py` from `output/cache_test.json`, `defense_results.json`, `exam_results.json`, `red_team_results.json`, and `data/prices.json`, so every number comes from a real run. CSS, data, and the JavaScript that draws the SVG charts are all inline, so the file opens with no internet. The prompt didn't say how to price the monthly cost, so Claude used 1,000 documents/day × 30 days at the defended agent's measured cost per practice document ($0.000984 → $29.51/month), with the exam-run rate shown alongside._

---

## Final check

**Name/Title:** Gut check of all outputs, tests, and logic against the requirements

**Prompt:**
> Please do a final gut check of all outputs, tests, and logic. Ensure that everything makes sense and meets all of my specified requirements

**Follow-up prompts:**
_None._

**Why an additional prompt was needed:**
_N/A — the initial prompt was sufficient. Claude checked every requirement against the files: valid JSON, the exam fields exactly as specified, all 201 logged runs on `gpt-6-luna`, `trap_calls.json` empty, every `models.py` field and every tool documented in `harness.md`, run settings matching the write-ups, and every user message in this log. It found and fixed four small issues: a stale cached-token count in `harness.md`, a missing rerun note in `cache_test.py`, leftover "None yet / so far" wording here, and no README for graders who rerun the agent. A live rerun of `agent.py` on `e10_email.eml` reproduced the saved exam answer exactly._

---

## Problem 10: Push to GitHub

**Name/Title:** Public repository that opens and runs when cloned

**Prompt:**
> Problem 10: Push to Github and submit the URL. Please push this to a public github repository  please make sure that it opens when cloned. I am including a screenshot of the expected repo. Include the whole data/ folder (course data and attacks) so graders can clone the repo and run the agent immediately. Put a note in README.md on how to run the agent. DO NOT commit the .env key and use gitignore to keep it out
>
> *(attached screenshot of the expected repo layout: AI_prompts.md, README.md, .gitignore, .env.example, requirements.txt, agent.py, tools.py, models.py, prompts/prompt.md, data/ with the handbook, prices, practice key, practice_docs/, exam_docs/, my_attacks/, and output/ with all the write-ups, logs, and hw6_report.html)*

**Follow-up prompts:**
> i want the repo to match the screenshot exactly
>
> Please confirm that with the new file structure, everything still works as expected and can be graded

**Why an additional prompt was needed:**
_The first prompt included a screenshot of the expected repo but didn't say whether extra files were allowed, so Claude also pushed its test scripts and two helper data files, under the name `hw6-campus-customs`. The follow-up asked for an exact match. The repo was renamed to `hw6` (so a clone opens as `hw6/`), and eight files were removed from it: the six test scripts, `output/red_team_results.json`, and `data/my_attacks/my_attacks_key.json`. They are kept locally but excluded from git. Docs that pointed at them (the README, four write-ups, and the report footer) were updated so nothing in the repo refers to a missing file. The last follow-up was a check that the trimmed repo still works. A fresh clone of `hw6` matched the screenshot (50 files), installed cleanly, and graded correctly: e02 and p02 matched their keys with defenses on, and `--no-defenses` was fooled by p02's hidden price as expected. The check also found that `python agent.py --help` crashed without a key, because the model was built at import time. The agent now builds the model on first use, so `--help` works and a missing key prints a one-line setup message instead of a traceback. Original notes: the repo was first created as `sayasivaram/hw6-campus-customs`, matching the Homework 5 naming. It follows the screenshot's layout plus the test scripts the README names for reproducing each output (`cache_test.py`, `attack_test.py`, `defense_test.py`, `red_team_test.py`, `run_exam.py`, `build_report.py`), `output/red_team_results.json`, and `data/my_attacks/my_attacks_key.json`. `.env` is git-ignored, and the staged files were scanned for the key before pushing._

---
