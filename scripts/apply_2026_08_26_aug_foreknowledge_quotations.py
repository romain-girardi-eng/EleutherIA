#!/usr/bin/env python3
"""HOW: restore transmitted Latin in `synthesis_aug_foreknowledge`.

Dry-run by default. Pass --write to touch anything.

Preconditions are re-checked at run time against the corpus itself, not
trusted from the data module: the replacement strings must actually occur in
`data/corpus/passages.jsonl` at the loci they claim, and the strings being
removed must actually occur nowhere. If either check fails the script refuses
to write — a repair that cannot re-prove its own evidence is not a repair.

Usage:
    PYTHONPATH=. python3 scripts/apply_2026_08_26_aug_foreknowledge_quotations.py
    PYTHONPATH=. python3 scripts/apply_2026_08_26_aug_foreknowledge_quotations.py --write
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from scripts.data_2026_08_26_aug_foreknowledge_quotations import (
    ALTERED_MEMORY_QUOTE,
    METADATA_UPDATES,
    NEW_MEMORY_LOCUS,
    NODE_ID,
    OLD_MEMORY_LOCUS,
    PARAPHRASED_PROBLEM,
    REMOVAL_REPLACEMENT,
    TRANSMITTED_MEMORY_QUOTE,
    TRANSMITTED_PROBLEM,
    UNATTESTED_DISTINCTION,
    WORK,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
SLUG = "aug_foreknowledge_quotations_2026_08_26"

# The strings this repair asserts are NOT transmitted text anywhere.
MUST_BE_ABSENT = (
    "si praescivit, necessario futurum erat",
    "mea voluntate futurum",
    "non voluntate futurum",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(node: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        node["metadata"] = value


def check_corpus_evidence(passages: list[dict[str, Any]]) -> list[str]:
    """Re-prove the evidence. Returns a list of failures; empty means sound."""
    failures: list[str] = []
    rows = {
        r.get("canonical_ref"): (r.get("text_content") or "")
        for r in passages
        if r.get("work_canonical_id") == WORK
    }

    # The replacements must be present at the loci they claim.
    memory = TRANSMITTED_MEMORY_QUOTE.rstrip(".")
    if memory not in rows.get("3.4.11", ""):
        failures.append("memory analogy not found verbatim at III.4.11")
    problem = TRANSMITTED_PROBLEM.split('"')[1]
    if problem not in rows.get("3.2.4", ""):
        failures.append("problem statement not found verbatim at III.2.4")

    # The removed strings must be absent from the ENTIRE corpus, not just here.
    whole_corpus = "\n".join((r.get("text_content") or "") for r in passages)
    for needle in MUST_BE_ABSENT:
        if needle in whole_corpus:
            failures.append(
                f"{needle!r} DOES occur in the corpus — re-examine before removing"
            )
    return failures


def transform(nodes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    out: list[dict[str, Any]] = []
    changed = False
    for node in nodes:
        if node_id(node) != NODE_ID:
            out.append(node)
            continue
        node = copy.deepcopy(node)
        description = node.get("description") or ""
        before = description

        description = description.replace(
            ALTERED_MEMORY_QUOTE, TRANSMITTED_MEMORY_QUOTE.rstrip("."), 1
        )
        description = description.replace(OLD_MEMORY_LOCUS, NEW_MEMORY_LOCUS, 1)
        description = description.replace(PARAPHRASED_PROBLEM, TRANSMITTED_PROBLEM, 1)
        description = description.replace(
            UNATTESTED_DISTINCTION, REMOVAL_REPLACEMENT, 1
        )

        if description != before:
            node["description"] = description
            meta = metadata(node)
            meta.update(METADATA_UPDATES)
            set_metadata(node, meta)
            changed = True
        out.append(node)
    return out, changed


def assert_invariants(
    before: list[dict[str, Any]], after: list[dict[str, Any]]
) -> None:
    assert len(before) == len(after), "node count changed"
    assert [node_id(n) for n in before] == [node_id(n) for n in after], (
        "node ids or order changed"
    )
    node = next(n for n in after if node_id(n) == NODE_ID)
    description = node.get("description") or ""
    for needle in MUST_BE_ABSENT:
        assert needle not in description, f"unattested Latin survived: {needle!r}"
    assert TRANSMITTED_MEMORY_QUOTE.rstrip(".") in description, (
        "transmitted memory analogy missing"
    )
    assert description.strip(), "emptied the description"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)

    data_root = args.data_root.expanduser().resolve()
    nodes_path = data_root / "kg/nodes.jsonl"
    passages = read_jsonl(data_root / "corpus/passages.jsonl")

    failures = check_corpus_evidence(passages)
    print("Augustine foreknowledge quotation repair —", SLUG)
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    if failures:
        print("PRECONDITION FAILURES — refusing to write:")
        for failure in failures:
            print("  -", failure)
        return 1
    print("corpus evidence re-proved: replacements attested, removals absent")

    original = read_jsonl(nodes_path)
    updated, changed = transform(original)
    assert_invariants(original, updated)
    print("node changed:", changed)

    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("already applied: no files written")
        return 0

    backup = nodes_path.with_suffix(f".jsonl.bak-{SLUG}")
    shutil.copy2(nodes_path, backup)
    write_jsonl(nodes_path, updated)

    report_dir = data_root / "audit"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "2026-08-26_aug_foreknowledge_quotations.json"
    report.write_text(
        json.dumps(
            {
                "slug": SLUG,
                "node": NODE_ID,
                "removed_because_unattested": list(MUST_BE_ABSENT),
                "restored_from_corpus": {
                    "III.4.11": TRANSMITTED_MEMORY_QUOTE,
                    "III.2.4": TRANSMITTED_PROBLEM.split('"')[1],
                },
                "metadata_updates": METADATA_UPDATES,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print("backup:", backup)
    print("wrote:", nodes_path, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
