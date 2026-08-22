#!/usr/bin/env python3
"""Audited repair plan for the residual KG/corpus parity debt.

This module is data-selection logic only.  It never writes repository data.
The companion applier uses the records produced here to reconcile genuine
twins and to demote false/stale ``db_passage_id`` declarations without
changing any ancient text.

The six ``passage_plut_cn_*`` rows are deliberately excluded: they belong to
the separately owned Plutarch ``tlg135``/``tlg138`` source adjudication.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

STAMP = "parity_zero_2026_08_18"
BACKUP_SUFFIX = ".bak-parity_zero_2026_08_18"

SYNC_NODE = "sync_node_from_corpus"
SYNC_CORPUS = "sync_corpus_from_kg"
DEMOTE = "demote_false_twin"

# Frozen after the Clement grounding and work-canonical repair waves.
BASELINE_FILE_SHA256 = {
    "kg/nodes.jsonl": "a7b15942b36c984eb48ad29af7fa0ece73c97e322fe087573e7122002c471988",
    "corpus/passages.jsonl": "d2035ed92731eb08959a7695287aa394535c1c99b32c797d5de04e7a9e86e7d2",
    "corpus/citations.jsonl": "b98a37e7eaa9240f81161f858c1d088c1e9bab0fdf7ee08545e4d90ac4c3ede0",
}

EVIDENCE_FILE_SHA256 = {
    "corpus/manifest.jsonl": "33a14073211b4e11827e82ba95d366ca44e2d45d45e50940d0d7721ce52965cc",
    "audit/2026-08-17_parity_propagation_plan.md": "9e803c7c3e1d955c52a3e9a88c95c83cb598578bc8a3ba26f4b7b6bca08fd843",
    "audit/2026-08-16_second_sweep_applied.md": "bb3b9787f41e0ded05c0eedfd556b73d7e522876de1275afc1165de4d93e1b0d",
    "audit/kg_work_child_canonical_known_ambiguities.json": "2b44ce4984307cd5cdcc65cad9d0ca869cbd2c4570ed015ecb28d0fed4b17c2f",
    "audit/primary_fetch/urn_cts_latinlit_phi0474_phi049_lat/mapping.json": "706c551da43326111cc65b75c5d419bdd627323928b469c92390484040ac5349",
    "audit/primary_wave/chunk_locus_changelog.jsonl": "a9975c0c1645b13772c9d6dbd0152d58ec48dda8bd2782cd5eb38eeae6b5bf7d",
    "audit/primary_wave/restore_changelog.jsonl": "ed5cd7d65e17c4df3f3d4f88ca7766d7f3f0025aa0a5e9e56042af843f252b65",
}

# Filled after the deterministic dry-run is generated.  The applier verifies
# both values before accepting a previously applied state.
APPLIED_NODES_SHA256 = (
    "79c30b8eaec874fa53747f9cea3ddcb84cd0598fada23f0bb6c77f5648b44f50"
)
APPLIED_PASSAGES_SHA256 = (
    "2b3fed3e8d22fc4eb0af0f5fc875b8b39d4626e1685a33653a39c51fd0bf8c52"
)
# Coordinated final state after the separately owned tlg135 Plutarch split.
FINAL_NODES_SHA256 = "bdf75f26ddf27dca289b1a54b6b7007ea913c01d88ba43f49dd6129a47aff0b7"
FINAL_PASSAGES_SHA256 = (
    "7a0a484d1146206fbd8d3dfe4b9b2b21fa31a0649c870461a53c52c2961d71d2"
)
FINAL_CITATIONS_SHA256 = (
    "d3d74079b280c2038495e9e396dee8339331b9b764432c1669ef1e132e3d1293"
)

EXPECTED_BEFORE = {
    "declared_twins": 11072,
    "shared_twins": 10994,
    "violations": 3051,
    "missing_twins": 78,
    "missing_citations": 0,
    "canonical_ref_mismatches": 1145,
    "cts_urn_mismatches": 1828,
}

# Only the separately owned tlg135/tlg138 cohort remains after this plan.
EXPECTED_AFTER = {
    "declared_twins": 10780,
    "shared_twins": 10780,
    "violations": 6,
    "missing_twins": 0,
    "missing_citations": 0,
    "canonical_ref_mismatches": 6,
    "cts_urn_mismatches": 0,
}

EXPECTED_FINAL = {
    "declared_twins": 10780,
    "shared_twins": 10780,
    "violations": 0,
    "missing_twins": 0,
    "missing_citations": 0,
    "canonical_ref_mismatches": 0,
    "cts_urn_mismatches": 0,
}

EXCLUDED_PLUTARCH_NODE_IDS = tuple(
    f"passage_plut_cn_{number}" for number in range(1, 7)
)

EXPECTED_FAMILY_NODES = {
    "aristotle_de_generatione_true_twin": 3,
    "aristotle_ne_excerpt_relation": 12,
    "aspasius_true_twin": 6,
    "athenagoras_english_true_twin": 10,
    "athenagoras_greek_translation_relation": 10,
    "augustine_civitate_unreliable_twin": 9,
    "barnabas_english_to_greek_relation": 1,
    "barnabas_greek_true_twin": 1,
    "boethius_provenance_conflict": 128,
    "cicero_edition_conflict": 48,
    "clement_english_true_twin": 1,
    "clement_greek_to_english_relation": 1,
    "epictetus_unresolved_locus": 1,
    "hegesippus_misclassified_corpus": 1,
    "justin_apologia_prima_true_twin": 68,
    "justin_apologia_secunda_true_twin": 15,
    "justin_trypho_composite_relation": 2,
    "justin_trypho_true_twin": 748,
    "philo_manifest_opp_truth": 172,
    "plato_28_segmentation_relation": 1,
    "plato_true_twin": 75,
    "plotinus_true_twin": 646,
    "plutarch_stoic_rep_true_twin": 47,
    "pseudo_plutarch_fine_to_coarse": 19,
    "tatian_fine_to_coarse": 59,
}

EXPECTED_FAMILY_VIOLATIONS = {
    "aristotle_de_generatione_true_twin": 3,
    "aristotle_ne_excerpt_relation": 14,
    "aspasius_true_twin": 6,
    "athenagoras_english_true_twin": 10,
    "athenagoras_greek_translation_relation": 10,
    "augustine_civitate_unreliable_twin": 14,
    "barnabas_english_to_greek_relation": 1,
    "barnabas_greek_true_twin": 1,
    "boethius_provenance_conflict": 255,
    "cicero_edition_conflict": 48,
    "clement_english_true_twin": 1,
    "clement_greek_to_english_relation": 1,
    "epictetus_unresolved_locus": 1,
    "hegesippus_misclassified_corpus": 1,
    "justin_apologia_prima_true_twin": 68,
    "justin_apologia_secunda_true_twin": 15,
    "justin_trypho_composite_relation": 4,
    "justin_trypho_true_twin": 1496,
    "philo_manifest_opp_truth": 173,
    "plato_28_segmentation_relation": 2,
    "plato_true_twin": 150,
    "plotinus_true_twin": 646,
    "plutarch_stoic_rep_true_twin": 47,
    "pseudo_plutarch_fine_to_coarse": 19,
    "tatian_fine_to_coarse": 59,
}

EXPECTED_ACTION_NODES = {
    DEMOTE: 292,
    SYNC_CORPUS: 172,
    SYNC_NODE: 1620,
}
EXPECTED_REPAIR_NODES = 2084
EXPECTED_FIXED_VIOLATIONS = 3045
EXPECTED_PLAN_SHA256 = (
    "97131ae4e8392fdcba05de26a8eaffcf0741474217220596c983b9518ad35241"
)

EXPECTED_FIELD_CHANGES = {
    "node_canonical_ref": 975,
    "node_cts_urn": 1470,
    "corpus_cts_urn": 172,
    "db_passage_id_removed": 292,
    "related_corpus_passage_id": 289,
    "former_corpus_passage_id": 3,
}

FAMILY_EVIDENCE = {
    "aristotle_de_generatione_true_twin": (
        "The node and corpus texts are byte-identical, their CTS loci are "
        "identical (2.9-2.11), and the corpus labels expose the real book/chapter "
        "instead of the legacy ordinal chunk labels Cons. 1-3."
    ),
    "aristotle_ne_excerpt_relation": (
        "The KG rows are whole chapters while the corpus rows are selected "
        "Bekker spans or analytical excerpt records; the relationship is useful "
        "but not an exact segmentation twin."
    ),
    "aspasius_true_twin": (
        "NFC/whitespace-normalized texts and CTS URNs are identical; the corpus "
        "canonical reference only expands the work title."
    ),
    "athenagoras_english_true_twin": (
        "The _en node description is byte-identical to the corpus row, whose "
        "work id is the explicit English source family."
    ),
    "athenagoras_greek_translation_relation": (
        "A Greek source node and its English translation node both declare the "
        "same English corpus UUID; only the English node is the exact twin."
    ),
    "augustine_civitate_unreliable_twin": (
        "The 2026-08-17 parity audit records coarse/fine source drift for six "
        "rows and intentional footer-junk deletion for three stale UUIDs."
    ),
    "barnabas_english_to_greek_relation": (
        "The English node points to the Greek SC 172 corpus row; preserve it as "
        "a cross-language relation, not an exact twin."
    ),
    "barnabas_greek_true_twin": (
        "The Greek corpus text is contained verbatim in the Greek SC node and "
        "the corpus work id is the Greek source family."
    ),
    "boethius_provenance_conflict": (
        "Three incompatible local identities coexist: KG CTS lat7127.011, "
        "corpus CTS stoa0058.stoa001, and work id phi2089.phi002; the manifest "
        "names lat7127.011.  Preserve the link without asserting witness identity."
    ),
    "cicero_edition_conflict": (
        "The local 48-row critical mapping establishes corpus phi054 "
        "(Mueller/Perseus), while KG descriptions retain the earlier phi056 "
        "witness.  Same section is a relation, not the same witness."
    ),
    "clement_english_true_twin": (
        "The _en node is byte-identical to the English SC 167 corpus row."
    ),
    "clement_greek_to_english_relation": (
        "The Greek SC 167 node points to an English corpus row; preserve the "
        "translation relation without declaring an exact twin."
    ),
    "epictetus_unresolved_locus": (
        "The primary-wave stamp says locus_defaked and records that no edition "
        "locus was resolved; neither legacy Epict. 185 nor Diss. 0.0.5-0.0.8 "
        "may be promoted as canonical."
    ),
    "hegesippus_misclassified_corpus": (
        "The 2026-08-16 audited correction proves the payload is Hegesippus, "
        "while its corpus row remains catalogued as Alcinous, Didasc. 1."
    ),
    "justin_apologia_prima_true_twin": (
        "Exact UUID/CTS/text alignment; the corpus reference expands the title."
    ),
    "justin_apologia_secunda_true_twin": (
        "Exact UUID/CTS/text alignment; the corpus reference expands the title."
    ),
    "justin_trypho_composite_relation": (
        "Two KG subpassages (88.5 and 140.4) point to corpus composites "
        "88.4-5 and 140.4-141.2; preserve the source-span relation without "
        "claiming identical segmentation."
    ),
    "justin_trypho_true_twin": (
        "The authoritative Perseus corpus family and node suffix agree on every "
        "two-level locus; underscores are a legacy KG serialization of CTS dots."
    ),
    "philo_manifest_opp_truth": (
        "All 172 texts match after NFC/whitespace normalization and the corpus "
        "manifest explicitly names opp-grc1 as the source; 1st1K-grc1 in the "
        "passage rows is provenance drift."
    ),
    "plato_28_segmentation_relation": (
        "Timaeus 28 has a 910-letter KG span but only an 89-letter corpus "
        "excerpt; the shared section is not an exact segmentation twin."
    ),
    "plato_true_twin": (
        "For the other 75 Timaeus rows, node suffix, corpus reference, passage "
        "locus, and Perseus edition align; corpus supplies the explicit version."
    ),
    "plotinus_true_twin": (
        "Canonical references already agree and both sides name perseus-grc1; "
        "the legacy KG URN was truncated to a book/chapter prefix."
    ),
    "plutarch_stoic_rep_true_twin": (
        "CTS URNs and near-verbatim Perseus texts agree; the corpus reference "
        "only expands the work title.  This is tlg136, not the excluded split."
    ),
    "pseudo_plutarch_fine_to_coarse": (
        "Nineteen deleted fine-grained UUIDs each have one surviving snapshot "
        "citation to one of eleven coarser tlg108 corpus passages."
    ),
    "tatian_fine_to_coarse": (
        "Fifty-six deleted fine-grained UUIDs and three enriched shared rows map "
        "to coarser or mixed analytical chapter records; preserve related spans."
    ),
}

FAMILY_REASON = dict(FAMILY_EVIDENCE)


class PlanError(RuntimeError):
    """Raised when selection or evidence no longer matches the audited state."""


@dataclass(frozen=True)
class RepairRecord:
    family: str
    action: str
    node_id: str
    former_passage_id: str
    related_passage_id: str | None
    violation_fields: tuple[str, ...]
    violation_count: int
    expected_node_metadata_sha256: str
    expected_description_sha256: str
    expected_passage_sha256: str | None
    expected_related_passage_sha256: str | None
    node_updates: dict[str, Any]
    node_removals: tuple[str, ...]
    passage_updates: dict[str, Any]
    stamp_value: dict[str, Any]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def normalized_letters(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or "")).casefold()
    text = text.replace("ς", "σ")
    return "".join(char for char in text if unicodedata.category(char).startswith("L"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PlanError(message)


def _violation_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("node_id") or ""),
        str(row.get("passage_id") or ""),
        str(row.get("field") or ""),
        str(row.get("reason") or ""),
    )


def _validate_evidence_files(data_root: Path) -> dict[str, Any]:
    for relative, expected in EVIDENCE_FILE_SHA256.items():
        path = data_root / relative
        actual = sha256_path(path)
        if actual != expected:
            raise PlanError(
                f"evidence file drift: {relative} is {actual}, expected {expected}"
            )

    manifest = read_jsonl(data_root / "corpus" / "manifest.jsonl")
    philo = [
        row
        for row in manifest
        if row.get("canonical_id") == "urn_cts_greeklit_tlg0018_tlg001_grc"
    ]
    _require(len(philo) == 1, "Philo manifest authority is not unique")
    _require(
        philo[0].get("source") == "scaife:urn:cts:greekLit:tlg0018.tlg001.opp-grc1",
        "Philo manifest no longer establishes opp-grc1",
    )
    _require(philo[0].get("passages") == 172, "Philo manifest count drift")

    boethius = [
        row
        for row in manifest
        if row.get("canonical_id") == "urn_cts_latinlit_phi2089_phi002_eng"
    ]
    _require(len(boethius) == 1, "Boethius manifest row is not unique")
    _require(
        boethius[0].get("source") == "scaife:urn:cts:latinLit:lat7127.011.perseus-lat1",
        "Boethius manifest source drift",
    )

    cicero_mapping = json.loads(
        (
            data_root
            / "audit"
            / "primary_fetch"
            / "urn_cts_latinlit_phi0474_phi049_lat"
            / "mapping.json"
        ).read_text(encoding="utf-8")
    )
    _require(len(cicero_mapping) == 48, "Cicero critical mapping count drift")
    cicero_by_id = {str(row["passage_id"]): row for row in cicero_mapping}
    _require(len(cicero_by_id) == 48, "Cicero mapping passage ids are not unique")

    ambiguity = json.loads(
        (
            data_root / "audit" / "kg_work_child_canonical_known_ambiguities.json"
        ).read_text(encoding="utf-8")
    )
    plutarch = ambiguity.get("known_ambiguities", {}).get(
        "work_plutarch_de_communibus_notitiis", {}
    )
    _require(
        plutarch.get("child_canonical") == "urn:cts:greekLit:tlg0007.tlg135",
        "excluded Plutarch child identity drift",
    )
    _require(
        plutarch.get("work_candidates") == ["urn:cts:greekLit:tlg0007.tlg138"],
        "excluded Plutarch parent candidate drift",
    )
    return {"cicero_by_id": cicero_by_id}


def _family_action(wanted: str) -> tuple[str, str] | None:
    if wanted in {"passage_just_tryph_88_5", "passage_just_tryph_140_4"}:
        return "justin_trypho_composite_relation", DEMOTE
    if wanted.startswith("passage_just_tryph_"):
        return "justin_trypho_true_twin", SYNC_NODE
    if wanted.startswith("passage_plotinus_"):
        return "plotinus_true_twin", SYNC_NODE
    if wanted.startswith("passage_boethius_cons_"):
        return "boethius_provenance_conflict", DEMOTE
    if wanted.startswith("passage_philo_de_opif_"):
        return "philo_manifest_opp_truth", SYNC_CORPUS
    if wanted == "passage_plato_tim_28":
        return "plato_28_segmentation_relation", DEMOTE
    if wanted.startswith("passage_plato_tim_"):
        return "plato_true_twin", SYNC_NODE
    if wanted.startswith("passage_just_apol1_"):
        return "justin_apologia_prima_true_twin", SYNC_NODE
    if wanted.startswith("passage_just_apol2_"):
        return "justin_apologia_secunda_true_twin", SYNC_NODE
    if wanted.startswith("passage_cic_fat_"):
        return "cicero_edition_conflict", DEMOTE
    if wanted.startswith("passage_plut_stoic_rep_"):
        return "plutarch_stoic_rep_true_twin", SYNC_NODE
    if wanted in EXCLUDED_PLUTARCH_NODE_IDS:
        return None
    if wanted.startswith("passage_athenagoras_leg_"):
        if wanted.endswith("_en"):
            return "athenagoras_english_true_twin", SYNC_NODE
        return "athenagoras_greek_translation_relation", DEMOTE
    if wanted.startswith("passage_tatian_"):
        return "tatian_fine_to_coarse", DEMOTE
    if wanted.startswith("passage_plut_fat_"):
        return "pseudo_plutarch_fine_to_coarse", DEMOTE
    if wanted.startswith("passage_arist_ne_"):
        return "aristotle_ne_excerpt_relation", DEMOTE
    if wanted.startswith("passage_aug_civ_"):
        return "augustine_civitate_unreliable_twin", DEMOTE
    if wanted.startswith("passage_aspasius_"):
        return "aspasius_true_twin", SYNC_NODE
    if wanted.startswith("passage_arist_gen_corr_"):
        return "aristotle_de_generatione_true_twin", SYNC_NODE
    if wanted.startswith("passage_sc_anonymous_"):
        if wanted.endswith("_en"):
            return "barnabas_english_to_greek_relation", DEMOTE
        return "barnabas_greek_true_twin", SYNC_NODE
    if wanted.startswith("passage_sc_clementofrome_"):
        if wanted.endswith("_en"):
            return "clement_english_true_twin", SYNC_NODE
        return "clement_greek_to_english_relation", DEMOTE
    if wanted == "passage_hegesippus_hypomnemata_fragments":
        return "hegesippus_misclassified_corpus", DEMOTE
    if wanted == "passage_epict_185_s185":
        return "epictetus_unresolved_locus", DEMOTE
    raise PlanError(f"unclassified residual parity node: {wanted}")


def _validate_family(
    family: str,
    wanted: str,
    node: dict[str, Any],
    data: dict[str, Any],
    passage: dict[str, Any] | None,
    fields: tuple[str, ...],
    evidence: dict[str, Any],
) -> None:
    field_set = set(fields)
    if passage is not None:
        kg_ref = data.get("canonical_ref")
        corpus_ref = passage.get("canonical_ref")
        kg_urn = data.get("cts_urn")
        corpus_urn = passage.get("cts_urn")
    else:
        kg_ref = data.get("canonical_ref")
        corpus_ref = kg_urn = corpus_urn = None

    if family in {"justin_trypho_true_twin", "justin_trypho_composite_relation"}:
        suffix = wanted.removeprefix("passage_just_tryph_")
        _require(field_set == {"canonical_ref", "cts_urn"}, wanted)
        expected_ref = suffix.replace("_", ".")
        if family == "justin_trypho_composite_relation":
            expected_ref = {
                "passage_just_tryph_88_5": "88.4-5",
                "passage_just_tryph_140_4": "140.4-141.2",
            }[wanted]
        _require(kg_ref == suffix and corpus_ref == expected_ref, wanted)
        _require(str(kg_urn).endswith(":" + suffix), wanted)
        _require(
            str(corpus_urn).endswith(":" + suffix.replace("_", ".")),
            wanted,
        )
    elif family == "plotinus_true_twin":
        _require(field_set == {"cts_urn"} and kg_ref == corpus_ref, wanted)
        _require(
            ".perseus-grc1:" in str(kg_urn)
            or str(kg_urn).startswith("urn:cts:greekLit:tlg2000.tlg001:"),
            wanted,
        )
        _require(".perseus-grc1:" in str(corpus_urn), wanted)
    elif family == "boethius_provenance_conflict":
        _require("cts_urn" in field_set, wanted)
        _require("lat7127.011.perseus-lat1" in str(kg_urn), wanted)
        _require(
            "stoa0058.stoa001.perseus-lat2" in str(corpus_urn)
            or "lat7127.011.perseus-lat1:34" in str(corpus_urn),
            wanted,
        )
    elif family == "philo_manifest_opp_truth":
        _require("cts_urn" in field_set, wanted)
        _require(".opp-grc1:" in str(kg_urn), wanted)
        _require(".1st1K-grc1:" in str(corpus_urn), wanted)
        kg_locus = str(kg_urn).split(":")[-1]
        corpus_locus = str(corpus_urn).split(":")[-1]
        if wanted == "passage_philo_de_opif_164":
            _require(kg_locus == "164" and corpus_locus == "163-164", wanted)
        else:
            _require(kg_locus == corpus_locus, wanted)
        _require(
            normalized_letters(node.get("description"))
            == normalized_letters(passage.get("text_content")),
            f"{wanted}: Philo texts are no longer identical",
        )
    elif family in {"plato_true_twin", "plato_28_segmentation_relation"}:
        suffix = wanted.removeprefix("passage_plato_tim_")
        _require(field_set == {"canonical_ref", "cts_urn"}, wanted)
        expected_ref = (
            "Tim. 28"
            if family == "plato_28_segmentation_relation"
            else f"Timaeus {suffix}"
        )
        _require(kg_ref == suffix and corpus_ref == expected_ref, wanted)
        _require(str(kg_urn).endswith(":" + suffix), wanted)
        if family == "plato_28_segmentation_relation":
            _require(str(corpus_urn).endswith(":" + suffix + "a"), wanted)
            node_len = len(normalized_letters(node.get("description")))
            corpus_len = len(normalized_letters(passage.get("text_content")))
            _require(
                node_len > corpus_len * 5, "Timaeus 28 segmentation drift vanished"
            )
        else:
            _require(str(corpus_urn).endswith(".perseus-grc2:" + suffix), wanted)
    elif family.startswith("justin_apologia_"):
        title = "Apologia Prima" if "prima" in family else "Apologia Secunda"
        _require(field_set == {"canonical_ref"}, wanted)
        allowed_refs = {f"{title} {kg_ref}"}
        if family == "justin_apologia_prima_true_twin" and kg_ref in {"43", "44"}:
            allowed_refs.add(f"Justin, 1 Apology {kg_ref}")
        _require(corpus_ref in allowed_refs and kg_urn == corpus_urn, wanted)
    elif family == "cicero_edition_conflict":
        _require(field_set == {"cts_urn"}, wanted)
        _require("phi0474.phi056:" in str(kg_urn), wanted)
        mapped = evidence["cicero_by_id"].get(str(passage.get("passage_id")))
        _require(mapped is not None, f"{wanted}: absent from Cicero critical map")
        _require(mapped.get("correct_cts_urn") == corpus_urn, wanted)
    elif family == "plutarch_stoic_rep_true_twin":
        _require(field_set == {"canonical_ref"} and kg_urn == corpus_urn, wanted)
        _require(corpus_ref == f"De Stoicorum Repugnantiis {kg_ref}", wanted)
        _require("tlg0007.tlg136" in str(kg_urn), wanted)
    elif family.startswith("athenagoras_"):
        _require(field_set == {"canonical_ref"}, wanted)
        equal = node.get("description") == passage.get("text_content")
        _require(equal == family.endswith("english_true_twin"), wanted)
        _require(
            passage.get("work_canonical_id") == "sc379_athenagoras_legatio_eng",
            wanted,
        )
    elif family == "tatian_fine_to_coarse":
        _require(wanted.startswith("passage_tatian_"), wanted)
        if passage is None:
            _require(field_set == {"passage_id"}, wanted)
        else:
            _require(field_set == {"canonical_ref"}, wanted)
            _require(str(corpus_ref).startswith("Orat. "), wanted)
    elif family == "pseudo_plutarch_fine_to_coarse":
        _require(passage is None and field_set == {"passage_id"}, wanted)
        _require(
            data.get("work_canonical_id") == "urn:cts:greekLit:tlg0007.tlg108", wanted
        )
    elif family == "aristotle_ne_excerpt_relation":
        _require(passage is not None and "canonical_ref" in field_set, wanted)
        _require(data.get("work_title") == "Ἠθικὰ Νικομάχεια", wanted)
        _require(node.get("description") != passage.get("text_content"), wanted)
    elif family == "augustine_civitate_unreliable_twin":
        _require(data.get("author") == "Augustine", wanted)
        if passage is None:
            _require(field_set == {"passage_id"}, wanted)
            _require(data.get("deep_audit_2026_08_16") == "flag_empty_passages", wanted)
        else:
            _require(field_set <= {"canonical_ref", "cts_urn"}, wanted)
            _require("cts_urn" in field_set, wanted)
    elif family == "aspasius_true_twin":
        _require(field_set == {"canonical_ref"} and kg_urn == corpus_urn, wanted)
        _require(corpus_ref == f"In Ethica Nicomachea Commentaria {kg_ref}", wanted)
        _require(
            normalized_letters(node.get("description"))
            == normalized_letters(passage.get("text_content")),
            wanted,
        )
    elif family == "aristotle_de_generatione_true_twin":
        _require(field_set == {"canonical_ref"} and kg_urn == corpus_urn, wanted)
        _require(node.get("description") == passage.get("text_content"), wanted)
        _require(str(corpus_ref).startswith("De Gen. et Corr. II."), wanted)
    elif family in {
        "barnabas_english_to_greek_relation",
        "barnabas_greek_true_twin",
        "clement_english_true_twin",
        "clement_greek_to_english_relation",
    }:
        _require(field_set == {"canonical_ref"}, wanted)
        equal = node.get("description") == passage.get("text_content")
        if family in {"clement_english_true_twin"}:
            _require(equal, wanted)
        if family in {
            "barnabas_english_to_greek_relation",
            "clement_greek_to_english_relation",
        }:
            _require(not equal, wanted)
    elif family == "hegesippus_misclassified_corpus":
        _require(field_set == {"canonical_ref"}, wanted)
        _require(data.get("mislabel_correction_2026_08_16"), wanted)
        _require(kg_ref is None and corpus_ref == "Didasc. 1", wanted)
        _require("tlg1398" in str(data.get("work_canonical_id")), wanted)
    elif family == "epictetus_unresolved_locus":
        _require(field_set == {"canonical_ref"}, wanted)
        prior = passage.get("parity_propagation_2026_08_17", {})
        _require(prior.get("family") == "epictetus_unresolved_urn_defake", wanted)
        _require("unresolved" in str(data.get("cts_urn_note")), wanted)
    else:
        raise PlanError(f"no family validator for {family}")


def _stamp_value(
    family: str,
    action: str,
    wanted: str,
    former_passage_id: str,
    related_passage_id: str | None,
    fields: tuple[str, ...],
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "family": family,
        "action": action,
        "kg_node_id": wanted,
        "former_db_passage_id": former_passage_id,
        "violation_fields": list(fields),
        "evidence": FAMILY_EVIDENCE[family],
    }
    if related_passage_id is not None:
        value["related_corpus_passage_id"] = related_passage_id
    return value


def build_repair_records(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    violations: Iterable[dict[str, Any]],
    data_root: Path,
) -> tuple[RepairRecord, ...]:
    """Build and fully account for the frozen residual violation set."""

    evidence = _validate_evidence_files(data_root)
    nodes_by_id = {node_id(node): node for node in nodes}
    passages_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    citation_counts = Counter(
        (
            str(row.get("passage_id") or ""),
            str(row.get("kg_node_id") or ""),
        )
        for row in citations
    )
    current_snapshot_ids: dict[str, list[str]] = defaultdict(list)
    for row in citations:
        passage_id = str(row.get("passage_id") or "")
        wanted = str(row.get("kg_node_id") or "")
        if (
            row.get("citation_type") == "snapshot_passage_node"
            and passage_id in passages_by_id
        ):
            current_snapshot_ids[wanted].append(passage_id)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    all_keys: set[tuple[str, str, str, str]] = set()
    for row in violations:
        key = _violation_key(row)
        if key in all_keys:
            raise PlanError(f"duplicate violation row: {key}")
        all_keys.add(key)
        grouped[(key[0], key[1])].append(row)

    excluded_keys: set[tuple[str, str, str, str]] = set()
    selected_keys: set[tuple[str, str, str, str]] = set()
    records: list[RepairRecord] = []

    for (wanted, former_passage_id), rows in sorted(grouped.items()):
        fields = tuple(sorted(str(row["field"]) for row in rows))
        if wanted in EXCLUDED_PLUTARCH_NODE_IDS:
            _require(fields == ("canonical_ref",), f"{wanted}: excluded issue drift")
            _require(all(row["reason"] == "locus_mismatch" for row in rows), wanted)
            excluded_keys.update(_violation_key(row) for row in rows)
            continue

        classified = _family_action(wanted)
        if classified is None:
            raise PlanError(f"unexpected unselected node: {wanted}")
        family, action = classified
        node = nodes_by_id.get(wanted)
        if node is None:
            raise PlanError(f"{wanted}: KG node missing")
        data = metadata(node)
        _require(
            str(data.get("db_passage_id") or "") == former_passage_id,
            f"{wanted}: db_passage_id precondition drift",
        )
        _require(STAMP not in data, f"{wanted}: parity-zero stamp pre-exists")
        for field in (
            "related_corpus_passage_id",
            "former_corpus_passage_id",
            "parity_status",
            "parity_reason",
        ):
            _require(field not in data, f"{wanted}: {field} pre-exists")

        passage = passages_by_id.get(former_passage_id)
        if passage is not None:
            _require(
                citation_counts[(former_passage_id, wanted)] == 1,
                f"{wanted}/{former_passage_id}: exact citation count drift",
            )
        else:
            _require(
                all(row["reason"] == "missing_corpus_twin" for row in rows),
                f"{wanted}: absent passage has non-missing issue",
            )

        _validate_family(family, wanted, node, data, passage, fields, evidence)

        node_updates: dict[str, Any] = {}
        node_removals: tuple[str, ...] = ()
        passage_updates: dict[str, Any] = {}
        related_passage_id: str | None = former_passage_id if passage else None

        if action == SYNC_NODE:
            _require(passage is not None, f"{wanted}: sync target missing")
            for field in fields:
                _require(field in {"canonical_ref", "cts_urn"}, wanted)
                node_updates[field] = passage.get(field)
        elif action == SYNC_CORPUS:
            _require(passage is not None, f"{wanted}: sync target missing")
            for field in fields:
                if field == "cts_urn":
                    desired_urn = str(passage.get(field)).replace(
                        ".1st1K-grc1:", ".opp-grc1:"
                    )
                    passage_updates[field] = desired_urn
                    if data.get(field) != desired_urn:
                        node_updates[field] = desired_urn
                elif field == "canonical_ref":
                    # The corpus's 163-164 span is more precise than the KG's
                    # legacy node suffix 164.
                    node_updates[field] = passage.get(field)
                else:
                    raise PlanError(f"{wanted}: unsupported Philo field {field}")
        elif action == DEMOTE:
            node_removals = ("db_passage_id",)
            if passage is None:
                candidates = sorted(set(current_snapshot_ids.get(wanted, [])))
                if family in {
                    "tatian_fine_to_coarse",
                    "pseudo_plutarch_fine_to_coarse",
                }:
                    _require(
                        len(candidates) == 1,
                        f"{wanted}: expected one surviving coarse snapshot, got {candidates}",
                    )
                    related_passage_id = candidates[0]
                else:
                    _require(not candidates, f"{wanted}: unexpected current relation")
                    related_passage_id = None
            if related_passage_id is None:
                node_updates["former_corpus_passage_id"] = former_passage_id
                node_updates["parity_status"] = "stale_deleted_twin"
            else:
                node_updates["related_corpus_passage_id"] = related_passage_id
                node_updates["parity_status"] = "related_not_exact_twin"
            node_updates["parity_reason"] = FAMILY_REASON[family]
        else:
            raise PlanError(f"{wanted}: unsupported action {action}")

        stamp_value = _stamp_value(
            family,
            action,
            wanted,
            former_passage_id,
            related_passage_id,
            fields,
        )
        related_passage = (
            passages_by_id.get(related_passage_id)
            if related_passage_id is not None
            else None
        )
        records.append(
            RepairRecord(
                family=family,
                action=action,
                node_id=wanted,
                former_passage_id=former_passage_id,
                related_passage_id=related_passage_id,
                violation_fields=fields,
                violation_count=len(rows),
                expected_node_metadata_sha256=sha256_text(canonical_json(data)),
                expected_description_sha256=sha256_text(
                    str(node.get("description") or "")
                ),
                expected_passage_sha256=(
                    sha256_text(canonical_json(passage))
                    if passage is not None
                    else None
                ),
                expected_related_passage_sha256=(
                    sha256_text(canonical_json(related_passage))
                    if related_passage is not None
                    else None
                ),
                node_updates=node_updates,
                node_removals=node_removals,
                passage_updates=passage_updates,
                stamp_value=stamp_value,
            )
        )
        selected_keys.update(_violation_key(row) for row in rows)

    _require(len(excluded_keys) == 6, "excluded Plutarch violation count drift")
    _require(
        {key[0] for key in excluded_keys} == set(EXCLUDED_PLUTARCH_NODE_IDS),
        "excluded Plutarch cohort drift",
    )
    _require(selected_keys | excluded_keys == all_keys, "violation coverage gap")
    _require(not selected_keys & excluded_keys, "selected/excluded overlap")

    records.sort(key=lambda row: (row.family, row.node_id, row.former_passage_id))
    family_nodes = Counter(row.family for row in records)
    family_violations = Counter()
    actions = Counter(row.action for row in records)
    for row in records:
        family_violations[row.family] += row.violation_count
    _require(
        dict(sorted(family_nodes.items())) == EXPECTED_FAMILY_NODES,
        f"family node cardinality drift: {dict(sorted(family_nodes.items()))}",
    )
    _require(
        dict(sorted(family_violations.items())) == EXPECTED_FAMILY_VIOLATIONS,
        "family violation cardinality drift: "
        f"{dict(sorted(family_violations.items()))}",
    )
    _require(
        dict(sorted(actions.items())) == EXPECTED_ACTION_NODES,
        f"action drift: {actions}",
    )
    _require(len(records) == EXPECTED_REPAIR_NODES, "repair node count drift")
    _require(
        sum(row.violation_count for row in records) == EXPECTED_FIXED_VIOLATIONS,
        "selected violation count drift",
    )
    _require(
        len({row.node_id for row in records}) == len(records),
        "a KG node was selected more than once",
    )
    return tuple(records)


def record_digest(records: tuple[RepairRecord, ...]) -> str:
    payload = [
        {
            "family": row.family,
            "action": row.action,
            "node_id": row.node_id,
            "former_passage_id": row.former_passage_id,
            "related_passage_id": row.related_passage_id,
            "violation_fields": row.violation_fields,
            "violation_count": row.violation_count,
            "expected_node_metadata_sha256": row.expected_node_metadata_sha256,
            "expected_description_sha256": row.expected_description_sha256,
            "expected_passage_sha256": row.expected_passage_sha256,
            "expected_related_passage_sha256": row.expected_related_passage_sha256,
            "node_updates": row.node_updates,
            "node_removals": row.node_removals,
            "passage_updates": row.passage_updates,
            "stamp_value": row.stamp_value,
        }
        for row in records
    ]
    return sha256_text(canonical_json(payload))
