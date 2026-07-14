#!/usr/bin/env python3
import glob
import json
import os

cr = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
voted_path = os.path.join(cr, "01_sealed", "_parts", "F1_voted.json")
patches = sorted(glob.glob(os.path.join(cr, "01_sealed", "_parts", "F1_deepdive_q*.patch.json")))
expected = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20,
            21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
            37, 38, 39, 40]
assert len(patches) == len(expected), f"patch 수 {len(patches)} != {len(expected)}"

with open(voted_path, encoding="utf-8") as f:
    original = json.load(f)
merged = json.loads(json.dumps(original, ensure_ascii=False))
idx = {x["no"]: i for i, x in enumerate(merged["answers"])}
seen = []
for path in patches:
    with open(path, encoding="utf-8") as f:
        patch = json.load(f)
    q = patch["question"]
    seen.append(q)
    assert patch["run"] == 1 and patch["model"] == "gpt-5.6-sol"
    assert patch["answer"]["no"] == q and patch["answer"].get("deepdive") is True
    merged["answers"][idx[q]] = patch["answer"]
assert seen == expected, f"대상 문항 불일치: {seen}"

target = set(expected)
omap = {x["no"]: x for x in original["answers"]}
mmap = {x["no"]: x for x in merged["answers"]}
assert all(omap[n] == mmap[n] for n in omap if n not in target), "비대상 문항 변경"
assert all(mmap[n].get("deepdive") is True for n in target), "대상 딥다이브 누락"

with open(voted_path, "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=1)
print(f"✔ F1_voted 병합: 딥다이브 {len(expected)}/{len(expected)}, 비대상 문항 보존")
