# Cache Test — With and Without Cached Tokens

The vendor desk agent (`gpt-6-luna` through Portkey, **no hidden-text filter**) was run on all 12 practice documents in two setups. Token counts are the ones the API reported on each model call. Dollar figures use `data/prices.json`. Every model call is saved in `output/cache_test.json`.

```
python cache_test.py
```

| Setup | What's reused from the cache | How |
|---|---|---|
| **cache** | **The handbook only** | The handbook is sent first, as its own message, with a cache breakpoint after it. The instructions (`prompts/prompt.md`) come next and open with a fresh `Request ID` on every call, so no call matches an earlier one past the end of the handbook. |
| **no_cache** | Nothing | No cache breakpoint, and the request ID is in the same block as the handbook, so no call shares anything reusable with another. |

Both setups used the same agent, the same 12 documents, and the same prompt text. Each document took **3 model calls**: read the document, check the rules, and return the answer. That's 36 calls per setup and 72 in total. **Both setups matched the practice key on 12 of 12 decisions, and there were 0 trap calls.**

### Token counts the API reported

| | cache | no_cache |
|---|---|---|
| Model calls | 36 | 36 |
| Input tokens (all) | 424,266 | 424,212 |
| – cached (reused) | **377,424** (= 36 × 10,484) | **0** |
| – cache write | 42,306 | **419,676** |
| – uncached (plain input) | 4,536 (= 36 × 126) | 4,536 (= 36 × 126) |
| Output tokens | 2,667 | 2,612 |
| – of which reasoning | 679 | 566 |
| Input tokens per document | 35,356 | 35,351 |
| Output tokens per document | 222 | 218 |

**Cached tokens per call: 10,484 on every one of the 36 cache-setup calls.** That's the handbook as sent (10,067 tokens: its 10,058 plus a 9-token heading) plus 417 tokens of tool definitions and output format, which the API places ahead of the handbook. Nothing from the instructions, the document, or the conversation was reused.

Typical single call (averages across the 12 documents):

| Call | cache: input / cached / written / out | cache $ | no_cache: input / cached / written / out | no_cache $ |
|---|---|---|---|---|
| 1. read document | 11,576 / 10,484 / 966 / 29 | $0.000253 | 11,574 / 0 / 11,448 / 29 | $0.001458 |
| 2. check rules | 11,773 / 10,484 / 1,163 / 84 | $0.000305 | 11,770 / 0 / 11,644 / 89 | $0.001513 |
| 3. final answer | 12,006 / 10,484 / 1,396 / 109 | $0.000346 | 12,007 / 0 / 11,881 / 100 | $0.001548 |

---

## 1. Total cost, cost per document, and percent saved

| Cost component | cache | no_cache |
|---|---|---|
| Uncached input (4,536 × $0.10/1M) | $0.00045360 | $0.00045360 |
| Cached input (× $0.01/1M) | $0.00377424 | $0.00000000 |
| Cache write (× $0.125/1M) | $0.00528825 | $0.05245955 |
| Output (× $0.50/1M) | $0.00133350 | $0.00130600 |
| **Total, 12 documents** | **$0.01084963** | **$0.05421914** |
| **Per document** (total ÷ 12) | **$0.00090414** | **$0.00451826** |

Worked example, cache setup: `4,536 × 0.10/1M + 377,424 × 0.01/1M + 42,306 × 0.125/1M + 2,667 × 0.50/1M = $0.00045360 + $0.00377424 + $0.00528825 + $0.00133350 = $0.01084963`.

**Percent saved by caching the handbook:** `1 − $0.01084963 ÷ $0.05421914 = 1 − 0.2001 = 80.0%`. Each document costs **about 5.0× less** with the handbook cached ($0.00452 vs $0.00090).

---

## 2. Real numbers vs. the Problem 2 estimates

Problem 2 priced **only the handbook (10,058 tokens)** for **one call**.

| | Problem 2 estimate | Real (this test) | Why they differ |
|---|---|---|---|
| Handbook tokens reused per call | 10,058 | **10,484** | The 9-token heading plus 417 tokens of tool definitions that the API sends ahead of the handbook. That's 4.2% more than the estimate. |
| **Cached handbook, one call** | **$0.0001006** | **$0.0001048** (10,484 × $0.01/1M) | **Within 5% of the estimate.** The cached rate and the handbook size were both right. |
| Uncached handbook, one call | $0.0010058 (at $0.10 input) | $0.0013105 (10,484 × $0.125/1M) | No-cache calls were billed at the **cache write** rate, not the plain input rate (see section 4). |
| Whole call, no cache | — | $0.00146–$0.00155 | The estimate left out `prompt.md`, the document, tool results, and output. |
| Whole call, handbook cached | — | $0.00025–$0.00035 | The handbook is cheap now. Most of the bill is the 960–1,580 tokens after it, written to the cache at $0.125/1M on every call. |
| Calls per document | 1 | 3 | The handbook is sent with every call, so each document carries it 3 times. |
| 1,000 units, no cache | $1.01 (1,000 calls) | **$4.52** (1,000 documents) | 3 calls per document, a bigger prompt, and the higher write rate. |
| 1,000 units, cached | $0.10 (1,000 calls) | **$0.90** (1,000 documents) | 3 calls per document, plus about 1,200 newly written tokens per call. |
| Percent saved | 89.9% | **80.0%** | Only the handbook is discounted. The instructions, document, tool results, and output are paid at full price (or the write price) on every call. |

**Verdict:** For the handbook itself, Problem 2 was almost exactly right. A cached handbook read costs $0.000105 per call vs. the estimated $0.000101. What the estimate missed is everything around the handbook: 3 calls per document, about 1,500 non-handbook tokens per call, and the write rate applying whenever something isn't reused. Per document, real costs are about **4.5×** (no cache) and **9.0×** (cache) the Problem 2 per-call figures.

---

## 3. Projection: 1,000 documents a day for 30 days

30,000 documents, at the per-document costs measured above.

| | Per document | Per day (1,000) | 30 days (30,000) |
|---|---|---|---|
| **Without cache** | $0.00451826 | $4.52 | **$135.55** |
| **With handbook cache** | $0.00090414 | $0.90 | **$27.12** |
| **Saved** | $0.00361412 | $3.61 | **$108.42 (80.0%)** |

The cached projection assumes the handbook stays in the cache, as it did for every call in this test. If the handbook had to be re-written for every document (call 1 billed like a no_cache call, $0.0014582, with calls 2 and 3 cached at $0.0003050 + $0.0003463), a document would cost $0.0021094, or **$63.28 for 30 days**. That's still less than half of no-cache.

The Problem 2 figures scaled to 30,000 calls give $30.17 without cache and $3.02 with cache, far below the real numbers for the reasons in section 2.

---

## 4. What's surprising, and why

1. **The first version of this test cached far more than the handbook.** Before this setup, the agent cached the whole prompt: instructions, document, and the growing conversation. Calls reused up to 11,716 tokens, and a document cost $0.00063. Moving the handbook first didn't fix it, and neither did adding OpenAI's explicit "cache only up to here" breakpoint. The request carried the breakpoint correctly, but the provider behind Portkey (`gpt-6-luna-global`) still cached everything. It turns out it reuses the **longest run of messages that exactly match an earlier call**. The fix was to make the message right after the handbook different on every call (the request ID), so the longest possible match ends at the handbook.

2. **Caching only the handbook costs more than caching everything.** That's $0.00090 vs. $0.00063 per document. Everything after the handbook (about 960–1,580 tokens per call) is now **written** to the cache at $0.125/1M on every call and never read back. When the whole prompt was cached, most of that was read back at $0.01/1M. The handbook alone accounts for only $0.000315 of each document's $0.000904.

3. **"No cache" doesn't mean "plain input."** The provider billed **419,676 of 424,212 input tokens (98.9%) as cache writes**, even with no breakpoint requested. Under `prices.json`, a write ($0.125/1M) costs more than plain input ($0.10/1M), so no_cache cost **24% more** than the plain-input price Problem 2 assumed ($0.05422 vs. $0.04373 for the same tokens). Against that plain-input baseline, caching the handbook saves 75.2%.

4. **The cached amount never moved: 10,484 tokens on all 36 calls**, and the extra over the handbook is the tool definitions. In an earlier run of this test, the reused block was 10,524 tokens. The only thing that changed in between was that the `read_vendor_document` tool description got one sentence shorter, when the hidden-text filter was removed. The reused block shrank by exactly that much (40 tokens). That confirms the 417 extra tokens are the tool definitions, which the API sends before the handbook, so they're part of every cached opening.

5. **Exactly 126 tokens per call were never cached or written, in all 72 calls** (4,536 = 36 × 126 in each setup). This held for prompts from about 11,570 to 12,190 tokens, so it's a fixed part of every request that's always billed as plain input. It costs $0.0000126 per call.

6. **Each document sends the handbook three times.** Input averaged about 35,350 tokens per document against only about 220 output tokens. Input was 88% of the cached bill and 98% of the no-cache bill. Cutting a call (for example, putting the document text in the first message so the agent can skip the read step) would save about a third of the input.

7. **Caching didn't change the answers.** Both setups got 12 of 12 decisions matching the practice key, with 0 trap calls, even though the agent now reads every document's hidden text too.
