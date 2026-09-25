#!/usr/bin/env python3
"""Decisions on c2_translations_descriptions/queue_b_identity_mismatch.csv (33 rows).

The Fédou 2026 bulletin rows were withdrawn by the fedou_bulletin_withdrawal
batch. One record carries an abstract that belongs to another book; the
rest describe their own entity.
"""

QUEUE = "c2_translations_descriptions/queue_b_identity_mismatch.csv"

# Abstract harvested from OpenAlex that is a publisher's blurb for a German
# constitutional-law commentary ("Verfassungskommentar", "Grundgesetz"), not
# the abstract of this Jewish Studies Quarterly article on Origen.
WRONG_ABSTRACT = {
    "pub_cohen_2010_sabbath_law_and_mishnah_shabbat_in_origen_de_principiis": ("Grundgesetz", "Verfassungskommentar"),
}

KEPT = {
    "pub_gauthier_1970_ethique_nicomaque": "Describes Gauthier's introduction and the claim Kahn 1988 reports from it.",
    "scholar_vibe_k": "Research areas of the scholar; nothing about another person.",
    "scholarly_argument_denzey_lewis_middle_platonism_heimarmene_an_4": "The position stated is the one in the label.",
    "pub_kolbet_2011_origen_185_253": "Abstract of Kolbet's chapter on Origen.",
}
