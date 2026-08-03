"""Cicero De Fato deep B1 — UPDATES list (metadata-only enrichments).

This batch is primarily edge-additive. We add a small `cicero_de_fato_deep_b1`
metadata flag to each of the 15+ scholar nodes that we anchor, so a downstream
audit can locate scholars whose Cic. Fat. citations were normalized.
No descriptions are rewritten.
"""
from __future__ import annotations

from typing import Any

# Nodes we anchor in this batch (used both here as a manifest and re-imported
# by the inserts/edges modules for cross-checking).
ANCHORED_SCHOLAR_IDS: list[str] = [
    # ---- target list provided by task brief
    "pub_sharples_1991_cicero_boethius",
    "argument_carneadean_assent_chain_via_cicero_amand1945",
    "pub_frede_2011_free_will",
    "argument_frede_2011_alexander_libertarian_dead_end",
    "argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction",
    "argument_bobzien_2001_b1_chrysippean_modal_system",
    "argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence",
    "argument_gourinat_2014_in_nostra_potestate_not_eph_hemin",
    "argument_maso_2014_cicero_motus_animi_voluntarius_independence",
    "pub_destree_salles_zingano_2014_what_is_up_to_us",
    "argument_furst_2022_de_princ_iii_1_first_freedom_treatise",
    "pub_furst_2022_wege_freiheit",
    # ---- legacy scholarly_argument_* discovered via grep, currently orphans
    "scholarly_argument_donini_cicero_s_de_fato_and_aristotle_5",
    "scholarly_argument_gourinat_cicero_s_critique_of_chrysippu_2",
    "scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4",
    # ---- Amand synthesis nodes (cannot host cites_primary_source per ontology,
    #      so we anchor only via discusses + their authored arguments)
    "synthesis_amand1945_cicero_defato_moral_lacuna",
    "synthesis_amand1945_cicero_defato_source_antiochus",
]

UPDATES: list[dict[str, Any]] = [
    {
        "id": sid,
        "metadata_updates": {
            "cicero_de_fato_deep_b1_anchored": True,
        },
    }
    for sid in ANCHORED_SCHOLAR_IDS
]
