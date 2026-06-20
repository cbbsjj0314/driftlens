# AGENTS.md

## Purpose

Repository-level instructions for coding agents working on DriftLens.

Keep this file short. Put detailed repeatable procedures in `docs/runbook/`.

## Project Context

### Project Identity

DriftLens is a local-first tool for detecting schema drift in external API or fixture JSON responses and producing operator-facing impact reports for data pipeline operators.

### Current Working Surface

The current implemented flow is `driftlens detect previous.json current.json --out-dir ...`: compare two stored JSON response snapshots, write deterministic schema/diff/severity artifacts, and optionally generate an LLM-assisted Markdown report.

### Non-goals

DriftLens is not an API collector, scheduler, alerting system, Steam semantic classifier, auto-fixer, or full data reliability platform.

## Core Boundary

* Deterministic code extracts observed schemas.
* Deterministic code computes schema diffs.
* Deterministic rules classify drift severity.
* LLM output is an operator-facing explanation and report layer only.
* Do not use LLM output as the source of truth for schema extraction, diffing, or severity.

## Working Rules

* Before changing files, state a short plan and relevant assumptions.
* Prefer the smallest useful slice that satisfies the task.
* Do not add speculative abstractions, broad configurability, or future platform behavior.
* Touch only files required by the current task.
* Do not reformat, rename, or refactor unrelated code.
* Ask for clarification when task boundary, data contract, or runtime boundary is ambiguous.
* Prefer repo-grounded evidence from code, tests, docs, and `docs/local/NEXT.md`.
* Do not create branches, commits, or pull requests unless the user explicitly asks.

## Default Scope

* Keep fixture-first local execution working.
* Do not add DB, collector, scheduler, alerting, release workflow, or automation platform code unless explicitly requested.
* For Steam `appdetails` examples, compare the prepared `response[appid]["data"]` inner object snapshot when the goal is schema drift in game data, not top-level appid wrapper differences.
* Use sanitized fixtures and examples only.

## Documentation Boundary

* Write durable human-facing docs in Korean by default.
* Agent-facing instruction files may use English when useful for tool compatibility.
* For detailed documentation style, translation, and inventory classification guidance, follow `docs/runbook/documentation-style.md`.
* Do not translate code-facing identifiers such as `endpoint`, `route`, `loader`, `table`, `view`, `CLI`, command names, module names, function names, config keys, or filenames.
* Keep `docs/local/` as local-only working material, not a public changelog.
* `docs/local/NEXT.md` is a local execution board. Keep it short and do not turn it into a detailed progress log.
* Do not put secrets, raw third-party payloads, private/local paths, provider account details, or private runtime data in public docs, prompts, logs, screenshots, fixtures, or reports.

## Validation

Use `uv`.

For runtime/code changes, run:

* `./scripts/check.sh`

For optional `llm` provider changes, run:

* `uv sync --locked --extra llm`
* `./scripts/check-llm.sh`

For package/build related changes, run:

* `./scripts/check-package.sh`

For CLI behavior changes, `./scripts/check.sh` includes a narrow fixture-based smoke. Add a focused CLI smoke only when the changed behavior is not covered by the default smoke.

For docs-only changes, runtime validation may be skipped. Instead, reread the changed docs and check for outdated claims, duplicated guidance, overbroad scope promises, and public exposure of secrets, raw payloads, private paths, or provider account details.

If validation cannot run, report the command attempted, failure reason, and what was still verified.

## Reporting After Changes

After making changes, summarize:

* files changed
* what was implemented
* validation result
* what was explicitly deferred
* any risks, notes, or user confirmation needed

For security-related changes, also summarize what was exposed or potentially exposed, what was rotated or revoked, and what remains deferred.

## Git Conventions

Only when the user explicitly asks for git actions:

* Prefer one branch per current work item.
* Use commit subjects like `type(scope): summary`.
* Suggested types: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`.
