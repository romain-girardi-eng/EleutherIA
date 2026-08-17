#!/usr/bin/env python3
"""Validate or apply the frozen 2026-08-17 English-translation plan.

The default is a non-writing dry run.  ``--write`` changes only the 170 planned
node lines, creates ``<nodes>.bak-translations`` once, and is idempotent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from typing import Any

from data_2026_08_17_translations import (
    BLOCKED,
    RECORDS,
    SOURCE_MODEL,
    STAMP_FIELD,
    STAMP_VALUE,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NODES = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
BACKUP_SUFFIX = ".bak-translations"


class PlanError(RuntimeError):
    """A failed precondition or invariant."""


@dataclass
class Prepared:
    original_lines: list[str]
    output_lines: list[str]
    changed_ids: list[str]
    already_applied_ids: list[str]
    translated_ids: list[str]
    blocked_ids: list[str]
    source_languages: Counter[str]
    metadata_representations: Counter[str]
    source_twins: int
    source_texts_unchanged: int


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def node_identifier(node: dict[str, Any]) -> str | None:
    value = node.get("node_id") or node.get("id")
    return value if isinstance(value, str) and value else None


def parse_metadata(node: dict[str, Any], node_id: str) -> tuple[dict[str, Any], str]:
    raw = node.get("metadata")
    if isinstance(raw, dict):
        return dict(raw), "dict"
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PlanError(f"{node_id}: metadata string is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise PlanError(f"{node_id}: decoded metadata is not an object")
        return parsed, "str"
    raise PlanError(f"{node_id}: metadata must be an object or a JSON-object string")


def install_metadata(node: dict[str, Any], metadata: dict[str, Any], representation: str) -> None:
    if representation == "dict":
        node["metadata"] = metadata
    elif representation == "str":
        node["metadata"] = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    else:  # defensive; parse_metadata constrains this value
        raise AssertionError(representation)


def load_nodes(path: Path) -> tuple[list[str], list[dict[str, Any]], dict[str, int]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            lines = handle.readlines()
    except OSError as exc:
        raise PlanError(f"cannot read {path}: {exc}") from exc

    nodes: list[dict[str, Any]] = []
    index: dict[str, int] = {}
    for line_number, line in enumerate(lines, 1):
        try:
            node = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PlanError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(node, dict):
            raise PlanError(f"{path}:{line_number}: node is not an object")
        node_id = node_identifier(node)
        if node_id:
            if node_id in index:
                raise PlanError(f"duplicate node identifier: {node_id}")
            index[node_id] = len(nodes)
        nodes.append(node)
    return lines, nodes, index


def source_twin_id(
    node_id: str,
    metadata: dict[str, Any],
    index: dict[str, int],
) -> str:
    candidates: list[str] = []
    for key in ("primary_text_node_id", "original_node_id", "translation_of", "source_passage_id"):
        value = metadata.get(key)
        if isinstance(value, str) and value and value not in candidates:
            candidates.append(value)
    if node_id.endswith("_en"):
        conventional = node_id[:-3]
        if conventional not in candidates:
            candidates.append(conventional)
    for candidate in candidates:
        if candidate in index:
            return candidate
    raise PlanError(f"{node_id}: no surviving original twin; tried {candidates}")


def expected_label(current: str, record: dict[str, Any]) -> str:
    old = record["label_suffix_from"]
    new = record["label_suffix_to"]
    if not current.endswith(old):
        raise PlanError(f"{record['node_id']}: label does not end with {old!r}: {current!r}")
    return current[: -len(old)] + new


def metadata_has_updates(metadata: dict[str, Any], record: dict[str, Any]) -> bool:
    if any(metadata.get(key) != value for key, value in record["metadata_updates"].items()):
        return False
    return not any(key in metadata for key in record.get("metadata_remove", []))


def validate_applied(
    node: dict[str, Any],
    metadata: dict[str, Any],
    record: dict[str, Any],
) -> None:
    node_id = record["node_id"]
    if metadata.get(STAMP_FIELD) != STAMP_VALUE:
        raise PlanError(f"{node_id}: invalid idempotence stamp")
    if not metadata_has_updates(metadata, record):
        raise PlanError(f"{node_id}: stamped node does not match planned metadata")

    if record["status"] == "translate":
        if node.get("description") != record["translation"]:
            raise PlanError(f"{node_id}: stamped translation text differs from the frozen plan")
        label = node.get("label")
        if not isinstance(label, str) or not label.endswith(record["label_suffix_to"]):
            raise PlanError(f"{node_id}: stamped translation label is invalid")
    else:
        description = node.get("description")
        if not isinstance(description, str) or sha256_text(description) != record["sha256"]:
            raise PlanError(f"{node_id}: blocked node description changed after stamping")
        label = node.get("label")
        if not isinstance(label, str) or not label.endswith("(translation pending)"):
            raise PlanError(f"{node_id}: blocked node label must remain pending")


def prepare(path: Path) -> Prepared:
    original_lines, nodes, index = load_nodes(path)
    if len(RECORDS) != 170:
        raise PlanError(f"plan must contain 170 records, found {len(RECORDS)}")
    record_ids = [record["node_id"] for record in RECORDS]
    if len(set(record_ids)) != len(record_ids):
        raise PlanError("translation plan contains duplicate node ids")
    missing = sorted(set(record_ids) - set(index))
    if missing:
        raise PlanError(f"planned nodes missing from graph: {missing}")

    output_lines = list(original_lines)
    changed_ids: list[str] = []
    already_applied_ids: list[str] = []
    translated_ids: list[str] = []
    blocked_ids: list[str] = []
    source_languages: Counter[str] = Counter()
    metadata_representations: Counter[str] = Counter()
    twin_snapshots: dict[str, tuple[str, str]] = {}

    for record in RECORDS:
        node_id = record["node_id"]
        line_index = index[node_id]
        node = nodes[line_index]
        metadata, representation = parse_metadata(node, node_id)
        metadata_representations[representation] += 1
        language = metadata.get("language")
        if isinstance(language, str):
            source_languages[language] += 1

        twin_id = source_twin_id(node_id, metadata, index)
        planned_twin = record["metadata_updates"].get("original_node_id")
        if record["status"] == "translate" and twin_id != planned_twin:
            raise PlanError(
                f"{node_id}: resolved twin {twin_id!r} differs from planned pointer {planned_twin!r}"
            )
        twin = nodes[index[twin_id]]
        twin_description = twin.get("description")
        if not isinstance(twin_description, str) or not twin_description:
            raise PlanError(f"{node_id}: original twin {twin_id} has no reachable source text")
        twin_snapshots[node_id] = (twin_id, twin_description)

        stamp = metadata.get(STAMP_FIELD)
        if stamp == STAMP_VALUE:
            validate_applied(node, metadata, record)
            already_applied_ids.append(node_id)
            if record["status"] == "translate":
                translated_ids.append(node_id)
            else:
                blocked_ids.append(node_id)
            continue
        if stamp is not None:
            raise PlanError(f"{node_id}: unexpected idempotence stamp value {stamp!r}")

        description = node.get("description")
        if not isinstance(description, str):
            raise PlanError(f"{node_id}: description is not a string")
        actual_sha = sha256_text(description)
        if actual_sha != record["sha256"]:
            raise PlanError(
                f"{node_id}: description SHA-256 precondition failed; "
                f"expected {record['sha256']}, found {actual_sha}"
            )

        changed_node = dict(node)
        changed_metadata = dict(metadata)
        changed_metadata.update(record["metadata_updates"])
        for key in record.get("metadata_remove", []):
            changed_metadata.pop(key, None)

        if record["status"] == "translate":
            label = changed_node.get("label")
            if not isinstance(label, str):
                raise PlanError(f"{node_id}: label is not a string")
            changed_node["description"] = record["translation"]
            changed_node["label"] = expected_label(label, record)
            translated_ids.append(node_id)
        else:
            blocked_ids.append(node_id)

        install_metadata(changed_node, changed_metadata, representation)
        output_lines[line_index] = json.dumps(changed_node, ensure_ascii=False, sort_keys=True) + "\n"
        changed_ids.append(node_id)

    # No non-target line may change, and no original twin may be a target.
    target_ids = set(record_ids)
    for node_id, line_index in index.items():
        if node_id not in target_ids and output_lines[line_index] != original_lines[line_index]:
            raise PlanError(f"non-target node line changed: {node_id}")

    output_nodes = [json.loads(line) for line in output_lines]
    output_index = {
        node_identifier(node): i
        for i, node in enumerate(output_nodes)
        if node_identifier(node) is not None
    }
    unchanged_sources = 0
    for target_id, (twin_id, source_text) in twin_snapshots.items():
        if twin_id in target_ids:
            raise PlanError(f"{target_id}: original twin {twin_id} is also a translation target")
        if twin_id not in output_index:
            raise PlanError(f"{target_id}: original twin {twin_id} disappeared")
        if output_nodes[output_index[twin_id]].get("description") != source_text:
            raise PlanError(f"{target_id}: source text in twin {twin_id} changed")
        unchanged_sources += 1

    # Validate the fully simulated result, including metadata representation.
    for record in RECORDS:
        node = output_nodes[output_index[record["node_id"]]]
        metadata, representation = parse_metadata(node, record["node_id"])
        validate_applied(node, metadata, record)
        original_representation = parse_metadata(nodes[index[record["node_id"]]], record["node_id"])[1]
        if representation != original_representation:
            raise PlanError(f"{record['node_id']}: metadata representation changed")

    if len(output_lines) != len(original_lines):
        raise PlanError("node count changed")
    if not already_applied_ids and source_languages != Counter({"lat": 153, "grc": 17}):
        raise PlanError(f"fresh-plan language counts differ from 153 lat / 17 grc: {source_languages}")

    return Prepared(
        original_lines=original_lines,
        output_lines=output_lines,
        changed_ids=changed_ids,
        already_applied_ids=already_applied_ids,
        translated_ids=translated_ids,
        blocked_ids=blocked_ids,
        source_languages=source_languages,
        metadata_representations=metadata_representations,
        source_twins=len(twin_snapshots),
        source_texts_unchanged=unchanged_sources,
    )


def write_backup(source: Path, backup: Path) -> None:
    try:
        descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise PlanError(f"refusing to overwrite existing backup: {backup}") from exc
    try:
        with os.fdopen(descriptor, "wb") as destination, source.open("rb") as origin:
            shutil.copyfileobj(origin, destination)
        shutil.copystat(source, backup)
    except Exception:
        try:
            backup.unlink()
        except OSError:
            pass
        raise


def atomic_write(path: Path, lines: list[str]) -> None:
    mode = path.stat().st_mode
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.translations-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.writelines(lines)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except OSError:
                pass


def render_report(path: Path, prepared: Prepared, write: bool, wrote: bool) -> str:
    original_bytes = "".join(prepared.original_lines).encode("utf-8")
    output_bytes = "".join(prepared.output_lines).encode("utf-8")
    status_counts = Counter(record["status"] for record in RECORDS)
    action = "WRITE" if write else "DRY-RUN"
    lines = [
        f"mode={action}",
        f"nodes={path}",
        f"records={len(RECORDS)}",
        f"translations={status_counts['translate']}",
        f"blocked_ocr={status_counts['translation_blocked_ocr']}",
        f"blocked_source_not_original={status_counts['translation_blocked_source_not_original']}",
        f"changed={len(prepared.changed_ids)}",
        f"already_applied={len(prepared.already_applied_ids)}",
        f"languages_current={dict(sorted(prepared.source_languages.items()))}",
        f"metadata_representations={dict(sorted(prepared.metadata_representations.items()))}",
        f"source_twins_reachable={prepared.source_twins}",
        f"source_texts_unchanged={prepared.source_texts_unchanged}",
        f"input_sha256={sha256_bytes(original_bytes)}",
        f"simulated_output_sha256={sha256_bytes(output_bytes)}",
        "invariants=PASS",
    ]
    if write:
        lines.append(f"write_performed={'yes' if wrote else 'no (idempotent)'}")
        if wrote:
            lines.append(f"backup={path.with_name(path.name + BACKUP_SUFFIX)}")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nodes",
        type=Path,
        default=DEFAULT_NODES,
        help=f"nodes JSONL to validate/apply (default: {DEFAULT_NODES})",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="apply atomically after creating <nodes>.bak-translations; default is dry-run",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    path = args.nodes.resolve()
    try:
        prepared = prepare(path)
        wrote = False
        if args.write and prepared.changed_ids:
            backup = path.with_name(path.name + BACKUP_SUFFIX)
            before = path.read_bytes()
            write_backup(path, backup)
            if backup.read_bytes() != before:
                raise PlanError("backup is not byte-identical to the pre-write input")
            atomic_write(path, prepared.output_lines)
            wrote = True

            verified = prepare(path)
            if verified.changed_ids:
                raise PlanError(
                    f"post-write idempotence failed; {len(verified.changed_ids)} changes still planned"
                )
            if len(verified.already_applied_ids) != 170:
                raise PlanError("post-write stamp verification did not find all 170 records")
        print(render_report(path, prepared, args.write, wrote))
        return 0
    except (OSError, PlanError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

