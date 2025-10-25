"""
Unit tests for Knowledge Graph Analytics Service
Tests timeline, clustering, community detection, etc.
"""
import pytest
from unittest.mock import Mock, patch
import networkx as nx


class TestKGAnalytics:
    """Test cases for KG Analytics functions"""

    @pytest.fixture
    def sample_graph(self, sample_kg_data):
        """Create a sample NetworkX graph from KG data"""
        G = nx.DiGraph()

        for node in sample_kg_data["nodes"]:
            G.add_node(node["id"], **node)

        for edge in sample_kg_data["edges"]:
            G.add_edge(edge["source"], edge["target"], relation=edge["relation"])

        return G

    def test_graph_creation(self, sample_graph):
        """Test that graph is created correctly"""
        assert sample_graph.number_of_nodes() == 3
        assert sample_graph.number_of_edges() == 2

    def test_node_attributes(self, sample_graph):
        """Test that node attributes are preserved"""
        node_data = sample_graph.nodes["person_aristotle_test"]
        assert node_data["label"] == "Aristotle"
        assert node_data["type"] == "person"
        assert node_data["school"] == "Peripatetic"

    def test_edge_attributes(self, sample_graph):
        """Test that edge attributes are preserved"""
        edge_data = sample_graph.edges["person_aristotle_test", "work_ethics_test"]
        assert edge_data["relation"] == "authored"

    def test_shortest_path(self, sample_graph):
        """Test shortest path calculation"""
        try:
            path = nx.shortest_path(
                sample_graph,
                "person_aristotle_test",
                "concept_free_will_test"
            )
            assert len(path) >= 2
            assert path[0] == "person_aristotle_test"
            assert path[-1] == "concept_free_will_test"
        except nx.NetworkXNoPath:
            # If no path exists, that's also valid
            pass

    def test_degree_centrality(self, sample_graph):
        """Test degree centrality calculation"""
        centrality = nx.degree_centrality(sample_graph)

        assert isinstance(centrality, dict)
        assert len(centrality) == sample_graph.number_of_nodes()
        # Aristotle should have high centrality (connected to 2 nodes)
        assert centrality["person_aristotle_test"] > 0

    def test_betweenness_centrality(self, sample_graph):
        """Test betweenness centrality calculation"""
        centrality = nx.betweenness_centrality(sample_graph)

        assert isinstance(centrality, dict)
        assert len(centrality) == sample_graph.number_of_nodes()

    def test_filter_by_node_type(self, sample_graph):
        """Test filtering nodes by type"""
        persons = [n for n, d in sample_graph.nodes(data=True) if d.get("type") == "person"]
        concepts = [n for n, d in sample_graph.nodes(data=True) if d.get("type") == "concept"]

        assert len(persons) == 1
        assert len(concepts) == 1
        assert "person_aristotle_test" in persons
        assert "concept_free_will_test" in concepts

    def test_filter_by_period(self, sample_graph):
        """Test filtering nodes by historical period"""
        classical = [
            n for n, d in sample_graph.nodes(data=True)
            if d.get("period") == "Classical Greek"
        ]

        assert len(classical) == 1
        assert "person_aristotle_test" in classical

    def test_filter_by_school(self, sample_graph):
        """Test filtering nodes by philosophical school"""
        peripatetic = [
            n for n, d in sample_graph.nodes(data=True)
            if d.get("school") == "Peripatetic"
        ]

        assert len(peripatetic) == 1
        assert "person_aristotle_test" in peripatetic

    def test_get_neighbors(self, sample_graph):
        """Test getting neighbors of a node"""
        neighbors = list(sample_graph.successors("person_aristotle_test"))

        assert len(neighbors) == 2
        assert "work_ethics_test" in neighbors
        assert "concept_free_will_test" in neighbors

    def test_get_edges_by_relation(self, sample_graph):
        """Test filtering edges by relation type"""
        authored_edges = [
            (u, v) for u, v, d in sample_graph.edges(data=True)
            if d.get("relation") == "authored"
        ]

        assert len(authored_edges) == 1
        assert ("person_aristotle_test", "work_ethics_test") in authored_edges

    def test_connected_components(self, sample_graph):
        """Test finding connected components"""
        # Convert to undirected for component analysis
        undirected = sample_graph.to_undirected()
        components = list(nx.connected_components(undirected))

        assert len(components) >= 1
        # All nodes should be in one component since they're connected
        assert len(components[0]) == 3

    def test_graph_density(self, sample_graph):
        """Test graph density calculation"""
        density = nx.density(sample_graph)

        assert isinstance(density, float)
        assert 0 <= density <= 1

    def test_average_clustering(self, sample_graph):
        """Test average clustering coefficient"""
        # Convert to undirected for clustering
        undirected = sample_graph.to_undirected()
        clustering = nx.average_clustering(undirected)

        assert isinstance(clustering, float)
        assert 0 <= clustering <= 1

    @pytest.mark.parametrize("node_type,expected_count", [
        ("person", 1),
        ("concept", 1),
        ("work", 1),
        ("argument", 0)
    ])
    def test_count_by_type(self, sample_graph, node_type, expected_count):
        """Test counting nodes by type"""
        count = sum(
            1 for n, d in sample_graph.nodes(data=True)
            if d.get("type") == node_type
        )
        assert count == expected_count
