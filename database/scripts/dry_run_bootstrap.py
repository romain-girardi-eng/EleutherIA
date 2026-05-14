"""Pre-deploy readiness check for Phase A.

Thin wrapper around `bootstrap_supabase.py --dry-run` that:
- loads .env from the repo root if present,
- confirms the snapshot files exist and reports their mtime,
- runs the dry-run and prints expected row counts.

No network calls, no writes. Safe to run anywhere.

Usage:
    python database/scripts/dry_run_bootstrap.py
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = REPO_ROOT / "data" / "kg"
SNAPSHOT_FILES = ("nodes.jsonl", "edges.jsonl")
BOOTSTRAP_SCRIPT = REPO_ROOT / "database" / "scripts" / "bootstrap_supabase.py"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _format_mtime(path: Path) -> str:
    ts = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.UTC)
    return ts.strftime("%Y-%m-%d %H:%M:%S UTC")


def _check_snapshot() -> bool:
    print("Snapshot files")
    print("-" * 60)
    ok = True
    for name in SNAPSHOT_FILES:
        path = SNAPSHOT_DIR / name
        if not path.exists():
            print(f"  [✗] {path} - MISSING")
            ok = False
            continue
        size = path.stat().st_size
        lines = sum(1 for _ in path.open("r", encoding="utf-8"))
        print(
            f"  [✓] {path.relative_to(REPO_ROOT)} - "
            f"{lines:,} lines, {size / 1024:.1f} KiB, mtime {_format_mtime(path)}"
        )
    print("-" * 60)
    return ok


def main() -> int:
    _load_dotenv(REPO_ROOT / ".env")

    print("Phase A readiness check")
    print("=" * 60)

    if not _check_snapshot():
        print(
            "Snapshot files missing. Regenerate via the KG snapshot service "
            "before retrying.",
            file=sys.stderr,
        )
        return 1

    if not BOOTSTRAP_SCRIPT.exists():
        print(f"bootstrap script not found: {BOOTSTRAP_SCRIPT}", file=sys.stderr)
        return 1

    print()
    print("Bootstrap dry-run (no DB connection, expected row counts)")
    print("-" * 60)
    result = subprocess.run(
        [sys.executable, str(BOOTSTRAP_SCRIPT), "--dry-run"],
        cwd=str(REPO_ROOT),
        check=False,
    )
    print("-" * 60)

    if result.returncode != 0:
        print(
            f"Dry-run exited with code {result.returncode}. Fix the snapshot "
            "or bootstrap script before deploying.",
            file=sys.stderr,
        )
        return result.returncode

    db_url = os.environ.get("SUPABASE_DATABASE_URL") or os.environ.get("DATABASE_URL")
    print()
    if db_url:
        marker = ":6543/" in db_url
        port_note = (
            " (transaction pooler - switch to port 5432 for migration)"
            if marker
            else " (direct)"
        )
        masked = db_url.split("@", 1)[-1] if "@" in db_url else db_url
        print(f"Target DSN host: {masked}{port_note}")
    else:
        print(
            "SUPABASE_DATABASE_URL / DATABASE_URL not set. "
            "Export the direct DSN (port 5432) before running the real bootstrap."
        )

    print()
    print("Readiness check complete. Proceed with the runbook in")
    print("  docs/runbooks/phase-a-supabase-rebuild.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
