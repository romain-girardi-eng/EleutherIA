"""Destrée/Salles/Zingano 2014 B1 — NEW_EDGES list.

Allowed relations per knowledge graph/ontology/edge_types.json :

  authored_by         : argument/passage/publication/quote/synthesis/work -> person
  wrote               : person -> work
  contains            : argument/concept/debate/quote/work/source_collection -> argument/...
  cites_primary_source: argument/publication/person -> passage/work
  discusses           : argument/argument_framework/concept/.../synthesis/work -> argument/concept/debate/group/person/school/synthesis/work
  evidenced_by        : argument/concept/group/school -> passage
  influences          : person/school/work -> person/school/work
  influenced_by       : person/school/work/event -> person/school/work
  precedes            : argument/person/event/publication/work -> argument/person/event/work
  critiques           : many -> argument/concept/controversy/person/publication/school/synthesis/work
  responds_to         : many -> argument/work/concept/debate/person
  employs             : argument/concept/passage/person/work -> argument/argument_framework/concept
  interprets          : argument/person/publication/modern_interpretation/work -> argument/argument_framework/concept/passage/person/school/work
  belongs_to_school   : person -> school
  member_of           : concept/person/work -> group/school
  part_of             : argument/concept/passage/synthesis/text_fragment/work -> concept/passage/work/source_collection
  supports            : argument/concept/event/group/passage/person/synthesis/work -> argument/concept/person
  extends             : (custom edge type, used in earlier batches)
"""
from __future__ import annotations

from typing import Any

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
# 1. PUBLICATION authorship — three editors authored the volume
# =============================================================================
PUB_ID = "pub_destree_salles_zingano_2014_what_is_up_to_us"

NEW_EDGES.extend([
    _edge(PUB_ID, "scholar_destr_e_p_salles_zingano_eds", "authored_by", confidence=0.99),
    # Individual editor authorship via separate edges
    _edge("scholar_destr_e_p", PUB_ID, "wrote", confidence=0.95,
          destree2014_role="co-editor + chapter 2 author"),
    _edge("scholar_salles_ricardo", PUB_ID, "wrote", confidence=0.95,
          destree2014_role="co-editor + chapter 11 author"),
    _edge("scholar_zingano_marco", PUB_ID, "wrote", confidence=0.95,
          destree2014_role="co-editor + chapter 13 author"),
])


# =============================================================================
# 2. SYNTHESES — chapter syntheses part_of publication + authored_by chapter author
# =============================================================================
# (chapter_synth_id, chapter_author_scholar_id)
CHAPTER_AUTHORS: list[tuple[str, str]] = [
    ("synthesis_destree2014_introduction_overview", "scholar_destr_e_p_salles_zingano_eds"),
    ("synthesis_destree2014_ch01_johnson_democritus", "scholar_johnson_monte"),
    ("synthesis_destree2014_ch02_destree_plato_er", "scholar_destr_e_p"),
    ("synthesis_destree2014_ch03_frede_d_aristotle_free_will", "scholar_frede_dorothea"),
    ("synthesis_destree2014_ch04_bobzien_aristotle_free_choice", "scholar_position_bobzien_no_free_will_problem_ancients"),
    ("synthesis_destree2014_ch05_sauve_meyer_aristotle_eph_hemin_contingent", "scholar_meyer_s"),
    ("synthesis_destree2014_ch06_echenique_aristotle_double_position", "scholar_eche_ique_j"),
    ("synthesis_destree2014_ch07_vogt_stoic_action", "scholar_vogt_katja"),
    ("synthesis_destree2014_ch08_gomez_chrysippus_compatibilism", "scholar_gomez_laura"),
    ("synthesis_destree2014_ch09_gourinat_in_nostra_potestate", "scholar_gourinat_jean_baptiste"),
    ("synthesis_destree2014_ch10_vimercati_panaetius", "scholar_vimercati_emmanuele"),
    ("synthesis_destree2014_ch11_salles_epictetus_causal", "scholar_salles_ricardo"),
    ("synthesis_destree2014_ch12_boeri_marcus_aurelius", "scholar_boeri_marcelo"),
    ("synthesis_destree2014_ch13_zingano_alexander_character_action", "scholar_zingano_marco"),
    ("synthesis_destree2014_ch14_morel_epicurus_primary_evidence", "scholar_morel_pierre_marie"),
    ("synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius", "scholar_maso_s"),
    ("synthesis_destree2014_ch16_gerson_plotinus_strawson", "scholar_gerson_l"),
    ("synthesis_destree2014_ch17_taormina_porphyry_myth_er", "scholar_taormina_daniela"),
    ("synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate", "scholar_bonazzi_mauro"),
    ("synthesis_destree2014_ch19_horn_augustine_liberum_arbitrium", "scholar_horn_christoph"),
    ("synthesis_destree2014_ch20_steel_proclus_human_or_divine_freedom", "scholar_steel_carlos"),
    ("synthesis_destree2014_ch21_wildberg_epictetus_simplicius", "scholar_wildberg_christian"),
    ("synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview", "scholar_frede_michael"),
]

# Note: Bobzien ch. 4 — pas de scholar_bobzien_susanne dans le KG. On utilise
# scholar_position_bobzien_no_free_will_problem_ancients comme proxy
# (existant). Si Romain crée scholar_bobzien_susanne plus tard, le proxy
# pourra être rattaché manuellement.

for synth_id, author_id in CHAPTER_AUTHORS:
    NEW_EDGES.append(_edge(synth_id, author_id, "authored_by"))


# =============================================================================
# 3. ARGUMENTS authored_by their chapter author
# =============================================================================
ARGUMENT_AUTHORS: list[tuple[str, str]] = [
    ("argument_johnson_2014_democritus_plasticity_intellectualism", "scholar_johnson_monte"),
    ("argument_destree_2014_plato_er_asymmetry", "scholar_destr_e_p"),
    ("argument_frede_d_2014_aristotle_psychological_determinism", "scholar_frede_dorothea"),
    ("argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist", "scholar_position_bobzien_no_free_will_problem_ancients"),
    ("argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap", "scholar_meyer_s"),
    ("argument_echenique_2014_aristotle_double_position_appraisals_accountability", "scholar_eche_ique_j"),
    ("argument_vogt_2014_stoic_cyclic_assent_eph_hemin", "scholar_vogt_katja"),
    ("argument_gomez_2014_chrysippus_reactive_compatibilism", "scholar_gomez_laura"),
    ("argument_gourinat_2014_in_nostra_potestate_not_eph_hemin", "scholar_gourinat_jean_baptiste"),
    ("argument_vimercati_2014_panaetius_eph_hemin_unique_occurrence", "scholar_vimercati_emmanuele"),
    ("argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus", "scholar_salles_ricardo"),
    ("argument_boeri_2014_marcus_present_indifferents_eph_hemin", "scholar_boeri_marcelo"),
    ("argument_zingano_2014_alexander_liability_vs_possibility", "scholar_zingano_marco"),
    ("argument_morel_2014_epicurean_eph_hemin_primary_evidence", "scholar_morel_pierre_marie"),
    ("argument_maso_2014_cicero_motus_animi_voluntarius_independence", "scholar_maso_s"),
    ("argument_gerson_2014_plotinus_qualified_moral_responsibility_against_strawson", "scholar_gerson_l"),
    ("argument_taormina_2014_porphyry_eph_hemin_rational_soul_only", "scholar_taormina_daniela"),
    ("argument_bonazzi_2014_middle_platonist_hypothetical_fate_partial_solution", "scholar_bonazzi_mauro"),
    ("argument_horn_2014_augustine_liberum_arbitrium_equivalent_plus_eph_hemin", "scholar_horn_christoph"),
    ("argument_steel_2014_proclus_causal_hierarchy_providence_fate_eph_hemin", "scholar_steel_carlos"),
    ("argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will", "scholar_wildberg_christian"),
    ("argument_frede_michael_2014_eph_hemin_emerges_with_alexander_epictetus_christianity", "scholar_frede_michael"),
]

for arg_id, author_id in ARGUMENT_AUTHORS:
    NEW_EDGES.append(_edge(arg_id, author_id, "authored_by"))


# =============================================================================
# 4. SYNTHESES discuss their main ancient targets
# =============================================================================
NEW_EDGES.extend([
    # Introduction discusses the central concept
    _edge("synthesis_destree2014_introduction_overview",
          "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", "discusses"),
    # Johnson - Democritus
    _edge("synthesis_destree2014_ch01_johnson_democritus",
          "person_democritus_460_370bce_g7h8i9j0", "discusses"),
    # Destrée - Plato + myth of Er
    _edge("synthesis_destree2014_ch02_destree_plato_er",
          "person_plato_428_348bce_a1b2c3d4", "discusses"),
    # D. Frede - Aristotle
    _edge("synthesis_destree2014_ch03_frede_d_aristotle_free_will",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("synthesis_destree2014_ch03_frede_d_aristotle_free_will",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "discusses"),
    # Bobzien - Aristotle EN III 1113b7-8
    _edge("synthesis_destree2014_ch04_bobzien_aristotle_free_choice",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("synthesis_destree2014_ch04_bobzien_aristotle_free_choice",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "discusses"),
    # Sauvé Meyer - Aristotle EE
    _edge("synthesis_destree2014_ch05_sauve_meyer_aristotle_eph_hemin_contingent",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("synthesis_destree2014_ch05_sauve_meyer_aristotle_eph_hemin_contingent",
          "work_aristotle_eudemian_ethics", "discusses"),
    _edge("synthesis_destree2014_ch05_sauve_meyer_aristotle_eph_hemin_contingent",
          "concept_two_sidedness_eph_hemin", "discusses"),
    # Echeñique - Aristotle
    _edge("synthesis_destree2014_ch06_echenique_aristotle_double_position",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("synthesis_destree2014_ch06_echenique_aristotle_double_position",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "discusses"),
    # Vogt - Stoic agency (general)
    _edge("synthesis_destree2014_ch07_vogt_stoic_action",
          "concept_synkatathesis_stoic_assent", "discusses"),
    # Gómez - Chrysippus
    _edge("synthesis_destree2014_ch08_gomez_chrysippus_compatibilism",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_destree2014_ch08_gomez_chrysippus_compatibilism",
          "argument_cylinder_analogy_chrysippus_k1l2m3n4", "discusses"),
    # Gourinat - Chrysippus + Cicero De Fato
    _edge("synthesis_destree2014_ch09_gourinat_in_nostra_potestate",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_destree2014_ch09_gourinat_in_nostra_potestate",
          "work_de_fato_cicero_44bce_b9c4e5d2", "discusses"),
    _edge("synthesis_destree2014_ch09_gourinat_in_nostra_potestate",
          "concept_eph_hemin_one_sided_causative", "discusses"),
    # Vimercati - Panaetius (via Nemesius)
    _edge("synthesis_destree2014_ch10_vimercati_panaetius",
          "work_nemesius_de_nat_hom", "discusses"),
    # Salles - Epictetus
    _edge("synthesis_destree2014_ch11_salles_epictetus_causal",
          "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("synthesis_destree2014_ch11_salles_epictetus_causal",
          "work_epictetus_discourses", "discusses"),
    _edge("synthesis_destree2014_ch11_salles_epictetus_causal",
          "argument_cylinder_analogy_chrysippus_k1l2m3n4", "discusses"),
    _edge("synthesis_destree2014_ch11_salles_epictetus_causal",
          "concept_causal_conception_eph_hemin_salles", "discusses"),
    # Boeri - Marcus Aurelius
    _edge("synthesis_destree2014_ch12_boeri_marcus_aurelius",
          "person_marcus_aurelius_121_180ce", "discusses"),
    _edge("synthesis_destree2014_ch12_boeri_marcus_aurelius",
          "work_marcus_aurelius_meditations", "discusses"),
    # Zingano - Alexander
    _edge("synthesis_destree2014_ch13_zingano_alexander_character_action",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge("synthesis_destree2014_ch13_zingano_alexander_character_action",
          "work_de_fato_alexander_c200ce_o6p7q8r9", "discusses"),
    # Morel - Epicurus
    _edge("synthesis_destree2014_ch14_morel_epicurus_primary_evidence",
          "person_epicurus_341_270bce_j0k1l2m3", "discusses"),
    _edge("synthesis_destree2014_ch14_morel_epicurus_primary_evidence",
          "work_epicurus_letter_menoeceus", "discusses"),
    _edge("synthesis_destree2014_ch14_morel_epicurus_primary_evidence",
          "work_epicurus_on_nature_xxv", "discusses"),
    # Maso - Cicero
    _edge("synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius",
          "person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "discusses"),
    _edge("synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius",
          "work_de_fato_cicero_44bce_b9c4e5d2", "discusses"),
    _edge("synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius",
          "argument_epicurean_swerve_for_freedom_m4n5o6p7", "discusses"),
    # Gerson - Plotinus
    _edge("synthesis_destree2014_ch16_gerson_plotinus_strawson",
          "person_plotinus_d270", "discusses"),
    # Taormina - Porphyry
    _edge("synthesis_destree2014_ch17_taormina_porphyry_myth_er",
          "person_porphyry", "discusses"),
    _edge("synthesis_destree2014_ch17_taormina_porphyry_myth_er",
          "work_porphyry_peri_tou_eph_hemin", "discusses"),
    _edge("synthesis_destree2014_ch17_taormina_porphyry_myth_er",
          "person_plato_428_348bce_a1b2c3d4", "discusses"),
    # Bonazzi - Middle Platonists
    _edge("synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate",
          "concept_hypothetical_fate_middle_platonist", "discusses"),
    # Horn - Augustine
    _edge("synthesis_destree2014_ch19_horn_augustine_liberum_arbitrium",
          "person_augustine_hippo_d430", "discusses"),
    _edge("synthesis_destree2014_ch19_horn_augustine_liberum_arbitrium",
          "work_de_libero_arbitrio", "discusses"),
    _edge("synthesis_destree2014_ch19_horn_augustine_liberum_arbitrium",
          "concept_liberum_arbitrium_u3v4w5x6", "discusses"),
    # Steel - Proclus
    _edge("synthesis_destree2014_ch20_steel_proclus_human_or_divine_freedom",
          "person_proclus_412_485ce_f3d8b2a9", "discusses"),
    _edge("synthesis_destree2014_ch20_steel_proclus_human_or_divine_freedom",
          "work_proclus_de_providentia_fato_in_nobis", "discusses"),
    # Wildberg - Epictetus + Simplicius
    _edge("synthesis_destree2014_ch21_wildberg_epictetus_simplicius",
          "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("synthesis_destree2014_ch21_wildberg_epictetus_simplicius",
          "person_simplicius_cilicia_490_560ce", "discusses"),
    _edge("synthesis_destree2014_ch21_wildberg_epictetus_simplicius",
          "work_simplicius_in_enchiridion", "discusses"),
    # Frede M. - global thesis
    _edge("synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview",
          "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", "discusses"),
    _edge("synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview",
          "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge("synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview",
          "person_justin_martyr_2c_ce", "discusses"),
    _edge("synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview",
          "person_tatian", "discusses"),
])


# =============================================================================
# 5. SYNTHESES part_of publication (volume coherence)
# =============================================================================
ALL_SYNTH_IDS = [
    "synthesis_destree2014_introduction_overview",
    "synthesis_destree2014_ch01_johnson_democritus",
    "synthesis_destree2014_ch02_destree_plato_er",
    "synthesis_destree2014_ch03_frede_d_aristotle_free_will",
    "synthesis_destree2014_ch04_bobzien_aristotle_free_choice",
    "synthesis_destree2014_ch05_sauve_meyer_aristotle_eph_hemin_contingent",
    "synthesis_destree2014_ch06_echenique_aristotle_double_position",
    "synthesis_destree2014_ch07_vogt_stoic_action",
    "synthesis_destree2014_ch08_gomez_chrysippus_compatibilism",
    "synthesis_destree2014_ch09_gourinat_in_nostra_potestate",
    "synthesis_destree2014_ch10_vimercati_panaetius",
    "synthesis_destree2014_ch11_salles_epictetus_causal",
    "synthesis_destree2014_ch12_boeri_marcus_aurelius",
    "synthesis_destree2014_ch13_zingano_alexander_character_action",
    "synthesis_destree2014_ch14_morel_epicurus_primary_evidence",
    "synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius",
    "synthesis_destree2014_ch16_gerson_plotinus_strawson",
    "synthesis_destree2014_ch17_taormina_porphyry_myth_er",
    "synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate",
    "synthesis_destree2014_ch19_horn_augustine_liberum_arbitrium",
    "synthesis_destree2014_ch20_steel_proclus_human_or_divine_freedom",
    "synthesis_destree2014_ch21_wildberg_epictetus_simplicius",
    "synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview",
]
# NB: part_of allowed target_types are concept/passage/work/source_collection
# only. publication is NOT a valid part_of target per the ontology. We keep
# the publication anchor via metadata.publication (set in destree_metadata).
# Synthesis -> publication via discusses works (publication is a valid
# discusses target).
for sid in ALL_SYNTH_IDS:
    NEW_EDGES.append(_edge(sid, PUB_ID, "discusses",
                           destree2014_role="this synthesis is a chapter summary of the publication"))


# =============================================================================
# 6. ARGUMENTS discuss / interpret their ancient targets
# =============================================================================
NEW_EDGES.extend([
    # Johnson 2014 - Democritus
    _edge("argument_johnson_2014_democritus_plasticity_intellectualism",
          "person_democritus_460_370bce_g7h8i9j0", "interprets"),
    # Destrée 2014 - Plato
    _edge("argument_destree_2014_plato_er_asymmetry",
          "person_plato_428_348bce_a1b2c3d4", "interprets"),
    # D. Frede 2014 - Aristotle
    _edge("argument_frede_d_2014_aristotle_psychological_determinism",
          "person_aristotle_384_322bce_c2d4f6a8", "interprets"),
    # Bobzien 2014 - Aristotle EN
    _edge("argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "interprets"),
    # Sauvé Meyer 2014 - Aristotle EE
    _edge("argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap",
          "work_aristotle_eudemian_ethics", "interprets"),
    _edge("argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap",
          "concept_two_sidedness_eph_hemin", "discusses"),
    _edge("argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap",
          "argument_frankfurt_cases_1o2p3q4r", "critiques"),
    # Echeñique 2014 - Aristotle EN III 5
    _edge("argument_echenique_2014_aristotle_double_position_appraisals_accountability",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "interprets"),
    # Vogt 2014 - Stoic assent
    _edge("argument_vogt_2014_stoic_cyclic_assent_eph_hemin",
          "concept_synkatathesis_stoic_assent", "discusses"),
    # Gómez 2014 - Chrysippus
    _edge("argument_gomez_2014_chrysippus_reactive_compatibilism",
          "person_chrysippus_280_206bce_i9j0k1l2", "interprets"),
    _edge("argument_gomez_2014_chrysippus_reactive_compatibilism",
          "argument_cylinder_analogy_chrysippus_k1l2m3n4", "discusses"),
    # Gourinat 2014 - Chrysippus + Cicero
    _edge("argument_gourinat_2014_in_nostra_potestate_not_eph_hemin",
          "person_chrysippus_280_206bce_i9j0k1l2", "interprets"),
    _edge("argument_gourinat_2014_in_nostra_potestate_not_eph_hemin",
          "work_de_fato_cicero_44bce_b9c4e5d2", "interprets"),
    # Vimercati 2014 - Panaetius
    _edge("argument_vimercati_2014_panaetius_eph_hemin_unique_occurrence",
          "work_nemesius_de_nat_hom", "interprets"),
    # Salles 2014 - Epictetus
    _edge("argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus",
          "person_epictetus_of_hierapolis_3c385bc2", "interprets"),
    _edge("argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus",
          "work_epictetus_discourses", "interprets"),
    _edge("argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus",
          "concept_causal_conception_eph_hemin_salles", "supports"),
    # Boeri 2014 - Marcus
    _edge("argument_boeri_2014_marcus_present_indifferents_eph_hemin",
          "person_marcus_aurelius_121_180ce", "interprets"),
    _edge("argument_boeri_2014_marcus_present_indifferents_eph_hemin",
          "work_marcus_aurelius_meditations", "interprets"),
    # Zingano 2014 - Alexander
    _edge("argument_zingano_2014_alexander_liability_vs_possibility",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "interprets"),
    _edge("argument_zingano_2014_alexander_liability_vs_possibility",
          "work_de_fato_alexander_c200ce_o6p7q8r9", "interprets"),
    # Morel 2014 - Epicurus
    _edge("argument_morel_2014_epicurean_eph_hemin_primary_evidence",
          "person_epicurus_341_270bce_j0k1l2m3", "interprets"),
    _edge("argument_morel_2014_epicurean_eph_hemin_primary_evidence",
          "work_epicurus_letter_menoeceus", "interprets"),
    _edge("argument_morel_2014_epicurean_eph_hemin_primary_evidence",
          "work_epicurus_on_nature_xxv", "interprets"),
    # Maso 2014 - Cicero
    _edge("argument_maso_2014_cicero_motus_animi_voluntarius_independence",
          "person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "interprets"),
    _edge("argument_maso_2014_cicero_motus_animi_voluntarius_independence",
          "work_de_fato_cicero_44bce_b9c4e5d2", "interprets"),
    # Gerson 2014 - Plotinus
    _edge("argument_gerson_2014_plotinus_qualified_moral_responsibility_against_strawson",
          "person_plotinus_d270", "interprets"),
    # Taormina 2014 - Porphyry
    _edge("argument_taormina_2014_porphyry_eph_hemin_rational_soul_only",
          "person_porphyry", "interprets"),
    _edge("argument_taormina_2014_porphyry_eph_hemin_rational_soul_only",
          "work_porphyry_peri_tou_eph_hemin", "interprets"),
    # Bonazzi 2014 - Middle Platonists
    _edge("argument_bonazzi_2014_middle_platonist_hypothetical_fate_partial_solution",
          "concept_hypothetical_fate_middle_platonist", "interprets"),
    # Horn 2014 - Augustine
    _edge("argument_horn_2014_augustine_liberum_arbitrium_equivalent_plus_eph_hemin",
          "person_augustine_hippo_d430", "interprets"),
    _edge("argument_horn_2014_augustine_liberum_arbitrium_equivalent_plus_eph_hemin",
          "work_de_libero_arbitrio", "interprets"),
    _edge("argument_horn_2014_augustine_liberum_arbitrium_equivalent_plus_eph_hemin",
          "concept_liberum_arbitrium_u3v4w5x6", "discusses"),
    # Steel 2014 - Proclus
    _edge("argument_steel_2014_proclus_causal_hierarchy_providence_fate_eph_hemin",
          "person_proclus_412_485ce_f3d8b2a9", "interprets"),
    _edge("argument_steel_2014_proclus_causal_hierarchy_providence_fate_eph_hemin",
          "work_proclus_de_providentia_fato_in_nobis", "interprets"),
    # Wildberg 2014 - Epictetus via Simplicius
    _edge("argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will",
          "person_epictetus_of_hierapolis_3c385bc2", "interprets"),
    _edge("argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will",
          "work_simplicius_in_enchiridion", "interprets"),
    # Frede M. 2014 - eph' hêmin overview
    _edge("argument_frede_michael_2014_eph_hemin_emerges_with_alexander_epictetus_christianity",
          "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", "interprets"),
    _edge("argument_frede_michael_2014_eph_hemin_emerges_with_alexander_epictetus_christianity",
          "person_aristotle_384_322bce_c2d4f6a8", "interprets"),
    _edge("argument_frede_michael_2014_eph_hemin_emerges_with_alexander_epictetus_christianity",
          "person_epictetus_of_hierapolis_3c385bc2", "interprets"),
    _edge("argument_frede_michael_2014_eph_hemin_emerges_with_alexander_epictetus_christianity",
          "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "interprets"),
])


# =============================================================================
# 7. SCHOLARLY RIVALRIES / RESPONDS_TO / CRITIQUES
# =============================================================================
NEW_EDGES.extend([
    # Salles ch. 11 engages Long 2002 and Brennan 2000
    _edge("argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus",
          "scholar_long_anthony", "critiques",
          confidence=0.85,
          destree2014_source="Salles ch. 11 explicit engagement with Long 2002 + Brennan 2000"),
    _edge("argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus",
          "scholar_brennan_tad", "critiques",
          confidence=0.85,
          destree2014_source="Salles ch. 11 OSAP-style engagement"),
    # Gourinat ch. 9 partially challenges Bobzien 1998 on Chrysippean eph' hêmin
    _edge("argument_gourinat_2014_in_nostra_potestate_not_eph_hemin",
          "pub_bobzien_1998_inadvertent", "responds_to",
          confidence=0.85,
          destree2014_source="Gourinat ch. 9 explicitly nuances Bobzien 1998 on Chrysippus's adoption of eph' hêmin"),
    # Morel ch. 14 engages Bobzien 2000 OSAP
    _edge("argument_morel_2014_epicurean_eph_hemin_primary_evidence",
          "pub_bobzien_2000_epicurus_free_will", "responds_to",
          confidence=0.85,
          destree2014_source="Morel ch. 14 positively answers Bobzien 2000 modulo qualification"),
    # Gerson ch. 16 answers Galen Strawson Basic Argument (no scholar Strawson in KG)
    # We add a metadata note via critiques edge to scholar_position_brennan_*
    # if Strawson lacks a node — skip to avoid orphan
    # Horn ch. 19 nuanced critique of Dihle 1982
    _edge("argument_horn_2014_augustine_liberum_arbitrium_equivalent_plus_eph_hemin",
          "pub_dihle_1982_theory_will", "critiques",
          confidence=0.8,
          destree2014_source="Horn ch. 19 nuanced critique of Dihle's discovery-of-will thesis"),
    # Wildberg ch. 21 partially challenges Frede 2011 on Epictetus
    # No scholar_frede_michael until this batch, so target person_epictetus + reasoning via concept
    _edge("argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will",
          "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "interprets"),
    # Sauvé Meyer ch. 5 anti-PAP critique of Frankfurt cases (already in section 6)
    # Convergence Bobzien-Sauvé Meyer
    _edge("argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist",
          "argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap", "supports",
          confidence=0.9,
          destree2014_source="Bobzien ch. 4 and Sauvé Meyer ch. 5 converge on anti-indeterminist Aristotle"),
    _edge("argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap",
          "argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist", "supports",
          confidence=0.9),
    # Frede M. ch. 22 = fundament of Bobzien-Frede line
    _edge("argument_frede_michael_2014_eph_hemin_emerges_with_alexander_epictetus_christianity",
          "argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist", "supports",
          confidence=0.95,
          destree2014_source="Frede M. ch. 22 = pivot of Bobzien-Frede thesis on late emergence of free will"),
    # Echeñique ch. 6 partially disagrees with Bobzien on Aristotle
    # (Echeñique = double position; Bobzien = full compatibilism)
    _edge("argument_echenique_2014_aristotle_double_position_appraisals_accountability",
          "argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist", "responds_to",
          confidence=0.8,
          destree2014_source="Echeñique ch. 6 carves a middle position between Bobzien (full compatibilism) and incompatibilist readings"),
    # Vimercati ch. 10 + Salles ch. 11 + Gourinat ch. 9 all engage the Stoic eph' hêmin
    _edge("argument_vimercati_2014_panaetius_eph_hemin_unique_occurrence",
          "argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus", "responds_to",
          confidence=0.7,
          destree2014_source="Both chapters anchor the technical Stoic notion of eph' hêmin in specific source texts"),
])


# =============================================================================
# 8. INFLUENCE CHAINS - intellectual context
# =============================================================================
NEW_EDGES.extend([
    # M. Frede major influence on Bobzien and the volume
    _edge("scholar_frede_michael", "scholar_position_bobzien_no_free_will_problem_ancients", "influences",
          confidence=0.95,
          destree2014_source="Frede-Bobzien line on late emergence of free will is the spine of the volume"),
    _edge("scholar_frede_michael", "scholar_destr_e_p_salles_zingano_eds", "influences",
          confidence=0.9),
    # Bobzien influences most chapters
    _edge("scholar_position_bobzien_no_free_will_problem_ancients", "scholar_meyer_s", "influences",
          confidence=0.85),
    _edge("scholar_position_bobzien_no_free_will_problem_ancients", "scholar_frede_dorothea", "influences",
          confidence=0.85),
    # Salles 2005 influences Vogt + Gómez (compatibilist line)
    _edge("scholar_salles_ricardo", "scholar_vogt_katja", "influences",
          confidence=0.7,
          destree2014_source="Salles 2005 Stoics on Determinism precedes Vogt 2014"),
    # Long influences Salles, Brennan
    _edge("scholar_long_anthony", "scholar_salles_ricardo", "influences",
          confidence=0.85,
          destree2014_source="Long 2002 Epictetus Stoic and Socratic Guide is Salles's main interlocutor"),
])


# =============================================================================
# 9. WORK AUTHORSHIP for new ancient works
# =============================================================================
NEW_EDGES.extend([
    _edge("person_aristotle_384_322bce_c2d4f6a8", "work_aristotle_eudemian_ethics", "wrote"),
    _edge("work_aristotle_eudemian_ethics", "person_aristotle_384_322bce_c2d4f6a8", "authored_by"),
    _edge("person_porphyry", "work_porphyry_peri_tou_eph_hemin", "wrote"),
    _edge("work_porphyry_peri_tou_eph_hemin", "person_porphyry", "authored_by"),
    _edge("person_proclus_412_485ce_f3d8b2a9", "work_proclus_de_providentia_fato_in_nobis", "wrote"),
    _edge("work_proclus_de_providentia_fato_in_nobis", "person_proclus_412_485ce_f3d8b2a9", "authored_by"),
])


# =============================================================================
# 10. WORK part_of relations (Tria Opuscula sub-treatise)
# =============================================================================
NEW_EDGES.extend([
    _edge("work_proclus_de_providentia_fato_in_nobis",
          "work_proclus_tria_opuscula_c9a8e4b3", "part_of",
          destree2014_source="Proclus's De Providentia, Fato et eo quod in nobis is the third of the Tria Opuscula"),
    _edge("work_porphyry_peri_tou_eph_hemin",
          "work_porphyry_vita_plotini", "part_of",
          confidence=0.5,
          destree2014_source="If alternative attribution (Porphyrian opera) — kept low-confidence; see Smith 1993 frr. 268-271"),
])


# =============================================================================
# 11. PUBLICATION cites_primary_source — key ancient passages
# =============================================================================
NEW_EDGES.extend([
    # Volume as a whole cites key Aristotelian, Stoic, Epicurean, Platonic works
    _edge(PUB_ID, "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "cites_primary_source",
          destree2014_role="Ch. 3-6 anchor"),
    _edge(PUB_ID, "work_aristotle_eudemian_ethics", "cites_primary_source",
          destree2014_role="Ch. 5 (Sauvé Meyer) + ch. 6 (Echeñique)"),
    _edge(PUB_ID, "work_de_fato_alexander_c200ce_o6p7q8r9", "cites_primary_source",
          destree2014_role="Ch. 13 (Zingano)"),
    _edge(PUB_ID, "work_de_fato_cicero_44bce_b9c4e5d2", "cites_primary_source",
          destree2014_role="Ch. 9 (Gourinat) + ch. 15 (Maso) + ch. 11 (Salles re cylinder)"),
    _edge(PUB_ID, "work_epictetus_discourses", "cites_primary_source",
          destree2014_role="Ch. 11 (Salles) + ch. 22 (Frede M.)"),
    _edge(PUB_ID, "work_epictetus_enchiridion", "cites_primary_source",
          destree2014_role="Ch. 21 (Wildberg)"),
    _edge(PUB_ID, "work_simplicius_in_enchiridion", "cites_primary_source",
          destree2014_role="Ch. 21 (Wildberg)"),
    _edge(PUB_ID, "work_marcus_aurelius_meditations", "cites_primary_source",
          destree2014_role="Ch. 12 (Boeri)"),
    _edge(PUB_ID, "work_epicurus_letter_menoeceus", "cites_primary_source",
          destree2014_role="Ch. 14 (Morel)"),
    _edge(PUB_ID, "work_epicurus_on_nature_xxv", "cites_primary_source",
          destree2014_role="Ch. 14 (Morel)"),
    _edge(PUB_ID, "work_porphyry_peri_tou_eph_hemin", "cites_primary_source",
          destree2014_role="Ch. 17 (Taormina)"),
    _edge(PUB_ID, "work_proclus_de_providentia_fato_in_nobis", "cites_primary_source",
          destree2014_role="Ch. 20 (Steel)"),
    _edge(PUB_ID, "work_proclus_tria_opuscula_c9a8e4b3", "cites_primary_source",
          destree2014_role="Ch. 20 (Steel) — third opusculum"),
    _edge(PUB_ID, "work_de_libero_arbitrio", "cites_primary_source",
          destree2014_role="Ch. 19 (Horn)"),
    _edge(PUB_ID, "work_nemesius_de_nat_hom", "cites_primary_source",
          destree2014_role="Ch. 10 (Vimercati) — preserves Panaetius fr. B26 Vim. on eph' hêmin"),
])


# =============================================================================
# 12. EMPLOYS / DISCUSSES — concept connections
# =============================================================================
NEW_EDGES.extend([
    # Volume employs the central eph' hêmin concept
    _edge(PUB_ID, "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", "discusses"),
    _edge(PUB_ID, "concept_two_sidedness_eph_hemin", "discusses"),
    _edge(PUB_ID, "concept_causal_conception_eph_hemin_salles", "discusses"),
    _edge(PUB_ID, "concept_synkatathesis_stoic_assent", "discusses"),
    _edge(PUB_ID, "concept_hypothetical_fate_middle_platonist", "discusses"),
    _edge(PUB_ID, "concept_liberum_arbitrium_u3v4w5x6", "discusses"),
    _edge(PUB_ID, "concept_hekousion_voluntary_aristotle_a1b2c3d4", "discusses"),
    _edge(PUB_ID, "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "discusses"),
    # Causal conception concept supports Bobzien-Frede line
    _edge("concept_causal_conception_eph_hemin_salles",
          "concept_eph_hemin_one_sided_causative", "part_of"),
    # Two-sidedness concept relates to two-sided potestative concept
    _edge("concept_two_sidedness_eph_hemin",
          "concept_eph_hemin_two_sided_potestative", "part_of",
          destree2014_source="Sauvé Meyer ch. 5 clarifies that Aristotelian two-sidedness ≠ modern PAP"),
])


# =============================================================================
# 13. PRECEDES — chronological / intellectual chains within the volume
# =============================================================================
NEW_EDGES.extend([
    # Editorial trio members worked together
    _edge("scholar_destr_e_p", "scholar_salles_ricardo", "influences",
          confidence=0.7,
          destree2014_source="Co-editors of Destrée/Salles/Zingano 2014"),
    _edge("scholar_destr_e_p", "scholar_zingano_marco", "influences",
          confidence=0.7),
    _edge("scholar_salles_ricardo", "scholar_zingano_marco", "influences",
          confidence=0.7),
    # Volume publication precedes Bobzien's later work
    _edge(PUB_ID, "pub_bobzien_2014_choice_responsibility", "precedes",
          confidence=0.7,
          destree2014_source="Both 2014 contributions — Destrée 2014 incorporates Bobzien's chapter on EN III"),
])
