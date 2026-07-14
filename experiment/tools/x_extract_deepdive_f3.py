#!/usr/bin/env python3
import hashlib
import json
import os
import sys

base_path, patched_path, q_raw, out_path = sys.argv[1:]
q = int(q_raw)

with open(base_path, encoding="utf-8") as f:
    base = json.load(f)
with open(patched_path, encoding="utf-8") as f:
    patched = json.load(f)

assert base.keys() == patched.keys(), "최상위 스키마 변경"
assert base["group"] == patched["group"] == "F3", "회차 불일치"
assert len(base["answers"]) == len(patched["answers"]) == 40, "문항 수 변경"

bmap = {x["no"]: x for x in base["answers"]}
pmap = {x["no"]: x for x in patched["answers"]}
assert sorted(bmap) == sorted(pmap) == list(range(1, 41)), "문항 번호 변경"
changed = [n for n in range(1, 41) if bmap[n] != pmap[n]]
assert changed == [q], f"대상 외 변경 또는 미패치: changed={changed}, target={q}"
item = pmap[q]
assert item.get("deepdive") is True, "deepdive=true 누락"
assert item.get("deepdive_model") == "gpt-5.6-sol", "딥다이브 모델 자기보고 불일치"
assert isinstance(item.get("answer"), int) and 1 <= item["answer"] <= 5, "answer 범위 오류"

with open(base_path, "rb") as f:
    base_sha = hashlib.sha256(f.read()).hexdigest()
payload = {
    "run": 3,
    "question": q,
    "model": item["deepdive_model"],
    "base_sha256": base_sha,
    "answer": item,
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
    f.write("\n")
print(f"✔ 문{q}: 대상 항목만 변경, model=gpt-5.6-sol, patch={os.path.basename(out_path)}")
