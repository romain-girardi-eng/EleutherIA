"""Phase D smoke test — drive a synthetic claim through DraftClaimLedger's
proof-chain attachment and print the resulting non-empty chain.

Bypasses the LLM entirely: we hand-craft an RAGState whose retrieval
layer has already populated ``inferred_edges`` (the same shape the live
``_expand_1hop`` writes in production), then call ``_attach_proof_chains``
exactly as ``DraftClaimLedger.run`` does. Pure-Python, no network."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "graphrag" / "src"))
sys.path.insert(0, str(ROOT / "knowledge graph" / "src"))

from unittest.mock import AsyncMock  # noqa: E402

from eleutheria_graphrag.agents.dependencies import Deps  # noqa: E402
from eleutheria_graphrag.agents.graph_nodes import (  # noqa: E402
    _attach_proof_chains,
)
from eleutheria_graphrag.agents.state import (  # noqa: E402
    ClaimLedgerItem,
    ClaimStatus,
    RAGState,
)
from eleutheria_graphrag.services.retrieval_strategy import SQLStrategy  # noqa: E402


def main() -> int:
    # Synthetic KG: Plato wrote Republic (asserted). The inverse
    # "Republic authored_by Plato" is not in the assertions.
    outgoing = {
        "person_plato": [
            {"source": "person_plato", "target": "work_republic", "relation": "wrote"}
        ]
    }
    incoming = {
        "work_republic": [
            {"source": "person_plato", "target": "work_republic", "relation": "wrote"}
        ]
    }
    deps = Deps(
        db=AsyncMock(),
        llm=AsyncMock(),
        node_lookup={
            "person_plato": {"label": "Plato", "type": "person"},
            "work_republic": {"label": "Republic", "type": "work"},
        },
        outgoing_edges=outgoing,
        incoming_edges=incoming,
    )
    state = RAGState(question="who wrote the Republic?")
    deps.state = state

    # Drive the retrieval layer: starting at "work_republic" — the
    # ontology-aware default surfaces Plato and records the derived
    # ``authored_by`` triple.
    expanded = SQLStrategy()._expand_1hop(["work_republic"], deps, state=state)
    print(f"expanded seeds: {expanded}")
    print(f"inferred_edges: {sorted(state.inferred_edges)}")

    # Construct a claim that uses both inferred-edge endpoints as
    # evidence — exactly the shape the LLM produces when prose
    # references the inferred relation.
    claim = ClaimLedgerItem(
        claim="The Republic is authored by Plato (derived).",
        evidence_ids=["work_republic", "person_plato"],
        confidence=0.95,
        status=ClaimStatus.SUPPORTED,
    )
    direct_claim = ClaimLedgerItem(
        claim="Plato wrote the Republic (directly asserted).",
        evidence_ids=["person_plato"],
        confidence=1.0,
        status=ClaimStatus.SUPPORTED,
    )

    n = _attach_proof_chains(state, deps, [claim, direct_claim])
    print(f"\nproof chains attached: {n}")
    print(f"\nclaim_with_proof.proof_chain =\n{json.dumps(claim.proof_chain, indent=2)}")
    print(f"\ndirect_claim.proof_chain = {direct_claim.proof_chain!r}")

    print(f"\nreasoning trace tail: {state.reasoning_trace[-1].node_name}")
    print(
        "parsed_result.steps[0].rule:",
        state.reasoning_trace[-1].parsed_result["steps"][0]["rule"],  # type: ignore[index]
    )

    assert claim.proof_chain is not None and len(claim.proof_chain) >= 1
    assert direct_claim.proof_chain is None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
