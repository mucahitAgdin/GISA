import json
from typing import Any, Dict, List, Literal, Optional

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


_INFO_REQUEST_MARKERS = [
    "please provide",
    "please share",
    "share any",
    "share reproduction",
    "share logs",
    "share screenshots",
    "provide logs",
    "provide screenshots",
    "provide more details",
    "share more details",
    "to triage this, share",
    "to triage this, please",
    "can you provide",
    "need more information",
    "needs more information",
    "add logs",
    "upload",
]

_INCONSISTENT_REASONING_MARKERS = [
    "lacks ",
    "missing ",
    "not provided",
    "does not provide",
    "needs more",
    "needs additional",
    "requires more",
    "no logs",
    "no actual behavior",
    "no screenshots",
    "more information",
    "additional information",
    "without additional",
    "difficult to determine",
    "difficult to investigate",
    "cannot investigate",
    "would help",
    "lack of",
    "given the lack",
]


def _contains_marker(text: str, markers: List[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _missing_item_is_already_provided(item: str, provided_evidence: Dict[str, bool]) -> bool:
    lowered = item.lower()

    if provided_evidence.get("reproduction_steps") and any(term in lowered for term in ["reproduction", "reproduce", "steps", "action performed"]):
        return True

    if provided_evidence.get("expected_behavior") and "expected" in lowered:
        return True

    if provided_evidence.get("actual_behavior") and "actual" in lowered:
        return True

    if provided_evidence.get("version") and "version" in lowered:
        return True

    if provided_evidence.get("confirmed_reproducible") and "reproducibility" in lowered:
        return True

    if provided_evidence.get("environment_or_platform") and any(
        term in lowered for term in ["environment", "platform", "browser", "os", "device"]
    ):
        return True

    if (provided_evidence.get("screenshots_or_video") or provided_evidence.get("logs_or_error_output")) and any(
        term in lowered for term in ["screenshot", "screenshots", "video", "logs", "log", "error output"]
    ):
        return True

    return False


def _filter_missing_information(
    missing_information: List[str],
    provided_evidence: Optional[Dict[str, bool]],
) -> List[str]:
    if not provided_evidence:
        return list(missing_information)

    return [
        item
        for item in missing_information
        if not _missing_item_is_already_provided(item, provided_evidence)
    ]




def _safe_complete_report_comment(summary: str) -> str:
    clean_summary = " ".join(summary.split()).strip().rstrip(".")

    return (
        f"GISA identified this issue: {clean_summary}. "
        "Next step: reproduce the reported behavior using the provided evidence, "
        "then inspect the likely affected code path."
    )


def _safe_complete_report_reasoning() -> str:
    return (
        "The issue includes core triage evidence such as reproduction steps, expected behavior, "
        "actual behavior, version, environment, and supporting media. The selected priority reflects "
        "a reproducible product bug without evidence of outage, security incident, data loss, "
        "or a broken critical flow."
    )


def _format_missing_information_items(missing_information: List[str]) -> str:
    if len(missing_information) == 1:
        return missing_information[0]

    if len(missing_information) == 2:
        return f"{missing_information[0]} and {missing_information[1]}"

    return f"{', '.join(missing_information[:-1])}, and {missing_information[-1]}"


def _safe_needs_info_comment(summary: str, missing_information: List[str]) -> str:
    clean_summary = " ".join(summary.split()).strip().rstrip(".")
    missing_items = _format_missing_information_items(missing_information)

    return (
        f"GISA identified this issue: {clean_summary}. "
        f"To triage this, share {missing_items}. "
        "This will help GISA narrow the failure path."
    )


def normalize_triage_result(
    result: TriageResult,
    provided_evidence: Optional[Dict[str, bool]] = None,
) -> TriageResult:
    suggested_labels = list(result.suggested_labels)
    missing_information = _filter_missing_information(result.missing_information, provided_evidence)
    draft_comment = result.draft_comment
    reasoning_summary = result.reasoning_summary
    issue_type = result.issue_type

    if not missing_information:
        suggested_labels = [label for label in suggested_labels if label != "needs-info"]

        if issue_type == "needs-info":
            issue_type = "bug"

        if _contains_marker(draft_comment, _INFO_REQUEST_MARKERS):
            draft_comment = _safe_complete_report_comment(result.summary)

        if _contains_marker(reasoning_summary, _INCONSISTENT_REASONING_MARKERS):
            reasoning_summary = _safe_complete_report_reasoning()

    elif missing_information:
        if _contains_marker(draft_comment, _INFO_REQUEST_MARKERS):
            draft_comment = _safe_needs_info_comment(result.summary, missing_information)

        if issue_type == "needs-info" and "needs-info" not in suggested_labels:
            suggested_labels.append("needs-info")

    return result.model_copy(
        update={
            "issue_type": issue_type,
            "suggested_labels": suggested_labels,
            "missing_information": missing_information,
            "draft_comment": draft_comment,
            "reasoning_summary": reasoning_summary,
        }
    )


def _clean_model_json(raw_json: str) -> str:
    text = raw_json.strip()

    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").strip()

    if text.endswith("```"):
        text = text.removesuffix("```").strip()

    return text


def parse_triage_json(raw_json: str) -> TriageResult:
    cleaned_json = _clean_model_json(raw_json)

    try:
        data = json.loads(cleaned_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model output is not valid JSON: {exc}") from exc

    return TriageResult.model_validate(data)


def triage_schema_json() -> Dict[str, Any]:
    return TriageResult.model_json_schema()
