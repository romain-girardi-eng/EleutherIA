"""Frede 2011 B1 — NEW_EDGES list.

Allowed relations per knowledge graph/ontology/edge_types.json :

  authored_by         : src argument/passage/publication/quote/synthesis/work -> tgt person
  wrote               : src person -> tgt work
  contains            : src argument/concept/debate/quote/work/source_collection -> tgt
                        argument/argument_framework/concept/debate/passage/text_fragment/work
  cites_primary_source: src argument/publication/person -> tgt passage/work
  discusses           : src argument/argument_framework/concept/conceptual_evolution/debate/
                        passage/person/publication/synthesis/work -> tgt argument/concept/debate/
                        group/person/school/synthesis/work
  evidenced_by        : src argument/concept/group/school -> tgt passage
  influences          : src person/school/work -> tgt person/school/work
  influenced_by       : src person/school/work/event -> tgt person/school/work
  precedes            : src argument/person/event/publication/work -> tgt argument/person/event/work
  critiques           : src many -> tgt argument/concept/controversy/person/publication/school/synthesis/work
  responds_to         : src many -> tgt argument/work/concept/debate/person
  employs             : src argument/concept/passage/person/work -> tgt argument/argument_framework/concept
  interprets          : src argument/person/publication/modern_interpretation/work -> tgt
                        argument/argument_framework/concept/passage/person/school/work
  belongs_to_school   : src person -> tgt school
  member_of           : src concept/person/work -> tgt group/school
  part_of             : src argument/concept/passage/synthesis/text_fragment/work -> tgt
                        concept/passage/work/source_collection
  supports            : src argument/concept/event/group/passage/person/synthesis/work -> tgt argument/concept/person

Note: synthesis -> publication is NOT a valid `part_of` per ontology (part_of
target_types = concept/passage/work/source_collection). Anchoring to the
publication is preserved via metadata.publication on every node (set by
frede_metadata()).
"""
from __future__ import annotations

from typing import Any

from frede_2011_b1_utils import FREDE_PUBLICATION_ID, FREDE_SCHOLAR_ID

NEW_EDGES: list[dict[str, Any]] = []


def _edge(source: str, target: str, relation: str, *, confidence: float = 0.85, **md: Any) -> dict[str, Any]:
    e: dict[str, Any] = {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": confidence,
    }
    if md:
        e["metadata"] = md
    return e


# =============================================================================
# 1. PUBLICATION ↔ AUTHOR/EDITOR/FOREWORD
# =============================================================================
NEW_EDGES.extend([
    _edge(FREDE_PUBLICATION_ID, FREDE_SCHOLAR_ID, "authored_by", confidence=0.99),
    # Long edited the volume - represented as "interprets" of Frede's work / "influences" Frede posthumously
    _edge("scholar_long_anthony", FREDE_SCHOLAR_ID, "influences", confidence=0.95,
          frede_note="A. A. Long as editor of the posthumous volume; longtime philosophical interlocutor at Berkeley/Oxford"),
    _edge("scholar_sedley_david", FREDE_SCHOLAR_ID, "influences", confidence=0.85,
          frede_note="David Sedley wrote the Foreword; longtime collaborator (LS = Long & Sedley 1987 The Hellenistic Philosophers, abbreviated throughout the book)"),
])


# =============================================================================
# 2. SYNTHESIS authorship — each chapter synthesis -> scholar_frede_michael
# =============================================================================
SYNTHESIS_IDS = [
    "synthesis_frede2011_ch1_introduction",
    "synthesis_frede2011_ch2_aristotle",
    "synthesis_frede2011_ch3_emergence_of_will_in_stoicism",
    "synthesis_frede2011_ch4_later_platonist_peripatetic_contributions",
    "synthesis_frede2011_ch5_emergence_of_free_will_in_stoicism",
    "synthesis_frede2011_ch6_platonist_peripatetic_criticisms",
    "synthesis_frede2011_ch7_origen",
    "synthesis_frede2011_ch8_plotinus",
    "synthesis_frede2011_ch9_augustine",
    "synthesis_frede2011_ch10_conclusion",
    "synthesis_frede2011_methodology_history_not_apologetic",
]
for sid in SYNTHESIS_IDS:
    NEW_EDGES.append(_edge(sid, FREDE_SCHOLAR_ID, "authored_by"))

# Chapter syntheses precede each other in the book ordering (1->2->...->10)
CHAPTER_ORDER = [
    "synthesis_frede2011_ch1_introduction",
    "synthesis_frede2011_ch2_aristotle",
    "synthesis_frede2011_ch3_emergence_of_will_in_stoicism",
    "synthesis_frede2011_ch4_later_platonist_peripatetic_contributions",
    "synthesis_frede2011_ch5_emergence_of_free_will_in_stoicism",
    "synthesis_frede2011_ch6_platonist_peripatetic_criticisms",
    "synthesis_frede2011_ch7_origen",
    "synthesis_frede2011_ch8_plotinus",
    "synthesis_frede2011_ch9_augustine",
    "synthesis_frede2011_ch10_conclusion",
]
# precedes target = argument/person/event/work — synthesis NOT in target list.
# So we skip precedes-chains for syntheses; book order is encoded in metadata.


# =============================================================================
# 3. ARGUMENT authorship — Frede's scholarly arguments -> scholar_frede_michael
# =============================================================================
ARGUMENT_IDS = [
    "argument_frede_2011_notion_is_technical_and_datable",
    "argument_frede_2011_aristotle_no_will_no_free_will",
    "argument_frede_2011_stoic_assent_is_proto_will",
    "argument_frede_2011_epictetus_first_free_will",
    "argument_frede_2011_autexousion_stoic_origin_then_christian",
    "argument_frede_2011_alexander_libertarian_dead_end",
    "argument_frede_2011_origen_stoic_christianity_anti_gnostic",
    "argument_frede_2011_origen_differences_from_platonism_not_christianity",
    "argument_frede_2011_plotinus_hierarchized_freedom",
    "argument_frede_2011_plotinus_divine_will_not_judeo_christian",
    "argument_frede_2011_augustine_no_new_notion_vs_dihle",
    "argument_frede_2011_augustine_stoic_paul_via_marius_victorinus",
    "argument_frede_2011_christianity_anti_gnostic_anti_astral_motivation",
    "argument_frede_2011_ancient_notion_not_basically_flawed",
]
for aid in ARGUMENT_IDS:
    NEW_EDGES.append(_edge(aid, FREDE_SCHOLAR_ID, "authored_by"))


# =============================================================================
# 4. PUBLICATION discusses ancient persons + works
# =============================================================================
NEW_EDGES.extend([
    _edge(FREDE_PUBLICATION_ID, "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_zeno_citium_334_262bce", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_carneades_214_129bce_l2m3n4o5", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_musonius_rufus_30_101ce", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_plotinus_d270", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_porphyry", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_augustine_hippo_d430", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_justin_martyr_2c_ce", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_tatian", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_clement_alexandria", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_alcinous_2c_ce", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_galen_pergamon_129_216ce", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_epicurus_341_270bce_j0k1l2m3", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_democritus_460_370bce_g7h8i9j0", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_seneca_4bce_65ce_a1b2c3d4", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_plato_428_348bce_a1b2c3d4", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_posidonius_apameia_135_51bce", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_aulus_gellius_125_180ce", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "person_maximus_confessor_d662", "discusses"),
])


# =============================================================================
# 5. PUBLICATION cites_primary_source — key ancient works
# =============================================================================
NEW_EDGES.extend([
    _edge(FREDE_PUBLICATION_ID, "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "cites_primary_source",
          confidence=0.95,
          frede_note="Ch. 2 base — EN III.1-5, EN VII (akrasia)"),
    _edge(FREDE_PUBLICATION_ID, "work_epictetus_discourses", "cites_primary_source",
          confidence=0.98,
          frede_note="Ch. 3 §3 + Ch. 5 §2 - primary anchor for first free will"),
    _edge(FREDE_PUBLICATION_ID, "work_epictetus_enchiridion", "cites_primary_source",
          confidence=0.9),
    _edge(FREDE_PUBLICATION_ID, "work_de_fato_cicero_44bce_b9c4e5d2", "cites_primary_source",
          confidence=0.95,
          frede_note="Ch. 6 §1 - Carneades-Chrysippus debate evidence"),
    _edge(FREDE_PUBLICATION_ID, "work_de_fato_alexander_c200ce_o6p7q8r9", "cites_primary_source",
          confidence=0.95,
          frede_note="Ch. 6 — De fato XI, XIV, XXVIII, XXXVIII, 192,22ff"),
    _edge(FREDE_PUBLICATION_ID, "work_plotinus_ennead_vi_8_d8b9c5a4", "cites_primary_source",
          confidence=0.98,
          frede_note="Ch. 8 — full-text close reading of Ennead VI.8"),
    _edge(FREDE_PUBLICATION_ID, "work_de_principiis_origen_230s_v2w3x4y5", "cites_primary_source",
          confidence=0.95,
          frede_note="Ch. 7 — De princ. III.1 (Peri autexousiou) and preface"),
    _edge(FREDE_PUBLICATION_ID, "work_origen_philocalia", "cites_primary_source",
          confidence=0.95,
          frede_note="Ch. 7 — Philocalia ch. 21-27 preserves De princ. III.1 in Greek"),
    _edge(FREDE_PUBLICATION_ID, "work_origen_contra_celsum_sc132", "cites_primary_source",
          confidence=0.85,
          frede_note="Ch. 7 — CC 5.61 against Gnostics"),
    _edge(FREDE_PUBLICATION_ID, "work_origen_commentary_romans", "cites_primary_source",
          confidence=0.85,
          frede_note="Ch. 7 — Origen Comm. Rom. on Pauline necessitism passages"),
    _edge(FREDE_PUBLICATION_ID, "work_augustine_de_libero_arbitrio", "cites_primary_source",
          confidence=0.98,
          frede_note="Ch. 9 — De lib. ar. central text"),
    _edge(FREDE_PUBLICATION_ID, "work_augustine_confessiones_viii", "cites_primary_source",
          confidence=0.9,
          frede_note="Ch. 9 — Conf. VIII.5-12 (tolle lege)"),
    _edge(FREDE_PUBLICATION_ID, "work_tatian_oratio", "cites_primary_source",
          confidence=0.95,
          frede_note="Ch. 7 — Oratio 7.1 first use of eleutheria tēs prohaireseōs"),
    _edge(FREDE_PUBLICATION_ID, "work_didaskalikos_alcinous_2nd_ce_q7r8s9t0", "cites_primary_source",
          confidence=0.7,
          frede_note="Ch. 4 — Middle Platonist context"),
])


# =============================================================================
# 6. PUBLICATION discusses concepts (Frede's analytical engagement)
# =============================================================================
NEW_EDGES.extend([
    _edge(FREDE_PUBLICATION_ID, "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_hekousion_voluntary_aristotle_a1b2c3d4", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_akousion_involuntary_aristotle_b2c3d4e5", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_voluntas_y7z8a9b0", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_boulesis_rational_desire_ef9f861d", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_synkatathesis_stoic_assent", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_liberum_arbitrium_u3v4w5x6", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_akrasia_weakness_of_will", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_horme_alex", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_thelesis_willing_87d2b3cf", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_plotinian_intellectual_eph_hemin", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_eph_hemin_kyrion_plut", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_eph_hemin_one_sided_causative", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_eph_hemin_two_sided_potestative", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_libertas_indifferentiae_4f8a9b57", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_libertas_spontaneitatis_5g9b0c68", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_to_eph_hemin_nemesius", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_frede_general_schema_of_free_will", "discusses"),
    _edge(FREDE_PUBLICATION_ID, "concept_frede_inner_life_late_stoic", "discusses"),
])


# =============================================================================
# 7. PUBLICATION critiques / responds_to modern scholars
# =============================================================================
NEW_EDGES.extend([
    # Critiques Dihle 1982 (primary interlocutor)
    _edge(FREDE_PUBLICATION_ID, "pub_dihle_1982_theory_will", "critiques",
          confidence=0.98,
          frede_note="Central polemic: Dihle's claim that Augustine invents the modern notion of will"),
    _edge(FREDE_PUBLICATION_ID, "scholar_dihle_albrecht", "critiques",
          confidence=0.98,
          frede_note="The whole book is structured as a sustained response to Dihle 1982"),
    # Responds to Bobzien 1998 — pub-to-pub responds_to is not allowed (target must be argument/work/concept/debate/person)
    # We replace by `critiques` on the pub target (allowed: pub -> publication critiques is allowed) and `responds_to` on the person.
    _edge(FREDE_PUBLICATION_ID, "pub_bobzien_1998_inadvertent", "critiques",
          confidence=0.85,
          frede_note="Frede largely accepts Bobzien's Stoic determinism analysis but extends/refines the late-birth thesis (note: 'critiques' here = scholarly engagement, not rejection)"),
    _edge(FREDE_PUBLICATION_ID, "person_bobzien_susanne_contemporary", "responds_to",
          confidence=0.9,
          frede_note="Frede 2011 Ch. 1 note 10 + Ch. 3 note 18 + Ch. 5 throughout - engages Bobzien 1998 directly"),
    # Engages Kahn (Kahn 1988 'Discovering the Will: From Aristotle to Augustine')
    _edge(FREDE_PUBLICATION_ID, "scholar_kahn_charles", "responds_to",
          confidence=0.85,
          frede_note="Kahn 1988 placed will-emergence at Seneca-Epictetus; Frede specifies Epictetus precisely"),
    # Engages Sorabji
    _edge(FREDE_PUBLICATION_ID, "person_sorabji_richard_contemporary", "responds_to",
          confidence=0.85,
          frede_note="Frede aligns with Sorabji 2006 ch. 10 on prohairesis but pushes further (FIRST free will, not just prefiguration)"),
    # Engages Broadie, Kenny on Aristotle
    _edge(FREDE_PUBLICATION_ID, "scholar_kenny_anthony", "responds_to",
          confidence=0.85,
          frede_note="Kenny 1979 Aristotle's Theory of the Will - Frede rejects the will-reading of Aristotle"),
    _edge(FREDE_PUBLICATION_ID, "scholar_broadie_sarah", "responds_to",
          confidence=0.8,
          frede_note="Broadie 1991 ch. 3 'The Voluntary' - Frede draws on her reading"),
    # Crouzel (cited on Origen)
    _edge(FREDE_PUBLICATION_ID, "scholar_crouzel_henri", "responds_to",
          confidence=0.7,
          frede_note="Crouzel 1956 Theologie de l'image de Dieu chez Origene - 2 mentions"),
])


# =============================================================================
# 8. SCHOLARLY ARGUMENTS discuss the ancient figures/works they thematize
# =============================================================================
NEW_EDGES.extend([
    # Ch.2 argument
    _edge("argument_frede_2011_aristotle_no_will_no_free_will",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("argument_frede_2011_aristotle_no_will_no_free_will",
          "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "discusses"),
    _edge("argument_frede_2011_aristotle_no_will_no_free_will",
          "concept_hekousion_voluntary_aristotle_a1b2c3d4", "discusses"),
    _edge("argument_frede_2011_aristotle_no_will_no_free_will",
          "concept_akrasia_weakness_of_will", "discusses"),
    _edge("argument_frede_2011_aristotle_no_will_no_free_will",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "cites_primary_source"),
    # Ch.3 argument (Stoic proto-will)
    _edge("argument_frede_2011_stoic_assent_is_proto_will",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("argument_frede_2011_stoic_assent_is_proto_will",
          "person_zeno_citium_334_262bce", "discusses"),
    _edge("argument_frede_2011_stoic_assent_is_proto_will",
          "concept_synkatathesis_stoic_assent", "discusses"),
    # Ch.5 argument (Epictetus first free will) - flagship
    _edge("argument_frede_2011_epictetus_first_free_will",
          "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("argument_frede_2011_epictetus_first_free_will",
          "person_musonius_rufus_30_101ce", "discusses"),
    _edge("argument_frede_2011_epictetus_first_free_will",
          "work_epictetus_discourses", "cites_primary_source"),
    _edge("argument_frede_2011_epictetus_first_free_will",
          "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", "discusses"),
    _edge("argument_frede_2011_epictetus_first_free_will",
          "concept_frede_inner_life_late_stoic", "employs"),
    # Autexousion stoic-Christian transmission
    _edge("argument_frede_2011_autexousion_stoic_origin_then_christian",
          "person_musonius_rufus_30_101ce", "discusses"),
    _edge("argument_frede_2011_autexousion_stoic_origin_then_christian",
          "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("argument_frede_2011_autexousion_stoic_origin_then_christian",
          "person_justin_martyr_2c_ce", "discusses"),
    _edge("argument_frede_2011_autexousion_stoic_origin_then_christian",
          "person_tatian", "discusses"),
    # Ch.6 (Alexander)
    _edge("argument_frede_2011_alexander_libertarian_dead_end",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge("argument_frede_2011_alexander_libertarian_dead_end",
          "person_carneades_214_129bce_l2m3n4o5", "discusses"),
    _edge("argument_frede_2011_alexander_libertarian_dead_end",
          "work_de_fato_alexander_c200ce_o6p7q8r9", "cites_primary_source"),
    _edge("argument_frede_2011_alexander_libertarian_dead_end",
          "work_de_fato_cicero_44bce_b9c4e5d2", "cites_primary_source"),
    # Ch.7 (Origen)
    _edge("argument_frede_2011_origen_stoic_christianity_anti_gnostic",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("argument_frede_2011_origen_stoic_christianity_anti_gnostic",
          "work_de_principiis_origen_230s_v2w3x4y5", "cites_primary_source"),
    _edge("argument_frede_2011_origen_stoic_christianity_anti_gnostic",
          "work_origen_philocalia", "cites_primary_source"),
    _edge("argument_frede_2011_origen_differences_from_platonism_not_christianity",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    # Ch.8 (Plotinus)
    _edge("argument_frede_2011_plotinus_hierarchized_freedom",
          "person_plotinus_d270", "discusses"),
    _edge("argument_frede_2011_plotinus_hierarchized_freedom",
          "work_plotinus_ennead_vi_8_d8b9c5a4", "cites_primary_source"),
    _edge("argument_frede_2011_plotinus_hierarchized_freedom",
          "concept_plotinian_intellectual_eph_hemin", "discusses"),
    _edge("argument_frede_2011_plotinus_divine_will_not_judeo_christian",
          "person_plotinus_d270", "discusses"),
    _edge("argument_frede_2011_plotinus_divine_will_not_judeo_christian",
          "work_plotinus_ennead_vi_8_d8b9c5a4", "cites_primary_source"),
    # Ch.9 (Augustine)
    _edge("argument_frede_2011_augustine_no_new_notion_vs_dihle",
          "person_augustine_hippo_d430", "discusses"),
    _edge("argument_frede_2011_augustine_no_new_notion_vs_dihle",
          "work_augustine_de_libero_arbitrio", "cites_primary_source"),
    _edge("argument_frede_2011_augustine_no_new_notion_vs_dihle",
          "scholar_dihle_albrecht", "critiques"),
    _edge("argument_frede_2011_augustine_no_new_notion_vs_dihle",
          "pub_dihle_1982_theory_will", "critiques"),
    _edge("argument_frede_2011_augustine_stoic_paul_via_marius_victorinus",
          "person_augustine_hippo_d430", "discusses"),
    # Ch.7 (Christianity motivation)
    _edge("argument_frede_2011_christianity_anti_gnostic_anti_astral_motivation",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("argument_frede_2011_christianity_anti_gnostic_anti_astral_motivation",
          "person_augustine_hippo_d430", "discusses"),
    # Ch.10 evaluative
    _edge("argument_frede_2011_ancient_notion_not_basically_flawed",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
])


# =============================================================================
# 9. SYNTHESES discuss their chapter content
# =============================================================================
NEW_EDGES.extend([
    # Ch.1
    _edge("synthesis_frede2011_ch1_introduction",
          "concept_frede_general_schema_of_free_will", "discusses"),
    _edge("synthesis_frede2011_ch1_introduction",
          "scholar_dihle_albrecht", "critiques"),
    # Ch.2
    _edge("synthesis_frede2011_ch2_aristotle",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("synthesis_frede2011_ch2_aristotle",
          "argument_frede_2011_aristotle_no_will_no_free_will", "discusses"),
    _edge("synthesis_frede2011_ch2_aristotle",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "discusses"),
    # Ch.3
    _edge("synthesis_frede2011_ch3_emergence_of_will_in_stoicism",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_frede2011_ch3_emergence_of_will_in_stoicism",
          "person_zeno_citium_334_262bce", "discusses"),
    _edge("synthesis_frede2011_ch3_emergence_of_will_in_stoicism",
          "argument_frede_2011_stoic_assent_is_proto_will", "discusses"),
    _edge("synthesis_frede2011_ch3_emergence_of_will_in_stoicism",
          "concept_synkatathesis_stoic_assent", "discusses"),
    # Ch.4
    _edge("synthesis_frede2011_ch4_later_platonist_peripatetic_contributions",
          "person_porphyry", "discusses"),
    _edge("synthesis_frede2011_ch4_later_platonist_peripatetic_contributions",
          "person_alcinous_2c_ce", "discusses"),
    # Ch.5
    _edge("synthesis_frede2011_ch5_emergence_of_free_will_in_stoicism",
          "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("synthesis_frede2011_ch5_emergence_of_free_will_in_stoicism",
          "person_musonius_rufus_30_101ce", "discusses"),
    _edge("synthesis_frede2011_ch5_emergence_of_free_will_in_stoicism",
          "argument_frede_2011_epictetus_first_free_will", "discusses"),
    _edge("synthesis_frede2011_ch5_emergence_of_free_will_in_stoicism",
          "concept_frede_inner_life_late_stoic", "discusses"),
    _edge("synthesis_frede2011_ch5_emergence_of_free_will_in_stoicism",
          "work_epictetus_discourses", "discusses"),
    # Ch.6
    _edge("synthesis_frede2011_ch6_platonist_peripatetic_criticisms",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge("synthesis_frede2011_ch6_platonist_peripatetic_criticisms",
          "person_carneades_214_129bce_l2m3n4o5", "discusses"),
    _edge("synthesis_frede2011_ch6_platonist_peripatetic_criticisms",
          "argument_frede_2011_alexander_libertarian_dead_end", "discusses"),
    _edge("synthesis_frede2011_ch6_platonist_peripatetic_criticisms",
          "work_de_fato_alexander_c200ce_o6p7q8r9", "discusses"),
    # Ch.7
    _edge("synthesis_frede2011_ch7_origen",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("synthesis_frede2011_ch7_origen",
          "argument_frede_2011_origen_stoic_christianity_anti_gnostic", "discusses"),
    _edge("synthesis_frede2011_ch7_origen",
          "argument_frede_2011_origen_differences_from_platonism_not_christianity", "discusses"),
    _edge("synthesis_frede2011_ch7_origen",
          "argument_frede_2011_christianity_anti_gnostic_anti_astral_motivation", "discusses"),
    _edge("synthesis_frede2011_ch7_origen",
          "work_de_principiis_origen_230s_v2w3x4y5", "discusses"),
    _edge("synthesis_frede2011_ch7_origen",
          "person_justin_martyr_2c_ce", "discusses"),
    _edge("synthesis_frede2011_ch7_origen",
          "person_tatian", "discusses"),
    _edge("synthesis_frede2011_ch7_origen",
          "person_clement_alexandria", "discusses"),
    # Ch.8
    _edge("synthesis_frede2011_ch8_plotinus",
          "person_plotinus_d270", "discusses"),
    _edge("synthesis_frede2011_ch8_plotinus",
          "argument_frede_2011_plotinus_hierarchized_freedom", "discusses"),
    _edge("synthesis_frede2011_ch8_plotinus",
          "argument_frede_2011_plotinus_divine_will_not_judeo_christian", "discusses"),
    _edge("synthesis_frede2011_ch8_plotinus",
          "work_plotinus_ennead_vi_8_d8b9c5a4", "discusses"),
    # Ch.9
    _edge("synthesis_frede2011_ch9_augustine",
          "person_augustine_hippo_d430", "discusses"),
    _edge("synthesis_frede2011_ch9_augustine",
          "argument_frede_2011_augustine_no_new_notion_vs_dihle", "discusses"),
    _edge("synthesis_frede2011_ch9_augustine",
          "argument_frede_2011_augustine_stoic_paul_via_marius_victorinus", "discusses"),
    _edge("synthesis_frede2011_ch9_augustine",
          "work_augustine_de_libero_arbitrio", "discusses"),
    _edge("synthesis_frede2011_ch9_augustine",
          "work_augustine_confessiones_viii", "discusses"),
    _edge("synthesis_frede2011_ch9_augustine",
          "scholar_dihle_albrecht", "critiques"),
    # Ch.10
    _edge("synthesis_frede2011_ch10_conclusion",
          "argument_frede_2011_ancient_notion_not_basically_flawed", "discusses"),
    _edge("synthesis_frede2011_ch10_conclusion",
          "argument_frede_2011_epictetus_first_free_will", "discusses"),
    # Methodology synthesis
    _edge("synthesis_frede2011_methodology_history_not_apologetic",
          "scholar_dihle_albrecht", "critiques"),
    _edge("synthesis_frede2011_methodology_history_not_apologetic",
          "argument_frede_2011_notion_is_technical_and_datable", "discusses"),
])


# =============================================================================
# 10. INFLUENCE CHAINS Frede asserts (ancient -> ancient)
# =============================================================================
NEW_EDGES.extend([
    # Chrysippus -> Epictetus (Stoic continuity, p. 81-82)
    _edge("person_chrysippus_280_206bce_i9j0k1l2",
          "person_epictetus_of_hierapolis_3c385bc2", "influences",
          confidence=0.95,
          frede_note="Frede 2011 Ch. 5 §3 (p. 81-83) - Epictetus inherits Chrysippean assent + modal logic"),
    # Musonius -> Epictetus (master-student, p. 74)
    _edge("person_musonius_rufus_30_101ce",
          "person_epictetus_of_hierapolis_3c385bc2", "influences",
          confidence=0.95,
          frede_note="Frede 2011 Ch. 5 (p. 74) - autexousion in Musonius then frequently in Epictetus"),
    # Epictetus -> Origen (Frede claims terminology and major claims are 'almost invariably found in Epictetus', p. 113)
    _edge("person_epictetus_of_hierapolis_3c385bc2",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.9,
          frede_note="Frede 2011 Ch. 7 (p. 113) - Origen's terminology and major claims 'almost invariably found in Epictetus'"),
    # Carneades -> Alexander (unforced assent criterion, p. 95)
    _edge("person_carneades_214_129bce_l2m3n4o5",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "influences",
          confidence=0.95,
          frede_note="Frede 2011 Ch. 6 (p. 95) - Alexander inherits Carneades's abiastos synkatathesis criterion"),
    # Cicero transmits Carneades to Alexander
    _edge("person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "influences",
          confidence=0.85,
          frede_note="Frede 2011 Ch. 6 - Cicero De fato is principal transmission channel of Carneades's argument"),
    # Origen -> Plotinus and inverse (Frede notes Ammonius Saccas teacher of both, p. 105; Porphyry knew Origen)
    _edge("person_origen_alexandria_185_254ce_s9t0u1v2",
          "person_plotinus_d270", "influences",
          confidence=0.7,
          frede_note="Frede 2011 Ch. 7 (p. 105) + Ch. 8 - Ammonius Saccas common teacher; Porphyry's claim about Origen"),
    # Origen -> Augustine (Frede's stronger claim: Augustine inherits Origenian Stoicism, then radicalizes)
    _edge("person_origen_alexandria_185_254ce_s9t0u1v2",
          "person_augustine_hippo_d430", "influences",
          confidence=0.85,
          frede_note="Frede 2011 Ch. 9 - Augustine inherits the Stoic-Origenian Christian framework, departing only where he adheres MORE strictly to Stoicism"),
    # Justin Martyr -> Tatian (master-disciple per Frede p. 104)
    _edge("person_justin_martyr_2c_ce",
          "person_tatian", "influences",
          confidence=0.95,
          frede_note="Frede 2011 Ch. 7 (p. 104) - 'Tatian was a follower of Justin Martyr'"),
    # Clement -> Origen (Pantaenus tradition, p. 104)
    _edge("person_clement_alexandria",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.9,
          frede_note="Frede 2011 Ch. 7 (p. 104) - Origen 'famous student' of Clement; Pantaenus's Stoic legacy at Alexandria"),
    # Plotinus -> Augustine (Plotinus Enn. IV.8.4 + influence on Augustinian dualism)
    _edge("person_plotinus_d270",
          "person_augustine_hippo_d430", "influences",
          confidence=0.8,
          frede_note="Frede 2011 Ch. 9 (p. 163) - Plotinus's preexisting-soul possibility echoes in Augustine"),
    # Plato -> Plotinus (Republic 6.509b on the Good beyond being - structural to Plotinus's God)
    _edge("person_plato_428_348bce_a1b2c3d4",
          "person_plotinus_d270", "influences",
          confidence=0.95,
          frede_note="Frede 2011 Ch. 7 (p. 109) + Ch. 8 - Republic VI.509b 'Good beyond being' structures Plotinus's transcendent One"),
])


# =============================================================================
# 11. INFLUENCED_BY (alternative direction for some links)
# =============================================================================
# Already covered by influences above. Skip dual-direction redundancy.


# =============================================================================
# 12. PRECEDES — book's historical chronology (person -> person)
# =============================================================================
NEW_EDGES.extend([
    _edge("person_aristotle_384_322bce_c2d4f6a8", "person_chrysippus_280_206bce_i9j0k1l2", "precedes"),
    _edge("person_chrysippus_280_206bce_i9j0k1l2", "person_carneades_214_129bce_l2m3n4o5", "precedes"),
    _edge("person_carneades_214_129bce_l2m3n4o5", "person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "precedes"),
    _edge("person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "person_musonius_rufus_30_101ce", "precedes"),
    _edge("person_musonius_rufus_30_101ce", "person_epictetus_of_hierapolis_3c385bc2", "precedes"),
    _edge("person_epictetus_of_hierapolis_3c385bc2", "person_justin_martyr_2c_ce", "precedes"),
    _edge("person_justin_martyr_2c_ce", "person_tatian", "precedes"),
    _edge("person_tatian", "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "precedes"),
    _edge("person_alexander_aphrodisias_fl200ce_n5o6p7q8", "person_origen_alexandria_185_254ce_s9t0u1v2", "precedes"),
    _edge("person_origen_alexandria_185_254ce_s9t0u1v2", "person_plotinus_d270", "precedes"),
    _edge("person_plotinus_d270", "person_porphyry", "precedes"),
    _edge("person_porphyry", "person_augustine_hippo_d430", "precedes"),
])


# =============================================================================
# 13. CONCEPTS: relations Frede establishes between concepts
# =============================================================================
NEW_EDGES.extend([
    # Stoic synkatathesis is the conceptual ancestor enriched by the inner-life supplement.
    # `precedes` is not allowed concept->concept per ontology (precedes targets are person/work/event/argument).
    # Use `discusses` which IS allowed concept->concept, with a metadata note specifying the precedence semantics.
    _edge("concept_synkatathesis_stoic_assent",
          "concept_frede_inner_life_late_stoic", "discusses",
          confidence=0.9,
          frede_note="Conceptual ancestry: Frede 2011 Ch. 3-5 - classical synkatathesis enriched by inner-life supplement in late Stoicism. Encoded as `discusses` because `precedes` does not accept concept->concept per ontology"),
    # Frede schema applies as analytical frame to inner-life concept
    _edge("concept_frede_general_schema_of_free_will",
          "concept_frede_inner_life_late_stoic", "discusses",
          confidence=0.85,
          frede_note="The inner-life concept is what makes Epictetus pass the schema's test"),
])


# =============================================================================
# 14. ARGUMENTS critiques Dihle's competing argument
# =============================================================================
NEW_EDGES.extend([
    # Frede's central argument vs Dihle's central argument (both as scholar_position_*)
    _edge("argument_frede_2011_augustine_no_new_notion_vs_dihle",
          "scholar_position_dihle_will_christian_innovation", "critiques",
          confidence=0.98,
          frede_note="Direct argument-to-argument refutation in Ch. 9"),
    _edge("argument_frede_2011_epictetus_first_free_will",
          "scholar_position_dihle_will_christian_innovation", "critiques",
          confidence=0.95,
          frede_note="Establishing Epictetan origin pre-empts Dihle's Augustinian-origin thesis"),
    # Frede vs Bobzien on dating
    _edge("argument_frede_2011_epictetus_first_free_will",
          "scholar_position_bobzien_no_free_will_problem_ancients", "responds_to",
          confidence=0.85,
          frede_note="Frede specifies and dates the emergence Bobzien left somewhat 'inadvertent'"),
    # Frede vs Kahn on locus (Kahn says Seneca-Epictetus; Frede precisely Epictetus)
    _edge("argument_frede_2011_epictetus_first_free_will",
          "scholar_position_kahn_will_emerges_seneca_epictetus", "responds_to",
          confidence=0.85,
          frede_note="Frede specifies Epictetus alone, not Seneca"),
    # Frede confirms / refines existing Frede position node (frede_will_originates_epictetus is already in the KG)
    _edge("argument_frede_2011_epictetus_first_free_will",
          "scholar_position_frede_will_originates_epictetus", "supports",
          confidence=0.99,
          frede_note="This argument node is the full textual basis for the scholar_position_frede_* placeholder"),
])
