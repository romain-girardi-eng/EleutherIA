"""Attested ancient text kept WITHOUT a citation: term lists, short phrases.

The production case (2026-08, an answer on Origen, *De principiis* III.1):
five Greek runs were removed by the deterministic gate. Two were LISTS OF
TECHNICAL TERMS — scholarly usage, not quotations — whose every lexeme is in
the corpus although the list as a whole is in no passage. Two were SHORT
PHRASES (three tokens) verbatim in the corpus, one in a single locus under a
different accent form (``δυνατόν καὶ μή`` against the corpus's ``δυνατὸν καὶ
μὴ``), the other in six loci. Deleting whole lines for these destroyed good
prose while nothing had been invented.

The fifth run — an Origen sentence the model attached to *De principiis* —
is in fact verbatim in the corpus snapshot too, in two records of the same
work under different reference labels (Contra Celsum ``1.20`` / ``SC 132,
par.: 20, §34``). Twelve tokens long, it is quotation-shaped and follows the
unchanged quotation rules: several distinct loci, removed as
``ambiguous-locus``. Nothing here weakens that.

Every Greek fixture is sliced from ``data/corpus/passages.jsonl`` (NFC-
normalized), never composed; ``test_fixtures_match_local_corpus_snapshot``
pins each slice to its record.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

import pytest

from eleutheria_graphrag.agents.publication_gate import evaluate_publication
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import ScholarlyAnswer
from eleutheria_graphrag.agents.text_verifier import (
    REASON_AMBIGUOUS_LOCUS,
    REASON_REFERENCE_MISMATCH,
    REASON_SHORT_PHRASE_ATTESTED,
    REASON_TERM_LIST_ATTESTED,
    REASON_UNATTESTED,
    REATTRIBUTION_NOTE,
    STATUS_SHORT_PHRASE,
    STATUS_TERM_LIST,
    _final_accent_variants,
    enforce_answer,
    folded_token_count,
    reattribute_unverified_spans,
    term_list_items,
    verify_ancient_text,
)

from .conftest import make_deps
from .test_programmatic_verify_quotes import (
    BUNDLE_GREEK,
    FOREIGN_GREEK,
    SHORT_GREEK,
    _state_with_bundle,
)
from .test_publication_gate import _metadata as _publication_metadata
from .test_text_verifier_reattribution import FakeCorpusDb

_SNAPSHOT = Path(__file__).resolve().parents[3] / "data" / "corpus" / "passages.jsonl"


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# ── Corpus records (sliced from the snapshot, NFC) ───────────────────────────

# Aristotle corpus, Magna Moralia 1.34.11 — holds ``ἕξις``.
HEXIS_ROW = {
    "passage_id": "c89efc4a-5d6e-4147-8082-f63505cbad3d",
    "work_id": "first1k_tlg0086_tlg022_1st1k_grc1_grc",
    "canonical_ref": "1.34.11",
    "cts_urn": "urn:cts:greekLit:tlg0086.tlg022.1st1K-grc1:1.34.11",
    "text_content": (
        "Ὥστε ἡ φρόνησις ἂν εἴη ἕξις τις προαιρετικὴ καὶ πρακτικὴ τῶν ἐφ' ἡμῖν "
        "ὄντων καὶ πρᾶξαι καὶ μὴ πρᾶξαι, ὅσα εἰς τὸ συμφέρον ἤδη συντείνει."
    ),
}
# Marcus Aurelius 4.9.1 — holds ``φύσις``.
PHYSIS_ROW = {
    "passage_id": "764d875e-7816-40a0-aec8-b332f3895c93",
    "work_id": "urn_cts_greeklit_tlg0562_tlg001_grc",
    "canonical_ref": "4.9.1",
    "cts_urn": "urn:cts:greekLit:tlg0562.tlg001.perseus-grc2:4.9.1",
    "text_content": "Ἠνάγκασται ἡ τοῦ συμφέροντος φύσις τοῦτο ποιεῖν.",
}
# Marcus Aurelius 6.53.1 — holds ``ψυχῇ`` (folded: ``ψυχη``).
PSYCHE_ROW = {
    "passage_id": "2f83a780-0409-444a-8c04-06ff288632da",
    "work_id": "urn_cts_greeklit_tlg0562_tlg001_grc",
    "canonical_ref": "6.53.1",
    "cts_urn": "urn:cts:greekLit:tlg0562.tlg001.perseus-grc2:6.53.1",
    "text_content": (
        "Ἔθισον σεαυτὸν πρὸς τῷ ὑφ’ ἑτέρου λεγομένῳ γίνεσθαι ἀπαρενθυμήτως καὶ "
        "ὡς οἷόν τε ἐν τῇ ψυχῇ τοῦ λέγοντος γίνου."
    ),
}
# Origen, De principiis 3.1.4 (full record) — holds ``εὐδόκησις``,
# ``συγκατάθεσις``, ``ῥοπὴ τοῦ ἡγεμονικοῦ`` and ``αὐτοτελὴς αἰτία``.
DE_PRINC_3_1_4_ROW = {
    "passage_id": "caa0cde6-5047-5e61-9ac5-b21415c0323e",
    "work_id": "work_de_principiis_origen_230s_v2w3x4y5_grc",
    "canonical_ref": "De Princ. 3.1.4",
    "cts_urn": "urn:cts:greekLit:tlg2042.tlg002:3.1.4",
    "text_content": (
        "Εἰ δέ τις αὐτὸ τὸ ἔξωθεν λέγοι εἶναι τοιόνδε, ὥστε ἀδυνάτως ἔχειν "
        "ἀντιβλέψαι αὐτῷ τοιῷδε γενομένῳ, οὗτος ἐπιστησάτω τοῖς ἰδίοις πάθεσι "
        "καὶ κινήμασιν, εἰ μὴ εὐδόκησις γίνεται καὶ συγκατάθεσις καὶ ῥοπὴ τοῦ "
        "ἡγεμονικοῦ ἐπὶ τόδε τι διὰ τάσδε τὰς πιθανότητας. οὐ γάρ, φέρ' εἰπεῖν, "
        "ἡ γυνὴ τῷ κρίναντι ἐγκρατεύεσθαι καὶ ἀνέχειν ἑαυτὸν ἀπὸ μίξεων, "
        "ἐπιφανεῖσα καὶ προκαλεσαμένη ἐπὶ τὸ ποιῆσαί τι παρὰ πρόθεσιν, "
        "αὐτοτελὴς αἰτία γίνεται τοῦ τὴν πρόθεσιν ἀθετῆσαι· πάντως γὰρ "
        "εὐδοκήσας τῷ γαργαλισμῷ καὶ τῷ λείῳ τῆς ἡδονῆς, ἀντιβλέψαι αὐτῷ μὴ "
        "βεβουλημένος μηδὲ τὸ κεκριμένον κυρῶσαι, πράττει τὸ ἀκόλαστον. ὁ δέ "
        "τις ἔμπαλιν, τῶν αὐτῶν συμβεβηκότων τῷ πλείονα μαθήματα ἀνειληφότι "
        "καὶ ἠσκηκότι· οἱ μὲν γαργαλισμοὶ καὶ οἱ ἐρεθισμοὶ συμβαίνουσιν, ὁ "
        "λόγος δέ, ἅτε ἐπὶ πλεῖον ἰσχυροποιηθεὶς καὶ τραφεὶς τῇ μελέτῃ καὶ "
        "βεβαιωθεὶς τοῖς δόγμασι πρὸς τὸ καλὸν ἢ ἐγγύς γε τοῦ βεβαιωθῆναι "
        "γεγενημένος, ἀνακρούει τοὺς ἐρεθισμοὺς καὶ ὑπεκλύει τὴν ἐπιθυμίαν."
    ),
}
# Alexander of Aphrodisias, Quaestiones p. 12 — holds ``δυνατὸν καὶ μὴ``
# (grave accents: running text), which the model wrote as ``δυνατόν καὶ μή``.
QUAEST_12_ROW = {
    "passage_id": "c56eb74c-b64f-4868-8ab9-716f7319305e",
    "work_id": "urn_cts_greeklit_tlg0732_tlg012_grc",
    "canonical_ref": "Quaest. p. 12",
    "cts_urn": "urn:cts:greekLit:tlg0732.tlg012:12",
    "text_content": (
        "εἱμαρμένην γίνεται, οὐδὲν τῶν γινομένων ὡς δυνατὸν καὶ μὴ γενέσθαι "
        "γίνεται. ἐδείχθη δ' ὅτι μηδὲ τῶν παρὰ τὴν εἱμαρμένην δυνατόν τι ἔστιν. "
        "οὐδὲν δυνατόν ἐστιν, εἴ γε πᾶν"
    ),
}
# The six loci of ``καὶ μὴ γενέσθαι`` reported by the production gate.
KAI_ME_GENESTHAI_ROWS = [
    {
        "passage_id": "98c9a41f-e99e-4f5b-827f-cdeeb3fa8220",
        "work_id": "tlg0732_tlg014_grc",
        "canonical_ref": "De Fato 10",
        "cts_urn": "urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1:10",
        "text_content": (
            "δὲ ἀδύνατον μὴ γενέσθαι, πῶς οἷόν τε τοῦτο λέγειν ἐνδέχεσθαι καὶ μὴ "
            "γενέσθαι; τὸ γὰρ ἀδύνατον μὴ γενέσθαι ἀναγκαῖον γενέσθαι. πάντα ἄρα τὰ"
        ),
    },
    {
        "passage_id": "498c37b2-4b5a-4f79-90f2-219e37f58d5e",
        "work_id": "tlg0732_tlg014_grc",
        "canonical_ref": "De Fato 27",
        "cts_urn": "urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1:27",
        "text_content": (
            "μὲν τοῦ τὴν ἀρετὴν ἔχειν τόνδε τινὰ ἀληθὲς ἦν τὸ ἐνδέχεσθαι καὶ μὴ "
            "γενέσθαι τοιοῦτον, ὃ δὲ τοιοῦτον γίνεται, τοῦτο καὶ γενόμενον ἀληθὲς"
        ),
    },
    {
        "passage_id": "8a7ecc77-2a73-5d39-8470-46b65ff495e0",
        "work_id": "tlg1264_tlg001_1st1k_grc1_grc",
        "canonical_ref": "SVF II.957",
        "cts_urn": "urn:cts:greekLit:tlg1264.tlg001.1st1K-grc1:957",
        "text_content": (
            "ἀκούει ἀντὶ τοῦ κατηναγκασμένως, οὐ δώσομεν αὐτῷ· δυνατὸν γὰρ ἦν καὶ "
            "μὴ γενέσθαι· εἰ δὲ τὸ πάντως λέγει ἀντὶ τοῦ ἔσται, ὅπερ οὐ κωλύεται "
            "εἶναι"
        ),
    },
    {
        "passage_id": "81da63cf-fb17-5581-9fc2-9bae9d06cf0f",
        "work_id": "tlg1264_tlg001_1st1k_grc1_grc",
        "canonical_ref": "SVF II.964",
        "cts_urn": "urn:cts:greekLit:tlg1264.tlg001.1st1K-grc1:964",
        "text_content": (
            "ἐνδέχεται ψεύσασθαι· ἐνδέχεται δὲ περὶ τῶν ἐνδεχομένων γενέσθαι καὶ "
            "μὴ γενέσθαι φρονῆσαι τὸ γενέσθαι αὐτὰ καὶ τὸ μὴ γενέσθαι. — — Καὶ "
            "λέγοι"
        ),
    },
    {
        "passage_id": "15cd3c13-ae01-43e2-b89f-724c52ac3894",
        "work_id": "urn_cts_greeklit_tlg0007_tlg108_grc",
        "canonical_ref": "De fato 6 (570F–571E)",
        "cts_urn": "urn:cts:greekLit:tlg0007.tlg108.perseus-grc2:6",
        "text_content": (
            "ἀδύνατον τὸ μὴ καταδῦναι· τὸ δὲ καταδύντος ἡλίου ὄμβρον γενέσθαι καὶ "
            "μὴ γενέσθαι, ἀμφότερα δυνατὰ καὶ ἐνδεχόμενα. πάλιν δὲ καὶ ἐπὶ τοῦ "
            "ἐνδεχομένου,"
        ),
    },
    {
        "passage_id": "aae362b3-1b81-59fa-a5ce-e7f46a9edf07",
        "work_id": "work_clement_stromateis_grc",
        "canonical_ref": "Strom. IV.24.153",
        "cts_urn": "urn:cts:greekLit:tlg0555.tlg004.perseus-grc2:4.24.153",
        "text_content": (
            "δυνατὸν εὑρίσκεται τὸ ἐφ’ ἡμῖν. καὶ δὴ αἱ ἐντολαὶ οἷαί τε γενέσθαι "
            "καὶ μὴ γενέσθαι ὑφ’ ἡμῶν, οἷς εὐλόγως ἕπεται ἔπαινός τε καὶ ψόγος, "
            "οἵ τ’ αὖ"
        ),
    },
]
# Origen, Contra Celsum — the same sentence in two records of one work under
# two reference labels (a duplicate ingestion of the SC text).
CONTRA_CELSUM_TEXT = (
    "τινος προγνώσεως θεσπισθέν, ἐπεὶ ἐθεσπίσθη · ἡμεῖς δὲ τοῦτο οὐ διδόντες "
    "φαμὲν οὐχὶ τὸν θεσπίσαντα αἴτιον εἶναι τοῦ ἐσομένου, ἐπεὶ προεῖπεν αὐτὸ "
    "γενησόμενον, ἀλλὰ τὸ ἐσόμενον, ἐσόμενον ἂν καὶ μὴ θεσπισθέν,"
)
CONTRA_CELSUM_ROWS = [
    {
        "passage_id": "b2e5f00e-d451-4b7d-8ace-0505c026f302",
        "work_id": "sc_origenes_contra_celsum_grc",
        "canonical_ref": "1.20",
        "cts_urn": None,
        "text_content": CONTRA_CELSUM_TEXT,
    },
    {
        "passage_id": "d68181e9-e3ba-4265-85af-2595c3bc8037",
        "work_id": "sc_origenes_contra_celsum_grc",
        "canonical_ref": "SC 132, par.: 20, §34",
        "cts_urn": None,
        "text_content": CONTRA_CELSUM_TEXT,
    },
]

PINNED_ROWS = [
    HEXIS_ROW,
    PHYSIS_ROW,
    PSYCHE_ROW,
    DE_PRINC_3_1_4_ROW,
    QUAEST_12_ROW,
    *KAI_ME_GENESTHAI_ROWS,
    *CONTRA_CELSUM_ROWS,
]

# ── The five production spans (as the gate reported them) ────────────────────

TERM_LIST_1 = "ἕξις, φύσις, ψυχή"
TERM_LIST_2 = "αὐτοτελὴς αἰτία, εὐδόκησις, συγκατάθεσις, ῥοπὴ τοῦ ἡγεμονικοῦ"
# Sliced from the Contra Celsum record: the clause up to its first comma.
ORIGEN_SENTENCE = CONTRA_CELSUM_TEXT.split("· ", 1)[1].split(",", 1)[0]
SHORT_PHRASE_4 = "δυνατόν καὶ μή"
SHORT_PHRASE_5 = "καὶ μὴ γενέσθαι"

# Sliced from the Quaestiones record: five tokens, no list separator.
FIVE_TOKEN_RUN = " ".join(QUAEST_12_ROW["text_content"].split()[2:7])
# Sliced from the De principiis record: five tokens joined by ``καὶ``.
_DE_PRINC_TEXT = DE_PRINC_3_1_4_ROW["text_content"]
KAI_JOINED_RUN = " ".join(
    _DE_PRINC_TEXT[_DE_PRINC_TEXT.index("γαργαλισμοὶ καὶ") :].split()[:5]
).rstrip(",")
# Three tokens of the audit-derived must-not-appear Greek.
THREE_TOKEN_FOREIGN = " ".join(FOREIGN_GREEK.split()[:3])


def _label_row(row: dict[str, Any]) -> dict[str, Any]:
    return {**row, "title": row["work_id"], "author": ""}


def _fillers(*tokens: str, count: int = 30) -> list[dict[str, Any]]:
    """Rows carrying the span's anchor tokens AHEAD of the real records, so
    the bounded single-token probe (LIMIT 25) misses them exactly as it did
    in production and the rescue pass is what decides."""
    return [
        {
            "passage_id": f"filler-{i}",
            "work_id": f"filler-work-{i}",
            "canonical_ref": str(i),
            "cts_urn": None,
            "text_content": f"filler {i} " + " ".join(tokens),
            "title": "Filler",
            "author": "Nobody",
        }
        for i in range(count)
    ]


def _table(*rows: dict[str, Any], fillers: list[dict[str, Any]] = ()) -> list[dict]:
    return [*fillers, *(_label_row(row) for row in rows)]


def _agent(rows: list[dict[str, Any]]) -> tuple[ScholarlyAgent, FakeCorpusDb]:
    agent = ScholarlyAgent(make_deps())
    db = FakeCorpusDb(rows)
    agent.deps.db = db
    return agent, db


async def _gate(rows: list[dict[str, Any]], *lines: str) -> ScholarlyAnswer:
    agent, _ = _agent(rows)
    answer = ScholarlyAnswer(answer="\n".join(lines), question="q")
    return await agent._verify_ancient_text(answer, _state_with_bundle())


@pytest.fixture(autouse=True)
def _enforce(monkeypatch):
    monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", "true")


def test_fixtures_match_local_corpus_snapshot() -> None:
    if not _SNAPSHOT.exists():
        pytest.skip("local corpus snapshot not available")
    wanted = {row["passage_id"]: row for row in PINNED_ROWS}
    seen: dict[str, dict[str, Any]] = {}
    with _SNAPSHOT.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record["passage_id"] in wanted:
                seen[record["passage_id"]] = record
    assert set(seen) == set(wanted)
    for passage_id, row in wanted.items():
        record = seen[passage_id]
        assert _nfc(row["text_content"]) in _nfc(record["text_content"]), passage_id
        assert record["canonical_ref"] == row["canonical_ref"], passage_id
        assert record["cts_urn"] == row["cts_urn"], passage_id
        assert record["work_canonical_id"] == row["work_id"], passage_id


# ── Shape helpers ────────────────────────────────────────────────────────────


class TestShapes:
    def test_token_count_uses_the_verifier_fold(self) -> None:
        assert folded_token_count(TERM_LIST_1) == 3
        assert folded_token_count(SHORT_PHRASE_4) == 3
        assert folded_token_count(SHORT_PHRASE_5) == 3
        assert folded_token_count(TERM_LIST_2) == 7
        assert folded_token_count(ORIGEN_SENTENCE) == 13

    def test_term_lists_split_on_punctuation_and_kai(self) -> None:
        assert term_list_items(TERM_LIST_1) == ["ἕξις", "φύσις", "ψυχή"]
        assert term_list_items(TERM_LIST_2) == [
            "αὐτοτελὴς αἰτία",
            "εὐδόκησις",
            "συγκατάθεσις",
            "ῥοπὴ τοῦ ἡγεμονικοῦ",
        ]
        assert term_list_items(KAI_JOINED_RUN) == [
            "γαργαλισμοὶ",
            "οἱ ἐρεθισμοὶ συμβαίνουσιν",
        ]

    def test_clause_fragments_are_not_a_term_list(self) -> None:
        # ``εἰ … , καὶ τὸ μὴ …``: chunks of a sentence, not lexemes.
        assert term_list_items(FOREIGN_GREEK) == []
        assert term_list_items(ORIGEN_SENTENCE) == []
        # A leading ``καὶ`` is not a separator; ``μὴ`` is a clause particle.
        assert term_list_items(SHORT_PHRASE_5) == []
        assert term_list_items(SHORT_PHRASE_4) == []
        # No separator at all.
        assert term_list_items(FIVE_TOKEN_RUN) == []
        # Elided runs are quotation-shaped.
        assert term_list_items("ἕξις, φύσις … ψυχή") == []

    def test_final_accent_variants(self) -> None:
        assert _final_accent_variants(SHORT_PHRASE_4) == [
            "δυνατόν καὶ μή",
            "δυνατὸν καὶ μὴ",
            "δυνατόν καί μή",
        ]
        # An acute on an earlier syllable is left alone.
        assert _final_accent_variants("διδόντες φαμὲν") == [
            "διδόντες φαμὲν",
            "διδόντες φαμέν",
        ]


# ── A. Term lists ────────────────────────────────────────────────────────────


class TestTermLists:
    @pytest.mark.asyncio
    async def test_lexeme_list_is_kept_without_citation(self) -> None:
        out = await _gate(
            _table(HEXIS_ROW, PHYSIS_ROW, PSYCHE_ROW),
            f"Justin writes {BUNDLE_GREEK} [P1].",
            f"Origen's anthropology turns on three terms ({TERM_LIST_1}) [P1].",
        )
        assert TERM_LIST_1 in out.answer
        assert "[removed:" not in out.answer
        assert out.citations == []
        meta = out.metadata["text_verification"]
        assert meta["unverified"] == 0
        assert meta["unverified_texts"] == []
        assert meta["reattributed_spans"] == []
        (kept,) = meta["attested_spans"]
        assert kept["text"] == TERM_LIST_1
        assert kept["status"] == STATUS_TERM_LIST
        assert kept["reason"] == REASON_TERM_LIST_ATTESTED
        assert kept["items"] == ["ἕξις", "φύσις", "ψυχή"]
        # Also a verified span, so the aggregate counts stay coherent.
        assert any(
            s["text"] == TERM_LIST_1 and s["status"] == STATUS_TERM_LIST
            for s in meta["verified_spans"]
        )

    @pytest.mark.asyncio
    async def test_stoic_causal_vocabulary_list_is_kept(self) -> None:
        out = await _gate(
            _table(DE_PRINC_3_1_4_ROW),
            f"The Stoic vocabulary of assent ({TERM_LIST_2}) is Origen's own [P1].",
        )
        assert TERM_LIST_2 in out.answer
        assert out.citations == []
        meta = out.metadata["text_verification"]
        assert meta["unverified"] == 0
        (kept,) = meta["attested_spans"]
        assert kept["reason"] == REASON_TERM_LIST_ATTESTED
        assert kept["items"] == [
            "αὐτοτελὴς αἰτία",
            "εὐδόκησις",
            "συγκατάθεσις",
            "ῥοπὴ τοῦ ἡγεμονικοῦ",
        ]

    @pytest.mark.asyncio
    async def test_list_with_one_unattested_item_is_removed(self) -> None:
        tainted = f"ἕξις, φύσις, {SHORT_GREEK}"
        out = await _gate(
            _table(HEXIS_ROW, PHYSIS_ROW, PSYCHE_ROW),
            f"Justin writes {BUNDLE_GREEK} [P1].",
            f"Three terms ({tainted}) [P1].",
            "Closing remark.",
        )
        assert tainted not in out.answer
        assert "*[removed: unverified ancient text]*" in out.answer
        meta = out.metadata["text_verification"]
        assert meta["unverified"] == 1
        assert meta["attested_spans"] == []
        (span,) = meta["unverified_spans"]
        assert span["text"] == tainted
        assert span["reason"] in {REASON_UNATTESTED, REASON_REFERENCE_MISMATCH}
        assert span["failed_item"] == SHORT_GREEK
        assert meta["unverified_texts"][0]["failed_item"] == SHORT_GREEK

    @pytest.mark.asyncio
    async def test_sentence_chunks_are_not_laundered_as_a_list(self) -> None:
        out = await _gate(
            _table(HEXIS_ROW, PHYSIS_ROW, PSYCHE_ROW),
            f"Justin writes {BUNDLE_GREEK} [P1].",
            f"Origen wrote {FOREIGN_GREEK} [P1].",
        )
        assert FOREIGN_GREEK not in out.answer
        assert out.metadata["text_verification"]["attested_spans"] == []

    @pytest.mark.asyncio
    async def test_kai_joined_run_attested_as_a_whole_follows_quotation_rules(
        self,
    ) -> None:
        """A five-token run that IS verbatim somewhere is quotation-shaped:
        unique locus → re-cited (never a citation-less list); two loci →
        removed as ambiguous, even though it splits on ``καὶ``."""
        hidden = _fillers("συμβαίνουσιν", "γαργαλισμοὶ")  # probe misses, rescue decides
        out = await _gate(
            _table(DE_PRINC_3_1_4_ROW, fillers=hidden),
            f"Origen: «{KAI_JOINED_RUN}» [P1].",
        )
        assert KAI_JOINED_RUN in out.answer
        assert [c.id for c in out.citations] == [DE_PRINC_3_1_4_ROW["passage_id"]]
        assert out.citations[0].verification_note == REATTRIBUTION_NOTE
        assert out.metadata["text_verification"]["attested_spans"] == []

        other = {
            **DE_PRINC_3_1_4_ROW,
            "passage_id": "other-work-row",
            "work_id": "work-other",
            "canonical_ref": "3.2",
            "text_content": f"Another author quoting: {KAI_JOINED_RUN}.",
        }
        out = await _gate(
            _table(DE_PRINC_3_1_4_ROW, other, fillers=hidden),
            f"Justin writes {BUNDLE_GREEK} [P1].",
            f"Origen: «{KAI_JOINED_RUN}» [P1].",
        )
        assert KAI_JOINED_RUN not in out.answer
        assert out.citations == []
        (span,) = out.metadata["text_verification"]["unverified_spans"]
        assert span["reason"] == REASON_AMBIGUOUS_LOCUS
        assert len(span["loci"]) == 2


# ── B. Short attested phrases ────────────────────────────────────────────────


class TestShortPhrases:
    @pytest.mark.asyncio
    async def test_generic_phrase_in_six_loci_is_kept(self) -> None:
        rows = _table(*KAI_ME_GENESTHAI_ROWS, fillers=_fillers("γενέσθαι"))
        out = await _gate(
            rows,
            f"Justin writes {BUNDLE_GREEK} [P1].",
            f"The modal formula {SHORT_PHRASE_5} is common property [P1].",
        )
        assert SHORT_PHRASE_5 in out.answer
        assert "[removed:" not in out.answer
        assert out.citations == []
        meta = out.metadata["text_verification"]
        assert meta["unverified"] == 0
        assert meta["reattributed_spans"] == []
        (kept,) = meta["attested_spans"]
        assert kept["text"] == SHORT_PHRASE_5
        assert kept["status"] == STATUS_SHORT_PHRASE
        assert kept["reason"] == REASON_SHORT_PHRASE_ATTESTED
        assert kept["loci_count"] == 6

    @pytest.mark.asyncio
    async def test_lexical_accent_form_is_found_and_kept(self) -> None:
        """``δυνατόν καὶ μή`` (lexical acutes) against the corpus's running
        ``δυνατὸν καὶ μὴ``: the accent-blind fold already matched, the LIKE
        anchor now finds the row; one locus, kept without re-attribution."""
        rows = _table(QUAEST_12_ROW, fillers=_fillers("δυνατόν"))
        # Precondition: the bounded probe alone still misses it.
        result = await verify_ancient_text(
            f"Alexander: {SHORT_PHRASE_4}.", FakeCorpusDb(rows)
        )
        assert not result.all_verified

        out = await _gate(rows, f"Alexander's {SHORT_PHRASE_4} is the modal pair [P1].")
        assert SHORT_PHRASE_4 in out.answer
        assert out.citations == []  # no re-attribution for a short phrase
        meta = out.metadata["text_verification"]
        assert meta["unverified"] == 0
        assert meta["reattributed_spans"] == []
        (kept,) = meta["attested_spans"]
        assert kept["reason"] == REASON_SHORT_PHRASE_ATTESTED
        assert kept["loci_count"] == 1

    @pytest.mark.asyncio
    async def test_three_token_unattested_run_is_still_removed(self) -> None:
        out = await _gate(
            _table(QUAEST_12_ROW, *KAI_ME_GENESTHAI_ROWS),
            f"Justin writes {BUNDLE_GREEK} [P1].",
            f"Origen wrote {THREE_TOKEN_FOREIGN} [P1].",
        )
        assert THREE_TOKEN_FOREIGN not in out.answer
        meta = out.metadata["text_verification"]
        assert meta["unverified"] == 1
        assert meta["attested_spans"] == []
        assert meta["unverified_spans"][0]["reason"] in {
            REASON_UNATTESTED,
            REASON_REFERENCE_MISMATCH,
        }

    @pytest.mark.asyncio
    async def test_five_token_ambiguous_run_is_still_removed(self) -> None:
        other = {
            **QUAEST_12_ROW,
            "passage_id": "other-work-row",
            "work_id": "work-other",
            "canonical_ref": "3.2",
            "text_content": f"Another author quoting: {FIVE_TOKEN_RUN}.",
        }
        out = await _gate(
            # Both anchor tokens hidden from the bounded probe: the rescue
            # pass, not the first-candidate probe, is what decides here.
            _table(QUAEST_12_ROW, other, fillers=_fillers("γινομένων", "δυνατὸν")),
            f"Justin writes {BUNDLE_GREEK} [P1].",
            f"Alexander: «{FIVE_TOKEN_RUN}» [P1].",
        )
        assert FIVE_TOKEN_RUN not in out.answer
        assert out.citations == []
        meta = out.metadata["text_verification"]
        assert meta["attested_spans"] == []
        (span,) = meta["unverified_spans"]
        assert span["reason"] == REASON_AMBIGUOUS_LOCUS
        assert len(span["loci"]) == 2

    @pytest.mark.asyncio
    async def test_origen_sentence_follows_the_quotation_rules(self) -> None:
        """The production span attached to De principiis is Contra Celsum,
        verbatim, in two records of one work under different reference
        labels: twelve tokens, quotation-shaped, several loci → removed as
        ``ambiguous-locus``. Neither policy touches it."""
        rows = _table(*CONTRA_CELSUM_ROWS, fillers=_fillers("θεσπίσαντα", "διδόντες"))
        out = await _gate(
            rows,
            f"Justin writes {BUNDLE_GREEK} [P1].",
            f"Origen: «{ORIGEN_SENTENCE}, …» [P1].",
        )
        assert ORIGEN_SENTENCE not in out.answer
        assert out.citations == []
        meta = out.metadata["text_verification"]
        assert meta["attested_spans"] == []
        (span,) = meta["unverified_spans"]
        assert span["reason"] == REASON_AMBIGUOUS_LOCUS
        assert len(span["loci"]) == 2


# ── D. Downstream contract ───────────────────────────────────────────────────


class TestDownstreamContract:
    @pytest.mark.asyncio
    async def test_kept_spans_do_not_shift_later_removals(self) -> None:
        db = FakeCorpusDb(_table(*KAI_ME_GENESTHAI_ROWS, fillers=_fillers("γενέσθαι")))
        text = "\n".join(
            [
                f"Formula: {SHORT_PHRASE_5}, he says.",
                f"Origen wrote {FOREIGN_GREEK}.",
                "Closing remark.",
            ]
        )
        result = await verify_ancient_text(text, db)
        assert len(result.unverified_spans) == 2
        rescued = await reattribute_unverified_spans(
            text, result, db, schema="free_will"
        )
        assert rescued.text == text
        assert rescued.citations == []
        assert [s.text for s in result.unverified_spans] == [FOREIGN_GREEK]
        lines = enforce_answer(rescued.text, result).split("\n")
        assert lines[0] == f"Formula: {SHORT_PHRASE_5}, he says."
        assert lines[1] == "*[removed: unverified ancient text]*"
        assert lines[2] == "Closing remark."

    @pytest.mark.asyncio
    async def test_report_only_mode_leaves_prose_and_policies_alone(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("ELEUTHERIA_TEXT_VERIFIER_ENFORCE", "false")
        text = f"Three terms ({TERM_LIST_1})."
        out = await _gate(_table(HEXIS_ROW, PHYSIS_ROW, PSYCHE_ROW), text)
        assert out.answer == text
        meta = out.metadata["text_verification"]
        assert meta["enforced"] is False
        assert meta["unverified"] == 1  # reported, not rescued, not removed
        assert meta["attested_spans"] == []

    def test_publication_gate_does_not_block_on_kept_spans(self) -> None:
        metadata = _publication_metadata()
        metadata["text_verification"] = {
            "verified": 2,
            "unverified": 0,
            "enforced": True,
            "attested_spans": [
                {
                    "text": TERM_LIST_1,
                    "language": "greek",
                    "status": STATUS_TERM_LIST,
                    "reason": REASON_TERM_LIST_ATTESTED,
                    "items": ["ἕξις", "φύσις", "ψυχή"],
                },
                {
                    "text": SHORT_PHRASE_5,
                    "language": "greek",
                    "status": STATUS_SHORT_PHRASE,
                    "reason": REASON_SHORT_PHRASE_ATTESTED,
                    "loci_count": 6,
                },
            ],
        }
        decision = evaluate_publication(metadata)
        assert decision.publishable is True
        assert "unverified_ancient_text_present" not in decision.reasons
