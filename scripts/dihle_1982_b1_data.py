"""Dihle 1982 B1 — UPDATES (metadata enrichments for existing nodes).

Targets existing nodes Dihle discusses in detail, adding fields with the
`dihle_1982_` prefix so future audits can filter Dihle-specific enrichments
without ambiguity. Descriptions are left intact.

Touches : Aristotle, Plato, Chrysippus, Zeno of Citium, Cleanthes, Epictetus,
Plotinus, Philo, Origen, Augustine, Frede, Bobzien, Pohlenz, Snell, Kahn,
Voelke, Tertullian, Nemesius, Iamblichus, the debate `debate_discovery_of_will`,
the debate `debate_intellectualism_vs_voluntarism_w3x4y5z6`, and key concepts
(prohairesis, synkatathesis, voluntas).
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # =========================================================================
    # ARISTOTLE — Lect. II §III, prohairesis as intellectualist concept
    # =========================================================================
    {
        "id": "person_aristotle_384_322bce_c2d4f6a8",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. II (Greek View of Human Action I), p. 20-47",
            "dihle_1982_lecture": "II",
            "dihle_1982_pages": "p. 20-47, esp. p. 27-30, 41-47",
            "dihle_1982_judgement": (
                "Aristote represente pour Dihle l'aboutissement de "
                "l'intellectualisme grec : prohairesis (choix delibere) "
                "et boulesis (volition rationnelle) sont des concepts "
                "intellectuels presupposant la cognition d'un objet "
                "determine. L'akrasia (EN VII) ouvre theoriquement un "
                "espace pour une faculte de volonte distincte, mais "
                "Aristote ne franchit jamais ce pas. Dihle critique "
                "explicitement Anthony Kenny (Aristotle's Theory of the "
                "Will, 1979) qui soutenait l'existence d'une theorie "
                "aristotelicienne de la volonte"
            ),
            "dihle_1982_critique_target": "Anthony Kenny 1979 (counter-thesis on Aristotelian will)",
        },
    },
    # =========================================================================
    # PLATO — Lect. II §I, Socratic intellectualism
    # =========================================================================
    {
        "id": "person_plato_428_348bce_a1b2c3d4",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. II §I, Protagoras 358c-d",
            "dihle_1982_lecture": "II",
            "dihle_1982_pages": "p. 20-25",
            "dihle_1982_judgement": (
                "Le paradoxe socratique 'nul ne fait le mal "
                "volontairement' (Prot. 358c-d) est, pour Dihle, "
                "l'enonce fondateur de l'intellectualisme grec : "
                "l'action est entierement reductible a la cognition du "
                "bien. Cette these socratico-platonicienne empechera "
                "structurellement la pensee grecque ulterieure de "
                "concevoir une faculte de volonte autonome"
            ),
        },
    },
    # =========================================================================
    # CHRYSIPPUS — Lect. III, synkatathesis (cognitive)
    # =========================================================================
    {
        "id": "person_chrysippus_280_206bce_i9j0k1l2",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. III (Greek View of Human Action II), p. 48-89",
            "dihle_1982_lecture": "III",
            "dihle_1982_pages": "p. 60-64",
            "dihle_1982_judgement": (
                "Pour Dihle, la synkatathesis chrysippeenne, malgre son "
                "apparence quasi-voluntariste, demeure cognitive : "
                "perception, imagination, assentiment et impulsion sont "
                "'entirely rational'. Le 'weak assent' (asthenes "
                "synkatathesis, SVF 3.172, 3.548) n'echappe pas a la "
                "grille intellectualiste — la faiblesse est analysee en "
                "termes de jugement defaillant. Chrysippe represente "
                "l'apogee de la sophistication psychologique grecque "
                "sans pour autant developper un concept autonome de "
                "volonte"
            ),
        },
    },
    # =========================================================================
    # ZENO OF CITIUM — founder of Stoic intellectualist psychology
    # =========================================================================
    {
        "id": "person_zeno_citium_334_262bce",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. III (Greek View of Human Action II), p. 48-89",
            "dihle_1982_lecture": "III",
            "dihle_1982_pages": "p. 48-60",
            "dihle_1982_judgement": (
                "Zenon, fondateur du portique, etablit le cadre "
                "intellectualiste que Chrysippe systematisera : "
                "l'assentiment (synkatathesis) a une impression "
                "(phantasia) est un acte de la raison, et toutes les "
                "phases de l'action procedent de l'hegemonikon rationnel"
            ),
        },
    },
    # =========================================================================
    # CLEANTHES — Lect. I, ep. 41.1 (Sen.) 'fata volentem ducunt'
    # =========================================================================
    {
        "id": "person_cleanthes_assos_330_230bce",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. I et III, p. 4, p. 60",
            "dihle_1982_lecture": "I, III",
            "dihle_1982_pages": "p. 4, p. 60",
            "dihle_1982_judgement": (
                "Dihle cite l'hymne et la phrase celebre 'fata volentem "
                "ducunt, nolentem trahunt' (ap. Sen. ep. 41.1) comme "
                "exemple d'un voluntarisme apparent qui reste cognitif : "
                "volentem signifie 'aligne avec' le destin, et le "
                "consentement (Sen. ep. : 'Non pareo deo sed assentior', "
                "md l. 840) est l'acte par lequel la raison embrasse "
                "l'ordre du logos"
            ),
        },
    },
    # =========================================================================
    # EPICTETUS — Lect. III, prohairesis (NOT yet 'free will' per Dihle)
    # =========================================================================
    {
        "id": "person_epictetus_of_hierapolis_3c385bc2",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. III, p. 60-66",
            "dihle_1982_lecture": "III",
            "dihle_1982_pages": "p. 60-66, esp. 855-870 (passim)",
            "dihle_1982_judgement": (
                "Pour Dihle, Epictete demeure dans le cadre intellectualiste "
                "grec : sa prohairesis est encore principalement cognitive, "
                "et son theleo (md l. 855) doit etre lu en continuite avec "
                "Aristote. POINT DE CONTROVERSE MAJEUR : Frede 2011 "
                "soutient au contraire qu'Epictete introduit la premiere "
                "notion de free will (eleuthera prohairesis), "
                "qu'Augustin ne fait que reformuler en latin. Cette "
                "divergence est l'une des principales lignes de fracture "
                "de la litterature recente sur l'histoire de la volonte"
            ),
            "dihle_1982_controversy_with_frede_2011": (
                "Dihle minimise Epictete ; Frede 2011 (p. 77) y voit le "
                "veritable inventeur. Augustin = variation latine selon "
                "Frede ; invention veritable selon Dihle"
            ),
        },
    },
    # =========================================================================
    # PLOTINUS — Lect. V, Enn. VI.8 'will of the One' remains intellectualist
    # =========================================================================
    {
        "id": "person_plotinus_d270",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. V (Philosophy and Religion in Late Antiquity), p. 101-122",
            "dihle_1982_lecture": "V",
            "dihle_1982_pages": "p. 101-122, esp. 117-120 sur Enn. VI.8",
            "dihle_1982_judgement": (
                "Plotin (Enn. III.1, IV.8, VI.8) introduit une terminologie "
                "apparemment voluntariste (autexousios, boulesis, ephesis "
                "tou agathou) et discute frontalement la liberte de l'Un et "
                "de l'ame. Mais Dihle demontre que la liberte plotinienne "
                "se ramene in fine a la coincidence de l'agent avec sa "
                "nature intellective (nous). La 'tolma' designe la chute "
                "dans la multiplicite ; l'ascension reste cognitive. Meme "
                "la 'volonte de l'Un' (Enn. VI.8) demeure intellectualiste : "
                "will = activity of nous. Plotin confirme donc la these de "
                "l'intellectualisme grec structurel"
            ),
        },
    },
    # =========================================================================
    # PHILO OF ALEXANDRIA — Lect. IV §IV, Judeo-Hellenistic mediation
    # =========================================================================
    {
        "id": "person_philo_alexandria_a1b2c3d4",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. IV (St. Paul and Philo), p. 91-100",
            "dihle_1982_lecture": "IV",
            "dihle_1982_pages": "p. 91-100",
            "dihle_1982_judgement": (
                "Philon represente la mediation judeo-hellenistique : il "
                "tente de concilier la theologie biblique de la volonte "
                "divine (theleo, boulesis) avec le langage philosophique "
                "grec, en insistant sur la grace, le soin et la bienveillance "
                "de Dieu. Pour Dihle, Philon est un jalon prepauline : il "
                "amorce le travail conceptuel sans le terminer, et son "
                "vocabulaire reste pluraliste (theleo, boule, boulesis, "
                "thelema, eudokia, gnome) sans terme technique unique"
            ),
        },
    },
    # =========================================================================
    # ORIGEN — Lect. V mention, Greek patristic preserving intellectualist frame
    # =========================================================================
    {
        "id": "person_origen_alexandria_185_254ce_s9t0u1v2",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. V (Philosophy and Religion in Late Antiquity), p. 101-122",
            "dihle_1982_lecture": "V",
            "dihle_1982_pages": "p. 105-110 (passim)",
            "dihle_1982_judgement": (
                "Origene exemplifie la patristique grecque qui developpe "
                "une terminologie de la liberte (autexousion, proairesis, "
                "to eph hemin) mais reste tributaire des categories "
                "intellectualistes grecques. Pour Dihle, Origene n'invente "
                "pas le concept philosophique de volonte au sens strict : "
                "ce sera Augustin, sous l'influence convergente de "
                "l'anthropologie biblique et de la polemique anti-"
                "manicheenne/anti-pelagienne"
            ),
        },
    },
    # =========================================================================
    # AUGUSTINE — Lect. VI, full thesis: he invents the philosophical concept
    # =========================================================================
    {
        "id": "person_augustine_hippo_d430",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. VI (St. Augustine and His Concept of Will), p. 123-150",
            "dihle_1982_lecture": "VI",
            "dihle_1982_pages": "p. 123-150",
            "dihle_1982_judgement": (
                "These centrale de Dihle 1982 : Augustin est l'inventeur "
                "du concept philosophique de volonte. 'The notion of will, "
                "as it is used as a tool of analysis and description in "
                "many philosophical doctrines from the early Scholastics "
                "to Schopenhauer and Nietzsche, was invented by St. "
                "Augustine' (p. 144). Trois sources convergentes : "
                "anthropologie biblique (homo imago Dei), ontologie "
                "neoplatonicienne (mal comme privation, amour comme "
                "orientation), introspection psychologique (Confessiones "
                "VIII : division interieure du vouloir). Augustin "
                "transforme le terme latin voluntas (jusqu'alors flou "
                "chez Ciceron et Seneque) en faculte mentale autonome, "
                "irreductible a l'intellect ET a l'emotion. La triade "
                "memoria-intellectus-voluntas (De Trin. IX-X) la pose au "
                "meme rang ontologique que la memoire et l'intelligence. "
                "Innovation forgee sous l'aiguillon double du manicheisme "
                "et du pelagianisme"
            ),
            "dihle_1982_central_thesis_anchor_quote": (
                "the notion of will ... was invented by St. Augustine "
                "(Dihle 1982 p. 144)"
            ),
        },
    },
    # =========================================================================
    # NEMESIUS OF EMESA — Greek patristic preserving intellectualist frame
    # =========================================================================
    {
        "id": "person_nemesius_emesa_4c_ce",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. V, p. 109-115 (passim)",
            "dihle_1982_lecture": "V",
            "dihle_1982_pages": "p. 109-115",
            "dihle_1982_judgement": (
                "Pour Dihle, Nemese d'Emese fait partie des Peres grecs "
                "qui developpent un vocabulaire technique de la liberte "
                "(to eph hemin, autexousion, prohairesis, boulesis) sans "
                "pour autant rompre avec l'intellectualisme grec. La "
                "rupture decisive viendra de l'Occident latin avec Augustin"
            ),
        },
    },
    # =========================================================================
    # IAMBLICHUS — Lect. V, late Neoplatonism remains intellectualist
    # =========================================================================
    {
        "id": "person_iamblichus_d325",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. V, p. 101-122 (passim, in line of Plotinus)",
            "dihle_1982_lecture": "V",
            "dihle_1982_pages": "p. 115-122",
            "dihle_1982_judgement": (
                "Iamblique herite et durcit la structure intellectualiste "
                "plotinienne. Pour Dihle, meme la theurgie iamblichienne "
                "n'introduit pas un concept autonome de volonte : elle "
                "reste un acte cognitif ritualise par lequel l'ame "
                "s'unit aux dieux"
            ),
        },
    },
    # =========================================================================
    # PORPHYRY — Lect. V, disciple of Plotinus
    # =========================================================================
    {
        "id": "person_porphyry",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. V, p. 117-118",
            "dihle_1982_lecture": "V",
            "dihle_1982_pages": "p. 117-118",
            "dihle_1982_judgement": (
                "Pour Dihle, Porphyre, 'most eminent pupil' de Plotin (md "
                "l. 4654), prolonge la structure intellectualiste de son "
                "maitre : la liberte reste cognitive, ascension vers l'Un "
                "par le nous"
            ),
        },
    },
    # =========================================================================
    # SENECA — Lect. III, voluntas in late writings (pre-Augustinian semantics)
    # =========================================================================
    {
        "id": "person_seneca_4bce_65ce_a1b2c3d4",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. III et VI, p. 60 et p. 138",
            "dihle_1982_lecture": "III, VI",
            "dihle_1982_pages": "p. 60, p. 138-139",
            "dihle_1982_judgement": (
                "Seneque presente une transition interessante pour Dihle : "
                "il commence a percevoir les implications voluntaristes "
                "du terme voluntas dans ses ecrits tardifs (md ll. 5433-"
                "5435) mais ne franchit pas le pas. Sa phrase 'Non pareo "
                "deo sed assentior' (ep. 41.1, md l. 840) reste cognitive. "
                "Seneque prepare le terrain latin sur lequel Augustin "
                "construira la voluntas comme faculte autonome"
            ),
        },
    },
    # =========================================================================
    # CICERO — Lect. VI, voluntas as loose pre-Augustinian Latin term
    # =========================================================================
    {
        "id": "person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. VI §I, p. 137-138",
            "dihle_1982_lecture": "VI",
            "dihle_1982_pages": "p. 137-138",
            "dihle_1982_judgement": (
                "Ciceron utilise voluntas comme equivalent libre de "
                "prohairesis / boulesis grecs. Le mot a chez lui un large "
                "champ semantique : tantot desir spontane, tantot impulsion "
                "(horme), tantot intention deliberee. Pas de valeur "
                "technique philosophique stricte. C'est ce terme souple "
                "qu'Augustin transformera en faculte autonome"
            ),
        },
    },
    # =========================================================================
    # TERTULLIAN — pre-Augustinian Latin Christian thinker
    # =========================================================================
    {
        "id": "person_tertullian_d220",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. V-VI, passim (in line of Latin Christian preparation)",
            "dihle_1982_lecture": "V, VI",
            "dihle_1982_pages": "p. 130-135 (passim)",
            "dihle_1982_judgement": (
                "Pour Dihle, Tertullien represente une etape "
                "preaugustinienne de la latinisation des concepts "
                "chretiens, mais sans encore thematiser une voluntas "
                "philosophique autonome. Il prepare le vocabulaire que "
                "Augustin systematisera"
            ),
        },
    },
    # =========================================================================
    # PELAGIUS — Lect. VI §II, polemical context for invention
    # =========================================================================
    {
        "id": "person_pelagius_d420",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. VI §II (anti-Pelagian controversy), p. 137-140",
            "dihle_1982_lecture": "VI",
            "dihle_1982_pages": "p. 137-140",
            "dihle_1982_judgement": (
                "Pour Dihle, Pelage exalte la liberte naturelle de la "
                "volonte humaine ('Pelagius understandably exaggerated "
                "the importance', md l. 5271) et provoque la reaction "
                "augustinienne. La polemique anti-pelagienne est l'un "
                "des deux aiguillons qui forcent Augustin a thematiser "
                "la voluntas — l'autre etant l'anti-manicheisme"
            ),
        },
    },
    # =========================================================================
    # FREDE MICHAEL — central interlocutor (39 citations of Dihle 1982)
    # =========================================================================
    {
        "id": "person_frede_michael_1940_2007",
        "metadata_updates": {
            "dihle_1982_treatment": "Interlocuteur scolaire central (Frede 2011 cite Dihle 1982 39 fois)",
            "dihle_1982_lecture": "n/a (modern reception)",
            "dihle_1982_pages": "n/a",
            "dihle_1982_judgement": (
                "Frede 2011 (*A Free Will*, Sather 64) est l'interlocuteur "
                "scolaire central de Dihle 1982 : 39 citations directes, "
                "discussion frontale de la these. Frede conteste la "
                "datation augustinienne : pour lui, la premiere notion de "
                "free will emerge chez Epictete (eleuthera prohairesis, "
                "Frede 2011 p. 77), et Augustin ne fait que reformuler en "
                "latin avec des ajustements platoniciens. Cette divergence "
                "est l'une des principales lignes de fracture de la "
                "litterature contemporaine sur l'histoire de la volonte"
            ),
        },
    },
    # =========================================================================
    # BOBZIEN SUSANNE — modern critic of Dihle's framework
    # =========================================================================
    {
        "id": "person_bobzien_susanne_contemporary",
        "metadata_updates": {
            "dihle_1982_treatment": "Critique methodologique (Bobzien 1998, 2001)",
            "dihle_1982_lecture": "n/a (modern reception)",
            "dihle_1982_pages": "n/a",
            "dihle_1982_judgement": (
                "Bobzien 1998 (*Determinism and Freedom in Stoic "
                "Philosophy*) ne cite Dihle 1982 que deux fois mais "
                "critique implicitement sa grille : projeter l'antithese "
                "'intellectualisme vs voluntarisme' sur le materiau "
                "hellenistique est anachronique. Pour Bobzien, le probleme "
                "veritable des Stoiciens est 'eph hemin / heimarmene', "
                "non 'will vs intellect'. Critique methodologique plus "
                "que doctrinale"
            ),
        },
    },
    # =========================================================================
    # POHLENZ MAX — Dihle's main historiographical precursor
    # =========================================================================
    {
        "id": "scholar_pohlenz_max",
        "metadata_updates": {
            "dihle_1982_treatment": "Precurseur historiographique principal",
            "dihle_1982_lecture": "n/a (lineage)",
            "dihle_1982_pages": "n/a",
            "dihle_1982_judgement": (
                "Pohlenz, *Die Stoa* (1948-49), est l'un des principaux "
                "precurseurs de Dihle 1982 : il a etabli que les "
                "Stoiciens ne disposaient pas d'un veritable concept de "
                "volonte. Dihle radicalise et generalise cette intuition "
                "a toute la pensee grecque, en y ajoutant la these "
                "augustinienne forte"
            ),
        },
    },
    # =========================================================================
    # SNELL BRUNO — Discovery of Mind (1946) — Dihle precursor
    # =========================================================================
    {
        "id": "scholar_snell_bruno",
        "metadata_updates": {
            "dihle_1982_treatment": "Precurseur (Snell 1946, Die Entdeckung des Geistes)",
            "dihle_1982_lecture": "n/a (lineage)",
            "dihle_1982_pages": "n/a",
            "dihle_1982_judgement": (
                "Snell, *Die Entdeckung des Geistes* (1946), defend une "
                "these de l'evolution graduelle de la conscience grecque "
                "depuis Homere jusqu'a la philosophie classique. Dihle "
                "etend cette logique en posant que la volonte autonome "
                "n'a *jamais* ete decouverte en Grece : c'est une "
                "invention chretienne"
            ),
        },
    },
    # =========================================================================
    # KAHN CHARLES — broad agreement on Greek terms vs voluntas
    # =========================================================================
    {
        "id": "scholar_kahn_charles",
        "metadata_updates": {
            "dihle_1982_treatment": "Accord large (Kahn 1988)",
            "dihle_1982_lecture": "n/a (reception)",
            "dihle_1982_pages": "n/a",
            "dihle_1982_judgement": (
                "Kahn 1988 (*Discovering the Will: from Aristotle to "
                "Augustine*) appuie largement Dihle : la boulesis et "
                "l'hekousion aristoteliciens ne constituent pas un "
                "concept de volonte, et l'ecart entre les termes grecs "
                "et la voluntas augustinienne marque une vraie innovation. "
                "Kahn est l'un des principaux relais anglophones de la "
                "these dihlienne"
            ),
        },
    },
    # =========================================================================
    # VOELKE ANDRE-JEAN — predecessor (1973 Stoic will study)
    # =========================================================================
    {
        "id": "scholar_voelke_andre_jean",
        "metadata_updates": {
            "dihle_1982_treatment": "Predecesseur direct (Voelke 1973)",
            "dihle_1982_lecture": "n/a (lineage)",
            "dihle_1982_pages": "n/a",
            "dihle_1982_judgement": (
                "Voelke, *L'idee de volonte dans le stoicisme* (1973), "
                "soutient que la pensee antique n'a pas developpe de "
                "concept de volonte comme tel ; les concepts stoiciens "
                "(synkatathesis, horme, tonos) fonctionnent comme "
                "facultes quasi-volitives organiquement liees. Dihle "
                "reprend cette these et l'etend a toute la pensee grecque "
                "(non plus seulement aux Stoiciens), en y greffant la "
                "these augustinienne"
            ),
        },
    },
    # =========================================================================
    # CONCEPTS — prohairesis (Aristotelian), synkatathesis (Stoic), voluntas
    # =========================================================================
    {
        "id": "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. II, p. 30-47 — concept central de l'intellectualisme grec",
            "dihle_1982_lecture": "II",
            "dihle_1982_pages": "p. 30-47",
            "dihle_1982_judgement": (
                "Pour Dihle, prohairesis aristotelicien est le concept "
                "paradigmatique de l'intellectualisme grec : 'choix "
                "delibere fonde sur la connaissance prealable d'un objet "
                "determine'. Traduire prohairesis par 'will' est "
                "anachronique. Concept central de toute l'analyse de la "
                "Lect. II"
            ),
        },
    },
    {
        "id": "concept_synkatathesis_stoic_assent",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. III, p. 60-64 — objection principale a la these de Dihle",
            "dihle_1982_lecture": "III",
            "dihle_1982_pages": "p. 60-64",
            "dihle_1982_judgement": (
                "La synkatathesis stoicienne est, pour Dihle, l'objection "
                "la plus forte contre sa these — et donc le concept qu'il "
                "doit demonter en detail. Sa demonstration : "
                "l'assentiment reste cognitif (les quatre phases de "
                "l'action sont 'entirely rational'), meme dans le cas du "
                "'weak assent' (SVF 3.172, 3.548). Concept-cle pour "
                "evaluer la these dihlienne"
            ),
        },
    },
    {
        "id": "concept_voluntas_y7z8a9b0",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. VI, p. 123-150 — concept invente par Augustin",
            "dihle_1982_lecture": "VI",
            "dihle_1982_pages": "p. 123-150",
            "dihle_1982_judgement": (
                "These centrale de Dihle : voluntas comme faculte mentale "
                "autonome irreductible a l'intellect et a l'emotion est "
                "une invention augustinienne. Le mot voluntas prexistait "
                "(Ciceron, Seneque) mais avec un champ semantique flou. "
                "Augustin lui confere un statut technique strict. Concept "
                "fondateur de toute la psychologie philosophique "
                "occidentale jusqu'a Schopenhauer et Nietzsche"
            ),
        },
    },
    {
        "id": "concept_socratic_intellectualism_f6g7h8i9",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. II §I — point de depart historique de l'intellectualisme grec",
            "dihle_1982_lecture": "II",
            "dihle_1982_pages": "p. 20-25",
            "dihle_1982_judgement": (
                "L'intellectualisme socratique (paradoxe 'nul ne fait le "
                "mal volontairement', Protagoras 358c-d) est, pour Dihle, "
                "le point de depart historique de l'intellectualisme grec "
                "qui rendra toute la tradition incapable de concevoir une "
                "faculte de volonte autonome"
            ),
        },
    },
    {
        "id": "concept_akrasia_weakness_of_will",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. II §III, akrasia comme echec cognitif et non comme defaillance volitionnelle",
            "dihle_1982_lecture": "II",
            "dihle_1982_pages": "p. 35-45",
            "dihle_1982_judgement": (
                "Pour Dihle, l'akrasia aristotelicienne (EN VII) ouvre "
                "theoriquement un espace pour une faculte de volonte "
                "distincte de la cognition, mais Aristote ne franchit "
                "pas le pas : l'akrasia reste analysee comme une "
                "defaillance cognitive (oubli, ignorance, dispersion de "
                "l'attention) et non comme une volonte qui s'oppose au "
                "jugement"
            ),
        },
    },
    {
        "id": "concept_liberum_arbitrium_u3v4w5x6",
        "metadata_updates": {
            "dihle_1982_treatment": "Lect. VI §II, le liberum arbitrium comme concept augustinien anti-pelagien",
            "dihle_1982_lecture": "VI",
            "dihle_1982_pages": "p. 137-144",
            "dihle_1982_judgement": (
                "Pour Dihle, le liberum arbitrium est une elaboration "
                "specifiquement latine d'Augustin, forgee dans la "
                "polemique anti-pelagienne. Il designe la volonte libre "
                "*blessee* par le peche originel et necessitant la grace "
                "prevenante — synthese paradoxale qui constitue la "
                "veritable invention augustinienne"
            ),
        },
    },
    # =========================================================================
    # DEBATES — debate_discovery_of_will, debate_intellectualism_vs_voluntarism
    # =========================================================================
    {
        "id": "debate_discovery_of_will",
        "metadata_updates": {
            "dihle_1982_treatment": "Debat structurant entierement organise par Dihle 1982",
            "dihle_1982_lecture": "I-VI (volume entier)",
            "dihle_1982_pages": "p. 1-150",
            "dihle_1982_judgement": (
                "Dihle 1982 est l'organisateur principal de ce debat : "
                "il pose la question 'quand et comment le concept "
                "philosophique de volonte a-t-il emerge ?' et y repond "
                "par 'avec Augustin, vers 396-415'. Toutes les positions "
                "ulterieures (Kahn 1988, Irwin 1992, Frede 2011, Sorabji "
                "2000, Cary 2007, Bobzien 1998) se positionnent par "
                "rapport a cette these. Dihle est cite comme reference "
                "fondatrice du debat dans la presque totalite des "
                "publications contemporaines"
            ),
        },
    },
    {
        "id": "debate_intellectualism_vs_voluntarism_w3x4y5z6",
        "metadata_updates": {
            "dihle_1982_treatment": "Debat principal structure par Dihle 1982",
            "dihle_1982_lecture": "I-VI (volume entier)",
            "dihle_1982_pages": "p. 1-150",
            "dihle_1982_judgement": (
                "L'antithese intellectualisme / voluntarisme est l'axe "
                "organisateur du volume de Dihle. Selon lui, toute la "
                "pensee grecque est intellectualiste ; le voluntarisme "
                "philosophique nait avec Augustin. Cette grille a ete "
                "questionnee comme anachronique par Bobzien et Frede, "
                "mais elle reste un point de reference structurant"
            ),
        },
    },
]
