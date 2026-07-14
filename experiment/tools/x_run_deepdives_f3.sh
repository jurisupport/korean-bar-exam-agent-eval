#!/bin/bash
# F3 경합문항 딥다이브 병렬 런처.
# 각 문항은 F3_voted.json과 픽스처의 격리 복제본에서 독립 실행하고,
# 결과 항목만 문항별 patch.json으로 추출한다. 공유 voted 병합은 별도 단계에서 한다.
set -euo pipefail

CR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
[ "$#" -ge 1 ] || { echo "사용: bash tools/x_run_deepdives_f3.sh Q [Q ...]" >&2; exit 2; }
[ "$#" -le 5 ] || { echo "한 wave는 최대 5문항" >&2; exit 2; }

run_q() {
  q="$1"
  case "$q" in ''|*[!0-9]*) echo "문항 번호 오류: $q" >&2; return 2 ;; esac
  [ "$q" -ge 1 ] && [ "$q" -le 40 ] || { echo "문항 범위 오류: $q" >&2; return 2; }
  qq="$(printf '%02d' "$q")"
  stem="F3_deepdive_q${qq}"
  patch="$CR/01_sealed/_parts/${stem}.patch.json"
  if [ -f "$patch" ]; then
    echo "↷ 이미 완료되어 건너뜀: 문$q"
    return 0
  fi

  # 실패·중단 후 재시도라면 기존 로그를 별도 이름으로 보존한다.
  retry_stamp="$(date '+%Y%m%dT%H%M%S')_$$"
  for old in "$CR/02_logs/${stem}.codex.jsonl" "$CR/02_logs/${stem}.stderr.log"; do
    [ ! -e "$old" ] || mv "$old" "${old}.failed.${retry_stamp}"
  done

  work="$(mktemp -d "${TMPDIR:-/tmp}/x_gpt56sol_${stem}.XXXXXX")"
  prompt="$(mktemp "${TMPDIR:-/tmp}/x_gpt56sol_${stem}_prompt.XXXXXX")"

  mkdir -p "$work/00_fixtures" "$work/01_sealed/_parts" "$work/tools"
  cp "$CR/RUNBOOK_X.md" "$work/RUNBOOK_X.md"
  cp "$CR/00_fixtures/공법_문항.md" "$work/00_fixtures/공법_문항.md"
  cp "$CR/01_sealed/_parts/F3_voted.json" "$work/01_sealed/_parts/F3_voted.json"
  cp "$CR/tools/f_deepdive_prompt.md" "$work/tools/f_deepdive_prompt.md"

  sed -e 's/{RUN}/3/g' "$CR/tools/f_deepdive_prompt.md" > "$prompt"
  sed -e 's/F1/F3/g' -e "s/{Q}/$q/g" "$CR/tools/f_deepdive_invocation.md" >> "$prompt"

  if codex exec -m gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' \
      --ephemeral --json --skip-git-repo-check -s workspace-write -C "$work" - \
      < "$prompt" > "$CR/02_logs/${stem}.codex.jsonl" \
      2> "$CR/02_logs/${stem}.stderr.log"; then
    status=0
  else
    status=$?
  fi
  rm -f "$prompt"
  [ "$status" -eq 0 ] || return "$status"

  python3 "$CR/tools/x_extract_deepdive_f3.py" \
    "$CR/01_sealed/_parts/F3_voted.json" \
    "$work/01_sealed/_parts/F3_voted.json" \
    "$q" "$patch"
}

pids=()
for q in "$@"; do
  run_q "$q" &
  pids+=("$!")
done

failed=0
for pid in "${pids[@]}"; do
  wait "$pid" || failed=1
done
[ "$failed" -eq 0 ] || { echo "✘ F3 딥다이브 wave 실패 — 해당 문항 stderr 확인" >&2; exit 1; }
echo "✔ F3 딥다이브 wave 완료: $*"
