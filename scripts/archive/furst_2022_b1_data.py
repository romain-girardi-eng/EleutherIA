"""Fürst 2022 B1 — UPDATES list (metadata enrichments for existing nodes).

Light enrichments only — descriptions left intact. Targets ancient persons,
works and concepts treated extensively by Fürst (Homer / Plato / Aristotle /
Chrysippus / Carneades / Epictetus / Cicero / Alcinous / Apuleius / Alexander
of Aphrodisias / Philo / Justin / Clement of Alexandria / Origen + key Origen
works), plus the two existing Fürst nodes (scholar + publication) and the
modern scholars he engages with (Dihle, Frede, Bobzien, Kobusch, Hengstermann,
Crouzel, Karamanolis, Sharples, Frede Michael, List, Kahn, Kane).
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # =========================================================================
    # SCHOLAR + PUBLICATION (already in KG, enrich metadata)
    # =========================================================================
    {
        "id": "scholar_furst_alfons",
        "metadata_updates": {
            "furst_2022_role_in_kg": (
                "auteur principal du monographe-pivot Wege zur Freiheit "
                "(Mohr Siebeck 2022) qui retrace la genèse de "
                "l'autodétermination humaine d'Homère à Origène, "
                "argumentant qu'Origène (et non Augustin) marque le tournant "
                "décisif où la liberté devient principe métaphysique"
            ),
            "furst_2022_central_thesis": (
                "Origène est le premier penseur de la liberté de l'histoire ; "
                "il a élevé la liberté au rang de principe ontologique "
                "(Freiheitsmetaphysik) avant Plotin, dans un cadre que Fürst "
                "qualifie de 'libertarisme compatibiliste' "
                "(kompatibilistischer Libertarismus)"
            ),
            "furst_engagement_with_dihle": (
                "Fürst engage la thèse augusto-centrique de Dihle "
                "(Vorstellung vom Willen, 1985) et la nuance : Origène "
                "représente déjà un tournant décisif avant Augustin"
            ),
            "furst_engagement_with_frede": (
                "Fürst dialogue avec Michael Frede (A Free Will, 2011) ; "
                "souscrit à Frede sur l'absence de concept de volonté chez "
                "Platon et Aristote, mais déplace l'origine du Freiheitsdenken "
                "vers Origène plutôt que vers Épictète"
            ),
            "furst_engagement_with_bobzien": (
                "Fürst reprend les analyses de Susanne Bobzien (Determinism "
                "and Freedom in Stoic Philosophy, 1998) sur le compatibilisme "
                "stoïcien tout en montrant ses limites face au libertarisme "
                "origénien"
            ),
            "furst_intellectual_lineage_engaged": [
                "Hengstermann 2016 (Origenes und der Ursprung der Freiheitsmetaphysik) — étude fondatrice citée comme pivot",
                "Kobusch 1985 / 2018 (Selbstbestimmte Freiheit) — opposition phusis/prohairesis",
                "Karamanolis (Philosophy of Early Christianity)",
                "Crouzel Henri — origénisme français",
                "Sharples Robert — Alexandre d'Aphrodise / De Fato",
                "Perkams Matthias — Historical Origins of Our Concept of Freedom (cité 5,103-5,107)",
                "List Christian (Why Free Will is Real) — compatibilist libertarianism (Fürst note p. 10143-10145)",
            ],
            "furst_2022_publication_id": "pub_furst_2022_wege_freiheit",
            "furst_specialization_extended": [
                "Origène (philosophie de la liberté)",
                "patrologie grecque",
                "platonisme chrétien",
                "histoire du concept de Selbstbestimmung",
            ],
        },
    },
    {
        "id": "pub_furst_2022_wege_freiheit",
        "metadata_updates": {
            "key_claim": (
                "Origène d'Alexandrie (3e s. ap. J.-C.) est le premier penseur "
                "à élever la liberté au rang de principe métaphysique central "
                "de l'anthropologie et de la métaphysique, dans un cadre que "
                "Fürst qualifie de « libertarisme compatibiliste » "
                "(kompatibilistischer Libertarismus). Ce tournant décisif se "
                "produit philosophiquement à partir de fondations stoïciennes "
                "mais sur sol platonicien, par les platoniciens chrétiens "
                "primitifs"
            ),
            "structure": {
                "ch_I": "Menschliche Selbstbestimmung im Alten Hellas und im Alten Israel (Homer, mythologie grecque, Bible hébraïque)",
                "ch_II": "Determinismus und Verantwortung — Die griechische Philosophie (Platon Mythe d'Er, Aristote, Chrysippe, Épicure/Lucrèce, Carnéade)",
                "ch_III": "Ethik der Freiheit — Die Freiheitsdebatte in der römischen Kaiserzeit (Épictète, Cicéron, médio-platonisme, Alexandre d'Aphrodise)",
                "ch_IV": "Freiheitspathos — Die frühchristliche Freiheitstheorie (Philon, Paul/NT, Justin, Clément)",
                "ch_V": "Die Freiheit der Selbstbestimmung — Das Freiheitsdenken des Origenes (concept de liberté, exégèse libertarienne)",
                "ch_VI": "Die Welt als freie Bewegung Gottes — Die Freiheitsmetaphysik des Origenes (monde en mouvement, dignité de l'homme, théologie de la liberté, libertarisme compatibiliste)",
                "Ausklang": "Origène a déplacé la métaphysique d'une doctrine statique de l'être vers une dynamique de la liberté",
            },
            "epigraphs_two_pillars": [
                "Platon, Rép. X 617e 4 f. : αἰτία ἑλομένου, θεὸς ἀναίτιος (la responsabilité incombe à celui qui choisit ; Dieu est sans cause)",
                "Origène, Hom. Jér. 18,3 : τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι (l'autodétermination, en effet, est liberté)",
            ],
            "page_count": 351,
            "word_count": 95582,
            "language": "de",
            "series_long": "Tria Corda — Jenaer Vorlesungen zu Judentum, Antike und Christentum",
            "series_editors": "Karl-Wilhelm Niebuhr, Matthias Perkams, Meinolf Vielberg",
            "lecture_series_origin": "Tria-Corda-Vorlesungen, Friedrich-Schiller-Universität Jena, November 2021",
            "key_innovation_claim": (
                "Origenes ist nicht nur Vorläufer Augustins, sondern der erste "
                "Freiheitsdenker schlechthin: er hat zeitlich noch vor Plotin "
                "die Freiheit als Prinzip des gesamten Seins aufgefasst und "
                "auf dieser Basis eine Freiheitsmetaphysik entworfen"
            ),
            "methodology": (
                "Étroitement travaillé sur les sources primaires ; sélection "
                "limitée mais ciblée de littérature secondaire ; développement "
                "d'un argument philosophico-historique en six étapes sur un "
                "millénaire de pensée"
            ),
        },
    },
    # =========================================================================
    # CHAPITRE I — Homère + Bible hébraïque (Homer / Hesiod non-présents en KG)
    # → uniquement enrichissement de concepts existants si possible
    # =========================================================================
    # =========================================================================
    # CHAPITRE II — Philosophie grecque (Platon, Aristote, Chrysippe, Épicure,
    # Carnéade)
    # =========================================================================
    {
        "id": "person_plato_428_348bce_a1b2c3d4",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. II 2 (p. 52-62) — Mythe d'Er de la République (Politeia X 617e 4-5)",
            "furst_2022_chapter": "II.2 Von der Schicksalsbestimmtheit zur Selbstbestimmung — Der Er-Mythos in Platons Politeia",
            "furst_2022_pages": "p. 52-62",
            "furst_2022_key_thesis": (
                "Fürst 2022 : le mythe d'Er marque le passage de la "
                "Schicksalsbestimmtheit à la Selbstbestimmung. La formule "
                "αἰτία ἑλομένου, θεὸς ἀναίτιος (Rép. X 617e) devient un "
                "axiome platonicien repris par les médio-platoniciens, par "
                "Justin et par Origène. Platon n'a cependant pas encore "
                "thématisé la liberté comme concept indépendant"
            ),
            "furst_2022_role": "fondateur de l'ontologie qui sépare l'esprit du matériel — condition de possibilité de la métaphysique de la liberté",
            "furst_2022_used_as_epigraph": True,
        },
    },
    {
        "id": "person_aristotle_384_322bce_c2d4f6a8",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. II 3 (p. 62-73) — Die überlegte Wahl eines vernünftigen Selbst",
            "furst_2022_chapter": "II.3 Die überlegte Wahl eines vernünftigen Selbst — Aristoteles",
            "furst_2022_pages": "p. 62-73",
            "furst_2022_key_thesis": (
                "Fürst 2022 (avec Dihle, Frede, Kahn, Pich) : Aristote n'a "
                "pas de concept de volonté distinct de l'intellect. Sa "
                "προαίρεσις est une « délibération » (Überlegung), un acte "
                "et un produit de la pensée — non un « choix libre » ni une "
                "« volonté ». L'intellectualisme socrato-platonicien domine. "
                "Aristote introduit néanmoins le terme technique τὸ ἐφ᾽ ἡμῖν "
                "qui devient le pivot terminologique de toute la débat "
                "ultérieur"
            ),
            "furst_2022_role": "introducteur de προαίρεσις et de τὸ ἐφ᾽ ἡμῖν dans le discours philosophique",
        },
    },
    {
        "id": "person_chrysippus_280_206bce_i9j0k1l2",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. II 4 (p. 73-91) — Kausaldeterminismus und Eigenverantwortung : Der Kompatibilismus Chrysipps",
            "furst_2022_chapter": "II.4 Kausaldeterminismus und Eigenverantwortung — Der Kompatibilismus des Stoikers Chrysipp",
            "furst_2022_pages": "p. 73-91",
            "furst_2022_key_thesis": (
                "Fürst 2022 (suivant Bobzien 1998) : Chrysippe a développé le "
                "premier compatibilisme rigoureux — l'assentiment (συγκατάθεσις) "
                "est notre fait (ἐφ᾽ ἡμῖν) bien que pleinement inscrit dans la "
                "chaîne causale du destin (εἱμαρμένη). La distinction des "
                "causes (causae perfectae vs adiuvantes) permet de sauver la "
                "responsabilité morale dans un déterminisme causal sans "
                "lacune. Origène reprendra cette analyse en y intégrant des "
                "alternatives possibles, ce que Chrysippe excluait"
            ),
            "furst_2022_role": "modèle théorique de référence — repris et corrigé par Carnéade, les médio-platoniciens, Alexandre, Origène",
        },
    },
    {
        "id": "person_epicurus_341_270bce_j0k1l2m3",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. II 5 (p. 91-96) — Spontane Selbstbewegung : Epikur und Lukrez",
            "furst_2022_chapter": "II.5 Spontane Selbstbewegung — Epikur und Lukrez",
            "furst_2022_pages": "p. 91-96",
            "furst_2022_key_thesis": (
                "Fürst 2022 : la déviation spontanée des atomes (parenklisis / "
                "clinamen) est une « solution un peu violente » (Krämer) au "
                "déterminisme physique épicurien. Lucrèce parle de "
                "« libera voluntas » dans un cadre atomistique où il s'agit "
                "moins de volonté libre que de désir naturel se déployant "
                "sans entrave. L'idée de spontanéité est une innovation qu'il "
                "aurait fallu prolonger"
            ),
        },
    },
    {
        "id": "person_carneades_214_129bce_l2m3n4o5",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. II 6 (p. 96-100) — Willentliche Selbstbewegung : Karneades",
            "furst_2022_chapter": "II.6 Willentliche Selbstbewegung — Karneades",
            "furst_2022_pages": "p. 96-100",
            "furst_2022_key_thesis": (
                "Fürst 2022 (suivant Cicéron De Fato 23-25, Schallenberg, "
                "Frede) : Carnéade introduit pour la première fois la "
                "distinction d'un règne du matériel (où règnent nécessité et "
                "hasard) et d'un règne du spirituel (où peut être posée la "
                "question d'une autodétermination libre). La voluntas a sa "
                "cause « en elle-même » (in nostra potestate) et non dans une "
                "cause externe antérieure. Première anticipation de "
                "l'ontologie dualiste qui permettra le libertarisme : "
                "« ce n'est pas chez les stoïciens ni chez les épicuriens "
                "mais chez les platoniciens que le chemin de la liberté hors "
                "des contraintes physiques a été tracé »"
            ),
            "furst_2022_role": "première formulation philosophique d'une auto-motion non causée par antécédents extérieurs",
            "furst_2022_dialog_with_schallenberg": "Schallenberg, Freiheit und Determinismus 302, parle de « libertarischer Kompatibilismus » à propos de Carnéade et Cicéron — Fürst note ce parallèle terminologique",
        },
    },
    # =========================================================================
    # CHAPITRE III — Époque impériale (Épictète, Cicéron, médio-platoniciens,
    # Alexandre)
    # =========================================================================
    {
        "id": "person_epictetus_of_hierapolis_3c385bc2",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. III 2 (p. 108-119) — Freiheit als Einwilligung in das Schicksal : Epiktet",
            "furst_2022_chapter": "III.2 Freiheit als Einwilligung in das Schicksal — Epiktet",
            "furst_2022_pages": "p. 108-119",
            "furst_2022_key_thesis": (
                "Fürst 2022 (en dialogue avec Frede 2011) : Épictète développe "
                "le concept de προαίρεσις comme centre éthique de la personne "
                "et utilise προαίρεσις ἐλεύθερα — mais en passant, sans en "
                "faire une innovation systématique. La liberté épictétienne "
                "est l'« acquiescement au destin » (Einwilligung in das "
                "Schicksal) ; Frede situe à tort l'origine du concept de "
                "volonté chez Épictète selon Fürst — Justin et les chrétiens "
                "marqueront le vrai tournant"
            ),
        },
    },
    {
        "id": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. III 3a (p. 121-126) — Postulat der Willensfreiheit : Cicero",
            "furst_2022_chapter": "III.3a Postulat der Willensfreiheit — Cicero",
            "furst_2022_pages": "p. 121-126",
            "furst_2022_key_thesis": (
                "Fürst 2022 : Cicéron (De Fato) transmet la critique académicienne "
                "de Carnéade contre le compatibilisme chrysippien et postule "
                "la liberté de la volonté (voluntas) comme requise pour la "
                "responsabilité morale. Il déplace le débat du grec "
                "(προαίρεσις = acte intellectuel) vers le latin (voluntas = "
                "appétit volontaire) — pas terminologique-conceptuel décisif "
                "qui prépare le voluntarisme augustinien"
            ),
        },
    },
    {
        "id": "person_alcinous_2c_ce",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. III 3b (p. 126-132) — Undeterminierte Entscheidung : Die platonische Schultradition",
            "furst_2022_chapter": "III.3b Undeterminierte Entscheidung — Die platonische Schultradition (Plutarque, ps.-Plutarque, Alcinoos, Apulée, Maxime de Tyr)",
            "furst_2022_pages": "p. 126-132",
            "furst_2022_key_thesis": (
                "Fürst 2022 : Alcinoos (Didask. 26) et la tradition "
                "médio-platonicienne formulent le principe d'un destin "
                "hypothétique (« si x, alors y ») et soutiennent que l'âme "
                "est « sans maître » (αδέσποτος) — concept emprunté au mythe "
                "d'Er. La liberté de décision est postulée comme indéterminée. "
                "Sans approfondissement philosophique de la cause de la "
                "décision : « on les sent insister plutôt qu'on ne le lit »"
            ),
            "furst_2022_role": "transmetteur clé du libertarisme platonicien vers Origène (via la formulation hypothétique du destin)",
        },
    },
    {
        "id": "person_calcidius_4c_ce",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. III 3b contexte (médio-platonisme tardif latin)",
            "furst_2022_chapter": "III.3b Tradition platonicienne (latine via Calcidius)",
            "furst_2022_pages": "p. 126-132 contexte",
            "furst_2022_key_thesis": (
                "Fürst 2022 (en contexte) : Calcidius transmet en latin la "
                "doctrine médio-platonicienne du destin hypothétique et de la "
                "liberté indéterminée, faisant le pont avec Augustin et le "
                "Moyen Âge"
            ),
        },
    },
    {
        "id": "person_plutarch_45_120ce_b9c2a8f3",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. III 3b (p. 126-132) — De Stoicorum repugnantiis 47",
            "furst_2022_chapter": "III.3b critique de Plutarque contre la différenciation chrysippienne des causes",
            "furst_2022_pages": "p. 127-128, 131",
            "furst_2022_key_thesis": (
                "Fürst 2022 : Plutarque (Stoic. repugn. 47, 1056 a-d) critique "
                "Chrysippe — pour lui la différenciation des causes ne résout "
                "pas la contradiction entre déterminisme causal sans lacune et "
                "autodétermination. Comme Cicéron, il argumente depuis la "
                "présupposition qu'il y a « quelque chose qui dépend de nous "
                "et de notre vouloir »"
            ),
        },
    },
    {
        "id": "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. III 3c (p. 132-138) — Wahlfreiheit : Alexander von Aphrodisias",
            "furst_2022_chapter": "III.3c Wahlfreiheit — Alexander von Aphrodisias",
            "furst_2022_pages": "p. 132-138",
            "furst_2022_key_thesis": (
                "Fürst 2022 : Alexandre d'Aphrodise (De Fato, vers 198-209) "
                "est le grand critique péripatéticien du compatibilisme "
                "stoïcien. Il introduit le critère décisif des possibilités "
                "alternatives (Alternativenoffenheit) : pour qu'une "
                "décision soit véritablement nôtre, il faut qu'il existe une "
                "alternative réellement ouverte. Argument standard repris : "
                "le déterminisme abolit blâme/louange/châtiment/récompense, "
                "rendant la vie humaine impossible. Origène intégrera cette "
                "exigence dans sa théorie"
            ),
        },
    },
    # =========================================================================
    # CHAPITRE IV — Pathos chrétien primitif (Philon, Justin, Clément)
    # =========================================================================
    {
        "id": "person_philo_alexandria_a1b2c3d4",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. IV 1 (p. 141-149) — Hintergründe im Frühjudentum : Philon von Alexandria",
            "furst_2022_chapter": "IV.1 Hintergründe im Frühjudentum — Philon von Alexandria",
            "furst_2022_pages": "p. 141-149",
            "furst_2022_key_thesis": (
                "Fürst 2022 : Philon est le maillon décisif entre la philosophie "
                "hellénistique et la pensée chrétienne primitive de la liberté. "
                "Trois innovations clés : (1) première occurrence attestée de la "
                "syntagme ἐλεύθερα προαίρεσις (De Deo immut. 47-49) ; (2) "
                "premier à attribuer la capacité d'autodétermination libre à "
                "chaque homme (pas seulement à l'élite sage stoïcienne) ; (3) "
                "fondation théologique de la liberté humaine sur Dieu « Père "
                "de la liberté » (πατὴρ ἐλευθερίας). Origène le reprendra "
                "presque directement"
            ),
            "furst_2022_role": "précurseur direct du concept chrétien de liberté ; Origène « particulièrement inspiré par lui »",
        },
    },
    {
        "id": "person_justin_martyr_2c_ce",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. IV 3 (p. 152-161) — Freiheit der Entscheidung : Justin der Märtyrer",
            "furst_2022_chapter": "IV.3 Freiheit der Entscheidung — Justin der Märtyrer",
            "furst_2022_pages": "p. 152-161",
            "furst_2022_key_thesis": (
                "Fürst 2022 : Justin (1 Apol. 43-44 et 2 Apol. 6-7) "
                "proclame pour la première fois explicitement la liberté de "
                "la décision (ἐλεύθερα προαίρεσις) — innovation majeure dont "
                "« l'importance ne peut être assez soulignée ». Justin "
                "platonicien chrétien suit les médio-platoniciens dans leur "
                "critique du déterminisme stoïcien, mais ajoute trois "
                "accents nouveaux : (1) répétition emphatique de "
                "« ἐλεύθερα » ; (2) preuve par la changement moral du même "
                "individu dans le temps (au lieu d'alternatives "
                "synchroniques) ; (3) première amorce vers l'idée que la "
                "libre décision détermine non seulement comment l'homme est "
                "(caractère) mais qui il est (ontologie de la liberté) — "
                "amorce qu'Origène développera"
            ),
            "furst_2022_role": "pionnier du concept chrétien de liberté de la décision ; pont entre médio-platonisme et Origène",
        },
    },
    {
        "id": "person_clement_alexandria",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. IV 5 (p. 180-186) — Natur und Freiheit : Clemens von Alexandria",
            "furst_2022_chapter": "IV.5 Natur und Freiheit — Clemens von Alexandria",
            "furst_2022_pages": "p. 180-186",
            "furst_2022_key_thesis": (
                "Fürst 2022 (suivant Kobusch) : Clément d'Alexandrie pose "
                "l'opposition φύσις / προαίρεσις qui ouvre la voie à Origène. "
                "Le perfectionnement éthique de l'homme « devient sa "
                "nature » (sa disposition intérieure devient nature). Cette "
                "opposition entre nature et liberté — qui deviendra chez "
                "Augustin l'opposition natura / voluntas — est le terrain "
                "préparé sur lequel Origène construira systématiquement sa "
                "métaphysique de la liberté"
            ),
            "furst_2022_role": "pivot doctrinal entre la théorie chrétienne primitive de la liberté et la métaphysique origénienne",
        },
    },
    # =========================================================================
    # CHAPITRES V + VI — ORIGÈNE (cœur du livre)
    # =========================================================================
    {
        "id": "person_origen_alexandria_185_254ce_s9t0u1v2",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. V + VI (p. 187-290) — le cœur de l'ouvrage",
            "furst_2022_chapter": "V Die Freiheit der Selbstbestimmung — Das Freiheitsdenken des Origenes ; VI Die Welt als freie Bewegung Gottes — Die Freiheitsmetaphysik des Origenes",
            "furst_2022_pages": "p. 187-290 (104 pages, 6e du livre)",
            "furst_2022_central_thesis": (
                "Fürst 2022 : Origène est le premier penseur de la liberté de "
                "l'histoire — temporellement avant Plotin, le premier à avoir "
                "saisi la liberté comme principe de l'être tout entier "
                "(Freiheitsmetaphysik) et à avoir pensé Dieu, l'homme et le "
                "monde à partir du principe de liberté. C'est l'innovation "
                "fondamentale d'Origène. « Origène a élevé le débat sur la "
                "liberté à un nouveau niveau et l'a placé dans un nouveau "
                "réseau de coordonnées dans lequel la liberté est discutée "
                "depuis lors »"
            ),
            "furst_2022_origenian_synthesis": (
                "Synthèse philosophique d'une ampleur sans précédent : (1) "
                "théorie de l'action stoïcienne (Chrysippe, Épictète) ; (2) "
                "ontologie platonicienne (Phédon, Phèdre 245e, Politeia X) ; "
                "(3) prohairesis et eph hemin aristotéliciens ; (4) "
                "exigence d'alternatives ouvertes (Alexandre, médio-platoniciens) ; "
                "(5) liberté de Dieu et de l'homme (Philon) ; (6) preuves "
                "scripturaires (Dt 30, 15-19 ; Rom 9) ; (7) écho carnéadien "
                "via Cicéron"
            ),
            "furst_2022_freiheits_innovation": (
                "Quatre innovations origéniennes : (1) traité Περὶ "
                "αὐτεξουσίου (De Princ. III 1) = premier traité Sur la "
                "liberté qui en mérite le nom (toutes les œuvres précédentes "
                "étaient Sur le destin) ; (2) la libre décision est érigée "
                "en quatrième article de foi (Comm. Jn XXXII 16) ; (3) la "
                "liberté n'est pas un accident mais le principe même de "
                "la substance des êtres rationnels — l'homme est liberté "
                "(« Der Mensch verfügt nicht nur über Freiheit; er ist "
                "Freiheit ») ; (4) Dieu lui-même est pensé comme liberté"
            ),
            "furst_2022_kompatibilistischer_libertarismus": (
                "Fürst caractérise la position d'Origène comme "
                "« libertarisme compatibiliste » (kompatibilistischer "
                "Libertarismus) : libertarisme radical (la liberté comme "
                "principe ontologique premier) compatible avec des aspects "
                "déterminés de la réalité (chaîne des causes physiques, "
                "préscience divine, providence). Origène prouve qu'on peut "
                "« même au plus fort soulignement du libertarisme » ne pas "
                "pouvoir éviter de reconnaître des aspects déterminés"
            ),
            "furst_2022_critique_dihle_augustine_centric_view": (
                "Fürst critique la perspective augusto-centrique dominante "
                "(Dihle, Warnach, Rosenberger) qui marginalise Origène. "
                "« Augustin apparaît toujours en bonne place, Origène "
                "seulement de manière marginale ou pas du tout, et quand il "
                "apparaît, sans reconnaître la véritable signification de sa "
                "pensée »"
            ),
            "furst_2022_pre_plotinian_priority": (
                "Origène est temporellement antérieur à Plotin et donc le "
                "« premier penseur de la liberté de l'histoire » — Plotin et "
                "le néoplatonisme suivront en parallèle"
            ),
            "furst_2022_works_central": [
                "De Principiis I praef. 5 + III 1,1-24 (Freiheitstraktat)",
                "De Oratione 6,1-5 (théorie de la liberté)",
                "Commentaire sur Jean XXXII 16,187-189 (4e article de foi)",
                "Contra Celsum IV 3 + V 21 + VIII 76 (défense de la liberté)",
                "Homélies sur Jérémie 18,3 (τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι — épigraphe)",
                "Commentaire sur le Cantique des Cantiques (don de liberté)",
                "Commentaire sur les Romains V 10 + VIII 10 (liberté permanente)",
                "Commentaire sur Matthieu X 11 + XVII 21 + 27 (liberté et nature)",
                "Fragment Comm. Genèse via Philocalie 23 (anti-astrologie)",
                "Homélies sur Ézéchiel 3,8 (homo homo, tier-mensch)",
            ],
        },
    },
    {
        "id": "work_de_principiis_origen_230s_v2w3x4y5",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. V 1-3 + VI 1-4 — œuvre majeure traitée tout au long de Wege zur Freiheit",
            "furst_2022_chapter": "V.1 zentraler Stellenwert ; V.2 Freiheitsbegriff ; V.3 libertarische Deutung biblischer Determinismus ; VI.1 Welt in Bewegung ; VI.2 Würde des Menschen ; VI.3 Theologie der Freiheit ; VI.4 Kompatibilistischer Libertarismus",
            "furst_2022_pages": "p. 187-290 (passim) ; spec. III 1,1-24 = le Freiheitstraktat",
            "furst_2022_key_thesis": (
                "Fürst 2022 : De Principiis I praef. 5 + III 1,1-24 contient "
                "le premier traité Sur la liberté digne de ce nom dans "
                "l'histoire (Origène n'écrit pas Sur le destin comme ses "
                "prédécesseurs mais Περὶ αὐτεξουσίου / De arbitrii libertate). "
                "Origène y proclame la liberté comme article fondamental de "
                "la prédication ecclésiastique et la fonde philosophiquement "
                "sur la théorie stoïcienne de l'action (incluant la "
                "συγκατάθεσις) tout en exigeant la possibilité d'alternatives. "
                "Le passage clé III 1,2-3 expose la doctrine du mouvement à "
                "quatre niveaux (ἔξωθεν / ἐξ αὑτοῦ / ἀφ᾽ αὑτοῦ / δι᾽ αὑτοῦ) "
                "et fonde la métaphysique de la liberté"
            ),
            "furst_2022_principal_edition_used": "GCS Orig. 5 (Koetschau) ; traduction allemande Görgemanns/Karpp ; SC 252-253/268-269/312 ; édition de référence pour Fürst",
            "furst_2022_central_passage": "III 1,1-24 (le Freiheitstraktat / Περὶ αὐτεξουσίου) = section autonome préservée en grec dans Philocalie 21-27",
        },
    },
    {
        "id": "work_origen_de_oratione",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. V 1 + VI 1 — œuvre clé de la théorie de la liberté",
            "furst_2022_chapter": "V.1 et VI.1 (passim) — De Oratione 6,1-5 sur la théorie du mouvement et la liberté",
            "furst_2022_pages": "p. 196, 248-251 et passim",
            "furst_2022_key_thesis": (
                "Fürst 2022 : De Oratione 6,1-5 (composé à Césarée entre "
                "233-235) reprend et enrichit la théorie de la liberté du "
                "Freiheitstraktat de De Principiis. Le passage sur les quatre "
                "modes de mouvement (ἔξωθεν / ἐξ αὑτοῦ / ἀφ᾽ αὑτοῦ / δι᾽ "
                "αὑτοῦ) est philologiquement comparé à Perrone (Preghiera "
                "108-116). C'est ici qu'Origène défend la compatibilité de "
                "la préscience divine avec la liberté humaine (6,3)"
            ),
            "furst_2022_principal_edition_used": "GCS Orig. 2 (Koetschau) ; traduction allemande von Stritzky OWD 21 ; études : van der Eijk 1988, Perrone, Benjamins, Hengstermann",
        },
    },
    {
        "id": "work_origen_philocalia",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. V 1 + V 3 — Philocalie ch. 21-27 contient le Freiheitstraktat en grec",
            "furst_2022_chapter": "V.1-3 (passim) — Philocalie comme collection de fragments grecs préservant le Περὶ αὐτεξουσίου",
            "furst_2022_pages": "p. 190 et passim",
            "furst_2022_key_thesis": (
                "Fürst 2022 : la Philocalie (anthologie compilée vers 360/70 "
                "par Grégoire de Nazianze et Basile de Césarée) préserve en "
                "grec les chapitres 21-27 = le Freiheitstraktat (= De "
                "Principiis III 1) et le chapitre 23 = fragment grec du "
                "Commentaire sur la Genèse Livre III (anti-astrologie). "
                "Texte critique : SC 226 (Junod)"
            ),
            "furst_2022_principal_edition_used": "SC 226 et 302 (Junod, Harl) ; édition de référence",
        },
    },
    {
        "id": "work_origen_contra_celsum_sc132",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. V 1 + VI 4 (passim) — œuvre tardive (248/49) où Origène réaffirme sa théorie de la liberté",
            "furst_2022_chapter": "V.1 et VI.4 — Contra Celsum II 13-27, IV 3, IV 45, V 21, VIII 15, VIII 76",
            "furst_2022_pages": "p. 188-189, 192, 287",
            "furst_2022_key_thesis": (
                "Fürst 2022 : Contra Celsum (248/49) contient les dernières "
                "formulations origéniennes sur la liberté. Cels. IV 3 : « si "
                "l'on supprime le caractère volontaire (τὸ ἑκούσιον) de la "
                "vertu, on supprime aussi son essence ». Cels. V 21 : « la "
                "nature de ce qui dépend de nous admet des possibilités "
                "différentes ». Cels. VIII 76 : tâche d'Origène = « par des "
                "doctrines droites encourager à la meilleure vie » (ἄριστος "
                "βίος)"
            ),
            "furst_2022_principal_edition_used": "GCS Orig. 1-2 (Koetschau) ; SC 132/136/147/150 (Borret) ; traduction allemande Barthold FC 50/1-5",
        },
    },
    {
        "id": "work_origen_commentary_romans",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. V 1 + VI 4 — œuvre tardive où Origène affirme la permanence du libre arbitre",
            "furst_2022_chapter": "V.1 et VI.4 — Comm. Rom. V 10,11-12 ; VI 3,4 ; VII 6,5 ; VIII 10,3-11",
            "furst_2022_pages": "p. 188, 254, 285",
            "furst_2022_key_thesis": (
                "Fürst 2022 : le Commentaire sur l'Épître aux Romains "
                "(traduit en latin par Rufin) contient des formulations "
                "tardives décisives : « cette liberté de décision (libertas "
                "arbitrii) appartiendra toujours pour la durée à un être "
                "rationnel » (V 10,11) ; « la nature de chaque homme a été "
                "déterminée par la liberté de sa décision (arbitrii "
                "libertas) » (VIII 10,11) — formulations qui prouvent que "
                "l'ontologisation de la liberté est une thèse permanente "
                "d'Origène"
            ),
            "furst_2022_principal_edition_used": "SC 539, 543 (Hammond Bammel) ; traduction allemande Heither FC 2/1-6",
        },
    },
    # =========================================================================
    # CONCEPTS — autexousion, prohairesis, eph hemin, will, etc.
    # =========================================================================
    {
        "id": "concept_autexousion_christian",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. V 2 + tout au long — concept central origénien",
            "furst_2022_chapter": "V.2 Der Freiheitsbegriff des Origenes",
            "furst_2022_pages": "p. 195-216",
            "furst_2022_key_thesis": (
                "Fürst 2022 : τὸ αὐτεξούσιον (« la maîtrise sur soi-même », "
                "« l'autodétermination ») est attesté pour la première fois "
                "chez Diodore de Sicile XIV 105,4 (1er s. av. J.-C.) et chez "
                "Josèphe AJ IV 146 et V 13,5 dans un sens politique-social. "
                "Origène en fait le terme technique central de sa théorie "
                "de la liberté, équivalent grec de De Principiis liberi "
                "arbitrii et voluntatis (rendu par Rufin). « L'autexousion "
                "est liberté » (Hom. Jér. 18,3 = épigraphe du livre)"
            ),
            "furst_2022_origenian_definition": "τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι (Origène, Hom. Jér. 18,3, GCS Orig. 32, 154)",
        },
    },
    {
        "id": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. II 3 + IV passim — προαίρεσις aristotélicienne et son destin chrétien",
            "furst_2022_chapter": "II.3 Aristoteles et passim",
            "furst_2022_pages": "p. 62-73 + 156-160 et passim",
            "furst_2022_key_thesis": (
                "Fürst 2022 : la προαίρεσις aristotélicienne signifie "
                "« délibération » avec laquelle « on préfère une chose à une "
                "autre » (Dirlmeier) — ni « choix libre » ni « volonté ». "
                "Justin la qualifiera pour la première fois explicitement de "
                "« libre » (ἐλεύθερα), innovation décisive. La syntagme "
                "« ἐλεύθερα προαίρεσις » est attestée pour la première fois "
                "chez Philon (De Deo immut. 47-49) puis revient chez Épictète "
                "en passant — mais c'est Justin qui en fait un slogan"
            ),
        },
    },
    {
        "id": "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. II 3-6 + III + V passim — concept terminologique central",
            "furst_2022_chapter": "II.3 et passim — τὸ ἐφ᾽ ἡμῖν dans toute la tradition",
            "furst_2022_pages": "passim p. 62 ss",
            "furst_2022_key_thesis": (
                "Fürst 2022 (suivant Bobzien Determinism and Freedom 280 "
                "Anm. 95) : la forme substantivée τὸ ἐφ᾽ ἡμῖν n'est pas "
                "attestée pour le Vieux-Stoïcisme et ne peut au plus tôt se "
                "trouver derrière les formulations latines in nostra "
                "potestate ou sita in nobis. Le rendu fréquent par "
                "« volonté » ou « liberté » ou « liberté de la volonté » est "
                "« franchement trompeur » selon Fürst — il s'agit de « ce "
                "qui dépend de nous », non de la volonté"
            ),
        },
    },
    {
        "id": "concept_liberum_arbitrium_u3v4w5x6",
        "metadata_updates": {
            "furst_2022_treatment": "Kap. III 3a + V passim — concept latin équivalent",
            "furst_2022_chapter": "III.3a Cicero ; V passim — réception latine d'Origène par Rufin",
            "furst_2022_pages": "p. 121-126, 193, 254",
            "furst_2022_key_thesis": (
                "Fürst 2022 : Rufin traduit τὸ αὐτεξούσιον / τὸ ἐφ᾽ ἡμῖν "
                "origéniens par l'hendiadyon liberum arbitrium et voluntas — "
                "le terme voluntas vient de la tradition latine cicéronienne "
                "et n'a pas d'équivalent direct grec chez Origène. Rufin "
                "« saisit correctement l'intellectualisme d'Origène, chez "
                "qui ce qu'on appelle plus tard 'volonté' et la décision "
                "guidée par la raison forment une unité » (citant "
                "Hengstermann)"
            ),
        },
    },
    # =========================================================================
    # SCHOLARS — Fürst engages with these
    # =========================================================================
    {
        "id": "scholar_dihle_albrecht",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 dialogue critique avec Dihle (Vorstellung vom "
                "Willen, 1985 / The Theory of Will, 1982) : accepte que la "
                "Grèce n'a pas de concept de volonté distinct de l'intellect "
                "et que le voluntarisme commence avec Augustin, MAIS conteste "
                "la marginalisation d'Origène. Pour Fürst, Origène marque "
                "déjà le tournant décisif avant Augustin par son ontologisation "
                "de la liberté — Dihle 1980 (Das Problem der "
                "Entscheidungsfreiheit) « méconnaît la contribution novatrice "
                "des chrétiens primitifs au débat sur la liberté »"
            ),
            "furst_2022_pages_engaged": "Anm. 1, Anm. 2, p. 8 ss + 5102 Anm. 1",
        },
    },
    {
        "id": "person_frede_michael_1940_2007",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 dialogue avec Michael Frede (A Free Will. Origins "
                "of the Notion in Ancient Thought, 2011) : (1) accord avec "
                "Frede sur l'absence de concept de volonté chez Platon et "
                "Aristote (« Neither Plato nor Aristotle has a notion of a "
                "will », Frede 19) ; (2) accord sur l'influence chrétienne "
                "sur la diffusion de la croyance au libre arbitre (Frede 89, "
                "102-103) ; (3) désaccord : Frede situe l'origine du concept "
                "de volonté chez Épictète — pour Fürst, c'est Justin et les "
                "platoniciens chrétiens qui marquent le vrai tournant, dont "
                "Origène est l'aboutissement"
            ),
            "furst_2022_pages_engaged": "Anm. 1, Anm. 4, 5096-5098, et passim",
        },
    },
    {
        "id": "person_bobzien_susanne_contemporary",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 reprend les analyses de Susanne Bobzien "
                "(Determinism and Freedom in Stoic Philosophy, 1998) : (1) "
                "sur la forme substantivée τὸ ἐφ᾽ ἡμῖν non attestée pour le "
                "Vieux-Stoïcisme (Bobzien 280 Anm. 95) ; (2) sur l'attribution "
                "tardive à Chrysippe du τὸ αὐτεξούσιον par Hippolyte ref. I "
                "21,2 — anachronisme. Fürst utilise Bobzien comme référence "
                "philologique standard mais déplace l'attention de la Stoa "
                "vers le platonisme chrétien"
            ),
            "furst_2022_pages_engaged": "p. 10, 90 Anm. 115, et passim",
        },
    },
    {
        "id": "scholar_kobusch_theo",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 s'appuie fortement sur Theo Kobusch "
                "(Selbstbestimmte Freiheit ; Selbstwerdung und Personalität ; "
                "Die philosophische Bedeutung des Kirchenvaters Origenes, "
                "1985) : Kobusch a, après Holz 1970, le premier souligné la "
                "place philosophique d'Origène dans l'histoire de la liberté. "
                "Fürst reprend l'opposition kobuschienne entre προαίρεσις et "
                "οὐσία chez les Pères grecs et entre natura et voluntas chez "
                "Augustin (Kobusch, Selbstbestimmte Freiheit 51)"
            ),
            "furst_2022_pages_engaged": "Anm. 1, Anm. 3, p. 51 et passim",
        },
    },
    {
        "id": "scholar_crouzel_henri",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 cite Crouzel comme grand origéniste français de "
                "référence ; ses travaux sur la théologie d'Origène et la "
                "liberté forment un arrière-plan constant"
            ),
        },
    },
    {
        "id": "scholar_sharples_robert",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 cite Sharples (Alexander of Aphrodisias, On Fate, "
                "1983) comme édition de référence pour Alexandre d'Aphrodise "
                "Kap. III 3c"
            ),
        },
    },
    {
        "id": "scholar_karamanolis_george",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 dialogue critique avec Karamanolis (The Philosophy "
                "of Early Christianity / Early Christian Philosophers on Free "
                "Will) : Karamanolis discute les textes patristiques que "
                "Fürst analyse aussi mais « sans reconnaître leur spécificité "
                "chrétienne » (Fürst 5102 Anm. 1)"
            ),
            "furst_2022_pages_engaged": "Anm. 1, p. 130-135, 140-151",
        },
    },
    {
        "id": "scholar_list_n",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 note que Christian List (Warum der freie Wille "
                "existiert, 2021 / Why Free Will is Real, 2019) a revendiqué "
                "la formation conceptuelle « libertarisme compatibiliste » "
                "(compatibilist libertarianism) — Fürst note ce parallèle et "
                "ajoute que Schallenberg (Freiheit und Determinismus 302) a "
                "parlé en miroir de « libertarischer Kompatibilismus » à "
                "propos de Carnéade et Cicéron. Fürst applique cette "
                "caractérisation à Origène"
            ),
            "furst_2022_pages_engaged": "p. 282-290 Anm. 99, 100",
        },
    },
    {
        "id": "scholar_kahn_charles",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 cite Kahn (Discovering the Will, p. 234-236) "
                "pour confirmer qu'il n'y avait pas de concept de volonté "
                "dans l'Antiquité avant Augustin"
            ),
            "furst_2022_pages_engaged": "Anm. 2, p. 8",
        },
    },
    {
        "id": "person_kane_robert_1938_2022",
        "metadata_updates": {
            "furst_2022_engagement": (
                "Fürst 2022 cite Kane (Contemporary Introduction to Free Will, "
                "2005) comme référence contemporaine sur le débat liberté/"
                "déterminisme, aux côtés de Geert Keil et Christian List"
            ),
            "furst_2022_pages_engaged": "Anm. 15, p. 13",
        },
    },
]
