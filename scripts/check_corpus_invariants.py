"""Corpus integrity gate: every citation must resolve to a passage AND a KG node.

--report (default): print counts, always exit 0 (use while dangling refs are
expected, i.e. before the corpus is reconciled).
--strict: exit 1 if any dangling reference exists (flip to this in CI once the
corpus is reconciled).
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


def find_violations(passages: list[dict], citations: list[dict],
                    node_ids: set[str]) -> dict[str, list[dict]]:
    passage_ids = {p["passage_id"] for p in passages}
    dangling_passage = [c for c in citations if c.get("passage_id") not in passage_ids]
    dangling_node = [c for c in citations if c.get("kg_node_id") not in node_ids]
    return {"dangling_passage": dangling_passage, "dangling_node": dangling_node}


def main(strict: bool) -> int:
    passages = read_jsonl(PASSAGES_PATH)
    citations = read_jsonl(CITATIONS_PATH)
    node_ids = {json.loads(l)["id"] for l in open(NODES_PATH, encoding="utf-8") if l.strip()}
    v = find_violations(passages, citations, node_ids)
    dp, dn = len(v["dangling_passage"]), len(v["dangling_node"])
    print(f"citations={len(citations)} passages={len(passages)}")
    print(f"dangling citation->passage: {dp}")
    print(f"dangling citation->kg_node: {dn}")
    if strict and (dp or dn):
        print("STRICT: dangling references present -> FAIL")
        return 1
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    raise SystemExit(main(ap.parse_args().strict))
