"""Post-deploy verification for a rebuilt Supabase project (Phase A).

Connects via SUPABASE_DATABASE_URL and runs a series of read-only checks
against the canonical EleutherIA tables. Exits 0 if every check passes,
1 if any fails. The script never writes data: the service-role write
check uses an explicit transaction that is always rolled back.

Usage:
    export SUPABASE_DATABASE_URL=postgresql://postgres:...@db.<ref>.supabase.co:5432/postgres
    python database/scripts/verify_supabase_deploy.py

Tolerance: count checks accept +/- 10% drift to absorb future ingestion.
"""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import asyncpg

EXPECTED_ANCIENT_WORKS = 487
EXPECTED_PASSAGES = 69_277
EXPECTED_KG_NODES = 17_746
EXPECTED_KG_EDGES = 42_925
COUNT_TOLERANCE = 0.10  # +/- 10%


@dataclass
class CheckResult:
    name: str
    passed: bool
    actual: str
    expected: str
    detail: str = ""


def _format_line(result: CheckResult) -> str:
    mark = "[✓]" if result.passed else "[✗]"
    base = f"{mark} {result.name}: {result.actual} (expected {result.expected})"
    if result.detail:
        base += f" - {result.detail}"
    return base


def _within_tolerance(actual: int, expected: int, tolerance: float) -> bool:
    if expected <= 0:
        return actual >= 0
    delta = abs(actual - expected) / expected
    return delta <= tolerance


async def _count(conn: asyncpg.Connection, table: str) -> int:
    row = await conn.fetchval(f"SELECT count(*) FROM {table}")
    return int(row or 0)


async def check_ancient_works_count(conn: asyncpg.Connection) -> CheckResult:
    actual = await _count(conn, "free_will.ancient_works")
    passed = _within_tolerance(actual, EXPECTED_ANCIENT_WORKS, COUNT_TOLERANCE)
    return CheckResult(
        name="ancient_works count",
        passed=passed,
        actual=str(actual),
        expected=f"~{EXPECTED_ANCIENT_WORKS} (+/-10%)",
    )


async def check_passages_count(conn: asyncpg.Connection) -> CheckResult:
    actual = await _count(conn, "free_will.passages")
    passed = _within_tolerance(actual, EXPECTED_PASSAGES, COUNT_TOLERANCE)
    return CheckResult(
        name="passages count",
        passed=passed,
        actual=str(actual),
        expected=f"~{EXPECTED_PASSAGES} (+/-10%)",
    )


async def check_kg_nodes_count(conn: asyncpg.Connection) -> CheckResult:
    actual = await _count(conn, "free_will.kg_nodes")
    passed = _within_tolerance(actual, EXPECTED_KG_NODES, COUNT_TOLERANCE)
    return CheckResult(
        name="kg_nodes count",
        passed=passed,
        actual=str(actual),
        expected=f"~{EXPECTED_KG_NODES} (+/-10%)",
    )


async def check_kg_edges_count(conn: asyncpg.Connection) -> CheckResult:
    actual = await _count(conn, "free_will.kg_edges")
    passed = _within_tolerance(actual, EXPECTED_KG_EDGES, COUNT_TOLERANCE)
    return CheckResult(
        name="kg_edges count",
        passed=passed,
        actual=str(actual),
        expected=f"~{EXPECTED_KG_EDGES} (+/-10%)",
    )


async def check_passage_citations_count(conn: asyncpg.Connection) -> CheckResult:
    actual = await _count(conn, "free_will.passage_citations")
    passed = actual > 0
    return CheckResult(
        name="passage_citations count",
        passed=passed,
        actual=str(actual),
        expected="> 0",
    )


async def check_translation_nodes(conn: asyncpg.Connection) -> CheckResult:
    actual = await conn.fetchval(
        "SELECT count(*) FROM free_will.kg_nodes WHERE node_id LIKE '%\\_en' ESCAPE '\\'"
    )
    actual_int = int(actual or 0)
    passed = actual_int > 0
    return CheckResult(
        name="translation _en kg_nodes",
        passed=passed,
        actual=str(actual_int),
        expected="> 0 (warn if 0; run create_passage_translations.py to backfill)",
    )


async def check_kg_nodes_anon_read(conn: asyncpg.Connection) -> CheckResult:
    """Simulate an anon client by SET ROLE anon and selecting a single row.

    The migration grants SELECT to anon and creates an RLS policy
    `kg_nodes_read_api` for anon, authenticated. If RLS denies the read,
    fetchval returns NULL or raises.
    """
    try:
        async with conn.transaction():
            await conn.execute("SET LOCAL ROLE anon")
            row = await conn.fetchval("SELECT count(*) FROM free_will.kg_nodes")
        actual = int(row or 0)
        passed = actual > 0
        return CheckResult(
            name="anon SELECT on kg_nodes",
            passed=passed,
            actual=f"{actual} rows visible",
            expected="> 0 rows (RLS read policy)",
        )
    except asyncpg.PostgresError as exc:
        return CheckResult(
            name="anon SELECT on kg_nodes",
            passed=False,
            actual=type(exc).__name__,
            expected="permitted by RLS",
            detail=str(exc).splitlines()[0],
        )


async def check_service_role_write(conn: asyncpg.Connection) -> CheckResult:
    """Confirm the current connection can write to free_will.users.

    Uses an explicit transaction that is always rolled back so no row
    is persisted. The current connection must be the postgres / service
    role for this to succeed.
    """
    try:
        tr = conn.transaction()
        await tr.start()
        try:
            await conn.execute(
                """
                INSERT INTO free_will.users (username, email, hashed_password, role)
                VALUES ($1, $2, $3, 'viewer')
                """,
                "_phase_a_verify_probe",
                "_phase_a_verify_probe@verify.test",
                "x",
            )
        finally:
            await tr.rollback()
        return CheckResult(
            name="service-role write to free_will.users",
            passed=True,
            actual="INSERT permitted (rolled back)",
            expected="permitted",
        )
    except asyncpg.PostgresError as exc:
        return CheckResult(
            name="service-role write to free_will.users",
            passed=False,
            actual=type(exc).__name__,
            expected="permitted",
            detail=str(exc).splitlines()[0],
        )


async def check_kg_stats_rpc(conn: asyncpg.Connection) -> CheckResult:
    try:
        row = await conn.fetchrow("SELECT * FROM public.get_kg_stats()")
        if row is None:
            return CheckResult(
                name="public.get_kg_stats() RPC",
                passed=False,
                actual="NULL",
                expected="row returned",
            )
        return CheckResult(
            name="public.get_kg_stats() RPC",
            passed=True,
            actual=f"row with {len(row)} columns",
            expected="row returned",
        )
    except asyncpg.PostgresError as exc:
        return CheckResult(
            name="public.get_kg_stats() RPC",
            passed=False,
            actual=type(exc).__name__,
            expected="row returned",
            detail=str(exc).splitlines()[0],
        )


CheckFn = Callable[[asyncpg.Connection], Coroutine[Any, Any, CheckResult]]

CHECKS: tuple[CheckFn, ...] = (
    check_ancient_works_count,
    check_passages_count,
    check_kg_nodes_count,
    check_kg_edges_count,
    check_passage_citations_count,
    check_translation_nodes,
    check_kg_nodes_anon_read,
    check_service_role_write,
    check_kg_stats_rpc,
)


async def run(database_url: str) -> int:
    conn = await asyncpg.connect(
        dsn=database_url,
        statement_cache_size=0,
        timeout=30,
        command_timeout=60,
    )
    try:
        results: list[CheckResult] = []
        for fn in CHECKS:
            try:
                results.append(await fn(conn))
            except Exception as exc:  # pragma: no cover - defensive
                results.append(
                    CheckResult(
                        name=fn.__name__.removeprefix("check_"),
                        passed=False,
                        actual=type(exc).__name__,
                        expected="check to complete",
                        detail=str(exc).splitlines()[0],
                    )
                )
    finally:
        await conn.close()

    print("Phase A Supabase verification")
    print("-" * 60)
    for result in results:
        print(_format_line(result))
    print("-" * 60)
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"{passed}/{total} checks passed")
    return 0 if passed == total else 1


def main() -> int:
    database_url = os.environ.get("SUPABASE_DATABASE_URL")
    if not database_url:
        print(
            "SUPABASE_DATABASE_URL is not set. Export the direct Supabase "
            "DSN (port 5432) and re-run.",
            file=sys.stderr,
        )
        return 2
    if ":6543/" in database_url:
        print(
            "Warning: SUPABASE_DATABASE_URL points at the transaction pooler "
            "(port 6543). Use the direct connection on port 5432 for "
            "verification, otherwise some checks may stall.",
            file=sys.stderr,
        )
    return asyncio.run(run(database_url))


if __name__ == "__main__":
    raise SystemExit(main())
