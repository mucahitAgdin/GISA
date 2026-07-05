from typing import Any, Dict

from pydantic import ValidationError

from app.infrastructure.llm_client import OllamaClient, OllamaClientError
from app.prompts.triage_prompt import build_triage_prompt
from app.domain.triage import TriageResult, parse_triage_json


class TriageAgentError(Exception):
    pass


class TriageAgent:
    def __init__(self, llm_client: OllamaClient) -> None:
        self.llm_client = llm_client

    def analyze_issue(self, issue: Dict[str, Any]) -> TriageResult:
        prompt = build_triage_prompt(issue)

        try:
            raw_response = self.llm_client.generate(prompt, json_mode=True)
        except OllamaClientError as exc:
            raise TriageAgentError(f"LLM call failed: {exc}") from exc

        try:
            return parse_triage_json(raw_response)
        except (ValueError, ValidationError) as exc:
            raise TriageAgentError(f"LLM output failed schema validation: {exc}") from exc
