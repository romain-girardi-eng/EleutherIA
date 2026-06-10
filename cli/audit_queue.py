"""eleutheria audit-queue — item-by-item integrity review workflow.

Operates ONLY on data/audit/review_queue.jsonl (built by
scripts/audit_queue/build_queue.py). Original audit files are never touched.

Deliberately no bulk operations: adjudication takes exactly one queue id at a
time, per the project's no-auto-fix / verify-each-item rule.
"""

from __future__ import annotations

import getpass
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

audit_queue_app = typer.Typer(
    help="Unified integrity review queue (item-by-item adjudication, no bulk ops)"
)

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
RESOLUTIONS = ("accepted", "rejected", "fixed")


def _queue_path() -> Path:
    override = os.getenv("ELEUTHERIA_REVIEW_QUEUE")
    if override:
        return Path(override)
    return PROJECT_ROOT / "data" / "audit" / "review_queue.jsonl"


def _load_queue(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        console.print(f"[red]Queue not found: {path}[/red]")
        console.print(
            "[dim]Build it first: python3 scripts/audit_queue/build_queue.py[/dim]"
        )
        raise typer.Exit(1)
    entries: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def _save_queue(path: Path, entries: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            f.write("\n")
    tmp.replace(path)


@audit_queue_app.command("list")
def list_entries(
    category: str | None = typer.Option(
        None, "--category", "-c", help="Filter by category (e.g. greek_fabrication)"
    ),
    status: str | None = typer.Option(
        None, "--status", "-s", help="Filter by status (pending, adjudicated)"
    ),
    limit: int = typer.Option(50, "--limit", "-n", help="Max rows to display"),
) -> None:
    """List review-queue entries, optionally filtered by category/status."""
    entries = _load_queue(_queue_path())
    if category:
        entries = [e for e in entries if e.get("category") == category]
    if status:
        entries = [e for e in entries if e.get("status") == status]

    table = Table(title=f"Integrity review queue ({len(entries)} match)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="green")
    table.add_column("Node / Passage", style="yellow", max_width=40)
    table.add_column("Status", style="magenta")
    table.add_column("Summary", style="dim", max_width=60)

    for entry in entries[:limit]:
        ref = entry.get("node_id") or entry.get("passage_id") or ""
        status_text = entry.get("status", "")
        if entry.get("resolution"):
            status_text = f"{status_text} ({entry['resolution']})"
        table.add_row(
            entry.get("id", ""),
            entry.get("category", ""),
            ref,
            status_text,
            (entry.get("summary") or "")[:60],
        )

    console.print(table)
    if len(entries) > limit:
        console.print(f"[dim]… {len(entries) - limit} more (use --limit)[/dim]")


@audit_queue_app.command("show")
def show_entry(
    entry_id: str = typer.Argument(..., help="Queue entry id (rq_…)"),
) -> None:
    """Show one queue entry in full (evidence, proposed action, adjudication)."""
    entries = _load_queue(_queue_path())
    entry = next((e for e in entries if e.get("id") == entry_id), None)
    if entry is None:
        console.print(f"[red]No queue entry with id {entry_id}[/red]")
        raise typer.Exit(1)
    console.print(
        Panel(
            json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=True),
            title=f"{entry_id} — {entry.get('category')}",
            subtitle=f"{entry.get('source_file')}:{entry.get('source_line')}",
            border_style="blue",
        )
    )


@audit_queue_app.command("adjudicate")
def adjudicate_entry(
    entry_id: str = typer.Argument(..., help="Queue entry id (rq_…) — exactly one"),
    resolution: str = typer.Option(
        ..., "--resolution", "-r", help="accepted | rejected | fixed"
    ),
    note: str = typer.Option(
        ..., "--note", help="Why — record the verification you actually did"
    ),
) -> None:
    """Adjudicate ONE entry. Updates only review_queue.jsonl, never source files.

    There is intentionally no apply-all / bulk mode: each finding must be
    verified individually before adjudication.
    """
    if resolution not in RESOLUTIONS:
        console.print(
            f"[red]Invalid resolution '{resolution}'. "
            f"Must be one of: {', '.join(RESOLUTIONS)}[/red]"
        )
        raise typer.Exit(1)

    path = _queue_path()
    entries = _load_queue(path)
    target = next((e for e in entries if e.get("id") == entry_id), None)
    if target is None:
        console.print(f"[red]No queue entry with id {entry_id}[/red]")
        raise typer.Exit(1)

    if target.get("status") == "adjudicated":
        console.print(
            f"[yellow]{entry_id} already adjudicated as "
            f"'{target.get('resolution')}' by {target.get('adjudicated_by')} "
            f"at {target.get('adjudicated_at')} — overwriting.[/yellow]"
        )

    target["status"] = "adjudicated"
    target["resolution"] = resolution
    target["note"] = note
    target["adjudicated_by"] = os.getenv("ELEUTHERIA_REVIEWER") or getpass.getuser()
    target["adjudicated_at"] = datetime.now(UTC).isoformat(timespec="seconds")

    _save_queue(path, entries)
    console.print(
        f"[green]{entry_id} adjudicated: {resolution}[/green] "
        f"[dim]({target['adjudicated_by']} @ {target['adjudicated_at']})[/dim]"
    )
