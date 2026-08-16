"""Regression tests for the reworked deterministic ancient-text verifier (G4).

Greek/Latin fixtures are never composed by hand: they are imported verbatim
from existing repo fixtures (``test_programmatic_verify_quotes``, itself
sourcing audit-derived strings from ``data/eval/must_not_appear.jsonl``) or
derived from them by mechanical transformations (slicing, accent stripping,
sigma swapping, punctuation insertion).
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.scholarly_agent import (
    ScholarlyAgent,
    _collect_evidence_texts,
    _mark_verifier_v2_error,
    _text_verifier_enabled,
)
from eleutheria_graphrag.agents.state import ScholarlyAnswer
from eleutheria_graphrag.agents.text_verifier import (
    _KNOWN_TERMS,
    _anchor_tokens,
    enforce_answer,
    enforcement_enabled,
    extract_greek_runs,
    extract_quoted_latin_spans,
    is_known_term,
    verify_ancient_text,
)

from .conftest import make_deps
from .test_programmatic_verify_quotes import (
    BUNDLE_GREEK,
    BUNDLE_LATIN,
    BUNDLE_TRANSLATION,
    FOREIGN_GREEK,
    FOREIGN_LATIN,
    _state_with_bundle,
)

_MUST_NOT_APPEAR = (
    Path(__file__).resolve().parents[3] / "data" / "eval" / "must_not_appear.jsonl"
)


def _strip_accents(text: str) -> str:
    """Mechanical accent/breathing removal — derives a variant, composes nothing."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _audit_greek_with_final_sigma(min_words: int = 4) -> str:
    """Audit-derived Greek string containing a final sigma (ς)."""
    for line in _MUST_NOT_APPEAR.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if (
            record.get("language") == "grc"
            and "ς" in record["string"]
            and len(record["string"].split()) >= min_words
        ):
            return record["string"]
    raise RuntimeError("no audit-derived Greek string with final sigma")


SIGMA_GREEK = _audit_greek_with_final_sigma()


class TestExtractGreekRuns:
    def test_finds_greek_text(self):
        text = "Origen argues about αὐτεξούσιον in his work."
        runs = extract_greek_runs(text)
        assert len(runs) == 1
        assert "αὐτεξούσιον" in runs[0][0]

    def test_finds_longer_greek_passage(self):
        text = 'He writes: "ἔνεστι δ\' ὁρᾶν εἰ ταῦτα λέγοντες σώζουσιν" in De Fato.'
        runs = extract_greek_runs(text)
        assert len(runs) >= 1
        assert "ὁρᾶν" in runs[0][0]

    def test_no_greek(self):
        text = "This is plain English text about free will."
        runs = extract_greek_runs(text)
        assert len(runs) == 0

    def test_multiple_runs(self):
        text = "The terms εἱμαρμένη and προαίρεσις are key."
        runs = extract_greek_runs(text)
        assert len(runs) == 2


class TestFreePass:
    def test_known_single_word(self):
        assert is_known_term("αὐτεξούσιον")

    def test_two_word_span_passes(self):
        assert is_known_term(" ".join(BUNDLE_GREEK.split()[:2]))

    def test_three_word_span_must_be_verified(self):
        # Regression: _MAX_TERM_WORDS was 4 — three-word Greek slipped by.
        assert not is_known_term(" ".join(BUNDLE_GREEK.split()[:3]))

    def test_four_word_span_must_be_verified(self):
        assert not is_known_term(" ".join(BUNDLE_GREEK.split()[:4]))

    def test_known_terms_are_single_word_only(self):
        assert all(len(term.split()) == 1 for term in _KNOWN_TERMS)


class TestBundleWhitelist:
    """Old false-positive class: legitimate Greek retrieved from evidence
    bundles was flagged/removed. Bundle-quoted text must pass with NO DB
    query."""

    @pytest.mark.asyncio
    async def test_bundle_text_verified_without_db(self):
        db = AsyncMock()
        answer = f"Justin writes {BUNDLE_GREEK} [P1]."
        result = await verify_ancient_text(answer, db, evidence_texts=[BUNDLE_GREEK])
        assert result.all_verified
        assert result.bundle_whitelisted == 1
        assert result.db_checked == 0
        db.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_accent_variant_matches_bundle(self):
        db = AsyncMock()
        variant = _strip_accents(BUNDLE_GREEK)
        result = await verify_ancient_text(
            f"He writes {variant} there.", db, evidence_texts=[BUNDLE_GREEK]
        )
        assert result.all_verified
        assert result.bundle_whitelisted == 1
        db.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_final_sigma_variant_matches_bundle(self):
        db = AsyncMock()
        variant = SIGMA_GREEK.replace("ς", "σ")
        result = await verify_ancient_text(
            f"The phrase {variant} recurs.", db, evidence_texts=[SIGMA_GREEK]
        )
        assert result.all_verified
        db.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_punctuation_variant_matches_bundle(self):
        db = AsyncMock()
        variant = BUNDLE_GREEK.replace(" ", ", ", 2)
        result = await verify_ancient_text(
            f"He writes {variant} there.", db, evidence_texts=[BUNDLE_GREEK]
        )
        assert result.all_verified
        db.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_span_of_bundle_matches(self):
        db = AsyncMock()
        sub_span = " ".join(BUNDLE_GREEK.split()[1:5])
        result = await verify_ancient_text(
            f"He writes {sub_span} there.", db, evidence_texts=[BUNDLE_GREEK]
        )
        assert result.all_verified
        db.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_quoted_latin_matches_bundle(self):
        db = AsyncMock()
        result = await verify_ancient_text(
            f'Cicero notes: "{FOREIGN_LATIN}".',
            db,
            evidence_texts=[FOREIGN_LATIN],
        )
        assert result.all_verified
        assert result.bundle_whitelisted == 1
        db.fetch.assert_not_called()


class TestDBProbe:
    @pytest.mark.asyncio
    async def test_accent_variant_found_via_fold_compare(self):
        db = AsyncMock()
        db.fetch.return_value = [
            {
                "passage_id": "p1",
                "title": "Apologia Prima",
                "canonical_ref": "43",
                "text_content": BUNDLE_GREEK,
            }
        ]
        variant = _strip_accents(BUNDLE_GREEK)
        result = await verify_ancient_text(f"He writes {variant}.", db)
        assert result.all_verified
        assert result.db_checked == 1
        span = result.verified_spans[0]
        assert span.status == "db_passage"
        assert span.source_id == "p1"
        # The probe anchors on a token of the span, not the full span.
        anchor_arg = db.fetch.await_args_list[0].args[1]
        assert anchor_arg in variant
        assert anchor_arg in _anchor_tokens(variant)

    @pytest.mark.asyncio
    async def test_fabricated_greek_flagged(self):
        db = AsyncMock()
        db.fetch.return_value = []
        result = await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)
        assert not result.all_verified
        assert result.unverified_spans[0].language == "greek"
        assert result.db_checked == 1

    @pytest.mark.asyncio
    async def test_fabricated_quoted_latin_flagged(self):
        db = AsyncMock()
        db.fetch.return_value = []
        result = await verify_ancient_text(f'Cicero writes: "{FOREIGN_LATIN}".', db)
        assert not result.all_verified
        assert result.unverified_spans[0].language == "latin"

    @pytest.mark.asyncio
    async def test_candidate_row_without_span_is_not_a_match(self):
        """The anchor LIKE may return unrelated rows; only the Python
        fold-compare may verify."""
        db = AsyncMock()
        db.fetch.return_value = [
            {
                "passage_id": "p9",
                "title": "De Fato",
                "canonical_ref": "20",
                "text_content": BUNDLE_LATIN,
            }
        ]
        result = await verify_ancient_text(f'Cicero writes: "{FOREIGN_LATIN}".', db)
        assert not result.all_verified

    @pytest.mark.asyncio
    async def test_no_db_still_reports_unverified(self):
        result = await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", None)
        assert not result.all_verified


class TestLatinExtraction:
    def test_quoted_latin_extracted(self):
        spans = extract_quoted_latin_spans(f'He says: "{FOREIGN_LATIN}" here.')
        assert [text for text, _pos in spans] == [FOREIGN_LATIN]

    def test_guillemets_extracted(self):
        spans = extract_quoted_latin_spans(f"Il écrit : « {FOREIGN_LATIN} »")
        assert [text for text, _pos in spans] == [FOREIGN_LATIN]

    def test_unquoted_latin_not_extracted(self):
        # Unquoted Latin prose is indistinguishable from English — out of
        # scope here (the graph_nodes blockquote gate covers blockquotes).
        assert extract_quoted_latin_spans(f"He says: {FOREIGN_LATIN} here.") == []

    def test_quoted_english_with_stopwords_skipped(self):
        text = 'He says: "the fate of every agent is sealed beforehand".'
        assert extract_quoted_latin_spans(text) == []

    def test_quoted_english_content_words_skipped(self):
        # Regression: a quoted English phrase with no function words used to
        # be classified as candidate Latin (report-only noise).
        text = 'He says: "moral responsibility requires causal freedom".'
        assert extract_quoted_latin_spans(text) == []

    def test_quoted_english_determinism_phrase_skipped(self):
        text = 'Bobzien argues: "causal determinism precludes free choice".'
        assert extract_quoted_latin_spans(text) == []

    def test_genuine_latin_unaffected_by_english_lexicon(self):
        # The English content-word check must never reject real Latin:
        # FOREIGN_LATIN and BUNDLE_LATIN contain zero lexicon hits.
        spans = extract_quoted_latin_spans(f'He writes: "{FOREIGN_LATIN}".')
        assert [text for text, _pos in spans] == [FOREIGN_LATIN]
        spans = extract_quoted_latin_spans(f'He writes: "{BUNDLE_LATIN}".')
        assert [text for text, _pos in spans] == [BUNDLE_LATIN]

    def test_production_english_phrases_pass_through(self):
        # Regression (production, 2026-08): both were classified as Latin and
        # removed from the answer as (latin, reason=reference-mismatch).
        assert extract_quoted_latin_spans('Leibniz: "same causes, same effects".') == []
        assert extract_quoted_latin_spans('See "Prohairesis in Epictetus".') == []

    def test_english_title_case_phrase_passes_through(self):
        text = 'the chapter "Moral Luck and Ancient Ethics" argues otherwise.'
        assert extract_quoted_latin_spans(text) == []

    def test_genuine_latin_still_screened(self):
        for latin in ("quicquid futurum est", "voluntas est animi motus"):
            spans = extract_quoted_latin_spans(f'Cicero: "{latin}".')
            assert [text for text, _pos in spans] == [latin]

    def test_latin_endings_alone_are_positive_evidence(self):
        # No Latin function word at all: two Latin-specific endings carry it.
        latin = "liberorum arbitriorum motibus"
        spans = extract_quoted_latin_spans(f'He writes: "{latin}".')
        assert [text for text, _pos in spans] == [latin]

    def test_english_phrase_with_a_latin_term_is_not_a_latin_quotation(self):
        text = 'Dihle traces "the notion of voluntas in Augustine" here.'
        assert extract_quoted_latin_spans(text) == []

    def test_two_word_quote_skipped(self):
        two_words = " ".join(FOREIGN_LATIN.split()[:2])
        assert extract_quoted_latin_spans(f'He says: "{two_words}".') == []

    def test_greek_quote_not_extracted_as_latin(self):
        assert extract_quoted_latin_spans(f'He writes: "{BUNDLE_GREEK}".') == []


class TestEnforcement:
    def test_enforcement_enabled_by_default(self, monkeypatch):
        monkeypatch.delenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", raising=False)
        assert enforcement_enabled()

    def test_enforcement_opt_out_by_env(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", "false")
        assert not enforcement_enabled()

    def test_enforcement_enabled_by_env(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", "true")
        assert enforcement_enabled()

    @pytest.mark.asyncio
    async def test_enforce_drops_only_offending_line(self):
        db = AsyncMock()
        db.fetch.return_value = []
        answer = "\n".join(
            [
                "A sound opening claim [P1].",
                f"Origen wrote {FOREIGN_GREEK} [P2].",
                "A sound closing claim.",
            ]
        )
        result = await verify_ancient_text(answer, db)
        enforced = enforce_answer(answer, result)
        assert FOREIGN_GREEK not in enforced
        assert "A sound opening claim" in enforced
        assert "A sound closing claim" in enforced
        assert "[removed: unverified ancient text]" in enforced

    @pytest.mark.asyncio
    async def test_enforce_noop_when_all_verified(self):
        db = AsyncMock()
        answer = f"Justin writes {BUNDLE_GREEK}."
        result = await verify_ancient_text(answer, db, evidence_texts=[BUNDLE_GREEK])
        assert enforce_answer(answer, result) == answer


class TestAgentWiring:
    """ScholarlyAgent._verify_ancient_text — report-only default, metadata
    recording, enforce gating, env kill-switch."""

    @pytest.mark.asyncio
    async def test_bundle_quoted_answer_passes_without_db(self):
        agent = ScholarlyAgent(make_deps())
        state = _state_with_bundle()
        answer = ScholarlyAnswer(
            answer=f"Justin writes {BUNDLE_GREEK} [P1].", question="q"
        )
        out = await agent._verify_ancient_text(answer, state)
        meta = out.metadata["text_verification"]
        assert meta["bundle_whitelisted"] == 1
        assert meta["db_checked"] == 0
        assert meta["unverified_spans"] == []
        assert meta["enforced"] is False
        agent.deps.db.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_report_only_keeps_prose_and_records_flag(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", "false")
        agent = ScholarlyAgent(make_deps())
        state = _state_with_bundle()
        answer = ScholarlyAnswer(
            answer=f"Origen wrote {FOREIGN_GREEK} [P2].", question="q"
        )
        out = await agent._verify_ancient_text(answer, state)
        assert FOREIGN_GREEK in out.answer  # NEVER auto-deleted
        meta = out.metadata["text_verification"]
        assert len(meta["unverified_spans"]) == 1
        assert meta["enforced"] is False

    @pytest.mark.asyncio
    async def test_enforce_mode_drops_line(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", "true")
        agent = ScholarlyAgent(make_deps())
        state = _state_with_bundle()
        answer = ScholarlyAnswer(
            answer="\n".join(
                [
                    f"Justin writes {BUNDLE_GREEK} [P1].",
                    f"Origen wrote {FOREIGN_GREEK} [P2].",
                ]
            ),
            question="q",
        )
        out = await agent._verify_ancient_text(answer, state)
        assert FOREIGN_GREEK not in out.answer
        assert BUNDLE_GREEK in out.answer
        assert out.metadata["text_verification"]["enforced"] is True

    def test_env_kill_switch(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER", "false")
        assert not _text_verifier_enabled()
        monkeypatch.delenv("ELEUTHERIA_TEXT_VERIFIER", raising=False)
        assert _text_verifier_enabled()

    def test_collect_evidence_texts_includes_bundles(self):
        state = _state_with_bundle()
        texts = _collect_evidence_texts(state)
        assert BUNDLE_GREEK in texts
        assert BUNDLE_TRANSLATION in texts


class TestVerifierV2ErrorMetadata:
    def test_mark_verifier_v2_error_sets_machine_readable_skip(self):
        answer = ScholarlyAnswer(answer="x", question="q")
        out = _mark_verifier_v2_error(answer, RuntimeError("boom"))
        meta = out.metadata["citation_verifier_v2"]
        assert meta["status"] == "error"
        assert "RuntimeError" in meta["reason"]
        assert "boom" in meta["reason"]


class TestKgNodeProbeIntegrityFilter:
    @pytest.mark.asyncio
    async def test_kg_node_probe_excludes_integrity_flagged_nodes(self):
        """The kg_nodes arm of the DB probe must filter audit-flagged rows:
        a node flagged greek_unverified/fabrication_confirmed_pending_fix
        must never return status='db_node' verification."""
        db = AsyncMock()
        db.fetch.return_value = []
        await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)

        kg_node_queries = [
            call.args[0]
            for call in db.fetch.await_args_list
            if "kg_nodes" in call.args[0]
        ]
        assert kg_node_queries, "the kg_nodes probe arm was never exercised"
        for query in kg_node_queries:
            assert "integrity_status" in query
            assert "IS NULL" in query


class TestSchemaResolution:
    """The DB probe must target the schema named by ELEUTHERIA_DB_SCHEMA —
    the same env var as the rest of the graphrag DB layer — with the
    'free_will' literal only as final fallback. Regression: the schema was a
    hardcoded 'free_will' default that no caller overrode."""

    @pytest.mark.asyncio
    async def test_env_var_schema_used_in_probe(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_DB_SCHEMA", "alt_schema")
        db = AsyncMock()
        db.fetch.return_value = []
        await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)
        queries = [call.args[0] for call in db.fetch.await_args_list]
        assert queries
        assert any("alt_schema.passages" in q for q in queries)
        assert all("free_will." not in q for q in queries)

    @pytest.mark.asyncio
    async def test_literal_fallback_without_env(self, monkeypatch):
        monkeypatch.delenv("ELEUTHERIA_DB_SCHEMA", raising=False)
        db = AsyncMock()
        db.fetch.return_value = []
        await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)
        queries = [call.args[0] for call in db.fetch.await_args_list]
        assert queries
        assert any("free_will.passages" in q for q in queries)

    @pytest.mark.asyncio
    async def test_explicit_schema_wins_over_env(self, monkeypatch):
        monkeypatch.setenv("ELEUTHERIA_DB_SCHEMA", "alt_schema")
        db = AsyncMock()
        db.fetch.return_value = []
        await verify_ancient_text(
            f"Origen wrote {FOREIGN_GREEK}.", db, schema="explicit_schema"
        )
        queries = [call.args[0] for call in db.fetch.await_args_list]
        assert queries
        assert all("alt_schema." not in q for q in queries)
        assert any("explicit_schema.passages" in q for q in queries)


class TestToMetadataContract:
    """metadata.text_verification must carry the aggregate fields the
    downstream consumers read (MessageBubble.tsx, share.py,
    graphrag_extras.py): integer ``verified``/``unverified`` counts and the
    ``unverified_texts`` array — not only the span lists."""

    @pytest.mark.asyncio
    async def test_unverified_span_surfaces_in_aggregate_fields(self):
        db = AsyncMock()
        db.fetch.return_value = []
        result = await verify_ancient_text(f"Origen wrote {FOREIGN_GREEK}.", db)
        meta = result.to_metadata()

        assert meta["unverified"] == 1
        assert meta["verified"] == 0
        assert len(meta["unverified_texts"]) == 1
        flagged = meta["unverified_texts"][0]
        assert flagged["text"] == FOREIGN_GREEK[:120]
        assert flagged["language"] == "greek"
        assert flagged["action"] == "flagged"
        # Span lists stay available for detailed consumers.
        assert len(meta["unverified_spans"]) == 1

    @pytest.mark.asyncio
    async def test_verified_span_counts_match(self):
        db = AsyncMock()
        result = await verify_ancient_text(
            f"Justin writes {BUNDLE_GREEK}.", db, evidence_texts=[BUNDLE_GREEK]
        )
        meta = result.to_metadata()
        assert meta["verified"] == 1
        assert meta["unverified"] == 0
        assert meta["unverified_texts"] == []
