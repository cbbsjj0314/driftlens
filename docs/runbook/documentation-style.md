# DriftLens 문서 작성 및 번역 기준

## 1. 목적과 책임 경계

이 문서는 DriftLens 문서의 작성, 번역, inventory 분류에 필요한 최소 기준을 정한다. `AGENTS.md`와 `.github/PULL_REQUEST_TEMPLATE.md`가 primary source of truth이며, 이 문서는 반복 작업을 위한 세부 기준이다.

문서 작업은 기존 의미와 제품 경계를 보존해야 한다. Koreanization이나 분류 작업을 runtime/code 변경, 광범위한 cleanup, 새 product behavior 정의의 근거로 사용하지 않는다.

## 2. 적용 범위

- 적용 대상: public docs, operator guide, developer reference, agent instruction, demo/fixture 설명, CLI/API message 후보, comment/docstring inventory.
- 기본 범위: 문서별 primary reader와 translation decision을 정하고, exact literal을 보존하며, 공개 가능 여부를 검토한다.
- 별도 scope 필요: 기존 문서 번역, README rewrite, demo/fixture rewrite, `docs/local/**` cleanup, comment/docstring rewrite, test/fixture string 변경.
- 이 기준은 runtime, CLI, schema extraction, schema diff, severity classification, LLM provider behavior, artifact path, output schema를 변경하지 않는다.

## 3. Primary reader 분류

- `operator_facing`: DriftLens 결과를 확인하고 대응하는 operator가 읽는다. 사용법, artifact 해석, report guide가 예다. Korean-first를 기본으로 하되 command와 artifact literal을 보존하고, LLM report를 source of truth처럼 설명하지 않는다.
- `agent_facing`: coding agent가 작업 경계와 절차를 확인한다. `AGENTS.md`, agent workflow가 예다. tool compatibility에 유리하면 English를 유지하며, human-facing 문서라는 이유만으로 일괄 번역하지 않는다.
- `public_facing`: public repository 방문자와 사용자가 읽는다. README, 공개 demo 설명이 예다. Korean-first를 기본으로 하며, private data와 과장된 product scope를 포함하지 않는다.
- `developer_facing`: 구현과 contract를 확인하는 maintainer가 읽는다. module/CLI/provider reference가 예다. 정확성을 위해 English technical prose를 유지할 수 있으며, identifier와 behavior contract를 번역으로 흐리지 않는다.
- `mixed_reader`: operator, contributor, agent 등 여러 reader가 함께 읽는다. runbook과 workflow 문서가 예다. Korean-first prose와 exact English literal을 조합하고, reader별 책임이 섞이면 section을 분리한다.

## 4. Translation decision 분류

- `translate_korean_first`: durable human-facing prose에 사용한다. identifier와 exact literal은 번역하지 않는다. 예를 들어 사용 방법은 짧은 한국어로 설명하고 command는 그대로 둔다.
- `keep_english`: agent-facing instruction이나 정확한 technical reference에 사용한다. code-facing 표현을 번역하지 않는다. 예를 들어 English로 작성된 `AGENTS.md`는 자동 Koreanization 대상이 아니다.
- `preserve_literals_only`: 주변 설명만 번역하고 literal은 그대로 둬야 할 때 사용한다. command, JSON key, path, output snippet은 바꾸지 않는다. 예를 들어 command 앞뒤의 안내 문장만 번역한다.
- `split_by_section`: reader나 목적이 section마다 다를 때 사용한다. exact contract와 example을 번역하지 않는다. 예를 들어 human-facing 설명은 Korean-first section으로, exact contract는 별도 section으로 둔다.
- `defer_to_separate_scope`: 번역이 test, fixture, output contract, runtime behavior 또는 광범위한 rewrite와 결합될 때 사용한다. 결합된 literal을 문서 작업에서 바꾸지 않는다. 예를 들어 CLI message 변경은 inventory에만 남기고 별도 scope로 넘긴다.

## 5. Inventory classification

- `public_docs_candidate`: 공개 사용자 문서 후보. Korean-first 검토 대상으로 두고, scope 과장과 공개 불가 정보를 확인한다.
- `operator_facing_candidate`: operator workflow 또는 결과 해석 문서 후보. 읽기 쉬운 한국어를 우선하고, artifact와 source-of-truth 경계를 확인한다.
- `agent_facing_review_only`: agent instruction. 자동 번역하지 않고, tool compatibility와 기존 instruction 의미만 검토한다.
- `developer_reference_keep_english`: 구현·contract reference. English 유지가 정확하면 그대로 두고, terminology drift를 확인한다.
- `demo_or_fixture_docs_candidate`: sanitized demo/fixture 설명. 문서 prose만 후보로 두고, fixture data와 exact command를 함께 바꾸지 않는다.
- `llm_report_boundary_sensitive`: LLM report 관련 문서나 예시. 별도 주의 대상으로 두고, LLM이 detection이나 classification을 수행한다고 암시하지 않는지 검토한다.
- `api_or_cli_message_candidate`: API/CLI user-visible message. 문서 번역과 분리해 검토하고, message contract와 test coupling을 확인한다.
- `comment_or_docstring_review_only`: source comment/docstring. 현재 문서 scope에서 수정하지 않고, code context와 maintainer value를 수동 검토한다.
- `test_or_fixture_coupled`: test assertion 또는 fixture string과 결합된 내용. 문서-only 작업에서 건드리지 않고, contract 영향이 있는 별도 scope로 분리한다.
- `already_sufficiently_korean`: 이미 충분히 명확한 Korean-first 문서. 변경하지 않고, 불필요한 wording churn을 피한다.
- `generated_or_excluded`: generated output, vendored content, 명시적 제외 대상. 번역하지 않고 생성 source와 exclusion 이유를 확인한다.
- `manual_review_needed`: reader, 공개 범위, contract 영향이 불명확한 항목. 자동 분류나 일괄 변경 없이 maintainer 판단을 요청한다.

## 6. Literal / identifier 보존 규칙

문서 작성과 Koreanization 중 다음 항목은 번역, rename, paraphrase 또는 cosmetic change를 하지 않는다.

- code-facing identifier, `endpoint`, `route`, `loader`, `table`, `view`, `CLI`
- command name, module name, function name, config key, filename, fixture name
- schema field, diff item, provider name, API payload key, JSON path, artifact path
- exact command example

특히 `driftlens detect`, `previous.json`, `current.json`, `--out-dir`, `summary.json`, `schema`, `diff`, `severity`, `response[appid]["data"]`를 그대로 보존한다.

## 7. Markdown formatting 규칙

- 짧은 section과 bullet을 우선하고 heading을 명확하고 안정적으로 유지한다.
- example은 작게 유지한다.
- command, JSON fragment, exact output snippet에는 fenced code block을 사용한다.
- Korean-first prose는 명확한 이유가 없으면 해라체를 기본으로 사용한다.
- PR body는 `.github/PULL_REQUEST_TEMPLATE.md`를 따르며, 실용적인 범위에서 짧은 명사형 bullet 또는 해라체를 사용한다.
- 문체와 관계없이 exact identifier와 literal을 그대로 보존한다.
- 번역하면서 의미를 바꾸지 않는다.
- broad rewrite, formatting-only churn, unrelated cleanup을 만들지 않는다.
- translation 또는 inventory 작업에 인접한 cleanup을 섞지 않는다.

## 8. Privacy/security boundary

Public docs, prompt, log, screenshot, fixture, report, PR body에 다음 내용을 포함하지 않는다.

- secret, API key
- raw third-party payload
- private/local path
- provider account detail
- private runtime data
- unsanitized fixture data

`docs/local/**`는 local-only working material이며 public changelog가 아니다. Local checkpoint 내용을 review와 sanitization 없이 public docs로 옮기지 않는다.

## 9. Deterministic-vs-LLM boundary 보존

- Deterministic code가 observed `schema` extraction, schema `diff` 계산, drift `severity` classification을 담당한다.
- LLM output은 계산된 결과를 operator에게 설명하거나 report로 정리할 수 있다.
- LLM output은 source of truth가 아니다.
- 문서에서 LLM이 schema drift를 detect하거나, `severity`를 classify하거나, API semantics를 verify한다고 암시하지 않는다.
- LLM report example은 `llm_report_boundary_sensitive`로 보고 특히 주의해서 검토한다.

## 10. Docs-code consistency 확인

변경된 문서에서 다음 내용을 주장하기 전에 현재 repo behavior와 일치하는지 확인한다.

- CLI command name
- artifact name과 path
- provider behavior
- fixture name
- `schema`, `diff`, `severity` behavior
- Steam `appdetails` comparison boundary

Steam `appdetails`에서 game data의 schema drift가 목적이면 top-level appid wrapper 차이가 아니라 준비된 `response[appid]["data"]` inner object snapshot을 비교한다고 설명한다.

## 11. Validation

Docs-only 변경은 다음을 수행한다.

- `git diff --check`
- 변경 문서 reread: stale claim, duplicated guidance, overbroad scope promise 확인
- 변경 문서 reread: private data와 raw third-party payload 노출 확인
- 변경 문서 reread: deterministic-vs-LLM boundary mismatch 확인
- 변경 문서 reread: docs-code consistency mismatch 확인

Runtime validation은 docs-only PR에 필요하지 않다. 실행하지 않은 runtime validation을 실행했다고 쓰지 않는다.

PR body의 `Validation`은 `.github/PULL_REQUEST_TEMPLATE.md`를 따르고 짧게 유지한다. Runtime test를 실행하지 않았다면 `- Not run (docs-only change)`를 사용하고, 수행한 changed docs reread 결과도 함께 적는다.

## 12. PR body / commit title 기준

- PR body와 PR title guidance의 source of truth는 `.github/PULL_REQUEST_TEMPLATE.md`다.
- Commit subject convention의 source of truth는 `AGENTS.md`다.
- PR template 전체를 다른 문서에 복제하지 않는다.
- PR body는 concise Korean으로 작성하고 identifier와 exact literal을 보존한다.
- 실제 변경, validation, deferred scope만 적고 실행하지 않은 결과를 주장하지 않는다.

## 13. Agent checklist

- [ ] Primary reader와 translation decision을 정했다.
- [ ] 필요한 inventory classification을 기록했다.
- [ ] identifier, literal, command, path를 그대로 보존했다.
- [ ] privacy/security와 `docs/local/**` 경계를 확인했다.
- [ ] deterministic-vs-LLM 및 Steam `appdetails` 경계를 보존했다.
- [ ] 현재 behavior와 문서 claim을 대조했다.
- [ ] unrelated cleanup과 기존 string 변경을 제외했다.
- [ ] docs-only validation 결과를 정확히 보고했다.

## 14. Completion criteria

- 요청된 문서와 section만 변경되었다.
- 필요한 reader, translation, inventory category가 빠짐없이 분류되었다.
- exact literal, product scope, privacy/security, deterministic-vs-LLM boundary가 보존되었다.
- 기존 README/docs/demo/fixture/comments/docstrings/tests string과 runtime behavior는 변경되지 않았다.
- `git diff --check`와 changed docs reread가 완료되었다.
- PR body가 실제 validation과 deferred scope를 정확히 반영한다.
