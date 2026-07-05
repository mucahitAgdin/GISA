# GISA - GitHub Issue Triage Agent

GISA is a local GitHub Issue Triage Agent MVP.

It fetches a public GitHub issue, analyzes the issue with a local Ollama model, validates the model output with Pydantic, and prints both a readable terminal report and structured JSON.

The MVP is intentionally read-only. It does not post GitHub comments, apply labels, close issues, create pull requests, or modify repositories.

## What GISA does

For a GitHub issue, GISA returns:

- issue summary
- issue type
- suggested priority
- suggested labels
- missing information
- risk level
- confidence score
- draft GitHub comment
- short reasoning summary
- structured JSON output

Valid issue types: bug, feature, question, duplicate, documentation, invalid, needs-info, maintenance.

Valid priorities:

- P0: outage, security incident, data loss, or broken critical flow
- P1: major user-facing bug or important regression
- P2: normal bug, unclear bug, or medium-impact issue
- P3: minor bug, question, documentation, cleanup, or low-impact improvement

## Current MVP scope

Included:

- local CLI
- public GitHub issue fetch
- optional GitHub token support
- local Ollama model call
- strict Pydantic schema validation
- readable Rich terminal output
- structured JSON output
- generated example outputs
- no automatic GitHub write actions

Not included yet:

- RAG
- fine-tuning
- automatic GitHub comments
- automatic labels
- PR creation
- code patches
- paid APIs
- Docker
- complex agent frameworks

## Project structure

    main.py
    app/
      application/
        analyze_issue.py
        triage_agent.py
      domain/
        triage.py
      infrastructure/
        github_client.py
        llm_client.py
      presentation/
        renderer.py
      prompts/
        triage_prompt.py
    examples/
      eval_cases_expensify.json
      generated/
    tests/
    .env.example
    requirements.txt
    README.md

## Requirements

- Python 3.9+
- Git
- Ollama running locally
- A small local Ollama model, such as qwen2.5-coder:3b

## Setup

Create and activate a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt

Install and check Ollama separately, then pull the default model:

    ollama --version
    ollama pull qwen2.5-coder:3b
    ollama run qwen2.5-coder:3b "Return JSON: {\"status\":\"ok\"}"

Create a local .env file from the example:

    cp .env.example .env

Setup .env example values:

    GITHUB_TOKEN=
    OLLAMA_MODEL=qwen2.5-coder:3b
    OLLAMA_HOST=http://localhost:11434

GITHUB_TOKEN is optional for public repositories. If it is set, GISA uses it for GitHub API requests. Do not commit .env.

## Usage

Analyze a GitHub issue:

    python main.py analyze --repo owner/repo --issue 123

Example:

    python main.py analyze --repo Expensify/App --issue 94507 --max-comments 0

--max-comments controls how many issue comments are fetched.

    python main.py analyze --repo owner/repo --issue 123 --max-comments 20
    python main.py analyze --repo owner/repo --issue 123 --max-comments 0

Use --max-comments 0 when evaluating resolved issues to avoid leaking solution discussion from comments into the model prompt.

## Example outputs

Generated example outputs are stored under:

    examples/generated/

Current examples:

    examples/generated/expensify-94507-complete-bug.json
    examples/generated/expensify-95089-complete-bug.json
    examples/generated/expensify-95225-needs-info.json

These examples intentionally omit full issue report text and fetched comments. They are portfolio examples of GISA output, not training data.

## Evaluation cases

examples/eval_cases_expensify.json contains offline evaluation metadata for selected public Expensify/App issues and their linked fix PR references.

Important rule:

The fix PR data should not be included in the agent prompt. It is only for offline evaluation after GISA generates its triage result.

## Safety and token handling

GISA is read-only.

It does not:

- post GitHub comments
- apply labels
- close or reopen issues
- create PRs
- push code changes
- modify remote repositories

Token rules:

- use .env for local secrets
- keep .env out of git
- keep .env.example safe and empty
- never hardcode GitHub tokens in source code
- public repositories should work without a token when GitHub rate limits allow it

## Limitations

This is an MVP. The model can still make mistakes.

Known limitations:

- classification quality depends on issue quality and the local model
- duplicate detection is not implemented
- repository-specific knowledge is not available yet
- generated draft comments are suggestions only
- priority is heuristic and should be reviewed by a human
- GitHub API rate limits may apply without a token

## Roadmap

Possible next steps after the MVP:

- add basic automated tests
- add more generated examples
- add a small evaluation script
- improve README screenshots or terminal demo
- add RAG for repo-specific context, docs, similar issues, and source files
- consider fine-tuning only after collecting real triage examples

Repo-specific knowledge belongs in RAG, not fine-tuning.

## MVP definition of done

- CLI runs locally
- public GitHub issue fetch works
- missing GitHub token is handled safely
- Ollama call works locally
- output validates against schema
- terminal output is readable
- at least 3 example outputs exist under examples/
- README explains setup, usage, limitations, and roadmap
- no token is committed
- no automatic GitHub write action exists
- code is simple enough to explain in an interview
