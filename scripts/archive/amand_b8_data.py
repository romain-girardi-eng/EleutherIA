"""Amand B8 — UPDATES list (metadata enrichments for existing nodes).

Targets light enrichments only:
- person_plotinus_d270 : add amand chapter treatment metadata
- person_porphyry : add amand chapter treatment metadata + evolution note
- person_iamblichus_d325 : amand witness role
- person_proclus_412_485ce_f3d8b2a9 : amand witness role
- person_hierocles_of_alexandria_1p6q8s54 : amand witness role + key claim hooks
- argument_plotinus_freedom_argument_7c561972 : description upgrade with Amand framing
- work_plotinus_enn_iii_1 : amand witness role
- work_plotinus_ennead_vi_8_d8b9c5a4 : amand witness role
- work_porphyry_vita_plotini : amand witness role
- work_iamblichus_de_anima : amand witness role
- work_proclus_tria_opuscula_c9a8e4b3 : amand witness role
- person_chrysippus_280_206bce_i9j0k1l2 : amand metadata enrichment
- person_posidonius_apameia_135_51bce : amand metadata enrichment

No description rewrites for Plotinus / Chrysippus / Posidonius — descriptions already rich.
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. Plotinus — Amand treatment notes (Ch. VI §I)
    # -------------------------------------------------------------------------
    {
        "id": "person_plotinus_d270",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §I (p. 157-163)",
            "amand_witness_role": "non_witness_carneadean (Amand: Plotin n'utilise pas l'argumentation morale antifataliste de Carnéade)",
            "amand_explanation_e_silentio": (
                "Amand 1945, p. 157-163 : l'omission s'explique parce que (a) "
                "Plotin réduit le τὸ ἐφ' ἡμῖν à une spontanéité intérieure de "
                "l'intelligence vertueuse, (b) il maintient le déterminisme "
                "stoïcien et la sympatheia universelle posidonienne, (c) la "
                "distinction astres-signes vs astres-causes lui suffit à "
                "préserver le libre arbitre intellectuel sans recourir aux "
                "topoi carnéadiens"
            ),
            "amand_key_works_treated_in_ch_vi": [
                "Enn. III.1 (Peri Heimarmenes)",
                "Enn. II.3 (On the Influence of the Stars)",
                "Enn. VI.8 (On the Voluntary)",
                "Enn. IV.4.39 (Sympatheia/Mantike)",
            ],
        },
    },
    # -------------------------------------------------------------------------
    # 2. Porphyry — Amand treatment notes (Ch. VI §II.1)
    # -------------------------------------------------------------------------
    {
        "id": "person_porphyry",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §II.1 (p. 164-169)",
            "amand_witness_role": "minimal_echo_only (Amand: un seul et faible écho de l'argument carnéadien sur l'inutilité de la prière, dans Proclus In Tim. II prol. citant Porphyre)",
            "amand_intellectual_evolution": (
                "Amand 1945, p. 165-168 : Porphyre passe par une évolution : "
                "(a) jeunesse — Philosophie des oracles, superstition astrologique "
                "et magique grossière ; (b) après rencontre avec Plotin — Lettre "
                "à Anébon, critique sceptique de l'astrologie populaire ; (c) "
                "mais aussi Eisagoge eis ten Apotelesmatiken (Introduction à la "
                "Tétrabible de Ptolémée), vulgarisation astrologique 'scientifique' "
                "compatible avec un compromis providentialiste. Bipolarité que "
                "Bidez 1913 a documentée"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 3. Iamblichus — Amand treatment notes (Ch. VI §II.2)
    # -------------------------------------------------------------------------
    {
        "id": "person_iamblichus_d325",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §II.2 (p. 169-170)",
            "amand_witness_role": "non_witness_carneadean (théurge païen ; mantique et astrologie pleinement acceptées)",
            "amand_judgement": (
                "Amand 1945, p. 169-170 : Jamblique défend la liberté humaine "
                "intellectuelle dans la lignée plotinienne mais sa métaphysique "
                "dogmatique et superstitieuse, son culte des images, sa théurgie "
                "et sa foi aveugle aux Oracles chaldaïques le rendent imperméable "
                "à l'argumentation néo-académicienne de Carnéade. La concession "
                "que les dieux connaissent ce qui pour nous est indéterminé "
                "suffit à concilier mantique et libre arbitre"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 4. Proclus — Amand treatment notes (Ch. VI §II.3)
    # -------------------------------------------------------------------------
    {
        "id": "person_proclus_412_485ce_f3d8b2a9",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §II.3 (p. 170-171)",
            "amand_witness_role": "non_witness_carneadean (Amand a parcouru en vain les Commentaires sur la République et le Timée)",
            "amand_judgement": (
                "Amand 1945, p. 170-171 : 'parfait scolastique', Proclus défend "
                "simultanément le dogme platonicien du libre arbitre et la thèse "
                "de l'εἱμαρμένη. La conciliation se fait selon le schéma "
                "néoplatonicien général (les âmes choisissent leur destinée avant "
                "incarnation puis sont liées par leur choix). Aucun recours aux "
                "topoi carnéadiens"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 5. Hierocles of Alexandria — Amand treatment notes (Ch. VI §II.5)
    # -------------------------------------------------------------------------
    {
        "id": "person_hierocles_of_alexandria_1p6q8s54",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §II.5 (p. 171-176)",
            "amand_witness_role": "anomalous_user (Amand : Hiéroclès utilise un topos carnéadien pour prouver l'εἱμαρμένη providentielle — adaptation 'bizarre')",
            "amand_treatise_referenced": (
                "Περὶ προνοίας καὶ εἱμαρμένης καὶ τῆς τοῦ ἐφ' ἡμῖν πρὸς τὴν "
                "θείαν ἡγεμονίαν συντάξεως (en 7 livres, perdu, conservé en "
                "analyse + extraits par Photius, Bibl. cod. 251)"
            ),
            "amand_doctrine_key": (
                "Amand 1945, p. 173-176 : Hiéroclès remplace le caractère "
                "nécessaire et fatal de l'εἱμαρμένη par un concept proprement "
                "moral — celui du gouvernement divin (πρόνοια) qui punit et "
                "éduque les âmes selon leurs actes libres. L'εἱμαρμένη devient "
                "παιδεύουσα — pédagogique — et présuppose le libre arbitre au "
                "lieu de le détruire. Proximité doctrinale notée par Amand avec "
                "Origène et avec le platonisme moyen"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 6. Plotinus' Freedom Argument — light Amand framing
    # -------------------------------------------------------------------------
    {
        "id": "argument_plotinus_freedom_argument_7c561972",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §I.3 (p. 162-163)",
            "amand_reading": (
                "Pour Amand 1945, p. 162-163 : l'argument de la liberté chez "
                "Plotin (Enn. VI.8) restreint le τὸ ἐφ' ἡμῖν à la conformité de "
                "l'esprit au Bien et à la disposition vertueuse de "
                "l'intelligence — il ne couvre pas l'extension du libre arbitre "
                "qu'exige l'argumentation morale antifataliste de Carnéade. D'où "
                "l'omission systématique par Plotin des topoi néo-académiciens"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 7. Plotinus Enn III.1 (Peri Heimarmenes) — Amand witness identification
    # -------------------------------------------------------------------------
    {
        "id": "work_plotinus_enn_iii_1",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §I (p. 158-163)",
            "amand_witness_role": (
                "non-Carneadean treatise on Fate : Amand observe que ni ce traité "
                "ni Enn II.3 ne déploient l'argumentation morale néo-académicienne"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 8. Plotinus Enn VI.8 — Amand citation
    # -------------------------------------------------------------------------
    {
        "id": "work_plotinus_ennead_vi_8_d8b9c5a4",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §I.3 (p. 162-163)",
            "amand_witness_role": (
                "central source for Plotinus's restricted conception of liberty "
                "as intellectual self-determination (ch. 2, 6, 8 explicitly cited "
                "by Amand)"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 9. Porphyry Vita Plotini — Amand citation context
    # -------------------------------------------------------------------------
    {
        "id": "work_porphyry_vita_plotini",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §II.1 (p. 164-169)",
            "amand_witness_role": (
                "biographical frame for Porphyry's intellectual evolution vis-à-vis "
                "astrology and fate (cited via Bidez 1913)"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 10. Iamblichus De Anima — Amand witness role
    # -------------------------------------------------------------------------
    {
        "id": "work_iamblichus_de_anima",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §II.2 (p. 169-170)",
            "amand_witness_role": (
                "context for Iamblichus's intellectualist conception of "
                "τὸ ἐφ' ἡμῖν, similar to Plotinus's"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 11. Proclus Tria Opuscula — Amand witness role
    # -------------------------------------------------------------------------
    {
        "id": "work_proclus_tria_opuscula_c9a8e4b3",
        "metadata_updates": {
            "amand_chapter_treatment": "Livre I Ch. VI §II.3 (p. 170-171)",
            "amand_witness_role": (
                "Amand notes that Proclus's Commentaries on Republic and Timaeus "
                "(referenced alongside the Tria Opuscula) defend simultaneously "
                "libre arbitre and εἱμαρμένη without invoking Carneadean topoi"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 12. Chrysippus — Intro §I framing
    # -------------------------------------------------------------------------
    {
        "id": "person_chrysippus_280_206bce_i9j0k1l2",
        "metadata_updates": {
            "amand_intro_treatment": "Introduction §I.IV (p. 8-12, ll. 1815-1994)",
            "amand_judgement_summary": (
                "Pour Amand 1945, p. 8-12 : Chrysippe est le second fondateur du "
                "Portique et le principal théoricien du fatalisme stoïcien intégral. "
                "Sa loi cosmique impose εἱμαρμένη comme liaison infrangible et "
                "éternelle des causes ; même les volontés divines lui sont soumises. "
                "Ses distinctions subtiles (causes parfaites/principales vs "
                "adjuvantes/prochaines, cylindre, confatalia) tentent de sauvegarder "
                "la spontanéité psychologique de l'agent — mais en fait le τὸ ἐφ' "
                "ἡμῖν chrysippien se réduit à une simple spontanéité sans autonomie "
                "véritable. C'est contre cette doctrine que Carnéade dirigera son "
                "argumentation morale antifataliste"
            ),
        },
    },
    # -------------------------------------------------------------------------
    # 13. Posidonius — Intro §I framing
    # -------------------------------------------------------------------------
    {
        "id": "person_posidonius_apameia_135_51bce",
        "metadata_updates": {
            "amand_intro_treatment": "Introduction §I.IV (p. 12-13, ll. 2027-2073)",
            "amand_judgement_summary": (
                "Pour Amand 1945, p. 12-13 : Posidonius est magnus astrologus "
                "idemque philosophus (cit. Augustin De civ. Dei V.2, V.5) — "
                "représentant principal de la conjonction Orient-Occident dans le "
                "stoïcisme moyen. Il édifie sur la sympatheia universelle une "
                "nouvelle physique, une nouvelle mantique, une nouvelle théorie de "
                "la connaissance et une nouvelle théorie du Destin. L'astrologie y "
                "devient connaissance concrète de l'εἱμαρμένη — lien causal "
                "éternel et immuable. Toutefois (comme Panétios), Posidonius "
                "maintient l'αὐτεξούσιον, privilège du λογικὸν ζῷον"
            ),
        },
    },
]
