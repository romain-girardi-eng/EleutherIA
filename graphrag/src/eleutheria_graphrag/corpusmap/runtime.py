"""Runtime wiring of the CorpusMap layer into the agent loop.

Gated by ``ELEUTHERIA_CORPUSMAP`` (default OFF, so the default pipeline is
unchanged). When on:

* ``search_entity_pages`` / ``read_entity_page`` join the tool registry;
* the native loop's opening message carries CorpusMap candidates (ids and
  titles only) for multi-document query types.

Candidates are withheld for ``specific_entity`` questions: in the 2026-10-05
agentic A/B (data/eval/corpusmap_ab/REPORT.md) the candidate block doubled the
input tokens of short single-passage trajectories without improving them,
while multi-hop thesis questions gained quality at −32% tokens.
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any

from eleutheria_graphrag.corpusmap.builder import (
    CorpusMap,
    build_corpus_map_from_rows,
    load_corpus,
)
from eleutheria_graphrag.corpusmap.candidates import select_candidates

logger = logging.getLogger(__name__)

CANDIDATE_QUERY_TYPES = frozenset(
    {"multi_hop", "comparative", "global_abstract", "temporal"}
)
_DEFAULT_CORPUS_DIR = Path(__file__).resolve().parents[4] / "data" / "corpus"

_lock = threading.Lock()
_cache: dict[int, CorpusMap] = {}


def corpusmap_enabled() -> bool:
    return os.getenv("ELEUTHERIA_CORPUSMAP", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _corpus_dir() -> Path | None:
    raw = os.getenv("ELEUTHERIA_CORPUS_DIR")
    path = Path(raw) if raw else _DEFAULT_CORPUS_DIR
    return path if (path / "passages.jsonl").exists() else None


def get_corpus_map(deps: Any) -> CorpusMap | None:
    """Build (once per loaded KG) and return the CorpusMap, or None if no KG is loaded."""
    kg = getattr(deps, "kg_data", None) or {}
    nodes, edges = kg.get("nodes"), kg.get("edges")
    if not nodes or edges is None:
        return None
    key = id(nodes)
    with _lock:
        if key not in _cache:
            passages, manifest, citations = load_corpus(_corpus_dir())
            _cache.clear()  # one live KG at a time
            _cache[key] = build_corpus_map_from_rows(
                nodes, edges, passages, manifest, citations
            )
            logger.info(
                "CorpusMap built: %d entity pages over %d documents",
                len(_cache[key].pages),
                len(_cache[key].docs),
            )
        return _cache[key]


def _query_type_value(state: Any) -> str:
    qt = getattr(state, "query_type", None)
    return str(getattr(qt, "value", qt) or "")


def corpusmap_candidate_context(
    deps: Any, state: Any, n_pages: int = 5, n_docs: int = 10
) -> str:
    """Opening-message candidate block, or "" when disabled / not a multi-document query. Never raises."""
    if not corpusmap_enabled() or _query_type_value(state) not in CANDIDATE_QUERY_TYPES:
        return ""
    try:
        cmap = get_corpus_map(deps)
        if cmap is None:
            return ""
        cand = select_candidates(cmap, state.question, n_pages=n_pages, n_docs=n_docs)
        return (
            cand.render()
            + "\nRead an entity page with read_entity_page to see source-attributed facts and the "
            "documents behind them; open a document with get_node_detail or read_passages."
        )
    except Exception:  # the map is an accelerator, never a point of failure
        logger.warning("CorpusMap candidate selection failed", exc_info=True)
        return ""
