#!/usr/bin/env python3
"""Apply the 2026-08-16 second curation sweep to the local KG mirror.

The 2026-08-14 curator-artifact cleanup (commit be4c085) deliberately stayed
inside the reader-facing fields and archived every `[Vérif. …]` tag into
`metadata.verification_notes`. Its review file
`data/audit/2026-08-14_curation_artifact_cleanup_applied.md` left five explicit
follow-up piles. This script closes them:

1. metadata-field defects the archived tags name (fabricated `sources` arrays,
   impossible Bruns loci, DOIs that are not DOIs, extraction line numbers stored
   as `page_range`, unverifiable dates, wrong counts, a mis-pointed
   `scholar_id`);
2. prose corrections the first pass had to leave conservative and that
   re-verification against a named source now supports precisely;
3. the curator brackets of other shapes (`[Vérifié …]`, `[Correction …]`,
   `[Greek removed: …]`, …) — merged into prose where they carry a correction,
   then moved verbatim to `metadata.verification_notes`;
4. the `passage_alcin_alcinous_untitled_full_text` escalation — the node is
   relabelled as what its payload actually is (the Hegesippus fragment
   collection) and the two edges asserting Alcinean authorship are deleted;
5. two allowlist entries for `scripts/check_greek_gate.py`, for runs re-confirmed
   in the local TLG E corpus.

Every edit is authored in `scripts/data_2026_08_16_second_sweep.py`, one `#`
comment per edit quoting the tag or the source that justifies it. The script is
deterministic and idempotent: touched nodes are stamped with
`metadata.second_sweep_2026_08_16` and a stamped node is skipped on any later
run. A span whose `old` text does not occur exactly once is reported and
skipped, never applied blind.

Usage:
    python3 scripts/apply_2026_08_16_second_sweep.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_16_second_sweep import (  # noqa: E402
    ALCINOUS_DELETE_EDGE_IDS,
    ALCINOUS_METADATA_OPS,
    ALCINOUS_NODE_FIELDS,
    ALCINOUS_NODE_ID,
    BRACKET_MARKERS,
    BRACKET_NODES,
    DEDUPE_BLOCKS,
    DESCRIPTION_EN_REWRITES,
    DESCRIPTION_REWRITES,
    EDGE_RETARGETS,
    GREEK_ALLOWLIST_ADDITIONS,
    LABEL_REWRITES,
    METADATA_OPS,
    NEW_NODES,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
ALLOWLIST_PATH = ROOT / "data" / "audit" / "greek_allowlist.json"

APPLIED_MARKER = "second_sweep_2026_08_16"

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


# --- text helpers -----------------------------------------------------------


def apply_span(nid: str, field: str, text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        log.append(f"[SKIP-SPAN] {nid} ({field}): old text occurs {n}x — {old[:70]!r}")
        bump("spans_skipped")
        return text
    bump("spans_applied")
    return text.replace(old, new, 1)


def find_bracketed(text: str, marker: str) -> list[tuple[int, int]]:
    """Spans of `marker`-introduced, bracket-balanced runs."""
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


def strip_brackets(nid: str, text: str) -> tuple[str, list[str]]:
    """Pull every curator bracket out of `text`, longest-marker-first."""
    notes: list[str] = []
    while True:
        spans: list[tuple[int, int]] = []
        for marker in BRACKET_MARKERS:
            spans.extend(find_bracketed(text, marker))
        if not spans:
            return text, notes
        # innermost-first is irrelevant here: markers never nest. Take the last
        # span so earlier offsets stay valid.
        start, end = max(spans)
        notes.append(text[start:end])
        text = remove_span(text, start, end)


def dedupe_blocks(nid: str, text: str) -> str:
    blocks = text.split("\n\n")
    seen: set[str] = set()
    kept: list[str] = []
    dropped = 0
    for b in blocks:
        key = b.strip()
        if key and key in seen:
            dropped += 1
            continue
        seen.add(key)
        kept.append(b)
    if dropped:
        log.append(f"[DEDUPE] {nid}: dropped {dropped} duplicate paragraph block(s)")
        bump("dedupe_blocks_dropped", dropped)
    return "\n\n".join(kept)


# --- metadata ops -----------------------------------------------------------


def resolve_path(meta: dict, key: str):
    """Return (container, last_key) for a dotted path with numeric list indices."""
    parts = key.split(".")
    cur = meta
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    last = parts[-1]
    if isinstance(cur, list):
        last = int(last)
    return cur, last


def run_metadata_op(nid: str, node: dict, meta: dict, op: dict) -> bool:
    kind = op["op"]
    key = op.get("key")
    try:
        if kind == "node_set":
            before = node.get(key)
            if before == op["value"]:
                log.append(f"[NOOP-META] {nid}: node.{key} already {before!r}")
                return False
            node[key] = op["value"]
            log.append(f"[NODE] {nid}: {key}: {before!r} -> {op['value']!r}")
            return True
        if kind == "set":
            before = meta.get(key, "<absent>")
            if before == op["value"]:
                log.append(f"[NOOP-META] {nid}: {key} already set")
                return False
            meta[key] = op["value"]
            log.append(
                f"[META] {nid}: {key}: {json.dumps(before, ensure_ascii=False)[:120]}"
                f" -> {json.dumps(op['value'], ensure_ascii=False)[:120]}"
            )
            return True
        if kind == "set_if":
            before = meta.get(key, "<absent>")
            if before != op["old"]:
                log.append(
                    f"[SKIP-META] {nid}: {key} is {before!r}, expected {op['old']!r}"
                )
                return False
            meta[key] = op["value"]
            log.append(f"[META] {nid}: {key}: {before!r} -> {op['value']!r}")
            return True
        if kind == "delete":
            if key not in meta:
                log.append(f"[NOOP-META] {nid}: {key} absent")
                return False
            before = meta.pop(key)
            log.append(
                f"[META] {nid}: deleted {key} "
                f"(was {json.dumps(before, ensure_ascii=False)[:120]})"
            )
            return True
        if kind == "list_remove":
            lst = meta.get(key)
            if not isinstance(lst, list) or op["value"] not in lst:
                log.append(f"[SKIP-META] {nid}: {key} has no such element")
                return False
            lst.remove(op["value"])
            log.append(
                f"[META] {nid}: {key} -= "
                f"{json.dumps(op['value'], ensure_ascii=False)[:120]}"
            )
            return True
        if kind == "list_replace":
            lst = meta.get(key)
            if not isinstance(lst, list) or op["old"] not in lst:
                log.append(f"[SKIP-META] {nid}: {key} has no element {op['old']!r}")
                return False
            lst[lst.index(op["old"])] = op["value"]
            log.append(f"[META] {nid}: {key}: {op['old']!r} -> {op['value']!r}")
            return True
        if kind == "list_set":
            before = meta.get(key, "<absent>")
            if before == op["value"]:
                log.append(f"[NOOP-META] {nid}: {key} already set")
                return False
            meta[key] = list(op["value"])
            log.append(
                f"[META] {nid}: {key}: "
                f"{json.dumps(before, ensure_ascii=False)[:150]} -> "
                f"{json.dumps(op['value'], ensure_ascii=False)[:150]}"
            )
            return True
        if kind == "str_replace":
            container, last = resolve_path(meta, key)
            before = container[last]
            if not isinstance(before, str) or before.count(op["old"]) != 1:
                log.append(f"[SKIP-META] {nid}: {key} has no unique {op['old']!r}")
                return False
            container[last] = before.replace(op["old"], op["new"], 1)
            log.append(f"[META] {nid}: {key}: {op['old']!r} -> {op['new']!r}")
            return True
        if kind == "premise_clear_sources":
            prem = meta.get(key)
            if not isinstance(prem, list):
                log.append(f"[SKIP-META] {nid}: {key} is not a list")
                return False
            hit = 0
            for p in prem:
                if isinstance(p, dict) and p.get("id") in op["ids"]:
                    if p.get("primary_sources"):
                        log.append(
                            f"[META] {nid}: {key}[{p['id']}].primary_sources cleared "
                            f"(was {json.dumps(p['primary_sources'], ensure_ascii=False)[:120]})"
                        )
                    p["primary_sources"] = []
                    p["attestation"] = "unverified"
                    hit += 1
            if not hit:
                log.append(f"[SKIP-META] {nid}: {key} matched no premise id")
                return False
            return True
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        log.append(f"[SKIP-META] {nid}: {kind} on {key} failed ({exc})")
        return False
    log.append(f"[SKIP-META] {nid}: unknown op {kind}")
    return False


def append_notes(meta: dict, notes: list[str]) -> None:
    if not notes:
        return
    existing = meta.get("verification_notes")
    if not isinstance(existing, list):
        existing = [existing] if existing else []
    for n in notes:
        if n not in existing:
            existing.append(n)
    meta["verification_notes"] = existing


# --- main -------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    nodes = load_jsonl(NODES_PATH)
    before_nodes = len(nodes)
    by_id = {node_id_of(n): n for n in nodes}

    planned = (
        set(METADATA_OPS)
        | set(DESCRIPTION_REWRITES)
        | set(DESCRIPTION_EN_REWRITES)
        | set(LABEL_REWRITES)
        | set(BRACKET_NODES)
        | set(DEDUPE_BLOCKS)
        | {ALCINOUS_NODE_ID}
    )
    missing = sorted(planned - set(by_id))
    for nid in missing:
        log.append(f"[MISSING] {nid}: planned but not present in nodes.jsonl")

    for nid in sorted(planned & set(by_id)):
        node = by_id[nid]
        meta, form = parse_metadata(node)
        if meta.get(APPLIED_MARKER):
            log.append(f"[STAMPED] {nid}: already applied, skipping")
            bump("stamped_skipped")
            continue

        changed = False
        desc = node.get("description") or ""
        original_desc = desc

        for old, new in DESCRIPTION_REWRITES.get(nid, ()):
            desc = apply_span(nid, "description", desc, old, new)

        if nid in BRACKET_NODES:
            desc, notes = strip_brackets(nid, desc)
            if notes:
                append_notes(meta, notes)
                bump("brackets_moved", len(notes))
                log.append(f"[BRACKET] {nid}: {len(notes)} bracket(s) -> metadata")
                changed = True

        if nid in DEDUPE_BLOCKS:
            desc = dedupe_blocks(nid, desc)

        if desc != original_desc:
            node["description"] = desc
            changed = True
            log.append(f"[DESC] {nid}: {len(original_desc)} -> {len(desc)} chars")

        if nid in LABEL_REWRITES:
            old, new = LABEL_REWRITES[nid]
            if node.get("label") == old:
                node["label"] = new
                log.append(f"[LABEL] {nid}: {old!r} -> {new!r}")
                bump("labels_rewritten")
                changed = True
            else:
                log.append(f"[SKIP-LABEL] {nid}: label is {node.get('label')!r}")

        for old, new in DESCRIPTION_EN_REWRITES.get(nid, ()):
            cur = meta.get("description_en")
            if not isinstance(cur, str):
                log.append(f"[SKIP-SPAN] {nid} (description_en): field absent")
                bump("spans_skipped")
                continue
            new_val = apply_span(nid, "description_en", cur, old, new)
            if new_val != cur:
                meta["description_en"] = new_val
                changed = True

        ops = METADATA_OPS.get(nid, ())
        if nid == ALCINOUS_NODE_ID:
            ops = ops + ALCINOUS_METADATA_OPS
            for k, v in ALCINOUS_NODE_FIELDS.items():
                if node.get(k) != v:
                    log.append(f"[NODE] {nid}: {k}: {node.get(k)!r} -> {v!r}")
                    node[k] = v
                    changed = True
        for op in ops:
            if run_metadata_op(nid, node, meta, op):
                changed = True
                bump("metadata_ops_applied")

        if changed:
            meta[APPLIED_MARKER] = True
            dump_metadata(node, meta, form)
            bump("nodes_touched")
        else:
            log.append(f"[NOOP] {nid}: nothing to change")
            bump("nodes_unchanged")

    # --- new nodes ---------------------------------------------------------
    for spec in NEW_NODES:
        nid = spec["node_id"]
        if nid in by_id:
            log.append(f"[NOOP-NEW] {nid}: already present")
            continue
        node = dict(spec)
        node["metadata"] = dict(spec["metadata"])
        node["metadata"][APPLIED_MARKER] = True
        nodes.append(node)
        by_id[nid] = node
        log.append(f"[NEW-NODE] {nid}: {node['label']}")
        bump("nodes_created")

    # --- edges -------------------------------------------------------------
    edges = load_jsonl(EDGES_PATH)
    before_edges = len(edges)
    kept_edges = []
    for edge in edges:
        if edge.get("edge_id") in ALCINOUS_DELETE_EDGE_IDS:
            log.append(
                f"[DELETE-EDGE] {edge.get('edge_id')} "
                f"{edge.get('source_id')} -{edge.get('relation')}-> "
                f"{edge.get('target_id')}"
            )
            bump("edges_deleted")
            continue
        kept_edges.append(edge)

    by_edge = {e.get("edge_id"): e for e in kept_edges}
    for spec in EDGE_RETARGETS:
        e = by_edge.get(spec["edge_id"])
        if e is None:
            log.append(f"[SKIP-EDGE] {spec['edge_id']}: not found")
            continue
        field = spec["field"]
        if e.get(field) != spec["old"]:
            log.append(f"[SKIP-EDGE] {spec['edge_id']}: {field} is {e.get(field)!r}")
            continue
        e[field] = spec["new"]
        # keep the legacy alias field, if present, in sync
        alias = "target" if field == "target_id" else "source"
        if alias in e and e[alias] == spec["old"]:
            e[alias] = spec["new"]
        log.append(f"[EDGE] {spec['edge_id']}: {field} {spec['old']} -> {spec['new']}")
        bump("edges_retargeted")

    # --- greek allowlist ---------------------------------------------------
    allow_doc = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    allow = allow_doc.setdefault("allow", {})
    for nid, entries in GREEK_ALLOWLIST_ADDITIONS.items():
        bucket = allow.setdefault(nid, [])
        known = {e.get("hash") for e in bucket}
        for entry in entries:
            if entry["hash"] in known:
                log.append(f"[NOOP-ALLOW] {nid}: {entry['hash']} already allowlisted")
                continue
            bucket.append(dict(entry))
            log.append(f"[ALLOW] {nid}: + {entry['hash']} ({entry['excerpt'][:40]}…)")
            bump("allowlist_entries_added")

    print("\n".join(log))
    print()
    print(f"nodes: {before_nodes} -> {len(nodes)}")
    print(f"edges: {before_edges} -> {len(kept_edges)}")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    dump_jsonl(NODES_PATH, nodes)
    dump_jsonl(EDGES_PATH, kept_edges)
    ALLOWLIST_PATH.write_text(
        json.dumps(allow_doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        f"\nwrote {NODES_PATH.relative_to(ROOT)}, {EDGES_PATH.relative_to(ROOT)} "
        f"and {ALLOWLIST_PATH.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
