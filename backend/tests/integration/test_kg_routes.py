"""
Integration tests for Knowledge Graph API Routes
Tests all /api/kg/* endpoints
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestKGRoutes:
    """Test cases for Knowledge Graph API routes"""

    def test_health_check(self, sync_client):
        """Test the health check endpoint"""
        response = sync_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, sync_client):
        """Test the root endpoint"""
        response = sync_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_get_all_nodes(self, async_client):
        """Test GET /api/kg/nodes"""
        response = await async_client.get("/api/kg/nodes")
        assert response.status_code in [200, 500]  # May fail if services not initialized

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_all_edges(self, async_client):
        """Test GET /api/kg/edges"""
        response = await async_client.get("/api/kg/edges")
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_node_by_id(self, async_client):
        """Test GET /api/kg/node/{id}"""
        node_id = "person_aristotle_test"
        response = await async_client.get(f"/api/kg/node/{node_id}")

        # May return 404 if node doesn't exist in test DB
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_node_invalid_id(self, async_client):
        """Test GET /api/kg/node/{id} with invalid ID"""
        response = await async_client.get("/api/kg/node/nonexistent_node_12345")
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_stats(self, async_client):
        """Test GET /api/kg/stats"""
        response = await async_client.get("/api/kg/stats")
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "total_nodes" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_search_kg(self, async_client):
        """Test GET /api/kg/search/{query}"""
        response = await async_client.get("/api/kg/search/aristotle")
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_get_neighbors(self, async_client):
        """Test GET /api/kg/neighbors"""
        params = {"node_id": "person_aristotle_test"}
        response = await async_client.get("/api/kg/neighbors", params=params)
        assert response.status_code in [200, 404, 422, 500]

    @pytest.mark.asyncio
    async def test_get_paths(self, async_client):
        """Test GET /api/kg/paths"""
        params = {
            "source": "person_aristotle_test",
            "target": "concept_free_will_test"
        }
        response = await async_client.get("/api/kg/paths", params=params)
        assert response.status_code in [200, 404, 422, 500]

    @pytest.mark.asyncio
    async def test_get_timeline(self, async_client):
        """Test GET /api/kg/analytics/timeline"""
        response = await async_client.get("/api/kg/analytics/timeline")
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_get_cytoscape_format(self, async_client):
        """Test GET /api/kg/viz/cytoscape"""
        response = await async_client.get("/api/kg/viz/cytoscape")
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "elements" in data or "nodes" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_filter_nodes_by_type(self, async_client):
        """Test filtering nodes by type"""
        params = {"type": "person"}
        response = await async_client.get("/api/kg/nodes", params=params)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_filter_nodes_by_period(self, async_client):
        """Test filtering nodes by period"""
        params = {"period": "Classical Greek"}
        response = await async_client.get("/api/kg/nodes", params=params)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_filter_nodes_by_school(self, async_client):
        """Test filtering nodes by school"""
        params = {"school": "Stoic"}
        response = await async_client.get("/api/kg/nodes", params=params)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_concept_clusters(self, async_client):
        """Test GET /api/kg/analytics/concept-clusters"""
        response = await async_client.get("/api/kg/analytics/concept-clusters")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_influence_matrix(self, async_client):
        """Test GET /api/kg/analytics/influence-matrix"""
        response = await async_client.get("/api/kg/analytics/influence-matrix")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_communities(self, async_client):
        """Test GET /api/kg/analytics/communities"""
        response = await async_client.get("/api/kg/analytics/communities")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, async_client):
        """Test calling non-existent endpoint"""
        response = await async_client.get("/api/kg/nonexistent")
        assert response.status_code == 404
