"""Amand B6 — NEW_INSERTS list (new nodes).

Each node carries an Amand-standard metadata block (page_range, md_line_range,
chapter, source_quality, bibtex_key, claimed_by, publication). Descriptions are
plain text (no markdown) — bilingual FR/EN.
"""
from __future__ import annotations

from typing import Any

from amand_b6_utils import amand_metadata, dump_metadata


def _node(
    *,
    id: str,
    type: str,
    label: str,
    description: str,
    description_en: str,
    period: str | None,
    metadata: dict[str, Any],
    confidence: float = 0.9,
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
# 1. NEW PERSONS (1)
# =============================================================================

NEW_PERSONS: list[dict[str, Any]] = [
    _node(
        id="person_gregory_nazianzus_d389",
        type="person",
        label="Gregory of Nazianzus",
        description=(
            "Grégoire de Nazianze (c. 329/330-389 CE), évêque de Sasime puis brièvement "
            "de Constantinople (380-381), 'le Théologien' selon l'Église orthodoxe, "
            "l'un des trois Pères cappadociens avec Basile et Grégoire de Nysse. Ami "
            "intime de Basile, avec lequel il compila la Philocalia d'Origène. Auteur "
            "de 45 Orationes, environ 250 lettres, et un vaste corpus poétique (~17 000 "
            "vers, dont les Carmina dogmatica, theologica, historica et moralia). Pour "
            "Amand 1945, en note supplémentaire au chapitre VIII (p. 401-404), Grégoire "
            "n'est pas un témoin majeur de la transmission carnéadienne mais montre que "
            "l'argumentation morale antifataliste de Carnéade 'était devenue, bien avant "
            "le IVᵉ siècle, un lieu commun d'école' — dégradée 'en idée banale et "
            "impersonnelle'. L'écho carnéadien le plus net se trouve dans le Carmen "
            "dogmaticum 5 Περὶ προνοίας (PG 37.424-429), composé en hexamètres "
            "dactyliques imités d'Homère."
        ),
        description_en=(
            "Gregory of Nazianzus (c. 329/330-389 CE), bishop of Sasima and briefly of "
            "Constantinople (380-381), 'the Theologian' in the Orthodox tradition, one "
            "of the three Cappadocian Fathers alongside Basil and Gregory of Nyssa. "
            "Intimate friend of Basil, with whom he compiled Origen's Philocalia. Author "
            "of 45 Orations, ~250 letters, and a vast poetic corpus (~17,000 lines, "
            "including Carmina dogmatica, theologica, historica and moralia). For Amand "
            "1945, in a supplementary note to chapter VIII (p. 401-404), Gregory is not a "
            "principal witness of the Carneadean transmission but shows that Carneades' "
            "moral antifatalist argumentation 'had become, well before the 4th century, "
            "a schoolroom commonplace' — degraded 'into a banal and impersonal idea'. "
            "The clearest Carneadean echo appears in Carmen dogmaticum 5 Peri pronoias "
            "(PG 37.424-429), composed in dactylic hexameters imitating Homer."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 401-404",
            md_line_range="ll. 20937-21130",
            chapter="Livre II Ch. VIII Note supplémentaire (Grégoire de Nazianze)",
            amand_chapter_actual="Grégoire de Nazianze (note suppl. au ch. Basile)",
            extra={
                "birth_date": "c. 329/330 CE",
                "death_date": "389 CE",
                "role": "bishop, theologian, poet",
                "school": "Cappadocian Fathers",
                "collaboration": "Philocalia of Origen (with Basil of Caesarea)",
                "amand_treatment": "Note supplémentaire au ch. VIII Basile (p. 401-404)",
                "principal_works": [
                    "Orationes (45)",
                    "Carmina dogmatica",
                    "Carmina theologica",
                    "Letters (~250)",
                ],
            },
        ),
        confidence=0.95,
    ),
]


# =============================================================================
# 2. NEW WORKS (5)
# =============================================================================

NEW_WORKS: list[dict[str, Any]] = [
    _node(
        id="work_eusebius_contra_hieroclem",
        type="work",
        label="Contra Hieroclem (Πρὸς τὰ ὑπὸ Φιλοστράτου εἰς Ἀπολλώνιον)",
        description=(
            "Réfutation par Eusèbe (c. 312 CE, peu après la mort de Galère en 311) du "
            "Λόγος φιλαλήθης d'Hiéroclès, gouverneur de Bithynie, qui avait soutenu la "
            "supériorité d'Apollonios de Tyane sur Jésus. Pour Amand 1945 (p. 362-364, "
            "369-376), les chapitres 45 à 48 de cet opuscule constituent un parallèle "
            "interne à PE VI.6 : Eusèbe y dénonce le fatalisme absolu du thaumaturge "
            "néoplatonicien avec les mêmes arguments carnéadiens (marionnettes "
            "νευροσπαστούμεναι, abolition de la responsabilité, anéantissement de la "
            "louange et du blâme). Texte fortement maniéré mais de ton modéré."
        ),
        description_en=(
            "Eusebius' refutation (c. 312 CE, shortly after Galerius' death in 311) of "
            "Hierocles' Logos philalethes, in which Hierocles, governor of Bithynia, "
            "had argued Apollonius of Tyana's superiority to Jesus. For Amand 1945 "
            "(p. 362-364, 369-376), chapters 45-48 of this opusculum constitute an "
            "internal parallel to PE VI.6: Eusebius denounces the absolute fatalism of "
            "the Neoplatonic thaumaturge using the same Carneadean arguments "
            "(marionettes neurospastoumenai, abolition of responsibility, "
            "annihilation of praise and blame). A heavily mannered text but moderate "
            "in tone."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 362-364, 369-376",
            md_line_range="ll. 18695-19376",
            chapter="Livre II Ch. VII (Eusèbe) §III.1 + parallèles",
            amand_chapter_actual="Eusèbe de Césarée",
            extra={
                "composition_date": "c. 311-313 CE (Schwartz)",
                "editions": [
                    {"raw": "Olearius, Opera Philostrati, Leipzig 1709, p. 511-545"},
                    {"raw": "Migne PG 22.795-868"},
                    {"raw": "C. L. Kayser, Flavii Philostrati opera I, Teubner, Leipzig 1870, p. 369-413"},
                ],
                "amand_parallel_to": "PE VI.6 (anti-fatalism argumentation)",
            },
        ),
    ),
    _node(
        id="work_eusebius_demonstratio_evangelica",
        type="work",
        label="Demonstratio Evangelica (Εὐαγγελικὴ Ἀπόδειξις)",
        description=(
            "Démonstration évangélique d'Eusèbe (c. 320 CE), complément positif à la "
            "Préparation évangélique. 20 livres composés, 10 préservés (livres I-X). "
            "Pour Amand 1945 (p. 354-355), Eusèbe y affirme à plusieurs reprises le "
            "libre arbitre humain, en termes étroitement origéniens. Amand cite deux "
            "passages caractéristiques (IV.1.4 et IV.6.7-8) où les âmes humaines "
            "reçoivent une 'nature indépendante et libre, douée d'un choix spontané "
            "entre le bien ou le mal' (texte grec : ἄφετον καὶ ἐλεύθερον ἐπὶ τῆς "
            "αὐθεκουσίου περὶ τὸ καλὸν ἢ τοὐναντίον αἱρέσεως)."
        ),
        description_en=(
            "Eusebius' Demonstratio Evangelica (c. 320 CE), positive complement to the "
            "Praeparatio. Originally 20 books, 10 preserved (Books I-X). For Amand 1945 "
            "(p. 354-355), Eusebius repeatedly affirms human free will in tightly "
            "Origenian terms. Amand cites two characteristic passages (IV.1.4 and "
            "IV.6.7-8) where human souls receive 'an independent and free nature, "
            "endowed with spontaneous choice between good and the contrary' (Greek text: "
            "apheton kai eleutheron epi tes authekousiou peri to kalon e tounantion "
            "haireseos)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 354-355",
            md_line_range="ll. 18375-18460",
            chapter="Livre II Ch. VII §II (Eusèbe défenseur du libre arbitre)",
            amand_chapter_actual="Eusèbe de Césarée",
            extra={
                "composition_date": "c. 318-323 CE",
                "books_preserved": "I-X (of 20 composed)",
                "editions": [
                    {"raw": "I. A. Heikel, Die Demonstratio evangelica, GCS 23, Leipzig 1913"},
                    {"raw": "Migne PG 22"},
                ],
                "amand_cited_passages": ["IV.1.4", "IV.6.7-8", "IV.9.5", "IV.10.1"],
            },
        ),
    ),
    _node(
        id="work_basil_hexaemeron",
        type="work",
        label="Homiliae in Hexaemeron (Ὁμιλίαι εἰς τὴν Ἑξαήμερον)",
        description=(
            "Neuf homélies de Basile de Césarée prêchées vers 378 CE sur les six jours "
            "de la création (Gn 1). Pour Amand 1945 (p. 393-400), **les chapitres 5, 6 "
            "et 7 de la sixième homélie constituent le point de départ de toute son "
            "étude sur la transmission de l'argumentation antifataliste de Carnéade** "
            "(cf. avant-propos d'Amand). Hex VI.5-7 est une violente digression "
            "antiastrologique : Basile y montre l'impossibilité d'une observation "
            "exacte du ciel à l'instant de naissance (reprenant un argument de "
            "Carnéade), raille les portraits des 'Crianien', 'Taurien', 'Scorpien' "
            "(extraits d'un ζῳδιολόγιον populaire identifié par Bidez 1938), et "
            "applique deux topoï carnéadiens : (a) inutilité de la législation, des "
            "juges, des artisans ; (b) destruction des espérances chrétiennes."
        ),
        description_en=(
            "Nine homilies by Basil of Caesarea preached c. 378 CE on the six days of "
            "creation (Gen 1). For Amand 1945 (p. 393-400), **chapters 5, 6 and 7 of "
            "the sixth homily are the very starting point of his entire study of the "
            "transmission of Carneades' antifatalist argumentation** (cf. Amand's "
            "foreword). Hexaemeron VI.5-7 is a violent antiastrological digression: "
            "Basil demonstrates the impossibility of exact celestial observation at the "
            "moment of birth (taking up a Carneadean argument), ridicules the portraits "
            "of the 'Crianien', 'Taurien', 'Scorpien' types (extracts from a popular "
            "zodiologion identified by Bidez 1938), and deploys two Carneadean topoi: "
            "(a) uselessness of legislation, judges, craftsmen; (b) destruction of "
            "Christian hopes."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 393-400",
            md_line_range="ll. 20564-20935",
            chapter="Livre II Ch. VIII §III-IV (Hex VI.5-7 = point de départ d'Amand)",
            amand_chapter_actual="Basile le Grand",
            extra={
                "cts_urn_candidate": "urn:cts:greekLit:tlg2040.tlg004",
                "composition_date": "c. 378 CE",
                "homily_count": 9,
                "editions": [
                    {"raw": "Garnier-Maran, Paris 1721/1722, t. I"},
                    {"raw": "Migne PG 29.4-208"},
                    {"raw": "S. Giet, Homélies sur l'Hexaéméron, SC 26, Cerf, Paris 1949 (2e éd. 1968)"},
                    {"raw": "M. Naldini, Sulla Genesi (Omelie sull'Esamerone), Mondadori, Milan 1990"},
                ],
                "amand_pivot_text": "VI.5-7 (anti-astrological digression — Amand's starting point)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="work_basil_homiliae_quod_deus_non_est_auctor_malorum",
        type="work",
        label="Homilia: Quod Deus non est auctor malorum (Ὅτι οὐκ ἔστιν αἴτιος τῶν κακῶν ὁ Θεός)",
        description=(
            "Homélie de Basile 'Que Dieu n'est pas l'auteur du mal' (GARNIER-MARAN II, "
            "p. 720-83A = PG 31.329A-353A). Pour Amand 1945 (p. 391-393), cette "
            "homélie 'reproduit avec exactitude la théodicée origénienne' : le mal "
            "physique est envoyé par Dieu pour notre utilité ; le péché seul est le "
            "vrai mal, et il provient uniquement du mauvais usage du libre arbitre. "
            "Amand cite le ch. 6 (PG 31.344BC) où Basile articule l'âme comme libre "
            "image de Dieu, et le ch. 7 (PG 31.345B) avec la formule centrale : "
            "τὸ ἐφ' ἡμῖν ἐστι τὸ αὐτεξούσιον (l'autonomie morale, voilà précisément le "
            "libre arbitre). Réminiscences du Phèdre platonicien notées par Amand."
        ),
        description_en=(
            "Basil's homily 'That God is not the Author of Evils' (GARNIER-MARAN II, "
            "p. 720-83A = PG 31.329A-353A). For Amand 1945 (p. 391-393), this homily "
            "'reproduces with exactitude the Origenian theodicy': physical evil is sent "
            "by God for our benefit; sin alone is the true evil, arising solely from "
            "misuse of free will. Amand cites ch. 6 (PG 31.344BC) where Basil "
            "articulates the soul as the free image of God, and ch. 7 (PG 31.345B) with "
            "the central formula: to eph' hemin esti to autexousion (moral autonomy is "
            "precisely free will). Reminiscences of Plato's Phaedrus noted by Amand."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 391-393",
            md_line_range="ll. 20483-20603",
            chapter="Livre II Ch. VIII §II (Basile défenseur du libre arbitre)",
            amand_chapter_actual="Basile le Grand",
            extra={
                "editions": [
                    {"raw": "Garnier-Maran, t. II, Paris 1722, p. 720 — 83A"},
                    {"raw": "Migne PG 31.329A-353A"},
                ],
                "amand_central_formula": "τὸ ἐφ' ἡμῖν ἐστι τὸ αὐτεξούσιον (Hom. 7, PG 31.345B)",
            },
        ),
    ),
    _node(
        id="work_gregory_naz_carmina_dogmatica",
        type="work",
        label="Carmina dogmatica (Ἔπη δογματικά)",
        description=(
            "Poèmes dogmatiques de Grégoire de Nazianze (PG 37.397-522), pièces "
            "didactiques en vers — surtout hexamètres dactyliques imités d'Homère — "
            "couvrant divers articles de la doctrine chrétienne. Pour Amand 1945 "
            "(p. 401-404), le **Carmen dogmaticum 5 Περὶ προνοίας (PG 37.424-429)** "
            "contient un écho explicite de l'argumentation antifataliste de Carnéade : "
            "(a) destinées divergentes sous une même constellation — un roi vs un "
            "orateur, un marchand, un vagabond (vers 19-24) ; (b) destruction des lois "
            "de la vie si le Zodiaque produit toutes choses (vers 44-52). Amand "
            "souligne qu'il s'agit d'un 'écho dégradé', preuve que l'argumentation "
            "carnéadienne 'était devenue un lieu commun d'école' à la fin du IVᵉ siècle."
        ),
        description_en=(
            "Doctrinal Poems of Gregory of Nazianzus (PG 37.397-522), didactic verse "
            "pieces — mainly dactylic hexameters imitating Homer — covering various "
            "articles of Christian doctrine. For Amand 1945 (p. 401-404), **Carmen "
            "dogmaticum 5 Peri pronoias (PG 37.424-429)** contains an explicit echo of "
            "Carneades' antifatalist argumentation: (a) divergent fates under the same "
            "constellation — a king versus an orator, a merchant, a vagabond (lines "
            "19-24); (b) destruction of the laws of life if the Zodiac produces all "
            "things (lines 44-52). Amand stresses this is a 'degraded echo', proof that "
            "Carneadean argumentation 'had become a schoolroom commonplace' by the "
            "late 4th century."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 401-404",
            md_line_range="ll. 20973-21130",
            chapter="Livre II Ch. VIII Note suppl. (Grégoire de Nazianze)",
            amand_chapter_actual="Grégoire de Nazianze",
            extra={
                "editions": [
                    {"raw": "Clémencet-de Cosniac-de Verneuil-Caillau (Maurists), Paris 1840, t. II, col. 224-229"},
                    {"raw": "Migne PG 37.397-522 (Carm. dogm. 5: col. 424A-429A)"},
                ],
                "amand_cited_poem": "Carm. dogm. 5 Peri pronoias (PG 37.424A-429A)",
                "amand_significance": "degraded echo — Carneadean argument become schoolroom commonplace",
            },
        ),
    ),
]


# =============================================================================
# 3. NEW SYNTHESIS ARGUMENTS (11)
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    # ---- Eusèbe (5) ----
    _node(
        id="synthesis_amand1945_eus_witness_n4",
        type="argument",
        label="Amand 1945: Eusebius as the fourth Carneadean witness (PE VI.6)",
        description=(
            "Synthèse Amand : Eusèbe constitue le quatrième témoin canonique de la "
            "transmission de l'argumentation morale antifataliste de Carnéade — après "
            "Philon (témoin n°1, De providentia), Alexandre d'Aphrodise (témoin n°2, "
            "De Fato 16-20) et Firmicus Maternus (témoin n°3, Mathesis). Le 'texte "
            "témoin' eusébien (Praep. ev. VI.6.4-21) comporte sept arguments structurés "
            "plus une conclusion psychologique, soit deux arguments de plus que la "
            "trame d'Alexandre. Amand juge cette 'gerbe de preuves habiles, subtiles, "
            "abondantes et frappant droit au but' comme ne pouvant être 'originairement "
            "liée que par l'intelligence fine et puissante du grand philosophe "
            "Carnéade' (p. 369). La source littéraire intermédiaire d'Eusèbe demeure "
            "indéterminée."
        ),
        description_en=(
            "Amand synthesis: Eusebius constitutes the fourth canonical witness of the "
            "transmission of Carneades' moral antifatalist argumentation — after Philo "
            "(witness 1, De providentia), Alexander of Aphrodisias (witness 2, De Fato "
            "16-20) and Firmicus Maternus (witness 3, Mathesis). The Eusebian 'witness "
            "text' (Praep. ev. VI.6.4-21) contains seven structured arguments plus a "
            "psychological conclusion — two more than Alexander's framework. Amand "
            "judges this 'sheaf of skilful, subtle, abundant proofs striking straight to "
            "the target' as 'originally bound only by the fine and powerful mind of the "
            "great philosopher Carneades' (p. 369). Eusebius' intermediate literary "
            "source remains undetermined."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 342-381",
            md_line_range="ll. 17876-20099",
            chapter="Livre II Ch. VII §IV (Un important 'texte témoin' de Carnéade)",
            amand_chapter_actual="Eusèbe de Césarée — synthèse globale",
            extra={
                "amand_witness_rank": 4,
                "arguments_structured_count": 7,
                "compared_to_alexander_de_fato": "PE VI.6 has 7 args vs Alexander's 5",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_eus_carneadean_source_question",
        type="argument",
        label="Amand 1945: open question on Eusebius' Carneadean intermediate source",
        description=(
            "Synthèse Amand : la question de la source littéraire intermédiaire utilisée "
            "par Eusèbe pour PE VI.6.4-21 reste ouverte. Amand : 'Nous devons "
            "provisoirement laisser ouverte la question de savoir si Eusèbe reproduit "
            "fidèlement ou s'il développe par des procédés littéraires l'argumentation "
            "originale de Carnéade. Nous ignorons aussi la source littéraire dont il "
            "s'est inspiré, ou qu'il a démarquée, ou qu'il a simplement copiée' (p. 368). "
            "Néanmoins le caractère carnéadien des sept arguments + conclusion est "
            "incontestable. P. Henry (1935) a démontré la fidélité philologique générale "
            "d'Eusèbe à ses sources, ce qui plaide pour une reproduction proche."
        ),
        description_en=(
            "Amand synthesis: the question of Eusebius' intermediate literary source for "
            "PE VI.6.4-21 remains open. Amand: 'We must provisionally leave open the "
            "question whether Eusebius faithfully reproduces, or develops through "
            "literary procedures, Carneades' original argumentation. We are also "
            "ignorant of the literary source he drew on, dressed up, or merely copied' "
            "(p. 368). Yet the Carneadean character of the seven arguments + conclusion "
            "is incontestable. P. Henry (1935) demonstrated Eusebius' general "
            "philological fidelity to his sources, supporting close reproduction."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 368-369",
            md_line_range="ll. 19002-19030",
            chapter="Livre II Ch. VII §IV.1 (Introduction au 'texte témoin')",
            amand_chapter_actual="Eusèbe de Césarée — méthode",
            extra={"open_question": "Carneadean source identity for Eusebius"},
        ),
    ),
    _node(
        id="synthesis_amand1945_eus_psychological_argument_modernity",
        type="argument",
        label="Amand 1945: 'modern' allure of Eusebius' psychological conclusion (PE VI.6.20-21)",
        description=(
            "Synthèse Amand : la conclusion psychologique d'Eusèbe (PE VI.6.20-21), "
            "fondée sur la conscience immédiate de notre προαίρεσις (parallèle "
            "douleur/plaisir/vision/audition), a selon Amand 'une allure si moderne' "
            "(p. 355-356). Toutefois Amand admet — en s'appuyant sur Robin 1938 — qu'il "
            "est probable que Carnéade ait lui-même 'insisté sur le sentiment que nous "
            "avons d'être libres'. Amand : 'J'estime probable l'opinion qui voit, dans "
            "la seconde partie du septième argument et dans la conclusion, la pensée "
            "même de Carnéade à laquelle Eusèbe ou sa source a donné un tour dogmatique "
            "et catégorique' (p. 377)."
        ),
        description_en=(
            "Amand synthesis: Eusebius' psychological conclusion (PE VI.6.20-21), based "
            "on the immediate consciousness of our prohairesis (parallel to "
            "pain/pleasure/sight/hearing), has according to Amand 'so modern an air' "
            "(p. 355-356). However Amand grants — relying on Robin 1938 — that Carneades "
            "himself probably 'insisted on the feeling we have of being free'. Amand: "
            "'I judge probable the opinion that sees, in the second half of the seventh "
            "argument and in the conclusion, the very thought of Carneades, to which "
            "Eusebius or his source gave a dogmatic and categorical turn' (p. 377)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 355-356, 376-377",
            md_line_range="ll. 18437-18460, 19370-19502",
            chapter="Livre II Ch. VII §II + §IV.2 (conclusion VI.6.21)",
            amand_chapter_actual="Eusèbe de Césarée — argument 7 + conclusion",
            extra={
                "amand_attribution_probability": "probable Carneades source for arg 7b + conclusion",
                "modern_secondary_source": "L. Robin, La morale antique, Paris 1938, p. 166-167",
            },
        ),
    ),
    _node(
        id="synthesis_amand1945_eus_dependence_origen",
        type="argument",
        label="Amand 1945: Eusebius as faithful disciple of Origen (free will doctrine)",
        description=(
            "Synthèse Amand : Eusèbe répète la doctrine origénienne du libre arbitre "
            "'sans la moindre originalité' (p. 354). 'Chrétien et origéniste, le "
            "disciple et l'ami de Pamphile ne manque aucune occasion d'insister sur le "
            "libre arbitre, qu'il présuppose comme condition de sa théologie du péché "
            "et du salut par le Christ.' La théodicée d'Eusèbe (PE VI.6.22-73) est "
            "'entièrement origénienne', organisée autour de l'axiome de l'hiérophante "
            "de la République : αἰτία ἑλομένου, θεὸς ἀναίτιος. La transmission "
            "philologique passe par la dissertation antiastrologique d'Origène "
            "(Comm. in Gen. tome III) que Eusèbe cite quasi-littéralement en PE VI.11 "
            "(parallèle Philocalia 23 de Basile et Grégoire de Nazianze)."
        ),
        description_en=(
            "Amand synthesis: Eusebius repeats Origen's doctrine of free will 'without "
            "the slightest originality' (p. 354). 'A Christian and Origenist, the "
            "disciple and friend of Pamphilus never misses an occasion to insist on "
            "free will, which he presupposes as condition of his theology of sin and "
            "salvation through Christ.' Eusebius' theodicy (PE VI.6.22-73) is "
            "'entirely Origenian', organised around the Republic's hierophant axiom: "
            "aitia helomenou, theos anaitios. Philological transmission runs through "
            "Origen's anti-astrological dissertation (Comm. in Gen. III) which Eusebius "
            "cites near-literally in PE VI.11 (parallel to Philocalia 23 by Basil and "
            "Gregory of Nazianzus)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 354-355, 365-367",
            md_line_range="ll. 18375-18460, 18918-18987",
            chapter="Livre II Ch. VII §II + §III.3 (origénisme et PE VI.11)",
            amand_chapter_actual="Eusèbe de Césarée — origénisme",
            extra={
                "filiation": "Origen Comm. in Gen. → Eusebius PE VI.11 (≈ Philocalia 23)",
                "axiom": "αἰτία ἑλομένου, θεὸς ἀναίτιος (Plato Rep.)",
            },
        ),
    ),
    _node(
        id="synthesis_amand1945_eus_philological_fidelity",
        type="argument",
        label="Amand 1945: Eusebius' philological fidelity (Henry 1935)",
        description=(
            "Synthèse Amand : la fidélité d'Eusèbe à ses sources excerptées est "
            "démontrée par P. Henry (1935, p. 16-26). Amand rapporte (p. 357-358) : "
            "'Avec quelle fidélité Eusèbe a-t-il copié les ouvrages originaux ? Des "
            "exemples bien choisis amènent à la conclusion qu'Eusèbe n'a nullement "
            "altéré les textes qu'il excerptait. Les comparaisons faites entre la "
            "Préparation évangélique et les meilleurs manuscrits de Platon, de Philon "
            "et de Plutarque prouvent à l'évidence la minutieuse fidélité de l'évêque "
            "de Césarée.' Cette fidélité fait du livre VI de la PE une source de "
            "première main pour les fragments perdus de Carnéade (via source "
            "intermédiaire), Diogénianos, Alexandre, Bardesane, Origène."
        ),
        description_en=(
            "Amand synthesis: Eusebius' fidelity to his excerpted sources is "
            "demonstrated by P. Henry (1935, p. 16-26). Amand reports (p. 357-358): "
            "'With what fidelity did Eusebius copy the original works? Well-chosen "
            "examples lead to the conclusion that Eusebius in no way altered the texts "
            "he excerpted. Comparisons made between the Praeparatio evangelica and the "
            "best manuscripts of Plato, Philo and Plutarch evidently prove the "
            "scrupulous fidelity of the bishop of Caesarea.' This fidelity makes PE "
            "Book VI a first-hand source for the lost fragments of Carneades (via "
            "intermediate source), Diogenianus, Alexander, Bardaisan, Origen."
        ),
        period="modern",
        metadata=amand_metadata(
            page_range="p. 357-358",
            md_line_range="ll. 18497-18550",
            chapter="Livre II Ch. VII §III (méthode philologique d'Eusèbe)",
            amand_chapter_actual="Eusèbe de Césarée — méthode philologique",
            extra={
                "source_authority": "P. Henry, Recherches sur la Préparation évangélique d'Eusèbe, Paris 1935, p. 16-26",
            },
        ),
    ),

    # ---- Basile (4) ----
    _node(
        id="synthesis_amand1945_basil_hex_vi_7_amand_origin_point",
        type="argument",
        label="Amand 1945: Hexaemeron VI.5-7 as Amand's own starting point",
        description=(
            "Synthèse Amand de premier ordre : les chapitres 5, 6 et 7 de la sixième "
            "homélie de l'Hexaéméron de Basile constituent **le point de départ "
            "explicite de toute l'enquête d'Amand 1945**. Amand l'affirme dans son "
            "avant-propos : 'Le point de départ fut une étude approfondie des chapitres "
            "5, 6 et 7 de la sixième homélie de l'Hexaéméron au cours desquels Basile "
            "de Césarée engage une violente et sarcastique polémique contre les "
            "Chaldéens et l'astrologie fataliste. Étendant progressivement le champ de "
            "nos recherches, nous nous sommes aperçu qu'un même type d'argumentation "
            "revenait fréquemment dans la controverse antifataliste. Cette "
            "argumentation tirée des conséquences morales désastreuses de la doctrine "
            "de l'εἱμαρμένη, il nous fut aisé de l'identifier : c'était celle que "
            "Carnéade avait sinon inventée, du moins aiguisée et popularisée dans sa "
            "lutte contre le dogmatisme stoïcien.' Ce nœud constitue donc la racine "
            "génétique de la thèse d'Amand sur la transmission carnéadienne."
        ),
        description_en=(
            "First-order Amand synthesis: chapters 5, 6 and 7 of the sixth homily of "
            "Basil's Hexaemeron are **the explicit starting point of Amand's entire "
            "1945 investigation**. Amand states in his foreword: 'The starting point was "
            "a thorough study of chapters 5, 6 and 7 of the sixth homily of the "
            "Hexaemeron, in which Basil of Caesarea engages in a violent and sarcastic "
            "polemic against the Chaldaeans and fatalist astrology. Progressively "
            "extending the field of our research, we noticed that the same type of "
            "argumentation recurred frequently in the antifatalist controversy. This "
            "argumentation drawn from the disastrous moral consequences of the doctrine "
            "of heimarmene, we easily identified: it was the one that Carneades had if "
            "not invented, then at least sharpened and popularised in his struggle "
            "against Stoic dogmatism.' This node is thus the genetic root of Amand's "
            "transmission thesis."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 383-400 (and foreword)",
            md_line_range="ll. 200-231, 20100-20935",
            chapter="Livre II Ch. VIII §III-IV (Hexaéméron VI.5-7)",
            amand_chapter_actual="Basile le Grand — point de départ d'Amand",
            extra={
                "amand_origin_quote": "Le point de départ fut une étude approfondie des chapitres 5, 6 et 7 de la sixième homélie de l'Hexaéméron",
                "thesis_genesis": "Hex VI.5-7 → identification of Carneadean argumentation pattern in patristic literature",
            },
        ),
        confidence=0.98,
    ),
    _node(
        id="synthesis_amand1945_basil_only_two_carneadean_topoi",
        type="argument",
        label="Amand 1945: Basil deploys only two explicit Carneadean topoi (Hex VI.7)",
        description=(
            "Synthèse Amand : Basile ne reproduit ni ne résume l'ensemble de "
            "l'argumentation carnéadienne. Il n'amplifie que **deux topoï explicites** : "
            "(a) l'inutilité de la législation, des tribunaux et des efforts des "
            "artisans si vertu et vice ne sont que résultats de la contrainte "
            "astrologique ; (b) la destruction de la religion + adaptation chrétienne : "
            "anéantissement des espérances eschatologiques. Amand : 'Ce qui "
            "m'empêcherait d'y voir un texte témoin, c'est uniquement le fait qu'il ne "
            "contient explicitement que deux arguments carnéadiens, tandis que les "
            "textes témoins que j'ai retenus comportent au moins trois ou quatre chefs "
            "largement exposés' (p. 399). Basile est donc dépositaire mais non témoin "
            "canonique."
        ),
        description_en=(
            "Amand synthesis: Basil neither reproduces nor summarises Carneades' "
            "argumentation as a whole. He amplifies only **two explicit topoi**: "
            "(a) uselessness of legislation, courts and craftsmen's efforts if virtue "
            "and vice are merely results of astrological constraint; (b) destruction of "
            "religion + Christian adaptation: annihilation of eschatological hope. "
            "Amand: 'What prevents me from seeing here a witness text is solely the fact "
            "that it explicitly contains only two Carneadean arguments, whereas the "
            "witness texts I have retained comprise at least three or four amply "
            "exposed heads' (p. 399). Basil is thus a depositary but not a canonical "
            "witness."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 398-399",
            md_line_range="ll. 20803-20880",
            chapter="Livre II Ch. VIII §IV (utilisation de Carnéade chez Basile)",
            amand_chapter_actual="Basile le Grand — économie de la réception",
            extra={
                "amand_witness_status": "depositary, not canonical witness",
                "carneadean_topoi_count": 2,
                "canonical_witness_threshold": "≥3-4 amply exposed arguments",
            },
        ),
    ),
    _node(
        id="synthesis_amand1945_basil_origen_christian_insertion",
        type="argument",
        label="Amand 1945: Basil inserts Origenian Christian element in philosophical demonstration",
        description=(
            "Synthèse Amand : la 'phrase chrétienne' insérée par Basile dans une "
            "démonstration exclusivement philosophique — concernant l'anéantissement "
            "des espérances chrétiennes par le fatalisme — a probablement été inspirée "
            "par Origène, dans le Commentaire de la Genèse (Philocalia 23.1). Amand "
            "(p. 399-400) : 'l'élément chrétien, tout adventice, inséré dans une "
            "démonstration exclusivement philosophique, a grande chance d'avoir été "
            "inspiré par Origène. Le maître alexandrin, après avoir affirmé que le "
            "fatalisme ruine la liberté, montrait les conséquences de l'εἱμαρμένη en "
            "ce qui concerne la religion du Christ : la prédication de l'Évangile a "
            "été vaine ; les menaces divines aux pécheurs sans objet ; les récompenses "
            "et béatitudes promises aux justes disparaissent ; la foi chrétienne "
            "devient superflue.'"
        ),
        description_en=(
            "Amand synthesis: the 'Christian sentence' inserted by Basil in an "
            "exclusively philosophical demonstration — concerning the annihilation of "
            "Christian hopes by fatalism — was probably inspired by Origen, in the "
            "Commentary on Genesis (Philocalia 23.1). Amand (p. 399-400): 'the wholly "
            "adventitious Christian element inserted in an exclusively philosophical "
            "demonstration has every chance of having been inspired by Origen. The "
            "Alexandrian master, after asserting that fatalism ruins freedom, showed "
            "the consequences of heimarmene for the religion of Christ: Gospel "
            "preaching has been in vain; divine threats to sinners are pointless; "
            "rewards and beatitudes promised to the just vanish; Christian faith "
            "becomes superfluous.'"
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 399-400",
            md_line_range="ll. 20879-20935",
            chapter="Livre II Ch. VIII §IV (filiation Origène→Basile)",
            amand_chapter_actual="Basile le Grand — dépendance origénienne",
            extra={
                "amand_source_for_christian_insertion": "Origen Comm. in Gen. = Philocalia 23.1 (Robinson 1893, p. 188)",
            },
        ),
    ),
    _node(
        id="synthesis_amand1945_basil_popular_homily_register",
        type="argument",
        label="Amand 1945: Hexaemeron VI as popular anti-Chaldean homily, not scientific anti-Ptolemy",
        description=(
            "Synthèse Amand : la digression antiastrologique de Basile (Hex VI.5-7) "
            "vise non l'astrologie scientifique des Ptolémée et autres généthliographes "
            "des observatoires, mais 'les confrères marrons des astrologues savants, "
            "ces bateleurs ignares, ces Chaldéens, qui, plus prestement et sans tant "
            "de cérémonie, disaient la bonne aventure dans leurs cabinets de "
            "consultation ou au coin des carrefours' (p. 394). 'Basile ne perd pas son "
            "temps à réfuter, minutieusement et à renfort de syllogismes, l'astrologie "
            "scientifique de Ptolémée et de ses pareils (il semble ignorer la "
            "Tétrabible). Pratique et s'adaptant au niveau intellectuel de son "
            "auditoire populaire, l'homéliste fait pleuvoir ses sarcasmes et ses "
            "invectives.' Le registre populaire explique l'absence d'argumentation "
            "technique."
        ),
        description_en=(
            "Amand synthesis: Basil's antiastrological digression (Hex VI.5-7) targets "
            "not the scientific astrology of Ptolemy and other observatory "
            "genethlialogists, but 'the dodgy colleagues of the learned astrologers, "
            "those ignorant mountebanks, those Chaldaeans who more swiftly and with "
            "less ceremony told fortunes in their consulting rooms or at street "
            "corners' (p. 394). 'Basil does not waste his time refuting Ptolemy's "
            "scientific astrology in minute syllogistic detail (he seems unaware of "
            "the Tetrabiblos). Practical and adapting to the intellectual level of his "
            "popular audience, the homilist rains down sarcasm and invective.' The "
            "popular register explains the absence of technical argumentation."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 393-394",
            md_line_range="ll. 20572-20646",
            chapter="Livre II Ch. VIII §III.1 (introduction à Hex VI.5-7)",
            amand_chapter_actual="Basile le Grand — registre populaire",
        ),
    ),

    # ---- Grégoire de Nazianze (2) ----
    _node(
        id="synthesis_amand1945_greg_naz_carmen_dogm_5_carneadean_echo",
        type="argument",
        label="Amand 1945: Carneadean echo in Gregory of Nazianzus Carm. dogm. 5",
        description=(
            "Synthèse Amand : le poème dogmatique 5 Περὶ προνοίας (PG 37.424-429) de "
            "Grégoire de Nazianze, en hexamètres dactyliques imités d'Homère, "
            "reproduit en écho deux arguments antifatalistes carnéadiens : "
            "(a) destinées divergentes sous une même constellation — 'un roi est né "
            "sous le même astre que plusieurs hommes : parmi ceux-ci il y en a de bons "
            "et de mauvais, tel est orateur, un autre marchand, un autre enfin "
            "vagabond' (vers 19-24) ; (b) destruction des lois de la vie + abolition "
            "de l'impulsion volontaire vers le bien si le Zodiaque produit tout "
            "(vers 44-52). Amand : 'Écho assurément, mais écho remarquablement distinct "
            "du fameux argument néo-académique' (p. 403)."
        ),
        description_en=(
            "Amand synthesis: Gregory of Nazianzus' dogmatic poem 5 Peri pronoias "
            "(PG 37.424-429), in dactylic hexameters imitating Homer, reproduces by "
            "echo two Carneadean antifatalist arguments: (a) divergent fates under the "
            "same constellation — 'a king is born under the same star as several men: "
            "among them are good and bad, this one an orator, another a merchant, "
            "another finally a vagabond' (lines 19-24); (b) destruction of the laws of "
            "life + abolition of the voluntary impulse toward the good if the Zodiac "
            "produces everything (lines 44-52). Amand: 'An echo certainly, but a "
            "remarkably distinct echo of the famous neo-academic argument' (p. 403)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 401-403",
            md_line_range="ll. 20937-21071",
            chapter="Livre II Ch. VIII Note suppl. (Grégoire de Nazianze)",
            amand_chapter_actual="Grégoire de Nazianze — Carm. dogm. 5",
            extra={
                "amand_cited_verses": "Carm. dogm. 5, vers 19-24, 44-52",
                "amand_echo_status": "distinct but degraded echo of neo-academic argument",
            },
        ),
    ),
    _node(
        id="synthesis_amand1945_greg_naz_school_commonplace",
        type="argument",
        label="Amand 1945: Carneadean argumentation as 4th-century schoolroom commonplace",
        description=(
            "Synthèse Amand : la présence de l'écho carnéadien chez Grégoire de "
            "Nazianze démontre une thèse plus générale de la diffusion. Amand "
            "(p. 401) : 'L'argumentation éthique antifataliste du fondateur de la "
            "Nouvelle Académie était devenue, bien avant le IVᵉ siècle, un lieu "
            "commun d'école. Elle s'était progressivement vidée de son contenu "
            "original et transformée en une idée banale et impersonnelle, incorporée "
            "au bagage intellectuel de tous les partisans du libre arbitre et en "
            "particulier des docteurs chrétiens.' Cette thèse de Diffusion vs "
            "Filiation explique pourquoi un même topos peut se trouver chez plusieurs "
            "auteurs sans dépendance littéraire directe — utile pour évaluer la "
            "transmission carnéadienne ailleurs (Cyrille de Jérusalem, Chrysostome, "
            "Commentateur arien)."
        ),
        description_en=(
            "Amand synthesis: the presence of the Carneadean echo in Gregory of "
            "Nazianzus demonstrates a more general diffusion thesis. Amand (p. 401): "
            "'The ethical antifatalist argumentation of the founder of the New Academy "
            "had become, well before the 4th century, a schoolroom commonplace. It had "
            "progressively been emptied of its original content and transformed into a "
            "banal and impersonal idea, incorporated into the intellectual baggage of "
            "all partisans of free will and particularly of the Christian doctors.' "
            "This Diffusion vs Filiation thesis explains why the same topos can appear "
            "in multiple authors without direct literary dependence — useful for "
            "assessing Carneadean transmission elsewhere (Cyril of Jerusalem, "
            "Chrysostom, Arian commentator on Job)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 401",
            md_line_range="ll. 20937-20949",
            chapter="Livre II Ch. VIII Note suppl. (intro Grégoire de Nazianze)",
            amand_chapter_actual="Grégoire de Nazianze — diffusion vs filiation",
        ),
    ),
]


# =============================================================================
# 4. NEW ARGUMENTS (15 — 9 Eusèbe pivots + 5 Basile + 1 Gr. Naz)
# =============================================================================

def _arg_eus(idx: int, *, label: str, fr: str, en: str, line_range: str, vi_6_section: str,
             pe_chapter: str = "VI.6") -> dict[str, Any]:
    """Helper for the 9 Eusèbe argument-pivots."""
    return _node(
        id=f"argument_eus_carneadean_pe_vi_6_{idx}",
        type="argument",
        label=label,
        description=fr,
        description_en=en,
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 369-376",
            md_line_range=line_range,
            chapter=f"Livre II Ch. VII §IV.2 (PE {pe_chapter}.{vi_6_section})",
            amand_chapter_actual="Eusèbe de Césarée — argument carnéadien",
            extra={
                "pe_reference": f"Praep. Ev. {pe_chapter}.{vi_6_section}",
                "amand_witness_rank": 4,
            },
        ),
    )


NEW_ARGUMENTS: list[dict[str, Any]] = [
    # ---- Eusèbe — 9 arguments-pivots ----
    _arg_eus(
        idx="general_theme",
        label="Eusebius PE VI.6.5: General theme — fatalism ruins morality, piety, religion",
        fr=(
            "Thème général d'Eusèbe PE VI.6.5 : 'En effet, s'il faut attribuer aux "
            "constellations et à l'εἱμαρμένη, non seulement les événements extérieurs, "
            "mais aussi les désirs et les volitions conformes à la raison, et si une "
            "inexorable Nécessité violente les pensées et les jugements de l'homme, "
            "c'en est fini de la morale, c'en est fait de la piété et de la "
            "religion.' Énoncé carnéadien posant le cadre des sept arguments suivants."
        ),
        en=(
            "Eusebius' general theme PE VI.6.5: 'For if one must attribute to the "
            "constellations and to heimarmene not only external events but also "
            "desires and rational volitions, and if an inexorable Necessity violates "
            "human thoughts and judgements, then morality is finished, piety and "
            "religion are done for.' Carneadean statement framing the seven subsequent "
            "arguments."
        ),
        line_range="ll. 19045-19052",
        vi_6_section="5",
    ),
    _arg_eus(
        idx="arg1_virtue_vice",
        label="Eusebius PE VI.6.5-7: Carneadean Arg 1 — Praise/blame, virtue/vice annulled",
        fr=(
            "Premier argument carnéadien chez Eusèbe (PE VI.6.5-7) : dans l'hypothèse "
            "du fatalisme absolu, louange et blâme, vertu et vice perdent toute "
            "raison d'être. Citation centrale (5-6) : 'Pour les honnêtes gens, elle "
            "n'existe plus la louange due à la vertu. L'amour que nous avons à "
            "l'égard de Dieu n'est plus qu'un mot. Le mérite des travaux que nous "
            "nous imposons disparaît également, si l'on proclame que le Destin et la "
            "Nécessité constituent la seule cause de tous les êtres.' Parallèle "
            "Alexandre De Fato 16 (Bruns p. 187, 2e argument 2e partie)."
        ),
        en=(
            "Eusebius' first Carneadean argument (PE VI.6.5-7): under absolute "
            "fatalism, praise/blame, virtue/vice lose all rationale. Central citation "
            "(5-6): 'For honest people, the praise due to virtue no longer exists. "
            "The love we have for God is just a word. The merit of the labours we "
            "impose on ourselves likewise disappears, if one proclaims that Destiny "
            "and Necessity are the sole cause of all beings.' Parallel: Alexander "
            "De Fato 16 (Bruns p. 187, 2nd argument part 2)."
        ),
        line_range="ll. 19053-19120",
        vi_6_section="5-7",
    ),
    _arg_eus(
        idx="arg2_indolence",
        label="Eusebius PE VI.6.8-10: Carneadean Arg 2 — Belief in fatalism breeds indolence",
        fr=(
            "Deuxième argument carnéadien (PE VI.6.8-10) : la croyance au fatalisme "
            "entraîne nécessairement le relâchement de l'effort, la négligence, "
            "l'indolence. Citation (9-10) : 'S'il pense que l'événement se produira "
            "par l'effet de l'εἱμαρμένη, que nous nous fatiguions et que nous "
            "prenions de la peine, ou que nous nous laissions aller à l'indolence, "
            "comment un tel homme ne serait-il pas porté à choisir le parti le plus "
            "facile ? On peut entendre de la bouche de la plupart des gens : Cela "
            "se fera, si mon destin l'a ainsi décidé.' Parallèle Alexandre De Fato 16 "
            "1re moitié (Bruns p. 186-187, 1er argument)."
        ),
        en=(
            "Eusebius' second Carneadean argument (PE VI.6.8-10): belief in fatalism "
            "necessarily produces slackening of effort, negligence, indolence. "
            "Citation (9-10): 'If he thinks the event will happen by effect of "
            "heimarmene, whether we tire ourselves and take pains or let ourselves "
            "go in indolence, how could such a man not be inclined to choose the "
            "easier course? One can hear from most people: This will happen if my "
            "destiny has so decided.' Parallel: Alexander De Fato 16 first half "
            "(Bruns p. 186-187, 1st argument)."
        ),
        line_range="ll. 19122-19164",
        vi_6_section="8-10",
    ),
    _arg_eus(
        idx="arg3_exhortations_useless",
        label="Eusebius PE VI.6.12-16: Carneadean Arg 3 — Exhortations, reproaches, reprimands useless",
        fr=(
            "Troisième argument carnéadien (PE VI.6.12-16) : sous le fatalisme, "
            "exhortations, reproches, réprimandes sont absurdes. Le réprimandé peut "
            "répondre : 'Pourquoi me réprimander ainsi ? Tous ces vices ne sont "
            "point miens. Il ne m'appartient pas de modifier ma résolution. C'est "
            "l'εἱμαρμένη qui me l'a imposée d'avance.' Argument anti-rhéteur "
            "particulièrement saillant chez Eusèbe — selon Amand (p. 371-373) il "
            "représente un développement ample que ne contient pas Alexandre."
        ),
        en=(
            "Eusebius' third Carneadean argument (PE VI.6.12-16): under fatalism, "
            "exhortations, reproaches and reprimands are absurd. The reprimanded can "
            "reply: 'Why reprimand me thus? None of these vices is mine. It is not "
            "for me to alter my decision. Heimarmene imposed it on me in advance.' "
            "Anti-rhetor argument particularly salient in Eusebius — per Amand "
            "(p. 371-373) representing an ample development not found in Alexander."
        ),
        line_range="ll. 19173-19232",
        vi_6_section="12-16",
    ),
    _arg_eus(
        idx="arg4_moral_action_proves_autonomy",
        label="Eusebius PE VI.6.16-17: Carneadean Arg 4 — Moral action proves internal autonomy",
        fr=(
            "Quatrième argument carnéadien (PE VI.6.16-17) : l'action morale "
            "elle-même implique la négation du fatalisme. Tout exhortateur, fût-il "
            "fataliste, prouve par sa conduite qu'il croit à l'autonomie. Citation : "
            "'N'est-il pas manifestement prouvé qu'un tel homme laisse subsister "
            "réellement l'autonomie de notre volonté, l'existence même de notre "
            "liberté ?' Argument auto-référentiel ad hominem. Parallèle Alexandre "
            "De Fato 18 (Bruns p. 188-189, 4e argument)."
        ),
        en=(
            "Eusebius' fourth Carneadean argument (PE VI.6.16-17): moral action "
            "itself implies the negation of fatalism. Any exhorter, even a fatalist, "
            "proves by his conduct that he believes in autonomy. Citation: 'Is it "
            "not manifestly proved that such a man really lets subsist the autonomy "
            "of our will, the very existence of our freedom?' Self-referential ad "
            "hominem argument. Parallel: Alexander De Fato 18 (Bruns p. 188-189, "
            "4th argument)."
        ),
        line_range="ll. 19234-19271",
        vi_6_section="16-17",
    ),
    _arg_eus(
        idx="arg5_laws_abolition",
        label="Eusebius PE VI.6.18: Carneadean Arg 5 — Laws, punishments, rewards abolished",
        fr=(
            "Cinquième argument carnéadien (PE VI.6.18) : le fatalisme absolu "
            "implique logiquement l'abolition des lois établies, ainsi que la "
            "suppression des châtiments et des récompenses. 'Que faut-il en effet "
            "commander ou interdire à des individus entravés et contraints par une "
            "nécessité extérieure ? Désormais il ne faudra plus châtier les "
            "criminels, qui pour cette même raison n'ont point mal agi. Il ne "
            "faudra pas non plus distribuer des récompenses et des honneurs à ceux "
            "qui ont accompli de nobles actions.' Cet argument apparaît dans tous "
            "les textes témoins mais pas comme tel dans Alexandre — c'est une "
            "spécificité d'Eusèbe (Amand p. 374-375 n. 1)."
        ),
        en=(
            "Eusebius' fifth Carneadean argument (PE VI.6.18): absolute fatalism "
            "logically entails abolition of established laws, suppression of "
            "punishments and rewards. 'What indeed should one command or forbid to "
            "individuals fettered and constrained by an external necessity? "
            "Henceforth criminals must not be punished, for that same reason they "
            "have not acted wrongly. Nor should rewards and honours be distributed "
            "to those who have accomplished noble actions.' This argument appears in "
            "all witness texts but not as such in Alexander — a specificity of "
            "Eusebius (Amand p. 374-375 n. 1)."
        ),
        line_range="ll. 19272-19294",
        vi_6_section="18",
    ),
    _arg_eus(
        idx="arg6_piety_destroyed",
        label="Eusebius PE VI.6.19: Carneadean Arg 6 — Piety toward divinity destroyed",
        fr=(
            "Sixième argument carnéadien (PE VI.6.19) : le fatalisme absolu ruine "
            "la piété envers le divin. 'Même si nous les prions et si nous "
            "accomplissons nos devoirs religieux à leur égard, Dieu et les "
            "divinités oraculaires ne peuvent en rien nous être secourables, car "
            "nous sommes enchaînés dans les liens fatals de l'εἱμαρμένη.' Parallèle "
            "Alexandre De Fato 17 (Bruns p. 188, 3e argument). Eusèbe avait déjà "
            "résumé cette objection en VI.2 et VI.3 (citant Porphyre)."
        ),
        en=(
            "Eusebius' sixth Carneadean argument (PE VI.6.19): absolute fatalism "
            "ruins piety toward the divine. 'Even if we pray to them and perform our "
            "religious duties to them, God and the oracular divinities cannot help "
            "us at all, for we are chained in the fatal bonds of heimarmene.' "
            "Parallel: Alexander De Fato 17 (Bruns p. 188, 3rd argument). Eusebius "
            "had already summarised this objection in VI.2 and VI.3 (citing "
            "Porphyry)."
        ),
        line_range="ll. 19295-19303",
        vi_6_section="19",
    ),
    _arg_eus(
        idx="arg7_marionettes_consciousness",
        label="Eusebius PE VI.6.20: Carneadean Arg 7 — Marionette metaphor, immediate consciousness",
        fr=(
            "Septième argument carnéadien (PE VI.6.20) : honte d'affirmer que nous "
            "sommes mus comme des inanimés, tirés par des ficelles comme des "
            "marionnettes (νευροσπαστουμένους) par une force extérieure. La "
            "conscience nous révèle, au contraire, que nous nous portons à des "
            "décisions par notre propre impulsion (ὁρμή) et choix (προαίρεσις). "
            "Métaphore carnéadienne identifiée par Amand comme attestée aussi en "
            "Contre Hiéroclès 45. Selon Amand (p. 376-377), la 2e moitié de cet "
            "argument + la conclusion (21) représentent probablement la pensée "
            "même de Carnéade à laquelle Eusèbe a donné un tour dogmatique."
        ),
        en=(
            "Eusebius' seventh Carneadean argument (PE VI.6.20): shame at claiming "
            "we are moved like inanimate things, pulled by strings like marionettes "
            "(neurospastoumenous) by external force. Consciousness reveals on the "
            "contrary that we are moved to decisions by our own impulse (horme) and "
            "choice (prohairesis). Carneadean metaphor identified by Amand as also "
            "attested in Contra Hieroclem 45. Per Amand (p. 376-377), the 2nd half "
            "of this argument plus the conclusion (21) probably represent Carneades' "
            "own thought to which Eusebius gave a dogmatic turn."
        ),
        line_range="ll. 19304-19354",
        vi_6_section="20",
    ),
    _arg_eus(
        idx="conclusion_autexousion",
        label="Eusebius PE VI.6.21: Carneadean Conclusion — autexousion as immediate evidence",
        fr=(
            "Conclusion d'Eusèbe (PE VI.6.21) sur l'évidence du libre arbitre : "
            "'Elle est donc évidente (ἐναργής), la doctrine du libre arbitre, aussi "
            "évidente que la conscience que nous avons que douleur et plaisir, "
            "vision et audition se perçoivent non par l'intermédiaire d'un "
            "syllogisme, mais directement par la sensation actuelle.' Affirmation "
            "centrale du αὐτεξούσιον (αὐθεκούσιον) de la nature rationnelle. Amand "
            "considère cette formulation comme probablement carnéadienne (cf. Robin "
            "1938, p. 166-167 sur le sentiment de liberté chez Carnéade) mais "
            "habillée d'un 'tour dogmatique et catégorique' par Eusèbe ou sa source."
        ),
        en=(
            "Eusebius' conclusion (PE VI.6.21) on the evidence of free will: 'So the "
            "doctrine of free will is evident (enarges), as evident as the "
            "consciousness we have that pain and pleasure, sight and hearing are "
            "perceived not via syllogism but directly by actual sensation.' Central "
            "affirmation of the autexousion (authekousion) of rational nature. Amand "
            "considers this formulation probably Carneadean (cf. Robin 1938, "
            "p. 166-167 on the feeling of freedom in Carneades) but clothed in a "
            "'dogmatic and categorical turn' by Eusebius or his source."
        ),
        line_range="ll. 19355-19376",
        vi_6_section="21",
    ),

    # ---- Basile — 5 arguments ----
    _node(
        id="argument_basil_carneadean_hex_vi_7_laws_useless",
        type="argument",
        label="Basil Hex VI.7: Carneadean topos — Legislators, judges, craftsmen useless under heimarmene",
        description=(
            "Premier topos carnéadien explicite chez Basile Hex VI.7 (PG 29.133BC) : "
            "si les principes de nos actes ne relèvent pas de notre libre arbitre, "
            "mais des fatalités de naissance, alors 'inutiles les législateurs qui "
            "nous prescrivent ce que nous devons accomplir et éviter ; inutiles les "
            "juges qui honorent la vertu et châtient la méchanceté. Aucune injustice "
            "n'est imputable au voleur et à l'assassin. L'agriculteur fera "
            "d'abondantes récoltes sans jeter de semence ; le marchand s'enrichira "
            "qu'il le veuille ou non.' Argument 5 carnéadien dans l'inventaire "
            "d'Amand."
        ),
        description_en=(
            "First explicit Carneadean topos in Basil Hex VI.7 (PG 29.133BC): if the "
            "principles of our acts depend not on our free will but on birth-given "
            "fatalities, then 'useless are the legislators who prescribe what we "
            "must do and avoid; useless are the judges who honour virtue and punish "
            "wickedness. No injustice is imputable to the thief and the murderer. "
            "The farmer will reap abundant harvests without sowing; the merchant "
            "will grow rich whether he wills it or not.' Carneadean argument 5 in "
            "Amand's inventory."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 400",
            md_line_range="ll. 20900-20931",
            chapter="Livre II Ch. VIII §IV (Hex VI.7 — topos 1 Carnéade)",
            amand_chapter_actual="Basile le Grand — Hex VI.7 topos 1",
            extra={
                "hex_reference": "Hex VI.7 (PG 29.133BC; Garnier-Maran I, p. 56E-57B)",
                "evidence_pending": True,
                "evidence_pending_reason": "Basil Hexaemeron VI.7 absent from corpus (ingestion path TBD — Migne PG 29 or SC ed. Giet/Naldini, see manifest)",
                "carneadean_arg_canonical_n": 5,
            },
        ),
        needs_evidence=True,
    ),
    _node(
        id="argument_basil_carneadean_hex_vi_7_christian_hopes_destroyed",
        type="argument",
        label="Basil Hex VI.7: Carneadean topos — Christian hopes destroyed by heimarmene",
        description=(
            "Second topos carnéadien explicite + adaptation chrétienne, Basile Hex "
            "VI.7 (PG 29.133BC) : 'Elles s'évanouissent, nos grandes espérances à "
            "nous chrétiens (αἱ δὲ μεγάλαι τῶν χριστιανῶν ἐλπίδες φροῦδαι ἡμῖν "
            "οἰχήσονται), puisqu'il n'y a ni récompense pour la justice, ni "
            "punition pour le péché, du moment qu'aucune action humaine ne "
            "s'accomplit librement. Sous le règne de la nécessité et de "
            "l'εἱμαρμένη, il n'y a point de place pour le mérite (τὸ πρὸς ἀξίαν), "
            "qui est la condition première de tout jugement équitable.' Adaptation "
            "origénienne (cf. Phil. 23.1, Amand p. 399-400)."
        ),
        description_en=(
            "Second explicit Carneadean topos plus Christian adaptation, Basil Hex "
            "VI.7 (PG 29.133BC): 'Our great Christian hopes vanish (hai de megalai "
            "ton christianon elpides phroudai hemin oichesontai), since there is "
            "neither reward for justice nor punishment for sin, when no human "
            "action is freely accomplished. Under the reign of necessity and "
            "heimarmene there is no room for merit (to pros axian), the prime "
            "condition of all equitable judgement.' Origenian adaptation (cf. "
            "Phil. 23.1, Amand p. 399-400)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 400",
            md_line_range="ll. 20932-20935",
            chapter="Livre II Ch. VIII §IV (Hex VI.7 — topos 2 Carnéade + adaptation chrétienne)",
            amand_chapter_actual="Basile le Grand — Hex VI.7 topos 2",
            extra={
                "hex_reference": "Hex VI.7 (PG 29.133BC; Garnier-Maran I, p. 56E-57B)",
                "evidence_pending": True,
                "evidence_pending_reason": "Basil Hexaemeron VI.7 absent from corpus (ingestion path TBD — Migne PG 29 or SC ed. Giet/Naldini, see manifest)",
                "origenist_adaptation_source": "Origen Comm. in Gen. = Philocalia 23.1",
                "carneadean_arg_canonical_n": 6,
            },
        ),
        needs_evidence=True,
    ),
    _node(
        id="argument_basil_observation_impossible_at_birth",
        type="argument",
        label="Basil Hex VI.5: Carneadean argument — Exact celestial observation at birth impossible",
        description=(
            "Argument carnéadien repris et précisé par Basile Hex VI.5 (PG 29.128B-"
            "129C) : à l'instant précis de la naissance, l'astrologue ne peut "
            "observer exactement la configuration du ciel. Entre l'accouchement et "
            "le dressage de l'horoscope s'intercalent des instants intermédiaires "
            "qui vicient le calcul. Or, l'astrologue doit noter l'astre horoscope à "
            "la seconde zodiacale précise et procéder de même pour chaque planète. "
            "Une exactitude pareille est pratiquement irréalisable. Amand (p. 395 "
            "n. 3) identifie trois autres auteurs développant cet argument "
            "carnéadien : Sextus Empiricus Adv. Math. V.27-28 + 68-71, Origène "
            "Philocalia 23.17, Commentateur arien de Job."
        ),
        description_en=(
            "Carneadean argument taken up and refined by Basil Hex VI.5 (PG 29.128B-"
            "129C): at the precise moment of birth, the astrologer cannot exactly "
            "observe the celestial configuration. Between delivery and casting of "
            "the horoscope, intervening moments vitiate the calculation. Yet the "
            "astrologer must note the horoscope-star to the precise zodiacal second "
            "and proceed likewise for each planet. Such exactitude is practically "
            "unrealisable. Amand (p. 395 n. 3) identifies three other authors "
            "developing this Carneadean argument: Sextus Empiricus Adv. Math. "
            "V.27-28 + 68-71, Origen Philocalia 23.17, Arian commentator on Job."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 395-396",
            md_line_range="ll. 20648-20697",
            chapter="Livre II Ch. VIII §III.2 (Hex VI.5 — section 1)",
            amand_chapter_actual="Basile le Grand — Hex VI.5 section 1",
            extra={
                "hex_reference": "Hex VI.5 (PG 29.128B-129C; Garnier-Maran I, p. 54C-55C)",
                "evidence_pending": True,
                "evidence_pending_reason": "Basil Hexaemeron VI.5 absent from corpus (ingestion path TBD)",
                "parallel_witnesses": [
                    "Sextus Empiricus Adv. Math. V.27-28, 68-71",
                    "Origen Philocalia 23.17 (Robinson 1893, p. 206)",
                    "Arian commentator on Job (pseudo-Origen / pseudo-Julian of Halicarnassus, Usener Rheinisches Museum 40, 1900, p. 330-331)",
                ],
            },
        ),
        needs_evidence=True,
    ),
    _node(
        id="argument_basil_zodiac_animal_absurdity",
        type="argument",
        label="Basil Hex VI.7 section 2: Absurdity of zodiac-animal derived characters",
        description=(
            "Section 2 de Hex VI.7 (PG 29.129C-132B) : Basile se gausse des "
            "portraits du 'Crianien', 'Taurien', 'Scorpien' extraits d'un "
            "ζῳδιολόγιον (manuel d'astrologie populaire identifié par Bidez 1938 "
            "comme proche du Mosquensis gr. 186). Les astrologues font dériver les "
            "mœurs des hommes non des animaux zodiacaux mais des animaux terrestres : "
            "absurdité, car il n'y a rien de commun entre la constellation et "
            "l'animal terrestre. Argument parallèle à Sextus Empiricus Adv. Math. "
            "V.95-102, mais Basile ne reprend que le deuxième chef de Sextus."
        ),
        description_en=(
            "Section 2 of Hex VI.7 (PG 29.129C-132B): Basil mocks the portraits of "
            "the 'Crianien', 'Taurien', 'Scorpien' types extracted from a "
            "zodiologion (popular astrology manual identified by Bidez 1938 as "
            "close to Mosquensis gr. 186). Astrologers derive human characters not "
            "from zodiacal animals but from terrestrial animals: absurd, since there "
            "is nothing in common between constellation and earthly animal. "
            "Argument parallel to Sextus Empiricus Adv. Math. V.95-102, but Basil "
            "takes up only the second of Sextus' heads."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 396",
            md_line_range="ll. 20699-20713",
            chapter="Livre II Ch. VIII §III.2 (Hex VI.7 — section 2)",
            amand_chapter_actual="Basile le Grand — Hex VI.7 section 2",
            extra={
                "hex_reference": "Hex VI.7 (PG 29.129C-132B; Garnier-Maran I, p. 55C-56A)",
                "evidence_pending": True,
                "evidence_pending_reason": "Basil Hexaemeron VI.7 absent from corpus",
                "zodiologion_source": "Bidez 1938, L'Antiquité classique 7, p. 19-21 (Mosquensis gr. 186)",
                "parallel_witnesses": ["Sextus Empiricus Adv. Math. V.95-102 (Bekker p. 745-747)"],
            },
        ),
        needs_evidence=True,
    ),
    _node(
        id="argument_basil_kings_born_daily",
        type="argument",
        label="Basil Hex VI.7 section 3: Variant Carneadean — Every day a king should be born",
        description=(
            "Variation de Basile (Hex VI.7 section 3, PG 29.132B-133D) sur "
            "l'objection carnéadienne classique 'pourquoi des individus nés dans les "
            "mêmes circonstances ont-ils des destinées si différentes ?' Basile "
            "demande : n'est-il pas dans la logique du système astrologique que "
            "chaque jour naissent des rois ? Comment les Chaldéens expliquent-ils la "
            "transmission de la royauté dans une même dynastie ? Selon Amand "
            "(p. 397), Ptolémée a tenté de répondre à cet argument 'très "
            "arbitrairement' (cf. Bouché-Leclercq, L'astrologie grecque, "
            "p. 437-438)."
        ),
        description_en=(
            "Basil's variant (Hex VI.7 section 3, PG 29.132B-133D) on the classical "
            "Carneadean objection 'why do individuals born in the same "
            "circumstances have such different destinies?' Basil asks: is it not "
            "logical to the astrological system that kings should be born every day? "
            "How do the Chaldaeans explain royal transmission within a single "
            "dynasty? Per Amand (p. 397), Ptolemy attempted to answer this argument "
            "'very arbitrarily' (cf. Bouché-Leclercq, L'astrologie grecque, "
            "p. 437-438)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 397",
            md_line_range="ll. 20756-20793",
            chapter="Livre II Ch. VIII §III.2 (Hex VI.7 — section 3 réfutation)",
            amand_chapter_actual="Basile le Grand — Hex VI.7 section 3",
            extra={
                "hex_reference": "Hex VI.7 (PG 29.132B-133D; Garnier-Maran I, p. 56A-57B)",
                "evidence_pending": True,
                "evidence_pending_reason": "Basil Hexaemeron VI.7 absent from corpus",
                "carneadean_origin": "Diversity-of-fate-under-same-circumstance variant",
                "ptolemy_response_reference": "Bouché-Leclercq, L'astrologie grecque, Paris 1899, p. 437-438",
            },
        ),
        needs_evidence=True,
    ),

    # ---- Grégoire de Nazianze — 1 argument ----
    _node(
        id="argument_greg_naz_carmen_dogm_5_carneadean",
        type="argument",
        label="Gregory of Nazianzus Carm. dogm. 5: Carneadean echo in dactylic hexameters",
        description=(
            "Argument carnéadien condensé en hexamètres dactyliques par Grégoire de "
            "Nazianze (Carm. dogm. 5 Περὶ προνοίας, vers 44-52, PG 37.427A-428A) : "
            "'Telle est ma doctrine : elle ne se fonde point sur le mouvement des "
            "astres, mais sur la liberté. Mais toi, tu n'as à la bouche "
            "qu'horoscopes, menues fractions du cercle zodiacal, mesures de la "
            "marche des planètes. Détruis donc les lois de la vie ! Que les "
            "criminels n'aient plus de sujet d'effroi, et que les bons soient privés "
            "de l'espérance qui devait se réaliser dans une autre vie. Si c'est le "
            "cercle du Zodiaque qui produit toutes choses, je suis emporté dans sa "
            "révolution. C'est ce cercle qui engendrera en moi le vouloir lui-même.' "
            "Variation poétique sur les arguments carnéadiens 1, 4, 5 (vertu/vice, "
            "négation de l'autonomie, abolition des lois)."
        ),
        description_en=(
            "Carneadean argument condensed in dactylic hexameters by Gregory of "
            "Nazianzus (Carm. dogm. 5 Peri pronoias, lines 44-52, PG 37.427A-428A): "
            "'Such is my doctrine: it is founded not on the motion of stars but on "
            "freedom. But you have on your lips only horoscopes, tiny fractions of "
            "the zodiacal circle, measures of the planets' course. Then destroy the "
            "laws of life! Let criminals no longer fear, and let the good be "
            "deprived of the hope to be realised in another life. If the Zodiac's "
            "circle produces everything, I am swept along in its revolution. That "
            "circle will engender in me even my willing.' Poetic variation on "
            "Carneadean arguments 1, 4, 5 (virtue/vice, denial of autonomy, "
            "abolition of laws)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 403",
            md_line_range="ll. 21038-21072",
            chapter="Livre II Ch. VIII Note suppl. (Grégoire Naz Carm. dogm. 5)",
            amand_chapter_actual="Grégoire de Nazianze — Carm. dogm. 5 vers 44-52",
            extra={
                "poem_reference": "Carm. dogm. 5 vers 44-52 (PG 37.427A-428A; Mauristes-Caillau II col. 226-229)",
                "evidence_pending": True,
                "evidence_pending_reason": "Gregory of Nazianzus Carmina dogmatica 5 (PG 37.424-429) absent from corpus (existing greg_naz passages are orationes 27/28/etc, not poems)",
                "carneadean_args_referenced": [1, 4, 5],
            },
        ),
        needs_evidence=True,
    ),
]


# =============================================================================
# 5. NEW CONCEPTS (7)
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    # ---- Eusèbe (4) ----
    _node(
        id="concept_autexousion_pe_vi_6_eusebius",
        type="concept",
        label="Autexousion as immediate evidence (Eusebius PE VI.6.21)",
        description=(
            "Articulation eusébienne de l'αὐτεξούσιον (αὐθεκούσιον) comme évidence "
            "immédiate au même titre que la sensation : 'Elle est donc évidente "
            "(ἐναργής), la doctrine du libre arbitre, aussi évidente que la "
            "conscience que nous avons que douleur et plaisir, vision et audition "
            "se perçoivent non par l'intermédiaire d'un syllogisme, mais "
            "directement par la sensation actuelle' (PE VI.6.21). Concept-clé "
            "carnéadien selon Amand (p. 376), où la liberté est posée comme "
            "phénomène psychologique de premier ordre, non comme conclusion "
            "syllogistique."
        ),
        description_en=(
            "Eusebian articulation of autexousion (authekousion) as immediate "
            "evidence on par with sensation: 'So the doctrine of free will is "
            "evident (enarges), as evident as the consciousness we have that pain "
            "and pleasure, sight and hearing are perceived not via syllogism but "
            "directly by actual sensation' (PE VI.6.21). Key Carneadean concept per "
            "Amand (p. 376), where freedom is posited as a first-order "
            "psychological phenomenon, not a syllogistic conclusion."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 355-356, 376",
            md_line_range="ll. 18437-18460, 19355-19376",
            chapter="Livre II Ch. VII §II + §IV.2 conclusion (PE VI.6.21)",
            amand_chapter_actual="Eusèbe de Césarée — αὐτεξούσιον",
            extra={
                "greek_term": "αὐτεξούσιον / αὐθεκούσιον",
                "evidence_type": "enarges (self-evident, parallel to sensation)",
            },
        ),
    ),
    _node(
        id="concept_neurospastoumenoi_carneadean_metaphor",
        type="concept",
        label="Neurospastoumenoi: marionette metaphor (Carneadean anti-fatalism)",
        description=(
            "Métaphore des marionnettes tirées par des ficelles externes "
            "(νευροσπαστουμένους) employée par Eusèbe pour dénoncer la "
            "déshumanisation impliquée par le fatalisme intégral. Attestée chez "
            "Eusèbe dans Contre Hiéroclès 45 (PG 22.861AB ; Kayser p. 408-409) et "
            "Praep. ev. VI.6.20. Amand l'identifie comme motif carnéadien — "
            "ailleurs absent des textes témoins, ce qui la rend distinctive du "
            "registre eusébien (mais probable origine carnéadienne via source "
            "intermédiaire). La métaphore résume l'argument 7 carnéadien : "
            "l'introspection contredit toute prétention à la passivité."
        ),
        description_en=(
            "Metaphor of marionettes pulled by external strings "
            "(neurospastoumenous) used by Eusebius to denounce the dehumanisation "
            "entailed by integral fatalism. Attested in Eusebius' Contra "
            "Hieroclem 45 (PG 22.861AB; Kayser p. 408-409) and Praep. ev. VI.6.20. "
            "Amand identifies it as a Carneadean motif — absent elsewhere from "
            "witness texts, making it distinctive of the Eusebian register (but "
            "probably Carneadean origin via intermediate source). The metaphor "
            "encapsulates Carneadean argument 7: introspection contradicts any "
            "claim to passivity."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 375-376",
            md_line_range="ll. 19304-19354",
            chapter="Livre II Ch. VII §IV.2 (argument 7 — métaphore marionnettes)",
            amand_chapter_actual="Eusèbe de Césarée — métaphore νευροσπαστουμένους",
            extra={
                "greek_term": "νευροσπαστουμένους",
                "eusebius_attestations": [
                    "Praep. Ev. VI.6.20",
                    "Contra Hieroclem 45 (PG 22.861AB)",
                ],
            },
        ),
    ),
    _node(
        id="concept_heimarmene_demonic_invention_eus",
        type="concept",
        label="Heimarmene as demonic invention (Eusebius PE VI.6.4)",
        description=(
            "Saveur théologique chrétienne propre à Eusèbe : l'εἱμαρμένη est "
            "présentée comme invention du démon trompeur (δαίμων) pour rendre "
            "compte des cas où les oracles se révèlent faux (PE VI.6.4 : πάντα δ' "
            "εἱμαρμένης διὰ τῶν χρησμῶν ἀναρτήσας ὁ δαίμων). Amand (p. 369 n. 2) "
            "identifie ce trait comme ajout propre à Eusèbe : 'Cette intervention "
            "du diable inventeur de l'εἱμαρμένη, destructeur de notre liberté et "
            "instigateur de notre chute dans un abîme d'erreurs, montre à elle "
            "seule que ce passage de saveur toute théologique ne correspond pas à "
            "une source littéraire néo-académicienne ou en dépendant directement. "
            "Il représente parfaitement les convictions personnelles d'Eusèbe.'"
        ),
        description_en=(
            "Christian theological flavour proper to Eusebius: heimarmene is "
            "presented as the invention of the deceiver-demon (daimon) to account "
            "for cases where oracles prove false (PE VI.6.4: panta d' heimarmenes "
            "dia ton chresmon anartesas ho daimon). Amand (p. 369 n. 2) identifies "
            "this trait as an Eusebian addition: 'This intervention of the devil "
            "as inventor of heimarmene, destroyer of our freedom and instigator of "
            "our fall into an abyss of errors, shows by itself that this passage "
            "of wholly theological flavour does not correspond to a neo-academic "
            "literary source or one directly dependent on it. It perfectly "
            "represents Eusebius' own convictions.'"
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 369-370",
            md_line_range="ll. 19039-19073",
            chapter="Livre II Ch. VII §IV.2 (section 4 = ajout d'Eusèbe)",
            amand_chapter_actual="Eusèbe de Césarée — εἱμαρμένη démonique",
            extra={
                "eusebian_addition_to_carneades": True,
                "pe_reference": "PE VI.6.4 (introduction = pre-Carneadean Eusebian frame)",
            },
        ),
    ),
    _node(
        id="concept_origenist_theodicy_eus",
        type="concept",
        label="Origenist theodicy in Eusebius PE VI.6.22-73",
        description=(
            "Théodicée chrétienne entièrement origénienne déployée par Eusèbe en "
            "PE VI.6.22-73 (suite directe des sept arguments carnéadiens). "
            "Organisée autour de l'axiome de l'hiérophante de la République de "
            "Platon : αἰτία ἑλομένου, θεὸς ἀναίτιος. Selon Amand (p. 365), 'le mal "
            "moral, c'est-à-dire le péché, est l'œuvre malheureuse de notre libre "
            "arbitre dont la nature est fortement soulignée. Dieu, l'Être "
            "essentiellement bon et étranger à toute jalousie, ne peut d'aucune "
            "manière en être tenu responsable, tout comme d'ailleurs l'εἱμαρμένη, "
            "cette funeste invention des méchants démons. La Providence divine "
            "exclut positivement toute doctrine fataliste.'"
        ),
        description_en=(
            "Wholly Origenian Christian theodicy deployed by Eusebius in PE "
            "VI.6.22-73 (direct sequel to the seven Carneadean arguments). "
            "Organised around the hierophant axiom from Plato's Republic: aitia "
            "helomenou, theos anaitios. Per Amand (p. 365), 'moral evil, i.e. sin, "
            "is the unhappy work of our free will whose nature is strongly "
            "emphasised. God, the essentially good Being foreign to all jealousy, "
            "can in no way be held responsible for it, just as neither can "
            "heimarmene, that disastrous invention of the wicked demons. Divine "
            "Providence positively excludes all fatalist doctrine.'"
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 365",
            md_line_range="ll. 18853-18874",
            chapter="Livre II Ch. VII §III.3 (PE VI.6 partie 2)",
            amand_chapter_actual="Eusèbe de Césarée — théodicée origénienne",
            extra={
                "axiom": "αἰτία ἑλομένου, θεὸς ἀναίτιος (Plato Rep. 617e)",
                "scope": "PE VI.6.22-73",
                "amand_judgement": "entièrement origénienne",
            },
        ),
    ),

    # ---- Basile (3) ----
    _node(
        id="concept_to_eph_hemin_basil",
        type="concept",
        label="To eph' hemin identified as autexousion (Basil Hom. 'Quod Deus non est auctor malorum' 7)",
        description=(
            "Articulation centrale de Basile : 'ce qui dépend de nous est "
            "précisément le libre arbitre' (τὸ ἐφ' ἡμῖν ἐστι τὸ αὐτεξούσιον), "
            "dans l'homélie 'Que Dieu n'est pas l'auteur du mal', ch. 7 "
            "(PG 31.345B ; Garnier-Maran II, p. 79E). Identification explicite des "
            "deux concepts stoïco-épicurien (τὸ ἐφ' ἡμῖν) et patristique-origénien "
            "(αὐτεξούσιον) que Basile fusionne sans distinction terminologique. "
            "Pour Amand (p. 393), cette formule est emblématique de la doctrine "
            "basilienne du libre arbitre — synergisme oriental précoce."
        ),
        description_en=(
            "Central Basilian articulation: 'what depends on us is precisely free "
            "will' (to eph' hemin esti to autexousion), in the homily 'That God is "
            "not the author of evil', ch. 7 (PG 31.345B; Garnier-Maran II, "
            "p. 79E). Explicit identification of two concepts — Stoic-Epicurean "
            "(to eph' hemin) and patristic-Origenian (autexousion) — which Basil "
            "fuses without terminological distinction. Per Amand (p. 393), this "
            "formula is emblematic of Basil's doctrine of free will — early "
            "Eastern synergism."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 392-393",
            md_line_range="ll. 20564-20603",
            chapter="Livre II Ch. VIII §II (homélie sur la théodicée)",
            amand_chapter_actual="Basile le Grand — concept central",
            extra={
                "greek_formula": "τὸ ἐφ' ἡμῖν ἐστι τὸ αὐτεξούσιον",
                "homily_reference": "Quod Deus non est auctor malorum 7 (PG 31.345B; Garnier-Maran II, p. 79E)",
            },
        ),
    ),
    _node(
        id="concept_synergism_basil_origenist",
        type="concept",
        label="Origenist synergism in Basil (Hom. Quod Deus non est auctor + Hex VI.7)",
        description=(
            "Théodicée origénienne reproduite par Basile : le libre arbitre est le "
            "ressort vital de toute la morale et le présupposé de la croyance "
            "évangélique ; le péché provient uniquement du mauvais usage du libre "
            "arbitre ; même Dieu ne peut nous mettre dans l'impossibilité de "
            "pécher tant le don du libre arbitre est excellent. Cette doctrine "
            "constitue la base de ce que la théologie orientale postérieure "
            "appellera synergisme — coopération de la grâce divine avec la libre "
            "volonté humaine (Amand p. 390-391)."
        ),
        description_en=(
            "Origenian theodicy reproduced by Basil: free will is the vital "
            "mainspring of all morality and the presupposition of evangelical "
            "belief; sin arises solely from misuse of free will; even God cannot "
            "make us unable to sin, so excellent is the gift of free will. This "
            "doctrine forms the basis of what later Eastern theology will call "
            "synergism — cooperation of divine grace with free human will "
            "(Amand p. 390-391)."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 390-391",
            md_line_range="ll. 20416-20490",
            chapter="Livre II Ch. VIII §II (Basile défenseur du libre arbitre)",
            amand_chapter_actual="Basile le Grand — synergisme",
            extra={
                "tradition": "Origenist patristic line (vs Augustinian priority of grace)",
                "later_designation": "Eastern synergism",
            },
        ),
    ),
    _node(
        id="concept_chaldeans_astrology_basil",
        type="concept",
        label="Chaldean street-corner astrology (Basil Hex VI.5-7)",
        description=(
            "Cible polémique précise de Basile dans Hex VI.5-7 : non l'astrologie "
            "scientifique de Ptolémée (la Tétrabible semble ignorée par Basile) "
            "mais les 'Chaldéens', charlatans de carrefour qui disaient la bonne "
            "aventure 'plus prestement et sans tant de cérémonie' à la population "
            "semi-chrétienne de Césarée de Cappadoce. Amand (p. 394) souligne le "
            "registre populaire et le caractère sarcastique de la polémique, qui "
            "vise un auditoire 'en majorité gagné à la foi astrologique et "
            "familiarisé avec les prétentions et la technique des tireurs "
            "d'horoscopes'."
        ),
        description_en=(
            "Basil's precise polemical target in Hex VI.5-7: not Ptolemy's "
            "scientific astrology (the Tetrabiblos seems unknown to Basil) but the "
            "'Chaldaeans', street-corner charlatans who told fortunes 'more "
            "swiftly and with less ceremony' to the semi-Christianised population "
            "of Caesarea in Cappadocia. Amand (p. 394) emphasises the popular "
            "register and sarcastic character of the polemic, which targets an "
            "audience 'mostly won over to astrological faith and familiar with "
            "the claims and technique of horoscope-casters'."
        ),
        period="late_antiquity",
        metadata=amand_metadata(
            page_range="p. 393-394",
            md_line_range="ll. 20572-20646",
            chapter="Livre II Ch. VIII §III.1 (registre populaire Hex VI)",
            amand_chapter_actual="Basile le Grand — anti-Chaldéens",
        ),
    ),
]


# =============================================================================
# UNIFIED INSERT LIST
# =============================================================================

NEW_INSERTS: list[dict[str, Any]] = (
    NEW_PERSONS + NEW_WORKS + NEW_SYNTHESES + NEW_ARGUMENTS + NEW_CONCEPTS
)
