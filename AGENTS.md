# AGENTS.md

## Purpose

Repository-level instructions for coding agents working on DriftLens.

## Project Context

DriftLens is a local-first schema drift monitor for external API and fixture JSON ingestion pipelines.

## Core Design Principle

* Deterministic code extracts observed schemas.
* Deterministic code computes schema diffs.
* Deterministic rules classify drift severity.
* LLM analysis is added later as an interpretation and reporting layer only.
* Do not mix deterministic schema logic with LLM analysis logic.

## Working Principles

### 1. Think Before Coding

* Before changing files, state a short plan.
* State assumptions when relevant.
* Ask for clarification when the task boundary, data contract, or runtime boundary is ambiguous.
* Prefer repo-grounded evidence from existing code, tests, docs, and docs/local/NEXT.md.
* For small obvious edits, keep the plan brief.

### 2. Simplicity First

* Implement the minimum successful path.
* No speculative abstractions.
* No features beyond the requested slice.
* No broad configurability before there is a real use case.
* Prefer simple functions before classes or frameworks.
* If a smaller implementation satisfies the task and tests, choose the smaller implementation.

### 3. Surgical Changes

* Touch only what the current task requires.
* Do not refactor adjacent code unless required.
* Do not reformat unrelated files.
* Do not rename modules or APIs unless required.
* If unrelated cleanup is noticed, mention it as deferred.
* Every material changed line should trace to the current request or its validation.

### 4. Goal-Driven Execution

* For non-trivial changes, define the smallest observable success criteria before editing.
* Prefer a failing test that describes the behavior.
* Prefer a narrow implementation that makes it pass.
* Prefer a verification command that proves the slice.
* Do not claim completion just because code changed.

## Current MVP Focus

Priority order:

1. Observed JSON schema extractor
2. Schema diff engine
3. Rule-based drift severity classifier
4. Artifact storage
5. CLI
6. Mock LLM provider
7. OpenAI-compatible LLM provider for DeepSeek/OpenAI

## Current Default Boundary

* Work on fixture-first local execution.
* Do not implement DB, CLI, reports, HTTP collection, storage, or LLM code unless the current task explicitly asks for it.
* Keep the first vertical slice small and testable.

## Project Structure

Use this layout:

* driftlens/
* tests/
* tests/fixtures/
* docs/
* docs/local/

## Guidelines

* Keep modules small.
* Keep tests close to behavior.
* Use sanitized fixtures.
* Do not commit secrets or private runtime data.

## Documentation Language

- Write durable human-facing docs in Korean by default.
- Write local working docs under `docs/local/` in Korean by default.
- Keep Korean prose concise and direct.
- Do not translate code-facing identifiers.
- Preserve actual code notation for names such as objects, endpoints, routes, loaders, tables, views, CLI commands, filenames, modules, classes, functions, and config keys.
- Examples:
  - Use `endpoint`, `route`, `loader`, `table`, `view`, and `CLI` when referring to code concepts.
  - Use `driftlens detect`, not a translated command name.
  - Use `api_samples`, not a translated table name.
- Agent-facing instruction files may use English when that improves tool compatibility.

## Tooling

Use uv.

After code changes, run:

* uv run ruff check .
* uv run pytest

For docs-only changes, validation may be skipped if no runtime path changed.

If validation cannot run in the current environment, report:

* command attempted
* failure reason
* what was still verified

## Planning Board

* Use docs/local/NEXT.md as the local execution board when present.
* If a task changes the current Now/Next status, update docs/local/NEXT.md in the same slice.
* docs/local/ is local-only by default and must not contain secrets, raw private payloads, or environment-specific paths.

## Configuration and Secrets

* Never hardcode API keys.
* Use environment variables for LLM credentials.
* Commit .env.example only.
* Keep .env out of git.
* Do not include secrets in prompts, docs, logs, screenshots, or test fixtures.

## Reporting After Changes

After making changes, summarize:

* files changed
* what was implemented
* what was explicitly deferred
* how to run and verify

For security-related changes, also summarize:

* what was exposed or potentially exposed
* what was rotated or revoked
* what remains deferred

## Git Conventions

* Prefer one branch per Now item.
* Commit message format: type(scope): summary
* Suggested types: feat, fix, test, docs, chore, refactor
* Example commit subjects:

  * test(schema): add flat JSON extractor coverage
  * feat(schema): implement flat observed schema extraction
  * docs(agent): add DriftLens working rules
