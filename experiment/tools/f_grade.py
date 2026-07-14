#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""f_grade.py — 클린룸 X 채점: 정답표 복귀 + Foff(베이스라인)·F(챔피언) 일괄 채점 +
오염 판정(사전등록 기준) + 재현성(진동) + 잔차 분류 + 안정성 평결.
봉인 후 1회 실행. 사용: python3 tools/f_grade.py
"""
import json, glob, os, statistics
from collections import Counter

CR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLD = "/tmp/keyhold_cleanroom_X_gpt56sol"
CONTAM_THRESH = 38.0   # 사전등록: Foff 평균 >= 38/40 → 회상 오염 의심
OPUS_BASELINE = 34.6   # 참고: Opus 4.8 OFF 5회 평균

if os.path.isdir(HOLD) and os.listdir(HOLD):
    for f in os.listdir(HOLD):
        os.replace(os.path.join(HOLD, f), os.path.join(CR, "03_answer_key", f))
    try: os.rmdir(HOLD)
    except OSError: pass
    print("정답표 복귀 완료")

key = {int(k): v for k, v in json.load(open(CR + "/03_answer_key/공법_정답.json", encoding="utf-8"))["key"].items()}

def load(path):
    A, meta = {}, {}
    for x in json.load(open(path, encoding="utf-8"))["answers"]:
        A[x["no"]] = x["answer"]; meta[x["no"]] = x
    return A, meta

def grade_cond(title, paths):
    runs = []
    print("=" * 64); print(f"## {title}")
    for s in paths:
        tag = os.path.basename(s)[:-5]; A, meta = load(s)
        wrong = [(n, A[n], key[n]) for n in range(1, 41) if A[n] != key[n]]
        runs.append((tag, 40 - len(wrong), wrong, A, meta))
        ws = ", ".join(f"문{n}({a}→{k})" for n, a, k in wrong) or "만점"
        print(f"  {tag}: {40-len(wrong)}/40  {(40-len(wrong))*2.5:.1f}점  {(40-len(wrong))/40*100:.1f}%  | 오답 {ws}")
        print(f"       답렬 {''.join(str(A[n]) for n in range(1,41))}")
    if not runs: return runs
    scores = [c for _, c, _, _, _ in runs]
    allwrong = Counter(); [allwrong.update(n for n, _, _ in w) for _, _, w, _, _ in runs]
    N = len(runs)
    always = sorted(n for n in allwrong if allwrong[n] == N)
    osc = sorted(n for n in allwrong if 0 < allwrong[n] < N)
    print(f"  분포 {scores} 평균 {statistics.mean(scores):.1f}/40 ({statistics.mean(scores)/40*100:.1f}%)"
          + (f" | 상시오답 {always}" if always else "") + (f" | 진동 {osc}" if osc else ""))
    return runs

off_runs = grade_cond("Phase F0 — GPT-5.6 Sol xhigh OFF 베이스라인 (도구 전무)",
                      sorted(glob.glob(CR + "/01_sealed/Foff[0-9].json")))
f_runs = grade_cond("Phase F1 — 조건 F++ (gpt-5.6-sol xhigh 3표 다수결 + 전문가드 + 경합한정 딥다이브)",
                    sorted(glob.glob(CR + "/01_sealed/F[0-9].json")))

# ── 오염 판정 (사전등록 기준, PREREG_X.txt에 고정)
if off_runs:
    m = statistics.mean(c for _, c, _, _, _ in off_runs)
    recalls = sorted({n for _, _, _, _, meta in off_runs for n in meta if meta[n].get("recall_flag")})
    print("=" * 64); print("## 오염 판정 (사전등록: Foff 평균 >= 38/40 → 의심)")
    print(f"  Foff 평균 {m:.1f}/40 vs 기준 {CONTAM_THRESH}/40 (참고: Opus4.8 OFF {OPUS_BASELINE}/40)")
    if m >= CONTAM_THRESH:
        print("  ⚠ 회상 오염 의심 — F1 보고에서 OFF<ON 격차 논증을 주장하지 말 것.")
        print("    프레임 전환: authorities→정답 역추적 감사(근거기반 도출 가시화) 중심으로 보고.")
    else:
        print("  ✔ 기준 미만 — OFF<ON 격차 논증 사용 가능(단, 학습데이터 회상 가능성 잔존은 상시 고지).")
    if recalls:
        print(f"  recall_flag 문항(솔버 자가보고): {recalls} — 오염 감사 참고자료")

# ── F1 안정성 평결 + 잔차 분류
if f_runs:
    N = len(f_runs)
    scores = [c for _, c, _, _, _ in f_runs]
    allwrong = Counter(); [allwrong.update(n for n, _, _ in w) for _, _, w, _, _ in f_runs]
    always = sorted(n for n in allwrong if allwrong[n] == N)
    osc = sorted(n for n in allwrong if 0 < allwrong[n] < N)
    maj_wrong = []
    for n in range(1, 41):
        c = Counter(A[n] for _, _, _, A, _ in f_runs)
        if c.most_common(1)[0][0] != key[n]: maj_wrong.append(n)

    def classify(n):
        flags = []
        for tag, _, _, _, meta in f_runs:
            m = meta.get(n, {})
            g = m.get("gap_class", "none")
            if m.get("contested"): flags.append(f"{tag}:경합")
            if m.get("deepdive"): flags.append(f"{tag}:딥다이브")
            if g and g != "none": flags.append(f"{tag}:{g}")
        gv = Counter(f.split(":")[1] for f in flags if f.split(":")[1] in ("evidence", "interpretation"))
        if gv:
            lab = gv.most_common(1)[0][0]
            return ("증거공백(소스 추가 필요)" if lab == "evidence" else "해석공백(천장 가능)"), flags
        return "보정실패(경합표시 없이 확신오답 → 경합식별·딥다이브 강화 대상)", flags

    if maj_wrong:
        print("\n## 잔차 분류(F 다수결 오답)")
        for n in maj_wrong:
            lab, flags = classify(n)
            print(f"  문{n}: {lab}")
            if flags: print(f"      회차표시: {', '.join(flags)}")

    print("\n## 안정성 평결 (F++)")
    if N >= 3 and all(c == 40 for c in scores):
        print("  ✅ 성공: 독립 3회+ 봉인본 모두 40/40 (재현 가능한 만점). → 민사·형사 확장 착수 가능.")
    elif all(c == 40 for c in scores):
        print(f"  ⏳ 진행 중: 현재 {N}회 모두 40/40. 성공 판정에는 독립 3회 필요 — 남은 회차 계속.")
    elif not maj_wrong and not always:
        print(f"  ⚠️ 부분: 다수결 40/40이나 진동문항 {osc} 존재 → 해당 문항 메커니즘 재점검 후 추가 3회.")
    else:
        print(f"  ❌ 미달: 상시오답 {always} / 다수결오답 {maj_wrong}.")
        print("     → 잔차 분류로 증거공백 vs 해석공백 vs 보정실패 분리 보고.")
        print("     해석공백 항목은 40/40 천장에 막힐 수 있으며, 정직한 산출물은 '그 문항=해석 다툼' 평결이다.")
    print(f"  (현재 F 봉인 {N}회. 성공 판정은 N>=3 필요. 점수로 회차 취사선택 금지 — 전건 보고.)")
