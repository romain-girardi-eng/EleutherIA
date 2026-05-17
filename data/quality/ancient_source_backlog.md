# Ancient Source Backlog

Passage-gap inventory generated from the live `free_will` Postgres schema.

- Entries: 78
- blocker: 14
- covered: 23
- metadata_only: 11
- missing_work_node: 2
- partial: 28

| Priority | Status | Work node | Label | DB passages | KG passages | Route | Next step |
|---|---|---:|---|---:|---:|---|---|
| P0 | partial | `work_de_interpretatione_aristotle_c350bce_e4f6g8h0` | Aristotle, De Interpretatione | 59 | 59 | db_reconciliation | Verify chapter 9 coverage and add translations where missing. |
| P0 | partial | `work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9` | Aristotle, Nicomachean Ethics | 681 | 681 | db_reconciliation | Split any mislinked Magna Moralia passages out of the Nicomachean Ethics work node. |
| P0 | partial | `work_augustine_de_gratia_la` | Augustine, De Gratia et Libero Arbitrio | 71 | 50 | db_reconciliation | Verify the dedicated work node and reconcile existing passages. |
| P0 | partial | `work_de_libero_arbitrio, work_augustine_de_libero_arbitrio` | Augustine, De Libero Arbitrio | 786 | 577 | db_reconciliation | Reconcile old KG nodes to DB passages and split unrelated works from the De Libero Arbitrio node. |
| P0 | partial | `work_consolatio_philosophiae_boethius_524ce_f1g2h3i4` | Boethius, De Consolatione Philosophiae | 258 | 258 | db_reconciliation | Reconcile old KG nodes to DB passage IDs. |
| P0 | partial | `work_de_fato_cicero_44bce_b9c4e5d2` | Cicero, De Fato | 98 | 96 | db_reconciliation | Verify existing passage nodes and translation coverage. |
| P0 | partial | `work_epictetus_discourses` | Epictetus, Discourses and Enchiridion | 559 | 350 | db_reconciliation | Reconcile old KG nodes to DB passage IDs and verify work split. |
| P0 | partial | `work_plutarch_de_fato_complete, work_plutarch_de_fato_authentic` | Pseudo-Plutarch, De Fato | 91 | 91 | db_reconciliation | Verify whether complete De Fato coverage should be split from authentic/disputed Plutarch nodes. |
| P0 | partial | `work_de_providentia_seneca_a2b3c4d5` | Seneca, De Providentia | 2271 | 2271 | db_reconciliation | Separate true De Providentia passages from Seneca Epistulae passages before judging coverage. |
| P0 | covered | `work_aristotle_eudemian_ethics` | Aristotle, Eudemian Ethics | 41 | 41 | db_reconciliation | Attach existing EE passages to the dedicated Eudemian Ethics work node or ingest missing passages. |
| P0 | covered | `work_augustine_de_civitate_dei` | Augustine, De Civitate Dei V/XII/XIV | 164 | 164 | db_reconciliation | Verify selected-book coverage and add DB passage IDs where missing. |
| P0 | covered | `work_epicurus_letters_fragments, work_epicurus_kuriai_doxai, work_epicurus_letter_herodotus, work_epicurus_letter_menoeceus` | Epicurus, Letters and Fragments | 193 | 193 | json_mirror | Consolidate Epicurus letters, Principal Doctrines, Vatican Sayings, and fragments under citable work nodes. |
| P0 | covered | `work_de_rerum_natura_lucretius_50sbce_l2m3n4o5` | Lucretius, De Rerum Natura | 304 | 302 | db_reconciliation | Verify passage count against DB and add translations where missing. |
| P0 | covered | `work_marcus_aurelius_meditations` | Marcus Aurelius, Meditations | 599 | 596 | db_reconciliation | Reconcile old KG nodes to DB passages, then create missing passage nodes. |
| P0 | covered | `work_methodius_de_libero_arbitrio` | Methodius, De Libero Arbitrio | 104 | 104 | db_reconciliation | Create or retarget passages for Methodius instead of sharing Augustine work nodes. |
| P0 | covered | `work_plutarch_stoic_repugnantiis` | Plutarch, De Stoicorum Repugnantiis | 47 | 47 | db_reconciliation | Attach or ingest passages for the dedicated work node. |
| P0 | covered | `work_seneca_epistulae_morales` | Seneca, Epistulae Morales | 2135 | 2135 | db_reconciliation | Create or repair the Epistulae work node and retarget Epistulae passage part_of edges away from De Providentia. |
| P1 | missing_work_node | `` | Stobaeus, Anthologium/Eclogae | 0 | 0 | manual_critical_edition | Create a source-collection/work node and ingest priority fate/free-will excerpts. |
| P1 | missing_work_node | `` | Zeno, SVF I fragments | 0 | 0 | manual_critical_edition | Add SVF collection anchors and Zeno fragment passage nodes from verified edition. |
| P1 | blocker | `` | Diogenes of Oenoanda, Inscription | 0 | 0 | manual_critical_edition | Source Smith edition and create inscription fragment passages. |
| P1 | blocker | `work_diogenianus_peri_heimarmenes` | Diogenianus, Anti-Stoic Fragments | 0 | 0 | manual_critical_edition | Create fragment collection/work node and ingest verified testimonia. |
| P1 | blocker | `` | Oenomaus of Gadara, Fragments | 0 | 0 | manual_critical_edition | Create fragment collection/work node and ingest verified testimonia. |
| P1 | blocker | `work_proclus_de_providentia_fato_in_nobis, work_proclus_tria_opuscula_c9a8e4b3` | Proclus, De Providentia/Fato/In Nobis | 0 | 0 | manual_critical_edition | Use Boese/Isaac-aligned evidence and distinguish Greek fragments from Latin translation. |
| P1 | metadata_only | `work_nemesius_de_nat_hom` | Nemesius, De Natura Hominis | 0 | 0 | scaife_library | Use generic Scaife CTS fetcher, then create KG passages. |
| P1 | metadata_only | `work_porphyry_peri_tou_eph_hemin` | Porphyry, Peri tou eph' hemin | 0 | 0 | manual_critical_edition | Create passages from a verified critical edition or fragment witness. |
| P1 | partial | `work_de_gen_corr_aristotle` | Aristotle, De Generatione et Corruptione | 69 | 69 | scaife_library | Verify current Scaife ingestion and translation coverage. |
| P1 | partial | `work_de_divinatione_cicero` | Cicero, De Divinatione | 100 | 100 | scaife_library | Verify current Scaife ingestion and complete missing passages. |
| P1 | partial | `work_de_natura_deorum_cicero` | Cicero, De Natura Deorum | 22 | 22 | scaife_library | Verify current Scaife ingestion and complete missing passages. |
| P1 | partial | `work_cleanthes_hymn_to_zeus` | Cleanthes, Hymn to Zeus | 51 | 1 | scaife_library | Verify the single passage and connect to Stoic fragment collection. |
| P1 | partial | `work_laws_plato_c350bce_d4e5f6g7` | Plato, Laws Book X | 326 | 326 | scaife_library | Slice or tag Book X passages from Laws coverage. |
| P1 | partial | `work_republic_plato_c380bce_c3d4e5f6` | Plato, Republic Book X | 405 | 404 | scaife_library | Slice or tag Book X passages from Republic coverage. |
| P1 | partial | `work_plutarch_de_communibus_notitiis` | Plutarch, De Communibus Notitiis adversus Stoicos | 6 | 6 | db_reconciliation | Attach or ingest passages for the dedicated work node. |
| P1 | covered | `work_didaskalikos_alcinous_2nd_ce_q7r8s9t0` | Alcinous, Didaskalikos | 1 | 1 | db_reconciliation | Verify the single existing passage and translation. |
| P1 | covered | `work_aristotle_de_anima` | Aristotle, De Anima | 30 | 30 | scaife_library | Ingest from First1K/Scaife and connect to Aristotle work metadata. |
| P1 | covered | `work_aristotle_magna_moralia` | Aristotle, Magna Moralia | 434 | 434 | db_reconciliation | Create a dedicated Magna Moralia work node and retarget current MM passages. |
| P1 | covered | `work_metaphysics_theta_aristotle_c350bce_f5g7h9i1` | Aristotle, Metaphysics | 142 | 142 | db_reconciliation | Verify whether current Book Theta-only node satisfies the intended work scope. |
| P1 | covered | `work_aristotle_physics` | Aristotle, Physics | 71 | 71 | scaife_library | Ingest from OGA/Scaife and verify causal vocabulary coverage. |
| P1 | covered | `text_aspasius_in_en` | Aspasius, In Ethica Nicomachea | 6 | 6 | db_reconciliation | Verify commentary passages on voluntary action. |
| P1 | covered | `work_calcidius_in_timaeum` | Calcidius, In Timaeum | 5 | 5 | json_mirror | Verify DLT source and add passage nodes. |
| P1 | covered | `work_diogenes_laertius_lives` | Diogenes Laertius, Vitae Philosophorum | 1204 | 1204 | db_reconciliation | Verify DB reconciliation and book-level passage counts. |
| P1 | covered | `work_plato_apology` | Plato, Apology | 125 | 125 | db_reconciliation | Ingest or reconcile Apology passages. |
| P1 | covered | `work_plato_phaedo` | Plato, Phaedo | 59 | 59 | db_reconciliation | Verify passage coverage. |
| P1 | covered | `work_plato_phaedrus` | Plato, Phaedrus | 261 | 261 | db_reconciliation | Ingest or reconcile Phaedrus passages. |
| P1 | covered | `work_plato_timaeus` | Plato, Timaeus | 82 | 82 | db_reconciliation | Verify passage coverage and translations. |
| P1 | covered | `work_plotinus_enneads_iv_8, work_plotinus_enn_iii_1` | Plotinus, Enneads | 1368 | 1365 | db_reconciliation | Verify whether all Enneads passages should remain under the current IV.8-labeled node. |
| P1 | covered | `work_porphyry_ad_marcellam` | Porphyry, Ad Marcellam | 35 | 35 | db_reconciliation | Verify passage coverage. |
| P1 | covered | `work_sextus_outlines_pyrrhonism_f9a7c8e4` | Sextus Empiricus, PH and Against the Professors | 534 | 534 | db_reconciliation | Verify work split and passage counts for PH versus M. |
| P2 | blocker | `work_diodore_tarsus_contra_astronomos_heimarmenen, work_diodore_tarsus_commentary_romans` | Diodore of Tarsus, Fragments | 0 | 0 | manual_critical_edition | Consolidate the existing metadata work nodes and ingest only verified fragment witnesses. |
| P2 | blocker | `work_gregory_contra_eunomium` | Gregory of Nyssa, Contra Eunomium | 0 | 0 | manual_critical_edition | Source GNO text and create passages. |
| P2 | blocker | `work_gregory_contra_fatum` | Gregory of Nyssa, Contra Fatum | 0 | 0 | manual_critical_edition | Source GNO III.2 or another verified edition before ingestion. |
| P2 | blocker | `work_gregory_de_anima_resurrectione` | Gregory of Nyssa, De Anima et Resurrectione | 0 | 0 | manual_critical_edition | Source GNO/PG text and create passages. |
| P2 | blocker | `work_gregory_de_hom_opif` | Gregory of Nyssa, De Hominis Opificio | 0 | 0 | manual_critical_edition | Source GNO/PG text and create passages. |
| P2 | blocker | `work_gregory_oratio_catechetica` | Gregory of Nyssa, Oratio Catechetica Magna | 0 | 0 | manual_critical_edition | Source GNO/PG text and create passages. |
| P2 | blocker | `` | Iamblichus, De Mysteriis | 0 | 0 | manual_critical_edition | Source a verified edition before ingestion. |
| P2 | blocker | `work_john_damascus_de_fide` | John of Damascus, De Fide Orthodoxa | 0 | 0 | manual_critical_edition | Source Kotter PTS or verified Greek text before passage ingestion. |
| P2 | blocker | `work_lactantius_divinarum_institutionum` | Lactantius, Divine Institutes | 0 | 0 | manual_critical_edition | Source a verified Latin edition and create passage nodes. |
| P2 | blocker | `work_philo_de_providentia` | Philo, De Providentia | 0 | 0 | manual_critical_edition | Source Cohn-Wendland/Armenian/Greek-fragment evidence before passage ingestion. |
| P2 | metadata_only | `work_aristotle_de_motu` | Aristotle, De Motu Animalium | 0 | 0 | json_mirror | Use First1K/TLG or Nussbaum-aligned critical text and add passages. |
| P2 | metadata_only | `work_josephus_antiquitates` | Josephus, Antiquitates Judaicae | 0 | 0 | json_mirror | Use Perseus XML or another verified Greek source and target sectarian fate passages first. |
| P2 | metadata_only | `work_josephus_bellum_jud` | Josephus, Bellum Judaicum | 0 | 0 | json_mirror | Use Perseus XML or another verified Greek source and target fate passages first. |
| P2 | metadata_only | `work_theodoret_graecarum_affectionum_curatio` | Theodoret, Graecarum Affectionum Curatio | 0 | 0 | manual_critical_edition | Source verified Greek edition and create passages. |
| P2 | partial | `work_basil_hexaemeron` | Basil, Hexaemeron | 15 | 15 | scaife_library | Ingest from Scaife CTS if needed. |
| P2 | partial | `work_clement_protrepticus` | Clement of Alexandria, Protrepticus | 51 | 51 | scaife_library | Ingest from Scaife CTS if not covered elsewhere. |
| P2 | partial | `work_clement_stromateis` | Clement of Alexandria, Stromata | 6 | 6 | scaife_library | Compare existing Clement/SC coverage, then ingest missing passages from Scaife. |
| P2 | partial | `work_galen_de_placitis` | Galen, De Placitis Hippocratis et Platonis | 3 | 3 | scaife_library | Ingest from Scaife CTS and create work/passages. |
| P2 | partial | `work_philo_de_opificio` | Philo, De Opificio Mundi | 172 | 172 | manual_critical_edition | Source Cohn-Wendland/Loeb-aligned Greek before passage ingestion. |
| P2 | partial | `work_simplicius_in_enchiridion` | Simplicius, In Epicteti Enchiridion | 9 | 9 | scaife_library | Complete Scaife ingestion and verify commentary passage granularity. |
| P2 | partial | `work_tertullian_adv_marcionem` | Tertullian, Adversus Marcionem | 13 | 13 | scaife_library | Ingest from Scaife/CSEL and prioritize Book II if splitting by book. |
| P2 | partial | `work_tertullian_de_anima` | Tertullian, De Anima | 31 | 31 | scaife_library | Ingest from Scaife/CCSL and add translations. |
| P3 | metadata_only | `work_exodus_c9d0e1f2` | Exodus | 0 | 0 | db_reconciliation | Ingest or reconcile Exodus passages relevant to hardening and divine agency. |
| P3 | metadata_only | `work_ezekiel_g3h4i5j6` | Ezekiel | 0 | 0 | db_reconciliation | Ingest or reconcile Ezekiel passages relevant to responsibility and new heart language. |
| P3 | metadata_only | `work_genesis_u1v2w3x4` | Genesis | 0 | 0 | db_reconciliation | Ingest or reconcile Genesis passages relevant to creation, fall, and responsibility. |
| P3 | metadata_only | `work_sirach_a3b4c5d6` | Sirach / Ecclesiasticus | 0 | 0 | db_reconciliation | Ingest or reconcile Septuagint/Vulgate Sirach passages, prioritizing Sirach 15. |
| P3 | metadata_only | `work_wisdom_of_solomon` | Wisdom of Solomon | 0 | 0 | db_reconciliation | Ingest or reconcile Wisdom passages from Septuagint source. |
| P3 | partial | `work_new_testament` | Galatians | 119 | 119 | db_reconciliation | Split Galatians from the generic New Testament node or create a dedicated work node. |
| P3 | partial | `work_new_testament` | John | 119 | 119 | db_reconciliation | Split Gospel of John from the generic New Testament node or create a dedicated work node. |
| P3 | partial | `work_new_testament` | Romans | 123 | 119 | db_reconciliation | Split Romans from the generic New Testament node or create a dedicated work node. |
| P3 | partial | `work_septuagint` | Septuagint Psalms | 1 | 1 | db_reconciliation | Split Psalms from generic Septuagint coverage and create priority passage nodes. |
