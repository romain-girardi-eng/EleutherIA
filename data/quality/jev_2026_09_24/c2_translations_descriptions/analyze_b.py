"""Part B analysis: tiers, queues, headline stats for description <-> identity integrity."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

D = Path(__file__).parent

MODERN_PERIODS = {"Modern", "Contemporary"}
ANCIENT_PERIODS = {
    "Presocratic", "Classical Greek", "Hellenistic", "Roman Imperial",
    "Late Antiquity", "Patristic", "Medieval", "Early Modern",
}


def load_jsonl(p):
    if not Path(p).exists():
        return
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


def excerpt(s: str, n: int = 220) -> str:
    return (s or "").replace("\n", " ").strip()[:n]


def main() -> None:
    cands = {c["id"]: c for c in load_jsonl(D / "candidates_b.jsonl")}
    results = list(load_jsonl(D / "results_b.jsonl"))
    errors = list(load_jsonl(D / "errors_b.jsonl"))

    n = len(results)
    cost = sum(float(r.get("cost") or 0.0) for r in results)
    tokens = sum(int(r.get("tokens") or 0) for r in results)
    print(f"PART B -- results: {n}/{len(cands)}  errors: {len(errors)}  cost: ${cost:.4f}  tokens: {tokens:,}")

    identity_tiers = Counter()
    mismatch = []
    curator_leaks = []
    non_english = []
    layer_conflicts = []
    lang_counter = Counter()

    for r in results:
        if "answers" not in r:
            continue
        c = cands.get(r["id"])
        if c is None:
            continue
        a = r["answers"]
        ae = a["about_entity"]["p"]
        identity_tiers[tier(ae)] += 1
        row_base = {
            "node_id": c["id"],
            "label": c["label"],
            "type": c["type"],
            "period": c.get("period"),
        }
        if ae <= 0.3:
            mismatch.append({**row_base, "p_about_entity": ae,
                              "description_excerpt": excerpt(c["state"]["description"])})
        cn = a["curator_notes"]["p"]
        if cn >= 0.7:
            curator_leaks.append({**row_base, "p_curator_notes": cn,
                                   "description_excerpt": excerpt(c["state"]["description"])})
        lang = a["language"]
        lang_counter[lang["choice"]] += 1
        if lang["choice"] != "en" and lang["probs"].get(lang["choice"], 0) >= 0.7:
            non_english.append({**row_base, "language": lang["choice"],
                                 "p_language": lang["probs"].get(lang["choice"]),
                                 "description_excerpt": excerpt(c["state"]["description"])})
        if c.get("is_person") and "modern_scholar" in a:
            ms = a["modern_scholar"]["p"]
            period = c.get("period")
            conflict = None
            if ms >= 0.7 and period in ANCIENT_PERIODS:
                conflict = "described_as_modern_but_period_ancient"
            elif ms <= 0.3 and period in MODERN_PERIODS:
                conflict = "described_as_ancient_but_period_modern"
            if conflict:
                layer_conflicts.append({**row_base, "p_modern_scholar": ms, "conflict": conflict,
                                         "description_excerpt": excerpt(c["state"]["description"])})

    mismatch.sort(key=lambda x: x["p_about_entity"])
    curator_leaks.sort(key=lambda x: -x["p_curator_notes"])
    non_english.sort(key=lambda x: (x["language"], -x["p_language"]))
    layer_conflicts.sort(key=lambda x: -abs(x["p_modern_scholar"] - 0.5))

    def write_csv(path, rows):
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    write_csv(D / "queue_b_identity_mismatch.csv", mismatch)
    write_csv(D / "queue_b_curator_notes.csv", curator_leaks)
    write_csv(D / "queue_b_non_english.csv", non_english)
    write_csv(D / "queue_b_layer_conflicts.csv", layer_conflicts)

    print(f"about_entity tiers: {dict(identity_tiers)}")
    print(f"identity mismatches (p<=0.3): {len(mismatch)}")
    print(f"curator-notes leaks (p>=0.7): {len(curator_leaks)}")
    print(f"non-English descriptions (p>=0.7): {len(non_english)}  by language: {dict(lang_counter)}")
    print(f"person layer conflicts: {len(layer_conflicts)}")

    summary = {
        "n_results": n,
        "n_candidates": len(cands),
        "n_errors": len(errors),
        "cost_usd": cost,
        "input_tokens": tokens,
        "about_entity_tiers": dict(identity_tiers),
        "n_identity_mismatch": len(mismatch),
        "n_curator_notes_leak": len(curator_leaks),
        "n_non_english": len(non_english),
        "language_distribution": dict(lang_counter),
        "n_layer_conflicts": len(layer_conflicts),
    }
    (D / "summary_b.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
