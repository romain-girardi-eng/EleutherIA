"""Deterministic retrieval A/B: current snapshot runners vs CorpusMap candidates.

No LLM, no DB. For each gold query, compares what each arm would put in front
of the agent before its first tool call:

* A_lexical / A_ppr — the existing ``tests/eval`` snapshot runners
  (BM25 passages + KG label match, optionally Personalized PageRank).
* B_corpusmap — CorpusMap candidates (paper §B.3): top Entity Pages plus the
  BM25-reranked documents linked to them.

Metrics are gold recall of entities, works and passages, plus the size of the
rendered handoff (approximate tokens = chars / 4).

    .venv/bin/python scripts/corpusmap_ab/retrieval_ab.py --out data/eval/corpusmap_ab
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "eval"))

from eleutheria_graphrag.corpusmap import (  # noqa: E402
    build_corpus_map,
    select_candidates,
)
from eval_lib.snapshot_runner import SnapshotIndex  # noqa: E402
from run_eval import load_query_files  # noqa: E402

QUERY_FILES = [
    REPO / "tests/eval/queries.yaml",
    REPO / "tests/eval/release_scholarly_2026_09_06.yaml",
    REPO / "tests/eval/repair_wave_2026_08_24.yaml",
]


def recall(gold: list[str], got: set[str]) -> float | None:
    return None if not gold else sum(g in got for g in gold) / len(gold)


def tokens(text: str) -> int:
    return len(text) // 4


def baseline_handoff(index: SnapshotIndex, ret) -> str:
    lines = []
    for nid in [*ret.entity_ids, *ret.work_ids]:
        row = index.nodes.get(nid, {})
        lines.append(
            f"- {nid} ({row.get('type')}) — {str(row.get('label') or '')[:110]}"
        )
    for pid in ret.passage_ids:
        ident = index.passage_identity(pid) or {}
        lines.append(f"- {pid} (passage) — {ident.get('canonical_ref') or ''}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "data/eval/corpusmap_ab")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cases = [
        c
        for c in load_query_files(QUERY_FILES)
        if c.expected_entities or c.expected_works or c.expected_passages
    ]
    index = SnapshotIndex()
    cmap = build_corpus_map(
        REPO / "data/kg", REPO / "data/corpus", allowed_passages=set(index.passages)
    )

    arms = {
        "A_lexical_k10": lambda q: (
            "snapshot-lexical",
            {"node_k": 10, "passage_k": 10},
        ),
        "A_lexical_default": lambda q: (
            "snapshot-lexical",
            {"node_k": 30, "passage_k": 12},
        ),
        "A_ppr_default": lambda q: (
            "snapshot-ppr-bidirectional",
            {"node_k": 30, "passage_k": 12},
        ),
        "B_corpusmap_5p10d": lambda q: ("corpusmap", {"n_pages": 5, "n_docs": 10}),
        "B_corpusmap_10p20d": lambda q: ("corpusmap", {"n_pages": 10, "n_docs": 20}),
        "C_ppr_plus_corpusmap": lambda q: ("hybrid", {"n_pages": 5, "n_docs": 10}),
    }
    rows = []
    for case in cases:
        for arm, cfg in arms.items():
            kind, kw = cfg(case.query)
            if kind == "hybrid":
                ret = index.retrieve(
                    case.query,
                    strategy="snapshot-ppr-bidirectional",
                    node_k=30,
                    passage_k=12,
                )
                cand = select_candidates(cmap, case.query, **kw)
                got = set(ret.entity_ids) | set(ret.work_ids) | set(ret.passage_ids)
                got |= {e for e, _ in cand.pages} | {d for d, _, _ in cand.documents}
                handoff = baseline_handoff(index, ret) + "\n" + cand.render()
            elif kind == "corpusmap":
                cand = select_candidates(cmap, case.query, **kw)
                got = {e for e, _ in cand.pages} | {d for d, _, _ in cand.documents}
                handoff = cand.render()
            else:
                ret = index.retrieve(case.query, strategy=kind, **kw)
                got = set(ret.entity_ids) | set(ret.work_ids) | set(ret.passage_ids)
                handoff = baseline_handoff(index, ret)
            rows.append(
                {
                    "query_id": case.id,
                    "query_type": case.query_type,
                    "arm": arm,
                    "entity_recall": recall(list(case.expected_entities), got),
                    "work_recall": recall(list(case.expected_works), got),
                    "passage_recall": recall(list(case.expected_passages), got),
                    "handoff_items": len(got),
                    "handoff_tokens": tokens(handoff),
                }
            )

    (args.out / "retrieval_ab_rows.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )
    summary = {}
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        summary[arm] = {
            m: round(mean(v), 4)
            if (v := [r[m] for r in rs if r[m] is not None])
            else None
            for m in (
                "entity_recall",
                "work_recall",
                "passage_recall",
                "handoff_items",
                "handoff_tokens",
            )
        }
        summary[arm]["n_queries"] = len(rs)
    (args.out / "retrieval_ab_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{'arm':<22}{'ent.rec':>9}{'work.rec':>10}{'pass.rec':>10}{'items':>7}{'tok':>6}"
    )
    for arm, s in summary.items():
        print(
            f"{arm:<22}{s['entity_recall']:>9.3f}{s['work_recall']:>10.3f}"
            f"{s['passage_recall']:>10.3f}{s['handoff_items']:>7.1f}{s['handoff_tokens']:>6.0f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
