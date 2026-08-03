"""Frede 2011 B1 — NEW_INSERTS list (new nodes).

Bilingual FR/EN descriptions. Standard structure :
  - PERSONS    : 1 (Michael Frede himself, as a scholar)
  - WORKS      : 0 (none — book is a publication, captured below)
  - PUBLICATIONS : 1 (pub_frede_2011_free_will)
  - SYNTHESES  : 11 (one per chapter, including Conclusion)
  - ARGUMENTS  : 14 (Frede's main scholarly theses)
  - CONCEPTS   : 2 (Frede-specific analytical categories)

Note: in the existing graph publications are `type: publication`. Frede's
scholarly arguments use `type: argument` to align with the existing
`scholarly_argument_bobzien_*` and `scholar_position_frede_*` patterns.
"""
from __future__ import annotations

from typing import Any

from frede_2011_b1_utils import (
    FREDE_PUBLICATION_ID,
    FREDE_SCHOLAR_ID,
    dump_metadata,
    frede_metadata,
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
# PERSONS — Michael Frede as a scholar
# =============================================================================

NEW_PERSONS: list[dict[str, Any]] = [
    _node(
        id=FREDE_SCHOLAR_ID,
        type="person",
        label="Michael Frede",
        description=(
            "Michael Frede (Berlin, 31 mai 1940 — Skala Eressou, Lesbos, 11 "
            "août 2007), historien allemand de la philosophie ancienne formé "
            "à Hambourg et Göttingen (PhD 1966, Prädikation und "
            "Existenzaussage). Successivement professeur à Göttingen (1966-71), "
            "Berkeley (1971-76), Princeton (1976-91), Oxford (Keble College, "
            "Chaire de philosophie ancienne, 1991-2005) et Athènes (2005-07). "
            "Œuvres majeures : monographie sur Plato's Sophist (1967), Die "
            "stoische Logik (1974), commentaire (avec Günther Patzig) de "
            "Métaphysique Zeta d'Aristote (1988), traduction (avec Richard "
            "Walzer) de Trois traités de Galien sur la nature de la science, "
            "Essays in Ancient Philosophy (1987). A Free Will (2011) est "
            "l'édition posthume par A. A. Long de ses Sather Lectures de "
            "1997-98, restées inédites du vivant de Frede. Frede meurt par "
            "noyade en mer Égée en 2007. Pour Sedley (Foreword, p. vii-x), "
            "ce volume 'crowns' un corpus dont 'few thinkers or topics' de "
            "la philosophie gréco-romaine 'have not been enriched by Frede's "
            "publications'"
        ),
        description_en=(
            "Michael Frede (Berlin, 31 May 1940 — Skala Eressou, Lesbos, 11 "
            "August 2007), German historian of ancient philosophy trained at "
            "Hamburg and Göttingen (PhD 1966, Prädikation und Existenzaussage). "
            "Successively professor at Göttingen (1966-71), Berkeley (1971-"
            "76), Princeton (1976-91), Oxford (Keble College, Chair of "
            "Ancient Philosophy, 1991-2005), and Athens (2005-07). Major "
            "works: monograph on Plato's Sophist (1967), Die stoische Logik "
            "(1974), commentary (with Günther Patzig) on Aristotle's "
            "Metaphysics Zeta (1988), translation (with Richard Walzer) of "
            "Galen's Three Treatises on the Nature of Science, Essays in "
            "Ancient Philosophy (1987). A Free Will (2011) is A. A. Long's "
            "posthumous edition of his 1997-98 Sather Lectures, unpublished "
            "in Frede's lifetime. He died by drowning in the Aegean in 2007. "
            "For Sedley (Foreword, p. vii-x), this volume 'crowns' a corpus "
            "in which 'few thinkers or topics' of Greco-Roman philosophy "
            "'have not been enriched by Frede's publications'"
        ),
        period="Modern",
        metadata={
            "role": "scholar",
            "specialty": "ancient philosophy, Stoicism, Aristotle, Galen, Plato's Sophist, history of the notion of free will",
            "birth_date": "1940 CE",
            "death_date": "2007 CE",
            "surname": "Frede",
            "given_names": "Michael",
            "affiliations": [
                "Universität Göttingen (1966-71)",
                "UC Berkeley (1971-76)",
                "Princeton University (1976-91)",
                "University of Oxford, Keble College (1991-2005, Chair of Ancient Philosophy)",
                "University of Athens (2005-07)",
            ],
            "major_works": [
                "Prädikation und Existenzaussage (Göttingen, 1967)",
                "Die stoische Logik (Göttingen, 1974)",
                "Aristotle's Metaphysics Lambda (with G. Patzig, Munich, 1988)",
                "Essays in Ancient Philosophy (Minneapolis, 1987)",
                "Three Treatises on the Nature of Science by Galen (with R. Walzer, Indianapolis, 1985)",
                "A Free Will: Origins of the Notion in Ancient Thought (Berkeley, 2011, posthumous)",
            ],
            "claimed_by": FREDE_SCHOLAR_ID,
            "bibtex_key": "frede-2011-free-will-origins-notion-ancient-thought",
        },
        confidence=0.95,
    ),
]


# =============================================================================
# PUBLICATIONS — 1
# =============================================================================

NEW_PUBLICATIONS: list[dict[str, Any]] = [
    _node(
        id=FREDE_PUBLICATION_ID,
        type="publication",
        label="Frede 2011 — A Free Will: Origins of the Notion in Ancient Thought",
        description=(
            "Michael Frede, A Free Will: Origins of the Notion in Ancient "
            "Thought, édité par A. A. Long, avec une préface (foreword) de "
            "David Sedley, Sather Classical Lectures vol. 68, Berkeley / Los "
            "Angeles / London : University of California Press, 2011, xiv + "
            "206 p. ISBN 978-0-520-26848-7. Édition posthume : Frede a "
            "donné les six Sather Lectures à Berkeley au semestre d'automne "
            "1997-98 mais ne les jugea jamais prêtes pour publication ; il "
            "meurt en 2007, le tapuscrit fut édité par son ami A. A. Long. "
            "Sedley parle dans son foreword d'un 'crowning' du corpus de "
            "Frede.\n\n"
            "Thèse centrale : la notion de libre arbitre est une notion "
            "philosophique technique, à l'origine historique identifiable, "
            "et non un trait pré-théorique de l'expérience humaine. Frede "
            "soutient contre Albrecht Dihle (1982 The Theory of Will in "
            "Classical Antiquity, Sather Lectures vol. 48) qu'Augustin "
            "n'invente pas 'notre notion moderne du vouloir' : la notion "
            "émerge dans le stoïcisme tardif avec Épictète (fin Ier - début "
            "IIe s.), à partir de l'enrichissement de la théorie classique "
            "de l'assentiment (synkatathesis) par une analyse développée de "
            "la vie intérieure. Augustin hérite, via Origène, d'une notion "
            "fondamentalement stoïcienne, qu'il radicalise en suivant Paul "
            "sur l'esclavage du vouloir déchu. Frede consacre toute la fin "
            "du livre à démontrer que les particularités d'Augustin "
            "(grâce, prédestination, esclavage du vouloir) ne sont pas dues "
            "à un voluntarisme christiano-innovant mais au contraire à une "
            "fidélité stricte au stoïcisme là où Origène s'en éloignait par "
            "platonisme. Cette thèse est en tension forte avec Susanne "
            "Bobzien (Determinism and Freedom in Stoic Philosophy, 1998 ; "
            "'The Inadvertent Conception and Late Birth of the Free-Will "
            "Problem', 1998a) — Frede localise la naissance plus tôt et "
            "comme acte intellectuel délibéré.\n\n"
            "Structure : 10 chapitres. (1) Introduction — la notion de "
            "libre arbitre est technique et historiquement datable ; (2) "
            "Aristote — choix sans volonté ; (3) Émergence de la volonté en "
            "stoïcisme ; (4) Contributions platoniciennes et péripatéticiennes "
            "tardives ; (5) Émergence du libre arbitre en stoïcisme (= "
            "Épictète) ; (6) Critiques platoniciennes et péripatéticiennes "
            "(= Alexandre d'Aphrodise) ; (7) Une vision chrétienne précoce "
            "du libre arbitre : Origène ; (8) Réactions à la notion stoïcienne "
            "de libre arbitre : Plotin ; (9) Augustin : une notion "
            "radicalement nouvelle ? ; (10) Conclusion"
        ),
        description_en=(
            "Michael Frede, A Free Will: Origins of the Notion in Ancient "
            "Thought, edited by A. A. Long, with a foreword by David Sedley. "
            "Sather Classical Lectures vol. 68. Berkeley / Los Angeles / "
            "London: University of California Press, 2011. xiv + 206 pp. "
            "ISBN 978-0-520-26848-7. Posthumous edition: Frede delivered the "
            "six Sather Lectures at Berkeley in the Fall semester of 1997-98 "
            "but never judged them ready for publication; he died in 2007 "
            "and the typescript was edited by his friend A. A. Long. Sedley's "
            "foreword characterizes the volume as 'crowning' Frede's corpus.\n\n"
            "Central thesis: the notion of a free will is a technical "
            "philosophical concept with an identifiable historical origin, "
            "not a pre-theoretical given. Frede argues against Albrecht "
            "Dihle (1982 The Theory of Will in Classical Antiquity, Sather "
            "vol. 48) that Augustine did NOT invent 'our modern notion of "
            "will': the notion emerges in late Stoicism with Epictetus "
            "(late 1st - early 2nd c. CE), through the enrichment of the "
            "classical Stoic theory of assent (synkatathesis) with a "
            "developed account of the inner life. Augustine inherits, via "
            "Origen, a basically Stoic notion that he radicalizes by "
            "following Paul on the enslavement of the fallen will. Frede "
            "devotes the entire end of the book to demonstrating that "
            "Augustine's particular features (grace, predestination, "
            "enslaved will) are not due to Christian voluntarist innovation "
            "but, on the contrary, to closer Stoic fidelity than Origen "
            "(whose differences from Stoicism stem from his Platonism). "
            "This thesis stands in tension with Susanne Bobzien "
            "(Determinism and Freedom in Stoic Philosophy, 1998; 'The "
            "Inadvertent Conception and Late Birth of the Free-Will "
            "Problem', 1998a) — Frede locates the birth earlier and as a "
            "deliberate intellectual achievement.\n\n"
            "Structure: 10 chapters. (1) Introduction — the notion of free "
            "will is technical and historically datable; (2) Aristotle — "
            "choice without a will; (3) Emergence of a notion of will in "
            "Stoicism; (4) Later Platonist and Peripatetic contributions; "
            "(5) Emergence of a notion of a free will in Stoicism "
            "(= Epictetus); (6) Platonist and Peripatetic criticisms and "
            "responses (= Alexander of Aphrodisias); (7) An early Christian "
            "view on a free will: Origen; (8) Reactions to the Stoic notion "
            "of a free will: Plotinus; (9) Augustine — a radically new "
            "notion of a free will?; (10) Conclusion"
        ),
        period="Modern",
        metadata={
            "author": "Michael Frede",
            "author_id": FREDE_SCHOLAR_ID,
            "editor": "A. A. Long",
            "editor_id": "scholar_long_anthony",
            "foreword_author": "David Sedley",
            "foreword_author_id": "scholar_sedley_david",
            "publication_year": 2011,
            "posthumous": True,
            "frede_died": "2007",
            "lectures_delivered": "1997-98 (Fall semester, UC Berkeley)",
            "publisher": "University of California Press",
            "publisher_city": "Berkeley / Los Angeles / London",
            "series": "Sather Classical Lectures",
            "series_volume": 68,
            "isbn": "978-0-520-26848-7",
            "lccn": "2010020858",
            "dewey": "123'.5093",
            "lc_classification": "B187.F7F74 2011",
            "pages": "xiv + 206",
            "languages": ["en"],
            "bibtex_key": "frede-2011-free-will-origins-notion-ancient-thought",
            "chapter_count": 10,
            "chapter_titles": [
                "1. Introduction",
                "2. Aristotle on Choice without a Will",
                "3. The Emergence of a Notion of Will in Stoicism",
                "4. Later Platonist and Peripatetic Contributions",
                "5. The Emergence of a Notion of a Free Will in Stoicism",
                "6. Platonist and Peripatetic Criticisms and Responses",
                "7. An Early Christian View on a Free Will: Origen",
                "8. Reactions to the Stoic Notion of a Free Will: Plotinus",
                "9. Augustine: A Radically New Notion of a Free Will?",
                "10. Conclusion",
            ],
            "primary_interlocutor": "Albrecht Dihle (1982)",
            "secondary_interlocutor": "Susanne Bobzien (1998)",
            "central_thesis": (
                "The notion of a free will is a technical philosophical "
                "concept that first emerges in late Stoicism with Epictetus, "
                "is inherited rather than invented by Christianity, and "
                "passes through Origen to Augustine without becoming "
                "voluntarist."
            ),
        },
        confidence=0.98,
    ),
]


# =============================================================================
# CONCEPTS — Frede-specific analytical categories
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    _node(
        id="concept_frede_general_schema_of_free_will",
        type="concept",
        label="Schéma général d'une notion de libre arbitre (Frede 2011)",
        description=(
            "Construction analytique de Frede 2011 (Ch. 1, p. 7-18) : tout "
            "concept antique de libre arbitre articule trois composantes "
            "que Frede distingue formellement. (1) Une notion de volonté = "
            "l'habileté à faire des choix ou des décisions qui causent nos "
            "actions, capacité différenciée selon les individus, susceptible "
            "d'être cultivée et perfectionnée. (2) Une notion de liberté = "
            "calquée par analogie sur la liberté politique (eleutheria : "
            "citoyen vs esclave) ; absence de contraintes externes "
            "(astrales, démoniques, gnostiques, fatalistes, providentielles) "
            "qui empêcheraient systématiquement de mener une vie bonne. (3) "
            "Une combinaison spécifique des deux : la volonté doit être "
            "libre dans le sens que rien ne peut la forcer à faire un autre "
            "choix que celui qu'elle veut faire. Frede insiste : il abstrait "
            "ce schéma a posteriori des textes anciens explicites, sans "
            "imposer une définition philosophique a priori. Le schéma "
            "fonctionne comme test : Aristote a la liberté politique mais "
            "pas la notion de volonté ; le stoïcisme classique a la volonté "
            "mais pas encore la liberté en ce sens technique ; Épictète a "
            "les deux"
        ),
        description_en=(
            "Frede 2011's analytical construction (Ch. 1, p. 7-18): every "
            "ancient concept of a free will articulates three components "
            "Frede formally distinguishes. (1) A notion of a will = the "
            "ability to make choices or decisions that cause our actions, "
            "an ability differentiated among individuals, capable of being "
            "cultivated and perfected. (2) A notion of freedom = patterned "
            "by analogy on political freedom (eleutheria: citizen vs slave); "
            "absence of external constraints (astral, demonic, Gnostic, "
            "fatalist, providential) that would systematically prevent "
            "living a good life. (3) A specific combination: the will must "
            "be free in the sense that nothing can force it to make any "
            "choice other than the one it wants to make. Frede insists this "
            "schema is abstracted a posteriori from explicit ancient texts, "
            "not imposed as an a priori philosophical definition. The "
            "schema functions as a test: Aristotle has political freedom "
            "but no notion of a will; classical Stoicism has the will but "
            "not yet freedom in this technical sense; Epictetus has both"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 5-18",
            chapter="Ch. 1 Introduction",
            chapter_actual="Frede's general schema (will + freedom + their combination) for testing ancient candidates",
            extra={
                "frede_2011_role": "analytical_template_for_whole_book",
                "frede_components": ["notion_of_will", "notion_of_freedom", "combination_into_free_will"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="concept_frede_inner_life_late_stoic",
        type="concept",
        label="Vie intérieure stoïcienne tardive comme condition d'une volonté libre (Frede 2011)",
        description=(
            "Catégorie analytique de Frede 2011 (Ch. 5 §1, p. 75-79 et Ch. "
            "3, p. 44-48) : 'enrichissement, dans le stoïcisme tardif, de "
            "la théorie classique de l'assentiment par une notion développée "
            "de vie intérieure'. C'est précisément ce supplément qui "
            "transforme le synkatathesis classique (Chrysippe) en une "
            "véritable volonté chez Épictète. Trois traits : (a) "
            "intériorisation systématique — l'eph' hēmin se rétrécit de "
            "l'action externe (traverser la rue) à l'assentiment intérieur "
            "à l'impression de la traverser ; (b) askēsis et "
            "auto-surveillance — l'application de la théorie à sa propre "
            "vie demande pratique et attention permanente ; (c) la "
            "prohairesis devient le 'soi' (Diss. 1.29.1 : 'c'est ce qui te "
            "définit comme personne'). Ce supplément n'est pas dans "
            "Chrysippe ni dans Sénèque. Pour Frede, Augustin hérite cette "
            "même vie intérieure via Origène (Ch. 9 p. 158-159 : la "
            "volonté augustinienne 'is just the Stoic notion of the will')"
        ),
        description_en=(
            "Frede 2011's analytical category (Ch. 5 §1, p. 75-79 and Ch. 3, "
            "p. 44-48): 'enrichment, in late Stoicism, of the classical "
            "theory of assent with a developed notion of an inner life'. "
            "It is precisely this supplement that transforms classical "
            "synkatathesis (Chrysippus) into a genuine will in Epictetus. "
            "Three features: (a) systematic interiorization — eph' hēmin "
            "narrows from external action (crossing the street) to internal "
            "assent to the impression of crossing it; (b) askēsis and "
            "self-surveillance — applying the theory to one's life requires "
            "constant practice and attention; (c) prohairesis becomes the "
            "'self' (Diss. 1.29.1 : 'this is what defines you as a "
            "person'). This supplement is not in Chrysippus nor in Seneca. "
            "For Frede, Augustine inherits this same inner life via Origen "
            "(Ch. 9 p. 158-159: the Augustinian will 'is just the Stoic "
            "notion of the will')"
        ),
        period="Roman Imperial",
        metadata=frede_metadata(
            page_range="p. 44-48, 75-79, 158-159",
            chapter="Ch. 3 §3 + Ch. 5 §1 + Ch. 9 §1",
            chapter_actual="The inner-life supplement that makes prohairesis a will in Epictetus and persists in Origen/Augustine",
            extra={
                "frede_2011_role": "missing_ingredient_for_first_free_will",
                "frede_components": ["interiorization_of_eph_hemin", "askēsis", "prohairesis_as_self"],
            },
        ),
        confidence=0.95,
    ),
]


# =============================================================================
# SYNTHESES — 11 (one per chapter; Ch. 1 + 9 substantive + Conclusion)
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    _node(
        id="synthesis_frede2011_ch1_introduction",
        type="synthesis",
        label="Ch. 1 Introduction — la notion de libre arbitre est technique et datable (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 1 (p. 1-18) : la notion de libre arbitre "
            "n'est pas une croyance ordinaire que les Grecs auraient toujours "
            "eue (contre Ross 1923 sur Aristote et 'the plain man's belief'), "
            "mais une notion philosophique technique avec une origine "
            "historique identifiable. Frede pose son désaccord central avec "
            "Dihle 1982 : il refuse de partir d'une 'notre notion moderne du "
            "vouloir' présumée universelle ; il construit a posteriori, à "
            "partir des textes anciens explicites, un schéma à trois "
            "composantes (volonté + liberté + leur combinaison) qui servira "
            "de test pour le reste du livre. Le contexte de l'émergence "
            "est précisé : peurs largement diffusées dans l'Antiquité tardive "
            "(archontes planétaires, démiurge gnostique, déterminisme stoïcien, "
            "déterminisme astral) qui rendent significatif d'affirmer que la "
            "volonté humaine n'est pas systématiquement contrainte"
        ),
        description_en=(
            "Frede 2011 Ch. 1 synthesis (p. 1-18): the notion of a free will "
            "is not an ordinary belief Greeks have always had (against Ross "
            "1923 on Aristotle and 'the plain man's belief'), but a "
            "technical philosophical concept with an identifiable historical "
            "origin. Frede states his central disagreement with Dihle 1982: "
            "he refuses to start from a presumed-universal 'our modern "
            "notion of will'; he constructs a posteriori, from explicit "
            "ancient texts, a three-component schema (will + freedom + "
            "their combination) that will function as a test for the rest "
            "of the book. The emergence context is specified: widespread "
            "late-antique fears (planetary archontes, Gnostic demiurge, "
            "Stoic determinism, astral determinism) make it significant to "
            "affirm that the human will is not systematically constrained"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 1-18",
            chapter="Ch. 1 Introduction",
            chapter_actual="Establishing the technical-historical-datable status of the notion of a free will against Ross/Dihle",
            extra={"frede_2011_role": "framing_thesis_and_methodology"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_frede2011_ch2_aristotle",
        type="synthesis",
        label="Ch. 2 — Aristote a un choix sans volonté (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 2 (p. 19-29) : Aristote n'a ni notion "
            "de volonté ni notion de libre arbitre. Il a (a) boulēsis = "
            "désir-de-raison spécifique à l'âme rationnelle, (b) prohairesis "
            "= forme spéciale de boulēsis restreinte à ce qui est eph' "
            "hēmin, et (c) le couple hekōn / akōn distinguant les actions "
            "responsables des actions forcées ou ignorantes. Mais aucune de "
            "ces trois constructions n'est une volonté au sens technique : "
            "(1) le désir de raison est fonction directe de l'état "
            "cognitif (voir le bien, c'est le vouloir) ; (2) l'akratique "
            "agit CONTRE sa prohairesis, non par choix contraire, mais par "
            "défaut antérieur d'habituation ; (3) hekōn / akōn s'applique "
            "même aux enfants et aux animaux et signifie 'de son propre "
            "gré', non 'volontaire' dans le sens voluntariste post-cicéronien"
        ),
        description_en=(
            "Frede 2011 Ch. 2 synthesis (p. 19-29): Aristotle has neither a "
            "notion of a will nor a notion of free will. He has (a) "
            "boulēsis = the desire-of-reason specific to the rational soul, "
            "(b) prohairesis = a special form of boulēsis restricted to "
            "what is eph' hēmin, and (c) the hekōn / akōn pair "
            "distinguishing responsible from forced/ignorant actions. But "
            "none of these three constructions is a will in the technical "
            "sense: (1) desire of reason is a direct function of cognitive "
            "state (seeing the good is wanting it); (2) the akratic acts "
            "AGAINST his prohairesis, not by contrary choice but by past "
            "failures of habituation; (3) hekōn / akōn applies even to "
            "children and animals and means 'of one's own accord', not "
            "'voluntary' in the post-Ciceronian voluntarist sense"
        ),
        period="Classical Greek",
        metadata=frede_metadata(
            page_range="p. 19-29",
            chapter="Ch. 2 Aristotle on Choice without a Will",
            chapter_actual="Aristotle has prohairesis, boulēsis, hekousion — but not a will or free will",
            extra={"frede_2011_role": "no_will_no_free_will_in_aristotle"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_frede2011_ch3_emergence_of_will_in_stoicism",
        type="synthesis",
        label="Ch. 3 — Émergence d'une notion de volonté dans le stoïcisme classique (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 3 (p. 31-48) : le stoïcisme construit "
            "la première notion authentique de volonté, mais pas encore de "
            "libre arbitre. Architecture conceptuelle : (a) rejet de "
            "l'âme bi- ou tripartite platonico-aristotélicienne au profit "
            "d'une âme unipartite = raison = hēgemonikon ; (b) toute action "
            "non-forcée présuppose un assentiment (synkatathesis) de la "
            "raison à une impression impulsive (phantasia hormētikē) ; (c) "
            "tout désir mûr est donc rationnel — il n'y a pas de désirs "
            "non-rationnels survivant à la métamorphose de l'âme infantile "
            "en âme adulte (acquisition de la raison). Chrysippe garantit la "
            "responsabilité par sa logique modale : aucune impression ne "
            "nécessite l'assentiment. Mais c'est seulement Épictète qui "
            "rassemble ces matériaux en une volonté véritable, en plaçant "
            "la prohairesis au centre"
        ),
        description_en=(
            "Frede 2011 Ch. 3 synthesis (p. 31-48): Stoicism constructs the "
            "first authentic notion of a will but not yet of a free will. "
            "Conceptual architecture: (a) rejection of the Platonic-"
            "Aristotelian bi-/tripartite soul in favor of a unipartite soul "
            "= reason = hēgemonikon; (b) any non-forced action presupposes "
            "an assent (synkatathesis) by reason to an impulsive impression "
            "(phantasia hormētikē); (c) every mature desire is therefore "
            "rational — there are no non-rational desires surviving the "
            "metamorphosis of the infantile soul into the adult soul "
            "(acquisition of reason). Chrysippus secures responsibility "
            "via modal logic: no impression necessitates assent. But only "
            "Epictetus will gather these materials into a genuine will, by "
            "centering prohairesis"
        ),
        period="Hellenistic",
        metadata=frede_metadata(
            page_range="p. 31-48",
            chapter="Ch. 3 The Emergence of a Notion of Will in Stoicism",
            chapter_actual="Stoic unipartite soul + synkatathesis + Chrysippean modal logic = materials of will, no freedom yet",
            extra={"frede_2011_role": "stoic_proto_will_classical_phase"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_frede2011_ch4_later_platonist_peripatetic_contributions",
        type="synthesis",
        label="Ch. 4 — Contributions platoniciennes et péripatéticiennes tardives (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 4 (p. 49-65) : entre Carnéade et "
            "Plotin, platoniciens (Numénius, Calcidius, Porphyre, Plotin) "
            "et péripatéticiens (Aspasius, Alexandre) adoptent le couple "
            "stoïcien impression-assentiment, tout en le combinant avec une "
            "âme bi- ou tripartite. Effet : on isole la propatheia "
            "(passion-incipiente, terme inventé par Philon d'Alexandrie selon "
            "Graver 1999, repris par Origène) et on développe une notion "
            "d'impression non-rationnelle issue de la partie non-rationnelle "
            "de l'âme à laquelle la raison peut donner ou refuser son "
            "assentiment. Frede analyse ensuite le rôle des logismoi chez "
            "Évagre Pontique, le contexte démonologique massif "
            "(Albicerius dans Contra Academicos I.17 d'Augustin) qui sert "
            "d'arrière-plan à la généralisation de la notion de tentation "
            "en Antiquité tardive"
        ),
        description_en=(
            "Frede 2011 Ch. 4 synthesis (p. 49-65): between Carneades and "
            "Plotinus, Platonists (Numenius, Calcidius, Porphyry, Plotinus) "
            "and Peripatetics (Aspasius, Alexander) adopt the Stoic "
            "impression-assent pair while combining it with a bi-/tripartite "
            "soul. Result: propatheia (incipient passion, term coined by "
            "Philo of Alexandria per Graver 1999, then Origen) is isolated, "
            "and a notion is developed of non-rational impressions arising "
            "from the non-rational soul-part to which reason can give or "
            "withhold assent. Frede then analyzes the role of logismoi in "
            "Evagrius Ponticus, and the massive demonological backdrop "
            "(Albicerius in Augustine's Contra Academicos I.17) that "
            "underwrites the late-antique generalization of 'temptation'"
        ),
        period="Roman Imperial",
        metadata=frede_metadata(
            page_range="p. 49-65",
            chapter="Ch. 4 Later Platonist and Peripatetic Contributions",
            chapter_actual="Platonist/Peripatetic uptake of Stoic assent within bi/tripartite psychology; propatheia, logismoi, demonological context",
            extra={"frede_2011_role": "syncretist_reception_of_stoic_assent"},
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_frede2011_ch5_emergence_of_free_will_in_stoicism",
        type="synthesis",
        label="Ch. 5 — Émergence du libre arbitre chez Épictète (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 5 (p. 66-88) : Épictète articule pour "
            "la première fois la notion de libre arbitre. Le mécanisme : "
            "(1) reprise de la définition stoïcienne classique de la "
            "liberté comme exousia autopragias (DL 7.121 = LS 67M, "
            "vraisemblablement chrysippéenne) — 'capacité d'agir de soi-même' "
            "par délégation légale (exousia) du droit divin (Origène Comm. "
            "in Ioan. I.4 et II.16) ; (2) introduction du terme autexousion, "
            "qui apparaît deux fois chez Musonius puis fréquemment chez "
            "Épictète, et 'à partir de Justin Martyr très fréquemment chez "
            "les auteurs chrétiens' ; (3) rétrécissement décisif de eph' "
            "hēmin : non plus l'action externe (traverser la rue) mais "
            "l'assentiment à l'impression de la traverser ; (4) "
            "déclaration explicite (Diss. 1.1.23 ; 1.4.18 ; 3.5.7) qu'aucune "
            "force au monde, pas même Dieu, ne peut forcer ce choix tant "
            "que la volonté reste libre. Seul le sage a effectivement un "
            "libre arbitre ; les autres se sont asservis aux 'biens' "
            "extérieurs. Frede consacre la fin du chapitre à montrer que "
            "cette notion est compatible avec le déterminisme providentiel "
            "stoïcien : l'action libre du sage n'est pas motivée par 'Dieu "
            "veut x' mais par 'x est l'action correcte', et le plan divin "
            "coïncide avec cette action correcte"
        ),
        description_en=(
            "Frede 2011 Ch. 5 synthesis (p. 66-88): Epictetus articulates "
            "for the first time the notion of a free will. The mechanism: "
            "(1) reprise of the classical Stoic definition of freedom as "
            "exousia autopragias (DL 7.121 = LS 67M, probably Chrysippean) "
            "— 'authority to act on one's own' by legal delegation (exousia) "
            "of divine right (Origen Comm. in Ioan. I.4 and II.16); (2) "
            "introduction of the term autexousion, twice in Musonius then "
            "frequently in Epictetus, and 'from Justin Martyr onwards very "
            "frequently among Christian authors'; (3) decisive narrowing of "
            "eph' hēmin: no longer external action (crossing the street) but "
            "assent to the impression of crossing it; (4) explicit "
            "declaration (Diss. 1.1.23; 1.4.18; 3.5.7) that no power in the "
            "world, not even God, can force this choice as long as the will "
            "remains free. Only the wise person actually has a free will; "
            "the rest have enslaved themselves to external 'goods'. Frede "
            "devotes the end of the chapter to showing this is compatible "
            "with Stoic providential determinism: the wise person's free "
            "action is motivated not by 'God wills x' but by 'x is the "
            "right thing', and the divine plan coincides with this"
        ),
        period="Roman Imperial",
        metadata=frede_metadata(
            page_range="p. 66-88",
            chapter="Ch. 5 The Emergence of a Notion of a Free Will in Stoicism",
            chapter_actual="Epictetus's invention via autexousion + narrowed eph' hēmin + cannot-be-forced clause",
            extra={"frede_2011_role": "first_actual_notion_of_a_free_will_thesis"},
        ),
        confidence=0.98,
    ),
    _node(
        id="synthesis_frede2011_ch6_platonist_peripatetic_criticisms",
        type="synthesis",
        label="Ch. 6 — Alexandre d'Aphrodise et la dérive libertarienne (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 6 (p. 89-101) : Platoniciens et "
            "Péripatéticiens reçoivent la notion stoïcienne, l'acceptent en "
            "partie, mais refusent le déterminisme providentiel qui "
            "l'accompagne. La trajectoire : Carnéade (Cicéron De fato XI.23-"
            "25) distingue assentiment forcé et assentiment d'origine "
            "interne (motus voluntarii), rétrécissant l'hekousion ; "
            "Alexandre d'Aphrodise hérite ce critère et l'identifie à "
            "l'autexousion stoïcien tout en refusant la fatalité stoïcienne. "
            "Mais Alexandre, voulant inscrire dans la notion de libre arbitre "
            "la possibilité de choisir autrement dans des circonstances "
            "internes-et-externes identiques (De fato 192, 22ff), se "
            "retrouve dans un 'inextricable tangle' : sa propre référence à "
            "Aristote (le vertueux ne peut faire autrement) entre en "
            "contradiction avec sa thèse libertarienne. Frede conclut "
            "(p. 100, et Conclusion p. 177-178) : Alexandre 'is the only "
            "major ancient philosopher' dont la conception est "
            "fondamentalement viciée, et 'in Alexander that we find the "
            "ancestor of the notion' modern voluntariste critiquée par Ryle, "
            "Williams et Frede"
        ),
        description_en=(
            "Frede 2011 Ch. 6 synthesis (p. 89-101): Platonists and "
            "Peripatetics receive the Stoic notion, partly accept it, but "
            "refuse the providential determinism that accompanies it. The "
            "trajectory: Carneades (Cicero De fato XI.23-25) distinguishes "
            "forced assent from internally-originating assent (motus "
            "voluntarii), narrowing hekousion; Alexander of Aphrodisias "
            "inherits this criterion and identifies it with Stoic "
            "autexousion while refusing Stoic fate. But Alexander, in "
            "trying to write into free will the could-have-chosen-otherwise-"
            "in-identical-circumstances clause (De fato 192, 22ff), gets "
            "into a 'hopeless tangle': his own reference to Aristotle (the "
            "virtuous cannot choose otherwise) contradicts his libertarian "
            "thesis. Frede concludes (p. 100, and Conclusion p. 177-178): "
            "Alexander 'is the only major ancient philosopher' whose "
            "conception is basically flawed, and 'it is in Alexander that "
            "we find the ancestor of the notion' of free will criticized "
            "by Ryle, Williams, and Frede"
        ),
        period="Roman Imperial",
        metadata=frede_metadata(
            page_range="p. 89-101",
            chapter="Ch. 6 Platonist and Peripatetic Criticisms and Responses",
            chapter_actual="Carneades-Alexander narrowing of eph' hēmin + Alexander's flawed libertarian could-have-chosen-otherwise notion",
            extra={"frede_2011_role": "alexander_libertarian_dead_end"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_frede2011_ch7_origen",
        type="synthesis",
        label="Ch. 7 — Origène et la première systématisation chrétienne du libre arbitre (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 7 (p. 102-124) : Origène est le premier "
            "auteur chrétien à écrire systématiquement sur le libre arbitre, "
            "dans un petit traité Peri autexousiou inséré au De principiis "
            "III.1 (préservé en grec par les Philocalia ch. 21-27 de "
            "Basile et Grégoire de Nazianze). Trois résultats principaux "
            "selon Frede : (1) le traité 'could have been taken straight "
            "from a late Stoic handbook' — terminologie et thèses "
            "majoritairement épictétiennes ; (2) là où Origène s'écarte "
            "du stoïcisme (identification autexousion = eph' hēmin, "
            "rétention permanente de la liberté même par les démons, "
            "possibilité de chute et de retour qui fonde l'apokatastasis), "
            "c'est par platonisme et non par christianisme ; (3) "
            "l'intérêt chrétien pour le libre arbitre est entièrement "
            "motivé par la polémique anti-gnostique (contre Marcion, "
            "Valentin, Basilide pour qui Dieu créateur est juste accusé) "
            "et anti-déterministe astrale (commentaire perdu sur Genèse + "
            "préface De princ. 5). Sub-thèse stratégique : il n'y a donc "
            "'no particular reason to expect a radically new notion of a "
            "free will emerging from Christianity' (p. 120-121)"
        ),
        description_en=(
            "Frede 2011 Ch. 7 synthesis (p. 102-124): Origen is the first "
            "Christian author to write systematically on free will, in a "
            "short treatise Peri autexousiou inserted into De principiis "
            "III.1 (preserved in Greek by Basil and Gregory Nazianzus's "
            "Philocalia ch. 21-27). Three main results per Frede: (1) the "
            "treatise 'could have been taken straight from a late Stoic "
            "handbook' — terminology and major theses are mostly Epictetan; "
            "(2) where Origen deviates from Stoicism (identification of "
            "autexousion with eph' hēmin, permanent retention of freedom "
            "even by demons, possibility of fall and return that grounds "
            "apokatastasis), it is by Platonism, not by Christianity; (3) "
            "Christian interest in free will is entirely motivated by anti-"
            "Gnostic polemic (against Marcion, Valentinus, Basilides who "
            "accuse the just Creator God) and anti-astral-determinist "
            "polemic (lost Commentary on Genesis + De princ. preface 5). "
            "Strategic sub-thesis: there is therefore 'no particular reason "
            "to expect a radically new notion of a free will emerging from "
            "Christianity' (p. 120-121)"
        ),
        period="Patristic",
        metadata=frede_metadata(
            page_range="p. 102-124",
            chapter="Ch. 7 An Early Christian View on a Free Will: Origen",
            chapter_actual="Origen as first systematic Christian author on free will, Stoic in substance, Platonist in differences, anti-Gnostic in motivation",
            extra={"frede_2011_role": "origen_christian_stoic_inheritance"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_frede2011_ch8_plotinus",
        type="synthesis",
        label="Ch. 8 — Plotin et la liberté divine archétype (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 8 (p. 125-152) : Plotin, dans Ennéade "
            "VI.8 'Sur la volontariété et la volonté de l'Un', donne la plus "
            "complète réception platonicienne de la notion stoïcienne. "
            "Innovation centrale : hiérarchisation de la liberté en quatre "
            "niveaux (homme incarné — âme — intellect — l'Un) où chaque "
            "niveau inférieur reflète et atténue le niveau supérieur. "
            "L'intellect est paradoxalement libre 'précisément parce qu'il "
            "n'y a aucune chance qu'il agisse autrement' (4.20-23) ; "
            "l'âme, par 'intellectualisation' (noōthēnai, 5.34-36), accède "
            "à la liberté ; l'Un, dans un acte de volonté libre absolue et "
            "non-conditionnée, est l'archétype de toute liberté. Deux thèses "
            "polémiques de Frede : (a) contre Armstrong, l'idée que Dieu "
            "agit par un acte libre de volonté n'est pas spécifiquement "
            "judéo-chrétienne — Plotin l'établit indépendamment ; (b) "
            "Plotin est plus proche du stoïcisme que d'Alexandre, "
            "'la liberté est une question de possession sûre et de contrôle "
            "de ce que l'on veut'"
        ),
        description_en=(
            "Frede 2011 Ch. 8 synthesis (p. 125-152): Plotinus, in Ennead "
            "VI.8 'On Voluntariness and the Will of the One', gives the "
            "fullest Platonist reception of the Stoic notion. Central "
            "innovation: hierarchization of freedom into four levels "
            "(embodied human — soul — intellect — the One), with each "
            "lower level reflecting and attenuating the higher. The "
            "intellect is paradoxically free 'precisely because there is "
            "no chance whatsoever that it might act otherwise' (4.20-23); "
            "the soul, by 'intellectualization' (noōthēnai, 5.34-36), "
            "achieves freedom; the One, in an absolutely free and "
            "unconditioned act of will, is the archetype of all freedom. "
            "Two of Frede's polemical theses: (a) against Armstrong, the "
            "idea that God acts by a free will-act is NOT specifically "
            "Judeo-Christian — Plotinus establishes it independently; (b) "
            "Plotinus is closer to Stoicism than to Alexander, 'freedom is "
            "a matter of the secure possession and control of what one wills'"
        ),
        period="Roman Imperial",
        metadata=frede_metadata(
            page_range="p. 125-152",
            chapter="Ch. 8 Reactions to the Stoic Notion of a Free Will: Plotinus",
            chapter_actual="Plotinus's hierarchized freedom (human/soul/intellect/One) and refutation of the 'monstrous claim' about God's nature",
            extra={"frede_2011_role": "plotinus_platonist_consummation"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_frede2011_ch9_augustine",
        type="synthesis",
        label="Ch. 9 — Augustin n'invente PAS une notion radicalement nouvelle (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 9 (p. 153-174) : Augustin n'a pas "
            "produit une notion radicalement nouvelle de libre arbitre — "
            "contre Dihle 1982. Démonstration en cinq mouvements : (1) le "
            "velle augustinien est précisément la notion complexe "
            "épictétienne de volonté impliquée dans tout assentiment, y "
            "compris à des impressions non-impulsives (Dihle l'a mal "
            "interprété comme nouveauté) ; (2) le De libero arbitrio "
            "(388-395), à la lumière de la Retractatio finale, est et "
            "demeure l'exposition autorisée ; (3) Augustin suit le "
            "stoïcisme plus rigoureusement qu'Origène sur la dichotomie "
            "libre / esclave : après la chute, plus de libertas, "
            "seulement liberum arbitrium (= eph' hēmin stoïcien) ; (4) la "
            "doctrine de la grâce restauratrice découle directement de la "
            "structure stoïcienne où Dieu, face à une volonté asservie, "
            "n'a qu'à 'set things up' pour forcer le bon assentiment "
            "(Conf. VIII.12 le tolle lege) — précédent de Marius "
            "Victorinus ; (5) il n'y a 'not a trace of voluntarism' dans le "
            "De libero arbitrio (p. 171, 173). Différence majeure avec "
            "Origène : Augustin accepte le péché originel collectif (Rm "
            "5.12ff) et lit Paul comme attribuant à Dieu le vouloir lui-"
            "même, tandis qu'Origène s'y refusait"
        ),
        description_en=(
            "Frede 2011 Ch. 9 synthesis (p. 153-174): Augustine did NOT "
            "produce a radically new notion of free will — against Dihle "
            "1982. Demonstration in five moves: (1) Augustinian velle is "
            "precisely the complex Epictetan notion of will involved in "
            "every assent, including assent to non-impulsive impressions "
            "(Dihle misread this as innovation); (2) De libero arbitrio "
            "(388-395), in light of the final Retractationes, is and "
            "remains the authoritative exposition; (3) Augustine follows "
            "Stoicism more strictly than Origen on the free/enslaved "
            "dichotomy: after the Fall, no more libertas, only liberum "
            "arbitrium (= Stoic eph' hēmin); (4) the restorative doctrine "
            "of grace follows directly from the Stoic structure where God, "
            "facing an enslaved will, only has to 'set things up' to force "
            "the right assent (Conf. VIII.12 tolle lege) — Marius "
            "Victorinus precedent; (5) there is 'not a trace of "
            "voluntarism' in De libero arbitrio (p. 171, 173). Major "
            "difference from Origen: Augustine accepts collective original "
            "sin (Rom. 5:12ff) and reads Paul as attributing willing itself "
            "to God, where Origen had refused"
        ),
        period="Patristic",
        metadata=frede_metadata(
            page_range="p. 153-174",
            chapter="Ch. 9 Augustine: A Radically New Notion of a Free Will?",
            chapter_actual="Refutation of Dihle's Augustine-as-innovator thesis; Augustine as closer-to-Stoicism than Origen",
            extra={"frede_2011_role": "augustine_no_voluntarism_no_innovation"},
        ),
        confidence=0.98,
    ),
    _node(
        id="synthesis_frede2011_ch10_conclusion",
        type="synthesis",
        label="Ch. 10 Conclusion — bilan et défense limitée de la notion antique (Frede 2011)",
        description=(
            "Synthèse Frede 2011 Ch. 10 (p. 175-178) : Frede réunit ses "
            "résultats et répond à sa quatrième question initiale (la "
            "notion antique est-elle fondamentalement viciée ?). Bilan : "
            "(1) le libre arbitre émerge dans le stoïcisme tardif (Ier s. "
            "ap. J.-C.), clairement chez Épictète ; (2) il s'agit d'une "
            "capacité à faire des choix tels qu'aucune force du monde ne "
            "puisse les empêcher, à condition de ne pas s'asservir aux "
            "biens externes ; (3) son utilité polémique tenait à la peur, "
            "généralisée dans l'Antiquité tardive, d'être 'rien' face aux "
            "forces cachées (Plotin Enn. VI.8.1.26-27, 'mē pote ouden "
            "esmen') ; (4) les chrétiens adoptent cette notion stoïcienne ; "
            "Augustin la radicalise via Paul. Réponse à la quatrième "
            "question : non, la notion antique n'est PAS fondamentalement "
            "viciée — sauf chez Alexandre. Toutes les autres formulations "
            "(stoïcienne, plotinienne, origénienne, augustinienne) "
            "partagent l'idée que la liberté consiste à se libérer des "
            "fausses croyances et des attachements irrationnels, et cette "
            "idée 'does not seem to me to be a basically flawed idea at all'"
        ),
        description_en=(
            "Frede 2011 Ch. 10 synthesis (p. 175-178): Frede gathers his "
            "results and answers his fourth opening question (is the "
            "ancient notion basically flawed?). Bilan: (1) free will emerges "
            "in late Stoicism (1st c. CE), clearly in Epictetus; (2) it is "
            "the ability to make choices no force in the world can prevent, "
            "provided we do not enslave ourselves to external goods; (3) "
            "its polemical utility lay in the late-antique fear of being "
            "'nothing' before hidden forces (Plotinus Enn. VI.8.1.26-27, "
            "'mē pote ouden esmen'); (4) Christians adopt this Stoic notion; "
            "Augustine radicalizes it via Paul. Answer to fourth question: "
            "no, the ancient notion is NOT basically flawed — except in "
            "Alexander. All other formulations (Stoic, Plotinian, "
            "Origenian, Augustinian) share the idea that freedom consists "
            "in liberating oneself from false beliefs and irrational "
            "attachments, and this idea 'does not seem to me to be a "
            "basically flawed idea at all'"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 175-178",
            chapter="Ch. 10 Conclusion",
            chapter_actual="Bilan + qualified philosophical defense of the ancient notion (minus Alexander)",
            extra={"frede_2011_role": "conclusive_balance_sheet"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_frede2011_methodology_history_not_apologetic",
        type="synthesis",
        label="Méthodologie — enquête historique, non philosophique, contre Dihle (Frede 2011)",
        description=(
            "Synthèse méthodologique Frede 2011 (Ch. 1, p. 5-7) : Frede "
            "explicite que son enquête est PUREMENT historique et NON "
            "philosophique. Il refuse de partir d'une 'notre notion "
            "moderne du vouloir' qu'il accepterait ou défendrait — qui "
            "serait justement le procédé de Dihle 1982. Il ne s'agit pas "
            "de défendre ou de réfuter une notion contemporaine, mais de "
            "reconstituer ce que les Anciens ont effectivement pensé. Cette "
            "posture explique la structure du livre : pas de discussion "
            "frontale avec la philosophie analytique contemporaine du "
            "libre arbitre, pas de prise de position compatibiliste / "
            "incompatibiliste, mais une reconstruction historique guidée "
            "par un schéma neutre à trois composantes (cf. concept_frede_"
            "general_schema_of_free_will). Conséquence importante pour "
            "l'historiographie : Frede récuse les hypothèses non-historiques "
            "(le libre arbitre comme croyance ordinaire universelle ; comme "
            "invention judéo-chrétienne ; comme intuition transhistorique)"
        ),
        description_en=(
            "Frede 2011 methodological synthesis (Ch. 1, p. 5-7): Frede "
            "explicates that his inquiry is PURELY historical and NOT "
            "philosophical. He refuses to start from a 'our modern notion "
            "of will' he would accept or defend — which would be Dihle "
            "1982's procedure. He is not in the business of defending or "
            "refuting any contemporary notion but of reconstructing what "
            "the Ancients actually thought. This stance explains the book's "
            "structure: no head-on engagement with contemporary analytic "
            "free-will philosophy, no compatibilist/incompatibilist stance, "
            "but a historical reconstruction guided by a neutral three-"
            "component schema (cf. concept_frede_general_schema_of_free_"
            "will). Important consequence for historiography: Frede rejects "
            "non-historical hypotheses (free will as universal ordinary "
            "belief; as Judeo-Christian invention; as transhistorical intuition)"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 5-7",
            chapter="Ch. 1 Introduction §2",
            chapter_actual="Methodological declaration: purely historical, not apologetic, against Dihle",
            extra={"frede_2011_role": "methodological_self_positioning"},
        ),
        confidence=0.95,
    ),
]


# =============================================================================
# ARGUMENTS — 14 Frede scholarly theses (type: argument)
# =============================================================================

NEW_ARGUMENTS: list[dict[str, Any]] = [
    _node(
        id="argument_frede_2011_notion_is_technical_and_datable",
        type="argument",
        label="Le libre arbitre est une notion technique avec une origine historique datable (Frede 2011)",
        description=(
            "Argument-cadre Frede 2011 Ch. 1 (p. 1-18) : la notion de libre "
            "arbitre est philosophique, technique, et n'apparaît qu'à un "
            "moment historiquement identifiable. Prémisse négative : aucun "
            "texte grec d'Homère à Aristote ne mentionne explicitement un "
            "libre arbitre — non par négligence, mais parce que la notion "
            "n'existe pas encore. Prémisse positive : la notion résulte "
            "d'assumptions massives sur l'âme, le monde, la providence "
            "qui ne sont pas universelles. Conclusion : il est légitime de "
            "demander 'quand' et 'pourquoi' elle apparaît, et cette "
            "question n'a de sens que si on rejette l'interprétation de "
            "Ross (1923) selon laquelle Aristote partagerait 'the plain "
            "man's belief in free will'"
        ),
        description_en=(
            "Frede 2011 framing argument (Ch. 1, p. 1-18): the notion of "
            "free will is philosophical, technical, and appears at a "
            "historically identifiable moment. Negative premise: no Greek "
            "text from Homer to Aristotle explicitly mentions a free will — "
            "not by oversight, but because the notion does not yet exist. "
            "Positive premise: the notion presupposes massive assumptions "
            "about the soul, the world, providence, which are not universal. "
            "Conclusion: it is legitimate to ask 'when' and 'why' it "
            "appears, and this question makes sense only if one rejects "
            "Ross's (1923) interpretation that Aristotle shared 'the plain "
            "man's belief in free will'"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 1-18",
            chapter="Ch. 1 Introduction",
            chapter_actual="Free will is a technical philosophical notion with identifiable historical origin",
            extra={
                "argument_type": "scholarly_framing",
                "frede_target": "W. D. Ross 1923 ; popular intuition of universal free-will belief",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_frede_2011_aristotle_no_will_no_free_will",
        type="argument",
        label="Aristote n'a ni notion de volonté ni notion de libre arbitre (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 2 (p. 19-29). Prémisses : (P1) "
            "Aristote a boulēsis = désir-de-raison fonctionnellement "
            "dépendant de la cognition (voir le bien = le vouloir) ; (P2) "
            "Aristote a prohairesis = forme spéciale de boulēsis restreinte "
            "à eph' hēmin ; (P3) dans l'akrasia (EN VII), Aristote dit "
            "explicitement qu'on agit CONTRE sa prohairesis, sans recourir "
            "à un événement mental volitionnel ; (P4) hekōn / akōn "
            "s'applique même aux enfants et aux animaux non-rationnels et "
            "ne fait donc pas appel à une faculté volitionnelle. "
            "Conclusion : la responsabilité chez Aristote ne requiert pas "
            "de volonté distincte ; Aristote n'a ni notion de volonté ni "
            "notion de libre arbitre"
        ),
        description_en=(
            "Frede 2011 argument Ch. 2 (p. 19-29). Premises: (P1) Aristotle "
            "has boulēsis = desire-of-reason functionally dependent on "
            "cognition (seeing the good = willing it); (P2) Aristotle has "
            "prohairesis = a special form of boulēsis restricted to eph' "
            "hēmin; (P3) in akrasia (EN VII), Aristotle explicitly says one "
            "acts AGAINST one's prohairesis without invoking a volitional "
            "mental event; (P4) hekōn/akōn applies even to children and "
            "non-rational animals and so does not invoke a volitional "
            "faculty. Conclusion: responsibility in Aristotle does not "
            "require a distinct will; Aristotle has neither a notion of a "
            "will nor a notion of free will"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 19-29",
            chapter="Ch. 2 Aristotle on Choice without a Will",
            chapter_actual="Aristotle has prohairesis without a will-faculty",
            extra={
                "argument_type": "scholarly_thesis",
                "frede_target": "Kenny 1979 (Aristotle's Theory of the Will) ; Ross 1923 ; Dihle 1982",
                "primary_textual_anchors": ["EN III.1-5 (1110b18-1113a33)", "EN VII (1145b21-1148a9)"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_frede_2011_stoic_assent_is_proto_will",
        type="argument",
        label="L'assentiment stoïcien fournit les matériaux d'une volonté, sans encore en être une (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 3 (p. 31-48). Le stoïcisme classique "
            "(Zénon, Chrysippe) construit l'architecture conceptuelle "
            "nécessaire à toute notion ultérieure de volonté : (a) âme "
            "unipartite = raison ; (b) toute action présuppose un "
            "assentiment (synkatathesis) à une impression impulsive "
            "(phantasia hormētikē) ; (c) tout désir mûr est rationnel ; "
            "(d) modal logic chrysippéenne : aucune impression ne nécessite "
            "l'assentiment. Mais ce dispositif n'est pas encore une notion "
            "de volonté : il manque l'unité subjective de la prohairesis "
            "comme 'soi', l'intériorisation systématique, et la "
            "fonction-clé épictétienne. Frede : 'we have the notion of "
            "assent, and hence the appropriate notion of a willing, but we "
            "do not yet have the notion of a choice, let alone of a will' "
            "(p. 43)"
        ),
        description_en=(
            "Frede 2011 argument Ch. 3 (p. 31-48). Classical Stoicism "
            "(Zeno, Chrysippus) constructs the conceptual architecture "
            "needed for any later notion of will: (a) unipartite soul = "
            "reason; (b) every action presupposes assent (synkatathesis) to "
            "an impulsive impression (phantasia hormētikē); (c) every "
            "mature desire is rational; (d) Chrysippean modal logic: no "
            "impression necessitates assent. But this apparatus is not yet "
            "a notion of will: it lacks the subjective unity of prohairesis "
            "as 'self', systematic interiorization, and Epictetus's key "
            "function. Frede: 'we have the notion of assent, and hence the "
            "appropriate notion of a willing, but we do not yet have the "
            "notion of a choice, let alone of a will' (p. 43)"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 31-48",
            chapter="Ch. 3 Emergence of a Notion of Will in Stoicism",
            chapter_actual="Classical Stoic assent architecture is proto-will, not yet will",
            extra={
                "argument_type": "scholarly_thesis",
                "frede_target": "any account that locates the will already in Chrysippus or Zeno",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_frede_2011_epictetus_first_free_will",
        type="argument",
        label="Épictète articule la première notion effective de libre arbitre (Frede 2011)",
        description=(
            "Thèse centrale du livre. Frede 2011 Ch. 5 §2 (p. 76-85). "
            "Prémisses : (P1) le terme autexousion apparaît deux fois chez "
            "Musonius puis fréquemment chez Épictète et nomme la liberté ; "
            "(P2) Épictète place la prohairesis au centre de sa "
            "psychologie morale (Diss. 1.29.1 : c'est ce qui te définit "
            "comme personne) ; (P3) Épictète rétrécit eph' hēmin de "
            "l'action externe à l'assentiment intérieur ; (P4) Épictète "
            "déclare explicitement (Diss. 1.1.23 ; 1.4.18 ; 3.5.7) "
            "qu'aucune force au monde, pas même Dieu, ne peut forcer ce "
            "choix tant que la volonté reste libre. Conclusion : 'here we "
            "have our first actual notion of a free will' (p. 76-77). "
            "Restriction : seul le sage l'exerce effectivement, les autres "
            "se sont asservis aux biens externes"
        ),
        description_en=(
            "Central thesis of the book. Frede 2011 Ch. 5 §2 (p. 76-85). "
            "Premises: (P1) the term autexousion appears twice in Musonius "
            "and frequently in Epictetus and names freedom; (P2) Epictetus "
            "places prohairesis at the center of his moral psychology "
            "(Diss. 1.29.1: this is what defines you as a person); (P3) "
            "Epictetus narrows eph' hēmin from external action to internal "
            "assent; (P4) Epictetus explicitly declares (Diss. 1.1.23; "
            "1.4.18; 3.5.7) that no force in the world, not even God, can "
            "force this choice as long as the will remains free. Conclusion: "
            "'here we have our first actual notion of a free will' "
            "(p. 76-77). Restriction: only the wise person actually "
            "exercises it; the rest have enslaved themselves to external goods"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 74-85",
            chapter="Ch. 5 The Emergence of a Notion of a Free Will in Stoicism",
            chapter_actual="The flagship thesis: Epictetus invents the first actual notion of a free will",
            extra={
                "argument_type": "scholarly_thesis_flagship",
                "frede_target": "Dihle 1982 (Augustine origin) ; Sorabji 2006 (gradual emergence) ; Kahn 1988 (Seneca-Epictetus) — Frede specifies Epictetus precisely",
                "primary_textual_anchors": [
                    "Epictetus Diss. 1.1 (whole)",
                    "Diss. 1.1.23 (God cannot force will)",
                    "Diss. 1.4.18 (will is intended to be free by nature)",
                    "Diss. 1.12.9 (no force can prevent will from making choices)",
                    "Diss. 1.29.1 (quality of person = quality of will)",
                    "Diss. 3.5.7 (free will up to last moment)",
                    "Diss. 3.3.8-10 (God will not take away free will)",
                    "Musonius Rufus fragments (autexousion attestation)",
                ],
            },
        ),
        confidence=0.98,
    ),
    _node(
        id="argument_frede_2011_autexousion_stoic_origin_then_christian",
        type="argument",
        label="Autexousion d'origine stoïcienne, popularisé par les chrétiens depuis Justin (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 5 (p. 74-75) et Ch. 7 (p. 102-104). "
            "Le terme autexousion (1) apparaît d'abord en contexte stoïcien : "
            "Musonius Rufus (2 occurrences attestées) puis Épictète "
            "(fréquent) ; (2) est repris par platoniciens et péripatéticiens "
            "tardifs ; (3) entre dans la littérature chrétienne avec Justin "
            "Martyr et y devient massivement plus fréquent que chez les "
            "auteurs païens contemporains. Conclusion stratégique : "
            "l'apparente 'omniprésence chrétienne' de la notion ne signe "
            "pas une invention chrétienne ; elle signe une adoption "
            "réussie d'un vocabulaire stoïcien-philosophique préexistant"
        ),
        description_en=(
            "Frede 2011 argument Ch. 5 (p. 74-75) and Ch. 7 (p. 102-104). "
            "The term autexousion (1) first appears in Stoic context: "
            "Musonius Rufus (2 attested occurrences) then Epictetus "
            "(frequently); (2) is taken up by later Platonists and "
            "Peripatetics; (3) enters Christian literature with Justin "
            "Martyr and becomes massively more frequent there than among "
            "contemporary pagan authors. Strategic conclusion: the "
            "apparent 'Christian ubiquity' of the notion does NOT signal "
            "Christian invention; it signals successful adoption of a "
            "preexisting Stoic-philosophical vocabulary"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 74-75, 102-104",
            chapter="Ch. 5 + Ch. 7",
            chapter_actual="Autexousion : Stoic origin (Musonius → Epictetus), Christian adoption (from Justin Martyr)",
            extra={
                "argument_type": "scholarly_thesis",
                "frede_target": "any view that takes autexousion as a Christian theological invention",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_frede_2011_alexander_libertarian_dead_end",
        type="argument",
        label="Alexandre d'Aphrodise = ancêtre direct du libre arbitre moderne vicié (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 6 (p. 95-101) + Conclusion (p. 177-178). "
            "Prémisses : (P1) Alexandre exige qu'une action soit libre "
            "seulement si l'agent aurait pu, dans des circonstances "
            "internes-et-externes identiques, choisir autrement (De fato "
            "192, 22ff) ; (P2) cette exigence est incompatible avec "
            "l'Aristotélisme qu'Alexandre défend ailleurs (le vertueux ne "
            "peut pas choisir autrement) ; (P3) le Mantissa ch. XXII "
            "(probablement par un disciple d'Alexandre) tire la conséquence "
            "que la liberté-comme-pouvoir-de-choisir-autrement est un signe "
            "de faiblesse. Conclusion : Alexandre 'is the only major "
            "ancient philosopher' dont la notion est fondamentalement "
            "viciée, et il est précisément 'the ancestor of the notion that "
            "to have a free will is to be able, in the very same "
            "circumstances, to choose between doing A and doing B' "
            "(p. 100) — la notion attaquée par Ryle, Williams et Frede"
        ),
        description_en=(
            "Frede 2011 argument Ch. 6 (p. 95-101) + Conclusion (p. 177-178). "
            "Premises: (P1) Alexander requires that an action be free only "
            "if the agent could, in identical internal-and-external "
            "circumstances, have chosen otherwise (De fato 192, 22ff); (P2) "
            "this requirement is incompatible with the Aristotelianism "
            "Alexander defends elsewhere (the virtuous cannot choose "
            "otherwise); (P3) the Mantissa ch. XXII (probably by an "
            "Alexandrian disciple) draws the consequence that freedom-as-"
            "power-to-choose-otherwise is a sign of weakness. Conclusion: "
            "Alexander 'is the only major ancient philosopher' whose notion "
            "is basically flawed, and he is precisely 'the ancestor of the "
            "notion that to have a free will is to be able, in the very "
            "same circumstances, to choose between doing A and doing B' "
            "(p. 100) — the notion attacked by Ryle, Williams, and Frede"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 95-101, 177-178",
            chapter="Ch. 6 + Ch. 10",
            chapter_actual="Alexander's libertarian incompatibilism as flawed ancestor of modern voluntarist free will",
            extra={
                "argument_type": "scholarly_thesis",
                "frede_target": "neo-libertarian readings of Alexander as paradigm of free will",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_frede_2011_origen_stoic_christianity_anti_gnostic",
        type="argument",
        label="Origène = stoïcisme christianisé motivé par anti-gnosticisme et anti-astrologie (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 7 (p. 102-124). Trois sous-thèses : "
            "(S1) Origène est le premier auteur chrétien à traiter "
            "systématiquement du libre arbitre, dans De principiis III.1 = "
            "Peri autexousiou (préservé en grec par les Philocalia 21-27 de "
            "Basile et Grégoire de Nazianze) ; (S2) la terminologie et les "
            "thèses majeures sont 'through and through Stoic, with the "
            "terminology almost invariably being found in Epictetus' "
            "(p. 113) ; (S3) les différences avec le stoïcisme (autexousion "
            "= eph' hēmin, liberté retenue par les démons, possibilité de "
            "chute et retour ouvrant la voie à l'apokatastasis) proviennent "
            "du platonisme d'Origène, pas de son christianisme. "
            "Conséquence stratégique : il n'y a 'no particular reason to "
            "expect a radically new notion of a free will emerging from "
            "Christianity' (p. 120-121). Le moteur historique de "
            "l'investissement chrétien dans le libre arbitre est polémique : "
            "anti-Marcion, anti-Valentin, anti-Basilide (Gnostiques) ; "
            "anti-déterminisme astral (Apocryphon de Jean, sermons "
            "augustiniens). Le doctrine de l'apokatastasis est sa "
            "conséquence directe : les intellects créés ne connaissent "
            "jamais inébranlablement le bien, donc chute et retour restent "
            "perpétuellement possibles"
        ),
        description_en=(
            "Frede 2011 argument Ch. 7 (p. 102-124). Three sub-theses: (S1) "
            "Origen is the first Christian author to treat free will "
            "systematically, in De principiis III.1 = Peri autexousiou "
            "(preserved in Greek by Basil and Gregory Nazianzus's "
            "Philocalia 21-27); (S2) terminology and major theses are "
            "'through and through Stoic, with the terminology almost "
            "invariably being found in Epictetus' (p. 113); (S3) differences "
            "from Stoicism (autexousion = eph' hēmin, freedom retained by "
            "demons, possibility of fall and return opening the way to "
            "apokatastasis) come from Origen's Platonism, not his "
            "Christianity. Strategic consequence: there is 'no particular "
            "reason to expect a radically new notion of a free will "
            "emerging from Christianity' (p. 120-121). The historical "
            "driver of the Christian investment in free will is polemical: "
            "anti-Marcion, anti-Valentinus, anti-Basilides (Gnostics); anti-"
            "astral-determinism (Apocryphon of John, Augustine's sermons). "
            "The apokatastasis doctrine is its direct consequence: created "
            "intellects never unshakeably know the good, so fall and return "
            "remain perpetually possible"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 102-124",
            chapter="Ch. 7 An Early Christian View on a Free Will: Origen",
            chapter_actual="Origen's free will is Stoic in substance, Platonist in distinctive features, anti-Gnostic in motivation",
            extra={
                "argument_type": "scholarly_thesis",
                "frede_target": "any view that locates a Christian innovation in Origen's free will",
                "primary_textual_anchors": [
                    "Origen De princ. III.1 (Peri autexousiou)",
                    "De princ. preface 4-5",
                    "De princ. I.3.8, I.4.1, I.6.2, I.8.2, II.9.2, II.9.5-6",
                    "Origen Comm. in Ioan. ad XIII.19.12.16",
                    "Origen CC 5.61 (against Gnostics)",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_frede_2011_origen_differences_from_platonism_not_christianity",
        type="argument",
        label="Les différences d'Origène avec les Stoïciens viennent de son platonisme, pas de son christianisme (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 7 (p. 120-124). Origène diffère du "
            "stoïcisme classique sur cinq points : (1) il identifie "
            "autexousion à eph' hēmin (alors que les Stoïciens distinguent "
            "liberté du sage et eph' hēmin du fou) ; (2) tous les humains "
            "sont libres dès la création, et la liberté ne peut être "
            "perdue ; (3) même les démons retiennent un libre arbitre ; "
            "(4) la moindre faute n'a pas chez Origène les conséquences "
            "catastrophiques (tous les péchés égaux) du stoïcisme ; (5) "
            "le sage stoïcien ne peut plus se tromper, mais les intellects "
            "créés d'Origène, séparés du Bien par un gouffre cognitif, "
            "le peuvent toujours. Frede démontre que ces cinq différences "
            "découlent du platonisme d'Origène — héritier d'Ammonius "
            "Saccas, formé à la philosophie grecque (Eusèbe HE VI.1.1 ; "
            "Porphyre dans la VP) — et non d'un substrat doctrinal "
            "chrétien spécifique"
        ),
        description_en=(
            "Frede 2011 argument Ch. 7 (p. 120-124). Origen differs from "
            "classical Stoicism on five points: (1) he identifies "
            "autexousion with eph' hēmin (whereas Stoics distinguish the "
            "wise person's freedom from the fool's eph' hēmin); (2) all "
            "humans are free from creation, and freedom cannot be lost; "
            "(3) even demons retain free will; (4) the smallest mistake "
            "lacks for Origen the catastrophic consequences (all sins "
            "equal) it has in Stoicism; (5) the Stoic wise can no longer "
            "err, but Origen's created intellects, separated from the Good "
            "by a cognitive gap, always can. Frede demonstrates that these "
            "five differences derive from Origen's Platonism — heir to "
            "Ammonius Saccas, trained in Greek philosophy (Eusebius HE "
            "VI.1.1; Porphyry in VP) — and not from any specifically "
            "Christian doctrinal substrate"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 120-124",
            chapter="Ch. 7 §3-4",
            chapter_actual="Origen's five differences from Stoic free will are Platonist, not Christian",
            extra={"argument_type": "scholarly_thesis"},
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_frede_2011_plotinus_hierarchized_freedom",
        type="argument",
        label="Plotin hiérarchise la liberté en quatre niveaux (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 8 (p. 130-149). Plotin (Enn. VI.8) "
            "construit une hiérarchie ontologique de la liberté qui "
            "renverse les intuitions modernes : (N1) homme incarné — "
            "liberté hautement qualifiée par le corps et la nécessité ; "
            "(N2) âme — liberté diminuée, dépendante de la vertu, "
            "menacée par le corps ; (N3) intellect — liberté inconditionnée "
            "PRÉCISÉMENT parce qu'il ne peut pas agir autrement (VI.8.4.20-"
            "23) ; (N4) l'Un — liberté absolue et archétype de toute "
            "liberté. Renversement plotinien crucial : le pouvoir-de-faire-"
            "autrement (Alexandre) signe au contraire une liberté diminuée, "
            "celui qui poursuit un bien qu'il n'a pas encore ('one is "
            "driven by something outside oneself', p. 143). 'Intellectua-"
            "lization' (noōthēnai, VI.8.5.34-36) = état de l'âme qui devient "
            "second-intellect et y trouve sa liberté"
        ),
        description_en=(
            "Frede 2011 argument Ch. 8 (p. 130-149). Plotinus (Enn. VI.8) "
            "constructs an ontological hierarchy of freedom that overturns "
            "modern intuitions: (N1) embodied human — freedom highly "
            "qualified by body and necessity; (N2) soul — diminished "
            "freedom, dependent on virtue, threatened by body; (N3) "
            "intellect — unqualified freedom PRECISELY because it cannot "
            "act otherwise (VI.8.4.20-23); (N4) the One — absolute freedom "
            "and archetype of all freedom. Crucial Plotinian inversion: "
            "the power-to-do-otherwise (Alexander) signals on the contrary "
            "diminished freedom — someone pursuing a good not yet had ('one "
            "is driven by something outside oneself', p. 143). 'Intellec-"
            "tualization' (noōthēnai, VI.8.5.34-36) = state of the soul "
            "that becomes a second-intellect and finds its freedom therein"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 125-149",
            chapter="Ch. 8 §1-3",
            chapter_actual="Plotinus's four-tier hierarchy of freedom inverts the could-have-chosen-otherwise criterion",
            extra={
                "argument_type": "scholarly_thesis",
                "frede_target": "Alexander-style libertarian readings",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_frede_2011_plotinus_divine_will_not_judeo_christian",
        type="argument",
        label="L'idée que Dieu agit par acte libre de volonté n'est PAS spécifiquement judéo-chrétienne (Frede 2011 vs Armstrong)",
        description=(
            "Argument Frede 2011 Ch. 8 §3 (p. 144-152). Polémique frontale "
            "contre A. H. Armstrong, qui voyait dans Plotin Enn. VI.8 une "
            "importation chrétienne. Frede démontre : (P1) Plotin déclare "
            "explicitement (VI.8.1.5-6) que Dieu peut absolument tout et "
            "que tout est eph' hēmin de lui ; (P2) il rejette comme "
            "'monstrous thing to say' (ho tolmēros logos, VI.8.7.11ff) "
            "l'idée que Dieu agirait par nécessité de sa propre nature ; "
            "(P3) il affirme que la réalité tout entière origine en un acte "
            "absolument libre et inconditionné de la volonté divine, dont "
            "la volonté humaine est une faible image (VI.8.15.1-2 : Dieu = "
            "amour, et amour de soi-même). Conclusion : 'it is not quite "
            "right to hold that such a way of looking at the human will is "
            "specifically Judaeo-Christian' (p. 129-130). Tout au plus on "
            "peut envisager une influence d'Origène (que Porphyre "
            "connaissait, qui avait étudié avec Ammonius Saccas comme Plotin) "
            "— mais l'argumentaire plotinien est philosophique-grec, non "
            "biblique"
        ),
        description_en=(
            "Frede 2011 argument Ch. 8 §3 (p. 144-152). Direct polemic "
            "against A. H. Armstrong, who saw in Plotinus Enn. VI.8 a "
            "Christian import. Frede demonstrates: (P1) Plotinus explicitly "
            "states (VI.8.1.5-6) that God can do absolutely everything and "
            "that everything is up to him; (P2) he rejects as 'a monstrous "
            "thing to say' (ho tolmēros logos, VI.8.7.11ff) the idea that "
            "God acts by necessity of his own nature; (P3) he affirms that "
            "all reality originates in an absolutely free and unconditioned "
            "act of divine will, of which human will is a faint image "
            "(VI.8.15.1-2: God = love, and self-love). Conclusion: 'it is "
            "not quite right to hold that such a way of looking at the "
            "human will is specifically Judaeo-Christian' (p. 129-130). At "
            "most one might consider an influence from Origen (whom "
            "Porphyry knew, who had studied with Ammonius Saccas like "
            "Plotinus) — but the Plotinian argument is philosophical-Greek, "
            "not biblical"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 129-152",
            chapter="Ch. 8 §3",
            chapter_actual="Refutation of Armstrong's reading of Enn. VI.8 as Christian-influenced",
            extra={
                "argument_type": "scholarly_polemic",
                "frede_target": "A. H. Armstrong (399: 'probably due to Jewish and Christian contacts')",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_frede_2011_augustine_no_new_notion_vs_dihle",
        type="argument",
        label="Augustin n'invente PAS une notion radicalement nouvelle de libre arbitre (Frede 2011 vs Dihle)",
        description=(
            "Argument Frede 2011 Ch. 9 (p. 153-174), thèse-réponse à Dihle "
            "1982. Cinq sous-prémisses : (P1) le velle augustinien est la "
            "notion complexe épictétienne de volonté impliquée dans tout "
            "assentiment, y compris non-impulsif (Dihle l'a mal interprété, "
            "p. 157-159) ; (P2) le De libero arbitrio (388-395) est "
            "l'exposition autorisée, encore endossée dans les "
            "Retractationes ; (P3) après la chute, Augustin suit "
            "rigoureusement la dichotomie stoïcienne libre / esclave : "
            "plus de libertas, seulement liberum arbitrium = eph' hēmin "
            "stoïcien (De lib. ar. II.205 ; CD I.25) ; (P4) la doctrine de "
            "la grâce dérive directement de la structure stoïcienne où "
            "Dieu force le bon assentiment chez la volonté asservie (cf. "
            "Conf. VIII.12 tolle lege ; Marius Victorinus précédent) ; (P5) "
            "il n'y a 'not a trace of voluntarism' dans le De libero "
            "arbitrio (p. 171, 173). Conclusion : 'Augustine turns out to "
            "differ from Origen, not by moving further away from Stoicism "
            "but by adhering to it much more closely than Origen did' "
            "(p. 177)"
        ),
        description_en=(
            "Frede 2011 argument Ch. 9 (p. 153-174), thesis-response to "
            "Dihle 1982. Five sub-premises: (P1) Augustinian velle is the "
            "complex Epictetan notion of will involved in every assent, "
            "including non-impulsive ones (Dihle misread this, p. 157-159); "
            "(P2) De libero arbitrio (388-395) is the authoritative "
            "exposition, still endorsed in the Retractationes; (P3) after "
            "the Fall, Augustine rigorously follows the Stoic free/enslaved "
            "dichotomy: no more libertas, only liberum arbitrium = Stoic "
            "eph' hēmin (De lib. ar. II.205; CD I.25); (P4) the grace "
            "doctrine derives directly from the Stoic structure where God "
            "forces the right assent in the enslaved will (cf. Conf. "
            "VIII.12 tolle lege; Marius Victorinus precedent); (P5) there "
            "is 'not a trace of voluntarism' in De libero arbitrio (p. 171, "
            "173). Conclusion: 'Augustine turns out to differ from Origen, "
            "not by moving further away from Stoicism but by adhering to "
            "it much more closely than Origen did' (p. 177)"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 153-174, 177",
            chapter="Ch. 9 + Conclusion",
            chapter_actual="Refutation of Dihle's Augustine-as-inventor-of-modern-free-will thesis",
            extra={
                "argument_type": "scholarly_thesis_flagship",
                "frede_target": "Albrecht Dihle 1982 (Theory of Will, Sather 48) ; Pelagian-vs-anti-Pelagian misreadings of Augustine",
                "primary_textual_anchors": [
                    "Augustine De lib. ar. I.10, I.77, I.79-81, I.86",
                    "De lib. ar. II.43, II.143, II.199-200, II.205",
                    "De lib. ar. III.240-263",
                    "CD I.25",
                    "Conf. VIII.5-12 (tolle lege)",
                    "Retractationes 2-6",
                ],
            },
        ),
        confidence=0.98,
    ),
    _node(
        id="argument_frede_2011_augustine_stoic_paul_via_marius_victorinus",
        type="argument",
        label="Augustin lit Paul via Marius Victorinus pour attribuer le vouloir lui-même à Dieu (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 9 (p. 168-172). Là où Origène avait "
            "refusé l'interprétation paulinienne (Rm 9.6 ; Ph 2.13) selon "
            "laquelle Dieu cause notre vouloir, Augustin l'accepte. Le "
            "précédent direct selon Frede est Marius Victorinus dans son "
            "commentaire sur Philippiens (le commentaire sur Romains de "
            "Victorinus étant perdu) : Dieu opère en nous pour nous faire "
            "vouloir ce qu'il veut et arrange le monde pour que notre "
            "vouloir soit efficace. Conséquence dogmatique : 'both the "
            "willing and the doing are God's'. Ce n'est PAS une rupture "
            "anti-stoïcienne mais l'application rigoureuse de la doctrine "
            "stoïcienne du fou-esclave dont l'assentiment est forcé par "
            "les circonstances arrangées par la providence"
        ),
        description_en=(
            "Frede 2011 argument Ch. 9 (p. 168-172). Where Origen had "
            "refused the Pauline reading (Rom. 9:6; Phil. 2:13) according "
            "to which God causes our willing, Augustine accepts it. The "
            "direct precedent per Frede is Marius Victorinus in his "
            "commentary on Philippians (Victorinus's Romans commentary "
            "being lost): God operates in us to make us will what he "
            "wills, and arranges the world so that our willing is "
            "effective. Doctrinal consequence: 'both the willing and the "
            "doing are God's'. This is NOT an anti-Stoic break but the "
            "rigorous application of the Stoic doctrine of the fool-slave "
            "whose assent is forced by circumstances providentially "
            "arranged"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 168-172",
            chapter="Ch. 9",
            chapter_actual="Marius Victorinus as precedent for Augustinian reading of Paul on grace",
            extra={"argument_type": "scholarly_thesis"},
        ),
        confidence=0.85,
    ),
    _node(
        id="argument_frede_2011_christianity_anti_gnostic_anti_astral_motivation",
        type="argument",
        label="Le motif chrétien d'investir le libre arbitre = polémique anti-gnostique et anti-astrale (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 7 (p. 114-121). L'intérêt massif des "
            "chrétiens des IIe-IVe siècles pour le libre arbitre n'a pas "
            "de source théologique-révélée : (1) l'Écriture ne fournit pas "
            "de termes techniques de liberté de la volonté ; Origène "
            "lui-même, voulant justifier scripturairement le libre arbitre, "
            "n'a 'que des passages qui présupposent qu'on y croit déjà' ; "
            "(2) le motif est polémique-doctrinal : combattre les Gnostiques "
            "(Marcion, Valentin, Basilide, Apocryphon de Jean) qui "
            "attribuent à un créateur inférieur la situation humaine, et "
            "combattre le déterminisme astral très répandu (Augustin dans "
            "un sermon : 'beaucoup hésitent à se convertir à cause de leurs "
            "croyances astrologiques') ; (3) la doctrine stoïcienne du "
            "libre arbitre 'admirably served the purpose of combating these "
            "unorthodox views', d'où sa réception massive. Conclusion : 'no "
            "particular reason to expect a radically new notion of a free "
            "will emerging from Christianity'"
        ),
        description_en=(
            "Frede 2011 argument Ch. 7 (p. 114-121). The massive 2nd-4th c. "
            "Christian interest in free will has no revealed-theological "
            "source: (1) Scripture provides no technical free-will "
            "vocabulary; Origen himself, trying to justify free will "
            "scripturally, can find only 'passages that presuppose belief "
            "in it'; (2) the motive is polemical-doctrinal: combating "
            "Gnostics (Marcion, Valentinus, Basilides, Apocryphon of John) "
            "who blame an inferior creator for the human condition, and "
            "combating very widespread astral determinism (Augustine in a "
            "sermon: 'many hesitate to convert because of their "
            "astrological beliefs'); (3) the Stoic doctrine of free will "
            "'admirably served the purpose of combating these unorthodox "
            "views', hence its massive reception. Conclusion: 'no "
            "particular reason to expect a radically new notion of a free "
            "will emerging from Christianity'"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 114-121",
            chapter="Ch. 7 §2-4",
            chapter_actual="Christian free-will doctrine motivated by anti-Gnostic and anti-astrological polemic, not theological invention",
            extra={"argument_type": "scholarly_thesis"},
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_frede_2011_ancient_notion_not_basically_flawed",
        type="argument",
        label="La notion antique de libre arbitre (sauf chez Alexandre) n'est PAS fondamentalement viciée (Frede 2011)",
        description=(
            "Argument Frede 2011 Ch. 10 (p. 177-178). Frede répond à sa "
            "quatrième question initiale (la notion était-elle fatalement "
            "viciée ?). Réponse : NON, sauf chez Alexandre. Toutes les "
            "autres formulations antiques (stoïcienne, plotinienne, "
            "origénienne, augustinienne) partagent une intuition rationnelle "
            "défendable : la liberté consiste à se libérer des fausses "
            "croyances et des attachements irrationnels qui obscurcissent "
            "notre choix. Le monde n'impose pas systématiquement ces "
            "fausses croyances ; nous pouvons donc, en principe, nous en "
            "libérer. Frede : cette idée 'does not seem to me to be a "
            "basically flawed idea at all'. Cette qualification est "
            "importante : elle distingue la critique philosophique "
            "contemporaine (Ryle, Williams) qui s'attaque à la version "
            "alexandrienne-libertarienne d'une critique de la notion comme "
            "telle"
        ),
        description_en=(
            "Frede 2011 argument Ch. 10 (p. 177-178). Frede answers his "
            "fourth opening question (was the notion fatally flawed?). "
            "Answer: NO, except in Alexander. All other ancient "
            "formulations (Stoic, Plotinian, Origenian, Augustinian) share "
            "a defensible rational intuition: freedom consists in "
            "liberating oneself from the false beliefs and irrational "
            "attachments that cloud our choices. The world does not "
            "systematically force these false beliefs on us; we can "
            "therefore, in principle, free ourselves. Frede: this idea "
            "'does not seem to me to be a basically flawed idea at all'. "
            "This qualification is important: it separates contemporary "
            "philosophical critique (Ryle, Williams), which attacks the "
            "Alexandrian-libertarian version, from a critique of the "
            "notion as such"
        ),
        period="Modern",
        metadata=frede_metadata(
            page_range="p. 177-178",
            chapter="Ch. 10 Conclusion",
            chapter_actual="Philosophical balance sheet: ancient notion is defensible except in Alexander",
            extra={"argument_type": "scholarly_thesis_evaluative"},
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# WORKS — none new; book is captured as publication. Empty list for symmetry.
# =============================================================================

NEW_WORKS: list[dict[str, Any]] = []
