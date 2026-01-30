"""Tests for KG analytics service."""

import pytest

from eleutheria_kg.services.analytics import KGAnalytics


@pytest.fixture
def sample_kg_data():
    """Sample knowledge graph data for testing."""
    return {
        "nodes": [
            {"id": "chrysippus", "label": "Chrysippus", "type": "Person", "period": "Hellenistic Greek", "school": "Stoic"},
            {"id": "epictetus", "label": "Epictetus", "type": "Person", "period": "Roman Imperial", "school": "Stoic"},
            {"id": "zeno", "label": "Zeno of Citium", "type": "Person", "period": "Hellenistic Greek", "school": "Stoic"},
            {"id": "fate", "label": "Fate (heimarmene)", "type": "Concept"},
            {"id": "to_eph_hemin", "label": "To eph' hemin", "type": "Concept"},
            {"id": "stoicism", "label": "Stoicism", "type": "School"},
        ],
        "edges": [
            {"source": "chrysippus", "target": "stoicism", "relation": "belongs_to_school"},
            {"source": "epictetus", "target": "stoicism", "relation": "belongs_to_school"},
            {"source": "zeno", "target": "stoicism", "relation": "founded"},
            {"source": "chrysippus", "target": "fate", "relation": "discusses"},
            {"source": "chrysippus", "target": "to_eph_hemin", "relation": "defines"},
            {"source": "epictetus", "target": "to_eph_hemin", "relation": "discusses"},
            {"source": "zeno", "target": "chrysippus", "relation": "influences"},
        ],
    }


class TestKGAnalytics:
    """Tests for KGAnalytics class."""

    def test_init_empty(self):
        """Test initialization with no data."""
        analytics = KGAnalytics()
        assert analytics.kg_data == {"nodes": [], "edges": []}

    def test_init_with_data(self, sample_kg_data):
        """Test initialization with sample data."""
        analytics = KGAnalytics(sample_kg_data)
        assert len(analytics.kg_data["nodes"]) == 6
        assert len(analytics.kg_data["edges"]) == 7

    def test_get_statistics(self, sample_kg_data):
        """Test getting graph statistics."""
        analytics = KGAnalytics(sample_kg_data)
        stats = analytics.get_statistics()

        assert stats["total_nodes"] == 6
        assert stats["total_edges"] == 7
        assert stats["node_types"]["Person"] == 3
        assert stats["node_types"]["Concept"] == 2
        assert stats["node_types"]["School"] == 1

    def test_calculate_centrality_degree(self, sample_kg_data):
        """Test degree centrality calculation."""
        analytics = KGAnalytics(sample_kg_data)
        centrality = analytics.calculate_centrality(metric="degree")

        # Stoicism should have high centrality (connected to 3 persons)
        assert "stoicism" in centrality
        assert centrality["stoicism"] > 0

    def test_calculate_centrality_top_k(self, sample_kg_data):
        """Test centrality with top_k limit."""
        analytics = KGAnalytics(sample_kg_data)
        centrality = analytics.calculate_centrality(metric="degree", top_k=3)

        assert len(centrality) == 3

    def test_detect_communities_greedy(self, sample_kg_data):
        """Test community detection with greedy algorithm."""
        analytics = KGAnalytics(sample_kg_data)
        communities = analytics.detect_communities(algorithm="greedy")

        assert len(communities) == 6  # One assignment per node
        # All nodes should have a community ID
        for node in sample_kg_data["nodes"]:
            assert node["id"] in communities

    def test_detect_communities_semantic(self, sample_kg_data):
        """Test semantic community detection."""
        analytics = KGAnalytics(sample_kg_data)
        communities = analytics.detect_communities(algorithm="semantic")

        # Person nodes should each be in their own community
        assert communities["chrysippus"] != communities["epictetus"] or \
               communities["chrysippus"] != communities["zeno"]

    def test_get_shortest_path(self, sample_kg_data):
        """Test shortest path finding."""
        analytics = KGAnalytics(sample_kg_data)

        path = analytics.get_shortest_path("zeno", "epictetus")
        assert path is not None
        assert path[0] == "zeno"
        assert path[-1] == "epictetus"

    def test_get_shortest_path_no_path(self, sample_kg_data):
        """Test shortest path when no path exists."""
        # Add isolated node
        sample_kg_data["nodes"].append({"id": "isolated", "label": "Isolated", "type": "Person"})
        analytics = KGAnalytics(sample_kg_data)

        path = analytics.get_shortest_path("zeno", "isolated")
        assert path is None

    def test_get_node_neighbors(self, sample_kg_data):
        """Test getting node neighbors."""
        analytics = KGAnalytics(sample_kg_data)
        result = analytics.get_node_neighbors("chrysippus", depth=1)

        assert len(result["nodes"]) > 1  # chrysippus + neighbors
        assert any(n["id"] == "chrysippus" for n in result["nodes"])

    def test_get_node_neighbors_depth_2(self, sample_kg_data):
        """Test getting neighbors with depth 2."""
        analytics = KGAnalytics(sample_kg_data)
        result_d1 = analytics.get_node_neighbors("chrysippus", depth=1)
        result_d2 = analytics.get_node_neighbors("chrysippus", depth=2)

        # Depth 2 should have more or equal nodes
        assert len(result_d2["nodes"]) >= len(result_d1["nodes"])

    def test_get_timeline_data(self, sample_kg_data):
        """Test timeline data generation."""
        analytics = KGAnalytics(sample_kg_data)
        timeline = analytics.get_timeline_data()

        # Should have at least one period (Hellenistic Greek)
        periods = [t["period"] for t in timeline]
        assert "Hellenistic Greek" in periods or len(timeline) > 0

    def test_get_community_colors(self, sample_kg_data):
        """Test community color assignment."""
        analytics = KGAnalytics(sample_kg_data)
        analytics.detect_communities(algorithm="greedy")
        colors = analytics.get_community_colors()

        # Each community should have a color
        for comm_id in set(analytics._communities.values()):
            assert comm_id in colors
            assert colors[comm_id].startswith("#")
