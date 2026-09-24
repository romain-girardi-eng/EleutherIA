"""Coverage / cost / confidence-tier stats for REPORT.md. Read-only."""
from __future__ import annotations
import json
from collections import Counter
from lib_common import CAMPAIGN_DIR


def tier(p: float) -> str:
    if p >= 0.9:
        return ">=0.9"
    if p >= 0.7:
        return "0.7-0.9"
    if p >= 0.3:
        return "0.3-0.7"
    return "<=0.3"


def dedup_stats():
    n_calls = n_err = 0
    cost = 0.0
    with (CAMPAIGN_DIR / "results_dedup.jsonl").open(encoding="utf-8") as f:
        for line in f:
            n_calls += 1
            cost += json.loads(line).get("cost") or 0.0
    if (CAMPAIGN_DIR / "errors_dedup.jsonl").exists():
        with (CAMPAIGN_DIR / "errors_dedup.jsonl").open(encoding="utf-8") as f:
            n_err = sum(1 for _ in f)
    n_pairs_total = sum(1 for _ in (CAMPAIGN_DIR / "candidates.jsonl").open(encoding="utf-8"))
    tiers = Counter()
    n_exploded = 0
    if (CAMPAIGN_DIR / "exploded_dedup.jsonl").exists():
        with (CAMPAIGN_DIR / "exploded_dedup.jsonl").open(encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                tiers[tier(d["same_probability"])] += 1
                n_exploded += 1
    return {
        "chunks_done": n_calls, "chunk_errors_logged": n_err,
        "cost_usd": round(cost, 4), "pairs_total": n_pairs_total,
        "pairs_answered": n_exploded, "tiers_same": dict(tiers),
    }


def school_stats():
    n_calls = n_err = 0
    cost = 0.0
    for fname in ("results_school.jsonl", "results_school_pw.jsonl"):
        p = CAMPAIGN_DIR / fname
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for line in f:
                n_calls += 1
                cost += json.loads(line).get("cost") or 0.0
    for fname in ("errors_school.jsonl", "errors_school_pw.jsonl"):
        p = CAMPAIGN_DIR / fname
        if p.exists():
            with p.open(encoding="utf-8") as f:
                n_err += sum(1 for _ in f)
    n_nodes_total = sum(1 for _ in (CAMPAIGN_DIR / "candidates_school.jsonl").open(encoding="utf-8"))
    tiers = Counter()
    n_exploded = 0
    choice_dist = Counter()
    if (CAMPAIGN_DIR / "exploded_school.jsonl").exists():
        with (CAMPAIGN_DIR / "exploded_school.jsonl").open(encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                tiers[tier(d["probability"])] += 1
                choice_dist[d["proposed_school"]] += 1
                n_exploded += 1
    return {
        "chunks_done": n_calls, "chunk_errors_logged": n_err,
        "cost_usd": round(cost, 4), "nodes_total": n_nodes_total,
        "nodes_answered": n_exploded, "tiers_choice_prob": dict(tiers),
        "choice_distribution": dict(choice_dist.most_common()),
    }


if __name__ == "__main__":
    print("DEDUP:", json.dumps(dedup_stats(), indent=2, ensure_ascii=False))
    print("SCHOOL:", json.dumps(school_stats(), indent=2, ensure_ascii=False))
