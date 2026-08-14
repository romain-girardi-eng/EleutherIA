"""Authored prose rewrites for the 2026-08-14 curator-artifact cleanup.

Companion data module for `apply_2026_08_14_curation_artifact_cleanup.py`.
Each entry is a verbatim (old_span -> new_span) pair on the node's reader-facing
text; the applier requires the old span to occur exactly once and rewrites only
that span, so the transformation stays deterministic and reviewable.

Provenance of every rewrite: the node's own `[Vérif. …]` tag (quoted in the `#`
comment above the pair) or the reviewed plan line
`data/audit/2026-08-14_curation_artifact_cleanup_plan.jsonl`. No ancient-language
string appears in a new span unless it is verbatim in the node's own description
or tag — nothing in Greek, Latin or Hebrew was composed.

`[Vérif. …]` tags themselves are NOT handled here: the applier strips them and
preserves them in `metadata.verification_notes`.
"""

from __future__ import annotations

# node_id -> ((old_span, new_span), ...) applied to `description`, in order.
REWRITES: dict[str, tuple[tuple[str, str], ...]] = {
    # --- argument_adversity_exercise_seneca_g8h9i0j1 (argument, risk=high) ---
    # FLAG: Tag truncated after 'Edition numbering varies by a subsection, so'; only the
    #   2.3->2.4 relocation could be applied. The node's passage anchor (passage_sen_prov_2_3)
    #   is metadata and still needs re-pointing.
    "argument_adversity_exercise_seneca_g8h9i0j1": (
        # tag: the maxim is at De Prov 2.4 in Reynolds' OCT and Basore's Loeb, not 2.3
        (
            'The pivot is the maxim at 2.3 — "Marcet sine adversario virtus"',
            'The pivot is the maxim at 2.4 — "Marcet sine adversario virtus"',
        ),
    ),
    # --- argument_agent_causation_alex (argument, risk=medium) ---
    # FLAG: Tag flags the reference '451-460' as unidentifiable/spurious, but that page range
    #   appears nowhere in the description prose (it lives in the node's reference metadata); no
    #   prose edit was possible.
    "argument_agent_causation_alex": (
        # PLAN_ACTION: strip the leading '**Avertissement méthodologique** … *(Phase 12)*'
        #   boilerplate paragraph and its '\n\n' separator
        (
            "**Avertissement méthodologique** : la terminologie « compatibiliste / libertarienne / agent-causation / etc. » employée ci-dessous appartient au vocabulaire de la philosophie analytique moderne (Frankfurt 1969, Kane 1996, Pereboom 2001). Ces étiquettes sont rétroactivement projetées sur la pensée antique par des chercheurs modernes (Bobzien 1998, Frede 2011, Sorabji 1980) pour cartographier la position d'un auteur ancien dans le débat contemporain. Le concept ancien correspondant — ἑκούσιον, ἐφ' ἡμῖν, αὐτεξούσιον, liberum arbitrium — précède de plusieurs siècles la formation du « problème du libre arbitre » au sens analytique. Cf. Dihle 1982, *The Theory of Will in Classical Antiquity* ; Frede 2011, *A Free Will: Origins of the Notion*. *(Phase 12)*\n\n",
            "",
        ),
    ),
    # --- argument_aristotelian_legislator_practice_amand1945 (argument, risk=medium) ---
    "argument_aristotelian_legislator_practice_amand1945": (
        # PLAN_ACTION: the internal curation cross-reference 'batch B1' is dropped; the node id
        #   is what the reader needs
        (
            "`argument_carneadean_legislation_amand1945` du batch B1)",
            "`argument_carneadean_legislation_amand1945`)",
        ),
    ),
    # --- argument_bardesanes_nomima_barbarika_amplified (argument, risk=medium) ---
    # FLAG: Verbatim wording and exact page of Amand's judgement are lost; only the paraphrased
    #   attribution survives.
    "argument_bardesanes_nomima_barbarika_amplified": (
        # tag: the attributed verbatim quotation and the page 'Amand p. 243' could not be
        #   located; page + quotation marks dropped, Amand's claim kept as paraphrase
        (
            "Selon Amand p. 243, Bardesane est « peut-être le premier à avoir mis en œuvre » l'argument carnéadien des nomima barbarika « avec une telle profusion et une telle exactitude documentaire »",
            "Selon Amand, Bardesane serait l'un des premiers à mettre en œuvre l'argument carnéadien des nomima barbarika avec une profusion et une exactitude documentaires remarquables.",
        ),
    ),
    # --- argument_cafma_futility_of_effort_8c3d5f21 (argument, risk=high) ---
    "argument_cafma_futility_of_effort_8c3d5f21": (
        # tag: this is the moral/practical argument, not the ἀργὸς λόγος; Amand's argument no. 5
        #   (583-584, conjectural); witness = Alexander De Fato 21 (Bruns 191); Gellius NA VII.2
        #   is not a witness
        (
            "if the outcome is predetermined regardless of effort?",
            "if the outcome is predetermined regardless of effort? This is the moral and practical argument — belief in εἱμαρμένη produces slackening of effort, negligence and indolence — and not the lazy argument (ἀργὸς λόγος) of Cicero, De Fato 28-30, which concludes 'then do not call the doctor' and which Chrysippus rebutted with confatalia. Amand reconstructs it as argument no. 5 of the Carneadean moral anti-fatalist argumentation (Fatalisme et liberté, 583-584), while stressing that the whole reconstruction is conjectural. Its best ancient witness is Alexander of Aphrodisias, De Fato 21 (Bruns 191); Aulus Gellius NA VII.2 is Chrysippus on fate (the cylinder), not a witness to this argument.",
        ),
    ),
    # --- argument_cafma_futility_of_legislation_9d4e6g32 (argument, risk=medium) ---
    "argument_cafma_futility_of_legislation_9d4e6g32": (
        # tag: 'átopoï nómoï' / ἄτοποι νόμοι is not verbatim-attested (zero TLG E hits); it is a
        #   modern back-translation, so the gloss is removed
        (" (átopoï nómoï)", ""),
    ),
    # --- argument_cafma_futility_of_piety_2g7h9j65 (argument, risk=medium) ---
    "argument_cafma_futility_of_piety_2g7h9j65": (
        # tag: 'anóētoï euchaí' is an unattested modern back-translation, not an attested
        #   ancient term
        (" (anóētoï euchaí)", ""),
    ),
    # --- argument_carneades_autonomous_mental_causation_argument_4e7e9250 (argument, risk=medium) ---
    # FLAG: metadata.description_en still carries the parallel markers '[Wave 7 initial
    #   summary]' and '[B2 enrichment - Amand 1945, pp. 66-68, Intro SII.III.IV]'; they need the
    #   same treatment but cannot be expressed as description spans.
    "argument_carneades_autonomous_mental_causation_argument_4e7e9250": (
        # batch marker '[Wave 7 - resume initial]' carries no bibliography: deleted with its
        #   trailing space
        ("[Wave 7 — résumé initial] ", ""),
        # '[Enrichissement B2 - Amand 1945, p. 66-68, Intro SII.III.IV]' carries a real locus:
        #   converted to a normal citation attached to the sentence it documents
        (
            "[Enrichissement B2 — Amand 1945, p. 66-68, Intro §II.III.IV] Amand reconstruit la polémique antifataliste « directe » de Carnéade comme une discussion technique de la doctrine chrysippéenne de l'εἱμαρμένη.",
            "Amand reconstruit la polémique antifataliste « directe » de Carnéade comme une discussion technique de la doctrine chrysippéenne de l'εἱμαρμένη (Amand 1945, p. 66-68, Intro §II.III.IV).",
        ),
    ),
    # --- argument_causal_asymmetry_alex (argument, risk=medium) ---
    "argument_causal_asymmetry_alex": (
        # tag: the temporal modal asymmetry is a modern reconstruction, not a thesis Alexander
        #   thematizes as his own
        (
            "Alexander argues for fundamental asymmetry between past and future:",
            "Alexander's text has been read as establishing an asymmetry between past and future:",
        ),
        # tag: TLG collation shows Alexander asserts fixity of the past and non-necessitation by
        #   foreknowledge without thematizing a temporal modal asymmetry
        (
            "Conclusion: Causal relations exhibit temporal asymmetry - necessity runs backward, contingency forward",
            "Conclusion: what the text itself affirms is the fixity of the past (not even the gods can undo what has happened) and the non-necessitation of the future by divine foreknowledge; the modern formula 'necessity runs backward, contingency forward' is a reconstruction",
        ),
    ),
    # --- argument_character_change_alex (argument, risk=medium) ---
    # FLAG: The three doctrinal claims were retained but can no longer be pinned to a chapter:
    #   the tag gives no replacement loci, only the Bruns page range of the whole treatise.
    "argument_character_change_alex": (
        # tag: 'Fat. 511-512 / 513-514 / 515-517' are not valid De Fato loci — Alexander's De
        #   Fato has 39 chapters and occupies Bruns pp. 164-212; the invented line-numbers are
        #   dropped and only the edition range the tag states is kept
        (
            "Sources: Fat. 511-512: Nature contributes but doesn't necessitate; many change characters\nFat. 513-514: Bad become good through philosophy; good become bad through neglect\nFat. 515-517: We are masters of our characters through choice (habituation doctrine)",
            "Sources: Alexander, De Fato (Bruns, pp. 164-212): nature contributes to character but does not necessitate it, and many people do change their characters; the bad become good through philosophy and the good become bad through neglect; we are masters of our characters through choice (habituation doctrine)",
        ),
    ),
    # --- argument_clement_grace_synergy_assent (argument, risk=medium) ---
    # FLAG: Tag truncated before naming the alternative section, so the precise locus is lost;
    #   only 'Strom. II' is retained. The parallel locus Strom. V.13.86 was not flagged and is
    #   kept.
    "argument_clement_grace_synergy_assent": (
        # tag: the definition of pistis as synkatathesis is real but its exact section (II.2.8
        #   vs …) is unverified; drop the over-precise locus, keep book II
        (", Strom. II.2.8.4)", ", Strom. II)"),
    ),
    # --- argument_common_cause_alex (argument, risk=medium) ---
    "argument_common_cause_alex": (
        # tag: 'Only the technical label κοινὴ αἰτία is modern — 0 hits in Alexander'
        (
            "koinē aitia (common cause) is a genuine technical notion in the ancient causal-classification debate.",
            "koinē aitia (common cause) is a modern label for a notion at work in the ancient causal-classification debate; it is not Alexander's own term (no attestation in his corpus).",
        ),
        # curator-addressed '[Corrected …]' bracket converted to prose; content preserved per
        #   tag (argument attested at Bruns 195)
        (
            "[Corrected 2026-08-03 against TLG0732: the argument IS in De Fato (Bruns 195). Alexander's own wording is not κοινὴ αἰτία (0 hits anywhere in his corpus) but τὸ αὐτὸ αἴτιον",
            "The argument itself is in De Fato (Bruns 195). Alexander's own wording is τὸ αὐτὸ αἴτιον",
        ),
        # closes the converted curator bracket
        (
            "And he denies that these events are interlocked ἁλύσεως δίκην, 'after the manner of a chain'.]",
            "And he denies that these events are interlocked ἁλύσεως δίκην, 'after the manner of a chain'.",
        ),
    ),
    # --- argument_gomez_2014_chrysippus_reactive_compatibilism (argument, risk=medium) ---
    # FLAG: Contributor name and page range removed as unconfirmed; the tag is truncated after
    #   naming Gourinat as a verified contributor, so the correct attribution could not be
    #   recovered.
    "argument_gomez_2014_chrysippus_reactive_compatibilism": (
        # tag: the attribution of a chapter to a contributor named 'Gomez' in Destree 2014 could
        #   not be confirmed
        (
            "Argument scholarly de Laura Liliana Gómez, « Chrysippean compatibilistic theory of fate, what is up to us, and moral responsibility », in Destrée/Salles/Zingano (éd.), What is Up to Us? (Academia Verlag 2014), p. 121-140 : la",
            "Argument scholarly issu du volume Destrée/Salles/Zingano (éd.), What is Up to Us? (Academia Verlag 2014), sur la théorie chrysippéenne du destin, de ce qui dépend de nous et de la responsabilité morale, dont l'auteur du chapitre n'a pu être confirmé : la",
        ),
    ),
    # --- argument_human_dignity_alex (argument, risk=medium) ---
    # FLAG: The tag's actual target is metadata.sources, which still lists passage ids
    #   passage_alex_fat_628/629/633-636; that cannot be fixed by a description edit and remains
    #   open.
    "argument_human_dignity_alex": (
        # tag: the Bruns loci 'Fat. 628-636' are fabricated; the curator-addressed bracket
        #   naming them is converted to plain prose keeping only the real fact (Bruns SA 2.2
        #   ends at p. 212)
        (
            " [Specific Bruns/chapter loci 'Fat. 628-636' removed as fabricated: De Fato in Bruns SA 2.2 ends at p. 212.]",
            " (De Fato in Bruns SA 2.2 ends at p. 212; page-loci beyond that point are spurious.)",
        ),
    ),
    # --- argument_irenaeus_recapitulation_theodicy (argument, risk=medium) ---
    # FLAG: The removal of '(ἀνακεφαλαιόω)' goes one step beyond the explicitly enumerated
    #   unattested strings: tag #2 generalises to all Greek forms in the node, and Book III has
    #   no Greek transmission, but that particular word was not individually listed as a TLG
    #   miss. The English 'recapitulates' still carries the doctrine.
    "argument_irenaeus_recapitulation_theodicy": (
        # PLAN_ACTION: strip the 'Avertissement conceptuel' boilerplate + '(Phase 12)' marker;
        #   it is factually wrong (misattributes to Dihle 1982 the location of the 'invention of
        #   free will' in Origen) and states a contested modern paradigm as fact
        (
            "**Avertissement conceptuel — anachronisme du « libre arbitre »** : la catégorie de « libre arbitre » (αὐτεξούσιον / liberum arbitrium) est, selon la thèse classique de Dihle 1982 — confirmée et nuancée par Bobzien 1998, Frede 2011, Fürst 2022 — une invention dogmatique chrétienne datant d'Origène (vers 230-250 ap. J.-C.). Les concepts anciens antérieurs — ἑκούσιον (volontaire) chez Aristote, ἐφ' ἡμῖν (ce qui dépend de nous) chez les Stoïciens et Académiques, voluntas libera chez Cicéron — recouvrent un champ conceptuel partiel et non-substitutif. Lorsque la présente description emploie « libre arbitre » / « free will » de manière apparemment naïve, il faut entendre une approximation lexicale moderne ; pour le contenu doctrinal exact de l'auteur ancien, voir le terme grec/latin propre. *(Phase 12)*\n\n",
            "",
        ),
        # tags: 'τὴν ἀσθένειαν τοῦ ἀνθρώπου' is unattested in Irenaeus (0 occurrences, TLG1447);
        #   it only appears in Ps.-Macarius. Book III survives whole only in Latin, so this is a
        #   retroversion presented as a quotation
        (" (τὴν ἀσθένειαν τοῦ ἀνθρώπου)", ""),
        # tag TLG1447: 'les formules grecques de ce nœud ne sont pas attestées chez Irénée — ce
        #   sont des rétroversions'; Book III is transmitted only in the old Latin version, so
        #   no Greek word-form can be quoted from it
        (" (ἀνακεφαλαιόω)", ""),
    ),
    # --- argument_lazy_argument_alex (argument, risk=medium) ---
    # FLAG: Page anchors lost: the tag says the given Bruns pages are impossible but does not
    #   supply the correct ones. The node label ('Lazy Argument (Argos Logos) in Alexander')
    #   still carries the conflation flagged by the tag.
    "argument_lazy_argument_alex": (
        # tag: mislabel/conflation - the 'Lazy Argument' (argos logos) is a fatalist sophism,
        #   not this pragmatic consequences-of-determinism argument
        ("Argument: THE LAZY Argument (ἈΡΓῸΣ ΛΌΓΟΣ) ", "Argument: "),
        # tag: 'Fat. 260/265/267/268/284' fall outside the pagination of Alexander's De Fato
        #   (pp. 164-212 Bruns), so the page anchors are removed while the claims are kept
        (
            'Fat. 265: Choose "pleasures with ease" since outcomes are fixed. Fat. 267: "Neglect of the noble by all". Fat. 268: Noble things require toil; vices come easily. Fat. 260: "Confusing and overturning human life". Fat. 284: "Cause of the overthrow of all human life".',
            'In De Fato Alexander spells out these consequences: choosing "pleasures with ease" since outcomes are fixed; the "Neglect of the noble by all"; noble things requiring toil while vices come easily; determinism as "Confusing and overturning human life" and as the "Cause of the overthrow of all human life".',
        ),
    ),
    # --- argument_nemesius_nat_hom_37_38_middle_platonism_critique_amand1945 (argument, risk=medium) ---
    "argument_nemesius_nat_hom_37_38_middle_platonism_critique_amand1945": (
        # tag: the biblical proofs 'Joshua halting the sun, Enoch and Elijah preserved alive'
        #   could not be confirmed in Nemesius (TLG search of tlg0743)
        (" (arrêt du soleil par Josué, conservation en vie d'Énoch et Élie)", ""),
    ),
    # --- argument_origen_anti_astrological (argument, risk=high) ---
    "argument_origen_anti_astrological": (
        # tag: the anti-astrological arguments belong to Comm. in Gen. III / Philocalia 23, NOT
        #   to De Principiis
        (
            "in De Principiis III.1.5-6 and the Commentary on Genesis (fragments in Philocalia ch. 23):",
            "in the Commentary on Genesis III (fragments in Philocalia ch. 23):",
        ),
    ),
    # --- argument_origen_argos_logos (argument, risk=high) ---
    # FLAG: Tag truncated mid-word ('the same presci'); the corrected characterization was
    #   recoverable, but the tag's further point about where the argos logos refutation proper
    #   is located was lost. The French header still lists Contra Celsum II.20 as source
    #   primaire and was left untouched.
    "argument_origen_argos_logos": (
        # tag: characterization slippage — II.20 is the 'foreknowledge/prophecy does not
        #   necessitate' passage (Judas), not a reply to a charge that prayer and effort are
        #   futile
        (
            "In Contra Celsum II.20, Origen addresses Celsus's charge that Christian prayer and moral effort are futile if God's will is sovereign.",
            "Contra Celsum II.20 is primarily the passage on foreknowledge and prophecy: Jesus's prediction of Judas's betrayal does not compel the betrayal, so what is foreknown is not thereby necessitated.",
        ),
    ),
    # --- argument_origen_prescience_causality (argument, risk=medium) ---
    # FLAG: The spurious Sources Chrétiennes edition tag for De Oratione flagged by the [Vérif.]
    #   note is in the node's edition metadata, not in the prose: the only SC reference in the
    #   description (SC 543) belongs to the Commentary on Romans and is untouched by the tag.
    "argument_origen_prescience_causality": (
        # PLAN_ACTION: strip the leading '**Avertissement méthodologique** … *(Phase 12)*'
        #   boilerplate paragraph and its '\n\n' separator
        (
            "**Avertissement méthodologique** : la terminologie « compatibiliste / libertarienne / agent-causation / etc. » employée ci-dessous appartient au vocabulaire de la philosophie analytique moderne (Frankfurt 1969, Kane 1996, Pereboom 2001). Ces étiquettes sont rétroactivement projetées sur la pensée antique par des chercheurs modernes (Bobzien 1998, Frede 2011, Sorabji 1980) pour cartographier la position d'un auteur ancien dans le débat contemporain. Le concept ancien correspondant — ἑκούσιον, ἐφ' ἡμῖν, αὐτεξούσιον, liberum arbitrium — précède de plusieurs siècles la formation du « problème du libre arbitre » au sens analytique. Cf. Dihle 1982, *The Theory of Will in Classical Antiquity* ; Frede 2011, *A Free Will: Origins of the Notion*. *(Phase 12)*\n\n",
            "",
        ),
    ),
    # --- argument_plutarch_providence_cooperation_8c5a9d3f (argument, risk=high) ---
    # FLAG: Tag truncated at 'De Sera Numinis Vindicta and De St'; whatever it stated about
    #   those authentic works could not be recovered and is not reflected.
    "argument_plutarch_providence_cooperation_8c5a9d3f": (
        # tag: the tripartite-providence doctrine occurs only in the pseudonymous De Fato, so
        #   the 'Plutarch' attribution is wrong
        (
            "Developed to reconcile divine providence with human freedom.",
            "Developed in the pseudonymous De Fato, whose author is conventionally designated Pseudo-Plutarch rather than Plutarch, to reconcile divine providence with human freedom.",
        ),
    ),
    # --- argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945 (argument, risk=high) ---
    "argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945": (
        # tag: RESERVE D'ATTRIBUTION - Amand attributes Discourse V to Chrysostom himself and
        #   CPG 4367 counts the six discourses among the authentic works; the 'Pseudo-
        #   Chrysostome' label is a modern editorial decision
        (
            "εἰπέ μοι; »",
            "εἰπέ μοι; » Réserve d'attribution : Amand intitule son chapitre « Jean Chrysostome » et attribue le Discours V à Chrysostome lui-même (avec un point d'interrogation), et le CPG 4367 range les six discours De fato et prouidentia parmi les œuvres authentiques ; l'étiquette « Pseudo-Chrysostome » retenue ici est donc une décision éditoriale moderne, non celle d'Amand.",
        ),
    ),
    # --- argument_pseudo_chrysostom_de_fato_v_witness6_amand1945 (argument, risk=medium) ---
    # FLAG: The sub-page spans for the French translation and the Greek text are lost; only the
    #   overall span p. 519-532 (already in the prose) is retained.
    "argument_pseudo_chrysostom_de_fato_v_witness6_amand1945": (
        # tag: the internal sub-spans for the translation and the Greek are mutually
        #   inconsistent with the recorded page range p. 519-532
        (
            "Amand publie d'abord la traduction française intégrale (p. 520-527), puis le texte grec original d'après Montfaucon (p. 527-532).",
            "Amand publie d'abord la traduction française intégrale, puis le texte grec original d'après Montfaucon (l'ensemble p. 519-532).",
        ),
    ),
    # --- argument_qumran_predestination_c3d4e5f6 (argument, risk=high) ---
    "argument_qumran_predestination_c3d4e5f6": (
        # tag: Frey's essay on modified Qumran dualism is 'Different Patterns of Dualistic
        #   Thought in the Qumran Library' (1997, STDJ 23), not 1999
        ("Jörg Frey (1999) contends", "Jörg Frey (1997) contends"),
    ),
    # --- argument_regret_alex (argument, risk=medium) ---
    "argument_regret_alex": (
        # tag: the 'early version of the Consequence Argument' framing is a loose analogy only;
        #   van Inwagen's argument is a modal transfer argument
        (
            'This is an early version of what Peter van Inwagen calls the "Consequence Argument" - if',
            'It is only loosely analogous to what Peter van Inwagen calls the "Consequence Argument", which is a modal transfer argument: if',
        ),
    ),
    # --- argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus (argument, risk=medium) ---
    "argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus": (
        # tag: the chapter number 'ch. 11' could not be confirmed and should be treated as
        #   unverified
        ("(Destrée 2014 ch. 11)", "(Destrée 2014)"),
    ),
    # --- argument_saving_teaching_alex (argument, risk=medium) ---
    # FLAG: tag concerns a metadata inconsistency (conclusion.primary_sources / locus_classicus
    #   point to passage_alex_fat_31 while the sources list gives passage_alex_fat_16); nothing
    #   to fix in the description prose
    "argument_saving_teaching_alex": (
        # curator changelog bracket converted to plain prose, keeping the real bibliographic
        #   fact
        (
            " [Corrected 2026-06-14: prior 'Fat. 651-659' refs are non-existent — De Fato has 39 chapters / Bruns pp. 164-212.]",
            " (De Fato comprises 39 chapters, Bruns pp. 164-212.)",
        ),
    ),
    # --- argument_skeptical_argument_from_divine_power_d217cdac (argument, risk=medium) ---
    # FLAG: Tag's main object is the grounding of every premise to work_bayle_rorarius_1702
    #   (metadata); in the prose the only fix available was to stop presenting 'Rorarius' as the
    #   locus of the argument. Tag is truncated, so the correct locus could not be substituted.
    "argument_skeptical_argument_from_divine_power_d217cdac": (
        # tag: 'Rorarius' is Bayle's article on animal souls / occasionalism / Leibniz, and is
        #   NOT where the omnipotence argument stands
        (
            '"Rorarius" (animal souls and human freedom)',
            '"Rorarius" (animal souls, occasionalism and Leibniz — not the locus of the divine-omnipotence argument)',
        ),
    ),
    # --- argument_spontaneity_within_determination_13fcd224 (argument, risk=high) ---
    # FLAG: The tag's REMAINING item (per-premise primary_sources of P1-P3 and P8-P10 still
    #   pointing at work_leibniz_theodicee_1710 for want of Spinoza/Hume work nodes) is
    #   metadata-level and cannot be fixed in prose.
    "argument_spontaneity_within_determination_13fcd224": (
        # tag: a single formulator misrepresents a synthetic argument (P1-P3 Spinoza, P4-P7
        #   Leibniz, P8-P10 Hume)
        (
            "Prominent in Spinoza, Leibniz, and Hume.",
            "Prominent in Spinoza, Leibniz, and Hume; as set out here the argument is a composite whose opening definitional premises are Spinoza's, its middle premises Leibniz's, and its closing premises Hume's.",
        ),
        # tag: correct grounding for the opening premises is Ethica I, Def. 7; I, Prop. 17, Cor.
        #   2; III, Prop. 1-3
        (
            "Key texts: Spinoza, Ethics I, Def. 7; III, Prop. 2;",
            "Key texts: Spinoza, Ethics I, Def. 7; I, Prop. 17, Cor. 2; III, Prop. 1-3;",
        ),
    ),
    # --- argument_tatian_freewill_paradox (argument, risk=high) ---
    "argument_tatian_freewill_paradox": (
        # PLAN_ACTION: strip the 'Avertissement conceptuel ... *(Phase 12)*' boilerplate +
        #   following blank line; the tag confirms it misattributes to Dihle 1982 the location
        #   of the invention of will in Origen (Dihle locates it in Augustine)
        (
            "**Avertissement conceptuel — anachronisme du « libre arbitre »** : la catégorie de « libre arbitre » (αὐτεξούσιον / liberum arbitrium) est, selon la thèse classique de Dihle 1982 — confirmée et nuancée par Bobzien 1998, Frede 2011, Fürst 2022 — une invention dogmatique chrétienne datant d'Origène (vers 230-250 ap. J.-C.). Les concepts anciens antérieurs — ἑκούσιον (volontaire) chez Aristote, ἐφ' ἡμῖν (ce qui dépend de nous) chez les Stoïciens et Académiques, voluntas libera chez Cicéron — recouvrent un champ conceptuel partiel et non-substitutif. Lorsque la présente description emploie « libre arbitre » / « free will » de manière apparemment naïve, il faut entendre une approximation lexicale moderne ; pour le contenu doctrinal exact de l'auteur ancien, voir le terme grec/latin propre. *(Phase 12)*\n\n",
            "",
        ),
    ),
    # --- argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will (argument, risk=medium) ---
    # FLAG: The tag also doubts whether Wildberg authored a chapter in Destrée-Salles-Zingano
    #   2014 at all; the attribution is only hedged ('attribué à'), not removed, since the tag
    #   is truncated and does not settle it.
    "argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will": (
        # tag: 'ch. 21' could not be confirmed against the volume; the chapter number is dropped
        #   and the attribution hedged
        (
            "Argument scholarly de Wildberg (Destrée 2014 ch. 21) :",
            "Argument scholarly attribué à Wildberg (Destrée 2014, chapitre non identifié) :",
        ),
    ),
    # --- collection_ls (source_collection, risk=medium) ---
    # FLAG: Both doubtful section numbers removed rather than corrected: the tag is truncated
    #   before giving the right LS numbers.
    "collection_ls": (
        # tag: '57 (impulsion et oikeiôsis) et 65 (passions)' is inconsistent with the printed
        #   LS volume and cannot be confirmed
        ("57 (impulsion et oikeiôsis) et 65 (passions), ", ""),
    ),
    # --- concept_acting_final_cause (concept, risk=medium) ---
    # FLAG: tag asks that a Clement locus (Strom. I.17.81-87; VI.17.157-162) and an exact
    #   secondary reference be supplied before the label is treated as sourced
    "concept_acting_final_cause": (
        # tag: 'Jourdan 2011' untraceable and 'cause finale agissante' is not an ancient term;
        #   curator-addressed 'formerly given here / has been withdrawn' framing removed
        (
            "Clement's innovation (modern interpretative label; the attribution formerly given here as 'Jourdan 2011' could not be traced to any publication and has been withdrawn):",
            "Clement's innovation (a modern interpretative label, not a term of Clement's own, and as yet without an established secondary source):",
        ),
    ),
    # --- concept_autexousion_pe_vi_6_eusebius (concept, risk=medium) ---
    "concept_autexousion_pe_vi_6_eusebius": (
        # tag: the quoted sentence (PE VI.6.21) is given only in translation and could not be
        #   verbatim-located
        (
            "au même titre que la sensation : 'Elle est donc évidente",
            "au même titre que la sensation. La citation n'est ici disponible qu'en traduction, le texte grec correspondant n'ayant pu être collationné : 'Elle est donc évidente",
        ),
    ),
    # --- concept_axia_biblos_tou_theou_origen_amand1945 (concept, risk=high) ---
    "concept_axia_biblos_tou_theou_origen_amand1945": (
        # tag: the stored note wrongly called the phrase unattested; it IS attested in Origen
        #   (TLG2042, Philocalia 23)
        (
            "(the signs of God). Amand",
            "(the signs of God), a phrase attested in Origen (TLG2042, Philocalia 23). Amand",
        ),
    ),
    # --- concept_bechirah_c1d2e3f4 (concept, risk=high) ---
    "concept_bechirah_c1d2e3f4": (
        # tag: Maimonides writes reshut (רשות) at Hilkhot Teshuvah 5:1; 'bechirah ḥofshit' is a
        #   modern label, not his own wording
        (
            'where bechirah ḥofshit ("free choice") is declared a foundational principle',
            'where free choice — Maimonides\' own term in Hilkhot Teshuvah 5:1 is reshut (רשות, "permission/authority"), "bechirah ḥofshit" being the standard modern-Hebrew label rather than his ipsissima verba — is declared a foundational principle',
        ),
    ),
    # --- concept_belial_demonic_source_of_sin (concept, risk=high) ---
    # FLAG: The tag's actual target is the top-level `period` field ('Late Antiquity'), which
    #   prose edits cannot reach; the correct dating was written into the description so the
    #   reader is not misled.
    "concept_belial_demonic_source_of_sin": (
        # tag: chronology miscoded as 'Late Antiquity'; Belial in CD, 1QM and 1QS is Second
        #   Temple / Hellenistic, 2nd c. BCE-1st c. CE — the dating is now carried by the prose
        #   itself
        (
            "much Second Temple sectarian literature, presented as",
            "much Second Temple sectarian literature (the Qumran sectarian scrolls CD, 1QM, 1QS: 2nd c. BCE-1st c. CE), presented as",
        ),
    ),
    # --- concept_bondage_of_will_1c5x6y24 (concept, risk=high) ---
    "concept_bondage_of_will_1c5x6y24": (
        # tag: 'irresistible grace' is TULIP/later-Reformed vocabulary; Luther speaks of the
        #   enslaved will freed by grace
        (
            "predestination and irresistible grace.",
            "predestination and the grace that alone frees the enslaved will.",
        ),
    ),
    # --- concept_boule_practical_wisdom (concept, risk=high) ---
    "concept_boule_practical_wisdom": (
        # tag: the βουλευτικόν/ἐπιστημονικόν division is primarily NE VI.1 (1139a11-15), not the
        #   Magna Moralia
        (
            "The Magna Moralia divides the rational soul",
            "NE VI.1 (1139a11-15) divides the rational soul",
        ),
    ),
    # --- concept_carneadean_probabilism_amand1945 (concept, risk=medium) ---
    # FLAG: precise chapter/page dropped: description said 'p. 65, Intro §II ch. III §III',
    #   metadata.amand_location says 'Introduction §II Ch. II, p. 41-58'; the tag is truncated
    #   before resolving which is correct
    "concept_carneadean_probabilism_amand1945": (
        # tag: the precise locus 'p. 65, Intro §II ch. III §III' conflicts with
        #   metadata.amand_location; wrong precision dropped
        (
            "Key concept identified by Amand (1945, p. 65, Intro §II ch. III §III) under the title",
            "Key concept identified by Amand (1945, Introduction §II) under the title",
        ),
    ),
    # --- concept_causal_asymmetry_alex (concept, risk=medium) ---
    "concept_causal_asymmetry_alex": (
        # PLAN_ACTION: strip the '**Avertissement méthodologique** … *(Phase 12)*' boilerplate
        #   paragraph with its separator
        (
            "**Avertissement méthodologique** : la terminologie « compatibiliste / libertarienne / agent-causation / etc. » employée ci-dessous appartient au vocabulaire de la philosophie analytique moderne (Frankfurt 1969, Kane 1996, Pereboom 2001). Ces étiquettes sont rétroactivement projetées sur la pensée antique par des chercheurs modernes (Bobzien 1998, Frede 2011, Sorabji 1980) pour cartographier la position d'un auteur ancien dans le débat contemporain. Le concept ancien correspondant — ἑκούσιον, ἐφ' ἡμῖν, αὐτεξούσιον, liberum arbitrium — précède de plusieurs siècles la formation du « problème du libre arbitre » au sens analytique. Cf. Dihle 1982, *The Theory of Will in Classical Antiquity* ; Frede 2011, *A Free Will: Origins of the Notion*. *(Phase 12)*\n\n",
            "",
        ),
        # tag: the 'backward necessity / forward contingency' doctrine with the Socrates-
        #   Sophroniscus and building-foundation examples reads as a modern reconstruction, not
        #   verbatim Alexander
        (
            "Alexander's doctrine that causal necessity operates asymmetrically across time:",
            "The 'backward necessity / forward contingency' formulation is a modern formalization rather than Alexander's own terminology; on this reading, causal necessity operates asymmetrically across time:",
        ),
    ),
    # --- concept_concupiscence_epithumia_transmitted_bd8e2fc9 (concept, risk=high) ---
    # FLAG: The flagged Greek phrase and its gloss 'stains of wickedness' do not occur in the
    #   description prose (they sit in metadata greek_quotes), so the spurious-reference removal
    #   has no prose target.
    "concept_concupiscence_epithumia_transmitted_bd8e2fc9": (
        # tag #125: epithumia is not Methodius' technical term for a transmitted post-lapsarian
        #   desire, only a modern label
        (
            "non culpabilité héritée.",
            "non culpabilité héritée ; le terme grec est toutefois une étiquette moderne et non un terme technique de l'auteur.",
        ),
        # tag #125: the hamartiological doctrine is transmitted through De resurrectione, not De
        #   autexousio
        (
            "Methodius distinguishes inherited consequence from inherited culpability.",
            "Methodius distinguishes inherited consequence from inherited culpability; the doctrine is carried by De resurrectione (Slavonic with Greek fragments) rather than by De autexousio.",
        ),
    ),
    # --- concept_conditional_fate_9a5c8b4d (concept, risk=high) ---
    # FLAG: The flagged Greek term lives in the node's greek_term / citation_corrected metadata,
    #   not in the prose; the correction was added to the prose so it survives tag removal.
    "concept_conditional_fate_9a5c8b4d": (
        # PLAN_ACTION: strip the 'Avertissement conceptuel ... *(Phase 12)*' boilerplate +
        #   following blank line
        (
            "**Avertissement conceptuel — anachronisme du « libre arbitre »** : la catégorie de « libre arbitre » (αὐτεξούσιον / liberum arbitrium) est, selon la thèse classique de Dihle 1982 — confirmée et nuancée par Bobzien 1998, Frede 2011, Fürst 2022 — une invention dogmatique chrétienne datant d'Origène (vers 230-250 ap. J.-C.). Les concepts anciens antérieurs — ἑκούσιον (volontaire) chez Aristote, ἐφ' ἡμῖν (ce qui dépend de nous) chez les Stoïciens et Académiques, voluntas libera chez Cicéron — recouvrent un champ conceptuel partiel et non-substitutif. Lorsque la présente description emploie « libre arbitre » / « free will » de manière apparemment naïve, il faut entendre une approximation lexicale moderne ; pour le contenu doctrinal exact de l'auteur ancien, voir le terme grec/latin propre. *(Phase 12)*\n\n",
            "",
        ),
        # tags: the head Greek phrase is a modern reconstruction (0 TLG hits); the attested term
        #   is ex hypotheseos applied to heimarmene by [Plutarch], De fato 570B-C, so the prose
        #   now carries the attested form
        (
            "Reconciles fate with free will by making outcomes dependent on free choices.",
            "Reconciles fate with free will by making outcomes dependent on free choices. The compressed form 'εἱμαρμένη ἐξ ὑποθέσεως' is a modern shorthand and is not attested verbatim; the ancient term is ἐξ ὑποθέσεως, applied to εἱμαρμένη by Ps.-Plutarch, De fato 570B-C.",
        ),
    ),
    # --- concept_eleutheron_kai_autexousion (concept, risk=medium) ---
    "concept_eleutheron_kai_autexousion": (
        # tag: the Greek attributed to Irenaeus, Demonstratio 11 is a modern retroversion
        #   presented as ancient Greek; the quoted Greek is therefore removed from the Irenaeus
        #   attribution
        (
            "Repeated by Irenaeus (Dem. 11): ἐλεύθερον καὶ αὐτεξούσιον.",
            "The same pairing is echoed by Irenaeus (Dem. 11), but the Greek given for that passage is a modern retroversion, not transmitted Greek text.",
        ),
    ),
    # --- concept_fate_principle_bobzien (concept, risk=medium) ---
    # FLAG: the node label still carries '(Bobzien 2001 §1.4.4)' — unconfirmable locus, outside
    #   the description field
    "concept_fate_principle_bobzien": (
        # tag: '§1.4.4 (p. 56-58)' could not be confirmed (§1.4.4 is ch. 1, p. 56-58 is ch. 2);
        #   substantive attribution to Bobzien retained
        (
            "Formule technique introduite par Bobzien 2001 §1.4.4 (p. 56-58) pour designer",
            "Formule technique introduite par Bobzien 2001 pour designer",
        ),
        # sentence ended mid-air before the stripped tag; final stop added
        ("une modification anti-stoicienne", "une modification anti-stoicienne."),
    ),
    # --- concept_fortuna_boethius_j5k6l7m8 (concept, risk=medium) ---
    # FLAG: Tag is truncated mid-sentence, so no corrected phrase or locus was recoverable; the
    #   whole unverified bullet was dropped rather than kept with a wrong locus.
    "concept_fortuna_boethius_j5k6l7m8": (
        # tag: the phrase 'inconstantia mea' and its locus 'II.1.10' could not be verified; the
        #   rest of the entry (wheel quotation, mutability, external goods, beatitudo) is
        #   confirmed correct
        ('\n• "inconstantia mea" - Fortune\'s inconstancy (II.1.10)', ""),
    ),
    # --- concept_frede_inner_life_late_stoic (concept, risk=medium) ---
    # FLAG: Tag truncated at 'Chapter numbers' - any correction to the Frede chapter/page loci
    #   (Ch. 5 §1 p. 75-79, Ch. 3 p. 44-48, Ch. 9 p. 158-159) is not recoverable and was left as
    #   is.
    "concept_frede_inner_life_late_stoic": (
        # tag: Diss. 1.29.1 is the right locus but the paraphrase is looser than the actual 'the
        #   essence of the good is a certain prohairesis'
        (
            "(Diss. 1.29.1 : 'c'est ce qui te définit comme personne')",
            "(Diss. 1.29.1, où l'essence du bien est identifiée à une certaine prohairesis ; 'c'est ce qui te définit comme personne' est une paraphrase plus large)",
        ),
    ),
    # --- concept_freiheitsmetaphysik_origenian (concept, risk=medium) ---
    "concept_freiheitsmetaphysik_origenian": (
        # tag: the verbatim German quotation and the page reference p. 254 could not be located
        (
            "(« Der Mensch verfügt nicht nur über Freiheit; er ist Freiheit », Fürst p. 254)",
            "(Fürst 2022)",
        ),
        # tag: the 'gigantisches Netzwerk von Freiheiten' image was not located at p. 292;
        #   quotation marks and page dropped, claim kept as paraphrase
        (
            "« gigantesque réseau de libertés s'interagissant constamment » (Fürst p. 292)",
            "un gigantesque réseau de libertés en interaction constante (Fürst 2022)",
        ),
    ),
    # --- concept_gnomic_will_gnome (concept, risk=high) ---
    # FLAG: The tag is truncated at 'The co…', so whether the figure '28' is itself correct
    #   could not be recovered; the count was dropped rather than moved to the new locus.
    "concept_gnomic_will_gnome": (
        # tag: the enumeration is in Opusculum 14 (PG 91:151C–153A); attaching it to Disp. Pyrr.
        #   PG 91:312B–C is a mislocated locus
        (
            "Maximus claims to distinguish 28 senses of γνώμη in Scripture and the Fathers (Disp. Pyrr., PG 91:312B–C).",
            "Maximus sets out the many senses of γνώμη in Scripture and the Fathers chiefly in Opusculum 14 (PG 91:151C–153A).",
        ),
    ),
    # --- concept_gratia_operans (concept, risk=medium) ---
    # FLAG: The other flagged item, the Greek back-translation χάρις ἐνεργοῦσα, does not occur
    #   in the description (it is stored elsewhere in the node) and so could not be removed
    #   here.
    "concept_gratia_operans": (
        # tag: 'Deus operatur in homine sine homine' is not a verbatim Augustinian quotation
        #   with an identifiable locus; it reads as a scholastic-style axiom
        (" (Deus operatur in homine sine homine)", ""),
    ),
    # --- concept_heimarmene_conditional_amand1945 (concept, risk=high) ---
    "concept_heimarmene_conditional_amand1945": (
        # tag: the Didaskalikos is now generally ascribed to Alcinous rather than Albinus
        #   (Whittaker 1990); Amand's identification is kept as such
        (
            "and its parallel in Albinus, Didaskalikos ch. 26",
            "and its parallel in the Didaskalikos ch. 26 (ascribed to Albinus by Amand 1945, but now generally attributed to Alcinous, Whittaker 1990)",
        ),
    ),
    # --- concept_hypothetical_fate_middle_platonist (concept, risk=high) ---
    "concept_hypothetical_fate_middle_platonist": (
        # tag: ps.-Plutarch's De Fato begins at Stephanus 568B, not 568A (568A closes the
        #   preceding treatise)
        ("De Fato 568A-574F", "De Fato 568B-574F"),
    ),
    # --- concept_inner_freedom_alex (concept, risk=medium) ---
    # FLAG: The tag's flagged string 'Epictetus, Diss. I.1.7-13; I.9.12-17; Ench. 1' is
    #   unidentifiable only as an *Alexander De Fato* reference; in the prose these are genuine
    #   Epictetus loci carrying verbatim quoted Greek, so they were kept and only the corrupted
    #   work-name substitutions were repaired.
    "concept_inner_freedom_alex": (
        # tag: the motif is a Stoic/Epictetan topos, not a documented argument of Alexander's;
        #   the botched work-name substitution left the clause unreadable
        (
            "(no verbatim Greek formulation attested in the Epictetus, Dissertationes / Encheiridion (Stoic topos) — NOT Alexander, De Fato)",
            "(no verbatim Greek formulation attested in Alexander's De Fato; the motif is a Stoic topos at home in Epictetus, Dissertationes / Encheiridion)",
        ),
        # same botched work-name substitution: the TLG0732 check concerns Alexander's De Fato
        (
            "anywhere in Alexander's Epictetus, Dissertationes / Encheiridion (Stoic topos) — NOT Alexander, De Fato (TLG0732 verified 2026-08-03).",
            "anywhere in Alexander's De Fato (TLG0732 verified 2026-08-03).",
        ),
    ),
    # --- concept_metriopatheia_moderation_passions (concept, risk=high) ---
    "concept_metriopatheia_moderation_passions": (
        # curator-addressed framing ('has been removed'): the tag records the deletion of the
        #   unattested ἐθισμὸς ἄλογος, so the reader-facing text only needs Galen's attested ἡ
        #   ἄλογος δύναμις
        (
            "(Galen's term is ἡ ἄλογος δύναμις, PHP; the phrase ἐθισμὸς ἄλογος is unattested in Greek and has been removed)",
            "(Galen's term for it is ἡ ἄλογος δύναμις, PHP)",
        ),
        # tag: « le renvoi 'PHP 5.6, fr. 161 EK' reste à vérifier sur De Lacy (CMG V.4.1.2) et
        #   sur Edelstein–Kidd II »
        (
            "According to Galen's reports (PHP 5.6, Fragment 161 EK), Posidonius taught",
            "According to Galen's reports (PHP 5.6, Fragment 161 EK — reference still to be checked against De Lacy, CMG V.4.1.2, and Edelstein-Kidd II), Posidonius taught",
        ),
    ),
    # --- concept_non_necessitating_cause_alex (concept, risk=medium) ---
    # FLAG: Neither flagged item ('459-462' and the Greek formula) occurs in the description
    #   prose - both sit in the label/metadata - so instead of a deletion the description now
    #   states explicitly that the Greek formula is a modern reconstruction. The Greek string is
    #   copied verbatim from the tags.
    "concept_non_necessitating_cause_alex": (
        # tags: the Greek formula is a modern back-translation unattested in Alexander (the stem
        #   is absent from the De fato), though the distinction remains a defensible reading
        (
            "Causation is broader than determination.",
            'Causation is broader than determination. The Greek formula "αἴτιον οὐκ ἀναγκαστικόν" attached to this distinction is a modern scholarly reconstruction, not Alexander\'s own vocabulary; the conceptual distinction itself remains defensible as a reading of his De Fato.',
        ),
    ),
    # --- concept_occasionalism_a5b6c7d8 (concept, risk=high) ---
    # FLAG: The real error is the node's period field ('Early Modern'), which cannot be fixed
    #   from the description; the prose now dates the Ash'arite strand explicitly.
    "concept_occasionalism_a5b6c7d8": (
        # tag: the Ash'arite strand is medieval (al-Ash'arī d.936, al-Ghazālī d.1111), which the
        #   period label 'Early Modern' obscures
        ("(Al-Ash'ari, Al-Ghazali)", "(Al-Ash'ari, d. 936; Al-Ghazali, d. 1111)"),
    ),
    # --- concept_olympic_paradigm_positive_embodiment (concept, risk=medium) ---
    # FLAG: the tag's other point ('Presocratic' is a loose period tag for Olympian religion,
    #   which is archaic) concerns metadata.period, not the description
    "concept_olympic_paradigm_positive_embodiment": (
        # tag: 'Olympic paradigm' is a modern heuristic, not an ancient technical term
        (
            "The view in ancient Greek religion that embodiment is natural and good,",
            "The view in ancient Greek religion — 'Olympic paradigm' being a modern heuristic label, not an ancient technical term — that embodiment is natural and good,",
        ),
    ),
    # --- concept_orphic_zagreus_dionysus_myth (concept, risk=medium) ---
    # FLAG: Tag is an interpretive caveat (class=other) and is truncated after 'Olympiodorus
    #   (6th c'; the prose was hedged and attributed rather than deleted.
    "concept_orphic_zagreus_dionysus_myth": (
        # tag: the anthropogony is a contested modern reconstruction presented as plain fact,
        #   explicitly attested only in Olympiodorus (6th c.)
        (
            "Humans are born from the ashes of the Titans who had consumed Zagreus, explaining why humans have both divine (from Zagreus) and titanic (sinful) natures.",
            "On a contested modern reconstruction, humans are born from the ashes of the Titans who had consumed Zagreus, which would explain why humans have both divine (from Zagreus) and titanic (sinful) natures; this anthropogony is explicitly attested only in Olympiodorus (6th c.).",
        ),
    ),
    # --- concept_patet_exitus_seneca_e6f7g8h9 (concept, risk=high) ---
    "concept_patet_exitus_seneca_e6f7g8h9": (
        # tag: the term is defined at Diog. Laert. VII.130; VII.28 and VII.176 only report the
        #   two deaths
        (
            "attested for Zeno and Cleanthes (DL VII.28, 176), but the Greek sources",
            "defined at DL VII.130 (DL VII.28 and VII.176 report instead the self-inflicted deaths of Zeno and Cleanthes), but the Greek sources",
        ),
    ),
    # --- concept_perfect_vs_antecedent_causes_8w3x5z21 (concept, risk=high) ---
    "concept_perfect_vs_antecedent_causes_8w3x5z21": (
        # tag: the record wrongly listed the term as unattested; it is confirmed in Clement
        #   Stromateis VIII.9 and Ps.-Galen Definitiones Medicae
        (
            "but cylinder's shape (perfect cause) determines that it rolls rather than slides.",
            "but cylinder's shape (perfect cause, αὐτοτελὲς αἴτιον — a term confirmed in Clement, Stromateis VIII.9, and Ps.-Galen, Definitiones Medicae) determines that it rolls rather than slides.",
        ),
    ),
    # --- concept_pithanon_8f3a6d2c (concept, risk=high) ---
    # FLAG: The corrects_content tag (criteria are in Sextus, Adv. Math. 7.166–184, not Cicero,
    #   Academica II.34.108) is already satisfied by the prose, which credits Sextus Empiricus,
    #   Adv. Math. VII 166-189 and never cites the Academica; the small line-range divergence
    #   (189 vs 184) was left untouched. metadata.description_en carries the same two markers
    #   and cannot be reached by a description edit.
    "concept_pithanon_8f3a6d2c": (
        # batch marker carrying no bibliography: deleted
        ("[Wave 7 — résumé initial] L'impression plausible", "L'impression plausible"),
        # batch marker converted to a normal citation, preserving the real bibliographic locus
        (
            "[Enrichissement B2 — Amand 1945, p. 44-45, Intro §II ch. II §III] Amand caractérise",
            "Amand (1945, p. 44-45, Intro §II ch. II §III) caractérise",
        ),
    ),
    # --- concept_plurality_goods_alex (concept, risk=medium) ---
    # FLAG: The tag's own justification is internally inconsistent: it grounds the rejection on
    #   'page-references 250/251', which do not appear in this description, while 185.30-186.4
    #   does fall inside the Bruns range 164-212 that the tag itself states. I therefore only
    #   demoted the line reference instead of correcting it — the true locus of the quoted Greek
    #   is not recoverable from the tag.
    "concept_plurality_goods_alex": (
        # tag flags 'De Fato XV (Bruns 185.30-186.4)' as an out-of-range reference; the precise
        #   page/line anchor is dropped while the chapter and the edition are kept so the Greek
        #   quotation is not left unsourced
        ("(De Fato XV, Bruns 185.30-186.4: «", "(De Fato XV, ed. Bruns: «"),
    ),
    # --- concept_pneumatic_causation_stoic_bobzien (concept, risk=medium) ---
    # FLAG: The node label still reads 'reconstruction Bobzien 2001'; only the description could
    #   be fixed here.
    "concept_pneumatic_causation_stoic_bobzien": (
        # tag: Bobzien's 'Determinism and Freedom in Stoic Philosophy' is standardly cited as
        #   1998; '2001' is at best a paperback reissue
        ("reconstruit par Bobzien 2001 (Ch. 1", "reconstruit par Bobzien 1998 (Ch. 1"),
    ),
    # --- concept_providentia_stoic_seneca_b3c4d5e6 (concept, risk=medium) ---
    # FLAG: tag truncated: it flags the two phrases as wrongly attributed to 1.1 but does not
    #   give their correct locus, so the locus was removed rather than corrected
    "concept_providentia_stoic_seneca_b3c4d5e6": (
        # tag: only the first phrase is verbatim De Providentia 1.1; the '(1.1)' attribution of
        #   this phrase is wrong, so the locus is dropped
        (
            '"praeesse universis providentiam" (1.1) - providence presides over all',
            '"praeesse universis providentiam" - providence presides over all',
        ),
        # same: '(1.1)' attribution flagged as incorrect by the tag
        (
            '"interesse nobis deum" (1.1) - god is involved in our affairs',
            '"interesse nobis deum" - god is involved in our affairs',
        ),
    ),
    # --- concept_thelesis_willing_87d2b3cf (concept, risk=high) ---
    "concept_thelesis_willing_87d2b3cf": (
        # tag: the common LXX word for will is θέλημα, θέλησις being rare there; 'preferred
        #   θέλησις' is overstated
        (
            "Septuagint translators preferred θέλησις over βούλησις for rendering",
            "Septuagint translators preferred the θελ- root — chiefly θέλημα, θέλησις itself remaining rare (Proverbs, Ecclesiastes, 2 Chronicles, Wisdom) — over βούλησις for rendering",
        ),
    ),
    # --- concept_voluntas_y7z8a9b0 (concept, risk=high) ---
    # FLAG: The erroneous 'voluntas recta' @ Ep. 71.36 sits in metadata, not in the prose; the
    #   corrected Ep. 20.5 locus and its quotation (both supplied verbatim by the tag) were
    #   added instead.
    "concept_voluntas_y7z8a9b0": (
        # tag: 'voluntas recta' is not at Ep. 71.36; the locus for wisdom as consistent right
        #   willing is Ep. 20.5
        (
            "at Ep. 71.36 the same theme appears in verbal form, 'magna pars est profectus velle proficere … volo et mente tota volo'.",
            "at Ep. 71.36 the same theme appears in verbal form, 'magna pars est profectus velle proficere … volo et mente tota volo'; and at Ep. 20.5 wisdom is consistent right willing, 'semper idem velle atque idem nolle… ut rectum sit quod velis'.",
        ),
    ),
    # --- debate_stoic_academic_hellenistic (debate, risk=medium) ---
    # FLAG: The second 'batch B1' occurrence lives in metadata.description_en and cannot be
    #   reached by a description edit.
    "debate_stoic_academic_hellenistic": (
        # batch marker carrying no bibliography: deleted
        ("[Wave 7 — résumé initial] La confrontation", "La confrontation"),
        # batch marker converted to a normal citation, preserving the real bibliographic locus
        (
            "[Enrichissement B2 — Amand 1945, p. 41-43 + p. 46-48, Intro §II ch. II] Amand caractérise",
            "Amand (1945, p. 41-43 et p. 46-48, Intro §II ch. II) caractérise",
        ),
        # internal curation cross-reference 'batch B1' reworded into the reference the reader
        #   needs
        (
            "(les 6 titres argumentatifs reconstruits en Conclusion = matière du batch B1)",
            "(les 6 titres argumentatifs reconstruits dans la Conclusion d'Amand 1945)",
        ),
    ),
    # --- person_boethius_480_524ce_w3x4y5z6 (person, risk=high) ---
    "person_boethius_480_524ce_w3x4y5z6": (
        # tag: factual error — Boethius' works belong to the Latin tradition and were not
        #   transmitted to Arabic falsafa
        (
            " and deeply influenced Islamic philosophy (Al-Farabi, Avicenna, Averroes)",
            "",
        ),
    ),
    # --- person_carneades_214_129bce_l2m3n4o5 (person, risk=medium) ---
    # FLAG: metadata.description_en carries the same markers ('[Wave 7 initial summary]', '[B2
    #   enrichment — Amand 1945, pp. 41-46, …]') and the same graph-internal aside; the edit
    #   schema only reaches `description`
    "person_carneades_214_129bce_l2m3n4o5": (
        # batch marker carrying no bibliography — deleted
        ("[Wave 7 — résumé initial] Carnéade de Cyrène", "Carnéade de Cyrène"),
        # graph-internal aside describing the KG, not Carneades; the disagreement is carried by
        #   the edges
        (
            " (Désaccord encodé via les arêtes disagrees_with / interprets reliant ce nœud aux nœuds Bobzien et Amand.)",
            "",
        ),
        # batch marker carrying a real bibliographic locus — converted to prose citation
        (
            "[Enrichissement B2 — Amand 1945, p. 41-46, Intro §II ch. II §I-III] Amand insiste",
            "Amand 1945, p. 41-46 (Introduction §II ch. II §I-III), insiste",
        ),
    ),
    # --- person_cyril_alexandria (person, risk=high) ---
    # FLAG: The tag notes that Boulnois's principal monograph is Le paradoxe trinitaire chez
    #   Cyrille d'Alexandrie (1994); I did not substitute it for '(2000)' because the tag does
    #   not assert that this is the work actually meant. The dubious year was dropped instead.
    "person_cyril_alexandria": (
        # tag: the plenitudo libertatis / liberum arbitrium distinction and the reference
        #   'Boulnois (2000)' (no title, no page) are both undocumented; the hapax status of the
        #   Greek formula is already stated in the prose
        (
            "Distinguished plenitudo libertatis (pre-Fall) vs. liberum arbitrium (post-Fall). Source: Boulnois (2000).",
            "The distinction between plenitudo libertatis (pre-Fall) and liberum arbitrium (post-Fall) applies Latin terminology to a Greek author and remains to be documented, as does the reference to Boulnois.",
        ),
    ),
    # --- person_cyril_jerusalem_315_386 (person, risk=high) ---
    "person_cyril_jerusalem_315_386": (
        # tag: the anti-fatalist / anti-astrological argument is in Catechesis IV (esp. §18-21),
        #   NOT Catechesis XIII, which is 'On Christ Crucified and Buried'
        (
            "Catechesis IV traite explicitement de la liberté et de la providence ; Catechesis XIII développe une argumentation anti-fataliste anti-astrologique.",
            "Catechesis IV traite explicitement de la liberté et de la providence, et c'est là que se trouve l'argumentation anti-fataliste et anti-astrologique (en particulier §18-21 : l'âme se détermine elle-même, le péché ne vient pas des astres) ; la Catechesis XIII, elle, porte sur le Christ crucifié et enseveli.",
        ),
        # tag: 'SC 384 (Bouvet 1992)' could not be confirmed — in Sources Chrétiennes only
        #   Cyril's Mystagogical Catecheses are published (SC 126)
        (
            "SC 126 (Catéchèses mystagogiques, éd. Piédagnel 1966) ; SC 384 (Procatéchèse + Cat. I-IV, éd. Bouvet 1992).",
            "SC 126 (Catéchèses mystagogiques, éd. Piédagnel 1966), seul volume cyrillien paru dans cette collection.",
        ),
    ),
    # --- person_cyrus_alexandria_d641 (person, risk=high) ---
    # FLAG: Tag truncated at "he did not survive to be 'dé'"; what he did not survive to do
    #   could not be recovered, so the incorrect post-conquest dismissal was dropped rather than
    #   replaced.
    "person_cyrus_alexandria_d641": (
        # tag: the dismissal chronology was muddled — Cyrus was summoned/disgraced in 640-641
        #   before Heraclius's death, then rehabilitated
        (
            "Cyrus reste en charge sous Héraclius ; démis par l'empereur après la chute d'Alexandrie aux mains des Arabes ('Amr ibn al-'As, 642).",
            "Cyrus est rappelé et disgracié par Héraclius en 640-641, du vivant de l'empereur, pour avoir négocié avec les Arabes, puis réhabilité ; Alexandrie tombe aux mains des Arabes ('Amr ibn al-'As) en 642.",
        ),
    ),
    # --- person_diogenes_babylon_240_152bce (person, risk=medium) ---
    # FLAG: Tag truncated at 'The CHHP treats' - the correct CHHP locus for Diogenes is not
    #   recoverable, so the secondary-literature reference was deleted outright rather than
    #   repaired.
    "person_diogenes_babylon_240_152bce": (
        # tag: the Sedley chapter 'Diogenes of Babylon' in the Cambridge History of Hellenistic
        #   Philosophy could not be confirmed as a standalone chapter with that title, so the
        #   reference is removed
        (
            " Sources secondaires : David Sedley, « Diogenes of Babylon », in Algra/Barnes/Mansfeld/Schofield, Cambridge History of Hellenistic Philosophy (CUP 1999).",
            "",
        ),
    ),
    # --- person_favorinus_of_arles_9n4o6q32 (person, risk=medium) ---
    # FLAG: metadata.description_en carries the same two markers and cannot be reached by a
    #   description edit.
    "person_favorinus_of_arles_9n4o6q32": (
        # batch marker carrying no bibliography: deleted
        ("[Wave 7 — note] Favorinus est avant tout", "Favorinus est avant tout"),
        # batch marker converted to a normal citation, preserving the real bibliographic locus
        (
            "[Enrichissement B3 — Amand 1945, p. 96-100, ll. 5919-6128] Selon Amand",
            "Selon Amand (1945, p. 96-100, ll. 5919-6128)",
        ),
        # residual batch label 'B3' inside the prose removed while the Gellius/Hosius locus is
        #   kept
        (
            "(cf. argument dixième B3, Aulu-Gelle XIV, 1, 23, p. 106 l. 31 — p. 107 l. 12 Hosius)",
            "(cf. le dixième argument, Aulu-Gelle XIV, 1, 23, p. 106 l. 31 — p. 107 l. 12 Hosius)",
        ),
    ),
    # --- person_hippolytus_rome_d235 (person, risk=medium) ---
    # FLAG: Precision lost: the tag says the two ranges must be reconciled but does not say
    #   which is right, so only the book number is kept.
    "person_hippolytus_rome_d235": (
        # tag: the range 'Adv. Math. V, 50-105' conflicts with 'V.37-105' recorded elsewhere in
        #   the node; at least one is imprecise, so the section range is dropped
        (
            "Sextus Empiricus Adv. Math. V, 50-105 (avec",
            "Sextus Empiricus, Adv. Math. V (avec",
        ),
    ),
    # --- person_maximus_of_tyre_125_185ce (person, risk=medium) ---
    "person_maximus_of_tyre_125_185ce": (
        # tag: a full ἀμφίβι- stem search of Maximus (TLG 0563) returns zero hits, so the word
        #   is not his own term
        (
            "et que la vie humaine est « amphibie » (ἀμφίβιος) — mélange de liberté et de nécessité.",
            "et que la vie humaine est « amphibie », mélange de liberté et de nécessité — cette caractérisation étant moderne, le terme ἀμφίβιος n'étant pas attesté dans le corpus conservé de Maxime.",
        ),
    ),
    # --- person_porphyry (person, risk=medium) ---
    # FLAG: Tag is truncated; the fragment-based paragraph and the 'Boulnois (2000)' edition
    #   line were kept but the attribution is now marked as unconfirmed rather than asserted.
    "person_porphyry": (
        # tag: the claim of a free-will treatise 'To Nemertius … seven fragments preserved and
        #   refuted by Cyril of Alexandria' could not be confirmed against a standard reference
        #   work
        (
            "For the free will debate, Porphyry's most significant contribution is the treatise To Nemertius (Pros Nemertion), on the topic of human freedom, surviving only as seven fragments preserved and refuted by Cyril of Alexandria. In these fragments, Porphyry argued",
            "For the free will debate, a treatise To Nemertius (Pros Nemertion) on human freedom, said to survive only as seven fragments preserved and refuted by Cyril of Alexandria, has been ascribed to Porphyry — but that ascription could not be confirmed against standard reference works. On that ascription, Porphyry argued",
        ),
    ),
    # --- person_rene_descartes_1aa22692 (person, risk=high) ---
    "person_rene_descartes_1aa22692": (
        # tag: 'infimus gradus libertatis' is from Meditatio IV (AT VII 58), NOT from Principia
        #   Philosophiae I.39-41
        (
            'is acknowledged as the "lowest degree of freedom" (infimus gradus libertatis).',
            'is acknowledged as the "lowest degree of freedom": the phrase infimus gradus libertatis itself comes from Meditatio IV (AT VII 58: indifferentia illa ... est infimus gradus libertatis), not from the Principia.',
        ),
    ),
    # --- pub_belcastro_predestinazione_origene (publication, risk=medium) ---
    # FLAG: Tag truncated: only the genre error could be recovered; the remainder of the
    #   objection (about the loci claimed across De Principiis III.1, Comm. Rom. and Philocalia
    #   21-27) is lost.
    "pub_belcastro_predestinazione_origene": (
        # tag disputes the description's framing; the node's own bibliographic label gives a
        #   journal article (Adamantius 22, p. 211-243), not a monograph
        (
            "Monographie de Mauro Belcastro consacrée à",
            "Article de Mauro Belcastro consacré à",
        ),
    ),
    # --- pub_pouderon_2000_athenagoras (publication, risk=medium) ---
    # FLAG: The node id and label still carry '2000'; that is outside the description and
    #   remains open.
    "pub_pouderon_2000_athenagoras": (
        # tag: Théologie historique 82 is the 1989 Beauchesne first edition; the '2000' comes
        #   from a file mislabel and no distinct 2000 edition is attested
        (
            "(Beauchesne 1989-rééd. 2000, *Théologie historique* 82, 368 p.)",
            "(Beauchesne 1989, *Théologie historique* 82, 368 p. ; aucune réédition distincte de 2000 n'est attestée)",
        ),
    ),
    # --- pub_sytsma_2020_universal_salvation_origen (publication, risk=medium) ---
    # FLAG: The tag is cut off before saying what became of the alleged 2020 monograph, so the
    #   prose only records that it is unconfirmed rather than asserting it does not exist. The
    #   node id and label still carry '2020'.
    "pub_sytsma_2020_universal_salvation_origen": (
        # tag: 'The verifiable object is the 2018 Marquette dissertation (title, author, no. 769
        #   all correct and confirmed by the local PDF). The claimed 2020 Gorgias Press
        #   MONOGRAPH … [truncated]'
        (
            "Monograph (Gorgias Press, 2020) revising Sytsma's 2018 Marquette dissertation 'Reconciling Universal Salvation and Freedom of Choice in Origen of Alexandria'.",
            "Sytsma's 2018 Marquette dissertation 'Reconciling Universal Salvation and Freedom of Choice in Origen of Alexandria' (no. 769), the only verifiable object behind this record; the claimed 2020 Gorgias Press monograph is unconfirmed.",
        ),
    ),
    # --- sc123_melito_apologia_ad_antoninum (work, risk=high) ---
    "sc123_melito_apologia_ad_antoninum": (
        # tag: the excerpt itself (local SC 31 text) names Hadrian as grandfather and Antoninus
        #   Pius as father, which identifies the addressee as Marcus Aurelius
        (
            "l'identification la plus probable étant Marc Aurèle 161-180 ap. J.-C., bien que la tradition manuscrite oscille",
            "l'excerptum nomme Hadrien comme grand-père du destinataire et Antonin le Pieux comme son père, ce qui identifie ce dernier à Marc Aurèle, 161-180 ap. J.-C.",
        ),
    ),
    # --- sc123_melito_de_anima_et_corpore (work, risk=high) ---
    "sc123_melito_de_anima_et_corpore": (
        # curator-addressed framing; the disputed-authorship correction demanded by the tag is
        #   already carried by the preceding clause
        (" and should not be stated as settled", ""),
    ),
    # --- scholar_harl_m (person, risk=high) ---
    "scholar_harl_m": (
        # tag: Harl did not co-edit SC 7bis (Homélies sur la Genèse); that volume is
        #   Doutreleau's, with an introduction by de Lubac and Doutreleau
        (
            " Co-éditrice (avec Doutreleau) des Homélies sur la Genèse d'Origène (SC 7bis, Cerf 1976, rééd.).",
            "",
        ),
    ),
    # --- scholar_jacobsen_a (person, risk=medium) ---
    "scholar_jacobsen_a": (
        # tag: 'né 1962' contradicts metadata.birth_date 1963 and the birth year could not be
        #   confirmed; the unsupported date is dropped
        (
            "Patristicien danois (né 1962), professeur",
            "Patristicien danois, professeur",
        ),
        # tag: no such edited volume by Jacobsen could be found; the title matches a different
        #   pair of editors, so the misattributed reference is removed
        (
            " Directeur de Universal Salvation: The Current Debate (Cambridge University Press 2019).",
            "",
        ),
    ),
    # --- scholar_list_n (person, risk=high) ---
    # FLAG: The tag is truncated before naming the other scholar, so the node label 'Nicholas
    #   List' could not be verified or corrected; the description now states the conflation
    #   explicitly rather than silently attaching patristic research fields to a philosopher of
    #   mind. The node probably needs splitting into two person nodes.
    "scholar_list_n": (
        # tag: 'This field conflates two different scholars. Fürst 2022 discusses CHRISTIAN List
        #   (LSE philosopher, Why Free Will Is Real 2019 / Warum der freie Wille existiert 2021,
        #   compatibilist libertarianism)'
        (
            "Early Christian studies, Middle Platonism, Justin Martyr",
            "Research fields recorded as Early Christian studies, Middle Platonism and Justin Martyr. These belong to a different scholar than the List discussed by Fürst 2022, which is Christian List, the LSE philosopher of 'compatibilist libertarianism' (Why Free Will Is Real, 2019; German edition Warum der freie Wille existiert, 2021).",
        ),
    ),
    # --- scholar_perrone_l (person, risk=medium) ---
    "scholar_perrone_l": (
        # tag: birth year '1948' could not be confirmed (some references give 1949)
        (
            "Patristicien italien (né 1948), professeur",
            "Patristicien italien, professeur",
        ),
    ),
    # --- scholar_stump_e (person, risk=medium) ---
    # FLAG: Tag truncated at 'an intellectualist account without '; the missing qualifier could
    #   not be recovered, so the prose says only 'conception intellectualiste'.
    "scholar_stump_e": (
        # tag: the label 'compatibilisme théologique' is contestable — Stump explicitly denies
        #   Aquinas's account is either standard libertarian or standard compatibilist and calls
        #   it an intellectualist account
        (
            "compatibilisme théologique, libre arbitre comme auto-détermination rationnelle compatible avec la grâce efficace augustino-thomiste.",
            "Stump refuse expressément de ranger la lecture thomiste du libre arbitre sous le libertarisme standard comme sous le compatibilisme standard ; elle la qualifie de conception intellectualiste, où le libre arbitre est une auto-détermination rationnelle compatible avec la grâce efficace augustino-thomiste.",
        ),
    ),
    # --- scholar_tomberlin_j (person, risk=medium) ---
    # FLAG: The residual text removed here is the tail of a nested/truncated audit note that
    #   falls OUTSIDE the tag as delimited in TAGS PRESENT (which closes at 'the argument t]'),
    #   so tag-stripping alone would leave it standing; the substantive point it was making is
    #   itself truncated ('the substantive point it makes (ar') and is therefore lost. If the
    #   applier's tag detection is bracket-balanced rather than first-']', this edit is simply a
    #   no-op. The node keeps only its minimal original prose ('philosophy of religion, free
    #   will defence').
    "scholar_tomberlin_j": (
        # tag: the description carries embedded malformed leftover verification text that should
        #   be cleaned; this trailing fragment sits outside the [Vérif.] tag's own brackets and
        #   would survive tag-stripping
        (
            "') that is malformed leftover text and should be cleaned; the substantive point it makes (ar]",
            "",
        ),
    ),
    # --- scholar_wildberg_christian (person, risk=medium) ---
    # FLAG: The chapter number is lost: the tag records the contradiction (ch. 21 vs ch. 18)
    #   without resolving it, so neither number could be asserted.
    "scholar_wildberg_christian": (
        # tag: internal contradiction 'ch. 21' (French) vs 'ch. 18' (description_en); the
        #   unverifiable chapter number is dropped
        ("Auteur du ch. 21 du volume Destrée 2014, «", "Auteur du chapitre «"),
        # keeps the Destrée 2014 volume reference once the chapter number is removed
        (
            "what is up to us », étudiant",
            "what is up to us » du volume Destrée 2014, étudiant",
        ),
    ),
    # --- scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0 (argument, risk=medium) ---
    "scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0": (
        # batch marker carrying no bibliography; deleted with its adjacent whitespace
        ("[Résumé initial — Wave 7] ", ""),
        # curation patch marker carrying no bibliographic locus; deleted with its line break
        (
            "[Enrichissement Conclusion-Épilogue — Patch B1 2026-05-15]\nThèse centrale",
            "Thèse centrale",
        ),
    ),
    # --- scholarly_argument_amand_de_mendieta_reconstruction_of_carneades_ar_4 (argument, risk=medium) ---
    # FLAG: The closing paragraph still addresses KG curators directly (confidence bands
    #   0.5-0.75, 'modélisation KG'); the plan did not call for its removal, so it was left as
    #   is.
    "scholarly_argument_amand_de_mendieta_reconstruction_of_carneades_ar_4": (
        # batch marker carrying no bibliography: deleted
        (
            "[Résumé initial — Wave 7] Reconstruction of Carneades'",
            "Reconstruction of Carneades'",
        ),
        # batch/patch marker deleted; its bibliographic locus (1945, p. 572) is already stated
        #   in the following sentence
        (
            "[Enrichissement Conclusion-Épilogue — Patch B1 2026-05-15]\nAveu philologique",
            "Aveu philologique",
        ),
    ),
    # --- scholarly_argument_bonaiuti_ambrosiaster_s_influence_on_au_1 (argument, risk=medium) ---
    # FLAG: Tag truncated at 'The page range'; the wrong year (1924) is encoded in the linked
    #   work id and still needs fixing in metadata.
    "scholarly_argument_bonaiuti_ambrosiaster_s_influence_on_au_1": (
        # tag: the linked work id encodes 1924, but the article appeared in HTR 10 (1917), pp.
        #   159–175, trans. Giorgio La Piana — the correct reference is stated in the prose
        (
            "and (4) the positive and realistic Scriptural interpretation method",
            "and (4) the positive and realistic Scriptural interpretation method (Bonaiuti, Harvard Theological Review 10, 1917, p. 159–175, translated by Giorgio La Piana)",
        ),
    ),
    # --- scholarly_argument_bonaiuti_augustine_s_predestination_and_2 (argument, risk=medium) ---
    "scholarly_argument_bonaiuti_augustine_s_predestination_and_2": (
        # tag: the article appeared in HTR vol. 10, no. 2 (April 1917), pp. 159-175, not 1924 as
        #   the linked work id implies
        (
            "'der Paulus nach Paulus und der Luther vor Luther'",
            "'der Paulus nach Paulus und der Luther vor Luther' (Harvard Theological Review 10.2, April 1917, pp. 159-175)",
        ),
    ),
    # --- scholarly_argument_fee_determinism_and_predestination_1 (argument, risk=high) ---
    # FLAG: Node was proposed for deletion; deletion is out of scope here, so it is rewritten as
    #   a negative finding per the plan's alternative. The label still reads '(placeholder — no
    #   argument on determinism)' and 3 edges point at it — both need handling outside the
    #   description.
    "scholarly_argument_fee_determinism_and_predestination_1": (
        # plan: curator-addressed deletion note removed; the remaining prose stands as a
        #   documented negative finding (Fee treats Rom 8,28-30 only on the grammatical subject
        #   of συνεργεῖ)
        (
            " Ce nœud est un artefact d'extraction et devrait être supprimé du graphe.",
            "",
        ),
    ),
    # --- scholarly_argument_gourinat_chrysippus_s_compatibilism_0 (argument, risk=high) ---
    # FLAG: the linked work node slug
    #   'scholarly_work_gourinat_0_responsabilit_morale_et_destin_une_r_pon' and this node's id
    #   still attribute the article to Gourinat — outside the description field
    "scholarly_argument_gourinat_chrysippus_s_compatibilism_0": (
        # tag: the source file confirms the author is Olivier D'Jeranian, not Gourinat (as the
        #   node/work slug implies)
        (
            "Chrysippus's compatibilism — Chrysippus's attempt",
            "Chrysippus's compatibilism (D'Jeranian) — Chrysippus's attempt",
        ),
    ),
    # --- scholarly_argument_gourinat_cicero_s_critique_of_chrysippu_2 (argument, risk=high) ---
    # FLAG: The misattribution itself lives in scholarly_work_id 'scholarly_work_gourinat_0_...'
    #   and still needs correcting in metadata.
    "scholarly_argument_gourinat_cicero_s_critique_of_chrysippu_2": (
        # tag: the article is by Olivier D'Jeranian, not Gourinat (whom the scholarly_work_id
        #   names); the correct author is now stated in the prose
        (
            "Cicero's critique of Chrysippus — Cicero demonstrates",
            "Cicero's critique of Chrysippus, as read by Olivier D'Jeranian — Cicero demonstrates",
        ),
    ),
    # --- scholarly_argument_grant_eusebius_s_suppression_of_evid_3 (argument, risk=medium) ---
    "scholarly_argument_grant_eusebius_s_suppression_of_evid_3": (
        # tag: Grant (p. 133) says Eusebius suppressed the criticism of Origen; the adjective
        #   'voluntary' is a spurious insertion
        ("information about voluntary criticism", "information about criticism"),
    ),
    # --- scholarly_argument_meyer_epicurean_freedom_from_determi_4 (argument, risk=high) ---
    # FLAG: The block's pointers to other KG nodes and the bibliography attached to them
    #   (Lucretius DRN II.251-293; Cicero De fato 22-23, De nat. deor. I.69-70; Fowler 1983,
    #   Englert 1987, Purinton 1999; Bobzien, O'Keefe, Furley) were dropped from the description
    #   per the plan and should be preserved in metadata.rescope_note.
    "scholarly_argument_meyer_epicurean_freedom_from_determi_4": (
        # PLAN_ACTION: the '[Re-scopé …]' block is a curation changelog; only its substantive
        #   scholarly content (Meyer does not hold the swerve thesis; zero occurrences of
        #   swerve/clinamen/declinatio in Ancient Ethics 2008) is kept, in the description's own
        #   English
        (
            " [Re-scopé 2026-08-03 : ce nœud attribuait auparavant à Meyer la thèse doxographique standard selon laquelle Épicure aurait introduit la παρέγκλισις / clinamen pour sauver la liberté contre le déterminisme démocritéen. Meyer n'écrit rien de tel : « swerve », « clinamen » et « declinatio » ont ZÉRO occurrence dans tout Ancient Ethics (2008). Pour cette thèse, voir les nœuds correctement sourcés argument_epicurean_swerve_for_freedom_m4n5o6p7 (Lucrèce DRN II.251-293 ; Cicéron, De fato 22-23 et De nat. deor. I.69-70 ; Fowler 1983, Englert 1987, Purinton 1999) et, pour la position contraire, pub_bobzien_2000_epicurus_free_will, scholarly_argument_o_keefe_role_of_the_swerve_in_epicurus_1 et scholar_position_furley_epicurus_swerve_indirect.]",
            ' Meyer does not advance the standard doxographic thesis that Epicurus introduced the swerve (παρέγκλισις / clinamen) to rescue freedom against Democritean determinism: "swerve", "clinamen" and "declinatio" have zero occurrences anywhere in Ancient Ethics (2008).',
        ),
    ),
    # --- scholarly_argument_narbonne_soul_s_descent_and_moral_respo_2 (argument, risk=medium) ---
    "scholarly_argument_narbonne_soul_s_descent_and_moral_respo_2": (
        # tag: the Greek gloss is incorrect and unattested in Narbonne's text (it means 'non-
        #   participation', not the undescended-soul doctrine)
        ("'partly undescended soul' (ἀμέθεξις) as", "'partly undescended soul' as"),
    ),
    # --- scholarly_argument_rousseau_irenaeus_s_own_position_on_fre_1 (argument, risk=medium) ---
    # FLAG: Tag truncated at 'the Valentinian/Marcosian systems'; the claim was qualified rather
    #   than deleted, per the tag's 'slightly overreaches'.
    "scholarly_argument_rousseau_irenaeus_s_own_position_on_fre_1": (
        # tag: attributing to the SC 263/264 Book I edition a presentation of Irenaeus's own
        #   positive free-will doctrine slightly overreaches, Book I being heresiography
        (
            "The edition presents Irenaeus's critique of Gnostic determinism as implying that Irenaeus himself affirms human moral responsibility and free choice;",
            "Book I of the edition is heresiography, an exposition of the Valentinian and Marcosian systems, so reading it as a presentation of Irenaeus's own positive doctrine of free will overreaches; his critique of Gnostic determinism does nonetheless imply that he affirms human moral responsibility and free choice, and",
        ),
    ),
    # --- scholarly_argument_still_paul_s_role_as_apologist_and_d_0 (argument, risk=medium) ---
    "scholarly_argument_still_paul_s_role_as_apologist_and_d_0": (
        # tag: unsupported editorial gloss — the framing is about categorising apologists and
        #   Pauline reception, not a defence of moral agency against fatalism
        (
            "; the editorial framing suggests Pauline theology provided resources for defending Christian moral agency and voluntary faith against fatalistic and deterministic philosophies",
            "; the editorial framing (Introduction and Afterword) concerns the categorisation of apologists and the reception of Paul",
        ),
    ),
    # --- scholarly_argument_telfer_christian_autexousia_and_jewis_2 (argument, risk=medium) ---
    # FLAG: The attested form is undeterminable from the truncated tag (the prose had γένεα, the
    #   tag records γένη on both sides of the arrow); the Greek parenthesis was deleted rather
    #   than reconstructed, per the zero-fabrication rule.
    "scholarly_argument_telfer_christian_autexousia_and_jewis_2": (
        # tag: the correction record is malformed (both sides of the arrow identical) and leaves
        #   an unverified Greek form standing; the parenthetical Greek is removed rather than
        #   guessed
        (" (γένεα αὐτεξούσια)", ""),
    ),
    # --- scholarly_argument_telfer_new_testament_and_autexousia_7 (argument, risk=high) ---
    "scholarly_argument_telfer_new_testament_and_autexousia_7": (
        # tag: the trailing clause is an editorial addition not found in Telfer's article
        #   (though factually true), so it is detached from the Telfer attribution rather than
        #   presented as his
        (
            ", though Paul does not use the term αὐτεξούσιος itself",
            ". The added remark that Paul does not use the term αὐτεξούσιος itself is editorial, not Telfer's",
        ),
    ),
    # --- scholarly_argument_tomberlin_divine_omniscience_and_counter_1 (argument, risk=medium) ---
    # FLAG: Co-authorship is now stated in the prose, but the node id, label and any author
    #   field still name Tomberlin alone — those need a separate fix.
    "scholarly_argument_tomberlin_divine_omniscience_and_counter_1": (
        # tag: the source article is CO-AUTHORED by James E. Tomberlin and Frank McGuinness,
        #   Religious Studies vol. 13 (1977), pp. 455-475; the node attributed it to Tomberlin
        #   alone
        (
            "divine omniscience and counterfactuals of freedom — If God is omniscient",
            "divine omniscience and counterfactuals of freedom (James E. Tomberlin and Frank McGuinness, Religious Studies 13, 1977, pp. 455-475) — If God is omniscient",
        ),
    ),
    # --- scholarly_argument_tomberlin_free_will_defence_0 (argument, risk=medium) ---
    "scholarly_argument_tomberlin_free_will_defence_0": (
        # tag: the article is co-authored with Frank McGuinness (Religious Studies 13, 1977,
        #   455-475); the node attributed it to Tomberlin alone
        (
            "does not exist",
            "does not exist. The argument is advanced by James E. Tomberlin and Frank McGuinness, Religious Studies vol. 13 (1977), pp. 455-475",
        ),
    ),
    # --- scholarly_argument_wolfson_comparison_with_plato_s_timaeu_3 (argument, risk=high) ---
    # FLAG: The Timaeus loci correction (node's '69C-72D' vs Wolfson's 'Tim. 42E ff.; 69C')
    #   applies to metadata loci absent from the description, and the tag is truncated on the
    #   second locus; the linked work node dated 1947 still needs re-pointing to the 1942
    #   article.
    "scholarly_argument_wolfson_comparison_with_plato_s_timaeu_3": (
        # tag: this pagination belongs to Wolfson's HTR 35 (1942) article, pp. 131-169, not to
        #   the 1947 book the node links
        ("(p. 135ff)", "(HTR 35, 1942, p. 135ff)"),
    ),
    # --- scholarly_argument_wolfson_laws_of_nature_and_divine_gove_0 (argument, risk=medium) ---
    # FLAG: node metadata still dates the work 1947
    "scholarly_argument_wolfson_laws_of_nature_and_divine_gove_0": (
        # tag: pages 131-132 belong to Wolfson's 1942 HTR article, not the 1947 book; correct
        #   year = 1942
        (
            "which is part of the pre-existent incorporeal Logos",
            "which is part of the pre-existent incorporeal Logos (Wolfson, HTR 35 [1942], p. 131-169, at 131-132)",
        ),
    ),
    # --- scholarly_argument_wolfson_mind_body_relation_and_human_c_1 (argument, risk=medium) ---
    # FLAG: The wrong year (1947) is stored in metadata and still needs fixing there.
    "scholarly_argument_wolfson_mind_body_relation_and_human_c_1": (
        # tag: the work is dated 1947 but the cited pages 131-133 belong to the 1942 HTR article
        #   (HTR 35: 131-169); correct year = 1942
        (
            "creating an ongoing internal struggle",
            "creating an ongoing internal struggle (Wolfson, Harvard Theological Review 35, 1942, p. 131-133)",
        ),
    ),
    # --- scholarly_work_barclay_2006_divine_and_human_agency_in_paul_and_his_ (publication, risk=medium) ---
    "scholarly_work_barclay_2006_divine_and_human_agency_in_paul_and_his_": (
        # tag: the volume is co-edited by Barclay AND Simon J. Gathercole; only Barclay was
        #   recorded
        (
            "Divine and Human Agency in Paul and His Cultural Environment",
            "Divine and Human Agency in Paul and His Cultural Environment, co-edited by John M. G. Barclay and Simon J. Gathercole",
        ),
    ),
    # --- scholarly_work_breytenbach_2023_early_christianity_in_athens_attica_and_ (publication, risk=medium) ---
    "scholarly_work_breytenbach_2023_early_christianity_in_athens_attica_and_": (
        # tag: the Brill copyright page reads 'Copyright 2023 by Cilliers Breytenbach and Elli
        #   Tzavella'; the co-author was omitted
        (
            "Early Christianity in Athens, Attica, and Adjacent Areas: From Paul to Justinian I (1st–6th cent. AD)",
            "Early Christianity in Athens, Attica, and Adjacent Areas: From Paul to Justinian I (1st–6th cent. AD), by Cilliers Breytenbach and Elli Tzavella (Brill, 2023); to be cited as Breytenbach & Tzavella 2023, not Breytenbach alone.",
        ),
    ),
    # --- scholarly_work_hendriksen_0_new_testament_commentary_romans (publication, risk=medium) ---
    # FLAG: The label still carries 'Hendriksen ?' — the publication year remains unknown and
    #   was not supplied by the tag.
    "scholarly_work_hendriksen_0_new_testament_commentary_romans": (
        # tag: publisher field is null; the NTC Romans was published by Baker Book House (Baker
        #   Academic), Grand Rapids
        (
            "New Testament Commentary: Romans",
            "New Testament Commentary: Romans (Grand Rapids: Baker Book House / Baker Academic).",
        ),
    ),
    # --- scholarly_work_martin_0_josephus_use_of_heimarmene_in_the_jewish (publication, risk=medium) ---
    "scholarly_work_martin_0_josephus_use_of_heimarmene_in_the_jewish": (
        # tag: the venue was unrecorded; the article appeared in Numen (Brill), vol. 28, fasc. 2
        (
            "XIII, 171-3",
            "XIII, 171-3. Article published in the journal Numen (Brill), vol. 28, fasc. 2",
        ),
    ),
    # --- scholarly_work_pironet_2003_faiblesse_de_la_raison_ou_faiblesse_de_v (publication, risk=medium) ---
    # FLAG: The co-author is now named in the prose, but author_id scholar_pironet_f still needs
    #   a second author entry in metadata. Tag truncated at 'Not an attribution error pe'.
    "scholarly_work_pironet_2003_faiblesse_de_la_raison_ou_faiblesse_de_v": (
        # tag: the article is co-authored by Fabienne Pironet and Christine Tappolet; the single
        #   author_id omits Tappolet
        (
            "peut-on choisir?",
            "peut-on choisir? Article co-signé par Fabienne Pironet et Christine Tappolet.",
        ),
    ),
    # --- scholarly_work_pouderon_1998_les_apologistes_chr_tiens_et_la_culture_ (publication, risk=medium) ---
    "scholarly_work_pouderon_1998_les_apologistes_chr_tiens_et_la_culture_": (
        # tag: the volume is co-edited by Bernard Pouderon AND Joseph Doré; the node recorded
        #   Pouderon alone
        (
            "Les Apologistes chrétiens et la culture grecque",
            "Les Apologistes chrétiens et la culture grecque, volume collectif co-édité par Bernard Pouderon et Joseph Doré.",
        ),
    ),
    # --- scholarly_work_pouderon_2003_aristide_apologie (publication, risk=medium) ---
    # FLAG: Tag truncated at 'The page_range v'; whatever page-range problem it reported could
    #   not be recovered and is not addressed.
    "scholarly_work_pouderon_2003_aristide_apologie": (
        # tag: SC 470 is edited by Pouderon AND Marie-Joseph Pierre (with B. Outtier and M.
        #   Guiorgadzé for the Armenian/Georgian)
        (
            "Aristide. Apologie",
            "Aristide. Apologie — SC 470, édité par Bernard Pouderon et Marie-Joseph Pierre, avec B. Outtier et M. Guiorgadzé pour l'arménien et le géorgien",
        ),
    ),
    # --- scholarly_work_schiffman_2007_the_dead_sea_scrolls_the_truth_behind_th (publication, risk=medium) ---
    # FLAG: Tag truncated at 'Author (Schif' - any correction to the author record could not be
    #   recovered.
    "scholarly_work_schiffman_2007_the_dead_sea_scrolls_the_truth_behind_th": (
        # tag: the item is an audio lecture course with a printed course guide, not a monograph
        (
            "The Dead Sea Scrolls: The Truth Behind the Mystique",
            "The Dead Sea Scrolls: The Truth Behind the Mystique — a Modern Scholar / Recorded Books audio lecture course with a printed course guide, not a conventional monograph.",
        ),
    ),
    # --- scholarly_work_schneider_2010_la_libert_dans_la_philosophie_de_proclus (publication, risk=medium) ---
    "scholarly_work_schneider_2010_la_libert_dans_la_philosophie_de_proclus": (
        # tag: the work is a doctoral thesis, not a monograph; year and institution confirmed by
        #   the tag
        (
            "La liberté dans la philosophie de Proclus",
            "La liberté dans la philosophie de Proclus — thèse de doctorat (Université de Neuchâtel, 2010).",
        ),
    ),
    # --- scholarly_work_tolan_2020_the_contemplation_of_the_transcendent_he (publication, risk=medium) ---
    # FLAG: Node id and label still say 2020; the year field itself should be reviewed.
    "scholarly_work_tolan_2020_the_contemplation_of_the_transcendent_he": (
        # tag: node dates the thesis 2020 while the source file is labelled 'Tolan - 2021';
        #   defended c.2020, deposited/dated 2021
        (
            "from the Stoics to Origen",
            "from the Stoics to Origen. Dissertation defended c. 2020 and deposited/dated 2021; '2021' is the more commonly cited year.",
        ),
    ),
    # --- synthesis_amand1945_basil_hex_vi_7_amand_origin_point (synthesis, risk=medium) ---
    # FLAG: metadata.description_en carries the mirror sentence ('This node is thus…'); the edit
    #   schema only reaches `description`
    "synthesis_amand1945_basil_hex_vi_7_amand_origin_point": (
        # curator self-reference to the KG node removed; claim unchanged
        (
            "Ce nœud constitue donc la racine génétique",
            "Ce passage constitue la racine génétique",
        ),
    ),
    # --- synthesis_amand1945_ch3_moral_argument_scheme_announcement (synthesis, risk=medium) ---
    # FLAG: The same artifacts remain in metadata.description_en ('the 6 argument-titles of
    #   batch B1', 'see B1 nodes …', 'Explicitly NOT to be duplicated with B1 …') and in the
    #   LABEL suffix ' = B1'; neither is reachable through description edits.
    "synthesis_amand1945_ch3_moral_argument_scheme_announcement": (
        # PLAN_ACTION: 'batch B1' is an internal curation cross-reference; the reader already
        #   has 'reconstruite en Conclusion'
        (" du batch B1)", ")"),
        # PLAN_ACTION: drop the 'B1' batch label, keep the pointer to the target nodes
        (
            "voir nœuds B1 argument_carneadean_*_amand1945",
            "voir les nœuds argument_carneadean_*_amand1945",
        ),
        # PLAN_ACTION: editorial directive addressed to the curator, not scholarship
        (
            " Annonce explicitement à ne PAS dupliquer avec B1 : ce nœud Ch. III est une porte d'entrée structurelle, B1 est le développement détaillé avec témoins.",
            "",
        ),
    ),
    # --- synthesis_amand1945_cicero_ch2i_cadre (synthesis, risk=high) ---
    # FLAG: The tag announces two soft points but is truncated after the first; point (2) is
    #   unrecoverable and no edit was made for it.
    "synthesis_amand1945_cicero_ch2i_cadre": (
        # tag: Amand's candidates (following Lörcher 1907) are Clitomachus/Antiochus, not
        #   'Antiochus of Ascalon OR Posidonius'
        (
            "probablement issu d'Antiochus d'Ascalon ou de Posidonius",
            "probablement issu de Clitomaque ou d'Antiochus d'Ascalon (les candidats retenus par Amand, à la suite de Lörcher 1907)",
        ),
    ),
    # --- synthesis_amand1945_gregory_nyssa_carneadean_role (synthesis, risk=medium) ---
    "synthesis_amand1945_gregory_nyssa_carneadean_role": (
        # tag: the exact figure '23 arguments anti-astrologiques' could not be confirmed in
        #   Amand and is over-precise
        (
            "il accumule 23 arguments anti-astrologiques",
            "il accumule une série d'arguments anti-astrologiques",
        ),
    ),
    # --- synthesis_amand1945_hierocles_bizarre_carneadean_inversion (synthesis, risk=high) ---
    "synthesis_amand1945_hierocles_bizarre_carneadean_inversion": (
        # tag: editorial overreach - Amand says only that Hierocles's developments 'rappellent
        #   singulierement' Origen's effort; neither he nor the sources establish a confirmed
        #   contact
        (
            " — proximité doctrinale qu'Amand juge probable (Phase 9 EleutherIA confirme contact philosophique direct)",
            ", sans qu'il affirme pour autant un contact doctrinal établi",
        ),
    ),
    # --- synthesis_amand1945_origen_pivot_witness (synthesis, risk=high) ---
    # FLAG: The tag names only part of Amand's six textes témoins (Cicéron, Philon, Favorinus
    #   ap. Gellius XIV.1, pseudo-Pl…) before truncating, so the spurious 7th list item could
    #   not be identified; the erroneous count was removed instead of a witness.
    "synthesis_amand1945_origen_pivot_witness": (
        # tag: 'Origène = 1er témoin patristique' overstates; in Amand's Livre II, Justin,
        #   Tatien, Bardesane and Clément precede Origène
        (
            "Synthèse Amand : Origène = 1er témoin patristique de la lignée carnéadienne anti-fataliste, pivot historiographique du Livre II d'Amand.",
            "Synthèse Amand : Origène, pivot historiographique du Livre II d'Amand dans la lignée carnéadienne anti-fataliste — il n'ouvre pas la série patristique, puisque Justin (Ch. I), Tatien (Ch. II), Bardesane (Ch. III) et Clément d'Alexandrie (Ch. IV) le précèdent.",
        ),
        # tag: the text says '6 témoins' but lists 7 items; the count is dropped since the
        #   spurious item cannot be identified from the truncated tag
        (
            "les 6 témoins de la reconstruction carnéadienne",
            "les témoins de la reconstruction carnéadienne",
        ),
    ),
    # --- synthesis_amand1945_philo_attitude_astrology_signs_not_causes (synthesis, risk=medium) ---
    "synthesis_amand1945_philo_attitude_astrology_signs_not_causes": (
        # tag: the Greek phrase is the node's own retroversion of Amand's French and could not
        #   be verified, so Amand's French wording (as quoted in the tag) replaces it
        (
            "(λογικαὶ καὶ θεῖαι φύσεις, οὐκ ἄνευ σωμάτων ; De opif. 144",
            "(« natures intellectuelles et divines mais non incorporelles », formule d'Amand p. 88 ; De opif. 144",
        ),
    ),
    # --- synthesis_amand1945_tatian_no_carneadean_link (synthesis, risk=high) ---
    # FLAG: Quotations rendered without accents to match this description's existing unaccented
    #   French.
    "synthesis_amand1945_tatian_no_carneadean_link": (
        # tag: the epithet 'Tertullien des Grecs' is not in Amand's text; Amand does speak of
        #   Tatian's 'violente polemique' and 'passion et zele outre'
        (
            "Tatien est un 'Tertullien des Grecs' violent et fanatique qui puise son antifatalisme",
            "Tatien, dont Amand releve la 'violente polemique' et la 'passion et zele outre', puise son antifatalisme",
        ),
    ),
    # --- synthesis_destree2014_ch02_destree_plato_er (synthesis, risk=high) ---
    "synthesis_destree2014_ch02_destree_plato_er": (
        # tag: the vice-as-ignorance claim is at Timaeus 86d–e; 86b only opens the diseases-of-
        #   the-soul discussion
        ("(Tim. 86b)", "(Tim. 86d-e)"),
    ),
    # --- synthesis_destree2014_ch10_vimercati_panaetius (synthesis, risk=medium) ---
    "synthesis_destree2014_ch10_vimercati_panaetius": (
        # tag: the Nemesius chapter number could not be confirmed against De natura hominis
        (
            "(Némésius Nat. hom. 26 = Panaet. fr. B26 Vim.)",
            "(Némésius, Nat. hom. = Panaet. fr. B26 Vim. ; numéro de chapitre non vérifié)",
        ),
        # sentence ended mid-air before the stripped tag; final stop added
        (
            "la liaison oikéiôsis–prohaïrèsis–responsabilité",
            "la liaison oikéiôsis–prohaïrèsis–responsabilité.",
        ),
    ),
    # --- synthesis_destree2014_ch11_salles_epictetus_causal (synthesis, risk=high) ---
    "synthesis_destree2014_ch11_salles_epictetus_causal": (
        # tag: Cicero's cylinder simile proper is De Fato 42–43 (broader context 39–45); '40–44'
        #   is loose
        ("(De Fato 40-44)", "(De Fato 42-43)"),
    ),
    # --- synthesis_destree2014_ch13_zingano_alexander_character_action (synthesis, risk=medium) ---
    "synthesis_destree2014_ch13_zingano_alexander_character_action": (
        # tag: the precise '§§ 26-29' focus could not be confirmed; the character/liability
        #   material clusters around chs. 26-34
        (
            "Zingano se concentre sur les §§ 26-29 du De Fato d'Alexandre.",
            "Zingano se concentre sur les chapitres du De Fato d'Alexandre où se regroupe le matériau sur le caractère et la responsabilité (chap. 26-34).",
        ),
    ),
    # --- synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius (synthesis, risk=medium) ---
    # FLAG: All numeric counts and section lists were dropped as unverifiable; the tag's second
    #   complaint (page range 'p. 283-300' colliding with ch. 18 and the ch. 19-22 run) concerns
    #   metadata, not this prose, which gives p. 235-249.
    "synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius": (
        # tag: the quantified claims (four passages / a single occurrence elsewhere / 14
        #   occurrences in six passages) are unverifiable and likely overstated
        (
            "employée dans quatre passages du De Fato (§§ 23, 25, 39, 48) et une seule fois ailleurs, en Tusculanes 4.79 — c'est en revanche la iunctura in nostra potestate qui compte, selon Maso (p. 238 n. 10), 14 occurrences réparties en six passages du De Fato (§§ 9, 25, 31, 40, 41, 45).",
            "employée dans plusieurs passages du De Fato et attestée également en Tusculanes 4.79 ; Maso met en regard la iunctura in nostra potestate, plus fréquente que la première dans le De Fato (p. 238 n. 10).",
        ),
    ),
    # --- synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate (synthesis, risk=medium) ---
    # FLAG: Page locus removed entirely: the tag says it is unreliable but is truncated before
    #   giving a correct range.
    "synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate": (
        # tag: the page range 'p. 283-293' is self-flagged as approximate and contradicts the
        #   surrounding chapter ranges, so the unreliable locus is dropped while the chapter
        #   attribution stands
        ("(Bonazzi, p. 283-293)", "(Bonazzi)"),
    ),
    # --- synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview (synthesis, risk=medium) ---
    "synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview": (
        # tag: the editorial provenance (2007 Greek journal, preparation by Sauvé Meyer with
        #   Ierodiakonou) could not be independently confirmed
        (
            "Synthèse du ch. 22 (M. Frede, p. 351-363) : article paru en 2007 dans une revue grecque, réimprimé avec permission et préparé pour l'édition par Susan Sauvé Meyer (avec l'aide de Katerina Ierodiakonou). Thèses centrales",
            "Synthèse du ch. 22 (M. Frede, p. 351-363). Thèses centrales",
        ),
    ),
    # --- synthesis_dihle1982_indian_excursus_intellectualism_parallel (synthesis, risk=medium) ---
    "synthesis_dihle1982_indian_excursus_intellectualism_parallel": (
        # tag: 'Cary 2007' is not attested; Cary's relevant work on Augustinian introspection is
        #   Augustine's Invention of the Inner Self (2000)
        (
            "Cary 2007 a contre-argue",
            "Phillip Cary (Augustine's Invention of the Inner Self, 2000) a contre-argue",
        ),
    ),
    # --- synthesis_dihle1982_lec1_cosmology_second_century (synthesis, risk=medium) ---
    "synthesis_dihle1982_lec1_cosmology_second_century": (
        # tag: the exact quote 'no separate will spontaneously interferes' and the anchors p. 4
        #   / md ll. 178-181 could not be verified verbatim against the printed text — 'treat as
        #   paraphrase'; the surrounding French paraphrase already carries the claim
        (" ('no separate will spontaneously interferes', md ll. 178-181)", ""),
    ),
    # --- synthesis_dihle1982_lec2_greek_intellectualism_action (synthesis, risk=medium) ---
    # FLAG: The tag also notes the exact wording of the quotation is unverified; the formula is
    #   genuine, so only the page anchor was dropped.
    "synthesis_dihle1982_lec2_greek_intellectualism_action": (
        # tag: the page anchor 'p. 20' for the quotation could not be confirmed against the
        #   printed edition
        (
            "never developed a distinct concept of will' (p. 20).",
            "never developed a distinct concept of will'.",
        ),
    ),
    # --- synthesis_dihle1982_lec3_stoic_assent_cognitive (synthesis, risk=medium) ---
    # FLAG: SVF references dropped rather than corrected; they still need checking against SVF
    #   vol. III.
    "synthesis_dihle1982_lec3_stoic_assent_cognitive": (
        # tag: the SVF numbers '3.172, 3.548' could not be verified as von Arnim's actual
        #   numbers
        ("(asthenes synkatathesis, SVF 3.172, 3.548)", "(asthenes synkatathesis)"),
    ),
    # --- synthesis_frede2011_ch6_platonist_peripatetic_criticisms (synthesis, risk=medium) ---
    # FLAG: the tag is truncated before giving Frede's actual sentence, so the claim is
    #   paraphrased rather than re-quoted; the second quoted fragment ('in Alexander that we
    #   find the ancestor of the notion') was not flagged and is left as is
    "synthesis_frede2011_ch6_platonist_peripatetic_criticisms": (
        # tag: the single-quoted fragment is a compressed paraphrase presented as a verbatim
        #   quotation
        (
            "Alexandre 'is the only major ancient philosopher' dont la conception est fondamentalement viciée",
            "Alexandre serait le seul philosophe antique majeur dont la conception soit fondamentalement viciée (paraphrase résumée, non citation littérale)",
        ),
        # sentence ended mid-air before the stripped tag; final stop added
        (
            "critiquée par Ryle, Williams et Frede",
            "critiquée par Ryle, Williams et Frede.",
        ),
    ),
    # --- synthesis_furst2022_carneades_will_innovation (synthesis, risk=medium) ---
    # FLAG: The Schallenberg attribution was removed entirely (tag: phrase absent from Fürst
    #   2022); the mirror-parallel framing is lost with it.
    "synthesis_furst2022_carneades_will_innovation": (
        # tag: the claim that Schallenberg qualifies Carneades-Cicero as «libertarischer
        #   Kompatibilismus» is not attested in Fürst 2022 — the phrase occurs nowhere in it;
        #   only the unflagged Fürst-on-Origen label is kept
        (
            " Schallenberg qualifie Carnéade-Cicéron de « libertarischer Kompatibilismus » (parallèle miroir au « kompatibilistischer Libertarismus » que Fürst attribue à Origène)",
            " Fürst caractérise pour sa part la position d'Origène comme un « kompatibilistischer Libertarismus ».",
        ),
    ),
    # --- work_augustine_retractationes (work, risk=high) ---
    # FLAG: Tag truncated after 'De correptione et gratia,' - the full list of excluded anti-
    #   Pelagian treatises could not be reproduced; the Retract. II.66(92) locus given for the
    #   removed item was dropped as unverified.
    "work_augustine_retractationes": (
        # tag: De gratia et libero arbitrio is NOT among the 93 works reviewed, so only two of
        #   the three listed retractationes stand
        ("trois rétractations sont pivots", "deux rétractations sont pivots"),
        # tag: De gratia et libero arbitrio (426/427) is not reviewed in the Retractationes; the
        #   false item (c) is replaced by the tag's own statement about the Hadrumetum/Gaul
        #   anti-Pelagian treatises
        (
            " ; (c) *Retract.* II.66(92) — sur *De Gratia et Libero Arbitrio* (c. 426-427), traité de coordination anti-pélagienne.",
            ". Les traités anti-pélagiens adressés à Hadrumète et à la Gaule — dont le *De Gratia et Libero Arbitrio* (426/427) — ne figurent pas parmi les 93 œuvres passées en revue dans les *Retractationes*.",
        ),
    ),
    # --- work_basil_homiliae_quod_deus_non_est_auctor_malorum (work, risk=medium) ---
    "work_basil_homiliae_quod_deus_non_est_auctor_malorum": (
        # tag: the 'central formula' is not verbatim-attested in Basil (0 hits in TLG-E
        #   tlg2040); the Greek collocation is removed, the French gloss kept
        (
            " avec la formule centrale : τὸ ἐφ' ἡμῖν ἐστι τὸ αὐτεξούσιον (l'autonomie morale, voilà précisément le libre arbitre)",
            " où l'autonomie morale est présentée comme étant précisément le libre arbitre",
        ),
    ),
    # --- work_consolation_v_boethius_524ce_x4y5z6a7 (work, risk=high) ---
    "work_consolation_v_boethius_524ce_x4y5z6a7": (
        # tag: 'Historically false: Boethius' Latin Consolatio was unknown to the Arabic
        #   philosophical tradition; Avicenna and Averroes did not read Boethius. The
        #   foreknowledge/eternity problem was treated independen[tly]'
        (
            " and was transmitted to Islamic philosophy (Avicenna, Averroes)",
            "; the Latin Consolatio was, however, unknown to the Arabic philosophical tradition — Avicenna and Averroes did not read Boethius, and the foreknowledge/eternity problem was treated independently there",
        ),
    ),
    # --- work_de_fato_cicero_44bce_b9c4e5d2 (work, risk=medium) ---
    "work_de_fato_cicero_44bce_b9c4e5d2": (
        # batch marker converted to prose, keeping the real bibliographic locus
        (
            "[Enrichissement B3 — Amand 1945, p. 78-80, ll. 5131-5230] D'après Amand, le De Fato",
            "D'après Amand 1945 (p. 78-80), le De Fato",
        ),
    ),
    # --- work_exodus_c9d0e1f2 (work, risk=high) ---
    # FLAG: The node's period field still reads 'Second Temple Judaism' and needs changing
    #   separately; the tag is truncated before naming the replacement period.
    "work_exodus_c9d0e1f2": (
        # tag: the period 'Second Temple Judaism' is the reception context, not the work's
        #   period; Exodus is a Pentateuchal composition
        (
            "Second book of Torah narrating Israel's liberation from Egypt.",
            "Second book of the Torah, narrating Israel's liberation from Egypt; a Pentateuchal composition for which Second Temple Judaism is the reception context rather than the period of composition.",
        ),
    ),
    # --- work_ezekiel_g3h4i5j6 (work, risk=high) ---
    # FLAG: metadata.period still reads 'Second Temple Judaism'; the tag calls this a systemic
    #   bucketing issue shared with Exodus
    "work_ezekiel_g3h4i5j6": (
        # tag: Ezekiel is exilic (6th c. BCE), pre-Second-Temple
        (
            "Major prophetic book emphasizing individual moral responsibility.",
            "Major prophetic book of the exilic period (6th c. BCE) emphasizing individual moral responsibility.",
        ),
    ),
    # --- work_maximus_opuscula (work, risk=high) ---
    "work_maximus_opuscula": (
        # tag: the Tomus ad Marinum on the two wills is usually Opusc. 20 and the Marinus letter
        #   on the Spirit's procession is Opusc. 10; the Opusc. 16 identification is doubtful
        (
            "Opusculum 3, Opusculum 16 (on the Tomos to Marinus).",
            "Opusculum 3, and the Tomus ad Marinum on the two wills, usually identified as Opusculum 20 (the letter to Marinus on the procession of the Spirit being Opusculum 10).",
        ),
    ),
    # --- work_maximus_tyre_dissertation_13 (work, risk=medium) ---
    # FLAG: The node LABEL still carries '/ 19 (Dübner)'; only the description was in scope. Tag
    #   truncated at 'The Hobein ', so no replacement concordance was available.
    "work_maximus_tyre_dissertation_13": (
        # tag: the Hobein-13 = Dubner-19 equivalence is not confirmable from the standard
        #   concordances and needs verification, so the equivalence is removed from the prose
        (" = 19e (numérotation Dübner)", ""),
    ),
    # --- work_methodius_de_libero_arbitrio (work, risk=high) ---
    # FLAG: Tag truncated before naming De autexusio's actual adversaries, so the removed
    #   character could not be replaced by the correct one.
    "work_methodius_de_libero_arbitrio": (
        # tag: Aglaophon is the interlocutor of Methodius's De resurrectione, not of De
        #   autexusio/De libero arbitrio
        (
            "between three characters: Orthodox (ΟΡΘΟΔ.), Aglaophon (ΑΓΛΑΟΦΩΝ), and possibly Valentinus (ΟΥΑΛ.)",
            "between an orthodox speaker (ΟΡΘΟΔ.) and his adversaries, one of whom is possibly Valentinus (ΟΥΑΛ.)",
        ),
    ),
    # --- work_philo_de_opificio (work, risk=medium) ---
    # FLAG: The tag names no specific spurious reference and stops mid-sentence; rather than
    #   delete Greek that may well be correct, the assertion was hedged. A verbatim collation
    #   against Cohn-Wendland is still required.
    "work_philo_de_opificio": (
        # tag: the Greek phrases at §§69, 149, 156, 158, 167 are plausible but were not
        #   verbatim-verified, so the claim is hedged rather than left as an implicit verbatim
        #   quotation
        (
            "Editions: Cohn-Wendland vol. I (1896); Runia (Brill, 2001).",
            "Editions: Cohn-Wendland vol. I (1896); Runia (Brill, 2001). The Greek terms cited above are consistent with Philo's vocabulary but have not been collated verbatim against a critical edition.",
        ),
    ),
    # --- work_philo_de_providentia (work, risk=medium) ---
    # FLAG: The correct Cohn–Wendland volume for the Greek fragments is not recoverable from the
    #   truncated tag, so the reference was hedged rather than corrected; the Eusebius fragments
    #   (Praep. ev. VII, 21; VIII, 14) already in the prose remain the only concrete Greek
    #   witnesses cited.
    "work_philo_de_providentia": (
        # tag: the claim that Cohn–Wendland vol. VI (1915) prints the Greek fragments of De
        #   providentia is unconfirmed and probably inaccurate — vol. VI of the editio maior
        #   contains De Abrahamo / De Ioseph / De vita Mosis
        (
            "Édition de référence : Cohn-Wendland, vol. VI (Berlin, 1915) pour les fragments grecs ; Aucher 1822 pour la version arménienne intégrale.",
            "Édition de référence : Aucher 1822 pour la version arménienne intégrale ; le volume de l'édition Cohn-Wendland qui imprime les fragments grecs reste à préciser.",
        ),
        # batch marker converted to prose: the real bibliographic locus (Amand 1945, p. 80-95)
        #   is kept and attached to the sentence it documents; the internal line numbers are
        #   curation bookkeeping
        (
            "[Enrichissement B3 — Amand 1945, p. 80-95, ll. 5232-5917] D'après Amand (suivant Wendland 1892 et Bousset 1915)",
            "D'après Amand 1945, p. 80-95 (suivant Wendland 1892 et Bousset 1915)",
        ),
    ),
    # --- work_plutarch_de_communibus_notitiis (work, risk=medium) ---
    # FLAG: Tag #1 ('Resolved; remove the verification note') is ambiguous - it may mean the
    #   count was confirmed rather than corrected; the count was hedged rather than kept
    #   precise.
    "work_plutarch_de_communibus_notitiis": (
        # tag: the exact figure '50 chapitres' is unverified and probably too high; the treatise
        #   is conventionally divided into roughly 48-50 chapters
        (
            "Repugnantiis*, structuré en 50 chapitres.",
            "Repugnantiis*, structuré en une cinquantaine de chapitres.",
        ),
    ),
    # --- work_salles_stoics_determinism_2008 (work, risk=medium) ---
    # FLAG: node id and label still carry '2008'; metadata still omits year and publisher
    "work_salles_stoics_determinism_2008": (
        # tag: publication year is 2005 (Ashgate), not 2008 as the node id implies
        (
            "showing parallels and differences.",
            "showing parallels and differences. The monograph appeared as Ashgate, 2005, in the series Ashgate New Critical Thinking in Philosophy.",
        ),
    ),
    # --- work_tertullian_adv_marcionem (work, risk=medium) ---
    # FLAG: The contradiction is not resolved — the tag does not say which URN is correct, so
    #   the prose assertion was removed rather than corrected. A single catalogue-verified CTS
    #   URN under stoa0275 still has to be established for metadata.canonical_id.
    "work_tertullian_adv_marcionem": (
        # tag: description's 'stoa0275.stoa006' contradicts metadata.canonical_id
        #   'urn:cts:latinLit:stoa0275.stoa015'; both cannot be right, so the unverified URN is
        #   dropped from the prose
        (" CTS URN: stoa0275.stoa006.", ""),
    ),
}

# node_id -> pairs applied to `metadata.description_en` (the English reader field).
DESCRIPTION_EN_REWRITES: dict[str, tuple[tuple[str, str], ...]] = {
    "argument_carneades_autonomous_mental_causation_argument_4e7e9250": (
        # batch marker carrying no bibliography
        ("[Wave 7 initial summary] ", ""),
        # batch marker converted to a prose citation, locus preserved
        (
            "[B2 enrichment — Amand 1945, pp. 66-68, Intro §II.III.IV] Amand reconstructs Carneades' 'direct' anti-fatalist polemic as a technical discussion of the Chrysippean doctrine of εἱμαρμένη.",
            "Amand reconstructs Carneades' 'direct' anti-fatalist polemic as a technical discussion of the Chrysippean doctrine of εἱμαρμένη (Amand 1945, pp. 66-68, Intro §II.III.IV).",
        ),
    ),
    "concept_pithanon_8f3a6d2c": (
        # batch marker carrying no bibliography
        ("[Wave 7 initial summary] The plausible", "The plausible"),
        # batch marker converted to a prose citation, locus preserved
        (
            "[B2 enrichment — Amand 1945, pp. 44-45, Intro §II ch. II §III] Amand characterises",
            "Amand (1945, pp. 44-45, Intro §II ch. II §III) characterises",
        ),
    ),
    "debate_stoic_academic_hellenistic": (
        # batch marker carrying no bibliography
        ("[Wave 7 initial summary] The central", "The central"),
        # batch marker converted to a prose citation, locus preserved
        (
            "[B2 enrichment — Amand 1945, pp. 41-43 and 46-48, Intro §II ch. II] Amand characterises",
            "Amand (1945, pp. 41-43 and 46-48, Intro §II ch. II) characterises",
        ),
        # internal batch cross-reference reworded
        (
            "(the 6 argument-titles reconstructed in the Conclusion = the B1 batch material)",
            "(the 6 argument-titles reconstructed in Amand's Conclusion)",
        ),
    ),
    "person_carneades_214_129bce_l2m3n4o5": (
        # batch marker carrying no bibliography
        ("[Wave 7 initial summary] Carneades of Cyrene", "Carneades of Cyrene"),
        # graph-internal aside, mirrors the French description edit
        (
            " (Disagreement encoded via disagrees_with / interprets edges linking this node to the Bobzien and Amand nodes.)",
            "",
        ),
        # batch marker converted to a prose citation, locus preserved
        (
            "[B2 enrichment — Amand 1945, pp. 41-46, Intro §II ch. II §I-III] Amand emphasises",
            "Amand 1945, pp. 41-46 (Introduction §II ch. II §I-III), emphasises",
        ),
    ),
    "person_favorinus_of_arles_9n4o6q32": (
        # batch marker carrying no bibliography
        ("[Wave 7 — note] Favorinus is primarily", "Favorinus is primarily"),
        # batch marker converted to a prose citation, locus preserved
        (
            "[B3 enrichment — Amand 1945, p. 96-100, ll. 5919-6128] On Amand's reading",
            "On Amand's reading (1945, p. 96-100, ll. 5919-6128)",
        ),
    ),
    "synthesis_amand1945_ch3_moral_argument_scheme_announcement": (
        # internal batch cross-reference dropped
        ("(= the 6 argument-titles of batch B1)", "(the 6 argument-titles)"),
        # batch label dropped, pointer kept
        (
            "see B1 nodes argument_carneadean_*_amand1945",
            "see the argument_carneadean_*_amand1945 nodes",
        ),
        # editorial directive addressed to the curator
        (
            " Explicitly NOT to be duplicated with B1: this Ch. III node is a structural gateway, B1 is the detailed development with witnesses.",
            "",
        ),
    ),
}

# node_id -> pairs applied to the node `label`.
LABEL_REWRITES: dict[str, tuple[tuple[str, str], ...]] = {
    "synthesis_amand1945_ch3_moral_argument_scheme_announcement": (
        # plan: drop the ' = B1' curation suffix from the label
        (" = B1)", ")"),
    ),
    "concept_pneumatic_causation_stoic_bobzien": (
        # tag: the monograph is standardly cited as 1998; the description was corrected
        #   accordingly
        ("Bobzien 2001", "Bobzien 1998"),
    ),
    "work_maximus_tyre_dissertation_13": (
        # tag: the Hobein-13 = Dübner-19 equivalence is unconfirmed; removed from the
        #   description, so removed from the label too
        ("Dissertation 13 (Hobein) / 19 (Dübner) — ", "Dissertation 13 (Hobein) — "),
    ),
}

# node_id -> metadata operations explicitly demanded by a [Vérif.] tag.
# Deliberately narrow: only unambiguous, purely destructive corrections. Every other
# metadata-level defect the tags report is listed as a follow-up in
# data/audit/2026-08-14_curation_artifact_cleanup_applied.md instead.
METADATA_FIXES: dict[str, tuple[dict, ...]] = {
    "scholar_harl_m": (
        # tag: 'Harl is not a co-editor of SC 7bis Homélies sur la Genèse. Remove this list
        #   element.'
        {
            "key": "key_works",
            "op": "list_remove",
            "value": "Origène, Homélies sur la Genèse — SC 7bis (Cerf 1976, avec Doutreleau)",
        },
    ),
}
