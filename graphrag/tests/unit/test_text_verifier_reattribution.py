"""Re-attribution of verbatim ancient text cited under the wrong reference.

The production case (2026-08): the only span the deterministic gate removed
from a real answer was Epictetus, *Encheiridion* 51 — verbatim in the corpus
but attached to another reference, and missed by the bounded single-token
probe (its anchor tokens are common). Deleting a genuine quotation because
its reference is wrong loses good content; the right behaviour is to keep the
Greek and correct the reference — without ever keeping Greek that is not
verbatim-attested.

The Greek fixture is the corpus record itself (``data/corpus/passages.jsonl``,
passage ``64838b2c-2480-509a-8182-168d32c82641``), never composed by hand;
``test_fixture_matches_local_corpus_snapshot`` pins it to the snapshot.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from eleutheria_graphrag.agents.dialectical_synthesis import build_provenance_ledger
from eleutheria_graphrag.agents.scholarly_agent import (
    ScholarlyAgent,
    _apply_final_content_gate,
)
from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimStatus,
    ControversyFrame,
    ControversyMap,
    PassageRef,
    ScholarlyAnswer,
)
from eleutheria_graphrag.agents.text_verifier import (
    REASON_AMBIGUOUS_LOCUS,
    REASON_REFERENCE_MISMATCH,
    REASON_UNATTESTED,
    REATTRIBUTION_NOTE,
    enforce_answer,
    locate_verbatim_loci,
    reattribute_unverified_spans,
    verify_ancient_text,
)

from .conftest import make_deps
from .test_programmatic_verify_quotes import (
    BUNDLE_GREEK,
    FOREIGN_GREEK,
    _state_with_bundle,
)

_SNAPSHOT = Path(__file__).resolve().parents[3] / "data" / "corpus" / "passages.jsonl"

ENCH_51_ID = "64838b2c-2480-509a-8182-168d32c82641"
ENCH_51_REF = "Epictetus, Enchiridion 51"
ENCH_51_URN = "urn:cts:greekLit:tlg0557.tlg002:51"
ENCH_51_WORK = "urn_cts_greeklit_tlg0557_grc"
ENCH_51_TEXT = (
    "[URGENCY OF PROKOPĒ - CRUCIAL]\n\n"
    "Greek: νῦν ὁ ἀγὼν καὶ ἤδη πάρεστι τὰ Ὀλύμπια\n"
    "(nyn ho agōn kai ēdē paresti ta Olympia)\n"
    '"Now is the contest and the Olympics are already here"\n\n'
    "1. τέλειος καὶ προκόπτων (teleios kai prokoptōn): complete and progressing\n"
    "2. No postponement: οὐκ ἔστιν ἀναβάλλεσθαι (no putting off)\n"
    "3. One day, one action saves or destroys progress\n\n"
    '- παρὰ μίαν ἡμέραν καὶ ἓν πρᾶγμα - "by one day and one action"\n'
    '- καὶ ἀπόλλυται προκοπὴ καὶ σῴζεται - "progress is lost and saved"\n'
    '- Σωκράτης οὕτως ἀπετελέσθη - "thus Socrates was perfected"\n\n'
    "[EPH HĒMIN DOCTRINE]\n"
    "Progress (προκοπή) is entirely ἐφ’ ἡμῖν - every moment is decisive. "
    "The Olympic metaphor emphasizes that the contest is always NOW, not future."
)
# The span the production gate removed — sliced from the record (first
# bullet line, before its English gloss), not composed.
ENCH_51_SPAN = next(
    line for line in ENCH_51_TEXT.splitlines() if line.startswith("- ")
)[2:].split(' - "')[0]

_LIMIT_RE = re.compile(r"LIMIT\s+(\d+)", re.IGNORECASE)


class FakeCorpusDb:
    """``fetch(sql, anchor)`` over an in-memory passages table with LIKE +
    LIMIT semantics; kg_nodes probes return nothing."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, str]] = []

    async def fetch(self, sql: str, anchor: str) -> list[dict[str, Any]]:
        self.calls.append((sql, anchor))
        if "kg_nodes" in sql:
            return []
        limit = int(_LIMIT_RE.search(sql).group(1))
        hits = [dict(row) for row in self.rows if anchor in row["text_content"]]
        return hits[:limit]


def _row(
    passage_id: str,
    text: str,
    *,
    work_id: str = ENCH_51_WORK,
    canonical_ref: str = ENCH_51_REF,
    title: str = "Enchiridion",
    author: str = "Epictetus",
) -> dict[str, Any]:
    return {
        "passage_id": passage_id,
        "work_id": work_id,
        "canonical_ref": canonical_ref,
        "cts_urn": ENCH_51_URN,
        "text_content": text,
        "title": title,
        "author": author,
    }


def _production_like_table(*extra: dict[str, Any]) -> list[dict[str, Any]]:
    """Thirty filler rows carrying the span's anchor tokens AHEAD of the real
    passage, so the bounded single-token probe (LIMIT 25) misses it exactly
    as it did in production."""
    tokens = ENCH_51_SPAN.split()
    fillers = [
        _row(
            f"filler-{i}",
            f"filler {i} {tokens[2]} {tokens[5]}",
            work_id=f"work-{i}",
            canonical_ref=str(i),
            title="Filler",
            author="Nobody",
        )
        for i in range(30)
    ]
    return [*fillers, _row(ENCH_51_ID, ENCH_51_TEXT), *extra]


def _agent(rows: list[dict[str, Any]]) -> tuple[ScholarlyAgent, FakeCorpusDb]:
    agent = ScholarlyAgent(make_deps())
    db = FakeCorpusDb(rows)
    agent.deps.db = db
    return agent, db


@pytest.fixture(autouse=True)
def _enforce(monkeypatch):
    monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", "true")


def test_fixture_matches_local_corpus_snapshot() -> None:
    if not _SNAPSHOT.exists():
        pytest.skip("local corpus snapshot not available")
    with _SNAPSHOT.open(encoding="utf-8") as handle:
        for line in handle:
            if ENCH_51_ID in line:
                record = json.loads(line)
                break
        else:
            pytest.fail("Encheiridion 51 record missing from the snapshot")
    assert record["text_content"] == ENCH_51_TEXT
    assert record["canonical_ref"] == ENCH_51_REF
    assert record["cts_urn"] == ENCH_51_URN
    assert ENCH_51_SPAN in record["text_content"]


class TestBoundedProbeStillMisses:
    @pytest.mark.asyncio
    async def test_single_token_probe_misses_the_passage(self) -> None:
        """Precondition of the whole feature: the existing probe, unchanged,
        removes the Encheiridion span as ``reference-mismatch``."""
        db = FakeCorpusDb(_production_like_table())
        result = await verify_ancient_text(f"Epictetus: «{ENCH_51_SPAN}» [P1].", db)
        assert not result.all_verified
        assert result.unverified_spans[0].reason == "reference-mismatch"

    @pytest.mark.asyncio
    async def test_locus_probe_finds_it(self) -> None:
        db = FakeCorpusDb(_production_like_table())
        loci = await locate_verbatim_loci(ENCH_51_SPAN, db, "free_will")
        assert [locus.passage_id for locus in loci] == [ENCH_51_ID]
        assert loci[0].label == f"Epictetus, Enchiridion {ENCH_51_REF}"
        # Nothing but the passages table is probed for a locus.
        assert all("passages" in sql for sql, _ in db.calls)


class TestWrongReferenceIsReattributed:
    @pytest.mark.asyncio
    async def test_encheiridion_kept_and_recited(self) -> None:
        agent, _ = _agent(_production_like_table())
        state = _state_with_bundle()  # P1 = Justin, Apol. 43 (passage p1)
        answer = ScholarlyAnswer(
            answer="\n".join(
                [
                    f"Justin writes {BUNDLE_GREEK} [P1].",
                    f"Epictetus insists «{ENCH_51_SPAN}» [P1].",
                ]
            ),
            question="q",
            citations=[Citation(ref="P1", type="passage", id="p1", label="Apol. 43")],
        )
        out = await agent._verify_ancient_text(answer, state)

        assert ENCH_51_SPAN in out.answer, "verbatim Greek must not be deleted"
        assert "[removed:" not in out.answer
        assert f"«{ENCH_51_SPAN}» [P2]." in out.answer
        assert f"Justin writes {BUNDLE_GREEK} [P1]." in out.answer

        added = [c for c in out.citations if c.id == ENCH_51_ID]
        assert len(added) == 1
        assert added[0].ref == "P2"
        assert added[0].type == "passage"
        assert added[0].verified is True
        assert added[0].verification_note == REATTRIBUTION_NOTE
        assert added[0].cts_urn == ENCH_51_URN
        assert added[0].label == f"Epictetus, Enchiridion {ENCH_51_REF}"

        meta = out.metadata["text_verification"]
        assert meta["unverified"] == 0
        assert meta["reattributed_citation_ids"] == [ENCH_51_ID]
        (record,) = meta["reattributed_spans"]
        assert record["text"] == ENCH_51_SPAN
        assert record["from_ref"] == "P1"
        assert record["from_id"] == "p1"
        assert record["to_ref"] == "P2"
        assert record["to_passage_id"] == ENCH_51_ID
        assert record["citation_added"] is True
        kept = [s for s in meta["verified_spans"] if s["text"] == ENCH_51_SPAN]
        assert kept[0]["status"] == "db_passage"
        assert kept[0]["source_id"] == ENCH_51_ID

    @pytest.mark.asyncio
    async def test_no_adjacent_marker_appends_one(self) -> None:
        agent, _ = _agent(_production_like_table())
        answer = ScholarlyAnswer(
            answer=f"Epictetus insists «{ENCH_51_SPAN}», and moves on.",
            question="q",
        )
        out = await agent._verify_ancient_text(answer, _state_with_bundle())
        assert f"«{ENCH_51_SPAN}» [P1], and moves on." in out.answer
        assert [c.ref for c in out.citations] == ["P1"]
        record = out.metadata["text_verification"]["reattributed_spans"][0]
        assert record["from_ref"] is None

    @pytest.mark.asyncio
    async def test_rerun_on_recited_prose_is_idempotent(self) -> None:
        """The referee re-runs the gate on revised prose: an already corrected
        marker must neither be rewritten nor yield a duplicate citation."""
        agent, _ = _agent(_production_like_table())
        state = _state_with_bundle()
        first = await agent._verify_ancient_text(
            ScholarlyAnswer(answer=f"Epictetus: «{ENCH_51_SPAN}» [P1].", question="q"),
            state,
        )
        second = await agent._verify_ancient_text(first, state)
        assert second.answer == first.answer
        assert [c.id for c in second.citations] == [ENCH_51_ID]
        meta = second.metadata["text_verification"]
        assert meta["reattributed_citation_ids"] == [ENCH_51_ID]
        assert meta["reattributed_spans"][0]["citation_added"] is False

    @pytest.mark.asyncio
    async def test_same_locus_in_two_rows_is_one_locus(self) -> None:
        """An original and a commentary record of the same passage share a
        work+locus: that is not an ambiguity."""
        twin = _row(
            "ench-51-commentary", f"Commentary record: {ENCH_51_SPAN} discussed."
        )
        agent, _ = _agent(_production_like_table(twin))
        out = await agent._verify_ancient_text(
            ScholarlyAnswer(answer=f"Epictetus: «{ENCH_51_SPAN}».", question="q"),
            _state_with_bundle(),
        )
        assert ENCH_51_SPAN in out.answer
        assert out.metadata["text_verification"]["reattributed_spans"]

    @pytest.mark.asyncio
    async def test_report_only_mode_leaves_prose_untouched(self, monkeypatch) -> None:
        monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", "false")
        agent, _ = _agent(_production_like_table())
        text = f"Epictetus: «{ENCH_51_SPAN}» [P1]."
        out = await agent._verify_ancient_text(
            ScholarlyAnswer(answer=text, question="q"), _state_with_bundle()
        )
        assert out.answer == text
        assert out.citations == []
        assert out.metadata["text_verification"]["reattributed_spans"] == []


class TestZeroFabricationGuaranteeKept:
    @pytest.mark.asyncio
    async def test_ambiguous_locus_is_removed_with_loci_recorded(self) -> None:
        other = _row(
            "other-work-row",
            f"Another author quoting: {ENCH_51_SPAN}.",
            work_id="work-other",
            canonical_ref="3.2",
            title="Stromateis",
            author="Clement",
        )
        agent, _ = _agent(_production_like_table(other))
        out = await agent._verify_ancient_text(
            ScholarlyAnswer(
                answer="\n".join(
                    [
                        f"Justin writes {BUNDLE_GREEK} [P1].",
                        f"Someone: «{ENCH_51_SPAN}» [P1].",
                    ]
                ),
                question="q",
            ),
            _state_with_bundle(),
        )
        assert ENCH_51_SPAN not in out.answer
        assert out.citations == []
        meta = out.metadata["text_verification"]
        assert meta["enforced"] is True
        assert meta["reattributed_spans"] == []
        (span,) = meta["unverified_spans"]
        assert span["reason"] == REASON_AMBIGUOUS_LOCUS
        assert len(span["loci"]) == 2
        assert any(ENCH_51_ID in locus for locus in span["loci"])
        assert any("Clement, Stromateis 3.2" in locus for locus in span["loci"])
        assert meta["unverified_texts"][0]["reason"] == REASON_AMBIGUOUS_LOCUS

    @pytest.mark.asyncio
    async def test_unattested_greek_is_still_removed(self) -> None:
        agent, _ = _agent(_production_like_table())
        out = await agent._verify_ancient_text(
            ScholarlyAnswer(
                answer="\n".join(
                    [
                        f"Justin writes {BUNDLE_GREEK} [P1].",
                        f"Origen wrote {FOREIGN_GREEK} [P2].",
                    ]
                ),
                question="q",
            ),
            _state_with_bundle(),
        )
        assert FOREIGN_GREEK not in out.answer
        assert BUNDLE_GREEK in out.answer
        meta = out.metadata["text_verification"]
        assert meta["reattributed_spans"] == []
        assert meta["reattributed_citation_ids"] == []
        # Classified by the unchanged probe (an anchor token may hit a
        # candidate row) — never as a locus ambiguity.
        assert meta["unverified_spans"][0]["reason"] in {
            REASON_UNATTESTED,
            REASON_REFERENCE_MISMATCH,
        }
        assert "loci" not in meta["unverified_spans"][0]
        assert out.citations == []

    @pytest.mark.asyncio
    async def test_partial_overlap_with_a_passage_is_not_attested(self) -> None:
        """A span only partly present in the one candidate passage is not
        verbatim: no re-attribution, removed as today."""
        agent, _ = _agent(_production_like_table())
        words = ENCH_51_SPAN.split()
        mangled = " ".join([*words[:4], *reversed(words[4:])])
        out = await agent._verify_ancient_text(
            ScholarlyAnswer(answer=f"Epictetus: «{mangled}» [P1].", question="q"),
            _state_with_bundle(),
        )
        assert mangled not in out.answer
        assert out.citations == []
        assert out.metadata["text_verification"]["reattributed_spans"] == []


class TestPositionsAndEnforcement:
    @pytest.mark.asyncio
    async def test_marker_insertion_keeps_later_removals_aligned(self) -> None:
        """A marker inserted on line 1 shifts line 2: the still-unverified
        span there must be dropped from the right line."""
        db = FakeCorpusDb(_production_like_table())
        text = "\n".join(
            [
                f"Epictetus: «{ENCH_51_SPAN}», he says.",
                f"Origen wrote {FOREIGN_GREEK}.",
                "Closing remark.",
            ]
        )
        result = await verify_ancient_text(text, db)
        assert len(result.unverified_spans) == 2
        rescued = await reattribute_unverified_spans(
            text, result, db, schema="free_will"
        )
        assert len(result.unverified_spans) == 1
        remaining = result.unverified_spans[0]
        assert rescued.text[remaining.position :].startswith(FOREIGN_GREEK)
        rendered = enforce_answer(rescued.text, result)
        lines = rendered.split("\n")
        assert lines[0] == f"Epictetus: «{ENCH_51_SPAN}» [P1], he says."
        assert lines[1] == "*[removed: unverified ancient text]*"
        assert lines[2] == "Closing remark."

    @pytest.mark.asyncio
    async def test_no_db_is_a_no_op(self) -> None:
        text = f"Epictetus: «{ENCH_51_SPAN}»."
        result = await verify_ancient_text(text, None)
        rescued = await reattribute_unverified_spans(text, result, None)
        assert rescued.text == text
        assert rescued.citations == []
        assert not result.all_verified


class TestDialecticalScheme:
    @pytest.mark.asyncio
    async def test_marker_and_provenance_follow_the_dialectical_scheme(self) -> None:
        agent, _ = _agent(_production_like_table())
        state = _state_with_bundle()
        wrong = PassageRef(
            passage_id="p1",
            work="Apologia Prima",
            author="Justin Martyr",
            canonical_ref="43",
            original_text=BUNDLE_GREEK,
        )
        state.controversy_map = ControversyMap(
            frames=[ControversyFrame(frame_id="f1", contested_passages=[wrong])]
        )
        state.metadata["render_answer_mode"] = "dialectical"
        prose = (
            f"Justin writes {BUNDLE_GREEK} [passage_p1: Apol. 43]. "
            f"Epictetus insists «{ENCH_51_SPAN}» [passage_p1: Apol. 43]."
        )
        answer = ScholarlyAnswer(
            answer=prose,
            question="q",
            citations=[Citation(ref="p1", type="passage", id="p1", label="Apol. 43")],
        )
        out = await agent._verify_ancient_text(answer, state)

        assert f"«{ENCH_51_SPAN}» [passage_{ENCH_51_ID}]." in out.answer
        assert "[passage_p1: Apol. 43]." in out.answer  # the correct one stays
        assert state.controversy_map.provenance[ENCH_51_ID].original_text == (
            ENCH_51_TEXT
        )

        ledger = build_provenance_ledger(out.answer, state.controversy_map)
        by_id = {item.evidence_ids[0]: item for item in ledger if item.evidence_ids}
        assert by_id[ENCH_51_ID].status is ClaimStatus.SUPPORTED
        assert by_id["p1"].status is ClaimStatus.SUPPORTED

        # The rebuild after the referee keeps the re-attribution note.
        final = _apply_final_content_gate(out, state)
        rebuilt = {c.id: c for c in final.citations}
        assert rebuilt[ENCH_51_ID].verification_note == REATTRIBUTION_NOTE
        assert rebuilt[ENCH_51_ID].verified is True
