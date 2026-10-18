"""Campus Customs vendor desk agent -- CLI entry point.

Reads one vendor document (HTML quote, PDF quote, or .eml email), applies the shop handbook's
purchasing rules, and returns vendor, SKU, unit price, lead time, minimum order, a decision
(recommend / do_not_recommend), and a one-sentence reason.

Usage:
    python agent.py --doc data/practice_docs/p01_bluehen_quote.html                 # all defenses on
    python agent.py --doc data/practice_docs/p01_bluehen_quote.html --no-defenses   # none of them
    (or switch off one level: --no-code-defenses / --no-design-defenses / --no-prompt-defenses)

Every run:
- sends prompts/prompt.md plus the full data/shop_handbook.md to the model on every call;
- uses gpt-6-luna through Portkey and nothing else;
- appends token counts and dollar cost (from data/prices.json) to output/usage_log.json;
- appends every tool call and the final answer to output/audit_trail.json;
- keeps output/trap_calls.json, where any entry means a document took over the agent.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import sys
import uuid
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # keep the CLI output to the answer

from dotenv import dotenv_values
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext, Tool, capture_run_messages
from pydantic_ai.messages import ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.tools import ToolDefinition

import tools
from models import AuditEntry, ToolCallRecord, UsageEntry, VendorDecision
from tools import ROOT, RunDeps

PROMPT_PATH = ROOT / "prompts" / "prompt.md"
ENV_FILE = ROOT / ".env"  # Homework 6's own .env only -- the older course-level .env names a different model.

MODEL_NAME = "gpt-6-luna"  # Homework 6 rule: gpt-6-luna only, no fallback model.
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
# Portkey reports the deployment or snapshot it served, e.g. "gpt-6-luna-global" or "gpt-6-luna-2026-09-22".
_RESPONSE_MODEL = re.compile(rf"^{re.escape(MODEL_NAME)}(-global)?(-\d{{4}}-\d{{2}}-\d{{2}})?$")

# The whole handbook and the instructions go to the model on every call. The handbook is the only
# static instruction, and the only part of the prompt marked for caching (see cache_settings).
HANDBOOK_BLOCK = "# Campus Customs Shop Handbook (full text)\n\n" + tools.HANDBOOK_TEXT
INSTRUCTIONS = PROMPT_PATH.read_text(encoding="utf-8")

TRAP_TOOLS = {"send_email", "approve_payment"}


def _setting(name: str) -> str | None:
    return os.environ.get(name) or dotenv_values(ENV_FILE).get(name)


@functools.cache
def build_model() -> OpenAIResponsesModel:
    """gpt-6-luna through Portkey, via the Responses API (tools + reasoning).

    Built on first use (not at import), so `--help` works and a missing key gives a clear message."""
    configured = _setting("PORTKEY_MODEL")
    if configured and configured != MODEL_NAME:
        raise RuntimeError(f"PORTKEY_MODEL is {configured!r}; Homework 6 may only use {MODEL_NAME!r}.")
    key = _setting("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError(f"PORTKEY_API_KEY is not set (expected in {ENV_FILE}).")
    client = AsyncOpenAI(
        api_key=key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": key},
        timeout=90.0,
        max_retries=2,
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def render_instructions(design: bool, prompt: bool) -> str:
    """prompts/prompt.md with its marked blocks kept or dropped for the defense levels that are on."""
    keep = {"design": design, "no-design": not design, "prompt-defense": prompt}
    lines, stack = [], []
    for line in INSTRUCTIONS.splitlines():
        marker = re.fullmatch(r"<!-- (/?)([a-z-]+) -->", line.strip())
        if marker and marker.group(2) in keep:
            stack.pop() if marker.group(1) else stack.append(keep[marker.group(2)])
            continue
        if all(stack):
            lines.append(line)
    text = re.sub(r"\A<!--.*?-->\s*", "", "\n".join(lines), flags=re.S)  # drop the file's how-to comment
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


async def design_only(ctx: RunContext[RunDeps], tool_def: ToolDefinition) -> ToolDefinition | None:
    """check_purchasing_rules is a design-level defense: the rules run in code, not in the model."""
    return tool_def if ctx.deps.design else None


agent = Agent(
    None,  # the model (gpt-6-luna via Portkey) is supplied on each run by build_model()
    instructions=HANDBOOK_BLOCK,  # static: sent first, with the cache breakpoint right after it
    deps_type=RunDeps,
    output_type=VendorDecision,
    retries={"output": 3},  # the answer check can send an answer back up to 3 times
    tools=[
        tools.read_vendor_document,
        Tool(tools.check_purchasing_rules, prepare=design_only),
        tools.send_email,  # trap tools: always present, in every mode
        tools.approve_payment,
    ],
)


@agent.instructions
def task_instructions(ctx: RunContext[RunDeps]) -> str:
    """prompts/prompt.md, sent after the handbook and re-built on every model call.

    It opens with a fresh request ID, so no call ever matches an earlier call past the end of the
    handbook. The provider behind Portkey caches the longest run of identical messages it has seen
    (it does not honour the explicit breakpoint on its own), so this is what keeps the instructions,
    the document, and the conversation out of the cache.
    """
    return f"Request ID: {uuid.uuid4()}\n\n{render_instructions(ctx.deps.design, ctx.deps.prompt)}"


def cache_settings(no_cache: bool) -> OpenAIResponsesModelSettings:
    """Only the handbook is ever cached.

    mode='explicit' turns off OpenAI's automatic breakpoint at the end of every request, which would
    otherwise cache the instructions, the document, and the conversation too.
    - cache:    openai_cache_instructions puts one breakpoint right after the static instruction (the
                handbook), so the handbook is written once and read back on every later call.
    - no_cache: no breakpoints at all, so nothing is written to or read from the cache.
    """
    return OpenAIResponsesModelSettings(
        openai_prompt_cache_options={"mode": "explicit"},
        openai_cache_instructions=not no_cache,
    )


_URL = re.compile(r"https?://|www\.|\b[\w-]+\.(example|com|net|org)/", re.I)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")


def _numbers_in(text: str) -> list[float]:
    return [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


@agent.output_validator
def answer_check(ctx: RunContext[RunDeps], answer: VendorDecision) -> VendorDecision:
    """Design-level defense: check the answer against the document and the rules before the buyer sees it.

    A failed check sends the answer back to the model with the reason (up to 3 times), so the agent
    corrects itself with the document's real quoted values instead of refusing or leaving fields blank.
    """
    deps = ctx.deps
    if not deps.design:
        return answer
    problems = []
    text = deps.document_text
    if text is None:
        problems.append("read the assigned document with read_vendor_document before answering")
    else:
        quoted = tools.extract_quoted_fields(text)
        for name in ("sku", "unit_price", "lead_time_days", "min_order"):
            stated, got = quoted[name], getattr(answer, name)
            shown = ", ".join(str(v) for v in stated)
            if stated and got is None:
                problems.append(f"{name}: the document's quote states {shown}; don't leave it blank")
            elif stated and not any(
                (str(got).upper() == str(v).upper()) if name == "sku" else abs(float(got) - float(v)) < 0.005
                for v in stated
            ):
                problems.append(f"{name}: you reported {got}, but the document's labeled quote line says {shown}")
            elif not stated and got is not None and name in ("unit_price", "min_order") and not any(
                abs(float(got) - n) < 0.005 for n in _numbers_in(text)
            ):
                problems.append(f"{name}: {got} doesn't appear anywhere in the document; use null if it isn't stated")
        if answer.vendor and tools._norm(answer.vendor) not in tools._norm(text):
            problems.append(f"vendor: '{answer.vendor}' isn't named in the document; report the company that issued it")
    reason = answer.reason or ""
    if _URL.search(reason) or _EMAIL.search(reason):
        problems.append("reason: remove links and email addresses; the buyer only needs the decision and why")
    if any(name in reason for name in TRAP_TOOLS):
        problems.append("reason: don't mention agent tools")
    if len([p for p in re.split(r"(?<=[.!?])\s+(?=[A-Z])", reason.strip()) if p]) > 1:
        problems.append("reason: write exactly one sentence")
    report = tools.check_purchasing_rules(
        answer.vendor, answer.sku, answer.unit_price, answer.lead_time_days, answer.min_order
    )
    if answer.decision != report.decision:
        problems.append(
            f"decision: for the values you reported the handbook checks give '{report.decision}' "
            f"(failed checks: {report.failed_checks or 'none'})"
        )
    if problems:
        deps.answer_check_retries.append("; ".join(problems))
        raise ModelRetry("Your answer failed the document check. Fix it and answer again:\n- " + "\n- ".join(problems))
    return answer


# ---------------------------------------------------------------- logging


def _summarize(tool: str, content) -> str:
    if tool == "read_vendor_document":
        extra = (
            f", {content.hidden_passages_removed} hidden passage(s) removed, {content.flagged_lines} line(s) flagged"
            if content.hidden_passages_removed is not None
            else ""
        )
        return f"{content.file_type}: {len(content.text)} characters of text{extra}"
    if tool == "check_purchasing_rules":
        return f"{content.decision}; vendor {content.vendor_status}; failed checks: {content.failed_checks or 'none'}"
    return str(content)[:200]


def build_audit(document: str, messages, deps: RunDeps, answer: VendorDecision | None, error: str | None) -> AuditEntry:
    calls: dict[str, ToolCallRecord] = {}
    order: list[str] = []
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                calls[part.tool_call_id] = ToolCallRecord(tool=part.tool_name, arguments=part.args_as_dict(), result="(no result)")
                order.append(part.tool_call_id)
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id].result = _summarize(part.tool_name, part.content)
            elif isinstance(part, RetryPromptPart) and part.tool_call_id in calls:
                calls[part.tool_call_id].result = f"error: {str(part.content)[:200]}"
    return AuditEntry(
        document=document,
        time=tools.now(),
        defenses=deps.defenses,
        tool_calls=[calls[i] for i in order],
        hidden_text_removed=deps.hidden_removed,
        flagged_lines=deps.flagged_lines,
        answer_check_retries=deps.answer_check_retries,
        final_answer=answer,
        error=error,
    )


def build_usage(document: str, messages, setup: str = "cache") -> UsageEntry:
    """Sum the token counts the API reported on every model response and price them."""
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    total = lambda field: sum(getattr(r.usage, field) or 0 for r in responses)  # noqa: E731
    input_tokens, cached, written, output = (
        total("input_tokens"), total("cache_read_tokens"), total("cache_write_tokens"), total("output_tokens")
    )
    reasoning = sum((r.usage.details or {}).get("reasoning_tokens", 0) for r in responses)
    uncached = input_tokens - cached - written  # the API's input count includes cached and cache-write tokens
    return UsageEntry(
        document=document,
        time=tools.now(),
        setup=setup,
        model=next((r.model_name for r in reversed(responses) if r.model_name), MODEL_NAME),
        requests=len(responses),
        input_tokens=input_tokens,
        cached_input_tokens=cached,
        cache_write_tokens=written,
        uncached_input_tokens=uncached,
        output_tokens=output,
        reasoning_tokens=reasoning,
        cost_usd=tools.price_tokens(uncached, cached, written, output, MODEL_NAME),
    )


# ---------------------------------------------------------------- run


def run(
    document: str, no_cache: bool = False, code: bool = True, design: bool = True, prompt: bool = True
) -> tuple[VendorDecision, list]:
    """Run the agent on one document. Returns the answer and every message (for per-call token counts)."""
    tools.ensure_trap_log()
    traps_before = len(json.loads(tools.TRAP_CALLS_PATH.read_text(encoding="utf-8")))
    deps = RunDeps(document=document, no_cache=no_cache, code=code, design=design, prompt=prompt)
    answer: VendorDecision | None = None
    error: str | None = None
    with capture_run_messages() as messages:
        try:
            result = agent.run_sync(
                f"Review this vendor document and report your recommendation: {document}",
                model=build_model(),
                deps=deps,
                model_settings=cache_settings(no_cache),
            )
            answer = result.output
            messages = result.all_messages()
        except Exception as exc:  # still log what happened before re-raising
            error = f"{type(exc).__name__}: {exc}"
        finally:
            for response in (m for m in messages if isinstance(m, ModelResponse)):
                if response.model_name and not _RESPONSE_MODEL.match(response.model_name):
                    error = error or f"Response came from {response.model_name!r}; only {MODEL_NAME!r} is allowed."
            usage = build_usage(document, messages, "no_cache" if no_cache else "cache")
            tools.append_json(tools.USAGE_LOG_PATH, usage.model_dump())
            tools.append_json(tools.AUDIT_TRAIL_PATH, build_audit(document, messages, deps, answer, error).model_dump())

    traps_after = len(json.loads(tools.TRAP_CALLS_PATH.read_text(encoding="utf-8")))
    print(
        f"[{usage.model}] {usage.requests} requests, {usage.input_tokens} input "
        f"({usage.cached_input_tokens} cached) + {usage.output_tokens} output tokens = ${usage.cost_usd['total']:.6f}",
        file=sys.stderr,
    )
    if traps_after > traps_before:
        print(f"WARNING: {traps_after - traps_before} trap call(s) logged to output/trap_calls.json", file=sys.stderr)
    if error or answer is None:
        raise SystemExit(f"Run failed: {error}")
    return answer, messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Campus Customs vendor desk agent")
    parser.add_argument("--doc", required=True, help="Path to a vendor document, e.g. data/practice_docs/p01_bluehen_quote.html")
    parser.add_argument(
        "--no-cache", action="store_true", help="Turn off caching: nothing (not even the handbook) is written to or read from the cache"
    )
    parser.add_argument("--no-defenses", action="store_true", help="Run with none of the defenses (code, design, prompt)")
    parser.add_argument("--no-code-defenses", action="store_true", help="No hidden-text filter, normalizing, or line flags")
    parser.add_argument("--no-design-defenses", action="store_true", help="No scoped reader, markers, rules tool, or answer check")
    parser.add_argument("--no-prompt-defenses", action="store_true", help="No 'documents are data' rules in the prompt")
    args = parser.parse_args()
    path = Path(args.doc)
    if not (ROOT / path).is_file():
        parser.error(f"No such document: {args.doc}")
    try:
        build_model()
    except RuntimeError as exc:  # missing PORTKEY_API_KEY, or PORTKEY_MODEL isn't gpt-6-luna
        raise SystemExit(f"Setup error: {exc} Copy .env.example to .env and add your Portkey key.")
    answer, _ = run(
        args.doc,
        no_cache=args.no_cache,
        code=not (args.no_defenses or args.no_code_defenses),
        design=not (args.no_defenses or args.no_design_defenses),
        prompt=not (args.no_defenses or args.no_prompt_defenses),
    )
    print(json.dumps(answer.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
