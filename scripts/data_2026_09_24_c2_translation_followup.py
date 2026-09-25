"""Decisions — follow-up of the C2 translation review (same machine batch), 2026-09-24.

Scope: the remaining machine translations of the works where the first batch found systematic
defects (Melito, Hermas, Barnabas, Theophilus, Contra Celsum V-VII) with Jev same_content < 0.7,
plus the remaining synopses written in the editor's voice (Hermas, Chrysostom). Every pair was
read. Same verdict scheme and notation as scripts/data_2026_09_24_c2_misaligned_translations.py.
Pairs with Jev >= 0.7 in these works were sampled (Melito 18, Contra Celsum V-VI 40): all faithful.
"""

DECISIONS = [
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc123_melito_peri_pascha_chap4_en', 'sc123_melito_peri_pascha_chap4', 'aligned_partial', 0.38),
    # the Greek says the type was precious before the truth and the parable wonderful before its interpretation; the English turns this into ‹the Law was once valuable, but it was abandoned› and drops type and parable — not a rendering
    ('sc123_melito_peri_pascha_chap41_en', 'sc123_melito_peri_pascha_chap41', 'misaligned', 0.51),
    # the English renders the neighbouring chapter (‹when the church arose and the Gospel took precedence, the type was emptied›), not this chapter (the Law fulfilled, the people emptied, the type dissolved, and today what was once precious has become worthless)
    ('sc123_melito_peri_pascha_chap43_en', 'sc123_melito_peri_pascha_chap43', 'misaligned', 0.43),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc123_melito_peri_pascha_chap80_en', 'sc123_melito_peri_pascha_chap80', 'aligned_partial', 0.58),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('This is a transformation not only of external behavior but of the soul ...')
    ('sc147_origenes_contra_celsum_v_par33_a_en', 'sc147_origenes_contra_celsum_v_par33_a', 'misaligned', 0.31),
    # pseudo-translation: 'But Origen interprets this saying differently ...' — third-person commentary, not a rendering of the Greek
    ('sc147_origenes_contra_celsum_v_par40_en', 'sc147_origenes_contra_celsum_v_par40', 'misaligned', 0.37),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('But this rhetorical dismissal is not an argument ...')
    ('sc147_origenes_contra_celsum_v_par41_a_en', 'sc147_origenes_contra_celsum_v_par41_a', 'misaligned', 0.35),
    # pseudo-translation: a summary of Celsus' claim followed by 'We say: ...' — not a rendering of the Greek
    ('sc147_origenes_contra_celsum_v_par44_en', 'sc147_origenes_contra_celsum_v_par44', 'misaligned', 0.4),
    # pseudo-translation: the English speaks of 'exorcists and theurgists' and an 'intrinsic power (dynamis)' of Hebrew names; the Greek discusses the meaning of the names Abraham, Isaac and Jacob translated into Greek
    ('sc147_origenes_contra_celsum_v_par45_a_en', 'sc147_origenes_contra_celsum_v_par45_a', 'misaligned', 0.41),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_v_par47_en', 'sc147_origenes_contra_celsum_v_par47', 'aligned_partial', 0.53),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_v_par48_en', 'sc147_origenes_contra_celsum_v_par48', 'aligned_partial', 0.61),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_v_par5_en', 'sc147_origenes_contra_celsum_v_par5', 'aligned_partial', 0.32),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_v_par50_en', 'sc147_origenes_contra_celsum_v_par50', 'aligned_partial', 0.46),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_v_par59_en', 'sc147_origenes_contra_celsum_v_par59', 'aligned_partial', 0.69),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_v_par65_en', 'sc147_origenes_contra_celsum_v_par65', 'aligned_partial', 0.37),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_vi_par17_b_en', 'sc147_origenes_contra_celsum_vi_par17_b', 'aligned_partial', 0.43),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek (the Greek says going beyond the teaching on punishment is not useful for the many; the English makes it 'a matter for those more advanced in understanding')
    ('sc147_origenes_contra_celsum_vi_par26_a_en', 'sc147_origenes_contra_celsum_vi_par26_a', 'misaligned', 0.55),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('He attributes to Christians certain formulas and passwords that belong entirely to the Ophian sect')
    ('sc147_origenes_contra_celsum_vi_par27_en', 'sc147_origenes_contra_celsum_vi_par27', 'misaligned', 0.33),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('We have directly examined these heretical systems and can distinguish them from authentic Christianity')
    ('sc147_origenes_contra_celsum_vi_par32_en', 'sc147_origenes_contra_celsum_vi_par32', 'misaligned', 0.37),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('Such ideas may be found among the Valentinians but are not mainstream Church doctrine')
    ('sc147_origenes_contra_celsum_vi_par35_a_en', 'sc147_origenes_contra_celsum_vi_par35_a', 'misaligned', 0.31),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('Celsus—what a man!—wishing to attack Christianity makes no distinction ...')
    ('sc147_origenes_contra_celsum_vi_par37_a_en', 'sc147_origenes_contra_celsum_vi_par37_a', 'misaligned', 0.31),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('These are slanders against Christians that have no basis in truth ...')
    ('sc147_origenes_contra_celsum_vi_par40_en', 'sc147_origenes_contra_celsum_vi_par40', 'misaligned', 0.42),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek (a summary sentence on Pherecydes 'interpreting mythological battles as cosmic principles')
    ('sc147_origenes_contra_celsum_vi_par42_a_en', 'sc147_origenes_contra_celsum_vi_par42_a', 'misaligned', 0.33),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_vi_par46_en', 'sc147_origenes_contra_celsum_vi_par46', 'aligned_partial', 0.39),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('Those who wish to study these matters more thoroughly can find abundant material ...')
    ('sc147_origenes_contra_celsum_vi_par46_b_en', 'sc147_origenes_contra_celsum_vi_par46_b', 'misaligned', 0.33),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc147_origenes_contra_celsum_vi_par47_a_en', 'sc147_origenes_contra_celsum_vi_par47_a', 'aligned_partial', 0.31),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('His criticism is therefore inconsistent')
    ('sc147_origenes_contra_celsum_vi_par48_en', 'sc147_origenes_contra_celsum_vi_par48', 'misaligned', 0.36),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('If he means the literal surface of the text, we agree that there is something more profound beneath it ...')
    ('sc147_origenes_contra_celsum_vi_par49_en', 'sc147_origenes_contra_celsum_vi_par49', 'misaligned', 0.4),
    # hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('The proof of a doctrine's truth lies also in its practical power to convert and heal souls')
    ('sc147_origenes_contra_celsum_vi_par5_a_en', 'sc147_origenes_contra_celsum_vi_par5_a', 'misaligned', 0.33),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc172_epistula_barnabae_chap_10_verset_3a_5c_en', 'sc172_epistula_barnabae_chap_10_verset_3a_5c', 'aligned_partial', 0.65),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc172_epistula_barnabae_chap_10_verset_6a_8c_en', 'sc172_epistula_barnabae_chap_10_verset_6a_8c', 'aligned_partial', 0.67),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc172_epistula_barnabae_chap_11_verset_2_5_en', 'sc172_epistula_barnabae_chap_11_verset_2_5', 'aligned_partial', 0.43),
    # the English begins with a different verse ('Blessed are those who, having hoped in the cross, descended into the water') and does not start with 11.9a ('And again another prophet says ...')
    ('sc172_epistula_barnabae_chap_11_verset_9a_11b_en', 'sc172_epistula_barnabae_chap_11_verset_9a_11b', 'misaligned', 0.32),
    # English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_12_verset_4_en', 'sc172_epistula_barnabae_chap_12_verset_4', 'aligned_exceeds', 0.37),
    # English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_16_verset_3_4b_en', 'sc172_epistula_barnabae_chap_16_verset_3_4b', 'aligned_exceeds', 0.35),
    # the English begins mid-way ('But it will be built in the name of the Lord. Give heed ...') and omits 16.6a–6c (whether there is a temple of God)
    ('sc172_epistula_barnabae_chap_16_verset_6a_10b_en', 'sc172_epistula_barnabae_chap_16_verset_6a_10b', 'misaligned', 0.35),
    # English renders this passage and then runs on into the following verses (coverage exceeds the locus)
    ('sc172_epistula_barnabae_chap_20_verset_1a_1b_en', 'sc172_epistula_barnabae_chap_20_verset_1a_1b', 'aligned_exceeds', 0.52),
    # the English begins at 20.2a ('persecutors of the good') and omits the catalogue of vices of 20.1c
    ('sc172_epistula_barnabae_chap_20_verset_1c_2k_en', 'sc172_epistula_barnabae_chap_20_verset_1c_2k', 'misaligned', 0.66),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc172_epistula_barnabae_chap_21_verset_8_9a_en', 'sc172_epistula_barnabae_chap_21_verset_8_9a', 'aligned_partial', 0.55),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc172_epistula_barnabae_chap_6_verset_5_7_en', 'sc172_epistula_barnabae_chap_6_verset_5_7', 'aligned_partial', 0.57),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc172_epistula_barnabae_chap_6_verset_8_9b_en', 'sc172_epistula_barnabae_chap_6_verset_8_9b', 'aligned_partial', 0.35),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc172_epistula_barnabae_chap_9_verset_1a_3d_en', 'sc172_epistula_barnabae_chap_9_verset_1a_3d', 'aligned_partial', 0.42),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_11_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_11', 'aligned_partial', 0.47),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_12_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_12', 'aligned_partial', 0.54),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_13_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_13', 'aligned_partial', 0.54),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_16_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_16', 'aligned_partial', 0.63),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_17_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_17', 'aligned_partial', 0.62),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_19_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_19', 'aligned_partial', 0.47),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_2_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_2', 'aligned_partial', 0.62),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_21_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_21', 'aligned_partial', 0.66),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_23_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_23', 'aligned_partial', 0.69),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_25_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_25', 'aligned_partial', 0.66),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_28_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_28', 'aligned_partial', 0.66),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_29_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_29', 'aligned_partial', 0.57),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_3_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_3', 'aligned_partial', 0.55),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_30_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_30', 'aligned_partial', 0.62),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_31_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_31', 'aligned_partial', 0.63),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_33_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_33', 'aligned_partial', 0.69),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_34_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_34', 'aligned_partial', 0.59),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_35_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_35', 'aligned_partial', 0.45),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_36_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_36', 'aligned_partial', 0.6),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_38_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_38', 'aligned_partial', 0.58),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_4_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_4', 'aligned_partial', 0.52),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_5_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_5', 'aligned_partial', 0.42),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_6_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_6', 'aligned_partial', 0.44),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_9_en', 'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_9', 'aligned_partial', 0.65),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_11_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_11', 'aligned_partial', 0.61),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_12_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_12', 'aligned_partial', 0.54),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_13_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_13', 'aligned_partial', 0.35),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_14_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_14', 'aligned_partial', 0.52),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_15_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_15', 'aligned_partial', 0.61),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_16_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_16', 'aligned_partial', 0.61),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_17_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_17', 'aligned_partial', 0.49),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_18_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_18', 'aligned_partial', 0.46),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_19_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_19', 'aligned_partial', 0.41),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_2_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_2', 'aligned_partial', 0.67),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_20_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_20', 'aligned_partial', 0.62),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_21_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_21', 'aligned_partial', 0.69),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_23_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_23', 'aligned_partial', 0.56),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_24_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_24', 'aligned_partial', 0.51),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_25_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_25', 'aligned_partial', 0.62),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_28_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_28', 'aligned_partial', 0.66),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_3_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_3', 'aligned_partial', 0.52),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_5_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_5', 'aligned_partial', 0.65),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_7_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_7', 'aligned_partial', 0.53),
    # English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)
    ('sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_9_en', 'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_9', 'aligned_partial', 0.49),
    # synopsis in the editor's voice with a wrong frame ('those from the eleventh mountain') for a passage on rods two parts dry and one green
    ('sc53bis_hermas_pastor_chap75_en', 'sc53bis_hermas_pastor_chap75', 'misaligned', 0.36),
    # synopsis in the editor's voice of the same chapter ('This chapter concludes the eighth parable ...'), not a translation
    ('sc53bis_hermas_pastor_chap77_en', 'sc53bis_hermas_pastor_chap77', 'aligned_paraphrase', 0.5),
    # synopsis in the editor's voice of the same chapter ('This chapter describes the fifth of the twelve mountains ...'), not a translation
    ('sc53bis_hermas_pastor_chap99_en', 'sc53bis_hermas_pastor_chap99', 'aligned_paraphrase', 0.91),
    # synopsis in the editor's voice of the same chapter ('Chapter 11 of Chrysostom's On Providence ...'), not a translation
    ('sc79_chrysostomus_de_providentia_chap11_en', 'sc79_chrysostomus_de_providentia_chap11', 'aligned_paraphrase', 0.44),
    # synopsis in the editor's voice of the same chapter ('Chapter 12 of Chrysostom's On Providence ...'), not a translation
    ('sc79_chrysostomus_de_providentia_chap12_en', 'sc79_chrysostomus_de_providentia_chap12', 'aligned_paraphrase', 0.54),
    # synopsis in the editor's voice of the same chapter ('Chapter 13 of Chrysostom's On Providence ...'), not a translation
    ('sc79_chrysostomus_de_providentia_chap13_en', 'sc79_chrysostomus_de_providentia_chap13', 'aligned_paraphrase', 0.59),
    # synopsis in the editor's voice of the same chapter ('Chapter 15 of Chrysostom's On Providence ...'), not a translation
    ('sc79_chrysostomus_de_providentia_chap15_en', 'sc79_chrysostomus_de_providentia_chap15', 'aligned_paraphrase', 0.58),
]

NOTES = {
    'sc123_melito_peri_pascha_chap4_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc123_melito_peri_pascha_chap41_en': 'the Greek says the type was precious before the truth and the parable wonderful before its interpretation; the English turns this into ‹the Law was once valuable, but it was abandoned› and drops type and parable — not a rendering',
    'sc123_melito_peri_pascha_chap43_en': "the English renders the neighbouring chapter (‹when the church arose and the Gospel took precedence, the type was emptied›), not this chapter (the Law fulfilled, the people emptied, the type dissolved, and today what was once precious has become worthless)",
    'sc123_melito_peri_pascha_chap80_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_v_par33_a_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('This is a transformation not only of external behavior but of the soul ...')",
    'sc147_origenes_contra_celsum_v_par40_en': "pseudo-translation: 'But Origen interprets this saying differently ...' — third-person commentary, not a rendering of the Greek",
    'sc147_origenes_contra_celsum_v_par41_a_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('But this rhetorical dismissal is not an argument ...')",
    'sc147_origenes_contra_celsum_v_par44_en': "pseudo-translation: a summary of Celsus' claim followed by 'We say: ...' — not a rendering of the Greek",
    'sc147_origenes_contra_celsum_v_par45_a_en': "pseudo-translation: the English speaks of 'exorcists and theurgists' and an 'intrinsic power (dynamis)' of Hebrew names; the Greek discusses the meaning of the names Abraham, Isaac and Jacob translated into Greek",
    'sc147_origenes_contra_celsum_v_par47_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_v_par48_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_v_par5_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_v_par50_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_v_par59_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_v_par65_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_vi_par17_b_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_vi_par26_a_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek (the Greek says going beyond the teaching on punishment is not useful for the many; the English makes it 'a matter for those more advanced in understanding')",
    'sc147_origenes_contra_celsum_vi_par27_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('He attributes to Christians certain formulas and passwords that belong entirely to the Ophian sect')",
    'sc147_origenes_contra_celsum_vi_par32_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('We have directly examined these heretical systems and can distinguish them from authentic Christianity')",
    'sc147_origenes_contra_celsum_vi_par35_a_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('Such ideas may be found among the Valentinians but are not mainstream Church doctrine')",
    'sc147_origenes_contra_celsum_vi_par37_a_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('Celsus—what a man!—wishing to attack Christianity makes no distinction ...')",
    'sc147_origenes_contra_celsum_vi_par40_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('These are slanders against Christians that have no basis in truth ...')",
    'sc147_origenes_contra_celsum_vi_par42_a_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek (a summary sentence on Pherecydes 'interpreting mythological battles as cosmic principles')",
    'sc147_origenes_contra_celsum_vi_par46_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_vi_par46_b_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('Those who wish to study these matters more thoroughly can find abundant material ...')",
    'sc147_origenes_contra_celsum_vi_par47_a_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc147_origenes_contra_celsum_vi_par48_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('His criticism is therefore inconsistent')",
    'sc147_origenes_contra_celsum_vi_par49_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('If he means the literal surface of the text, we agree that there is something more profound beneath it ...')",
    'sc147_origenes_contra_celsum_vi_par5_a_en': "hybrid pseudo-translation: the opening renders the Greek, then the English closes with commentary absent from the Greek ('The proof of a doctrine's truth lies also in its practical power to convert and heal souls')",
    'sc172_epistula_barnabae_chap_10_verset_3a_5c_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc172_epistula_barnabae_chap_10_verset_6a_8c_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc172_epistula_barnabae_chap_11_verset_2_5_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc172_epistula_barnabae_chap_11_verset_9a_11b_en': "the English begins with a different verse ('Blessed are those who, having hoped in the cross, descended into the water') and does not start with 11.9a ('And again another prophet says ...')",
    'sc172_epistula_barnabae_chap_12_verset_4_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_16_verset_3_4b_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_16_verset_6a_10b_en': "the English begins mid-way ('But it will be built in the name of the Lord. Give heed ...') and omits 16.6a–6c (whether there is a temple of God)",
    'sc172_epistula_barnabae_chap_20_verset_1a_1b_en': 'English renders this passage and then runs on into the following verses (coverage exceeds the locus)',
    'sc172_epistula_barnabae_chap_20_verset_1c_2k_en': "the English begins at 20.2a ('persecutors of the good') and omits the catalogue of vices of 20.1c",
    'sc172_epistula_barnabae_chap_21_verset_8_9a_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc172_epistula_barnabae_chap_6_verset_5_7_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc172_epistula_barnabae_chap_6_verset_8_9b_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc172_epistula_barnabae_chap_9_verset_1a_3d_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_11_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_12_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_13_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_16_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_17_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_19_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_2_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_21_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_23_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_25_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_28_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_29_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_3_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_30_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_31_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_33_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_34_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_35_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_36_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_38_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_4_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_5_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_6_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_9_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_11_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_12_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_13_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_14_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_15_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_16_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_17_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_18_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_19_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_2_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_20_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_21_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_23_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_24_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_25_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_28_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_3_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_5_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_7_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc20_theophilus_ad_autolycum_iii_liv_3_sur_la_question_prealable_chap_9_en': 'English renders the same passage (checked: opening and wording follow the original; coverage partial or condensed)',
    'sc53bis_hermas_pastor_chap75_en': "synopsis in the editor's voice with a wrong frame ('those from the eleventh mountain') for a passage on rods two parts dry and one green",
    'sc53bis_hermas_pastor_chap77_en': "synopsis in the editor's voice of the same chapter ('This chapter concludes the eighth parable ...'), not a translation",
    'sc53bis_hermas_pastor_chap99_en': "synopsis in the editor's voice of the same chapter ('This chapter describes the fifth of the twelve mountains ...'), not a translation",
    'sc79_chrysostomus_de_providentia_chap11_en': "synopsis in the editor's voice of the same chapter ('Chapter 11 of Chrysostom's On Providence ...'), not a translation",
    'sc79_chrysostomus_de_providentia_chap12_en': "synopsis in the editor's voice of the same chapter ('Chapter 12 of Chrysostom's On Providence ...'), not a translation",
    'sc79_chrysostomus_de_providentia_chap13_en': "synopsis in the editor's voice of the same chapter ('Chapter 13 of Chrysostom's On Providence ...'), not a translation",
    'sc79_chrysostomus_de_providentia_chap15_en': "synopsis in the editor's voice of the same chapter ('Chapter 15 of Chrysostom's On Providence ...'), not a translation",
}
