#!/usr/bin/env python3
"""Repair the EN III.5 1113b7-8 / 1114b1-12 corpus-KG collision.

The graph previously mapped three different KG passage nodes to the corpus UUID
for 1114b1-12. Worse, the node labelled 1113b7-21 stopped before 1113b7-8 and
its English companion paraphrased the preceding lines. This wave creates an
exact 1113b7-8 corpus record, restores one-to-one snapshot mappings, and removes
an irreparably corrupted AI-generated editorial synthesis from the primary
corpus while preserving it in an audit quarantine file.

Dry-run is the default. Use ``--write`` to apply. Every mutation is guarded by
preconditions and the transformation is idempotent.

This file is the functional historical applier restored after the separate
manifest-gap follow-up was split into its own script. Byte identity with the
original untracked working-tree file is not asserted.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "aristotle_en_iii_5_locus_repair_2026_08_24"

GREEK_NODE_1113 = "passage_aristotle_en_iii_5_1113b7"
ENGLISH_NODE_1113 = "passage_aristotle_en_iii_5_1113b7_en"
GREEK_NODE_1114 = "passage_aristotle_en_iii_5_1114b1"
ENGLISH_NODE_1114 = "passage_aristotle_en_iii_5_1114b1_en"
SYNTHESIS_NODE = "passage_arist_en_3_5"
CORRUPT_SYNTHESIS_EN_NODE = "passage_arist_en_3_5_en"

PASSAGE_1113_GRC = "1e336c5e-391c-5613-a59d-b83d2bcc5523"
PASSAGE_1113_ENG = "88ac0d42-994e-5dee-9df0-7069da06cc60"
PASSAGE_1114_GRC = "28b16b62-34cb-4db0-a445-c778d696cb4e"
PASSAGE_1114_ENG = "1da67f00-a117-5916-94e8-0238afb57bfb"
CORRUPT_SYNTHESIS_PASSAGE = "189c67ca-ad95-5155-91ec-da7c41f2f1fc"
PASSAGE_PROHAIRESIS = "1184b45a-1b9b-4672-a77c-adef6ca1d25a"

REF_1113_GRC = "EN III.5, 1113b7-8 (ἐφ’ ἡμῖν)"
REF_1113_ENG = "EN III.5, 1113b7-8 (ἐφ’ ἡμῖν) (English)"
URN_III_5 = "urn:cts:greekLit:tlg0086.tlg010:3.5"

GREEK_1113 = (
    "ἐν οἷς γὰρ ἐφ’ ἡμῖν τὸ πράττειν, καὶ τὸ μὴ πράττειν, "
    "καὶ ἐν οἷς τὸ μή, καὶ τὸ ναί·"
)
ENGLISH_1113 = (
    "For, where to act is up to us, also to not act is up to us, and where "
    "to not act is up to us, also to act is up to us."
)

SYNTHESIS_DESCRIPTION = """EDITORIAL SYNTHESIS — NOT A PRIMARY-SOURCE TRANSCRIPT.

This node summarizes Aristotle, Nicomachean Ethics III.5 (1113b3-1115a3).
At 1113b7-8 Aristotle states a vice-versa relation between acting and not
acting: where acting is up to us, not acting is also up to us, and conversely.
The passage does not say that it is up to us to “say yes” or “say no”.  At
1114b1-12 Aristotle considers the objection that character determines how the
good appears and replies by connecting agents causally to their dispositions.

For quotation or factual attribution, use the exact primary Greek passage
nodes and their separately identified translations, not this synthesis."""

SYNTHESIS_EN_DESCRIPTION = """EDITORIAL SYNTHESIS — NOT A TRANSLATION OR PRIMARY-SOURCE TRANSCRIPT.

This English research aid summarizes Nicomachean Ethics III.5
(1113b3-1115a3).  At 1113b7-8 the Greek expresses a vice-versa relation between
acting and not acting; it contains no verb meaning “say”.  At 1114b1-12
Aristotle addresses the objection that a person's character determines how the
good appears.  Cite the exact Greek locus or a named published translation."""

DROP_EDGE_IDS = {
    "31e2663c-5269-4e37-bb23-759637ca94b7",
    "917c5656-d5a4-45b3-93c8-ee69eb22edb4",
    "338f93b6-5df4-47a3-b77a-53e26892bb1e",
    "8e75f9e6-5cd8-4c02-b61b-9f47c8197e93",
    "e681b70e-940e-4b4b-86e1-8429e6436aa4",
    "2c791352-c34d-433c-a9a0-5b2bc20ce0f5",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(obj: dict[str, Any]) -> dict[str, Any]:
    value = obj.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(obj: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(obj.get("metadata"), str):
        obj["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        obj["metadata"] = value


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def text_hash(value: str) -> str:
    return hashlib.sha256(nfc(value).encode("utf-8")).hexdigest()


def require_unique(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    found = [row for row in rows if str(row.get(key) or "") == value]
    if len(found) != 1:
        raise RuntimeError(f"expected exactly one {key}={value!r}; found {len(found)}")
    return found[0]


def require_node(nodes: list[dict[str, Any]], wanted: str) -> dict[str, Any]:
    found = [node for node in nodes if node_id(node) == wanted]
    if len(found) != 1:
        raise RuntimeError(f"expected exactly one node {wanted!r}; found {len(found)}")
    return found[0]


def update_exact_node(
    node: dict[str, Any],
    *,
    label: str,
    description: str,
    passage_id: str,
    canonical_ref: str,
    language: str,
) -> None:
    node["label"] = label
    node["description"] = description
    node["updated_at"] = "2026-08-24 00:00:00+00:00"
    data = metadata(node)
    data.update(
        {
            "author": "Aristotle",
            "bekker": "1113b7-8",
            "canonical_ref": canonical_ref,
            "citable_as_primary": language == "grc",
            "corpus_passage_id": passage_id,
            "cts_urn": URN_III_5,
            "db_passage_id": passage_id,
            "language": language,
            "passage_id": passage_id,
            "text_content_sha256_nfc": text_hash(description),
            STAMP: True,
            f"{STAMP}_status": "source_checked_exact_locus",
        }
    )
    if language == "grc":
        data.update(
            {
                "attestation_type": "direct",
                "edition": "Bywater (OCT)",
                "key_terms": ["ἐφ’ ἡμῖν", "πράττειν", "μὴ πράττειν"],
                "passage_role": "original",
                "translation_verified": False,
            }
        )
    else:
        for key in ("auto_generated", "source_model", "translation_source"):
            data.pop(key, None)
        data.update(
            {
                "attestation_type": "translation",
                "citable_as_primary": False,
                "original_node_id": GREEK_NODE_1113,
                "passage_role": "translation",
                "source": "published_scholarly_translation",
                "source_language": "grc",
                "translation_source": (
                    "Susanne Bobzien, ‘Found in Translation’, Oxford Studies "
                    "in Ancient Philosophy 45 (2013), 103-148, translation (I)"
                ),
                "translation_source_doi": "10.1093/acprof:oso/9780199679430.003.0004",
                "translation_type": "published_scholarly_translation",
                "translator": "Susanne Bobzien",
                "verified_against_source": True,
            }
        )
    set_metadata(node, data)


def quarantine_editorial_node(node: dict[str, Any], *, english: bool) -> None:
    node["label"] = (
        "Editorial synthesis: Aristotle, EN III.5 (English research aid)"
        if english
        else "Editorial synthesis: Aristotle, EN III.5"
    )
    node["description"] = SYNTHESIS_EN_DESCRIPTION if english else SYNTHESIS_DESCRIPTION
    node["updated_at"] = "2026-08-24 00:00:00+00:00"
    data = metadata(node)
    for key in (
        "author",
        "auto_generated",
        "cts_urn",
        "db_passage_id",
        "passage_id",
        "corpus_passage_id",
        "source_model",
        "translation_source",
    ):
        data.pop(key, None)
    data.update(
        {
            "about_author": "Aristotle",
            "attestation_type": "editorial_synthesis",
            "citable_as_primary": False,
            "editorial_author": "EleutherIA",
            "language": "eng" if english else "mul",
            "passage_role": "editorial_synthesis",
            "primary_node_id": "passage_arist_ne_3_5",
            "synthesis_of_urn": "urn:cts:greekLit:tlg0086.tlg010.perseus-grc2:3.5",
            STAMP: True,
            f"{STAMP}_status": "quarantined_non_primary",
        }
    )
    if english:
        data["original_node_id"] = SYNTHESIS_NODE
        data["translation_type"] = "editorial_research_aid"
    set_metadata(node, data)


def citation_key(row: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (
        row.get("kg_node_id"),
        row.get("passage_id"),
        row.get("citation_type"),
    )


def transform(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    Counter[str],
]:
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)
    passages = copy.deepcopy(passages)
    citations = copy.deepcopy(citations)
    counts: Counter[str] = Counter()
    quarantine: list[dict[str, Any]] = []

    targets = {
        wanted: require_node(nodes, wanted)
        for wanted in (
            GREEK_NODE_1113,
            ENGLISH_NODE_1113,
            GREEK_NODE_1114,
            ENGLISH_NODE_1114,
            SYNTHESIS_NODE,
            CORRUPT_SYNTHESIS_EN_NODE,
        )
    }
    if all(metadata(node).get(STAMP) is True for node in targets.values()):
        validate_repaired_state(nodes, edges, passages, citations)
        return nodes, edges, passages, citations, [], counts

    old_1114 = require_unique(passages, "passage_id", PASSAGE_1114_GRC)
    old_1113_en = require_unique(passages, "passage_id", PASSAGE_1113_ENG)
    require_unique(passages, "passage_id", PASSAGE_1114_ENG)
    for node in targets.values():
        quarantine.append({"record_type": "kg_node_before", "record": copy.deepcopy(node)})

    existing_1113 = [
        row for row in passages if row.get("passage_id") == PASSAGE_1113_GRC
    ]
    if existing_1113:
        if (
            len(existing_1113) != 1
            or nfc(existing_1113[0].get("text_content", "")) != nfc(GREEK_1113)
        ):
            raise RuntimeError("new 1113b7-8 UUID already exists with non-canonical content")
        passage_1113 = existing_1113[0]
    else:
        passage_1113 = {
            "canonical_ref": REF_1113_GRC,
            "cts_urn": URN_III_5,
            "passage_id": PASSAGE_1113_GRC,
            "sequence_number": 5111300070008,
            "text_content": GREEK_1113,
            "work_canonical_id": "oga_tlg0086_tlg010_perseus_grc2_grc",
        }
        passages.append(passage_1113)
        counts["passages_added"] += 1
    passage_1113.update(
        {"canonical_ref": REF_1113_GRC, "cts_urn": URN_III_5, "text_content": GREEK_1113}
    )
    old_1113_en.update(
        {
            "canonical_ref": REF_1113_ENG,
            "cts_urn": URN_III_5,
            "sequence_number": 5111300070008,
            "text_content": ENGLISH_1113,
        }
    )
    counts["corpus_rows_corrected"] += 2

    update_exact_node(
        targets[GREEK_NODE_1113],
        label="EN III.5, 1113b7-8 (ἐφ’ ἡμῖν: acting / not acting)",
        description=GREEK_1113,
        passage_id=PASSAGE_1113_GRC,
        canonical_ref=REF_1113_GRC,
        language="grc",
    )
    update_exact_node(
        targets[ENGLISH_NODE_1113],
        label="EN III.5, 1113b7-8 (Bobzien translation)",
        description=ENGLISH_1113,
        passage_id=PASSAGE_1113_ENG,
        canonical_ref=REF_1113_ENG,
        language="eng",
    )

    targets[GREEK_NODE_1114]["description"] = old_1114["text_content"]
    for wanted, passage_id, passage in (
        (GREEK_NODE_1114, PASSAGE_1114_GRC, old_1114),
        (
            ENGLISH_NODE_1114,
            PASSAGE_1114_ENG,
            require_unique(passages, "passage_id", PASSAGE_1114_ENG),
        ),
    ):
        node = targets[wanted]
        data = metadata(node)
        data.update(
            {
                "canonical_ref": passage["canonical_ref"],
                "corpus_passage_id": passage_id,
                "db_passage_id": passage_id,
                "passage_id": passage_id,
                "text_content_sha256_nfc": text_hash(node.get("description", "")),
                STAMP: True,
                f"{STAMP}_status": "existing_exact_locus_relinked",
            }
        )
        set_metadata(node, data)

    quarantine_editorial_node(targets[SYNTHESIS_NODE], english=False)
    quarantine_editorial_node(targets[CORRUPT_SYNTHESIS_EN_NODE], english=True)
    counts["nodes_corrected"] += 6

    removed_passages = [
        row for row in passages if row.get("passage_id") == CORRUPT_SYNTHESIS_PASSAGE
    ]
    for row in removed_passages:
        quarantine.append({"record_type": "corpus_passage_removed", "record": row})
    passages = [
        row for row in passages if row.get("passage_id") != CORRUPT_SYNTHESIS_PASSAGE
    ]
    counts["corrupt_corpus_rows_quarantined"] += len(removed_passages)

    drop_citations = {
        ("concept_akousion_involuntary_aristotle_b2c3d4e5", PASSAGE_1114_GRC, "discusses"),
        ("concept_hekousion_voluntary_aristotle_a1b2c3d4", PASSAGE_1114_GRC, "discusses"),
        ("concept_hekousion_voluntary_aristotle_a1b2c3d4", PASSAGE_1114_GRC, "evidenced_by"),
        ("concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", PASSAGE_1114_GRC, "discusses"),
        ("concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", PASSAGE_1114_GRC, "evidenced_by"),
        (SYNTHESIS_NODE, PASSAGE_1114_GRC, "snapshot_passage_node"),
        (CORRUPT_SYNTHESIS_EN_NODE, CORRUPT_SYNTHESIS_PASSAGE, "snapshot_passage_node"),
    }
    repoint_citations = {
        ("concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", PASSAGE_1114_GRC, "evidenced_by"): PASSAGE_1113_GRC,
        ("concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", PASSAGE_1114_GRC, "grounded_in"): PASSAGE_1113_GRC,
        ("concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", PASSAGE_1114_GRC, "grounded_in"): PASSAGE_PROHAIRESIS,
        (GREEK_NODE_1113, PASSAGE_1114_GRC, "snapshot_passage_node"): PASSAGE_1113_GRC,
    }
    repaired_citations: list[dict[str, Any]] = []
    for citation in citations:
        triple = citation_key(citation)
        if triple in drop_citations:
            quarantine.append({"record_type": "citation_removed", "record": citation})
            counts["citations_removed"] += 1
            continue
        if triple in repoint_citations:
            citation["passage_id"] = repoint_citations[triple]
            citation["notes"] = f"{STAMP}: corrected locus"
            counts["citations_repointed"] += 1
        if (
            citation.get("kg_node_id")
            == "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7"
            and citation.get("passage_id") == PASSAGE_1114_GRC
            and citation.get("citation_type") == "discusses"
        ):
            citation["confidence"] = 0.65
            citation["notes"] = (
                f"{STAMP}: thematic character/apparent-good corollary, not a definition"
            )
            counts["citations_qualified"] += 1
        repaired_citations.append(citation)
    citations = repaired_citations

    new_citation = {
        "citation_type": "source_for",
        "confidence": 1.0,
        "kg_node_id": "argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        "notes": f"{STAMP}: exact symmetry premise at 1113b7-8",
        "passage_id": PASSAGE_1113_GRC,
    }
    if citation_key(new_citation) not in {citation_key(row) for row in citations}:
        citations.append(new_citation)
        counts["citations_added"] += 1

    repaired_edges: list[dict[str, Any]] = []
    for edge in edges:
        if edge.get("edge_id") in DROP_EDGE_IDS:
            quarantine.append({"record_type": "kg_edge_removed", "record": edge})
            counts["edges_removed"] += 1
            continue
        if edge.get("edge_id") == "8033b080-9a93-429c-83c1-42994e253005":
            edge["target"] = GREEK_NODE_1113
            edge["target_id"] = GREEK_NODE_1113
            data = metadata(edge)
            data.update(
                {
                    STAMP: True,
                    "scope_note": "P6 symmetry premise only; other premises need their own loci",
                }
            )
            set_metadata(edge, data)
            counts["edges_repointed"] += 1
        elif edge.get("edge_id") == "437087b9-973e-4a8a-829c-688b7ca769dc":
            edge["target"] = GREEK_NODE_1113
            edge["target_id"] = GREEK_NODE_1113
            data = metadata(edge)
            data.update({STAMP: True, "confidence": 1.0})
            set_metadata(edge, data)
            counts["edges_repointed"] += 1
        repaired_edges.append(edge)
    edges = repaired_edges

    validate_repaired_state(nodes, edges, passages, citations)
    return nodes, edges, passages, citations, quarantine, counts


def validate_repaired_state(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> None:
    by_node = {node_id(node): node for node in nodes}
    by_passage = {str(row.get("passage_id")): row for row in passages}
    if nfc(by_passage[PASSAGE_1113_GRC]["text_content"]) != nfc(GREEK_1113):
        raise RuntimeError("1113b7-8 Greek corpus text is not exact")
    if "λέγειν" in GREEK_1113 or "οὔ" in GREEK_1113:
        raise RuntimeError("1113b7-8 repair accidentally contains saying-no vocabulary")
    if "say yes" in ENGLISH_1113.lower() or "say no" in ENGLISH_1113.lower():
        raise RuntimeError("1113b7-8 English repair contains the rejected saying-no reading")

    snapshot_counts: Counter[str] = Counter()
    snapshot_nodes: Counter[str] = Counter()
    pairs: set[tuple[str, str]] = set()
    for row in citations:
        if row.get("citation_type") != "snapshot_passage_node":
            continue
        passage = str(row.get("passage_id"))
        node = str(row.get("kg_node_id"))
        snapshot_counts[passage] += 1
        snapshot_nodes[node] += 1
        pairs.add((passage, node))
    expected = {
        PASSAGE_1113_GRC: GREEK_NODE_1113,
        PASSAGE_1113_ENG: ENGLISH_NODE_1113,
        PASSAGE_1114_GRC: GREEK_NODE_1114,
        PASSAGE_1114_ENG: ENGLISH_NODE_1114,
    }
    for passage_id, wanted_node in expected.items():
        if snapshot_counts[passage_id] != 1 or (passage_id, wanted_node) not in pairs:
            raise RuntimeError(
                f"snapshot bijection failed for {passage_id}: "
                f"count={snapshot_counts[passage_id]}, expected node={wanted_node}"
            )
        if snapshot_nodes[wanted_node] != 1:
            raise RuntimeError(f"snapshot node {wanted_node} is not unique")

    for wanted in (SYNTHESIS_NODE, CORRUPT_SYNTHESIS_EN_NODE):
        data = metadata(by_node[wanted])
        if data.get("citable_as_primary") is not False or any(
            key in data for key in ("passage_id", "db_passage_id", "corpus_passage_id")
        ):
            raise RuntimeError(f"editorial synthesis {wanted} still looks primary")
        if snapshot_nodes[wanted]:
            raise RuntimeError(f"editorial synthesis {wanted} still has a snapshot")
    if CORRUPT_SYNTHESIS_PASSAGE in by_passage:
        raise RuntimeError("corrupt synthetic passage remains in primary corpus")

    triples = {
        (edge.get("source"), edge.get("relation"), edge.get("target")) for edge in edges
    }
    if (
        "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
        "evidenced_by",
        GREEK_NODE_1113,
    ) not in triples:
        raise RuntimeError("eph' hemin is not evidenced by the repaired exact locus")
    if any(edge.get("edge_id") in DROP_EDGE_IDS for edge in edges):
        raise RuntimeError("a forbidden stale edge survived the repair")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply changes")
    parser.add_argument("--dry-run", action="store_true", help="explicit no-op default")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    if args.write and args.dry_run:
        parser.error("--write and --dry-run are mutually exclusive")

    data_root = args.data_root.expanduser().resolve()
    paths = {
        "nodes": data_root / "kg" / "nodes.jsonl",
        "edges": data_root / "kg" / "edges.jsonl",
        "passages": data_root / "corpus" / "passages.jsonl",
        "citations": data_root / "corpus" / "citations.jsonl",
    }
    before = {name: read_jsonl(path) for name, path in paths.items()}
    nodes, edges, passages, citations, quarantine, counts = transform(
        before["nodes"], before["edges"], before["passages"], before["citations"]
    )

    print("Aristotle EN III.5 atomic locus repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    for key, value in sorted(counts.items()):
        print(f"{key}: {value}")
    print(
        "rows:",
        f"nodes {len(before['nodes'])}->{len(nodes)},",
        f"edges {len(before['edges'])}->{len(edges)},",
        f"passages {len(before['passages'])}->{len(passages)},",
        f"citations {len(before['citations'])}->{len(citations)}",
    )
    print("quarantine records:", len(quarantine))
    if not args.write:
        print("dry-run: nothing written (use --write to apply)")
        return 0
    if not counts:
        print("already applied: no files written")
        return 0
    write_jsonl_atomic(paths["nodes"], nodes)
    write_jsonl_atomic(paths["edges"], edges)
    write_jsonl_atomic(paths["passages"], passages)
    write_jsonl_atomic(paths["citations"], citations)
    quarantine_path = data_root / "audit" / "2026-08-24_aristotle_en_iii_5_quarantine.jsonl"
    write_jsonl_atomic(quarantine_path, quarantine)
    print("wrote:", ", ".join(str(path) for path in (*paths.values(), quarantine_path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
