"""Copy public answer payloads without private, draft-bearing diagnostics.

Call this at serialization/cache boundaries, never on the working RAGState.
The internal state retains diagnostics; a public answer is not a trace dump.
Keep this key policy aligned with frontend/src/utils/publicGraphRagPayload.ts
so old servers and browser snapshots receive the same defence in depth.
"""

from collections.abc import Mapping
from typing import Any

_PRIVATE_KEYS = frozenset(
    {
        "debug_trace",
        "raw_excerpt",
        "raw_output",
        "raw_response",
        "answer_excerpt",
        "reasoning_excerpt",
        "raw_answer",
        "draft_answer",
        "provisionalAnswer",
        "provisional_answer",
        "synthesis_reasoning",
        "scholar_synthesis_reasoning",
        "verification_note",
        "thinking_process",
        "thinking",
        "full_prompt",
    }
)


def public_payload(value: Any, *, _diagnostic: bool = False) -> Any:
    """Return an independent JSON-shaped copy, excluding private subtrees."""
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if key in _PRIVATE_KEYS:
                continue
            if _diagnostic and key in {
                "claim",
                "sentence",
                "clause",
                "reasoning",
                "text",
            }:
                continue
            if key == "research_graph" and isinstance(item, Mapping):
                # This notebook was built BEFORE the publication verdict. Its
                # synthesized claims are drafts, even when marked supported.
                # The public claim_ledger is the sole post-verdict claim list.
                item = {**item, "claims": []}
            if key == "claim_ledger" and isinstance(item, (list, tuple)):
                item = [
                    claim
                    for claim in item
                    if not isinstance(claim, Mapping)
                    or claim.get("status") not in {"insufficient", "unverified"}
                ]
            result[key] = public_payload(
                item,
                _diagnostic=_diagnostic
                or key in {"citation_verifier_v2", "text_verification"},
            )
        return result
    if isinstance(value, (list, tuple)):
        return [public_payload(item, _diagnostic=_diagnostic) for item in value]
    return value
