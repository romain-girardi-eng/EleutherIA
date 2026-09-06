#!/usr/bin/env python3
"""Replayable, hash-bound source repair. Dry-run by default; --apply writes."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import unicodedata
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_2026_09_05_source_editions import (  # noqa: E402
    EXCLUDED_TEI,
    SOURCES,
    STAMP,
)

NS = {"t": "http://www.tei-c.org/ns/1.0"}
NOW = "2026-09-05T00:00:00Z"


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def md(n):
    value = n.get("metadata") or {}
    return json.loads(value) if isinstance(value, str) else dict(value)


def set_md(n, data):
    n["metadata"] = (
        json.dumps(data, ensure_ascii=False, sort_keys=True)
        if isinstance(n.get("metadata"), str)
        else data
    )


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def digest_nfc(text):
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode()).hexdigest()


def tei_reading(element):
    """Only whitespace is normalized; characters come from the edited TEI body."""

    def walk(e):
        parts = [e.text or ""]
        for child in e:
            if child.tag.rsplit("}", 1)[-1] not in EXCLUDED_TEI:
                parts.append(walk(child))
            parts.append(child.tail or "")
        return "".join(parts)

    return " ".join(walk(element).split())


def load_source(name):
    source = SOURCES[name]
    path = ROOT / "data/corpus/sources/2026-09-05" / source["file"]
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source["sha256"], (
        f"Unexpected source bytes: {path}"
    )
    root = ET.fromstring(raw)
    body = root.find(".//t:body", NS)
    assert root.find(f'.//t:div[@n="{source["urn"]}"]', NS) is not None or (
        body is not None
        and body.get("{http://www.w3.org/XML/1998/namespace}base") == source["urn"]
    )
    return root


def provenance(source):
    return {
        "source": source["url"],
        "source_sha256": source["sha256"],
        "edition": source["edition"],
        "license": source["license"],
        "ingested_at": NOW,
        "ingest_script": Path(__file__).name,
        "extraction_policy": "edited TEI body; notes, heads and deleted readings excluded; whitespace collapsed",
    }


def node(nid, typ, label, description, metadata):
    return {
        "id": nid,
        "node_id": nid,
        "type": typ,
        "label": label,
        "description": description,
        "period": None,
        "school": None,
        "role": None,
        "alternative_names": "[]",
        "created_at": NOW,
        "updated_at": NOW,
        "metadata": metadata,
    }


def edge(src, rel, target, prov):
    eid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{STAMP}:{src}:{rel}:{target}"))
    return {
        "edge_id": eid,
        "source": src,
        "source_id": src,
        "target": target,
        "target_id": target,
        "relation": rel,
        "weight": 1.0,
        "created_at": NOW,
        "metadata": {"provenance": prov},
    }


def transform(files):
    files = copy.deepcopy(files)
    nodes, edges, passages, citations, manifests = (
        files[k]
        for k in [
            "kg/nodes.jsonl",
            "kg/edges.jsonl",
            "corpus/passages.jsonl",
            "corpus/citations.jsonl",
            "corpus/manifest.jsonl",
        ]
    )
    lookup = {n["id"]: n for n in nodes}
    changed = []
    new_nodes, new_edges = [], []
    source = SOURCES["cicero"]
    sections = load_source("cicero").findall(".//t:body/t:div/t:div", NS)
    assert {e.get("n") for e in sections} == {str(i) for i in range(1, 49)}
    corpus = [p for p in passages if p.get("work_canonical_id") == source["manifest"]]
    assert len(corpus) == 48
    by_ref = {str(p["canonical_ref"]).removeprefix("Fat. "): p for p in corpus}
    assert set(by_ref) == {str(i) for i in range(1, 49)}
    for section in sections:
        ref = section.get("n")
        p = by_ref[ref]
        n = lookup[f"passage_cic_fat_{ref}"]
        m = md(n)
        text = tei_reading(section)
        assert len(text) > 30
        urn = f"{source['urn']}:{ref}"
        if m.get(STAMP) and p["text_content"] == text and n["description"] == text:
            continue
        assert (
            m.get("work_title") == "De Fato"
            and str(m.get("canonical_ref")) == f"Fat. {ref}"
        )
        m["previous_text_sha256"] = digest(n["description"])
        m["previous_cts_urn"] = m.get("cts_urn")
        m["previous_related_corpus_passage_id"] = m.pop(
            "related_corpus_passage_id", None
        )
        for key in [
            "edition_identity_status",
            "parity_reason",
            "needs_page_verification",
        ]:
            m.pop(key, None)
        m.update(
            {
                STAMP: True,
                "provenance": provenance(source),
                "cts_urn": urn,
                "edition_identity_status": "verified_perseus_tei_sourceDesc",
                "edition": source["edition"],
                "language": "lat",
                "passage_role": "original",
                "passage_id": p["passage_id"],
                "db_passage_id": p["passage_id"],
                "corpus_passage_id": p["passage_id"],
                "parity_status": "exact_tei_snapshot",
                "citation_type": "snapshot_passage_node",
                "primary_text_status": "critical_edition_transcription",
                "auto_generated": False,
                "text_content_sha256_nfc": digest_nfc(text),
                "citable_as_primary": True,
            }
        )
        set_md(n, m)
        n["description"] = text
        n["updated_at"] = NOW
        p.update(
            {
                "text_content": text,
                "cts_urn": urn,
                "passage_role": "original",
                "language": "lat",
                "edition_identity_status": "verified_perseus_tei_sourceDesc",
                "provenance": provenance(source),
                "text_content_sha256": digest(text),
            }
        )
        hits = [c for c in citations if c.get("kg_node_id") == n["id"]]
        assert len(hits) == 1 and hits[0]["passage_id"] == p["passage_id"]
        hits[0].update(citation_type="snapshot_passage_node", confidence=1.0)
        changed.append(n["id"])
    manifest = next(m for m in manifests if m["canonical_id"] == source["manifest"])
    manifest.update(
        {
            "cts_urn": source["urn"],
            "source": source["url"],
            "edition": source["edition"],
            "edition_status": "verified_perseus_tei_sourceDesc",
            "ingest_class": "perseus_critical_edition",
            "provenance": provenance(source),
            "license": source["license"],
        }
    )

    # Add the missing Romans work and a single chapter-9 evidence unit. No
    # unrelated chapters are presented as ingested; chapter 1.1 only proves author.
    source = SOURCES["romans"]
    wid = "work_pauline_epistle_romans"
    nid = "passage_paul_romans_9"
    root = load_source("romans")
    chapter = root.find('.//t:div[@subtype="chapter"][@n="9"]', NS)
    assert chapter is not None
    verses = chapter.findall('t:div[@subtype="verse"]', NS)
    assert [v.get("n") for v in verses] == [str(i) for i in range(1, 34)]
    text = "\n\n".join(tei_reading(v) for v in verses)
    urn = source["urn"] + ":9"
    pid = str(uuid.uuid5(uuid.NAMESPACE_URL, urn))
    prov = provenance(source)
    if wid not in lookup:
        assert not any(
            md(n).get("cts_urn") == "urn:cts:greekLit:tlg0031.tlg006" for n in nodes
        )
        new_nodes.append(
            node(
                wid,
                "work",
                "Epistle to the Romans",
                "Paul’s Epistle to the Romans. The corpus contains chapter 9 from the Westcott–Hort Greek text in the Perseus Digital Library; coverage is explicitly partial.",
                {
                    "cts_urn": "urn:cts:greekLit:tlg0031.tlg006",
                    "work_canonical_id": "urn:cts:greekLit:tlg0031.tlg006",
                    "author": "Paul the Apostle",
                    "author_id": "person_paul_apostle",
                    "authorship_locus": "Romans 1.1 in the pinned source",
                    "provenance": prov,
                    "corpus_coverage": "chapter 9 only",
                    STAMP: True,
                },
            )
        )
        new_edges.append(edge(wid, "authored_by", "person_paul_apostle", prov))
    if nid not in lookup:
        new_nodes.append(
            node(
                nid,
                "passage",
                "Paul, Romans 9 (Westcott–Hort; Perseus)",
                text,
                {
                    "cts_urn": urn,
                    "canonical_ref": "Romans 9",
                    "work_canonical_id": source["manifest"],
                    "author": "Paul the Apostle",
                    "author_id": "person_paul_apostle",
                    "work_title": "Epistle to the Romans",
                    "language": "grc",
                    "passage_role": "original",
                    "provenance": prov,
                    "auto_generated": False,
                    "passage_id": pid,
                    "corpus_passage_id": pid,
                    "db_passage_id": pid,
                    "parity_status": "exact_tei_snapshot",
                    "text_content_sha256_nfc": digest_nfc(text),
                    STAMP: True,
                },
            )
        )
        new_edges.extend(
            [
                edge(nid, "part_of", wid, prov),
                edge(nid, "authored_by", "person_paul_apostle", prov),
            ]
        )
        passages.append(
            {
                "passage_id": pid,
                "work_canonical_id": source["manifest"],
                "canonical_ref": "Romans 9",
                "cts_urn": urn,
                "sequence_number": 9,
                "text_content": text,
                "passage_role": "original",
                "language": "grc",
                "provenance": prov,
                "text_content_sha256": digest(text),
            }
        )
        citations.append(
            {
                "kg_node_id": nid,
                "passage_id": pid,
                "citation_type": "snapshot_passage_node",
                "confidence": 1.0,
            }
        )
        manifests.append(
            {
                "canonical_id": source["manifest"],
                "cts_urn": source["urn"],
                "title": "Epistle to the Romans",
                "author": "Paul the Apostle",
                "language": "grc",
                "source": source["url"],
                "edition": source["edition"],
                "passages": 1,
                "status": "in_corpus",
                "coverage": "chapter 9 only",
                "ingest_class": "perseus_critical_edition",
                "license": source["license"],
                "provenance": prov,
            }
        )
        changed.append(nid)
    exact_ids = {f"passage_cic_fat_{i}" for i in range(1, 49)} | {
        "passage_paul_romans_9"
    }
    for citation in citations:
        if (
            citation["kg_node_id"] in exact_ids
            and citation["citation_type"] == "kg_snapshot"
        ):
            citation["citation_type"] = "snapshot_passage_node"
            changed.append("citation:" + citation["kg_node_id"])
    nodes.extend(new_nodes)
    edges.extend(new_edges)
    ids = {n["id"] for n in nodes}
    assert len(ids) == len(nodes)
    assert all(
        e["source"] == e["source_id"] and e["target"] == e["target_id"] for e in edges
    )
    assert all(
        e["source"] in ids and e["target"] in ids and e["source"] != e["target"]
        for e in edges
    )
    assert all(
        v == 1
        for v in Counter(
            (e["source"], e["relation"], e["target"]) for e in edges
        ).values()
    )
    assert len({p["passage_id"] for p in passages}) == len(passages)
    return files, {
        "changed": changed,
        "new_nodes": new_nodes,
        "new_edges": new_edges,
        "romans_passage_id": pid,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    names = [
        "kg/nodes.jsonl",
        "kg/edges.jsonl",
        "corpus/passages.jsonl",
        "corpus/citations.jsonl",
        "corpus/manifest.jsonl",
    ]
    initial = {name: read(ROOT / "data" / name) for name in names}
    output, report = transform(initial)
    replay, replayed = transform(output)
    assert replay == output and not replayed["changed"]
    delta_path = Path("/tmp/eleutheria-source-editions-delta.json")
    delta_path.write_text(
        json.dumps(
            {"nodes": report["new_nodes"], "edges": report["new_edges"]},
            ensure_ascii=False,
        )
    )
    if report["new_nodes"]:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/check_ingestion_rules.py"),
                "--new-only",
                str(delta_path),
            ],
            check=True,
            cwd=ROOT,
        )
    if args.apply and not args.dry_run:
        for name, rows in output.items():
            if rows == initial[name]:
                continue
            path = ROOT / "data" / name
            backup = path.with_suffix(path.suffix + ".bak-" + STAMP)
            if not backup.exists():
                shutil.copy2(path, backup)
            # Preserve untouched JSONL bytes so the review contains only this delta.
            keys = {
                "kg/nodes.jsonl": lambda r: r["id"],
                "kg/edges.jsonl": lambda r: r["edge_id"],
                "corpus/passages.jsonl": lambda r: r["passage_id"],
                "corpus/citations.jsonl": lambda r: (r["passage_id"], r["kg_node_id"]),
                "corpus/manifest.jsonl": lambda r: r["canonical_id"],
            }
            key = keys[name]
            old_lines = {
                key(r): line
                for r, line in zip(
                    initial[name], path.read_text().splitlines(), strict=True
                )
            }
            old_rows = {key(r): r for r in initial[name]}
            lines = [
                old_lines[key(r)]
                if old_rows.get(key(r)) == r
                else json.dumps(r, ensure_ascii=False, sort_keys=True)
                for r in rows
            ]
            path.write_text("\n".join(lines) + "\n")
        audit = ROOT / "data/audit/2026-09-05_source_editions_applied.json"
        audit.write_text(
            json.dumps(
                {
                    k: v
                    for k, v in report.items()
                    if k not in ["new_nodes", "new_edges"]
                },
                indent=2,
            )
            + "\n"
        )
    print(
        json.dumps(
            {
                "status": "applied" if args.apply and not args.dry_run else "dry_run",
                "changed_count": len(report["changed"]),
                "romans_passage_id": report["romans_passage_id"],
                "idempotent": True,
            }
        )
    )


if __name__ == "__main__":
    main()
