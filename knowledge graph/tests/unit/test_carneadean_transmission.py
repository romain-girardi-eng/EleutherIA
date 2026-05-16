"""Sanity tests for ``scripts/analyze_carneadean_transmission.py``.

These tests are read-only against ``data/kg/`` (no mutation). They skip
gracefully when the JSONL snapshot is not available so CI without KG data
still passes.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

ROOT = Path(__file__).resolve().parents[3]
NODES = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES = ROOT / "data" / "kg" / "edges.jsonl"
SCRIPT = ROOT / "scripts" / "analyze_carneadean_transmission.py"

skip_if_no_kg = pytest.mark.skipif(
    not NODES.exists() or not EDGES.exists() or not SCRIPT.exists(),
    reason="data/kg snapshot or script missing",
)


@pytest.fixture(scope="module")
def transmission_module():  # type: ignore[no-untyped-def]
    """Import the script as a module so we can call its functions directly."""
    if not SCRIPT.exists():
        pytest.skip("script not available")
    sys.path.insert(0, str(ROOT / "knowledge graph" / "src"))
    name = "analyze_carneadean_transmission"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so @dataclass can resolve module-level references
    # via sys.modules (Python 3.12+ dataclass introspection requirement).
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@skip_if_no_kg
def test_canonical_constants_consistent(transmission_module) -> None:
    """Six witnesses, ≥ 6 pivots, six declared witness authors."""
    assert len(transmission_module.WITNESSES) == 6
    assert len(transmission_module.PIVOTS) >= 6
    assert len(transmission_module.WITNESS_AUTHORS) == 6
    witness_ranks = {w[0] for w in transmission_module.WITNESSES}
    author_ranks = {a[0] for a in transmission_module.WITNESS_AUTHORS}
    assert witness_ranks == author_ranks


@skip_if_no_kg
def test_pipeline_runs_and_produces_expected_shape(transmission_module) -> None:  # type: ignore[no-untyped-def]
    state = transmission_module.load_and_materialize(NODES, EDGES)
    assert state.inferred > 0, "OWL-RL closure must materialize at least one inverse"
    witnesses = transmission_module.inventory_witnesses(state.graph)
    assert len(witnesses) == 6
    matrix, attesters = transmission_module.attestation_matrix(state.graph, witnesses)
    assert len(matrix) == 6 * len(transmission_module.PIVOTS)
    # At least three pivots must satisfy the 3/6 Amand rule in the current KG.
    passing = sum(
        1
        for pid, _ in transmission_module.PIVOTS
        if len(attesters.get(pid, set())) >= 3
    )
    assert passing >= 3, f"expected at least 3 pivots passing 3/6 rule, got {passing}"

    chains = transmission_module.transmission_chains(state.graph, max_depth=5)
    assert len(chains) == 6
    assert all(c.found for c in chains), "every witness author must reach Carneades"
    assert all(c.hops >= 1 for c in chains if c.found)

    pivots = transmission_module.proof_chains_for_pivots(state.graph, state.pre_graph)
    # The first pivot (general theme) has many inbound attestations; at least
    # one must yield an inverseOf proof chain.
    total_inverse_rules = sum(p.rule_counts.get("inverseOf", 0) for p in pivots)
    assert total_inverse_rules > 0, "no inverseOf proof chains were reconstructed"


@skip_if_no_kg
def test_render_json_serializable(transmission_module) -> None:
    state = transmission_module.load_and_materialize(NODES, EDGES)
    witnesses = transmission_module.inventory_witnesses(state.graph)
    matrix, attesters = transmission_module.attestation_matrix(state.graph, witnesses)
    chains = transmission_module.transmission_chains(state.graph, max_depth=4)
    pivots = transmission_module.proof_chains_for_pivots(state.graph, state.pre_graph)
    js = transmission_module.render_json(
        state=state,
        witnesses=witnesses,
        matrix=matrix,
        attesters=attesters,
        chains=chains,
        pivots=pivots,
        candidates=[],
        timestamp="2026-05-16T00:00:00+00:00",
    )
    parsed = json.loads(js)
    assert parsed["graph"]["inferred"] == state.inferred
    assert len(parsed["witnesses"]) == 6
    assert len(parsed["transmission_chains"]) == 6
