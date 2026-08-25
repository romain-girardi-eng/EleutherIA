#!/usr/bin/env python3
"""HOW: apply the corpus text artifacts described in data_2026_08_26_*.

Dry-run by default. Pass --write to touch anything.

House rules this follows:
  * preconditions are re-checked at run time, not trusted from the data module;
    if the evidence no longer holds the row is skipped and logged, never forced
  * idempotent: the transforms are self-detecting, so a second run is a no-op
  * invariants asserted before writing (row count, ids, no Greek/Latin added)
  * backup written next to the file before the replace
  * a report lands in data/audit/

Usage:
    PYTHONPATH=. python3 scripts/apply_2026_08_26_corpus_text_artifacts.py
    PYTHONPATH=. python3 scripts/apply_2026_08_26_corpus_text_artifacts.py --write
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from scripts.data_2026_08_26_corpus_text_artifacts import (
    BOETHIUS_ROW_COUNT,
    BOETHIUS_WORK,
    NOT_REPAIRED,
    SVF_ARTIFACT,
    SVF_ATTESTATION,
    SVF_PASSAGE_ID,
    SVF_REPAIRED,
    collapse_echoed_braces,
    strip_language_prefix,
    strip_running_footer,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
SLUG = "corpus_text_artifacts_2026_08_26"

GREEK_RANGES = ((0x0370, 0x03FF), (0x1F00, 0x1FFF))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def greek_chars(text: str) -> str:
    """Every Greek codepoint in `text`, NFC-normalised, in order."""
    normalized = unicodedata.normalize("NFC", text)
    return "".join(
        ch
        for ch in normalized
        if any(low <= ord(ch) <= high for low, high in GREEK_RANGES)
    )


def transform(
    passages: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (passages, changed, skipped). Never mutates the input rows."""
    out: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for row in passages:
        row = dict(row)
        text = row.get("text_content")
        if not isinstance(text, str):
            out.append(row)
            continue
        before = text

        if row.get("passage_id") == SVF_PASSAGE_ID:
            # Precondition: the exact artifact string is present, exactly once.
            if text.count(SVF_ARTIFACT) == 1:
                text = text.replace(SVF_ARTIFACT, SVF_REPAIRED, 1)
            elif SVF_REPAIRED in text:
                pass  # already applied
            else:
                skipped.append(
                    {
                        "passage_id": SVF_PASSAGE_ID,
                        "reason": "artifact string not found as declared",
                    }
                )

        if row.get("work_canonical_id") == BOETHIUS_WORK:
            text = strip_language_prefix(text)
            text = strip_running_footer(text, row.get("sequence_number"))
            text = collapse_echoed_braces(text)

        if text != before:
            # Nothing in this repair may add or alter a single Greek character.
            assert greek_chars(text) == greek_chars(before).replace(
                greek_chars(SVF_ARTIFACT), greek_chars(SVF_REPAIRED)
            ) or greek_chars(text) == greek_chars(before), (
                f"Greek changed unexpectedly in {row.get('passage_id')}"
            )
            row["text_content"] = text
            changed.append(
                {
                    "passage_id": row.get("passage_id"),
                    "work_canonical_id": row.get("work_canonical_id"),
                    "canonical_ref": row.get("canonical_ref"),
                    "chars_removed": len(before) - len(text),
                }
            )
        out.append(row)

    return out, changed, skipped


def assert_invariants(
    before: list[dict[str, Any]], after: list[dict[str, Any]]
) -> None:
    assert len(before) == len(after), "row count changed"
    assert [r.get("passage_id") for r in before] == [
        r.get("passage_id") for r in after
    ], "passage_id order or identity changed"

    ids = [r.get("passage_id") for r in after]
    assert len(ids) == len(set(ids)), "duplicate passage_id"

    for row in after:
        text = row.get("text_content")
        if not isinstance(text, str):
            continue
        assert text.strip(), f"emptied a passage: {row.get('passage_id')}"
        if row.get("work_canonical_id") == BOETHIUS_WORK:
            assert not text.startswith("Latin:"), "language prefix survived"
            assert "De consolatione philosophiae" not in text.split("\n")[-1], (
                "running footer survived"
            )
        # Scoped to the artifact itself. "Augustinus" appears legitimately in
        # 40 rows corpus-wide (SVF cites him as a witness, Latin works name
        # him); only this splice is a defect.
        assert SVF_ARTIFACT not in text, (
            f"line-join artifact survived in {row.get('passage_id')}"
        )

    boethius = [r for r in after if r.get("work_canonical_id") == BOETHIUS_WORK]
    assert len(boethius) == BOETHIUS_ROW_COUNT, (
        f"expected {BOETHIUS_ROW_COUNT} Boethius rows, found {len(boethius)}"
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)
        for row in rows:
            handle.write(
                json.dumps(
                    row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
                + "\n"
            )
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)

    data_root = args.data_root.expanduser().resolve()
    passages_path = data_root / "corpus/passages.jsonl"
    original = read_jsonl(passages_path)
    updated, changed, skipped = transform(original)
    assert_invariants(original, updated)

    print("Corpus text artifacts repair —", SLUG)
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("rows changed:", len(changed))
    print("rows skipped on failed precondition:", len(skipped))
    for entry in skipped:
        print("  SKIP", entry)
    print("deliberately not repaired:", len(NOT_REPAIRED), "classes (see data module)")

    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("already applied: no files written")
        return 0

    backup = passages_path.with_suffix(f".jsonl.bak-{SLUG}")
    shutil.copy2(passages_path, backup)
    write_jsonl(passages_path, updated)

    report_dir = data_root / "audit"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "2026-08-26_corpus_text_artifacts.json"
    report.write_text(
        json.dumps(
            {
                "slug": SLUG,
                "changed_records": changed,
                "skipped": skipped,
                "svf_attestation": SVF_ATTESTATION,
                "not_repaired": NOT_REPAIRED,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print("backup:", backup)
    print("wrote:", passages_path, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
