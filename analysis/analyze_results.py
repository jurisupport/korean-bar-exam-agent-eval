#!/usr/bin/env python3
"""Recompute the published accuracy and workflow decomposition metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiment"
SEALED = EXP / "01_sealed"
PARTS = SEALED / "_parts"

EXPECTED_HASHES = {
    "Foff1": "b26a0d1d720987135421231e8cbf3ce34da10efa9e8a8aeeba2705c89f366ff5",
    "Foff2": "a22fe5f3d17c3ffd119dd279f74172e943008df65ef9992db21dde734c5c3122",
    "Foff3": "6f58d2157d8a05dbf3d39a6938caf8b496404cb9d725376240c8ef39fadd570c",
    "F1": "34b47ad027c9b452be57b1b92625c2edc596f6c2c22fb499009658cab6d9c4e4",
    "F2": "44ce0a3da3281e5ad3daed12bb11fa15950144f92d05b686847789768b6d8434",
    "F3": "2bc8c55b0e2ae2cfab7413149257ddce582129c608bb9c92c120d4a34fa271a7",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def answer_map(path: Path):
    return {row["no"]: row for row in read_json(path)["answers"]}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_variant(run: int, variant: str):
    rows = {}
    for path in sorted(PARTS.glob(f"F{run}_{variant}_part_*.json")):
        for row in read_json(path)["answers"]:
            rows[row["no"]] = row
    if sorted(rows) != list(range(1, 41)):
        raise RuntimeError(f"F{run} {variant}: incomplete question set")
    return rows


def compute_metrics():
    key_data = read_json(EXP / "03_answer_key" / "공법_정답.json")["key"]
    key = {int(number): answer for number, answer in key_data.items()}

    integrity = {}
    for tag, expected in EXPECTED_HASHES.items():
        actual = sha256(SEALED / f"{tag}.json")
        integrity[tag] = {"expected": expected, "actual": actual, "ok": actual == expected}

    off_runs = []
    off_miss_frequency = Counter()
    for run in (1, 2, 3):
        answers = answer_map(SEALED / f"Foff{run}.json")
        wrong = [number for number in range(1, 41) if answers[number]["answer"] != key[number]]
        off_miss_frequency.update(wrong)
        off_runs.append({"run": run, "score": 40 - len(wrong), "wrong": wrong})

    on_runs = []
    variant_scores = defaultdict(list)
    for run in (1, 2, 3):
        variants = {name: load_variant(run, name) for name in ("V1", "V2", "V3")}
        scores = {
            name: sum(rows[number]["answer"] == key[number] for number in range(1, 41))
            for name, rows in variants.items()
        }
        for name, score in scores.items():
            variant_scores[name].append(score)

        majority = {}
        vote_patterns = Counter()
        votes_by_question = {}
        for number in range(1, 41):
            votes = [variants[name][number]["answer"] for name in ("V1", "V2", "V3")]
            counts = Counter(votes)
            majority[number] = counts.most_common(1)[0][0]
            votes_by_question[number] = votes
            vote_patterns["-".join(map(str, sorted(counts.values(), reverse=True)))] += 1

        final = answer_map(SEALED / f"F{run}.json")
        flips = [number for number in range(1, 41) if final[number]["answer"] != majority[number]]
        improved = [
            number
            for number in flips
            if majority[number] != key[number] and final[number]["answer"] == key[number]
        ]
        harmed = [
            number
            for number in flips
            if majority[number] == key[number] and final[number]["answer"] != key[number]
        ]
        deepdives = [number for number in range(1, 41) if final[number].get("deepdive") is True]

        on_runs.append(
            {
                "run": run,
                "variant_scores": scores,
                "vote_patterns": dict(vote_patterns),
                "majority_score": sum(majority[number] == key[number] for number in range(1, 41)),
                "final_score": sum(final[number]["answer"] == key[number] for number in range(1, 41)),
                "deepdive_count": len(deepdives),
                "flips": flips,
                "flip_vote_patterns": {
                    str(number): "-".join(
                        map(str, sorted(Counter(votes_by_question[number]).values(), reverse=True))
                    )
                    for number in flips
                },
                "improved": improved,
                "harmed": harmed,
            }
        )

    return {
        "integrity": integrity,
        "off_runs": off_runs,
        "off_mean": sum(item["score"] for item in off_runs) / len(off_runs),
        "off_unique_missed": sorted(off_miss_frequency),
        "off_miss_frequency": dict(sorted(off_miss_frequency.items())),
        "on_runs": on_runs,
        "variant_means": {
            name: sum(scores) / len(scores) for name, scores in sorted(variant_scores.items())
        },
        "deepdive_total": sum(item["deepdive_count"] for item in on_runs),
        "deepdive_rate": sum(item["deepdive_count"] for item in on_runs) / 120,
        "flip_total": sum(len(item["flips"]) for item in on_runs),
        "improved_total": sum(len(item["improved"]) for item in on_runs),
        "harmed_total": sum(len(item["harmed"]) for item in on_runs),
    }


def print_text(metrics):
    print("Integrity")
    for tag, result in metrics["integrity"].items():
        print(f"  {tag}: {'OK' if result['ok'] else 'MISMATCH'} {result['actual']}")

    print("\nOFF")
    for item in metrics["off_runs"]:
        print(f"  Foff{item['run']}: {item['score']}/40, wrong={item['wrong']}")
    print(f"  mean: {metrics['off_mean']:.1f}/40")
    print(f"  unique missed: {metrics['off_unique_missed']}")

    print("\nON workflow decomposition")
    for item in metrics["on_runs"]:
        print(
            f"  F{item['run']}: variants={item['variant_scores']} "
            f"majority={item['majority_score']}/40 final={item['final_score']}/40 "
            f"deepdives={item['deepdive_count']} flips={item['flips']} "
            f"improved={item['improved']} harmed={item['harmed']}"
        )
    print(f"  variant means: {metrics['variant_means']}")
    print(
        f"  deepdives: {metrics['deepdive_total']}/120 "
        f"({metrics['deepdive_rate'] * 100:.1f}%)"
    )
    print(
        f"  flips: {metrics['flip_total']}, improved: {metrics['improved_total']}, "
        f"harmed: {metrics['harmed_total']}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args()
    metrics = compute_metrics()
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    else:
        print_text(metrics)
    if not all(result["ok"] for result in metrics["integrity"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
