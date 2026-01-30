#!/usr/bin/env python3
"""
EleutherIA CLI - Ancient Philosophy Knowledge Graph

Usage:
    eleutheria run          # Start all services
    eleutheria dev          # Start in development mode
    eleutheria test         # Run all tests
    eleutheria lint         # Check code quality
    eleutheria db           # Database commands
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
app.add_typer(db_app, name="db")
app.add_typer(test_app, name="test")

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> int:
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
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# =============================================================================
# Main Commands
# =============================================================================


@app.command()
def run(
    profile: str = typer.Option(
        "default", "--profile", "-p", help="Profile: default, admin, full"
    ),
):
    """
    Start all services with Docker Compose.

    Profiles:
    - default: Core services (PostgreSQL, Qdrant, Backend, Frontend)
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
            title="🏛️ EleutherIA",
        )
    )

    compose_file = PROJECT_ROOT / "deploy" / "docker" / "docker-compose.yml"

    if profile == "admin":
        cmd = ["docker", "compose", "-f", str(compose_file), "--profile", "admin", "up"]
    elif profile == "full":
        cmd = [
            "docker", "compose", "-f", str(compose_file),
            "--profile", "admin", "--profile", "monitoring", "up"
        ]
    else:
        cmd = ["docker", "compose", "-f", str(compose_file), "up"]

    raise typer.Exit(run_command(cmd))


@app.command()
def dev(
    service: str = typer.Option(
        "all", "--service", "-s", help="Service: all, backend, frontend"
    ),
):
    """
    Start development servers (without Docker).
    """
    if service == "backend":
        console.print("[blue]Starting backend on http://localhost:8000[/blue]")
        cmd = ["uvicorn", "api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
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
def stop():
    """Stop all Docker services."""
    if not check_docker():
        console.print("[red]Docker is not installed or not running.[/red]")
        raise typer.Exit(1)

    compose_file = PROJECT_ROOT / "deploy" / "docker" / "docker-compose.yml"
    cmd = ["docker", "compose", "-f", str(compose_file), "down"]
    raise typer.Exit(run_command(cmd))


@app.command()
def clean():
    """Stop services and remove all data volumes."""
    if not check_docker():
        console.print("[red]Docker is not installed or not running.[/red]")
        raise typer.Exit(1)

    confirm = typer.confirm("This will DELETE all data. Are you sure?")
    if not confirm:
        raise typer.Exit(0)

    compose_file = PROJECT_ROOT / "deploy" / "docker" / "docker-compose.yml"
    cmd = ["docker", "compose", "-f", str(compose_file), "down", "-v", "--remove-orphans"]
    raise typer.Exit(run_command(cmd))


@app.command()
def logs(
    service: str = typer.Argument(None, help="Service name (optional)"),
    follow: bool = typer.Option(True, "--follow/--no-follow", "-f", help="Follow logs"),
):
    """View Docker service logs."""
    compose_file = PROJECT_ROOT / "deploy" / "docker" / "docker-compose.yml"
    cmd = ["docker", "compose", "-f", str(compose_file), "logs"]
    if follow:
        cmd.append("-f")
    if service:
        cmd.append(service)
    raise typer.Exit(run_command(cmd))


# =============================================================================
# Test Commands
# =============================================================================


@test_app.command("all")
def test_all(
    coverage: bool = typer.Option(False, "--coverage", "-c", help="Generate coverage report"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run all tests across all packages."""
    console.print("[blue]Running all tests...[/blue]")

    cmd = ["pytest"]
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])

    raise typer.Exit(run_command(cmd))


@test_app.command("database")
def test_database():
    """Run database package tests."""
    console.print("[blue]Running database tests...[/blue]")
    raise typer.Exit(run_command(["pytest", "database/tests/", "-v"]))


@test_app.command("kg")
def test_kg():
    """Run knowledge graph package tests."""
    console.print("[blue]Running KG tests...[/blue]")
    raise typer.Exit(run_command(["pytest", "kg/tests/", "-v"]))


@test_app.command("graphrag")
def test_graphrag():
    """Run GraphRAG package tests."""
    console.print("[blue]Running GraphRAG tests...[/blue]")
    raise typer.Exit(run_command(["pytest", "graphrag/tests/", "-v"]))


@test_app.command("frontend")
def test_frontend():
    """Run frontend tests."""
    console.print("[blue]Running frontend tests...[/blue]")
    raise typer.Exit(run_command(["npm", "test"], cwd=PROJECT_ROOT / "frontend"))


# =============================================================================
# Code Quality Commands
# =============================================================================


@app.command()
def lint(
    fix: bool = typer.Option(False, "--fix", "-f", help="Auto-fix issues"),
):
    """Run linter (Ruff) on all Python code."""
    console.print("[blue]Running Ruff linter...[/blue]")

    cmd = ["ruff", "check", "database/", "kg/", "graphrag/"]
    if fix:
        cmd.append("--fix")

    raise typer.Exit(run_command(cmd))


@app.command()
def format(
    check: bool = typer.Option(False, "--check", help="Check only, don't modify"),
):
    """Format Python code with Ruff."""
    console.print("[blue]Formatting code...[/blue]")

    cmd = ["ruff", "format", "database/", "kg/", "graphrag/"]
    if check:
        cmd.append("--check")

    raise typer.Exit(run_command(cmd))


@app.command()
def typecheck():
    """Run type checker (mypy) on all Python code."""
    console.print("[blue]Running mypy type checker...[/blue]")
    raise typer.Exit(run_command(["mypy", "database/", "kg/", "graphrag/"]))


@app.command()
def quality():
    """Run all code quality checks (lint + typecheck)."""
    console.print("[blue]Running all quality checks...[/blue]\n")

    # Lint
    console.print("[bold]1. Linting (Ruff)...[/bold]")
    lint_result = run_command(["ruff", "check", "database/", "kg/", "graphrag/"])

    # Type check
    console.print("\n[bold]2. Type checking (mypy)...[/bold]")
    type_result = run_command(["mypy", "database/", "kg/", "graphrag/"])

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
def db_migrate():
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
def db_shell():
    """Open PostgreSQL shell."""
    console.print("[blue]Opening database shell...[/blue]")
    raise typer.Exit(run_command(["psql", "${DATABASE_URL}"]))


# =============================================================================
# Info Commands
# =============================================================================


@app.command()
def info():
    """Show project information."""
    table = Table(title="EleutherIA Project Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Website", "https://free-will.app")
    table.add_row("Repository", "github.com/romain-girardi-eng/EleutherIA")
    table.add_row("License", "CC BY 4.0")
    table.add_row("", "")
    table.add_row("KG Nodes", "2,193")
    table.add_row("KG Edges", "8,616")
    table.add_row("Ancient Works", "189")
    table.add_row("Passages", "16,968")
    table.add_row("", "")
    table.add_row("Backend", "FastAPI + Python 3.11+")
    table.add_row("Frontend", "React 19 + TypeScript")
    table.add_row("Database", "PostgreSQL + Qdrant")
    table.add_row("LLM", "Gemini 3 + Kimi K2.5")

    console.print(table)


@app.command()
def version():
    """Show CLI version."""
    from cli import __version__
    console.print(f"eleutheria CLI v{__version__}")


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
