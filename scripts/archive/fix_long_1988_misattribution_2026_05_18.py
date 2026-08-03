#!/usr/bin/env python3
"""Fix Long 1988 'Discovering the Will' misattribution — 2026-05-18.

CONTEXT
-------
Phase B dedupe (2026-05-18) flagged ``pub_long_1988_discovering_will`` AMBIGUOUS
because its label/desc claim "Discovering the Will: From Aristotle to Augustine
(Long)". That title is **Charles H. Kahn's** chapter 9 in:

    Dillon, J. M. & Long, A. A. (eds.), *The Question of "Eclecticism": Studies
    in Later Greek Philosophy*, Hellenistic Culture & Society 3, University of
    California Press, 1988, pp. 234-259. DOI 10.1525/9780520317611-014.

A. A. Long was *co-editor* of the volume, **not author** of that chapter. The
canonical chapter node already exists as ``pub_kahn_1988_discovering_will``
(rich metadata, 5 verified_critiques from local PDF, full edition info, DOI).

EVIDENCE (verified 2026-05-18)
------------------------------
1. A. A. Long, canonical bibliography 1963-2009 (Cambridge UP, *Ancient Models
   of Mind*, Cambridge Companions): his only 1988 publications are
     (1988a) "Reply to Jonathan Barnes, 'Epicurean signs'," OSAP suppl. 135-44
     (1988b) "Socrates in Hellenistic philosophy," CQ 38: 150-71
   NO publication titled "Discovering the Will".
   URL: https://www.cambridge.org/core/books/abs/ancient-models-of-mind/
        a-long-publications-19632009/5B59FFC2C301473975FCD72BDFB164A7
2. PhilPapers KAHDWA, Semantic Scholar, De Gruyter/Brill (DOI
   10.1525/9780520317611-014): all attribute the chapter to Charles H. Kahn.
3. The canonical node ``pub_kahn_1988_discovering_will`` already carries the
   correct ``authored_by → scholar_kahn_charles`` edge (edge_id
   c4f054d2-6f64-424b-9043-7723353f6abb).

DECISION
--------
MISATTRIBUTION. The shell ``pub_long_1988_discovering_will`` is not a real
publication — it is the same Kahn chapter, incorrectly attributed to A. A. Long
(presumably because Long appears on the volume's spine as co-editor).

ACTIONS
-------
1. Snapshot ``data/kg/{nodes,edges}.jsonl`` to
   ``data/kg/snapshots/2026-05-18-pre-long-misattrib-fix/``.
2. Inspect the shell's only incident edge:
       pub_long_1988_discovering_will --authored_by--> scholar_long_anthony
   This edge is itself the misattribution. We DROP it (we do NOT redirect it,
   because that would yield ``pub_kahn → scholar_long``, which is also false).
3. Mark the shell deprecated, wrong_attribution=true, superseded_by canonical
   Kahn node. Shell is KEPT in JSONL (preserves any external citation by ID).

IDEMPOTENCY
-----------
- If shell already carries metadata.deprecated=true with this fix marker, the
  script is a no-op and reports it.
- If the shell's incident edge has already been removed, it's not re-removed.
- Re-running with --commit after a successful run is a no-op.

DRY-RUN by default. Pass ``--commit`` to write to disk.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = REPO_ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-long-misattrib-fix"

PATCH_MARKER = "long_1988_misattrib_fix_2026_05_18"
FIX_DATE = "2026-05-18"

SHELL_ID = "pub_long_1988_discovering_will"
CANONICAL_ID = "pub_kahn_1988_discovering_will"
WRONG_AUTHOR_ID = "scholar_long_anthony"  # the misattributed authored_by target


# -----------------------------------------------------------------------------
# Helpers (consistent with scripts/fix_phase_b_dedupe_publications_2026_05_18.py)
# -----------------------------------------------------------------------------


def parse_metadata(node: dict[str, Any]) -> dict[str, Any]:
    md = node.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    try:
        return json.loads(md)
    except (json.JSONDecodeError, TypeError):
        return {}


def serialise_metadata(node: dict[str, Any], md: dict[str, Any]) -> None:
    node["metadata"] = json.dumps(md, ensure_ascii=False)


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if not (SNAPSHOT_DIR / NODES_PATH.name).exists():
        shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    if not (SNAPSHOT_DIR / EDGES_PATH.name).exists():
        shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)


def load_node_lines() -> list[str]:
    return NODES_PATH.read_text(encoding="utf-8").splitlines()


def load_edge_lines() -> list[str]:
    return EDGES_PATH.read_text(encoding="utf-8").splitlines()


def edge_touches_shell(edge: dict[str, Any]) -> bool:
    return SHELL_ID in (
        edge.get("source"),
        edge.get("source_id"),
        edge.get("target"),
        edge.get("target_id"),
    )


# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------


def run(commit: bool) -> int:
    if not NODES_PATH.exists() or not EDGES_PATH.exists():
        print(f"ERROR: missing {NODES_PATH} or {EDGES_PATH}", file=sys.stderr)
        return 2

    print(
        f"Long 1988 misattribution fix — {'COMMIT' if commit else 'DRY-RUN'} "
        f"— {FIX_DATE}\n"
    )

    node_lines = load_node_lines()
    edge_lines = load_edge_lines()

    # ---- Locate shell + canonical ----
    shell_idx: int | None = None
    canonical_idx: int | None = None
    shell_node: dict[str, Any] | None = None
    canonical_node: dict[str, Any] | None = None

    for i, line in enumerate(node_lines):
        if not line.strip():
            continue
        try:
            n = json.loads(line)
        except json.JSONDecodeError:
            continue
        nid = n.get("id") or n.get("node_id")
        if nid == SHELL_ID:
            shell_idx, shell_node = i, n
        elif nid == CANONICAL_ID:
            canonical_idx, canonical_node = i, n

    if shell_node is None or shell_idx is None:
        print(f"ERROR: shell node {SHELL_ID} not found.", file=sys.stderr)
        return 2
    if canonical_node is None or canonical_idx is None:
        print(f"ERROR: canonical node {CANONICAL_ID} not found.", file=sys.stderr)
        return 2

    shell_md = parse_metadata(shell_node)
    already_done = bool(shell_md.get(PATCH_MARKER)) and bool(shell_md.get("deprecated"))

    # ---- Locate incident edges ----
    incident_indices: list[int] = []
    drop_indices: list[int] = []  # edges we will drop outright
    redirect_indices: list[int] = []  # edges to redirect to canonical

    for i, line in enumerate(edge_lines):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not edge_touches_shell(e):
            continue
        incident_indices.append(i)

        relation = e.get("relation")
        src = e.get("source") or e.get("source_id")
        tgt = e.get("target") or e.get("target_id")

        # The misattribution: SHELL --authored_by--> scholar_long_anthony
        # Dropping (not redirecting) — Long did NOT author this chapter.
        if (
            src == SHELL_ID
            and tgt == WRONG_AUTHOR_ID
            and relation == "authored_by"
        ):
            drop_indices.append(i)
        else:
            # Any other incident edge: it concerns the *publication itself*
            # (e.g. citations of the chapter, topical edges). Those facts about
            # the chapter remain true — redirect the endpoint to the real Kahn
            # node so the claim is preserved.
            redirect_indices.append(i)

    # ---- Report ----
    print(f"Shell node:     {SHELL_ID}")
    print(f"  label:        {shell_node.get('label')!r}")
    print(f"  description:  {shell_node.get('description')!r}")
    print(f"  already deprecated w/ this fix marker? {already_done}")
    print()
    print(f"Canonical node: {CANONICAL_ID}")
    print(f"  label:        {canonical_node.get('label')!r}")
    print()
    print(f"Incident edges on shell: {len(incident_indices)}")
    for i in incident_indices:
        e = json.loads(edge_lines[i])
        src = e.get("source") or e.get("source_id")
        tgt = e.get("target") or e.get("target_id")
        rel = e.get("relation")
        action = (
            "DROP (misattribution)"
            if i in drop_indices
            else f"REDIRECT endpoint to {CANONICAL_ID}"
        )
        print(f"  {src} --{rel}--> {tgt}    [{action}]")
    print()

    if already_done and not incident_indices:
        print("Idempotent no-op — shell already deprecated, no incident edges remain.")
        return 0

    if not commit:
        print("[DRY-RUN] No files modified. Re-run with --commit to apply.")
        return 0

    # ---- Snapshot ----
    snapshot()
    print(f"Snapshot written to {SNAPSHOT_DIR}\n")

    # ---- Mutate edges: build a new list (drops + redirects) ----
    new_edge_lines: list[str] = []
    redirected_count = 0
    dropped_count = 0

    # Pre-compute existing canonical edge signatures for dedup on redirect
    canon_sigs: set[tuple[str, str, str]] = set()
    for line in edge_lines:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        src = e.get("source") or e.get("source_id") or ""
        tgt = e.get("target") or e.get("target_id") or ""
        rel = e.get("relation") or ""
        if CANONICAL_ID in (src, tgt):
            canon_sigs.add((src, tgt, rel))

    for i, line in enumerate(edge_lines):
        if not line.strip():
            new_edge_lines.append(line)
            continue
        if i in drop_indices:
            dropped_count += 1
            continue
        if i in redirect_indices:
            e = json.loads(line)
            for f in ("source", "source_id"):
                if e.get(f) == SHELL_ID:
                    e[f] = CANONICAL_ID
            for f in ("target", "target_id"):
                if e.get(f) == SHELL_ID:
                    e[f] = CANONICAL_ID
            new_src = e.get("source") or e.get("source_id") or ""
            new_tgt = e.get("target") or e.get("target_id") or ""
            new_rel = e.get("relation") or ""
            new_sig = (new_src, new_tgt, new_rel)
            # Drop self-loop or duplicate-of-canonical
            if new_src == new_tgt:
                dropped_count += 1
                continue
            if new_sig in canon_sigs:
                dropped_count += 1
                continue
            canon_sigs.add(new_sig)
            new_edge_lines.append(json.dumps(e, ensure_ascii=False))
            redirected_count += 1
        else:
            new_edge_lines.append(line)

    # ---- Mutate shell node ----
    shell_md["deprecated"] = True
    shell_md["deprecated_at"] = FIX_DATE
    shell_md["wrong_attribution"] = True
    shell_md["wrong_attribution_reason"] = (
        "Label/desc claim 'Discovering the Will: From Aristotle to Augustine' "
        "by A. A. Long, but this is Charles H. Kahn's chapter 9 in Dillon & "
        "Long (eds.), The Question of 'Eclecticism' (UC Press, 1988), pp. "
        "234-259. A. A. Long was co-editor of the volume, not author of this "
        "chapter. Verified against A. A. Long's canonical 1963-2009 "
        "bibliography (Cambridge UP, Ancient Models of Mind): his 1988 "
        "publications are only the OSAP Epicurean-signs reply and the CQ "
        "'Socrates in Hellenistic philosophy' article. The chapter is "
        "consistently attributed to Kahn by PhilPapers (KAHDWA), Semantic "
        "Scholar, and De Gruyter/Brill (DOI 10.1525/9780520317611-014)."
    )
    shell_md["superseded_by"] = CANONICAL_ID
    shell_md[PATCH_MARKER] = True
    shell_md["misattrib_fix_at"] = FIX_DATE
    serialise_metadata(shell_node, shell_md)
    node_lines[shell_idx] = json.dumps(shell_node, ensure_ascii=False)

    # ---- Stamp canonical node so the merge is traceable from either side ----
    canon_md = parse_metadata(canonical_node)
    merged_in = canon_md.get("merged_in") or []
    if not isinstance(merged_in, list):
        merged_in = [merged_in]
    if SHELL_ID not in merged_in:
        merged_in.append(SHELL_ID)
    canon_md["merged_in"] = merged_in
    canon_md[PATCH_MARKER] = True
    canon_md["misattrib_fix_at"] = FIX_DATE
    serialise_metadata(canonical_node, canon_md)
    node_lines[canonical_idx] = json.dumps(canonical_node, ensure_ascii=False)

    # ---- Write ----
    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    EDGES_PATH.write_text("\n".join(new_edge_lines) + "\n", encoding="utf-8")

    print(f"Edges redirected: {redirected_count}")
    print(f"Edges dropped:    {dropped_count}")
    print("Shell node:       deprecated + wrong_attribution flagged")
    print("Canonical node:   merged_in updated")
    print("\nDone.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--commit", action="store_true", help="Write changes to disk")
    args = p.parse_args()
    return run(commit=args.commit)


if __name__ == "__main__":
    sys.exit(main())
