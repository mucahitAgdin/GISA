from dataclasses import dataclass
from typing import Any, Dict, Protocol

from app.domain.triage import TriageResult
from app.application.triage_agent import TriageAgent


class IssueFetcher(Protocol):
    def fetch_issue(self, repo: str, issue_number: int) -> Dict[str, Any]:
        ...


@dataclass(frozen=True)
class AnalyzeIssueResult:
    issue: Dict[str, Any]
    triage: TriageResult


class AnalyzeIssueUseCase:
    def __init__(self, issue_fetcher: IssueFetcher, triage_agent: TriageAgent) -> None:
        self.issue_fetcher = issue_fetcher
        self.triage_agent = triage_agent

    def execute(self, repo: str, issue_number: int) -> AnalyzeIssueResult:
        issue = self.issue_fetcher.fetch_issue(repo=repo, issue_number=issue_number)
        triage = self.triage_agent.analyze_issue(issue)

        return AnalyzeIssueResult(issue=issue, triage=triage)
