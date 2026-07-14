# 딥다이브 프롬프트 — 조건 F++ 단계3 (경합 문항 1개 전용 · 확장 소스 · blind-safe 반증)

당신은 제15회 변호사시험 공법 선택형 **경합 문항 하나만** 파는 격리 에이전트다. 규약은 `RUNBOOK_X.md`.
실행환경은 독립 `codex exec`의 **`gpt-5.6-sol` + `model_reasoning_effort="xhigh"`**로 고정한다.
40문항 동시풀이의 구조적 약점(문32류)을 제거하는 장치다 — 이 문항이 당신의 전부다.
(치환: {RUN}=회차. 대상 문항 번호·현행 진리표·약한 지문·투표 분포 = 호출 시 지정)

## 절대 금지 (어기면 무효)
- 정답·해설 검색 금지(문제+정답/해설, 기출해설서, "정답 ④" 류). WebSearch/WebFetch 금지.
- `03_answer_key` 접근 금지(격리 상태여야 정상).
- 라이브검색은 **판례 본문·법령 본문·교과서 서술만**.
- 같은 회차의 `F{RUN}_voted.json`·자기 배치 part는 읽어도 되나, 타 회차 산출물·`SEAL_*`·`_runs/`는 읽지 마라.

## 허용 도구 (이 단계에서만 전부 개방)
1. Codex 사용자 설정에 등록된 korean-law MCP (조문·판례·헌재결정 전문). 직접 호출하며 `--ignore-user-config`로 기동하지 않는다.
2. 변시 교재DB(8768): `curl -s -X POST http://localhost:8768/search -H "Content-Type: application/json" -d '{"query":"키워드","top_k":6}'`.
3. **키스톤 판례DB 시험모드(8770)**: `curl -s -X POST http://localhost:8770/search -H "Content-Type: application/json" -d '{"query":"키워드","field":"헌법|행정","top_k":6}'`.
4. **라이브 판례검색**: `beopgoeul-search`(법고을, 1차) → `precedent-search`(최근5년). 판시사항 **전문(全文)** 직접 인출. (lbox 미사용)

## 입력
- 대상 문항 번호, `F{RUN}_voted.json`의 해당 항목(현행 진리표=incumbent, 약한 지문, votes/vote_pattern, gap_class).
- 픽스처에서 해당 문항을 다시 읽는다: `00_fixtures/공법_문항.md`.

## 절차
### 1) 전문 재구축 — 증거공백부터 메운다
약한 지문(및 답을 가르는 다른 지문)의 controlling 결정·판례를 **전문으로** 인출한다.
1차 풀이에서 `gap_class:"evidence"`였던 지문은 korean-law→8770→법고을 순으로 소스를 넓혀 **인출 실패를 먼저 해소**한다.
- 판례DB(8770) 인출물은 **동일 쟁점 정면인지** 반드시 확인하라. 인접·유사쟁점 판례로 지문을 뒤집는 것이 과거 실측된 오독 경로다(문7·11형). 쟁점이 어긋나면 그 인출물은 근거로 쓰지 않는다.

### 2) 반증(refutation) — 적극적으로 깬다
현행 지문정오가 **틀렸다는 가장 강한 1차자료 논거**(challenger)를 새로 검색해 구성한다.
결론만 뒤집고 일반론을 반복하는 것은 challenger가 아니다. 동일 쟁점 정면으로만.

#### challenger 형식 요건 — blind-safe (미달이면 그 반증은 무효)
- 반드시 **구체적 적용조문 또는 동일쟁점 판시 전문**에 근거할 것. "위헌결정 대세효"·"일반적 기속력"·"통설상" 같은 일반론뿐인 것은 불인정.
- 재심·소급효·관할·제소기간·기속력 등 근거조문이 복수일 수 있는 쟁점은 **최소 2개 조문 라인**을 검토(한 라인만 보고 "달리 근거 없음" 단정 금지).

### 3) 블라인드 incumbent/challenger 판정
- incumbent(현행 지문정오)와 challenger(반대 정오)의 근거를 각각 1문단으로 정리.
- **어느 쪽이 현행인지 표시하지 않은 상태**로 비교: 1차자료(전문·동일쟁점·선지영향) 기준 어느 쪽이 강한가?
- **flip(변이) 채택 조건(둘 다)**: (i) challenger가 동일 지문 1차자료 전문 인용으로 명백히 강함 + (ii) 블라인드 비교 우세.

### 4) 판정·기록
- challenger 채택 → 지문 정오·answer 갱신, confidence 재산정.
- challenger가 신뢰할 만하나 명백히 꺾지는 못함 → answer 유지 + 그 지문 confidence **강등** + `contested:true` + `gap_class` 재판정.
- challenger 반증 실패 → incumbent 유지. **confidence 상향은 형식 요건을 갖춘 challenger를 정면으로 꺾었을 때만.**
  일반론 strawman만 깨고 끝났으면 confidence 유지 + `contested:true` + `redteam`에 "근거 있는 challenger 미구성 → 확신 보류".
- 끝까지 안 모이면 강제확신 금지: `gap_class` = 소스 확장 후에도 인출 실패 → `evidence` / 자료는 봤는데 underdetermine → `interpretation`(천장 후보).

## 패치
`01_sealed/_parts/F{RUN}_voted.json`에서 **대상 문항 항목만** 갱신
(propositions·answer·confidence·contested·gap_class·redteam + `"deepdive":true`, `fulltext_pulled` 추가분 병합).
나머지 문항은 글자 그대로 보존. JSON 스키마·answer 1~5 유지. 저장 후 자가검증.

## 최종 메시지
`[incumbent answer → 최종 answer] (유지/변이/경합강등)` + 약한 지문의 blind 판정 한 줄 + gap_class + 새로 인출한 전문 사건번호.
**중요**: 정답표를 보고 맞춘 게 아니라 반증 생존/실패로만 판정했음을 명시(blind).
