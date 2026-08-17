# Plan de lecture et d’ingestion — vague A (2026-08-17)

## 1. Périmètre et méthode

Cette vague couvre les items 1 à 5 du TOP 10 de la section 6 de `data/audit/2026-08-17_cold_audit_sol.md`. La section 6 a été lue avant les PDF, puis les règles R1–R18 et les patrons `scripts/data_2026_08_17_origen_lit.json`, `scripts/ingest_2026_08_17_origen_lit.py` et `scripts/ingest_2026_08_17_origenality_import.py` ont été contrôlés.

Les PDF ont été lus dans leur langue : anglais pour Karavites et Crawford, norvégien pour Nilsen, tchèque pour Karfíková, allemand pour van der Eijk. Les descriptions de tous les arguments sont en anglais dans le delta. Les extractions texte ont servi d’index ; les pages retenues ont également été rendues en image et contrôlées visuellement. Aucun texte grec ou latin n’a été produit : les descriptions nouvelles emploient uniquement des translittérations lorsque le terme technique est indispensable.

Le delta contient :

- 53 nœuds nouveaux : 5 chercheurs, 4 publications et 44 arguments ;
- 145 arêtes déclarées, dont 144 sont nouvelles dans l’état courant du KG ;
- 1 enrichissement conditionnel de shell bibliographique ;
- 17 arguments pour Karavites, 6 pour Nilsen, 7 pour Karfíková, 6 pour van der Eijk et 8 pour Crawford.

## 2. Contrôle R2 et corridors existants

La recherche d’identité dans `data/kg/nodes.jsonl` n’a trouvé aucun shell de personne pour les cinq auteurs et aucun shell de publication pour Karavites, Nilsen, Karfíková ou Crawford. Un seul shell Origenality existe et doit être promu, non dupliqué :

- `pub_eijk_1988_origenes_verteidigung_des_freien_willens_in_de_oratione`.

Les ancrages primaires suivants ont été vérifiés dans le snapshot :

| Corridor | Nœuds existants vérifiés | Usage dans la vague |
|---|---|---|
| Clément, *Stromates* | `work_clement_stromateis`; `passage_clement_strom_1_17_82`; `passage_clement_strom_1_17_83`; `passage_clement_strom_1_17_84`; les nœuds `passage_clement_strom_2_11_50` à `_52` existent aussi | Les trois passages I.17 sont reliés lorsque le locus coïncide exactement ; les autres analyses sont reliées au work, sans inventer de passage absent. |
| Clément, *Pédagogue* | `work_clement_paedagogus` | Ancrage des arguments de paideia, peur et correction. |
| Tatien, *Oratio* 7–11 | `work_tatian_oratio`; `passage_tatian_orat_7`; `passage_tatian_orat_8_9`; `passage_tatian_orat_11` | Ancrage des arguments sur chute angélique, astrologie, destin et passions. |
| Tatien, *Oratio* 5 et 16–18 | `passage_tatian_5_2`; `passage_tatian_16_2`; `passage_tatian_17_2`; `passage_tatian_18_1` | Ancrage non forcé des arguments réels de Crawford sur maladie, pharmacologie et logothérapie. |
| Origène, *De oratione* 6 | `work_origen_de_oratione`; `passage_origen_de_orat_6` | Les six arguments de van der Eijk citent le passage existant. |

Le triple `pub_eijk_1988... --discusses--> person_origen_alexandria_185_254ce_s9t0u1v2` existe déjà ; l’appliqueur le saute. C’est l’unique différence entre les 145 arêtes du delta et les 144 arêtes nouvelles.

## 3. Peter Karavites, 1999

### Pages lues et saut motivé

Ont été lus intégralement : préface et introduction, chapitres I–II et IV–VI, soit les pages imprimées ix–xii, 1–86 et 109–180. Cela couvre les antécédents et la théorie du mal, la justice et la paideia divines, l’`autexousion` et la `prohairesis`, la polémique anti-gnostique, la perfection et la conclusion.

Le chapitre III, « Sexuality and Evil », pp. 87–108, est le seul chapitre sauté. Il traite principalement du mariage, de l’encratisme et de l’éthique sexuelle. Il ne développe ni l’argument sur l’`autexousion`, ni la paideia corrective, ni le désaccord anti-déterministe requis. Les conclusions qui touchent réellement la liberté et la perfection sont reprises et vérifiées dans les chapitres IV–VI. Le saut évite donc de forcer une pertinence au libre arbitre.

### Carte argumentative

| Pages | Nœud | Argument retenu |
|---|---|---|
| 29–35 | `scholarly_argument_karavites_sin_voluntary_existential_failure` | Le péché est une activité et un échec existentiel volontaire, non une substance ou une nature mauvaise. |
| 30–38 | `scholarly_argument_karavites_ignorance_weakness_remedies_responsibility` | Ignorance et faiblesse restent corrigibles par démonstration et entraînement ; elles n’abolissent donc pas la responsabilité. |
| 43–46 | `scholarly_argument_karavites_demonic_influence_preserves_human_agency` | La sollicitation démonique n’est pas une contrainte irrésistible ; l’alliance avec le mal passe par le choix. |
| 44–46 | `scholarly_argument_karavites_adaptability_to_virtue_answers_gnostic_dilemma` | Adam est créé apte à acquérir la vertu, non déjà achevé ; cette perfectibilité répond au dilemme gnostique sur un créateur parfait. |
| 55–61 | `scholarly_argument_karavites_divine_justice_corrective_communion` | La justice divine est une activité bonne et communicative ordonnée à la restauration, non d’abord une sentence magistrale. |
| 64–68 | `scholarly_argument_karavites_law_trains_choice_without_compulsion` | La Loi forme le jugement et donne des critères de blâme et de louange sans remplacer la décision de l’agent. |
| 68–75 | `scholarly_argument_karavites_punishment_therapeutic_not_retributive` | Réprimande, peur et peine sont une paideia thérapeutique visant repentir et restauration, non vengeance. |
| 73–78 | `scholarly_argument_karavites_fear_temporary_pedagogy_acknowledged_limits` | La peur révérencielle est un instrument initial et provisoire ; Karavites signale aussi les limites philosophiques et le risque coercitif de cette défense. |
| 115–120 | `scholarly_argument_karavites_autexousion_rational_self_determination` | Dans une terminologie non fixée, l’`autexousion` est la puissance rationnelle d’auto-détermination morale qui fonde responsabilité, louange et blâme. |
| 120–121 | `scholarly_argument_karavites_prohairesis_good_or_evil_broader_than_aristotle` | Clément élargit la `prohairesis` aristotélicienne : elle peut choisir le bien ou le mal, et pas seulement les moyens corrects. |
| 121–122, 135–138 | `scholarly_argument_karavites_true_freedom_passions_and_grace` | La vraie liberté vainc les passions, mais ne se réduit pas à l’autarcie stoïcienne : elle requiert grâce, communion et relation à Dieu. |
| 122–124 | `scholarly_argument_karavites_antignostic_faith_voluntary_not_natural` | Contre Basilide et Valentin, la foi est assentiment volontaire ; une foi possédée par nature rendrait inutiles incarnation, instruction et repentir. |
| 124–126 | `scholarly_argument_karavites_antitactae_license_is_slavery` | La licence antitacte prend la servitude aux désirs pour la liberté ; l’ascèse et l’entraînement restaurent l’autorité rationnelle. |
| 127–129, 139–143 | `scholarly_argument_karavites_grace_impels_does_not_compel` | La grâce éveille, instruit et donne ce que l’effort ne produit pas ; elle ne contraint pourtant pas l’assentiment. |
| 133–135 | `scholarly_argument_karavites_permission_of_evil_exposes_tension` | La permission du mal préserve une liberté significative, mais l’appel à des raisons divines suffisantes non spécifiées reste circulaire pour le sceptique. |
| 155–156, 163–165 | `scholarly_argument_karavites_virtue_potential_training_and_grace` | La vertu joint perfectibilité naturelle, habituation volontaire et grâce ; la perfection humaine reste relative. |
| 170–174 | `scholarly_argument_karavites_second_adam_reopens_freedom_as_communion` | Le second Adam rouvre une liberté personnelle comme amour et communion, au-delà de l’enfermement passionnel dans l’individualité biologique. |

Aucune arête dialectique moderne n’est ajoutée pour Karavites : les critiques qu’il formule portent surtout sur la cohérence de Clément ou sur des adversaires anciens, pas sur une thèse savante moderne déjà modélisée avec engagement paginé.

## 4. Fredrik Nilsen, 2025

### Pages lues

Article lu intégralement en norvégien, pp. 52–63, bibliographie comprise. Les arguments sont décrits en anglais dans le delta.

### Carte argumentative

| Pages | Nœud | Argument retenu |
|---|---|---|
| 53–55 | `scholarly_argument_nilsen_negative_free_will_two_criteria` | Un libre arbitre négatif adéquat doit placer la volonté entre raison et désirs, puis lui reconnaître une indépendance relative vis-à-vis des deux. |
| 56–58 | `scholarly_argument_nilsen_aristotle_prohairesis_fails_independence` | Chez Aristote, la `prohairesis` choisit les moyens de la fin rationnelle ; l’akratique agit contre elle, donc le second critère échoue. |
| 58–59 | `scholarly_argument_nilsen_clement_prohairesis_chooses_logos_or_desire` | Chez Clément, la `prohairesis` choisit réellement entre Logos divin et désir irrationnel et peut porter sur l’orientation générale de l’action. |
| 59–60 | `scholarly_argument_nilsen_pedagogy_habituates_without_erasing_choice` | La paideia transforme la peur servile en loyauté rationnelle et forme l’habitude sans se substituer à l’agent. |
| 60 | `scholarly_argument_nilsen_epictetus_only_partial_precursor` | Épictète anticipe partiellement le modèle, mais la fusion finale de la `prohairesis` et de la raison empêche de remplir sûrement les deux critères. |
| 60–61 | `scholarly_argument_nilsen_clement_first_negative_free_will` | Clément, non Augustin, serait le premier philosophe à posséder un concept adéquat de libre arbitre négatif, malgré la préscience et l’élection divines. |

### Arêtes dialectiques attestées

- `scholarly_argument_nilsen_clement_first_negative_free_will --opposes--> argument_dihle_1982_augustine_invents_philosophical_voluntas` ; attestation : Nilsen 2025, pp. 53 et 60–61.
- `scholarly_argument_nilsen_clement_first_negative_free_will --opposes--> argument_dihle_1982_greek_intellectualism_thesis` ; attestation : Nilsen 2025, pp. 53–55 et 58–61.

Ces deux arêtes expriment des engagements nommés et paginés. Elles expliquent le passage du compte `opposes` de 21 à 23. Aucune arête contre Arendt n’est fabriquée, car le KG ne possède pas de shell suffisamment précis à promouvoir dans ce périmètre.

## 5. Lenka Karfíková, 2025

### Pages lues

Article lu intégralement en tchèque, pp. 171–183. Les arguments sont décrits en anglais dans le delta.

### Carte argumentative

| Pages | Nœud | Argument retenu |
|---|---|---|
| 171–172 | `scholarly_argument_karfikova_clement_freedom_lexical_field` | `Eleutheria`, `parresia`, `prohairesis`, `eph' hemin` et `autexousios` forment un champ différencié, non des synonymes interchangeables. |
| 173–175 | `scholarly_argument_karfikova_antignostic_faith_is_free_assent` | Contre le déterminisme naturel valentinien et basilidien, la foi est l’assentiment rationnel d’une âme qui se gouverne elle-même. |
| 175–176 | `scholarly_argument_karfikova_adult_self_rule_replaces_childish_fear` | L’`autexousios` marque la maturité de l’adulte qui obéit au Logos, tandis que la `prohairesis` volontaire nomme sa décision de foi. |
| 176–178 | `scholarly_argument_karfikova_grace_prompts_and_rewards_free_choice` | La Sagesse divine sollicite, attire, soutient et récompense le choix ; le saut humain au-delà de ses forces n’a pas lieu sans grâce. |
| 179–180 | `scholarly_argument_karfikova_self_rule_grounds_good_and_evil_responsibility` | L’auto-gouvernement peut servir le bien ou le mal et s’applique même au diable ; il fonde donc la responsabilité plutôt qu’une direction morale garantie. |
| 180–181 | `scholarly_argument_karfikova_will_as_free_self_moving_mind` | Le fragment du traité perdu *Sur la providence* définit la volonté comme mouvement libre d’un esprit qui se gouverne lui-même. |
| 181–183 | `scholarly_argument_karfikova_autexousion_prerequisite_not_gnostic_freedom` | Verdict explicitement enregistré comme `suspended` sur l’égalité réelle des alternatives : l’`autexousion` est la condition permettant de choisir la liberté, tandis que la liberté gnostique accomplie choisit le bien pour lui-même. |

Karfíková ne répond pas à Nilsen dans l’article. Leur différence de cadre n’est donc pas transformée artificiellement en `opposes`, `critiques` ou `agrees_with`.

## 6. Ph. J. van der Eijk, 1988

### Pages lues

Article lu intégralement en allemand, pp. 339–351. L’argument principal occupe les pp. 339–348 ; les notes pp. 348–351 ont également été lues.

### Carte argumentative

| Pages | Nœud | Argument retenu |
|---|---|---|
| 339 | `scholarly_argument_van_der_eijk_foreknowledge_logically_secondary` | La préscience est antérieure temporellement mais secondaire logiquement par rapport aux actes libres ; prédestination et providence se structurent à partir d’elle. |
| 340–341 | `scholarly_argument_van_der_eijk_prayer_objections_christian_probably_gnostic` | Les objections à la prière sont chrétiennes et probablement gnostiques ; un arrière-plan stoïcien indirect reste possible, sans être affirmé comme verdict ferme. |
| 341–345 | `scholarly_argument_van_der_eijk_movement_taxonomy_prepares_reductio` | La taxonomie des mouvements affine l’opposition intérieur/extérieur et prépare une reductio ontologique. |
| 345–347 | `scholarly_argument_van_der_eijk_denial_freedom_erases_living_rational_essence` | Nier l’auto-mouvement humain fait perdre à l’homme son statut d’être vivant, puis plus précisément d’être rationnel. |
| 345–346 | `scholarly_argument_van_der_eijk_animal_quasi_reason_verdict_suspended` | Le statut quasi rationnel de certains animaux est explicitement `suspended` : Origène envisage cette possibilité sans l’accepter ni la rejeter sans équivoque. |
| 347–348 | `scholarly_argument_van_der_eijk_de_oratione_strengthens_de_principiis_proof` | *De oratione* ajoute la catégorie du mouvement « par soi » et une liaison entre mouvement et essence qui renforce théoriquement la preuve de *De principiis*. |

### Promotion du shell

L’enrichissement cible exclusivement `pub_eijk_1988_origenes_verteidigung_des_freien_willens_in_de_oratione`. Il exige avant mutation :

- type `publication` ;
- label exact du shell ;
- année 1988 ;
- DOI `10.1163/157007288x00147` ;
- `citation_verdict == bibliographic_import` ;
- `source_rank` Origenality exact indiquant que le contenu n’a pas encore été lu.

Après application autorisée, il remplacera `citation_verdict` par `read_and_extracted`, réécrira `source_rank` comme lecture intégrale allemande paginée, ajoutera le chemin du PDF, la portée pp. 339–351, `author_id`, la référence vérifiée et une provenance de lecture séparée. Une précondition divergente provoque un arrêt fatal ; aucune promotion partielle n’est possible.

## 7. Matthew R. Crawford, 2021

### Pages lues

Article lu intégralement, pp. 31–59.

### Carte argumentative

| Pages | Nœud | Argument retenu |
|---|---|---|
| 34–39 | `scholarly_argument_crawford_astrology_continues_angelic_fall_not_digression` | L’astrologie d’*Oratio* 8–11 prolonge directement la chute angélique du chapitre 7 ; elle n’est pas une digression. |
| 35–39, 50–52 | `scholarly_argument_crawford_enochic_illicit_instruction_explains_two_domains` | L’enseignement illicite de 1 Hénoch explique le choix précis de l’astrologie et de la pharmacologie ; la voie de transmission directe ou via Justin reste `suspended`. |
| 40–42 | `scholarly_argument_crawford_astral_fate_arbitrary_not_efficacious` | Les affirmations apparentes de l’efficacité du destin rejouent ironiquement la position adverse ; les constellations arbitraires n’ont pas de prise cosmique naturelle. |
| 42–43 | `scholarly_argument_crawford_real_fate_redefined_as_slavery_to_passions` | Le seul destin réel est la servitude aux passions, dont l’humain peut sortir par la maîtrise du désir. |
| 43–45 | `scholarly_argument_crawford_demons_can_directly_cause_bodily_disease` | Tatien attribue aux démons une action corporelle réelle dans certaines maladies, et pas seulement une illusion mentale. |
| 45–48 | `scholarly_argument_crawford_pharmacology_has_no_intrinsic_efficacy` | L’analogie avec le langage conventionnel signifie que racines et composés n’ont aucune efficacité intrinsèque ; leur apparence d’ordre est imposée par les démons. |
| 48–50 | `scholarly_argument_crawford_rejects_all_pharmacology_not_medicine_only_softly` | Tatien rejette toute la pharmacologie, remèdes comme poisons, et non seulement les cultes guérisseurs païens ; cette radicalité est exceptionnelle. |
| 53–58 | `scholarly_argument_crawford_oration_as_logotherapy_against_demonic_disorder` | L’*Oratio* se présente comme logothérapie imitant le Logos ; la métaphore des démons-bandits oppose leur pseudo-ordre illégitime à l’ordre vrai du Créateur. |

### Arête dialectique attestée

- `scholarly_argument_crawford_astral_fate_arbitrary_not_efficacious --critiques--> scholarly_work_denzey_lewis_2013_cosmology_and_fate_in_gnosticism_and_gra` ; attestation : Crawford 2021, pp. 40–42.

Crawford nomme et cite la thèse de Denzey Lewis avant de l’écarter. Les désaccords avec Timotin et Crosignani sont conservés dans les descriptions paginées, mais aucun shell supplémentaire non lu n’est créé seulement pour multiplier les arêtes.

## 8. Vérifications et sorties

### Structure du delta

```text
nodes: 53
arguments: 44
edges: 145
enrichments: 1
relations: advanced_in=44, cites_primary_source=44, created_by=49,
           critiques=1, discusses=5, opposes=2
duplicate node ids: 0
duplicate edge ids: 0
duplicate edge triples: 0
Greek-script runs in new argument descriptions: 0
```

### Compilation

Commande :

```bash
python3 -m py_compile scripts/ingest_2026_08_17_reading_wave_a.py
```

Sortie : aucune ; code de retour 0.

### Gate R1–R18 et dry-run

Le module partagé existant `graphrag/src/eleutheria_graphrag/agents/dialectical_relations.py` contient actuellement une graphie d’exception Python 2, `except TypeError, ValueError`, qui empêche son import direct sous Python 3 avant même l’examen d’un delta. Conformément au patron déjà établi par l’appliqueur `central_debates`, le nouvel appliqueur copie le gate et ses dépendances dans un répertoire temporaire, normalise cette unique graphie dans la copie, puis exécute le vrai `check_ingestion_rules.py --new-only`. Aucun fichier du dépôt n’est modifié par cette normalisation.

Commande :

```bash
python3 scripts/ingest_2026_08_17_reading_wave_a.py
```

Sortie :

```text
delta: 53 nodes / 145 edges / 1 enrichments
novel: 53 nodes / 144 edges (skipped existing: 0 nodes, 1 edges)
promotions: ready=1, already-applied=0, failed=0
opposes: current=21, novel=2, post-apply=23, g6-pin=21
--- check_ingestion_rules.py --new-only (temporary mirror) ---
temporary parser normalisations: 1 (shared dependency only; repository unchanged)
ingestion-rules: delta of 53 nodes / 144 edges
  no violations

BLOCK: 0   WARN: 0
dry-run: nothing written; future --apply requires the G6 opposes pin to be 23 (currently 21)
```

### Contrôle du refus `--apply`

Commande de contrôle :

```bash
python3 scripts/ingest_2026_08_17_reading_wave_a.py --apply
```

Fin de sortie et code :

```text
FATAL: G6 opposes pin is 21, but post-apply count is 23; update the pin in the same commit before --apply
nothing written
exit code: 1
```

Les empreintes SHA-256 avant et après ce contrôle sont identiques :

```text
33cc28709c4288625278e69d8ea4c37d8c123e0987d96418c1ac2ed8f57c14ba  data/kg/nodes.jsonl
d93ffc920afe05013ec9cd0da3660fc7c5a5220e5be7c77978bcd028f55cd7db  data/kg/edges.jsonl
```

Aucun fichier `.bak-reading_a` n’a été créé. Rien n’a été écrit dans `data/kg` ou `data/corpus`. Pour autoriser une future application, le pin de `graphrag/tests/g6/test_reachability_probe.py` devra être porté de 21 à 23 dans la même révision ; cette vague additive ne modifie pas ce fichier existant.
