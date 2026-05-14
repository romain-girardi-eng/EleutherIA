"""Tests for WeightedTraversal service."""

from eleutheria_graphrag.services.weighted_traversal import (
    EDGE_CATEGORY_MULTIPLIERS,
    RELATION_TO_CATEGORY,
    WeightedTraversal,
)


def _make_graph():
    """Build a small test graph.

    Graph::

        A --argues_for--> B --influences--> C
        A --related_to--> D --interprets--> E
        D --argues_against--> F
    """
    nodes = {
        "A": {"id": "A", "type": "Person", "label": "A"},
        "B": {"id": "B", "type": "Concept", "label": "B"},
        "C": {"id": "C", "type": "Person", "label": "C"},
        "D": {"id": "D", "type": "Concept", "label": "D"},
        "E": {"id": "E", "type": "Modern_Interpretation", "label": "E"},
        "F": {"id": "F", "type": "Argument", "label": "F"},
    }
    outgoing = {
        "A": [
            {"source": "A", "target": "B", "relation": "argues_for", "weight": 1.0},
            {"source": "A", "target": "D", "relation": "related_to", "weight": 0.5},
        ],
        "B": [
            {"source": "B", "target": "C", "relation": "influences", "weight": 1.0},
        ],
        "D": [
            {"source": "D", "target": "E", "relation": "interprets", "weight": 1.0},
            {
                "source": "D",
                "target": "F",
                "relation": "argues_against",
                "weight": 0.8,
            },
        ],
    }
    incoming = {
        "B": [outgoing["A"][0]],
        "C": [outgoing["B"][0]],
        "D": [outgoing["A"][1]],
        "E": [outgoing["D"][0]],
        "F": [outgoing["D"][1]],
    }
    return nodes, outgoing, incoming


class TestWeightedTraversal:
    """Tests for WeightedTraversal graph expansion."""

    def test_expand_from_single_seed(self):
        nodes, out, inc = _make_graph()
        wt = WeightedTraversal(nodes, out, inc)
        visited = wt.expand(seed_ids=["A"], max_nodes=10)
        # Should visit A and its neighbours
        assert "A" in visited
        assert "B" in visited

    def test_expand_max_nodes(self):
        nodes, out, inc = _make_graph()
        wt = WeightedTraversal(nodes, out, inc)
        visited = wt.expand(seed_ids=["A"], max_nodes=3)
        assert len(visited) <= 3

    def test_expand_empty_seeds(self):
        nodes, out, inc = _make_graph()
        wt = WeightedTraversal(nodes, out, inc)
        visited = wt.expand(seed_ids=[])
        assert visited == set()

    def test_expand_unknown_seed(self):
        nodes, out, inc = _make_graph()
        wt = WeightedTraversal(nodes, out, inc)
        visited = wt.expand(seed_ids=["UNKNOWN"])
        assert visited == set()

    def test_edge_filter(self):
        nodes, out, inc = _make_graph()
        wt = WeightedTraversal(nodes, out, inc)
        # Only follow argumentative edges
        visited = wt.expand(
            seed_ids=["A"],
            edge_filter={"argues_for", "argues_against"},
        )
        assert "B" in visited  # argues_for from A
        assert "D" not in visited  # related_to is filtered out

    def test_score_threshold(self):
        nodes, out, inc = _make_graph()
        wt = WeightedTraversal(nodes, out, inc)
        # Very high threshold → only seeds
        visited = wt.expand(seed_ids=["A"], score_threshold=0.99)
        # Seeds are scored 1.0, their neighbours < 1.0
        assert "A" in visited

    def test_pagerank_influence(self):
        nodes, out, inc = _make_graph()
        pagerank = {"A": 0.1, "B": 0.9, "C": 0.1, "D": 0.1, "E": 0.1, "F": 0.1}
        wt = WeightedTraversal(nodes, out, inc, pagerank_scores=pagerank)
        # B has high PageRank → should be prioritised
        visited = wt.expand(seed_ids=["A"], max_nodes=3)
        assert "B" in visited

    def test_bidirectional_traversal(self):
        nodes, out, inc = _make_graph()
        wt = WeightedTraversal(nodes, out, inc)
        # Starting from B, should be able to go back to A via incoming edges
        visited = wt.expand(seed_ids=["B"], max_nodes=10)
        assert "A" in visited  # via incoming edge
        assert "C" in visited  # via outgoing edge

    def test_score_edge_formula(self):
        nodes, out, inc = _make_graph()
        pagerank = {"B": 0.5}
        wt = WeightedTraversal(nodes, out, inc, pagerank_scores=pagerank)
        edge = {"source": "A", "target": "B", "relation": "argues_for", "weight": 1.0}
        score = wt._score_edge(edge, "B", parent_score=1.0)
        # Expected: 1.0 * 1.0 * 1.5 * (0.5 + 1.0) * 0.7
        # (pagerank B = 0.5/0.5 = 1.0 normalized)
        expected = 1.0 * 1.0 * 1.5 * (0.5 + 1.0) * 0.7
        assert abs(score - expected) < 0.001

    def test_no_pagerank(self):
        nodes, out, inc = _make_graph()
        wt = WeightedTraversal(nodes, out, inc)
        # Without PageRank, centrality is 0.0, base is 0.5
        edge = {"source": "A", "target": "B", "relation": "argues_for", "weight": 1.0}
        score = wt._score_edge(edge, "B", parent_score=1.0)
        expected = 1.0 * 1.0 * 1.5 * 0.5 * 0.7
        assert abs(score - expected) < 0.001


class TestEdgeMappings:
    """Tests for edge category configuration."""

    def test_all_relations_mapped(self):
        for relation, category in RELATION_TO_CATEGORY.items():
            assert category in EDGE_CATEGORY_MULTIPLIERS, (
                f"Relation {relation} maps to unknown category {category}"
            )

    def test_argumentative_highest(self):
        assert EDGE_CATEGORY_MULTIPLIERS["argumentative"] >= max(
            v for k, v in EDGE_CATEGORY_MULTIPLIERS.items() if k != "argumentative"
        )

    def test_temporal_lowest(self):
        assert EDGE_CATEGORY_MULTIPLIERS["temporal"] <= min(
            v for k, v in EDGE_CATEGORY_MULTIPLIERS.items() if k != "temporal"
        )
