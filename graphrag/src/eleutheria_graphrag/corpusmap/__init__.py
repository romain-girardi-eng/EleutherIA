"""CorpusMap: an entity-centric navigation layer over the KG snapshot.

Implements the Rendering stage of Jeong et al. 2026, "Follow the Entities:
A Corpus Map for Agentic Search" (arXiv:2609.37226). The Cataloging,
Extraction and Resolution stages of the paper are already done by the
curated KG: its person / concept / work / school / debate nodes are the
resolved cross-document entities, and arguments, syntheses, publications
and passages are the documents they link.
"""

from eleutheria_graphrag.corpusmap.builder import (
    CorpusMap,
    EntityPage,
    build_corpus_map,
)
from eleutheria_graphrag.corpusmap.candidates import select_candidates

__all__ = ["CorpusMap", "EntityPage", "build_corpus_map", "select_candidates"]
