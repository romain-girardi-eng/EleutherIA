#!/usr/bin/env python3
"""
Quick profiling script for analytics endpoints
"""

import time
import json
from pathlib import Path
from services.kg_analytics import (
    build_timeline_overview,
    build_argument_evidence,
    build_concept_clusters,
    build_influence_matrix,
    compute_shortest_path,
)

def profile_endpoint(name, func, *args):
    """Profile a function execution"""
    start = time.perf_counter()
    result = func(*args)
    elapsed = time.perf_counter() - start

    # Estimate result size
    serialized = json.dumps(result)
    size_kb = len(serialized) / 1024

    print(f"{name:30s} | {elapsed*1000:8.2f} ms | {size_kb:8.2f} KB")
    return result, elapsed

def main():
    print("Loading KG database...")
    kg_path = Path(__file__).parent / "ancient_free_will_database.json"

    load_start = time.perf_counter()
    with open(kg_path, 'r', encoding='utf-8') as f:
        kg_data = json.load(f)
    load_time = time.perf_counter() - load_start

    print(f"Database loaded in {load_time*1000:.2f} ms")
    print(f"Nodes: {len(kg_data['nodes'])}, Edges: {len(kg_data['edges'])}")
    print("\n" + "="*70)
    print(f"{'Endpoint':<30} | {'Time':>8} | {'Size':>8}")
    print("="*70)

    # Profile each endpoint
    profile_endpoint("Timeline Overview", build_timeline_overview, kg_data, None)
    profile_endpoint("Argument Evidence", build_argument_evidence, kg_data, None)
    profile_endpoint("Concept Clusters", build_concept_clusters, kg_data, None)
    profile_endpoint("Influence Matrix", build_influence_matrix, kg_data, None)

    # Test path computation
    path_request = {
        "sourceId": "person_aristotle_384_322bce_b2c3d4e5",
        "targetId": "person_augustine_354_430ce_a1b2c3d4",
        "maxDepth": 6,
        "allowBidirectional": True,
    }
    profile_endpoint("Path Computation", compute_shortest_path, kg_data, path_request)

    print("="*70)
    print("\nRunning multiple iterations to test consistency...")

    iterations = 5
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        build_timeline_overview(kg_data, None)
        build_argument_evidence(kg_data, None)
        build_concept_clusters(kg_data, None)
        build_influence_matrix(kg_data, None)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Iteration {i+1}: {elapsed*1000:.2f} ms")

    avg_time = sum(times) / len(times)
    print(f"\nAverage full refresh: {avg_time*1000:.2f} ms")
    print(f"Load time overhead: {load_time*1000:.2f} ms per request")
    print(f"\nTotal time per request: {(load_time + avg_time)*1000:.2f} ms")

if __name__ == "__main__":
    main()
