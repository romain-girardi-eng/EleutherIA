"""Amand B6 — NEW_EDGES list.

Edges carry the Amand-claim metadata via the `metadata` field (JSON string) and
use `relation` (not `type`). All edges idempotent — verified against existing
edges by (source, target, relation) triple before insertion.
"""
from __future__ import annotations

from typing import Any

from amand_b6_utils import amand_metadata, dump_metadata


def _edge(
    *,
    source: str,
    target: str,
    relation: str,
    page_range: str = "p. 342-404",
    md_line_range: str = "ll. 17876-21130",
    chapter: str = "Livre II Ch. VII-VIII (Eusèbe + Basile)",
    amand_chapter_actual: str = "Amand 1945 B6",
    confidence: float = 0.9,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    md = amand_metadata(
        page_range=page_range,
        md_line_range=md_line_range,
        chapter=chapter,
        amand_chapter_actual=amand_chapter_actual,
        extra=extra,
    )
    return {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": confidence,
        "metadata": dump_metadata(md),
    }


# =============================================================================
# 1. evidenced_by — Eusèbe arguments → PE VI.6 section-grained passages (21)
# =============================================================================

# Map: argument_id -> list of passage section numbers (within PE VI.6)
_EVIDENCED_BY_MAP = {
    "argument_eus_carneadean_pe_vi_6_general_theme": [5],
    "argument_eus_carneadean_pe_vi_6_arg1_virtue_vice": [5, 6, 7],
    "argument_eus_carneadean_pe_vi_6_arg2_indolence": [8, 9, 10],
    "argument_eus_carneadean_pe_vi_6_arg3_exhortations_useless": [12, 13, 14, 15, 16],
    "argument_eus_carneadean_pe_vi_6_arg4_moral_action_proves_autonomy": [16, 17],
    "argument_eus_carneadean_pe_vi_6_arg5_laws_abolition": [18],
    "argument_eus_carneadean_pe_vi_6_arg6_piety_destroyed": [19],
    "argument_eus_carneadean_pe_vi_6_arg7_marionettes_consciousness": [20],
    "argument_eus_carneadean_pe_vi_6_conclusion_autexousion": [21],
}


EUSEBIUS_EVIDENCED_BY: list[dict[str, Any]] = []
for arg_id, sections in _EVIDENCED_BY_MAP.items():
    for sec in sections:
        EUSEBIUS_EVIDENCED_BY.append(_edge(
            source=arg_id,
            target=f"passage_eusebius_praep_ev_6_6_{sec}",
            relation="evidenced_by",
            page_range="p. 369-376",
            md_line_range="ll. 19053-19376",
            chapter=f"Livre II Ch. VII §IV.2 (PE VI.6.{sec})",
            amand_chapter_actual="Eusèbe de Césarée — texte témoin VI.6.4-21",
            confidence=0.92,
            extra={"pe_section_anchor": f"PE VI.6.{sec}"},
        ))


# =============================================================================
# 2. cites_primary_source — Eusèbe arguments → PE book monolithic passages (3)
# =============================================================================

EUSEBIUS_CITES_PRIMARY: list[dict[str, Any]] = [
    # Synthesis on Origenist theodicy → PE book 6 (covers VI.6.22-73)
    _edge(
        source="concept_origenist_theodicy_eus",
        target="passage_eusebius_praep_ev_book_06",
        relation="cites_primary_source",
        page_range="p. 365",
        md_line_range="ll. 18853-18874",
        chapter="Livre II Ch. VII §III.3 (PE VI.6.22-73)",
        amand_chapter_actual="Eusèbe — théodicée VI.6.22-73",
        confidence=0.85,
        extra={"pe_reference": "PE VI.6.22-73", "passage_granularity": "monolithic_book"},
    ),
    # Synthesis on Eusebius' platonism → PE books 11-13
    _edge(
        source="synthesis_amand1945_eus_dependence_origen",
        target="passage_eusebius_praep_ev_book_11",
        relation="cites_primary_source",
        page_range="p. 365-367",
        md_line_range="ll. 18918-18987",
        chapter="Livre II Ch. VII §III.3 (PE VI.11 = Origen Comm. in Gen.)",
        amand_chapter_actual="Eusèbe — transmission origénienne",
        confidence=0.9,
        extra={"pe_reference": "PE VI.11.1-81 (Origen Comm. in Gen. citation)"},
    ),
]


# =============================================================================
# 3. cites_primary_source — Basile/Greg Naz → work-shells (Hex VI absent) (6)
# =============================================================================

BASIL_CITES_WORKS: list[dict[str, Any]] = [
    _edge(
        source="argument_basil_carneadean_hex_vi_7_laws_useless",
        target="work_basil_hexaemeron",
        relation="cites_primary_source",
        page_range="p. 400",
        md_line_range="ll. 20900-20931",
        chapter="Livre II Ch. VIII §IV (Hex VI.7 topos 1)",
        amand_chapter_actual="Basile — Hex VI.7",
        confidence=0.92,
        extra={"hex_reference": "Hex VI.7 (PG 29.133BC)"},
    ),
    _edge(
        source="argument_basil_carneadean_hex_vi_7_christian_hopes_destroyed",
        target="work_basil_hexaemeron",
        relation="cites_primary_source",
        page_range="p. 400",
        md_line_range="ll. 20932-20935",
        chapter="Livre II Ch. VIII §IV (Hex VI.7 topos 2)",
        amand_chapter_actual="Basile — Hex VI.7",
        confidence=0.92,
        extra={"hex_reference": "Hex VI.7 (PG 29.133BC)"},
    ),
    _edge(
        source="argument_basil_observation_impossible_at_birth",
        target="work_basil_hexaemeron",
        relation="cites_primary_source",
        page_range="p. 395-396",
        md_line_range="ll. 20648-20697",
        chapter="Livre II Ch. VIII §III.2 (Hex VI.5)",
        amand_chapter_actual="Basile — Hex VI.5",
        confidence=0.92,
        extra={"hex_reference": "Hex VI.5 (PG 29.128B-129C)"},
    ),
    _edge(
        source="argument_basil_zodiac_animal_absurdity",
        target="work_basil_hexaemeron",
        relation="cites_primary_source",
        page_range="p. 396",
        md_line_range="ll. 20699-20713",
        chapter="Livre II Ch. VIII §III.2 (Hex VI.7 section 2)",
        amand_chapter_actual="Basile — Hex VI.7",
        confidence=0.92,
        extra={"hex_reference": "Hex VI.7 (PG 29.129C-132B)"},
    ),
    _edge(
        source="argument_basil_kings_born_daily",
        target="work_basil_hexaemeron",
        relation="cites_primary_source",
        page_range="p. 397",
        md_line_range="ll. 20756-20793",
        chapter="Livre II Ch. VIII §III.2 (Hex VI.7 section 3)",
        amand_chapter_actual="Basile — Hex VI.7",
        confidence=0.92,
        extra={"hex_reference": "Hex VI.7 (PG 29.132B-133D)"},
    ),
    _edge(
        source="argument_greg_naz_carmen_dogm_5_carneadean",
        target="work_gregory_naz_carmina_dogmatica",
        relation="cites_primary_source",
        page_range="p. 403",
        md_line_range="ll. 21038-21072",
        chapter="Livre II Ch. VIII Note suppl. (Carm. dogm. 5 vers 44-52)",
        amand_chapter_actual="Grégoire de Nazianze — Carm. dogm. 5",
        confidence=0.9,
        extra={"poem_reference": "Carm. dogm. 5 vers 44-52 (PG 37.427A-428A)"},
    ),
]


# =============================================================================
# 4. transmits_to / influences (JALON PISTE 1 + filiations) (8)
# =============================================================================

FILIATION_EDGES: list[dict[str, Any]] = [
    # *** JALON PISTE 1 *** Origen Philocalia 23 → Eusebius PE VI.11
    _edge(
        source="work_origen_philocalia",
        target="work_eusebius_praeparatio_evangelica",
        relation="transmits_to",
        page_range="p. 366-367",
        md_line_range="ll. 18941-18951",
        chapter="Livre II Ch. VII §III.3 (PE VI.11 ≈ Phil. 23)",
        amand_chapter_actual="Filiation Origène→Eusèbe (Phil. 23 → PE VI.11)",
        confidence=0.95,
        extra={
            "filiation_type": "near-literal textual transmission",
            "amand_note_3_p366": "La dissertation antiastrologique et antifataliste d'Origène nous a été conservée également, et d'une manière plus complète, par Basile et Grégoire de Nazianze dans leur Philocalie d'Origène, où cette digression constitue l'interminable chapitre 23",
            "piste_1_jalon": True,
        },
    ),
    # Eusebius → Origen
    _edge(
        source="person_eusebius_caesarea_d339",
        target="person_origen_alexandria_185_254ce_s9t0u1v2",
        relation="influenced_by",
        page_range="p. 354-355",
        md_line_range="ll. 18379-18386",
        chapter="Livre II Ch. VII §II (origéniste)",
        amand_chapter_actual="Eusèbe disciple d'Origène",
        confidence=0.95,
        extra={"transmission_channel": "Pamphilus → Eusebius (Caesarean library)"},
    ),
    # Basil → Origen
    _edge(
        source="person_basil_great_d379",
        target="person_origen_alexandria_185_254ce_s9t0u1v2",
        relation="influenced_by",
        page_range="p. 384, 391, 399",
        md_line_range="ll. 20146-20155, 20502-20503, 20879-20884",
        chapter="Livre II Ch. VIII (dépendance origénienne)",
        amand_chapter_actual="Basile disciple d'Origène",
        confidence=0.92,
        extra={"transmission_channel": "Philocalia compilation with Gregory of Nazianzus"},
    ),
    # Gregory of Nazianzus → Origen
    _edge(
        source="person_gregory_nazianzus_d389",
        target="person_origen_alexandria_185_254ce_s9t0u1v2",
        relation="influenced_by",
        page_range="p. 384, 401",
        md_line_range="ll. 20146-20155, 20937-20949",
        chapter="Livre II Ch. VIII (collab. Philocalia)",
        amand_chapter_actual="Grégoire Naz disciple d'Origène",
        confidence=0.9,
        extra={"transmission_channel": "Philocalia compilation with Basil"},
    ),
    # Basil <-> Gregory of Nazianzus (Philocalia collaboration)
    _edge(
        source="person_basil_great_d379",
        target="person_gregory_nazianzus_d389",
        relation="collaborates_with",
        page_range="p. 384",
        md_line_range="ll. 20147-20149",
        chapter="Livre II Ch. VIII §I (Basile/Grégoire Naz amitié)",
        amand_chapter_actual="Amitié et collaboration Philocalia",
        confidence=0.98,
        extra={"collaboration_output": "Philocalia of Origen"},
    ),
    # Eusebius → Basil (cappadocian chain)
    _edge(
        source="person_eusebius_caesarea_d339",
        target="person_basil_great_d379",
        relation="precedes",
        page_range="p. 383-384",
        md_line_range="ll. 20100-20149",
        chapter="Livre II Ch. VIII §I (Basile successor cappadocien)",
        amand_chapter_actual="Chaîne cappadocienne Eusèbe→Basile",
        confidence=0.85,
        extra={"chain": "Cappadocian patristic transmission"},
    ),
    # Basil → Gregory of Nyssa (already may exist as 'sibling_of'; we add 'precedes' for doctrine)
    _edge(
        source="person_basil_great_d379",
        target="person_gregory_nyssa_d395",
        relation="precedes",
        page_range="p. 384",
        md_line_range="ll. 20161-20163",
        chapter="Livre II Ch. VIII §I (frère puîné, Hex influence)",
        amand_chapter_actual="Basile précède Grégoire Nysse",
        confidence=0.92,
        extra={"chain": "Cappadocian fraternal transmission"},
    ),
    # Origen Philocalia 23 → Basil Hex VI.7 (Christian insertion source)
    _edge(
        source="work_origen_philocalia",
        target="work_basil_hexaemeron",
        relation="transmits_to",
        page_range="p. 399-400",
        md_line_range="ll. 20879-20920",
        chapter="Livre II Ch. VIII §IV (filiation origénienne Christian insertion)",
        amand_chapter_actual="Origen Phil. 23.1 → Basile Hex VI.7 (insert chrétien)",
        confidence=0.88,
        extra={
            "amand_assertion": "L'élément chrétien adventice inséré chez Basile a grande chance d'avoir été inspiré par Origène (Phil. 23.1)",
        },
    ),
]


# =============================================================================
# 5. cites — Eusèbe → primary sources copied in PE VI (5)
# =============================================================================

EUSEBIUS_COPIES: list[dict[str, Any]] = [
    # Eusebius cites Alexander of Aphrodisias (PE VI.9)
    _edge(
        source="person_eusebius_caesarea_d339",
        target="person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        relation="cites",
        page_range="p. 366",
        md_line_range="ll. 18902-18936",
        chapter="Livre II Ch. VII §III.3 (PE VI.9)",
        amand_chapter_actual="Eusèbe copie Alexandre De Fato 16-20",
        confidence=0.95,
        extra={
            "pe_chapter": "PE VI.9.1-31",
            "amand_assertion": "Le chapitre 9 est constitué d'extraits et de résumés de cet important ouvrage (De Fato)",
        },
    ),
    # Eusebius cites Porphyry (PE VI.1-5 + V.16-36)
    _edge(
        source="person_eusebius_caesarea_d339",
        target="person_porphyry",
        relation="cites",
        page_range="p. 360-363",
        md_line_range="ll. 18640-18811",
        chapter="Livre II Ch. VII §III (PE V.16-36, VI.1-5)",
        amand_chapter_actual="Eusèbe copie Porphyre Philosophie des oracles",
        confidence=0.95,
        extra={
            "pe_chapters": "PE VI.1-5 (Philosophy from Oracles) + V.16-36 (oracles)",
        },
    ),
    # Eusebius cites Bardesane (PE VI.10)
    _edge(
        source="person_eusebius_caesarea_d339",
        target="person_bardesanes_the_syrian_3r8s0u76",
        relation="cites",
        page_range="p. 366",
        md_line_range="ll. 18908-18917",
        chapter="Livre II Ch. VII §III.3 (PE VI.10)",
        amand_chapter_actual="Eusèbe copie Bardesane Livre des lois",
        confidence=0.95,
        extra={
            "pe_chapter": "PE VI.10.1-48",
            "amand_assertion": "Le studieux compilateur a copié deux longs fragments de la version grecque du dialogue bardesanien",
        },
    ),
    # Eusebius cites Diogenianos (PE VI.8)
    _edge(
        source="person_eusebius_caesarea_d339",
        target="person_diogenianos_8m3n5p21",
        relation="cites",
        page_range="p. 365",
        md_line_range="ll. 18880-18900",
        chapter="Livre II Ch. VII §III.3 (PE VI.8)",
        amand_chapter_actual="Eusèbe copie Diogénianos Περὶ εἱμαρμένης",
        confidence=0.95,
        extra={
            "pe_chapter": "PE VI.8.1-38",
            "amand_assertion": "Eusèbe transcrit trois longs passages du Περὶ εἱμαρμένης de l'Épicurien Diogénianos",
        },
    ),
    # Eusebius cites Diogenes of Oenoanda (Oinomaos — closest existing match is diogenes_oenoanda, NOT
    # the Cynic Oinomaos of Gadara; but the Cynic is referenced. Skip if no proper node exists.)
    # We add the link via the work-shell stub for completeness:
    _edge(
        source="person_eusebius_caesarea_d339",
        target="work_eusebius_praeparatio_evangelica",
        relation="authored",
        page_range="p. 342-381",
        md_line_range="ll. 17876-20099",
        chapter="Livre II Ch. VII (Eusèbe autorité de la PE)",
        amand_chapter_actual="Eusèbe auteur PE",
        confidence=0.99,
    ),
]


# =============================================================================
# 6. authored_by — works → persons (4 new authored relations)
# =============================================================================

AUTHORSHIP_EDGES: list[dict[str, Any]] = [
    _edge(
        source="work_eusebius_contra_hieroclem",
        target="person_eusebius_caesarea_d339",
        relation="authored_by",
        confidence=0.98,
    ),
    _edge(
        source="work_eusebius_demonstratio_evangelica",
        target="person_eusebius_caesarea_d339",
        relation="authored_by",
        confidence=0.98,
    ),
    _edge(
        source="work_basil_hexaemeron",
        target="person_basil_great_d379",
        relation="authored_by",
        confidence=0.98,
    ),
    _edge(
        source="work_basil_homiliae_quod_deus_non_est_auctor_malorum",
        target="person_basil_great_d379",
        relation="authored_by",
        confidence=0.98,
    ),
    _edge(
        source="work_gregory_naz_carmina_dogmatica",
        target="person_gregory_nazianzus_d389",
        relation="authored_by",
        confidence=0.98,
    ),
]


# =============================================================================
# 7. contains — Synthesis VI.6 → 7 arguments + conclusion (8)
# =============================================================================

CONTAINS_EDGES: list[dict[str, Any]] = []
_SYNTH_WITNESS = "synthesis_amand1945_eus_witness_n4"
for arg_idx in [
    "general_theme",
    "arg1_virtue_vice",
    "arg2_indolence",
    "arg3_exhortations_useless",
    "arg4_moral_action_proves_autonomy",
    "arg5_laws_abolition",
    "arg6_piety_destroyed",
    "arg7_marionettes_consciousness",
    "conclusion_autexousion",
]:
    CONTAINS_EDGES.append(_edge(
        source=_SYNTH_WITNESS,
        target=f"argument_eus_carneadean_pe_vi_6_{arg_idx}",
        relation="contains",
        confidence=0.95,
        page_range="p. 369-376",
        md_line_range="ll. 19045-19376",
        chapter="Livre II Ch. VII §IV.2 (structure du texte témoin)",
        amand_chapter_actual="Eusèbe — structure VI.6.4-21",
    ))


# =============================================================================
# 8. addresses — Arguments → concepts (7)
# =============================================================================

ADDRESSES_EDGES: list[dict[str, Any]] = [
    _edge(
        source="argument_eus_carneadean_pe_vi_6_conclusion_autexousion",
        target="concept_autexousion_pe_vi_6_eusebius",
        relation="addresses",
        confidence=0.95,
    ),
    _edge(
        source="argument_eus_carneadean_pe_vi_6_arg7_marionettes_consciousness",
        target="concept_neurospastoumenoi_carneadean_metaphor",
        relation="addresses",
        confidence=0.95,
    ),
    _edge(
        source="synthesis_amand1945_eus_witness_n4",
        target="concept_heimarmene_demonic_invention_eus",
        relation="addresses",
        confidence=0.9,
    ),
    _edge(
        source="synthesis_amand1945_eus_dependence_origen",
        target="concept_origenist_theodicy_eus",
        relation="addresses",
        confidence=0.95,
    ),
    _edge(
        source="synthesis_amand1945_basil_hex_vi_7_amand_origin_point",
        target="concept_chaldeans_astrology_basil",
        relation="addresses",
        confidence=0.92,
    ),
    _edge(
        source="argument_basil_carneadean_hex_vi_7_laws_useless",
        target="concept_to_eph_hemin_basil",
        relation="addresses",
        confidence=0.9,
    ),
    _edge(
        source="synthesis_amand1945_basil_origen_christian_insertion",
        target="concept_synergism_basil_origenist",
        relation="addresses",
        confidence=0.92,
    ),
]


# =============================================================================
# 9. claimed_by — synthesis → scholar Amand (anchor links) (11)
# =============================================================================

CLAIMED_BY_EDGES: list[dict[str, Any]] = []
for synth_id in [
    "synthesis_amand1945_eus_witness_n4",
    "synthesis_amand1945_eus_carneadean_source_question",
    "synthesis_amand1945_eus_psychological_argument_modernity",
    "synthesis_amand1945_eus_dependence_origen",
    "synthesis_amand1945_eus_philological_fidelity",
    "synthesis_amand1945_basil_hex_vi_7_amand_origin_point",
    "synthesis_amand1945_basil_only_two_carneadean_topoi",
    "synthesis_amand1945_basil_origen_christian_insertion",
    "synthesis_amand1945_basil_popular_homily_register",
    "synthesis_amand1945_greg_naz_carmen_dogm_5_carneadean_echo",
    "synthesis_amand1945_greg_naz_school_commonplace",
]:
    CLAIMED_BY_EDGES.append(_edge(
        source=synth_id,
        target="scholar_amand_de_mendieta_e",
        relation="claimed_by",
        confidence=0.99,
    ))


# =============================================================================
# UNIFIED EDGE LIST
# =============================================================================

NEW_EDGES: list[dict[str, Any]] = (
    EUSEBIUS_EVIDENCED_BY
    + EUSEBIUS_CITES_PRIMARY
    + BASIL_CITES_WORKS
    + FILIATION_EDGES
    + EUSEBIUS_COPIES
    + AUTHORSHIP_EDGES
    + CONTAINS_EDGES
    + ADDRESSES_EDGES
    + CLAIMED_BY_EDGES
)
