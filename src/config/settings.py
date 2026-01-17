from __future__ import annotations

RISK_SCORE_DAYS_OVERDUE = [
    (7, 0),
    (30, 1),
    (60, 2),
    (10_000, 3),
]

RISK_SCORE_AMOUNT = [
    (500, 0),
    (2_000, 1),
    (10_000, 2),
    (1_000_000, 3),
]

RISK_SCORE_RELATIONSHIP = {
    "vip": -1,
    "recurring": 0,
    "new": 1,
    "risky": 2,
}

RISK_SCORE_NOTES_KEYWORDS = {
    "high": ["late payment", "overdue", "broken promise", "collection", "ignored"],
    "low": ["apologized", "good standing", "long-term", "paid on time"],
    "soften": ["dispute", "billing issue", "invoice error", "incorrect"],
    "no_followup": ["paid", "settled", "resolved", "closed"],
}

RISK_LEVEL_THRESHOLDS = {
    "low_max": 2,
    "medium_max": 5,
}

FOLLOWUP_TIMING_RULES = {
    "urgent_days_overdue": 30,
    "standard_days_overdue": 7,
    "min_days_between_followups": 3,
    "wait_short_days": 3,
    "wait_long_days": 7,
}

TONE_PREFERENCE_BY_RELATIONSHIP = {
    "vip": "soft",
    "new": "soft",
    "recurring": "neutral",
    "risky": "firm",
}
