"""Part A analysis: tiers, queues, headline stats for translation_of alignment."""
from __future__ import annotations

import csv
import json
import statistics as st
from collections import Counter
from pathlib import Path

D = Path(__file__).parent


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def tier(p: float) -> str:
    if p >= 0.9:
        return ">=0.9"
    if p >= 0.7:
        return "0.7-0.9"
    if p >= 0.3:
        return "0.3-0.7"
    return "<=0.3"


def excerpt(s: str, n: int = 180) -> str:
    return (s or "").replace("\n", " ").strip()[:n]


def main() -> None:
    cands = {c["id"]: c for c in load_jsonl(D / "candidates_a.jsonl")}
    results = list(load_jsonl(D / "results_a.jsonl"))
    errors = list(load_jsonl(D / "errors_a.jsonl")) if (D / "errors_a.jsonl").exists() else []
    determ = list(load_jsonl(D / "determ_flags_a.jsonl"))

    n = len(results)
    cost = sum(float(r.get("cost") or 0.0) for r in results)
    tokens = sum(int(r.get("tokens") or 0) for r in results)
    print(f"PART A -- results: {n}/{len(cands)}  errors: {len(errors)}  cost: ${cost:.4f}  tokens: {tokens:,}")

    same_content_tiers = Counter()
    misaligned = []
    partial_cov = []
    identical = []
    lang_mismatch = []

    for r in results:
        if "answers" not in r:
            continue
        c = cands.get(r["id"])
        if c is None:
            continue
        a = r["answers"]
        sc = a["same_content"]["p"]
        same_content_tiers[tier(sc)] += 1
        row_base = {
            "edge_id": c["id"],
            "translation_id": c["translation_id"],
            "original_id": c["original_id"],
            "translation_label": c["translation_label"],
            "original_label": c["original_label"],
        }
        if sc <= 0.3:
            misaligned.append({**row_base, "p_same_content": sc,
                                "coverage_choice": a["coverage"]["choice"],
                                "original_excerpt": excerpt(c["state"]["original"]),
                                "translation_excerpt": excerpt(c["state"]["translation"])})
        cov = a["coverage"]
        if cov["choice"] == "partial" and (cov["probs"].get("partial", 0) >= 0.7):
            partial_cov.append({**row_base, "p_partial": cov["probs"].get("partial"),
                                 "p_same_content": sc,
                                 "original_excerpt": excerpt(c["state"]["original"]),
                                 "translation_excerpt": excerpt(c["state"]["translation"])})
        it = a["identical_text"]["p"]
        if it >= 0.7:
            identical.append({**row_base, "p_identical": it,
                               "original_excerpt": excerpt(c["state"]["original"]),
                               "translation_excerpt": excerpt(c["state"]["translation"])})
        fr = a["is_french"]["p"]
        en = a["is_english"]["p"]
        if fr >= 0.7 and en < 0.5:
            lang_mismatch.append({**row_base, "p_is_french": fr, "p_is_english": en,
                                   "translation_language_meta": c.get("translation_language_meta"),
                                   "translation_excerpt": excerpt(c["state"]["translation"])})

    misaligned.sort(key=lambda x: x["p_same_content"])
    partial_cov.sort(key=lambda x: -x["p_partial"])
    identical.sort(key=lambda x: -x["p_identical"])
    lang_mismatch.sort(key=lambda x: -x["p_is_french"])

    def write_csv(path, rows):
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    write_csv(D / "queue_a_misaligned.csv", misaligned)
    write_csv(D / "queue_a_partial_coverage.csv", partial_cov)
    write_csv(D / "queue_a_identical_text.csv", identical)
    write_csv(D / "queue_a_language_mismatch.csv", lang_mismatch)

    determ_rows = []
    for d in determ:
        determ_rows.append({**d})
    write_csv(D / "queue_a_deterministic_flags.csv", determ_rows)

    print(f"same_content tiers: {dict(same_content_tiers)}")
    print(f"misaligned (p<=0.3): {len(misaligned)}")
    print(f"partial coverage (p>=0.7): {len(partial_cov)}")
    print(f"identical text (p>=0.7): {len(identical)}")
    print(f"language mismatch (French, not English): {len(lang_mismatch)}")
    print(f"deterministic flags (empty/identical/near-identical): {len(determ)}")

    summary = {
        "n_results": n,
        "n_candidates": len(cands),
        "n_errors": len(errors),
        "cost_usd": cost,
        "input_tokens": tokens,
        "same_content_tiers": dict(same_content_tiers),
        "n_misaligned": len(misaligned),
        "n_partial_coverage": len(partial_cov),
        "n_identical_text": len(identical),
        "n_language_mismatch": len(lang_mismatch),
        "n_deterministic_flags": len(determ),
    }
    (D / "summary_a.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
