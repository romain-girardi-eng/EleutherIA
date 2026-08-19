#!/usr/bin/env python3
"""
EleutherIA CLI - Ancient Philosophy Knowledge Graph

Usage:
    eleutheria run              # Start all services
    eleutheria ask "question"   # Ask a question (GraphRAG)
    eleutheria search "query"   # Search the knowledge graph
    eleutheria stats            # Show database statistics
"""

import json
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import quote


# Load .env files (project root, then deploy/production)
def _load_env() -> None:
    """Load environment variables from .env files if not already set."""
    project_root = Path(__file__).parent.parent
    for env_path in [
        project_root / ".env",
        project_root / "deploy" / "production" / ".env",
    ]:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        key, value = key.strip(), value.strip()
                        if key and key not in os.environ:
                            os.environ[key] = value


_load_env()

import typer  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.markdown import Markdown  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.progress import Progress, SpinnerColumn, TextColumn  # noqa: E402
from rich.table import Table  # noqa: E402

from cli.audit_queue import audit_queue_app  # noqa: E402

app = typer.Typer(
    name="eleutheria",
    help="EleutherIA - Ancient Philosophy Knowledge Graph CLI",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()

# Sub-command groups
db_app = typer.Typer(help="Database commands")
test_app = typer.Typer(help="Testing commands")
export_app = typer.Typer(help="Export data commands")
import_app = typer.Typer(help="Import data commands")
app.add_typer(db_app, name="db")
app.add_typer(test_app, name="test")
app.add_typer(export_app, name="export")
app.add_typer(import_app, name="import")
app.add_typer(audit_queue_app, name="audit-queue")

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent

# API configuration
API_BASE_URL = os.getenv("ELEUTHERIA_API_URL", "http://localhost:8000")


def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a shell command and return exit code."""
    try:
        result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        console.print(f"[red]Command not found: {cmd[0]}[/red]")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        return 130


def check_docker() -> bool:
    """Check if Docker is available."""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError, FileNotFoundError:
        return False


def api_request(
    endpoint: str, method: str = "GET", data: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """Make an API request to the backend."""
    try:
        import httpx

        url = f"{API_BASE_URL}/api{endpoint}"
        with httpx.Client(timeout=30.0) as client:
            if method == "GET":
                response = client.get(url)
            else:
                response = client.post(url, json=data)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
    except ImportError:
        console.print(
            "[yellow]Install httpx for API features: pip install httpx[/yellow]"
        )
        return None
    except Exception as e:
        console.print(f"[red]API error: {e}[/red]")
        console.print(f"[dim]Make sure the backend is running at {API_BASE_URL}[/dim]")
        return None


# =============================================================================
# Main Commands
# =============================================================================


@app.command()
def run(
    profile: str = typer.Option(
        "default", "--profile", "-p", help="Profile: default, admin, full"
    ),
) -> None:
    """
    Start all services with Docker Compose.

    Profiles:
    - default: Core services (PostgreSQL, Backend, Frontend)
    - admin: + PgAdmin database admin
    - full: + Prometheus + Grafana monitoring
    """
    if not check_docker():
        console.print("[red]Docker is not installed or not running.[/red]")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            "[bold blue]Starting EleutherIA[/bold blue]\n"
            f"Profile: [green]{profile}[/green]",
            title="EleutherIA",
        )
    )

    compose_file = PROJECT_ROOT / "deploy" / "docker-compose.yml"

    if profile == "admin":
        cmd = ["docker", "compose", "-f", str(compose_file), "--profile", "admin", "up"]
    elif profile == "full":
        cmd = [
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "--profile",
            "admin",
            "--profile",
            "monitoring",
            "up",
        ]
    else:
        cmd = ["docker", "compose", "-f", str(compose_file), "up"]

    raise typer.Exit(run_command(cmd))


@app.command()
def dev(
    service: str = typer.Option(
        "all", "--service", "-s", help="Service: all, backend, frontend"
    ),
) -> None:
    """Start development servers (without Docker)."""
    if service == "backend":
        console.print("[blue]Starting backend on http://localhost:8000[/blue]")
        cmd = [
            "uvicorn",
            "api.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
        raise typer.Exit(run_command(cmd, cwd=PROJECT_ROOT / "backend"))

    elif service == "frontend":
        console.print("[blue]Starting frontend on http://localhost:5173[/blue]")
        cmd = ["npm", "run", "dev"]
        raise typer.Exit(run_command(cmd, cwd=PROJECT_ROOT / "frontend"))

    else:
        console.print("[yellow]Starting all services...[/yellow]")
        console.print("Run in separate terminals:")
        console.print("  [green]eleutheria dev -s backend[/green]")
        console.print("  [green]eleutheria dev -s frontend[/green]")


@app.command()
def stop() -> None:
    """Stop all Docker services."""
    if not check_docker():
        console.print("[red]Docker is not installed or not running.[/red]")
        raise typer.Exit(1)

    compose_file = PROJECT_ROOT / "deploy" / "docker-compose.yml"
    cmd = ["docker", "compose", "-f", str(compose_file), "down"]
    raise typer.Exit(run_command(cmd))


@app.command()
def clean() -> None:
    """Stop services and remove all data volumes."""
    if not check_docker():
        console.print("[red]Docker is not installed or not running.[/red]")
        raise typer.Exit(1)

    confirm = typer.confirm("This will DELETE all data. Are you sure?")
    if not confirm:
        raise typer.Exit(0)

    compose_file = PROJECT_ROOT / "deploy" / "docker-compose.yml"
    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "down",
        "-v",
        "--remove-orphans",
    ]
    raise typer.Exit(run_command(cmd))


@app.command()
def logs(
    service: str = typer.Argument(None, help="Service name (optional)"),
    follow: bool = typer.Option(True, "--follow/--no-follow", "-f", help="Follow logs"),
) -> None:
    """View Docker service logs."""
    compose_file = PROJECT_ROOT / "deploy" / "docker-compose.yml"
    cmd = ["docker", "compose", "-f", str(compose_file), "logs"]
    if follow:
        cmd.append("-f")
    if service:
        cmd.append(service)
    raise typer.Exit(run_command(cmd))


# =============================================================================
# Search & Query Commands
# =============================================================================


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    node_type: str | None = typer.Option(
        None, "--type", "-t", help="Filter by node type"
    ),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of results"),
) -> None:
    """Search the knowledge graph for nodes."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Searching knowledge graph...", total=None)

        # URL encode user input to prevent injection
        params = f"?search={quote(query)}&limit={limit}"
        if node_type:
            params += f"&node_type={quote(node_type)}"

        result = api_request(f"/kg/nodes{params}")

    if not result:
        return

    nodes = result.get("nodes", result) if isinstance(result, dict) else result

    if not nodes:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        return

    table = Table(title=f"Search Results: '{query}'")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Description", style="dim", max_width=50)

    for node in nodes[:limit]:
        name = node.get("name", node.get("label", "Unknown"))
        ntype = node.get("node_type", node.get("type", ""))
        desc = (
            node.get("description", "")[:50] + "..."
            if len(node.get("description", "")) > 50
            else node.get("description", "")
        )
        table.add_row(name, ntype, desc)

    console.print(table)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    thinking: bool = typer.Option(
        False, "--thinking", "-t", help="Use extended reasoning mode"
    ),
) -> None:
    """Ask a question using GraphRAG."""
    console.print(Panel(f"[bold]{question}[/bold]", title="Question"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Thinking...", total=None)

        result = api_request(
            "/graphrag/query",
            method="POST",
            data={
                "question": question,
                "thinking_mode": thinking,
            },
        )

    if not result:
        return

    answer = result.get("answer", result.get("response", "No answer received"))
    sources = result.get("sources", [])

    console.print(Panel(Markdown(answer), title="Answer", border_style="green"))

    if sources:
        console.print("\n[bold]Sources:[/bold]")
        for i, source in enumerate(sources[:5], 1):
            console.print(f"  [{i}] {source}")


@app.command()
def passage(
    urn: str = typer.Argument(..., help="CTS URN or passage ID"),
) -> None:
    """Look up a passage by CTS URN or ID."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Fetching passage...", total=None)
        result = api_request(f"/passages/{urn}")

    if not result:
        return

    content = result.get("content", result.get("text", ""))
    work = result.get("work_title", result.get("work", "Unknown work"))
    author = result.get("author", "")

    console.print(
        Panel(
            f"[italic]{content}[/italic]",
            title=f"{author} - {work}",
            subtitle=urn,
            border_style="blue",
        )
    )


# =============================================================================
# Data Exploration Commands
# =============================================================================


def _query_supabase() -> dict[str, Any] | None:
    """Query Supabase PostgreSQL directly for live statistics."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None

    try:
        import psycopg2  # sync driver — no async needed for CLI

        conn = psycopg2.connect(database_url, connect_timeout=10)
        cur = conn.cursor()

        queries = {
            "nodes": "SELECT count(*) FROM free_will.kg_nodes",
            "edges": "SELECT count(*) FROM free_will.kg_edges",
            "works": "SELECT count(*) FROM free_will.ancient_works",
            "passages": "SELECT count(*) FROM free_will.passages",
            "node_types": "SELECT count(DISTINCT type) FROM free_will.kg_nodes",
            "edge_types": "SELECT count(DISTINCT relation) FROM free_will.kg_edges",
        }

        result: dict[str, Any] = {}
        for key, query in queries.items():
            cur.execute(query)
            row = cur.fetchone()
            result[key] = row[0] if row else 0

        cur.close()
        conn.close()
        return result

    except ImportError:
        console.print(
            "[yellow]Install psycopg2 for direct DB access: "
            "pip install psycopg2-binary[/yellow]"
        )
        return None
    except Exception as e:
        console.print(f"[dim]Supabase query failed: {e}[/dim]")
        return None


@app.command()
def stats() -> None:
    """Show live database statistics from Supabase (primary) or local API (fallback)."""
    result: dict[str, Any] | None = None
    source = ""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # 1. Primary: query Supabase directly
        task = progress.add_task("Querying Supabase...", total=None)
        result = _query_supabase()
        if result:
            source = "supabase"
        else:
            # 2. Fallback: local API (/kg/stats has no corpus counts,
            # so complete them from /works/stats like `info` does)
            progress.update(task, description="Trying local API...")
            result = api_request("/kg/stats")
            if result:
                source = "api"
                works_api = api_request("/works/stats") or {}
                result.setdefault(
                    "works", (works_api.get("works") or {}).get("total_works", 0)
                )
                result.setdefault(
                    "passages",
                    (works_api.get("passages") or {}).get("total_passages", 0),
                )

    if result and source:
        label = "Supabase (live)" if source == "supabase" else "Local API"
        console.print(f"[dim]Source: {label}[/dim]\n")
    else:
        console.print("[red]Could not reach Supabase or local API.[/red]")
        console.print("[dim]Set DATABASE_URL in .env or start the backend.[/dim]\n")
        return

    table = Table(title="EleutherIA Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green", justify="right")

    nodes = result.get("total_nodes", result.get("nodes", 0))
    edges = result.get("total_edges", result.get("edges", 0))
    works = result.get("works", 0)
    passages = result.get("passages", 0)
    node_types = result.get("node_types", 0)
    edge_types = result.get("relation_types", result.get("edge_types", 0))

    # If node_types/edge_types are dicts (from API), get the count
    if isinstance(node_types, dict):
        node_types = len(node_types)
    if isinstance(edge_types, dict):
        edge_types = len(edge_types)

    table.add_row("Knowledge Graph Nodes", f"{nodes:,}")
    table.add_row("Knowledge Graph Edges", f"{edges:,}")
    table.add_row("Ancient Works", f"{works:,}")
    table.add_row("Text Passages", f"{passages:,}")
    table.add_row("Node Types", f"{node_types:,}")
    table.add_row("Relation Types", f"{edge_types:,}")

    console.print(table)


@app.command()
def philosophers(
    school: str | None = typer.Option(
        None, "--school", "-s", help="Filter by school (stoic, epicurean, etc.)"
    ),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of results"),
) -> None:
    """List philosophers in the knowledge graph."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Fetching philosophers...", total=None)

        params = f"?node_type=person&limit={limit}"
        if school:
            params += f"&school={quote(school)}"
        result = api_request(f"/kg/nodes{params}")

    if not result:
        return

    nodes = result.get("nodes", result) if isinstance(result, dict) else result

    table = Table(title="Philosophers")
    table.add_column("Name", style="cyan")
    table.add_column("School", style="green")
    table.add_column("Period", style="yellow")

    for node in nodes[:limit]:
        name = node.get("name", node.get("label", "Unknown"))
        meta = node.get("metadata") or {}
        school_name = meta.get("school", "")
        period = node.get("period", node.get("dates", ""))
        table.add_row(name, school_name, period)

    console.print(table)


@app.command()
def concepts(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of results"),
) -> None:
    """List philosophical concepts in the knowledge graph."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Fetching concepts...", total=None)
        result = api_request(f"/kg/nodes?node_type=concept&limit={limit}")

    if not result:
        return

    nodes = result.get("nodes", result) if isinstance(result, dict) else result

    table = Table(title="Philosophical Concepts")
    table.add_column("Name", style="cyan")
    table.add_column("Greek/Latin", style="green")
    table.add_column("Description", style="dim", max_width=40)

    for node in nodes[:limit]:
        name = node.get("name", node.get("label", "Unknown"))
        meta = node.get("metadata") or {}
        original = meta.get("greek_term", node.get("original_term", ""))
        desc = (
            node.get("description", "")[:40] + "..."
            if len(node.get("description", "")) > 40
            else node.get("description", "")
        )
        table.add_row(name, original, desc)

    console.print(table)


@app.command()
def works(
    language: str | None = typer.Option(
        None, "--language", "-l", help="Filter by language (grc, lat)"
    ),
    author: str | None = typer.Option(None, "--author", "-a", help="Filter by author"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of results"),
) -> None:
    """List ancient works in the database."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Fetching works...", total=None)

        params = f"?limit={limit}"
        if language:
            params += f"&language={quote(language)}"
        if author:
            params += f"&author={quote(author)}"
        result = api_request(f"/works{params}")

    if not result:
        return

    works_list = result.get("works", result) if isinstance(result, dict) else result

    table = Table(title="Ancient Works")
    table.add_column("Title", style="cyan")
    table.add_column("Author", style="green")
    table.add_column("Language", style="yellow")
    table.add_column("Passages", style="dim", justify="right")

    for work in works_list[:limit]:
        title = work.get("title", "Unknown")
        author_name = work.get("author", work.get("author_name", ""))
        lang = work.get("language", "")
        passages = work.get("passage_count", work.get("passages", ""))
        table.add_row(title, author_name, lang, str(passages))

    console.print(table)


# =============================================================================
# Export Commands
# =============================================================================


@export_app.command("kg")
def export_kg(
    format: str = typer.Option("json", "--format", "-f", help="Format: json, csv, rdf"),
    output: str = typer.Option(
        "eleutheria_kg", "--output", "-o", help="Output filename"
    ),
) -> None:
    """Export knowledge graph data."""
    if format == "rdf":
        _export_kg_rdf(output)
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Exporting knowledge graph...", total=None)
        result = api_request("/kg/export")

    if not result:
        console.print(
            "[yellow]Could not fetch from API. Try exporting manually.[/yellow]"
        )
        return

    filename = f"{output}.{format}"

    if format == "json":
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
    elif format == "csv":
        console.print("[yellow]CSV export not yet implemented[/yellow]")
        return

    console.print(f"[green]Exported to {filename}[/green]")


def _export_kg_rdf(output: str) -> None:
    """Build the RDF graph from the JSONL snapshot and emit Turtle, JSON-LD, N-Triples."""
    nodes_path = PROJECT_ROOT / "data" / "kg" / "nodes.jsonl"
    edges_path = PROJECT_ROOT / "data" / "kg" / "edges.jsonl"
    if not nodes_path.exists() or not edges_path.exists():
        console.print(
            f"[red]Missing JSONL snapshot at {nodes_path.parent}. "
            f"Run the KG export snapshot first.[/red]"
        )
        raise typer.Exit(code=1)

    try:
        import sys

        sys.path.insert(0, str(PROJECT_ROOT / "knowledge graph" / "src"))
        from eleutheria_kg.semantic import build_graph, export_graph
    except ImportError as exc:
        console.print(
            f"[red]RDF export requires the semantic extras. Install with: "
            f"uv pip install -e 'knowledge graph[semantic]'\n{exc}[/red]"
        )
        raise typer.Exit(code=1) from exc

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Building RDF graph...", total=None)
        graph = build_graph(nodes_path, edges_path)
        paths = export_graph(graph, output)

    console.print(f"[green]Exported {len(graph):,} triples to:[/green]")
    for fmt, path in paths.items():
        size_mb = path.stat().st_size / (1024 * 1024)
        console.print(f"  • {fmt}: [cyan]{path}[/cyan] ({size_mb:.1f} MB)")


@export_app.command("passages")
def export_passages(
    work: str = typer.Option(None, "--work", "-w", help="Filter by work title"),
    output: str = typer.Option("passages", "--output", "-o", help="Output filename"),
) -> None:
    """Export passage data."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Exporting passages...", total=None)

        params = ""
        if work:
            params = f"?work={quote(work)}"
        result = api_request(f"/works/passages/export{params}")

    if not result:
        console.print("[yellow]Could not fetch from API.[/yellow]")
        return

    filename = f"{output}.json"
    with open(filename, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    console.print(f"[green]Exported to {filename}[/green]")


# =============================================================================
# Import Commands
# =============================================================================


@import_app.command("passages")
def import_passages(
    file: str = typer.Argument(..., help="JSON file to import"),
    dry_run: bool = typer.Option(
        True, "--dry-run/--apply", help="Preview without applying"
    ),
) -> None:
    """Import passages from JSON file."""
    filepath = Path(file)
    if not filepath.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    with open(filepath) as f:
        data = json.load(f)

    count = len(data) if isinstance(data, list) else 1

    if dry_run:
        console.print(f"[yellow]DRY RUN: Would import {count} passages[/yellow]")
        console.print("[dim]Use --apply to actually import[/dim]")
    else:
        confirm = typer.confirm(f"Import {count} passages?")
        if not confirm:
            raise typer.Exit(0)

        result = api_request("/works/passages/import", method="POST", data=data)
        if result:
            console.print(f"[green]Successfully imported {count} passages[/green]")


# =============================================================================
# Health & Status Commands
# =============================================================================


@app.command()
def status() -> None:
    """Check status of all services."""

    table = Table(title="Service Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    # Check backend
    try:
        import httpx

        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{API_BASE_URL}/api/health")
            if response.status_code == 200:
                table.add_row("Backend API", "[green]Running[/green]", API_BASE_URL)
            else:
                table.add_row(
                    "Backend API", "[red]Error[/red]", f"Status {response.status_code}"
                )
    except Exception:
        table.add_row("Backend API", "[red]Not running[/red]", API_BASE_URL)

    # Check Docker services
    if check_docker():
        try:
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(PROJECT_ROOT / "deploy" / "docker-compose.yml"),
                    "ps",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    try:
                        svc = json.loads(line)
                        name = svc.get("Service", svc.get("Name", "unknown"))
                        state = svc.get("State", "unknown")
                        status_style = (
                            "[green]Running[/green]"
                            if state == "running"
                            else f"[yellow]{state}[/yellow]"
                        )
                        table.add_row(f"Docker: {name}", status_style, "")
                    except json.JSONDecodeError, KeyError:
                        pass
        except Exception:
            table.add_row("Docker", "[yellow]Unable to check[/yellow]", "")
    else:
        table.add_row("Docker", "[red]Not installed[/red]", "")

    console.print(table)


@app.command()
def doctor() -> None:
    """Diagnose common issues and suggest fixes."""
    console.print(
        Panel("[bold]Running diagnostics...[/bold]", title="EleutherIA Doctor")
    )

    issues = []

    # Check Python version
    console.print("[green]✓[/green] Python version OK")

    # Check Docker
    if check_docker():
        console.print("[green]✓[/green] Docker installed")
    else:
        issues.append(
            ("Docker", "Not installed or not running. Install from docker.com")
        )

    # Check .env file
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        console.print("[green]✓[/green] .env file exists")

        # Check for API keys
        with open(env_file) as f:
            env_content = f.read()
            if any(
                k in env_content
                for k in (
                    "CODEX_PROXY_API_KEY",
                    "CLAUDE_PROXY_API_KEY",
                    "GEMINI_API_KEY",
                )
            ):
                console.print("[green]✓[/green] API keys configured")
            else:
                issues.append(
                    (
                        "API Keys",
                        "No LLM API keys found in .env. Add CODEX_PROXY_API_KEY, "
                        "CLAUDE_PROXY_API_KEY or GEMINI_API_KEY",
                    )
                )
    else:
        issues.append(
            (".env", "File not found. Copy from .env.example: cp .env.example .env")
        )

    # Check httpx for API features
    try:
        import httpx  # noqa: F401

        console.print("[green]✓[/green] httpx installed (API features available)")
    except ImportError:
        issues.append(("httpx", "Not installed. Run: pip install httpx"))

    # Print issues
    if issues:
        console.print(f"\n[bold red]Found {len(issues)} issue(s):[/bold red]\n")
        for name, fix in issues:
            console.print(f"[red]✗[/red] [bold]{name}:[/bold] {fix}")
    else:
        console.print("\n[bold green]All checks passed![/bold green]")


# =============================================================================
# Quick Access Commands
# =============================================================================


@app.command()
def docs() -> None:
    """Open documentation in browser."""
    url = "https://github.com/romain-girardi-eng/EleutherIA/tree/main/docs"
    console.print(f"[blue]Opening documentation: {url}[/blue]")
    webbrowser.open(url)


@app.command()
def web() -> None:
    """Open free-will.app in browser."""
    url = "https://free-will.app"
    console.print(f"[blue]Opening: {url}[/blue]")
    webbrowser.open(url)


@app.command()
def api() -> None:
    """Open API documentation in browser."""
    url = f"{API_BASE_URL}/docs"
    console.print(f"[blue]Opening API docs: {url}[/blue]")
    webbrowser.open(url)


# =============================================================================
# Interactive Shell
# =============================================================================


@app.command()
def shell() -> None:
    """Start interactive exploration shell."""
    console.print(
        Panel(
            "[bold]EleutherIA Interactive Shell[/bold]\n\n"
            "Commands:\n"
            "  search <query>     - Search knowledge graph\n"
            "  ask <question>     - Ask a question\n"
            "  stats              - Show statistics\n"
            "  philosophers       - List philosophers\n"
            "  concepts           - List concepts\n"
            "  help               - Show this help\n"
            "  exit               - Exit shell",
            title="Interactive Mode",
            border_style="blue",
        )
    )

    while True:
        try:
            cmd = console.input("\n[bold blue]eleutheria>[/bold blue] ").strip()

            if not cmd:
                continue
            elif cmd in ("exit", "quit", "q"):
                console.print("[dim]Goodbye![/dim]")
                break
            elif cmd == "help":
                console.print(
                    "Commands: search, ask, stats, philosophers, concepts, works, exit"
                )
            elif cmd == "stats":
                stats()
            elif cmd == "philosophers":
                philosophers(school=None, limit=10)
            elif cmd == "concepts":
                concepts(limit=10)
            elif cmd == "works":
                works(language=None, author=None, limit=10)
            elif cmd.startswith("search "):
                query = cmd[7:].strip()
                if query:
                    search(query=query, node_type=None, limit=10)
            elif cmd.startswith("ask "):
                question = cmd[4:].strip()
                if question:
                    ask(question=question, thinking=False)
            else:
                console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
                console.print("[dim]Type 'help' for available commands[/dim]")

        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit[/dim]")
        except EOFError:
            break


# =============================================================================
# Temporal / Ingestion Commands
# =============================================================================


@app.command()
def translate(
    priority: str = typer.Option(
        "P0", "--priority", "-p", help="Priority tier: P0, P1, P2, P3"
    ),
    batch_size: int = typer.Option(
        5, "--batch-size", "-b", help="Passages per activity batch"
    ),
    local: bool = typer.Option(
        False,
        "--local",
        help="Bypass Temporal and run the legacy inline script (offline dev).",
    ),
) -> None:
    """Translate KG passages in a priority tier to English.

    By default this dispatches BatchTranslateWorkflow onto the platform's Temporal
    cluster. Pass --local to run the legacy `batch_translate_passages` script
    inline (offline dev, no Temporal required).
    """
    import asyncio
    import time

    if local:
        try:
            from database.scripts import batch_translate_passages
        except ImportError as exc:
            console.print(f"[red]Local translate script unavailable: {exc}[/red]")
            raise typer.Exit(1) from exc
        console.print("[blue]Running translation locally (no Temporal)...[/blue]")
        batch_translate_passages.main()
        return

    async def _dispatch() -> str:
        from backend.services.temporal import get_temporal_client
        from eleutheria_worker.workflows import (
            BatchTranslateInput,
            BatchTranslateWorkflow,
        )

        client = await get_temporal_client()
        workflow_id = f"translate-{priority}-{int(time.time())}"
        task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "eleutheria-ingestion")
        handle = await client.start_workflow(
            BatchTranslateWorkflow.run,
            BatchTranslateInput(priority=priority, batch_size=batch_size),
            id=workflow_id,
            task_queue=task_queue,
        )
        console.print(f"[dim]Workflow: {handle.id}  (task queue: {task_queue})[/dim]")
        result = await handle.result()
        return (
            f"{len(result.translations)} translated, "
            f"{len(result.failed_node_ids)} failed, "
            f"{result.batches_completed} batches"
        )

    try:
        outcome = asyncio.run(_dispatch())
    except Exception as exc:
        console.print(f"[red]Temporal dispatch failed: {exc}[/red]")
        raise typer.Exit(1) from exc

    console.print(f"[green]{outcome}[/green]")


# =============================================================================
# Test Commands
# =============================================================================


@test_app.command("all")
def test_all(
    coverage: bool = typer.Option(
        False, "--coverage", "-c", help="Generate coverage report"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Run all tests across all packages."""
    console.print("[blue]Running all tests...[/blue]")

    cmd = ["pytest"]
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])

    raise typer.Exit(run_command(cmd))


@test_app.command("database")
def test_database() -> None:
    """Run database package tests."""
    console.print("[blue]Running database tests...[/blue]")
    raise typer.Exit(run_command(["pytest", "database/tests/", "-v"]))


@test_app.command("kg")
def test_kg() -> None:
    """Run knowledge graph package tests."""
    console.print("[blue]Running KG tests...[/blue]")
    raise typer.Exit(run_command(["pytest", "knowledge graph/tests/", "-v"]))


@test_app.command("graphrag")
def test_graphrag() -> None:
    """Run GraphRAG package tests."""
    console.print("[blue]Running GraphRAG tests...[/blue]")
    raise typer.Exit(run_command(["pytest", "graphrag/tests/", "-v"]))


@test_app.command("frontend")
def test_frontend() -> None:
    """Run frontend tests."""
    console.print("[blue]Running frontend tests...[/blue]")
    raise typer.Exit(run_command(["npm", "test"], cwd=PROJECT_ROOT / "frontend"))


# =============================================================================
# Code Quality Commands
# =============================================================================


@app.command()
def lint(
    fix: bool = typer.Option(False, "--fix", "-f", help="Auto-fix issues"),
) -> None:
    """Run linter (Ruff) on all Python code."""
    console.print("[blue]Running Ruff linter...[/blue]")

    cmd = ["ruff", "check", "database/", "knowledge graph/", "graphrag/"]
    if fix:
        cmd.append("--fix")

    raise typer.Exit(run_command(cmd))


@app.command()
def format(
    check: bool = typer.Option(False, "--check", help="Check only, don't modify"),
) -> None:
    """Format Python code with Ruff."""
    console.print("[blue]Formatting code...[/blue]")

    cmd = ["ruff", "format", "database/", "knowledge graph/", "graphrag/"]
    if check:
        cmd.append("--check")

    raise typer.Exit(run_command(cmd))


@app.command()
def typecheck() -> None:
    """Run type checker (mypy) on all Python code."""
    console.print("[blue]Running mypy type checker...[/blue]")
    raise typer.Exit(
        run_command(["mypy", "database/", "knowledge graph/", "graphrag/"])
    )


@app.command()
def quality() -> None:
    """Run all code quality checks (lint + typecheck)."""
    console.print("[blue]Running all quality checks...[/blue]\n")

    # Lint
    console.print("[bold]1. Linting (Ruff)...[/bold]")
    lint_result = run_command(
        ["ruff", "check", "database/", "knowledge graph/", "graphrag/"]
    )

    # Type check
    console.print("\n[bold]2. Type checking (mypy)...[/bold]")
    type_result = run_command(["mypy", "database/", "knowledge graph/", "graphrag/"])

    if lint_result == 0 and type_result == 0:
        console.print("\n[green]All checks passed![/green]")
        raise typer.Exit(0)
    else:
        console.print("\n[red]Some checks failed.[/red]")
        raise typer.Exit(1)


# =============================================================================
# Database Commands
# =============================================================================


@db_app.command("migrate")
def db_migrate() -> None:
    """Apply database migrations."""
    console.print("[blue]Applying database migrations...[/blue]")
    schema_file = PROJECT_ROOT / "database" / "schema" / "schema.sql"

    if not schema_file.exists():
        console.print(f"[red]Schema file not found: {schema_file}[/red]")
        raise typer.Exit(1)

    console.print(f"Schema file: {schema_file}")
    console.print("[yellow]Run manually:[/yellow]")
    console.print(f"  psql $DATABASE_URL -f {schema_file}")


@db_app.command("shell")
def db_shell() -> None:
    """Open PostgreSQL shell."""
    console.print("[blue]Opening database shell...[/blue]")
    raise typer.Exit(run_command(["psql", "${DATABASE_URL}"]))


# =============================================================================
# Info Commands
# =============================================================================


@app.command()
def info() -> None:
    """Show project information with LIVE corpus/KG counts from the database.

    Falls back to a hint string ("—") for any count that can't be fetched
    (DB unreachable, etc.). Never shows pre-baked stale numbers; we tried
    that and they were 4-5x off after a few weeks of growth.
    """
    table = Table(title="EleutherIA Project Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Website", "https://free-will.app")
    table.add_row("Repository", "github.com/romain-girardi-eng/EleutherIA")
    table.add_row("License", "CC BY 4.0")
    table.add_row("", "")

    live = _query_supabase()
    source: str
    if live:
        source = "live · Supabase"
        n = live.get("nodes", 0)
        e = live.get("edges", 0)
        w = live.get("works", 0)
        p = live.get("passages", 0)
    else:
        # Best-effort fallback to the public API stats endpoint
        api = api_request("/kg/stats") or {}
        works_api = api_request("/works/stats") or {}
        if api or works_api:
            source = "fallback · public API"
            n = api.get("total_nodes", 0)
            e = api.get("total_edges", 0)
            w = (works_api.get("works") or {}).get("total_works", 0)
            p = (works_api.get("passages") or {}).get("total_passages", 0)
        else:
            source = "unavailable (set DATABASE_URL or start the backend)"
            n = e = w = p = None

    def f(v: Any) -> str:
        return f"{v:,}" if isinstance(v, (int, float)) and v else "—"

    table.add_row("KG Nodes", f(n))
    table.add_row("KG Edges", f(e))
    table.add_row("Ancient Works", f(w))
    table.add_row("Passages", f(p))
    table.add_row("Counts source", f"[dim]{source}[/dim]")
    table.add_row("", "")
    table.add_row("Backend", "FastAPI + Python 3.14+")
    table.add_row("Frontend", "React 19 + TypeScript")
    table.add_row("Database", "PostgreSQL (self-hosted)")
    table.add_row("LLM", "Codex proxy → Claude proxy → Gemini")

    console.print(table)


@app.command()
def version() -> None:
    """Show CLI version."""
    from cli import __version__

    console.print(f"eleutheria CLI v{__version__}")


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
