"""B5 NEW_INSERTS — 33 nouveaux nœuds Amand 1945 sur Origène (Livre II Ch. V).

Structure :
- 4 enveloppes (§I, §II, §III, §IV)
- 24 sub-arguments distribués
- 3 concepts (λογικὸν ζῷον, ἀξία βίβλος τοῦ θεοῦ, métensomatose)
- 5 syntheses Amand-style
- 1 sub-arg « virtue voluntary essence » (citation CC IV.3)

Total : 33 inserts (4 + 7 + 5 + 8 + 7 + 3 + 5 + 1 essence = 40 mais ajusté en consolidation)

NB : on cible **environ** 33 ; le décompte exact peut bouger selon décisions ad hoc.
"""
from __future__ import annotations

from amand_b5_utils import make_node, md_base, WAVE_TAG  # type: ignore

NEW_INSERTS: list[dict] = []


# ============================================================================
# §I — ENVELOPPE Personnalité (1)
# ============================================================================

NEW_INSERTS.append(make_node(
    nid="argument_origen_witness_personality_envelope_amand1945",
    ntype="argument", label="Origène — Personnalité intellectuelle/religieuse + attitude vis-à-vis de la philosophie (Amand 1945 Livre II Ch. V §I)",
    period="Patristic", school="school_middle_platonism", role="amand1945_witness_envelope",
    description=(
        "**Enveloppe argumentaire** regroupant les claims d'Amand de Mendieta (Fatalisme et liberté dans l'antiquité grecque, "
        "Louvain 1945, Livre II Ch. V §I, p. 276-296) sur la personnalité intellectuelle et religieuse d'Origène, son attitude "
        "vis-à-vis de la philosophie hellénique, et l'influence réelle de la philosophie grecque sur sa pensée.\n\n"
        "Trois sous-sections d'Amand : (1) personnalité intellectuelle et religieuse — Bible-Platon double pôle, refus de "
        "l'unilatéralisme E. de Faye/Hal Koch et de Bardy ; (2) attitude d'Origène à l'égard de la philosophie — pas de "
        "sympathie personnelle, mais usage rigoureux ; les Épicuriens sont méprisés, les Stoïciens reconnus utiles, Platon "
        "et Socrate admirés (sauf le coq d'Asclépios et le sacrifice d'Artémis) ; (3) influence réelle — platonisme premier, "
        "puis aristotélisme, stoïcisme, médio-platonisme (Albinos, Atticos, Numénios), école d'Ammonios Saccas."
    ),
    description_en=(
        "**Argumentative envelope** grouping Amand de Mendieta's claims (Fatalism and freedom in Greek antiquity, Louvain 1945, "
        "Book II Ch. V §I, p. 276-296) on Origen's intellectual and religious personality, his attitude toward Hellenic philosophy, "
        "and the real influence of Greek philosophy on his thought.\n\n"
        "Amand's three sub-sections: (1) intellectual and religious personality — Bible-Plato double pole, rejection of "
        "De Faye/Hal Koch's and Bardy's unilateral readings; (2) Origen's attitude toward philosophy — no personal sympathy, "
        "but rigorous use; Epicureans despised, Stoics acknowledged useful, Plato and Socrates admired (except cock to "
        "Asclepius and sacrifice to Artemis); (3) real influence — Platonism first, then Aristotelianism, Stoicism, "
        "Middle Platonism (Albinus, Atticus, Numenius), school of Ammonius Saccas."
    ),
    md=md_base(
        page_range="p. 276-296",
        md_line_range="ll. 14740-15578",
        chapter="Livre II Ch. V §I (Origène)",
        chapter_actual="Livre II Ch. V §I — Esquisse de la personnalité d'Origène. Origène et la philosophie grecque",
        confidence=0.9,
        cited_editions=[
            "GILSON-BÔHNER, G.Chr.Phil., p. 43-44 et p. 45-67 (synthèse système Origène)",
            "Hal KOCH, Pronoia und Paideusis (Berlin 1932)",
            "E. DE FAYE, Origène. Sa vie, son œuvre, sa pensée (3 vol., Paris 1923-1928)",
            "R. CADIOU, La jeunesse d'Origène (Paris 1936)",
            "G. BARDY, art. Origène dans D.Th.C. XI, 2 (1932) col. 1489-1565",
        ],
        extra={
            "is_witness_argument": True,
            "amand_witness_rank": "primary_witness_n1_envelope",
            "amand_witness_role": "envelope_personality_philosophy",
            "amand_envelope_subarguments": [
                "argument_origen_witness_personality_double_polarity_amand1945",
                "argument_origen_witness_personality_anti_unilateral_amand1945",
                "argument_origen_witness_personality_christian_gnosis_amand1945",
                "argument_origen_witness_platonism_influence_amand1945",
                "argument_origen_witness_aristotelism_influence_amand1945",
                "argument_origen_witness_stoicism_influence_amand1945",
                "argument_origen_witness_middle_platonism_amand1945",
            ],
        },
    ),
))


# ============================================================================
# §I sub-arguments (3)
# ============================================================================

NEW_INSERTS.append(make_node(
    nid="argument_origen_witness_personality_double_polarity_amand1945",
    ntype="argument", label="Origène — Bible-Platon comme double pôle (Amand 1945)",
    period="Patristic", school="school_middle_platonism", role="amand1945_subarg",
    description=(
        "Selon Amand (p. 279-280), « la Bible et Platon constituent les pôles de la vie spirituelle » d'Origène. "
        "L'âme est fermement chrétienne, fidèlement ancrée à la règle de foi ecclésiastique, tandis que l'esprit "
        "rationnel est tout informé par la philosophie platonicienne, en particulier le platonisme moyen, mêlée "
        "d'apports aristotéliciens et stoïciens considérables. La vie de prière, les traités sur la prière et le "
        "martyre, le Commentaire du Cantique, certaines homélies sur l'AT révèlent une mystique authentiquement "
        "chrétienne. Amand récuse explicitement les lectures unilatérales de E. de Faye et Hal Koch (Origène "
        "comme philosophe-platonicien égaré dans l'Église) et celle de Bardy (Origène comme bibliste pur)."
    ),
    description_en=(
        "According to Amand (p. 279-280), 'the Bible and Plato constitute the poles' of Origen's spiritual life. "
        "His soul is firmly Christian, faithfully anchored to the ecclesiastical rule of faith, while his rational "
        "mind is wholly informed by Platonic philosophy, particularly Middle Platonism, mixed with considerable "
        "Aristotelian and Stoic contributions. His prayer life, treatises on prayer and martyrdom, Commentary on "
        "the Song, certain OT homilies reveal an authentically Christian mysticism. Amand explicitly rejects the "
        "unilateral readings of E. de Faye and Hal Koch (Origen as Platonist philosopher stranded in the Church) "
        "and Bardy's (Origen as pure biblicist)."
    ),
    md=md_base(
        page_range="p. 279-280",
        md_line_range="ll. 14990-15065",
        chapter="Livre II Ch. V §I.1 (Personnalité intellectuelle et religieuse)",
        chapter_actual="Livre II Ch. V §I.1 — Bible-Platon double pôle, contra E. de Faye/Hal Koch et Bardy",
        confidence=0.9,
        cited_editions=[
            "Hal KOCH, Pronoia und Paideusis, Berlin 1932, p. 32-36, 159-161, 315-317",
            "E. DE FAYE, Origène. Sa vie, son œuvre, sa pensée III. La doctrine, Paris 1928, p. 287",
            "G. BARDY, D.Th.C. XI, 2 (1932), col. 1494",
            "W. VÖLKER, Das Vollkommenheitsideal des Origenes, Tübingen 1931",
            "E. SCHWARTZ, Kaiser Constantin und die christliche Kirche², Leipzig 1936, p. 101-104",
        ],
        extra={
            "amand_witness_rank": "primary_witness_n1_subarg",
            "is_witness_argument": True,
            "amand_judgement_quote_fr": "La Bible et Platon constituent les pôles de sa vie spirituelle. Si son esprit est grec, foncièrement grec, si sa pensée rationnelle est tout informée par la philosophie platonicienne, en particulier par celle du platonisme moyen, mêlée d'ailleurs d'apports aristotéliciens et stoïciens considérables, son âme, en revanche, est fermement chrétienne",
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="argument_origen_witness_personality_anti_unilateral_amand1945",
    ntype="argument", label="Origène — Rejet des lectures unilatérales (Amand contra de Faye/Koch et contra Bardy)",
    period="Patristic", school=None, role="amand1945_subarg",
    description=(
        "Amand (p. 279) argumente que les deux opinions extrêmes sur Origène sont également défectueuses : (1) l'opinion "
        "qui réduit le christianisme d'Origène à un simple instrument de la philosophie grecque (Hal Koch attribue à la "
        "philosophie un rôle capital ; E. de Faye y voit un idéalisme pédagogique théorique transformant le christianisme "
        "historique en métaphysique) ; (2) l'opinion qui réduit la philosophie à un simple instrument du christianisme "
        "biblique (Bardy : « prêtre dévoué au salut des âmes, bien plus que philosophe »). Aucune ne tient compte de la "
        "complexité réelle de l'intelligence d'Origène. La preuve : la règle d'or qu'Origène formule dans la préface du "
        "De Principiis (« On ne peut admettre comme vérité de foi que celle qui ne s'écarte en aucun point de la tradition "
        "ecclésiastique et apostolique ») distingue très nettement les données certaines de la foi et les questions non "
        "encore définies par l'Église, où la spéculation philosophique peut se donner libre cours."
    ),
    description_en=(
        "Amand (p. 279) argues that the two extreme opinions on Origen are equally defective: (1) the view that reduces "
        "Origen's Christianity to a mere instrument of Greek philosophy (Hal Koch gives philosophy a capital role; "
        "E. de Faye sees in him a theoretical pedagogical idealism transforming historical Christianity into metaphysics); "
        "(2) the view that reduces philosophy to a mere instrument of biblical Christianity (Bardy: 'priest dedicated to "
        "the salvation of souls, more than philosopher'). Neither accounts for the real complexity of Origen's intelligence. "
        "Proof: Origen's golden rule in the preface of De Principiis ('No truth of faith can be admitted that deviates at "
        "any point from the ecclesiastical and apostolic tradition') very clearly distinguishes certain data of faith from "
        "questions not yet defined by the Church, where philosophical speculation can freely operate."
    ),
    md=md_base(
        page_range="p. 279, 284 note 1, 285",
        md_line_range="ll. 15045-15310",
        chapter="Livre II Ch. V §I.1 (Personnalité)",
        chapter_actual="Livre II Ch. V §I.1 — Rejet des lectures unilatérales de Koch/de Faye et de Bardy",
        confidence=0.85,
        cited_editions=[
            "Origène, Traité des Principes I, Préface, 2, éd. Koetschau, GCS 22 Leipzig 1913, p. 8 l. 27-28",
            "Origène, Traité des Principes I, Préface, 3-10, éd. Koetschau, p. 9-16",
        ],
        extra={
            "amand_witness_rank": "primary_witness_n1_subarg",
            "is_witness_argument": True,
            "evidence_pending": True,
            "evidence_pending_reason": "Princ. I, Préface (Koetschau p. 8-16) absent du corpus KG (SC268 ne couvre que III.1 + IV.1-3)",
            "cites_primary_source_target": "work_de_principiis_origen_230s_v2w3x4y5",
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="argument_origen_witness_personality_christian_gnosis_amand1945",
    ntype="argument", label="Origène — Premier maître éminent d'un système de gnose chrétienne (Amand-Schwartz)",
    period="Patristic", school=None, role="amand1945_subarg",
    description=(
        "Amand (p. 281-282) endosse le jugement de Schwartz : Origène est « le premier maître éminent d'un système de "
        "gnose chrétienne ». Cette formule signifie : la nouvelle gnose qu'Origène introduit dans l'Église se veut "
        "véritablement connaissance rationnelle (rationelle Erkenntnis), à la différence de l'ancienne gnose religieux-"
        "mystique étrangère à la philosophie hellénique. À la suite de Clément, mais avec une autre envergure intellectuelle, "
        "Origène a élevé la foi simple transmise par les apôtres à la dignité d'une gnose, par une diligente exégèse "
        "principalement allégorique des θεόπνευσται γραφαί, en utilisant la philosophie hellénique d'inspiration "
        "platonicienne comme instrument. Amand refuse explicitement de qualifier Valentin, Basilide et Marcion de "
        "« gnostiques chrétiens » au sens plénier, car ils se sont permis trop de fantaisies à l'égard du κανὼν "
        "ἐκκλησιαστικός. Quant à Irénée, il est un polémiste antignostique, non un théoricien systématique."
    ),
    description_en=(
        "Amand (p. 281-282) endorses Schwartz's judgment: Origen is 'the first eminent master of a Christian gnosis system'. "
        "This formula means: the new gnosis Origen introduces into the Church genuinely seeks to be rational knowledge "
        "(rationelle Erkenntnis), unlike the older religious-mystical gnosis foreign to Hellenic philosophy. Following "
        "Clement but with greater intellectual scope, Origen elevated the simple faith transmitted by the apostles to the "
        "dignity of a gnosis, through diligent (chiefly allegorical) exegesis of the θεόπνευσται γραφαί, using Plato-"
        "inspired Hellenic philosophy as instrument. Amand explicitly refuses to qualify Valentinus, Basilides, and "
        "Marcion as fully 'Christian gnostics', because they took too many liberties with the κανὼν ἐκκλησιαστικός. "
        "As for Irenaeus, he is an anti-Gnostic polemicist, not a systematic theorist."
    ),
    md=md_base(
        page_range="p. 281-282",
        md_line_range="ll. 15155-15225",
        chapter="Livre II Ch. V §I.1",
        chapter_actual="Livre II Ch. V §I.1 — Origène premier maître éminent de gnose chrétienne (formule Schwartz endossée)",
        confidence=0.8,
        cited_editions=[
            "E. SCHWARTZ, Kaiser Constantin und die christliche Kirche², Leipzig 1936, p. 96",
        ],
        extra={
            "amand_witness_rank": "primary_witness_n1_subarg",
            "is_witness_argument": True,
            "amand_judgement_quote_fr": "Origène, ce puissant esprit, devint le fondateur de la critique textuelle biblique et de l'exégèse scripturaire, qu'il fut le plus éminent défenseur que l'Église préconstantinienne opposa au paganisme et aux hérésies",
            "amand_explicit_refusal": ["Valentin", "Basilide", "Marcion", "Irénée (polémiste seulement)"],
        },
    ),
))


# ============================================================================
# §I.3 — Influences philosophiques (4 sub-args)
# ============================================================================

for nid, label, src_short, desc_fr, desc_en, locus_md, citations in [
    (
        "argument_origen_witness_platonism_influence_amand1945",
        "Origène — Influence platonicienne réelle (Amand 1945)",
        "platonisme",
        "Amand (p. 291-292) : Platon plus que tout autre exerça une profonde influence. Bigg dans un livre célèbre l'accrédita. "
        "Doctrine origénienne sur Dieu et le monde = pour l'essentiel celle de Platon. Idéalisme absolu, pensée centrée sur "
        "Dieu et le monde divin. De Platon : transcendance divine, bonté suréminente, théodicée (Dieu n'est nullement la "
        "cause du mal, punition cathartique-pédagogique, vertu suffit au bonheur, homme libre et responsable). Cosmologie "
        "inconcevable sans le Timée. Psychologie répond essentiellement au Phèdre. Origène a lu et relu le Phédon, le Phèdre, "
        "la République, le Timée, les Lois et les Lettres.",
        "Amand (p. 291-292): Plato more than any other exercised profound influence. Bigg in a famous book established this. "
        "Origenian doctrine on God and the world = essentially Plato's. Absolute idealism, thought centered on God and the "
        "divine world. From Plato: divine transcendence, supreme goodness, theodicy (God is not the cause of evil, "
        "punishment is cathartic-pedagogical, virtue is sufficient for happiness, man is free and responsible). Cosmology "
        "inconceivable without the Timaeus. Psychology essentially answers the Phaedrus. Origen read and reread the Phaedo, "
        "Phaedrus, Republic, Timaeus, Laws, and Letters.",
        "p. 291-292, ll. 15430-15490",
        ["BIGG C., The Christian Platonists of Alexandria (Oxford 1886/1913)", "E. DE FAYE, Origène III p. 52-64, 80-87", "Hal KOCH, Pronoia und Paideusis p. 180-205, 243-268", "P. KOETSCHAU, Contre Celse intro I p. XL-XLII"],
    ),
    (
        "argument_origen_witness_aristotelism_influence_amand1945",
        "Origène — Influence aristotélicienne réelle (Amand 1945)",
        "aristotélisme",
        "Amand (p. 292) : Influence d'Aristote moins accusée mais réelle. Terminologie d'Origène dérive principalement "
        "d'Aristote autant que des Stoïciens. Habitude d'aborder un problème en passant en revue toutes les questions (les "
        "ἀπορίαι) = méthode du Stagirite. Origène emprunte la notion d'οὐσία rationnelle, ποιότητες, ὑποκείμενα. Sa "
        "psychologie est étroitement apparentée à celle du Περὶ ψυχῆς, et sa théorie du libre arbitre s'appuie en partie "
        "sur les analyses précises de l'Éthique Nicomachéenne. E. de Faye a mis cette influence aristotélicienne en lumière. "
        "Cf. Bardy, Origène et l'aristotélisme (Mélanges Glotz I, 1932, p. 75-83) : Origène connaît surtout des idées "
        "courantes, des définitions traditionnelles ; il adopte vis-à-vis du Stagirite une attitude défiante.",
        "Amand (p. 292): Aristotle's influence less marked but real. Origen's terminology derives chiefly from Aristotle "
        "as much as from Stoics. The habit of approaching a problem by reviewing all possible questions (the ἀπορίαι) = "
        "Stagirite's method. Origen borrows the notion of rational οὐσία, ποιότητες, ὑποκείμενα. His psychology is closely "
        "related to that of De anima, and his theory of free will partly relies on the precise analyses of the Nicomachean "
        "Ethics. E. de Faye highlighted this Aristotelian influence. Cf. Bardy, Origène et l'aristotélisme (Mélanges Glotz "
        "I, 1932, p. 75-83): Origen knows mostly common ideas and traditional definitions; he adopts a wary attitude toward "
        "the Stagirite.",
        "p. 292, ll. 15495-15530",
        ["E. DE FAYE, Origène III p. 87 note, 167-170, 172-178", "G. BARDY, Origène et l'aristotélisme, dans Mélanges Glotz I, Paris 1932, p. 75-83"],
    ),
    (
        "argument_origen_witness_stoicism_influence_amand1945",
        "Origène — Influence stoïcienne réelle (Amand 1945)",
        "stoïcisme",
        "Amand (p. 292-293) : Le stoïcisme primitif et le stoïcisme moyen de Posidonios ont profondément marqué "
        "l'élaboration du système origénien. Origène a sûrement lu et étudié des œuvres de Chrysippe, peut-être Zénon "
        "et Cléanthe, possiblement Posidonios. Le vocabulaire philosophique du IIIe s. est imprégné de stoïcisme : "
        "καθῆκον, κατόρθωμα, προκόπτων, σπουδαῖος, φαῦλος. Presque toute la terminologie anthropologique d'Origène, "
        "y compris τὸ ἐφ᾽ ἡμῖν, dérive de celle de Chrysippe. Origène emprunte à la morale du Portique de nombreuses "
        "définitions, notions, préceptes. À la théodicée stoïcienne, à la conception du Logos, à la théorie de la "
        "Providence (problème central chez Chrysippe), il prend de nombreux points de vue et arguments. **Mais sa "
        "mentalité n'est point stoïcienne** : aucune parenté spirituelle avec Chrysippe. Au point de vue philosophique, "
        "Origène se rattache au platonisme éclectique contemporain. Cf. von Arnim SVF I, Praefatio p. XLVI.",
        "Amand (p. 292-293): Early Stoicism and Posidonian Middle Stoicism profoundly shaped Origen's system. Origen "
        "certainly read and studied Chrysippus's works, perhaps Zeno and Cleanthes, possibly Posidonius. 3rd c. "
        "philosophical vocabulary is saturated with Stoicism: καθῆκον, κατόρθωμα, προκόπτων, σπουδαῖος, φαῦλος. Almost "
        "all of Origen's anthropological terminology, including τὸ ἐφ᾽ ἡμῖν, derives from Chrysippus. Origen borrows "
        "from Stoic ethics numerous definitions, concepts, and precepts. From Stoic theodicy, Logos conception, "
        "Providence theory (central problem for Chrysippus), he takes many viewpoints and arguments. **But his mentality "
        "is not Stoic**: no spiritual kinship with Chrysippus. Philosophically Origen belongs to contemporary eclectic "
        "Platonism. Cf. von Arnim SVF I, Praefatio p. XLVI.",
        "p. 292-293, ll. 15533-15625",
        ["H. von ARNIM, SVF I (1921 réimpr.) Praefatio p. XLVI + vol. IV (1924) index fontium p. 204-205 (78 références Origène→Stoïciens)", "Hal KOCH, Pronoia und Paideusis p. 205-216"],
    ),
    (
        "argument_origen_witness_middle_platonism_amand1945",
        "Origène — Influence médio-platonicienne + école d'Ammonios Saccas (Amand 1945)",
        "médio-platonisme",
        "Amand (p. 294-296) : Le médio-platonisme (Plutarque, Albinos, Atticos, Celse) a exercé une **influence directe "
        "et importante sur tous les points essentiels du système d'Origène**. Même éclectisme, même prépondérance des "
        "préoccupations religieuses et morales, même recul de l'intérêt pour le visible et les phénomènes naturels, "
        "même terminologie empruntée à diverses sources, mêmes problèmes (Dieu/Providence, cosmologie, insistance sur "
        "la liberté de la volonté). L'analyse du manuel d'Albinos par Hal Koch est révélatrice : même terminologie, "
        "mêmes problèmes, mêmes solutions partielles. Conclusion : Origène en tant que philosophe appartient naturellement "
        "à cette école platonicienne. **L'école d'Ammonios Saccas** continuait/transformait cette tradition médio-"
        "platonicienne, et fut d'une importance capitale pour la maturation philosophique du futur auteur du Περὶ "
        "ἀρχῶν. Ammonios = « premier néoplatonisme alexandrin ». Cf. Cadiou pour la reconstitution Némésios/Hiéroclès/"
        "Priscien d'Ammonios.",
        "Amand (p. 294-296): Middle Platonism (Plutarch, Albinus, Atticus, Celsus) exerted a **direct and important "
        "influence on all essential points** of Origen's system. Same eclecticism, same primacy of religious/moral "
        "concerns, same retreat of interest for the visible and natural phenomena, same terminology borrowed from "
        "various sources, same problems (God/Providence, cosmology, insistence on freedom of will). Hal Koch's analysis "
        "of Albinus's Didaskalikos is revealing: same terminology, same problems, same partial solutions. Conclusion: "
        "Origen as philosopher naturally belongs to this Platonic school. **Ammonius Saccas's school** continued/"
        "transformed this Middle Platonic tradition, and was capital for the philosophical maturation of the future "
        "author of De Principiis. Ammonius = 'first Alexandrian Neoplatonism'. Cf. Cadiou for the Nemesius/Hierocles/"
        "Priscianus reconstruction of Ammonius.",
        "p. 294-296, ll. 15630-15760",
        ["Hal KOCH, Pronoia und Paideusis p. 225-304 (notably p. 243-268 Albinos)", "R. CADIOU, La jeunesse d'Origène, Paris 1936, p. 184-203, 227-228 (Ammonios)"],
    ),
]:
    NEW_INSERTS.append(make_node(
        nid=nid,
        ntype="argument", label=label,
        period="Patristic", school="school_middle_platonism", role="amand1945_subarg",
        description=desc_fr,
        description_en=desc_en,
        md=md_base(
            page_range=locus_md.split(", ")[0],
            md_line_range=locus_md.split(", ")[1],
            chapter="Livre II Ch. V §I.3 (Influence réelle de la philosophie)",
            chapter_actual=f"Livre II Ch. V §I.3 — Influence {src_short} sur Origène",
            confidence=0.85 if src_short == "aristotélisme" else 0.9,
            cited_editions=citations,
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "amand_influence_target": src_short,
            },
        ),
    ))


# ============================================================================
# §II — ENVELOPPE Libre arbitre (1)
# ============================================================================

NEW_INSERTS.append(make_node(
    nid="argument_origen_witness_freewill_doctrine_envelope_amand1945",
    ntype="argument", label="Origène — Le libre arbitre dans le cadre de sa philosophie religieuse (Amand 1945 Livre II Ch. V §II)",
    period="Patristic", school=None, role="amand1945_witness_envelope",
    description=(
        "**Enveloppe argumentaire** regroupant les claims d'Amand sur la doctrine origénienne du libre arbitre (§II, "
        "p. 297-304). Pour Amand, le libre arbitre constitue **la pièce maîtresse du système de philosophie religieuse "
        "d'Origène**, considéré sous double aspect : dogme religieux (défini dans la préface de De Principiis comme "
        "doctrine de la prédication ecclésiastique) ET théorie rationnelle (élaborée philosophiquement au ch. III.1 du "
        "Περὶ ἀρχῶν περὶ αὐτεξουσίου). Origène y traite : préexistence des νόες, refroidissement par négligence du "
        "libre arbitre, hiérarchie ange-homme-démon, *possibilitas utriusque partis*, localisation dans la συγκατάθεσις, "
        "distinction liberté formelle / liberté réelle (cette dernière supposant l'aide du Logos).\n\n"
        "Amand suit les analyses de Klein 1894, Vinard 1911, de Faye, Hal Koch, Bardy, Völker pour identifier deux "
        "composantes constitutives : (1) un élément éthique-philosophique de provenance principalement aristotélo-"
        "stoïcienne ; (2) un élément chrétien-théologique d'inspiration néo-testamentaire (intervention de la grâce)."
    ),
    description_en=(
        "**Argumentative envelope** grouping Amand's claims on Origen's free will doctrine (§II, p. 297-304). For Amand, "
        "free will constitutes **the keystone of Origen's religious philosophy system**, considered in dual aspect: "
        "religious dogma (defined in the preface of De Principiis as ecclesiastical preaching doctrine) AND rational "
        "theory (philosophically elaborated in ch. III.1 of Peri Archon περὶ αὐτεξουσίου). Origen treats: preexistence "
        "of νόες, cooling through neglect of free will, hierarchy angel-human-demon, *possibilitas utriusque partis*, "
        "localization in συγκατάθεσις, distinction formal/real liberty (the latter presupposing the Logos's aid).\n\n"
        "Amand follows Klein 1894, Vinard 1911, de Faye, Hal Koch, Bardy, Völker to identify two constitutive components: "
        "(1) an ethical-philosophical element of chiefly Aristotelian-Stoic provenance; (2) a Christian-theological "
        "element of NT inspiration (intervention of grace)."
    ),
    md=md_base(
        page_range="p. 297-304",
        md_line_range="ll. 15715-16030",
        chapter="Livre II Ch. V §II",
        chapter_actual="Livre II Ch. V §II — Libre arbitre dogme + théorie",
        confidence=0.95,
        cited_editions=[
            "Origène, Traité des Principes I, Préface, 5, éd. Koetschau p. 12,8 — 13,6",
            "Origène, Traité des Principes III, 1-2, éd. Koetschau p. 195-256",
            "C. KLEIN, Die Freiheitslehre des Origenes (Strasbourg 1894)",
            "G. VINARD, Étude historique de la doctrine de la liberté humaine chez Origène (Angers 1911)",
            "G. BARDY, D.Th.C. XI, 2 (1932), col. 1536-1538",
            "W. VÖLKER, Das Vollkommenheitsideal p. 27-31",
        ],
        extra={
            "is_witness_argument": True,
            "amand_witness_rank": "primary_witness_n1_envelope",
            "amand_witness_role": "envelope_free_will_doctrine",
            "amand_judgement_quote_fr": "Le libre arbitre constitue une pièce maîtresse dans le système de philosophie religieuse d'Origène",
            "amand_envelope_subarguments": [
                "argument_origen_witness_freewill_dogma_status_amand1945",
                "argument_origen_witness_preexistence_souls_amand1945",
                "argument_origen_witness_possibilitas_utriusque_amand1945",
                "argument_origen_witness_synkatathesis_locus_amand1945",
                "argument_origen_witness_double_freedom_amand1945",
            ],
        },
    ),
))


# §II sub-args (5)

NEW_INSERTS.extend([
    make_node(
        nid="argument_origen_witness_freewill_dogma_status_amand1945",
        ntype="argument", label="Origène — Libre arbitre comme dogme apostolique-ecclésiastique (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 297-298) : Origène mentionne dans la préface du Traité des Principes le libre arbitre comme une des "
            "doctrines définies par la règle de foi et contenues dans la prédication ecclésiastique. Le passage cité par "
            "Amand (Princ. I, Préface 5, éd. Koetschau p. 12,8—13,6, version Rufin) déclare : « omnem animam rationabilem "
            "esse liberi arbitrii et uoluntatis ». **Étroite connexion** de trois doctrines : (1) affirmation de la croyance "
            "chrétienne à la liberté morale ; (2) nécessité de l'ascèse spirituelle délivrant l'âme des influences "
            "démoniaques ; (3) ardente polémique contre le fatalisme gnostique (déterminisme physique bien/mal) et le "
            "fatalisme astrologique. Origène ne se borne pas au dogme : il bâtit aussi une « imposante théorie περὶ "
            "αὐτεξουσίου ». La liberté est condition indispensable de moralité et de salut."
        ),
        description_en=(
            "Amand (p. 297-298): In the De Principiis preface Origen mentions free will as one of the doctrines defined by "
            "the rule of faith and contained in ecclesiastical preaching. The passage Amand cites (Princ. I, Preface 5, "
            "Koetschau p. 12,8—13,6, Rufin's version) declares: 'omnem animam rationabilem esse liberi arbitrii et uoluntatis'. "
            "**Tight connection** of three doctrines: (1) Christian belief in moral freedom; (2) necessity of spiritual "
            "ascesis freeing the soul from demonic influences; (3) ardent polemic against Gnostic fatalism (physical "
            "good/evil determinism) and astrological fatalism. Origen does not stop at dogma: he also builds an 'imposing "
            "theory περὶ αὐτεξουσίου'. Freedom is the indispensable condition of morality and salvation."
        ),
        md=md_base(
            page_range="p. 297-298",
            md_line_range="ll. 15715-15770",
            chapter="Livre II Ch. V §II",
            chapter_actual="Livre II Ch. V §II — Libre arbitre comme dogme ecclésiastique (Princ. I Préface 5)",
            confidence=0.9,
            cited_editions=["Origène, Traité des Principes I, Préface 5, éd. Koetschau GCS 22 Leipzig 1913, p. 12,8 — 13,6 (version latine Rufin)"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidenced_by_passage": ["sc268_origenes_peri_archon_iii_chap1", "sc268_origenes_peri_archon_iii_chap1_en"],
                "amand_judgement_quote_fr": "Le libre arbitre constitue une pièce maîtresse dans le système de philosophie religieuse d'Origène",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_preexistence_souls_amand1945",
        ntype="argument", label="Origène — Préexistence des νόες et refroidissement par négligence (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 299-301) : Inégalité actuelle entre créatures intellectuelles n'est pas un fait primitif. À l'origine, "
            "toutes furent créées semblables et égales (Princ. II.9,6 Koetschau p. 169,22—170,17). L'exercice du libre arbitre "
            "a entraîné les uns au progrès, les autres à la défaillance. À l'exception de l'esprit qui par sa fidélité devint "
            "esprit du Christ, tous les νόες se laissèrent distraire et se refroidirent. **D'esprits ils devinrent âmes** "
            "(ψυχαί), âmes inégales par suite de l'inégal refroidissement. Selon la gravité de la chute : Chérubins → "
            "Puissances → Trônes → Anges (incl. anges des corps célestes) → hommes → démons. Chaque âme reçoit un corps "
            "proportionné. Rien n'est définitivement perdu : la nature tombée garde l'usage du libre arbitre, peut "
            "redevenir esprit. Mutabilité = racine métaphysique du mal moral."
        ),
        description_en=(
            "Amand (p. 299-301): Current inequality between intellectual creatures is not primitive. Originally, all were "
            "created similar and equal (Princ. II.9,6 Koetschau p. 169,22—170,17). Use of free will led some to progress, "
            "others to negligence. Except the spirit that through faithfulness became Christ's spirit, all νόες allowed "
            "themselves to be distracted and cooled. **From spirits they became souls** (ψυχαί), unequal souls following "
            "unequal cooling. According to severity of fall: Cherubim → Powers → Thrones → Angels (incl. heavenly bodies' "
            "angels) → humans → demons. Each soul receives a proportioned body. Nothing is definitively lost: fallen "
            "nature retains free will, can again become spirit. Mutability = metaphysical root of moral evil."
        ),
        md=md_base(
            page_range="p. 299-301",
            md_line_range="ll. 15790-15860",
            chapter="Livre II Ch. V §II",
            chapter_actual="Livre II Ch. V §II — Préexistence des νόες, hiérarchie de la chute (Princ. II.9)",
            confidence=0.85,
            cited_editions=["Origène, Traité des Principes II.9.2 éd. Koetschau p. 165,17 — 166,11", "Princ. II.9.6 éd. Koetschau p. 169,22 — 170,17", "GILSON-BÖHNER, G.Chr.Phil. p. 60-62", "G. BARDY, Origène. Coll. Les moralistes chrétiens. Paris 1931, p. 39-40 (trad. modifiée par Amand)"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Princ. II.9.2 + II.9.6 absent du corpus KG (SC268 ne couvre que Livre III.1 + IV.1-3)",
                "cites_primary_source_target": "work_de_principiis_origen_230s_v2w3x4y5",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_possibilitas_utriusque_amand1945",
        ntype="argument", label="Origène — Possibilitas utriusque partis (laudis et culpae capax) (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 299) : La *possibilitas utriusque partis* constitue **la propriété essentielle et active de l'être "
            "créé raisonnable** (λογικὸν ζῷον). Origène (Princ. I.5,2 éd. Koetschau p. 70,4-7) : « toute créature intellectuelle "
            "est *laudis et culpae capax* ; laudis, si secundum rationem, quam in se habet, ad meliora proficiat, culpae, "
            "si rationem recti tenoremque declinet ; propter quod recte etiam poenis ac suppliciis subiacet ». **L'homme "
            "n'est pas comme Dieu bon οὐσιωδῶς, mais seulement bon κατὰ συμβεβηκός**. Cette faculté d'auto-détermination "
            "spontanée est ce qui rend possible vertu, vice, mérite, démérite, sanctions d'outre-tombe. Amand cite "
            "également CC IV.3 (éd. Koetschau I p. 276,18-19) où Origène écrit : « ἀρετῆς μὲν ἐὰν ἀνέλῃς τὸ ἑκούσιον, "
            "ἀνεῖλες αὐτῆς καὶ τὴν οὐσίαν »."
        ),
        description_en=(
            "Amand (p. 299): The *possibilitas utriusque partis* constitutes **the essential and active property of the "
            "rational created being** (λογικὸν ζῷον). Origen (Princ. I.5,2 Koetschau p. 70,4-7): 'every intellectual "
            "creature is *laudis et culpae capax*; laudis, si secundum rationem, quam in se habet, ad meliora proficiat, "
            "culpae, si rationem recti tenoremque declinet; propter quod recte etiam poenis ac suppliciis subiacet'. "
            "**Man is not good οὐσιωδῶς (essentially) as God is, but only κατὰ συμβεβηκός (accidentally)**. This faculty "
            "of spontaneous self-determination is what makes virtue, vice, merit, demerit, and eschatological sanctions "
            "possible. Amand also cites CC IV.3 (Koetschau I p. 276,18-19): 'ἀρετῆς μὲν ἐὰν ἀνέλῃς τὸ ἑκούσιον, ἀνεῖλες "
            "αὐτῆς καὶ τὴν οὐσίαν' (remove the voluntary from virtue and you remove its very essence)."
        ),
        md=md_base(
            page_range="p. 299",
            md_line_range="ll. 15777-15805",
            chapter="Livre II Ch. V §II",
            chapter_actual="Livre II Ch. V §II — Possibilitas utriusque partis (Princ. I.5,2 + CC IV.3)",
            confidence=0.9,
            cited_editions=["Origène, Princ. I.5,2 éd. Koetschau p. 70,4-7 (Rufin)", "Origène, Contre Celse IV.3 éd. Koetschau I p. 276,18-19"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidenced_by_passage": ["sc268_origenes_peri_archon_iii_chap1", "sc268_origenes_peri_archon_iii_chap1_en"],
                "evidence_pending": True,
                "evidence_pending_reason": "Princ. I.5,2 (Livre I) absent du SC268-corpus disponible. CC IV.3 hors couverture SC132 (livres I-II uniquement)",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_synkatathesis_locus_amand1945",
        ntype="argument", label="Origène — Libre arbitre localisé dans la συγκατάθεσις (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 302-303) : Origène localise précisément le libre arbitre dans la **συγκατάθεσις** (assentiment). "
            "Le point de départ de la démonstration origénienne (Princ. III.1, 2-5, éd. Koetschau p. 196,3—201,6) est la "
            "hiérarchie des êtres. Seuls les êtres raisonnables ont la faculté de choisir entre différentes φαντασίαι "
            "laquelle ils veulent suivre, et d'accorder à telle d'entre elles leur assentiment, συγκατάθεσις. **Ce qui ne "
            "dépend pas de nous, c'est la représentation ; ce qui dépend de nous (τὸ ἐφ᾽ ἡμῖν), c'est le jugement et le "
            "choix**. Amand note (note 1 p. 303) la **notable ressemblance** entre ce chapitre περὶ αὐτεξουσίου et de "
            "nombreux passages du Manuel et des Entretiens d'Épictète, ainsi qu'avec le Περὶ εἱμαρμένης d'Alexandre "
            "d'Aphrodise (mêmes idées, même terminologie) — constatation déjà faite par Hal Koch."
        ),
        description_en=(
            "Amand (p. 302-303): Origen precisely locates free will in **συγκατάθεσις** (assent). The starting point of "
            "Origen's demonstration (Princ. III.1, 2-5, Koetschau p. 196,3—201,6) is the hierarchy of beings. Only "
            "rational beings have the faculty of choosing among different φαντασίαι which one they will follow, and of "
            "granting their assent (συγκατάθεσις) to a specific one. **What does not depend on us is the representation; "
            "what depends on us (τὸ ἐφ᾽ ἡμῖν) is the judgment and the choice**. Amand notes (n. 1 p. 303) the **notable "
            "resemblance** between this περὶ αὐτεξουσίου chapter and numerous passages of Epictetus's Encheiridion and "
            "Discourses, as well as with Alexander of Aphrodisias's Peri Heimarmenes (same ideas, same terminology) — "
            "observation already made by Hal Koch."
        ),
        md=md_base(
            page_range="p. 302-303",
            md_line_range="ll. 15900-15960",
            chapter="Livre II Ch. V §II",
            chapter_actual="Livre II Ch. V §II — Synkatathesis comme locus du libre arbitre (Princ. III.1,2-5)",
            confidence=0.9,
            cited_editions=["Origène, Princ. III.1,2-5 éd. Koetschau p. 196,3 — 201,6", "Épictète, Manuel et Entretiens (analogie terminologique signalée par Hal Koch)", "Alexandre d'Aphrodise, Περὶ εἱμαρμένης (analogie signalée par Hal Koch)"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidenced_by_passage": ["sc268_origenes_peri_archon_iii_chap1", "sc268_origenes_peri_archon_iii_chap1_en"],
                "amand_philosophical_dependencies": ["Epictetus (Encheiridion + Discourses)", "Alexander of Aphrodisias (De Fato)"],
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_double_freedom_amand1945",
        ntype="argument", label="Origène — Liberté formelle / liberté réelle (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 304 + note 2) : Origène distingue (Princ. III.6,1 éd. Koetschau p. 280,6-17) deux ordres de liberté : "
            "**(1) Liberté formelle** = la liberté du choix entre le bien et le mal, la faculté de se décider pour l'un "
            "ou pour l'autre. L'homme la possède en propre. **(2) Liberté réelle** = celle qui consiste à se décider de "
            "fait pour le bien et, par là, à devenir semblable à Dieu. L'homme doit se l'approprier, en mettant à profit "
            "le secours gracieux du Logos. Amand (citant C. Klein 1894 et W. Völker 1931) note que cette distinction "
            "comporte **deux éléments constitutifs** : (a) un élément éthique-philosophique de provenance principalement "
            "aristotélo-stoïcienne (liberté formelle, choix indéterminé) ; (b) un élément chrétien-théologique "
            "d'inspiration néo-testamentaire (liberté réelle, intervention de la grâce). Origène n'envisage presque pas "
            "le problème pélagien (alors inactuel) du rapport liberté humaine / grâce, mais il aurait accordé sans "
            "hésitation que l'homme ne peut rien accomplir pour son salut sans l'aide divine."
        ),
        description_en=(
            "Amand (p. 304 + n. 2): Origen distinguishes (Princ. III.6,1 Koetschau p. 280,6-17) two orders of freedom: "
            "**(1) Formal freedom** = freedom of choice between good and evil, the faculty to decide for one or the other. "
            "Man possesses this properly. **(2) Real freedom** = freedom that consists in actually deciding for the good "
            "and thereby becoming like God. Man must appropriate this, leveraging the gracious aid of the Logos. Amand "
            "(citing C. Klein 1894 and W. Völker 1931) notes this distinction has **two constitutive elements**: "
            "(a) ethical-philosophical of chiefly Aristotelian-Stoic provenance (formal freedom, indeterminate choice); "
            "(b) Christian-theological of NT inspiration (real freedom, intervention of grace). Origen barely considers "
            "the Pelagian problem (then non-actual) of human-freedom/grace relation, but he would have conceded without "
            "hesitation that man cannot accomplish anything for his salvation without divine aid."
        ),
        md=md_base(
            page_range="p. 304 + note 2",
            md_line_range="ll. 16000-16040",
            chapter="Livre II Ch. V §II (fin)",
            chapter_actual="Livre II Ch. V §II — Distinction liberté formelle / liberté réelle (Princ. III.6,1)",
            confidence=0.85,
            cited_editions=["Origène, Princ. III.6,1 éd. Koetschau p. 280,6-17", "C. KLEIN, Die Freiheitslehre des Origenes (1894) p. 74", "W. VÖLKER, Das Vollkommenheitsideal des Origenes (1931) p. 28-30"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Princ. III.6,1 absent du corpus KG (SC268 disponible : III.1 + IV.1-3)",
                "cites_primary_source_target": "work_de_principiis_origen_230s_v2w3x4y5",
                "amand_two_constitutive_elements": [
                    "ethical-philosophical Aristotelian-Stoic (formal freedom)",
                    "Christian-theological NT (real freedom + grace)",
                ],
            },
        ),
    ),
])


# ============================================================================
# §III — ENVELOPPE Antiastrologique (1)
# ============================================================================

NEW_INSERTS.append(make_node(
    nid="argument_origen_witness_antiastrological_dissertation_envelope_amand1945",
    ntype="argument", label="Origène — Polémique antiastrologique + dissertation Comm. Gen. III (Amand 1945 Livre II Ch. V §III)",
    period="Patristic", school=None, role="amand1945_witness_envelope",
    description=(
        "**Enveloppe argumentaire** regroupant les claims d'Amand sur la polémique antiastrologique d'Origène (§III, "
        "p. 304-318). Amand consacre 11 pages à cette dissertation qu'il considère comme **le monument anti-astrologique "
        "d'Origène** — partiellement conservée via la Philocalie 23 de Basile et Grégoire de Nazianze (Robinson 1893, "
        "p. 187-212), et transcrite quasi-littéralement par Eusèbe dans Préparation Évangélique VI.11.1-81.\n\n"
        "La dissertation antiastrologique (Comm. Gen. III) comporte **trois parties** identifiées par Amand : "
        "(1) première partie — réfutation par arguments moraux carnéadiens (Phil. 23.1-2) + premier examen prescience "
        "(Phil. 23.3-5) ; (2) deuxième partie — quatre problèmes méthodiques (Phil. 23.6-21) ; (3) troisième partie — "
        "longue citation pseudo-clémentine ch. 14 (Phil. 23.22).\n\n"
        "Origène concentre l'attaque sur les conséquences morales du fatalisme astrologique (ruine du libre arbitre, "
        "ruine de la responsabilité, ruine de la morale chrétienne), non pas tant sur l'absurdité physique."
    ),
    description_en=(
        "**Argumentative envelope** grouping Amand's claims on Origen's anti-astrological polemic (§III, p. 304-318). "
        "Amand devotes 11 pages to this dissertation he considers **Origen's anti-astrological monument** — partially "
        "preserved through the Philocalia 23 of Basil and Gregory of Nazianzus (Robinson 1893, p. 187-212), and almost "
        "verbatim transcribed by Eusebius in Praeparatio Evangelica VI.11.1-81.\n\n"
        "The anti-astrological dissertation (Comm. Gen. III) has **three parts** identified by Amand: "
        "(1) first part — refutation by Carneadean moral arguments (Phil. 23.1-2) + preliminary foreknowledge examination "
        "(Phil. 23.3-5); (2) second part — four methodical problems (Phil. 23.6-21); (3) third part — long pseudo-"
        "Clementine ch. 14 citation (Phil. 23.22).\n\n"
        "Origen concentrates the attack on the moral consequences of astrological fatalism (ruin of free will, ruin of "
        "responsibility, ruin of Christian morality), rather than on physical absurdity."
    ),
    md=md_base(
        page_range="p. 304-318",
        md_line_range="ll. 16030-16560",
        chapter="Livre II Ch. V §III",
        chapter_actual="Livre II Ch. V §III — Polémique antiastrologique (incl. dissertation Comm. Gen. III dans Philocalie 23)",
        confidence=0.95,
        cited_editions=[
            "ROBINSON J.A., The Philocalia of Origen, Cambridge UP 1893, p. 187-212",
            "DINDORF W. (éd.), Eusebii Caesariensis opera. Praeparatio evangelica I. Leipzig 1867, p. 324-343 (= MIGNE PG 21,477B—505A reproduction Viger)",
            "MESSERSCHMIDT F., Himmelsbuch und Sternenschrift, dans Römische Quartalschrift 39 (1931) p. 63-69",
            "C. SCHMIDT, Studien zu den Pseudo-Clementinen, TU 46,1 Leipzig 1929",
            "R. CADIOU, Origène et les Reconnaissances clémentines, dans RechSR 20 (1930) p. 506-528",
            "P. DUHEM, Le système du monde II Paris 1914, p. 180-189, 191-192, 393-394 (précession équinoxes)",
        ],
        extra={
            "is_witness_argument": True,
            "amand_witness_rank": "primary_witness_n1_envelope",
            "amand_witness_role": "envelope_antiastrological_dissertation",
            "amand_envelope_subarguments": [
                "argument_origen_witness_antiastrology_moral_attack_amand1945",
                "argument_origen_witness_diss_problem1_prescience_amand1945",
                "argument_origen_witness_diss_argos_logos_refutation_amand1945",
                "argument_origen_witness_diss_problem2_signs_not_causes_amand1945",
                "argument_origen_witness_diss_problem3_human_ignorance_amand1945",
                "argument_origen_witness_diss_problem4_angelic_knowledge_amand1945",
                "argument_origen_witness_diss_part3_pseudo_clementine_amand1945",
                "argument_origen_witness_diss_precession_equinoxes_amand1945",
            ],
        },
    ),
))


# §III sub-args (8)

NEW_INSERTS.extend([
    make_node(
        nid="argument_origen_witness_antiastrology_moral_attack_amand1945",
        ntype="argument", label="Origène — Attaque morale (pas physique) du fatalisme astrologique (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 305-306) : « Si Origène a combattu aussi énergiquement l'astrologie contemporaine, ce n'est pas tant "
            "parce qu'il la jugeait absurde, que parce qu'il estimait qu'elle ruinait la morale en niant la liberté de "
            "l'homme. » Origène concentre presque toutes ses attaques sur **ce grief capital** : la généthlialogie favorise "
            "le fatalisme et entraîne les conséquences les plus désastreuses pour la morale en abolissant la responsabilité. "
            "Il répète sans grande conviction les arguments carnéadiens usés (jumeaux, νόμιμα βαρβαρικά, impossibilité "
            "exigences astrologues) ; mais insiste énergiquement sur l'argumentation morale antifataliste, car cette fois "
            "le libre arbitre est en jeu. Amand note que **Origène ne formule pas d'objections pressantes contre le dogme "
            "fondamental de l'apotélesmatique** : il n'ose contester sa possibilité ni même sa réalité (rester de son "
            "siècle). Il accepte avec Plotin la distinction astres-signes / astres-causes."
        ),
        description_en=(
            "Amand (p. 305-306): 'If Origen fought contemporary astrology so energetically, it is not so much because he "
            "judged it absurd, but because he believed it ruined morality by denying human freedom.' Origen concentrates "
            "almost all his attacks on **this capital grievance**: genethlialogy favors fatalism and entails the most "
            "disastrous consequences for morality by abolishing responsibility. He repeats without great conviction the "
            "worn Carneadean arguments (twins, νόμιμα βαρβαρικά, impossibility of astrologers' demands); but energetically "
            "insists on the anti-fatalist moral argumentation, because this time free will is at stake. Amand notes that "
            "**Origen does not formulate pressing objections against the fundamental dogma of apotelesmatic**: he dares "
            "not contest its possibility or even its reality (a man of his century). He accepts with Plotinus the "
            "distinction stars-as-signs / stars-as-causes."
        ),
        md=md_base(
            page_range="p. 305-306",
            md_line_range="ll. 16104-16170",
            chapter="Livre II Ch. V §III.1",
            chapter_actual="Livre II Ch. V §III.1 — Attitude d'Origène envers fatalisme astrologique et apotélesmatique",
            confidence=0.9,
            cited_editions=["Origène, Comm. Jean II.3 éd. Preuschen GCS 10 Leipzig 1903, p. 56,9-28", "Plotin, Ennéades III.1 ch. 5-6 + II.3 ch. 1, 6, 7"],
            extra={"amand_witness_rank": "primary_witness_n1_subarg", "is_witness_argument": True},
        ),
    ),
    make_node(
        nid="argument_origen_witness_diss_problem1_prescience_amand1945",
        ntype="argument", label="Origène — Premier théologien à résoudre prescience vs libre arbitre (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 309-311) : « **Origène est le premier théologien chrétien qui ait envisagé dans toute son ampleur la "
            "redoutable difficulté que la prescience divine soulevait à l'encontre de la libre détermination de la volonté "
            "humaine.** » Solution proposée (Phil. 23.7-11, Robinson p. 194-198) : Dieu a une connaissance si compréhensive "
            "et pénétrante de sa créature qu'il sait à l'avance comment chacune usera de sa liberté. Grâce à cette prescience, "
            "le Créateur dirige l'économie de sa Providence de telle sorte qu'elle corresponde et s'adapte exactement aux "
            "libres actions des hommes, et qu'il accorde à chaque individu l'éducation spirituelle dont celui-ci a besoin. "
            "**Les événements humains ne sont donc point produits par un Destin tout-puissant** (Stoïciens), ni le résultat "
            "de la conjonction Destin + actions libres (Platoniciens moyens). Ils sont la conséquence de la liberté + "
            "l'éducation des êtres libres par le divin Pédagogue. Amand : « solution qui dans l'ensemble a été entérinée par "
            "la théologie ecclésiastique postérieure »."
        ),
        description_en=(
            "Amand (p. 309-311): '**Origen is the first Christian theologian to have considered in all its scope the "
            "formidable difficulty that divine foreknowledge raised against the free determination of human will.**' "
            "Proposed solution (Phil. 23.7-11, Robinson p. 194-198): God has a knowledge so comprehensive and penetrating "
            "of His creature that He knows in advance how each will use its freedom. Through this foreknowledge, the "
            "Creator directs the economy of His Providence so that it corresponds and adapts exactly to humans' free "
            "actions, granting each individual the spiritual education they need. **Human events are therefore not "
            "produced by an all-powerful Destiny** (Stoics), nor the result of Destiny + free actions conjunction "
            "(Middle Platonists). They are the consequence of freedom + the education of free beings by the divine "
            "Pedagogue. Amand: 'solution which overall was endorsed by subsequent ecclesiastical theology'."
        ),
        md=md_base(
            page_range="p. 309-311",
            md_line_range="ll. 16320-16410",
            chapter="Livre II Ch. V §III.2 (Phil. 23.7-11)",
            chapter_actual="Livre II Ch. V §III.2 — Problème 1 : prescience vs libre arbitre, solution origénienne entérinée",
            confidence=0.95,
            cited_editions=["Origène, Philocalie 23.7-11 éd. Robinson p. 194-198", "Origène, Comm. Rom. tome I dans Philocalie ch. 25 éd. Robinson p. 226-231", "Origène, Comm. Psaume 4 dans Philocalie ch. 26 éd. Robinson p. 231-241", "Origène, Comm. Matt., Philocalie ch. 27 sur Exode 10,27 'le Seigneur endurcit le cœur du Pharaon' p. 242-256", "Origène, Contre Celse III.38 éd. Koetschau I p. 234,30—235,5", "Hal KOCH, Pronoia und Paideusis p. 114-117, 128-131"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.7-11 + Comm. Rom. + Comm. Psaume 4 absents du corpus KG (work-shells seulement)",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_first_christian_prescience_problem": True,
                "amand_judgement_quote_fr": "Origène est le premier théologien chrétien qui ait envisagé dans toute son ampleur la redoutable difficulté que la prescience divine soulevait à l'encontre de la libre détermination de la volonté humaine",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_diss_argos_logos_refutation_amand1945",
        ntype="argument", label="Origène — Réfutation de l'Argos Logos via prophéties Judas/Œdipe (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 311) : Les compilateurs de la Philocalie ont joint à la discussion sur la prescience une **copieuse "
            "citation du Contre Celse II.20** (sections 12-13 de la Philocalie 23, Robinson p. 199-201). Origène y fait "
            "voir comment la prescience divine ne porte aucun préjudice au libre arbitre. Il se réfère à : (1) la prophétie "
            "de la trahison de Judas (Psaume 109,16 selon LXX) ; (2) la prédiction du meurtre de Laios par son propre fils, "
            "Œdipe (Euripide, Phéniciennes vers 18-20). Il **décèle ensuite le sophisme de l'ἀργὸς λόγος** (lazy argument) "
            "qu'il réfute. Ce passage = la matière du Contre Celse II.20, déjà partiellement traitée dans le KG par "
            "`argument_origen_argos_logos` (Phase 9 deep review). Amand confirme : la dissertation antiastrologique du "
            "Comm. Gen. III réutilise la matière de CC II.20 — preuve indirecte de la cohérence du système anti-astrologique."
        ),
        description_en=(
            "Amand (p. 311): Philocalia compilers attached to the foreknowledge discussion a **copious citation from Contra "
            "Celsum II.20** (sections 12-13 of Philocalia 23, Robinson p. 199-201). Origen shows there how divine foreknowledge "
            "in no way prejudices free will. He refers to: (1) the prophecy of Judas's betrayal (Psalm 109,16 LXX); "
            "(2) the prediction of Laius's murder by his own son Oedipus (Euripides, Phoenissae vv. 18-20). He **then "
            "detects the sophism of the ἀργὸς λόγος** (lazy argument) which he refutes. This passage = the material of "
            "Contra Celsum II.20, already partially treated in the KG by `argument_origen_argos_logos` (Phase 9 deep "
            "review). Amand confirms: the anti-astrological dissertation of Comm. Gen. III reuses CC II.20 material — "
            "indirect proof of the anti-astrological system's coherence."
        ),
        md=md_base(
            page_range="p. 311",
            md_line_range="ll. 16414-16435",
            chapter="Livre II Ch. V §III.2 (Phil. 23.12-13)",
            chapter_actual="Livre II Ch. V §III.2 — Argos Logos réfuté via Judas+Œdipe (Phil. 23.12-13 = excerpt CC II.20)",
            confidence=0.9,
            cited_editions=["Origène, Philocalie 23.12-13 éd. Robinson p. 199-201 (= excerpt Contre Celse II.20)", "Psaume 109,16 (LXX)", "Euripide, Phéniciennes vv. 18-20"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidenced_by_passage": ["sc132_origenes_contra_celsum_ii_par20", "sc132_origenes_contra_celsum_ii_par20_en"],
                "amand_cross_ref_existing_node": "argument_origen_argos_logos (Phase 9 deep review)",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_diss_problem2_signs_not_causes_amand1945",
        ntype="argument", label="Origène — Astres = signes, non causes efficientes : 4 arguments (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 311-313) : **Problème 2** — Origène pose en thèse que les astres ne sont nullement causes efficientes "
            "de la destinée et des actions humaines, mais qu'ils se bornent à les signifier (σημαντικοί, non ποιητικοί). "
            "Quatre arguments alignés (Phil. 23.14-16, Robinson p. 202-205) : **(1)** Si une configuration actuelle cause les "
            "événements futurs, elle ne peut causer ceux qui lui sont antérieurs ; mais les astrologues prétendent que "
            "l'horoscope d'un nouveau-né renseigne sur ses frères et ses parents : absurde. **(2)** Le sort heureux ou "
            "malheureux d'un homme causé par configuration de naissance, est aussi produit ou annoncé par les configurations "
            "présidant à la naissance d'autrui (parents, frères, conjoints, enfants, domestiques) — absurde. **(3)** Argument "
            "des νόμιμα βαρβαρικά [carnéadien] : Juifs circoncis le 8e jour, Arabes à 13 ans, Éthiopiens rotule enlevée, "
            "Amazones mamelle coupée — tous ne peuvent être nés sous la même position des astres. **(4)** Argument ad hominem "
            "aux devins : inconséquence — auguraux/haruspice/astrométéorologie n'accordent valeur de signe, mais "
            "généthlialogie accorde action physique."
        ),
        description_en=(
            "Amand (p. 311-313): **Problem 2** — Origen posits that stars are by no means efficient causes of destiny and "
            "human actions, but merely signify them (σημαντικοί, not ποιητικοί). Four aligned arguments (Phil. 23.14-16, "
            "Robinson p. 202-205): **(1)** If a current configuration causes future events, it cannot cause prior ones; "
            "but astrologers claim a newborn's horoscope informs about his siblings and parents: absurd. **(2)** A man's "
            "fate (caused by his birth configuration) is also produced or announced by configurations presiding over "
            "others' births (parents, siblings, spouse, children, servants) — absurd. **(3)** Argument of νόμιμα βαρβαρικά "
            "[Carneadean]: Jews circumcised on day 8, Arabs at 13 years, Ethiopians have kneecap removed, Amazons "
            "have breast cut — all cannot have been born under same star position. **(4)** Ad hominem argument to diviners: "
            "inconsistency — augury/haruspicy/astrometeorology grant only sign value, but genethlialogy grants physical action."
        ),
        md=md_base(
            page_range="p. 311-313",
            md_line_range="ll. 16440-16500",
            chapter="Livre II Ch. V §III.2 (Phil. 23.14-16)",
            chapter_actual="Livre II Ch. V §III.2 — Problème 2 : 4 arguments contre causalité astrale efficiente",
            confidence=0.9,
            cited_editions=["Origène, Philocalie 23.14-16 éd. Robinson p. 202-205", "Plotin, Ennéades III.1 ch. 5-6 et II.3 ch. 7 (conception analogue 'ciel livre de Dieu')"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.14-16 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_carneadean_filiation": "Argument 3 (νόμιμα βαρβαρικά) explicitement carnéadien",
                "amand_sub_arguments": [
                    {"locus": "Phil. 23.14-15", "topic": "Configurations actuelles ne peuvent causer événements antérieurs"},
                    {"locus": "Phil. 23.16 §1", "topic": "Absurdité horoscope d'autrui"},
                    {"locus": "Phil. 23.16 §2", "topic": "νόμιμα βαρβαρικά carnéadien (rituels simultanés)"},
                    {"locus": "Phil. 23.16 §3", "topic": "Inconséquence ad hominem des devins"},
                ],
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_diss_problem3_human_ignorance_amand1945",
        ntype="argument", label="Origène — Problème 3 : ignorance humaine des signes (4 arguments) (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 313-315) : **Problème 3** — L'homme ne peut acquérir une connaissance exacte des événements et "
            "actions humaines annoncés par les configurations astrales. Quatre arguments (Phil. 23.17-19, Robinson "
            "p. 205-208) : **(1)** Imprécision de l'instant de naissance vs. minute zodiacale (les astrologues poussent "
            "jusqu'aux tierces) → différences de mœurs et destinées chez les jumeaux. **(2)** **Précession des équinoxes "
            "d'Hipparque** : les astrologues calculent sur le ζῳδιακὸν κύκλον théorique (νοητὸν δωδεκατημόριον), tandis "
            "que les constellations réelles (μορφώματα) se sont décalées par mouvement séculaire de 1° tous les 100 ans. "
            "Tous calculs astrologiques portent donc sur des entités abstraites différentes des signes réels. Amand : "
            "« Origène est le premier ou l'un des premiers » à mobiliser cette astronomie. Cf. Duhem II p. 191-192, 393-394. "
            "Basile reprend ce point dans Hexaéméron VI.5. **(3)** Mélange d'influences contraires entre planètes maléfiques/"
            "bénéfiques que les astrologues ne peuvent rigoureusement apprécier. **(4)** Erreurs avouées des astrologues : "
            "ils se trompent plus souvent qu'ils ne prédisent (citation Isaïe 47,13 ; exégèse Testament des 12 Patriarches/Aser 7)."
        ),
        description_en=(
            "Amand (p. 313-315): **Problem 3** — Man cannot acquire exact knowledge of events and human actions announced "
            "by astral configurations. Four arguments (Phil. 23.17-19, Robinson p. 205-208): **(1)** Imprecision of birth "
            "moment vs. zodiacal minute (astrologers push to thirds) → differences in morals and destinies of twins. "
            "**(2)** **Hipparchus's precession of equinoxes**: astrologers calculate on theoretical ζῳδιακὸν κύκλον "
            "(νοητὸν δωδεκατημόριον), while real constellations (μορφώματα) shifted by secular 1°/100 years motion. All "
            "astrological calculations therefore concern abstract entities different from real signs. Amand: 'Origen is "
            "the first or one of the first' to mobilize this astronomy. Cf. Duhem II p. 191-192, 393-394. Basil repeats "
            "this point in Hexaemeron VI.5. **(3)** Mixing of contrary influences between malefic/benefic planets that "
            "astrologers cannot rigorously assess. **(4)** Astrologers' admitted errors: they are wrong more often than "
            "they predict correctly (citation Isaiah 47,13; exegesis Testament of 12 Patriarchs/Asher 7)."
        ),
        md=md_base(
            page_range="p. 313-315",
            md_line_range="ll. 16510-16575",
            chapter="Livre II Ch. V §III.2 (Phil. 23.17-19)",
            chapter_actual="Livre II Ch. V §III.2 — Problème 3 : ignorance humaine des signes (4 arguments)",
            confidence=0.9,
            cited_editions=["Origène, Philocalie 23.17-19 éd. Robinson p. 205-208", "Isaïe 47,13", "Testament des 12 Patriarches, Testament d'Aser 7", "P. DUHEM, Le système du monde II Paris 1914, p. 191-192, 393-394", "W. GUNDEL, Nachträge à Boll-Bezold-Gundel, Sternglaube und Sterndeutung (Leipzig 1931) p. 131-132", "BASILE, Hexaéméron VI.5 PG 29.129,14-25 (démarquage habilement)"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.17-19 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_first_precession_polemicist": True,
                "amand_scientific_signature": "Précession des équinoxes (Hipparque) mobilisée par Origène contre l'astrologie scientifique",
                "amand_basil_transmission": "Basile démarque Origène habilement dans Hexaéméron VI.5",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_diss_problem4_angelic_knowledge_amand1945",
        ntype="argument", label="Origène — Problème 4 : connaissance des signes réservée aux anges (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 315-316) : **Problème 4** — La connaissance exacte des astres et des événements signifiés n'est "
            "accessible qu'aux Puissances supérieures à l'homme, aux anges. Dieu a créé les luminaires comme signes en "
            "faveur de ses anges. **Du soleil, de la lune et des étoiles, le Démiurge a fait une mouvante écriture, "
            "formée de lettres et de caractères tracés de sa main, afin que les anges et les Puissances divines (δυνάμεις "
            "θεῖαι) puissent lire les σημεῖα τοῦ θεοῦ**. Ces signes célestes préfigurent tous les événements cosmiques, "
            "depuis la création jusqu'à la consommation des choses. Ce sont l'**ἀξία βίβλος τοῦ θεοῦ** (le livre digne de "
            "Dieu). Double but : (a) instruire et réjouir les Puissances célestes en leur découvrant mystères divins ; "
            "(b) leur intimer des ordres précis pour leurs missions auprès des hommes. Conclusion : « les démons, s'ils "
            "exécutent des actions préfigurées par les corps célestes, ne les font point parce qu'ils lisent à découvert "
            "le livre de Dieu, mais seulement parce qu'ils agissent volontairement et conformément à leur malice »."
        ),
        description_en=(
            "Amand (p. 315-316): **Problem 4** — Exact knowledge of stars and signified events is accessible only to "
            "Powers superior to humans, to angels. God created luminaries as signs in favor of His angels. **From the sun, "
            "moon, and stars, the Demiurge made a moving writing, formed of letters and characters traced by His hand, "
            "so that angels and divine Powers (δυνάμεις θεῖαι) can read the σημεῖα τοῦ θεοῦ**. These celestial signs "
            "prefigure all cosmic events, from creation to the consummation of things. They are the **ἀξία βίβλος τοῦ "
            "θεοῦ** (the book worthy of God). Dual purpose: (a) instruct and gladden Celestial Powers by revealing divine "
            "mysteries; (b) issue precise orders for their missions to humans. Conclusion: 'demons, if they execute "
            "actions prefigured by celestial bodies, do not do so because they openly read God's book, but only because "
            "they act voluntarily and according to their malice'."
        ),
        md=md_base(
            page_range="p. 315-316",
            md_line_range="ll. 16580-16630",
            chapter="Livre II Ch. V §III.2 (Phil. 23.20-21)",
            chapter_actual="Livre II Ch. V §III.2 — Problème 4 : ἀξία βίβλος τοῦ θεοῦ + démons agissent volontairement",
            confidence=0.85,
            cited_editions=["Origène, Philocalie 23.20-21 éd. Robinson p. 208-210", "MESSERSCHMIDT F., Himmelsbuch und Sternenschrift, Römische Quartalschrift 39 (1931) p. 63-69"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.20-21 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_derived_concept": "concept_axia_biblos_tou_theou_origen_amand1945",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_diss_part3_pseudo_clementine_amand1945",
        ntype="argument", label="Origène — Citation pseudo-clémentine du ch. 14 (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 316-317) : **Troisième partie** de la dissertation antiastrologique : longue citation empruntée au "
            "roman pseudo-clémentin intitulé Περίοδοι. Cet extrait reproduit une réponse de Clément à son père Faustus, "
            "à Laodicée, sur le problème de la Γένεσις (Fatalité astrologique). Tirée du quatorzième livre des Περίοδοι "
            "de Clément. Sauf modifications mineures, l'extrait coïncide presque littéralement avec le passage "
            "correspondant des Reconnaissances pseudo-clémentines (Rufin, MIGNE PG 1, 1425A — 1427B). Amand note la "
            "**double dépendance** : Origène et le rédacteur des Reconnaissances dépendent d'une **polémique chrétienne "
            "antiastrologique commune et antérieure** (cf. C. Schmidt TU 46,1 et R. Cadiou RechSR 1930). Conclusion "
            "d'Amand : Origène n'a pas négligé, pour achever sa critique de l'astrologie, de consulter les discussions "
            "de Clément et de Faustus."
        ),
        description_en=(
            "Amand (p. 316-317): **Third part** of the anti-astrological dissertation: long citation borrowed from the "
            "pseudo-Clementine novel titled Periodoi. This excerpt reproduces a reply of Clement to his father Faustus, "
            "at Laodicea, on the problem of Genesis (astrological Fate). Taken from book 14 of Clement's Periodoi. "
            "Apart from minor modifications, the excerpt coincides almost literally with the corresponding passage of "
            "the pseudo-Clementine Recognitions (Rufin, MIGNE PG 1, 1425A — 1427B). Amand notes the **dual dependence**: "
            "Origen and the Recognitions's redactor both depend on a **common, earlier Christian anti-astrological "
            "polemic** (cf. C. Schmidt TU 46,1 and R. Cadiou RechSR 1930). Amand's conclusion: Origen did not neglect, "
            "to complete his critique of astrology, to consult Clement and Faustus's discussions."
        ),
        md=md_base(
            page_range="p. 316-317",
            md_line_range="ll. 16635-16730",
            chapter="Livre II Ch. V §III.2 (Phil. 23.22)",
            chapter_actual="Livre II Ch. V §III.2 (Phil. 23.22) — Citation Pseudo-Clementines",
            confidence=0.75,
            cited_editions=["Origène, Philocalie 23.22 éd. Robinson p. 210,22 — 212,19", "Pseudo-Clémentines, Reconnaissances (trad. Rufin) PG 1, 1425A — 1427B", "C. SCHMIDT, Studien zu den Pseudo-Clementinen, TU 46,1 Leipzig 1929, p. 170-178", "R. CADIOU, Origène et les Reconnaissances clémentines, RechSR 20 (1930) p. 506-528"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.22 + Pseudo-Clementines absentes du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_dual_dependence": "Origène + Reconnaissances dépendent d'une polémique chrétienne antiastrologique commune antérieure",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_diss_precession_equinoxes_amand1945",
        ntype="argument", label="Origène — Précession des équinoxes mobilisée contre l'astrologie scientifique (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 314) [sub-thème spécifique extrait du Problème 3] : Amand insiste sur la signification scientifique-"
            "philologique exceptionnelle de l'argument d'Origène. Origène distingue (Phil. 23.18, Robinson p. 206,29 — 207,6) "
            "le **νοητὸν δωδεκατημόριον** (signe zodiacal abstrait, intelligible) du **μόρφωμα** (constellation visible). "
            "Par la loi de la précession des équinoxes (1° tous les 100 ans, découverte par Hipparque), les μορφώματα ont "
            "lentement glissé d'Occident en Orient autour de l'axe de l'écliptique, élargissant la distance entre les "
            "signes purement abstraits et les constellations réelles. Tous les calculs astrologiques portent donc sur "
            "des entités imaginaires différentes des signes véritables. Amand : « Origène est le premier ou l'un des "
            "premiers parmi les adversaires de l'apotélesmatique à faire appel à la loi de la précession des équinoxes ». "
            "Apomasar (Abū Maʿshar, 9e s.) reprendra l'objection. Junctinus au XVIe s. répondra par l'expérience. "
            "« Connaissances astronomiques authentiques » (Duhem)."
        ),
        description_en=(
            "Amand (p. 314) [specific sub-theme extracted from Problem 3]: Amand insists on the exceptional scientific-"
            "philological significance of Origen's argument. Origen distinguishes (Phil. 23.18, Robinson p. 206,29 — 207,6) "
            "the **νοητὸν δωδεκατημόριον** (abstract, intelligible zodiacal sign) from the **μόρφωμα** (visible constellation). "
            "Through the precession of equinoxes law (1°/100 years, discovered by Hipparchus), μορφώματα slowly slid from "
            "West to East around the ecliptic axis, widening the distance between purely abstract signs and real "
            "constellations. All astrological calculations therefore concern imaginary entities different from true signs. "
            "Amand: 'Origen is the first or one of the first among apotelesmatic opponents to invoke the precession of "
            "equinoxes law'. Apomasar (Abu Mashar, 9th c.) will resume the objection. Junctinus (16th c.) will respond "
            "with experience. 'Authentic astronomical knowledge' (Duhem)."
        ),
        md=md_base(
            page_range="p. 314 (sub-thème scientifique du Problème 3)",
            md_line_range="ll. 16520-16560",
            chapter="Livre II Ch. V §III.2 (Phil. 23.18 zoom scientifique)",
            chapter_actual="Livre II Ch. V §III.2 — Précession des équinoxes d'Hipparque (Phil. 23.18)",
            confidence=0.85,
            cited_editions=["Origène, Philocalie 23.18 éd. Robinson p. 206,29 — 207,6 (verbatim grec cité par Amand)", "P. DUHEM, Le système du monde II Paris 1914, p. 180-189, 191-192, 393-394"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.18 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_scientific_priority": True,
                "amand_first_precession_polemicist": True,
                "amand_judgement_quote_fr": "Origène est le premier ou l'un des premiers parmi les adversaires de l'apotélesmatique à faire appel à la loi de la précession des équinoxes",
            },
        ),
    ),
])


# ============================================================================
# §IV — ENVELOPPE Transposition carnéadienne (1)
# ============================================================================

NEW_INSERTS.append(make_node(
    nid="argument_origen_witness_carneadean_transposition_envelope_amand1945",
    ntype="argument", label="Origène — Transposition théologique des arguments moraux de Carnéade (Amand 1945 Livre II Ch. V §IV)",
    period="Patristic", school=None, role="amand1945_witness_envelope",
    description=(
        "**Enveloppe argumentaire** : Amand consacre §IV (p. 318-325) à l'utilisation par Origène de l'argumentation morale "
        "antifataliste de Carnéade. Ce sont les **deux premières sections du chapitre 23 de la Philocalie** (Phil. 23.1-2, "
        "Robinson p. 187-189) qui transmettent cette transposition.\n\n"
        "**Méthode-signature d'Amand** : Origène « transpose partout des preuves philosophiques et abstraites en arguments "
        "théologiques ; partout il élargit la perspective morale par la considération des sanctions d'outre-tombe » (p. 320). "
        "Origène applique une argumentation néo-académicienne toute rationnelle à des valeurs morales et religieuses que ne "
        "pouvait soupçonner Carnéade : mérite, démérite, foi chrétienne, Christ, Église, rétributions eschatologiques. "
        "Origène **adapte librement** Carnéade ; il ne transcrit pas une source littéraire ; il est très probable qu'il "
        "ait connu Carnéade indirectement via Cicéron (Académiques, De Natura Deorum, Tusculanes, De Divinatione)."
    ),
    description_en=(
        "**Argumentative envelope**: Amand devotes §IV (p. 318-325) to Origen's use of Carneades' anti-fatalist moral "
        "argumentation. **The first two sections of Philocalia chapter 23** (Phil. 23.1-2, Robinson p. 187-189) transmit "
        "this transposition.\n\n"
        "**Amand's signature method**: Origen 'everywhere transposes philosophical and abstract proofs into theological "
        "arguments; everywhere he broadens the moral perspective through the consideration of eschatological sanctions' "
        "(p. 320). Origen applies a wholly rational New-Academic argumentation to moral and religious values Carneades "
        "could not have suspected: merit, demerit, Christian faith, Christ, Church, eschatological retributions. Origen "
        "**adapts Carneades freely**; he does not transcribe a literary source; he most likely knew Carneades indirectly "
        "via Cicero (Academica, De Natura Deorum, Tusculanae, De Divinatione)."
    ),
    md=md_base(
        page_range="p. 318-325",
        md_line_range="ll. 16762-17120",
        chapter="Livre II Ch. V §IV",
        chapter_actual="Livre II Ch. V §IV — Utilisation par Origène de l'argumentation morale antifataliste de Carnéade",
        confidence=0.95,
        cited_editions=[
            "Origène, Philocalie 23.1-2 éd. Robinson p. 187-189",
            "Origène, Contre Celse IV.3 éd. Koetschau I p. 276,3-22 (cité 'ἀρετῆς μὲν ἐὰν ἀνέλῃς τὸ ἑκούσιον...')",
            "Origène, Contre Celse VIII.15 éd. Koetschau II p. 233,15-18 (aphorisme repris)",
            "Origène, Traité de la prière 29.13, 29.15 éd. Koetschau II p. 387,26—391,1 (économie divine respecte liberté)",
            "Origène, Philocalie 23.2 éd. Robinson p. 189,18-22 (prières superflues sous fatalisme)",
            "Origène, Philocalie 23.2 éd. Robinson p. 188,30—189,18 (excursus Marcionites/Gnostiques)",
            "E. DE FAYE, Origène II. L'ambiance philosophique. Paris 1927, p. 219",
        ],
        extra={
            "is_witness_argument": True,
            "amand_witness_rank": "primary_witness_n1_envelope",
            "amand_witness_role": "envelope_carneadean_transposition",
            "amand_method_signature_quote_fr": "Il transpose partout des preuves philosophiques et abstraites en arguments théologiques ; partout il élargit la perspective morale par la considération des sanctions d'outre-tombe",
            "amand_envelope_subarguments": [
                "argument_origen_witness_carneades_transposition_praise_blame_amand1945",
                "argument_origen_witness_carneades_transposition_theological_consequences_amand1945",
                "argument_origen_witness_carneades_transposition_god_as_evil_amand1945",
                "argument_origen_witness_carneades_transposition_prayer_useless_amand1945",
                "argument_origen_witness_carneades_transposition_gnostic_excursus_amand1945",
                "argument_origen_witness_carneades_transposition_theological_method_amand1945",
                "argument_origen_witness_virtue_voluntary_essence_amand1945",
            ],
        },
    ),
))


# §IV sub-args (7)

NEW_INSERTS.extend([
    make_node(
        nid="argument_origen_witness_carneades_transposition_praise_blame_amand1945",
        ntype="argument", label="Origène (transposant Carnéade) — Fatalisme ruine louange/blâme + récompenses eschatologiques (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 321) : Premier argument carnéadien repris par Origène, mis en forme catégorique et adapté à "
            "l'eschatologie biblique (Phil. 23.1, Robinson p. 187,24 — 188,5). **Texte original grec** : « Ἕπεται δὲ τοῖς "
            "ταῦτα δογματίζουσιν ἐξ ὅλων τὸ ἐφ᾽ ἡμῖν ἀναιρεῖν' διόπερ καὶ ἔπαινον καὶ ψόγον καὶ πράξεις ἀποδεκτὰς πάλιν τε "
            "αὖ ψεκτάς. ἅπερ εἰ οὕτως ἔχει, τὰ τῆς κεκηρυγμένης τοῦ θεοῦ κρίσεως οἴχεται, καὶ ἀπειλαὶ πρὸς τοὺς ἡμαρτηκότας "
            "ὡς κολασθησομένους, τιμαί τε αὖ πρὸς τοὺς τοῖς κρείττοσιν ἑαυτοὺς ἐπιδεδωκότας καὶ μακαριότητες ». **Transposition "
            "d'Amand** : seconde partie place le τόπος carnéadien dans la **perspective chrétienne de l'au-delà et de la "
            "résonance éternelle de nos actes** — les punitions des pécheurs et les récompenses promises aux justes sont "
            "réservées à l'autre vie. Carnéade rationnel → Origène eschatologique."
        ),
        description_en=(
            "Amand (p. 321): First Carneadean argument resumed by Origen, given a categorical form and adapted to biblical "
            "eschatology (Phil. 23.1, Robinson p. 187,24 — 188,5). **Original Greek text**: 'Ἕπεται δὲ τοῖς ταῦτα δογματίζουσιν "
            "ἐξ ὅλων τὸ ἐφ᾽ ἡμῖν ἀναιρεῖν' διόπερ καὶ ἔπαινον καὶ ψόγον καὶ πράξεις ἀποδεκτὰς πάλιν τε αὖ ψεκτάς. ἅπερ εἰ "
            "οὕτως ἔχει, τὰ τῆς κεκηρυγμένης τοῦ θεοῦ κρίσεως οἴχεται, καὶ ἀπειλαὶ πρὸς τοὺς ἡμαρτηκότας ὡς κολασθησομένους, "
            "τιμαί τε αὖ πρὸς τοὺς τοῖς κρείττοσιν ἑαυτοὺς ἐπιδεδωκότας καὶ μακαριότητες'. **Amand's transposition**: second "
            "part places the Carneadean topos in the **Christian perspective of afterlife and eternal resonance of our acts** "
            "— sinners' punishments and just rewards are reserved for the other life. Carneades rational → Origen "
            "eschatological."
        ),
        md=md_base(
            page_range="p. 321",
            md_line_range="ll. 16855-16920",
            chapter="Livre II Ch. V §IV (Phil. 23.1)",
            chapter_actual="Livre II Ch. V §IV — Transposition #1 : ruine louange/blâme + récompenses eschatologiques",
            confidence=0.9,
            cited_editions=["Origène, Philocalie 23.1 éd. Robinson p. 187,24 — 188,5 (verbatim grec cité par Amand)"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.1 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_carneadean_filiation": "Argument I (CAFMA, vertu/vice/louange/blâme) transposé eschatologiquement",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_carneades_transposition_theological_consequences_amand1945",
        ntype="argument", label="Origène (transposant Carnéade) — Conséquences théologiques : vanité du Christ, des Apôtres, de l'Économie (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 321) : Origène **développe ensuite la série des conséquences théologiques, impies et blasphématoires**, "
            "du fatalisme astrologique (Phil. 23.1, Robinson p. 188,5-16). Texte cité par Amand : « la foi chrétienne devient "
            "vaine, la venue du Christ ne nous est d'aucun secours, toute l'économie de la Loi et des Prophètes a été "
            "inutile, et les travaux des Apôtres pour fonder les Églises de Dieu ont été prodigués en pure perte. Les "
            "téméraires iront jusqu'à prétendre que, par sa naissance même, le Christ lui-même est soumis à la contrainte "
            "du mouvement des astres, que toutes ses actions et toutes ses souffrances ont été produites par les "
            "configurations planétaires, et que ce n'est point Dieu et le Père de tous les êtres qui leur a concédé le "
            "pouvoir d'accomplir d'étonnantes merveilles, mais bien les astres. » **Argument proprement chrétien** (pas "
            "directement chez Carnéade) : transposition d'Amand 100% théologique."
        ),
        description_en=(
            "Amand (p. 321): Origen **then develops the series of theological, impious, and blasphemous consequences** of "
            "astrological fatalism (Phil. 23.1, Robinson p. 188,5-16). Text cited by Amand: 'the Christian faith becomes "
            "vain, Christ's coming is of no help to us, the entire economy of the Law and the Prophets was useless, and "
            "the Apostles' labors to found God's Churches were spent in pure waste. The reckless will go so far as to claim "
            "that, by his very birth, Christ himself is subject to the constraint of star motion, that all his actions and "
            "all his sufferings were produced by planetary configurations, and that it is not God and the Father of all "
            "beings who granted them the power to perform astonishing wonders, but rather the stars.' **Properly Christian "
            "argument** (not directly in Carneades): Amand's transposition is 100% theological."
        ),
        md=md_base(
            page_range="p. 321",
            md_line_range="ll. 16920-16955",
            chapter="Livre II Ch. V §IV (Phil. 23.1)",
            chapter_actual="Livre II Ch. V §IV — Transposition #2 : vanité du Christ et de toute l'économie chrétienne",
            confidence=0.85,
            cited_editions=["Origène, Philocalie 23.1 éd. Robinson p. 188,5-16 (verbatim grec cité par Amand)"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.1 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_carneadean_filiation": "Argument 100% chrétien — transposition pure d'Amand sans antécédent rationnel-carnéadien direct",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_carneades_transposition_god_as_evil_amand1945",
        ntype="argument", label="Origène (transposant Carnéade) — Dieu devient auteur du mal (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 322-323) : Origène se **rapproche de Carnéade** dans l'argument suivant (Phil. 23.1, Robinson "
            "p. 188,16-29). Carnéade avait montré que si fatalisme, les pires criminels sont irresponsables et leurs forfaits "
            "doivent être imputés à εἱμαρμένη. **Origène complète par considération de théodicée** : en faisant retomber la "
            "responsabilité sur le Destin, c'est en définitive Dieu lui-même qu'on accuse d'être l'auteur du mal. Le "
            "Créateur devient principe et instigateur des péchés des hommes. Texte cité (homosexualité, brigandage, "
            "piraterie) : les fatalistes s'absolvent eux-mêmes de toute accusation et attribuent à Dieu la responsabilité "
            "de toutes les actions perverses. Position d'Origène : Dieu n'a point créé le mal et n'en est nullement "
            "responsable. Le mal moral = éloignement du Bien consenti par notre libre arbitre. Amand cite (note 1 p. 323) "
            "les axiomes platoniciens repris par Origène : Rép. II 380b « κακῶν δὲ αἴτιον φάναι θεόν τοῦ γίγνεσθαι ἀγαθὸν "
            "ὄντα, διαμαχετέον » + Rép. X 617e « αἰτία ἑλομένου' θεὸς ἀναίτιος »."
        ),
        description_en=(
            "Amand (p. 322-323): Origen **approaches Carneades** in the following argument (Phil. 23.1, Robinson p. 188,16-29). "
            "Carneades had shown that under fatalism, the worst criminals are irresponsible and their crimes must be "
            "imputed to εἱμαρμένη. **Origen completes with a theodicy consideration**: by placing responsibility on Destiny, "
            "it is ultimately God Himself who is accused of being the author of evil. The Creator becomes principle and "
            "instigator of human sins. Cited text (homosexuality, brigandage, piracy): the fatalists absolve themselves of "
            "any accusation and attribute to God the responsibility for all perverse actions. Origen's position: God has "
            "not created evil and is in no way responsible for it. Moral evil = distancing from the Good consented by our "
            "free will. Amand cites (n. 1 p. 323) Platonic axioms taken up by Origen: Rep. II 380b 'κακῶν δὲ αἴτιον φάναι "
            "θεόν τοῦ γίγνεσθαι ἀγαθὸν ὄντα, διαμαχετέον' + Rep. X 617e 'αἰτία ἑλομένου' θεὸς ἀναίτιος'."
        ),
        md=md_base(
            page_range="p. 322-323",
            md_line_range="ll. 16958-17005",
            chapter="Livre II Ch. V §IV (Phil. 23.1)",
            chapter_actual="Livre II Ch. V §IV — Transposition #3 : théodicée — Dieu auteur du mal si fatalisme",
            confidence=0.85,
            cited_editions=["Origène, Philocalie 23.1 éd. Robinson p. 188,16-29 (verbatim grec)", "Platon, République II 380b + X 617e (axiomes repris par Origène)", "Hal KOCH, Pronoia und Paideusis p. 99-109"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.1 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_carneadean_filiation": "Argument carnéadien sur l'irresponsabilité criminelle complété par théodicée juive et axiomes platoniciens",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_carneades_transposition_prayer_useless_amand1945",
        ntype="argument", label="Origène (transposant Carnéade) — Inutilité des prières sous fatalisme astral (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 323-324) : Origène **esquisse le développement d'un autre thème de l'argumentation morale de Carnéade** "
            "(Phil. 23.2, Robinson p. 189,18-22). Note d'Amand : « demeurant dans des généralités, il n'éprouve pas ici le "
            "besoin de transposer sur le plan chrétien l'argument religieux de l'inutilité des prières, dans l'hypothèse "
            "du fatalisme astrologique. » Texte cité : « Outre les preuves énumérées plus haut, ajoutons celle-ci. Si l'on "
            "admet le fatalisme astral, les prières sont superflues et c'est en vain qu'on y recourt. En effet, si tels "
            "événements doivent arriver de toute nécessité, si les astres eux-mêmes les produisent, et si rien n'arrive en "
            "dehors des influences exercées par les configurations des astres qui s'entre-croisent, nous agissons "
            "déraisonnablement en demandant à Dieu que ces événements-là nous arrivent grâce à sa Providence » (Phil. 23.2 "
            "Robinson p. 189,18-22 cité verbatim en grec par Amand)."
        ),
        description_en=(
            "Amand (p. 323-324): Origen **sketches the development of another Carneadean moral argumentation theme** (Phil. "
            "23.2, Robinson p. 189,18-22). Amand's note: 'remaining in generalities, he does not feel the need here to "
            "transpose onto the Christian plane the religious argument of the uselessness of prayers, under the hypothesis "
            "of astrological fatalism.' Cited text: 'Beyond the proofs enumerated above, let us add this one. If astral "
            "fatalism is admitted, prayers are superfluous and we resort to them in vain. Indeed, if such events must "
            "happen of necessity, if the stars themselves produce them, and if nothing happens outside the influences "
            "exercised by intersecting star configurations, we act unreasonably by asking God to grant us these events "
            "through His Providence' (Phil. 23.2 Robinson p. 189,18-22, cited verbatim in Greek by Amand)."
        ),
        md=md_base(
            page_range="p. 323-324",
            md_line_range="ll. 17004-17035",
            chapter="Livre II Ch. V §IV (Phil. 23.2)",
            chapter_actual="Livre II Ch. V §IV — Transposition #4 : inutilité des prières sous fatalisme",
            confidence=0.85,
            cited_editions=["Origène, Philocalie 23.2 éd. Robinson p. 189,18-22 (verbatim grec cité par Amand)"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.2 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
                "amand_carneadean_filiation": "Argument carnéadien sur prières/piété transposé moins fortement (généralité)",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_carneades_transposition_gnostic_excursus_amand1945",
        ntype="argument", label="Origène — Excursus contre Marcionites/Gnostiques dualistes (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 323) : Avant de conclure §IV, Origène « pousse une botte vigoureuse aux Gnostiques dualistes, ses "
            "principaux adversaires », et dirige en particulier ses coups contre les **Marcionites** (Phil. 23.2, Robinson "
            "p. 188,30 — 189,18). Les Marcionites plaçaient en-dessous du Dieu suprême (ou Dieu bon) un Démiurge "
            "simplement juste, responsable de toutes les erreurs et de tous les maux. **Origène dénie expressément à ce "
            "Démiurge l'attribut de justice**. Aporie interne posée : si les hérétiques se reconnaissent esclaves de la "
            "nécessité astrale, ils doivent en bonne logique nier l'existence du Dieu bon ; s'ils se proclament libres "
            "et exempts de contrainte astrologique et de la domination du Démiurge, qu'ils nous expliquent la raison de "
            "la différence qu'ils établissent entre les âmes libres et les âmes soumises à la γένεσις et à l'εἱμαρμένη."
        ),
        description_en=(
            "Amand (p. 323): Before concluding §IV, Origen 'delivers a vigorous thrust against dualist Gnostics, his "
            "principal adversaries', and directs in particular his strikes against **Marcionites** (Phil. 23.2, Robinson "
            "p. 188,30 — 189,18). Marcionites placed below the supreme God (or good God) a merely just Demiurge, responsible "
            "for all errors and evils. **Origen expressly denies this Demiurge the attribute of justice**. Posed internal "
            "aporia: if heretics acknowledge themselves slaves of astral necessity, they must in good logic deny the "
            "existence of the good God; if they proclaim themselves free and exempt from astrological constraint and "
            "Demiurge's domination, let them explain the reason for the difference they establish between free souls and "
            "souls subject to genesis and εἱμαρμένη."
        ),
        md=md_base(
            page_range="p. 323",
            md_line_range="ll. 16980-17005",
            chapter="Livre II Ch. V §IV (Phil. 23.2)",
            chapter_actual="Livre II Ch. V §IV — Transposition #5 : excursus anti-Marcionites/Gnostiques dualistes",
            confidence=0.8,
            cited_editions=["Origène, Philocalie 23.2 éd. Robinson p. 188,30 — 189,18", "H. KOCH, Pronoia und Paideusis p. 100"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.2 absent du corpus KG",
                "cites_primary_source_target": "work_origen_philocalia",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_carneades_transposition_theological_method_amand1945",
        ntype="argument", label="Origène — Méthode signature : transposition philosophique → théologique (méta-argument Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "**Méta-argument méthodologique d'Amand** (p. 320, 324) : Amand identifie la **méthode signature** de la "
            "transposition origénienne, qui sera reprise par tous les patristiques post-origéniens (témoins suivants : "
            "Eusèbe, Basile, Grégoire de Nysse, Méthode d'Olympe, Némésius, Diodore de Tarse). Citation centrale : « Le "
            "didascale alexandrin a utilisé avec aisance et liberté l'argumentation antifataliste de Carnéade. Il est très "
            "probable qu'il ne transcrit pas une source littéraire, mais qu'il adapte lui-même ces arguments à sa polémique "
            "antignostique. Il **transpose partout des preuves philosophiques et abstraites en arguments théologiques** ; "
            "partout il **élargit la perspective morale par la considération des sanctions d'outre-tombe**. Nous verrons "
            "concrètement comment le théologien Origène applique une argumentation néo-académicienne toute rationnelle à des "
            "valeurs morales et religieuses que ne pouvait soupçonner Carnéade : mérite, démérite, foi chrétienne, Christ, "
            "Église, rétributions eschatologiques. » Origène = **pivot méthodologique** entre Carnéade rationnel et "
            "patristique théologique."
        ),
        description_en=(
            "**Amand's methodological meta-argument** (p. 320, 324): Amand identifies the **signature method** of Origenian "
            "transposition, taken up by all post-Origenian patristics (subsequent witnesses: Eusebius, Basil, Gregory of "
            "Nyssa, Methodius of Olympus, Nemesius, Diodore of Tarsus). Central citation: 'The Alexandrian didascalus used "
            "Carneades' anti-fatalist argumentation with ease and freedom. It is very probable that he does not transcribe "
            "a literary source, but adapts these arguments himself to his anti-Gnostic polemic. He **everywhere transposes "
            "philosophical and abstract proofs into theological arguments**; everywhere he **broadens the moral perspective "
            "through the consideration of eschatological sanctions**. We will see concretely how Origen the theologian "
            "applies a wholly rational New-Academic argumentation to moral and religious values Carneades could not have "
            "suspected: merit, demerit, Christian faith, Christ, Church, eschatological retributions.' Origen = "
            "**methodological pivot** between rational Carneades and theological patristics."
        ),
        md=md_base(
            page_range="p. 320, 324",
            md_line_range="ll. 16805-16830, 17075-17085",
            chapter="Livre II Ch. V §IV (méta-méthodologique)",
            chapter_actual="Livre II Ch. V §IV — Méta-argument méthodologique : transposition philosophique → théologique",
            confidence=0.9,
            cited_editions=["Amand 1945 p. 320 (citation directe) et p. 324 (bilan §IV)"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "amand_method_signature": True,
                "amand_pivot_role": "Origène = pivot méthodologique entre Carnéade rationnel et patristique théologique",
                "amand_subsequent_witnesses": [
                    "Eusèbe de Césarée (Ch. VII)",
                    "Basile le Grand (Ch. VIII)",
                    "Grégoire de Nysse (Ch. IX)",
                    "Méthode d'Olympe (Ch. VI)",
                    "Némésius",
                    "Diodore de Tarse",
                ],
                "amand_judgement_quote_fr": "Il transpose partout des preuves philosophiques et abstraites en arguments théologiques ; partout il élargit la perspective morale par la considération des sanctions d'outre-tombe",
            },
        ),
    ),
    make_node(
        nid="argument_origen_witness_virtue_voluntary_essence_amand1945",
        ntype="argument", label="Origène — « Supprimer le volontaire dans la vertu, c'est supprimer son essence » (CC IV.3) (Amand 1945)",
        period="Patristic", school=None, role="amand1945_subarg",
        description=(
            "Amand (p. 319-320) cite et commente la maxime origénienne, **pivot conceptuel d'Amand pour la valeur ontologique "
            "du libre arbitre dans la moralité**. Origène (Contre Celse IV.3, éd. Koetschau I p. 276,3-22) répondant à "
            "Celse : si Dieu améliorait et réformait les hommes en abolissant la malice et en semant la vertu dans les "
            "cœurs, « où est le libre arbitre ? Où est la louable adhésion à la vérité, ou bien la fuite méritoire du "
            "mensonge ? » Origène conclut : « Ὅτι ἀρετῆς μὲν ἐὰν ἀνέλῃς τὸ ἑκούσιον, ἀνεῖλες αὐτῆς καὶ τὴν οὐσίαν » "
            "(« supprimer le volontaire dans la vertu, c'est supprimer son essence-même »). Amand note que cette maxime "
            "est reprise en Contre Celse VIII.15 (éd. Koetschau II p. 233,15-18). Origène ajoute que pour expliquer ce "
            "point, il faudrait tout un traité, et note expressément que **dans les livres Sur la Providence (Περὶ προνοίας) "
            "des philosophes grecs ont traité abondamment de cette matière** — référence implicite à Chrysippe et au "
            "stoïcisme."
        ),
        description_en=(
            "Amand (p. 319-320) cites and comments on Origen's maxim, **Amand's conceptual pivot for the ontological value "
            "of free will in morality**. Origen (Contra Celsum IV.3, Koetschau I p. 276,3-22) replying to Celsus: if God "
            "improved and reformed men by abolishing malice and sowing virtue in hearts, 'where is free will? Where is the "
            "laudable adherence to truth, or the meritorious flight from falsehood?' Origen concludes: 'Ὅτι ἀρετῆς μὲν ἐὰν "
            "ἀνέλῃς τὸ ἑκούσιον, ἀνεῖλες αὐτῆς καὶ τὴν οὐσίαν' ('remove the voluntary from virtue and you remove its very "
            "essence'). Amand notes this maxim is taken up in Contra Celsum VIII.15 (Koetschau II p. 233,15-18). Origen "
            "adds that to explain this point a whole treatise would be needed, and expressly notes that **in the Greek "
            "philosophers' books On Providence (Περὶ προνοίας) this matter has been abundantly treated** — implicit "
            "reference to Chrysippus and Stoicism."
        ),
        md=md_base(
            page_range="p. 319-320",
            md_line_range="ll. 16790-16830",
            chapter="Livre II Ch. V §IV (citation pivot CC IV.3)",
            chapter_actual="Livre II Ch. V §IV — Maxime pivot CC IV.3 sur essence volontaire de la vertu",
            confidence=0.85,
            cited_editions=["Origène, Contre Celse IV.3 éd. Koetschau I p. 276,3-22", "Origène, Contre Celse VIII.15 éd. Koetschau II p. 233,15-18 (reprise)", "Origène, Traité de la prière 29.13-15 éd. Koetschau II p. 387,26 — 391,1"],
            extra={
                "amand_witness_rank": "primary_witness_n1_subarg",
                "is_witness_argument": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Contre Celse IV.3 + VIII.15 hors couverture SC132 (livres I-II seulement). De Oratione 29.13-15 hors couverture De Oratione disponible (2 passages seulement)",
                "cites_primary_source_target": "work_origen_contra_celsum_sc132",
                "amand_pivot_quote_gr": "ἀρετῆς μὲν ἐὰν ἀνέλῃς τὸ ἑκούσιον, ἀνεῖλες αὐτῆς καὶ τὴν οὐσίαν",
                "amand_implicit_reference": "Chrysippe + stoïcisme (livres Περὶ προνοίας)",
            },
        ),
    ),
])


# ============================================================================
# CONCEPTS (3 inserts)
# ============================================================================

NEW_INSERTS.extend([
    make_node(
        nid="concept_logikon_zoon_origen_amand1945",
        ntype="concept", label="Λογικὸν ζῷον — être rationnel chez Origène (Amand 1945)",
        period="Patristic", school=None, role="amand1945_concept",
        description=(
            "Concept-pivot d'Origène : **λογικὸν ζῷον** (être rationnel) — le sujet humain comme être doué de raison ET de "
            "liberté. Amand (p. 299) le caractérise par sa propriété active : *possibilitas utriusque partis*, qui le rend "
            "*laudis et culpae capax* (Princ. I.5,2). Pour Origène, l'homme appartient à la classe des λογικαὶ οὐσίαι "
            "incluant aussi les anges et les démons (hiérarchie des νόες refroidis). La rationalité ET la liberté sont "
            "inséparables : « chez les créatures, la raison a pour corollaire inévitable la liberté » (Amand p. 302 "
            "paraphrasant Princ. III.1, 2-5). L'homme bon **κατὰ συμβεβηκός** (par accident, non par essence comme Dieu)."
        ),
        description_en=(
            "Origenian pivot-concept: **λογικὸν ζῷον** (rational being) — the human subject as endowed with reason AND "
            "freedom. Amand (p. 299) characterizes it by its active property: *possibilitas utriusque partis*, which makes "
            "it *laudis et culpae capax* (Princ. I.5,2). For Origen, man belongs to the class of λογικαὶ οὐσίαι including "
            "also angels and demons (hierarchy of cooled νόες). Rationality AND freedom are inseparable: 'in creatures, "
            "reason has as inevitable corollary freedom' (Amand p. 302 paraphrasing Princ. III.1, 2-5). Man good **κατὰ "
            "συμβεβηκός** (accidentally, not essentially like God)."
        ),
        md=md_base(
            page_range="p. 299, 302",
            md_line_range="ll. 15777-15805, 15895-15920",
            chapter="Livre II Ch. V §II",
            chapter_actual="Livre II Ch. V §II — Concept λογικὸν ζῷον (sujet du libre arbitre)",
            confidence=0.85,
            cited_editions=["Origène, Princ. I.5,2 éd. Koetschau p. 70,4-7", "Origène, Princ. III.1,2-5 éd. Koetschau p. 196-201"],
            extra={
                "amand_concept_pivot": True,
                "amand_related_arguments": ["argument_origen_witness_possibilitas_utriusque_amand1945", "argument_origen_witness_synkatathesis_locus_amand1945"],
            },
        ),
    ),
    make_node(
        nid="concept_axia_biblos_tou_theou_origen_amand1945",
        ntype="concept", label="Ἀξία βίβλος τοῦ θεοῦ — le ciel comme livre digne de Dieu (Amand 1945)",
        period="Patristic", school=None, role="amand1945_concept",
        description=(
            "Concept origénien (Comm. Gen. III via Philocalie 23.20-21) : **ἀξία βίβλος τοῦ θεοῦ** (livre digne de Dieu). "
            "Amand (p. 315-316) : Du soleil, de la lune et des étoiles emportés dans leurs révolutions sidérales, le "
            "Démiurge a fait une **mouvante écriture, formée de lettres et de caractères tracés de sa main**, afin que les "
            "anges et les Puissances divines (δυνάμεις θεῖαι) puissent lire les σημεῖα τοῦ θεοῦ. Ces signes célestes "
            "préfigurent tous les événements cosmiques. Concept lié à la métaphore plus large de l'univers comme texte "
            "déchiffrable, ressort de la sémiotique théologique origénienne. Cf. F. Messerschmidt, Himmelsbuch und "
            "Sternenschrift (1931). Plotin (Enn. III.1 ch. 6) a une conception analogue, mais sans le surcroît théologique "
            "chrétien."
        ),
        description_en=(
            "Origenian concept (Comm. Gen. III via Philocalia 23.20-21): **ἀξία βίβλος τοῦ θεοῦ** (book worthy of God). "
            "Amand (p. 315-316): From sun, moon, and stars in their sidereal revolutions, the Demiurge made a **moving "
            "writing, formed of letters and characters traced by His hand**, so that angels and divine Powers (δυνάμεις "
            "θεῖαι) can read the σημεῖα τοῦ θεοῦ. These celestial signs prefigure all cosmic events. Concept linked to "
            "the broader metaphor of the universe as decipherable text, a lever of Origenian theological semiotics. Cf. "
            "F. Messerschmidt, Himmelsbuch und Sternenschrift (1931). Plotinus (Enn. III.1 ch. 6) has an analogous "
            "conception, but without the Christian theological surplus."
        ),
        md=md_base(
            page_range="p. 315-316",
            md_line_range="ll. 16585-16630",
            chapter="Livre II Ch. V §III.2 (Phil. 23.20-21)",
            chapter_actual="Livre II Ch. V §III.2 — Concept ἀξία βίβλος τοῦ θεοῦ",
            confidence=0.8,
            cited_editions=["Origène, Philocalie 23.20-21 éd. Robinson p. 208-210", "MESSERSCHMIDT F., Himmelsbuch und Sternenschrift, RQ 39 (1931) p. 63-69", "Plotin, Ennéades III.1 ch. 6"],
            extra={
                "amand_concept_pivot": True,
                "evidence_pending": True,
                "evidence_pending_reason": "Philocalie 23.20-21 absent du corpus KG",
            },
        ),
    ),
    make_node(
        nid="concept_metensomatosis_origen_amand1945",
        ntype="concept", label="Métensomatose — transmigration des νόες refroidis chez Origène (Amand 1945)",
        period="Patristic", school=None, role="amand1945_concept",
        description=(
            "Concept origénien (Amand p. 300-301) : **métensomatose** (μετενσωμάτωσις, par contraste avec métempsycose "
            "platonicienne classique). À l'origine, tous les νόες furent créés semblables et égaux. Par exercice du libre "
            "arbitre, ils se sont laissé distraire et se sont refroidis. Hiérarchie de la chute : Chérubins → Puissances "
            "→ Trônes → Anges → hommes → démons. **Chaque âme reçoit un corps proportionné** à la gravité de sa chute. La "
            "nature tombée garde l'usage du libre arbitre et la capacité de redevenir esprit. Rien n'est définitivement "
            "perdu : hommes et démons retrouveront leur état primitif au cours de nouvelles existences purifiantes "
            "(apocatastase). Amand : « le libre arbitre est conçu par Origène comme une force indéfiniment souple, "
            "capable de remonter comme aussi de descendre ». Le concept rejoint celui d'apocatastase et de pédagogie divine."
        ),
        description_en=(
            "Origenian concept (Amand p. 300-301): **metensomatosis** (μετενσωμάτωσις, by contrast with classical Platonic "
            "metempsychosis). Originally, all νόες were created similar and equal. Through exercise of free will, they "
            "let themselves be distracted and cooled. Hierarchy of fall: Cherubim → Powers → Thrones → Angels → humans "
            "→ demons. **Each soul receives a body proportioned** to the severity of its fall. Fallen nature retains "
            "the use of free will and the capacity to again become spirit. Nothing is definitively lost: humans and "
            "demons will recover their primitive state through new purifying existences (apocatastasis). Amand: 'free "
            "will is conceived by Origen as an indefinitely supple force, capable of ascending as well as descending'. "
            "The concept joins those of apocatastasis and divine pedagogy."
        ),
        md=md_base(
            page_range="p. 300-301",
            md_line_range="ll. 15830-15880",
            chapter="Livre II Ch. V §II",
            chapter_actual="Livre II Ch. V §II — Concept de métensomatose (transmigration des νόες)",
            confidence=0.75,
            cited_editions=["Origène, Princ. II.9 éd. Koetschau p. 165-170", "GILSON-BÖHNER, G.Chr.Phil. p. 60-62"],
            extra={
                "amand_concept_pivot": True,
                "amand_related_concepts": ["concept_apocatastasis", "concept_logikon_zoon_origen_amand1945"],
                "evidence_pending": True,
                "evidence_pending_reason": "Princ. II.9 absent du corpus KG",
            },
        ),
    ),
])


# ============================================================================
# SYNTHESES Amand-style (5 inserts)
# ============================================================================

NEW_INSERTS.extend([
    make_node(
        nid="synthesis_amand1945_origen_carneadean_filiation",
        ntype="synthesis", label="Amand 1945 — Filiation Carnéade → Origène (4 siècles, vraisemblablement via Cicéron)",
        period=None, school=None, role="amand1945_synthesis",
        description=(
            "Synthèse Amand : la filiation Carnéade → Origène est établie par Amand sur la base de la **comparaison "
            "structurelle des 6 arguments moraux** (B1/B2 CAFMA chez Cicéron De Fato 39-43, Plutarque De Stoic. Rep., Aulu "
            "Gelle VI.2) avec les sections 1-2 de la Philocalie 23 d'Origène (Phil. 23.1-2, Robinson p. 187-189). Quatre "
            "siècles séparent les deux. Origène cite Carnéade indirectement : Amand (note 3 p. 294 citant De Faye) : « il "
            "ne semble pas probable qu'il ait pris la peine d'étudier la philosophie de la Nouvelle Académie, encore moins "
            "celle de l'école sceptique. Cependant les nombreux passages qui rappellent les Académiques de Cicéron, son "
            "De natura deorum, les Tusculanes, son traité sur la divination, impliquent qu'il n'ignorait pas les thèses "
            "d'Arcésilas, de Carnéade et de Clitomaque ». Origène adapte librement, ne transcrit pas. Transmission "
            "probable : **Carnéade (oral) → Clitomaque (écrit) → Cicéron (transmission latine) → Origène (paraphrase "
            "grecque transposée théologiquement)**."
        ),
        description_en=(
            "Amand's synthesis: the Carneades → Origen filiation is established by Amand on the basis of **structural "
            "comparison of the 6 moral arguments** (B1/B2 CAFMA in Cicero De Fato 39-43, Plutarch De Stoic. Rep., Aulus "
            "Gellius VI.2) with sections 1-2 of Origen's Philocalia 23 (Phil. 23.1-2, Robinson p. 187-189). Four centuries "
            "separate the two. Origen cites Carneades indirectly: Amand (n. 3 p. 294 citing De Faye): 'it does not seem "
            "probable that he took the trouble to study New Academy philosophy, let alone the skeptical school. However, "
            "the many passages reminiscent of Cicero's Academica, De natura deorum, Tusculanae, his treatise on divination, "
            "imply that he was not unaware of the theses of Arcesilaus, Carneades, and Clitomachus'. Origen adapts freely, "
            "does not transcribe. Probable transmission: **Carneades (oral) → Clitomachus (written) → Cicero (Latin "
            "transmission) → Origen (Greek paraphrase transposed theologically)**."
        ),
        md=md_base(
            page_range="p. 294 note 3, 320, 324",
            md_line_range="ll. 15592-15605, 16805-16830, 17075-17085",
            chapter="Livre II Ch. V §IV (synthèse globale)",
            chapter_actual="Livre II Ch. V §IV (synthèse globale) — Filiation Carnéade → Origène via Cicéron",
            confidence=0.75,
            cited_editions=["E. DE FAYE, Origène II. L'ambiance philosophique. Paris 1927, p. 219"],
            extra={
                "amand_synthesis_type": "filiation",
                "amand_transmission_chain": ["Carneades (oral)", "Clitomachus (written)", "Cicero (Academica, De NatDeor, Tusculanae, De Div)", "Origen (Greek paraphrase, theological transposition)"],
            },
        ),
    ),
    make_node(
        nid="synthesis_amand1945_origen_first_christian_prescience_problem",
        ntype="synthesis", label="Amand 1945 — Origène, premier théologien chrétien à problématiser méthodiquement prescience vs libre arbitre",
        period=None, school=None, role="amand1945_synthesis",
        description=(
            "Synthèse Amand : Origène (Phil. 23.7-11, Robinson p. 194-198) est, selon Amand, **le premier théologien chrétien "
            "qui ait envisagé dans toute son ampleur la redoutable difficulté que la prescience divine soulève à l'encontre "
            "de la libre détermination de la volonté humaine**. La problématique n'est pas absente avant Origène, mais "
            "personne ne lui avait consacré un traitement méthodique. Solution origénienne : connaissance compréhensive de "
            "Dieu permettant une économie providentielle qui s'adapte aux libres actions humaines (≠ Stoïciens fatalistes, "
            "≠ Platoniciens moyens combinant Destin + actions libres). **Solution entérinée dans l'ensemble par la théologie "
            "ecclésiastique postérieure** (Augustin, Boèce, scolastique). Pivot historique-théologique majeur."
        ),
        description_en=(
            "Amand's synthesis: Origen (Phil. 23.7-11, Robinson p. 194-198) is, according to Amand, **the first Christian "
            "theologian to have considered in all its scope the formidable difficulty that divine foreknowledge raises "
            "against the free determination of human will**. The problem is not absent before Origen, but no one had "
            "devoted a methodical treatment to it. Origen's solution: comprehensive divine knowledge enabling a "
            "providential economy that adapts to free human actions (≠ Stoic fatalists, ≠ Middle Platonists combining "
            "Fate + free actions). **Solution endorsed overall by subsequent ecclesiastical theology** (Augustine, "
            "Boethius, Scholasticism). Major historical-theological pivot."
        ),
        md=md_base(
            page_range="p. 310",
            md_line_range="ll. 16336-16360",
            chapter="Livre II Ch. V §III.2",
            chapter_actual="Livre II Ch. V §III.2 — Synthèse : Origène pionnier du problème prescience-libre arbitre",
            confidence=0.9,
            cited_editions=["Hal KOCH, Pronoia und Paideusis p. 114-117, 128-131", "E. DE FAYE, Origène III p. 185-191"],
            extra={
                "amand_synthesis_type": "priority_claim",
                "amand_subsequent_endorsement": ["Augustin", "Boèce", "scolastique"],
            },
        ),
    ),
    make_node(
        nid="synthesis_amand1945_origen_first_precession_polemicist",
        ntype="synthesis", label="Amand 1945 — Origène, premier (ou un des premiers) à mobiliser la précession des équinoxes contre l'astrologie",
        period=None, school=None, role="amand1945_synthesis",
        description=(
            "Synthèse Amand (p. 314) : Origène est « le premier ou l'un des premiers parmi les adversaires de "
            "l'apotélesmatique à faire appel à la loi de la précession des équinoxes découverte par Hipparque ». Note "
            "scientifique-technique exceptionnelle : Origène distingue le ζῳδιακὸν κύκλον théorique (νοητὸν δωδεκατημόριον) "
            "du μόρφωμα (constellation réelle) en arguant que le second se décale par mouvement séculaire de 1° tous les "
            "100 ans. Apomasar (Abū Maʿshar, 9e s.) reprendra l'argument. Au XVIe s., Junctinus tentera d'y répondre par "
            "l'expérience justifiant les prédictions. Duhem (Système du monde II p. 393-394) : « Nous sommes portés à "
            "croire que l'auteur (Origène) s'y montrait (dans le Commentaire de la Genèse) exactement informé des "
            "doctrines élaborées par les astronomes de son temps ». Cf. W. Gundel, Nachträge, p. 131-132."
        ),
        description_en=(
            "Amand's synthesis (p. 314): Origen is 'the first or one of the first among apotelesmatic opponents to "
            "invoke the precession of equinoxes law discovered by Hipparchus'. Exceptional scientific-technical note: "
            "Origen distinguishes the theoretical ζῳδιακὸν κύκλον (νοητὸν δωδεκατημόριον) from the μόρφωμα (real "
            "constellation) by arguing that the latter shifts by secular 1°/100 years motion. Apomasar (Abu Mashar, "
            "9th c.) will resume the argument. In 16th c., Junctinus will try to respond via experience justifying "
            "predictions. Duhem (Système du monde II p. 393-394): 'We are inclined to believe that the author (Origen) "
            "showed himself (in the Commentary on Genesis) accurately informed of the doctrines elaborated by the "
            "astronomers of his time'. Cf. W. Gundel, Nachträge, p. 131-132."
        ),
        md=md_base(
            page_range="p. 314",
            md_line_range="ll. 16520-16560",
            chapter="Livre II Ch. V §III.2 (Phil. 23.18)",
            chapter_actual="Livre II Ch. V §III.2 — Synthèse priorité scientifique précession équinoxes",
            confidence=0.85,
            cited_editions=["P. DUHEM, Le système du monde II Paris 1914, p. 191-192, 393-394", "W. GUNDEL, Nachträge à Boll-Bezold-Gundel, Sternglaube und Sterndeutung, Leipzig 1931, p. 131-132"],
            extra={
                "amand_synthesis_type": "priority_claim_scientific",
                "amand_subsequent_reception": ["Apomasar (9e s.)", "Junctinus (16e s.)"],
            },
        ),
    ),
    make_node(
        nid="synthesis_amand1945_origen_carneadean_method_signature",
        ntype="synthesis", label="Amand 1945 — Méthode signature : transposition philosophique → théologique de la matière carnéadienne",
        period=None, school=None, role="amand1945_synthesis",
        description=(
            "Synthèse Amand : la **méthode signature** de la transposition origénienne consiste à : (1) ne pas transcrire "
            "littéralement la source rationnelle néo-académicienne ; (2) adapter librement la matière à la polémique "
            "antignostique chrétienne ; (3) transposer partout les preuves philosophiques abstraites en arguments "
            "théologiques ; (4) élargir la perspective morale par la considération des sanctions d'outre-tombe ; (5) "
            "appliquer la rationalité néo-académicienne à des valeurs religieuses inaccessibles à Carnéade : mérite, "
            "démérite, foi chrétienne, Christ, Église, rétributions eschatologiques. Toute argumentation morale d'Amand "
            "patristique post-origénienne (Eusèbe, Basile, Grégoire de Nysse, Méthode, Némésius, Diodore) porte cette "
            "signature méthodologique."
        ),
        description_en=(
            "Amand's synthesis: the **signature method** of Origenian transposition consists in: (1) not literally "
            "transcribing the rational New-Academic source; (2) freely adapting the matter to Christian anti-Gnostic "
            "polemic; (3) everywhere transposing abstract philosophical proofs into theological arguments; (4) broadening "
            "the moral perspective through eschatological sanctions; (5) applying New-Academic rationality to religious "
            "values inaccessible to Carneades: merit, demerit, Christian faith, Christ, Church, eschatological "
            "retributions. All Amand's post-Origenian patristic moral argumentation (Eusebius, Basil, Gregory of Nyssa, "
            "Methodius, Nemesius, Diodore) carries this methodological signature."
        ),
        md=md_base(
            page_range="p. 320, 324-325",
            md_line_range="ll. 16805-16830, 17075-17120",
            chapter="Livre II Ch. V §IV (méta-synthèse)",
            chapter_actual="Livre II Ch. V §IV — Méta-synthèse méthode signature transposition",
            confidence=0.85,
            extra={
                "amand_synthesis_type": "method_signature",
                "amand_subsequent_witnesses_carrying_signature": [
                    "person_eusebius_caesarea_d339 (Ch. VII)",
                    "person_basil_great_d379 (Ch. VIII)",
                    "person_gregory_nyssa_d395 (Ch. IX)",
                    "person_methodius_olympus_d311 (Ch. VI)",
                ],
            },
        ),
    ),
    make_node(
        nid="synthesis_amand1945_origen_pivot_witness",
        ntype="synthesis", label="Amand 1945 — Origène = 1er témoin patristique pivot de la lignée carnéadienne",
        period=None, school=None, role="amand1945_synthesis",
        description=(
            "Synthèse Amand : **Origène = 1er témoin patristique de la lignée carnéadienne anti-fataliste**, pivot "
            "historiographique du Livre II d'Amand. Position structurelle : pont entre (a) les 6 témoins de la "
            "reconstruction carnéadienne (Cicéron De Fato 39-43, Aulu Gelle VI.2, Philon De Provid., Plutarque De Stoic. "
            "Rep., Pseudo-Plutarque De Fato, Alexandre De Fato 16-20, Firmicus Mathesis I.2.5-11) traités au Livre I + B3/B4 ; "
            "et (b) les témoins patristiques suivants : Méthode d'Olympe (Ch. VI), Eusèbe de Césarée (Ch. VII), Basile "
            "le Grand (Ch. VIII), Grégoire de Nysse (Ch. IX), Diodore de Tarse, Némésius, Théodoret. Origène est le **point "
            "d'articulation** où la matière rationnelle carnéadienne devient outil de polémique théologique chrétienne. "
            "Sans Origène, pas de patristique anti-astrologique cohérente."
        ),
        description_en=(
            "Amand's synthesis: **Origen = 1st patristic witness of the Carneadean anti-fatalist lineage**, historiographical "
            "pivot of Amand's Book II. Structural position: bridge between (a) the 6 witnesses of the Carneadean "
            "reconstruction (Cicero De Fato 39-43, Aulus Gellius VI.2, Philo De Prov., Plutarch De Stoic. Rep., "
            "Pseudo-Plutarch De Fato, Alexander De Fato 16-20, Firmicus Mathesis I.2.5-11) treated in Book I + B3/B4; "
            "and (b) subsequent patristic witnesses: Methodius of Olympus (Ch. VI), Eusebius of Caesarea (Ch. VII), "
            "Basil the Great (Ch. VIII), Gregory of Nyssa (Ch. IX), Diodore of Tarsus, Nemesius, Theodoret. Origen is "
            "the **articulation point** where rational Carneadean matter becomes a tool of Christian theological polemic. "
            "Without Origen, no coherent anti-astrological patristic."
        ),
        md=md_base(
            page_range="p. 275-325 (synthèse globale Ch. V)",
            md_line_range="ll. 14740-17120",
            chapter="Livre II Ch. V (synthèse globale)",
            chapter_actual="Livre II Ch. V — Synthèse globale : Origène pivot historiographique",
            confidence=0.95,
            extra={
                "amand_synthesis_type": "structural_pivot",
                "amand_book_structure_position": "Pont entre Livre I (témoins reconstruction Carnéade) et Livre II (Origène → Eusèbe → Basile → Grégoire Nysse → Méthode → Diodore → Némésius → Théodoret)",
                "amand_carneadean_witnesses_book_I": [
                    "Cicero De Fato 39-43",
                    "Aulus Gellius VI.2",
                    "Philo De Providentia",
                    "Plutarch De Stoic. Rep.",
                    "Pseudo-Plutarch De Fato",
                    "Alexander De Fato 16-20",
                    "Firmicus Mathesis I.2.5-11",
                ],
                "amand_patristic_witnesses_book_II": [
                    "Origène (Ch. V) = pivot",
                    "Méthode d'Olympe (Ch. VI)",
                    "Eusèbe de Césarée (Ch. VII)",
                    "Basile le Grand (Ch. VIII)",
                    "Grégoire de Nysse (Ch. IX)",
                    "Diodore de Tarse",
                    "Némésius",
                    "Théodoret",
                ],
            },
        ),
    ),
])
