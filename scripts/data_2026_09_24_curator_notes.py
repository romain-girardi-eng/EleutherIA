#!/usr/bin/env python3
"""Decisions: curator notes standing in for public descriptions.

C2 queue_b_curator_notes.csv lists 141 descriptions that read as curator
notes. Only the cases that can be fixed without rewriting scholarly prose are
applied here; the others are recorded as needs_romain.
"""

QUEUE = "c2_translations_descriptions/queue_b_curator_notes.csv"

# The whole description is a verification note; the scholar's position is in
# metadata.stance. The note moves to metadata, the stance becomes the text.
STANCE_AS_DESCRIPTION = [
    "scholarly_argument_de_monneron_epicurean_indeterminism_and_fr_1",
    "scholarly_argument_dunn_free_will_and_determinism_in_p_0",
    "scholarly_argument_engberg_pedersen_fate_and_moral_responsibility__2",
    "scholarly_argument_engberg_pedersen_progression_and_moral_developm_3",
    "scholarly_argument_engberg_pedersen_determinism_and_fate_in_stoic__1",
    "scholarly_argument_frick_divine_providence_and_moral_re_0",
    "scholarly_argument_frick_divine_transcendence_and_provi_4",
    "scholarly_argument_frick_providence_and_creation_5",
    "scholarly_argument_o_keefe_epicurus_as_first_libertarian__2",
    "scholarly_argument_wolfson_comparison_with_plato_s_timaeu_3",
    "scholarly_argument_wolfson_laws_of_nature_and_divine_gove_0",
    "scholarly_argument_wolfson_mind_body_relation_and_human_c_1",
    "scholarly_argument_wolfson_rational_vs_irrational_soul_an_2",
    "scholarly_argument_bobichon_free_will_and_determinism_in_j_0",
]
# Audit verdicts under which the position is not supported by the source.
UNSUPPORTED = ("NOT_FOUND", "SOURCE_ABSENT", "DISTORTED")

# A truncated edit left a fragment of an instruction in the description; the
# intact text is metadata.specialty.
SPECIALTY_AS_DESCRIPTION = ["scholar_wolfson_h"]

# A private file path at the end of a public description.
TRAILING_LOCAL_PATH = {"pub_lienemann_2012_review_frede": " Texte intégral acquis : [local-path] "}
