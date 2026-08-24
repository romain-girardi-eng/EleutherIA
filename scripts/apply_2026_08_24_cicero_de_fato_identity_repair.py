#!/usr/bin/env python3
"""Normalize Cicero De Fato to authoritative Perseus work phi0474.phi054.

Legacy rows used phi049 as the canonical work and phi056 in passage CTS URNs;
phi056 is Epistulae ad Familiares.  This repair corrects work identity across
KG/corpus/manifest, declares the existing Yonge translation snapshots, and
keeps Latin edition exactness explicitly open rather than inventing a version.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import tempfile
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "cicero_de_fato_identity_repair_2026_08_24"
WORK_NODE = "work_de_fato_cicero_44bce_b9c4e5d2"
OLD_WORK_URN = "urn:cts:latinLit:phi0474.phi049"
WRONG_PASSAGE_URN = "urn:cts:latinLit:phi0474.phi056"
NEW_WORK_URN = "urn:cts:latinLit:phi0474.phi054"
OLD_LAT = "urn_cts_latinlit_phi0474_phi049_lat"
OLD_ENG = "urn_cts_latinlit_phi0474_phi049_eng"
NEW_LAT = "urn_cts_latinlit_phi0474_phi054_lat"
NEW_ENG = "urn_cts_latinlit_phi0474_phi054_eng"


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


def sha256_nfc(value: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", value).encode("utf-8")).hexdigest()


def rewrite_work_vocabulary(value: str) -> str:
    return value.replace(
        "fatum, liberum arbitrium, voluntas, adsensio",
        "fatum, necessitas, voluntas, adsensio, in nostra potestate",
    )


def transform(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    nodes = copy.deepcopy(nodes)
    passages = copy.deepcopy(passages)
    manifest = copy.deepcopy(manifest)
    changed: list[str] = []

    corpus_by_id = {str(row.get("passage_id")): row for row in passages}
    by_node = {node_id(node): node for node in nodes}
    already_current = (
        metadata(by_node.get(WORK_NODE, {})).get("cts_urn") == NEW_WORK_URN
        and sum(
            row.get("work_canonical_id") in {NEW_LAT, NEW_ENG} for row in passages
        )
        == 96
        and {
            row.get("canonical_id")
            for row in manifest
            if row.get("canonical_id") in {NEW_LAT, NEW_ENG}
        }
        == {NEW_LAT, NEW_ENG}
        and all(
            metadata(by_node.get(f"passage_cic_fat_{i}_en", {})).get("db_passage_id")
            for i in range(1, 49)
        )
    )
    if already_current:
        validate(nodes, passages, manifest)
        return nodes, passages, manifest, changed

    for row in passages:
        if row.get("work_canonical_id") not in {OLD_LAT, OLD_ENG, NEW_LAT, NEW_ENG}:
            continue
        is_english = str(row.get("work_canonical_id")).endswith("_eng")
        row["work_canonical_id"] = NEW_ENG if is_english else NEW_LAT
        cts = str(row.get("cts_urn") or "")
        row["cts_urn"] = cts.replace(WRONG_PASSAGE_URN, NEW_WORK_URN)
        row["work_identity_authority"] = "Perseus Catalog urn:cts:latinLit:phi0474.phi054"
        row["edition_identity_status"] = (
            "C.D. Yonge 1853 published public-domain translation"
            if is_english
            else "legacy Latin text; exact edition/version still requires adjudication"
        )
        changed.append("corpus:" + str(row.get("passage_id")))

    for node in nodes:
        wanted = node_id(node)
        if wanted == WORK_NODE:
            node["description"] = rewrite_work_vocabulary(str(node.get("description") or ""))
            data = metadata(node)
            for key in ("description_en", "description_fr", "description_en_pre_2026_08_16"):
                if isinstance(data.get(key), str):
                    data[key] = rewrite_work_vocabulary(data[key])
            data.update(
                {
                    "cts_urn": NEW_WORK_URN,
                    "work_canonical_id": NEW_WORK_URN,
                    STAMP: {
                        "previous_work_urn": OLD_WORK_URN,
                        "wrong_passage_work_urn": WRONG_PASSAGE_URN,
                        "authority": "Perseus Catalog",
                    },
                }
            )
            set_metadata(node, data)
            node["updated_at"] = "2026-08-24 00:00:00+00:00"
            changed.append(wanted)
            continue
        if not re.fullmatch(r"passage_cic_fat_\d+(?:_en)?", wanted):
            continue
        data = metadata(node)
        data["cts_urn"] = str(data.get("cts_urn") or "").replace(
            WRONG_PASSAGE_URN, NEW_WORK_URN
        )
        data["work_canonical_id"] = NEW_WORK_URN
        data.pop("parity_reason", None)
        data.pop("parity_zero_2026_08_18", None)
        data[STAMP] = {
            "previous_work_urn": OLD_WORK_URN,
            "wrong_passage_work_urn": WRONG_PASSAGE_URN,
            "authority": "Perseus Catalog",
            "edition_scope": (
                "Yonge 1853 translation"
                if wanted.endswith("_en")
                else "Latin edition unresolved; identity correction only"
            ),
        }
        if wanted.endswith("_en"):
            passage_id = str(data.get("source_passage_id") or "")
            corpus = corpus_by_id.get(passage_id)
            if corpus is None or corpus.get("text_content") != node.get("description"):
                raise RuntimeError(f"English translation is not an exact corpus snapshot: {wanted}")
            data.update(
                {
                    "citable_as_primary": True,
                    "corpus_passage_id": passage_id,
                    "db_passage_id": passage_id,
                    "passage_id": passage_id,
                    "primary_text_status": "published_translation",
                    "text_content_sha256_nfc": sha256_nfc(str(node.get("description") or "")),
                }
            )
        else:
            data["edition_identity_status"] = (
                "legacy Latin text; exact edition/version still requires adjudication"
            )
            if data.get("related_corpus_passage_id"):
                data["parity_status"] = "related_non_exact_pending_edition_adjudication"
        set_metadata(node, data)
        node["updated_at"] = "2026-08-24 00:00:00+00:00"
        changed.append(wanted)

    repaired_manifest: list[dict[str, Any]] = []
    has_latin = False
    for row in manifest:
        if row.get("canonical_id") in {OLD_ENG, NEW_ENG}:
            row["canonical_id"] = NEW_ENG
            row["cts_urn"] = NEW_WORK_URN
            row["ingest_class"] = "published_translation"
            row["source"] = "C.D. Yonge, The Treatises of M.T. Cicero (Bohn, 1853)"
            row["identity_repair_2026_08_24"] = {
                "previous_canonical_id": OLD_ENG,
                "wrong_source_urn": WRONG_PASSAGE_URN,
                "authority": "Perseus Catalog",
            }
            changed.append("manifest:" + NEW_ENG)
        if row.get("canonical_id") == NEW_LAT:
            has_latin = True
        repaired_manifest.append(row)
    manifest = repaired_manifest
    if not has_latin:
        manifest.append(
            {
                "author": "Cicero",
                "canonical_id": NEW_LAT,
                "cts_urn": NEW_WORK_URN,
                "edition_status": "legacy Latin text; exact edition/version requires adjudication",
                "identity_authority": "Perseus Catalog urn:cts:latinLit:phi0474.phi054",
                "ingest_class": "legacy_curated_text",
                "passages": 48,
                "period": "Roman Republican",
                "source": "local legacy Cicero_De_Fato_LAT text; work identity corrected only",
                "status": "in_corpus",
                "title": "De Fato (On Fate) — Latin",
            }
        )
        changed.append("manifest:" + NEW_LAT)

    validate(nodes, passages, manifest)
    return nodes, passages, manifest, changed


def validate(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> None:
    by_node = {node_id(node): node for node in nodes}
    work = metadata(by_node[WORK_NODE])
    if work.get("cts_urn") != NEW_WORK_URN or work.get("work_canonical_id") != NEW_WORK_URN:
        raise RuntimeError("Cicero work identity is not phi054")
    passage_nodes = [
        node for node in nodes if re.fullmatch(r"passage_cic_fat_\d+(?:_en)?", node_id(node))
    ]
    if len(passage_nodes) != 96:
        raise RuntimeError(f"expected 96 Cicero passage nodes, found {len(passage_nodes)}")
    for node in passage_nodes:
        data = metadata(node)
        if data.get("work_canonical_id") != NEW_WORK_URN or not str(data.get("cts_urn")).startswith(
            NEW_WORK_URN
        ):
            raise RuntimeError(f"Cicero node identity mismatch: {node_id(node)}")
    corpus = [
        row for row in passages if row.get("work_canonical_id") in {NEW_LAT, NEW_ENG}
    ]
    if len(corpus) != 96 or {row.get("work_canonical_id") for row in corpus} != {
        NEW_LAT,
        NEW_ENG,
    }:
        raise RuntimeError("Cicero corpus language manifestations are incomplete")
    if any(not str(row.get("cts_urn")).startswith(NEW_WORK_URN) for row in corpus):
        raise RuntimeError("Cicero corpus CTS still points to another work")
    current_manifest = [
        row for row in manifest if row.get("canonical_id") in {NEW_LAT, NEW_ENG}
    ]
    if len(current_manifest) != 2:
        raise RuntimeError("Cicero Latin/English manifest records are not distinct")
    if any(
        OLD_WORK_URN in str(metadata(node).get("work_canonical_id"))
        or WRONG_PASSAGE_URN in str(metadata(node).get("cts_urn"))
        for node in passage_nodes
    ):
        raise RuntimeError("wrong Cicero work identity survives current fields")
    if "fatum, liberum arbitrium" in by_node[WORK_NODE].get("description", ""):
        raise RuntimeError("unsupported Ciceronian terminology claim survives")


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
        compact = path.name in {"passages.jsonl", "manifest.jsonl"}
        output.append(
            json.dumps(
                desired[wanted],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":") if compact else None,
            )
        )
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
    nodes, passages, manifest, changed = transform(
        read_jsonl(nodes_path), read_jsonl(passages_path), read_jsonl(manifest_path)
    )
    print("Cicero De Fato identity repair")
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
    report = data_root / "audit/2026-08-24_cicero_de_fato_identity_repair.json"
    report.write_text(
        json.dumps(
            {
                "authoritative_work_urn": NEW_WORK_URN,
                "changed_records": changed,
                "latin_edition_status": "open",
                "authority": "Perseus Catalog",
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
