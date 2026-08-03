"""Dihle 1982 B1 — NEW_EDGES list.

Allowed relations per knowledge graph/ontology/edge_types.json. We rely
exclusively on attested edge types and source/target type combinations.

Sections :
  1. Authorship (Dihle wrote pub_dihle_1982 ; syntheses authored_by Dihle ;
                 scholarly arguments authored_by Dihle)
  2. Publication anchoring (synthesis -> publication via part_of)
       NOTE: synthesis -> publication.part_of is NOT in the ontology
       (part_of target_types = concept/passage/work/source_collection). We
       use the metadata.publication field instead (set via dihle_metadata),
       and use `discusses` for synthesis -> publication is also invalid.
       For publication anchoring we use `cites_primary_source` from
       scholarly_arg -> ancient_work where applicable.
  3. Scholarly discussion (synthesis -> ancient persons / works / concepts)
  4. Critiques (Dihle scholarly args critique Greek intellectualism etc.)
  5. Disagreement edges (Dihle vs Frede on Epictetus / Augustine ;
                         Dihle vs Bobzien on category of will)
  6. Influence chains (Pohlenz/Snell/Voelke/Kahn -> Dihle ; Dihle -> Frede/
                       Sorabji as influenced_by since Dihle is target)
  7. Debate participation (Dihle scholarly args contribute to
                            debate_discovery_of_will and
                            debate_intellectualism_vs_voluntarism)
  8. Engages_with edges (modern scholarly dialogue with metadata.stance)
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
# 1. AUTHORSHIP — Dihle published pub_dihle_1982 ; syntheses & args authored_by Dihle
# =============================================================================
NEW_EDGES.extend([
    # Dihle published his monograph (analogous to wrote, but for publication)
    _edge("scholar_albrecht_dihle", "pub_dihle_1982_theory_of_will", "published",
          confidence=0.99),
])


# =============================================================================
# 2. SYNTHESIS authorship by Dihle
# =============================================================================
SYNTHESIS_IDS = [
    "synthesis_dihle1982_lec1_cosmology_second_century",
    "synthesis_dihle1982_lec2_greek_intellectualism_action",
    "synthesis_dihle1982_lec3_stoic_assent_cognitive",
    "synthesis_dihle1982_lec4_paul_philo_implicit_will",
    "synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
    "synthesis_dihle1982_lec6_augustine_invents_voluntas",
    "synthesis_dihle1982_indian_excursus_intellectualism_parallel",
    "synthesis_dihle1982_methodological_thesis_summary",
]
for sid in SYNTHESIS_IDS:
    NEW_EDGES.append(_edge(sid, "scholar_albrecht_dihle", "authored_by"))


# =============================================================================
# 3. SCHOLARLY ARGUMENTS authored_by Dihle
# =============================================================================
ARGUMENT_IDS = [
    "argument_dihle_1982_greek_intellectualism_thesis",
    "argument_dihle_1982_hebrew_obedience_non_cognitive_will",
    "argument_dihle_1982_paul_romans_7_split_will",
    "argument_dihle_1982_paul_no_dedicated_term_for_will",
    "argument_dihle_1982_pauline_conscience_distinctive",
    "argument_dihle_1982_augustine_invents_philosophical_voluntas",
    "argument_dihle_1982_plotinus_remains_intellectualist",
    "argument_dihle_1982_synkatathesis_is_cognitive_not_volitional",
    "argument_dihle_1982_critique_anachronism_in_attribution_will_to_greeks",
    "argument_dihle_1982_voluntas_latin_pre_augustine_loose_semantics",
    "argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
    "argument_dihle_1982_indian_parallel_dharma_intellectualism",
]
for aid in ARGUMENT_IDS:
    NEW_EDGES.append(_edge(aid, "scholar_albrecht_dihle", "authored_by"))


# =============================================================================
# 4. SYNTHESIS-LEVEL DISCUSSIONS — synthesis -> ancient persons / works / concepts
# =============================================================================
NEW_EDGES.extend([
    # Lect. I — cosmology
    _edge("synthesis_dihle1982_lec1_cosmology_second_century",
          "concept_greek_intellectualism_dihle", "discusses"),
    _edge("synthesis_dihle1982_lec1_cosmology_second_century",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_dihle1982_lec1_cosmology_second_century",
          "person_cleanthes_assos_330_230bce", "discusses"),

    # Lect. II — Greek intellectualism
    _edge("synthesis_dihle1982_lec2_greek_intellectualism_action",
          "person_plato_428_348bce_a1b2c3d4", "discusses"),
    _edge("synthesis_dihle1982_lec2_greek_intellectualism_action",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("synthesis_dihle1982_lec2_greek_intellectualism_action",
          "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "discusses"),
    _edge("synthesis_dihle1982_lec2_greek_intellectualism_action",
          "concept_boulesis_rational_desire_ef9f861d", "discusses"),
    _edge("synthesis_dihle1982_lec2_greek_intellectualism_action",
          "concept_akrasia_weakness_of_will", "discusses"),
    _edge("synthesis_dihle1982_lec2_greek_intellectualism_action",
          "concept_socratic_intellectualism_f6g7h8i9", "discusses"),
    _edge("synthesis_dihle1982_lec2_greek_intellectualism_action",
          "concept_greek_intellectualism_dihle", "discusses"),

    # Lect. III — Stoic synkatathesis
    _edge("synthesis_dihle1982_lec3_stoic_assent_cognitive",
          "person_zeno_citium_334_262bce", "discusses"),
    _edge("synthesis_dihle1982_lec3_stoic_assent_cognitive",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_dihle1982_lec3_stoic_assent_cognitive",
          "person_cleanthes_assos_330_230bce", "discusses"),
    _edge("synthesis_dihle1982_lec3_stoic_assent_cognitive",
          "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("synthesis_dihle1982_lec3_stoic_assent_cognitive",
          "person_seneca_4bce_65ce_a1b2c3d4", "discusses"),
    _edge("synthesis_dihle1982_lec3_stoic_assent_cognitive",
          "person_epicurus_341_270bce_j0k1l2m3", "discusses"),
    _edge("synthesis_dihle1982_lec3_stoic_assent_cognitive",
          "concept_synkatathesis_stoic_assent", "discusses"),

    # Lect. IV — Paul and Philo
    _edge("synthesis_dihle1982_lec4_paul_philo_implicit_will",
          "person_philo_alexandria_a1b2c3d4", "discusses"),

    # Lect. V — late antiquity / Plotinus
    _edge("synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
          "person_plotinus_d270", "discusses"),
    _edge("synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
          "person_porphyry", "discusses"),
    _edge("synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
          "person_iamblichus_d325", "discusses"),
    _edge("synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
          "person_nemesius_emesa_4c_ce", "discusses"),
    _edge("synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
          "work_plotinus_ennead_vi_8_d8b9c5a4", "discusses"),
    _edge("synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
          "work_plotinus_enneads_iv_8", "discusses"),
    _edge("synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
          "work_plotinus_enn_iii_1", "discusses"),

    # Lect. VI — Augustine invents voluntas
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "person_augustine_hippo_d430", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "person_pelagius_d420", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "person_seneca_4bce_65ce_a1b2c3d4", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "concept_voluntas_y7z8a9b0", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "concept_liberum_arbitrium_u3v4w5x6", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "work_augustine_de_libero_arbitrio", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "work_augustine_confessiones_viii", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "work_augustine_de_gratia_la", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "work_augustine_de_spiritu_littera", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "work_augustine_de_correptione", "discusses"),
    _edge("synthesis_dihle1982_lec6_augustine_invents_voluntas",
          "work_augustine_de_praed_sanct", "discusses"),

    # Methodological / Indian
    _edge("synthesis_dihle1982_methodological_thesis_summary",
          "person_frede_michael_1940_2007", "discusses"),
    _edge("synthesis_dihle1982_methodological_thesis_summary",
          "person_bobzien_susanne_contemporary", "discusses"),
    _edge("synthesis_dihle1982_methodological_thesis_summary",
          "person_sorabji_richard_contemporary", "discusses"),
    _edge("synthesis_dihle1982_indian_excursus_intellectualism_parallel",
          "concept_greek_intellectualism_dihle", "discusses"),
])


# =============================================================================
# 5. ARGUMENT-LEVEL DISCUSSIONS — scholarly arg -> ancient target
# =============================================================================
NEW_EDGES.extend([
    # 1. Greek intellectualism thesis
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "concept_greek_intellectualism_dihle", "discusses"),
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "person_plato_428_348bce_a1b2c3d4", "discusses"),
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "person_epicurus_341_270bce_j0k1l2m3", "discusses"),
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "person_plotinus_d270", "discusses"),

    # 2. Hebrew obedience
    _edge("argument_dihle_1982_hebrew_obedience_non_cognitive_will",
          "concept_ratzon_g5h6i7j8", "discusses"),

    # 3. Paul Rom 7
    _edge("argument_dihle_1982_paul_romans_7_split_will",
          "work_new_testament", "discusses"),

    # 4. Paul no dedicated term
    _edge("argument_dihle_1982_paul_no_dedicated_term_for_will",
          "work_new_testament", "discusses"),
    _edge("argument_dihle_1982_paul_no_dedicated_term_for_will",
          "concept_thelesis_willing_87d2b3cf", "discusses"),
    _edge("argument_dihle_1982_paul_no_dedicated_term_for_will",
          "concept_boulesis_rational_desire_ef9f861d", "discusses"),

    # 5. Pauline conscience
    _edge("argument_dihle_1982_pauline_conscience_distinctive",
          "work_new_testament", "discusses"),

    # 6. Augustine invents voluntas (central thesis)
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "person_augustine_hippo_d430", "discusses"),
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "concept_voluntas_y7z8a9b0", "discusses"),
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "work_augustine_confessiones_viii", "discusses"),
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "work_augustine_de_libero_arbitrio", "discusses"),
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "work_augustine_de_gratia_la", "discusses"),

    # 7. Plotinus
    _edge("argument_dihle_1982_plotinus_remains_intellectualist",
          "person_plotinus_d270", "discusses"),
    _edge("argument_dihle_1982_plotinus_remains_intellectualist",
          "work_plotinus_ennead_vi_8_d8b9c5a4", "discusses"),
    _edge("argument_dihle_1982_plotinus_remains_intellectualist",
          "work_plotinus_enn_iii_1", "discusses"),

    # 8. Synkatathesis is cognitive
    _edge("argument_dihle_1982_synkatathesis_is_cognitive_not_volitional",
          "concept_synkatathesis_stoic_assent", "discusses"),
    _edge("argument_dihle_1982_synkatathesis_is_cognitive_not_volitional",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("argument_dihle_1982_synkatathesis_is_cognitive_not_volitional",
          "person_zeno_citium_334_262bce", "discusses"),
    _edge("argument_dihle_1982_synkatathesis_is_cognitive_not_volitional",
          "person_cleanthes_assos_330_230bce", "discusses"),
    _edge("argument_dihle_1982_synkatathesis_is_cognitive_not_volitional",
          "person_seneca_4bce_65ce_a1b2c3d4", "discusses"),

    # 9. Critique anachronism
    _edge("argument_dihle_1982_critique_anachronism_in_attribution_will_to_greeks",
          "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "discusses"),
    _edge("argument_dihle_1982_critique_anachronism_in_attribution_will_to_greeks",
          "concept_boulesis_rational_desire_ef9f861d", "discusses"),

    # 10. Voluntas Latin pre-Augustinian
    _edge("argument_dihle_1982_voluntas_latin_pre_augustine_loose_semantics",
          "person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "discusses"),
    _edge("argument_dihle_1982_voluntas_latin_pre_augustine_loose_semantics",
          "person_seneca_4bce_65ce_a1b2c3d4", "discusses"),
    _edge("argument_dihle_1982_voluntas_latin_pre_augustine_loose_semantics",
          "concept_voluntas_y7z8a9b0", "discusses"),

    # 11. Augustine responds to Manichean and Pelagian
    _edge("argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
          "person_augustine_hippo_d430", "discusses"),
    _edge("argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
          "person_pelagius_d420", "discusses"),
])


# =============================================================================
# 6. CRITIQUES — Dihle scholarly args critique Kenny, Greek intellectualism
# =============================================================================
NEW_EDGES.extend([
    # Critique of Kenny's "Aristotle's Theory of the Will" (1979)
    # Kenny does not have an existing person node, so we critique at the
    # argument level. No edge — to be added in a follow-up if Kenny is added.

    # Critique of Greek intellectualism as a structural feature (not a defect)
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "concept_socratic_intellectualism_f6g7h8i9", "critiques",
          confidence=0.8,
          dihle_source="Dihle 1982 Lect. II §I, p. 20-25"),
])


# =============================================================================
# 7. DISAGREEMENT EDGES — Dihle vs Frede / Bobzien
# =============================================================================
NEW_EDGES.extend([
    # Dihle disagrees with Frede on locus of free-will genesis
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "person_frede_michael_1940_2007", "opposes",
          confidence=0.9,
          stance="opposes",
          dihle_source="Dihle = Augustinian invention; Frede 2011 p. 77 = Epictetus",
          methodological_disagreement="locus of free-will genesis"),
    # Dihle 's central thesis is critiqued by Frede 2011 in turn (reverse)
    _edge("scholar_albrecht_dihle", "person_frede_michael_1940_2007", "engages_with",
          confidence=0.95,
          stance="critiqued_by",
          note="Frede 2011 (Sather 64) cites Dihle 1982 39 times — central interlocutor"),

    # Bobzien rejects Dihle's interpretive grid
    _edge("argument_dihle_1982_critique_anachronism_in_attribution_will_to_greeks",
          "person_bobzien_susanne_contemporary", "engages_with",
          confidence=0.85,
          stance="qualifies",
          note="Bobzien 1998 cites Dihle 2x; rejects 'intellectualism vs voluntarism' as anachronistic"),
])


# =============================================================================
# 8. INFLUENCE CHAINS — Pohlenz / Snell / Voelke / Kahn -> Dihle
# =============================================================================
NEW_EDGES.extend([
    # Pohlenz precedes and influences Dihle
    _edge("scholar_pohlenz_max", "scholar_albrecht_dihle", "influences",
          confidence=0.9,
          dihle_source="Pohlenz Die Stoa 1948-49 = main precursor on 'Stoa without will'"),
    # Snell precedes Dihle
    _edge("scholar_snell_bruno", "scholar_albrecht_dihle", "influences",
          confidence=0.85,
          dihle_source="Snell Die Entdeckung des Geistes 1946 = precursor on evolution of self"),
    # Voelke directly precedes Dihle
    _edge("scholar_voelke_andre_jean", "scholar_albrecht_dihle", "influences",
          confidence=0.9,
          dihle_source="Voelke 1973 L'idee de volonte dans le stoicisme = direct predecessor"),
    # Kahn agrees and supports Dihle (we use influences cautiously here)
    _edge("scholar_kahn_charles", "scholar_albrecht_dihle", "agrees_with",
          confidence=0.85,
          dihle_source="Kahn 1988 supports Dihle's thesis on Aristotelian terms"),

    # Dihle influences subsequent scholars (forward propagation)
    _edge("scholar_albrecht_dihle", "person_frede_michael_1940_2007", "influences",
          confidence=0.95,
          dihle_source="Frede 2011 cites Dihle 39 times — central engagement"),
    _edge("scholar_albrecht_dihle", "person_sorabji_richard_contemporary", "influences",
          confidence=0.85,
          dihle_source="Sorabji 2000 Emotion and Peace of Mind builds partly on Dihle"),
    _edge("scholar_albrecht_dihle", "person_bobzien_susanne_contemporary", "influences",
          confidence=0.7,
          dihle_source="Bobzien 1998 engages critically with Dihle"),
])


# =============================================================================
# 9. RELATED PUBLICATIONS — pub_dihle_1982 influenced by pub_pohlenz / pub_snell / pub_voelke
# =============================================================================
NEW_EDGES.extend([
    _edge("pub_dihle_1982_theory_of_will", "pub_pohlenz_1948_stoa", "extends",
          confidence=0.9,
          stance="extends_methodology_and_thesis"),
    _edge("pub_dihle_1982_theory_of_will", "pub_snell_1946_entdeckung_geistes", "extends",
          confidence=0.85,
          stance="extends_evolution_of_self_thesis"),
    _edge("pub_dihle_1982_theory_of_will", "pub_voelke_1973_idee_volonte", "extends",
          confidence=0.9,
          stance="extends_no_concept_of_will_thesis"),
])


# =============================================================================
# 10. DEBATE PARTICIPATION — Dihle args + syntheses contribute to debates
# =============================================================================
NEW_EDGES.extend([
    # Central thesis -> debate_discovery_of_will
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "debate_discovery_of_will", "contributes_to"),
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "debate_discovery_of_will", "contributes_to"),
    _edge("argument_dihle_1982_paul_romans_7_split_will",
          "debate_discovery_of_will", "contributes_to"),
    _edge("argument_dihle_1982_plotinus_remains_intellectualist",
          "debate_discovery_of_will", "contributes_to"),

    # Synkatathesis arg + critique arg -> debate_intellectualism_vs_voluntarism
    _edge("argument_dihle_1982_synkatathesis_is_cognitive_not_volitional",
          "debate_intellectualism_vs_voluntarism_w3x4y5z6", "contributes_to"),
    _edge("argument_dihle_1982_critique_anachronism_in_attribution_will_to_greeks",
          "debate_intellectualism_vs_voluntarism_w3x4y5z6", "contributes_to"),
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "debate_intellectualism_vs_voluntarism_w3x4y5z6", "contributes_to"),

    # Augustine-Pelagian arg -> debate_augustine_pelagius_grace
    _edge("argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
          "debate_augustine_pelagius_grace", "contributes_to"),

    # Pub -> debates
    _edge("pub_dihle_1982_theory_of_will",
          "debate_discovery_of_will", "contributes_to"),
    _edge("pub_dihle_1982_theory_of_will",
          "debate_intellectualism_vs_voluntarism_w3x4y5z6", "contributes_to"),
])


# =============================================================================
# 11. CITES_PRIMARY_SOURCE — Dihle scholarly args cite ancient works
# =============================================================================
NEW_EDGES.extend([
    # Paul Rom 7 -> work_new_testament
    _edge("argument_dihle_1982_paul_romans_7_split_will",
          "work_new_testament", "cites_primary_source",
          confidence=0.95,
          dihle_source="Dihle 1982 Lect. IV §II-III, Rom 7 exegesis"),
    _edge("argument_dihle_1982_paul_no_dedicated_term_for_will",
          "work_new_testament", "cites_primary_source",
          confidence=0.95),
    _edge("argument_dihle_1982_pauline_conscience_distinctive",
          "work_new_testament", "cites_primary_source",
          confidence=0.9),

    # Hebrew obedience -> work_septuagint (closest preserved biblical work node)
    _edge("argument_dihle_1982_hebrew_obedience_non_cognitive_will",
          "work_septuagint", "cites_primary_source",
          confidence=0.7,
          dihle_source="Dihle 1982 Lect. IV §I, Hebrew Bible terminology (ratzon, kavod)"),

    # Synkatathesis -> Stoic works (no SVF work node ; use Seneca ep proxy)
    # Augustine arg -> Augustine works
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "work_augustine_de_libero_arbitrio", "cites_primary_source",
          confidence=0.9),
    _edge("argument_dihle_1982_augustine_invents_philosophical_voluntas",
          "work_augustine_confessiones_viii", "cites_primary_source",
          confidence=0.9),
    _edge("argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
          "work_augustine_de_libero_arbitrio", "cites_primary_source",
          confidence=0.9),
    _edge("argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
          "work_augustine_de_gratia_la", "cites_primary_source",
          confidence=0.9),
    _edge("argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
          "work_augustine_de_correptione", "cites_primary_source",
          confidence=0.85),
    _edge("argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
          "work_augustine_de_praed_sanct", "cites_primary_source",
          confidence=0.85),
    _edge("argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
          "work_augustine_de_spiritu_littera", "cites_primary_source",
          confidence=0.85),

    # Plotinus arg -> Plotinus works
    _edge("argument_dihle_1982_plotinus_remains_intellectualist",
          "work_plotinus_ennead_vi_8_d8b9c5a4", "cites_primary_source",
          confidence=0.95),
    _edge("argument_dihle_1982_plotinus_remains_intellectualist",
          "work_plotinus_enn_iii_1", "cites_primary_source",
          confidence=0.9),
    _edge("argument_dihle_1982_plotinus_remains_intellectualist",
          "work_plotinus_enneads_iv_8", "cites_primary_source",
          confidence=0.9),

    # Aristotle (Greek intellectualism + critique anachronism)
    _edge("argument_dihle_1982_greek_intellectualism_thesis",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "cites_primary_source",
          confidence=0.9),
    _edge("argument_dihle_1982_critique_anachronism_in_attribution_will_to_greeks",
          "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9", "cites_primary_source",
          confidence=0.85),
])


# =============================================================================
# 12. SCHOLAR identity edges — Dihle is a scholar (person) ; affiliations
# =============================================================================
# (no school-of-philosophy edges — Dihle is modern; we keep him as a person scholar)


# =============================================================================
# 13. WROTE_ABOUT — Dihle wrote about Augustine, Paul, Aristotle, Plotinus, Stoics
# =============================================================================
NEW_EDGES.extend([
    _edge("scholar_albrecht_dihle", "person_augustine_hippo_d430", "wrote_about",
          confidence=0.99,
          dihle_source="Dihle 1982 Lect. VI entirely on Augustine"),
    _edge("scholar_albrecht_dihle", "person_aristotle_384_322bce_c2d4f6a8", "wrote_about",
          confidence=0.95,
          dihle_source="Dihle 1982 Lect. II §III on Aristotle"),
    _edge("scholar_albrecht_dihle", "person_plato_428_348bce_a1b2c3d4", "wrote_about",
          confidence=0.9,
          dihle_source="Dihle 1982 Lect. II §I on Socratic intellectualism"),
    _edge("scholar_albrecht_dihle", "person_chrysippus_280_206bce_i9j0k1l2", "wrote_about",
          confidence=0.95,
          dihle_source="Dihle 1982 Lect. III on Stoic synkatathesis"),
    _edge("scholar_albrecht_dihle", "person_plotinus_d270", "wrote_about",
          confidence=0.95,
          dihle_source="Dihle 1982 Lect. V on Plotinus"),
    _edge("scholar_albrecht_dihle", "person_philo_alexandria_a1b2c3d4", "wrote_about",
          confidence=0.95,
          dihle_source="Dihle 1982 Lect. IV §IV on Philo"),
    _edge("scholar_albrecht_dihle", "person_epictetus_of_hierapolis_3c385bc2", "wrote_about",
          confidence=0.9,
          dihle_source="Dihle 1982 Lect. III on Epictetus"),
])


# =============================================================================
# 14. PUBLICATION-LEVEL discusses ancient debates and persons
# =============================================================================
NEW_EDGES.extend([
    _edge("pub_dihle_1982_theory_of_will", "person_augustine_hippo_d430", "discusses",
          confidence=0.99),
    _edge("pub_dihle_1982_theory_of_will", "person_aristotle_384_322bce_c2d4f6a8", "discusses",
          confidence=0.95),
    _edge("pub_dihle_1982_theory_of_will", "person_chrysippus_280_206bce_i9j0k1l2", "discusses",
          confidence=0.95),
    _edge("pub_dihle_1982_theory_of_will", "person_plotinus_d270", "discusses",
          confidence=0.95),
    _edge("pub_dihle_1982_theory_of_will", "person_philo_alexandria_a1b2c3d4", "discusses",
          confidence=0.95),
    _edge("pub_dihle_1982_theory_of_will", "person_plato_428_348bce_a1b2c3d4", "discusses",
          confidence=0.9),
    _edge("pub_dihle_1982_theory_of_will", "concept_voluntas_y7z8a9b0", "discusses"),
    _edge("pub_dihle_1982_theory_of_will", "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6", "discusses"),
    _edge("pub_dihle_1982_theory_of_will", "concept_synkatathesis_stoic_assent", "discusses"),
    _edge("pub_dihle_1982_theory_of_will", "concept_greek_intellectualism_dihle", "discusses"),
    _edge("pub_dihle_1982_theory_of_will", "concept_liberum_arbitrium_u3v4w5x6", "discusses"),
])
