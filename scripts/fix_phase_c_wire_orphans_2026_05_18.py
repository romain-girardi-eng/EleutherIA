#!/usr/bin/env python3
"""Phase C — wire the residual orphans + thin nodes detected by the
2026-05-18 KG quality audit.

Scope (post-Phase B, after ``wire_orphan_arguments_2026_05_18.py``):

    type              | orphans (0 edges) | thin (1 edge)
    ------------------+-------------------+---------------
    publication       |     23            |   120
    person            |     13            |    16
    work              |      2            |    36
    concept           |      1            |    15
    school            |      2            |     2
    source_collection |      4            |     0

Wiring strategy
---------------

1. **Publications without ``authored_by``** (59 = 23 orphan + 36 thin
   without that relation): parse surname from the canonical pub ID
   pattern ``pub_<surname>_<year>_*`` or ``scholarly_work_<surname>_*`` and
   match the scholar/person in the KG. When the surname slug is compound
   (e.g. ``boysstones`` for *George Boys-Stones*) try the joined form,
   underscored form, and a metadata-authors fallback. Emit
   ``authored_by`` (pub → person).

2. **``_amand1945``-attributed concepts** (9 concepts with the Amand
   suffix, mostly thin/orphan): emit
   ``discusses`` (pub_amand_1945_fatalisme → concept).

3. **Concepts with embedded ancient-person attribution** (suffixes
   ``_origen``, ``_basil``, ``_eus``/``_eusebius``,
   ``_iamblichus``, ``_methodian_doctrine``, ``_alexander``,
   ``_carneadean``, ``_favorinus``): emit
   ``discusses`` (concept → person). Targets resolved against the
   verified person-id map below.

4. **Works marked "SC <N>"** (5 thin works whose label or id matches
   ``SC ?\\d+``): emit ``belongs_to_corpus`` (work → ``sources_chretiennes``).

5. **LXX-canonical orphan works** (Wisdom of Solomon, 4 Maccabees):
   emit ``part_of`` (work → ``work_septuagint``).

6. **Schools with member metadata**: emit ``member_of`` (person → school)
   when the person's id slug exposes the school affiliation. Only
   Clitomachus of Carthage → ``school_academy_middle`` survives the
   strict-attribution filter; no candidates exist in the KG for
   Cyrenaics / Cynics / Old Academy / Megarians beyond those already
   wired.

Anything not matchable is marked ``wiring_status: unmatched`` with a
reason. We **do not fabricate** edges and we **do not** auto-create
scholar nodes for the 18 publications whose author has no person node
(Alberti, Astolfi, Brass, Comerro, Deery, Di Muzio, Dobbin, Gauthier,
Haggard, Hardie, Merker, Müller, O'Keefe, Rambaux, Renard, Ryle,
Schöckenhoff, Williams) — these are left flagged for manual scholar
creation.

Idempotency
-----------
A second run is a no-op:
* edge dedup by (source, target, relation) signature
* nodes already carrying ``phase_c_wired_at == "2026-05-18"`` are
  skipped.

Existing flags (``orphan_*``, ``needs_evidence``, ``wiring_status`` from
prior phases) are preserved.

Usage
-----
    python3 scripts/fix_phase_c_wire_orphans_2026_05_18.py           # dry-run
    python3 scripts/fix_phase_c_wire_orphans_2026_05_18.py --commit  # apply

A snapshot is written to
``data/kg/snapshots/2026-05-18-pre-phase-c-orphans/`` before any
mutation.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-phase-c-orphans"

WIRED_DATE = "2026-05-18"
WIRED_WAVE = "wave_phase_c_orphan_wiring_2026_05_18"

# ---------------------------------------------------------------------------
# Verified anchors (ids checked against data/kg/nodes.jsonl on 2026-05-18)
# ---------------------------------------------------------------------------

AMAND_PUB_ID = "pub_amand_1945_fatalisme"
SC_CORPUS_ID = "sources_chretiennes"
LXX_WORK_ID = "work_septuagint"

# Concept-attribution → ancient person target. Suffix keys checked against
# concept ids in order (longest-first) to avoid false positives.
CONCEPT_PERSON_ATTRIB: list[tuple[str, str]] = [
    ("_methodian_doctrine", "person_methodius_olympus_d311"),
    ("_gregory_nyssa", "person_gregory_nyssa_d395"),
    ("_carneadean", "person_carneades_214_129bce_l2m3n4o5"),
    ("_iamblichus", "person_iamblichus_d325"),
    ("_eusebius", "person_eusebius_caesarea_d339"),
    ("_origenist", "person_origen_alexandria_185_254ce_s9t0u1v2"),
    ("_favorinus", "person_favorinus_of_arles_9n4o6q32"),
    ("_origen", "person_origen_alexandria_185_254ce_s9t0u1v2"),
    ("_basil", "person_basil_great_d379"),
    ("_alexander", "person_alexander_aphrodisias_fl200ce_n5o6p7q8"),
    ("_philo", "person_philo_alexandria_a1b2c3d4"),
    ("_eus", "person_eusebius_caesarea_d339"),  # short suffix — check LAST
]

# Person → school (strict, verified individually)
PERSON_TO_SCHOOL: dict[str, str] = {
    "person_clitomachus_of_carthage_7l2m4o10": "school_academy_middle",
}

# LXX-canonical orphan works
LXX_ORPHAN_WORKS: set[str] = {
    "work_wisdom_of_solomon",
    "work_4_maccabees",
}

# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for src in (NODES_PATH, EDGES_PATH):
        dst = SNAPSHOT_DIR / src.name
        if not dst.exists():
            shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def normalize(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def md_dict(node: dict) -> dict:
    md = node.get("metadata")
    if isinstance(md, dict):
        return md
    if isinstance(md, str):
        try:
            parsed = json.loads(md)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


# ---------------------------------------------------------------------------
# Scholar (person) index — copied from Phase B + extended for compound surnames
# ---------------------------------------------------------------------------

PARTICLES = ("o", "f", "de", "la", "van", "von", "du", "l", "el")
COMPOUND_HEADS: dict[str, frozenset[str]] = {
    "engberg": frozenset({"pedersen"}),
    "boys": frozenset({"stones"}),
    "denzey": frozenset({"lewis"}),
    "acosta": frozenset({"l"}),
    "amand": frozenset({"de"}),
    "koch": frozenset({"piettre"}),
}


def person_surname_variants(person: dict) -> set[str]:
    out: set[str] = set()
    pid = person["id"]
    label = person.get("label", "") or ""
    body = pid
    for prefix in ("scholar_", "person_"):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    body = body.replace("_contemporary", "")
    parts = body.split("_")

    def _is_hash(tok: str) -> bool:
        return bool(tok) and 6 <= len(tok) <= 12 and any(c.isdigit() for c in tok)

    while parts and (len(parts[-1]) == 1 or _is_hash(parts[-1]) or parts[-1].isdigit()):
        parts.pop()
    if parts:
        p0 = parts[0]
        if p0 in PARTICLES and len(parts) >= 2:
            out.add(f"{p0}_{parts[1]}")
            out.add(parts[1])
        elif p0 in COMPOUND_HEADS and len(parts) >= 2 and parts[1] in COMPOUND_HEADS[p0]:
            out.add(f"{p0}_{parts[1]}")
            out.add(f"{p0}{parts[1]}")     # joined: "boys_stones" → "boysstones"
            out.add(p0)
        else:
            out.add(p0)
    # label
    norm = normalize(label)
    toks = re.findall(r"[a-z]+", norm)
    if toks:
        out.add(toks[-1])
        if len(toks) >= 2:
            out.add(f"{toks[-2]}_{toks[-1]}")
            out.add(f"{toks[-2]}{toks[-1]}")
            if toks[-2] in PARTICLES and len(toks) >= 3:
                out.add(f"{toks[-3]}_{toks[-2]}_{toks[-1]}")
    return {x for x in out if x and len(x) >= 2}


def build_scholar_index(nodes: list[dict]) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = defaultdict(list)
    for n in nodes:
        if n.get("type") != "person":
            continue
        pid = n["id"]
        for sn in person_surname_variants(n):
            if pid not in idx[sn]:
                idx[sn].append(pid)
    return idx


# ---------------------------------------------------------------------------
# Publication → scholar resolution
# ---------------------------------------------------------------------------

PUB_ID_RE = re.compile(r"^(?:pub|scholarly_work)_([a-z][a-z_]*?)_(\d{4})(?:_.*)?$")


def is_scholarly_person(pid: str) -> bool:
    return pid.startswith("scholar_") or pid.endswith("_contemporary")


def resolve_pub_author(
    pub_id: str,
    pub_md: dict,
    scholar_idx: dict[str, list[str]],
    nodes_by_id: dict[str, dict],
) -> tuple[str | None, str, str]:
    """Return (person_id, confidence, reason). person_id is None when unmatched."""
    m = PUB_ID_RE.match(pub_id)
    candidates: list[str] = []
    surname = None
    if m:
        surname = m.group(1)
        # 1. full compound surname
        candidates = scholar_idx.get(surname, [])
        # 2. underscored→joined or joined→underscored
        if not candidates and "_" in surname:
            candidates = scholar_idx.get(surname.replace("_", ""), [])
        # 3. first token of compound
        if not candidates and "_" in surname:
            candidates = scholar_idx.get(surname.split("_")[0], [])
        # 4. underscored split of a joined form ("boysstones" → "boys_stones")
        if not candidates and "_" not in surname:
            # look for an indexed compound that starts with the surname's first letters
            for k in list(scholar_idx.keys()):
                if "_" in k and k.replace("_", "") == surname:
                    candidates = scholar_idx[k]
                    break

    # Metadata-author fallback
    if not candidates:
        md_authors = pub_md.get("authors") or pub_md.get("author")
        if md_authors:
            if isinstance(md_authors, list):
                au_str = md_authors[0] if md_authors else ""
            else:
                au_str = str(md_authors)
            first = au_str.split(";")[0].split(" and ")[0].split("&")[0].strip()
            if "," in first:
                last = first.split(",")[0].strip()
            else:
                last = first.split()[-1] if first.split() else ""
            last_norm = re.sub(r"[^a-z]", "", normalize(last))
            if last_norm:
                candidates = scholar_idx.get(last_norm, [])
                if not candidates and "-" in last:
                    joined = re.sub(r"[^a-z]", "", last.lower())
                    underscored = last.lower().replace("-", "_")
                    candidates = (
                        scholar_idx.get(joined, [])
                        or scholar_idx.get(underscored, [])
                    )

    if not candidates:
        return None, "none", f"no_scholar:surname={surname}"

    # Filter to actually-existing nodes
    candidates = [c for c in candidates if c in nodes_by_id]
    if not candidates:
        return None, "none", "candidates_resolved_to_missing_nodes"

    # Prefer scholar_* over plain person_*
    scholar_pri = [c for c in candidates if c.startswith("scholar_")]
    contemporary = [c for c in candidates if c.endswith("_contemporary")]
    others = [c for c in candidates if c not in scholar_pri and c not in contemporary]
    ranked = scholar_pri + contemporary + others

    n_scholarly = sum(1 for c in candidates if is_scholarly_person(c))
    if n_scholarly == 1 or len(candidates) == 1:
        return ranked[0], "high", "unique" if len(candidates) == 1 else "unique-scholarly"
    return ranked[0], "medium", f"ambiguous:{len(candidates)}"


# ---------------------------------------------------------------------------
# Concept attribution
# ---------------------------------------------------------------------------

def concept_attributed_person(concept_id: str, nodes_by_id: dict[str, dict]) -> str | None:
    """Return person id when the concept id's tail names an ancient figure."""
    for suffix, pid in CONCEPT_PERSON_ATTRIB:
        if suffix in concept_id and pid in nodes_by_id:
            return pid
    return None


# ---------------------------------------------------------------------------
# Edge factory
# ---------------------------------------------------------------------------

def signature(s: str, t: str, r: str) -> tuple[str, str, str]:
    return (s, t, r)


def edge_record(source: str, target: str, relation: str, *, weight: float, meta: dict) -> dict:
    now = datetime.now(UTC).isoformat(sep=" ")
    return {
        "created_at": now,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(meta, ensure_ascii=False),
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": weight,
    }


def patch_node(node: dict, *, edges_added: list[str], status: str, extra: dict | None = None) -> dict:
    md = md_dict(node)
    md = dict(md)
    md["phase_c_wired_at"] = WIRED_DATE
    md["phase_c_wave"] = WIRED_WAVE
    md["phase_c_status"] = status
    md["phase_c_edges_added"] = edges_added
    if extra:
        md.update(extra)
    out = dict(node)
    out["metadata"] = md
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="apply changes; otherwise dry-run")
    parser.add_argument(
        "--limit-per-type", type=int, default=None,
        help="process only first N nodes of each handled type (debug)",
    )
    args = parser.parse_args(argv)

    print(f"=== Phase C orphan/thin wiring  ({'COMMIT' if args.commit else 'dry-run'}) ===")
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    print(f"loaded {len(nodes)} nodes, {len(edges)} edges")

    nodes_by_id = {n["id"]: n for n in nodes}

    edges_in: dict[str, list[tuple[str, str]]] = defaultdict(list)
    edges_out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    existing_sigs: set[tuple[str, str, str]] = set()
    for e in edges:
        s, t, r = e["source"], e["target"], e["relation"]
        edges_out[s].append((r, t))
        edges_in[t].append((r, s))
        existing_sigs.add(signature(s, t, r))

    scholar_idx = build_scholar_index(nodes)

    new_edges: list[dict] = []
    node_updates: dict[str, dict] = {}
    edge_seen: set[tuple[str, str, str]] = set(existing_sigs)
    stat: Counter = Counter()
    unmatched_samples: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def add_edge(s: str, t: str, r: str, *, weight: float, meta: dict) -> bool:
        sig = signature(s, t, r)
        if sig in edge_seen:
            return False
        new_edges.append(edge_record(s, t, r, weight=weight, meta=meta))
        edge_seen.add(sig)
        return True

    def already_wired_by_phase_c(node: dict) -> bool:
        return md_dict(node).get("phase_c_wired_at") == WIRED_DATE

    # ------------------------------------------------------------------ #
    # 1. PUBLICATIONS → authored_by → person
    # ------------------------------------------------------------------ #
    pubs_no_auth = [
        n for n in nodes
        if n.get("type") == "publication"
        and not any(r == "authored_by" for r, _ in edges_out[n["id"]])
        and not already_wired_by_phase_c(n)
    ]
    if args.limit_per_type:
        pubs_no_auth = pubs_no_auth[: args.limit_per_type]
    print(f"\n[1] publications without authored_by: {len(pubs_no_auth)}")

    for pub in pubs_no_auth:
        pid = pub["id"]
        pmd = md_dict(pub)
        person_id, conf, reason = resolve_pub_author(pid, pmd, scholar_idx, nodes_by_id)
        edges_added: list[str] = []

        if person_id:
            meta = {
                "auto_generated": True,
                "wired_from": "phase_c_2026_05_18",
                "wiring_confidence": conf,
                "wiring_reason": reason,
            }
            if add_edge(pid, person_id, "authored_by", weight=1.0, meta=meta):
                edges_added.append(f"authored_by:{person_id}")
                stat["edges_authored_by"] += 1
            node_updates[pid] = patch_node(
                pub, edges_added=edges_added, status=f"matched_{conf}",
                extra={"phase_c_author": person_id, "phase_c_wiring_reason": reason},
            )
            stat["pubs_matched"] += 1
        else:
            node_updates[pid] = patch_node(
                pub, edges_added=[], status="unmatched_scholar",
                extra={"phase_c_wiring_reason": reason},
            )
            stat["pubs_unmatched"] += 1
            unmatched_samples["publication"].append((pid, reason))

    # ------------------------------------------------------------------ #
    # 2. _amand1945 CONCEPTS → discusses ← pub_amand_1945_fatalisme
    # ------------------------------------------------------------------ #
    amand_concepts = [
        n for n in nodes
        if n.get("type") == "concept" and "amand1945" in n["id"]
        and not already_wired_by_phase_c(n)
    ]
    print(f"\n[2] _amand1945 concepts: {len(amand_concepts)}")
    amand_exists = AMAND_PUB_ID in nodes_by_id
    if not amand_exists:
        print(f"    WARNING: anchor {AMAND_PUB_ID} not found; skipping amand wiring")

    for c in amand_concepts:
        cid = c["id"]
        edges_added = []
        if amand_exists:
            meta = {
                "auto_generated": True,
                "wired_from": "phase_c_2026_05_18",
                "wiring_confidence": "high",
                "wiring_basis": "amand1945_suffix_attribution",
            }
            if add_edge(AMAND_PUB_ID, cid, "discusses", weight=0.85, meta=meta):
                edges_added.append("discusses_from_amand_pub")
                stat["edges_amand_discusses"] += 1
            node_updates[cid] = patch_node(
                c, edges_added=edges_added, status="matched_high",
                extra={"phase_c_publication": AMAND_PUB_ID},
            )
            stat["concepts_amand_matched"] += 1
        else:
            node_updates[cid] = patch_node(
                c, edges_added=[], status="unmatched_pub_missing",
            )
            stat["concepts_amand_unmatched"] += 1

    # ------------------------------------------------------------------ #
    # 3. Other thin/orphan concepts with embedded person attribution
    # ------------------------------------------------------------------ #
    concept_low_edge = [
        n for n in nodes
        if n.get("type") == "concept"
        and (len(edges_in[n["id"]]) + len(edges_out[n["id"]])) <= 1
        and "amand1945" not in n["id"]
        and not already_wired_by_phase_c(n)
    ]
    print(f"\n[3] other thin/orphan concepts: {len(concept_low_edge)}")

    for c in concept_low_edge:
        cid = c["id"]
        person_id = concept_attributed_person(cid, nodes_by_id)
        edges_added = []
        if person_id:
            meta = {
                "auto_generated": True,
                "wired_from": "phase_c_2026_05_18",
                "wiring_confidence": "medium",
                "wiring_basis": "id_suffix_person_attribution",
            }
            if add_edge(cid, person_id, "discusses", weight=0.7, meta=meta):
                edges_added.append(f"discusses:{person_id}")
                stat["edges_concept_discusses_person"] += 1
            node_updates[cid] = patch_node(
                c, edges_added=edges_added, status="matched_medium",
                extra={"phase_c_target_person": person_id},
            )
            stat["concepts_person_matched"] += 1
        else:
            node_updates[cid] = patch_node(
                c, edges_added=[], status="unmatched_no_attribution",
            )
            stat["concepts_unmatched"] += 1
            unmatched_samples["concept"].append((cid, "no id-suffix attribution match"))

    # ------------------------------------------------------------------ #
    # 4. SC-marked WORKS → belongs_to_corpus → sources_chretiennes
    # ------------------------------------------------------------------ #
    sc_pattern = re.compile(r"\bSC\s?\d+", re.IGNORECASE)
    sc_works = [
        n for n in nodes
        if n.get("type") == "work"
        and (sc_pattern.search(n.get("label") or "") or "_sc" in n["id"].lower())
        and not any(r == "belongs_to_corpus" and t == SC_CORPUS_ID for r, t in edges_out[n["id"]])
        and not already_wired_by_phase_c(n)
    ]
    print(f"\n[4] SC-marked works to link → {SC_CORPUS_ID}: {len(sc_works)}")

    sc_anchor_exists = SC_CORPUS_ID in nodes_by_id
    if not sc_anchor_exists:
        print(f"    WARNING: anchor {SC_CORPUS_ID} not found; skipping SC wiring")

    for w in sc_works:
        wid = w["id"]
        edges_added = []
        if sc_anchor_exists:
            meta = {
                "auto_generated": True,
                "wired_from": "phase_c_2026_05_18",
                "wiring_confidence": "high",
                "wiring_basis": "sc_marker_in_label_or_id",
            }
            if add_edge(wid, SC_CORPUS_ID, "belongs_to_corpus", weight=0.95, meta=meta):
                edges_added.append("belongs_to_corpus:sources_chretiennes")
                stat["edges_sc_belongs"] += 1
            node_updates[wid] = patch_node(
                w, edges_added=edges_added, status="matched_high",
                extra={"phase_c_corpus": SC_CORPUS_ID},
            )
            stat["works_sc_matched"] += 1
        else:
            node_updates[wid] = patch_node(
                w, edges_added=[], status="unmatched_corpus_missing",
            )
            stat["works_sc_unmatched"] += 1

    # ------------------------------------------------------------------ #
    # 5. LXX-canonical orphan works → part_of → work_septuagint
    # ------------------------------------------------------------------ #
    lxx_works = [
        n for n in nodes
        if n["id"] in LXX_ORPHAN_WORKS
        and not any(r == "part_of" and t == LXX_WORK_ID for r, t in edges_out[n["id"]])
        and not already_wired_by_phase_c(n)
    ]
    print(f"\n[5] LXX orphan works to link → {LXX_WORK_ID}: {len(lxx_works)}")

    lxx_anchor_exists = LXX_WORK_ID in nodes_by_id
    if not lxx_anchor_exists:
        print(f"    WARNING: anchor {LXX_WORK_ID} not found; skipping LXX wiring")

    for w in lxx_works:
        wid = w["id"]
        edges_added = []
        if lxx_anchor_exists:
            meta = {
                "auto_generated": True,
                "wired_from": "phase_c_2026_05_18",
                "wiring_confidence": "high",
                "wiring_basis": "lxx_deuterocanonical_attribution",
            }
            if add_edge(wid, LXX_WORK_ID, "part_of", weight=0.9, meta=meta):
                edges_added.append("part_of:work_septuagint")
                stat["edges_lxx_partof"] += 1
            node_updates[wid] = patch_node(
                w, edges_added=edges_added, status="matched_high",
                extra={"phase_c_parent_work": LXX_WORK_ID},
            )
            stat["works_lxx_matched"] += 1
        else:
            node_updates[wid] = patch_node(
                w, edges_added=[], status="unmatched_lxx_anchor_missing",
            )

    # ------------------------------------------------------------------ #
    # 6. Person → school memberships (strict, manually verified)
    # ------------------------------------------------------------------ #
    print(f"\n[6] person→school memberships: {len(PERSON_TO_SCHOOL)}")
    for person_id, school_id in PERSON_TO_SCHOOL.items():
        if person_id not in nodes_by_id or school_id not in nodes_by_id:
            stat["schools_unmatched"] += 1
            continue
        # skip if already linked
        if any(r == "member_of" and t == school_id for r, t in edges_out[person_id]):
            stat["schools_already_linked"] += 1
            continue
        meta = {
            "auto_generated": True,
            "wired_from": "phase_c_2026_05_18",
            "wiring_confidence": "high",
            "wiring_basis": "manual_attribution_verified",
        }
        if add_edge(person_id, school_id, "member_of", weight=0.95, meta=meta):
            stat["edges_school_member_of"] += 1
            p = nodes_by_id[person_id]
            node_updates[person_id] = patch_node(
                p, edges_added=[f"member_of:{school_id}"],
                status="matched_high",
                extra={"phase_c_school": school_id},
            )
            stat["persons_school_matched"] += 1

    # ------------------------------------------------------------------ #
    # 7. Flag remaining orphan persons / source_collections that we cannot
    #    wire automatically — mark wiring_status without adding edges.
    # ------------------------------------------------------------------ #
    remaining_person_orphans = [
        n for n in nodes
        if n.get("type") == "person"
        and not edges_in[n["id"]] and not edges_out[n["id"]]
        and not already_wired_by_phase_c(n)
        and n["id"] not in PERSON_TO_SCHOOL  # already handled
    ]
    print(f"\n[7] residual person orphans (no auto-wire): {len(remaining_person_orphans)}")
    for p in remaining_person_orphans:
        pid = p["id"]
        # Reason: scholar w/o pubs OR ancient w/o works in KG
        pmd = md_dict(p)
        is_scholar = pid.startswith("scholar_") or pmd.get("role") == "scholar"
        reason = "scholar_without_kg_publications" if is_scholar else "ancient_person_without_kg_works"
        node_updates[pid] = patch_node(
            p, edges_added=[], status="unmatched",
            extra={"phase_c_wiring_reason": reason},
        )
        stat[f"person_unmatched_{ 'scholar' if is_scholar else 'ancient'}"] += 1
        unmatched_samples["person"].append((pid, reason))

    sc_orphans = [
        n for n in nodes
        if n.get("type") == "source_collection"
        and not edges_in[n["id"]] and not edges_out[n["id"]]
        and not already_wired_by_phase_c(n)
    ]
    print(f"\n[8] source_collection orphans (no auto-wire): {len(sc_orphans)}")
    for sc in sc_orphans:
        node_updates[sc["id"]] = patch_node(
            sc, edges_added=[], status="unmatched",
            extra={"phase_c_wiring_reason": "no_constituent_works_in_kg"},
        )
        stat["source_collection_unmatched"] += 1
        unmatched_samples["source_collection"].append((sc["id"], "no constituent works in KG"))

    # ------------------------------------------------------------------ #
    # Report
    # ------------------------------------------------------------------ #
    print("\n=== Stats ===")
    for k in sorted(stat):
        print(f"  {k}: {stat[k]}")
    print(f"\n  total new edges: {len(new_edges)}")
    print(f"  total node updates: {len(node_updates)}")

    for typ, samples in unmatched_samples.items():
        if not samples:
            continue
        print(f"\n  unmatched samples [{typ}] (first 10 of {len(samples)}):")
        for nid, reason in samples[:10]:
            print(f"    {nid:<55} :: {reason}")

    if not args.commit:
        print("\n(dry-run; pass --commit to write)")
        return 0

    if not new_edges and not node_updates:
        print("\nOK: nothing to apply.")
        return 0

    snapshot()
    print(f"\nsnapshot written to {SNAPSHOT_DIR}")

    if node_updates:
        new_nodes = [node_updates.get(n["id"], n) for n in nodes]
        write_jsonl(NODES_PATH, new_nodes)
        print(f"updated {len(node_updates)} nodes in {NODES_PATH.name}")

    if new_edges:
        with EDGES_PATH.open("a", encoding="utf-8") as fh:
            for e in new_edges:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"appended {len(new_edges)} edges to {EDGES_PATH.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
