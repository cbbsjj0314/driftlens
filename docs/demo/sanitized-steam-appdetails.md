# Sanitized Steam appdetails schema drift demo

이 문서는 DriftLens가 저장된 이전/현재 JSON object snapshot을 비교해 스키마 변경(schema drift) artifact와 mock Markdown report를 생성하는 작은 공개용 demo이다.

fixture는 Steam `appdetails` 응답에서 자주 문제가 되는 구조를 참고했지만, 값과 구조는 모두 안전하게 가공 및 익명화된(synthetic/sanitized) 예시이다.

raw Steam API response, API key, provider 계정 정보, private path, local runtime data는 포함하지 않는다.

## 왜 appid wrapper를 제외하는가

Steam `appdetails` 원본 응답은 보통 실제 게임 데이터 바깥에 `response[appid]` wrapper가 붙어 있다.

DriftLens는 입력 JSON에서 비교할 부분을 자동 선택하지 않는다. 이 demo의 목적은 서로 다른 `appid` wrapper 차이가 아니라 game data 내부의 schema drift를 보는 것이므로, `response[appid]["data"]`에 해당하는 inner object만 snapshot으로 저장했다.

## 실행

```bash
uv run driftlens detect examples/sanitized-steam-appdetails/previous.json examples/sanitized-steam-appdetails/current.json --out-dir .artifacts/sanitized-steam-appdetails --report --analysis-provider mock
```

재현 가능한 artifact만 확인하려면 `--report --analysis-provider mock` 없이 실행할 수도 있다.

## 생성되는 파일

기본 artifact:

- `summary.json`
- `samples/previous.json`
- `samples/current.json`
- `schemas/previous.json`
- `schemas/current.json`
- `diffs/schema_diff.json`
- `diffs/classified_diff.json`

`--report --analysis-provider mock` 사용 시 추가 artifact:

- `llm/analysis.json`
- `reports/schema_drift.md`

## 예상 summary 일부

아래는 핵심 shape만 보여주는 짧은 예시이다. 전체 artifact는 문서에 붙여 넣지 않는다.

```json
{
  "change_count": 6,
  "severity_counts": {
    "high": 4,
    "medium": 0,
    "low": 2
  }
}
```

## 대표적인 변화

아래 표는 `classified_diff.json` 전체가 아니라, 이해하기 쉬운 대표 변화만 발췌한 것이다.

| path | change_type | 의미 |
| --- | --- | --- |
| `price_overview` | `field_removed` | 가격 object가 현재 snapshot에서 사라짐 |
| `price_overview.currency` | `field_removed` | nested currency field가 현재 snapshot에서 사라짐 |
| `metacritic.score` | `field_removed` | metacritic 점수 field가 현재 snapshot에서 사라짐 |
| `required_age` | `type_changed` | 값의 type이 `string`에서 `integer`로 변경됨 |
| `ratings.agcom.rating` | `field_added` | 현재 snapshot에 `ratings.agcom.rating` field가 새로 추가됨 |

## 주의사항

- 이 demo는 저장된 JSON snapshot 사이의 schema drift를 확인하기 위한 예시이다.
- DriftLens가 담당하지 않는 일:
  - Steam API 수집
  - scheduling 또는 alerting
  - 자동 코드 수정
  - Steam free/unavailable/delisted/unlisted/region-blocked 상태 자동 판정
- DriftLens의 source of truth는 deterministic schema extraction, schema diff, rule-based severity classification이다.
- LLM 또는 mock report는 이미 계산된 diff를 operator-facing 설명으로 바꾸는 report layer이다.
