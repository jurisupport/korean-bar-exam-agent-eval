#!/bin/bash
# f_serve.sh — 검색 서버 기동·점검 (클린룸 X). 사용: bash tools/f_serve.sh
# DB는 클린룸 외부 공용 인프라(localhost 공유). 클린룸 무결성은 데이터/봉인 격리로 보장.
# 주의: 8770(판례DB)·법고을은 딥다이브 단계 전용이다 — 1차 솔버 프롬프트에서 금지됨.
: "${KDB:?Set KDB to the local precedent database directory}"

echo "== 변시 교재DB(8768) — 1차 솔버용 =="
H8768="$(curl -s -m 3 http://localhost:8768/health 2>/dev/null || true)"
echo "$H8768"
echo "$H8768" | grep -q '"embeddings_loaded": 17167' && echo "  ✔ embeddings_loaded=17167" || { echo "  ✘ 8768 요구값 미확인 — 중단"; exit 1; }

echo "== 시험모드 판례DB(8770, 선고일<=2026-01-05) — 딥다이브 전용 =="
if ! curl -s -m 3 http://localhost:8770/health >/dev/null 2>&1; then
  ( cd "$KDB" && EXAM_MAX_DATE=2026-01-05 PRECEDENT_PORT=8770 nohup python3 serve.py >/tmp/prec-8770.log 2>&1 & )
  for i in $(seq 1 25); do sleep 3; curl -s -m 3 http://localhost:8770/health >/dev/null 2>&1 && break; done
fi
H8770="$(curl -s http://localhost:8770/health)"
echo "$H8770"
echo "$H8770" | grep -q '"max_date": "2026-01-05"' && echo "  ✔ 시점차단 확인" || { echo "  ✘ max_date 미확인 — 중단"; exit 1; }

echo "== korean-law MCP는 Codex 사용자 설정의 등록 도구를 직접 사용(--ignore-user-config 금지) =="
echo "== 라이브 판례검색(딥다이브 전용): beopgoeul-search(법고을, 1차) / precedent-search 가용 확인 (lbox 미사용) =="
echo "== Phase F0(Foff)는 위 서버 전부 미사용 — 순수 모델지식 =="
