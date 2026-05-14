"""SHACL shape graph loaders.

Shapes are split into two subdirectories:

- ``invariants/`` — true data invariants (severity ``sh:Violation``). Driven
  by ``edge_types.json`` source/target type constraints. A violation here
  is a data bug and blocks conformance.
- ``quality/`` — quality goals (severity ``sh:Warning``). Drives the triage
  backlog without blocking conformance.

Three loaders are exposed:

- :func:`load_invariant_shapes` — only ``invariants/``
- :func:`load_quality_shapes` — only ``quality/``
- :func:`load_shapes` — the union, for the legacy callers that want both
"""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph

_SHAPES_DIR = Path(__file__).parent
_INVARIANTS_DIR = _SHAPES_DIR / "invariants"
_QUALITY_DIR = _SHAPES_DIR / "quality"


def _load_from(directory: Path) -> Graph:
    graph = Graph()
    if not directory.exists():
        return graph
    for ttl in sorted(directory.rglob("*.ttl")):
        graph.parse(ttl, format="turtle")
    return graph


def load_invariant_shapes(shapes_dir: Path | None = None) -> Graph:
    """Load just the invariant shapes (severity ``sh:Violation``)."""
    directory = shapes_dir or _INVARIANTS_DIR
    return _load_from(directory)


def load_quality_shapes(shapes_dir: Path | None = None) -> Graph:
    """Load just the quality shapes (severity ``sh:Warning``)."""
    directory = shapes_dir or _QUALITY_DIR
    return _load_from(directory)


def load_shapes(shapes_dir: Path | None = None) -> Graph:
    """Load the union of invariants + quality shapes.

    If ``shapes_dir`` is given, recursively reads every ``*.ttl`` underneath
    (legacy behavior). Otherwise loads both ``invariants/`` and ``quality/``
    from the package's own shapes directory.
    """
    if shapes_dir is not None:
        return _load_from(shapes_dir)
    graph = Graph()
    for ttl in sorted(_INVARIANTS_DIR.rglob("*.ttl")):
        graph.parse(ttl, format="turtle")
    for ttl in sorted(_QUALITY_DIR.rglob("*.ttl")):
        graph.parse(ttl, format="turtle")
    return graph


__all__ = [
    "load_invariant_shapes",
    "load_quality_shapes",
    "load_shapes",
]
