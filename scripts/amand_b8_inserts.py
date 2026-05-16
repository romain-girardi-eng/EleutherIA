"""Amand B8 — NEW_INSERTS list (new nodes).

Bilingual FR/EN plain-text descriptions. Periods title-case canonical only.
Type prefixes match `type` field. Metadata via amand_metadata().

Sections:
  - PERSONS  : Lucian, Oinomaos, Demonax, Diogenes of Oinoanda, Diogenianus
  - WORKS    : Lucian dialogues, Oinomaos Goeton phora, Diogenes inscription,
               Diogenianus Peri heimarmenes
  - SYNTHESES: 4 Intro §I + 3 Lucian + 2 Oinomaos + 5 Neoplatonists + 1 Hierocles
  - ARGUMENTS: 2 Lucian + 1 Oinomaos + 2 Diogenes Oinoanda + 2 Diogenianus +
               1 Hierocles bizarre adaptation
  - CONCEPTS : 2 (heimarmene_astrologica_amand, plotinian_intellectual_eph_hemin)
"""
from __future__ import annotations

from typing import Any

from amand_b8_utils import amand_metadata, dump_metadata


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
        id="person_lucian_samosata_c125_180",
        type="person",
        label="Lucien de Samosate",
        description=(
            "Lucien de Samosate (c. 125 - après 180 CE), rhéteur et satiriste "
            "grec d'origine syrienne, formé à la rhétorique d'Asie Mineure puis "
            "actif comme conférencier itinérant en Ionie, Grèce, Italie et Gaule, "
            "et finalement haut fonctionnaire impérial en Égypte sous Commode. "
            "Pour Amand 1945 (Livre I Ch. III, p. 107-115), Lucien est un sophiste "
            "tardif sans opinion philosophique stable et ennemi acharné du "
            "charlatanisme, du dogmatisme et de la superstition. Bien qu'il n'ait "
            "pas une optique méthodique d'observateur, il met dans la bouche de "
            "ses personnages (Cyniscos dans Zeus à court de raisons, Sostratos "
            "dans le 30e Dialogue des morts, le narrateur dans l'Apologie) des "
            "adaptations populaires et incisives d'un topos antifataliste "
            "néo-académicien tombé dans le domaine public. Sa polémique demeure "
            "purement morale et négative — aucune connexion avec l'apotélesmatique "
            "proprement dite. Ami des Épicuriens et grand admirateur d'Épicure "
            "pour son rationalisme antireligieux (Alex. 47), sympathisant du "
            "cynisme sincère (Vie de Démonax)"
        ),
        description_en=(
            "Lucian of Samosata (c. 125 - after 180 CE), Greek rhetorician and "
            "satirist of Syrian origin, trained in Asia Minor rhetoric then "
            "active as a wandering lecturer in Ionia, Greece, Italy and Gaul, "
            "finally an imperial high official in Egypt under Commodus. For "
            "Amand 1945 (Book I Ch. III, p. 107-115), Lucian is a late sophist "
            "without stable philosophical opinion and a fierce enemy of "
            "charlatanism, dogmatism and superstition. Although he has no "
            "methodical observer's optic, he places into his characters' mouths "
            "(Cyniscus in Zeus Confuted, Sostratus in Dialogue of the Dead 30, "
            "the narrator in the Apology) popular and incisive adaptations of a "
            "Neo-Academic antifatalist topos that had become public domain. His "
            "polemic remains purely moral and negative — no link to apotelesmatic "
            "astrology proper. Friend of the Epicureans and great admirer of "
            "Epicurus for his anti-religious rationalism (Alex. 47), sympathetic "
            "to sincere Cynicism (Life of Demonax)"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 107-115",
            md_line_range="ll. 6445-6792",
            chapter="Livre I Ch. III (Lucien de Samosate)",
            amand_chapter_actual="Lucien de Samosate",
            extra={
                "amand_witness_role": "popular_adaptor_carneadean (not a primary witness — adaptation libre)",
                "alternative_names": [
                    "Lucian of Samosata",
                    "Λουκιανὸς ὁ Σαμοσατεύς",
                ],
                "language": "Greek",
                "origin": "Samosata (Commagene, Syria)",
                "principal_editions_cited_by_amand": [
                    "Jacobitz, Luciani Samosatensis opera, Teubner 1904-1907",
                    "Nilén, Lucianus vol. I, Teubner 1906 (Vie de Démonax)",
                    "A.M. Harmon, Loeb (cited via Caster 1938)",
                ],
                "key_scholarly_studies_via_amand": [
                    "M. Caster, Lucien et la pensée religieuse de son temps (Paris 1937)",
                    "M. Caster, Études sur Alexandre ou le faux prophète (Paris 1938)",
                    "R. Helm, Lucian und Menipp (Teubner 1906)",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="person_oinomaos_gadara_2c_ce",
        type="person",
        label="Oinomaos de Gadara",
        description=(
            "Oinomaos de Gadara (Pérée ; floruit sous les Antonins, IIe siècle CE), "
            "philosophe cynique contemporain de Plutarque (plus jeune) et de "
            "Lucien (plus âgé). Pour Amand 1945 (Livre I Ch. IV §II, p. 127-134), "
            "Oinomaos est un tempérament impétueux mais un esprit peu profond et "
            "peu spéculatif, partisan décidé du libre arbitre et adversaire "
            "acharné du fatalisme stoïcien et de la mantique oraculaire. Son "
            "œuvre majeure, le Γοήτων φώρα (Les charlatans démasqués), pamphlet "
            "écrit dans le style vif, haché et caustique de la diatribe cynique, "
            "rédige une accusation en règle contre Apollon, dieu des oracles. "
            "Eusèbe en a transcrit d'importants fragments dans Préparation "
            "évangélique V.19-36 et VI.7.1-42, et P. Vallette 1908 en a donné "
            "l'édition critique. Julien (Discours 7) lui reproche de graves "
            "impiétés. Oinomaos n'apporte aucun argument vraiment nouveau dans "
            "la polémique antifataliste — il accommode 'à une sauce fort "
            "pimentée' les lieux communs traditionnels depuis Carnéade"
        ),
        description_en=(
            "Oinomaos of Gadara (Peraea; floruit under the Antonines, 2nd c. CE), "
            "Cynic philosopher contemporary with Plutarch (younger) and Lucian "
            "(older). For Amand 1945 (Book I Ch. IV §II, p. 127-134), Oinomaos "
            "is an impetuous temperament but a shallow and unspeculative mind, "
            "a determined partisan of free will and a fierce adversary of Stoic "
            "fatalism and oracular divination. His major work, the Γοήτων φώρα "
            "(Charlatans Unmasked), a pamphlet written in the lively, choppy and "
            "caustic style of the Cynic diatribe, draws up a formal indictment "
            "of Apollo, god of oracles. Eusebius transcribed important fragments "
            "in Praeparatio Evangelica V.19-36 and VI.7.1-42, and P. Vallette "
            "1908 published the critical edition. Julian (Discourse 7) reproaches "
            "him with grave impieties. Oinomaos brings no genuinely new argument "
            "to the antifatalist polemic — he accommodates 'with a strongly "
            "spiced sauce' the traditional commonplaces stemming from Carneades"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 127-134",
            md_line_range="ll. 7370-7636",
            chapter="Livre I Ch. IV §II (Oinomaos de Gadara)",
            amand_chapter_actual="Oinomaos de Gadara et le cynisme du IIᵉ s.",
            extra={
                "amand_witness_role": "carneadean_adaptor_not_witness (pas un texte témoin — adaptation libre Cynique)",
                "alternative_names": [
                    "Oenomaus of Gadara",
                    "Οἰνόμαος ὁ Γαδαρεύς",
                ],
                "language": "Greek",
                "origin": "Gadara (Peraea)",
                "principal_editions_cited_by_amand": [
                    "P. Vallette, De Oenomao Cynico (Paris, C. Klincksieck, 1908)",
                    "W. Dindorf, Eusebii Praeparatio Evangelica I, Teubner 1867",
                ],
                "key_scholarly_studies_via_amand": [
                    "H. J. Mette, art. Oinomaos von Gadara, RE XVII.2 (1937), col. 2249-2251",
                    "I. Bruns, Lucian und Oenomaus, Rhein. Mus. 44 (1889), p. 374-396",
                    "E. Zeller, Ph. Gr. III.1.5 (1923), p. 796-798",
                    "K. Praechter dans Ueberweg-Praechter, Ph. Alt. (1926), p. 509-510",
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="person_demonax_cyprus_2c_ce",
        type="person",
        label="Démonax de Chypre",
        description=(
            "Démonax de Chypre (IIe siècle CE), philosophe cynique de bonne "
            "compagnie, cultivé et platonisant, dont la douceur et l'humanité "
            "contrastent avec la rudesse de Diogène. Pour Amand 1945 (Livre I "
            "Ch. IV §I, p. 128-129), Démonax illustre la polémique antifataliste "
            "cynique du IIe siècle par un trait conservé chez Lucien (Vie de "
            "Démonax 37, éd. Nilén p. 84) : voyant un devin prédire l'avenir "
            "moyennant salaire, Démonax l'interpelle — si tu peux changer les "
            "décrets du Destin, quel que soit le prix tu demandes trop peu ; "
            "mais si tous les événements s'accomplissent selon le bon plaisir "
            "du Destin, quelle peut être l'utilité de ton art ? La source unique "
            "de renseignements sur ce Cynique est la Vie de Démonax de Lucien, "
            "dont l'authenticité est admise. Esprit large, indépendant, enclin à "
            "l'éclectisme"
        ),
        description_en=(
            "Demonax of Cyprus (2nd c. CE), Cynic philosopher of good company, "
            "cultivated and Platonizing, whose mildness and humanity contrast "
            "with Diogenes's roughness. For Amand 1945 (Book I Ch. IV §I, p. "
            "128-129), Demonax illustrates 2nd-century Cynic antifatalist "
            "polemic through an anecdote preserved in Lucian (Life of Demonax "
            "37, ed. Nilén p. 84): seeing a soothsayer predict the future for "
            "pay, Demonax challenges him — if you can change the decrees of "
            "Fate, whatever your price you ask too little; but if all events "
            "unfold by Fate's pleasure, what use can your art have? The sole "
            "source on this Cynic is Lucian's Life of Demonax, whose "
            "authenticity is admitted. A broad, independent mind inclined to "
            "eclecticism"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 128-129",
            md_line_range="ll. 7329-7370",
            chapter="Livre I Ch. IV §I (Le cynisme au IIᵉ s.)",
            amand_chapter_actual="Démonax — figure cynique du IIᵉ s.",
            extra={
                "alternative_names": ["Demonax", "Δημώναξ"],
                "language": "Greek",
                "origin": "Cyprus",
                "principal_attestation": "Lucian, Vita Demonactis (Vie de Démonax)",
                "amand_pedigree_witness": "Cynic antifatalist line — soothsayer paradox",
            },
        ),
        confidence=0.8,
    ),
    _node(
        id="person_diogenes_oinoanda_c200_ce",
        type="person",
        label="Diogénès d'Oinoanda",
        description=(
            "Diogénès d'Oinoanda (Lycie ; vers 200 CE), philosophe épicurien "
            "âgé qui fit graver sur le mur d'un portique de sa ville natale une "
            "immense inscription philosophique. Pour Amand 1945 (Livre I Ch. III "
            "Note supplémentaire §II, p. 117-120), Diogénès est un 'apôtre de "
            "l'ataraxie', épicurien convaincu et militant mais 'assez ignorant "
            "et sans envergure d'esprit', philanthrope qui veut détromper "
            "l'humanité et la guider dans le vrai chemin du salut épicurien. "
            "L'inscription comprend une esquisse de la physique, une lettre à "
            "Antipatros sur l'infinité des mondes, un exposé d'éthique, des "
            "sentences d'Épicure, des lettres personnelles et un opuscule sur "
            "la vieillesse. Au fragment XXXIII (William 1907) il démontre la "
            "non-existence de l'εἱμαρμένη, en s'appuyant sur la non-existence "
            "de la mantique : si la mantique est écartée, il n'y a plus d'argument "
            "en faveur de l'εἱμαρμένη"
        ),
        description_en=(
            "Diogenes of Oinoanda (Lycia; c. 200 CE), elderly Epicurean "
            "philosopher who had a huge philosophical inscription carved on the "
            "wall of a portico in his native city. For Amand 1945 (Book I Ch. "
            "III Supplementary Note §II, p. 117-120), Diogenes is an 'apostle "
            "of ataraxia', a convinced and militant Epicurean but 'rather "
            "ignorant and without breadth of mind', a philanthropist who wishes "
            "to undeceive humanity and guide it on the true path of Epicurean "
            "salvation. The inscription comprises a sketch of physics, a letter "
            "to Antipater on the infinity of worlds, an ethical exposition, "
            "Epicurean sentences, personal letters and an opusculum on old "
            "age. At fragment XXXIII (William 1907) he demonstrates the "
            "non-existence of εἱμαρμένη, leaning on the non-existence of "
            "divination: if divination is set aside, there is no further "
            "argument in favour of εἱμαρμένη"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 117-120",
            md_line_range="ll. 6845-6975",
            chapter="Livre I Ch. III Note supplémentaire §II (Diogénès d'Oinoanda)",
            amand_chapter_actual="Note supplémentaire — Diogénès d'Oinoanda",
            extra={
                "alternative_names": ["Diogenes of Oenoanda", "Διογένης Οἰνοανδεύς"],
                "language": "Greek",
                "origin": "Oinoanda (Lycia)",
                "principal_editions_cited_by_amand": [
                    "I. William, Diogenis Oinoandensis fragmenta (Teubner 1907) — édition de référence",
                    "G. Cousin, Bull. corr. hellén. 16 (1892), p. 1-76",
                    "H. Usener, Epikureische Schriften auf Stein, Rhein. Mus. 47 (1892), p. 414-456",
                    "R. Heberdey & E. Kalinka, Bull. corr. hellén. 21 (1897), p. 346-443",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="person_diogenianus_epicurean_2c_ce",
        type="person",
        label="Diogénianos l'Épicurien",
        description=(
            "Diogénianos (probablement IIe siècle CE), philosophe épicurien (sous "
            "réserve d'inventaire selon Amand) auteur d'un Περὶ εἱμαρμένης dont "
            "Eusèbe a transcrit plusieurs longs passages dans la Préparation "
            "évangélique IV.3.1-13 et VI.8.1-38. Pour Amand 1945 (Livre I Ch. "
            "III Note supplémentaire §III, p. 120-126), Diogénianos mène une "
            "vigoureuse polémique contre la doctrine chrysippienne de l'εἱμαρμένη "
            "et de la mantique, révélant une dépendance très nette à l'égard "
            "de la lutte que Carnéade a soutenue. Trois axes : (1) vanité et "
            "mensonge de la divination — la plupart des prédictions ne se "
            "réalisent pas, et les rares vérifiées sont dues au hasard ; (2) "
            "inutilité voire nocivité de la divination — la connaissance de "
            "maux inévitables n'apporte qu'ennui et tristesse ; (3) réfutation "
            "des étymologies chrysippiennes (Πεπρωμένη, Λάχεσις, Ἄτροπος, "
            "Κλωθώ, εἱμαρμένη). Diogénianos concède toutefois — chose curieuse "
            "pour un Épicurien strict — que beaucoup d'événements sont gouvernés "
            "par l'εἱμαρμένη, ce qui fait douter Amand de son strict épicurisme. "
            "Gercke 1885 et von Arnim (SVF II, 914, 998-999) ont rassemblé les "
            "fragments"
        ),
        description_en=(
            "Diogenianus (probably 2nd c. CE), Epicurean philosopher (with "
            "reservation per Amand) author of a Περὶ εἱμαρμένης several long "
            "passages of which Eusebius transcribed in Praeparatio Evangelica "
            "IV.3.1-13 and VI.8.1-38. For Amand 1945 (Book I Ch. III "
            "Supplementary Note §III, p. 120-126), Diogenianus conducts a "
            "vigorous polemic against the Chrysippan doctrine of εἱμαρμένη and "
            "divination, revealing very clear dependence on Carneades's "
            "struggle. Three axes: (1) vanity and falsehood of divination — "
            "most predictions are unfulfilled, the rare verified ones due to "
            "chance; (2) uselessness or harmfulness of divination — knowledge "
            "of inevitable evils brings only sorrow; (3) refutation of "
            "Chrysippus's etymologies (Πεπρωμένη, Λάχεσις, Ἄτροπος, Κλωθώ, "
            "εἱμαρμένη). Diogenianus however concedes — curious for a strict "
            "Epicurean — that many events are governed by εἱμαρμένη, leading "
            "Amand to doubt his strict Epicureanism. Gercke 1885 and von Arnim "
            "(SVF II, 914, 998-999) collected the fragments"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 120-126",
            md_line_range="ll. 6975-7278",
            chapter="Livre I Ch. III Note supplémentaire §III (Diogénianos)",
            amand_chapter_actual="Note supplémentaire — Diogénianos",
            extra={
                "alternative_names": ["Diogenianus", "Διογενιανός"],
                "language": "Greek",
                "school_uncertainty_amand": "Épicurien sous réserve d'inventaire — concession sur portée de l'εἱμαρμένη",
                "principal_editions_cited_by_amand": [
                    "W. Dindorf, Eusebii Praeparatio Evangelica I, Teubner 1867, p. 162-165 + 300-307",
                    "A. Gercke, Chrysippea (Jahrbücher f. klass. Philol. Suppl. 14, 1885), p. 748-755",
                    "H. von Arnim, SVF II.914, 998-999",
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
        id="work_lucian_apologia",
        type="work",
        label="Lucien, Apologie",
        description=(
            "Apologie (Ἀπολογία) de Lucien de Samosate, opuscule où le rhéteur "
            "syrien s'excuse auprès de son ami Sabinus d'avoir accepté un emploi "
            "rémunéré dans l'administration provinciale d'Égypte sur ses vieux "
            "jours. Pour Amand 1945 (Livre I Ch. III §II.1, p. 110-111), le "
            "passage clé est Apologie 8 (éd. Jacobitz I, p. 323-324) où Lucien "
            "énumère les raisons spécieuses qu'il pourrait invoquer — au "
            "premier rang desquelles le fatalisme. Mais il rejette aussitôt "
            "cette excuse comme 'trop vulgaire' (κομιδῇ ἰδιωτικόν), grossier "
            "artifice pour excuser une conduite blâmable. Allusion fugitive — "
            "Amand juge peu probable que ce soit un emploi conscient de "
            "l'argument moral de Carnéade — mais témoignage du mépris de "
            "Lucien pour la conception fataliste vulgaire de son temps"
        ),
        description_en=(
            "Apology (Ἀπολογία) by Lucian of Samosata, an opusculum in which "
            "the Syrian rhetorician excuses himself to his friend Sabinus for "
            "having accepted a paid post in the Egyptian provincial "
            "administration in his old age. For Amand 1945 (Book I Ch. III §II.1, "
            "p. 110-111), the key passage is Apology 8 (ed. Jacobitz I, p. "
            "323-324) where Lucian lists the specious reasons he might invoke "
            "— first among them fatalism. But he immediately rejects this "
            "excuse as 'too vulgar' (κομιδῇ ἰδιωτικόν), a coarse artifice for "
            "excusing blameworthy conduct. Fleeting allusion — Amand judges it "
            "unlikely to be a conscious use of Carneades's moral argument — "
            "but a testimony to Lucian's contempt for the vulgar fatalist "
            "conception of his time"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 110-111",
            md_line_range="ll. 6534-6573",
            chapter="Livre I Ch. III §II.1 (Apologie)",
            amand_chapter_actual="Lucien — Apologie 8",
            extra={
                "amand_passage_key": "Apol. 8 (ed. Jacobitz I, p. 323-324)",
                "amand_classification": "trace_marginale_carneadean",
                "amand_cited_edition_unverified": True,
                "editions": [
                    {"raw": "C. Jacobitz, Luciani Samosatensis opera I (Teubner 1905)"},
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="work_lucian_dialogues_mortuorum",
        type="work",
        label="Lucien, Dialogues des morts (Nekrikoi Dialogoi)",
        description=(
            "Dialogues des morts (Νεκρικοὶ Διάλογοι) de Lucien de Samosate, "
            "série de courts dialogues satiriques imités de Ménippe de Gadara "
            "mettant en scène des morts dans l'Hadès, présidés par Minos, "
            "Hermès et les juges infernaux. Pour Amand 1945 (Livre I Ch. III "
            "§II.2, p. 111-112), le 30e Dialogue des morts (éd. Jacobitz I, p. "
            "189-190) — entre Minos et le brigand Sostratos — fait écho à la "
            "violente polémique de Carnéade contre les fatalistes stoïciens. "
            "Sostratos, sommé d'être torturé dans le Pyriphlégéton, oblige "
            "Minos à reconnaître que (a) tout est filé par la Moîra à la "
            "naissance, (b) l'instrument n'est pas responsable, et conclut : "
            "'il est injuste de nous punir, nous qui n'avons fait qu'accomplir "
            "les ordres de Clotho' (Dial. mort. 30.3). L'argument ad absurdum "
            "carnéadien contre Chrysippe ressort intact. Voir aussi Dial. mort. "
            "19.2 fin"
        ),
        description_en=(
            "Dialogues of the Dead (Νεκρικοὶ Διάλογοι) by Lucian of Samosata, "
            "a series of short satirical dialogues imitated from Menippus of "
            "Gadara, staging the dead in Hades, presided over by Minos, Hermes "
            "and the infernal judges. For Amand 1945 (Book I Ch. III §II.2, "
            "p. 111-112), the 30th Dialogue of the Dead (ed. Jacobitz I, p. "
            "189-190) — between Minos and the brigand Sostratus — echoes "
            "Carneades's violent polemic against Stoic fatalists. Sostratus, "
            "ordered to be tortured in the Pyriphlegethon, forces Minos to "
            "concede that (a) all is spun by Moira at birth, (b) the "
            "instrument is not responsible, and concludes: 'it is unjust to "
            "punish us, who only carried out Clotho's orders' (Dial. mort. "
            "30.3). The Carneadean reductio ad absurdum against Chrysippus "
            "appears intact. See also Dial. mort. 19.2 end"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 111-112",
            md_line_range="ll. 6574-6622",
            chapter="Livre I Ch. III §II.2 (30e Dialogue des morts)",
            amand_chapter_actual="Lucien — Dialogues des morts 30 (Sostratos-Minos)",
            extra={
                "amand_passage_key": "Dial. mort. 30.2-3 (ed. Jacobitz I, p. 189-190)",
                "amand_classification": "echo_carneadean_topos_morality",
                "editions": [
                    {"raw": "C. Jacobitz, Luciani Samosatensis opera I (Teubner 1905)"},
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_lucian_iuppiter_confutatus",
        type="work",
        label="Lucien, Zeus à court de raisons (Iuppiter confutatus)",
        description=(
            "Zeus à court de raisons (Ζεὺς ἐλεγχόμενος) de Lucien de Samosate, "
            "dialogue satirique imité de Ménippe où le philosophe cynique "
            "Cyniscos accable Zeus de questions outrecuidantes sur la "
            "Providence, la mantique, l'immortalité divine et le fatalisme. "
            "Pour Amand 1945 (Livre I Ch. III §II.3, p. 112-115), c'est dans "
            "ce piquant dialogue (éd. Jacobitz II, p. 338-348) que Lucien "
            "accumule le plus systématiquement les objections néo-académiciennes "
            "et épicuriennes contre l'omnipotence de l'εἱμαρμένη. Étapes "
            "successives : Zeus avoue son impuissance vis-à-vis de la Moîra "
            "(ch. 2) ; les Moires commandent aux dieux (ch. 4) ; les prières "
            "et hécatombes deviennent inutiles (ch. 5) ; Zeus s'en prend "
            "vainement aux Épicuriens (ch. 6) ; l'immortalité des dieux ne fait "
            "qu'éterniser leur esclavage (ch. 7) ; la divination oraculaire "
            "est réfutée (ch. 12-14) ; et culmination : si tout est régi par "
            "le Destin, Minos doit châtier l'Heimarmene au lieu de Sisyphe et "
            "la Moîra au lieu de Tantale (ch. 18). L'argument ad absurdum "
            "carnéadien ferme la bouche à Zeus lui-même. Pour Amand, c'est "
            "ici que le topos néo-académicien est présenté de la manière la "
            "plus populaire et incisive"
        ),
        description_en=(
            "Zeus Confuted (Ζεὺς ἐλεγχόμενος) by Lucian of Samosata, satirical "
            "dialogue imitated from Menippus in which the Cynic philosopher "
            "Cyniscus assails Zeus with insolent questions on Providence, "
            "divination, divine immortality and fatalism. For Amand 1945 (Book "
            "I Ch. III §II.3, p. 112-115), it is in this piquant dialogue (ed. "
            "Jacobitz II, p. 338-348) that Lucian most systematically piles up "
            "the Neo-Academic and Epicurean objections against the omnipotence "
            "of εἱμαρμένη. Successive stages: Zeus admits his impotence "
            "before Moira (ch. 2); the Moirai command the gods (ch. 4); "
            "prayers and hecatombs become useless (ch. 5); Zeus vainly attacks "
            "the Epicureans (ch. 6); the immortality of the gods only "
            "eternalises their slavery (ch. 7); oracular divination is refuted "
            "(ch. 12-14); and the climax: if all is governed by Fate, Minos "
            "should chastise Heimarmene rather than Sisyphus, and Moira rather "
            "than Tantalus (ch. 18). The Carneadean reductio ad absurdum "
            "silences Zeus himself. For Amand, this is where the Neo-Academic "
            "topos is presented in the most popular and incisive way"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 112-115",
            md_line_range="ll. 6623-6792",
            chapter="Livre I Ch. III §II.3 (Zeus à court de raisons)",
            amand_chapter_actual="Lucien — Iuppiter confutatus",
            extra={
                "amand_passage_key": "Iupp. conf. 1-19 (ed. Jacobitz II, p. 338-348)",
                "amand_classification": "principal_lucianic_locus_carneadean_moral_topos",
                "editions": [
                    {"raw": "C. Jacobitz, Luciani Samosatensis opera II (Teubner 1907)"},
                    {"raw": "R. Helm, Lucian und Menipp (Teubner 1906), ch. 4 p. 115-132 — analyse des sources"},
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="work_lucian_vita_demonactis",
        type="work",
        label="Lucien, Vie de Démonax (Vita Demonactis)",
        description=(
            "Vie de Démonax (Δημώνακτος Βίος) de Lucien de Samosate, biographie "
            "sympathique du philosophe cynique chypriote Démonax. Pour Amand "
            "1945 (Livre I Ch. IV §I, p. 128-129), la source unique de "
            "renseignements sur ce Cynique de bonne compagnie. Authenticité "
            "lucianesque non contestée. Le passage clé Vie Dém. 37 (éd. Nilén "
            "p. 84, Teubner 1906) conserve le mot de Démonax au devin payant : "
            "'si tu peux changer les décrets du Destin, quel que soit ton prix "
            "tu demandes trop peu ; mais si tous les événements s'accomplissent "
            "selon le bon plaisir du Destin, quelle peut être l'utilité de ton "
            "art ?' — argument classique de l'incompatibilité fatum-mantique"
        ),
        description_en=(
            "Life of Demonax (Δημώνακτος Βίος) by Lucian of Samosata, a "
            "sympathetic biography of the Cynic philosopher from Cyprus, "
            "Demonax. For Amand 1945 (Book I Ch. IV §I, p. 128-129), the sole "
            "source of information on this Cynic of good company. Lucianic "
            "authenticity not contested. The key passage Vita Dem. 37 (ed. "
            "Nilén p. 84, Teubner 1906) preserves Demonax's remark to a paid "
            "soothsayer: 'if you can change the decrees of Fate, whatever your "
            "price you ask too little; but if all events come about by Fate's "
            "pleasure, what use can your art have?' — classical argument of "
            "the fatum-divination incompatibility"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 128-129",
            md_line_range="ll. 7329-7370",
            chapter="Livre I Ch. IV §I (Démonax)",
            amand_chapter_actual="Lucien — Vita Demonactis",
            extra={
                "amand_passage_key": "Vit. Dem. 37 (ed. Nilén p. 84)",
                "editions": [
                    {"raw": "N. Nilén, Lucianus I.1 (Teubner 1906), p. 73-90"},
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_oinomaos_goeton_phora",
        type="work",
        label="Oinomaos, Les Charlatans démasqués (Γοήτων φώρα)",
        description=(
            "Γοήτων φώρα (Les charlatans démasqués) d'Oinomaos de Gadara, "
            "pamphlet cynique perdu en intégralité mais transmis par citations "
            "étendues dans la Préparation évangélique d'Eusèbe de Césarée (V, "
            "ch. 19-36, et VI, ch. 7, 1-42). Pour Amand 1945 (Livre I Ch. IV "
            "§II, p. 129-134), le pamphlet rédige une accusation en règle "
            "contre Apollon, dieu des oracles, dans le style vif et caustique "
            "de la diatribe. L'accusateur harcèle Apollon d'interrogations "
            "répétées qui ne lui laissent aucun répit, puis apostrophe également "
            "Démocrite et surtout Chrysippe, 'coryphées du déterminisme'. Deux "
            "axes : (1) polémique antioraculaire — perversion morale des oracles, "
            "ambiguïté voulue, charlatans cupides (V.19-36) ; (2) polémique "
            "antifataliste — incompatibilité entre prédiction et liberté de "
            "l'homme, contradiction entre εἱμαρμένη et responsabilité morale "
            "(VI.7.1-42). Citation centrale en VI.7.35-41 : 'Vous ne nous avez "
            "pas permis, ô dieux, de devenir vertueux ! Au contraire vous nous "
            "avez contraints et forcés à vivre en criminels' — adaptation libre "
            "et pimentée du topos carnéadien. Édition critique : P. Vallette, "
            "De Oenomao Cynico, Paris, Klincksieck, 1908"
        ),
        description_en=(
            "Γοήτων φώρα (Charlatans Unmasked) by Oinomaos of Gadara, a Cynic "
            "pamphlet entirely lost but transmitted through extensive citations "
            "in Eusebius of Caesarea's Praeparatio Evangelica (V, ch. 19-36, "
            "and VI, ch. 7, 1-42). For Amand 1945 (Book I Ch. IV §II, p. "
            "129-134), the pamphlet drafts a formal indictment against Apollo, "
            "god of oracles, in the lively caustic style of the diatribe. The "
            "accuser harasses Apollo with repeated questions that leave him no "
            "respite, then also apostrophizes Democritus and especially "
            "Chrysippus, 'coryphaei of determinism'. Two axes: (1) "
            "anti-oracular polemic — moral perversion of oracles, deliberate "
            "ambiguity, greedy charlatans (V.19-36); (2) antifatalist polemic "
            "— incompatibility between prediction and human freedom, "
            "contradiction between εἱμαρμένη and moral responsibility "
            "(VI.7.1-42). Central citation at VI.7.35-41: 'You did not allow "
            "us, O gods, to become virtuous! On the contrary you constrained "
            "and forced us to live as criminals' — a free and spiced adaptation "
            "of the Carneadean topos. Critical edition: P. Vallette, De "
            "Oenomao Cynico, Paris, Klincksieck, 1908"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 129-134",
            md_line_range="ll. 7372-7636",
            chapter="Livre I Ch. IV §II (Oinomaos — Γοήτων φώρα)",
            amand_chapter_actual="Oinomaos — Goeton phora",
            extra={
                "amand_passage_key_oracular": "Eus. PE V.19-36 (Dindorf I, p. 241-269)",
                "amand_passage_key_antifatalist": "Eus. PE VI.7.1-42 (Dindorf I, p. 291-299)",
                "amand_classification": "carneadean_adaptation_libre_cynique_paganisme_2c",
                "title_alternative_amand": "Antiperiades (variante mentionnée par Amand)",
                "editions": [
                    {"raw": "P. Vallette, De Oenomao Cynico (Klincksieck 1908) — édition critique avec traduction latine"},
                    {"raw": "W. Dindorf, Eusebii Praeparatio Evangelica I (Teubner 1867)"},
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_diogenes_oinoanda_inscription",
        type="work",
        label="Diogénès d'Oinoanda, Inscription philosophique",
        description=(
            "Immense inscription philosophique épicurienne gravée sur le mur "
            "d'un portique d'Oinoanda en Lycie, vers 200 CE, par le philosophe "
            "âgé Diogénès. Pour Amand 1945 (Livre I Ch. III Note suppl. §II, "
            "p. 117-120), l'inscription se compose d'un préambule sur la "
            "mission philanthropique de l'auteur, d'une esquisse de la physique "
            "épicurienne, d'une lettre à Antipatros sur l'infinité des mondes, "
            "d'un exposé d'éthique avec choix de sentences du Maître, de "
            "lettres à sa mère et à ses amis, d'une copie de son testament, et "
            "d'un opuscule défendant la vieillesse. Au fragment XXXIII (éd. "
            "William 1907) — préservé seulement en début et fin avec énorme "
            "lacune au milieu — Diogénès démontre la non-existence de "
            "l'εἱμαρμένη : si les arguments en faveur de la mantique sont "
            "inefficaces (préalablement démontré au fragment XXXI), il n'y a "
            "plus d'autre preuve pour l'εἱμαρμένη. Et de plus : 'si l'on croit "
            "à l'εἱμαρμένη, tout avertissement devient inutile, tout blâme "
            "superflu, et il n'est plus même permis de punir les criminels' "
            "(fragment XXXIII col. 1-3) — argument moral antifataliste type, "
            "venu peut-être d'Épicure (cf. fragment 378 Usener) plutôt que de "
            "Carnéade directement"
        ),
        description_en=(
            "Vast Epicurean philosophical inscription carved on the wall of a "
            "portico at Oinoanda in Lycia, c. 200 CE, by the elderly Diogenes. "
            "For Amand 1945 (Book I Ch. III Suppl. Note §II, p. 117-120), the "
            "inscription comprises a preamble on the author's philanthropic "
            "mission, a sketch of Epicurean physics, a letter to Antipater on "
            "the infinity of worlds, an ethical exposition with selected "
            "Master's sentences, letters to his mother and friends, a copy of "
            "his testament, and an opusculum defending old age. At fragment "
            "XXXIII (ed. William 1907) — preserved only at start and end with "
            "a huge lacuna in the middle — Diogenes demonstrates the "
            "non-existence of εἱμαρμένη: if the arguments for divination are "
            "ineffective (previously shown at fragment XXXI), no further proof "
            "remains for εἱμαρμένη. And moreover: 'if one believes in "
            "εἱμαρμένη, all warning becomes useless, all blame superfluous, "
            "and it is no longer even permitted to punish criminals' (fragment "
            "XXXIII col. 1-3) — a typical antifatalist moral argument, "
            "perhaps from Epicurus himself (cf. fragment 378 Usener) rather "
            "than from Carneades directly"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 117-120",
            md_line_range="ll. 6845-6975",
            chapter="Livre I Ch. III Note suppl. §II (Diogénès d'Oinoanda)",
            amand_chapter_actual="Inscription d'Oinoanda — Diogénès",
            extra={
                "amand_passage_key": "fragm. XXXIII (ed. William 1907, p. 40-42)",
                "amand_classification": "epicurean_antifatalist_inscription_2c_3c",
                "editions": [
                    {"raw": "I. William, Diogenis Oinoandensis fragmenta (Teubner 1907) — édition de référence Amand"},
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_diogenianus_peri_heimarmenes",
        type="work",
        label="Diogénianos, Περὶ εἱμαρμένης",
        description=(
            "Περὶ εἱμαρμένης de Diogénianos l'Épicurien, traité perdu en "
            "intégralité mais conservé en plusieurs longs fragments par Eusèbe "
            "de Césarée dans la Préparation évangélique IV.3.1-13 et VI.8.1-38. "
            "Pour Amand 1945 (Livre I Ch. III Note suppl. §III, p. 120-126), "
            "Eusèbe les a recueillis avec empressement comme confirmation païenne "
            "de sa propre réfutation de la divination oraculaire et du "
            "fatalisme. Trois fragments majeurs : (1) PE IV.3.1-13 — vanité et "
            "inutilité de la divination ; (2) PE VI.8.1-7 — Homère réfute "
            "Chrysippe ; (3) PE VI.8.8-24 — réfutation des étymologies "
            "chrysippiennes ; (4) PE VI.8.25-38 — réfutation de la conciliation "
            "chrysippienne entre εἱμαρμένη et liberté via les confatalia. "
            "Gercke 1885 a édité l'ensemble (frag. I-IV, p. 748-755). Pour "
            "Amand, ces fragments révèlent une dépendance très nette à l'égard "
            "de la polémique antifataliste de Carnéade ; ils mériteraient "
            "comparaison spécifique avec les textes parallèles du De divinatione "
            "de Cicéron"
        ),
        description_en=(
            "Περὶ εἱμαρμένης by Diogenianus the Epicurean, a treatise lost in "
            "its entirety but preserved in several long fragments by Eusebius "
            "of Caesarea in Praeparatio Evangelica IV.3.1-13 and VI.8.1-38. "
            "For Amand 1945 (Book I Ch. III Suppl. Note §III, p. 120-126), "
            "Eusebius collected them eagerly as a pagan confirmation of his "
            "own refutation of oracular divination and fatalism. Four major "
            "fragments: (1) PE IV.3.1-13 — vanity and uselessness of "
            "divination; (2) PE VI.8.1-7 — Homer refutes Chrysippus; (3) PE "
            "VI.8.8-24 — refutation of Chrysippus's etymologies; (4) PE "
            "VI.8.25-38 — refutation of the Chrysippan reconciliation between "
            "εἱμαρμένη and freedom via the confatalia. Gercke 1885 edited the "
            "ensemble (frag. I-IV, p. 748-755). For Amand, these fragments "
            "reveal very clear dependence on Carneades's antifatalist polemic; "
            "they would deserve specific comparison with the parallel texts of "
            "Cicero's De divinatione"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 120-126",
            md_line_range="ll. 6975-7278",
            chapter="Livre I Ch. III Note suppl. §III (Diogénianos)",
            amand_chapter_actual="Diogénianos — Peri heimarmenes",
            extra={
                "amand_passage_key_divination": "Eus. PE IV.3.1-13 (Dindorf I, p. 162-165)",
                "amand_passage_key_etymologies": "Eus. PE VI.8.1-24 (Dindorf I, p. 300-304)",
                "amand_passage_key_confatalia": "Eus. PE VI.8.25-38 (Dindorf I, p. 304-307)",
                "amand_classification": "epicurean_antifatalist_treatise_carneadean_dependence",
                "editions": [
                    {"raw": "W. Dindorf, Eusebii Praeparatio Evangelica I (Teubner 1867)"},
                    {"raw": "A. Gercke, Chrysippea, Jahrbücher klass. Philol. Suppl. 14 (1885), p. 748-755"},
                    {"raw": "H. von Arnim, SVF II.914 (étymologies), 998-999 (confatalia)"},
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_hierocles_peri_pronoias",
        type="work",
        label="Hiéroclès d'Alexandrie, Περὶ προνοίας καὶ εἱμαρμένης",
        description=(
            "Περὶ προνοίας καὶ εἱμαρμένης καὶ τῆς τοῦ ἐφ' ἡμῖν πρὸς τὴν θείαν "
            "ἡγεμονίαν συντάξεως — grand traité néoplatonicien en sept livres "
            "d'Hiéroclès d'Alexandrie (composé peu après 412 CE). Perdu en "
            "intégralité, mais Photius (Bibliothèque cod. 214 et surtout cod. "
            "251) en a consigné une analyse détaillée et en a transcrit "
            "d'abondants extraits (= PG 103, 701A-708B + PG 104, 76A-96D). "
            "Pour Amand 1945 (Livre I Ch. VI §II.5, p. 173-176), ce traité "
            "présente une bizarre utilisation de l'argumentation morale de "
            "Carnéade : Hiéroclès s'en sert non pas pour réfuter mais pour "
            "prouver l'existence de la Providence et de l'εἱμαρμένη — au sens "
            "précis et nouveau qu'il lui donne. L'extrait clé est Livre III "
            "ch. 10 (Photius cod. 251, p. 465 a 13-31 Bekker = PG 104, 92AC) : "
            "'Les lois (νόμοι), les raisonnements (λογισμός), les vertus et les "
            "faits analogues postulent la Providence... C'est précisément "
            "l'εἱμαρμένη providentielle qui fait l'éducation de notre liberté "
            "(τὸ ἐφ' ἡμῖν παιδεύουσα) par des maux qui échappent à notre "
            "pouvoir.' Le caractère nécessaire et fatal de l'εἱμαρμένη "
            "(ἀνάγκη qui choquait les chrétiens) est remplacé par un concept "
            "personnel et moral — celui du gouvernement divin qui punit et "
            "éduque les âmes (κρίσις θεία οὖσα ἐν τοῖς οὐκ ἐφ' ἡμῖν πρὸς τὴν "
            "ἀξίαν ἀμοιβὴν τῶν ἐφ' ἡμῖν, Photius p. 465 b 33-38)"
        ),
        description_en=(
            "Περὶ προνοίας καὶ εἱμαρμένης καὶ τῆς τοῦ ἐφ' ἡμῖν πρὸς τὴν θείαν "
            "ἡγεμονίαν συντάξεως — major Neoplatonic treatise in seven books "
            "by Hierocles of Alexandria (composed shortly after 412 CE). "
            "Entirely lost, but Photius (Bibliotheca cod. 214 and especially "
            "cod. 251) recorded a detailed analysis and transcribed abundant "
            "extracts (= PG 103, 701A-708B + PG 104, 76A-96D). For Amand 1945 "
            "(Book I Ch. VI §II.5, p. 173-176), this treatise presents a "
            "bizarre use of Carneades's moral argument: Hierocles uses it not "
            "to refute but to prove the existence of Providence and εἱμαρμένη "
            "— in the precise and new sense he gives them. The key extract is "
            "Book III ch. 10 (Photius cod. 251, p. 465 a 13-31 Bekker = PG "
            "104, 92AC): 'Laws (νόμοι), reasonings (λογισμός), virtues and "
            "analogous facts postulate Providence... It is precisely the "
            "providential εἱμαρμένη that educates our freedom (τὸ ἐφ' ἡμῖν "
            "παιδεύουσα) through evils that escape our power.' The necessary "
            "fatal character of εἱμαρμένη (ἀνάγκη that shocked Christians) is "
            "replaced by a personal and moral concept — the divine government "
            "that punishes and educates souls (κρίσις θεία οὖσα ἐν τοῖς οὐκ "
            "ἐφ' ἡμῖν πρὸς τὴν ἀξίαν ἀμοιβὴν τῶν ἐφ' ἡμῖν, Photius p. 465 b "
            "33-38)"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 173-176",
            md_line_range="ll. 9924-10138",
            chapter="Livre I Ch. VI §II.5 (Hiéroclès — Peri pronoias)",
            amand_chapter_actual="Hiéroclès d'Alexandrie — Peri pronoias kai heimarmenes",
            extra={
                "amand_passage_key": "Photius cod. 251 p. 465 a 13-31 Bekker (= PG 104, 92AC)",
                "amand_classification": "anomalous_carneadean_use_providential",
                "principal_attestation": "Photius Bibl. cod. 214 + cod. 251 (PG 103-104)",
                "editions": [
                    {"raw": "I. Bekker, Photius Bibliotheca (Berlin 1824)"},
                    {"raw": "Migne PG 103, 701A-708B + PG 104, 76A-96D"},
                    {"raw": "F. W. A. Mullach, Hierocles. In aureum Pythagoreorum carmen commentarius (Berlin 1853)"},
                ],
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# CONCEPTS (2)
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    _node(
        id="concept_heimarmene_astrologica_amand",
        type="concept",
        label="εἱμαρμένη astrologique (Empire romain)",
        description=(
            "Concept-cadre, distillé par Amand 1945 (Introduction §I.VI, p. "
            "14-16) à partir des Astronomiques de Manilius, des Anthologies de "
            "Vettius Valens et du témoignage de Sénèque : sous l'Empire romain, "
            "l'εἱμαρμένη astrologique s'identifie désormais aux révolutions "
            "planétaires et à la domination des astres sur le monde sublunaire. "
            "Dieu et les divinités secondaires sont pratiquement exclus ; le "
            "gouvernement de l'univers est confié aux planètes omnipotentes. "
            "L'εἱμαρμένη astrologique n'a plus rien d'un être personnel ou "
            "d'une fiction mythologique — elle est la loi naturelle selon "
            "laquelle la συμπάθεια τῶν ὅλων (Posidonios) met en connexion "
            "intime mouvements astraux et événements terrestres. À l'instant "
            "précis où le nouveau-né voit la lumière, sa constellation lui fixe "
            "irrévocablement son destin (genesis, generaire). Cette doctrine "
            "fut popularisée par les rhéteurs (Manilius Astronomiques IV.14 : "
            "Fata regunt orbem, certa stant omnia lege), les compilations "
            "techniques (Vettius Valens), et surtout par le prosélytisme des "
            "cultes orientaux à mystères qui submergèrent l'Empire au IIe-IIIe "
            "siècle"
        ),
        description_en=(
            "Frame-concept, distilled by Amand 1945 (Introduction §I.VI, p. "
            "14-16) from Manilius's Astronomica, Vettius Valens's Anthologies "
            "and Seneca's testimony: under the Roman Empire, astrological "
            "εἱμαρμένη is now identified with planetary revolutions and the "
            "stars' domination over the sublunar world. God and secondary "
            "deities are practically excluded; the government of the universe "
            "is entrusted to the omnipotent planets. Astrological εἱμαρμένη "
            "is no longer a personal being or mythological fiction — it is "
            "the natural law by which the συμπάθεια τῶν ὅλων (Posidonius) "
            "intimately connects astral motions and terrestrial events. At "
            "the precise instant of birth, the constellation irrevocably fixes "
            "the newborn's destiny (genesis, generaire). This doctrine was "
            "popularised by the rhetors (Manilius Astronomica IV.14: Fata "
            "regunt orbem, certa stant omnia lege), technical compilations "
            "(Vettius Valens), and especially by the proselytism of Oriental "
            "mystery cults that flooded the Empire in the 2nd-3rd centuries"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 14-16",
            md_line_range="ll. 2111-2212",
            chapter="Introduction §I.VI (Le fatalisme astrologique sous l'Empire)",
            amand_chapter_actual="Introduction §I.VI",
            extra={
                "amand_concept_role": "frame_concept_carneadean_target",
                "alternative_names": [
                    "Astrological Heimarmene under the Empire",
                    "εἱμαρμένη astrologique impériale",
                ],
                "key_primary_sources_via_amand": [
                    "Manilius, Astronomiques IV.12-22, IV.108-118 (ed. Van Wageningen, Teubner 1915)",
                    "Vettius Valens, Anthologiae V.9, IX.11 (ed. Kroll)",
                    "Seneca, lettres et De providentia",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="concept_plotinian_intellectual_eph_hemin",
        type="concept",
        label="τὸ ἐφ' ἡμῖν intellectuel (conception plotinienne)",
        description=(
            "Conception spécifiquement plotinienne du τὸ ἐφ' ἡμῖν, distillée "
            "par Amand 1945 (Livre I Ch. VI §I.3, p. 162-163) à partir des "
            "Ennéades VI.8 (notamment ch. 2, 6, 8) et II.3.9. La liberté ne "
            "réside ni dans l'alternative entre actions ni dans l'extension "
            "des choix concrets, mais exclusivement dans l'intention honnête, "
            "dans la vertu comme disposition intérieure, dans l'intelligence "
            "affranchie de l'action et conformée au Bien. 'Il reste ce que "
            "nous sommes en toute vérité, ce moi à qui il a été donné par la "
            "nature de dominer les passions. Au milieu de tous les maux qui "
            "nous sont infligés par le corps, Dieu nous a donné la vertu, et "
            "la vertu n'a pas de maître' (Enn. II.3.9, ἀδέσποτον ἀρετὴν θεὸς "
            "ἔδωκεν). Seules la vertu et l'intelligence sont souveraines ; "
            "tout le reste relève de la nécessité cosmique. Pour Amand, c'est "
            "précisément cette restriction du τὸ ἐφ' ἡμῖν à une spontanéité "
            "intellectuelle qui explique l'omission systématique chez Plotin "
            "et ses successeurs (Porphyre, Jamblique, Proclus) des topoi "
            "antifatalistes de Carnéade — lesquels supposent au contraire "
            "une extension large du libre arbitre aux actions concrètes"
        ),
        description_en=(
            "Specifically Plotinian conception of τὸ ἐφ' ἡμῖν, distilled by "
            "Amand 1945 (Book I Ch. VI §I.3, p. 162-163) from Enneads VI.8 "
            "(notably ch. 2, 6, 8) and II.3.9. Freedom resides neither in "
            "alternative possibilities between actions nor in the extension "
            "of concrete choices, but exclusively in honest intention, in "
            "virtue as inner disposition, in intelligence freed from action "
            "and conformed to the Good. 'There remains what we truly are, "
            "this self to which nature has given the power to dominate the "
            "passions. Amid all the evils inflicted on us by the body, God "
            "has given us virtue, and virtue has no master' (Enn. II.3.9, "
            "ἀδέσποτον ἀρετὴν θεὸς ἔδωκεν). Only virtue and intelligence are "
            "sovereign; all the rest pertains to cosmic necessity. For Amand, "
            "it is precisely this restriction of τὸ ἐφ' ἡμῖν to an "
            "intellectual spontaneity that explains the systematic omission "
            "by Plotinus and his successors (Porphyry, Iamblichus, Proclus) "
            "of Carneades's antifatalist topoi — which on the contrary "
            "presuppose a broad extension of free will to concrete actions"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 162-163",
            md_line_range="ll. 9519-9546",
            chapter="Livre I Ch. VI §I.3",
            amand_chapter_actual="Plotin — restriction du τὸ ἐφ' ἡμῖν",
            extra={
                "amand_concept_role": "explains_omission_carneadean_neoplatonism",
                "alternative_names": [
                    "Plotinian Intellectual eph hēmin",
                    "to eph hēmin intellectuel plotinien",
                ],
                "key_primary_sources_via_amand": [
                    "Plotinus, Enn. VI.8.2, 6, 8 (Bréhier ed.)",
                    "Plotinus, Enn. II.3.9 (Bréhier II, p. 35)",
                    "Plotinus, Enn. III.1.8-9 (Bréhier III, p. 13-16)",
                ],
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# SYNTHESES (15)
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    # ---- Intro §I (8 syntheses) ----
    _node(
        id="synthesis_amand1945_intro_chaldean_origin_fatalism",
        type="synthesis",
        label="Origine chaldéenne du fatalisme astral (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Introduction §I.I, p. 1-2) : la découverte "
            "capitale des astronomes sacerdotaux de Babylonie — la constance "
            "immuable des révolutions sidérales et la périodicité permettant "
            "de prédire les phénomènes astronomiques — conduisit naturellement "
            "à la notion d'une Nécessité, soit conçue comme résultant de la "
            "volonté des dieux, soit comme supérieure à celle-ci. C'est en "
            "Chaldée que naquit l'idée d'une Fatalité liée aux mouvements "
            "réguliers du soleil, de la lune et des planètes distribuant aux "
            "hommes bienfaits et maux. Le déterminisme babylonien initial ne "
            "fut pas poussé à ses ultimes conséquences (prêtres maintenaient "
            "la possibilité d'éloigner les maux par purifications, sacrifices, "
            "incantations). À l'époque alexandrine, certaines écoles de prêtres "
            "astronomes, sous l'influence du stoïcisme, professèrent une "
            "doctrine plus rigoureuse : la Fatalité gouverne Dieu lui-même et "
            "produit par l'intermédiaire des astres tous les phénomènes "
            "physiques, intellectuels et moraux (Strabon Géogr. XVI.1.6 ; "
            "Pline HN VI.26.123 ; Bidez 1935)"
        ),
        description_en=(
            "Thesis of Amand 1945 (Introduction §I.I, p. 1-2): the major "
            "discovery of the sacerdotal astronomers of Babylonia — the "
            "immutable constancy of sidereal revolutions and the periodicity "
            "allowing prediction of astronomical phenomena — naturally led to "
            "the notion of a Necessity, conceived either as resulting from "
            "the gods' will or as superior to it. It is in Chaldea that the "
            "idea was born of a Fatality linked to the regular motions of "
            "sun, moon and planets distributing to men benefits and ills. The "
            "initial Babylonian determinism was not pressed to its ultimate "
            "consequences (priests maintained the possibility of warding off "
            "evils through purifications, sacrifices, incantations). In the "
            "Alexandrian period, certain schools of priestly astronomers, "
            "under Stoic influence, professed a stricter doctrine: Fatality "
            "governs God himself and produces through the stars all physical, "
            "intellectual and moral phenomena (Strabo Geog. XVI.1.6; Pliny HN "
            "VI.26.123; Bidez 1935)"
        ),
        period="Cross-period",
        metadata=amand_metadata(
            page_range="p. 1-2",
            md_line_range="ll. 1489-1538",
            chapter="Introduction §I.I (Les Babyloniens)",
            amand_chapter_actual="Introduction §I.I",
            extra={"amand_thesis_type": "historical_origin"},
        ),
        confidence=0.85,
    ),
    _node(
        id="synthesis_amand1945_intro_presocratics_create_heimarmene_concept",
        type="synthesis",
        label="Les Pré-Socratiques créateurs du concept d'εἱμαρμένη (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Introduction §I.II, p. 2-4) : les notions "
            "philosophiques corrélatives d'εἱμαρμένη et d'ἀνάγκη ne sont "
            "nullement étrangères aux Pré-Socratiques — ce sont eux qui les "
            "ont créées et qui se sont efforcés d'en élaborer une analyse "
            "rationnelle. Héraclite, le premier parmi les Grecs, approfondit "
            "l'idée d'εἱμαρμένη — soit principe positif du devenir, loi "
            "cosmique, force immanente agissant mécaniquement, soit λόγος "
            "divin plus ou moins personnel. Parménide attribue à ᾿Ανάγκη "
            "(déesse de la mort, du Destin) le gouvernement du monde et les "
            "révolutions sidérales. Les Atomistes Leucippe et Démocrite "
            "rompent avec la représentation mythologique : leur ἀνάγκη est "
            "force naturelle mécanique entraînant les atomes ; ils défendent "
            "néanmoins la responsabilité humaine et la mantique. Pythagore et "
            "Empédocle redoutent ᾿Ανάγκη comme déesse maléfique enfermant les "
            "âmes dans le cycle des renaissances orphiques. Cette élaboration "
            "rationnelle pré-socratique exerce une profonde influence "
            "jusqu'à la fin de l'antiquité (Gundel Beiträge p. 9-27, 42-58)"
        ),
        description_en=(
            "Thesis of Amand 1945 (Introduction §I.II, p. 2-4): the "
            "philosophical correlative notions of εἱμαρμένη and ἀνάγκη are "
            "by no means foreign to the Pre-Socratics — it is they who "
            "created them and strove to elaborate a rational analysis. "
            "Heraclitus, the first among the Greeks, deepened the idea of "
            "εἱμαρμένη — either positive principle of becoming, cosmic law, "
            "immanent force acting mechanically, or divine λόγος more or "
            "less personal. Parmenides attributes to ᾿Ανάγκη (goddess of "
            "death, of Destiny) the government of the world and the sidereal "
            "revolutions. The Atomists Leucippus and Democritus break with "
            "the mythological representation: their ἀνάγκη is a mechanical "
            "natural force driving the atoms; they nevertheless defend human "
            "responsibility and divination. Pythagoras and Empedocles dread "
            "᾿Ανάγκη as the maleficent goddess imprisoning souls in the cycle "
            "of Orphic rebirths. This Pre-Socratic rational elaboration "
            "exercises profound influence until the end of antiquity (Gundel "
            "Beiträge p. 9-27, 42-58)"
        ),
        period="Cross-period",
        metadata=amand_metadata(
            page_range="p. 2-4",
            md_line_range="ll. 1539-1636",
            chapter="Introduction §I.II (Les philosophes pré-socratiques)",
            amand_chapter_actual="Introduction §I.II",
            extra={"amand_thesis_type": "conceptual_genealogy"},
        ),
        confidence=0.85,
    ),
    _node(
        id="synthesis_amand1945_intro_plato_aristotle_partial_determinism",
        type="synthesis",
        label="Platon et Aristote : déterminismes partiels (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Introduction §I.III, p. 4-6) : Platon imprime "
            "à sa pensée une nette empreinte déterministe qui n'est pourtant "
            "pas exclusive de la liberté. Les concepts d'εἱμαρμένη et d'ἀνάγκη "
            "y reçoivent des significations multiples — événements extérieurs "
            "constituant le cadre d'une vie, loi morale réglant les "
            "réincarnations, principe mauvais immanent au cosmos, ensemble des "
            "lois invariables. Tantôt l'ἀνάγκη est déesse trônant au-dessus de "
            "l'univers, tantôt elle s'identifie à la φύσις. Le mythe d'Er "
            "(Rép. X, 617e) — αἰτία ἑλομένου· θεὸς ἀναίτιος — illustre l'effort "
            "platonicien pour sauvegarder la liberté humaine et la vertu au "
            "sein d'un déterminisme rigoureux. Aristote, au contraire, "
            "reconnaît le déterminisme physique mais repousse tout déterminisme "
            "psychologique : l'εἱμαρμένη y est réduite à la disposition "
            "naturelle organique d'un corps doué d'hérédité, et dans son "
            "domaine strictement limité la liberté du vouloir est pleine et "
            "totale. La nécessité absolue ne règne que dans la sphère de "
            "l'être et de l'immuable"
        ),
        description_en=(
            "Thesis of Amand 1945 (Introduction §I.III, p. 4-6): Plato "
            "imprints on his thought a marked deterministic stamp that is "
            "however not exclusive of freedom. The concepts of εἱμαρμένη and "
            "ἀνάγκη there receive multiple meanings — external events "
            "constituting the framework of a life, moral law regulating "
            "reincarnations, evil principle immanent to the cosmos, set of "
            "invariable laws. Sometimes ἀνάγκη is a goddess enthroned above "
            "the universe, sometimes she is identified with φύσις. The myth "
            "of Er (Rep. X, 617e) — αἰτία ἑλομένου· θεὸς ἀναίτιος — "
            "illustrates the Platonic effort to safeguard human freedom and "
            "virtue within a strict determinism. Aristotle, on the contrary, "
            "recognises physical determinism but rejects all psychological "
            "determinism: εἱμαρμένη is there reduced to the natural organic "
            "disposition of a body endowed with heredity, and in its strictly "
            "limited domain the freedom of the will is full and total. "
            "Absolute necessity reigns only in the sphere of being and the "
            "immutable"
        ),
        period="Classical Greek",
        metadata=amand_metadata(
            page_range="p. 4-6",
            md_line_range="ll. 1637-1741",
            chapter="Introduction §I.III (Platon, Aristote)",
            amand_chapter_actual="Introduction §I.III",
            extra={"amand_thesis_type": "classical_partial_determinism"},
        ),
        confidence=0.85,
    ),
    _node(
        id="synthesis_amand1945_intro_stoic_integral_fatalism",
        type="synthesis",
        label="Fatalisme intégral stoïcien (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Introduction §I.IV, p. 6-13) : ce furent les "
            "Stoïciens qui, élargissant les vues d'Héraclite sur l'εἱμαρμένη, "
            "firent du déterminisme une doctrine capitale et élevèrent "
            "l'εἱμαρμένη à la hauteur d'un concept central analogue à ceux de "
            "Dieu, de Nature et de Providence. Zénon enseigne l'enchaînement "
            "ininterrompu des causes avec nécessité absolue ; il compare la "
            "coaction du Destin à la violence subie par un chien attaché à "
            "une voiture, qu'il suit de bon gré ou est traîné de force. "
            "Cléanthe voit dans les astres les interprètes du plan cosmique "
            "divin (frayant la voie au fatalisme astral). Chrysippe, second "
            "fondateur du Portique, pousse jusqu'aux conséquences extrêmes — "
            "l'εἱμαρμένη est la liaison infrangible et éternelle des causes ; "
            "même la volonté des dieux y est soumise. Ses subtiles distinctions "
            "(causes parfaites/principales vs adjuvantes/prochaines, cylindre, "
            "confatalia) ne préservent en fait qu'une simple spontanéité "
            "psychologique sans autonomie véritable. Le τὸ ἐφ' ἡμῖν chrysippien "
            "se réduit à une demi-liberté. Posidonios élève la sympatheia "
            "universelle au rang de concept scientifique et l'astrologie au "
            "rang de connaissance concrète de l'εἱμαρμένη — tout en maintenant "
            "(comme Panétios) l'αὐτεξούσιον"
        ),
        description_en=(
            "Thesis of Amand 1945 (Introduction §I.IV, p. 6-13): it was the "
            "Stoics who, expanding Heraclitus's views on εἱμαρμένη, made "
            "determinism a capital doctrine and elevated εἱμαρμένη to a "
            "central concept analogous to those of God, Nature and "
            "Providence. Zeno teaches the uninterrupted chaining of causes "
            "with absolute necessity; he compares Fate's coaction to the "
            "violence suffered by a dog tied to a cart, which it follows "
            "willingly or is dragged by force. Cleanthes sees in the stars "
            "the interpreters of the divine cosmic plan (paving the way for "
            "astral fatalism). Chrysippus, second founder of the Stoa, "
            "pushes to extreme consequences — εἱμαρμένη is the indissoluble "
            "and eternal binding of causes; even the gods' will is subject "
            "to it. His subtle distinctions (perfect/principal vs auxiliary/"
            "proximate causes, cylinder, confatalia) in fact preserve only a "
            "simple psychological spontaneity without true autonomy. The "
            "Chrysippan τὸ ἐφ' ἡμῖν is reduced to a half-freedom. Posidonius "
            "elevates universal sympatheia to a scientific concept and "
            "astrology to a concrete knowledge of εἱμαρμένη — while "
            "maintaining (like Panaetius) the αὐτεξούσιον"
        ),
        period="Hellenistic",
        metadata=amand_metadata(
            page_range="p. 6-13",
            md_line_range="ll. 1742-2089",
            chapter="Introduction §I.IV (Les Stoïciens : Zénon, Cléanthe, Chrysippe, Posidonios)",
            amand_chapter_actual="Introduction §I.IV",
            extra={"amand_thesis_type": "stoic_integral_fatalism_genealogy"},
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_amand1945_intro_hellenistic_astrological_diffusion",
        type="synthesis",
        label="Diffusion hellénistique du fatalisme astrologique (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Introduction §I.V, p. 13-14) : à l'époque "
            "hellénistique, le fatalisme — ou plus exactement la mentalité "
            "fataliste — s'imposa peu à peu aux religions de tous les peuples "
            "méditerranéens. Sa forme astrologique pénétra le paganisme "
            "sémitique : culte de la Τύχη, du Temps divinisé (zervanisme) en "
            "Syrie ; théologie solaire syrienne assimilant tous les Baals au "
            "Soleil moteur. Le judaïsme post-exilien lui-même fut tenté : "
            "Esséniens admettant la Fatalité, Sadducéens la rejetant, "
            "Pharisiens à mi-chemin (Josèphe AJ XIII.172, XVIII.13 ; BJ "
            "II.16.3-5). En Égypte, l'astrologie babylonienne fataliste "
            "s'introduisit à l'époque perse et sous les Lagides prit un "
            "développement original — grands zodiaques décorant les temples, "
            "imposante Somme astrologique de Néchepso et Pétosiris composée à "
            "Alexandrie vers 150 av. J.-C. Pour Amand, c'est le contact des "
            "Séleucides qui forgea la synthèse entre stoïcisme hellénique et "
            "théologie chaldéenne — Cumont (cit. p. 13) : 'en certains cas, le "
            "stoïcisme fut une philosophie sémitique'"
        ),
        description_en=(
            "Thesis of Amand 1945 (Introduction §I.V, p. 13-14): in the "
            "Hellenistic period, fatalism — or more accurately the fatalist "
            "mentality — gradually imposed itself on the religions of all "
            "Mediterranean peoples. Its astrological form penetrated Semitic "
            "paganism: cult of Τύχη, of divinized Time (Zervanism) in Syria; "
            "Syrian solar theology assimilating all Baals to the Sun as "
            "mover. Post-exilic Judaism itself was tempted: Essenes admitting "
            "Fatality, Sadducees rejecting it, Pharisees halfway (Josephus AJ "
            "XIII.172, XVIII.13; BJ II.16.3-5). In Egypt, Babylonian "
            "fatalist astrology was introduced under the Persians and under "
            "the Lagids took an original development — great zodiacs "
            "decorating temples, imposing astrological Summa by Nechepso and "
            "Petosiris composed at Alexandria c. 150 BCE. For Amand, contact "
            "with the Seleucids forged the synthesis between Hellenic "
            "Stoicism and Chaldean theology — Cumont (cited p. 13): 'in "
            "certain cases, Stoicism was a Semitic philosophy'"
        ),
        period="Hellenistic",
        metadata=amand_metadata(
            page_range="p. 13-14",
            md_line_range="ll. 2074-2110",
            chapter="Introduction §I.V (Le fatalisme astrologique à l'époque hellénistique)",
            amand_chapter_actual="Introduction §I.V",
            extra={"amand_thesis_type": "hellenistic_diffusion"},
        ),
        confidence=0.85,
    ),
    _node(
        id="synthesis_amand1945_intro_astrologers_pragmatic_responses",
        type="synthesis",
        label="Réponses pragmatiques des astrologues à Carnéade (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Introduction §I.VII, p. 16-18) : devant "
            "l'argumentation morale antifataliste de Carnéade qui leur fut "
            "opposée pendant des siècles par néo-académiciens, péripatéticiens, "
            "épicuriens, sceptiques, cyniques puis théologiens chrétiens, les "
            "astrologues développèrent des réponses pragmatiques transigeant "
            "aux dépens de la logique sans désavouer leurs doctrines. Trois "
            "stratégies principales : (1) Manilius (Astr. IV.108-118) "
            "empoigne le taureau par les cornes — peu importe l'origine du "
            "crime, il faut convenir que c'est un crime, et expier sa "
            "destinée elle-même cela aussi est fatal ; (2) Ptolémée "
            "(Tétrabible I.3.4-12) distingue εἱμαρμένη θεία (éternelle, "
            "invariable, mouvement des astres) et εἱμαρμένη φυσική (sublunaire, "
            "soumise au changement, partiellement modifiable par les forces "
            "intercurrentes que l'homme peut faire fonctionner) ; (3) "
            "Ptolémée et Vettius Valens développent l'idée d'ἀπάθεια "
            "(impassibilité, paix de l'âme) comme fruit spirituel de la "
            "prévision astrologique. Pour Amand, ces tactiques ne résolvent "
            "pas vraiment la difficulté"
        ),
        description_en=(
            "Thesis of Amand 1945 (Introduction §I.VII, p. 16-18): facing "
            "Carneades's antifatalist moral argumentation opposed to them for "
            "centuries by Neo-Academics, Peripatetics, Epicureans, Sceptics, "
            "Cynics and then Christian theologians, the astrologers developed "
            "pragmatic responses compromising on logic without disavowing "
            "their doctrines. Three main strategies: (1) Manilius (Astr. "
            "IV.108-118) takes the bull by the horns — no matter the origin "
            "of the crime, one must agree it is a crime, and to expiate one's "
            "destiny is itself fated; (2) Ptolemy (Tetrabiblos I.3.4-12) "
            "distinguishes εἱμαρμένη θεία (eternal, invariable, motion of "
            "the stars) and εἱμαρμένη φυσική (sublunar, subject to change, "
            "partially modifiable by intercurrent forces that humans can set "
            "in motion); (3) Ptolemy and Vettius Valens develop the idea of "
            "ἀπάθεια (impassibility, peace of soul) as the spiritual fruit "
            "of astrological foresight. For Amand, these tactics do not "
            "really resolve the difficulty"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 16-18",
            md_line_range="ll. 2213-2290",
            chapter="Introduction §I.VII (Réponses des astrologues)",
            amand_chapter_actual="Introduction §I.VII",
            extra={"amand_thesis_type": "astrologer_apologetic_strategies"},
        ),
        confidence=0.85,
    ),
    _node(
        id="synthesis_amand1945_intro_stoic_joyful_resignation",
        type="synthesis",
        label="Résignation joyeuse stoïcienne au Destin (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Introduction §I.VIII, p. 18-21) : tant que le "
            "stoïcisme fut debout, il prouva par le fait même de son existence "
            "que le fatalisme théorique n'est pas incompatible avec une vertu "
            "virile et agissante. De Cléanthe à Marc-Aurèle, le fatalisme "
            "professé par des âmes généreuses fortifia la conscience de la "
            "dépendance de l'homme à l'égard de la Cause toute-puissante. Les "
            "'soldats du Destin' (στρατιῶται τῆς εἱμαρμένης, Vettius Valens "
            "V.9) érigent en devoir la soumission absolue à l'irrésistible "
            "Destinée. Sénèque (De prov. 5.5-8 : Demetrius le Cynique ; De "
            "vita beata 15.5-7) et Marc-Aurèle (Pensées V.8.10, etc.) "
            "s'élèvent jusqu'à aimer leur destinée. Le sage devient maître de "
            "l'εἱμαρμένη en y consentant généreusement. Amand distingue "
            "soigneusement Épictète qui s'écarte de la résignation fataliste "
            "stoïcienne en accordant à l'homme une liberté absolue (note 2 "
            "p. 19-20). Pour Amand, cette piété stoïcienne tardive offre "
            "d'incontestables analogies de forme avec la prière chrétienne "
            "(Suscipe me d'Ignace de Loyola, Fiat voluntas tua) — mais "
            "l'objet diffère absolument : Destin impersonnel vs Dieu "
            "personnel et trinitaire"
        ),
        description_en=(
            "Thesis of Amand 1945 (Introduction §I.VIII, p. 18-21): as long "
            "as Stoicism stood, it proved by its very existence that "
            "theoretical fatalism is not incompatible with manly and active "
            "virtue. From Cleanthes to Marcus Aurelius, fatalism professed "
            "by generous souls strengthened the consciousness of man's "
            "dependence on the all-powerful Cause. The 'soldiers of Destiny' "
            "(στρατιῶται τῆς εἱμαρμένης, Vettius Valens V.9) erect as a duty "
            "absolute submission to irresistible Destiny. Seneca (De prov. "
            "5.5-8: Demetrius the Cynic; De vita beata 15.5-7) and Marcus "
            "Aurelius (Meditations V.8.10, etc.) rise to loving their fate. "
            "The sage becomes master of εἱμαρμένη by consenting to it "
            "generously. Amand carefully distinguishes Epictetus who departs "
            "from Stoic fatalist resignation by granting man absolute freedom "
            "(note 2 p. 19-20). For Amand, this late Stoic piety offers "
            "undeniable formal analogies with Christian prayer (Ignatius of "
            "Loyola's Suscipe me, Fiat voluntas tua) — but the object differs "
            "absolutely: impersonal Destiny vs personal trinitarian God"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 18-21",
            md_line_range="ll. 2291-2466",
            chapter="Introduction §I.VIII (La résignation au Destin)",
            amand_chapter_actual="Introduction §I.VIII",
            extra={"amand_thesis_type": "stoic_resignation_christian_analogy"},
        ),
        confidence=0.85,
    ),
    _node(
        id="synthesis_amand1945_intro_christian_baptismal_liberation",
        type="synthesis",
        label="Délivrance baptismale de l'εἱμαρμένη par le Christ (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Introduction §I.X, p. 25-28) : dans le "
            "cadre culturel gréco-latin, le christianisme des trois premiers "
            "siècles offre par certains traits des analogies avec les "
            "religions à mystères contemporaines. Les fidèles adorent en "
            "Jésus le Seigneur, Sauveur, Rédempteur, vrai triomphateur des "
            "astres et libérateur des puissances astrales démoniaques. Déjà "
            "Paul (Rom. 8.38-39 : οὔτε ἄγγελοι οὔτε ἀρχαί... οὔτε ὕψωμα οὔτε "
            "βάθος, lecture astrologique selon Lietzmann 1928) ; Gal. 4.3 "
            "(στοιχεῖα τοῦ κόσμου). Le Valentinien Théodotos (Excerpta ex "
            "Theodoto 69-78, ed. Casey 1934) expose avec énergie la conception "
            "du Christ Kyrios délivrant les croyants du joug de l'εἱμαρμένη "
            "sidérale. Amand y dégage quatre idées dominantes : (1) les "
            "chrétiens admettaient l'existence de l'εἱμαρμένη astrologique "
            "comme effective sur les non-baptisés ; (2) le baptême brise "
            "l'empire de cette εἱμαρμένη ; (3) γένεσις = εἱμαρμένη = "
            "résultante d'un conflit de Puissances astrales bienveillantes "
            "et hostiles ; (4) la connaissance (gnose) accompagne le bain. "
            "Pour Amand, ces extraits documentent l'influence profonde du "
            "cauchemar de l'εἱμαρμένη sur le christianisme primitif"
        ),
        description_en=(
            "Thesis of Amand 1945 (Introduction §I.X, p. 25-28): in the "
            "Greco-Latin cultural framework, the Christianity of the first "
            "three centuries presents in certain features analogies with "
            "contemporary mystery religions. The faithful adore in Jesus "
            "the Lord, Saviour, Redeemer, true conqueror of the stars and "
            "liberator from the demonic astral powers. Already Paul (Rom. "
            "8.38-39: οὔτε ἄγγελοι οὔτε ἀρχαί... οὔτε ὕψωμα οὔτε βάθος, "
            "astrological reading per Lietzmann 1928); Gal. 4.3 (στοιχεῖα τοῦ "
            "κόσμου). The Valentinian Theodotus (Excerpta ex Theodoto 69-78, "
            "ed. Casey 1934) energetically exposes the conception of Christ "
            "Kyrios delivering believers from the yoke of sidereal εἱμαρμένη. "
            "Amand extracts four dominant ideas: (1) Christians admitted the "
            "existence of astrological εἱμαρμένη as effective over the "
            "unbaptized; (2) baptism breaks the empire of this εἱμαρμένη; "
            "(3) γένεσις = εἱμαρμένη = resultant of a conflict of benevolent "
            "and hostile astral Powers; (4) knowledge (gnosis) accompanies "
            "the bath. For Amand, these extracts document the profound "
            "influence of the εἱμαρμένη nightmare on primitive Christianity"
        ),
        period="Patristic",
        metadata=amand_metadata(
            page_range="p. 25-28",
            md_line_range="ll. 2568-2788",
            chapter="Introduction §I.X (La foi au Christ Sauveur)",
            amand_chapter_actual="Introduction §I.X",
            extra={"amand_thesis_type": "christian_response_to_fatalism"},
        ),
        confidence=0.85,
    ),
    # ---- Lucien (2 syntheses) ----
    _node(
        id="synthesis_amand1945_lucian_sophist_satirist_carneadean_topos",
        type="synthesis",
        label="Lucien sophiste antifataliste — adaptation libre d'un topos carnéadien (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Livre I Ch. III §I+II, p. 107-115) : Lucien "
            "de Samosate, sophiste tardif sans opinion philosophique stable, "
            "réduit la philosophie à une morale terre à terre dépourvue de "
            "justification scientifique et adopte théoriquement un scepticisme "
            "mitigé. Mais cet impitoyable satirique a lancé des traits acérés "
            "contre la croyance fataliste si répandue de son époque, et a pris "
            "un malin plaisir à en montrer l'inanité. Il manie le topos "
            "antifataliste carnéadien sous trois formes : (1) trace marginale "
            "dans l'Apologie 8 — rejet du fatalisme comme excuse 'trop "
            "vulgaire' ; (2) écho narratif dans le 30e Dialogue des morts — "
            "Sostratos pousse Minos à reconnaître l'absurdité morale du "
            "fatalisme ; (3) déploiement systématique dans Zeus à court de "
            "raisons — Cyniscos accumule contre Zeus toutes les objections "
            "néo-académiciennes et épicuriennes contre l'εἱμαρμένη. Pour "
            "Amand, c'est dans Iuppiter confutatus que le topos est présenté "
            "de la manière la plus populaire et incisive. Notable absence : "
            "Lucien ne met nulle part en connexion sa critique du fatalisme "
            "vulgaire avec l'apotélesmatique proprement dite — son optique "
            "rétrospective et son peu de goût pour son époque l'empêchent "
            "d'être un observateur méthodique"
        ),
        description_en=(
            "Thesis of Amand 1945 (Book I Ch. III §I+II, p. 107-115): Lucian "
            "of Samosata, a late sophist without stable philosophical opinion, "
            "reduces philosophy to a down-to-earth morality without scientific "
            "justification and theoretically adopts mild scepticism. But this "
            "ruthless satirist has launched sharp shafts against the fatalist "
            "belief so widespread in his time, and has taken malicious "
            "pleasure in showing its emptiness. He handles the Carneadean "
            "antifatalist topos in three forms: (1) marginal trace in Apology "
            "8 — rejection of fatalism as 'too vulgar' excuse; (2) narrative "
            "echo in Dialogue of the Dead 30 — Sostratus forces Minos to "
            "acknowledge fatalism's moral absurdity; (3) systematic deployment "
            "in Zeus Confuted — Cyniscus piles up against Zeus all "
            "Neo-Academic and Epicurean objections against εἱμαρμένη. For "
            "Amand, it is in Iuppiter confutatus that the topos is presented "
            "most popularly and incisively. Notable absence: Lucian nowhere "
            "links his critique of vulgar fatalism with apotelesmatic "
            "astrology proper — his retrospective optic and lack of taste "
            "for his era prevent him from being a methodical observer"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 107-115",
            md_line_range="ll. 6445-6792",
            chapter="Livre I Ch. III",
            amand_chapter_actual="Lucien de Samosate — adaptation populaire",
            extra={"amand_thesis_type": "popular_carneadean_adaptation"},
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_amand1945_lucian_epicurean_2c_revival",
        type="synthesis",
        label="Renouveau épicurien au IIe siècle et lutte antifataliste (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Livre I Ch. III Note suppl. §I, p. 116-117) : "
            "c'est au IIe siècle de notre ère que la lutte contre la doctrine "
            "de l'εἱμαρμένη atteignit son plus haut point de violence dans les "
            "écoles philosophiques opposées au Portique. Le nouvel essor "
            "épicurien sous les Antonins s'explique comme la réaction "
            "naturelle du rationalisme aréligieux contre la foi de plus en "
            "plus envahissante aux révélations divines, à la magie, à "
            "l'astrologie et aux religions à mystères. Trois témoignages "
            "structurels : (1) Usener (Epicurea LXXXIV) : 'Permulti certe "
            "fuere multumque valuit disciplina (Epicureorum) sub Antoninis' "
            "— les Épicuriens étaient nombreux et influents ; (2) Amastris en "
            "Paphlagonie comme centre actif de propagande antireligieuse "
            "(Lépidus, amis d'Épicure, cf. Lucien Alex. 25, 43-44) ; (3) "
            "fondation à Athènes par Marc-Aurèle d'une chaire officielle "
            "d'épicurisme parmi les quatre écoles universitaires. Cette "
            "vitalité retrouvée explique que Diogénès d'Oinoanda et "
            "Diogénianos puissent transmettre l'argumentation antifataliste "
            "carnéadienne en mode épicurien"
        ),
        description_en=(
            "Thesis of Amand 1945 (Book I Ch. III Suppl. Note §I, p. "
            "116-117): it is in the 2nd century CE that the struggle against "
            "the doctrine of εἱμαρμένη reached its highest point of violence "
            "in the philosophical schools opposed to the Stoa. The new "
            "Epicurean upsurge under the Antonines is explained as the "
            "natural reaction of irreligious rationalism against the "
            "increasingly invasive faith in divine revelations, magic, "
            "astrology and mystery religions. Three structural testimonies: "
            "(1) Usener (Epicurea LXXXIV): 'Permulti certe fuere multumque "
            "valuit disciplina (Epicureorum) sub Antoninis' — the Epicureans "
            "were numerous and influential; (2) Amastris in Paphlagonia as an "
            "active centre of irreligious propaganda (Lepidus, friends of "
            "Epicurus, cf. Lucian Alex. 25, 43-44); (3) foundation at Athens "
            "by Marcus Aurelius of an official Epicurean chair among the four "
            "university schools. This renewed vitality explains why Diogenes "
            "of Oinoanda and Diogenianus can transmit Carneadean antifatalist "
            "argumentation in Epicurean mode"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 116-117",
            md_line_range="ll. 6794-6845",
            chapter="Livre I Ch. III Note suppl. §I (Renouveau épicurien)",
            amand_chapter_actual="Note suppl. — Renouveau épicurien 2C",
            extra={"amand_thesis_type": "epicurean_revival_explanation"},
        ),
        confidence=0.85,
    ),
    # ---- Oinomaos (2 syntheses) ----
    _node(
        id="synthesis_amand1945_oinomaos_cynic_carneadean_libre_adaptation",
        type="synthesis",
        label="Oinomaos cynique — libre adaptation du topos carnéadien (Amand 1945)",
        description=(
            "Thèse d'Amand 1945 (Livre I Ch. IV §II.3, p. 132-134) : dans "
            "sa polémique antifataliste contre Démocrite et Chrysippe (Γοήτων "
            "φώρα, conservé par Eusèbe PE VI.7.1-42), Oinomaos de Gadara ne "
            "produit aucun argument vraiment nouveau — il accommode à une "
            "sauce fort pimentée les lieux communs traditionnels depuis "
            "Carnéade. Tempérament impétueux mais esprit peu profond, "
            "Oinomaos sauvegarde la pleine liberté du vouloir comme donnée "
            "immédiate et incontestable de la conscience personnelle. Le "
            "passage caractéristique (PE VI.7.35-41 = Vallette p. 78-80) "
            "déploie l'idée centrale : dans l'hypothèse du fatalisme absolu, "
            "toute moralité est impossible, vertu et vice deviennent mots "
            "vides, l'homme est innocent quelque crime qu'il commette, et les "
            "dieux ne peuvent ni se fâcher ni punir. Les dieux eux-mêmes sont "
            "interpellés : 'Vous ne nous avez pas permis, ô dieux, de devenir "
            "vertueux !' Pour Amand, ce n'est pas un 'texte témoin' (le "
            "Cynique est trop libre et personnel pour reconstituer une "
            "architecture carnéadienne précise) — mais cette utilisation "
            "frappante atteste la diffusion populaire du τόπος moral "
            "néo-académicien au IIe siècle. Parallèles formels avec Lucien "
            "Iuppiter confutatus et Iuppiter tragoedus notés par Bruns 1889"
        ),
        description_en=(
            "Thesis of Amand 1945 (Book I Ch. IV §II.3, p. 132-134): in his "
            "antifatalist polemic against Democritus and Chrysippus (Γοήτων "
            "φώρα, preserved in Eusebius PE VI.7.1-42), Oinomaos of Gadara "
            "produces no genuinely new argument — he accommodates with a "
            "strongly spiced sauce the traditional commonplaces stemming "
            "from Carneades. An impetuous temperament but a shallow mind, "
            "Oinomaos safeguards the full freedom of the will as an immediate "
            "and incontestable datum of personal consciousness. The "
            "characteristic passage (PE VI.7.35-41 = Vallette p. 78-80) "
            "deploys the central idea: under the hypothesis of absolute "
            "fatalism, all morality is impossible, virtue and vice become "
            "empty words, man is innocent whatever crime he commits, and the "
            "gods can neither be angry nor punish. The gods themselves are "
            "addressed: 'You did not allow us, O gods, to become virtuous!' "
            "For Amand, this is not a 'witness text' (the Cynic is too "
            "free and personal to reconstitute a precise Carneadean "
            "architecture) — but this striking use attests the popular "
            "diffusion of the Neo-Academic moral topos in the 2nd century. "
            "Formal parallels with Lucian's Iuppiter confutatus and Iuppiter "
            "tragoedus noted by Bruns 1889"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 132-134",
            md_line_range="ll. 7465-7636",
            chapter="Livre I Ch. IV §II.3 (Polémique antifataliste)",
            amand_chapter_actual="Oinomaos — libre adaptation carnéadienne",
            extra={"amand_thesis_type": "cynic_carneadean_adaptation_2c"},
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_amand1945_oinomaos_julian_pagan_critique",
        type="synthesis",
        label="Critique julienne d'Oinomaos — symptôme pagan tardif (Amand 1945)",
        description=(
            "Note d'Amand 1945 (Livre I Ch. IV §II.1, p. 129-130) : Julien "
            "l'Apostat, fervent néoplatonicien et restaurateur du paganisme, "
            "reproche à Oinomaos de Gadara (Discours 7, éd. Hertlein, p. "
            "271.1—273.2 ; cf. Discours 6, p. 257.22-25) de graves impiétés — "
            "détruire le respect dû aux dieux, mépriser la raison, fouler aux "
            "pieds lois divines et humaines, composer des tragédies "
            "scandaleuses. Pour Amand, ce jugement passionné est dicté pour "
            "une part par l'horreur du pieux restaurateur à l'égard du "
            "contempteur de la religion populaire — mais documente "
            "indirectement le caractère iconoclaste du cynisme antifataliste "
            "du IIe siècle. Oinomaos s'écartait de façon frappante des mœurs "
            "de son époque et s'opposait à la mentalité mystique et "
            "superstitieuse de la plupart de ses contemporains — ce que "
            "Julien lit comme insulte au génie hellénique"
        ),
        description_en=(
            "Note in Amand 1945 (Book I Ch. IV §II.1, p. 129-130): Julian "
            "the Apostate, fervent Neoplatonist and restorer of paganism, "
            "reproaches Oinomaos of Gadara (Discourse 7, ed. Hertlein, p. "
            "271.1—273.2; cf. Discourse 6, p. 257.22-25) with grave impieties "
            "— destroying the respect due to the gods, despising reason, "
            "trampling divine and human laws, composing scandalous "
            "tragedies. For Amand, this passionate judgement is dictated in "
            "part by the pious restorer's horror at the contemner of "
            "popular religion — but indirectly documents the iconoclastic "
            "character of 2nd-century antifatalist Cynicism. Oinomaos "
            "departed strikingly from the customs of his time and opposed "
            "the mystical and superstitious mentality of most of his "
            "contemporaries — which Julian reads as an insult to the "
            "Hellenic genius"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 129-130",
            md_line_range="ll. 7411-7445",
            chapter="Livre I Ch. IV §II.1 (Critique julienne)",
            amand_chapter_actual="Oinomaos vu par Julien l'Apostat",
            extra={"amand_thesis_type": "later_reception_julian"},
        ),
        confidence=0.85,
    ),
    # ---- Neoplatonists (3 syntheses) ----
    _node(
        id="synthesis_amand1945_plotinus_non_witness_explanation",
        type="synthesis",
        label="Plotin ne recourt jamais aux topoi carnéadiens — explication e silentio (Amand 1945)",
        description=(
            "Thèse centrale d'Amand 1945 pour le chapitre néoplatonicien "
            "(Livre I Ch. VI §I, p. 157-163) : 'chose curieuse, Plotin, ce "
            "mystique oriental, qui fut aussi le dernier philosophe grec de "
            "génie, ne fait nulle part appel, dans les Ennéades, à "
            "l'argumentation morale de Carnéade.' Ni Enn. III.1 (Peri "
            "Heimarmenes), ni Enn. II.3 (De l'influence des astres), ni "
            "ailleurs, Plotin ne manie les lieux communs tirés des "
            "conséquences désastreuses du fatalisme absolu. L'argument e "
            "silentio est ici probant. Amand propose trois facteurs "
            "explicatifs convergents : (1) Plotin croit fermement à la "
            "liberté de la volonté (Enn. III.1.4-5 : la doctrine adverse "
            "réduit l'homme à 'l'état de pierres subissant le mouvement') ; "
            "(2) mais il professe le déterminisme stoïcien et la sympatheia "
            "universelle posidonienne (Enn. II.3.7, IV.4.39), fondant la "
            "légitimité de la mantique 'naturelle' ; (3) sa solution propre — "
            "la distinction astres-signes vs astres-causes (Enn. II.3.1-7) "
            "héritée de l'astrométéorologie hellénistique — préserve le "
            "libre arbitre intellectuel sans recourir aux topoi carnéadiens. "
            "Mais surtout, en restreignant le τὸ ἐφ' ἡμῖν à l'intelligence "
            "et à la vertu intérieure (Enn. VI.8.2, 6, 8), Plotin neutralise "
            "préalablement l'objection morale néo-académicienne qui suppose "
            "une extension large du libre arbitre aux actions concrètes"
        ),
        description_en=(
            "Central thesis of Amand 1945 for the Neoplatonist chapter (Book "
            "I Ch. VI §I, p. 157-163): 'curiously, Plotinus, this Oriental "
            "mystic, who was also the last Greek philosopher of genius, "
            "nowhere in the Enneads appeals to Carneades's moral "
            "argumentation.' Neither in Enn. III.1 (Peri Heimarmenes), nor "
            "in Enn. II.3 (On Stellar Influence), nor elsewhere, does "
            "Plotinus handle the commonplaces drawn from the disastrous "
            "consequences of absolute fatalism. The argumentum e silentio "
            "is here probative. Amand proposes three converging explanatory "
            "factors: (1) Plotinus firmly believes in the freedom of the "
            "will (Enn. III.1.4-5: the adverse doctrine reduces man to 'the "
            "state of stones undergoing motion'); (2) but he professes Stoic "
            "determinism and Posidonian universal sympatheia (Enn. II.3.7, "
            "IV.4.39), grounding the legitimacy of 'natural' divination; (3) "
            "his own solution — the distinction stars-as-signs vs "
            "stars-as-causes (Enn. II.3.1-7) inherited from Hellenistic "
            "astrometeorology — preserves intellectual free will without "
            "recourse to Carneadean topoi. But above all, by restricting τὸ "
            "ἐφ' ἡμῖν to the intellect and inner virtue (Enn. VI.8.2, 6, 8), "
            "Plotinus neutralizes in advance the Neo-Academic moral "
            "objection which presupposes a broad extension of free will to "
            "concrete actions"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 157-163",
            md_line_range="ll. 9250-9546",
            chapter="Livre I Ch. VI §I",
            amand_chapter_actual="Plotin — non-utilisation de Carnéade",
            extra={"amand_thesis_type": "e_silentio_explanation"},
        ),
        confidence=0.95,
    ),
    _node(
        id="synthesis_amand1945_neoplatonic_school_no_carneadean_use",
        type="synthesis",
        label="L'école néoplatonicienne plotinienne néglige Carnéade (Amand 1945)",
        description=(
            "Thèse-cadre d'Amand 1945 (Livre I Ch. VI §II.4, p. 171) : les "
            "Néo-Platoniciens de la tendance plotinienne (Porphyre, Jamblique, "
            "Proclus), métaphysiciens et mystiques, négligent l'argumentation "
            "maniée contre le fatalisme stoïcien, qu'ils admettent "
            "partiellement, tout en maintenant en paroles la libre volonté "
            "humaine. Ils professent que les astres sont les signes "
            "annonciateurs et non les causes efficientes de nos destinées ; "
            "les âmes ne sont libres que d'une εἱμαρμένη qu'elles se sont "
            "imposée à elles-mêmes par libre choix prénatal (interprétation "
            "néoplatonicienne du mythe d'Er de République X). Dans un système "
            "foncièrement déterministe où l'âme humaine est soumise à une "
            "εἱμαρμένη se combinant avec la spontanéité de la volonté, la "
            "discussion de Carnéade (qui suppose l'indéterminisme du vouloir "
            "s'étendant aux actions concrètes) ne peut s'insérer naturellement "
            "— elle constituerait un élément discordant et hétérogène. Pour "
            "Amand, cette continuité doctrinale plotinienne explique le "
            "silence universel des Néo-Platoniciens classiques sur les "
            "topoi carnéadiens"
        ),
        description_en=(
            "Frame thesis of Amand 1945 (Book I Ch. VI §II.4, p. 171): the "
            "Neoplatonists of the Plotinian tendency (Porphyry, Iamblichus, "
            "Proclus), metaphysicians and mystics, neglect the argumentation "
            "deployed against Stoic fatalism, which they partially accept, "
            "while maintaining in words human free will. They profess that "
            "the stars are announcing signs and not efficient causes of our "
            "destinies; souls are free only of an εἱμαρμένη that they have "
            "imposed on themselves by prenatal free choice (Neoplatonic "
            "interpretation of the myth of Er in Republic X). In a "
            "fundamentally deterministic system where the human soul is "
            "subject to an εἱμαρμένη combining with the will's spontaneity, "
            "Carneades's discussion (which presupposes the indeterminism of "
            "the will extending to concrete actions) cannot naturally "
            "insert itself — it would constitute a discordant and "
            "heterogeneous element. For Amand, this Plotinian doctrinal "
            "continuity explains the universal silence of classical "
            "Neoplatonists on the Carneadean topoi"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 171",
            md_line_range="ll. 9887-9907",
            chapter="Livre I Ch. VI §II.4",
            amand_chapter_actual="École néoplatonicienne plotinienne entière",
            extra={"amand_thesis_type": "school_systematic_silence"},
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_amand1945_hierocles_bizarre_carneadean_inversion",
        type="synthesis",
        label="Hiéroclès et l'inversion bizarre du topos carnéadien (Amand 1945)",
        description=(
            "Thèse spectaculaire d'Amand 1945 (Livre I Ch. VI §II.5, p. "
            "173-176) : alors que tous les Néoplatoniciens plotiniens "
            "négligent l'argumentation de Carnéade, le néoplatonicien "
            "alexandrin Hiéroclès (début Ve siècle) en fait une 'utilisation "
            "inattendue' — voire 'bizarre' — pour prouver l'existence de la "
            "Providence et de l'εἱμαρμένη providentielle. Au lieu d'utiliser "
            "le topos comme réfutation du fatalisme (lois, raisonnements, "
            "vertus deviennent inutiles si fatalisme), Hiéroclès l'inverse : "
            "puisque lois, raisonnements, vertus, prières sont des choses "
            "nécessaires, bonnes et salutaires, alors la disposition "
            "providentielle de l'εἱμαρμένη existe et n'est nullement "
            "supprimée. La preuve antifataliste par excellence est appelée "
            "à démontrer une εἱμαρμένη providentielle pédagogique (παιδεύουσα). "
            "Tour de force conceptuel rendu possible par une métamorphose "
            "sémantique radicale du sinistre vocable : l'ἀνάγκη rigide "
            "(choquante pour les chrétiens) est remplacée par un concept "
            "personnel et moral — celui du gouvernement divin qui punit et "
            "éduque les âmes selon leurs actes libres (κρίσις θεία οὖσα ἐν "
            "τοῖς οὐκ ἐφ' ἡμῖν πρὸς τὴν ἀξίαν ἀμοιβὴν τῶν ἐφ' ἡμῖν, Photius "
            "p. 465 b 33-38). Pour Amand, les développements d'Hiéroclès "
            "rappellent singulièrement le grand effort d'Origène pour "
            "harmoniser libre arbitre et Providence — proximité doctrinale "
            "qu'Amand juge probable (Phase 9 EleutherIA confirme contact "
            "philosophique direct)"
        ),
        description_en=(
            "Spectacular thesis of Amand 1945 (Book I Ch. VI §II.5, p. "
            "173-176): while all Plotinian Neoplatonists neglect Carneades's "
            "argumentation, the Alexandrian Neoplatonist Hierocles (early "
            "5th c.) makes an 'unexpected' — even 'bizarre' — use of it to "
            "prove the existence of Providence and providential εἱμαρμένη. "
            "Instead of using the topos as refutation of fatalism (laws, "
            "reasonings, virtues become useless if fatalism holds), Hierocles "
            "inverts it: since laws, reasonings, virtues, prayers are "
            "necessary, good and salutary things, then the providential "
            "disposition of εἱμαρμένη exists and is by no means suppressed. "
            "The quintessential antifatalist proof is enlisted to demonstrate "
            "a pedagogical providential εἱμαρμένη (παιδεύουσα). A conceptual "
            "tour de force made possible by a radical semantic metamorphosis "
            "of the sinister term: rigid ἀνάγκη (shocking to Christians) is "
            "replaced by a personal moral concept — that of the divine "
            "government punishing and educating souls according to their "
            "free acts (κρίσις θεία οὖσα ἐν τοῖς οὐκ ἐφ' ἡμῖν πρὸς τὴν "
            "ἀξίαν ἀμοιβὴν τῶν ἐφ' ἡμῖν, Photius p. 465 b 33-38). For Amand, "
            "Hierocles's developments singularly recall Origen's great "
            "effort to harmonize free will and Providence — a doctrinal "
            "proximity Amand judges probable (EleutherIA Phase 9 confirms "
            "direct philosophical contact)"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 173-176",
            md_line_range="ll. 9974-10138",
            chapter="Livre I Ch. VI §II.5",
            amand_chapter_actual="Hiéroclès — inversion bizarre du topos",
            extra={"amand_thesis_type": "anomalous_carneadean_inversion_providential"},
        ),
        confidence=0.95,
    ),
]


# =============================================================================
# ARGUMENTS (4)
# =============================================================================

NEW_ARGUMENTS: list[dict[str, Any]] = [
    _node(
        id="argument_lucian_zeus_confutatus_carneadean_topos",
        type="argument",
        label="Argumentation morale carnéadienne dans Iuppiter confutatus 18 (Lucien)",
        description=(
            "Argument-cadre déployé par Cyniscos dans Lucien Iuppiter "
            "confutatus 18 (éd. Jacobitz II, p. 347) — reductio ad absurdum "
            "directe du fatalisme. Texte clé : Ὅτι οὐδὲν ἑκόντες οἱ ἄνθρωποι "
            "ποιοῦμεν, ἀλλά τινι ἀνάγκῃ ἀφύκτῳ κεκελευσμένοι, εἴ γε ἀληθῆ "
            "ἐκεῖνά ἐστι τὰ ἔμπροσθεν ὡμολογημένα, ὡς ἡ Μοῖρα πάντων αἰτία. "
            "Structure : (P1) Zeus a concédé que Μοῖρα est cause universelle ; "
            "(P2) Zeus a concédé qu'on ne punit ni l'instrument ni l'acte "
            "involontaire ; (P3) tout acte humain est exécution d'un "
            "commandement nécessaire de la Moira ; (C1) tout acte humain "
            "est donc involontaire et l'agent humain ne peut être ni châtié "
            "ni récompensé en justice ; (C2) Minos devrait punir l'Heimarmene "
            "elle-même au lieu de Sisyphe, et la Moira au lieu de Tantale. "
            "Pour Amand 1945 (Livre I Ch. III §II.3, p. 113-115), cet argument "
            "ad absurdum 'manié avec tant d'éclat par Carnéade dans sa lutte "
            "contre Chrysippe ferme la bouche à Zeus lui-même'. C'est "
            "l'utilisation lucianesque la plus systématique du topos moral "
            "antifataliste néo-académicien"
        ),
        description_en=(
            "Frame-argument deployed by Cyniscus in Lucian's Iuppiter "
            "confutatus 18 (ed. Jacobitz II, p. 347) — direct reductio ad "
            "absurdum of fatalism. Key text: Ὅτι οὐδὲν ἑκόντες οἱ ἄνθρωποι "
            "ποιοῦμεν, ἀλλά τινι ἀνάγκῃ ἀφύκτῳ κεκελευσμένοι, εἴ γε ἀληθῆ "
            "ἐκεῖνά ἐστι τὰ ἔμπροσθεν ὡμολογημένα, ὡς ἡ Μοῖρα πάντων αἰτία. "
            "Structure: (P1) Zeus has conceded that Moira is universal cause; "
            "(P2) Zeus has conceded that one punishes neither the instrument "
            "nor the involuntary act; (P3) every human act is execution of "
            "a necessary command of Moira; (C1) every human act is thus "
            "involuntary and the human agent can be neither punished nor "
            "rewarded in justice; (C2) Minos should punish Heimarmene itself "
            "instead of Sisyphus, and Moira instead of Tantalus. For Amand "
            "1945 (Book I Ch. III §II.3, p. 113-115), this reductio ad "
            "absurdum 'wielded so brilliantly by Carneades in his struggle "
            "against Chrysippus silences Zeus himself'. This is the most "
            "systematic Lucianic use of the Neo-Academic antifatalist moral "
            "topos"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 113-115",
            md_line_range="ll. 6705-6762",
            chapter="Livre I Ch. III §II.3 (Argument central Iupp. conf. 18)",
            amand_chapter_actual="Lucien Iupp. conf. 18 — reductio ad absurdum carnéadien",
            extra={
                "amand_classification": "carneadean_topos_moral_lucianic_reductio",
                "premises": [
                    "Zeus concède que Μοῖρα est cause universelle",
                    "Acte involontaire ou par contrainte n'est ni puni ni récompensé en justice",
                    "Tout acte humain exécute une nécessité fatale",
                ],
                "conclusion": "Si fatalisme intégral, la justice infernale doit s'exercer sur la Moira et l'Heimarmene, non sur les humains.",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_oinomaos_carneadean_libre_adaptation",
        type="argument",
        label="Adaptation libre du topos carnéadien chez Oinomaos (PE VI.7.35-41)",
        description=(
            "Argument cynique antifataliste d'Oinomaos de Gadara dans Γοήτων "
            "φώρα (cité par Eusèbe PE VI.7.35-41, Dindorf I, p. 298.1—299.8 ; "
            "Vallette p. 78-80). Forme : apostrophe pamphlétaire à Apollon et "
            "Zeus, accusés d'imposer une nécessité tout en punissant les "
            "humains pour leurs actes nécessaires. Texte caractéristique : "
            "'Tu es injuste, Apollon ! Ce n'est pas à bon droit que tu nous "
            "punis, nous les innocents... Vous ne nous avez pas permis, ô "
            "dieux, de devenir vertueux ! Au contraire vous nous avez "
            "contraints et forcés à vivre en criminels.' Structure : (P1) "
            "Apollon (oracles) et Zeus (Heimarmene) imposent une nécessité "
            "extérieure ; (P2) sous nécessité, vertu et vice cessent d'être "
            "imputables ; (C1) les dieux n'ont aucun droit de châtier ni "
            "récompenser ; (C2) Lycurgue ne peut être loué (il n'agissait "
            "pas de son propre gré) ; (C3) Épicure doit être absous de tous "
            "les reproches chrysippiens. Pour Amand 1945 (Livre I Ch. IV "
            "§II.3, p. 132-134), 'libre adaptation d'un argument célèbre de "
            "Carnéade' — pas un texte témoin mais attestation populaire "
            "vivante du τόπος"
        ),
        description_en=(
            "Cynic antifatalist argument by Oinomaos of Gadara in Γοήτων "
            "φώρα (cited by Eusebius PE VI.7.35-41, Dindorf I, p. "
            "298.1—299.8; Vallette p. 78-80). Form: pamphleteer's apostrophe "
            "to Apollo and Zeus, accused of imposing a necessity while "
            "punishing humans for their necessary acts. Characteristic text: "
            "'You are unjust, Apollo! It is not rightly that you punish us, "
            "the innocent... You did not allow us, O gods, to become "
            "virtuous! On the contrary you constrained and forced us to live "
            "as criminals.' Structure: (P1) Apollo (oracles) and Zeus "
            "(Heimarmene) impose external necessity; (P2) under necessity, "
            "virtue and vice cease to be imputable; (C1) the gods have no "
            "right to chastise or reward; (C2) Lycurgus cannot be praised (he "
            "did not act of his own will); (C3) Epicurus must be absolved "
            "of all Chrysippan reproaches. For Amand 1945 (Book I Ch. IV "
            "§II.3, p. 132-134), 'free adaptation of a famous Carneades "
            "argument' — not a witness text but a lively popular attestation "
            "of the τόπος"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 132-134",
            md_line_range="ll. 7547-7636",
            chapter="Livre I Ch. IV §II.3 (PE VI.7.35-41)",
            amand_chapter_actual="Oinomaos — apostrophe aux dieux",
            extra={
                "amand_classification": "carneadean_topos_moral_cynic_apostrophe",
                "primary_attestation": "Eusebius PE VI.7.35-41 (= Vallette p. 78-80)",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_diogenes_oinoanda_no_heimarmene_fragm_xxxiii",
        type="argument",
        label="Diogénès d'Oinoanda fragm. XXXIII : pas de mantique, donc pas d'εἱμαρμένη",
        description=(
            "Argument épicurien antifataliste inscrit par Diogénès d'Oinoanda "
            "sur le portique d'Oinoanda (fragment XXXIII, éd. William 1907, "
            "p. 40-42). Texte original cité par Amand : τὸ δὲ μέγιστον· "
            "πιστευθείσης γὰρ εἱμαρμένης, αἴρεται πᾶσα νουθεσία καὶ ἐπιτείμησις "
            "καὶ οὐδὲ τοὺς πονηροὺς [ἐξέσται κολάζειν]. Structure : (P1) "
            "L'εἱμαρμένη n'est prouvée que par la mantique (cf. Chrysippe) ; "
            "(P2) la mantique a été préalablement réfutée comme nulle et "
            "fausse (fragm. XXXI, perdu en grande partie) ; (C1) il n'existe "
            "plus aucun argument en faveur de l'εἱμαρμένη. Suit l'argument "
            "moral indépendant — si l'on croit à l'εἱμαρμένη, tout "
            "avertissement (νουθεσία) devient inutile, tout blâme (ἐπιτίμησις) "
            "superflu, et il n'est plus permis de punir les criminels. Pour "
            "Amand 1945 (Livre I Ch. III Note suppl. §II, p. 119-120), c'est "
            "l'écho probable de la doctrine d'Épicure (fragm. 378 Usener) "
            "plutôt que de Carnéade directement — mais montre la diffusion "
            "des deux topoi (anti-mantique + moral antifataliste) dans "
            "l'épicurisme tardif"
        ),
        description_en=(
            "Epicurean antifatalist argument inscribed by Diogenes of "
            "Oinoanda on the Oinoanda portico (fragment XXXIII, ed. William "
            "1907, p. 40-42). Original text cited by Amand: τὸ δὲ μέγιστον· "
            "πιστευθείσης γὰρ εἱμαρμένης, αἴρεται πᾶσα νουθεσία καὶ "
            "ἐπιτείμησις καὶ οὐδὲ τοὺς πονηροὺς [ἐξέσται κολάζειν]. Structure: "
            "(P1) εἱμαρμένη is proved only by divination (cf. Chrysippus); "
            "(P2) divination has been previously refuted as null and false "
            "(fragm. XXXI, largely lost); (C1) no further argument remains "
            "for εἱμαρμένη. Follows the independent moral argument — if one "
            "believes in εἱμαρμένη, all warning (νουθεσία) becomes useless, "
            "all blame (ἐπιτίμησις) superfluous, and it is no longer "
            "permitted to punish criminals. For Amand 1945 (Book I Ch. III "
            "Suppl. Note §II, p. 119-120), this is the probable echo of "
            "Epicurus's own doctrine (fragm. 378 Usener) rather than "
            "Carneades directly — but it shows the diffusion of both topoi "
            "(anti-divination + antifatalist moral) in late Epicureanism"
        ),
        period="Roman Imperial",
        metadata=amand_metadata(
            page_range="p. 119-120",
            md_line_range="ll. 6928-6975",
            chapter="Livre I Ch. III Note suppl. §II (Diogénès d'Oinoanda)",
            amand_chapter_actual="Diogénès d'Oinoanda fragm. XXXIII",
            extra={
                "amand_classification": "epicurean_anti_mantike_anti_heimarmene",
                "primary_attestation": "Inscription d'Oinoanda fragm. XXXIII col. 1-3",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_hierocles_carneadean_inversion_for_providential_heimarmene",
        type="argument",
        label="Hiéroclès — inversion du topos carnéadien pour prouver l'εἱμαρμένη providentielle",
        description=(
            "Argument néoplatonicien anomalous d'Hiéroclès d'Alexandrie dans "
            "Περὶ προνοίας Livre III ch. 10 (cité par Photius cod. 251 Bekker "
            "p. 465 a 13-31 = PG 104, 92AC). Structure logique inversée par "
            "rapport à Carnéade : (P1) si la Providence n'existe pas, alors "
            "lois (νόμοι), raison (λογισμός), délibération (τὸ βουλεύεσθαι), "
            "prière (τὸ εὔχεσθαι), vertus sont sans utilité et même cessent "
            "d'exister ; (P2) or lois, raisonnements, vertus, prières sont "
            "des choses 'nécessaires, bonnes et salutaires' ; (C1) donc la "
            "disposition de l'εἱμαρμένη providentielle (ἡ τῆς προνοητικῆς "
            "εἱμαρμένης τάξις) existe et n'est nullement supprimée. (C2) Bien "
            "loin de réduire à néant la liberté humaine, cette εἱμαρμένη "
            "providentielle se concilie parfaitement avec le libre arbitre, "
            "et qui plus est en a besoin et le présuppose. Pour Amand 1945 "
            "(Livre I Ch. VI §II.5, p. 173-176), Hiéroclès retourne ainsi le "
            "topos antifataliste de Carnéade en preuve positive de la "
            "providence pédagogique — adaptation 'bizarre' mais "
            "philosophiquement subtile, rendue possible par la métamorphose "
            "sémantique de l'εἱμαρμένη en κρίσις θεία οὖσα ἐν τοῖς οὐκ ἐφ' "
            "ἡμῖν πρὸς τὴν ἀξίαν ἀμοιβὴν τῶν ἐφ' ἡμῖν (Photius p. 465 b "
            "33-38). Affinité doctrinale notée avec Origène"
        ),
        description_en=(
            "Anomalous Neoplatonic argument by Hierocles of Alexandria in "
            "Περὶ προνοίας Book III ch. 10 (cited by Photius cod. 251 "
            "Bekker p. 465 a 13-31 = PG 104, 92AC). Logical structure "
            "inverted relative to Carneades: (P1) if Providence does not "
            "exist, then laws (νόμοι), reason (λογισμός), deliberation (τὸ "
            "βουλεύεσθαι), prayer (τὸ εὔχεσθαι), virtues are useless and "
            "even cease to exist; (P2) but laws, reasonings, virtues, "
            "prayers are 'necessary, good and salutary' things; (C1) "
            "therefore the disposition of providential εἱμαρμένη (ἡ τῆς "
            "προνοητικῆς εἱμαρμένης τάξις) exists and is by no means "
            "suppressed. (C2) Far from annihilating human freedom, this "
            "providential εἱμαρμένη perfectly reconciles with free will, and "
            "moreover needs it and presupposes it. For Amand 1945 (Book I "
            "Ch. VI §II.5, p. 173-176), Hierocles thereby turns the "
            "Carneadean antifatalist topos into a positive proof of "
            "pedagogical providence — a 'bizarre' but philosophically "
            "subtle adaptation, made possible by the semantic metamorphosis "
            "of εἱμαρμένη into κρίσις θεία οὖσα ἐν τοῖς οὐκ ἐφ' ἡμῖν πρὸς "
            "τὴν ἀξίαν ἀμοιβὴν τῶν ἐφ' ἡμῖν (Photius p. 465 b 33-38). "
            "Doctrinal affinity noted with Origen"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 173-176",
            md_line_range="ll. 10058-10138",
            chapter="Livre I Ch. VI §II.5",
            amand_chapter_actual="Hiéroclès — inversion providentielle (Peri pronoias III.10)",
            extra={
                "amand_classification": "carneadean_topos_inverted_neoplatonic_providential",
                "primary_attestation": "Photius Bibl. cod. 251 p. 465 a 13-31 Bekker = PG 104, 92AC",
            },
        ),
        confidence=0.95,
    ),
]


# =============================================================================
# AGGREGATE
# =============================================================================

NEW_INSERTS: list[dict[str, Any]] = (
    NEW_PERSONS
    + NEW_WORKS
    + NEW_CONCEPTS
    + NEW_SYNTHESES
    + NEW_ARGUMENTS
)
