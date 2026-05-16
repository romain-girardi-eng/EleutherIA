"""Frede 2011 B1 — UPDATES list (metadata enrichments for existing nodes).

Frede's central thesis: the notion of a free will is not classical Greek;
it emerges with Epictetus in late Stoicism (early Imperial period), is
shaped by Platonist/Peripatetic reactions (Alexander, Plotinus), and is
inherited — not invented — by Christianity (Origen, Augustine).

Each UPDATE adds frede_2011_* metadata keys to existing ancient/early-
Christian person/work/concept nodes that Frede discusses in detail. No
node descriptions are overwritten; we only enrich metadata.
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # =========================================================================
    # ARISTOTLE — Ch. 2 (p. 19-29) : choice without a will
    # =========================================================================
    {
        "id": "person_aristotle_384_322bce_c2d4f6a8",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 2 'Aristotle on Choice without a Will' (p. 19-29)",
            "frede_2011_judgement": (
                "Frede 2011, p. 19-29 : Aristotle has neither a notion of a will "
                "nor a notion of free will. His boulesis is the desire-of-reason "
                "(orexis logistike) specific to a rational soul, not a will as a "
                "distinct faculty. His prohairesis is a special form of willing "
                "restricted to what is up to us (eph' hēmin), not a volitional "
                "choice between alternatives. Cases of akrasia in EN VII are "
                "explained not by a contrary choice but by past failures of "
                "habituation. Frede therefore rejects W. D. Ross's claim that "
                "Aristotle 'shared the plain man's belief in free will' (Ross "
                "1923, 201) — Aristotle simply has the ordinary belief in "
                "responsibility for unforced unignorant action, which is not "
                "yet a doctrine of free will. The hekon/akon distinction is "
                "wider than the prohairesis-class : it applies even to "
                "children and to non-rational animals, and is correctly read "
                "as 'of one's own accord' rather than 'voluntary' in the "
                "later voluntaristic sense"
            ),
            "frede_2011_key_pages": "p. 19-29 (Ch. 2) ; p. 89-101 (Ch. 6 on Peripatetic reactions) ; p. 156 (Ch. 9 on Augustine contrast)",
            "frede_2011_role": "no_will_no_free_will_paradigm",
        },
    },
    # =========================================================================
    # CHRYSIPPUS — Ch. 3 (p. 31-48) : has assent and responsibility, not yet a will
    # =========================================================================
    {
        "id": "person_chrysippus_280_206bce_i9j0k1l2",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 3 'Emergence of a Notion of Will in Stoicism' (p. 31-48)",
            "frede_2011_judgement": (
                "Frede 2011, p. 31-48, 81-82 : Chrysippus furnishes the "
                "psychological materials from which a notion of a will will "
                "later be built — unipartite rational soul, hēgemonikon, "
                "rational impulsive impressions (phantasiai hormētikai), "
                "synkatathesis as assent — but Chrysippus himself does NOT yet "
                "have a notion of a free will. Responsibility for him is "
                "anchored in the fact that one's assent reflects the kind of "
                "person one is (Chrysippean modal logic showing assent is not "
                "necessitated). Frede insists Chrysippus has no notion of "
                "freedom in the technical sense; that emerges only in later "
                "Stoicism with Epictetus"
            ),
            "frede_2011_key_pages": "p. 31-48 (Ch. 3 Stoic psychology) ; p. 81-83 (Ch. 5 on Chrysippean assent and modal logic)",
            "frede_2011_role": "stoic_proto_will_without_freedom",
        },
    },
    # =========================================================================
    # ZENO of Citium — founder, p. 37 (typōsis impression)
    # =========================================================================
    {
        "id": "person_zeno_citium_334_262bce",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 3 (p. 37-38) — typōsis impression",
            "frede_2011_judgement": (
                "Frede 2011, p. 37-38 : Zeno characterized the impression "
                "(phantasia) as a typōsis (imprint) — a formulation Chrysippus "
                "later objected to as misleading. Zeno's account already "
                "presupposes the assent-architecture from which the Stoic "
                "notion of a will will eventually be built"
            ),
            "frede_2011_role": "founder_of_stoic_psychology_of_assent",
        },
    },
    # =========================================================================
    # MUSONIUS RUFUS — Ch. 5 (p. 75) : earliest extant pagan usage of autexousion
    # =========================================================================
    {
        "id": "person_musonius_rufus_30_101ce",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 5 (p. 74-75) — autexousion in Musonius fragments",
            "frede_2011_judgement": (
                "Frede 2011, p. 74-75 : the technical term autexousion 'is "
                "twice found in the fragments of Musonius and then more often "
                "in Epictetus'. It comes to be used by Platonists and "
                "Peripatetics but, crucially, 'from Justin Martyr onwards "
                "very frequently by Christian authors'. Musonius therefore "
                "stands as the earliest extant attestation of the term that "
                "will name freedom in the technical Stoic-Christian sense"
            ),
            "frede_2011_role": "earliest_extant_autexousion_attestation",
        },
    },
    # =========================================================================
    # EPICTETUS — Ch. 3 §3 (p. 44-48) + Ch. 5 §2 (p. 76-85) : first notion of a free will
    # =========================================================================
    {
        "id": "person_epictetus_of_hierapolis_3c385bc2",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 3 §3 (p. 44-48) + Ch. 5 §2 (p. 76-85, esp. 76-79)",
            "frede_2011_judgement": (
                "Frede 2011, p. 44-48, 76-79 : Epictetus is the philosopher in "
                "whom we find the first actual notion of a free will. Three "
                "shifts make it visible : (1) prohairesis (Aristotelian "
                "vocabulary, Stoic content) becomes the central category — "
                "what defines us as persons (Diss. 1.29.1, 3.5.7) ; (2) eph' "
                "hēmin is narrowed : not the external action of crossing the "
                "street, but the choice to assent to the impulsive impression "
                "to cross it ; (3) freedom is reframed as the impossibility "
                "of being forced in this choice — 'there is no power or "
                "force in the world which could prevent it from making the "
                "choices one needs to make to live a good life' (Diss. 1.1.23, "
                "1.4.18, 1.12.9, 3.5.7). 'So here we have our first actual "
                "notion of a free will' (p. 76-77). Only the wise person "
                "actually has a free will; everyone else is potentially free "
                "but has enslaved himself"
            ),
            "frede_2011_key_pages": "p. 44-48, 74-85 ; major Diss. references : 1.1, 1.4.18, 1.12.9, 1.17.21-28, 1.29.1, 2.2.1-7, 3.3.8-10, 3.5.3-7, 3.6.4, 3.9.11",
            "frede_2011_role": "first_actual_notion_of_a_free_will",
        },
    },
    # =========================================================================
    # ALEXANDER OF APHRODISIAS — Ch. 6 (p. 93-101)
    # =========================================================================
    {
        "id": "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 6 'Platonist and Peripatetic Criticisms and Responses' (p. 93-101)",
            "frede_2011_judgement": (
                "Frede 2011, p. 95-101 : Alexander appropriates Carneades' "
                "notion of unforced assent (abiastos synkatathesis) and Aristotle's "
                "eph' hēmin to forge a Peripatetic alternative to Stoic "
                "freedom. He uses autexousion repeatedly. But Frede argues "
                "Alexander gets driven into a 'hopeless tangle' (p. 97-100) "
                "by trying to combine (a) the requirement that one could "
                "have chosen otherwise in identical internal-and-external "
                "circumstances (De fato 192, 22ff) with (b) the Aristotelian "
                "claim that the virtuous person cannot choose otherwise. "
                "Result : a libertarian-indeterminist notion of freedom that "
                "is, in Frede's judgement, 'very close to' Dihle's favoured "
                "modern notion (p. 97) — and the ancestor of the flawed "
                "modern conception of free will. Alexander is 'the only major "
                "ancient philosopher' whose notion is, in Frede's view, "
                "basically flawed (Conclusion p. 177-178). Cause : mistaken "
                "Aristotle-incompatible notion of merit-as-counterfactual-"
                "alternative-rejection"
            ),
            "frede_2011_key_pages": "p. 93-101 (Ch. 6) ; p. 134-135, 142-143 (Ch. 8 Plotinus contrast) ; p. 177-178 (Conclusion, Alexander as outlier)",
            "frede_2011_role": "flawed_libertarian_ancestor_of_modern_voluntarism",
        },
    },
    # =========================================================================
    # CARNEADES — Ch. 6 (p. 91-95)
    # =========================================================================
    {
        "id": "person_carneades_214_129bce_l2m3n4o5",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 6 §1 (p. 91-95)",
            "frede_2011_judgement": (
                "Frede 2011, p. 91-95 : Carneades, in dialectical opposition to "
                "Chrysippus, introduces the distinction between forced assent "
                "and assent originating in the nature of the soul/organism "
                "(motus voluntarii, Cicero De fato XI.23-25). He thereby "
                "considerably narrows the scope of what is hekousion and of "
                "what is eph' hēmin. But Frede insists Carneades does NOT yet "
                "have a notion of a will, of freedom, or of a free will. He "
                "is the originator of the 'unforced assent' criterion that "
                "Alexander will later inherit"
            ),
            "frede_2011_role": "originator_unforced_assent_criterion",
        },
    },
    # =========================================================================
    # PLOTINUS — Ch. 8 (p. 125-152)
    # =========================================================================
    {
        "id": "person_plotinus_d270",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 8 'Reactions to the Stoic Notion of a Free Will: Plotinus' (p. 125-152)",
            "frede_2011_judgement": (
                "Frede 2011, p. 125-152 : Plotinus's treatise Ennead VI.8 'On "
                "Voluntariness and the Will of the One' is the most thorough "
                "Platonist reception of the Stoic notion of free will. "
                "Plotinus innovates by hierarchizing freedom : (1) embodied "
                "human beings — freedom highly qualified by body, (2) souls "
                "— diminished freedom dependent on virtue, (3) intellects — "
                "unqualified freedom precisely because they cannot choose "
                "otherwise, (4) the One/God — absolute freedom as the "
                "archetype. Two of Frede's strongest claims : (a) Plotinus's "
                "ascription to the One of an absolutely free, unconditioned "
                "act of will (VI.8.1.5-6 ; VI.8.7.11ff against the 'monstrous "
                "claim' ho tolmēros logos) refutes A. H. Armstrong's thesis "
                "that this is a specifically Judaeo-Christian conception "
                "imported under Christian influence (Frede vs Armstrong, "
                "p. 150-152) ; (b) Plotinus is closer to the Stoic notion "
                "than to Alexander's : only the wise are free in his deeper "
                "sense, freedom is 'a matter of the secure possession and "
                "control over what one wills and wants' (p. 143). The soul "
                "achieves 'intellectualization' (noōthēnai, VI.8.5.34-36) — "
                "becomes a 'second intellect' — in its freedom"
            ),
            "frede_2011_key_pages": "p. 125-152 (Ch. 8) ; key Enn. VI.8 sections : 1.4-6, 1.18-19, 1.26-27 ('we might be nothing'), 1.30-34, 2.13-15, 4.4-23, 5.4-7, 5.27-36, 6.14-17, 7.11ff, 11.1-2, 15.1-2",
            "frede_2011_role": "platonist_hierarchized_freedom_against_alexander",
        },
    },
    # =========================================================================
    # ORIGEN — Ch. 7 (p. 102-124)
    # =========================================================================
    {
        "id": "person_origen_alexandria_185_254ce_s9t0u1v2",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 7 'An Early Christian View on a Free Will: Origen' (p. 102-124)",
            "frede_2011_judgement": (
                "Frede 2011, p. 102-124 : Origen is 'the first Christian "
                "author ever to write in detail and systematically about the "
                "free will' (p. 105). His short treatise Peri autexousiou (De "
                "principiis III.1, preserved in Greek in the Philocalia ch. "
                "21-27 by Basil and Gregory Nazianzus) proceeds 'along "
                "standard Stoic lines'. Three central Frede claims : (1) "
                "Origen's terminology and major claims are 'through and "
                "through Stoic, with the terminology almost invariably being "
                "found in Epictetus' (p. 113) ; (2) Origen's differences "
                "from Stoicism — identification of autexousion with eph' "
                "hēmin (= things up to us to do or not), permanent retention "
                "of freedom even by demons, possibility of fall and return — "
                "derive from his Platonism, NOT his Christianity (p. 121-122) ; "
                "(3) Christianity's interest in free will is motivated by "
                "anti-Gnostic (anti-Marcion / anti-Valentinus / anti-Basilides) "
                "and anti-astral-deterministic polemic — there is therefore "
                "'no particular reason to expect a radically new notion of a "
                "free will emerging from Christianity' (p. 120-121). Origen's "
                "doctrine of apokatastasis follows directly from his view of "
                "freedom : created intellects never unshakeably know the good, "
                "so ascent and descent remain perpetually possible (p. 122-124)"
            ),
            "frede_2011_key_pages": "p. 102-124 (Ch. 7) ; De princ. III.1.1-7, I.3.8, I.4.1, I.6.2, I.8.2, II.9.2, II.9.5-6 ; Comm. Rom. ; Comm. Gen. ; CC 5.61 ; Comm. Ioan. ad XIII.19.12.16",
            "frede_2011_role": "first_christian_systematic_free_will_treatise_stoic_inheritance",
        },
    },
    # =========================================================================
    # AUGUSTINE — Ch. 9 (p. 153-174)
    # =========================================================================
    {
        "id": "person_augustine_hippo_d430",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 9 'Augustine: A Radically New Notion of a Free Will?' (p. 153-174)",
            "frede_2011_judgement": (
                "Frede 2011, p. 153-174 : Augustine does NOT, contra Dihle "
                "1982, invent a radically new notion of free will. His De "
                "libero arbitrio (388-395) is constructed against Manichaean "
                "determinism in a way structurally parallel to Origen's anti-"
                "Gnostic polemic. Augustine differs from Origen not by moving "
                "further from Stoicism but by adhering more closely to it : "
                "(a) he accepts the Stoic dichotomy free/enslaved with no "
                "middle term ; (b) after the Fall we have lost libertas "
                "altogether and retain only liberum arbitrium (= eph' hēmin "
                "in the Stoic sense), so 'we are not free to liberate "
                "ourselves' (De lib. ar. II.205) ; (c) his velle is the "
                "complex Stoic Epictetan will involved in every assent — even "
                "to non-impulsive impressions (so will is involved in faith "
                "and even in perception, contra Dihle p. 157-159 who reads "
                "this as Augustinian innovation) ; (d) the famous doctrine "
                "that grace alone restores willing follows from the Stoic "
                "fact that the enslaved will is forced. There is 'not a "
                "trace of voluntarism' in Augustine's De lib. ar. (p. 171, "
                "173). Differences from Origen : Augustine accepts collective "
                "original sin (Romans 5:12ff) and reads Paul as ascribing "
                "willing itself to God (Marius Victorinus precedent)"
            ),
            "frede_2011_key_pages": "p. 153-174 (Ch. 9) ; De lib. ar. I.10, I.77, I.79-81, I.86, II.43, II.143, II.199, II.200, II.205, III.240ff ; CD I.25 ; Conf. VIII.5-12 ; Retr. 2-6",
            "frede_2011_role": "stoic_inheritor_via_paul_not_voluntarist_innovator",
        },
    },
    # =========================================================================
    # ALCINOUS — Ch. 4 background ; Middle Platonist reception
    # =========================================================================
    {
        "id": "person_alcinous_2c_ce",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 4 background — Middle Platonist reception of Stoic assent",
            "frede_2011_judgement": (
                "Frede 2011, p. 56-59 : Frede locates Middle Platonist authors "
                "(in particular those represented by the Stobaeus extracts) "
                "as adopting the Stoic doctrine of assent and refashioning "
                "boulesis in a wider sense compatible with bi/tripartite "
                "psychology. Alcinous's Didaskalikos belongs to this milieu, "
                "though Frede does not cite him by name"
            ),
            "frede_2011_role": "middle_platonist_assent_uptake",
        },
    },
    # =========================================================================
    # PORPHYRY — Ch. 4 (p. 57-58) and Ch. 7 (p. 105-106)
    # =========================================================================
    {
        "id": "person_porphyry",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 4 (p. 57-58) + Ch. 7 (p. 105-106) + Ch. 8 (anti-Aristotle on intellects)",
            "frede_2011_judgement": (
                "Frede 2011 : Porphyry is a key transmitter of the Stoic "
                "doctrine of assent in Platonism. In Stob. Ecl. II.167.9ff "
                "(Porphyry's On the Powers of the Soul) he affirms that "
                "natural inclinations do not force assent — the Carneadean-"
                "Alexandrian criterion. Porphyry also reports having known "
                "Origen and could find no fault with his doctrines (Eusebius "
                "HE VI.1.1 ; p. 105). He recommends calling 'gods' angels "
                "(Ch. 8, p. 144)"
            ),
            "frede_2011_role": "transmitter_stoic_assent_into_platonism",
        },
    },
    # =========================================================================
    # JUSTIN MARTYR — Ch. 5 (p. 74-75) + Ch. 7 (p. 103-104)
    # =========================================================================
    {
        "id": "person_justin_martyr_2c_ce",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 5 (p. 74-75) + Ch. 7 (p. 103-104)",
            "frede_2011_judgement": (
                "Frede 2011, p. 74-75 : 'from Justin Martyr onwards [the term "
                "autexousion is used] very frequently by Christian authors' — "
                "Justin is the pivot through which technical Stoic autexousion "
                "enters Christian literature. p. 103-104 : Justin remains a "
                "self-presenting philosopher after his conversion ('new "
                "Christian philosophy'), advancing autexousion as the "
                "Christian-philosophical category of human freedom. Tatian, "
                "his follower, will be the first ever (pagan or Christian) "
                "to use the phrase 'freedom of the will' (eleutheria tēs "
                "prohaireseōs) in Oratio ad Graecos 7.1"
            ),
            "frede_2011_role": "pivot_autexousion_into_christian_use",
        },
    },
    # =========================================================================
    # TATIAN — Ch. 7 (p. 102-104) : eleutheria tes prohaireseos
    # =========================================================================
    {
        "id": "person_tatian",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 7 §1 (p. 102-104) — first ever use of eleutheria tēs prohaireseōs",
            "frede_2011_judgement": (
                "Frede 2011, p. 102-104 : 'The first person ever, whether "
                "pagan or Christian, to use the expression the freedom of "
                "the will (eleutheria tēs prohaireseōs) is Tatian in his "
                "Oratio ad Graecos (chapter 7.1) in the third quarter of "
                "the second century a.d.' Tatian must have been a Platonist "
                "philosopher before his conversion (cf. his book On Animals "
                "attacking the Stoic-Peripatetic denial of animal reason ; "
                "his second-century-Platonist parallels with Celsus)"
            ),
            "frede_2011_role": "first_ever_use_eleutheria_tes_prohaireseos",
        },
    },
    # =========================================================================
    # CICERO — De fato as transmitter of Carneades-Chrysippus debate
    # =========================================================================
    {
        "id": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 6 §1 (p. 91-94) — De fato as main evidence for Carneades-Chrysippus debate",
            "frede_2011_judgement": (
                "Frede 2011, p. 91-94 : Cicero's De fato 'extant only in a "
                "highly mutilated form' is Frede's principal evidence for the "
                "Carneades-Chrysippus debate about unforced assent, the "
                "motus voluntarii (XI.23-25), and what is in nostra potestate. "
                "Cicero, Frede notes, is the first to translate hekōn by "
                "voluntarius — already shifting the Greek term toward the "
                "later voluntaristic register (p. 24-25, Ch. 2 note 7)"
            ),
            "frede_2011_role": "transmitter_de_fato_carneades_chrysippus",
        },
    },
    # =========================================================================
    # CLEMENT OF ALEXANDRIA — Ch. 7 (p. 104) : eph' hēmin retention
    # =========================================================================
    {
        "id": "person_clement_alexandria",
        "metadata_updates": {
            "frede_2011_chapter_treatment": "Ch. 7 (p. 104) — Pantaenus's Stoic legacy in Alexandria",
            "frede_2011_judgement": (
                "Frede 2011, p. 104 : Clement is the immediate Alexandrian "
                "predecessor whose 'good deal of reference to the fact that "
                "there are things which it is up to us (to eph' hēmin) to do "
                "or not to do' anchors the Stoic-philosophical inheritance "
                "of Origen's free-will doctrine. The Alexandrian school was "
                "founded by Pantaenus, originally a Stoic"
            ),
            "frede_2011_role": "alexandrian_eph_hemin_predecessor_of_origen",
        },
    },
    # =========================================================================
    # CONCEPTS ENRICHED — prohairesis, hekousion, eph' hemin, voluntas, autexousion
    # =========================================================================
    {
        "id": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 2 (p. 26-29) : in Aristotle prohairesis is NOT "
                "a will but a special form of willing (orexis bouleutikē) "
                "restricted to actions whose getting-done depends on us "
                "(eph' hēmin). Distinct from boulēsis only because one can "
                "will what is unattainable but can choose only what is in "
                "one's power. Critically, the akratic acts AGAINST his "
                "prohairesis, not because he chose against it but because of "
                "past habituation-failure. Frede invokes this against modern "
                "readings that project a voluntarist will-faculty onto "
                "Aristotle"
            ),
            "frede_2011_key_pages": "p. 26-29 (Ch. 2) ; Ch. 3 §3 (p. 44-48) for Epictetan re-semanticization",
        },
    },
    {
        "id": "concept_hekousion_voluntary_aristotle_a1b2c3d4",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 2 (p. 24-26) : Aristotle's hekōn / akōn is "
                "wider than the prohairesis-class, applies even to children "
                "and non-rational animals, and means 'of one's own accord' "
                "rather than 'voluntary' in the post-Ciceronian voluntaristic "
                "sense. Cicero (Acad. 1.40) first translates hekōn by "
                "voluntarius, projecting a later mental-faculty into the term. "
                "Carneades and then Alexander further narrow hekousion by "
                "excluding psychologically forced assent"
            ),
            "frede_2011_key_pages": "p. 24-26 (Ch. 2) ; p. 93-95 (Ch. 6, Carneades' narrowing) ; p. 95-97 (Alexander)",
        },
    },
    {
        "id": "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 — to eph' hēmin is the spine of the whole "
                "narrative. In Aristotle (Ch. 2, p. 27) it picks out actions "
                "whose getting-done depends entirely on us (the precondition "
                "for choice). In classical Stoicism (Ch. 5, p. 75) it covers "
                "any action depending on our assent. In Epictetus (Ch. 5, "
                "p. 75-76) it is sharply narrowed : not the external action "
                "but only the assent to the impulsive impression — this is "
                "the conceptual move that makes a free will articulable. In "
                "Alexander (Ch. 6, p. 96-100) it requires more than unforced "
                "assent : critical rational evaluation. In Origen (Ch. 7, "
                "p. 112) eph' hēmin is identified with autexousion. In "
                "Augustine (Ch. 9, p. 168) liberum arbitrium = eph' hēmin in "
                "the Stoic sense, retained even after the loss of libertas"
            ),
            "frede_2011_key_pages": "p. 27, 75-79, 95-100, 112, 168",
        },
    },
    {
        "id": "concept_voluntas_y7z8a9b0",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 — Cicero's voluntas (and the Latin verb velle) "
                "is the lexical channel through which Aristotelian hekōn / "
                "Stoic boulēsis-prohairesis cross into the Latin tradition. "
                "Augustine uses velle to render both willing and choosing, "
                "collapsing a Stoic-Epictetan distinction that the Greek "
                "tradition maintained (Ch. 9 p. 158) — but this collapse "
                "does NOT make Augustine a voluntarist (Frede p. 171, 173)"
            ),
            "frede_2011_key_pages": "p. 21, 158, 171-173",
        },
    },
    {
        "id": "concept_synkatathesis_stoic_assent",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 3 (p. 36-42) : synkatathesis is THE Stoic "
                "construct that makes a notion of a will possible. Any non-"
                "forced human action presupposes reason's assent to an "
                "impulsive impression. This passive/active compound (passive "
                "impression + active assent) is what later Stoicism "
                "interiorizes into a will. Plotinus (Enn. 1.8.14) uses the "
                "term — Frede notes only one such occurrence in the whole "
                "Enneads, evidence that Plotinus's Stoic inheritance is "
                "structural rather than verbal"
            ),
            "frede_2011_key_pages": "p. 36-42, 57-58",
        },
    },
    # =========================================================================
    # KEY ANCIENT WORKS Frede uses as primary evidence
    # =========================================================================
    {
        "id": "work_epictetus_discourses",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 — the Discourses are the principal locus where "
                "Frede locates the first actual notion of a free will. Key "
                "passages cited : 1.1 (whole), 1.4.18-21, 1.12.9, 1.17.21-28, "
                "1.19.9, 1.29.1, 2.2.1-7, 3.3.8-10, 3.5.3-7, 3.6.4, 3.9.11. "
                "On the inversion of eph' hēmin, see esp. 1.1 with Bobzien "
                "1998 ch. 7 (cited by Frede)"
            ),
            "frede_2011_role": "primary_evidence_first_free_will",
        },
    },
    {
        "id": "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 2 — Frede's case against an Aristotelian will "
                "rests on EN III.1-5 (hekōn/akōn distinction at 1110b18-"
                "1111a21), EN III.2-4 (prohairesis at 1111b5-1113a33), EN VI.2 "
                "(1139a31-b13), and the akrasia analysis in EN VII (1145b21-"
                "1146b5 ; 1147b13-19 ; 1148a9). His reading is in dialogue "
                "with Kenny 1979 (Aristotle's Theory of the Will), Kahn 1988, "
                "and Broadie 1991 ch. 3 (note 8 to Ch. 2)"
            ),
            "frede_2011_role": "primary_evidence_no_will_in_aristotle",
        },
    },
    {
        "id": "work_de_fato_alexander_c200ce_o6p7q8r9",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 6 — Alexander's De fato is the central "
                "Peripatetic response to Stoic determinism. Frede cites De "
                "fato XI (p. 178, 17ff Bruns), XIV (p. 183, 27ff — hekousion "
                "as unforced assent), XXVIII (p. 199, 16ff — only one or two "
                "Stoic wise men ever), XXXVIII (p. 211, 27ff — Stoic misuse "
                "of 'up to us'), and 192, 22ff (could-have-chosen-otherwise "
                "in identical circumstances). The Mantissa Ch. 22 (also "
                "Bruns) draws the consequence that freedom-as-otherwise-"
                "ability is a sign of weakness"
            ),
            "frede_2011_role": "primary_evidence_libertarian_indeterminism",
        },
    },
    {
        "id": "work_plotinus_ennead_vi_8_d8b9c5a4",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 8 (p. 125-152) — Ennead VI.8 'On Voluntariness "
                "and the Will of the One' is the most thoroughly analyzed "
                "treatise in the book. Frede follows it section by section, "
                "anchoring his reading of Plotinus's hierarchized freedom "
                "(embodied human / soul / intellect / One) and his refutation "
                "of the 'monstrous claim' (ho tolmēros logos, VI.8.7.11ff) "
                "that God's nature is a brute fact. Against Armstrong, Frede "
                "argues VI.8 owes nothing structural to Christian influence"
            ),
            "frede_2011_role": "primary_evidence_platonist_hierarchy_of_freedom",
        },
    },
    {
        "id": "work_de_principiis_origen_230s_v2w3x4y5",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 7 — De principiis is the textual heart of "
                "Frede's Christian chapter. Free-will treatise = De princ. "
                "III.1 (Peri autexousiou). Greek preserved by Basil and "
                "Gregory Nazianzus in Philocalia ch. 21-27. Other key "
                "passages : preface 4-5 (church doctrine list including free "
                "will) ; I.3.8 (grace of perseverance) ; I.4.1 (carelessness) ; "
                "I.6.2 (creatures not by nature good) ; I.8.2 (anti-Gnostic) ; "
                "II.9.2 (laziness) ; II.9.5-6 (against Marcion-Valentinus-"
                "Basilides). Frede insists III.1.2-3 'could have been taken "
                "straight from a late Stoic handbook' (p. 113)"
            ),
            "frede_2011_role": "primary_evidence_first_christian_systematic_free_will",
        },
    },
    {
        "id": "work_origen_philocalia",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 7 (p. 106) — Basil of Caesarea and Gregory "
                "Nazianzus's Philocalia preserves the original Greek of "
                "Origen's free-will treatise (Philoc. ch. 21-27 = De princ. "
                "III.1) as well as supporting Origen texts on the Genesis "
                "commentary, Contra Celsum, and the Commentary on Romans. "
                "Frede treats it as the principal Greek witness to Origen's "
                "free-will doctrine, given Rufinus's mediation of the rest "
                "of De principiis"
            ),
            "frede_2011_role": "primary_witness_origen_free_will_greek",
        },
    },
    {
        "id": "work_augustine_de_libero_arbitrio",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 9 — De libero arbitrio (388-395) is Frede's "
                "central Augustinian text. Key passages : I.10 (anti-"
                "Manichaean), I.77 (gloomy picture of life), I.79-81 (terrible "
                "deed and primal wisdom), I.86 ('we just have to will to have "
                "a good will'), II.43 (need for liberation), II.143 (only God "
                "liberates), II.199-200 (original sin not forced), II.205 "
                "(post-fall non-freedom), III.240ff (Stoic mixed account), "
                "III.244-46, III.255, III.263 (superbia). Frede insists the "
                "Retractationes (2-6) confirm De lib. ar. still fully "
                "represented Augustine's view at the end of his life"
            ),
            "frede_2011_role": "primary_evidence_augustinian_stoic_inheritance",
        },
    },
    {
        "id": "work_de_fato_cicero_44bce_b9c4e5d2",
        "metadata_updates": {
            "frede_2011_treatment": (
                "Frede 2011 Ch. 6 §1 (p. 91-94) — Cicero's De fato is the "
                "principal (and 'highly mutilated') evidence for Carneades's "
                "internal-cause / motus voluntarii doctrine (esp. XI.23-25). "
                "Frede argues Cicero misidentifies the cause as the 'nature "
                "of these voluntary motions' when, by the atom-analogy, "
                "Carneades must have meant the nature of the soul or organism"
            ),
            "frede_2011_role": "primary_evidence_carneades_motus_voluntarii",
        },
    },
    # =========================================================================
    # MODERN SCHOLARS Frede dialogues with — light metadata only
    # =========================================================================
    {
        "id": "scholar_dihle_albrecht",
        "metadata_updates": {
            "frede_2011_role_in_book": (
                "Principal interlocutor (39 mentions per CITATIONS.md). The "
                "entire book is a response to Dihle 1982 The Theory of Will "
                "in Classical Antiquity. Frede grants Dihle that Augustine "
                "matters but rejects Dihle's central claim that Augustine "
                "invents 'our modern notion of will' (Dihle 1982, 144). For "
                "Frede, Augustine inherits a Stoic-Epictetan-Origenian notion "
                "and Christianizes it via Paul, without voluntarism"
            ),
            "frede_2011_chapters_engaging_dihle": "Ch. 1 (p. 5-7), Ch. 8 (p. 127-130), Ch. 9 (p. 153-159 et passim)",
        },
    },
    {
        "id": "person_bobzien_susanne_contemporary",
        "metadata_updates": {
            "frede_2011_role_in_book": (
                "Major interlocutor : Bobzien 1998 Determinism and Freedom "
                "in Stoic Philosophy is cited 5+ times. Frede largely accepts "
                "Bobzien's analysis of classical Stoic determinism and her "
                "argument that the 'free will problem' as we know it is post-"
                "Stoic. He extends Bobzien's narrative by locating the first "
                "actual notion of a FREE WILL in Epictetus rather than "
                "merely an 'inadvertent' birth (Bobzien 1998a)"
            ),
            "frede_2011_chapters_engaging_bobzien": "Ch. 1 note 10 (p. 182), Ch. 3 note 18 (p. 185), and throughout Ch. 5",
        },
    },
    {
        "id": "person_sorabji_richard_contemporary",
        "metadata_updates": {
            "frede_2011_role_in_book": (
                "Cited (Sorabji 2006 Self ch. 10) in Ch. 3 note 17 (p. 185) "
                "on Epictetan prohairesis. Frede aligns broadly with Sorabji "
                "on the centrality of prohairesis to Epictetus's psychology "
                "but goes further in claiming this constitutes the FIRST "
                "actual notion of a free will, not just a prefiguration"
            ),
        },
    },
    {
        "id": "scholar_kahn_charles",
        "metadata_updates": {
            "frede_2011_role_in_book": (
                "Cited (Kahn 1988 'Discovering the Will: From Aristotle to "
                "Augustine') in Ch. 1 note 3 (p. 181-182), Ch. 2 note 8 (p. "
                "183), Ch. 3 note 17 (p. 185). Frede engages Kahn's claim "
                "that the will emerges in Seneca-Epictetus. He shares Kahn's "
                "Stoic-origin thesis but specifies Epictetus rather than "
                "Seneca as the locus of the first actual notion of a free "
                "will"
            ),
        },
    },
    {
        "id": "scholar_broadie_sarah",
        "metadata_updates": {
            "frede_2011_role_in_book": (
                "Cited (Broadie 1991 Ethics with Aristotle ch. 3 'The "
                "Voluntary') in Ch. 2 note 8 (p. 183) on Aristotelian "
                "hekousion. Frede draws on Broadie's reading of Aristotle's "
                "involuntary/voluntary distinction"
            ),
        },
    },
    {
        "id": "scholar_kenny_anthony",
        "metadata_updates": {
            "frede_2011_role_in_book": (
                "Cited (Kenny 1979 Aristotle's Theory of the Will) in Ch. 2 "
                "note 8 (p. 183). Kenny is the standard interlocutor for the "
                "claim that Aristotle's prohairesis is or is not a will. "
                "Frede rejects the will-reading"
            ),
        },
    },
    {
        "id": "scholar_long_anthony",
        "metadata_updates": {
            "frede_2011_role_in_book": (
                "Editor of the volume. Long supplied the editorial notes "
                "(introduced by < … > brackets), the Preface, and identified "
                "primary-source citations. Cited as scholar : Long 2002 "
                "Epictetus: A Stoic and Socratic Guide to Life ch. 8 (Ch. 3 "
                "note 17, p. 185) ; Long & Sedley 1987 The Hellenistic "
                "Philosophers (abbreviated LS throughout)"
            ),
            "frede_2011_chapters_engaging_long": "Editor's Preface (p. xi-xiv) ; all chapter notes",
        },
    },
    {
        "id": "scholar_sedley_david",
        "metadata_updates": {
            "frede_2011_role_in_book": (
                "Author of the Foreword (p. vii-x). Cited as scholar : Long "
                "& Sedley 1987 (LS) is the standard reference work for Stoic "
                "primary evidence throughout the book"
            ),
            "frede_2011_chapters_engaging_sedley": "Foreword (p. vii-x)",
        },
    },
]
