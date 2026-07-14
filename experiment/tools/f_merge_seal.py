#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""f_merge_seal.py — 클린룸 X 봉인: {tag}.json + SEAL + _runs/ 스냅샷 + chmod 444 쓰기잠금 + 자가검증.
정답표 복귀 '전' 실행. 사용:
  python3 tools/f_merge_seal.py Foff1   # F0 베이스라인: _parts/Foff1_part_*.json 5개 병합
  python3 tools/f_merge_seal.py F1      # F1 챔피언: _parts/F1_voted.json(다수결+딥다이브 패치본) 봉인
쓰기잠금은 봉인본 사후 교체 사고(A_off ③→⑤, Mplus2 40/40→38/40 재봉인) 재발 방지 장치다.
이미 봉인된 tag의 재봉인은 거부한다 — 정당한 재실행이면 사람 판단으로 기존 봉인을 명시 폐기(_runs에 사유 기록) 후 진행.
"""
import json, glob, hashlib, datetime, sys, os, shutil, stat

CR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_MODEL = "gpt-5.6-sol"
tag = sys.argv[1]  # Foff1|Foff2|Foff3|F1|F2|F3
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

op = f"{CR}/01_sealed/{tag}.json"
sp = f"{CR}/01_sealed/SEAL_{tag}.txt"
if os.path.exists(op) or os.path.exists(sp):
    print(f"✘ {tag}는 이미 봉인됨 — 재봉인 거부(봉인 후 불변 원칙).")
    print("  정당한 재실행이면: 기존 봉인을 _runs/에 폐기 사유와 함께 이동시킨 뒤 다시 실행하라.")
    raise SystemExit(1)

voted = f"{CR}/01_sealed/_parts/{tag}_voted.json"
srcs = []
if os.path.exists(voted):
    data = json.load(open(voted, encoding="utf-8"))
    ans = {a["no"]: a for a in data["answers"]}
    condition = data.get("condition", "F++")
    srcs = [voted]
else:
    parts = sorted(glob.glob(f"{CR}/01_sealed/_parts/{tag}_part_*.json"))
    if tag.startswith("Foff") and len(parts) != 5:
        raise SystemExit(f"✘ {tag}: part 파일 {len(parts)}개(기대 5개) — 누락 슬롯 재실행 필요")
    ans = {}
    models = set()
    for p in parts:
        part = json.load(open(p, encoding="utf-8"))
        models.add(part.get("model", "?"))
        for a in part["answers"]:
            ans[a["no"]] = a
    if models != {EXPECTED_MODEL}:
        raise SystemExit(f"✘ 모델 자기보고 불일치: {sorted(models)} (기대: {EXPECTED_MODEL}) — 해당 슬롯 재실행 필요")
    print(f"✔ 모델 자기보고 검증: {len(parts)}/{len(parts)} 슬롯 = {EXPECTED_MODEL}")
    condition = "F_off(gpt-5.6-sol xhigh 순수지식, 도구 전무)" if tag.startswith("Foff") else "F++"
    srcs = parts

nos = sorted(ans)
assert nos == list(range(1, 41)), f"문항 누락/중복: {nos} (소스={len(srcs)})"
assert all(isinstance(ans[n]["answer"], int) and 1 <= ans[n]["answer"] <= 5 for n in nos), "답 범위 오류"

out = {"group": tag, "subject": "공법", "condition": condition, "answers": [ans[n] for n in nos]}
json.dump(out, open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

seq = "".join(str(ans[n]["answer"]) for n in nos)
contested = [n for n in nos if ans[n].get("contested")]
gaps = {}
for n in nos:
    g = ans[n].get("gap_class", "none")
    if g and g != "none": gaps.setdefault(g, []).append(n)
recalls = [n for n in nos if ans[n].get("recall_flag")]

TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
seal = f"""# SEAL — 클린룸 {tag} 제15회 공법 선택형 (정답표 격리 상태에서 봉인)
봉인 시각: {TS}
[픽스처]      {sha(CR+'/00_fixtures/공법_문항.md')}  00_fixtures/공법_문항.md
[OFF프롬프트]  {sha(CR+'/tools/f_off_prompt.md')}  tools/f_off_prompt.md
[배치프롬프트] {sha(CR+'/tools/f_batch_prompt.md')}  tools/f_batch_prompt.md
[딥다이브]    {sha(CR+'/tools/f_deepdive_prompt.md')}  tools/f_deepdive_prompt.md
[봉인답안]    {sha(op)}  01_sealed/{tag}.json
답렬: {seq}
경합표시(blind): {contested or '없음'}
잔차분류: {gaps or '없음'}
recall_flag(오염 감사, F0만): {recalls or '없음'}
"""
open(sp, "w", encoding="utf-8").write(seal)

# 즉시 스냅샷 + 쓰기잠금(444) — 봉인 후 불변
snapdir = f"{CR}/_runs/{tag}_{sha(op)[:8]}"; os.makedirs(snapdir, exist_ok=True)
shutil.copy(op, snapdir); shutil.copy(sp, snapdir)
for p in srcs: shutil.copy(p, snapdir)
RO = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH  # 444
for p in [op, sp] + [os.path.join(snapdir, f) for f in os.listdir(snapdir)]:
    os.chmod(p, RO)

# 봉인후 자가검증
chk = "".join(str(x["answer"]) for x in json.load(open(op, encoding="utf-8"))["answers"])
locked = not (os.stat(op).st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
print(seal)
print("스냅샷:", snapdir)
print(f"봉인후 자가검증: {'✔ 봉인본=SEAL 일치' if chk == seq else '✘ 불일치 — 봉인 오염!'}")
print(f"쓰기잠금: {'✔ 444' if locked else '✘ 잠금 실패'}")
print(f"→ {tag} 봉인 완료. 전 회차(Foff1~3 + F1~3) 봉인 후 f_grade.py로 일괄 채점.")
