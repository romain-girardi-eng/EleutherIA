"""Amand B6 — UPDATES list (description + metadata enrichments for existing nodes).

Updates are op:update operations on pre-existing nodes. Each entry specifies the
target node id, optional description/description_en/label patches, and metadata
keys to merge.
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # ---------------------------------------------------------------------------
    # 1. Eusebius of Caesarea — enrichissement portrait Amand
    # ---------------------------------------------------------------------------
    {
        "id": "person_eusebius_caesarea_d339",
        "description": (
            "Eusèbe de Césarée (c. 260-339 CE), évêque de Césarée de Palestine, historien "
            "ecclésiastique et apologiste chrétien. Pour Amand 1945 (Livre II Ch. VII, "
            "p. 342-381), Eusèbe constitue le **témoin n°4** de la transmission carnéadienne "
            "antifataliste : son livre VI de la Préparation évangélique (et particulièrement "
            "VI.6.4-21) forme l'un des deux 'textes témoins' les plus détaillés de "
            "l'argumentation morale de Carnéade, avec De Fato 16-20 d'Alexandre d'Aphrodise. "
            "Amand insiste : Eusèbe est essentiellement un archiviste — 'fureteur de bouquins', "
            "compilateur 'maniant habilement les ciseaux' à la bibliothèque de Césarée fondée "
            "par Pamphile (cf. P. Henry 1935). Formé à l'école de Pamphile et par lui à celle "
            "d'Origène, Eusèbe est un anténicéen conservateur, théologien de capacité médiocre "
            "selon Amand mais d'une 'érudition extraordinaire'. Sa fidélité philologique aux "
            "textes excerptés (démontrée par Henry sur Platon, Philon, Plutarque) fait du "
            "livre VI de la PE une source fiable pour les fragments perdus de Carnéade, "
            "Diogénianos, Alexandre d'Aphrodise, Bardesane et Origène. Pour la défense du "
            "libre arbitre, Eusèbe répète sans originalité la doctrine de son maître Origène."
        ),
        "description_en": (
            "Eusebius of Caesarea (c. 260-339 CE), bishop of Caesarea in Palestine, church "
            "historian and Christian apologist. For Amand 1945 (Book II Ch. VII, p. 342-381), "
            "Eusebius is the **fourth canonical witness** of the Carneadean antifatalist "
            "tradition: Praeparatio Evangelica Book VI (especially VI.6.4-21) constitutes "
            "one of the two most detailed 'witness texts' to Carneades' moral argumentation, "
            "alongside Alexander of Aphrodisias' De Fato 16-20. Amand stresses that Eusebius "
            "is essentially an archivist — a 'rummager of books', compiler 'skilfully wielding "
            "the scissors' at the Caesarean library founded by Pamphilus (cf. P. Henry 1935). "
            "Trained in the Pamphilian school and through him in the Origenist tradition, "
            "Eusebius is a conservative ante-Nicene, in Amand's view a theologian of mediocre "
            "originality but extraordinary erudition. His philological fidelity to excerpted "
            "texts (demonstrated by Henry for Plato, Philo, Plutarch) makes PE Book VI a "
            "reliable source for lost fragments of Carneades, Diogenianus, Alexander, "
            "Bardaisan and Origen. On free will, Eusebius repeats Origen's doctrine without "
            "originality."
        ),
        "metadata_updates": {
            "formation": "Pamphilus → Origenist school of Caesarea",
            "library": "Caesarea (Pamphilus foundation)",
            "composition_date_praep_ev": "315-321 CE (Schwartz; Henry 1935)",
            "amand_witness_rank": 4,
            "amand_chapter_treatment": "Livre II Ch. VII (p. 342-381)",
        },
    },

    # ---------------------------------------------------------------------------
    # 2. Praeparatio Evangelica — enrichissement metadata éditoriale
    # ---------------------------------------------------------------------------
    {
        "id": "work_eusebius_praeparatio_evangelica",
        "description": (
            "Praeparatio Evangelica d'Eusèbe de Césarée (c. 315-321 CE), monumentale "
            "apologie en 15 livres. Pour Amand 1945, le livre VI est consacré à la "
            "réfutation du fatalisme intégral, et son chapitre 6 (sections 4-21) "
            "constitue avec De Fato 16-20 d'Alexandre d'Aphrodise l'un des deux "
            "'textes témoins' les plus détaillés de l'argumentation morale antifataliste "
            "de Carnéade — sept arguments structurés (vs cinq chez Alexandre) suivis "
            "d'une conclusion psychologique sur l'évidence du libre arbitre. La PE est, "
            "selon P. Henry (1935), 'un florilège de textes profanes et sacrés, choisis "
            "et commentés dans un dessein apologétique' : son inestimable valeur tient à "
            "la conservation d'extraits perdus de Carnéade (via une source intermédiaire), "
            "Diogénianos (PE VI.8), Alexandre d'Aphrodise (PE VI.9), Bardesane (PE VI.10), "
            "Origène Comm. in Gen. (PE VI.11, quasi-littéralement parallèle à Philocalia 23) "
            "et Porphyre (PE VI.1-5 + V.16-36)."
        ),
        "description_en": (
            "Eusebius of Caesarea's Praeparatio Evangelica (c. 315-321 CE), monumental "
            "apologetic in 15 books. For Amand 1945, Book VI is devoted to refutation of "
            "integral fatalism, and chapter 6 (sections 4-21) constitutes — alongside "
            "Alexander of Aphrodisias' De Fato 16-20 — one of the two most detailed "
            "'witness texts' for Carneades' moral antifatalist argumentation: seven "
            "structured arguments (vs five in Alexander) followed by a psychological "
            "conclusion on the evidential immediacy of free will. The PE is, per P. Henry "
            "(1935), 'a florilegium of secular and sacred texts chosen and annotated for "
            "an apologetic purpose'; its inestimable value lies in preservation of lost "
            "excerpts from Carneades (via an intermediate source), Diogenianus (PE VI.8), "
            "Alexander of Aphrodisias (PE VI.9), Bardaisan (PE VI.10), Origen's Comm. in "
            "Genesim (PE VI.11, near-literally paralleling Philocalia 23) and Porphyry "
            "(PE VI.1-5 and V.16-36)."
        ),
        "metadata_updates": {
            "composition_date": "c. 315-321 CE (Schwartz; Henry 1935)",
            "book_vi_topic": "anti-fatalism polemic (Amand 1945 'witness text')",
            "amand_witness_rank": 4,
            "additional_editions": [
                {"raw": "Viger, Paris 1628 (princeps; reprinted in Migne PG 21)"},
                {"raw": "Dindorf, Teubner, Leipzig 1867 (Eusebii Caesariensis opera. Praeparatio euangelica)"},
                {"raw": "Gifford, Eusebii Pamphili euangelicae Praeparationis libri XV, Oxford Clarendon 1903"},
            ],
            "amand_cited_witness_text": "VI.6.4-21 (= Carneadean argumentum morale antifatalisticum)",
        },
    },

    # ---------------------------------------------------------------------------
    # 3. Basil the Great — enrichissement portrait Amand
    # ---------------------------------------------------------------------------
    {
        "id": "person_basil_great_d379",
        "description": (
            "Basile le Grand (c. 329/330-379 CE), évêque de Césarée de Cappadoce, "
            "l'un des trois Pères cappadociens (avec son frère Grégoire de Nysse et son "
            "ami Grégoire de Nazianze). Formé à Athènes auprès de Libanios, Himérios et "
            "Prohaerésios, métaphysicien malgré lui mais théologien plutôt que philosophe "
            "(Amand 1945, p. 385-386). Pour Amand, **Hex VI.5-7 — la digression "
            "antiastrologique de la sixième homélie sur l'Hexaéméron — constitue le point "
            "de départ de toute son étude sur Carnéade** (cf. avant-propos d'Amand : 'le "
            "point de départ fut une étude approfondie des chapitres 5, 6 et 7 de la "
            "sixième homélie de l'Hexaéméron'). Basile y déploie deux topoï carnéadiens "
            "explicites : (a) l'inutilité de la législation, des juges, des artisans si "
            "l'εἱμαρμένη domine ; (b) la destruction de la religion et — adaptation "
            "chrétienne — l'évanouissement des espérances eschatologiques. Amand établit "
            "la dépendance Origène → Basile via la Philocalie d'Origène que Basile compila "
            "avec son ami Grégoire de Nazianze. La signification de Basile pour le débat "
            "sur le libre arbitre tient à son articulation de ce que la théologie orientale "
            "ultérieure appellera synergisme : la grâce divine coopère avec, sans dominer, "
            "la libre volonté humaine. Sa polémique anti-'Chaldéens' (Hex VI.5-7) cible "
            "non l'astrologie scientifique de Ptolémée mais les charlatans de carrefour "
            "qu'écoutait la population semi-chrétienne de Césarée."
        ),
        "description_en": (
            "Basil the Great (c. 329/330-379 CE), bishop of Caesarea in Cappadocia, one "
            "of the three Cappadocian Fathers (with his brother Gregory of Nyssa and his "
            "friend Gregory of Nazianzus). Trained at Athens under Libanius, Himerius and "
            "Prohaeresius; a metaphysician reluctantly but more a theologian than a "
            "philosopher (Amand 1945, p. 385-386). For Amand, **Hexaemeron VI.5-7 — the "
            "anti-astrological digression of the sixth homily — is the very starting point "
            "of his entire study of Carneades** (cf. Amand's foreword: 'the starting "
            "point was a thorough study of chapters 5, 6 and 7 of the sixth homily on the "
            "Hexaemeron'). Basil there deploys two explicit Carneadean topoi: (a) the "
            "uselessness of legislation, judges, craftsmen if heimarmene rules; (b) the "
            "destruction of religion plus — Christian adaptation — the vanishing of "
            "eschatological hope. Amand establishes the Origen → Basil filiation via the "
            "Philocalia of Origen which Basil compiled with his friend Gregory of "
            "Nazianzus. Basil's significance for the free will debate lies in his "
            "articulation of what later Eastern theology would call synergism: divine grace "
            "cooperates with, rather than overrides, human free will. His anti-'Chaldean' "
            "polemic (Hex VI.5-7) targets not Ptolemy's scientific astrology but the "
            "street-corner charlatans heeded by the semi-Christianised population of "
            "Caesarea."
        ),
        "metadata_updates": {
            "formation": "Athens (Libanius, Himerius, Prohaeresius)",
            "philocalia_collaboration": "Philocalia of Origen, co-compiled with Gregory of Nazianzus",
            "hexaemeron_vi_significance": "Amand 1945 starting point — origin of Carneadean reception study",
            "amand_chapter_treatment": "Livre II Ch. VIII (p. 383-404)",
            "amand_carneadean_topoi_count": 2,
        },
    },
]
