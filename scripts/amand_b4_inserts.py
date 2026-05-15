"""B4 inserts : new nodes for Alexandre + Firmicus."""
from __future__ import annotations
from typing import Any
from amand_b4_utils import md_base, make_node  # type: ignore

NEW_INSERTS: list[dict[str, Any]] = []

# ============================================================================
# ALEXANDRE D'APHRODISE — Ch. V (p. 127-156, ll. 7670-9249)
# ============================================================================

# --- Syntheses §I (portrait commentateur) ---

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_portrait_exegete",
    ntype="synthesis", label="Amand 1945 — Alexandre d'Aphrodise comme « second Aristote » et exégète scrupuleux",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. V §I, p. 127-138, ll. 7670-7848). Selon Amand, Alexandre "
        "d'Aphrodise, scholarque péripatéticien à Athènes de 198 à 217 sous Septime Sévère, est "
        "communément regardé comme le plus savant, le plus solide et le plus intelligent interprète "
        "antique des œuvres aristotéliciennes. La postérité lui a décerné le titre d'« exégète » par "
        "excellence et celui de « second Aristote ». Esprit froid et positif, hostile à la mentalité "
        "religieuse, superstitieuse et mystique du siècle des Antonins, Alexandre borne son ambition à "
        "exposer dans sa pureté l'aristotélisme authentique. Sa méthode commentariste : signaler les "
        "leçons divergentes de la tradition manuscrite, peser leur signification, tracer le plan des "
        "chapitres en montrant les rapports mutuels, résoudre les contradictions réelles ou apparentes, "
        "proposer ses solutions avec réserve et modestie. Amand s'appuie sur Zeller (Ph. Gr. III/1⁶ "
        "p. 817-830), Praechter dans Ueberweg-Praechter (1926, p. 564-565), l'article de A. Gercke dans "
        "Pauly-Wissowa RE I 1894 col. 1453-1455, et l'ouvrage récent (à l'époque) de P. Moraux "
        "(Alexandre d'Aphrodise, exégète de la noétique d'Aristote, Liège-Paris 1942)."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. V §I, p. 127-138, ll. 7670-7848). According to Amand, "
        "Alexander of Aphrodisias, Peripatetic scholarch in Athens from 198 to 217 under Septimius "
        "Severus, is commonly regarded as the most learned, sound and intelligent ancient interpreter "
        "of Aristotle's works. Posterity has bestowed on him the titles 'exegete' par excellence and "
        "'second Aristotle'. A cold, positive mind, hostile to the religious, superstitious and "
        "mystical mentality of the Antonine age, Alexander limits his ambition to expounding "
        "authentic Aristotelianism in its purity. His commentary method: signaling divergent readings "
        "of the manuscript tradition, weighing their significance, mapping out chapter plans showing "
        "mutual relations, resolving real or apparent contradictions, proposing solutions with "
        "reserve and modesty. Amand draws on Zeller (Ph. Gr. III/1⁶ p. 817-830), Praechter in "
        "Ueberweg-Praechter (1926, p. 564-565), A. Gercke's article in Pauly-Wissowa RE I 1894 col. "
        "1453-1455, and Moraux's (then recent) book (Alexandre d'Aphrodise, exégète de la noétique "
        "d'Aristote, Liège-Paris 1942)."
    ),
    md=md_base(
        page_range="p. 127-138", md_line_range="ll. 7670-7848",
        chapter="Livre I Ch. V §I (Alexandre commentateur d'Aristote)",
        chapter_actual="Livre I Ch. V §I — Portrait du commentateur",
        confidence=0.9,
        cited_editions=[
            "E. Zeller, Philosophie der Griechen III/1⁶, 1923, p. 817-830",
            "H. Meyer, Geschichte der alten Philosophie, München 1925, p. 389-391",
            "Ueberweg-Praechter, Philosophie des Altertums, 1926, p. 564-565",
            "A. Gercke, art. Alexandros (94) von Aphrodisias, Pauly-Wissowa RE I 1894, col. 1453-1455",
            "P. Moraux, Alexandre d'Aphrodise, exégète de la noétique d'Aristote, Bibliothèque de la Faculté de Philosophie et Lettres de l'Université de Liège, Fasc. 99, Liège-Paris 1942",
            "P. Wilpert, Reste verlorener Aristotelesschriften bei Alexander von Aphrodisias, Hermes 75 (1940) p. 369-396",
        ],
        extra={
            "amand_thesis_type": "doctrinal_portrait",
            "engages_with_scholars": ["Zeller", "Praechter", "Gercke", "Moraux", "Wilpert"],
            "alexander_scholarchate_athens": "198-217 CE sous Septime Sévère",
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_naturalist_materialism",
    ntype="synthesis",
    label="Amand 1945 — Tendance naturaliste et matérialiste d'Alexandre (sur l'âme et l'intellect)",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. V §I, p. 137-138 + notes p. 137-138, ll. 7760-7848). En "
        "dépit de sa volonté affichée d'exposer Aristote purement et simplement, Alexandre est conduit "
        "par sa tendance naturaliste à s'écarter de la doctrine du fondateur du Lycée sur deux points "
        "majeurs : (1) nominalisme strict : l'universel n'existe que dans la pensée comme résultat "
        "d'une abstraction des êtres individuels ; seul l'individuel existe en soi et par nature. "
        "(2) Matérialisme psychologique : corps et âme constituent un composé unique et indivisible ; "
        "l'âme, forme du corps organique, naît et périt avec le corps. L'intelligence humaine "
        "(ὁ νοῦς ὁ ἔνυλος = νοῦς ὑλικός) est une faculté de l'âme, mais l'intellect séparé est identique "
        "à Dieu. Selon Amand (citant Moraux 1942), un secret antagonisme oppose dans la pensée "
        "d'Alexandre la propension foncière au matérialisme avec le souci de s'en tenir à "
        "l'aristotélisme orthodoxe — conflit interne qui « vicie l'orthodoxie de l'alexandrisme et "
        "compromet la cohérence de ce système ». Amand qualifie Alexandre de « philosophe mineur »."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. V §I, p. 137-138 + footnotes, ll. 7760-7848). Despite "
        "his proclaimed will to expound Aristotle purely and simply, Alexander is led by his "
        "naturalistic tendency to depart from the Lyceum founder's doctrine on two major points: "
        "(1) strict nominalism: the universal exists only in thought as the result of abstraction from "
        "individual beings; only the individual exists in itself by nature. (2) Psychological "
        "materialism: body and soul constitute a unique indivisible composite; the soul, as form of "
        "the organic body, is born and perishes with the body. Human intelligence (ὁ νοῦς ὁ ἔνυλος = "
        "νοῦς ὑλικός) is a faculty of the soul, but the separated intellect is identical with God. "
        "According to Amand (citing Moraux 1942), a secret antagonism opposes in Alexander's thought "
        "the fundamental propensity to materialism with the concern to adhere to orthodox "
        "Aristotelianism — an internal conflict that 'vitiates the orthodoxy of Alexandrism and "
        "compromises the coherence of this system'. Amand calls Alexander a 'minor philosopher'."
    ),
    md=md_base(
        page_range="p. 137-138", md_line_range="ll. 7760-7848",
        chapter="Livre I Ch. V §I (Alexandre commentateur d'Aristote)",
        chapter_actual="Livre I Ch. V §I — Tendance naturaliste",
        confidence=0.85,
        cited_editions=[
            "E. Zeller, Ph. Gr. III/1⁶, 1923, p. 822-827",
            "P. Moraux, Alexandre d'Aphrodise, Liège-Paris 1942, spécialement p. 17-20",
        ],
        extra={
            "amand_thesis_type": "doctrinal_portrait_naturalism",
            "amand_judgement_register": "evaluation_critique_negative",
            "amand_qualifier": "philosophe mineur",
            "key_alexandrian_doctrines": ["nominalisme", "matérialisme psychologique", "noûs hylikos vs noûs poiêtikos"],
        },
    ),
))


# --- Syntheses §II (importance du De fato + problème des sources) ---

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_de_fato_triple_composition",
    ntype="synthesis",
    label="Amand 1945 — Composition triple du De Fato d'Alexandre (péripatétisme + Carnéade via Clitomaque + Chrysippe direct)",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. V §II.2, p. 139-140, ll. 7820-7920). Amand identifie "
        "trois apports doctrinaux différents que le commentateur d'Aristote concilie dans sa synthèse "
        "du Περὶ εἱμαρμένης : (1) Élément dominant : tradition d'enseignement péripatéticien sur "
        "τὸ ἐφ' ἡμῖν et εἱμαρμένη qu'Alexandre recueille comme « continuateur et interprète » des "
        "scholarques de l'époque impériale, problèmes de « brûlante actualité » mis en œuvre dans le "
        "sens de l'aristotélisme le plus orthodoxe. (2) Arsenal carnéadien néo-académicien : Alexandre "
        "ajoute à cette tradition autochtone l'ensemble des arguments les plus forts que la Nouvelle "
        "Académie avait proposés contre le fatalisme intégral de Chrysippe ; hypothèse de filiation "
        "via Clitomaque ou un manuel d'école, présentée comme « raisonnable » et non gratuite par "
        "Amand. (3) Lecture directe et critique des ouvrages mêmes de Chrysippe, avec conservation de "
        "nombreux passages et arguments ad hominem dirigés contre le déterminisme rigoureux — selon "
        "le jugement de H. von Arnim (SVF I p. XVI-XVII), Alexandre est un témoignage de très grande "
        "fidélité documentaire sur Chrysippe."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. V §II.2, p. 139-140, ll. 7820-7920). Amand identifies "
        "three different doctrinal contributions that the commentator of Aristotle reconciles in his "
        "Περὶ εἱμαρμένης synthesis: (1) Dominant element: Peripatetic teaching tradition on "
        "τὸ ἐφ' ἡμῖν and εἱμαρμένη which Alexander gathers as 'continuator and interpreter' of "
        "imperial-period scholarchs, problems of 'burning topicality' implemented in the most "
        "orthodox Aristotelian sense. (2) Neo-Academic Carneadean arsenal: Alexander adds to this "
        "indigenous tradition the strongest arguments the New Academy had proposed against "
        "Chrysippus' absolute fatalism; hypothesis of filiation via Clitomachus or a scholastic "
        "handbook, presented as 'reasonable' and not gratuitous by Amand. (3) Direct critical reading "
        "of Chrysippus' own works, with preservation of many passages and ad hominem arguments "
        "directed against rigorous determinism — per H. von Arnim's judgement (SVF I p. XVI-XVII), "
        "Alexander is a witness of very high documentary fidelity on Chrysippus."
    ),
    md=md_base(
        page_range="p. 139-140", md_line_range="ll. 7820-7920",
        chapter="Livre I Ch. V §II.2 (Le Περὶ εἱμαρμένης : son importance, problème des sources)",
        chapter_actual="Livre I Ch. V §II.2 — Composition doctrinale triple",
        confidence=0.8,
        cited_editions=[
            "H. von Arnim, Stoicorum Veterum Fragmenta I, Leipzig Teubner 1903, p. XVI-XVII",
            "P. Wilpert, Reste verlorener Aristotelesschriften bei Alexander, Hermes 75 (1940) p. 369-396",
        ],
        extra={
            "amand_thesis_type": "philological_source_reconstruction",
            "three_sources_identified_by_amand": [
                "tradition_peripatetic_imperial_scholarchs",
                "carneadean_arsenal_via_clitomachus_conjectural",
                "direct_reading_of_chrysippus_works",
            ],
            "amand_judgement_on_conjecture_register": "haute_probabilite_avoue",
            "engages_with_scholars": ["von Arnim", "Wilpert"],
        },
    ),
))


# --- Syntheses §II.3 (déterminisme physique + contingence + libre arbitre) ---

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_physical_determinism_sublunar",
    ntype="synthesis",
    label="Amand 1945 — Déterminisme physique sublunaire chez Alexandre (astres comme causes secondes des mixtes)",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. V §II.3.1, p. 140-141, ll. 7849-7926). Selon Amand, "
        "Alexandre maintient rigoureusement le déterminisme physique dans le monde matériel sublunaire "
        "et accorde sans peine à l'astrologie que les astres errants et fixes produisent réellement, "
        "sous l'orbe de la lune, les générations, les destructions, les transformations et tous les "
        "mouvements locaux. Tout changement a pour principe un mouvement local, et tout mouvement "
        "local sublunaire a pour cause l'éternelle circulation des sphères célestes (Quaestiones "
        "naturales II.3, Bruns p. 47-50). Le soleil, la lune et les planètes en parcourant le Zodiaque "
        "dispensent chaleur et sécheresse, ou les qualités contraires, aux parties de la matière qui "
        "leur sont proches, déterminant ainsi les corps simples (feu, air, eau, terre) puis octroyant "
        "une plus grande perfection aux mixtes (cf. Περὶ κράσεως καὶ αὐξήσεως II, Bruns p. 225). "
        "Cette puissance céleste « astrologique » est donc cause de génération, corruption et "
        "transformation des corps simples. P. Duhem (Le système du monde II, 1914, p. 302, 344-356) "
        "rapproche ces hypothèses des théories des alchimistes grecs et arabes."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. V §II.3.1, p. 140-141, ll. 7849-7926). According to "
        "Amand, Alexander rigorously maintains physical determinism in the material sublunar world and "
        "readily grants astrology that wandering and fixed stars actually produce, beneath the lunar "
        "orb, generations, destructions, transformations and all local motions. Every change has a "
        "local motion as principle, and every sublunar local motion is caused by the eternal "
        "circulation of celestial spheres (Quaestiones naturales II.3, Bruns p. 47-50). Sun, moon and "
        "planets, traversing the Zodiac, dispense heat and dryness, or contrary qualities, to the "
        "nearby parts of matter, thus determining the simple bodies (fire, air, water, earth) and "
        "then granting greater perfection to the mixtures (cf. Περὶ κράσεως καὶ αὐξήσεως II, Bruns "
        "p. 225). This celestial 'astrological' power is therefore cause of generation, corruption "
        "and transformation of simple bodies. P. Duhem (Le système du monde II, 1914, p. 302, "
        "344-356) connects these hypotheses to Greek and Arab alchemists' theories."
    ),
    md=md_base(
        page_range="p. 140-141", md_line_range="ll. 7849-7926",
        chapter="Livre I Ch. V §II.3.1 (Le déterminisme physique selon Alexandre)",
        chapter_actual="Livre I Ch. V §II.3.1 — Déterminisme physique sublunaire",
        confidence=0.9,
        cited_editions=[
            "Alexandre d'Aphrodise, Quaestiones naturales II.3, éd. I. Bruns, Suppl. Arist. II.2, Berlin 1892, p. 47-50",
            "Alexandre d'Aphrodise, Περὶ κράσεως καὶ αὐξήσεως II, éd. Bruns p. 225 l. 30-35",
            "P. Duhem, Le système du monde, t. II, Paris 1914, p. 302, 344-356",
        ],
        extra={
            "amand_thesis_type": "doctrinal_portrait_physics",
            "alexander_position_summary": "Déterminisme physique sublunaire strict + astrologie comme causalité secondaire reconnue",
            "engages_with_scholars": ["Duhem"],
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_defends_contingency",
    ntype="synthesis",
    label="Amand 1945 — Alexandre défenseur de la contingence (τὸ ἐνδεχόμενον) contre le fatalisme chrysippéen",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. V §II.3.2, p. 141-142, ll. 7927-7990). Alexandre refuse "
        "le déterminisme rigoureux et universel de Chrysippe. Dans le Περὶ εἱμαρμένης il démontre "
        "longuement (chapitres 9 et 11-15, Bruns p. 176, 178-186) que le déterminisme stoïcien sans "
        "exception supprime entièrement la contingence, à l'existence de laquelle il ne veut pas "
        "renoncer. Définition d'Alexandre (De Fato 9, Bruns p. 176 l. 1-2) : τὸ ἐνδεχομένως γεγονὸς "
        "ἐν τινι καὶ μὴ γεγονέναι ἐν αὐτῷ οἷόν τε ἦν — « ce qui s'est produit dans une chose, mais qui "
        "pouvait également ne pas s'y produire ». À l'exemple d'Aristote, Alexandre montre que nier "
        "la contingence rend incompréhensible la délibération qui précède l'accomplissement d'une "
        "action : à quoi bon peser les deux partis et les comparer entre eux si celui que nous devons "
        "prendre est irrémédiablement fixé d'avance par l'εἱμαρμένη ? Le fait que nous discutons et "
        "tenons conseil avant d'agir est preuve manifeste qu'il y a dans l'avenir des événements "
        "contingents. Amand emploie aussi le terme τὸ ὁπότερα (« le l'un ou l'autre »)."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. V §II.3.2, p. 141-142, ll. 7927-7990). Alexander "
        "refuses Chrysippus' rigorous and universal determinism. In Περὶ εἱμαρμένης he argues at "
        "length (chapters 9 and 11-15, Bruns p. 176, 178-186) that exceptionless Stoic determinism "
        "entirely abolishes contingency, whose existence he refuses to surrender. Alexander's "
        "definition (De Fato 9, Bruns p. 176 ll. 1-2): τὸ ἐνδεχομένως γεγονὸς ἐν τινι καὶ μὴ "
        "γεγονέναι ἐν αὐτῷ οἷόν τε ἦν — 'that which has come about in a thing but which could equally "
        "have not come about in it'. Following Aristotle, Alexander shows that denying contingency "
        "makes incomprehensible the deliberation preceding any action: why weigh two options and "
        "compare them if the one we must take is irretrievably fixed in advance by εἱμαρμένη? The "
        "fact that we discuss and deliberate before acting is manifest proof of future contingent "
        "events. Amand also uses the term τὸ ὁπότερα ('either-or')."
    ),
    md=md_base(
        page_range="p. 141-142", md_line_range="ll. 7927-7990",
        chapter="Livre I Ch. V §II.3.2 (La contingence dans la philosophie d'Alexandre)",
        chapter_actual="Livre I Ch. V §II.3.2 — Défense de la contingence",
        confidence=0.95,
        cited_editions=[
            "Alexandre d'Aphrodise, De Fato 9, éd. Bruns p. 176 l. 1-2 (définition τὸ ἐνδεχόμενον)",
            "Alexandre d'Aphrodise, De Fato 11-15, éd. Bruns p. 178-186 (démonstration anti-Chrysippe)",
        ],
        extra={
            "amand_thesis_type": "doctrinal_portrait_metaphysics",
            "alexander_key_terms_gr": ["τὸ ἐνδεχόμενον", "τὸ ὁπότερα"],
            "aristotelian_lineage": "argument deliberatif EN III.3 + De interpretatione 9",
        },
    ),
))


# --- Syntheses §III (Argumentation morale antifataliste de Carnéade dans De fato 16-20) ---

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_witness_n2_identification",
    ntype="synthesis",
    label="Amand 1945 — Identification du témoin n°2 : De Fato 16-20 d'Alexandre comme dossier carnéadien le plus rigoureux",
    period=None, school=None, role=None,
    description=(
        "Synthèse philologique d'Amand 1945 (Livre I Ch. V §III.1, p. 143-145, ll. 8050-8133). "
        "Identification du témoin n°2 sur la liste des six textes témoins (cf. p. 571-572). Amand "
        "affirme : « Il suffit de lire même superficiellement ces cinq chapitres pour y reconnaître "
        "immédiatement une utilisation aussi précise qu'étendue de l'argumentation antifataliste du "
        "fondateur de la Nouvelle Académie » (p. 144). Question philologique posée par Amand : "
        "Alexandre reproduit-il purement et simplement, d'après une source littéraire telle que "
        "Clitomaque, les arguments de Carnéade en les accommodant à son style froid et positif ? Se "
        "borne-t-il à les résumer en les étoffant à l'occasion de preuves de son cru ? Est-il "
        "tributaire d'une tradition d'école ? Amand juge prématuré de trancher mais affirme : « la "
        "gerbe de raisonnements habiles, abondants et atteignant droit au but, a été originairement "
        "liée par un esprit puissant et subtil qui ne peut être que Carnéade » (p. 144). Amand "
        "qualifie ce témoin comme : (a) le plus rigoureux logiquement parmi les six ; (b) construit "
        "selon une méthode toute philosophique ; (c) seul des six témoins à offrir une « impeccable "
        "rigueur logique » ; (d) dépourvu d'illustrations astrologiques ou de diatribe imagée ; "
        "(e) « document capital » et de « valeur documentaire » pour la reconstruction de "
        "l'argumentation carnéadienne. La cible polémique d'Alexandre est exclusivement Chrysippe "
        "(jamais nommé directement mais désigné comme leader du « dogme stoïcien »)."
    ),
    description_en=(
        "Philological synthesis from Amand 1945 (Book I Ch. V §III.1, p. 143-145, ll. 8050-8133). "
        "Identification of witness no. 2 on the list of six witness texts (cf. p. 571-572). Amand "
        "affirms: 'It suffices to read even superficially these five chapters to recognize immediately "
        "in them as precise as extensive a use of the anti-fatalist argumentation of the New "
        "Academy's founder' (p. 144). Philological question posed by Amand: does Alexander reproduce "
        "purely and simply, from a literary source such as Clitomachus, Carneades' arguments while "
        "accommodating them to his cold positive style? Does he limit himself to summarizing them, "
        "fleshing them out occasionally with his own proofs? Is he indebted to a school tradition? "
        "Amand judges it premature to decide but affirms: 'this sheaf of skillful reasoning, abundant "
        "and hitting straight to the target, was originally linked by a powerful and subtle mind that "
        "can only be Carneades' (p. 144). Amand characterizes this witness as: (a) the most "
        "logically rigorous of the six; (b) built according to a wholly philosophical method; "
        "(c) the only one of the six witnesses to offer 'impeccable logical rigor'; (d) devoid of "
        "astrological illustrations or imaged diatribe; (e) 'capital document' of 'documentary value' "
        "for reconstructing the Carneadean argumentation. Alexander's polemical target is exclusively "
        "Chrysippus (never directly named but designated as leader of the 'Stoic dogma')."
    ),
    md=md_base(
        page_range="p. 143-145, 571-572",
        md_line_range="ll. 8050-8133",
        chapter="Livre I Ch. V §III.1 (Introduction au témoin n°2)",
        chapter_actual="Livre I Ch. V §III.1 — Identification philologique du témoin n°2",
        confidence=0.95,
        cited_editions=[
            "Alexandre d'Aphrodise, De Fato 16-20, éd. I. Bruns, Suppl. Arist. II.2, Berlin 1892, p. 186 l. 13 — p. 191 l. 2",
        ],
        extra={
            "amand_thesis_type": "philological_identification",
            "amand_witness_rank": "primary_witness_n2",
            "amand_witness_role": "witness_2_alexander",
            "is_witness_argument": True,
            "amand_qualifier_witness_n2": [
                "most_logically_rigorous_of_six",
                "constructed_philosophically",
                "no_astrological_illustration",
                "no_imaged_diatribe",
                "capital_document",
            ],
            "amand_locus": "ch. 16-20 = Bruns p. 186 l. 13 — p. 191 l. 2",
        },
    ),
))


def make_witness2_arg(*, nid: str, label: str, page_range: str, md_line_range: str,
                      chapter_actual: str, confidence: float, fr_desc: str, en_desc: str,
                      alexander_chapter: int, transmits_b1: list[str],
                      sub_arguments: list[dict[str, str]],
                      witness_role_detail: str = "") -> dict[str, Any]:
    """Helper for Alexander witness-2 arguments."""
    return make_node(
        nid=nid, ntype="argument", label=label,
        period="Hellenistic", school="school_academics", role=None,
        description=fr_desc, description_en=en_desc,
        md=md_base(
            page_range=page_range, md_line_range=md_line_range,
            chapter=f"Livre I Ch. V §III.2 (Alexandre De Fato {alexander_chapter})",
            chapter_actual=chapter_actual,
            confidence=confidence,
            cited_editions=[
                f"Alexandre d'Aphrodise, De Fato {alexander_chapter}, éd. I. Bruns, Suppl. Arist. II.2, Berlin Reimer 1892",
            ],
            extra={
                "amand_witness_rank": "primary_witness_n2",
                "amand_witness_role": "witness_2_alexander",
                "is_witness_argument": True,
                "argument_category": "argument_carneadean_moral_reconstruction_via_witness_alexander",
                "transmits_argument_pivots_b1": transmits_b1,
                "alexander_section_locus": f"Περὶ εἱμαρμένης {alexander_chapter}",
                "sub_arguments": sub_arguments,
                **({"witness_role_detail": witness_role_detail} if witness_role_detail else {}),
            },
        ),
    )


# --- 5 arguments-pivots du témoin n°2 (Alexandre De Fato 16-20) ---

NEW_INSERTS.append(make_witness2_arg(
    nid="argument_alexander_witness2_ch16_theme_virtue_neglect_amand1945",
    label="Témoin n°2 (Alexandre De Fato 16) — Thème général + premier argument : négligence de la vertu",
    page_range="p. 145, 149-150",
    md_line_range="ll. 8133-8205",
    chapter_actual="Livre I Ch. V §III.2.A — Témoin n°2 ch. 16 : thème général + arg 1 (négligence)",
    confidence=0.95,
    fr_desc=(
        "Premier argument moral antifataliste reconstruit chez Alexandre De Fato 16 (Bruns p. 186 "
        "l. 13 — p. 187 l. 5) par Amand 1945 (analyse p. 145, texte grec p. 149-150). Thème général : "
        "la négation du libre arbitre et l'acceptation du fatalisme absolu à la Chrysippe introduisent "
        "la confusion et le bouleversement dans la vie morale de l'humanité (« συγχεῖν τε καὶ "
        "ἀνατρέπειν […] τὸν τῶν ἀνθρώπων βίον », Bruns p. 186 l. 19-21). Premier argument formel : "
        "dans l'hypothèse du fatalisme absolu, tous ceux qui sont imbus de cette croyance "
        "« enverront promener » la vertu, dont la pratique requiert fatigue et labeur (« μετὰ πόνου "
        "τινὸς καὶ φροντίδος »), ou du moins ne s'y porteront qu'avec négligence et mollesse, tandis "
        "qu'ils se livreront avec empressement aux joies faciles que leur procure le vice (« μετὰ "
        "ῥαστώνης τε καὶ ἡδονῆς »). Argument du conséquentialisme pratique : la croyance fataliste "
        "produit en pratique l'abandon des bonnes choses (κτῆσις τε καὶ παρουσία τῶν τοιούτων μετὰ "
        "καμάτου περιγίνεται) au profit du choix des maux faciles."
    ),
    en_desc=(
        "First moral anti-fatalist argument reconstructed in Alexander De Fato 16 (Bruns p. 186 "
        "l. 13 — p. 187 l. 5) by Amand 1945 (analysis p. 145, Greek text p. 149-150). General theme: "
        "denying free will and accepting absolute Chrysippean fatalism introduces confusion and "
        "subversion into human moral life ('συγχεῖν τε καὶ ἀνατρέπειν […] τὸν τῶν ἀνθρώπων βίον', "
        "Bruns p. 186 ll. 19-21). First formal argument: under the absolute fatalism hypothesis, all "
        "those persuaded by this belief will 'send virtue packing', since virtue's practice requires "
        "toil and care ('μετὰ πόνου τινὸς καὶ φροντίδος'), or at least will pursue it only with "
        "neglect and lethargy, while eagerly indulging the easy pleasures vice offers ('μετὰ "
        "ῥαστώνης τε καὶ ἡδονῆς'). Argument from practical consequentialism: the fatalist belief "
        "produces in practice the abandonment of good things (whose acquisition and possession "
        "involve effort) in favor of the choice of easy evils."
    ),
    alexander_chapter=16,
    transmits_b1=["argument_carneadean_action_futility_amand1945",
                  "argument_carneadean_general_theme_amand1945"],
    sub_arguments=[
        {"locus": "Bruns 186,13-21", "topic": "thème général : confusion et bouleversement de la vie morale"},
        {"locus": "Bruns 186,22-187,5", "topic": "arg 1 : négligence de la vertu, choix du vice facile"},
    ],
    witness_role_detail="témoin n°2 §III.2.A — couvre De Fato 16 dans son intégralité (thème + arg 1)",
))

NEW_INSERTS.append(make_witness2_arg(
    nid="argument_alexander_witness2_ch16_praise_blame_punishment_amand1945",
    label="Témoin n°2 (Alexandre De Fato 16, fin) — Deuxième argument : louange/blâme, punition, vice/vertu vidés de sens",
    page_range="p. 145-146, 150-151",
    md_line_range="ll. 8206-8275",
    chapter_actual="Livre I Ch. V §III.2.B — Témoin n°2 ch. 16 (suite) : louange-blâme-punition",
    confidence=0.95,
    fr_desc=(
        "Deuxième argument moral antifataliste reconstruit chez Alexandre De Fato 16 (fin, Bruns "
        "p. 187 l. 5-22) par Amand 1945 (analyse p. 145-146, texte grec p. 150-151). Si les "
        "circonstances imposent absolument leur action, les Stoïciens qui enseignent ce déterminisme "
        "ne peuvent ni blâmer (ψόγος), ni réprimander (ἐπιτιμᾶν), ni encourager (προτροπή), ni "
        "récompenser (τιμή), ni punir (κόλασις) ceux qui s'excusent de leurs fautes en prétextant "
        "cette doctrine. Exemples mythologiques : comment accuser Pâris d'adultère et Agamemnon "
        "d'orgueil si tout est prédéterminé ? « Πῶς γὰρ ἂν ἔτι Ἀλέξανδρος ὁ Πριάμου ἐν αἰτίᾳ εἴη ὡς "
        "διαμαρτὼν περὶ τὴν τῆς Ἑλένης ἁρπαγήν ; » Dans l'hypothèse fataliste : (a) plus de "
        "responsabilité criminelle juste (« εἰ δ' ἦν πάλαι καὶ πρόπαλαι […] ἀληθὲς προλεγόμενον »), "
        "(b) plus de vertus ni de vices (αἱ ἀρεταὶ καὶ αἱ κακίαι vides), (c) plus d'éloges ni de "
        "blâmes justes (ἔπαινοι/ψόγοι sans objet), (d) doctrine objective qui devient en réalité un "
        "plaidoyer pour les méchants (« συνηγορίαν τοῖς κακοῖς »). Personne n'attribue à εἱμαρμένη "
        "ses actions bonnes ; seuls les méchants l'invoquent comme excuse — preuve psychologique "
        "ad hominem du caractère partial de cette doctrine."
    ),
    en_desc=(
        "Second moral anti-fatalist argument reconstructed in Alexander De Fato 16 (end, Bruns p. "
        "187 ll. 5-22) by Amand 1945 (analysis p. 145-146, Greek text p. 150-151). If circumstances "
        "absolutely impose their action, the Stoics teaching this determinism can neither blame "
        "(ψόγος), reprimand (ἐπιτιμᾶν), encourage (προτροπή), reward (τιμή), nor punish (κόλασις) "
        "those who excuse their faults by invoking this doctrine. Mythological examples: how can one "
        "accuse Paris of adultery and Agamemnon of pride if all is predetermined? 'Πῶς γὰρ ἂν ἔτι "
        "Ἀλέξανδρος ὁ Πριάμου ἐν αἰτίᾳ εἴη ὡς διαμαρτὼν περὶ τὴν τῆς Ἑλένης ἁρπαγήν;' Under the "
        "fatalist hypothesis: (a) no more just criminal responsibility ('εἰ δ' ἦν πάλαι καὶ "
        "πρόπαλαι […] ἀληθὲς προλεγόμενον'), (b) no more virtues or vices (αἱ ἀρεταὶ καὶ αἱ κακίαι "
        "voided), (c) no more just praise or blame (ἔπαινοι/ψόγοι without object), (d) objectively "
        "the doctrine becomes a plea for the wicked ('συνηγορίαν τοῖς κακοῖς'). No one attributes "
        "their good actions to εἱμαρμένη; only the wicked invoke it as excuse — psychological "
        "ad hominem proof of this doctrine's partiality."
    ),
    alexander_chapter=16,
    transmits_b1=["argument_carneadean_virtue_vice_amand1945",
                  "argument_carneadean_legislation_amand1945",
                  "argument_carneadean_incentives_amand1945"],
    sub_arguments=[
        {"locus": "Bruns 187,5-12", "topic": "Stoïciens ne peuvent juger sans liberté"},
        {"locus": "Bruns 187,12-22", "topic": "exemples mythiques Pâris/Agamemnon ; doctrine = plaidoyer des méchants"},
    ],
    witness_role_detail="témoin n°2 §III.2.B — couvre la fin de De Fato 16 (Bruns 187,5-22)",
))

NEW_INSERTS.append(make_witness2_arg(
    nid="argument_alexander_witness2_ch18_stoic_practical_self_refutation_amand1945",
    label="Témoin n°2 (Alexandre De Fato 18) — Quatrième argument : auto-réfutation pragmatique des Stoïciens",
    page_range="p. 146-147, 152",
    md_line_range="ll. 8276-8360",
    chapter_actual="Livre I Ch. V §III.2.D — Témoin n°2 ch. 18 : auto-réfutation pragmatique",
    confidence=0.95,
    fr_desc=(
        "Quatrième argument moral antifataliste reconstruit chez Alexandre De Fato 18 (Bruns p. 188 "
        "l. 22 — p. 189 l. 25) par Amand 1945 (analyse p. 146-147, texte grec p. 152). L'attitude "
        "pratique des Stoïciens révèle clairement le mensonge de leur théorie fataliste : tous leurs "
        "discours supposent le franc arbitre. (a) Ils s'évertuent à exhorter leurs auditeurs (« ὅτι "
        "δὲ καὶ ψεῦδος »), comme s'ils avaient la faculté de les encourager ou non. (b) Ils "
        "s'efforcent de les persuader d'adopter tels ou tels dogmes, comme si leurs disciples avaient "
        "le pouvoir de les admettre. (c) Ils réprimandent leurs auditeurs et leur reprochent de ne "
        "pas accomplir leur devoir. (d) Ils écrivent de nombreux traités pour l'instruction de la "
        "jeunesse, pleinement conscients de leur faculté de les rédiger ou non — non pas sous une "
        "pression nécessitante mais, disent-ils, « par amour de l'humanité » (φιλανθρωπίας ἕνεκα). "
        "Argument ad hominem central : la praxis stoïcienne contredit logiquement leur dogme "
        "(εἱμαρμένη universelle) ; ils ne peuvent pas eux-mêmes croire à leurs propres thèses sous "
        "peine d'absurdité performative."
    ),
    en_desc=(
        "Fourth moral anti-fatalist argument reconstructed in Alexander De Fato 18 (Bruns p. 188 "
        "l. 22 — p. 189 l. 25) by Amand 1945 (analysis p. 146-147, Greek text p. 152). The Stoics' "
        "practical attitude clearly reveals the falsehood of their fatalist theory: all their "
        "discourse presupposes free choice. (a) They strive to exhort their listeners ('ὅτι δὲ καὶ "
        "ψεῦδος'), as if they had the power to encourage them or not. (b) They strive to persuade "
        "them to adopt this or that dogma, as if their disciples had the power to admit it. "
        "(c) They reprimand their listeners and reproach them for not doing their duty. (d) They "
        "write many treatises for the instruction of youth, fully aware of their faculty to write "
        "them or not — not under necessitating pressure but, they say, 'out of love of humanity' "
        "(φιλανθρωπίας ἕνεκα). Central ad hominem argument: Stoic praxis logically contradicts their "
        "dogma (universal εἱμαρμένη); they cannot themselves believe their own theses without "
        "performative absurdity."
    ),
    alexander_chapter=18,
    transmits_b1=["argument_carneadean_stoic_pragmatic_self_refutation_amand1945",
                  "argument_carneadean_action_futility_amand1945"],
    sub_arguments=[
        {"locus": "Bruns 188,22-189,5", "topic": "exhortation/persuasion stoïcienne suppose franc arbitre"},
        {"locus": "Bruns 189,5-15", "topic": "réprimandes et reproches au sujet du devoir"},
        {"locus": "Bruns 189,15-25", "topic": "écriture de traités par 'amour de l'humanité' (φιλανθρωπία)"},
    ],
    witness_role_detail="témoin n°2 §III.2.D — couvre De Fato 18 dans son intégralité (Bruns 188,22-189,25)",
))

NEW_INSERTS.append(make_witness2_arg(
    nid="argument_alexander_witness2_ch19_de_facto_punishment_amand1945",
    label="Témoin n°2 (Alexandre De Fato 19) — Cinquième argument : châtiment effectif des criminels par les Stoïciens",
    page_range="p. 147-148, 152-154",
    md_line_range="ll. 8361-8480",
    chapter_actual="Livre I Ch. V §III.2.E — Témoin n°2 ch. 19 : châtiment de fait des criminels",
    confidence=0.95,
    fr_desc=(
        "Cinquième argument moral antifataliste reconstruit chez Alexandre De Fato 19 (Bruns p. 189 "
        "l. 25 — p. 190 l. 30) par Amand 1945 (analyse p. 147-148, texte grec p. 152-154). Les "
        "Stoïciens reconnaissent en pratique la liberté humaine (« ἐλεύθερον »), la faculté de "
        "choisir entre opinions et actions différentes. Tout le monde admet que celui qui a agi "
        "involontairement (ἀκούσιον) est digne de pardon parce qu'innocent. Si Chrysippe et ses "
        "disciples étaient conséquents avec eux-mêmes, ils devraient absoudre non seulement les "
        "ignorants ou contraints extérieurement, mais aussi tous ceux qui savent ce qu'ils font mais "
        "qui ne peuvent agir autrement, du fait de l'ensemble nécessitant des circonstances et "
        "parce que chacune de leurs actions est déterminée par εἱμαρμένη — « ὥσπερ τὰ τῶν βαρέων "
        "σωμάτων κάτω φέρεσθαι » (comme la nature des corps graves est de tomber). Or, en pratique, "
        "tous les hommes (Stoïciens compris) estiment dignes de châtiment ceux qui se détournent du "
        "but de l'existence et se livrent à des actions criminelles, tandis qu'ils pardonnent à ceux "
        "qui ont commis une faute contre leur gré. Conséquence : les méchants pourraient invoquer "
        "le fatalisme pour leur justification (« Nous aussi, nous sommes dignes de grâce, tout comme "
        "ceux qui commettent involontairement une faute, car nous sommes poussés par notre propre "
        "nature »), mais personne, pas même un Stoïcien, ne croira à la vérité de cette excuse. "
        "Donc en pratique, les Stoïciens reconnaissent la liberté."
    ),
    en_desc=(
        "Fifth moral anti-fatalist argument reconstructed in Alexander De Fato 19 (Bruns p. 189 "
        "l. 25 — p. 190 l. 30) by Amand 1945 (analysis p. 147-148, Greek text p. 152-154). The "
        "Stoics in practice recognize human freedom ('ἐλεύθερον'), the faculty to choose between "
        "different opinions and actions. Everyone admits that one who acts involuntarily (ἀκούσιον) "
        "deserves pardon as innocent. If Chrysippus and his disciples were consistent with "
        "themselves, they should absolve not only the ignorant or externally constrained, but also "
        "all those who know what they do but cannot act otherwise, given the necessitating set of "
        "circumstances and the fact that each action is determined by εἱμαρμένη — 'ὥσπερ τὰ τῶν "
        "βαρέων σωμάτων κάτω φέρεσθαι' (as heavy bodies' nature is to fall). Yet in practice, all "
        "people (Stoics included) deem worthy of punishment those who turn from life's end and "
        "engage in crime, while pardoning those who erred against their will. Consequence: the "
        "wicked might invoke fatalism to justify themselves ('We too deserve grace, just like those "
        "who err involuntarily, since we are driven by our own nature'), but no one, not even a "
        "Stoic, will believe this excuse. Therefore in practice, the Stoics recognize freedom."
    ),
    alexander_chapter=19,
    transmits_b1=["argument_carneadean_stoic_pragmatic_punishment_amand1945",
                  "argument_carneadean_virtue_vice_amand1945",
                  "argument_carneadean_legislation_amand1945"],
    sub_arguments=[
        {"locus": "Bruns 189,25-190,10", "topic": "le pardon de l'acte involontaire suppose le libre arbitre"},
        {"locus": "Bruns 190,10-20", "topic": "si déterminisme, tous les criminels devraient être absous"},
        {"locus": "Bruns 190,20-30", "topic": "la pratique judiciaire universelle révèle la croyance en la liberté"},
    ],
    witness_role_detail="témoin n°2 §III.2.E — couvre De Fato 19 dans son intégralité (Bruns 189,25-190,30)",
))

NEW_INSERTS.append(make_witness2_arg(
    nid="argument_alexander_witness2_ch20_conclusion_amand1945",
    label="Témoin n°2 (Alexandre De Fato 20) — Conclusion : la vie humaine devient impossible sans libre arbitre",
    page_range="p. 148, 154",
    md_line_range="ll. 8481-8560",
    chapter_actual="Livre I Ch. V §III.2.F — Témoin n°2 ch. 20 : conclusion (vie impossible sans liberté)",
    confidence=0.95,
    fr_desc=(
        "Conclusion du témoin n°2 reconstruit chez Alexandre De Fato 20 (Bruns p. 190 l. 30 — p. 191 "
        "l. 2) par Amand 1945 (analyse p. 148, texte grec p. 154). « ἀλλ' ὅτι μὲν καὶ ἔστι τι ἐφ' "
        "ἡμῖν ὀνομάσαι » — il y a bien quelque chose à nommer 'ce qui dépend de nous'. Et cependant, "
        "malgré le libre arbitre, rien ne se fait sans cause (« οὐ διὰ τὴν ἐξουσίαν ταύτην ἀναιτίως "
        "τι γίνεται ») : c'est l'homme lui-même qui est le principe responsable des actions émanant "
        "de lui (« ἀρχὴν αὐτὸν ὄντα τῶν γινομένων ὑφ' αὐτοῦ »). Ceux qui demeurent imbus de la "
        "croyance au fatalisme absolu ne devraient logiquement : (a) ni réprimander ni louer autrui ; "
        "(b) ni conseiller (συμβουλεύειν) ; (c) ni exhorter (προτρέπειν) ; (d) ni prier les dieux "
        "(εὐξάσθαι θεοῖς) ; (e) ni les remercier (χάριν αὐτοῖς γνῶναι) ; (f) ni accomplir aucune "
        "des actions raisonnables que font ceux qui croient à la liberté de leur volonté. "
        "Affirmation finale : ôtez la conviction du libre arbitre et « ἔξω τούτων ἀβίωτος ὁ τῶν "
        "ἀνθρώπων (βίος) καὶ οὐδὲ τὴν ἀρχὴν ἀνθρώπων ἔτι » — la vie humaine devient invivable, et "
        "n'est plus même celle d'hommes. Argument-récapitulatif structurant tout le témoin n°2."
    ),
    en_desc=(
        "Conclusion of witness no. 2 reconstructed in Alexander De Fato 20 (Bruns p. 190 l. 30 — "
        "p. 191 l. 2) by Amand 1945 (analysis p. 148, Greek text p. 154). 'ἀλλ' ὅτι μὲν καὶ ἔστι τι "
        "ἐφ' ἡμῖν ὀνομάσαι' — there is indeed something to name 'what depends on us'. And yet, "
        "despite free will, nothing happens without cause ('οὐ διὰ τὴν ἐξουσίαν ταύτην ἀναιτίως τι "
        "γίνεται'): it is man himself who is the responsible principle of actions emanating from him "
        "('ἀρχὴν αὐτὸν ὄντα τῶν γινομένων ὑφ' αὐτοῦ'). Those who remain steeped in belief in "
        "absolute fatalism should logically: (a) neither reprimand nor praise others; (b) nor "
        "advise (συμβουλεύειν); (c) nor exhort (προτρέπειν); (d) nor pray to the gods (εὐξάσθαι "
        "θεοῖς); (e) nor thank them (χάριν αὐτοῖς γνῶναι); (f) nor do any of the reasonable actions "
        "done by those who believe in the freedom of their will. Final assertion: remove the "
        "conviction of free will and 'ἔξω τούτων ἀβίωτος ὁ τῶν ἀνθρώπων (βίος) καὶ οὐδὲ τὴν ἀρχὴν "
        "ἀνθρώπων ἔτι' — human life becomes unlivable, and is no longer even that of humans. "
        "Structuring summary argument of the entire witness no. 2."
    ),
    alexander_chapter=20,
    transmits_b1=["argument_carneadean_action_futility_amand1945",
                  "argument_carneadean_piety_amand1945",
                  "argument_carneadean_general_theme_amand1945"],
    sub_arguments=[
        {"locus": "Bruns 190,30-191,1", "topic": "affirmation du τὸ ἐφ' ἡμῖν avec causalité humaine non aitiologique"},
        {"locus": "Bruns 191,1-2", "topic": "incompatibilité avec prière, exhortation, conseil, louange"},
        {"locus": "Bruns 191,2", "topic": "vie sans libre arbitre = ἀβίωτος"},
    ],
    witness_role_detail="témoin n°2 §III.2.F — couvre De Fato 20 dans son intégralité",
))


# --- Envelope Alexandre (containement) ---
NEW_INSERTS.append(make_node(
    nid="argument_alexander_witness2_envelope_amand1945",
    ntype="argument",
    label="Argument-cadre du témoin n°2 Alexandre De Fato 16-20 — enveloppe quinquépartite de la diatribe antifataliste",
    period="Hellenistic", school="school_academics", role=None,
    description=(
        "Enveloppe argumentative générale identifiée par Amand 1945 (p. 148, ll. 8481-8530) à "
        "l'intérieur du De Fato 16-20 d'Alexandre. Selon Amand, Alexandre « accumule les arguments "
        "d'ordre moral contre le déterminisme absolu de Chrysippe, qui de fait supprime la "
        "responsabilité, l'effort moral et la règle des mœurs, renverse toute société humaine, et "
        "détruit enfin la religion, la piété et toutes les cérémonies du culte des dieux » (p. 144). "
        "Le schéma de cette argumentation se ramène à cinq points (Amand p. 148, schéma "
        "récapitulatif) : (1) si l'on croit au fatalisme absolu, on négligera la vertu (ch. 16, "
        "début) ; (2) reproches, punitions, encouragements, récompenses n'ont plus de raison d'être "
        "(ch. 16, fin) ; (3) il faut nier la Providence, rejeter la piété, condamner la divination "
        "(ch. 17) ; (4) l'attitude pratique des Stoïciens contredit leur théorie (ch. 18) ; (5) les "
        "Stoïciens reconnaissent en réalité notre liberté par leur jugement des criminels (ch. 19), "
        "et l'incompatibilité finale avec la vie humaine vivable (ch. 20). Squelette logique "
        "rigoureux, sans diatribe imagée — la marque distinctive du témoin n°2."
    ),
    description_en=(
        "General argumentative envelope identified by Amand 1945 (p. 148, ll. 8481-8530) inside "
        "Alexander's De Fato 16-20. According to Amand, Alexander 'accumulates moral arguments "
        "against Chrysippus' absolute determinism, which in fact suppresses responsibility, moral "
        "effort and the rule of customs, overturns all human society, and finally destroys "
        "religion, piety and all ceremonies of divine worship' (p. 144). The schema of this "
        "argumentation reduces to five points (Amand p. 148, recapitulative schema): (1) if one "
        "believes in absolute fatalism, one will neglect virtue (ch. 16 opening); (2) reproaches, "
        "punishments, encouragements, rewards lose their raison d'être (ch. 16 end); (3) one must "
        "deny Providence, reject piety, condemn divination (ch. 17); (4) the Stoics' practical "
        "attitude contradicts their theory (ch. 18); (5) the Stoics actually recognize our freedom "
        "by their judgment of criminals (ch. 19), with final incompatibility with livable human "
        "life (ch. 20). Rigorous logical skeleton, without imaged diatribe — the distinctive mark "
        "of witness no. 2."
    ),
    md=md_base(
        page_range="p. 144-148", md_line_range="ll. 8050-8530",
        chapter="Livre I Ch. V §III.2 (Alexandre, schéma récapitulatif)",
        chapter_actual="Livre I Ch. V §III.2 — Enveloppe quinquépartite du témoin n°2",
        confidence=0.95,
        cited_editions=[
            "Alexandre d'Aphrodise, De Fato 16-20, éd. I. Bruns, Suppl. Arist. II.2, Berlin 1892, p. 186 l. 13 — p. 191 l. 2",
        ],
        extra={
            "envelope_for_sub_arguments": [
                "argument_alexander_witness2_ch16_theme_virtue_neglect_amand1945",
                "argument_alexander_witness2_ch16_praise_blame_punishment_amand1945",
                "argument_carneadean_providence_mantike_alexander_amand1945",
                "argument_alexander_witness2_ch18_stoic_practical_self_refutation_amand1945",
                "argument_alexander_witness2_ch19_de_facto_punishment_amand1945",
                "argument_alexander_witness2_ch20_conclusion_amand1945",
            ],
            "argument_category": "argument_carneadean_moral_reconstruction_envelope_witness_n2",
            "amand_witness_rank": "primary_witness_n2_structure",
            "amand_witness_role": "witness_2_alexander",
            "is_witness_argument": True,
        },
    ),
))


# --- Syntheses §III.4 Observations finales ---

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_no_astrological_targeting",
    ntype="synthesis",
    label="Amand 1945 — Absence d'allusions astrologiques chez Alexandre (cible polémique = εἱμαρμένη métaphysique chrysippéenne)",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. V §III.4, p. 154-155, ll. 8990-9070). Observation "
        "finale d'Amand sur le témoin n°2 : « nous sommes frappés par l'absence totale d'allusions "
        "directes à l'astrologie » dans les chapitres 16-20 comme dans tout le Περὶ εἱμαρμένης. "
        "Alexandre ne souffle mot de l'art oriental de la généthlialogie et de l'apotélesmatique en "
        "général. Il ne réfute point l'εἱμαρμένη astrologique ou populaire, mais seulement "
        "l'εἱμαρμένη métaphysique systématisée par Chrysippe. La discussion est conduite dans "
        "l'esprit « un peu sec mais précis du rationalisme aristotélicien ». Amand renonce à "
        "chercher le motif de cette « réserve assez surprenante » à l'égard d'une pseudo-science "
        "qui recrutait pourtant un nombre croissant d'adeptes au IIe siècle. Cible polémique "
        "explicite : le déterminisme intégral et universel de Chrysippe, son fatalisme rigide et "
        "sans exception. Alexandre représente « excellemment l'école d'Aristote au siècle des "
        "Antonins » sur ces points."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. V §III.4, p. 154-155, ll. 8990-9070). Amand's final "
        "observation on witness no. 2: 'we are struck by the total absence of direct allusions to "
        "astrology' in chapters 16-20 as in the entire Περὶ εἱμαρμένης. Alexander breathes not a "
        "word of the oriental art of genethlialogy and apotelesmatic in general. He does not refute "
        "astrological or popular εἱμαρμένη, but only the metaphysical εἱμαρμένη systematized by "
        "Chrysippus. The discussion is conducted in the 'somewhat dry but precise spirit of "
        "Aristotelian rationalism'. Amand refrains from seeking the motive of this 'rather "
        "surprising reserve' towards a pseudo-science that nevertheless recruited growing adherents "
        "in the 2nd century. Explicit polemical target: Chrysippus' integral and universal "
        "determinism, his rigid exceptionless fatalism. On these points Alexander represents "
        "'excellently the Aristotelian school in the Antonine age'."
    ),
    md=md_base(
        page_range="p. 154-155", md_line_range="ll. 8990-9070",
        chapter="Livre I Ch. V §III.4 (Observations finales)",
        chapter_actual="Livre I Ch. V §III.4 — Absence d'astrologie, cible = Chrysippe métaphysique",
        confidence=0.95,
        cited_editions=[],
        extra={
            "amand_thesis_type": "philological_observation_negative_finding",
            "amand_witness_property": "no_astrological_illustration_n2_distinctive",
            "alexander_target": "chrysippus_metaphysical_heimarmene_only",
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_scholastic_vs_philo_firmicus_diatribe",
    ntype="synthesis",
    label="Amand 1945 — Contraste stylistique : Alexandre scolastique vs Philon/Firmicus en diatribe imagée",
    period=None, school=None, role=None,
    description=(
        "Synthèse comparative d'Amand 1945 (Livre I Ch. V §III.4, p. 155-156, ll. 9070-9200 + "
        "réf. transversales p. 187-188). Selon Amand, alors que « le scholarque péripatéticien "
        "d'Athènes expose [l'argumentation] sous une forme strictement scientifique, avec une "
        "rigueur et une sécheresse bien aristotélicienne », Philon (témoin n°1) et Firmicus "
        "Maternus (témoin n°3) la présentent « sous un aspect populaire et imagé ». Tous deux "
        "évitent les termes d'école, emploient « le procédé vivant et piquant de la diatribe » "
        "(apostrophes, exclamations, mise en scène, anecdotes), et recourent à l'illustration "
        "astrologique pour appuyer et éclairer leurs affirmations. Amand reconstruit Carnéade "
        "lui-même comme orateur capable d'accommoder ses discours à l'intelligence d'un auditoire "
        "populaire : le rusé dialecticien parait ses arguments schématiques et abstraits d'une "
        "« affabulation oratoire » dont Philon et Firmicus offrent de curieux spécimens, tandis "
        "qu'Alexandre conserve la forme nue de l'argument technique réservé aux disciples et aux "
        "auditeurs d'élite — « le ton de cette discussion technique et purement philosophique, "
        "réservée surtout aux disciples et à des auditeurs d'élite » (p. 155). Le contraste "
        "Alexandre/Philon-Firmicus reflète ainsi une polarité genre-rhétorique au sein de la "
        "transmission carnéadienne, non un désaccord doctrinal."
    ),
    description_en=(
        "Comparative synthesis from Amand 1945 (Book I Ch. V §III.4, p. 155-156, ll. 9070-9200 + "
        "cross-references p. 187-188). According to Amand, while 'the Peripatetic scholarch of "
        "Athens expounds [the argumentation] in a strictly scientific form, with Aristotelian "
        "rigor and dryness', Philo (witness no. 1) and Firmicus Maternus (witness no. 3) present it "
        "'in a popular and imaged aspect'. Both avoid school terms, employ 'the lively and "
        "stinging procedure of diatribe' (apostrophes, exclamations, mise en scène, anecdotes), and "
        "resort to astrological illustration to support and illuminate their statements. Amand "
        "reconstructs Carneades himself as an orator capable of adapting his discourse to a "
        "popular audience's intelligence: the cunning dialectician adorns his schematic and "
        "abstract arguments with 'oratorical fabulation' of which Philo and Firmicus offer curious "
        "specimens, while Alexander preserves the bare form of the technical argument reserved for "
        "disciples and elite auditors — 'the tone of this technical and purely philosophical "
        "discussion, reserved above all for disciples and elite hearers' (p. 155). The "
        "Alexander/Philo-Firmicus contrast thus reflects a genre-rhetorical polarity within "
        "Carneadean transmission, not a doctrinal disagreement."
    ),
    md=md_base(
        page_range="p. 155-156", md_line_range="ll. 9070-9200",
        chapter="Livre I Ch. V §III.4 (Observations finales) + références transversales p. 187-188",
        chapter_actual="Livre I Ch. V §III.4 — Contraste stylistique avec témoins n°1 et n°3",
        confidence=0.85,
        cited_editions=[],
        extra={
            "amand_thesis_type": "stylistic_comparative_observation",
            "amand_genre_polarity": [
                "Alexander = technical philosophical exposition for disciples/elite",
                "Philo + Firmicus = popular imaged diatribe for general audience",
                "Carneades original = orator able to operate in both registers",
            ],
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_alexander_witness_n2_insufficient_alone",
    ntype="synthesis",
    label="Amand 1945 — Insuffisance du témoin n°2 seul pour reconstituer Carnéade",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. V §III.4, p. 156, ll. 9200-9249, conclusion du "
        "chapitre). Aveu méthodologique d'Amand : « Elle est précieuse assurément cette discussion "
        "ad hominem et ad absurdum ! Elle constitue un excellent témoin de l'ensemble des arguments "
        "moraux antifatalistes de Carnéade. Elle ne suffit cependant point à reconstituer ce "
        "complexus, si on la considère séparément. Seule l'étude comparative des autres « textes "
        "témoins » pourra déterminer dans quelle mesure ces chapitres du commentateur d'Aristote "
        "peuvent contribuer à un essai de reconstruction de cette argumentation du chef de la "
        "Nouvelle Académie. Provisoirement la question reste donc pendante. » Implications : "
        "(a) un seul témoin ne suffit pas, même le plus rigoureux ; (b) la règle des « 3 témoins "
        "sur 6 » qu'Amand formulera dans la conclusion (p. 571-572) gouverne déjà la méthode "
        "ici ; (c) le témoin n°2 reste néanmoins la pierre angulaire logique de la reconstruction. "
        "Amand transitionne vers la « revue des philosophes grecs » suivante qui ne donnera, "
        "selon ses propres termes, « guère que des déceptions » (Néo-Platoniciens du Ch. VI)."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. V §III.4, p. 156, ll. 9200-9249, chapter conclusion). "
        "Amand's methodological admission: 'This ad hominem and ad absurdum discussion is "
        "certainly precious! It constitutes an excellent witness of the totality of Carneades' "
        "moral anti-fatalist arguments. However, it does not suffice to reconstruct this complex "
        "if considered separately. Only the comparative study of the other 'witness texts' can "
        "determine to what extent these chapters of Aristotle's commentator can contribute to an "
        "attempted reconstruction of this argumentation of the New Academy's head. The question "
        "thus remains provisionally pending.' Implications: (a) a single witness does not suffice, "
        "even the most rigorous; (b) the '3 witnesses out of 6' rule Amand will formulate in the "
        "conclusion (p. 571-572) already governs the method here; (c) witness no. 2 nonetheless "
        "remains the logical cornerstone of the reconstruction. Amand transitions to the next "
        "'review of Greek philosophers' which will yield, in his own words, 'hardly anything but "
        "disappointments' (Neo-Platonists of Ch. VI)."
    ),
    md=md_base(
        page_range="p. 156, 571-572",
        md_line_range="ll. 9200-9249",
        chapter="Livre I Ch. V §III.4 (Observations finales — conclusion)",
        chapter_actual="Livre I Ch. V §III.4 — Insuffisance du témoin seul + transition",
        confidence=0.95,
        cited_editions=[],
        extra={
            "amand_thesis_type": "methodological_admission",
            "amand_verbatim_quote_fr": "Elle ne suffit cependant point à reconstituer ce complexus, si on la considère séparément",
            "anticipates_rule_3_of_6": True,
        },
    ),
))


# --- Concept : two-way powers / contingency / Aristotelian deliberation Alexander ---
NEW_INSERTS.append(make_node(
    nid="concept_to_endechomenon_alexander_amand1945",
    ntype="concept",
    label="τὸ ἐνδεχόμενον / τὸ ὁπότερα — concept de contingence chez Alexandre selon Amand 1945",
    period="Roman Imperial", school="school_peripatetics", role=None,
    description=(
        "Concept aristotélico-péripatéticien dont Amand 1945 (Livre I Ch. V §II.3.2, p. 141-142) "
        "souligne l'importance dans la défense alexandrienne du libre arbitre contre Chrysippe. "
        "Définition d'Alexandre (De Fato 9, Bruns p. 176 l. 1-2) : τὸ ἐνδεχομένως γεγονὸς ἐν τινι "
        "καὶ μὴ γεγονέναι ἐν αὐτῷ οἷόν τε ἦν — « ce qui s'est produit dans une chose mais qui "
        "pouvait également ne pas s'y produire ». Synonyme employé par Alexandre : τὸ ὁπότερα "
        "(« le l'un ou l'autre »). Le concept articule (1) la possibilité réelle dans la nature "
        "(non purement logique), (2) la délibération humaine qui présuppose des futurs ouverts, "
        "(3) l'incompatibilité radicale avec l'εἱμαρμένη universelle chrysippéenne. C'est sur ce "
        "terrain métaphysique que se joue, selon Amand, le différend péripatétisme/stoïcisme avant "
        "même l'argumentation morale carnéadienne. Voir aussi concept_endechomenon_contingent_aristotle "
        "(version aristotélicienne) pour la généalogie du concept."
    ),
    description_en=(
        "Aristotelian-Peripatetic concept whose importance in Alexander's defence of free will "
        "against Chrysippus is highlighted by Amand 1945 (Book I Ch. V §II.3.2, p. 141-142). "
        "Alexander's definition (De Fato 9, Bruns p. 176 ll. 1-2): τὸ ἐνδεχομένως γεγονὸς ἐν τινι "
        "καὶ μὴ γεγονέναι ἐν αὐτῷ οἷόν τε ἦν — 'that which has come about in a thing but could "
        "equally not have come about in it'. Synonym used by Alexander: τὸ ὁπότερα ('either-or'). "
        "The concept articulates (1) real possibility in nature (not purely logical), (2) human "
        "deliberation presupposing open futures, (3) radical incompatibility with Chrysippean "
        "universal εἱμαρμένη. On this metaphysical terrain, according to Amand, the "
        "Peripatos/Stoa quarrel plays out before the moral Carneadean argumentation. See also "
        "concept_endechomenon_contingent_aristotle (Aristotelian version) for the concept's "
        "genealogy."
    ),
    md=md_base(
        page_range="p. 141-142",
        md_line_range="ll. 7927-7990",
        chapter="Livre I Ch. V §II.3.2 (La contingence dans la philosophie d'Alexandre)",
        chapter_actual="Livre I Ch. V §II.3.2 — concept d'endechomenon chez Alexandre",
        confidence=0.95,
        cited_editions=[
            "Alexandre d'Aphrodise, De Fato 9, éd. Bruns p. 176 l. 1-2",
        ],
        extra={
            "concept_key_terms_greek": ["τὸ ἐνδεχόμενον", "τὸ ὁπότερα", "τὸ ἐνδεχομένως γεγονός"],
            "concept_genealogy": "Aristote (EN III.3 + De interpr. 9) → Alexandre De Fato 9-15",
            "polemical_target": "εἱμαρμένη universelle chrysippéenne",
        },
    ),
))


# ============================================================================
# FIRMICUS MATERNUS — Ch. VII (p. 177-188, ll. 10135-10791)
# ============================================================================

# --- Work-shells (Mathesis + De errore) ---

NEW_INSERTS.append(make_node(
    nid="work_firmicus_mathesis",
    ntype="work",
    label="Iulius Firmicus Maternus, Mathesis (8 livres)",
    period="Late Antiquity", school=None, role=None,
    description=(
        "Somme astrologique latine en 8 livres composée par Iulius Firmicus Maternus, sénateur "
        "romain, sous le règne de Constantin (vers 334-337). Selon Amand 1945 (Livre I Ch. VII, "
        "p. 178-188), c'est « cet imposant traité d'astrologie » qui mène les initiés des principes "
        "rudimentaires jusqu'aux mystères de la Sphaera barbarica. Le livre I constitue une apologie "
        "introductive de l'astrologie : il rapporte in extenso, pour les réfuter, trois séries "
        "d'arguments antiastrologiques d'origine néo-académicienne (Carnéade), dont (en I, 2, 5-11) "
        "l'argumentation morale antifataliste qui fait de Firmicus le « témoin n°3 » d'Amand pour "
        "la reconstruction de Carnéade. Édition critique de référence (citée par Amand) : Iulii "
        "Firmici Materni Matheseos libri VIII, ed. W. Kroll et F. Skutsch in operis societatem "
        "assumpto K. Ziegler, Leipzig Teubner, t. I (libri I-IV) 1897, t. II (libri V-VIII cum "
        "praefatione et indicibus) 1913. Étude de référence : Fr. Boll, art. Firmicus, in "
        "Pauly-Wissowa RE VI, 1909, col. 2365-2379. Selon Boll-Amand, source principale (médiate ?) "
        "= le manuel apotélesmatique alexandrin mis sous les noms de Néchepso et Pétosiris. Style "
        "médiocre, compilation pédante. STATUT : work-shell créé en B4 ; aucun passage Mathesis "
        "n'est actuellement ingéré dans le corpus EleutherIA — ingestion à venir."
    ),
    description_en=(
        "Latin astrological summa in 8 books composed by Iulius Firmicus Maternus, Roman senator, "
        "under Constantine's reign (c. 334-337 CE). According to Amand 1945 (Book I Ch. VII, "
        "p. 178-188), it is 'this imposing astrological treatise' that leads initiates from "
        "rudimentary principles to the mysteries of the Sphaera barbarica. Book I constitutes an "
        "introductory apology for astrology: it reports in extenso, in order to refute them, three "
        "series of anti-astrological arguments of Neo-Academic origin (Carneades), including (at "
        "I, 2, 5-11) the moral anti-fatalist argumentation that makes Firmicus Amand's 'witness "
        "no. 3' for reconstructing Carneades. Critical edition of reference (cited by Amand): "
        "Iulii Firmici Materni Matheseos libri VIII, ed. W. Kroll and F. Skutsch in operis "
        "societatem assumpto K. Ziegler, Leipzig Teubner, vol. I (books I-IV) 1897, vol. II "
        "(books V-VIII cum praefatione et indicibus) 1913. Reference study: Fr. Boll, art. "
        "Firmicus, in Pauly-Wissowa RE VI, 1909, col. 2365-2379. According to Boll-Amand, main "
        "(mediate?) source = the Alexandrian apotelesmatic manual attributed to Nechepso and "
        "Petosiris. Mediocre style, pedantic compilation. STATUS: work-shell created in B4; no "
        "Mathesis passage is currently ingested in the EleutherIA corpus — ingestion forthcoming."
    ),
    md=md_base(
        page_range="p. 178-188",
        md_line_range="ll. 10188-10791",
        chapter="Livre I Ch. VII (Iulius Firmicus Maternus)",
        chapter_actual="Livre I Ch. VII §II — La Mathesis comme témoin n°3",
        confidence=0.95, contains_greek=True, contains_latin=True,
        cited_editions=[
            "Iulii Firmici Materni Matheseos libri VIII, ed. W. Kroll et F. Skutsch in operis societatem assumpto K. Ziegler, Leipzig Teubner, t. I (libri I-IV) 1897 ; t. II (libri V-VIII) 1913",
            "Fr. Boll, art. Firmicus, Pauly-Wissowa RE VI, 1909, col. 2365-2379",
            "M. Schanz, Geschichte der römischen Litteratur, IV/1², 1914, p. 129-137",
            "O. Bardenhewer, Geschichte der altkirchlichen Literatur, III³, 1923, p. 456-460 et p. 676",
        ],
        evidence_pending=True,
        evidence_pending_reason="Firmicus Mathesis absent du corpus EleutherIA (ingestion path : archive.org Kroll-Skutsch 1897 djvu, cf. docs/reports/2026-05-15-five-witnesses-ingestion-paths.md)",
        extra={
            "preservation_status": "complete_critical_edition_kroll_skutsch_1897_1913",
            "title_latin": "Matheseos libri VIII",
            "books_count": 8,
            "amand_witness_role": "primary_witness_n3",
            "amand_witness_passage_locus": "I, 2, 5-11 (Kroll-Skutsch I p. 7 l. 8 — p. 9 l. 4)",
            "amand_main_source_hypothesis": "manuel apotélesmatique alexandrin Néchepso-Pétosiris (médiate ?)",
            "compositional_date": "c. 334-337 CE sous Constantin",
            "dedicatee": "Lollianus Mauortius, proconsul d'Afrique",
            "structure_book_i": [
                "ch. 1 : controverses entre philosophes (nature des dieux, immortalité de l'âme, bien/mal)",
                "ch. 2-3 : trois arguments antiastrologiques carnéadiens rapportés in extenso",
                "ch. 3-4 : considérations posidoniennes apologétiques",
                "ch. 5 : réfutation de l'argument ethnographique (sans géographie astrologique, via Chrysippe)",
                "ch. 6 : réfutation de l'argument moral (lois pénales aident les faibles)",
                "ch. 7 : exemples mythologico-historiques de la Fortuna",
                "ch. 8 : contre l'opinion intermédiaire (naissance/mort fatalistes, vie libre)",
                "ch. 9 : récapitulation du fatalisme universel",
                "ch. 10 : retour sur l'argument ethnographique via théorie des cinq zones",
            ],
        },
    ),
    alternative_names=["Mathesis", "Matheseos libri VIII"],
))

NEW_INSERTS.append(make_node(
    nid="work_firmicus_de_errore_profanarum_religionum",
    ntype="work",
    label="Iulius Firmicus Maternus, De errore profanarum religionum",
    period="Late Antiquity", school=None, role=None,
    description=(
        "Pamphlet apologétique chrétien composé par Iulius Firmicus Maternus après sa conversion "
        "au christianisme, vers 343-350 CE — environ dix ans après sa Mathesis astrologique. Selon "
        "Amand 1945 (Livre I Ch. VII §I, p. 178), ce « furieux pamphlet » insulte les cultes à "
        "mystères et les religions nationales, et presse les empereurs (Constance II et Constant) "
        "de donner le coup de grâce au paganisme expirant. Firmicus exhorte au châtiment légal des "
        "adeptes du paganisme, à la destruction de leurs temples, à la confiscation de leurs statues "
        "et de leurs propriétés sacerdotales (cf. De err. 16, 4-5 ; 20, 7 ; 28, 6 ; 29, 1, citant "
        "Deutéronome 13, 6-10 et 12-18 en faveur de la répression sanglante). Édition critique citée "
        "par Amand : G. Heuten, Iulius Firmicus Maternus, De errore profanarum religionum, "
        "Traduction nouvelle avec texte et commentaire, Travaux de la Faculté de Philosophie et "
        "Lettres de l'Université de Bruxelles 8, Bruxelles 1938 (214 p.) ; édition antérieure de "
        "K. Ziegler. Compte rendu : dom C. Lambot, Bulletin d'ancienne littérature chrétienne "
        "latine III (1939) p. [14]-[15] n. 28. Bibliographie complète chez Heuten 1938, p. 31-34. "
        "Malgré son intolérance virulente, c'est selon Amand notre principale source d'information "
        "sur le paganisme tardif du IVe siècle, et sur bien des points elle est unique."
    ),
    description_en=(
        "Christian apologetic pamphlet composed by Iulius Firmicus Maternus after his conversion "
        "to Christianity, c. 343-350 CE — about ten years after his astrological Mathesis. "
        "According to Amand 1945 (Book I Ch. VII §I, p. 178), this 'furious pamphlet' insults "
        "mystery cults and national religions, and presses emperors (Constantius II and Constans) "
        "to deal the death-blow to expiring paganism. Firmicus exhorts to legal punishment of "
        "pagan adherents, destruction of their temples, confiscation of their statues and priestly "
        "properties (cf. De err. 16, 4-5; 20, 7; 28, 6; 29, 1, citing Deuteronomy 13:6-10 and "
        "12-18 in favor of bloody repression). Critical edition cited by Amand: G. Heuten, "
        "Iulius Firmicus Maternus, De errore profanarum religionum, Traduction nouvelle avec "
        "texte et commentaire, Travaux de la Faculté de Philosophie et Lettres de l'Université "
        "de Bruxelles 8, Bruxelles 1938 (214 p.); earlier edition by K. Ziegler. Review: dom C. "
        "Lambot, Bulletin d'ancienne littérature chrétienne latine III (1939) p. [14]-[15] n. 28. "
        "Complete bibliography in Heuten 1938, p. 31-34. Despite its virulent intolerance, "
        "according to Amand it is our principal source of information on late-4th-century "
        "paganism, and on many points it is unique."
    ),
    md=md_base(
        page_range="p. 178",
        md_line_range="ll. 10259-10271",
        chapter="Livre I Ch. VII §I (Le sénateur astrologue → pamphlétaire chrétien)",
        chapter_actual="Livre I Ch. VII §I — Le pamphlet De errore",
        confidence=0.9, contains_greek=False, contains_latin=True,
        cited_editions=[
            "Iulius Firmicus Maternus, De errore profanarum religionum, traduction nouvelle avec texte et commentaire par G. Heuten, Travaux de la Faculté de Philosophie et Lettres de l'Université de Bruxelles 8, Bruxelles 1938",
            "K. Ziegler (édition antérieure citée par Amand pour le texte)",
        ],
        evidence_pending=True,
        evidence_pending_reason="De errore absent du corpus EleutherIA (ingestion path : Heuten 1938 ou Ziegler)",
        extra={
            "preservation_status": "complete_unique_manuscript_tradition",
            "title_latin": "De errore profanarum religionum",
            "compositional_date": "c. 343-350 CE",
            "dedicatees": "Constance II et Constant",
            "amand_judgement_register": "evaluation_critique_negative_pamphlet_intolerant",
            "amand_secondary_value": "principale source sur le paganisme tardif IVe s.",
        },
    ),
))


# --- Syntheses Firmicus portrait + thèse paradoxale ---

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_firmicus_paradox_pagan_christian",
    ntype="synthesis",
    label="Amand 1945 — Le paradoxe Firmicus : astrologue paien sénatorial puis pamphlétaire chrétien fanatique",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. VII §I, p. 177-179, ll. 10135-10285). « Étrange "
        "physionomie que celle de ce personnage ! » Iulius Firmicus Maternus, haut fonctionnaire "
        "de l'Empire et sénateur romain, fut d'abord « un païen convaincu et un 'prêtre' de la "
        "religion astrologique ». Il compile alors avec la ferveur d'un initié, sous Constantin "
        "(vers 334-337), l'énorme Somme astrologique de la Mathesis. À peine dix ans plus tard, le "
        "même homme rédige le De errore profanarum religionum, « ce furieux pamphlet où l'apologiste "
        "improvisé insulte les cultes à mystères et les religions nationales, et où il presse les "
        "empereurs de donner le coup de grâce au paganisme expirant ». Amand le décrit comme « païen "
        "dévot, prêtre du Soleil, de la Lune et des autres dieux astraux, — puis chrétien excessivement "
        "zélé et converti trop empressé, dont l'ardeur, peut-être sincère, dégénère en un étroit et "
        "sombre fanatisme » (p. 180). L'intérêt philologique : c'est précisément ce paradoxe — un "
        "astrologue qui rapporte fidèlement les arguments contre l'astrologie — qui fait de Firmicus "
        "le témoin n°3 d'Amand : « cet infatigable copiste, expert dans l'art de démarquer les "
        "textes, a inséré dans sa Mathesis pour les réfuter ensuite trois séries d'arguments "
        "antiastrologiques d'origine néo-académicienne, parmi lesquels nous découvrons, avec quelque "
        "surprise, l'argumentation morale du chef de la Nouvelle Académie » (p. 178)."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. VII §I, p. 177-179, ll. 10135-10285). 'Strange "
        "physiognomy of this character!' Iulius Firmicus Maternus, high imperial official and "
        "Roman senator, was first 'a convinced pagan and a priest of the astrological religion'. "
        "He then compiles, with the fervor of an initiate, under Constantine (c. 334-337), the "
        "enormous astrological summa of the Mathesis. Barely ten years later, the same man writes "
        "De errore profanarum religionum, 'that furious pamphlet where the improvised apologist "
        "insults mystery cults and national religions, and where he presses emperors to deal "
        "expiring paganism the death-blow'. Amand describes him as 'devout pagan, priest of the "
        "Sun, Moon and other astral gods, — then excessively zealous Christian and overeager "
        "convert, whose ardor, perhaps sincere, degenerates into a narrow and dark fanaticism' "
        "(p. 180). Philological interest: it is precisely this paradox — an astrologer faithfully "
        "reporting arguments against astrology — that makes Firmicus Amand's witness no. 3: 'this "
        "indefatigable copyist, expert in the art of marking texts, has inserted into his "
        "Mathesis in order subsequently to refute them three series of anti-astrological "
        "arguments of Neo-Academic origin, among which we discover, with some surprise, the moral "
        "argumentation of the New Academy's head' (p. 178)."
    ),
    md=md_base(
        page_range="p. 177-180",
        md_line_range="ll. 10135-10285",
        chapter="Livre I Ch. VII §I (Le sénateur astrologue paien → pamphlétaire chrétien)",
        chapter_actual="Livre I Ch. VII §I — Le paradoxe biographique",
        confidence=0.95,
        cited_editions=[
            "Fr. Boll, art. Firmicus, Pauly-Wissowa RE VI 1909, col. 2365-2379",
            "M. Schanz, Geschichte der römischen Litteratur IV/1² 1914, p. 129-137",
            "G. Heuten, De errore profanarum religionum, Bruxelles 1938, biographie p. 3-11",
        ],
        extra={
            "amand_thesis_type": "biographical_paradox",
            "amand_judgement_register": "evaluation_critique_assumee",
            "two_works_polar_opposition": ["Mathesis astrologue", "De errore pamphlétaire chrétien"],
            "amand_witness_justification": "paradoxe documentaire : un astrologue rapporte fidèlement les arguments contre l'astrologie",
            "engages_with_scholars": ["Boll", "Schanz", "Bardenhewer", "Heuten", "Lambot"],
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_firmicus_absolute_fatalism_doctrine",
    ntype="synthesis",
    label="Amand 1945 — Fatalisme absolu professé par Firmicus (Mathesis I, 9, 2-3)",
    period=None, school=None, role=None,
    description=(
        "Synthèse d'Amand 1945 (Livre I Ch. VII §I.3, p. 180, ll. 10272-10310). Amand établit "
        "sans équivoque que Firmicus est « un partisan enthousiaste et convaincu du fatalisme "
        "absolu sous sa forme astrologique » : les textes foisonnent dans la Mathesis, mais "
        "Amand cite spécifiquement Mathesis I, 9, 2-3 (Kroll-Skutsch I p. 33 l. 23 — p. 34 l. 7) : "
        "« Hanc mortium nobis uarietatem fata describunt ; haec sunt illa stellarum decreta, quae "
        "paulo ante protulimus. […] hinc constat ortum finemque uitae, actus etiam nostros uniuersos, "
        "studia, cupiditates et quicquid illud est, quod ad humanae nationis (rationis, corr. Kroll) "
        "conuersationem pertinet, fatalis necessitatis ineuitabili sententia contineri. Cedamus "
        "itaque fide ueritatis oppressi, et confiteamur, uerae rationis secuti iudicia, nihil in "
        "nostra, sed totum in fatorum esse positum potestate, ut quicquid uel facimus uel patimur, "
        "totum hoc Fortunae nobis iudicio conferatur ». Position fataliste sans exception : naissance, "
        "fin de vie, actes, désirs, conversations, tout est sous la juridiction inévitable de la "
        "necessitas fatalis. Rien dans notre puissance, tout dans le pouvoir des destins. "
        "Conséquence : la valeur philologique du témoin n°3 est d'autant plus forte que Firmicus, "
        "fataliste convaincu, n'a aucun intérêt à embellir les arguments adversaires — la fidélité "
        "documentaire est ainsi maximale."
    ),
    description_en=(
        "Synthesis from Amand 1945 (Book I Ch. VII §I.3, p. 180, ll. 10272-10310). Amand "
        "unequivocally establishes that Firmicus is 'an enthusiastic and convinced supporter of "
        "absolute fatalism in its astrological form': texts abound in the Mathesis, but Amand "
        "specifically cites Mathesis I, 9, 2-3 (Kroll-Skutsch I p. 33 l. 23 — p. 34 l. 7): 'Hanc "
        "mortium nobis uarietatem fata describunt; haec sunt illa stellarum decreta, quae paulo "
        "ante protulimus. […] hinc constat ortum finemque uitae, actus etiam nostros uniuersos, "
        "studia, cupiditates et quicquid illud est, quod ad humanae nationis (rationis, corr. "
        "Kroll) conuersationem pertinet, fatalis necessitatis ineuitabili sententia contineri. "
        "Cedamus itaque fide ueritatis oppressi, et confiteamur, uerae rationis secuti iudicia, "
        "nihil in nostra, sed totum in fatorum esse positum potestate, ut quicquid uel facimus uel "
        "patimur, totum hoc Fortunae nobis iudicio conferatur'. Fatalist position without "
        "exception: birth, end of life, acts, desires, conversations, all is under the "
        "inescapable jurisdiction of necessitas fatalis. Nothing in our power, all in the fates' "
        "power. Consequence: the philological value of witness no. 3 is all the stronger since "
        "Firmicus, a convinced fatalist, has no interest in embellishing adversarial arguments — "
        "documentary fidelity is thus maximal."
    ),
    md=md_base(
        page_range="p. 180",
        md_line_range="ll. 10272-10310",
        chapter="Livre I Ch. VII §I.3 (Le fatalisme absolu professé par Firmicus)",
        chapter_actual="Livre I Ch. VII §I.3 — Doctrine fataliste",
        confidence=0.95, contains_latin=True,
        cited_editions=[
            "Iulius Firmicus Maternus, Mathesis I, 9, 2-3, éd. Kroll-Skutsch t. I 1897, p. 33 l. 23 — p. 34 l. 7",
        ],
        evidence_pending=True,
        evidence_pending_reason="Math I.9.2-3 absent du corpus EleutherIA",
        extra={
            "amand_thesis_type": "doctrinal_portrait_fatalism",
            "key_latin_terms": ["necessitas fatalis", "fatorum potestas", "Fortunae iudicium"],
            "philological_value_paradox": "fataliste convaincu = témoin fidèle des arguments adversaires",
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_firmicus_book_i_apologetic_structure",
    ntype="synthesis",
    label="Amand 1945 — Structure du livre I de la Mathesis : apologie introductive contre 3 arguments carnéadiens",
    period=None, school=None, role=None,
    description=(
        "Synthèse philologique d'Amand 1945 (Livre I Ch. VII §II.1, p. 181 + résumé note 2, "
        "ll. 10396-10500). Le premier livre de la Mathesis n'est qu'une « apologie détaillée de "
        "l'astrologie », spécifiquement du fatalisme astral. Après le prologue (adresse à Lollianus "
        "Mauortius), le ch. 1 expose les controverses entre philosophes (nature des dieux, "
        "immortalité de l'âme, bien/mal moral — Boll note que Firmicus paraphrase Cicéron De "
        "natura deorum I, 1, 2 — 3, 5). Les ch. 2-3 rapportent in extenso et sans les réfuter "
        "TROIS importantes objections : (a) argument ethnographique « a coloribus et moribus "
        "gentium » des particularités physiques et morales des peuples (Math I, 2, 1-4 ; "
        "Kroll-Skutsch I p. 6, 1 — p. 7, 8 ; cf. §B2 carnéadien) ; (b) argumentation morale "
        "antifataliste (Math I, 2, 5-11 ; le témoin n°3) ; (c) impossibilité d'une exacte "
        "observation des astres au moment de la naissance (Math I, 3, 2 ; Kroll-Skutsch I p. 9 "
        "l. 17-25). Les ch. 3-10 réfutent ces arguments : ch. 3-4 considérations posidoniennes ; "
        "ch. 5 réfutation de l'argument ethnographique par Chrysippe ; ch. 6 réfutation morale "
        "(« lois pénales aident les faibles ») ; ch. 7 exemples mythologico-historiques de Fortuna ; "
        "ch. 8 contre l'opinion intermédiaire (vie libre / naissance-mort fatales) ; ch. 9 "
        "récapitulation fataliste ; ch. 10 retour ethnographique via théorie des cinq zones. Source "
        "principale identifiée par Boll : manuel apotélesmatique Néchepso-Pétosiris (col. 2367-2369)."
    ),
    description_en=(
        "Philological synthesis from Amand 1945 (Book I Ch. VII §II.1, p. 181 + summary footnote 2, "
        "ll. 10396-10500). Mathesis Book I is merely a 'detailed apology for astrology', "
        "specifically for astral fatalism. After the prologue (address to Lollianus Mauortius), "
        "ch. 1 exposes controversies between philosophers (nature of gods, immortality of soul, "
        "moral good/evil — Boll notes Firmicus paraphrases Cicero De natura deorum I, 1, 2 — 3, "
        "5). Ch. 2-3 report in extenso and without refuting them THREE important objections: "
        "(a) ethnographic argument 'a coloribus et moribus gentium' on physical and moral "
        "particularities of peoples (Math I, 2, 1-4; Kroll-Skutsch I p. 6, 1 — p. 7, 8; cf. §B2 "
        "Carneadean); (b) moral anti-fatalist argumentation (Math I, 2, 5-11; the witness no. 3); "
        "(c) impossibility of exact astral observation at birth (Math I, 3, 2; Kroll-Skutsch I "
        "p. 9 ll. 17-25). Ch. 3-10 refute these arguments: ch. 3-4 Posidonian considerations; "
        "ch. 5 refutation of ethnographic argument via Chrysippus; ch. 6 moral refutation "
        "('penal laws help the weak'); ch. 7 mythologico-historical examples of Fortuna; ch. 8 "
        "against the intermediate opinion (free life / fatalist birth-death); ch. 9 fatalist "
        "recap; ch. 10 ethnographic return via five-zones theory. Main source identified by Boll: "
        "the Nechepso-Petosiris apotelesmatic manual (col. 2367-2369)."
    ),
    md=md_base(
        page_range="p. 181",
        md_line_range="ll. 10396-10500",
        chapter="Livre I Ch. VII §II.1 (Les arguments antiastrologiques consignés dans la Mathesis)",
        chapter_actual="Livre I Ch. VII §II.1 — Structure du livre I",
        confidence=0.9,
        cited_editions=[
            "Iulius Firmicus Maternus, Mathesis, livre I, éd. Kroll-Skutsch t. I 1897",
            "Fr. Boll, art. Firmicus, Pauly-Wissowa RE VI 1909, col. 2367-2373",
            "Cicéron, De natura deorum I, 1, 2 — 3, 5 (parallèle paraphrasé par Firmicus)",
        ],
        evidence_pending=True,
        evidence_pending_reason="Mathesis livre I absent du corpus EleutherIA",
        extra={
            "amand_thesis_type": "philological_structure_analysis",
            "three_carneadean_arguments_in_book_i": [
                {"locus": "Math I, 2, 1-4", "topic": "argument ethnographique a coloribus et moribus gentium"},
                {"locus": "Math I, 2, 5-11", "topic": "argumentation morale antifataliste (témoin n°3)"},
                {"locus": "Math I, 3, 2", "topic": "impossibilité observation exacte au moment naissance"},
            ],
            "main_source_hypothesis_boll": "manuel apotélesmatique Néchepso-Pétosiris",
            "engages_with_scholars": ["Boll", "Posidonius"],
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_firmicus_carneadean_origin_identification",
    ntype="synthesis",
    label="Amand 1945 — Identification néo-académicienne (Carnéade) des adversaires de Firmicus (Boll + portrait Math I, 3, 4)",
    period=None, school=None, role=None,
    description=(
        "Synthèse philologique d'Amand 1945 (Livre I Ch. VII §II.2, p. 183-185, ll. 10500-10580). "
        "Amand reprend l'identification du Fr. Boll (RE VI col. 2367 l. 65 — 2368 l. 3) selon "
        "laquelle les adversaires visés par Firmicus dans la Mathesis livre I sont « les "
        "Néo-Académiciens dont le chef Carnéade avait formulé les arguments les plus pénétrants "
        "contre l'astrologie ». Amand ajoute ses propres preuves textuelles : le portrait des "
        "adversaires (Math I, 1, 1-2 ; Kroll-Skutsch I p. 4 l. 9-24) décrit des opposants oraux, "
        "oratoires, dialecticiens belliqueux qui manient des arguments ad hominem pénétrants et "
        "syllogistiques. Puis Math I, 3, 4 (Kroll-Skutsch I p. 10 l. 9-15) ajoute le trait "
        "décisif : « Iste uehemens mathematicorum accusator, qui artem istam tam elata oratione "
        "persequitur, [...] seuerus et uehemens et totius quodammodo diuinitatis iura perturbans "
        "argumentorum suorum aculeos licentia exercitati sermonis exacuit » — « Qui s'y "
        "tromperait ? C'est Carnéade en personne, à peine défiguré par la caricature » (Amand "
        "p. 185). Amand écarte explicitement la candidature des Sceptiques de type radical "
        "(Énésidème, Ménodote, Sextus) en arguant qu'ils n'ont apporté aucun argument vraiment "
        "nouveau à l'arsenal de Carnéade (cf. Brochard 1923, Les Sceptiques grecs, p. 125-127)."
    ),
    description_en=(
        "Philological synthesis from Amand 1945 (Book I Ch. VII §II.2, p. 183-185, ll. "
        "10500-10580). Amand takes up Fr. Boll's identification (RE VI col. 2367 l. 65 — 2368 "
        "l. 3) according to which the adversaries targeted by Firmicus in Mathesis Book I are "
        "'the Neo-Academics whose head Carneades had formulated the most penetrating arguments "
        "against astrology'. Amand adds his own textual proofs: the portrait of the adversaries "
        "(Math I, 1, 1-2; Kroll-Skutsch I p. 4 ll. 9-24) describes oral, oratorical, bellicose "
        "dialectic opponents wielding penetrating ad hominem and syllogistic arguments. Then "
        "Math I, 3, 4 (Kroll-Skutsch I p. 10 ll. 9-15) adds the decisive trait: 'Iste uehemens "
        "mathematicorum accusator, qui artem istam tam elata oratione persequitur, [...] seuerus "
        "et uehemens et totius quodammodo diuinitatis iura perturbans argumentorum suorum aculeos "
        "licentia exercitati sermonis exacuit' — 'Who could be mistaken? It is Carneades in "
        "person, barely disguised by caricature' (Amand p. 185). Amand explicitly rules out the "
        "candidacy of radical-type Skeptics (Aenesidemus, Menodotus, Sextus) by arguing they "
        "brought no genuinely new argument to Carneades' arsenal (cf. Brochard 1923, Les "
        "Sceptiques grecs, p. 125-127)."
    ),
    md=md_base(
        page_range="p. 183-185",
        md_line_range="ll. 10500-10580",
        chapter="Livre I Ch. VII §II.2 (L'origine carnéadienne de ces arguments)",
        chapter_actual="Livre I Ch. VII §II.2 — Identification néo-académicienne (Boll + portrait)",
        confidence=0.9, contains_latin=True,
        cited_editions=[
            "Iulius Firmicus Maternus, Mathesis I, 1, 1-2, éd. Kroll-Skutsch I p. 4 l. 9-24",
            "Iulius Firmicus Maternus, Mathesis I, 3, 4, éd. Kroll-Skutsch I p. 10 l. 9-15",
            "Fr. Boll, art. Firmicus, Pauly-Wissowa RE VI 1909, col. 2367-2368",
            "V. Brochard, Les Sceptiques grecs, Paris 1923 (réimpression), p. 125-127",
        ],
        evidence_pending=True,
        evidence_pending_reason="Mathesis I.1.1-2 et I.3.4 absents du corpus EleutherIA",
        extra={
            "amand_thesis_type": "philological_identification_targeted_school",
            "amand_judgement_register": "haute_probabilite_appuyee_sur_Boll",
            "amand_verbatim_fr": "C'est Carnéade en personne, à peine défiguré par la caricature",
            "ruled_out_alternatives": ["Aenésidème", "Ménodote", "Sextus Empiricus"],
            "engages_with_scholars": ["Boll", "Brochard"],
        },
    ),
))


def make_witness3_arg(*, nid: str, label: str, page_range: str, md_line_range: str,
                      chapter_actual: str, confidence: float, fr_desc: str, en_desc: str,
                      firmicus_locus: str, transmits_b1: list[str],
                      sub_arguments: list[dict[str, str]]) -> dict[str, Any]:
    return make_node(
        nid=nid, ntype="argument", label=label,
        period="Hellenistic", school="school_academics", role=None,
        description=fr_desc, description_en=en_desc,
        md=md_base(
            page_range=page_range, md_line_range=md_line_range,
            chapter="Livre I Ch. VII §III (L'argumentation de Carnéade rapportée par Firmicus)",
            chapter_actual=chapter_actual,
            confidence=confidence, contains_latin=True,
            cited_editions=[
                f"Iulius Firmicus Maternus, Mathesis {firmicus_locus}, éd. Kroll-Skutsch t. I 1897, p. 7 l. 8 — p. 9 l. 4",
            ],
            evidence_pending=True,
            evidence_pending_reason=f"Firmicus Mathesis {firmicus_locus} absent du corpus EleutherIA (ingestion path: archive.org Kroll-Skutsch 1897 djvu, see docs/reports/2026-05-15-five-witnesses-ingestion-paths.md)",
            extra={
                "amand_witness_rank": "primary_witness_n3",
                "amand_witness_role": "witness_3_firmicus",
                "is_witness_argument": True,
                "argument_category": "argument_carneadean_moral_reconstruction_via_witness_firmicus",
                "transmits_argument_pivots_b1": transmits_b1,
                "firmicus_section_locus": firmicus_locus,
                "sub_arguments": sub_arguments,
                "stylistic_register": "diatribe_populaire_imagée_avec_illustrations_astrologiques",
            },
        ),
    )


# --- 3 arguments du témoin n°3 Firmicus Mathesis I, 2, 5-11 ---

NEW_INSERTS.append(make_witness3_arg(
    nid="argument_firmicus_witness3_virtue_vain_under_stars_amand1945",
    label="Témoin n°3 (Firmicus Math I, 2, 5-7) — Premier argument : effort de vertu vain sous les constellations",
    page_range="p. 185-186, 186-187 (texte latin)",
    md_line_range="ll. 10500-10600",
    chapter_actual="Livre I Ch. VII §III.1.A — Témoin n°3 : vertu vaine si dépendante des astres",
    confidence=0.85,
    fr_desc=(
        "Premier argument moral antifataliste reconstruit chez Firmicus Mathesis I, 2, 5-7 "
        "(Kroll-Skutsch I p. 7 l. 8 — p. 8) par Amand 1945 (analyse p. 185-186, texte latin "
        "p. 186-187). Thème principal du témoin n°3 : le fatalisme astrologique fait dépendre les "
        "vertus (temperantia, fortitudo, prudentia, iustitia) et les vices des décrets des astres "
        "(stellarum decretis), non de nos volontés propres. Si nos vices sont l'effet d'une "
        "constellation maléfique (par exemple Mercure et Mars conjoints), il est vain pour quiconque "
        "d'essayer d'acquérir la vertu (« Frustra igitur consilio ac ratione errantis animi uitia "
        "comprimimus, frustra luxuriosas libidinum illecebras temperamus, frustra grauitatis "
        "instinctu aequitatis modestiam iuraque conquirimus »). La vertu elle-même devient un don "
        "des astres (Saturne ou Jupiter). Tout zèle moral est dépensé en pure perte. Argument "
        "conséquentialiste pratique parallèle à Alexandre De Fato 16 (Amand p. 145-146, p. 150-151) "
        "et à Philon De prov. I, 82 (Amand p. 92-93, p. 94). Style : diatribe populaire imagée avec "
        "noms planétaires (Mercure, Mars, Vénus, Saturne, Jupiter, Lune)."
    ),
    en_desc=(
        "First moral anti-fatalist argument reconstructed in Firmicus Mathesis I, 2, 5-7 "
        "(Kroll-Skutsch I p. 7 l. 8 — p. 8) by Amand 1945 (analysis p. 185-186, Latin text "
        "p. 186-187). Main theme of witness no. 3: astrological fatalism makes virtues "
        "(temperantia, fortitudo, prudentia, iustitia) and vices depend on stellar decrees "
        "(stellarum decretis), not on our own wills. If our vices result from a maleficent "
        "constellation (e.g. Mercury and Mars conjoined), it is vain for anyone to try to acquire "
        "virtue ('Frustra igitur consilio ac ratione errantis animi uitia comprimimus, frustra "
        "luxuriosas libidinum illecebras temperamus, frustra grauitatis instinctu aequitatis "
        "modestiam iuraque conquirimus'). Virtue itself becomes a gift of the stars (Saturn or "
        "Jupiter). All moral zeal is spent in pure loss. Practical consequentialist argument "
        "parallel to Alexander De Fato 16 (Amand p. 145-146, p. 150-151) and Philo De prov. I, "
        "82 (Amand p. 92-93, p. 94). Style: popular imaged diatribe with planetary names "
        "(Mercury, Mars, Venus, Saturn, Jupiter, Moon)."
    ),
    firmicus_locus="I, 2, 5-7",
    transmits_b1=["argument_carneadean_virtue_vice_amand1945",
                  "argument_carneadean_action_futility_amand1945",
                  "argument_carneadean_general_theme_amand1945"],
    sub_arguments=[
        {"locus": "Math I, 2, 5", "topic": "thème général : vertus/vices = décrets stellaires"},
        {"locus": "Math I, 2, 6", "topic": "ad hominem : 'sit iniquus, sit perfidus' — excuse offerte aux vices"},
        {"locus": "Math I, 2, 7", "topic": "vanité de l'effort moral en présence de la nécessité stellaire"},
    ],
))

NEW_INSERTS.append(make_witness3_arg(
    nid="argument_firmicus_witness3_religion_useless_amand1945",
    label="Témoin n°3 (Firmicus Math I, 2, 8-9) — Deuxième argument : mépris des dieux et inutilité des rites",
    page_range="p. 186, 187",
    md_line_range="ll. 10600-10670",
    chapter_actual="Livre I Ch. VII §III.1.B — Témoin n°3 : conséquences religieuses du fatalisme",
    confidence=0.85,
    fr_desc=(
        "Deuxième argument moral antifataliste reconstruit chez Firmicus Mathesis I, 2, 8-9 "
        "(Kroll-Skutsch I p. 8) par Amand 1945 (analyse p. 186, texte latin p. 187). Conclusion "
        "logique du fatalisme astrologique : le mépris des dieux et l'inutilité des rites sacrés. "
        "« Contemnamus, si uidetur, deos, et religionum sanctas uenerabilesque caerimonias "
        "sacrilego desperationis ardore publicemus ! Quid inuocas, arator, deos ? » C'est bien "
        "inutilement que le laboureur invoquera les dieux, et que le vigneron recommandera ses "
        "plants de vigne à Bacchus (« frustra deuoues uitium palmites Libero tuo religiosa cum "
        "trepidatione »). Si les bénéfices et les pertes dépendent du cours des astres, sans "
        "intervention de la divinité, prière et culte deviennent absurdes. Argument parallèle à "
        "Alexandre De Fato 17 (Amand p. 146, p. 151) sur la suppression de providence, piété, "
        "mantique — donc témoin convergent (= 2 témoins sur 6) pour l'arg-pivot B1 carnéadien "
        "providence-piété. Style : diatribe avec apostrophes (arator, uini cultor)."
    ),
    en_desc=(
        "Second moral anti-fatalist argument reconstructed in Firmicus Mathesis I, 2, 8-9 "
        "(Kroll-Skutsch I p. 8) by Amand 1945 (analysis p. 186, Latin text p. 187). Logical "
        "consequence of astrological fatalism: contempt of the gods and uselessness of sacred "
        "rites. 'Contemnamus, si uidetur, deos, et religionum sanctas uenerabilesque caerimonias "
        "sacrilego desperationis ardore publicemus! Quid inuocas, arator, deos?' It is uselessly "
        "that the ploughman invokes the gods, and that the vine-grower recommends his vine-"
        "shoots to Bacchus ('frustra deuoues uitium palmites Libero tuo religiosa cum "
        "trepidatione'). If profits and losses depend on stellar courses, without divine "
        "intervention, prayer and cult become absurd. Argument parallel to Alexander De Fato 17 "
        "(Amand p. 146, p. 151) on suppression of providence, piety, mantic — thus convergent "
        "witness (= 2 witnesses out of 6) for the Carneadean B1 pivot-argument on providence-"
        "piety. Style: diatribe with apostrophes (arator, uini cultor)."
    ),
    firmicus_locus="I, 2, 8-9",
    transmits_b1=["argument_carneadean_piety_amand1945",
                  "argument_carneadean_providence_mantike_alexander_amand1945"],
    sub_arguments=[
        {"locus": "Math I, 2, 8", "topic": "Frustra, o bone uir — vanité de la diligence morale"},
        {"locus": "Math I, 2, 9", "topic": "Contemnamus deos — mépris des dieux ; arator/uinitor inutiles"},
    ],
))

NEW_INSERTS.append(make_witness3_arg(
    nid="argument_firmicus_witness3_laws_abrogated_amand1945",
    label="Témoin n°3 (Firmicus Math I, 2, 10-11) — Troisième argument : abrogation des lois et droits du magistrat",
    page_range="p. 186, 187-188",
    md_line_range="ll. 10670-10780",
    chapter_actual="Livre I Ch. VII §III.1.C — Témoin n°3 : abrogation des lois et magistrature",
    confidence=0.9,
    fr_desc=(
        "Troisième argument moral antifataliste reconstruit chez Firmicus Mathesis I, 2, 10-11 "
        "(Kroll-Skutsch I p. 8 l. 25 — p. 9 l. 4) par Amand 1945 (analyse p. 186, texte latin "
        "p. 187-188). Argument législatif-juridique : si le fatalisme astrologique est vrai, le "
        "législateur doit abroger ses lois et supprimer les châtiments. « Tu qui promulgas leges "
        "ac iura sancis, tolle scita, refige tabulas, et istis nos seuerissimis animaduersionibus "
        "libera ». Pourquoi ? Parce que ce n'est pas nous qui sommes responsables de nos crimes "
        "mais bien Mercure (l'a fait sacrilège), Vénus (l'a fait adultère), Mars (l'a armé pour "
        "tuer). De plus, les magistrats n'ont aucun droit de châtier des hommes qui ne sont que "
        "des instruments passifs des planètes maléfiques (« non habetis, magistratus, iustam "
        "animaduertendi substantiam, quia scitis nos ad ista uitia malignis stellarum semper "
        "incitari fomitibus »). Argument parallèle à Philon De prov. I, 79-81 (Amand p. 92 ; "
        "p. 93-94) et plus partiellement à Alexandre De Fato 19 (Amand p. 147-148, p. 152-154). "
        "Double convergence : 3 témoins (Philon + Firmicus + Alexandre) pour l'argument-pivot B1 "
        "legislation/responsabilité — atteint le seuil de Carnéade selon la règle d'Amand des "
        "« 3 témoins sur 6 »."
    ),
    en_desc=(
        "Third moral anti-fatalist argument reconstructed in Firmicus Mathesis I, 2, 10-11 "
        "(Kroll-Skutsch I p. 8 l. 25 — p. 9 l. 4) by Amand 1945 (analysis p. 186, Latin text "
        "p. 187-188). Legislative-juridical argument: if astrological fatalism is true, the "
        "legislator must abrogate his laws and abolish punishments. 'Tu qui promulgas leges ac "
        "iura sancis, tolle scita, refige tabulas, et istis nos seuerissimis animaduersionibus "
        "libera'. Why? Because we are not responsible for our crimes but rather Mercury (made him "
        "sacrilegious), Venus (made him adulterous), Mars (armed him to kill). Furthermore, "
        "magistrates have no right to punish men who are only passive instruments of malign "
        "planets ('non habetis, magistratus, iustam animaduertendi substantiam, quia scitis nos "
        "ad ista uitia malignis stellarum semper incitari fomitibus'). Argument parallel to Philo "
        "De prov. I, 79-81 (Amand p. 92; p. 93-94) and more partially to Alexander De Fato 19 "
        "(Amand p. 147-148, p. 152-154). Double convergence: 3 witnesses (Philo + Firmicus + "
        "Alexander) for B1 pivot-argument on legislation/responsibility — reaches the Carneadean "
        "threshold per Amand's 'three witnesses out of six' rule."
    ),
    firmicus_locus="I, 2, 10-11",
    transmits_b1=["argument_carneadean_legislation_amand1945",
                  "argument_carneadean_virtue_vice_amand1945",
                  "argument_carneadean_incentives_amand1945"],
    sub_arguments=[
        {"locus": "Math I, 2, 10", "topic": "abrogation des lois (tolle scita, refige tabulas) ; crimes attribués aux planètes"},
        {"locus": "Math I, 2, 11", "topic": "magistrats sans droit de châtier des instruments passifs"},
    ],
))


# --- Envelope Firmicus ---
NEW_INSERTS.append(make_node(
    nid="argument_firmicus_witness3_envelope_amand1945",
    ntype="argument",
    label="Argument-cadre du témoin n°3 Firmicus Mathesis I, 2, 5-11 — enveloppe tripartite de la diatribe antifataliste",
    period="Hellenistic", school="school_academics", role=None,
    description=(
        "Enveloppe argumentative générale identifiée par Amand 1945 (p. 185-188, ll. 10500-10791) "
        "à l'intérieur de Firmicus Mathesis I, 2, 5-11 (Kroll-Skutsch I p. 7 l. 8 — p. 9 l. 4). "
        "Le témoin n°3 articule trois arguments en cascade : (1) vertu et effort moral vains sous "
        "la nécessité stellaire (Math I, 2, 5-7) ; (2) mépris des dieux et inutilité des rites "
        "(Math I, 2, 8-9) ; (3) abrogation des lois et droits du magistrat (Math I, 2, 10-11). "
        "Selon Amand, ce témoin « est présenté[e] ici avec une insistance singulière et une vie "
        "étonnante, qui contrastent avec la froideur et la rigueur scolastique de l'exposé "
        "d'Alexandre d'Aphrodise » (p. 184). Caractère stylistique : diatribe populaire avec "
        "apostrophes (arator, uini cultor, magistratus), exclamations rhétoriques, mise en scène "
        "des planètes (Mercure, Mars, Vénus, Saturne, Jupiter), parallélismes anaphoriques "
        "(frustra…frustra…frustra). Convergence philologique : ce témoin recoupe et complète "
        "(via la règle des 3/6) les témoins n°1 (Philon) et n°2 (Alexandre) sur les arguments-"
        "pivots B1 carnéadiens — notamment vertu/vice, législation, providence/piété. Cible "
        "polémique : Carnéade en personne, à peine défiguré (cf. Math I, 1, 1-2 et I, 3, 4)."
    ),
    description_en=(
        "General argumentative envelope identified by Amand 1945 (p. 185-188, ll. 10500-10791) "
        "inside Firmicus Mathesis I, 2, 5-11 (Kroll-Skutsch I p. 7 l. 8 — p. 9 l. 4). Witness "
        "no. 3 articulates three cascading arguments: (1) virtue and moral effort vain under "
        "stellar necessity (Math I, 2, 5-7); (2) contempt of gods and uselessness of rites "
        "(Math I, 2, 8-9); (3) abrogation of laws and magistrates' rights (Math I, 2, 10-11). "
        "According to Amand, this witness 'is presented here with a singular insistence and "
        "astonishing vivacity, contrasting with the coldness and scholastic rigor of Alexander "
        "of Aphrodisias' exposition' (p. 184). Stylistic character: popular diatribe with "
        "apostrophes (arator, uini cultor, magistratus), rhetorical exclamations, planetary "
        "mise en scène (Mercury, Mars, Venus, Saturn, Jupiter), anaphoric parallelisms "
        "(frustra…frustra…frustra). Philological convergence: this witness overlaps and "
        "complements (via the 3/6 rule) witnesses no. 1 (Philo) and no. 2 (Alexander) on the "
        "B1 Carneadean pivot-arguments — notably virtue/vice, legislation, providence/piety. "
        "Polemical target: Carneades in person, barely disguised (cf. Math I, 1, 1-2 and I, 3, 4)."
    ),
    md=md_base(
        page_range="p. 184-188",
        md_line_range="ll. 10500-10791",
        chapter="Livre I Ch. VII §III (Argumentation de Carnéade rapportée par Firmicus)",
        chapter_actual="Livre I Ch. VII §III — Enveloppe tripartite du témoin n°3",
        confidence=0.9, contains_latin=True,
        cited_editions=[
            "Iulius Firmicus Maternus, Mathesis I, 2, 5-11, éd. Kroll-Skutsch t. I 1897, p. 7 l. 8 — p. 9 l. 4",
        ],
        evidence_pending=True,
        evidence_pending_reason="Firmicus Mathesis I.2.5-11 absent du corpus EleutherIA",
        extra={
            "envelope_for_sub_arguments": [
                "argument_firmicus_witness3_virtue_vain_under_stars_amand1945",
                "argument_firmicus_witness3_religion_useless_amand1945",
                "argument_firmicus_witness3_laws_abrogated_amand1945",
            ],
            "argument_category": "argument_carneadean_moral_reconstruction_envelope_witness_n3",
            "amand_witness_rank": "primary_witness_n3_structure",
            "amand_witness_role": "witness_3_firmicus",
            "is_witness_argument": True,
            "stylistic_register": "diatribe_populaire_imagée",
        },
    ),
))


# --- Synthesis comparative Firmicus vs Philon/Alexandre ---
NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_firmicus_diatribe_style_vs_alexander_scholasticism",
    ntype="synthesis",
    label="Amand 1945 — Firmicus en diatribe imagée populaire ≠ Alexandre scolastique sec ; affinité avec Philon",
    period=None, school=None, role=None,
    description=(
        "Synthèse comparative d'Amand 1945 (Livre I Ch. VII §III.2 fin, p. 188, ll. 10780-10791). "
        "Selon Amand, « tandis que le scholarque péripatéticien d'Athènes [Alexandre] expose cette "
        "argumentation sous une forme strictement scientifique, avec une rigueur et une sécheresse "
        "bien aristotélicienne, Philon et Firmicus Maternus la présentent sous un aspect populaire "
        "et imagé. Tous deux évitent les termes d'école, tous deux emploient le procédé vivant et "
        "piquant de la diatribe, tous deux enfin recourent à l'illustration astrologique pour "
        "appuyer et éclairer leurs affirmations » (p. 188). Affinité stylistique forte Philon-"
        "Firmicus, contraste fort avec Alexandre. Conséquence philologique : la tradition "
        "carnéadienne se transmet selon deux canaux genres : (a) canal scolaire-philosophique "
        "(Alexandre) destiné aux disciples et auditeurs d'élite ; (b) canal populaire-rhétorique "
        "(Philon, Firmicus) destiné à un large auditoire. Carnéade lui-même opérait dans les deux "
        "registres (cf. Cicéron Acad. II, 78). Cette polarité stylistique sert d'argument auxiliaire "
        "à Amand pour démontrer que les trois témoins n°1, n°2, n°3 dérivent d'une source commune "
        "(Carnéade) sans qu'ils dépendent textuellement les uns des autres."
    ),
    description_en=(
        "Comparative synthesis from Amand 1945 (Book I Ch. VII §III.2 end, p. 188, ll. 10780-10791). "
        "According to Amand, 'while the Peripatetic scholarch of Athens [Alexander] expounds this "
        "argumentation in a strictly scientific form, with Aristotelian rigor and dryness, Philo "
        "and Firmicus Maternus present it in a popular and imaged aspect. Both avoid school terms, "
        "both employ the lively and stinging procedure of diatribe, both finally resort to "
        "astrological illustration to support and illuminate their statements' (p. 188). Strong "
        "stylistic affinity Philo-Firmicus, strong contrast with Alexander. Philological "
        "consequence: the Carneadean tradition is transmitted along two genre channels: "
        "(a) scholastic-philosophical channel (Alexander) destined for disciples and elite "
        "auditors; (b) popular-rhetorical channel (Philo, Firmicus) destined for a broad "
        "audience. Carneades himself operated in both registers (cf. Cicero Acad. II, 78). This "
        "stylistic polarity serves as auxiliary argument for Amand to demonstrate that the three "
        "witnesses no. 1, no. 2, no. 3 derive from a common source (Carneades) without textually "
        "depending on each other."
    ),
    md=md_base(
        page_range="p. 188",
        md_line_range="ll. 10780-10791",
        chapter="Livre I Ch. VII §III.2 (Texte original — clôture de chapitre)",
        chapter_actual="Livre I Ch. VII §III.2 — Synthèse stylistique comparative",
        confidence=0.85,
        cited_editions=[],
        extra={
            "amand_thesis_type": "stylistic_comparative_synthesis",
            "two_channels_transmission": [
                "channel_a_scholastic_philosophical_Alexander",
                "channel_b_popular_rhetorical_diatribe_Philo_Firmicus",
            ],
            "philological_consequence": "common_source_Carneades_without_inter_textual_dependence_among_witnesses",
        },
    ),
))


# --- Synthesis : transmission Carnéade → Firmicus (long path via manuel apotélesmatique) ---
NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_transmission_carneades_to_firmicus_chain",
    ntype="synthesis",
    label="Amand 1945 — Chaîne de transmission Carnéade → Néchepso-Pétosiris → Firmicus (conjecturale)",
    period=None, school=None, role=None,
    description=(
        "Synthèse transversale d'Amand 1945 (Livre I Ch. VII §II.1 note 2 + §II.2, p. 181-185, "
        "ll. 10396-10580). Chaîne de transmission proposée : (1) Carnéade (214/213-129/128 BCE) "
        "formule oralement les arguments antiastrologiques et antifatalistes ; (2) Clitomaque "
        "(187/186-110/109 BCE) en consigne par écrit la substance dans 400+ livres aujourd'hui "
        "perdus ; (3) intégration des arguments dans le manuel apotélesmatique alexandrin attribué "
        "à Néchepso et Pétosiris (compilation hellénistique, IIe-Ier s. BCE, perdue mais reconstruit "
        "par K. Riess via fragments) — paradoxe : un manuel astrologique conserve des arguments "
        "antiastrologiques pour les citer et les réfuter ; (4) Firmicus Maternus (IVe s. CE) copie "
        "ces objections du manuel pour les présenter et les réfuter dans la Mathesis I, 2, 5-11. "
        "Confidence faible (0.55) car la médiation par Néchepso-Pétosiris est une conjecture de Boll "
        "(RE VI col. 2372) et non une démonstration. Distance temporelle 500+ ans entre Carnéade et "
        "Firmicus implique de multiples intermédiaires perdus. Amand : « c'est cependant cette "
        "chaîne qui permet seule de comprendre pourquoi un astrologue convaincu du IVe siècle "
        "transmet fidèlement (par copie scolaire) des arguments forgés cinq siècles plus tôt par "
        "le chef de la Nouvelle Académie ». Filiation conjecturale assumée comme telle."
    ),
    description_en=(
        "Cross-cutting synthesis from Amand 1945 (Book I Ch. VII §II.1 footnote 2 + §II.2, p. "
        "181-185, ll. 10396-10580). Proposed transmission chain: (1) Carneades (214/213-129/128 "
        "BCE) orally formulates the anti-astrological and anti-fatalist arguments; (2) "
        "Clitomachus (187/186-110/109 BCE) commits their substance to writing in 400+ books now "
        "lost; (3) integration of arguments into the Alexandrian apotelesmatic manual attributed "
        "to Nechepso and Petosiris (Hellenistic compilation, 2nd-1st c. BCE, lost but reconstructed "
        "by K. Riess via fragments) — paradox: an astrological manual preserves anti-astrological "
        "arguments to cite and refute them; (4) Firmicus Maternus (4th c. CE) copies these "
        "objections from the manual to present and refute them in Mathesis I, 2, 5-11. Low "
        "confidence (0.55) since Nechepso-Petosiris mediation is a Boll conjecture (RE VI col. "
        "2372), not a demonstration. 500+ year temporal distance between Carneades and Firmicus "
        "implies multiple lost intermediaries. Amand: 'this is however the chain that alone "
        "allows us to understand why a convinced astrologer of the 4th century faithfully "
        "transmits (via scholastic copy) arguments forged five centuries earlier by the head of "
        "the New Academy'. Conjectural filiation assumed as such."
    ),
    md=md_base(
        page_range="p. 181-185",
        md_line_range="ll. 10396-10580",
        chapter="Livre I Ch. VII §II — synthèse de chaîne (Carnéade → Firmicus)",
        chapter_actual="Synthèse transversale B4 : chaîne Carnéade → Firmicus",
        confidence=0.55,
        cited_editions=[
            "Fr. Boll, art. Firmicus, Pauly-Wissowa RE VI 1909, col. 2367-2372 (hypothèse Néchepso-Pétosiris)",
            "K. Riess, Nechepsonis et Petosiridis fragmenta magica, Philologus Suppl. VI (1893)",
        ],
        extra={
            "amand_thesis_type": "transmission_chain_conjecture",
            "amand_judgement_register": "haute_probabilite_avoue_chaîne_longue",
            "chain_steps": [
                "Carnéade (214/213-129/128 BCE) — Académie, n'écrit rien",
                "Clitomaque (187/186-110/109 BCE) — disciple, 400+ livres perdus",
                "manuel apotélesmatique Néchepso-Pétosiris (IIe-Ier s. BCE, perdu) — conjecture de Boll",
                "Firmicus Maternus (IVe s. CE), Mathesis I, 2, 5-11",
            ],
            "temporal_distance_years": "~500",
            "lost_intermediaries_count_min": 2,
            "engages_with_scholars": ["Boll", "Riess"],
        },
    ),
))
