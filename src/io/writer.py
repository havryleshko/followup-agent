from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional
from src.state import FollowupDecision, FollowupMessage, FollowupState, InvoiceRow


def write_markdown_report(states: Iterable[FollowupState], output_path: str) -> str:
    rows: List[FollowupState] = list(states)
    lines: List[str] = ["# Follow-up Recommendations", ""]

    lines.extend(_render_summary_table(rows))
    lines.append("")

    for index, state in enumerate(rows, start=1):
        lines.extend(_render_invoice_section(state, index=index))
        lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    Path(output_path).write_text(content, encoding="utf-8")
    return content


def _render_summary_table(states: List[FollowupState]) -> List[str]:
    header = (
        "| Invoice ID | Client | Amount | Days Overdue | Timing | Tone | Follow-up |"
    )
    separator = "| --- | --- | --- | --- | --- | --- | --- |"
    lines = ["## Summary", "", header, separator]
    for state in states:
        invoice = state["invoice_data"]
        decision = state.get("decision")
        timing = decision.recommended_timing if decision else "unknown"
        tone = decision.tone if decision else "unknown"
        required = (
            "yes"
            if decision and decision.followup_required
            else "no"
            if decision
            else "unknown"
        )
        amount = _format_amount(invoice)
        lines.append(
            f"| {invoice.invoice_id} | {invoice.client_name} | {amount} | "
            f"{invoice.days_overdue} | {timing} | {tone} | {required} |"
        )
    return lines


def _render_invoice_section(state: FollowupState, index: int) -> List[str]:
    invoice = state["invoice_data"]
    decision = state.get("decision")
    message = state.get("message")

    lines = [f"## Invoice {index}: {invoice.invoice_id}"]
    lines.append("")
    lines.append("**Identifiers**")
    lines.append(
        f"- Client: {invoice.client_name}\n"
        f"- Invoice ID: {invoice.invoice_id}\n"
        f"- Amount: {_format_amount(invoice)}\n"
        f"- Issue Date: {_format_date(invoice.invoice_issue_date)}\n"
        f"- Days Overdue: {invoice.days_overdue}"
    )
    lines.append("")
    lines.append("**Decision**")
    if decision:
        suggested_send = _suggested_send_date(decision.recommended_timing)
        lines.append(
            f"- Follow-up Required: {decision.followup_required}\n"
            f"- Timing: {decision.recommended_timing}\n"
            f"- Suggested Send Date: {suggested_send}\n"
            f"- Tone: {decision.tone}"
        )
    else:
        lines.append("- Decision: unavailable")
    lines.append("")
    lines.append("**Message Draft**")
    if message:
        lines.append(f"- Subject: {message.subject}")
        lines.append("")
        lines.append(message.body.strip())
    else:
        lines.append("- Message: unavailable (not generated)")
    lines.append("")
    lines.append("**Explanation**")
    if decision and decision.explanation:
        lines.append(decision.explanation)
    else:
        lines.append("Explanation unavailable.")
    return lines


def _format_amount(invoice: InvoiceRow) -> str:
    amount = invoice.invoice_amount
    if float(amount).is_integer():
        amount_text = str(int(amount))
    else:
        amount_text = f"{amount:.2f}"
    return f"{amount_text} {invoice.currency}"


def _format_date(value: Optional[date]) -> str:
    if value is None:
        return "unknown"
    return value.isoformat()


def _suggested_send_date(timing: str) -> str:
    if timing == "now":
        return "now"
    if timing == "wait_3_days":
        return "in 3 days"
    if timing == "wait_7_days":
        return "in 7 days"
    if timing == "skip":
        return "no follow-up"
    return "unknown"
