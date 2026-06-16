"""GOAL-8 (Workstream B) — citation resolution regression.

The root-cause bug: ``_dialectical_citations`` set ``label = ev_id`` for passages
and fell back to ``ev_id`` for positions, so raw KG/passage node ids
(``b_2dceaab7``, ``scholarly_argument_long_2002_…``, ``concept_…``) flowed
verbatim into the citation payload and rendered as labels in the UI.

This test pins the resolved behaviour for the architect's worst case: a position
whose ``holder`` is empty and whose ``publication`` is ``None`` (nothing to
format) and a passage carried under a hashed ``b_…`` id. After resolution:

* the passage label is the human reference ``"Cicero, De Fato 41-43"`` (no ``b_``),
* the position label is either resolved or the citation is OMITTED — but its
  label NEVER equals the raw ``position_id``, and
* no emitted label matches the leaked-id shape.
"""

from __future__ import annotations

import re

from eleutheria_graphrag.agents.graph_nodes import _dialectical_citations
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ClaimLedgerItem,
    ClaimStatus,
    ControversyFrame,
    ControversyMap,
    EvidenceLayer,
    GroundedPosition,
    PassageRef,
    RAGState,
)

# Same id-shape guard the API uses (routes._LEAKED_ID_RE) — no label may match.
_LEAKED_ID_RE = re.compile(
    r"^(?:b_[0-9a-f]+"
    r"|scholarly_argument_"
    r"|scholar_position_"
    r"|concept_"
    r"|person_"
    r"|work_"
    r"|argument_"
    r"|publication_"
    r"|pub_)"
)

_POSITION_ID = "scholarly_argument_long_2002_aristotelian_tie_to_what_is_up_to_us"
_PASSAGE_ID = "b_2dceaab7"


def _state() -> RAGState:
    # A position with NO holder and NO publication — nothing format_scholar_
    # reference can build from. The OLD code leaked the position_id as the label.
    bare_position = GroundedPosition(
        position_id=_POSITION_ID,
        holder="",
        publication=None,
    )
    # A contested passage carried under a hashed b_ id (the OLD code leaked it).
    passage = PassageRef(
        passage_id=_PASSAGE_ID,
        author="Cicero",
        work="De Fato",
        canonical_ref="41-43",
        original_text="adsensiones igitur...",
        english_text="Assent, then...",
        language="lat",
    )
    frame = ControversyFrame(
        frame_id="up_to_us",
        positions=[bare_position],
        contested_passages=[passage],
    )
    cmap = ControversyMap(
        question_frame="what is up to us?",
        shape=AnswerShape.SURVEY_OF_DEBATES,
        frames=[frame],
    )
    cmap.provenance[passage.passage_id] = passage

    state = RAGState(question="what is up to us?")
    state.controversy_map = cmap
    state.claim_ledger = [
        ClaimLedgerItem(
            claim="Cicero records the Stoic view on assent.",
            evidence_ids=[_PASSAGE_ID],
            support_type="passage",
            status=ClaimStatus.SUPPORTED,
            confidence=0.8,
        ),
        ClaimLedgerItem(
            claim="Long ties the Aristotelian to what is up to us.",
            evidence_ids=[_POSITION_ID],
            support_type="position",
            status=ClaimStatus.SUPPORTED,
            confidence=0.8,
        ),
    ]
    return state


def test_passage_label_resolves_no_raw_id() -> None:
    citations = _dialectical_citations(_state())

    primary = [c for c in citations if c.layer == EvidenceLayer.PRIMARY]
    assert len(primary) == 1
    passage_cite = primary[0]
    # The human reference, NOT the hashed id.
    assert passage_cite.label == "Cicero, De Fato 41-43"
    assert "b_" not in passage_cite.label
    # id is KEPT for clickability.
    assert passage_cite.id == _PASSAGE_ID


def test_position_label_never_equals_position_id() -> None:
    citations = _dialectical_citations(_state())

    secondary = [c for c in citations if c.layer == EvidenceLayer.SECONDARY]
    # With no holder and no publication, the position resolves to nothing →
    # the citation is OMITTED rather than leaking the id.
    for c in secondary:
        assert c.label != _POSITION_ID
        assert c.label.strip() != ""


def test_no_emitted_label_matches_leaked_id_shape() -> None:
    citations = _dialectical_citations(_state())
    for c in citations:
        assert not _LEAKED_ID_RE.match(c.label), (
            f"leaked raw id surfaced as label: {c.label!r}"
        )
