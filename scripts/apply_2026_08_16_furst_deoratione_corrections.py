#!/usr/bin/env python3
"""Apply the 2026-08-16 Fürst / De oratione corrections to the local KG mirror.

Scope: `data/kg/nodes.jsonl` only — no edge is added, retargeted or deleted.

Four corrections, all authored in
`scripts/data_2026_08_16_furst_deoratione_corrections.py`, each `#`-commented
with the source that justifies it:

1. `scholarly_argument_f_rst_origen_s_libertarian_compatibi_4` — description,
   `stance`, `page_range` and `verified_reference` rewritten: the node carried
   Fürst's ch. V 3 content under the ch. VI 4 title and flattened his
   deliberately suspended verdict.
2. `concept_kompatibilistischer_libertarismus_origenian` and
   `argument_furst_2022_kompatibilistischer_libertarismus` — the claim that
   Origen's libertarianism stays compatible with "the Stoic chain of (physical)
   causes" is replaced by what Fürst 2022, 286-290 actually says (he rules out a
   Kausaldeterminismus in as many words); the suspended verdict is appended;
   "C. M. Fürst" → "A. Fürst".
3. `passage_origen_de_orat_6` — the recomposed Greek (0 TLG hits, labelled
   "GCS 3 Koetschau") is replaced by the verbatim De oratione 6,3 text from the
   local TLG E extract and archived under `metadata.removed_unattested_text`;
   `work_title` "Contra Celsum" → "De Oratione"; the twin
   `passage_origen_de_orat_6_en`, left as punctuation debris by an earlier
   Greek-stripping pass, is restored to a plain English rendering (its edges are
   kept).
4. `passage_origen_philocalia_21_23` — relabelled: the payload is a French
   translation, not the Greek the label advertised.

The script is deterministic and idempotent: touched nodes are stamped with
`metadata.furst_deoratione_corrections_2026_08_16` and a stamped node is skipped
on any later run. A span whose `old` text does not occur exactly once is
reported and skipped, never applied blind.

Usage:
    python3 scripts/apply_2026_08_16_furst_deoratione_corrections.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_16_furst_deoratione_corrections import (  # noqa: E402
    CITATION_VERIFIED_TRUE,
    FIELD_APPENDS,
    FIELD_REWRITES,
    FIELD_SETS,
    LABEL_REWRITES,
    LIST_SETS,
    REMOVED_TEXT_ARCHIVE,
    VERIFICATION_NOTES,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"

APPLIED_MARKER = "furst_deoratione_corrections_2026_08_16"

log: list[str] = []
stats: dict[str, int] = {}


def bump(key: str, n: int = 1) -> None:
    stats[key] = stats.get(key, 0) + n


# --- io ---------------------------------------------------------------------


def node_id_of(node: dict) -> str | None:
    return node.get("node_id") or node.get("id")


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


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
    # "opaque" -> leave untouched


# --- field addressing -------------------------------------------------------
# A field path is either "description" (node level) or "metadata.<key>".


def read_field(node: dict, meta: dict, path: str):
    if path.startswith("metadata."):
        return meta.get(path[len("metadata.") :])
    return node.get(path)


def write_field(node: dict, meta: dict, path: str, value) -> None:
    if path.startswith("metadata."):
        meta[path[len("metadata.") :]] = value
    else:
        node[path] = value


# --- edits ------------------------------------------------------------------


def do_rewrites(nid: str, node: dict, meta: dict) -> bool:
    changed = False
    for path, spans in FIELD_REWRITES.get(nid, {}).items():
        cur = read_field(node, meta, path)
        if not isinstance(cur, str):
            log.append(f"[SKIP-SPAN] {nid} ({path}): field absent or not a string")
            bump("spans_skipped")
            continue
        for old, new in spans:
            n = cur.count(old)
            if n != 1:
                log.append(
                    f"[SKIP-SPAN] {nid} ({path}): old text occurs {n}x — {old[:70]!r}"
                )
                bump("spans_skipped")
                continue
            cur = cur.replace(old, new, 1)
            bump("spans_applied")
            log.append(f"[SPAN] {nid} ({path}): {old[:60]!r} -> {new[:60]!r}…")
        if cur != read_field(node, meta, path):
            write_field(node, meta, path, cur)
            changed = True
    return changed


def do_appends(nid: str, node: dict, meta: dict) -> bool:
    changed = False
    for path, tail in FIELD_APPENDS.get(nid, {}).items():
        cur = read_field(node, meta, path)
        if not isinstance(cur, str):
            log.append(f"[SKIP-APPEND] {nid} ({path}): field absent or not a string")
            continue
        if tail.strip() in cur:
            log.append(f"[NOOP-APPEND] {nid} ({path}): tail already present")
            continue
        write_field(node, meta, path, cur.rstrip() + tail)
        log.append(f"[APPEND] {nid} ({path}): +{len(tail)} chars")
        bump("appends_applied")
        changed = True
    return changed


def do_sets(nid: str, node: dict, meta: dict) -> bool:
    changed = False
    for path, value in FIELD_SETS.get(nid, {}).items():
        before = read_field(node, meta, path)
        if before == value:
            log.append(f"[NOOP-SET] {nid} ({path}): already set")
            continue
        write_field(node, meta, path, value)
        log.append(
            f"[SET] {nid} ({path}): "
            f"{json.dumps(before, ensure_ascii=False)[:90]} -> "
            f"{json.dumps(value, ensure_ascii=False)[:90]}"
        )
        bump("fields_set")
        changed = True
    return changed


def do_list_sets(nid: str, meta: dict) -> bool:
    changed = False
    for key, value in LIST_SETS.get(nid, {}).items():
        before = meta.get(key)
        if before == value:
            log.append(f"[NOOP-LIST] {nid} ({key}): already set")
            continue
        meta[key] = list(value)
        log.append(
            f"[LIST] {nid} ({key}): "
            f"{json.dumps(before, ensure_ascii=False)} -> "
            f"{json.dumps(value, ensure_ascii=False)}"
        )
        bump("lists_set")
        changed = True
    return changed


def do_label(nid: str, node: dict) -> bool:
    if nid not in LABEL_REWRITES:
        return False
    old, new = LABEL_REWRITES[nid]
    if node.get("label") == new:
        log.append(f"[NOOP-LABEL] {nid}: already relabelled")
        return False
    if node.get("label") != old:
        log.append(f"[SKIP-LABEL] {nid}: label is {node.get('label')!r}")
        return False
    node["label"] = new
    log.append(f"[LABEL] {nid}: {old!r} -> {new!r}")
    bump("labels_rewritten")
    return True


def do_archive(nid: str, meta: dict) -> bool:
    archive = REMOVED_TEXT_ARCHIVE.get(nid)
    if archive is None:
        return False
    if meta.get("removed_unattested_text") == archive:
        log.append(f"[NOOP-ARCHIVE] {nid}: archive already present")
        return False
    meta["removed_unattested_text"] = json.loads(json.dumps(archive))
    log.append(f"[ARCHIVE] {nid}: removed text stored in removed_unattested_text")
    bump("archives_written")
    return True


def do_notes(nid: str, meta: dict) -> bool:
    notes = VERIFICATION_NOTES.get(nid, ())
    if not notes:
        return False
    existing = meta.get("verification_notes")
    if not isinstance(existing, list):
        existing = [existing] if existing else []
    changed = False
    for note in notes:
        if note in existing:
            log.append(f"[NOOP-NOTE] {nid}: note already recorded")
            continue
        existing.append(note)
        bump("notes_appended")
        changed = True
    if changed:
        meta["verification_notes"] = existing
        log.append(f"[NOTE] {nid}: verification_notes -> {len(existing)} entr(y|ies)")
    return changed


def do_citation_verified(nid: str, meta: dict) -> bool:
    if nid not in CITATION_VERIFIED_TRUE:
        return False
    if meta.get("citation_verified") is True:
        log.append(f"[NOOP-META] {nid}: citation_verified already True")
        return False
    before = meta.get("citation_verified", "<absent>")
    meta["citation_verified"] = True
    log.append(f"[META] {nid}: citation_verified: {before!r} -> True")
    bump("fields_set")
    return True


# --- main -------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    nodes = load_jsonl(NODES_PATH)
    before_nodes = len(nodes)
    by_id = {node_id_of(n): n for n in nodes}

    planned = (
        set(FIELD_REWRITES)
        | set(FIELD_APPENDS)
        | set(FIELD_SETS)
        | set(LIST_SETS)
        | set(LABEL_REWRITES)
        | set(REMOVED_TEXT_ARCHIVE)
        | set(VERIFICATION_NOTES)
        | set(CITATION_VERIFIED_TRUE)
    )
    for nid in sorted(planned - set(by_id)):
        log.append(f"[MISSING] {nid}: planned but not present in nodes.jsonl")
        bump("nodes_missing")

    for nid in sorted(planned & set(by_id)):
        node = by_id[nid]
        meta, form = parse_metadata(node)
        if form == "opaque":
            log.append(f"[SKIP-NODE] {nid}: metadata is not decodable JSON")
            bump("nodes_skipped")
            continue
        if meta.get(APPLIED_MARKER):
            log.append(f"[STAMPED] {nid}: already applied, skipping")
            bump("stamped_skipped")
            continue

        changed = False
        changed |= do_rewrites(nid, node, meta)
        changed |= do_appends(nid, node, meta)
        changed |= do_sets(nid, node, meta)
        changed |= do_list_sets(nid, meta)
        changed |= do_label(nid, node)
        changed |= do_archive(nid, meta)
        changed |= do_citation_verified(nid, meta)
        changed |= do_notes(nid, meta)

        if changed:
            meta[APPLIED_MARKER] = True
            dump_metadata(node, meta, form)
            bump("nodes_touched")
        else:
            log.append(f"[NOOP] {nid}: nothing to change")
            bump("nodes_unchanged")

    print("\n".join(log))
    print()
    print(f"nodes: {before_nodes} -> {len(nodes)}")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    dump_jsonl(NODES_PATH, nodes)
    print(f"\nwrote {NODES_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
