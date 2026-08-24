#!/usr/bin/env python3
"""Correct Porphyry Ad Marcellam from TLG work 009 to authoritative 005."""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "porphyry_ad_marcellam_identity_repair_2026_08_24"
OLD_URN = "urn:cts:greekLit:tlg2034.tlg009"
NEW_URN = "urn:cts:greekLit:tlg2034.tlg005"
OLD_CANONICAL = "urn_cts_greeklit_tlg2034_tlg009_grc"
NEW_CANONICAL = "urn_cts_greeklit_tlg2034_tlg005_grc"
WORK_NODE = "work_porphyry_ad_marcellam"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(node: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        node["metadata"] = value


def transform(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    nodes = copy.deepcopy(nodes)
    passages = copy.deepcopy(passages)
    manifest = copy.deepcopy(manifest)
    changed: list[str] = []

    for node in nodes:
        data = metadata(node)
        if data.get("work_canonical_id") == OLD_URN:
            data["work_canonical_id"] = NEW_URN
            data[STAMP] = {
                "previous_work_urn": OLD_URN,
                "authority": "OpenGreekAndLatin First1KGreek catalog and CTS inventory",
            }
            if node_id(node) == WORK_NODE:
                data["cts_urn"] = NEW_URN
            set_metadata(node, data)
            node["updated_at"] = "2026-08-24 00:00:00+00:00"
            changed.append(node_id(node))
        elif node_id(node) == WORK_NODE and data.get("cts_urn") == OLD_URN:
            data["cts_urn"] = NEW_URN
            data["work_canonical_id"] = NEW_URN
            data[STAMP] = {"previous_work_urn": OLD_URN}
            set_metadata(node, data)
            node["updated_at"] = "2026-08-24 00:00:00+00:00"
            changed.append(node_id(node))

    for row in passages:
        if row.get("work_canonical_id") == OLD_CANONICAL:
            row["work_canonical_id"] = NEW_CANONICAL
            changed.append(str(row.get("passage_id")))

    for row in manifest:
        if row.get("canonical_id") == OLD_CANONICAL:
            row["canonical_id"] = NEW_CANONICAL
            row["cts_urn"] = "urn:cts:greekLit:tlg2034.tlg005.1st1K-grc1"
            row["identity_repair_2026_08_24"] = {
                "previous_canonical_id": OLD_CANONICAL,
                "authority": "OpenGreekAndLatin First1KGreek",
            }
            changed.append("manifest:" + NEW_CANONICAL)

    validate(nodes, passages, manifest)
    return nodes, passages, manifest, changed


def validate(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> None:
    relevant_nodes = []
    for node in nodes:
        data = metadata(node)
        if node_id(node) == WORK_NODE or str(data.get("cts_urn") or "").startswith(
            "urn:cts:greekLit:tlg2034.tlg005"
        ):
            relevant_nodes.append(node)
            if data.get("work_canonical_id") != NEW_URN:
                raise RuntimeError(f"Porphyry node retains wrong work identity: {node_id(node)}")
    if len(relevant_nodes) != 36:
        raise RuntimeError(f"expected work + 35 Porphyry nodes, found {len(relevant_nodes)}")
    rows = [row for row in passages if row.get("work_canonical_id") == NEW_CANONICAL]
    if len(rows) != 35:
        raise RuntimeError(f"expected 35 Porphyry corpus rows, found {len(rows)}")
    if any(
        not str(row.get("cts_urn") or "").startswith(
            "urn:cts:greekLit:tlg2034.tlg005.1st1K-grc1:"
        )
        for row in rows
    ):
        raise RuntimeError("Porphyry passage CTS does not match authoritative work")
    manifests = [row for row in manifest if row.get("canonical_id") == NEW_CANONICAL]
    if len(manifests) != 1:
        raise RuntimeError("Porphyry manifest identity is not unique")


def write_preserving(
    path: Path, rows: list[dict[str, Any]], key: Callable[[dict[str, Any]], str]
) -> None:
    original = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    desired = {key(row): row for row in rows}
    if len(desired) != len(rows):
        raise RuntimeError(f"duplicate identity in {path}")
    seen: set[str] = set()
    output: list[str] = []
    for line in original:
        old = json.loads(line)
        wanted = key(old)
        if wanted not in desired:
            continue
        new = desired[wanted]
        compact = ": " not in line
        output.append(
            line
            if old == new
            else json.dumps(
                new,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":") if compact else None,
            )
        )
        seen.add(wanted)
    for wanted in sorted(desired.keys() - seen):
        output.append(json.dumps(desired[wanted], ensure_ascii=False, sort_keys=True))
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write("\n".join(output) + "\n")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    nodes_path = data_root / "kg/nodes.jsonl"
    passages_path = data_root / "corpus/passages.jsonl"
    manifest_path = data_root / "corpus/manifest.jsonl"
    result = transform(
        read_jsonl(nodes_path), read_jsonl(passages_path), read_jsonl(manifest_path)
    )
    nodes, passages, manifest, changed = result
    print("Porphyry Ad Marcellam identity repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("records changed:", len(changed))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("already applied: no files written")
        return 0
    write_preserving(nodes_path, nodes, node_id)
    write_preserving(passages_path, passages, lambda row: str(row.get("passage_id") or ""))
    write_preserving(manifest_path, manifest, lambda row: str(row.get("canonical_id") or ""))
    report = data_root / "audit/2026-08-24_porphyry_ad_marcellam_identity_repair.json"
    report.write_text(
        json.dumps(
            {
                "old_urn": OLD_URN,
                "new_urn": NEW_URN,
                "changed_records": changed,
                "authority": "OpenGreekAndLatin First1KGreek catalog",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print("wrote:", nodes_path, passages_path, manifest_path, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
