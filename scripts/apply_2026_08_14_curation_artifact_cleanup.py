#!/usr/bin/env python3
"""Apply the 2026-08-14 curator-artifact cleanup to the local KG mirror.

Reads the reviewed plan `data/audit/2026-08-14_curation_artifact_cleanup_plan.jsonl`
(one line per affected node + a trailing summary object) and applies, per node:

1. the authored prose rewrites carried by `data_2026_08_14_curation_rewrites`
   (`corrects_content` merges, `flags_spurious_reference` removals, wave/batch
   markers turned into real prose citations, curator prose dropped);
2. removal of the two `*(Phase 12)*` boilerplate paragraphs — the
   "Avertissement méthodologique" (variant A, 24 nodes) and the
   "Avertissement conceptuel — anachronisme du « libre arbitre »" (variant B,
   9 nodes). Variant B misattributes Dihle 1982's Augustine thesis to Origen,
   so it is deleted outright and NOT relocated to metadata;
3. removal of every `[Vérif. …]` tag from the reader-facing description, with
   its verbatim text appended to `metadata.verification_notes` so that no
   verification provenance is destroyed;
4. the single deletion voted by the plan
   (`scholarly_argument_fee_determinism_and_predestination_1`, a self-described
   extraction artifact) together with its 3 edges.

Nodes the plan marks out of scope (see SKIP_NODES) are left untouched.

The script is deterministic and idempotent: every rewritten node is stamped with
`metadata.curation_artifact_cleanup_2026_08_14`, and a stamped node is skipped on
any later run, so re-running never re-applies a span twice.

Usage:
    python3 scripts/apply_2026_08_14_curation_artifact_cleanup.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_14_curation_rewrites import (  # noqa: E402
    DESCRIPTION_EN_REWRITES,
    LABEL_REWRITES,
    METADATA_FIXES,
    REWRITES,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
PLAN_PATH = ROOT / "data" / "audit" / "2026-08-14_curation_artifact_cleanup_plan.jsonl"

# --- the two curator boilerplate paragraphs (byte-exact, verified in the plan) ---

BOILERPLATE_A = (
    "**Avertissement méthodologique** : la terminologie « compatibiliste / libertarienne / "
    "agent-causation / etc. » employée ci-dessous appartient au vocabulaire de la philosophie "
    "analytique moderne (Frankfurt 1969, Kane 1996, Pereboom 2001). Ces étiquettes sont "
    "rétroactivement projetées sur la pensée antique par des chercheurs modernes (Bobzien 1998, "
    "Frede 2011, Sorabji 1980) pour cartographier la position d'un auteur ancien dans le débat "
    "contemporain. Le concept ancien correspondant — ἑκούσιον, ἐφ' ἡμῖν, αὐτεξούσιον, liberum "
    "arbitrium — précède de plusieurs siècles la formation du « problème du libre arbitre » au "
    "sens analytique. Cf. Dihle 1982, *The Theory of Will in Classical Antiquity* ; Frede 2011, "
    "*A Free Will: Origins of the Notion*. *(Phase 12)*"
)

_BOILERPLATE_B_BODY = (
    "Avertissement conceptuel — anachronisme du « libre arbitre »** : la catégorie de « libre "
    "arbitre » (αὐτεξούσιον / liberum arbitrium) est, selon la thèse classique de Dihle 1982 — "
    "confirmée et nuancée par Bobzien 1998, Frede 2011, Fürst 2022 — une invention dogmatique "
    "chrétienne datant d'Origène (vers 230-250 ap. J.-C.). Les concepts anciens antérieurs — "
    "ἑκούσιον (volontaire) chez Aristote, ἐφ' ἡμῖν (ce qui dépend de nous) chez les Stoïciens et "
    "Académiques, voluntas libera chez Cicéron — recouvrent un champ conceptuel partiel et "
    "non-substitutif. Lorsque la présente description emploie « libre arbitre » / « free will » de "
    "manière apparemment naïve, il faut entendre une approximation lexicale moderne ; pour le "
    "contenu doctrinal exact de l'auteur ancien, voir le terme grec/latin propre. *(Phase 12)*"
)

BOILERPLATE_B = "**" + _BOILERPLATE_B_BODY
# `synthesis_cic_fat_in_nostra_potestate` carries the same text without the ** markers.
BOILERPLATE_B_PLAIN = _BOILERPLATE_B_BODY.replace(
    "« libre arbitre »** :", "« libre arbitre » :", 1
)

BOILERPLATES = (BOILERPLATE_A, BOILERPLATE_B, BOILERPLATE_B_PLAIN)

# --- the single deletion voted by the plan ---

DELETE_NODE_ID = "scholarly_argument_fee_determinism_and_predestination_1"
DELETE_EDGE_IDS = {
    "483ba42e-9ab4-4bc8-8aa9-194a1c9c5575",  # -created_by-> scholar_fee_g
    "51afafba-c8ce-4ead-9b5f-3fb719472be1",  # scholarly_work_fee_1994… -discusses->
    "6efb20b0-6ca2-4e02-8ae6-6f116d168808",  # -advanced_in-> scholarly_work_fee_1994…
}

# --- escalations: corpus-integrity problems, explicitly out of scope here ---

SKIP_NODES = {
    # label says Alcinous, Didasc. 1 but the 8.2k-char payload is Eusebius/Hegesippus
    # on James the Just. Needs its own verification pass, not a curation-artifact fix.
    "passage_alcin_alcinous_untitled_full_text",
}

VERIF_MARKER = "[Vérif."

# Stamped on every node the script rewrites, so a second run is a no-op instead of
# re-applying spans whose `old` text survives inside the rewritten prose.
APPLIED_MARKER = "curation_artifact_cleanup_2026_08_14"


def node_id_of(node: dict) -> str | None:
    return node.get("node_id") or node.get("id")


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_metadata(node: dict):
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
            if isinstance(inner, dict):
                return inner, "str2"
            return {}, "opaque"
        if isinstance(parsed, dict):
            return parsed, "str"
        return {}, "opaque"
    return {}, "none"


def dump_metadata(node: dict, meta: dict, form: str) -> None:
    if form == "dict":
        node["metadata"] = meta
    elif form == "str":
        node["metadata"] = json.dumps(meta, ensure_ascii=False)
    elif form == "str2":
        node["metadata"] = json.dumps(
            json.dumps(meta, ensure_ascii=False), ensure_ascii=False
        )
    elif form == "none":
        node["metadata"] = meta
    # "opaque" -> leave untouched


def find_bracketed(text: str, marker: str) -> list[tuple[int, int]]:
    """Spans of `marker`-introduced, bracket-balanced runs, e.g. '[Vérif. …]'."""
    spans: list[tuple[int, int]] = []
    i = 0
    while True:
        start = text.find(marker, i)
        if start < 0:
            return spans
        depth = 0
        end = start
        while end < len(text):
            if text[end] == "[":
                depth += 1
            elif text[end] == "]":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        spans.append((start, end + 1))
        i = end + 1


def remove_span(text: str, start: int, end: int) -> str:
    """Remove text[start:end] and heal the whitespace at the junction."""
    before, after = text[:start], text[end:]
    if not after.strip():
        return before.rstrip()
    if not before.strip():
        return after.lstrip()
    junction = re.search(r"\s*$", before).group() + re.match(r"\s*", after).group()
    if "\n\n" in junction:
        sep = "\n\n"
    elif "\n" in junction:
        sep = "\n"
    elif junction:
        sep = " "
    else:
        sep = ""
    return before.rstrip() + sep + after.lstrip()


def tidy(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def apply_rewrites(
    text: str, pairs, node_id: str, log: list[str]
) -> tuple[str, int, int]:
    applied = missed = 0
    for old, new in pairs:
        count = text.count(old)
        if count == 1:
            text = text.replace(old, new, 1)
            applied += 1
        elif count == 0:
            log.append(f"    [SKIP-NOMATCH] {node_id}: span not found: {old[:70]!r}")
            missed += 1
        else:
            log.append(
                f"    [SKIP-AMBIGUOUS] {node_id}: span occurs {count}x: {old[:70]!r}"
            )
            missed += 1
    return text, applied, missed


def strip_boilerplate(text: str) -> tuple[str, int]:
    removed = 0
    for block in BOILERPLATES:
        idx = text.find(block)
        while idx >= 0:
            text = remove_span(text, idx, idx + len(block))
            removed += 1
            idx = text.find(block)
    return text, removed


def strip_verif_tags(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    while True:
        spans = find_bracketed(text, VERIF_MARKER)
        if not spans:
            return text, notes
        start, end = spans[0]
        notes.append(text[start:end])
        text = remove_span(text, start, end)


def apply_metadata_fixes(
    meta: dict, fixes: list[dict], node_id: str, log: list[str]
) -> int:
    applied = 0
    for fix in fixes:
        key, op = fix["key"], fix["op"]
        if key not in meta:
            log.append(f"    [SKIP-META] {node_id}: metadata key {key!r} absent")
            continue
        if op == "list_remove":
            value = meta[key]
            if isinstance(value, list) and fix["value"] in value:
                value.remove(fix["value"])
                applied += 1
                log.append(
                    f"    [META] {node_id}: removed from {key}: {fix['value'][:70]!r}"
                )
            else:
                log.append(f"    [SKIP-META] {node_id}: element absent from {key}")
        elif op == "set":
            if meta[key] != fix["value"]:
                log.append(
                    f"    [META] {node_id}: {key}: {meta[key]!r} -> {fix['value']!r}"
                )
                meta[key] = fix["value"]
                applied += 1
        else:  # pragma: no cover - guarded by the data module
            raise ValueError(f"unknown metadata op {op!r}")
    return applied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    args = ap.parse_args()

    plan_rows = [row for row in load_jsonl(PLAN_PATH) if "node_id" in row]
    planned = {row["node_id"] for row in plan_rows}

    nodes = load_jsonl(NODES_PATH)
    before_count = len(nodes)

    log: list[str] = []
    stats = {
        "nodes_touched": 0,
        "prose_rewrites_applied": 0,
        "prose_rewrites_missed": 0,
        "boilerplate_removed": 0,
        "verif_tags_moved": 0,
        "description_en_rewrites": 0,
        "label_rewrites": 0,
        "metadata_fixes": 0,
        "skipped_escalation": 0,
        "already_applied": 0,
        "unchanged": 0,
    }

    seen = set()
    kept_nodes = []
    for node in nodes:
        nid = node_id_of(node)
        if nid == DELETE_NODE_ID:
            log.append(f"[DELETE] {nid} (self-described extraction artifact, plan §5)")
            continue
        kept_nodes.append(node)
        if nid not in planned:
            continue
        seen.add(nid)
        if nid in SKIP_NODES:
            stats["skipped_escalation"] += 1
            log.append(f"[ESCALATE-SKIP] {nid}: out of scope, left untouched")
            continue

        meta, form = parse_metadata(node)
        if meta.get(APPLIED_MARKER):
            stats["already_applied"] += 1
            log.append(f"[DONE-ALREADY] {nid}: cleanup already applied, skipped")
            continue

        original = node.get("description") or ""
        text = original
        entry_log: list[str] = []

        text, applied, missed = apply_rewrites(
            text, REWRITES.get(nid, ()), nid, entry_log
        )
        stats["prose_rewrites_applied"] += applied
        stats["prose_rewrites_missed"] += missed

        text, n_boiler = strip_boilerplate(text)
        stats["boilerplate_removed"] += n_boiler

        text, notes = strip_verif_tags(text)
        stats["verif_tags_moved"] += len(notes)

        text = tidy(text)
        if not text:
            raise SystemExit(f"ABORT: {nid} would end up with an empty description")

        meta_changed = False

        if notes:
            existing = meta.get("verification_notes")
            if not isinstance(existing, list):
                existing = [] if existing in (None, "") else [existing]
            for note in notes:
                if note not in existing:
                    existing.append(note)
            meta["verification_notes"] = existing
            meta_changed = True

        en_pairs = DESCRIPTION_EN_REWRITES.get(nid)
        if en_pairs and isinstance(meta.get("description_en"), str):
            new_en, en_applied, en_missed = apply_rewrites(
                meta["description_en"], en_pairs, nid + ".description_en", entry_log
            )
            stats["prose_rewrites_missed"] += en_missed
            new_en, _ = strip_boilerplate(new_en)
            new_en, en_notes = strip_verif_tags(new_en)
            new_en = tidy(new_en)
            if new_en != meta["description_en"]:
                meta["description_en"] = new_en
                meta_changed = True
                stats["description_en_rewrites"] += en_applied
            if en_notes:
                meta.setdefault("verification_notes", []).extend(en_notes)
                meta_changed = True

        label_pairs = LABEL_REWRITES.get(nid)
        label_changed = False
        if label_pairs and isinstance(node.get("label"), str):
            new_label, lab_applied, lab_missed = apply_rewrites(
                node["label"], label_pairs, nid + ".label", entry_log
            )
            stats["prose_rewrites_missed"] += lab_missed
            if new_label.strip() and new_label != node["label"]:
                entry_log.append(
                    f"    [LABEL] {nid}: {node['label']!r} -> {new_label!r}"
                )
                node["label"] = new_label.strip()
                label_changed = True
                stats["label_rewrites"] += lab_applied

        fixes = METADATA_FIXES.get(nid)
        if fixes:
            n_fixed = apply_metadata_fixes(meta, fixes, nid, entry_log)
            stats["metadata_fixes"] += n_fixed
            meta_changed = meta_changed or bool(n_fixed)

        changed = text != original or meta_changed or label_changed
        if changed:
            meta[APPLIED_MARKER] = True
            meta_changed = True
            node["description"] = text
            if meta_changed:
                dump_metadata(node, meta, form)
            stats["nodes_touched"] += 1
            log.append(
                f"[NODE] {nid}: rewrites={applied} boilerplate={n_boiler} "
                f"verif_tags->metadata={len(notes)} "
                f"desc {len(original)}->{len(text)} chars"
            )
        else:
            stats["unchanged"] += 1
            log.append(f"[NOOP] {nid}: nothing to change")
        log.extend(entry_log)

    unseen = planned - seen - {DELETE_NODE_ID}
    for nid in sorted(unseen):
        log.append(f"[MISSING] {nid}: planned but not present in nodes.jsonl")

    edges = load_jsonl(EDGES_PATH)
    kept_edges = []
    dropped_edges = 0
    for edge in edges:
        if edge.get("edge_id") in DELETE_EDGE_IDS or DELETE_NODE_ID in (
            edge.get("source"),
            edge.get("source_id"),
            edge.get("target"),
            edge.get("target_id"),
        ):
            dropped_edges += 1
            log.append(
                f"[DELETE-EDGE] {edge.get('edge_id')} "
                f"{edge.get('source_id')} -{edge.get('relation')}-> {edge.get('target_id')}"
            )
            continue
        kept_edges.append(edge)

    print("\n".join(log))
    print()
    print(f"nodes: {before_count} -> {len(kept_nodes)} (deleted 1)")
    print(f"edges: {len(edges)} -> {len(kept_edges)} (deleted {dropped_edges})")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    dump_jsonl(NODES_PATH, kept_nodes)
    dump_jsonl(EDGES_PATH, kept_edges)
    print(f"\nwrote {NODES_PATH.relative_to(ROOT)} and {EDGES_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
