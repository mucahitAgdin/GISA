import json
from typing import Any, Dict, List

from app.schemas import triage_schema_json


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
- User-facing text fields should match the issue language when the language is clear.
- If the issue language is unclear or mixed, use English.
- Do not translate technical identifiers, error messages, package names, file names, commands, stack traces, or URLs.

Allowed issue types:
bug, feature, question, duplicate, documentation, invalid, needs-info, maintenance.

Priority rules:
- P0: outage, security incident, data loss, or broken critical flow.
- P1: major user-facing bug or important regression.
- P2: normal bug, unclear bug, or medium-impact issue.
- P3: minor bug, question, documentation, cleanup, or low-impact improvement.

Triage rules:
- Use needs-info when key details are missing, such as reproduction steps, expected behavior, actual behavior, environment, logs, screenshots, or version information.
- Do not claim a root cause is certain unless the issue provides strong evidence.
- Do not say the issue is fixed.
- Do not classify as duplicate unless the issue itself provides explicit duplicate evidence.
- Suggested labels are only suggestions. Do not imply that labels were applied.
- Keep the summary specific and non-repetitive.
- Keep the reasoning_summary short and user-safe. Do not reveal hidden chain-of-thought.

Draft comment rules:
- Thank the reporter briefly.
- Summarize the issue in one short sentence.
- Ask only for missing information that is not already provided.
- Suggest one clear next step.
- Keep it concise, natural, and non-repetitive.
- Do not overpromise.
- Do not say that you will fix the issue.

JSON schema:
{json.dumps(schema, indent=2)}

GitHub issue data:
{json.dumps(issue_data, indent=2, ensure_ascii=False)}
""".strip()
