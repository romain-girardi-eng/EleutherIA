#!/usr/bin/env python3
"""Wave P — Final polish — 2026-05-16.

Last data-mutation wave before the Final Gate. Applies six conservative,
idempotent polish steps :

* **P1**  DOI cleanup on publication / scholarly_work nodes — delete
          ``metadata.doi`` when value is empty, ``UNKNOWN`` / ``N/A``
          (case-insensitive), or a raw URL (``http://`` / ``https://``).
* **P2**  Rename ``metadata.source_language`` → ``original_language``
          on ``translation_of`` edges (current naming is misleading: it
          stores the language of the original / target, not the
          translation source).
* **P3**  Flag passage nodes whose ID starts with ``passage_didache_``
          and which only have ``part_of`` structural edges, by setting
          ``metadata.text_only_ingestion = true`` and
          ``metadata.semantic_status = "structural_only"``.
* **P4**  Period backfill for nodes whose ``period`` is None/empty —
          inherit from ``authored_by`` person, fallback to ``part_of``
          work, last-resort default ``Cross-period`` with marker.
          Excluded types: ``synthesis`` (cross-period reception),
          ``publication`` (Contemporary already set elsewhere),
          ``source_collection``.
* **P5**  Add canonical etymology prepend (``**Étymologie** :``) to up
          to 20 most-referenced concepts where no termes/etymology block
          is already present. Conservative — only standard etymologies
          (αὐτεξούσιον < αὐτο- + ἐξουσία ; clinamen < clinare ; etc.).
* **P6**  Flag ``scholarly_argument_*`` nodes with 0 outgoing edges
          via ``metadata.orphan_scholarly_argument = true`` for
          curation — not auto-linked, just visible to future waves.

Snapshots ``data/kg/{nodes,edges}.jsonl`` to
``data/kg/snapshots/2026-05-16-pre-wave_p_final_polish_2026_05_16/``
before any mutation. Romain est seul auteur.
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
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

WAVE_TAG = "wave_p_final_polish_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    with NODES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_edges() -> list[dict[str, Any]]:
    with EDGES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_nodes(nodes: list[dict[str, Any]]) -> None:
    with NODES_PATH.open("w") as fh:
        for n in nodes:
            fh.write(json.dumps(n, ensure_ascii=False) + "\n")


def write_edges(edges: list[dict[str, Any]]) -> None:
    with EDGES_PATH.open("w") as fh:
        for e in edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def node_id_of(n: dict[str, Any]) -> str:
    return n.get("id") or n.get("node_id") or ""


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    snap_edges = SNAPSHOT_DIR / "edges.jsonl"
    if snap_nodes.exists() and snap_edges.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} - skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    shutil.copy2(EDGES_PATH, snap_edges)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


def parse_metadata(raw: Any) -> dict[str, Any]:
    """Return a mutable dict view of node/edge ``metadata`` regardless of
    whether it is stored as a JSON string or already-parsed dict.

    Empty / None metadata yields an empty dict.
    """
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
        return {}
    return {}


def serialize_metadata(md: dict[str, Any], original: Any) -> Any:
    """Round-trip metadata back to the storage format used by the
    original record (string-encoded JSON if the original was a string,
    dict otherwise). Keeps existing repo convention.
    """
    if isinstance(original, str):
        return json.dumps(md, ensure_ascii=False)
    return md


# ---------------------------------------------------------------------------
# P1 — DOI cleanup
# ---------------------------------------------------------------------------


_DOI_PUBLICATION_TYPES = {"publication"}
_DOI_PUBLICATION_ID_PREFIXES = ("pub_", "scholarly_work_")


def _is_publication_like(n: dict[str, Any]) -> bool:
    if n.get("type") in _DOI_PUBLICATION_TYPES:
        return True
    nid = node_id_of(n)
    return any(nid.startswith(p) for p in _DOI_PUBLICATION_ID_PREFIXES)


def _doi_should_be_deleted(raw_doi: Any) -> bool:
    if raw_doi is None:
        return False
    if not isinstance(raw_doi, str):
        # Non-string DOIs (numbers etc.) are abnormal — leave to manual review.
        return False
    val = raw_doi.strip()
    if val == "":
        return True
    upper = val.upper()
    if upper in ("UNKNOWN", "N/A"):
        return True
    lower = val.lower()
    return lower.startswith("http://") or lower.startswith("https://")


def run_p1_doi_cleanup(nodes: list[dict[str, Any]]) -> tuple[int, int]:
    """Sweep publication-like nodes ; delete bogus DOI fields."""
    cleaned = 0
    already_clean = 0
    for n in nodes:
        if not _is_publication_like(n):
            continue
        original_md = n.get("metadata")
        md = parse_metadata(original_md)
        if "doi" not in md:
            already_clean += 1
            continue
        if _doi_should_be_deleted(md.get("doi")):
            md.pop("doi", None)
            n["metadata"] = serialize_metadata(md, original_md)
            n["updated_at"] = NOW_ISO
            cleaned += 1
        else:
            already_clean += 1
    return cleaned, already_clean


# ---------------------------------------------------------------------------
# P2 — translation_of edges : source_language → original_language
# ---------------------------------------------------------------------------


def run_p2_translation_rename(edges: list[dict[str, Any]]) -> tuple[int, int]:
    renamed = 0
    already_renamed = 0
    for e in edges:
        if e.get("relation") != "translation_of":
            continue
        original_md = e.get("metadata")
        md = parse_metadata(original_md)
        has_src = "source_language" in md
        has_orig = "original_language" in md
        if not has_src and not has_orig:
            continue
        if not has_src and has_orig:
            already_renamed += 1
            continue
        if has_src and has_orig:
            # Drop redundant source_language ; keep original_language.
            md.pop("source_language", None)
            e["metadata"] = serialize_metadata(md, original_md)
            already_renamed += 1
            continue
        # has_src only — perform the rename.
        md["original_language"] = md.pop("source_language")
        e["metadata"] = serialize_metadata(md, original_md)
        renamed += 1
    return renamed, already_renamed


# ---------------------------------------------------------------------------
# P3 — Didache passages : flag text-only / structural-only
# ---------------------------------------------------------------------------


def run_p3_didache_flag(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[int, int]:
    """Flag ``passage_didache_*`` nodes whose only edges are ``part_of``.

    The spec described ~215 such nodes ; in the current KG only 6 exist
    (the ingestion plan for the full Didache is still pending). The
    logic remains forward-compatible : any future passage_didache_*
    ingest will be picked up automatically.
    """
    semantic_count: dict[str, int] = {}
    for e in edges:
        rel = e.get("relation") or ""
        if rel == "part_of":
            continue
        src = e.get("source") or e.get("source_id") or ""
        tgt = e.get("target") or e.get("target_id") or ""
        for nid in (src, tgt):
            if nid.startswith("passage_didache_"):
                semantic_count[nid] = semantic_count.get(nid, 0) + 1

    flagged = 0
    already_flagged = 0
    for n in nodes:
        nid = node_id_of(n)
        if not nid.startswith("passage_didache_"):
            continue
        if semantic_count.get(nid, 0) > 0:
            # Has semantic edges — not eligible for the structural-only flag.
            continue
        original_md = n.get("metadata")
        md = parse_metadata(original_md)
        already = (
            md.get("text_only_ingestion") is True
            and md.get("semantic_status") == "structural_only"
        )
        if already:
            already_flagged += 1
            continue
        md["text_only_ingestion"] = True
        md["semantic_status"] = "structural_only"
        md["semantic_status_wave"] = WAVE_TAG
        n["metadata"] = serialize_metadata(md, original_md)
        n["updated_at"] = NOW_ISO
        flagged += 1
    return flagged, already_flagged


# ---------------------------------------------------------------------------
# P4 — Period backfill
# ---------------------------------------------------------------------------


_P4_EXCLUDED_TYPES = {"synthesis", "publication", "source_collection"}


def _period_missing(n: dict[str, Any]) -> bool:
    p = n.get("period")
    if p is None:
        return True
    return isinstance(p, str) and p.strip() == ""


def run_p4_period_backfill(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[int, int, int, int]:
    """Backfill period via authored_by → part_of → Cross-period default."""

    # Index of node periods by canonical id.
    id_to_period: dict[str, str] = {}
    for n in nodes:
        nid = node_id_of(n)
        if not nid:
            continue
        p = n.get("period")
        if isinstance(p, str) and p.strip():
            id_to_period[nid] = p.strip()

    # authored_by : source (work / passage / argument / concept) → target (person)
    authored_by_target: dict[str, str] = {}
    # part_of : source → target (parent work / book / chapter)
    part_of_target: dict[str, str] = {}
    for e in edges:
        rel = e.get("relation") or ""
        src = e.get("source") or e.get("source_id") or ""
        tgt = e.get("target") or e.get("target_id") or ""
        if not src or not tgt:
            continue
        if rel == "authored_by" and src not in authored_by_target:
            authored_by_target[src] = tgt
        elif rel == "part_of" and src not in part_of_target:
            part_of_target[src] = tgt

    inherited_from_author = 0
    inherited_from_work = 0
    crossperiod_default = 0
    already_set = 0

    for n in nodes:
        if n.get("type") in _P4_EXCLUDED_TYPES:
            continue
        if not _period_missing(n):
            already_set += 1
            continue
        nid = node_id_of(n)
        if not nid:
            continue
        period: str | None = None
        inheritance_source: str | None = None

        author_id = authored_by_target.get(nid)
        if author_id and author_id in id_to_period:
            period = id_to_period[author_id]
            inheritance_source = "authored_by_person"

        if period is None:
            parent_id = part_of_target.get(nid)
            # Walk up the part_of chain (cap at 8 hops) to find a periodised parent.
            hops = 0
            visited: set[str] = {nid}
            while parent_id and hops < 8 and parent_id not in visited:
                visited.add(parent_id)
                if parent_id in id_to_period:
                    period = id_to_period[parent_id]
                    inheritance_source = "part_of_work"
                    break
                parent_id = part_of_target.get(parent_id)
                hops += 1

        if period is None:
            period = "Cross-period"
            inheritance_source = "wave_p_default_crossperiod"

        n["period"] = period
        original_md = n.get("metadata")
        md = parse_metadata(original_md)
        md["period_inferred"] = inheritance_source
        md["period_inferred_wave"] = WAVE_TAG
        n["metadata"] = serialize_metadata(md, original_md)
        n["updated_at"] = NOW_ISO

        if inheritance_source == "authored_by_person":
            inherited_from_author += 1
        elif inheritance_source == "part_of_work":
            inherited_from_work += 1
        else:
            crossperiod_default += 1

        # Make the new period available for downstream cascading.
        id_to_period[nid] = period

    return (
        inherited_from_author,
        inherited_from_work,
        crossperiod_default,
        already_set,
    )


# ---------------------------------------------------------------------------
# P5 — Etymology prepend on top concepts (conservative)
# ---------------------------------------------------------------------------


# Canonical etymologies — only those that are standard scholarly consensus,
# repeatedly attested across LSJ / DELG / OLD / TLL entries. Keyed by node id
# so we hit only the precise concept and never falsely brand a related one.
ETYMOLOGIES: dict[str, str] = {
    "concept_autexousion_christian_freedom_u1v2w3x4": (
        "**Étymologie** : αὐτεξούσιον < αὐτο- (réflexif, « soi-même ») + "
        "ἐξουσία (« autorité, pouvoir d'agir »), néologisme composé attesté "
        "à partir du IIᵉ s. ap. J.-C. dans la littérature patristique grecque."
    ),
    "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6": (
        "**Étymologie** : *clinamen* < lat. *clinare* (« incliner, "
        "pencher »), néologisme lucrétien (DRN II.292) calque du grec "
        "παρέγκλισις (Épicure, fr. ap. Diog. Laert. X) ; *parenklisis* < "
        "παρά- + ἐγκλίνω."
    ),
    "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6": (
        "**Étymologie** : προαίρεσις < πρό- (« avant ») + αἵρεσις "
        "(« choix, prise », de αἱρέω « prendre, saisir »), littéralement "
        "« choix préalable / antérieur ». Premier emploi technique chez "
        "Aristote, *Éthique à Nicomaque* III.4 (1112a15)."
    ),
    "concept_hekousion_voluntary_aristotle_a1b2c3d4": (
        "**Étymologie** : ἑκούσιον < adjectif neutre substantivé de ἑκών "
        "(« de plein gré, volontaire »), apparenté au verbe ἐθέλω. "
        "Opposé technique chez Aristote : ἀκούσιον (involontaire)."
    ),
    "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7": (
        "**Étymologie** : τὸ ἐφ' ἡμῖν, syntagme attributif « ce qui est "
        "sur nous / en notre pouvoir » < ἐπί + datif pronom personnel "
        "1ʳᵉ pl. Locution technique aristotélicienne (*EN* III.5) reprise "
        "par les Stoïciens et les Médio-Platoniciens."
    ),
    "concept_heimarmene_fate_stoics_j0k1l2m3": (
        "**Étymologie** : εἱμαρμένη, participe parfait passif féminin "
        "substantivé du verbe défectif μείρομαι / εἵμαρται "
        "(« recevoir en partage, échoir »), littéralement « ce qui est "
        "départi/assigné » — d'où « le destin »."
    ),
    "concept_endechomenon_contingent_aristotle_e5f6g7h8": (
        "**Étymologie** : τὸ ἐνδεχόμενον, participe présent neutre "
        "substantivé du verbe ἐνδέχομαι (« admettre, accepter, être "
        "possible »), littéralement « ce qui admet d'être (autrement) » — "
        "concept modal central d'Aristote (*De Int.* 9, *An. Pr.* I.13)."
    ),
    "concept_synkatathesis_stoic_assent": (
        "**Étymologie** : συγκατάθεσις < συν- (« avec, ensemble ») + "
        "κατάθεσις (« dépôt, position », de κατατίθημι), littéralement "
        "« co-déposition / assentiment ». Terme technique stoïcien "
        "(Chrysippe, SVF II.74-91) pour l'acte mental d'assentiment à "
        "une représentation (φαντασία)."
    ),
    "concept_ananke_necessity_democritus_h8i9j0k1": (
        "**Étymologie** : ἀνάγκη, terme archaïque (Homère, *Il.* VI.85 ; "
        "Hésiode, *Théog.* 517) signifiant « contrainte, nécessité, "
        "destin », étymologie incertaine (peut-être lié à un radical "
        "*ank- « serrer, étrangler »). Substantivé comme principe "
        "cosmologique chez les Présocratiques (Démocrite, Parménide)."
    ),
    "concept_voluntas_y7z8a9b0": (
        "**Étymologie** : *voluntas* < radical *vol-* du verbe *velle* "
        "(« vouloir »), même racine que *voluptas* (« plaisir ») et que "
        "le grec βούλομαι. Suffixe nominal -*tas* d'abstraction. "
        "Calque cicéronien du grec βούλησις (*Tusc.* 4.6.12)."
    ),
    "concept_liberum_arbitrium_u3v4w5x6": (
        "**Étymologie** : *liberum arbitrium*, syntagme nominal latin "
        "associant *liber* (« libre, non-asservi », racine indo-européenne "
        "*leudʰ- « croître, peuple libre ») et *arbitrium* "
        "(« jugement, décision arbitrale », < *arbiter* « témoin, juge »). "
        "Première attestation comme syntagme philosophique technique : "
        "Tertullien, *Adv. Marc.* II.6.3."
    ),
}


def _description_has_etymology_block(desc: str) -> bool:
    if not desc:
        return False
    stripped = desc.lstrip()
    if stripped.startswith("**Termes**"):
        return True
    if "**Étymologie**" in desc:
        return True
    return "**Première occurrence attestée**" in desc


def run_p5_etymology(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Add canonical etymology on top-20 concepts (best-effort)."""

    incoming: dict[str, int] = {}
    for e in edges:
        tgt = e.get("target") or e.get("target_id") or ""
        if tgt:
            incoming[tgt] = incoming.get(tgt, 0) + 1

    concept_nodes = [n for n in nodes if n.get("type") == "concept"]
    concept_nodes.sort(
        key=lambda n: -incoming.get(node_id_of(n), 0),
    )
    top_concepts = concept_nodes[:20]

    audited = 0
    etymology_added = 0
    already_has = 0
    for n in top_concepts:
        audited += 1
        nid = node_id_of(n)
        original_md = n.get("metadata")
        md = parse_metadata(original_md)
        if md.get("p5_etymology_added") is True:
            already_has += 1
            continue
        desc = n.get("description") or ""
        if _description_has_etymology_block(desc):
            already_has += 1
            continue
        etymology = ETYMOLOGIES.get(nid)
        if etymology is None:
            # Not a canonical case — leave alone (P5 is conservative).
            continue
        new_desc = etymology + "\n\n" + desc
        n["description"] = new_desc
        md["p5_etymology_added"] = True
        md["p5_etymology_wave"] = WAVE_TAG
        n["metadata"] = serialize_metadata(md, original_md)
        n["updated_at"] = NOW_ISO
        etymology_added += 1

    return audited, etymology_added, already_has


# ---------------------------------------------------------------------------
# P6 — Flag orphan scholarly_arguments (0 outgoing edges)
# ---------------------------------------------------------------------------


def run_p6_flag_orphans(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[int, int]:
    outgoing: dict[str, int] = {}
    for e in edges:
        src = e.get("source") or e.get("source_id") or ""
        if src.startswith("scholarly_argument_"):
            outgoing[src] = outgoing.get(src, 0) + 1

    flagged = 0
    already_flagged = 0
    for n in nodes:
        nid = node_id_of(n)
        if not nid.startswith("scholarly_argument_"):
            continue
        if outgoing.get(nid, 0) > 0:
            continue
        original_md = n.get("metadata")
        md = parse_metadata(original_md)
        if md.get("orphan_scholarly_argument") is True:
            already_flagged += 1
            continue
        md["orphan_scholarly_argument"] = True
        md["orphan_flagged_wave"] = WAVE_TAG
        n["metadata"] = serialize_metadata(md, original_md)
        n["updated_at"] = NOW_ISO
        flagged += 1
    return flagged, already_flagged


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-p] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,}  edges={len(edges):,}")

    p1_cleaned, p1_already = run_p1_doi_cleanup(nodes)
    p2_renamed, p2_already = run_p2_translation_rename(edges)
    p3_flagged, p3_already = run_p3_didache_flag(nodes, edges)
    (
        p4_from_author,
        p4_from_work,
        p4_crossperiod,
        p4_already,
    ) = run_p4_period_backfill(nodes, edges)
    p5_audited, p5_added, p5_already = run_p5_etymology(nodes, edges)
    p6_flagged, p6_already = run_p6_flag_orphans(nodes, edges)

    node_changes = (
        p1_cleaned
        + p3_flagged
        + p4_from_author
        + p4_from_work
        + p4_crossperiod
        + p5_added
        + p6_flagged
    )
    edge_changes = p2_renamed

    if node_changes:
        write_nodes(nodes)
        print(f"[write] nodes={len(nodes):,}  (touched={node_changes})")
    else:
        print("[write] no node changes")

    if edge_changes:
        write_edges(edges)
        print(f"[write] edges={len(edges):,}  (renamed={edge_changes})")
    else:
        print("[write] no edge changes")

    print(f"[wave-p] p1_doi_cleaned={p1_cleaned}  p1_doi_already_clean={p1_already}")
    print(
        f"[wave-p] p2_translation_edges_renamed={p2_renamed}  "
        f"p2_already_renamed={p2_already}"
    )
    print(f"[wave-p] p3_didache_flagged={p3_flagged}  p3_already_flagged={p3_already}")
    print(
        f"[wave-p] p4_period_inherited_from_author={p4_from_author}  "
        f"p4_period_inherited_from_work={p4_from_work}  "
        f"p4_period_crossperiod_default={p4_crossperiod}  "
        f"p4_period_already_set={p4_already}"
    )
    print(
        f"[wave-p] p5_concepts_audited={p5_audited}  "
        f"p5_etymology_added={p5_added}  "
        f"p5_already_has={p5_already}"
    )
    print(
        f"[wave-p] p6_scholarly_args_flagged_orphan={p6_flagged}  "
        f"p6_already_flagged={p6_already}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
