# DriftLens 문서 inventory

## 목적과 범위

이 문서는 DriftLens repository의 durable documentation surface를 reader와 translation 관점에서 분류하는 lightweight map이다. 번역 진행 상황이나 작업 이력을 기록하지 않는다.

분류 기준은 `docs/runbook/documentation-style.md`를 따른다. Repo-level agent rule과 PR rule의 primary source of truth는 각각 `AGENTS.md`와 `.github/PULL_REQUEST_TEMPLATE.md`다.

## Inventory

| Path | Primary reader | Translation decision | Inventory classification | Action | Notes |
| --- | --- | --- | --- | --- | --- |
| `AGENTS.md` | `agent_facing` | `keep_english` | `agent_facing_review_only` | 현재 상태를 유지하라. | Coding agent의 repo boundary와 validation rule을 정의한다. Tool compatibility가 필요하면 English를 유지하라. |
| `.github/PULL_REQUEST_TEMPLATE.md` | `mixed_reader` | `split_by_section` | `already_sufficiently_korean` | 자동 번역하지 마라. | Contributor와 coding agent가 함께 사용한다. Korean guidance와 exact section heading, command, identifier를 보존하라. |
| `README.md` | `public_facing` | `translate_korean_first` | `already_sufficiently_korean` | 이번 pass에서 변경하지 마라. | 이미 Korean-first다. 별도 scope가 승인되지 않으면 stale claim과 product boundary만 검토하라. |
| `docs/demo/sanitized-steam-appdetails.md` | `public_facing` | `defer_to_separate_scope` | `demo_or_fixture_docs_candidate` | 별도 demo/fixture scope로 넘겨라. | Sanitized demo prose만 검토 대상으로 삼고 fixture data와 exact command는 변경하지 마라. LLM report boundary를 보존하라. |
| `docs/integration/scheduled-ingestion-diagnostics.md` | `operator_facing` | `translate_korean_first` | `operator_facing_candidate` | 별도 PR에서 Korean-first 일관성을 검토하라. | Host pipeline과 DriftLens의 responsibility boundary, artifact literal, LLM report boundary를 보존하라. |
| `docs/runbook/agent-workflow.md` | `mixed_reader` | `preserve_literals_only` | `agent_facing_review_only` | 자동 번역하지 마라. | 이미 Korean-first다. Terminology drift와 scope boundary를 검토하고 exact workflow term과 command를 보존하라. |
| `docs/runbook/documentation-style.md` | `mixed_reader` | `preserve_literals_only` | `already_sufficiently_korean` | Classification rulebook으로 유지하라. | Maintainer와 coding agent가 사용하는 durable classification rulebook이다. |
| `docs/runbook/ticket-template.md` | `mixed_reader` | `split_by_section` | `agent_facing_review_only` | 현재 template structure를 유지하라. | Human과 coding agent가 함께 사용한다. Exact heading과 validation command를 보존하라. |
| `docs/runbook/documentation-inventory.md` | `developer_facing` | `translate_korean_first` | `already_sufficiently_korean` | Durable map으로만 갱신하라. | Progress log나 Koreanization checklist로 확장하지 마라. |
| `docs/assets/driftlens-flow.png` | `public_facing` | `preserve_literals_only` | `generated_or_excluded` | Asset 자체는 번역하지 마라. | 필요하면 reference, alt text, surrounding prose만 별도 docs pass에서 검토하라. |
| `LICENSE` | `public_facing` | `keep_english` | `generated_or_excluded` | 법적 원문을 변경하지 마라. | Documentation Koreanization scope에서 제외하라. |

## 후속 순서

1. `docs/integration/scheduled-ingestion-diagnostics.md`의 operator-facing prose와 English section heading을 별도 Koreanization PR 후보로 검토하라.
2. `README.md`는 Koreanization이 아니라 stale claim과 product boundary 검토 후보로 다뤄라. Rewrite가 필요하면 별도 scope를 먼저 승인받아라.
3. `docs/demo/sanitized-steam-appdetails.md`는 demo prose와 fixture boundary를 함께 검토할 수 있는 별도 scope로 다뤄라.
4. Agent-facing 또는 developer-facing 문서는 terminology drift나 scope mismatch가 확인될 때만 수정하라.

## 이번 pass에 포함하지 말 것

- 기존 documentation 번역 또는 rewrite
- `README.md`, demo/fixture docs, fixture data 변경
- runtime/code, tests, CLI/API user-visible message 변경
- source comment/docstring 변경
- CI workflow 변경
- `docs/local/**` 내용 또는 local execution history
- secret, raw third-party payload, private/local path, provider account detail, private runtime data, unsanitized fixture data
