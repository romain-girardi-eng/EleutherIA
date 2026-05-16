"""Amand B8 — NEW_EDGES list.

Allowed relations (source/target types per knowledge graph/ontology/edge_types.json):

  authored_by         : src argument/passage/publication/quote/synthesis/work -> tgt person
  wrote               : src person -> tgt work
  contains            : src argument/concept/debate/quote/work/source_collection -> tgt
                        argument/argument_framework/concept/debate/passage/text_fragment/work
                        (NB: synthesis is NOT allowed as source)
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
  has_member          : src school -> tgt person
  member_of           : src concept/person/work -> tgt group/school
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
# 1. AUTHORSHIP (wrote / authored_by) — for new persons and works
# =============================================================================
NEW_EDGES.extend([
    # Lucian
    _edge("person_lucian_samosata_c125_180", "work_lucian_apologia", "wrote"),
    _edge("person_lucian_samosata_c125_180", "work_lucian_dialogues_mortuorum", "wrote"),
    _edge("person_lucian_samosata_c125_180", "work_lucian_iuppiter_confutatus", "wrote"),
    _edge("person_lucian_samosata_c125_180", "work_lucian_vita_demonactis", "wrote"),
    _edge("work_lucian_apologia", "person_lucian_samosata_c125_180", "authored_by"),
    _edge("work_lucian_dialogues_mortuorum", "person_lucian_samosata_c125_180", "authored_by"),
    _edge("work_lucian_iuppiter_confutatus", "person_lucian_samosata_c125_180", "authored_by"),
    _edge("work_lucian_vita_demonactis", "person_lucian_samosata_c125_180", "authored_by"),
    # Oinomaos
    _edge("person_oinomaos_gadara_2c_ce", "work_oinomaos_goeton_phora", "wrote"),
    _edge("work_oinomaos_goeton_phora", "person_oinomaos_gadara_2c_ce", "authored_by"),
    # Diogenes Oinoanda
    _edge("person_diogenes_oinoanda_c200_ce", "work_diogenes_oinoanda_inscription", "wrote"),
    _edge("work_diogenes_oinoanda_inscription", "person_diogenes_oinoanda_c200_ce", "authored_by"),
    # Diogenianus
    _edge("person_diogenianus_epicurean_2c_ce", "work_diogenianus_peri_heimarmenes", "wrote"),
    _edge("work_diogenianus_peri_heimarmenes", "person_diogenianus_epicurean_2c_ce", "authored_by"),
    # Hierocles — Peri pronoias work-shell
    _edge("person_hierocles_of_alexandria_1p6q8s54", "work_hierocles_peri_pronoias", "wrote"),
    _edge("work_hierocles_peri_pronoias", "person_hierocles_of_alexandria_1p6q8s54", "authored_by"),
])


# =============================================================================
# 2. SYNTHESIS authorship by Amand (via authored_by → scholar node)
# =============================================================================
SYNTHESIS_IDS = [
    # Intro §I
    "synthesis_amand1945_intro_chaldean_origin_fatalism",
    "synthesis_amand1945_intro_presocratics_create_heimarmene_concept",
    "synthesis_amand1945_intro_plato_aristotle_partial_determinism",
    "synthesis_amand1945_intro_stoic_integral_fatalism",
    "synthesis_amand1945_intro_hellenistic_astrological_diffusion",
    "synthesis_amand1945_intro_astrologers_pragmatic_responses",
    "synthesis_amand1945_intro_stoic_joyful_resignation",
    "synthesis_amand1945_intro_christian_baptismal_liberation",
    # Lucian
    "synthesis_amand1945_lucian_sophist_satirist_carneadean_topos",
    "synthesis_amand1945_lucian_epicurean_2c_revival",
    # Oinomaos
    "synthesis_amand1945_oinomaos_cynic_carneadean_libre_adaptation",
    "synthesis_amand1945_oinomaos_julian_pagan_critique",
    # Neoplatonists
    "synthesis_amand1945_plotinus_non_witness_explanation",
    "synthesis_amand1945_neoplatonic_school_no_carneadean_use",
    "synthesis_amand1945_hierocles_bizarre_carneadean_inversion",
]
for sid in SYNTHESIS_IDS:
    NEW_EDGES.append(_edge(sid, "scholar_amand_de_mendieta_e", "authored_by"))


# =============================================================================
# 3. SCHOLARLY DISCUSSION — syntheses discuss argument/concept/person/work/school
# =============================================================================
NEW_EDGES.extend([
    # Intro §I.I — Chaldean origin
    _edge("synthesis_amand1945_intro_chaldean_origin_fatalism",
          "concept_heimarmene_astrologica_amand", "discusses"),

    # Intro §I.II — Pre-Socratics
    _edge("synthesis_amand1945_intro_presocratics_create_heimarmene_concept",
          "concept_heimarmene_fate_stoics_j0k1l2m3", "discusses"),

    # Intro §I.III — Plato/Aristotle partial determinism
    _edge("synthesis_amand1945_intro_plato_aristotle_partial_determinism",
          "person_plato_428_348bce_a1b2c3d4", "discusses"),
    _edge("synthesis_amand1945_intro_plato_aristotle_partial_determinism",
          "person_aristotle_384_322bce_c2d4f6a8", "discusses"),

    # Intro §I.IV — Stoic integral fatalism
    _edge("synthesis_amand1945_intro_stoic_integral_fatalism",
          "person_zeno_citium_334_262bce", "discusses"),
    _edge("synthesis_amand1945_intro_stoic_integral_fatalism",
          "person_cleanthes_assos_330_230bce", "discusses"),
    _edge("synthesis_amand1945_intro_stoic_integral_fatalism",
          "person_chrysippus_280_206bce_i9j0k1l2", "discusses"),
    _edge("synthesis_amand1945_intro_stoic_integral_fatalism",
          "person_posidonius_apameia_135_51bce", "discusses"),

    # Intro §I.V — Hellenistic astrological diffusion
    _edge("synthesis_amand1945_intro_hellenistic_astrological_diffusion",
          "concept_heimarmene_astrologica_amand", "discusses"),

    # Intro §I.VII — Astrologers' pragmatic responses
    _edge("synthesis_amand1945_intro_astrologers_pragmatic_responses",
          "concept_heimarmene_astrologica_amand", "discusses"),

    # Intro §I.VIII — Stoic resignation
    _edge("synthesis_amand1945_intro_stoic_joyful_resignation",
          "person_cleanthes_assos_330_230bce", "discusses"),

    # Intro §I.X — Christian baptismal liberation
    _edge("synthesis_amand1945_intro_christian_baptismal_liberation",
          "concept_heimarmene_astrologica_amand", "discusses"),

    # Lucian synthesis
    _edge("synthesis_amand1945_lucian_sophist_satirist_carneadean_topos",
          "person_lucian_samosata_c125_180", "discusses"),
    _edge("synthesis_amand1945_lucian_sophist_satirist_carneadean_topos",
          "argument_lucian_zeus_confutatus_carneadean_topos", "discusses"),
    _edge("synthesis_amand1945_lucian_sophist_satirist_carneadean_topos",
          "argument_carneadean_general_theme_amand1945", "discusses"),

    # Lucian — Epicurean 2c revival
    _edge("synthesis_amand1945_lucian_epicurean_2c_revival",
          "person_diogenes_oinoanda_c200_ce", "discusses"),
    _edge("synthesis_amand1945_lucian_epicurean_2c_revival",
          "person_diogenianus_epicurean_2c_ce", "discusses"),

    # Oinomaos syntheses
    _edge("synthesis_amand1945_oinomaos_cynic_carneadean_libre_adaptation",
          "person_oinomaos_gadara_2c_ce", "discusses"),
    _edge("synthesis_amand1945_oinomaos_cynic_carneadean_libre_adaptation",
          "argument_oinomaos_carneadean_libre_adaptation", "discusses"),
    _edge("synthesis_amand1945_oinomaos_cynic_carneadean_libre_adaptation",
          "argument_carneadean_general_theme_amand1945", "discusses"),
    _edge("synthesis_amand1945_oinomaos_julian_pagan_critique",
          "person_oinomaos_gadara_2c_ce", "discusses"),

    # Neoplatonist syntheses
    _edge("synthesis_amand1945_plotinus_non_witness_explanation",
          "person_plotinus_d270", "discusses"),
    _edge("synthesis_amand1945_plotinus_non_witness_explanation",
          "concept_plotinian_intellectual_eph_hemin", "discusses"),
    _edge("synthesis_amand1945_plotinus_non_witness_explanation",
          "argument_carneadean_general_theme_amand1945", "discusses"),
    _edge("synthesis_amand1945_neoplatonic_school_no_carneadean_use",
          "person_porphyry", "discusses"),
    _edge("synthesis_amand1945_neoplatonic_school_no_carneadean_use",
          "person_iamblichus_d325", "discusses"),
    _edge("synthesis_amand1945_neoplatonic_school_no_carneadean_use",
          "person_proclus_412_485ce_f3d8b2a9", "discusses"),
    _edge("synthesis_amand1945_hierocles_bizarre_carneadean_inversion",
          "person_hierocles_of_alexandria_1p6q8s54", "discusses"),
    _edge("synthesis_amand1945_hierocles_bizarre_carneadean_inversion",
          "argument_hierocles_carneadean_inversion_for_providential_heimarmene", "discusses"),
])


# =============================================================================
# 4. ARGUMENT CONTAINMENT IN WORKS — work contains argument (where ontology
#    permits). Also: arguments cites_primary_source -> work-shells
# =============================================================================
NEW_EDGES.extend([
    # Iuppiter confutatus contains Lucian's Carneadean argument
    _edge("work_lucian_iuppiter_confutatus",
          "argument_lucian_zeus_confutatus_carneadean_topos", "contains"),
    # Goeton phora contains Oinomaos's Carneadean adaptation
    _edge("work_oinomaos_goeton_phora",
          "argument_oinomaos_carneadean_libre_adaptation", "contains"),
    # Diogenes Oinoanda inscription contains anti-heimarmene argument
    _edge("work_diogenes_oinoanda_inscription",
          "argument_diogenes_oinoanda_no_heimarmene_fragm_xxxiii", "contains"),
    # Hierocles Peri pronoias contains the bizarre carneadean inversion
    _edge("work_hierocles_peri_pronoias",
          "argument_hierocles_carneadean_inversion_for_providential_heimarmene", "contains"),
])


# =============================================================================
# 5. CITES_PRIMARY_SOURCE — args cite the works they live in (work-shells)
# =============================================================================
NEW_EDGES.extend([
    _edge("argument_lucian_zeus_confutatus_carneadean_topos",
          "work_lucian_iuppiter_confutatus", "cites_primary_source",
          confidence=0.95),
    _edge("argument_oinomaos_carneadean_libre_adaptation",
          "work_oinomaos_goeton_phora", "cites_primary_source",
          confidence=0.95),
    _edge("argument_diogenes_oinoanda_no_heimarmene_fragm_xxxiii",
          "work_diogenes_oinoanda_inscription", "cites_primary_source",
          confidence=0.95),
    _edge("argument_hierocles_carneadean_inversion_for_providential_heimarmene",
          "work_hierocles_peri_pronoias", "cites_primary_source",
          confidence=0.95),
])


# =============================================================================
# 6. EVIDENCED_BY — Plotinian arguments and concepts grounded in Plotinus passages
#    (1367 Plotinus passages available; we use the most relevant ones —
#     III.1 Peri Heimarmenes, IV.4.39 sympatheia, VI.8 will, II.3 stars)
# =============================================================================
NEW_EDGES.extend([
    # Plotinus' freedom argument grounded in VI.8 + II.3.9
    _edge("argument_plotinus_freedom_argument_7c561972",
          "passage_plotinus_vi_8_2", "evidenced_by"),
    _edge("argument_plotinus_freedom_argument_7c561972",
          "passage_plotinus_vi_8_6", "evidenced_by"),
    _edge("argument_plotinus_freedom_argument_7c561972",
          "passage_plotinus_vi_8_8", "evidenced_by"),
    _edge("argument_plotinus_freedom_argument_7c561972",
          "passage_plotinus_iii_1_4", "evidenced_by"),
    _edge("argument_plotinus_freedom_argument_7c561972",
          "passage_plotinus_iii_1_5", "evidenced_by"),
    # Plotinian intellectual eph-hēmin concept grounded in same loci
    _edge("concept_plotinian_intellectual_eph_hemin",
          "passage_plotinus_vi_8_2", "evidenced_by"),
    _edge("concept_plotinian_intellectual_eph_hemin",
          "passage_plotinus_vi_8_6", "evidenced_by"),
    _edge("concept_plotinian_intellectual_eph_hemin",
          "passage_plotinus_vi_8_8", "evidenced_by"),
    _edge("concept_plotinian_intellectual_eph_hemin",
          "passage_plotinus_iii_1_8", "evidenced_by"),
    _edge("concept_plotinian_intellectual_eph_hemin",
          "passage_plotinus_iii_1_9", "evidenced_by"),
    # Plotinus universal sympatheia / mantike basis — concept_sympatheia_universal_posidonius_nyssa
    _edge("concept_sympatheia_universal_posidonius_nyssa",
          "passage_plotinus_iii_1_7", "evidenced_by"),
])


# =============================================================================
# 7. INFLUENCES — Carneades influences Lucian/Oinomaos/Diogenianus
#    (Amand-asserted filiations; confidence 0.5-0.7 per plan R4)
# =============================================================================
NEW_EDGES.extend([
    _edge("person_carneades_214_129bce_l2m3n4o5",
          "person_lucian_samosata_c125_180", "influences",
          confidence=0.6,
          amand_qualification="topos morale antifataliste tombé dans le domaine public — pas filiation directe selon Amand"),
    _edge("person_carneades_214_129bce_l2m3n4o5",
          "person_oinomaos_gadara_2c_ce", "influences",
          confidence=0.7,
          amand_qualification="libre adaptation du τόπος carnéadien selon Amand"),
    _edge("person_carneades_214_129bce_l2m3n4o5",
          "person_diogenianus_epicurean_2c_ce", "influences",
          confidence=0.7,
          amand_qualification="dépendance très nette d'après Amand — comparaison souhaitée avec De divinatione de Cicéron"),
    _edge("person_carneades_214_129bce_l2m3n4o5",
          "person_diogenes_oinoanda_c200_ce", "influences",
          confidence=0.5,
          amand_qualification="probable mais Amand suggère écho via Épicure plutôt que Carnéade direct"),
    _edge("person_carneades_214_129bce_l2m3n4o5",
          "person_demonax_cyprus_2c_ce", "influences",
          confidence=0.5,
          amand_qualification="dilemme mantique/fatalisme — topos diffusé, source précise non identifiable"),
])


# =============================================================================
# 8. INFLUENCES — Neoplatonic chain Plotinus → Porphyry → Iamblichus → Proclus
# =============================================================================
NEW_EDGES.extend([
    _edge("person_plotinus_d270",
          "person_porphyry", "influences",
          confidence=0.98,
          relation_amand="maître direct (Porphyre disciple à Rome 263-269)"),
    _edge("person_porphyry",
          "person_iamblichus_d325", "influences",
          confidence=0.9,
          relation_amand="enseignement néoplatonicien transmis via Anatolius selon Eunape Vit. Soph."),
    _edge("person_iamblichus_d325",
          "person_proclus_412_485ce_f3d8b2a9", "influences",
          confidence=0.85,
          relation_amand="lignée néoplatonicienne syrienne via Syrianos selon Marinus Vit. Procli"),
    # Hierocles — Alexandrian Neoplatonist, influenced more by Origen than by Plotinian chain
    _edge("person_plotinus_d270",
          "person_hierocles_of_alexandria_1p6q8s54", "influences",
          confidence=0.7,
          relation_amand="Hiéroclès reste plutôt en deçà du plotinisme — 'platonisme moyen pré-plotinien' selon Praechter cité par Amand"),
])


# =============================================================================
# 9. PRECEDES — work-level chronological chain (where useful)
# =============================================================================
NEW_EDGES.extend([
    _edge("work_plotinus_enn_iii_1", "work_porphyry_vita_plotini", "precedes"),
    _edge("work_porphyry_vita_plotini", "work_iamblichus_de_anima", "precedes"),
    _edge("work_iamblichus_de_anima", "work_proclus_tria_opuscula_c9a8e4b3", "precedes"),
    _edge("work_proclus_tria_opuscula_c9a8e4b3", "work_hierocles_peri_pronoias", "precedes"),
    # Lucian → Oinomaos contemporary chain
    _edge("work_lucian_iuppiter_confutatus", "work_oinomaos_goeton_phora", "precedes"),
])


# =============================================================================
# 10. INFLUENCED_BY — Hierocles influenced by Origen (Amand's key claim)
# =============================================================================
NEW_EDGES.extend([
    _edge("person_hierocles_of_alexandria_1p6q8s54",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "influenced_by",
          confidence=0.7,
          amand_qualification="proximité doctrinale notée par Amand — possibility of direct contact via Alexandrian school"),
])


# =============================================================================
# 11. CRITIQUES — Lucian/Oinomaos/Diogenianus critique Chrysippus's fatalism
# =============================================================================
NEW_EDGES.extend([
    _edge("argument_lucian_zeus_confutatus_carneadean_topos",
          "person_chrysippus_280_206bce_i9j0k1l2", "critiques"),
    _edge("argument_oinomaos_carneadean_libre_adaptation",
          "person_chrysippus_280_206bce_i9j0k1l2", "critiques"),
    _edge("argument_diogenes_oinoanda_no_heimarmene_fragm_xxxiii",
          "person_chrysippus_280_206bce_i9j0k1l2", "critiques"),
])


# =============================================================================
# 12. RESPONDS_TO — Carneadean arguments answer Stoic fatalism
# =============================================================================
NEW_EDGES.extend([
    _edge("argument_lucian_zeus_confutatus_carneadean_topos",
          "concept_heimarmene_fate_stoics_j0k1l2m3", "responds_to"),
    _edge("argument_oinomaos_carneadean_libre_adaptation",
          "concept_heimarmene_fate_stoics_j0k1l2m3", "responds_to"),
])


# =============================================================================
# 13. INTERPRETS — Hierocles interprets Carneadean topos in a new key
# =============================================================================
NEW_EDGES.extend([
    _edge("argument_hierocles_carneadean_inversion_for_providential_heimarmene",
          "argument_carneadean_general_theme_amand1945", "interprets"),
])


# =============================================================================
# 14. PART_OF — work-shells belong to Plotinus/Porphyry/etc. corpora
# =============================================================================
# (No source_collection nodes for Lucian/Oinomaos — keep simple)


# =============================================================================
# 15. MEMBER_OF — Oinomaos & Demonax members of Cynic school (if school node exists)
# =============================================================================
# Check via apply script — will skip if school node missing.
# Both Cynics; existing school node IDs vary — best skipped here, included
# only if school_cynics already exists in KG.
# (Conservative: emit candidates; apply script will skip-missing if absent)
NEW_EDGES.extend([
    # Suspected school node (school_cynics or similar). Apply script will
    # report SKIP-NO-TGT if absent — non-blocking.
])


# =============================================================================
# Optional: Hierocles links to Origen-related Origenist Providence argument
# =============================================================================
# argument_proclus_levels_of_providence is the proclus argument; we link
# Hierocles's inversion as RESPONDS_TO Origen's prescience argument if it exists
# (skip-missing safe)
NEW_EDGES.extend([
    _edge("synthesis_amand1945_hierocles_bizarre_carneadean_inversion",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses",
          confidence=0.8,
          amand_qualification="parallel between Hierocles and Origen on providential pedagogy"),
])
