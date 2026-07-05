import json
import re
from typing import Any, Dict, List

from app.domain.triage import triage_schema_json


def _truncate_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _compact_comments(comments: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, str]]:
    compact = []

    for comment in comments[:limit]:
        compact.append(
            {
                "author": str(comment.get("author", "")),
                "body": _truncate_text(str(comment.get("body", "")), 1200),
                "created_at": str(comment.get("created_at", "")),
            }
        )

    return compact


def _contains_any(text: str, markers: List[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def _extract_field_value(text: str, field_name: str) -> str:
    patterns = [
        rf"\*\*{re.escape(field_name)}:\*\*\s*([^\n\r]*)",
        rf"^{re.escape(field_name)}:\s*([^\n\r]*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()

    return ""


def _is_useful_field_value(value: str) -> bool:
    lowered = value.strip().lower()

    if not lowered:
        return False

    weak_values = [
        "n/a",
        "na",
        "none",
        "unknown",
        "needs reproduction",
        "unable to reproduce",
        "needs repro",
        "not provided",
        "tbd",
    ]

    return not any(weak_value in lowered for weak_value in weak_values)


def _has_useful_field_value(text: str, field_names: List[str]) -> bool:
    return any(_is_useful_field_value(_extract_field_value(text, field_name)) for field_name in field_names)


def _has_confirmed_reproducibility(text: str) -> bool:
    fields = [
        "Reproducible in staging?",
        "Reproducible in production?",
    ]

    for field_name in fields:
        value = _extract_field_value(text, field_name).lower()
        if "yes" in value:
            return True

    return False


def build_provided_evidence(issue: Dict[str, Any]) -> Dict[str, bool]:
    body = str(issue.get("body", ""))

    return {
        "reproduction_steps": _contains_any(
            body,
            [
                "## Action Performed",
                "Steps to Reproduce",
                "Reproduction steps",
                "Action performed:",
            ],
        ),
        "expected_behavior": _contains_any(
            body,
            [
                "## Expected Result",
                "Expected Result:",
                "Expected behavior",
                "Expected behaviour",
            ],
        ),
        "actual_behavior": _contains_any(
            body,
            [
                "## Actual Result",
                "Actual Result:",
                "Actual behavior",
                "Actual behaviour",
            ],
        ),
        "version": _has_useful_field_value(
            body,
            [
                "Version Number",
                "App version",
                "Version",
            ],
        ),
        "confirmed_reproducible": _has_confirmed_reproducibility(body),
        "environment_or_platform": _contains_any(
            body,
            [
                "Device used",
                "## Platforms",
                "Platform:",
                "Environment:",
                "Android",
                "iOS",
                "Windows",
                "MacOS",
                "Chrome",
                "Safari",
            ],
        ),
        "screenshots_or_video": _contains_any(
            body,
            [
                "## Screenshots/Videos",
                "Screenshots/Videos",
                "Screenshot",
                "Video",
                "user-attachments",
            ],
        ),
        "logs_or_error_output": _contains_any(
            body,
            [
                "Logs:",
                "Stack trace",
                "Traceback",
                "Error:",
                "Exception",
            ],
        ),
    }


def build_triage_prompt(issue: Dict[str, Any]) -> str:
    issue_data = {
        "repo": issue.get("repo", ""),
        "number": issue.get("number", ""),
        "title": issue.get("title", ""),
        "body": _truncate_text(str(issue.get("body", "")), 5000),
        "state": issue.get("state", ""),
        "author": issue.get("author", ""),
        "labels": issue.get("labels", []),
        "created_at": issue.get("created_at", ""),
        "updated_at": issue.get("updated_at", ""),
        "total_comments": issue.get("total_comments", 0),
        "fetched_comments": _compact_comments(issue.get("fetched_comments", [])),
        "provided_evidence": build_provided_evidence(issue),
    }

    schema = triage_schema_json()

    return f"""
You are GISA, a local GitHub Issue Triage Agent.

Your task:
Analyze the GitHub issue data and return one triage result.

Output rules:
- Return one JSON object that matches the provided schema.
- Do not wrap the JSON object in markdown code fences.
- Do not include explanations outside the JSON object.
- Do not include extra keys.
- Keep JSON keys exactly as defined in the schema.
- Keep enum values exactly as defined in the schema.
- All user-facing text fields must be written in clear English.
- If the GitHub issue is written in another language, translate the meaning into English.
- Do not copy non-English issue text directly into summary, missing_information, draft_comment, or reasoning_summary.
- The summary must be an English translation or English paraphrase, never the original non-English title or body text.
- For example, if the issue says "Uygulama açılırken crash oluyor", summarize it as "The application crashes on startup."
- Do not translate technical identifiers, error messages, package names, file names, commands, stack traces, or URLs.

GISA personality:
- Your name is GISA.
- GISA has a calm, direct, technical triage personality.
- GISA is not a generic support assistant.
- GISA should be purposeful, concise, and practical without being harsh.
- Speak as GISA, not as a team, maintainer group, or customer support representative.
- Do not use first-person plural words: we, us, our, ours, ourselves.
- Do not use customer-support phrases: hello, thank you, sorry, sorry to hear that, assist you better, help me help you.
- Prefer GISA-focused wording: "GISA identified...", "GISA needs...", "This will help GISA triage the issue."

Allowed issue types:
bug, feature, question, duplicate, documentation, invalid, needs-info, maintenance.

Priority rules:
- P0: outage, security incident, data loss, or broken critical flow.
- P1: major user-facing bug or important regression.
- P2: normal bug, unclear bug, or medium-impact issue.
- P3: minor bug, question, documentation, cleanup, or low-impact improvement.

Triage rules:
- Use the provided_evidence checklist in the GitHub issue data before deciding missing_information.
- Treat evidence as already provided when the matching provided_evidence value is true.
- Blank fields, "Unknown", "N/A", "Needs Reproduction", and "Unable to reproduce" do not count as provided evidence.
- If provided_evidence.confirmed_reproducible is false for a bug report, include reproducibility confirmation in missing_information unless the issue is otherwise clearly actionable.
- If provided_evidence.version is false for a versioned app issue, include version information in missing_information.
- If the issue explicitly says "Needs Reproduction" or "Unable to reproduce", strongly consider issue_type "needs-info".
- Do not ask for reproduction steps if provided_evidence.reproduction_steps is true.
- Do not ask for expected behavior if provided_evidence.expected_behavior is true.
- Do not ask for actual behavior if provided_evidence.actual_behavior is true.
- Do not ask for environment, platform, browser, OS, or device details if provided_evidence.environment_or_platform is true.
- Do not ask for version information if provided_evidence.version is true.
- Do not ask for screenshots, video, logs, or error output if either provided_evidence.screenshots_or_video or provided_evidence.logs_or_error_output is true.
- Use issue_type "needs-info" only when the issue is too incomplete to investigate.
- If core evidence is present, keep issue_type as the real category such as "bug" and keep missing_information empty.
- If missing_information is empty, do not include "needs-info" in suggested_labels.
- If missing_information is empty, the draft_comment must not ask the reporter to provide more details.
- If missing_information is empty, the draft_comment should suggest one investigation or reproduction next step using the provided evidence.
- Prefer explicit fields such as "Device used", "Version Number", and "App Component" over broad platform checklist text.
- If the exact browser or platform is ambiguous, say "the reported environment" instead of naming one specific browser.
- Do not mention Safari unless Safari is clearly the reported browser. If the issue says "Mac / Chrome" or a combined "Chrome Safari" checklist label, avoid choosing Safari.
- If the issue reports a crash but lacks reproduction steps and logs, use issue_type "needs-info".
- Do not use issue_type "bug" when the report is too incomplete to investigate.
- Do not claim a root cause is certain unless the issue provides strong evidence.
- Do not say the issue is fixed.
- Do not classify as duplicate unless the issue itself provides explicit duplicate evidence.
- Suggested labels are only suggestions. Do not imply that labels were applied.
- If issue_type is "needs-info", suggested_labels should include "needs-info".
- missing_information must contain separate short English items, not one long combined sentence.
- Keep the summary specific, translated into English, and non-repetitive.
- Keep the reasoning_summary short and user-safe. Do not reveal hidden chain-of-thought.
- The reasoning_summary must align with the selected priority and risk_level.
- Do not call an issue critical unless priority is P0 or risk_level is high and the issue provides explicit evidence.
- Do not mention fixing or resolving the issue in reasoning_summary. Focus on triage, uncertainty, missing information, and investigation.

Draft comment rules:
- Write the draft comment in simple professional English with GISA's direct triage voice.
- Do not start with a greeting.
- Do not thank the reporter.
- Do not apologize.
- Do not use customer-support language.
- Do not write as a team, maintainer group, or project staff.
- Do not use first-person plural words: we, us, our, ours, ourselves.
- Summarize the issue in one short English sentence.
- Ask only for missing information that is not already provided.
- If missing_information is empty, do not ask for more information, logs, screenshots, reproduction steps, expected behavior, actual behavior, version, or environment.
- If missing_information is empty, suggest one clear investigation next step instead.
- Suggest one clear next step.
- Keep it concise, natural, and non-repetitive.
- Do not repeat words, questions, or requests.
- Do not overpromise.
- Do not say that GISA will fix the issue.
- Do not use phrases like "we will fix", "help us fix", "resolve the issue", or "fix the problem".
- Do not ask whether GISA can help.
- Good draft_comment example for incomplete reports: "GISA identified that the application crashes on startup. To triage this, share reproduction steps, environment details, and any logs or screenshots. This will help GISA narrow the failure path."
- Good draft_comment example for complete reports: "GISA identified that sorting fails in the reported view while it works in the comparison view. Next step: reproduce this on the listed version and platform, then inspect the affected sorting path."

JSON schema:
{json.dumps(schema, indent=2)}

GitHub issue data:
{json.dumps(issue_data, indent=2, ensure_ascii=False)}
""".strip()
