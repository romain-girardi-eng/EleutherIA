"""Summarize G2 eval runs: agentic vs BM25 (+ optional vanilla).

Reads run_*.json produced by tests/eval/run_eval.py and prints the headline
table the G2 plan §3 specifies: citation_f1_mean, mean citation_recall,
entity/work recall, forbidden_hits_total, latency, judge verified_rate.

Usage:
    python data/goals/g2/_summarize.py run_bm25.json run_graphrag.json [run_vanilla.json]
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def mean(xs: list[float]) -> float | None:
    return round(statistics.mean(xs), 4) if xs else None


def summarize(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    agg = d["aggregate"]
    results = d["results"]
    succ = [r for r in results if r.get("error") is None]

    cit_rec = [r["citation_recall"] for r in succ if r.get("citation_recall") is not None]
    cit_prec = [r["citation_precision"] for r in succ if r.get("citation_precision") is not None]
    cit_f1 = [r["citation_f1"] for r in succ if r.get("citation_f1") is not None]
    vr = [r["judge"]["verified_rate"] for r in succ if r.get("judge")]

    return {
        "base_url": d.get("base_url"),
        "n_queries": d.get("n_queries"),
        "successes": agg["successes"],
        "error_rate": agg["error_rate"],
        "citation_f1_mean": mean(cit_f1),
        "citation_recall_mean": mean(cit_rec),
        "citation_precision_mean": mean(cit_prec),
        "citation_scored_queries": len(cit_f1),
        "entity_recall_mean": agg["entity_recall_mean"],
        "work_recall_mean": agg["work_recall_mean"],
        "keyword_hit_rate_mean": agg["keyword_hit_rate_mean"],
        "citation_count_mean": agg["citation_count_mean"],
        "forbidden_hits_total": agg["forbidden_hits_total"],
        "latency_p50_ms": agg["latency_p50_ms"],
        "latency_p95_ms": agg["latency_p95_ms"],
        "latency_mean_ms": agg["latency_mean_ms"],
        "judge_verified_rate_mean": mean(vr),
        "judged_queries": len(vr),
    }


def main(argv: list[str]) -> int:
    paths = [Path(p) for p in argv]
    summaries = {p.stem: summarize(p) for p in paths}
    print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
