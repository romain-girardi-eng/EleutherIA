"""Ingest Chrysippus SVF II (Fragmenta Logica et Physica) fragments from First1KGreek TEI.

Source TEI : OpenGreekAndLatin/First1KGreek `tlg1264.tlg001.1st1K-grc1.xml` (CC BY-SA 4.0),
re-encoded from Hans von Arnim, *Stoicorum Veterum Fragmenta*, vol. II (Teubner, Leipzig 1903).

Why ? The KG had a single empty work-shell `work_chrysippus_svf_ii` (auto-generated,
`needs_edition_metadata=true`) with **zero** passage children — yet Chrysippus is the
keystone Stoic for the article's provenance test against Carneadean anti-fatalism.
SVF II §§913-1000 are the core εἱμαρμένη / fate fragments (Bobzien 1998 ch. 4-5).

Strategy :
  1. Default ingest = fragments **913-1000** (88 fragments, anti-fatalist core).
  2. Each fragment → `passage_chrysippus_svf_ii_{N}` node (passage_role=original,
     period=Hellenistic, language=greek_ancient, full TEI provenance metadata).
  3. Edges : `part_of → work_chrysippus_svf_ii` + `authored_by → person_chrysippus_280_206bce_i9j0k1l2`.
  4. Enrich `work_chrysippus_svf_ii` with bibliographic edition metadata (von Arnim 1903 +
     OGL TEI source).

Pattern : mirrors `scripts/ingest_eusebius_pe6_first1kgreek.py` (commit 309cbfb7).

Idempotent : re-runs skip already-ingested fragments.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from lxml import etree

# -----------------------------------------------------------------------------
# Paths and constants
# -----------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
KG_ROOT = REPO_ROOT / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"

TEI_LOCAL = REPO_ROOT / "data/scholarly_sources/ocr/svf_chrysippus/svf_ii_tei.xml"
TEI_URL = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/"
    "data/tlg1264/tlg001/tlg1264.tlg001.1st1K-grc1.xml"
)
TEI_NS = "{http://www.tei-c.org/ns/1.0}"
NS_MAP = {"t": "http://www.tei-c.org/ns/1.0"}

CTS_URN_BASE = "urn:cts:greekLit:tlg1264.tlg001.1st1K-grc1"
WORK_ID = "work_chrysippus_svf_ii"
PERSON_ID = "person_chrysippus_280_206bce_i9j0k1l2"
BIBTEX_KEY = "von-arnim-1903-svf-ii"

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "chrysippus_svf_ii_ingestion_2026-05-16"
SOURCE_TAG = "OpenGreekAndLatin/First1KGreek (TEI re-encoding of von Arnim 1903)"

# Anti-fatalist / εἱμαρμένη / determinism core (Bobzien 1998 ch. 4-5).
DEFAULT_FRAGMENT_RANGE = list(range(913, 1001))


# -----------------------------------------------------------------------------
# Public API (tested)
# -----------------------------------------------------------------------------


def fragment_node_id(n: int | str) -> str:
    """Canonical node id for an SVF II fragment.

    Accepts integers (913) or strings (1, 1a, 1b) — letter suffixes preserved verbatim.
    """
    return f"passage_chrysippus_svf_ii_{n}"


def extract_fragments_from_tei(path: Path) -> list[dict[str, Any]]:
    """Parse a TEI XML and return [{number, text}] for every `div[@subtype="fragment"]`.

    Text is the verbatim concatenation of every `<p>` inside the fragment div
    (whitespace-normalized — newlines collapsed to single spaces). Fragment numbers
    are kept as strings to preserve letter suffixes (e.g. `1a`, `1b`).
    """
    tree = etree.parse(str(path))
    root = tree.getroot()
    out: list[dict[str, Any]] = []
    for div in root.findall(".//t:div[@type='textpart']", NS_MAP):
        if div.get("subtype") != "fragment":
            continue
        n = div.get("n")
        if not n:
            continue
        # Verbatim concatenation of <p> children
        parts: list[str] = []
        for p in div.findall(".//t:p", NS_MAP):
            text = etree.tostring(p, method="text", encoding="unicode")
            parts.append(text)
        joined = " ".join(" ".join(parts).split())
        out.append({"number": n, "text": joined})
    return out


# -----------------------------------------------------------------------------
# Node / edge factories
# -----------------------------------------------------------------------------


def build_passage_node(number: str, greek_text: str) -> dict[str, Any]:
    pid = fragment_node_id(number)
    metadata: dict[str, Any] = {
        "attestation_type": "fragment_collection",
        "author": "Chrysippus of Soli",
        "canonical_ref": f"SVF II.{number}",
        "char_length": len(greek_text),
        "word_count": len(greek_text.split()),
        "cts_urn": f"{CTS_URN_BASE}:{number}",
        "language": "grc",
        "passage_role": "original",
        "school": "Stoic",
        "work_canonical_id": "tlg1264.tlg001.1st1K-grc1",
        "work_title": "Stoicorum Veterum Fragmenta II — Fragmenta Logica et Physica",
        "fragment_number": number,
        "fragment_collection": "SVF",
        "fragment_volume": "II",
        "edition": "Hans von Arnim, Stoicorum Veterum Fragmenta II (Teubner, Leipzig 1903)",
        "bibtex_key": BIBTEX_KEY,
        "source_tei": "OpenGreekAndLatin/First1KGreek tlg1264.tlg001.1st1K-grc1.xml",
        "source_tei_url": TEI_URL,
        "source": SOURCE_TAG,
        "license": "CC BY-SA 4.0 (OGL re-encoding)",
        "created_by": CREATED_BY,
        "contains_greek_to_verify": False,  # canonical TEI source, not OCR
        "period": "Hellenistic",
        "fragmented_philosopher": "Chrysippus",
        "fragmented_philosopher_node_id": PERSON_ID,
    }
    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Chrysippus, SVF II.{number}",
        "description": greek_text,
        "alternative_names": "[]",
        "period": "Hellenistic",
        "role": None,
        "school": "Stoic",
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def build_edge(source: str, target: str, relation: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    md = metadata or {}
    md.setdefault("created_by", CREATED_BY)
    return {
        "edge_id": str(uuid4()),
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "relation": relation,
        "weight": 1.0,
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP,
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write to data/kg/{nodes,edges}.jsonl. Default = dry-run preview.",
    )
    parser.add_argument(
        "--range",
        type=str,
        default=f"{DEFAULT_FRAGMENT_RANGE[0]}-{DEFAULT_FRAGMENT_RANGE[-1]}",
        help="Inclusive integer range of SVF II fragment numbers to ingest (e.g. 913-1000). "
             "Letter-suffixed fragments (1a, 1b) are included if their integer base is in range.",
    )
    args = parser.parse_args()

    # Parse range
    try:
        lo_str, hi_str = args.range.split("-", 1)
        lo, hi = int(lo_str), int(hi_str)
    except ValueError:
        print(f"FATAL: --range must be in form N-M (got: {args.range})")
        return 2
    target_ints = set(range(lo, hi + 1))

    print(f"== Chrysippus SVF II ingestion (range {lo}-{hi}) — commit={args.commit} ==")

    if not TEI_LOCAL.exists():
        print(f"FATAL: TEI file missing at {TEI_LOCAL}. Download with:")
        print(f"  curl -sL -o {TEI_LOCAL} {TEI_URL}")
        return 2

    # Phase 1 : parse TEI
    print("\n== PHASE 1 : PARSE TEI ==")
    fragments = extract_fragments_from_tei(TEI_LOCAL)
    print(f"  Total fragments in TEI: {len(fragments)}")

    # Filter to target range (including letter suffixes whose integer base is in range)
    def in_range(n: str) -> bool:
        digits = "".join(c for c in n if c.isdigit())
        if not digits:
            return False
        return int(digits) in target_ints

    target_fragments = [f for f in fragments if in_range(f["number"])]
    print(f"  In target range ({lo}-{hi}): {len(target_fragments)}")

    # Phase 2 : load current KG
    print("\n== PHASE 2 : LOAD CURRENT KG ==")
    nodes = [json.loads(line) for line in NODES_PATH.read_text().splitlines() if line.strip()]
    edges = [json.loads(line) for line in EDGES_PATH.read_text().splitlines() if line.strip()]
    print(f"  Nodes loaded : {len(nodes)}")
    print(f"  Edges loaded : {len(edges)}")
    node_ids = {n["id"] for n in nodes}

    if WORK_ID not in node_ids:
        print(f"FATAL: work node {WORK_ID} missing — abort")
        return 1
    if PERSON_ID not in node_ids:
        print(f"FATAL: person node {PERSON_ID} missing — abort")
        return 1

    existing_part_of = {
        (e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target"))
        for e in edges
        if e.get("relation") == "part_of"
    }
    existing_authored = {
        (e.get("source_id") or e.get("source"), e.get("target_id") or e.get("target"))
        for e in edges
        if e.get("relation") == "authored_by"
    }

    # Phase 3 : build new nodes + edges
    print("\n== PHASE 3 : BUILD PASSAGE NODES + EDGES ==")
    new_nodes: list[dict[str, Any]] = []
    new_edges: list[dict[str, Any]] = []
    skipped_existing = 0
    skipped_empty = 0
    for frag in target_fragments:
        n = frag["number"]
        text = frag["text"]
        if not text.strip():
            skipped_empty += 1
            continue
        pid = fragment_node_id(n)
        if pid in node_ids:
            skipped_existing += 1
            continue
        new_nodes.append(build_passage_node(n, text))
        node_ids.add(pid)
        if (pid, WORK_ID) not in existing_part_of:
            new_edges.append(build_edge(pid, WORK_ID, "part_of", {"auto_generated": True}))
            existing_part_of.add((pid, WORK_ID))
        if (pid, PERSON_ID) not in existing_authored:
            new_edges.append(
                build_edge(
                    pid,
                    PERSON_ID,
                    "authored_by",
                    {"auto_generated": True, "propagated_from_work": True},
                )
            )
            existing_authored.add((pid, PERSON_ID))

    print(f"  New passage nodes : {len(new_nodes)}")
    print(f"  New edges         : {len(new_edges)}")
    print(f"  Skipped (already in KG) : {skipped_existing}")
    print(f"  Skipped (empty TEI text): {skipped_empty}")

    # Sample preview
    if new_nodes:
        sample = new_nodes[0]
        sample_md = json.loads(sample["metadata"])
        print(f"\n  Sample node: {sample['id']}")
        print(f"    label   : {sample['label']}")
        print(f"    cts_urn : {sample_md['cts_urn']}")
        print(f"    chars   : {sample_md['char_length']}")
        print(f"    text[:120]: {sample['description'][:120]}")

    # Phase 4 : enrich work node
    print("\n== PHASE 4 : ENRICH WORK NODE METADATA ==")
    work_updated = False
    for i, n in enumerate(nodes):
        if n["id"] != WORK_ID:
            continue
        md_raw = n.get("metadata") or "{}"
        md = json.loads(md_raw) if isinstance(md_raw, str) else md_raw
        if "source_tei" not in md or md.get("needs_edition_metadata"):
            md["source_tei"] = "OpenGreekAndLatin/First1KGreek tlg1264.tlg001.1st1K-grc1.xml"
            md["source_tei_url"] = TEI_URL
            md["edition"] = (
                "Hans von Arnim, Stoicorum Veterum Fragmenta II — "
                "Fragmenta Logica et Physica (Teubner, Leipzig 1903)"
            )
            md["bibtex_key"] = BIBTEX_KEY
            md["license"] = "CC BY-SA 4.0 (OGL re-encoding)"
            md["cts_urn"] = CTS_URN_BASE
            md.pop("needs_edition_metadata", None)
            md["enriched_by"] = CREATED_BY
            md["enriched_at"] = TIMESTAMP
            n["metadata"] = json.dumps(md, ensure_ascii=False)
            n["updated_at"] = TIMESTAMP
            work_updated = True
            print(f"  Enriched: {WORK_ID}")
        else:
            print(f"  Already enriched: {WORK_ID}")
        break

    # Phase 5 : commit or dry-run
    print("\n== PHASE 5 : COMMIT ==")
    if not args.commit:
        print("  DRY-RUN — no files written. Pass --commit to persist.")
        return 0

    # Append-mode write to avoid rewriting the huge files
    with NODES_PATH.open("a", encoding="utf-8") as f:
        for n in new_nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("a", encoding="utf-8") as f:
        for e in new_edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"  Appended {len(new_nodes)} nodes to {NODES_PATH}")
    print(f"  Appended {len(new_edges)} edges to {EDGES_PATH}")

    # Work-node enrichment requires a full rewrite (in-place mutation).
    if work_updated:
        with NODES_PATH.open("w", encoding="utf-8") as f:
            for n in nodes:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")
            for n in new_nodes:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")
        print(f"  Rewrote {NODES_PATH} (work-node enrichment merged)")

    print("\n== CHRYSIPPUS SVF II INGESTION COMPLETE ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
