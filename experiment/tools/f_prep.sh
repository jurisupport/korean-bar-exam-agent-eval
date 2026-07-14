#!/bin/bash
# f_prep.sh — 클린룸 X 준비상태 검증: 사전등록·픽스처 무결성 + 정답표 부재 확인.
# PREREG_X.txt는 오케스트레이터가 풀이 전에 Git으로 봉인하므로 이 스크립트는 생성·수정하지 않는다.
set -eu
CR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PRE="$CR/PREREG_X.txt"
mkdir -p "$CR/01_sealed/_parts" "$CR/_runs" "$CR/02_logs" "$CR/03_answer_key" "$CR/04_scoring"

echo "== [1] 사전등록 봉인 존재·읽기전용 확인 =="
[ -f "$PRE" ] || { echo "✘ PREREG_X.txt 없음 — 풀이 금지"; exit 1; }
[ ! -w "$PRE" ] || { echo "✘ PREREG_X.txt가 쓰기 가능 — 풀이 금지"; exit 1; }

echo "== [2] 픽스처 무결성 (기대 430a7396…) =="
FIXTURE_SHA="$(shasum -a 256 "$CR/00_fixtures/공법_문항.md" | awk '{print $1}')"
[ "$FIXTURE_SHA" = "430a7396c3d359f886741aa339ce665cef5a4b34b652cbbc2f6b5f37c4b1bdd1" ] || { echo "✘ 픽스처 해시 불일치"; exit 1; }
grep -q "$FIXTURE_SHA" "$PRE" || { echo "✘ PREREG_X에 픽스처 해시 없음"; exit 1; }
echo "$FIXTURE_SHA  00_fixtures/공법_문항.md"

echo "== [3] 정답표 격리 확인 =="
if find "$CR/03_answer_key" -mindepth 1 -print -quit | grep -q .; then
  echo "✘ 03_answer_key가 비어 있지 않음 — 접근하지 말고 중단"
  exit 1
fi
echo "✔ 03_answer_key 비어 있음"

echo "== [4] 산출 디렉터리 확인 =="
echo "준비 완료. f_serve.sh로 서버 확인 후 Phase F0(Foff 3회)부터 진행."
