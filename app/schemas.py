import json
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


IssueType = Literal[
    "bug",
    "feature",
    "question",
    "duplicate",
    "documentation",
    "invalid",
    "needs-info",
    "maintenance",
]

Priority = Literal["P0", "P1", "P2", "P3"]

RiskLevel = Literal["low", "medium", "high"]


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_type: IssueType
    priority: Priority
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1, max_length=1200)
    suggested_labels: List[str] = Field(default_factory=list, max_length=10)
    missing_information: List[str] = Field(default_factory=list, max_length=12)
    risk_level: RiskLevel
    draft_comment: str = Field(min_length=1, max_length=3000)
    reasoning_summary: str = Field(min_length=1, max_length=1200)

    @field_validator("summary", "draft_comment", "reasoning_summary")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("Text fields must not be empty.")
        return clean

    @field_validator("suggested_labels", "missing_information")
    @classmethod
    def clean_string_list(cls, values: List[str]) -> List[str]:
        clean_values = []
        seen = set()

        for value in values:
            clean = value.strip().lower()
            if clean and clean not in seen:
                clean_values.append(clean)
                seen.add(clean)

        return clean_values


def parse_triage_json(raw_json: str) -> TriageResult:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model output is not valid JSON: {exc}") from exc

    return TriageResult.model_validate(data)


def triage_schema_json() -> Dict[str, Any]:
    return TriageResult.model_json_schema()
