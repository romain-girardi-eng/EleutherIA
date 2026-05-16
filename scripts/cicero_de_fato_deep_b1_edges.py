"""Cicero De Fato deep B1 — NEW_EDGES list.

Anchor 15+ scholar nodes at PASSAGE level for Cicero, De Fato (44 BCE).
Each scholar already had work-level edges to `work_de_fato_cicero_44bce_b9c4e5d2`
(or to a passage subset for Bobzien cylinder). We add precise §-level
`cites_primary_source` edges with rich metadata.

Ontology constraints (knowledge graph/ontology/edge_types.json) :
- cites_primary_source : src {argument | publication | person} -> tgt {passage | work}
- evidenced_by         : src {argument | concept | group | school} -> tgt {passage}
- discusses            : src {... synthesis ...} -> tgt {... NOT passage ...}
- interprets           : src {argument | publication | ...} -> tgt {... passage ...}

=> Syntheses CANNOT directly cite passages. We anchor them via the arguments
   they discuss (which DO cite passages) and via discusses->work edges that
   already exist.

Passage prefix used : `passage_cic_fat_<N>` (Latin canonical text, the prefix
already targeted by existing Bobzien cylinder edges). Parallel
`passage_cicero_fat_<N>` (curated EN + Latin) also exists but we stay
consistent with the prefix already in use to avoid splitting the citation
graph across two synonymous IDs.

Section mapping rationale :
- §7-11   Master Argument set-up (Diodorus vs Chrysippus)
- §12-14  Chrysippus on possibility / modality / past necessity
- §15-17  Diodorus's full statement, Carneadean assent chain (§17)
- §18-21  Sea battle / Scipio's death / future necessity / Epicurean swerve
- §23-25  Carneades on internal voluntary motion (motus animi voluntarius)
- §26-31  Lazy Argument + co-fated reply
- §32-33  Future-truth without natural causation (Carneadean modal argument)
- §34-38  Cicero's positio, divination, Epicurean clinamen critique
- §39-44  Chrysippean cylinder, perfect/auxiliary causes, in nostra potestate
- §45-48  Closing summary (last paragraph)
"""
from __future__ import annotations

from typing import Any

from cicero_de_fato_deep_b1_utils import PASSAGE_PREFIX, WORK_ID

NEW_EDGES: list[dict[str, Any]] = []


def _passage(section: int) -> str:
    """Return the canonical passage ID for De Fato §section."""
    return f"{PASSAGE_PREFIX}{section}"


def _cite(
    source: str,
    sections: list[int],
    *,
    scholar: str,
    original_citation: str,
    confidence: float = 0.9,
    relation: str = "cites_primary_source",
    note: str | None = None,
) -> None:
    """Add cites_primary_source edges from `source` to each §section.

    All edges carry metadata locating the citation in the scholarly source.
    """
    for sec in sections:
        e: dict[str, Any] = {
            "source": source,
            "target": _passage(sec),
            "relation": relation,
            "confidence": confidence,
            "metadata": {
                "scholar": scholar,
                "original_citation": original_citation,
                "anchored_in_batch": "cicero_de_fato_deep_b1",
                "ancient_locus": f"Cic. Fat. {sec}",
            },
        }
        if note:
            e["metadata"]["note"] = note
        NEW_EDGES.append(e)


# =============================================================================
# 1. BOBZIEN 2001 — three argument nodes, each with precise § coverage
#    (cylinder §39-44 already exists in KG ; we add §32-33 + extend coverage)
# =============================================================================

# --- 1a. Cylinder reconstruction : extend §32-33 (Carneadean foil) + §41 already
#         covered by existing edges. We add §32 (eternal truth vs causation) and
#         §33 (limits of foreknowledge) which Bobzien §6.3.3 uses to contrast
#         Chrysippean cylinder with the broader modal architecture.
_cite(
    "argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction",
    [32, 33],
    scholar="Bobzien 2001",
    original_citation="Bobzien 2001 §6.3.3 (Determinism and Freedom, p. 258-271)",
    confidence=0.85,
    note="Carneadean foil to Chrysippean cylinder reading : eternal truth need not require natural causation",
)

# --- 1b. Chrysippean modal system §3.1.4 + §3.4 — anchors at the §11-17
#         possibility/necessity passages
_cite(
    "argument_bobzien_2001_b1_chrysippean_modal_system",
    [11, 12, 13, 14, 17],
    scholar="Bobzien 2001",
    original_citation="Bobzien 2001 §3.1.4 (p. 112-122) + §3.4 (p. 136-143)",
    confidence=0.9,
    note="Possibility / necessity / past-truth — Chrysippus vs Diodorus / Cleanthes",
)

# --- 1c. Sea Battle / bivalence §2.1 (p. 59-86)
#         The Chrysippean acceptance of bivalence comes through in §18-21
#         (Scipio passage + future truth necessity), not Cic. Fat. §11
#         (which is the Master-Argument set-up).
_cite(
    "argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence",
    [18, 19, 20, 21],
    scholar="Bobzien 2001",
    original_citation="Bobzien 2001 §2.1 (p. 59-86)",
    confidence=0.9,
    note="Chrysippean bivalence : Scipio passage + future truth as immutable",
)


# =============================================================================
# 2. CARNEADEAN ASSENT CHAIN (Amand 1945, p. 79-80) — the *centerpiece* of
#    Amand's reconstruction. The argument explicitly references Cic. Fat. 17,
#    40 — already anchored via `evidenced_by`. We extend to §40 via
#    cites_primary_source (ontology-conformant for argument->passage) and add
#    §39 + §41 which Amand p. 78 ll. 5135-5158 invokes as the Stoic
#    counter-position the Carneadean chain attacks.
# =============================================================================
_cite(
    "argument_carneadean_assent_chain_via_cicero_amand1945",
    [17, 40],
    scholar="Amand 1945",
    original_citation="Amand 1945, p. 79-80 ll. 5169-5206 (citing Cic. Fat. 17 + 40)",
    confidence=0.95,
    note="Primary witness passages for the Carneadean fatal-chain argument",
)
_cite(
    "argument_carneadean_assent_chain_via_cicero_amand1945",
    [39, 41],
    scholar="Amand 1945",
    original_citation="Amand 1945, p. 78-79 ll. 5135-5158 (Stoic counter-position)",
    confidence=0.8,
    relation="interprets",
    note="Chrysippean cylinder / cause-distinction = position the Carneadean chain attacks",
)


# =============================================================================
# 3. SHARPLES 1991 — Cicero: On Fate & Boethius: Consolation
#    The Sharples commentary covers the entire surviving De Fato §1-48. We
#    anchor him to the structural high-points (Master Argument, Carneades,
#    Lazy Argument, cylinder, closing) — 16 § anchors that together represent
#    the lemmata of his commentary chapters.
# =============================================================================
SHARPLES_SECTIONS = [
    7, 11, 12, 13, 17,         # Master Argument & possibility (commentary p. 8-12 / p. 173-179)
    18, 20,                    # Future contingents / Scipio
    23, 24, 25,                # Carneades on internal voluntary motion (p. 181-184)
    28, 30,                    # Lazy Argument & cofatalia (p. 186-188)
    32, 33,                    # Future truth without natural causation
    39, 40, 41, 42, 43, 44,    # Chrysippean cylinder (p. 192-198)
    45, 48,                    # Closing
]
_cite(
    "pub_sharples_1991_cicero_boethius",
    SHARPLES_SECTIONS,
    scholar="Sharples 1991",
    original_citation="R.W. Sharples (ed., tr.), Cicero, On Fate (De Fato) (1991), commentary on §-by-§ lemmata",
    confidence=0.95,
    note="Sharples 1991 provides English translation + lemma-by-lemma commentary on Cic. Fat. 1-48",
)


# =============================================================================
# 4. FREDE 2011 — A Free Will: Origins of the Notion in Ancient Thought
#    Frede engages De Fato chiefly for : (a) Chrysippus on assent in nostra
#    potestate §40-44, (b) the Carneadean §23-25 voluntary-motion passage as
#    the locus that *Alexander* later weaponizes into the "could have done
#    otherwise" libertarian dead-end he diagnoses Frede 2011 ch. 6, p. 95-101.
# =============================================================================
_cite(
    "pub_frede_2011_free_will",
    [23, 24, 25, 40, 41, 42, 43, 44],
    scholar="Frede 2011",
    original_citation="Frede 2011, A Free Will (Sather 68), ch. 4-6 esp. p. 71-78 (assent) and p. 95-101 (Alexander as Carneadean heir)",
    confidence=0.85,
    note="Carneadean §23-25 + Chrysippean cylinder §40-44 as the loci of the Hellenistic prehistory of Epictetan prohairesis",
)

_cite(
    "argument_frede_2011_alexander_libertarian_dead_end",
    [23, 24, 25],
    scholar="Frede 2011",
    original_citation="Frede 2011 ch. 6 (p. 95-101) + Conclusion p. 177-178",
    confidence=0.85,
    note="Carneadean motus animi voluntarius §23-25 = locus where the 'could have done otherwise' temptation Frede diagnoses in Alexander is first hinted at via Cicero",
)


# =============================================================================
# 5. DESTRÉE / SALLES / ZINGANO 2014 — What is Up to Us
#    Two of the volume's chapters target Cic. Fat. directly :
#    ch. 9 Gourinat (in nostra potestate, p. 169-181) and ch. 15 Maso (motus
#    animi voluntarius, p. 283-300).
# =============================================================================
# --- 5a. Volume-level anchoring for all sections discussed by either chapter
DSZ_2014_SECTIONS = [
    20, 23, 24, 25,            # Maso ch. 15 motus animi voluntarius (14× in De Fato)
    39, 40, 41, 42, 43, 44,    # Gourinat ch. 9 in nostra potestate / Chrysippus assent
]
_cite(
    "pub_destree_salles_zingano_2014_what_is_up_to_us",
    DSZ_2014_SECTIONS,
    scholar="Destrée / Salles / Zingano 2014",
    original_citation="Destrée, Salles & Zingano (eds.), What is Up to Us (Academia Verlag, 2014), chs. 9 + 15",
    confidence=0.85,
    note="Volume-level citation routed through chapters 9 (Gourinat) and 15 (Maso)",
)

# --- 5b. Gourinat 2014 ch. 9 argument : in nostra potestate (Cic.) =/= eph' hêmin (Gk)
#         The argument depends on the *frequency* of in nostra potestate in De
#         Fato — Maso 2014 counts 14 occurrences ; the densest cluster is
#         §39-44 (Chrysippean cylinder + assent), with §25 the Carneadean
#         occurrence Gourinat treats as semantically distinct.
_cite(
    "argument_gourinat_2014_in_nostra_potestate_not_eph_hemin",
    [25, 39, 40, 41, 42, 43, 44],
    scholar="Gourinat 2014",
    original_citation="Gourinat in Destrée 2014 ch. 9, p. 169-181",
    confidence=0.9,
    note="In nostra potestate cluster + Carneadean §25 contrast",
)

# --- 5c. Maso 2014 ch. 15 — motus animi voluntarius 14× in De Fato
#         Documented loci : §23-25 (Carneades' positive use), §20 (Scipio
#         passage — voluntary action vs necessity), §40 (the in nostra
#         potestate / assent cluster), and the §44-46 closing where Cicero
#         situates the Epicurean alternative.
_cite(
    "argument_maso_2014_cicero_motus_animi_voluntarius_independence",
    [20, 23, 24, 25, 40, 44, 45, 46],
    scholar="Maso 2014",
    original_citation="Maso in Destrée 2014 ch. 15, p. 283-300",
    confidence=0.9,
    note="14× occurrences of motus animi voluntarius in De Fato + 1× in Tusc. 4.79",
)


# =============================================================================
# 6. FÜRST 2022 — Wege zur Freiheit + the Carneades-introduces-voluntas argument
#    Fürst Kap. II 6 (p. 96-100) explicitly cites De Fato 23-25 for Carneades'
#    introduction of voluntas as cause non-extérieure. Kap. V 2 (p. 196-197)
#    uses De Fato as the contrast — Cicero still writes "On Fate" whereas
#    Origen will inaugurate "On Free Will".
# =============================================================================
_cite(
    "pub_furst_2022_wege_freiheit",
    [23, 24, 25],
    scholar="Fürst 2022",
    original_citation="Fürst 2022, Wege zur Freiheit (Mohr Siebeck), Kap. II 6 (p. 96-100)",
    confidence=0.95,
    note="Carneadean voluntas / motus animi voluntarius locus",
)

_cite(
    "argument_furst_2022_de_princ_iii_1_first_freedom_treatise",
    [23, 24, 25, 39, 40, 41],
    scholar="Fürst 2022",
    original_citation="Fürst 2022 Kap. V 2 (p. 196-197) + Kap. II 6 (p. 96-100)",
    confidence=0.85,
    note="De Fato = Hellenistic genre Cicero still writes ; Origen will inaugurate Peri autexousiou. Carneadean §23-25 + Chrysippean cylinder §39-41 = the Hellenistic baseline Origen transforms",
)


# =============================================================================
# 7. LEGACY scholarly_argument_* nodes (currently orphans — anchor + author).
#    These pre-date the structured pub_* / argument_* schema.
# =============================================================================

# --- 7a. Donini : Cicero's claim that Aristotle was in a certain sense a
#         determinist should be traced to Carneades via Clitomachus, not
#         Antiochus. Locus : the passage list Cicero attributes to "the old
#         philosophers" §39 (Democritus + Heraclitus + Empedocles + Aristotle).
_cite(
    "scholarly_argument_donini_cicero_s_de_fato_and_aristotle_5",
    [39],
    scholar="Donini",
    original_citation="Donini on Cic. Fat. 39 (Aristotle in the determinist group)",
    confidence=0.85,
    note="Cicero lists Aristotle alongside Democritus / Heraclitus / Empedocles as a determinist of sorts (§39)",
)

# --- 7b. Gourinat (legacy) : Cicero's critique of Chrysippus's assent doctrine
#         — locus : §40-44 (assent in nostra potestate + cylinder).
_cite(
    "scholarly_argument_gourinat_cicero_s_critique_of_chrysippu_2",
    [40, 41, 42, 43, 44],
    scholar="Gourinat (legacy node)",
    original_citation="Gourinat on Cic. Fat. 40-44 (Chrysippean assent + cylinder)",
    confidence=0.85,
    note="Cicero's diagnosis : Chrysippus must withdraw assent from fate, abandoning his fatalist position",
)

# --- 7c. Sorabji : Cicero follows Lucretius defending free will against the
#         Stoics — Lucretius parallel is the clinamen / motus animi voluntarius
#         cluster §22-25.
_cite(
    "scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4",
    [22, 23, 24, 25],
    scholar="Sorabji",
    original_citation="Sorabji on Cic. Fat. 22-25 (Lucretian clinamen parallel)",
    confidence=0.85,
    note="Carneadean / Epicurean clinamen cluster Cicero engages",
)


# =============================================================================
# 8. AMAND 1945 syntheses — ONTOLOGY-CONFORMANT routing.
#    Syntheses cannot cites_primary_source -> passage. Two avenues remain :
#    (a) the synthesis's own discusses->work edge already exists at work level ;
#    (b) we add evidence-routing via the *argument* the synthesis discusses
#        (argument_carneadean_assent_chain_via_cicero_amand1945, already
#        anchored at §17, §40 by existing edges + §39, §41 added above).
#    We add explicit discusses-edges between the two Amand syntheses and the
#    Carneadean assent-chain argument so the citation chain is graph-traversal
#    visible without violating cites_primary_source target_types.
# =============================================================================
NEW_EDGES.extend([
    {
        "source": "synthesis_amand1945_cicero_defato_moral_lacuna",
        "target": "argument_carneadean_assent_chain_via_cicero_amand1945",
        "relation": "discusses",
        "confidence": 0.95,
        "metadata": {
            "scholar": "Amand 1945",
            "original_citation": "Amand 1945, p. 78-79 ll. 5135-5158 (the moral-section lacuna in Cic. Fat.) + p. 79-80 ll. 5169-5206 (the Carneadean §17, 40 fragmentary witness)",
            "anchored_in_batch": "cicero_de_fato_deep_b1",
            "note": "Routes the synthesis's reconstruction of the lost moral section to its concrete §17 + §40 surviving witness",
        },
    },
    {
        "source": "synthesis_amand1945_cicero_defato_source_antiochus",
        "target": "argument_carneadean_assent_chain_via_cicero_amand1945",
        "relation": "discusses",
        "confidence": 0.85,
        "metadata": {
            "scholar": "Amand 1945",
            "original_citation": "Amand 1945, p. 66-67 (Antiochus-source hypothesis) + p. 79-80 (witness §17, 40)",
            "anchored_in_batch": "cicero_de_fato_deep_b1",
            "note": "If Cicero -> Antiochus -> Clitomachus -> Carneades is the true chain (Lörcher 1907), the surviving §17, 40 echo carries the Carneadean argument indirectly",
        },
    },
])


# =============================================================================
# 9. SANITY-CHECK NOTE on edges intentionally NOT added :
#
#   - Synthesis (Destrée ch.9, ch.15, Fürst Carneades) cites_primary_source ->
#     passage : ontology-forbidden ; routed via authored arguments.
#   - Bobzien cylinder reconstruction §39-44 : already in KG, do not duplicate.
#   - Bobzien lazy-argument cofated solution -> §28 : already in KG, do not
#     duplicate (and the §26-31 lazy-argument cluster is owned by a different
#     Bobzien argument — `argument_bobzien_2001_b1_lazy_argument_cofated_solution`
#     — which the task brief did NOT include in the 15-scholar list, so we
#     leave its §-anchoring to a future batch).
#   - Bobzien master-argument reconstruction §12, 13 : already in KG, do not
#     duplicate. We extend `chrysippean_modal_system` to §11, §14, §17.
# =============================================================================
