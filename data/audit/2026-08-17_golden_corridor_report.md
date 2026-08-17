# Audit du « golden corridor » — 17 août 2026

## Résultat exécutif

Audit en lecture seule de `data/kg/nodes.jsonl` (19 994 nœuds) et
`data/kg/edges.jsonl` (49 391 arêtes). Aucun fichier de `data/kg` ou de
`data/corpus` n'a été modifié.

Le corridor est **traversable de Justin à Origène** dans le graphe actuel :
`person_justin_martyr_2c_ce -> influences ->
person_origen_alexandria_185_254ce_s9t0u1v2`, avec en outre le sous-chemin
argumentatif `argument_justin_prophecy_freedom -> precedes ->
argument_origen_prescience_causality`. Il n'est toutefois pas encore une chaîne
linéaire qui visite chaque apologiste : Tatien et Théophile convergent vers
Irénée, tandis que Clément constitue une branche alexandrine distincte vers
Origène. Aucune dépendance Tatien/Irénée → Clément n'a été forcée.

Le delta proposé contient **45 arêtes manquantes et aucune création de nœud** :

- 5 ancrages argument → passage authentique ;
- 37 raccords de réception moderne réellement attestés ;
- 3 raccords de continuité ou de développement historique.

Le gate `--new-only` donne `BLOCK: 0 / WARN: 0`. Le dry-run trouve 45 arêtes
nouvelles, zéro extrémité non résolue et n'écrit rien.

Les lacunes critiques ne sont donc pas principalement des lacunes de câblage :
elles portent sur l'**ingestion du texte** (Irénée IV.38-39, loci étendus de
Clément, Philocalie 22-27, Commentaire sur Romains) et sur une **nouvelle vague
de lecture** (arguments de Tatien 7 et 10, Irénée 38-39, plusieurs loci
origéniens hors du traité III.1).

## Méthode et critères

- Un passage est `OK` au niveau texte seulement s'il contient effectivement un
  texte ancien grec ou latin, et non une traduction moderne, un résumé, un
  extrait vide ou un nœud `needs_text_ingestion`.
- Les nœuds de traduction et les coquilles conservées avec
  `passage_role=original` par contrainte de schéma ne sont pas comptés comme
  texte ancien.
- Un argument est considéré câblé si un lien `cites_primary_source`,
  `evidenced_by` ou `grounded_in` l'attache au locus pertinent.
- La réception est jugée sur les descriptions, `page_range`,
  `verified_reference` et `supporting_evidence` des nœuds savants. Une simple
  proximité thématique ne suffit pas.
- Le tableau final tient compte du delta proposé, mais celui-ci reste **non
  appliqué**.

## Contrôle TLG E

Commandes exécutées avec `scripts/tlg_search.py`, corpus TLG E local. Les
recherches sont insensibles aux accents et aux esprits.

| Station | Échantillon vérifié | Auteur TLG | Résultat |
|---|---|---:|---|
| Justin, 1 Apol. 43 | `καθ' εἱμαρμένην πάντα γίνεται ... τὸ ἐφ' ἡμῖν` | 0645 | 1 hit |
| Justin, 2 Apol. 6/7 | contrôle adjacent `κακίας καὶ ἀρετῆς δεκτικὸν εἶναι` | 0645 | 1 hit |
| Tatien, Or. 7 | `τὸ δὲ ἑκάτερον ... αὐτεξούσιον γέγονε` | 1766 | 1 hit |
| Tatien, Or. 9 | `ἡμεῖς δὲ καὶ εἱμαρμένης ἐσμὲν ἀνώτεροι` | 1766 | 1 hit |
| Théophile, Autol. II.27 | `ἐλεύθερον ... καὶ αὐτεξούσιον ... τὸν ἄνθρωπον` | 1725 | 1 hit |
| Irénée, Haer. IV.37 | `τὸ αὐτεξούσιον ἐπιδείκνυσι τοῦ ἀνθρώπου` | 1447 | 1 hit |
| Clément, Strom. I.17.83 | `οὔτε ... οἱ ἔπαινοι ... οὔτε οἱ ψόγοι` | 0555 | 1 hit |
| Origène, Princ. III.1 | titre `Περὶ αὐτεξουσίου ...` | 2042 | 2 hits |
| Origène, Or. 6.3 | `οὐχὶ τῆς προγνώσεως ... αἰτίας γινομένης` | 2042 | 1 hit |
| Origène, Cels. II.20 | `οὐχὶ τὸν θεσπίσαντα αἴτιον ...` | 2042 | ≥ 3 hits |
| Alexandre, Fat. 14 | `οὐκ ὄνομα μόνον τοῦ ἐφ' ἡμῖν` | 0732 | 1 hit |
| Ps.-Plutarque, Fat. 6 | `τὸ ἐξ ὑποθέσεως ἅμα καὶ καθόλου` | 0007 | 1 hit |
| définition chrysippéenne du destin | `φυσικήν τινα σύνταξιν τῶν ὅλων` | 1264 | 1 hit |

Deux requêtes longues ont d'abord rendu zéro hit : la formule complète de
Justin sur les anges et les hommes αὐτεξούσιοι et une formulation paraphrasée
de la distinction pseudo-plutarquéenne. Dans les deux cas, un second segment
distinctif du **même passage** a rendu un hit unique. Ce sont des variantes
d'ordre/encodage ou une paraphrase de requête, non une invalidation du passage.
La formule alexandrinienne a pareillement été retrouvée par un segment plus
court.

Deux limites sont réelles et signalées : Carnéade n'a pas de texte propre et
doit être vérifié dans les témoins (surtout Cicéron, latin) ; le grec du
Commentaire sur Romains est perdu et ne peut donc pas être contrôlé par TLG.

## 1. Arrière-plan stoïcien : destin, assentiment et τὸ ἐφ' ἡμῖν

### Texte

**OK, avec médiation doxographique.** La chaîne textuelle authentique repose
notamment sur :

- `passage_cic_fat_39` à `passage_cic_fat_43` (latin, rôle `original`) ;
- `work_gellius_na_vii_2` et ses témoins latins ;
- `concept_heimarmene_fate_stoics_j0k1l2m3`, dont la définition grecque
  chrysippéenne transmise par Gellius a été retrouvée dans TLG 1264 ;
- `concept_synkatathesis_stoic_assent` et
  `concept_eph_hemin_one_sided_causative` comme nœuds conceptuels.

Réserve philologique importante : le nœud
`concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` note lui-même, suivant
Fürst/Bobzien, que la forme substantivée `τὸ ἐφ' ἡμῖν` n'est pas directement
attestée pour le Vieux Portique. Le contenu stoïcien est donc accessible par
les témoins latins et les reconstructions savantes, pas par un traité grec de
Chrysippe conservé.

### Argument

**OK.** `argument_cylinder_analogy_chrysippus_k1l2m3n4` est relié à Cicéron,
Fat. 42-43 et à Gellius ; `argument_the_lazy_argument_argos_logos_702a77ed`,
`argument_the_cofated_events_argument_confatalia_b7715646` et les concepts
d'assentiment et de cause interne couvrent le noyau compatibiliste.

### Réception

**OK.** Sont présents et câblés :

- Bobzien : `argument_bobzien_2001_b1_eph_hemin_one_vs_two_sided`,
  `argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction`,
  `argument_bobzien_2001_b1_synkatathesis_psychology_action` ;
- Frede : `argument_frede_2011_stoic_assent_is_proto_will` ;
- Dihle : `argument_dihle_1982_synkatathesis_is_cognitive_not_volitional` ;
- Fürst : `argument_furst_2022_stoic_eph_hemin_late_substantive` ;
- Koch : `scholarly_argument_koch_stoic_causal_theory_and_human__0` et les
  positions sur Cicéron Fat. 39-45.

Kahn et Irwin sont présents dans le graphe pour l'histoire générale de la
volonté, mais leurs nœuds ne documentent pas ce locus stoïcien avec une
précision suffisante pour recevoir de nouvelles arêtes.

### Continuité

**OK.** Le fond stoïcien rejoint Clément et Origène par les liens existants vers
`concept_synkatathesis_stoic_assent`, `person_chrysippus_280_206bce_i9j0k1l2`
et `school_stoics`. Aucun nouveau lien n'est requis.

## 2. Destin conditionnel médio-platonicien

### Texte

**OK.** `passage_plut_fat_4`, `passage_plut_fat_5`, `passage_plut_fat_6` et
`passage_plut_fat_15` contiennent le grec ancien de Ps.-Plutarque, De fato, avec
`work_plutarch_de_fato_complete`. Le contrôle TLG de Fat. 6 est positif.
`work_didaskalikos_alcinous_2nd_ce_q7r8s9t0` apporte le parallèle d'Alcinoos.

### Argument

**OK.** `argument_hypothetical_fate_plut` est câblé aux passages 4-6 et 15 ;
`concept_hypothetical_fate_middle_platonist`,
`concept_heimarmene_conditional_amand1945` et
`argument_chance_cosmos_middle_platonist` modélisent les interprétations
concurrentes.

### Réception

**OK après delta.** Déjà câblés : Bonazzi, Fürst, Boys-Stones 2018 et Amand.
Trois positions riches existaient sans raccord au nœud doctrinal précis :

- Koch, `scholarly_argument_koch_middle_platonic_conditional_fa_5` → delta
  `corridor-wiring-042` ;
- Bobzien, `scholarly_argument_bobzien_middle_platonists_on_contingen_7` →
  delta `corridor-wiring-043` ;
- Boys-Stones, `scholarly_argument_boys_stones_hypothetical_fate_ex_hypothese_3`
  → delta `corridor-wiring-044`.

### Continuité

**OK.** `person_justin_martyr_2c_ce employs
concept_hypothetical_fate_middle_platonist`, et Origène `extends` le nœud
général médio-platonicien. Le graphe conserve aussi le désaccord historiographique
sur la lecture exacte du destin hypothétique.

## 3. Carnéade

### Texte

**OK comme dossier de témoins, non comme œuvre propre.** Carnéade n'ayant rien
écrit, le texte ancien authentique est celui de ses témoins :

- Cicéron, De fato 23-25 : `passage_cic_fat_23`, `24`, `25` ;
- Cicéron, De fato 31-33 : `passage_cic_fat_31`, `32`, `33` ;
- la tradition grecque tardive regroupée notamment dans les passages
  d'Eusèbe, PE VI.6.

TLG ne peut pas vérifier les phrases latines de Cicéron. Elles ont été lues
directement dans les nœuds latins ; il serait fautif de parler ici d'un
« original grec de Carnéade ».

### Argument

**OK après delta.** `argument_carneades_autonomous_mental_causation_argument_4e7e9250`
est câblé à Cicéron 23-25. `argument_cafma_carneades_m3n4o5p6` possède un riche
dossier cicéronien et eusébien, mais son propre `verified_reference` citait
Fat. 31 sans arête sortante correspondante : ajout
`corridor-wiring-002`.

Les nombreuses reconstructions Amand (`argument_carneadean_*_amand1945`) sont
correctement présentées comme reconstructions à partir de témoins, non comme
contenu écrit directement par Carnéade.

### Réception

**OK.** Amand, Bobzien, Frede et Fürst sont présents et reliés :

- `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0` ;
- `argument_bobzien_2001_b1_rise_fall_freedom_problem` ;
- `argument_frede_2011_alexander_libertarian_dead_end` ;
- `argument_furst_2022_carneades_voluntary_self_motion`.

La divergence « doctrine positive » versus « stratégie dialectique » reste
visible dans `person_carneades_214_129bce_l2m3n4o5` et n'a pas été aplatie.

### Continuité

**OK.** `argument_cafma_carneades_m3n4o5p6 influences
argument_justin_antifatalism`; Carnéade influence aussi Alexandre et Origène au
niveau des personnes, avec une médiation clairement doxographique.

## 4. Alexandre d'Aphrodise, De fato

### Texte

**OK.** Les 39 chapitres grecs sont présents dans `passage_alex_fat_1` à
`passage_alex_fat_39`, sous `work_de_fato_alexander_c200ce_o6p7q8r9`. Les
traductions `_en` ne sont pas utilisées comme preuve primaire. Le contrôle TLG
du chapitre 14 est positif.

Attention bibliographique : le nœud de l'œuvre possède encore un ancien
`cts_urn` divergent (`tlg2018.tlg005`) tandis que les passages portent le bon
identifiant `tlg0732.tlg014`. Cette dette de métadonnées ne remet pas en cause
le texte des passages.

### Argument

**OK.** La couverture est exceptionnellement riche :
`argument_incompatibilism_alexander_p7q8r9s0`,
`argument_agent_causation_alex`, `argument_deliberation_alex`,
`argument_power_contraries_alex`, les cinq arguments Amand sur Fat. 16-20 et
de nombreux sous-arguments sont reliés à leurs chapitres grecs.

### Réception

**OK.** Koch fournit un câblage chapitre par chapitre ; Bobzien, Frede,
Sharples, Ramelli et Zingano ont des positions distinctes et reliées. Exemples :

- `scholarly_argument_koch_alexander_s_conception_of_what_2` ;
- `scholarly_argument_bobzien_alexander_of_aphrodisias_as_fi_3` ;
- `argument_frede_2011_alexander_libertarian_dead_end` ;
- `scholarly_position_sharples_alexander_libertarian_unsupported` ;
- `scholarly_argument_ramelli_alexander_of_aphrodisias_as_so_0`.

### Continuité

**OK après delta.** Le graphe possède déjà `person_alexander... influences
person_origen...`; l'inverse n'a pas été matérialisé, conformément à R17. Le
lien conceptuel plus précis entre les deux arguments est ajouté par
`corridor-wiring-045`, attesté par le nœud Ramelli.

## 5. Justin Martyr — 1 Apol. 43-44 ; 2 Apol. 6/7

### Texte

**OK.** Sont présents en grec :

- `passage_just_apol1_43` ;
- `passage_just_apol1_44` ;
- `passage_just_apol2_6` et `passage_just_apol2_7`.

La formule sur les anges et les hommes αὐτεξούσιοι se trouve dans
`passage_just_apol2_6` selon la numérotation Minns-Parvis/Perseus, équivalant au
traditionnel 2 Apol. 7. Le chapitre 7 du jeu de données ne contient donc pas
cette phrase : ce n'est pas une lacune textuelle, mais une divergence de
numérotation dûment documentée dans `work_justin_second_apology_sc507`.

### Argument

**OK.** Le KG modélise séparément :

- l'antifatalisme : `argument_justin_antifatalism` et
  `argument_justin_1apol_43_three_carneadean_topoi` ;
- prophétie et liberté : `argument_justin_prophecy_freedom` ;
- chute des anges et universalité de l'autexousion :
  `argument_justin_angel_fall` ;
- la synthèse apologétique :
  `argument_justin_martyrs_apologetic_argument_for_free_will_45c2dde2`.

Les passages 43, 44 et 2 Apol. 6/7 sont déjà correctement attachés.

### Réception

**OK après delta.** Fürst et Frede étaient déjà reliés au travail/personne. Le
delta complète les positions précises d'Andresen, Bobzien, Boys-Stones, Hall,
Minns, Telfer et Pouderon (`corridor-wiring-006` à `021`). Chaque ajout repose
sur un locus ou une page explicite ; aucun lien n'est tiré des seuls titres.

### Continuité

**OK.** Justin influence Tatien, Irénée et Origène au niveau des personnes ;
son argument antifataliste influence celui de Tatien ; 1 Apol. 44 précède
l'argument origénien sur prescience et causalité.

## 6. Tatien — Oratio 7-11

### Texte

**OK.** Les sections 7-11 sont présentes en grec dans les nœuds
`passage_tatian_7_1`–`7_2`, `8_1`–`8_5`, `9_1`–`9_2`, `10_1`–`10_3` et
`11_1`–`11_2`. Les nœuds composites `passage_tatian_orat_7`,
`passage_tatian_orat_8_9` et `passage_tatian_orat_11` doublent certains loci.
Les contrôles TLG des chapitres 7 et 9 sont positifs.

### Argument

**GAP.** Deux arguments sont bien modélisés et câblés :

- `argument_tatian_above_fate` pour Or. 8-9 ;
- `argument_tatian_freewill_paradox` pour Or. 11.

En revanche, aucun nœud d'argument autonome ne modélise la structure de Or. 7
(êtres angéliques et humains créés αὐτεξούσιοι, perfection du bien par la
liberté de la prohairesis), et Or. 10 n'a pas fait l'objet d'une lecture
argumentative propre. Conformément à la mission, aucun nouvel argument ancien
n'est créé : il faut une vague de lecture de Or. 7 et 10, avec segmentation des
prémisses et contrôle Whittaker/Marcovich.

### Réception

**OK.** Secord est câblé jusque dans `passage_tatian_orat_8_9`; Frede, Bobzien,
Pouderon et la synthèse Fürst sont reliés à Tatien ou au concept précis.
`scholarly_argument_secord_tatian_reworks_astrological_idiom_from_within` ne
reçoit pas une seconde arête au passage 8-9 : le nœud décrit l'idiome général
des chapitres 8-9, déjà porté par sa position sœur, et aucun besoin de doublon
n'est démontré.

### Continuité

**GAP pour la chaîne linéaire, OK comme branche.** Justin influence Tatien ;
Tatien précède Irénée. Il n'existe pas de lien historique suffisamment précis
de Tatien vers Clément. Aucun lien n'a été forcé entre contemporains.

## 7. Théophile d'Antioche — Ad Autolycum II.27

### Texte

**OK.** `passage_theophilus_autol_2_27` contient le locus grec vérifié TLG ;
`sc20_theophilus_ad_autolycum_ii_liv_2_superiorite_des_auteurs_sacres_sur_les_profanes_chap_27`
fournit le chapitre SC complet. La présence du premier nœud comme extrait
critique externe n'est pas un shell de traduction.

### Argument

**OK.** `argument_theophilus_capable_of_both` est relié au passage et aux
concepts `concept_autexousion_christian_freedom_u1v2w3x4` et
`concept_dektikon_amphoteron`.

### Réception

**OK après delta.** Les deux positions réellement explicites sont :

- Pouderon, `scholarly_argument_pouderon_free_will_libre_arbitre_in_gre_0` →
  `corridor-wiring-022` ;
- Fürst, `argument_furst_2022_christian_philosophers_freedom_innovation` →
  `corridor-wiring-023`.

Les nœuds généraux de Karamanolis ne nomment pas ce locus dans leur description
ou leur `page_range`; ils ne sont pas raccordés artificiellement.

### Continuité

**OK.** `person_theophilus_antioch_c183 influences person_irenaeus_d202`. Le
nœud argumentatif reste distinct : l'influence historique n'autorise pas à
identifier les deux arguments.

## 8. Irénée — Haer. IV.37-39

### Texte

**GAP.** `passage_irenaeus_ah_4_37` contient un fragment grec authentique de
IV.37.1, confirmé dans TLG 1447. Le nœud documente correctement que le latin
complet doit encore être contrôlé dans SC 100. Il n'existe pas de passages
authentiques pour IV.38 et IV.39. Le `work_irenaeus_adversus_haereses_book4`
ne remplace pas ces passages.

Besoin d'ingestion : latin de IV.37-39 d'après SC 100 (ou édition critique
équivalente), plus fragments grecs survivants avec leurs limites exactes ; ne
pas reconstruire du grec à partir du latin.

### Argument

**GAP malgré un bon noyau.** Sont présents :

- `argument_irenaeus_adv_haer_iv_37_praise_blame_transposed`, déjà relié au
  passage ;
- `argument_irenaeuss_antignostic_argument_for_free_will_f54fe920`, qui ne
  citait que l'œuvre : `corridor-wiring-001` ajoute IV.37.1.

Les chapitres 38-39 (croissance, état de νήπιος, bon versus parfait, pédagogie)
ne disposent pas d'un découpage argumentatif contrôlé contre le texte. Une
vague de lecture est requise après ingestion.

### Réception

**OK après delta.** Amand est déjà relié par
`synthesis_amand1945_irenaeus_transposed_topos`; Grant, Rousseau, Hick et
d'autres sont reliés à Irénée. Le delta ajoute :

- Fürst vers l'argument anti-gnostique (`corridor-wiring-024`) ;
- Löhr vers l'argument IV.37.1-2 (`corridor-wiring-025`) ;
- Sagnard vers l'œuvre IV.37-39 (`corridor-wiring-026`).

Le nœud Rousseau fondé sur l'édition du livre I n'est pas relié au passage
IV.37 : sa propre note de vérification avertit que cela surinterpréterait cette
édition.

### Continuité

**OK après delta.** Justin et Théophile influencent déjà Irénée. Fürst affirme
explicitement qu'Origène hérite de la frontière anti-gnostique irénéenne ;
`corridor-wiring-027` ajoute donc `Origen influenced_by Irenaeus` au niveau des
personnes. Aucun lien Irénée → Clément n'est ajouté : la connexion serait
chronologique/thématique, non une influence démontrée.

## 9. Clément d'Alexandrie — Stromates

### Texte

**GAP critique.** Six passages grecs seulement ont été ingérés :

- `passage_clement_strom_1_17_82`, `83`, `84` ;
- `passage_clement_strom_2_11_50`, `51`, `52`.

Le premier groupe contient bien l'argument sur louange/blâme et l'exousia de
l'âme. Le second groupe est une section sur mesure/nombre et gnosticisme ; il
**n'est pas** le locus II.11.1-2 sur foi naturelle, choix et responsabilité.
Les arêtes actuelles qui utilisent II.11.50-52 comme preuve de
`argument_clement_alex_carneadean_glissement_faith_unbelief` et de
`argument_clement_grace_synergy_assent` sont donc sémantiquement erronées.
Elles ne sont pas supprimées ici, puisque le livrable est un delta de liens
manquants seulement.

À ingérer au minimum : Strom. II.11.1-2 (GCS II 118,21-119,3), II.2.8.3-4,
V.13.86, II.6-15 et IV.23-24, avec le grec Stählin/SC et une segmentation
canonique non ambiguë.

### Argument

**GAP.** Les trois nœuds anciens sont substantiels :
`argument_clement_alex_strom_1_83_5_praise_blame`,
`argument_clement_alex_carneadean_glissement_faith_unbelief` et
`argument_clement_grace_synergy_assent`. Seul le premier est proprement
ancré dans le texte actuellement ingéré. Les deux autres doivent être
ré-ancrés après ingestion des vrais loci ; aucune nouvelle prose ancienne
n'est autorisée.

### Réception

**OK après delta.** Fürst, Frede et Amand étaient déjà présents. Les positions
d'Havrda, Jourdan, Löhr et Telfer étaient riches mais largement orphelines des
nœuds anciens clémentins. `corridor-wiring-028` à `037` les rattache, soit à la
personne, soit à l'argument précis qu'elles interprètent.

### Continuité

**GAP en amont, OK vers Origène.** `person_clement_alexandria influences
person_origen...` existe. Löhr p. 385 atteste plus précisément qu'Origène
reprend et étend la charge clémentine de déterminisme :
`corridor-wiring-038`. Il n'existe pas de pont documenté entre la branche
Irénée/Tatien et Clément ; aucun n'est ajouté.

## 10. Origène — station terminale

### Texte

**GAP global, malgré trois ensembles solides.** État par sous-corpus :

1. **De principiis III.1 — OK.**
   `sc268_origenes_peri_archon_iii_chap1` contient le grec complet de la
   section (41 689 caractères). Les nœuds `passage_origen_pa_3_1_1` à `_24`
   sont presque tous des traductions françaises ; ils ne doivent pas être
   comptés comme texte ancien. `passage_origen_pa_3_1_3` est grec mais porte un
   `work_title` erroné (`Contra Celsum`).

2. **Philocalie 21-27 — GAP.**
   Le chapitre 21 possède 24 extraits grecs (`passage_origen_philocalia_21_*`),
   dont la plupart sont enveloppés dans une notice éditoriale mais contiennent
   bien le grec ancien. Les nœuds du chapitre 22 sont des shells vides
   `needs_text_ingestion`; le chapitre 23 et les chapitres 25-27 ne contiennent
   que la traduction française SC 226, parfois encore marquée
   `passage_role=original`; le chapitre 24 n'est pas matérialisé. L'ensemble
   22-27 exige donc une ingestion grecque contrôlée.

3. **Contra Celsum — OK.**
   Le corpus SC contient le grec complet. Loci vérifiés :
   `sc132_origenes_contra_celsum_ii_par20`,
   `sc136_origenes_contra_celsum_iv_par3_b`,
   `sc136_origenes_contra_celsum_iv_par45`,
   `sc147_origenes_contra_celsum_v_par21`. Les `canonical_ref` SC portent
   parfois un préfixe de livre fautif (`1.x`) alors que les identifiants/labels
   de livre sont corrects : dette de métadonnées, pas absence du grec.

4. **De oratione 6 — OK.**
   `passage_origen_de_orat_6` contient le grec exact de 6.3, recopié et vérifié
   contre TLG 2042.008 après suppression documentée d'une ancienne recomposition
   non attestée.

5. **Commentaire sur Romains 7 et 9 — GAP critique.**
   `passage_origen_com_rm_7_16` et `_sun` contiennent des notices modernes et
   quelques citations latines, sont `needs_text_ingestion=true` et portent le
   `work_title` fautif `Contra Celsum`. Aucun passage authentique complet de
   Romains 7 n'est présent. Il faut ingérer le latin de Rufin dans l'édition
   Hammond Bammel/SC, avec passages distincts pour les traitements de Rom 7 et
   Rom 9 ; le grec perdu ne doit pas être reconstruit.

### Argument

**GAP global, couverture très forte de III.1.**

- De principiis III.1 :
  `argument_origens_de_principiis_argument_for_free_will_93d043fc`,
  `argument_origen_free_will_theodicy_6f9d8a3c` et les arguments Amand couvrent
  le traité. `corridor-wiring-004`, `005` et `041` renforcent l'ancrage au nœud
  grec complet.
- Contra Celsum II.20 : `argument_origen_argos_logos` est bien câblé.
- Contra Celsum IV.3 :
  `argument_origen_witness_virtue_voluntary_essence_amand1945` n'avait qu'un
  lien à l'œuvre ; `corridor-wiring-003` l'attache au bon sous-passage `_3_b`.
- De oratione 6 : `argument_origen_prescience_causality` est correctement
  `grounded_in` le passage grec.
- Commentaire sur Romains 9 : `argument_origen_diatribe_inversion` est câblé à
  un shell textuel, donc l'argument ne sera pleinement fondé qu'après ingestion.
- Commentaire sur Romains 7 et les loci CC IV.45/V.21 : pas de nœud d'argument
  ancien suffisamment précis ; vague de lecture nécessaire.

Plusieurs arguments sur Philocalie 23 sont actuellement `evidenced_by` des
traductions françaises marquées comme originales. Ces arêtes décrivent le bon
locus, mais ne satisfont pas le niveau TEXT tant que le grec n'est pas ingéré.

### Réception

**OK après delta.** Couverture particulièrement riche :

- Fürst : traité III.1, métaphysique de la liberté, Philocalie ;
- Gibbons : assentiment, caractère, révisabilité, providence, avec plusieurs
  arêtes paginées vers III.1, Or. 6, CC II.20 et Philocalie ;
- Frede : adaptation de la psychologie stoïcienne ;
- Bobzien : réponse à l'argos logos ;
- Telfer : systématisation de l'autexousia ;
- Amand : dossier complet de transposition carnéadienne ;
- Markschies : Romains 7, providence, apocatastase ;
- Belcastro : prédestination dans le Commentaire sur Romains ;
- Ramelli : rapport à Alexandre.

Ajouts : `corridor-wiring-039` (Bobzien → argument de l'argos logos), `040`
(Belcastro → Commentaire sur Romains), `041` (Fürst → texte grec complet).

Dihle, Kahn et Irwin sont importants pour la question générale de la volonté,
mais leurs nœuds ne discutent pas ces loci origéniens. Karamanolis offre une
synthèse de l'early Christianity, sans page/locus assez précis dans les nœuds
actuels. Ils ne sont pas reliés de force.

### Continuité

**OK comme terme du corridor.** Origène reçoit déjà Justin, Clément, le
stoïcisme, le Moyen Platonisme, Carnéade et Alexandre par plusieurs chemins.
Le delta ajoute la continuité anti-gnostique avec Irénée (`027`), le
développement de Clément (`038`) et le rapport argumentatif à Alexandre (`045`).

## Tableau final station × niveau

État après prise en compte du delta proposé, toujours non appliqué.

| Station | TEXT | ARGUMENT | RÉCEPTION | CONTINUITÉ |
|---|---|---|---|---|
| Stoïcisme : destin/assentiment/ἐφ' ἡμῖν | OK | OK | OK | OK |
| Moyen Platonisme : destin conditionnel | OK | OK | OK | OK |
| Carnéade | OK | OK | OK | OK |
| Alexandre, De fato | OK | OK | OK | OK |
| Justin, 1 Apol. 43-44 ; 2 Apol. 6/7 | OK | OK | OK | OK |
| Tatien, Or. 7-11 | OK | GAP | OK | GAP |
| Théophile, Autol. II.27 | OK | OK | OK | OK |
| Irénée, Haer. IV.37-39 | GAP | GAP | OK | OK |
| Clément, Stromates | GAP | GAP | OK | GAP |
| Origène, ensemble terminal | GAP | GAP | OK | OK |

## Lacunes prioritaires

### Wire now — inclus dans le delta (45 arêtes)

1. **Ancrages anciens (priorité haute)** : `corridor-wiring-001` à `005` —
   Irénée IV.37.1, Carnéade/Cicéron 31, Origène CC IV.3 et Princ. III.1.
2. **Justin** : `006` à `021` — Fürst, Andresen, Bobzien, Boys-Stones, Hall,
   Minns, Telfer, Pouderon.
3. **Théophile** : `022`-`023` — Pouderon et Fürst.
4. **Irénée et continuité anti-gnostique** : `024`-`027` — Fürst, Löhr,
   Sagnard, Irénée → Origène.
5. **Clément et continuité alexandrine** : `028`-`038` — Havrda, Jourdan,
   Löhr, Telfer, Clément → Origène.
6. **Origène** : `039`-`041` — Bobzien, Belcastro, Fürst.
7. **Moyen Platonisme** : `042`-`044` — Koch, Bobzien, Boys-Stones.
8. **Alexandre → Origène** : `045`, au niveau argumentatif pour ne pas
   matérialiser l'inverse d'une arête `influences` déjà existante (R17).

### Needs reading wave — aucun contenu ancien créé ici

1. Tatien, Or. 7 : reconstruire l'argument de la création αὐτεξούσιος et de la
   perfection par liberté de la prohairesis ; Or. 10 : déterminer s'il porte un
   argument distinct ou une continuation rhétorique.
2. Irénée, Haer. IV.38-39 : distinguer croissance/νήπιος, bon/perfait,
   pédagogie divine et responsabilité sans projeter rétrospectivement la
   « soul-making theodicy » de Hick.
3. Clément : relire II.11.1-2, II.2.8.3-4, V.13.86, II.6-15 et IV.23-24 ;
   séparer doctrine antique de la synthèse moderne « soft synergism ».
4. Origène : modéliser, après lecture, les arguments propres de CC IV.45,
   CC V.21, Commentaire sur Romains 7 et les sections de Romains 9 autres que
   la persona objectionnelle.
5. Carnéade : maintenir l'opposition historiographique entre argument
   dialectique et doctrine positive ; ne pas transformer les reconstructions
   d'Amand en ipsissima verba.

### Needs text ingestion

1. Irénée, Haer. IV.37-39 : latin critique complet + fragments grecs survivants.
2. Clément : vrais loci de Strom. II.11.1-2, II.2.8.3-4, V.13.86, II.6-15,
   IV.23-24.
3. Philocalie 22-27 : grec SC 226/édition critique ; matérialiser 24 ; remplacer
   les shells 22 et les traductions-only 23/25-27 comme preuves primaires.
4. Origène, Commentaire sur Romains : latin de Rufin pour Rom 7 et Rom 9 ; ne
   jamais reconstruire le grec perdu.

### Dette de correction hors périmètre du delta « missing links only »

- retirer/remapper les trois arêtes de
  `argument_clement_alex_carneadean_glissement_faith_unbelief` vers
  `passage_clement_strom_2_11_50`-`52`, et les trois arêtes identiques de
  `argument_clement_grace_synergy_assent` ;
- corriger `work_title=Contra Celsum` sur les nœuds du Commentaire sur Romains ;
- réconcilier l'URN de l'œuvre d'Alexandre avec `tlg0732.tlg014` ;
- corriger les `canonical_ref` de livres dans les passages SC de Contra Celsum ;
- normaliser les rôles des traductions françaises de Philocalie après ingestion
  des originaux.

## Connexions refusées / skips documentés

- **Aucune arête Tatien → Clément** ni Irénée → Clément : contemporanéité et
  ressemblance ne prouvent pas une dépendance.
- **Aucune arête Kahn/Irwin/Dihle → Justin, Tatien, Théophile, Irénée, Clément
  ou Origène** sans locus dans les descriptions/pages des nœuds concernés.
- **Aucune arête Karamanolis vers un passage précis** : le chapitre 4 est trop
  large dans le nœud actuel pour attester un locus.
- **Aucune arête Rousseau livre I → Haer. IV.37** : la note de vérification du
  nœud interdit cette extrapolation.
- **Aucune arête Markschies Romains 7 → `passage_origen_com_rm_7_16`** : ce
  dernier concerne Romains 9 ; les deux dossiers ne doivent pas être confondus.
- **Aucune arête Gibbons “Pauline anthropology” → Commentaire sur Romains** :
  le nœud 2016 ne donne pas ce locus dans son `verified_reference`.
- **Aucun lien de preuve vers une traduction-only ou un shell vide** ajouté.
- **Aucun nœud de texte ou d'argument ancien créé**, même lorsque la lacune est
  évidente.

## Gate et dry-run

Commande gate :

```text
$ python3 scripts/check_ingestion_rules.py --new-only scripts/data_2026_08_17_corridor_wiring.json
ingestion-rules: delta of 0 nodes / 45 edges
  no violations

BLOCK: 0   WARN: 0
```

Commande applier en dry-run :

```text
$ python3 scripts/ingest_2026_08_17_corridor_wiring.py --dry-run
--- check_ingestion_rules.py --new-only (novel subset) ---
ingestion-rules: delta of 0 nodes / 45 edges
  no violations

BLOCK: 0   WARN: 0
--- corridor wiring summary ---
mode: dry-run
delta edges: 45
novel edges: 45
already present: 0
unresolved endpoints: 0
dry-run: nothing written
```

Les empreintes SHA-256 de `data/kg/nodes.jsonl` et `data/kg/edges.jsonl` sont
identiques avant et après le dry-run.
