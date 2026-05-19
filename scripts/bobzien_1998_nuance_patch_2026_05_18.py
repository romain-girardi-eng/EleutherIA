#!/usr/bin/env python3
"""Bobzien 1998 nuance patch — 2026-05-18

Adds the §XII "volatility / absorption" framing to the description of
``pub_bobzien_1998_inadvertent`` and records an additional verified thesis
in its metadata.

Context: the existing description correctly states the §I "mix-up of
Aristotelian and Stoic thought" thesis but omits the §XII counterpoint
that the concept *develops by absorbing* Stoic / Peripatetic /
Middle-Platonist / Epictetan elements — explicitly framed as
"inadvertent conception" and "volatility", NOT as a deliberate
refinement driven by inter-school divergences.

Idempotent: re-running detects the nuance marker and exits without rewriting.
Snapshots data/kg/nodes.jsonl before mutation.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-bobzien-1998-nuance"

TARGET_ID = "pub_bobzien_1998_inadvertent"
# Marker must be a substring of NUANCE_PARAGRAPH for idempotence.
NUANCE_MARKER = "§XII (Volatility, p. 167-168)"

NUANCE_PARAGRAPH = (
    " §XII (Volatility, p. 167-168) precises the developmental mechanism: "
    "the concept of \"freedom to do otherwise\" develops by *absorbing* "
    "Stoic, Peripatetic, Middle-Platonist and Epictetan elements via "
    "Aristotle exegesis — explicitly framed as an INADVERTENT conception "
    "and a VOLATILITY of the concept, NOT as a deliberate refinement "
    "driven by inter-school divergences. Abstract (p. 133): \"It undergoes "
    "several developments, absorbing Epictetan, Middle-Platonist, and "
    "Peripatetic ideas.\" §XII (p. 167): \"We have now seen how this "
    "concept developed, absorbing both Stoic and Aristotelian and perhaps "
    "Platonic elements on its way.\" Bobzien further insists (p. 167-168) "
    "that even at Alexander's time the concept of freedom to do otherwise "
    "remains \"almost an isolated case, a rather marginal phenomenon "
    "without a clear philosophical context\"."
)

NEW_VERIFIED_THESIS = {
    "page": "133, 167-168",
    "thesis": (
        "Conceptual development is by inadvertent absorption "
        "(Stoic + Peripatetic + Middle-Platonist + Epictetan) via "
        "Aristotle exegesis, not by deliberate refinement through "
        "inter-school divergence (§I abstract + §XII Volatility)"
    ),
    "quote": (
        "this concept developed, absorbing both Stoic and Aristotelian "
        "and perhaps Platonic elements on its way (§XII, p. 167)"
    ),
    "marker": "§XII (Volatility)",
}


def load_raw_lines() -> list[str]:
    with NODES_PATH.open("r", encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh if line.strip()]


def node_id_of(line: str) -> str:
    n = json.loads(line)
    return n.get("id") or n.get("node_id") or ""


def dump_raw_lines(lines: list[str]) -> None:
    with NODES_PATH.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)


def main() -> int:
    lines = load_raw_lines()
    target_idx = next(
        (i for i, ln in enumerate(lines) if node_id_of(ln) == TARGET_ID),
        None,
    )
    if target_idx is None:
        print(f"ERROR: node {TARGET_ID} not found in {NODES_PATH}", file=sys.stderr)
        return 2

    target = json.loads(lines[target_idx])
    description = target.get("description") or ""
    if NUANCE_MARKER in description:
        print(f"OK: nuance already present on {TARGET_ID} — no-op")
        return 0

    snapshot()
    print(f"snapshot: {SNAPSHOT_DIR / NODES_PATH.name}")

    target["description"] = description.rstrip() + NUANCE_PARAGRAPH

    metadata = parse_metadata(target.get("metadata"))
    verified = list(metadata.get("verified_theses") or [])
    marker_tag = NEW_VERIFIED_THESIS["marker"]
    if not any(v.get("marker") == marker_tag for v in verified):
        verified.append(NEW_VERIFIED_THESIS)
    metadata["verified_theses"] = verified
    metadata["nuance_patch_2026_05_18"] = (
        "Added §XII volatility / absorption framing to balance the §I "
        "mix-up thesis; clarifies that development is by inadvertent "
        "absorption, not deliberate inter-school refinement"
    )
    target["metadata"] = json.dumps(metadata, ensure_ascii=False)
    target["updated_at"] = datetime.now(UTC).isoformat(sep=" ")

    # Only rewrite the target line — preserves byte-exact formatting of all
    # other nodes (some were stored compact, others spaced).
    lines[target_idx] = json.dumps(target, ensure_ascii=False)
    dump_raw_lines(lines)
    print(f"OK: patched {TARGET_ID} (+nuance paragraph, +1 verified_thesis)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
