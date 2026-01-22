from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import date
from typing_extensions import TypedDict

class InvoiceRow(BaseModel):
    client_name: str
    invoice_id: str
    invoice_amount: float
    currency: str = Field(default="USD")
    invoice_issue_date: date
    days_overdue: int
    last_followup_date: Optional[date] = None
    relationship_tag: Literal["new", "recurring", "vip", "risky"]
    notes: str = ""

class InvoiceContext(BaseModel):
    risk_level: Literal["low", "medium", "high"]
    relationship_summary: str
    invoice_status_summary: str
    days_since_last_followup: Optional[int] = None
    context_summary: str

class FollowupDecision(BaseModel):
    followup_required: bool
    recommended_timing: Literal["now", "wait_3_days", "wait_7_days", "skip"]
    tone: Literal["soft", "neutral", "firm"]
    explanation: str


class FollowupMessage(BaseModel):
    subject: str
    body: str
    reasoning: str


class ControlResult(BaseModel):
    stage: Literal["decision", "message"]
    passed: bool
    violations: List[str] = Field(default_factory=list)

class FollowupState(TypedDict, total=False):
    invoice_data: InvoiceRow
    context: InvoiceContext
    decision: FollowupDecision
    message: FollowupMessage
    control_decision: ControlResult
    control_message: ControlResult
