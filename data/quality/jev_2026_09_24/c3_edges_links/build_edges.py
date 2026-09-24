"""Part A — build candidates + questions for validating existing semantic KG edges.

Reads data/kg/nodes.jsonl + data/kg/edges.jsonl (read-only). Selects every
non-structural relation with >= 30 edges total, builds one candidate row per
edge with {source, target} node summaries, and writes one question template
per relation (a literal, relation-specific boolean) plus a generic boolean
asked on every edge for comparison.

Outputs (this directory):
  questions_A.json     -- {relation: {"specific": "...", } } + "_generic"
  candidates_A.jsonl    -- one row per edge: id, relation, source, target, edge_id
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("/Users/romaingirardi/Projects/EleutherIA/data")
OUT = Path(__file__).parent

STRUCTURAL = {
    "authored_by", "part_of", "has_section", "has_chapter", "translation_of",
    "member_of", "created_by", "advanced_in", "belongs_to_corpus",
}
MIN_EDGES = 30
MAX_DESC = 3000
MAX_PASSAGE = 4000


def load_jsonl(p: Path):
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def node_id(n: dict) -> str:
    return n.get("node_id") or n.get("id")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


# ---------------------------------------------------------------------------
# Relation-specific literal boolean templates. Each references the JSON
# state fields `source` and `target` (type/name/description) directly, since
# Jev reads the whole state object. Kept literal to the relation semantics,
# not generic "does this relation hold" phrasing (that's the second question).
# ---------------------------------------------------------------------------
REL_TEMPLATES = {
    "cites_primary_source": (
        "`target` is an ancient primary-source passage or work whose wording or "
        "content `source`, as described, explicitly relies on and cites as evidence."
    ),
    "evidenced_by": (
        "`target` is a primary source that contains wording or content directly "
        "evidencing the claim, concept or argument described in `source`."
    ),
    "source_for": (
        "`source`, a primary text or work, directly provides the textual basis or "
        "origin that `target`, as described, draws on."
    ),
    "discusses": (
        "`source`, as described, explicitly discusses or addresses the topic, "
        "person, concept, work, school or text described in `target`."
    ),
    "engages_with": (
        "`source`, as described, directly engages with, responds to, or debates "
        "`target`, as described (not merely sharing a period or topic)."
    ),
    "creates": (
        "`source` is described as the creator, author or originator of `target` "
        "(the argument, work or concept)."
    ),
    "interprets": (
        "`source`, as described, offers an interpretation or reading of `target`, "
        "as described."
    ),
    "contributes_to": (
        "`source`, as described, is presented as making a substantive contribution "
        "to `target` (a debate or larger inquiry)."
    ),
    "influences": (
        "`source`, as described, is presented as having had a direct influence on "
        "`target`, as described."
    ),
    "influenced_by": (
        "`source`, as described, is presented as having been directly influenced by "
        "`target`, as described."
    ),
    "extends": (
        "`source`, as described, is presented as extending, building on, or "
        "developing further `target`, as described."
    ),
    "contains": (
        "`target` is presented as a constituent part or component contained within "
        "`source`, as described."
    ),
    "critiques": (
        "`source`, as described, explicitly critiques, challenges, or argues "
        "against `target`, as described."
    ),
    "employs": (
        "`source`, as described, explicitly employs, uses, or relies on `target` "
        "(a concept, method or argument) in its own reasoning."
    ),
    "parallel_to": (
        "`source` and `target` are presented as closely parallel or analogous to "
        "each other, as described."
    ),
    "supports": (
        "`source`, as described, provides support for or corroborates `target`, "
        "as described."
    ),
    "same_thesis_as": (
        "`source` and `target` are presented as advancing the same thesis or "
        "conclusion, as described."
    ),
    "has_position": (
        "`target` is presented as a distinct position taken within the debate "
        "described in `source`."
    ),
    "participates_in": (
        "`source` (a person) is presented as an active participant in `target` "
        "(a debate, controversy or event), as described."
    ),
    "grounded_in": (
        "`source`, as described, is presented as resting on or grounded in "
        "`target`, as described."
    ),
    "exemplifies": (
        "`source`, as described, is presented as a concrete example or instance "
        "of `target`, as described."
    ),
    "precedes": (
        "`source` is presented as chronologically or logically preceding "
        "`target`, as described."
    ),
    "presupposes": (
        "`source`, as described, logically presupposes or depends on `target`, "
        "as described."
    ),
}

GENERIC_INSTRUCTION = (
    "The relation holds between these two entities as described: `target` "
    "stands in the stated relation to `source`, taking both descriptions at "
    "face value."
)


def node_summary(n: dict) -> dict:
    t = n.get("type")
    cap = MAX_PASSAGE if t == "passage" else MAX_DESC
    desc = clean(n.get("description") or "")
    return {
        "type": t,
        "name": n.get("label") or n.get("id"),
        "description": desc[:cap],
    }


def main() -> None:
    nodes = {}
    for n in load_jsonl(ROOT / "kg/nodes.jsonl"):
        nodes[node_id(n)] = n

    rel_counts: dict[str, int] = {}
    for e in load_jsonl(ROOT / "kg/edges.jsonl"):
        rel = e.get("relation")
        rel_counts[rel] = rel_counts.get(rel, 0) + 1

    target_rels = {
        r for r, c in rel_counts.items()
        if r not in STRUCTURAL and c >= MIN_EDGES
    }
    print("relations selected:", sorted(target_rels))

    questions = {}
    for r in sorted(target_rels):
        tmpl = REL_TEMPLATES.get(r)
        if tmpl is None:
            tmpl = (
                f"`source`, as described, stands in the `{r}` relation to "
                "`target`, as described, in the specific sense that relation "
                "name implies (not merely a loose thematic connection)."
            )
        questions[r] = {"specific": tmpl, "generic": GENERIC_INSTRUCTION}
    with open(OUT / "questions_A.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=1)

    n_written = 0
    n_skipped_missing = 0
    n_skipped_empty = 0
    with open(OUT / "candidates_A.jsonl", "w", encoding="utf-8") as f:
        for e in load_jsonl(ROOT / "kg/edges.jsonl"):
            rel = e.get("relation")
            if rel not in target_rels:
                continue
            s_id = e.get("source") or e.get("source_id")
            t_id = e.get("target") or e.get("target_id")
            sn = nodes.get(s_id)
            tn = nodes.get(t_id)
            if sn is None or tn is None:
                n_skipped_missing += 1
                continue
            src = node_summary(sn)
            tgt = node_summary(tn)
            if not src["description"] or not tgt["description"]:
                n_skipped_empty += 1
                continue
            row = {
                "id": e.get("edge_id"),
                "relation": rel,
                "source_id": s_id,
                "target_id": t_id,
                "source": src,
                "target": tgt,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_written += 1

    print(f"candidates written: {n_written}, skipped missing-node: {n_skipped_missing}, "
          f"skipped empty-desc: {n_skipped_empty}")
    print(f"relations: {len(target_rels)}, total edges considered: {sum(rel_counts[r] for r in target_rels)}")


if __name__ == "__main__":
    main()
