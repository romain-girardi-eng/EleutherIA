"""Deploy-container entrypoints and their local imports must parse on Python 3.12."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_312_IMAGE = "python:3.12-slim"
PYTHON_SCRIPT = re.compile(r"\bpython\s+([A-Za-z0-9_./-]+\.py)\b")
SOURCE_ROOTS = (ROOT, *(path for path in ROOT.glob("*/src") if path.is_dir()))


def _deploy_entrypoints() -> set[Path]:
    """Find scripts run in Makefile shell commands that use the 3.12 image."""
    logical_lines = (ROOT / "Makefile").read_text(encoding="utf-8").replace("\\\n", " ")
    entrypoints: set[Path] = set()
    for line in logical_lines.splitlines():
        if PYTHON_312_IMAGE not in line:
            continue
        entrypoints.update(ROOT / match for match in PYTHON_SCRIPT.findall(line))
    return entrypoints


def _resolve_module(module: str) -> Path | None:
    relative = Path(*module.split("."))
    for source_root in SOURCE_ROOTS:
        module_file = source_root / relative.with_suffix(".py")
        if module_file.is_file():
            return module_file
        package_file = source_root / relative / "__init__.py"
        if package_file.is_file():
            return package_file
    return None


def _module_name(path: Path) -> tuple[str, str]:
    for source_root in SOURCE_ROOTS:
        try:
            relative = path.relative_to(source_root)
        except ValueError:
            continue
        parts = list(relative.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
            return ".".join(parts), ".".join(parts)
        return ".".join(parts), ".".join(parts[:-1])
    raise AssertionError(f"module is outside repository source roots: {path}")


def _imported_modules(path: Path, tree: ast.AST) -> Iterable[str]:
    _module, package = _module_name(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue

        if node.level:
            package_parts = package.split(".") if package else []
            keep = len(package_parts) - node.level + 1
            base_parts = package_parts[: max(keep, 0)]
            if node.module:
                base_parts.extend(node.module.split("."))
            base = ".".join(base_parts)
        else:
            base = node.module or ""

        if base:
            yield base
        for alias in node.names:
            if alias.name != "*":
                yield ".".join(part for part in (base, alias.name) if part)


def _transitive_local_modules(entrypoints: set[Path]) -> tuple[set[Path], list[str]]:
    pending = list(entrypoints)
    visited: set[Path] = set()
    syntax_errors: list[str] = []

    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        source = path.read_text(encoding="utf-8")
        current_tree = ast.parse(source, filename=str(path))
        try:
            ast.parse(source, filename=str(path), feature_version=(3, 12))
        except SyntaxError as exc:
            relative = path.relative_to(ROOT)
            syntax_errors.append(f"{relative}:{exc.lineno}: {exc.msg}")

        for module in _imported_modules(path, current_tree):
            imported_path = _resolve_module(module)
            if imported_path is not None and imported_path not in visited:
                pending.append(imported_path)

    return visited, syntax_errors


def test_deploy_import_graph_parses_on_python_312() -> None:
    entrypoints = _deploy_entrypoints()
    assert entrypoints, (
        f"no Python entrypoint found in Makefile commands using {PYTHON_312_IMAGE}"
    )
    missing = sorted(
        str(path.relative_to(ROOT)) for path in entrypoints if not path.is_file()
    )
    assert not missing, f"Python 3.12 deploy entrypoints do not exist: {missing}"

    modules, syntax_errors = _transitive_local_modules(entrypoints)
    checked = ", ".join(sorted(str(path.relative_to(ROOT)) for path in modules))
    assert not syntax_errors, (
        "repository modules imported by Python 3.12 deploy entrypoints contain "
        f"unsupported syntax:\n{chr(10).join(sorted(syntax_errors))}\n"
        f"checked modules: {checked}"
    )
