#!/usr/bin/env python3
"""Apply the adjudication of the C2 misaligned-translation queue. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_c2_misaligned_translations.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_c2_misaligned_translations.py --apply
"""

from __future__ import annotations

import argparse
import collections
import json
import re

from scripts.data_2026_09_24_c2_misaligned_translations import DECISIONS, NOTES
from scripts.verification_2026_09_24_lib import Store, meta, set_meta, write_decisions

SLUG = "c2_misaligned_translations"
STAMP = "c2_translation_review_2026_09_24"
NOW = "2026-09-24 00:00:00+00:00"
MACHINE_SOURCE = "AI batch: claude-opus-4-6"
TRAILING_NOTE = re.compile(r"\s*\[(?:Origen|Clement) [^\[\]]*\]\s*$")
EXCERPT = 300


def excerpt(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= EXCERPT else text[:EXCERPT] + " […]"


def run(decisions_in, notes, slug: str, queue: str) -> None:
    """Apply a list of (translation_id, original_id, verdict, p) decisions."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    NOTES = notes
    store = Store()
    nodes = store.nodes
    passages = {p["passage_id"]: p for p in store.rows["passages"]}
    decisions, skipped = [], []
    counts: collections.Counter = collections.Counter()

    for tid, oid, verdict, p in decisions_in:
        t, o = nodes.get(tid), nodes.get(oid)
        if t is None:
            skipped.append((tid, "translation node absent (already withdrawn?)"))
            continue
        tm = meta(t)
        if tm.get(STAMP):
            skipped.append((tid, "already stamped"))
            continue
        # Preconditions: still the machine translation of this very original.
        if tm.get("translation_source") != MACHINE_SOURCE or tm.get("original_node_id") != oid or o is None:
            skipped.append((tid, "no longer the machine translation of " + oid))
            continue
        edge = [e for e in store.edges if e["source"] == tid and e["relation"] == "translation_of" and e["target"] == oid]
        if not edge:
            skipped.append((tid, "translation_of edge to the original is gone"))
            continue
        record = {
            "item_id": tid,
            "queue": queue,
            "claim_checked": f"The English node renders the text of {oid}.",
            "evidence": {"original_excerpt": excerpt(o.get("description")),
                         "translation_excerpt": excerpt(t.get("description")),
                         "reviewer_note": NOTES[tid]},
            "source": f"the original's own text (node {oid}, edition as recorded in its metadata) against the English node",
            "method": "read both texts in full (Contra Celsum V–VI and Hermas also checked against the openings of neighbouring sections)",
            "jev": {"question": "same_content", "probability": p},
        }
        if verdict == "misaligned":
            cits = [c for c in store.rows["citations"] if c["kg_node_id"] == tid]
            reason = f"misaligned machine translation of {oid}: {NOTES[tid]}"
            n_edges = store.remove_edges(lambda e, tid=tid: tid in (e["source"], e["target"]), reason)
            store.remove_citations(lambda c, tid=tid: c["kg_node_id"] == tid, reason)
            still_cited = {c["passage_id"] for c in store.rows["citations"]}
            orphan = {c["passage_id"] for c in cits} - still_cited
            n_pass = store.remove_passages(lambda q, orphan=orphan: q["passage_id"] in orphan, reason)
            store.remove_node(tid, reason)
            record.update(verdict="removed", change=f"node withdrawn with {n_edges} edges, {len(cits)} corpus citations, {n_pass} corpus passages (all in quarantine)")
            counts["removed"] += 1
        elif verdict == "not_a_pair":
            record.update(verdict="false_positive", change="none (vocabulary_gloss original, not a translation pair)")
            counts["not_a_pair"] += 1
            decisions.append(record)
            continue
        else:
            label = {
                "aligned_partial": "aligned_partial",
                "aligned_exceeds": "aligned_exceeds_locus",
                "aligned_strip_note": "aligned_editorial_note_removed",
                "aligned_paraphrase": "paraphrase_not_translation",
            }[verdict]
            change = [f"metadata.{STAMP} = {label}"]
            if verdict == "aligned_strip_note":
                desc = t["description"]
                m = TRAILING_NOTE.search(desc)
                if not m:
                    skipped.append((tid, "bracketed editorial note not found"))
                    continue
                note = m.group(0).strip()
                new = desc[: m.start()].rstrip()
                tm[f"{STAMP}_removed_editorial_note"] = note
                for c in store.rows["citations"]:
                    if c["kg_node_id"] == tid and c["passage_id"] in passages:
                        q = passages[c["passage_id"]]
                        if q.get("text_content") == desc:
                            q["text_content"] = new
                            change.append(f"corpus passage {q['passage_id']} text trimmed identically")
                t["description"] = new
                change.append("trailing bracketed editorial summary moved to metadata")
            if verdict == "aligned_paraphrase":
                tm["translation_type_before_2026_09_24"] = tm.get("translation_type")
                tm["translation_type"] = "machine_paraphrase"
                tm["alignment_note"] = "English synopsis of the same passage in the editor's voice; not a translation."
                change.append("translation_type machine -> machine_paraphrase")
            if verdict == "aligned_exceeds":
                tm["alignment_note"] = "Renders this passage and runs on into the following verses."
            tm[STAMP] = label
            set_meta(t, tm)
            t["updated_at"] = NOW
            record.update(verdict="false_positive" if verdict != "aligned_paraphrase" else "corrected", change="; ".join(change))
            counts[verdict] += 1
        decisions.append(record)

    summary = store.commit(slug, apply=args.apply and not args.dry_run)
    if args.apply and not args.dry_run:
        write_decisions(slug, decisions)
    print(json.dumps({"mode": "apply" if args.apply and not args.dry_run else "dry_run",
                      "counts": counts, "skipped": skipped[:10], "n_skipped": len(skipped),
                      "changes": summary}, ensure_ascii=False, indent=1))


def main() -> None:
    run(DECISIONS, NOTES, SLUG, "c2_translations_descriptions/queue_a_misaligned.csv")


if __name__ == "__main__":
    main()
