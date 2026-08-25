"""Regression tests for the 2026-08-26 Augustine quotation repair.

`synthesis_aug_foreknowledge` presented three Latin strings inside quotation
marks at precise loci. Two occurred nowhere in the corpus; the third was an
altered quotation. The node was flagged `citation_verified: true` throughout —
its own `latin_verdict: "false_positive"` was overridden by that flag.

These tests exist so a future ingestion cannot quietly put unattested Latin
back inside quotation marks in this node.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.apply_2026_08_26_aug_foreknowledge_quotations import (
    MUST_BE_ABSENT,
    check_corpus_evidence,
    metadata,
    node_id,
    read_jsonl,
    transform,
)
from scripts.data_2026_08_26_aug_foreknowledge_quotations import (
    NODE_ID,
    TRANSMITTED_MEMORY_QUOTE,
    WORK,
)

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "data/kg/nodes.jsonl"
PASSAGES = ROOT / "data/corpus/passages.jsonl"


def load_node() -> dict:
    for line in NODES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        node = json.loads(line)
        if (node.get("id") or node.get("node_id")) == NODE_ID:
            return node
    raise AssertionError(f"{NODE_ID} not found")


def test_no_unattested_latin_remains_in_quotation_marks() -> None:
    description = load_node()["description"]
    for needle in MUST_BE_ABSENT:
        assert needle not in description, needle


def test_the_memory_analogy_is_the_transmitted_wording() -> None:
    description = load_node()["description"]
    # The node used to drop `enim` and swap the semicolon for a comma.
    assert TRANSMITTED_MEMORY_QUOTE.rstrip(".") in description
    assert "sicut tu memoria tua non cogis" not in description


def test_every_quoted_latin_string_is_attested_in_the_corpus() -> None:
    """The point of the whole repair, asserted directly.

    Any run of Latin inside double quotes in this node must occur verbatim in
    the transmitted text of De libero arbitrio.
    """
    import re

    description = load_node()["description"]
    rows = [
        (r.get("text_content") or "")
        for r in read_jsonl(PASSAGES)
        if r.get("work_canonical_id") == WORK
    ]
    corpus = "\n".join(rows)
    quoted = re.findall(r'"([^"]{12,})"', description)
    assert quoted, "expected the node to still carry quotations"
    for candidate in quoted:
        assert candidate.rstrip(".") in corpus, candidate


def test_the_unsupported_locus_was_removed_not_re_sourced() -> None:
    # 3.5.14 is the analogy of the round nut and the sinless angels; it does
    # not contain the distinction the node claimed. The claim was deleted
    # rather than re-attached to some other passage that would fit.
    description = load_node()["description"]
    assert "3.5.14" not in description


def test_metadata_no_longer_certifies_the_breach() -> None:
    meta = metadata(load_node())
    assert meta.get("citation_verdict") == "corrected"
    assert meta.get("latin_verdict") == "verified"
    assert "quotation_audit_2026_08_26" in meta


def test_corpus_evidence_still_proves_the_repair() -> None:
    assert check_corpus_evidence(read_jsonl(PASSAGES)) == []


def test_repair_is_idempotent() -> None:
    nodes = read_jsonl(NODES)
    once, changed = transform(nodes)
    assert changed is False
    assert [node_id(n) for n in once] == [node_id(n) for n in nodes]
