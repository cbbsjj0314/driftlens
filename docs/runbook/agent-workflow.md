# Agent 작업 workflow

## 목적

이 문서는 DriftLens에서 AI coding agent에게 작업을 맡기기 전후에 확인할 수 있는 수동 workflow와 검토 기준을 정리한다.

목표는 자동화 플랫폼을 만드는 것이 아니라, 반복해서 prompt에 넣던 작업 규칙을 repo 안의 durable 문서로 옮겨 짧고 일관된 작업 지시를 가능하게 하는 것이다.

이 workflow는 DriftLens의 lightweight PR-native 작업 모델이다. Release는 개념적 endpoint로만 볼 수 있으며, 이 문서는 release automation이나 publishing process를 추가하지 않는다.

## 언제 사용하는가

다음 상황에서 이 runbook을 참조한다.

- repo-level 작업 규칙을 agent에게 짧게 전달해야 할 때
- 변경 전 precheck와 작업 boundary를 맞춰야 할 때
- docs-only 변경과 runtime 변경의 validation 기준을 구분해야 할 때
- 작업 완료 보고 형식을 일관되게 유지해야 할 때
- public docs에 올릴 수 있는 내용과 local-only 자료를 구분해야 할 때

## 기본 workflow

기본 흐름은 다음 순서를 따른다.

1. Spec / Ticket
2. Agent implementation
3. PR
4. CI checks
5. Review
6. Human Gate

Spec / Ticket은 작업을 충분히 명확하게 만드는 수단이다. 모든 PR에 formal ticket이나 issue가 필요한 것은 아니다. 작은 docs/test/runtime fix는 PR body 자체를 lightweight spec으로 사용할 수 있다.

이 workflow는 agent에게 반복 가능한 경계를 주기 위한 수동 절차다. DriftLens를 automation platform, release platform, scheduler, alerting system으로 확장하는 근거로 쓰지 않는다.

## Ticket types

DriftLens에서는 다음 ticket 형태를 우선 사용한다.

- `Atomic ticket`: 하나의 작은 구현 slice를 지정한다. 목표, scope, non-goals, required checks가 분명해야 한다.
- `Read-only review`: code, docs, PR, CI 결과를 읽고 risk와 gap을 찾는다. 파일 수정, branch, commit, PR 생성은 하지 않는다.
- `Planning-contract ticket`: 바로 구현하지 않고 contract, boundary, validation 방법을 확정한다. schema, diff, severity, LLM provider boundary가 애매할 때 사용한다.

## 작업 전 precheck

작업을 시작하기 전에 agent는 먼저 repo의 현재 상태를 확인한다.

- `AGENTS.md`, `README.md`, `.gitignore`, `pyproject.toml`처럼 작업 판단에 필요한 public 파일을 읽는다.
- 필요한 경우 `docs/local/` 아래 local working docs를 확인할 수 있는지 확인한다.
- local docs를 읽을 수 없고 작업 판단에 꼭 필요하면, 어떤 내용이 필요한지 사용자에게 요청한다.
- public 파일만으로 판단 가능한 내용과 local docs가 필요한 내용을 구분한다.
- 요청이 docs-only인지 runtime/code 변경인지 구분한다.
- task boundary, data contract, runtime boundary가 모호하면 수정 전에 질문한다.
- DriftLens의 source of truth가 deterministic schema extraction, schema diff, rule-based severity classification인지 확인한다.

작업 전 짧은 plan에는 다음을 포함한다.

- 읽은 파일
- 선택한 smallest useful slice
- 변경할 파일
- 변경하지 않을 파일
- validation 계획
- out-of-scope 확인

## 작업 중 원칙

작업은 요청된 slice에 맞춰 작게 진행한다.

- 가장 작은 유용한 변경을 우선한다.
- speculative abstraction이나 미래 platform 동작을 추가하지 않는다.
- unrelated formatting, rename, refactor를 하지 않는다.
- fixture-first local execution 경계를 유지한다.
- DriftLens를 API collector, scheduler, alerting system, Steam semantic classifier, auto-fixer로 설명하거나 확장하지 않는다.
- deterministic logic과 LLM layer를 섞지 않는다.
- LLM output은 operator-facing explanation 또는 Markdown report 생성에만 사용한다.
- schema extraction, schema diff, severity classification의 판단 근거는 deterministic output이어야 한다.
- branch, commit, PR, tag, release는 사용자가 해당 task에서 명시적으로 요청하지 않으면 만들지 않는다.
- force-push 또는 `main` push는 사용자가 해당 task에서 명시적으로 요청하지 않으면 하지 않는다.
- 요청된 scope를 adjacent product feature로 넓히지 않는다.

## Human Gate

Human Gate는 agent가 구현이나 검토를 마친 뒤 사람이 반드시 확인해야 하는 지점을 뜻한다.

다음 변경은 Human Gate Required로 취급한다.

- schema extraction contract 변경
- schema diff output shape 변경
- severity classification rule 변경
- artifact path 또는 `summary.json` shape 변경
- LLM prompt, response schema, provider behavior 변경
- secret을 사용하는 real provider smoke
- public docs 또는 fixtures에 raw payload, private path, provider account detail, private runtime data가 노출될 수 있는 변경
- CI permissions, release, publishing, package distribution 변경

Human Gate가 필요한 변경은 PR의 `Risk / Human Gate`에 이유와 확인 기준을 짧게 적는다.

## Validation guide

변경 유형에 따라 validation을 다르게 적용한다.

Docs-only 변경:

- 변경한 문서를 직접 다시 읽는다.
- 중복, 오래된 표현, 과한 scope 약속이 없는지 확인한다.
- `AGENTS.md`와 runbook의 역할 중복이 과하지 않은지 확인한다.
- public docs에 secret, raw third-party payload, private/local path, provider account detail, private runtime data가 없는지 확인한다.
- runtime 파일을 건드리지 않았다면 `uv run pytest`와 `uv run ruff check .`는 생략할 수 있다.

Runtime/code 변경:

- `uv run ruff check .`
- `uv run pytest`

CLI behavior를 건드린 경우:

- 관련 `uv run driftlens ... --help`를 확인한다.
- 필요하면 좁은 smoke command로 실제 입력과 output 생성을 확인한다.

Validation을 실행할 수 없으면 완료 보고에 다음을 남긴다.

- 시도한 command
- 실패 이유
- 대신 확인한 내용

## Reporting format

작업 완료 보고는 다음 형식을 기본으로 한다.

1. 변경 파일
2. 변경 요약
3. 검증 결과
4. 명시적으로 제외한 것
5. 사용자 확인이 필요한 점

보고는 짧고 구체적으로 작성한다. 코드나 문서를 변경했다는 사실만으로 완료를 주장하지 말고, 어떤 검증을 했는지 함께 적는다.

PR body는 `.github/PULL_REQUEST_TEMPLATE.md`를 따른다. `Ticket / Spec`은 optional이며, 관련 ticket이나 spec이 없으면 지울 수 있다. CI 결과가 확인 가능하면 `Required Checks / CI`에 적는다.

Security 관련 변경이라면 다음도 포함한다.

- 노출됐거나 노출 가능성이 있었던 것
- rotate 또는 revoke한 것
- 남은 deferred 항목

## Local data governance

Public docs에는 안정된 사용법, 설계 원칙, 검토 기준만 남긴다.

다음 내용은 public docs, prompt, log, screenshot, fixture, report에 넣지 않는다.

- API key, token, credential
- raw third-party payload
- private endpoint detail
- private/local path
- provider account detail
- private runtime data
- 임시 실행 log 전문

Public docs에는 sanitized example만 사용한다. Local working docs는 임시 판단과 handoff에 쓸 수 있지만 secret이나 raw private data를 담지 않는다.
