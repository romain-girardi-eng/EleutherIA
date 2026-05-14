"""Apply schema + migrations to a Supabase project via asyncpg.

Reads each SQL file and executes it as a single statement so that
dollar-quoted PL/pgSQL blocks and CREATE EXTENSION statements work
correctly. Connection details come from the SUPABASE_DATABASE_URL
or DATABASE_URL env vars.

Usage:
    .venv-py314/bin/python database/scripts/apply_schema.py
    .venv-py314/bin/python database/scripts/apply_schema.py --migration database/migrations/X.sql
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_FILES = [
    "database/schema/schema.sql",
    "database/schema/work_tree_indices.sql",
    "database/schema/supabase_functions.sql",
    "database/schema/supabase_public_api.sql",
    "database/migrations/20260514_01_supabase_rebuild_support.sql",
]


async def _apply(files: list[str]) -> int:
    dsn = os.environ.get("SUPABASE_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: SUPABASE_DATABASE_URL or DATABASE_URL must be set", file=sys.stderr)
        return 2

    conn = await asyncpg.connect(dsn, statement_cache_size=0)
    try:
        for rel in files:
            path = (REPO_ROOT / rel) if not Path(rel).is_absolute() else Path(rel)
            if not path.exists():
                print(f"MISSING {rel}", file=sys.stderr)
                return 3
            sql = path.read_text()
            t0 = time.perf_counter()
            try:
                await conn.execute(sql)
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL  {rel}: {exc!r}", file=sys.stderr)
                raise
            dt = time.perf_counter() - t0
            print(f"OK    {rel}  ({dt:.2f}s, {len(sql)} chars)")
    finally:
        await conn.close()
    return 0


async def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--migration",
        action="append",
        default=None,
        help="Apply only the given migration file(s) instead of the full schema set.",
    )
    args = parser.parse_args()

    files = args.migration if args.migration else SCHEMA_FILES
    return await _apply(files)


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
