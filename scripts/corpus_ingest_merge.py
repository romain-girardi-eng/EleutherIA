"""Compute which fetched passages are new to a work (dedup by CTS URN).

Full-work coverage is achieved by ADDING missing passages only; existing
(possibly cited) passages are never modified. Empty/whitespace text is skipped —
we never fabricate or store blank ancient text.
"""
from __future__ import annotations


def passages_to_insert(
    existing: list[dict],
    fetched: list[dict],
    work_canonical_id: str,
    start_seq: int,
) -> list[dict]:
    have = {p.get("cts_urn") for p in existing}
    out: list[dict] = []
    seq = start_seq
    for f in fetched:
        urn = f.get("cts_urn")
        text = (f.get("text_content") or "").strip()
        if not urn or urn in have or not text:
            continue
        have.add(urn)
        out.append({
            "work_canonical_id": work_canonical_id,
            "cts_urn": urn,
            "canonical_ref": urn.split(":")[-1] if ":" in urn else urn,
            "sequence_number": seq,
            "text_content": f.get("text_content"),
        })
        seq += 1
    return out
