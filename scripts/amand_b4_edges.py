"""B4 edges : evidenced_by (CRITICAL for Alexandre De Fato 16-20) + transmission + envelope + influences."""
from __future__ import annotations
from typing import Any
from amand_b4_utils import make_edge  # type: ignore

NEW_EDGES: list[dict[str, Any]] = []


# ============================================================================
# CRITICAL : evidenced_by Alexander witness-2 args → passage_alex_fat_16-20
# This is the first time arguments-pivots get anchored passage-by-passage in B-series
# ============================================================================

# Ch. 16 = thème + 2 arguments (négligence + louange/blâme)
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch16_theme_virtue_neglect_amand1945",
    tgt="passage_alex_fat_16", relation="evidenced_by", confidence=0.95,
    md={"source_text_role": "primary_witness_n2_text", "amand_page": "p. 145, 149-150",
        "locus": "Bruns 186,13-187,5"},
))
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch16_theme_virtue_neglect_amand1945",
    tgt="passage_alex_fat_16_en", relation="evidenced_by", confidence=0.9,
    md={"source_text_role": "primary_witness_n2_text_translation", "amand_page": "p. 145"},
))
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch16_praise_blame_punishment_amand1945",
    tgt="passage_alex_fat_16", relation="evidenced_by", confidence=0.95,
    md={"source_text_role": "primary_witness_n2_text", "amand_page": "p. 145-146, 150-151",
        "locus": "Bruns 187,5-22"},
))
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch16_praise_blame_punishment_amand1945",
    tgt="passage_alex_fat_16_en", relation="evidenced_by", confidence=0.9,
    md={"source_text_role": "primary_witness_n2_text_translation"},
))

# Ch. 17 = providence/piété/mantique (REPAIRED node)
NEW_EDGES.append(make_edge(
    src="argument_carneadean_providence_mantike_alexander_amand1945",
    tgt="passage_alex_fat_17", relation="evidenced_by", confidence=0.95,
    md={"source_text_role": "primary_witness_n2_text", "amand_page": "p. 146-147, 151",
        "locus": "Bruns 187,22-188,22"},
))
NEW_EDGES.append(make_edge(
    src="argument_carneadean_providence_mantike_alexander_amand1945",
    tgt="passage_alex_fat_17_en", relation="evidenced_by", confidence=0.9,
    md={"source_text_role": "primary_witness_n2_text_translation"},
))

# Ch. 18 = auto-réfutation pragmatique
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch18_stoic_practical_self_refutation_amand1945",
    tgt="passage_alex_fat_18", relation="evidenced_by", confidence=0.95,
    md={"source_text_role": "primary_witness_n2_text", "amand_page": "p. 146-147, 152",
        "locus": "Bruns 188,22-189,25"},
))
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch18_stoic_practical_self_refutation_amand1945",
    tgt="passage_alex_fat_18_en", relation="evidenced_by", confidence=0.9,
    md={"source_text_role": "primary_witness_n2_text_translation"},
))

# Ch. 19 = châtiment effectif
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch19_de_facto_punishment_amand1945",
    tgt="passage_alex_fat_19", relation="evidenced_by", confidence=0.95,
    md={"source_text_role": "primary_witness_n2_text", "amand_page": "p. 147-148, 152-154",
        "locus": "Bruns 189,25-190,30"},
))
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch19_de_facto_punishment_amand1945",
    tgt="passage_alex_fat_19_en", relation="evidenced_by", confidence=0.9,
    md={"source_text_role": "primary_witness_n2_text_translation"},
))

# Ch. 20 = conclusion
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch20_conclusion_amand1945",
    tgt="passage_alex_fat_20", relation="evidenced_by", confidence=0.95,
    md={"source_text_role": "primary_witness_n2_text", "amand_page": "p. 148, 154",
        "locus": "Bruns 190,30-191,2"},
))
NEW_EDGES.append(make_edge(
    src="argument_alexander_witness2_ch20_conclusion_amand1945",
    tgt="passage_alex_fat_20_en", relation="evidenced_by", confidence=0.9,
    md={"source_text_role": "primary_witness_n2_text_translation"},
))

# Envelope (whole 16-20 range) → all 5 main passages
for pid in ["passage_alex_fat_16", "passage_alex_fat_17", "passage_alex_fat_18",
            "passage_alex_fat_19", "passage_alex_fat_20"]:
    NEW_EDGES.append(make_edge(
        src="argument_alexander_witness2_envelope_amand1945",
        tgt=pid, relation="evidenced_by", confidence=0.9,
        md={"source_text_role": "envelope_witness_n2", "amand_chapter": "De Fato 16-20"},
    ))


# ============================================================================
# Contains : envelopes → sub-arguments (witness-2 + witness-3)
# ============================================================================

for sub in [
    "argument_alexander_witness2_ch16_theme_virtue_neglect_amand1945",
    "argument_alexander_witness2_ch16_praise_blame_punishment_amand1945",
    "argument_carneadean_providence_mantike_alexander_amand1945",
    "argument_alexander_witness2_ch18_stoic_practical_self_refutation_amand1945",
    "argument_alexander_witness2_ch19_de_facto_punishment_amand1945",
    "argument_alexander_witness2_ch20_conclusion_amand1945",
]:
    NEW_EDGES.append(make_edge(
        src="argument_alexander_witness2_envelope_amand1945",
        tgt=sub, relation="contains", confidence=0.95,
    ))

for sub in [
    "argument_firmicus_witness3_virtue_vain_under_stars_amand1945",
    "argument_firmicus_witness3_religion_useless_amand1945",
    "argument_firmicus_witness3_laws_abrogated_amand1945",
]:
    NEW_EDGES.append(make_edge(
        src="argument_firmicus_witness3_envelope_amand1945",
        tgt=sub, relation="contains", confidence=0.95,
    ))


# ============================================================================
# evidence_for : witness arguments → B1 pivot arguments (Carneadean reconstruction)
# ============================================================================

# Alexander witness-2 → B1 pivots
witness2_to_b1 = [
    ("argument_alexander_witness2_ch16_theme_virtue_neglect_amand1945", "argument_carneadean_general_theme_amand1945", 0.9),
    ("argument_alexander_witness2_ch16_theme_virtue_neglect_amand1945", "argument_carneadean_action_futility_amand1945", 0.9),
    ("argument_alexander_witness2_ch16_praise_blame_punishment_amand1945", "argument_carneadean_virtue_vice_amand1945", 0.9),
    ("argument_alexander_witness2_ch16_praise_blame_punishment_amand1945", "argument_carneadean_legislation_amand1945", 0.85),
    ("argument_alexander_witness2_ch16_praise_blame_punishment_amand1945", "argument_carneadean_incentives_amand1945", 0.85),
    ("argument_carneadean_providence_mantike_alexander_amand1945", "argument_carneadean_piety_amand1945", 0.9),
    ("argument_alexander_witness2_ch18_stoic_practical_self_refutation_amand1945", "argument_carneadean_stoic_pragmatic_self_refutation_amand1945", 0.95),
    ("argument_alexander_witness2_ch19_de_facto_punishment_amand1945", "argument_carneadean_stoic_pragmatic_punishment_amand1945", 0.95),
    ("argument_alexander_witness2_ch19_de_facto_punishment_amand1945", "argument_carneadean_legislation_amand1945", 0.8),
    ("argument_alexander_witness2_ch20_conclusion_amand1945", "argument_carneadean_general_theme_amand1945", 0.85),
    ("argument_alexander_witness2_ch20_conclusion_amand1945", "argument_carneadean_piety_amand1945", 0.85),
    ("argument_alexander_witness2_envelope_amand1945", "argument_carneadean_general_theme_amand1945", 0.95),
]
for src, tgt, conf in witness2_to_b1:
    NEW_EDGES.append(make_edge(
        src=src, tgt=tgt, relation="evidence_for", confidence=conf,
        md={"amand_witness_rank": "primary_witness_n2", "amand_witness_role": "witness_2_alexander"},
    ))

# Firmicus witness-3 → B1 pivots
witness3_to_b1 = [
    ("argument_firmicus_witness3_virtue_vain_under_stars_amand1945", "argument_carneadean_virtue_vice_amand1945", 0.85),
    ("argument_firmicus_witness3_virtue_vain_under_stars_amand1945", "argument_carneadean_action_futility_amand1945", 0.85),
    ("argument_firmicus_witness3_religion_useless_amand1945", "argument_carneadean_piety_amand1945", 0.85),
    ("argument_firmicus_witness3_religion_useless_amand1945", "argument_carneadean_providence_mantike_alexander_amand1945", 0.7),
    ("argument_firmicus_witness3_laws_abrogated_amand1945", "argument_carneadean_legislation_amand1945", 0.9),
    ("argument_firmicus_witness3_laws_abrogated_amand1945", "argument_carneadean_virtue_vice_amand1945", 0.8),
    ("argument_firmicus_witness3_laws_abrogated_amand1945", "argument_carneadean_incentives_amand1945", 0.8),
    ("argument_firmicus_witness3_envelope_amand1945", "argument_carneadean_general_theme_amand1945", 0.85),
]
for src, tgt, conf in witness3_to_b1:
    NEW_EDGES.append(make_edge(
        src=src, tgt=tgt, relation="evidence_for", confidence=conf,
        md={"amand_witness_rank": "primary_witness_n3", "amand_witness_role": "witness_3_firmicus"},
    ))


# ============================================================================
# cites_primary_source : Firmicus witness-3 args → work_firmicus_mathesis
# ============================================================================

for src in [
    "argument_firmicus_witness3_virtue_vain_under_stars_amand1945",
    "argument_firmicus_witness3_religion_useless_amand1945",
    "argument_firmicus_witness3_laws_abrogated_amand1945",
    "argument_firmicus_witness3_envelope_amand1945",
]:
    NEW_EDGES.append(make_edge(
        src=src, tgt="work_firmicus_mathesis",
        relation="cites_primary_source", confidence=0.95,
        md={"locus": "Mathesis I, 2, 5-11"},
    ))


# ============================================================================
# Authorship : works → person
# ============================================================================

NEW_EDGES.append(make_edge(
    src="work_firmicus_mathesis",
    tgt="person_firmicus_maternus_2q7r9t65",
    relation="authored_by", confidence=1.0,
))
NEW_EDGES.append(make_edge(
    src="work_firmicus_de_errore_profanarum_religionum",
    tgt="person_firmicus_maternus_2q7r9t65",
    relation="authored_by", confidence=1.0,
))


# ============================================================================
# Discusses : persons/works → concepts/key arguments
# ============================================================================

NEW_EDGES.append(make_edge(
    src="person_alexander_aphrodisias_fl200ce_n5o6p7q8",
    tgt="concept_to_endechomenon_alexander_amand1945",
    relation="discusses", confidence=0.95,
    md={"amand_locus": "De Fato 9, 11-15"},
))
NEW_EDGES.append(make_edge(
    src="work_de_fato_alexander_c200ce_o6p7q8r9",
    tgt="concept_to_endechomenon_alexander_amand1945",
    relation="discusses", confidence=0.95,
))


# ============================================================================
# Influences (filiations transmission)
# ============================================================================

NEW_EDGES.append(make_edge(
    src="person_carneades_214_129bce_l2m3n4o5",
    tgt="person_alexander_aphrodisias_fl200ce_n5o6p7q8",
    relation="influences", confidence=0.7,
    md={"transmission_path": "via Clitomaque + tradition d'école péripatéticienne (conjectural)",
        "amand_page": "p. 139-140, 144-145"},
))
NEW_EDGES.append(make_edge(
    src="person_carneades_214_129bce_l2m3n4o5",
    tgt="person_firmicus_maternus_2q7r9t65",
    relation="influences", confidence=0.55,
    md={"transmission_path": "via Clitomaque + manuel apotélesmatique Néchepso-Pétosiris (conjectural, Boll)",
        "amand_page": "p. 181-185"},
))
NEW_EDGES.append(make_edge(
    src="person_chrysippus_280_206bce_i9j0k1l2",
    tgt="person_alexander_aphrodisias_fl200ce_n5o6p7q8",
    relation="influences", confidence=0.85,
    md={"transmission_path": "lecture directe et critique des œuvres de Chrysippe par Alexandre (von Arnim SVF I p. XVI-XVII)",
        "amand_page": "p. 139-140 + note"},
))


# ============================================================================
# Critiques : Alexandre and Firmicus's targets
# ============================================================================

NEW_EDGES.append(make_edge(
    src="person_alexander_aphrodisias_fl200ce_n5o6p7q8",
    tgt="person_chrysippus_280_206bce_i9j0k1l2",
    relation="critiques", confidence=0.95,
    md={"amand_note": "Cible polémique exclusive d'Alexandre dans le Περὶ εἱμαρμένης, jamais nommé mais désigné comme leader du dogme stoïcien"},
))


# ============================================================================
# Member_of school
# ============================================================================

NEW_EDGES.append(make_edge(
    src="person_alexander_aphrodisias_fl200ce_n5o6p7q8",
    tgt="school_peripatetics",
    relation="member_of", confidence=1.0,
    md={"amand_note": "scholarque péripatéticien à Athènes 198-217 sous Septime Sévère"},
))


# ============================================================================
# is_witness_for : the 5 carneadean-pivot arguments
# ============================================================================
# Already covered by evidence_for above; we don't duplicate.


# ============================================================================
# Cross-witness convergence (3-witnesses-out-of-six rule)
# Alexandre + Philon + Firmicus on argument_carneadean_legislation = 3/6 → confirmed Carneadean
# ============================================================================

# These are recorded as metadata on the convergence-synthesis (no edge needed); the convergence
# is implicit in the multiple evidence_for edges going to the same B1 pivot.


# ============================================================================
# Synthesis links : témoin-related syntheses connected to person and work
# ============================================================================

# Alexandre portrait syntheses → person Alexandre
for syn in [
    "synthesis_amand1945_alexander_portrait_exegete",
    "synthesis_amand1945_alexander_naturalist_materialism",
    "synthesis_amand1945_alexander_physical_determinism_sublunar",
    "synthesis_amand1945_alexander_defends_contingency",
    "synthesis_amand1945_alexander_no_astrological_targeting",
    "synthesis_amand1945_alexander_witness_n2_insufficient_alone",
]:
    NEW_EDGES.append(make_edge(
        src=syn, tgt="person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        relation="discusses", confidence=0.9,
    ))

# Alexandre De Fato composition + witness identification → work
for syn in [
    "synthesis_amand1945_alexander_de_fato_triple_composition",
    "synthesis_amand1945_alexander_witness_n2_identification",
]:
    NEW_EDGES.append(make_edge(
        src=syn, tgt="work_de_fato_alexander_c200ce_o6p7q8r9",
        relation="discusses", confidence=0.95,
    ))

# Firmicus syntheses → person Firmicus + works
for syn in [
    "synthesis_amand1945_firmicus_paradox_pagan_christian",
    "synthesis_amand1945_firmicus_absolute_fatalism_doctrine",
]:
    NEW_EDGES.append(make_edge(
        src=syn, tgt="person_firmicus_maternus_2q7r9t65",
        relation="discusses", confidence=0.95,
    ))
for syn in [
    "synthesis_amand1945_firmicus_book_i_apologetic_structure",
    "synthesis_amand1945_firmicus_carneadean_origin_identification",
]:
    NEW_EDGES.append(make_edge(
        src=syn, tgt="work_firmicus_mathesis",
        relation="discusses", confidence=0.95,
    ))

# Comparative syntheses → both Alexander and Firmicus persons
for syn in [
    "synthesis_amand1945_alexander_scholastic_vs_philo_firmicus_diatribe",
    "synthesis_amand1945_firmicus_diatribe_style_vs_alexander_scholasticism",
]:
    NEW_EDGES.append(make_edge(
        src=syn, tgt="person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        relation="discusses", confidence=0.85,
    ))
    NEW_EDGES.append(make_edge(
        src=syn, tgt="person_firmicus_maternus_2q7r9t65",
        relation="discusses", confidence=0.85,
    ))

# Transmission chain synthesis → key persons
NEW_EDGES.append(make_edge(
    src="synthesis_amand1945_transmission_carneades_to_firmicus_chain",
    tgt="person_carneades_214_129bce_l2m3n4o5",
    relation="discusses", confidence=0.9,
))
NEW_EDGES.append(make_edge(
    src="synthesis_amand1945_transmission_carneades_to_firmicus_chain",
    tgt="person_firmicus_maternus_2q7r9t65",
    relation="discusses", confidence=0.9,
))


# ============================================================================
# claimed_by Amand : envelope nodes attest the Amand-reconstruction status
# ============================================================================

for env in [
    "argument_alexander_witness2_envelope_amand1945",
    "argument_firmicus_witness3_envelope_amand1945",
]:
    NEW_EDGES.append(make_edge(
        src=env, tgt="scholar_amand_de_mendieta_e",
        relation="claimed_by", confidence=1.0,
    ))
