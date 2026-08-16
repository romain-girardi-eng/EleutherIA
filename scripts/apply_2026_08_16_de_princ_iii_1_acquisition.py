#!/usr/bin/env python3
"""Apply the 2026-08-16 acquisition wave to the local KG + corpus mirror.

Two independent parts, both idempotent, both stamped so a second run is a no-op:

A. **De principiis III.1 (= Philocalia 21) in Greek** — the platform's own audit
   named this the #1 gap.  The Greek of the Περὶ αὐτεξουσίου, §§1-24, is
   ingested from the local TLG E disk (TLG2042 work 002 = De principiis,
   digitizing P. Koetschau, GCS 22, Leipzig 1913), section-aligned against the
   local SC 268 "Extraits grecs" file, which also supplies the French.
   See `scripts/data_2026_08_16_de_princ_iii_1_greek.py` for the full method,
   the byte spans and the per-section collation figures.

   - `passage_origen_philocalia_21_{1..24}`: the four nodes that already existed
     (5, 7, 18, 23) are ENRICHED, never duplicated; 20 are created.
     NB the four existing nodes all carried the SC 268 **French** while three of
     them advertised "Greek text" in their label and `metadata.language = "grc"`
     — the same defect that was corrected for §23 on 2026-08-16.  All four are
     corrected here and now really do carry Greek.
   - 24 corpus passages under the new work id
     `work_de_principiis_origen_230s_v2w3x4y5_grc`, one manifest row, and 24
     citations tying each KG node to its corpus passage.
   - 2 edges per new node, mirroring the existing four exactly
     (`part_of work_origen_philocalia`, `discusses work_de_principiis_...`).

B. **Historiography nodes** — Benjamins 1994 and Brown / Harrison / Rist /
   TeSelle, plus enrichment of the Hengstermann pair and one correction to
   `pub_wetzel_1992_augustine_limits_virtue`.  Every position statement is
   grounded in text that was read locally; no work among them is held, so each
   node carries `source_rank`, `held_locally: false`, `reference_status` and a
   `grounding` list of verbatim anchors.  See
   `scripts/data_2026_08_16_historiography_nodes.py`.

Usage:
    python3 scripts/apply_2026_08_16_de_princ_iii_1_acquisition.py [--dry-run]
                                                                  [--only greek|historiography]
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_16_de_princ_iii_1_greek import (  # noqa: E402
    CHAPTER_TITLE_EN,
    CHAPTER_TITLE_GRC,
    FRENCH_EDITION,
    FRENCH_SOURCE_FILE,
    GREEK_EDITION,
    PHILOCALIA_EDITIONS,
    SECTIONS,
    SOURCE_RANK,
    TLG_SOURCE,
)
from data_2026_08_16_de_princ_iii_1_greek import WAVE as GREEK_WAVE  # noqa: E402
from data_2026_08_16_historiography_nodes import (  # noqa: E402
    NEW_EDGES,
    NEW_NODES,
    NODE_ENRICHMENTS,
)
from data_2026_08_16_historiography_nodes import WAVE as HIST_WAVE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
PASSAGES_PATH = ROOT / "data" / "corpus" / "passages.jsonl"
CITATIONS_PATH = ROOT / "data" / "corpus" / "citations.jsonl"
MANIFEST_PATH = ROOT / "data" / "corpus" / "manifest.jsonl"

GREEK_MARKER = "de_princ_iii_1_greek_acquisition_2026_08_16"
HIST_MARKER = "historiography_acquisition_2026_08_16"
# bump when an enrichment spec changes, so a stamped node is revisited exactly once
HIST_REVISION = "r2"

PHILOCALIA_WORK = "work_origen_philocalia"
DE_PRINCIPIIS_WORK = "work_de_principiis_origen_230s_v2w3x4y5"
CORPUS_WORK_GRC = "work_de_principiis_origen_230s_v2w3x4y5_grc"
PASSAGE_UUID_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

NOW = datetime.now(UTC).isoformat(sep=" ")

log: list[str] = []
stats: dict[str, int] = {}


def bump(key: str, n: int = 1) -> None:
    stats[key] = stats.get(key, 0) + n


# --- io ---------------------------------------------------------------------


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def node_id_of(node: dict) -> str | None:
    return node.get("node_id") or node.get("id")


def parse_metadata(node: dict) -> tuple[dict, str]:
    """Metadata is sometimes a dict, sometimes a (double-)encoded JSON string."""
    raw = node.get("metadata")
    if isinstance(raw, dict):
        return raw, "dict"
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except ValueError:
            return {}, "opaque"
        if isinstance(parsed, str):
            try:
                inner = json.loads(parsed)
            except ValueError:
                return {}, "opaque"
            return (inner, "str2") if isinstance(inner, dict) else ({}, "opaque")
        return (parsed, "str") if isinstance(parsed, dict) else ({}, "opaque")
    return {}, "none"


def dump_metadata(node: dict, meta: dict, form: str) -> None:
    if form in ("dict", "none"):
        node["metadata"] = meta
    elif form == "str":
        node["metadata"] = json.dumps(meta, ensure_ascii=False)
    elif form == "str2":
        node["metadata"] = json.dumps(
            json.dumps(meta, ensure_ascii=False), ensure_ascii=False
        )


def append_note(meta: dict, note: str) -> None:
    notes = meta.get("verification_notes")
    if not isinstance(notes, list):
        notes = [notes] if isinstance(notes, str) else []
    if note not in notes:
        notes.append(note)
    meta["verification_notes"] = notes


# --- part A: De principiis III.1 Greek --------------------------------------


def short_label(text: str, limit: int = 92) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:") + "…"


def build_description(n: int, sec: dict) -> str:
    parts = [
        f"**Reference:** De principiis III.1.{n} = Philocalia 21.{n} "
        f"(Robinson 1893 §{sec['robinson_1893_section']})",
        "**Author:** Origen",
        f"**Work:** De principiis (Περὶ ἀρχῶν), Book III, chapter 1 — "
        f"{CHAPTER_TITLE_GRC} ({CHAPTER_TITLE_EN})",
        f"**Greek edition:** {GREEK_EDITION}",
        f"**French translation:** {FRENCH_EDITION}",
    ]
    if sec.get("rubric_sc268"):
        parts.append(f"**Section rubric (SC 268):** {sec['rubric_sc268']}")
    body = "\n".join(parts)
    return (
        f"{body}\n\n"
        f"**Original Greek:**\n{sec['greek']}\n\n"
        f"**French translation (SC 268, Crouzel–Simonetti):**\n{sec['french_sc268']}\n\n"
        f"**Greek character length:** {len(sec['greek'])}"
    )


def build_passage_metadata(n: int, sec: dict, corpus_passage_id: str) -> dict:
    meta = {
        "author": "Origen",
        "work": "De principiis (Περὶ ἀρχῶν)",
        "work_title": "De principiis, Book III, ch. 1 (Περὶ αὐτεξουσίου)",
        "school": "Christian Platonism",
        "language": "grc",
        "language_note": (
            "The payload carries the Greek of De principiis III.1 verbatim from "
            "the TLG digitization of Koetschau GCS 22, followed by the French "
            "translation printed in SC 268. No English translation of III.1 is "
            "held locally."
        ),
        "cts_urn": f"urn:cts:greekLit:tlg2042.tlg002:3.1.{n}",
        "philocalia_cts_urn": f"urn:cts:greekLit:tlg2042.tlg028:21.{n}",
        "de_princ_cts_urn": f"urn:cts:greekLit:tlg2042.tlg002:3.1.{n}",
        "reference": f"De principiis III.1.{n} = Philocalia 21.{n}",
        "section_label": sec["label_en"],
        "section_rubric_sc268": sec.get("rubric_sc268"),
        "philocalia_section": n,
        "de_princ_section_equivalent": n,
        "robinson_1893_section": sec["robinson_1893_section"],
        "passage_role": "original",
        "anchor_role": "philocalia_sub_anchor",
        "greek_edition": GREEK_EDITION,
        "greek_source": TLG_SOURCE,
        "greek_tlg_byte_span": sec["tlg_byte_span"],
        "greek_chars": len(sec["greek"]),
        "french_edition": FRENCH_EDITION,
        "french_source_file": FRENCH_SOURCE_FILE,
        "philocalia_editions": PHILOCALIA_EDITIONS,
        "sc268_greek_pages": sec["sc268_greek_pages"],
        "sc268_french_pages": sec["sc268_french_pages"],
        "sc268_collation_similarity": sec["sc268_similarity"],
        "collation_note": (
            "Letter-only, accent- and space-insensitive similarity of this "
            f"section's Greek against the SC 268 'Extraits grecs' witness: "
            f"{sec['sc268_similarity']}. The section boundary is the TLG's own "
            "section-level citation byte, not an editorial guess."
        ),
        "tlg_attestation": (
            "re-attested 2026-08-16 with scripts/tlg_search.py on a 12-word window "
            "from the middle of this section: hit in TLG2042"
        ),
        "source_rank": SOURCE_RANK,
        "source_quality": "critical_edition_koetschau_gcs22_via_tlg_e",
        "corpus_passage_id": corpus_passage_id,
        "corpus_work_canonical_id": CORPUS_WORK_GRC,
        "doxographical_source": "scholarly_critical_edition",
        "doxographical_confidence": "high",
        "citation_verdict": "verified",
        "citation_verified": True,
        "verified_reference": (
            f"Origen, De principiis III.1.{n} (= Philocalia 21.{n}; Robinson 1893 "
            f"§{sec['robinson_1893_section']}). Greek verbatim from the local TLG E "
            f"disk, TLG2042 work 002, bytes {sec['tlg_byte_span'][0]}-"
            f"{sec['tlg_byte_span'][1]} — digitizing {GREEK_EDITION}. French "
            f"verbatim from {FRENCH_SOURCE_FILE} (= {FRENCH_EDITION}), SC 268 "
            f"pages {sec['sc268_french_pages']}."
        ),
        "wave": GREEK_WAVE,
        GREEK_MARKER: True,
    }
    if sec.get("variant_note"):
        meta["variant_note"] = sec["variant_note"]
    if sec.get("page_marker_anomaly"):
        meta["page_marker_anomaly"] = sec["page_marker_anomaly"]
    if n == 1:
        meta["chapter_title_grc"] = CHAPTER_TITLE_GRC
        meta["chapter_title_en"] = CHAPTER_TITLE_EN
        meta["chapter_title_note"] = (
            "The chapter title stands in the transmitted text immediately before "
            "§1; it is stored here rather than inside the §1 payload."
        )
    return meta


def apply_greek(nodes: list[dict], edges: list[dict], dry: bool) -> None:
    by_id = {node_id_of(n): n for n in nodes}
    existing_edge_keys = {
        (e.get("source") or e.get("source_id"), e.get("relation"),
         e.get("target") or e.get("target_id"))
        for e in edges
    }

    # deterministic corpus passage ids
    corpus_ids = {
        n: str(uuid.uuid5(PASSAGE_UUID_NS,
                          f"{CORPUS_WORK_GRC}|urn:cts:greekLit:tlg2042.tlg002:3.1.{n}"))
        for n in SECTIONS
    }

    for n in sorted(SECTIONS):
        sec = SECTIONS[n]
        nid = f"passage_origen_philocalia_21_{n}"
        desc = build_description(n, sec)
        new_meta = build_passage_metadata(n, sec, corpus_ids[n])
        label = (
            f"Origen, De principiis III.1.{n} (= Philocalia 21.{n}) — "
            f"{short_label(sec['label_en'])} "
            f"[Greek: Koetschau GCS 22; French: SC 268]"
        )
        node = by_id.get(nid)
        if node is None:
            nodes.append({
                "alternative_names": "[]",
                "created_at": NOW,
                "description": desc,
                "id": nid,
                "label": label,
                "metadata": new_meta,
                "node_id": nid,
                "period": "Patristic",
                "role": None,
                "school": "Christian Platonism",
                "type": "passage",
                "updated_at": NOW,
            })
            bump("passage_nodes_created")
            log.append(f"created {nid} ({len(sec['greek'])} Greek chars)")
            for rel, tgt, note in (
                ("part_of", PHILOCALIA_WORK,
                 f"Philocalia 21.{n} is the Greek witness excerpted from De princ. III.1.{n}"),
                ("discusses", DE_PRINCIPIIS_WORK,
                 f"De principiis III.1.{n}, Greek text (Koetschau GCS 22 via TLG E)"),
            ):
                if (nid, rel, tgt) in existing_edge_keys:
                    continue
                edges.append({
                    "created_at": NOW,
                    "edge_id": str(uuid.uuid4()),
                    "metadata": {"wave": GREEK_WAVE, "note": note},
                    "relation": rel,
                    "source": nid,
                    "source_id": nid,
                    "target": tgt,
                    "target_id": tgt,
                    "weight": 1.0,
                })
                existing_edge_keys.add((nid, rel, tgt))
                bump("passage_edges_created")
            continue

        meta, form = parse_metadata(node)
        if meta.get(GREEK_MARKER):
            bump("passage_nodes_already_applied")
            continue
        old_desc = node.get("description") or ""
        old_label = node.get("label") or ""
        merged = dict(meta)
        merged.update(new_meta)
        merged["description_pre_greek_ingestion_2026_08_16"] = old_desc
        merged["label_pre_greek_ingestion_2026_08_16"] = old_label
        merged["citation_verdict"] = "corrected"
        note = (
            f"[Vérif. 2026-08-16 : the node held only the SC 268 FRENCH translation "
            f"of De princ. III.1.{n}"
            + (
                " while its label advertised 'Greek text' and metadata.language was "
                "'grc'" if "Greek" in old_label else ""
            )
            + ". The Greek is now ingested verbatim from the local TLG E disk "
            f"(TLG2042 work 002, bytes {sec['tlg_byte_span'][0]}-{sec['tlg_byte_span'][1]}, "
            f"= Koetschau GCS 22), collated against the SC 268 'Extraits grecs' file at "
            f"letter-similarity {sec['sc268_similarity']} and re-attested with "
            "scripts/tlg_search.py. The previous description and label are archived in "
            "metadata.description_pre_greek_ingestion_2026_08_16 / "
            "label_pre_greek_ingestion_2026_08_16.]"
        )
        append_note(merged, note)
        node["description"] = desc
        node["label"] = label
        node["updated_at"] = NOW
        dump_metadata(node, merged, form)
        bump("passage_nodes_enriched")
        log.append(f"enriched {nid} (+{len(sec['greek'])} Greek chars)")

    if not dry:
        apply_corpus(corpus_ids)


def apply_corpus(corpus_ids: dict[int, str]) -> None:
    passages = load_jsonl(PASSAGES_PATH)
    have = {p.get("passage_id") for p in passages}
    added = 0
    seq = 0
    for n in sorted(SECTIONS):
        seq += 1
        pid = corpus_ids[n]
        if pid in have:
            continue
        passages.append({
            "canonical_ref": f"De Princ. 3.1.{n}",
            "cts_urn": f"urn:cts:greekLit:tlg2042.tlg002:3.1.{n}",
            "passage_id": pid,
            "sequence_number": seq,
            "text_content": SECTIONS[n]["greek"],
            "work_canonical_id": CORPUS_WORK_GRC,
        })
        added += 1
    if added:
        dump_jsonl(PASSAGES_PATH, passages)
    bump("corpus_passages_added", added)

    citations = load_jsonl(CITATIONS_PATH)
    have_c = {(c.get("kg_node_id"), c.get("passage_id")) for c in citations}
    added_c = 0
    for n in sorted(SECTIONS):
        key = (f"passage_origen_philocalia_21_{n}", corpus_ids[n])
        if key in have_c:
            continue
        citations.append({
            "citation_type": "snapshot_passage_node",
            "confidence": 1.0,
            "kg_node_id": key[0],
            "passage_id": key[1],
        })
        added_c += 1
    if added_c:
        dump_jsonl(CITATIONS_PATH, citations)
    bump("corpus_citations_added", added_c)

    manifest = load_jsonl(MANIFEST_PATH)
    if not any(m.get("canonical_id") == CORPUS_WORK_GRC for m in manifest):
        manifest.append({
            "author": "Origen",
            "canonical_id": CORPUS_WORK_GRC,
            "cts_urn": "urn:cts:greekLit:tlg2042.tlg002",
            "ingest_class": "tlg_e_local",
            "passages": sum(
                1 for row in load_jsonl(PASSAGES_PATH)
                if row.get("work_canonical_id") == CORPUS_WORK_GRC
            ),
            "period": "Patristic",
            "source": (
                "tlge:TLG2042.TXT work 002 (Koetschau, GCS 22, Leipzig 1913) — 24 "
                "Greek sections III.1.1-24 ingested 2026-08-16; any further row "
                "under this id pre-dates this wave"
            ),
            "status": "in_corpus",
            "title": "De Principiis III.1 (Περὶ αὐτεξουσίου) — Greek",
        })
        dump_jsonl(MANIFEST_PATH, manifest)
        bump("corpus_manifest_rows_added")


# --- part B: historiography -------------------------------------------------


def apply_historiography(nodes: list[dict], edges: list[dict]) -> None:
    by_id = {node_id_of(n): n for n in nodes}

    for payload in NEW_NODES:
        nid = payload["id"]
        if nid in by_id:
            bump("hist_nodes_already_present")
            log.append(f"SKIP node {nid}: already present")
            continue
        meta = dict(payload["metadata"])
        meta[HIST_MARKER] = True
        nodes.append({
            "alternative_names": "[]",
            "created_at": NOW,
            "description": payload["description"],
            "id": nid,
            "label": payload["label"],
            "metadata": meta,
            "node_id": nid,
            "period": payload.get("period"),
            "role": payload.get("role"),
            "school": payload.get("school"),
            "type": payload["type"],
            "updated_at": NOW,
        })
        by_id[nid] = nodes[-1]
        bump("hist_nodes_created")
        log.append(f"created {nid} ({payload['type']})")

    for nid, spec in NODE_ENRICHMENTS.items():
        node = by_id.get(nid)
        if node is None:
            log.append(f"MISS enrichment target {nid}: not in nodes.jsonl")
            bump("hist_enrichment_targets_missing")
            continue
        meta, form = parse_metadata(node)
        if meta.get(HIST_MARKER) == HIST_REVISION:
            bump("hist_nodes_already_applied")
            continue
        for span_old, span_new in spec.get("description_replace", []):
            desc = node.get("description") or ""
            if desc.count(span_old) != 1:
                log.append(
                    f"SKIP description span on {nid}: found {desc.count(span_old)} "
                    "occurrences, expected exactly 1"
                )
                bump("hist_spans_skipped")
                continue
            node["description"] = desc.replace(span_old, span_new)
            bump("hist_description_spans_applied")
        for field, spans in spec.get("metadata_field_replace", {}).items():
            for span_old, span_new in spans:
                cur = meta.get(field) or ""
                if cur.count(span_old) != 1:
                    log.append(
                        f"SKIP metadata span {nid}.{field}: found "
                        f"{cur.count(span_old)} occurrences, expected exactly 1"
                    )
                    bump("hist_spans_skipped")
                    continue
                meta[field] = cur.replace(span_old, span_new)
                bump("hist_metadata_spans_applied")
        meta.update(spec.get("metadata_sets", {}))
        if spec.get("verification_note"):
            append_note(meta, spec["verification_note"])
        meta[HIST_MARKER] = HIST_REVISION
        meta.setdefault("wave", HIST_WAVE)
        node["updated_at"] = NOW
        dump_metadata(node, meta, form)
        bump("hist_nodes_enriched")
        log.append(f"enriched {nid}")

    known = set(by_id)
    existing = {
        (e.get("source") or e.get("source_id"), e.get("relation"),
         e.get("target") or e.get("target_id"))
        for e in edges
    }
    for spec in NEW_EDGES:
        key = (spec["source"], spec["relation"], spec["target"])
        if spec["source"] not in known or spec["target"] not in known:
            log.append(f"SKIP edge {key}: endpoint missing from nodes.jsonl")
            bump("hist_edges_skipped_missing_endpoint")
            continue
        if key in existing:
            bump("hist_edges_already_present")
            continue
        edges.append({
            "created_at": NOW,
            "edge_id": str(uuid.uuid4()),
            "metadata": spec.get("metadata", {}),
            "relation": spec["relation"],
            "source": spec["source"],
            "source_id": spec["source"],
            "target": spec["target"],
            "target_id": spec["target"],
            "weight": spec.get("weight", 1.0),
        })
        existing.add(key)
        bump("hist_edges_created")
        log.append(f"edge {spec['source']} --{spec['relation']}--> {spec['target']}")


# --- main -------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", choices=["greek", "historiography"])
    args = ap.parse_args()

    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    n0, e0 = len(nodes), len(edges)

    if args.only in (None, "greek"):
        apply_greek(nodes, edges, args.dry_run)
    if args.only in (None, "historiography"):
        apply_historiography(nodes, edges)

    ids = [node_id_of(n) for n in nodes]
    dupes = {i for i in ids if ids.count(i) > 1} if len(set(ids)) != len(ids) else set()
    if dupes:
        print(f"ABORT: duplicate node ids after apply: {sorted(dupes)[:10]}")
        return 1

    if not args.dry_run:
        dump_jsonl(NODES_PATH, nodes)
        dump_jsonl(EDGES_PATH, edges)

    for line in log:
        print(("[dry-run] " if args.dry_run else "") + line)
    print("\n--- stats ---")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    print(f"  nodes: {n0} -> {len(nodes)}")
    print(f"  edges: {e0} -> {len(edges)}")
    if args.dry_run:
        print("\n(dry run — nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
