"""In-memory retrieval helpers for KG snapshots.

These helpers keep GraphRAG useful when PostgreSQL/Supabase is down but the
knowledge graph snapshot is available. They intentionally return rows shaped
like the SQL passage queries used by the pipeline.
"""

from __future__ import annotations

import inspect
import json
import re
from typing import Any

from eleutheria_graphrag.agents.citability import (
    CitabilityTier,
    evidence_policy,
    stricter_decision,
)

PASSAGE_TYPES = {"passage", "quote"}
STOP_TERMS = {
    "about",
    "after",
    "also",
    "and",
    "avec",
    "dans",
    "des",
    "for",
    "from",
    "how",
    "les",
    "mais",
    "pour",
    "sur",
    "that",
    "the",
    "their",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
}
TERM_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ\u0370-\u03FF\u1F00-\u1FFF']+")


def db_is_connected(db: Any) -> bool:
    """Return whether a DatabaseService-like object is connected."""
    if db is None:
        return False
    checker = getattr(db, "is_connected", None)
    if callable(checker):
        try:
            result = checker()
            if inspect.isawaitable(result):
                close = getattr(result, "close", None)
                if callable(close):
                    close()
                return True
            return bool(result)
        except Exception:
            return False
    return bool(getattr(db, "pool", None))


def normalize_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def node_is_passage(node: dict[str, Any] | None) -> bool:
    return str((node or {}).get("type") or "").strip().lower() in PASSAGE_TYPES


def passage_row_from_node(
    deps: Any,
    node_id: str,
    *,
    confidence: float | None = None,
) -> dict[str, Any] | None:
    """Convert a snapshot passage/quote node into a SQL-shaped passage row."""
    node = getattr(deps, "node_lookup", {}).get(node_id)
    if not node_is_passage(node):
        return None

    decision = evidence_policy(node)
    if decision.tier is CitabilityTier.BLOCKED:
        return None

    metadata = normalize_mapping(node.get("metadata"))
    work_id = (
        metadata.get("work_id")
        or metadata.get("work_canonical_id")
        or _first_neighbor_id(deps, node_id, relation="part_of")
        or metadata.get("source_work")
        or "snapshot"
    )
    work_title = (
        metadata.get("work_title")
        or metadata.get("source_work")
        or _first_neighbor_label(deps, node_id, relation="part_of")
        or node.get("label")
        or "Unknown work"
    )
    author = metadata.get("author") or _first_neighbor_label(
        deps, node_id, relation="authored_by"
    )

    return {
        "passage_id": node_id,
        "kg_node_id": node_id,
        "db_passage_id": metadata.get("passage_id"),
        "work_id": str(work_id),
        "text_content": (
            node.get("description") or ""
            if decision.tier is CitabilityTier.CITABLE
            else ""
        ),
        "canonical_ref": metadata.get("canonical_ref") or metadata.get("cts_urn"),
        "sequence_number": metadata.get("sequence_number") or metadata.get("section"),
        "title": work_title,
        "author": author,
        "language": metadata.get("language") or node.get("language"),
        "confidence": 1.0 if confidence is None else confidence,
        "source": "kg_snapshot",
        "metadata": metadata,
        "evidence_tier": decision.tier.value,
        "evidence_notice": decision.prompt_notice,
    }


def node_for_passage_row(deps: Any, row: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve a SQL/snapshot passage row back to its honesty-bearing KG node."""

    lookup = getattr(deps, "node_lookup", {})
    for key in ("kg_node_id", "node_id"):
        value = str(row.get(key) or "")
        if value and value in lookup:
            return lookup[value]
    passage_id = str(row.get("passage_id") or row.get("id") or "")
    if passage_id in lookup and node_is_passage(lookup[passage_id]):
        return lookup[passage_id]
    if not passage_id:
        return None
    for node in lookup.values():
        if not node_is_passage(node):
            continue
        metadata = normalize_mapping(node.get("metadata"))
        # A related KG node must protect rows reached through that relation,
        # but must not taint an independently retrieved corpus UUID merely
        # because historical metadata still records the related passage id.
        if metadata.get("parity_status") == "related_not_exact_twin":
            continue
        if str(metadata.get("passage_id") or "") == passage_id:
            return node
    return None


def protect_passage_row(deps: Any, row: dict[str, Any]) -> dict[str, Any] | None:
    """Apply central citability to a row returned by any retrieval backend.

    Discovery-only rows retain bibliographic/locus metadata but lose all source
    text before they reach a tool result or prompt.  Blocked rows are omitted.
    """

    node = node_for_passage_row(deps, row)
    decision = stricter_decision(
        evidence_policy(node or normalize_mapping(row.get("metadata"))),
        evidence_policy(row),
    )
    if decision.tier is CitabilityTier.BLOCKED:
        return None
    protected = dict(row)
    protected["evidence_tier"] = decision.tier.value
    protected["evidence_notice"] = decision.prompt_notice
    if decision.tier is not CitabilityTier.CITABLE:
        protected["text_content"] = ""
    return protected


def linked_passage_rows(
    deps: Any,
    node_ids: list[str],
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return snapshot passage rows linked to the supplied KG nodes."""
    candidates: dict[str, float] = {}
    node_lookup = getattr(deps, "node_lookup", {})
    outgoing = getattr(deps, "outgoing_edges", {})
    incoming = getattr(deps, "incoming_edges", {})

    def add(node_id: str, score: float) -> None:
        if node_is_passage(node_lookup.get(node_id)):
            candidates[node_id] = max(score, candidates.get(node_id, 0.0))

    for anchor in node_ids:
        add(anchor, 1.0)

        for edge in outgoing.get(anchor, []):
            score = _edge_score(edge)
            add(str(edge.get("target") or edge.get("target_id") or ""), score)

        for edge in incoming.get(anchor, []):
            score = _edge_score(edge)
            add(str(edge.get("source") or edge.get("source_id") or ""), score)

    rows: list[dict[str, Any]] = []
    for passage_id, score in sorted(candidates.items(), key=lambda item: -item[1]):
        row = passage_row_from_node(deps, passage_id, confidence=score)
        if row:
            rows.append(row)
        if limit is not None and len(rows) >= limit:
            break
    return rows


def search_passage_rows(
    deps: Any,
    query: str,
    *,
    limit: int = 10,
    work_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Keyword search over passage nodes in the loaded snapshot."""
    terms = _terms(query)
    if not terms:
        return []

    scored: list[tuple[float, str]] = []
    for node_id, node in getattr(deps, "node_lookup", {}).items():
        if not node_is_passage(node):
            continue
        row = passage_row_from_node(deps, node_id)
        if not row:
            continue
        if work_filter and not _matches_work_filter(row, work_filter):
            continue

        metadata = normalize_mapping(node.get("metadata"))
        haystack = " ".join(
            str(part or "")
            for part in (
                node.get("label"),
                node.get("description"),
                metadata.get("canonical_ref"),
                metadata.get("work_title"),
                metadata.get("source_work"),
                metadata.get("author"),
                " ".join(str(item) for item in metadata.get("themes", []) or []),
                " ".join(str(item) for item in metadata.get("key_terms", []) or []),
            )
        ).lower()
        score = sum(1.0 for term in terms if term in haystack)
        if query.lower() in haystack:
            score += 4.0
        if score > 0:
            scored.append((score, node_id))

    rows: list[dict[str, Any]] = []
    for score, node_id in sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]:
        row = passage_row_from_node(deps, node_id, confidence=score)
        if row:
            row["rank"] = score
            rows.append(row)
    return rows


def translation_for_passage(deps: Any, passage_id: str) -> dict[str, Any] | None:
    """Find an English translation passage linked by translation_of in the snapshot."""
    source_node_ids = _kg_node_ids_for_passage_id(deps, passage_id)
    if not source_node_ids:
        return None

    translation_ids: list[str] = []
    seen: set[str] = set()
    for source_id in source_node_ids:
        for edge in getattr(deps, "incoming_edges", {}).get(source_id, []):
            if edge.get("relation") == "translation_of":
                candidate = str(edge.get("source") or "")
                if candidate not in seen:
                    translation_ids.append(candidate)
                    seen.add(candidate)
        for edge in getattr(deps, "outgoing_edges", {}).get(source_id, []):
            if edge.get("relation") == "translation_of":
                candidate = str(edge.get("target") or "")
                if candidate not in seen:
                    translation_ids.append(candidate)
                    seen.add(candidate)

    translation_ids.sort(key=lambda node_id: _translation_priority(deps, node_id))
    for node_id in translation_ids:
        row = passage_row_from_node(deps, node_id, confidence=1.0)
        if row and row.get("text_content"):
            row["source"] = "kg_node_description"
            return row
    return None


def _kg_node_ids_for_passage_id(deps: Any, passage_id: str) -> list[str]:
    node_lookup = getattr(deps, "node_lookup", {})
    if passage_id in node_lookup:
        node = node_lookup[passage_id]
        if (
            node_is_passage(node)
            and evidence_policy(node).tier is CitabilityTier.CITABLE
        ):
            return [passage_id]
        return []

    matches: list[str] = []
    for node_id, node in node_lookup.items():
        if not node_is_passage(node):
            continue
        if evidence_policy(node).tier is not CitabilityTier.CITABLE:
            continue
        metadata = normalize_mapping(node.get("metadata"))
        if str(metadata.get("passage_id") or "") == str(passage_id):
            matches.append(node_id)
    return matches


def _terms(text: str) -> list[str]:
    return [
        term.lower()
        for term in TERM_RE.findall(text)
        if len(term) > 2 and term.lower() not in STOP_TERMS
    ][:24]


def _edge_score(edge: dict[str, Any]) -> float:
    metadata = normalize_mapping(edge.get("metadata"))
    raw = metadata.get("confidence", edge.get("weight", metadata.get("weight", 1.0)))
    try:
        score = float(raw)
    except (TypeError, ValueError) as _exc:
        del _exc
        score = 1.0
    relation = edge.get("relation")
    if relation in {"evidenced_by", "grounded_in", "source_for"}:
        score += 0.3
    elif relation in {"discusses", "part_of", "authored_by"}:
        score += 0.1
    return score


def _first_neighbor_id(deps: Any, node_id: str, *, relation: str) -> str | None:
    for edge in getattr(deps, "outgoing_edges", {}).get(node_id, []):
        if edge.get("relation") == relation and edge.get("target"):
            return str(edge["target"])
    return None


def _first_neighbor_label(deps: Any, node_id: str, *, relation: str) -> str | None:
    neighbor_id = _first_neighbor_id(deps, node_id, relation=relation)
    if not neighbor_id:
        return None
    return (getattr(deps, "node_lookup", {}).get(neighbor_id) or {}).get("label")


def _matches_work_filter(row: dict[str, Any], work_filter: str) -> bool:
    needle = work_filter.lower()
    haystack = " ".join(
        str(row.get(key) or "")
        for key in ("work_id", "title", "canonical_ref", "author")
    ).lower()
    return needle in haystack


def _translation_priority(deps: Any, node_id: str) -> tuple[int, str]:
    node = getattr(deps, "node_lookup", {}).get(node_id, {})
    metadata = normalize_mapping(node.get("metadata"))
    language = str(metadata.get("language") or node.get("language") or "").lower()
    label = str(node.get("label") or "").lower()
    score = 0
    if language in {"eng", "en"}:
        score += 4
    if node_id.endswith("_en"):
        score += 3
    if "translation" in label or "english" in label:
        score += 1
    return (-score, node_id)
