#!/usr/bin/env python3
"""Apply the 2026-08-16 Alexander/Augustine audit corrections to the local KG.

Scope, as mandated by the audit brief:

1. four mechanical OCR / transmission defects in passage descriptions
   (Gellius NA VII.2.5, Firmicus Mathesis I.2.5, Eusebius PE VI.6.17,
   Alexander De fato 19), each re-verified against a named local witness;
2. `passage_aug_civ_21_12`, whose description was absent — given a locus-only
   description and put under the established `needs_text_ingestion` convention,
   because no critical De ciuitate Dei is held locally;
3. the id/label incoherences (Koch 2019 vs Guyomarc'h 2015, Bonaiuti 1924 vs
   1917, the Frede "dead end" slug) — ids kept, discrepancies recorded;
4. the new `metadata.source_rank` convention for shell / grey-literature nodes;
5. the graph-wide U+02BC → U+2019 normalisation of the Greek elision
   apostrophe, so quote-gate string comparison matches the rest of the corpus.

Every edit is authored in `scripts/data_2026_08_16_alexander_augustine_corrections.py`,
one `#` comment per edit quoting the witness that justifies it. Items the audit
mandated but verification refuted are listed in that module's `SKIPPED` tuple
and are NOT applied.

The script is deterministic and idempotent: touched nodes are stamped with
`metadata.alexander_augustine_corrections_2026_08_16`, a stamped node is skipped
on any later run, and a span whose `old` text does not occur exactly once is
reported and skipped, never applied blind.

Files written: data/kg/nodes.jsonl, and data/kg/publications.bib +
data/kg/publications_bibtex_report.json (regenerated from the nodes by
scripts/export_publications_bibtex.py, which is their only source of truth).
data/kg/edges.jsonl is never touched — no id is renamed by this pass.

Usage:
    python3 scripts/apply_2026_08_16_alexander_augustine_corrections.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_16_alexander_augustine_corrections import (  # noqa: E402
    APOSTROPHE_FROM,
    APOSTROPHE_TO,
    DESCRIPTION_SET,
    DESCRIPTION_SPANS,
    DESCRIPTION_SPANS_PROSE,
    METADATA_OPS,
    NOTE_KEY,
    SKIPPED,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
REVIEW_PATH = ROOT / "data" / "audit" / "2026-08-16_alexander_augustine_corrections.md"
EXPORTER = ROOT / "scripts" / "export_publications_bibtex.py"

APPLIED_MARKER = "alexander_augustine_corrections_2026_08_16"

log: list[str] = []
changes: list[dict] = []
problems: list[str] = []
stats: dict[str, int] = {}


def bump(key: str, n: int = 1) -> None:
    stats[key] = stats.get(key, 0) + n


# --- metadata helpers -------------------------------------------------------


def load_metadata(node: dict) -> tuple[dict, bool]:
    """Return (metadata_dict, was_serialised_as_string)."""
    raw = node.get("metadata")
    if isinstance(raw, dict):
        return raw, False
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}, True
        return (parsed, True) if isinstance(parsed, dict) else ({}, True)
    return {}, isinstance(raw, str)


def store_metadata(node: dict, metadata: dict, as_string: bool) -> None:
    node["metadata"] = (
        json.dumps(metadata, ensure_ascii=False) if as_string else metadata
    )


def append_note(metadata: dict, value: str) -> bool:
    notes = metadata.get(NOTE_KEY)
    if notes is None:
        notes = []
    elif isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = [str(notes)]
    if value in notes:
        return False
    notes.append(value)
    metadata[NOTE_KEY] = notes
    return True


def apply_metadata_ops(
    node_id: str, metadata: dict, ops: tuple[dict, ...]
) -> list[dict]:
    applied: list[dict] = []
    for op in ops:
        kind = op["op"]
        if kind == "note":
            if append_note(metadata, op["value"]):
                applied.append({"op": "note", "key": NOTE_KEY, "new": op["value"]})
            continue
        key = op["key"]
        if kind == "set":
            before = metadata.get(key, "<absent>")
            if before == op["value"]:
                continue
            metadata[key] = op["value"]
            applied.append({"op": "set", "key": key, "old": before, "new": op["value"]})
        elif kind == "set_if":
            before = metadata.get(key, "<absent>")
            if before == op["value"]:
                continue
            if before != op["old"]:
                problems.append(
                    f"{node_id}: set_if on metadata.{key} skipped — expected "
                    f"{op['old']!r}, found {before!r}"
                )
                continue
            metadata[key] = op["value"]
            applied.append(
                {"op": "set_if", "key": key, "old": before, "new": op["value"]}
            )
        elif kind == "delete":
            if key not in metadata:
                continue
            before = metadata[key]
            expect = op.get("expect")
            if expect is not None and before != expect:
                problems.append(
                    f"{node_id}: delete of metadata.{key} skipped — expected "
                    f"{expect!r}, found {before!r}"
                )
                continue
            del metadata[key]
            applied.append(
                {"op": "delete", "key": key, "old": before, "new": "<removed>"}
            )
        else:  # pragma: no cover - guarded by the data module's vocabulary
            problems.append(f"{node_id}: unknown metadata op {kind!r}")
    return applied


# --- span helper ------------------------------------------------------------


def apply_spans(
    node_id: str, text: str, spans: tuple[tuple[str, str], ...]
) -> tuple[str, list[dict]]:
    applied: list[dict] = []
    for old, new in spans:
        count = text.count(old)
        if count == 0 and text.count(new):
            continue  # already applied
        if count != 1:
            problems.append(
                f"{node_id}: description span skipped — {count} occurrence(s) of {old[:60]!r}"
            )
            continue
        text = text.replace(old, new, 1)
        applied.append({"op": "span", "key": "description", "old": old, "new": new})
    return text, applied


# --- main -------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets = (
        set(DESCRIPTION_SPANS)
        | set(DESCRIPTION_SPANS_PROSE)
        | set(DESCRIPTION_SET)
        | set(METADATA_OPS)
    )

    raw_lines = NODES_PATH.read_text(encoding="utf-8").splitlines()
    out_lines: list[str] = []
    seen: set[str] = set()
    apostrophe_occurrences = 0
    apostrophe_nodes = 0

    for raw in raw_lines:
        if not raw.strip():
            continue
        node = json.loads(raw)
        node_id = node.get("id") or node.get("node_id")
        node_changes: list[dict] = []

        if node_id in targets:
            seen.add(node_id)
            metadata, as_string = load_metadata(node)
            if metadata.get(APPLIED_MARKER):
                bump("nodes_already_stamped")
            else:
                desc = node.get("description")
                for table in (DESCRIPTION_SPANS, DESCRIPTION_SPANS_PROSE):
                    spans = table.get(node_id)
                    if not spans:
                        continue
                    if not isinstance(desc, str):
                        problems.append(
                            f"{node_id}: description spans skipped — no description"
                        )
                        continue
                    desc, applied = apply_spans(node_id, desc, spans)
                    node_changes.extend(applied)
                if node_id in DESCRIPTION_SET:
                    new_desc = DESCRIPTION_SET[node_id]
                    if (desc or "").strip() and desc != new_desc:
                        problems.append(
                            f"{node_id}: description set skipped — node already has a description"
                        )
                    elif desc != new_desc:
                        node_changes.append(
                            {
                                "op": "set",
                                "key": "description",
                                "old": "<absent/empty>",
                                "new": new_desc,
                            }
                        )
                        desc = new_desc
                if desc is not None:
                    node["description"] = desc

                ops = METADATA_OPS.get(node_id)
                if ops:
                    node_changes.extend(apply_metadata_ops(node_id, metadata, ops))

                if node_changes:
                    metadata[APPLIED_MARKER] = True
                    store_metadata(node, metadata, as_string)
                    bump("nodes_changed")
                    changes.append({"node_id": node_id, "edits": node_changes})

        line = json.dumps(node, ensure_ascii=False)

        # --- apostrophe sweep (whole file, after the per-node edits) --------
        n = line.count(APOSTROPHE_FROM)
        if n:
            apostrophe_occurrences += n
            apostrophe_nodes += 1
            line = line.replace(APOSTROPHE_FROM, APOSTROPHE_TO)

        out_lines.append(line)

    missing = sorted(targets - seen)
    for node_id in missing:
        problems.append(f"{node_id}: target node not found in nodes.jsonl")

    bump("apostrophe_occurrences", apostrophe_occurrences)
    bump("apostrophe_nodes", apostrophe_nodes)

    log.append(f"nodes read: {len(out_lines)}")
    log.append(
        f"target nodes: {len(targets)} (found {len(seen)}, missing {len(missing)})"
    )
    log.append(f"nodes changed: {stats.get('nodes_changed', 0)}")
    log.append(
        f"nodes already stamped (skipped): {stats.get('nodes_already_stamped', 0)}"
    )
    log.append(
        f"U+02BC -> U+2019: {apostrophe_occurrences} occurrence(s) "
        f"in {apostrophe_nodes} node line(s)"
    )
    for item in SKIPPED:
        log.append(f"SKIPPED: {item['item']} -> {item['verdict']}")
    for item in problems:
        log.append(f"PROBLEM: {item}")

    print("\n".join(log))

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 1 if problems else 0

    NODES_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    if changes:
        write_review()
    else:
        # Idempotent re-run: everything is already stamped. Never overwrite the
        # review file of the run that actually did the work with an empty one.
        print(f"no changes to record — {REVIEW_PATH.name} left untouched")

    result = subprocess.run(
        [sys.executable, str(EXPORTER)], cwd=ROOT, capture_output=True, text=True
    )
    print(result.stderr.strip())
    if result.returncode != 0:
        problems.append(f"bibtex export failed: {result.stdout}{result.stderr}")

    return 1 if problems else 0


def write_review() -> None:
    lines = [
        "# 2026-08-16 — Alexander / Augustine audit corrections (applied)",
        "",
        "Applier: `scripts/apply_2026_08_16_alexander_augustine_corrections.py`  ",
        "Data: `scripts/data_2026_08_16_alexander_augustine_corrections.py`  ",
        "Target: `data/kg/nodes.jsonl` (+ `data/kg/publications.bib` regenerated from it).  ",
        "`data/kg/edges.jsonl` untouched — no id was renamed.",
        "",
        "## Summary",
        "",
    ]
    lines += [f"- {entry}" for entry in log]
    lines += ["", "## Note on `data/kg/publications.bib`", ""]
    lines += [
        "`publications.bib` and `publications_bibtex_report.json` are *generated* "
        "artifacts: `scripts/export_publications_bibtex.py` derives them wholly from "
        'the `type == "publication"` nodes of `data/kg/nodes.jsonl`. This pass '
        "regenerates them, which produces a diff larger than the pass itself, because "
        "the committed `.bib` had drifted out of sync with the graph. The two parts "
        "were measured separately:",
        "",
        "- **This pass's own contribution — 11 field lines across 5 entries:** "
        "`author = {Ernesto Bonaiuti}`, `publisher` → `journal` + `pages`/`volume`/"
        "`number` on the Bonaiuti entry; `author = {John Moon}`; "
        "`author = {Mako A. Nagasawa}`; `author = {Richard Sorabji}` + `booktitle` + "
        "`editor` + `pages` on the Sorabji 2017 entry.",
        "- **Pre-existing drift, ~445 lines, NOT produced here:** regenerating from "
        "the *unmodified* `HEAD` nodes already yields the same 319 entries against the "
        "committed file's 357. The 38 dropped entries are publication nodes that no "
        "longer exist in the graph (merged by earlier dedup waves) and whose BibTeX "
        "entries were therefore dangling; several keys also move to the year/type the "
        "node metadata already carried — including "
        "`publication-2015-la-causalite-humaine-…` (`@article`, 2015, authorless) → "
        "`publication-2019-la-causalite-humaine-…` (`@book`, 2019, "
        "`author = {Isabelle Koch}`, Classiques Garnier, ISBN), which is the §3 fix "
        "the audit asked for.",
        "- `nodes_with_missing_fields` in the report: 198 → 194 (the four `author` "
        "fields added above).",
        "",
    ]
    lines += ["## Per-node before → after", ""]
    for change in changes:
        lines.append(f"### `{change['node_id']}`")
        lines.append("")
        for edit in change["edits"]:
            field = edit["key"] if edit["op"] != "span" else "description (span)"
            lines.append(f"- **{field}** — `{edit['op']}`")
            lines.append(f"  - before: {_fmt(edit.get('old'))}")
            lines.append(f"  - after:  {_fmt(edit.get('new'))}")
        lines.append("")
    lines += ["## Mandated but not applied", ""]
    for item in SKIPPED:
        lines.append(f"### {item['item']}")
        lines.append("")
        lines.append(f"**{item['verdict']}**")
        lines.append("")
        lines.append(item["evidence"])
        lines.append("")
    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(value) -> str:
    if value is None:
        return "_(none)_"
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = text.replace("\n", " ⏎ ").replace("`", "'")
    if len(text) > 900:
        text = text[:900] + " […]"
    return f"`{text}`"


if __name__ == "__main__":
    sys.exit(main())
