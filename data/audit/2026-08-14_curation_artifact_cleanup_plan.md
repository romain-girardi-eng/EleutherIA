# Curator-artifact cleanup plan — `data/kg/nodes.jsonl`

**Date:** 2026-08-14 · **Machine-readable plan:** `data/audit/2026-08-14_curation_artifact_cleanup_plan.jsonl` (one line per node + a trailing summary object)

> **No data file was modified.** `data/kg/nodes.jsonl` and `data/kg/edges.jsonl` were read only. Per the house rule, nothing here may be applied in bulk: **each of the 284 lines is an individual decision** for a human/orchestrator.

---

## 1. Scope

284 nodes carry curator-artifact text in reader-facing fields. Issue tallies (a node can carry several):

| issue code | nodes |
|---|---|
| `verif_tag` | 244 |
| `avertissement_boilerplate` | 33 |
| `phase_tag` | 33 |
| `wave_tag` | 9 |
| `curator_prose` | 6 |
| `batch_ref` | 3 |
| `placeholder` | 2 |

Risk split: **83 high**, **180 medium**, **21 low**.

## 2. Corrections to the prior audit

Three of the prior audit's claims did not survive verification against the file:

1. **Category B is not "9 nodes with a bare `(Phase 12)` tag".** All 9 carry a *second* full boilerplate paragraph — `Avertissement conceptuel — anachronisme du « libre arbitre »` — 808 characters, byte-identical in 8 of the 9; `synthesis_cic_fat_in_nostra_potestate` carries the same text without the `**` bold markers. This matters: the strip span is a whole paragraph, not a 10-character marker.
   *And that boilerplate is itself wrong*: it attributes to Dihle 1982 the location of the "invention of free will" in **Origen**, whereas Dihle locates it in **Augustine** (flagged by the node's own `[Vérif. 2026-08-02]` on `argument_tatian_freewill_paradox`). It also states the contested modern "invention of the will" paradigm as plain fact. Strip it — do not preserve it in reworded form.
2. **The PLACEHOLDER category is mostly a false positive.** 4 of the 6 hits are Richard Double's own technical term — a *placeholder definition* of "free choice", neutral between competing theories (`scholarly_argument_double_definition_of_free_will_free_c_2`, `scholarly_argument_double_placeholder_definition_of_free_3`, `scholar_double_r`). Those are legitimate scholarship and are **excluded** from this plan. `passage_alcin_alcinous_untitled_full_text`'s note ("previous value was a fake placeholder") is legitimate provenance and should be kept. Only the Fee node's label is a genuine curation placeholder.
3. **`argument_carneadean_general_theme_amand1945` is not a batch-tagged node.** Its "résumé initial" is Amand's own description of Ps.-Chrysostom's Discourse V ("résumé initial et récapitulation finale"). Excluded.

## 3. `[Vérif.]` tag classification (289 tags across 244 nodes)

Every tag was read and classified individually; nothing was defaulted to "strip".

| class | tags | what it means for the fix |
|---|---|---|
| `confirms_ok` | 41 | verification passed or the note is superseded — the tag alone comes out, prose untouched |
| `flags_spurious_reference` | 119 | the tag says a citation, locus, page range, Greek term or attribution is unidentifiable / spurious / unattested. **Stripping the tag alone would leave the bad citation standing in the prose** — the reference itself must be removed or reworded |
| `corrects_content` | 113 | the tag *carries* the corrected fact. It must be merged into the prose before the tag is stripped, or the correction is lost |
| `other` | 16 | interpretive caveats, truncated/garbled fields, or self-referential notes — no mechanical rule applies; the full tag is quoted in the plan line |

**Only 41 of 289 tags are strip-safe, and 5 of those are not deletable either** — `argument_irenaeus_recapitulation_theodicy`, `argument_wager_alex`, `concept_exousia_alex`, `concept_platonic_vs_christian_original_sin`, `concept_practical_life_alex` carry the TLG-E collation evidence that underwrites the node's Greek. Those move to `metadata.verification_note` rather than being deleted.

## 4. Sanity checks

- **Boilerplate byte-identity (A):** confirmed. One distinct 808-char string across all 24 nodes. 23 sit at offset 0; **`concept_ananke_necessity_democritus_h8i9j0k1` is the exception** — the paragraph starts at offset 302, after a substantive `**Étymologie**` paragraph that must be preserved, so the strip span there includes the *preceding* `\n\n`, not the following one.
- **Boilerplate byte-identity (B):** confirmed for 8/9; one unbolded variant (above).
- **Nothing legitimate is removed by a strip.** Re-running the proposed strips over all 284 nodes leaves a minimum remainder of 18 characters (`scholarly_work_pouderon_2003_aristide_apologie` → `Aristide. Apologie`). The ten shortest remainders are all bibliographic work/scholar nodes whose description is only a title. No ancient-text or argumentative content is lost anywhere.
- **No Greek or Latin is silently discarded.** Every tag containing Greek/Latin or a TLG collation is classed `corrects_content`, `flags_spurious_reference`, or routed to metadata — never a bare strip.
- **Deletion candidates were checked against `edges.jsonl` first** (counts and edge types recorded in the plan lines).

## 5. High-risk lines — 83, each needs individual review

High risk = the fix changes what the node asserts, or deletes the node. Every line below carries a `post_excerpt` field in the JSONL showing the first 100 characters of what survives.

| node_id | type | why it is high-risk |
|---|---|---|
| `argument_adversity_exercise_seneca_g8h9i0j1` | argument | The pivot maxim 'Marcet sine adversario virtus' is at De Prov 2.4 in Reynolds' OCT and Basore's Loeb, not 2.3; the node anchors it to passage_sen_prov_2_3. Edition number |
| `argument_arts_efficacy_alex` | argument | Audit note superseded: the flag is confirmed and now acted on. ; The seven source ids passage_alex_fat_559 ... passage_alex_fat_565 are dangling: no such passage nodes ex |
| `argument_cafma_character_contradiction_1f6g8i54` | argument | 'Cicero, De Fato 28-33' is the lazy-argument section, not the anti-astrology section. For a natal-astrology refutation the relevant loci are De Fato §§11-17 and, for Carn |
| `argument_cafma_futility_of_effort_8c3d5f21` | argument | this is not simply the ἀργὸς λόγος. The lazy argument (Cicero, De Fato 28-30) concludes 'then do not call the doctor' and is the fatalist sophism Chrysippus rebutted with |
| `argument_cleanthes_hymn_to_zeus_argument_f71f5b37` | argument | Premise P4 'ducunt volentem fata, nolentem trahunt' is Seneca's own Latin coda (Ep. 107.11), not a line of Cleanthes; presenting it as a premise of Cleanthes' argument is |
| `argument_four_categories_alex` | argument | Bruns 207-208 is not the locus of τὸ ἐφ' ἡμῖν. Occurrence-mapping of 'τὸ ἐφ' ἡμῖν' across De Fato in TLG 0732 shows a dense cluster at Bruns ~179-186 (chs. 11-15) and onl |
| `argument_gerson_2014_plotinus_qualified_moral_responsibility_against_strawson` | argument | CONFIRMÉ sur le volume (extraction locale du PDF Destrée–Salles–Zingano 2014). Gerson est bien le 16e des 22 contributions ; titre : « Moral responsibility and what is 'u |
| `argument_origen_anti_astrological` | argument | Locus imprecision: the specifically anti-astrological arguments (Gen 1:14 'signs not causes'; the Jacob/Esau twin argument) belong to Origen's Commentary on Genesis III / |
| `argument_origen_argos_logos` | argument | Characterization slippage: Contra Celsum II.20 is primarily the 'foreknowledge/prophecy does not necessitate' passage (Jesus's prediction of Judas's betrayal does not com |
| `argument_plutarch_providence_cooperation_8c5a9d3f` | argument | The tripartite-providence doctrine occurs only in the pseudonymous De Fato (correctly signalled 'Pseudo-Plutarch' in the label), yet formulator is set to 'Plutarch'. De S |
| `argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945` | argument | RÉSOLU sur le texte d'Amand (extraction locale). L'argumentation (8e argument), les comparaisons du gouffre et de la maîtresse barbare, le pardon des ennemis, la question |
| `argument_qumran_predestination_c3d4e5f6` | argument | Jörg Frey's foundational essay on modified Qumran dualism is 'Different Patterns of Dualistic Thought in the Qumran Library' (1997, STDJ 23), not 1999; the 1999 date coul |
| `argument_spontaneity_within_determination_13fcd224` | argument | Misattribution at premise level. P1 is a verbatim translation of Spinoza's Ethica I, Definition 7 (and P2-P3 are Spinoza's absolute-freedom / adequate-vs-inadequate-ideas |
| `argument_tatian_freewill_paradox` | argument | The anachronism-warning note misattributes the scholarly thesis. Dihle (The Theory of Will in Classical Antiquity, 1982) locates the invention of the concept of will in A |
| `concept_autokrateia_alex` | concept | The head-term αὐτοκράτεια (and αὐτοκρατής) is unattested in the entire Alexander corpus (0 TLG hits), so labelling this an Alexandrian term is a misattribution. Head term |
| `concept_axia_biblos_tou_theou_origen_amand1945` | concept | This stored note falsely asserts the phrase is unattested ('No hit in any form in TLG … incl. Origen TLG2042'). In fact τὰ σημεῖα τοῦ θεοῦ IS attested in Origen (TLG2042, |
| `concept_bechirah_c1d2e3f4` | concept | Minor precision: Maimonides' own term in Hilkhot Teshuvah 5:1 is reshut (רשות, 'permission/authority'); 'bechirah ḥofshit' is the standard modern-Hebrew label rather than |
| `concept_belial_demonic_source_of_sin` | concept | Chronology is miscoded. Belial in the Qumran sectarian scrolls (CD, 1QM, 1QS) is Second Temple / Hellenistic (2nd c. BCE–1st c. CE). The top-level period field 'Late Anti |
| `concept_bondage_of_will_1c5x6y24` | concept | Minor characterization: 'irresistible grace' is TULIP/later-Reformed vocabulary; Luther speaks of the enslaved will freed by grace and of the 'beast ridden by God or Sata |
| `concept_boule_practical_wisdom` | concept | Minor: the division of the rational soul into βουλευτικόν and ἐπιστημονικόν is primarily Aristotle NE VI.1 (1139a11-15, logistikon=bouleutikon vs epistēmonikon); attribut |
| `concept_concupiscence_epithumia_transmitted_bd8e2fc9` | concept | Audit note half-superseded: παρακοή IS confirmed verbatim; only κηλῖδας κακίας fails. ; ἐπιθυμία is not Methodius' technical term for a transmitted post-lapsarian desire. |
| `concept_conditional_fate_9a5c8b4d` | concept | la forme compressée « εἱμαρμένη ἐξ ὑποθέσεως » est une abréviation moderne (0 occurrence). Le terme antique est bien ἐξ ὑποθέσεως, appliqué à la εἱμαρμένη par [Plutarque] |
| `concept_four_categories_alex` | concept | les quatre expressions grecques sont authentiques et toutes présentes chez Alexandre ; la classification quadripartite elle-même est une reconstruction de Sharples 1983,  |
| `concept_gnomic_will_gnome` | concept | The enumeration of the many senses of γνώμη is set out chiefly in Opusculum 14 (PG 91:151C–153A); attaching the '28 senses' claim specifically to Disp. Pyrr. PG 91:312B–C |
| `concept_heimarmene_conditional_amand1945` | concept | Minor authorship note: the Didaskalikos is now generally ascribed to Alcinous rather than Albinus (Whittaker 1990). The node follows Amand's 1945 identification ('Albinus |
| `concept_horme_alex` | concept | RÉSOLU par dépouillement de ὁρμή/προαίρεσις dans le De fato (TLG0732). La définition de la proaíresis est en Bruns ~179 (De fato 11) : « ἡ γὰρ ἐπὶ τὸ προκριθὲν ἐκ τῆς βου |
| `concept_hypothetical_fate_middle_platonist` | concept | Very minor: the ps.-Plutarch De Fato begins at Stephanus 568B, not 568A (568A closes the preceding treatise). Not worth a hard correction. |
| `concept_metriopatheia_moderation_passions` | concept | ἐθισμὸς ἄλογος est inattesté dans tout le TLG (0 occurrence) et a été retiré ; le vocabulaire de Galien pour la partie non rationnelle est ἡ ἄλογος δύναμις (PHP). μετριοπ |
| `concept_occasionalism_a5b6c7d8` | concept | Minor: period is set to 'Early Modern', but the doctrine described is substantially medieval (Ash'arite kalām: al-Ash'arī d.936, al-Ghazālī d.1111). The node correctly co |
| `concept_original_sin` | concept | Broken correction record: the 'unattested → attested' pair is identical on both sides ('προπατορικὴ ἁμαρτία → προπατορικὴ ἁμαρτία'), conveying no correction. The genuine  |
| `concept_patet_exitus_seneca_e6f7g8h9` | concept | Minor citation imprecision: the Stoic doctrine/term 'εὔλογος ἐξαγωγή' as such is defined at Diog. Laert. VII.130. DL VII.28 and VII.176 report the (self-inflicted) deaths |
| `concept_perfect_vs_antecedent_causes_8w3x5z21` | concept | Broken record: 'unattested «αὐτοτελὲς αἴτιον» → attested «αὐτοτελὲς αἴτιον»' is identical on both sides. In fact αὐτοτελὲς αἴτιον IS attested (Clement Strom.; Ps.-Galen D |
| `concept_pithanon_8f3a6d2c` | concept | The tripartite technical criteria (πιθανή / ἀπερίσπαστος / διεξωδευμένη-περιωδευμένη) are canonically reported by Sextus Empiricus, Adv. Math. 7.166–184, NOT by Cicero, A |
| `concept_thelesis_willing_87d2b3cf` | concept | Overstated: the common LXX word for will is θέλημα (frequent), while θέλησις is rare in the LXX (Prov, Eccl, 2 Chr, Wisdom). 'preferred θέλησις over βούλησις' should be s |
| `concept_tripartite_descent_iamblichus` | concept | Label/description mismatch. The label 'Tripartite Descent Typology' points to Iamblichus's threefold classification of the MODES of descent (souls descend for salvation o |
| `concept_voluntas_y7z8a9b0` | concept | Could not verify 'voluntas recta' at Seneca Ep. 71.36. The locus for wisdom as consistent right willing ('semper idem velle atque idem nolle… ut rectum sit quod velis') i |
| `passage_alcin_alcinous_untitled_full_text` | passage | label says Alcinous, *Didaskalikos* 1 but the 8.2k-char payload is Eusebius/Hegesippus on James the Just — label/payload mismatch, escalate separately |
| `passage_eusebius_he_iv_26_melito_fr_iv` | work | RÉSOLU par lecture du fichier de preuve sur disque (SC31_Melito_Sardensis_Fragments_IV…bilingue.txt). Le texte réellement porté par ce nœud est le seul paragraphe d'Eus., |
| `person_boethius_480_524ce_w3x4y5z6` | person | Overreach / factual error: Boethius did not 'deeply influence Islamic philosophy.' His Consolatio and logical works belong to the Latin tradition and were not transmitted |
| `person_cyril_alexandria` | person | formule grecque authentifiée mot pour mot dans le TLG (Glaphyres sur la Genèse I.4, PG 69, 24-25), mais unique — le qualificatif « récurrent » a été corrigé. La distincti |
| `person_cyril_jerusalem_315_386` | person | The anti-fatalist / anti-astrological argument is located in Catechesis IV (esp. §18-21, the self-determined soul, sin not from the stars), NOT Catechesis XIII. Cat. XIII |
| `person_cyrus_alexandria_d641` | person | Chronology of the dismissal is muddled: Cyrus was summoned/disgraced by Heraclius in 640-641 (before Heraclius's death) for negotiating with the Arabs, then rehabilitated |
| `person_julian_eclanum_d454` | person | The works list double-counts a single work: 'To Florus' (Ad Florum) IS the eight-book polemic against Augustine, so 'Eight books against Augustine (mostly lost)' is the s |
| `person_methodius_olympus_d311` | person | The TLG URN 'TLG 2959.001' is assigned to De autexusio, but 2959.001 is the Symposium (Convivium decem virginum); De autexusio (De libero arbitrio) is TLG 2959.002. The n |
| `person_rene_descartes_1aa22692` | person | The Latin tag 'infimus gradus libertatis' ("lowest degree of freedom") is from Meditatio IV (AT VII 58: 'indifferentia illa ... est infimus gradus libertatis'), NOT from  |
| `sc123_melito_apologia_ad_antoninum` | work | Minor: the excerpt itself (verified in the local SC-31 text) names Hadrian as the addressee's grandfather and Antoninus Pius as his father, which identifies the addressee |
| `sc123_melito_de_anima_et_corpore` | work | The Melitonian authorship of the De anima et corpore homily is disputed in scholarship (widely regarded as spurious / a later Melitonian homily), not the settled fact the |
| `sc379_athenagoras_legatio` | work | Minor: the Legatio has 37 chapters; metadata records 38. Not in the displayed description. |
| `scholar_harl_m` | person | Marguerite Harl did not co-edit SC 7bis (Homélies sur la Genèse). That volume is Doutreleau (Latin text, trans., notes) with an introduction by de Lubac and Doutreleau. H |
| `scholar_list_n` | person | This field conflates two different scholars. Fürst 2022 discusses CHRISTIAN List (LSE philosopher, Why Free Will Is Real 2019 / Warum der freie Wille existiert 2021, 'com |
| `scholar_position_karamanolis_early_christian_engagement` | argument | Minor imprecision. 'Epektasis' (perpetual progress toward God, from Phil 3:13) is distinctively Gregory of Nyssa's doctrine, not a shared Cappadocian tenet, and it is a b |
| `scholar_wolfson_h` | person | Work/date mismatch. The node links scholarly_work 'wolfson_1947_philo_on_free_will_and_the_historical_influence', but that title and the pagination (131-169 / at 133-134) |
| `scholarly_argument_crouzel_manuscript_tradition_and_textu_1` | argument | scholar_id points to scholar_crouzel_henri, but the cited textual-critical section is Simonetti's; attribution should be to Manlio Simonetti. SC 312's Avant-Propos: 'Ce t |
| `scholarly_argument_f_rst_origen_s_metaphysics_of_freedo_5` | argument | Minor/soft: 'De principiis I.3.8 (God as spirit and movement)' — I.3 is 'De Spiritu Sancto' (participation in the Holy Spirit); Origen's 'God is spirit' (John 4:24, deus  |
| `scholarly_argument_fee_determinism_and_predestination_1` | argument | self-described extraction artifact (« Ce nœud est un artefact d'extraction et devrait être supprimé du graphe »); label is a `(placeholder …)` marker — **deletion candidate** |
| `scholarly_argument_gourinat_chrysippus_s_compatibilism_0` | argument | The linked work node is slugged 'scholarly_work_gourinat_0_responsabilit_morale_et_destin_une_r_pon', which attributes this article to Gourinat. The source file confirms  |
| `scholarly_argument_gourinat_cicero_s_critique_of_chrysippu_2` | argument | Same misattribution as the sibling node: scholarly_work_id 'scholarly_work_gourinat_0_...' names Gourinat as author of an article actually written by Olivier D'Jeranian ( |
| `scholarly_argument_gourinat_epictetus_s_original_contribut_1` | argument | scholarly_work_id 'scholarly_work_gourinat_0_...' misattributes this D'Jeranian article to Gourinat (source file confirms author = Olivier D'Jeranian). Node label/scholar |
| `scholarly_argument_gourinat_the_anti_fatalist_objection_an_4` | argument | The argument is correctly attributed to the FIGURE D'Jeranian (label + scholar_id scholar_djeranian_o), but the scholarly_work_id 'scholarly_work_gourinat_0_responsabilit |
| `scholarly_argument_gourinat_the_cylinder_analogy_and_its_l_3` | argument | Same provenance issue as node _4: D'Jeranian's article (scholar_djeranian_o) is filed under scholarly_work_id 'scholarly_work_gourinat_0_...' and a 'gourinat'-prefixed no |
| `scholarly_argument_grant_origen_s_self_castration_and_a_0` | argument | The ZKG 71 (1960) study on Origen's life is by Manfred (M.) Hornschuh, not 'G. Hornschuh'. Grant's own footnote 4 as OCR'd reads 'G. Horaschuh', so the KG faithfully copi |
| `scholarly_argument_l_hr_clement_of_alexandria_s_adapta_2` | argument | The author of 'Gnostic Determinism Reconsidered' (VC 46, 1992) is Winrich A. Löhr; the filename renders him 'Alfried Löhr' (his middle name Alfried used as first name). T |
| `scholarly_argument_l_hr_clement_s_use_of_stoic_concept_3` | argument | Same author-name issue as the sibling node: the VC 1992 article is by Winrich A. Löhr; the filename reads 'Alfried Löhr'. Cosmetic, in the path only; scholar_id scholar_l |
| `scholarly_argument_linjamaa_free_will_and_moral_accountabi_1` | argument | Stance label 'critiques' toward Origen is the wrong direction: Linjamaa situates TriTrac as one of the determinist targets whom Origen polemicized against (De Principiis  |
| `scholarly_argument_meyer_epicurean_freedom_from_determi_4` | argument | reader-facing prose contains a `[Re-scopé 2026-08-03 : …]` curation changelog that also carries the node's corrected scope (Meyer never advances the swerve thesis) |
| `scholarly_argument_pouderon_resurrection_and_moral_account_3` | argument | page_range 62-67 of the monograph is the section 'L'authenticité du Traité sur la résurrection' (introduction/authenticity), not where Pouderon analyzes the Traité's just |
| `scholarly_argument_rousseau_marcus_s_deterministic_numerol_2` | argument | RÉSOLU par collation de SC 264 (texte et traduction, extraction locale). Loci I.14-16 confirmés (capitula ch. X « per numeros et per syllabas », titre courant « Marc le M |
| `scholarly_argument_telfer_new_testament_and_autexousia_7` | argument | The trailing clause 'though Paul does not use the term αὐτεξούσιος itself' is an editorial addition NOT found in Telfer's article, which does not single out Paul here. It |
| `scholarly_argument_wolfson_comparison_with_plato_s_timaeu_3` | argument | Several Timaeus loci diverge from Wolfson's own footnotes (nn. 20-27, p. 134): Wolfson cites the rational/irrational souls at 'Tim. 42E ff.; 69C' (node has 69C-72D), the  |
| `synthesis_amand1945_cicero_ch2i_cadre` | synthesis | Two soft points not supported by Amand as stated. (1) The node lists the possible source as 'Antiochus of Ascalon OR Posidonius'; Amand's candidates (following Lörcher 19 |
| `synthesis_amand1945_hierocles_bizarre_carneadean_inversion` | synthesis | Editorial overreach. Amand says only that Hierocles's developments 'rappellent singulièrement' Origen's effort (a striking resemblance); he does not assert, and the sourc |
| `synthesis_amand1945_origen_pivot_witness` | synthesis | Count/membership error: text says « 6 témoins » but lists 7 items. Amand's six principal 'textes témoins' of the Carneadean moral argument are Cicéron, Philon, Favorinus  |
| `synthesis_amand1945_tatian_no_carneadean_link` | synthesis | The epithet 'Tertullien des Grecs' (in quotes, framed as Amand's characterization) is NOT found in Amand's text. Amand does describe Tatian's 'violente polémique' and 'pa |
| `synthesis_destree2014_ch02_destree_plato_er` | synthesis | Minor locus imprecision: the 'no one is voluntarily wicked' / vice-as-ignorance claim in the Timaeus is at 86d–e (86b only opens the diseases-of-the-soul discussion). Con |
| `synthesis_destree2014_ch11_salles_epictetus_causal` | synthesis | Minor locus imprecision: Cicero's cylinder simile proper is De Fato 42–43 (broader context 39–45); '40–44' is slightly loose but acceptable. |
| `work_augustine_de_correptione` | work | CSEL 92 attribution unverified and probably wrong: CSEL 92 (Folliet 2000) contains De perfectione iustitiae hominis, De gestis Pelagii, De gratia Christi et de peccato or |
| `work_augustine_retractationes` | work | De gratia et libero arbitrio (426/427) is NOT among the 93 works reviewed in the Retractationes. The anti-Pelagian treatises to Hadrumetum/Gaul (De gratia et libero arbit |
| `work_consolation_v_boethius_524ce_x4y5z6a7` | work | Historically false: Boethius' Latin Consolatio was unknown to the Arabic philosophical tradition; Avicenna and Averroes did not read Boethius. The foreknowledge/eternity  |
| `work_exodus_c9d0e1f2` | work | Period tagged 'Second Temple Judaism', but Exodus is a Pentateuchal/pre-exilic-to-Persian composition set in the 2nd millennium BCE — Second Temple (516 BCE–70 CE) is the |
| `work_ezekiel_g3h4i5j6` | work | Period tagged 'Second Temple Judaism' though Ezekiel is exilic (6th c. BCE, pre-Second-Temple). Same systemic bucketing note as Exodus — minor, not a description-level er |
| `work_maximus_opuscula` | work | The Opusculum-16 identification is doubtful: the 'Tomus ad Marinum' on the two wills is usually Opusc. 20, and the letter to Marinus on the Spirit's procession is Opusc.  |
| `work_methodius_de_libero_arbitrio` | work | Character conflated with a different work: Aglaophon is the eponymous interlocutor of Methodius's De resurrectione (subtitled 'Aglaophon'), not of De autexusio/De libero  |
| `work_ps_clement_homiliae` | work | Internal loci not independently confirmable and likely imprecise. The fuller nomima barbarika / Book-of-the-Laws-of-Countries (Bardaisan) argument is Recogn. IX.19–29; th |

### The one deletion proposal

`scholarly_argument_fee_determinism_and_predestination_1` — label `Fee on Romans 8:28-30 (placeholder — no argument on determinism)`.
The description says in plain French that the node is an extraction artifact and should be removed from the graph. Fee, *God's Empowering Presence* (1994), pp. 587-591 does treat Rom 8:28-30, but only on the grammatical subject of συνεργεῖ; he advances no thesis on determinism or predestination.

**Edges to reconcile first — 3:**

- `-created_by->scholar_fee_g`
- `scholarly_work_fee_1994_god_s_empowering_presence_the_holy_spiri-discusses->`
- `-advanced_in->scholarly_work_fee_1994_god_s_empowering_presence_the_holy_spiri`

Alternative if deletion is refused: keep it as a documented **negative finding** (Fee does *not* argue determinism here — useful in a corpus that maps who says what), drop the curator sentence, and rewrite the label without the `(placeholder …)` marker.

### Escalation, out of scope for this cleanup

`passage_alcin_alcinous_untitled_full_text` is labelled *Alcinous, Handbook of Platonism (Didaskalikos), Didasc. 1*, but its 8,218-character payload is Eusebius / Hegesippus on James the Just. The label and the text do not match. This is a corpus-integrity problem, not a curation-artifact one — it needs its own verification pass.

## 6. Suggested order of work

1. **21 low-risk lines** — pure strips (boilerplate paragraphs, `confirms_ok` tags with no Greek). Still one commit per reviewed batch, never a blind sweep.
2. **180 medium-risk lines** — mostly `flags_spurious_reference` (delete or reword the bad citation) plus bibliographic-metadata corrections (co-authors, DOIs, publishers, years) and the `wave_tag` / `batch_ref` markers.
3. **83 high-risk lines** — one at a time, each verified against the source before the correction is merged. Where the tag cites the local library (`~/Desktop/DOCTORAT/…`) or TLG-E, re-verify there rather than trusting the tag.

A caution on `wave_tag` nodes: the `[Enrichissement B2 — Amand 1945, p. 66-68, Intro §II.III.IV]` brackets look like batch markers but contain a **real bibliographic locus**. Convert them to normal prose citations; do not delete the bracket wholesale.
