"""Amand B9 — NEW_INSERTS list (new nodes).

Bilingual FR/EN plain-text descriptions. Periods title-case canonical only.
Type prefixes match `type` field. Metadata via amand_metadata().

Sections :
  - PERSONS  : Hippolytus of Rome, Diodorus Tarsus, Epiphanius Salamis,
               Anonymous Arian Job commentator, Crescens the Cynic
  - WORKS    : Hippolytus Philosophoumena + Contra Noetum ;
               Bardesanes Liber Legum Regionum ;
               Epiphanius Panarion + Ancoratus ;
               Diodorus Contra Astronomos / Tarsus Genesis comm / Romans comm ;
               Pseudo-Origenes In Iob (commentaire arien)
  - SYNTHESES: 1-2 par chapitre = 13-14 syntheses
  - ARGUMENTS: 10-13 arguments-temoins majeurs
  - CONCEPTS : 1 nomima_barbarika_bardesanes (ethnographie carneadienne amplifiee)
"""
from __future__ import annotations

from typing import Any

from amand_b9_utils import amand_metadata, dump_metadata


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
# PERSONS (5)
# =============================================================================

NEW_PERSONS: list[dict[str, Any]] = [
    _node(
        id="person_hippolytus_rome_d235",
        type="person",
        label="Hippolyte de Rome",
        description=(
            "Hippolyte de Rome (mort martyr en 235 CE), heresiologue romain de "
            "langue grecque, disciple d'Irenee et theologien du Logos. Pour "
            "Amand 1945 (Livre II Ch. II Note supplementaire, p. 224-227), "
            "Hippolyte chercha en vain dans l'argumentation morale antifataliste "
            "de Carneade des armes contre les gnostiques et les astrologues. "
            "Sa Refutation de toutes les heresies (Philosophoumena) consacre le "
            "livre IV a une refutation de l'astrologie qui n'est autre que la "
            "transcription presque textuelle de Sextus Empiricus Adv. Math. V, "
            "50-105 (avec quelques suppplements personnels mediocres). "
            "Compilateur servile selon Amand : 'cet esprit moyen ne domine "
            "jamais sa matiere, et ne reussit a organiser les parties en un "
            "ensemble bati et solidement coordonne' (citant Wendland). Aucune "
            "trace de l'argumentation morale neo-academicienne de Carneade"
        ),
        description_en=(
            "Hippolytus of Rome (martyred 235 CE), Roman Greek-speaking "
            "heresiologist, disciple of Irenaeus and Logos theologian. For "
            "Amand 1945 (Book II Ch. II Note, p. 224-227), Hippolytus sought "
            "in vain for the moral antifatalist argumentation of Carneades as "
            "a weapon against gnostics and astrologers. His Refutation of all "
            "Heresies (Philosophumena) devotes Book IV to a refutation of "
            "astrology which is nothing other than a near-textual transcription "
            "of Sextus Empiricus Adv. Math. V, 50-105 (with poor personal "
            "supplements). Slavish compiler per Amand : never dominates his "
            "material. No trace of Carneadean moral antifatalist argumentation"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 224-227",
            md_line_range="ll. 12362-12562",
            chapter="Livre II Ch. II Note supplementaire (Hippolyte)",
            amand_chapter_actual="Polemique antiastrologique d'Hippolyte dans sa Refutation de toutes les heresies",
            extra={
                "amand_witness_role": "non_witness_carneadean (refutation astrologie copiee servilement de Sextus Empiricus)",
                "alternative_names": [
                    "Hippolytus Romanus",
                    "Hippolyte Romain",
                    "Hippolytos",
                ],
                "language": "Greek",
                "principal_editions_cited_by_amand": [
                    "P. Wendland, Hippolytus Werke III. Refutatio omnium haeresium, GCS 26 (Hinrichs, Leipzig 1916)",
                ],
                "key_scholarly_studies_via_amand": [
                    "A. d'Ales, La theologie de saint Hippolyte (Paris 1906)",
                    "L. Dieu, Fragments dogmatiques de Julien d'Halicarnase, Melanges Moeller I (Louvain 1914)",
                ],
                "amand_note_on_copying": (
                    "Amand 1945 p. 226-227 reproduit un tableau synoptique "
                    "comparant Philosophoumena IV.1-IV.7 et Sextus Empiricus "
                    "Adv. Math. V.37-105 prouvant la copie quasi-textuelle"
                ),
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="person_diodore_tarsus_d390",
        type="person",
        label="Diodore de Tarse",
        description=(
            "Diodore de Tarse (mort peu avant 394 CE), pretre d'Antioche, eveque "
            "de Tarse a partir de 378, principal promoteur de l'ecole exegetique "
            "antiochienne, maitre de Jean Chrysostome et de Theodore de "
            "Mopsueste. Pour Amand 1945 (Livre II Ch. XI, p. 461-479), Diodore "
            "est l'auteur du plus volumineux traite antifataliste produit par "
            "l'apologetique chretienne : Contra astronomos et astrologos et "
            "Heimarmenen, en 8 livres et 53 chapitres, perdu mais resume avec "
            "abondants extraits par Photius (Bibliotheque cod. 223). Designe "
            "par Theodose en 381 avec Pelagios de Laodicee comme garant de "
            "l'orthodoxie nicene pour le diocese politique d'Orient. Sa "
            "christologie nestorianisante (si l'attribution du Kata "
            "Synousiastōn par Leonce de Byzance est exacte) lui valut "
            "condamnation posthume au synode de Constantinople de 499 : ses "
            "oeuvres ont presque entierement disparu. Amand y voit un theologien "
            "polymathe sans envergure d'esprit, qui 'utilise sans le savoir' "
            "l'argumentation morale de Carneade dans deux passages conserves "
            "par Photius"
        ),
        description_en=(
            "Diodore of Tarsus (died shortly before 394 CE), Antioch priest, "
            "bishop of Tarsus from 378, main promoter of the Antioch exegetical "
            "school, teacher of John Chrysostom and Theodore of Mopsuestia. For "
            "Amand 1945 (Book II Ch. XI, p. 461-479), Diodore authored the "
            "most voluminous antifatalist treatise produced by Christian "
            "apologetic : Contra Astronomos et Astrologos et Heimarmenen in 8 "
            "books and 53 chapters, lost but summarized with abundant extracts "
            "by Photius (Bibliotheca cod. 223). Designated by Theodosius in "
            "381 with Pelagius of Laodicea as guarantor of Nicene orthodoxy "
            "for the political diocese of the East. His Nestorianizing "
            "christology (if Leontius's attribution of Kata Synousiastōn is "
            "correct) earned posthumous condemnation at the synod of "
            "Constantinople 499 : his works almost entirely disappeared. Amand "
            "sees in him a polymathic theologian without intellectual scope, "
            "who 'unknowingly uses' Carneades's moral argumentation in two "
            "passages preserved by Photius"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 461-479",
            md_line_range="ll. 23582-24480",
            chapter="Livre II Ch. XI (Diodore de Tarse)",
            amand_chapter_actual="Diodore de Tarse et son traite Contra astronomos et astrologos et Heimarmenen",
            extra={
                "amand_witness_role": "indirect_echo_carneadean (utilisation libre de plusieurs topoi carneadiens dans le traite Contra Heimarmenen)",
                "alternative_names": [
                    "Diodorus Tarsensis",
                    "Diodoros of Tarsus",
                ],
                "language": "Greek",
                "school": "Antiochene exegetical school",
                "teachers": ["Eusebe d'Emese (jeune Antiochien selon Fetisov)"],
                "students_via_amand": ["Jean Chrysostome", "Theodore de Mopsueste", "Theodoret de Cyr"],
                "principal_editions_cited_by_amand": [
                    "Photius, Bibliotheca cod. 223, ed. Imm. Bekker (Berlin 1825, p. 208b-222a = PG 103, 829B-877C)",
                    "K. Staab, Pauluskommentare aus der griechischen Kirche, Neutestamentliche Abhandlungen 15 (Munster 1933) - fragments du commentaire de Diodore sur Romains",
                    "L. Maries, Etudes preliminaires a l'edition de Diodore de Tarse sur les psaumes (Belles Lettres, Paris 1933)",
                ],
                "key_scholarly_studies_via_amand": [
                    "V. Ermoni, Diodore de Tarse et son role doctrinal, Le Museon NS 2 (1901) 422-444",
                    "R. Abramowski, Untersuchungen zu Diodor von Tarsus, ZNTW 30 (1931) 234-262",
                    "N. Fetisov, Diodor Tarsskij (Kiev 1915) - 460 p., non accessible a Amand",
                    "P. Doll, De Diodori Tarsensis libro kata heimarmenes, Diss. Bonn 1923 (non publiee)",
                    "Cl. Baur, Der heilige Johannes Chrysostomus und seine Zeit I (Munich 1929) p. 69-81",
                    "E. Schweizer, Diodor von Tarsus als Exeget, ZNTW 40 (1941) 33-75",
                ],
                "amand_distinguishing_note": (
                    "A ne pas confondre avec Diodore Cronos (megarique 4e s. "
                    "BCE, ID KG : person_diodorus_cronus_48ef6200), ni avec "
                    "Theodore de Mopsueste son disciple"
                ),
                "julian_invective_testimony": (
                    "Empereur Julien Lettre 90 (ed. Bidez) a Photin de Sirmium "
                    "(362-363) : Diodore = 'magicien du Nazareen', forme a "
                    "Athenes, atteint de phtisie pulmonaire — temoignage "
                    "hostile reproduit p. 467-468 par Amand"
                ),
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="person_epiphanius_salamis_d403",
        type="person",
        label="Epiphane de Salamine",
        description=(
            "Epiphane (vers 315-403 CE), Palestinien d'origine, moine puis "
            "metropolitain de l'ile de Chypre et eveque de Constantia (l'ancienne "
            "Salamine) de 367 a 403. Pour Amand 1945 (Livre II Ch. X, p. 440-460), "
            "Epiphane est le type du zelateur fanatique de l'orthodoxie nicene "
            "et l'ennemi acharne de l'origenisme. Polyglotte (grec, syriaque, "
            "hebreu, copte, latin sommaire), il composa l'Ancoratus (374) et le "
            "Panarion (374-377), repertoire de 80 heresies. Esprit borne, "
            "depourvu de tout sens critique, hostile a la philosophie grecque "
            "et a la dialectique aristotelicienne en bloc, il associe "
            "systematiquement syllogistique et arianisme. Pour Amand, sa "
            "polemique antifataliste se reduit a la reproduction servile de "
            "deux lieux communs derives de Carneade dans la refutation de la "
            "'troisieme heresie de l'hellenisme' (le stoicisme). Le Panarion "
            "est cite contre Origene comme 'pere de toutes les heresies' et "
            "'fauteur de l'arianisme'"
        ),
        description_en=(
            "Epiphanius (c. 315-403 CE), of Palestinian origin, monk then "
            "metropolitan of Cyprus and bishop of Constantia (ancient Salamis) "
            "from 367 to 403. For Amand 1945 (Book II Ch. X, p. 440-460), "
            "Epiphanius is the type of fanatic Nicene zealot and fierce enemy "
            "of Origenism. Polyglot (Greek, Syriac, Hebrew, Coptic, basic "
            "Latin), he composed the Ancoratus (374) and Panarion (374-377), "
            "a catalog of 80 heresies. Narrow-minded, lacking critical sense, "
            "hostile to Greek philosophy and Aristotelian dialectic wholesale, "
            "he systematically associates syllogism and Arianism. For Amand, "
            "his antifatalist polemic reduces to servile reproduction of two "
            "Carneadean topoi in the refutation of the 'third heresy of "
            "Hellenism' (Stoicism). The Panarion cites Origen as 'father of "
            "all heresies' and 'instigator of Arianism'"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 440-460",
            md_line_range="ll. 22677-23581",
            chapter="Livre II Ch. X (Epiphane de Salamine)",
            amand_chapter_actual="Epiphane de Salamine — chasseur d'heresies, polemique antiorigeniste, deux lieux communs derives de Carneade",
            extra={
                "amand_witness_role": "minimal_echo_carneadean (deux topoi seulement, reproduction servile)",
                "alternative_names": [
                    "Epiphanius of Salamis",
                    "Epiphanius of Constantia",
                ],
                "language": "Greek (with Syriac, Hebrew, Coptic, basic Latin)",
                "episcopal_see": "Constantia (Salamis, Cyprus)",
                "episcopate_dates": "367-403 CE",
                "principal_editions_cited_by_amand": [
                    "K. Holl, Epiphanius, Ancoratus und Panarion, GCS 25 (I 1915), GCS 31 (II 1922), GCS 37.1 (III/1 1931), GCS 37.2 (III/2 1933) — Hinrichs, Leipzig",
                ],
                "key_scholarly_studies_via_amand": [
                    "R. A. Lipsius, Epiphanius bishop of Salamis, DCB II (1880) 149-156",
                    "N. Bonwetsch, Epiphanius, RE.Pr.Th. 3rd ed., V (1898) 417-421",
                    "A. Puech, Histoire de la litterature grecque chretienne III (Paris 1930) p. 644-667",
                    "J. de Ghellinck, Quelques appreciations de la dialectique et d'Aristote durant les conflits trinitaires du IVe siecle, RHE 26 (1930) 5-42",
                    "J. Martin, Saint Epiphane, Annales de philosophie chretienne 155-156 (1907-1908) - panegyrique sans valeur scientifique",
                ],
                "amand_doctrine_key": (
                    "Liberte humaine = pur dogme ecclesiastique : Epiphane "
                    "suppose partout la pleine liberte mais ne la conoit ni "
                    "philosophiquement ni psychologiquement. Liberte associee "
                    "exclusivement aux notions de peche et d'heresie. Anc. 52, "
                    "5 = seul passage psychologique"
                ),
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="person_anonymous_arian_job_commentator_4c_ce",
        type="person",
        label="Commentateur arien anonyme du livre de Job",
        description=(
            "Auteur anonyme arien (probablement homeen) du commentaire grec sur "
            "le livre de Job faussement attribue a Origene dans la tradition "
            "manuscrite tardive (Parisinus gr. 454, Berolinensis Phillip. 1406, "
            "Vaticanus gr. 1518). Pour Amand 1945 (Livre II Ch. XIII, p. "
            "533-548), suivant la demonstration de R. Draguet (RHE 1924), "
            "l'attribution a Julien d'Halicarnasse proposee par H. Usener "
            "(1897, 1900) doit etre rejetee : l'analyse theologique du "
            "commentaire revele un subordinatianisme arien marque, qui attaque "
            "l'homoousios et l'homoiousios nicees — doctrine etrangere au "
            "monophysite julianiste. L'auteur ecrit probablement vers la fin "
            "du IVe siecle ou au debut du Ve, 'aux temps des Ariens'. Le "
            "commentaire contient une longue digression antiastrologique greffee "
            "sur Job 38, 7 (hote egenethēsan astra) : 11 arguments dont au moins "
            "trois portent clairement la marque carneadienne, transmise via une "
            "source philosophique probable (peut-etre un hypomnema scolaire) "
            "dont s'inspire aussi Basile (Hex. VI, 5-7)"
        ),
        description_en=(
            "Anonymous Arian author (probably Homoean) of the Greek commentary "
            "on the book of Job falsely attributed to Origen in late manuscript "
            "tradition (Paris gr. 454, Berlin Phillip. 1406, Vatican gr. 1518). "
            "For Amand 1945 (Book II Ch. XIII, p. 533-548), following R. "
            "Draguet's demonstration (RHE 1924), the attribution to Julian of "
            "Halicarnassus proposed by H. Usener (1897, 1900) must be rejected : "
            "the theological analysis reveals a marked Arian subordinationism, "
            "attacking the Nicene homoousios and homoiousios — a doctrine "
            "foreign to the Julianist monophysite. The author probably writes "
            "in the late 4th or early 5th century, 'in the times of the Arians'. "
            "The commentary contains a long antiastrological digression grafted "
            "on Job 38, 7 : 11 arguments of which at least three bear the clear "
            "Carneadean mark, transmitted via a probable philosophical source "
            "(perhaps a school hypomnema) which also inspires Basil (Hex. VI, "
            "5-7)"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 533-548",
            md_line_range="ll. 27637-28348",
            chapter="Livre II Ch. XIII (Commentateur arien de Job)",
            amand_chapter_actual="Le commentateur arien de Job — digression antiastrologique sur Job 38, 7",
            extra={
                "amand_witness_role": "secondary_witness_carneadean_arian (un texte temoin du Ve titre argumentatif de Carneade — pardon des criminels condamnes par la fatalite)",
                "alternative_names": [
                    "Pseudo-Origene",
                    "Anonymous Arian Job commentator",
                    "Homoean Job commentator",
                ],
                "language": "Greek",
                "theological_position": "Homoean Arianism (subordinationist, rejects homoousios and homoiousios)",
                "manuscripts": [
                    "Parisinus gr. 454 (1448 CE) — complet",
                    "Berolinensis Phillip. 1406 (1542, copie du Paris. gr. 454)",
                    "Vaticanus gr. 1518",
                ],
                "principal_editions_cited_by_amand": [
                    "H. Usener, Aus Julian von Halikarnass, Rheinisches Museum NS 55 (1900) 321-340 — edition de la digression antiastrologique (Paris. gr. 454 fol. 121-126v)",
                ],
                "key_scholarly_studies_via_amand": [
                    "R. Draguet, Un commentaire grec arien sur Job, RHE 20 (1924) 38-65 — demonstration definitive de l'attribution arienne",
                    "H. Usener, Julian von Halikarnass, dans H. Lietzmann Catenen (Fribourg 1897) p. 28-34",
                    "L. Dieu, Fragments dogmatiques de Julien d'Halicarnase, Melanges Moeller I (Louvain 1914) p. 192-196",
                    "P. Ferhat, Der Jobprolog des Julianos von Halikarnassos in einer armenischen Bearbeitung, Oriens christianus NS 1 (1911) 26-31",
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="person_crescens_cynic_2c_ce",
        type="person",
        label="Crescens le Cynique",
        description=(
            "Crescens (Crescens Cynicus), philosophe cynique romain du IIe "
            "siecle CE, accusateur de Justin Martyr selon le temoignage de "
            "Tatien (Discours aux Grecs 19) et de Justin lui-meme (2 Apol. 3). "
            "Pour Amand 1945, mentionne en passant dans le contexte du martyre "
            "de Justin (entre 163 et 167 CE) sous Marc Aurele. Personnage "
            "secondaire d'arriere-plan pour l'argumentation antifataliste, "
            "mais represente le type du faux philosophe paien, hostile aux "
            "chretiens cultives qui revendiquent la philosophie comme leur "
            "patrimoine legitime"
        ),
        description_en=(
            "Crescens (Crescens Cynicus), Roman Cynic philosopher of the 2nd "
            "century CE, accuser of Justin Martyr per Tatian (Oratio 19) and "
            "Justin himself (2 Apol. 3). For Amand 1945, mentioned in passing "
            "in the context of Justin's martyrdom (163-167 CE) under Marcus "
            "Aurelius. Secondary background figure for antifatalist "
            "argumentation, but represents the type of false pagan philosopher "
            "hostile to cultured Christians claiming philosophy as their "
            "legitimate patrimony"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 195",
            md_line_range="ll. 10992",
            chapter="Livre II Ch. I background",
            amand_chapter_actual="Justin philosophe et martyr — contexte du martyre sous Marc Aurele",
            extra={
                "amand_witness_role": "background_only (non-temoin carneadien, contexte du martyre de Justin)",
                "school": "Cynic",
                "alternative_names": ["Crescens Cynicus"],
                "key_sources": [
                    "Justin, 2 Apologie 3 (accusation de Crescens)",
                    "Tatien, Discours aux Grecs 19 (denonciation de Crescens)",
                    "Eusebe HE IV, 16, 7-9",
                ],
            },
        ),
        confidence=0.75,
    ),
]


# =============================================================================
# WORKS (8)
# =============================================================================

NEW_WORKS: list[dict[str, Any]] = [
    _node(
        id="work_hippolytus_philosophoumena",
        type="work",
        label="Hippolyte, Refutation de toutes les heresies (Philosophoumena)",
        description=(
            "Refutation omnium haeresium (Philosophoumena), grand traite "
            "antignostique d'Hippolyte de Rome (debut IIIe siecle, avant 235), "
            "en 10 livres. Le livre I esquisse l'histoire des doctrines "
            "philosophiques grecques (compilation mediocre selon Amand). Le "
            "livre IV ouvre par une refutation systematique de l'astrologie "
            "qui est, comme l'a etabli P. Wendland, la transcription presque "
            "textuelle de Sextus Empiricus Adv. Math. V, 50-105 — avec quelques "
            "supplements personnels et de frequentes erreurs d'adaptation. "
            "Pour Amand 1945, aucune trace de l'argumentation morale "
            "antifataliste de Carneade malgre la longue dissertation "
            "antiastrologique"
        ),
        description_en=(
            "Refutatio omnium haeresium (Philosophoumena), great antignostic "
            "treatise of Hippolytus of Rome (early 3rd c., before 235), in 10 "
            "books. Book I sketches the history of Greek philosophical "
            "doctrines (mediocre compilation per Amand). Book IV opens with a "
            "systematic refutation of astrology which is, as P. Wendland "
            "established, the near-textual transcription of Sextus Empiricus "
            "Adv. Math. V, 50-105 — with some personal supplements and "
            "frequent adaptation errors. For Amand 1945, no trace of the "
            "Carneadean moral antifatalist argumentation despite the long "
            "antiastrological dissertation"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 224-227",
            md_line_range="ll. 12362-12562",
            chapter="Livre II Ch. II Note supplementaire",
            amand_chapter_actual="Polemique antiastrologique d'Hippolyte",
            extra={
                "amand_witness_role": "non_witness_carneadean (refutation astrologie copiee de Sextus)",
                "books_count": 10,
                "language": "Greek",
                "principal_edition_cited_by_amand": "P. Wendland, Hippolytus Werke III, GCS 26 (Hinrichs, Leipzig 1916)",
                "amand_focus_book": "Livre IV (refutation systematique de l'astrologie = Sextus Empiricus Adv. Math. V, 50-105)",
                "amand_synoptic_table_pages": "Amand 1945 p. 226-227 fournit un tableau synoptique detaillent les correspondances",
                "alternative_titles": [
                    "Refutatio omnium haeresium",
                    "Elenchos",
                    "Refutation of all Heresies",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="work_bardesanes_liber_legum_regionum",
        type="work",
        label="Bardesane (et Philippe), Le Livre des lois des pays (Liber Legum Regionum)",
        description=(
            "Dialogue syriaque attribue a Bardesane d'Edesse, redige selon la "
            "communis opinio par son disciple Philippe vers le debut du IIIe "
            "siecle (probablement avant 222, mort de Bardesane). Plus ancien "
            "monument conserve de la litterature syriaque hors traductions "
            "bibliques. Le dialogue, originellement intitule Dialogue sur le "
            "Destin (peri heimarmenes), met en scene Bardesane vieillissant "
            "discutant avec ses disciples Awida, Schemaschgram, Philippe et "
            "Bar-Yamma de la conciliation entre fatalisme astrologique et "
            "liberte humaine. Pour Amand 1945 (Livre II Ch. III, p. 229-257), "
            "l'ouvrage est un temoin secondaire crucial pour la transmission "
            "carneadienne : Bardesane y deploie avec une profusion "
            "ethnographique sans precedent l'argument des nomima barbarika, "
            "et reproduit plusieurs autres topoi neo-academiciens. La triple "
            "delimitation physis / heimarmene / autexousion structure tout le "
            "dialogue. Eusebe PE VI.10 cite de longs extraits de la traduction "
            "grecque, et les Recognitiones pseudo-clementines IX.19-28 ainsi "
            "que le pseudo-Cesaire Quaest. 109-110 en derivent egalement"
        ),
        description_en=(
            "Syriac dialogue attributed to Bardesanes of Edessa, redacted per "
            "communis opinio by his disciple Philip around early 3rd century "
            "(probably before Bardesanes's death in 222). Oldest preserved "
            "monument of Syriac literature outside biblical translations. The "
            "dialogue, originally titled Dialogue on Fate (peri heimarmenes), "
            "stages aging Bardesanes discussing with his disciples Awida, "
            "Schemaschgram, Philip and Bar-Yamma the reconciliation between "
            "astrological fatalism and human freedom. For Amand 1945 (Book "
            "II Ch. III, p. 229-257), the work is a crucial secondary witness "
            "for Carneadean transmission : Bardesanes deploys with "
            "unprecedented ethnographic profusion the nomima barbarika "
            "argument, and reproduces several other Neo-Academic topoi. The "
            "triple delimitation physis / heimarmene / autexousion structures "
            "the entire dialogue. Eusebius PE VI.10 cites long extracts from "
            "the Greek translation, and Recognitiones pseudo-clementinae "
            "IX.19-28 and pseudo-Caesarius Quaest. 109-110 also derive from it"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 229-257",
            md_line_range="ll. 12563-13920",
            chapter="Livre II Ch. III (Bardesane et le LLR)",
            amand_chapter_actual="Bardesane le Syrien — Le Livre des lois des pays",
            extra={
                "amand_witness_role": "secondary_witness_bardesanes (temoin secondaire fondamental)",
                "amand_witness_rank": "secondary",
                "languages": ["syriac (original)", "Greek (traduction utilisee par Eusebe)", "Latin (Recognitiones Rufin)"],
                "authorship_note": "Redaction par le disciple Philippe ; doctrine du maitre Bardesane",
                "original_title_attested": "peri heimarmenes (Eusebe HE VI.30.2) ou pros tous hetairous (Eusebe PE VI.10)",
                "principal_editions_cited_by_amand": [
                    "F. Nau, Bardesanes. Liber legum regionum, Patrologia syriaca I.2 (Firmin-Didot, Paris 1907) col. 490-657 — texte syriaque + traduction latine",
                    "W. Cureton, Spicilegium syriacum (Londres 1855) - editio princeps",
                    "F. Nau, Bardesane l'astrologue. Le livre des lois des pays (Paris 1899) - traduction francaise",
                    "G. Levi Della Vida, Bardesane. Il dialogo delli leggi dei paesi (Rome 1921)",
                    "A. Merx, Bardesanes von Edessa (Halle 1863) - p. 25-55 traduction allemande",
                ],
                "amand_witness_n_secondary_role": "Confirme la reconstitution conjecturale carneadienne d'Amand sans appartenir aux 6 temoins canoniques",
                "amand_carneadean_topoi_used": [
                    "Nomima barbarika (amplifie avec profusion ethnographique)",
                    "Climatologie astrologique refutee",
                    "Inutilite de la legislation dans hypothese fataliste",
                    "Constance des moeurs juives et chretiennes a travers les climats",
                ],
                "greek_witnesses_attestation": [
                    "Eusebe Praeparatio Evangelica VI.10.1-48 (ed. Dindorf I, p. 314-323)",
                    "Pseudo-Clement Recognitiones IX, 19-28 (version latine de Rufin)",
                    "Pseudo-Cesaire Pevseis kai apokriseis, 2e Dialogue, reponses 109-110 (PG 38, 980-988)",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_epiphanius_panarion",
        type="work",
        label="Epiphane, Panarion (Refutation de toutes les heresies, ou Coffre a remedes)",
        description=(
            "Panarion (Coffre a remedes, ou Refutation de toutes les heresies), "
            "grand repertoire heresiologique d'Epiphane de Salamine, redige "
            "entre 374 et 377 CE. Catalogue 80 heresies depuis 'barbarisme' "
            "(adamique) jusqu'aux Massalliens contemporains. Pour Amand 1945 "
            "(Livre II Ch. X, p. 440-460), le Panarion est l'instrument "
            "principal de la polemique anti-origenienne d'Epiphane : Heresie "
            "64 contre les origenistes (avec compilation a charge de textes du "
            "De Principiis), Heresie 69-76 contre les Ariens et les "
            "Anomeens-Eunomiens. La 'troisieme heresie de l'hellenisme' (le "
            "stoicisme) contient deux lieux communs derives de Carneade que "
            "l'eveque cypriote reproduit servilement d'une source litteraire "
            "non identifiee. Texte conserve dans la magistrale edition de K. "
            "Holl, GCS 25, 31, 37.1, 37.2"
        ),
        description_en=(
            "Panarion (Medicine-Chest, or Refutation of all Heresies), great "
            "heresiological repertory of Epiphanius of Salamis, written "
            "between 374 and 377 CE. Catalogs 80 heresies from 'barbarism' "
            "(Adamic) through contemporary Massalians. For Amand 1945 (Book "
            "II Ch. X, p. 440-460), the Panarion is the principal instrument "
            "of Epiphanius's anti-Origenist polemic : Heresy 64 against "
            "Origenists (with hostile compilation of texts from De Principiis), "
            "Heresies 69-76 against Arians and Anomoeans-Eunomians. The "
            "'third heresy of Hellenism' (Stoicism) contains two Carneadean "
            "topoi which the Cyprian bishop reproduces servilely from an "
            "unidentified literary source. Text preserved in K. Holl's "
            "magisterial edition, GCS 25, 31, 37.1, 37.2"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 440-460",
            md_line_range="ll. 22677-23581",
            chapter="Livre II Ch. X (Epiphane et le Panarion)",
            amand_chapter_actual="Epiphane de Salamine — Panarion comme repertoire heresiologique anti-origeniste",
            extra={
                "amand_witness_role": "minimal_echo_carneadean (deux topoi servilement reproduits, sources non identifiees)",
                "composition_dates": "374-377 CE",
                "heresy_count": 80,
                "language": "Greek",
                "principal_edition_cited_by_amand": "K. Holl, Epiphanius, Ancoratus und Panarion, GCS 25/31/37.1/37.2 (Hinrichs, Leipzig 1915-1933)",
                "amand_focus_heresies": [
                    "Heresie 5 (stoicisme) - deux topoi carneadiens",
                    "Heresie 64 (Origene) - compilation antiorigeniste",
                    "Heresies 69-76 (Ariens, Anomeens, Eunomiens) - polemique antidialectique",
                ],
                "alternative_titles": [
                    "Adversus Haereses (Panarion)",
                    "Medicine Chest",
                    "Coffre a remedes",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_epiphanius_ancoratus",
        type="work",
        label="Epiphane, Ancoratus (L'Ancre de la foi)",
        description=(
            "Ancoratus (L'Homme bien ancre, ou L'Ancre de la foi), traite "
            "dogmatique d'Epiphane de Salamine redige en 374 CE a la demande "
            "des chretiens de Suedres (Pamphylie). Expose synthetique de la "
            "foi orthodoxe nicene, defendue contre l'arianisme, "
            "l'origenisme et toutes les heresies pneumatologiques. Pour "
            "Amand 1945 (Livre II Ch. X, p. 440-460), l'Ancoratus complete le "
            "Panarion comme oeuvre de polemique anti-origeniste (ch. 54-58 "
            "sur l'interpretation litterale du paradis terrestre vs allegorisme "
            "d'Origene ; ch. 62-63 sur les tuniques de peau ; ch. 87 sur la "
            "resurrection corporelle). Le ch. 52, 5 contient le seul passage "
            "psychologique d'Epiphane sur la volonte humaine"
        ),
        description_en=(
            "Ancoratus (The Well-Anchored Man, or Anchor of Faith), dogmatic "
            "treatise of Epiphanius of Salamis written in 374 CE at the "
            "request of the Christians of Suedrae (Pamphylia). Synthetic "
            "exposition of orthodox Nicene faith, defended against Arianism, "
            "Origenism and all pneumatological heresies. For Amand 1945 (Book "
            "II Ch. X, p. 440-460), the Ancoratus complements the Panarion as "
            "anti-Origenist polemic (ch. 54-58 on literal interpretation of "
            "earthly paradise vs Origen's allegorism ; ch. 62-63 on tunics of "
            "skin ; ch. 87 on bodily resurrection). Ch. 52, 5 contains "
            "Epiphanius's only psychological passage on human will"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 440-460",
            md_line_range="ll. 22677-23581",
            chapter="Livre II Ch. X (Epiphane et l'Ancoratus)",
            amand_chapter_actual="Epiphane de Salamine — Ancoratus comme expose dogmatique nicen",
            extra={
                "amand_witness_role": "non_witness_carneadean (oeuvre dogmatique antiorigeniste, aucune trace de Carneade)",
                "composition_date": "374 CE",
                "language": "Greek",
                "principal_edition_cited_by_amand": "K. Holl, Epiphanius, Ancoratus und Panarion I, GCS 25 (Hinrichs, Leipzig 1915)",
                "amand_focus_chapters": [
                    "ch. 52, 5 (seul passage psychologique sur la volonte)",
                    "ch. 54-58 (paradis terrestre litteral contre allegorisme d'Origene)",
                    "ch. 62-63 (tuniques de peau, blasphemes attribues a Origene)",
                    "ch. 87 (resurrection corporelle contre vues spiritualisees)",
                ],
                "alternative_titles": [
                    "L'Ancre de la foi",
                    "Well-Anchored Man",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_diodore_tarsus_contra_astronomos_heimarmenen",
        type="work",
        label="Diodore de Tarse, Contre les astronomes, les astrologues et le Destin",
        description=(
            "Kata astronomōn kai astrologōn kai heimarmenēs, le plus volumineux "
            "traite antifataliste produit par l'apologetique chretienne, en 8 "
            "livres et 53 chapitres. Compose vers 370-390 CE par Diodore de "
            "Tarse alors pretre puis eveque. Perdu mais resume en detail dans "
            "la Bibliotheca de Photius cod. 223 (ed. Bekker 1825 p. 208b-222a "
            "= PG 103, 829B-877C), avec abondants extraits litteraux. Pour "
            "Amand 1945 (Livre II Ch. XI, p. 461-479), l'ouvrage merite une "
            "etude scientifique approfondie qui n'a pas encore ete entreprise. "
            "Le traite defend Dieu createur et la Providence contre fatalisme "
            "astral ; il insiste sur le libre arbitre comme 'plus beau privilege' "
            "de l'homme (l. IV §41) et utilise plusieurs arguments "
            "antiastrologiques de Carneade (impossibilite de la prediction "
            "exacte, dilemme du fatalisme et de la legislation, nomima "
            "barbarika, climatologie). Deux passages utilisent l'argumentation "
            "morale antifataliste de Carneade (l. VI §45, l. VII §45). Photius "
            "approuve la christologie comme non-nestorianisante"
        ),
        description_en=(
            "Kata astronomōn kai astrologōn kai heimarmenēs, the most "
            "voluminous antifatalist treatise produced by Christian apologetic, "
            "in 8 books and 53 chapters. Composed c. 370-390 CE by Diodore "
            "of Tarsus as priest then bishop. Lost but summarized in detail "
            "in Photius's Bibliotheca cod. 223, with abundant literal extracts. "
            "For Amand 1945 (Book II Ch. XI, p. 461-479), the work deserves "
            "an in-depth scientific study not yet undertaken. The treatise "
            "defends God-creator and Providence against astral fatalism ; it "
            "insists on free will as man's 'fairest privilege' (Book IV §41) "
            "and uses several antiastrological arguments of Carneades "
            "(impossibility of exact prediction, dilemma of fatalism and "
            "legislation, nomima barbarika, climatology). Two passages use "
            "Carneades's moral antifatalist argumentation (Book VI §45, Book "
            "VII §45). Photius approves the christology as non-Nestorianizing"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 461-479",
            md_line_range="ll. 23582-24480",
            chapter="Livre II Ch. XI (Diodore et son traite antifataliste)",
            amand_chapter_actual="Diodore de Tarse — Contra astronomos et astrologos et heimarmenen, en 8 livres",
            extra={
                "amand_witness_role": "indirect_echo_carneadean (utilisation libre de plusieurs topoi carneadiens)",
                "books_count": 8,
                "chapters_count": 53,
                "composition_dates": "c. 370-390 CE",
                "language": "Greek",
                "preservation_status": "perdu, resume + extraits par Photius",
                "principal_edition_cited_by_amand": "Photius, Bibliotheca cod. 223, ed. Imm. Bekker (Berlin 1825) p. 208b-222a = PG 103, 829B-877C",
                "alternative_titles": [
                    "Kata heimarmenes",
                    "Contra Heimarmenen",
                    "Against Astrologers and Fate",
                ],
                "amand_focus_passages": [
                    "Livre IV §41 (digression sur la conception animale ; eloge du libre arbitre)",
                    "Livre V §43 (rejet de la heimarmene comme cause unique)",
                    "Livre VI §44 (nomima barbarika contracte)",
                    "Livre VI §45 (constance religieuse, argument anticlimatologique)",
                    "Livre VI §45 (echo carneadien lointain : absurdites du fatalisme moral)",
                    "Livre VII §45 (theodicee, axiome platonicien aitia helomenou)",
                    "Livre VII §45 (echo carneadien sur recompenses/chatiments)",
                    "Livre VIII §45 (dilemme de la prediction astrologique)",
                ],
                "studies_via_amand": [
                    "P. Doll, De Diodori Tarsensis libro kata heimarmenes, Diss. Bonn 1923 (non publiee, manuscrit a Bonn)",
                    "V. Ermoni, Diodore de Tarse et son role doctrinal, Le Museon NS 2 (1901) 422-444 p. 433-436 (analyse superficielle)",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_diodore_tarsus_commentary_romans",
        type="work",
        label="Diodore de Tarse, Commentaire sur l'epitre aux Romains",
        description=(
            "Commentaire exegetique de Diodore de Tarse sur l'epitre paulinienne "
            "aux Romains, perdu en tradition directe mais reconstitue a partir "
            "de fragments substantiels (une trentaine de pages) decouverts par "
            "K. Staab dans des chaines exegetiques (Vatic. gr. 762, Monac. gr. "
            "412, Athous Pantocrat. 762) et publies en 1933. Pour Amand 1945 "
            "(Livre II Ch. XI p. 474), Diodore y insiste energiquement sur le "
            "libre arbitre, particulierement dans le commentaire de Rom. 9, "
            "19-20 (peut-on objecter a Dieu son choix souverain ?), Rom. 11, 8 "
            "(esprit de stupeur), et Rom. 11, 31-32 (misericorde universelle). "
            "Diodore s'efforce de demontrer qu'en depit des paroles dures, "
            "l'apotre Paul n'a pas eu l'intention de nier la liberte humaine"
        ),
        description_en=(
            "Exegetical commentary of Diodore of Tarsus on Paul's Letter to "
            "the Romans, lost in direct tradition but reconstituted from "
            "substantial fragments (about thirty pages) discovered by K. Staab "
            "in exegetical chains (Vatic. gr. 762, Monac. gr. 412, Athous "
            "Pantocrat. 762) and published in 1933. For Amand 1945 (Book II "
            "Ch. XI p. 474), Diodore there insists energetically on free will, "
            "particularly in his commentary on Rom. 9, 19-20, Rom. 11, 8, and "
            "Rom. 11, 31-32. Diodore strives to demonstrate that despite "
            "harsh words, the apostle Paul did not intend to deny human freedom"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 474",
            md_line_range="ll. 24220-24255",
            chapter="Livre II Ch. XI §II (Diodore commentateur de Romains)",
            amand_chapter_actual="Commentaire de Diodore sur Romains - liberte humaine contre necessitarisme paulinien apparent",
            extra={
                "amand_witness_role": "supplementary_echo_carneadean (defense systematique du libre arbitre dans l'exegese paulinienne)",
                "preservation_status": "fragments substantiels (~30 pages)",
                "language": "Greek",
                "manuscripts": [
                    "Vatic. gr. 762",
                    "Monac. gr. 412",
                    "Athous Pantocrat. 762",
                ],
                "principal_edition_cited_by_amand": "K. Staab, Pauluskommentare aus der griechischen Kirche aus Katenenhandschriften, Neutestamentliche Abhandlungen 15 (Munster-en-Westph. 1933)",
                "amand_focus_passages": [
                    "Rom. 9, 19-20 (Staab p. 99 l. 33 - p. 100 l. 12)",
                    "Rom. 11, 8 (Staab p. 103 l. 1-4)",
                    "Rom. 11, 31-32 (Staab p. 105 l. 3-14)",
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="work_pseudo_origenes_in_iob_arian_commentary",
        type="work",
        label="Pseudo-Origene, Commentaire arien sur le livre de Job",
        description=(
            "Commentaire grec sur le livre de Job, faussement attribue a "
            "Origene par la tradition manuscrite tardive (Parisinus gr. 454 de "
            "1448, Berolinensis Phillip. 1406 de 1542, Vaticanus gr. 1518). "
            "H. Usener (1897, 1900) avait propose l'attribution a Julien "
            "d'Halicarnasse mais R. Draguet (RHE 20, 1924, 38-65) a "
            "definitivement etabli l'origine arienne (probablement homeenne) "
            "et la date approximative de la fin du IVe ou du debut du Ve "
            "siecle. Pour Amand 1945 (Livre II Ch. XIII, p. 533-548), le "
            "commentaire est plat et terne sauf pour une longue digression "
            "antiastrologique greffee sur Job 38, 7 (hote egenethēsan astra), "
            "qui contraste vivement par sa dialectique et son erudition "
            "philosophique. Cette digression edite par H. Usener (Rheinisches "
            "Museum NS 55, 1900, 321-340) contient 11 arguments, dont au moins "
            "trois portent la marque carneadienne, transmise via une source "
            "philosophique probable (peut-etre un hypomnema scolaire) dont "
            "Basile (Hex. VI, 5-7) s'inspire aussi"
        ),
        description_en=(
            "Greek commentary on the book of Job, falsely attributed to "
            "Origen by late manuscript tradition. H. Usener (1897, 1900) had "
            "proposed attribution to Julian of Halicarnassus but R. Draguet "
            "(RHE 20, 1924, 38-65) definitively established the Arian "
            "(probably Homoean) origin and approximate date of late 4th or "
            "early 5th century. For Amand 1945 (Book II Ch. XIII, p. "
            "533-548), the commentary is flat and dull except for a long "
            "antiastrological digression grafted on Job 38, 7, which contrasts "
            "sharply by its dialectic and philosophical erudition. This "
            "digression, edited by H. Usener (RhM NS 55, 1900, 321-340), "
            "contains 11 arguments, of which at least three bear the "
            "Carneadean mark, transmitted via a probable philosophical source"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 533-548",
            md_line_range="ll. 27637-28348",
            chapter="Livre II Ch. XIII (Pseudo-Origene Comm. in Iob)",
            amand_chapter_actual="Le commentaire grec arien sur Job - digression antiastrologique sur Job 38, 7",
            extra={
                "amand_witness_role": "secondary_witness_carneadean_arian (digression contient un argument carneadien complet : pardon des criminels)",
                "language": "Greek",
                "composition_period": "late 4th - early 5th century CE",
                "manuscripts": [
                    "Parisinus gr. 454 (1448 CE)",
                    "Berolinensis Phillip. 1406 (1542 CE, copie de Paris. gr. 454)",
                    "Vaticanus gr. 1518",
                ],
                "principal_edition_cited_by_amand": "H. Usener, Aus Julian von Halikarnass, Rheinisches Museum NS 55 (1900) 321-340 - digression antiastrologique Paris. gr. 454 fol. 121r-126v",
                "studies_via_amand": [
                    "R. Draguet, Un commentaire grec arien sur Job, RHE 20 (1924) 38-65",
                    "H. Usener, Julian von Halikarnass, dans H. Lietzmann Catenen (Fribourg 1897) p. 28-34",
                ],
                "amand_argument_count": 11,
                "amand_carneadean_arguments_marked": [
                    "Arg. 1 : dilemme fatalisme vs legislation",
                    "Arg. 4 : pitie obligatoire envers criminels-victimes-du-fatalisme (texte temoin du Ve titre argumentatif)",
                    "Arg. 6 : jumeaux nes a la meme heure avec destinees differentes",
                    "Arg. 7 : impossibilite de fixation precise de l'instant natal (Sextus Empiricus Adv. Math. V)",
                    "Arg. 9 : nomima barbarika contracte (mal compris)",
                    "Arg. 11 : inutilite de la priere dans l'hypothese fataliste",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_irenaeus_demonstratio_apostolic",
        type="work",
        label="Irenee de Lyon, Demonstration de la predication apostolique (Epideixis)",
        description=(
            "Epideixis tou apostolikou kerygmatos, court traite catechetique "
            "d'Irenee de Lyon. Connu uniquement par une traduction armenienne "
            "decouverte en 1904. Pour Amand 1945 (Livre II Ch. II, p. 213, "
            "215), l'ouvrage complete l'Adversus Haereses comme expose "
            "synthetique de la 'regle de foi' (kanon tes aletheias). Edition "
            "de reference K. Ter-Mekerttschian et Wilson dans la Patrologia "
            "orientalis XII fasc. 5 (Firmin-Didot, Paris 1919) p. 663-664. "
            "Sans rapport direct avec l'argumentation antifataliste mais utile "
            "pour la theodicee irenenne du libre arbitre divin"
        ),
        description_en=(
            "Demonstration of the Apostolic Preaching, short catechetical "
            "treatise of Irenaeus of Lyon. Known only through an Armenian "
            "translation discovered in 1904. For Amand 1945 (Book II Ch. II, "
            "p. 213, 215), the work complements Adversus Haereses as a "
            "synthetic exposition of the 'rule of faith'. Reference edition "
            "K. Ter-Mekerttschian and Wilson in Patrologia orientalis XII "
            "fasc. 5 (Firmin-Didot, Paris 1919) p. 663-664. Not directly "
            "related to antifatalist argumentation but useful for Irenaean "
            "theodicy of divine free will"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 213, 215",
            md_line_range="ll. 11997-12003",
            chapter="Livre II Ch. II (Irenee theologien de la regle de foi)",
            amand_chapter_actual="Demonstration de la predication apostolique - regle de foi synthetique",
            extra={
                "amand_witness_role": "non_witness_carneadean (catechese, sans rapport direct avec Carneade)",
                "preservation_status": "Armenian translation only, discovered 1904",
                "language": "Greek (original lost) / Armenian (preserved)",
                "principal_edition_cited_by_amand": "K. Ter-Mekerttschian et Wilson, dans la Patrologia orientalis XII fasc. 5 (Firmin-Didot, Paris 1919) p. 663-664",
                "alternative_titles": [
                    "Demonstratio apostolicae praedicationis",
                    "Demonstration of the Apostolic Preaching",
                    "Epideixis",
                ],
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# CONCEPTS (1)
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    _node(
        id="concept_nomima_barbarika_amand",
        type="concept",
        label="Nomima barbarika (argument ethnographique antiastrologique)",
        description=(
            "Argument carneadien classique fonde sur l'ethnographie comparative : "
            "les peuples barbares (= non-grecs) obeissent a des lois et "
            "coutumes specifiques, transmises culturellement et non determinees "
            "astrologiquement, alors meme que les individus de chaque peuple "
            "naissent sous toutes les configurations zodiacales possibles. Cet "
            "argument refute la geographie astrologique (climatologie des sept "
            "climats regis par les sept planetes) en montrant que les pratiques "
            "religieuses, juridiques, alimentaires et sexuelles d'un peuple "
            "demeurent constantes a travers les climats et les hasards "
            "individuels de naissance. Pour Amand 1945, c'est l'un des "
            "arguments antiastrologiques carneadiens les plus largement utilises "
            "dans la patristique secondaire : Bardesane (LLR 25-46, profusion "
            "ethnographique sans precedent), commentateur arien de Job (esquisse "
            "deformee), Recognitiones pseudo-clementines IX.19-28, pseudo-"
            "Cesaire Quaest. 109-110, Eusebe PE VI.10 (citant Bardesane), "
            "Diodore de Tarse Contra Heimarmenen VI.44, Gregoire de Nysse "
            "Contra Fatum. Pour Amand p. 243, Bardesane est 'peut-etre le "
            "premier a avoir mis en oeuvre cet argument avec une telle "
            "profusion et une telle exactitude documentaire'"
        ),
        description_en=(
            "Classical Carneadean argument founded on comparative ethnography : "
            "barbarian peoples (= non-Greek) obey specific laws and customs, "
            "culturally transmitted and not astrologically determined, even "
            "though individuals of each people are born under all possible "
            "zodiacal configurations. This argument refutes astrological "
            "geography (climatology of seven climates ruled by seven planets) "
            "by showing that religious, juridical, dietary and sexual "
            "practices of a people remain constant across climates and "
            "individual birth contingencies. For Amand 1945, this is one of "
            "the most widely used Carneadean antiastrological arguments in "
            "secondary patristic literature : Bardesanes (LLR 25-46, "
            "unprecedented ethnographic profusion), Arian Job commentator "
            "(deformed sketch), pseudo-Clementine Recognitiones IX.19-28, "
            "pseudo-Caesarius Quaest. 109-110, Eusebius PE VI.10 (citing "
            "Bardesanes), Diodore Tarsus Contra Heimarmenen VI.44, Gregory "
            "of Nyssa Contra Fatum. Amand p. 243 : Bardesanes is 'perhaps "
            "the first to have implemented this argument with such profusion "
            "and documentary accuracy'"
        ),
        period="Hellenistic",
        metadata=amand_metadata(
            page_range="p. 55-60, 243-244",
            md_line_range="ll. 13273-13294",
            chapter="Livre II Ch. III §II analyse LLR + cross-reference Intro Ch. II",
            amand_chapter_actual="Argument carneadien des nomima barbarika - section ethnographique du Livre des lois des pays",
            extra={
                "carneadean_topos": True,
                "carneadean_attestations": [
                    "Cicero De Divinatione II.97-98 (texte temoin n°0 indirect via Cicero)",
                    "Bardesanes LLR 25-46 (amplification ethnographique)",
                    "Eusebius PE VI.10 (citant Bardesane)",
                    "Pseudo-Clement Recognitiones IX.19-28",
                    "Pseudo-Cesaire Quaest. 109-110",
                    "Diodore Tarsus Contra Heimarmenen VI.44",
                    "Anonymous Arian Job commentary, arg. 9 (deformation)",
                ],
                "greek_term": "nomima barbarika (νόμιμα βαρβαρικά)",
                "amand_witness_role": "argument_carneadean_widely_transmitted",
            },
        ),
        confidence=0.95,
    ),
]


# =============================================================================
# SYNTHESES (14)
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    _node(
        id="synthesis_amand1945_justin_first_christian_carneadean_user",
        type="synthesis",
        label="Justin = premier ecrivain chretien grec a utiliser l'argumentation carneadienne (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. I (p. 195-207) : Justin philosophe "
            "et martyr est le premier ecrivain chretien de langue grecque, a la "
            "connaissance d'Amand, qui ait utilise l'argumentation morale "
            "antifataliste de Carneade. Cette utilisation est partielle et "
            "indirecte : Justin reproduit en 1 Apol. 43, 1-8 trois arguments "
            "carneadiens identifiables (1- absence de louange/blame, 2- "
            "abolition de la responsabilite, 3- changement moral du meme homme), "
            "non par lecture directe de Clitomaque mais par transmission "
            "scolaire ('lieu commun rouille tombe dans le domaine public'). "
            "Justin ne se rend probablement pas compte qu'il transmet du "
            "materiel carneadien. Texte temoin de niveau 'echo perceptible' "
            "mais non 'temoin' au sens des 6 canoniques d'Amand"
        ),
        description_en=(
            "Amand 1945 synthesis, Book II Ch. I : Justin is the first Greek-"
            "speaking Christian writer, to Amand's knowledge, to have used "
            "the moral antifatalist argumentation of Carneades. This use is "
            "partial and indirect : Justin reproduces in 1 Apol. 43, 1-8 three "
            "identifiable Carneadean arguments, not by direct reading of "
            "Clitomachus but by school transmission ('rusty commonplace fallen "
            "into public domain'). Justin probably does not realize he is "
            "transmitting Carneadean material. Witness text of 'perceptible "
            "echo' level but not 'witness' in the sense of Amand's 6 canonical"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 195-207",
            md_line_range="ll. 10992-11679",
            chapter="Livre II Ch. I (Justin philosophe et martyr)",
            amand_chapter_actual="Synthese Amand sur Justin comme premier utilisateur chretien grec",
            extra={"amand_witness_role": "indirect_echo_carneadean_first_christian"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_tatian_no_carneadean_link",
        type="synthesis",
        label="Tatien = sans dependance directe ou indirecte de Carneade (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. I Note supplementaire (p. "
            "208-211) : la polemique antiastrologique de Tatien (Discours aux "
            "Grecs ch. 7-11) ne se rattache pas a la tradition carneadienne. "
            "Tatien est un 'Tertullien des Grecs' violent et fanatique qui "
            "puise son antifatalisme directement dans le dogme chretien du "
            "libre arbitre, non dans la dialectique philosophique. La doctrine "
            "chretienne 'fournissait elle-meme naturellement a Tatien "
            "l'objection qui se fonde sur le fait de la responsabilite de nos "
            "actes'. Apologie d'Aristide, Discours de Tatien, Apologie "
            "d'Athenagore, Trois livres a Autolycos de Theophile d'Antioche, "
            "Exhortation aux Grecs du pseudo-Justin : aucun ne presente la "
            "moindre trace de l'argumentation carneadienne"
        ),
        description_en=(
            "Amand 1945 synthesis : Tatian's antiastrological polemic (Oratio "
            "ch. 7-11) is not linked to the Carneadean tradition. Tatian is a "
            "'Tertullian of the Greeks', violent and fanatic, drawing his "
            "antifatalism directly from the Christian dogma of free will, not "
            "from philosophical dialectic. Aristides Apol., Tatian Oratio, "
            "Athenagoras Apol., Theophilus Ad Autol., pseudo-Justin Cohort. : "
            "none shows the slightest trace of Carneadean argumentation"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 208-211",
            md_line_range="ll. 11681-11828",
            chapter="Livre II Ch. I Note supplementaire (Tatien)",
            amand_chapter_actual="Synthese Amand : ni Tatien ni les autres apologistes du 2e siecle (hors Justin) ne sont temoins carneadiens",
            extra={"amand_witness_role": "non_witness_carneadean_explicit"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_irenaeus_transposed_topos",
        type="synthesis",
        label="Irenee = echo lointain mais transpose chretiennement du topos carneadien (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. II (p. 212-223) : Irenee de "
            "Lyon, fondateur de la dogmatique catholique avec Origene et "
            "Augustin, reproduit dans Adv. Haer. IV, 37, 1-2 un echo lointain "
            "mais reconnaissable de l'argument carneadien sur l'inutilite de "
            "la louange et du blame contre Valentin et Basilide. La preuve "
            "rationnelle est 'a peine esquissee', dominee par la preuve "
            "scripturaire abondante. Particularite irenaenne cruciale : la "
            "transposition christianise les valeurs paiennes (vertu/vice -> "
            "obeissance/desobeissance a Dieu, recompense temporelle -> vie "
            "eternelle). Cette transposition prefigure la christianisation "
            "complete de l'argumentation neo-academicienne dans la patristique "
            "ulterieure"
        ),
        description_en=(
            "Amand 1945 synthesis : Irenaeus reproduces in Adv. Haer. IV, 37, "
            "1-2 a distant but recognizable echo of the Carneadean argument "
            "on uselessness of praise/blame against Valentinus and Basilides. "
            "The rational proof is 'barely sketched', dominated by abundant "
            "scriptural proof. Crucial Irenaean particularity : Christian "
            "transposition (virtue/vice -> obedience/disobedience to God, "
            "temporal reward -> eternal life). This transposition foreshadows "
            "the full Christianization of Neo-Academic argumentation in later "
            "patristics"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 212-223",
            md_line_range="ll. 11830-12362",
            chapter="Livre II Ch. II (Irenee de Lyon)",
            amand_chapter_actual="Synthese Amand sur Irenee comme echo transpose",
            extra={"amand_witness_role": "transposed_echo_carneadean"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_hippolytus_no_carneadean_use",
        type="synthesis",
        label="Hippolyte = aucune trace de Carneade malgre la polemique antiastrologique (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. II Note supplementaire (p. "
            "224-227) : Hippolyte de Rome, disciple d'Irenee et heresiologue "
            "antignostique, n'utilise pas l'argumentation morale antifataliste "
            "de Carneade. Sa refutation systematique de l'astrologie dans le "
            "livre IV des Philosophoumena est la copie quasi-litterale de "
            "Sextus Empiricus Adv. Math. V, 50-105 — avec ajouts personnels "
            "mediocres revelant son incompetence en matiere astrologique. "
            "Compilateur servile selon le jugement d'A. d'Ales reproduit par "
            "Amand : 'esprit mediocre et aigri, encyclopediste sans "
            "originalite, compilateur sans critique'. Amand fournit p. 226-227 "
            "un tableau synoptique detaillant les correspondances entre "
            "Philosophoumena IV et Sextus Empiricus Adv. Math. V"
        ),
        description_en=(
            "Amand 1945 synthesis : Hippolytus of Rome does not use the moral "
            "antifatalist argumentation of Carneades. His systematic refutation "
            "of astrology in Book IV of the Philosophumena is the near-literal "
            "copy of Sextus Empiricus Adv. Math. V, 50-105 — with mediocre "
            "personal additions revealing his astrological incompetence. "
            "Servile compiler per d'Ales : 'mediocre and bitter mind, "
            "uncritical encyclopedist'. Amand provides p. 226-227 a synoptic "
            "table detailing correspondences"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 224-227",
            md_line_range="ll. 12362-12562",
            chapter="Livre II Ch. II Note supplementaire (Hippolyte)",
            amand_chapter_actual="Synthese Amand : Hippolyte copiste de Sextus, non-temoin carneadien",
            extra={"amand_witness_role": "non_witness_carneadean_servile_copyist"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_bardesanes_secondary_witness_ethnographic",
        type="synthesis",
        label="Bardesane = temoin secondaire crucial avec amplification ethnographique sans precedent (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. III (p. 229-257) : Bardesane "
            "d'Edesse, philosophe-theologien syrien (154-222), est temoin "
            "secondaire fondamental de la transmission carneadienne grace au "
            "Livre des lois des pays (dialogue syriaque redige par son disciple "
            "Philippe). Trois caracteristiques essentielles : (1) Doctrine "
            "hybride conciliante : physis pour les phenomenes corporels "
            "communs, heimarmene astrale pour les evenements exterieurs et le "
            "corps, autexousion pour l'ame humaine = compromis original face "
            "au fatalisme integral des Chaldeens. (2) Amplification "
            "ethnographique sans precedent : Bardesane deploie l'argument "
            "carneadien des nomima barbarika avec 'une telle profusion et une "
            "telle exactitude documentaire' qu'il en est peut-etre le premier "
            "a operer ce genre d'amplification ethnographique. (3) Transmission "
            "grecque cruciale : Eusebe PE VI.10, Recognitiones pseudo-"
            "clementines IX.19-28, pseudo-Cesaire Quaest. 109-110 derivent "
            "tous de la traduction grecque du LLR"
        ),
        description_en=(
            "Amand 1945 synthesis : Bardesanes of Edessa (154-222) is the "
            "crucial secondary witness of Carneadean transmission via the "
            "Liber Legum Regionum (Syriac dialogue redacted by his disciple "
            "Philip). Three essential characteristics : (1) Conciliating "
            "hybrid doctrine — physis for common corporeal phenomena, astral "
            "heimarmene for external events and body, autexousion for the "
            "human soul = original compromise vs Chaldean integral fatalism. "
            "(2) Unprecedented ethnographic amplification : Bardesanes deploys "
            "the Carneadean nomima barbarika argument with 'such profusion "
            "and documentary accuracy' that he is perhaps the first to operate "
            "such ethnographic amplification. (3) Crucial Greek transmission : "
            "Eusebius PE VI.10, ps-Clement Recognitiones IX.19-28, ps-"
            "Caesarius Quaest. 109-110 all derive from the Greek translation "
            "of LLR"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 229-257",
            md_line_range="ll. 12563-13920",
            chapter="Livre II Ch. III (Bardesane le Syrien)",
            amand_chapter_actual="Synthese Amand sur Bardesane comme temoin secondaire critique avec amplification ethnographique",
            extra={
                "amand_witness_role": "secondary_witness_bardesanes",
                "amand_witness_rank": "secondary",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_clement_alexandria_minimal_echo",
        type="synthesis",
        label="Clement d'Alexandrie = deux echos lointains seulement, transposition chretienne explicite (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. IV (p. 258-273) : Clement, "
            "mystique et moraliste, n'a pas ete frappe par l'influence du "
            "fatalisme astrologique sur les chretiens populaires comme le sera "
            "son disciple Origene. Il n'entreprend donc pas de refutation "
            "systematique de l'heimarmene — le mot 'brille par son absence' "
            "dans toute son oeuvre personnelle conservee, et il ne mentionne "
            "Carneade qu'une seule fois (Strom. I, 64, 1) dans une liste "
            "scolaire empruntee. Deux echos lointains seulement : (1) Strom. "
            "I, 83, 5 — argument incomplet sur louange/blame/recompense/"
            "chatiment ; (2) Strom. II, 11, 1-2 — transposition chretienne "
            "remarquable de l'argument antifataliste contre Basilide et "
            "Valentin (foi/incroyance au lieu de vertu/vice). Le texte II.11 "
            "est interessant comme premiere demonstration patristique de "
            "'glissement' chretien sur du materiel philosophique"
        ),
        description_en=(
            "Amand 1945 synthesis : Clement of Alexandria, mystic and moralist, "
            "was not struck by the influence of astrological fatalism on "
            "popular Christians as his disciple Origen will be. He therefore "
            "does not undertake systematic refutation of heimarmene — the word "
            "'shines by its absence' in all his preserved personal work, and "
            "he mentions Carneades only once (Strom. I, 64, 1) in a borrowed "
            "school list. Two distant echoes only : (1) Strom. I, 83, 5 — "
            "incomplete argument on praise/blame ; (2) Strom. II, 11, 1-2 — "
            "remarkable Christian transposition of the antifatalist argument "
            "against Basilides and Valentinus (faith/unbelief instead of "
            "virtue/vice)"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 258-273",
            md_line_range="ll. 13925-14672",
            chapter="Livre II Ch. IV (Clement d'Alexandrie)",
            amand_chapter_actual="Synthese Amand sur Clement comme minimal echo carneadien avec transposition chretienne explicite",
            extra={"amand_witness_role": "minimal_echo_carneadean_transposed"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_methodius_indirect_via_hypomnema",
        type="synthesis",
        label="Methode d'Olympe = utilisation indirecte via un hypomnema scolaire (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. VI (p. 326-341) : Methode "
            "d'Olympe (martyr vers 311), evêque platonisant adversaire "
            "d'Origene, utilise dans le Banquet des dix Vierges VIII, 16, "
            "227-229 trois syllogismes ou Amand decele l'origine "
            "neo-academicienne. Mais l'utilisation est indirecte : 'Methode "
            "les aura probablement extraits d'un manuel scolaire ; on sait "
            "la vogue des hypomnemata dans l'enseignement philosophique a "
            "l'epoque imperiale'. Il transcrit a peu pres litteralement sa "
            "source sans transposition chretienne — au contraire des autres "
            "Peres patristiques. Le De Autexusio 16, 6 contient un echo fugace "
            "supplementaire mais d'origine plus probablement irenenne que "
            "carneadienne directe"
        ),
        description_en=(
            "Amand 1945 synthesis : Methodius of Olympus (martyr c. 311), "
            "Platonizing bishop adversary of Origen, uses in Symposium VIII, "
            "16, 227-229 three syllogisms where Amand detects Neo-Academic "
            "origin. But the use is indirect : 'Methodius probably extracted "
            "them from a school manual ; the vogue of hypomnemata in imperial "
            "philosophical teaching is known'. He transcribes his source "
            "almost literally without Christian transposition — contrary to "
            "other patristic Fathers. De Autexusio 16, 6 contains an additional "
            "fugitive echo but more probably of Irenaean than direct "
            "Carneadean origin"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 326-341",
            md_line_range="ll. 17085-17791",
            chapter="Livre II Ch. VI (Methode d'Olympe)",
            amand_chapter_actual="Synthese Amand sur Methode comme transmission indirecte via hypomnema scolaire",
            extra={"amand_witness_role": "indirect_echo_carneadean_via_hypomnema"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_methodius_anti_origenist_reaction",
        type="synthesis",
        label="Methode = principal organisateur de la reaction anti-origeniste (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. VI §I.1 (p. 327-329) : Methode "
            "d'Olympe est le principal adversaire intellectuel d'Origene a la "
            "fin du IIIe siecle et, en un sens, l'organisateur de la reaction "
            "ecclesiastique conservatrice contre certaines theses de l'Ecole "
            "d'Alexandrie. Il combat la creation ab aeterno, la preexistence "
            "des ames, leur chute et incarceration dans le corps, une theorie "
            "trop spiritualisee de la resurrection — sans nier le platonisme "
            "fondamental qu'il partage avec Origene. Sa reaction est efficace "
            "precisement parce qu'elle s'inspire du meme idealisme platonicien, "
            "dont elle combat les exces. Selon Harnack repris par Amand, sa "
            "maniere d'unir tradition et speculation 'n'a pas ete atteinte au "
            "quatrieme siecle, meme par les Cappadociens'. La theologie "
            "methodienne represente 'deja le dernier degre auquel parviendra "
            "la theologie grecque'"
        ),
        description_en=(
            "Amand 1945 synthesis : Methodius of Olympus is Origen's principal "
            "intellectual adversary at the end of the 3rd century and, in a "
            "sense, the organizer of the conservative ecclesiastical reaction "
            "against some theses of the Alexandrian School. He combats "
            "creation ab aeterno, preexistence of souls, their fall and "
            "incarceration in body, an overly spiritualized resurrection "
            "theory — without denying the fundamental Platonism he shares "
            "with Origen. His reaction is effective precisely because it "
            "draws on the same Platonic idealism it combats the excesses of"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 327-329",
            md_line_range="ll. 17127-17204",
            chapter="Livre II Ch. VI §I.1 (Methode et Origene)",
            amand_chapter_actual="Synthese Amand sur Methode comme organisateur de la reaction anti-origeniste conservatrice",
            extra={"amand_witness_role": "anti_origenist_reaction_leader"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_epiphanius_servile_carneadean_topoi",
        type="synthesis",
        label="Epiphane = reproduction servile de deux lieux communs carneadiens (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. X (p. 440-460) : Epiphane de "
            "Salamine, type du zelateur fanatique de l'orthodoxie nicene, "
            "ennemi acharne d'Origene et de la philosophie grecque, reproduit "
            "dans le Panarion (refutation du stoicisme = troisieme heresie de "
            "l'hellenisme) deux lieux communs derives de l'argumentation "
            "morale antifataliste de Carneade — d'une source litteraire qu'il "
            "n'identifie pas et qu'il copie servilement. Sa conviction du "
            "libre arbitre est exclusivement fondee sur la tradition dogmatique "
            "chretienne et associee aux seules notions de peche et d'heresie : "
            "aucune analyse psychologique ou philosophique. Le seul passage "
            "psychologique se trouve dans l'Ancoratus 52, 5. Sa polemique "
            "antiorigeniste impose au IVe siecle un retrecissement durable du "
            "champ de la theologie scientifique grecque"
        ),
        description_en=(
            "Amand 1945 synthesis : Epiphanius of Salamis, type of fanatic "
            "Nicene zealot, fierce enemy of Origen and Greek philosophy, "
            "reproduces in the Panarion (refutation of Stoicism = third heresy "
            "of Hellenism) two commonplaces derived from Carneades's moral "
            "antifatalist argumentation — from an unidentified literary source "
            "which he servilely copies. His conviction of free will is "
            "exclusively founded on Christian dogmatic tradition and "
            "associated only with notions of sin and heresy : no psychological "
            "or philosophical analysis. The only psychological passage is in "
            "Ancoratus 52, 5"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 440-460",
            md_line_range="ll. 22677-23581",
            chapter="Livre II Ch. X (Epiphane de Salamine)",
            amand_chapter_actual="Synthese Amand sur Epiphane comme reproduction servile de topoi carneadiens",
            extra={"amand_witness_role": "servile_echo_carneadean_topoi"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_epiphanius_antiorigenist_polemic_anti_philosophy",
        type="synthesis",
        label="Epiphane = polemique antiorigeniste comme aversion structurelle pour la philosophie hellenique (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. X §I.3 (p. 449-451) : "
            "l'aversion d'Epiphane pour Origene est inseparable de son "
            "aversion structurelle pour la philosophie hellenique en general. "
            "L'eveque cypriote appelle Origene 'pere de l'arianisme et de "
            "toutes les heresies' precisement parce qu'Origene a fait alliance "
            "avec la philosophie. Au Panarion Heresie 64, Epiphane compare "
            "Origene a 'un crapaud qui remue dans un marecage et pousse de "
            "sonores coassements', a 'une vipere' qui l'a 'aveugle' par "
            "l'education hellenique. Il refuse la distinction explicite des "
            "Cappadociens entre usage utile et abus de la philosophie. La "
            "culture grecque est 'hautement suspecte' par 'son humanisme et "
            "son autonomie rationnelle'. Cette posture clericale retroactive "
            "exclut Epiphane de la lignee origenienne et antiochienne d'usage "
            "controle de Carneade contre l'astrologie"
        ),
        description_en=(
            "Amand 1945 synthesis : Epiphanius's aversion for Origen is "
            "inseparable from his structural aversion for Greek philosophy in "
            "general. The Cyprian bishop calls Origen 'father of Arianism and "
            "all heresies' precisely because Origen allied with philosophy. "
            "In Panarion Heresy 64, Epiphanius compares Origen to 'a toad "
            "stirring in a swamp and emitting sonorous croaks', to 'a viper' "
            "that 'blinded him' through Hellenic education. He refuses the "
            "Cappadocians' explicit distinction between useful use and abuse "
            "of philosophy. Greek culture is 'highly suspect' through 'its "
            "humanism and rational autonomy'"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 449-451",
            md_line_range="ll. 23087-23192",
            chapter="Livre II Ch. X §I.3 (Epiphane et la theologie d'Origene)",
            amand_chapter_actual="Synthese Amand sur la posture anti-philosophie comme cle de la polemique antiorigeniste epiphanienne",
            extra={"amand_witness_role": "structural_anti_philosophy_carneadean_exclusion"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_diodore_tarsus_largest_antifatalist_treatise",
        type="synthesis",
        label="Diodore de Tarse = auteur du plus volumineux traite antifataliste chretien (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. XI §II (p. 469-474) : Diodore "
            "de Tarse a produit avec Kata astronomōn kai astrologōn kai "
            "heimarmenēs le plus volumineux traite antifataliste de "
            "l'apologetique chretienne — 8 livres et 53 chapitres. L'ouvrage "
            "est perdu mais 'le plus important ou plus exactement le plus "
            "massif' (Amand p. 469), resume avec abondants extraits par "
            "Photius cod. 223. Photius lui-meme reconnaît la 'purete et "
            "clarte du style' tout en reprochant les digressions et 'la "
            "discussion contre les partisans de la heimarmene parfois "
            "heureuse et pertinente' mais 'frequemment superficielle'. Pour "
            "Amand, le compte rendu photien n'a fait l'objet d'aucune etude "
            "scientifique approfondie hormis la dissertation manuscrite de P. "
            "Doll (Bonn 1923, non publiee) que Amand juge severement comme "
            "'audace assez aventureuse' avec 'methode mecanique' marquee de "
            "la Poseidoniosforschung d'avant 1914"
        ),
        description_en=(
            "Amand 1945 synthesis : Diodore of Tarsus produced with Kata "
            "astronomōn kai astrologōn kai heimarmenēs the most voluminous "
            "antifatalist treatise of Christian apologetic — 8 books and 53 "
            "chapters. Lost but summarized with abundant extracts by Photius "
            "cod. 223. Photius himself recognizes the 'purity and clarity of "
            "style' while reproaching digressions and 'the discussion against "
            "heimarmene partisans sometimes happy and pertinent' but "
            "'frequently superficial'. For Amand, the Photian summary has "
            "received no in-depth scientific study other than P. Doll's "
            "unpublished Bonn dissertation 1923, severely judged"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 469-474",
            md_line_range="ll. 23968-24225",
            chapter="Livre II Ch. XI §II (Diodore et son traite Contra Heimarmenen)",
            amand_chapter_actual="Synthese Amand : Diodore producteur du plus massif traite antifataliste chretien",
            extra={"amand_witness_role": "indirect_echo_carneadean_largest_treatise"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_diodore_tarsus_two_carneadean_echoes",
        type="synthesis",
        label="Diodore = deux passages-echos de l'argumentation morale carneadienne via Photius (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. XI §III.2 (p. 476-479) : "
            "L'argumentation morale antifataliste de Carneade laisse dans le "
            "Contra Heimarmenen de Diodore deux passages-echos conserves par "
            "Photius. (1) Livre VI §45 : 'N'est-ce pas le comble de "
            "l'absurdite que de devenir mechant par l'effet de la genesis et "
            "d'etre hai a cause de la mechancete qu'elle a inspiree ?' = "
            "developpement libre du topos carneadien des absurdites morales. "
            "(2) Livre VII §45 : 'les partisans de la heimarmene enlevent "
            "louanges et couronnes aux hommes vertueux, et proclament injustes "
            "les corrections et chatiments des malfaiteurs' = forme abregee "
            "(par Photius lui-meme ?) du raisonnement carneadien sur "
            "recompenses et chatiments. Amand qualifie ces passages d'echo "
            "indirect via 'lieu commun de l'ecole du rheteur' transmis aux "
            "defenseurs chretiens du libre arbitre"
        ),
        description_en=(
            "Amand 1945 synthesis : Carneades's moral antifatalist "
            "argumentation leaves in Diodore's Contra Heimarmenen two echo-"
            "passages preserved by Photius. (1) Book VI §45 : 'is it not the "
            "height of absurdity to become wicked through genesis and be "
            "hated for the wickedness it inspired ?' = free development of "
            "the Carneadean topos of moral absurdities. (2) Book VII §45 : "
            "'partisans of heimarmene take praises and crowns from virtuous "
            "men, and proclaim corrections and punishments of evildoers "
            "unjust' = abbreviated form (by Photius himself ?) of the "
            "Carneadean reasoning on rewards and punishments"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 476-479",
            md_line_range="ll. 24351-24480",
            chapter="Livre II Ch. XI §III.2 (Diodore et l'argumentation morale carneadienne)",
            amand_chapter_actual="Synthese Amand : deux echoes carneadiens dans Diodore via Photius",
            extra={"amand_witness_role": "indirect_double_echo_carneadean_via_photius"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_arian_job_witness_carneadean_pity_argument",
        type="synthesis",
        label="Commentateur arien de Job = temoin du Ve titre carneadien (pardon des criminels) (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. XIII (p. 533-548) : la "
            "digression antiastrologique du commentateur arien anonyme sur Job "
            "38, 7 contient onze arguments dont au moins trois portent la "
            "marque carneadienne, transmise via une source philosophique "
            "probable (peut-etre un hypomnema scolaire) dont Basile s'inspire "
            "aussi (Hex. VI, 5-7). L'argument 4 (Paris. gr. 454 fol. 123v) "
            "constitue, selon Amand, un texte temoin etonnamment complet du "
            "Ve titre argumentatif carneadien : 'au lieu de chatier les "
            "coupables, il faudrait avoir pitie de ces malheureux jouets de "
            "la heimarmene et leur pardonner tous leurs mefaits' — argument "
            "que Amand juge 'un des plus impressionnants que Carneade avait "
            "aiguises contre la theorie de la heimarmene'. La digression "
            "n'est cependant pas un 'texte temoin' au sens des 6 canoniques "
            "car elle ne reproduit pas l'ensemble de l'argumentation morale "
            "antifataliste de Carneade"
        ),
        description_en=(
            "Amand 1945 synthesis : the antiastrological digression of the "
            "anonymous Arian commentator on Job 38, 7 contains eleven "
            "arguments of which at least three bear the Carneadean mark. "
            "Argument 4 constitutes, per Amand, an astonishingly complete "
            "witness-text of Carneades's fifth argumentative heading : 'instead "
            "of punishing the guilty, one should pity these wretched playthings "
            "of heimarmene and forgive them all their misdeeds' — argument "
            "Amand judges 'one of the most impressive Carneades sharpened "
            "against the theory of heimarmene'"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 533-548",
            md_line_range="ll. 27637-28348",
            chapter="Livre II Ch. XIII (Commentateur arien de Job)",
            amand_chapter_actual="Synthese Amand : digression antiastrologique sur Job 38, 7 et son temoignage carneadien partiel",
            extra={"amand_witness_role": "secondary_witness_carneadean_pity_argument"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_arian_job_homoean_dating_draguet",
        type="synthesis",
        label="Commentateur arien de Job = homéen ecrivant vers 380-400 selon Draguet 1924 (Amand 1945)",
        description=(
            "Synthese Amand 1945, Livre II Ch. XIII §I (p. 534-537) : "
            "l'attribution du commentaire grec arien sur Job (Pseudo-Origene "
            "des manuscrits Paris. gr. 454, Berol. Phillip. 1406, Vat. gr. "
            "1518) a Julien d'Halicarnasse, proposee par H. Usener (1897, "
            "1900) et acceptee par L. Dieu (1914), a ete definitivement "
            "refutee par R. Draguet (RHE 20, 1924, 38-65). L'analyse "
            "theologique du commentaire revele un subordinatianisme arien "
            "marque qui attaque l'homoousios et l'homoiousios nicees — "
            "doctrine impossible pour un monophysite julianiste. L'auteur "
            "est probablement homeen et ecrit 'aux temps des Ariens', soit "
            "apres 340-350 et probablement pas notablement apres 400 CE. "
            "Amand adhere pleinement a la demonstration draguetienne"
        ),
        description_en=(
            "Amand 1945 synthesis : the attribution of the Arian Greek "
            "commentary on Job (Pseudo-Origen of mss. Paris. gr. 454, Berol. "
            "Phillip. 1406, Vat. gr. 1518) to Julian of Halicarnassus, proposed "
            "by H. Usener (1897, 1900) and accepted by L. Dieu (1914), has "
            "been definitively refuted by R. Draguet (RHE 20, 1924, 38-65). "
            "Theological analysis reveals a marked Arian subordinationism "
            "attacking Nicene homoousios and homoiousios — doctrine impossible "
            "for a Julianist monophysite. The author is probably Homoean and "
            "writes 'in the times of the Arians', after 340-350 and probably "
            "not notably after 400 CE"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 534-537",
            md_line_range="ll. 27664-27810",
            chapter="Livre II Ch. XIII §I (auteur du commentaire)",
            amand_chapter_actual="Synthese Amand : datation et attribution homeenne selon Draguet 1924",
            extra={"amand_witness_role": "homoean_arian_authorship_attribution"},
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# ARGUMENTS (10)
# =============================================================================

NEW_ARGUMENTS: list[dict[str, Any]] = [
    _node(
        id="argument_bardesanes_nomima_barbarika_amplified",
        type="argument",
        label="Bardesane LLR §25-46 - argument ethnographique amplifie (nomima barbarika)",
        description=(
            "Argument antiastrologique deploye par Bardesane dans le Livre des "
            "lois des pays §25-46. Refute la geographie astrologique des sept "
            "climats en deployant une longue liste de lois et coutumes "
            "particulieres en vigueur parmi les peuples (Brahmanes, Perses, "
            "Mages, Sarmates, Bactriens, Cushites, Romains, Grecs, Galates, "
            "Britanniques, Parthes, Elamites, Mèdes, Hatra, Edesseens, etc.). "
            "Bardesane y ajoute deux sous-arguments cruciaux : (a) la "
            "constance des coutumes nationales independamment du climat "
            "geographique (exemple : les Juifs ont conserve la circoncision "
            "partout dans l'Empire apres la dispersion par Vespasien) ; (b) "
            "la nouveaute des chretiens, 'nouvelle race', qui gardent leur foi "
            "sous tous les climats. Selon Amand p. 243, c'est 'peut-etre la "
            "premiere fois' que l'argument carneadien est mis en oeuvre avec "
            "'une telle profusion et une telle exactitude documentaire'"
        ),
        description_en=(
            "Antiastrological argument deployed by Bardesanes in the Liber "
            "Legum Regionum §25-46. Refutes the astrological geography of the "
            "seven climates by deploying a long list of laws and customs "
            "particular to peoples (Brahmans, Persians, Magi, Sarmatians, "
            "Bactrians, Kushites, Romans, Greeks, Galatians, Britons, Parthians, "
            "Elamites, Medes, Hatra, Edessans, etc.). Bardesanes adds two "
            "crucial sub-arguments : (a) constancy of national customs "
            "regardless of geographic climate (example : Jews preserved "
            "circumcision throughout the Empire after Vespasian's dispersion) ; "
            "(b) novelty of Christians, 'new race', who keep their faith "
            "under all climates"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 242-244",
            md_line_range="ll. 13256-13314",
            chapter="Livre II Ch. III §II (analyse du LLR)",
            amand_chapter_actual="Argument nomima barbarika amplifie ethnographiquement dans Bardesane LLR §25-46",
            extra={
                "amand_witness_role": "secondary_carneadean_argument_amplified",
                "carneadean_origin": True,
                "amand_key_passage": "LLR ed. Nau, PS I.2, col. 580-608 = §25-46",
                "amand_amplification_status": "ethnographic_amplification_unprecedented",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_bardesanes_triple_delimitation_physis_heimarmene_autexousion",
        type="argument",
        label="Bardesane LLR - triple delimitation physis / heimarmene / autexousion",
        description=(
            "Argument structurel de Bardesane dans le LLR §15-22 : delimitation "
            "tripartite des spheres de causalite. (1) Physis (nature, necessite "
            "physique) = principe des actions communes aux humains et aux "
            "animaux ; ne peut vinculer les ames humaines. (2) Heimarmene "
            "(Destin astrologique) = configuration des sept planetes a "
            "l'instant de la naissance ; gouverne les evenements exterieurs "
            "(richesse, pauvrete, sante, maladie) et le corps de l'homme "
            "visible. (3) Autexousion (libre arbitre) = pouvoir de l'ame "
            "humaine, image de Dieu ; choisir bien ou mal, vertu ou vice. "
            "Cette delimitation, originale par sa systematicite, etablit une "
            "concession astrologique mitigee tout en sauvegardant la liberte "
            "intellectuelle et morale. Pour Amand, c'est le 'curieux "
            "compromis' propre a Bardesane vieillissant, contrastant avec le "
            "fatalisme integral chaldeen de ses debuts"
        ),
        description_en=(
            "Bardesanes's structural argument in LLR §15-22 : tripartite "
            "delimitation of causality spheres. (1) Physis = principle of "
            "actions common to humans and animals ; cannot bind human souls. "
            "(2) Heimarmene = configuration of the seven planets at birth ; "
            "governs external events (wealth, poverty, health, illness) and "
            "the visible man's body. (3) Autexousion = power of the human "
            "soul, image of God ; choosing good or evil, virtue or vice. This "
            "delimitation, original in its systematicity, establishes a "
            "moderate astrological concession while safeguarding intellectual "
            "and moral freedom"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 240-244",
            md_line_range="ll. 13196-13317",
            chapter="Livre II Ch. III §II-§III (analyse doctrinale du LLR)",
            amand_chapter_actual="Triple delimitation physis/heimarmene/autexousion - compromis original bardesanien",
            extra={
                "amand_witness_role": "secondary_doctrinal_compromise",
                "amand_key_passages": [
                    "LLR §15-17 ed. Nau, col. 559-564 (physis)",
                    "LLR §18-22 ed. Nau, col. 564-570 (heimarmene des Chaldeens)",
                    "LLR §22-24 ed. Nau, col. 570-580 (autexousion)",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_clement_alex_carneadean_glissement_faith_unbelief",
        type="argument",
        label="Clement, Strom. II, 11, 1-2 - glissement chretien faith/unbelief (Amand 1945)",
        description=(
            "Argument antifataliste de Clement d'Alexandrie dans les "
            "Stromates II, 11, 1-2 contre Basilide et Valentin. Clement "
            "transpose un argument originellement carneadien : 'si la foi est "
            "une prerogative de la nature, elle n'est plus l'acte conscient "
            "d'un choix volontaire. Celui qui ne croit pas ne recevra point "
            "un juste chatiment, puisqu'il n'est en rien responsable, et "
            "celui qui croit ne sera pas non plus recompense'. Pour Amand "
            "(p. 272-273), le glissement chretien consiste a remplacer "
            "vertu/vice par foi/incroyance, sans toutefois maintenir cette "
            "transposition jusqu'au bout — Clement 'oublie' les valeurs "
            "chretiennes et reprend l'argumentation pure de Carneade dans la "
            "deuxieme partie de la citation (nevrospasmenōn de hēmōn = "
            "expression caracteristiquement carneadienne)"
        ),
        description_en=(
            "Clement of Alexandria's antifatalist argument in Stromateis II, "
            "11, 1-2 against Basilides and Valentinus. Clement transposes an "
            "originally Carneadean argument : 'if faith is a prerogative of "
            "nature, it is no longer the conscious act of a voluntary "
            "choice'. For Amand (p. 272-273), the Christian glissement "
            "consists in replacing virtue/vice with faith/unbelief, without "
            "however maintaining this transposition through the end — Clement "
            "'forgets' Christian values and resumes pure Carneadean "
            "argumentation in the second part"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 271-273",
            md_line_range="ll. 14502-14627",
            chapter="Livre II Ch. IV §III (echos carneadiens chez Clement)",
            amand_chapter_actual="Argument transpose Strom. II.11.1-2 - premier glissement patristique sur materiel carneadien",
            extra={
                "amand_witness_role": "minimal_echo_carneadean_christianized",
                "carneadean_origin_qualified": True,
                "amand_signature_expression": "νευροσπασμένων δὲ ἡμῶν (nevrospasmenōn de hēmōn) = expression caracteristiquement carneadienne",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_clement_alex_strom_1_83_5_praise_blame",
        type="argument",
        label="Clement, Strom. I, 83, 5 - argument incomplet sur louange/blame",
        description=(
            "Echo carneadien incomplet et bref dans les Stromates I, 83, 5 de "
            "Clement d'Alexandrie : 'ni les louanges ni les reproches ne sont "
            "justes, ni les recompenses ni les punitions ne sont equitables, "
            "si l'ame ne possede point le pouvoir spontane de se porter vers "
            "tel acte ou de s'en eloigner, et si mal agir ne releve en rien "
            "de notre volonte' (oute de hoi epainoi oute hoi psogoi outhe hai "
            "timai outhe hai kolaseis dikaiai, me tēs psychēs echousēs tēn "
            "exousian tēs hormēs kai aphormēs, all' akousiou tēs kakias "
            "ousēs). Pour Amand (p. 271), 'c'est peu, on l'avouera. Clement "
            "s'est borne a esquisser, une fois et en passant, le theme d'une "
            "des preuves constituant l'argumentation antifataliste de Carneade'"
        ),
        description_en=(
            "Incomplete and brief Carneadean echo in Clement of Alexandria's "
            "Stromateis I, 83, 5 : 'neither praises nor reproaches are just, "
            "neither rewards nor punishments are equitable, if the soul does "
            "not possess the spontaneous power to move toward or away from a "
            "given act'. For Amand (p. 271), 'this is little. Clement has "
            "merely sketched, once and in passing, the theme of one of the "
            "proofs constituting Carneades's antifatalist argumentation'"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 270-271",
            md_line_range="ll. 14495-14548",
            chapter="Livre II Ch. IV §III (echos carneadiens chez Clement)",
            amand_chapter_actual="Echo minimal Strom. I.83.5 sur louange/blame/recompenses/punitions",
            extra={
                "amand_witness_role": "minimal_echo_carneadean_incomplete",
                "carneadean_origin": True,
                "amand_judgement": "C'est peu, on l'avouera (Amand p. 271)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_methodius_symposium_three_carneadean_syllogisms",
        type="argument",
        label="Methode, Banquet VIII.16.227-229 - trois syllogismes neo-academiciens via hypomnema",
        description=(
            "Trois syllogismes antifatalistes deployes par Methode dans le "
            "Banquet des dix Vierges VIII, 16, 227-229, ou Amand decele "
            "l'origine neo-academicienne (carneadienne) probable. (1) Si etre "
            "juste est meilleur qu'etre injuste, pourquoi l'homme ne devient-"
            "il pas juste tout de suite par le destin de naissance ? S'il "
            "doit etre corrige par des enseignements et des lois, c'est qu'il "
            "est doue de libre arbitre. (2) Si les mechants sont mechants par "
            "destin de naissance d'apres la Providence, ils ne sont pas "
            "blamables ni dignes de chatiment. (3) Si les bons sont bons par "
            "destin de naissance, et qu'ils sont loues, alors les mechants "
            "vivant aussi selon leur propre nature ne devraient pas etre "
            "accuses. Aucune transposition chretienne notable : Methode copie "
            "presque litteralement sa source (probablement un hypomnema "
            "scolaire)"
        ),
        description_en=(
            "Three antifatalist syllogisms deployed by Methodius in the "
            "Symposium of the Ten Virgins VIII, 16, 227-229, where Amand "
            "detects probable Neo-Academic (Carneadean) origin. No notable "
            "Christian transposition : Methodius copies his source almost "
            "literally (probably a school hypomnema)"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 339-340",
            md_line_range="ll. 17676-17740",
            chapter="Livre II Ch. VI §IV (utilisation par Methode de l'argumentation morale de Carneade)",
            amand_chapter_actual="Trois syllogismes du Banquet VIII.16 - transmission via hypomnema scolaire",
            extra={
                "amand_witness_role": "indirect_carneadean_via_hypomnema",
                "carneadean_origin": True,
                "amand_judgement": "Methode copie sans transposition chretienne (Amand p. 340)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_irenaeus_adv_haer_iv_37_praise_blame_transposed",
        type="argument",
        label="Irenee, Adv. Haer. IV.37.1-2 - echo carneadien transpose contre Valentin",
        description=(
            "Echo carneadien transpose chretiennement dans Adv. Haer. IV, 37, "
            "1-2 (texte original conserve par Jean Damascene dans les Hiera, "
            "ed. K. Holl, TU 20.2, p. 63) : 'Si les uns (comme le pretend "
            "Valentin), sont mauvais par nature et si les autres sont bons "
            "egalement par nature, ceux-ci ne doivent point etre loues, meme "
            "s'ils sont bons, car ils ont ete constitues tels. Les mechants "
            "ne doivent pas non plus etre blames, puisqu'ils ont ete faits "
            "tels'. Pour Amand, l'argument est 'a peine esquisse' — Irenee "
            "le mentionne 'par acquit de conscience' avant de developper "
            "longuement la preuve scripturaire. La transposition chretienne "
            "est claire : Dieu remplace les juges grecs comme regulateur "
            "supreme de la moralite, et les sanctions sont eternelles (et "
            "non temporelles)"
        ),
        description_en=(
            "Christianly transposed Carneadean echo in Adv. Haer. IV, 37, "
            "1-2 (original text preserved by John of Damascus in the Hiera) : "
            "'If some (as Valentinus claims) are evil by nature and others "
            "are equally good by nature, these should not be praised, even "
            "if they are good, for they were so constituted'. For Amand, the "
            "argument is 'barely sketched' — Irenaeus mentions it 'by "
            "conscience-clearing' before developing the scriptural proof at "
            "length"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 222-223",
            md_line_range="ll. 12290-12359",
            chapter="Livre II Ch. II §III (echo carneadien chez Irenee)",
            amand_chapter_actual="Echo Adv. Haer. IV.37.1-2 - argument transpose contre les gnostiques valentiniens",
            extra={
                "amand_witness_role": "transposed_echo_carneadean",
                "carneadean_origin": True,
                "amand_text_preservation": "Texte grec original conserve par Jean Damascene Hiera (ed. K. Holl TU 20.2 p. 63)",
                "amand_judgement": "A peine esquisse, mentionne par acquit de conscience",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_justin_1apol_43_three_carneadean_topoi",
        type="argument",
        label="Justin, 1 Apol. 43.1-8 - trois arguments carneadiens en forme squelettique",
        description=(
            "Trois arguments carneadiens identifiables par Amand dans 1 "
            "Apologie 43, 1-8 (ed. Pautigny 1904, p. 86-88) : (1) absence de "
            "louange et de blame dans l'hypothese du fatalisme — 'si tout "
            "etait produit par l'heimarmene, le bon n'est pas digne d'eloge, "
            "ni le mauvais blamable' ; (2) abolition de la responsabilite "
            "morale — 'si l'homme ne peut, par libre election de sa volonte, "
            "fuir le mal et choisir le bien, il n'a aucunement a repondre de "
            "n'importe laquelle de ses actions' ; (3) changement moral du "
            "meme homme — 'nous voyons le meme homme passer d'un extreme a "
            "l'autre. S'il etait fatalement bon ou mauvais, il n'y aurait "
            "pas de ces contradictions dans sa maniere d'agir, et ses "
            "frequents changements d'attitude morale seraient inconcevables'. "
            "Pour Amand, Justin reproduit ces arguments 'a l'etat "
            "squelettique', sans la souplesse de raisonnement de Carneade, "
            "et probablement sans connaissance directe de Clitomaque"
        ),
        description_en=(
            "Three identifiable Carneadean arguments per Amand in 1 Apology "
            "43, 1-8 (ed. Pautigny 1904, p. 86-88) : (1) absence of praise "
            "and blame in fatalist hypothesis ; (2) abolition of moral "
            "responsibility ; (3) moral change in the same man. For Amand, "
            "Justin reproduces these arguments 'in skeletal state', without "
            "Carneades's reasoning suppleness, and probably without direct "
            "knowledge of Clitomachus"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 205-207",
            md_line_range="ll. 11403-11679",
            chapter="Livre II Ch. I §IV (echos carneadiens chez Justin)",
            amand_chapter_actual="Trois topoi carneadiens dans 1 Apol. 43.1-8 - utilisation squelettique",
            extra={
                "amand_witness_role": "indirect_echo_carneadean_skeletal",
                "carneadean_origin": True,
                "amand_topoi_count": 3,
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_diodore_tarsus_impossibility_prediction_carneadean",
        type="argument",
        label="Diodore, Contra Heimarmenen VIII.45 - dilemme carneadien de la prediction astrologique",
        description=(
            "Dilemme antiastrologique deploye par Diodore de Tarse dans le "
            "Contra Heimarmenen Livre VIII §45 (= Photius Bibl. cod. 223, ed. "
            "Bekker p. 219a-219b = PG 103, 868AB). Argument carneadien "
            "classique : 'si ceux qui savent l'avenir que leur file la "
            "genesis peuvent l'eviter ou l'esquiver, la prediction "
            "astrologique est une sottise. Car dans ce cas, c'est notre libre "
            "arbitre qui est plus fort que la genesis'. Le dilemme se "
            "poursuit : si la connaissance future est elle-meme incluse dans "
            "la genesis, alors 'la genesis est scindee en deux fractions "
            "s'excluant l'une l'autre : l'une predit l'avenir, l'autre se "
            "moque de la prediction'. Inegalite ridicule. Et si meme la "
            "connaissance n'evite pas le destin, alors 'pourquoi faut-il "
            "apprendre en pure perte cet inflexible avenir, se consumer en "
            "soucis, se frapper soi-meme avant le coup fatal ?'. Amand "
            "rapproche cet argument de Ciceron De div. II.7.19-9.24"
        ),
        description_en=(
            "Antiastrological dilemma deployed by Diodore of Tarsus in Contra "
            "Heimarmenen Book VIII §45 (= Photius Bibl. cod. 223). Classical "
            "Carneadean argument on the impossibility-or-uselessness of "
            "astrological prediction. Amand draws parallel with Cicero De "
            "divinatione II.7.19-9.24"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 475-476",
            md_line_range="ll. 24225-24310",
            chapter="Livre II Ch. XI §III.1 (echos antiastrologiques carneadiens chez Diodore)",
            amand_chapter_actual="Dilemme carneadien de la prediction astrologique - Contra Heim. VIII.45",
            extra={
                "amand_witness_role": "indirect_carneadean_antiastrological",
                "carneadean_origin": True,
                "amand_parallel_text": "Ciceron De divinatione II.7.19-9.24",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_arian_job_pity_criminals_carneadean_5th_title",
        type="argument",
        label="Commentateur arien de Job, arg. 4 - pitie des criminels (Ve titre carneadien)",
        description=(
            "Argument central de la digression antiastrologique du "
            "commentateur arien anonyme sur Job 38, 7 (Paris. gr. 454 fol. "
            "123v, ed. Usener 1900 p. 329-330). Texte temoin etonnamment "
            "complet du cinquieme titre argumentatif carneadien : 'Si "
            "vraiment les dieux produisent les maux, comme tu le pretends de "
            "maniere impie, ne frappe pas celui qui a commis une faute, ne "
            "t'irrite pas contre ton epouse convaincue d'adultere, ne livre "
            "pas le meurtrier au chatiment, et accorde ton pardon a celui "
            "qui t'a derobe... Ces criminels sont traînes de force, ils ne "
            "courent point de bon gre, ils sont vaincus par la necessite de "
            "la heimarmene. Il faudrait donc avoir pitie d'eux plutot que "
            "de les punir'. L'argument se conclut par la citation de "
            "Republique X 617e : aitia helomenou theos anaitios. Pour Amand, "
            "c'est 'un des arguments les plus impressionnants que Carneade "
            "avait aiguises contre la theorie de l'heimarmene'"
        ),
        description_en=(
            "Central argument of the anonymous Arian commentator's "
            "antiastrological digression on Job 38, 7 (Paris. gr. 454 fol. "
            "123v, ed. Usener 1900 p. 329-330). Astonishingly complete "
            "witness-text of the fifth Carneadean argumentative heading : "
            "'If indeed the gods produce evils, as you impiously claim, do "
            "not strike the wrongdoer... It would be necessary to pity them "
            "rather than to punish them'. The argument concludes with the "
            "quotation of Republic X 617e : aitia helomenou theos anaitios. "
            "For Amand, 'one of the most impressive arguments Carneades had "
            "sharpened against the theory of heimarmene'"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 540, 545-547",
            md_line_range="ll. 27961-28304",
            chapter="Livre II Ch. XIII §II-§III (commentateur arien de Job)",
            amand_chapter_actual="Argument 4 du Pseudo-Origene Comm. in Iob - texte temoin carneadien pres-complet du Ve titre",
            extra={
                "amand_witness_role": "secondary_witness_carneadean_pity_argument",
                "carneadean_origin": True,
                "amand_argument_completeness": "Texte temoin etonnamment complet (Amand p. 546)",
                "amand_platonic_citation": "Conclu par Republique X.617e (aitia helomenou theos anaitios)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_arian_job_useless_prayer_under_fatalism",
        type="argument",
        label="Commentateur arien de Job, arg. 11 - inutilite de la priere sous le fatalisme",
        description=(
            "Onzieme et dernier argument de la digression antiastrologique du "
            "commentateur arien anonyme sur Job 38, 7 (Paris. gr. 454 fol. "
            "125v-126, ed. Usener 1900 p. 333). Argument carneadien sur "
            "l'inutilite de la priere dans l'hypothese du fatalisme absolu : "
            "'Pourquoi proposes-tu aux hommes des prieres tendant a ce qu'ils "
            "ne deviennent pas pires ? La priere est impuissante a flechir "
            "une invincible heimarmene, elle est incapable de la renverser. "
            "Prier les dieux pour obtenir l'eloignement des maux, et croire "
            "en meme temps a la toute-puissance de la heimarmene, c'est agir "
            "de maniere grossierement contradictoire'. Pour Amand (p. "
            "547-548), l'argument est traite assez librement par le "
            "commentateur arien, mais sa parente avec l'argumentation morale "
            "carneadienne reste manifeste"
        ),
        description_en=(
            "Eleventh and last argument of the anonymous Arian commentator's "
            "antiastrological digression on Job 38, 7. Carneadean argument "
            "on the uselessness of prayer in the hypothesis of absolute "
            "fatalism : 'prayer is powerless to bend an invincible heimarmene'. "
            "For Amand (p. 547-548), the argument is treated quite freely by "
            "the Arian commentator, but its kinship with Carneadean moral "
            "argumentation remains manifest"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 544, 547-548",
            md_line_range="ll. 28143-28323",
            chapter="Livre II Ch. XIII §III (commentateur arien de Job)",
            amand_chapter_actual="Argument 11 du Pseudo-Origene Comm. in Iob - inutilite priere sous fatalisme",
            extra={
                "amand_witness_role": "secondary_echo_carneadean",
                "carneadean_origin": True,
                "amand_judgement": "Traitement assez libre mais parente manifeste (Amand p. 547-548)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_methodius_libre_arbitre_obeissance_irenean",
        type="argument",
        label="Methode, De Autex. 16-17 - libre arbitre comme don d'obeissance irenenne",
        description=(
            "Argument de Methode dans le De Autexusio ch. 16-17 (ed. Bonwetsch "
            "GCS 27 p. 186-190 ; ed. Vaillant PO 22.5 p. 795-801). Methode "
            "reprend la conception irenenne du libre arbitre comme 'meilleur "
            "don que Dieu ait accorde a l'homme' : pouvoir d'obeir sans "
            "contrainte. Argument anti-instrumental : Dieu n'a pas voulu faire "
            "de l'homme 'un vulgaire instrument' incapable d'accorder ou "
            "refuser son obeissance. La justice exigeait qu'il possedat 'le "
            "pouvoir de se determiner en deux sens'. Banquet des dix Vierges "
            "VIII, 16-17, 228 reprend cette these : 'accomplir le bien ou le "
            "mal depend uniquement de nous, et non des astres'. L'Aglaophon "
            "I.38.3 ajoute : 'l'homme est libre et maître de lui-meme'"
        ),
        description_en=(
            "Methodius's argument in De Autexusio ch. 16-17. Methodius takes "
            "up the Irenaean conception of free will as 'the best gift God "
            "gave man' : power to obey without constraint. Anti-instrumental "
            "argument : God did not want to make man 'a vulgar instrument' "
            "incapable of granting or refusing obedience"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 333-335",
            md_line_range="ll. 17358-17506",
            chapter="Livre II Ch. VI §II (conception du libre arbitre chez Methode)",
            amand_chapter_actual="Don du libre arbitre comme obeissance volontaire - lignee irenenne",
            extra={
                "amand_witness_role": "irenean_lineage_not_carneadean",
                "amand_lineage": "Irenee -> Methode",
            },
        ),
        confidence=0.9,
    ),
]
