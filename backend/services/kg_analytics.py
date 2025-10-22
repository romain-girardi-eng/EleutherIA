#!/usr/bin/env python3
"""
Knowledge Graph analytics helpers for high-level visualizations
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
import importlib.util
import logging
import math
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)

KGNode = Dict[str, Any]
KGEdge = Dict[str, Any]
KGData = Dict[str, Any]

PERIOD_METADATA: Dict[str, Dict[str, Optional[int]]] = {
    "Presocratic": {"label": "Presocratic", "start": -600, "end": -450},
    "Classical Greek": {"label": "Classical Greek", "start": -450, "end": -323},
    "Hellenistic Greek": {"label": "Hellenistic Greek", "start": -323, "end": -31},
    "Roman Republican": {"label": "Roman Republican", "start": -146, "end": -27},
    "Roman Imperial": {"label": "Roman Imperial", "start": -27, "end": 300},
    "Patristic": {"label": "Patristic", "start": 150, "end": 450},
    "Late Antiquity": {"label": "Late Antiquity", "start": 300, "end": 600},
}

ANCIENT_PERIODS: Set[str] = {
    "Presocratic",
    "Classical Greek",
    "Hellenistic Greek",
    "Roman Republican",
    "Roman Imperial",
    "Patristic",
    "Late Antiquity",
}

ANCIENT_ROLES: Set[str] = {
    "ancient_primary",
    "late_antique_theologian",
    "medieval_development",
    "early_modern_transition",
}

MODERN_ROLES: Set[str] = {
    "modern_scholar",
    "modern_analytic_philosopher",
}

MODERN_WORK_CATEGORIES: Set[str] = {
    "scholarly_work",
    "scholarly_article",
    "modern_reception",
    "contemporary_scholar",
}

COMMUNITY_ALGORITHM_DESCRIPTIONS: Dict[str, str] = {
    "leiden": (
        "Leiden (requires python-igraph + leidenalg): guarantees well-connected communities and "
        "iteratively refines partitions for higher modularity."
    ),
    "louvain": (
        "Louvain (requires python-louvain): classic modularity optimisation; fast but may produce "
        "disconnected communities."
    ),
    "greedy": (
        "Greedy modularity (NetworkX built-in): dependency-free fallback that maximises modularity "
        "hierarchically; slower and less precise on large graphs."
    ),
}

COMMUNITY_COLOR_PALETTE: List[str] = [
    "#2563eb",
    "#16a34a",
    "#db2777",
    "#f97316",
    "#0ea5e9",
    "#9333ea",
    "#22c55e",
    "#facc15",
    "#ef4444",
    "#8b5cf6",
    "#14b8a6",
    "#f59e0b",
    "#3b82f6",
    "#ec4899",
    "#10b981",
    "#6366f1",
]

STOPWORDS: Set[str] = {
    "the",
    "and",
    "of",
    "to",
    "in",
    "a",
    "for",
    "on",
    "with",
    "by",
    "an",
    "as",
    "at",
    "from",
    "that",
    "this",
    "through",
    "into",
    "within",
    "about",
    "its",
    "their",
    "between",
    "history",
    "philosophy",
    "argument",
    "free",
    "will",
    "fate",
}


def _algorithm_available(name: str) -> bool:
    """Check whether the dependencies for a community detection algorithm are available."""
    if name == "leiden":
        return bool(
            importlib.util.find_spec("igraph") and importlib.util.find_spec("leidenalg")
        )
    if name == "louvain":
        return bool(importlib.util.find_spec("community"))
    if name == "greedy":
        return True
    return False


def _build_network_graph(kg_data: KGData) -> nx.Graph:
    """Build an undirected NetworkX graph from KG data."""
    graph = nx.Graph()
    nodes = kg_data.get("nodes", [])
    edges = kg_data.get("edges", [])

    for node in nodes:
        node_id = node.get("id")
        if node_id:
            graph.add_node(node_id)

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        weight = edge.get("weight", 1.0)
        try:
            weight_value = float(weight)
        except (TypeError, ValueError):
            weight_value = 1.0
        if graph.has_edge(source, target):
            graph[source][target]["weight"] += weight_value
        else:
            graph.add_edge(source, target, weight=weight_value)

    return graph


def _run_leiden(graph: nx.Graph) -> Tuple[Dict[str, int], Optional[float]]:
    """Execute the Leiden algorithm using igraph and leidenalg."""
    import igraph as ig  # type: ignore
    import leidenalg  # type: ignore

    if graph.number_of_nodes() == 0:
        return {}, None

    node_to_index = {node: idx for idx, node in enumerate(graph.nodes())}
    index_to_node = {idx: node for node, idx in node_to_index.items()}

    ig_graph = ig.Graph(
        n=len(node_to_index),
        edges=[(node_to_index[u], node_to_index[v]) for u, v in graph.edges()],
        directed=False,
    )
    weights = [graph[u][v].get("weight", 1.0) for u, v in graph.edges()]
    if weights:
        ig_graph.es["weight"] = weights
        partition = leidenalg.find_partition(
            ig_graph,
            leidenalg.ModularityVertexPartition,
            weights=weights,
        )
    else:
        partition = leidenalg.find_partition(
            ig_graph,
            leidenalg.ModularityVertexPartition,
        )

    membership = partition.membership
    assignments = {
        index_to_node[idx]: community_id for idx, community_id in enumerate(membership)
    }
    try:
        quality = float(partition.quality())
    except Exception:
        quality = None
    return assignments, quality


def _run_louvain(graph: nx.Graph) -> Tuple[Dict[str, int], Optional[float]]:
    """Execute the Louvain algorithm using python-louvain."""
    import community as community_louvain  # type: ignore

    if graph.number_of_nodes() == 0:
        return {}, None

    assignments = community_louvain.best_partition(graph, weight="weight")
    try:
        quality = float(community_louvain.modularity(assignments, graph))
    except Exception:
        quality = None
    return assignments, quality


def _run_greedy(graph: nx.Graph) -> Tuple[Dict[str, int], Optional[float]]:
    """Execute greedy modularity maximisation using NetworkX."""
    if graph.number_of_nodes() == 0:
        return {}, None

    communities = list(
        nx.algorithms.community.greedy_modularity_communities(graph, weight="weight")
    )
    assignments: Dict[str, int] = {}
    for idx, community in enumerate(communities):
        for node in community:
            assignments[node] = idx
    try:
        quality = float(
            nx.algorithms.community.quality.modularity(
                graph, communities, weight="weight"
            )
        )
    except Exception:
        quality = None
    return assignments, quality


def detect_communities(
    kg_data: KGData, algorithm: str = "auto"
) -> Dict[str, Any]:
    """Detect communities using the requested algorithm with intelligent fallbacks."""
    requested = (algorithm or "auto").lower()
    available_map = {
        name: _algorithm_available(name) for name in ("leiden", "louvain", "greedy")
    }

    graph = _build_network_graph(kg_data)
    if graph.number_of_edges() == 0 or graph.number_of_nodes() == 0:
        return {
            "algorithm_requested": requested,
            "algorithm_used": "none",
            "quality": None,
            "communities": [],
            "node_assignments": {},
            "available_algorithms": [
                {"name": name, "available": available, "description": desc}
                for name, available in available_map.items()
                for desc in [COMMUNITY_ALGORITHM_DESCRIPTIONS[name]]
            ],
        }

    def execute(algo: str) -> Optional[Tuple[Dict[str, int], Optional[float]]]:
        try:
            if algo == "leiden" and available_map["leiden"]:
                return _run_leiden(graph)
            if algo == "louvain" and available_map["louvain"]:
                return _run_louvain(graph)
            if algo == "greedy":
                return _run_greedy(graph)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Community detection failed for %s: %s", algo, exc)
        return None

    assignments: Dict[str, int] = {}
    quality: Optional[float] = None
    algorithm_used = "none"

    if requested == "auto" or requested not in ("leiden", "louvain", "greedy"):
        for candidate in ("leiden", "louvain", "greedy"):
            result = execute(candidate)
            if result:
                assignments, quality = result
                algorithm_used = candidate
                break
    else:
        result = execute(requested)
        if result:
            assignments, quality = result
            algorithm_used = requested
        else:
            # fall back to greedy
            fallback = execute("greedy")
            if fallback:
                assignments, quality = fallback
                algorithm_used = "greedy"

    if not assignments:
        return {
            "algorithm_requested": requested,
            "algorithm_used": "none",
            "quality": None,
            "communities": [],
            "node_assignments": {},
            "available_algorithms": [
                {"name": name, "available": available, "description": desc}
                for name, available in available_map.items()
                for desc in [COMMUNITY_ALGORITHM_DESCRIPTIONS[name]]
            ],
        }

    counts = Counter(assignments.values())
    sorted_counts = sorted(
        counts.items(), key=lambda item: (-item[1], item[0])
    )

    community_summaries: List[Dict[str, Any]] = []
    color_map: Dict[int, str] = {}
    for index, (community_id, size) in enumerate(sorted_counts):
        color = COMMUNITY_COLOR_PALETTE[index % len(COMMUNITY_COLOR_PALETTE)]
        color_map[int(community_id)] = color
        community_summaries.append(
            {
                "id": int(community_id),
                "size": int(size),
                "order": index,
                "color": color,
                "label": f"Community {index + 1}",
            }
        )

    return {
        "algorithm_requested": requested,
        "algorithm_used": algorithm_used,
        "quality": quality,
        "communities": community_summaries,
        "node_assignments": assignments,
        "available_algorithms": [
            {"name": name, "available": available, "description": desc}
            for name, available in available_map.items()
            for desc in [COMMUNITY_ALGORITHM_DESCRIPTIONS[name]]
        ],
        "colors": color_map,
    }


def apply_filters(
    kg_data: KGData,
    filters: Optional[Dict[str, Any]] = None,
) -> Tuple[List[KGNode], List[KGEdge], Dict[str, KGNode]]:
    """Apply frontend filters to KG nodes and edges"""
    filters = filters or {}
    nodes: List[KGNode] = kg_data.get("nodes", [])
    edges: List[KGEdge] = kg_data.get("edges", [])

    node_types: Set[str] = set(filters.get("nodeTypes") or [])
    periods: Set[str] = set(filters.get("periods") or [])
    schools: Set[str] = set(filters.get("schools") or [])
    relations_filter: Set[str] = set(filters.get("relations") or [])
    search_term: Optional[str] = (filters.get("searchTerm") or "").strip().lower() or None

    def node_matches(node: KGNode) -> bool:
        if node_types and node.get("type") not in node_types:
            return False
        if periods and node.get("period") not in periods:
            return False
        if schools and node.get("school") not in schools:
            return False
        if search_term:
            haystacks = [
                node.get("label", ""),
                node.get("description", ""),
                node.get("summary", ""),
            ]
            if not any(search_term in (text or "").lower() for text in haystacks):
                return False
        return True

    filtered_nodes = [node for node in nodes if node_matches(node)]
    node_lookup: Dict[str, KGNode] = {node["id"]: node for node in filtered_nodes}

    def edge_matches(edge: KGEdge) -> bool:
        if relations_filter and edge.get("relation") not in relations_filter:
            return False
        source_id = edge.get("source")
        target_id = edge.get("target")
        return source_id in node_lookup and target_id in node_lookup

    filtered_edges = [edge for edge in edges if edge_matches(edge)]

    return filtered_nodes, filtered_edges, node_lookup


def get_period_metadata(period: Optional[str]) -> Tuple[str, Optional[int], Optional[int]]:
    """Resolve period metadata from controlled vocabulary"""
    if not period:
        return "Unspecified", None, None
    meta = PERIOD_METADATA.get(period)
    if not meta:
        return period, None, None
    return meta["label"], meta["start"], meta["end"]


DATE_RANGE_PATTERN = re.compile(
    r"(?P<prefix>c\.|ca\.|circa)?\s*(?P<start>-?\d{1,4})\s*[-–]\s*(?P<end>-?\d{1,4})\s*(?P<era>BCE|CE)?",
    flags=re.IGNORECASE,
)

SINGLE_YEAR_PATTERN = re.compile(
    r"(?P<prefix>c\.|ca\.|circa)?\s*(?P<year>-?\d{1,4})\s*(?P<era>BCE|CE)?",
    flags=re.IGNORECASE,
)

CENTURY_PATTERN = re.compile(
    r"(?P<order>(?:early|mid|late)\s+)?(?P<number>\d{1,2})(?:st|nd|rd|th)?\s+century\s+(?P<era>BCE|CE)",
    flags=re.IGNORECASE,
)


def era_adjust(value: int, era: Optional[str]) -> int:
    """Adjust year based on BCE/CE indicator"""
    if era and era.upper() == "BCE":
        return -abs(value)
    return value


def parse_year_range(raw: Any) -> Tuple[Optional[int], Optional[int]]:
    """Attempt to parse a year range from textual metadata"""
    if raw is None:
        return None, None

    if isinstance(raw, (int, float)):
        value = int(raw)
        return value, value

    text = str(raw).strip()
    if not text:
        return None, None

    match = DATE_RANGE_PATTERN.search(text)
    if match:
        start = era_adjust(int(match.group("start")), match.group("era"))
        end = era_adjust(int(match.group("end")), match.group("era"))
        if start > end:
            start, end = end, start
        return start, end

    match = SINGLE_YEAR_PATTERN.search(text)
    if match:
        year = era_adjust(int(match.group("year")), match.group("era"))
        return year, year

    match = CENTURY_PATTERN.search(text)
    if match:
        number = int(match.group("number"))
        era = match.group("era")
        base_start = (number - 1) * 100
        base_end = number * 100
        if era and era.upper() == "BCE":
            base_start, base_end = -base_end, -base_start
        order = (match.group("order") or "").strip().lower()
        if order == "early":
            return base_start, base_start + 33
        if order == "mid":
            return base_start + 33, base_start + 66
        if order == "late":
            return base_start + 66, base_end
        return base_start, base_end

    return None, None


def infer_node_years(node: KGNode, fallback: Tuple[Optional[int], Optional[int]]) -> Tuple[Optional[int], Optional[int]]:
    """Infer start/end years for a node using several fields"""
    candidates = [
        node.get("dates"),
        node.get("approximate_dates"),
        node.get("floruit"),
        node.get("birth"),
        node.get("death"),
        node.get("date"),
        node.get("year"),
    ]

    for raw in candidates:
        parsed = parse_year_range(raw)
        if any(parsed):
            return parsed

    return fallback


def extract_keywords(text: Optional[str], limit: int = 3) -> List[str]:
    """Rough keyword extraction using frequency and stopword filtering"""
    if not text:
        return []

    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower())
    filtered = [token for token in tokens if token not in STOPWORDS and len(token) > 3]
    if not filtered:
        return []

    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(limit)]


def slugify(value: str, prefix: str) -> str:
    """Generate predictable IDs for synthetic evidence nodes"""
    safe = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return f"{prefix}_{safe[:40]}" if safe else f"{prefix}_item"


def classify_evidence_node(node: KGNode) -> Optional[str]:
    """Classify a node as ancient or modern evidence"""
    node_type = node.get("type")
    period = node.get("period")
    role = node.get("scholarly_role")
    category = node.get("category")
    year = node.get("year")

    if node_type in {"work", "quote"}:
        if category in MODERN_WORK_CATEGORIES:
            return "modern"
        if isinstance(year, int) and year >= 1400:
            return "modern"
        if isinstance(year, int) and year <= 600:
            return "ancient"
        if period in ANCIENT_PERIODS:
            return "ancient"
        if category == "scholarly_work":
            return "modern"
        date_range = parse_year_range(node.get("date"))
        if any(date_range):
            if date_range[1] and date_range[1] >= 1400:
                return "modern"
            return "ancient"
    elif node_type == "person":
        if role in MODERN_ROLES:
            return "modern"
        if role in ANCIENT_ROLES:
            return "ancient"
        if period in ANCIENT_PERIODS:
            return "ancient"
    elif node_type == "argument" and period in ANCIENT_PERIODS:
        return "ancient"

    return None


def build_timeline_overview(
    kg_data: KGData,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct timeline overview for chronological storyline panel"""
    nodes, edges, _ = apply_filters(kg_data, filters)

    node_edge_relations: Dict[str, List[KGEdge]] = defaultdict(list)
    for edge in edges:
        node_edge_relations[edge.get("source")].append(edge)
        node_edge_relations[edge.get("target")].append(edge)

    period_summaries: Dict[str, Dict[str, Any]] = {}
    totals_by_type: Counter[str] = Counter()
    min_year: Optional[int] = None
    max_year: Optional[int] = None

    for node in nodes:
        period_label, period_start, period_end = get_period_metadata(node.get("period"))
        period_key = node.get("period") or "Unspecified"

        if period_key not in period_summaries:
            period_summaries[period_key] = {
                "key": period_key,
                "label": period_label,
                "startYear": period_start,
                "endYear": period_end,
                "counts": defaultdict(int),
                "nodes": [],
            }

        period_entry = period_summaries[period_key]
        fallback_range = (period_entry["startYear"], period_entry["endYear"])
        start_year, end_year = infer_node_years(node, fallback_range)

        if start_year is not None:
            min_year = start_year if min_year is None else min(min_year, start_year)
        if end_year is not None:
            max_year = end_year if max_year is None else max(max_year, end_year)

        related_edges = node_edge_relations.get(node["id"], [])
        relation_counts = Counter(edge.get("relation") for edge in related_edges)
        top_relations = [relation for relation, _ in relation_counts.most_common(3)]

        period_entry["counts"][node.get("type", "unknown")] += 1
        totals_by_type[node.get("type", "unknown")] += 1

        period_entry["nodes"].append(
            {
                "id": node["id"],
                "label": node.get("label"),
                "type": node.get("type"),
                "period": node.get("period"),
                "school": node.get("school"),
                "startYear": start_year,
                "endYear": end_year,
                "description": node.get("description"),
                "significance": node.get("historical_importance") or node.get("position_on_free_will"),
                "relationCount": len(related_edges),
                "relatedTypes": top_relations,
            }
        )

    periods_sorted = sorted(
        period_summaries.values(),
        key=lambda item: (
            item["startYear"] if item["startYear"] is not None else math.inf,
            item["label"],
        ),
    )

    for period in periods_sorted:
        counts = dict(period["counts"])
        period["counts"] = counts
        period["nodes"].sort(
            key=lambda item: (
                item["startYear"] if item["startYear"] is not None else math.inf,
                item["label"],
            )
        )

    return {
        "periods": periods_sorted,
        "totals": {
            "nodes": len(nodes),
            "edges": len(edges),
            "byType": dict(totals_by_type),
        },
        "range": {
            "minYear": min_year,
            "maxYear": max_year,
        },
    }


def build_argument_evidence(
    kg_data: KGData,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct argument evidence flow data for Sankey visualization"""
    nodes, edges, node_lookup = apply_filters(kg_data, filters)
    arguments = [node for node in nodes if node.get("type") == "argument"]

    node_edge_relations: Dict[str, List[KGEdge]] = defaultdict(list)
    for edge in edges:
        node_edge_relations[edge.get("source")].append(edge)
        node_edge_relations[edge.get("target")].append(edge)

    evidence_nodes: Dict[str, Dict[str, Any]] = {}
    link_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    argument_summaries: List[Dict[str, Any]] = []

    total_ancient = 0
    total_modern = 0

    for argument in arguments:
        argument_id = argument["id"]
        argument_label = argument.get("label")
        argument_entry = {
            "id": argument_id,
            "label": argument_label,
            "period": argument.get("period"),
            "school": argument.get("school"),
            "description": argument.get("description"),
            "ancientCount": 0,
            "modernCount": 0,
            "totalConnections": 0,
        }

        evidence_nodes[argument_id] = {
            "id": argument_id,
            "label": argument_label,
            "group": "argument",
            "size": 1,
            "metadata": {"type": "argument"},
        }

        related_edges = node_edge_relations.get(argument_id, [])
        ancient_targets: List[Tuple[str, Optional[str]]] = []
        modern_targets: List[Tuple[str, Optional[str]]] = []

        for edge in related_edges:
            other_id = edge["target"] if edge["source"] == argument_id else edge["source"]
            other_node = node_lookup.get(other_id)
            if not other_node:
                continue

            classification = classify_evidence_node(other_node)
            if classification == "ancient":
                evidence_nodes.setdefault(
                    other_id,
                    {
                        "id": other_id,
                        "label": other_node.get("label"),
                        "group": "ancient_source",
                        "size": 1,
                        "metadata": {"type": other_node.get("type"), "source": "node"},
                    },
                )
                ancient_targets.append((other_id, edge.get("relation")))
            elif classification == "modern":
                evidence_nodes.setdefault(
                    other_id,
                    {
                        "id": other_id,
                        "label": other_node.get("label"),
                        "group": "modern_reception",
                        "size": 1,
                        "metadata": {"type": other_node.get("type"), "source": "node"},
                    },
                )
                modern_targets.append((other_id, edge.get("relation")))

        for citation in argument.get("ancient_sources", []) or []:
            synthetic_id = slugify(str(citation), "ancient")
            evidence_nodes.setdefault(
                synthetic_id,
                {
                    "id": synthetic_id,
                    "label": citation,
                    "group": "ancient_source",
                    "size": 1,
                    "metadata": {"type": "citation", "source": "citation"},
                },
            )
            ancient_targets.append((synthetic_id, "cites"))

        for citation in argument.get("modern_scholarship", []) or []:
            synthetic_id = slugify(str(citation), "modern")
            evidence_nodes.setdefault(
                synthetic_id,
                {
                    "id": synthetic_id,
                    "label": citation,
                    "group": "modern_reception",
                    "size": 1,
                    "metadata": {"type": "citation", "source": "citation"},
                },
            )
            modern_targets.append((synthetic_id, "discusses"))

        unique_ancient_ids = {item[0] for item in ancient_targets}
        unique_modern_ids = {item[0] for item in modern_targets}

        argument_entry["ancientCount"] = len(unique_ancient_ids)
        argument_entry["modernCount"] = len(unique_modern_ids)
        argument_entry["totalConnections"] = len(ancient_targets) + len(modern_targets)

        argument_summaries.append(argument_entry)
        total_ancient += len(unique_ancient_ids)
        total_modern += len(unique_modern_ids)

        for target_id, relation in ancient_targets:
            key = (argument_id, target_id)
            entry = link_map.setdefault(
                key,
                {"source": argument_id, "target": target_id, "value": 0, "argumentIds": set(), "relation": relation},
            )
            entry["value"] += 1
            entry["argumentIds"].add(argument_id)

        for target_id, relation in modern_targets:
            # connect argument directly to modern node if no ancient evidence
            if not unique_ancient_ids:
                key = (argument_id, target_id)
                entry = link_map.setdefault(
                    key,
                    {"source": argument_id, "target": target_id, "value": 0, "argumentIds": set(), "relation": relation},
                )
                entry["value"] += 1
                entry["argumentIds"].add(argument_id)

        for ancient_id in unique_ancient_ids:
            for modern_id in unique_modern_ids:
                key = (ancient_id, modern_id)
                entry = link_map.setdefault(
                    key,
                    {
                        "source": ancient_id,
                        "target": modern_id,
                        "value": 0,
                        "argumentIds": set(),
                        "relation": "interpreted_by",
                    },
                )
                entry["value"] += 1
                entry["argumentIds"].add(argument_id)

    links = []
    for (_, _), entry in link_map.items():
        link = dict(entry)
        link["argumentId"] = sorted(entry["argumentIds"])[0] if entry["argumentIds"] else None
        link["argumentIds"] = None  # remove set before serialization
        links.append({k: v for k, v in link.items() if v is not None})

    argument_summaries.sort(key=lambda item: item["totalConnections"], reverse=True)

    return {
        "nodes": list(evidence_nodes.values()),
        "links": links,
        "arguments": argument_summaries,
        "stats": {
            "totalArguments": len(arguments),
            "totalAncientSources": total_ancient,
            "totalModernReception": total_modern,
        },
    }


def choose_cluster_count(n: int) -> int:
    """Heuristic to select number of clusters based on concept count"""
    if n <= 6:
        return n
    if n <= 20:
        return 4
    if n <= 40:
        return 5
    if n <= 80:
        return 6
    return 8


def run_kmeans(vectors: np.ndarray, k: int, random_state: int = 42, iterations: int = 25) -> Tuple[np.ndarray, np.ndarray]:
    """Simple k-means clustering without external dependencies"""
    rng = np.random.default_rng(seed=random_state)
    n_samples = vectors.shape[0]
    if n_samples < k:
        k = n_samples

    if k == 0:
        return np.array([], dtype=int), np.empty((0, vectors.shape[1]))

    initial_indices = rng.choice(n_samples, size=k, replace=False)
    centroids = vectors[initial_indices]

    assignments = np.zeros(n_samples, dtype=int)
    for _ in range(iterations):
        distances = np.linalg.norm(vectors[:, None, :] - centroids[None, :, :], axis=2)
        new_assignments = distances.argmin(axis=1)
        if np.array_equal(assignments, new_assignments):
            break
        assignments = new_assignments

        for idx in range(k):
            cluster_points = vectors[assignments == idx]
            if len(cluster_points) > 0:
                centroids[idx] = cluster_points.mean(axis=0)

    return assignments, centroids


def project_vectors(vectors: np.ndarray) -> np.ndarray:
    """Project high-dimensional embeddings to 2D with PCA"""
    vectors = np.nan_to_num(vectors, nan=0.0, posinf=0.0, neginf=0.0)
    vectors = np.clip(vectors, -10.0, 10.0)
    if vectors.shape[1] <= 2:
        coords = vectors.copy()
    else:
        centered = vectors - vectors.mean(axis=0)
        try:
            cov = np.cov(centered, rowvar=False)
            eigvals, eigvecs = np.linalg.eigh(cov)
            idx = np.argsort(eigvals)[-2:]
            components = np.nan_to_num(eigvecs[:, idx], nan=0.0, posinf=0.0, neginf=0.0)
            with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
                coords = centered @ components
        except np.linalg.LinAlgError:
            coords = centered[:, :2]

    coords = np.nan_to_num(coords, nan=0.0, posinf=0.0, neginf=0.0)

    # Normalize to [-1, 1] range for consistency
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    ranges = np.where(maxs - mins == 0, 1, maxs - mins)
    normalized = ((coords - mins) / ranges) * 2 - 1
    return normalized


def build_concept_clusters(
    kg_data: KGData,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct concept cluster overview"""
    nodes, _, _ = apply_filters(kg_data, filters)
    concepts = [node for node in nodes if node.get("type") == "concept"]

    if not concepts:
        return {
            "clusters": [],
            "stats": {
                "totalConcepts": 0,
                "clusterCount": 0,
            },
        }

    embeddings = []
    valid_concepts = []
    for concept in concepts:
        embedding = concept.get("embedding")
        if embedding and isinstance(embedding, list):
            embeddings.append(embedding)
            valid_concepts.append(concept)

    if not embeddings:
        # Fallback: treat each concept as own cluster
        clusters = [
            {
                "id": concept["id"],
                "label": concept.get("label"),
                "size": 1,
                "keywords": extract_keywords(concept.get("description")),
                "nodes": [
                    {
                        "id": concept["id"],
                        "label": concept.get("label"),
                        "type": concept.get("type"),
                        "x": 0,
                        "y": 0,
                        "period": concept.get("period"),
                        "school": concept.get("school"),
                        "keywords": extract_keywords(concept.get("description")),
                    }
                ],
            }
            for concept in concepts
        ]
        return {
            "clusters": clusters,
            "stats": {
                "totalConcepts": len(concepts),
                "clusterCount": len(clusters),
            },
        }

    vectors = np.array(embeddings, dtype=float)
    vectors = np.nan_to_num(vectors, nan=0.0, posinf=0.0, neginf=0.0)
    vectors = np.clip(vectors, -10.0, 10.0)
    k = choose_cluster_count(len(valid_concepts))
    assignments, centroids = run_kmeans(vectors, k=k)
    coords = project_vectors(vectors)

    cluster_entries: Dict[int, Dict[str, Any]] = {}
    for idx, concept in enumerate(valid_concepts):
        cluster_id = int(assignments[idx])
        entry = cluster_entries.setdefault(
            cluster_id,
            {
                "id": f"cluster_{cluster_id}",
                "label": f"Cluster {cluster_id + 1}",
                "size": 0,
                "keywords": Counter(),
                "nodes": [],
                "metadata": {"centroid": centroids[cluster_id].tolist()},
            },
        )

        keywords = extract_keywords(
            concept.get("description") or concept.get("embedding_text") or concept.get("label")
        )

        entry["size"] += 1
        entry["keywords"].update(keywords)
        entry["nodes"].append(
            {
                "id": concept["id"],
                "label": concept.get("label"),
                "type": concept.get("type"),
                "x": float(coords[idx, 0]),
                "y": float(coords[idx, 1]),
                "period": concept.get("period"),
                "school": concept.get("school"),
                "keywords": keywords,
            }
        )

    clusters = []
    for entry in cluster_entries.values():
        top_keywords = [word for word, _ in entry["keywords"].most_common(4)]
        entry["keywords"] = top_keywords
        if top_keywords:
            entry["label"] = f"{', '.join(top_keywords[:2])}".title()
        entry["nodes"].sort(key=lambda node: node["label"])
        clusters.append(entry)

    clusters.sort(key=lambda item: item["size"], reverse=True)

    return {
        "clusters": clusters,
        "stats": {
            "totalConcepts": len(concepts),
            "clusterCount": len(clusters),
        },
    }


def build_influence_matrix(
    kg_data: KGData,
    filters: Optional[Dict[str, Any]] = None,
    max_schools: int = 12,
    max_relations: int = 12,
) -> Dict[str, Any]:
    """Construct influence matrix aggregating schools vs relation types"""
    nodes, edges, node_lookup = apply_filters(kg_data, filters)

    school_counts = Counter(node.get("school") for node in nodes if node.get("school"))
    top_schools = [school for school, _ in school_counts.most_common(max_schools)]

    relation_counts = Counter(edge.get("relation") for edge in edges if edge.get("relation"))
    top_relations = [relation for relation, _ in relation_counts.most_common(max_relations)]

    if not top_schools or not top_relations:
        return {
            "rows": [],
            "columns": [],
            "cells": [],
            "totals": {
                "relationsConsidered": 0,
                "schoolsCovered": 0,
                "edgesMapped": 0,
            },
        }

    cell_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    edges_mapped = 0

    for edge in edges:
        relation = edge.get("relation")
        if relation not in top_relations:
            continue

        source = node_lookup.get(edge.get("source"))
        target = node_lookup.get(edge.get("target"))

        school = (source or {}).get("school") or (target or {}).get("school")
        if not school or school not in top_schools:
            continue

        key = (school, relation)
        entry = cell_map.setdefault(
            key,
            {"rowKey": school, "columnKey": relation, "count": 0, "sampleEdges": []},
        )
        entry["count"] += 1
        edges_mapped += 1

        if len(entry["sampleEdges"]) < 5:
            entry["sampleEdges"].append(edge.get("id") or f"{edge.get('source')}->{edge.get('target')}")

    rows = [
        {"key": school, "label": school, "type": "school", "order": idx}
        for idx, school in enumerate(top_schools)
    ]
    columns = [
        {"key": relation, "label": relation.replace("_", " ").title(), "type": "relation", "order": idx}
        for idx, relation in enumerate(top_relations)
    ]
    cells = list(cell_map.values())

    return {
        "rows": rows,
        "columns": columns,
        "cells": cells,
        "totals": {
            "relationsConsidered": len(columns),
            "schoolsCovered": len(rows),
            "edgesMapped": edges_mapped,
        },
    }


def compute_shortest_path(
    kg_data: KGData,
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute a shortest path between two nodes"""
    source_id = request.get("sourceId")
    target_id = request.get("targetId")
    if not source_id or not target_id:
        raise ValueError("sourceId and targetId are required")

    max_depth = int(request.get("maxDepth") or 6)
    allow_bidirectional = bool(request.get("allowBidirectional", True))
    whitelist = set(request.get("relationWhitelist") or [])
    blacklist = set(request.get("relationBlacklist") or [])

    nodes_by_id = {node["id"]: node for node in kg_data.get("nodes", [])}
    edges = kg_data.get("edges", [])

    if source_id not in nodes_by_id or target_id not in nodes_by_id:
        raise ValueError("Source or target node not found in knowledge graph")

    adjacency: Dict[str, List[Tuple[str, KGEdge]]] = defaultdict(list)
    for edge in edges:
        relation = edge.get("relation", "related_to")
        if whitelist and relation not in whitelist:
            continue
        if blacklist and relation in blacklist:
            continue

        adjacency[edge.get("source")].append((edge.get("target"), edge))
        if allow_bidirectional:
            adjacency[edge.get("target")].append((edge.get("source"), edge))

    queue = deque([(source_id, [])])
    visited = {source_id: 0}
    best_path: Optional[List[Tuple[str, str, KGEdge]]] = None

    while queue:
        current, path_edges = queue.popleft()

        if current == target_id:
            best_path = path_edges
            break

        if len(path_edges) >= max_depth:
            continue

        for neighbor, edge in adjacency.get(current, []):
            depth = len(path_edges) + 1
            if neighbor not in visited or visited[neighbor] > depth:
                visited[neighbor] = depth
                queue.append((neighbor, path_edges + [(current, neighbor, edge)]))

    if best_path is None:
        return {
            "nodes": [
                {
                    "id": nodes_by_id[source_id]["id"],
                    "label": nodes_by_id[source_id].get("label"),
                    "type": nodes_by_id[source_id].get("type"),
                    "period": nodes_by_id[source_id].get("period"),
                    "school": nodes_by_id[source_id].get("school"),
                    "description": nodes_by_id[source_id].get("description"),
                }
            ],
            "edges": [],
            "length": 0,
            "warnings": ["No path found within the depth limit"],
        }

    def make_node_payload(node: KGNode) -> Dict[str, Any]:
        return {
            "id": node["id"],
            "label": node.get("label"),
            "type": node.get("type"),
            "period": node.get("period"),
            "school": node.get("school"),
            "description": node.get("description"),
        }

    path_nodes: List[Dict[str, Any]] = []
    path_edges: List[Dict[str, Any]] = []

    encountered: Set[str] = set()
    for src, tgt, edge in best_path:
        if src not in encountered:
            path_nodes.append(make_node_payload(nodes_by_id[src]))
            encountered.add(src)
        if tgt not in encountered:
            path_nodes.append(make_node_payload(nodes_by_id[tgt]))
            encountered.add(tgt)

        path_edges.append(
            {
                "source": src,
                "target": tgt,
                "relation": edge.get("relation"),
                "description": edge.get("description"),
            }
            )

    if target_id not in encountered:
        path_nodes.append(make_node_payload(nodes_by_id[target_id]))

    summary = f"Shortest path between {nodes_by_id[source_id].get('label')} and {nodes_by_id[target_id].get('label')} spans {len(best_path)} steps."

    return {
        "nodes": path_nodes,
        "edges": path_edges,
        "length": len(best_path),
        "summary": summary,
    }
