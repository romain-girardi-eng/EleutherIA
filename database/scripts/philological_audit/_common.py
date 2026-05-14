"""Shared utilities for the philological audit pass.

Each audit script writes a JSONL report to ``data/philological_audit``
with the canonical schema:

    {"node_id": str, "dimension": str, "issue": str,
     "current": Any, "suggested_fix": Any, "confidence": float,
     "auto_apply": bool}

Where ``auto_apply`` flags whether the fix is mechanical enough to apply
without human review. The ``--apply`` flag on each script only writes
rows where ``auto_apply == True``.

All scripts respect the same env var ``DATABASE_URL`` and the same DSN
fallback used elsewhere in the repo (Supabase pooler).
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import asyncpg

DEFAULT_DSN = (
    "postgresql://postgres.[redacted-project-ref]:[REDACTED]"
    "@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
)


REPORTS_DIR = Path(__file__).resolve().parents[3] / "data" / "philological_audit"


def dsn() -> str:
    return os.environ.get("DATABASE_URL") or DEFAULT_DSN


async def connect() -> asyncpg.Connection:
    return await asyncpg.connect(dsn(), statement_cache_size=0)


def normalize_meta(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


def write_jsonl(rows: Iterable[Mapping[str, Any]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            fh.write("\n")
            count += 1
    return count


def emit_summary(name: str, counts: Mapping[str, int]) -> None:
    width = max((len(k) for k in counts), default=0)
    print(f"[{name}] summary", file=sys.stderr)
    for key, val in counts.items():
        print(f"  {key.ljust(width)}  {val}", file=sys.stderr)
