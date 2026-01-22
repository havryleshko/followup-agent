from __future__ import annotations
from langgraph.graph import END, StateGraph
from src.agents import (
    run_context_agent,
    run_decision_agent,
    run_message_agent,
    run_control_agent,
)
from src.state import FollowupState

def _context_node(state: FollowupState) -> FollowupState:
    return run_context_agent(state)


def _decision_node(state: FollowupState) -> FollowupState:
    return run_decision_agent(state)


def _message_node(state: FollowupState) -> FollowupState:
    return run_message_agent(state)


def _control_decision_node(state: FollowupState) -> FollowupState:
    return run_control_agent(state, stage="decision")


def _control_message_node(state: FollowupState) -> FollowupState:
    return run_control_agent(state, stage="message")


def build_workflow():
    graph = StateGraph(FollowupState)
    graph.add_node("context_node", _context_node)
    graph.add_node("decision_node", _decision_node)
    graph.add_node("control_decision_node", _control_decision_node)
    graph.add_node("message_node", _message_node)
    graph.add_node("control_message_node", _control_message_node)

    graph.set_entry_point("context_node")
    graph.add_edge("context_node", "decision_node")
    graph.add_edge("decision_node", "control_decision_node")
    graph.add_edge("control_decision_node", "message_node")
    graph.add_edge("message_node", "control_message_node")
    graph.add_edge("control_message_node", END)

    return graph.compile()
