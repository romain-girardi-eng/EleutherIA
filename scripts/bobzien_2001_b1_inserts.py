"""Bobzien 2001 B1 — NEW_INSERTS list (new nodes).

Bilingual FR/EN plain-text descriptions. Type prefixes match `type` field.
Metadata via bobzien_metadata().

The scholar (person_bobzien_susanne_contemporary) and the publication
(scholarly_work_bobzien_2001_determinism_and_freedom_in_stoic_philoso) ALREADY
EXIST in the KG and are touched via UPDATES, NOT inserts.

Sections:
  - PERSONS  : (empty — no new persons)
  - WORKS    : (empty — no new ancient works needed; all Bobzien-cited primary
               sources already exist)
  - CONCEPTS : 4 new concepts (chrysippean compatibilism, pneumatic causation,
               philopator compatibilism, fate principle)
  - SYNTHESES: 8 chapter syntheses (one per chapter of the monograph)
  - ARGUMENTS: 15 scholarly arguments capturing Bobzien's central theses
"""
from __future__ import annotations

from typing import Any

from bobzien_2001_b1_utils import (
    BOBZIEN_PERSON_ID,
    BOBZIEN_PUBLICATION_ID,
    bobzien_metadata,
    dump_metadata,
)


def _node(
    *,
    id: str,
    type: str,
    label: str,
    description: str,
    description_en: str,
    period: str | None,
    metadata: dict[str, Any],
    confidence: float = 0.85,
    needs_evidence: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    n: dict[str, Any] = {
        "id": id,
        "type": type,
        "label": label,
        "description": description,
        "description_en": description_en,
        "metadata": dump_metadata(metadata),
        "confidence": confidence,
    }
    if period is not None:
        n["period"] = period
    if needs_evidence:
        n["needs_evidence"] = True
    n.update(extra)
    return n


# =============================================================================
# PERSONS — empty for B1
# =============================================================================
NEW_PERSONS: list[dict[str, Any]] = []


# =============================================================================
# WORKS — empty for B1 (all Bobzien-cited works already exist)
# =============================================================================
NEW_WORKS: list[dict[str, Any]] = []


# =============================================================================
# CONCEPTS (4 new)
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    _node(
        id="concept_chrysippean_compatibilism_bobzien",
        type="concept",
        label="Compatibilisme chrysippeen (reconstruction Bobzien 2001)",
        description=(
            "Reconstruction par Bobzien 2001 du compatibilisme chrysippeen "
            "comme position philosophique distincte du compatibilisme moderne. "
            "Caracteristiques : (1) determinisme causal universel "
            "teleologique, mais NON necessitarien ; (2) distinction entre "
            "causes antecedentes/externes et causes proches/internes ; (3) "
            "responsabilite morale attachee a la nature interne de l'agent "
            "(analogie du cylindre, Cic. Fat. 39-44 + Gellius NA 7.2) ; (4) "
            "to_eph_hemin entendu comme di' hemon (causatif a une face, "
            "non potestatif a deux faces) ; (5) systeme modal preservant la "
            "contingence dans le determinisme. Pour Bobzien, ce n'est PAS "
            "une theorie du libre arbitre au sens moderne — Chrysippe ne se "
            "pose pas la question de la liberte de faire autrement, mais "
            "celle de l'attribution causale de la responsabilite morale"
        ),
        description_en=(
            "Bobzien 2001's reconstruction of Chrysippean compatibilism as "
            "a philosophical position distinct from modern compatibilism. "
            "Characteristics: (1) universal teleological causal "
            "determinism, but NOT necessitarian; (2) distinction between "
            "antecedent/external and proximate/internal causes; (3) moral "
            "responsibility attached to the agent's internal nature "
            "(cylinder analogy, Cic. Fat. 39-44 + Gellius NA 7.2); (4) "
            "to_eph_hemin understood as di' hemon (one-sided causative, "
            "not two-sided potestative); (5) modal system preserving "
            "contingency within determinism. For Bobzien, this is NOT a "
            "theory of free will in the modern sense — Chrysippus does "
            "not pose the question of freedom to do otherwise, but of "
            "causal attribution of moral responsibility"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 234-329",
            chapter="Ch. 6 Determinism and Moral Responsibility",
            bobzien_chapter_actual="Chrysippus's Compatibilism — reconstructed by Bobzien 2001 as a distinct philosophical position",
            extra={
                "greek_terms": "compatibilism is modern terminology; ancient = peri tou hēmin agapan",
                "primary_sources": [
                    "Cicero De Fato 39-44 (cylinder + Carneadean argument)",
                    "Gellius NA VII.2 (cylinder analogy + Posidonius transmission)",
                    "Plutarch De Stoic. repug. 47",
                    "Origen, Contra Celsum II.20 (Idle Argument reply)",
                ],
                "modern_label_status": "modern scholarly label; ancient Stoa lacks 'compatibilism' as such",
                "bobzien_2001_distinguishing_feature": "ancient Stoic compatibilism preserves causal attribution without requiring libertarian alternative possibilities",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="concept_pneumatic_causation_stoic_bobzien",
        type="concept",
        label="Causation pneumatique stoicienne (reconstruction Bobzien 2001)",
        description=(
            "Modele physique stoicien de la causation universelle reconstruit "
            "par Bobzien 2001 (Ch. 1 §1.1.2 + Ch. 4 §4.2). La causation se "
            "transmet a travers le cosmos via le pneuma, principe actif "
            "(=Dieu = Providence = Nature = Destin). Tous les corps sont "
            "interpenetres et causalement connectes via la tension "
            "pneumatique (tonos), produisant la sympatheia universelle. "
            "Caracteristiques cles : (1) causation = relation entre corps, "
            "non entre evenements ; (2) cause = corps actif agissant sur "
            "un corps passif ; (3) causalite teleologique + causalite "
            "mecanique combinees (Bobzien §1.4.3) ; (4) regularite + "
            "irreversibilite de la chaine causale. Modele explicitement "
            "distinct du necessitarisme megarique de Diodore Cronos"
        ),
        description_en=(
            "Stoic physical model of universal causation reconstructed by "
            "Bobzien 2001 (Ch. 1 §1.1.2 + Ch. 4 §4.2). Causation is "
            "transmitted through the cosmos via pneuma, the active "
            "principle (=God=Providence=Nature=Fate). All bodies are "
            "interpenetrated and causally connected via pneumatic tension "
            "(tonos), producing universal sympatheia. Key features: (1) "
            "causation = body-to-body relation, not event-to-event; (2) "
            "cause = active body acting on passive body; (3) teleological "
            "and mechanical causality combined (Bobzien §1.4.3); (4) "
            "regularity + irreversibility of the causal chain. Explicitly "
            "distinct from Diodorean Megaric necessitarianism"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 18-58, 156-170",
            chapter="Ch. 1 §1.1.2 + Ch. 4 §4.2",
            bobzien_chapter_actual="Stoic pneumatic causation as foundation of universal causal determinism",
            extra={
                "primary_sources": [
                    "Stobaeus Ecl. I.79 (pneumatic transmission)",
                    "Diogenes Laertius VII.150 (active principle)",
                    "Cicero De Natura Deorum II",
                    "Galen De Placitis (Posidonius fragments)",
                ],
                "bobzien_2001_distinguishing_feature": "Stoic causation is body-to-body, not event-to-event",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="concept_fate_principle_bobzien",
        type="concept",
        label="Principe du Destin (Fate Principle, Bobzien 2001 §1.4.4)",
        description=(
            "Formule technique introduite par Bobzien 2001 §1.4.4 (p. 56-58) "
            "pour designer le principe stoicien fondamental selon lequel "
            "TOUT ce qui se produit se produit en accord avec le destin "
            "(panta kath' heimarmenēn ginetai). Le Principe du Destin est "
            "l'identification du Destin avec Dieu, la Providence, la "
            "Nature, le Principe Actif (Cic. ND I.39 + DL VII.135-136). "
            "Bobzien distingue le Principe du Destin (forme generale) de "
            "ses applications particulieres (Principe causal, Principe "
            "providentiel, etc.). Cette formulation technique permet de "
            "distinguer le determinisme stoicien (=causal+teleologique) "
            "du determinisme logique de Diodore et du fatalisme oriental. "
            "Une variante tardive — 'la necessite du destin' (kath' "
            "heimarmenes anagken panta ginetai), citee par Justin — "
            "represente une modification anti-stoicienne"
        ),
        description_en=(
            "Technical formula introduced by Bobzien 2001 §1.4.4 (p. "
            "56-58) to designate the fundamental Stoic principle that "
            "EVERYTHING that occurs occurs according to fate (panta "
            "kath' heimarmenēn ginetai). The Fate Principle identifies "
            "Fate with God-Providence-Nature-Active Principle (Cic. ND "
            "I.39 + DL VII.135-136). Bobzien distinguishes the Fate "
            "Principle (general form) from its particular applications "
            "(Causal Principle, Providential Principle, etc.). This "
            "technical formulation distinguishes Stoic determinism "
            "(=causal+teleological) from Diodorean logical determinism "
            "and Oriental fatalism. A late variant — 'the necessity of "
            "fate' (kath' heimarmenes anagken panta ginetai), cited by "
            "Justin — represents an anti-Stoic modification"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 56-58",
            chapter="Ch. 1 §1.4.4",
            bobzien_chapter_actual="The Fate Principle — formal articulation of the central Stoic identity",
            extra={
                "bobzien_technical_term": True,
                "greek_term_attested": "πάντα καθ᾽ εἱμαρμένην γίνεται (panta kath' heimarmenēn ginetai)",
                "primary_sources": [
                    "Diogenes Laertius VII.135-136 (identity series God-Nature-Fate)",
                    "Cicero De Natura Deorum I.39",
                    "Stobaeus Ecl. I.79 (Aetius Placita)",
                ],
                "late_variant_attestation": "kath' heimarmenes anagken panta ginetai (cited by Justin, identified by Bobzien as late anti-Stoic modification)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="concept_philopator_compatibilism_bobzien",
        type="concept",
        label="Compatibilisme philopatorien (PHILOPATOR, theorie stoicienne tardive, Bobzien 2001 Ch. 8)",
        description=(
            "Theorie compatibiliste tardive (1er-2e siecle CE) attribuee "
            "par Bobzien 2001 (Ch. 8) a un Stoicien designe sous le nom "
            "conventionnel 'PHILOPATOR' (sources principales : Nemesius "
            "De Nat. Hom. 35 + Eusebe PE VI). Caracteristiques selon "
            "Bobzien §§8.2-8.5 : (1) principe causal raffine (memes "
            "causes, memes circonstances => memes effets) ; (2) "
            "conception developpee de to_eph_hemin allant au-dela du "
            "di' hemon chrysippeen ; (3) compatibilisme explicite "
            "entre liberte et necessite causale ; (4) reprise de "
            "l'analogie du cylindre dans un cadre plus systematique "
            "(§8.6). PHILOPATOR represente le sommet du compatibilisme "
            "stoicien et marque la fin du paradigme stoicien classique "
            "avant la montee du probleme du libre arbitre chez "
            "Alexandre d'Aphrodise"
        ),
        description_en=(
            "Late compatibilist theory (1st-2nd c. CE) attributed by "
            "Bobzien 2001 (Ch. 8) to a Stoic conventionally named "
            "'PHILOPATOR' (principal sources: Nemesius De Nat. Hom. 35 "
            "+ Eusebius PE VI). Features per Bobzien §§8.2-8.5: (1) "
            "refined causal principle (same cause + same circumstances "
            "=> same effect); (2) developed conception of to_eph_hemin "
            "going beyond Chrysippean di' hemon; (3) explicit "
            "compatibilism between freedom and causal necessity; (4) "
            "reprise of the cylinder analogy in a more systematic "
            "frame (§8.6). PHILOPATOR represents the peak of Stoic "
            "compatibilism and marks the end of the classical Stoic "
            "paradigm before the rise of the free-will problem with "
            "Alexander of Aphrodisias"
        ),
        period="Roman Imperial",
        metadata=bobzien_metadata(
            page_range="p. 358-412",
            chapter="Ch. 8 A Later Stoic Theory of Compatibilism",
            bobzien_chapter_actual="PHILOPATOR — late Stoic compatibilism reconstructed by Bobzien from Nemesius + Eusebius",
            extra={
                "primary_sources": [
                    "Nemesius, De Natura Hominis 35 (Morani p. 105-106)",
                    "Eusebius, Praeparatio Evangelica VI",
                ],
                "bobzien_2001_attribution_caveat": "PHILOPATOR is a conventional name; Bobzien acknowledges attribution uncertainty",
                "philopator_distinguishing_features": [
                    "refined causal principle (Bobzien §8.2)",
                    "developed to_eph_hemin (Bobzien §8.4)",
                    "explicit compatibilism (Bobzien §8.5)",
                    "cylinder in later fate theory (Bobzien §8.6)",
                ],
            },
        ),
        confidence=0.85,
    ),
]


# =============================================================================
# SYNTHESES — 8 chapter syntheses
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    _node(
        id="synthesis_bobzien2001_ch1_determinism_and_fate",
        type="synthesis",
        label="Bobzien 2001 Ch. 1 — Determinisme et Destin (heimarmene, providence, nature)",
        description=(
            "Synthese Bobzien 2001 Ch. 1 (p. 16-58) : le determinisme "
            "stoicien repose sur deux fondations physico-ontologiques : "
            "(1) le principe actif (logos / pneuma / Dieu) qui penetre "
            "et structure tout le cosmos ; (2) la causation universelle "
            "comme relation entre corps via la tension pneumatique. "
            "Bobzien distingue determinisme teleologique (§1.2) et "
            "determinisme causal (§1.3), montrant qu'ils sont combines "
            "chez les Stoiciens (§1.4.3). Le destin (heimarmene) est "
            "identifie a Dieu, Providence, Nature et Principe Actif — "
            "c'est le 'Principe du Destin' (§1.4.4). L'objection "
            "anti-stoicienne des mouvements spontanes (Cic. Fat. 23-25) "
            "et la reponse chrysippeenne (§1.3.1-1.3.2) sont analysees "
            "comme cadre dialectique fondamental. Le determinisme "
            "stoicien est distingue du determinisme logique de Diodore, "
            "du fatalisme oriental et du necessitarisme megarique"
        ),
        description_en=(
            "Bobzien 2001 Ch. 1 synthesis (p. 16-58): Stoic determinism "
            "rests on two physico-ontological foundations: (1) the "
            "active principle (logos/pneuma/God) which pervades and "
            "structures the entire cosmos; (2) universal causation as "
            "a body-to-body relation via pneumatic tension. Bobzien "
            "distinguishes teleological determinism (§1.2) and causal "
            "determinism (§1.3), showing they are combined in Stoic "
            "thought (§1.4.3). Fate (heimarmene) is identified with "
            "God-Providence-Nature-Active Principle — the 'Fate "
            "Principle' (§1.4.4). The anti-Stoic objection from "
            "spontaneous motions (Cic. Fat. 23-25) and Chrysippus's "
            "reply (§1.3.1-1.3.2) are analyzed as fundamental "
            "dialectical frame"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 16-58",
            chapter="Ch. 1 Determinism and Fate",
            bobzien_chapter_actual="Chapter 1 synthesis — Stoic universal causal determinism + the Fate Principle",
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_bobzien2001_ch2_chrysippean_arguments",
        type="synthesis",
        label="Bobzien 2001 Ch. 2 — Deux arguments chrysippeens pour le determinisme causal (bivalence + divination)",
        description=(
            "Synthese Bobzien 2001 Ch. 2 (p. 59-96) : Chrysippe developpe "
            "deux arguments distincts pour etablir le determinisme causal "
            "universel. (1) Argument de la bivalence (§2.1) : toute "
            "proposition au futur a deja une valeur de verite determinee ; "
            "donc le futur est causalement fixe. Chrysippe accepte la "
            "bivalence sans restriction, contrairement a Epicure (§2.1.2) "
            "qui la rejette pour preserver l'indeterminisme. (2) Argument "
            "de la divination (§2.2) : la divination existe et est "
            "verifiee par l'experience ; or elle presuppose la fixite "
            "causale du futur ; donc le futur est causalement fixe. "
            "Bobzien rejette les lectures simplistes : l'argument est "
            "conditionnel — la divination presuppose la regularite "
            "causale, mais Bobzien §2.2.3 distingue divination-comme-"
            "presupposition vs divination-comme-condition-necessaire"
        ),
        description_en=(
            "Bobzien 2001 Ch. 2 synthesis (p. 59-96): Chrysippus develops "
            "two distinct arguments establishing universal causal "
            "determinism. (1) Bivalence Argument (§2.1): every "
            "future-tense proposition already has a determinate truth-"
            "value; therefore the future is causally fixed. Chrysippus "
            "accepts unrestricted bivalence, unlike Epicurus (§2.1.2) "
            "who rejects it to preserve indeterminism. (2) Divination "
            "Argument (§2.2): divination exists and is empirically "
            "verified; it presupposes causal fixity of the future; "
            "therefore the future is causally fixed. Bobzien rejects "
            "simplistic readings: the argument is conditional — "
            "divination presupposes causal regularity"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 59-96",
            chapter="Ch. 2 Two Chrysippean Arguments for Causal Determinism",
            bobzien_chapter_actual="Chapter 2 synthesis — Bivalence + Divination as twin Chrysippean proofs",
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_bobzien2001_ch3_modality",
        type="synthesis",
        label="Bobzien 2001 Ch. 3 — Modalite, determinisme, liberte (Chrysippe vs Diodore vs Philon)",
        description=(
            "Synthese Bobzien 2001 Ch. 3 (p. 97-143) : Chrysippe developpe "
            "un systeme modal distinct qui doit preserver la contingence "
            "dans le cadre du determinisme causal. (1) Modalites "
            "hellenistiques (§3.1.1) : Bobzien distingue rigoureusement "
            "(a) la necessitarisme diodoreen (§3.1.2) qui identifie "
            "possible et 'soit actuel soit a-venir', collapsant possible-"
            "mais-non-actuel dans l'impossible ; (b) les modalites "
            "conceptuelles ou essentialistes de Philon de Megare (§3.1.3) ; "
            "(c) le systeme chrysippeen (§3.1.4) qui preserve contingence "
            "+ liberte (§3.1.5). (2) L'objection que determinisme stoicien "
            "+ logique modale stoicienne sont incompatibles (§3.2) est "
            "refutee par appel a des modalites epistemiques liees au "
            "destin (§3.3). (3) Distinction chrysippeenne entre Necessite "
            "et ce-qui-est-necessaire (§3.4) : Bobzien soutient que cette "
            "distinction technique permet a Chrysippe d'eviter le piege "
            "diodoreen"
        ),
        description_en=(
            "Bobzien 2001 Ch. 3 synthesis (p. 97-143): Chrysippus "
            "develops a distinct modal system designed to preserve "
            "contingency within causal determinism. Bobzien rigorously "
            "distinguishes Diodorean necessitarianism (§3.1.2), Philonian "
            "essentialism (§3.1.3), and Chrysippean modality (§3.1.4). "
            "The objection that Stoic determinism + Stoic modal logic are "
            "incompatible (§3.2) is refuted via epistemic modalities "
            "linked to fate (§3.3). Chrysippean distinction between "
            "Necessity and that-which-is-necessary (§3.4) allows escape "
            "from the Diodorean trap"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 97-143",
            chapter="Ch. 3 Modality, Determinism, and Freedom",
            bobzien_chapter_actual="Chapter 3 synthesis — Chrysippean modal system contrasted with Diodorus and Philo",
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_bobzien2001_ch4_divination_regularity",
        type="synthesis",
        label="Bobzien 2001 Ch. 4 — Divination, modalite et regularite universelle",
        description=(
            "Synthese Bobzien 2001 Ch. 4 (p. 144-179) : analyse "
            "approfondie de l'argument anti-stoicien selon lequel "
            "divination et contingence stoicienne sont incompatibles "
            "(§4.1). Bobzien distingue deux arguments anti-stoiciens "
            "(§4.1.2-4.1.3) et analyse leur relation logique (§4.1.4). "
            "L'objection cle (§4.1.5) : les notions modales chrysippeennes "
            "entrent en conflit avec la divination. La reponse "
            "chrysippeenne (§4.2) repose sur la distinction entre "
            "causation active et regularite des occurrents : (a) les "
            "conjonctions negees remplacent les conditionnels (§4.2.1) ; "
            "(b) les theoremes divinatoires, les relations signaletiques "
            "et la causation sont distincts (§4.2.2) ; (c) modification "
            "de l'objection anti-stoicienne (§4.2.3) ; (d) divination + "
            "action humaine (§4.2.4). Annexe sur les predictions "
            "conditionnelles (§4.2.5)"
        ),
        description_en=(
            "Bobzien 2001 Ch. 4 synthesis (p. 144-179): in-depth "
            "analysis of the anti-Stoic argument that divination and "
            "Stoic contingency are incompatible (§4.1). Bobzien "
            "distinguishes two anti-Stoic arguments and analyzes their "
            "logical relation. Chrysippean reply (§4.2) rests on the "
            "distinction between active causation and regularity of "
            "occurrents: negated conjunctions replace conditionals, "
            "divinatory theorems are distinguished from causation"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 144-179",
            chapter="Ch. 4 Divination, Modality, and Universal Regularity",
            bobzien_chapter_actual="Chapter 4 synthesis — Chrysippean reply to divination-vs-contingency objection",
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_bobzien2001_ch5_idle_argument",
        type="synthesis",
        label="Bobzien 2001 Ch. 5 — L'argument paresseux (argos logos) et le sof' lution des co-fatedness",
        description=(
            "Synthese Bobzien 2001 Ch. 5 (p. 180-233) : reconstruction "
            "definitive de l'argument paresseux (argos logos / ignava "
            "ratio) et de sa refutation chrysippeenne. (1) Exposition de "
            "l'argument (§5.1.1) : si tout est fixe par le destin, alors "
            "agir est inutile ; donc autant rester oisif. Plausibilite "
            "(§5.1.2) et futilite vs activite teleologique (§5.1.3). "
            "L'argument est-il un sophisme ? (§5.1.4). (2) Les trois "
            "principales reponses anciennes (§5.2) : Cic. Fat. 30 "
            "(§5.2.1) ; Origene Contra Celsum II.20 §5.2.2) ; Eusebe "
            "PE VI.8.25-38 (§5.2.3). (3) Refutation chrysippeenne par "
            "evenements co-fatedness (synfata / confatalia, §5.3) : "
            "l'action et son resultat ne sont pas deux evenements "
            "separement fatedés — ils sont co-fated. Bobzien §5.3.2 "
            "(p. 221-226) : analyse technique des evenements co-fated. "
            "§5.3.3 : implications pour le determinisme chrysippeen. "
            "§5.3.4 : critique de la refutation chrysippeenne"
        ),
        description_en=(
            "Bobzien 2001 Ch. 5 synthesis (p. 180-233): definitive "
            "reconstruction of the Idle Argument (argos logos / ignava "
            "ratio) and its Chrysippean refutation. Three principal "
            "ancient replies analyzed (§5.2): Cic. Fat. 30; Origen "
            "Contra Celsum II.20; Eusebius PE VI.8.25-38. Chrysippean "
            "refutation via co-fated events (synfata / confatalia, "
            "§5.3): action and outcome are not two independently fated "
            "events — they are co-fated"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 180-233",
            chapter="Ch. 5 Fate, Action, and Motivation: The Idle Argument",
            bobzien_chapter_actual="Chapter 5 synthesis — Idle Argument + Chrysippean co-fated-events refutation",
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_bobzien2001_ch6_chrysippean_compatibilism",
        type="synthesis",
        label="Bobzien 2001 Ch. 6 — Determinisme et responsabilite morale : compatibilisme chrysippeen (analogie du cylindre)",
        description=(
            "Synthese Bobzien 2001 Ch. 6 (p. 234-329) : chapitre central "
            "du livre, reconstruction definitive du compatibilisme "
            "chrysippeen. (1) Considerations preliminaires (§6.1) : "
            "vue d'ensemble des passages centraux + conception "
            "chrysippeenne de l'esprit et de l'action (§6.1.2). (2) Un "
            "autre argument contre le destin : le destin rend "
            "l'appreciation morale injuste (§6.2). Argument dans "
            "Gellius (§6.2.1) + dans Ciceron (§6.2.2). (3) La reponse "
            "de Chrysippe (§6.3) : (a) la replique de Chrysippe dans "
            "Gellius (§6.3.1) ; (b) la refutation formelle dans "
            "Ciceron (§6.3.2) ; (c) l'analogie du cylindre et du cone "
            "(§6.3.3, p. 258-271) — analyse technique definitive ; (d) "
            "un autre argument chrysippeen pour la responsabilite "
            "morale (§6.3.4) ; (e) liberte, responsabilite morale et "
            "ce-qui-depend-de-nous (§6.3.5) — distinction one-sided "
            "causative vs two-sided potestative ; (f) determination du "
            "caractere (§6.3.6) ; (g) relation entre causes antecedentes, "
            "destin et necessite (§6.3.7). (4) Une interpretation tardive "
            "de la conception chrysippeenne du destin ? (§6.4) : "
            "framework story ciceronien + dilemme de Plutarque"
        ),
        description_en=(
            "Bobzien 2001 Ch. 6 synthesis (p. 234-329): central chapter "
            "of the book, definitive reconstruction of Chrysippean "
            "compatibilism. Cylinder-and-cone analogy reconstructed "
            "§6.3.3 (p. 258-271): the cylinder's roll is determined by "
            "the push (antecedent cause) + its own shape (internal "
            "nature); moral responsibility attaches to the internal "
            "nature. Sources: Cic. Fat. 39-44 + Gellius NA 7.2. The "
            "distinction one-sided causative vs two-sided potestative "
            "to_eph_hemin established §6.3.5"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 234-329",
            chapter="Ch. 6 Determinism and Moral Responsibility: Chrysippus's Compatibilism",
            bobzien_chapter_actual="Chapter 6 synthesis — definitive reconstruction of cylinder analogy + Chrysippean compatibilism",
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_bobzien2001_ch7_epictetus_eph_hemin_eleutheria",
        type="synthesis",
        label="Bobzien 2001 Ch. 7 — Epictete sur 'ce qui depend de nous' et la liberte (eleutheria)",
        description=(
            "Synthese Bobzien 2001 Ch. 7 (p. 330-357) : Epictete + les "
            "Stoiciens anciens sur to_eph_hemin et eleutheria. (1) "
            "Epictete sur ce-qui-depend-de-nous (§7.1) : reconstruction "
            "du to_eph_hemin epictetien comme prohairesis + usage "
            "correct des impressions (orthōs chrōmenos tais phantasiais). "
            "Bobzien soutient que ce to_eph_hemin reste fondamentalement "
            "causatif (continu avec l'usage stoicien ancien), non "
            "potestatif (au sens libertaire). (2) Liberte (eleutheria) "
            "§7.2 : (a) les Stoiciens anciens sur la liberte (§7.2.1) — "
            "liberte = perfection morale ; (b) Epictete sur la liberte "
            "(§7.2.2) — liberte = independance des choses exterieures + "
            "maitrise de soi via la raison ; (c) eleutheria est-elle la "
            "seule vraie liberte ? (§7.2.3) ; (d) liberte et "
            "ce-qui-depend-de-nous dans l'antiquite tardive (§7.2.4*). "
            "(3) Cleanthes, Epictete, le chien et le char (§7.3) : "
            "Cleanthe sur le destin (§7.3.1), Epictete sur Cleanthe "
            "(§7.3.2), la similitude du chien et du char (§7.3.3). "
            "These centrale : Epictete n'introduit PAS la notion "
            "libertaire de libre arbitre"
        ),
        description_en=(
            "Bobzien 2001 Ch. 7 synthesis (p. 330-357): Epictetus + "
            "early Stoics on to_eph_hemin and eleutheria. Bobzien "
            "argues Epictetan eph' hemin remains causative (continuous "
            "with early Stoic usage), NOT potestative (in the "
            "libertarian sense). Eleutheria reconstructed as moral "
            "perfection achieved via prohairesis + correct use of "
            "impressions. Central thesis: Epictetus does NOT introduce "
            "the libertarian notion of free will"
        ),
        period="Roman Imperial",
        metadata=bobzien_metadata(
            page_range="p. 330-357",
            chapter="Ch. 7 Freedom and That Which Depends On Us",
            bobzien_chapter_actual="Chapter 7 synthesis — Epictetus's compatibilist eleutheria, NOT libertarian",
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_bobzien2001_ch8_philopator_late_stoic",
        type="synthesis",
        label="Bobzien 2001 Ch. 8 — Une theorie stoicienne tardive du compatibilisme (PHILOPATOR)",
        description=(
            "Synthese Bobzien 2001 Ch. 8 (p. 358-412) : chapitre final "
            "consacre a une theorie compatibiliste stoicienne tardive "
            "(1er-2e siecle CE) que Bobzien attribue conventionnellement "
            "a 'PHILOPATOR'. (1) Notes sur les sources et l'origine de "
            "la theorie (§8.1*) : Nemesius De Nat. Hom. 35 + Eusebe PE "
            "VI. (2) Determinisme causal de PHILOPATOR (§8.2) : principe "
            "causal raffine (memes causes + memes circonstances => "
            "memes effets). (3) Role du destin dans la theorie de "
            "PHILOPATOR (§8.3). (4) Conception philopatoriene de "
            "ce-qui-depend-de-nous (§8.4). (5) Compatibilisme "
            "philopatorien (§8.5) — explicite, articule comme "
            "reconciliation de la liberte et de la necessite causale. "
            "(6) Le cylindre dans la theorie stoicienne tardive (§8.6) — "
            "reprise systematique de l'analogie chrysippeenne. (7) La "
            "montee et la chute du probleme de la liberte d'agir "
            "autrement et du determinisme causal (§8.7, p. 396-412) — "
            "Bobzien conclut que le 'probleme du libre arbitre' tel "
            "qu'on le connait modernement ne s'enracine pas dans le "
            "Stoa classique mais emerge tardivement via Alexandre"
        ),
        description_en=(
            "Bobzien 2001 Ch. 8 synthesis (p. 358-412): final chapter "
            "on a late Stoic compatibilist theory (1st-2nd c. CE) "
            "conventionally attributed by Bobzien to 'PHILOPATOR'. "
            "Sources: Nemesius De Nat. Hom. 35 + Eusebius PE VI. "
            "PHILOPATOR refines the Stoic causal principle, develops "
            "to_eph_hemin further, and articulates compatibilism more "
            "explicitly. §8.7 'The rise and fall of the problem of "
            "freedom to do otherwise and causal determinism' concludes "
            "that the modern 'free-will problem' does not root in the "
            "classical Stoa but emerges late via Alexander"
        ),
        period="Roman Imperial",
        metadata=bobzien_metadata(
            page_range="p. 358-412",
            chapter="Ch. 8 A Later Stoic Theory of Compatibilism (PHILOPATOR)",
            bobzien_chapter_actual="Chapter 8 synthesis — PHILOPATOR + the rise/fall of the freedom-to-do-otherwise problem",
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# ARGUMENTS — 15 scholarly arguments capturing Bobzien's central theses
# =============================================================================

NEW_ARGUMENTS: list[dict[str, Any]] = [
    _node(
        id="argument_bobzien_2001_b1_no_free_will_in_stoa",
        type="argument",
        label="Bobzien 2001 — Les Stoiciens anciens n'ont PAS la notion de libre arbitre (these centrale)",
        description=(
            "Argument-pivot du monograph (esp. ch. 6-7 + conclusion §8.7) : "
            "les Stoiciens anciens (Zenon, Cleanthe, Chrysippe) n'ont PAS "
            "developpe une notion de libre arbitre au sens libertaire "
            "moderne — c'est-a-dire une capacite a faire autrement (alternative "
            "possibilities) deconnectee de la causation universelle. Ils "
            "ont developpe (1) un determinisme causal universel "
            "teleologique ; (2) une theorie causale de la responsabilite "
            "morale via l'analogie du cylindre ; (3) un concept de "
            "to_eph_hemin = di' hemon (causatif a une face). Le probleme "
            "du libre arbitre tel que pose modernement (compatibilisme vs "
            "incompatibilisme, free will vs determinism) est anachronique "
            "au Stoa classique. Cette these methodologique se cristallise "
            "particulierement dans la conclusion (§8.7, p. 396-412) qui "
            "trace 'la montee et la chute du probleme de la liberte d'agir "
            "autrement'"
        ),
        description_en=(
            "Pivot argument of the monograph (esp. ch. 6-7 + conclusion "
            "§8.7): early Stoics (Zeno, Cleanthes, Chrysippus) did NOT "
            "develop a notion of free will in the modern libertarian "
            "sense — i.e. an ability to do otherwise (alternative "
            "possibilities) disconnected from universal causation. They "
            "developed (1) universal teleological causal determinism; "
            "(2) a causal theory of moral responsibility via cylinder "
            "analogy; (3) a concept of to_eph_hemin = di' hemon "
            "(one-sided causative). The free-will problem as modernly "
            "posed is anachronistic to classical Stoa"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="passim — esp. p. 234-329, 330-357, 396-412",
            chapter="Ch. 6-7 + conclusion §8.7",
            bobzien_chapter_actual="Central thesis — Stoics do not have a modern libertarian free-will notion",
            extra={
                "argument_type": "scholarly thesis (methodological + exegetical)",
                "bobzien_2001_judgement": "0.95 — central monograph thesis",
                "central_thesis": True,
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction",
        type="argument",
        label="Bobzien 2001 — Reconstruction definitive de l'analogie du cylindre (Cic. Fat. 39-44 + Gellius NA 7.2)",
        description=(
            "Reconstruction technique definitive (Bobzien 2001 §6.3.3, "
            "p. 258-271) de l'analogie chrysippeenne du cylindre et du "
            "cone. Strucutre : (1) cause antecedente / externe = la "
            "poussee qui met le cylindre en mouvement ; (2) cause "
            "proche / interne = la forme cylindrique elle-meme, qui "
            "determine le mode de roulement ; (3) le mouvement effectif "
            "est causalement determine par la conjonction des deux ; "
            "(4) la responsabilite morale est attribuee a la cause "
            "interne (la forme = la nature de l'agent), non a la cause "
            "externe. Bobzien soutient que cette analogie n'invoque "
            "PAS une capacite a faire autrement — elle n'est pas "
            "libertaire. Elle establishit la responsabilite causale "
            "(qui est responsable de l'effet) sans requerir des "
            "possibilites alternatives. Sources textuelles centrales : "
            "Cic. Fat. 39-44 (Yon Bude + Sharples) + Gellius NA VII.2 "
            "(Marshall OCT) avec lecture Posidonius-Chrysippe"
        ),
        description_en=(
            "Definitive technical reconstruction (Bobzien 2001 §6.3.3, "
            "p. 258-271) of Chrysippus's cylinder-and-cone analogy. "
            "Structure: (1) antecedent/external cause = the push; (2) "
            "proximate/internal cause = the cylindrical shape itself; "
            "(3) actual motion causally determined by both conjoined; "
            "(4) moral responsibility attaches to internal cause "
            "(shape = agent's nature). Bobzien argues this does NOT "
            "invoke ability to do otherwise — it is not libertarian. "
            "It establishes causal responsibility without requiring "
            "alternative possibilities. Central textual sources: Cic. "
            "Fat. 39-44 + Gellius NA VII.2"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 258-271",
            chapter="Ch. 6 §6.3.3",
            bobzien_chapter_actual="Cylinder-cone analogy — Bobzien's definitive modern reconstruction",
            extra={
                "argument_type": "exegetical reconstruction",
                "primary_sources": ["Cic. Fat. 39-44", "Gellius NA VII.2"],
                "interpretive_claim": "cylinder analogy is NOT libertarian — only attributes causal responsibility",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_bobzien_2001_b1_lazy_argument_cofated_solution",
        type="argument",
        label="Bobzien 2001 — Solution de l'argument paresseux via evenements co-fated (synfata)",
        description=(
            "Reconstruction Bobzien 2001 ch. 5 (esp. §5.3.2, p. 221-226) "
            "de la solution chrysippeenne a l'argument paresseux. "
            "L'argument paresseux (Cic. Fat. 28-30 ; Origene CC II.20 ; "
            "Eus. PE VI.8.25-38) soutient que si le destin determine "
            "tout, l'action humaine est inutile. La refutation "
            "chrysippeenne par les evenements co-fated (synfata / "
            "confatalia) : l'action et son resultat NE SONT PAS deux "
            "evenements fated independamment — ils sont co-fated. Donc "
            "'consulter un medecin pour guerir' est co-fated avec "
            "'guerir' ; refuser de consulter ne preserve pas la "
            "guerison, mais la previent. Bobzien §5.3.3 montre que cette "
            "solution PRESERVE le determinisme causal universel tout "
            "en sauvant la rationalite teleologique de l'action. §5.3.4 "
            "evalue les critiques modernes de la refutation"
        ),
        description_en=(
            "Bobzien 2001 ch. 5 reconstruction (esp. §5.3.2, p. "
            "221-226) of Chrysippus's solution to the Idle Argument. "
            "The Idle Argument (Cic. Fat. 28-30; Origen CC II.20; Eus. "
            "PE VI.8.25-38) holds that if fate determines everything, "
            "human action is otiose. Chrysippean refutation via "
            "co-fated events (synfata / confatalia): action and outcome "
            "are NOT two independently fated events — they are "
            "co-fated. 'Consulting a doctor to recover' is co-fated "
            "with 'recovering'; refusing to consult does not preserve "
            "recovery, it prevents it"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 217-233",
            chapter="Ch. 5 §5.3.2",
            bobzien_chapter_actual="Bobzien's reconstruction of Chrysippus's co-fated-events refutation of the Idle Argument",
            extra={
                "argument_type": "exegetical reconstruction",
                "primary_sources": ["Cic. Fat. 28-30", "Origen CC II.20", "Eus. PE VI.8.25-38"],
                "key_concept": "synfata / confatalia (co-fated events)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided",
        type="argument",
        label="Bobzien 2001 — Distinction one-sided causative vs two-sided potestative to_eph_hemin",
        description=(
            "These cle Bobzien 2001 §6.3.5 + §7.1 : to_eph_hemin a deux "
            "sens fondamentalement distincts dans la philosophie "
            "ancienne. (a) Sens stoicien ancien = causatif a une face "
            "(one-sided causative) : 'ce qui se produit a travers nous' "
            "(di' hemon), c'est-a-dire ce dont nous sommes la cause "
            "interne dans la chaine causale du destin. Compatible avec "
            "le determinisme. Pas de capacite implicite a faire "
            "autrement. (b) Sens tardif (Alexandre + commentateurs "
            "aristoteliciens) = potestatif a deux faces (two-sided "
            "potestative) : 'ce qui est a nous de faire OU de ne pas "
            "faire', impliquant capacite reelle a faire autrement. "
            "Incompatible avec le determinisme. Pour Bobzien, l'erreur "
            "anachronique consiste a lire le sens (b) chez les "
            "Stoiciens anciens. Distinction fondatrice pour toute la "
            "lecture revisionniste de Bobzien et fondement de son "
            "argumentation dans Bobzien 1998 Phronesis"
        ),
        description_en=(
            "Bobzien 2001 key thesis §6.3.5 + §7.1: to_eph_hemin has "
            "two fundamentally distinct senses in ancient philosophy. "
            "(a) Early Stoic sense = one-sided causative: 'that which "
            "happens through us' (di' hemon), i.e. that of which we "
            "are the internal cause in fate's causal chain. Compatible "
            "with determinism. No implicit ability to do otherwise. "
            "(b) Late sense (Alexander + Aristotelian commentators) = "
            "two-sided potestative: 'that which is up to us to do OR "
            "not do', implying real ability to do otherwise. "
            "Incompatible with determinism. Anachronistic to read (b) "
            "into early Stoics"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 276-301, 331-338",
            chapter="Ch. 6 §6.3.5 + Ch. 7 §7.1",
            bobzien_chapter_actual="Foundational distinction one-sided vs two-sided to_eph_hemin",
            extra={
                "argument_type": "central conceptual distinction",
                "central_thesis": True,
                "linked_to_bobzien_1998": "fully argued in companion 1998 Phronesis paper",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_bobzien_2001_b1_synkatathesis_psychology_action",
        type="argument",
        label="Bobzien 2001 — La synkatathesis (assentiment) au centre de la psychologie chrysippeenne de l'action",
        description=(
            "Reconstruction Bobzien 2001 §6.1.2 (p. 239-242) + §6.3.5 : "
            "la psychologie stoicienne de l'action met synkatathesis "
            "(συγκατάθεσις, assentiment) au centre. Sequence : "
            "(1) impression (phantasia) se presente a l'hegemonikon ; "
            "(2) l'agent rationnel assenti (ou refuse l'assentiment) ; "
            "(3) l'assentiment produit l'impulsion (hormē) vers "
            "l'action ; (4) l'action suit. Dans l'analogie du cylindre, "
            "l'assentiment correspond a la nature interne — c'est le "
            "lieu de la responsabilite morale. La synkatathesis est "
            "causalement determinee par l'impression + l'etat "
            "rationnel de l'agent (caractere, habitudes, dispositions). "
            "Donc la responsabilite ne requiert pas une 'liberte' "
            "indeterministe — elle requiert seulement l'attribution "
            "causale a l'agent. Bobzien insiste : l'assentiment est "
            "EN NOTRE POUVOIR au sens one-sided causative, non au sens "
            "two-sided potestative"
        ),
        description_en=(
            "Bobzien 2001 reconstruction §6.1.2 (p. 239-242) + §6.3.5: "
            "Stoic psychology of action places synkatathesis "
            "(συγκατάθεσις, assent) at center. Sequence: (1) impression "
            "(phantasia) presents to the hegemonikon; (2) the rational "
            "agent assents (or withholds); (3) assent produces "
            "impulse (hormē) toward action; (4) action follows. In the "
            "cylinder analogy, assent corresponds to the internal "
            "nature — locus of moral responsibility. Assent is "
            "causally determined by impression + agent's rational "
            "state. Responsibility requires only causal attribution, "
            "not indeterministic freedom"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 239-242, 276-301",
            chapter="Ch. 6 §6.1.2 + §6.3.5",
            bobzien_chapter_actual="Synkatathesis as core of Chrysippean action psychology",
            extra={
                "argument_type": "exegetical reconstruction",
                "greek_term_attested": "συγκατάθεσις (synkatathesis)",
                "primary_sources": ["Cic. Acad. II.40-41", "Sextus M VII.151-157", "Plutarch Stoic. rep."],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_bobzien_2001_b1_master_argument_reconstruction",
        type="argument",
        label="Bobzien 2001 — Reconstruction de l'Argument Maitre (kurieuon logos) de Diodore Cronos",
        description=(
            "Reconstruction Bobzien 2001 §3.1.2 (p. 102-108) de "
            "l'Argument Maitre de Diodore Cronos. Premisses : (1) toute "
            "verite passee est necessaire ; (2) l'impossible ne suit pas "
            "du possible. Conclusion incompatible : (3) le possible = "
            "ce qui est ou sera actuellement vrai (collapsant "
            "possible-mais-non-actuel dans l'impossible). Diodore "
            "renonce a (3') la version 'opposee' (rien n'est possible "
            "qui ne soit ou ne sera) au profit de la negation de la "
            "contingence. Pour Bobzien, l'Argument Maitre est la cible "
            "directe contre laquelle Chrysippe articule son systeme "
            "modal : Chrysippe accepte les premisses (1) et (2) mais "
            "rejette (3) en distinguant Necessite et "
            "ce-qui-est-necessaire (cf. Bobzien §3.4). Source "
            "principale : Epictete Diss. II.19"
        ),
        description_en=(
            "Bobzien 2001 §3.1.2 (p. 102-108) reconstruction of "
            "Diodorus Cronus's Master Argument. Premises: (1) every "
            "past truth is necessary; (2) the impossible does not "
            "follow from the possible. Incompatible conclusion: (3) "
            "the possible = what is or will be actually true "
            "(collapsing possible-but-not-actual into impossible). For "
            "Bobzien, the Master Argument is the direct target against "
            "which Chrysippus articulates his modal system: Chrysippus "
            "accepts (1) + (2) but rejects (3) by distinguishing "
            "Necessity from that-which-is-necessary (Bobzien §3.4). "
            "Principal source: Epictetus Diss. II.19"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 102-108",
            chapter="Ch. 3 §3.1.2",
            bobzien_chapter_actual="Master Argument reconstruction — the Diodorean foil for Chrysippean modality",
            extra={
                "argument_type": "exegetical reconstruction",
                "primary_sources": ["Epictetus Diss. II.19", "Alexander In APr. 184", "Boethius In De Int."],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_bobzien_2001_b1_sea_battle_chrysippus_bivalence",
        type="argument",
        label="Bobzien 2001 — Chrysippe accepte la bivalence pour fonder le determinisme causal",
        description=(
            "Reconstruction Bobzien 2001 §2.1 (p. 59-86) : Chrysippe "
            "accepte la bivalence sans restriction pour les "
            "propositions au futur, contrairement a Aristote (De Int. 9, "
            "argument de la bataille navale) qui semble la restreindre, "
            "et a Epicure (§2.1.2, p. 75-86) qui la rejette explicitement "
            "pour preserver l'indeterminisme. L'argument chrysippeen de "
            "la bivalence : (1) toute proposition au futur a deja une "
            "valeur de verite determinee (P ou non-P) ; (2) une valeur "
            "de verite determinee presuppose un fait correspondant ; "
            "(3) le fait correspondant doit etre causalement determine ; "
            "(4) donc le futur est causalement determine. Bobzien "
            "souligne que pour Chrysippe la bivalence + la causation "
            "universelle se renforcent mutuellement"
        ),
        description_en=(
            "Bobzien 2001 §2.1 (p. 59-86) reconstruction: Chrysippus "
            "accepts unrestricted bivalence for future-tense "
            "propositions, contrary to Aristotle (De Int. 9 sea-battle "
            "argument) who appears to restrict it, and contrary to "
            "Epicurus (§2.1.2, p. 75-86) who explicitly rejects it to "
            "preserve indeterminism. Chrysippus's Bivalence Argument: "
            "(1) every future proposition has a determinate truth-"
            "value; (2) determinate truth-value presupposes a "
            "corresponding fact; (3) the fact must be causally "
            "determined; (4) therefore the future is causally "
            "determined"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 59-86",
            chapter="Ch. 2 §2.1",
            bobzien_chapter_actual="Chrysippus's Bivalence Argument vs Aristotle De Int. 9 vs Epicurean restriction",
            extra={
                "argument_type": "exegetical reconstruction",
                "primary_sources": ["Cic. Fat. 20-21", "Cic. Acad. II.97", "Aristotle De Int. 9", "Epicurus apud Cic. ND I"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_bobzien_2001_b1_pneumatic_causation_model",
        type="argument",
        label="Bobzien 2001 — Modele pneumatique de la causation stoicienne (body-to-body)",
        description=(
            "Argument Bobzien 2001 §1.1.2 (p. 18-27) : la causation "
            "stoicienne est fondamentalement body-to-body (corps a "
            "corps), non event-to-event (evenement a evenement). Le "
            "pneuma penetre tous les corps et transmet la causation "
            "via la tension (tonos). Cela distingue radicalement la "
            "causation stoicienne du modele humien moderne. Pour "
            "Bobzien, ce point est fondamental : la responsabilite "
            "morale est attribuee a un CORPS rationnel (l'agent) en "
            "tant que cause interne, pas a une succession "
            "d'evenements. Sources : Stobaeus Ecl. I.79 + DL VII.150 + "
            "Galien De Plac. Hipp. Plat. VII (Posidonius). L'objection "
            "anti-stoicienne des mouvements spontanes (Cic. Fat. "
            "23-25) est repondue par la pneumatic causation : il n'y "
            "a pas de mouvement spontane sans cause corporelle "
            "anterieure"
        ),
        description_en=(
            "Bobzien 2001 §1.1.2 (p. 18-27): Stoic causation is "
            "fundamentally body-to-body, not event-to-event. Pneuma "
            "pervades all bodies and transmits causation via tension "
            "(tonos). This radically distinguishes Stoic causation "
            "from the modern Humean model. Crucially: moral "
            "responsibility attaches to a rational BODY (the agent) "
            "as internal cause, not to a sequence of events. Sources: "
            "Stobaeus Ecl. I.79 + DL VII.150 + Galen De Plac. Hipp. "
            "Plat. VII"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 18-27",
            chapter="Ch. 1 §1.1.2",
            bobzien_chapter_actual="Pneumatic body-to-body causation as foundational Stoic ontology",
            extra={
                "argument_type": "exegetical reconstruction",
                "primary_sources": ["Stobaeus Ecl. I.79", "Diogenes Laertius VII.150", "Galen De Placitis VII"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_bobzien_2001_b1_critique_anachronistic_freewill",
        type="argument",
        label="Bobzien 2001 — Critique de la lecture anachronique du libre arbitre dans le Stoa ancien",
        description=(
            "Argument methodologique central Bobzien 2001 (introduction "
            "p. 1-15 + ch. 6-7 passim + §8.7) : la lecture du Stoa "
            "ancien a travers le prisme du probleme moderne du libre "
            "arbitre est ANACHRONIQUE et OBSCURCISSANTE. (1) Les "
            "Stoiciens ne posent pas la question 'sommes-nous libres "
            "ou determinés ?' au sens libertaire ; ils posent 'a quel "
            "agent attribuer causalement quelle action ?'. (2) Les "
            "traductions modernes (eph' hemin = 'free will', "
            "synkatathesis = 'free assent') introduisent un cadre "
            "conceptuel inexistant en grec. (3) Bobzien recommande "
            "rigoureusement de lire les Stoiciens dans leur propre "
            "cadre ontologique avant toute comparaison. (4) Critique "
            "specifique des lectures de Long & Sedley (HP 1987) et de "
            "Dihle (1982) sur ce point. Pour Bobzien (p. 277-280) : "
            "'under the surface of superficial resemblance to modern "
            "discussions of the free-will problem ... a very different "
            "ontological framework lurks'"
        ),
        description_en=(
            "Bobzien 2001 central methodological argument (intro p. "
            "1-15 + ch. 6-7 passim + §8.7): reading early Stoa through "
            "the modern free-will problem is ANACHRONISTIC and "
            "OBSCURING. (1) Stoics don't ask 'are we free or "
            "determined?' libertarian-style; they ask 'to which agent "
            "to causally attribute which action?'. (2) Modern "
            "translations (eph' hemin = 'free will') import "
            "non-existent conceptual frames. (3) Bobzien recommends "
            "rigorously reading Stoics within their own ontological "
            "frame. Quote (p. 277-280): 'under the surface of "
            "superficial resemblance to modern discussions of the "
            "free-will problem ... a very different ontological "
            "framework lurks'"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 1-15 passim + 277-280",
            chapter="Introduction + Ch. 6-7 + §8.7",
            bobzien_chapter_actual="Methodological critique of anachronistic free-will readings",
            extra={
                "argument_type": "methodological",
                "central_thesis": True,
                "verbatim_quote": "under the surface of superficial resemblance to modern discussions of the free-will problem ... a very different ontological framework lurks",
                "critiques_targets": ["Long & Sedley 1987", "Dihle 1982 (Theory of Will)"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_bobzien_2001_b1_epictetus_developmental_freedom",
        type="argument",
        label="Bobzien 2001 — Epictete developpe (mais n'invente pas) la notion stoicienne de liberte",
        description=(
            "Argument Bobzien 2001 ch. 7 (p. 330-357) : Epictete "
            "developpe la notion stoicienne de liberte (eleutheria) "
            "comme perfection morale + maitrise de soi, mais N'INVENTE "
            "PAS la liberte au sens libertaire. (1) Continuite avec le "
            "Stoa ancien : Epictete utilise eph' hemin au sens "
            "causatif a une face. (2) Innovation epictetienne : "
            "l'accent sur la prohairesis (capacite de choix rationnel) "
            "comme lieu propre de la liberte. (3) Liberte = "
            "independance des choses exterieures + acceptation des "
            "evenements selon la raison. (4) La 'capacite a faire "
            "autrement' chez Epictete est rhetorique-ethique, non "
            "metaphysique-libertaire. (5) Bobzien resiste a la lecture "
            "(qui sera celle de Frede 2011) selon laquelle Epictete "
            "introduirait la notion de libre arbitre. Sources : "
            "Diss. I.1, I.6, II.5, IV.1, IV.7 + Enchiridion 1, 14, 19, "
            "53. Caveat : cette these complete sera affinee mais "
            "maintenue dans Bobzien 2017 'Found in Translation'"
        ),
        description_en=(
            "Bobzien 2001 ch. 7 (p. 330-357): Epictetus develops the "
            "Stoic notion of freedom (eleutheria) as moral perfection "
            "+ self-mastery, but does NOT invent freedom in the "
            "libertarian sense. (1) Continuity with early Stoa: "
            "Epictetus uses eph' hemin in one-sided causative sense. "
            "(2) Epictetan innovation: emphasis on prohairesis as "
            "the proper locus of freedom. (3) Freedom = independence "
            "from external things + rational acceptance of events. "
            "(4) 'Ability to do otherwise' in Epictetus is rhetorical-"
            "ethical, not metaphysical-libertarian. (5) Bobzien "
            "resists the reading (which Frede 2011 will adopt) that "
            "Epictetus introduces the libertarian notion"
        ),
        period="Roman Imperial",
        metadata=bobzien_metadata(
            page_range="p. 330-357",
            chapter="Ch. 7",
            bobzien_chapter_actual="Epictetus's eleutheria as moral perfection, NOT libertarian innovation",
            extra={
                "argument_type": "exegetical thesis",
                "primary_sources": ["Epictetus Diss. I.1, I.6, II.5, IV.1, IV.7", "Enchiridion 1, 14, 19, 53"],
                "later_disagreement_with": "Frede 2011 (A Free Will: Origins of the Notion in Ancient Thought)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_bobzien_2001_b1_chrysippean_modal_system",
        type="argument",
        label="Bobzien 2001 — Chrysippe construit un systeme modal preservant la contingence",
        description=(
            "Reconstruction Bobzien 2001 §3.1.4 (p. 112-122) + §3.4 "
            "(p. 136-143) du systeme modal chrysippeen. Definitions : "
            "(1) le possible = ce qui admet la verite, ne rencontrant "
            "pas d'obstacle exterieur a sa realisation ; (2) "
            "l'impossible = ce qui rencontre un tel obstacle ; (3) le "
            "necessaire = le vrai-non-receptif-au-faux ; (4) le "
            "non-necessaire = le receptif-au-faux. Distinction "
            "fondamentale §3.4 entre Necessite (universelle, "
            "modale-au-second-degre) et ce-qui-est-necessaire "
            "(propositions specifiques). Chrysippe maintient ainsi : "
            "(a) tout occurrent est cause par le destin ; (b) certains "
            "occurrents sont neanmoins non-necessaires ; (c) donc "
            "determinisme + contingence coexistent. Critique anti-"
            "stoicienne (§3.2) : ce systeme est incompatible avec le "
            "determinisme stoicien. Reponse stoicienne (§3.3) : appel "
            "a des modalites epistemiques liees au destin"
        ),
        description_en=(
            "Bobzien 2001 §3.1.4 (p. 112-122) + §3.4 (p. 136-143) "
            "reconstruction of Chrysippean modal system. Definitions: "
            "(1) possible = admitting truth, encountering no external "
            "obstacle; (2) impossible = encountering such obstacle; "
            "(3) necessary = true-not-receptive-of-false; (4) "
            "non-necessary = receptive-of-false. Fundamental "
            "distinction §3.4 between Necessity (universal, "
            "second-order modal) and that-which-is-necessary (specific "
            "propositions). Chrysippus thus maintains: (a) all "
            "occurrents are caused by fate; (b) some are nevertheless "
            "non-necessary; (c) therefore determinism + contingency "
            "coexist"
        ),
        period="Hellenistic",
        metadata=bobzien_metadata(
            page_range="p. 112-143",
            chapter="Ch. 3 §3.1.4 + §3.4",
            bobzien_chapter_actual="Chrysippus's modal system — preserving contingency in determinism",
            extra={
                "argument_type": "logico-philosophical reconstruction",
                "primary_sources": ["Diogenes Laertius VII.75", "Cic. Fat. 12-15", "Alexander In APr."],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_bobzien_2001_b1_philopator_late_compatibilism",
        type="argument",
        label="Bobzien 2001 — PHILOPATOR : compatibilisme stoicien tardif raffine (Ch. 8)",
        description=(
            "Argument Bobzien 2001 ch. 8 (p. 358-412) : reconstruction "
            "d'une theorie compatibiliste stoicienne tardive (1er-2e "
            "siecle CE) attribuee conventionnellement a 'PHILOPATOR'. "
            "Innovations : (1) principe causal raffine — memes causes "
            "+ memes circonstances => memes effets (§8.2) ; (2) "
            "conception developpee de to_eph_hemin allant au-dela du "
            "di' hemon chrysippeen mais SANS atteindre le potestatif "
            "alexandrien (§8.4) ; (3) compatibilisme articule "
            "explicitement (§8.5) ; (4) cylindre repris dans theorie "
            "systematique (§8.6). Sources : Nemesius De Nat. Hom. 35 + "
            "Eusebe PE VI. PHILOPATOR represente le sommet du "
            "compatibilisme stoicien — apres lui, le paradigme se "
            "dissout dans la critique alexandrienne. Conclusion §8.7 "
            "(p. 396-412) : 'la montee et la chute du probleme de la "
            "liberte d'agir autrement et du determinisme causal'"
        ),
        description_en=(
            "Bobzien 2001 ch. 8 (p. 358-412): reconstruction of a "
            "late Stoic compatibilist theory (1st-2nd c. CE) "
            "conventionally attributed to 'PHILOPATOR'. Innovations: "
            "(1) refined causal principle — same causes + same "
            "circumstances => same effects (§8.2); (2) developed "
            "to_eph_hemin going beyond Chrysippean di' hemon but NOT "
            "reaching Alexandrian potestative sense (§8.4); (3) "
            "explicit compatibilism (§8.5); (4) cylinder taken up in "
            "systematic theory (§8.6). Sources: Nemesius De Nat. Hom. "
            "35 + Eusebius PE VI"
        ),
        period="Roman Imperial",
        metadata=bobzien_metadata(
            page_range="p. 358-412",
            chapter="Ch. 8",
            bobzien_chapter_actual="PHILOPATOR — refined late Stoic compatibilism",
            extra={
                "argument_type": "reconstructive scholarship",
                "primary_sources": ["Nemesius De Nat. Hom. 35", "Eusebius PE VI"],
                "attribution_caveat": "PHILOPATOR is a conventional name",
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="argument_bobzien_2001_b1_origen_idle_argument_reply",
        type="argument",
        label="Bobzien 2001 — Lecture de la reponse origenienne a l'argument paresseux (CC II.20)",
        description=(
            "Analyse Bobzien 2001 §5.2.2 (p. 205-208) de la reponse "
            "d'Origene a l'argument paresseux dans Contra Celsum II.20 "
            "(SC 132, 342.71-82 = Marcovich 95). Bobzien soutient que "
            "(1) Origene preserve l'argumentation chrysippeenne "
            "fondamentale (evenements co-fatedness) ; (2) il la "
            "transpose dans un cadre theologique chretien (providence "
            "divine au lieu de heimarmene) ; (3) le coeur logique de la "
            "refutation reste identifiable comme stoicien-chrysippeen ; "
            "(4) la transposition n'affaiblit pas la structure "
            "argumentative. Cette analyse est tres importante pour H3 "
            "(Origene chretien et sources stoiciennes). Bobzien compare "
            "Origene a Cic. Fat. 30 + Eus. PE VI.8.25-38 pour montrer "
            "la convergence des trois reponses sur la solution "
            "co-fatedness, par-dela les differences theologiques"
        ),
        description_en=(
            "Bobzien 2001 §5.2.2 (p. 205-208) analysis of Origen's "
            "reply to the Idle Argument in Contra Celsum II.20 (SC "
            "132, 342.71-82 = Marcovich 95). Bobzien argues: (1) "
            "Origen preserves the fundamental Chrysippean structure "
            "(co-fated events); (2) he transposes it into Christian "
            "theological frame (divine providence instead of "
            "heimarmene); (3) the logical core of the refutation "
            "remains identifiably Stoic-Chrysippean; (4) "
            "transposition does not weaken the argumentative "
            "structure. Bobzien compares Origen to Cic. Fat. 30 + Eus. "
            "PE VI.8.25-38 to show three-way convergence"
        ),
        period="Patristic",
        metadata=bobzien_metadata(
            page_range="p. 205-208",
            chapter="Ch. 5 §5.2.2",
            bobzien_chapter_actual="Origen's Contra Celsum II.20 as Christian transposition of Chrysippean refutation",
            extra={
                "argument_type": "exegetical analysis",
                "primary_sources": ["Origen Contra Celsum II.20", "Cic. Fat. 30", "Eus. PE VI.8.25-38"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_bobzien_2001_b1_cylinder_in_later_fate_theory",
        type="argument",
        label="Bobzien 2001 — Reprise de l'analogie du cylindre dans la theorie tardive du destin (§8.6)",
        description=(
            "Argument Bobzien 2001 §8.6 (p. 394-396) : l'analogie "
            "chrysippeenne du cylindre est reprise et systematisee dans "
            "la theorie stoicienne tardive (PHILOPATOR + sources "
            "preservees par Nemesius). La reprise tardive : (1) "
            "conserve la distinction antecedent vs proximate cause ; "
            "(2) integre l'analogie dans un cadre causal plus precis "
            "(principe causal raffine §8.2) ; (3) la mobilise dans une "
            "defense explicite du compatibilisme ; (4) prepare "
            "implicitement le terrain pour la critique alexandrienne. "
            "Pour Bobzien, cette reprise tardive est philologiquement "
            "importante car elle montre la continuite + l'evolution "
            "du Stoa apres Chrysippe — sans pour autant introduire "
            "la notion libertaire de libre arbitre"
        ),
        description_en=(
            "Bobzien 2001 §8.6 (p. 394-396): the Chrysippean cylinder "
            "analogy is taken up and systematized in late Stoic "
            "theory (PHILOPATOR + sources preserved by Nemesius). The "
            "late reprise: (1) preserves antecedent vs proximate cause "
            "distinction; (2) integrates the analogy in a more precise "
            "causal frame (refined causal principle §8.2); (3) deploys "
            "it in explicit defense of compatibilism; (4) implicitly "
            "prepares the ground for Alexandrian critique"
        ),
        period="Roman Imperial",
        metadata=bobzien_metadata(
            page_range="p. 394-396",
            chapter="Ch. 8 §8.6",
            bobzien_chapter_actual="Cylinder analogy in late Stoic fate theory",
            extra={
                "argument_type": "reconstruction of late Stoic appropriation",
                "primary_sources": ["Nemesius De Nat. Hom. 35"],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="argument_bobzien_2001_b1_rise_fall_freedom_problem",
        type="argument",
        label="Bobzien 2001 — La montee et la chute du probleme de la liberte d'agir autrement (§8.7)",
        description=(
            "Argument-conclusion Bobzien 2001 §8.7 (p. 396-412) : trace "
            "l'emergence et l'extinction du probleme de la liberte "
            "d'agir autrement (freedom to do otherwise) en philosophie "
            "ancienne. (1) Le Stoa classique (Zenon, Cleanthe, "
            "Chrysippe) ne pose PAS le probleme. (2) Carneade le "
            "soulève dialectiquement contre le Stoa (via Cic. Fat. 23-25 "
            "+ 31-33) mais ne le construit pas comme position propre. "
            "(3) Le Stoa tardif (PHILOPATOR) developpe le "
            "compatibilisme sans introduire la liberte d'agir "
            "autrement. (4) Alexandre d'Aphrodise (2e siecle CE) "
            "construit pour la premiere fois explicitement la position "
            "two-sided potestative — c'est la 'montee' du probleme. "
            "(5) Apres Alexandre, le probleme se diffuse dans les "
            "ecoles aristoteliciennes + chretiennes. (6) La 'chute' = "
            "l'absorption du probleme dans des cadres theologiques "
            "(predestination + grace) qui transforment la question. "
            "Pour Bobzien, cette these est complementee par son 1998 "
            "Phronesis companion paper"
        ),
        description_en=(
            "Bobzien 2001 §8.7 (p. 396-412) concluding argument: "
            "traces the emergence and extinction of the freedom-to-"
            "do-otherwise problem in ancient philosophy. (1) Classical "
            "Stoa (Zeno, Cleanthes, Chrysippus) does NOT pose the "
            "problem. (2) Carneades dialectically raises it against "
            "the Stoa but does not construct it as his own position. "
            "(3) Late Stoa (PHILOPATOR) develops compatibilism "
            "without introducing freedom to do otherwise. (4) "
            "Alexander of Aphrodisias (2nd c. CE) first constructs "
            "the two-sided potestative position explicitly — the "
            "'rise' of the problem. (5) After Alexander, the problem "
            "diffuses through Aristotelian + Christian schools. (6) "
            "The 'fall' = absorption into theological frames "
            "(predestination + grace)"
        ),
        period="Roman Imperial",
        metadata=bobzien_metadata(
            page_range="p. 396-412",
            chapter="Ch. 8 §8.7",
            bobzien_chapter_actual="Rise and fall of the freedom-to-do-otherwise problem — concluding thesis",
            extra={
                "argument_type": "historical-conceptual narrative",
                "central_thesis": True,
                "companion_paper": "Bobzien 1998 Phronesis 'The Inadvertent Conception and Late Birth of the Free-Will Problem'",
            },
        ),
        confidence=0.95,
    ),
]
