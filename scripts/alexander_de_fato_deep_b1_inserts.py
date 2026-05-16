"""Alexander De Fato deep-anchor batch B1 — no new node shells.

The 78 existing `passage_alex_fat_<n>` nodes already cover all 39 chapters of
De Fato (Greek + English). The 12 scholar nodes targeted by this batch already
exist. Therefore this batch only adds metadata updates (see
`alexander_de_fato_deep_b1_data.UPDATES`) and edges
(`alexander_de_fato_deep_b1_edges.NEW_EDGES`).
"""
from __future__ import annotations

from typing import Any

NEW_PASSAGES: list[dict[str, Any]] = []
NEW_ARGUMENTS: list[dict[str, Any]] = []
NEW_PERSONS: list[dict[str, Any]] = []
NEW_WORKS: list[dict[str, Any]] = []
NEW_CONCEPTS: list[dict[str, Any]] = []
NEW_SYNTHESES: list[dict[str, Any]] = []
