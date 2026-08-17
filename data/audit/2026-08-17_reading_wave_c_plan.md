# Plan d'ingestion — reading wave C — 2026-08-17

## 1. Résultat

La file NEXT 15, rangs 11 à 25, a été contrôlée dans l'ordre du rapport froid. Les quinze PDF ont été ouverts, leur texte a servi d'index de lecture et au moins une page argumentative de chaque fichier a été rendue en image pour vérifier pagination, lisibilité et portée. Tous les quinze produisent au moins un argument pertinent ; aucun ouvrage entier n'est donc rejeté. Les rendements faibles de Harl, Whitmarsh et Hodges sont conservés sans leur imposer une théorie du libre arbitre qu'ils ne soutiennent pas.

Le delta contient 110 nœuds nouveaux : 14 personnes, 12 publications et 84 arguments. Il déclare 271 arêtes : created_by=99, advanced_in=84, cites_primary_source=77, discusses=11. Trois enrichissements promeuvent des shells Origenality existants. Aucune arête dialectique moderne n'est créée : les divergences repérées ne donnent pas toujours un engagement direct contre une thèse déjà modélisée. Quatre verdicts explicitement incertains restent suspended.

Aucun texte grec ou latin n'a été produit. Les descriptions d'arguments sont en anglais ; les termes techniques n'apparaissent qu'en translittération. Aucun fichier de data/kg ou data/corpus n'a été écrit.

## 2. Contrôle R2 et promotions

La recherche d'identité dans data/kg/nodes.jsonl a conduit à réemployer scholar_harl_m et à promouvoir exactement :

- pub_holz_1970_uber_den_begriff_des_willens_und_der_freiheit_bei_origenes ;
- pub_holliday_2008_will_satan_be_saved_reconsidering_origen_theory_of_volition_in_p ;
- pub_heinze_2026_origen_on_demonic_executioners_and_the_problem_of_evil.

Pour Holliday, le conflit apparent est résolu sans réécrire l'identité : 2008 est l'année online-first portée par le DOI et le shell ; le PDF appartient au volume imprimé 63 de 2009. L'enrichissement ajoute print_year=2009, online_first_year=2008 et la note de réconciliation.

Les ancrages primaires sont exclusivement des œuvres ou passages déjà présents. Hodges et Harl n'ont pas reçu de cites_primary_source : les textes effectivement analysés n'ont pas de shell exact dans le KG et un rattachement à Tatien, Clément ou Origène aurait été forcé.

## 3. Périmètre de lecture et sauts motivés

| Rang | Ouvrage | Pages réellement lues | Saut motivé | Statut R2 |
|---:|---|---|---|---|
| 11 | J. Wytzes, « Paideia and Pronoia in the Works of Clemens Alexandrinus » | article intégral, pp. 148-158 | aucun saut | nouvelle publication |
| 12 | Judith L. Kovacs, « Divine Pedagogy and the Gnostic Teacher according to Clement of Alexandria » | article intégral, pp. 3-25 | aucun saut | nouvelle publication |
| 13 | Jon D. Ewing, The Christianization of Pronoia | abstract, sommaire et chapitre 6, pp. 125-173 | chap. 1-5 : traditions de fond déjà synthétisées dans le chapitre 6 ; chap. 7 et annexes : réception byzantine et récupération orthodoxe, sans nouveaux arguments Clément-liberté-providence | nouvelle publication |
| 14 | Hildegard König, Clemens von Alexandrien als Seelsorger | chapitres systématiques pp. 274-329 et synthèse pp. 364-369 | pp. 7-273 : biographie, institutions, genres et publics ; pp. 330-363 : développement détaillé des ministères et destinataires, sans nouvelle prémisse liberté-providence | nouvelle publication |
| 15 | Uwe Kühneweg, « Die griechischen Apologeten und die Ethik » | article intégral, pp. 112-120 | aucun saut | nouvelle publication |
| 16 | Elaine Pagels, « Christian Apologists and the Fall of the Angels » | article intégral, pp. 301-325 | aucun saut | nouvelle publication |
| 17 | Tim Whitmarsh, « Justin, Tatian and the Forging of a Christian Voice » | article intégral, pp. 123-144 | aucun saut ; seules les thèses rhétoriques utiles au statut des énoncés apologétiques sont retenues | nouvelle publication |
| 18 | Harald Holz, « Über den Begriff des Willens und der Freiheit bei Origenes » | article intégral, pp. 63-84 | aucun saut ; les reconstructions spéculatives sont signalées comme telles | promotion du shell Origenality |
| 19 | Lisa R. Holliday, « Will Satan Be Saved? » | article intégral, pp. 1-23 | aucun saut | promotion du shell ; 2008 = online first, 2009 = volume imprimé 63 |
| 20 | Carl Fries, « Zur Willensfreiheit bei Origenes » | article intégral, pp. 92-101 | non extraits : physiologie, analogies de sexologie et théorie personnelle du Urwille, historiographiquement datées et non probantes pour Origène | nouvelle publication |
| 21 | Hermut Löhr, « Paulus und der Wille zur Tat » | article intégral, pp. 165-188 | aucun saut | nouvelle publication |
| 22 | A. van den Beld, « Romans 7:14-25 and the Problem of Akrasia » | article intégral, pp. 495-515 | aucun saut ; le rapport attribuait A. et T., mais la page de titre et l'en-tête imprimés donnent Dr A. van den Beld seul | nouvelle publication |
| 23 | Horace Jeffery Hodges, « Gnostic Liberation from Astrological Determinism » | article intégral, pp. 359-373 | aucun saut ; aucun lien primaire forcé, faute de shell existant pour Pistis Sophia ou Trimorphic Protennoia | nouvelle publication |
| 24 | Marguerite Harl, « Problèmes posés par l'histoire du mot to autexousion » | compte rendu survivant intégral, p. XXVIII | le PDF ne contient pas la communication complète ; aucune extrapolation au-delà de la page conservée | nouvelle publication ; personne existante scholar_harl_m réemployée |
| 25 | Ky Heinze, Origen on Demonic Executioners and the Problem of Evil | chap. 1, sections utiles pp. 11-21 ; chap. 3 intégral pp. 40-67 | chap. 2, pp. 21-39 : histoire des traditions juives, chrétiennes et grecques antérieures, sans nouveau nœud argumentatif propre à Origène | promotion du shell Origenality |

## 4. Carte argumentative, attestations et ancrages

### Rang 11 — J. Wytzes, « Paideia and Pronoia in the Works of Clemens Alexandrinus »

Lecture : article intégral, pp. 148-158. Saut : aucun saut. R2 : nouvelle publication. Corridor : Clément : Stromates et Pédagogue.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 148-150 | scholarly_argument_wytzes_goodness_choice | Wytzes: divine goodness and human choice jointly frame Clement's paideia | work_clement_stromateis |
| 149-150 | scholarly_argument_wytzes_corrective_punishment | Wytzes: punishment corrects rather than avenges | work_clement_paedagogus |
| 150-153 | scholarly_argument_wytzes_postmortem_paideia | Wytzes: postmortem education points toward universal salvation, but the verdict remains suspended — verdict suspended | work_clement_stromateis |
| 152-155 | scholarly_argument_wytzes_differentiated_methods | Wytzes: the Logos uses differentiated methods to lead toward vision | work_clement_paedagogus |
| 155-158 | scholarly_argument_wytzes_continuous_paideia | Wytzes: continuous paideia reduces the unique explanatory role of the incarnation | work_clement_stromateis |

### Rang 12 — Judith L. Kovacs, « Divine Pedagogy and the Gnostic Teacher according to Clement of Alexandria »

Lecture : article intégral, pp. 3-25. Saut : aucun saut. R2 : nouvelle publication. Corridor : Clément : Stromates et Pédagogue.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 3-7 | scholarly_argument_kovacs_teacher_living_image | Kovacs: the Gnostic teacher is a living image participating in the divine plan | work_clement_stromateis |
| 6-8 | scholarly_argument_kovacs_adapted_pedagogy | Kovacs: pedagogy differentiates punishment, hope, and mystery by readiness | work_clement_stromateis |
| 7-10 | scholarly_argument_kovacs_staged_curriculum | Kovacs: law and philosophy prepare staged faith and knowledge | work_clement_stromateis |
| 10 | scholarly_argument_kovacs_endless_progress | Kovacs: Clement turns provisional progress into endless development | work_clement_stromateis |
| 11-17 | scholarly_argument_kovacs_whole_person_psychagogy | Kovacs: psychagogy forms the whole person through care and correction | work_clement_paedagogus |
| 17-25 | scholarly_argument_kovacs_responsible_concealment | Kovacs: pedagogical concealment protects immature students | work_clement_stromateis |

### Rang 13 — Jon D. Ewing, The Christianization of Pronoia

Lecture : abstract, sommaire et chapitre 6, pp. 125-173. Saut : chap. 1-5 : traditions de fond déjà synthétisées dans le chapitre 6 ; chap. 7 et annexes : réception byzantine et récupération orthodoxe, sans nouveaux arguments Clément-liberté-providence. R2 : nouvelle publication. Corridor : Clément : Stromates.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 125-126 | scholarly_argument_ewing_creative_synthesis | Ewing: Clement's providence is a creative synthesis, not source dependence | work_clement_stromateis |
| 127-143 | scholarly_argument_ewing_redirected_choice | Ewing: providence redirects misused choice without authoring evil | work_clement_stromateis |
| 128-145 | scholarly_argument_ewing_permitted_persecution | Ewing: persecution is permitted rather than willed by God | work_clement_stromateis |
| 145-147 | scholarly_argument_ewing_personalized_providence | Ewing: Clement personalizes Philonic providence in the Logos | work_clement_stromateis |
| 148 | scholarly_argument_ewing_generic_philosophy | Ewing: philosophy reaches generic providence but not the Son's economy | work_clement_stromateis |
| 149 | scholarly_argument_ewing_secondary_causes | Ewing: secondary causes require human assent and preserve agency | work_clement_stromateis |
| 151-152, 168 | scholarly_argument_ewing_mercy_over_fate | Ewing: providence proceeds from mercy rather than necessity and frees from fate | work_clement_stromateis |
| 154-157 | scholarly_argument_ewing_universal_preparation | Ewing: providence universalizes law and philosophy as preparation | work_clement_stromateis |
| 158-168 | scholarly_argument_ewing_stoic_pervasion | Ewing: Clement adopts Stoic pervasion but rejects the identity of providence and fate | work_clement_stromateis |
| 169-173 | scholarly_argument_ewing_son_possesses_providence | Ewing: Clement makes providence a personal possession of the Son | work_clement_stromateis |

### Rang 14 — Hildegard König, Clemens von Alexandrien als Seelsorger

Lecture : chapitres systématiques pp. 274-329 et synthèse pp. 364-369. Saut : pp. 7-273 : biographie, institutions, genres et publics ; pp. 330-363 : développement détaillé des ministères et destinataires, sans nouvelle prémisse liberté-providence. R2 : nouvelle publication. Corridor : Clément : Protreptique, Pédagogue et Stromates.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 274-275 | scholarly_argument_koenig_soul_choice_risk | König: the soul is both the seat of free decision and pastoral risk | work_clement_protrepticus |
| 276-280 | scholarly_argument_koenig_therapy_repentance | König: pedagogy is therapy because free souls can repent | work_clement_paedagogus |
| 279-280, 303-305 | scholarly_argument_koenig_pastoral_punishment | König: legal punishment has a pastoral function | work_clement_stromateis |
| 288-294 | scholarly_argument_koenig_active_care | König: care for others ranks above solitary self-perfection | work_clement_stromateis |
| 296-302 | scholarly_argument_koenig_varied_means | König: providence varies commands, threats, signs, and promises | work_clement_stromateis |
| 317-321 | scholarly_argument_koenig_grace_without_force | König: grace precedes choice without saving anyone by force | work_clement_stromateis |
| 321-324 | scholarly_argument_koenig_grace_grounded_optimism | König: moral optimism is grounded in providence, not self-sufficiency | work_clement_stromateis |
| 324-327, 364-368 | scholarly_argument_koenig_mimetic_care | König: Clement's pastoral system is Christ-centered and mimetic | work_clement_stromateis |

### Rang 15 — Uwe Kühneweg, « Die griechischen Apologeten und die Ethik »

Lecture : article intégral, pp. 112-120. Saut : aucun saut. R2 : nouvelle publication. Corridor : Justin : Première et Seconde Apologies, passage 1 Apol. 43.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 112-114 | scholarly_argument_kuehneweg_systematic_grounding | Kühneweg: apologetic originality lies in the systematic grounding of ethics | work_justin_first_apology |
| 113-114 | scholarly_argument_kuehneweg_reason_and_logos | Kühneweg: natural discernment and the incarnate Logos ground conduct | work_justin_first_apology |
| 115 | scholarly_argument_kuehneweg_judgment_safeguard | Kühneweg: Justin's free will safeguards responsibility and judgment | passage_justin_1apol_43 |
| 115-117 | scholarly_argument_kuehneweg_externalized_evil | Kühneweg: demonology externalizes evil and leaves first angelic choice unexplained | work_justin_second_apology_sc507 |
| 117-118 | scholarly_argument_kuehneweg_common_perfection | Kühneweg: restored knowledge makes moral perfection a common Christian possibility | work_justin_first_apology |

### Rang 16 — Elaine Pagels, « Christian Apologists and the Fall of the Angels »

Lecture : article intégral, pp. 301-325. Saut : aucun saut. R2 : nouvelle publication. Corridor : Justin, Athénagore et Clément.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 301-304 | scholarly_argument_pagels_imperial_indictment | Pagels: the angelic fall indicts imperial power | work_justin_second_apology_sc507 |
| 304-308 | scholarly_argument_pagels_reversed_power | Pagels: apologetic rhetoric depicts the ruler as enslaved and the martyr as free | work_justin_first_apology |
| 308-310 | scholarly_argument_pagels_limited_obedience | Pagels: civil obedience is limited by religious refusal | work_athenagoras_legatio_sc379 |
| 310-313 | scholarly_argument_pagels_moral_revaluation | Pagels: demonizing the gods supports radical moral revaluation | work_clement_protrepticus |
| 319-322 | scholarly_argument_pagels_rational_equality | Pagels: the divine image democratizes rational and moral equality | work_clement_stromateis |
| 322-325 | scholarly_argument_pagels_christian_liberty | Pagels: Christian liberty joins release from passions to resistance to coercion | work_clement_protrepticus |

### Rang 17 — Tim Whitmarsh, « Justin, Tatian and the Forging of a Christian Voice »

Lecture : article intégral, pp. 123-144. Saut : aucun saut ; seules les thèses rhétoriques utiles au statut des énoncés apologétiques sont retenues. R2 : nouvelle publication. Corridor : Justin : Apologies ; Tatien : Oratio.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 123-126 | scholarly_argument_whitmarsh_polarized_identities | Whitmarsh: apologetic writing produces polarized identities | work_justin_first_apology |
| 128-131 | scholarly_argument_whitmarsh_generic_bricolage | Whitmarsh: Justin and Tatian use generic bricolage in an imaginary forum | work_tatian_oratio |
| 130-133 | scholarly_argument_whitmarsh_antagonistic_groups | Whitmarsh: rhetorical performance creates the antagonistic groups it addresses | work_justin_first_apology |
| 135-139 | scholarly_argument_whitmarsh_martyr_verdict | Whitmarsh: Justin's martyr autobiography authorizes speech, but historical fulfillment remains suspended — verdict suspended | work_justin_second_apology_sc507 |
| 140-144 | scholarly_argument_whitmarsh_experimental_voice | Whitmarsh: Tatian's Christian voice is mimetic and experimental | work_tatian_oratio |

### Rang 18 — Harald Holz, « Über den Begriff des Willens und der Freiheit bei Origenes »

Lecture : article intégral, pp. 63-84. Saut : aucun saut ; les reconstructions spéculatives sont signalées comme telles. R2 : promotion du shell Origenality. Corridor : Origène : De principiis.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 63-64 | scholarly_argument_holz_dynamic_core | Holz: will and freedom are a dynamic systematic core in Origen | work_de_principiis_origen_230s_v2w3x4y5 |
| 68-71 | scholarly_argument_holz_nonarbitrary_absolute_will | Holz: absolute will means self-determination rather than arbitrariness | work_de_principiis_origen_230s_v2w3x4y5 |
| 73-75 | scholarly_argument_holz_restoration_without_coercion | Holz: restoration requires the good to prevail without coercion — verdict suspended | work_de_principiis_origen_230s_v2w3x4y5 |
| 77-78 | scholarly_argument_holz_primordial_choice | Holz: primordial choice differentiates originally equal intellects | work_de_principiis_origen_230s_v2w3x4y5 |
| 79-84 | scholarly_argument_holz_freedom_tension | Holz: reparable evil creates a tension between pedagogy and freedom | work_de_principiis_origen_230s_v2w3x4y5 |

### Rang 19 — Lisa R. Holliday, « Will Satan Be Saved? »

Lecture : article intégral, pp. 1-23. Saut : aucun saut. R2 : promotion du shell ; 2008 = online first, 2009 = volume imprimé 63. Corridor : Origène : De principiis.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 6-7 | scholarly_argument_holliday_two_desires | Holliday: Origen distinguishes generic capacity from directed desire | work_de_principiis_origen_230s_v2w3x4y5 |
| 7-14 | scholarly_argument_holliday_power_and_exercise | Holliday: power of choice and moral exercise are distinct | work_de_principiis_origen_230s_v2w3x4y5 |
| 14-16 | scholarly_argument_holliday_previous_causes | Holliday: previous causes result from choice rather than determine it | work_de_principiis_origen_230s_v2w3x4y5 |
| 17-20 | scholarly_argument_holliday_devil_habit | Holliday: the devil retains power while habit removes effective desire for good | work_de_principiis_origen_230s_v2w3x4y5 |
| 19-22 | scholarly_argument_holliday_habit_responsibility | Holliday: moral habit influences without externally determining | work_de_principiis_origen_230s_v2w3x4y5 |
| 22-23 | scholarly_argument_holliday_restoration_contradiction | Holliday: the devil's salvation remains contradictory if restoration is universal — verdict suspended | work_de_principiis_origen_230s_v2w3x4y5 |

### Rang 20 — Carl Fries, « Zur Willensfreiheit bei Origenes »

Lecture : article intégral, pp. 92-101. Saut : non extraits : physiologie, analogies de sexologie et théorie personnelle du Urwille, historiographiquement datées et non probantes pour Origène. R2 : nouvelle publication. Corridor : Origène : De principiis.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 92-95 | scholarly_argument_fries_biblical_indeterminism | Fries: Origen argues for indeterminism through biblical exegesis | work_de_principiis_origen_230s_v2w3x4y5 |
| 95-97 | scholarly_argument_fries_pharaoh_analogies | Fries: the Pharaoh analogies refute a fixed evil nature | work_de_principiis_origen_230s_v2w3x4y5 |
| 97-100 | scholarly_argument_fries_receptive_healing | Fries: willing reception mediates divine healing | work_de_principiis_origen_230s_v2w3x4y5 |

### Rang 21 — Hermut Löhr, « Paulus und der Wille zur Tat »

Lecture : article intégral, pp. 165-188. Saut : aucun saut. R2 : nouvelle publication. Corridor : Paul : Romains 7.18-25.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 165-173 | scholarly_argument_loehr_action_will | Löhr: Paul's language shows an emerging concept of action-directed willing | passage_nt_rom_7_18 |
| 176-179 | scholarly_argument_loehr_good_deed | Löhr: Paul describes a will to perform the good deed | passage_nt_rom_7_19 |
| 177-180 | scholarly_argument_loehr_choice_and_aporia | Löhr: Galatians presents choice while Romans stages an aporia | passage_nt_rom_7_23 |
| 180-181, 186-188 | scholarly_argument_loehr_not_autonomous_faculty | Löhr: Paul implies liberated willing without an autonomous faculty | passage_nt_rom_7_25 |
| 181-184 | scholarly_argument_loehr_captured_law | Löhr: the ethical norm remains good even when sin captures it | passage_nt_rom_7_22 |
| 184-188 | scholarly_argument_loehr_relative_freedom | Löhr: Pauline exhortation presupposes relative freedom rather than mechanical causation | passage_nt_rom_7_19 |

### Rang 22 — A. van den Beld, « Romans 7:14-25 and the Problem of Akrasia »

Lecture : article intégral, pp. 495-515. Saut : aucun saut ; le rapport attribuait A. et T., mais la page de titre et l'en-tête imprimés donnent Dr A. van den Beld seul. R2 : nouvelle publication. Corridor : Paul : Romains 7.15-22.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 495-500 | scholarly_argument_vandenbeld_intentional_actor | Beld: the Romans 7 self remains an intentional actor | passage_nt_rom_7_15 |
| 500-506 | scholarly_argument_vandenbeld_akrasia_paradox | Beld: akrasia is voluntary action contrary to preference | passage_nt_rom_7_19 |
| 508-512 | scholarly_argument_vandenbeld_normative_systems | Beld: Romans 7 concerns conflict between normative systems | passage_nt_rom_7_22 |
| 511-514 | scholarly_argument_vandenbeld_second_order_preference | Beld: a second-order preference need not become effective will | passage_nt_rom_7_19 |
| 514-515 | scholarly_argument_vandenbeld_voluntary_not_free | Beld: the divided self acts voluntarily without freely willing | passage_nt_rom_7_20 |

### Rang 23 — Horace Jeffery Hodges, « Gnostic Liberation from Astrological Determinism »

Lecture : article intégral, pp. 359-373. Saut : aucun saut ; aucun lien primaire forcé, faute de shell existant pour Pistis Sophia ou Trimorphic Protennoia. R2 : nouvelle publication. Corridor : aucun corridor primaire exact disponible.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 359-362 | scholarly_argument_hodges_irregularity | Hodges: cosmic irregularity could signal liberation from astral rule | — |
| 362-364 | scholarly_argument_hodges_redeemer | Hodges: the redeemer descends through hostile spheres and breaks fate | — |
| 364-369 | scholarly_argument_hodges_zodiac_rotation | Hodges: Gnostic texts imagine zodiac rotation as scrambling fate | — |
| 370-373 | scholarly_argument_hodges_catastrophist_precession | Hodges: Gnostic liberation reinterprets precession catastrophically | — |

### Rang 24 — Marguerite Harl, « Problèmes posés par l'histoire du mot to autexousion »

Lecture : compte rendu survivant intégral, p. XXVIII. Saut : le PDF ne contient pas la communication complète ; aucune extrapolation au-delà de la page conservée. R2 : nouvelle publication ; personne existante scholar_harl_m réemployée. Corridor : aucun locus primaire précis affirmé.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| XXVIII | scholarly_argument_harl_unknown_origin | Harl: the technical term appears around 150, but its origin remains unknown | — |
| XXVIII | scholarly_argument_harl_stoic_release | Harl: early Stoic use means release from constraint more than alternative choice | — |
| XXVIII | scholarly_argument_harl_christian_choice | Harl: Christian apologists turn the term into responsible choice | — |

### Rang 25 — Ky Heinze, Origen on Demonic Executioners and the Problem of Evil

Lecture : chap. 1, sections utiles pp. 11-21 ; chap. 3 intégral pp. 40-67. Saut : chap. 2, pp. 21-39 : histoire des traditions juives, chrétiennes et grecques antérieures, sans nouveau nœud argumentatif propre à Origène. R2 : promotion du shell Origenality. Corridor : Origène : De principiis, Contra Celsum, Homélies sur Jérémie, Commentaire sur Romains.

| Pages | Nœud | Argument (English) | Ancrage primaire existant |
|---|---|---|---|
| 13-14 | scholarly_argument_heinze_determinism | Heinze: determinism would make God the author of sin | work_de_principiis_origen_230s_v2w3x4y5 |
| 17-21 | scholarly_argument_heinze_used_not_caused | Heinze: providence uses evil choices without causing them | work_de_principiis_origen_230s_v2w3x4y5 |
| 40-41 | scholarly_argument_heinze_two_functions | Heinze: demonic agents distance God from evil and affirm supremacy | work_origen_contra_celsum_sc132 |
| 40-44 | scholarly_argument_heinze_integrated_roles | Heinze: freely acquired evil roles are integrated without divine approval | work_de_principiis_origen_230s_v2w3x4y5 |
| 44-47 | scholarly_argument_heinze_therapeutic_wrath | Heinze: punishment is therapeutic consequence, not passionate retaliation | work_origen_homilies_jeremiah |
| 47-50 | scholarly_argument_heinze_executioners | Heinze: demonic executioners retain evil intent while serving judgment | work_origen_commentary_romans |
| 65-67 | scholarly_argument_heinze_no_dualism | Heinze: the use of evil balances divine goodness and supremacy without dualism | work_origen_contra_celsum_sc132 |

## 5. Décisions dialectiques

Aucune arête opposes, critiques, responds_to, refutes, contrasts_with, agrees_with ou supports n'est ajoutée. Les critiques de Whitmarsh sur le récit de martyre, l'aporie signalée par Holliday et la reconstruction spéculative de Holz sont enregistrées dans leurs propres nœuds avec pages et, lorsque nécessaire, verdict suspended. Elles ne sont pas transformées en désaccords avec des nœuds modernes préexistants sans attestation directe visant exactement ces thèses.

Le compte post-application de opposes resterait donc 24 : current=24, novel=0, post-apply=24, g6-pin=24. L'appliqueur conserve le contrôle de refus G6 du patron de la vague A : si une révision future ajoutait des opposes et que le pin ne correspondait pas au compte post-application, --apply s'arrêterait avant toute écriture.

## 6. Vérifications

### Structure du delta

    nodes: 110
    persons: 14
    publications: 12
    arguments: 84
    edges: 271
    enrichments: 3
    relations: advanced_in=84, cites_primary_source=77, created_by=99, discusses=11
    duplicate node ids: 0
    duplicate edge ids: 0
    duplicate edge triples: 0
    unresolved edge endpoints: 0
    primary target types: work=65, passage=12
    Greek-script runs in new argument descriptions: 0
    dialectical edges: 0
    suspended verdicts: 4
    promotion targets: Holz 1970, Holliday 2008/2009, Heinze 2026

### Compilation

Commande :

    python3 -m py_compile scripts/ingest_2026_08_17_reading_wave_c.py

Sortie : aucune ; code de retour 0.

### Gate R1-R18 et dry-run

Commande :

    python3 scripts/ingest_2026_08_17_reading_wave_c.py

Sortie :

    delta: 110 nodes / 271 edges / 3 enrichments
    novel: 110 nodes / 271 edges (skipped existing: 0 nodes, 0 edges)
    promotions: ready=3, already-applied=0, failed=0
    opposes: current=24, novel=0, post-apply=24, g6-pin=24
    --- check_ingestion_rules.py --new-only (temporary mirror) ---
    temporary parser normalisations: 1 (shared dependency only; repository unchanged)
    ingestion-rules: delta of 110 nodes / 271 edges
      no violations

    BLOCK: 0   WARN: 0
    dry-run: nothing written (use --apply)

Comme dans la vague A, la seule normalisation temporaire corrige dans une copie isolée la graphie Python 2 préexistante du module partagé. Aucun fichier vivant du dépôt n'est modifié par ce mécanisme.

### Non-écriture des données

La commande --apply n'a pas été exécutée, conformément à l'interdiction d'écrire dans data/kg. Aucun fichier .bak-reading_c n'existe. Empreintes observées après le dry-run :

    bc488d8cdfdcbe1c3ac6c6407920c45289720672d1fa642028f92a853741d0d2  data/kg/nodes.jsonl
    a8d41261413bf3cb9a6af01f0c814c39652d94e406d6150c1a4ab954dfe1a16f  data/kg/edges.jsonl
