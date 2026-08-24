#!/usr/bin/env python3
"""Export publication nodes from the KG snapshot as BibTeX.

This is intentionally deterministic and conservative: missing required
bibliographic fields are reported, and ``--strict`` exits non-zero so CI can
gate the thesis bibliography once the backlog is cleared.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("author", "title", "year")


def normalize_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        # Export is a read-only projection.  Returning the caller's metadata
        # object let ``setdefault`` below silently mutate KG nodes in-memory.
        return copy.deepcopy(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return copy.deepcopy(parsed) if isinstance(parsed, dict) else {}
    return {}


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def slugify(value: str, fallback: str) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or fallback


def bibtex_key(node: dict[str, Any], metadata: dict[str, Any]) -> str:
    for key in ("bibtex_key", "zotero_key", "zotero_id"):
        if value := metadata.get(key):
            return slugify(str(value), str(node.get("id") or "publication"))
    author = str(metadata.get("author") or "")
    surname = author.split(" and ")[0].split(",")[0].split()[-1:] or ["publication"]
    year = str(metadata.get("year") or "n.d.")
    title = str(metadata.get("title") or node.get("label") or "")
    return slugify("-".join([surname[0], year, title]), str(node.get("id")))


def entry_type(metadata: dict[str, Any]) -> str:
    raw = str(metadata.get("type") or metadata.get("item_type") or "").lower()
    if "chapter" in raw:
        return "incollection"
    if "article" in raw or metadata.get("journal"):
        return "article"
    if "thesis" in raw:
        return "phdthesis"
    return "book"


def field_value(node: dict[str, Any], metadata: dict[str, Any], field: str) -> str | None:
    if field == "title":
        return str(metadata.get("title") or node.get("label") or "").strip() or None
    aliases = {
        "booktitle": ("book_title", "booktitle"),
        "doi": ("doi", "DOI"),
        "isbn": ("isbn", "ISBN"),
        "url": ("url", "source_url"),
    }
    for key in aliases.get(field, (field,)):
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def escape_bibtex(value: str) -> str:
    return value.replace("\\", "\\textbackslash{}").replace("{", "\\{").replace("}", "\\}")


def publication_to_bibtex(node: dict[str, Any]) -> tuple[str, list[str]]:
    metadata = normalize_mapping(node.get("metadata"))
    metadata.setdefault("title", node.get("label"))
    missing = [field for field in REQUIRED_FIELDS if not field_value(node, metadata, field)]

    fields = [
        "author",
        "title",
        "year",
        "journal",
        "booktitle",
        "editor",
        "publisher",
        "address",
        "pages",
        "volume",
        "number",
        "doi",
        "isbn",
        "url",
    ]
    rendered: list[str] = []
    for field in fields:
        value = field_value(node, metadata, field)
        if value:
            rendered.append(f"  {field} = {{{escape_bibtex(value)}}}")
    note = f"EleutherIA KG node: {node.get('id') or node.get('node_id')}"
    if manifestation_id := metadata.get("manifestation_id"):
        note += f"; manifestation: {manifestation_id}"
    rendered.append(f"  note = {{{note}}}")

    body = ",\n".join(rendered)
    return f"@{entry_type(metadata)}{{{bibtex_key(node, metadata)},\n{body}\n}}\n", missing


def publication_entries_to_bibtex(
    node: dict[str, Any],
) -> list[tuple[str, list[str], str | None]]:
    """Render one legacy entry or explicit manifestation-bound entries.

    ``metadata.bibtex_manifestations`` is intentionally opt-in.  It lets an
    intellectual-work node stay publisher-neutral while the generated
    bibliography remains concrete and reproducible.  Existing publication
    nodes retain their historical single-entry behavior.
    """

    metadata = normalize_mapping(node.get("metadata"))
    manifestations = metadata.get("bibtex_manifestations")
    if not isinstance(manifestations, list) or not manifestations:
        entry, missing = publication_to_bibtex(node)
        return [(entry, missing, None)]

    result: list[tuple[str, list[str], str | None]] = []
    for index, manifestation in enumerate(manifestations):
        if not isinstance(manifestation, dict):
            raise ValueError(f"bibtex_manifestations[{index}] must be an object")
        concrete = copy.deepcopy(manifestation)
        for inherited in ("author", "title", "type"):
            if inherited not in concrete and metadata.get(inherited) not in (None, ""):
                concrete[inherited] = metadata[inherited]
        concrete.setdefault("type", "book")
        synthetic = dict(node)
        synthetic["metadata"] = concrete
        entry, missing = publication_to_bibtex(synthetic)
        result.append((entry, missing, str(concrete.get("manifestation_id") or "") or None))
    return result


def bibtex_entry_keys(text: str) -> list[str]:
    """Return entry keys in artifact order, rejecting malformed entry headers."""

    keys = re.findall(r"^@[A-Za-z]+\{([^,\s]+),", text, flags=re.MULTILINE)
    header_count = sum(1 for line in text.splitlines() if line.startswith("@"))
    if len(keys) != header_count:
        raise ValueError("one or more BibTeX entry headers could not be parsed")
    return keys


def _keys_sha256(keys: list[str]) -> str:
    payload = json.dumps(
        keys, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_publication_export(
    nodes: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    """Build the canonical full BibTeX artifact and its base report."""

    publications = [row for row in nodes if row.get("type") == "publication"]
    entries: list[str] = []
    missing_report: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for node in publications:
        for entry, raw_missing, manifestation_id in publication_entries_to_bibtex(node):
            missing = list(raw_missing)
            key = bibtex_entry_keys(entry)[0]
            if key in seen_keys:
                missing.append("unique_bibtex_key")
            seen_keys.add(key)
            entries.append(entry)
            if missing:
                item: dict[str, Any] = {
                    "node_id": node.get("id") or node.get("node_id"),
                    "label": node.get("label"),
                    "missing": missing,
                }
                if manifestation_id is not None:
                    item["manifestation_id"] = manifestation_id
                missing_report.append(item)
    bibtex_text = "\n".join(entries)
    return bibtex_text, {
        "publication_count": len(publications),
        "entries_written": len(entries),
        "nodes_with_missing_fields": len(missing_report),
        "missing": missing_report,
    }


def build_companion_report(
    nodes: list[dict[str, Any]],
    bibtex_text: str,
    *,
    generation_mode: str,
    baseline_bibtex_sha256: str | None = None,
) -> dict[str, Any]:
    """Describe an exact BibTeX artifact, including any preserved legacy drift."""

    canonical_text, canonical = build_publication_export(nodes)
    artifact_keys = bibtex_entry_keys(bibtex_text)
    canonical_keys = bibtex_entry_keys(canonical_text)
    if len(artifact_keys) != len(set(artifact_keys)):
        raise ValueError("BibTeX artifact contains duplicate entry keys")
    report = dict(canonical)
    report.update(
        {
            "companion_report_schema_version": "2.0.0",
            "generation_mode": generation_mode,
            "entries_written": len(artifact_keys),
            "entry_keys": artifact_keys,
            "entry_keys_sha256": _keys_sha256(artifact_keys),
            "bibtex_sha256": hashlib.sha256(bibtex_text.encode("utf-8")).hexdigest(),
            "canonical_export_entry_count": len(canonical_keys),
            "canonical_export_bibtex_sha256": hashlib.sha256(
                canonical_text.encode("utf-8")
            ).hexdigest(),
            "artifact_only_keys_vs_canonical_export": sorted(
                set(artifact_keys) - set(canonical_keys)
            ),
            "canonical_export_only_keys_vs_artifact": sorted(
                set(canonical_keys) - set(artifact_keys)
            ),
        }
    )
    if baseline_bibtex_sha256 is not None:
        report["baseline_bibtex_sha256"] = baseline_bibtex_sha256
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=Path, default=Path("data/kg/nodes.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/kg/publications.bib"))
    parser.add_argument("--report", type=Path, default=Path("data/kg/publications_bibtex_report.json"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    nodes = list(iter_jsonl(args.nodes))
    bibtex_text, _base_report = build_publication_export(nodes)
    report = build_companion_report(
        nodes,
        bibtex_text,
        generation_mode="canonical_full_export",
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(bibtex_text, encoding="utf-8")
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    print(
        f"wrote {report['entries_written']} BibTeX entries to {args.output}; "
        f"{report['nodes_with_missing_fields']} nodes need metadata",
        file=sys.stderr,
    )
    return 1 if args.strict and report["missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
