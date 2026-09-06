#!/usr/bin/env python3
"""Normalize the language/role of three gold translations. Dry-run first."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.data_2026_09_05_origen_translation_identity import (  # noqa: E402
    CASES,
    MANIFESTS,
)

STAMP = "origen_translation_identity_2026_09_05"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    paths = ["kg/nodes.jsonl", "corpus/passages.jsonl", "corpus/manifest.jsonl"]
    records = {
        name: [json.loads(line) for line in (ROOT / "data" / name).read_text().splitlines()]
        for name in paths
    }
    originals = {
        name: json.dumps(rows, sort_keys=True, ensure_ascii=False)
        for name, rows in records.items()
    }
    ns = {n["id"]: n for n in records[paths[0]]}
    ps = {p["passage_id"]: p for p in records[paths[1]]}
    report = []
    for pid, nid, cid, ref in CASES:
        p = ps[pid]
        n = ns[nid]
        m = n["metadata"]
        string = isinstance(m, str)
        m = json.loads(m) if string else dict(m)
        assert (
            m["language"] == "fra" and "fr" not in str(p.get("cts_urn", "")).lower()
        )  # source declared, never guessed from content
        assert p["text_content"] and n["description"]
        m.setdefault("previous_corpus_cts_urn", p.get("cts_urn"))
        m.setdefault("previous_corpus_manifestation", p.get("work_canonical_id"))
        p.update(
            work_canonical_id=cid,
            canonical_ref=ref,
            language="fra",
            passage_role="translation",
            cts_urn=None,
        )
        # Conventional source references suffice for these ancient works;
        # do not retain an unverified machine-assigned CTS identity.
        m.update(
            {
                STAMP: True,
                "cts_urn": None,
                "canonical_ref": ref,
                "language": "fra",
                "passage_role": "translation",
                "translation_type": "published_scholarly_translation",
                "translation_source": MANIFESTS[cid]["edition"],
                "corpus_manifestation_id": cid,
                "db_passage_id": pid,
                "corpus_passage_id": pid,
                "passage_id": pid,
                "language_note": "French scholarly translation; not the Greek or Latin text.",
                "section_label": ref,
            }
        )
        if m.get("anti_determinism_target"):
            m["previous_anti_determinism_target"] = m.pop("anti_determinism_target")
        n["metadata"] = (
            json.dumps(m, ensure_ascii=False, sort_keys=True) if string else m
        )
        report.append(
            {
                "node_id": nid,
                "passage_id": pid,
                "manifestation": cid,
                "locus": ref,
                "language": "fra",
                "text_sha256": hashlib.sha256(p["text_content"].encode()).hexdigest(),
                "edition": MANIFESTS[cid]["edition"],
            }
        )
    for cid, data in MANIFESTS.items():
        if not any(m["canonical_id"] == cid for m in records[paths[2]]):
            records[paths[2]].append(
                {
                    **data,
                    "canonical_id": cid,
                    "cts_urn": "",
                    "author": "Origen",
                    "language": "fra",
                    "ingest_class": "published_translation",
                    "status": "in_corpus",
                    "passages": sum(c[2] == cid for c in CASES),
                    STAMP: True,
                }
            )
    goldpath = ROOT / "tests/eval/queries.yaml"
    gold = yaml.safe_load(goldpath.read_text())
    q = next(q for q in gold["queries"] if q["id"] == "r002")
    q["expected_manifestations"] = list(MANIFESTS)
    q["expected_passage_identities"] = {
        pid: {
            "work_canonical_id": cid,
            "canonical_ref": ref,
            "language": "fra",
            "cts_urn": "",
        }
        for pid, _, cid, ref in CASES
    }
    if args.apply and not args.dry_run:
        for name, rows in records.items():
            if json.dumps(rows, sort_keys=True, ensure_ascii=False) == originals[name]:
                continue
            path = ROOT / "data" / name
            lines = path.read_text().splitlines()
            key = {
                "kg/nodes.jsonl": "id",
                "corpus/passages.jsonl": "passage_id",
                "corpus/manifest.jsonl": "canonical_id",
            }[name]
            old = {json.loads(line)[key]: (json.loads(line), line) for line in lines}
            backup = path.with_suffix(path.suffix + ".bak-" + STAMP)
            if not backup.exists():
                shutil.copy2(path, backup)
            path.write_text(
                "\n".join(
                    old[r[key]][1]
                    if r[key] in old and old[r[key]][0] == r
                    else json.dumps(r, ensure_ascii=False, sort_keys=True)
                    for r in rows
                )
                + "\n"
            )
        goldpath.write_text(yaml.safe_dump(gold, sort_keys=False, allow_unicode=True))
        (ROOT / "data/audit/2026-09-05_origen_translation_identity.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
    print(
        json.dumps(
            {
                "status": "applied" if args.apply and not args.dry_run else "dry_run",
                "translated_passages": len(report),
                "languages": ["fra"],
            }
        )
    )


if __name__ == "__main__":
    main()
