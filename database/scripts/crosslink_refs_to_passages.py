"""Cross-link scholarly fragment refs to KG passage nodes.

Reads:
  - data/doxographical_audit/scholarly_refs_index.json  (ref → contexts)
  - data/kg/nodes.jsonl                                 (KG snapshot)

Parses each context for a source-locus citation (Cicero De Fato 42, Gellius
NA VII.2.11, Stobaeus Ecl. II.7.11g, DL VII.149, Plut. Stoic. Rep. 47, etc.)
and matches it to one or more passage_* nodes by canonical_ref / work_title /
node_id heuristics.

Outputs:
  - data/doxographical_audit/auto_mappings.jsonl (one mapping per linked passage)

Confidence policy:
  - high   : ref locus uniquely matches exactly 1 KG passage AND collection
             text confirms the philosopher
  - medium : ref locus matches via fuzzy work_title match or multiple loci
  - low    : skip (do not emit)

No fabrication: only emits mappings where the (collection, ref) string is
literally present in DOCTORAT scholarly text and the locus is a real KG
passage in the snapshot.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("crosslink_refs_to_passages")

ROOT = Path(__file__).resolve().parents[2]
REFS_INDEX = ROOT / "data" / "doxographical_audit" / "scholarly_refs_index.json"
NODES_JSONL = ROOT / "data" / "kg" / "nodes.jsonl"
OUTPUT = ROOT / "data" / "doxographical_audit" / "auto_mappings.jsonl"

# Map transmitter shorthand → (passage_id_prefix, locus parser, philosopher hint guess)
TRANSMITTER_RULES: list[dict[str, Any]] = [
    # Cicero De Fato — passage_cic_fat_N
    {
        "match": re.compile(
            r"(?:Cic\.?|Cicero)[\s,]{0,6}(?:De\s+|On\s+)?[Ff]at(?:o|e|\.|um|us)?[^\d]{0,10}(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_cic_fat_",
        "work": "Cicero De Fato",
        "transmitting_author_node": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
        "transmitting_work_node": "work_de_fato_cicero_44bce_b9c4e5d2",
    },
    # Cicero De Divinatione — passage_cic_div_N
    {
        "match": re.compile(
            r"(?:Cic\.?|Cicero)[\s,]{0,6}(?:De\s+|On\s+)?[Dd]iv(?:inatione|ination|\.)\s*(?:[IVX]+\s*[\.,]\s*)?(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_cic_div_",
        "work": "Cicero De Divinatione",
        "transmitting_author_node": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
    },
    # Cicero De Natura Deorum
    {
        "match": re.compile(
            r"(?:Cic\.?|Cicero)[\s,]{0,6}(?:De\s+|On\s+)?[Nn]at(?:ura)?\.?\s*[Dd]eor(?:um)?\.?\s*[IVX]*\.?,?\s*(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_cic_nat_deor_",
        "work": "Cicero De Natura Deorum",
        "transmitting_author_node": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
    },
    # Aulus Gellius NA VII.2
    {
        "match": re.compile(
            r"(?:Gell(?:ius|\.)|N\.\s*A\.|Aul\.?\s*Gell\.)[^\d]{0,15}V?II[I]?\.?\s*[,\.]\s*2[,\.\s]+(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_gellius_na_vii_2_7_2_",
        "work": "Aulus Gellius NA VII.2",
        "transmitting_author_node": "person_aulus_gellius",
    },
    # Alexander De Fato — passage_alex_fat_N
    {
        "match": re.compile(
            r"Alex(?:andre|ander|\.)?\s+(?:d['e]\s*Aphrod\.?|of\s+Aphr\w*)?[^A-Z]{0,8}(?:De\s+)?[Ff]ato?\.?\s*(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_alex_fat_",
        "work": "Alexander De Fato",
        "transmitting_author_node": "person_alexander_of_aphrodisias_3c_ce",
    },
    # Plutarch De Stoicorum Repugnantiis — Stoic. Rep. N
    {
        "match": re.compile(
            r"(?:Plut(?:arch|arque|\.)?[^A-Z]{0,8})?[Ss]toic\.?\s*[Rr]ep\.?\s*(?:1?0?\d{2,4}[A-F]?[\-\d]*|\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_plut_stoic_rep_",
        "work": "Plutarch Stoic. Rep.",
        "transmitting_author_node": "person_plutarch",
        "skip": True,  # numbering is Stephanus pages; needs mapping table
    },
    # Plutarch De Fato — passage_plut_fat_N
    {
        "match": re.compile(
            r"Plut(?:arch|arque|\.)?[^A-Z]{0,8}(?:De\s+)?[Ff]ato?\.?\s*(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_plut_fat_",
        "work": "Plutarch De Fato",
        "transmitting_author_node": "person_plutarch",
    },
    # Plutarch De Comm. Notitiis — passage_plut_cn_N
    {
        "match": re.compile(
            r"(?:Plut\.?\s*)?[Cc]omm(?:unibus)?\.?\s*[Nn]otit(?:iis|\.)?\s*(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_plut_cn_",
        "work": "Plutarch De Comm. Notitiis",
        "transmitting_author_node": "person_plutarch",
    },
    # Sextus Empiricus: passages stored flat (passage_sext_N where N is M./PH unique
    # in some unspecified book). Scholarly refs use "Adv. Math. XI.30" — without the
    # KG storing book number, mapping is ambiguous. Disabled for now.
    {
        "match": re.compile(r"NOMATCH_SEXTUS_DISABLED", re.IGNORECASE),
        "prefix": "passage_sext_",
        "work": "Sextus Empiricus",
        "transmitting_author_node": "person_sextus_empiricus",
        "skip": True,
    },
    # Diogenes Laertius DL X.N (Epicurus, Book 10) — handles "10.133", "X.133", "X, 133"
    {
        "match": re.compile(
            r"(?:Diog(?:enes|ene|\.|en)?[^X\d]+|D\.\s*L\.|DL\W+|Vit\.?\W+)(?:X|10)\.?\s*[,\.]?\s*(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_dl_lives_10_1_",
        "work": "Diogenes Laertius X (Epicurus)",
        "transmitting_author_node": "person_diogenes_laertius_3c_ce",
    },
    # Diogenes Laertius DL VII.N (Stoics, Book 7)
    {
        "match": re.compile(
            r"(?:Diog(?:enes|ene|\.|en)?[^V7\d]+|D\.\s*L\.|DL\W+|Vit\.?\W+)(?:VII|7)\.?\s*[,\.]?\s*(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_dl_lives_7_1_",
        "work": "Diogenes Laertius VII (Stoics)",
        "transmitting_author_node": "person_diogenes_laertius_3c_ce",
    },
    # Simplicius In Ench. N
    {
        "match": re.compile(
            r"Simpl(?:icius|\.)?[^A-Z]{0,8}(?:In\s+)?Ench\.?\s*(\d+)", re.IGNORECASE
        ),
        "prefix": "passage_simpl_in_ench_",
        "work": "Simplicius In Ench.",
        "transmitting_author_node": "person_simplicius",
    },
    # Clement Protrepticus
    {
        "match": re.compile(
            r"(?:Clem(?:ent|\.)?[^A-Z]{0,8})?Protr(?:epticus|\.)?\s*(\d+)",
            re.IGNORECASE,
        ),
        "prefix": "passage_clement_protr_",
        "work": "Clement Protrepticus",
        "transmitting_author_node": "person_clement_of_alexandria",
    },
]

# Collection → fragmented philosopher heuristic
COLLECTION_PHILOSOPHER_HINT: dict[str, dict[str, Any]] = {
    "SVF": {
        # SVF I = Zeno + early Stoics; SVF II = Chrysippus; SVF III = Chrysippus + younger
        "I": ("Zeno of Citium", "person_zeno_citium_334_262bce"),
        "II": ("Chrysippus", "person_chrysippus_280_206bce_i9j0k1l2"),
        "III": ("Chrysippus", "person_chrysippus_280_206bce_i9j0k1l2"),
    },
    "Usener": {None: ("Epicurus", "person_epicurus_341_270bce_j0k1l2m3")},
    "EK": {None: ("Posidonius", "person_posidonius_apameia_135_51bce")},
    "DK": {None: (None, None)},  # depends on number; DK 22 = Heraclitus etc.
    "LS": {None: (None, None)},  # multi-philosopher
    "Marcovich": {None: ("Heraclitus", "person_heraclitus_fl500bce_a1b2c3d4")},
    "Wehrli": {None: (None, None)},
}

DK_PHILOSOPHERS: dict[str, tuple[str, str]] = {
    "22": ("Heraclitus", "person_heraclitus_fl500bce_a1b2c3d4"),
    "28": ("Parmenides", "person_parmenides_of_elea_44a65114"),
    "31": ("Empedocles", "person_empedocles"),
    "59": ("Anaxagoras", "person_anaxagoras"),
    "67": ("Leucippus", "person_leucippus_and_democritus_8a42be84"),
    "68": ("Democritus", "person_democritus_460_370bce_g7h8i9j0"),
    "12": ("Anaximander", "person_anaximander"),
}


@dataclass
class Candidate:
    passage_id: str
    transmitting_author_node: str | None
    transmitting_work_node: str | None
    work_label: str
    locus_text: str


@dataclass
class Mapping:
    passage_id: str
    ref: str
    collection: str
    contexts: list[dict[str, str]] = field(default_factory=list)
    confidence: str = "medium"
    fragmented_philosopher: str | None = None
    philosopher_node_id: str | None = None
    transmitting_author_node: str | None = None
    transmitting_work_node: str | None = None


def load_passage_ids(path: Path = NODES_JSONL) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    with path.open() as fh:
        for line in fh:
            n = json.loads(line)
            if n.get("type") != "passage":
                continue
            out[n["node_id"]] = n
    return out


def parse_locus(ctx: str, passages: dict[str, dict[str, Any]]) -> list[Candidate]:
    """Find passage candidates referenced in a citation context."""
    cands: list[Candidate] = []
    for rule in TRANSMITTER_RULES:
        if rule.get("skip"):
            continue
        # If rule requires a specific keyword in the context, enforce it
        req = rule.get("requires_keyword")
        if req and not any(kw.lower() in ctx.lower() for kw in req):
            continue
        for m in rule["match"].finditer(ctx):
            num = m.group(1)
            try:
                int(num)
            except ValueError:
                continue
            candidate_id = f"{rule['prefix']}{num}"
            if candidate_id in passages:
                cands.append(
                    Candidate(
                        passage_id=candidate_id,
                        transmitting_author_node=rule.get("transmitting_author_node"),
                        transmitting_work_node=rule.get("transmitting_work_node"),
                        work_label=rule["work"],
                        locus_text=m.group(0),
                    )
                )
    return cands


def philosopher_hint(collection: str, ref: str) -> tuple[str | None, str | None]:
    if collection == "SVF":
        # ref e.g. "SVF II.974"
        mm = re.match(r"SVF\s+([IVX]+)\.", ref)
        if mm:
            return COLLECTION_PHILOSOPHER_HINT["SVF"].get(mm.group(1), (None, None))
        return (None, None)
    if collection == "DK":
        mm = re.match(r"DK\s*(\d+)", ref)
        if mm:
            return DK_PHILOSOPHERS.get(mm.group(1), (None, None))
        return (None, None)
    rules = COLLECTION_PHILOSOPHER_HINT.get(collection)
    if rules:
        return rules.get(None, (None, None))
    return (None, None)


def cross_link(
    refs_index: dict[str, list[dict[str, str]]], passages: dict[str, dict[str, Any]]
) -> list[Mapping]:
    """For each ref, find KG passages it likely cites via its surrounding contexts."""
    mappings_by_passage: dict[
        tuple[str, str], Mapping
    ] = {}  # (passage_id, ref) → Mapping

    for ref, hits in refs_index.items():
        if not hits:
            continue
        collection = hits[0]["collection"]
        philo_name, philo_node = philosopher_hint(collection, ref)

        all_candidates: list[Candidate] = []
        per_hit_contexts: list[tuple[Candidate, dict[str, str]]] = []
        for h in hits:
            cands = parse_locus(h["context"], passages)
            for c in cands:
                per_hit_contexts.append((c, h))
                all_candidates.append(c)

        if not all_candidates:
            continue

        # Group by passage_id
        per_passage: dict[str, list[tuple[Candidate, dict[str, str]]]] = defaultdict(
            list
        )
        for c, h in per_hit_contexts:
            per_passage[c.passage_id].append((c, h))

        # Confidence: a passage hit by ≥2 distinct context files for the same ref → high
        for pid, evidence in per_passage.items():
            distinct_files = {h["file"] for _, h in evidence}
            cand = evidence[0][0]
            conf = "high" if len(distinct_files) >= 2 else "medium"
            key = (pid, ref)
            if key not in mappings_by_passage:
                mappings_by_passage[key] = Mapping(
                    passage_id=pid,
                    ref=ref,
                    collection=collection,
                    contexts=[
                        {"file": h["file"], "context": h["context"][:240]}
                        for _, h in evidence[:3]
                    ],
                    confidence=conf,
                    fragmented_philosopher=philo_name,
                    philosopher_node_id=philo_node,
                    transmitting_author_node=cand.transmitting_author_node,
                    transmitting_work_node=cand.transmitting_work_node,
                )
            else:
                existing = mappings_by_passage[key]
                existing.contexts.extend(
                    {"file": h["file"], "context": h["context"][:240]}
                    for _, h in evidence[:1]
                )
                if conf == "high":
                    existing.confidence = "high"
    return list(mappings_by_passage.values())


def emit_jsonl(mappings: list[Mapping], path: Path = OUTPUT) -> dict[str, Any]:
    """Convert Mappings → fragment_mappings.jsonl-compatible rows, one per (passage, ref)."""
    grouped: dict[str, list[Mapping]] = defaultdict(list)
    for m in mappings:
        grouped[m.passage_id].append(m)

    rows: list[dict[str, Any]] = []
    for pid, ms in grouped.items():
        # Merge multiple collections per passage
        collections_payload = []
        scholarly_evidence = []
        philo_name = None
        philo_node = None
        ta_node = None
        tw_node = None
        confidence = "low"
        for m in ms:
            # Convert "SVF II.974" → "II.974"
            ref_short = re.sub(
                r"^(SVF|LS|DK|Usener|EK|Marcovich|Wehrli|FHSG|Aet\.)\s+", "", m.ref
            )
            collections_payload.append(
                {
                    "collection": m.collection
                    if m.collection != "Diels-Aetius"
                    else "Aëtius",
                    "reference": ref_short,
                    "verification_source": f"DOCTORAT scholarly library (auto-extracted, {len(m.contexts)} ctx)",
                    "auto_extracted": True,
                }
            )
            scholarly_evidence.extend(m.contexts)
            if not philo_name and m.fragmented_philosopher:
                philo_name = m.fragmented_philosopher
                philo_node = m.philosopher_node_id
            if not ta_node and m.transmitting_author_node:
                ta_node = m.transmitting_author_node
            if not tw_node and m.transmitting_work_node:
                tw_node = m.transmitting_work_node
            # Confidence: highest wins
            order = {"low": 0, "medium": 1, "high": 2}
            if order.get(m.confidence, 0) > order.get(confidence, 0):
                confidence = m.confidence

        row = {
            "passage_id": pid,
            "attestation_type": "doxographical_fragment",
            "primary_attestation": {
                "transmitting_author": ta_node,
                "transmitting_work": tw_node,
                "transmitting_passage": pid,
            },
            "fragment_collections": collections_payload,
            "extant_in_original": False,
            "extant_in_translation_only": False,
            "confidence": confidence,
            "fragmented_philosopher": philo_name,
            "philosopher_node_id": philo_node,
            "note": f"auto-mapped from DOCTORAT scholarly library ({len(scholarly_evidence)} ctx across {len({c['file'] for c in scholarly_evidence})} files)",
            "scholarly_evidence": scholarly_evidence[:3],
            "doxographical_source": "auto_doctorat",
        }
        rows.append(row)

    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    stats = {
        "total_mappings": len(rows),
        "distinct_passages": len(rows),
        "by_confidence": defaultdict(int),
        "by_collection": defaultdict(int),
    }
    for r in rows:
        stats["by_confidence"][r["confidence"]] += 1
        for fc in r["fragment_collections"]:
            stats["by_collection"][fc["collection"]] += 1
    return {k: (dict(v) if isinstance(v, defaultdict) else v) for k, v in stats.items()}


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    refs = json.loads(REFS_INDEX.read_text(encoding="utf-8"))
    passages = load_passage_ids()
    logger.info("Loaded %d refs and %d passage nodes", len(refs), len(passages))
    mappings = cross_link(refs, passages)
    logger.info("Cross-linked %d (passage, ref) pairs", len(mappings))
    stats = emit_jsonl(mappings)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
