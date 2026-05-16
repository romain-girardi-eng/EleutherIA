#!/usr/bin/env python3
"""Wave M — Anachronism hedging — 2026-05-16.

Two sub-tasks :

M1. **Modern terminology hedge** — Detect ancient KG nodes (``period``
   in the ancient set ; ``type`` in {argument, concept, synthesis,
   position, debate}) whose description mentions modern analytic
   philosophy of action vocabulary (compatibilism, libertarianism,
   incompatibilism, soft / hard determinism, agent causation,
   Frankfurt cases, manipulation argument, principle of alternative
   possibilities / PAP) WITHOUT a nearby methodological hedge.
   Prepend a ``**Avertissement méthodologique**`` block citing
   Frankfurt 1969, Kane 1996, Pereboom 2001 on the modern coinage
   and Bobzien 1998, Frede 2011, Sorabji 1980 on the retrospective
   projection onto ancient authors. Map the modern label back to
   the ancient term — ἑκούσιον, ἐφ' ἡμῖν, αὐτεξούσιον, liberum
   arbitrium — and cite Dihle 1982 and Frede 2011 for the
   historical thesis.

M2. **Pre-Origen "free will" hedge** — For nine specific
   audit-flagged pre-Origen nodes (Pharaoh hardening, Epicurean
   swerve, Cicero in nostra potestate, Middle Platonist conditional
   fate, Justin antifatalism / angel fall / prophecy freedom,
   Tatian, Irenaeus), prepend a ``**Avertissement conceptuel —
   anachronisme du « libre arbitre »**`` block stating the
   Dihle / Bobzien / Frede / Fürst thesis that the dogmatic
   category of « libre arbitre » (αὐτεξούσιον / liberum arbitrium)
   is an Origenian invention c. 230-250 CE — and that earlier
   references to ἑκούσιον, ἐφ' ἡμῖν, voluntas libera cover a
   partial, non-substitutive conceptual field.

Idempotency :

* M1 skips nodes whose description already starts with
  ``**Avertissement méthodologique**`` OR whose metadata flag
  ``m1_hedged_2026_05_16`` is true.
* M2 skips nodes whose description already starts with
  ``**Avertissement conceptuel — anachronisme du « libre arbitre »**``
  OR whose metadata flag ``m2_hedged_2026_05_16`` is true.
* A second run logs zero new prepensions.

Important schema note from Wave L : 111 / 177 synthesis nodes have
``node_id`` divergent from ``id``. RDF + edges use the ``id``
field. For M2 target resolution we look up by EITHER ``id`` or
``node_id`` so users can refer to the human-friendly handle.

Romain est seul auteur. Aucune mention de Claude / IA / Co-Author.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"

WAVE_TAG = "wave_m_anachronism_hedging_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")

# Ancient period set per Wave M spec (Patristic + earlier).
ANCIENT_PERIODS: frozenset[str] = frozenset(
    {
        "Presocratic",
        "Classical Greek",
        "Hellenistic",
        "Roman Republican",
        "Roman Imperial",
        "Late Antiquity",
        "Patristic",
        "Second Temple Judaism",
    }
)

# Pre-Origen subset — strictly earlier than Patristic in chronology.
# Patristic-flagged nodes that nonetheless predate Origen (e.g.
# Justin / Tatian / Irenaeus) are addressed explicitly via the
# nine-node allowlist below rather than the period filter, so this
# set is informational and not consulted in the main loop.
PRE_ORIGEN_PERIODS: frozenset[str] = frozenset(
    {
        "Presocratic",
        "Classical Greek",
        "Hellenistic",
        "Roman Republican",
        "Roman Imperial",
        "Second Temple Judaism",
    }
)

# Node types eligible for M1 scanning.
M1_TYPES: frozenset[str] = frozenset(
    {"argument", "concept", "synthesis", "position", "debate"}
)

# Modern philosophical terminology patterns flagged as anachronism
# when used unhedged on an ancient node. All case-insensitive,
# word-boundary anchored. Pattern matches are intentionally
# conservative — we hedge only obviously modern terms, not
# borderline "determinism" / "freedom" / "voluntary".
MODERN_TERM_PATTERNS: tuple[str, ...] = (
    r"\bcompatibili(?:sm|st|sme)\b",
    r"\blibertaria?ni(?:sm|st|sme)\b",
    r"\bincompatibili(?:sm|st|sme)\b",
    r"\bsoft[\s-]determini(?:sm|st|sme)\b",
    r"\bhard[\s-]determini(?:sm|st|sme)\b",
    r"\bagent[\s-]causation\b",
    r"\bFrankfurt[\s-]case",
    r"\bmanipulation[\s-]argument",
    r"\bprinciple of alternative possibilities\b",
    r"\bPAP\b",
)
MODERN_TERM_RE = re.compile("|".join(MODERN_TERM_PATTERNS), re.IGNORECASE)

# Phrases that count as an existing hedge ; if any of these is
# present in the description, the modern terminology is taken to
# already be flagged as such and we skip the node. Phase-12 audits
# from MEMORY already added several of these earlier.
HEDGE_PHRASES: tuple[str, ...] = (
    "ce que les chercheurs modernes désignent",
    "ce que les chercheurs modernes appellent",
    "ce que la philosophie analytique moderne",
    "modern scholars characterize as",
    "modern scholars term",
    "modern scholarly characterization",
    "rétroactivement",
    "rétrospectivement",
    "with modern terminology",
    "modern terminology",
    "Bobzien terms",
    "anachronism",
    "anachronique",
    "anachronistic",
    "Phase 12",
    "Avertissement méthodologique",
    "Avertissement conceptuel",
    "Avertissement conceptuel — anachronisme",
    "vocabulaire de la philosophie analytique",
    "characterized in modern scholarship",
    "characterized by modern scholars",
)
HEDGE_RE = re.compile(
    "|".join(re.escape(p) for p in HEDGE_PHRASES), re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Hedge blocks
# ---------------------------------------------------------------------------

HEDGE_M1 = (
    "**Avertissement méthodologique** : la terminologie « compatibiliste / "
    "libertarienne / agent-causation / etc. » employée ci-dessous appartient "
    "au vocabulaire de la philosophie analytique moderne (Frankfurt 1969, "
    "Kane 1996, Pereboom 2001). Ces étiquettes sont rétroactivement "
    "projetées sur la pensée antique par des chercheurs modernes "
    "(Bobzien 1998, Frede 2011, Sorabji 1980) pour cartographier la "
    "position d'un auteur ancien dans le débat contemporain. Le concept "
    "ancien correspondant — ἑκούσιον, ἐφ' ἡμῖν, αὐτεξούσιον, liberum "
    "arbitrium — précède de plusieurs siècles la formation du « problème "
    "du libre arbitre » au sens analytique. Cf. Dihle 1982, *The Theory "
    "of Will in Classical Antiquity* ; Frede 2011, *A Free Will: Origins "
    "of the Notion*. *(Phase 12)*\n\n"
)

HEDGE_M2 = (
    "**Avertissement conceptuel — anachronisme du « libre arbitre »** : "
    "la catégorie de « libre arbitre » (αὐτεξούσιον / liberum arbitrium) "
    "est, selon la thèse classique de Dihle 1982 — confirmée et nuancée "
    "par Bobzien 1998, Frede 2011, Fürst 2022 — une invention "
    "dogmatique chrétienne datant d'Origène (vers 230-250 ap. J.-C.). "
    "Les concepts anciens antérieurs — ἑκούσιον (volontaire) chez "
    "Aristote, ἐφ' ἡμῖν (ce qui dépend de nous) chez les Stoïciens et "
    "Académiques, voluntas libera chez Cicéron — recouvrent un champ "
    "conceptuel partiel et non-substitutif. Lorsque la présente "
    "description emploie « libre arbitre » / « free will » de manière "
    "apparemment naïve, il faut entendre une approximation lexicale "
    "moderne ; pour le contenu doctrinal exact de l'auteur ancien, voir "
    "le terme grec/latin propre. *(Phase 12)*\n\n"
)

HEDGE_M1_PREFIX = "**Avertissement méthodologique**"
HEDGE_M2_PREFIX = "**Avertissement conceptuel — anachronisme du « libre arbitre »**"


# Nine pre-Origen audit-flagged nodes (M2).
M2_TARGETS: frozenset[str] = frozenset(
    {
        "argument_divine_hardening_problem_y9z0a1b2",
        "argument_epicurean_swerve_for_freedom_m4n5o6p7",
        "concept_cic_fat_synthesis",
        "concept_conditional_fate_9a5c8b4d",
        "argument_justin_antifatalism",
        "argument_justin_angel_fall",
        "argument_justin_prophecy_freedom",
        "argument_tatian_freewill_paradox",
        "argument_irenaeus_recapitulation_theodicy",
    }
)


# ---------------------------------------------------------------------------
# IO helpers (mirrored from Wave J)
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    with NODES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_nodes(nodes: list[dict[str, Any]]) -> None:
    with NODES_PATH.open("w") as fh:
        for n in nodes:
            fh.write(json.dumps(n, ensure_ascii=False) + "\n")


def parse_metadata(raw: Any) -> tuple[dict[str, Any], bool]:
    """Return ``(metadata-dict, was_string)``."""
    if raw is None:
        return {}, False
    if isinstance(raw, str):
        try:
            obj = json.loads(raw) if raw.strip() else {}
            if not isinstance(obj, dict):
                obj = {}
            return obj, True
        except json.JSONDecodeError:
            return {}, True
    if isinstance(raw, dict):
        return dict(raw), False
    return {}, False


def reencode_metadata(
    node: dict[str, Any], md: dict[str, Any], was_string: bool
) -> None:
    raw = node.get("metadata")
    if was_string or isinstance(raw, str):
        node["metadata"] = json.dumps(md, ensure_ascii=False)
    else:
        node["metadata"] = md


def node_primary_id(n: dict[str, Any]) -> str:
    """Canonical node identifier (RDF + edges use ``id``)."""
    return n.get("id") or n.get("node_id") or ""


def node_matches_handle(n: dict[str, Any], handle: str) -> bool:
    """Match a target handle against either ``id`` or ``node_id``."""
    return n.get("id") == handle or n.get("node_id") == handle


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    if snap_nodes.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} - skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Audit / detection helpers
# ---------------------------------------------------------------------------


def has_modern_term(desc: str) -> bool:
    return bool(MODERN_TERM_RE.search(desc))


def has_hedge(desc: str) -> bool:
    return bool(HEDGE_RE.search(desc))


# ---------------------------------------------------------------------------
# Sub-task runners
# ---------------------------------------------------------------------------


def run_m1(nodes: list[dict[str, Any]]) -> tuple[int, int, int, int, list[tuple[str, str]]]:
    """Apply M1 hedge to ancient argument/concept/synthesis/position/debate
    nodes whose description uses unhedged modern terminology.

    Returns: ``(ancient_scanned, unhedged_found, hedge_prepended,
    skipped_already_hedged, touched_samples)`` — touched_samples is a
    list of ``(node_id, label)`` pairs (top-5 by description length).
    """
    ancient_scanned = 0
    unhedged_found = 0
    hedge_prepended = 0
    skipped_already_hedged = 0
    touched: list[tuple[str, str, int]] = []

    for n in nodes:
        if n.get("type") not in M1_TYPES:
            continue
        if n.get("period") not in ANCIENT_PERIODS:
            continue
        ancient_scanned += 1
        desc = n.get("description") or ""
        if not has_modern_term(desc):
            continue
        md, was_string = parse_metadata(n.get("metadata"))
        already_hedged_meta = md.get("m1_hedged_2026_05_16") is True
        already_hedged_prefix = desc.lstrip().startswith(HEDGE_M1_PREFIX)
        already_hedged_phrase = has_hedge(desc)
        if already_hedged_meta or already_hedged_prefix:
            skipped_already_hedged += 1
            continue
        if already_hedged_phrase:
            # description includes a hedge phrase elsewhere — count
            # as already-hedged, no double-prepend.
            skipped_already_hedged += 1
            continue
        # This is genuinely unhedged.
        unhedged_found += 1
        n["description"] = HEDGE_M1 + desc
        n["updated_at"] = NOW_ISO
        md["m1_hedged_2026_05_16"] = True
        md["wave"] = WAVE_TAG
        reencode_metadata(n, md, was_string)
        hedge_prepended += 1
        nid = node_primary_id(n)
        label = (n.get("label") or "")[:90]
        touched.append((nid, label, len(desc)))

    # Rank touched by original description length descending — these
    # are the highest-priority nodes (more affected text).
    touched.sort(key=lambda t: -t[2])
    samples = [(nid, label) for nid, label, _ in touched[:5]]
    return (
        ancient_scanned,
        unhedged_found,
        hedge_prepended,
        skipped_already_hedged,
        samples,
    )


def run_m2(nodes: list[dict[str, Any]]) -> tuple[int, int, int, list[tuple[str, str]]]:
    """Apply M2 hedge to the 9 pre-Origen audit-flagged nodes.

    Returns: ``(present_in_kg, hedge_prepended, skipped_already_hedged,
    touched_samples)``.
    """
    present_in_kg = 0
    hedge_prepended = 0
    skipped_already_hedged = 0
    touched: list[tuple[str, str]] = []

    targets_remaining = set(M2_TARGETS)
    for n in nodes:
        if not targets_remaining:
            break
        matched_handle: str | None = None
        for handle in targets_remaining:
            if node_matches_handle(n, handle):
                matched_handle = handle
                break
        if matched_handle is None:
            continue
        targets_remaining.discard(matched_handle)
        present_in_kg += 1
        desc = n.get("description") or ""
        md, was_string = parse_metadata(n.get("metadata"))
        already_hedged_meta = md.get("m2_hedged_2026_05_16") is True
        already_hedged_prefix = desc.lstrip().startswith(HEDGE_M2_PREFIX)
        if already_hedged_meta or already_hedged_prefix:
            skipped_already_hedged += 1
            continue
        n["description"] = HEDGE_M2 + desc
        n["updated_at"] = NOW_ISO
        md["m2_hedged_2026_05_16"] = True
        md["wave"] = WAVE_TAG
        reencode_metadata(n, md, was_string)
        hedge_prepended += 1
        touched.append((node_primary_id(n), (n.get("label") or "")[:90]))

    if targets_remaining:
        print(
            f"[wave-m] WARNING: {len(targets_remaining)} M2 target(s) "
            f"not found in KG: {sorted(targets_remaining)}"
        )

    return present_in_kg, hedge_prepended, skipped_already_hedged, touched


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-m] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    print(f"[load] nodes={len(nodes):,}")

    (
        m1_scanned,
        m1_unhedged,
        m1_prepended,
        m1_skipped,
        m1_samples,
    ) = run_m1(nodes)
    print(
        f"[wave-m] m1_ancient_scanned={m1_scanned}  "
        f"m1_unhedged_found={m1_unhedged}  "
        f"m1_hedge_prepended={m1_prepended}  "
        f"m1_skipped_already_hedged={m1_skipped}"
    )
    if m1_samples:
        print("[wave-m] M1 top-5 touched (by original description length desc):")
        for nid, label in m1_samples:
            print(f"  - {nid:<70} {label}")

    m2_present, m2_prepended, m2_skipped, m2_samples = run_m2(nodes)
    print(
        f"[wave-m] m2_pre_origen_audit_listed={len(M2_TARGETS)}  "
        f"m2_present_in_kg={m2_present}  "
        f"m2_hedge_prepended={m2_prepended}  "
        f"m2_skipped_already_hedged={m2_skipped}"
    )
    if m2_samples:
        print("[wave-m] M2 touched nodes (order of traversal):")
        for nid, label in m2_samples[:5]:
            print(f"  - {nid:<70} {label}")

    if m1_prepended or m2_prepended:
        write_nodes(nodes)
        print(f"[write] nodes={len(nodes):,}")
    else:
        print("[write] no changes - file untouched")

    return 0


if __name__ == "__main__":
    sys.exit(main())
