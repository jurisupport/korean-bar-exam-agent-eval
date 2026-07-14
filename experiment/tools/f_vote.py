#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""f_vote.py — 클린룸 X 단계2: 프레이밍 3표(V1·V2·V3) 다수결 + 경합 식별 (blind: 정답표 미사용).
15개 솔버 part(F{run}_{V}_part_*.json)를 읽어 문항별 다수결 → _parts/F{run}_voted.json 생성.
경합 = 비만장일치 ∨ 지문conf<0.70 ∨ contested플래그 ∨ gap_class:evidence ∨ 워치리스트.
사용: python3 tools/f_vote.py {RUN}
"""
import json, glob, sys, os
from collections import Counter

CR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
run = sys.argv[1] if len(sys.argv) > 1 else "1"
VOTERS = ["V1", "V2", "V3"]
WATCH = {6, 7, 8, 11, 19, 25, 30, 32, 38}  # 과거 진동/난문 이력(사전지식이지 정답지식 아님)
THRESH = 0.70
EXPECTED_MODEL = "gpt-5.6-sol"

# ── parts 로드 (보터별 문항 dict)
by_voter, models = {}, {}
for v in VOTERS:
    parts = sorted(glob.glob(f"{CR}/01_sealed/_parts/F{run}_{v}_part_*.json"))
    if len(parts) != 5:
        raise SystemExit(f"✘ {v}: part 파일 {len(parts)}개(기대 5개) — 누락 슬롯 재실행 필요")
    rows = {}
    for p in parts:
        d = json.load(open(p, encoding="utf-8"))
        models.setdefault(v, set()).add(d.get("model", "?"))
        for a in d["answers"]:
            rows[a["no"]] = a
    by_voter[v] = rows
    missing = [n for n in range(1, 41) if n not in rows]
    if missing:
        print(f"⚠ {v}: 문항 누락 {missing} (parts={len(parts)}) — 해당 배치 재실행 필요")

# ── 모델 검증
for v in VOTERS:
    ms = models.get(v, set())
    bad = {m for m in ms if m != EXPECTED_MODEL}
    if bad:
        raise SystemExit(f"✘ {v} 모델 불일치: {sorted(ms)} (기대: {EXPECTED_MODEL}) — 해당 슬롯 재실행 필요")
print(f"✔ 모델 자기보고 검증: 15/15 슬롯 = {EXPECTED_MODEL}")

def weakest(a):
    props = a.get("propositions") or {}
    best = None
    for k, x in props.items():
        c = x.get("confidence", 1.0) if isinstance(x, dict) else 1.0
        if best is None or c < best[1]:
            best = (k, c)
    return best or (None, a.get("min_prop_confidence", a.get("confidence", 1.0)))

voted, contested = [], []
for n in range(1, 41):
    entries = {v: by_voter[v].get(n) for v in VOTERS}
    avail = {v: e for v, e in entries.items() if e}
    if not avail:
        print(f"✘ 문{n}: 전 보터 누락 — 중단 사유"); continue
    votes = {v: e["answer"] for v, e in avail.items()}
    cnt = Counter(votes.values())
    top, topn = cnt.most_common(1)[0]
    pattern = "-".join(str(c) for _, c in cnt.most_common())  # "3", "2-1", "1-1-1"

    # 대표 레코드 = 다수답 보터 중 min_prop_confidence 최고 (1-1-1이면 전체 중 최고)
    pool = [e for v, e in avail.items() if e["answer"] == top] if topn > 1 else list(avail.values())
    rep = max(pool, key=lambda e: e.get("min_prop_confidence", 0))
    rec = dict(rep)
    rec["answer"] = top if topn > 1 else rec["answer"]
    rec["votes"] = votes
    rec["vote_pattern"] = pattern

    reasons = []
    if len(avail) < len(VOTERS):
        reasons.append(f"보터누락({len(avail)}/{len(VOTERS)})")
    if topn < len(avail):
        reasons.append(f"비만장일치({pattern})")
    wk, wc = weakest(rec)
    mpc = min(rec.get("min_prop_confidence", wc), wc)
    if mpc < THRESH:
        reasons.append(f"지문conf<{THRESH}")
    if any(e.get("contested") for e in avail.values()):
        reasons.append("contested플래그")
    if any(e.get("gap_class") == "evidence" for e in avail.values()):
        reasons.append("증거공백(전문인출실패)")
    if n in WATCH:
        reasons.append("워치리스트")
    if reasons:
        rec["contested"] = True
        rec["contest_reasons"] = reasons
        contested.append((n, "+".join(reasons), f"약한지문 {wk}={wc}" if wk else f"conf={wc}",
                          rec.get("gap_class", "none")))
    voted.append(rec)

nos = sorted(r["no"] for r in voted)
assert nos == list(range(1, 41)), f"문항 누락/중복: {nos}"
out = {"group": f"F{run}", "subject": "공법",
       "condition": "F++(gpt-5.6-sol xhigh 프레이밍3표 다수결 + 전문가드 + 경합한정 딥다이브)",
       "answers": sorted(voted, key=lambda r: r["no"])}
op = f"{CR}/01_sealed/_parts/F{run}_voted.json"
json.dump(out, open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"\n## 다수결 완료 → {os.path.relpath(op, CR)}")
print("답렬(잠정):", "".join(str(r["answer"]) for r in out["answers"]))
print(f"\n## 경합문항 (F{run}) — 단계3 딥다이브 대상  [{len(contested)}개]")
for n, why, detail, gap in contested:
    print(f"  문{n:2}: {why:40} {detail} {('['+gap+']') if gap and gap!='none' else ''}")
print("\n주: 정답표 미사용. 불확실성·투표분열·약한지문·이력으로만 선정(blind).")
print("→ 각 경합문항을 f_deepdive_prompt.md로 독립 codex exec(gpt-5.6-sol, xhigh) 딥다이브 → voted.json 패치 → f_merge_seal.py")
