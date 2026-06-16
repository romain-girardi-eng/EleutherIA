"""F6 (observability) + F7 (smoke metrics) regression tests.

F6: prod drops INFO logs, so the ``ControversyMap assembled: …`` line was
invisible live and grounding could not be debugged. ``_build_scholar_diagnostics``
packs the same signals (frames, author histogram, quotable-Greek count, synthesis
model, fallback/hedge flags, ancient count) into ``state.metadata`` so they ride
onto the SSE ``complete.metadata`` without changing the prod log level.

F7: the Cloudflare tunnel cuts long external SSE streams, so CI cannot E2E-test
the answer path. ``_smoke_metrics`` reduces one canned-query result to pass/fail
metrics callable in-process.
"""

from __future__ import annotations

from eleutheria_graphrag.agents.scholarly_agent import _build_scholar_diagnostics
from eleutheria_graphrag.agents.state import (
    ControversyFrame,
    ControversyMap,
    PassageRef,
    RAGState,
)
from eleutheria_graphrag.api.routes import _smoke_metrics


def _state_with_map() -> RAGState:
    state = RAGState(question="Did Epictetus think freedom is up to us?")
    state.controversy_map = ControversyMap(
        frames=[
            ControversyFrame(
                frame_id="f1",
                contested_passages=[
                    PassageRef(
                        passage_id="p1",
                        author="Epictetus",
                        original_text="ἐφ' ἡμῖν ἐστι …",  # quotable Greek
                    ),
                    PassageRef(
                        passage_id="p2",
                        author="Epictetus",
                        original_text="no greek metadata block",
                    ),
                    PassageRef(
                        passage_id="p3",
                        author="Chrysippus",
                        original_text="συγκατάθεσις",
                    ),
                ],
            )
        ]
    )
    return state


# ---------- F6: structured diagnostics ----------


def test_diagnostics_counts_frames_authors_and_greek() -> None:
    state = _state_with_map()
    state.metadata["scholar_synthesis"] = {
        "status": "ok",
        "model_used": "accounts/fireworks/models/deepseek-v4-pro",
    }
    diag = _build_scholar_diagnostics(state)
    assert diag["frames"] == 1
    assert diag["author_histogram"] == {"Epictetus": 2, "Chrysippus": 1}
    assert diag["passages_with_quotable_greek"] == 2
    assert diag["ancient_sources"] == 3
    assert diag["synthesis_model_used"].endswith("deepseek-v4-pro")
    assert diag["kimi_fallback_fired"] is False
    assert diag["deterministic_hedge_fired"] is False


def test_diagnostics_dedupes_passage_shared_across_frames() -> None:
    state = RAGState(question="q")
    shared = PassageRef(passage_id="p1", author="Plato", original_text="ψυχή")
    state.controversy_map = ControversyMap(
        frames=[
            ControversyFrame(frame_id="a", contested_passages=[shared]),
            ControversyFrame(frame_id="b", contested_passages=[shared]),
        ]
    )
    diag = _build_scholar_diagnostics(state)
    # One physical passage shared by two frames is ONE primary source.
    assert diag["ancient_sources"] == 1
    assert diag["author_histogram"] == {"Plato": 1}


def test_diagnostics_flags_kimi_fallback_and_deterministic_hedge() -> None:
    state = _state_with_map()
    state.metadata["scholar_synthesis"] = {
        "status": "deterministic_map",
        "model_used": "accounts/fireworks/models/kimi-k2p7-code",
    }
    diag = _build_scholar_diagnostics(state)
    assert diag["kimi_fallback_fired"] is True
    assert diag["deterministic_hedge_fired"] is True


def test_diagnostics_handles_no_map_without_crashing() -> None:
    state = RAGState(question="q")  # controversy_map is None (flag OFF)
    diag = _build_scholar_diagnostics(state)
    assert diag["frames"] == 0
    assert diag["ancient_sources"] == 0
    assert diag["author_histogram"] == {}
    assert "error" not in diag


# ---------- F7: smoke metrics ----------


def test_smoke_metrics_pass_when_grounded() -> None:
    result = {
        "answer": "x" * 300,
        "citations": [
            {"label": "Epictetus, Diss. 1.1", "layer": "primary"},
            {"label": "Bobzien 1998", "layer": "secondary"},
        ],
        "metadata": {
            "scholar_diagnostics": {
                "passages_with_quotable_greek": 2,
                "ancient_sources": 3,
            }
        },
    }
    m = _smoke_metrics(result, elapsed_s=12.34)
    assert m["non_empty"] is True
    assert m["greek"] == 2
    assert m["ancient"] == 3
    assert m["leaked_ids"] == 0
    assert m["elapsed_s"] == 12.34
    assert m["pass"] is True


def test_smoke_metrics_fail_on_leaked_id() -> None:
    result = {
        "answer": "x" * 300,
        "citations": [
            {"label": "person_epictetus_1c_ce", "layer": "primary"},
        ],
        "metadata": {
            "scholar_diagnostics": {
                "passages_with_quotable_greek": 1,
                "ancient_sources": 1,
            }
        },
    }
    m = _smoke_metrics(result, elapsed_s=1.0)
    assert m["leaked_ids"] == 1
    assert m["pass"] is False


def test_smoke_metrics_fail_on_empty_answer() -> None:
    m = _smoke_metrics({"answer": "", "citations": []}, elapsed_s=0.5)
    assert m["non_empty"] is False
    assert m["pass"] is False


def test_smoke_metrics_greek_falls_back_to_citation_labels() -> None:
    # No diagnostics -> scan citation labels for polytonic Greek + count
    # non-secondary citations as ancient.
    result = {
        "answer": "x" * 300,
        "citations": [
            {"label": "Epictetus ἐφ' ἡμῖν", "layer": "primary"},
        ],
    }
    m = _smoke_metrics(result, elapsed_s=2.0)
    assert m["greek"] == 1
    assert m["ancient"] == 1
    assert m["pass"] is True
