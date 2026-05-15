"""Amand B7 — NEW_EDGES list.

Edge categories:
- authored_by: arguments/works → person
- contains: work → arguments
- evidenced_by: arguments → passages (CRITICAL: anchor Chrys arguments to sc79_* when matter matches)
- cites_primary_source: arguments → work-shells (Greek text absent from corpus)
- discusses: syntheses → works/arguments/concepts
- critiques: arguments → arguments
- supports: arguments → concepts
- precedes: work → work (Cappadocian chain), argument → argument (witness chronology)
- influences: person → person (Origen→Gregory Nyssa, Eusebius→Chrysostom, Basil→Nemesius)
- influenced_by: person → person (reverse declarations)
- belongs_to_school: person → school (existing schools)
- interprets: person → person (Nemesius interprets Aristotle)
- responds_to: argument → argument (Pseudo-Chrysostom V responds to fatalist objections)
- employs: argument → concept (uses Carneadean topoi)
- attests: passage → passage (for primary witnesses, but we use cites_primary_source for arg→work since Hom. Goth = work-shell)

All edges include confidence (default 0.85) and Amand-claim metadata.
"""
from __future__ import annotations

from typing import Any

from amand_b7_utils import AMAND_BIBTEX_KEY, dump_metadata


def _edge(
    *,
    source: str,
    target: str,
    relation: str,
    confidence: float = 0.85,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    md = {
        "claimed_by": "scholar_amand_de_mendieta_e",
        "publication": "pub_amand_1945_fatalisme",
        "bibtex_key": AMAND_BIBTEX_KEY,
    }
    if metadata:
        md.update(metadata)
    return {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": confidence,
        "metadata": dump_metadata(md),
    }


# =============================================================================
# 1. AUTHORED_BY — Gregory CF + Disc Cat arguments → Gregory of Nyssa
# =============================================================================

AUTHORED_BY_EDGES: list[dict[str, Any]] = [
    _edge(source="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
          target="person_gregory_nyssa_d395", relation="authored_by"),
    _edge(source="argument_gregory_contrafatum_catastrophes_amand1945",
          target="person_gregory_nyssa_d395", relation="authored_by"),
    _edge(source="argument_gregory_contrafatum_nomima_barbarika_amand1945",
          target="person_gregory_nyssa_d395", relation="authored_by"),
    _edge(source="argument_gregory_contrafatum_fate_of_fate_dilemma_amand1945",
          target="person_gregory_nyssa_d395", relation="authored_by"),
    _edge(source="argument_gregory_contrafatum_heimarmene_no_being_amand1945",
          target="person_gregory_nyssa_d395", relation="authored_by"),
    _edge(source="argument_gregory_contrafatum_diversity_destinies_amand1945",
          target="person_gregory_nyssa_d395", relation="authored_by"),
    _edge(source="argument_gregory_contrafatum_demonic_origin_amand1945",
          target="person_gregory_nyssa_d395", relation="authored_by"),
    _edge(source="argument_gregory_disccat31_carneadean_moral_amand1945",
          target="person_gregory_nyssa_d395", relation="authored_by"),
    # Chrysostom witness 5 + first text + 3 other args
    _edge(source="argument_chrysostom_hom_goth_witness5_amand1945",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="argument_chrysostom_hom_1tim_first_text_amand1945",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="argument_chrysostom_antiastrological_demonic_amand1945",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="argument_chrysostom_anti_hellenism_amand1945",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="argument_chrysostom_libre_arbitre_pastoral_amand1945",
          target="person_john_chrysostom_d407", relation="authored_by"),
    # Pseudo-Chrysostom witness 6
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="person_pseudo_chrysostom_de_fato", relation="authored_by"),
    _edge(source="argument_pseudo_chrysostom_de_fato_recapitulation_amand1945",
          target="person_pseudo_chrysostom_de_fato", relation="authored_by"),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945",
          target="person_pseudo_chrysostom_de_fato", relation="authored_by"),
    # Nemesius
    _edge(source="argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
          target="person_nemesius_emesa_4c_ce", relation="authored_by"),
    _edge(source="argument_nemesius_nat_hom_35_blasphemy_amand1945",
          target="person_nemesius_emesa_4c_ce", relation="authored_by"),
    _edge(source="argument_nemesius_nat_hom_36_apotropaic_refutation_amand1945",
          target="person_nemesius_emesa_4c_ce", relation="authored_by"),
    _edge(source="argument_nemesius_nat_hom_37_38_middle_platonism_critique_amand1945",
          target="person_nemesius_emesa_4c_ce", relation="authored_by"),
    # Authored_by for the work_pseudo_chrys → person_pseudo_chrys
    _edge(source="work_pseudo_chrysostom_de_fato_providentia",
          target="person_pseudo_chrysostom_de_fato", relation="authored_by"),
    # Authored_by for Chrysostom new work-shells → person_john_chrysostom_d407
    _edge(source="work_chrysostom_hom_paul_after_goth",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="work_chrysostom_hom_1_timothy",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="work_chrysostom_hom_ephesians",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="work_chrysostom_de_babylas_contra_julianum",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="work_chrysostom_hom_john",
          target="person_john_chrysostom_d407", relation="authored_by"),
    _edge(source="work_chrysostom_hom_colossians",
          target="person_john_chrysostom_d407", relation="authored_by"),
]


# =============================================================================
# 2. CONTAINS — works → arguments
# =============================================================================

CONTAINS_EDGES: list[dict[str, Any]] = [
    # Gregory Contra Fatum contains 7 arguments
    _edge(source="work_gregory_contra_fatum",
          target="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
          relation="contains"),
    _edge(source="work_gregory_contra_fatum",
          target="argument_gregory_contrafatum_catastrophes_amand1945",
          relation="contains"),
    _edge(source="work_gregory_contra_fatum",
          target="argument_gregory_contrafatum_nomima_barbarika_amand1945",
          relation="contains"),
    _edge(source="work_gregory_contra_fatum",
          target="argument_gregory_contrafatum_fate_of_fate_dilemma_amand1945",
          relation="contains"),
    _edge(source="work_gregory_contra_fatum",
          target="argument_gregory_contrafatum_heimarmene_no_being_amand1945",
          relation="contains"),
    _edge(source="work_gregory_contra_fatum",
          target="argument_gregory_contrafatum_diversity_destinies_amand1945",
          relation="contains"),
    _edge(source="work_gregory_contra_fatum",
          target="argument_gregory_contrafatum_demonic_origin_amand1945",
          relation="contains"),
    # Gregory Disc Cat 31
    _edge(source="work_gregory_oratio_catechetica",
          target="argument_gregory_disccat31_carneadean_moral_amand1945",
          relation="contains"),
    # Chrysostom works → arguments
    _edge(source="work_chrysostom_hom_paul_after_goth",
          target="argument_chrysostom_hom_goth_witness5_amand1945",
          relation="contains"),
    _edge(source="work_chrysostom_hom_1_timothy",
          target="argument_chrysostom_hom_1tim_first_text_amand1945",
          relation="contains"),
    _edge(source="work_chrysostom_hom_colossians",
          target="argument_chrysostom_antiastrological_demonic_amand1945",
          relation="contains"),
    _edge(source="work_chrysostom_hom_ephesians",
          target="argument_chrysostom_anti_hellenism_amand1945",
          relation="contains"),
    _edge(source="work_chrysostom_de_babylas_contra_julianum",
          target="argument_chrysostom_anti_hellenism_amand1945",
          relation="contains"),
    _edge(source="work_chrysostom_hom_john",
          target="argument_chrysostom_anti_hellenism_amand1945",
          relation="contains"),
    # Pseudo-Chrys De Fato V
    _edge(source="work_pseudo_chrysostom_de_fato_providentia",
          target="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          relation="contains"),
    _edge(source="work_pseudo_chrysostom_de_fato_providentia",
          target="argument_pseudo_chrysostom_de_fato_recapitulation_amand1945",
          relation="contains"),
    _edge(source="work_pseudo_chrysostom_de_fato_providentia",
          target="argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945",
          relation="contains"),
    # Nemesius Nat Hom contains 4 arguments
    _edge(source="work_nemesius_de_nat_hom",
          target="argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
          relation="contains"),
    _edge(source="work_nemesius_de_nat_hom",
          target="argument_nemesius_nat_hom_35_blasphemy_amand1945",
          relation="contains"),
    _edge(source="work_nemesius_de_nat_hom",
          target="argument_nemesius_nat_hom_36_apotropaic_refutation_amand1945",
          relation="contains"),
    _edge(source="work_nemesius_de_nat_hom",
          target="argument_nemesius_nat_hom_37_38_middle_platonism_critique_amand1945",
          relation="contains"),
]


# =============================================================================
# 3. EVIDENCED_BY — Chrysostom args → sc79_* passages (anchor to corpus!)
# =============================================================================

# Map: 5 Chrysostom args that can be anchored to existing SC79 sections.
# The matter overlaps these chapters per Amand:
# - libre_arbitre_pastoral: chap 1 (harmonie ame chretienne), chap 2 (libre arbitre vs heimarmene), chap 4 (justice divine)
# - antiastrological_demonic: chap 2 (diabolical tactic), chap 3 (anti-heimarmene)

EVIDENCED_BY_EDGES: list[dict[str, Any]] = [
    # libre_arbitre_pastoral → 3 SC79 sections
    _edge(source="argument_chrysostom_libre_arbitre_pastoral_amand1945",
          target="sc79_chrysostomus_de_providentia_chap1",
          relation="evidenced_by",
          confidence=0.85,
          metadata={"amand_anchor_rationale": "Discourse I: harmonie de l'âme chrétienne (Amand p. 505)"}),
    _edge(source="argument_chrysostom_libre_arbitre_pastoral_amand1945",
          target="sc79_chrysostomus_de_providentia_chap2",
          relation="evidenced_by",
          confidence=0.9,
          metadata={"amand_anchor_rationale": "Discourse II: incompatibilité libre arbitre vs heimarmene (Amand p. 505-506)"}),
    _edge(source="argument_chrysostom_libre_arbitre_pastoral_amand1945",
          target="sc79_chrysostomus_de_providentia_chap4",
          relation="evidenced_by",
          confidence=0.85,
          metadata={"amand_anchor_rationale": "Discourse IV: défense de la justice divine + jugement dernier (Amand p. 506)"}),
    # antiastrological_demonic → chap 2 + chap 3
    _edge(source="argument_chrysostom_antiastrological_demonic_amand1945",
          target="sc79_chrysostomus_de_providentia_chap2",
          relation="evidenced_by",
          confidence=0.9,
          metadata={"amand_anchor_rationale": "Discourse II: tactique diabolique introduisant heimarmene (Amand p. 506)"}),
    _edge(source="argument_chrysostom_antiastrological_demonic_amand1945",
          target="sc79_chrysostomus_de_providentia_chap3",
          relation="evidenced_by",
          confidence=0.9,
          metadata={"amand_anchor_rationale": "Discourse III: condamnation de la genesis (Amand p. 506)"}),
    # Pseudo-Chrysostom witness6 → chap 5 (the parallel SC79 section per PG numbering)
    # SC 79 numbering chap5 corresponds to Discourse V (Amand witness text n°6)
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="sc79_chrysostomus_de_providentia_chap5",
          relation="evidenced_by",
          confidence=0.9,
          metadata={
              "amand_anchor_rationale": "SC79 chap5 corresponds to Discourse V (PG 50, 765-768 witness text)",
              "anchor_status": "tentative — confirm SC79 chap5 = PG 50 Discourse V mapping",
          }),
    _edge(source="argument_pseudo_chrysostom_de_fato_recapitulation_amand1945",
          target="sc79_chrysostomus_de_providentia_chap5",
          relation="evidenced_by",
          confidence=0.85,
          metadata={"amand_anchor_rationale": "Climax récapitulatif au sein du Discours V"}),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945",
          target="sc79_chrysostomus_de_providentia_chap5",
          relation="evidenced_by",
          confidence=0.85,
          metadata={"amand_anchor_rationale": "Argument 8 (heimarmene injuste) au sein du Discours V"}),
]


# =============================================================================
# 4. CITES_PRIMARY_SOURCE — arguments → work-shells (corpus absent)
# =============================================================================

CITES_PRIMARY_SOURCE_EDGES: list[dict[str, Any]] = [
    # Gregory args → Contra Fatum work-shell
    _edge(source="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
          target="work_gregory_contra_fatum", relation="cites_primary_source"),
    _edge(source="argument_gregory_contrafatum_catastrophes_amand1945",
          target="work_gregory_contra_fatum", relation="cites_primary_source"),
    _edge(source="argument_gregory_contrafatum_nomima_barbarika_amand1945",
          target="work_gregory_contra_fatum", relation="cites_primary_source"),
    _edge(source="argument_gregory_contrafatum_fate_of_fate_dilemma_amand1945",
          target="work_gregory_contra_fatum", relation="cites_primary_source"),
    _edge(source="argument_gregory_contrafatum_heimarmene_no_being_amand1945",
          target="work_gregory_contra_fatum", relation="cites_primary_source"),
    _edge(source="argument_gregory_contrafatum_diversity_destinies_amand1945",
          target="work_gregory_contra_fatum", relation="cites_primary_source"),
    _edge(source="argument_gregory_contrafatum_demonic_origin_amand1945",
          target="work_gregory_contra_fatum", relation="cites_primary_source"),
    _edge(source="argument_gregory_disccat31_carneadean_moral_amand1945",
          target="work_gregory_oratio_catechetica", relation="cites_primary_source"),
    # Chrysostom witness 5 → Hom Goth
    _edge(source="argument_chrysostom_hom_goth_witness5_amand1945",
          target="work_chrysostom_hom_paul_after_goth", relation="cites_primary_source"),
    # Chrys first text → Hom 1 Tim
    _edge(source="argument_chrysostom_hom_1tim_first_text_amand1945",
          target="work_chrysostom_hom_1_timothy", relation="cites_primary_source"),
    # Chrys anti-hellenism → 3 works
    _edge(source="argument_chrysostom_anti_hellenism_amand1945",
          target="work_chrysostom_hom_ephesians", relation="cites_primary_source"),
    _edge(source="argument_chrysostom_anti_hellenism_amand1945",
          target="work_chrysostom_de_babylas_contra_julianum", relation="cites_primary_source"),
    _edge(source="argument_chrysostom_anti_hellenism_amand1945",
          target="work_chrysostom_hom_john", relation="cites_primary_source"),
    # Pseudo-Chrys witness6 → work-shell
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="work_pseudo_chrysostom_de_fato_providentia", relation="cites_primary_source"),
    _edge(source="argument_pseudo_chrysostom_de_fato_recapitulation_amand1945",
          target="work_pseudo_chrysostom_de_fato_providentia", relation="cites_primary_source"),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945",
          target="work_pseudo_chrysostom_de_fato_providentia", relation="cites_primary_source"),
    # Nemesius args → Nat Hom
    _edge(source="argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
          target="work_nemesius_de_nat_hom", relation="cites_primary_source"),
    _edge(source="argument_nemesius_nat_hom_35_blasphemy_amand1945",
          target="work_nemesius_de_nat_hom", relation="cites_primary_source"),
    _edge(source="argument_nemesius_nat_hom_36_apotropaic_refutation_amand1945",
          target="work_nemesius_de_nat_hom", relation="cites_primary_source"),
    _edge(source="argument_nemesius_nat_hom_37_38_middle_platonism_critique_amand1945",
          target="work_nemesius_de_nat_hom", relation="cites_primary_source"),
]


# =============================================================================
# 5. SYNTHESES discussing arguments/works
# =============================================================================

SYNTHESIS_DISCUSSES_EDGES: list[dict[str, Any]] = [
    # synthesis_amand1945_gregory_nyssa_carneadean_role
    _edge(source="synthesis_amand1945_gregory_nyssa_carneadean_role",
          target="work_gregory_contra_fatum", relation="discusses"),
    _edge(source="synthesis_amand1945_gregory_nyssa_carneadean_role",
          target="work_gregory_oratio_catechetica", relation="discusses"),
    _edge(source="synthesis_amand1945_gregory_nyssa_carneadean_role",
          target="person_gregory_nyssa_d395", relation="discusses"),
    _edge(source="synthesis_amand1945_gregory_nyssa_carneadean_role",
          target="argument_gregory_contrafatum_catastrophes_amand1945", relation="discusses"),
    _edge(source="synthesis_amand1945_gregory_nyssa_carneadean_role",
          target="argument_gregory_contrafatum_nomima_barbarika_amand1945", relation="discusses"),
    _edge(source="synthesis_amand1945_gregory_nyssa_carneadean_role",
          target="argument_gregory_disccat31_carneadean_moral_amand1945", relation="discusses"),
    # synthesis_amand1945_chrysostom_carneadean_paradox
    _edge(source="synthesis_amand1945_chrysostom_carneadean_paradox",
          target="person_john_chrysostom_d407", relation="discusses"),
    _edge(source="synthesis_amand1945_chrysostom_carneadean_paradox",
          target="argument_chrysostom_hom_goth_witness5_amand1945", relation="discusses"),
    _edge(source="synthesis_amand1945_chrysostom_carneadean_paradox",
          target="argument_chrysostom_anti_hellenism_amand1945", relation="discusses"),
    _edge(source="synthesis_amand1945_chrysostom_carneadean_paradox",
          target="work_chrysostom_hom_paul_after_goth", relation="discusses"),
    # synthesis_amand1945_pseudo_chrysostom_witness6_status
    _edge(source="synthesis_amand1945_pseudo_chrysostom_witness6_status",
          target="person_pseudo_chrysostom_de_fato", relation="discusses"),
    _edge(source="synthesis_amand1945_pseudo_chrysostom_witness6_status",
          target="work_pseudo_chrysostom_de_fato_providentia", relation="discusses"),
    _edge(source="synthesis_amand1945_pseudo_chrysostom_witness6_status",
          target="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945", relation="discusses"),
    # synthesis_amand1945_nemesius_witness_decay
    _edge(source="synthesis_amand1945_nemesius_witness_decay",
          target="person_nemesius_emesa_4c_ce", relation="discusses"),
    _edge(source="synthesis_amand1945_nemesius_witness_decay",
          target="work_nemesius_de_nat_hom", relation="discusses"),
    _edge(source="synthesis_amand1945_nemesius_witness_decay",
          target="argument_nemesius_nat_hom_35_carneadean_summary_amand1945", relation="discusses"),
    # synthesis_amand1945_cappadocian_chain
    _edge(source="synthesis_amand1945_cappadocian_chain",
          target="person_gregory_nyssa_d395", relation="discusses"),
    _edge(source="synthesis_amand1945_cappadocian_chain",
          target="person_basil_great_d379", relation="discusses"),
    _edge(source="synthesis_amand1945_cappadocian_chain",
          target="person_gregory_nazianzus_d389", relation="discusses"),
    _edge(source="synthesis_amand1945_cappadocian_chain",
          target="person_origen_alexandria_185_254ce_s9t0u1v2", relation="discusses"),
]


# =============================================================================
# 6. INFLUENCES / INFLUENCED_BY / PRECEDES — intellectual filiations
# =============================================================================

INFLUENCES_EDGES: list[dict[str, Any]] = [
    # Origen → Gregory of Nyssa (intellectual influence per Amand p. 411)
    _edge(source="person_origen_alexandria_185_254ce_s9t0u1v2", target="person_gregory_nyssa_d395",
          relation="influences",
          metadata={"amand_evidence": "Amand 1945 p. 407-411 — Origenian inheritance deeper than on Basil"}),
    # Basil → Gregory of Nyssa (elder brother)
    _edge(source="person_basil_great_d379", target="person_gregory_nyssa_d395",
          relation="influences",
          metadata={"amand_evidence": "Amand 1945 p. 405-407 — elder brother & teacher in monasticism"}),
    # Gregory of Nazianzus → Gregory of Nyssa (Cappadocian chain via Philocalia)
    _edge(source="person_gregory_nazianzus_d389", target="person_gregory_nyssa_d395",
          relation="influences",
          metadata={"amand_evidence": "Amand 1945 p. 401-411 — Cappadocian milieu + Philocalia"}),
    # Diodore of Tarsus → John Chrysostom (teacher per Socrates HE VI.3)
    # Skip if person_diodore_tarsus doesn't exist; only declare if exists
    # Origen → Nemesius (via Comm. in Gen. for the encomium of man, Skard 1936)
    _edge(source="person_origen_alexandria_185_254ce_s9t0u1v2", target="person_nemesius_emesa_4c_ce",
          relation="influences",
          metadata={"amand_evidence": "Amand 1945 p. 553-555 — Comm. in Gen. source for ch. 1 anthropology"}),
    # Aristotle → Nemesius (EN III, 1-8 via lost Peripatetic commentary)
    _edge(source="person_aristotle_384_322bce_c2d4f6a8", target="person_nemesius_emesa_4c_ce",
          relation="influences",
          metadata={"amand_evidence": "Amand 1945 p. 553-562 — EN III, 1-8 via lost Peripatetic commentary 2nd-3rd c."}),
    # Posidonius → Nemesius (Peri pathon via Galen)
    _edge(source="person_posidonius_apameia_135_51bce", target="person_nemesius_emesa_4c_ce",
          relation="influences",
          metadata={"amand_evidence": "Amand 1945 p. 553-554 — Peri pathon via Galen"}),
    # Galen → Nemesius (anatomy, physiology, Peri apodeixeos)
    _edge(source="person_galen_pergamon_129_216ce", target="person_nemesius_emesa_4c_ce",
          relation="influences",
          metadata={"amand_evidence": "Amand 1945 p. 552-555 — anatomy, physiology, Peri apodeixeos"}),
    # Chrysostom → Pseudo-Chrysostom (stylistic continuity even if attribution doubtful)
    _edge(source="person_john_chrysostom_d407", target="person_pseudo_chrysostom_de_fato",
          relation="influences",
          metadata={"amand_evidence": "Amand 1945 p. 504-506 — De Fato influenced by authentic Chrysostomian preaching"}),
]


# =============================================================================
# 7. PRECEDES — Cappadocian work chain + witness chronology
# =============================================================================

PRECEDES_EDGES: list[dict[str, Any]] = [
    # Cappadocian work chain
    _edge(source="work_basil_hexaemeron", target="work_gregory_contra_fatum",
          relation="precedes",
          metadata={"amand_evidence": "Amand 1945 p. 405-411 — Hex VI.5-7 precedes Gr. Nysse CF in Cappadocian chain"}),
    _edge(source="work_gregory_contra_fatum", target="work_nemesius_de_nat_hom",
          relation="precedes",
          metadata={"amand_evidence": "Amand 1945 p. 549-552 — Gr. Nysse precedes Nemesius chronologically"}),
    # Witness chronology arguments
    _edge(source="argument_chrysostom_hom_goth_witness5_amand1945",
          target="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          relation="precedes",
          metadata={"amand_evidence": "Amand 1945 Ch. XII — witness 5 (authentic) before witness 6 (Ps-Chrys reuse)"}),
]


# =============================================================================
# 8. CRITIQUES — anti-fatalist arguments critique fatalism positions
# =============================================================================

CRITIQUES_EDGES: list[dict[str, Any]] = [
    # The Carneadean witness arguments critique fatalist arguments/concepts
    _edge(source="argument_chrysostom_hom_goth_witness5_amand1945",
          target="concept_heimarmene_fate_stoics_j0k1l2m3",
          relation="critiques",
          metadata={"amand_evidence": "Amand 1945 p. 510-525 — Hom. Goth ch. 6 critiques Stoic heimarmene"}),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="concept_heimarmene_fate_stoics_j0k1l2m3",
          relation="critiques",
          metadata={"amand_evidence": "Amand 1945 p. 525-532 — De Fato V critiques heimarmene"}),
    _edge(source="argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
          target="concept_heimarmene_fate_stoics_j0k1l2m3",
          relation="critiques",
          metadata={"amand_evidence": "Amand 1945 p. 568-569 — Nat. Hom. 35 dry summary critiques heimarmene"}),
    _edge(source="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
          target="concept_sympatheia_universal_posidonius_nyssa",
          relation="critiques",
          metadata={"amand_evidence": "Amand 1945 p. 423-424 — Gregory critiques Posidonian sympatheia"}),
]


# =============================================================================
# 9. EMPLOYS — arguments employ Carneadean concepts/topoi
# =============================================================================

EMPLOYS_EDGES: list[dict[str, Any]] = [
    # All witness arguments employ Carneadean topoi
    _edge(source="argument_chrysostom_hom_goth_witness5_amand1945",
          target="argument_carneadean_legislation_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 5 employs Carneadean topos of legislation futility"}),
    _edge(source="argument_chrysostom_hom_goth_witness5_amand1945",
          target="argument_carneadean_virtue_vice_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 5 employs Carneadean topos of virtue/vice indistinction"}),
    _edge(source="argument_chrysostom_hom_goth_witness5_amand1945",
          target="argument_carneadean_incentives_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 5 employs Carneadean topos of useless incentives/punishments"}),
    _edge(source="argument_chrysostom_hom_goth_witness5_amand1945",
          target="argument_carneadean_action_futility_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 5 employs Carneadean topos of action futility"}),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="argument_carneadean_general_theme_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 6 employs Carneadean general theme"}),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="argument_carneadean_legislation_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 6 employs Carneadean topos of legislation"}),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="argument_carneadean_virtue_vice_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 6 employs Carneadean topos of virtue/vice"}),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="argument_carneadean_incentives_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 6 employs Carneadean topos of incentives"}),
    _edge(source="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
          target="argument_carneadean_action_futility_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Witness 6 employs Carneadean topos of action futility"}),
    _edge(source="argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
          target="argument_carneadean_general_theme_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Nat. Hom. 35 dryly enumerates Carneadean consequences"}),
    _edge(source="argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
          target="argument_carneadean_legislation_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Nat. Hom. 35 employs Carneadean legislation topos"}),
    _edge(source="argument_gregory_disccat31_carneadean_moral_amand1945",
          target="argument_carneadean_virtue_vice_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Disc. cat. 31 condenses Carneadean virtue/vice topos"}),
    _edge(source="argument_gregory_disccat31_carneadean_moral_amand1945",
          target="argument_carneadean_incentives_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Disc. cat. 31 condenses Carneadean praise/blame topos"}),
    _edge(source="argument_gregory_contrafatum_catastrophes_amand1945",
          target="argument_carneadean_general_theme_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Gregory CF catastrophes argument is Carneadean (Amand p. 431)"}),
    _edge(source="argument_gregory_contrafatum_nomima_barbarika_amand1945",
          target="argument_carneadean_general_theme_amand1945",
          relation="employs",
          metadata={"amand_evidence": "Gregory CF nomima barbarika is Carneadean (Amand p. 431)"}),
    # Gregory CF pagan philosopher thesis employs Posidonian sympatheia
    _edge(source="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
          target="concept_sympatheia_universal_posidonius_nyssa",
          relation="employs",
          metadata={"amand_evidence": "Amand 1945 p. 423-424 — pagan philosopher employs Posidonian sympatheia"}),
    # Gregory Disc Cat 31 supports concept of prohairesis
    _edge(source="argument_gregory_disccat31_carneadean_moral_amand1945",
          target="concept_prohairesis_gregory_nyssa",
          relation="employs",
          metadata={"amand_evidence": "Amand 1945 p. 432 — Disc. cat. 31 employs prohairesis concept"}),
    # Nemesius argument employs to_eph_hemin
    _edge(source="argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
          target="concept_to_eph_hemin_nemesius",
          relation="employs",
          metadata={"amand_evidence": "Amand 1945 p. 568 — Nat. Hom. 35 employs to_eph_hemin"}),
]


# =============================================================================
# 10. INTERPRETS — Nemesius interprets Aristotle
# =============================================================================

INTERPRETS_EDGES: list[dict[str, Any]] = [
    _edge(source="person_nemesius_emesa_4c_ce", target="person_aristotle_384_322bce_c2d4f6a8",
          relation="interprets",
          metadata={"amand_evidence": "Amand 1945 p. 558-562 — Nat. Hom. 29-34 and 39-41 follow Aristotle EN III"}),
]


# =============================================================================
# 11. RESPONDS_TO — witness arguments respond to fatalist positions
# =============================================================================

RESPONDS_TO_EDGES: list[dict[str, Any]] = [
    _edge(source="argument_gregory_contrafatum_catastrophes_amand1945",
          target="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
          relation="responds_to",
          metadata={"amand_evidence": "Amand 1945 p. 423-431 — Gregory's 23 arguments respond to pagan thesis"}),
    _edge(source="argument_gregory_contrafatum_diversity_destinies_amand1945",
          target="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
          relation="responds_to",
          metadata={"amand_evidence": "Amand 1945 p. 425-426 — diversity argument refutes integral fatalism"}),
    _edge(source="argument_gregory_contrafatum_nomima_barbarika_amand1945",
          target="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
          relation="responds_to",
          metadata={"amand_evidence": "Amand 1945 p. 428-429 — nomima barbarika refutes astrological fatalism"}),
]


# =============================================================================
# 12. SUPPORTS — arguments supporting concepts (prohairesis, autexousion, to_eph_hemin)
# =============================================================================

SUPPORTS_EDGES: list[dict[str, Any]] = [
    _edge(source="argument_gregory_disccat31_carneadean_moral_amand1945",
          target="concept_autexousion_christian",
          relation="supports",
          metadata={"amand_evidence": "Amand 1945 p. 432-435 — Disc. cat. 31 supports autexousion"}),
    _edge(source="argument_chrysostom_libre_arbitre_pastoral_amand1945",
          target="concept_autexousion_christian",
          relation="supports",
          metadata={"amand_evidence": "Amand 1945 p. 491-501 — Chrysostom's libre arbitre is autexousion"}),
]


# =============================================================================
# 13. BELONGS_TO_SCHOOL — Pseudo-Chrysostom is not a school but Nemesius can be Neoplatonist
# =============================================================================
# Skip if school_neoplatonism doesn't exist — handled by missing-target skip in apply.

BELONGS_TO_SCHOOL_EDGES: list[dict[str, Any]] = [
    # Nemesius is eclectic but his dominant tendency per Amand is Neoplatonist
    # Use influenced_by school if school_neoplatonism exists
]


# =============================================================================
# AGGREGATE
# =============================================================================

NEW_EDGES: list[dict[str, Any]] = (
    AUTHORED_BY_EDGES
    + CONTAINS_EDGES
    + EVIDENCED_BY_EDGES
    + CITES_PRIMARY_SOURCE_EDGES
    + SYNTHESIS_DISCUSSES_EDGES
    + INFLUENCES_EDGES
    + PRECEDES_EDGES
    + CRITIQUES_EDGES
    + EMPLOYS_EDGES
    + INTERPRETS_EDGES
    + RESPONDS_TO_EDGES
    + SUPPORTS_EDGES
    + BELONGS_TO_SCHOOL_EDGES
)
