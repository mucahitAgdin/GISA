import argparse
import json
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.config import load_settings
from app.github_client import GitHubClient, GitHubClientError


console = Console()


def _preview(text: str, limit: int = 500) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def render_issue(issue: Dict[str, Any]) -> None:
    table = Table(title="GitHub Issue Fetch Result")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Repository", issue["repo"])
    table.add_row("Issue", str(issue["number"]))
    table.add_row("State", issue["state"])
    table.add_row("Author", issue["author"])
    table.add_row("Labels", ", ".join(issue["labels"]) if issue["labels"] else "None")
    table.add_row("Created", issue["created_at"])
    table.add_row("Updated", issue["updated_at"])
    table.add_row("Total comments", str(issue["total_comments"]))
    table.add_row("Fetched comments", str(len(issue["fetched_comments"])))
    table.add_row("GitHub token used", "yes" if issue["token_used"] else "no")

    console.print(table)
    console.print(Panel(_preview(issue["title"]), title="Title"))
    console.print(Panel(_preview(issue["body"]), title="Body Preview"))

    console.print("\nStructured JSON:")
    console.print(json.dumps(issue, indent=2, ensure_ascii=False))


def analyze_command(args: argparse.Namespace) -> int:
    settings = load_settings()
    client = GitHubClient(token=settings.github_token)

    try:
        issue = client.fetch_issue(repo=args.repo, issue_number=args.issue)
    except GitHubClientError as exc:
        console.print(f"[bold red]GitHub fetch failed:[/bold red] {exc}")
        return 1

    render_issue(issue)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GISA local GitHub Issue Solver Agent MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Fetch and analyze a GitHub issue")
    analyze_parser.add_argument("--repo", required=True, help="GitHub repository in owner/repo format")
    analyze_parser.add_argument("--issue", required=True, type=int, help="GitHub issue number")
    analyze_parser.set_defaults(func=analyze_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
