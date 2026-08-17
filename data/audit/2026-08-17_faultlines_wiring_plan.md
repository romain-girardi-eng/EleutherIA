# Plan de câblage des lignes de fracture historiographiques — 2026-08-17

## Statut et périmètre

Ce lot est un **dry-run non appliqué**. Il ne contient aucun nœud et propose 32 arêtes nouvelles : 15 `critiques`, 8 `agrees_with`, 5 `extends`, 3 `opposes` et 1 `responds_to`. Aucun fichier sous `data/kg` ou `data/corpus` n'a été écrit.

Le contrôle mécanique a porté sur les nœuds `argument` et `synthesis`, leurs descriptions, leurs métadonnées d'engagement et leurs pages, puis sur les sources locales lorsque le texte du nœud ne suffisait pas. Chaque triplet a été comparé au graphe dans les deux directions. Les 32 triplets sont nouveaux, leurs extrémités existent, et aucun ne relie deux positions du même chercheur.

État dialectique du graphe avant application pour les cinq relations du lot : 18 `opposes`, 15 `agrees_with`, 271 `critiques`, 59 `responds_to`, 147 `extends`.

## 1. Naissance de la volonté

**Participants cartographiés :** Dihle, Frede, Kahn, Irwin, MacIntyre, Bobzien, Acosta López de Mesa, Blackson, Mansfeld et Sorabji. Les arêtes Irwin–MacIntyre, Irwin–Dihle, Frede–Dihle et Bobzien–Frede déjà présentes ont été conservées sans duplication.

### Arêtes ajoutées au delta

1. `scholarly_argument_acosta_l_pez_de_mesa_origin_of_free_will_in_ancient_0 critiques argument_frede_2011_notion_is_technical_and_datable` — **Acosta López de Mesa 2012, pp. 32-35 :** rejet de la méthode de recherche terminologique et de l'origine stoïcienne unique chez Frede.
2. `scholarly_argument_acosta_l_pez_de_mesa_origin_of_free_will_in_ancient_0 critiques scholarly_position_dihle_will_christian_innovation` — **Acosta López de Mesa 2012, pp. 32-33 :** rejet du modèle augustinien de Dihle.
3. `scholarly_argument_acosta_l_pez_de_mesa_aristotle_s_notion_of_free_wil_1 critiques argument_frede_2011_aristotle_no_will_no_free_will` — **Acosta López de Mesa 2012, pp. 34-35 :** Frede est déclaré aveugle aux ressources non intellectualistes d'Aristote.
4. `scholarly_argument_acosta_l_pez_de_mesa_stoic_conception_of_free_will__2 critiques argument_frede_2011_epictetus_first_free_will` — **Acosta López de Mesa 2012, pp. 34-35 :** accord partiel sur les matériaux stoïciens, désaccord sur la priorité d'Épictète.
5. `scholarly_argument_blackson_minimum_belief_for_having_a_no_0 critiques argument_frede_2011_epictetus_first_free_will` — **Blackson 2025, pp. 83-85 :** substitution de l'exercice d'une capacité à l'assentiment comme objet du choix; Épictète n'est plus le premier.
6. `scholarly_argument_blackson_frede_s_schema_of_the_will_3 extends scholarly_argument_frede_stoic_origin_of_the_will_2` — **Blackson 2025, p. 85 :** reprise explicite du schéma minimal de Frede, avec modification de son objet.
7. `scholarly_argument_mansfeld_origin_of_free_will_concept_0 agrees_with argument_frede_2011_epictetus_first_free_will` — **Mansfeld 2012, pp. 351-353 :** les données sont jugées favorables à la priorité d'Épictète.
8. `scholarly_argument_mansfeld_origin_of_free_will_concept_0 critiques scholarly_position_dihle_will_christian_innovation` — **Mansfeld 2012, pp. 351-353 :** rejet de la chronologie qui ne fait apparaître la volonté qu'avec Augustin.
9. `scholarly_argument_mansfeld_aristotle_on_choice_and_will_1 agrees_with argument_frede_2011_aristotle_no_will_no_free_will` — **Mansfeld 2012, p. 354 :** approbation du choix aristotélicien sans faculté de volonté.
10. `scholarly_argument_mansfeld_simpler_doctrine_of_will_4 critiques argument_frede_2011_notion_is_technical_and_datable` — **Mansfeld 2012, p. 354 :** objection d'une volonté motrice plus simple, exclue par le cadrage moral de Frede.
11. `scholarly_argument_sorabji_freedom_and_the_will_in_ancien_0 critiques argument_frede_2011_epictetus_first_free_will` — **Sorabji 2017, pp. 57-58 :** aucune des quatre composantes de la volonté augustinienne n'est trouvée chez Épictète.

### Candidats rejetés

- `Frede -> Dihle`, `Irwin -> Dihle`, `Irwin -> MacIntyre`, `Frede -> Kahn` et `Bobzien -> Frede/Voelke` : triplets ou engagements équivalents déjà présents.
- `Bobzien 1998/2001 -> Frede 2011` : Bobzien précède Frede; les descriptions rétrospectives du KG ne constituent pas une réponse historique attestée.
- Plusieurs nœuds doublons d'une même extraction Frede/Bobzien : pas de nouvelles arêtes intra-chercheur, faute de rétractation documentée.

## 2. Aristote : déterminisme, indéterminisme et responsabilité

**Participants cartographiés :** Sorabji, Bobzien, Sauvé Meyer, Dorothea Frede, Echeñique et Natali. L'opposition Sorabji–Bobzien déjà vérifiée reste en place.

### Arêtes ajoutées au delta

12. `scholarly_argument_natali_causal_determinism_in_ancient__0 critiques scholarly_argument_bobzien_origin_of_free_will_problem_in_0` — **Natali 2005, pp. 13-14 :** objection explicite à la réduction bobzienne du débat à un épisode tardif et à la sous-estimation d'Aristote.
13. `argument_echenique_2014_aristotle_double_position_appraisals_accountability critiques argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap` — **Echeñique 2014, pp. 91-106 :** l'imputabilité empêche de rendre Aristote uniformément compatibiliste.
14. `argument_echenique_2014_aristotle_double_position_appraisals_accountability critiques scholarly_position_sorabji_aristotle_indeterminist` — **Echeñique 2014, pp. 91-106 :** l'évaluation morale empêche de rendre Aristote uniformément incompatibiliste.
15. `argument_frede_d_2014_aristotle_psychological_determinism agrees_with argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist` — **Dorothea Frede 2014, pp. 39-58 :** convergence anti-indéterministe sur le rôle du caractère et de la disposition.
16. `argument_frede_d_2014_aristotle_psychological_determinism agrees_with argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap` — **Dorothea Frede 2014, pp. 39-58 :** même convergence contre l'assimilation du bilatéralisme aristotélicien au PAP.

### Candidats rejetés

- `scholarly_position_sorabji_aristotle_indeterminist opposes scholarly_argument_bobzien_origin_of_free_will_problem_in_0` : déjà présent et attesté par Sorabji 1980, pp. 246-247, et Bobzien 1998, p. 144.
- Une seconde arête Natali depuis le nœud « importance d'Aristote » : même passage et même proposition que l'arête 12; rejet pour éviter une duplication sémantique.
- Donini contre des « commentateurs modernes » non nommés : cible insuffisamment déterminée.

## 3. Compatibilisme chrysippéen

**Participants cartographiés :** Bobzien, Salles, Gourinat, Brennan, Koch, Sharples, Sedley, Maso et Šuster. Les objections déjà câblées de Brennan, Koch, Sharples, Gourinat et Sedley à Bobzien n'ont pas été dupliquées.

### Arêtes ajoutées au delta

17. `scholarly_work_salles_2005_the_stoics_on_determinism_and_compatibil opposes scholarly_argument_bobzien_origin_of_free_will_problem_in_0` — **Salles 2005, pp. 78-81 :** rejet direct de la prémisse bobzienne selon laquelle l'exigence de possibilités spécifiques n'apparaît qu'avec un aristotélicien médio-platonicien; Salles la trouve déjà chez Aristote.
18. `argument_maso_2014_cicero_motus_animi_voluntarius_independence agrees_with argument_gourinat_2014_in_nostra_potestate_not_eph_hemin` — **Maso 2014, pp. 235-249 :** accord explicite sur l'autonomie sémantique des formules latines par rapport à `eph' hêmin`.
19. `scholarly_argument_uster_stoic_causal_determinism_and_i_1 agrees_with scholarly_argument_bobzien_stoic_causal_determinism_vs_fa_0` — **Šuster 2021, pp. 65-66 :** adoption de l'interprétation causale générale de Bobzien.
20. `scholarly_argument_uster_stoic_causal_determinism_and_i_1 agrees_with scholarly_argument_salles_stoic_determinism_0` — **Šuster 2021, pp. 65-66 :** adoption de la nécessitation par causes antérieures formulée par Salles.
21. `scholarly_argument_uster_the_structure_of_stoic_action__2 extends scholarly_argument_bobzien_chrysippus_compatibilism_fate__1` — **Šuster 2021, pp. 66-67 :** développement de la séquence impression–assentiment–action de Bobzien.
22. `scholarly_argument_uster_the_structure_of_stoic_action__2 extends scholarly_argument_salles_chrysippus_theory_of_action_an_3` — **Šuster 2021, pp. 66-67 :** même développement à partir de la théorie de l'action exposée par Salles.
23. `scholarly_argument_uster_chrysippus_s_cylinder_and_cone_0 extends scholarly_argument_bobzien_chrysippus_s_compatibilism_3` — **Šuster 2021, pp. 65-82 :** extension de la lecture du cylindre en « distillation mentale » des facteurs causalement pertinents.

### Candidats rejetés

- Rétractation Gourinat 2005, p. 237 n. 93 : la source dit bien « I am no longer confident » au sujet de Gourinat 1996, pp. 118-119. Le graphe ne possède toutefois aucun nœud pour cette position de 1996. Un `responds_to` vers la personne ou vers Bobzien aurait perdu la cible exacte; aucune arête n'est écrite dans un delta edges-only.
- Les critiques Brennan–Bobzien, Koch–Bobzien/Sharples, Sharples–Bobzien, Gourinat–Bobzien et Sedley–Bobzien/Sharples : déjà présentes.
- L'introduction Destrée/Salles/Zingano résume le chapitre de Salles, mais Salles est coauteur de l'introduction; rejet d'un faux accord entre coauteurs et d'une attribution trop lâche au seul Destrée.

## 4. Origène : libertarianisme, autonomie et apocatastase

**Participants cartographiés :** Fürst et le milieu de Münster, Gibbons, Sytsma, Ramelli, Crouzel, Koch, Frede, Bobzien et Boys-Stones.

### Arêtes ajoutées au delta

24. `scholarly_argument_gibbons_origen_s_theory_of_autonomy_an_0 critiques scholar_ramelli_ilaria` — **Gibbons 2016, pp. 673-674 :** Ramelli est nommée parmi les lectures par possibilités alternatives, exigence que Gibbons rejette ensuite.
25. `scholarly_argument_sytsma_permanent_apokatastasis opposes scholarly_work_crouzel_1985_origene` — **Sytsma 2018, pp. 24-25 :** rejet de l'incompatibilité posée par Crouzel entre libre arbitre et restauration universelle certaine.
26. `scholarly_argument_sytsma_critique_of_modern_critique agrees_with scholar_ramelli_ilaria` — **Sytsma 2018, pp. 30-31 :** accord sur la coexistence chez Origène de l'universalisme et de l'autonomie.
27. `scholarly_argument_sytsma_preselection_prearrangement_thesis critiques scholar_ramelli_ilaria` — **Sytsma 2018, pp. 31-34 et 182-223 :** les trois mécanismes proposés par Ramelli sont jugés insuffisamment expliqués; Sytsma leur substitue la présélection providentielle des circonstances.
28. `scholarly_argument_sytsma_autexousion_technical_term extends scholarly_argument_bobzien_autexousion_as_philosophical_t_6` — **Sytsma 2018, pp. 79-80 :** reprise explicite de Bobzien sur la technicisation et le renforcement d'`autexousion`, sans faculté indépendante de volonté.
29. `scholarly_argument_crouzel_origen_s_relationship_to_greek_0 critiques pub_koch_1932_pronoia` — **Crouzel 1962, pp. 105-112 :** rejet du paradoxe d'un Origène simultanément philosophe grec et chrétien fervent chez Koch.

### Candidats rejetés

- Fürst 2022 contre Gibbons 2016 : leurs thèses sont incompatibles, mais la recherche dans les pages substantielles de *Wege zur Freiheit* ne montre pas d'engagement nommé envers Gibbons. Une simple incompatibilité reconstruite ne suffit pas.
- « Lecture de Münster » comme cible institutionnelle : Münster est un milieu de recherche, pas un nœud-position. Les positions Fürst/Hengstermann existent, mais aucune source vérifiée ne les relie directement à Gibbons ou Sytsma sous forme de réponse nommée.
- Gibbons contre Koch et Benjamins, accord avec Frede, Boys-Stones et Bobzien : cinq arêtes déjà présentes et paginées dans le lot Gibbons.
- Ramelli 2014 cite Bobzien, Sharples et Frede, mais les passages inspectés ne marquent pas à eux seuls un verdict dialectique assez précis pour une nouvelle arête.

## 5. Le tournant augustinien

**Participants cartographiés :** Brown, Harrison, Fredriksen, Wetzel, Rist et TeSelle.

### Arêtes ajoutées au delta

Aucune. Les trois lignes de fracture sûres sont déjà câblées : Harrison contre Brown, Wetzel contre Rist et Wetzel contre TeSelle.

### Candidats rejetés

- Harrison–Brown : triplet existant, attesté par Barclay 2015 n. 17.
- Wetzel–Rist : triplet existant, attesté par Wetzel 1992, pp. 202 et 220-221.
- Wetzel–TeSelle : triplet existant, attesté par Wetzel 1992, pp. 198-202, avec qualification positive séparée.
- Harrison–Fredriksen : la source secondaire résume une opposition collective mais aucun nœud-publication Fredriksen suffisamment précis n'est disponible pour ce triplet.

## 6. Héritage carnéadien et thèse des *veteres*

**Participants cartographiés :** Amand, Koch 2011, Cicéron, Carnéade, Clitomaque et Antiochus.

### Arêtes ajoutées au delta

Aucune. Les divergences ont été cartographiées dans le rapport, mais aucune ne satisfait le seuil d'engagement nommé sans dupliquer les arêtes Koch déjà présentes.

### Candidats rejetés

- `scholarly_argument_koch_2011_veteres_debate_anachronistic critiques synthesis_amand1945_cicero_defato_source_antiochus` : Koch 2011, pp. 368-373, démontre l'anachronisme de la mise en scène des *veteres*, tandis qu'Amand 1945, pp. 66-67, adopte la source Antiochus. Koch ne nomme cependant pas Amand dans ce passage; conflit propositionnel sans engagement attesté, donc aucune arête.
- Koch 2011 contre Bobzien et Sharples : engagements explicites déjà câblés dans le lot stoïcien.
- Amand contre Ramelli : ancienne arête réfutée lors de l'audit dialectique; elle n'est pas réintroduite.

## 7. Prolongement épicurien révélé par le scan systématique

**Participants cartographiés :** O'Keefe, Sedley, Long et la position « Épicure premier inventeur du libre arbitre ».

### Arêtes ajoutées au delta

30. `scholarly_argument_o_keefe_epicurus_theory_of_freedom_vs__0 opposes scholarly_position_long_sedley_epicurus_first_freewill` — **O'Keefe 2005, pp. 1-2 et p. viii :** rejet de la lecture centrée sur le clinamen comme solution au problème moderne du libre arbitre.
31. `scholarly_argument_o_keefe_epicurus_position_on_reduction_0 critiques scholar_sedley_david` — **O'Keefe 2002, pp. 153-155 :** rejet du soi radicalement émergent exerçant une causalité descendante sur les atomes.
32. `scholarly_argument_o_keefe_role_of_the_swerve_in_epicurus_1 responds_to scholar_sedley_david` — **O'Keefe 2005, p. viii :** dette explicitement reconnue envers le travail pionnier de Sedley, malgré le désaccord.

### Candidats rejetés

- Multiplication de trois critiques O'Keefe 2002 contre Sedley depuis des nœuds quasi synonymes : une seule arête précise est conservée pour la causalité descendante.
- `extends` vers Sedley pour le rôle du clinamen : `responds_to` est plus exact, car O'Keefe reconnaît la dette tout en rejetant la conclusion.

## Pin G6 `opposes`

Le graphe contient actuellement **18** arêtes `opposes`. Le delta en ajoute exactement **3** : Salles–Bobzien, Sytsma–Crouzel et O'Keefe–Long/Sedley. Le compte post-application sera donc **21**.

Le pin `assert len(all_opposes) == 18` de `graphrag/tests/g6/test_reachability_probe.py` **doit devenir 21 dans le même commit que l'application**. Il n'est pas modifié dans ce dry-run. L'applier refuse `--apply` tant que le pin ne correspond pas au compte post-application.

## Sorties de contrôle

Commande gate directe :

```text
$ python3 scripts/check_ingestion_rules.py --new-only scripts/data_2026_08_17_faultlines_wiring.json
ingestion-rules: delta of 0 nodes / 32 edges
  no violations

BLOCK: 0   WARN: 0
```

Commande dry-run de l'applier :

```text
$ python3 scripts/ingest_2026_08_17_faultlines_wiring.py
delta: 0 nodes / 32 edges
novel: 0 nodes / 32 edges (skipped existing: 0 edges)
relations: agrees_with=8, critiques=15, extends=5, opposes=3, responds_to=1
opposes: current=18, novel=3, post-apply=21, g6-pin=18
ingestion-rules: delta of 0 nodes / 32 edges
  no violations

BLOCK: 0   WARN: 0
dry-run: nothing written; future apply must update G6 opposes pin from 18 to 21 in the same commit
```

Contrôle G6 de l'état live non appliqué :

```text
$ PYTHONPATH='knowledge graph/src:graphrag/src' .venv/bin/python -m pytest -q graphrag/tests/g6/test_reachability_probe.py
graphrag/tests/g6/test_reachability_probe.py ......                      [100%]
6 passed
```

## Verdict

Le lot est prêt à être revu et commité comme delta edges-only. Il n'a pas été appliqué. L'application future exige simultanément la mise à jour du pin G6 à 21.
