#!/usr/bin/env python3
"""Strip doxographic source-citation headers from SVF fragment passages.

Work(s) with canonical_id starting 'tlg1269'. The SVF (Stoicorum Veterum Fragmenta)
text in our corpus (tlg1269.tlg002.1st1K-grc1) mixes doxographic headers with the
Greek text. Each passage begins with a Latin/abbreviated source citation like
'Arrianus Epict. Diss. II 19, 1-4.' before the Greek starts.

Fix: strip the leading run of non-Greek characters up to (and including) the first
whitespace after the first occurrence of the first Greek character.

More precisely:
  - Scan from the start for the first Unicode character in the Greek Unicode blocks
    U+0370–U+03FF or U+1F00–U+1FFF (Greek + Extended).
  - The prefix is everything BEFORE that first Greek character.
  - Strip only if: (a) the prefix is non-trivial (> 3 chars after strip), AND
    (b) a Greek character exists in the text, AND (c) the text remains non-empty.

passage_id unchanged → all citations preserved.

Shows 5 before/after samples in dry-run.
Dry-run by default; --commit to write. Idempotent. Snapshot to
data/corpus/fix_snapshots/ before mutating.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "fix_svf_headers_2026_05_24"

WORK_CANONICAL_ID_PREFIX = "tlg1269"

# Greek Unicode ranges
_GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")


def _strip_header(text: str) -> str | None:
    """Return stripped text, or None if no stripping needed/possible."""
    m = _GREEK_RE.search(text)
    if not m:
        return None  # no Greek → skip

    prefix = text[: m.start()]
    stripped_prefix = prefix.strip()
    if len(stripped_prefix) <= 3:
        return None  # trivial prefix (e.g. a quote mark)

    remaining = text[m.start() :]
    if not remaining.strip():
        return None  # nothing left

    return remaining.strip()


def _db_url() -> str:
    for line in (ROOT / ".env").open():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


async def main(commit: bool) -> int:
    import asyncpg

    conn = await asyncpg.connect(_db_url())
    try:
        rows = await conn.fetch(
            """
            SELECT p.passage_id::text AS passage_id,
                   p.cts_urn, p.canonical_ref, p.text_content
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON w.work_id = p.work_id
            WHERE w.canonical_id LIKE $1
            """,
            f"{WORK_CANONICAL_ID_PREFIX}%",
        )
        print(f"Total SVF passages found: {len(rows)}")

        to_fix: list[dict] = []
        for r in rows:
            text = r["text_content"] or ""
            stripped = _strip_header(text)
            if stripped is not None and stripped != text:
                to_fix.append({
                    "passage_id": r["passage_id"],
                    "cts_urn": r["cts_urn"],
                    "canonical_ref": r["canonical_ref"],
                    "old_text": text,
                    "new_text": stripped,
                })

        print(f"Passages with strippable headers: {len(to_fix)}/{len(rows)}")

        # Show 5 before/after samples
        print("\n--- 5 before/after samples ---")
        for sample in to_fix[:5]:
            old_preview = sample["old_text"][:120].replace("\n", " ")
            new_preview = sample["new_text"][:120].replace("\n", " ")
            print(f"  REF: {sample['canonical_ref']}")
            print(f"  BEFORE: {old_preview!r}")
            print(f"  AFTER:  {new_preview!r}")
            print()

        if not to_fix:
            print("Nothing to do.")
            return 0

        if not commit:
            print("[DRY-RUN] Pass --commit to write changes.")
            return 0

        # Snapshot
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snap_path = SNAPSHOT_DIR / "affected_passages.json"
        snap_path.write_text(
            json.dumps(
                [{"passage_id": r["passage_id"], "cts_urn": r["cts_urn"],
                  "old_text": r["old_text"]}
                 for r in to_fix],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Snapshot written: {snap_path}")

        # passages table has no updated_at column
        updated = 0
        for row in to_fix:
            await conn.execute(
                """
                UPDATE free_will.passages
                   SET text_content = $1
                 WHERE passage_id = $2
                """,
                row["new_text"],
                row["passage_id"],
            )
            updated += 1

        print(f"Updated {updated} passages. DONE.")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write changes (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
