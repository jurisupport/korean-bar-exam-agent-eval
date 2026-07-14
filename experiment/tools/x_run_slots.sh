#!/bin/bash
# GPT-5.6 Sol(xhigh) 슬롯 런처. 각 슬롯은 독립 비대화 codex exec 프로세스다.
# 사용: bash tools/x_run_slots.sh off RUN  또는  bash tools/x_run_slots.sh on RUN
set -euo pipefail

CR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PHASE="${1:-}"
RUN="${2:-}"

if [ "$PHASE" != "off" ] && [ "$PHASE" != "on" ]; then
  echo "사용: bash tools/x_run_slots.sh off|on RUN" >&2
  exit 2
fi
case "$RUN" in 1|2|3) ;; *) echo "RUN은 1, 2, 3 중 하나" >&2; exit 2 ;; esac

mkdir -p "$CR/01_sealed/_parts" "$CR/02_logs"

run_slot() {
  phase="$1"; run="$2"; variant="$3"; a="$4"; b="$5"; field="$6"; framing="$7"
  prompt="$(mktemp "${TMPDIR:-/tmp}/x_gpt56sol_prompt.XXXXXX")"
  if [ "$phase" = "off" ]; then
    sed -e "s/{RUN}/$run/g" -e "s/{A}/$a/g" -e "s/{B}/$b/g" \
      "$CR/tools/f_off_prompt.md" > "$prompt"
    stem="Foff${run}_part_${a}-${b}"
  else
    sed -e "s/{RUN}/$run/g" -e "s/{A}/$a/g" -e "s/{B}/$b/g" \
      -e "s/{FIELD}/$field/g" -e "s/{V}/$variant/g" -e "s/{VARIANT}/$framing/g" \
      "$CR/tools/f_batch_prompt.md" > "$prompt"
    stem="F${run}_${variant}_part_${a}-${b}"
  fi

  if codex exec -m gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' \
      --ephemeral --json -s workspace-write -C "$CR" - \
      < "$prompt" > "$CR/02_logs/${stem}.codex.jsonl" \
      2> "$CR/02_logs/${stem}.stderr.log"; then
    status=0
  else
    status=$?
  fi
  rm -f "$prompt"
  return "$status"
}

wait_wave() {
  failed=0
  for pid in "$@"; do
    wait "$pid" || failed=1
  done
  [ "$failed" -eq 0 ] || { echo "✘ 슬롯 실패 — 02_logs의 해당 로그 확인" >&2; exit 1; }
}

ranges=("1 8 헌법" "9 16 헌법" "17 24 행정" "25 32 행정" "33 40 행정")
if [ "$PHASE" = "off" ]; then
  pids=()
  for item in "${ranges[@]}"; do
    set -- $item
    run_slot off "$RUN" OFF "$1" "$2" "$3" OFF &
    pids+=("$!")
  done
  wait_wave "${pids[@]}"
else
  variants=(V1 V2 V3)
  framings=(
    "조문순행: 조문 문언·통설 진입 → 포섭 → 판례 확인"
    "판례역행: controlling 판시 인출 → 지문 정오 역산 → 반대가정 셀프체크"
    "중립 재도출: 지문별 독립 정오 → 선지 교차 → 반대가정"
  )
  for wave in 0 1 2; do
    pids=()
    variant="${variants[$wave]}"
    framing="${framings[$wave]}"
    for item in "${ranges[@]}"; do
      set -- $item
      run_slot on "$RUN" "$variant" "$1" "$2" "$3" "$framing" &
      pids+=("$!")
    done
    wait_wave "${pids[@]}"
  done
fi

echo "✔ $PHASE run=$RUN 독립 슬롯 실행 완료. 모델 자기보고 검증은 다음 단계에서 강제된다."
