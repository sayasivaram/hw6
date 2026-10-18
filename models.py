"""Structured data types for the Campus Customs vendor desk agent.

VendorDecision is the agent's structured output -- the fields the handbook (section 13) says
the vendor desk must report for every vendor document. The other models describe what the
tools return and what gets written to the output/ logs, so every file has a fixed shape.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Decision = Literal["recommend", "do_not_recommend"]
CheckName = Literal["approved_vendor", "price", "lead_time", "minimum_order"]


class VendorDecision(BaseModel):
    """The agent's final answer for one vendor document (handbook section 13)."""

    vendor: str = Field(description="Vendor name exactly as the document states it, e.g. 'Blue Hen Apparel'.")
    sku: str | None = Field(
        description="Campus Customs SKU the quote is for, e.g. 'CC-HD-006'. null if the document does not say."
    )
    unit_price: float | None = Field(
        description="Quoted unit price in US dollars, e.g. 21.80. null (unknown) if the document does not say."
    )
    lead_time_days: int | None = Field(
        description="Lead time in days as the document states it, e.g. 14. null (unknown) if the document does not say."
    )
    min_order: int | None = Field(
        description="Minimum order in units, e.g. 240. null (unknown) if the document does not say."
    )
    decision: Decision = Field(
        description="'recommend' only if all four purchasing checks pass; otherwise 'do_not_recommend'."
    )
    reason: str = Field(
        description="One sentence that names the purchasing check that decided it (the failed check, or all four passing)."
    )


class DocumentText(BaseModel):
    """What read_vendor_document returns."""

    path: str
    file_type: Literal["html", "pdf", "email"]
    text: str = Field(
        description="The document text. Code defenses on: visible text only, normalized, suspicious lines "
        "flagged. Design defenses on: fenced in untrusted-content markers. No defenses: all text, unfiltered."
    )
    hidden_passages_removed: int | None = Field(
        default=None, description="How many invisible passages the code defenses stripped (null when they are off)."
    )
    flagged_lines: int | None = Field(
        default=None, description="How many lines the code defenses flagged as possible manipulation (null when off)."
    )


class CheckResult(BaseModel):
    """One of the four handbook section 4 purchasing checks."""

    check: CheckName
    passed: bool
    detail: str


class RuleReport(BaseModel):
    """What check_purchasing_rules returns: the four checks and the decision they add up to."""

    vendor_status: Literal["approved", "removed", "pending", "not_on_any_list"]
    max_unit_cost: float | None = Field(description="Max unit cost for the SKU from handbook section 9, or null.")
    checks: list[CheckResult]
    failed_checks: list[CheckName]
    decision: Decision


class TrapCall(BaseModel):
    """One entry in output/trap_calls.json: a document got the agent to try to email or pay."""

    time: str
    document: str
    tool: Literal["send_email", "approve_payment"]
    arguments: dict


class UsageEntry(BaseModel):
    """One entry in output/usage_log.json: the token counts the API reported and their cost."""

    document: str
    time: str
    setup: Literal["cache", "no_cache"] = Field(
        description="'cache': the system prompt is identical on every call, so the API can reuse it. "
        "'no_cache': every call starts with a unique ID, so nothing can be reused."
    )
    model: str
    requests: int
    input_tokens: int = Field(description="All input tokens the API reported, cached ones included.")
    cached_input_tokens: int
    cache_write_tokens: int
    uncached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int = Field(description="Part of output_tokens; already counted there.")
    cost_usd: dict[str, float]


class ToolCallRecord(BaseModel):
    """One tool call inside an audit trail entry."""

    tool: str
    arguments: dict
    result: str = Field(description="Short summary of what the tool returned.")


class AuditEntry(BaseModel):
    """One entry in output/audit_trail.json: every tool the agent called, then its final answer."""

    document: str
    time: str
    defenses: dict[str, bool] = Field(
        default_factory=dict, description="Which defense levels were on: code, design, prompt."
    )
    tool_calls: list[ToolCallRecord]
    hidden_text_removed: list[str] = Field(
        default_factory=list, description="Invisible passages the code defenses stripped before the model saw the document."
    )
    flagged_lines: list[str] = Field(
        default_factory=list, description="Lines the code defenses flagged as possible manipulation (kept, but marked)."
    )
    answer_check_retries: list[str] = Field(
        default_factory=list, description="Each time the design-level answer check sent the answer back, and why."
    )
    final_answer: VendorDecision | None
    error: str | None = None
