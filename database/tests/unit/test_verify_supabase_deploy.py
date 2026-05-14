"""Unit tests for the post-deploy verification helpers.

The DB-touching checks are covered by integration runs against a real
Supabase project; here we only exercise the pure helpers.
"""

from __future__ import annotations

from database.scripts.verify_supabase_deploy import (
    CheckResult,
    _format_line,
    _within_tolerance,
)


def test_within_tolerance_accepts_small_drift() -> None:
    assert _within_tolerance(487, 487, 0.10)
    assert _within_tolerance(490, 487, 0.10)
    assert _within_tolerance(440, 487, 0.10)


def test_within_tolerance_rejects_large_drift() -> None:
    assert not _within_tolerance(100, 487, 0.10)
    assert not _within_tolerance(1000, 487, 0.10)


def test_within_tolerance_zero_expected() -> None:
    # Defensive: never divide by zero.
    assert _within_tolerance(0, 0, 0.10)
    assert _within_tolerance(5, 0, 0.10)


def test_format_line_pass() -> None:
    line = _format_line(
        CheckResult(name="x", passed=True, actual="487", expected="~487")
    )
    assert line.startswith("[✓]")
    assert "x: 487" in line
    assert "(expected ~487)" in line


def test_format_line_fail_with_detail() -> None:
    line = _format_line(
        CheckResult(
            name="x",
            passed=False,
            actual="PostgresError",
            expected="permitted",
            detail="permission denied",
        )
    )
    assert line.startswith("[✗]")
    assert "permission denied" in line
