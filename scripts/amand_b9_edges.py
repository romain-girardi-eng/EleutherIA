"""Amand B9 — NEW_EDGES list.

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
    # Hippolyte de Rome -> Philosophoumena
    _edge("person_hippolytus_rome_d235", "work_hippolytus_philosophoumena", "wrote"),
    _edge("work_hippolytus_philosophoumena", "person_hippolytus_rome_d235", "authored_by"),
    # Bardesane (et Philippe disciple) -> LLR
    _edge("person_bardesanes_the_syrian_3r8s0u76", "work_bardesanes_liber_legum_regionum", "wrote"),
    _edge("work_bardesanes_liber_legum_regionum", "person_bardesanes_the_syrian_3r8s0u76", "authored_by"),
    # Epiphane -> Panarion + Ancoratus
    _edge("person_epiphanius_salamis_d403", "work_epiphanius_panarion", "wrote"),
    _edge("person_epiphanius_salamis_d403", "work_epiphanius_ancoratus", "wrote"),
    _edge("work_epiphanius_panarion", "person_epiphanius_salamis_d403", "authored_by"),
    _edge("work_epiphanius_ancoratus", "person_epiphanius_salamis_d403", "authored_by"),
    # Diodore de Tarse -> Contra Heimarmenen + Romans commentary
    _edge("person_diodore_tarsus_d390", "work_diodore_tarsus_contra_astronomos_heimarmenen", "wrote"),
    _edge("person_diodore_tarsus_d390", "work_diodore_tarsus_commentary_romans", "wrote"),
    _edge("work_diodore_tarsus_contra_astronomos_heimarmenen", "person_diodore_tarsus_d390", "authored_by"),
    _edge("work_diodore_tarsus_commentary_romans", "person_diodore_tarsus_d390", "authored_by"),
    # Commentateur arien anonyme de Job -> Pseudo-Origenes In Iob
    _edge("person_anonymous_arian_job_commentator_4c_ce", "work_pseudo_origenes_in_iob_arian_commentary", "wrote"),
    _edge("work_pseudo_origenes_in_iob_arian_commentary", "person_anonymous_arian_job_commentator_4c_ce", "authored_by"),
    # Irenee -> Demonstratio apostolic
    _edge("person_irenaeus_d202", "work_irenaeus_demonstratio_apostolic", "wrote"),
    _edge("work_irenaeus_demonstratio_apostolic", "person_irenaeus_d202", "authored_by"),
])


# =============================================================================
# 2. SYNTHESIS authorship by Amand (synthesis -> scholar_amand_de_mendieta_e)
# =============================================================================
SYNTHESIS_IDS = [
    "synthesis_amand1945_justin_first_christian_carneadean_user",
    "synthesis_amand1945_tatian_no_carneadean_link",
    "synthesis_amand1945_irenaeus_transposed_topos",
    "synthesis_amand1945_hippolytus_no_carneadean_use",
    "synthesis_amand1945_bardesanes_secondary_witness_ethnographic",
    "synthesis_amand1945_clement_alexandria_minimal_echo",
    "synthesis_amand1945_methodius_indirect_via_hypomnema",
    "synthesis_amand1945_methodius_anti_origenist_reaction",
    "synthesis_amand1945_epiphanius_servile_carneadean_topoi",
    "synthesis_amand1945_epiphanius_antiorigenist_polemic_anti_philosophy",
    "synthesis_amand1945_diodore_tarsus_largest_antifatalist_treatise",
    "synthesis_amand1945_diodore_tarsus_two_carneadean_echoes",
    "synthesis_amand1945_arian_job_witness_carneadean_pity_argument",
    "synthesis_amand1945_arian_job_homoean_dating_draguet",
]
for sid in SYNTHESIS_IDS:
    NEW_EDGES.append(_edge(sid, "scholar_amand_de_mendieta_e", "authored_by"))


# =============================================================================
# 3. SCHOLARLY DISCUSSION — syntheses discuss argument/concept/person/work
# =============================================================================
NEW_EDGES.extend([
    # Justin synthesis
    _edge("synthesis_amand1945_justin_first_christian_carneadean_user",
          "person_justin_martyr_2c_ce", "discusses"),
    _edge("synthesis_amand1945_justin_first_christian_carneadean_user",
          "person_carneades_214_129bce_l2m3n4o5", "discusses"),
    _edge("synthesis_amand1945_justin_first_christian_carneadean_user",
          "argument_justin_1apol_43_three_carneadean_topoi", "discusses"),
    # Tatian synthesis
    _edge("synthesis_amand1945_tatian_no_carneadean_link",
          "person_tatian", "discusses"),
    _edge("synthesis_amand1945_tatian_no_carneadean_link",
          "work_tatian_oratio", "discusses"),
    # Irenaeus synthesis
    _edge("synthesis_amand1945_irenaeus_transposed_topos",
          "person_irenaeus_d202", "discusses"),
    _edge("synthesis_amand1945_irenaeus_transposed_topos",
          "argument_irenaeus_adv_haer_iv_37_praise_blame_transposed", "discusses"),
    # Hippolytus synthesis
    _edge("synthesis_amand1945_hippolytus_no_carneadean_use",
          "person_hippolytus_rome_d235", "discusses"),
    _edge("synthesis_amand1945_hippolytus_no_carneadean_use",
          "work_hippolytus_philosophoumena", "discusses"),
    # Bardesanes synthesis
    _edge("synthesis_amand1945_bardesanes_secondary_witness_ethnographic",
          "person_bardesanes_the_syrian_3r8s0u76", "discusses"),
    _edge("synthesis_amand1945_bardesanes_secondary_witness_ethnographic",
          "work_bardesanes_liber_legum_regionum", "discusses"),
    _edge("synthesis_amand1945_bardesanes_secondary_witness_ethnographic",
          "argument_bardesanes_nomima_barbarika_amplified", "discusses"),
    _edge("synthesis_amand1945_bardesanes_secondary_witness_ethnographic",
          "argument_bardesanes_triple_delimitation_physis_heimarmene_autexousion", "discusses"),
    _edge("synthesis_amand1945_bardesanes_secondary_witness_ethnographic",
          "concept_nomima_barbarika_amand", "discusses"),
    # Clement synthesis
    _edge("synthesis_amand1945_clement_alexandria_minimal_echo",
          "person_clement_alexandria", "discusses"),
    _edge("synthesis_amand1945_clement_alexandria_minimal_echo",
          "argument_clement_alex_carneadean_glissement_faith_unbelief", "discusses"),
    _edge("synthesis_amand1945_clement_alexandria_minimal_echo",
          "argument_clement_alex_strom_1_83_5_praise_blame", "discusses"),
    # Methodius syntheses
    _edge("synthesis_amand1945_methodius_indirect_via_hypomnema",
          "person_methodius_olympus_d311", "discusses"),
    _edge("synthesis_amand1945_methodius_indirect_via_hypomnema",
          "argument_methodius_symposium_three_carneadean_syllogisms", "discusses"),
    _edge("synthesis_amand1945_methodius_anti_origenist_reaction",
          "person_methodius_olympus_d311", "discusses"),
    _edge("synthesis_amand1945_methodius_anti_origenist_reaction",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    # Epiphanius syntheses
    _edge("synthesis_amand1945_epiphanius_servile_carneadean_topoi",
          "person_epiphanius_salamis_d403", "discusses"),
    _edge("synthesis_amand1945_epiphanius_servile_carneadean_topoi",
          "work_epiphanius_panarion", "discusses"),
    _edge("synthesis_amand1945_epiphanius_antiorigenist_polemic_anti_philosophy",
          "person_epiphanius_salamis_d403", "discusses"),
    _edge("synthesis_amand1945_epiphanius_antiorigenist_polemic_anti_philosophy",
          "person_origen_alexandria_185_254ce_s9t0u1v2", "discusses"),
    # Diodore syntheses
    _edge("synthesis_amand1945_diodore_tarsus_largest_antifatalist_treatise",
          "person_diodore_tarsus_d390", "discusses"),
    _edge("synthesis_amand1945_diodore_tarsus_largest_antifatalist_treatise",
          "work_diodore_tarsus_contra_astronomos_heimarmenen", "discusses"),
    _edge("synthesis_amand1945_diodore_tarsus_two_carneadean_echoes",
          "argument_diodore_tarsus_impossibility_prediction_carneadean", "discusses"),
    _edge("synthesis_amand1945_diodore_tarsus_two_carneadean_echoes",
          "person_carneades_214_129bce_l2m3n4o5", "discusses"),
    # Arian Job syntheses
    _edge("synthesis_amand1945_arian_job_witness_carneadean_pity_argument",
          "person_anonymous_arian_job_commentator_4c_ce", "discusses"),
    _edge("synthesis_amand1945_arian_job_witness_carneadean_pity_argument",
          "work_pseudo_origenes_in_iob_arian_commentary", "discusses"),
    _edge("synthesis_amand1945_arian_job_witness_carneadean_pity_argument",
          "argument_arian_job_pity_criminals_carneadean_5th_title", "discusses"),
    _edge("synthesis_amand1945_arian_job_witness_carneadean_pity_argument",
          "argument_arian_job_useless_prayer_under_fatalism", "discusses"),
    _edge("synthesis_amand1945_arian_job_homoean_dating_draguet",
          "person_anonymous_arian_job_commentator_4c_ce", "discusses"),
])


# =============================================================================
# 4. ARGUMENTS authored_by their respective persons
# =============================================================================
NEW_EDGES.extend([
    _edge("argument_bardesanes_nomima_barbarika_amplified",
          "person_bardesanes_the_syrian_3r8s0u76", "authored_by"),
    _edge("argument_bardesanes_triple_delimitation_physis_heimarmene_autexousion",
          "person_bardesanes_the_syrian_3r8s0u76", "authored_by"),
    _edge("argument_clement_alex_carneadean_glissement_faith_unbelief",
          "person_clement_alexandria", "authored_by"),
    _edge("argument_clement_alex_strom_1_83_5_praise_blame",
          "person_clement_alexandria", "authored_by"),
    _edge("argument_methodius_symposium_three_carneadean_syllogisms",
          "person_methodius_olympus_d311", "authored_by"),
    _edge("argument_methodius_libre_arbitre_obeissance_irenean",
          "person_methodius_olympus_d311", "authored_by"),
    _edge("argument_irenaeus_adv_haer_iv_37_praise_blame_transposed",
          "person_irenaeus_d202", "authored_by"),
    _edge("argument_justin_1apol_43_three_carneadean_topoi",
          "person_justin_martyr_2c_ce", "authored_by"),
    _edge("argument_diodore_tarsus_impossibility_prediction_carneadean",
          "person_diodore_tarsus_d390", "authored_by"),
    _edge("argument_arian_job_pity_criminals_carneadean_5th_title",
          "person_anonymous_arian_job_commentator_4c_ce", "authored_by"),
    _edge("argument_arian_job_useless_prayer_under_fatalism",
          "person_anonymous_arian_job_commentator_4c_ce", "authored_by"),
])


# =============================================================================
# 5. CITES_PRIMARY_SOURCE — arguments -> works (witness anchoring)
# =============================================================================
NEW_EDGES.extend([
    # Bardesanes arguments -> LLR
    _edge("argument_bardesanes_nomima_barbarika_amplified",
          "work_bardesanes_liber_legum_regionum", "cites_primary_source"),
    _edge("argument_bardesanes_triple_delimitation_physis_heimarmene_autexousion",
          "work_bardesanes_liber_legum_regionum", "cites_primary_source"),
    # Justin's arg -> 1 Apol.
    _edge("argument_justin_1apol_43_three_carneadean_topoi",
          "work_justin_first_apology", "cites_primary_source"),
    # Irenaeus's arg -> Adv. Haer. Book IV
    _edge("argument_irenaeus_adv_haer_iv_37_praise_blame_transposed",
          "work_irenaeus_adversus_haereses_book4", "cites_primary_source"),
    # Clement's args -> Stromateis
    _edge("argument_clement_alex_carneadean_glissement_faith_unbelief",
          "work_clement_stromateis", "cites_primary_source"),
    _edge("argument_clement_alex_strom_1_83_5_praise_blame",
          "work_clement_stromateis", "cites_primary_source"),
    # Methodius's args -> Symposium / De Autexusio
    _edge("argument_methodius_symposium_three_carneadean_syllogisms",
          "work_methodius_symposium_144841d0", "cites_primary_source"),
    _edge("argument_methodius_libre_arbitre_obeissance_irenean",
          "work_methodius_de_autexusio_4c37c892", "cites_primary_source"),
    # Diodore's arg -> Contra Heimarmenen
    _edge("argument_diodore_tarsus_impossibility_prediction_carneadean",
          "work_diodore_tarsus_contra_astronomos_heimarmenen", "cites_primary_source"),
    # Arian Job's args -> Pseudo-Origenes In Iob
    _edge("argument_arian_job_pity_criminals_carneadean_5th_title",
          "work_pseudo_origenes_in_iob_arian_commentary", "cites_primary_source"),
    _edge("argument_arian_job_useless_prayer_under_fatalism",
          "work_pseudo_origenes_in_iob_arian_commentary", "cites_primary_source"),
])


# =============================================================================
# 6. EVIDENCED_BY — Irenaeus argument -> existing passage (Adv. Haer. IV.37)
#    Clement Stromateis : aucun passage Stromateis present dans le corpus
#    (53 passages Clement = Protrepticus uniquement) - donc pas d'ancrage
#    evidenced_by possible pour Clement, on reste sur cites_primary_source
#    vers work_clement_stromateis. Evidence_pending pour Clement.
# =============================================================================
NEW_EDGES.extend([
    # Irenaeus Adv. Haer. IV 37 echo - direct anchor possible
    _edge("argument_irenaeus_adv_haer_iv_37_praise_blame_transposed",
          "passage_irenaeus_ah_4_37", "evidenced_by", confidence=0.9,
          amand_source="Amand 1945 p. 222-223 - Adv. Haer. IV.37.1-2 contient l'echo carneadien"),
])


# =============================================================================
# 7. INFLUENCE CHAINS — patristic filiations Amand-asserted
# =============================================================================
NEW_EDGES.extend([
    # Justin influences Tatien (master-disciple, Amand p. 209)
    _edge("person_justin_martyr_2c_ce", "person_tatian", "influences",
          confidence=0.95,
          amand_source="Amand 1945 p. 209 - 'Tatien n'en est pas moins l'ouvrier de la meme oeuvre que son maitre' Justin"),
    # Justin influences Irenee (Amand p. 200 - precurseur)
    _edge("person_justin_martyr_2c_ce", "person_irenaeus_d202", "influences",
          confidence=0.85,
          amand_source="Amand 1945 p. 200 - Justin 'initiateur du christianisme humaniste' avant Clement et Irenee"),
    # Irenee influences Methode (Amand p. 333 - dependance directe sur le libre arbitre)
    _edge("person_irenaeus_d202", "person_methodius_olympus_d311", "influences",
          confidence=0.9,
          amand_source="Amand 1945 p. 333-335 - 'A la suite des Apologistes et surtout d'Irenee' Methode affirme la liberte comme don divin"),
    # Carneades influences Bardesane via tradition scolaire (Amand p. 233, 243)
    _edge("person_carneades_214_129bce_l2m3n4o5", "person_bardesanes_the_syrian_3r8s0u76", "influences",
          confidence=0.75,
          amand_source="Amand 1945 p. 243 - 'Bardesane est peut-etre le premier a avoir mis en oeuvre [nomima barbarika] avec une telle profusion'"),
    # Carneades influences Diodore via Cicero/transmission scolaire
    _edge("person_carneades_214_129bce_l2m3n4o5", "person_diodore_tarsus_d390", "influences",
          confidence=0.75,
          amand_source="Amand 1945 p. 477-478 - Diodore reproduit deux topoi carneadiens"),
    # Cicero influences Diodore (Amand p. 470 - rapprochements pertinents avec De Nat. Deor.)
    _edge("person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "person_diodore_tarsus_d390", "influences",
          confidence=0.7,
          amand_source="Amand 1945 p. 470 note - 'parallels entre certains passages de Diodore et des endroits du De natura deorum de Ciceron'"),
    # Diodore influences Chrysostome (maitre-disciple direct, Amand p. 463)
    _edge("person_diodore_tarsus_d390", "person_john_chrysostom_d407", "influences",
          confidence=0.95,
          amand_source="Amand 1945 p. 463 - 'maitre de Jean Chrysostome qui a conserve de lui un souvenir enthousiaste'"),
    # Methode critiques Origene (Amand p. 327-329)
    _edge("person_methodius_olympus_d311", "person_origen_alexandria_185_254ce_s9t0u1v2", "critiques",
          confidence=0.95,
          amand_source="Amand 1945 p. 327-329 - 'principal adversaire intellectuel d'Origene a la fin du IIIe siecle'"),
    # Epiphane critiques Origene (Amand p. 449-451)
    _edge("person_epiphanius_salamis_d403", "person_origen_alexandria_185_254ce_s9t0u1v2", "critiques",
          confidence=0.95,
          amand_source="Amand 1945 p. 449-451 - polemique antiorigeniste violente, Origene = 'pere de l'arianisme'"),
    # Eusebe influences Epiphane (Amand p. 442 - meme decennie d'activite)
    _edge("person_eusebius_caesarea_d339", "person_epiphanius_salamis_d403", "influences",
          confidence=0.7,
          amand_source="Amand 1945 p. 441-442 - activite litteraire d'Epiphane contemporaine de Basile/Gregoire de Nazianze, succede a Eusebe heresiologue"),
    # Hippolyte influence par Irenee (disciple selon Amand p. 224)
    _edge("person_irenaeus_d202", "person_hippolytus_rome_d235", "influences",
          confidence=0.9,
          amand_source="Amand 1945 p. 224 - Hippolyte 'disciple d'Irenee, theologien du Logos et polemiste antignostique'"),
    # Carneades influences Arien Job commentateur (via source philosophique probable)
    _edge("person_carneades_214_129bce_l2m3n4o5", "person_anonymous_arian_job_commentator_4c_ce", "influences",
          confidence=0.7,
          amand_source="Amand 1945 p. 545 - digression utilise des arguments carneadiens via une source philosophique probable (peut-etre un hypomnema scolaire)"),
    # Basile influence par meme source que commentateur arien (Amand p. 537-538)
    _edge("person_anonymous_arian_job_commentator_4c_ce", "person_basil_great_d379", "influenced_by",
          confidence=0.7,
          amand_source="Amand 1945 p. 537-538 - source philosophique commune avec Basile Hex. VI.5-7"),
    # Crescens accuses Justin
    _edge("person_crescens_cynic_2c_ce", "person_justin_martyr_2c_ce", "critiques",
          confidence=0.95,
          amand_source="Amand 1945 p. 195 - Justin martyrise sous Marc Aurele apres accusation"),
])


# =============================================================================
# 8. CITES_PRIMARY_SOURCE - Eusebe PE VI.10 cites Bardesane LLR
# =============================================================================
NEW_EDGES.extend([
    _edge("person_eusebius_caesarea_d339", "work_bardesanes_liber_legum_regionum",
          "cites_primary_source",
          confidence=0.95,
          amand_source="Amand 1945 p. 239 - PE VI.10.1-48 transcrit deux longs fragments de la version grecque du LLR"),
])


# =============================================================================
# 9. EMPLOYS / DISCUSSES - Bardesanes & Diodore & Arian Job employ nomima barbarika concept
# =============================================================================
NEW_EDGES.extend([
    _edge("argument_bardesanes_nomima_barbarika_amplified", "concept_nomima_barbarika_amand", "employs"),
    _edge("argument_diodore_tarsus_impossibility_prediction_carneadean", "concept_nomima_barbarika_amand", "employs"),
    # Bardesane discute heimarmene fate stoics
    _edge("argument_bardesanes_triple_delimitation_physis_heimarmene_autexousion",
          "concept_heimarmene_fate_stoics_j0k1l2m3", "discusses"),
])


# =============================================================================
# 10. (removed) — synthesis -> publication part_of is invalid per edge_types.json
#    (part_of target_types = concept/passage/work/source_collection only).
#    Publication anchoring is preserved via metadata.publication field on each
#    synthesis (set via amand_metadata helper).
# =============================================================================


# =============================================================================
# 11. PRECEDES chains - patristic chronological ordering for Carneadean transmission
# =============================================================================
NEW_EDGES.extend([
    _edge("person_justin_martyr_2c_ce", "person_tatian", "precedes"),
    _edge("person_tatian", "person_irenaeus_d202", "precedes"),
    _edge("person_irenaeus_d202", "person_hippolytus_rome_d235", "precedes"),
    _edge("person_irenaeus_d202", "person_bardesanes_the_syrian_3r8s0u76", "precedes"),
    _edge("person_bardesanes_the_syrian_3r8s0u76", "person_clement_alexandria", "precedes"),
    _edge("person_clement_alexandria", "person_origen_alexandria_185_254ce_s9t0u1v2", "precedes"),
    _edge("person_origen_alexandria_185_254ce_s9t0u1v2", "person_methodius_olympus_d311", "precedes"),
    _edge("person_methodius_olympus_d311", "person_epiphanius_salamis_d403", "precedes"),
    _edge("person_epiphanius_salamis_d403", "person_diodore_tarsus_d390", "precedes"),
    _edge("person_diodore_tarsus_d390", "person_anonymous_arian_job_commentator_4c_ce", "precedes"),
    _edge("person_diodore_tarsus_d390", "person_john_chrysostom_d407", "precedes"),
])


# =============================================================================
# 12. MEMBER_OF - Diodore as Christian patristic + Crescens as cynic
#    (school_antiochene_exegesis n'existe pas dans le KG ; on rattache Diodore
#    et Crescens aux groupes/schools existants pour amorcer la connectivite)
# =============================================================================
NEW_EDGES.extend([
    _edge("person_diodore_tarsus_d390", "school_christian_patristic", "member_of"),
    _edge("person_crescens_cynic_2c_ce", "school_christian_apologists", "critiques",
          confidence=0.9,
          amand_source="Amand 1945 p. 195 - Crescens accusateur de Justin et des chretiens cultives"),
])
