#!/usr/bin/env python3
"""Source-gated Methodius re-ingestion data and provenance checks.

No Greek replacement is embedded in this module.  The requested source files,
``TLG2959.TXT`` and ``TLG2959.IDT``, are absent from the supplied TLG E tree,
and ``TLG2959`` is absent from that tree's ``AUTHTAB.DIR``.  The only safe
delta is therefore a conservative mapping-blocker record for each of the 82
nodes already classified as GCS apparatus.

The IDT routines are retained here as executable preparation for a later wave.
They use the same level-update state machine and 8192-byte block model as
``data_2026_08_17_plotinus_remap.py``.  ``extract_idt_works`` additionally
decodes the work-id header used by TLG IDT files.  Once the missing files are
restored, this module deliberately invalidates the blocker delta so that a new
Greek payload must be rebuilt and reviewed from the actual source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

STAMP = "methodius_reingest_2026_08_17"
BACKUP_SUFFIX = ".bak-methodius"
TLG_AUTHOR = "2959"
TLG_FILE = "TLG2959.TXT"
IDT_FILE = "TLG2959.IDT"
AUTHTAB_FILE = "AUTHTAB.DIR"
TLG_BLOCK_SIZE = 8192
WORK_URN_CANDIDATE = "urn:cts:greekLit:tlg2959.tlg002"
TEXT_SOURCE = "TLG2959 (TLG E disk)"
AUTHTAB_SHA256 = "8457a0cbe7943d148157a4ec8fb001c5412cc6ee5655e1c6bac14a818ed5e731"
SOURCE_BLOCKER_REASON = (
    "TLG2959.TXT and TLG2959.IDT are absent from the supplied TLG E tree, "
    "and TLG2959 is absent from its AUTHTAB.DIR; no TLG span or IDT citation "
    "can be attested without the missing source files"
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NODES = ROOT / "data" / "kg" / "nodes.jsonl"
DEFAULT_TLGE = Path(
    os.environ.get("TLGE_DIR", "~/Desktop/Romain/TLGE")
).expanduser()

APPARATUS_NODE_IDS = (
    "passage_meth_dla_1",
    "passage_meth_dla_2",
    "passage_meth_dla_3",
    "passage_meth_dla_6",
    "passage_meth_dla_7",
    "passage_meth_dla_8",
    "passage_meth_dla_9",
    "passage_meth_dla_10",
    "passage_meth_dla_11",
    "passage_meth_dla_12",
    "passage_meth_dla_14",
    "passage_meth_dla_15",
    "passage_meth_dla_17",
    "passage_meth_dla_19",
    "passage_meth_dla_20",
    "passage_meth_dla_21",
    "passage_meth_dla_22",
    "passage_meth_dla_23",
    "passage_meth_dla_24",
    "passage_meth_dla_26",
    "passage_meth_dla_27",
    "passage_meth_dla_28",
    "passage_meth_dla_29",
    "passage_meth_dla_30",
    "passage_meth_dla_31",
    "passage_meth_dla_32",
    "passage_meth_dla_33",
    "passage_meth_dla_34",
    "passage_meth_dla_35",
    "passage_meth_dla_36",
    "passage_meth_dla_37",
    "passage_meth_dla_38",
    "passage_meth_dla_39",
    "passage_meth_dla_40",
    "passage_meth_dla_41",
    "passage_meth_dla_42",
    "passage_meth_dla_43",
    "passage_meth_dla_44",
    "passage_meth_dla_45",
    "passage_meth_dla_49",
    "passage_meth_dla_50",
    "passage_meth_dla_51",
    "passage_meth_dla_52",
    "passage_meth_dla_55",
    "passage_meth_dla_57",
    "passage_meth_dla_58",
    "passage_meth_dla_59",
    "passage_meth_dla_60",
    "passage_meth_dla_61",
    "passage_meth_dla_62",
    "passage_meth_dla_65",
    "passage_meth_dla_66",
    "passage_meth_dla_67",
    "passage_meth_dla_68",
    "passage_meth_dla_69",
    "passage_meth_dla_73",
    "passage_meth_dla_74",
    "passage_meth_dla_75",
    "passage_meth_dla_76",
    "passage_meth_dla_77",
    "passage_meth_dla_78",
    "passage_meth_dla_80",
    "passage_meth_dla_81",
    "passage_meth_dla_83",
    "passage_meth_dla_84",
    "passage_meth_dla_85",
    "passage_meth_dla_86",
    "passage_meth_dla_87",
    "passage_meth_dla_88",
    "passage_meth_dla_89",
    "passage_meth_dla_91",
    "passage_meth_dla_94",
    "passage_meth_dla_95",
    "passage_meth_dla_98",
    "passage_meth_dla_100",
    "passage_meth_dla_101",
    "passage_meth_dla_102",
    "passage_meth_dla_103",
    "passage_meth_dla_104",
    "passage_meth_dla_105",
    "passage_meth_dla_106",
    "passage_meth_dla_107",
)
RECORD_COUNT = 82
EXPECTED_FAMILY_SIZE = 111


def node_id(node: dict) -> str:
    return node.get("node_id") or node.get("id") or ""


def metadata(node: dict) -> dict:
    value = node.get("metadata")
    if isinstance(value, str):
        value = json.loads(value)
    return value if isinstance(value, dict) else {}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_inventory(tlge_dir: Path) -> dict:
    """Return exact, read-only evidence about the requested TLG source."""
    txt_path = tlge_dir / TLG_FILE
    idt_path = tlge_dir / IDT_FILE
    authtab_path = tlge_dir / AUTHTAB_FILE
    authtab = authtab_path.read_bytes() if authtab_path.is_file() else b""
    txt_files = list(tlge_dir.glob("TLG[0-9][0-9][0-9][0-9].TXT"))
    idt_files = list(tlge_dir.glob("TLG[0-9][0-9][0-9][0-9].IDT"))
    result = {
        "tlge_dir": str(tlge_dir),
        "txt_path": str(txt_path),
        "txt_exists": txt_path.is_file(),
        "idt_path": str(idt_path),
        "idt_exists": idt_path.is_file(),
        "authtab_path": str(authtab_path),
        "authtab_exists": authtab_path.is_file(),
        "authtab_sha256": sha256(authtab_path),
        "authtab_has_tlg2959": b"TLG2959" in authtab,
        "txt_file_count": len(txt_files),
        "idt_file_count": len(idt_files),
    }
    result["source_available"] = bool(result["txt_exists"] and result["idt_exists"])
    result["source_fully_indexed"] = bool(
        result["source_available"] and result["authtab_has_tlg2959"]
    )
    result["blocker"] = None if result["source_available"] else SOURCE_BLOCKER_REASON
    return result


def _empty_citation_state() -> dict[str, list[int | str]]:
    return {key: [0, ""] for key in "abcdnvwxyz"}


_LEVEL_BY_CASE = {0: "z", 1: "y", 2: "x", 3: "w", 4: "v", 5: "n"}


def _reset_lower_levels(state: dict, level: str) -> None:
    if level in "ab":
        lower = "nvwxyz"
        reset_value = 0
    elif level == "n":
        lower = "vwxyz"
        reset_value = 0
    elif level in "vwxyz":
        order = "vwxyz"
        lower = order[order.index(level) + 1 :]
        reset_value = 1
    else:
        return
    for item in lower:
        state[item] = [reset_value, ""]


def _ascii_payload(raw: bytes, start: int, end: int) -> str:
    return bytes(value & 0x7F for value in raw[start:end]).decode("ascii", "strict")


def apply_id_codes(raw: bytes, offset: int, state: dict) -> int:
    """Decode consecutive PHI/TLG high-bit level-update commands."""
    while offset < len(raw) and raw[offset] >= 0x80:
        lead = raw[offset]
        offset += 1
        if lead >= 0xF0:
            continue
        if lead >= 0xE0:
            command = lead & 0x0F
            level_byte = raw[offset] & 0x7F
            offset += 1
            if level_byte >= ord("a"):
                level = chr(level_byte)
            else:
                level = {0: "a", 1: "b", 2: "c", 4: "d"}.get(
                    level_byte & 7, "?"
                )
        else:
            command = lead & 0x0F
            level = _LEVEL_BY_CASE.get((lead >> 4) & 7, "?")
        value, suffix = state.get(level, [0, ""])
        if command == 0:
            if suffix:
                suffix = suffix[:-1] + chr(ord(suffix[-1]) + 1)
            else:
                value += 1
        elif 1 <= command <= 7:
            value, suffix = command, ""
        elif command == 8:
            value, suffix = raw[offset] & 0x7F, ""
            offset += 1
        elif command == 9:
            value = raw[offset] & 0x7F
            suffix = chr(raw[offset + 1] & 0x7F)
            offset += 2
        elif command == 10:
            value = raw[offset] & 0x7F
            offset += 1
            end = raw.index(0xFF, offset)
            suffix = _ascii_payload(raw, offset, end)
            offset = end + 1
        elif command in (11, 12, 13):
            value = ((raw[offset] & 0x7F) << 7) | (raw[offset + 1] & 0x7F)
            offset += 2
            if command == 11:
                suffix = ""
            elif command == 12:
                suffix = chr(raw[offset] & 0x7F)
                offset += 1
            else:
                end = raw.index(0xFF, offset)
                suffix = _ascii_payload(raw, offset, end)
                offset = end + 1
        elif command == 14:
            suffix = chr(raw[offset] & 0x7F)
            offset += 1
        elif command == 15:
            value = 0
            end = raw.index(0xFF, offset)
            suffix = _ascii_payload(raw, offset, end)
            offset = end + 1
        else:  # pragma: no cover
            raise AssertionError(f"impossible ID command: {command}")
        if level in state:
            state[level] = [value, suffix]
            _reset_lower_levels(state, level)
    return offset


def extract_idt_works(raw: bytes) -> list[dict[str, str]]:
    """Extract work numbers and titles from IDT work headers.

    A work header stores its three-digit identifier as an ``ef 81 ... ff``
    level-b string, followed by a ``10 01 <length> <title>`` field.
    """
    works = []
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
            length_at = title_marker + 2
            length = raw[length_at]
            title_start = length_at + 1
            title_end = title_start + length
            if title_end <= len(raw):
                title = raw[title_start:title_end].decode("ascii", "replace")
                works.append({"work_id": work_id, "title": title})
        position = end + 1
    return works


def parse_idt_schema(raw: bytes) -> dict[int, str]:
    """Read the citation-level labels from every IDT work header."""
    descriptors: dict[int, str] = {}
    position = 0
    while position + 3 <= len(raw):
        if raw[position] != 0x11:
            position += 1
            continue
        level = raw[position + 1]
        length = raw[position + 2]
        end = position + 3 + length
        if (
            end <= len(raw)
            and level <= 3
            and all(0x20 <= value < 0x7F for value in raw[position + 3 : end])
        ):
            descriptors[level] = raw[position + 3 : end].decode("ascii")
            position = end
        else:
            position += 1
    return descriptors


def blocked_records(nodes_path: Path) -> tuple[dict, ...]:
    """Build the metadata-only delta after strict live-family validation."""
    nodes = read_jsonl(nodes_path)
    family = [node for node in nodes if node_id(node).startswith("passage_meth_dla_")]
    if len(family) != EXPECTED_FAMILY_SIZE:
        raise ValueError(
            f"found {len(family)} passage_meth_dla_* nodes; expected {EXPECTED_FAMILY_SIZE}"
        )
    by_id = {node_id(node): node for node in family}
    actual = {
        wanted_id
        for wanted_id, node in by_id.items()
        if metadata(node).get("content_kind") == "apparatus_gcs"
    }
    expected = set(APPARATUS_NODE_IDS)
    if actual != expected:
        raise ValueError(
            "apparatus node set drift: "
            f"missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        )
    records = []
    for wanted_id in APPARATUS_NODE_IDS:
        node = by_id[wanted_id]
        meta = metadata(node)
        records.append(
            {
                "node_id": wanted_id,
                "canonical_ref": meta.get("canonical_ref"),
                "corpus_uuid": meta.get("db_passage_id"),
                "description_sha256": hashlib.sha256(
                    (node.get("description") or "").encode("utf-8")
                ).hexdigest(),
                "action": "flag_needs_locus_mapping",
                "reason": SOURCE_BLOCKER_REASON,
            }
        )
    return tuple(records)


def check_data(nodes_path: Path) -> tuple[dict, ...]:
    assert len(APPARATUS_NODE_IDS) == RECORD_COUNT
    assert len(APPARATUS_NODE_IDS) == len(set(APPARATUS_NODE_IDS))
    records = blocked_records(nodes_path)
    assert len(records) == RECORD_COUNT
    assert all(record["canonical_ref"] for record in records)
    assert all(record["corpus_uuid"] for record in records)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--tlge-dir", type=Path, default=DEFAULT_TLGE)
    args = parser.parse_args()
    records = check_data(args.nodes)
    inventory = source_inventory(args.tlge_dir.expanduser())
    if inventory["source_available"]:
        idt = (args.tlge_dir.expanduser() / IDT_FILE).read_bytes()
        inventory["idt_works"] = extract_idt_works(idt)
        inventory["idt_schema"] = parse_idt_schema(idt)
    print(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"blocked records: {len(records)}")
    print("Greek replacement records: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
