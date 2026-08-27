"""Deploy-critical imports must remain parseable by Python 3.12.

The production schema and data deploy entrypoints run in ``python:3.12-slim``.
Walk their repository-local imports transitively so newer syntax cannot hide in
a shared module that the deployment container imports at runtime.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY_ENTRYPOINTS = (
    Path("database/scripts/apply_schema.py"),
    Path("scripts/deploy_data_staged.py"),
)


def _source_roots(repo_root: Path) -> tuple[Path, ...]:
    return (repo_root / "graphrag" / "src", repo_root)


def _module_name(path: Path, source_roots: Iterable[Path]) -> tuple[str, bool]:
    for source_root in source_roots:
        try:
            relative = path.relative_to(source_root)
        except ValueError:
            continue
        parts = list(relative.with_suffix("").parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts.pop()
        return ".".join(parts), is_package
    raise ValueError(f"{path} is outside the configured source roots")


def _resolve_module(module: str, source_roots: Iterable[Path]) -> set[Path]:
    """Resolve a local module and the package initializers Python executes."""
    resolved: set[Path] = set()
    parts = module.split(".") if module else []
    for source_root in source_roots:
        for package_depth in range(1, len(parts) + 1):
            initializer = source_root.joinpath(*parts[:package_depth], "__init__.py")
            if initializer.is_file():
                resolved.add(initializer.resolve())

        module_file = source_root.joinpath(*parts).with_suffix(".py")
        package_file = source_root.joinpath(*parts, "__init__.py")
        if module_file.is_file():
            resolved.add(module_file.resolve())
        if package_file.is_file():
            resolved.add(package_file.resolve())
    return resolved


def _absolute_from_module(
    node: ast.ImportFrom,
    current_module: str,
    current_is_package: bool,
) -> str:
    if node.level == 0:
        return node.module or ""

    package_parts = current_module.split(".")
    if not current_is_package:
        package_parts.pop()
    parent_hops = node.level - 1
    if parent_hops:
        package_parts = package_parts[:-parent_hops]
    if node.module:
        package_parts.extend(node.module.split("."))
    return ".".join(package_parts)


def discover_repo_local_files(
    entrypoints: Iterable[Path],
    *,
    repo_root: Path,
) -> set[Path]:
    """Return entrypoints and all repository-local modules they import."""
    source_roots = _source_roots(repo_root)
    pending = [(repo_root / path).resolve() for path in entrypoints]
    discovered: set[Path] = set()

    while pending:
        path = pending.pop()
        if path in discovered:
            continue
        discovered.add(path)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        current_module, current_is_package = _module_name(path, source_roots)

        imported_paths: set[Path] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_paths.update(_resolve_module(alias.name, source_roots))
            elif isinstance(node, ast.ImportFrom):
                base_module = _absolute_from_module(
                    node, current_module, current_is_package
                )
                imported_paths.update(_resolve_module(base_module, source_roots))
                for alias in node.names:
                    if alias.name != "*":
                        imported_paths.update(
                            _resolve_module(
                                ".".join(filter(None, (base_module, alias.name))),
                                source_roots,
                            )
                        )
        pending.extend(imported_paths - discovered)

    return discovered


def _python_312_syntax_errors(paths: Iterable[Path]) -> list[str]:
    errors: list[str] = []
    for path in sorted(paths):
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source, filename=str(path), feature_version=(3, 12))
        except SyntaxError as exc:
            errors.append(f"{path}:{exc.lineno}:{exc.offset}: {exc.msg}")
    return errors


def test_deploy_import_graph_is_python_312_compatible() -> None:
    deployed_files = discover_repo_local_files(
        DEPLOY_ENTRYPOINTS,
        repo_root=ROOT,
    )
    errors = _python_312_syntax_errors(deployed_files)
    assert not errors, "Python 3.12-incompatible deploy imports:\n" + "\n".join(errors)


def test_transitive_import_discovery_reaches_incompatible_dependency(
    tmp_path: Path,
) -> None:
    entrypoint = tmp_path / "entrypoint.py"
    dependency = tmp_path / "dependency.py"
    entrypoint.write_text(
        "def load_dependency():\n    import dependency\n",
        encoding="utf-8",
    )
    dependency.write_text(
        "try:\n    pass\nexcept TypeError, ValueError:\n    pass\n",
        encoding="utf-8",
    )

    discovered = discover_repo_local_files(
        (Path("entrypoint.py"),),
        repo_root=tmp_path,
    )

    assert discovered == {entrypoint.resolve(), dependency.resolve()}
    errors = _python_312_syntax_errors(discovered)
    assert len(errors) == 1
    assert str(dependency) in errors[0]
    assert "Python 3.14 and greater" in errors[0]
