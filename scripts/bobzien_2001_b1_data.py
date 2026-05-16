"""Bobzien 2001 B1 — UPDATES list (metadata enrichments for existing nodes).

Light metadata-only enrichments. Descriptions remain intact unless explicitly
overhauled by the central scholar / publication updates.

Targets:
- Scholar: person_bobzien_susanne_contemporary  -> bio overhaul
- Publication: scholarly_work_bobzien_2001_determinism_and_freedom_in_stoic_philoso -> overhaul
- Ancient persons + works + arguments + concepts Bobzien interprets in 2001
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # =========================================================================
    # 1. SCHOLAR NODE — overhaul Bobzien's bio
    # =========================================================================
    {
        "id": "person_bobzien_susanne_contemporary",
        "description": (
            "Susanne Bobzien (nee Susanne Bobzien, b. 1960), philosophe germano-"
            "britannique, professeur de philosophie a l'Universite de Yale (chaire "
            "Joseph C. Hutchinson) puis senior research fellow All Souls College "
            "Oxford. Specialiste mondiale du stoicisme ancien, de la logique "
            "stoicienne et de la philosophie ancienne du determinisme. Eleve "
            "de Michael Frede a Princeton (these de doctorat sur Chrysippe). Son "
            "ouvrage de 2001 Determinism and Freedom in Stoic Philosophy "
            "(Clarendon Press; copyright 1998, reedition broche 2001) est "
            "universellement reconnu comme la reconstruction de reference du "
            "determinisme causal stoicien et du compatibilisme chrysippeen. "
            "These centrale : les Stoiciens n'ont pas eu de notion de libre "
            "arbitre au sens libertaire moderne ; ils ont developpe un "
            "compatibilisme causal sophistique mais distinct du probleme moderne. "
            "Le probleme du libre arbitre est ne tardivement et par "
            "inadvertance au IIe siecle CE avec Alexandre d'Aphrodise (these "
            "complementaire : Bobzien 1998 OSAP)"
        ),
        "description_en": (
            "Susanne Bobzien (b. 1960), German-British philosopher, Joseph C. "
            "Hutchinson Professor of Philosophy at Yale University then senior "
            "research fellow at All Souls College, Oxford. World specialist on "
            "ancient Stoicism, Stoic logic and ancient philosophy of "
            "determinism. Student of Michael Frede at Princeton (doctoral "
            "thesis on Chrysippus). Her 2001 monograph Determinism and "
            "Freedom in Stoic Philosophy (Clarendon Press; copyright 1998, "
            "paperback 2001) is universally recognized as the reference "
            "reconstruction of Stoic causal determinism and Chrysippean "
            "compatibilism. Central thesis: the Stoics did not have a notion "
            "of free will in the modern libertarian sense; they developed a "
            "sophisticated causal compatibilism distinct from the modern "
            "problem. The free-will problem emerged late and inadvertently "
            "in the 2nd century CE with Alexander of Aphrodisias (companion "
            "thesis: Bobzien 1998 OSAP)"
        ),
        "metadata_updates": {
            "specialty": "ancient Stoicism, Stoic logic, determinism, philosophy of free will",
            "career": [
                "DPhil supervised by Michael Frede (Princeton/Oxford)",
                "Christ Church Oxford (1980s-90s)",
                "Queens College Oxford",
                "Yale University — Joseph C. Hutchinson Professor of Philosophy",
                "All Souls College, Oxford — senior research fellow (current)",
            ],
            "key_works": [
                "Determinism and Freedom in Stoic Philosophy (Clarendon Press, 1998 hb / 2001 pb)",
                "The Inadvertent Conception and Late Birth of the Free-Will Problem (Phronesis 1998)",
                "Did Epicurus Discover the Free Will Problem? (OSAP 2000)",
                "Choice and Moral Responsibility in Nicomachean Ethics III 1-5 (Cambridge Companion 2014)",
                "Determinism, Freedom and Moral Responsibility (OUP 2021, collected papers)",
            ],
            "central_theses": [
                "Stoic determinism is universal, causal, and teleological — but NOT necessitarian",
                "Chrysippus's cylinder analogy grounds compatibilism via internal vs external causes",
                "Early Stoic to_eph_hemin is one-sided causative, not two-sided potestative",
                "The free-will problem is anachronistic to ancient Stoa — born inadvertently 2c CE",
                "Epictetus's freedom (eleutheria) is moral perfection, NOT libertarian free will",
                "A later Stoic (PHILOPATOR) developed a more sophisticated causal compatibilism",
            ],
            "supervisors_and_influences": [
                "Michael Frede (DPhil supervisor; The Original Notion of Cause 1980)",
                "Jonathan Barnes (Oxford ancient philosophy mentor)",
                "Myles Burnyeat",
            ],
            "disagrees_with_in_2001": [
                "Long & Sedley (Hellenistic Philosophers 1987) on certain modal interpretations",
                "Dihle 1982 (theory of will) on the very existence of an ancient notion of will",
                "Sorabji (Necessity, Cause and Blame 1980) on selected modal points",
                "Sambursky on Stoic physics fine details",
            ],
            "later_disagreement_with_michael_frede_2011": (
                "Bobzien resiste partiellement a la these de Frede 2011 (A Free Will: Origins of "
                "the Notion in Ancient Thought) selon laquelle Epictete invente la notion ; "
                "pour Bobzien le probleme du libre arbitre nait plus tard, avec Alexandre"
            ),
            "bobzien_2001_role": "central modern voice on Stoic determinism",
            "wikidata_qid": "Q57991146",
        },
    },
    # =========================================================================
    # 2. PUBLICATION NODE — overhaul Bobzien 2001 monograph
    # =========================================================================
    {
        "id": "scholarly_work_bobzien_2001_determinism_and_freedom_in_stoic_philoso",
        "description": (
            "Susanne Bobzien, Determinism and Freedom in Stoic Philosophy "
            "(Oxford: Clarendon Press, 1998 hardback ; 2001 paperback reprint ; "
            "ISBN 0-19-823794-4 hb / 0-19-924767-6 pb, 454 pages). Monographie "
            "de reference, dense et techniquement irreprochable, sur le "
            "determinisme causal universel stoicien et son rapport au libre "
            "arbitre, a la modalite et a la responsabilite morale. Huit "
            "chapitres : (1) determinisme et destin (heimarmene, providence, "
            "nature, principe actif) ; (2) deux arguments chrysippeens pour le "
            "determinisme causal (bivalence + divination) ; (3) modalite, "
            "determinisme et liberte (systeme modal chrysippeen vs Diodore "
            "Cronos vs Philon) ; (4) divination et regularite universelle ; "
            "(5) l'argument paresseux (argos logos) et les contre-arguments ; "
            "(6) responsabilite morale et compatibilisme chrysippeen (analogie "
            "du cylindre, eph' hemin causatif) ; (7) Epictete et 'ce qui depend "
            "de nous' / liberte (eleutheria) ; (8) une theorie stoicienne plus "
            "tardive attribuee a PHILOPATOR. Bobzien soutient que les Stoiciens "
            "anciens n'ont pas eu de probleme du libre arbitre au sens moderne "
            "— ils ont developpe un compatibilisme causal sophistique, mais le "
            "concept de liberte d'agir autrement (to_eph_hemin a deux faces) "
            "n'apparait que tardivement chez les commentateurs aristoteliciens. "
            "L'ouvrage est issu d'une these de DPhil sous la direction de "
            "Michael Frede"
        ),
        "description_en": (
            "Susanne Bobzien, Determinism and Freedom in Stoic Philosophy "
            "(Oxford: Clarendon Press, 1998 hb; 2001 pb reprint; ISBN "
            "0-19-823794-4 hb / 0-19-924767-6 pb, 454 pp). Reference "
            "monograph, dense and technically impeccable, on Stoic universal "
            "causal determinism and its relation to free will, modality and "
            "moral responsibility. Eight chapters: (1) determinism and fate; "
            "(2) two Chrysippean arguments for causal determinism (bivalence "
            "+ divination); (3) modality, determinism, freedom (Chrysippean "
            "modal system vs Diodorus Cronus vs Philo); (4) divination and "
            "universal regularity; (5) the Idle Argument (argos logos) and "
            "counter-arguments; (6) moral responsibility and Chrysippean "
            "compatibilism (cylinder analogy, causative eph' hemin); (7) "
            "Epictetus and what depends on us / freedom (eleutheria); (8) a "
            "later Stoic theory attributed to PHILOPATOR. Bobzien argues "
            "that early Stoics did not have a free-will problem in the "
            "modern sense — they developed sophisticated causal "
            "compatibilism but the two-sided potestative concept of freedom "
            "to do otherwise emerges only later with Aristotelian "
            "commentators. The book derives from her DPhil thesis under "
            "Michael Frede"
        ),
        "metadata_updates": {
            "title": "Determinism and Freedom in Stoic Philosophy",
            "author": "Bobzien, Susanne",
            "author_id": "person_bobzien_susanne_contemporary",
            "publisher": "Clarendon Press / Oxford University Press",
            "year": 2001,
            "year_first_published": 1998,
            "pages": 454,
            "isbn_hardback": "0-19-823794-4",
            "isbn_paperback": "0-19-924767-6",
            "doi": "10.1093/0199247676.001.0001",
            "series": "Oxford Aristotle Studies / Oxford Classical Monographs",
            "bibtex_key": "bobzien-2001-determinism-and-freedom-in-stoic-philosophy",
            "structure_8_chapters": [
                "Ch.1: Determinism and Fate (pp. 16-58)",
                "Ch.2: Two Chrysippean Arguments for Causal Determinism (pp. 59-96)",
                "Ch.3: Modality, Determinism, and Freedom (pp. 97-143)",
                "Ch.4: Divination, Modality, and Universal Regularity (pp. 144-179)",
                "Ch.5: Fate, Action, and Motivation - the Idle Argument (pp. 180-233)",
                "Ch.6: Determinism and Moral Responsibility - Chrysippus's Compatibilism (pp. 234-329)",
                "Ch.7: Freedom and That Which Depends On Us - Epictetus and Early Stoics (pp. 330-357)",
                "Ch.8: A Later Stoic Theory of Compatibilism - PHILOPATOR (pp. 358-412)",
            ],
            "central_theses": [
                "Stoic determinism is teleological + causal, NOT necessitarian/fatalist",
                "Chrysippus's cylinder analogy = founding compatibilist analogy",
                "Early Stoic to_eph_hemin = di' hemon (one-sided causative)",
                "Free-will problem is anachronistic to early Stoa",
                "Epictetus's eleutheria = moral perfection, not libertarian freedom",
                "PHILOPATOR represents a later refinement of Stoic causal compatibilism",
            ],
            "primary_sources_central": [
                "Cicero, De Fato (passages 28-44 central)",
                "Cicero, De Divinatione",
                "Aulus Gellius, Noctes Atticae VII.2 (cylinder analogy)",
                "Alexander of Aphrodisias, De Fato",
                "Plutarch, De Stoicorum Repugnantiis",
                "Plutarch (ps.), De Fato",
                "Origen, Contra Celsum II.20 (against Idle Argument)",
                "Eusebius, Praeparatio Evangelica VI",
                "Epictetus, Discourses + Encheiridion",
                "Stobaeus (Eclogae I + II)",
                "Diogenes Laertius VII",
                "Nemesius, De Natura Hominis",
                "Boethius, In Aristotelis De Interpretatione",
            ],
            "key_modern_interlocutors": [
                "Michael Frede (supervisor; 'The Original Notion of Cause' 1980)",
                "Dorothea Frede",
                "Jonathan Barnes",
                "A.A. Long & D.N. Sedley (Hellenistic Philosophers 1987)",
                "Richard Sorabji (Necessity, Cause and Blame 1980)",
                "Bob Sharples (Alexander of Aphrodisias)",
                "Albrecht Dihle (Theory of Will 1982 — Bobzien resists)",
            ],
            "key_concepts_indexed": [
                "heimarmene (fate)",
                "to eph' hemin (what is up to us)",
                "synkatathesis (assent)",
                "hormē / aphormē (impulse / counter-impulse)",
                "eleutheria (freedom)",
                "co-fated events (confatalia / synfata)",
                "cylinder and cone analogy",
                "Idle Argument (argos logos / ignava ratio)",
                "Master Argument (kurieuon logos)",
                "Bivalence + future contingents",
                "sympatheia (cosmic sympathy)",
            ],
            "bobzien_2001_canonical_role": "definitive scholarly monograph on Stoic determinism",
            "topic_tags": ["stoicism", "determinism", "free_will", "compatibilism", "chrysippus", "epictetus", "modality"],
        },
    },
    # =========================================================================
    # 3. ANCIENT PERSON UPDATES — Bobzien 2001 treatments
    # =========================================================================
    {
        "id": "person_chrysippus_280_206bce_i9j0k1l2",
        "metadata_updates": {
            "bobzien_2001_treatment": "central focus of the entire monograph (Ch. 1-6 passim)",
            "bobzien_2001_chapter": "all chapters 1-6, especially 1, 2, 3, 5, 6",
            "bobzien_2001_pages": "passim — esp. pp. 16-58, 59-96, 97-143, 217-233, 234-329",
            "bobzien_2001_judgement": (
                "Bobzien 2001 reconstructs Chrysippus as the central author of "
                "Stoic universal causal determinism. His compatibilism is "
                "grounded in (a) the cylinder-and-cone analogy (Cic. Fat. 39-44 / "
                "Gellius NA 7.2), (b) the distinction between antecedent/external "
                "and proximate/internal causes, (c) a modal system designed to "
                "preserve contingency, (d) the doctrine of co-fated events as "
                "reply to the Idle Argument. Bobzien resists labeling Chrysippus "
                "a 'compatibilist' in the modern libertarian-vs-determinist "
                "frame — his concern is with causal responsibility, not freedom "
                "to do otherwise. Birth date 280 BCE / death c. 207 BCE confirmed"
            ),
        },
    },
    {
        "id": "person_cleanthes_assos_330_230bce",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 7 §7.3 dedicated section pp. 345-352",
            "bobzien_2001_chapter": "Ch. 7 Freedom and That Which Depends On Us",
            "bobzien_2001_pages": "p. 345-357 (Cleanthes on Destiny + the dog and cart simile)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 ch. 7.3 reconstructs Cleanthes's verses on "
                "Destiny (preserved Epict. Ench. 53 + Sen. Ep. 107.11) as a "
                "Stoic theology of acquiescence to fate. The dog-and-cart "
                "simile (canis a curru) is shown by Bobzien to belong to "
                "Epictetus's report of Cleanthes/Chrysippus, illustrating "
                "willing assent to fate while preserving causal "
                "responsibility. Cleanthes's position is consistent with "
                "Chrysippus's later refinement but less developed"
            ),
        },
    },
    {
        "id": "person_zeno_citium_334_262bce",
        "metadata_updates": {
            "bobzien_2001_treatment": "background figure — Stoic doctrine of fate inherited from",
            "bobzien_2001_chapter": "Ch. 1 + 7 (founding context)",
            "bobzien_2001_pages": "pp. 16-58 (founding doctrines) + p. 339-341 (early Stoics on eleutheria)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 treats Zeno as the founder of Stoic universal "
                "causation but credits Chrysippus with the systematic "
                "compatibilist articulation. Early Stoic freedom (eleutheria) "
                "is moral perfection, NOT freedom to do otherwise — Bobzien "
                "pp. 339-341"
            ),
        },
    },
    {
        "id": "person_epictetus_of_hierapolis_3c385bc2",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 7 dedicated chapter pp. 330-357",
            "bobzien_2001_chapter": "Ch. 7 Freedom and That Which Depends On Us: Epictetus and Early Stoics",
            "bobzien_2001_pages": "p. 330-357 (entire ch. 7)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 ch. 7 develops a contained reading of Epictetus's "
                "to_eph_hemin and eleutheria. Crucially against Frede 2011 "
                "(written later, but anticipated here): Epictetan freedom is "
                "moral self-mastery via prohairesis, NOT libertarian free will. "
                "Epictetus does not introduce the free-will problem. His "
                "two-sided ability formulations are read by Bobzien as "
                "ethical-rhetorical, not metaphysical-libertarian. Bobzien "
                "p. 333-338 + 341-343 stresses continuity with early Stoa"
            ),
        },
    },
    {
        "id": "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        "metadata_updates": {
            "bobzien_2001_treatment": "interlocutor + critical foil to Stoic position",
            "bobzien_2001_chapter": "passim — esp. Ch. 1, 3, 6 anti-Stoic arguments",
            "bobzien_2001_pages": "pp. 34-36, 102-108, 270-279, 297-301",
            "bobzien_2001_judgement": (
                "Bobzien 2001 treats Alexander as the principal late-ancient "
                "anti-Stoic interlocutor. The De Fato critiques Stoic "
                "compatibilism by reading it through a non-Stoic ontological "
                "frame, generating misunderstandings Bobzien systematically "
                "diagnoses. Crucially Alexander's two-sided to_eph_hemin = "
                "first unambiguous evidence of libertarian-style free will in "
                "antiquity (this thesis fully argued in Bobzien 1998 OSAP / "
                "Phronesis companion paper)"
            ),
        },
    },
    {
        "id": "person_carneades_214_129bce_l2m3n4o5",
        "metadata_updates": {
            "bobzien_2001_treatment": "Academic critic — Bobzien examines Cic. Fat. report of Carneades",
            "bobzien_2001_chapter": "Ch. 6 esp. §6.3.4-6.3.7",
            "bobzien_2001_pages": "p. 277-313 (Carneades on autonomous mental causation)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 treats Carneades as a key Academic interlocutor "
                "whose argument against Stoic causal determinism (via Cic. "
                "Fat. 23-25 + 31-33) sharpens the cylinder reply. Carneades's "
                "argument that voluntary mental motions need not be caused "
                "by antecedent external causes is read by Bobzien as setting "
                "the dialectical agenda for Chrysippus's compatibilist "
                "response"
            ),
        },
    },
    {
        "id": "person_diodorus_cronus_48ef6200",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 3 §3.1.2 dedicated subsection pp. 102-108",
            "bobzien_2001_chapter": "Ch. 3 Modality, Determinism, and Freedom",
            "bobzien_2001_pages": "p. 102-108 (Diodorus and necessitarianism)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §3.1.2 reconstructs Diodorus Cronus's modal "
                "system (the Master Argument, kurieuon logos) as Megaric "
                "necessitarianism — collapsing possible-but-not-actual into "
                "the impossible. Chrysippus's distinct modal system is "
                "explicitly designed to escape this Diodorean collapse while "
                "preserving causal determinism. Diodorus = the foil against "
                "which Chrysippus's compatibilism is articulated"
            ),
        },
    },
    {
        "id": "person_posidonius_apameia_135_51bce",
        "metadata_updates": {
            "bobzien_2001_treatment": "secondary figure — discussed re astrology + divination",
            "bobzien_2001_chapter": "Ch. 4 (divination) + Ch. 8 (later Stoic theory possibly related)",
            "bobzien_2001_pages": "p. 87-96, 360-370",
            "bobzien_2001_judgement": (
                "Bobzien 2001 cites Posidonius primarily through Cicero's De "
                "Divinatione, treating him as a Stoic intermediary between "
                "Chrysippus and later Stoic theory (Ch. 8 / PHILOPATOR). "
                "Bobzien is cautious about Poseidoniosforschung-style "
                "attributions; she resists reading every later innovation "
                "back into Posidonius without explicit textual warrant"
            ),
        },
    },
    {
        "id": "person_plutarch_45_120ce_b9c2a8f3",
        "metadata_updates": {
            "bobzien_2001_treatment": "principal doxographical source — De Stoic. repug. + De comm. not.",
            "bobzien_2001_chapter": "passim — esp. Ch. 1, 6",
            "bobzien_2001_pages": "p. 16-58, 234-329 passim, 324-329 (Plutarch's dilemma)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 reads Plutarch's De Stoicorum Repugnantiis and "
                "De Communibus Notitiis as the principal Middle Platonist "
                "anti-Stoic source preserving Chrysippean fragments. Plutarch "
                "constructs a dilemma (Bobzien p. 324-329) that purports to "
                "show Stoic determinism inconsistent with moral "
                "responsibility — Bobzien argues the dilemma misconstrues "
                "Chrysippean compatibilism"
            ),
        },
    },
    {
        "id": "person_origen_alexandria_185_254ce_s9t0u1v2",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 5 §5.2.2 — Origen's reply to the Idle Argument",
            "bobzien_2001_chapter": "Ch. 5 The Idle Argument (replies)",
            "bobzien_2001_pages": "p. 205-208 (Origen, Contra Celsum II.20)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §5.2.2 analyzes Origen's Contra Celsum II.20 "
                "(SC 132, 342.71-82) as one of the three key ancient replies "
                "to the argos logos (alongside Cic. Fat. 30 + Eus. PE 6.8). "
                "Origen preserves a Chrysippean refutation strategy: the "
                "actions that produce results are themselves co-fated, so "
                "fate does not render rational action otiose. Origen's "
                "Christian appropriation transforms the Stoic frame but the "
                "logical core is identifiable as a Chrysippean refutation"
            ),
        },
    },
    {
        "id": "person_frede_michael_1940_2007",
        "metadata_updates": {
            "bobzien_2001_treatment": "DPhil supervisor; central modern influence",
            "bobzien_2001_pages": "preface + 23 cross-references in main text",
            "bobzien_2001_judgement": (
                "Bobzien 2001 acknowledges Michael Frede (the late, NOT his "
                "wife Dorothea Frede) as supervisor and central methodological "
                "influence. Frede's 1980 paper 'The Original Notion of Cause' "
                "supplies the framework for Bobzien's reconstruction of Stoic "
                "causation. NOTE: existing KG node person_frede_michael_1940_2007 "
                "is mislabeled 'Dorothea Frede' but the ID indicates Michael; "
                "this metadata update points to Michael Frede"
            ),
        },
    },
    # =========================================================================
    # 4. ANCIENT WORK UPDATES — central primary sources
    # =========================================================================
    {
        "id": "work_de_fato_cicero_44bce_b9c4e5d2",
        "metadata_updates": {
            "bobzien_2001_treatment": "the single most important primary source",
            "bobzien_2001_chapter": "Ch. 3, 5, 6 passim — Cic. Fat. 28-44 central",
            "bobzien_2001_pages": "p. 199-205 (Idle Argument in Cic. Fat. 30), p. 234-329 (Ch. 6 cylinder analogy from Fat. 39-44)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 treats Cicero De Fato as the central source — "
                "esp. §§39-44 (cylinder + Chrysippus's reply to the Carneadean "
                "argument from moral responsibility) + §30 (Idle Argument). "
                "Bobzien follows Yon's Bude text + Sharples's Aris & Phillips "
                "edition + Eisenberger's German translation. Major textual + "
                "interpretive choices in pp. 256-269"
            ),
        },
    },
    {
        "id": "work_de_fato_alexander_c200ce_o6p7q8r9",
        "metadata_updates": {
            "bobzien_2001_treatment": "secondary source for anti-Stoic critique reconstruction",
            "bobzien_2001_chapter": "passim — Alexander as anti-Stoic foil",
            "bobzien_2001_pages": "p. 34-36, 270-279, 297-301",
            "bobzien_2001_judgement": (
                "Bobzien 2001 uses Alexander's De Fato selectively. Where "
                "Alexander reports Stoic positions, Bobzien checks against "
                "Cicero / Gellius / Plutarch and frequently corrects "
                "Alexander's polemical distortions. Where Alexander argues "
                "the libertarian counter-position, Bobzien reads this as "
                "first explicit evidence of two-sided to_eph_hemin"
            ),
        },
    },
    {
        "id": "work_de_divinatione_cicero",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 2 §2.2 + Ch. 4 — divination + universal regularity",
            "bobzien_2001_chapter": "Ch. 2 + Ch. 4",
            "bobzien_2001_pages": "p. 87-96, 144-179",
            "bobzien_2001_judgement": (
                "Bobzien 2001 reconstructs from Cic. Div. I.125-128 + II passim "
                "Chrysippus's argument from divination to causal determinism: "
                "since the gods know the future and divination is possible, "
                "future events must be causally fixed. Bobzien rejects "
                "simplistic readings — the argument is conditional on the "
                "premise that divination presupposes causal regularity"
            ),
        },
    },
    {
        "id": "work_gellius_na_vii_2",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 6 §6.3.1 + §6.3.3 dedicated analysis",
            "bobzien_2001_chapter": "Ch. 6 Compatibilism",
            "bobzien_2001_pages": "p. 250-269 (cylinder + cone analogy reconstruction)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §6.3.1 + §6.3.3 reconstructs Gellius NA VII.2 "
                "(De Fato et Chrysippo) as one of the two principal sources "
                "for the cylinder analogy (with Cic. Fat. 39-44). Gellius "
                "preserves Posidonius-Chrysippean transmission. Bobzien's "
                "p. 250-269 is the definitive modern reconstruction of the "
                "cylinder-cone analogy"
            ),
        },
    },
    {
        "id": "work_plutarch_de_fato_complete",
        "metadata_updates": {
            "bobzien_2001_treatment": "Middle Platonist source — limited use",
            "bobzien_2001_chapter": "Ch. 6 §6.4 (a later interpretation of Chrysippus)",
            "bobzien_2001_pages": "p. 314-329",
            "bobzien_2001_judgement": (
                "Bobzien 2001 treats Pseudo-Plutarch De Fato as a Middle "
                "Platonist source presenting a 'framework story' on "
                "Chrysippean fate. §6.4 discusses Plutarch's dilemma — "
                "Bobzien argues the dilemma rests on a misreading of "
                "Chrysippean co-fated events"
            ),
        },
    },
    {
        "id": "work_epictetus_discourses",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 7 primary source — Discourses + Enchiridion",
            "bobzien_2001_chapter": "Ch. 7 Freedom and That Which Depends On Us",
            "bobzien_2001_pages": "p. 330-357 passim",
            "bobzien_2001_judgement": (
                "Bobzien 2001 ch. 7 anchors her reading of Stoic freedom in "
                "Epictetus Discourses I.1, I.6, II.5, IV.1, IV.7 + Enchiridion "
                "1, 14, 19, 53. Epictetan eleutheria reconstructed as moral "
                "perfection achieved via prohairesis + correct use of "
                "impressions (orthōs chrōmenos tais phantasiais), NOT "
                "libertarian indeterminism"
            ),
        },
    },
    {
        "id": "work_origen_contra_celsum_sc132",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 5 §5.2.2 — anti-Idle-Argument reply",
            "bobzien_2001_chapter": "Ch. 5 The Idle Argument",
            "bobzien_2001_pages": "p. 205-208",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §5.2.2 reads Origen, Contra Celsum II.20 (SC "
                "132, 342.71-82 = Marcovich p. 95) as one of three key "
                "ancient replies to the argos logos. Origen preserves a "
                "Stoic refutation pattern via co-fated events, transposed "
                "into Christian theological frame"
            ),
        },
    },
    # =========================================================================
    # 5. ARGUMENT UPDATES — central Stoic arguments interpreted by Bobzien
    # =========================================================================
    {
        "id": "argument_cylinder_analogy_chrysippus_k1l2m3n4",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 6 §6.3.3 definitive modern reconstruction",
            "bobzien_2001_chapter": "Ch. 6 Compatibilism",
            "bobzien_2001_pages": "p. 258-271 (the cylinder and cone analogy)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §6.3.3 (p. 258-271) supplies the definitive "
                "modern reconstruction of Chrysippus's cylinder-and-cone "
                "analogy. Key moves: (a) the cylinder's roll is determined "
                "by the push (antecedent cause) + its own shape (internal "
                "nature); (b) moral responsibility attaches to the internal "
                "nature, not the push; (c) the analogy is a model of "
                "compatibilist causation, not of libertarian freedom. Sources "
                "= Cic. Fat. 39-44 + Gellius NA 7.2"
            ),
        },
    },
    {
        "id": "argument_the_lazy_argument_argos_logos_702a77ed",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 5 entire chapter dedicated",
            "bobzien_2001_chapter": "Ch. 5 Fate, Action, and Motivation: The Idle Argument",
            "bobzien_2001_pages": "p. 180-233 (entire ch. 5)",
            "bobzien_2001_judgement": (
                "Bobzien 2001 ch. 5 is the definitive modern treatment of "
                "the Idle Argument (argos logos / ignava ratio). She "
                "reconstructs: (1) the argument structure (p. 182-198); (2) "
                "the three principal ancient replies (Cic. Fat. 30 + Origen "
                "CC II.20 + Eus. PE VI.8.25-38) p. 199-216; (3) Chrysippus's "
                "co-fated events refutation (synfata) p. 217-233. Co-fated "
                "events theory dissolves the Idle Argument by showing that "
                "the actions producing results are themselves part of fate"
            ),
        },
    },
    {
        "id": "argument_the_cofated_events_argument_confatalia_b7715646",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 5 §5.3.2 dedicated analysis",
            "bobzien_2001_chapter": "Ch. 5 The Idle Argument",
            "bobzien_2001_pages": "p. 217-233",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §5.3.2 (p. 221-226) reconstructs Chrysippean "
                "co-fated events (synfata / confatalia) as the technical "
                "device dissolving the Idle Argument. The action and its "
                "outcome are not two separately fated events — they are "
                "co-fated. So 'doing X to get Y' is not rendered otiose by "
                "fate but is part of fate's causal structure"
            ),
        },
    },
    {
        "id": "argument_the_master_argument_kurieuon_logos_355f4d3f",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 3 §3.1.2 dedicated analysis (Diodorean necessitarianism)",
            "bobzien_2001_chapter": "Ch. 3 Modality",
            "bobzien_2001_pages": "p. 102-108",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §3.1.2 reconstructs the Master Argument as "
                "Diodorus Cronus's argument for necessitarianism: from "
                "(1) every past truth is necessary, (2) the impossible does "
                "not follow from the possible, infer (3) every possible is "
                "or will be true. This collapses possible-but-not-actual "
                "into the impossible. Chrysippus's modal system is "
                "explicitly designed to escape this collapse"
            ),
        },
    },
    {
        "id": "argument_sea_battle_aristotle_f6g7h8i9",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 2 §2.1 — Bivalence and future contingents",
            "bobzien_2001_chapter": "Ch. 2 Two Chrysippean Arguments for Causal Determinism",
            "bobzien_2001_pages": "p. 59-86",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §2.1 (p. 59-86) reconstructs the relation "
                "between Chrysippus's Bivalence Argument and Aristotle's "
                "sea-battle problem (De Int. 9). Chrysippus accepts "
                "unrestricted bivalence + uses it to argue from "
                "determinate-truth-values-of-future-tense-statements to "
                "causal determinism. Bobzien contrasts this with Epicurus's "
                "rejection of bivalence to preserve indeterminism (p. 75-86)"
            ),
        },
    },
    # =========================================================================
    # 6. CONCEPT UPDATES — central Stoic concepts
    # =========================================================================
    {
        "id": "concept_heimarmene_fate_stoics_j0k1l2m3",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 1 §1.4 dedicated section",
            "bobzien_2001_chapter": "Ch. 1 Determinism and Fate",
            "bobzien_2001_pages": "p. 44-58",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §1.4 (p. 44-58) reconstructs Stoic heimarmene "
                "as identical with God-Providence-Nature-Active Principle "
                "(the 'Fate Principle'). Fate is universal causal connection "
                "+ teleological order, NOT external compulsion. The "
                "principal aspects are: causal connection, pneumatic "
                "transmission, sympatheia, providence, ekpyrosis cycle"
            ),
        },
    },
    {
        "id": "concept_eph_hemin_one_sided_causative",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 6 §6.3.5 + Ch. 7 §7.1 — definitive distinction",
            "bobzien_2001_chapter": "Ch. 6 + Ch. 7",
            "bobzien_2001_pages": "p. 276-301, 331-338",
            "bobzien_2001_judgement": (
                "Bobzien 2001 establishes the canonical distinction between "
                "(a) one-sided causative to_eph_hemin = di' hemon = 'that "
                "which happens THROUGH us' (early Stoa); and (b) two-sided "
                "potestative to_eph_hemin = 'that which is up to us to do "
                "or not to do' (Alexander + later). Early Stoic eph' hemin "
                "is about causal attribution, not freedom to do otherwise. "
                "This distinction is fundamental for the entire chapter 7 "
                "argument"
            ),
        },
    },
    {
        "id": "concept_eph_hemin_two_sided_potestative",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 6 + 7 — the late development Bobzien diagnoses",
            "bobzien_2001_chapter": "Ch. 6 + 7",
            "bobzien_2001_pages": "p. 276-301, 331-338, 344-345",
            "bobzien_2001_judgement": (
                "Bobzien 2001 argues the two-sided potestative to_eph_hemin "
                "is NOT early Stoic — it emerges with Alexander of "
                "Aphrodisias and is read back anachronistically into the "
                "early Stoa by later commentators. This is Bobzien's "
                "central exegetical claim and the foundation for her 1998 "
                "OSAP paper on the late birth of the free-will problem"
            ),
        },
    },
    {
        "id": "concept_synkatathesis_stoic_assent",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 6 §6.1.2 + 6.3 — Stoic psychology of action",
            "bobzien_2001_chapter": "Ch. 6 Compatibilism",
            "bobzien_2001_pages": "p. 239-242, 258-271",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §6.1.2 (p. 239-242) reconstructs synkatathesis "
                "(assent, συγκατάθεσις) as the central Stoic concept of "
                "rational action: an impression presents itself, the "
                "rational agent assents (or withholds assent), assent "
                "produces impulse (hormē) toward action. In the cylinder "
                "analogy, assent corresponds to the internal nature — the "
                "locus of moral responsibility"
            ),
        },
    },
    {
        "id": "concept_sympatheia_stoic",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 1 §1.4 + Ch. 4 — pneumatic causation framework",
            "bobzien_2001_chapter": "Ch. 1 + Ch. 4",
            "bobzien_2001_pages": "p. 47-58, 156-170",
            "bobzien_2001_judgement": (
                "Bobzien 2001 treats sympatheia as the cosmic-physical "
                "expression of the Fate Principle: all parts of the "
                "cosmos are causally interconnected via pneumatic "
                "transmission. This grounds the universality of causation "
                "without requiring local determinism to be reductively "
                "mechanical"
            ),
        },
    },
    {
        "id": "concept_confatalia_chrysippus",
        "metadata_updates": {
            "bobzien_2001_treatment": "Ch. 5 §5.3.2 dedicated analysis",
            "bobzien_2001_chapter": "Ch. 5 The Idle Argument",
            "bobzien_2001_pages": "p. 217-233",
            "bobzien_2001_judgement": (
                "Bobzien 2001 §5.3.2 establishes confatalia / synfata as "
                "the Chrysippean technical device dissolving the Idle "
                "Argument. The action producing an outcome is co-fated "
                "with the outcome — they are not two independently fated "
                "events. So fate does not render rational deliberation "
                "and action otiose"
            ),
        },
    },
]
