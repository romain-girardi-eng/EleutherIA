#!/usr/bin/env python3
"""Export publication nodes from the KG snapshot as BibTeX.

This is intentionally deterministic and conservative: missing required
bibliographic fields are reported, and ``--strict`` exits non-zero so CI can
gate the thesis bibliography once the backlog is cleared.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("author", "title", "year")


def normalize_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
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
    rendered.append(f"  note = {{EleutherIA KG node: {node.get('id') or node.get('node_id')}}}")

    body = ",\n".join(rendered)
    return f"@{entry_type(metadata)}{{{bibtex_key(node, metadata)},\n{body}\n}}\n", missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=Path, default=Path("data/kg/nodes.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/kg/publications.bib"))
    parser.add_argument("--report", type=Path, default=Path("data/kg/publications_bibtex_report.json"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    publications = [row for row in iter_jsonl(args.nodes) if row.get("type") == "publication"]
    entries: list[str] = []
    missing_report: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for node in publications:
        entry, missing = publication_to_bibtex(node)
        key = entry.split("{", 1)[1].split(",", 1)[0]
        if key in seen_keys:
            missing.append("unique_bibtex_key")
        seen_keys.add(key)
        entries.append(entry)
        if missing:
            missing_report.append(
                {
                    "node_id": node.get("id") or node.get("node_id"),
                    "label": node.get("label"),
                    "missing": missing,
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(entries), encoding="utf-8")
    args.report.write_text(
        json.dumps(
            {
                "publication_count": len(publications),
                "entries_written": len(entries),
                "nodes_with_missing_fields": len(missing_report),
                "missing": missing_report,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"wrote {len(entries)} BibTeX entries to {args.output}; "
        f"{len(missing_report)} nodes need metadata",
        file=sys.stderr,
    )
    return 1 if args.strict and missing_report else 0


if __name__ == "__main__":
    sys.exit(main())
