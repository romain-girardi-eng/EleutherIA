# Campagne Jev 2026-09-24 — c4_dedup_schools

Fenêtre gratuite Vercel AI Gateway (`typesafe-ai/jev`), close le 2026-09-25. Les réponses ci-dessous sont des PREUVES pour arbitrage humain ultérieur — aucune écriture n'a été faite dans `data/kg/*`, `data/corpus/*`, la base ou la prod. Coût confirmé sur tous les appels : `$0.00`.

**Couverture COMPLÈTE** sur les deux volets (relance supervisée après saturation initiale de l'endpoint partagé — voir « historique » plus bas) : 25895/25895 paires (100%), 2428/2428 nœuds (100%).

## Ce qui a été demandé

**Partie A — résolution d'entités.** Sur les nœuds non-`passage` de `data/kg/nodes.jsonl` (person, work, publication, concept, argument, synthesis, school, debate, position, quote, group, source_collection, controversy, event, conceptual_evolution), construction déterministe de paires candidates par blocage (tokens partagés du label/alternative_names, tokens partagés de la description, bibtex_key exact, (auteur, année), patronyme partagé), puis pour chaque paire deux questions booléennes à Jev : « même entité » et « partie/édition/traduction l'une de l'autre ». Voir `questions.json` pour le texte exact.

**Partie B —** (1) table de normalisation déterministe des chaînes `school` existantes (aucun appel Jev), (2) question CHOICE à Jev sur chaque nœud person/work/argument : à quelle école ou tradition appartient ce nœud, d'après sa seule description ? Liste de 16 options fournie par la consigne de campagne (voir `questions.json`).

## Couverture (finale)

| Volet | Fait | Prévu | Couverture | Erreurs de chunk journalisées (retries épuisés, comptent aussi les runs de reprise) |
|---|---|---|---|---|
| A — paires dédup | 25895 paires (2590 appels) | 25895 paires | **100%** | 467 |
| B2 — proposition école | 2428 nœuds (398 appels) | 2428 nœuds (person+work+argument) | **100%** | 110 |

Sur les 2428 nœuds répondus : 494 person, 252 work, 1682 argument.

**Historique** : la première passe (menée en direct dans cette session) a buté sur la saturation de l'endpoint gratuit partagé `typesafe-ai/jev` (429/503 en continu même après 5 tentatives avec backoff exponentiel par appel) et s'est arrêtée à 23,5% (dédup) / 16,8% (école). L'orchestrateur a relancé les mêmes runners (`run_dedup.py`, `run_school_propose.py`, `run_school_propose_pw.py` — idempotents, reprise automatique sur `results_*.jsonl`) sous supervision jusqu'à couverture complète. Aucune donnée déjà collectée n'a été perdue ou recalculée : les runs de reprise ajoutent simplement les chunks manquants.

## Coût

`$0.00` sur les 2988 appels réussis (fenêtre gratuite confirmée, `providerMetadata.gateway.cost` à zéro sur chaque réponse, y compris pendant les runs de reprise).

## Distribution des réponses par palier de confiance

**Partie A — probabilité « même entité »** (sur les 25895 paires, couverture complète) :

| Palier | N | % |
|---|---|---|
| ≥0,9 | 8 | 0.0% |
| 0,7–0,9 | 131 | 0.5% |
| 0,3–0,7 | 1342 | 5.2% |
| ≤0,3 | 24414 | 94.3% |

**Partie B2 — probabilité du choix retenu** (sur les 2428 nœuds, couverture complète) :

| Palier | N | % |
|---|---|---|
| ≥0,9 | 848 | 34.9% |
| 0,7–0,9 | 748 | 30.8% |
| 0,3–0,7 | 818 | 33.7% |
| ≤0,3 | 14 | 0.6% |

Distribution des écoles proposées (choix retenu, tous paliers confondus, 2428 nœuds) : Christian (patristic) : 831, Modern scholarship : 748, Stoic : 236, Peripatetic : 170, Jewish : 107, Neoplatonist : 82, Pyrrhonist/Sceptic : 67, Middle Platonist : 60, Epicurean : 42, Academic/Platonist : 31, Gnostic : 21, Cannot be determined from the description : 11, Presocratic : 9, Cynic : 7, No school affiliation / not a school-bound figure : 6.

## Résultats marquants — exemples vérifiés à la main (relecture directe de `data/kg/nodes.jsonl`, pas seulement de l'avis de Jev)

### Partie A — les 8 doublons probables (p≥0,9), TOUS relus intégralement

1. **`sc123_melito_peri_pascha` / `work_melito_peri_pascha`** — p=0,96. Deux nœuds `work` pour la même homélie pascale de Méliton de Sardes (*Peri Pascha*, c. 160-170 CE) — confirmé, les deux descriptions renvoient au même texte (l'une cite *Pasch.* 47-54).
2. **`work_bardaisan_book_of_laws` / `work_bardesanes_liber_legum_regionum`** — p=0,95. Deux nœuds pour le même dialogue syriaque (*Livre des lois des pays* / *Liber Legum Regionum*), composé par Philippe(us), disciple de Bardesane/Bardaisan d'Édesse, avant 222 CE. Un nœud en anglais, l'autre en français, même œuvre — confirmé.
3. **`sc379_athenagoras_legatio` / `work_athenagoras_legatio_sc379`** — p=0,94. Deux nœuds `work` pour la même *Legatio pro Christianis* d'Athénagore (c. 176-177 CE) — confirmé.
4. **`pub_linjamaa_2019_ethics_tripartite_tractate` / `scholarly_work_linjamaa_2019_the_ethics_of_the_tripartite_tractate_nh`** — p=0,94. Même monographie, Linjamaa 2019, *The Ethics of the Tripartite Tractate* (Brill, NHMS 95) — confirmé.
5. **`work_irenaeus_demonstratio_apostolic` / `work_irenaeus_epideixis`** — p=0,94. Même traité catéchétique d'Irénée de Lyon (*Epideixis tou apostolikou kerygmatos* / *Démonstration de la prédication apostolique*, connu par la seule traduction arménienne de 1904) — confirmé, deux résumés différents du même texte.
6. **`argument_bobzien_2001_b1_philopator_late_compatibilism` / `scholarly_argument_bobzien_later_stoic_compatibilism_phil_6`** — p=0,93. Même reconstruction (Bobzien 2001, ch. 8) de la théorie stoïcienne tardive attribuée à « PHILOPATOR » — confirmé, l'un est la fiche complète, l'autre un doublon condensé de la même thèse.
7. **`sc470_aristides_apologia` / `work_aristides_apology_sc470`** — p=0,92. Même *Apologie* d'Aristide d'Athènes (SC 470, éd. Pouderon) — confirmé.
8. **`pub_plantinga_god_evil_free_will_defence` / `scholarly_work_tomberlin_1977_god_evil_and_the_free_will_defence`** — p=0,92. Doublon Tomberlin & McGuinness 1977 — confirmé, et l'id du premier nœud (`pub_plantinga_...`) attribue par erreur l'article à Plantinga alors que la fiche elle-même nomme Tomberlin & McGuinness comme auteurs (défaut R9 en prime).

**8/8 confirmés à la lecture directe des deux nœuds** — exactement le type d'incident que documente `docs/development/ingestion-rules.md` (R2/R3b) : deux ids pour un seul texte ou une seule publication.

### Partie B2 — 10 nouvelles propositions d'école à haute confiance (p≥0,9), vérifiées une à une contre la description du nœud

| Nœud | Type | Proposition | p | Vérification |
|---|---|---|---|---|
| `argument_fate_efficient_cause_alex` | argument | Peripatetic | 1,0 | Alexandre d'Aphrodise, *De Fato* 3-4 — confirmé |
| `argument_plotinus_freedom_argument_7c561972` | argument | Neoplatonist | 1,0 | description dit explicitement « Neoplatonic metaphysics » — confirmé |
| `argument_sea_battle_aristotle_f6g7h8i9` | argument | Peripatetic | 1,0 | Aristote, *De Interpretatione* 9 — confirmé |
| `argument_sirach_free_will_theodicy_m7n8o9p0` | argument | Jewish | 1,0 | Ben Sira, Sir 15 :11-20, « Jewish wisdom tradition » — confirmé |
| `person_basil_great_d379` | person | Christian (patristic) | 1,0 | Basile de Césarée, Père cappadocien — confirmé |
| `person_apuleius_madauros_124_170` | person | Middle Platonist | 1,0 | « Platonizing philosopher », *De Platone* proche du *Didaskalikos* d'Alcinoos — confirmé |
| `person_atticus_2c_ce` | person | Middle Platonist | 1,0 | description le nomme explicitement « Middle Platonist » — confirmé |
| `work_apuleius_de_platone` | work | Middle Platonist | 1,0 | « Latin Middle-Platonist doxographical handbook » — confirmé |
| `work_augustine_de_civitate_dei` | work | Christian (patristic) | 1,0 | Augustin, *De Civitate Dei*, œuvre apologétique chrétienne — confirmé |
| `sc268_origenes_peri_archon` | work | Christian (patristic) | 1,0 | Origène, *Peri Archon* III, traité chrétien sur l'αὐτεξούσιον — confirmé |

**10/10 confirmées.** Aucune erreur trouvée dans cet échantillon à p=1,0 — la précision à ce palier de confiance est excellente sur ce lot, contrairement au cas isolé Dennett→« Cynic » (p=0,55 seulement, hors des files de qualité) relevé lors de la couverture partielle et toujours présent dans les données complètes.

### « Conflits » avec l'école déjà renseignée — 40 lignes, à lire avec prudence

Le motif observé sur la couverture partielle se confirme à 100% : quasiment tous les « conflits » (ex. Diodore de Tarse : `Antiochene School` existant vs `Christian (patristic)` proposé ; Ignatius/Clément de Rome : `Apostolic Fathers` vs `Christian (patristic)` ; Méliton, Athénagore : `Christian Apologetics` vs `Christian (patristic)`) reflètent un écart de **granularité** entre le vocabulaire gelé du projet (`school_scheme.json`, 18 labels, R18) et la liste à 16 options imposée par cette campagne, qui n'a qu'un seul seau « Christian (patristic) » là où le projet distingue Apostolic Fathers / Christian Apologetics / Antiochene School / Christian Platonism / Patristic / Latin Patristic. **Aucune ligne de `queue_school_conflicts.csv` ne doit être appliquée telle quelle.**

### Partie B1 — normalisation des chaînes `school`

Constat déterministe, sans appel Jev : les 18 valeurs `school` actuellement présentes sur `data/kg/nodes.jsonl` (tous types, 19109 affectations non nulles) correspondent **déjà exactement** aux 18 labels canoniques du vocabulaire gelé (`knowledge graph/ontology/school_scheme.json`, R18) — 0 valeur non mappée. Rien à corriger côté orthographe/synonymes ; le vrai manque est la **couverture** : seuls 34 person et 27 work sur 496/252 portent un `school`, contre 19043 passage sur 19902. C'est exactement ce que la partie B2 comble (792 propositions à p≥0,9 pour des nœuds actuellement sans `school`).

## Limites connues

- **Liste d'écoles de la campagne plus grossière que le vocabulaire gelé du projet.** Voir la section « conflits » ci-dessus — ne pas les traiter comme des corrections.
- **Blocage à fort rappel, donc beaucoup d'ambigus/rejetés côté dédup.** Sur 25895 paires (couverture complète), seules 8 atteignent p≥0,9 (0.0%) ; 1473 tombent en zone ambiguë (0,3-0,9) et méritent un tri humain plus fin que le seuil automatique. C'est le comportement attendu d'un blocage optimisé pour le rappel — le filtrage utile se fait en aval, par palier de confiance.
- **Jev n'est pas infaillible.** Sur l'échantillon élargi à couverture complète, l'unique erreur nette repérée reste Dennett→« Cynic » à p=0,55 (sous le seuil de toutes les files de qualité). Les 8 doublons et les 10 propositions d'école vérifiés ci-dessus sont 100% corrects, mais restent un échantillon, pas une preuve d'exhaustivité — traiter les files comme des propositions à arbitrer, pas comme des vérités.
- **`queue_ambiguous_pairs.csv`** (1473 lignes) et **`queue_school_undetermined.csv`** (204 lignes) sont volumineuses par construction (le blocage et la liste d'écoles visent le rappel) : elles servent de réservoir pour un tri humain ultérieur, pas de liste à traiter en bloc.

## Fichiers livrés

Dans `data/quality/jev_2026_09_24/c4_dedup_schools/` :

- Scripts : `lib_common.py`, `build_candidates_dedup.py`, `run_dedup.py`, `build_school_norm_table.py`, `build_candidates_school.py`, `run_school_propose.py`, `run_school_propose_pw.py`, `make_queues.py`, `compute_stats.py`
- `questions.json` — texte exact des questions et schéma d'état
- `candidates.jsonl` (+ `candidates.jsonl.gz`), `candidates_school.jsonl`, `candidates_school_pw.jsonl` — paires/nœuds candidats (25895 + 2428 + 746)
- `results_dedup.jsonl` (2590/2590 appels), `results_school.jsonl` (304/304), `results_school_pw.jsonl` (94/94) — réponses Jev brutes, couverture complète
- `errors_dedup.jsonl`, `errors_school.jsonl`, `errors_school_pw.jsonl` — échecs journalisés en cours de route (retries épuisés), sans incidence sur la couverture finale
- `exploded_dedup.jsonl` (25895 lignes), `exploded_school.jsonl` (2428 lignes) — réponses éclatées une ligne par paire/nœud
- `school_normalization_table.csv` — table déterministe partie B1
- Files de relecture, triées par valeur attendue : `queue_likely_duplicates.csv` (8), `queue_ambiguous_pairs.csv` (1473), `queue_part_of_relations.csv` (96), `queue_rejected_sample.csv` (300, échantillon), `queue_school_fill_in.csv` (792), `queue_school_conflicts.csv` (40), `queue_school_undetermined.csv` (204)
- `queue_stats.json` — compteurs des files

## Ce qu'il reste à faire

1. Arbitrage humain (Romain) sur `queue_likely_duplicates.csv` (8 paires, 8/8 pré-vérifiées ci-dessus) et `queue_school_fill_in.csv` (792 propositions, échantillon de 10 pré-vérifié) — ce sont les deux files à plus forte valeur immédiate, prêtes pour un passage en écriture KG (hors périmètre de cette campagne).
2. `queue_ambiguous_pairs.csv` (1473 lignes) et `queue_school_undetermined.csv` (204 lignes) : tri humain plus lent, pas de raccourci automatique proposé.
3. Ne jamais appliquer `queue_school_conflicts.csv` (40 lignes) sans relire manuellement — c'est presque toujours un écart de granularité, pas une erreur.
