"""Destrée/Salles/Zingano 2014 B1 — UPDATES list.

Metadata-only enrichments on existing nodes (scholars + ancient persons +
ancient works + key concepts). No description overwrites except where the
existing description was minimal/placeholder and Destrée 2014 provides clear
scholarly context.

Tags every touched node with:
  - destree2014_treatment: short summary of how the volume treats it
  - destree2014_chapter, destree2014_author, destree2014_pages
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # ========================================================================
    # SCHOLAR UPDATES — anchor existing scholar nodes to this volume
    # ========================================================================
    {
        "id": "scholar_destr_e_p",
        "metadata_updates": {
            "destree2014_treatment": "Co-éditeur du volume; auteur du Ch. 2 sur Platon et le mythe d'Er",
            "destree2014_chapter": "Ch. 2 — How can our fate be up to us? Plato and the myth of Er",
            "destree2014_pages": "p. 31-52",
            "destree2014_role": "editor + chapter author",
            "linked_publication": "pub_destree_salles_zingano_2014_what_is_up_to_us",
            "linked_chapter_publication": "pub_destree_2014_plato_er",
        },
    },
    {
        "id": "scholar_frede_dorothea",
        "metadata_updates": {
            "destree2014_treatment": "Auteure du Ch. 3 'Free will in Aristotle?' — défend une lecture psychologiquement déterministe d'Aristote (pas de volonté, a fortiori pas de libre arbitre)",
            "destree2014_chapter": "Ch. 3 — Free will in Aristotle?",
            "destree2014_pages": "p. 53-75",
            "destree2014_position": "anti-indeterministic, psychological-deterministic reading of Aristotelian agency",
        },
    },
    {
        "id": "scholar_eche_ique_j",
        "metadata_updates": {
            "destree2014_treatment": "Auteur du Ch. 6 — défend la 'double position' aristotélicienne (compatibiliste sur les évaluations éthiques, incompatibiliste sur l'imputabilité)",
            "destree2014_chapter": "Ch. 6 — Aristotle on accountability and the principle of alternate possibilities",
            "destree2014_pages": "p. 115-135",
            "destree2014_thesis": "double position — compatibilist on appraisals, incompatibilist on accountability",
        },
    },
    {
        "id": "scholar_meyer_s",
        "metadata_updates": {
            "destree2014_treatment": "Auteure du Ch. 5 sur EE II 6 (bilatéralité ≠ PAP); éditrice de l'article posthume de M. Frede (Ch. 22)",
            "destree2014_chapter": "Ch. 5 — Aristotle on what is up to us and what is contingent + editorial Ch. 22",
            "destree2014_pages": "p. 93-114 + p. 351-363 (Frede posthumous edition)",
            "destree2014_role": "chapter author + editor of M. Frede posthumous reprint",
        },
    },
    {
        "id": "scholar_long_anthony",
        "metadata_updates": {
            "destree2014_treatment": "Cité comme adversaire scholarly de Salles dans le Ch. 11 (Long 2002 voit chez Épictète une rupture avec Chrysippe, contre quoi Salles défend une continuité causale)",
            "destree2014_rival_role_in_volume": "Salles ch. 11 engages Long 2002 (Epictetus, Stoic and Socratic Guide)",
        },
    },
    {
        "id": "scholar_brennan_tad",
        "metadata_updates": {
            "destree2014_treatment": "Cité comme adversaire scholarly de Salles dans le Ch. 11 (Brennan 2000 OSAP 21)",
            "destree2014_rival_role_in_volume": "Salles ch. 11 engages Brennan 2000 review of Bobzien",
        },
    },
    {
        "id": "scholar_natali_c",
        "metadata_updates": {
            "destree2014_treatment": "Cité par Maso (ch. 15) sur l'opposition causal-one-sided vs potestative-two-sided dans Natali 2007",
            "destree2014_referenced_in": "Ch. 15 (Maso), n. 22",
        },
    },
    {
        "id": "scholar_maso_s",
        "metadata_updates": {
            "destree2014_treatment": "Auteur du Ch. 15 'Motus animi voluntarius' — Cicéron, Épicure et la réception du clinamen lucrétien",
            "destree2014_chapter": "Ch. 15 — Motus animi voluntarius",
            "destree2014_pages": "p. 283-300",
        },
    },
    {
        "id": "scholar_gerson_l",
        "metadata_updates": {
            "destree2014_treatment": "Auteur du Ch. 16 sur Plotin et la responsabilité morale — construction d'une réponse plotinienne à l'argument de base de Galen Strawson",
            "destree2014_chapter": "Ch. 16 — Moral responsibility and what is 'up to us' in Plotinus",
            "destree2014_pages": "p. 301-322",
        },
    },
    {
        "id": "scholar_gourinat_jean_baptiste",
        "metadata_updates": {
            "destree2014_treatment": "Auteur du Ch. 9 'Adsensio in nostra potestate' — thèse iconoclaste : in nostra potestate ne traduit pas nécessairement eph' hêmin",
            "destree2014_chapter": "Ch. 9 — Adsensio in nostra potestate: 'from us' and 'to us' in ancient Stoicism",
            "destree2014_pages": "p. 169-181",
            "destree2014_iconoclastic_thesis": "Chrysippus may not have used eph' hêmin in Greek; preferred par' hêmas / ex hêmôn",
        },
    },
    {
        "id": "scholar_donini_p",
        "metadata_updates": {
            "destree2014_treatment": "Référencé par Zingano (ch. 13) sur Alexandre et la liberté ; non-contributeur du volume mais figure tutelaire",
            "destree2014_referenced_in": "Ch. 13 (Zingano)",
        },
    },
    # ========================================================================
    # ANCIENT PERSONS — anchor canonical targets discussed by the volume
    # ========================================================================
    {
        "id": "person_aristotle_384_322bce_c2d4f6a8",
        "metadata_updates": {
            "destree2014_treatment": "Sujet central de quatre chapitres (Ch. 3 Frede D., Ch. 4 Bobzien, Ch. 5 Sauvé Meyer, Ch. 6 Echeñique) — tous défendent une lecture déterministe ou anti-indéterministe",
            "destree2014_chapters": "Ch. 3-6",
            "destree2014_pages": "p. 53-135",
            "destree2014_thesis_collective": (
                "Le volume aligne quatre lectures convergentes : pas de "
                "volonté chez Aristote (D. Frede); EN III 1113b7-8 lu "
                "anti-indéterministe (Bobzien); bilatéralité du eph' "
                "hêmin ≠ PAP (Sauvé Meyer); double position "
                "compatibiliste/incompatibiliste sur "
                "appraisals/accountability (Echeñique)"
            ),
        },
    },
    {
        "id": "person_democritus_460_370bce_g7h8i9j0",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 1 (Johnson) — éthique intellectualiste fondée sur la plasticité de la nature humaine (gnômê, didachê), proto-thérapie cognitivo-comportementale",
            "destree2014_chapter": "Ch. 1 — Changing our minds: Democritus on what is up to us",
            "destree2014_pages": "p. 7-30",
            "destree2014_author": "Monte Ransome Johnson",
        },
    },
    {
        "id": "person_plato_428_348bce_a1b2c3d4",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 2 (Destrée) sur le mythe d'Er, et arrière-plan des Ch. 17 (Taormina) et Ch. 18 (Bonazzi)",
            "destree2014_chapters": "Ch. 2 (Destrée) + Ch. 17 (Taormina) + Ch. 18 (Bonazzi)",
            "destree2014_central_passage": "Plato Rep. X 617e (aitia helomenou, theos anaitios)",
        },
    },
    {
        "id": "person_chrysippus_280_206bce_i9j0k1l2",
        "metadata_updates": {
            "destree2014_treatment": "Sujet de deux chapitres (Ch. 8 Gómez sur le compatibilisme chrysippéen, Ch. 9 Gourinat sur in nostra potestate ≠ eph' hêmin)",
            "destree2014_chapters": "Ch. 8 (Gómez) + Ch. 9 (Gourinat)",
            "destree2014_pages": "p. 159-181",
            "destree2014_thesis_iconoclastic": "Gourinat: Chrysippus may not have used eph' hêmin in Greek (only par' hêmas / ex hêmôn)",
        },
    },
    {
        "id": "person_epictetus_of_hierapolis_3c385bc2",
        "metadata_updates": {
            "destree2014_treatment": "Sujet de trois chapitres (Ch. 11 Salles sur la conception causale, Ch. 21 Wildberg lu par Simplicius, Ch. 22 Frede M. sur la transition au libre arbitre)",
            "destree2014_chapters": "Ch. 11 (Salles) + Ch. 21 (Wildberg) + Ch. 22 (Frede M.)",
            "destree2014_pages": "p. 199-217 + p. 329-350 + p. 351-363",
            "destree2014_thesis_collective": (
                "Trois lectures triangulées : (1) continuité causale "
                "avec Chrysippe (Salles); (2) lecture néoplatonicienne "
                "tardive de Simplicius (Wildberg); (3) point-pivot "
                "vers le libre arbitre via Justin Martyr / Tatien "
                "(Frede M.)"
            ),
        },
    },
    {
        "id": "person_marcus_aurelius_121_180ce",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 12 (Boeri) — fonction du eph' hêmin via la conjonction du présent et des indifférents",
            "destree2014_chapter": "Ch. 12 — Present time and indifferents",
            "destree2014_pages": "p. 219-243",
            "destree2014_author": "Marcelo D. Boeri",
        },
    },
    {
        "id": "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 13 (Zingano) — libertarianisme alexandrien compatible avec déterminisme psychologique du caractère; lecture rétroprojective dans Aristote critiquée par Frede M. (Ch. 22)",
            "destree2014_chapters": "Ch. 13 (Zingano) + Ch. 22 (Frede M.)",
            "destree2014_pages": "p. 245-263 + p. 351-363",
            "destree2014_thesis_zingano": "Distinction liability (strong, contraries) / possibility (weak, equivalents)",
        },
    },
    {
        "id": "person_epicurus_341_270bce_j0k1l2m3",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 14 (Morel) — eph' hêmin comme évidence primaire, non comme demonstrandum",
            "destree2014_chapter": "Ch. 14 — The Epicurean 'up to us': not to be proved",
            "destree2014_pages": "p. 265-282",
            "destree2014_author": "Pierre-Marie Morel",
        },
    },
    {
        "id": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 15 (Maso) sur motus animi voluntarius et la réception du clinamen ; mobilisé par Ch. 9 (Gourinat) sur in nostra potestate",
            "destree2014_chapters": "Ch. 15 (Maso) + Ch. 9 (Gourinat)",
            "destree2014_pages": "p. 169-181 + p. 283-300",
            "destree2014_central_passages_maso": "Cicero De Fato 9, 25, 31, 40, 41, 45 + Tusc. 4.79",
        },
    },
    {
        "id": "person_plotinus_d270",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 16 (Gerson) — réponse plotinienne à l'argument de base de Galen Strawson ; responsabilité morale qualifiée",
            "destree2014_chapter": "Ch. 16 — Moral responsibility and what is 'up to us' in Plotinus",
            "destree2014_pages": "p. 301-322",
            "destree2014_author": "Lloyd P. Gerson",
            "destree2014_key_text": "Plotinus Enn. VI 8 [39] on the One as causa sui",
        },
    },
    {
        "id": "person_porphyry",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 17 (Taormina) — restriction du eph' hêmin à la partie rationnelle de l'âme humaine ; lecture du mythe d'Er",
            "destree2014_chapter": "Ch. 17 — Choice, self-determination and what is in our power in Porphyry's interpretation of the myth of Er",
            "destree2014_pages": "p. 323-340",
            "destree2014_author": "Daniela Patrizia Taormina",
            "destree2014_key_fragments": "Porphyry frr. 268-271 Smith = Stobaeus Anth. II 8 39-42",
        },
    },
    {
        "id": "person_proclus_412_485ce_f3d8b2a9",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 20 (Steel) — hiérarchie causale Providence > Destin > eph' hêmin (3e des Tria Opuscula)",
            "destree2014_chapter": "Ch. 20 — Human or divine freedom: Proclus on what is up to us",
            "destree2014_pages": "p. 311-328",
            "destree2014_author": "Carlos Steel",
            "destree2014_key_work": "Proclus De Providentia, Fato et eo quod in nobis",
        },
    },
    {
        "id": "person_simplicius_cilicia_490_560ce",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 21 (Wildberg) — lecture néoplatonicienne tardive d'Épictète dans le Commentaire sur l'Enchiridion (post-529 CE)",
            "destree2014_chapter": "Ch. 21 — The will and its freedom: Epictetus and Simplicius on what is up to us",
            "destree2014_pages": "p. 329-350",
            "destree2014_author": "Christian Wildberg",
            "destree2014_historical_context": "Post-Sasanian exile (529 CE Justinian closure of Academy)",
        },
    },
    {
        "id": "person_augustine_hippo_d430",
        "metadata_updates": {
            "destree2014_treatment": "Sujet du Ch. 19 (Horn) — liberum arbitrium comme équivalent et dépassement du eph' hêmin",
            "destree2014_chapter": "Ch. 19 — How close is Augustine's liberum arbitrium to the concept of to eph' hêmin?",
            "destree2014_pages": "p. 295-310",
            "destree2014_author": "Christoph Horn",
            "destree2014_key_passages": "De lib. arb. 2.3.7 + De civ. dei 11.26 + De trin. 10-15",
        },
    },
    {
        "id": "person_justin_martyr_2c_ce",
        "metadata_updates": {
            "destree2014_treatment": "Cité par Frede M. (Ch. 22) comme premier auteur chrétien lisant l'eph' hêmin épictétéen comme incompatible avec le destin stoïcien",
            "destree2014_referenced_in_chapter": "Ch. 22 (Frede M.)",
        },
    },
    {
        "id": "person_tatian",
        "metadata_updates": {
            "destree2014_treatment": "Cité par Frede M. (Ch. 22) comme co-récepteur (avec Justin) de l'eph' hêmin épictétéen contre le destin stoïcien",
            "destree2014_referenced_in_chapter": "Ch. 22 (Frede M.)",
        },
    },
    # ========================================================================
    # ANCIENT WORKS — key targets
    # ========================================================================
    {
        "id": "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9",
        "metadata_updates": {
            "destree2014_treatment": "Texte central des Ch. 3-6 du volume — EN III 1-5 (notion de eph' hêmin, voluntariness, prohairesis); EN III 1113b7-8 (cible centrale de Bobzien); EN III 5 (cible centrale d'Echeñique)",
            "destree2014_chapters": "Ch. 3 (D. Frede), Ch. 4 (Bobzien), Ch. 5 (Sauvé Meyer), Ch. 6 (Echeñique)",
            "destree2014_focus_passages": [
                "EN III 1-5 (entire books on voluntary action, choice, accountability)",
                "EN III 1113b7-8 (Bobzien anti-indeterminist reading)",
                "EN III 5 1114a (character accountability — Echeñique)",
                "EN VI on phronêsis (D. Frede)",
                "EN VII on akrasia (D. Frede)",
            ],
        },
    },
    {
        "id": "work_epictetus_discourses",
        "metadata_updates": {
            "destree2014_treatment": "Texte central des Ch. 11 (Salles sur Diss. I.11 philostorgia) et Ch. 22 (Frede M. sur Diss. I.1 + I.17 + 4.1)",
            "destree2014_chapters": "Ch. 11 (Salles) + Ch. 22 (Frede M.)",
            "destree2014_focus_passages": [
                "Diss. I.11 (philostorgia — Salles)",
                "Diss. I.1 + I.17 + 4.1 (general eph' hêmin — Frede M.)",
            ],
        },
    },
    {
        "id": "work_epictetus_enchiridion",
        "metadata_updates": {
            "destree2014_treatment": "Lu via le Commentaire de Simplicius dans le Ch. 21 (Wildberg)",
            "destree2014_chapter": "Ch. 21 (Wildberg)",
            "destree2014_secondary_text": "Simplicius In Epicteti Enchiridion (CAG)",
        },
    },
    {
        "id": "work_simplicius_in_enchiridion",
        "metadata_updates": {
            "destree2014_treatment": "Texte central du Ch. 21 (Wildberg) — lecture néoplatonicienne tardive d'Épictète post-529 CE",
            "destree2014_chapter": "Ch. 21 (Wildberg)",
            "destree2014_pages": "p. 329-350",
            "destree2014_historical_context": "Probablement rédigé après l'exil sassanide post-529 CE",
        },
    },
    {
        "id": "work_de_fato_alexander_c200ce_o6p7q8r9",
        "metadata_updates": {
            "destree2014_treatment": "Texte central du Ch. 13 (Zingano) sur les §§ 26-29 (caractère et action) ; mobilisé aussi par Frede M. (Ch. 22) sur la rétroprojection libre-arbitriste",
            "destree2014_chapter": "Ch. 13 (Zingano) + Ch. 22 (Frede M.)",
            "destree2014_focus_passage": "Alexander De Fato §§ 26-29 (Bruns p. 196.13-200.12)",
        },
    },
    {
        "id": "work_de_fato_cicero_44bce_b9c4e5d2",
        "metadata_updates": {
            "destree2014_treatment": "Texte central du Ch. 9 (Gourinat sur in nostra potestate) et Ch. 15 (Maso sur motus animi voluntarius)",
            "destree2014_chapters": "Ch. 9 (Gourinat) + Ch. 15 (Maso)",
            "destree2014_focus_passages": [
                "De Fato passim (in nostra potestate — Gourinat)",
                "De Fato 9, 25, 31, 40, 41, 45 (motus animi voluntarius — Maso)",
                "De Fato 40-44 (Chrysippean cylinder — Salles ch. 11)",
            ],
        },
    },
    {
        "id": "work_epicurus_letter_menoeceus",
        "metadata_updates": {
            "destree2014_treatment": "Texte central du Ch. 14 (Morel) sur l'argument cosmologique épicurien de l'évidence primaire du eph' hêmin",
            "destree2014_chapter": "Ch. 14 (Morel)",
            "destree2014_focus_passage": "Letter to Menoeceus 133 (par' hêmas — explicit Epicurean term)",
        },
    },
    {
        "id": "work_epicurus_on_nature_xxv",
        "metadata_updates": {
            "destree2014_treatment": "Texte central du Ch. 14 (Morel) sur l'argument éthique épicurien — absurdités morales de la négation de la liberté",
            "destree2014_chapter": "Ch. 14 (Morel)",
        },
    },
    {
        "id": "work_marcus_aurelius_meditations",
        "metadata_updates": {
            "destree2014_treatment": "Texte central du Ch. 12 (Boeri) — fonction du eph' hêmin via la conjonction présent + indifférents",
            "destree2014_chapter": "Ch. 12 (Boeri)",
            "destree2014_focus_passages": "Med. 2.17 (philosophy as way of life) + 4.3 (inner citadel) + 6.32 + 8.41-43",
        },
    },
    {
        "id": "work_proclus_tria_opuscula_c9a8e4b3",
        "metadata_updates": {
            "destree2014_treatment": "Texte central du Ch. 20 (Steel) — focalisation sur le troisième opuscule (De Providentia, Fato et eo quod in nobis)",
            "destree2014_chapter": "Ch. 20 (Steel)",
            "destree2014_focus_treatise": "Third opusculum: De Providentia, Fato et eo quod in nobis",
        },
    },
    {
        "id": "work_de_libero_arbitrio",
        "metadata_updates": {
            "destree2014_treatment": "Texte central du Ch. 19 (Horn) sur Augustin et le rapport entre liberum arbitrium et eph' hêmin",
            "destree2014_chapter": "Ch. 19 (Horn)",
            "destree2014_focus_passage": "De lib. arb. 2.3.7 (cogito-argument)",
        },
    },
    {
        "id": "work_augustine_de_libero_arbitrio",
        "metadata_updates": {
            "destree2014_treatment": "Cité par Horn (Ch. 19) sur Augustin et le rapport entre liberum arbitrium et eph' hêmin (variante alias du même traité)",
            "destree2014_chapter": "Ch. 19 (Horn)",
        },
    },
    # ========================================================================
    # KEY CONCEPTS — anchor central concepts
    # ========================================================================
    {
        "id": "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
        "metadata_updates": {
            "destree2014_treatment": "Concept-pivot de tout le volume Destrée 2014 — 20 chapitres convergeant sur l'analyse historique-conceptuelle du eph' hêmin",
            "destree2014_chapters": "Tous les 22 chapitres",
            "destree2014_collective_thesis": (
                "Le eph' hêmin commence sa vie philosophique chez "
                "Aristote (Ch. 3-6), est technique chez Chrysippe "
                "(controverse Gourinat ch. 9), devient causal chez "
                "Épictète (Salles ch. 11), critique du libertarianisme "
                "moderne (Sauvé Meyer ch. 5 anti-PAP). Le libre arbitre "
                "n'émerge qu'à l'antiquité tardive (Frede M. ch. 22 + "
                "Wildberg ch. 21 + Horn ch. 19)"
            ),
        },
    },
    {
        "id": "concept_eph_hemin_one_sided_causative",
        "metadata_updates": {
            "destree2014_treatment": "Cible centrale de Gourinat (Ch. 9), Salles (Ch. 11), Maso (Ch. 15) — distinction sémantique alignée avec Bobzien 1998",
            "destree2014_chapters_referenced": ["Ch. 9 (Gourinat)", "Ch. 11 (Salles)", "Ch. 15 (Maso)"],
        },
    },
    {
        "id": "concept_eph_hemin_two_sided_potestative",
        "metadata_updates": {
            "destree2014_treatment": "Concept distingué de Sauvé Meyer (ch. 5) en bilatéralité agent-contrôlée vs PAP de type Frankfurt 1969 (modern indeterminist)",
            "destree2014_chapter": "Ch. 5 (Sauvé Meyer) clarifies vs PAP",
        },
    },
    {
        "id": "concept_synkatathesis_stoic_assent",
        "metadata_updates": {
            "destree2014_treatment": "Concept central du Ch. 7 (Vogt sur l'assentiment cyclique stoïcien), Ch. 9 (Gourinat sur Chrysippean assensio), Ch. 11 (Salles sur Épictète), Ch. 22 (Frede M. sur la transition au libre arbitre)",
            "destree2014_chapters": ["Ch. 7 (Vogt)", "Ch. 9 (Gourinat)", "Ch. 11 (Salles)", "Ch. 22 (Frede M.)"],
        },
    },
    {
        "id": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
        "metadata_updates": {
            "destree2014_treatment": "Concept aristotélicien analysé dans Ch. 3 (D. Frede), Ch. 4 (Bobzien), Ch. 5 (Sauvé Meyer); transposé chez Épictète et discuté par Wildberg (Ch. 21)",
            "destree2014_chapters": ["Ch. 3-5", "Ch. 21 (Wildberg)"],
        },
    },
    {
        "id": "concept_hekousion_voluntary_aristotle_a1b2c3d4",
        "metadata_updates": {
            "destree2014_treatment": "Concept aristotélicien fondamental analysé conjointement au eph' hêmin dans tous les chapitres aristotéliciens (Ch. 3-6)",
            "destree2014_chapters": "Ch. 3-6",
        },
    },
    {
        "id": "concept_hypothetical_fate_middle_platonist",
        "metadata_updates": {
            "destree2014_treatment": "Concept central du Ch. 18 (Bonazzi) — doctrine platonicienne médiane qui rend compte d'actions individuelles mais non de leurs rapports mutuels",
            "destree2014_chapter": "Ch. 18 (Bonazzi)",
            "destree2014_pages": "p. 283-294 (approx.)",
            "destree2014_author": "Mauro Bonazzi",
            "destree2014_bonazzi_limit": "Accounts for individual actions/decisions but not for their mutual relations (= character as sedimented choices)",
        },
    },
    {
        "id": "concept_liberum_arbitrium_u3v4w5x6",
        "metadata_updates": {
            "destree2014_treatment": "Concept augustinien analysé dans Ch. 19 (Horn) comme équivalent fonctionnel et dépassement du eph' hêmin",
            "destree2014_chapter": "Ch. 19 (Horn)",
            "destree2014_thesis_horn": "Augustinian liberum arbitrium = functional equivalent of eph' hêmin + scope of individual moral responsibility",
        },
    },
    {
        "id": "concept_autexousion_alex",
        "metadata_updates": {
            "destree2014_treatment": "Concept alexandrien discuté par Zingano (Ch. 13) en lien avec character/action ; aussi mobilisé par Taormina (Ch. 17) chez Porphyre et par Steel (Ch. 20) chez Proclus",
            "destree2014_chapters": ["Ch. 13 (Zingano)", "Ch. 17 (Taormina)", "Ch. 20 (Steel)"],
        },
    },
    # ========================================================================
    # KEY ARGUMENTS (existing) — anchor with Destrée 2014 references
    # ========================================================================
    {
        "id": "argument_cylinder_analogy_chrysippus_k1l2m3n4",
        "metadata_updates": {
            "destree2014_treatment": "Cité dans Ch. 8 (Gómez) comme analogie psychique chrysippéenne, et dans Ch. 11 (Salles) comme modèle causal antérieur à Épictète",
            "destree2014_chapters": ["Ch. 8 (Gómez)", "Ch. 11 (Salles)"],
            "destree2014_central_text": "Cicero De Fato 40-44 (= SVF 2.974 + 977)",
        },
    },
    {
        "id": "argument_epicurean_swerve_for_freedom_m4n5o6p7",
        "metadata_updates": {
            "destree2014_treatment": "Cité comme prélude à l'argument cosmologique de Morel (Ch. 14) sur le eph' hêmin comme évidence primaire ; mobilisé aussi par Maso (Ch. 15) sur la réception cicéronienne du clinamen",
            "destree2014_chapters": ["Ch. 14 (Morel)", "Ch. 15 (Maso)"],
        },
    },
    {
        "id": "argument_epictetus_prohairesis_argument_aa13b932",
        "metadata_updates": {
            "destree2014_treatment": "Argument épictétéen central — Salles (Ch. 11) défend lecture causale en continuité avec Chrysippe ; Wildberg (Ch. 21) défend lecture néoplatonicienne par Simplicius ; Frede M. (Ch. 22) y voit le point-pivot vers le libre arbitre",
            "destree2014_chapters": ["Ch. 11 (Salles)", "Ch. 21 (Wildberg)", "Ch. 22 (Frede M.)"],
        },
    },
    {
        "id": "argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        "metadata_updates": {
            "destree2014_treatment": "Argument aristotélicien analysé dans tous les chapitres aristotéliciens — lecture déterministe/anti-indéterministe par D. Frede (Ch. 3), Bobzien (Ch. 4), Sauvé Meyer (Ch. 5), Echeñique (Ch. 6)",
            "destree2014_chapters": "Ch. 3-6",
        },
    },
    {
        "id": "argument_frankfurt_cases_1o2p3q4r",
        "metadata_updates": {
            "destree2014_treatment": "PAP de Frankfurt 1969 (Principle of Alternate Possibilities) critiqué par Sauvé Meyer (Ch. 5) comme application anachronique à Aristote ; aussi mobilisé par Maso (Ch. 15) comme grille interprétative à dépasser",
            "destree2014_chapters": ["Ch. 5 (Sauvé Meyer)", "Ch. 15 (Maso)"],
            "destree2014_critique_role": "Sauvé Meyer & Bobzien argue PAP misreads Aristotelian two-sidedness",
        },
    },
]
