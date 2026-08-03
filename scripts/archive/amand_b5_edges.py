"""B5 NEW_EDGES — ~70 edges Amand 1945 sur Origène.

Categories :
1. evidenced_by — sub-args → SC132 CC + SC268 Princ. passages (ANCHORING)
2. cites_primary_source — sub-args → work-shells (evidence_pending)
3. influences / transmits_to / precedes — filiations Carnéade → Origène + Origène → patristiques
4. critiqued_by — adversaires d'Origène
5. influenced_by — école / sources philosophiques d'Origène
6. creates — Origène → arguments (direction active per ontology)
7. contains — enveloppes → sub-args
8. discusses — sub-args → concepts
9. refines — sub-args §IV → arguments_carneadean_*_amand1945
"""
from __future__ import annotations

from amand_b5_utils import make_edge  # type: ignore

NEW_EDGES: list[dict] = []

ORIGEN = "person_origen_alexandria_185_254ce_s9t0u1v2"
CARNEADES = "person_carneades_214_129bce_l2m3n4o5"
CLITOMACHUS = "person_clitomachus_of_carthage_7l2m4o10"

# ============================================================================
# 1. evidenced_by — sub-args → SC132/SC268 passages (ANCHORING CRITIQUE)
# ============================================================================

# §II : libre arbitre dogme — ANCHORED Princ. III.1
for src in [
    "argument_origen_witness_freewill_dogma_status_amand1945",
    "argument_origen_witness_possibilitas_utriusque_amand1945",
    "argument_origen_witness_synkatathesis_locus_amand1945",
]:
    for tgt in ["sc268_origenes_peri_archon_iii_chap1", "sc268_origenes_peri_archon_iii_chap1_en"]:
        NEW_EDGES.append(make_edge(src=src, tgt=tgt, relation="evidenced_by", confidence=0.9))

# Update node also evidenced (ancrage de l'argument existant Phase 9 enrichi)
for tgt in ["sc268_origenes_peri_archon_iii_chap1", "sc268_origenes_peri_archon_iii_chap1_en"]:
    NEW_EDGES.append(make_edge(
        src="argument_origens_de_principiis_argument_for_free_will_93d043fc",
        tgt=tgt, relation="evidenced_by", confidence=0.9,
        md={"note": "B5 enrichment Amand 1945 — anchor for the Phase 9 De Principiis argument node"},
    ))

# §III : Argos Logos reuse from CC II.20 — ANCHORED
for tgt in ["sc132_origenes_contra_celsum_ii_par20", "sc132_origenes_contra_celsum_ii_par20_en"]:
    NEW_EDGES.append(make_edge(
        src="argument_origen_witness_diss_argos_logos_refutation_amand1945",
        tgt=tgt, relation="evidenced_by", confidence=0.9,
        md={"note": "Philocalie 23.12-13 = excerpt CC II.20"},
    ))

# §I.1 : double polarity Bible-Platon — anchored on CC I.2 (dialectique + Origène débiteur des hommes cultivés)
for tgt in ["sc132_origenes_contra_celsum_i_par2", "sc132_origenes_contra_celsum_i_par2_en"]:
    NEW_EDGES.append(make_edge(
        src="argument_origen_witness_personality_double_polarity_amand1945",
        tgt=tgt, relation="evidenced_by", confidence=0.7,
        md={"note": "Amand cite CC I.2 dans son exposé sur dialectique et exégèse — ancrage indirect"},
    ))


# ============================================================================
# 2. cites_primary_source — sub-args → work-shells (evidence_pending)
# ============================================================================

# Phil. 23 (Philocalia work-shell)
for src in [
    "argument_origen_witness_diss_problem1_prescience_amand1945",
    "argument_origen_witness_diss_problem2_signs_not_causes_amand1945",
    "argument_origen_witness_diss_problem3_human_ignorance_amand1945",
    "argument_origen_witness_diss_problem4_angelic_knowledge_amand1945",
    "argument_origen_witness_diss_part3_pseudo_clementine_amand1945",
    "argument_origen_witness_diss_precession_equinoxes_amand1945",
    "argument_origen_witness_carneades_transposition_praise_blame_amand1945",
    "argument_origen_witness_carneades_transposition_theological_consequences_amand1945",
    "argument_origen_witness_carneades_transposition_god_as_evil_amand1945",
    "argument_origen_witness_carneades_transposition_prayer_useless_amand1945",
    "argument_origen_witness_carneades_transposition_gnostic_excursus_amand1945",
]:
    NEW_EDGES.append(make_edge(
        src=src, tgt="work_origen_philocalia",
        relation="cites_primary_source", confidence=0.85,
        md={"evidence_pending": True, "note": "Philocalia ch. 23 partial source. Absent du corpus KG"},
    ))

# Princ. (work-shell preexistence + double freedom)
for src in [
    "argument_origen_witness_preexistence_souls_amand1945",
    "argument_origen_witness_double_freedom_amand1945",
    "argument_origen_witness_personality_anti_unilateral_amand1945",
]:
    NEW_EDGES.append(make_edge(
        src=src, tgt="work_de_principiis_origen_230s_v2w3x4y5",
        relation="cites_primary_source", confidence=0.85,
        md={"evidence_pending": True, "note": "Princ. I/II/III.6 outside SC268 corpus coverage (III.1 + IV.1-3 only)"},
    ))

# CC IV.3 + VIII.15 + De Oratione 29 (virtue voluntary essence)
NEW_EDGES.append(make_edge(
    src="argument_origen_witness_virtue_voluntary_essence_amand1945",
    tgt="work_origen_contra_celsum_sc132",
    relation="cites_primary_source", confidence=0.85,
    md={"evidence_pending": True, "note": "CC IV.3 + VIII.15 outside SC132 corpus coverage (books I-II only)"},
))
NEW_EDGES.append(make_edge(
    src="argument_origen_witness_virtue_voluntary_essence_amand1945",
    tgt="work_origen_de_oratione",
    relation="cites_primary_source", confidence=0.75,
    md={"evidence_pending": True, "note": "De Oratione 29.13-15 outside KG corpus (only 2 passages available)"},
))


# ============================================================================
# 3. influences / transmits_to / precedes
# ============================================================================

NEW_EDGES.append(make_edge(
    src=CARNEADES, tgt=ORIGEN,
    relation="influences", confidence=0.7,
    md={
        "filiation_amand_asserted": True,
        "filiation_chain": "Carneades (oral) → Clitomachus (written) → Cicero (Academica, De NatDeor) → Origen",
        "note": "Reconstruction d'Amand (synthesis_amand1945_origen_carneadean_filiation). Indirect, via Cicéron probable.",
    },
))

NEW_EDGES.append(make_edge(
    src=CLITOMACHUS, tgt=ORIGEN,
    relation="precedes", confidence=0.65,
    md={
        "filiation_amand_asserted": True,
        "note": "Médiateur écrit de Carnéade — pas d'évidence directe de lecture par Origène, transmission via Cicéron probable",
    },
))

# Origène influence subsequent patristics (transmission lineage)
NEW_EDGES.append(make_edge(
    src=ORIGEN, tgt="person_eusebius_caesarea_d339",
    relation="influences", confidence=0.9,
    md={"note": "Eusèbe transcrit Phil. 23 dans Préparation Évangélique VI.11.1-81 (Dindorf p. 324-343)", "amand_transmission_chain": True},
))
NEW_EDGES.append(make_edge(
    src=ORIGEN, tgt="person_basil_great_d379",
    relation="influences", confidence=0.95,
    md={"note": "Basile compilateur de la Philocalie (avec Grégoire Naz.). Démarque Hexaéméron VI.5 sur Origène Phil. 23.18", "amand_transmission_chain": True},
))
NEW_EDGES.append(make_edge(
    src=ORIGEN, tgt="person_methodius_olympus_d311",
    relation="influences", confidence=0.85,
    md={"note": "Méthode d'Olympe successeur direct + ch. VI Amand 1945", "amand_transmission_chain": True},
))
NEW_EDGES.append(make_edge(
    src=ORIGEN, tgt="person_gregory_nyssa_d395",
    relation="influences", confidence=0.85,
    md={"note": "Grégoire de Nysse héritier théologique majeur d'Origène", "amand_transmission_chain": True},
))

# CAFMA précede transposition method
NEW_EDGES.append(make_edge(
    src="argument_cafma_carneades_m3n4o5p6",
    tgt="argument_origen_witness_carneades_transposition_theological_method_amand1945",
    relation="precedes", confidence=0.85,
    md={"note": "Carneadean Anti-Fatalist Moral Argumentation = matériau philosophique transposé théologiquement par Origène"},
))


# ============================================================================
# 4. critiqued_by — adversaires d'Origène
# ============================================================================

for tgt in [
    "person_chrysippus_280_206bce_i9j0k1l2",
    "person_epicurus_341_270bce_j0k1l2m3",
    "person_marcion_sinope_2c_ce",
    "person_valentinus_gnostic_2c_ce",
]:
    NEW_EDGES.append(make_edge(
        src=ORIGEN, tgt=tgt,
        relation="critiques", confidence=0.85,
        md={"note": f"Origène critique {tgt.split('_')[1]} dans Contre Celse + Philocalie"},
    ))


# ============================================================================
# 5. influenced_by — sources philosophiques d'Origène (Amand-asserted)
# ============================================================================

for tgt in [
    "school_middle_platonism",
    "school_stoics",
    "school_peripatetics",
    "person_plato_428_348bce_a1b2c3d4",
    "person_chrysippus_280_206bce_i9j0k1l2",
    "person_aristotle_384_322bce_c2d4f6a8",
]:
    conf = 0.9 if tgt == "school_middle_platonism" else 0.8
    NEW_EDGES.append(make_edge(
        src=ORIGEN, tgt=tgt,
        relation="influenced_by", confidence=conf,
        md={"amand_asserted": True, "amand_locus": "Livre II Ch. V §I.3 (p. 290-296)"},
    ))


# ============================================================================
# 6. creates — Origène → arguments (direction active)
# ============================================================================

ORIGEN_CREATED_ARGS = [
    # Enveloppes
    "argument_origen_witness_personality_envelope_amand1945",
    "argument_origen_witness_freewill_doctrine_envelope_amand1945",
    "argument_origen_witness_antiastrological_dissertation_envelope_amand1945",
    "argument_origen_witness_carneadean_transposition_envelope_amand1945",
    # §I subs (3)
    "argument_origen_witness_personality_double_polarity_amand1945",
    "argument_origen_witness_personality_anti_unilateral_amand1945",
    "argument_origen_witness_personality_christian_gnosis_amand1945",
    # §I.3 subs (4)
    "argument_origen_witness_platonism_influence_amand1945",
    "argument_origen_witness_aristotelism_influence_amand1945",
    "argument_origen_witness_stoicism_influence_amand1945",
    "argument_origen_witness_middle_platonism_amand1945",
    # §II subs (5)
    "argument_origen_witness_freewill_dogma_status_amand1945",
    "argument_origen_witness_preexistence_souls_amand1945",
    "argument_origen_witness_possibilitas_utriusque_amand1945",
    "argument_origen_witness_synkatathesis_locus_amand1945",
    "argument_origen_witness_double_freedom_amand1945",
    # §III subs (8)
    "argument_origen_witness_antiastrology_moral_attack_amand1945",
    "argument_origen_witness_diss_problem1_prescience_amand1945",
    "argument_origen_witness_diss_argos_logos_refutation_amand1945",
    "argument_origen_witness_diss_problem2_signs_not_causes_amand1945",
    "argument_origen_witness_diss_problem3_human_ignorance_amand1945",
    "argument_origen_witness_diss_problem4_angelic_knowledge_amand1945",
    "argument_origen_witness_diss_part3_pseudo_clementine_amand1945",
    "argument_origen_witness_diss_precession_equinoxes_amand1945",
    # §IV subs (7)
    "argument_origen_witness_carneades_transposition_praise_blame_amand1945",
    "argument_origen_witness_carneades_transposition_theological_consequences_amand1945",
    "argument_origen_witness_carneades_transposition_god_as_evil_amand1945",
    "argument_origen_witness_carneades_transposition_prayer_useless_amand1945",
    "argument_origen_witness_carneades_transposition_gnostic_excursus_amand1945",
    "argument_origen_witness_carneades_transposition_theological_method_amand1945",
    "argument_origen_witness_virtue_voluntary_essence_amand1945",
]

for tgt in ORIGEN_CREATED_ARGS:
    NEW_EDGES.append(make_edge(
        src=ORIGEN, tgt=tgt,
        relation="creates", confidence=0.95,
        md={"note": "Amand 1945 B5 attributes argument to Origen as expressed in his works (paraphrase Amand)"},
    ))


# ============================================================================
# 7. contains — enveloppes → sub-args
# ============================================================================

ENVELOPES = {
    "argument_origen_witness_personality_envelope_amand1945": [
        "argument_origen_witness_personality_double_polarity_amand1945",
        "argument_origen_witness_personality_anti_unilateral_amand1945",
        "argument_origen_witness_personality_christian_gnosis_amand1945",
        "argument_origen_witness_platonism_influence_amand1945",
        "argument_origen_witness_aristotelism_influence_amand1945",
        "argument_origen_witness_stoicism_influence_amand1945",
        "argument_origen_witness_middle_platonism_amand1945",
    ],
    "argument_origen_witness_freewill_doctrine_envelope_amand1945": [
        "argument_origen_witness_freewill_dogma_status_amand1945",
        "argument_origen_witness_preexistence_souls_amand1945",
        "argument_origen_witness_possibilitas_utriusque_amand1945",
        "argument_origen_witness_synkatathesis_locus_amand1945",
        "argument_origen_witness_double_freedom_amand1945",
    ],
    "argument_origen_witness_antiastrological_dissertation_envelope_amand1945": [
        "argument_origen_witness_antiastrology_moral_attack_amand1945",
        "argument_origen_witness_diss_problem1_prescience_amand1945",
        "argument_origen_witness_diss_argos_logos_refutation_amand1945",
        "argument_origen_witness_diss_problem2_signs_not_causes_amand1945",
        "argument_origen_witness_diss_problem3_human_ignorance_amand1945",
        "argument_origen_witness_diss_problem4_angelic_knowledge_amand1945",
        "argument_origen_witness_diss_part3_pseudo_clementine_amand1945",
        "argument_origen_witness_diss_precession_equinoxes_amand1945",
    ],
    "argument_origen_witness_carneadean_transposition_envelope_amand1945": [
        "argument_origen_witness_carneades_transposition_praise_blame_amand1945",
        "argument_origen_witness_carneades_transposition_theological_consequences_amand1945",
        "argument_origen_witness_carneades_transposition_god_as_evil_amand1945",
        "argument_origen_witness_carneades_transposition_prayer_useless_amand1945",
        "argument_origen_witness_carneades_transposition_gnostic_excursus_amand1945",
        "argument_origen_witness_carneades_transposition_theological_method_amand1945",
        "argument_origen_witness_virtue_voluntary_essence_amand1945",
    ],
}

for envelope, subs in ENVELOPES.items():
    for sub in subs:
        NEW_EDGES.append(make_edge(
            src=envelope, tgt=sub,
            relation="contains", confidence=1.0,
        ))


# ============================================================================
# 8. discusses — sub-args → concepts
# ============================================================================

DISCUSSES = [
    ("argument_origen_witness_freewill_dogma_status_amand1945", "concept_autexousion_christian_freedom_u1v2w3x4"),
    ("argument_origen_witness_possibilitas_utriusque_amand1945", "concept_logikon_zoon_origen_amand1945"),
    ("argument_origen_witness_possibilitas_utriusque_amand1945", "concept_autexousion_christian_freedom_u1v2w3x4"),
    ("argument_origen_witness_synkatathesis_locus_amand1945", "concept_synkatathesis_stoic_assent"),
    ("argument_origen_witness_synkatathesis_locus_amand1945", "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7"),
    ("argument_origen_witness_preexistence_souls_amand1945", "concept_apocatastasis"),
    ("argument_origen_witness_preexistence_souls_amand1945", "concept_metensomatosis_origen_amand1945"),
    ("argument_origen_witness_diss_problem1_prescience_amand1945", "concept_divine_prescience"),
    ("argument_origen_witness_diss_problem4_angelic_knowledge_amand1945", "concept_axia_biblos_tou_theou_origen_amand1945"),
    ("argument_origen_witness_double_freedom_amand1945", "concept_apocatastasis"),
]

for src, tgt in DISCUSSES:
    NEW_EDGES.append(make_edge(
        src=src, tgt=tgt,
        relation="discusses", confidence=0.85,
    ))


# ============================================================================
# 9. refines — §IV sub-args → arguments_carneadean_*_amand1945
# ============================================================================

REFINES = [
    # Transposition praise/blame → arg I + III carnéadiens
    ("argument_origen_witness_carneades_transposition_praise_blame_amand1945", "argument_carneadean_virtue_vice_amand1945"),
    ("argument_origen_witness_carneades_transposition_praise_blame_amand1945", "argument_carneadean_incentives_amand1945"),
    # Transposition theological consequences → general theme
    ("argument_origen_witness_carneades_transposition_theological_consequences_amand1945", "argument_carneadean_general_theme_amand1945"),
    # God as evil → providence/mantike (carnéadien transposé sur théodicée)
    ("argument_origen_witness_carneades_transposition_god_as_evil_amand1945", "argument_carneadean_providence_mantike_alexander_amand1945"),
    # Prayer useless → piety
    ("argument_origen_witness_carneades_transposition_prayer_useless_amand1945", "argument_carneadean_piety_amand1945"),
    # Method signature → general theme (méta)
    ("argument_origen_witness_carneades_transposition_theological_method_amand1945", "argument_carneadean_general_theme_amand1945"),
    # Antiastrological problem2 (νόμιμα βαρβαρικά) → twins + horoscope arg carnéadien
    ("argument_origen_witness_diss_problem2_signs_not_causes_amand1945", "argument_carneadean_antiastrological_twins_amand1945"),
    ("argument_origen_witness_diss_problem3_human_ignorance_amand1945", "argument_carneadean_antiastrological_horoscope_impossibility_amand1945"),
]

for src, tgt in REFINES:
    NEW_EDGES.append(make_edge(
        src=src, tgt=tgt,
        relation="extends", confidence=0.8,
        md={"note": "B5 — sub-argument origénien transpose théologiquement le pivot carnéadien correspondant"},
    ))


# ============================================================================
# 10. derived_from — syntheses → enveloppes/sub-args
# ============================================================================

NEW_EDGES.extend([
    make_edge(
        src="synthesis_amand1945_origen_carneadean_filiation",
        tgt="argument_origen_witness_carneadean_transposition_envelope_amand1945",
        relation="discusses", confidence=0.9,
    ),
    make_edge(
        src="synthesis_amand1945_origen_first_christian_prescience_problem",
        tgt="argument_origen_witness_diss_problem1_prescience_amand1945",
        relation="discusses", confidence=0.95,
    ),
    make_edge(
        src="synthesis_amand1945_origen_first_precession_polemicist",
        tgt="argument_origen_witness_diss_precession_equinoxes_amand1945",
        relation="discusses", confidence=0.9,
    ),
    make_edge(
        src="synthesis_amand1945_origen_carneadean_method_signature",
        tgt="argument_origen_witness_carneades_transposition_theological_method_amand1945",
        relation="discusses", confidence=0.95,
    ),
    make_edge(
        src="synthesis_amand1945_origen_pivot_witness",
        tgt=ORIGEN,
        relation="discusses", confidence=0.95,
    ),
])


# ============================================================================
# 11. wrote_about — scholar Amand → Origen (le sujet) (un seul edge global)
# ============================================================================
# La metadata.claimed_by sur chaque synthesis suffit pour le rattachement. Amand→Origène
# est une relation suffisamment portée par les publications + scholarly_argument_* d'autres
# scholars. Pour cette wave, on n'ajoute PAS d'edge scholar→synthesis car `creates` n'accepte
# pas synthesis comme target. (Phase Origène déjà documentée via pub_amand_1945_fatalisme.)
