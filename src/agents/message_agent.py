from __future__ import annotations
import json
import logging
from typing import Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from src.config import prompts, settings
from src.state import FollowupMessage, FollowupState

logger = logging.getLogger(__name__)


class MessageGenerationError(RuntimeError):
    pass


def run_message_agent(state: FollowupState) -> FollowupState:
    decision = state.get("decision")
    if decision is None:
        raise ValueError("Message agent requires decision in state.")

    if not decision.followup_required or decision.recommended_timing == "skip":
        return state

    invoice = state["invoice_data"]
    context = state.get("context")
    input_payload = {
        "invoice": _model_to_dict(invoice),
        "context": _model_to_dict(context),
        "decision": _model_to_dict(decision),
        "escalation_thresholds": settings.ESCALATION_THRESHOLDS,
    }
    input_json = json.dumps(input_payload, default=str)

    message = _generate_message(input_json=input_json)
    next_state = dict(state)
    next_state["message"] = message
    return next_state


@retry(
    retry=retry_if_exception_type(MessageGenerationError),
    stop=stop_after_attempt(settings.LLM_MESSAGE_MAX_RETRIES),
    wait=wait_exponential(
        min=settings.LLM_MESSAGE_BACKOFF_MIN_SECONDS,
        max=settings.LLM_MESSAGE_BACKOFF_MAX_SECONDS,
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _generate_message(input_json: str) -> FollowupMessage:
    llm = ChatOpenAI(
        model=settings.LLM_MESSAGE_MODEL,
        temperature=settings.LLM_MESSAGE_TEMPERATURE,
    )
    messages = [
        SystemMessage(content=prompts.MESSAGE_AGENT_SYSTEM_PROMPT),
        HumanMessage(
            content=prompts.MESSAGE_AGENT_USER_PROMPT.format(input_json=input_json)
        ),
    ]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)
    data = _parse_json(content)
    try:
        return FollowupMessage(**data)
    except ValidationError as exc:
        raise MessageGenerationError(f"Invalid message JSON: {exc}") from exc


def _parse_json(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        trimmed = content.strip()
        start = trimmed.find("{")
        end = trimmed.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(trimmed[start : end + 1])
            except json.JSONDecodeError as exc:
                raise MessageGenerationError("Failed to parse JSON response.") from exc
        raise MessageGenerationError("No JSON object found in response.")


def _model_to_dict(model: Optional[Any]) -> Optional[dict]:
    if model is None:
        return None
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return None
