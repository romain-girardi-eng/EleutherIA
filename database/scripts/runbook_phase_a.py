"""Interactive orchestrator for the Phase A Supabase rebuild runbook.

Walks through the runbook steps with confirm prompts, shelling out to the
authoritative scripts (`bootstrap_supabase.py`, `create_passage_translations.py`,
`verify_supabase_deploy.py`) and to `psql` for schema files. This is a
convenience layer over the runbook in `docs/runbooks/phase-a-supabase-rebuild.md`;
the runbook is the source of truth for the procedure.

Usage:
    python database/scripts/runbook_phase_a.py
    python database/scripts/runbook_phase_a.py --start-at 4   # skip to bootstrap
    python database/scripts/runbook_phase_a.py --yes           # non-interactive

Safe to abort at any prompt - nothing runs without explicit confirmation.
"""

from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "database" / "scripts"
SCHEMA_DIR = REPO_ROOT / "database" / "schema"
MIGRATIONS_DIR = REPO_ROOT / "database" / "migrations"
SNAPSHOT_DIR = REPO_ROOT / "data" / "kg"

SCHEMA_FILES: tuple[Path, ...] = (
    SCHEMA_DIR / "schema.sql",
    SCHEMA_DIR / "work_tree_indices.sql",
    SCHEMA_DIR / "supabase_functions.sql",
    SCHEMA_DIR / "supabase_public_api.sql",
    MIGRATIONS_DIR / "20260514_01_supabase_rebuild_support.sql",
)


app = typer.Typer(add_completion=False, help=__doc__)


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


def _confirm(message: str, *, assume_yes: bool, default: bool = False) -> bool:
    if assume_yes:
        typer.echo(f"{message} [auto-yes]")
        return True
    return typer.confirm(message, default=default)


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    typer.echo(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, check=False)
    return result.returncode


def step_preflight(*, assume_yes: bool) -> bool:
    typer.echo("\nStep 1/6: Preflight checks")
    typer.echo("-" * 60)

    db_url = os.environ.get("SUPABASE_DATABASE_URL")
    if db_url:
        masked = db_url.split("@", 1)[-1] if "@" in db_url else db_url
        is_pooler = ":6543/" in db_url
        marker = "[✗]" if is_pooler else "[✓]"
        suffix = " (transaction pooler - switch to 5432)" if is_pooler else ""
        typer.echo(f"  {marker} SUPABASE_DATABASE_URL set: {masked}{suffix}")
        if is_pooler:
            return False
    else:
        typer.echo("  [✗] SUPABASE_DATABASE_URL not set")
        return False

    ok = True
    for name in ("nodes.jsonl", "edges.jsonl"):
        path = SNAPSHOT_DIR / name
        if not path.exists():
            typer.echo(f"  [✗] snapshot missing: {path.relative_to(REPO_ROOT)}")
            ok = False
            continue
        mtime = dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
        typer.echo(
            f"  [✓] {path.relative_to(REPO_ROOT)} ({path.stat().st_size / 1024:.0f} KiB, "
            f"updated {mtime})"
        )

    if not shutil.which("psql"):
        typer.echo("  [✗] `psql` not found on PATH - install Postgres client tools")
        ok = False
    else:
        typer.echo("  [✓] psql available")

    if not ok:
        return False

    return _confirm(
        "Preflight looks good. Continue?", assume_yes=assume_yes, default=True
    )


def step_dry_run(*, assume_yes: bool) -> bool:
    typer.echo("\nStep 2/6: Dry-run bootstrap")
    typer.echo("-" * 60)
    if not _confirm("Run dry_run_bootstrap.py?", assume_yes=assume_yes, default=True):
        return False
    code = _run([sys.executable, str(SCRIPTS_DIR / "dry_run_bootstrap.py")])
    if code != 0:
        typer.secho(f"  dry-run failed (exit {code})", fg="red")
        return False
    return _confirm(
        "Dry-run counts look correct. Continue to schema apply?",
        assume_yes=assume_yes,
        default=False,
    )


def step_schema(*, assume_yes: bool) -> bool:
    typer.echo("\nStep 3/6: Apply schema files (in order)")
    typer.echo("-" * 60)
    for path in SCHEMA_FILES:
        typer.echo(f"  - {path.relative_to(REPO_ROOT)}")
    if not _confirm(
        "Apply schema with psql -v ON_ERROR_STOP=1?",
        assume_yes=assume_yes,
        default=False,
    ):
        return False
    db_url = os.environ["SUPABASE_DATABASE_URL"]
    for path in SCHEMA_FILES:
        code = _run(
            [
                "psql",
                db_url,
                "-v",
                "ON_ERROR_STOP=1",
                "-f",
                str(path),
            ]
        )
        if code != 0:
            typer.secho(f"  schema apply failed on {path.name} (exit {code})", fg="red")
            return False
    return True


def step_bootstrap(*, assume_yes: bool) -> bool:
    typer.echo("\nStep 4/6: Run bootstrap (idempotent upsert)")
    typer.echo("-" * 60)
    if not _confirm(
        "Run bootstrap_supabase.py against the new project?",
        assume_yes=assume_yes,
        default=False,
    ):
        return False
    code = _run([sys.executable, str(SCRIPTS_DIR / "bootstrap_supabase.py")])
    if code != 0:
        typer.secho(f"  bootstrap failed (exit {code})", fg="red")
        return False
    return True


def step_translations(*, assume_yes: bool) -> bool:
    typer.echo("\nStep 5/6: Translation pass (optional)")
    typer.echo("-" * 60)
    translations_dir = REPO_ROOT / "data" / "translations"
    if not translations_dir.exists():
        typer.echo(
            "  data/translations/ not found - skipping. Backfill later via "
            "create_passage_translations.py."
        )
        return True
    files = sorted(translations_dir.glob("*.json"))
    if not files:
        typer.echo("  no translation JSON files found - skipping.")
        return True
    typer.echo(f"  Found {len(files)} translation file(s):")
    for path in files:
        typer.echo(f"    - {path.relative_to(REPO_ROOT)}")
    if not _confirm("Apply each in turn?", assume_yes=assume_yes, default=False):
        return True
    env = os.environ.copy()
    env["DATABASE_URL"] = env["SUPABASE_DATABASE_URL"]
    for path in files:
        code = _run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "create_passage_translations.py"),
                "--confirm",
                "--translations",
                str(path),
            ],
            env=env,
        )
        if code != 0:
            typer.secho(f"  translation pass failed on {path.name}", fg="red")
            return False
    return True


def step_verify(*, assume_yes: bool) -> bool:
    typer.echo("\nStep 6/6: Verification")
    typer.echo("-" * 60)
    if not _confirm(
        "Run verify_supabase_deploy.py?", assume_yes=assume_yes, default=True
    ):
        return False
    code = _run([sys.executable, str(SCRIPTS_DIR / "verify_supabase_deploy.py")])
    if code != 0:
        typer.secho(
            f"  verification reported failures (exit {code}). See the "
            "'Common failures + remedies' table in the runbook.",
            fg="red",
        )
        return False
    typer.secho("  All verification checks passed.", fg="green")
    return True


STEPS = (
    step_preflight,
    step_dry_run,
    step_schema,
    step_bootstrap,
    step_translations,
    step_verify,
)


@app.command()
def run(
    start_at: int = typer.Option(
        1, "--start-at", min=1, max=len(STEPS), help="1-indexed step to start from."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Assume yes on every prompt (non-interactive)."
    ),
) -> None:
    """Walk through Phase A interactively."""
    _load_dotenv(REPO_ROOT / ".env")

    typer.echo("Phase A - Supabase rebuild")
    typer.echo("=" * 60)
    typer.echo("Runbook: docs/runbooks/phase-a-supabase-rebuild.md")
    typer.echo("Abort at any time with Ctrl+C; nothing runs without confirmation.")
    typer.echo("")

    for index, step in enumerate(STEPS, start=1):
        if index < start_at:
            continue
        ok = step(assume_yes=yes)
        if not ok:
            typer.secho(
                f"\nStopped at step {index}/{len(STEPS)} ({step.__name__}). "
                "Resolve and resume with --start-at {index}.",
                fg="yellow",
            )
            raise typer.Exit(code=1)

    typer.secho("\nPhase A complete. Proceed with cutover per the runbook.", fg="green")


if __name__ == "__main__":
    app()
