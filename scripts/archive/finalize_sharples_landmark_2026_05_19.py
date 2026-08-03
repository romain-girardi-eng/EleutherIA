#!/usr/bin/env python3
"""
finalize_sharples_landmark_2026_05_19.py

Two tasks, both idempotent:

Task A — create the Sharples-vs-Frede landmark scholarly position node
  id: scholarly_position_sharples_alexander_libertarian_unsupported
  + 5 edges (created_by, discusses, critiques, 2x discusses from publications)

Task B — re-wire 4 Sharples args mis-attributed to Sharples 1983 (Duckworth)
  Per data/kg/e2_patches/sharples.json wrong_source_suspicion field:
    free_will_and_determinism_in_a_1   -> pub_sharples_2008_accident_determinisme
    historical_determinism_0           -> pub_sharples_2008_accident_determinisme
    tension_between_neglect_and_de_3   -> pub_sharples_1982_providence  (+ flag missing Vigiliae node)
    the_tetralemma_argument_5          -> pub_sharples_1991_cicero_boethius

Snapshot mandatory. --commit required to write.
Re-run is no-op.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("[local-path]")
KG = ROOT / "data" / "kg"
NODES_PATH = KG / "nodes.jsonl"
EDGES_PATH = KG / "edges.jsonl"
SNAP_DIR = KG / "snapshots" / "2026-05-19-pre-sharples-finalize"

WAVE = "sharples_landmark_finalize_2026_05_19"
NOW = "2026-05-19T00:00:00+00:00"

# --- Task A: new landmark node ---------------------------------------------

NEW_NODE_ID = "scholarly_position_sharples_alexander_libertarian_unsupported"

NEW_NODE_DESCRIPTION = (
    "La position centrale de R. W. Sharples dans son commentaire De Fato (Duckworth 1983) "
    "distingue ce qu'Alexandre stipule (« Alexander's own conception of responsibility is a "
    "libertarian one », p. 22) de ce qu'il démontre philosophiquement (très peu). Au commentaire "
    "p. 141, Sharples écrit : « Alexander is wrong to assume that determinism implies that "
    "deliberation will make no difference to our actions ; it is perfectly compatible with "
    "determinism that deliberation should lead us to decide against the course of action that "
    "initially appeared favourable, only it will be predetermined that it should do so. » Cette "
    "distinction interprétative est précisément celle que Frede 2011 collapse en attribuant à "
    "Alexandre un indéterminisme « libertaire » solidement argumenté ; et que Lienemann 2012 "
    "(BPJAM 15, p. 260) ressuscite contre Frede : « Sharples bemerkt zu Recht in den angefügten "
    "Endnoten, dass sich bei Alexander kein so eindeutiger Beleg für die Zuschreibung eines "
    "indeterministischen Freiheitsbegriffs findet, wie es Fredes Darstellung suggeriert ». La "
    "position Sharples est ainsi le maillon scholarly fondateur d'une lecture skeptical-libertaire "
    "d'Alexandre."
)

NEW_NODE_LABEL = (
    "Sharples 1983 : Alexandre stipule un libertarisme mais ne le démontre pas philosophiquement"
)

NEW_NODE_METADATA = {
    "wave": WAVE,
    "created_at": NOW,
    "updated_at": NOW,
    "scholar": "Robert W. Sharples",
    "scholar_node_id": "scholar_sharples_robert",
    "primary_publication": "pub_sharples_1983_alexander_fate",
    "landmark_finding": (
        "Sharples 1983 p. 141 = sourced anchor for Lienemann 2012 critique of Frede 2011 on "
        "Alexander's libertarianism"
    ),
    "verified_critiques": [
        {
            "page": "22",
            "section": "Introduction §2 'Alexander and the De Fato'",
            "quote_verbatim": (
                "One crucial point that is however clear is that Alexander's own conception of "
                "responsibility is a libertarian one. He objects not just to determination of our "
                "actions by external causes alone, but to that resulting from a combination of "
                "internal and external factors; it is not enough that an individual contributes "
                "something to the result, if that contribution is predetermined."
            ),
            "role": "balancing_finding (Sharples does grant Alexander a libertarian intent)",
        },
        {
            "page": "129",
            "section": "Commentary, on De Fato V",
            "quote_verbatim": (
                "Such possibility is incompatible with determinism if it is understood in "
                "Alexander's libertarian sense, but not if it is taken in a qualified "
                "soft-determinist one; nor would the appeal to common usage (169.10-12) "
                "necessarily be regarded by a Stoic as finally settling the matter."
            ),
            "role": "corroborating (the libertarian reading is one available reading among others)",
        },
        {
            "page": "141",
            "section": "Commentary, on De Fato XI",
            "quote_verbatim": (
                "More generally, Alexander is wrong to assume that determinism implies that "
                "deliberation will make no difference to our actions (179.17-23, cf. XII "
                "181.3-5); it is perfectly compatible with determinism that deliberation should "
                "lead us to decide against the course of action that initially appeared "
                "favourable, only it will be predetermined that it should do so."
            ),
            "role": "primary_hit (Lienemann 2012 BPJAM p. 260 anchor)",
        },
        {
            "page": "147",
            "section": "Commentary, on De Fato XIV (continuing into XV)",
            "quote_verbatim": (
                "by the distinction that he draws between voluntary and responsible action "
                "Alexander puts himself in a position which risks being paradoxical if pressed."
            ),
            "role": "corroborating (internal incoherence in the voluntary/responsible distinction)",
        },
        {
            "page": "148",
            "section": "Commentary, on De Fato XV",
            "quote_verbatim": (
                "it can hardly be said that Alexander gives adequate attention in the de fato to "
                "the analysis of causation as such — even in chs. XXII–XXV, between which and "
                "the present chapter no explicit link is drawn — or that he is fully conscious "
                "of the significance of the difference between his approach and his opponents'; "
                "the impression given is rather of an uncritical acceptance of Aristotelian "
                "positions, and of a series of debating points rather than a detailed examination "
                "of the issue."
            ),
            "role": "corroborating (De Fato is a string of debating points, not a rigorous demonstration)",
        },
        {
            "page": "173",
            "section": "Commentary, on Mantissa XXII (De Fato XXXIX continuation)",
            "quote_verbatim": (
                "211.20ff. wrongly assumes that determinism implies that our being wise or "
                "otherwise will have no effect on our actions (above, p. 10)."
            ),
            "role": "corroborating (Mantissa reproduces the same begging-of-the-question)",
        },
    ],
    "thesis_significance": (
        "Citation pivot for the Sharples–Bobzien–Frede–Lienemann debate over whether 'free will' "
        "really emerged with Alexander of Aphrodisias (Frede 2011) or only with Augustine "
        "(Sharples/Lienemann)."
    ),
    "pdf_source": (
        "[local-path] SHAL/04_Littérature_secondaire/"
        "01_Philosophie_antique/sharples_1983_alexander_de_fato.pdf"
    ),
    "pdf_md5": "f62fcffa6f56cc224803de2b8437dc9c",
    "needs_evidence": False,
    "pub_evidence_attached": True,
}

# Use existing node_types.json types: `position` would be ontologically clean
# but only supports a tiny edge set (no created_by/discusses/critiques as source).
# `argument` is the type used by all 906 sibling `scholarly_argument_*` nodes
# and supports created_by/discusses/critiques as source (per edge_types.json).
# Per the project "Reuse existing ontology" rule, mirror the 906 siblings' choice.
NEW_NODE_TYPE = "argument"

NEW_NODE = {
    "alternative_names": "[]",
    "created_at": NOW,
    "description": NEW_NODE_DESCRIPTION,
    "id": NEW_NODE_ID,
    "label": NEW_NODE_LABEL,
    "metadata": NEW_NODE_METADATA,
    "node_id": NEW_NODE_ID,
    "period": "Modern",
    "role": None,
    "school": None,
    "type": NEW_NODE_TYPE,
    "updated_at": NOW,
}

NEW_EDGES_SPEC = [
    {
        "source": NEW_NODE_ID,
        "relation": "created_by",
        "target": "scholar_sharples_robert",
        "weight": 1.0,
        "rationale": "Scholar Sharples is the originator of this scholarly position.",
    },
    {
        "source": NEW_NODE_ID,
        "relation": "discusses",
        "target": "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        "weight": 1.0,
        "rationale": "The position is an interpretive thesis ABOUT Alexander of Aphrodisias.",
    },
    {
        "source": NEW_NODE_ID,
        "relation": "critiques",
        "target": "pub_frede_2011_free_will",
        "weight": 1.0,
        "rationale": (
            "The position is mobilised against Frede 2011's reading of Alexander as the "
            "first fully libertarian thinker; ontology-checked: argument -> publication is "
            "allowed for `critiques`."
        ),
    },
    {
        "source": "pub_sharples_1983_alexander_fate",
        "relation": "discusses",
        "target": NEW_NODE_ID,
        "weight": 1.0,
        "rationale": "Sharples 1983 is the primary source for this position (pp. 22, 129, 141, 147, 148, 173).",
    },
    {
        "source": "pub_lienemann_2012_review_frede",
        "relation": "discusses",
        "target": NEW_NODE_ID,
        "weight": 1.0,
        "rationale": "Lienemann 2012 BPJAM p. 260 explicitly cites this Sharples position against Frede.",
    },
]

# --- Task B: re-wire 4 args mis-attributed to Sharples 1983 -----------------

# 4 args with verification_confidence not_found / low AND wrong_source_suspicion
# in data/kg/e2_patches/sharples.json. NO existing
# `pub_sharples_1983_alexander_fate --discusses--> arg` edges exist for any of
# them (verified by independent inspection of edges.jsonl), so the re-wire is
# purely additive: add the corrected pub->arg discusses edge + update arg
# metadata to record the re-attribution.
REWIRES = [
    {
        "arg_id": "scholarly_argument_sharples_free_will_and_determinism_in_a_1",
        "original_pub": "pub_sharples_1983_alexander_fate",
        "corrected_pub": "pub_sharples_2008_accident_determinisme",
        "lift_needs_evidence": False,
        "wrong_source_note": (
            "Probably belongs to pub_sharples_2008_accident_determinisme (whose title "
            "'L'accident du déterminisme' literally makes the contingency claim). The 1983 "
            "Introduction is COMPATIBLE with the claim but does not voice it."
        ),
        "verification_confidence_e2": "low",
    },
    {
        "arg_id": "scholarly_argument_sharples_historical_determinism_0",
        "original_pub": "pub_sharples_1983_alexander_fate",
        "corrected_pub": "pub_sharples_2008_accident_determinisme",
        "lift_needs_evidence": False,
        "wrong_source_note": (
            "Should be re-wired from pub_sharples_1983_alexander_fate to "
            "pub_sharples_2008_accident_determinisme (the meta-historiographical thesis is the "
            "framing argument of the 2008 Études philosophiques paper)."
        ),
        "verification_confidence_e2": "not_found",
    },
    {
        "arg_id": "scholarly_argument_sharples_tension_between_neglect_and_de_3",
        "original_pub": "pub_sharples_1983_alexander_fate",
        "corrected_pub": "pub_sharples_1982_providence",
        "lift_needs_evidence": False,
        "wrong_source_note": (
            "Should be re-wired to either pub_sharples_1982_providence (CQ 'Two Problems') or "
            "Sharples's 1983 'Nemesius and some theories of divine providence' (Vigiliae "
            "Christianae 37, pp. 141-156). The Vigiliae piece is NOT in the KG as a distinct "
            "pub node — flagged via metadata.needs_pub_node_creation."
        ),
        "needs_pub_node_creation": "pub_sharples_1983_nemesius_vigiliae",
        "verification_confidence_e2": "not_found",
    },
    {
        "arg_id": "scholarly_argument_sharples_the_tetralemma_argument_5",
        "original_pub": "pub_sharples_1983_alexander_fate",
        "corrected_pub": "pub_sharples_1991_cicero_boethius",
        "lift_needs_evidence": False,
        "wrong_source_note": (
            "Should be re-wired from pub_sharples_1983_alexander_fate to "
            "pub_sharples_1991_cicero_boethius (which does treat Carneadean and Academic-"
            "skeptical arguments)."
        ),
        "verification_confidence_e2": "not_found",
    },
]

# ----------------------------------------------------------------------------


def log(msg: str) -> None:
    print(msg, flush=True)


def stable_edge_id(source: str, relation: str, target: str) -> str:
    """Deterministic UUIDv5 so re-runs produce the same edge id (true idempotence)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}|{relation}|{target}|{WAVE}"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, items: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False))
            f.write("\n")


def snapshot(commit: bool) -> None:
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    for src in (NODES_PATH, EDGES_PATH):
        dst = SNAP_DIR / src.name
        if dst.exists():
            log(f"  snapshot already present: {dst} (kept)")
            continue
        if commit:
            shutil.copy2(src, dst)
            log(f"  snapshotted {src} -> {dst}")
        else:
            log(f"  [dry-run] would snapshot {src} -> {dst}")


def parse_edge_metadata(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"_raw": raw}
    return {}


def build_edge(source: str, relation: str, target: str, weight: float, rationale: str) -> dict:
    meta = {
        "wave": WAVE,
        "rationale": rationale,
        "wiring_confidence": "high",
        "auto_generated": False,
        "verified_at": NOW,
    }
    return {
        "created_at": NOW,
        "edge_id": stable_edge_id(source, relation, target),
        "metadata": json.dumps(meta, ensure_ascii=False),
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": weight,
    }


def edge_key(e: dict) -> tuple[str, str, str]:
    return (e.get("source_id") or e.get("source"), e.get("relation"), e.get("target_id") or e.get("target"))


# --- Pre-flight checks ------------------------------------------------------


def preflight(nodes: list[dict]) -> None:
    by_id = {n["id"]: n for n in nodes}
    required = [
        "scholar_sharples_robert",
        "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        "pub_frede_2011_free_will",
        "pub_sharples_1983_alexander_fate",
        "pub_lienemann_2012_review_frede",
        "pub_sharples_1982_providence",
        "pub_sharples_1991_cicero_boethius",
        "pub_sharples_2008_accident_determinisme",
    ] + [r["arg_id"] for r in REWIRES]
    missing = [r for r in required if r not in by_id]
    if missing:
        log(f"FATAL: missing required nodes: {missing}")
        sys.exit(2)
    log("  preflight: all target nodes exist")


# --- Task A -----------------------------------------------------------------


def task_a(nodes: list[dict], edges: list[dict]) -> tuple[list[dict], list[dict], dict]:
    stats = {"node_created": False, "node_already_present": False, "edges_added": 0, "edges_already_present": 0}
    by_id = {n["id"]: i for i, n in enumerate(nodes)}

    if NEW_NODE_ID in by_id:
        stats["node_already_present"] = True
        log(f"  [A] node {NEW_NODE_ID} already present (no-op)")
    else:
        nodes.append(NEW_NODE)
        stats["node_created"] = True
        log(f"  [A] node {NEW_NODE_ID} created (type={NEW_NODE_TYPE}, period=Modern)")

    existing_keys = {edge_key(e) for e in edges}
    for spec in NEW_EDGES_SPEC:
        k = (spec["source"], spec["relation"], spec["target"])
        if k in existing_keys:
            stats["edges_already_present"] += 1
            log(f"  [A] edge already present: {k[0]} --{k[1]}--> {k[2]} (no-op)")
        else:
            new_e = build_edge(
                source=spec["source"],
                relation=spec["relation"],
                target=spec["target"],
                weight=spec["weight"],
                rationale=spec["rationale"],
            )
            edges.append(new_e)
            existing_keys.add(k)
            stats["edges_added"] += 1
            log(f"  [A] edge added: {k[0]} --{k[1]}--> {k[2]}")
    return nodes, edges, stats


# --- Task B -----------------------------------------------------------------


def task_b(nodes: list[dict], edges: list[dict]) -> tuple[list[dict], list[dict], dict]:
    stats = {
        "args_processed": 0,
        "rewire_edges_added": 0,
        "rewire_edges_already_present": 0,
        "old_edges_deleted": 0,
        "needs_evidence_lifted": 0,
        "missing_pub_flags": 0,
        "metadata_updated": 0,
        "metadata_already_correct": 0,
    }
    by_id = {n["id"]: i for i, n in enumerate(nodes)}
    existing_keys = {edge_key(e) for e in edges}

    # Identify edges to delete: any pub_sharples_1983_alexander_fate --discusses--> <one of our 4 args>
    delete_keys = set()
    for r in REWIRES:
        delete_keys.add(("pub_sharples_1983_alexander_fate", "discusses", r["arg_id"]))

    kept_edges = []
    for e in edges:
        if edge_key(e) in delete_keys:
            stats["old_edges_deleted"] += 1
            log(f"  [B] deleting wrong edge: {edge_key(e)}")
            continue
        kept_edges.append(e)
    edges = kept_edges
    existing_keys = {edge_key(e) for e in edges}

    for r in REWIRES:
        stats["args_processed"] += 1
        arg_id = r["arg_id"]
        corrected_pub = r["corrected_pub"]

        # Add corrected pub --discusses--> arg edge
        k = (corrected_pub, "discusses", arg_id)
        if k in existing_keys:
            stats["rewire_edges_already_present"] += 1
            log(f"  [B] corrected edge already present: {k[0]} --discusses--> {k[2]} (no-op)")
        else:
            new_e = build_edge(
                source=corrected_pub,
                relation="discusses",
                target=arg_id,
                weight=0.85,
                rationale=(
                    f"Re-attribution per data/kg/e2_patches/sharples.json: "
                    f"original_pub={r['original_pub']}, corrected_pub={corrected_pub}. "
                    f"E2 verification_confidence on Sharples 1983: {r['verification_confidence_e2']}."
                ),
            )
            edges.append(new_e)
            existing_keys.add(k)
            stats["rewire_edges_added"] += 1
            log(f"  [B] edge added: {k[0]} --discusses--> {k[2]}")

        # Update arg metadata (idempotent)
        if arg_id not in by_id:
            log(f"  [B] FATAL: arg {arg_id} missing from nodes.jsonl (already pre-flighted)")
            sys.exit(2)
        n = nodes[by_id[arg_id]]
        meta = n.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {"_raw": meta}
        existing_correct = (
            meta.get("sharples_reattribution_at") == NOW
            and meta.get("corrected_pub") == corrected_pub
        )
        if existing_correct:
            stats["metadata_already_correct"] += 1
            log(f"  [B] metadata already correct for {arg_id} (no-op)")
        else:
            meta["sharples_reattribution_at"] = NOW
            meta["sharples_reattribution_wave"] = WAVE
            meta["original_pub"] = r["original_pub"]
            meta["corrected_pub"] = corrected_pub
            meta["wrong_pub_attribution"] = (
                f"originally wired to {r['original_pub']}; corrected to {corrected_pub}"
            )
            meta["wrong_source_note"] = r["wrong_source_note"]
            meta["e2_verification_confidence_on_original_pub"] = r["verification_confidence_e2"]
            if "needs_pub_node_creation" in r:
                meta["needs_pub_node_creation"] = r["needs_pub_node_creation"]
                stats["missing_pub_flags"] += 1
                log(
                    f"  [B] flagged missing pub for {arg_id}: needs_pub_node_creation="
                    f"{r['needs_pub_node_creation']}"
                )
            if r["lift_needs_evidence"] and meta.get("needs_evidence") is not False:
                meta["needs_evidence"] = False
                meta["needs_evidence_lifted_at"] = NOW
                meta["needs_evidence_lifted_reason"] = (
                    f"Re-attributed to verified pub {corrected_pub} (E2 confidence verified)."
                )
                stats["needs_evidence_lifted"] += 1
                log(f"  [B] needs_evidence lifted for {arg_id}")
            n["metadata"] = meta
            n["updated_at"] = NOW
            stats["metadata_updated"] += 1
            log(f"  [B] metadata updated for {arg_id}")

    return nodes, edges, stats


# --- Main -------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Sharples landmark finalization (idempotent).")
    parser.add_argument("--commit", action="store_true", help="Write changes to disk.")
    args = parser.parse_args()

    log(f"== Sharples landmark finalize ({WAVE}) ==")
    log(f"  commit={args.commit}")
    log("  loading nodes & edges...")
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    log(f"  loaded {len(nodes)} nodes, {len(edges)} edges")

    log("  preflight checks...")
    preflight(nodes)

    log("  snapshotting...")
    snapshot(args.commit)

    log("  -- Task A: landmark node + 5 edges --")
    nodes, edges, stats_a = task_a(nodes, edges)

    log("  -- Task B: re-wire 4 mis-attributed args --")
    nodes, edges, stats_b = task_b(nodes, edges)

    log("")
    log("STATS A:")
    for k, v in stats_a.items():
        log(f"  {k}: {v}")
    log("STATS B:")
    for k, v in stats_b.items():
        log(f"  {k}: {v}")
    log(f"  final node count: {len(nodes)}")
    log(f"  final edge count: {len(edges)}")

    if args.commit:
        write_jsonl(NODES_PATH, nodes)
        write_jsonl(EDGES_PATH, edges)
        log("  wrote nodes.jsonl and edges.jsonl")
    else:
        log("  [dry-run] no files written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
