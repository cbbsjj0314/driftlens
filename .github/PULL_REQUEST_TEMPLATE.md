<!--
빠르게 훑어볼 수 있게 짧게 쓴다.
긴 문단보다 짧은 bullet을 선호한다.
구체적이고 명확하게 쓴다.
쓸데없이 길게 쓰지 않는다.
추상적인 표현은 피한다.
효과를 과장하는 표현보다 구현 사실을 먼저 적는다.
PR 범위는 분명히 적는다.
인접하지만 이번 PR에 넣지 않은 내용만 별도로 적는다.
의도적으로 제외한 범위를 적을 필요가 없으면 해당 section은 지운다.
PR 본문은 한국어로 작성한다.
설명 문장은 간결한 한국어로 쓴다.
객체명 / endpoint / route / loader / table / view / CLI command / fixture / schema / diff / provider / filename은 번역하지 않고 실제 코드 표기를 유지한다.
docs-only PR이면 Validation section은 남기고 `- Not run (docs-only change)`라고 적는다.
Ticket / Spec은 optional이다.
작은 docs/test/runtime fix는 PR 본문 자체를 lightweight spec으로 써도 된다.

PR title guidance:
PR 전체를 한 줄로 요약하는 짧고 읽기 쉬운 제목으로 쓴다.
개별 commit 메시지보다 한 단계 위에서 작업 결과나 범위를 설명한다.

Good examples:
- Add flat JSON schema extraction
- Add nested object schema paths
- Introduce schema diff engine
- Document local agent workflow
- Add rule-based drift severity classification

Avoid:
- feat(schema): update extractor
- fix: update tests and docs
- misc cleanup
-->

## Summary

<!--
가능하면 입력과 출력이 함께 보이게 쓴다.
첫 bullet에서 이 PR이 왜 필요한지 한 줄로 설명하면 좋다.
내부 개발 용어만으로 설명하지 않는다.
-->

- 변경 사항
- 변경 이유
- 필요하면 범위 경계

---

## Changes

<!--
어떤 fixture, schema field, diff item, CLI command, provider, file path가 바뀌는지 보이게 쓴다.
실제 객체명과 코드 표기를 우선 쓴다.
-->

- 변경 1
- 변경 2
- 변경 3

---

<!--
관련 ticket, issue, spec, local prompt가 있을 때만 남긴다.
없으면 이 section은 통째로 지운다.
모든 PR에 ticket이나 formal spec이 필요한 것은 아니다.
작은 변경은 Summary와 Changes가 lightweight spec 역할을 할 수 있다.
-->

## Ticket / Spec

- 관련 ticket, issue, spec, prompt

---

<!--
리뷰어가 같이 기대할 만한 인접 작업을 이번 PR에서 의도적으로 제외했을 때만 남긴다.
범위가 이미 자명하면 이 section은 통째로 지운다.
특히 deterministic schema logic과 LLM analysis의 경계가 헷갈릴 수 있으면 남기는 편이 좋다.
-->

## Out of scope / Deferred

- 의도적으로 제외한 인접 작업
- 별도 PR로 남긴 후속 작업

---

## Risk / Human Gate

<!--
human review가 필요한 contract, runtime boundary, secret/public exposure risk가 있으면 적는다.
없으면 낮은 risk와 이유를 짧게 적는다.
schema extraction, schema diff, severity classification, artifact path, summary.json, LLM provider behavior가 바뀌면 명확히 적는다.
-->

- Risk: 낮음 / 중간 / 높음
- Human Gate: 필요 / 불필요
- 이유

---

## Validation

<!--
기본은 `command: result` 한 줄 형식으로 쓴다.
명령 목록과 결과를 따로 반복하지 않는다.
모든 PR이 모든 command를 실행해야 하는 것은 아니다.
default runtime/code 변경은 `./scripts/check.sh`를 우선 적는다.
optional `llm` provider 변경은 `uv sync --locked --extra llm`와 `./scripts/check-llm.sh`를 적는다.
package/build 변경은 `./scripts/check-package.sh`를 적는다.
docs-only 또는 template-only PR이면 runtime test를 생략할 수 있다.
그 경우 `- Not run (docs-only change)` 또는 `- Not run (docs/template-only change)`라고 적는다.
대신 `git diff --check`와 changed docs reread 결과를 적는다.
CLI behavior를 바꿨고 `./scripts/check.sh`의 default smoke로 덮이지 않을 때만 focused CLI smoke를 추가한다.
Required Checks / CI는 PR에서 확인 가능한 결과가 있을 때 job 이름과 함께 적는다.
-->

- `./scripts/check.sh`: result
- `uv sync --locked --extra llm`: result, when applicable
- `./scripts/check-llm.sh`: result, when applicable
- `./scripts/check-package.sh`: result, when applicable
- `git diff --check`: result, for docs-only or template-only changes
- changed docs reread: result, when applicable
- Required Checks / CI: passed (`Default checks`, `LLM extra checks`, `Package build`)

---

<!--
Summary, Changes, Out of scope / Deferred, Validation에 이미 적은 내용을 반복하지 않는다.
리뷰어가 알아야 할 추가 맥락, caveat, assumption이 있을 때만 남긴다.
추가로 적을 내용이 없으면 이 section은 통째로 지운다.
-->

## Notes

- 리뷰어가 알아야 할 맥락
- caveat, rollout note, assumption
