import json
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.domain.triage import TriageResult


console = Console()


def _preview(text: str, limit: int = 500) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _join_list(values: List[str]) -> str:
    return ", ".join(values) if values else "None"


def render_analysis(issue: Dict[str, Any], triage: TriageResult) -> None:
    issue_table = Table(title="GitHub Issue")
    issue_table.add_column("Field", style="bold")
    issue_table.add_column("Value")

    issue_table.add_row("Repository", str(issue.get("repo", "")))
    issue_table.add_row("Issue", str(issue.get("number", "")))
    issue_table.add_row("State", str(issue.get("state", "")))
    issue_table.add_row("Author", str(issue.get("author", "")))
    issue_table.add_row("Existing labels", _join_list(issue.get("labels", [])))
    issue_table.add_row("Created", str(issue.get("created_at", "")))
    issue_table.add_row("Updated", str(issue.get("updated_at", "")))
    issue_table.add_row("Fetched comments", str(len(issue.get("fetched_comments", []))))
    issue_table.add_row("GitHub token used", "yes" if issue.get("token_used") else "no")

    console.print(issue_table)
    console.print(Panel(_preview(str(issue.get("title", ""))), title="Issue Title"))
    console.print(Panel(_preview(str(issue.get("body", ""))), title="Issue Body Preview"))

    triage_table = Table(title="GISA Triage Result")
    triage_table.add_column("Field", style="bold")
    triage_table.add_column("Value")

    triage_table.add_row("Issue type", triage.issue_type)
    triage_table.add_row("Priority", triage.priority)
    triage_table.add_row("Risk level", triage.risk_level)
    triage_table.add_row("Confidence", f"{triage.confidence:.2f}")
    triage_table.add_row("Suggested labels", _join_list(triage.suggested_labels))
    triage_table.add_row("Missing information", _join_list(triage.missing_information))

    console.print(triage_table)
    console.print(Panel(triage.summary, title="Summary"))
    console.print(Panel(triage.draft_comment, title="Draft GitHub Comment"))
    console.print(Panel(triage.reasoning_summary, title="Reasoning Summary"))

    output = {
        "issue": issue,
        "triage": triage.model_dump(),
    }

    console.print("\nStructured JSON:")
    console.print(json.dumps(output, indent=2, ensure_ascii=False))
