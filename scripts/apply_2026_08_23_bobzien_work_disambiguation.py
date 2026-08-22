#!/usr/bin/env python3
"""Apply the Bobzien 1998/2001 work disambiguation (see the data module).

Dry-run by default; ``--write`` to apply. Backups of both files; idempotent
(``metadata.bobzien_disambiguation_2026_08_23`` stamp / already-applied state
is a no-op); every precondition re-checked at run time; edges keep
``source == source_id`` / ``target == target_id``; unchanged lines are written
back byte-for-byte. Report: data/audit/2026-08-23_bobzien_work_disambiguation_applied.md
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from data_2026_08_23_bobzien_work_disambiguation import (  # noqa: E402
    ARTICLE_ID,
    BOOK_ID,
    BOOK_NEW_LABEL,
    BOOK_OLD_LABEL,
    PAGE_FIXES,
    RELINK_NODE,
    WAVE_STAMP,
)

NODES = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES = ROOT / "data" / "kg" / "edges.jsonl"
REPORT = ROOT / "data" / "audit" / "2026-08-23_bobzien_work_disambiguation_applied.md"
SUFFIX = ".bak-bobzien-disambiguation"


def _load_md(node: dict) -> dict:
    md = node.get("metadata")
    if isinstance(md, str):
        try:
            md = json.loads(md)
        except json.JSONDecodeError:
            return {}
    return md if isinstance(md, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    node_lines = NODES.read_text(encoding="utf-8").splitlines(keepends=True)
    nodes = [json.loads(line) for line in node_lines]
    edge_lines = EDGES.read_text(encoding="utf-8").splitlines(keepends=True)
    edges = [json.loads(line) for line in edge_lines]

    actions: list[str] = []
    skips: list[str] = []
    touched_nodes: set[int] = set()
    touched_edges: set[int] = set()

    # 1. Relabel the monograph node.
    for i, n in enumerate(nodes):
        if n.get("id") != BOOK_ID:
            continue
        md = _load_md(n)
        if md.get(WAVE_STAMP):
            skips.append(f"{BOOK_ID}: already stamped (no-op)")
        elif n.get("label") != BOOK_OLD_LABEL:
            skips.append(f"{BOOK_ID}: label precondition no longer holds")
        else:
            n["label"] = BOOK_NEW_LABEL
            md["year"] = 2001
            md.setdefault("year_first_published", 1998)
            md[WAVE_STAMP] = True
            n["metadata"] = md
            touched_nodes.add(i)
            actions.append(f"relabel `{BOOK_ID}` -> \"{BOOK_NEW_LABEL}\" (year 2001)")
        break

    # 2. Relink the 375-412 node's advanced_in edge from article to monograph.
    relinked = False
    for i, e in enumerate(edges):
        if (
            e.get("source") == RELINK_NODE
            and e.get("relation") == "advanced_in"
            and e.get("target") == ARTICLE_ID
        ):
            if e.get("source") != e.get("source_id") or e.get("target") != e.get(
                "target_id"
            ):
                skips.append(f"relink: {RELINK_NODE} edge has source/target_id skew")
                break
            dup = any(
                x.get("source") == RELINK_NODE
                and x.get("relation") == "advanced_in"
                and x.get("target") == BOOK_ID
                for x in edges
            )
            if dup:
                skips.append("relink: advanced_in -> monograph already exists")
                break
            e["target"] = BOOK_ID
            e["target_id"] = BOOK_ID
            md = e.get("metadata")
            if not isinstance(md, dict):
                md = {}
            md[WAVE_STAMP] = True
            e["metadata"] = md
            touched_edges.add(i)
            relinked = True
            actions.append(
                f"relink `{RELINK_NODE}` advanced_in: article -> monograph "
                "(pp. 375-412 are the monograph's ch. 8)"
            )
            break
    if not relinked and not any(s.startswith("relink") for s in skips):
        already = any(
            e.get("source") == RELINK_NODE
            and e.get("relation") == "advanced_in"
            and e.get("target") == BOOK_ID
            for e in edges
        )
        skips.append(
            "relink: article edge absent"
            + (" (monograph edge already in place — no-op)" if already else "")
        )

    # 3-4. Page-range fixes.
    index = {n.get("id"): i for i, n in enumerate(nodes)}
    for fix in PAGE_FIXES:
        i = index.get(fix["node_id"])
        if i is None:
            skips.append(f"{fix['node_id']}: node absent")
            continue
        n = nodes[i]
        md = _load_md(n)
        if md.get("page_range") == fix["new_page_range"]:
            skips.append(f"{fix['node_id']}: already fixed (no-op)")
            continue
        if md.get("page_range") != fix["old_page_range"]:
            skips.append(f"{fix['node_id']}: page_range precondition no longer holds")
            continue
        md["page_range"] = fix["new_page_range"]
        md[WAVE_STAMP] = True
        n["metadata"] = md
        touched_nodes.add(i)
        actions.append(
            f"page_range `{fix['node_id']}`: "
            f"{fix['old_page_range']!r} -> {fix['new_page_range']!r}"
        )

    # Invariants.
    assert len(nodes) == len(node_lines) and len(edges) == len(edge_lines)
    for e in edges:
        assert e.get("source") == e.get("source_id"), "source/source_id skew"
        assert e.get("target") == e.get("target_id"), "target/target_id skew"
        assert e.get("source") != e.get("target"), "self-loop"

    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"[{mode}] actions={len(actions)} skips={len(skips)}")
    for a in actions:
        print(f"  + {a}")
    for s in skips:
        print(f"  ! {s}")

    if not args.write or not actions:
        if args.write:
            print("nothing to write")
        return 0

    shutil.copy2(NODES, str(NODES) + SUFFIX)
    shutil.copy2(EDGES, str(EDGES) + SUFFIX)

    def render(lines: list[str], rows: list[dict], touched: set[int]) -> str:
        out = []
        for i, (line, row) in enumerate(zip(lines, rows)):
            if i in touched:
                rendered = json.dumps(row, ensure_ascii=False)
                json.loads(rendered)
                out.append(rendered + ("\n" if line.endswith("\n") else ""))
            else:
                out.append(line)
        return "".join(out)

    NODES.write_text(render(node_lines, nodes, touched_nodes), encoding="utf-8")
    EDGES.write_text(render(edge_lines, edges, touched_edges), encoding="utf-8")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "# Bobzien 1998/2001 work disambiguation (applied 2026-08-23)",
        "",
        "Convention: Bobzien 1998 = the Phronesis article; Bobzien 2001 = the",
        "monograph *Determinism and Freedom in Stoic Philosophy* (first published",
        "1998, cited from the 2001 paperback; `year_first_published` kept).",
        "",
    ]
    body += [f"- {a}" for a in actions]
    if skips:
        body += ["", "Skipped:", ""] + [f"- {s}" for s in skips]
    REPORT.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"report -> {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
