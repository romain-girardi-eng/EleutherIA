# EleutherIA KG — Quality Audit Ledger (Wave 1: Ancient-Layer Integrity)

_Generated 2026-06-05 from the git-tracked mirror `data/kg/nodes.jsonl` (snapshot 2026-05-30). Prod Supabase paused → applied to mirror; deploy-up via `scripts/migrations/apply_kg_audit_to_prod.py` when reachable._

## Method

Multi-agent dynamic workflow. Sonnet batch-scanners triaged **453 persons + 241 works** for false facts, misattribution, anachronism, and fabricated bibliography; every flag was then **adversarially re-verified by an independent Opus agent** against the live corpus + Wikidata/Perseus/TLG/SEP/critical-edition metadata (web-grounded). Only `confirmed` findings with sources were applied; `needs_human` items were never guessed. Structural/mechanical layer was separately proven clean (0 FK orphans, 0 ontology violations, 0 sigma errors).

## Results

- Verdicts: **85** | confirmed **81**, rejected 2, needs_human 2
- Severity (confirmed): high 37, medium 27, critical 12, low 5
- Dimensions (confirmed): J1_false_fact 45, J3_biblio 31, J5_anachronism 3, J4_misattribution 2
- **Applied to mirror: 71 fixes across 66 nodes** (backup `data/kg/nodes.jsonl.bak-wave1`). Deferred for manual review: 5.

## Critical fixes (wrong Wikidata QIDs — linked-data integrity)

The `wikidata_qid` field was broadly corrupt; each was replaced with the verified entity:

| Node | Old QID (resolved to) | Corrected |
|---|---|---|
| irenaeus d202 | Q192568 (“Ethical dilemma”) | Q182123 |
| gottfried leibniz 0r4m5n13 | Q9191 (René Descartes) | Q9047 |
| maimonides k7l8m9n0 | Q80359 (1999 WWE event) | Q127398 |
| alexander aphrodisias fl200ce n5o6p7q8 | Q192477 | Q317146 |
| ambrose milan 339 397 | Q44183 (William Golding) | Q43689 |
| philo alexandria a1b2c3d4 | Q170090 (a cycling race) | Q189597 |
| plotinus d270 | Q41155 (Heraclitus) | Q134189 |
| augustine hippo d430 | Q8963 (Johannes Kepler) | Q8018 |
| thomas hobbes 2t6o7p35 | Q46734 | Q37621 |
| averroes c9d0e1f2 | Q17894 | Q39837 |
| thomas aquinas 61b633ce | Q42443 | Q9438 |
| porphyry | Q192430 (menadiol (chemical)) | Q203445 |
| origen alexandria 185 254ce s9t0u1v2 | Q188651 (photochemistry) | Q170472 |
| valentinus gnostic 2c ce | Q230769 | Q309864 |

## Other confirmed fixes (sample)

- **[high/J3_biblio]** `person_maximus_confessor_d662` — The Disputatio cum Pyrrho bibliographic note cites a non-existent / mis-numbered edition: 'new critical edition Doucet, SC 478 (forthcoming) / Riou 1973 thesis'. SC 478 in the Sources Chrétiennes cata
- **[high/J3_biblio]** `work_clement_stromateis` — The 'Critical editions' line collapses six distinct Sources Chrétiennes volumes under a single 'A. Le Boulluec' credit, misattributing the editors of at least SC 38 (Stromate II) and SC 463 (Stromate 
- **[high/J3_biblio]** `work_plotinus_ennead_vi_8_d8b9c5a4` — The reference 'translation française de référence' for Ennead VI.8 (Traité 39) is misattributed to Pierre Hadot, Cerf 1988. Hadot's 1988 Cerf volume is his translation+commentary of Traité 38 (VI, 7),
- **[high/J1_false_fact]** `scholar_frede_michael` — Death location stated as 'Skala Eressou, Lesbos' is factually wrong. Michael Frede drowned on 11 August 2007 at Agios Minas, a cove near Itea below Delphi (Gulf of Corinth), while attending the 11th S
- **[high/J1_false_fact]** `person_john_chrysostom_d407` — The description body opens 'Jean Chrysostome (354-407 CE)'. Scholarly consensus places Chrysostom's birth in the range c. 344-349 CE (Kelly and Carter favour 349; Wikipedia/Britannica give c. 347). 35
- **[high/J1_false_fact]** `work_josephus_bellum_jud` — The description references 'Books II and XIII' for the account of Pharisees, Sadducees, and Essenes on fate and free will. The Bellum Judaicum (Jewish War) has only seven books — Book XIII does not ex
- **[high/J1_false_fact]** `scholar_steel_carlos` — The description states Steel was 'Co-éditeur de la rétroversion grecque des Tria Opuscula de Proclus.' This is false. The Greek retroversion of Proclus's Tria Opuscula was produced by Benedikt Strobel
- **[high/J3_biblio]** `work_frede_free_will_2011` — The hardcover ISBN stated in the description is wrong. The node gives '978-0-520-26969-0', which corresponds to no edition of Frede's 'A Free Will: Origins of the Notion in Ancient Thought'. The corre
- **[critical/J3_biblio]** `scholar_jacobsen_a` — The description attributes to Anders-Christian Jacobsen the editorship of 'Universal Salvation: The Current Debate (Cambridge University Press 2019)'. This is a fabricated bibliographic attribution. T
- **[high/J3_biblio]** `work_chrysostom_de_babylas_contra_julianum` — The description self-states the work is 'PG 50, 533-572' and cites ch. 9 correctly as 'PG 50, 546', but cites ch. 2 as 'PG 57, 536'. PG 57 is the volume for Chrysostom's Homilies on Matthew (In Mattha
- **[high/J1_false_fact]** `person_ginet_carl_0t1u2v3w` — Birth year recorded as 1933 CE, but authoritative sources consistently give 1932.
- **[high/J1_false_fact]** `person_pereboom_derk_contemporary` — Birth year listed as 1950 CE, but Derk Pereboom was born 6 February 1957.
- **[high/J1_false_fact]** `work_origen_exhortation_martyrdom` — Protoctetus is described as 'the deacon' but Eusebius (HE VI.28) explicitly identifies him as a presbyter of the parish of Caesarea (πρεσβύτερον τῆς ἐν Καισαρείᾳ παροικίας), not a deacon. The Exhortat
- **[high/J1_false_fact]** `scholar_dunn_j` — The node calls Dunn 'co-fondateur (avec E. P. Sanders et N. T. Wright) de la New Perspective on Paul', implying a three-way joint founding. That is historically false. The NPP was a sequence of distin
- **[high/J3_biblio]** `work_gregory_de_anima_resurrectione` — The node cites a fabricated Sources Chretiennes reference for Gregory of Nyssa's De Anima et Resurrectione: 'SC 614, ed. P. Maraval (Cerf 2022)' (in the critical-edition line) and 'Maraval, SC 614 (20
- **[high/J1_false_fact]** `scholar_cooper_john` — The description gives John M. Cooper's Princeton title as 'Stuart Professor of Philosophy'. That chair belonged to Gregory Vlastos (Stuart Professor 1955-1976). Cooper's actual title was the Henry Put
- **[high/J1_false_fact]** `scholar_harl_m` — Node falsely credits Marguerite Harl as 'co-éditrice (avec Doutreleau) des Homélies sur la Genèse d'Origène (SC 7bis, Cerf 1976, rééd.)'. SC 7/7bis (Origène, Homélies sur la Genèse) was edited, transl
- **[high/J3_biblio]** `work_justin_second_apology_sc507` — The description contains two false cross-references in its free-will content note. (1) 'Chapter 6' misplaces the autexousion-for-angels-and-men passage: in the standard Maran/ANF chapter division also
- **[high/J3_biblio]** `sc79_chrysostomus_de_providentia` — The node's metadata assigns sc_number '79' to the six homilies De fato et providentia (Peri heimarmenes te kai pronoias logoi hex, PG 50, 749-774). SC 79 is an entirely different Chrysostom work: 'Sur
- **[high/J1_false_fact]** `work_ad_simplicianum` — The description attributes the quotation 'What have you that you did not receive?' to Romans 9:13. That quotation is 1 Corinthians 4:7. Romans 9:13 reads 'Jacob I loved, but Esau I hated' (Paul citing
- **[high/J3_biblio]** `person_jerome_stridon_347_420` — The description cites 'SC 533, éd. Canellis 2010-2011' as the Sources Chrétiennes edition of Jerome's Dialogus adversus Pelagianos. This is a conflated/fabricated bibliographic reference. SC 533 is in
- **[high/J3_biblio]** `person_ambrose_milan_339_397` — The edition reference 'SC 488 (De Officiis, éd. Testard 2005)' is wrong. SC 488 in the Sources Chrétiennes collection is Tyconius, 'Le Livre des Règles' (introd./trad./notes Jean-Marc Vercruysse, Cerf
- **[high/J3_biblio]** `work_lactantius_divinarum_institutionum` — The node attributes 'SC 509 + 547 (Inst. VI-VII, éd. Ingremeau 2007 + 2014)' to Lactantius. SC 547 is NOT Lactantius: it is Cyprien de Carthage, 'Ceux qui sont tombés (De lapsis)', Cerf 2012 (texte cr
- **[high/J3_biblio]** `work_4_maccabees` — The critical edition cited conflates three distinct facts. (1) Septuaginta IX/1 is 1 Maccabees (ed. Werner Kappler, 1936; 2nd ed. 1967; 3rd ed. 1990), NOT 4 Maccabees — 4 Maccabees is fascicle IX/4. (
- **[high/J3_biblio]** `work_methodius_de_libero_arbitrio` — The CTS URN points to the wrong TLG author. tlg2042 is the TLG author number for Origenes (Origen), not Methodius of Olympus. Methodius's TLG author number is 2959, and De Libero Arbitrio (De autexusi
- **[high/J1_false_fact]** `person_bobzien_susanne_contemporary` — The 'a Princeton' localisation is factually false. Bobzien's D.Phil. was awarded by Oxford University in 1993 (affiliated with Somerville College from 1987), where she was registered throughout her gr
- **[critical/J1_false_fact]** `work_de_principiis_origen_230s_v2w3x4y5` — The description asserts that Origen uses 'Carneadean arguments (explicitly cited)' in De Principiis. This is false. Origen never names Carneades anywhere in De Principiis Book III. The full text (Rufi
- **[high/J3_biblio]** `person_athanasius_alexandria_298_373` — The scanner-flagged entry 'SC 18bis (Kannengiesser 1973)' misattributes the editor and conflates two distinct Sources Chrétiennes volumes. SC 18bis is Contre les Païens ALONE, edited by Pierre-Thomas 
- **[high/J3_biblio]** `scholar_gourinat_jean_baptiste` — The node attributes the 1996 original edition of 'Les Stoïciens et l'âme' to Vrin. The 1996 original was published by PUF (Presses Universitaires de France) in the collection 'Philosophies' (ISBN 2130
- **[high/J1_false_fact]** `scholar_gourinat_jean_baptiste` — Birth year stated as 1962, but Jean-Baptiste Gourinat was born 19 July 1964 in Nice.
- **[high/J3_biblio]** `work_epictetus_fragments` — The node attributes the Gellius witness to 'Noctes Atticae, Bk. 17'. The Gellius fragment of Epictetus (Fragment 9 Schenkl) is in Noctes Atticae Book 19, chapter 1, sections 14-21 (19.1.14-21) — the f
- **[high/J3_biblio]** `person_augustine_hippo_d430` — The editions list in the description contains two bibliographic errors. (1) 'CSEL 74 (De Civ. Dei)' is wrong: CSEL 74 is W. M. Green's 1956 Vienna edition of Augustine's De libero arbitrio, not De Civ
- **[high/J3_biblio]** `work_clement_protrepticus` — The description lists 'A. Heuser-Hofmann (Fontes Christiani 60)' as a critical edition of Clement of Alexandria's Protrepticus. This is a fabricated/wrong bibliographic reference. Fontes Christiani Ba
- **[high/J3_biblio]** `scholar_amand_de_mendieta_e` — Description falsely attributes the critical edition of Basil's De Spiritu Sancto (SC 17, Cerf, 1947; rev. SC 17bis, 1968) to Amand de Mendieta. SC 17 / SC 17bis was edited by Benoît Pruche O.P., not A
- **[high/J1_false_fact]** `person_kane_robert_1938_2022` — Robert Hilary Kane's death date is recorded as 2022 CE, but he died April 20, 2024.

## Deferred (manual review — non-surgical or ambiguous)

- `scholar_harl_m` (description) — non-surgical description change — manual review
- `person_pseudodionysius_the_areopagite_anonymous_c_500_ce_4ea569e3` (metadata.birth_date / metadata.death_date) — unhandled field: metadata.birth_date / metadata.death_date
- `work_gregory_contra_eunomium` (description) — non-surgical description change — manual review
- `work_maximus_ambigua_iohannem` (description) — non-surgical description change — manual review
- `scholar_gourinat_jean_baptiste` (description) — non-surgical description change — manual review


## Wave 1b — Greek fabrication (J2)

173 nodes whose embedded Greek is absent from the (partial) corpus, each adversarially verified vs TLG/Perseus/editions. **14 genuine fabrications** found, 142 cleared as legitimate terms/corpus-gaps, 9 needs_human.

Applied: 11 safe fixes (spelling/accents + replacing fabricated Greek with English). **Deferred (9): fixes that insert sourced Greek — verify against the edition** (see `data/audit/wave1_greek_deferred.jsonl`).

Confirmed fabrications:
- **person_melito_sardis** — Parenthetical Greek presented as a genuine quotation from a work that survives only in Syriac/Coptic/Georgian/Armenian, with no surviving Greek original to quot
- **work_tatian_oratio** — The parenthetical Greek run 'οὐ φύσει... ἐκ τῆς τοῦ ἐλευθέρου γνώμης', presented as a verbatim quotation of Tatian Orat. 7, is fabricated/conflated pseudo-Greek
- **argument_civilization_alex** — Two Greek runs presented as verbatim quotations from Alexander, De Fato, anchored to fabricated Bruns page references. The description cites 'Fat. 508-510', 'Fa
- **concept_prohairesis_alex** — Reconstructed gloss 'τὸ ἐκ βουλῆς αἱρετόν' presented inside quotation marks as Alexander's verbatim definition of prohairesis 'at De Fato 175'.
- **argument_homonymy_alex** — The run 'ἑκούσιον, ἐφ' ἡμῖν, αὐτεξούσιον' is a list of three genuine, correctly-spelled ancient technical terms (legit_term). But the run 'ὁμωνυμίᾳ παρακρουόμεν
- **concept_saving_teaching_alex** — Run 1 'ἑκούσιον, ἐφ' ἡμῖν, αὐτεξούσιον' (methodological caveat) is legit standard terminology. Run 2 'σῴζουσα διδασκαλία' is a coined phrase carrying an impossi
- **concept_practical_life_alex** — Composed Greek sentence presented as a verbatim Alexander quotation at a specific locus ('In Fat. 580 … "all practical life is abolished" (πᾶς ὁ πρακτικὸς βίος 
- **argument_common_cause_alex** — Two Greek runs presented as Alexander's terminology. 'ἡ προαίρεσις αἰτία κοινή' ("choice as common cause") is a composed schematic nominal phrase, not attested 
- **argument_hypothetical_fate_plut** — Fabricated Greek quotation attached to a non-existent citation ('Fat. 15')
- **argument_human_constitution_alex** — Two Greek runs ('τὸ εἶναι ἡμᾶς ἀνθρώπους', 'ἀναγκαῖον πρὸς τὸ εἶναι') are presented as Alexander's terminology and anchored to Bruns references 'Fat. 498', 'Fat
- **concept_inner_freedom_alex** — Two Greek runs are presented as Alexander's 'Greek terminology' but neither is attested in the corpus, in Alexander's De Fato, or in scholarship; the second is 
- **work_origen_de_oratione** — The description presents a verbatim Greek quotation attributed to 'De Orat. 6.2' — οὐχ ὅτι γινώσκει... διὰ τοῦτο ἔσται, ἀλλ' ὅτι ἐσόμενόν ἐστι, διὰ τοῦτο γινώσκ
- **concept_boulesis_rational_desire_ef9f861d** — The Greek run 'πᾶσα βούλησις ἐν λογιστικῷ' is presented as a verbatim Aristotle quotation at a precise Bekker locus (De Anima III.9, 432b5-7) with the gloss 'al
- **argument_irenaeus_recapitulation_theodicy** — Greek back-translation of a lost-Greek passage (AH III.20.3) presented as the original quotation


## Wave 2 — Semantic integrity

- **Citation–claim support (214 grounded claim nodes):** 43 confirmed mismatches where the cited passage does not support the asserted claim → **review queue `docs/kg-citation-mismatch-review.md`** (touches passage_citations; single-pass; not auto-applied).
- **Anachronism (132 candidates):** 20 unhedged modern labels confirmed; 10 high-confidence hedges applied surgically; rest rejected as legitimate modern-scholarship framing.
