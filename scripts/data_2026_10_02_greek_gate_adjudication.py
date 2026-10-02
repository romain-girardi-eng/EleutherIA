#!/usr/bin/env python3
"""Decisions on the 56 Greek runs that fail ``check_greek_gate.py --all``.

All 56 sit in metadata copied from modern scholarship (53 in
``quote_verbatim``, which is a byte copy of the thesis-fonds extraction and
must not be edited; one in ``supporting_evidence``; two in the record of an
earlier audit). None is in the gate baseline, and the same 56 failed on
34ea208, before the 2026-09-24 verification.

Each run was searched letter by letter (accents, breathings, case, spaces and
punctuation ignored, final sigma folded) in the TEI of a critical edition.
Categories:

``verified``     the letters of the run occur, in order, in the named edition;
                 the only differences are those of the PDF extraction (lost
                 word spaces, apostrophe forms, accents dropped by OCR).
``composite``    two quotations or lemmas fused by the extraction; each part
                 is checked separately.
``ocr_damaged``  the scholar quotes a passage that is in the named edition,
                 but the extraction of an old printed article mangled the
                 letters; the run is not certified as Greek text, and the node
                 receives an English note naming the passage.
``scholar_greek`` Greek written by the scholar (a label, a list of terms, a
                 paraphrase, a modern title), not a quotation of an ancient
                 text; recorded as such so it is never cited as one.
``needs_romain`` the source could not be reached here (TLG E, Cyril's Contra
                 Iulianum, Stobaeus, the Acts of 553, Trelenberg's Tatian);
                 left failing, with the check to run.

Tuple: (node_id, run_hash, category, tei_file or None, checks, source)
``checks`` lists the fragments of the run whose letters must be found in
``tei_file`` at apply time (None = the whole run, split on ellipses).
TEI paths are relative to a directory holding checkouts of
OpenGreekAndLatin/canonical-greekLit (commit bcc5df0) and
OpenGreekAndLatin/First1KGreek (commit 8ee111e).
"""

CG = "canonical-greekLit/data/"
F1 = "First1KGreek/data/"

ALEX_FAT = F1 + "tlg0732/tlg014/tlg0732.tlg014.1st1K-grc1.xml"
ALEX_MIXT = F1 + "tlg0732/tlg001/tlg0732.tlg001.1st1K-grc1.xml"
ALEX_MANT = F1 + "tlg0732/tlg011/tlg0732.tlg011.1st1K-grc1.xml"
PS_ALEX_FEBR = F1 + "tlg0732/tlg003/tlg0732.tlg003.1st1K-grc1.xml"
ARIST_PHYS = F1 + "tlg0086/tlg031/tlg0086.tlg031.1st1K-grc1.xml"
ARIST_POET = CG + "tlg0086/tlg034/tlg0086.tlg034.perseus-grc2.xml"
ARIST_TOP = F1 + "tlg0086/tlg044/tlg0086.tlg044.1st1K-grc1.xml"
ARIST_SE = F1 + "tlg0086/tlg040/tlg0086.tlg040.1st1K-grc1.xml"
PLATO_LEG = CG + "tlg0059/tlg034/tlg0059.tlg034.perseus-grc2.xml"
JOS_AJ = CG + "tlg0526/tlg001/tlg0526.tlg001.perseus-grc2.xml"
JOS_BJ = CG + "tlg0526/tlg004/tlg0526.tlg004.perseus-grc2.xml"
PHILO_HER = F1 + "tlg0018/tlg015/tlg0018.tlg015.1st1K-grc1.xml"
JUSTIN_1APOL = F1 + "tlg0645/tlg001/tlg0645.tlg001.1st1K-grc1.xml"
TATIAN = F1 + "tlg1766/tlg001/tlg1766.tlg001.perseus-grc1.xml"
CLEM_PAED = F1 + "tlg0555/tlg002/tlg0555.tlg002.1st1K-grc1.xml"
CLEM_STROM = CG + "tlg0555/tlg004/tlg0555.tlg004.perseus-grc2.xml"
ORIG_HOMJER = F1 + "tlg2042/tlg021/tlg2042.tlg021.opp-grc1.xml"
EPICT_DISS = CG + "tlg0557/tlg001/tlg0557.tlg001.perseus-grc2.xml"
IGN_EPH = F1 + "tlg1443/tlg001/tlg1443.tlg001.1st1K-grc1.xml"
LUC_PEREGR = CG + "tlg0062/tlg042/tlg0062.tlg042.perseus-grc2.xml"

PDF = "letters identical; word spaces lost in the PDF extraction of the scholar's text"

DECISIONS = [
    # ---- Alexander of Aphrodisias, Aristotle, Plato (Koch, Faure, Bobzien)
    ("scholarly_argument_faure_cyclical_vs_linear_time_in_gre_0", "adf2c65ea21b8944", "verified", ARIST_PHYS, None,
     f"Aristotle, Physics IV.14, 223b28-224a2 (ed. W. D. Ross), quoted by Faure 2022, pp. 2-3; {PDF}."),
    ("scholarly_argument_koch_alexander_s_aristotelian_sourc_5", "446e2b0913373c12", "verified", ALEX_FAT, None,
     f"Alexander of Aphrodisias, De fato 1 (ed. I. Bruns 1892, p. 164), quoted by Koch; {PDF}."),
    ("scholarly_argument_koch_alexander_s_aristotelian_sourc_5", "45f96286f263b8cb", "composite", ARIST_POET, ["ἰδοῦσαι γὰρ τὸν τόπον"],
     "Two quotations fused by the extraction: the last word of Alexander, De fato 1 (Bruns p. 164) and Aristotle, Poetics 16, 1455a10-12 (the Phineidae; ed. R. Kassel 1965), the latter letter-identical."),
    ("scholarly_argument_koch_alexander_s_conception_of_what_2", "a41ce65042c85088", "verified", ALEX_MANT, None,
     f"Alexander of Aphrodisias, De anima libri mantissa, title of the chapter on what is up to us (ed. I. Bruns, Suppl. Arist. II.1; First1KGreek section 21), quoted by Koch; {PDF}."),
    ("scholarly_argument_koch_the_human_problem_of_free_will_4", "a41ce65042c85088", "verified", ALEX_MANT, None,
     f"Alexander of Aphrodisias, De anima libri mantissa, title of the chapter on what is up to us (ed. I. Bruns, Suppl. Arist. II.1; First1KGreek section 21), quoted by Koch; {PDF}."),
    ("scholarly_argument_koch_alexander_s_rhetorical_strateg_6", "4277a5682ea53679", "verified", ALEX_FAT, ["μέγιστοι αὐτοκράτορες", "Σεβῆρε καὶ Ἀντωνῖνε"],
     "Alexander of Aphrodisias, De fato 1, address to Severus and Caracalla (ed. I. Bruns 1892, p. 164, 3). The First1KGreek TEI prints a stray capital delta before the first name; the reading is otherwise identical."),
    ("scholarly_argument_koch_alexander_s_rhetorical_strateg_6", "425f00e6a6236313", "verified", ALEX_FAT, ["μέγιστοι αὐτοκράτορες", "Σεβῆρε καὶ Ἀντωνῖνε"],
     "Alexander of Aphrodisias, De fato 1, address to Severus and Caracalla (ed. I. Bruns 1892, p. 164, 3); same words as the supporting_evidence run, with the space before the second name lost in extraction."),
    ("scholarly_argument_koch_alexander_s_target_stoic_deter_1", "5f3c68b4cb5aa404", "composite", PLATO_LEG, ["κατὰ τὴν τῆς εἱμαρμένης τάξιν καὶ νόμον"],
     "Plato, Laws X 904c (ed. J. Burnet), letter-identical, quoted by Koch; the single word after the full stop is a separate lemma of Koch's text fused by the extraction."),
    ("scholarly_argument_koch_alexander_s_target_stoic_deter_1", "354d0bd17a580fa0", "scholar_greek", ARIST_POET, ["ἐκ συλλογισμοῦ"],
     "Lemmas of Koch's footnotes fused by the extraction: Koch's label for Aristotle's 'recognition by inference' (Poetics 16, 1455a4 has only the article and 'by inference'; the noun is understood from the context) followed by two words of Poetics 16, 1455a11. Not a continuous quotation."),
    ("scholarly_argument_koch_aristotle_s_alleged_doctrine_o_3", "b55d8897cd89f29d", "scholar_greek", ARIST_POET, ["ἐκ συλλογισμοῦ"],
     "Koch's label for Aristotle's 'recognition by inference'. Poetics 16, 1455a4 (ed. R. Kassel) has the article and 'by inference' after 'the fourth'; the noun 'recognition' is supplied by Koch from the context. Not a verbatim quotation."),
    ("scholarly_argument_koch_necessity_and_fate_alexander_s_3", "083331b6d88e19f0", "verified", PS_ALEX_FEBR, None,
     "Pseudo-Alexander, De febribus 2.1 (ed. J. L. Ideler, Physici et medici Graeci minores I, 1841), the definition of fever that Koch discusses ('2, 1, 2' in his note)."),
    ("scholarly_argument_koch_necessity_and_fate_alexander_s_3", "404930c8e357c7f7", "verified", ALEX_MIXT, None,
     f"Alexander of Aphrodisias, De mixtione 3 (ed. I. Bruns 1892, p. 216), on Sosigenes, quoted by Koch; {PDF}."),
    ("scholarly_argument_koch_necessity_and_fate_alexander_s_3", "7eeacf2320828d60", "verified", ALEX_MIXT, None,
     f"Alexander of Aphrodisias, De mixtione 3 (ed. I. Bruns 1892, p. 216), quoted by Koch; {PDF}."),
    ("scholarly_argument_koch_necessity_and_fate_alexander_s_3", "f5e43df95e8bd963", "verified", ALEX_MIXT, None,
     "Alexander of Aphrodisias, De mixtione 3 (ed. I. Bruns 1892, p. 216), quoted a second time by Koch."),
    ("scholarly_argument_koch_chronological_and_conceptual_r_2", "c8112a444272529f", "needs_romain", None, None,
     "Title of a treatise on providence that Cyril of Alexandria, Contra Iulianum, attributes to Alexander, as reported by Koch 2015. Cyril's text is not in the open TEI corpora; check it in TLG E (TLG 4090) before allowlisting."),
    ("scholarly_argument_koch_peripatetic_definitions_of_fat_1", "c8112a444272529f", "needs_romain", None, None,
     "Same title as in scholarly_argument_koch_chronological_and_conceptual_r_2; same check."),
    ("argument_bobzien_2013_1113b7_8_vice_versa_translation", "1d72509b7f997206", "verified", ARIST_TOP, None,
     "Aristotle, Topics VIII.2, 158a15-16 (ed. I. Bekker), quoted by Bobzien 2013 with this locus."),
    ("argument_bobzien_2013_1113b7_8_vice_versa_translation", "f3e35215a80fc070", "verified", ARIST_TOP, None,
     "Aristotle, Topics VIII.7, 160a33-34 (ed. I. Bekker), quoted by Bobzien 2013 with this locus."),
    ("argument_bobzien_2013_1113b7_8_vice_versa_translation", "71f266622c192c0a", "verified", ARIST_SE, None,
     "Aristotle, Sophistical Refutations 17, 175b9-10 (ed. I. Bekker), quoted by Bobzien 2013 with this locus."),
    ("argument_bobzien_2013_1113b7_8_vice_versa_translation", "0dd90259cd7c35b7", "verified", ARIST_SE, None,
     "Aristotle, Sophistical Refutations 17, 175b13-14 (ed. I. Bekker), quoted by Bobzien 2013 with this locus."),
    ("argument_bobzien_2013_1113b7_8_vice_versa_translation", "08bcc8842dac0644", "verified", ARIST_SE, None,
     "Aristotle, Sophistical Refutations 17, 176a10-11 (ed. I. Bekker), quoted by Bobzien 2013 with this locus (Bobzien marks an omission before it)."),
    ("argument_bobzien_2013_1113b7_8_vice_versa_translation", "5bfa254e95de7ad9", "verified", ARIST_SE, None,
     "Aristotle, Sophistical Refutations 17, 176a15-16 (ed. I. Bekker), quoted by Bobzien 2013 with this locus; the run stops at a footnote number of the preprint."),
    ("scholarly_argument_ramelli_origen_s_modification_of_stoic_3", "43d53eb97870807b", "verified", ALEX_MIXT, None,
     "Alexander of Aphrodisias, De mixtione 4 (ed. I. Bruns 1892, SVF II 473), quoted by Ramelli 2014, p. 259, with this attribution."),
    ("scholarly_argument_ramelli_origen_s_modification_of_stoic_3", "cf3762f55f1c4581", "needs_romain", None, None,
     "Stobaeus, Eclogae I, p. 153 Wachsmuth (SVF II 471), as given by Ramelli 2014, p. 259. Stobaeus is not in the open TEI corpora; check in TLG E (TLG 2037)."),
    # ---- Josephus, Philo
    ("scholarly_argument_maston_josephus_as_evidence_for_ancie_6", "56801ed7e4eb78f5", "verified", JOS_AJ, None,
     "Josephus, Antiquitates XIII.171 (ed. B. Niese), quoted by Maston 2010, p. 175."),
    ("scholarly_argument_maston_josephus_as_evidence_for_ancie_6", "e27686a957d5d485", "verified", JOS_AJ, None,
     "Josephus, Antiquitates XIII.172 (ed. B. Niese), quoted by Maston 2010, p. 175."),
    ("scholarly_argument_velardo_stoic_influence_on_josephus_s__2", "0a5d346ab46dc15c", "verified", JOS_BJ, None,
     "Josephus, Bellum VI.267-268 (ed. B. Niese), quoted in full by Velardo, pp. 128-129."),
    ("scholarly_argument_vibe_divine_freedom_vs_human_freedo_2", "8e783a4926fe086b", "verified", PHILO_HER, None,
     "Philo, Quis rerum divinarum heres sit 301 (ed. P. Wendland 1898), quoted by Vibe 2021, pp. 11-12."),
    ("scholarly_argument_vibe_divine_freedom_vs_human_freedo_2", "20ab204292310305", "verified", PHILO_HER, None,
     "Philo, Quis rerum divinarum heres sit 301 (ed. P. Wendland 1898), quoted by Vibe 2021, pp. 11-12."),
    # ---- Justin, Tatian, Clement, Origen, Lucian
    ("scholarly_argument_f_rst_early_christian_freedom_theory_6", "fae89a34001967f7", "verified", JUSTIN_1APOL, None,
     "Justin, 1 Apology 43 (ed. G. Rauschen 1911), quoted by Fürst 2022, pp. 159-161."),
    ("scholarly_argument_minns_justin_martyr_s_anti_stoic_arg_0", "bed8d650a2301c7b", "verified", JUSTIN_1APOL, None,
     "Justin, 1 Apology 43.8 (ed. G. Rauschen 1911), lemma of the critical apparatus in Minns-Parvis; the OCR dropped accents and breathings and cut the last word, but the letters match."),
    ("scholarly_argument_f_rst_scope_and_chronological_framew_2", "0d7e2a44a7f9f364", "verified", ORIG_HOMJER, None,
     "Origen, Homiliae in Ieremiam 18.3 (ed. E. Klostermann, GCS Origenes III), one of the epigraphs of Fürst 2022, p. 1."),
    ("scholarly_argument_crawford_real_fate_redefined_as_slavery_to_passions", "add0ac2c066d4cbf", "verified", TATIAN, None,
     "Tatian, Oratio ad Graecos 12 (ed. J. C. T. Otto 1851), quoted with omissions by Crawford 2021, p. 43."),
    ("scholarly_argument_crawford_demons_can_directly_cause_bodily_disease", "add0ac2c066d4cbf", "verified", TATIAN, None,
     "Tatian, Oratio ad Graecos 12 (ed. J. C. T. Otto 1851), quoted with omissions by Crawford 2021, p. 43."),
    ("scholarly_argument_crawford_oration_as_logotherapy_against_demonic_disorder", "0d628497dbeba3ff", "verified", TATIAN, None,
     "Tatian, Oratio ad Graecos 5 (ed. J. C. T. Otto 1851), quoted by Crawford 2021, p. 53."),
    ("scholarly_argument_crawford_oration_as_logotherapy_against_demonic_disorder", "f3b282ebb8031861", "verified", TATIAN, None,
     "Tatian, Oratio ad Graecos 16 (ed. J. C. T. Otto 1851), quoted by Crawford 2021, p. 53."),
    ("scholarly_argument_crawford_oration_as_logotherapy_against_demonic_disorder", "a03308722d37335d", "verified", TATIAN, None,
     "Tatian, Oratio ad Graecos 12 (ed. J. C. T. Otto 1851, p. 54), quoted with an omission by Crawford 2021, p. 53."),
    ("scholarly_argument_crawford_astral_fate_arbitrary_not_efficacious", "ff1462ff641263c4", "needs_romain", None, None,
     "Tatian, Oratio ad Graecos 9, quoted by Crawford 2021, p. 41, from Trelenberg's edition. Otto's text (First1KGreek) is letter-identical except one word: Otto has the word for 'actions' where Crawford has 'orders'. Check Trelenberg 2012 (or Schwartz 1888) for that reading."),
    ("scholarly_argument_crawford_pharmacology_has_no_intrinsic_efficacy", "ead50801425e75f1", "scholar_greek", None, None,
     "Title of the Nepualius fragment as printed by W. Gemoll (Striegau 1884), cited by Crawford 2021, p. 47, n. 64. A modern edition's title, not a quotation."),
    ("scholarly_argument_crawford_pharmacology_has_no_intrinsic_efficacy", "ddb694b134c08aad", "scholar_greek", None, None,
     "Title of the pseudo-Democritean treatise as printed in the same Gemoll volume (1884), cited by Crawford 2021, p. 47, n. 64. A modern edition's title, not a quotation."),
    ("scholarly_argument_karfikova_adult_self_rule_replaces_childish_fear", "068f8afdc3f9274b", "verified", CLEM_PAED, None,
     "Clement of Alexandria, Paedagogus I.6 (ed. O. Stählin 1905), quoted by Karfíková 2025, pp. 176-177."),
    ("scholarly_argument_karfikova_adult_self_rule_replaces_childish_fear", "eefeb5f65828521f", "verified", CLEM_STROM, None,
     "Clement of Alexandria, Stromateis V.13.83 (ed. O. Stählin), quoted by Karfíková 2025."),
    ("scholarly_argument_karfikova_grace_prompts_and_rewards_free_choice", "eefeb5f65828521f", "verified", CLEM_STROM, None,
     "Clement of Alexandria, Stromateis V.13.83 (ed. O. Stählin), quoted by Karfíková 2025."),
    ("scholarly_argument_karfikova_grace_prompts_and_rewards_free_choice", "0283404854701f1b", "verified", CLEM_STROM, None,
     "Clement of Alexandria, Stromateis V.13.83 (ed. O. Stählin), quoted in a note by Karfíková 2025, pp. 177-178."),
    ("scholarly_argument_whitmarsh_martyr_verdict", "ffeb3d908001ec68", "verified", LUC_PEREGR, None,
     "Lucian, De morte Peregrini 18 (ed. A. M. Harmon, Loeb), quoted by Whitmarsh 2024, p. 135."),
    # ---- Müller 1926: OCR of an old printed article
    ("scholarly_argument_mueller_stoic_freedom_autonomous_self_limitation", "3c507707c175fe92", "ocr_damaged", EPICT_DISS, ["ἡ ἐλευθερία"],
     "OCR-damaged copy of Epictetus, Dissertationes IV.1.56 (ed. H. Schenkl 1916) as printed by Müller 1926, pp. 179-180. Several letters are misread (upsilon read as delta, accents lost); do not cite this run, cite the passage from the edition."),
    ("scholarly_argument_mueller_stoic_freedom_autonomous_self_limitation", "75887bcc85c68214", "ocr_damaged", EPICT_DISS, ["ἡ ἐλευθερία"],
     "Second half of the same OCR-damaged quotation of Epictetus, Dissertationes IV.1.56 (ed. H. Schenkl 1916); do not cite this run."),
    ("scholarly_argument_mueller_postpauline_parenesis_prepares_explicit_free_choice", "772889b78bf9c05b", "ocr_damaged", IGN_EPH, ["ἐν δυνάμει πίστεως"],
     "OCR-damaged copy of Ignatius, To the Ephesians 14.2 (ed. K. Lake 1912) as printed by Müller 1926, pp. 198-199 (one word misread, accents lost); do not cite this run."),
    ("scholarly_argument_mueller_clement_defines_choice_between_opposites", "bc57828bd9f60791", "ocr_damaged", CLEM_STROM, ["βούλεται σῴζεσθαι"],
     "OCR-damaged copy of Clement of Alexandria, Stromateis VI.12.96 (ed. O. Stählin) as printed by Müller 1926, pp. 217-218 (letters misread, a hyphen inserted); do not cite this run."),
    # ---- Tolan, de Faye, Dettwiler: the scholars' own Greek
    ("scholarly_argument_tolan_romans_and_divine_sovereignty__5", "3b749caec7d44046", "scholar_greek", None, None,
     "A list of Stoic technical terms drawn up by E. de Faye (1928) and quoted by Tolan 2020, pp. 121-122: a terminology list, not a quotation."),
    ("scholarly_argument_tolan_what_depends_on_us_and_4", "a44daf465f8f9427", "scholar_greek", None, None,
     "Tolan's own formulation ('we could, perhaps, encapsulate Origen's thought ... by noting that ...'), adapting the division at the opening of Epictetus' Encheiridion (1.1); not a quotation."),
    ("scholarly_argument_tolan_what_depends_on_us_and_4", "ba3ff0c450adde16", "scholar_greek", None, None,
     "De Faye's (1928) Greek tag for Epictetus, quoted by Tolan 2020: not found in Schenkl's Dissertationes or Encheiridion (searched letter by letter), so a paraphrase, not a quotation."),
    ("scholarly_argument_tolan_what_depends_on_us_and_4", "b062e17fea0b39a7", "scholar_greek", None, None,
     "De Faye's (1928) Greek tag for the Stoic-Origenian 'use of impressions', quoted by Tolan 2020: not found in Schenkl's Epictetus in this form (the Dissertationes have the accusative-genitive expression, e.g. IV.6.25), so a paraphrase, not a quotation."),
    ("scholarly_argument_tolan_what_depends_on_us_and_4", "530dcb50be5e5247", "needs_romain", None, None,
     "De Faye (1928) gives this as Origen's wording (De principiis III.1.3), quoted by Tolan 2020. Koetschau's Greek of De principiis is not in the open TEI corpora; check it (or Philocalia 21) in TLG E before allowlisting."),
    ("scholarly_argument_tolan_moral_responsibility_and_theod_3", "ee84c917d9187349", "needs_romain", None, None,
     "From the second of the anathemas against Origen of 553 (ACO IV.1, p. 248, 8), as cited by Tolan 2020, pp. 33-34. The Acts are not in the open TEI corpora; check in ACO or TLG E."),
    ("scholarly_argument_dettwiler_hellenistic_influence_on_pauli_4", "b4d7859c28cf439d", "scholar_greek", None, None,
     "The audit's own record of three Pauline anthropological terms listed by Dettwiler 2020, pp. 2-3 (body, mind, conscience). The source file writes the first term with a micro sign, which cuts the run. A list of terms, not a quotation."),
]
