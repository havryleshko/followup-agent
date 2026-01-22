from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional
from src.state import (
    ControlResult,
    FollowupDecision,
    FollowupMessage,
    FollowupState,
    InvoiceRow,
)


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
        "| Invoice ID | Client | Amount | Days Overdue | Timing | Tone | Follow-up | "
        "Decision Control | Message Control |"
    )
    separator = "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
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
        control_decision = _control_status(state.get("control_decision"))
        control_message = _control_status(state.get("control_message"))
        lines.append(
            f"| {invoice.invoice_id} | {invoice.client_name} | {amount} | "
            f"{invoice.days_overdue} | {timing} | {tone} | {required} | "
            f"{control_decision} | {control_message} |"
        )
    return lines


def _render_invoice_section(state: FollowupState, index: int) -> List[str]:
    invoice = state["invoice_data"]
    decision = state.get("decision")
    message = state.get("message")
    control_decision = state.get("control_decision")
    control_message = state.get("control_message")

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
    lines.append("**Control Checks**")
    if control_decision or control_message:
        lines.extend(_render_control_block("Decision", control_decision))
        lines.extend(_render_control_block("Message", control_message))
    else:
        lines.append("- Control: unavailable")
    lines.append("")
    lines.append("**Message Draft**")
    withhold_reason = _message_withhold_reason(
        decision, control_decision, control_message
    )
    if message and not withhold_reason:
        lines.append(f"- Subject: {message.subject}")
        lines.append("")
        lines.append(message.body.strip())
    else:
        reason = withhold_reason or "Message unavailable (not generated)."
        lines.append(f"- Message: {reason}")
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


def _control_status(control: Optional[ControlResult]) -> str:
    if control is None:
        return "unknown"
    return "pass" if control.passed else "fail"


def _render_control_block(
    label: str, control: Optional[ControlResult]
) -> List[str]:
    if control is None:
        return [f"- {label} Control: unavailable"]
    status = "pass" if control.passed else "fail"
    if not control.violations:
        return [f"- {label} Control: {status}"]
    violations = "; ".join(control.violations)
    return [f"- {label} Control: {status} ({violations})"]


def _message_withhold_reason(
    decision: Optional[FollowupDecision],
    control_decision: Optional[ControlResult],
    control_message: Optional[ControlResult],
) -> Optional[str]:
    if decision and (
        not decision.followup_required or decision.recommended_timing == "skip"
    ):
        return "Follow-up not required."
    if control_decision and not control_decision.passed:
        return "Decision control failed; message withheld."
    if control_message and not control_message.passed:
        return "Message control failed; message withheld."
    return None
