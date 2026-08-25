#!/usr/bin/env python3
"""HOW: restore the transmitted Greek in two Aristotle passage nodes.

Dry-run by default. Pass --write to touch anything.

Preconditions are re-proved at run time against the local TLG E corpus, not
trusted from the data module: each replacement must be attested and each
stored string must be unattested. If TLG E is unavailable the script REFUSES
to run rather than writing Greek it cannot check — the whole point of the
repair is that nothing goes in unverified.

Usage:
    PYTHONPATH=. python3 scripts/apply_2026_08_26_aristotle_en_iii_readings.py
    PYTHONPATH=. python3 scripts/apply_2026_08_26_aristotle_en_iii_readings.py --write
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from scripts.data_2026_08_26_aristotle_en_iii_readings import (
    BEKKER_FLAG,
    LEFT_ALONE,
    METADATA_STAMP,
    REPAIRS,
    TLG_AUTHOR,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
TLG_SEARCH = ROOT / "scripts" / "tlg_search.py"
SLUG = "aristotle_en_iii_readings_2026_08_26"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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


def tlg_hits(greek: str) -> int | None:
    """Number of TLG E hits, or None when the corpus is unavailable."""
    needle = greek.strip().rstrip(".·;")
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(TLG_SEARCH),
                "search",
                needle,
                "--authors",
                TLG_AUTHOR,
                "--max",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except OSError, subprocess.SubprocessError:
        return None
    if proc.returncode not in (0, 1):
        return None
    # tlg_search prints its `#` diagnostics (including "total hits: 0") on
    # stderr and its hits on stdout, so both have to be read. Reading only
    # stdout made a genuine zero-hit answer indistinguishable from "the corpus
    # is missing" — which would have turned a proved fabrication into a
    # refusal to act.
    for line in (proc.stdout + "\n" + proc.stderr).splitlines():
        if line.startswith("TLG"):
            return 1
        if "total hits:" in line:
            return int(line.rsplit(":", 1)[1].strip())
    return None


def prove_evidence() -> list[str]:
    """Re-prove every claim the repair rests on. Empty list means sound."""
    failures: list[str] = []
    for repair in REPAIRS:
        attested = tlg_hits(repair["attested"])
        stored = tlg_hits(repair["stored"])
        if attested is None or stored is None:
            failures.append(
                f"{repair['node_id']}: TLG E unavailable — refusing to write Greek "
                "that cannot be checked"
            )
            continue
        if attested < 1:
            failures.append(
                f"{repair['node_id']}: replacement NOT attested in TLG{TLG_AUTHOR}"
            )
        if stored > 0:
            failures.append(
                f"{repair['node_id']}: the stored reading IS attested after all — "
                "re-examine before replacing it"
            )
    return failures


def transform(
    nodes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    out: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    skipped: list[str] = []
    by_id = {r["node_id"]: r for r in REPAIRS}

    for node in nodes:
        nid = node_id(node)
        repair = by_id.get(nid)
        if repair is None:
            out.append(node)
            continue
        node = copy.deepcopy(node)
        description = node.get("description") or ""
        if repair["stored"] not in description:
            if repair["attested"] in description:
                skipped.append(f"{nid}: already applied")
            else:
                skipped.append(f"{nid}: stored reading not found as declared")
            out.append(node)
            continue

        node["description"] = description.replace(
            repair["stored"], repair["attested"], 1
        )
        meta = metadata(node)
        meta[METADATA_STAMP] = {
            "replaced": repair["stored"],
            "with": repair["attested"],
            "attestation": repair["attestation"],
            "note": (
                "The stored Greek was unattested: a genuine Aristotelian clause "
                "with a rewritten opening. Replacement copied verbatim from the "
                "TLG E hit named above; nothing was composed."
            ),
        }
        meta["attestation_type"] = "tlg_verbatim"
        if not repair["bekker_ok"]:
            meta["bekker_reference_unverified"] = BEKKER_FLAG
        set_metadata(node, meta)
        changed.append({"node_id": nid, "attestation": repair["attestation"]})
        out.append(node)

    return out, changed, skipped


def assert_invariants(
    before: list[dict[str, Any]], after: list[dict[str, Any]]
) -> None:
    assert len(before) == len(after), "node count changed"
    assert [node_id(n) for n in before] == [node_id(n) for n in after], (
        "node ids or order changed"
    )
    wanted = {r["node_id"]: r for r in REPAIRS}
    for node in after:
        nid = node_id(node)
        if nid in wanted:
            description = node.get("description") or ""
            assert wanted[nid]["stored"] not in description, (
                f"unattested reading survived in {nid}"
            )
            assert wanted[nid]["attested"] in description, (
                f"transmitted reading missing from {nid}"
            )
        # The two genuine nodes in the same cohort must be untouched.
        if nid in LEFT_ALONE:
            original = next(n for n in before if node_id(n) == nid)
            assert node == original, f"{nid} was verified genuine and must not change"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)

    print("Aristotle EN III reading repair —", SLUG)
    print("mode:", "WRITE" if args.write else "DRY-RUN")

    nodes_path = args.data_root.expanduser().resolve() / "kg/nodes.jsonl"
    original = read_jsonl(nodes_path)
    updated, changed, skipped = transform(original)

    if changed:
        failures = prove_evidence()
        if failures:
            print("PRECONDITION FAILURES — refusing to write:")
            for failure in failures:
                print("  -", failure)
            return 1
        print("TLG E evidence re-proved: replacements attested, stored readings not")

    assert_invariants(original, updated)
    print("nodes changed:", len(changed))
    for entry in skipped:
        print("  skip:", entry)
    print("verified genuine and left alone:", ", ".join(sorted(LEFT_ALONE)))

    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("already applied: no files written")
        return 0

    backup = nodes_path.with_suffix(f".jsonl.bak-{SLUG}")
    shutil.copy2(nodes_path, backup)
    write_jsonl(nodes_path, updated)

    report_dir = args.data_root / "audit"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "2026-08-26_aristotle_en_iii_readings.json"
    report.write_text(
        json.dumps(
            {
                "slug": SLUG,
                "changed": changed,
                "skipped": skipped,
                "left_alone_verified_genuine": LEFT_ALONE,
                "repairs": REPAIRS,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print("backup:", backup)
    print("wrote:", nodes_path, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
