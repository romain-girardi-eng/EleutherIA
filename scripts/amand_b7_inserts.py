"""Amand B7 — NEW_INSERTS list (new nodes).

Each node carries an Amand-standard metadata block. Descriptions are plain text
(no markdown) — bilingual FR/EN. Periods are title-case canonical only.
"""
from __future__ import annotations

from typing import Any

from amand_b7_utils import amand_metadata, dump_metadata


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
# PERSONS (1) — Pseudo-Chrysostom (distinct from authentic Chrysostom)
# =============================================================================

NEW_PERSONS: list[dict[str, Any]] = [
    _node(
        id="person_pseudo_chrysostom_de_fato",
        type="person",
        label="Pseudo-Chrysostom (De Fato et Providentia)",
        description=(
            "Pseudo-Jean Chrysostome, auteur anonyme du Discours sur le Destin et la "
            "Providence V (PG 50, 765-768) — l'un des six Discours sur le Destin et la "
            "Providence transmis sous le nom de Jean Chrysostome (PG 50, 749-774). Pour "
            "Amand 1945 (Livre II Ch. XII, p. 525-532), l'authenticité chrysostomienne "
            "de ces six discours est douteuse : ni démontrée par Montfaucon, ni "
            "démontrablement infirmée. Amand pencherait personnellement en faveur de "
            "l'authenticité mais retient l'attribution traditionnelle pseudo-épigraphe "
            "pour le Discours V — d'où le statut de témoin n°6 distinct du témoin "
            "Chrysostome authentique (témoin n°5 = Homélie après le discours du prêtre "
            "Goth, ch. 6, PG 63, 500-510). Le Pseudo-Chrysostome écrit en grec d'Orient "
            "au IVe-Ve siècle, dans un style à la fois moins ample et plus verbeux que "
            "celui de Chrysostome authentique, avec doxologies christologiques (et non "
            "trinitaires) aux cinq premiers discours. Distinction posée selon le pattern "
            "EleutherIA Phase 7 (Pseudo-Plutarque, Pseudo-Justin, Pseudo-Iustinus "
            "Cohortatio) : créer un nœud distinct pour préserver l'intégrité "
            "philologique de la KG."
        ),
        description_en=(
            "Pseudo-John Chrysostom, anonymous author of Discourse on Fate and "
            "Providence V (PG 50, 765-768) — one of six Discourses on Fate and "
            "Providence transmitted under John Chrysostom's name (PG 50, 749-774). For "
            "Amand 1945 (Book II Ch. XII, p. 525-532), the Chrysostomian authenticity of "
            "these six discourses is doubtful: neither demonstrated by Montfaucon nor "
            "demonstrably refuted. Amand himself inclines toward authenticity but "
            "retains the traditional pseudo-epigraphic attribution for Discourse V — "
            "hence its status as witness n°6 distinct from the authentic Chrysostom "
            "witness (witness n°5 = Homily after the Goth priest's discourse, ch. 6, "
            "PG 63, 500-510). The Pseudo-Chrysostom writes in Eastern Greek in the "
            "4th-5th century, in a style that is at once less ample and more verbose "
            "than authentic Chrysostom, with Christological (not Trinitarian) "
            "doxologies for the first five discourses. Distinction made per the "
            "EleutherIA Phase 7 pattern (Pseudo-Plutarch, Pseudo-Justin, "
            "Pseudo-Iustinus Cohortatio): create a distinct node to preserve "
            "philological integrity of the KG."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 504-510, 525-532",
            md_line_range="ll. 25623-27634",
            chapter="Livre II Ch. XII §III + §IV.3 (Pseudo-Chrysostome)",
            amand_chapter_actual="Jean Chrysostome (témoin n°6)",
            extra={
                "amand_witness_rank": "primary_witness_n6",
                "amand_witness_role": "witness_6_pseudo_chrysostom",
                "authenticity_status_amand": "doubtful (Amand personally inclines toward genuine; status pseudo-epigraphic retained)",
                "language": "Greek",
                "milieu": "Eastern Christian (likely Antiochene or Constantinopolitan, 4th-5th c.)",
                "principal_attestation": "PG 50, 749-774 (Montfaucon ed., Colbertinus 49)",
            },
        ),
        confidence=0.7,
    ),
]


# =============================================================================
# WORKS (7) — Chrysostom homilies (work-shells) + Ps-Chrys De Fato + Cohortatio companion
# =============================================================================

NEW_WORKS: list[dict[str, Any]] = [
    _node(
        id="work_chrysostom_hom_paul_after_goth",
        type="work",
        label="John Chrysostom, Homilia post sermonem presbyteri Gothi (Hom. Saint-Paul après prêtre Goth)",
        description=(
            "Homélie de Jean Chrysostome prononcée en l'église Saint-Paul de "
            "Constantinople après le discours d'un prêtre Goth, transmise par "
            "Montfaucon dans les onze homélies inédites de Chrysostome (PG 63, 499-510). "
            "Pour Amand 1945 (Livre II Ch. XII p. 510-525), le chapitre 6 (PG 63, 500 "
            "l.16 — 510 l.36) constitue le 'texte témoin n°5' — l'un des deux 'textes "
            "témoins' les plus détaillés et précis de l'argumentation morale "
            "antifataliste de Carnéade conservée dans la littérature grecque chrétienne "
            "des quatre premiers siècles. Le passage déploie cinq arguments structurés "
            "(rougeur de la honte, sévérité des châtiments, éducation des enfants, vanité "
            "de toutes les activités humaines si la genesis règne, distinction "
            "vertu/vice) suivis d'une conclusion : 'si nous supprimons toute différence "
            "entre l'homme juste et l'homme injuste, tout sera confusion, désordre et "
            "bouleversement. Il n'y aura plus ni vertu ni vice, ni sciences ni lois.' "
            "Le même passage est repris textuellement (avec inversions secondaires) dans "
            "l'homélie pseudo-chrysostomienne Sur la charité parfaite, 3 (PG 56, 282-283) "
            "= centon homilétique."
        ),
        description_en=(
            "John Chrysostom's homily delivered in St Paul's church at Constantinople "
            "after a Gothic priest's discourse, transmitted by Montfaucon in his eleven "
            "previously unedited Chrysostomian homilies (PG 63, 499-510). For Amand 1945 "
            "(Book II Ch. XII p. 510-525), chapter 6 (PG 63, 500 l.16 — 510 l.36) "
            "constitutes 'witness text n°5' — one of the two most detailed and precise "
            "'witness texts' of Carneades' moral antifatalist argumentation preserved in "
            "Christian Greek literature of the first four centuries. The passage "
            "deploys five structured arguments (blushing shame, severity of punishment, "
            "education of children, vanity of all human activity if genesis rules, "
            "virtue/vice distinction) followed by a conclusion: 'if we suppress all "
            "difference between the just and the unjust, everything will be confusion, "
            "disorder and upheaval. There will be neither virtue nor vice, nor sciences "
            "nor laws.' The same passage is reproduced verbatim (with minor inversions) "
            "in the pseudo-Chrysostomian homily On Perfect Love, 3 (PG 56, 282-283) — "
            "a homiletic centon."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 510-525",
            md_line_range="ll. 25900-26076",
            chapter="Livre II Ch. XII §IV.2 (texte témoin n°5)",
            amand_chapter_actual="Jean Chrysostome (témoin n°5)",
            extra={
                "amand_witness_rank": "primary_witness_n5",
                "principal_attestation": "PG 63, 499-510",
                "witness_text_location": "ch. 6 (PG 63, 500 l.16 — 510 l.36)",
                "centonic_parallel": "Ps-Chrys Hom. On Perfect Love 3 (PG 56, 282-283)",
                "editions": [
                    {"raw": "B. de Montfaucon, the eleven previously unedited homilies, PG 63, 499-510"},
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_chrysostom_hom_1_timothy",
        type="work",
        label="John Chrysostom, Homiliae in Epistulam I ad Timotheum",
        description=(
            "Homélies de Jean Chrysostome sur la première lettre à Timothée (PG 62, "
            "501-600). Pour Amand 1945 (Livre II Ch. XII p. 504, 509-510), la première "
            "homélie (sur 1 Tim 1, ch. 3) à PG 62, 507 l.45 — 508 l.4 contient un "
            "argument antifataliste cité par Amand comme 'premier texte' du témoin "
            "Chrysostome — argument carnéadien sur la futilité de toute activité "
            "(semence, plantation, service militaire, métiers) si la genesis détermine "
            "tout. Le passage est suivi d'une polémique contre les chrétiens qui "
            "préfèrent l'heimarmene à la Providence devant le désordre moral du monde. "
            "Amand admet que ce premier texte n'est pas 'd'allure pure' carnéadienne, le "
            "ton dogmatique de la fin de la citation ne convenant guère au probabilisme "
            "néo-académicien — il s'agit d'une libre utilisation amplifiée par "
            "l'orateur."
        ),
        description_en=(
            "John Chrysostom's Homilies on the First Letter to Timothy (PG 62, 501-600). "
            "For Amand 1945 (Book II Ch. XII p. 504, 509-510), the first homily (on 1 "
            "Tim 1, ch. 3) at PG 62, 507 l.45 — 508 l.4 contains an antifatalist "
            "argument cited by Amand as the 'first text' of the Chrysostom witness — a "
            "Carneadean argument on the futility of all activity (sowing, planting, "
            "soldiering, crafts) if genesis determines everything. The passage is "
            "followed by a polemic against Christians who prefer heimarmene to "
            "Providence in the face of the world's moral disorder. Amand grants that "
            "this first text is not 'purely' Carneadean in flavour, since the "
            "dogmatic tone at the end suits ill the Academic probabilism — it is a "
            "free use amplified by the orator."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 504, 509-510",
            md_line_range="ll. 25600-25921",
            chapter="Livre II Ch. XII §IV.1 (premier texte)",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "amand_role": "witness_5_supplementary (first text alongside Hom. Goth)",
                "cited_passage": "Hom. 1 (1 Tim 1, ch. 3) PG 62, 507 l.45 — 508 l.4",
                "editions": [
                    {"raw": "Migne PG 62, 501-600"},
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="work_chrysostom_hom_ephesians",
        type="work",
        label="John Chrysostom, Homiliae in Epistulam ad Ephesios",
        description=(
            "Homélies de Jean Chrysostome sur la lettre aux Éphésiens (PG 62, 9-176). "
            "Pour Amand 1945 (Livre II Ch. XII p. 485), la XXIe homélie (PG 62, 153 "
            "l.1-4) renferme la formule fameuse traitant la philosophie hellénique et "
            "ses représentants de triobolimaios — 'trois oboles' — et de 'chiens'. "
            "L'homélie est mobilisée par Amand comme témoignage du mépris affiché de "
            "Chrysostome à l'égard de la sagesse grecque."
        ),
        description_en=(
            "John Chrysostom's Homilies on the Letter to the Ephesians (PG 62, 9-176). "
            "For Amand 1945 (Book II Ch. XII p. 485), Homily XXI (PG 62, 153 l.1-4) "
            "contains the famous formula treating Hellenic philosophy and its "
            "representatives as triobolimaios — 'three obols' worth — and as 'dogs'. "
            "Amand mobilises this homily as testimony to Chrysostom's overt contempt "
            "for Greek wisdom."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 485",
            md_line_range="ll. 24727-24766",
            chapter="Livre II Ch. XII §I (attitude envers la philosophie grecque)",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "cited_passage": "Hom. XXI, 3 (PG 62, 153 l.1-4)",
                "editions": [
                    {"raw": "Migne PG 62, 9-176"},
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_chrysostom_de_babylas_contra_julianum",
        type="work",
        label="John Chrysostom, Liber in S. Babylam contra Iulianum et gentiles",
        description=(
            "Discours de Jean Chrysostome en l'honneur de saint Babylas, contre Julien "
            "et contre les Grecs (PG 50, 533-572). Pour Amand 1945 (Livre II Ch. XII "
            "p. 485, 488-489), Amand cite ch. 2 (PG 57, 536 l.56-60) et ch. 9 (PG 50, "
            "546 l.14-46) pour le réquisitoire chrysostomien contre les mœurs des "
            "philosophes — Diogène le Cynique, Aristote, Zénon de Cition, Platon — où "
            "le prédicateur recourt à l'attaque ad hominem (Platon traité de souteneur "
            "de filles, Aristote goûteur de sperme humain, Zénon recommandant l'inceste). "
            "Texte typique de la rhétorique anti-philosophique de Chrysostome."
        ),
        description_en=(
            "John Chrysostom's Discourse in honour of St Babylas, against Julian and the "
            "Greeks (PG 50, 533-572). For Amand 1945 (Book II Ch. XII p. 485, 488-489), "
            "Amand cites ch. 2 (PG 57, 536 l.56-60) and ch. 9 (PG 50, 546 l.14-46) for "
            "Chrysostom's indictment of the philosophers' morals — Diogenes the Cynic, "
            "Aristotle, Zeno of Citium, Plato — where the preacher resorts to ad "
            "hominem attacks (Plato called pimp of girls, Aristotle taster of human "
            "sperm, Zeno recommending incest). Typical text of Chrysostom's "
            "anti-philosophical rhetoric."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 485, 488-489",
            md_line_range="ll. 24761-24953",
            chapter="Livre II Ch. XII §I (anti-philosophie)",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "editions": [
                    {"raw": "Migne PG 50, 533-572"},
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="work_chrysostom_hom_john",
        type="work",
        label="John Chrysostom, Homiliae in Iohannem",
        description=(
            "Homélies de Jean Chrysostome sur l'Évangile de Jean (PG 59). Pour Amand "
            "1945 (Livre II Ch. XII p. 486, 488), Amand cite plusieurs homélies (Hom. "
            "IX, XLIII, LXVI) pour les sorties anti-helléniques : 'C'est un grand bien "
            "que la philosophie — j'entends notre philosophie à nous, chrétiens. Car "
            "quant à celle du dehors, ce ne sont que paroles et fables' (Hom. XLIII.1, "
            "PG 59, 349 l.5-9). L'orateur compare les apôtres au coryphée des "
            "philosophes (Pierre vs Platon) au mépris des philosophes ioniens dégradés "
            "à de simples matérialistes."
        ),
        description_en=(
            "John Chrysostom's Homilies on the Gospel of John (PG 59). For Amand 1945 "
            "(Book II Ch. XII p. 486, 488), Amand cites several homilies (Hom. IX, "
            "XLIII, LXVI) for the anti-Hellenic outbursts: 'philosophy is a great good "
            "— I mean our Christian philosophy. For the philosophy of the outside is "
            "but words and fables' (Hom. XLIII.1, PG 59, 349 l.5-9). The orator "
            "contrasts the apostles with the chief of philosophers (Peter vs Plato) and "
            "scorns the Ionian philosophers reduced to simple materialists."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 486, 488",
            md_line_range="ll. 24784-24997",
            chapter="Livre II Ch. XII §I",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "editions": [
                    {"raw": "Migne PG 59"},
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="work_chrysostom_hom_colossians",
        type="work",
        label="John Chrysostom, Homiliae in Epistulam ad Colossenses",
        description=(
            "Homélies de Jean Chrysostome sur la lettre aux Colossiens (PG 62, 299-392). "
            "Pour Amand 1945 (Livre II Ch. XII p. 503-504), la deuxième homélie (PG 62, "
            "318 l.16-27) dénonce la croyance des chrétiens à la nécessité et à "
            "l'heimarmene comme tactique du diable pour les amener à négliger la vertu "
            "et à adorer les démons."
        ),
        description_en=(
            "John Chrysostom's Homilies on the Letter to the Colossians (PG 62, 299-392). "
            "For Amand 1945 (Book II Ch. XII p. 503-504), Homily II (PG 62, 318 l.16-27) "
            "denounces Christians' belief in necessity and heimarmene as a diabolical "
            "tactic to lead them to neglect virtue and worship demons."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 503-504",
            md_line_range="ll. 25609-25640",
            chapter="Livre II Ch. XII §III (anti-fatalisme)",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "cited_passage": "Hom. II (PG 62, 318 l.16-27)",
                "editions": [
                    {"raw": "Migne PG 62, 299-392"},
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="work_pseudo_chrysostom_de_fato_providentia",
        type="work",
        label="Pseudo-John Chrysostom, De Fato et Providentia (Discourses on Fate and Providence)",
        description=(
            "Les Six Discours sur le Destin et la Providence (Peri heimarmenes te kai "
            "pronoias logoi hex) tels qu'attribués au Pseudo-Chrysostome pour le besoin "
            "du témoin n°6 d'Amand 1945 — particulièrement le Discours V (PG 50, 765 "
            "l.24 — 768 l.44). Sous l'attribution traditionnelle Jean Chrysostome (PG "
            "50, 749-774), l'authenticité reste contestée : ni démontrée ni infirmée. "
            "Le Discours V renferme 'un texte capital' (Amand) — neuf arguments "
            "antifatalistes carnéadiens accumulés, suivis d'une récapitulation "
            "oratoire célèbre : 'Si la genesis existe, il n'y a plus de justice. Si la "
            "genesis existe, il n'y a plus de foi. Si la genesis existe, Dieu n'existe "
            "pas. Si la genesis existe, il n'y a plus de vertu, il n'y a plus de vice. "
            "Si la genesis existe, tout se fait en vain.' Voir aussi le nœud "
            "sc79_chrysostomus_de_providentia pour la transmission authentique-attribuée "
            "et les passages SC79 ingérés."
        ),
        description_en=(
            "The Six Discourses on Fate and Providence (Peri heimarmenes te kai pronoias "
            "logoi hex) as attributed to Pseudo-Chrysostom for the purpose of Amand "
            "1945's witness n°6 — particularly Discourse V (PG 50, 765 l.24 — 768 l.44). "
            "Under the traditional attribution to John Chrysostom (PG 50, 749-774), "
            "authenticity remains contested: neither demonstrated nor refuted. "
            "Discourse V contains 'a capital text' (Amand) — nine accumulated "
            "Carneadean antifatalist arguments followed by a famous oratorical "
            "recapitulation: 'If genesis exists, there is no justice. If genesis "
            "exists, there is no faith. If genesis exists, God does not exist. If "
            "genesis exists, there is neither virtue nor vice. If genesis exists, "
            "everything is done in vain.' See also the node sc79_chrysostomus_de_"
            "providentia for the authentically-attributed transmission and the "
            "ingested SC79 passages."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 504-510, 525-532",
            md_line_range="ll. 25623-27634",
            chapter="Livre II Ch. XII §III + §IV.3 (texte témoin n°6)",
            amand_chapter_actual="Jean Chrysostome (Pseudo-Chrys, témoin n°6)",
            extra={
                "amand_witness_rank": "primary_witness_n6",
                "principal_attestation": "PG 50, 749-774 (witness text at 765-768)",
                "discourse_v_witness_location": "PG 50, 765 l.24 — 768 l.44",
                "centonic_parallel_for_argument_1_3": "Hom. on perfect love 3 (PG 56, 282-283)",
                "authenticity_status_amand": "doubtful (pseudo-epigraphic attribution retained for Discourse V)",
                "editions": [
                    {"raw": "Montfaucon, PG 50, 749-774 (Colbertinus 49)"},
                    {"raw": "SC 79 (Malingrey 1961) for authentically-attributed transmission"},
                ],
            },
        ),
        confidence=0.7,
    ),
]


# =============================================================================
# SYNTHESES (5) — Amand scholarly assessments
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    _node(
        id="synthesis_amand1945_gregory_nyssa_carneadean_role",
        type="synthesis",
        label="Amand 1945 — Grégoire de Nysse, témoin secondaire double",
        description=(
            "Synthèse Amand 1945 (Livre II Ch. IX, p. 405-439) sur le rôle de "
            "Grégoire de Nysse dans la transmission carnéadienne antifataliste. "
            "Grégoire occupe une place double et atypique : (a) dans le Contre le "
            "Destin (Kata heimarmenes, PG 45, 145C-173D), il accumule 23 arguments "
            "anti-astrologiques dont au moins deux remontent directement à Carnéade "
            "(catastrophes collectives, nomima barbarika), mais sans contenu moral "
            "antifataliste ; Amand formule l'hypothèse d'une source littéraire perdue "
            "représentant la polémique carnéadienne/clitomachéenne ; (b) dans le "
            "Discours catéchétique 31 (ed. Srawley p. 113-114 ; PG 45, 77BD), il "
            "résume un ou deux arguments éthiques de Carnéade comme lieu commun "
            "scolaire dans un encadrement théologique origénien. Grégoire ne figure "
            "donc pas parmi les six textes témoins majeurs mais illustre la diffusion "
            "diffuse de l'argumentation néo-académicienne à la fin du IVe siècle, "
            "réduite chez lui à 'une condensation schématique'."
        ),
        description_en=(
            "Amand 1945 synthesis (Book II Ch. IX, p. 405-439) on Gregory of Nyssa's "
            "role in the Carneadean antifatalist transmission. Gregory holds a "
            "twofold and atypical position: (a) in the Contra Fatum (Kata "
            "heimarmenes, PG 45, 145C-173D), he accumulates 23 anti-astrological "
            "arguments at least two of which go directly back to Carneades (collective "
            "catastrophes, nomima barbarika), yet with no moral antifatalist content; "
            "Amand formulates the hypothesis of a lost literary source representing "
            "the Carneadean/Clitomachean polemic; (b) in Catechetical Discourse 31 "
            "(ed. Srawley p. 113-114; PG 45, 77BD), he summarises one or two ethical "
            "Carneadean arguments as a schoolroom commonplace embedded in an "
            "Origenian theological framing. Gregory therefore does not figure among "
            "the six major witness texts but illustrates the diffuse spread of "
            "neo-Academic argumentation at the close of the 4th century, reduced in "
            "him to 'a schematic condensation'."
        ),
        period=None,  # synthesis modern scholarship
        metadata=amand_metadata(
            page_range="p. 405-439",
            md_line_range="ll. 21179-22740",
            chapter="Livre II Ch. IX (Grégoire de Nysse)",
            amand_chapter_actual="Grégoire de Nysse",
            extra={
                "synthesis_type": "scholarly_assessment",
                "amand_witness_role": "secondary_double (Contra Fatum + Disc. cat. 31)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_amand1945_chrysostom_carneadean_paradox",
        type="synthesis",
        label="Amand 1945 — paradoxe Chrysostome: hellénisme nul, transmission carnéadienne maximale",
        description=(
            "Synthèse Amand 1945 (Livre II Ch. XII, p. 480-532) sur le paradoxe "
            "constitutif de Jean Chrysostome dans la transmission carnéadienne. "
            "Chrysostome est, selon Amand suivant Puech, peut-être le plus détaché de "
            "l'hellénisme parmi tous les Pères du IVe siècle : il accable de sarcasmes "
            "la philosophie grecque (triobolimaios), invective Platon (souteneur de "
            "filles, sépulcre blanchi), Aristote, Zénon, Diogène. Son hellénisme est "
            "purement formel — technique oratoire apprise des rhéteurs (peut-être "
            "Libanios) — et l'âme de son éloquence puise dans la foi chrétienne et le "
            "zèle apostolique. Or, paradoxe : c'est précisément ce prédicateur "
            "anti-philosophe qui livre, dans son Homélie après le discours du prêtre "
            "Goth (ch. 6, PG 63, 500-510), le texte témoin n°5 de l'argumentation "
            "morale antifataliste carnéadienne — l'un des deux 'textes témoins' les "
            "plus détaillés et précis conservés dans la littérature grecque chrétienne "
            "des quatre premiers siècles. Amand explique ce paradoxe par "
            "l'amplification oratoire : Chrysostome a hérité d'une matrice scolaire "
            "(probablement via Diodore de Tarse ou un commentaire intermédiaire), qu'il "
            "déploie avec la véhémence du prédicateur populaire. Le second 'texte "
            "témoin' chrysostomien (témoin n°6) est attribué à un Pseudo-Chrysostome "
            "(Discours sur le Destin et la Providence V, PG 50, 765-768)."
        ),
        description_en=(
            "Amand 1945 synthesis (Book II Ch. XII, p. 480-532) on the constitutive "
            "paradox of John Chrysostom in the Carneadean transmission. Chrysostom is, "
            "per Amand following Puech, perhaps the most detached from Hellenism among "
            "all 4th-century Fathers: he heaps sarcasms on Greek philosophy "
            "(triobolimaios), invectives against Plato (pimp of girls, whitewashed "
            "tomb), Aristotle, Zeno, Diogenes. His Hellenism is purely formal — "
            "oratorical technique learnt from rhetors (possibly Libanius) — and the "
            "soul of his eloquence draws from Christian faith and apostolic zeal. Yet, "
            "paradox: this anti-philosophical preacher precisely delivers, in his "
            "Homily after the Goth priest's discourse (ch. 6, PG 63, 500-510), witness "
            "text n°5 of Carneades' moral antifatalist argumentation — one of the two "
            "most detailed and precise 'witness texts' preserved in Christian Greek "
            "literature of the first four centuries. Amand explains this paradox via "
            "oratorical amplification: Chrysostom inherited a scholastic matrix "
            "(probably via Diodore of Tarsus or an intermediate commentary), which he "
            "deploys with the popular preacher's vehemence. The second Chrysostomian "
            "'witness text' (witness n°6) is attributed to a Pseudo-Chrysostom "
            "(Discourse on Fate and Providence V, PG 50, 765-768)."
        ),
        period=None,
        metadata=amand_metadata(
            page_range="p. 480-532",
            md_line_range="ll. 24500-27635",
            chapter="Livre II Ch. XII (Jean Chrysostome)",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "synthesis_type": "scholarly_paradox_assessment",
                "amand_witness_role": "primary_witnesses_5_and_6",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_amand1945_pseudo_chrysostom_witness6_status",
        type="synthesis",
        label="Amand 1945 — statut du témoin n°6 Pseudo-Chrysostome",
        description=(
            "Synthèse Amand 1945 (Livre II Ch. XII p. 504-510, 525-532) sur "
            "l'attribution et le statut du Discours sur le Destin et la Providence V "
            "(PG 50, 765-768) comme témoin n°6 de la reconstruction carnéadienne. "
            "Amand reconnaît l'incertitude philologique : 'Je n'ai pas la compétence "
            "requise pour me prononcer en connaissance de cause sur le problème de "
            "leur authenticité' ; Montfaucon et Savile n'ont pas tranché. Personnellement "
            "Amand pencherait en faveur de l'authenticité chrysostomienne — le style "
            "moins ample, plus verbeux, et les doxologies christologiques pouvant "
            "s'expliquer par la notation tachygraphique ou les éditeurs posthumes. "
            "Mais il retient l'attribution traditionnelle pseudo-épigraphe pour la "
            "reconstruction. Le Discours V renferme 'le texte capital' du témoin n°6 "
            ": neuf arguments antifatalistes structurés culminant dans la "
            "récapitulation oratoire 'si genesis est, krisis ouk est…' — l'un des "
            "exemples les plus systématiques de la trame carnéadienne dans la "
            "littérature patristique."
        ),
        description_en=(
            "Amand 1945 synthesis (Book II Ch. XII p. 504-510, 525-532) on the "
            "attribution and status of Discourse on Fate and Providence V (PG 50, "
            "765-768) as witness n°6 of the Carneadean reconstruction. Amand "
            "acknowledges the philological uncertainty: 'I lack the competence to "
            "decide on the problem of their authenticity'; Montfaucon and Savile did "
            "not settle the matter. Amand personally inclines toward Chrysostomian "
            "authenticity — the less ample, more verbose style, and the "
            "Christological doxologies can be explained by tachygraphic notation or "
            "posthumous editors. Yet he retains the traditional pseudo-epigraphic "
            "attribution for the reconstruction. Discourse V contains 'the capital "
            "text' of witness n°6: nine structured antifatalist arguments culminating "
            "in the oratorical recapitulation 'if genesis exists, krisis does not "
            "exist…' — one of the most systematic instances of the Carneadean "
            "framework in patristic literature."
        ),
        period=None,
        metadata=amand_metadata(
            page_range="p. 504-510, 525-532",
            md_line_range="ll. 25623-27634",
            chapter="Livre II Ch. XII §III (six Discours) + §IV.3 (texte témoin n°6)",
            amand_chapter_actual="Pseudo-Chrysostome (témoin n°6)",
            extra={
                "synthesis_type": "scholarly_attribution_assessment",
                "amand_witness_role": "witness_6_pseudo_chrysostom",
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="synthesis_amand1945_nemesius_witness_decay",
        type="synthesis",
        label="Amand 1945 — Némésios: l'argumentation carnéadienne 'rapetissée et momifiée'",
        description=(
            "Synthèse Amand 1945 (Livre II Ch. XIV, p. 549-569) sur le rôle de "
            "Némésios d'Émèse dans la transmission carnéadienne antifataliste. "
            "Némésios est un témoin secondaire au statut singulier : son chapitre 35 "
            "du Peri physeos anthropou (PG 40, 741 BC, l. 18-33) ouvre par un résumé "
            "'sec et squelettique' de l'argumentation morale antifataliste de "
            "Carnéade — inutilité de la législation, des tribunaux, des louanges et "
            "blâmes, des prières ; négation de la Providence et de la religion ; "
            "réduction de l'homme à 'instrument dirigé par les mouvements circulaires "
            "des corps célestes'. Pour Amand, ces 'arguments desséchés et stériles' "
            "l'évêque chrétien les a 'copiés ou démarqués dans sa source [un "
            "commentaire péripatéticien perdu sur l'EN III, datant du IIe ou IIIe s.] "
            "sans même songer à amplifier'. 'L'ample et vivante argumentation de "
            "Carnéade a été rapetissée et momifiée par les faiseurs de manuels ; elle "
            "s'est muée en vulgaire recette d'école.' Némésios atteste ainsi, en fin "
            "de période patristique grecque, la dégradation manualiste de la matière "
            "carnéadienne — précieux indice négatif pour la reconstruction d'Amand."
        ),
        description_en=(
            "Amand 1945 synthesis (Book II Ch. XIV, p. 549-569) on Nemesius of Emesa's "
            "role in the Carneadean antifatalist transmission. Nemesius is a "
            "secondary witness of singular status: his chapter 35 of the Peri physeos "
            "anthropou (PG 40, 741 BC, l. 18-33) opens with a 'dry and skeletal' "
            "summary of Carneades' moral antifatalist argumentation — futility of "
            "legislation, courts, praise and blame, prayers; negation of Providence "
            "and religion; reduction of man to 'an instrument directed by the "
            "circular motions of celestial bodies'. For Amand, these 'desiccated and "
            "sterile arguments' the Christian bishop 'copied or paraphrased from his "
            "source [a lost Peripatetic commentary on EN III, dating from the 2nd or "
            "3rd c.] without even thinking to amplify them'. 'Carneades' ample and "
            "living argumentation has been shrunken and mummified by the "
            "manual-makers; it has turned into a vulgar schoolroom recipe.' Nemesius "
            "thus attests, at the end of the Greek patristic period, the "
            "manual-driven degradation of the Carneadean matter — a precious "
            "negative indicator for Amand's reconstruction."
        ),
        period=None,
        metadata=amand_metadata(
            page_range="p. 549-569",
            md_line_range="ll. 28349-29327",
            chapter="Livre II Ch. XIV (Némésios d'Émèse)",
            amand_chapter_actual="Némésios d'Émèse",
            extra={
                "synthesis_type": "scholarly_decay_assessment",
                "amand_witness_role": "secondary_witness_decayed",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_amand1945_cappadocian_chain",
        type="synthesis",
        label="Amand 1945 — chaîne cappadocienne Origène→Basile→Grégoire de Nysse",
        description=(
            "Synthèse Amand 1945 transversale (Livre II Ch. VIII-IX) sur la chaîne de "
            "transmission cappadocienne du libre arbitre origénien et de la polémique "
            "antifataliste. La filiation s'établit : (a) Origène (Comm. in Gen., "
            "préservé partiellement dans Philocalia 23 et PE VI.11) → (b) Basile et "
            "Grégoire de Nazianze co-compilent la Philocalia (vers 358-360, à Annisi) "
            "→ (c) Basile, Hexaemeron VI.5-7 (anti-Chaldéens) et Grégoire de Nysse, "
            "Contra Fatum + Discours catéchétique 31. Le frère cadet hérite donc "
            "doublement : par la formation directe au sein du milieu cappadocien, et "
            "par l'accès aux excerpta origéniens compilés par Basile et son ami. Pour "
            "Amand (p. 407-411), l'influence d'Origène est encore plus pénétrante sur "
            "Grégoire de Nysse que sur Basile — 'le maître alexandrin lui a surtout "
            "éveillé en lui le sens et le goût de la spéculation'. La méthode "
            "rationnelle de Grégoire (preuves ek ton koinon ennoion, ek tes ton "
            "eikoton logismon akolouthias) extends celle de Basile et l'enracinement "
            "dans Origène."
        ),
        description_en=(
            "Amand 1945 transversal synthesis (Book II Ch. VIII-IX) on the Cappadocian "
            "chain of transmission of Origenian free will and antifatalist polemic. "
            "The filiation runs: (a) Origen (Comm. in Gen., partially preserved in "
            "Philocalia 23 and PE VI.11) → (b) Basil and Gregory of Nazianzus "
            "co-compile the Philocalia (ca. 358-360, at Annisi) → (c) Basil, "
            "Hexaemeron VI.5-7 (anti-Chaldean) and Gregory of Nyssa, Contra Fatum + "
            "Catechetical Discourse 31. The younger brother thus inherits doubly: "
            "through direct formation within the Cappadocian milieu, and through "
            "access to the Origenian excerpts compiled by Basil and his friend. For "
            "Amand (p. 407-411), Origen's influence is even more penetrating on "
            "Gregory of Nyssa than on Basil — 'the Alexandrian master above all "
            "awakened in him the taste for speculation'. Gregory's rational method "
            "(proofs ek ton koinon ennoion, ek tes ton eikoton logismon akolouthias) "
            "extends Basil's and the rooting in Origen."
        ),
        period=None,
        metadata=amand_metadata(
            page_range="p. 401-417",
            md_line_range="ll. 21179-21478",
            chapter="Livre II Ch. VIII-IX (chaîne cappadocienne)",
            amand_chapter_actual="Basile + Grégoire de Nazianze + Grégoire de Nysse",
            extra={
                "synthesis_type": "intellectual_filiation",
                "philocalia_collaboration_date": "ca. 358-360 CE at Annisi",
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# ARGUMENTS — Gregory of Nyssa Contra Fatum (8) + Disc. Cat. (1)
# =============================================================================

NEW_ARGUMENTS_GREGORY: list[dict[str, Any]] = [
    _node(
        id="argument_gregory_contrafatum_pagan_philosopher_thesis_amand1945",
        type="argument",
        label="Gregory of Nyssa CF — thèse du philosophe païen sur la sympatheia universelle",
        description=(
            "Thèse exposée par le philosophe païen stoïcisant interlocuteur de "
            "Grégoire dans le Contre le Destin (PG 45, 148B-153C). Le fatalisme "
            "astrologique intégral repose sur la doctrine posidonienne de la sympatheia "
            "universelle (mia tis estin en tois ousi sympatheia) : les régions "
            "supérieures du kosmos (corps célestes) dirigent à leur guise les "
            "mouvements subordonnés et inférieurs des corps terrestres. Conséquences "
            "apotélesmatiques : les hommes de l'art peuvent prédire à coup sûr les "
            "actions humaines grâce aux influx planétaires ; la frappe instantanée de "
            "l'horoscope au moment de la naissance fixe fatalement le caractère, "
            "l'intelligence, les mœurs et la vie future de chaque individu — comme la "
            "cire reçoit l'empreinte du sceau (PG 45, 153 AC). Cette exposition est "
            "présentée en grec dans la note supplémentaire d'Amand (p. 435-439). "
            "Amand attire l'attention des historiens de la philosophie sur la "
            "présence ici du dogme stoïcien de la sympathie universelle de Posidonios."
        ),
        description_en=(
            "Thesis expounded by the Stoicising pagan philosopher who serves as "
            "Gregory's interlocutor in Contra Fatum (PG 45, 148B-153C). Integral "
            "astrological fatalism rests on the Posidonian doctrine of universal "
            "sympatheia (mia tis estin en tois ousi sympatheia): the upper regions of "
            "the cosmos (celestial bodies) direct at will the subordinate and "
            "inferior motions of terrestrial bodies. Apotelesmatic consequences: "
            "practitioners of the art can predict human actions with certainty thanks "
            "to planetary influxes; the instantaneous strike of the horoscope at "
            "birth fatally fixes the character, intelligence, morals and future life "
            "of each individual — as wax receives the imprint of the seal (PG 45, "
            "153 AC). This exposition is given in Greek in Amand's supplementary "
            "note (p. 435-439). Amand draws historians' attention to the presence "
            "here of Posidonius' Stoic dogma of universal sympathy."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 423-424, 435-439",
            md_line_range="ll. 22043-22075, 22536-22675",
            chapter="Livre II Ch. IX §III.1 + Note suppl. (Contre le Destin première partie)",
            amand_chapter_actual="Grégoire de Nysse (Contra Fatum, exposé du fatalisme par le philosophe)",
            extra={
                "amand_evidence_pg": "PG 45, 148B-153C",
                "argument_type": "doxographical_exposition_of_opposed_position",
                "evidence_pending": True,
                "evidence_pending_reason": "Contra Fatum (PG 45, 148B-153C) absent from EleutherIA corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
    _node(
        id="argument_gregory_contrafatum_catastrophes_amand1945",
        type="argument",
        label="Gregory of Nyssa CF — argument carnéadien des catastrophes collectives",
        description=(
            "Argument de Grégoire dans le Contre le Destin (PG 45, 165 AC + 168B-169B), "
            "explicitement identifié par Amand 1945 (p. 428, 431) comme un argument "
            "antiastrologique de Carnéade. Si les destinées humaines sont prédéterminées "
            "à l'instant fatidique par les influx planétaires, comment expliquer les "
            "catastrophes et morts collectives — batailles sanglantes, tremblements de "
            "terre, naufrages, inondations, incendies — qui frappent simultanément des "
            "personnes aux horoscopes très divers ? Grégoire emprunte ses exemples à "
            "l'Ancien Testament, à l'histoire grecque (guerres médiques) et à "
            "l'actualité du IVe s. (incendie et tremblement de terre de Nicomédie, "
            "dévastation de la Thrace par les Goths). Cet argument confirme la "
            "dépendance de l'opuscule envers une source carnéadienne directe ou "
            "indirecte."
        ),
        description_en=(
            "Gregory's argument in Contra Fatum (PG 45, 165 AC + 168B-169B), "
            "explicitly identified by Amand 1945 (p. 428, 431) as a Carneadean "
            "anti-astrological argument. If human destinies are predetermined at the "
            "fatal instant by planetary influxes, how to explain collective "
            "catastrophes and deaths — bloody battles, earthquakes, shipwrecks, "
            "floods, fires — striking simultaneously persons with very diverse "
            "horoscopes? Gregory draws his examples from the Old Testament, from "
            "Greek history (Median Wars) and from 4th c. current events (Nicomedia "
            "fire and earthquake, Goths' devastation of Thrace). This argument "
            "confirms the opusculum's dependence on a Carneadean source direct or "
            "indirect."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 428, 431",
            md_line_range="ll. 22225-22246, 22366-22368",
            chapter="Livre II Ch. IX §III.2 args 15+17 (Contre le Destin)",
            amand_chapter_actual="Grégoire de Nysse (Contra Fatum)",
            extra={
                "amand_evidence_pg": "PG 45, 165 AC + 168B-169B",
                "argument_type": "carneadean_anti_astrological",
                "carneadean_certainty_per_amand": "high (explicit identification)",
                "evidence_pending": True,
                "evidence_pending_reason": "Contra Fatum (PG 45) absent from EleutherIA corpus",
            },
        ),
        confidence=0.9,
        needs_evidence=True,
    ),
    _node(
        id="argument_gregory_contrafatum_nomima_barbarika_amand1945",
        type="argument",
        label="Gregory of Nyssa CF — argument carnéadien des nomima barbarika",
        description=(
            "Argument de Grégoire dans le Contre le Destin (PG 45, 169B), explicitement "
            "identifié par Amand 1945 (p. 428-429, 431) comme le second argument "
            "antiastrologique carnéadien préservé dans l'opuscule. L'argument des "
            "nomima barbarika (la diversité des mœurs et coutumes humaines) : sous "
            "tous les climats et toutes les influences astrales, les Juifs conservent "
            "jalousement leur religion et leurs coutumes spécifiques (telle que la "
            "circoncision). Cette persistance culturelle prouve que la véritable "
            "heimarmene n'est autre que 'la libre volonté d'un chacun qui choisit ce "
            "qu'il lui plaît'. Argument carnéadien classique attesté également chez "
            "Bardesane (Livre des lois des pays) et Eusèbe (PE VI.10) — pour Amand "
            "indice solide d'une source carnéadienne commune."
        ),
        description_en=(
            "Gregory's argument in Contra Fatum (PG 45, 169B), explicitly identified "
            "by Amand 1945 (p. 428-429, 431) as the second Carneadean "
            "anti-astrological argument preserved in the opusculum. The nomima "
            "barbarika argument (diversity of human customs and laws): under all "
            "climates and all astral influences, Jews jealously preserve their "
            "religion and their specific customs (like circumcision). This cultural "
            "persistence proves that the true heimarmene is none other than 'each "
            "person's free will choosing what it pleases'. Classic Carneadean "
            "argument also attested in Bardaisan (Book of the Laws of the Lands) and "
            "Eusebius (PE VI.10) — for Amand a solid clue to a common Carneadean "
            "source."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 428-429, 431",
            md_line_range="ll. 22247-22267, 22368-22369",
            chapter="Livre II Ch. IX §III.2 args 18-19 (Contre le Destin)",
            amand_chapter_actual="Grégoire de Nysse (Contra Fatum)",
            extra={
                "amand_evidence_pg": "PG 45, 169B",
                "argument_type": "carneadean_anti_astrological",
                "carneadean_certainty_per_amand": "high (explicit identification)",
                "parallel_witnesses": ["Bardaisan", "Eusebius PE VI.10"],
                "evidence_pending": True,
                "evidence_pending_reason": "Contra Fatum (PG 45) absent from EleutherIA corpus",
            },
        ),
        confidence=0.9,
        needs_evidence=True,
    ),
    _node(
        id="argument_gregory_contrafatum_fate_of_fate_dilemma_amand1945",
        type="argument",
        label="Gregory of Nyssa CF — dilemme du Destin du Destin (12e argument)",
        description=(
            "Douzième argument de Grégoire dans le Contre le Destin (PG 45, 161 BD), "
            "présenté sous forme de dilemme dialectique. Ou bien les influences "
            "maléfiques des signes zodiacaux et des planètes sont libres et "
            "volontaires — auquel cas ces astres sont eux-mêmes malheureux ; ou bien "
            "leurs influx malfaisants sont involontaires et soumis à la contrainte — "
            "auquel cas il faut poser un Destin du Destin, une Fatalité de la Fatalité, "
            "et cela à l'infini. Cet argument 'ad absurdum' caractéristique de la "
            "manière néo-académicienne s'inscrit pour Amand dans la trame "
            "carnéadienne probable du traité."
        ),
        description_en=(
            "Gregory's twelfth argument in Contra Fatum (PG 45, 161 BD), presented as "
            "a dialectical dilemma. Either the maleficent influences of the zodiacal "
            "signs and planets are free and voluntary — in which case these stars are "
            "themselves unhappy; or their malefic influxes are involuntary and "
            "subject to constraint — in which case one must posit a Fate of Fate, a "
            "Fatality of Fatality, and so on to infinity. This 'ad absurdum' "
            "argument characteristic of the neo-Academic style fits, for Amand, into "
            "the probable Carneadean framework of the treatise."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 427",
            md_line_range="ll. 22190-22196",
            chapter="Livre II Ch. IX §III.2 arg 12 (Contre le Destin)",
            amand_chapter_actual="Grégoire de Nysse (Contra Fatum)",
            extra={
                "amand_evidence_pg": "PG 45, 161 BD",
                "argument_type": "dialectical_dilemma",
                "carneadean_certainty_per_amand": "moderate (style consistent)",
                "evidence_pending": True,
                "evidence_pending_reason": "Contra Fatum (PG 45) absent from EleutherIA corpus",
            },
        ),
        confidence=0.8,
        needs_evidence=True,
    ),
    _node(
        id="argument_gregory_contrafatum_heimarmene_no_being_amand1945",
        type="argument",
        label="Gregory of Nyssa CF — l'heimarmene est le non-être (7e argument)",
        description=(
            "Septième argument de Grégoire dans le Contre le Destin (PG 45, 160 AB). "
            "L'heimarmene n'est ni une personne ni une Providence. Si, comme on "
            "l'affirme, elle est privée d'âme et dépourvue de volonté, elle n'est "
            "point une substance. Il est ridicule d'attribuer à quelque chose "
            "d'inanimé le gouvernement des âmes et des volontés. L'heimarmene n'est "
            "ni un être vivant ni même une nature — c'est proprement le non-être (to "
            "me on). A fortiori, c'est le comble de la démence de l'identifier à Dieu "
            "lui-même."
        ),
        description_en=(
            "Gregory's seventh argument in Contra Fatum (PG 45, 160 AB). Heimarmene "
            "is neither a person nor a Providence. If, as is asserted, it is soulless "
            "and willless, it is no substance. It is absurd to attribute to "
            "something inanimate the governance of souls and wills. Heimarmene is "
            "neither a living being nor even a nature — it is properly non-being (to "
            "me on). A fortiori it is the height of madness to identify it with God "
            "himself."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 426",
            md_line_range="ll. 22146-22154",
            chapter="Livre II Ch. IX §III.2 arg 7 (Contre le Destin)",
            amand_chapter_actual="Grégoire de Nysse (Contra Fatum)",
            extra={
                "amand_evidence_pg": "PG 45, 160 AB",
                "argument_type": "ontological_refutation",
                "evidence_pending": True,
                "evidence_pending_reason": "Contra Fatum (PG 45) absent from EleutherIA corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
    _node(
        id="argument_gregory_contrafatum_diversity_destinies_amand1945",
        type="argument",
        label="Gregory of Nyssa CF — diversité des destinées contredit la toute-puissance de l'heimarmene",
        description=(
            "Argument de Grégoire dans le Contre le Destin (PG 45, 157 AC + 157 C — 160 A). "
            "Si chaque influx astral est doué d'une infrangible puissance, tous les "
            "hommes devraient être également rois, heureux, riches, comblés de biens. "
            "L'expérience inflige à ce rêve un cruel démenti. La diversité des "
            "destinées et des genres de vie montre que l'heimarmene n'est point "
            "toute-puissante. Si l'on objecte qu'il y a deux heimarmenai contraires "
            "(l'une puissante, l'autre faible), la plupart des hommes menant une "
            "existence misérable, c'est l'heimarmene impuissante qui l'emporte sur "
            "l'autre — la toute-puissance prétendue n'est qu'une chimère. Variante : "
            "deux enfants naissent en même temps, l'un fils de roi, l'autre fils "
            "d'esclave — comment expliquer cette conduite injuste de l'heimarmene ?"
        ),
        description_en=(
            "Gregory's argument in Contra Fatum (PG 45, 157 AC + 157 C — 160 A). If "
            "each astral influx is endowed with unbreakable power, all humans should "
            "be equally kings, happy, rich, sated. Experience cruelly refutes this "
            "dream. The diversity of destinies and modes of life shows that "
            "heimarmene is not all-powerful. If one objects that there are two "
            "contrary heimarmenai (one powerful, one weak), with most humans living "
            "miserable lives, it is the powerless heimarmene that prevails — the "
            "alleged omnipotence is mere chimera. Variant: two children born at the "
            "same instant, one a king's son, the other a slave's son — how to "
            "explain this unjust conduct of heimarmene?"
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 425-426",
            md_line_range="ll. 22104-22145",
            chapter="Livre II Ch. IX §III.2 args 4-6 (Contre le Destin)",
            amand_chapter_actual="Grégoire de Nysse (Contra Fatum)",
            extra={
                "amand_evidence_pg": "PG 45, 156 C — 160 A",
                "argument_type": "empirical_refutation",
                "evidence_pending": True,
                "evidence_pending_reason": "Contra Fatum (PG 45) absent from EleutherIA corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
    _node(
        id="argument_gregory_contrafatum_demonic_origin_amand1945",
        type="argument",
        label="Gregory of Nyssa CF — argument théologique de l'origine démonique de l'astrologie",
        description=(
            "Argument théologique inséré par Grégoire dans le Contre le Destin (PG "
            "45, 169 D — 172 C + 173 B), à distinguer des arguments philosophiques "
            "carnéadiens. Le diable et les démons, par haine de l'humanité, ont "
            "inventé l'astrologie et toutes les branches de la mantique en abusant du "
            "désir passionné des hommes de connaître l'avenir. La vraie cause des "
            "prédictions astrologiques n'est donc pas l'heimarmene — elle est à "
            "chercher dans la fraude et la perfidie des démons. Amand note que cet "
            "argument 'spécifiquement chrétien' est ressassé par presque tous les "
            "docteurs qui ont écrit ou prêché contre l'astrologie et le fatalisme des "
            "Chaldéens — il ne fait donc pas partie de la trame carnéadienne mais "
            "représente l'apport chrétien spécifique de Grégoire."
        ),
        description_en=(
            "Theological argument inserted by Gregory in Contra Fatum (PG 45, 169 D "
            "— 172 C + 173 B), to be distinguished from the Carneadean philosophical "
            "arguments. The devil and demons, out of hatred for humanity, invented "
            "astrology and all branches of divination by abusing humans' passionate "
            "desire to know the future. The true cause of astrological predictions "
            "is therefore not heimarmene — it lies in the fraud and perfidy of "
            "demons. Amand notes that this 'specifically Christian' argument is "
            "rehashed by almost all doctors who wrote or preached against astrology "
            "and Chaldean fatalism — it is therefore not part of the Carneadean "
            "framework but represents Gregory's specifically Christian contribution."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 429-430",
            md_line_range="ll. 22275-22316",
            chapter="Livre II Ch. IX §III.2 args 20+23 (Contre le Destin)",
            amand_chapter_actual="Grégoire de Nysse (Contra Fatum)",
            extra={
                "amand_evidence_pg": "PG 45, 169 D — 172 C + 173 B",
                "argument_type": "specifically_christian_apologetic",
                "carneadean_certainty_per_amand": "none (Christian addition)",
                "evidence_pending": True,
                "evidence_pending_reason": "Contra Fatum (PG 45) absent from EleutherIA corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
    _node(
        id="argument_gregory_disccat31_carneadean_moral_amand1945",
        type="argument",
        label="Gregory of Nyssa Disc. Cat. 31 — argument carnéadien moral comme topos scolaire",
        description=(
            "Argument du Discours catéchétique 31 de Grégoire de Nysse (ed. Srawley "
            "p. 113-114 ; PG 45, 77BD), encadré par une aporie théologique : pourquoi "
            "Dieu ne force-t-il pas les incrédules à embrasser la foi ? Réponse de "
            "Grégoire (résumant un ou deux arguments éthiques de Carnéade) : ce "
            "serait détruire le libre arbitre et, avec lui, la vertu. Sans libre "
            "arbitre, louange et blâme ne peuvent s'appliquer aux actions humaines. "
            "Si la volonté demeure inactive, la vertu disparaît nécessairement ; "
            "l'injustice est commise avec impunité ; toute distinction est abolie "
            "entre les divers genres d'existence. Qui pourra raisonnablement accuser "
            "le débauché ou louer l'homme tempérant ? Pour Amand, ce passage 'assez "
            "bref' ne constitue pas un texte témoin mais 'une condensation "
            "schématique d'un ou deux arguments éthiques de Carnéade' versée au "
            "dossier de l'utilisation par les écrivains chrétiens — à titre de lieu "
            "commun scolaire indispensable à toute polémique anti-heimarmene."
        ),
        description_en=(
            "Argument from Gregory of Nyssa's Catechetical Discourse 31 (ed. Srawley "
            "p. 113-114; PG 45, 77BD), framed by a theological aporia: why does God "
            "not force unbelievers to embrace the faith? Gregory's reply (summarising "
            "one or two ethical Carneadean arguments): this would destroy free will "
            "and, with it, virtue. Without free will, praise and blame cannot apply "
            "to human actions. If the will remains inactive, virtue necessarily "
            "disappears; injustice is committed with impunity; all distinction "
            "between modes of life is abolished. Who could reasonably accuse the "
            "debauched man or praise the temperate one? For Amand, this 'rather "
            "brief' passage is not a witness text but 'a schematic condensation of "
            "one or two ethical Carneadean arguments' contributed to the dossier of "
            "Christian writers' use — as a schoolroom commonplace indispensable for "
            "any anti-heimarmene polemic."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 432-435",
            md_line_range="ll. 22391-22534",
            chapter="Livre II Ch. IX §IV (Disc. cat. 31)",
            amand_chapter_actual="Grégoire de Nysse (Disc. cat. 31)",
            extra={
                "amand_evidence_loc": "ed. Srawley p. 113-114 = PG 45, 77BD",
                "argument_type": "carneadean_moral_topos_condensed",
                "amand_witness_role": "scholastic_topos_not_witness",
                "evidence_pending": True,
                "evidence_pending_reason": "Or. cat. 31 (PG 45, 77BD) absent from EleutherIA corpus",
            },
        ),
        confidence=0.9,
        needs_evidence=True,
    ),
]


# =============================================================================
# ARGUMENTS — Chrysostom witness 5 + first text + other (5)
# =============================================================================

NEW_ARGUMENTS_CHRYSOSTOM: list[dict[str, Any]] = [
    _node(
        id="argument_chrysostom_hom_goth_witness5_amand1945",
        type="argument",
        label="Chrysostome Hom. Goth 6 — texte témoin n°5 (argumentation morale carnéadienne)",
        description=(
            "Argument central de Jean Chrysostome dans l'Homélie après le discours du "
            "prêtre Goth, chapitre 6 (PG 63, 500 l.16 — 510 l.36). Pour Amand 1945 "
            "(Livre II Ch. XII §IV.2, p. 510-525), ce passage constitue le 'texte "
            "témoin n°5' — l'un des deux 'textes témoins' les plus détaillés et "
            "précis de l'argumentation morale antifataliste de Carnéade conservée "
            "dans la littérature grecque chrétienne. Cinq arguments structurés : "
            "(1) si l'homme est soumis à l'heimarmene, pourquoi punissons-nous les "
            "fautes, rougissons-nous de la honte, qualifions-nous d'insulte certaines "
            "paroles ? (2) la sévérité des châtiments domestiques, juridiques et "
            "pédagogiques n'a aucun sens dans l'hypothèse fataliste — nous "
            "pardonnerions au déterminé comme nous pardonnons au démoniaque ; "
            "(3) l'éducation des enfants (pédagogues, maîtres, menaces, gifles) "
            "implique un libre arbitre, sinon tout effort éducatif serait superflu ; "
            "(4) toutes les formes d'activité humaine (commerce maritime, agriculture, "
            "bâtiment, médecine, régime des malades) sont vaines si la vie et la mort "
            "sont réglées par l'heimarmene — or l'expérience prouve le contraire ; "
            "(5) si l'heimarmene détermine vertu et vice, nul ne mérite ni louange ni "
            "blâme ; il n'y a plus de différence entre l'homme juste et l'homme "
            "injuste. Conclusion : 'tout sera confusion, désordre et bouleversement. "
            "Il n'y aura plus ni vertu ni vice, ni sciences ni lois.' Amand publie le "
            "texte grec original (p. 514-518) puis sa traduction française intégrale."
        ),
        description_en=(
            "Central argument of John Chrysostom in the Homily after the Goth "
            "priest's discourse, chapter 6 (PG 63, 500 l.16 — 510 l.36). For Amand "
            "1945 (Book II Ch. XII §IV.2, p. 510-525), this passage constitutes "
            "'witness text n°5' — one of the two most detailed and precise 'witness "
            "texts' of Carneades' moral antifatalist argumentation preserved in "
            "Christian Greek literature. Five structured arguments: (1) if humans "
            "are subject to heimarmene, why do we punish faults, blush in shame, "
            "qualify certain words as insults? (2) the severity of domestic, "
            "judicial and pedagogical punishments has no sense under fatalism — we "
            "would forgive the determined as we forgive the demoniac; (3) the "
            "education of children (pedagogues, teachers, threats, slaps) implies "
            "free will, else every educational effort would be superfluous; (4) all "
            "forms of human activity (maritime trade, agriculture, building, "
            "medicine, dietary regimens) are vain if life and death are ruled by "
            "heimarmene — yet experience proves the contrary; (5) if heimarmene "
            "determines virtue and vice, no one deserves praise or blame; there is "
            "no longer any difference between the just and the unjust. Conclusion: "
            "'everything will be confusion, disorder and upheaval. There will be "
            "neither virtue nor vice, nor sciences nor laws.' Amand publishes the "
            "original Greek (p. 514-518) and its full French translation."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 510-525",
            md_line_range="ll. 25900-26076",
            chapter="Livre II Ch. XII §IV.2 (texte témoin n°5)",
            amand_chapter_actual="Jean Chrysostome (Hom. Goth ch. 6)",
            extra={
                "amand_evidence_pg": "PG 63, 500 l.16 — 510 l.36",
                "amand_witness_rank": "primary_witness_n5",
                "amand_witness_role": "witness_5_chrysostom",
                "is_witness_argument": True,
                "argument_type": "carneadean_moral_witness_text",
                "carneadean_arguments_count": 5,
                "evidence_pending": True,
                "evidence_pending_reason": "Chrysostom Hom. Goth ch. 6 (PG 63, 500-510) absent from corpus",
                "centonic_parallel": "Ps-Chrys Hom. On Perfect Love 3 (PG 56, 282-283)",
            },
        ),
        confidence=0.95,
        needs_evidence=True,
    ),
    _node(
        id="argument_chrysostom_hom_1tim_first_text_amand1945",
        type="argument",
        label="Chrysostome Hom. 1 Tim 1.3 — premier texte antifataliste",
        description=(
            "Argument antifataliste cité par Amand 1945 (Livre II Ch. XII §IV.1, "
            "p. 509-510) comme 'premier texte' du dossier Chrysostome. Source : Hom. "
            "1 Tim 1.3 (PG 62, 507 l.45 — 508 l.4). Le prédicateur déploie une "
            "réduction à l'absurde : si l'on croit à l'heimarmene et à la genesis, il "
            "faut renoncer à toute activité — ne sème pas, ne plante pas, ne sers pas "
            "comme soldat ; que tu le veuilles ou non, ce qui relève de la genesis "
            "s'accomplira absolument. Quel profit retirer des prières ? Pourquoi vivre "
            "en chrétien ? Mais l'argument inverse soutient la doctrine carnéadienne "
            ": les arts s'apprennent par les travaux et les fatigues, non par la "
            "genesis ; donc la genesis n'existe pas. Amand reconnaît que cet "
            "argument est 'une libre utilisation' de Carnéade — le ton dogmatique de "
            "la fin ne convient guère au probabilisme néo-académicien — mais il "
            "appartient pleinement au dossier de la transmission."
        ),
        description_en=(
            "Antifatalist argument cited by Amand 1945 (Book II Ch. XII §IV.1, p. "
            "509-510) as the 'first text' of the Chrysostom dossier. Source: Hom. 1 "
            "Tim 1.3 (PG 62, 507 l.45 — 508 l.4). The preacher deploys a reductio ad "
            "absurdum: if one believes in heimarmene and genesis, one must renounce "
            "all activity — do not sow, do not plant, do not serve as soldier; "
            "willing or unwilling, what depends on genesis will absolutely come to "
            "pass. What profit from prayers? Why live as a Christian? But the "
            "converse argument supports the Carneadean doctrine: arts are learnt "
            "through labour and fatigue, not through genesis; therefore genesis does "
            "not exist. Amand grants this argument is 'a free use' of Carneades — "
            "the dogmatic tone at the end fits poorly with neo-Academic probabilism "
            "— but it belongs fully to the transmission dossier."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 509-510",
            md_line_range="ll. 25871-25921",
            chapter="Livre II Ch. XII §IV.1 (premier texte)",
            amand_chapter_actual="Jean Chrysostome (Hom. 1 Tim)",
            extra={
                "amand_evidence_pg": "PG 62, 507 l.45 — 508 l.4",
                "amand_witness_rank": "ancillary_to_witness_5",
                "argument_type": "carneadean_futility_amplified",
                "evidence_pending": True,
                "evidence_pending_reason": "Chrysostom Hom. 1 Tim 1.3 absent from corpus",
            },
        ),
        confidence=0.9,
        needs_evidence=True,
    ),
    _node(
        id="argument_chrysostom_antiastrological_demonic_amand1945",
        type="argument",
        label="Chrysostome — argument démonique contre l'astrologie populaire",
        description=(
            "Argument récurrent de Chrysostome contre la croyance des chrétiens à "
            "l'heimarmene et à la genesis astrologique, témoignant de la persistance "
            "de la superstition fataliste dans son auditoire antiochien puis "
            "constantinopolitain. Cf. Hom. 2 Col (PG 62, 318 l.16-27) où le diable a "
            "réussi à induire les chrétiens à négliger la vertu et à adorer les "
            "démons en introduisant la croyance à la nécessité ; Hom. 1 Tim 1.3 (PG "
            "62, 507-510) où Chrysostome combat un auditeur scandalisé par l'insolent "
            "bonheur des riches et des méchants. Pour Amand 1945 (p. 502-504), ces "
            "passages témoignent de la fascination que le fatalisme exerçait sur les "
            "âmes même chrétiennes au IVe siècle, et fournissent le contexte "
            "rhétorique du recours à l'argumentation morale carnéadienne par "
            "Chrysostome. Argument enrichi par l'élément théologique-démonique "
            "spécifiquement chrétien."
        ),
        description_en=(
            "Recurring argument of Chrysostom against Christians' belief in "
            "heimarmene and astrological genesis, witnessing the persistence of "
            "fatalist superstition among his Antiochene and Constantinopolitan "
            "audience. Cf. Hom. 2 Col (PG 62, 318 l.16-27) where the devil "
            "succeeded in inducing Christians to neglect virtue and worship demons "
            "by introducing the belief in necessity; Hom. 1 Tim 1.3 (PG 62, 507-510) "
            "where Chrysostom debates a listener scandalised by the insolent "
            "happiness of the rich and wicked. For Amand 1945 (p. 502-504), these "
            "passages testify to the fascination fatalism exerted even on Christian "
            "souls in the 4th century, and supply the rhetorical context for "
            "Chrysostom's recourse to Carneadean moral argumentation. Argument "
            "enriched by the specifically Christian theological-demonic element."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 502-504",
            md_line_range="ll. 25540-25640",
            chapter="Livre II Ch. XII §III (polémique anti-astrologique)",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "amand_evidence_pg": "PG 62, 318 + PG 62, 507-510 + PG 56, 282-283",
                "argument_type": "demonological_antifatalism",
                "evidence_pending": False,
                "anchor_passages": [
                    "sc79_chrysostomus_de_providentia_chap2",
                    "sc79_chrysostomus_de_providentia_chap3",
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="argument_chrysostom_anti_hellenism_amand1945",
        type="argument",
        label="Chrysostome — anti-philosophie hellénique (triobolimaios)",
        description=(
            "Argument-cadre récurrent par lequel Chrysostome dénigre la philosophie "
            "grecque dans son ensemble : triobolimaios (qui ne vaut que trois oboles), "
            "fables, paroles, ostentation, vaine gloire (Hom. 21 Eph 3, PG 62, 153 ; "
            "Hom. 9 Jean 1, PG 59, 70-71 ; Hom. 43 Jean 1, PG 59, 349 ; Hom. 66 Jean 3, "
            "PG 59, 369-370 ; Disc. Babylas 2 et 9, PG 50, 536, 546 ; etc.). Pour Amand "
            "1945 (Livre II Ch. XII §I, p. 481-489), cette polémique d'ensemble — "
            "dirigée contre Platon (sépulcre blanchi), Pythagore (matérialiste "
            "absurde), Aristote (goûteur de sperme humain), Zénon (incestueux), "
            "Diogène le Cynique (impudique) — révèle un Chrysostome détaché de "
            "l'hellénisme à un degré inégalé parmi les Pères du IVe siècle. "
            "Paradoxalement, cette posture anti-philosophique ne l'empêche pas de "
            "transmettre l'argumentation carnéadienne avec la précision la plus "
            "remarquable du corpus patristique."
        ),
        description_en=(
            "Recurring framing argument by which Chrysostom denigrates Greek "
            "philosophy as a whole: triobolimaios (worth only three obols), fables, "
            "mere words, ostentation, vainglory (Hom. 21 Eph 3, PG 62, 153; Hom. 9 "
            "John 1, PG 59, 70-71; Hom. 43 John 1, PG 59, 349; Hom. 66 John 3, PG "
            "59, 369-370; Disc. Babylas 2 and 9, PG 50, 536, 546; etc.). For Amand "
            "1945 (Book II Ch. XII §I, p. 481-489), this overarching polemic — "
            "aimed at Plato (whitewashed tomb), Pythagoras (absurd materialist), "
            "Aristotle (taster of human sperm), Zeno (incestuous), Diogenes the "
            "Cynic (lewd) — reveals a Chrysostom detached from Hellenism to an "
            "unmatched degree among 4th-century Fathers. Paradoxically, this "
            "anti-philosophical stance does not prevent him from transmitting "
            "Carneadean argumentation with the most remarkable precision of the "
            "patristic corpus."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 481-489",
            md_line_range="ll. 24559-24953",
            chapter="Livre II Ch. XII §I (anti-philosophie)",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "amand_evidence_pg_multi": ["PG 62, 153", "PG 59, 70-71", "PG 59, 349", "PG 50, 546", "PG 57, 536"],
                "argument_type": "anti_philosophical_topos",
                "evidence_pending": True,
                "evidence_pending_reason": "Chrysostom anti-Hellenic homilies absent from corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
    _node(
        id="argument_chrysostom_libre_arbitre_pastoral_amand1945",
        type="argument",
        label="Chrysostome — libre arbitre comme ressort de l'apostolat oratoire",
        description=(
            "Pour Amand 1945 (Livre II Ch. XII §II, p. 491-501), Chrysostome accorde "
            "au libre arbitre humain une importance capitale comme ressort moteur de "
            "son apostolat oratoire et réformateur. L'efficacité même de la "
            "prédication présuppose que l'auditeur puisse changer de conduite ; donc "
            "qu'il soit libre. Cette conviction homilétique-pratique alimente sa "
            "polémique contre tout déterminisme — astrologique, démonique, ou même "
            "providentialiste mal compris. Cf. notamment les six Discours sur le "
            "Destin et la Providence (PG 50, 749-774, en partie attribués à un "
            "Pseudo-Chrysostome) et les nombreuses sorties dans les commentaires sur "
            "Paul. Cette structure pratique-pastorale, et non spéculative-académique, "
            "explique le paradoxe Chrysostome — anti-hellénisme + transmission "
            "carnéadienne maximale."
        ),
        description_en=(
            "For Amand 1945 (Book II Ch. XII §II, p. 491-501), Chrysostom grants "
            "capital importance to human free will as the driving force of his "
            "oratorical and reforming apostolate. The very efficacy of preaching "
            "presupposes that the listener can change conduct; therefore that he is "
            "free. This homiletic-practical conviction fuels his polemic against "
            "every determinism — astrological, demonological, or even "
            "ill-understood providentialism. Cf. especially the six Discourses on "
            "Fate and Providence (PG 50, 749-774, partly attributed to a "
            "Pseudo-Chrysostom) and the many outbursts in the commentaries on Paul. "
            "This practical-pastoral structure, not speculative-academic, explains "
            "the Chrysostom paradox — anti-Hellenism + maximal Carneadean "
            "transmission."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 491-501",
            md_line_range="ll. 25100-25530",
            chapter="Livre II Ch. XII §II (libre arbitre dans l'apostolat)",
            amand_chapter_actual="Jean Chrysostome",
            extra={
                "argument_type": "pastoral_freewill_foundation",
                "evidence_pending": False,
                "anchor_passages": [
                    "sc79_chrysostomus_de_providentia_chap1",
                    "sc79_chrysostomus_de_providentia_chap2",
                    "sc79_chrysostomus_de_providentia_chap4",
                ],
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# ARGUMENTS — Pseudo-Chrysostom De Fato V witness 6 (3)
# =============================================================================

NEW_ARGUMENTS_PSEUDO_CHRYS: list[dict[str, Any]] = [
    _node(
        id="argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
        type="argument",
        label="Pseudo-Chrysostom De Fato V — texte témoin n°6 (récapitulation carnéadienne)",
        description=(
            "Argument central du Pseudo-Chrysostome dans le Discours sur le Destin et "
            "la Providence V (PG 50, 765 l.24 — 768 l.44). Pour Amand 1945 (Livre II "
            "Ch. XII §IV.3, p. 525-532), ce passage constitue le 'texte témoin n°6' "
            "— l'un des six textes témoins de l'argumentation morale antifataliste de "
            "Carnéade dans la reconstruction d'Amand. Neuf arguments accumulés "
            "(numérotés par Amand 1-9) : (1) image médicale — l'heimarmene ressemble à "
            "un homme qui pousse un malade à refuser tout médicament ; (2) inutilité "
            "des lois, juges, châtiments, honneurs et récompenses ; (3) absurdité de "
            "voir l'enfant fréquenter l'école, l'homme observer les lois ; (4) abolir "
            "agriculture, navigation, métiers — alors on verra ce que l'heimarmene "
            "produit ; (5) inutilité de réprimander l'enfant — si heimarmene fait les "
            "bons et les mauvais ; (6) traitement contradictoire des esclaves (qu'on "
            "punit mais en se croyant fataliste) ; (7) inutilité de la prière ; (8) "
            "absurdité et barbarie de l'heimarmene — elle pousse au vice et châtie ; "
            "(9) répétition condensée du premier argument. Suivi de la récapitulation "
            "oratoire célèbre : 'Si la genesis existe, il n'y a plus de justice. Si la "
            "genesis existe, il n'y a plus de foi. Si la genesis existe, Dieu n'existe "
            "pas. Si la genesis existe, il n'y a plus de vertu, il n'y a plus de "
            "vice. Si la genesis existe, tout se fait en vain.' Amand publie le texte "
            "grec original (p. 527-532) et sa traduction française intégrale "
            "(p. 522-527)."
        ),
        description_en=(
            "Central argument of the Pseudo-Chrysostom in the Discourse on Fate and "
            "Providence V (PG 50, 765 l.24 — 768 l.44). For Amand 1945 (Book II Ch. "
            "XII §IV.3, p. 525-532), this passage constitutes 'witness text n°6' — "
            "one of the six witness texts of Carneades' moral antifatalist "
            "argumentation in Amand's reconstruction. Nine accumulated arguments "
            "(numbered by Amand 1-9): (1) medical image — heimarmene resembles a man "
            "who urges a sick person to refuse all medicine; (2) uselessness of "
            "laws, judges, punishments, honours and rewards; (3) absurdity of seeing "
            "the child attend school, the man observe laws; (4) abolish agriculture, "
            "navigation, crafts — then we'll see what heimarmene produces; (5) "
            "uselessness of reprimanding the child if heimarmene makes the good and "
            "the bad; (6) contradictory treatment of slaves (whom one punishes "
            "though calling oneself fatalist); (7) uselessness of prayer; (8) "
            "absurdity and barbarism of heimarmene — it pushes to vice and punishes; "
            "(9) condensed repetition of the first argument. Followed by the famous "
            "oratorical recapitulation: 'If genesis exists, there is no justice. If "
            "genesis exists, there is no faith. If genesis exists, God does not "
            "exist. If genesis exists, there is neither virtue nor vice. If genesis "
            "exists, everything is done in vain.' Amand publishes the Greek original "
            "(p. 527-532) and full French translation (p. 522-527)."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 525-532",
            md_line_range="ll. 27000-27634",
            chapter="Livre II Ch. XII §IV.3 (texte témoin n°6)",
            amand_chapter_actual="Pseudo-Chrysostome (De Fato V)",
            extra={
                "amand_evidence_pg": "PG 50, 765 l.24 — 768 l.44",
                "amand_witness_rank": "primary_witness_n6",
                "amand_witness_role": "witness_6_pseudo_chrysostom",
                "is_witness_argument": True,
                "argument_type": "carneadean_moral_witness_text",
                "carneadean_arguments_count": 9,
                "evidence_pending": True,
                "evidence_pending_reason": "Ps-Chrysostom De Fato et Providentia V (PG 50, 765-768) absent from corpus",
            },
        ),
        confidence=0.95,
        needs_evidence=True,
    ),
    _node(
        id="argument_pseudo_chrysostom_de_fato_recapitulation_amand1945",
        type="argument",
        label="Pseudo-Chrysostom De Fato V — récapitulation oratoire 'εἰ γένεσίς ἐστι, ...'",
        description=(
            "Récapitulation oratoire célèbre du Pseudo-Chrysostome à la fin du "
            "Discours V (PG 50, 768 l.30-44). Climax rhétorique condensant en huit "
            "négations parallèles toute l'argumentation morale antifataliste "
            "déployée : 'Si la genesis existe, il n'y a plus de justice (krisis). Si "
            "la genesis existe, il n'y a plus de foi. Si la genesis existe, Dieu "
            "n'existe pas. Si la genesis existe, il n'y a plus de vertu, il n'y a "
            "plus de vice. Si la genesis existe, tout se fait en vain ; tout ce que "
            "nous faisons et subissons est inutile. Si la genesis existe, il n'y a "
            "plus de louange, il n'y a plus de blâme ; il n'y a plus de pudeur, il "
            "n'y a plus de honte ; il n'y a plus de lois, il n'y a plus de tribunaux.' "
            "Pour Amand 1945 (p. 526-527), ce climax est le plus remarquable "
            "résumé patristique de la trame des conséquences morales désastreuses "
            "qu'attribuait Carnéade à la doctrine de l'heimarmene — point "
            "d'aboutissement de la reconstruction conjecturale."
        ),
        description_en=(
            "Famous oratorical recapitulation of the Pseudo-Chrysostom at the close "
            "of Discourse V (PG 50, 768 l.30-44). Rhetorical climax condensing into "
            "eight parallel negations the entire moral antifatalist argumentation "
            "deployed: 'If genesis exists, there is no justice (krisis). If genesis "
            "exists, there is no faith. If genesis exists, God does not exist. If "
            "genesis exists, there is neither virtue nor vice. If genesis exists, "
            "everything is done in vain; everything we do and suffer is useless. If "
            "genesis exists, there is no praise, no blame; there is no modesty, no "
            "shame; there are no laws, no courts.' For Amand 1945 (p. 526-527), this "
            "climax is the most remarkable patristic summary of the chain of "
            "disastrous moral consequences Carneades ascribed to the heimarmene "
            "doctrine — culmination of the conjectural reconstruction."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 526-527, 531-532",
            md_line_range="ll. 26996-27004, 27585-27633",
            chapter="Livre II Ch. XII §IV.3 climax",
            amand_chapter_actual="Pseudo-Chrysostome (De Fato V récapitulation)",
            extra={
                "amand_evidence_pg": "PG 50, 768 l.30-44",
                "amand_witness_role": "climax_of_witness_6",
                "argument_type": "rhetorical_recapitulation",
                "negations_count": 8,
                "evidence_pending": True,
                "evidence_pending_reason": "Ps-Chrysostom De Fato V (PG 50) absent from corpus",
            },
        ),
        confidence=0.95,
        needs_evidence=True,
    ),
    _node(
        id="argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945",
        type="argument",
        label="Pseudo-Chrysostom De Fato V — heimarmene comme barbarie injuste",
        description=(
            "Argument du Pseudo-Chrysostome dans le Discours V (8e argument selon "
            "Amand, PG 50, 767-768) : l'heimarmene est doublement absurde et barbare "
            "— elle pousse les hommes au vice par contrainte, puis exige leur "
            "supplice pour les fautes ainsi commises. Comparaisons : un homme qui en "
            "pousse un autre dans le gouffre puis le retire pour l'accuser de "
            "suicide ; un homme qui livre son prochain à une maîtresse cruelle puis "
            "réclame son châtiment en invoquant l'esclavage. Les ennemis savent "
            "pardonner aux ennemis quand l'acte est involontaire ; mais l'heimarmene "
            "ne sait pardonner à ses sujets qui lui obéissent. 'Quel bourbier, quel "
            "labyrinthe, quelle tempête peuvent donner l'image d'une si parfaite "
            "confusion ?' L'heimarmene est qualifiée d'Erinnye ('cette Erinnye "
            "gouvernant les choses humaines confond et brouille toutes choses')."
        ),
        description_en=(
            "Pseudo-Chrysostom's argument in Discourse V (Amand's 8th argument, PG "
            "50, 767-768): heimarmene is doubly absurd and barbaric — it pushes "
            "humans to vice through constraint, then demands their punishment for "
            "the faults thus committed. Comparisons: a man who pushes another into "
            "the abyss then pulls him out to accuse him of suicide; a man who hands "
            "over his neighbour to a cruel mistress then demands his punishment "
            "invoking slavery. Enemies know how to forgive enemies when the act is "
            "involuntary; but heimarmene cannot forgive its subjects who obey it. "
            "'What mire, what labyrinth, what tempest can match this perfect "
            "confusion?' Heimarmene is called an Erinys ('this Erinys governing "
            "human affairs confuses and tangles everything')."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 525-526",
            md_line_range="ll. 26900-26960",
            chapter="Livre II Ch. XII §IV.3 arg 8 (texte témoin n°6)",
            amand_chapter_actual="Pseudo-Chrysostome (De Fato V)",
            extra={
                "amand_evidence_pg": "PG 50, 767-768",
                "argument_type": "carneadean_paradox_punishment",
                "evidence_pending": True,
                "evidence_pending_reason": "Ps-Chrysostom De Fato V (PG 50) absent from corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
]


# =============================================================================
# ARGUMENTS — Nemesius Nat. Hom. 35-38 (4)
# =============================================================================

NEW_ARGUMENTS_NEMESIUS: list[dict[str, Any]] = [
    _node(
        id="argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
        type="argument",
        label="Némésios Nat. Hom. 35 — résumé sec de l'argumentation morale carnéadienne",
        description=(
            "Résumé sec et squelettique de l'argumentation morale antifataliste de "
            "Carnéade inséré par Némésios au début du chapitre 35 du Peri physeos "
            "anthropou (PG 40, 741 BC, l. 18-33). Pour Amand 1945 (Livre II Ch. XIV "
            "§IV, p. 568-569), le passage énumère cinq conséquences absurdes du "
            "fatalisme astrologique : (1) les lois sont absurdes ; (2) les tribunaux "
            "sont superflus, condamnant des innocents ; (3) blâmes et louanges n'ont "
            "plus de raison d'être ; (4) les prières sont insensées ; (5) Providence "
            "et religion sont bannies de la vie humaine, l'homme n'étant plus qu'un "
            "instrument dirigé par les mouvements circulaires des corps célestes — "
            "ceux-ci meuvent et gouvernent les actions, non seulement les diverses "
            "parties du corps, mais aussi les pensées et les vouloirs. Conclusion : "
            "supprimer le libre arbitre, c'est supprimer la nature même du "
            "contingent. Pour Amand, cet exposé 'desséché et stérile' est copié par "
            "Némésios d'un commentaire péripatéticien perdu sur EN III (IIe-IIIe s.) "
            "sans amplification — illustration de la dégradation manualiste de la "
            "matière carnéadienne. Texte grec donné en note (p. 568)."
        ),
        description_en=(
            "Dry and skeletal summary of Carneades' moral antifatalist argumentation "
            "inserted by Nemesius at the start of chapter 35 of the Peri physeos "
            "anthropou (PG 40, 741 BC, l. 18-33). For Amand 1945 (Book II Ch. XIV "
            "§IV, p. 568-569), the passage enumerates five absurd consequences of "
            "astrological fatalism: (1) laws are absurd; (2) courts are superfluous, "
            "condemning the innocent; (3) blame and praise lose their ground; (4) "
            "prayers are senseless; (5) Providence and religion are banished from "
            "human life, man being but an instrument directed by the circular "
            "motions of celestial bodies — these move and govern actions, not only "
            "the various parts of the body but also thoughts and volitions. "
            "Conclusion: to suppress free will is to suppress the very nature of "
            "the contingent. For Amand, this 'desiccated and sterile' exposition is "
            "copied by Nemesius from a lost Peripatetic commentary on EN III "
            "(2nd-3rd c.) without amplification — illustration of the manual-driven "
            "degradation of Carneadean matter. Greek text given in Amand's note "
            "(p. 568)."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 568-569",
            md_line_range="ll. 29202-29272",
            chapter="Livre II Ch. XIV §IV (Nat. Hom. 35 résumé carnéadien)",
            amand_chapter_actual="Némésios d'Émèse (Nat. Hom. 35)",
            extra={
                "amand_evidence_pg": "PG 40, 741 BC, l. 18-33",
                "argument_type": "carneadean_moral_topos_decayed",
                "amand_witness_role": "secondary_witness_decayed",
                "carneadean_consequences_count": 5,
                "evidence_pending": True,
                "evidence_pending_reason": "Nemesius Nat. Hom. 35 (PG 40, 741) absent from corpus",
            },
        ),
        confidence=0.9,
        needs_evidence=True,
    ),
    _node(
        id="argument_nemesius_nat_hom_35_blasphemy_amand1945",
        type="argument",
        label="Némésios Nat. Hom. 35 — preuve théologique du 'blasphème' contre les astres",
        description=(
            "Argument théologique ajouté par Némésios à l'argumentation morale "
            "carnéadienne dans Nat. Hom. 35 (PG 40, 741 C, l. 33 — 744 A, l. 9). Les "
            "astres eux-mêmes sont injustes, puisqu'ils produisent les adultères et "
            "les homicides. Plus grave encore : Dieu lui-même est responsable de ces "
            "crimes, s'il a créé des astres capables de causer nécessairement les "
            "forfaits. Pour Amand 1945 (p. 563), cet argument 'plutôt théologique, "
            "rabâché par l'apologétique chrétienne' n'est pas démontrablement "
            "carnéadien — il représente l'apport spécifiquement chrétien-apologétique "
            "à la trame héritée. L'évêque syrien conclut en soulignant à la fois "
            "l'absurdité du fatalisme astrologique radical (ruinant toute vie "
            "sociale) et l'impiété d'une doctrine qui fait retomber sur Dieu la "
            "responsabilité des maux moraux."
        ),
        description_en=(
            "Theological argument added by Nemesius to the Carneadean moral "
            "argumentation in Nat. Hom. 35 (PG 40, 741 C, l. 33 — 744 A, l. 9). The "
            "stars themselves are unjust, since they produce adulteries and "
            "homicides. Worse still: God himself is responsible for these crimes if "
            "he has created stars capable of necessarily causing the misdeeds. For "
            "Amand 1945 (p. 563), this argument 'rather theological, rehashed by "
            "Christian apologetics' is not demonstrably Carneadean — it represents "
            "the specifically Christian-apologetic addition to the inherited "
            "framework. The Syrian bishop concludes by stressing both the absurdity "
            "of radical astrological fatalism (ruining all social life) and the "
            "impiety of a doctrine that pins on God the responsibility for moral "
            "evils."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 563",
            md_line_range="ll. 28985-29008",
            chapter="Livre II Ch. XIV §III (Nat. Hom. 35 preuve du blasphème)",
            amand_chapter_actual="Némésios d'Émèse (Nat. Hom. 35)",
            extra={
                "amand_evidence_pg": "PG 40, 741 C — 744 A",
                "argument_type": "christian_apologetic_addition",
                "carneadean_certainty_per_amand": "low (specifically Christian)",
                "evidence_pending": True,
                "evidence_pending_reason": "Nemesius Nat. Hom. 35 (PG 40, 741-744) absent from corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
    _node(
        id="argument_nemesius_nat_hom_36_apotropaic_refutation_amand1945",
        type="argument",
        label="Némésios Nat. Hom. 36 — réfutation des rites apotropaïques égyptiens",
        description=(
            "Réfutation par Némésios des astrologues égyptiens qui affirment "
            "l'heimarmene astrale tout en soutenant qu'on peut la détourner par des "
            "prières et des cérémonies apotropaïques (Nat. Hom. 36, PG 40, 745 BC — "
            "749 B). Deux arguments péripatéticiens (sans retouche chrétienne) : "
            "(1) ces astrologues rapportent l'heimarmene au contingent et non au "
            "nécessaire — or le contingent est illimité, indéterminé, inconnaissable ; "
            "leur opinion détruit donc toute forme de divination et ruine la science "
            "des généthlialogues elle-même ; pourquoi seules les prières et "
            "cérémonies seraient-elles dépendantes de notre volonté, alors que tout "
            "le reste serait soumis à l'heimarmene ? (2) si la science des rites "
            "apotropaïques est possédée par tous, la puissance de l'heimarmene est "
            "détruite ; si elle n'est possédée que par certains, c'est l'heimarmene "
            "qui distribue ce privilège — et celui qui le distribue (démon ou autre "
            "heimarmene) est injuste, certains étant favorisés. Argument "
            "péripatéticien sec et dialectique."
        ),
        description_en=(
            "Nemesius' refutation of the Egyptian astrologers who affirm astral "
            "heimarmene yet maintain it can be averted by prayers and apotropaic "
            "ceremonies (Nat. Hom. 36, PG 40, 745 BC — 749 B). Two Peripatetic "
            "arguments (without Christian retouching): (1) these astrologers refer "
            "heimarmene to the contingent and not the necessary — yet the contingent "
            "is unlimited, indeterminate, unknowable; their opinion thus destroys "
            "every form of divination and ruins the science of horoscope-casters "
            "themselves; why should only prayers and ceremonies depend on our will "
            "while all the rest is subject to heimarmene? (2) if the science of "
            "apotropaic rites is possessed by all, heimarmene's power is destroyed; "
            "if only by some, heimarmene itself distributes this privilege — and "
            "whoever distributes it (demon or another heimarmene) is unjust, since "
            "some are favoured. Dry and dialectical Peripatetic argument."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 564-565",
            md_line_range="ll. 29017-29109",
            chapter="Livre II Ch. XIV §III (Nat. Hom. 36 anti-apotropaïque)",
            amand_chapter_actual="Némésios d'Émèse (Nat. Hom. 36)",
            extra={
                "amand_evidence_pg": "PG 40, 745 BC — 749 B",
                "argument_type": "peripatetic_anti_apotropaic",
                "carneadean_certainty_per_amand": "none (Peripatetic specific)",
                "evidence_pending": True,
                "evidence_pending_reason": "Nemesius Nat. Hom. 36 (PG 40, 745-749) absent from corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
    _node(
        id="argument_nemesius_nat_hom_37_38_middle_platonism_critique_amand1945",
        type="argument",
        label="Némésios Nat. Hom. 37-38 — critique péripatéticienne du fatalisme du platonisme moyen",
        description=(
            "Critique péripatéticienne (transcrite par Némésios des chapitres 37-38 du "
            "Peri physeos anthropou, PG 40, 749 B — 760 A) de la théorie du "
            "platonisme moyen — caractéristique du Pseudo-Plutarque Peri "
            "heimarmenes — qui prétend concilier libre arbitre et heimarmene en "
            "attribuant à la liberté le choix des actions et à l'heimarmene leurs "
            "conséquences. Pour Némésios suivant sa source péripatéticienne, cette "
            "théorie 'hybride' est frappée d'une contradiction interne : elle retire "
            "de fait tout pouvoir à l'heimarmene, contraire à la définition stoïcienne "
            "(eirmos tis aition aparabatos, taxis kai episundesis aparallaktos). Le "
            "chapitre 37 dénonce aussi le problème des déments qui ne peuvent plus "
            "délibérer librement. Conclusion : la théorie composite mène "
            "directement au fatalisme stoïcien intégral. Le chapitre 38 ajoute des "
            "considérations théologiques chrétiennes (arrêt du soleil par Josué, "
            "conservation en vie d'Énoch et Élie) montrant la puissance absolue de "
            "Dieu — gouvernement divin indépendant de toute contrainte. Némésios "
            "expose ensuite le 'dogme' stoïcien du retour éternel (ekpyrosis + "
            "apokatastasis) sans le combattre, se bornant à le distinguer de la "
            "résurrection chrétienne (unique et non cyclique)."
        ),
        description_en=(
            "Peripatetic critique (transcribed by Nemesius from chapters 37-38 of the "
            "Peri physeos anthropou, PG 40, 749 B — 760 A) of the Middle Platonist "
            "theory — typical of Pseudo-Plutarch Peri heimarmenes — which claims to "
            "reconcile free will and heimarmene by attributing to freedom the choice "
            "of actions and to heimarmene their consequences. For Nemesius "
            "following his Peripatetic source, this 'hybrid' theory is struck by an "
            "internal contradiction: it in fact withdraws all power from "
            "heimarmene, contrary to the Stoic definition (eirmos tis aition "
            "aparabatos, taxis kai episundesis aparallaktos). Chapter 37 also "
            "denounces the problem of the demented who can no longer freely "
            "deliberate. Conclusion: the composite theory leads directly to "
            "integral Stoic fatalism. Chapter 38 adds Christian theological "
            "considerations (Joshua halting the sun, Enoch and Elijah preserved "
            "alive) showing God's absolute power — divine governance independent of "
            "every constraint. Nemesius then expounds the Stoic 'dogma' of eternal "
            "return (ekpyrosis + apokatastasis) without combating it, only "
            "distinguishing it from the Christian resurrection (unique and "
            "non-cyclic)."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 565-567",
            md_line_range="ll. 29085-29200",
            chapter="Livre II Ch. XIV §III (Nat. Hom. 37-38)",
            amand_chapter_actual="Némésios d'Émèse (Nat. Hom. 37-38)",
            extra={
                "amand_evidence_pg": "PG 40, 749 B — 760 A",
                "argument_type": "peripatetic_critique_middle_platonism",
                "carneadean_certainty_per_amand": "none (Peripatetic specific)",
                "targets": ["Pseudo-Plutarch Peri heimarmenes", "Chrysippus", "Philopator", "Stoic apokatastasis"],
                "evidence_pending": True,
                "evidence_pending_reason": "Nemesius Nat. Hom. 37-38 (PG 40) absent from corpus",
            },
        ),
        confidence=0.85,
        needs_evidence=True,
    ),
]


# =============================================================================
# CONCEPTS (3) — autexousion in Gregory of Nyssa, prohairesis in Disc. Cat., to eph hemin in Nemesius
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    _node(
        id="concept_prohairesis_gregory_nyssa",
        type="concept",
        label="Prohairesis (προαίρεσις) — Gregory of Nyssa",
        description=(
            "Concept de prohairesis (προαίρεσις) tel que défini par Grégoire de "
            "Nysse dans le Discours catéchétique 30 (ed. Srawley p. 112, l. 9-13 = "
            "PG 45, 77 A) : 'celui qui a le pouvoir sur l'univers, par excès "
            "d'honneur envers l'homme, a laissé quelque chose être aussi sous notre "
            "pouvoir — chose dont chacun est seul maître. C'est la prohairesis, "
            "chose non-asservie et autexousion, située dans la liberté de la "
            "pensée.' Pour Amand 1945 (p. 432, n. 2), cette définition résume la "
            "doctrine origénienne du libre arbitre adoptée par Grégoire et "
            "constitue le socle conceptuel sur lequel s'appuie sa polémique "
            "antifataliste — articulant prohairesis, autexousion et eleutheria tes "
            "dianoias dans un seul cadre humain de responsabilité morale."
        ),
        description_en=(
            "Concept of prohairesis (προαίρεσις) as defined by Gregory of Nyssa in "
            "the Catechetical Discourse 30 (ed. Srawley p. 112, l. 9-13 = PG 45, "
            "77 A): 'he who has power over all things, out of an excess of honour "
            "toward man, allowed something also to be under our power — something "
            "of which each of us alone is master. This is prohairesis, a "
            "non-enslaved and autexousion thing, lying in the freedom of thought.' "
            "For Amand 1945 (p. 432, n. 2), this definition summarises the "
            "Origenian doctrine of free will adopted by Gregory and constitutes the "
            "conceptual foundation on which his antifatalist polemic rests — "
            "articulating prohairesis, autexousion and eleutheria tes dianoias in "
            "a single human framework of moral responsibility."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 432",
            md_line_range="ll. 22422-22428",
            chapter="Livre II Ch. IX §IV (Disc. cat. 30 définition)",
            amand_chapter_actual="Grégoire de Nysse (Disc. cat. 30)",
            extra={
                "greek_term": "προαίρεσις",
                "amand_evidence_loc": "ed. Srawley p. 112, l. 9-13 = PG 45, 77 A",
                "linked_concepts": ["autexousion", "eleutheria tes dianoias"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="concept_sympatheia_universal_posidonius_nyssa",
        type="concept",
        label="Universal Sympatheia (μία ἐν τοῖς οὖσι συμπάθεια) — Posidonian dogma in Gregory CF",
        description=(
            "Doctrine posidonienne de la sympatheia universelle (mia tis estin en "
            "tois ousi sympatheia, kai syneches esti to pan heauto), telle "
            "qu'exposée par le philosophe païen stoïcisant interlocuteur de Grégoire "
            "de Nysse dans le Contre le Destin (PG 45, 152 CD ; texte cité par Amand "
            "1945 p. 437-438). Le tout est continu avec lui-même ; chaque partie "
            "est saisie dans le tout comme dans un corps unique, par une seule "
            "respiration commune, toutes les parties convergeant les unes vers les "
            "autres. Sur cette base, les mouvements des corps célestes dirigent à "
            "leur guise les mouvements subordonnés des corps terrestres — fondement "
            "métaphysique du fatalisme astrologique intégral. Pour Amand, ce passage "
            "est l'un des témoignages les plus nets de la transmission "
            "posidonienne au IVe siècle dans un texte chrétien (cf. Reinhardt "
            "1926). À distinguer de la sympathie universelle stoïcienne plus "
            "ancienne — la formulation est spécifiquement posidonienne."
        ),
        description_en=(
            "Posidonian doctrine of universal sympatheia (mia tis estin en tois "
            "ousi sympatheia, kai syneches esti to pan heauto), as expounded by "
            "the Stoicising pagan philosopher who serves as Gregory of Nyssa's "
            "interlocutor in the Contra Fatum (PG 45, 152 CD; text quoted by Amand "
            "1945 p. 437-438). The whole is continuous with itself; each part is "
            "grasped in the whole as in a single body, by one common breathing, "
            "all parts converging with each other. On this basis the motions of "
            "celestial bodies direct at will the subordinate motions of terrestrial "
            "bodies — metaphysical foundation of integral astrological fatalism. "
            "For Amand, this passage is one of the clearest testimonies to the "
            "Posidonian transmission in the 4th century in a Christian text (cf. "
            "Reinhardt 1926). To be distinguished from the older Stoic universal "
            "sympathy — the formulation is specifically Posidonian."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 423-424, 437-438",
            md_line_range="ll. 22056-22059, 22619-22626",
            chapter="Livre II Ch. IX §III.1 (Contre le Destin Posidonios)",
            amand_chapter_actual="Grégoire de Nysse (CF philosophe païen)",
            extra={
                "greek_term": "μία ἐν τοῖς οὖσι συμπάθεια",
                "amand_evidence_pg": "PG 45, 152 CD",
                "philosophical_source": "Posidonius via the Stoicising pagan philosopher",
                "modern_reference": "Reinhardt, Kosmos und Sympathie 1926",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="concept_to_eph_hemin_nemesius",
        type="concept",
        label="To eph' hemin (τὸ ἐφ᾽ ἡμῖν) — Nemesius",
        description=(
            "Concept du to eph' hemin (ce qui dépend de nous) tel que développé par "
            "Némésios dans le Peri physeos anthropou ch. 29-34 et 39-41, en stricte "
            "dépendance d'un commentaire péripatéticien perdu sur l'Éthique à "
            "Nicomaque III, 1-8 d'Aristote. Pour Amand 1945 (Livre II Ch. XIV §II, "
            "p. 558-562), Némésios développe une démonstration aristotélicienne "
            "complète : volontaire/involontaire (ch. 29-32), prohairesis distinguée "
            "de la boulesis et de la bouleusis (ch. 33-34), to eph' hemin et son "
            "champ d'application (ch. 39-41). Distinction cruciale entre dynameis "
            "(facultés innées et naturelles, hors libre arbitre) et hexeis "
            "(dispositions psychologiques, créées par la répétition d'actes vertueux "
            "ou vicieux, dans le champ du libre arbitre). Cette articulation "
            "aristotélicienne, transmise par un commentateur péripatéticien "
            "indéterministe du IIe-IIIe siècle, fonde la polémique anti-heimarmene "
            "de Nat. Hom. 35-38."
        ),
        description_en=(
            "Concept of to eph' hemin (what depends on us) as developed by Nemesius "
            "in Peri physeos anthropou ch. 29-34 and 39-41, in strict dependence on "
            "a lost Peripatetic commentary on Aristotle's Nicomachean Ethics III, "
            "1-8. For Amand 1945 (Book II Ch. XIV §II, p. 558-562), Nemesius "
            "develops a complete Aristotelian demonstration: voluntary/involuntary "
            "(ch. 29-32), prohairesis distinguished from boulesis and bouleusis "
            "(ch. 33-34), to eph' hemin and its field of application (ch. 39-41). "
            "Crucial distinction between dynameis (innate and natural faculties, "
            "beyond free will) and hexeis (psychological dispositions created by "
            "repetition of virtuous or vicious acts, within free will). This "
            "Aristotelian articulation, transmitted by an indeterminist Peripatetic "
            "commentator of the 2nd-3rd century, grounds the anti-heimarmene "
            "polemic of Nat. Hom. 35-38."
        ),
        period="Late Antiquity",
        metadata=amand_metadata(
            page_range="p. 558-562",
            md_line_range="ll. 28780-28967",
            chapter="Livre II Ch. XIV §II (théoricien du libre arbitre)",
            amand_chapter_actual="Némésios d'Émèse (Nat. Hom. 29-34, 39-41)",
            extra={
                "greek_term": "τὸ ἐφ᾽ ἡμῖν",
                "amand_evidence_pg": "PG 40, 729 A — 780 B (chs 29-34 and 39-41)",
                "philosophical_source": "lost Peripatetic commentary on EN III, 1-8 (2nd-3rd c., indeterminist)",
                "linked_concepts": ["prohairesis", "boulesis", "bouleusis", "dynameis vs hexeis"],
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# AGGREGATE
# =============================================================================

NEW_INSERTS: list[dict[str, Any]] = (
    NEW_PERSONS
    + NEW_WORKS
    + NEW_SYNTHESES
    + NEW_ARGUMENTS_GREGORY
    + NEW_ARGUMENTS_CHRYSOSTOM
    + NEW_ARGUMENTS_PSEUDO_CHRYS
    + NEW_ARGUMENTS_NEMESIUS
    + NEW_CONCEPTS
)
