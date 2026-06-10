"""kg_work_id integrity gate: one KG work node must map to ONE canonical work.

The bug this guards against: several distinct corpus works sharing a single
kg_work_id, e.g. Plato's Apology passages (tlg0059.tlg002) hanging under
`work_republic_plato_c380bce_c3d4e5f6`. Retrieval then silently returns the
wrong work's text.

Offline mode (default, used in CI) reads the committed KG exports:
- data/kg/nodes.jsonl   (passage nodes carry metadata.work_canonical_id,
  metadata.author, metadata.work_title)
- data/kg/edges.jsonl   (`part_of` passage -> work edges)

A collision = one KG work node whose `part_of` passages span >1 distinct
`work_canonical_id`. The DB column free_will.ancient_works.kg_work_id is not
exported locally, so the DB-side grouping (kg_work_id shared by several
ancient_works rows) is only available in --db mode (env-gated, read-only).

Exit policy (CI-friendly):
- known collisions listed in the committed allowlist -> warning, exit 0
- any NEW collision (new work node, or new member work in a known group) -> exit 1
- --strict: exit 1 on ANY collision, allowlist ignored
- --write-allowlist / --report regenerate the committed artifacts

Usage:
    python scripts/check_kg_work_id_uniqueness.py
    python scripts/check_kg_work_id_uniqueness.py --strict
    python scripts/check_kg_work_id_uniqueness.py --write-allowlist --report
    DATABASE_URL=... python scripts/check_kg_work_id_uniqueness.py --db
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
ALLOWLIST_PATH = ROOT / "data" / "audit" / "kg_work_id_known_collisions.json"
REPORT_PATH = ROOT / "data" / "audit" / "kg_work_id_collisions_report.md"


def parse_metadata(value: Any) -> dict[str, Any]:
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
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def collect_work_groups(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> dict[str, dict[str, dict[str, Any]]]:
    """Group passage nodes under their `part_of` work node.

    Returns {work_node_id: {work_canonical_id: {count, authors, titles}}}
    where authors/titles are Counters over the member passages' metadata.
    """
    by_id: dict[str, dict[str, Any]] = {}
    for n in nodes:
        nid = str(n.get("id") or n.get("node_id") or "")
        if nid:
            by_id[nid] = n

    groups: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for e in edges:
        if e.get("relation") != "part_of":
            continue
        src = str(e.get("source") or e.get("source_id") or "")
        tgt = str(e.get("target") or e.get("target_id") or "")
        sn, tn = by_id.get(src), by_id.get(tgt)
        if not sn or not tn:
            continue
        if sn.get("type") != "passage" or tn.get("type") != "work":
            continue
        meta = parse_metadata(sn.get("metadata"))
        wcid = str(meta.get("work_canonical_id") or "").strip()
        if not wcid:
            continue
        member = groups[tgt].setdefault(
            wcid, {"count": 0, "authors": Counter(), "titles": Counter()}
        )
        member["count"] += 1
        if meta.get("author"):
            member["authors"][str(meta["author"])] += 1
        if meta.get("work_title"):
            member["titles"][str(meta["work_title"])] += 1
    return groups


def find_collisions(
    groups: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """A collision = one kg work node claimed by >1 distinct canonical works."""
    collisions = []
    for work_node_id in sorted(groups):
        members = groups[work_node_id]
        if len(members) <= 1:
            continue
        out_members = []
        for wcid in sorted(members):
            m = members[wcid]
            authors = m["authors"].most_common(1)
            titles = m["titles"].most_common(1)
            out_members.append(
                {
                    "work_canonical_id": wcid,
                    "passages": m["count"],
                    "author": authors[0][0] if authors else None,
                    "title": titles[0][0] if titles else None,
                }
            )
        collisions.append({"kg_work_id": work_node_id, "members": out_members})
    return collisions


def split_known_new(
    collisions: list[dict[str, Any]], allowlist: dict[str, list[str]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """A collision is known only if its kg_work_id is allowlisted AND its member
    works are a subset of the allowlisted members (a new member = new collision)."""
    known, new = [], []
    for c in collisions:
        allowed = set(allowlist.get(c["kg_work_id"], []))
        members = {m["work_canonical_id"] for m in c["members"]}
        (known if allowed and members <= allowed else new).append(c)
    return known, new


def load_allowlist(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    groups = data.get("collisions", data) if isinstance(data, dict) else {}
    return {str(k): [str(v) for v in vals] for k, vals in groups.items()}


def write_allowlist(collisions: list[dict[str, Any]], path: Path) -> None:
    payload = {
        "_comment": (
            "Known kg_work_id collisions (one KG work node claimed by several "
            "distinct corpus works). CI warns on these but hard-fails on any "
            "collision NOT in this list. Shrink this file as works are "
            "remediated; never grow it without a scholarly review."
        ),
        "generated_by": "scripts/check_kg_work_id_uniqueness.py --write-allowlist",
        "collisions": {
            c["kg_work_id"]: sorted(m["work_canonical_id"] for m in c["members"])
            for c in collisions
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render_report(collisions: list[dict[str, Any]]) -> str:
    lines = [
        "# kg_work_id collision report",
        "",
        "One KG work node claimed by several distinct corpus works "
        "(`work_canonical_id` of its `part_of` passages). Each group below "
        "needs manual per-work remediation: keep the passages that truly "
        "belong to the work node, re-home the rest under their own work node, "
        "then remove the group from "
        "`data/audit/kg_work_id_known_collisions.json`.",
        "",
        "Generated read-only by `scripts/check_kg_work_id_uniqueness.py "
        "--report` from `data/kg/nodes.jsonl` + `data/kg/edges.jsonl`.",
        "",
        f"**Colliding KG work nodes: {len(collisions)}**",
        "",
    ]
    for c in collisions:
        lines.append(f"## `{c['kg_work_id']}`")
        lines.append("")
        lines.append("| work_canonical_id | author | title | passages |")
        lines.append("|---|---|---|---|")
        for m in c["members"]:
            lines.append(
                f"| `{m['work_canonical_id']}` | {m['author'] or '?'} "
                f"| {m['title'] or '?'} | {m['passages']} |"
            )
        lines.append("")
    return "\n".join(lines)


async def fetch_db_collisions(database_url: str) -> list[dict[str, Any]]:
    """DB-side grouping: several free_will.ancient_works rows sharing one
    kg_work_id. Read-only SELECT; requires DATABASE_URL (env-gated)."""
    import asyncpg  # optional dependency, db mode only

    conn = await asyncpg.connect(database_url)
    try:
        rows = await conn.fetch(
            """
            SELECT w.kg_work_id, w.canonical_id, w.title, w.author,
                   (SELECT count(*) FROM free_will.passages p
                    WHERE p.work_id = w.work_id) AS passages
            FROM free_will.ancient_works w
            WHERE w.kg_work_id IS NOT NULL
              AND w.kg_work_id IN (
                SELECT kg_work_id FROM free_will.ancient_works
                WHERE kg_work_id IS NOT NULL
                GROUP BY kg_work_id
                HAVING count(DISTINCT work_id) > 1
              )
            ORDER BY w.kg_work_id, w.canonical_id
            """
        )
    finally:
        await conn.close()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        grouped[r["kg_work_id"]].append(
            {
                "work_canonical_id": r["canonical_id"],
                "passages": r["passages"],
                "author": r["author"],
                "title": r["title"],
            }
        )
    return [
        {"kg_work_id": k, "members": grouped[k]} for k in sorted(grouped)
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", action="store_true",
                    help="check the live DB (requires DATABASE_URL) instead of "
                         "the committed JSONL exports")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on ANY collision, ignoring the allowlist")
    ap.add_argument("--allowlist", type=Path, default=ALLOWLIST_PATH)
    ap.add_argument("--write-allowlist", action="store_true",
                    help="regenerate the known-collisions allowlist")
    ap.add_argument("--report", nargs="?", type=Path, const=REPORT_PATH,
                    default=None, metavar="PATH",
                    help="write the markdown remediation report "
                         f"(default {REPORT_PATH.relative_to(ROOT)})")
    args = ap.parse_args(argv)

    if args.db:
        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            print("--db requires DATABASE_URL in the environment", file=sys.stderr)
            return 2
        import asyncio

        collisions = asyncio.run(fetch_db_collisions(database_url))
        source = "free_will.ancient_works (live DB)"
    else:
        nodes = list(iter_jsonl(NODES_PATH))
        edges = list(iter_jsonl(EDGES_PATH))
        collisions = find_collisions(collect_work_groups(nodes, edges))
        source = "data/kg/nodes.jsonl + data/kg/edges.jsonl"

    if args.write_allowlist:
        write_allowlist(collisions, args.allowlist)
        print(f"allowlist written: {args.allowlist} ({len(collisions)} groups)")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_report(collisions), encoding="utf-8")
        print(f"report written: {args.report}")

    print(f"source: {source}")
    print(f"colliding kg_work_id groups: {len(collisions)}")
    if not collisions:
        print("OK: every kg_work_id maps to a single canonical work")
        return 0

    allowlist = {} if args.strict else load_allowlist(args.allowlist)
    known, new = split_known_new(collisions, allowlist)

    for label, items in (("KNOWN (allowlisted)", known), ("NEW", new)):
        if not items:
            continue
        print(f"\n{label}: {len(items)} group(s)")
        for c in items:
            print(f"  {c['kg_work_id']}")
            for m in c["members"]:
                print(
                    f"    - {m['work_canonical_id']} "
                    f"({m['author'] or '?'}, {m['title'] or '?'}, "
                    f"{m['passages']} passages)"
                )

    if new:
        allowlist_path = args.allowlist
        if allowlist_path.is_relative_to(ROOT):
            allowlist_path = allowlist_path.relative_to(ROOT)
        print(f"\nFAIL: {len(new)} collision group(s) not in the allowlist "
              f"({allowlist_path})")
        return 1
    print("\nWARN: only known (allowlisted) collisions present — "
          "remediation pending, not blocking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
