#!/usr/bin/env python3
"""Audited payload and deterministic selectors for the 2026-08-17 data repairs.

The large populations are deliberately derived from the live JSONL rows.  In
particular, the Fédou quarantine is selected by author plus the demonstrable
title/abstract span mismatch; there is no hard-coded list or target count.

Plotinus records reuse the already-reviewed byte-anchored payload in
``data_2026_08_17_plotinus_remap.py``.  The Galen records are the only small
static adjudication payload: all three descriptions are pinned by SHA-256 and
by their opening words in *De naturalibus facultatibus* books 1-3.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from data_2026_08_17_linguistic_repairs import (
    THEOPHRASTUS_MISFILED_CORPUS_IDS,
    THEOPHRASTUS_MISFILED_NODES,
)
from data_2026_08_17_plotinus_remap import (
    PLOTINUS_REMAP_RECORDS,
)
from data_2026_08_17_plotinus_remap import (
    RECORD_COUNT as PLOTINUS_RECORD_COUNT,
)
from data_2026_08_17_plotinus_remap import (
    check_payload as check_plotinus_payload,
)

ROOT = Path(__file__).resolve().parent.parent
STAMP = "cold_audit_data_repairs_2026_08_17"
BACKUP_SUFFIX = ".bak-cold_audit_data_repairs_2026_08_17"

SYTSMA_DUPLICATE_ID = (
    "pub_sytsma_2018_reconciling_universal_salvation_and_freedom_of_choice_"
    "in_origen"
)
SYTSMA_CANONICAL_ID = "pub_sytsma_2020_universal_salvation_origen"
SYTSMA_ORIGENALITY_ID = "OR04b4c9130080"

SIMPLICIUS_WORK_ID = "work_simplicius_in_enchiridion"
SIMPLICIUS_CANONICAL_URN = "urn:cts:greekLit:tlg4013.tlg001"
SIMPLICIUS_STALE_URN = "urn:cts:greekLit:tlg0093.tlg001"

GALEN_OLD_WORK_ID = "work_galen_de_placitis"
GALEN_NEW_WORK_ID = "work_galen_de_naturalibus_facultatibus"
GALEN_DE_PLACITIS_URN = "urn:cts:greekLit:tlg0057.tlg032"
GALEN_NATURAL_FACULTIES_URN = "urn:cts:greekLit:tlg0057.tlg010"
GALEN_PRIMARY_SOURCE = (
    "OpenGreekAndLatin First1KGreek, "
    "data/tlg0057/tlg010/tlg0057.tlg010.1st1K-grc1.xml"
)

GALEN_PASSAGES: tuple[dict[str, Any], ...] = (
    {
        "node_id": "passage_galen_plac_1",
        "passage_id": "429f228e-9268-4d9b-96a9-5676f54d07a0",
        "book": 1,
        "chapters": "1.1-1.17",
        "description_sha256": (
            "c444f282f07b719419e35487a49d12e6dff934c4e670e32eebe8b4c4a1d17176"
        ),
        "corpus_text_sha256": (
            "0c85bc52188b43f468b98f252d47b7783b9c009c5053326ce8c3c5199a5df639"
        ),
        "opening": "Ἐπειδὴ τὸ μὲν αἰσθάνεσθαί τε καὶ κινεῖσθαι",
    },
    {
        "node_id": "passage_galen_plac_2",
        "passage_id": "ced253e3-7ffc-46e2-a75b-90c1ca8bca71",
        "book": 2,
        "chapters": "2.1-2.9",
        "description_sha256": (
            "686ad6e59991c3818aa019e8e7a374fc2d87c3c3a737ac57df55417a5a135fac"
        ),
        "corpus_text_sha256": (
            "1b69f28be44b27f6aa257bcf11f758037975887d2fa8763b8b08fd74fa9ffeee"
        ),
        "opening": "Ὅτι μὲν οὖν ἀναγκαῖόν ἐστιν οὐκ Ἐρασιστράτῳ",
    },
    {
        "node_id": "passage_galen_plac_3",
        "passage_id": "9f86c8e0-af5d-46db-ac08-dfb8a0accb2c",
        "book": 3,
        "chapters": "3.1-3.15",
        "description_sha256": (
            "fd9acce404da89a12b1a6fbd53f99b42b5816ff06fe774f3c133538d7756afc7"
        ),
        "corpus_text_sha256": (
            "eb2ff1a74690293e177edf73a437adf4b822b5e5b292ae971f009fdaa85a57f7"
        ),
        "opening": "Ὅτι μὲν οὖν, ἡ θρέψις ἀλλοιουμένου τε",
    },
)

METHODIUS_BAD_PASSAGE_URN = (
    "urn:cts:greekLit:tlg0338.tlg307.perseus-grc1:1.1"
)
METHODIUS_WORK_URN = "urn:cts:greekLit:tlg2959.tlg002"
METHODIUS_OLD_WORK_ID = "urn_cts_greeklit_tlg2959_tlg001_grc"
METHODIUS_NEW_WORK_ID = "urn_cts_greeklit_tlg2959_tlg002_grc"
METHODIUS_SPAN_PREFIX = "gcs27:methodius-de-autexousio:pg18."
METHODIUS_REF = re.compile(r"^PG 18\.(\d+)$")

FEDOU_PRAYER_MARKERS = (
    "traite sur la priere d origene",
    "tratado sobre la oracion de origenes",
)


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def set_metadata(node: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(value, ensure_ascii=False)
    else:
        node["metadata"] = value


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fold(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.casefold()).split())


def derive_fedou_contamination(
    nodes: list[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Return only records whose Fédou title and prayer abstract cannot match."""
    records: list[dict[str, Any]] = []
    for node in nodes:
        data = metadata(node)
        if data.get("citation_verdict") != "bibliographic_import":
            continue
        if fold(data.get("author")) != "michel fedou":
            continue
        description = fold(node.get("description"))
        marker = next(
            (item for item in FEDOU_PRAYER_MARKERS if item in description), None
        )
        if marker is None:
            continue
        title = fold(data.get("title") or node.get("label"))
        if any(item in title for item in FEDOU_PRAYER_MARKERS):
            continue
        records.append(
            {
                "node_id": node_id(node),
                "description_sha256": sha256_text(node.get("description") or ""),
                "title": data.get("title") or node.get("label"),
                "abstract_marker": marker,
                "reason": (
                    "Michel Fédou bulletin row: abstract describes Origen's "
                    "De oratione while the row title names another item"
                ),
            }
        )
    return tuple(sorted(records, key=lambda record: record["node_id"]))


def methodius_source_span_id(canonical_ref: str) -> str:
    match = METHODIUS_REF.fullmatch(canonical_ref)
    if not match:
        raise ValueError(f"not a Methodius PG 18 span: {canonical_ref!r}")
    return f"{METHODIUS_SPAN_PREFIX}{int(match.group(1)):03d}"


def derive_methodius_spans(
    passages: list[dict[str, Any]], nodes: list[dict[str, Any]]
) -> tuple[dict[str, Any], ...]:
    """Derive the 97 source rows and their one-to-one KG mirror nodes."""
    twins: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        data = metadata(node)
        passage_id = data.get("db_passage_id")
        if passage_id:
            twins.setdefault(str(passage_id), []).append(node)

    records: list[dict[str, Any]] = []
    for passage in passages:
        canonical_ref = str(passage.get("canonical_ref") or "")
        span_id = passage.get("source_span_id")
        is_before = passage.get("cts_urn") == METHODIUS_BAD_PASSAGE_URN
        is_after = (
            passage.get("cts_urn") == METHODIUS_WORK_URN
            and isinstance(span_id, str)
            and span_id.startswith(METHODIUS_SPAN_PREFIX)
        )
        if not (is_before or is_after) or not METHODIUS_REF.fullmatch(canonical_ref):
            continue
        passage_id = str(passage.get("passage_id") or "")
        candidates = [
            node
            for node in twins.get(passage_id, [])
            if node_id(node).startswith("passage_meth_dla_")
        ]
        if len(candidates) != 1:
            raise ValueError(
                f"Methodius passage {passage_id} has {len(candidates)} KG twins"
            )
        node = candidates[0]
        records.append(
            {
                "passage_id": passage_id,
                "node_id": node_id(node),
                "canonical_ref": canonical_ref,
                "source_span_id": methodius_source_span_id(canonical_ref),
                "passage_text_sha256": sha256_text(
                    str(passage.get("text_content") or "")
                ),
                "node_description_sha256": sha256_text(
                    str(node.get("description") or "")
                ),
            }
        )
    return tuple(sorted(records, key=lambda record: record["source_span_id"]))


def check_payload() -> None:
    check_plotinus_payload()
    if len(PLOTINUS_REMAP_RECORDS) != PLOTINUS_RECORD_COUNT:
        raise ValueError("Plotinus byte-anchor payload is incomplete")
    if len({record["node_id"] for record in GALEN_PASSAGES}) != len(GALEN_PASSAGES):
        raise ValueError("duplicate Galen node id in payload")
    if len({record["passage_id"] for record in GALEN_PASSAGES}) != len(
        GALEN_PASSAGES
    ):
        raise ValueError("duplicate Galen corpus passage id in payload")
    if set(THEOPHRASTUS_MISFILED_NODES) != {
        f"passage_simpl_in_ench_{index}" for index in range(1, 10)
    }:
        raise ValueError("Theophrastus removal evidence changed")
    if len(THEOPHRASTUS_MISFILED_CORPUS_IDS) != len(
        THEOPHRASTUS_MISFILED_NODES
    ):
        raise ValueError("Theophrastus node/corpus evidence is incomplete")


if __name__ == "__main__":
    check_payload()
    print(f"Plotinus byte-anchored records: {len(PLOTINUS_REMAP_RECORDS)}")
    print(f"Galen adjudicated books: {len(GALEN_PASSAGES)}")
    print("payload: OK")
