"""Fürst 2022 B1 — NEW_EDGES list.

Allowed relations per knowledge graph/ontology/edge_types.json. We use:

  authored_by         : src argument/passage/publication/quote/synthesis/work -> tgt person
  cites_primary_source: src argument/publication/person -> tgt passage/work
  discusses           : src argument/argument_framework/concept/conceptual_evolution/debate/
                        passage/person/publication/synthesis/work -> tgt argument/concept/debate/
                        group/person/school/synthesis/work
  influences          : src person/school/work -> tgt person/school/work
  influenced_by       : src person/school/work/event -> tgt person/school/work
  precedes            : src argument/person/event/publication/work -> tgt argument/person/event/work
  critiques           : src many -> tgt argument/concept/controversy/person/publication/school/synthesis/work
  responds_to         : src many -> tgt argument/work/concept/debate/person
  employs             : src argument/concept/passage/person/work -> tgt argument/argument_framework/concept
  interprets          : src argument/person/publication/modern_interpretation/work -> tgt
                        argument/argument_framework/concept/passage/person/school/work
  part_of             : src argument/concept/passage/synthesis/text_fragment/work -> tgt
                        concept/passage/work/source_collection
  supports            : src argument/concept/event/group/passage/person/synthesis/work -> tgt argument/concept/person
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
# 1. AUTHORSHIP — new Origen works -> Origen
# =============================================================================
NEW_EDGES.extend([
    _edge("work_origen_homilies_jeremiah", "person_origen_alexandria_185_254ce_s9t0u1v2", "authored_by", confidence=0.95),
    _edge("work_origen_commentary_canticles", "person_origen_alexandria_185_254ce_s9t0u1v2", "authored_by", confidence=0.95),
    _edge("work_origen_commentary_john", "person_origen_alexandria_185_254ce_s9t0u1v2", "authored_by", confidence=0.95),
    _edge("work_origen_commentary_matthew", "person_origen_alexandria_185_254ce_s9t0u1v2", "authored_by", confidence=0.95),
    _edge("work_origen_commentary_genesis", "person_origen_alexandria_185_254ce_s9t0u1v2", "authored_by", confidence=0.95),
])


# =============================================================================
# 2. SYNTHESIS authorship by Fürst (synthesis -> scholar_furst_alfons)
# =============================================================================
SYNTHESIS_IDS = [
    "synthesis_furst2022_homer_origins_selbstbestimmung",
    "synthesis_furst2022_chrysippus_compatibilism",
    "synthesis_furst2022_carneades_will_innovation",
    "synthesis_furst2022_imperial_freedom_debate",
    "synthesis_furst2022_alexander_alternativenoffenheit",
    "synthesis_furst2022_philo_alexandria_pivot",
    "synthesis_furst2022_justin_first_christian_freiheits_philosophy",
    "synthesis_furst2022_clement_phusis_prohairesis",
    "synthesis_furst2022_origen_central_freedom",
    "synthesis_furst2022_origenian_freiheitsmetaphysik",
    "synthesis_furst2022_after_origen_new_freedom_debate",
]
for sid in SYNTHESIS_IDS:
    NEW_EDGES.append(_edge(sid, "scholar_furst_alfons", "authored_by"))


# =============================================================================
# 3. ARGUMENT authorship by Fürst — scholarly arguments -> scholar_furst_alfons
# =============================================================================
ARGUMENT_IDS = [
    "argument_furst_2022_continuity_homer_to_origen",
    "argument_furst_2022_origen_first_freedom_thinker",
    "argument_furst_2022_origen_culmination_autexousion",
    "argument_furst_2022_middle_platonist_origin_autexousion",
    "argument_furst_2022_de_princ_iii_1_first_freedom_treatise",
    "argument_furst_2022_freedom_fourth_article_of_faith",
    "argument_furst_2022_freedom_principle_of_substance",
    "argument_furst_2022_kompatibilistischer_libertarismus",
    "argument_furst_2022_critique_dihle_augustine_thesis",
    "argument_furst_2022_christian_philosophers_freedom_innovation",
    "argument_furst_2022_aristotle_no_will_intellectualism",
    "argument_furst_2022_stoic_eph_hemin_late_substantive",
    "argument_furst_2022_justin_first_explicit_freedom_decision",
    "argument_furst_2022_world_as_network_of_freedoms",
    "argument_furst_2022_origen_against_three_determinisms",
]
for aid in ARGUMENT_IDS:
    NEW_EDGES.append(_edge(aid, "scholar_furst_alfons", "authored_by"))


# =============================================================================
# 4. SYNTHESES discuss persons/works/arguments/concepts
# =============================================================================
NEW_EDGES.extend([
    # Homer synthesis (no Homer node in KG ; discusses general concept)
    _edge("synthesis_furst2022_homer_origins_selbstbestimmung", "concept_selbstbestimmung_modern_furst", "discusses"),

    # Chrysippus synthesis
    _edge("synthesis_furst2022_chrysippus_compatibilism", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_furst2022_chrysippus_compatibilism", "debate_stoic_compatibilism", "discusses"),
    _edge("synthesis_furst2022_chrysippus_compatibilism", "person_bobzien_susanne_contemporary", "discusses"),

    # Carneades synthesis
    _edge("synthesis_furst2022_carneades_will_innovation", "person_carneades_214_129bce_l2m3n4o5", "discusses"),
    _edge("synthesis_furst2022_carneades_will_innovation", "person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "discusses"),
    _edge("synthesis_furst2022_carneades_will_innovation", "work_de_fato_cicero_44bce_b9c4e5d2", "discusses"),

    # Imperial freedom debate synthesis
    _edge("synthesis_furst2022_imperial_freedom_debate", "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("synthesis_furst2022_imperial_freedom_debate", "person_alcinous_2c_ce", "discusses"),
    _edge("synthesis_furst2022_imperial_freedom_debate", "person_plutarch_45_120ce_b9c2a8f3", "discusses"),
    _edge("synthesis_furst2022_imperial_freedom_debate", "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge("synthesis_furst2022_imperial_freedom_debate", "person_oinomaos_gadara_2c_ce", "discusses"),
    _edge("synthesis_furst2022_imperial_freedom_debate", "person_diogenianos_8m3n5p21", "discusses"),
    _edge("synthesis_furst2022_imperial_freedom_debate", "person_galen_pergamon_129_216ce", "discusses"),
    _edge("synthesis_furst2022_imperial_freedom_debate", "person_sextus_empiricus_c160_210ce_d4f8a2b1", "discusses"),

    # Alexander synthesis
    _edge("synthesis_furst2022_alexander_alternativenoffenheit", "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge("synthesis_furst2022_alexander_alternativenoffenheit", "work_de_fato_alexander_c200ce_o6p7q8r9", "discusses"),
    _edge("synthesis_furst2022_alexander_alternativenoffenheit", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),

    # Philo synthesis
    _edge("synthesis_furst2022_philo_alexandria_pivot", "person_philo_alexandria_a1b2c3d4", "discusses"),
    _edge("synthesis_furst2022_philo_alexandria_pivot", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),

    # Justin synthesis
    _edge("synthesis_furst2022_justin_first_christian_freiheits_philosophy", "person_justin_martyr_2c_ce", "discusses"),
    _edge("synthesis_furst2022_justin_first_christian_freiheits_philosophy", "work_justin_first_apology", "discusses"),
    _edge("synthesis_furst2022_justin_first_christian_freiheits_philosophy", "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "discusses"),

    # Clement synthesis
    _edge("synthesis_furst2022_clement_phusis_prohairesis", "person_clement_alexandria", "discusses"),
    _edge("synthesis_furst2022_clement_phusis_prohairesis", "work_clement_stromateis", "discusses"),
    _edge("synthesis_furst2022_clement_phusis_prohairesis", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("synthesis_furst2022_clement_phusis_prohairesis", "scholar_kobusch_theo", "discusses"),

    # Origen central freedom synthesis
    _edge("synthesis_furst2022_origen_central_freedom", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("synthesis_furst2022_origen_central_freedom", "work_de_principiis_origen_230s_v2w3x4y5", "discusses"),
    _edge("synthesis_furst2022_origen_central_freedom", "work_origen_philocalia", "discusses"),
    _edge("synthesis_furst2022_origen_central_freedom", "work_origen_commentary_john", "discusses"),
    _edge("synthesis_furst2022_origen_central_freedom", "concept_autexousion_christian", "discusses"),

    # Freiheitsmetaphysik synthesis
    _edge("synthesis_furst2022_origenian_freiheitsmetaphysik", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("synthesis_furst2022_origenian_freiheitsmetaphysik", "concept_freiheitsmetaphysik_origenian", "discusses"),
    _edge("synthesis_furst2022_origenian_freiheitsmetaphysik", "concept_kompatibilistischer_libertarismus_origenian", "discusses"),
    _edge("synthesis_furst2022_origenian_freiheitsmetaphysik", "scholar_hengstermann_christian", "discusses"),

    # After Origen synthesis
    _edge("synthesis_furst2022_after_origen_new_freedom_debate", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("synthesis_furst2022_after_origen_new_freedom_debate", "person_plotinus_d270", "discusses"),
    _edge("synthesis_furst2022_after_origen_new_freedom_debate", "person_gregory_nyssa_d395", "discusses"),
    _edge("synthesis_furst2022_after_origen_new_freedom_debate", "person_porphyry", "discusses"),
])


# =============================================================================
# 5. SYNTHESES part_of publication
# =============================================================================
for sid in SYNTHESIS_IDS:
    NEW_EDGES.append(_edge(sid, "pub_furst_2022_wege_freiheit", "part_of"))


# =============================================================================
# 6. ARGUMENTS part_of publication + discuss their targets
# =============================================================================
for aid in ARGUMENT_IDS:
    # Arguments are part_of the publication
    NEW_EDGES.append(_edge(aid, "pub_furst_2022_wege_freiheit", "part_of"))

NEW_EDGES.extend([
    # Continuity Homer to Origen — discusses Origen + Homer (no Homer node, skip)
    _edge("argument_furst_2022_continuity_homer_to_origen", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),

    # Origen first freedom thinker
    _edge("argument_furst_2022_origen_first_freedom_thinker", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("argument_furst_2022_origen_first_freedom_thinker", "person_plotinus_d270", "discusses"),
    _edge("argument_furst_2022_origen_first_freedom_thinker", "concept_freiheitsmetaphysik_origenian", "supports"),

    # Origen culmination of autexousion
    _edge("argument_furst_2022_origen_culmination_autexousion", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("argument_furst_2022_origen_culmination_autexousion", "concept_autexousion_christian", "discusses"),
    _edge("argument_furst_2022_origen_culmination_autexousion", "work_de_principiis_origen_230s_v2w3x4y5", "cites_primary_source"),
    _edge("argument_furst_2022_origen_culmination_autexousion", "work_origen_homilies_jeremiah", "cites_primary_source"),

    # Middle Platonist origin of autexousion
    _edge("argument_furst_2022_middle_platonist_origin_autexousion", "person_alcinous_2c_ce", "discusses"),
    _edge("argument_furst_2022_middle_platonist_origin_autexousion", "person_calcidius_4c_ce", "discusses"),
    _edge("argument_furst_2022_middle_platonist_origin_autexousion", "person_plutarch_45_120ce_b9c2a8f3", "discusses"),
    _edge("argument_furst_2022_middle_platonist_origin_autexousion", "work_didaskalikos_alcinous_2nd_ce_q7r8s9t0", "cites_primary_source"),
    _edge("argument_furst_2022_middle_platonist_origin_autexousion", "work_plutarch_de_fato_complete", "cites_primary_source"),
    _edge("argument_furst_2022_middle_platonist_origin_autexousion", "person_origen_alexandria_185_254ce_s9t0u1v2", "supports"),

    # De Princ III 1 first freedom treatise
    _edge("argument_furst_2022_de_princ_iii_1_first_freedom_treatise", "work_de_principiis_origen_230s_v2w3x4y5", "discusses"),
    _edge("argument_furst_2022_de_princ_iii_1_first_freedom_treatise", "work_origen_philocalia", "cites_primary_source"),
    _edge("argument_furst_2022_de_princ_iii_1_first_freedom_treatise", "work_de_fato_alexander_c200ce_o6p7q8r9", "discusses"),
    _edge("argument_furst_2022_de_princ_iii_1_first_freedom_treatise", "work_de_fato_cicero_44bce_b9c4e5d2", "discusses"),

    # Fourth article of faith
    _edge("argument_furst_2022_freedom_fourth_article_of_faith", "work_origen_commentary_john", "cites_primary_source"),
    _edge("argument_furst_2022_freedom_fourth_article_of_faith", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),

    # Freedom principle of substance
    _edge("argument_furst_2022_freedom_principle_of_substance", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("argument_furst_2022_freedom_principle_of_substance", "concept_freiheitsmetaphysik_origenian", "supports"),
    _edge("argument_furst_2022_freedom_principle_of_substance", "person_aristotle_384_322bce_c2d4f6a8", "critiques"),
    _edge("argument_furst_2022_freedom_principle_of_substance", "scholar_hengstermann_christian", "discusses"),
    _edge("argument_furst_2022_freedom_principle_of_substance", "work_origen_commentary_john", "cites_primary_source"),

    # Kompatibilistischer Libertarismus
    _edge("argument_furst_2022_kompatibilistischer_libertarismus", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("argument_furst_2022_kompatibilistischer_libertarismus", "concept_kompatibilistischer_libertarismus_origenian", "supports"),
    _edge("argument_furst_2022_kompatibilistischer_libertarismus", "scholar_list_n", "discusses"),
    _edge("argument_furst_2022_kompatibilistischer_libertarismus", "debate_compatibility_question_ea55e118", "discusses"),
    _edge("argument_furst_2022_kompatibilistischer_libertarismus", "work_origen_de_oratione", "cites_primary_source"),

    # Critique of Dihle / Augustine-centric thesis
    _edge("argument_furst_2022_critique_dihle_augustine_thesis", "scholar_dihle_albrecht", "critiques"),
    _edge("argument_furst_2022_critique_dihle_augustine_thesis", "person_augustine_hippo_d430", "discusses"),
    _edge("argument_furst_2022_critique_dihle_augustine_thesis", "person_origen_alexandria_185_254ce_s9t0u1v2", "supports"),

    # Christian philosophers freedom innovation
    _edge("argument_furst_2022_christian_philosophers_freedom_innovation", "person_justin_martyr_2c_ce", "discusses"),
    _edge("argument_furst_2022_christian_philosophers_freedom_innovation", "person_irenaeus_d202", "discusses"),
    _edge("argument_furst_2022_christian_philosophers_freedom_innovation", "person_tatian", "discusses"),
    _edge("argument_furst_2022_christian_philosophers_freedom_innovation", "person_tertullian_d220", "discusses"),
    _edge("argument_furst_2022_christian_philosophers_freedom_innovation", "person_clement_alexandria", "discusses"),

    # Aristotle no will intellectualism
    _edge("argument_furst_2022_aristotle_no_will_intellectualism", "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("argument_furst_2022_aristotle_no_will_intellectualism", "person_plato_428_348bce_a1b2c3d4", "discusses"),
    _edge("argument_furst_2022_aristotle_no_will_intellectualism", "person_frede_michael_1940_2007", "supports"),
    _edge("argument_furst_2022_aristotle_no_will_intellectualism", "scholar_dihle_albrecht", "supports"),
    _edge("argument_furst_2022_aristotle_no_will_intellectualism", "scholar_kahn_charles", "supports"),

    # Stoic eph hemin late substantive
    _edge("argument_furst_2022_stoic_eph_hemin_late_substantive", "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", "discusses"),
    _edge("argument_furst_2022_stoic_eph_hemin_late_substantive", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("argument_furst_2022_stoic_eph_hemin_late_substantive", "person_hippolytus_rome_d235", "critiques"),
    _edge("argument_furst_2022_stoic_eph_hemin_late_substantive", "person_bobzien_susanne_contemporary", "supports"),

    # Justin first explicit freedom of decision
    _edge("argument_furst_2022_justin_first_explicit_freedom_decision", "person_justin_martyr_2c_ce", "discusses"),
    _edge("argument_furst_2022_justin_first_explicit_freedom_decision", "work_justin_first_apology", "cites_primary_source"),
    _edge("argument_furst_2022_justin_first_explicit_freedom_decision", "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "discusses"),

    # World as network of freedoms
    _edge("argument_furst_2022_world_as_network_of_freedoms", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("argument_furst_2022_world_as_network_of_freedoms", "work_de_principiis_origen_230s_v2w3x4y5", "cites_primary_source"),
    _edge("argument_furst_2022_world_as_network_of_freedoms", "work_origen_de_oratione", "cites_primary_source"),
    _edge("argument_furst_2022_world_as_network_of_freedoms", "concept_freiheitsmetaphysik_origenian", "supports"),

    # Origen against three determinisms
    _edge("argument_furst_2022_origen_against_three_determinisms", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("argument_furst_2022_origen_against_three_determinisms", "work_de_principiis_origen_230s_v2w3x4y5", "cites_primary_source"),
    _edge("argument_furst_2022_origen_against_three_determinisms", "work_origen_commentary_genesis", "cites_primary_source"),
    _edge("argument_furst_2022_origen_against_three_determinisms", "work_origen_contra_celsum_sc132", "cites_primary_source"),
])


# =============================================================================
# 7. PUBLICATION cites primary sources (ancient works central to Fürst)
# =============================================================================
NEW_EDGES.extend([
    _edge("pub_furst_2022_wege_freiheit", "work_de_principiis_origen_230s_v2w3x4y5", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_de_oratione", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_commentary_john", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_commentary_genesis", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_commentary_canticles", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_commentary_matthew", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_homilies_jeremiah", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_contra_celsum_sc132", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_philocalia", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_origen_commentary_romans", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_de_fato_cicero_44bce_b9c4e5d2", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_de_fato_alexander_c200ce_o6p7q8r9", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_didaskalikos_alcinous_2nd_ce_q7r8s9t0", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_plutarch_de_fato_complete", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_republic_plato_c380bce_c3d4e5f6", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_chrysippus_svf_ii", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_epictetus_discourses", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_justin_first_apology", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_justin_second_apology_sc507", "cites_primary_source", confidence=0.95),
    _edge("pub_furst_2022_wege_freiheit", "work_clement_stromateis", "cites_primary_source", confidence=0.95),
])


# =============================================================================
# 8. INFLUENCE CHAINS — Fürst-asserted philosophical filiations
# =============================================================================
NEW_EDGES.extend([
    # Carneades → Origen (via medio-platonic transmission + Cicero)
    _edge("person_carneades_214_129bce_l2m3n4o5", "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.8,
          furst_source="Wege zur Freiheit, Kap. II 6 + Kap. V — Carneades introduces matter/spirit distinction Origen will inherit"),
    # Middle Platonists → Origen
    _edge("person_alcinous_2c_ce", "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.9,
          furst_source="Wege zur Freiheit, Kap. III 3b — Origen takes up Alcinous Didask. 26 (Laios example)"),
    _edge("person_plutarch_45_120ce_b9c2a8f3", "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.85,
          furst_source="Wege zur Freiheit, Kap. III 3b"),
    # Alexander of Aphrodisias → Origen (Alternativenoffenheit)
    _edge("person_alexander_aphrodisias_fl200ce_n5o6p7q8", "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.9,
          furst_source="Wege zur Freiheit, Kap. III 3c — Origen integrates Alexander's demand for open alternatives"),
    # Philo → Origen (heavy direct influence per Fürst)
    _edge("person_philo_alexandria_a1b2c3d4", "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.95,
          furst_source="Wege zur Freiheit, Kap. IV 1 + Kap. V — Origen 'particularly inspired by Philo' / direct takeover"),
    # Justin → Origen (foundational predecessor)
    _edge("person_justin_martyr_2c_ce", "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.85,
          furst_source="Wege zur Freiheit, Kap. IV 3 — Justin first proclaims ἐλεύθερα προαίρεσις, Origen develops it"),
    # Clement → Origen (master-disciple, doctrinal continuity)
    _edge("person_clement_alexandria", "person_origen_alexandria_185_254ce_s9t0u1v2", "influences",
          confidence=0.95,
          furst_source="Wege zur Freiheit, Kap. IV 5 — Clement posits phusis/prohairesis opposition Origen will systematize"),
    # Origen influences Plotinus (chronological priority claim per Fürst)
    _edge("person_origen_alexandria_185_254ce_s9t0u1v2", "person_plotinus_d270", "precedes",
          confidence=0.85,
          furst_source="Wege zur Freiheit, Zum Geleit p. 2 — Origen 'temporally before Plotinus the first freedom thinker'"),
    # Origen influences Gregory of Nyssa
    _edge("person_origen_alexandria_185_254ce_s9t0u1v2", "person_gregory_nyssa_d395", "influences",
          confidence=0.9,
          furst_source="Wege zur Freiheit, Zum Ausklang p. 291"),
])


# =============================================================================
# 9. FÜRST CRITIQUES + RESPONDS_TO modern scholars
# =============================================================================
NEW_EDGES.extend([
    # Fürst critiques Dihle's Augustine-centric view
    _edge("scholar_furst_alfons", "scholar_dihle_albrecht", "critiques",
          confidence=0.85,
          furst_source="Wege zur Freiheit, Zum Geleit + Anm. 1 — partial critique of Dihle's Augustine-centric perspective"),
    # Fürst responds to / engages with Frede on origin of will concept
    _edge("scholar_furst_alfons", "person_frede_michael_1940_2007", "responds_to",
          confidence=0.85,
          furst_source="Wege zur Freiheit, passim — agrees with Frede on no-will-in-Plato/Aristotle, disagrees on Epictetus locus"),
    # Fürst engages with / supports Bobzien on philological points
    _edge("scholar_furst_alfons", "person_bobzien_susanne_contemporary", "supports",
          confidence=0.85,
          furst_source="Wege zur Freiheit, Anm. 9-11 — adopts Bobzien's philological analysis of τὸ ἐφ᾽ ἡμῖν"),
    # Fürst builds on Hengstermann
    _edge("scholar_furst_alfons", "scholar_hengstermann_christian", "supports",
          confidence=0.95,
          furst_source="Wege zur Freiheit, passim — Hengstermann 2016 'comprehensive and fundamental study' pivotal"),
    # Fürst builds on Kobusch
    _edge("scholar_furst_alfons", "scholar_kobusch_theo", "supports",
          confidence=0.9,
          furst_source="Wege zur Freiheit, passim — adopts Kobusch's phusis/prohairesis opposition framework"),
    # Fürst engages with Karamanolis (critical)
    _edge("scholar_furst_alfons", "scholar_karamanolis_george", "critiques",
          confidence=0.8,
          furst_source="Wege zur Freiheit, 5102 Anm. 1 — Karamanolis 'does not see Christian specificity'"),
    # Fürst supports Andresen (Justin und der mittlere Platonismus)
    # No scholar_andresen node in KG, skip
    # Fürst supports Schallenberg (mirror term)
    # No scholar_schallenberg node in KG, skip
])


# =============================================================================
# 10. ARGUMENTS interpret canonical works
# =============================================================================
NEW_EDGES.extend([
    _edge("argument_furst_2022_de_princ_iii_1_first_freedom_treatise",
          "work_de_principiis_origen_230s_v2w3x4y5", "interprets"),
    _edge("argument_furst_2022_freedom_principle_of_substance",
          "work_de_principiis_origen_230s_v2w3x4y5", "interprets"),
    _edge("argument_furst_2022_kompatibilistischer_libertarismus",
          "work_origen_de_oratione", "interprets"),
    _edge("argument_furst_2022_kompatibilistischer_libertarismus",
          "work_de_principiis_origen_230s_v2w3x4y5", "interprets"),
    _edge("argument_furst_2022_freedom_fourth_article_of_faith",
          "work_origen_commentary_john", "interprets"),
    _edge("argument_furst_2022_world_as_network_of_freedoms",
          "work_origen_de_oratione", "interprets"),
    _edge("argument_furst_2022_origen_culmination_autexousion",
          "work_origen_homilies_jeremiah", "interprets"),
])


# =============================================================================
# 11. ORIGEN WORKS part_of DE PRINCIPIIS / PHILOCALIA structure
# =============================================================================
NEW_EDGES.extend([
    # Philocalia ch. 23 contains the Genesis commentary fragment
    _edge("work_origen_commentary_genesis", "work_origen_philocalia", "part_of",
          confidence=0.85,
          furst_source="Wege zur Freiheit, Anm. 9-10 (p. 189-190) — Philocalie 23 = In Gen. frg. D 7"),
])


# =============================================================================
# 12. CONCEPTS — autexousion concept network
# =============================================================================
NEW_EDGES.extend([
    # Autexousion christian builds on concept established by Origen
    _edge("concept_autexousion_christian", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("concept_autexousion_christian", "scholar_furst_alfons", "discusses"),

    # Freiheitsmetaphysik = origenian innovation
    _edge("concept_freiheitsmetaphysik_origenian", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),

    # Kompatibilistischer Libertarismus applied to Origen
    _edge("concept_kompatibilistischer_libertarismus_origenian", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),

    # Selbstbestimmung modern term — heuristic frame
    _edge("concept_selbstbestimmung_modern_furst", "concept_autexousion_christian", "discusses"),
])


# =============================================================================
# 13. CONCEPTS employ/support each other
# =============================================================================
NEW_EDGES.extend([
    _edge("concept_freiheitsmetaphysik_origenian", "concept_autexousion_christian", "employs"),
    _edge("concept_kompatibilistischer_libertarismus_origenian", "concept_freiheitsmetaphysik_origenian", "employs"),
])
