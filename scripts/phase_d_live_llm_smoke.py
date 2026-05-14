"""Phase D *live LLM* smoke test on the production KG snapshot.

This script complements `scripts/phase_d_smoke.py` (which uses a synthetic
two-node graph and no LLM). Here we:

1. Load the production KG snapshot (`data/kg/{nodes,edges}.jsonl`) into
   the same `Deps` shape the live pipeline uses.
2. Call the real `LLMService` end-to-end to answer a scholarly question
   in French — this exercises the configured primary provider (Fireworks
   / Kimi K2.6 unless overridden via `LLM_PREFERRED_PROVIDER`).
3. Drive the real Phase D ontology-aware retrieval (`SQLStrategy._expand_1hop`
   with `state=state`) over the production KG — this populates
   `state.inferred_edges` with derived `(s, p, o)` triples obtained from
   `CLEAN_INVERSE_PAIRS`.
4. Build a `ClaimLedgerItem` from the live LLM's answer whose
   `evidence_ids` cite both endpoints of an inferred triple, then call
   `_attach_proof_chains(state, deps, [claim])` — the exact code path
   used inside `DraftClaimLedger.run` in production.
5. Emit a single JSON blob to stdout / disk: the question, the LLM
   answer, the populated `proof_chain`, and minimal metadata.

Why this layout. The Supabase tenant referenced by `DATABASE_URL` is
currently unreachable (cf. `MEMORY.md`: FSM broken since Railway
migration), which means `SQLStrategy.discover_seeds` cannot run end-to-
end against the live DB. We therefore exercise the *same* Phase D
functions (`_expand_1hop`, `_attach_proof_chains`) on the *real* KG
snapshot rather than synthesizing fixtures. The wiring being tested
(ontology_aware default, `inferred_edges` tracking, proof-chain
attachment, `ClaimLedgerEntry.proof_chain`) is identical.

Usage:
    .venv/bin/python scripts/phase_d_live_llm_smoke.py \\
        --output docs/reports/phase_d_live_llm_demo.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "graphrag" / "src"))
sys.path.insert(0, str(ROOT / "knowledge graph" / "src"))


def _load_env() -> None:
    """Mirror cli/main.py: hydrate environment from .env if unset."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    with env_path.open() as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env()


DEFAULT_QUESTION = (
    "Quels textes Augustin a-t-il écrits qui discutent du libre arbitre, "
    "et pourquoi le De libero arbitrio occupe-t-il une place centrale dans "
    "ce corpus ?"
)
AUGUSTINE_PERSON_ID = "person_augustine_hippo_d430"


async def run_smoke(
    question: str,
    *,
    seed_node_id: str,
    output_path: Path | None,
    max_inferred_to_dump: int = 8,
) -> dict[str, Any]:
    # Late imports so _load_env runs first.
    from unittest.mock import AsyncMock

    from eleutheria_graphrag.agents.dependencies import Deps
    from eleutheria_graphrag.agents.graph_nodes import _attach_proof_chains
    from eleutheria_graphrag.agents.state import (
        ClaimLedgerItem,
        ClaimStatus,
        RAGState,
    )
    from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider
    from eleutheria_graphrag.services.retrieval_strategy import SQLStrategy
    from eleutheria_kg.services.snapshot import load_kg_snapshot

    started = time.perf_counter()

    # 1) Load the production KG snapshot.
    kg = load_kg_snapshot(ROOT / "data" / "kg")
    nodes = kg["nodes"]
    edges = kg["edges"]
    node_lookup = {str(n["id"]): n for n in nodes}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    incoming: dict[str, list[dict[str, Any]]] = {}
    for e in edges:
        outgoing.setdefault(str(e["source"]), []).append(e)
        incoming.setdefault(str(e["target"]), []).append(e)

    # 2) Build Deps. db is a stub — Phase D retrieval (the ontology-aware
    # hop) only needs node_lookup + outgoing_edges + incoming_edges.
    deps = Deps(
        db=AsyncMock(),
        llm=LLMService(),  # picks provider from env (Fireworks default)
        node_lookup=node_lookup,
        outgoing_edges=outgoing,
        incoming_edges=incoming,
    )
    state = RAGState(question=question)
    deps.state = state

    # 3) Drive Phase D ontology-aware expansion on the real KG.
    # Seeding on the Augustine person node guarantees the inverse pair
    # (authored_by → wrote) is exercised: each inbound `authored_by`
    # edge yields a derived `(person, wrote, work)` triple recorded in
    # `state.inferred_edges`.
    strategy = SQLStrategy()
    expansion_seeds = [seed_node_id]
    expanded_neighbours = strategy._expand_1hop(  # noqa: SLF001 — direct Phase D entry point
        expansion_seeds, deps, state=state
    )

    # Pick the inferred triple whose object node has the richest description
    # — that gives the LLM the most material to ground a real prose claim.
    inferred_sorted = sorted(
        (
            t
            for t in state.inferred_edges
            if t[0] == seed_node_id and t[1] == "wrote"
        ),
        key=lambda t: -(
            len(str(node_lookup.get(t[2], {}).get("description") or ""))
        ),
    )
    if not inferred_sorted:
        raise RuntimeError(
            f"No inferred 'wrote' edges produced from seed {seed_node_id!r} — "
            f"unexpected: {len(state.inferred_edges)} total inferred triples"
        )
    target_triple = inferred_sorted[0]
    target_work_id = target_triple[2]
    target_work = node_lookup.get(target_work_id, {})

    # 4) Real LLM call. We give it the seed node + the inferred target
    # so it can write a grounded paragraph that mentions both — exactly
    # what a production answer would look like.
    seed_node = node_lookup.get(seed_node_id, {})
    system_prompt = (
        "Tu es un spécialiste de la philosophie antique. Tu écris directement "
        "la réponse, sans préambule, sans méta-commentaire, sans étapes de "
        "raisonnement, sans répéter la question. La réponse commence par une "
        "phrase de fond immédiate."
    )
    llm_prompt = (
        "Rédige UN seul paragraphe de 80-110 mots, en français, qui mentionne "
        f"l'auteur « {seed_node.get('label', seed_node_id)} » et l'œuvre "
        f"« {target_work.get('label', target_work_id)} » et explique brièvement "
        "leur rapport au libre arbitre.\n\n"
        "Contraintes strictes :\n"
        "- Pas d'introduction, pas de méta-commentaire, pas de listes.\n"
        "- Aucune autre œuvre que celle nommée ci-dessus.\n"
        "- Commence directement par le nom de l'auteur.\n\n"
        "Contexte de référence :\n"
        f"- {seed_node.get('label', seed_node_id)} : "
        f"{str(seed_node.get('description') or '')[:400]}\n"
        f"- {target_work.get('label', target_work_id)} : "
        f"{str(target_work.get('description') or '')[:400]}\n\n"
        f"(Question du lecteur : {question})"
    )

    llm_started = time.perf_counter()
    try:
        llm_answer = await deps.llm.generate(
            llm_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=800,
        )
        llm_error: str | None = None
    except Exception as exc:  # noqa: BLE001 — capture for honest reporting
        llm_answer = ""
        llm_error = f"{type(exc).__name__}: {exc}"
    llm_elapsed = time.perf_counter() - llm_started
    await deps.llm.close()

    # 5) Build a ClaimLedgerItem citing both endpoints of the inferred
    # triple. _attach_proof_chains will detect the inferred edge inside
    # state.inferred_edges and populate proof_chain.
    claim_text = (
        llm_answer.strip()
        if llm_answer
        else (
            f"{seed_node.get('label', seed_node_id)} a écrit "
            f"{target_work.get('label', target_work_id)} — relation "
            "dérivée par inverseOf depuis l'edge authored_by asserté."
        )
    )
    claim = ClaimLedgerItem(
        claim=claim_text[:600],
        evidence_ids=[seed_node_id, target_work_id],
        confidence=0.95,
        status=ClaimStatus.SUPPORTED,
    )
    # Sanity control: a claim that only cites the seed (no inferred-edge
    # endpoint pair) must NOT receive a proof_chain.
    control_claim = ClaimLedgerItem(
        claim=(
            f"{seed_node.get('label')} est une figure majeure de la "
            "patristique latine (assertion directe, sans inférence)."
        ),
        evidence_ids=[seed_node_id],
        confidence=1.0,
        status=ClaimStatus.SUPPORTED,
    )

    attached = _attach_proof_chains(state, deps, [claim, control_claim])

    # 6) Build a portable JSON-safe report.
    elapsed = time.perf_counter() - started
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "question": question,
        "snapshot": {
            "nodes": len(nodes),
            "edges": len(edges),
            "path": str((ROOT / "data" / "kg").resolve()),
        },
        "phase_d": {
            "ontology_aware_default": True,
            "seed_node_id": seed_node_id,
            "seed_label": seed_node.get("label"),
            "expanded_neighbours_count": len(expanded_neighbours),
            "inferred_edges_total": len(state.inferred_edges),
            "inferred_edges_sample": [
                {"subject": s, "relation": p, "object": o}
                for s, p, o in list(state.inferred_edges)[:max_inferred_to_dump]
            ],
            "target_triple": {
                "subject": target_triple[0],
                "relation": target_triple[1],
                "object": target_triple[2],
                "object_label": target_work.get("label"),
                "object_type": target_work.get("type"),
            },
            "claims_with_proof_chain_attached": attached,
        },
        "llm": {
            "provider_used": deps.llm.last_provider_used,
            "model_used": deps.llm.last_model_used,
            "elapsed_seconds": round(llm_elapsed, 3),
            "answer": llm_answer,
            "error": llm_error,
        },
        "claim_ledger": [
            {
                "claim": claim.claim,
                "evidence_ids": claim.evidence_ids,
                "confidence": claim.confidence,
                "status": claim.status.value,
                "proof_chain": claim.proof_chain,
            },
            {
                "claim": control_claim.claim,
                "evidence_ids": control_claim.evidence_ids,
                "confidence": control_claim.confidence,
                "status": control_claim.status.value,
                "proof_chain": control_claim.proof_chain,
            },
        ],
        "reasoning_trace_tail": [
            {
                "node_name": step.node_name,
                "prompt_summary": step.prompt_summary,
                "parsed_result_keys": (
                    sorted(step.parsed_result.keys())
                    if isinstance(step.parsed_result, dict)
                    else None
                ),
            }
            for step in state.reasoning_trace[-3:]
        ],
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--seed-node-id", default=AUGUSTINE_PERSON_ID)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "reports" / "phase_d_live_llm_demo.json",
    )
    args = parser.parse_args()

    report = asyncio.run(
        run_smoke(
            args.question,
            seed_node_id=args.seed_node_id,
            output_path=args.output,
        )
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    # Assert at least one claim has a non-empty proof_chain — that's the
    # whole point of the smoke test.
    populated = [
        entry
        for entry in report["claim_ledger"]
        if entry.get("proof_chain")
    ]
    if not populated:
        print("\nFAIL: no claim received a populated proof_chain", file=sys.stderr)
        return 1
    print(
        f"\nOK: {len(populated)} claim(s) carry a populated proof_chain "
        f"(provider={report['llm']['provider_used']}, "
        f"model={report['llm']['model_used']}, "
        f"inferred_edges={report['phase_d']['inferred_edges_total']})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
