"""SHACL validation as a quality gate over the EleutherIA RDF graph.

Wraps :func:`pyshacl.validate` and reshapes its native rdflib report into a
structured :class:`ValidationReport` that downstream tools (CLI audit, CI,
Markdown reports) can consume without re-parsing SHACL triples.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Final

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF
from rdflib.term import Node

SH: Final[Namespace] = Namespace("http://www.w3.org/ns/shacl#")

# Maps the verbose SHACL severity IRIs to terse strings used in reports.
_SEVERITY_BY_IRI: Final[dict[str, str]] = {
    str(SH.Violation): "violation",
    str(SH.Warning): "warning",
    str(SH.Info): "info",
}


@dataclass(slots=True, frozen=True)
class Violation:
    focus_node: str
    source_shape: str | None
    severity: str
    message: str
    source_constraint_component: str | None
    result_path: str | None
    value: str | None


@dataclass(slots=True)
class ValidationReport:
    conforms: bool
    violation_count: int
    violations: list[Violation] = field(default_factory=list)
    duration_seconds: float = 0.0

    def by_severity(self) -> Counter[str]:
        return Counter(v.severity for v in self.violations)

    def by_constraint(self) -> Counter[str]:
        return Counter(
            v.source_constraint_component or "<unknown>" for v in self.violations
        )

    def by_shape(self) -> Counter[str]:
        return Counter(v.source_shape or "<unknown>" for v in self.violations)

    def format_markdown_report(self, *, max_examples: int = 10) -> str:
        lines: list[str] = [
            "# SHACL Validation Report",
            "",
            f"- Conforms: {self.conforms}",
            f"- Violation count: {self.violation_count}",
            f"- Validation duration: {self.duration_seconds:.2f}s",
            "",
            "## By severity",
            "",
        ]
        for severity, count in self.by_severity().most_common():
            lines.append(f"- `{severity}`: {count}")

        lines.extend(["", "## By shape", ""])
        for shape, count in self.by_shape().most_common(20):
            lines.append(f"- `{shape}`: {count}")

        lines.extend(["", "## By constraint component", ""])
        for component, count in self.by_constraint().most_common():
            lines.append(f"- `{component}`: {count}")

        lines.extend(["", "## Examples", ""])
        for v in self.violations[:max_examples]:
            lines.append(f"- `{v.focus_node}` ({v.severity}) — {v.message}")
        return "\n".join(lines) + "\n"


def _str_or_none(node: Node | None) -> str | None:
    return str(node) if node is not None else None


def _extract_violations(results_graph: Graph) -> list[Violation]:
    violations: list[Violation] = []
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        focus = results_graph.value(result, SH.focusNode)
        shape = results_graph.value(result, SH.sourceShape)
        severity_iri = results_graph.value(result, SH.resultSeverity)
        message_node = results_graph.value(result, SH.resultMessage)
        component = results_graph.value(result, SH.sourceConstraintComponent)
        path = results_graph.value(result, SH.resultPath)
        value = results_graph.value(result, SH.value)

        severity = _SEVERITY_BY_IRI.get(str(severity_iri), "violation")
        # Anonymous shape IRIs (blank nodes from sh:property) are noisy —
        # collapse them to None so callers don't choke on bnode labels.
        shape_str: str | None = None
        if isinstance(shape, URIRef):
            shape_str = str(shape)

        violations.append(
            Violation(
                focus_node=_str_or_none(focus) or "<unknown>",
                source_shape=shape_str,
                severity=severity,
                message=str(message_node) if message_node else "",
                source_constraint_component=_str_or_none(component),
                result_path=_str_or_none(path),
                value=_str_or_none(value),
            )
        )
    return violations


def validate_kg(data_graph: Graph, shapes_graph: Graph) -> ValidationReport:
    """Run SHACL validation and return a structured report.

    ``data_graph`` is the rdflib graph produced by
    :func:`eleutheria_kg.semantic.build_graph`. ``shapes_graph`` is the
    combined shape graph loaded from
    :func:`eleutheria_kg.semantic.shapes.load_shapes`.
    """
    from pyshacl import validate as _shacl_validate  # local import: heavy

    start = time.perf_counter()
    conforms, results_graph, _report_text = _shacl_validate(
        data_graph,
        shacl_graph=shapes_graph,
        # We deliberately skip OWL-RL inference: shapes are written against
        # the kg-namespaced classes/properties that build_graph already
        # emits, so reasoning would only slow things down.
        inference="none",
        meta_shacl=False,
        advanced=True,
        debug=False,
    )
    duration = time.perf_counter() - start

    violations = _extract_violations(results_graph)
    return ValidationReport(
        conforms=bool(conforms),
        violation_count=len(violations),
        violations=violations,
        duration_seconds=duration,
    )


def validate_kg_invariants(data_graph: Graph) -> ValidationReport:
    """Validate the KG against the invariant shapes only.

    Invariants are the constraints whose violation indicates a true data
    bug (edge domain/range from ``edge_types.json``). Quality goals
    (NeedsEvidence, IdPrefix conventions, period whitelist, description
    hygiene) live in ``shapes/quality/`` and are validated separately via
    :func:`validate_kg`. This split lets CI gate on invariants while the
    quality backlog stays visible without blocking conformance.
    """
    # Local import to avoid circular dependency (shapes module imports
    # nothing from validator, but loading shapes is a heavy operation we
    # do not want at module import time).
    from eleutheria_kg.semantic.shapes import load_invariant_shapes

    return validate_kg(data_graph, load_invariant_shapes())


__all__ = [
    "ValidationReport",
    "Violation",
    "validate_kg",
    "validate_kg_invariants",
]
