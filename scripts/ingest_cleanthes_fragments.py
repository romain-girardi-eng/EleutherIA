"""Ingest Cleanthes' Hymn to Zeus + SVF I selected fragments from First1KGreek TEI.

Source TEI : OpenGreekAndLatin/First1KGreek `tlg1269.tlg002.1st1K-grc1.xml` (CC BY-SA 4.0),
re-encoded from Hans von Arnim, *Stoicorum Veterum Fragmenta*, vol. I (Teubner, Leipzig 1903) —
section "5. Cleanthis Assii fragmenta et apophthegmata" (frag. 463-619).

Why ? The KG had a single empty work-shell `work_cleanthes_hymn_to_zeus` and 1 lone argument
node with **zero** passage children — yet Cleanthes is the key transitional Stoic between
Zeno and Chrysippus, and his Hymn to Zeus is the most complete extant Stoic theological poem.
SVF I.486-619 also preserves fate / providence / πεπρωμένη / ἀνάγκη testimonia
(Aetius, Cicero, Stobaeus, Philo) directly relevant to the article's provenance test
against Carneadean anti-fatalism.

Strategy :
  1. Hymn to Zeus (SVF I.537, transmitted by Stobaeus Ecl. I.1.12) :
     - 1 "Hymn complete" passage = full 39-line poem
     - 39 line-level sub-passages (`passage_cleanthes_hymn_zeus_line_N`) for line-precise
       citation downstream
  2. SVF I selected anti-fatalist / theology fragments (default = 11 fate-relevant entries:
     489, 509, 511, 527, 532, 536, 548, 549, 551, 555, 579) :
     - 1 passage per fragment (`passage_cleanthes_svf_i_N`)
  3. Edges : every passage gets `part_of → work_*` + `authored_by → person_cleanthes_assos_330_230bce`.
     Hymn lines also get `part_of → passage_cleanthes_hymn_zeus_complete`.
  4. New work-shell `work_cleanthes_svf_i_fragments` is created (mirrors `work_chrysippus_svf_ii`).
  5. Enrich `work_cleanthes_hymn_to_zeus` with full bibliographic metadata.

Pattern : mirrors `scripts/ingest_chrysippus_svf_first1kgreek.py` (commits cca8141a + de108e0e).

Idempotent : re-runs skip already-ingested nodes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import UTC, datetime
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

TEI_LOCAL = REPO_ROOT / "data/scholarly_sources/ocr/svf_cleanthes/svf_i_cleanthes_tei.xml"
TEI_URL = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/"
    "data/tlg1269/tlg002/tlg1269.tlg002.1st1K-grc1.xml"
)
NS_MAP = {"t": "http://www.tei-c.org/ns/1.0"}

CTS_URN_BASE = "urn:cts:greekLit:tlg1269.tlg002.1st1K-grc1"
HYMN_FRAGMENT_NUMBER = "537"
HYMN_WORK_ID = "work_cleanthes_hymn_to_zeus"
SVF_WORK_ID = "work_cleanthes_svf_i_fragments"
PERSON_ID = "person_cleanthes_assos_330_230bce"
BIBTEX_KEY = "von-arnim-1903-svf-i"

TIMESTAMP = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "cleanthes_fragments_ingestion_2026-05-16"
SOURCE_TAG = "OpenGreekAndLatin/First1KGreek (TEI re-encoding of von Arnim 1903, SVF I)"

# Default SVF I fragments to ingest besides the Hymn: anti-fatalist / theology core
# (per T1 audit, Bobzien 1998 ch. 1, Long 1971, Algra 1995).
# These are the fragments that contain εἱμαρμέν / πρόνοια / fatum / providentia / πεπρωμέν / ἀνάγκη.
DEFAULT_SVF_FRAGMENTS = ["489", "509", "511", "527", "532", "536", "548", "549", "551", "555", "579"]


# -----------------------------------------------------------------------------
# TEI fetch
# -----------------------------------------------------------------------------


def ensure_tei_local() -> Path:
    """Return the local TEI path, downloading from OGL if missing or truncated."""
    if TEI_LOCAL.exists() and TEI_LOCAL.stat().st_size > 50_000:
        return TEI_LOCAL
    TEI_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Fetching TEI from {TEI_URL}")
    with urllib.request.urlopen(TEI_URL, timeout=60) as resp:
        data = resp.read()
    TEI_LOCAL.write_bytes(data)
    print(f"  Saved {len(data):,} bytes to {TEI_LOCAL}")
    return TEI_LOCAL


# -----------------------------------------------------------------------------
# Public API (tested)
# -----------------------------------------------------------------------------


def fragment_node_id(n: int | str) -> str:
    """Canonical node id for an SVF I Cleanthes fragment."""
    return f"passage_cleanthes_svf_i_{n}"


def hymn_line_node_id(line: int) -> str:
    """Canonical node id for a Hymn to Zeus line passage."""
    return f"passage_cleanthes_hymn_zeus_line_{line}"


def extract_fragments_from_tei(path: Path) -> list[dict[str, Any]]:
    """Parse a TEI XML and return [{number, text}] for every `div[@subtype="fragment"]`.

    Text = whitespace-normalized concatenation of every <p> inside the fragment div.
    Fragment numbers preserved as strings to retain any letter suffixes.
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
        parts: list[str] = []
        for p in div.findall(".//t:p", NS_MAP):
            text = etree.tostring(p, method="text", encoding="unicode")
            parts.append(text)
        joined = " ".join(" ".join(parts).split())
        out.append({"number": n, "text": joined})
    return out


def extract_hymn_lines(path: Path, hymn_fragment_number: str = HYMN_FRAGMENT_NUMBER) -> list[str]:
    """Extract the Hymn to Zeus as a list of one Greek line per `<lb/>` marker.

    The Hymn is encoded as `<quote rend="blockquote"><lb/>line 1<lb/>line 2...</quote>`
    inside fragment 537. We tokenise on <lb/> elements (preserving original line breaks)
    rather than on whitespace alone.

    Returns an empty list if the fragment is not found.
    """
    tree = etree.parse(str(path))
    root = tree.getroot()
    for div in root.findall(".//t:div[@type='textpart']", NS_MAP):
        if div.get("subtype") != "fragment" or div.get("n") != hymn_fragment_number:
            continue
        # Hymn lines live inside the <quote> child of the fragment's <p>
        quote = div.find(".//t:quote", NS_MAP)
        if quote is None:
            return []
        # Serialise the <quote> subtree, then split on <lb/>.
        raw_xml = etree.tostring(quote, encoding="unicode")
        # Normalise <lb/> variations into a single newline marker.
        xml_with_breaks = re.sub(r"<(?:[a-z]+:)?lb\b[^>]*/?\s*>", "\n", raw_xml)
        # Strip remaining XML tags (bibl, foreign, q, pb, etc.).
        text_only = re.sub(r"<[^>]+>", "", xml_with_breaks)
        # Decode XML entities (we're only stripping tags so &amp; etc. remain — fix any)
        text_only = text_only.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        lines = [" ".join(piece.split()) for piece in text_only.split("\n") if piece.strip()]
        return lines
    return []


# -----------------------------------------------------------------------------
# Node / edge factories
# -----------------------------------------------------------------------------


def _base_metadata() -> dict[str, Any]:
    return {
        "author": "Cleanthes of Assos",
        "school": "Stoic",
        "language": "grc",
        "passage_role": "original",
        "edition": "Hans von Arnim, Stoicorum Veterum Fragmenta I (Teubner, Leipzig 1903)",
        "bibtex_key": BIBTEX_KEY,
        "source_tei": "OpenGreekAndLatin/First1KGreek tlg1269.tlg002.1st1K-grc1.xml",
        "source_tei_url": TEI_URL,
        "source": SOURCE_TAG,
        "license": "CC BY-SA 4.0 (OGL re-encoding)",
        "created_by": CREATED_BY,
        "contains_greek_to_verify": False,
        "period": "Hellenistic",
        "fragmented_philosopher": "Cleanthes",
        "fragmented_philosopher_node_id": PERSON_ID,
        "work_canonical_id": "tlg1269.tlg002.1st1K-grc1",
    }


def build_svf_fragment_node(number: str, greek_text: str) -> dict[str, Any]:
    pid = fragment_node_id(number)
    md = _base_metadata()
    md.update(
        {
            "attestation_type": "fragment_collection",
            "canonical_ref": f"SVF I.{number}",
            "char_length": len(greek_text),
            "word_count": len(greek_text.split()),
            "cts_urn": f"{CTS_URN_BASE}:{number}",
            "work_title": "Stoicorum Veterum Fragmenta I — Cleanthis Assii fragmenta",
            "fragment_number": number,
            "fragment_collection": "SVF",
            "fragment_volume": "I",
        }
    )
    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Cleanthes, SVF I.{number}",
        "description": greek_text,
        "alternative_names": "[]",
        "period": "Hellenistic",
        "role": None,
        "school": "Stoic",
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def build_hymn_complete_node(full_text: str, line_count: int) -> dict[str, Any]:
    pid = "passage_cleanthes_hymn_zeus_complete"
    md = _base_metadata()
    md.update(
        {
            "attestation_type": "complete_poem",
            "canonical_ref": "SVF I.537 (= Stobaeus, Ecl. I.1.12)",
            "transmission": "Stobaeus, Anthologium I.1.12 p. 25.3 Wachsmuth",
            "char_length": len(full_text),
            "word_count": len(full_text.split()),
            "line_count": line_count,
            "metre": "dactylic hexameter",
            "cts_urn": f"{CTS_URN_BASE}:{HYMN_FRAGMENT_NUMBER}",
            "work_title": "Cleanthes, Hymn to Zeus (Ὕμνος εἰς Δία)",
            "fragment_number": HYMN_FRAGMENT_NUMBER,
            "fragment_collection": "SVF",
            "fragment_volume": "I",
            "editions_other": [
                "Powell, Collectanea Alexandrina (Clarendon Press, Oxford 1925, repr. 1981)",
                "Thom, Cleanthes' Hymn to Zeus, STAC 33 (Mohr Siebeck, Tübingen 2005)",
            ],
        }
    )
    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": "Cleanthes, Hymn to Zeus (complete, 39 lines)",
        "description": full_text,
        "alternative_names": "[]",
        "period": "Hellenistic",
        "role": None,
        "school": "Stoic",
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def build_hymn_line_node(line_no: int, line_text: str) -> dict[str, Any]:
    pid = hymn_line_node_id(line_no)
    md = _base_metadata()
    md.update(
        {
            "attestation_type": "verse_line",
            "canonical_ref": f"Hymn to Zeus, line {line_no} (SVF I.537)",
            "char_length": len(line_text),
            "word_count": len(line_text.split()),
            "line_number": line_no,
            "metre": "dactylic hexameter",
            "cts_urn": f"{CTS_URN_BASE}:{HYMN_FRAGMENT_NUMBER}.{line_no}",
            "work_title": "Cleanthes, Hymn to Zeus (Ὕμνος εἰς Δία)",
            "fragment_number": HYMN_FRAGMENT_NUMBER,
            "fragment_collection": "SVF",
            "fragment_volume": "I",
            "parent_passage_id": "passage_cleanthes_hymn_zeus_complete",
        }
    )
    return {
        "id": pid,
        "node_id": pid,
        "type": "passage",
        "label": f"Cleanthes, Hymn to Zeus l. {line_no}",
        "description": line_text,
        "alternative_names": "[]",
        "period": "Hellenistic",
        "role": None,
        "school": "Stoic",
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def build_svf_i_work_node() -> dict[str, Any]:
    """Create the parent work node for SVF I Cleanthes fragments (mirrors work_chrysippus_svf_ii)."""
    md = {
        "title_grc": "Cleanthis Assii fragmenta",
        "title_en": "Cleanthes of Assos, Fragments",
        "edition": (
            "Hans von Arnim, Stoicorum Veterum Fragmenta I — Zeno et Zenonis discipuli "
            "(Teubner, Leipzig 1903)"
        ),
        "bibtex_key": BIBTEX_KEY,
        "source_tei": "OpenGreekAndLatin/First1KGreek tlg1269.tlg002.1st1K-grc1.xml",
        "source_tei_url": TEI_URL,
        "license": "CC BY-SA 4.0 (OGL re-encoding)",
        "cts_urn": CTS_URN_BASE,
        "language": "grc",
        "period": "Hellenistic",
        "approximate_date": "c. 280-230 BCE",
        "fragment_range": "SVF I.463-619",
        "school": "Stoic",
        "created_by": CREATED_BY,
        "created_at": TIMESTAMP,
    }
    return {
        "id": SVF_WORK_ID,
        "node_id": SVF_WORK_ID,
        "type": "work",
        "label": "Cleanthes, Fragmenta (SVF I.463-619, Arnim)",
        "description": (
            "Collected fragments of Cleanthes of Assos (Stoic scholarch c. 263-230 BCE), "
            "edited by Hans von Arnim in Stoicorum Veterum Fragmenta vol. I (Teubner 1903), "
            "section 5: 'Cleanthis Assii fragmenta et apophthegmata' = SVF I.463-619. "
            "Includes biographical testimonia, theology (φύσις, Ζεύς, εἱμαρμένη), cosmology, "
            "and ethics. The Hymn to Zeus (SVF I.537 = Stobaeus Ecl. I.1.12) is the most "
            "extensive extant Stoic theological poem."
        ),
        "alternative_names": "[]",
        "period": "Hellenistic",
        "role": None,
        "school": "Stoic",
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


def build_edge(
    source: str,
    target: str,
    relation: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write to data/kg/{nodes,edges}.jsonl. Default = dry-run preview.",
    )
    parser.add_argument(
        "--svf-fragments",
        type=str,
        default=",".join(DEFAULT_SVF_FRAGMENTS),
        help="Comma-separated SVF I Cleanthes fragment numbers to ingest. "
             f"Default = {','.join(DEFAULT_SVF_FRAGMENTS)} (fate/theology core).",
    )
    parser.add_argument(
        "--skip-hymn",
        action="store_true",
        help="Skip ingesting the Hymn to Zeus complete + 39 line passages.",
    )
    parser.add_argument(
        "--skip-svf",
        action="store_true",
        help="Skip ingesting selected SVF I fragments (Hymn only).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    target_svf_fragments = (
        [f.strip() for f in args.svf_fragments.split(",") if f.strip()]
        if not args.skip_svf
        else []
    )

    print(f"== Cleanthes ingestion — commit={args.commit} ==")
    print(f"  Hymn ingestion : {'SKIPPED' if args.skip_hymn else 'YES (1 complete + 39 lines)'}")
    print(f"  SVF I fragments: {target_svf_fragments if target_svf_fragments else 'NONE'}")

    # Phase 1 : parse TEI
    print("\n== PHASE 1 : PARSE TEI ==")
    ensure_tei_local()
    fragments = extract_fragments_from_tei(TEI_LOCAL)
    print(f"  Total Cleanthes fragments in TEI: {len(fragments)}")
    frag_by_n = {f["number"]: f for f in fragments}

    if not args.skip_hymn:
        if HYMN_FRAGMENT_NUMBER not in frag_by_n:
            print(f"FATAL: Hymn fragment {HYMN_FRAGMENT_NUMBER} missing from TEI — abort")
            return 1
        hymn_lines = extract_hymn_lines(TEI_LOCAL, HYMN_FRAGMENT_NUMBER)
        if len(hymn_lines) != 39:
            print(f"WARNING: Hymn has {len(hymn_lines)} lines (expected 39)")
        print(f"  Hymn lines extracted: {len(hymn_lines)}")

    # Phase 2 : load current KG
    print("\n== PHASE 2 : LOAD CURRENT KG ==")
    nodes = [json.loads(line) for line in NODES_PATH.read_text().splitlines() if line.strip()]
    edges = [json.loads(line) for line in EDGES_PATH.read_text().splitlines() if line.strip()]
    print(f"  Nodes loaded : {len(nodes)}")
    print(f"  Edges loaded : {len(edges)}")
    node_ids = {n["id"] for n in nodes}

    if HYMN_WORK_ID not in node_ids:
        print(f"FATAL: Hymn work node {HYMN_WORK_ID} missing — abort")
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

    # 3a. Hymn complete + lines
    if not args.skip_hymn:
        hymn_lines = extract_hymn_lines(TEI_LOCAL, HYMN_FRAGMENT_NUMBER)
        full_hymn_text = "\n".join(hymn_lines)
        complete_id = "passage_cleanthes_hymn_zeus_complete"
        if complete_id not in node_ids:
            new_nodes.append(build_hymn_complete_node(full_hymn_text, len(hymn_lines)))
            node_ids.add(complete_id)
            if (complete_id, HYMN_WORK_ID) not in existing_part_of:
                new_edges.append(
                    build_edge(complete_id, HYMN_WORK_ID, "part_of", {"auto_generated": True})
                )
                existing_part_of.add((complete_id, HYMN_WORK_ID))
            if (complete_id, PERSON_ID) not in existing_authored:
                new_edges.append(
                    build_edge(
                        complete_id,
                        PERSON_ID,
                        "authored_by",
                        {"auto_generated": True, "propagated_from_work": True},
                    )
                )
                existing_authored.add((complete_id, PERSON_ID))
        else:
            skipped_existing += 1

        for i, line_text in enumerate(hymn_lines, start=1):
            line_id = hymn_line_node_id(i)
            if line_id in node_ids:
                skipped_existing += 1
                continue
            new_nodes.append(build_hymn_line_node(i, line_text))
            node_ids.add(line_id)
            # Line is part_of the Hymn-complete passage (NOT directly part_of the work-shell;
            # the complete-passage handles that hop, and SHACL prefers single part_of per node).
            if (line_id, complete_id) not in existing_part_of:
                new_edges.append(
                    build_edge(line_id, complete_id, "part_of", {"auto_generated": True})
                )
                existing_part_of.add((line_id, complete_id))
            if (line_id, PERSON_ID) not in existing_authored:
                new_edges.append(
                    build_edge(
                        line_id,
                        PERSON_ID,
                        "authored_by",
                        {"auto_generated": True, "propagated_from_work": True},
                    )
                )
                existing_authored.add((line_id, PERSON_ID))

    # 3b. New SVF I work-shell (parent for non-Hymn fragments)
    svf_work_created = False
    if target_svf_fragments and SVF_WORK_ID not in node_ids:
        new_nodes.append(build_svf_i_work_node())
        node_ids.add(SVF_WORK_ID)
        # Wire work → collection_svf if it exists
        if "collection_svf" in node_ids:
            new_edges.append(
                build_edge(SVF_WORK_ID, "collection_svf", "part_of", {"auto_generated": True})
            )
        # Wire work → person_cleanthes (authored_by at work level)
        if (SVF_WORK_ID, PERSON_ID) not in existing_authored:
            new_edges.append(
                build_edge(SVF_WORK_ID, PERSON_ID, "authored_by", {"auto_generated": True})
            )
            existing_authored.add((SVF_WORK_ID, PERSON_ID))
        svf_work_created = True

    # 3c. SVF I fragment passages
    skipped_missing_in_tei = 0
    skipped_empty = 0
    for n in target_svf_fragments:
        if n not in frag_by_n:
            skipped_missing_in_tei += 1
            continue
        frag = frag_by_n[n]
        text = frag["text"]
        if not text.strip():
            skipped_empty += 1
            continue
        pid = fragment_node_id(n)
        if pid in node_ids:
            skipped_existing += 1
            continue
        new_nodes.append(build_svf_fragment_node(n, text))
        node_ids.add(pid)
        if (pid, SVF_WORK_ID) not in existing_part_of:
            new_edges.append(build_edge(pid, SVF_WORK_ID, "part_of", {"auto_generated": True}))
            existing_part_of.add((pid, SVF_WORK_ID))
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

    print(f"  New nodes : {len(new_nodes)}")
    print(f"  New edges : {len(new_edges)}")
    print(f"  Skipped (already in KG)         : {skipped_existing}")
    print(f"  Skipped (missing in TEI)        : {skipped_missing_in_tei}")
    print(f"  Skipped (empty TEI fragment)    : {skipped_empty}")
    print(f"  New SVF I work-shell created    : {svf_work_created}")

    # Sample preview
    if new_nodes:
        sample = new_nodes[0]
        sample_md = json.loads(sample["metadata"])
        print(f"\n  Sample node : {sample['id']}")
        print(f"    label    : {sample['label']}")
        if "cts_urn" in sample_md:
            print(f"    cts_urn  : {sample_md['cts_urn']}")
        if "char_length" in sample_md:
            print(f"    chars    : {sample_md['char_length']}")
        print(f"    text[:120]: {sample['description'][:120]}")

    # Phase 4 : enrich Hymn work node
    print("\n== PHASE 4 : ENRICH HYMN WORK NODE METADATA ==")
    hymn_work_updated = False
    for n in nodes:
        if n["id"] != HYMN_WORK_ID:
            continue
        md_raw = n.get("metadata") or "{}"
        md = json.loads(md_raw) if isinstance(md_raw, str) else md_raw
        if md.get("needs_text_ingestion") or "source_tei" not in md:
            md["source_tei"] = "OpenGreekAndLatin/First1KGreek tlg1269.tlg002.1st1K-grc1.xml"
            md["source_tei_url"] = TEI_URL
            md["bibtex_key"] = BIBTEX_KEY
            md["license"] = "CC BY-SA 4.0 (OGL re-encoding)"
            md["cts_urn"] = f"{CTS_URN_BASE}:{HYMN_FRAGMENT_NUMBER}"
            md.pop("needs_text_ingestion", None)
            md["enriched_by"] = CREATED_BY
            md["enriched_at"] = TIMESTAMP
            n["metadata"] = json.dumps(md, ensure_ascii=False)
            n["updated_at"] = TIMESTAMP
            hymn_work_updated = True
            print(f"  Enriched: {HYMN_WORK_ID}")
        else:
            print(f"  Already enriched: {HYMN_WORK_ID}")
        break

    # Phase 5 : commit or dry-run
    print("\n== PHASE 5 : COMMIT ==")
    if not args.commit:
        print("  DRY-RUN — no files written. Pass --commit to persist.")
        return 0

    # Append-mode write for new nodes/edges.
    with NODES_PATH.open("a", encoding="utf-8") as f:
        for n in new_nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("a", encoding="utf-8") as f:
        for e in new_edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"  Appended {len(new_nodes)} nodes to {NODES_PATH}")
    print(f"  Appended {len(new_edges)} edges to {EDGES_PATH}")

    # Hymn-work enrichment requires a full rewrite (in-place mutation).
    if hymn_work_updated:
        with NODES_PATH.open("w", encoding="utf-8") as f:
            for n in nodes:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")
            for n in new_nodes:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")
        print(f"  Rewrote {NODES_PATH} (Hymn work-node enrichment merged)")

    print("\n== CLEANTHES INGESTION COMPLETE ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
