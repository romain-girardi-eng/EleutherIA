#!/usr/bin/env python3
"""Wave 6: linguistic repairs from the 2026-08-16 deep audit.

See ``data_2026_08_17_linguistic_repairs.py`` for the evidence behind each edit —
every Greek replacement carries the TLG E byte range it was decoded from.

Nothing is written blind. Every write states a precondition first: the text still
contains the corruption, the URN still holds the wrong TLG id, the language still
detects as something other than what the node declares. When a precondition
fails the item is SKIPPED and reported, never forced. Re-running is a no-op.

Usage:
    python3 scripts/apply_2026_08_17_linguistic_repairs.py            # dry run
    python3 scripts/apply_2026_08_17_linguistic_repairs.py --apply    # write
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_linguistic_repairs import (  # noqa: E402
    APPARATUS_RULE,
    CLEMENT_PROTREPTICUS_FLAG,
    COMPOSITE_TEXT_RULE,
    EXHORTATIO_ID_DEBT,
    EXHORTATIO_REATTRIBUTION,
    GRC_WITHOUT_GREEK_RULE,
    LAT_WITHOUT_LATIN_RULE,
    MAGNA_MORALIA_REPAIRS,
    MAGNA_MORALIA_UNRESOLVED,
    PLOTINUS_EXPECTED,
    PLOTINUS_FALSE_URN,
    PLOTINUS_FLAG,
    PLOTINUS_ID_PATTERN,
    PLOTINUS_REF_PATTERN,
    PLOTINUS_WORK_URN,
    PRE_UNICODE_CORPUS_IDS,
    PRE_UNICODE_FLAG,
    PRE_UNICODE_KG_NODES,
    SIMPLICIUS_WORK_FLAG,
    SIMPLICIUS_WORK_NODE,
    THEOPHRASTUS_EXPECTED_EDGE_COUNT,
    THEOPHRASTUS_MISFILED_CORPUS_IDS,
    THEOPHRASTUS_MISFILED_NODES,
    TOKEN_REPAIRS,
    URN_FAMILY_REWRITES,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
CORPUS_PATH = ROOT / "data" / "corpus" / "passages.jsonl"
AUDIT_IDS = ROOT / "data" / "audit" / "2026-08-16_deep_audit_linguistic.jsonl"

STAMP = "linguistic_repairs_2026_08_17"
BACKUP_SUFFIX = ".bak-linguistic"

GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
LATIN = re.compile(r"[A-Za-z]")
WORDS = re.compile(r"[a-zA-ZäöüßàâçéèêëîïôûùüÿœæÀÂÇÉÈÊËÎÏÔÛÙÜ']+")

LAT_WORDS = frozenset(
    [
        "quod",
        "enim",
        "autem",
        "non",
        "sed",
        "est",
        "ut",
        "in",
        "ad",
        "cum",
        "qui",
        "quae",
        "hoc",
        "esse",
        "etiam",
        "nam",
        "per",
        "si",
        "atque",
        "nec",
        "ex",
        "quia",
        "ipse",
        "omnia",
    ]
)
FRA_WORDS = frozenset(
    [
        "le",
        "la",
        "les",
        "des",
        "une",
        "dans",
        "est",
        "pour",
        "que",
        "qui",
        "plus",
        "sur",
        "avec",
        "cette",
        "nous",
        "par",
        "aux",
        "ainsi",
        "mais",
        "donc",
        "entre",
        "selon",
        "car",
        "il",
        "elle",
        "ce",
    ]
)
DEU_WORDS = frozenset(
    [
        "und",
        "der",
        "die",
        "das",
        "nicht",
        "ist",
        "mit",
        "von",
        "den",
        "dem",
        "auch",
        "wird",
        "sich",
        "aber",
        "nach",
        "oder",
        "wie",
        "zur",
        "zum",
        "ein",
        "eine",
        "nämlich",
        "wohl",
        "vgl",
        "statt",
        "fehlt",
    ]
)

log: list[str] = []
counts: dict[str, int] = {}


def note(op: str, msg: str) -> None:
    log.append(f"[{op}] {msg}")
    counts[op] = counts.get(op, 0) + 1


def skip(op: str, msg: str) -> None:
    log.append(f"[{op}] SKIPPED: {msg}")
    key = op + "__skipped"
    counts[key] = counts.get(key, 0) + 1


# --------------------------------------------------------------------------- io
def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def nid(node: dict) -> str:
    return node.get("node_id") or node.get("id") or ""


def meta(node: dict) -> dict:
    """Some nodes store metadata as a JSON *string*; read either shape."""
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def set_meta(node: dict, data: dict) -> None:
    """Write metadata back in the same shape it was read in."""
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(data, ensure_ascii=False)
    else:
        node["metadata"] = data


def stamp(node: dict, op: str, why: str) -> None:
    data = meta(node)
    data[STAMP] = op
    data[f"{STAMP}_note"] = why
    set_meta(node, data)


def stamped(node: dict, op: str) -> bool:
    return meta(node).get(STAMP) == op


def body(node: dict) -> str:
    return (node.get("description") or "") or (meta(node).get("text_content") or "")


def set_body(node: dict, text: str) -> None:
    if node.get("description"):
        node["description"] = text
    else:
        data = meta(node)
        data["text_content"] = text
        set_meta(node, data)


# ------------------------------------------------------------------- detection
def word_counts(text: str) -> dict[str, int]:
    words = [w for w in WORDS.findall(text.lower()) if len(w) > 1]
    if not words:
        return {"_n": 0, "lat": 0, "fra": 0, "deu": 0}
    return {
        "_n": len(words),
        "lat": sum(1 for w in words if w in LAT_WORDS),
        "fra": sum(1 for w in words if w in FRA_WORDS),
        "deu": sum(1 for w in words if w in DEU_WORDS),
    }


def detect(text: str) -> str | None:
    """Coarse but conservative: name a language only on 3+ function words."""
    wc = word_counts(text)
    best = max(("lat", "fra", "deu"), key=lambda k: wc[k])
    return best if wc[best] >= 3 else None


def greek_chars(text: str) -> int:
    return len(GREEK.findall(text))


def latin_chars(text: str) -> int:
    return len(LATIN.findall(text))


# ============================================================================ 1
def repair_magna_moralia(nodes_by_id: dict[str, dict], corpus: list[dict]) -> None:
    """Replace OCR-mangled Magna Moralia Greek with the TLG E reading."""
    op = "repair_magna_moralia"
    corpus_by_id = {row.get("passage_id"): row for row in corpus}

    for node_id, spec in MAGNA_MORALIA_REPAIRS.items():
        node = nodes_by_id.get(node_id)
        if node is None:
            skip(op, f"{node_id}: node not found")
            continue
        if stamped(node, op):
            continue  # idempotent
        current = body(node)
        # Precondition 1: the corruption this repair targets is still present.
        if "??" not in current and "**" not in current:
            skip(op, f"{node_id}: no '??'/'**' left in the text — already repaired?")
            continue
        # Precondition 2: the node is still the passage the alignment was run on.
        data = meta(node)
        if data.get("canonical_ref") != spec["canonical_ref"]:
            skip(
                op,
                f"{node_id}: canonical_ref is {data.get('canonical_ref')!r}, "
                f"expected {spec['canonical_ref']!r}",
            )
            continue
        if data.get("db_passage_id") != spec["db_passage_id"]:
            skip(op, f"{node_id}: db_passage_id moved")
            continue
        # Precondition 3: the replacement is clean Greek.
        new = unicodedata.normalize("NFC", spec["text"])
        solid = [c for c in new if not c.isspace()]
        gfrac = greek_chars(new) / max(1, len(solid))
        if "?" in new or gfrac < 0.90:
            skip(op, f"{node_id}: replacement failed the Greek gate ({gfrac:.2f})")
            continue

        node["description"] = new
        data["char_length"] = len(new)
        data["word_count"] = len(new.split())
        data["tlg_anchor"] = {
            "file": "TLG0086.TXT",
            "bytes": list(spec["tlg_bytes"]),
            "work": "tlg0086.tlg022 Magna moralia",
        }
        set_meta(node, data)
        stamp(
            node,
            op,
            "OCR-corrupted Greek replaced by the TLG E reading of the same "
            f"passage (TLG0086 bytes {spec['tlg_bytes'][0]}-{spec['tlg_bytes'][1]})",
        )
        note(op, f"{node_id}: {spec['old_len']} -> {len(new)} chars")

        twin = corpus_by_id.get(spec["db_passage_id"])
        if twin is None:
            skip(op + "_corpus", f"{node_id}: corpus twin not found")
        elif "??" not in (twin.get("text_content") or ""):
            skip(op + "_corpus", f"{node_id}: corpus twin already clean")
        else:
            twin["text_content"] = new
            note(op + "_corpus", f"{spec['db_passage_id']}: text_content replaced")

    for node_id, why in MAGNA_MORALIA_UNRESOLVED:
        node = nodes_by_id.get(node_id)
        if node is None or stamped(node, "flag_needs_reingestion"):
            continue
        data = meta(node)
        data["needs_reingestion"] = True
        set_meta(node, data)
        stamp(node, "flag_needs_reingestion", why)
        note("flag_needs_reingestion", node_id)


# =========================================================================== 1b
def repair_tokens(nodes_by_id: dict[str, dict]) -> None:
    """Surgical substitutions where the surrounding text is sound."""
    op = "repair_tokens"
    for spec in TOKEN_REPAIRS:
        node = nodes_by_id.get(spec["node"])
        if node is None:
            skip(op, f"{spec['node']}: node not found")
            continue
        current = body(node)
        if spec["old"] not in current:
            if spec["new"] in current:
                continue  # already applied
            skip(op, f"{spec['node']}: {spec['old']!r} not found in the text")
            continue
        set_body(node, current.replace(spec["old"], spec["new"]))
        data = meta(node)
        fixes = data.get(f"{STAMP}_token_fixes") or []
        fixes.append(f"{spec['old']} -> {spec['new']} ({spec['tlg']}): {spec['why']}")
        data[f"{STAMP}_token_fixes"] = fixes
        set_meta(node, data)
        stamp(node, op, "OCR-lost characters restored from TLG E")
        note(op, f"{spec['node']}: {spec['old']!r} -> {spec['new']!r}")


# ============================================================================ 2
def remove_theophrastus(
    nodes: list[dict], edges: list[dict], corpus: list[dict]
) -> tuple[list[dict], list[dict], list[dict]]:
    """Delete the nine Historia Plantarum passages filed under Simplicius."""
    op = "remove_theophrastus_misfiling"
    present = {nid(n) for n in nodes}
    doomed = {i for i in THEOPHRASTUS_MISFILED_NODES if i in present}
    if not doomed:
        return nodes, edges, corpus  # idempotent

    missing = set(THEOPHRASTUS_MISFILED_NODES) - doomed
    if missing:
        skip(op, f"already absent: {sorted(missing)}")

    # Precondition: the text really is botany, not Simplicius. Checked node by
    # node against the marker vocabulary of the Historia Plantarum.
    botanical = re.compile(r"φυτ|δένδρ|θάμν|καρπ|φύλλ|ῥίζ|σπέρμ|βλαστ|φλοι")
    for node in nodes:
        if nid(node) not in doomed:
            continue
        if not botanical.search(body(node)):
            skip(op, f"{nid(node)}: no botanical vocabulary — refusing to delete")
            doomed.discard(nid(node))

    touching = [e for e in edges if e["source"] in doomed or e["target"] in doomed]
    if len(doomed) == len(THEOPHRASTUS_MISFILED_NODES) and (
        len(touching) != THEOPHRASTUS_EXPECTED_EDGE_COUNT
    ):
        skip(
            op,
            f"expected {THEOPHRASTUS_EXPECTED_EDGE_COUNT} edges on these nodes, "
            f"found {len(touching)} — refusing to delete",
        )
        return nodes, edges, corpus

    nodes = [n for n in nodes if nid(n) not in doomed]
    edges = [
        e for e in edges if e["source"] not in doomed and e["target"] not in doomed
    ]
    note(op, f"deleted {len(doomed)} nodes and {len(touching)} edges")

    doomed_corpus = set(THEOPHRASTUS_MISFILED_CORPUS_IDS)
    before = len(corpus)
    corpus = [r for r in corpus if r.get("passage_id") not in doomed_corpus]
    note(op + "_corpus", f"deleted {before - len(corpus)} corpus lines")
    return nodes, edges, corpus


def flag_work(nodes_by_id: dict[str, dict], node_id: str, spec: dict, op: str) -> None:
    node = nodes_by_id.get(node_id)
    if node is None:
        skip(op, f"{node_id}: node not found")
        return
    data = meta(node)
    if data.get("needs_text_ingestion") is True and data.get(STAMP) == op:
        return
    data["needs_text_ingestion"] = True
    set_meta(node, data)
    stamp(node, op, spec["why"])
    note(op, node_id)


# ============================================================================ 3
def rewrite_urn_families(nodes: list[dict]) -> None:
    """Repoint CTS URNs that name a TLG author or work the text is not."""
    op = "rewrite_cts_urn"
    for family in URN_FAMILY_REWRITES:
        hits = 0
        for node in nodes:
            data = meta(node)
            urn = data.get("cts_urn")
            if not isinstance(urn, str) or not urn.startswith(family["old_prefix"]):
                continue
            # Precondition: the node is from the family this rewrite describes.
            if not nid(node).startswith(family["id_prefix"]):
                skip(
                    op,
                    f"{nid(node)}: carries {family['old_prefix']} but its id is "
                    f"outside {family['id_prefix']}*",
                )
                continue
            new_urn = family["new_prefix"] + urn[len(family["old_prefix"]) :]
            data["cts_urn"] = new_urn
            history = data.get(f"{STAMP}_urn_history") or []
            history.append(f"{urn} -> {new_urn}: {family['why']}")
            data[f"{STAMP}_urn_history"] = history
            set_meta(node, data)
            hits += 1
        if hits == 0:
            skip(op, f"{family['name']}: nothing carries {family['old_prefix']}")
        elif hits != family["expected"]:
            note(
                op,
                f"{family['name']}: rewrote {hits} URNs "
                f"(audit expected {family['expected']})",
            )
        else:
            note(op, f"{family['name']}: rewrote {hits} URNs")
        counts[f"{op}__{family['name']}"] = hits


# =========================================================================== 3d
def reattribute_exhortatio(nodes_by_id: dict[str, dict], edges: list[dict]) -> None:
    """The 51 'Clement, Protrepticus' passages are Origen's Exhortatio."""
    op = "reattribute_exhortatio"
    spec = EXHORTATIO_REATTRIBUTION
    targets = [
        n for i, n in nodes_by_id.items() if re.fullmatch(spec["id_prefix"] + r"\d+", i)
    ]
    if not targets:
        skip(op, "no passage_clement_protr_* nodes found")
        return
    if len(targets) != spec["expected"]:
        skip(op, f"expected {spec['expected']} nodes, found {len(targets)}")
        return
    for endpoint in (spec["right_person_node"], spec["right_work_node"]):
        if endpoint not in nodes_by_id:
            skip(op, f"target node {endpoint} does not exist")
            return

    for node in targets:
        if stamped(node, op):
            continue
        data = meta(node)
        # Precondition: the URN really is Origen's Exhortatio, and the node
        # really still claims Clement.
        if not str(data.get("cts_urn", "")).startswith(spec["urn"]):
            skip(op, f"{nid(node)}: cts_urn is {data.get('cts_urn')!r}")
            continue
        if data.get("author") != spec["wrong_author"]:
            skip(op, f"{nid(node)}: author is {data.get('author')!r}")
            continue
        n = nid(node).rsplit("_", 1)[1]
        data["author"] = spec["right_author"]
        data["work_title"] = spec["right_work_title"]
        data["canonical_ref"] = spec["ref_template"].format(n=n)
        data["id_debt"] = EXHORTATIO_ID_DEBT
        set_meta(node, data)
        node["label"] = spec["label_template"].format(n=n)
        stamp(node, op, spec["evidence"])
        note(op, f"{nid(node)}: Clement/Protrepticus -> Origen/Exhortatio")

    moved = 0
    for edge in edges:
        if not re.fullmatch(spec["id_prefix"] + r"\d+", edge.get("source", "")):
            continue
        if (
            edge["relation"] == "authored_by"
            and edge["target"] == spec["wrong_person_node"]
        ):
            edge["target"] = edge["target_id"] = spec["right_person_node"]
            moved += 1
        elif (
            edge["relation"] == "part_of" and edge["target"] == spec["wrong_work_node"]
        ):
            edge["target"] = edge["target_id"] = spec["right_work_node"]
            moved += 1
        else:
            continue
        data = edge.get("metadata")
        if isinstance(data, dict):
            data[STAMP] = op
            data[f"{STAMP}_note"] = spec["evidence"]
    if moved:
        note(op + "_edges", f"re-pointed {moved} edges")


# ============================================================================ 4
def flag_pre_unicode(nodes_by_id: dict[str, dict]) -> None:
    op = "flag_pre_unicode_font"
    for node_id, where in PRE_UNICODE_KG_NODES:
        node = nodes_by_id.get(node_id)
        if node is None:
            skip(op, f"{node_id}: node not found")
            continue
        if stamped(node, op):
            continue
        data = meta(node)
        data["pre_unicode_font"] = True
        data["needs_reocr"] = True
        data["pre_unicode_locus"] = where
        set_meta(node, data)
        stamp(node, op, PRE_UNICODE_FLAG["why"])
        note(op, node_id)
    counts[op + "__corpus_lines_listed_only"] = len(PRE_UNICODE_CORPUS_IDS)


# ============================================================================ 5
def audit_candidates() -> dict[str, list[str]]:
    """Group the audit's own findings by the defect they name."""
    groups: dict[str, list[str]] = {}
    if not AUDIT_IDS.exists():
        return groups
    for row in read_jsonl(AUDIT_IDS):
        if row.get("field") != "metadata.language":
            continue
        issue = row.get("issue", "")
        if "déclaré lat" in issue:
            key = "lat_no_latin"
        elif "déclaré grc mais aucun grec" in issue:
            key = "grc_no_greek"
        elif "traduction anglaise" in issue:
            key = "en_untranslated"
        else:
            continue
        groups.setdefault(key, []).append(row["id"])
    return groups


def requalify_languages(nodes: list[dict], nodes_by_id: dict[str, dict]) -> None:
    groups = audit_candidates()

    # --- 5a: lat nodes ------------------------------------------------------
    op = "requalify_lat"
    for node_id in groups.get("lat_no_latin", []):
        node = nodes_by_id.get(node_id)
        if node is None:
            skip(op, f"{node_id}: node not found")
            continue
        if node.get("type") != "passage":
            # On a person or work node `metadata.language` names the language the
            # author wrote in, not the language of the description. Not a defect.
            skip(op, f"{node_id}: type is {node.get('type')!r}, not a passage")
            continue
        data = meta(node)
        if data.get("language") not in LAT_WITHOUT_LATIN_RULE["requires_declared"]:
            skip(op, f"{node_id}: language is {data.get('language')!r}")
            continue
        text = body(node)
        # Re-detection, now, on the live text — this is the whole point.
        if word_counts(text)["lat"] == 0 and "LATIN TEXT" not in text:
            if stamped(node, op):
                continue
            data["language"] = LAT_WITHOUT_LATIN_RULE["set_language"]
            data.update(LAT_WITHOUT_LATIN_RULE["set_flags"])
            set_meta(node, data)
            stamp(node, op, LAT_WITHOUT_LATIN_RULE["why"])
            note(op, f"{node_id}: lat -> eng, needs_text_ingestion")
        else:
            if data.get("content_kind") == "commentary_plus_text":
                continue
            data.update(COMPOSITE_TEXT_RULE["set_flags"])
            set_meta(node, data)
            counts["mark_composite_latin"] = counts.get("mark_composite_latin", 0) + 1

    # --- 5b: the _en batch --------------------------------------------------
    op = "requalify_en"
    for node_id in groups.get("en_untranslated", []):
        node = nodes_by_id.get(node_id)
        if node is None:
            skip(op, f"{node_id}: node not found")
            continue
        data = meta(node)
        if data.get("passage_role") == "untranslated_duplicate":
            counts[op + "__already_fixed"] = counts.get(op + "__already_fixed", 0) + 1
            continue
        if data.get("language") != "eng":
            skip(op, f"{node_id}: language is {data.get('language')!r}")
            continue
        skip(op, f"{node_id}: still declares eng but was not handled in 2026-08-16")

    # --- 5c: grc nodes with no Greek ---------------------------------------
    op = "requalify_grc"
    by_urn: dict[str, list[dict]] = {}
    for node in nodes:
        urn = meta(node).get("cts_urn")
        if isinstance(urn, str):
            by_urn.setdefault(urn, []).append(node)

    apparatus_ids = {
        nid(n)
        for n in nodes
        if re.fullmatch(APPARATUS_RULE["id_pattern"], nid(n))
        and word_counts(body(n))["deu"] >= APPARATUS_RULE["min_german_words"]
        and re.search(APPARATUS_RULE["marker_pattern"], body(n))
    }

    for node_id in groups.get("grc_no_greek", []):
        node = nodes_by_id.get(node_id)
        if node is None:
            skip(op, f"{node_id}: node not found")
            continue
        if node_id in apparatus_ids:
            continue  # handled by the apparatus rule below
        if node.get("type") != "passage":
            skip(op, f"{node_id}: type is {node.get('type')!r}, not a passage")
            continue
        data = meta(node)
        if data.get("language") not in GRC_WITHOUT_GREEK_RULE["requires_declared"]:
            skip(op, f"{node_id}: language is {data.get('language')!r}")
            continue
        text = body(node)
        if greek_chars(text) > 0:
            skip(op, f"{node_id}: contains {greek_chars(text)} Greek characters")
            continue
        found = detect(text)
        if found is None:
            skip(op, f"{node_id}: language could not be re-detected")
            continue
        if stamped(node, op):
            continue

        data["language"] = found
        pairing = GRC_WITHOUT_GREEK_RULE["translation_pairing"]
        original = None
        for cand in by_urn.get(data.get("cts_urn"), []):
            if nid(cand) == node_id:
                continue
            if meta(cand).get("language") != pairing["require_target_language"]:
                continue
            if greek_chars(body(cand)) < 20:
                continue
            if body(cand).strip() == text.strip():
                continue
            original = cand
            break
        if original is not None:
            data["passage_role"] = "translation"
            data["original_node_id"] = nid(original)
            why = (
                f"declared {GRC_WITHOUT_GREEK_RULE['requires_declared'][0]} while "
                f"holding the modern {found} translation; the Greek original is "
                f"{nid(original)}, matched on the identical CTS URN "
                f"{data.get('cts_urn')}"
            )
        else:
            data["content_kind"] = "modern_translation"
            data["needs_text_ingestion"] = True
            why = (
                f"declared as Greek while holding a modern {found} translation; "
                "no Greek original for this locus exists in the graph, so the "
                "node keeps passage_role=original (R7 forbids a translation with "
                "no resolvable original) and is queued for text ingestion"
            )
        set_meta(node, data)
        stamp(node, op, why)
        note(op, f"{node_id}: -> {found}" + (" + translation link" if original else ""))

    # --- 5d: the GCS apparatus ---------------------------------------------
    op = "mark_apparatus_gcs"
    for node in nodes:
        if nid(node) not in apparatus_ids:
            continue
        if stamped(node, op):
            continue
        data = meta(node)
        data["language"] = APPARATUS_RULE["set_language"]
        data.update(APPARATUS_RULE["set_flags"])
        set_meta(node, data)
        stamp(node, op, APPARATUS_RULE["why"])
        note(op, nid(node))


# ============================================================================ 6
def normalise_edges_nfc(edges: list[dict]) -> None:
    op = "normalise_nfc"
    for edge in edges:
        raw = json.dumps(edge, ensure_ascii=False)
        fixed = unicodedata.normalize("NFC", raw)
        if fixed == raw:
            continue
        edge.clear()
        edge.update(json.loads(fixed))
        counts[op] = counts.get(op, 0) + 1
    if counts.get(op):
        note(op + "_done", f"{counts[op]} edge records normalised to NFC")


# ============================================================================ 7
def flag_plotinus(nodes: list[dict]) -> None:
    op = "flag_plotinus_fragment_refs"
    hits = 0
    for node in nodes:
        if not re.fullmatch(PLOTINUS_ID_PATTERN, nid(node)):
            continue
        data = meta(node)
        if data.get("needs_reference_remapping") is True:
            continue
        ref = data.get("canonical_ref")
        match = re.fullmatch(PLOTINUS_REF_PATTERN, str(ref))
        if match is None:
            skip(op, f"{nid(node)}: canonical_ref is {ref!r}")
            continue
        if data.get("cts_urn") != PLOTINUS_FALSE_URN:
            skip(op, f"{nid(node)}: cts_urn is {data.get('cts_urn')!r}")
            continue
        data["source_fragment_index"] = int(match.group(1))
        data["canonical_ref"] = None
        data["cts_urn"] = PLOTINUS_WORK_URN
        data["needs_reference_remapping"] = True
        set_meta(node, data)
        stamp(node, op, PLOTINUS_FLAG["why"])
        hits += 1
    counts[op] = hits
    if hits and hits != PLOTINUS_EXPECTED:
        note(op, f"flagged {hits} nodes (audit expected {PLOTINUS_EXPECTED})")


# ====================================================================== driver
def check_invariants(nodes: list[dict], edges: list[dict], corpus: list[dict]) -> None:
    ids = [nid(n) for n in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids"
    present = set(ids)
    dangling = [
        e for e in edges if e["source"] not in present or e["target"] not in present
    ]
    assert not dangling, f"{len(dangling)} dangling edges"
    split = [
        e
        for e in edges
        if e["source"] != e.get("source_id") or e["target"] != e.get("target_id")
    ]
    assert not split, (
        f"{len(split)} edges with source/source_id or target/target_id split"
    )
    triples = [(e["source"], e["relation"], e["target"]) for e in edges]
    assert len(triples) == len(set(triples)), "duplicate triples"
    assert not [e for e in edges if e["source"] == e["target"]], "self-loops"

    corpus_ids = [r.get("passage_id") for r in corpus]
    assert len(corpus_ids) == len(set(corpus_ids)), "duplicate corpus passage_ids"

    # No node this wave rewrote may still carry the corruption it targeted.
    leftover = [
        n
        for n in nodes
        if meta(n).get(STAMP) == "repair_magna_moralia" and "??" in body(n)
    ]
    assert not leftover, f"{len(leftover)} repaired nodes still contain '??'"

    # No node this wave rewrote may have lost its Greek.
    thin = [
        n
        for n in nodes
        if meta(n).get(STAMP) == "repair_magna_moralia"
        and greek_chars(body(n)) < 0.8 * len([c for c in body(n) if not c.isspace()])
    ]
    assert not thin, f"{len(thin)} repaired nodes are under 80% Greek"


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True)
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry_run = not args.apply

    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    corpus = read_jsonl(CORPUS_PATH)
    before = (len(nodes), len(edges), len(corpus))

    by_id = {nid(n): n for n in nodes}

    repair_magna_moralia(by_id, corpus)
    repair_tokens(by_id)

    nodes, edges, corpus = remove_theophrastus(nodes, edges, corpus)
    by_id = {nid(n): n for n in nodes}
    flag_work(by_id, SIMPLICIUS_WORK_NODE, SIMPLICIUS_WORK_FLAG, "flag_simplicius_work")

    rewrite_urn_families(nodes)
    reattribute_exhortatio(by_id, edges)
    flag_work(
        by_id,
        CLEMENT_PROTREPTICUS_FLAG["node"],
        CLEMENT_PROTREPTICUS_FLAG,
        "flag_clement_protrepticus",
    )

    flag_pre_unicode(by_id)
    requalify_languages(nodes, by_id)
    normalise_edges_nfc(edges)
    flag_plotinus(nodes)

    check_invariants(nodes, edges, corpus)

    print(
        f"nodes {before[0]} -> {len(nodes)}   "
        f"edges {before[1]} -> {len(edges)}   "
        f"corpus {before[2]} -> {len(corpus)}"
    )
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print("invariants: OK")

    if dry_run:
        print("\n--dry-run (default): nothing written. Pass --apply to write.")
        return 0

    for path in (NODES_PATH, EDGES_PATH, CORPUS_PATH):
        shutil.copyfile(path, path.with_suffix(path.suffix + BACKUP_SUFFIX))
    write_jsonl(NODES_PATH, nodes)
    write_jsonl(EDGES_PATH, edges)
    write_jsonl(CORPUS_PATH, corpus)

    report = ROOT / "data" / "audit" / "2026-08-17_linguistic_repairs_applied.md"
    report.write_text(
        "# Linguistic repairs (wave 6) — applied 2026-08-17\n\n"
        f"nodes {before[0]} -> {len(nodes)}, edges {before[1]} -> {len(edges)}, "
        f"corpus {before[2]} -> {len(corpus)}\n\n"
        + "\n".join(f"- {line}" for line in log)
        + "\n",
        encoding="utf-8",
    )
    print(
        f"\nwrote {NODES_PATH}\nwrote {EDGES_PATH}\nwrote {CORPUS_PATH}\nwrote {report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
