import argparse

from rich.console import Console

from app.application.analyze_issue import AnalyzeIssueUseCase
from app.config import load_settings
from app.infrastructure.github_client import GitHubClient, GitHubClientError
from app.infrastructure.llm_client import OllamaClient
from app.presentation.renderer import render_analysis
from app.triage_agent import TriageAgent, TriageAgentError


console = Console()


def analyze_command(args: argparse.Namespace) -> int:
    settings = load_settings()

    github_client = GitHubClient(token=settings.github_token)
    llm_client = OllamaClient(
        host=settings.ollama_host,
        model=settings.ollama_model,
    )
    triage_agent = TriageAgent(llm_client=llm_client)
    use_case = AnalyzeIssueUseCase(
        issue_fetcher=github_client,
        triage_agent=triage_agent,
    )

    try:
        result = use_case.execute(repo=args.repo, issue_number=args.issue)
    except GitHubClientError as exc:
        console.print(f"[bold red]GitHub fetch failed:[/bold red] {exc}")
        return 1
    except TriageAgentError as exc:
        console.print(f"[bold red]Triage failed:[/bold red] {exc}")
        return 1

    render_analysis(issue=result.issue, triage=result.triage)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GISA local GitHub Issue Triage Agent MVP")
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
