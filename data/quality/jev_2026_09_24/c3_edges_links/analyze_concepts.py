"""Part B analysis: stats + review queues from results_B.jsonl."""
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
    candidates = {r["id"]: r for r in load_jsonl(D / "candidates_B.jsonl")}
    concepts = json.loads((D / "concepts_B.json").read_text(encoding="utf-8"))
    results = list(load_jsonl(D / "results_B.jsonl"))
    errors = list(load_jsonl(D / "errors_B.jsonl")) if (D / "errors_B.jsonl").exists() else []

    n_nodes = len(results)
    cost = sum(r.get("cost", 0) for r in results)
    n_judgments = sum(len(r["p"]) for r in results)

    tiers = Counter()
    new_high = []
    contradicted = []
    uncertain = []
    per_concept = defaultdict(lambda: {"sur": 0, "probable": 0, "existing": 0, "existing_contradicted": 0})
    per_type = defaultdict(lambda: {"n_nodes": 0, "n_new_sur": 0})

    for r in results:
        c = candidates.get(r["id"])
        if c is None:
            continue
        per_type[r["type"]]["n_nodes"] += 1
        existing = set(c.get("existing") or [])
        node_new_sur = 0
        for cid, p in r["p"].items():
            if p >= 0.9:
                tiers[">=0.9"] += 1
            elif p >= 0.7:
                tiers["0.7-0.9"] += 1
            elif p >= 0.3:
                tiers["0.3-0.7"] += 1
            else:
                tiers["<=0.3"] += 1

            is_existing = cid in existing
            if is_existing:
                per_concept[cid]["existing"] += 1
                if p <= 0.3:
                    per_concept[cid]["existing_contradicted"] += 1
                    contradicted.append({
                        "node_id": r["id"], "node_type": r["type"], "node_name": c["name"],
                        "concept_id": cid, "concept_label": concepts[cid]["label"], "p": p,
                        "node_excerpt": excerpt(c["description"]),
                    })
            else:
                if p >= 0.9:
                    per_concept[cid]["sur"] += 1
                    node_new_sur += 1
                    new_high.append({
                        "node_id": r["id"], "node_type": r["type"], "node_name": c["name"],
                        "concept_id": cid, "concept_label": concepts[cid]["label"], "p": p,
                        "node_excerpt": excerpt(c["description"]),
                    })
                elif p >= 0.7:
                    per_concept[cid]["probable"] += 1
                elif 0.3 <= p < 0.7:
                    uncertain.append({
                        "node_id": r["id"], "node_type": r["type"], "node_name": c["name"],
                        "concept_id": cid, "concept_label": concepts[cid]["label"], "p": p,
                        "node_excerpt": excerpt(c["description"]),
                    })
        per_type[r["type"]]["n_new_sur"] += node_new_sur

    new_high.sort(key=lambda r: -r["p"])
    contradicted.sort(key=lambda r: r["p"])
    uncertain.sort(key=lambda r: abs(r["p"] - 0.5))

    fieldnames = ["node_id", "node_type", "node_name", "concept_id", "concept_label", "p", "node_excerpt"]
    with open(D / "queue_B_new_high_conf.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(new_high)
    with open(D / "queue_B_contradicted.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(contradicted)
    with open(D / "queue_B_uncertain_sample.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(uncertain[:3000])

    with open(D / "stats_by_concept_B.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["concept_id", "label", "existing_edges", "existing_contradicted_p<=0.3",
                    "new_sure_p>=0.9", "new_probable_0.7_0.9"])
        for cid, d in sorted(per_concept.items(), key=lambda kv: -kv[1]["sur"]):
            w.writerow([cid, concepts[cid]["label"], d["existing"], d["existing_contradicted"], d["sur"], d["probable"]])

    with open(D / "stats_by_type_B.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node_type", "n_nodes_evaluated", "n_new_sure_links_p>=0.9"])
        for t, d in sorted(per_type.items(), key=lambda kv: -kv[1]["n_nodes"]):
            w.writerow([t, d["n_nodes"], d["n_new_sur"]])

    print(f"nodes evaluated {n_nodes}/{len(candidates)}, errors {len(errors)}, "
          f"judgments {n_judgments:,}, cost ${cost:.3f}")
    print("confidence tiers:", dict(tiers))
    print(f"new_high_conf (p>=0.9, no existing edge): {len(new_high)}")
    print(f"contradicted (existing edge, p<=0.3): {len(contradicted)}")
    print(f"uncertain sample written: {min(len(uncertain), 3000)} / {len(uncertain)}")


if __name__ == "__main__":
    main()
