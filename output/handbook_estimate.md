# Handbook Token and Cost Estimate

What it costs to send `data/shop_handbook.md` to `gpt-6-luna` as part of the vendor desk agent's prompt. Only two inputs are used: the handbook file and the prices in `data/prices.json`.

---

## 1. How many tokens is the handbook?

**Answer: 10,058 tokens.**

### How I got there

1. **Read the file.** `data/shop_handbook.md` has 28,903 characters, 6,127 words, and 338 lines.
2. **Ran the full text through a tokenizer.** I used the `tiktoken` Python library with its `o200k_base` encoding and counted the tokens it returned:

   ```python
   import tiktoken
   text = open("data/shop_handbook.md", encoding="utf-8").read()
   len(tiktoken.get_encoding("o200k_base").encode(text))   # -> 10058
   ```

3. **Why the count is high for the file's length.** 10,058 tokens for 28,903 characters works out to `28,903 ÷ 10,058 ≈ 2.9` characters per token. Most of the handbook is markdown tables: the 177-row product catalogue in section 9 and the 40-row purchase order table in section 10. These are full of pipes (`|`), SKU codes (`CC-HD-001`), dollar amounts (`$29.48`), and dates, and each of those splits into several short tokens.

### Assumptions
- `data/prices.json` doesn't name a tokenizer for `gpt-6-luna`. I assumed `o200k_base` gives the token count the model would bill.
- 10,058 counts only the handbook text. It doesn't include the rest of a real call: the vendor document, any other instructions, or the model's reply.

---

## 2. What does the handbook cost?

### Prices (from `data/prices.json`, `gpt-6-luna`, per 1M tokens)

| Field in `prices.json` | $ per 1M tokens | $ per token |
|---|---|---|
| `input_per_1m` | $0.10 | $0.0000001 |
| `cache_write_per_1m` | $0.125 | $0.000000125 |
| `cached_input_per_1m` | $0.01 | $0.00000001 |

Formula: **cost = tokens × (price per 1M ÷ 1,000,000)**

How I read the three prices:
- **Without caching**, every call pays `input_per_1m`.
- **With caching**, the first call pays `cache_write_per_1m` to store the handbook. Every later call pays `cached_input_per_1m` to reuse it.

### Without caching

**One call**
```
10,058 × $0.10 / 1,000,000 = $0.0010058   ≈ $0.0010
```

**1,000 calls**
```
1,000 × $0.0010058 = $1.0058   ≈ $1.01
```

### With caching

**One call** (the first call, which writes the cache)
```
10,058 × $0.125 / 1,000,000 = $0.0012573   ≈ $0.0013
```

For comparison, each later call that reads from the cache costs:
```
10,058 × $0.01 / 1,000,000 = $0.0001006   ≈ $0.0001
```

**1,000 calls** (1 cache write + 999 cache reads)
```
Cache write:   1 × 10,058 × $0.125 / 1,000,000 = $0.0012573
Cache reads: 999 × 10,058 × $0.01  / 1,000,000 = $0.1004794
                                                 ----------
Total                                          = $0.1017367   ≈ $0.10
```

### Summary

| | One call | 1,000 calls |
|---|---|---|
| **Without caching** | $0.0010 | **$1.01** |
| **With caching** | $0.0013 (first call writes the cache) | **$0.10** |
| **Savings from caching** | −$0.0003 (caching costs *more* on a single call) | **$0.90 saved (89.9% less)** |

Savings at 1,000 calls: `$1.0058 − $0.1017 = $0.9041`, and `$0.9041 ÷ $1.0058 = 89.9%`.

### What this means
- **For one call, caching doesn't help.** `cache_write_per_1m` ($0.125) is higher than `input_per_1m` ($0.10).
- **Caching pays for itself on the second call.** Two calls without caching cost `2 × $0.0010058 = $0.0020116`. Two calls with caching cost `$0.0012573 + $0.0001006 = $0.0013579`.
- **At scale, caching cuts the handbook cost about 10×.** `cached_input_per_1m` ($0.01) is one-tenth of `input_per_1m` ($0.10), and the one-time write cost is spread across all the calls.

### Assumptions behind the cached numbers
- The handbook is written to the cache **once**, and all 1,000 calls reuse that same copy. If it has to be written again, each extra write adds $0.0012573.
- All 10,058 handbook tokens are billed at the cached rate after the first call.
- These numbers cover the handbook only. Each real call also pays for the vendor document and the agent's output (`output_per_1m` = $0.50).
