# Scheduled ingestion 진단 가이드

## 목적

이 문서는 scheduled ingestion pipeline 옆에서 DriftLens를 diagnostic/report layer로 사용하는 handoff contract를 정리한다.

DriftLens는 host pipeline을 대체하지 않는다. 저장된 previous/current JSON object `snapshot`을 비교해 schema drift evidence, rule-based `severity`, operator-facing artifact와 report를 남기는 local-first CLI다.

Steam 또는 `picking-my-time-sink`에서 발견한 response shape 차이는 첫 reference use case일 뿐이다. 같은 방식은 외부 API response를 저장하고 정규화하는 일반적인 data engineering pipeline에 적용할 수 있다.

## Host pipeline 책임

Host pipeline은 DriftLens 실행 전후의 운영 경계를 담당한다.

- API 호출과 인증
- `scheduler` 또는 pipeline failure hook 운영
- raw response 저장과 retention policy
- data missing, `parser` failure, `normalizer` failure, suspicious null increase, `partial_success` 같은 trigger 감지
- 비교할 previous/current JSON object `snapshot` 선택
- provider-specific semantics 판단
- `alert` delivery와 ticket, dashboard, incident workflow 연계

## DriftLens 책임

DriftLens는 준비된 입력을 비교하고 재현 가능한 artifact를 생성한다.

- JSON object `snapshot`에서 observed `schema` 추출
- previous/current `schema` 비교
- `diff` 생성
- deterministic rule 기반 `severity` 분류
- `summary.json`, `schemas/*`, `diffs/*` artifact 저장
- 선택적으로 LLM-assisted operator-facing Markdown report 생성

LLM output은 source of truth가 아니다. Source of truth는 deterministic `schema` extraction, `schema` diff, rule-based `severity` artifact다.

## Handoff 입력

DriftLens 입력은 비교 목적에 맞게 준비된 두 개의 JSON object `snapshot`이다.

```bash
uv run driftlens detect previous.json current.json --out-dir output-dir
```

Host pipeline은 원본 response 전체를 그대로 넘길지, response 내부의 특정 object를 추출해 넘길지 결정해야 한다. 예를 들어 wrapper key가 noise를 만들 수 있다면, host pipeline이 비교하려는 실제 domain object만 별도 `snapshot`으로 준비한다.

## 예상 출력

기본 실행은 아래 artifact를 생성한다.

- `summary.json`
- `samples/previous.json`
- `samples/current.json`
- `schemas/previous.json`
- `schemas/current.json`
- `diffs/schema_diff.json`
- `diffs/classified_diff.json`

`--report`를 사용하면 아래 파일이 추가된다.

- `llm/analysis.json`
- `reports/schema_drift.md`

Host pipeline은 이 artifact를 보관하거나 후속 `alert`, ticket, dashboard, incident workflow에 연결할 수 있다. DriftLens 자체가 `alert` sender나 scheduler를 구현하지는 않는다.

## Data governance 주의사항

Public docs, prompts, logs, fixtures, screenshots, reports에는 secret, raw third-party payload, private/local path, provider account detail을 넣지 않는다.

DriftLens artifact는 입력 `snapshot` copy와 diff 결과를 포함할 수 있으므로, host pipeline은 저장 위치, 접근 권한, retention policy를 별도로 관리해야 한다.

Steam 상태나 provider-specific business state는 DriftLens가 의미론적으로 분류하지 않는다. DriftLens는 schema drift evidence와 downstream impact 후보를 제공하고, domain-specific 판단은 host pipeline 또는 운영자가 담당한다.
