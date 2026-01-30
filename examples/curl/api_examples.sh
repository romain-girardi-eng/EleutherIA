#!/bin/bash
# EleutherIA API examples using curl
# Base URL: http://localhost:8000/api

BASE_URL="http://localhost:8000/api"

echo "=== Health Check ==="
curl -s "$BASE_URL/health" | jq

echo -e "\n=== List Ancient Works (Stoic) ==="
curl -s "$BASE_URL/works?school=Stoic&limit=5" | jq '.[].title'

echo -e "\n=== Search for 'fate' ==="
curl -s "$BASE_URL/search?q=fate&limit=3" | jq '.[] | {author, title, snippet}'

echo -e "\n=== KG Statistics ==="
curl -s "$BASE_URL/kg/statistics" | jq

echo -e "\n=== List KG Nodes (Concepts) ==="
curl -s "$BASE_URL/kg/nodes?node_type=Concept&limit=5" | jq '.[].label'

echo -e "\n=== Get Centrality (Top 5) ==="
curl -s "$BASE_URL/kg/centrality?metric=betweenness&top_k=5" | jq '.top_nodes[] | {label, score}'

echo -e "\n=== GraphRAG Query ==="
curl -s -X POST "$BASE_URL/graphrag/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Stoic fate?", "semantic_k": 5, "graph_depth": 1}' \
  | jq '{answer: .answer[0:200], citations: .citations}'

echo -e "\n=== Done ==="
