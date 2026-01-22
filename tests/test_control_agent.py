from datetime import date

from src.agents.control_agent import run_control_agent
from src.state import FollowupDecision, FollowupMessage, InvoiceRow


def build_invoice(**overrides) -> InvoiceRow:
    base = dict(
        client_name="Acme Co",
        invoice_id="INV-300",
        invoice_amount=1200.0,
        currency="USD",
        invoice_issue_date=date(2025, 1, 1),
        days_overdue=2,
        last_followup_date=None,
        relationship_tag="vip",
        notes="",
    )
    base.update(overrides)
    return InvoiceRow(**base)


def test_control_decision_flags_tone_cap_exceeded() -> None:
    invoice = build_invoice()
    decision = FollowupDecision(
        followup_required=True,
        recommended_timing="now",
        tone="firm",
        explanation="inputs: days_overdue=2 | rules: none | decision: tone=firm",
    )
    state = {"invoice_data": invoice, "decision": decision}
    result = run_control_agent(state, stage="decision")

    control = result["control_decision"]
    assert control.passed is False
    assert any("TONE_CAP_EXCEEDED" in item for item in control.violations)


def test_control_message_flags_forbidden_language() -> None:
    invoice = build_invoice(days_overdue=20, relationship_tag="recurring")
    decision = FollowupDecision(
        followup_required=True,
        recommended_timing="now",
        tone="neutral",
        explanation="inputs: days_overdue=20 | rules: STANDARD_OVERDUE | decision: tone=neutral",
    )
    message = FollowupMessage(
        subject="Overdue invoice reminder",
        body="We require payment immediately or we will take legal action.",
        reasoning="Invoice is overdue.",
    )
    state = {"invoice_data": invoice, "decision": decision, "message": message}
    result = run_control_agent(state, stage="message")

    control = result["control_message"]
    assert control.passed is False
    assert any("FORBIDDEN_PHRASE" in item for item in control.violations)


def test_control_message_passes_when_followup_not_required() -> None:
    invoice = build_invoice(days_overdue=0)
    decision = FollowupDecision(
        followup_required=False,
        recommended_timing="skip",
        tone="soft",
        explanation="inputs: days_overdue=0 | rules: NOT_OVERDUE | decision: skip",
    )
    state = {"invoice_data": invoice, "decision": decision}
    result = run_control_agent(state, stage="message")

    control = result["control_message"]
    assert control.passed is True
    assert control.violations == []
