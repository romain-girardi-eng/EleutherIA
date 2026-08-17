"""Corpus integrity gate for resolution and citation uniqueness.

--report (default): print counts, always exit 0 (use while dangling refs are
expected, i.e. before the corpus is reconciled).
--strict: exit 1 on dangling references, duplicate passage ids, or duplicate
``(passage_id, kg_node_id, citation_type)`` citation triplets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.corpus_lib import read_jsonl

ROOT = Path(__file__).resolve().parents[1]
PASSAGES_PATH = ROOT / "data" / "corpus" / "passages.jsonl"
CITATIONS_PATH = ROOT / "data" / "corpus" / "citations.jsonl"
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"


def _duplicates(rows: list[dict], key) -> list[dict]:
    seen = set()
    duplicates = []
    for row in rows:
        value = key(row)
        if value in seen:
            duplicates.append(row)
        else:
            seen.add(value)
    return duplicates


def find_violations(passages: list[dict], citations: list[dict],
                    node_ids: set[str]) -> dict[str, list[dict]]:
    passage_ids = {p.get("passage_id") for p in passages}
    dangling_passage = [c for c in citations if c.get("passage_id") not in passage_ids]
    dangling_node = [c for c in citations if c.get("kg_node_id") not in node_ids]
    duplicate_passage_id = _duplicates(passages, lambda row: row.get("passage_id"))
    duplicate_citation_triplet = _duplicates(
        citations,
        lambda row: (
            row.get("passage_id"),
            row.get("kg_node_id"),
            row.get("citation_type"),
        ),
    )
    return {
        "dangling_passage": dangling_passage,
        "dangling_node": dangling_node,
        "duplicate_passage_id": duplicate_passage_id,
        "duplicate_citation_triplet": duplicate_citation_triplet,
    }


def main(strict: bool) -> int:
    passages = read_jsonl(PASSAGES_PATH)
    citations = read_jsonl(CITATIONS_PATH)
    with NODES_PATH.open(encoding="utf-8") as handle:
        node_ids = {
            row.get("id") or row.get("node_id")
            for row in (
                json.loads(line) for line in handle if line.strip()
            )
        }
    v = find_violations(passages, citations, node_ids)
    dp, dn = len(v["dangling_passage"]), len(v["dangling_node"])
    dpid = len(v["duplicate_passage_id"])
    dct = len(v["duplicate_citation_triplet"])
    print(f"citations={len(citations)} passages={len(passages)}")
    print(f"dangling citation->passage: {dp}")
    print(f"dangling citation->kg_node: {dn}")
    print(f"duplicate passage_id rows: {dpid}")
    print(f"duplicate citation triplets: {dct}")
    if strict and (dp or dn or dpid or dct):
        print("STRICT: corpus invariant violations present -> FAIL")
        return 1
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    raise SystemExit(main(ap.parse_args().strict))
