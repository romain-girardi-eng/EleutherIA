#!/usr/bin/env python3
"""Repair the "&#45;" artefacts of Justin's Dialogue against the Archambault TEI. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_justin_tryph_entities.py --tei PATH --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_justin_tryph_entities.py --tei PATH --apply

PATH is a local copy of tlg0645.tlg003.perseus-grc2.xml (First1KGreek).
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from xml.etree import ElementTree as ET

from scripts.data_2026_09_24_justin_tryph_entities import ENTITY, LOCUS_FIXES
from scripts.verification_2026_09_24_lib import Store, meta, set_meta, write_decisions

SLUG = "justin_tryph_entities"
STAMP = "justin_tryph_entities_2026_09_24"
NOW = "2026-09-24 00:00:00+00:00"
TEI = "{http://www.tei-c.org/ns/1.0}"


def squeeze(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text or ""))


def sections(path: str) -> dict[str, str]:
    root = ET.parse(path).getroot()
    out = {}
    for ch in root.iter(TEI + "div"):
        if ch.get("subtype") == "chapter":
            for s in ch.findall(TEI + "div"):
                if s.get("subtype") == "section":
                    out[f"{ch.get('n')}.{s.get('n')}"] = "".join(s.itertext())
    return out


def fix(text: str) -> str:
    return re.sub(r"\s*" + re.escape(ENTITY) + r"\s*", "-", text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tei", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sec = sections(args.tei)
    store = Store()
    decisions, skipped = [], []
    for node in store.rows["nodes"]:
        nid = node["id"]
        desc = node.get("description") or ""
        if ENTITY not in desc and nid not in LOCUS_FIXES:
            continue
        data = meta(node)
        if data.get(STAMP):
            continue
        ref = (data.get("cts_urn") or "").rsplit(":", 1)[-1]
        change = []
        if nid in LOCUS_FIXES:
            old, new = LOCUS_FIXES[nid]
            if ref != old:
                skipped.append((nid, "locus precondition failed"))
                continue
            ref = new
        tei = sec.get(ref)
        new_desc = fix(desc)
        if tei is None or squeeze(new_desc) != squeeze(tei):
            skipped.append((nid, "text does not equal TEI section " + ref))
            continue
        if new_desc != desc:
            node["description"] = new_desc
            change.append(f"{desc.count(ENTITY)} × '&#45;' -> '-'")
        if nid in LOCUS_FIXES:
            old, new = LOCUS_FIXES[nid]
            data["previous_cts_urn"] = data["cts_urn"]
            data["cts_urn"] = data["cts_urn"][: -len(old)] + new
            data["canonical_ref"] = new
            change.append(f"locus {old} -> {new}")
        data[STAMP] = True
        set_meta(node, data)
        node["updated_at"] = NOW
        decisions.append({
            "item_id": nid, "queue": "c1_passage_concepts/queue_quality_flags.csv (pattern extended)",
            "claim_checked": "The stored Greek equals the edition's text of this section.",
            "verdict": "corrected", "evidence": f"TEI section {ref} equals the repaired text (whitespace-insensitive)",
            "source": "Archambault 1909, Dialogue avec Tryphon (Perseus/First1KGreek tlg0645.tlg003.perseus-grc2), section " + ref,
            "method": "programmatic character comparison against the TEI section of the node's own locus",
            "jev": "c1 quality flag p=0.93 on 27.3", "change": "; ".join(change),
        })
    n_pass = 0
    for p in store.rows["passages"]:
        text = p.get("text_content") or ""
        if ENTITY not in text:
            continue
        ref = (p.get("cts_urn") or "").rsplit(":", 1)[-1]
        new = fix(text)
        if ref in sec and squeeze(new) == squeeze(sec[ref]):
            p["text_content"] = new
            n_pass += 1
        else:
            skipped.append((p["passage_id"], "corpus text does not equal TEI " + ref))
    summary = store.commit(SLUG, apply=args.apply and not args.dry_run)
    if args.apply and not args.dry_run:
        write_decisions(SLUG, decisions)
    print(json.dumps({"nodes": len(decisions), "corpus_passages": n_pass, "skipped": skipped, "changes": summary}, indent=1))


if __name__ == "__main__":
    main()
