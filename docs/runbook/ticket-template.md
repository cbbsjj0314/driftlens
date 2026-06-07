# Ticket template

## Goal

- 이 ticket이 달성해야 하는 결과

## Scope

- 이번 작업에 포함할 변경

## Non-goals

- 이번 작업에서 제외할 인접 변경

## Acceptance Criteria

- 완료로 판단할 수 있는 조건

## Required Checks

- Default runtime/code: `./scripts/check.sh`
- Optional `llm` provider: `uv sync --locked --extra llm` + `./scripts/check-llm.sh`
- Package/build: `./scripts/check-package.sh`
- Docs-only: changed docs reread

## Risk / Human Gate

- Risk: 낮음 / 중간 / 높음
- Human Gate: 필요 / 불필요
- 필요한 경우 확인 기준

## Notes

- 추가 맥락, caveat, assumption
