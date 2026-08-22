#!/usr/bin/env python3
"""Audited data for the Plutarch tlg135/tlg138 work split.

This module is deliberately read-only.  It records the exact six passages,
their current graph edges, and the independent source evidence which proves
that ``tlg0007.tlg135`` is *Epitome libri de animae procreatione in Timaeo*,
not another edition of *De communibus notitiis adversus Stoicos*.

Run it before the applier to re-check the repository and, when available, the
local TLG E authority files::

    .venv/bin/python scripts/data_2026_08_18_plutarch_split.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TLGE = Path(os.environ.get("TLGE_DIR", "~/Desktop/Romain/TLGE")).expanduser()

WAVE = "plutarch_work_split_2026_08_18"
STAMP_DATE = "2026-08-18"

OLD_WORK_ID = "work_plutarch_de_communibus_notitiis"
NEW_WORK_ID = "work_plutarch_epitome_animae_procreatione_timaeo"
AUTHOR_ID = "person_plutarch_45_120ce_b9c2a8f3"
AUTHOR_NAME = "Plutarch"

TLG135_WORK_URN = "urn:cts:greekLit:tlg0007.tlg135"
TLG135_EDITION_URN = f"{TLG135_WORK_URN}.perseus-grc2"
TLG135_CORPUS_ID = "urn_cts_greeklit_tlg0007_tlg135_grc"
TLG135_TITLE = "Epitome libri de animae procreatione in Timaeo"
TLG135_GREEK_TITLE = "Ἐπιτομὴ τοῦ περὶ τῆς ἐν τῷ Τιμαίῳ ψυχογονίας"
TLG135_MORALIA_LOCUS = "1030d-1032f"

TLG138_WORK_URN = "urn:cts:greekLit:tlg0007.tlg138"
TLG138_EDITION_URN = f"{TLG138_WORK_URN}.perseus-grc2"
TLG138_CORPUS_ID = "urn_cts_greeklit_tlg0007_tlg138_grc"
TLG138_TITLE = "De communibus notitiis adversus Stoicos"
TLG138_GREEK_TITLE = "Περὶ τῶν κοινῶν ἐννοιῶν πρὸς τοὺς Στωικοὺς"
TLG138_MORALIA_LOCUS = "1058e-1086b"

OLD_TLG135_TITLE = "De Communibus Notitiis adversus Stoicos"
NEW_WORK_LABEL = f"Plutarch, {TLG135_TITLE}"
NEW_AUTHORSHIP_EDGE_ID = "c18e0331-02d4-583b-a077-a10af1f2767e"

PERSEUS_COMMIT = "d07c21b26a14bb945b5291ecd34ee3e45f55a7b3"
PERSEUS_ROOT = (
    f"https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/{PERSEUS_COMMIT}"
)
PERSEUS_FILES = {
    "tlg135_catalogue": {
        "path": "data/tlg0007/tlg135/__cts__.xml",
        "sha256": "d1e5b5437c45208e7c4579bb1a5a30526dd7acb78d64e58b783fbb4d25b30f51",
    },
    "tlg135_tei": {
        "path": "data/tlg0007/tlg135/tlg0007.tlg135.perseus-grc2.xml",
        "sha256": "508c470409a7e17c36d664d443f6b9b4ff924c06099a65c6e7ad59de482f3283",
    },
    "tlg138_catalogue": {
        "path": "data/tlg0007/tlg138/__cts__.xml",
        "sha256": "3369386da92e844bc9e8fa22aeebfde9f3a04fc8b0bff6e0d5334157b0ed6cbe",
    },
    "tlg138_tei": {
        "path": "data/tlg0007/tlg138/tlg0007.tlg138.perseus-grc2.xml",
        "sha256": "ad18f6e88956f0c991891fb5fbb27384683ea6ab13202c2a492d7185d6f5e689",
    },
}
for _source in PERSEUS_FILES.values():
    _source["url"] = f"{PERSEUS_ROOT}/{_source['path']}"

TLGE_IDT_SHA256 = "c07ad80734df042f6f9d361a17cb984550871c7f306721d26691058a45712d22"
TLGE_TXT_SHA256 = "d868b60d4bd911ee6b32c2309fe49935a19bf9184d6c9ff4671b3d52cb29891d"
TLGE_IDT_NEIGHBOURS = {
    "134": "De animae procreatione in Timaeo (1012b-1030c)",
    "135": "Epitome libri de animae procreatione in Timaeo (1030d-1032f)",
    "136": "De Stoicorum repugnantiis (1033a-1057b)",
    "137": "Stoicos absurdiora poetis dicere (1057c-1058e)",
    "138": "De communibus notitiis adversus Stoicos (1058e-1086b)",
}
TLGE_TEXT_PROBES = {
    b"*E*P*I*T*O*M*H *T*O*U *P*E*R*I *T*H*S *E*N *T*W*I": 7_961_190,
    b"LE/GEI DE\\ TH\\N U(/LHN DIAMORFWQH=NAI": 7_961_635,
    b"*P*E*R*I *T*W*N *K*O*I*N*W*N": 8_071_619,
    b"SOI\\ ME\\N EI)KO/S, W)= *DIADOU/MENE": 8_071_739,
}

PASSAGES: tuple[dict[str, Any], ...] = (
    {
        "sequence": 1,
        "node_id": "passage_plut_cn_1",
        "passage_id": "c0460502-4859-4a25-ad61-3e7723937953",
        "part_of_edge_id": "182f9a45-1b5d-4630-9950-0810a1e4f47c",
        "text_sha256": "2809d014bc92feb62390617f459277c10c2f36ea2add57ecd619042be192e467",
        "kg_text_sha256": "2809d014bc92feb62390617f459277c10c2f36ea2add57ecd619042be192e467",
    },
    {
        "sequence": 2,
        "node_id": "passage_plut_cn_2",
        "passage_id": "cbea7bff-8674-4b2a-9e91-2be555ae40c9",
        "part_of_edge_id": "150dd402-a5cc-427c-b026-4bc49e3c1370",
        "text_sha256": "6aa15244b0da2d3532e672d4416a4735f9fd736fd1a8af87fb689474d5560e97",
        "kg_text_sha256": "6aa15244b0da2d3532e672d4416a4735f9fd736fd1a8af87fb689474d5560e97",
    },
    {
        "sequence": 3,
        "node_id": "passage_plut_cn_3",
        "passage_id": "2236e0eb-3fdb-473f-8053-da7a4d2c042d",
        "part_of_edge_id": "071d871c-23a0-44f8-b017-bae375dc70c2",
        "text_sha256": "7cec2e3db932aa2905832553f831d147fbe1bc34ede6a3a38c21713ba42cd229",
        "kg_text_sha256": "b915d6a21e661ddfa5887908d458cc1a7aa0a1a338658a288bcc428f086cd27f",
    },
    {
        "sequence": 4,
        "node_id": "passage_plut_cn_4",
        "passage_id": "1491dca2-426f-486a-9340-e1340ce64110",
        "part_of_edge_id": "fdcbe4a6-4289-48a4-aa9d-481368784f23",
        "text_sha256": "6b048e70e488b3ca3d24982300115596885dde79e66cbd0575689f945c741806",
        "kg_text_sha256": "8831739a9193dcaa3e9c18e1fd195ae0c397b86e6d14084127011a5d2cf5717a",
    },
    {
        "sequence": 5,
        "node_id": "passage_plut_cn_5",
        "passage_id": "06aa0904-ec48-4d51-a70f-f92548670896",
        "part_of_edge_id": "bf9531cb-0ca9-48d0-8ec1-cfecb4c0b27d",
        "text_sha256": "82ade7eff845211d27ade970cced5aa1ff7917198503f5d83665267d1aefd2f6",
        "kg_text_sha256": "4f2ceff96dd1645c6e9242e707786f593b88c828c0faa22425474c679926e386",
    },
    {
        "sequence": 6,
        "node_id": "passage_plut_cn_6",
        "passage_id": "693256f2-5aa2-4a9e-9cda-6fc00136963a",
        "part_of_edge_id": "abcb4124-bc15-4817-b7d9-5b55a74946e8",
        "text_sha256": "decb9e76e0427420bbe1cf085445f4badcdd51790af97b9bb2595ae5af94ace5",
        "kg_text_sha256": "698a1d2fbd18163b7ee5873dc7581bbc47b429f9d03cb141ad8fbf42358025df",
    },
)

EXPECTED_ALLOWLIST_ENTRY = {
    "work_candidates": [TLG138_WORK_URN],
    "child_canonical": TLG135_WORK_URN,
    "reason": (
        "The corpus manifest contains two same-title source families: 6 passages "
        "under tlg0007.tlg135 and 50 under tlg0007.tlg138. The KG work "
        "identifies tlg138 but its six materialized children identify tlg135. "
        "This split requires source-level adjudication, not a mechanical parent "
        "rewrite."
    ),
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def record_id(row: dict[str, Any]) -> str:
    return str(row.get("id") or row.get("node_id") or "")


def metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata") or {}
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError(f"metadata is not an object on {record_id(row)}")
    return value


def _ascii_payload(raw: bytes, start: int, end: int) -> str:
    return bytes(value & 0x7F for value in raw[start:end]).decode("ascii", "replace")


def extract_idt_works(raw: bytes) -> dict[str, str]:
    """Decode the work-id/title fields from a TLG E ``.IDT`` file."""

    works: dict[str, str] = {}
    position = 0
    while True:
        marker = raw.find(b"\xef\x81", position)
        if marker < 0:
            break
        end = raw.find(b"\xff", marker + 2)
        if end < 0:
            break
        work_id = _ascii_payload(raw, marker + 2, end)
        title_marker = raw.find(b"\x10\x01", end + 1, min(len(raw), end + 32))
        if title_marker >= 0 and work_id.isdigit() and len(work_id) == 3:
            title_length = raw[title_marker + 2]
            title_start = title_marker + 3
            title_end = title_start + title_length
            if title_end <= len(raw):
                works[work_id] = raw[title_start:title_end].decode("ascii", "replace")
        position = end + 1
    return works


def verify_local_tlge(tlge_dir: Path = DEFAULT_TLGE) -> dict[str, Any]:
    """Verify the independent TLG E catalogue and text witnesses exactly."""

    idt_path = tlge_dir / "TLG0007.IDT"
    txt_path = tlge_dir / "TLG0007.TXT"
    if not idt_path.is_file() or not txt_path.is_file():
        raise ValueError(f"missing local TLG E authority: {idt_path} / {txt_path}")

    idt_raw = idt_path.read_bytes()
    txt_raw = txt_path.read_bytes()
    observed_idt_hash = sha256_bytes(idt_raw)
    observed_txt_hash = sha256_bytes(txt_raw)
    if observed_idt_hash != TLGE_IDT_SHA256:
        raise ValueError(
            f"TLG0007.IDT hash drift: {observed_idt_hash} != {TLGE_IDT_SHA256}"
        )
    if observed_txt_hash != TLGE_TXT_SHA256:
        raise ValueError(
            f"TLG0007.TXT hash drift: {observed_txt_hash} != {TLGE_TXT_SHA256}"
        )

    works = extract_idt_works(idt_raw)
    observed_neighbours = {
        work_id: works.get(work_id) for work_id in TLGE_IDT_NEIGHBOURS
    }
    if observed_neighbours != TLGE_IDT_NEIGHBOURS:
        raise ValueError(
            "TLG0007.IDT work table drift: "
            f"{observed_neighbours!r} != {TLGE_IDT_NEIGHBOURS!r}"
        )

    observed_offsets = {probe: txt_raw.find(probe) for probe in TLGE_TEXT_PROBES}
    if observed_offsets != TLGE_TEXT_PROBES:
        printable = {
            probe.decode("ascii"): offset for probe, offset in observed_offsets.items()
        }
        raise ValueError(f"TLG0007.TXT probe drift: {printable}")

    return {
        "idt_path": str(idt_path),
        "idt_sha256": observed_idt_hash,
        "txt_path": str(txt_path),
        "txt_sha256": observed_txt_hash,
        "work_table": observed_neighbours,
        "text_offsets": {
            probe.decode("ascii"): offset for probe, offset in observed_offsets.items()
        },
    }


def inspect_repository(root: Path = ROOT) -> dict[str, Any]:
    """Classify the exact repository family as pre-repair or applied."""

    nodes = read_jsonl(root / "data/kg/nodes.jsonl")
    edges = read_jsonl(root / "data/kg/edges.jsonl")
    manifest = read_jsonl(root / "data/corpus/manifest.jsonl")
    passages = read_jsonl(root / "data/corpus/passages.jsonl")
    allowlist = json.loads(
        (root / "data/audit/kg_work_child_canonical_known_ambiguities.json").read_text(
            encoding="utf-8"
        )
    )

    nodes_by_id = {record_id(row): row for row in nodes}
    if len(nodes_by_id) != len(nodes):
        raise ValueError("duplicate KG node ids")
    edges_by_id = {str(row.get("edge_id") or ""): row for row in edges}
    if len(edges_by_id) != len(edges):
        raise ValueError("duplicate KG edge ids")
    passages_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    if len(passages_by_id) != len(passages):
        raise ValueError("duplicate corpus passage ids")

    parent = nodes_by_id.get(OLD_WORK_ID)
    if parent is None or parent.get("type") != "work":
        raise ValueError(f"missing verified tlg138 work node: {OLD_WORK_ID}")
    parent_metadata = metadata(parent)
    if parent_metadata.get("cts_urn") != TLG138_WORK_URN:
        raise ValueError("the tlg138 parent work identity drifted")
    if parent_metadata.get("work_canonical_id") != TLG138_CORPUS_ID:
        raise ValueError("the tlg138 parent corpus identity drifted")

    manifest_families: dict[str, list[dict[str, Any]]] = {
        TLG135_CORPUS_ID: [],
        TLG138_CORPUS_ID: [],
    }
    for row in manifest:
        canonical_id = str(row.get("canonical_id") or "")
        if canonical_id in manifest_families:
            manifest_families[canonical_id].append(row)
    if any(len(rows) != 1 for rows in manifest_families.values()):
        raise ValueError("expected exactly one manifest row for each Plutarch family")
    row135 = manifest_families[TLG135_CORPUS_ID][0]
    row138 = manifest_families[TLG138_CORPUS_ID][0]
    if (row135.get("passages"), row135.get("source")) != (
        6,
        f"scaife:{TLG135_EDITION_URN}",
    ):
        raise ValueError("tlg135 manifest family drifted")
    if (
        row138.get("passages"),
        row138.get("source"),
        row138.get("cts_urn"),
    ) != (50, f"scaife:{TLG138_EDITION_URN}", TLG138_WORK_URN):
        raise ValueError("tlg138 manifest family drifted")

    corpus135 = [
        row for row in passages if row.get("work_canonical_id") == TLG135_CORPUS_ID
    ]
    corpus138 = [
        row for row in passages if row.get("work_canonical_id") == TLG138_CORPUS_ID
    ]
    if len(corpus135) != 6 or len(corpus138) != 50:
        raise ValueError(
            f"Plutarch family counts drifted: tlg135={len(corpus135)}, "
            f"tlg138={len(corpus138)}"
        )
    if [row.get("sequence_number") for row in corpus135] != list(range(1, 7)):
        raise ValueError("tlg135 corpus sequence is not exactly 1-6")
    if [row.get("sequence_number") for row in corpus138] != list(range(1, 51)):
        raise ValueError("tlg138 corpus sequence is not exactly 1-50")
    if {row["text_content"] for row in corpus135} & {
        row["text_content"] for row in corpus138
    }:
        raise ValueError("tlg135/tlg138 corpus families unexpectedly overlap")

    edge_targets: set[str] = set()
    label_states: set[str] = set()
    metadata_states: set[str] = set()
    ref_states: set[str] = set()
    for spec in PASSAGES:
        sequence = spec["sequence"]
        node = nodes_by_id.get(spec["node_id"])
        passage = passages_by_id.get(spec["passage_id"])
        edge = edges_by_id.get(spec["part_of_edge_id"])
        if node is None or node.get("type") != "passage":
            raise ValueError(f"missing passage node: {spec['node_id']}")
        if passage is None or edge is None:
            raise ValueError(f"missing corpus/edge twin for {spec['node_id']}")
        node_metadata = metadata(node)
        if node_metadata.get("db_passage_id") != spec["passage_id"]:
            raise ValueError(f"db passage id drift on {spec['node_id']}")
        if node_metadata.get("cts_urn") != f"{TLG135_EDITION_URN}:{sequence}":
            raise ValueError(f"CTS locus drift on {spec['node_id']}")
        if node_metadata.get("work_canonical_id") != TLG135_WORK_URN:
            raise ValueError(f"work identity drift on {spec['node_id']}")
        if passage.get("cts_urn") != f"{TLG135_EDITION_URN}:{sequence}":
            raise ValueError(f"corpus CTS locus drift on {spec['passage_id']}")
        if sha256_text(str(passage.get("text_content") or "")) != spec["text_sha256"]:
            raise ValueError(f"corpus text drift on {spec['passage_id']}")
        if sha256_text(str(node.get("description") or "")) != spec["kg_text_sha256"]:
            raise ValueError(f"KG text drift on {spec['node_id']}")
        if edge.get("relation") != "part_of" or edge.get("source") != spec["node_id"]:
            raise ValueError(f"part_of edge drift on {spec['part_of_edge_id']}")
        if edge.get("source_id") != spec["node_id"]:
            raise ValueError(f"part_of source_id drift on {spec['part_of_edge_id']}")
        edge_targets.add(str(edge.get("target") or ""))
        if edge.get("target") != edge.get("target_id"):
            raise ValueError(f"unpaired edge target on {spec['part_of_edge_id']}")

        old_label = f"Plutarch, {OLD_TLG135_TITLE}, {sequence}"
        new_label = f"Plutarch, {TLG135_TITLE}, {sequence}"
        if node.get("label") == old_label:
            label_states.add("pre")
        elif node.get("label") == new_label:
            label_states.add("applied")
        else:
            raise ValueError(f"unexpected label on {spec['node_id']}")

        if (
            node_metadata.get("work_title") == OLD_TLG135_TITLE
            and node_metadata.get("canonical_ref") == str(sequence)
            and not node_metadata.get("work_node_id")
        ):
            metadata_states.add("pre")
        elif (
            node_metadata.get("work_title") == TLG135_TITLE
            and node_metadata.get("canonical_ref") == f"{TLG135_TITLE} {sequence}"
            and node_metadata.get("work_node_id") == NEW_WORK_ID
            and node_metadata.get("citation_verified") is True
            and WAVE in node_metadata
        ):
            metadata_states.add("applied")
        else:
            raise ValueError(f"mixed identity metadata on {spec['node_id']}")

        old_ref = f"{OLD_TLG135_TITLE} {sequence}"
        new_ref = f"{TLG135_TITLE} {sequence}"
        if passage.get("canonical_ref") == old_ref:
            ref_states.add("pre")
        elif passage.get("canonical_ref") == new_ref:
            ref_states.add("applied")
        else:
            raise ValueError(f"unexpected corpus ref on {spec['passage_id']}")

    ambiguity = (allowlist.get("known_ambiguities") or {}).get(OLD_WORK_ID)
    new_work_present = NEW_WORK_ID in nodes_by_id
    new_authorship_present = NEW_AUTHORSHIP_EDGE_ID in edges_by_id
    if new_work_present:
        new_work = nodes_by_id[NEW_WORK_ID]
        new_work_metadata = metadata(new_work)
        if (
            new_work.get("type") != "work"
            or new_work.get("label") != NEW_WORK_LABEL
            or new_work_metadata.get("cts_urn") != TLG135_WORK_URN
            or new_work_metadata.get("work_canonical_id") != TLG135_CORPUS_ID
            or new_work_metadata.get("citation_verified") is not True
            or WAVE not in new_work_metadata
        ):
            raise ValueError("new tlg135 work node does not match the adjudication")
    if new_authorship_present:
        authorship = edges_by_id[NEW_AUTHORSHIP_EDGE_ID]
        if (
            authorship.get("relation") != "authored_by"
            or authorship.get("source") != NEW_WORK_ID
            or authorship.get("source_id") != NEW_WORK_ID
            or authorship.get("target") != AUTHOR_ID
            or authorship.get("target_id") != AUTHOR_ID
        ):
            raise ValueError("new tlg135 authorship edge drifted")
    pre = (
        edge_targets == {OLD_WORK_ID}
        and label_states == {"pre"}
        and metadata_states == {"pre"}
        and ref_states == {"pre"}
        and row135.get("title") == OLD_TLG135_TITLE
        and row135.get("cts_urn") == ""
        and ambiguity == EXPECTED_ALLOWLIST_ENTRY
        and not new_work_present
        and not new_authorship_present
    )
    applied = (
        edge_targets == {NEW_WORK_ID}
        and label_states == {"applied"}
        and metadata_states == {"applied"}
        and ref_states == {"applied"}
        and row135.get("title") == TLG135_TITLE
        and row135.get("cts_urn") == TLG135_WORK_URN
        and ambiguity is None
        and new_work_present
        and new_authorship_present
    )
    if pre == applied:
        raise ValueError(
            "mixed or unrecognized Plutarch split state; exact preconditions failed"
        )

    return {
        "state": "pre" if pre else "applied",
        "tlg135_corpus_passages": len(corpus135),
        "tlg138_corpus_passages": len(corpus138),
        "tlg135_part_of_target": next(iter(edge_targets)),
        "manifest_tlg135_title": row135.get("title"),
        "manifest_tlg138_title": row138.get("title"),
        "allowlist_entry_present": ambiguity is not None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--tlge-dir", type=Path, default=DEFAULT_TLGE)
    parser.add_argument(
        "--skip-local-tlge",
        action="store_true",
        help="skip the independent local TLG E hash/catalogue/text check",
    )
    args = parser.parse_args()
    try:
        result: dict[str, Any] = {
            "repository": inspect_repository(args.root.expanduser().resolve())
        }
        if not args.skip_local_tlge:
            result["local_tlge"] = verify_local_tlge(
                args.tlge_dir.expanduser().resolve()
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ABORT: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
