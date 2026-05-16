"""Bobzien 2001 B1 — NEW_EDGES list.

Allowed relations per knowledge graph/ontology/edge_types.json (subset used here):
- authored_by         : src argument/synthesis -> tgt person
- discusses           : src argument/synthesis/publication -> tgt argument/concept/person/school/work
- interprets          : src argument/publication -> tgt argument/concept/passage/person/work
- critiques           : src argument/publication -> tgt argument/concept/person/publication/work
- cites_primary_source: src argument/publication/person -> tgt passage/work
- influences / influenced_by : src person -> tgt person
- part_of             : src argument/synthesis -> tgt publication / work
- supports            : src argument/synthesis -> tgt argument/concept/person
- responds_to         : src argument -> tgt argument/concept/debate/person
- engages_with        : modern scholar/publication engages with another
- agrees_with / opposes : modern scholar position vs another

NB. `part_of` cannot point to `publication` per ontology — synthesis/argument
nodes link to the publication via `discusses` (the publication) or
`authored_by` the scholar. We use `discusses` + `authored_by` consistently.
"""
from __future__ import annotations

from typing import Any

from bobzien_2001_b1_utils import (
    BOBZIEN_PERSON_ID,
    BOBZIEN_PUBLICATION_ID,
)

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
# 1. AUTHORSHIP — all new syntheses + arguments authored_by Bobzien
# =============================================================================
NEW_SYNTHESES_IDS = [
    "synthesis_bobzien2001_ch1_determinism_and_fate",
    "synthesis_bobzien2001_ch2_chrysippean_arguments",
    "synthesis_bobzien2001_ch3_modality",
    "synthesis_bobzien2001_ch4_divination_regularity",
    "synthesis_bobzien2001_ch5_idle_argument",
    "synthesis_bobzien2001_ch6_chrysippean_compatibilism",
    "synthesis_bobzien2001_ch7_epictetus_eph_hemin_eleutheria",
    "synthesis_bobzien2001_ch8_philopator_late_stoic",
]

NEW_ARGUMENT_IDS = [
    "argument_bobzien_2001_b1_no_free_will_in_stoa",
    "argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction",
    "argument_bobzien_2001_b1_lazy_argument_cofated_solution",
    "argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided",
    "argument_bobzien_2001_b1_synkatathesis_psychology_action",
    "argument_bobzien_2001_b1_master_argument_reconstruction",
    "argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence",
    "argument_bobzien_2001_b1_pneumatic_causation_model",
    "argument_bobzien_2001_b1_critique_anachronistic_freewill",
    "argument_bobzien_2001_b1_epictetus_developmental_freedom",
    "argument_bobzien_2001_b1_chrysippean_modal_system",
    "argument_bobzien_2001_b1_philopator_late_compatibilism",
    "argument_bobzien_2001_b1_origen_idle_argument_reply",
    "argument_bobzien_2001_b1_cylinder_in_later_fate_theory",
    "argument_bobzien_2001_b1_rise_fall_freedom_problem",
]

NEW_CONCEPT_IDS = [
    "concept_chrysippean_compatibilism_bobzien",
    "concept_pneumatic_causation_stoic_bobzien",
    "concept_fate_principle_bobzien",
    "concept_philopator_compatibilism_bobzien",
]

# All scholarly syntheses + arguments are authored by Bobzien
for sid in NEW_SYNTHESES_IDS + NEW_ARGUMENT_IDS:
    NEW_EDGES.append(_edge(sid, BOBZIEN_PERSON_ID, "authored_by"))


# =============================================================================
# 2. PUBLICATION RELATIONS — syntheses + arguments link to the publication
#    via metadata only (per ontology, `discusses` cannot target publication).
#    The `published` edge from Bobzien -> publication is left to the existing
#    KG / not duplicated here.
# =============================================================================
# (intentionally empty — see metadata.publication on every node for the link)


# =============================================================================
# 3. SYNTHESIS DISCUSSES the ancient figures + concepts of each chapter
# =============================================================================
NEW_EDGES.extend([
    # Ch.1 — determinism and fate: Chrysippus, Zeno, Cleanthes, heimarmene, sympatheia
    _edge("synthesis_bobzien2001_ch1_determinism_and_fate", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_bobzien2001_ch1_determinism_and_fate", "person_zeno_citium_334_262bce", "discusses"),
    _edge("synthesis_bobzien2001_ch1_determinism_and_fate", "person_cleanthes_assos_330_230bce", "discusses"),
    _edge("synthesis_bobzien2001_ch1_determinism_and_fate", "concept_heimarmene_fate_stoics_j0k1l2m3", "discusses"),
    _edge("synthesis_bobzien2001_ch1_determinism_and_fate", "concept_sympatheia_stoic", "discusses"),
    _edge("synthesis_bobzien2001_ch1_determinism_and_fate", "concept_fate_principle_bobzien", "discusses"),
    _edge("synthesis_bobzien2001_ch1_determinism_and_fate", "concept_pneumatic_causation_stoic_bobzien", "discusses"),

    # Ch.2 — Chrysippean arguments (bivalence + divination)
    _edge("synthesis_bobzien2001_ch2_chrysippean_arguments", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_bobzien2001_ch2_chrysippean_arguments", "argument_sea_battle_aristotle_f6g7h8i9", "discusses"),
    _edge("synthesis_bobzien2001_ch2_chrysippean_arguments", "concept_sea_battle_future_contingents", "discusses"),
    _edge("synthesis_bobzien2001_ch2_chrysippean_arguments", "work_de_divinatione_cicero", "discusses"),

    # Ch.3 — Modality: Chrysippus vs Diodorus
    _edge("synthesis_bobzien2001_ch3_modality", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_bobzien2001_ch3_modality", "person_diodorus_cronus_48ef6200", "discusses"),
    _edge("synthesis_bobzien2001_ch3_modality", "argument_the_master_argument_kurieuon_logos_355f4d3f", "discusses"),

    # Ch.4 — Divination
    _edge("synthesis_bobzien2001_ch4_divination_regularity", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_bobzien2001_ch4_divination_regularity", "work_de_divinatione_cicero", "discusses"),

    # Ch.5 — Idle Argument
    _edge("synthesis_bobzien2001_ch5_idle_argument", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_bobzien2001_ch5_idle_argument", "argument_the_lazy_argument_argos_logos_702a77ed", "discusses"),
    _edge("synthesis_bobzien2001_ch5_idle_argument", "argument_the_cofated_events_argument_confatalia_b7715646", "discusses"),
    _edge("synthesis_bobzien2001_ch5_idle_argument", "debate_lazy_argument", "discusses"),
    _edge("synthesis_bobzien2001_ch5_idle_argument", "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    _edge("synthesis_bobzien2001_ch5_idle_argument", "concept_confatalia_chrysippus", "discusses"),

    # Ch.6 — Compatibilism + cylinder
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "argument_cylinder_analogy_chrysippus_k1l2m3n4", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "concept_cylinder_analogy_chrysippus_e5f6g7h8", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "concept_eph_hemin_one_sided_causative", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "concept_eph_hemin_two_sided_potestative", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "concept_synkatathesis_stoic_assent", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "concept_chrysippean_compatibilism_bobzien", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "person_carneades_214_129bce_l2m3n4o5", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "person_plutarch_45_120ce_b9c2a8f3", "discusses"),

    # Ch.7 — Epictetus + eleutheria
    _edge("synthesis_bobzien2001_ch7_epictetus_eph_hemin_eleutheria", "person_epictetus_of_hierapolis_3c385bc2", "discusses"),
    _edge("synthesis_bobzien2001_ch7_epictetus_eph_hemin_eleutheria", "person_cleanthes_assos_330_230bce", "discusses"),
    _edge("synthesis_bobzien2001_ch7_epictetus_eph_hemin_eleutheria", "concept_eph_hemin_one_sided_causative", "discusses"),
    _edge("synthesis_bobzien2001_ch7_epictetus_eph_hemin_eleutheria", "work_epictetus_discourses", "discusses"),

    # Ch.8 — PHILOPATOR
    _edge("synthesis_bobzien2001_ch8_philopator_late_stoic", "concept_philopator_compatibilism_bobzien", "discusses"),
    _edge("synthesis_bobzien2001_ch8_philopator_late_stoic", "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge("synthesis_bobzien2001_ch8_philopator_late_stoic", "argument_cylinder_analogy_chrysippus_k1l2m3n4", "discusses"),
])


# =============================================================================
# 4. SYNTHESES discuss central scholarly arguments (cross-link)
# =============================================================================
NEW_EDGES.extend([
    _edge("synthesis_bobzien2001_ch1_determinism_and_fate", "argument_bobzien_2001_b1_pneumatic_causation_model", "discusses"),
    _edge("synthesis_bobzien2001_ch2_chrysippean_arguments", "argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence", "discusses"),
    _edge("synthesis_bobzien2001_ch3_modality", "argument_bobzien_2001_b1_master_argument_reconstruction", "discusses"),
    _edge("synthesis_bobzien2001_ch3_modality", "argument_bobzien_2001_b1_chrysippean_modal_system", "discusses"),
    _edge("synthesis_bobzien2001_ch5_idle_argument", "argument_bobzien_2001_b1_lazy_argument_cofated_solution", "discusses"),
    _edge("synthesis_bobzien2001_ch5_idle_argument", "argument_bobzien_2001_b1_origen_idle_argument_reply", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided", "discusses"),
    _edge("synthesis_bobzien2001_ch6_chrysippean_compatibilism", "argument_bobzien_2001_b1_synkatathesis_psychology_action", "discusses"),
    _edge("synthesis_bobzien2001_ch7_epictetus_eph_hemin_eleutheria", "argument_bobzien_2001_b1_epictetus_developmental_freedom", "discusses"),
    _edge("synthesis_bobzien2001_ch8_philopator_late_stoic", "argument_bobzien_2001_b1_philopator_late_compatibilism", "discusses"),
    _edge("synthesis_bobzien2001_ch8_philopator_late_stoic", "argument_bobzien_2001_b1_cylinder_in_later_fate_theory", "discusses"),
    _edge("synthesis_bobzien2001_ch8_philopator_late_stoic", "argument_bobzien_2001_b1_rise_fall_freedom_problem", "discusses"),
    _edge("synthesis_bobzien2001_ch8_philopator_late_stoic", "argument_bobzien_2001_b1_no_free_will_in_stoa", "discusses"),
])


# =============================================================================
# 5. SCHOLARLY ARGUMENTS INTERPRET ancient arguments / concepts / persons
# =============================================================================
NEW_EDGES.extend([
    # No free will in stoa — interprets the Stoic position on freedom
    _edge("argument_bobzien_2001_b1_no_free_will_in_stoa", "person_chrysippus_280_206bce_i9j0k1l2", "interprets"),
    _edge("argument_bobzien_2001_b1_no_free_will_in_stoa", "person_epictetus_of_hierapolis_3c385bc2", "interprets"),
    _edge("argument_bobzien_2001_b1_no_free_will_in_stoa", "concept_eph_hemin_one_sided_causative", "interprets"),
    _edge("argument_bobzien_2001_b1_no_free_will_in_stoa", "concept_chrysippean_compatibilism_bobzien", "supports"),

    # Cylinder reconstruction
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "argument_cylinder_analogy_chrysippus_k1l2m3n4", "interprets"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "concept_cylinder_analogy_chrysippus_e5f6g7h8", "interprets"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "person_chrysippus_280_206bce_i9j0k1l2", "interprets"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "concept_chrysippean_compatibilism_bobzien", "supports"),

    # Lazy Argument
    _edge("argument_bobzien_2001_b1_lazy_argument_cofated_solution", "argument_the_lazy_argument_argos_logos_702a77ed", "interprets"),
    _edge("argument_bobzien_2001_b1_lazy_argument_cofated_solution", "argument_the_cofated_events_argument_confatalia_b7715646", "interprets"),
    _edge("argument_bobzien_2001_b1_lazy_argument_cofated_solution", "concept_confatalia_chrysippus", "interprets"),
    _edge("argument_bobzien_2001_b1_lazy_argument_cofated_solution", "debate_lazy_argument", "discusses"),

    # Eph hemin distinction
    _edge("argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided", "concept_eph_hemin_one_sided_causative", "interprets"),
    _edge("argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided", "concept_eph_hemin_two_sided_potestative", "interprets"),
    _edge("argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided", "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "discusses"),
    _edge("argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided", "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7", "discusses"),

    # Synkatathesis
    _edge("argument_bobzien_2001_b1_synkatathesis_psychology_action", "concept_synkatathesis_stoic_assent", "interprets"),
    _edge("argument_bobzien_2001_b1_synkatathesis_psychology_action", "person_chrysippus_280_206bce_i9j0k1l2", "interprets"),

    # Master Argument
    _edge("argument_bobzien_2001_b1_master_argument_reconstruction", "argument_the_master_argument_kurieuon_logos_355f4d3f", "interprets"),
    _edge("argument_bobzien_2001_b1_master_argument_reconstruction", "person_diodorus_cronus_48ef6200", "interprets"),

    # Sea Battle / bivalence
    _edge("argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence", "argument_sea_battle_aristotle_f6g7h8i9", "interprets"),
    _edge("argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence", "concept_sea_battle_future_contingents", "interprets"),
    _edge("argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence", "person_chrysippus_280_206bce_i9j0k1l2", "interprets"),

    # Pneumatic causation
    _edge("argument_bobzien_2001_b1_pneumatic_causation_model", "concept_pneumatic_causation_stoic_bobzien", "supports"),
    _edge("argument_bobzien_2001_b1_pneumatic_causation_model", "concept_sympatheia_stoic", "interprets"),

    # Critique anachronistic — critiques Long & Sedley + Dihle
    _edge("argument_bobzien_2001_b1_critique_anachronistic_freewill", "scholarly_work_long_sedley_1987_hellenistic_philosophers", "critiques"),

    # Epictetus developmental
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "person_epictetus_of_hierapolis_3c385bc2", "interprets"),
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "argument_epictetus_dichotomy_control", "interprets"),
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "argument_epictetus_freedom_renunciation", "interprets"),
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "argument_epictetus_prohairesis_argument_aa13b932", "interprets"),

    # Chrysippean modal system
    _edge("argument_bobzien_2001_b1_chrysippean_modal_system", "person_chrysippus_280_206bce_i9j0k1l2", "interprets"),
    _edge("argument_bobzien_2001_b1_chrysippean_modal_system", "person_diodorus_cronus_48ef6200", "discusses"),

    # PHILOPATOR
    _edge("argument_bobzien_2001_b1_philopator_late_compatibilism", "concept_philopator_compatibilism_bobzien", "supports"),
    _edge("argument_bobzien_2001_b1_philopator_late_compatibilism", "concept_chrysippean_compatibilism_bobzien", "discusses"),

    # Origen reply
    _edge("argument_bobzien_2001_b1_origen_idle_argument_reply", "person_origen_alexandria_185_254ce_s9t0u1v2", "interprets"),
    _edge("argument_bobzien_2001_b1_origen_idle_argument_reply", "argument_origen_argos_logos", "interprets"),
    _edge("argument_bobzien_2001_b1_origen_idle_argument_reply", "argument_the_lazy_argument_argos_logos_702a77ed", "discusses"),

    # Cylinder in later fate theory
    _edge("argument_bobzien_2001_b1_cylinder_in_later_fate_theory", "argument_cylinder_analogy_chrysippus_k1l2m3n4", "interprets"),
    _edge("argument_bobzien_2001_b1_cylinder_in_later_fate_theory", "concept_philopator_compatibilism_bobzien", "supports"),

    # Rise and fall of freedom problem
    _edge("argument_bobzien_2001_b1_rise_fall_freedom_problem", "person_alexander_aphrodisias_fl200ce_n5o6p7q8", "interprets"),
    _edge("argument_bobzien_2001_b1_rise_fall_freedom_problem", "concept_eph_hemin_two_sided_potestative", "interprets"),
    _edge("argument_bobzien_2001_b1_rise_fall_freedom_problem", "concept_eph_hemin_one_sided_causative", "interprets"),
    _edge("argument_bobzien_2001_b1_rise_fall_freedom_problem", "person_carneades_214_129bce_l2m3n4o5", "discusses"),
])


# =============================================================================
# 6. CITES_PRIMARY_SOURCE — scholarly arguments cite ancient passages/works
# =============================================================================
NEW_EDGES.extend([
    # Cylinder analogy <-- Cic. Fat. 39-44 + Gellius NA 7.2
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "passage_cicero_fat_39", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "passage_cicero_fat_40", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "passage_cicero_fat_41", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "passage_cicero_fat_42", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "passage_cicero_fat_43", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "passage_cicero_fat_44", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "work_gellius_na_vii_2", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "work_de_fato_cicero_44bce_b9c4e5d2", "cites_primary_source"),

    # Lazy Argument cites Cic. Fat. 28, Origen CC, work_origen_contra_celsum_sc132
    _edge("argument_bobzien_2001_b1_lazy_argument_cofated_solution", "passage_cicero_fat_28", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_lazy_argument_cofated_solution", "work_origen_contra_celsum_sc132", "cites_primary_source"),

    # Origen Idle reply cites Origen CC
    _edge("argument_bobzien_2001_b1_origen_idle_argument_reply", "work_origen_contra_celsum_sc132", "cites_primary_source"),

    # Synkatathesis & cylinder = Gellius NA + Cic. Fat.
    _edge("argument_bobzien_2001_b1_synkatathesis_psychology_action", "work_gellius_na_vii_2", "cites_primary_source"),

    # Chrysippus and modality cites Cic. Fat.
    _edge("argument_bobzien_2001_b1_chrysippean_modal_system", "work_de_fato_cicero_44bce_b9c4e5d2", "cites_primary_source"),

    # Sea battle cites Cic. Fat. (general)
    _edge("argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence", "work_de_fato_cicero_44bce_b9c4e5d2", "cites_primary_source"),

    # Divination — synthesis nodes link via `discusses` (ontology forbids
    # synthesis->work cites_primary_source); the per-argument cites_primary_source
    # edges (above) carry the citation chain. The synthesis->work_de_divinatione
    # discusses edges are already declared in section 3.

    # Epictetus developmental cites Epictetus Discourses + Enchiridion
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "work_epictetus_discourses", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "work_epictetus_enchiridion", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "passage_epictetus_disc_i_1_1", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "passage_epictetus_disc_i_1_23", "cites_primary_source"),

    # Cylinder in later fate theory — Nemesius via work nodes if exist (skip if not)
    # Master argument cites
    _edge("argument_bobzien_2001_b1_master_argument_reconstruction", "passage_cicero_fat_12", "cites_primary_source"),
    _edge("argument_bobzien_2001_b1_master_argument_reconstruction", "passage_cicero_fat_13", "cites_primary_source"),
])


# =============================================================================
# 7. INFLUENCE CHAINS — Bobzien <-> Frede (supervisor) + later disagreements
# =============================================================================
NEW_EDGES.extend([
    # Michael Frede influences Bobzien (DPhil supervisor + 1980 paper on cause)
    _edge("person_frede_michael_1940_2007", BOBZIEN_PERSON_ID, "influences",
          confidence=0.9,
          note="Michael Frede supervised Bobzien's DPhil; 'The Original Notion of Cause' (1980) supplies methodological frame"),
    _edge(BOBZIEN_PERSON_ID, "person_frede_michael_1940_2007", "influenced_by",
          confidence=0.9,
          note="DPhil supervision + methodological influence on Stoic causation"),

    # Bobzien engages with Long & Sedley (Hellenistic Philosophers)
    _edge(BOBZIEN_PERSON_ID, "scholarly_work_long_sedley_1987_hellenistic_philosophers", "engages_with",
          confidence=0.9,
          note="Bobzien 2001 frequently disagrees with L&S on modal + compatibilist details"),

    # Bobzien resists Dihle 1982 — Dihle person/publication may not exist, leave for Dihle agent
])


# =============================================================================
# 8. INTERNAL CROSS-LINKS BETWEEN BOBZIEN ARGUMENTS
# =============================================================================
NEW_EDGES.extend([
    # The 'no free will' thesis is supported by the eph hemin distinction
    _edge("argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided", "argument_bobzien_2001_b1_no_free_will_in_stoa", "supports"),
    _edge("argument_bobzien_2001_b1_critique_anachronistic_freewill", "argument_bobzien_2001_b1_no_free_will_in_stoa", "supports"),
    _edge("argument_bobzien_2001_b1_rise_fall_freedom_problem", "argument_bobzien_2001_b1_no_free_will_in_stoa", "supports"),
    _edge("argument_bobzien_2001_b1_epictetus_developmental_freedom", "argument_bobzien_2001_b1_no_free_will_in_stoa", "supports"),

    # Cylinder reconstruction supports compatibilism reconstruction
    _edge("argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "argument_bobzien_2001_b1_synkatathesis_psychology_action", "supports"),

    # Pneumatic causation supports cylinder analogy
    _edge("argument_bobzien_2001_b1_pneumatic_causation_model", "argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "supports"),

    # Master Argument is the foil for the modal system
    _edge("argument_bobzien_2001_b1_chrysippean_modal_system", "argument_bobzien_2001_b1_master_argument_reconstruction", "responds_to"),

    # PHILOPATOR extends Chrysippean compatibilism
    _edge("argument_bobzien_2001_b1_philopator_late_compatibilism", "argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "extends"),
    _edge("argument_bobzien_2001_b1_cylinder_in_later_fate_theory", "argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction", "extends"),
])


# =============================================================================
# 9. CONCEPT-LEVEL EDGES — new concepts link to ancient persons + concepts
# =============================================================================
NEW_EDGES.extend([
    # Chrysippean compatibilism concept
    _edge("concept_chrysippean_compatibilism_bobzien", "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("concept_chrysippean_compatibilism_bobzien", "concept_cylinder_analogy_chrysippus_e5f6g7h8", "related_to"),
    _edge("concept_chrysippean_compatibilism_bobzien", "concept_synkatathesis_stoic_assent", "related_to"),
    _edge("concept_chrysippean_compatibilism_bobzien", "concept_eph_hemin_one_sided_causative", "related_to"),

    # Pneumatic causation
    _edge("concept_pneumatic_causation_stoic_bobzien", "concept_sympatheia_stoic", "related_to"),
    _edge("concept_pneumatic_causation_stoic_bobzien", "concept_heimarmene_fate_stoics_j0k1l2m3", "related_to"),

    # Fate Principle
    _edge("concept_fate_principle_bobzien", "concept_heimarmene_fate_stoics_j0k1l2m3", "related_to"),

    # PHILOPATOR compatibilism
    _edge("concept_philopator_compatibilism_bobzien", "concept_chrysippean_compatibilism_bobzien", "extends"),
    _edge("concept_philopator_compatibilism_bobzien", "concept_eph_hemin_one_sided_causative", "related_to"),
])
