# G1 — Transmission / Influence Chains

Directed person-person influence graph built from `influences, teaches, precedes, student_of, responds_to, influenced_by`.
Each hop is anchored by a *licensing passage* (shared grounded argument, an argument citing the source's own text, or a `parallel_to` overlap). Modern labels are not asserted here.

## Graph stats

- Persons: **453**
- In the dialectical component (>=1 person-person edge): **129**
- Isolated persons (no dialectical edge): **324**
- Directed person-person edges: **160**

## Top-10 betweenness (transmission brokers)

1. **Origen of Alexandria** — 385.817  `person_origen_alexandria_185_254ce_s9t0u1v2`
2. **Chrysippus of Soli** — 220.833  `person_chrysippus_280_206bce_i9j0k1l2`
3. **Carneades of Cyrene** — 125.833  `person_carneades_214_129bce_l2m3n4o5`
4. **Aristotle of Stagira** — 106.333  `person_aristotle_384_322bce_c2d4f6a8`
5. **Augustine of Hippo** — 91.0  `person_augustine_hippo_d430`
6. **Irenaeus of Lyon** — 89.833  `person_irenaeus_d202`
7. **Epictetus of Hierapolis** — 87.0  `person_epictetus_of_hierapolis_3c385bc2`
8. **Plotinus** — 81.667  `person_plotinus_d270`
9. **Bardaisan of Edessa (Bar-Daisan)** — 78.95  `person_bardesanes_the_syrian_3r8s0u76`
10. **Eusebius of Caesarea** — 73.633  `person_eusebius_caesarea_d339`

## Canonical transmission paths

### carneades → boethius
**Carneades of Cyrene → Boethius (Anicius Manlius Severinus Boethius)** — 3 hop(s) · _via augmented graph (shared-argument / parallel_to backbone)_

- `Carneades of Cyrene` **--influences-->** `Alexander of Aphrodisias`
  - licence: passage **passage_alex_fat_11** via shared argument `argument_frede_2011_alexander_libertarian_dead_end`
- `Alexander of Aphrodisias` **--shared_argument-->** `Augustine of Hippo`
  - licence: _scholarly-reception node_ `scholarly_argument_gill_later_ancient_reception_of_sto_3` (secondary literature; no primary passage)
- `Augustine of Hippo` **--shared_argument-->** `Boethius (Anicius Manlius Severinus Boethius)`
  - licence: _scholarly-reception node_ `scholarly_argument_brouwer_influence_on_late_antiquity_an_4` (secondary literature; no primary passage)

### carneades → origen
**Carneades of Cyrene → Origen of Alexandria** — 1 hop(s) · _via strict influence graph_

- `Carneades of Cyrene` **--influences-->** `Origen of Alexandria`
  - licence: passage **passage_cic_fat_23** via shared argument `argument_cafma_carneades_m3n4o5p6`

### alexander_aphrodisias → origen
**Alexander of Aphrodisias → Origen of Alexandria** — 1 hop(s) · _via strict influence graph_

- `Alexander of Aphrodisias` **--influences-->** `Origen of Alexandria`
  - licence: _scholarly-reception node_ `scholarly_argument_gill_later_ancient_reception_of_sto_3` (secondary literature; no primary passage)

### chrysippus → augustine
**Chrysippus of Soli → Augustine of Hippo** — 2 hop(s) · _via strict influence graph_

- `Chrysippus of Soli` **--influences-->** `Origen of Alexandria`
  - licence: passage **passage_cic_fat_23** via shared argument `argument_cafma_carneades_m3n4o5p6`
- `Origen of Alexandria` **--influences-->** `Augustine of Hippo`
  - licence: _scholarly-reception node_ `argument_frede_2011_christianity_anti_gnostic_anti_astral_motivation` (secondary literature; no primary passage)

## Isolated persons worklist (324 — no person-person dialectical edge)
_101 ancient/non-scholar (priority for wiring) · 223 modern scholars._

### Ancient / non-scholar (priority)

- Al-Ash'ari (Abū al-Ḥasan al-Ashʿarī)  `person_al_ashari_m3n4o5p6`
- Al-Ghazali (Abū Ḥāmid Muḥammad ibn Muḥammad al-Ghazālī)  `person_al_ghazali_u1v2w3x4`
- Ambroise de Milan  `person_ambrose_milan_339_397`
- Ammonius, son of Hermias  `person_ammonius_hermiae_c440_520`
- Anonymous EN Commentator  `person_anonymous_en_commentator_2c_ce`
- Apollinaris of Hierapolis  `person_apollinaris_hierapolis_2c`
- Apulée de Madaure  `person_apuleius_madauros_124_170`
- Arcesilaus of Pitane  `person_arcesilaus_316_241bce`
- Aristides of Athens  `person_aristides_athens_2c_ce`
- Aspasius  `person_aspasius_2c_ce`
- Athanase d'Alexandrie  `person_athanasius_alexandria_298_373`
- Athenagoras of Athens  `person_athenagoras`
- Atticus (Middle Platonist)  `person_atticus_2c_ce`
- Aulus Gellius  `person_aulus_gellius_125_180ce`
- Blaise Pascal  `person_blaise_pascal_6n0i1j79`
- Bonaventure (Giovanni di Fidanza)  `person_bonaventure_e7f8g9h0`
- Caesarius of Arles  `person_caesarius_arles_d542`
- Calcidius  `person_calcidius_4c_ce`
- Celsus (the Platonist)  `person_celsus_platonist_2c_ce`
- Clement of Rome  `person_clement_rome_d99`
- Crescens the Cynic  `person_crescens_cynic_2c_ce`
- Cyrille de Jérusalem  `person_cyril_jerusalem_315_386`
- Cyrus d'Alexandrie  `person_cyrus_alexandria_d641`
- Diodorus Cronus  `person_diodorus_cronus_48ef6200`
- Diogenes Laertius  `person_diogenes_laertius_3c_ce`
- Domingo Báñez  `person_domingo_banez_4l8g9h57`
- Laura Waddell Ekstrom  `person_ekstrom_laura_1u2v3w4x`
- Faustus of Riez  `person_faustus_riez_d495`
- Francis Macdonald Cornford  `person_fm_cornford_cambridge`
- Francisco Suárez (late 16th c.) / Scholastic tradition continued into 17th c.  `person_francisco_suarez_late_16th_c_scholastic_tradition_continued_into_17th_c_d5e0d92c`
- Franciscus Gomarus  `person_franciscus_gomarus_2j6e7f35`
- Carl Ginet  `person_ginet_carl_0t1u2v3w`
- Gottschalk of Orbais  `person_gottschalk_of_orbais_e5f6g7h8`
- Gregory of Rimini  `person_gregory_of_rimini_i1j2k3l4`
- Hasdai Crescas  `person_hasdai_crescas_s5t6u7v8`
- John-Dylan Haynes  `person_haynes_john_dylan_2f3g4h5i`
- Heraclitus of Ephesus  `person_heraclitus_fl500bce_a1b2c3d4`
- Hermas  `person_hermas_2c_ce`
- Hillel the Elder  `person_hillel_elder_m3n4o5p6`
- Hincmar of Reims  `person_hincmar_of_reims_i9j0k1l2`
- Pope Honorius I (d. 638)  `person_honorius_i_pope_d638`
- Ignatius of Antioch  `person_ignatius_antioch_d110`
- Jacobus Arminius  `person_jacobus_arminius_1i5d6e24`
- Jean Buridan (attributed)  `person_jean_buridan_attributed_e5990f67`
- Jérôme de Stridon  `person_jerome_stridon_347_420`
- John Cassian  `person_john_cassian_d435`
- John of Damascus (John Damascene)  `person_john_damascene_d749`
- John Duns Scotus  `person_john_duns_scotus_48daa9ee`
- John Scotus Eriugena  `person_john_scotus_eriugena_a1b2c3d4`
- Flavius Josephus  `person_josephus_flavius_e5f6g7h8`
- Julian of Eclanum  `person_julian_eclanum_d454`
- Joshua Knobe  `person_knobe_joshua_5i6j7k8l`
- Lactantius  `person_lactantius_250_325ce`
- Leucippus and Democritus  `person_leucippus_and_democritus_8a42be84`
- Benjamin Libet  `person_libet_benjamin_1e2f3g4h`
- Luis de Molina (expanded)  `person_luis_de_molina_3k7f8g46`
- Catriona Mackenzie  `person_mackenzie_catriona_9m0n1o2p`
- Marcion of Sinope  `person_marcion_sinope_2c_ce`
- Pape Martin Ier  `person_martin_i_pope_590_655`
- Maximus of Tyre  `person_maximus_of_tyre_125_185ce`
- Michael McKenna  `person_mckenna_michael_4x5y6z7a`
- Alfred Mele  `person_mele_alfred_3g4h5i6j`
- Melito of Sardis  `person_melito_sardis`
- John Stuart Mill  `person_mill_john_stuart_2b3c4d5e`
- Eddy Nahmias  `person_nahmias_eddy_4h5i6j7k`
- Shaun Nichols  `person_nichols_shaun_6j7k8l9m`
- Nicostratus (Middle Platonist)  `person_nicostratus_2c_ce`
- Numenius of Apamea  `person_numenius_apamea_2c_ce`
- Timothy O'Connor  `person_oconnor_timothy_8r9s0t1u`
- Pamphilus of Caesarea  `person_pamphilus_caesarea_d310`
- Parmenides of Elea  `person_parmenides_of_elea_44a65114`
- Paul the Apostle  `person_paul_apostle`
- Peter Abelard  `person_peter_abelard_w9x0y1z2`
- Peter Lombard  `person_peter_lombard_a3b4c5d6`
- Jean Philopon  `person_philoponus_johannes_490_570`
- Pierre Bayle  `person_pierre_bayle_701cb0a7`
- Prosper of Aquitaine  `person_prosper_aquitaine_d455`
- Pseudo-Barnabas (Anonymous)  `person_pseudo_barnabas`
- Pseudo-Justin (Anonymous)  `person_pseudo_justin`
- Pseudo-Plutarch  `person_pseudo_plutarch_2c_ce`
- Pseudo-Dionysius the Areopagite (anonymous, c. 500 CE)  `person_pseudodionysius_the_areopagite_anonymous_c_500_ce_4ea569e3`
- Pyrrhus de Constantinople  `person_pyrrhus_constantinople_d654`
- Ralph Cudworth  `person_ralph_cudworth_77de5c65`
- Saadia Gaon (Saʿadya ben Yōsēf)  `person_saadia_gaon_g3h4i5j6`
- Lucius Annaeus Seneca (Seneca the Younger)  `person_seneca_4bce_65ce_a1b2c3d4`
- Sergius Ier de Constantinople  `person_sergius_constantinople_565_638`
- Shammai  `person_shammai_q7r8s9t0`
- Simplicius of Cilicia  `person_simplicius_cilicia_490_560ce`
- Saul Smilansky  `person_smilansky_saul_9c0d1e2f`
- Sophrone de Jérusalem  `person_sophronius_jerusalem_560_638`
- Richard Taylor  `person_taylor_richard_6p7q8r9s`
- Tertullian  `person_tertullian_d220`
- Theodoret of Cyrrhus  `person_theodoret_cyrrhus_393_466ce`
- Thomas Reid  `person_thomas_reid_8z2u3v91`
- Tomasz Stępień  `person_tomasz_stepien_warsaw`
- Valentinus  `person_valentinus_gnostic_2c_ce`
- Peter van Inwagen  `person_van_inwagen_peter_9s0t1u2v`
- Kadri Vihvelin  `person_vihvelin_kadri_6z7a8b9c`
- Vincent of Lérins  `person_vincent_lerins_d450`
- R. Jay Wallace  `person_wallace_r_jay_5y6z7a8b`
- William of Ockham  `person_william_of_ockham_8df17ab4`

### Modern scholars

- Julia Annas  `person_annas_julia_contemporary`
- László Bernáth  `person_bernath_laszlo_contemporary`
- Brad Inwood  `person_inwood_brad_contemporary`
- Martha Nussbaum  `person_nussbaum_martha_contemporary`
- Derk Pereboom  `person_pereboom_derk_contemporary`
- Juliana Acosta López de Mesa  `scholar_acosta_l_pez_de_mesa_j`
- Antonina Alberti  `scholar_alberti_a`
- Emmanuel Amand de Mendieta  `scholar_amand_de_mendieta_e`
- Carl Andresen  `scholar_andresen_carl`
- Antonella Astolfi  `scholar_astolfi_a`
- John M. G. Barclay  `scholar_barclay_j`
- Gustave Bardy  `scholar_bardy_g`
- John Behr  `scholar_behr_john`
- Mauro Belcastro  `scholar_belcastro_m`
- Richard Bett  `scholar_bett_richard`
- Michael F. Bird  `scholar_bird_m`
- Thomas A. Blackson  `scholar_blackson_t`
- Ben C. Blackwell  `scholar_blackwell_b`
- Paul M. Blowers  `scholar_blowers_paul`
- Philippe Bobichon  `scholar_bobichon_p`
- Marcelo D. Boeri  `scholar_boeri_marcelo`
- Ernesto Bonaiuti  `scholar_bonaiuti_e`
- Mauro Bonazzi  `scholar_bonazzi_mauro`
- Marie-Odile Boulnois  `scholar_boulnois_m`
- George Boys-Stones  `scholar_boys_stones_g`
- Miryam T. Brand  `scholar_brand_miryam`
- Marcel Brass  `scholar_brass_m`
- Tad Brennan  `scholar_brennan_tad`
- Cilliers Breytenbach  `scholar_breytenbach_c`
- Sarah Broadie  `scholar_broadie_sarah`
- René Brouwer  `scholar_brouwer_r`
- Jacques Brunschwig  `scholar_brunschwig_jacques`
- Simon Butticaz  `scholar_butticaz_s`
- T. Ryan Byerly  `scholar_byerly_t`
- Jason W. Carter  `scholar_carter_jason`
- Phillip Cary  `scholar_cary_p`
- Charles Chamberlain  `scholar_chamberlain_c`
- Viviane Comerro  `scholar_comerro_v`
- Ursula Coope  `scholar_coope_ursula`
- John Cooper  `scholar_cooper_john`
- Wayne Coppins  `scholar_coppins_w`
- William Lane Craig  `scholar_craig_w`
- Frank Moore Cross  `scholar_cross_f`
- Henri Crouzel  `scholar_crouzel_henri`
- Michel Crubellier  `scholar_crubellier_m`
- Micah Currado  `scholar_currado_m`
- Brian E. Daley  `scholar_daley_b`
- Jean Daniélou  `scholar_danielou_j`
- François DE MONNERON  `scholar_de_monneron_f`
- Oisín Deery  `scholar_deery_o`
- Nicola Denzey Lewis  `scholar_denzey_lewis_n`
- Andreas DETTWILER  `scholar_dettwiler_a`
- Gianluca Di Muzio  `scholar_di_muzio_g`
- John Dillon  `scholar_dillon_john`
- Olivier D'Jeranian  `scholar_djeranian_o`
- Robert F. Dobbin  `scholar_dobbin_r`
- Joseph R. Dodson  `scholar_dodson_j`
- Pier Luigi Donini  `scholar_donini_p`
- Richard Double  `scholar_double_r`
- James D. G. Dunn  `scholar_dunn_j`
- Susan Grove Eastman  `scholar_eastman_susan`
- Javier Echeñique  `scholar_eche_ique_j`
- Mark J. Edwards  `scholar_edwards_mark`
- Erik Eliasson  `scholar_eliasson_e`
- Troels Engberg-Pedersen  `scholar_engberg_pedersen_t`
- Timo Eskola  `scholar_eskola_t`
- Stephen Everson  `scholar_everson_s`
- Jacques Fantino  `scholar_fantino_j`
- Richard Faure  `scholar_faure_r`
- Gordon D. Fee  `scholar_fee_g`
- Joseph A. Fitzmyer  `scholar_fitzmyer_j`
- Maximilian Forschner  `scholar_forschner_maximilian`
- Dorothea Frede  `scholar_frede_dorothea`
- Peter Frick  `scholar_frick_p`
- David J. Furley  `scholar_furley_david`
- René-Antoine Gauthier  `scholar_gauthier_r_a`
- Beverly Roberts Gaventa  `scholar_gaventa_b`
- Lloyd P. Gerson  `scholar_gerson_l`
- Kathleen Gibbons  `scholar_gibbons_k`
- Christopher Gill  `scholar_gill_christopher`
- Laura Liliana Gómez  `scholar_gomez_laura`
- P. W. Gooch  `scholar_gooch_p`
- John K. Goodrich  `scholar_goodrich_j`
- Peter Gorday  `scholar_gorday_p`
- Jean-Baptiste Gourinat  `scholar_gourinat_jean_baptiste`
- Andreas Graeser  `scholar_graeser_a`
- Robert M. Grant  `scholar_grant_r`
- Margaret Graver  `scholar_graver_margaret`
- Filip Grgić  `scholar_grgi_f`
- Jean-Baptiste Guillon  `scholar_guillon_j`
- Gweltaz Guyomarc'h  `scholar_guyomarc_h_g`
- Klaus Haacker  `scholar_haacker_k`
- Pierre Hadot  `scholar_hadot_pierre`
- Patrick Haggard  `scholar_haggard_p`
- Claire Hall  `scholar_hall_c`
- Stuart George Hall  `scholar_hall_sg`
- R. J. Hankinson  `scholar_hankinson_rj`
- W. F. R. Hardie  `scholar_hardie_w_f_r`
- Marguerite Harl  `scholar_harl_m`
- Marco Hausmann  `scholar_hausmann_m`
- Matyáš Havrda  `scholar_havrda_m`
- A. P. Hayman  `scholar_hayman_a`
- Paul Helm  `scholar_helm_p`
- William Hendriksen  `scholar_hendriksen_w`
- Christian Hengstermann  `scholar_hengstermann_christian`
- John Hick  `scholar_hick_j`
- Ronja Hildebrandt  `scholar_hildebrandt_ronja`
- Albert L. A. Hogeterp  `scholar_hogeterp_a`
- Ted Honderich  `scholar_honderich_t`
- Christoph Horn  `scholar_horn_christoph`
- Pamela M. Huby  `scholar_huby_pamela`
- J. Philip Hyatt  `scholar_hyatt_jp`
- T. H. Irwin  `scholar_irwin_terence`
- Anders-Christian Jacobsen  `scholar_jacobsen_a`
- Annie Jaubert  `scholar_jaubert_a`
- Robert Jewett  `scholar_jewett_r`
- Monte Ransome Johnson  `scholar_johnson_monte`
- Fabienne Jourdan  `scholar_jourdan_f`
- Dennis W. Jowers  `scholar_jowers_d`
- Izabela Jurasz  `scholar_jurasz_i`
- Charles H. Kahn  `scholar_kahn_charles`
- George E. Karamanolis  `scholar_karamanolis_george`
- Anthony Kenny  `scholar_kenny_anthony`
- I. G. Kidd  `scholar_kidd_ig`
- Peter King  `scholar_king_p`
- Jonathan Klawans  `scholar_klawans_jonathan`
- Theo Kobusch  `scholar_kobusch_theo`
- Isabelle Koch  `scholar_koch_i`
- Renée Koch Piettre  `scholar_koch_piettre_r`
- Marcin Kowalski  `scholar_kowalski_m`
- Gerd Lüdemann  `scholar_l_demann_g`
- Winrich Alfried Löhr  `scholar_l_hr_w`
- Antti Laato  `scholar_laato_a`
- Jean-Louis Labarrière  `scholar_labarri_re_j`
- Béatrice Lienemann  `scholar_lienemann_beatrice`
- Andreas Lindemann  `scholar_lindemann_a`
- Paul Linjamaa  `scholar_linjamaa_p`
- Nicholas List  `scholar_list_n`
- Andrew Louth  `scholar_louth_a`
- Aldo Magris  `scholar_magris_aldo`
- Jaap Mansfeld  `scholar_mansfeld_j`
- Christoph Markschies  `scholar_markschies_christoph`
- Luther H. Martin  `scholar_martin_l`
- Stefano Maso  `scholar_maso_s`
- Jason Maston  `scholar_maston_j`
- Sara Matteoli  `scholar_matteoli_s`
- Anne Merker  `scholar_merker_a`
- Susan Sauvé Meyer  `scholar_meyer_s`
- Cyrille Michon  `scholar_michon_c`
- Denis Minns  `scholar_minns_d`
- Phillip Mitsis  `scholar_mitsis_phillip`
- John Moon  `scholar_moon_j`
- George Foot Moore  `scholar_moore_g`
- Pierre-Marie Morel  `scholar_morel_pierre_marie`
- Jörn Müller  `scholar_muller_j`
- Charles Munier  `scholar_munier_c`
- Thomas Nadelhoffer  `scholar_nadelhoffer_t`
- Mako A. Nagasawa  `scholar_nagasawa_m`
- Jean-Marc Narbonne  `scholar_narbonne_j`
- Carlo Natali  `scholar_natali_c`
- Benjamin J. Nickodemus  `scholar_nickodemus_b`
- Karen Margrethe Nielsen  `scholar_nielsen_k`
- David E. Nyström  `scholar_nystr_m_d`
- Tim O'Keefe  `scholar_o_keefe_t`
- Julien Olive  `scholar_olive_j`
- B. J. Oropeza  `scholar_oropeza_b`
- Lluis Oviedo  `scholar_oviedo_l`
- Matthew C. Pawlak  `scholar_pawlak_m`
- Lorenzo Perrone  `scholar_perrone_l`
- Fabienne Pironet  `scholar_pironet_f`
- Alvin Plantinga  `scholar_plantinga_a`
- Bernard Pouderon  `scholar_pouderon_b`
- Jean G. Préaux  `scholar_pr_aux_j`
- Pierre Prigent  `scholar_prigent_p`
- Claude Rambaux  `scholar_rambaux_c`
- Ilaria Ramelli  `scholar_ramelli_ilaria`
- Maguelone Renard  `scholar_renard_m`
- Cyril C. Richardson  `scholar_richardson_c`
- John M. Rist  `scholar_rist_john`
- Adelin Rousseau  `scholar_rousseau_a`
- David T. Runia  `scholar_runia_d`
- Gilbert Ryle  `scholar_ryle_g`
- François Sagnard  `scholar_sagnard_f`
- Robert M. Sapolsky  `scholar_sapolsky_r`
- Lawrence H. Schiffman  `scholar_schiffman_l`
- Jean-Pierre Schneider  `scholar_schneider_j`
- Eberhard Schockenhoff  `scholar_schockenhoff_e`
- Malcolm Schofield  `scholar_schofield_malcolm`
- Jens Schröter  `scholar_schr_ter_j`
- Jared Secord  `scholar_secord_j`
- Robert W. Sharples  `scholar_sharples_robert`
- Oskar Skarsaune  `scholar_skarsaune_o`
- Tamler Sommers  `scholar_sommers_t`
- Carlos Steel  `scholar_steel_carlos`
- Todd D. Still  `scholar_still_t`
- Gisela Striker  `scholar_striker_gisela`
- Eleonore Stump  `scholar_stump_e`
- Lee W. Sytsma  `scholar_sytsma_lee`
- Daniela Patrizia Taormina  `scholar_taormina_daniela`
- W. Telfer  `scholar_telfer_w`
- Teun Tieleman  `scholar_tieleman_t`
- Kevin Timpe  `scholar_timpe_k`
- Daniel Jonathan Tolan  `scholar_tolan_d`
- James E. Tomberlin  `scholar_tomberlin_j`
- Danilo Šuster  `scholar_uster_d`
- George H. van Kooten  `scholar_van_kooten_g`
- Manuel Vargas  `scholar_vargas_m`
- Leandro Velardo  `scholar_velardo_l`
- Klaus Vibe  `scholar_vibe_k`
- Stephen J. Vicchio  `scholar_vicchio_s`
- Leigh Vicens  `scholar_vicens_l`
- Emmanuele Vimercati  `scholar_vimercati_emmanuele`
- Paul Chua Wang  `scholar_wang_p`
- Kyle B. Wells  `scholar_wells_k`
- Rodney Werline  `scholar_werline_r`
- James Wetzel  `scholar_wetzel_james`
- Christian Wildberg  `scholar_wildberg_christian`
- Bernard Williams  `scholar_williams_b`
- Harry Austryn Wolfson  `scholar_wolfson_h`
- Michael Wolter  `scholar_wolter_m`
- Simon Shengjian Xie  `scholar_xie_s`
- Stephen L. Young  `scholar_young_s`
- Magnus Zetterholm  `scholar_zetterholm_m`
