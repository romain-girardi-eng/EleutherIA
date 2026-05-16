"""Amand B9 — UPDATES list (metadata enrichments for existing nodes).

Targets light enrichments only — descriptions left intact :
- Justin Ch. I (p. 195-211) : person + 2 args
- Tatien Ch. I note (p. 208-211) : person + work
- Irénée Ch. II (p. 212-227) : person + 1 arg
- Bardesane Ch. III (p. 229-257) : person (will also get linked to LLR work created in inserts)
- Clément d'Alexandrie Ch. IV (p. 258-274) : person + 3 works
- Méthode d'Olympe Ch. VI (p. 326-341) : person + 2 works + 1 arg
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # =========================================================================
    # JUSTIN — Ch. I (p. 195-211, ll. 10992-11860)
    # =========================================================================
    {
        "id": "person_justin_martyr_2c_ce",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. I (p. 195-208)",
            "amand_witness_role": "indirect_echo_carneadean (Amand : Justin = premier écrivain chrétien grec à utiliser, sous forme squelettique, 3 arguments carnéadiens dans 1 Apol. 43)",
            "amand_judgement": (
                "Amand 1945, p. 205-207 : Justin n'a pas emprunté directement "
                "ses arguments à Clitomaque. Il a simplement repete une "
                "argumentation antifataliste anonyme ressassee par la tradition "
                "scolaire, ravalee a l'etat de lieu commun, et passee dans le "
                "patrimoine intellectuel des hommes cultives. Trois arguments "
                "carneadiens reconnaissables : (1) sans libre arbitre, "
                "louange/blame perdent leur sens ; (2) sans libre arbitre, la "
                "responsabilite morale est abolie ; (3) le meme homme passe "
                "successivement du bien au mal, ce qui exclut un destin "
                "fataliste fixe"
            ),
            "amand_key_text": "1 Apol. 43, 1-8 (ed. Pautigny 1904, p. 86-88) + 1 Apol. 28, 3-4 + 2 Apol. 7, 3-9",
            "amand_principal_editions_cited": [
                "L. Pautigny, Justin Apologies, Textes et documents (Picard, 1904)",
                "G. Archambault, Justin Dialogue avec Tryphon, Textes et documents 8 (Picard, 1909)",
            ],
        },
    },
    {
        "id": "argument_justin_antifatalism",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. I §IV (p. 205-207)",
            "amand_witness_role": "indirect_carneadean_topos (Amand : echo perceptible non-direct)",
            "amand_qualification": (
                "Amand 1945, p. 207 : 'Ce chapitre de Justin ne peut etre regarde "
                "comme un texte temoin de l'argumentation morale de Carneade. "
                "Il nous en offre cependant un echo bien perceptible'"
            ),
        },
    },
    {
        "id": "argument_justin_prophecy_freedom",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. I §III (p. 202-204)",
            "amand_judgement": (
                "Amand 1945, p. 203-204 : Justin combat l'objection fataliste "
                "selon laquelle l'accomplissement des propheties resulte de "
                "l'heimarmene. Sa reponse mele preuve scripturaire (Dt 30, 15.19 ; "
                "Is 1, 16-20) et axiome platonicien (aitia helomenou theos anaitios, "
                "Rep. X 617e), 'que les Neo-Platoniciens et les theologiens "
                "chretiens repetent a l'envi'"
            ),
        },
    },
    # =========================================================================
    # TATIEN — Note supplementaire Ch. I (p. 208-211, ll. 11681-11828)
    # =========================================================================
    {
        "id": "person_tatian",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. I Note supplementaire (p. 208-211)",
            "amand_witness_role": "non_witness_carneadean (polemique antiastrologique mais aucune trace d'argumentation morale carneadienne)",
            "amand_judgement": (
                "Amand 1945, p. 211 : 'Ces breves indications jetees en passant "
                "ne demontrent nullement une dependance directe ou indirecte a "
                "l'egard de l'argumentation morale antifataliste de Carneade. La "
                "doctrine chretienne avec son dogme du libre arbitre, condition "
                "de la vie morale, fournissait elle-meme naturellement a Tatien "
                "l'objection qui se fonde sur le fait de la responsabilite de "
                "nos actes'. Tatien = 'Tertullien des Grecs, depourvu toutefois "
                "de genie'. Son antifatalisme demeure purement religieux, fonde "
                "sur le dogme chretien et non sur la dialectique philosophique"
            ),
            "amand_key_text": "Discours aux Grecs ch. 7-11 (ed. E. Schwartz, TU 4.1, Leipzig 1888)",
        },
    },
    {
        "id": "work_tatian_oratio",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. I Note (p. 208-211)",
            "amand_focus_chapters": "Oratio 7-11 (autexousion, antiastrologie, demons inventeurs de l'heimarmene)",
            "amand_principal_edition_cited": "E. Schwartz, Tatiani oratio ad Graecos, TU 4.1 (Hinrichs, Leipzig 1888)",
            "amand_secondary_reference": "A. Puech, Recherches sur le Discours aux Grecs de Tatien, Bibliotheque de la Faculte des Lettres de l'Universite de Paris 17 (Alcan, 1903)",
        },
    },
    # =========================================================================
    # IRENEE — Ch. II (p. 212-227, ll. 11830-12362)
    # =========================================================================
    {
        "id": "person_irenaeus_d202",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. II (p. 212-223)",
            "amand_witness_role": "transposed_echo_carneadean (Amand : echo lointain mais reconnaissable de l'argument carneadien sur l'inutilite de la louange et du blame, transpose sur le plan chretien)",
            "amand_judgement": (
                "Amand 1945, p. 222-223 : Irenee 'repete un lieu commun rouille "
                "et emousse qu'il a pris a une source litteraire quelconque (un "
                "opuscule theologique, ou un manuel philosophique, etc.), ou bien "
                "qu'il a retrouve simplement dans sa memoire'. Il ne se doute "
                "probablement pas que Carneade fut le createur ou du moins le "
                "propagateur de ce topos. L'eveque gaulois 'ne recite pas "
                "mecaniquement une demonstration neo-academicienne, mais il la "
                "transpose, en melangeant au contenu hellenique des pensees "
                "specifiquement chretiennes' : libre arbitre dogmatique, Dieu "
                "regulateur supreme de la moralite, consequences eternelles des "
                "actions"
            ),
            "amand_key_text": "Adv. Haer. IV, 37, 1-2 (texte original conserve par Jean Damascene dans les Hiera, ed. K. Holl, TU 20.2, Leipzig 1901, p. 63)",
            "amand_principal_editions_cited": [
                "PG 7 (Migne) - Adversus Haereses dans la traduction latine litterale du IIIe siecle",
                "K. Holl, Fragmente vornicanischer Kirchenvater aus den Sacra Parallela, TU 20.2 (Hinrichs, Leipzig 1901)",
                "K. Ter-Mekerttschian-Wilson, Demonstration de la predication apostolique, PO XII fasc. 5 (Firmin-Didot, 1919)",
            ],
        },
    },
    {
        "id": "work_irenaeus_adversus_haereses_book4",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. II §III (p. 222-223)",
            "amand_focus_passage": "Adv. Haer. IV, 37, 1-2 — preuve rationnelle anti-gnostique du libre arbitre, ou Amand decele l'echo carneadien",
            "amand_witness_role": "transposed_echo_carneadean",
        },
    },
    # =========================================================================
    # BARDESANE — Ch. III (p. 229-257, ll. 12563-13920)
    # =========================================================================
    {
        "id": "person_bardesanes_the_syrian_3r8s0u76",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. III (p. 229-257) — temoin secondaire crucial pour la transmission carneadienne",
            "amand_witness_role": "secondary_witness_bardesanes (utilisation tres personnelle et amplifiee de l'argumentation antifataliste de Carneade)",
            "amand_witness_rank": "secondary",
            "amand_judgement": (
                "Amand 1945, p. 232-233, 243-244 : Bardesane d'Edesse, philosophe-"
                "theologien syrien (154-222), n'est ni un gnostique au sens "
                "valentinien ni un orthodoxe pur. Sa theologie hybride accepte un "
                "fatalisme astrologique mitige : les astres regissent les "
                "phenomenes corporels et les evenements exterieurs, mais l'ame et "
                "le libre arbitre y echappent. Dans le Livre des lois des pays "
                "(dialogue syriaque redige par son disciple Philippe), il deploie "
                "avec une profusion ethnographique sans precedent l'argument "
                "carneadien des nomima barbarika, et reproduit plusieurs autres "
                "topoi neo-academiciens. 'Peut-etre le premier a avoir mis en "
                "oeuvre [l'argument ethnographique] avec une telle profusion et "
                "une telle exactitude documentaire'"
            ),
            "amand_doctrine_key": (
                "Triple delimitation : (1) physis ou ananke = necessite naturelle "
                "qui regit les actions corporelles communes aux animaux et aux "
                "hommes ; (2) heimarmene des Chaldeens = configuration astrale a "
                "la naissance qui determine richesse/pauvrete, sante/maladie, "
                "evenements exterieurs ; (3) autexousion ou to eph hemin = "
                "libre arbitre de l'ame humaine, image de Dieu, intacte hors "
                "des phenomenes corporels"
            ),
            "language": "syriac",
            "amand_principal_editions_cited": [
                "F. Nau, Bardesanes. Liber legum regionum (Patrologia syriaca I.2, Firmin-Didot 1907, col. 490-657) — texte syriaque + traduction latine",
                "W. Cureton, Spicilegium syriacum (Londres 1855) — editio princeps + traduction anglaise",
                "F. Nau, Bardesane l'astrologue. Le livre des lois des pays (Paris 1899) — traduction francaise + introduction",
                "G. Levi Della Vida, Bardesane. Il dialogo delli leggi dei paesi (Rome 1921)",
                "A. Merx, Bardesanes von Edessa (Halle 1863) — etude + traduction allemande p. 25-55",
            ],
            "amand_key_studies_cited": [
                "F. Haase, Zur Bardesanischen Gnosis, TU 34.4 (Leipzig 1910)",
                "H. H. Schaeder, Bardesanes von Edessa in der Uberlieferung der griechischen und der syrischen Kirche, ZKG 51 (1932) 21-74",
                "F. Nau, Une biographie inedite de Bardesane l'astrologue (Paris 1897)",
            ],
            "amand_eusebius_attestation": (
                "Eusebe HE VI.30.2 mentionne un pros Antoninon hikanotatos peri "
                "heimarmenes dialogos ; Eusebe PE VI.10 cite de longs extraits "
                "grecs du dialogue pros tous hetairous (= identique au LLR "
                "syriaque selon Nau, Noldeke, Levi Della Vida, Schaeder)"
            ),
        },
    },
    # =========================================================================
    # CLEMENT D'ALEXANDRIE — Ch. IV (p. 258-274, ll. 13925-14672)
    # =========================================================================
    {
        "id": "person_clement_alexandria",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. IV (p. 258-274)",
            "amand_witness_role": "minimal_echo_carneadean (Amand : seulement deux echos assez lointains dans toute l'oeuvre conservee)",
            "amand_judgement": (
                "Amand 1945, p. 270-273 : Clement, mystique et moraliste, n'a pas "
                "ete frappe par l'influence du fatalisme astrologique sur les "
                "chretiens populaires comme le sera son disciple Origene. Il "
                "n'entreprend donc pas de refutation systematique de l'heimarmene. "
                "Le mot heimarmene 'brille par son absence' dans ses ecrits "
                "personnels (Strom. I-VII), n'apparaissant que dans les Excerpta "
                "ex Theodoto (citations valentiniennes). Clement n'a mentionne "
                "Carneade qu'une seule fois (Strom. I, 64, 1), dans une liste "
                "scolaire de successions academiciennes empruntee a un manuel. "
                "Deux echos lointains : (1) Strom. I, 83, 5 — argument sur "
                "louange/blame/recompense/chatiment incompatibles avec absence "
                "de libre arbitre ; (2) Strom. II, 11, 1-2 — argument transpose "
                "sur foi/incroyance contre Basilide/Valentin"
            ),
            "amand_key_texts": [
                "Stromateis I, 82-84 (echo sur louange/blame)",
                "Stromateis II, 11, 1-2 (transposition chretienne contre Basilide/Valentin)",
                "Stromateis VI, 148, 1-3 (le seul passage personnel sur l'astrologie)",
            ],
            "amand_principal_edition_cited": "O. Stahlin, Clemens Alexandrinus, GCS (Hinrichs, Leipzig I-1905, II-1906, III-1909, IV-1934/36)",
            "amand_secondary_references": [
                "M. Pohlenz, Klemens von Alexandreia und sein hellenisches Christentum, AAWG Phil.-Hist. Kl. 1943 nr 3",
                "J. Meifort, Der Platonismus bei Clemens Alexandrinus, Heidelberger Abh. 17 (Mohr Tubingen 1928)",
                "P. Camelot, Clement d'Alexandrie et l'utilisation de la philosophie grecque, RSR 21 (1931) 541-569",
                "W. Bousset, Judisch-christlicher Schulbetrieb in Alexandria und Rom, FRLANT NF 6 (Gottingue 1915)",
            ],
        },
    },
    {
        "id": "work_clement_stromateis",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. IV §III (p. 270-273) — ouvrage central pour les deux echos carneadiens",
            "amand_focus_passages": [
                "Strom. I, 82-84 (echo louange/blame ; cas du soldat-bouclier et demon de Socrate)",
                "Strom. II, 11, 1-2 (transposition chretienne contre Basilide/Valentin sur necessite naturelle vs foi volontaire)",
                "Strom. I, 64, 1 (seule mention de Carneade)",
                "Strom. VI, 148, 1-3 (unique discussion personnelle de l'astrologie)",
            ],
        },
    },
    {
        "id": "work_clement_paedagogus",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. IV (p. 258-261, 268)",
            "amand_witness_role": "non_witness_carneadean — utilite morale des sanctions sociales (Paed. I, 94, 1)",
            "amand_doctrinal_note": "Amand p. 268-269 : conseils de morale stoicienne (Musonius Rufus) ; theologie morale empruntee largement a Chrysippe, Panetius, Posidonius",
        },
    },
    {
        "id": "work_clement_protrepticus",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. IV (p. 258-260)",
            "amand_witness_role": "non_witness_carneadean — exhortation evangelique generale",
        },
    },
    # =========================================================================
    # METHODE D'OLYMPE — Ch. VI (p. 326-341, ll. 17085-17791)
    # =========================================================================
    {
        "id": "person_methodius_olympus_d311",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. VI (p. 326-341)",
            "amand_witness_role": "indirect_echo_carneadean (Amand : utilisation indirecte mais reconnaissable de l'argumentation morale antifataliste, probablement via un manuel scolaire / hypomnema)",
            "amand_judgement": (
                "Amand 1945, p. 340 : 'Une utilisation directe des arguments "
                "ethiques de Carneade par l'intermediaire de Clitomaque doit etre "
                "absolument exclue. Methode n'a meme pas reproduit les details "
                "de ceux-ci. A ces syllogismes arides, raccourcis et depourvus "
                "de toute forme oratoire, il convient cependant d'attribuer en "
                "definitive une origine neo-academicienne. Methode les aura "
                "probablement extraits d'un manuel scolaire ; on sait la vogue "
                "des hypomnemata dans l'enseignement philosophique a l'epoque "
                "imperiale'. Le Banquet des dix Vierges VIII, 16, 227-229 "
                "contient trois syllogismes ou Amand decele cette origine "
                "carneadienne, sans transposition chretienne notable"
            ),
            "amand_principal_editions_cited": [
                "G. N. Bonwetsch, Methodius, GCS 27 (Hinrichs, Leipzig 1917)",
                "A. Vaillant, Le De Autexusio de Methode d'Olympe. Version slave et texte grec, PO 22 fasc. 5 (Firmin-Didot, 1930)",
            ],
            "amand_secondary_reference": "J. Farges, Les idees morales et religieuses de Methode d'Olympe (Paris 1929)",
        },
    },
    {
        "id": "work_methodius_symposium_144841d0",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. VI §III-§IV (p. 335-341)",
            "amand_witness_role": "indirect_carneadean_topos (discours VIII pretendu par Thecla : trois syllogismes ou Amand decele l'origine neo-academicienne)",
            "amand_focus_passage": "Banquet VIII, 13-17, 208-230 (ed. Bonwetsch, p. 98 l. 16 - p. 111 l. 12) — polemique antiastrologique et antifataliste",
            "amand_principal_edition_cited": "G. N. Bonwetsch, Methodius, GCS 27 (Hinrichs, Leipzig 1917)",
        },
    },
    {
        "id": "work_methodius_de_autexusio_4c37c892",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. VI §II (p. 332-335)",
            "amand_witness_role": "supplementary_echo_carneadean (De Autex. 16, 6 : echo fugace de l'argument sur l'inutilite de la louange et du blame dans l'hypothese du fatalisme absolu)",
            "amand_focus_passage": "De Autexusio ch. 16 (ed. Bonwetsch, GCS 27, p. 186-188 ; ed. Vaillant, PO 22.5, p. 795-801)",
            "amand_doctrinal_note": (
                "Amand p. 333-335 : Methode reprend Irenee plus que Platon. Le "
                "libre arbitre est don divin permettant l'obeissance volontaire "
                "a Dieu. Texte original grec connu par recoupement avec la "
                "version slave et la Refutation des sectes d'Eznik (cf. Bonwetsch "
                "p. 187 apparat critique)"
            ),
        },
    },
    {
        "id": "argument_methodius_theodicy_autexousion",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. VI §II.16-17 (De Autex.)",
            "amand_qualification": (
                "Amand 1945, p. 333-334 : Methode situe la theodicee dans la "
                "lignee d'Irenee. Le libre arbitre n'est pas une fin en soi "
                "mais le moyen d'obeir volontairement a Dieu, qui n'a pas voulu "
                "faire de l'homme 'un vulgaire instrument'. Argument de "
                "l'incorruptibilite eternelle attachee a l'obeissance libre"
            ),
        },
    },
]
