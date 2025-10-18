#!/usr/bin/env python3
"""
Knowledge Graph API Routes
Endpoints for accessing KG nodes, edges, and visualizations
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Any, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

# Path to KG database
# In Docker: /app/api/kg_routes.py -> /app/ancient_free_will_database.json
# Locally: backend/api/kg_routes.py -> ancient_free_will_database.json
KG_PATH = Path(__file__).parent.parent / "ancient_free_will_database.json"


def load_kg_data() -> Dict[str, Any]:
    """Load Knowledge Graph data"""
    try:
        with open(KG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading KG: {e}")
        raise HTTPException(status_code=500, detail="Failed to load Knowledge Graph")


@router.get("/nodes")
async def get_all_nodes(
    node_type: Optional[str] = None,
    period: Optional[str] = None,
    school: Optional[str] = None
):
    """Get all KG nodes with optional filtering"""
    kg_data = load_kg_data()
    nodes = kg_data.get('nodes', [])

    # Apply filters
    if node_type:
        nodes = [n for n in nodes if n.get('type') == node_type]
    if period:
        nodes = [n for n in nodes if n.get('period') == period]
    if school:
        nodes = [n for n in nodes if n.get('school') == school]

    return {
        'nodes': nodes,
        'total': len(nodes)
    }


@router.get("/edges")
async def get_all_edges(
    relation: Optional[str] = None
):
    """Get all KG edges with optional filtering"""
    kg_data = load_kg_data()
    edges = kg_data.get('edges', [])

    # Apply filters
    if relation:
        edges = [e for e in edges if e.get('relation') == relation]

    return {
        'edges': edges,
        'total': len(edges)
    }


@router.get("/node/{node_id}")
async def get_node_by_id(node_id: str):
    """Get detailed information about a specific node"""
    kg_data = load_kg_data()
    nodes = kg_data.get('nodes', [])

    node = next((n for n in nodes if n.get('id') == node_id), None)

    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    return node


@router.get("/node/{node_id}/connections")
async def get_node_connections(node_id: str):
    """Get all edges connected to a specific node"""
    kg_data = load_kg_data()
    edges = kg_data.get('edges', [])

    # Find edges where node is source or target
    connected_edges = [
        e for e in edges
        if e.get('source') == node_id or e.get('target') == node_id
    ]

    return {
        'node_id': node_id,
        'connections': connected_edges,
        'total': len(connected_edges)
    }


@router.get("/viz/cytoscape")
async def get_cytoscape_data():
    """Get KG data formatted for Cytoscape.js"""
    kg_data = load_kg_data()

    # Format for Cytoscape.js
    cytoscape_data = {
        'elements': {
            'nodes': [
                {
                    'data': {
                        'id': node['id'],
                        'label': node.get('label', ''),
                        'type': node.get('type', ''),
                        'period': node.get('period', ''),
                        'school': node.get('school', ''),
                        **node  # Include all node properties
                    }
                }
                for node in kg_data.get('nodes', [])
            ],
            'edges': [
                {
                    'data': {
                        'id': edge.get('id', f"{edge['source']}-{edge['target']}"),
                        'source': edge['source'],
                        'target': edge['target'],
                        'relation': edge.get('relation', ''),
                        'label': edge.get('relation', ''),
                        **edge  # Include all edge properties
                    }
                }
                for edge in kg_data.get('edges', [])
            ]
        }
    }

    return cytoscape_data


@router.get("/stats")
async def get_kg_stats():
    """Get Knowledge Graph statistics"""
    kg_data = load_kg_data()
    nodes = kg_data.get('nodes', [])
    edges = kg_data.get('edges', [])

    # Node type counts
    node_types = {}
    for node in nodes:
        node_type = node.get('type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    # Relation type counts
    relation_types = {}
    for edge in edges:
        relation = edge.get('relation', 'unknown')
        relation_types[relation] = relation_types.get(relation, 0) + 1

    # Period counts
    periods = {}
    for node in nodes:
        period = node.get('period', 'unknown')
        periods[period] = periods.get(period, 0) + 1

    return {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'node_types': node_types,
        'relation_types': relation_types,
        'periods': periods
    }
