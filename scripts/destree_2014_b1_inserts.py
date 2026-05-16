"""Destrée/Salles/Zingano 2014 B1 — NEW_INSERTS lists.

Bilingual FR/EN descriptions. French uses correct accents; English compact.

Sections:
  - PUBLICATION : 1 master node for the edited volume
  - PERSONS     : new scholar nodes for contributors absent from the KG
                  (Vimercati, Vogt, Gómez, Boeri, Morel, Bonazzi, Horn, Steel,
                   Wildberg, Johnson, Taormina, M. Frede)
  - WORKS       : Aristotle Eudemian Ethics (missing in KG), Porphyry
                  Peri tou eph' hêmin (Stobaeus frr. 268-271 Smith), Proclus
                  De Providentia, Fato et eo quod in nobis (the *third* Tria
                  Opuscula treatise — central for Steel's chapter)
  - CONCEPTS    : 1 hypothetical_fate clarification (already exists but we add
                  a Bonazzi-anchored confrontation concept), plus
                  concept_to_eph_hemin (general unified term node), and
                  Plotinian/Stoic distinction concept (only if absent).
                  Most "central" concepts already exist — we mainly UPDATE
                  rather than INSERT.
  - SYNTHESES   : 20 chapter syntheses (one per chapter substantively read)
  - ARGUMENTS   : 22 scholarly arguments — one or two per chapter, capturing
                  the central thesis
"""
from __future__ import annotations

from typing import Any

from destree_2014_b1_utils import DESTREE_BIBTEX_KEY, DESTREE_PUB_ID, destree_metadata, dump_metadata


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
# PUBLICATION (1)
# =============================================================================

NEW_PUBLICATION: list[dict[str, Any]] = [
    _node(
        id=DESTREE_PUB_ID,
        type="publication",
        label="Destrée, Salles & Zingano (eds.), What is Up to Us? Studies on Agency and Responsibility in Ancient Philosophy (2014)",
        description=(
            "Volume collectif édité par Pierre Destrée, Ricardo Salles et "
            "Marco Zingano, publié en 2014 par Academia Verlag (Sankt "
            "Augustin) dans la série Studies in Ancient Moral and Political "
            "Philosophy. Réunit vingt contributions étudiant la notion de "
            "ce qui dépend de nous — τὸ ἐφ' ἡμῖν / in nostra potestate / "
            "in nobis — depuis Démocrite et Platon jusqu'à Augustin, "
            "Proclus et Simplicius, en passant par Aristote, les stoïciens "
            "(Chrysippe, Panétius, Épictète, Marc Aurèle), Alexandre "
            "d'Aphrodise, Épicure, Cicéron, Plotin, Porphyre et les "
            "platoniciens médiens. Le volume s'ouvre par une introduction "
            "synoptique des trois éditeurs et se clôt sur la réimpression "
            "(avec permission) d'un article de Michael Frede paru en 2007 "
            "dans une revue grecque, consacré à τὸ ἐφ' ἡμῖν dans la "
            "philosophie antique — édité à titre posthume par Susan Sauvé "
            "Meyer. Toutes les contributions sur Aristote défendent une "
            "lecture déterministe ou anti-indéterministe (Frede D., "
            "Bobzien, Sauvé Meyer, Echeñique). Le volume aligne donc une "
            "défense méthodique de la thèse Bobzien 1998 : le problème "
            "moderne du libre arbitre n'émerge pas avant l'Antiquité "
            "tardive. Pierre Destrée est aussi co-éditeur du chapitre "
            "sur Platon et le mythe d'Er (déjà indexé séparément comme "
            "pub_destree_2014_plato_er)"
        ),
        description_en=(
            "Edited volume by Pierre Destrée, Ricardo Salles and Marco "
            "Zingano, published in 2014 by Academia Verlag (Sankt Augustin) "
            "in the series Studies in Ancient Moral and Political "
            "Philosophy. Twenty contributions on what depends on us — to "
            "eph' hêmin / in nostra potestate / in nobis — from Democritus "
            "and Plato through Augustine, Proclus and Simplicius, "
            "encompassing Aristotle, the Stoics (Chrysippus, Panaetius, "
            "Epictetus, Marcus Aurelius), Alexander of Aphrodisias, "
            "Epicurus, Cicero, Plotinus, Porphyry and the Middle "
            "Platonists. Opens with synoptic introduction by the three "
            "editors and closes on reprint of Michael Frede's 2007 paper "
            "on to eph' hêmin in ancient philosophy, prepared "
            "posthumously by Susan Sauvé Meyer. All Aristotle chapters "
            "uphold a deterministic or anti-indeterministic reading "
            "(D. Frede, Bobzien, Sauvé Meyer, Echeñique). The volume thus "
            "constitutes a methodical defense of the Bobzien 1998 thesis: "
            "the modern free-will problem does not emerge before late "
            "antiquity"
        ),
        period=None,
        metadata={
            "type": "edited_volume",
            "year": 2014,
            "editors": ["Pierre Destrée", "Ricardo Salles", "Marco Zingano"],
            "publisher": "Academia Verlag",
            "publisher_location": "Sankt Augustin",
            "series": "Studies in Ancient Moral and Political Philosophy",
            "isbn": "978-3-89665-634-6",
            "page_count": 363,
            "chapter_count": 20,
            "bibtex_key": DESTREE_BIBTEX_KEY,
            "source_file": "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/01_Philosophie_antique/Destrée - 2014 - What is Up to Us Studies on Agency and Responsibi.pdf",
            "key_claim": (
                "The notion of τὸ ἐφ' ἡμῖν is reconstructed historically as "
                "an evolving technical term, beginning informally with "
                "Democritus and Plato, becoming a technical (but not "
                "indeterministic) concept in Aristotle, and only acquiring "
                "the modern resonance of free will in late Stoicism "
                "(Epictetus) and Christian / Neoplatonist contexts"
            ),
            "thematic_axes": [
                "to eph' hêmin / what is up to us",
                "moral responsibility",
                "voluntariness (hekousion)",
                "deliberate choice (prohairesis)",
                "Stoic assent (sunkatathesis)",
                "fate (heimarmenê)",
                "compatibilism / incompatibilism (modern terms applied with caveats)",
            ],
        },
        confidence=0.99,
    ),
]


# =============================================================================
# PERSONS — new scholar nodes (12)
# =============================================================================

NEW_PERSONS: list[dict[str, Any]] = [
    _node(
        id="scholar_destr_e_p_salles_zingano_eds",
        type="person",
        label="Destrée / Salles / Zingano (editors)",
        description=(
            "Triple éditorial du volume collectif Destrée/Salles/Zingano "
            "2014. Pierre Destrée (UCLouvain), Ricardo Salles (UNAM) et "
            "Marco Zingano (USP) ont co-organisé en 2010 le colloque de "
            "São Paulo « A noção de eph' hêmin no Pós-Aristotelismo » d'où "
            "est issu le volume. Nœud de coordination éditoriale créé "
            "pour permettre l'attribution claimed_by des syntheses de ce "
            "volume sans surcharger les trois nœuds de scholars "
            "individuels existants (scholar_destr_e_p, plus deux à créer)"
        ),
        description_en=(
            "Editorial trio of the Destrée/Salles/Zingano 2014 volume. "
            "Pierre Destrée (UCLouvain), Ricardo Salles (UNAM) and Marco "
            "Zingano (USP) co-organized the 2010 São Paulo colloquium "
            "from which the volume emerged. Coordination node for "
            "synthesis claimed_by attribution"
        ),
        period="Contemporary",
        metadata={
            "role": "editorial_group",
            "members": [
                "scholar_destr_e_p",
                "scholar_salles_ricardo",
                "scholar_zingano_marco",
            ],
            "publication": DESTREE_PUB_ID,
            "bibtex_key": DESTREE_BIBTEX_KEY,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_salles_ricardo",
        type="person",
        label="Ricardo Salles",
        description=(
            "Ricardo Salles, philosophe argentin-mexicain, professeur à "
            "l'Instituto de Investigaciones Filosóficas de l'UNAM (Mexico). "
            "Spécialiste du stoïcisme, du déterminisme stoïcien et de la "
            "philosophie de l'action ancienne. Auteur de The Stoics on "
            "Determinism and Compatibilism (Ashgate 2005), éditeur de God "
            "and Cosmos in Stoicism (OUP 2009). Co-éditeur du volume "
            "Destrée/Salles/Zingano 2014 et auteur du ch. 8 « Epictetus "
            "and the causal conception of moral responsibility and what is "
            "eph' hêmin » défendant la lecture causale de l'ἐφ' ἡμῖν "
            "épictétéen en continuité avec Chrysippe"
        ),
        description_en=(
            "Ricardo Salles, Argentinian-Mexican philosopher, professor at "
            "the Instituto de Investigaciones Filosóficas, UNAM. "
            "Specialist of Stoicism, Stoic determinism, and ancient "
            "action theory. Author of The Stoics on Determinism and "
            "Compatibilism (Ashgate 2005), editor of God and Cosmos in "
            "Stoicism (OUP 2009). Co-editor of Destrée/Salles/Zingano 2014 "
            "and author of ch. 8 on Epictetus's causal conception of moral "
            "responsibility in continuity with Chrysippus"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Salles",
            "given_names": "Ricardo",
            "specialty": "Stoicism, determinism, compatibilism, philosophy of action",
            "affiliations": ["Instituto de Investigaciones Filosóficas, UNAM"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_zingano_marco",
        type="person",
        label="Marco Zingano",
        description=(
            "Marco Zingano, philosophe brésilien, professeur à "
            "l'Universidade de São Paulo (USP). Spécialiste d'Aristote et "
            "d'Alexandre d'Aphrodise. Auteur de plusieurs études sur "
            "l'éthique aristotélicienne et la théorie de l'action. "
            "Co-éditeur du volume Destrée/Salles/Zingano 2014 et auteur "
            "du ch. 9 « Alexander and Aristotle on character and action », "
            "où il propose une lecture du libertarianisme d'Alexandre "
            "compatible avec un déterminisme psychologique rigide fondé "
            "sur la notion de caractère"
        ),
        description_en=(
            "Marco Zingano, Brazilian philosopher, professor at the "
            "Universidade de São Paulo. Specialist of Aristotle and "
            "Alexander of Aphrodisias. Co-editor of Destrée/Salles/Zingano "
            "2014 and author of ch. 9 on Alexander's libertarianism, "
            "proposing it as compatible with rigid psychological "
            "determinism grounded on character"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Zingano",
            "given_names": "Marco",
            "specialty": "Aristotle, Alexander of Aphrodisias, ethics, action theory",
            "affiliations": ["Universidade de São Paulo"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_johnson_monte",
        type="person",
        label="Monte Ransome Johnson",
        description=(
            "Monte Ransome Johnson, philosophe états-unien, professeur "
            "associé à l'Université de Californie à San Diego (UCSD). "
            "Spécialiste de la philosophie présocratique, de l'éthique "
            "démocritéenne et d'Aristote. Auteur du ch. 1 du volume "
            "Destrée 2014, « Changing our minds: Democritus on what is up "
            "to us », défendant une lecture intellectualiste et "
            "non-fataliste de l'éthique démocritéenne fondée sur la "
            "plasticité de la nature humaine et le rôle de l'enseignement "
            "et du jugement (gnômê)"
        ),
        description_en=(
            "Monte Ransome Johnson, American philosopher, associate "
            "professor at UC San Diego. Specialist of Presocratic "
            "philosophy, Democritean ethics, and Aristotle. Author of "
            "ch. 1 of Destrée 2014, defending an intellectualist and "
            "non-fatalist reading of Democritean ethics grounded on the "
            "plasticity of human nature and the role of teaching and "
            "judgment (gnômê)"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Johnson",
            "given_names": "Monte Ransome",
            "specialty": "Presocratic philosophy, Democritus, Aristotle",
            "affiliations": ["University of California, San Diego"],
            "confidence": 0.9,
        },
        confidence=0.9,
    ),
    _node(
        id="scholar_vogt_katja",
        type="person",
        label="Katja Maria Vogt",
        description=(
            "Katja Maria Vogt, philosophe allemande, professeure à "
            "l'Université Columbia (New York). Spécialiste du stoïcisme, "
            "du scepticisme académicien et de la philosophie de l'action "
            "ancienne. Auteure du ch. 5 du volume Destrée 2014, « I shall "
            "do what I did: Stoic views on action », analysant le cas "
            "type de l'agent stoïcien qui assent à une représentation "
            "(« prends le parapluie ») et l'interprétant à travers la "
            "thèse cyclique stoïcienne (ekpurôsis / palingénésie) : "
            "l'agent fera ce qu'il a fait dans les cycles précédents"
        ),
        description_en=(
            "Katja Maria Vogt, German philosopher, professor at Columbia "
            "University. Specialist of Stoicism, Academic skepticism, and "
            "ancient action theory. Author of ch. 5 of Destrée 2014 on "
            "the Stoic agent who assents to an impression — interpreted "
            "through Stoic cyclic theory: the agent will do what she did "
            "in previous world-cycles"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Vogt",
            "given_names": "Katja Maria",
            "specialty": "Stoicism, Academic skepticism, action theory",
            "affiliations": ["Columbia University"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_gomez_laura",
        type="person",
        label="Laura Liliana Gómez",
        description=(
            "Laura Liliana Gómez, philosophe latino-américaine, "
            "spécialiste du stoïcisme ancien. Auteure du ch. 6 du volume "
            "Destrée 2014, « Chrysippean compatibilistic theory of fate, "
            "what is up to us, and moral responsibility », analysant la "
            "stratégie de Chrysippe pour défendre la compatibilité entre "
            "destin stoïcien et responsabilité morale par sa réaction "
            "aux objections antifatalistes adressées à l'École"
        ),
        description_en=(
            "Laura Liliana Gómez, Latin American philosopher, specialist "
            "of ancient Stoicism. Author of ch. 6 of Destrée 2014 on "
            "Chrysippus's compatibilist strategy reconstructed from his "
            "responses to antifatalist objections"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Gómez",
            "given_names": "Laura Liliana",
            "specialty": "Stoicism, Chrysippus, fate and moral responsibility",
            "confidence": 0.85,
        },
        confidence=0.85,
    ),
    _node(
        id="scholar_vimercati_emmanuele",
        type="person",
        label="Emmanuele Vimercati",
        description=(
            "Emmanuele Vimercati, philologue italien, professeur à la "
            "Pontificia Università Lateranense (Rome). Spécialiste du "
            "stoïcisme moyen et de Panétius. Éditeur des fragments de "
            "Panétius (Vimercati 2002). Auteur du ch. 7 du volume Destrée "
            "2014, « Panaetius on self-knowledge and moral "
            "responsibility », montrant que l'unique occurrence "
            "panétienne de τὸ ἐφ' ἡμῖν (Némésius Nat. hom. 26 = Panaetius "
            "fr. B26 Vimercati) confirme une articulation entre oikéiôsis, "
            "connaissance de soi et responsabilité, et que la théorie "
            "panétienne des quatre personae (Cic. Off. I) laisse place à "
            "des choses ἐφ' ἡμῖν via le iudicium/voluntas"
        ),
        description_en=(
            "Emmanuele Vimercati, Italian classicist, professor at the "
            "Pontifical Lateran University. Specialist of Middle Stoicism "
            "and Panaetius. Editor of Panaetius's fragments (Vimercati "
            "2002). Author of ch. 7 of Destrée 2014, arguing that the "
            "single Panaetian occurrence of to eph' hêmin (Nemesius "
            "Nat. hom. 26 = Panaet. fr. B26 Vim.) confirms a linkage "
            "between oikeiôsis, self-knowledge and responsibility"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Vimercati",
            "given_names": "Emmanuele",
            "specialty": "Middle Stoicism, Panaetius, Roman Stoicism",
            "affiliations": ["Pontificia Università Lateranense, Roma"],
            "key_works": ["Vimercati 2002 (ed.) Panezio, Testimonianze e frammenti"],
            "confidence": 0.9,
        },
        confidence=0.9,
    ),
    _node(
        id="scholar_boeri_marcelo",
        type="person",
        label="Marcelo D. Boeri",
        description=(
            "Marcelo D. Boeri, philosophe argentino-chilien, professeur à "
            "l'Université du Chili (Pontificia Universidad Católica de "
            "Chile, puis Adolfo Ibáñez). Spécialiste du stoïcisme et de "
            "Platon. Auteur du ch. 10 du volume Destrée 2014, « Present "
            "time and indifferents: making room for 'what depends on us' "
            "in Marcus Aurelius », démontrant que la liaison entre "
            "présent et indifférents est cruciale pour comprendre τὸ ἐφ' "
            "ἡμῖν chez Marc Aurèle, et que l'esprit confère 'réalité' aux "
            "choses extérieures, donnant valeur ou non-valeur dans la vie "
            "pratique"
        ),
        description_en=(
            "Marcelo D. Boeri, Argentinian-Chilean philosopher, professor "
            "at Adolfo Ibáñez University. Specialist of Stoicism and "
            "Plato. Author of ch. 10 of Destrée 2014 on the function and "
            "value of to eph' hêmin in Marcus Aurelius, showing the "
            "crucial connection between the present and indifferents"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Boeri",
            "given_names": "Marcelo D.",
            "specialty": "Stoicism, Plato, Marcus Aurelius",
            "affiliations": ["Universidad Adolfo Ibáñez", "Pontificia Universidad Católica de Chile"],
            "confidence": 0.9,
        },
        confidence=0.9,
    ),
    _node(
        id="scholar_morel_pierre_marie",
        type="person",
        label="Pierre-Marie Morel",
        description=(
            "Pierre-Marie Morel, philosophe français, professeur à "
            "l'Université Paris 1 Panthéon-Sorbonne. Spécialiste de "
            "l'atomisme ancien (Démocrite, Épicure) et d'Aristote. Auteur "
            "du ch. 12 du volume Destrée 2014, « The Epicurean 'up to us': "
            "not to be proved », défendant que τὸ ἐφ' ἡμῖν chez Épicure "
            "n'est pas un *demonstrandum* mais une *évidence primaire* — "
            "thèse étayée par trois types d'arguments : cosmologiques "
            "(Lettre à Ménécée), éthiques (Sur la nature, livre XXV) et "
            "épistémologiques (logique de l'absurdité de la négation)"
        ),
        description_en=(
            "Pierre-Marie Morel, French philosopher, professor at the "
            "Université Paris 1 Panthéon-Sorbonne. Specialist of ancient "
            "atomism (Democritus, Epicurus) and Aristotle. Author of "
            "ch. 12 of Destrée 2014, arguing that the Epicurean to eph' "
            "hêmin is not a demonstrandum but a primary evidence — "
            "supported by three argument types: cosmological, ethical, "
            "epistemological"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Morel",
            "given_names": "Pierre-Marie",
            "specialty": "ancient atomism, Democritus, Epicurus, Aristotle",
            "affiliations": ["Université Paris 1 Panthéon-Sorbonne"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_taormina_daniela",
        type="person",
        label="Daniela Patrizia Taormina",
        description=(
            "Daniela Patrizia Taormina, philologue italienne, professeure "
            "à l'Université de Rome Tor Vergata. Spécialiste de Plotin, "
            "Porphyre et Jamblique. Auteure du ch. 14 du volume Destrée "
            "2014, « Choice (hairesis), self-determination (to autexousion) "
            "and what is in our power (to eph' hêmin) in Porphyry's "
            "interpretation of the myth of Er », étudiant les fragments "
            "268-271 Smith (= Stobée Anth. II 8 39-42) où Porphyre relit "
            "le mythe d'Er à la lumière des réflexions hellénistiques sur "
            "la causalité et la responsabilité, en restreignant τὸ ἐφ' "
            "ἡμῖν à la partie rationnelle de l'âme humaine"
        ),
        description_en=(
            "Daniela Patrizia Taormina, Italian classicist, professor at "
            "the Università di Roma Tor Vergata. Specialist of Plotinus, "
            "Porphyry, Iamblichus. Author of ch. 14 of Destrée 2014 on "
            "Porphyry's interpretation of the Myth of Er in frr. 268-271 "
            "Smith (= Stobaeus Anth. II 8 39-42), where Porphyry "
            "restricts to eph' hêmin to the rational part of the human "
            "soul"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Taormina",
            "given_names": "Daniela Patrizia",
            "specialty": "Neoplatonism, Plotinus, Porphyry, Iamblichus",
            "affiliations": ["Università di Roma Tor Vergata"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_bonazzi_mauro",
        type="person",
        label="Mauro Bonazzi",
        description=(
            "Mauro Bonazzi, philologue italien, professeur à l'Université "
            "d'Utrecht (anciennement Milan). Spécialiste du platonisme "
            "médian et de l'Académie hellénistique. Auteur du ch. 15 du "
            "volume Destrée 2014, « Middle Platonists on fate and human "
            "autonomy: a confrontation with the Stoics », étudiant la "
            "doctrine platonicienne médiane du *destin hypothétique* "
            "(héimarménê ex hypothéseôs) — réponse platonicienne à "
            "l'attribution conditionnelle de la responsabilité face au "
            "déterminisme stoïcien. Bonazzi conclut que cette doctrine "
            "rend compte d'actions individuelles, mais non de leurs "
            "rapports mutuels"
        ),
        description_en=(
            "Mauro Bonazzi, Italian classicist, professor at Utrecht "
            "University (formerly Milan). Specialist of Middle Platonism "
            "and the Hellenistic Academy. Author of ch. 15 of Destrée "
            "2014 on the Middle Platonist doctrine of hypothetical fate "
            "(heimarmenê ex hypotheseôs) as Platonist confrontation with "
            "Stoic determinism. Bonazzi concludes the doctrine accounts "
            "for individual actions but not their mutual relations"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Bonazzi",
            "given_names": "Mauro",
            "specialty": "Middle Platonism, Hellenistic Academy, Plutarch",
            "affiliations": ["Universiteit Utrecht", "Università degli Studi di Milano"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_horn_christoph",
        type="person",
        label="Christoph Horn",
        description=(
            "Christoph Horn, philosophe allemand, professeur à "
            "l'Université de Bonn. Spécialiste de Platon, Plotin, "
            "Augustin et de la philosophie politique antique. Auteur du "
            "ch. 16 du volume Destrée 2014, « How close is Augustine's "
            "liberum arbitrium to the concept of to eph' hêmin? », "
            "soutenant que le concept augustinien de liberum arbitrium "
            "remplit la fonction du τὸ ἐφ' ἡμῖν tout en l'élargissant : "
            "il décrit non seulement ce qui est en notre disposition mais "
            "aussi le périmètre de la responsabilité morale d'un agent "
            "individuel"
        ),
        description_en=(
            "Christoph Horn, German philosopher, professor at the "
            "University of Bonn. Specialist of Plato, Plotinus, "
            "Augustine, and ancient political philosophy. Author of "
            "ch. 16 of Destrée 2014, arguing that Augustinian liberum "
            "arbitrium plays the role of to eph' hêmin but goes beyond "
            "it by describing the scope of individual moral "
            "responsibility"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Horn",
            "given_names": "Christoph",
            "specialty": "Plato, Plotinus, Augustine, ancient ethics",
            "affiliations": ["Rheinische Friedrich-Wilhelms-Universität Bonn"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_steel_carlos",
        type="person",
        label="Carlos Steel",
        description=(
            "Carlos Steel, philologue belge, professeur émérite à la KU "
            "Leuven (De Wulf-Mansion Centre for Ancient, Medieval and "
            "Renaissance Philosophy). Spécialiste de Proclus, Damascius, "
            "Olympiodore et du néoplatonisme tardif. Co-éditeur de la "
            "rétroversion grecque des Tria Opuscula de Proclus. Auteur du "
            "ch. 17 du volume Destrée 2014, « Human or divine freedom: "
            "Proclus on what is up to us », étudiant le troisième traité "
            "des Tria Opuscula (De Providentia, Fato et eo quod in nobis) "
            "où Proclus répond à l'engineer Théodore défendant un "
            "déterminisme mécaniste radical"
        ),
        description_en=(
            "Carlos Steel, Belgian classicist, professor emeritus at KU "
            "Leuven (De Wulf-Mansion Centre). Specialist of Proclus, "
            "Damascius, Olympiodorus, and late Neoplatonism. Co-editor of "
            "the Greek retroversion of Proclus's Tria Opuscula. Author of "
            "ch. 17 of Destrée 2014 on Proclus's third opusculum, in "
            "which he answers Theodore the engineer's radical mechanistic "
            "determinism"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Steel",
            "given_names": "Carlos",
            "specialty": "Neoplatonism, Proclus, Damascius, late ancient philosophy",
            "affiliations": ["KU Leuven"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_wildberg_christian",
        type="person",
        label="Christian Wildberg",
        description=(
            "Christian Wildberg, philologue germano-américain, professeur "
            "à l'Université de Pittsburgh (anciennement Princeton). "
            "Spécialiste de Simplicius, Philopon et de la philosophie de "
            "la nature néoplatonicienne. Auteur du ch. 18 du volume "
            "Destrée 2014, « The will and its freedom: Epictetus and "
            "Simplicius on what is up to us », étudiant la lecture "
            "néoplatonicienne tardive d'Épictète par Simplicius dans son "
            "Commentaire sur l'Enchiridion, écrit probablement après "
            "l'exil sassanide (529 CE)"
        ),
        description_en=(
            "Christian Wildberg, German-American classicist, professor at "
            "the University of Pittsburgh (formerly Princeton). "
            "Specialist of Simplicius, Philoponus, and Neoplatonist "
            "natural philosophy. Author of ch. 18 of Destrée 2014 on "
            "Simplicius's late Neoplatonist reading of Epictetus in the "
            "Commentary on the Handbook, probably written after the "
            "Sasanian exile (529 CE)"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Wildberg",
            "given_names": "Christian",
            "specialty": "Neoplatonism, Simplicius, Philoponus",
            "affiliations": ["University of Pittsburgh", "Princeton University (former)"],
            "confidence": 0.95,
        },
        confidence=0.95,
    ),
    _node(
        id="scholar_frede_michael",
        type="person",
        label="Michael Frede",
        description=(
            "Michael Frede (1940-2007), philosophe et philologue allemand, "
            "professeur à Princeton puis à Oxford (Keble College). Élève "
            "de Günther Patzig à Göttingen, l'une des figures majeures de "
            "l'étude de la philosophie hellénistique au XXe siècle. "
            "Spécialiste du stoïcisme, du scepticisme antique, de Galien "
            "et d'Aristote. Auteur posthume de A Free Will: Origins of "
            "the Notion in Ancient Thought (UC Press 2011), ses Sather "
            "Lectures de 1997-98 éditées par A. A. Long. Décédé en 2007 "
            "lors d'un accident de baignade à Skala Eressou (Lesbos). Sa "
            "contribution au volume Destrée 2014 est la réimpression "
            "(avec permission, et avec l'aide de Katerina Ierodiakonou et "
            "Susan Sauvé Meyer) de son article paru en 2007 dans une "
            "revue grecque sur τὸ ἐφ' ἡμῖν dans la philosophie antique"
        ),
        description_en=(
            "Michael Frede (1940-2007), German philosopher and "
            "classicist, professor at Princeton then Oxford (Keble "
            "College). Student of Günther Patzig at Göttingen, one of "
            "the major figures of 20th-century Hellenistic philosophy "
            "studies. Author of the posthumous A Free Will: Origins of "
            "the Notion in Ancient Thought (UC Press 2011), his "
            "1997-98 Sather Lectures edited by A. A. Long. Died in 2007 "
            "in a swimming accident at Skala Eressou (Lesbos). His "
            "contribution to Destrée 2014 is the permission-reprint of "
            "his 2007 Greek-journal article on to eph' hêmin in ancient "
            "philosophy, prepared posthumously by Katerina Ierodiakonou "
            "and Susan Sauvé Meyer"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "surname": "Frede",
            "given_names": "Michael",
            "birth": 1940,
            "death": 2007,
            "specialty": "Hellenistic philosophy, Aristotle, Galen, scepticism, Stoicism",
            "affiliations": ["Princeton University", "University of Oxford (Keble College)"],
            "key_works": [
                "Frede 2011, A Free Will: Origins of the Notion in Ancient Thought (UC Press, Sather Lectures)",
                "Frede 2007, 'On the existence of an antiquity-spanning concept of to eph' hêmin'",
                "Frede 1987, Essays in Ancient Philosophy (Oxford)",
            ],
            "wikidata_qid": "Q1928930",
            "confidence": 0.99,
        },
        confidence=0.99,
    ),
]


# =============================================================================
# WORKS (3)
# =============================================================================

NEW_WORKS: list[dict[str, Any]] = [
    _node(
        id="work_aristotle_eudemian_ethics",
        type="work",
        label="Aristote, Éthique à Eudème (Ethica Eudemia)",
        description=(
            "Éthique à Eudème (Ἠθικά Εὐδήμεια), traité éthique d'Aristote "
            "en huit livres (dont trois communs avec l'Éthique à "
            "Nicomaque : EE IV-V-VI = EN V-VI-VII), longtemps tenu pour "
            "plus ancien que l'EN mais aujourd'hui considéré comme "
            "globalement contemporain par la majorité des spécialistes "
            "(Kenny, Frede D., Sauvé Meyer). Pour le volume Destrée 2014, "
            "ce traité est central pour Susan Sauvé Meyer (ch. 4) qui se "
            "concentre sur EE II 6 (la *bilatéralité* du τὸ ἐφ' ἡμῖν : ce "
            "qui est en notre pouvoir de faire est aussi en notre pouvoir "
            "de ne pas faire), et pour Javier Echeñique (ch. 5) sur EE I "
            "1.1214a14-26 et EE II 6 1223a9-15. L'EE I 1 énumère cinq "
            "causes possibles du bien-vivre : nature, apprentissage, "
            "entraînement, divinité, fortune"
        ),
        description_en=(
            "Eudemian Ethics, Aristotle's eight-book ethical treatise "
            "(three books shared with Nicomachean Ethics: EE IV-V-VI = "
            "EN V-VI-VII), long considered earlier than EN but now "
            "widely held by specialists (Kenny, D. Frede, Sauvé Meyer) "
            "to be roughly contemporary. Central for Sauvé Meyer (ch. 4) "
            "on EE II 6 (the two-sidedness of to eph' hêmin) and "
            "Echeñique (ch. 5) on EE I 1 and EE II 6"
        ),
        period="Classical Greek",
        metadata={
            "cts_urn": "urn:cts:greekLit:tlg0086.tlg010",
            "author": "Aristotle",
            "language": "grc",
            "books_count": 8,
            "books_shared_with_en": "EE IV-V-VI = EN V-VI-VII",
            "approximate_date": "c. 340 BCE",
            "key_passages_destree2014": [
                "EE I 1 1214a14-26 (causes du bien-vivre - Johnson, Echeñique)",
                "EE I 3 1215a12-17 (en tôi auton poion tina einai)",
                "EE II 6 1222b15-1223a20 (humans as origin of actions - Sauvé Meyer, Echeñique)",
                "EE II 8 1224b29-35 (deux sources naturelles : raison + appétit)",
            ],
            "principal_editions": [
                "F. Susemihl, Aristotelis Ethica Eudemia (Teubner, 1884)",
                "R. R. Walzer & J. M. Mingay, Aristotelis Ethica Eudemia (OCT, 1991)",
                "A. Kenny, Aristotle: The Eudemian Ethics (OUP 2011, Eng. tr.)",
            ],
            "destree2014_chapter": "Discussed across ch. 4 (Sauvé Meyer) and ch. 5 (Echeñique)",
            "destree2014_pages": "p. 53-91 + p. 92-114",
        },
        confidence=0.99,
    ),
    _node(
        id="work_porphyry_peri_tou_eph_hemin",
        type="work",
        label="Porphyre, Sur ce qui dépend de nous (Περὶ τοῦ ἐφ' ἡμῖν)",
        description=(
            "Traité (ou commentaire) de Porphyre sur τὸ ἐφ' ἡμῖν, perdu "
            "en tradition directe mais conservé par fragments dans "
            "l'Anthologion de Stobée (II 8 39-42 pp. 163.16-173.2 "
            "Wachsmuth) — frr. 268-271 dans l'édition Smith (1993). "
            "La tradition historiographique a longtemps attribué ces "
            "extraits à un traité indépendant intitulé Περὶ τοῦ ἐφ' "
            "ἡμῖν ; Taormina (Destrée 2014 ch. 14) montre cependant "
            "qu'ils sont plus vraisemblablement extraits d'un commentaire "
            "porphyrien sur République X 617e-620e (le mythe d'Er), "
            "commentaire également attesté par Proclus. Porphyre y "
            "déploie une stratégie sémantique sophistiquée pour "
            "distinguer haïrésis (choix), to autexousion "
            "(auto-détermination) et to eph' hêmin (ce qui est en notre "
            "pouvoir), en restreignant ce dernier à la partie rationnelle "
            "de l'âme humaine"
        ),
        description_en=(
            "Treatise (or commentary) by Porphyry on to eph' hêmin, lost "
            "in direct tradition but preserved fragmentarily in "
            "Stobaeus's Anthologion (II 8 39-42 pp. 163.16-173.2 "
            "Wachsmuth) — frr. 268-271 in Smith's edition (1993). "
            "Historiography long attributed these extracts to an "
            "independent treatise titled Peri tou eph' hêmin; Taormina "
            "(Destrée 2014 ch. 14) shows they are more likely from a "
            "Porphyrian commentary on Republic X 617e-620e, also attested "
            "by Proclus"
        ),
        period="Late Antiquity",
        metadata={
            "author": "Porphyry",
            "language": "grc",
            "preservation": "fragments in Stobaeus Anth. II 8 39-42",
            "fragment_numbers": "Smith frr. 268-271",
            "approximate_date": "c. 270-300 CE",
            "principal_editions": [
                "A. Smith (ed.), Porphyrius. Fragmenta (Teubner 1993) frr. 268-271",
                "C. Wachsmuth (ed.), Ioannis Stobaei Anthologii libri duo priores I-II (Weidmann 1884/1958)",
            ],
            "destree2014_chapter": "Ch. 14 (Taormina) — entire chapter focused on this work",
            "destree2014_pages": "p. 265-282",
            "key_distinction_destree2014": (
                "Porphyry distinguishes hairesis / to autexousion / "
                "to eph' hêmin — restricting the last to the rational "
                "part of the human soul"
            ),
        },
        confidence=0.95,
    ),
    _node(
        id="work_proclus_de_providentia_fato_in_nobis",
        type="work",
        label="Proclus, Sur la Providence, le Destin et ce qui dépend de nous (De Providentia, Fato et eo quod in nobis)",
        description=(
            "Troisième opuscule des Tria Opuscula de Proclus, perdu en "
            "grec mais conservé dans la traduction latine littérale de "
            "Guillaume de Moerbeke (XIIIe s.). Proclus y répond aux "
            "objections de Théodore l'ingénieur (vieil ami de l'École), "
            "qui avait défendu dans une lettre un déterminisme mécaniste "
            "radical (« le monde comme système mécanique gouverné par "
            "une nécessité inaltérable, sans place pour "
            "l'auto-détermination de l'âme humaine »). Proclus défend "
            "une théorie hiérarchique : la Providence régit l'ordre "
            "cosmique, le Destin régit les phénomènes corporels et "
            "extérieurs, mais l'auto-détermination (τὸ αὐτεξούσιον) et "
            "le τὸ ἐφ' ἡμῖν appartiennent à l'âme rationnelle. Pour "
            "Steel (Destrée 2014 ch. 17), Proclus représente une "
            "synthèse mature néoplatonicienne de la question, "
            "particulièrement attentive au lien entre liberté humaine et "
            "providence divine"
        ),
        description_en=(
            "Third of Proclus's Tria Opuscula, lost in Greek but "
            "preserved in William of Moerbeke's literal Latin translation "
            "(13th c.). Proclus answers Theodore the engineer's letter "
            "defending radical mechanistic determinism. Proclus defends "
            "a hierarchical theory: Providence governs cosmic order, "
            "Fate governs corporeal/external phenomena, but "
            "self-determination (to autexousion) and to eph' hêmin "
            "belong to the rational soul"
        ),
        period="Late Antiquity",
        metadata={
            "author": "Proclus",
            "language": "grc (lost) / lat (preserved via Moerbeke)",
            "preservation": "Latin only (Moerbeke), Greek lost",
            "approximate_date": "c. 460-485 CE",
            "tria_opuscula_position": "third (after De decem dubitationibus circa providentiam and De Malorum Subsistentia)",
            "principal_editions": [
                "D. Isaac (ed.), Proclus. Trois études sur la providence III: De la Providence, du destin et de ce qui dépend de nous (Belles Lettres 1982)",
                "C. Steel & B. Strobel (eds.), Greek retroversion in Strobel 2014 (De Gruyter)",
                "B. Steel & B. Strobel, Proklos, Tria opuscula (De Gruyter 2014)",
            ],
            "destree2014_chapter": "Ch. 17 (Steel) — entire chapter focused on this work",
            "destree2014_pages": "p. 311-328",
            "interlocutor": "Theodore the engineer (old school friend of Proclus)",
        },
        confidence=0.95,
    ),
]


# =============================================================================
# CONCEPTS (2)
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    _node(
        id="concept_two_sidedness_eph_hemin",
        type="concept",
        label="Bilatéralité du τὸ ἐφ' ἡμῖν (two-sidedness)",
        description=(
            "Caractéristique centrale du τὸ ἐφ' ἡμῖν chez Aristote selon "
            "Susan Sauvé Meyer (Destrée 2014 ch. 4) : ce qui est en "
            "notre pouvoir de faire est aussi en notre pouvoir de ne pas "
            "faire. Sauvé Meyer souligne que cette bilatéralité ne doit "
            "pas être lue comme une affirmation du Principle of "
            "Alternate Possibilities (PAP) : Aristote ne s'intéresse pas "
            "aux alternatives non-actuelles de nos actions, mais cherche "
            "à montrer que *nos actions elles-mêmes* sont à nous (ἐφ' "
            "ἡμῖν). La bilatéralité est donc une affirmation de notre "
            "contrôle sur nos actions, neutre par rapport au "
            "déterminisme. Bobzien (Destrée 2014 ch. 3) défend une thèse "
            "convergente sur EN III 1113b7-8 (« là où nous sommes libres "
            "de dire oui, nous sommes aussi libres de dire non »)"
        ),
        description_en=(
            "Central feature of Aristotelian to eph' hêmin per Sauvé "
            "Meyer (Destrée 2014 ch. 4): what is up to us to do is also "
            "up to us not to do. Sauvé Meyer stresses this two-sidedness "
            "should not be read as PAP — Aristotle is concerned that our "
            "actions themselves are ours, not their non-actual "
            "alternatives. The two-sidedness affirms control over our "
            "actions and is neutral wrt determinism. Bobzien (ch. 3) "
            "defends a convergent thesis on EN III 1113b7-8"
        ),
        period="Classical Greek",
        metadata={
            "greek_term": "τὸ ἐφ' ἡμῖν δίθυρον / ἀμφίδρομον",
            "introduced_by": "Aristotle (anti-indeterministic reading per Sauvé Meyer & Bobzien)",
            "key_passages": [
                "Aristotle, EN III 1113b7-8",
                "Aristotle, EE II 6 1223a9-15",
            ],
            "destree2014_chapters": ["ch. 3 (Bobzien)", "ch. 4 (Sauvé Meyer)"],
            "destree2014_pages": "p. 41-91",
            "modern_scholarship_caveat": (
                "Modern scholars often misread two-sidedness as PAP — "
                "but Sauvé Meyer/Bobzien argue this is anachronistic. "
                "The 'principle of alternate possibilities' (PAP) is a "
                "20th-c. analytic notion (Frankfurt 1969)"
            ),
        },
        confidence=0.95,
    ),
    _node(
        id="concept_causal_conception_eph_hemin_salles",
        type="concept",
        label="Conception causale de τὸ ἐφ' ἡμῖν (Salles)",
        description=(
            "Lecture du τὸ ἐφ' ἡμῖν stoïcien défendue par Ricardo Salles "
            "(Destrée 2014 ch. 8) : une action est ἐφ' ἡμῖν si nous en "
            "sommes la cause (αἴτιον), sans présupposer la disponibilité "
            "d'alternatives. Cette conception est donc *congeniale* au "
            "déterminisme et au compatibilisme. Salles soutient que la "
            "conception causale, généralement reconnue chez Chrysippe, "
            "se trouve aussi chez Épictète (notamment Diss. I.11) — "
            "contrairement à une interprétation influente qui voit chez "
            "Épictète une rupture avec Chrysippe par introduction d'une "
            "exigence d'alternatives. Le rapprochement Épictète-Chrysippe "
            "se voit dans l'argument du cylindre (De Fato 40-44)"
        ),
        description_en=(
            "Reading of Stoic to eph' hêmin defended by Salles (Destrée "
            "2014 ch. 8): an action is in my power if I am its cause "
            "(aition), without presupposing alternative possibilities. "
            "Hence congenial to determinism and compatibilism. Salles "
            "argues this causal conception, generally recognized in "
            "Chrysippus, is also found in Epictetus (esp. Diss. I.11) — "
            "contra an influential reading that sees Epictetus departing "
            "from Chrysippus by introducing an alternatives requirement"
        ),
        period="Roman Imperial",
        metadata={
            "greek_term": "τὸ ἐφ' ἡμῖν αἰτιακῶς",
            "introduced_by": "Salles 2005 / Salles 2014 ch. 8 (formalization)",
            "key_passages": [
                "Epictetus, Discourses I.11 (philostorgia dialogue)",
                "Cicero, De Fato 40-44 (Chrysippean cylinder)",
            ],
            "destree2014_chapter": "ch. 8 (Salles)",
            "destree2014_pages": "p. 169-183",
            "alternative_terms": ["one-sided causative conception", "causal account of moral responsibility"],
            "modern_scholarship_context": (
                "Salles's reading aligns with Bobzien 1998 against the "
                "two-sided potestative reading attributed to Alexander "
                "of Aphrodisias and modern indeterminists"
            ),
        },
        confidence=0.95,
    ),
]


# =============================================================================
# SYNTHESES (20) — one per chapter
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    _node(
        id="synthesis_destree2014_introduction_overview",
        type="synthesis",
        label="Destrée/Salles/Zingano — Introduction au volume (synthèse)",
        description=(
            "Synthèse de l'introduction au volume (Destrée, Salles, "
            "Zingano, p. 1-6) : les vingt contributions ont pour but "
            "d'étudier la responsabilité morale dans l'Antiquité en "
            "lien avec τὸ ἐφ' ἡμῖν / in nostra potestate / in nobis. "
            "L'introduction défend trois thèses méthodologiques : (1) "
            "τὸ ἐφ' ἡμῖν commence sa vie philosophique chez Aristote, "
            "mais des éléments sont déjà présents chez Démocrite et "
            "Platon ; (2) tous les chapitres aristotéliciens du volume "
            "défendent une lecture déterministe ou anti-indéterministe "
            "(suivant Loening 1903 contre la lecture indéterministe "
            "traditionnelle) ; (3) la post-aristotélicienne se "
            "structure autour du dialogue Stoïciens/Aristotéliciens, "
            "avec des inflexions néoplatoniciennes (Plotin, Porphyre, "
            "Proclus, Simplicius) et chrétiennes (Augustin) en fin de "
            "course"
        ),
        description_en=(
            "Synthesis of the volume's introduction (p. 1-6). Three "
            "methodological theses: (1) to eph' hêmin starts its "
            "philosophical life with Aristotle but with antecedents in "
            "Democritus and Plato; (2) all Aristotle chapters uphold a "
            "deterministic or anti-indeterministic reading (Loening "
            "1903 line, contra traditional indeterminist reading); (3) "
            "post-Aristotelian discussion structured around "
            "Stoic/Aristotelian dialogue with Neoplatonic and Christian "
            "inflections"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Introduction",
            pages="p. 1-6",
            author="Destrée, Salles, Zingano (eds.)",
            md_line_range="ll. 11-290",
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch01_johnson_democritus",
        type="synthesis",
        label="Johnson — Changing our minds: Democritus on what is up to us",
        description=(
            "Synthèse du ch. 1 (Johnson, p. 7-30) : interprétation "
            "positive et intellectualiste de l'éthique démocritéenne, "
            "fondée non sur le problème (anachronique) du libre arbitre "
            "vs déterminisme, mais sur le problème démocritéen "
            "authentique des *causes du bien-être humain*. Johnson "
            "défend que pour Démocrite : (a) la chance et les dieux ne "
            "sont pas des causes décisives ; (b) la nature humaine est "
            "*docile* (plastique), reformable par l'enseignement "
            "(didachê), la pensée (gnômê), l'intelligence (nous, "
            "phronêsis). L'éthique démocritéenne envisage une "
            "*thérapie cognitivo-comportementale* avant la lettre, "
            "fondée sur la plasticité des atomes psychiques. Johnson "
            "s'inspire de Vlastos 1945-46, Kahn 1985, Annas 2002 contre "
            "les interprétations « naïves » de Bailey 1928 et Barnes "
            "1979"
        ),
        description_en=(
            "Synthesis of ch. 1 (Johnson, p. 7-30): positive "
            "intellectualist reading of Democritean ethics, grounded not "
            "on the anachronistic free-will/determinism problem but on "
            "the authentically Democritean question of the causes of "
            "human flourishing. Johnson argues: (a) luck and gods are "
            "not decisive causes; (b) human nature is docile (plastic), "
            "reformable by teaching, thought, intelligence. Democritean "
            "ethics envisions a proto-cognitive-behavioral therapy "
            "grounded on psychic-atom plasticity"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 1 — Changing our minds: Democritus on what is up to us",
            pages="p. 7-30",
            author="Monte Ransome Johnson",
            md_line_range="ll. 291-1130",
            extra={
                "key_fragments_discussed": ["DK 68B33", "B35", "B173", "B191", "B197", "B242"],
                "key_concepts": ["gnômê", "didachê", "phusiopoiei", "euthumia"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch02_destree_plato_er",
        type="synthesis",
        label="Destrée — How can our fate be up to us? Plato and the myth of Er",
        description=(
            "Synthèse du ch. 2 (Destrée, p. 31-52) : Platon dans le "
            "mythe d'Er (Rép. X 614b-621d) pose les éléments qui "
            "deviendront le τὸ ἐφ' ἡμῖν aristotélicien dans le contexte "
            "de la responsabilité. Destrée défend que Platon développe "
            "une thèse asymétrique (Sauvé Meyer 2011) : on est "
            "responsable de ses choix vertueux par soi-même, mais les "
            "choix vicieux sont l'effet d'une ignorance (Tim. 86b). La "
            "formule platonicienne aitia hélomenou, theos anaitios "
            "(Rép. 617e — « le responsable est celui qui choisit, le "
            "dieu n'est pas coupable ») devient le verset-clé de toute "
            "l'apologétique antifataliste ultérieure, des néoplatoniciens "
            "à Justin Martyr"
        ),
        description_en=(
            "Synthesis of ch. 2 (Destrée, p. 31-52): Plato in the Myth "
            "of Er (Rep. X 614b-621d) lays elements that become the "
            "Aristotelian to eph' hêmin in responsibility contexts. "
            "Destrée defends an asymmetry thesis (Sauvé Meyer 2011): "
            "one is responsible by oneself for virtuous choices, but "
            "vicious choices are effects of ignorance (Tim. 86b). The "
            "Platonic formula aitia helomenou, theos anaitios (Rep. "
            "617e) becomes the key verse of all later antifatalist "
            "apologetics, from Neoplatonists to Justin Martyr"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 2 — How can our fate be up to us? Plato and the myth of Er",
            pages="p. 31-52",
            author="Pierre Destrée",
            md_line_range="ll. 1135-1780",
            extra={
                "key_passages": ["Plato Rep. X 617e", "Tim. 86b", "Laws X"],
                "linked_publication": "pub_destree_2014_plato_er (already in KG)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch03_frede_d_aristotle_free_will",
        type="synthesis",
        label="Frede D. — Free will in Aristotle?",
        description=(
            "Synthèse du ch. 3 (D. Frede, p. 53-75) : il n'y a aucune "
            "notion explicite de volonté chez Aristote, donc a fortiori "
            "aucune conception de libre arbitre. Mais la théorie "
            "aristotélicienne de la délibération et du choix face à des "
            "actions particulières fait néanmoins surgir le problème : "
            "pouvons-nous agir autrement ? D. Frede défend une lecture "
            "psychologiquement déterministe : les individus doivent "
            "avoir la disposition à choisir les moyens corrects pour "
            "atteindre leurs fins jugées bonnes ; la liberté comme "
            "indifférence morale aurait été inconcevable pour Aristote. "
            "Les notions de souhait, désir et choix dessinent néanmoins, "
            "dans leurs interrelations complexes, une notion non-vague "
            "d'agir-par-soi-même sous contraintes (caractère, "
            "disposition)"
        ),
        description_en=(
            "Synthesis of ch. 3 (D. Frede, p. 53-75): no explicit notion "
            "of will in Aristotle, a fortiori no free will. But "
            "Aristotle's theory of deliberation and choice raises the "
            "problem: can we act otherwise? D. Frede defends a "
            "psychologically deterministic reading: individuals must have "
            "the disposition to choose right means to ends judged good; "
            "moral indifference would be inconceivable for Aristotle. "
            "Wish, desire, choice in complex interrelations sketch a "
            "non-vague notion of acting-by-oneself under constraints"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 3 — Free will in Aristotle?",
            pages="p. 53-75",
            author="Dorothea Frede",
            md_line_range="ll. 1781-2660",
            extra={
                "key_passages": ["EN III 1-5", "EN VI on phronêsis", "EN VII on akrasia"],
                "thesis": "anti-indeterministic, psychological-deterministic reading of Aristotelian agency",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch04_bobzien_aristotle_free_choice",
        type="synthesis",
        label="Bobzien — Aristotle on free choice (EN III 1113b7-8)",
        description=(
            "Synthèse du ch. 4 (Bobzien, p. 77-91) : Bobzien attaque le "
            "problème du libre choix en EN III 1113b7-8 (« là où il est "
            "en notre pouvoir d'agir, il est aussi en notre pouvoir de "
            "nous abstenir »), passage souvent invoqué comme appui "
            "indiscutable d'une lecture indéterministe d'Aristote. "
            "Bobzien argumente *contra* : il y a au contraire de bonnes "
            "raisons de lire ce passage dans la direction opposée — "
            "comme expression de la bilatéralité contrôlée par l'agent, "
            "non d'une indétermination causale. Cette interprétation "
            "complète et prolonge Bobzien 1998 (Determinism and Freedom "
            "in Stoic Philosophy) et Bobzien 2013-2014 sur EN III. "
            "Convergence forte avec Sauvé Meyer (ch. 5)"
        ),
        description_en=(
            "Synthesis of ch. 4 (Bobzien, p. 77-91): Bobzien tackles "
            "free choice at EN III 1113b7-8 ('where we are free to act, "
            "we are also free to refrain'), often invoked as decisive "
            "support for indeterministic Aristotle. Bobzien argues "
            "contra: there is good reason to read it the opposite way "
            "— as an expression of agent-controlled two-sidedness, not "
            "causal indeterminacy. Extends Bobzien 1998 and 2013-14 on "
            "EN III. Strong convergence with Sauvé Meyer (ch. 5)"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 4 — Choice and moral responsibility in Nicomachean Ethics III 1-5 (final title in volume)",
            pages="p. 77-91",
            author="Susanne Bobzien",
            md_line_range="ll. 2661-3370",
            extra={
                "key_passage": "EN III 1113b7-8",
                "scholarly_extends": "Bobzien 1998 Determinism and Freedom in Stoic Philosophy",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch05_sauve_meyer_aristotle_eph_hemin_contingent",
        type="synthesis",
        label="Sauvé Meyer — Aristotle on what is up to us and what is contingent",
        description=(
            "Synthèse du ch. 5 (Sauvé Meyer, p. 93-114) : Sauvé Meyer "
            "se concentre sur EE II 6 et insiste sur la *bilatéralité* "
            "du τὸ ἐφ' ἡμῖν : ce qui est en notre pouvoir de faire est "
            "aussi en notre pouvoir de ne pas faire. Le problème surgit "
            "quand on lit cette bilatéralité comme une invocation du "
            "Principe des Possibilités Alternatives (PAP). Or, le PAP "
            "souligne la *possibilité d'alternatives non-actuelles* de "
            "nos actions, tandis qu'Aristote cherche à montrer que *nos "
            "actions, et non leurs alternatives*, sont à nous. "
            "Présenter le τὸ ἐφ' ἡμῖν comme affirmation de la "
            "contingence des actions humaines peut donc être trompeur. "
            "L'affirmation 'cette action est ἐφ' ἡμῖν' établit *le "
            "contrôle agentif*, qui n'implique ni n'exclut le "
            "déterminisme"
        ),
        description_en=(
            "Synthesis of ch. 5 (Sauvé Meyer, p. 93-114): focused on "
            "EE II 6. Sauvé Meyer stresses the two-sidedness of to eph' "
            "hêmin (what is up to us to do is also up to us not to do). "
            "The problem arises when this is read as PAP. PAP emphasizes "
            "non-actual alternatives; Aristotle is concerned that our "
            "actions, not their alternatives, are ours. Saying 'X is "
            "eph' hêmin' establishes agent control, neutral wrt "
            "determinism"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 5 — Aristotle on what is up to us and what is contingent",
            pages="p. 93-114",
            author="Susan Sauvé Meyer",
            md_line_range="ll. 3371-4060",
            extra={
                "key_passages": ["EE II 6 1222b15-1223a20", "EN III"],
                "thesis": "two-sidedness ≠ PAP; agent-control affirmation neutral wrt determinism",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch06_echenique_aristotle_double_position",
        type="synthesis",
        label="Echeñique — Aristotle as compatibilist and incompatibilist",
        description=(
            "Synthèse du ch. 6 (Echeñique, p. 115-135) : thèse "
            "iconoclaste de la double position aristotélicienne. "
            "Aristote est *compatibiliste* en matière d'« évaluations "
            "éthiques » (appraisals : louange/blâme), qui sont la "
            "préoccupation centrale de son Éthique. Mais il est aussi "
            "*incompatibiliste* en matière d'imputabilité "
            "(*accountability* : le mérite des récompenses et "
            "châtiments). Echeñique défend que cette double position "
            "est cohérente et soutenue par la majorité des passages-clés "
            "sur τὸ ἐφ' ἡμῖν. EN III 5 (sur l'imputabilité du "
            "caractère) fournit l'évidence d'une position "
            "proto-incompatibiliste"
        ),
        description_en=(
            "Synthesis of ch. 6 (Echeñique, p. 115-135): iconoclastic "
            "thesis of Aristotle's double position. Aristotle is "
            "compatibilist regarding ethical appraisals (praise/blame) "
            "but incompatibilist regarding accountability (desert of "
            "rewards/punishments). Echeñique argues this double "
            "position is coherent and supported by most key eph' hêmin "
            "passages. EN III 5 provides evidence for the "
            "proto-incompatibilist position"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 6 — Aristotle on accountability and the principle of alternate possibilities",
            pages="p. 115-135",
            author="Javier Echeñique",
            md_line_range="ll. 4061-4820",
            extra={
                "key_passages": ["EN III 5", "EE II 6 1223a9-15"],
                "thesis": "double position — compatibilist on appraisals, incompatibilist on accountability",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch07_vogt_stoic_action",
        type="synthesis",
        label="Vogt — I shall do what I did: Stoic views on action",
        description=(
            "Synthèse du ch. 7 (Vogt, p. 137-158) : Vogt présente le cas "
            "type de l'agent stoïcien (la « Porteuse de Parapluie "
            "Prudente ») qui se meut à l'action en assentant à une "
            "représentation. Pour tout agent à tout moment, il n'y a "
            "qu'un seul assentiment qu'elle peut et donnera, donc une "
            "seule action. De plus, l'assentiment qu'elle donne est *le "
            "même* que celui qu'elle a donné dans les cycles cosmiques "
            "antérieurs (ekpurôsis stoïcienne). L'agent fera donc ce "
            "qu'elle fera et fera ce qu'elle a fait. Qu'est-ce que cela "
            "signifie que l'assentiment soit ἐφ' ἡμῖν ? Deux choses : "
            "(1) on assente comme le cognisant que l'on est ; (2) "
            "l'agent est capable d'adhérer aux normes d'assentiment. La "
            "difficulté centrale de la théorie stoïcienne est ce second "
            "point. Pour le sage, n'avoir qu'une seule option est "
            "parfaitement satisfaisant : elle fera ce qui est le mieux"
        ),
        description_en=(
            "Synthesis of ch. 7 (Vogt, p. 137-158): the Stoic agent "
            "moves herself to action by assent to an impression. For any "
            "agent at any time, there is just one assent she can and "
            "will give, hence one action. Moreover, this assent is the "
            "same one she gave in earlier world-cycles (Stoic "
            "conflagration). The agent will do what she will do and "
            "what she did. Two things make assent eph' hêmin: (1) one "
            "assents as the cognizer one is; (2) the agent can adhere "
            "to norms of assent — the central Stoic difficulty"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 7 — I shall do what I did: Stoic views on action",
            pages="p. 137-158",
            author="Katja Maria Vogt",
            md_line_range="ll. 4821-5510",
            extra={
                "key_example": "Cautious Umbrella Carrier",
                "thesis": "Stoic up-to-us via cyclic assent, not freedom/alternatives",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch08_gomez_chrysippus_compatibilism",
        type="synthesis",
        label="Gómez — Chrysippean compatibilistic theory of fate, what is up to us and moral responsibility",
        description=(
            "Synthèse du ch. 8 (Gómez, p. 159-167) : Gómez analyse "
            "Chrysippe à travers ses *réactions* aux objections "
            "spécifiques adressées au stoïcisme. La théorie chrysippéenne "
            "du destin combinée avec le τὸ ἐφ' ἡμῖν est reconstruite "
            "comme stratégie de défense : (a) distinction entre causes "
            "principales et auxiliaires ; (b) argument du cylindre — la "
            "première impulsion (prôtê hormê) vient de l'extérieur, mais "
            "le mouvement reste régi par la nature propre du cylindre ; "
            "(c) responsabilité morale comme appartenance des "
            "co-fatalia. Gómez s'aligne sur Bobzien 1998 contre les "
            "interprétations indéterministes"
        ),
        description_en=(
            "Synthesis of ch. 8 (Gómez, p. 159-167): Chrysippus analyzed "
            "via his responses to objections specifically directed at "
            "Stoicism. Chrysippean theory of fate + to eph' hêmin "
            "reconstructed as defense strategy: (a) principal vs "
            "auxiliary causes; (b) cylinder argument (first impulse "
            "external, motion governed by cylinder's own nature); (c) "
            "moral responsibility via co-fatalia. Aligned with Bobzien "
            "1998 against indeterminist readings"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 8 — Chrysippean compatibilistic theory of fate, what is up to us, and moral responsibility",
            pages="p. 159-167",
            author="Laura Liliana Gómez",
            md_line_range="ll. 5511-6390",
            extra={
                "key_arguments_discussed": ["cylinder argument", "co-fatalia", "principal vs auxiliary causes"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_destree2014_ch09_gourinat_in_nostra_potestate",
        type="synthesis",
        label="Gourinat — Adsensio in nostra potestate: 'from us' and 'to us' in ancient Stoicism",
        description=(
            "Synthèse du ch. 9 (Gourinat, p. 169-181) : Gourinat focalise "
            "sur le terme latin in nostra potestate dans les sources "
            "ciceroniennes pour Chrysippe. Thèse iconoclaste : in "
            "nostra potestate ne traduit *pas nécessairement* le grec "
            "ἐφ' ἡμῖν. Donc les passages cicéroniens (notamment De Fato "
            "où l'expression est très fréquente) ne sont pas des preuves "
            "irréfutables que Chrysippe ait jamais utilisé en grec "
            "l'expression ἐφ' ἡμῖν. Chrysippe pourrait avoir préféré les "
            "expressions par' hêmas (« par nous ») ou ex hêmôn (« à "
            "partir de nous »), qui sont *à une voix* (causales), non "
            "*à deux voix* (potestatives). Gourinat conteste donc la "
            "thèse Bobzien 1998 (qui attribue à Chrysippe la diffusion "
            "du τὸ ἐφ' ἡμῖν stoïcien)"
        ),
        description_en=(
            "Synthesis of ch. 9 (Gourinat, p. 169-181): Gourinat focuses "
            "on Latin in nostra potestate in Ciceronian sources for "
            "Chrysippus. Iconoclastic thesis: in nostra potestate is "
            "not necessarily a translation of Greek eph' hêmin. Hence "
            "Ciceronian passages do not decisively prove Chrysippus "
            "ever used eph' hêmin in Greek. Chrysippus might have "
            "preferred par' hêmas (from us) or ex hêmôn (out of us) — "
            "one-sided causal expressions, not two-sided potestative. "
            "Gourinat thus challenges Bobzien 1998"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 9 — Adsensio in nostra potestate: 'from us' and 'to us' in ancient Stoicism",
            pages="p. 169-181",
            author="Jean-Baptiste Gourinat",
            md_line_range="ll. 6391-6840",
            extra={
                "key_terms": ["in nostra potestate", "ἐφ' ἡμῖν", "παρ' ἡμᾶς", "ἐξ ἡμῶν"],
                "iconoclastic_thesis": "Cicero's in nostra potestate ≠ direct translation of eph' hêmin",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch10_vimercati_panaetius",
        type="synthesis",
        label="Vimercati — Panaetius on self-knowledge and moral responsibility",
        description=(
            "Synthèse du ch. 10 (Vimercati, p. 183-198) : Vimercati "
            "déploie une méthode indirecte (*makrotéra periodos*) car la "
            "formule τὸ ἐφ' ἡμῖν n'apparaît qu'une seule fois dans les "
            "fragments de Panétius (Némésius Nat. hom. 26 = Panaet. fr. "
            "B26 Vim.). Trois éléments structurants : (1) Panétius "
            "rejette la conflagration cyclique stoïcienne (ekpurôsis), "
            "réduisant ainsi l'influence du logos universel et "
            "élargissant la responsabilité humaine ; (2) son "
            "interprétation de l'oikéiôsis dans la lignée "
            "socratico-platonicienne fonde la connaissance de soi comme "
            "axe de la théorie de l'action ; (3) sa théorie des quatre "
            "personae (Cic. Off. I), particulièrement les troisième "
            "(casus aut tempus) et quatrième (iudicium / voluntas), "
            "laisse place au ἐφ' ἡμῖν. Le fragment B26 confirme la "
            "liaison oikéiôsis–prohaïrèsis–responsabilité"
        ),
        description_en=(
            "Synthesis of ch. 10 (Vimercati, p. 183-198): Vimercati uses "
            "an indirect method (makrotera periodos) since to eph' "
            "hêmin appears only once in Panaetius's fragments (Nemesius "
            "Nat. hom. 26 = Panaet. fr. B26 Vim.). Three structuring "
            "elements: (1) Panaetius's rejection of Stoic conflagration "
            "expanding human responsibility; (2) his "
            "Socratic-Platonic-influenced oikeiôsis grounding "
            "self-knowledge; (3) his four-personae theory (Cic. Off. I) "
            "leaving room for eph' hêmin in third (casus aut tempus) "
            "and fourth (iudicium/voluntas) personae"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 10 — Panaetius on self-knowledge and moral responsibility",
            pages="p. 183-198",
            author="Emmanuele Vimercati",
            md_line_range="ll. 6841-7680",
            extra={
                "key_fragment": "Panaet. fr. B26 Vim. / T126 Alesse / fr. 86a van Straaten = Nemesius Nat. hom. 26",
                "linked_theory": "four personae (Cicero De officiis I)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch11_salles_epictetus_causal",
        type="synthesis",
        label="Salles — Epictetus and the causal conception of moral responsibility and what is eph' hêmin",
        description=(
            "Synthèse du ch. 11 (Salles, p. 199-217) : Salles défend "
            "que la théorie épictétéenne de la responsabilité morale et "
            "du τὸ ἐφ' ἡμῖν est *essentiellement causale* : les choses "
            "dont nous sommes moralement responsables et qui sont en "
            "notre pouvoir sont celles dont nous sommes la cause "
            "(aition). Forte proximité entre Épictète et Chrysippe (le "
            "premier stoïcien majeur à articuler une théorie causale). "
            "Salles centre son argument sur la onzième Diatribe du "
            "premier livre (Diss. I.11, sur la philostorgia — dialogue "
            "entre Épictète et un homme qui a abandonné sa fille "
            "malade). Salles répond à deux objections philosophiques "
            "contre les conceptions causales du ἐφ' ἡμῖν, en s'appuyant "
            "sur l'argument chrysippéen du cylindre (De Fato 40-44). "
            "Contre Long 2002, Brennan 2000 qui voient chez Épictète "
            "une innovation par rapport à Chrysippe"
        ),
        description_en=(
            "Synthesis of ch. 11 (Salles, p. 199-217): Salles argues "
            "Epictetus's theory of moral responsibility and to eph' "
            "hêmin is essentially causal — actions for which we are "
            "responsible are those of which we are the cause (aition). "
            "Strong proximity Epictetus–Chrysippus. Argument centered "
            "on Diss. I.11 (philostorgia dialogue with father who "
            "abandoned sick daughter). Salles answers two objections to "
            "causal conceptions using Chrysippus's cylinder (De Fato "
            "40-44). Against Long 2002, Brennan 2000 who see Epictetan "
            "innovation"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 11 — Epictetus and the causal conception of moral responsibility and what is eph' hêmin",
            pages="p. 199-217",
            author="Ricardo Salles",
            md_line_range="ll. 7681-8330",
            extra={
                "key_passage": "Epictetus Diss. I.11 (philostorgia)",
                "parallel_argument": "Chrysippus cylinder (Cicero De Fato 40-44)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch12_boeri_marcus_aurelius",
        type="synthesis",
        label="Boeri — Present time and indifferents: making room for what depends on us in Marcus Aurelius",
        description=(
            "Synthèse du ch. 12 (Boeri, p. 219-243) : Boeri demande "
            "quelle est la fonction et la valeur de la notion de τὸ ἐφ' "
            "ἡμῖν chez Marc Aurèle. Thèse : la liaison entre le présent "
            "et les indifférents est cruciale pour la compréhension du "
            "dépendant-de-nous chez Marc. La valeur de la croyance et "
            "le pouvoir de décider de quoi croire sont au centre. Boeri "
            "soutient que Marc endosse l'idée que notre esprit est ce "
            "qui confère « réalité » à quelque chose d'extérieur, "
            "donnant ainsi à l'esprit individuel — en tant qu'il dépend "
            "de soi — la capacité de donner valeur ou non-valeur aux "
            "objets extérieurs pour la vie pratique. L'usage marcusien "
            "de l'impératif est interprété comme positionnement "
            "thétique d'arguments théoriques"
        ),
        description_en=(
            "Synthesis of ch. 12 (Boeri, p. 219-243): Boeri asks the "
            "function and value of to eph' hêmin in Marcus Aurelius. "
            "Thesis: the connection between the present and "
            "indifferents is crucial. The mind bestows 'reality' on "
            "external things; the individual's mind, depending on "
            "itself, gives value or disvalue to externals for practical "
            "life. Marcus's imperatives are theoretical-thesis "
            "positioning"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 12 — Present time and indifferents: making room for 'what depends on us' in Marcus Aurelius",
            pages="p. 219-243",
            author="Marcelo D. Boeri",
            md_line_range="ll. 8331-9040",
            extra={
                "key_passages": ["Marcus Med. 2.17", "Med. 6.32", "Med. 4.3 (inner citadel)"],
                "thesis": "the present + indifferents = key to to eph' hêmin in Marcus",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch13_zingano_alexander_character_action",
        type="synthesis",
        label="Zingano — Alexander and Aristotle on character and action",
        description=(
            "Synthèse du ch. 13 (Zingano, p. 245-263) : Zingano se "
            "concentre sur les §§ 26-29 du De Fato d'Alexandre. "
            "Alexandre examine des arguments soutenant la position "
            "déterministe puis y répond. Thèse principale de Zingano : "
            "le libertarianisme d'Alexandre est compatible avec un "
            "déterminisme psychologique rigide fondé sur le caractère. "
            "Distinction clé : (1) la *liability* à agir autrement (au "
            "sens fort : faire x ou non-x dans les circonstances mêmes "
            "où x et non-x sont contraires comme le bon et le mauvais) ; "
            "(2) la *possibilité* d'agir différemment (au sens faible : "
            "agir-autrement-mais-équivalent, sans contrariété). Le sage "
            "ne peut faire que des « contraires » au sens faible (il ne "
            "peut être méchant). Le caractère détermine l'action, mais "
            "le caractère lui-même est acquis par des actions où "
            "l'agent aurait pu faire autrement au sens fort"
        ),
        description_en=(
            "Synthesis of ch. 13 (Zingano, p. 245-263): focused on "
            "Alexander's De Fato §§ 26-29. Zingano's main thesis: "
            "Alexander's libertarianism is compatible with rigid "
            "character-based psychological determinism. Key distinction: "
            "liability to act otherwise (strong sense: x or not-x in "
            "the very circumstances, where x and not-x are contraries) "
            "vs possibility of acting differently (weak sense: slightly "
            "different equivalents). The sage can only do 'opposites' "
            "in the weak sense"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 13 — Alexander and Aristotle on character and action",
            pages="p. 245-263",
            author="Marco Zingano",
            md_line_range="ll. 9041-10050",
            extra={
                "key_passage": "Alexander De Fato §§ 26-29",
                "thesis": "Alexander's libertarianism + rigid character-based determinism",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch14_morel_epicurus_primary_evidence",
        type="synthesis",
        label="Morel — The Epicurean 'up to us': not to be proved",
        description=(
            "Synthèse du ch. 14 (Morel, p. 265-282) : Morel argue qu'il "
            "n'existe pas (et qu'il *ne peut exister*) une démonstration "
            "épicurienne explicite du τὸ ἐφ' ἡμῖν. Aucun texte conservé "
            "n'en présente une, et c'est *normal* : pour l'épicurien, "
            "l'existence du dépendant-de-nous n'a pas besoin de "
            "démonstration — c'est une *évidence primaire*. Trois types "
            "d'arguments soutiennent cette thèse : (1) *cosmologiques* "
            "— Lettre à Ménécée, sur les conditions cosmologiques de "
            "l'action ; le sage ne dépend pas absolument d'une chaîne "
            "causale ; (2) *éthiques* — Sur la Nature livre XXV, sur "
            "les conséquences éthiques absurdes de la négation de la "
            "liberté humaine ; (3) *épistémologiques* — l'absurdité "
            "logique d'une telle négation. Position alignée avec le "
            "schéma épicurien général de la primauté des prolepses "
            "cognitives"
        ),
        description_en=(
            "Synthesis of ch. 14 (Morel, p. 265-282): Morel argues there "
            "is and can be no explicit Epicurean demonstration of to "
            "eph' hêmin. None of the preserved texts contains one — and "
            "this is normal: for the Epicurean, the existence of the "
            "up-to-us needs no demonstration, it is primary evidence. "
            "Three argument types: cosmological (Letter to Menoeceus), "
            "ethical (Peri Phuseos book XXV), epistemological (logical "
            "absurdity of denial). Aligned with general Epicurean primacy "
            "of cognitive prolepseis"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 14 — The Epicurean 'up to us': not to be proved",
            pages="p. 265-282",
            author="Pierre-Marie Morel",
            md_line_range="ll. 10051-10670",
            extra={
                "key_works_discussed": ["Letter to Menoeceus", "Peri Phuseos book XXV", "Letter to Herodotus 63-65"],
                "thesis": "Epicurean eph' hêmin = primary evidence, not demonstrandum",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius",
        type="synthesis",
        label="Maso — Motus animi voluntarius: Cicero on Epicurean freedom",
        description=(
            "Synthèse du ch. 15 (Maso, p. 283-300) : Maso étudie "
            "l'expression cicéronienne *motus animi voluntarius* (« "
            "mouvement volontaire de l'âme »), employée 14 fois dans "
            "le De Fato et seulement une fois ailleurs (Tusculanes "
            "4.79). Maso passe en revue les distinctions philologiques "
            "entre ἐφ' ἡμῖν (Stoïciens), par' hêmas (Épicuriens) et in "
            "nostra potestate (Cicéron). Position alignée avec Gourinat "
            "(ch. 9) sur l'autonomie sémantique de l'expression "
            "latine. Maso suggère que Cicéron utilise l'épicurisme "
            "comme miroir pour développer sa propre position sur le "
            "« libre arbitre » et le « libre choix », via une réception "
            "originale du *clinamen* lucrétien"
        ),
        description_en=(
            "Synthesis of ch. 15 (Maso, p. 283-300): Maso studies the "
            "Ciceronian expression motus animi voluntarius (used 14 "
            "times in De Fato, once elsewhere in Tusc. 4.79). Reviews "
            "philological distinctions between eph' hêmin (Stoics), "
            "par' hêmas (Epicureans), in nostra potestate (Cicero). "
            "Aligned with Gourinat (ch. 9) on the semantic autonomy of "
            "the Latin expression. Cicero uses Epicureanism as mirror "
            "to develop his own free-will/free-choice position via "
            "original reception of Lucretian clinamen"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 15 — Motus animi voluntarius (Cicero on Epicurean freedom)",
            pages="p. 283-300",
            author="Stefano Maso",
            md_line_range="ll. 10671-11380",
            extra={
                "key_passages": ["Cicero De Fato 9, 25, 31, 40, 41, 45", "Tusc. 4.79"],
                "linked_terms": ["motus animi voluntarius", "iunctura", "in nostra potestate"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch16_gerson_plotinus_strawson",
        type="synthesis",
        label="Gerson — Moral responsibility and what is up to us in Plotinus",
        description=(
            "Synthèse du ch. 16 (Gerson, p. 301-322) : Gerson aborde "
            "Plotin via une discussion de l'« argument de base » récent "
            "de Galen Strawson contre la possibilité de la "
            "responsabilité morale (Strawson : nul ne peut être causa "
            "sui, donc nul ne peut être véritablement moralement "
            "responsable). Bien que Plotin n'ait pas le concept précis "
            "de *responsabilité morale*, il déploie une famille de "
            "termes apparentés. Aucun ne correspond exactement à "
            "Strawson. Gerson examine ces notions pour construire une "
            "réponse plotinienne à Strawson. Conclusion : Plotin "
            "accepte qu'une grande partie de ce qui est ordinairement "
            "tenu pour ἐφ' ἡμῖν ne l'est pas sans qualification, mais "
            "refuse l'option binaire de Strawson. La *responsabilité "
            "morale qualifiée* suffit, tant que le paradigme de la "
            "responsabilité morale non-qualifiée — la volonté "
            "complètement libre — demeure intact. Texte central : Enn. "
            "VI 8 [39] sur l'Un comme cause-de-soi"
        ),
        description_en=(
            "Synthesis of ch. 16 (Gerson, p. 301-322): Gerson approaches "
            "Plotinus via Galen Strawson's recent 'basic argument' "
            "against moral responsibility (no causa sui, hence no true "
            "moral responsibility). Plotinus lacks the precise concept "
            "of moral responsibility but deploys related notions. "
            "Gerson constructs a Plotinian answer: Plotinus accepts "
            "much of what is ordinarily taken as eph' hêmin is not so "
            "unqualifiedly, but rejects Strawson's binary. Qualified "
            "moral responsibility suffices as long as the paradigm of "
            "unqualified moral responsibility (the completely "
            "unfettered will of the One) remains intact. Central text: "
            "Enn. VI 8 [39]"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 16 — Moral responsibility and what is 'up to us' in Plotinus",
            pages="p. 301-322",
            author="Lloyd P. Gerson",
            md_line_range="ll. 11381-11960",
            extra={
                "key_text": "Plotinus Enn. VI 8 [39]",
                "modern_interlocutor": "Galen Strawson — Basic Argument",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch17_taormina_porphyry_myth_er",
        type="synthesis",
        label="Taormina — Choice, autexousion and eph' hêmin in Porphyry's interpretation of the Myth of Er",
        description=(
            "Synthèse du ch. 17 (Taormina, p. 323-340) : étude "
            "philologique fine de fragments porphyriens conservés par "
            "Stobée (Anth. II 8 39-42 = Smith frr. 268-271). Porphyre "
            "lit le mythe d'Er à la lumière des réflexions "
            "hellénistiques sur causalité et responsabilité. Aporie "
            "centrale : étant donné que les vies des individus "
            "apparaissent déterminées et nécessitées par des forces "
            "extérieures, comment Platon peut-il affirmer que la vertu "
            "n'a pas de maître (Rép. 617e) ? Stratégie de Porphyre : "
            "(1) analyse sémantique sophistiquée fondée sur la logique ; "
            "(2) détermination du sens spécifique de choix (hairesis), "
            "auto-détermination (to autexousion), et ce-qui-est-en-notre-"
            "pouvoir (to eph' hêmin) ; (3) restriction du ἐφ' ἡμῖν à "
            "l'homme, comme capacité de la partie rationnelle de l'âme. "
            "Cette restriction résout l'aporie tout en sauvegardant la "
            "possibilité pour les individus d'exercer librement la "
            "vertu"
        ),
        description_en=(
            "Synthesis of ch. 17 (Taormina, p. 323-340): fine "
            "philological study of Porphyrian fragments preserved by "
            "Stobaeus (Anth. II 8 39-42 = Smith frr. 268-271). "
            "Porphyry reads the Myth of Er via Hellenistic reflections "
            "on causality and responsibility. Central aporia: given "
            "external determination of individual lives, how can Plato "
            "claim virtue has no master? Strategy: (1) sophisticated "
            "logic-grounded semantic analysis; (2) specific meanings of "
            "hairesis, to autexousion, to eph' hêmin; (3) restriction "
            "of eph' hêmin to humans as capacity of rational soul. The "
            "restriction solves the aporia and safeguards free virtue"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 17 — Choice, self-determination and what is in our power in Porphyry's interpretation of the myth of Er",
            pages="p. 323-340",
            author="Daniela Patrizia Taormina",
            md_line_range="ll. 11961-12860",
            extra={
                "key_fragments": ["Porphyry frr. 268-271 Smith = Stobaeus Anth. II 8 39-42"],
                "key_passage": "Plato Rep. X 614b ff. (Myth of Er)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate",
        type="synthesis",
        label="Bonazzi — Middle Platonists on fate and human autonomy: a confrontation with the Stoics",
        description=(
            "Synthèse du ch. 18 (Bonazzi, p. 283-310 — pagination "
            "approchée) : étude de la doctrine du *destin hypothétique* "
            "(heimarmenê ex hypotheseôs) — réponse platonicienne "
            "médiane (Albinos/Alcinoos, ps.-Plutarque De Fato, "
            "Apulée De Platone, Némésius, Calcidius) à la question : "
            "comment l'attribution de la responsabilité morale est-elle "
            "compatible avec la thèse que tout est déterminé ? Le "
            "destin platonicien est hypothétique au sens où il "
            "conditionne les conséquences d'un choix initial sans "
            "nécessiter ce choix lui-même : *si* X choisit A, *alors* B "
            "s'ensuit nécessairement. Les platoniciens médiens "
            "soutiennent ainsi la supériorité du platonisme sur les "
            "écoles hellénistiques (surtout le stoïcisme). Toutefois, "
            "selon Bonazzi, cette doctrine ne résout pas définitivement "
            "le problème : elle rend compte d'actions et de décisions "
            "singulières, mais pas de leurs *rapports mutuels* (donc "
            "pas du caractère comme histoire de choix sédimentés)"
        ),
        description_en=(
            "Synthesis of ch. 18 (Bonazzi): doctrine of hypothetical "
            "fate (heimarmenê ex hypotheseôs) — Middle Platonist "
            "response (Alcinous, ps.-Plutarch De Fato, Apuleius De "
            "Platone, Nemesius, Calcidius) to the question of how moral "
            "responsibility is compatible with universal determinism. "
            "Platonic fate is hypothetical: it conditions consequences "
            "of an initial choice without necessitating the choice "
            "itself. Bonazzi: this doctrine accounts for individual "
            "actions/decisions but not their mutual relations (hence "
            "not character as sedimented history)"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 18 — Middle Platonists on fate and human autonomy: a confrontation with the Stoics",
            pages="p. 283-310 (approx.)",
            author="Mauro Bonazzi",
            md_line_range="ll. 12861-13380",
            extra={
                "key_sources": ["Alcinous Didaskalikos 26", "ps.-Plutarch De Fato", "Calcidius In Tim.", "Nemesius Nat. Hom."],
                "thesis": "hypothetical fate solves only individual cases, not character relations",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch19_horn_augustine_liberum_arbitrium",
        type="synthesis",
        label="Horn — How close is Augustine's liberum arbitrium to the concept of to eph' hêmin?",
        description=(
            "Synthèse du ch. 19 (Horn, p. 295-310) : le concept de τὸ "
            "ἐφ' ἡμῖν ne joue aucun rôle *explicite* central dans les "
            "écrits d'Augustin. Mais il est fortement présent de "
            "manière *indirecte*, médiatisé par le concept de liberum "
            "arbitrium. Le liberum arbitrium augustinien remplit "
            "précisément la fonction de décrire ce qui est en notre "
            "disposition — dans cette mesure, il est un équivalent du "
            "ἐφ' ἡμῖν. Mais il *va au-delà* en décrivant aussi le "
            "périmètre de la responsabilité morale d'un agent "
            "individuel. Horn pose ainsi deux questions : (1) comment "
            "Augustin intègre-t-il la compréhension traditionnelle du "
            "ἐφ' ἡμῖν dans sa pensée ? (2) est-il innovant ? Horn défend "
            "une nuance contre Dihle 1982 : Augustin n'introduit pas "
            "ex nihilo le concept de volonté ; il ré-articule des "
            "éléments présents chez Platon, les stoïciens et "
            "Plotin/Porphyre. Le nouveau monde augustinien est celui "
            "du *libre arbitre*, à l'aube d'une ère nouvelle"
        ),
        description_en=(
            "Synthesis of ch. 19 (Horn, p. 295-310): the concept of to "
            "eph' hêmin plays no explicit central role in Augustine. "
            "But strongly present indirectly via liberum arbitrium. "
            "Augustinian liberum arbitrium fulfills the function of "
            "what-is-in-our-disposition (= eph' hêmin) but goes beyond "
            "by also describing the scope of individual moral "
            "responsibility. Horn defends a nuance against Dihle 1982: "
            "Augustine doesn't introduce will ex nihilo; he "
            "re-articulates Platonic, Stoic, and Plotinian/Porphyrian "
            "elements"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 19 — How close is Augustine's liberum arbitrium to the concept of to eph' hêmin?",
            pages="p. 295-310",
            author="Christoph Horn",
            md_line_range="ll. 13381-14080",
            extra={
                "key_works_discussed": ["De libero arbitrio", "De civitate dei XI 26", "De trinitate X-XV"],
                "interlocutor": "Dihle 1982 The Theory of Will in Classical Antiquity (nuanced critique)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch20_steel_proclus_human_or_divine_freedom",
        type="synthesis",
        label="Steel — Human or divine freedom: Proclus on what is up to us",
        description=(
            "Synthèse du ch. 20 (Steel, p. 311-328) : étude du "
            "troisième opuscule des Tria Opuscula de Proclus (De "
            "Providentia, Fato et eo quod in nobis), où Proclus "
            "répond aux objections de Théodore l'ingénieur défendant un "
            "déterminisme mécaniste radical. Stratégie procléenne : "
            "construire une *hiérarchie causale* (Providence > Destin > "
            "Auto-détermination de l'âme rationnelle). La Providence "
            "régit l'ordre cosmique global ; le Destin régit les "
            "phénomènes corporels et extérieurs (cf. l'astrologie de "
            "Bardesane et Plotin Enn. III 1) ; l'auto-détermination (τὸ "
            "αὐτεξούσιον) et le τὸ ἐφ' ἡμῖν appartiennent à l'âme "
            "rationnelle, qui *transcende* la chaîne fatale. La liberté "
            "humaine est donc une *participation* à la liberté divine — "
            "thèse néoplatonicienne mature qui prépare Boèce et la "
            "scolastique"
        ),
        description_en=(
            "Synthesis of ch. 20 (Steel, p. 311-328): study of Proclus's "
            "third Tria Opuscula treatise (De Providentia, Fato et eo "
            "quod in nobis), where Proclus answers Theodore the "
            "engineer's radical mechanistic determinism. Proclean "
            "strategy: build a causal hierarchy (Providence > Fate > "
            "rational soul's self-determination). Providence governs "
            "global cosmic order; Fate governs corporeal/external "
            "phenomena (cf. Bardesanes/Plotinus Enn. III 1); "
            "self-determination (to autexousion) and to eph' hêmin "
            "belong to the rational soul, transcending the fatal chain. "
            "Human freedom is participation in divine freedom — mature "
            "Neoplatonist thesis preparing Boethius and Scholasticism"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 20 — Human or divine freedom: Proclus on what is up to us",
            pages="p. 311-328",
            author="Carlos Steel",
            md_line_range="ll. 14081-14965",
            extra={
                "key_work": "Proclus De Providentia, Fato et eo quod in nobis (Tria Opuscula III)",
                "interlocutor_ancient": "Theodore the engineer",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch21_wildberg_epictetus_simplicius",
        type="synthesis",
        label="Wildberg — The will and its freedom: Epictetus and Simplicius on what is up to us",
        description=(
            "Synthèse du ch. 21 (Wildberg, p. 329-350) : étude de la "
            "lecture néoplatonicienne tardive d'Épictète par Simplicius "
            "dans son Commentaire sur l'Enchiridion. Wildberg situe le "
            "contexte historique : Simplicius rédige probablement ce "
            "commentaire après l'exil sassanide (529 CE, fermeture de "
            "l'Académie par Justinien), dans un état de circonstances "
            "« qui n'étaient certainement pas à lui ». Le commentaire "
            "est à la fois traité théorique d'éthique et démonstration "
            "pratique de la réponse philosophique à l'adversité. "
            "Wildberg défend que l'on ne peut crediter Épictète de la "
            "première articulation d'une notion de libre arbitre : la "
            "*prohaïrèsis* épictétéenne est une instance particulière "
            "de choix moral comme engagement rationnel, et reste "
            "déterminée par des considérations bien-formées — "
            "*non-libre* au sens absolu. Simplicius lit Épictète à "
            "travers la grille néoplatonicienne (autexousion comme "
            "fondement métaphysique)"
        ),
        description_en=(
            "Synthesis of ch. 21 (Wildberg, p. 329-350): study of "
            "Simplicius's late Neoplatonist reading of Epictetus in the "
            "Commentary on the Handbook, probably written after the "
            "Sasanian exile (529 CE, Justinian closure of the Academy). "
            "The commentary is both theoretical ethics treatise and "
            "practical demonstration of philosophical response to "
            "adversity. Wildberg argues against crediting Epictetus "
            "with the first articulation of free will: Epictetan "
            "prohairesis is a particular instance of moral choice as "
            "rational commitment, determined by well-formed "
            "considerations — not free in any absolute sense. "
            "Simplicius reads Epictetus via the Neoplatonist grid "
            "(autexousion as metaphysical foundation)"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 21 — The will and its freedom: Epictetus and Simplicius on what is up to us",
            pages="p. 329-350",
            author="Christian Wildberg",
            md_line_range="ll. 14966-15670",
            extra={
                "key_works": ["Epictetus Enchiridion", "Simplicius In Epicteti Enchiridion"],
                "historical_context": "Closure of Athenian Academy by Justinian, 529 CE",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview",
        type="synthesis",
        label="Frede M. — The eph' hêmin in ancient philosophy (posthumous reprint)",
        description=(
            "Synthèse du ch. 22 (M. Frede, p. 351-363) : article paru en "
            "2007 dans une revue grecque, réimprimé avec permission et "
            "préparé pour l'édition par Susan Sauvé Meyer (avec l'aide "
            "de Katerina Ierodiakonou). Thèses centrales : (1) chez "
            "Aristote, ἐφ' ἡμῖν signifie « ce qui est en notre pouvoir » "
            "au sens où ce n'est pas pure fonction de notre nature et "
            "n'est pas réglé par des facteurs hors de notre contrôle ; "
            "l'usage *n'implique pas* qu'on soit libre au sens "
            "indéterministe. (2) Chez les premiers stoïciens, les "
            "actions sont ἐφ' ἡμῖν *en tant qu'elles dépendent de notre "
            "assentiment* (sunkatathesis), ce qui *ne signifie pas* "
            "qu'on aurait pu faire ou choisir autrement dans les mêmes "
            "circonstances. (3) Les stoïciens tardifs comme Épictète "
            "raffinent : ce n'est pas l'action mais l'assentiment qui "
            "est ἐφ' ἡμῖν — *cela* se rapproche de la notion de libre "
            "arbitre, et c'est ainsi que Justin Martyr et Tatien le "
            "prennent (incompatible avec le destin stoïcien). (4) "
            "Alexandre d'Aphrodise relit cette conception du libre "
            "arbitre dans Aristote, mais c'est une rétro-projection. "
            "Article-charnière de la thèse Frede sur l'émergence "
            "tardive du libre arbitre"
        ),
        description_en=(
            "Synthesis of ch. 22 (M. Frede, p. 351-363): 2007 paper "
            "reprinted with permission, prepared by Sauvé Meyer (with "
            "Ierodiakonou). Central theses: (1) in Aristotle eph' hêmin "
            "means in our power, not function of our nature nor settled "
            "by factors outside our control; does NOT imply indeterminist "
            "freedom. (2) For early Stoics, actions are eph' hêmin "
            "insofar as they depend on assent (sunkatathesis), NOT "
            "implying could-have-done-otherwise. (3) Later Stoics like "
            "Epictetus refine: it is not action but assent that is eph' "
            "hêmin — this approximates free will, as Justin Martyr and "
            "Tatian take it (incompatible with Stoic fate). (4) "
            "Alexander reads this back into Aristotle (retroprojection). "
            "Pivot paper of Frede's thesis on late emergence of free will"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 22 — The eph' hêmin in ancient philosophy",
            pages="p. 351-363",
            author="Michael Frede (posthumous, ed. Sauvé Meyer with Ierodiakonou)",
            md_line_range="ll. 15671-16580",
            extra={
                "original_publication": "2007, Greek philosophical journal (Skepsis or similar)",
                "thesis_pivot": "Bobzien-Frede line on late emergence of free will via Alexander/Epictetus",
                "key_passages_discussed": [
                    "Herodotus VIII 29 (early ep' hêmin)",
                    "Pindar Pyth. VIII 76",
                    "Aristotle EN III",
                    "Epictetus Diss. I.1 + I.17 + 4.1",
                ],
            },
        ),
        confidence=0.99,
    ),
]


# =============================================================================
# ARGUMENTS (22) — one or two per chapter, capturing central scholarly thesis
# =============================================================================

NEW_ARGUMENTS: list[dict[str, Any]] = [
    _node(
        id="argument_johnson_2014_democritus_plasticity_intellectualism",
        type="argument",
        label="Johnson 2014 — Democritus's intellectualist ethics grounded on nature plasticity (gnômê reform)",
        description=(
            "Argument scholarly de Johnson (Destrée 2014 ch. 1) : "
            "l'éthique démocritéenne doit être lue, non comme « naïve » "
            "face au problème libre arbitre/déterminisme (Bailey 1928, "
            "Barnes 1979), mais comme une *thérapie cognitivo-"
            "comportementale* fondée sur la plasticité de la nature "
            "humaine. Trois prémisses : (1) la chance et les dieux ne "
            "sont pas des causes décisives du bien-être ; (2) la "
            "nature humaine n'est pas fixée mais *docile* (B33 : « la "
            "nature et l'enseignement sont presque identiques ; "
            "l'enseignement reforme l'homme et, en le reformant, "
            "produit une nature ») ; (3) la *gnômê* (B35, B175, B191), "
            "le *nous* (B175), la *phronêsis* (B119) sont les clés "
            "intellectuelles du succès. Conclusion : l'éthique "
            "démocritéenne est *à nous* (ἐφ' ἡμῖν) par la pensée — "
            "« changer notre esprit »"
        ),
        description_en=(
            "Scholarly argument by Johnson: Democritean ethics is not "
            "naive (contra Bailey, Barnes) but a proto-cognitive "
            "behavioral therapy grounded on human nature plasticity. "
            "Three premises: luck/gods not decisive; nature is docile "
            "(B33); gnômê/nous/phronêsis are intellectual keys. "
            "Conclusion: Democritean ethics is ours via thought"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 1",
            pages="p. 7-30",
            author="Monte Ransome Johnson",
            extra={
                "key_fragments": ["DK 68B33", "B35", "B173", "B175", "B191", "B197", "B242"],
                "thesis_type": "scholarly_reconstruction",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_destree_2014_plato_er_asymmetry",
        type="argument",
        label="Destrée 2014 — Asymmetry thesis on Plato's myth of Er (responsibility for virtue, ignorance for vice)",
        description=(
            "Argument scholarly de Destrée (Destrée 2014 ch. 2 + "
            "publication pub_destree_2014_plato_er) : Platon dans le "
            "mythe d'Er développe une thèse asymétrique de la "
            "responsabilité (la *asymmetry thesis* de Sauvé Meyer "
            "2011) : (a) la vertu est par nous (volontaire, "
            "ἐφ' ἡμῖν) ; (b) le vice est par ignorance (Tim. 86b ; "
            "personne ne fait le mal volontairement). Cette asymétrie "
            "explique pourquoi le mythe peut combiner « aitia "
            "helomenou, theos anaitios » (Rép. 617e) avec la thèse "
            "socratique de l'akrasia involontaire. Destrée défend que "
            "cette asymétrie *prépare* le τὸ ἐφ' ἡμῖν aristotélicien "
            "dans son ancrage éthique (et non purement métaphysique)"
        ),
        description_en=(
            "Scholarly argument by Destrée: Plato's myth of Er develops "
            "the Sauvé Meyer 2011 asymmetry thesis — virtue is by us "
            "(voluntary, eph' hêmin), vice is by ignorance (Tim. 86b). "
            "This explains how the myth combines aitia helomenou "
            "(Rep. 617e) with Socratic involuntary akrasia. Prepares "
            "the Aristotelian eph' hêmin in ethical anchoring"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 2",
            pages="p. 31-52",
            author="Pierre Destrée",
            extra={
                "key_passages": ["Plato Rep. X 617e", "Tim. 86b", "Laws X"],
                "linked_publication": "pub_destree_2014_plato_er",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_frede_d_2014_aristotle_psychological_determinism",
        type="argument",
        label="Frede D. 2014 — Aristotle's psychological determinism without will",
        description=(
            "Argument scholarly de Dorothea Frede (Destrée 2014 ch. 3) : "
            "Aristote n'a pas de notion de volonté, donc a fortiori "
            "pas de libre arbitre, mais sa théorie de la délibération "
            "et du choix est *psychologiquement déterministe*. La "
            "liberté comme indifférence morale aurait été inconcevable "
            "pour Aristote. Pour comprendre la portée et les limites "
            "du déterminisme psychologique aristotélicien, il faut "
            "examiner la notion de *disposition* (hexis) / caractère "
            "(éthos), qui détermine l'action sans la nécessiter "
            "extérieurement. Convergence avec Bobzien, Sauvé Meyer, "
            "Echeñique contre les lectures indéterministes "
            "(Sorabji 1980, Kenny 1979)"
        ),
        description_en=(
            "Scholarly argument by D. Frede: Aristotle has no notion of "
            "will, a fortiori no free will, but his theory of "
            "deliberation and choice is psychologically deterministic. "
            "Moral indifference inconceivable for Aristotle. Disposition "
            "(hexis)/character (ethos) determines action without "
            "external necessitation. Convergence with Bobzien, Sauvé "
            "Meyer, Echeñique against indeterminist readings (Sorabji, "
            "Kenny)"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 3",
            pages="p. 53-75",
            author="Dorothea Frede",
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist",
        type="argument",
        label="Bobzien 2014 — Anti-indeterminist reading of EN III 1113b7-8",
        description=(
            "Argument scholarly de Bobzien (Destrée 2014 ch. 4 + "
            "Bobzien 2014a, b) : le passage EN III 1113b7-8 (« là où il "
            "est en notre pouvoir de dire oui, il est en notre pouvoir "
            "de dire non »), souvent cité comme appui indiscutable d'une "
            "lecture indéterministe d'Aristote, doit être lu dans la "
            "direction opposée. Bobzien défend que la traduction "
            "habituelle (« we are free to act ») est *anachronique* : "
            "l'expression ἐφ' ἡμῖν ne signifie pas être libre au sens "
            "indéterministe. Bobzien argue que la « libre choix » est "
            "ici une expression *non-technique* de la bilatéralité "
            "agent-contrôlée — compatible avec la causation par le "
            "caractère. Étend Bobzien 1998 (chapitre sur Aristote) et "
            "Bobzien 2013 'Found in Translation'"
        ),
        description_en=(
            "Scholarly argument by Bobzien: EN III 1113b7-8 ('where we "
            "are free to say yes, we are free to say no'), often "
            "invoked for indeterministic Aristotle, should be read the "
            "opposite way. The standard translation is anachronistic: "
            "eph' hêmin does not mean free in an indeterminist sense. "
            "'Free choice' here is a non-technical expression of "
            "agent-controlled two-sidedness, compatible with "
            "character-causation. Extends Bobzien 1998 + 2013"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 4",
            pages="p. 77-91",
            author="Susanne Bobzien",
            extra={
                "key_passage": "Aristotle EN III 1113b7-8",
                "extends_publications": ["pub_bobzien_1998_inadvertent", "pub_bobzien_2014_choice_responsibility"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap",
        type="argument",
        label="Sauvé Meyer 2014 — Aristotle's two-sidedness is not PAP",
        description=(
            "Argument scholarly de Sauvé Meyer (Destrée 2014 ch. 5) : "
            "la bilatéralité aristotélicienne du τὸ ἐφ' ἡμῖν (EE II 6, "
            "EN III) ne doit pas être assimilée au Principle of "
            "Alternate Possibilities (PAP) du libertarianisme moderne "
            "(Frankfurt 1969). Pourquoi ? Parce que le PAP souligne la "
            "*possibilité d'alternatives non-actuelles* à nos actions, "
            "tandis qu'Aristote cherche à montrer que *nos actions "
            "elles-mêmes* — et non leurs alternatives — sont à nous. "
            "Présenter le τὸ ἐφ' ἡμῖν comme affirmation de la "
            "contingence des actions humaines est trompeur. La "
            "bilatéralité affirme le *contrôle agentif*, neutre "
            "vis-à-vis du déterminisme"
        ),
        description_en=(
            "Scholarly argument by Sauvé Meyer: Aristotelian "
            "two-sidedness of to eph' hêmin (EE II 6, EN III) should "
            "not be identified with the modern PAP (Frankfurt 1969). "
            "PAP emphasizes non-actual alternatives; Aristotle is "
            "concerned that our actions themselves are ours. "
            "Two-sidedness affirms agent control, neutral wrt "
            "determinism"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 5",
            pages="p. 93-114",
            author="Susan Sauvé Meyer",
            extra={
                "key_passage": "Aristotle EE II 6 1223a9-15",
                "modern_distance": "anti-Frankfurt 1969 PAP reading",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_echenique_2014_aristotle_double_position_appraisals_accountability",
        type="argument",
        label="Echeñique 2014 — Aristotle's double position: compatibilist on appraisals, incompatibilist on accountability",
        description=(
            "Argument scholarly d'Echeñique (Destrée 2014 ch. 6) : "
            "Aristote tient une *double position* cohérente sur la "
            "responsabilité morale. (1) Il est *compatibiliste* en "
            "matière d'évaluations éthiques (appraisals : "
            "louange/blâme) — préoccupation centrale de l'Éthique. (2) "
            "Il est *incompatibiliste* en matière d'imputabilité "
            "(accountability : mérite des récompenses et châtiments). "
            "Les passages-clés sur τὸ ἐφ' ἡμῖν soutiennent cette double "
            "position : EN III 5 (sur l'imputabilité du caractère) "
            "fournit l'évidence proto-incompatibiliste. Position "
            "intermédiaire entre Bobzien/Sauvé Meyer (compatibilisme "
            "intégral) et Sorabji/Kenny (incompatibilisme intégral)"
        ),
        description_en=(
            "Scholarly argument by Echeñique: Aristotle holds a "
            "coherent double position on moral responsibility. (1) "
            "Compatibilist on ethical appraisals (praise/blame). (2) "
            "Incompatibilist on accountability (desert of rewards/"
            "punishments). EN III 5 (on character accountability) "
            "provides proto-incompatibilist evidence. Intermediate "
            "position between Bobzien/Sauvé Meyer (full compatibilism) "
            "and Sorabji/Kenny (full incompatibilism)"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 6",
            pages="p. 115-135",
            author="Javier Echeñique",
            extra={
                "key_passages": ["Aristotle EN III 5", "EE II 6 1223a9-15"],
                "novel_thesis": "double_position_appraisals_vs_accountability",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_vogt_2014_stoic_cyclic_assent_eph_hemin",
        type="argument",
        label="Vogt 2014 — Stoic agency via cyclic assent, not freedom",
        description=(
            "Argument scholarly de Vogt (Destrée 2014 ch. 7) : la "
            "question stoïcienne du τὸ ἐφ' ἡμῖν est mieux *non* posée "
            "en termes de liberté/déterminisme, car la physique et la "
            "théorie de la causalité stoïciennes divergent trop "
            "profondément des cadres modernes. Trois thèses : (1) "
            "l'agent stoïcien assent comme le cognisant qu'elle est — "
            "le τὸ ἐφ' ἡμῖν est l'expression du *caractère cognitif* "
            "de l'agent ; (2) le τὸ ἐφ' ἡμῖν est la capacité d'adhérer "
            "aux normes d'assentiment — ce point est la difficulté "
            "centrale, expliquant comment l'agent peut devenir "
            "meilleur assenteur ; (3) la pensée « je ferai ce que je "
            "ferai » est frustrante seulement pour le raisonneur "
            "imparfait — pour le sage, n'avoir qu'une option est "
            "satisfaisant car elle est *la meilleure*"
        ),
        description_en=(
            "Scholarly argument by Vogt: the Stoic question of to eph' "
            "hêmin is best NOT cast in freedom/determinism terms. "
            "Three theses: (1) Stoic agent assents as cognizer she is; "
            "(2) to eph' hêmin = capacity to adhere to assent norms — "
            "central difficulty; (3) 'I'll do what I'll do' frustrates "
            "only the imperfect reasoner — for the sage, having one "
            "option is fine because it is the best"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 7",
            pages="p. 137-158",
            author="Katja Maria Vogt",
            extra={
                "key_example": "Cautious Umbrella Carrier",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_gomez_2014_chrysippus_reactive_compatibilism",
        type="argument",
        label="Gómez 2014 — Chrysippean compatibilism reconstructed from reactions to objections",
        description=(
            "Argument scholarly de Gómez (Destrée 2014 ch. 8) : la "
            "théorie chrysippéenne de la compatibilité entre destin "
            "stoïcien et responsabilité morale se reconstruit "
            "*réactivement*, c'est-à-dire à partir des objections "
            "spécifiques auxquelles Chrysippe a tenté de répondre. "
            "Trois objections-clés analysées : (1) l'argument paresseux "
            "(*argos logos*) ; (2) l'argument du destin réflexif (« si "
            "je suis destiné à mourir, peu importe ce que je fais ») ; "
            "(3) l'objection sur la fixité des dispositions. Chrysippe "
            "y répond par : (a) la distinction des causes principales "
            "et auxiliaires ; (b) le cylindre comme analogie psychique ; "
            "(c) les co-fatalia. Lecture compatibiliste alignée sur "
            "Bobzien 1998"
        ),
        description_en=(
            "Scholarly argument by Gómez: Chrysippean compatibilism "
            "between fate and responsibility is reconstructed reactively "
            "from the objections Chrysippus addressed. Three analyzed: "
            "lazy argument (argos logos); reflexive fate; fixity of "
            "dispositions. Chrysippus answers via: principal/auxiliary "
            "causes; cylinder psychic analogy; co-fatalia. Aligned "
            "with Bobzien 1998"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 8",
            pages="p. 159-167",
            author="Laura Liliana Gómez",
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_gourinat_2014_in_nostra_potestate_not_eph_hemin",
        type="argument",
        label="Gourinat 2014 — In nostra potestate may not translate eph' hêmin (re Chrysippus)",
        description=(
            "Argument scholarly iconoclaste de Gourinat (Destrée 2014 "
            "ch. 9) : la formule latine *in nostra potestate*, "
            "abondante dans le De Fato de Cicéron et attribuée à "
            "Chrysippe (« assensio in nostra potestate »), n'est *pas "
            "nécessairement* une traduction du grec ἐφ' ἡμῖν. Donc les "
            "sources cicéroniennes ne sont pas des preuves "
            "irréfutables que Chrysippe ait utilisé l'expression ἐφ' "
            "ἡμῖν en grec. Hypothèse alternative : Chrysippe préférait "
            "des expressions *à une voix* (causales) comme παρ' ἡμᾶς "
            "(« par nous », attesté chez Diogénien apud Eusèbe PE "
            "6.8.2) ou ἐξ ἡμῶν (« à partir de nous »). Le ἐφ' ἡμῖν *à "
            "deux voix* (potestatif) ne deviendrait technique que dans "
            "le moyen-stoïcisme et chez Épictète. Conteste partiellement "
            "la thèse Bobzien 1998 sur Chrysippe et le ἐφ' ἡμῖν"
        ),
        description_en=(
            "Iconoclastic scholarly argument by Gourinat: Latin in "
            "nostra potestate, frequent in Cicero's De Fato and "
            "attributed to Chrysippus, is NOT necessarily a translation "
            "of Greek eph' hêmin. Ciceronian sources thus do not "
            "decisively prove Chrysippus used eph' hêmin in Greek. "
            "Hypothesis: Chrysippus preferred one-sided causal "
            "expressions par' hêmas (attested in Diogenianus apud "
            "Eusebius PE 6.8.2) or ex hêmôn. Two-sided potestative eph' "
            "hêmin becomes technical only in middle/late Stoicism "
            "(Epictetus). Partially challenges Bobzien 1998"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 9",
            pages="p. 169-181",
            author="Jean-Baptiste Gourinat",
            extra={
                "iconoclastic_relative_to": "Bobzien 1998 on Chrysippus's adoption of eph' hêmin",
                "key_witnesses_discussed": [
                    "Plutarch Stoic. Repugn. 47 1056b = SVF 2.997",
                    "Diogenianus apud Eusebius PE 6.8.2 = SVF 2.999",
                    "Alexander Aphrod. De Fato 13 = SVF 2.979",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_vimercati_2014_panaetius_eph_hemin_unique_occurrence",
        type="argument",
        label="Vimercati 2014 — Panaetius's unique eph' hêmin occurrence (Nemesius) confirms oikeiôsis-self-knowledge-responsibility nexus",
        description=(
            "Argument scholarly de Vimercati (Destrée 2014 ch. 10) : "
            "l'unique occurrence de τὸ ἐφ' ἡμῖν dans les fragments de "
            "Panétius (Némésius Nat. hom. 26 = Panaetius fr. B26 "
            "Vimercati / T126 Alesse / fr. 86a van Straaten) confirme "
            "l'articulation panétienne entre *oikéiôsis*, "
            "*connaissance de soi* et *responsabilité*. Stratégie "
            "argumentative en trois temps : (1) le rejet panétien de "
            "l'ekpurôsis stoïcienne (conflagration cyclique) "
            "élargit la responsabilité humaine ; (2) l'interprétation "
            "panétienne de l'oikéiôsis dans la lignée "
            "socratico-platonicienne fonde la connaissance de soi "
            "comme axe ; (3) la théorie des quatre personae (Cic. "
            "Off. I) laisse explicitement place au ἐφ' ἡμῖν dans les "
            "troisième (casus) et quatrième (iudicium/voluntas) "
            "personae"
        ),
        description_en=(
            "Scholarly argument by Vimercati: the single occurrence of "
            "to eph' hêmin in Panaetius's fragments (Nemesius Nat. hom. "
            "26 = Panaet. fr. B26 Vim.) confirms the Panaetian linkage "
            "between oikeiôsis, self-knowledge, and responsibility. "
            "Three steps: rejection of Stoic conflagration expands "
            "responsibility; Socratic-Platonic oikeiôsis grounds "
            "self-knowledge; four-personae theory explicitly leaves "
            "room for eph' hêmin in third (casus) and fourth "
            "(iudicium/voluntas) personae"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 10",
            pages="p. 183-198",
            author="Emmanuele Vimercati",
            extra={
                "key_fragment": "Panaetius fr. B26 Vim. = Nemesius Nat. hom. 26",
                "key_text_secondary": "Cicero De officiis I (four personae)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus",
        type="argument",
        label="Salles 2014 — Epictetus's causal conception of eph' hêmin in continuity with Chrysippus",
        description=(
            "Argument scholarly de Salles (Destrée 2014 ch. 11) : la "
            "conception épictétéenne du τὸ ἐφ' ἡμῖν est *causale* — "
            "une action est en notre pouvoir si nous en sommes la "
            "cause (aition) — et non pas dépendante de l'existence "
            "d'alternatives. Trois preuves : (1) Diss. I.11 "
            "(philostorgia) déploie un argument causal explicite ; (2) "
            "l'argument du cylindre chrysippéen (Cic. De Fato 40-44) "
            "fournit le modèle causal antérieur ; (3) Épictète et "
            "Chrysippe peuvent répondre conjointement à deux objections "
            "standard contre les conceptions causales (regress des "
            "causes, manipulation). Contre Long 2002 et Brennan 2000 "
            "(qui voient chez Épictète une rupture)"
        ),
        description_en=(
            "Scholarly argument by Salles: Epictetus's conception of "
            "to eph' hêmin is causal — an action is in our power if we "
            "are its cause (aition), not dependent on alternatives. "
            "Three proofs: Diss. I.11 (philostorgia) causal argument; "
            "Chrysippean cylinder (Cic. De Fato 40-44) as prior causal "
            "model; Epictetus + Chrysippus jointly answer standard "
            "objections (causal regress, manipulation). Against "
            "Long 2002, Brennan 2000"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 11",
            pages="p. 199-217",
            author="Ricardo Salles",
            extra={
                "key_passages": ["Epictetus Diss. I.11", "Cicero De Fato 40-44"],
                "rivals_engaged": ["Long 2002 Epictetus Stoic Socratic Guide", "Brennan 2000 OSAP 21"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_boeri_2014_marcus_present_indifferents_eph_hemin",
        type="argument",
        label="Boeri 2014 — Marcus's eph' hêmin via the conjunction of present-time and indifferents",
        description=(
            "Argument scholarly de Boeri (Destrée 2014 ch. 12) : la "
            "conjonction du *présent* et des *indifférents* (adiaphora) "
            "est la clé pour comprendre la fonction de τὸ ἐφ' ἡμῖν "
            "chez Marc Aurèle. Trois étapes : (1) la philosophie pour "
            "Marc est une *manière de vivre* qui garantit que l'on "
            "saura s'abstenir de désirer ce qui n'est pas en notre "
            "pouvoir ; (2) Marc soutient que notre esprit est ce qui "
            "confère « réalité » aux choses extérieures — l'esprit "
            "individuel, en tant qu'il dépend de soi, donne valeur ou "
            "non-valeur aux indifférents pour la vie pratique ; (3) "
            "les impératifs marcusiens (Med. passim) ne sont pas "
            "anti-théoriques mais positionnement *thétique* d'arguments "
            "théoriques"
        ),
        description_en=(
            "Scholarly argument by Boeri: the conjunction of present "
            "and indifferents (adiaphora) is key for understanding the "
            "function of to eph' hêmin in Marcus Aurelius. Three steps: "
            "philosophy as way of life enabling abstention from desiring "
            "what is not in our power; mind bestows 'reality' on "
            "externals — individual mind gives value/disvalue to "
            "indifferents; Marcus's imperatives are thetic positioning "
            "of theoretical arguments"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 12",
            pages="p. 219-243",
            author="Marcelo D. Boeri",
            extra={
                "key_passages": ["Marcus Med. 2.17", "4.3", "6.32", "8.41-43"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_zingano_2014_alexander_liability_vs_possibility",
        type="argument",
        label="Zingano 2014 — Alexander's distinction between liability and possibility of acting otherwise",
        description=(
            "Argument scholarly de Zingano (Destrée 2014 ch. 13) : "
            "Alexandre dans De Fato §§ 26-29 distingue deux sens de "
            "« pouvoir agir autrement » : (1) la *liability* (au sens "
            "fort) d'être *capable* de faire x ou non-x dans les "
            "circonstances mêmes, où x et non-x sont *contraires* "
            "comme bon et mauvais — ce sens est requis pour la "
            "constitution du caractère par les actions ; (2) la "
            "*possibilité* (au sens faible) d'agir différemment, sans "
            "contrariété (par exemple, choisir entre deux bonnes "
            "actions). Le sage ne peut faire que des « contraires » au "
            "sens faible (il ne peut être méchant). Conséquence : le "
            "libertarianisme alexandrien sur la formation du caractère "
            "est compatible avec un déterminisme psychologique rigide "
            "sur les actions du sage. Soutient Sharples 1983 contre "
            "Bobzien 1998 sur la cohérence d'Alexandre"
        ),
        description_en=(
            "Scholarly argument by Zingano: Alexander in De Fato §§ "
            "26-29 distinguishes two senses of acting otherwise. (1) "
            "Liability (strong): able to do x or not-x in the very "
            "circumstances, where x and not-x are contraries — "
            "required for character constitution. (2) Possibility "
            "(weak): acting differently without contrariety. The sage "
            "only does 'opposites' in the weak sense. Consequence: "
            "Alexandrian libertarianism on character-formation is "
            "compatible with rigid psychological determinism on "
            "sage's actions. Supports Sharples 1983 against Bobzien "
            "1998 on Alexander's coherence"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 13",
            pages="p. 245-263",
            author="Marco Zingano",
            extra={
                "key_passage": "Alexander De Fato §§ 26-29 (= Bruns p. 196.13-200.12)",
                "scholarly_alignment": "Sharples 1983 contra Bobzien 1998 on Alexander",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_morel_2014_epicurean_eph_hemin_primary_evidence",
        type="argument",
        label="Morel 2014 — Epicurean eph' hêmin as primary evidence, not demonstrandum",
        description=(
            "Argument scholarly de Morel (Destrée 2014 ch. 14) : il "
            "n'existe et il ne peut exister aucune *démonstration* "
            "épicurienne du τὸ ἐφ' ἡμῖν, car pour l'épicurien, "
            "l'existence du dépendant-de-nous est une *évidence "
            "primaire* — comparable aux prolepses cognitives. Trois "
            "types d'arguments épicuriens soutiennent indirectement la "
            "thèse : (1) cosmologique (Lettre à Ménécée : le sage ne "
            "dépend pas absolument d'une chaîne causale ; cf. clinamen "
            "lucrétien) ; (2) éthique (Sur la Nature, livre XXV : "
            "absurdités morales de la négation) ; (3) épistémologique "
            "(absurdité logique de la négation = se nier comme agent "
            "rationnel). Position qui dialogue avec Bobzien 2000 'Did "
            "Epicurus Discover the Free Will Problem?' (OSAP) — Morel "
            "y répond positivement *modulo* la qualification : Épicure "
            "n'a pas découvert le *problème* mais a *présupposé* la "
            "réalité du ἐφ' ἡμῖν comme évidence"
        ),
        description_en=(
            "Scholarly argument by Morel: there is and can be no "
            "Epicurean demonstration of to eph' hêmin, because for the "
            "Epicurean the existence of the up-to-us is primary "
            "evidence — analogous to cognitive prolepseis. Three "
            "supporting argument types: cosmological (Letter to "
            "Menoeceus + Lucretian clinamen); ethical (Peri Phuseos "
            "XXV); epistemological (logical absurdity of denial = "
            "self-refutation as rational agent). Dialogues with "
            "Bobzien 2000 (OSAP) — Morel answers positively modulo "
            "qualification"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 14",
            pages="p. 265-282",
            author="Pierre-Marie Morel",
            extra={
                "rival_engaged": "Bobzien 2000 'Did Epicurus Discover the Free Will Problem?'",
                "key_works": ["Epicurus Letter to Menoeceus 133", "Peri Phuseos book XXV", "Lucretius DRN II 251-93"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_maso_2014_cicero_motus_animi_voluntarius_independence",
        type="argument",
        label="Maso 2014 — Cicero's motus animi voluntarius as semantically independent of eph' hêmin",
        description=(
            "Argument scholarly de Maso (Destrée 2014 ch. 15) : "
            "l'expression cicéronienne *motus animi voluntarius* — "
            "employée 14 fois dans le De Fato et seulement une fois "
            "ailleurs (Tusc. 4.79) — possède une autonomie sémantique "
            "vis-à-vis du grec ἐφ' ἡμῖν. Trois constats : (1) les "
            "termes grecs (ἐφ' ἡμῖν stoïcien, par' hêmas épicurien, "
            "ex hêmôn) répondent à des sémantiques différentes ; (2) "
            "le PAP de O'Keefe 2005 obscurcit ces distinctions ; (3) "
            "Cicéron utilise l'épicurisme comme miroir pour développer "
            "sa propre position via une *réception originale* du "
            "clinamen lucrétien. Position alignée sur Gourinat (ch. 9) "
            "sur l'autonomie linguistique latine"
        ),
        description_en=(
            "Scholarly argument by Maso: Cicero's motus animi "
            "voluntarius (14 occurrences in De Fato, 1 elsewhere in "
            "Tusc. 4.79) has semantic autonomy from Greek eph' hêmin. "
            "Three observations: Greek terms (eph' hêmin Stoic, par' "
            "hêmas Epicurean, ex hêmôn) respond to different "
            "semantics; O'Keefe 2005 PAP obscures these distinctions; "
            "Cicero uses Epicureanism as mirror via original reception "
            "of Lucretian clinamen. Aligned with Gourinat (ch. 9) on "
            "Latin linguistic autonomy"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 15",
            pages="p. 283-300",
            author="Stefano Maso",
            extra={
                "key_passages": ["Cicero De Fato 9, 25, 31, 40, 41, 45", "Tusc. 4.79"],
                "rivals_engaged": ["O'Keefe 2005 Epicurus on Freedom"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_gerson_2014_plotinus_qualified_moral_responsibility_against_strawson",
        type="argument",
        label="Gerson 2014 — Plotinian qualified moral responsibility against Strawson's Basic Argument",
        description=(
            "Argument scholarly de Gerson (Destrée 2014 ch. 16) : "
            "réponse plotinienne reconstruite à l'« argument de base » "
            "de Galen Strawson (1994 + 2002), qui conclut à "
            "l'impossibilité de la responsabilité morale de tout "
            "non-causa-sui. Stratégie reconstruite : (1) Plotin accepte "
            "que la plupart de ce qu'on prend ordinairement pour ἐφ' "
            "ἡμῖν ne l'est pas sans qualification ; (2) il refuse "
            "néanmoins l'option binaire de Strawson "
            "(unqualified-or-nothing) ; (3) la *responsabilité morale "
            "qualifiée* suffit pour distinguer continence/incontinence "
            "et vertu/vice ; (4) le paradigme de la responsabilité "
            "morale *non-qualifiée* reste intact dans la volonté "
            "complètement libre de l'Un (Enn. VI 8 [39] sur l'Un comme "
            "cause-de-soi). Conclusion : Plotin offre une réponse "
            "originale et résiliente à Strawson"
        ),
        description_en=(
            "Scholarly argument by Gerson: reconstructed Plotinian "
            "answer to Galen Strawson's Basic Argument (1994 + 2002) "
            "concluding the impossibility of moral responsibility for "
            "any non-causa-sui. Strategy: (1) Plotinus accepts much of "
            "ordinary eph' hêmin is qualified; (2) rejects Strawson's "
            "binary (unqualified-or-nothing); (3) qualified moral "
            "responsibility suffices for continence/incontinence and "
            "virtue/vice distinctions; (4) paradigm of unqualified "
            "moral responsibility remains intact in completely "
            "unfettered will of the One (Enn. VI 8 [39] on One as "
            "causa sui)"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 16",
            pages="p. 301-322",
            author="Lloyd P. Gerson",
            extra={
                "modern_interlocutor": "Galen Strawson 1994 (PSA) + 2002 (book)",
                "key_text": "Plotinus Enn. VI 8 [39]",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_taormina_2014_porphyry_eph_hemin_rational_soul_only",
        type="argument",
        label="Taormina 2014 — Porphyry restricts eph' hêmin to the rational part of the soul",
        description=(
            "Argument scholarly de Taormina (Destrée 2014 ch. 17) : "
            "Porphyre dans les frr. 268-271 Smith (= Stobée Anth. II 8 "
            "39-42) distingue trois notions souvent confondues : "
            "*choix* (hairesis), *auto-détermination* (to autexousion), "
            "et *ce-qui-est-en-notre-pouvoir* (to eph' hêmin). "
            "Stratégie sémantique sophistiquée fondée sur la logique : "
            "(1) hairesis appartient à toute âme (humaine et animale) ; "
            "(2) to autexousion implique le pouvoir réfléchi de l'âme "
            "humaine sur ses propres impulsions ; (3) to eph' hêmin est "
            "restreint à la *partie rationnelle* de l'âme humaine — "
            "qui seule peut exercer librement la vertu. Cette "
            "restriction résout l'aporie du mythe d'Er : étant donné "
            "que les vies sont extérieurement déterminées, comment "
            "Platon peut-il maintenir que la vertu n'a pas de maître "
            "(Rép. 617e) ? Réponse : la vertu reste libre car ancrée "
            "dans la rationalité de l'âme"
        ),
        description_en=(
            "Scholarly argument by Taormina: Porphyry in frr. 268-271 "
            "Smith (= Stobaeus Anth. II 8 39-42) distinguishes three "
            "often-conflated notions: hairesis (choice), to autexousion "
            "(self-determination), to eph' hêmin (what is in our "
            "power). Sophisticated logic-grounded semantic strategy: "
            "hairesis = all souls; to autexousion = human soul's "
            "reflexive power over its impulses; to eph' hêmin = "
            "rational part only — alone capable of free virtue. "
            "Restriction solves myth-of-Er aporia"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 17",
            pages="p. 323-340",
            author="Daniela Patrizia Taormina",
            extra={
                "key_fragments": "Porphyry frr. 268-271 Smith = Stobaeus Anth. II 8 39-42",
                "platonic_anchor": "Plato Rep. X 614b-621d (Myth of Er) + 617e (aitia helomenou)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_bonazzi_2014_middle_platonist_hypothetical_fate_partial_solution",
        type="argument",
        label="Bonazzi 2014 — Middle Platonist hypothetical fate as partial Platonic solution to Stoic determinism",
        description=(
            "Argument scholarly de Bonazzi (Destrée 2014 ch. 18) : la "
            "doctrine platonicienne médiane du *destin hypothétique* "
            "(heimarmenê ex hypotheseôs), attestée chez Alcinoos "
            "(Didask. 26), ps.-Plutarque (De Fato), Apulée (De Plat. "
            "I), Némésius (Nat. hom. 34-43), Calcidius (In Tim. "
            "143-189), est une réponse platonicienne à la question : "
            "comment l'attribution de la responsabilité morale "
            "est-elle compatible avec le déterminisme universel ? "
            "Stratégie : le destin platonicien est *hypothétique* — il "
            "conditionne les conséquences d'un choix initial sans "
            "nécessiter ce choix lui-même (« si A choisit X, alors Y "
            "s'ensuit nécessairement »). Cela maintient les humains "
            "responsables des choix tout en préservant le déterminisme "
            "conséquentiel. Limite, selon Bonazzi : la doctrine rend "
            "compte d'actions et de décisions singulières, mais non "
            "de leurs *rapports mutuels* — donc pas du caractère "
            "comme sédimentation des choix"
        ),
        description_en=(
            "Scholarly argument by Bonazzi: Middle Platonist "
            "hypothetical fate (heimarmenê ex hypotheseôs), attested in "
            "Alcinous Didask. 26, ps.-Plutarch De Fato, Apuleius De "
            "Plat. I, Nemesius Nat. hom. 34-43, Calcidius In Tim. "
            "143-189. Platonic strategy: fate is hypothetical — "
            "conditions consequences of initial choice without "
            "necessitating it ('if A chooses X, then Y follows "
            "necessarily'). Maintains responsibility for choice + "
            "consequential determinism. Limit per Bonazzi: accounts "
            "for individual actions but not mutual relations — hence "
            "not character as sedimentation"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 18",
            pages="p. 283-294 (approximate, internal volume reorder)",
            author="Mauro Bonazzi",
            extra={
                "key_sources": ["Alcinous Didask. 26", "ps.-Plutarch De Fato", "Apuleius De Plat. I", "Nemesius Nat. hom. 34-43", "Calcidius In Tim. 143-189"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_horn_2014_augustine_liberum_arbitrium_equivalent_plus_eph_hemin",
        type="argument",
        label="Horn 2014 — Augustine's liberum arbitrium is functionally equivalent to and goes beyond eph' hêmin",
        description=(
            "Argument scholarly de Horn (Destrée 2014 ch. 19) : le "
            "concept augustinien de *liberum arbitrium* est "
            "fonctionnellement équivalent au τὸ ἐφ' ἡμῖν dans sa "
            "fonction descriptive (ce qui est dans notre disposition) "
            "mais le *dépasse* en décrivant aussi le périmètre de la "
            "responsabilité morale d'un agent individuel. Trois "
            "thèses : (1) Augustin n'introduit pas ex nihilo le "
            "concept de volonté (contre Dihle 1982) — il ré-articule "
            "des éléments présents chez Platon, les stoïciens et "
            "Plotin/Porphyre ; (2) le liberum arbitrium augustinien "
            "intègre la compréhension traditionnelle du ἐφ' ἡμῖν dans "
            "un cadre nouveau ; (3) Augustin est innovant en "
            "élargissant le ἐφ' ἡμῖν à la responsabilité globale du "
            "moi (cf. cogito-argument De lib. arb. 2.3.7 ; De civ. dei "
            "11.26 ; De trin. 10.10.13-15.12.21)"
        ),
        description_en=(
            "Scholarly argument by Horn: Augustinian liberum arbitrium "
            "is functionally equivalent to to eph' hêmin in descriptive "
            "function but goes beyond by also describing scope of "
            "individual moral responsibility. Three theses: Augustine "
            "doesn't introduce will ex nihilo (against Dihle 1982); "
            "liberum arbitrium integrates traditional eph' hêmin into "
            "new framework; Augustine innovates by extending eph' hêmin "
            "to global self-responsibility (cogito-argument)"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 19",
            pages="p. 295-310",
            author="Christoph Horn",
            extra={
                "key_passages_augustine": ["De lib. arb. 2.3.7", "De civ. dei 11.26", "De trin. 10.10.13-15.12.21"],
                "rival_engaged": "Dihle 1982 (nuanced critique)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_steel_2014_proclus_causal_hierarchy_providence_fate_eph_hemin",
        type="argument",
        label="Steel 2014 — Proclus's causal hierarchy Providence > Fate > eph' hêmin",
        description=(
            "Argument scholarly de Steel (Destrée 2014 ch. 20) : "
            "Proclus dans son troisième opuscule (De Providentia, "
            "Fato et eo quod in nobis) construit une *hiérarchie "
            "causale tripartite* en réponse au déterminisme mécaniste "
            "de Théodore l'ingénieur. (1) La Providence (pronoia) "
            "régit l'ordre cosmique global comme bonté providentielle "
            "non-mécaniste. (2) Le Destin (heimarmenê) régit les "
            "phénomènes corporels et extérieurs, comme chez Bardesane "
            "et Plotin Enn. III 1. (3) L'auto-détermination (το "
            "αὐτεξούσιον) et le τὸ ἐφ' ἡμῖν appartiennent à l'âme "
            "rationnelle, qui *transcende* la chaîne fatale par "
            "participation à la liberté divine. Thèse "
            "néoplatonicienne mature qui prépare Boèce (Consolatio V) "
            "et la scolastique latine sur la prescience divine"
        ),
        description_en=(
            "Scholarly argument by Steel: Proclus in his third "
            "opusculum builds a tripartite causal hierarchy in response "
            "to Theodore the engineer's mechanistic determinism. (1) "
            "Providence (pronoia) governs global cosmic order as "
            "non-mechanistic providential goodness. (2) Fate "
            "(heimarmenê) governs corporeal/external phenomena (cf. "
            "Bardesanes, Plotinus Enn. III 1). (3) Self-determination "
            "(to autexousion) and to eph' hêmin belong to the rational "
            "soul, transcending the fatal chain via participation in "
            "divine freedom. Mature Neoplatonist thesis preparing "
            "Boethius Cons. V and Latin Scholasticism"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 20",
            pages="p. 311-328",
            author="Carlos Steel",
            extra={
                "key_work": "Proclus De Providentia, Fato et eo quod in nobis (Tria Opuscula III)",
                "interlocutor_ancient": "Theodore the engineer",
                "later_reception": "Boethius Consolatio V, Latin Scholasticism",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will",
        type="argument",
        label="Wildberg 2014 — Simplicius's Neoplatonist reading of Epictetan prohairesis (not yet free will)",
        description=(
            "Argument scholarly de Wildberg (Destrée 2014 ch. 21) : "
            "deux thèses. (1) Épictète n'a *pas* l'articulation moderne "
            "du libre arbitre : la *prohaïrèsis* épictétéenne est une "
            "instance particulière de *choix moral comme engagement "
            "rationnel*, et reste déterminée par des considérations "
            "bien-formées chez le sage. Elle est libre seulement de "
            "l'influence disruptive des impressions externes — non "
            "libre au sens absolu (contre Frede 2011, Dihle 1982). (2) "
            "Simplicius lit Épictète à travers la grille "
            "néoplatonicienne (autexousion comme fondement "
            "métaphysique), produisant à la fois un traité théorique "
            "d'éthique et une démonstration pratique de la réponse "
            "philosophique à l'adversité — dans le contexte historique "
            "de l'exil sassanide post-529 CE (fermeture de l'Académie "
            "par Justinien)"
        ),
        description_en=(
            "Scholarly argument by Wildberg: two theses. (1) Epictetus "
            "lacks the modern articulation of free will: Epictetan "
            "prohairesis is a particular instance of moral choice as "
            "rational commitment, determined by well-formed "
            "considerations for the sage. Free only of disruptive "
            "external impressions, not free in absolute sense (against "
            "Frede 2011, Dihle 1982). (2) Simplicius reads Epictetus "
            "via Neoplatonist grid (autexousion as metaphysical "
            "foundation), producing both theoretical ethics treatise "
            "and practical demonstration of philosophical response to "
            "adversity — in post-529 CE Sasanian exile context"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 21",
            pages="p. 329-350",
            author="Christian Wildberg",
            extra={
                "rivals_engaged": ["Frede 2011 A Free Will (esp. ch. on Epictetus)", "Dihle 1982 Theory of Will"],
                "key_works": ["Epictetus Enchiridion", "Simplicius In Epicteti Enchiridion (CAG)"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_frede_michael_2014_eph_hemin_emerges_with_alexander_epictetus_christianity",
        type="argument",
        label="Frede M. 2014 — Eph' hêmin acquires free-will resonance only with Alexander/Epictetus/Christians (Justin, Tatian)",
        description=(
            "Argument scholarly central de Michael Frede (Destrée 2014 "
            "ch. 22 ; original 2007, posthume) : quatre thèses "
            "fondamentales sur l'histoire conceptuelle du τὸ ἐφ' ἡμῖν. "
            "(1) Chez Aristote, ἐφ' ἡμῖν signifie *ce qui est en notre "
            "pouvoir* au sens où ce n'est pas pure fonction de notre "
            "nature ; l'usage *n'implique pas* la liberté "
            "indéterministe. (2) Chez les premiers stoïciens, les "
            "actions sont ἐφ' ἡμῖν *en tant qu'elles dépendent de "
            "l'assentiment* (sunkatathesis), *sans* impliquer que l'on "
            "aurait pu faire autrement dans les mêmes circonstances. "
            "(3) Les stoïciens tardifs (Épictète) raffinent : c'est "
            "l'assentiment, non l'action, qui est ἐφ' ἡμῖν — et "
            "*cela* se rapproche du libre arbitre. (4) Justin Martyr "
            "et Tatien lisent cet ἐφ' ἡμῖν épictétéen comme "
            "incompatible avec le destin stoïcien (intégration "
            "chrétienne). Alexandre d'Aphrodise relit cette conception "
            "*libre-arbitriste* dans Aristote (rétro-projection). "
            "Article-charnière fondateur de la thèse "
            "Bobzien-Frede sur l'émergence tardive du libre arbitre"
        ),
        description_en=(
            "Scholarly central argument by Michael Frede (Destrée 2014 "
            "ch. 22; original 2007, posthumous): four foundational "
            "theses on the conceptual history of to eph' hêmin. (1) In "
            "Aristotle, eph' hêmin means in our power as not function "
            "of our nature; does NOT imply indeterminist freedom. (2) "
            "For early Stoics, actions are eph' hêmin insofar as they "
            "depend on assent (sunkatathesis), NOT implying "
            "could-have-done-otherwise. (3) Later Stoics (Epictetus) "
            "refine: it's assent, not action, that is eph' hêmin — "
            "approximating free will. (4) Justin Martyr and Tatian "
            "read this Epictetan eph' hêmin as incompatible with Stoic "
            "fate (Christian integration). Alexander reads "
            "free-will-resonance back into Aristotle "
            "(retroprojection). Foundational paper of the Bobzien-Frede "
            "thesis on the late emergence of free will"
        ),
        period="Contemporary",
        metadata=destree_metadata(
            chapter="Ch. 22",
            pages="p. 351-363",
            author="Michael Frede (posthumous; ed. Sauvé Meyer)",
            extra={
                "original_publication_year": 2007,
                "original_venue": "Greek philosophical journal (preserved via Ierodiakonou)",
                "thesis_pivotal_for": "Bobzien-Frede line on late emergence of free will",
                "key_authors_discussed": ["Aristotle", "early Stoics", "Epictetus", "Justin Martyr", "Tatian", "Alexander of Aphrodisias"],
            },
        ),
        confidence=0.99,
    ),
]
