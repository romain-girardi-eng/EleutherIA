"""Part A candidate builder: every translation_of edge (passage -> passage).

Text source: node["description"] directly. Verified against data/kg/nodes.jsonl
(2026-09-24) that all 2,607 translation_of edges resolve to nodes carrying their
full text in `description` (no dependency on data/corpus/passages.jsonl for this
campaign -- the corpus file has its own passage_id namespace and is not needed
here). source/source_id and target/target_id agree on every edge (checked).

Also computes, deterministically (no Jev call):
  - byte-identical original/translation text
  - near-identical text (difflib ratio >= 0.97)
  - empty translation (or original) text
and writes them to determ_flags.jsonl, independent of the Jev queues.
"""
from __future__ import annotations

import difflib
import json
from pathlib import Path

ROOT = Path("/Users/romaingirardi/Projects/EleutherIA/data")
OUT = Path(__file__).parent
MAX_CHARS = 8000  # per side; keeps state well under the 64k-token limit


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def meta_of(n):
    m = n.get("metadata") or {}
    if isinstance(m, str):
        try:
            m = json.loads(m)
        except Exception:
            m = {}
    return m


def main() -> None:
    nodes = {}
    for n in load_jsonl(ROOT / "kg/nodes.jsonl"):
        nodes[n.get("node_id") or n.get("id")] = n

    edges = [e for e in load_jsonl(ROOT / "kg/edges.jsonl") if e.get("relation") == "translation_of"]
    print(f"translation_of edges: {len(edges)}")

    candidates = []
    determ_flags = []
    missing = 0
    for e in edges:
        eid = e.get("edge_id")
        src_id = e.get("source")  # translation
        tgt_id = e.get("target")  # original
        assert e.get("source") == e.get("source_id"), e
        assert e.get("target") == e.get("target_id"), e
        s = nodes.get(src_id)
        t = nodes.get(tgt_id)
        if s is None or t is None:
            missing += 1
            continue
        sm, tm = meta_of(s), meta_of(t)
        orig_text = (t.get("description") or "").strip()
        tr_text = (s.get("description") or "").strip()

        empty_orig = not orig_text
        empty_tr = not tr_text
        identical = bool(orig_text) and orig_text == tr_text
        ratio = None
        near_identical = False
        if orig_text and tr_text and not identical:
            ratio = difflib.SequenceMatcher(None, orig_text[:4000], tr_text[:4000]).ratio()
            near_identical = ratio >= 0.97
        if empty_orig or empty_tr or identical or near_identical:
            determ_flags.append({
                "edge_id": eid,
                "translation_id": src_id,
                "original_id": tgt_id,
                "translation_label": s.get("label"),
                "original_label": t.get("label"),
                "empty_original": empty_orig,
                "empty_translation": empty_tr,
                "byte_identical": identical,
                "near_identical": near_identical,
                "similarity_ratio": round(ratio, 4) if ratio is not None else (1.0 if identical else None),
            })

        orig_trunc = len(orig_text) > MAX_CHARS
        tr_trunc = len(tr_text) > MAX_CHARS
        candidates.append({
            "id": eid,
            "translation_id": src_id,
            "original_id": tgt_id,
            "translation_label": s.get("label"),
            "original_label": t.get("label"),
            "translation_author": sm.get("author"),
            "original_author": tm.get("author"),
            "original_language_meta": tm.get("language"),
            "translation_language_meta": sm.get("language"),
            "state": {
                "original": orig_text[:MAX_CHARS],
                "translation": tr_text[:MAX_CHARS],
            },
            "original_truncated": orig_trunc,
            "translation_truncated": tr_trunc,
        })

    print(f"missing endpoint node: {missing}")
    print(f"candidates built: {len(candidates)}")
    print(f"deterministic flags (empty/identical/near-identical): {len(determ_flags)}")

    with open(OUT / "candidates_a.jsonl", "w", encoding="utf-8") as f:
        for c in candidates:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    with open(OUT / "determ_flags_a.jsonl", "w", encoding="utf-8") as f:
        for d in determ_flags:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    questions = {
        "same_content": {
            "type": "boolean",
            "instructions": (
                "The text under `translation` renders the same passage as the text under "
                "`original` (same content, not a different passage of the same work)."
            ),
        },
        "coverage": {
            "type": "choice",
            "instructions": (
                "How much of `original` does `translation` cover? Judge the extent of content "
                "overlap, not literary quality."
            ),
            "criteria": {
                "whole": "the translation covers the whole original",
                "partial": "the translation covers only part of the original",
                "more": "the translation contains substantially more than the original",
                "not_translation": "the translation is not a translation of this original",
            },
        },
        "identical_text": {
            "type": "boolean",
            "instructions": (
                "The text under `translation` is identical (or near-verbatim identical) to the "
                "text under `original` -- i.e. no actual translation happened."
            ),
        },
        "is_english": {
            "type": "boolean",
            "instructions": "The text under `translation` is written in English.",
        },
        "is_french": {
            "type": "boolean",
            "instructions": "The text under `translation` is written in French.",
        },
    }
    with open(OUT / "questions_a.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
