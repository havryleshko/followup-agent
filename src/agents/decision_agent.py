from __future__ import annotations
from datetime import date
from typing import List, Optional, Tuple
from src.config import settings
from src.state import FollowupDecision, FollowupState, InvoiceContext, InvoiceRow
from src.agents.context_agent import compute_days_since_followup, extract_notes_signals


TONE_RANK = {"soft": 0, "neutral": 1, "firm": 2}


def run_decision_agent(state: FollowupState, today: Optional[date] = None) -> FollowupState:
    invoice = state["invoice_data"]
    context = state.get("context")
    days_since_followup = _resolve_days_since_followup(
        invoice, context, today=today
    )
    notes_signals = extract_notes_signals(invoice.notes)

    decision, rules = determine_decision(
        invoice=invoice,
        context=context,
        days_since_followup=days_since_followup,
        notes_signals=notes_signals,
    )

    explanation = build_explanation(
        invoice=invoice,
        context=context,
        days_since_followup=days_since_followup,
        rules=rules,
        decision=decision,
    )

    decision = FollowupDecision(
        followup_required=decision.followup_required,
        recommended_timing=decision.recommended_timing,
        tone=decision.tone,
        explanation=explanation,
    )

    next_state = dict(state)
    next_state["decision"] = decision
    return next_state


def determine_decision(
    invoice: InvoiceRow,
    context: Optional[InvoiceContext],
    days_since_followup: Optional[int],
    notes_signals,
) -> Tuple[FollowupDecision, List[str]]:
    rules: List[str] = []

    if notes_signals.no_followup:
        rules.append("NO_FOLLOWUP_KEYWORD")
        decision = FollowupDecision(
            followup_required=False,
            recommended_timing="skip",
            tone="soft",
            explanation="",
        )
        return decision, rules

    if invoice.days_overdue <= 0:
        rules.append("NOT_OVERDUE")
        decision = FollowupDecision(
            followup_required=False,
            recommended_timing="skip",
            tone="soft",
            explanation="",
        )
        return decision, rules

    followup_required = True
    timing = determine_timing(invoice, context, days_since_followup, rules)
    tone = determine_tone(invoice, context, notes_signals, rules)

    decision = FollowupDecision(
        followup_required=followup_required,
        recommended_timing=timing,
        tone=tone,
        explanation="",
    )
    return decision, rules


def determine_timing(
    invoice: InvoiceRow,
    context: Optional[InvoiceContext],
    days_since_followup: Optional[int],
    rules: List[str],
) -> str:
    timing_rules = settings.FOLLOWUP_TIMING_RULES
    min_gap = timing_rules["min_days_between_followups"]
    urgent_days = timing_rules["urgent_days_overdue"]
    standard_days = timing_rules["standard_days_overdue"]

    if days_since_followup is not None and days_since_followup < min_gap:
        remaining = max(min_gap - days_since_followup, 0)
        rules.append("RECENT_FOLLOWUP")
        return (
            "wait_3_days"
            if remaining <= timing_rules["wait_short_days"]
            else "wait_7_days"
        )

    if invoice.days_overdue >= urgent_days:
        rules.append("URGENT_OVERDUE")
        return "now"

    if context and context.risk_level == "high":
        rules.append("RISK_HIGH_TIMING")
        return "now"

    if invoice.days_overdue >= standard_days:
        rules.append("STANDARD_OVERDUE")
        return "now"

    rules.append("LOW_OVERDUE_WAIT")
    return "wait_3_days"


def determine_tone(
    invoice: InvoiceRow,
    context: Optional[InvoiceContext],
    notes_signals,
    rules: List[str],
) -> str:
    risk_level = context.risk_level if context else "medium"
    tone = _tone_from_risk(risk_level)

    if invoice.relationship_tag in {"vip", "new"}:
        if risk_level == "high":
            tone = "neutral"
            rules.append("RELATIONSHIP_SOFTEN_HIGH")
        else:
            tone = "soft"
            rules.append("RELATIONSHIP_SOFTEN")
    elif invoice.relationship_tag == "risky":
        if risk_level == "low":
            tone = "neutral"
            rules.append("RELATIONSHIP_FIRM_LOW")
        else:
            tone = "firm"
            rules.append("RELATIONSHIP_FIRM")

    if notes_signals.soften:
        if tone == "firm":
            tone = "neutral"
            rules.append("SOFTEN_NOTES_DOWNGRADE")
        else:
            tone = "soft"
            rules.append("SOFTEN_NOTES")

    return tone


def build_explanation(
    invoice: InvoiceRow,
    context: Optional[InvoiceContext],
    days_since_followup: Optional[int],
    rules: List[str],
    decision: FollowupDecision,
) -> str:
    last_followup = (
        str(days_since_followup) if days_since_followup is not None else "none"
    )
    risk_level = context.risk_level if context else "unknown"
    inputs = (
        f"days_overdue={invoice.days_overdue}, "
        f"amount={invoice.invoice_amount}, "
        f"relationship={invoice.relationship_tag}, "
        f"last_followup_days={last_followup}, "
        f"risk={risk_level}"
    )
    applied = ",".join(rules) if rules else "none"
    decision_text = (
        f"followup_required={decision.followup_required}, "
        f"timing={decision.recommended_timing}, "
        f"tone={decision.tone}"
    )
    return f"inputs: {inputs} | rules: {applied} | decision: {decision_text}"


def _resolve_days_since_followup(
    invoice: InvoiceRow,
    context: Optional[InvoiceContext],
    today: Optional[date],
) -> Optional[int]:
    if context and context.days_since_last_followup is not None:
        return context.days_since_last_followup
    return compute_days_since_followup(invoice, today=today)


def _tone_from_risk(risk_level: str) -> str:
    if risk_level == "low":
        return "soft"
    if risk_level == "high":
        return "firm"
    return "neutral"
