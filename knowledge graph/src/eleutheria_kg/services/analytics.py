"""
Knowledge Graph Analytics - Community detection, centrality, and graph metrics.

Provides high-level analytics for the EleutherIA knowledge graph including:
- Community detection (Leiden, Louvain, greedy modularity)
- Centrality metrics (betweenness, PageRank, degree)
- Graph statistics and visualization helpers
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
from collections import Counter, defaultdict
from collections.abc import Mapping
from typing import Any, cast

import networkx as nx

logger = logging.getLogger(__name__)

# Type aliases
KGNode = dict[str, Any]
KGEdge = dict[str, Any]
KGData = dict[str, Any]

# Period metadata for timeline visualization
PERIOD_METADATA: dict[str, dict[str, str | int | None]] = {
    "Presocratic": {"label": "Presocratic", "start": -600, "end": -450},
    "Classical Greek": {"label": "Classical Greek", "start": -450, "end": -323},
    "Hellenistic": {"label": "Hellenistic", "start": -323, "end": -31},
    "Roman Republican": {"label": "Roman Republican", "start": -146, "end": -27},
    "Roman Imperial": {"label": "Roman Imperial", "start": -27, "end": 300},
    "Patristic": {"label": "Patristic", "start": 150, "end": 450},
    "Late Antiquity": {"label": "Late Antiquity", "start": 300, "end": 600},
    "Second Temple Judaism": {
        "label": "Second Temple Judaism",
        "start": -515,
        "end": 70,
    },
    "Rabbinic": {"label": "Rabbinic", "start": 70, "end": 600},
    "Medieval": {"label": "Medieval", "start": 500, "end": 1500},
    "Early Modern": {"label": "Early Modern", "start": 1500, "end": 1800},
    "Modern": {"label": "Modern", "start": 1800, "end": 1950},
    "Contemporary": {"label": "Contemporary", "start": 1950, "end": None},
}

ANCIENT_PERIODS: set[str] = {
    "Presocratic",
    "Classical Greek",
    "Hellenistic",
    "Roman Republican",
    "Roman Imperial",
    "Patristic",
    "Late Antiquity",
    "Second Temple Judaism",
    "Rabbinic",
}

MODERN_PERIODS: set[str] = {
    "Medieval",
    "Early Modern",
    "Modern",
    "Contemporary",
}

# Community detection color palette
COMMUNITY_COLORS: list[str] = [
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
]


def _algorithm_available(name: str) -> bool:
    """Check whether dependencies for a community detection algorithm are available."""
    if name == "leiden":
        return bool(
            importlib.util.find_spec("igraph") and importlib.util.find_spec("leidenalg")
        )
    if name == "louvain":
        return bool(importlib.util.find_spec("community"))
    return name in ("greedy", "semantic")


def _normalized_node_type(node: KGNode) -> str:
    return str(node.get("type", "")).strip().lower()


def _canonical_release_row(row: Any) -> bytes:
    """Serialize one served row deterministically for the release digest."""
    payload = dict(row) if isinstance(row, Mapping) else row
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def is_derived_edge(edge: Mapping[str, Any]) -> bool:
    """Return whether an edge is a materialized inference rather than an assertion.

    Snapshot normalization writes the marker at the top level, while older
    exports sometimes only carried it in ``metadata``.  Treat the small set of
    string spellings emitted by historical JSON/SQL exporters as true too so a
    workspace view can never accidentally publish an inverse twin as asserted.
    """

    def _truthy(value: Any) -> bool:
        return value is True or (
            isinstance(value, str) and value.strip().lower() in {"1", "true", "yes"}
        )

    if _truthy(edge.get("derived")):
        return True
    metadata = edge.get("metadata")
    return isinstance(metadata, Mapping) and _truthy(metadata.get("derived"))


def _release_metadata(kg_data: KGData) -> dict[str, str | int]:
    """Return immutable identity/counts for one in-memory KG snapshot.

    List order is deliberately part of the digest because it defines API
    pagination. Two replicas serving byte-equivalent ordered rows therefore
    share a release ID, while any content or ordering change creates a new one.
    """
    nodes = kg_data.get("nodes", [])
    edges = kg_data.get("edges", [])
    digest = hashlib.sha256()

    for resource, rows in (("nodes", nodes), ("edges", edges)):
        digest.update(resource.encode("ascii"))
        digest.update(b"\0")
        for row in rows:
            encoded = _canonical_release_row(row)
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)

    asserted_edges = sum(1 for edge in edges if not is_derived_edge(edge))
    return {
        "release_id": f"kg-sha256-{digest.hexdigest()}",
        "served_total_nodes": len(nodes),
        "served_total_edges": len(edges),
        "served_total_asserted_edges": asserted_edges,
    }


class KGAnalytics:
    """
    Knowledge graph analytics service.

    Provides community detection, centrality metrics, and graph statistics.
    """

    def __init__(self, kg_data: KGData | None = None) -> None:
        """
        Initialize analytics with knowledge graph data.

        Args:
            kg_data: Dictionary with 'nodes' and 'edges' lists
        """
        self.kg_data = kg_data or {"nodes": [], "edges": []}
        self._graph: nx.Graph | None = None
        self._digraph: nx.DiGraph | None = None
        self._communities: dict[str, int] | None = None
        self._community_memo: dict[tuple[str, float], dict[str, int]] = {}
        self._release = _release_metadata(self.kg_data)

    def set_data(self, kg_data: KGData) -> None:
        """Atomically publish a new immutable knowledge-graph release.

        This method is synchronous: under the asyncio server, the data swap,
        release digest and served totals become visible as one event-loop turn.
        Callers must replace the snapshot through ``set_data`` rather than
        mutating ``kg_data`` in place.
        """
        # Compute before publishing: if canonicalization fails, the previous
        # data+contract pair remains intact rather than becoming half-swapped.
        release = _release_metadata(kg_data)
        self.kg_data = kg_data
        self._release = release
        self._graph = None
        self._digraph = None
        self._communities = None
        self._community_memo.clear()

    def get_release_metadata(self) -> dict[str, str | int]:
        """Return a copy of the immutable contract for the served snapshot."""
        return dict(self._release)

    def _build_graph(self) -> nx.Graph:
        """Build an UNDIRECTED NetworkX graph from KG data.

        Used for community detection and any metric where directionality
        of a relation (e.g. authored_by, refutes, taught_by) shouldn't
        matter for the computation (connectivity, modularity, shortest
        path, neighbor traversal).
        """
        if self._graph is not None:
            return self._graph

        graph = nx.Graph()

        # Add nodes
        for node in self.kg_data.get("nodes", []):
            node_id = node.get("id")
            if node_id:
                graph.add_node(node_id, **node)

        # Add edges
        for edge in self.kg_data.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            if source and target and graph.has_node(source) and graph.has_node(target):
                graph.add_edge(source, target, **edge)

        self._graph = graph
        return graph

    def _build_digraph(self) -> nx.DiGraph:
        """Build a DIRECTED NetworkX graph (source -> target) from KG data.

        Used for authority-style centrality (PageRank, eigenvector) so that
        a node cited/refuted/taught-by many others outranks a node that
        merely has a high undirected degree. On an undirected graph
        PageRank collapses to a function of degree; the directed edge
        orientation is what encodes "authority".
        """
        if self._digraph is not None:
            return self._digraph

        digraph = nx.DiGraph()

        for node in self.kg_data.get("nodes", []):
            node_id = node.get("id")
            if node_id:
                digraph.add_node(node_id, **node)

        for edge in self.kg_data.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            if (
                source
                and target
                and digraph.has_node(source)
                and digraph.has_node(target)
            ):
                digraph.add_edge(source, target, **edge)

        self._digraph = digraph
        return digraph

    def get_statistics(self) -> dict[str, Any]:
        """
        Get basic graph statistics.

        Returns:
            Dictionary with node count, edge count, density, etc.
        """
        graph = self._build_graph()

        # Node type distribution
        node_types = Counter(
            node.get("type", "unknown") for node in self.kg_data.get("nodes", [])
        )

        # Edge type distribution
        edge_types = Counter(
            edge.get("relation", "unknown") for edge in self.kg_data.get("edges", [])
        )

        release = self.get_release_metadata()
        return {
            # These aliases intentionally describe the rows served by the list
            # endpoints, not a live database that may be ahead of this process.
            "total_nodes": release["served_total_nodes"],
            "total_edges": release["served_total_edges"],
            **release,
            "density": nx.density(graph) if graph.number_of_nodes() > 0 else 0,
            "connected_components": nx.number_connected_components(graph),
            "node_types": dict(node_types),
            "edge_types": dict(edge_types),
            "avg_degree": (
                sum(dict(graph.degree()).values()) / graph.number_of_nodes()
                if graph.number_of_nodes() > 0
                else 0
            ),
        }

    def detect_communities(
        self,
        algorithm: str = "leiden",
        resolution: float = 1.0,
    ) -> dict[str, int]:
        """
        Detect communities in the knowledge graph.

        Args:
            algorithm: One of 'leiden', 'louvain', 'greedy', or 'semantic'
            resolution: Resolution parameter for modularity (higher = more communities)

        Returns:
            Dictionary mapping node IDs to community IDs
        """
        if not _algorithm_available(algorithm):
            logger.warning(
                f"Algorithm {algorithm} not available, falling back to greedy"
            )
            algorithm = "greedy"

        memo_key = (algorithm, resolution)
        memoized = self._community_memo.get(memo_key)
        if memoized is not None:
            self._communities = memoized
            return memoized

        graph = self._build_graph()

        if algorithm == "leiden":
            communities = self._leiden_communities(graph, resolution)
        elif algorithm == "louvain":
            communities = self._louvain_communities(graph, resolution)
        elif algorithm == "semantic":
            communities = self._semantic_communities()
        else:
            communities = self._greedy_communities(graph)

        self._community_memo[memo_key] = communities
        self._communities = communities
        return communities

    def _leiden_communities(self, graph: nx.Graph, resolution: float) -> dict[str, int]:
        """Detect communities using Leiden algorithm."""
        import igraph as ig
        import leidenalg

        # Convert to igraph
        ig_graph = ig.Graph.from_networkx(graph)

        # Run Leiden
        partition = leidenalg.find_partition(
            ig_graph,
            leidenalg.RBConfigurationVertexPartition,
            resolution_parameter=resolution,
        )

        # Map back to node IDs
        node_list = list(graph.nodes())
        return {node_list[i]: partition.membership[i] for i in range(len(node_list))}

    def _louvain_communities(
        self, graph: nx.Graph, resolution: float
    ) -> dict[str, int]:
        """Detect communities using Louvain algorithm."""
        import community as community_louvain

        result: dict[str, int] = community_louvain.best_partition(
            graph, resolution=resolution
        )
        return result

    def _greedy_communities(self, graph: nx.Graph) -> dict[str, int]:
        """Detect communities using greedy modularity optimization."""
        communities = nx.community.greedy_modularity_communities(graph)

        result = {}
        for i, comm in enumerate(communities):
            for node in comm:
                result[node] = i

        return result

    def _semantic_communities(self) -> dict[str, int]:
        """
        Assign communities based on semantic relationships.

        Groups nodes by their connection to Person nodes (authors/philosophers).
        """
        # Build person-centric clusters
        person_nodes = {
            node["id"]
            for node in self.kg_data.get("nodes", [])
            if _normalized_node_type(node) == "person"
        }

        communities: dict[str, int] = {}
        community_id = 0

        # Assign each person their own community
        for person_id in person_nodes:
            communities[person_id] = community_id
            community_id += 1

        # Assign other nodes to the community of their closest person
        edges_by_node: dict[str, list[str]] = defaultdict(list)
        for edge in self.kg_data.get("edges", []):
            edges_by_node[edge["source"]].append(edge["target"])
            edges_by_node[edge["target"]].append(edge["source"])

        for node in self.kg_data.get("nodes", []):
            node_id = node["id"]
            if node_id in communities:
                continue

            # Find connected persons
            connected_persons = [n for n in edges_by_node[node_id] if n in person_nodes]

            if connected_persons:
                # Assign to first connected person's community
                communities[node_id] = communities[connected_persons[0]]
            else:
                # Orphan node gets its own community
                communities[node_id] = community_id
                community_id += 1

        return communities

    def calculate_centrality(
        self,
        metric: str = "betweenness",
        top_k: int | None = None,
    ) -> dict[str, float]:
        """
        Calculate centrality scores for nodes.

        Args:
            metric: One of 'betweenness', 'pagerank', 'degree', 'eigenvector'
            top_k: If set, return only top K nodes

        Returns:
            Dictionary mapping node IDs to centrality scores
        """
        graph = self._build_graph()

        if metric == "betweenness":
            scores = nx.betweenness_centrality(graph)
        elif metric == "pagerank":
            # Directed graph: a node cited/refuted/taught-by many others
            # accrues authority even with modest undirected degree. On the
            # undirected graph PageRank degenerates to ~degree.
            digraph = self._build_digraph()
            scores = nx.pagerank(digraph)
        elif metric == "eigenvector":
            digraph = self._build_digraph()
            try:
                scores = nx.eigenvector_centrality(digraph, max_iter=1000)
            except nx.PowerIterationFailedConvergence:
                logger.warning("Eigenvector centrality failed, using degree")
                scores = dict(graph.degree())
        else:  # degree
            scores = {
                node: deg / (graph.number_of_nodes() - 1)
                for node, deg in graph.degree()
            }

        if top_k:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return cast(dict[str, float], dict(sorted_scores[:top_k]))

        return cast(dict[str, float], scores)

    def get_shortest_path(
        self,
        source: str,
        target: str,
    ) -> list[str] | None:
        """
        Find shortest path between two nodes.

        Args:
            source: Source node ID
            target: Target node ID

        Returns:
            List of node IDs in the path, or None if no path exists
        """
        graph = self._build_graph()

        try:
            path: list[str] = nx.shortest_path(graph, source, target)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):  # fmt: skip
            return None

    def get_node_neighbors(
        self,
        node_id: str,
        depth: int = 1,
    ) -> dict[str, Any]:
        """
        Get neighbors of a node up to a certain depth.

        Args:
            node_id: Node ID to start from
            depth: Maximum traversal depth

        Returns:
            Dictionary with 'nodes' and 'edges' in the neighborhood
        """
        graph = self._build_graph()

        if node_id not in graph:
            return {"nodes": [], "edges": []}

        # BFS to find nodes within depth
        visited = {node_id}
        current_level = {node_id}

        for _ in range(depth):
            next_level = set()
            for node in current_level:
                for neighbor in graph.neighbors(node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.add(neighbor)
            current_level = next_level

        # Extract subgraph
        graph.subgraph(visited)

        # Convert back to node/edge format
        nodes = [
            next(
                (n for n in self.kg_data["nodes"] if n["id"] == node_id),
                {"id": node_id},
            )
            for node_id in visited
        ]

        edges = [
            edge
            for edge in self.kg_data.get("edges", [])
            if edge["source"] in visited and edge["target"] in visited
        ]

        return {"nodes": nodes, "edges": edges}

    def get_timeline_data(self) -> list[dict[str, Any]]:
        """
        Get timeline data for visualization.

        Returns:
            List of periods with their nodes grouped by time.
        """
        timeline = []

        for period_name, metadata in PERIOD_METADATA.items():
            period_nodes = [
                node
                for node in self.kg_data.get("nodes", [])
                if node.get("period") == period_name
            ]

            if period_nodes:
                timeline.append(
                    {
                        "period": period_name,
                        "label": metadata["label"],
                        "start_year": metadata["start"],
                        "end_year": metadata["end"],
                        "node_count": len(period_nodes),
                        "nodes": period_nodes,
                    }
                )

        return sorted(timeline, key=lambda x: x["start_year"] or 0)

    def get_community_colors(self) -> dict[int, str]:
        """
        Get color assignments for communities.

        Returns:
            Dictionary mapping community IDs to hex colors
        """
        if not self._communities:
            return {}

        unique_communities = set(self._communities.values())
        return {
            comm_id: COMMUNITY_COLORS[i % len(COMMUNITY_COLORS)]
            for i, comm_id in enumerate(sorted(unique_communities))
        }
