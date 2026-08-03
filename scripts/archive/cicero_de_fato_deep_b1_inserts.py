"""Cicero De Fato deep B1 — NEW_INSERTS list.

This batch adds NO new nodes — Cicero's De Fato is already fully covered in the
KG (144 passages : passage_cic_fat_1..48 + passage_cicero_fat_1..48 +
passage_cicero_fat_1..48_en). All scholar nodes already exist as well.

The module is kept for parity with the amand_b9 / bobzien_2001_b1 layout so the
orchestrator can `from cicero_de_fato_deep_b1_inserts import NEW_*` without
conditional imports.
"""
from __future__ import annotations

from typing import Any

NEW_PERSONS: list[dict[str, Any]] = []
NEW_WORKS: list[dict[str, Any]] = []
NEW_CONCEPTS: list[dict[str, Any]] = []
NEW_SYNTHESES: list[dict[str, Any]] = []
NEW_ARGUMENTS: list[dict[str, Any]] = []
