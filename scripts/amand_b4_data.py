"""B4 data : repairs / updates / inserts / edges."""
from __future__ import annotations
from typing import Any

from amand_b4_utils import md_base  # type: ignore

# ============================================================================
# REPAIRS : nodes pre-existing with broken metadata=dict
# ============================================================================

REPAIRS: dict[str, dict[str, Any]] = {
    "argument_carneadean_providence_mantike_alexander_amand1945": dict(
        period="Hellenistic",
        school="school_academics",
        md=md_base(
            page_range="p. 146-147, 151",
            md_line_range="ll. 8170-8235",
            chapter="Livre I Ch. V §III.2 (Alexandre De Fato 17)",
            chapter_actual="Livre I Ch. V §III.2 — Troisième argument moral (De Fato 17) : suppression providence, piété, mantique",
            confidence=0.85,
            cited_editions=[
                "Alexandre d'Aphrodise, De Fato 17, éd. I. Bruns, Suppl. Arist. II.2, Berlin Reimer 1892, p. 187 l. 22 — p. 188 l. 22",
            ],
            extra={
                "amand_witness_rank": "primary_witness_n2",
                "amand_witness_role": "witness_2_alexander",
                "is_witness_argument": True,
                "argument_category": "argument_carneadean_moral_reconstruction_via_witness_alexander",
                "transmits_argument_pivots_b1": [
                    "argument_carneadean_providence_amand1945_or_piety",
                    "argument_carneadean_piety_amand1945",
                ],
                "amand_judgement_quote_fr": "Ceux qui professent le déterminisme absolu, entendez Chrysippe et son école, devraient nier la Providence des dieux à l'égard des hommes",
                "alexander_section_locus": "Περὶ εἱμαρμένης 17 (Bruns p. 187-188)",
                "sub_arguments": [
                    {"locus": "Bruns 187,22-188,5", "topic": "nier providence des dieux (mérites pré-fixés)"},
                    {"locus": "Bruns 188,5-12", "topic": "abolir la piété (faux vertus déterminées)"},
                    {"locus": "Bruns 188,12-22", "topic": "détruire la mantique (inutile si rien ne dépend de nous)"},
                ],
            },
        ),
    ),
}


# ============================================================================
# UPDATES : existing nodes enriched with B4 witness metadata
# ============================================================================

UPDATES: dict[str, dict[str, Any]] = {
    "person_alexander_aphrodisias_fl200ce_n5o6p7q8": dict(
        md_additions={
            "amand1945_witness_role": "witness_2_for_carneadean_moral_reconstruction",
            "amand1945_treated_in": "Livre I Ch. V (p. 127-156, ll. 7670-9249)",
            "amand1945_witness_passage": "De Fato 16-20, éd. Bruns p. 186 l. 13 — p. 191 l. 2",
            "amand1945_judgement_fr": (
                "Alexandre n'est pas un génie créateur ; il a recueilli dans son De fato la tradition "
                "d'enseignement péripatéticien et y a inséré une utilisation aussi précise qu'étendue de "
                "l'argumentation antifataliste de la Nouvelle Académie (Carnéade), probablement via "
                "Clitomaque. Les chapitres 16-20 constituent le témoin n°2 le plus rigoureux logiquement et "
                "le plus 'philosophique' parmi les six retenus par Amand."
            ),
            "amand1945_dates": "scholarque péripatéticien à Athènes 198-217 sous Septime Sévère",
            "amand1945_titles": ["second Aristote", "exégète par excellence"],
            "amand1945_doctrinal_traits": [
                "esprit froid et positif",
                "hostile à la mentalité religieuse, superstitieuse et mystique du siècle des Antonins",
                "nominaliste (universel = abstraction de l'individuel)",
                "matérialiste sur le couple corps-âme (âme = forme du corps, périt avec lui)",
                "intellect identique à Dieu",
            ],
        },
        description_append=(
            "[Amand 1945 — témoin n°2] : Selon Amand 1945 (p. 127-156, Livre I Ch. V), Alexandre est "
            "moins un philosophe original qu'un compilateur scrupuleux qui recueille dans son traité "
            "Περὶ εἱμαρμένης (Du Destin) la tradition péripatéticienne d'enseignement sur τὸ ἐφ' ἡμῖν et "
            "y intègre l'arsenal carnéadien anti-Chrysippe. Les chapitres 16-20 (éd. Bruns p. 186-191) "
            "constituent le second des « six textes témoins » d'Amand pour la reconstruction de "
            "l'argumentation morale antifataliste de Carnéade : 5 arguments structurés contre le "
            "fatalisme intégral de Chrysippe (vertu négligée ; louange/blâme/punition vides ; négation "
            "providence-piété-mantique ; auto-réfutation pragmatique des Stoïciens ; châtiment de fait "
            "des criminels). Amand juge ce témoin le plus rigoureux logiquement, le plus 'philosophique' "
            "et le moins ornementé des six (Philon et Firmicus emploient au contraire la diatribe imagée)."
        ),
        description_en_append=(
            "[Amand 1945 — witness no. 2]: According to Amand 1945 (p. 127-156, Book I Ch. V), Alexander "
            "is less an original philosopher than a scrupulous compiler who gathers in his treatise "
            "Περὶ εἱμαρμένης (On Fate) the Peripatetic tradition of teaching on τὸ ἐφ' ἡμῖν and integrates "
            "into it the Carneadean anti-Chrysippus arsenal. Chapters 16-20 (ed. Bruns p. 186-191) "
            "constitute the second of Amand's 'six witness texts' for reconstructing Carneades' moral "
            "anti-fatalist argumentation: 5 structured arguments against Chrysippus' absolute fatalism "
            "(neglected virtue; empty praise/blame/punishment; negation of providence-piety-mantic; "
            "Stoic pragmatic self-refutation; de facto punishment of criminals). Amand judges this "
            "witness the most logically rigorous, the most 'philosophical' and the least ornamented of "
            "the six (Philo and Firmicus by contrast deploy imaged diatribe)."
        ),
    ),
    "work_de_fato_alexander_c200ce_o6p7q8r9": dict(
        md_additions={
            "amand1945_status": "second of six witness texts (témoin n°2)",
            "amand1945_witness_passage": "Περὶ εἱμαρμένης chapters 16-20, ed. Bruns Suppl. Arist. II.2 p. 186 l. 13 — p. 191 l. 2",
            "amand1945_witness_role": "primary_witness_n2_for_carneadean_moral_reconstruction",
            "amand1945_treated_in_amand": "Livre I Ch. V (p. 127-156), texte original ch. 16-20 reproduit p. 149-154",
            "amand1945_original_title": "Περὶ εἱμαρμένης καὶ τοῦ ἐφ' ἡμῖν πρὸς τοὺς αὐτοκράτορας",
            "amand1945_dedicatees": "Septime Sévère et son fils Caracalla",
            "amand1945_cited_edition": "I. Bruns, Alexandri Aphrodisiensis praeter commentaria scripta minora. Quaestiones. De fato. De mixtione. (Supplementum Aristotelicum II.2). Berlin, Reimer, 1892",
            "amand1945_french_translation": "J.-F. Nourrisson, Essai sur Alexandre d'Aphrodisias, suivi du traité du destin et du libre pouvoir aux empereurs, Paris 1870",
            "amand1945_judgement_register": "traité clair et bien composé ; oeuvre de circonstance ; somme péripatéticienne antifataliste",
        },
        description_append=(
            "[Amand 1945 — témoin n°2] : Selon Amand 1945 (Livre I Ch. V, p. 138-156), le Περὶ εἱμαρμένης "
            "καὶ τοῦ ἐφ' ἡμῖν πρὸς τοὺς αὐτοκράτορας d'Alexandre est dédié à Septime Sévère et Caracalla. "
            "Composition triple selon Amand : (a) tradition d'enseignement péripatéticien sur τὸ ἐφ' ἡμῖν / "
            "εἱμαρμένη qu'Alexandre recueille comme « continuateur et interprète » ; (b) arsenal carnéadien "
            "néo-académicien anti-Chrysippe, vraisemblablement via une source littéraire telle que "
            "Clitomaque ; (c) lecture directe et critique des ouvrages mêmes de Chrysippe, avec arguments "
            "ad hominem nourris. Les chapitres 16-20 (Bruns p. 186 l. 13 — p. 191 l. 2) constituent le "
            "témoin n°2 pour la reconstruction Amand. Édition critique de référence chez Amand : I. Bruns, "
            "Supplementum Aristotelicum II.2, Berlin Reimer 1892. Traduction française disponible : J.-F. "
            "Nourrisson, Essai sur Alexandre d'Aphrodisias, Paris 1870."
        ),
        description_en_append=(
            "[Amand 1945 — witness no. 2]: According to Amand 1945 (Book I Ch. V, p. 138-156), Alexander's "
            "Περὶ εἱμαρμένης καὶ τοῦ ἐφ' ἡμῖν πρὸς τοὺς αὐτοκράτορας is dedicated to Septimius Severus and "
            "Caracalla. Triple composition per Amand: (a) Peripatetic teaching tradition on τὸ ἐφ' ἡμῖν / "
            "εἱμαρμένη which Alexander gathers as 'continuator and interpreter'; (b) Neo-Academic "
            "Carneadean anti-Chrysippus arsenal, plausibly via a literary source such as Clitomachus; "
            "(c) direct critical reading of Chrysippus' own works, with ad hominem arguments. Chapters "
            "16-20 (Bruns p. 186 l. 13 — p. 191 l. 2) constitute witness no. 2 for the Amand reconstruction. "
            "Critical edition cited by Amand: I. Bruns, Supplementum Aristotelicum II.2, Berlin Reimer "
            "1892. French translation available: J.-F. Nourrisson, Essai sur Alexandre d'Aphrodisias, "
            "Paris 1870."
        ),
    ),
    "argument_alexander_of_aphrodisias_freedom_argument_8058a30c": dict(
        md_additions={
            "amand1945_b4_enrichment": True,
            "amand1945_witness_role": "general_freedom_defence_alexander",
            "amand1945_treated_in": "Livre I Ch. V §II.3.3 (p. 142-143)",
            "amand1945_doctrinal_summary_fr": (
                "Alexandre reconnaît pleinement notre libre arbitre, le défend vigoureusement, certifie "
                "qu'il est des œuvres réellement en notre pouvoir, revendique la faculté d'agir en toute "
                "indépendance comme principe autonome de mouvement. L'εἱμαρμένη n'est ni le principe "
                "efficient ni aucune cause extérieure prédéterminante. L'homme, et lui seul, est principe "
                "et cause des actes qu'il pose."
            ),
            "amand1945_alexander_method_fr": (
                "Défense à la manière de Kant : insiste sur les conséquences pratiques détestables du "
                "fatalisme plutôt que sur une étude approfondie originale de la volonté humaine. Appel au "
                "consensus universel et aux idées innées du langage (« preuve suffisante et inébranlable "
                "de la liberté »), ainsi qu'à la conscience immédiate de notre libre arbitre."
            ),
            "amand1945_cited_passages": "De Fato 5 (Bruns 169,14-22) ; 12 (Bruns 180,3-181,7) ; 15 (Bruns 185,7-186,12)",
        },
        description_append=(
            "[Amand 1945] : Selon Amand 1945 (Livre I Ch. V §II.3.3, p. 142-143), la défense alexandrienne "
            "du libre arbitre repose sur trois mouvements. (1) Reconnaissance pleine et entière de la "
            "liberté de la volonté humaine comme principe autonome de mouvement : l'homme, et lui seul, "
            "est principe et cause des actes qu'il pose (De Fato 5 et 15, Bruns p. 169 et p. 185). "
            "(2) Argumentation par les conséquences pratiques inacceptables du fatalisme, à la manière "
            "« kantienne » avant la lettre selon Amand, plutôt qu'analyse positive de la volonté. (3) "
            "Appel au consensus universel des hommes et aux idées innées exprimées dans le langage "
            "(« preuve suffisante et inébranlable »), ainsi qu'à la conscience immédiate de notre libre "
            "arbitre, comme l'a fait la philosophie populaire depuis Cicéron."
        ),
        description_en_append=(
            "[Amand 1945]: According to Amand 1945 (Book I Ch. V §II.3.3, p. 142-143), Alexander's defence "
            "of free will rests on three moves. (1) Full recognition of the freedom of human will as an "
            "autonomous principle of motion: man, and man alone, is the principle and cause of his acts "
            "(De Fato 5 and 15, Bruns p. 169 and p. 185). (2) Argument from unacceptable practical "
            "consequences of fatalism, in a 'Kantian' manner avant la lettre per Amand, rather than a "
            "positive analysis of the will. (3) Appeal to universal consensus of mankind and to innate "
            "ideas expressed in language ('sufficient and unshakeable proof'), and to the immediate "
            "consciousness of our free will, as popular philosophy has done since Cicero."
        ),
    ),
    "person_firmicus_maternus_2q7r9t65": dict(
        md_additions={
            "amand1945_witness_role": "witness_3_for_carneadean_moral_reconstruction",
            "amand1945_treated_in": "Livre I Ch. VII (p. 177-188, ll. 10135-10791)",
            "amand1945_witness_passage": "Mathesis I, 2, 5-11, éd. Kroll-Skutsch I p. 7 l. 8 — p. 9 l. 4",
            "amand1945_paradox_fr": (
                "Personnage paradoxal : d'abord païen convaincu et 'prêtre' de la religion astrologique "
                "compilant la Mathesis ; converti ensuite au christianisme, devient néophyte excessivement "
                "zélé et rédige peu après le pamphlet De errore profanarum religionum exhortant les "
                "empereurs à exterminer le paganisme. Haut fonctionnaire de l'Empire, sénateur romain."
            ),
            "amand1945_judgement_fr": (
                "Auteur latin mais zélé compilateur d'ouvrages grecs ; styliste médiocre, partisan "
                "enthousiaste du fatalisme absolu astrologique. Témoin n°3 d'Amand par hasard "
                "documentaire : ayant copié in extenso pour les réfuter trois arguments antiastrologiques "
                "néo-académiciens, il transmet sans le savoir l'argumentation morale carnéadienne sous "
                "une forme populaire et imagée (diatribe)."
            ),
            "amand1945_dates": "fl. milieu IVe siècle (Mathesis sous Constantin, vers 334-337 ; De errore vers 343-350)",
            "amand1945_works": [
                "Mathesis (8 livres, somme astrologique latine, éd. Kroll-Skutsch Teubner 1897-1913)",
                "De errore profanarum religionum (pamphlet anti-paganisme, éd. K. Ziegler, trad. G. Heuten Bruxelles 1938)",
            ],
        },
        description_append=(
            "[Amand 1945 — témoin n°3] : Selon Amand 1945 (Livre I Ch. VII, p. 177-188), Firmicus est une "
            "« étrange physionomie » : d'abord païen convaincu et 'prêtre' de la religion astrologique "
            "qui compile avec ferveur la Mathesis (vers 334-337, sous Constantin), il se convertit ensuite "
            "au christianisme et rédige peu après le furieux pamphlet De errore profanarum religionum "
            "exhortant les empereurs à exterminer le paganisme. Bien que partisan enthousiaste du "
            "fatalisme absolu astrologique, Firmicus transmet par hasard documentaire le témoin n°3 de "
            "la reconstruction Amand : la Mathesis I, 2, 5-11 (éd. Kroll-Skutsch I p. 7 l. 8 — p. 9 l. 4) "
            "rapporte in extenso, pour les réfuter, trois arguments antiastrologiques d'origine "
            "néo-académicienne dont l'argumentation morale antifataliste de Carnéade — présentée sous une "
            "forme populaire, vivante et imagée caractéristique de la diatribe, à la différence de "
            "l'exposé scolastique et sec d'Alexandre d'Aphrodise. Le portrait des adversaires (Math I,1,1-2 "
            "et I,3,4) est, selon Boll et Amand, celui de Carnéade en personne à peine défiguré."
        ),
        description_en_append=(
            "[Amand 1945 — witness no. 3]: According to Amand 1945 (Book I Ch. VII, p. 177-188), Firmicus "
            "is a 'strange physiognomy': first a convinced pagan and 'priest' of the astrological "
            "religion who fervently compiles the Mathesis (c. 334-337, under Constantine), he then "
            "converts to Christianity and soon writes the furious pamphlet De errore profanarum religionum "
            "exhorting emperors to exterminate paganism. Although an enthusiastic adherent of absolute "
            "astrological fatalism, Firmicus transmits by documentary accident Amand's witness no. 3: "
            "Mathesis I, 2, 5-11 (ed. Kroll-Skutsch I p. 7 l. 8 — p. 9 l. 4) reports in extenso, in order "
            "to refute them, three anti-astrological arguments of Neo-Academic origin including "
            "Carneades' moral anti-fatalist argumentation — presented in a popular, lively and imaged "
            "form characteristic of diatribe, contrasting with Alexander of Aphrodisias' dry scholastic "
            "exposition. The portrait of the adversaries (Math I,1,1-2 and I,3,4) is, per Boll and Amand, "
            "Carneades himself barely disguised."
        ),
    ),
}


# NEW_INSERTS / NEW_EDGES are defined in their own modules (amand_b4_inserts, amand_b4_edges).
