from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional, Sequence, Tuple
from src.config import settings
from src.state import FollowupState, InvoiceContext, InvoiceRow


@dataclass(frozen=True)
class NotesSignals:
    high: List[str]
    low: List[str]
    soften: List[str]
    no_followup: List[str]


def run_context_agent(state: FollowupState, today: Optional[date] = None) -> FollowupState:
    invoice = state["invoice_data"]
    days_since_followup = compute_days_since_followup(invoice, today=today)
    notes_signals = extract_notes_signals(invoice.notes)
    risk_level, risk_score = compute_risk_level(invoice, notes_signals)

    relationship_summary = build_relationship_summary(invoice, notes_signals)
    invoice_status_summary = build_invoice_status_summary(
        invoice, days_since_followup
    )
    context_summary = build_context_summary(
        invoice=invoice,
        days_since_followup=days_since_followup,
        notes_signals=notes_signals,
        risk_level=risk_level,
        risk_score=risk_score,
    )

    context = InvoiceContext(
        risk_level=risk_level,
        relationship_summary=relationship_summary,
        invoice_status_summary=invoice_status_summary,
        days_since_last_followup=days_since_followup,
        context_summary=context_summary,
    )

    next_state = dict(state)
    next_state["context"] = context
    return next_state


def compute_days_since_followup(
    invoice: InvoiceRow, today: Optional[date] = None
) -> Optional[int]:
    if invoice.last_followup_date is None:
        return None
    today = today or date.today()
    delta = (today - invoice.last_followup_date).days
    return max(delta, 0)


def compute_risk_level(
    invoice: InvoiceRow, notes_signals: NotesSignals
) -> Tuple[str, int]:
    score = 0
    score += _score_by_thresholds(
        invoice.days_overdue, settings.RISK_SCORE_DAYS_OVERDUE
    )
    score += _score_by_thresholds(invoice.invoice_amount, settings.RISK_SCORE_AMOUNT)
    score += settings.RISK_SCORE_RELATIONSHIP.get(invoice.relationship_tag, 0)

    if notes_signals.high:
        score += 2
    if notes_signals.low:
        score -= 1

    score = max(score, 0)
    if score <= settings.RISK_LEVEL_THRESHOLDS["low_max"]:
        return "low", score
    if score <= settings.RISK_LEVEL_THRESHOLDS["medium_max"]:
        return "medium", score
    return "high", score


def extract_notes_signals(notes: str) -> NotesSignals:
    text = (notes or "").lower()
    high = _find_keywords(text, settings.RISK_SCORE_NOTES_KEYWORDS["high"])
    low = _find_keywords(text, settings.RISK_SCORE_NOTES_KEYWORDS["low"])
    soften = _find_keywords(text, settings.RISK_SCORE_NOTES_KEYWORDS["soften"])
    no_followup = _find_keywords(
        text, settings.RISK_SCORE_NOTES_KEYWORDS["no_followup"]
    )
    return NotesSignals(high=high, low=low, soften=soften, no_followup=no_followup)


def build_relationship_summary(invoice: InvoiceRow, notes_signals: NotesSignals) -> str:
    notes_hint = "notes: none"
    if notes_signals.high or notes_signals.low or notes_signals.soften:
        notes_hint = "notes: " + ",".join(
            _flatten_notes_flags(notes_signals, include_no_followup=False)
        )
    return f"{invoice.relationship_tag} relationship ({notes_hint})"


def build_invoice_status_summary(
    invoice: InvoiceRow, days_since_followup: Optional[int]
) -> str:
    followup_text = (
        f"last follow-up {days_since_followup}d ago"
        if days_since_followup is not None
        else "no prior follow-up"
    )
    return (
        f"{invoice.days_overdue}d overdue, "
        f"{_format_amount(invoice.invoice_amount)} {invoice.currency}, "
        f"{followup_text}"
    )


def build_context_summary(
    invoice: InvoiceRow,
    days_since_followup: Optional[int],
    notes_signals: NotesSignals,
    risk_level: str,
    risk_score: int,
) -> str:
    flags = _flatten_notes_flags(notes_signals)
    flags_text = ",".join(flags) if flags else "none"
    last_followup = (
        str(days_since_followup) if days_since_followup is not None else "none"
    )
    parts = [
        f"days_overdue={invoice.days_overdue}",
        f"amount={_format_amount(invoice.invoice_amount)}",
        f"currency={invoice.currency}",
        f"relationship={invoice.relationship_tag}",
        f"last_followup_days={last_followup}",
        f"notes_flags={flags_text}",
        f"risk={risk_level}",
        f"risk_score={risk_score}",
    ]
    return " | ".join(parts)


def _score_by_thresholds(
    value: float, rules: Sequence[Tuple[float, int]]
) -> int:
    for max_value, score in rules:
        if value <= max_value:
            return score
    return rules[-1][1] if rules else 0


def _find_keywords(text: str, keywords: Iterable[str]) -> List[str]:
    found: List[str] = []
    for keyword in keywords:
        if keyword in text:
            found.append(keyword)
    return found


def _flatten_notes_flags(
    notes_signals: NotesSignals, include_no_followup: bool = True
) -> List[str]:
    flags: List[str] = []
    for label, items in (
        ("high", notes_signals.high),
        ("low", notes_signals.low),
        ("soften", notes_signals.soften),
    ):
        for item in items:
            flags.append(f"{label}:{item}")
    if include_no_followup:
        for item in notes_signals.no_followup:
            flags.append(f"no_followup:{item}")
    return flags


def _format_amount(amount: float) -> str:
    if amount.is_integer():
        return str(int(amount))
    return f"{amount:.2f}"
