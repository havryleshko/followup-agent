from datetime import date, timedelta

import pandas as pd
from src.agents.context_agent import extract_notes_signals, run_context_agent
from src.agents.decision_agent import (
    determine_decision,
    determine_timing,
    determine_tone,
    run_decision_agent,
)
from src.io.loader import load_invoices
from src.state import InvoiceContext, InvoiceRow


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


def test_determine_timing_returns_now_when_urgent() -> None:
    invoice = build_invoice(days_overdue=40)
    rules: list[str] = []
    timing = determine_timing(
        invoice=invoice, context=None, days_since_followup=10, rules=rules
    )
    assert timing == "now"
    assert "URGENT_OVERDUE" in rules


def test_determine_tone_softens_for_vip() -> None:
    invoice = build_invoice(relationship_tag="vip")
    context = InvoiceContext(
        risk_level="medium",
        relationship_summary="vip relationship (notes: none)",
        invoice_status_summary="",
        days_since_last_followup=None,
        context_summary="",
    )
    rules: list[str] = []
    notes_signals = extract_notes_signals("")
    tone = determine_tone(
        invoice=invoice, context=context, notes_signals=notes_signals, rules=rules
    )
    assert tone == "soft"
    assert "RELATIONSHIP_SOFTEN" in rules


def test_determine_tone_downgrades_when_soften_notes() -> None:
    invoice = build_invoice(relationship_tag="risky")
    context = InvoiceContext(
        risk_level="high",
        relationship_summary="risky relationship (notes: none)",
        invoice_status_summary="",
        days_since_last_followup=None,
        context_summary="",
    )
    rules: list[str] = []
    notes_signals = extract_notes_signals("Billing issue reported.")
    tone = determine_tone(
        invoice=invoice, context=context, notes_signals=notes_signals, rules=rules
    )
    assert tone == "neutral"
    assert "RELATIONSHIP_FIRM" in rules
    assert "SOFTEN_NOTES_DOWNGRADE" in rules


def test_determine_decision_skips_when_not_overdue() -> None:
    invoice = build_invoice(days_overdue=0)
    decision, rules = determine_decision(
        invoice=invoice,
        context=None,
        days_since_followup=None,
        notes_signals=extract_notes_signals(""),
    )
    assert decision.followup_required is False
    assert decision.recommended_timing == "skip"
    assert "NOT_OVERDUE" in rules


def test_load_invoices_csv_normalizes_fields(tmp_path) -> None:
    data = {
        "Client Name": ["Acme Co"],
        "Invoice ID": ["INV-200"],
        "Invoice Amount": ["1,200.50"],
        "Currency": [""],
        "Invoice Issue Date": ["2025-01-01"],
        "Days Overdue": ["5"],
        "Last Followup Date": [""],
        "Relationship Tag": ["VIP"],
        "Notes": [""],
    }
    df = pd.DataFrame(data)
    path = tmp_path / "invoices.csv"
    df.to_csv(path, index=False)

    rows = load_invoices(str(path))
    assert len(rows) == 1
    row = rows[0]
    assert row.currency == "USD"
    assert row.relationship_tag == "vip"
    assert row.last_followup_date is None
    assert row.notes == ""
    assert row.invoice_amount == 1200.50
    assert row.days_overdue == 5
    assert row.invoice_issue_date == date(2025, 1, 1)


def test_load_invoices_excel_normalizes_fields(tmp_path) -> None:
    data = {
        "client_name": ["Beta LLC"],
        "invoice_id": ["INV-201"],
        "invoice_amount": ["950"],
        "currency": ["USD"],
        "invoice_issue_date": ["2025-02-10"],
        "days_overdue": ["12"],
        "last_followup_date": ["2025-02-15"],
        "relationship_tag": ["new"],
        "notes": ["Promised to pay next week."],
    }
    df = pd.DataFrame(data)
    path = tmp_path / "invoices.xlsx"
    df.to_excel(path, index=False)

    rows = load_invoices(str(path))
    assert len(rows) == 1
    row = rows[0]
    assert row.invoice_amount == 950.0
    assert row.days_overdue == 12
    assert row.last_followup_date == date(2025, 2, 15)
