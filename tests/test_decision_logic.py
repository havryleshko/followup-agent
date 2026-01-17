from datetime import date, timedelta

from src.agents.context_agent import run_context_agent
from src.agents.decision_agent import run_decision_agent
from src.state import InvoiceRow


def build_invoice(**overrides) -> InvoiceRow:
    base = dict(
        client_name="Acme Co",
        invoice_id="INV-100",
        invoice_amount=2500.0,
        currency="USD",
        invoice_issue_date=date(2025, 1, 1),
        days_overdue=20,
        last_followup_date=None,
        relationship_tag="recurring",
        notes="",
    )
    base.update(overrides)
    return InvoiceRow(**base)


def test_context_risk_tier_high_from_overdue_amount_and_notes() -> None:
    invoice = build_invoice(
        days_overdue=45,
        invoice_amount=9000.0,
        relationship_tag="risky",
        notes="Late payment, ignored prior reminders.",
    )
    state = {"invoice_data": invoice}
    result = run_context_agent(state, today=date(2025, 3, 1))

    context = result["context"]
    assert context.risk_level == "high"
    assert "risk=high" in context.context_summary
    assert "notes_flags=high:late payment" in context.context_summary


def test_decision_waits_when_recent_followup() -> None:
    today = date(2025, 3, 1)
    invoice = build_invoice(
        days_overdue=10, last_followup_date=today - timedelta(days=1)
    )
    state = {"invoice_data": invoice}
    state = run_context_agent(state, today=today)
    result = run_decision_agent(state, today=today)

    decision = result["decision"]
    assert decision.followup_required is True
    assert decision.recommended_timing == "wait_3_days"
    assert "RECENT_FOLLOWUP" in decision.explanation


def test_decision_skips_when_paid_keyword_present() -> None:
    invoice = build_invoice(notes="Paid in full yesterday.")
    state = {"invoice_data": invoice}
    result = run_decision_agent(state, today=date(2025, 3, 1))

    decision = result["decision"]
    assert decision.followup_required is False
    assert decision.recommended_timing == "skip"
