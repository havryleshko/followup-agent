from __future__ import annotations
from typing import Iterable, List, Optional
from src.config import settings
from src.state import ControlResult, FollowupDecision, FollowupMessage, FollowupState, InvoiceRow



TONE_ORDER = {"soft": 0, "neutral": 1, "firm": 2}

def run_control_agent(state: FollowupState, stage: str) -> FollowupState:
    if stage not in {"decision", "message"}:
        raise ValueError(f"Unknown control stage: {stage}")

    if stage == "decision":
        result = _control_decision(state)
        next_state = dict(state)
        next_state["control_decision"] = result
        return next_state

    result = _control_message(state)
    next_state = dict(state)
    next_state["control_message"] = result
    return next_state


def _control_decision(state: FollowupState) -> ControlResult:
    violations: List[str] = []
    decision = state.get("decision")
    if decision is None:
        violations.append("DECISION_MISSING")
        return ControlResult(stage="decision", passed=False, violations=violations)

    _validate_required_fields(
        decision,
        settings.CONTROL_REQUIRED_DECISION_FIELDS,
        violations,
        prefix="DECISION",
    )
    if isinstance(decision.explanation, str) and not decision.explanation.strip():
        violations.append("DECISION_EXPLANATION_MISSING")

    invoice = state.get("invoice_data")
    cap = _resolve_tone_cap(invoice)
    if cap and decision.tone in TONE_ORDER:
        if TONE_ORDER[decision.tone] > TONE_ORDER[cap]:
            violations.append(f"TONE_CAP_EXCEEDED:cap={cap},tone={decision.tone}")

    return ControlResult(stage="decision", passed=not violations, violations=violations)


def _control_message(state: FollowupState) -> ControlResult:
    violations: List[str] = []
    decision = state.get("decision")
    message = state.get("message")

    if decision and (not decision.followup_required or decision.recommended_timing == "skip"):
        return ControlResult(stage="message", passed=True, violations=violations)

    if message is None:
        violations.append("MESSAGE_MISSING")
        return ControlResult(stage="message", passed=False, violations=violations)

    _validate_required_fields(
        message,
        settings.CONTROL_REQUIRED_MESSAGE_FIELDS,
        violations,
        prefix="MESSAGE",
    )

    text = _normalize_text([message.subject, message.body, message.reasoning])
    _find_phrase_violations(
        text, settings.CONTROL_FORBIDDEN_PHRASES, "FORBIDDEN_PHRASE", violations
    )
    _find_phrase_violations(
        text,
        settings.CONTROL_UNSUPPORTED_CLAIMS,
        "UNSUPPORTED_CLAIM",
        violations,
    )

    return ControlResult(stage="message", passed=not violations, violations=violations)


def _validate_required_fields(
    model: object, fields: Iterable[str], violations: List[str], prefix: str
) -> None:
    for field in fields:
        value = getattr(model, field, None)
        if value is None:
            violations.append(f"{prefix}_FIELD_MISSING:{field}")
            continue
        if isinstance(value, str) and not value.strip():
            violations.append(f"{prefix}_FIELD_EMPTY:{field}")


def _resolve_tone_cap(invoice: Optional[InvoiceRow]) -> Optional[str]:
    caps: List[str] = []
    if invoice:
        rel_cap = settings.CONTROL_TONE_CAPS_BY_RELATIONSHIP.get(
            invoice.relationship_tag
        )
        if rel_cap:
            caps.append(rel_cap)
        day_cap = _tone_cap_by_days_overdue(invoice.days_overdue)
        if day_cap:
            caps.append(day_cap)
    if not caps:
        return None
    return min(caps, key=lambda tone: TONE_ORDER.get(tone, 99))


def _tone_cap_by_days_overdue(days_overdue: int) -> Optional[str]:
    for max_days, tone in settings.CONTROL_TONE_CAPS_BY_DAYS_OVERDUE:
        if days_overdue <= max_days:
            return tone
    return None


def _normalize_text(parts: Iterable[Optional[str]]) -> str:
    return " ".join(part.lower() for part in parts if part).strip()


def _find_phrase_violations(
    text: str, phrases: Iterable[str], label: str, violations: List[str]
) -> None:
    for phrase in phrases:
        if phrase in text:
            violations.append(f"{label}:{phrase}")
