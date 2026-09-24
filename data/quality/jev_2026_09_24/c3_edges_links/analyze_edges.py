"""Part A analysis: stats + review queues from results_A.jsonl."""
from __future__ import annotations

import csv
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).parent


def load_jsonl(p: Path):
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def excerpt(text: str, n: int = 220) -> str:
    return (text or "")[:n].replace("\n", " ").replace("\r", " ")


def main() -> None:
    candidates = {r["id"]: r for r in load_jsonl(D / "candidates_A.jsonl")}
    results = list(load_jsonl(D / "results_A.jsonl"))
    errors = list(load_jsonl(D / "errors_A.jsonl")) if (D / "errors_A.jsonl").exists() else []

    n = len(results)
    cost = sum(r.get("cost", 0) for r in results)
    tiers = Counter()
    for r in results:
        p = r["p_specific"]
        if p >= 0.9:
            tiers[">=0.9"] += 1
        elif p >= 0.7:
            tiers["0.7-0.9"] += 1
        elif p >= 0.3:
            tiers["0.3-0.7"] += 1
        else:
            tiers["<=0.3"] += 1

    per_rel = defaultdict(lambda: {"n": 0, "sum_specific": 0.0, "sum_generic": 0.0,
                                    "likely_wrong": 0, "weak": 0, "agree_low_generic_high_specific": 0})
    for r in results:
        rel = r["relation"]
        d = per_rel[rel]
        d["n"] += 1
        d["sum_specific"] += r["p_specific"]
        d["sum_generic"] += r["p_generic"]
        if r["p_specific"] <= 0.3 and r["p_generic"] <= 0.3:
            d["likely_wrong"] += 1
        elif 0.3 < r["p_specific"] < 0.7:
            d["weak"] += 1

    with open(D / "stats_by_relation_A.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["relation", "n", "mean_p_specific", "mean_p_generic", "likely_wrong_both<=0.3", "weak_0.3_0.7"])
        for rel, d in sorted(per_rel.items(), key=lambda kv: -kv[1]["n"]):
            w.writerow([rel, d["n"], round(d["sum_specific"] / d["n"], 3), round(d["sum_generic"] / d["n"], 3),
                        d["likely_wrong"], d["weak"]])

    likely_wrong = []
    weak = []
    for r in results:
        c = candidates.get(r["id"])
        if c is None:
            continue
        row = {
            "relation": r["relation"],
            "edge_id": r["id"],
            "source_id": r["source_id"],
            "source_type": c["source"]["type"],
            "source_name": c["source"]["name"],
            "target_id": r["target_id"],
            "target_type": c["target"]["type"],
            "target_name": c["target"]["name"],
            "p_specific": r["p_specific"],
            "p_generic": r["p_generic"],
            "source_excerpt": excerpt(c["source"]["description"]),
            "target_excerpt": excerpt(c["target"]["description"]),
        }
        if r["p_specific"] <= 0.3 and r["p_generic"] <= 0.3:
            likely_wrong.append(row)
        elif 0.3 < r["p_specific"] < 0.7:
            weak.append(row)

    likely_wrong.sort(key=lambda r: (r["p_specific"] + r["p_generic"]))
    weak.sort(key=lambda r: abs(r["p_specific"] - 0.5))

    fieldnames = ["relation", "edge_id", "source_id", "source_type", "source_name",
                  "target_id", "target_type", "target_name", "p_specific", "p_generic",
                  "source_excerpt", "target_excerpt"]
    with open(D / "queue_A_likely_wrong.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(likely_wrong)
    with open(D / "queue_A_weak.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(weak)

    print(f"results {n}/{len(candidates)}, errors {len(errors)}, cost ${cost:.3f}")
    print("confidence tiers (p_specific):", dict(tiers))
    print(f"likely_wrong (both<=0.3): {len(likely_wrong)}, weak (0.3-0.7): {len(weak)}")
    print("wrote stats_by_relation_A.csv, queue_A_likely_wrong.csv, queue_A_weak.csv")


if __name__ == "__main__":
    main()
