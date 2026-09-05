#!/usr/bin/env python3
"""Restore primary editions; keep old editorial records explicitly non-citable."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from lxml import html
from pypdf import PdfReader

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.apply_2026_09_05_source_editions import (  # noqa: E402
    NS,
    ROOT,
    digest,
    digest_nfc,
    edge,
    md,
    node,
    provenance,
    read,
    set_md,
    tei_reading,
)
from scripts.data_2026_09_05_augustine_dihle_adjudication import (  # noqa: E402
    CIV_SOURCE,
    DIHLE_NODE,
    DIHLE_PAGE,
    DLA_AUTHORITY,
    DLA_EDITION,
    DLA_HASHES,
    STAMP,
)

DLA_LAT = "augustine_de_libero_arbitrio_migne_lat"
DLA_ENG = "augustine_de_libero_arbitrio_editorial_eng"
OLD_DLA_LAT = "urn_cts_latinlit_stoa0040_stoa003_lat"
OLD_DLA_ENG = "urn_cts_latinlit_stoa0040_stoa003_eng"
OLD_CIV_LAT = "urn_cts_latinlit_stoa0040_stoa001_v_xii_xiv_lat"
OLD_CIV_ENG = "urn_cts_latinlit_stoa0040_stoa001_v_xii_xiv_eng"
CIV_NOTE = "augustine_civitate_legacy_notes_lat"
CIV_ENG = "augustine_civitate_editorial_eng"
CIV_EXACT = "978fc8cb-d39e-4fd7-a690-1a2c958c634a"
CIV_EXACT_NODE = "passage_aug_civ_5_10_2"
NOW = "2026-09-05T00:00:00Z"


def read_dla():
    sections = {}
    for book, expected in DLA_HASHES.items():
        raw = (
            ROOT / f"data/corpus/sources/2026-09-05/augustine-dla-{book}.html"
        ).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected
        root = html.fromstring(raw)
        current = None
        for p in root.xpath(
            '//p[translate(@align,"abcdefghijklmnopqrstuvwxyz","ABCDEFGHIJKLMNOPQRSTUVWXYZ")="JUSTIFY"]'
        ):
            anchors = p.xpath('.//a[starts-with(@name,"LA_")]')
            if anchors:
                current = ".".join(
                    str(int(x)) for x in anchors[0].get("name").split("_")[1:]
                )
                assert current not in sections
                sections[current] = []
            if current:
                for a in p.xpath(".//a"):
                    a.drop_tree()  # locus labels and footnote links are apparatus
                sections[current].append(" ".join(p.text_content().split()))
    assert len(sections) == 170
    return {key: "\n\n".join(parts) for key, parts in sections.items()}


def dla_prov(ref):
    book = int(ref.split(".")[0])
    return {
        "source": f"https://www.augustinus.it/latino/libero_arbitrio/libero_arbitrio_{book}_libro.htm",
        "source_sha256": DLA_HASHES[book],
        "edition": DLA_EDITION,
        "work_authority": DLA_AUTHORITY,
        "source_anchor": "LA_" + "_".join(f"{int(x):03d}" for x in ref.split(".")),
        "ingested_at": NOW,
        "ingest_script": Path(__file__).name,
        "extraction_policy": "HTML paragraphs at named locus; locus enumeration and footnote links excluded; whitespace collapsed",
    }


def transform(initial):
    out = copy.deepcopy(initial)
    nodes = out["kg/nodes.jsonl"]
    edges = out["kg/edges.jsonl"]
    ps = out["corpus/passages.jsonl"]
    cs = out["corpus/citations.jsonl"]
    mans = out["corpus/manifest.jsonl"]
    lookup = {n["id"]: n for n in nodes}
    by_pid = {p["passage_id"]: p for p in ps}
    changes = []
    new_nodes = []
    new_edges = []
    sections = read_dla()
    latin = [p for p in ps if p.get("work_canonical_id") in [OLD_DLA_LAT, DLA_LAT]]
    assert len(latin) == 171 and {p["canonical_ref"] for p in latin} == set(sections)
    # IDs are preserved, including one existing duplicate of 3.4.9. Both carry
    # the same source-span identity and cannot count as two distinct witnesses.
    for p in latin:
        ref = p["canonical_ref"]
        text = sections[ref]
        p.update(
            work_canonical_id=DLA_LAT,
            text_content=text,
            cts_urn=None,
            passage_role="original",
            language="lat",
            canonical_work_id="cpl260",
            source_span_id=dla_prov(ref)["source_anchor"],
            provenance=dla_prov(ref),
            text_content_sha256=digest(text),
        )
    for n in nodes:
        if n["id"].startswith("passage_aug_dla_"):
            ref = n["id"].removeprefix("passage_aug_dla_").replace("_", ".")
            assert ref in sections
            m = md(n)
            if not m.get(STAMP):
                m["previous_cts_urn"] = m.get("cts_urn")
                m["previous_text_sha256"] = digest(n["description"])
                changes.append(n["id"])
            pid = m.get("db_passage_id") or m.get("passage_id")
            if pid not in by_pid or by_pid[pid].get("canonical_ref") != ref:
                hits = [
                    c["passage_id"]
                    for c in cs
                    if c["kg_node_id"] == n["id"]
                    and c["passage_id"] in {p["passage_id"] for p in latin}
                ]
                assert len(set(hits)) == 1, (n["id"], hits)
                pid = hits[0]
            n["description"] = sections[ref]
            m.update(
                {
                    STAMP: True,
                    "cts_urn": None,
                    "work_canonical_id": DLA_LAT,
                    "canonical_work_id": "cpl260",
                    "canonical_ref": ref,
                    "work_title": "De libero arbitrio",
                    "language": "lat",
                    "passage_role": "original",
                    "auto_generated": False,
                    "source_span_id": dla_prov(ref)["source_anchor"],
                    "provenance": dla_prov(ref),
                    "edition": DLA_EDITION,
                    "db_passage_id": pid,
                    "passage_id": pid,
                    "corpus_passage_id": pid,
                    "parity_status": "exact_edition_snapshot",
                    "text_content_sha256_nfc": digest_nfc(sections[ref]),
                    "citation_verified": True,
                    "citation_verdict": "verified",
                }
            )
            m.pop("related_corpus_passage_id", None)
            set_md(n, m)
            for c in cs:
                if c["kg_node_id"] == n["id"] and c["passage_id"] == pid:
                    c["citation_type"] = "snapshot_passage_node"
        elif n["id"].startswith("passage_aug_lib_arb_"):
            m = md(n)
            m.update(
                {
                    STAMP: True,
                    "cts_urn": None,
                    "work_canonical_id": DLA_ENG,
                    "canonical_work_id": "cpl260",
                    "passage_role": "paraphrase",
                    "citability": "discoverable_only",
                    "citation_verified": False,
                    "citation_verdict": "editorial_summary_not_primary_text",
                }
            )
            set_md(n, m)
    for p in ps:
        if p.get("work_canonical_id") in [OLD_DLA_ENG, DLA_ENG]:
            p.update(
                work_canonical_id=DLA_ENG,
                cts_urn=None,
                passage_role="paraphrase",
                language="eng",
                canonical_work_id="cpl260",
            )
    work = lookup["work_de_libero_arbitrio"]
    m = md(work)
    m.update(
        {
            STAMP: True,
            "cts_urn": None,
            "work_canonical_id": "cpl260",
            "canonical_work_id": "cpl260",
            "provenance": {
                "source": DLA_AUTHORITY,
                "ingested_at": NOW,
                "ingest_script": Path(__file__).name,
            },
            "corpus_manifestations": [DLA_LAT, DLA_ENG],
        }
    )
    set_md(work, m)

    raw = (ROOT / "data/corpus/sources/2026-09-05" / CIV_SOURCE["file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CIV_SOURCE["sha256"]
    root = ET.fromstring(raw)
    chapters = {}
    for book in root.findall('.//t:div[@subtype="book"]', NS):
        if book.get("n") not in {"5", "12", "14"}:
            continue
        for chapter in book.findall('t:div[@subtype="chapter"]', NS):
            if chapter.get("n"):
                ref = book.get("n") + "." + chapter.get("n")
                chapters[ref] = "\n\n".join(
                    tei_reading(p) for p in chapter.findall("t:p", NS)
                )
    assert len(chapters) == 81 and all(len(t) > 50 for t in chapters.values())
    prov = provenance(CIV_SOURCE)
    # Old excerpts contain apparatus, crossed chapter boundaries, wrong loci,
    # and editorial summaries. Retain them for discovery, not as quotations.
    for p in ps:
        if (
            p.get("work_canonical_id") in [OLD_CIV_LAT, CIV_NOTE]
            and p["passage_id"] != CIV_EXACT
        ):
            p.update(
                work_canonical_id=CIV_NOTE,
                cts_urn=None,
                passage_role="paraphrase",
                language="lat",
            )
        elif p.get("work_canonical_id") in [OLD_CIV_ENG, CIV_ENG]:
            p.update(
                work_canonical_id=CIV_ENG,
                cts_urn=None,
                passage_role="paraphrase",
                language="eng",
            )
    legacy_ids = {
        p["passage_id"] for p in ps if p.get("work_canonical_id") in [CIV_NOTE, CIV_ENG]
    }
    legacy_nodes = {c["kg_node_id"] for c in cs if c["passage_id"] in legacy_ids}
    for n in nodes:
        if (
            n["id"] in legacy_nodes
            and n["type"] in ["passage", "quote"]
            and n["id"] != CIV_EXACT_NODE
        ):
            m = md(n)
            m.update(
                {
                    STAMP: True,
                    "cts_urn": None,
                    "passage_role": "paraphrase",
                    "citability": "discoverable_only",
                    "source_identity_unresolved": "Legacy excerpt boundaries/apparatus are not verified; use the new Hoffmann chapter units.",
                    "citation_verified": False,
                    "citation_verdict": "requires_recollation",
                }
            )
            set_md(n, m)
    # Restore the exact paragraph cited in the observed production failure.
    chapter = root.find(
        './/t:div[@subtype="book"][@n="5"]/t:div[@subtype="chapter"][@n="10"]', NS
    )
    para = tei_reading(chapter.findall("t:p", NS)[1])
    assert para.startswith("Non ergo propterea nihil est in nostra uoluntate")
    p = by_pid[CIV_EXACT]
    p.update(
        work_canonical_id=CIV_SOURCE["manifest"],
        text_content=para,
        canonical_ref="De Civitate Dei 5.10, paragraph 2",
        cts_urn=None,
        parent_cts_urn=CIV_SOURCE["urn"] + ":5.10",
        source_span_id="5.10/p[2]",
        passage_role="original",
        language="lat",
        provenance=prov,
        text_content_sha256=digest(para),
    )
    n = lookup[CIV_EXACT_NODE]
    m = md(n)
    if not m.get(STAMP):
        changes.append(n["id"])
        m["previous_text_sha256"] = digest(n["description"])
    n["description"] = para
    n["label"] = "Augustine, De Civitate Dei 5.10, paragraph 2 (Hoffmann)"
    for k in [
        "work_id",
        "content_kind",
        "translation_source",
        "related_corpus_passage_id",
        "source_identity_unresolved",
        "citability",
    ]:
        m.pop(k, None)
    m.update(
        {
            STAMP: True,
            "cts_urn": None,
            "parent_cts_urn": CIV_SOURCE["urn"] + ":5.10",
            "source_span_id": "5.10/p[2]",
            "canonical_ref": p["canonical_ref"],
            "work_title": "De Civitate Dei",
            "work_canonical_id": CIV_SOURCE["manifest"],
            "db_passage_id": CIV_EXACT,
            "corpus_passage_id": CIV_EXACT,
            "passage_id": CIV_EXACT,
            "provenance": prov,
            "edition": CIV_SOURCE["edition"],
            "language": "lat",
            "passage_role": "original",
            "parity_status": "exact_edition_snapshot",
            "auto_generated": False,
            "text_content_sha256_nfc": digest_nfc(para),
        }
    )
    set_md(n, m)
    for c in cs:
        if c["kg_node_id"] == CIV_EXACT_NODE and c["passage_id"] == CIV_EXACT:
            c["citation_type"] = "snapshot_passage_node"
    for ref, text in chapters.items():
        nid = "passage_augustine_civ_" + ref.replace(".", "_") + "_hoffmann"
        urn = CIV_SOURCE["urn"] + ":" + ref
        pid = str(uuid.uuid5(uuid.NAMESPACE_URL, urn))
        if nid in lookup:
            continue
        new_nodes.append(
            node(
                nid,
                "passage",
                f"Augustine, De Civitate Dei {ref} (Hoffmann)",
                text,
                {
                    STAMP: True,
                    "cts_urn": urn,
                    "work_canonical_id": CIV_SOURCE["manifest"],
                    "canonical_ref": f"De Civitate Dei {ref}",
                    "author": "Augustine",
                    "author_id": "person_augustine_hippo_d430",
                    "work_title": "De Civitate Dei",
                    "language": "lat",
                    "passage_role": "original",
                    "auto_generated": False,
                    "provenance": prov,
                    "db_passage_id": pid,
                    "corpus_passage_id": pid,
                    "passage_id": pid,
                    "text_content_sha256_nfc": digest_nfc(text),
                    "parity_status": "exact_edition_snapshot",
                },
            )
        )
        new_edges.extend(
            [
                edge(nid, "part_of", "work_augustine_de_civitate_dei", prov),
                edge(nid, "authored_by", "person_augustine_hippo_d430", prov),
            ]
        )
        ps.append(
            {
                "passage_id": pid,
                "work_canonical_id": CIV_SOURCE["manifest"],
                "canonical_ref": f"De Civitate Dei {ref}",
                "cts_urn": urn,
                "sequence_number": int(ref.split(".")[0]) * 1000
                + int(ref.split(".")[1]),
                "text_content": text,
                "passage_role": "original",
                "language": "lat",
                "provenance": prov,
                "text_content_sha256": digest(text),
            }
        )
        cs.append(
            {
                "kg_node_id": nid,
                "passage_id": pid,
                "citation_type": "snapshot_passage_node",
                "confidence": 1.0,
            }
        )
        changes.append(nid)
    work = lookup["work_augustine_de_civitate_dei"]
    m = md(work)
    m.update(
        {
            STAMP: True,
            "cts_urn": "urn:cts:latinLit:stoa0040.stoa003",
            "work_canonical_id": "urn:cts:latinLit:stoa0040.stoa003",
            "corpus_manifestations": [CIV_SOURCE["manifest"]],
            "edition": CIV_SOURCE["edition"],
            "provenance": prov,
        }
    )
    set_md(work, m)

    n = lookup[DIHLE_NODE]
    m = md(n)
    if not m.get(STAMP):
        pdf = Path(m["quote_source_file"]).with_suffix(".pdf")
        raw = pdf.read_bytes()
        page = PdfReader(pdf).pages[74]
        text = re.sub(r"\u00ad\s*", "", page.extract_text())
        normalized = re.sub(r"\s+", " ", text)
        quote = m["quote_verbatim"]
        assert quote in normalized and re.search(r"\b68\b", normalized)
        m.update(
            {
                STAMP: True,
                "previous_page_range": m.get("page_range"),
                "page_range": DIHLE_PAGE,
                "quote_page": DIHLE_PAGE,
                "needs_page_verification": False,
                "citation_verified": True,
                "citation_verdict": "verified",
                "verified_reference": "Dihle 1982, printed p. 68, chapter IV opening; visually checked against PDF p. 75.",
                "page_adjudication": {
                    "printed_page": 68,
                    "pdf_page": 75,
                    "pdf_sha256": hashlib.sha256(raw).hexdigest(),
                    "review_date": NOW,
                },
            }
        )
        # Scope the claim to the checked sentence rather than keeping unrelated
        # assertions formerly tied to the invalid offset range.
        m["previous_stance"] = m.get("stance")
        m["stance"] = (
            "Dihle states that the Greeks never developed a distinct concept of will."
        )
        n["description"] = (
            "Dihle states that the Greeks never developed a distinct concept of will (The Theory of Will in Classical Antiquity, 1982, p. 68)."
        )
        set_md(n, m)
        changes.append(n["id"])
    # A KG work identity is distinct from its corpus manifestations. Normalize
    # all existing members before checking the atomic additions, so a corrected
    # City-of-God work never appears to contain Confessions or De libero arbitrio.
    roots = {
        "work_de_libero_arbitrio": "cpl260",
        "work_augustine_de_civitate_dei": "urn:cts:latinLit:stoa0040.stoa003",
    }
    memberships = {
        e["source"]: roots[e["target"]]
        for e in edges
        if e["relation"] == "part_of" and e["target"] in roots
    }
    verified_civ_ids = {
        "passage_augustine_civ_" + ref.replace(".", "_") + "_hoffmann"
        for ref in chapters
    }
    for n in nodes + new_nodes:
        canonical = memberships.get(n["id"])
        if n["id"] in verified_civ_ids:
            canonical = "urn:cts:latinLit:stoa0040.stoa003"
        if not canonical or n["type"] not in {"passage", "quote"}:
            continue
        m = md(n)
        if m.get("work_canonical_id") != canonical:
            m.setdefault("previous_work_canonical_id", m.get("work_canonical_id"))
            m["work_canonical_id"] = canonical
        if (
            canonical.endswith("stoa003")
            and n["id"] != CIV_EXACT_NODE
            and n["id"] not in verified_civ_ids
        ):
            m.update(
                {
                    STAMP: True,
                    "cts_urn": None,
                    "work_title": "De Civitate Dei",
                    "passage_role": "paraphrase",
                    "citability": "discoverable_only",
                    "source_identity_unresolved": "Legacy excerpt boundaries/apparatus are not verified; use the new Hoffmann chapter units.",
                    "citation_verified": False,
                    "citation_verdict": "requires_recollation",
                }
            )
            m.pop("work_id", None)
        set_md(n, m)
    for n in nodes + new_nodes:
        if (
            n["id"] in verified_civ_ids
            or n["id"] == CIV_EXACT_NODE
            or n["id"].startswith("passage_aug_dla_")
        ):
            m = md(n)
            expected_hash = digest_nfc(n["description"])
            if m.get("text_content_sha256_nfc") != expected_hash:
                m["text_content_sha256_nfc"] = expected_hash
                set_md(n, m)
                changes.append("nfc_hash:" + n["id"])
    for citation in cs:
        nid = citation["kg_node_id"]
        if (
            nid in verified_civ_ids
            or nid == CIV_EXACT_NODE
            or nid.startswith("passage_aug_dla_")
        ) and citation["citation_type"] == "kg_snapshot":
            citation["citation_type"] = "snapshot_passage_node"
            changes.append("citation:" + nid)
    nodes.extend(new_nodes)
    edges.extend(new_edges)
    remove = {
        OLD_DLA_LAT,
        OLD_DLA_ENG,
        OLD_CIV_LAT,
        OLD_CIV_ENG,
        DLA_LAT,
        DLA_ENG,
        CIV_NOTE,
        CIV_ENG,
        CIV_SOURCE["manifest"],
    }
    out["corpus/manifest.jsonl"] = [m for m in mans if m["canonical_id"] not in remove]
    definitions = [
        (
            DLA_LAT,
            "De libero arbitrio",
            "Augustine",
            "lat",
            DLA_EDITION,
            DLA_AUTHORITY,
            "published_edition",
        ),
        (
            DLA_ENG,
            "Research summaries on De libero arbitrio",
            "EleutherIA editorial records",
            "eng",
            "Not a published translation",
            "legacy editorial summaries",
            "editorial_research_notes",
        ),
        (
            CIV_NOTE,
            "Legacy research excerpts on De civitate Dei (not quotation evidence)",
            "EleutherIA legacy records",
            "lat",
            "Source boundaries require recollation",
            "legacy excerpts; not verified primary evidence",
            "editorial_research_notes",
        ),
        (
            CIV_ENG,
            "Research notes on De civitate Dei",
            "EleutherIA editorial records",
            "eng",
            "Not a published translation",
            "legacy editorial notes",
            "editorial_research_notes",
        ),
        (
            CIV_SOURCE["manifest"],
            "De civitate Dei (books 5, 12, 14)",
            "Augustine",
            "lat",
            CIV_SOURCE["edition"],
            CIV_SOURCE["url"],
            "published_edition",
        ),
    ]
    for cid, title, author, lang, edition, source, kind in definitions:
        out["corpus/manifest.jsonl"].append(
            {
                "canonical_id": cid,
                "title": title,
                "author": author,
                "language": lang,
                "source": source,
                "edition": edition,
                "ingest_class": kind,
                "status": "in_corpus",
                "passages": sum(p.get("work_canonical_id") == cid for p in ps),
                "cts_urn": CIV_SOURCE["urn"] if cid == CIV_SOURCE["manifest"] else "",
                STAMP: True,
            }
        )
    ids = {n["id"] for n in nodes}
    assert len(ids) == len(nodes) and all(
        e["source"] in ids and e["target"] in ids for e in edges
    )
    assert all(
        e["source"] == e["source_id"] and e["target"] == e["target_id"] for e in edges
    )
    assert all(
        v == 1
        for v in Counter(
            (e["source"], e["relation"], e["target"]) for e in edges
        ).values()
    )
    return out, {
        "changes": changes,
        "new_nodes": new_nodes,
        "new_edges": new_edges,
        "dla_primary_sections": len(sections),
        "civ_verified_chapters": len(chapters),
        "retained_non_citable_civ_records": len(legacy_ids),
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
    replay, second = transform(output)
    assert replay == output and not second["changes"]
    delta = Path("/tmp/eleutheria-augustine-adjudication-delta.json")
    delta.write_text(
        json.dumps(
            {"nodes": report["new_nodes"], "edges": report["new_edges"]},
            ensure_ascii=False,
        )
    )
    if report["new_nodes"]:
        old_lookup = {n["id"]: n for n in initial["kg/nodes.jsonl"]}
        updates = [
            n
            for n in output["kg/nodes.jsonl"]
            if n["id"] in old_lookup and n != old_lookup[n["id"]]
        ]
        updates_file = Path("/tmp/eleutheria-augustine-updated-nodes.json")
        updates_file.write_text(json.dumps(updates, ensure_ascii=False))
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/check_ingestion_rules.py"),
                "--new-only",
                str(delta),
                "--updated-nodes",
                str(updates_file),
            ],
            check=True,
            cwd=ROOT,
        )
    if args.apply and not args.dry_run:
        for name, rows in output.items():
            if initial[name] == rows:
                continue
            path = ROOT / "data" / name
            backup = path.with_suffix(path.suffix + ".bak-" + STAMP)
            if not backup.exists():
                shutil.copy2(path, backup)

            def key(r, name=name):
                if name.startswith("kg/nodes"):
                    return r["id"]
                if name.startswith("kg/edges"):
                    return r["edge_id"]
                if name.startswith("corpus/passages"):
                    return r["passage_id"]
                if name.startswith("corpus/citations"):
                    return r["passage_id"], r["kg_node_id"]
                return r["canonical_id"]

            old_rows = {key(r): r for r in initial[name]}
            old_lines = {
                key(r): line
                for r, line in zip(
                    initial[name], path.read_text().splitlines(), strict=True
                )
            }
            path.write_text(
                "\n".join(
                    old_lines[key(r)]
                    if old_rows.get(key(r)) == r
                    else json.dumps(r, ensure_ascii=False, sort_keys=True)
                    for r in rows
                )
                + "\n"
            )
        (ROOT / "data/audit/2026-09-05_augustine_dihle_adjudication.json").write_text(
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
                k: v
                for k, v in report.items()
                if k not in ["new_nodes", "new_edges", "changes"]
            }
            | {
                "status": "applied" if args.apply and not args.dry_run else "dry_run",
                "changes": len(report["changes"]),
                "idempotent": True,
            }
        )
    )


if __name__ == "__main__":
    main()
