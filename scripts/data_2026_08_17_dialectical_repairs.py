#!/usr/bin/env python3
"""Data for ``apply_2026_08_17_dialectical_repairs.py`` (wave 6).

Four lots, each answering a defect the 2026-08-16 deep audit measured or that
re-verification exposed while checking it.

**Lot 1 — the ``g5_deep_2026_06_15`` dialectical batch.** The audit measured the
whole dialectical population of the graph and found the errors concentrated in a
single provenance: 21 ``opposes`` / ``agrees_with`` / ``critiques`` edges carrying
``provenance: g5_deep_2026_06_15``, none of which carries ``attested_by``. Every
one of the 21 has been re-read against the two nodes it joins and against the
scholar's own text where a copy is on disk. The verdicts below record what each
scholar actually says; where the source could not be consulted, the edge is
flagged, not guessed. **The audit's own verdicts are confirmed for some edges and
refuted for others** — each entry says which.

**Lot 2 — passage nodes that are editorial syntheses sharing a primary's URN.**
``docs/development/ingestion-rules.md`` records this debt as "~2,774 passage nodes
share a locus with another node (661 groups)". Re-measured on the current graph
that identity-key collision covers 436 groups / 2,968 nodes — and a hand sample of
30 groups shows the collision is *mostly* something else entirely (see
``LOT2_SAMPLE_AUDIT``). The genuine editorial-synthesis population, isolated by a
quotation-anchored detector, is 57 nodes.

**Lot 3 — 44 Tertullian passages whose id and text name different works.** Both
clusters are resolved against the text: 13 are *De exhortatione castitatis*
(collated verbatim against SC 319), 31 are *Adversus Praxean* (proved *not* to be
*De anima* against SC 601).

**Lot 4 — the R16 gate** lives in ``scripts/check_ingestion_rules.py``; the
motivating incident is the g5 batch's measured error rate (see ``R16_INCIDENT``).

Nothing here generates ancient Greek or Latin, and nothing here decides a
scholarly dispute. Where two scholars disagree, both positions stay and the edge
records the proposition they disagree *about*.
"""

from __future__ import annotations

import collections
import re

# ---------------------------------------------------------------------------
# Shared vocabulary
# ---------------------------------------------------------------------------

STAMP = "dialectical_repairs_2026_08_17"

#: Relations the R16 gate governs and this wave re-verifies.
DIALECTICAL_RELATIONS = ("opposes", "agrees_with", "critiques")

#: How an edge between two scholarly positions is grounded. Recorded in
#: ``metadata.relation_basis`` so a reader can tell a documented act of
#: engagement from a mere convergence of theses.
#:
#: - ``explicit_engagement`` — the source's author names the target's author (or
#:   the target work) and takes the stance the relation asserts.
#: - ``convergence`` — the two theses agree on the stated proposition, but the
#:   source cannot have engaged the target (it is earlier, or does not cite it).
#:   The graph asserts agreement of content, never an act of assent.
#: - ``propositional_conflict`` — same, for disagreement: the theses are
#:   incompatible on the stated proposition, with no act of criticism attested.
RELATION_BASIS = ("explicit_engagement", "convergence", "propositional_conflict")


# ===========================================================================
# LOT 1 — the g5_deep_2026_06_15 dialectical batch
# ===========================================================================
#
# Verdict vocabulary:
#   keep        - relation is right; add proposition + attested_by (+ basis).
#   retype      - relation is wrong; `new_relation` is right and attested.
#   delete      - the relation asserts something the sources contradict.
#   flag        - could not be checked against the source; mark unverified_g5,
#                 downgrade confidence, invent nothing.
#
# Every entry carries `expected_relation`. The applier refuses to touch an edge
# whose relation has drifted since this file was written.

G5_EDGE_VERDICTS: dict[str, dict] = {
    # -- 1 --------------------------------------------------------------
    "d2b269d5-e3ed-48ff-8851-cc767c4d69ae": {
        "pair": "Inwood (Stoic action theory) -> Bobzien (no free-will problem in the ancients)",
        "expected_relation": "agrees_with",
        "verdict": "keep",
        "relation_basis": "convergence",
        "confidence": 0.75,
        "proposition": (
            "Early Stoic psychology contains no faculty of will — no power in the soul "
            "distinct from and able to oppose reason. Inwood and Bobzien converge on this "
            "narrower claim only; Inwood makes no claim about whether the ancients had a "
            "'free-will problem'."
        ),
        "attested_by": [
            "Inwood, *Ethics and Human Action in Early Stoicism* (Clarendon, 1985), pp. 96-97: "
            "'As Long says, there is in Stoicism no traditional Kantian or existentialist "
            '"will" as a distinct power and faculty in the human soul; and we ought to feel '
            "uncomfortable with attempts to identify anticipations of such notions in the "
            "Stoic theory.'",
            "Inwood 1985, pp. 89-90: Alexander judges the Stoics by a two-sided τὸ ἐφ' ἡμῖν "
            "'He knows that this is not what the Stoics mean' — the same diagnosis Bobzien "
            "1998b gives thirteen years later.",
            "Bobzien, 'The Inadvertent Conception and Late Birth of the Free-Will Problem', "
            "Phronesis 43 (1998), pp. 142-143: 'There is in this model no space for free will.'",
        ],
        "scope_note": (
            "Inwood 1985 predates Bobzien 1998 and cannot be assenting to her thesis; the "
            "edge records convergence of content, not an act of agreement. A search of the "
            "full text found no general statement that the Stoics lacked a concept of free "
            "will — only the faculty-specific denial (p. 97) and the Cleanthes case (p. 71)."
        ),
        "audit_finding": None,
    },
    # -- 3 --------------------------------------------------------------
    "ebc3a02a-e31e-4d53-a328-6bff0f1b6985": {
        "pair": "Inwood (Stoic action theory) -critiques-> concept: two-sidedness of τὸ ἐφ' ἡμῖν",
        "expected_relation": "critiques",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.7,
        "proposition": (
            "The two-sided reading of τὸ ἐφ' ἡμῖν ('able to do either of two opposite "
            "actions') is not the Stoic sense of the phrase, and using it to judge the "
            "Stoics imposes an alien standard."
        ),
        "attested_by": [
            "Inwood 1985, pp. 89-90: Alexander 'bases his argument on the presumption that "
            '"what is in our power" (to eph\' hēmin) is that which enables a man to do '
            "either of two opposite actions in a given circumstance… He knows that this is "
            "not what the Stoics mean by to eph' hēmin… Yet they form the standard against "
            "which the Stoics are criticized.'",
        ],
        "scope_note": (
            "The target node states the bilaterality of τὸ ἐφ' ἡμῖν *in Aristotle* on Sauvé "
            "Meyer's reading (Destrée 2014 ch. 4). Inwood's critique bears on the two-sided "
            "criterion as applied to the Stoics by Alexander, not on Sauvé Meyer's reading "
            "of Aristotle, which postdates him. The edge is kept with that scope recorded; "
            "it would be better carried by a node for Alexander's criterion."
        ),
        "audit_finding": None,
    },
    # -- 4 --------------------------------------------------------------
    "c6393385-0c3b-4fc7-85e6-95fc4c84b1d9": {
        "pair": "Salles (Chrysippus' Frankfurt-style argument) -> Bobzien (no free-will problem)",
        "expected_relation": "agrees_with",
        "verdict": "retype",
        "new_relation": "opposes",
        "relation_basis": "explicit_engagement",
        "confidence": 0.95,
        "proposition": (
            "Whether the requirement that responsibility needs a *specific* dual capacity to "
            "do otherwise arose only in the 2nd c. CE with a Middle-Platonist Aristotle "
            "scholar (Bobzien) or is already Aristotle's own view and therefore available to "
            "Chrysippus as a target (Salles)."
        ),
        "attested_by": [
            "Salles, *The Stoics on Determinism and Compatibilism* (Ashgate, 2005), p. 78: "
            "'(ii) such an incompatibilist position only arose with this Aristotle scholar, "
            "not earlier. As I explained in the previous chapter, I agree with (i). But I now "
            "want to show that (ii) is wrong.' (n. 29 names Bobzien, *Determinism and "
            "Freedom* 359 and 'The inadvertent conception…' §§6-7.)",
            "Salles 2005, p. 81: 'This rebuts the claim that Chrysippus could not have been "
            "the author of the theory because the position it rejects only arose later in "
            "antiquity.'",
            "Salles 2005, p. 80 n. 35: names Bobzien as defending the reading of Aristotle he "
            "rejects, citing 'The inadvertent conception…', 140.",
        ],
        "why": (
            "The g5 batch had the sign backwards. Salles cites Bobzien constantly and agrees "
            "with her on much (pp. 72 n. 13, 78 n. 28, 83 nn. 47-48), but §5.3 is a sustained "
            "argument *against* the dating plank of Bobzien 1998b. Reversing the relation is "
            "the correction; deleting the edge would erase a real, well-documented dispute."
        ),
        "audit_finding": "DAS-095 (listed as a dubious agrees_with; the direction, not the "
        "existence, of the relation was the defect)",
    },
    # -- 6 --------------------------------------------------------------
    "e9a05566-97e9-40fc-9bb7-3324953da859": {
        "pair": "Brennan (Stoic emotions and fate) -> Bobzien (no free-will problem)",
        "expected_relation": "agrees_with",
        "verdict": "retype",
        "new_relation": "engages_with",
        "relation_basis": "explicit_engagement",
        "confidence": 0.8,
        "proposition": (
            "How the ancient and modern debates on responsibility differ. Brennan grants "
            "Bobzien's contrast and then rejects her formulation of it, substituting a "
            "'shrinking of the self' genealogy. Agreement is not what the sources support; "
            "documented engagement is."
        ),
        "attested_by": [
            "Brennan, *The Stoic Life* (OUP, 2005), p. 240: 'I could not have written this "
            "part, nor would I have attempted it, without the immense assistance provided by "
            "Bobzien (1998a)… I have also not hesitated to disagree with her on many points "
            "of interpretation.'",
            "Brennan 2005, p. 289: 'As Susanne Bobzien has shown, the ancient debate over "
            "moral responsibility is carried out in very different terms from the modern one.'",
            "Brennan 2005, pp. 292-293: 'I think these historical investigations would be "
            "misguided, however, because I think the contrast between the two conceptions is "
            "somewhat obscured in Bobzien's formulation.'",
        ],
        "why": (
            "``agrees_with`` is false: Brennan's chapter 17 argues Bobzien's contrast is "
            "misdrawn and offers a rival genealogy in which the Peripatetics play no part. "
            "``engages_with`` is symmetric and asserts only what the print shows."
        ),
        "audit_finding": "DAS-095 (confirmed: the agrees_with was unfounded)",
        "followup": (
            "Brennan's own thesis on the origin of the modern problem (Plato's alienation of "
            "bodily desire, revived in Plotinus, plus a misreading of Epictetus on assent; "
            "pp. 294-302) has no node. Until it does, the substantive Brennan/Bobzien "
            "disagreement cannot be carried at the level of propositions."
        ),
    },
    # -- 7 --------------------------------------------------------------
    "9fba7de0-3c0e-4a63-b563-aa94572fe7b1": {
        "pair": "Brennan (Stoic emotions and fate) -critiques-> Bobzien on Origen and the Idle Argument",
        "expected_relation": "critiques",
        "verdict": "flag",
        "confidence": 0.3,
        "why": (
            "Bobzien 1998a p. 173 (the target's page anchor) is on the Idle Argument; "
            "Brennan 2005 has no discussion of Origen's *Contra Celsum* II 20, and the "
            "index carries no Origen entry for it. His declared disagreement with Bobzien "
            "(p. 240) is general and cannot be attached to this claim. Nothing found either "
            "way — the edge is marked unverified rather than deleted or invented."
        ),
        "audit_finding": None,
    },
    # -- 8 --------------------------------------------------------------
    "cd75c8b6-70e9-4f37-80ec-29c46011ff88": {
        "pair": "Karamanolis (early Christian philosophical engagement) -> Bobzien (no free-will problem)",
        "expected_relation": "agrees_with",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.95,
        "proposition": (
            "On the emergence of the notion of will: not an Augustinian, Christian invention. "
            "Karamanolis declares his alignment with Bobzien (and with Frede) against Dihle."
        ),
        "attested_by": [
            "Karamanolis, *The Philosophy of Early Christianity*, 2nd ed. (Routledge, 2021), "
            "ch. 4 n. 15: 'In this respect I side with Bobzien (1998a, 1998b) and Frede "
            "(2011) against Dihle (1982).'",
            "Karamanolis 2021, ch. 4 n. 14: 'For the emergence of the notion of will, see "
            "Kahn (1988), and especially Bobzien (1998a, 1998b), and Frede (2011).'",
        ],
        "why": (
            "The audit read this as an agreement with no shared proposition, and took "
            "'Karamanolis agrees with Bobzien AND with Frede, who oppose each other' as proof "
            "of incoherence. The print refutes both points: Karamanolis says in one sentence "
            "that he sides with both against Dihle. Bobzien and Frede disagree about *where* "
            "a notion of will first appears; they agree that it is not Augustine's invention, "
            "and that is the proposition Karamanolis endorses. Recording the proposition "
            "dissolves the apparent contradiction without resolving anyone's dispute."
        ),
        "audit_finding": "DAS-095 (REFUTED by the print)",
    },
    # -- 9 --------------------------------------------------------------
    "eecd644f-a8eb-4169-b0a4-812f6fe40625": {
        "pair": "Karamanolis -> Frede (will originates with Epictetus)",
        "expected_relation": "agrees_with",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.95,
        "proposition": (
            "Same proposition as the Bobzien edge: the notion of will emerges within later "
            "ancient philosophy, not with Augustine. Karamanolis records a particular debt to "
            "Frede's account without adopting Frede's dating against Bobzien's."
        ),
        "attested_by": [
            "Karamanolis 2021, ch. 4 n. 15: 'In this respect I side with Bobzien (1998a, "
            "1998b) and Frede (2011) against Dihle (1982).'",
            "Karamanolis 2021, ch. 4 n. 14 (end): 'I am especially indebted to Frede's "
            "account here.'",
        ],
        "audit_finding": "DAS-095 (REFUTED by the print)",
    },
    # -- 10 -------------------------------------------------------------
    "c51a0f90-38a6-4ad3-bea2-cea52f87c34b": {
        "pair": "Karamanolis -critiques-> Dihle (will as Christian innovation)",
        "expected_relation": "critiques",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.95,
        "proposition": (
            "Whether the notion of an autonomous will emerges principally with Augustine and "
            "the Christian tradition (Dihle) or within later ancient philosophy (Karamanolis, "
            "with Bobzien and Frede)."
        ),
        "attested_by": [
            "Karamanolis 2021, ch. 4 n. 15: '…against Dihle (1982).'",
        ],
        "audit_finding": None,
    },
    # -- 13 -------------------------------------------------------------
    "d319ccd0-b346-4fb1-9342-6e5fdc654782": {
        "pair": "Sorabji (four strands of the will) -critiques-> Frede (will originates with Epictetus)",
        "expected_relation": "critiques",
        "verdict": "flag",
        "confidence": 0.5,
        "why": (
            "The source node cites Sorabji 2017, 'Freedom and Will: Graeco-Roman Origins' "
            "(OUP, ISBN 978-0-19-877725-0), pp. 49-66. No copy is on disk: the local library "
            "holds only Sorabji 1980 and *Aristotle Transformed* (1990). The date makes a "
            "critique of Frede 2011 possible, and the four-strands thesis (each strand found "
            "separately before being assembled in Augustine) is in tension with Frede's "
            "single origin in Epictetus — but tension is not a citation. Flagged, not fixed."
        ),
        "audit_finding": None,
    },
    # -- 14 -------------------------------------------------------------
    "a39ea0a6-ac41-49bb-9970-ad0354c8485b": {
        "pair": "Kahn (will emerges with Seneca/Epictetus) -> Frede (will originates with Epictetus)",
        "expected_relation": "agrees_with",
        "verdict": "keep",
        "relation_basis": "convergence",
        "confidence": 0.85,
        "proposition": (
            "Epictetus is the decisive locus for the emergence of a notion of will in "
            "antiquity — for Kahn through προαίρεσις, prepared by Seneca's *voluntas*."
        ),
        "attested_by": [
            "Kahn, 'Discovering the Will: From Aristotle to Augustine', in Dillon & Long "
            "(eds.), *The Question of 'Eclecticism'* (California, 1988), pp. 234-259, at "
            "p. 250: 'It seems clear that Epictetus has used this rather old-fashioned term "
            "[prohairesis] to express a fundamentally new idea, much the same idea that "
            "Seneca had recently expressed by voluntas.'",
            "Frede, *A Free Will* (California, 2011), ch. 3, on Epictetus.",
        ],
        "scope_note": (
            "Kahn 1988 predates Frede 2011 by 23 years: this is convergence of theses, not an "
            "act of assent. The relation is directional in the store only; no engagement is "
            "claimed."
        ),
        "audit_finding": "DAS-093 (part of the Kahn/Dihle/Frede triangle)",
    },
    # -- 15 -------------------------------------------------------------
    "b01bc633-7535-4545-b758-388541d423bb": {
        "pair": "Irwin (Greeks may have had a concept of the will) -opposes-> Frede",
        "expected_relation": "opposes",
        "verdict": "keep",
        "relation_basis": "propositional_conflict",
        "confidence": 0.8,
        "proposition": (
            "Whether Aristotle can be credited with a concept of the will. Irwin argues the "
            "denial is premature and that Aquinas may be reading Aristotle correctly; Frede "
            "holds that no notion of a will is available before Epictetus."
        ),
        "attested_by": [
            "Irwin, 'Who Discovered the Will?', *Philosophical Perspectives* 6 (1992), "
            "pp. 453-473, at p. 455: 'We ought not to infer, however, that the earlier "
            "philosophers have no concept of the will… it may be reasonable to attribute a "
            "concept of the will to Greek philosophers.'",
        ],
        "scope_note": (
            "Irwin 1992 predates Frede 2011 and does not cite him; the conflict is between "
            "the theses, not an act of criticism. Irwin's named targets are Ross, Gauthier, "
            "MacIntyre and Dihle (nn. 2-7)."
        ),
        "audit_finding": None,
    },
    # -- 16 -------------------------------------------------------------
    "df2df6bf-9e0a-41e8-90fc-17d021a35ee1": {
        "pair": "Irwin -opposes-> Dihle (will as Christian innovation)",
        "expected_relation": "opposes",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.9,
        "proposition": (
            "Whether the concept of the will is absent from Greek philosophy and first "
            "articulated under Hebraic and Christian influence."
        ),
        "attested_by": [
            "Irwin 1992, p. 454 n. 5: 'Sometimes Augustine is regarded as the pioneer, under "
            "Hebraic and Christian influence. [n. 5] This is MacIntyre's view. It is defended "
            "at length by A. Dihle, *The Theory of the Will in Classical Antiquity* (1982).'",
            "Irwin 1992, n. 7: 'Dihle's failure to identify the relevant issues is justly "
            "remarked in C. A. Kirwan's review, *Classical Review* 34 (1984), pp. 335-6.'",
        ],
        "audit_finding": None,
    },
    # -- 19 -------------------------------------------------------------
    "ac0529aa-13b2-4088-bf63-aad3c136b64f": {
        "pair": "Frede -critiques-> Bobzien (Alexander as first evidence for the free-will problem)",
        "expected_relation": "critiques",
        "verdict": "retype",
        "new_relation": "discusses",
        "relation_basis": None,
        "confidence": 0.6,
        "proposition": None,
        "attested_by": [
            "Frede, *A Free Will* (2011), pp. 91-95, on Carneades and Alexander of "
            "Aphrodisias: 'our evidence concerning this debate is extremely meager until we "
            "come to Alexander of Aphrodisias at the end of the second century a.d.'",
        ],
        "why": (
            "Frede 2011 cites Bobzien 1998 only three times, all in evidential footnotes "
            "(nn. 10, 12, 14), and never engages her claim about Alexander. His own placing "
            "of Alexander at pp. 91-95 is broadly consonant with hers. A ``critiques`` edge "
            "asserts an act of criticism the book does not perform. The topical link is real "
            "and worth keeping — the two texts are about the same locus — so the edge is "
            "downgraded to ``discusses`` rather than deleted. The genuine Frede/Bobzien "
            "disagreement is carried by edge 8c34b2dc (below) and by the attested "
            "Bobzien-reviews-Frede edge 99e418a3."
        ),
        "audit_finding": None,
    },
    # -- 21 -------------------------------------------------------------
    "c5e3815d-9279-444c-9a95-eb74fb277849": {
        "pair": "Sharples 2008 (accident thesis) -agrees_with-> Sharples 2008 (limits of historical explanation)",
        "expected_relation": "agrees_with",
        "verdict": "retype",
        "new_relation": "extends",
        "relation_basis": None,
        "confidence": 0.9,
        "proposition": None,
        "attested_by": [
            "R. W. Sharples, \"L'accident du déterminisme: Alexandre d'Aphrodise dans son "
            'contexte historique", *Les Études philosophiques* 2008/3 n° 86, pp. 285-303. '
            "The two nodes anchor to p. 285 (limits of historical explanation) and "
            "pp. 289-301 (the coincidence thesis) of that one article.",
        ],
        "why": (
            "The audit called these 'two nodes from the same article carrying the same "
            "thesis' and recommended merging them and deleting the edge. **The premise is "
            "wrong**: they carry two different claims of the same article — the methodological "
            "one at p. 285 ('historical explanations cannot be entirely deterministic'), and "
            "the substantive one at pp. 289-301 (the near-modern free-will problem in "
            "Alexander is a coincidence of RDS and PEA). Four nodes in all come from this "
            "article, each with its own page anchor. What is wrong is the relation: "
            "``agrees_with`` is a relation between scholars' positions and is a category "
            "error applied to one author agreeing with himself in one article. ``extends`` "
            "(argument -> argument) states the real dependence: the coincidence thesis is "
            "the methodological caution applied to a case. No merge is performed here; "
            "merging four distinct claims would destroy page-level citability."
        ),
        "audit_finding": "DAS-094 (relation defect CONFIRMED, duplicate premise REFUTED)",
    },
    # -- 23 -------------------------------------------------------------
    "905f4fb6-c2aa-45b3-832b-0cd764966b8c": {
        "pair": "Inwood (Stoic action theory) -critiques-> concept: ἐλεύθερον καὶ αὐτεξούσιον",
        "expected_relation": "critiques",
        "verdict": "delete",
        "why": (
            "The target is the 2nd-c. Patristic formula 'free and self-determining', first "
            "attested in Theophilus, *Ad Autolycum* II.27. Inwood 1985 is a study of early "
            "Stoic ethics and action theory; a full-text search of the book returns no "
            "occurrence of Theophilus, of αὐτεξούσιον, or of the formula. The edge asserts a "
            "critique of a Christian formula by a book that never mentions it. Like the "
            "Amand/Ramelli edge, this is an unrelated-theses pairing, not an imprecision."
        ),
        "audit_finding": None,
    },
    # -- 27 -------------------------------------------------------------
    "8c34b2dc-28e1-4a37-a70d-55aabdf783aa": {
        "pair": "Frede (will originates with Epictetus) -opposes-> Bobzien (no free-will problem)",
        "expected_relation": "opposes",
        "verdict": "keep",
        "relation_basis": "propositional_conflict",
        "confidence": 0.9,
        "proposition": (
            "Whether a notion of a free will exists in antiquity at all, and if so where it "
            "first appears. Frede: it originates with Epictetus and is then transmitted "
            "through late Platonism to Origen and Augustine. Bobzien: no ancient philosopher "
            "operates with a concept of free will; the problem is an accident of 2nd-c. "
            "Aristotle exegesis meeting Stoic determinism, and even Alexander 'stops short of "
            "a concept of free will'."
        ),
        "attested_by": [
            "Bobzien 1998b, p. 172: 'The Stoics did not require a concept of free-will… "
            "Alexander had no free-will problem either'; p. 174: 'Alexander stops short of a "
            "concept of free will.'",
            "Frede 2011, ch. 3 and pp. 91-95.",
            "The disagreement is attested from Bobzien's side: her review of Frede 2011, "
            "already carried in this graph by edge 99e418a3 "
            "(person_bobzien_susanne_contemporary -critiques-> scholar_frede_michael).",
        ],
        "scope_note": (
            "Frede 2011 cites Bobzien only in evidential footnotes and does not engage her "
            "thesis; the attestation runs one way, from Bobzien to Frede."
        ),
        "audit_finding": None,
    },
    # -- 28 -------------------------------------------------------------
    "4bd99485-5a3c-46c0-8e64-f9cc81788a4c": {
        "pair": "Blackson (E vs D: the object of choice) -opposes-> Frede",
        "expected_relation": "opposes",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.95,
        "proposition": (
            "Whether late Stoicism is the first place a notion of a will appears. Blackson "
            "argues that on the correct specification of the object of choice (E: adults "
            "choose to exercise the ability to use impressions) the early Stoics probably "
            "held it too, so Frede's dating fails."
        ),
        "attested_by": [
            "T. Blackson, 'Epictetus, the Early Stoics, and Frede's Argument for the First "
            "Notion of a Will', *Rhizomata* (2025), doi:10.1515/rhiz-2025-0004, pp. 83-101, "
            "at p. 100: 'Because, however, the early Stoics probably believed E too, Frede is "
            'very likely wrong that "the first time we have any notion of a will" (p. 46) '
            "is in the time of late Stoicism.'",
            "Blackson 2025, p. 100: 'In this case, Frede is wrong about both Epictetus and "
            "the early Stoics.'",
        ],
        "why": (
            "The audit judged this opposition 'imprecise', on the ground that Blackson "
            "contests only the specification of the object of choice and not the Epictetan "
            "origin thesis. **The conclusion of the article refutes that**: Blackson's "
            "explicit conclusion is that Frede is 'very likely wrong' about the dating. The "
            "edge is precise as it stands and only needed its proposition and attestation."
        ),
        "audit_finding": "DAS-096 (REFUTED by the print)",
    },
    # -- 29 -------------------------------------------------------------
    "526b2160-b08b-45e8-94d8-be8bd289fd8a": {
        "pair": "Frede -opposes-> Dihle",
        "expected_relation": "opposes",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.95,
        "proposition": (
            "Whether the history of the notion of a free will should be written as the "
            "genealogy of one specific ('our modern') notion culminating in Augustine "
            "(Dihle), or as a purely historical inquiry into when and why *a* notion of free "
            "will first arose, which Frede locates in Epictetus."
        ),
        "attested_by": [
            "Frede, *A Free Will* (2011), Introduction, pp. 5-7: 'By far the most substantial "
            "attempt to answer this question was made by Albrecht Dihle… we should query the "
            'phrase "our modern notion of will"… he hardly seems entitled to the assumption '
            "that there is one notion of a will, and a free will at that, which we all "
            "share… But my aim is completely different from Dihle's.'",
            "Already recorded in this graph: pub_frede_2011_free_will -critiques-> "
            "scholar_albrecht_dihle, 'The whole book is structured as a sustained response to "
            "Dihle 1982'.",
        ],
        "audit_finding": "DAS-093 (part of the triangle; this leg is sound)",
    },
    # -- 30 -------------------------------------------------------------
    "9a26acd5-0647-4245-8589-4e2b87ba10a1": {
        "pair": "Kahn (will emerges with Seneca/Epictetus) -opposes-> Dihle",
        "expected_relation": "opposes",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.85,
        "proposition": (
            "The LOCUS of emergence only. Kahn accepts Dihle's thesis for the Augustinian "
            "and Thomist concept of will, and dissents on the pagan strand: Chrysippus on "
            "assent, Lucretius and Seneca on *voluntas*, Epictetus on προαίρεσις are not "
            "explained by biblical religious experience."
        ),
        "attested_by": [
            "Kahn 1988, pp. 258-259: 'And so, at the end, we return to Dihle's thesis about "
            "the biblical and theological origins of the concept of will. That does not "
            "apply, however, to what we found in Chrysippus's theory of assent, in "
            "Lucretius's and Seneca's discussions of voluntas, or in Epictetus's doctrine of "
            "prohairesis.'",
            "Kahn 1988, p. 259: 'Dihle has documented in detail what we always suspected: "
            "that the concept of the will as we find it developed in Augustine and Aquinas "
            "presupposes biblical religious experience as one of its indispensable "
            "conditions. But there were other conditions as well.'",
        ],
        "why": (
            "The audit read the triangle as contradictory: Kahn agrees with Dihle at the "
            "person level while Kahn's position opposes Dihle's position. Kahn's own "
            "conclusion shows both are true of *different propositions* — endorsement of the "
            "Augustinian conclusion, dissent on the pagan strand — which is exactly what he "
            "means by 'Major historical developments are always overdetermined' (p. 259). "
            "Recording the two propositions removes the contradiction without deciding "
            "anything on the scholars' behalf."
        ),
        "audit_finding": "DAS-093 (contradiction dissolved, not by deletion but by scoping)",
    },
    # -- 31 -------------------------------------------------------------
    "0a7b02a6-13f2-4b57-bdfc-05c62f5b801e": {
        "pair": "Sorabji (Aristotle on causation and necessity) -opposes-> Bobzien (origin of the free-will problem)",
        "expected_relation": "opposes",
        "verdict": "keep",
        "relation_basis": "propositional_conflict",
        "confidence": 0.9,
        "proposition": (
            "Whether Aristotle was aware of a clash between determinism and the presuppositions "
            "of ethics. Sorabji: he was, and rejects the view that he was 'merely not yet in a "
            "position to appreciate the problem'. Bobzien: his τὸ ἐφ' ἡμῖν does not entail "
            "indeterminism and he is not concerned with fate or causal determinism at all."
        ),
        "attested_by": [
            "Sorabji, *Necessity, Cause and Blame* (1980), p. 246: 'It misrepresents the "
            "situation to suggest that Aristotle was merely not yet in a position to "
            "appreciate the problem; he would not have agreed that the problem was one for "
            "believers in voluntariness.' (Targets listed at p. 243 n. 1.)",
            "Sorabji 1980, p. 247: 'The new development was that Diodorus and the Stoics "
            "persisted in endorsing determinism in a context where many people, Aristotle "
            "included, had already become aware of the clash.'",
            "Bobzien 1998b, p. 144: 'Aristotle's concept of what depends on us does not entail "
            "indeterminism… nor is he concerned with fate or causal determinism.'",
        ],
        "why": (
            "The audit judged the two 'largely compatible' and the opposition imprecise. The "
            "print shows a head-on disagreement about Aristotle's awareness of the problem — "
            "the very hinge of Bobzien's late-birth thesis. Sorabji 1980 predates Bobzien "
            "1998b, so this is a propositional conflict, not an act of criticism."
        ),
        "audit_finding": "DAS-096 (REFUTED by the print)",
    },
    # -- 32 -------------------------------------------------------------
    "af6d44fa-b3c9-43d7-b0cc-e7c8799c166a": {
        "pair": "Amand de Mendieta (Carneades' anti-fatalist argumentation) -opposes-> Ramelli (Origen knew Alexander)",
        "expected_relation": "opposes",
        "verdict": "delete",
        "why": (
            "The two theses concern different transmission channels and can both be true. "
            "Worse for the edge, Ramelli does not oppose Amand — she builds on him: Ramelli "
            "2014, p. 260 n. 88 cites 'Amand 1945' in support of her account of Origen's "
            "reception of the Carneadean objection to fatalism (the ἀργὸς λόγος), and lists "
            "*Fatalisme et liberté dans l'antiquité grecque* in her bibliography. Deleting "
            "removes a false assertion of disagreement; the real relation (Ramelli's article "
            "citing Amand's book) belongs on the publication nodes, not between these two "
            "argument nodes, and is left for a citation wave."
        ),
        "audit_finding": "DAS-092 (CONFIRMED, with the additional evidence that Ramelli "
        "cites Amand approvingly)",
    },
}


# ---------------------------------------------------------------------------
# Lot 1b — the person-level legs of the Kahn / Dihle / Frede triangle.
#
# Not part of the g5 batch (different provenance) but named by the same audit
# finding, DAS-093. The audit's recommendation — carry agrees_with / opposes at
# the level of positions, with a mandatory proposition — is adopted here for the
# legs that survive; the anachronistic leg is removed.
# ---------------------------------------------------------------------------

PERSON_LEVEL_REPAIRS: dict[str, dict] = {
    "0494ed6b-ce74-478e-9e9a-9d901edff796": {
        "pair": "Dihle -agrees_with-> Kahn",
        "expected_relation": "agrees_with",
        "verdict": "delete",
        "why": (
            "Dihle's Sather Lectures were delivered in 1974 and published in 1982; Kahn's "
            "essay appeared in 1988. Dihle cannot be agreeing with Kahn. This is the "
            "redundant half of a symmetric pair the audit flagged, and the half that runs "
            "backwards in time. The relation is kept in the other direction, scoped."
        ),
        "audit_finding": "DAS-093",
    },
    "e9c1ce27-7cd6-4244-abaa-6c05a83567b2": {
        "pair": "Kahn -agrees_with-> Dihle",
        "expected_relation": "agrees_with",
        "verdict": "keep",
        "relation_basis": "explicit_engagement",
        "confidence": 0.85,
        "proposition": (
            "PARTIAL, and on one proposition only: that the concept of the will as developed "
            "in Augustine and Aquinas presupposes biblical religious experience as one of its "
            "indispensable conditions. Kahn dissents on the pagan strand — see the "
            "position-level opposition, edge 9a26acd5."
        ),
        "attested_by": [
            "Kahn 1988, p. 259: 'Dihle has documented in detail what we always suspected: "
            "that the concept of the will as we find it developed in Augustine and Aquinas "
            "presupposes biblical religious experience as one of its indispensable "
            "conditions. But there were other conditions as well.'",
            "Kahn 1988, p. 236: Dihle's book 'remains… a rich treasury of scholarship and "
            "insight'; Kahn thanks Dihle in the opening note.",
        ],
        "audit_finding": "DAS-093",
    },
    "727f9c54-d5e1-488a-87de-720b4cb25d67": {
        "pair": "Kahn -agrees_with-> Frede",
        "expected_relation": "agrees_with",
        "verdict": "keep",
        "relation_basis": "convergence",
        "confidence": 0.8,
        "proposition": (
            "That the concept of will as a distinct faculty is absent from classical Greek "
            "philosophy and emerges in the Stoic-Roman period, with Epictetus decisive."
        ),
        "attested_by": [
            "Kahn 1988, p. 250 (Epictetus' προαίρεσις expresses 'a fundamentally new idea').",
            "Frede 2011, ch. 3.",
        ],
        "scope_note": (
            "Kahn 1988 precedes Frede 2011 by 23 years and cannot be assenting to it; "
            "convergence of theses only."
        ),
        "audit_finding": "DAS-093",
    },
}


# ---------------------------------------------------------------------------
# Lot 1c — mistargeted `supports` edges named by the audit.
# ---------------------------------------------------------------------------

MISTARGETED_SUPPORTS: dict[str, dict] = {
    "24874839-3429-42ed-a6e1-9961f437c0aa": {
        "pair": "CAFMA V (futility of piety and prayer) -supports-> Levels of Providence (Proclean)",
        "expected_relation": "supports",
        "verdict": "delete",
        "why": (
            "Wrong on two counts. Chronologically: the Carneadean moral argument against "
            "fatalism belongs to the 2nd c. BCE (Amand 1945 ch. III; the argument is "
            "reported at Eusebius, *Praep. ev.* VI.6.19, which this node already cites) and "
            "cannot support Proclus' 5th-c. CE hierarchy of providence — the target node is "
            "explicitly Proclean. Substantively: the argument denies that piety and prayer "
            "have any point under fate; it does not *support* a doctrine of providence. "
            "Retargeting was the audit's alternative, but the graph has no node for "
            "providence in general — only the Proclean one — so retargeting would require "
            "creating a concept node, which belongs to an ingestion, not a repair."
        ),
        "audit_finding": "DAS-098 (CONFIRMED)",
    },
}

#: Recorded, not acted on: the audit's DAS-099 (Locke's suspension of desire
#: -supports-> concept_autonomy, whose description is strictly the Greek
#: political αὐτονομία). Fixing it means either widening a concept's definition
#: or creating a node for moral autonomy — a curatorial decision, not a repair.
DEFERRED_SUPPORTS_FINDINGS = [
    (
        "17e6cb7e-2aa2-4d05-937f-cb8c4ee352f8",
        "argument_lockes_suspension_of_desire_e45dc337 -supports-> concept_autonomy_8j2e3f91",
        "DAS-099: the target concept is defined as Greek political self-government. Either "
        "widen the concept to moral autonomy or create a separate node; both are ingestion "
        "decisions.",
    ),
    (
        "d406b586-583f-4ed9-9fae-989e28b64f40",
        "argument_dihle_1982_augustine_invents_philosophical_voluntas -opposes-> scholar_frede_michael",
        "DAS-097: the target is the person Michael Frede rather than one of his positions. "
        "Retargeting to scholarly_position_frede_will_originates_epictetus would duplicate "
        "the triple already asserted by edge 526b2160 in the other direction; resolving it "
        "requires deciding which node is canonical for Dihle's thesis, which the "
        "same-thesis-family finding (DAS-001) has to settle first.",
    ),
]


# ---------------------------------------------------------------------------
# Lot 1d — a node whose description misattributes its own scholar.
#
# Found while verifying edge 0a7b02a6. Not an edge defect: the node text states
# the opposite of what Sorabji argues.
# ---------------------------------------------------------------------------

NODE_CLAIM_CORRECTIONS: list[dict] = [
    {
        "node": "scholarly_position_sorabji_aristotle_indeterminist",
        "field": "description",
        "expect_contains": "did not have a doctrine of libertarian human agency",
        "new_description": (
            "Aristotle on causation and necessity — Aristotle separates necessity from "
            "causation: actions open to moral scrutiny may be caused without being "
            "necessitated. Sorabji reads Aristotle as an indeterminist about human action as "
            "well as about coincidences: in the very same circumstances the agent could have "
            "acted otherwise. What he denies Aristotle is not undetermined agency but the "
            "libertarian machinery usually attached to it — 'fresh starts', uncaused causes "
            "and a faculty of will; on his reading no break in the causal chain is required, "
            "because causes are primarily explanatory rather than necessitating."
        ),
        "why": (
            "The node said Sorabji denies Aristotle a doctrine of libertarian human agency. "
            "He affirms undetermined human action and denies only the uncaused-cause "
            "apparatus. Sorabji 1980, p. 139: 'In Chapter Fourteen, I shall further deny that "
            "Aristotle's account of action is deterministic'; p. 242: 'my case against "
            "deterministic interpretations, by denying that Aristotle's treatment of action "
            "is wholly deterministic… Aristotle is an indeterminist in the sense defined in "
            "the Introduction, but not in the more radical sense suggested by others'; "
            "p. 232 n. 9: 'In the very same circumstances, the child could have acted in the "
            "other way.' The 'fresh starts' he rejects are Ross's, Furley's and Hardie's "
            "(pp. 26 n. 1, 229). He never uses 'free will' in his own voice."
        ),
        "attested_by": [
            "Sorabji, *Necessity, Cause and Blame* (1980), pp. xi, 26, 139, 229, 232, 242, 250.",
        ],
    },
]


# ===========================================================================
# LOT 2 — passage nodes that are editorial syntheses sharing a primary's URN
# ===========================================================================
#
# The debt as recorded (~2,774 nodes / 661 groups) is the count of nodes sharing
# the R2 passage identity key `(cts_urn, passage_role)`. Re-measured on the
# current graph that is 436 groups / 2,968 nodes — and a hand sample of 30 groups
# shows the collision is overwhelmingly caused by two OTHER defects. Applying an
# editorial-synthesis policy to the raw collision set would mark ~2,900 genuine
# primary passages as non-citable.

LOT2_NAIVE_DETECTOR = (
    "identity-key collision: two or more `passage` nodes share "
    "`(metadata.cts_urn, metadata.passage_role)` — the R2 key used by "
    "scripts/check_ingestion_rules.py"
)

#: Hand classification of 30 groups drawn at random (seed 2026) from the naive
#: detector's 436 groups. Counted at group level.
LOT2_SAMPLE_AUDIT = {
    "sampled_groups": 30,
    "true_positive_pure": 2,  # every member is either the primary or its synthesis
    "true_positive_mixed": 4,  # a genuine synthesis pair plus URN-collision intruders
    "false_positive": 24,
    "group_level_precision_pure": "6,7 %",
    "group_level_precision_including_mixed": "20,0 %",
    "false_positive_rate": "80,0 % (93,3 % if mixed groups count as failures)",
    "false_positive_classes": {
        "urn_construction_error": (
            "11 of 30. Different real passages forced onto one URN. Augustine, *De libero "
            "arbitrio* is the worst case: 1.3.8, 2.3.8 and 3.3.8 all carry "
            "`urn:cts:latinLit:stoa0040.stoa003:2.3.8`, because the URN was built from the "
            "section number alone and dropped the book. The same shape produces the giant "
            "groups: all 1,335 Plotinus passages carry "
            "`urn:cts:greekLit:tlg2000.tlg001.perseus-grc1:1`, all 258 Boethius "
            "*Consolatio* passages `urn:cts:latinLit:lat7127.011.perseus-lat1:1`, all 97 "
            "Methodius, all 39 Augustine *De natura boni*, all 38 Plutarch *De fato*, all 36 "
            "Evodius, all 26 Augustine *Adv. Fulgentium*. Marking these non-citable would "
            "silently retire most of the corpus."
        ),
        "duplicate_ingestion_both_primary": (
            "8 of 30. Seneca, *De providentia*: `passage_sen_prov_1_3_14` and "
            "`passage_sen_prov_3_14` hold the SAME Latin, one bare and one prefixed "
            "'Latin: ' under an editorial title. Neither is a summary — both are primary "
            "text. The fix is deduplication, not a role flag."
        ),
        "duplicate_ingestion_both_translation": (
            "7 of 30. Epictetus: `passage_epict_44_en` (a curated key-phrase extract) and "
            "`passage_epict_44_s44_en` (a fuller chunk) are both English translations of the "
            "same locus. There is no primary twin in the group at all."
        ),
        "coarse_urn_not_a_defect": (
            "2 of 30. Tatian, *Oratio ad Graecos* 15.1, 15.2 and 15.3 share the chapter-level "
            "URN `…perseus-grc1:15` because the URN has no sub-section. Three genuinely "
            "different sections, correctly ingested."
        ),
    },
}

#: Preconditions the refined detector adds, each one motivated by a false-positive
#: class above. Implemented by ``detect_editorial_syntheses`` below and re-run by
#: the applier at apply time — the pairs are never hard-coded.
LOT2_PRECONDITIONS = (
    "P1  the two nodes share the R2 identity key (cts_urn, passage_role)",
    "P2  exactly one of them is the PRIMARY: for a Greek locus, >=150 ancient-script "
    "characters and an ancient-script ratio >= 0.55; for a Latin locus, no Greek "
    "anywhere in the group and >=200 characters of text",
    "P3  the candidate synthesis carries >=80 Latin-script characters of prose, and for "
    "a Greek locus an ancient-script ratio < 0.5 and strictly fewer ancient characters "
    "than the primary",
    "P4  the candidate synthesis QUOTES the primary: a normalised run of >=40 ancient "
    "characters taken from the synthesis is a substring of the primary's text (or the "
    "primary's opening 40 characters appear in the synthesis). This is what excludes the "
    "URN-construction false positives — a different passage does not quote this one",
    "P5  the quotation covers <= 50 % of the primary's normalised text. This is what "
    "excludes the Seneca and Boethius duplicates, whose 'synthesis' reproduces the "
    "primary in full, and the bilingual Plutarch nodes",
    "P6  the synthesis carries editorial prose outside the quotation (>=20 Latin-script "
    "characters before the first 'Greek:'/'Latin:' marker, or no marker at all)",
    "P7  the synthesis resolves to exactly ONE primary. Ambiguous cases are reported and "
    "skipped, never guessed",
)

#: Measured on the graph as of 2026-08-17. The applier asserts the shape it finds
#: is within tolerance of these numbers and refuses to run on a wild divergence.
LOT2_EXPECTED = {
    "identity_key_groups": 436,
    "identity_key_nodes": 2968,
    "detected_syntheses": 57,
    "ambiguous": 0,
    "tolerance_pct": 25,
    "by_work_prefix": {
        "passage_aug_lib_arb_*": 33,  # -> passage_aug_dla_*
        "passage_arist_en_*": 12,  # -> passage_arist_ne_*
        "passage_ma_med_*": 7,  # -> passage_marc_aur_*
        "passage_justin_1apol_*": 2,  # -> passage_just_apol1_*
        "passage_plut_fat_*": 2,  # -> passage_plut_fat_*_s*
        "passage_plotinus_enn_*": 1,  # -> passage_plotinus_iv_*
    },
}

#: The policy. No merge: a synthesis is a real editorial object and deleting it
#: would lose curatorial work. What changes is that it stops being citable as if
#: it were the ancient author.
LOT2_POLICY = {
    "passage_role": "editorial_synthesis",
    "citable_as_primary": False,
    "metadata_primary_node_id": "the primary twin",
    "cts_urn": (
        "moved to metadata.synthesis_of_urn and removed from metadata.cts_urn, but ONLY "
        "because it is the collision: with the URN gone the R2 identity key no longer "
        "clashes, and the locus is still recorded and still resolvable through "
        "primary_node_id. If a synthesis's URN is not the one causing the collision, it "
        "is left alone."
    ),
}

#: Defects this wave deliberately does NOT touch, each named so the next wave can
#: find it. Recording them is the point: the ~2,774-node debt line in
#: docs/development/ingestion-rules.md conflates all three.
LOT2_DEBT_HANDED_ON = [
    (
        "urn_construction_error",
        "~2,600 nodes",
        "Passages of a whole work share one work-level URN with a fabricated ':1' or "
        "':1.1' subreference (Plotinus 1,335; Boethius *Cons.* 258+99+30; Methodius 97; "
        "Augustine *De nat. boni* 39; Plutarch *De fato* 38+16; Evodius 36; Augustine "
        "*Adv. Fulg.* 26), or the book level is dropped from the reference (Augustine "
        "*De libero arbitrio*, where 1.x.N / 2.y.N / 3.z.N collapse onto one URN). "
        "Needs URN reconstruction from canonical_ref, not a role flag.",
    ),
    (
        "duplicate_ingestion_same_text",
        "~150 nodes",
        "Seneca *De providentia* and Boethius *Consolatio*: two nodes per locus, both "
        "carrying the same primary text, one under an editorial title. Needs "
        "deduplication with a canonical choice.",
    ),
    (
        "duplicate_translation_chunks",
        "~120 nodes",
        "Epictetus: a curated key-phrase extract and a fuller chunk of the same locus, "
        "both typed as translations. Needs a decision on which is canonical, or a "
        "role that distinguishes an extract from a full translation.",
    ),
]


def _norm_text(s: str) -> str:
    return re.sub(r"[^0-9A-Za-zÀ-ÿͰ-Ͽἀ-῿]", "", s or "").lower()


_ANCIENT = re.compile(r"[Ͱ-Ͽἀ-῿]")
_ANCIENT_RUN = re.compile(r"[Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿\s'’,.·;:\-]{25,}")
_LANG_MARKER = re.compile(r"(?im)^\s*(greek|latin|grec|texte grec)\s*:")
_TRAILING_NUMS = re.compile(r"\d+")

LOT2_MIN_QUOTE = 40
LOT2_MAX_COVERAGE = 0.50


def _profile(node: dict, description: str) -> tuple[str, float, int, int]:
    greek = len(_ANCIENT.findall(description))
    latin = len(re.findall(r"[A-Za-z]", description))
    total = greek + latin
    return description, (greek / total if total else 0.0), greek, latin


def _quoted_runs(text: str, greek_locus: bool) -> list[str]:
    if greek_locus:
        return [m.group(0) for m in _ANCIENT_RUN.finditer(text)]
    out: list[str] = []
    for segment in _LANG_MARKER.split(text)[1:]:
        for part in re.split(r"\n\s*\n", segment):
            if len(part) > 40:
                out.append(part)
    return out


def detect_editorial_syntheses(
    nodes: list[dict], nid, meta
) -> tuple[list[dict], list[dict], dict]:
    """Find passage nodes that are editorial syntheses of a primary twin.

    Returns ``(pairs, ambiguous, stats)``. ``nid`` and ``meta`` are the applier's
    id and metadata accessors, passed in so this module stays free of I/O.

    The preconditions are ``LOT2_PRECONDITIONS``; each exists because a class of
    false positive was found by hand in ``LOT2_SAMPLE_AUDIT``.
    """
    groups: dict[tuple, list[dict]] = collections.defaultdict(list)
    for node in nodes:
        if node.get("type") != "passage":
            continue
        data = meta(node)
        urn = data.get("cts_urn")
        if urn:
            groups[(urn, data.get("passage_role") or "original")].append(node)
    multi = {k: v for k, v in groups.items() if len(v) > 1}

    def locus(node: dict) -> tuple:
        data = meta(node)
        ref = data.get("canonical_ref") or node.get("label") or ""
        return tuple(_TRAILING_NUMS.findall(ref)[-3:])

    def is_synthesis_of(primary: dict, cand: dict) -> float | None:
        pd, p_ratio, p_greek, _ = _profile(primary, primary.get("description") or "")
        sd, s_ratio, s_greek, s_latin = _profile(cand, cand.get("description") or "")
        if s_latin < 80:  # P3
            return None
        greek_locus = p_greek >= 150  # P2
        if greek_locus:
            if p_ratio < 0.55 or s_ratio >= 0.5 or s_greek >= p_greek:
                return None
        else:
            if p_greek > 0 or s_greek > 0 or len(pd) < 200:
                return None
        pn = _norm_text(pd)
        if len(pn) < 200:
            return None
        matched = 0
        for run in _quoted_runs(sd, greek_locus):  # P4
            rn = _norm_text(run)
            if len(rn) < LOT2_MIN_QUOTE:
                continue
            trimmed = rn
            while len(trimmed) >= LOT2_MIN_QUOTE and trimmed not in pn:
                trimmed = trimmed[:-10]
            if len(trimmed) >= LOT2_MIN_QUOTE:
                matched = max(matched, len(trimmed))
        if not matched and pn[:LOT2_MIN_QUOTE] in _norm_text(sd):
            matched = LOT2_MIN_QUOTE
        if not matched:
            return None
        coverage = matched / len(pn)
        if coverage > LOT2_MAX_COVERAGE:  # P5
            return None
        head = _LANG_MARKER.split(sd)[0] if _LANG_MARKER.search(sd) else sd
        if len(re.findall(r"[A-Za-z]", head)) < 20:  # P6
            return None
        return round(coverage, 3)

    found: dict[str, list[dict]] = collections.defaultdict(list)
    for key, members in multi.items():
        if len(members) <= 24:
            candidates = [(a, b) for a in members for b in members if a is not b]
        else:
            buckets: dict[tuple, list[dict]] = collections.defaultdict(list)
            for node in members:
                buckets[locus(node)].append(node)
            candidates = [
                (a, b)
                for bucket in buckets.values()
                if len(bucket) > 1
                for a in bucket
                for b in bucket
                if a is not b
            ]
        for primary, cand in candidates:
            coverage = is_synthesis_of(primary, cand)
            if coverage is not None:
                found[nid(cand)].append(
                    {
                        "synthesis": nid(cand),
                        "primary": nid(primary),
                        "cts_urn": key[0],
                        "passage_role": key[1],
                        "quote_coverage": coverage,
                    }
                )
    pairs = [v[0] for v in found.values() if len(v) == 1]  # P7
    ambiguous = [v for v in found.values() if len(v) > 1]
    stats = {
        "identity_key_groups": len(multi),
        "identity_key_nodes": sum(len(v) for v in multi.values()),
        "detected_syntheses": len(pairs),
        "ambiguous": len(ambiguous),
    }
    return sorted(pairs, key=lambda p: p["synthesis"]), ambiguous, stats


# ===========================================================================
# LOT 3 — 44 Tertullian passages whose id and text name different works
# ===========================================================================
#
# Two clusters, each identified from the TEXT, which is what settles the
# question. Both were carrying two `part_of` parents, so both a right and a
# wrong work claimed them.

TERTULLIAN_REATTRIBUTIONS: list[dict] = [
    {
        "cluster": "A",
        "count": 13,
        "id_prefix": "passage_tert_adv_marc_",
        "chapters": list(range(1, 14)),
        "id_prefix_new": "passage_tert_exhort_cast_",
        "claimed_by_id": "Tertullian, Adversus Marcionem (canonical_ref 'Adv. Marc. N')",
        "claimed_by_label": "Tertullian, De monogamia (label 'De monog. N')",
        "real_work": "Tertullian, De exhortatione castitatis",
        "real_work_node": "work_tertullian_de_exhortatione_castitatis",
        "create_work_node": True,
        "drop_part_of": [
            "work_tertullian_adv_marcionem",
            "work_tertullian_de_monogamia",
        ],
        "canonical_ref_fmt": "De exh. cast. {n}",
        "label_fmt": "Tertullian, De exhortatione castitatis, De exh. cast. {n}",
        "work_title": "De exhortatione castitatis",
        "certainty": "verbatim collation",
        "evidence": (
            "Collated against Sources Chrétiennes 319 (Tertullien, *Exhortation à la "
            "chasteté*), on disk at 02_Corpus/SCO_brepols/Tertullianus/"
            "SCO_Tertullianus_De_exhortatione_castitatis_source.txt. Eleven of thirteen "
            "incipits match the SC text verbatim and IN ORDER after accent/u-v/i-j "
            "normalisation; the two that did not match on the first pass differ by a single "
            "graphic variant in the graph's copy and match once it is allowed for: ch. 1 "
            "'conpositionem' for SC 'compositionem', ch. 5 'erigo' for SC 'origo'. "
            "The chapter count settles it independently: *De exhortatione castitatis* has "
            "thirteen chapters, *De monogamia* seventeen."
        ),
        "incipits": {
            1: "Non dubito, frater, te post uxorem in pace praemissam ad conpositionem animi conversum…",
            2: "Quam denique modesta illa vox est: Dominus dedit, dominus abstulit…",
            3: "Quae enim in manifesto, scimus omnes, eaque ipsa qualiter in manifesto sint…",
            4: "Ceterum de secundo matrimonio scimus plane apostolum pronuntiasse…",
            5: "Ad legem semel nubendi dirigendam ipsa erigo [SC: origo] humani generis patrocinatur…",
            6: "Sed et benedicti, inquis, patriarchae non modo pluribus uxoribus…",
            7: "Cur autem de pristinis exemplis non ea potius agnoscamus…",
            8: "Liceat nunc denuo nubere, si omne quod licet bonum est…",
            9: "Si penitus sensus eius interpretemur, non aliud dicendum erit secundum matrimonium quam species stupri…",
            10: "Renuntiemus carnalibus, ut aliquando spiritalia fructificemus…",
            11: "Duplex enim rubor est, quia in secundo matrimonio duae uxores eundem circumstant maritum…",
            12: "Scio, quibus causationibus coloremus insatiabilem carnis cupiditatem…",
            13: "Ad hanc meam cohortationem, frater dilectissime, accedunt etiam saecularia exempla…",
        },
        "flags": {
            "text_collation_variants": (
                "ch. 1 'conpositionem' and ch. 5 'erigo' diverge from SC 319. The ancient "
                "text is NOT edited by this wave — the divergence is recorded so a "
                "collation pass can resolve it against the print."
            )
        },
    },
    {
        "cluster": "B",
        "count": 31,
        "id_prefix": "passage_tert_de_anima_",
        "chapters": list(range(1, 32)),
        "id_prefix_new": "passage_tert_adv_prax_",
        "claimed_by_id": "Tertullian, De Anima (canonical_ref 'De An. N')",
        "claimed_by_label": "Tertullian, Adversus Praxean (label 'Adv. Prax. N') — already correct",
        "real_work": "Tertullian, Adversus Praxean",
        "real_work_node": "work_tertullian_adversus_praxean",
        "create_work_node": False,
        "drop_part_of": ["work_tertullian_de_anima"],
        "canonical_ref_fmt": "Adv. Prax. {n}",
        "label_fmt": "Tertullian, Adversus Praxean, Adv. Prax. {n}",
        "work_title": "Adversus Praxean",
        "certainty": "negative collation + content + structure",
        "evidence": (
            "NEGATIVE PROOF: none of the 31 incipits occurs anywhere in Tertullian's *De "
            "anima*, collated against Sources Chrétiennes 601 on disk at "
            "02_Corpus/SCO_brepols/Tertullianus/SCO_Tertullianus_De_anima_source.txt "
            "(0/31 matches). *De anima* opens 'De solo censu animae congressus Hermogeni…'; "
            "these passages open 'Varie diabolus aemulatus est veritatem…'. "
            "POSITIVE: the content of all 31 chapters is monarchian polemic — ch. 2 states "
            "the Praxean thesis itself ('post tempus pater natus et pater passus, ipse deus, "
            "dominus omnipotens, Iesus Christus praedicatur'), and chs. 5-31 argue the "
            "Father/Son distinction, *sermo*, and the *trinitas*. *Adversus Praxean* has "
            "exactly 31 chapters. The label, set by an earlier wave, already says so; only "
            "the id, canonical_ref, work_title and work_canonical_id were left behind."
        ),
        "incipits": {
            1: "Varie diabolus aemulatus est veritatem. Adfectavit illam aliquando defendendo concutere…",
            2: "Itaque post tempus pater natus et pater passus, ipse deus, dominus omnipotens, Iesus Christus praedicatur…",
            31: "Ceterum Iudaicae fidei ista res, sic unum deum credere, ut filium adnumerare ei nolis…",
        },
        "flags": {
            "text_collation_pending": (
                "No critical edition of *Adversus Praxean* is on disk (the local Brepols set "
                "holds *De anima*, *Adversus Marcionem* I-III, *Adversus Hermogenem*, "
                "*Adversus Valentinianos*, *De exhortatione castitatis* and others, but not "
                "*Adversus Praxean*). The attribution rests on the negative collation, the "
                "content and the chapter count — strong, but not verbatim-collated."
            )
        },
    },
]

#: Metadata keys on the 44 passages that name the wrong work and must be cleared
#: or rewritten. `work_canonical_id` is CLEARED, never re-guessed: the correct
#: canonical id for either work is not established here.
TERTULLIAN_METADATA_KEYS = {
    "rewrite": ("canonical_ref", "work_title"),
    "clear": ("work_canonical_id", "cts_urn"),
}

#: Work nodes that lose every passage they held. Recorded exactly like
#: work_origen_exhortation_martyrdom in wave 4: the honest state is 'no text
#: ingested', not 'text belonging to another work'.
TERTULLIAN_EMPTIED_WORKS = {
    "work_tertullian_de_anima": (
        "Its 31 children were *Adversus Praxean*. Tertullian's *De anima* has no ingested "
        "text. A critical edition (SC 601) IS on disk at 02_Corpus/SCO_brepols/Tertullianus/"
        "SCO_Tertullianus_De_anima_source.txt and can be ingested."
    ),
    "work_tertullian_adv_marcionem": (
        "Its 13 children were *De exhortatione castitatis*. *Adversus Marcionem* has no "
        "ingested text. Books I-III are on disk in 02_Corpus/SCO_brepols/Tertullianus/."
    ),
    "work_tertullian_de_monogamia": (
        "Its 13 children were *De exhortatione castitatis*, mislabelled by an earlier wave. "
        "*De monogamia* has no ingested text."
    ),
}

#: Flagged, not fixed: two different Tertullian work nodes claim the same
#: canonical identifier. Deciding which is entitled to it needs the Perseus/stoa
#: register, not a guess.
TERTULLIAN_IDENTIFIER_CONFLICT = (
    "work_tertullian_de_monogamia carries cts_urn 'urn:cts:latinLit:stoa0275.stoa015' and "
    "work_tertullian_adv_marcionem carries work_canonical_id "
    "'urn:cts:latinLit:stoa0275.stoa015'. One of the two is wrong (R2/R3b). Not resolved "
    "here — no register was consulted, and inventing a stoa number is exactly the failure "
    "R5 and R10 exist to prevent."
)

#: The new work node for cluster A. It carries full provenance because the
#: applier gates it through check_ingestion_rules.py --new-only, where R1 is a
#: BLOCK. No canonical id is asserted (R3b WARN, accepted and recorded).
TERTULLIAN_NEW_WORK_NODE = {
    "node_id": "work_tertullian_de_exhortatione_castitatis",
    "id": "work_tertullian_de_exhortatione_castitatis",
    "type": "work",
    "label": "Tertullian, De exhortatione castitatis",
    "description": (
        "Tertullian's exhortation to a recently widowed correspondent not to remarry "
        "(13 chapters, c. 208-212 CE). One of the three treatises in which Tertullian "
        "argues against second marriage, alongside *Ad uxorem* and *De monogamia*. Cited "
        "here because chapter 2 grounds the argument in the distinction between what God "
        "wills, permits and merely tolerates, and chapter 9 calls second marriage a "
        "'species stupri'."
    ),
    "period": "Patristic",
    "metadata": {
        "author": "Tertullian",
        "language": "lat",
        "needs_canonical_id": True,
        "provenance": {
            "source": (
                "[local-path] Doctorat SHAL/02_Corpus/SCO_brepols/Tertullianus/"
                "SCO_Tertullianus_De_exhortatione_castitatis_source.txt (Sources Chrétiennes 319)"
            ),
            "ingest_script": "apply_2026_08_17_dialectical_repairs.py",
        },
        "note": (
            "Created to receive 13 passages that had been filed under Adversus Marcionem "
            "(by id) and De monogamia (by label). No cts_urn or work_canonical_id is "
            "asserted: none was verified against a register."
        ),
    },
}

#: The new work node's authorship edge. Without it R14 blocks — a node with no
#: edge is invisible to every retrieval path. Its 13 passages arrive by
#: repointing existing `part_of` edges in the same transaction, which the gate
#: cannot see because it reads edges.jsonl from disk.
TERTULLIAN_NEW_WORK_EDGE = {
    "edge_id": "6d21a8c0-3f4e-4b17-9a52-1c0d7e8f5b39",
    "relation": "authored_by",
    "source": "work_tertullian_de_exhortatione_castitatis",
    "source_id": "work_tertullian_de_exhortatione_castitatis",
    "target": "person_tertullian_d220",
    "target_id": "person_tertullian_d220",
    "weight": 1.0,
    "metadata": {
        "ingest_script": "apply_2026_08_17_dialectical_repairs.py",
        "note": "Tertullian's authorship of De exhortatione castitatis is undisputed.",
    },
}

#: Files outside data/kg that reference the renamed passage ids and must be
#: rewritten in the same transaction, or the rename would dangle.
TERTULLIAN_ID_PROPAGATION_TARGETS = (
    "data/kg/nodes.jsonl",  # node_id / id, plus metadata pointers
    "data/kg/edges.jsonl",  # source / source_id / target / target_id
    "data/corpus/citations.jsonl",  # 31 + 13 references
)


# ===========================================================================
# LOT 4 — the R16 gate
# ===========================================================================

R16_INCIDENT = (
    "Every measured error in the graph's dialectical layer came from one batch. The "
    "2026-08-16 audit sampled the complete populations of `opposes` (14 edges) and "
    "`agrees_with` (13) and 30 of 177 `supports`, and found clear errors at 14,3 % / "
    "23,1 % / 6,7 %. All of them carried `provenance: g5_deep_2026_06_15` and none of "
    "them carried `attested_by`. Every edge that DID carry `attested_by` was correct in "
    "the sample. Re-verification against the print later confirmed the calibration and "
    "added a defect the audit had not caught: an `agrees_with` pointing the wrong way "
    "(Salles 2005 pp. 78-81 argues AGAINST the Bobzien thesis he was recorded as agreeing "
    "with). A dialectical edge without a citation is a claim about what a scholar thinks, "
    "made by nobody."
)

R16_RULE = {
    "id": "R16",
    "name": "attested dialectic",
    "new_only_level": "BLOCK",
    "whole_graph_level": "WARN",
    "relations": DIALECTICAL_RELATIONS,
    "requirement": (
        "A new `opposes`, `agrees_with` or `critiques` edge must carry "
        "`metadata.attested_by` — a citation, with a page or locus, showing that the "
        "relation holds. In whole-graph mode existing dialectical edges without it are "
        "reported as debt."
    ),
}
