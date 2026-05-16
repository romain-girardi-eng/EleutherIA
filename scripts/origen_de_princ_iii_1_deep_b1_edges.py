"""Origen De Princ III.1 deep batch B1 — NEW_EDGES.

Three categories :

  1. STRUCTURAL part_of edges (27 = 23 De Princ shells + 4 Philocalia
     sub-anchors)
       passage_origen_pa_3_1_<n>           -> work_de_principiis_origen_230s_v2w3x4y5
       passage_origen_philocalia_21_<n>    -> work_origen_philocalia

  2. CITATION cites_primary_source edges (~50-60)
       <scholar argument/publication> -> <specific passage>
     Hangs each argument on the section it specifically references, based on
     metadata in the existing nodes (audited at planning step).

  3. INTERPRETATION interprets edges (a few key Furst arguments anchor
     directly on the Philocalia Greek anchors when they cite the Greek
     terminology specifically — kept minimal to avoid duplication with
     cites_primary_source).

Allowed relations per knowledge graph/ontology/edge_types.json :
  cites_primary_source : src argument/publication/person -> tgt passage/work
  part_of              : src argument/concept/passage/synthesis/text_fragment/work
                         -> tgt concept/passage/work/source_collection
  interprets           : src argument/person/publication/modern_interpretation/work
                         -> tgt argument/argument_framework/concept/passage/person/school/work
  discusses            : src argument/argument_framework/concept/conceptual_evolution/debate/
                         passage/person/publication/synthesis/work
                         -> tgt argument/concept/debate/group/person/school/synthesis/work
                         (NB : synthesis -> passage is NOT allowed by ontology ;
                          synthesis nodes anchor to WORK level only, not passage.)
"""
from __future__ import annotations

from typing import Any

NEW_EDGES: list[dict[str, Any]] = []


def _edge(
    source: str,
    target: str,
    relation: str,
    *,
    confidence: float = 0.85,
    **md: Any,
) -> dict[str, Any]:
    e: dict[str, Any] = {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": confidence,
    }
    if md:
        e["metadata"] = md
    return e


WORK_DE_PRINC = "work_de_principiis_origen_230s_v2w3x4y5"
WORK_PHILOCALIA = "work_origen_philocalia"

DE_PRINC_SHELL_SECTIONS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                            17, 18, 19, 20, 21, 22, 23, 24]
PHILOC_SHELL_SECTIONS = [5, 7, 18, 23]

BATCH_TAG = {"wave": "origen_de_princ_iii_1_deep_b1_2026-05-16"}


# =============================================================================
# 1. STRUCTURAL part_of edges (27)
# =============================================================================
# 23 De Princ shells -> De Principiis work
for n in DE_PRINC_SHELL_SECTIONS:
    NEW_EDGES.append(
        _edge(
            f"passage_origen_pa_3_1_{n}",
            WORK_DE_PRINC,
            "part_of",
            confidence=1.0,
            **BATCH_TAG,
        )
    )

# 4 Philocalia 21 sub-anchors -> Philocalia work
for n in PHILOC_SHELL_SECTIONS:
    NEW_EDGES.append(
        _edge(
            f"passage_origen_philocalia_21_{n}",
            WORK_PHILOCALIA,
            "part_of",
            confidence=1.0,
            **BATCH_TAG,
        )
    )

# Philocalia anchors also discuss the De Princ section they parallel
# (passage -> work_de_principiis : structural pointer not allowed via part_of
#  to a non-containing work ; use `discusses` instead at the passage level
#  to express "this Greek excerpt is the Greek text of De Princ III.1.<n>").
# Ontology check : discusses src can be `passage` ; target can be `work`. OK.
for n in PHILOC_SHELL_SECTIONS:
    NEW_EDGES.append(
        _edge(
            f"passage_origen_philocalia_21_{n}",
            WORK_DE_PRINC,
            "discusses",
            confidence=1.0,
            note=f"Philocalia 21.{n} preserves the Greek of De Princ III.1.{n}",
            **BATCH_TAG,
        )
    )


# =============================================================================
# 2. CITATION cites_primary_source edges — scholar arguments to specific
#    passage shells. Refs drawn from existing node descriptions audited at
#    planning step.
# =============================================================================
# Notation: _cite(arg_id, section_num, [philoc_too]=False, **md)

def _cite(
    arg_id: str,
    section_num: int,
    *,
    also_philocalia: bool = False,
    confidence: float = 0.9,
    **md: Any,
) -> list[dict[str, Any]]:
    """Build cites_primary_source edges for a scholar arg on a given section.

    If `also_philocalia=True` and the section has a Philocalia sub-anchor
    (§§5, 7, 18, 23), also add a cite on the Philocalia anchor.
    """
    edges = [
        _edge(
            arg_id,
            f"passage_origen_pa_3_1_{section_num}",
            "cites_primary_source",
            confidence=confidence,
            **BATCH_TAG,
            **md,
        )
    ]
    if also_philocalia and section_num in PHILOC_SHELL_SECTIONS:
        edges.append(
            _edge(
                arg_id,
                f"passage_origen_philocalia_21_{section_num}",
                "cites_primary_source",
                confidence=confidence,
                **BATCH_TAG,
                **md,
            )
        )
    return edges


# -----------------------------------------------------------------------------
# 2.A Amand 1945 — Origen witness arguments
# -----------------------------------------------------------------------------
# argument_origen_witness_preexistence_souls_amand1945 cites :
#   - Princ. III.1.19-20 (Esau-Jacob, preexistence locus)
#   - Princ. II.9.6 (extra-treatise, NOT covered here ; left at work level)
NEW_EDGES.extend(_cite("argument_origen_witness_preexistence_souls_amand1945", 19,
                       note="Esau-Jacob preexistence locus, Rom 9:11-13"))
NEW_EDGES.extend(_cite("argument_origen_witness_preexistence_souls_amand1945", 20,
                       confidence=0.85))

# argument_origen_witness_double_freedom_amand1945 cites :
#   - Princ. III.6,1 (extra-treatise, NOT covered) — formal/real freedom
#   - But indirectly draws on III.1.3 (already exists) for the formal-freedom
#     concept ; we add a cite on existing §3 + §4 (assent/judgment).
NEW_EDGES.append(
    _edge(
        "argument_origen_witness_double_freedom_amand1945",
        "passage_origen_pa_3_1_3",
        "cites_primary_source",
        confidence=0.85,
        note="Formal freedom = autexousios krisis (Amand p. 304 + n. 2 implicates III.1.3 as the locus where formal freedom is defined before being thematised in III.6,1)",
        **BATCH_TAG,
    )
)
NEW_EDGES.extend(_cite("argument_origen_witness_double_freedom_amand1945", 4,
                       confidence=0.8,
                       note="Continuation of the formal-freedom analysis (assent/response)"))

# argument_origen_witness_personality_anti_unilateral_amand1945 cites :
#   - De Princ. PREFACE (not in III.1) — left at work level.
#   - But the principle articulated in the preface is operative throughout
#     III.1 ; we add a cite on §1 (programmatic prologue) where the
#     methodological stance is restated.
NEW_EDGES.extend(_cite("argument_origen_witness_personality_anti_unilateral_amand1945", 1,
                       confidence=0.75,
                       note="Programmatic prologue restates the rule (preface vs III.1 distinction in Amand p. 279)"))


# -----------------------------------------------------------------------------
# 2.B Frede 2011 — Origen-Stoic-Christianity-Anti-Gnostic argument
# -----------------------------------------------------------------------------
# argument_frede_2011_origen_stoic_christianity_anti_gnostic — Frede p. 113 :
# "could have been taken straight from a late Stoic handbook" referring to
# III.1.2-3 specifically.
NEW_EDGES.append(
    _edge(
        "argument_frede_2011_origen_stoic_christianity_anti_gnostic",
        "passage_origen_pa_3_1_2",
        "cites_primary_source",
        confidence=0.95,
        note="Frede 2011 p. 113 : III.1.2 ('four modes of motion') is one of the two passages cited as 'taken straight from a late Stoic handbook'",
        **BATCH_TAG,
    )
)
NEW_EDGES.append(
    _edge(
        "argument_frede_2011_origen_stoic_christianity_anti_gnostic",
        "passage_origen_pa_3_1_3",
        "cites_primary_source",
        confidence=0.95,
        note="Frede 2011 p. 113 : III.1.3 ('self-determining judgment') is the second 'Stoic handbook' passage",
        **BATCH_TAG,
    )
)
NEW_EDGES.extend(_cite("argument_frede_2011_origen_stoic_christianity_anti_gnostic", 4,
                       confidence=0.9,
                       note="Frede 2011 — assent/synkatathesis core of the Stoic action-theory adoption"))
# anti-Gnostic locus :
NEW_EDGES.extend(_cite("argument_frede_2011_origen_stoic_christianity_anti_gnostic", 6,
                       confidence=0.9,
                       note="Frede 2011 — anti-Valentinian/Basilidean refutation"))
# universalist locus (apokatastasis) :
NEW_EDGES.extend(_cite("argument_frede_2011_origen_stoic_christianity_anti_gnostic", 23,
                       confidence=0.95,
                       also_philocalia=True,
                       note="Frede 2011 p. 117 — freedom retained even by demons (universalist horizon)"))

# pub_frede_2011_free_will — the monograph as a whole cites the work ;
# also anchor on the structural-pillar sections :
NEW_EDGES.extend(_cite("pub_frede_2011_free_will", 2,
                       confidence=0.95,
                       note="Frede 2011 Ch. 7 p. 113 — four modes of motion"))
NEW_EDGES.extend(_cite("pub_frede_2011_free_will", 6,
                       confidence=0.9,
                       note="Frede 2011 Ch. 7 — anti-Gnostic motivation"))
NEW_EDGES.extend(_cite("pub_frede_2011_free_will", 23,
                       confidence=0.95,
                       also_philocalia=True,
                       note="Frede 2011 Ch. 7 p. 117 — universalist horizon distinguishing Origen from Stoic compatibilism"))


# -----------------------------------------------------------------------------
# 2.C Fürst 2022 — multiple arguments
# -----------------------------------------------------------------------------
# argument_furst_2022_origen_culmination_autexousion — citing III.1.1
# explicitly ("the question of highest importance, develop the concept")
NEW_EDGES.extend(_cite("argument_furst_2022_origen_culmination_autexousion", 1,
                       confidence=0.95,
                       note="Furst 2022 Kap. V 2 p. 195-216 — Princ. III 1,1 'question d'importance suprême ; développer le concept (ἔννοια)'"))

# argument_furst_2022_de_princ_iii_1_first_freedom_treatise — anchors on
# the whole treatise. Anchor on §1 (incipit), §3 (existing canonical),
# §24 (conclusion).
NEW_EDGES.extend(_cite("argument_furst_2022_de_princ_iii_1_first_freedom_treatise", 1,
                       confidence=0.95,
                       note="Furst 2022 Kap. V 2 p. 196-197 — incipit of the first 'On Freedom' treatise"))
NEW_EDGES.append(
    _edge(
        "argument_furst_2022_de_princ_iii_1_first_freedom_treatise",
        "passage_origen_pa_3_1_3",
        "cites_primary_source",
        confidence=0.95,
        note="Furst 2022 — autexousios krisis as the technical core of the treatise",
        **BATCH_TAG,
    )
)
NEW_EDGES.extend(_cite("argument_furst_2022_de_princ_iii_1_first_freedom_treatise", 24,
                       confidence=0.9,
                       note="Furst 2022 — conclusion of the first systematic Sur la liberte"))

# argument_furst_2022_origen_against_three_determinisms — explicit refs :
#   - Princ. I praef. 5 (NOT in III.1, work-level only)
#   - Princ. III.1,4 ff. (Stoic determinism)
#   - Princ. III.1,6 (Gnostic determinism)
#   - In Gen. frg. D 7 = Philocalia 23 (NOT in III.1)
NEW_EDGES.extend(_cite("argument_furst_2022_origen_against_three_determinisms", 4,
                       confidence=0.95,
                       note="Furst 2022 Kap. V 1 p. 188-192 — Princ. III 1,4 ss : déterminisme causal stoïcien"))
NEW_EDGES.extend(_cite("argument_furst_2022_origen_against_three_determinisms", 5,
                       confidence=0.9,
                       also_philocalia=True,
                       note="Furst 2022 — anti-astrological argument (continuation in In Gen.)"))
NEW_EDGES.extend(_cite("argument_furst_2022_origen_against_three_determinisms", 6,
                       confidence=0.95,
                       note="Furst 2022 Kap. V 1 — Princ. III 1,6 : déterminisme théologique gnostique"))

# argument_furst_2022_world_as_network_of_freedoms — Zum Ausklang +
# Kap. VI 4 ; not anchored on a single section but on the dynamic theology
# spread through III.1.18 (theodicy) + III.1.23 (universalist horizon).
NEW_EDGES.extend(_cite("argument_furst_2022_world_as_network_of_freedoms", 18,
                       confidence=0.85,
                       note="Furst 2022 Zum Ausklang p. 291-292 — God-and-creature dynamic order presupposes pedagogical theodicy"))
NEW_EDGES.extend(_cite("argument_furst_2022_world_as_network_of_freedoms", 23,
                       confidence=0.85,
                       also_philocalia=True,
                       note="Furst 2022 — universalist horizon = eirmos of interconnected freedoms"))

# argument_furst_2022_freedom_principle_of_substance — Hengstermann 2016 +
# Furst Kap. VI 1. Ontological reading anchored on §2 (four modes) + §3
# (autexousios krisis) + §6 (anti-Gnostic equality of natures).
NEW_EDGES.extend(_cite("argument_furst_2022_freedom_principle_of_substance", 2,
                       confidence=0.9,
                       note="Furst 2022 Kap. VI 1 p. 252-254 — four-mode classification grounds the ontologisation of freedom"))
NEW_EDGES.append(
    _edge(
        "argument_furst_2022_freedom_principle_of_substance",
        "passage_origen_pa_3_1_3",
        "cites_primary_source",
        confidence=0.95,
        note="Furst 2022 — III.1.3 as the technical-definition locus from which the substance-principle reading proceeds",
        **BATCH_TAG,
    )
)
NEW_EDGES.extend(_cite("argument_furst_2022_freedom_principle_of_substance", 6,
                       confidence=0.85,
                       note="Furst 2022 — anti-Gnostic equality of rational creatures is the ontological corollary of freedom = principle of substance"))

# argument_furst_2022_kompatibilistischer_libertarismus — Furst Kap. VI 4 :
# kompatibilistischer Libertarismus. Anchored on §4 (Stoic frame accepted) +
# §18 (theodicy) + §23 (universalist apex) + §3 (autexousios krisis).
NEW_EDGES.append(
    _edge(
        "argument_furst_2022_kompatibilistischer_libertarismus",
        "passage_origen_pa_3_1_3",
        "cites_primary_source",
        confidence=0.95,
        note="Furst 2022 Kap. VI 4 — III.1.3 autexousios krisis as the technical core of compatibilist libertarianism",
        **BATCH_TAG,
    )
)
NEW_EDGES.extend(_cite("argument_furst_2022_kompatibilistischer_libertarismus", 4,
                       confidence=0.9,
                       note="Furst 2022 Kap. VI 4 — Stoic-frame acceptance"))
NEW_EDGES.extend(_cite("argument_furst_2022_kompatibilistischer_libertarismus", 18,
                       confidence=0.95,
                       also_philocalia=True,
                       note="Furst 2022 Kap. VI 4 — pedagogical theodicy as the structural keystone of compatibilist libertarianism"))
NEW_EDGES.extend(_cite("argument_furst_2022_kompatibilistischer_libertarismus", 23,
                       confidence=0.9,
                       also_philocalia=True,
                       note="Furst 2022 Kap. VI 4 — universalist horizon : freedom retained even by demons"))

# pub_furst_2022_wege_freiheit — anchor publication on the 3 keystone sections
NEW_EDGES.extend(_cite("pub_furst_2022_wege_freiheit", 1,
                       confidence=0.95,
                       note="Furst 2022 Kap. V — incipit of the treatise"))
NEW_EDGES.extend(_cite("pub_furst_2022_wege_freiheit", 2,
                       confidence=0.95,
                       note="Furst 2022 Kap. V — four modes of motion"))
NEW_EDGES.extend(_cite("pub_furst_2022_wege_freiheit", 18,
                       confidence=0.9,
                       also_philocalia=True,
                       note="Furst 2022 Kap. VI — pedagogical theodicy"))
NEW_EDGES.extend(_cite("pub_furst_2022_wege_freiheit", 23,
                       confidence=0.9,
                       also_philocalia=True,
                       note="Furst 2022 Zum Ausklang — universalist horizon"))


# -----------------------------------------------------------------------------
# 2.D Synthesis nodes (synthesis -> work_de_principiis via discusses ;
#     ontology forbids synthesis -> passage)
# -----------------------------------------------------------------------------
# synthesis_frede2011_ch7_origen, synthesis_furst2022_origen_central_freedom
# already point to work_de_principiis at work level (or should).
# We re-add the discusses-work edges defensively (idempotent — duplicates
# are skipped by apply orchestrator).
NEW_EDGES.append(
    _edge(
        "synthesis_frede2011_ch7_origen",
        WORK_DE_PRINC,
        "discusses",
        confidence=0.95,
        note="Frede 2011 Ch. 7 synthesises De Principiis III.1 (preserved Greek Philocalia 21-27)",
        **BATCH_TAG,
    )
)
NEW_EDGES.append(
    _edge(
        "synthesis_frede2011_ch7_origen",
        WORK_PHILOCALIA,
        "discusses",
        confidence=0.95,
        note="Frede 2011 Ch. 7 — Philocalia is the principal Greek witness",
        **BATCH_TAG,
    )
)
NEW_EDGES.append(
    _edge(
        "synthesis_furst2022_origen_central_freedom",
        WORK_DE_PRINC,
        "discusses",
        confidence=0.95,
        note="Furst 2022 Kap. V synthesises De Principiis III.1 = the first 'On Freedom' treatise",
        **BATCH_TAG,
    )
)
NEW_EDGES.append(
    _edge(
        "synthesis_furst2022_origen_central_freedom",
        WORK_PHILOCALIA,
        "discusses",
        confidence=0.9,
        note="Furst 2022 — Philocalie 21-27 = Freiheitstraktat en grec",
        **BATCH_TAG,
    )
)


# -----------------------------------------------------------------------------
# 2.E Concept evidenced_by — anchor key Origenist concepts on shells
# -----------------------------------------------------------------------------
# concept_autexousion_christian_freedom_u1v2w3x4 already pointed to §3.
# Add the anti-determinist evidence anchors.
NEW_EDGES.append(
    _edge(
        "concept_autexousion_christian_freedom_u1v2w3x4",
        "passage_origen_pa_3_1_1",
        "evidenced_by",
        confidence=0.9,
        note="Programmatic incipit demands development of the autexousion concept",
        **BATCH_TAG,
    )
)
NEW_EDGES.append(
    _edge(
        "concept_autexousion_christian_freedom_u1v2w3x4",
        "passage_origen_pa_3_1_2",
        "evidenced_by",
        confidence=0.9,
        note="Four-mode classification of motion : autexousion = dia hautou movement",
        **BATCH_TAG,
    )
)
NEW_EDGES.append(
    _edge(
        "concept_autexousion_christian_freedom_u1v2w3x4",
        "passage_origen_pa_3_1_24",
        "evidenced_by",
        confidence=0.85,
        note="Concluding summary of the autexousion doctrine",
        **BATCH_TAG,
    )
)
