from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from src.agents import run_context_agent, run_decision_agent
from src.graph import build_workflow
from src.io.loader import load_invoices
from src.io.writer import write_markdown_report
from src.state import FollowupState

app = typer.Typer(add_completion=False)
console = Console()


@app.command("run")
def run_followups(
    path: str = typer.Argument(..., help="Path to CSV or Excel invoice file."),
    output: str = typer.Option(
        "outputs/report.md", help="Output path for the Markdown report."
    ),
    limit: Optional[int] = typer.Option(
        None, help="Limit number of invoice rows processed."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Skip LLM message generation."
    ),
    format: str = typer.Option(
        "md", "--format", help="Output format (only md supported)."
    ),
) -> None:
    load_dotenv()
    if format != "md":
        raise typer.BadParameter("Only --format md is supported.")

    if not dry_run and not os.getenv("OPENAI_API_KEY"):
        raise typer.BadParameter(
            "OPENAI_API_KEY is required unless --dry-run is set."
        )

    invoices = load_invoices(path)
    if limit:
        invoices = invoices[:limit]

    workflow = build_workflow()
    results: List[FollowupState] = []
    for invoice in invoices:
        state: FollowupState = {"invoice_data": invoice}
        if dry_run:
            state = _run_without_message(state)
        else:
            state = workflow.invoke(state)
        results.append(state)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_markdown_report(results, str(output_path))
    _render_summary(results, str(output_path))


def _run_without_message(state: FollowupState) -> FollowupState:
    # run through context and decision nodes only, skip message generation
    state = run_context_agent(state)
    state = run_decision_agent(state)
    return state


def _render_summary(states: List[FollowupState], output_path: str) -> None:
    table = Table(title="Follow-up Summary")
    table.add_column("Invoice ID")
    table.add_column("Client")
    table.add_column("Timing")
    table.add_column("Tone")
    table.add_column("Follow-up")

    for state in states:
        invoice = state["invoice_data"]
        decision = state.get("decision")
        timing = decision.recommended_timing if decision else "unknown"
        tone = decision.tone if decision else "unknown"
        required = (
            "yes"
            if decision and decision.followup_required
            else "no"
            if decision
            else "unknown"
        )
        table.add_row(invoice.invoice_id, invoice.client_name, timing, tone, required)

    console.print(table)
    console.print(f"Report written to {output_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
