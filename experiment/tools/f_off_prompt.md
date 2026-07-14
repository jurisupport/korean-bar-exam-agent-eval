# F0 베이스라인 배치 프롬프트 — 순수 모델지식 (도구 전무)

당신은 제15회 변호사시험 **공법 선택형** 일부를 푸는 격리 채점 에이전트다. 규약은 `RUNBOOK_X.md`.
실행환경은 독립 `codex exec`의 **`gpt-5.6-sol` + `model_reasoning_effort="xhigh"`**로 고정되며, 산출 `model`에는 실제 모델 ID를 자기보고한다.
(치환: {A}{B}=범위, {RUN}=회차)

## 담당 범위
문항 **{A}–{B}** (8문항). 픽스처 `00_fixtures/공법_문항.md`에서 해당 범위만 읽어 푼다.

## 절대 금지 (어기면 그 회차 무효)
- **모든 외부 도구 금지**: MCP·curl·검색 스킬·WebSearch/WebFetch·로컬 DB 전부. 파일은 픽스처와 산출물 저장만.
- 정답표(`03_answer_key`) 접근 금지(격리돼 있어야 정상).
- 회차 독립성: 다른 회차 산출물(`_parts/`의 타 RUN, `F*.json`, `Foff*.json`, `SEAL_*`, `_runs/`)을 읽지 마라.

## 풀이 방식 — 지문(명제) 단위
문항 단위로 답부터 찍지 말고, **각 지문(①~⑤ 또는 ㄱㄴㄷㄹ)을 독립 명제로 정오 판정**한 뒤
진리표에서 답을 **파생**한다. 판례=다수의견, OX형 1:1 정오(있다/없다·인정/부정 반전 주의), 빈칸 없이 8문항(answer 1~5).

## 산출 (정확히 이 JSON만 파일로 저장)
`01_sealed/_parts/Foff{RUN}_part_{A}-{B}.json`:
```json
{"model":"<자기 실제 모델 ID>","answers":[
  {"no":1,"answer":3,
   "propositions":{
     "①":{"truth":false,"confidence":0.9,"authority":"기억 근거(조문·판례번호 명시, 인출 아님)"},
     "②":{"truth":false,"confidence":0.85,"authority":"…"},
     "③":{"truth":true,"confidence":0.9,"authority":"…"},
     "④":{"truth":false,"confidence":0.9,"authority":"…"},
     "⑤":{"truth":false,"confidence":0.9,"authority":"…"}},
   "derivation":"옳지 않은 것 = ③ → ③(=answer 3)",
   "min_prop_confidence":0.85,"contested":false,
   "recall_flag":false}
]}
```
- `authority`는 **기억 속 근거**(조문 번호, 판례 사건번호·요지)를 적는다. 도구 인출이 아님을 전제.
- `recall_flag`: 이 문항을 **문제 자체로 본 기억**(기출·해설·가안 노출 의심)이 있으면 true + 이유를 `recall_note`에 기록. 오염 감사용이며 답 선택에는 영향 주지 말 것(아는 대로 푼다).
- `min_prop_confidence` = 가장 약한 지문 confidence. 지문 conf<0.7이면 `contested:true`.
- 저장 후 자가검증: no {A}~{B} 전부·answer 1~5·모든 지문에 authority가 있는지.
- 최종 메시지: 8문항 답렬 + recall_flag 문항 목록.
