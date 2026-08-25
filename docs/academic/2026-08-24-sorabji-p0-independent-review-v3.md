# Revue indépendante Sorabji P0 v3

Date: 2026-08-24  
Portée: revue indépendante, adversariale et sans écriture de données de la proposition Sorabji P0 v3. Aucun `--write` n'a été exécuté. Aucun fichier KG, corpus, registre, manifeste, BibTeX ou audit data n'a été modifié par cette revue.  
Verdict: **FAIL - NO APPLY**.

## 1. Tuple exact revu

Le verdict est borné au tuple suivant. Le hash de l'applier seul ne suffit pas, car celui-ci importe dynamiquement l'exporteur BibTeX.

| Artefact | SHA-256 revu |
|---|---|
| Applier Sorabji | `984225f5083fd0fb0241441f9a55405c60187899cf0ab89590df1e51f319ad1f` |
| Exporteur BibTeX | `24bd0decd932fd08ef386d3f80e3badfb22e24e0dbacfc9d35bf298b372ae53e` |
| Tests Sorabji | `c48ebd6a4acd77475a9ec7fd84eca40a86a19a778e65c022f24d675a5966bc59` |
| Tests exporteur | `3cb168c5da84dfef349cd74cfbd422be54db80dd4ca8bd48570ddbf28eed5c41` |
| Preview `/tmp/sorabji-v3-final.json` | `aa79bde106f2fad6fabfe9ebe1708333eb7cb6a876846d470c25aa1a8da2d508` |
| Schéma normatif registry | `829d39c081b4b4cbeaaf1c5381870a91ae350b086e78043979856d1d9d85129a` |
| Report BibTeX baseline | `137076a4635826407b5454a8b9fe6611b5548c736138e85930b2917c3fd80325` |

Le dry-run de ce tuple était byte-identique au preview v3 et retournait `write_performed=false`, `status=ready_for_independent_re_review_no_apply`.

Après la découverte décrite en section 5, l'exporteur et les tests ont été modifiés pour préparer une v4. Ces fichiers plus récents ne sont pas couverts ici. La v3 reste une proposition distincte et échouée, même si le fichier applier conserve le même hash.

## 2. Verdict synthétique

| Contrôle | Résultat v3 | Verdict |
|---|---|---|
| Ancien blocker v2: schéma normatif registry | dette héritée `41 -> 41`, nouvelles erreurs `0`, erreurs retirées `0`; 19 records Sorabji individuellement valides | PASS |
| Ancien blocker v2: BibTeX et report compagnon | `540/538 -> 543/543`; report exact, hashé et transactionnel | PASS |
| Huit stratégies Sorabji | huit entrées exactes, Cléanthe et Chrysippe séparés | PASS |
| Citabilité runtime | neuf noeuds interprétatifs `discoverable_only` dans la policy réelle | PASS |
| Descriptions, dog-cart et références héritées | corrections v2 inchangées et fail-closed | PASS |
| Manifestations 1980/1983 | objet intellectuel et manifestations correctement séparés | PASS |
| Rollback, journal et recovery | mécanisme durable et report BibTeX inclus dans Snapshot A | PASS |
| E2 rights et exposition | `internal_audit_only`, `unverified_do_not_republish`, citations longues non dupliquées | PASS |
| Touched-set KG réel | 100 noeuds modifiés, dont 89 publications hors des 11 IDs déclarés | **FAIL P0** |

Les deux blockers v2 sont effectivement corrigés. La v3 reste toutefois inapplicable à cause d'un nouveau blocker P0: une mutation par aliasing de 89 noeuds hors périmètre.

## 3. Ancien blocker v2 corrigé: schéma normatif

La validation a été recalculée indépendamment avec `jsonschema.Draft7Validator`, les `$defs` de `data/goals/sota/registry.schema.json` et tous les shards des cinq familles registry.

| Type | Records baseline | Erreurs baseline | Erreurs preview |
|---|---:|---:|---:|
| source | 34 | 11 | 11 |
| evidence | 25 | 21 | 21 |
| issue | 29 | 9 | 9 |
| verification | 101 | 0 | 0 |
| wave | 4 | 0 | 0 |
| **Total** | **193** | **41** | **41** |

Résultats de la comparaison par identité, chemin de propriété, validateur et message:

- nouvelles erreurs: `0`;
- erreurs retirées: `0`;
- identités dupliquées dans les cinq familles: `0`;
- erreurs sur la source Sorabji touchée: `0`;
- erreurs sur les sept evidence units Sorabji: `0`;
- erreurs sur les deux issues Sorabji: `0`;
- erreurs sur les huit verifications Sorabji: `0`;
- erreurs sur la wave touchée: `0`.

Les stamps top-level interdits ont disparu. Les précisions d'acquisition sont maintenant dans le champ source `notes` permis. Les propriétés non admises ont été retirées des objets artefacts. Les sept evidence units restent `in_review` et `paraphrase_only`; les deux issues restent `open`; les huit verifications sont une `identity` et sept `primary`. Aucun stage `independent`, `adversarial` ou `human_signoff` n'est inventé.

Verdict de cet ancien blocker: **PASS**.

## 4. Ancien blocker v2 corrigé: BibTeX et report compagnon

### 4.1 Recalcul indépendant

| Mesure | Baseline | Preview v3 |
|---|---:|---:|
| Entrées BibTeX réelles | 540 | 543 |
| `entries_written` du report | 538 | 543 |
| Ecart | 2 | 0 |
| Publication nodes | 538 dans l'ancien report | 540 recalculés |
| Records `missing` | 176 dans l'ancien report | 175 recalculés |

Le BibTeX preview a le SHA-256 `2bf6ea54d93bb86249997a076e73dde025b8e765e1edcab59f641ad77c5f4dcc`. Ses 543 headers sont tous parsables et correspondent à 543 clés uniques. La liste ordonnée de clés a le SHA-256 `a9bd6ea98e9748562d1dc62f0cca1ba5bfe262fb14c94acb0bfc4c8cfd965d7e`.

Le report preview:

- contient exactement les 543 clés dans l'ordre de l'artefact;
- contient le bon hash du BibTeX;
- compte 540 publication nodes;
- contient 175 records `missing` et `nodes_with_missing_fields=175`;
- est byte-identique, après sérialisation canonique, à une recomputation par `build_companion_report`;
- explicite les deux clés Bobzien historiques présentes seulement dans l'artefact et les deux clés longues correspondantes présentes seulement dans l'export canonique.

Le fichier report preview a le SHA-256 `66355e056418b9c446a278e9d29b0119d60628504f73bc10af08d73d155b6f72`.

### 4.2 Inclusion transactionnelle

Le plan contient exactement 11 sorties data, dont `data/kg/publications_bibtex_report.json`. `apply_plan` ajoute le report d'application et la quarantine, soit 13 cibles transactionnelles. Snapshot A contient exactement les mêmes 13 chemins.

Pour le report BibTeX:

- before-image complète dans Snapshot A: SHA-256 `137076a4635826407b5454a8b9fe6611b5548c736138e85930b2917c3fd80325`;
- desired image: SHA-256 `66355e056418b9c446a278e9d29b0119d60628504f73bc10af08d73d155b6f72`;
- quarantine: un record `bibtex_report_before_summary` avec hash, comptes et hash des IDs manquants;
- journal, backup, rollback, second recovery et post-validation idempotente couvrent cette cible comme les autres.

La quarantine proposée contient 36 records. Elle comprend 11 before-images de noeuds, 2 arêtes supprimées, les résumés E2 et report BibTeX, les absences attendues et les records registry remplacés. Aucun chemin corpus ou citation ne fait partie des sorties.

Verdict de cet ancien blocker: **PASS**.

## 5. Nouveau blocker P0: 89 mutations KG hors touched-set

### 5.1 Diff réel

Une comparaison indépendante, par ID et JSON canonique, entre `data/kg/nodes.jsonl` et la sortie nodes du plan v3 donne:

| Mesure | Valeur |
|---|---:|
| Noeuds déclarés dans `touched_node_ids` | 11 |
| Noeuds réellement modifiés | 100 |
| Noeuds déclarés réellement modifiés | 11 |
| Noeuds modifiés hors déclaration | **89** |
| Noeuds ajoutés ou supprimés | 0 |
| Type des 89 noeuds cachés | publication |
| Forme du diff sur chacun | ajout unique de `metadata.title` |

Pour chacun des 89 noeuds, la valeur ajoutée est le `label` existant. Aucun autre champ n'est modifié dans ces 89 records. Par exemple:

- `pub_alberti_1999_aspasius`: ajout de `metadata.title="Il volontario e la scelta in Aspasio"`;
- `pub_astolfi_2015_alexander_fate`: ajout de `metadata.title` depuis son label;
- `pub_long_1986_hellenistic`: ajout de `metadata.title` depuis son label.

Le compteur annoncé reste pourtant `kg_nodes_modified=11`. `touched_node_ids` contient seulement les 11 IDs Sorabji prévus, et la quarantine ne conserve que 11 `kg_node_before`. Les 89 mutations supplémentaires ne sont donc ni déclarées, ni comptées, ni représentées par des before-images record-level. La before-image fichier de Snapshot A rendrait un rollback physique possible, mais elle ne corrige pas la violation de périmètre ni l'incomplétude de l'audit record-level.

### 5.2 Cause reproduite

Dans l'exporteur portant le hash v3:

1. `normalize_mapping(value)` retourne directement `value` lorsque metadata est déjà un dictionnaire.
2. `publication_to_bibtex(node)` exécute ensuite `metadata.setdefault("title", node.get("label"))`.
3. `build_companion_report` appelle l'export complet sur les 540 publication nodes.
4. L'applier passe sa liste `nodes` vivante comme `all_nodes` à `transform_bib`.
5. L'applier sérialise cette même liste après le calcul du report.

Le `setdefault` modifie donc les dictionnaires metadata originaux par aliasing. Un appel isolé à l'export complet sur une copie des nodes baseline reproduit exactement 89 mutations. Ces 89 IDs correspondent un pour un aux 89 modifications hors touched-set du preview.

Ce bug n'est pas une simple variation de rendu BibTeX: il ferait écrire des changements KG non autorisés, y compris sur des publications Long, Bobzien, Sharples et d'autres transactions savantes indépendantes.

### 5.3 Inventaire exact des 89 IDs cachés

```text
pub_alberti_1999_aspasius
pub_astolfi_2015_alexander_fate
pub_banner_2017_indeterminate_self_plotinus
pub_barclay_2020_power_of_grace
pub_blowers_2016_maximus_confessor
pub_bobichon_2003_justin_dialogue_tryphon
pub_bobzien_2013_found_in_translation
pub_bobzien_2014_aristotle_ne_1113b7_8_free_choice
pub_bobzien_2014_choice_responsibility
pub_boyd_2011_response_to_ron_highfield
pub_boys_stones_2007_origen
pub_boys_stones_2018_platonist_philosophy
pub_brand_2013_evil_within_without
pub_brass_2019_neuroscience_free_will
pub_broadie_1991_ethics_aristotle
pub_camplani_2017_bardaisan_and_the_bible
pub_caruso_2016_free_will_skepticism_criminal_behavior
pub_comerro_2013_libre_arbitre_islam
pub_cooper_1999_reason_emotion
pub_deery_2007_compatibilism
pub_destree_2014_plato_er
pub_destree_salles_zingano_2014_what_is_up_to_us
pub_dillon_1977_middle_platonists
pub_dimuzio_2008_aristotle_determinism
pub_dobbin_1991_prohairesis_epictetus
pub_eastman_2017_paul_and_the_person
pub_edelstein_kidd_1972_posidonius
pub_eliasson_2008_notion_eph_hemin_plotinus
pub_forschner_2018_philosophie_stoa
pub_gauthier_1970_ethique_nicomaque
pub_gourinat_2005_stoiciens
pub_graver_1999_propatheia
pub_graver_2007_stoicism_emotion
pub_hadot_1981_exercices_spirituels
pub_haggard_2008_human_volition
pub_hankinson_1999_determinism
pub_hardie_1968_aristotle_freewill
pub_hengstermann_2016_freiheitsmetaphysik
pub_highfield_2011_god_controls_by_liberating
pub_hildebrandt_2022_alexander_lazy_arguments
pub_horn_1996_augustinus_wille
pub_jurasz_2023_bardesane_hermeneutique
pub_kahn_1988_discovering_will
pub_kane_2005_contemporary_intro
pub_karamanolis_2021_philosophy_early_christianity
pub_kenny_1979_aristotle_will
pub_kidd_1971_posidonius
pub_kirwan_1984_review_dihle
pub_klawans_2012_josephus_theologies
pub_knobe_2003_intentional_action_side_effects
pub_kobusch_2018_selbstwerdung
pub_koch_1932_pronoia
pub_koch_2011_destin_causes_impulsion
pub_koch_2018_kinesis_anaitios
pub_leroux_1996_human_freedom_plotinus
pub_linjamaa_2019_ethics_tripartite_tractate
pub_list_2019_free_will_real
pub_long_1971_freedom_determinism
pub_long_1986_hellenistic
pub_long_2002_epictetus
pub_macintyre_1990_three_rival_versions
pub_mansfeld_1991_will_chrysippus
pub_merker_2013_frede_review
pub_meyer_1998_moral_responsibility_aristotle_after
pub_minns_parvis_2009_justin_apologies
pub_muller_2009_willensschwache
pub_plantinga_god_evil_free_will_defence
pub_pohlenz_1948_stoa
pub_rambaux_1993_clinamen
pub_renard_2020_fatalite_providence
pub_ross_1923_aristotle
pub_ryle_1949_concept_mind
pub_schockenhoff_1990_fest_freiheit
pub_sharples_1982_providence
pub_sharples_1983_alexander_fate
pub_sharples_1986_soft_determinism
pub_sharples_1987_anrw
pub_sharples_1991_cicero_boethius
pub_sharples_2008_accident_determinisme
pub_sharples_2010_peripatetic
pub_sharples_alberti_1999_aspasius
pub_sharples_sorabji_2007_greek_roman
pub_snell_1946_entdeckung_geistes
pub_sorabji_2006_self
pub_sytsma_2020_universal_salvation_origen
pub_ter_haar_romeny_1997_syrian_greek_dress
pub_voelke_1973_idee_volonte
pub_williams_1993_shame_necessity
pub_wolfson_1942_philo_free_will
```

Verdict touched-set: **FAIL P0**.

## 6. Régression des six familles précédemment PASS

### 6.1 Huit stratégies

La structure E2 contient exactement huit entrées numérotées `1` à `8`. La première est attribuée à Cléanthe et la deuxième à Chrysippe. La liste correspond exactement à `EIGHT_STRATEGIES`.

Verdict: **PASS**.

### 6.2 Citabilité runtime

La policy réelle `graphrag/src/eleutheria_graphrag/agents/citability.py` retourne `discoverable_only` pour chacun des neuf IDs interprétatifs. Aucun des onze noeuds touchés ne conserve `verified`, `citation_verified` ou `verified_reference`.

Verdict: **PASS**.

### 6.3 Descriptions et dog-cart

Les descriptions publiques de `concept_eph_hemin...` et `debate_stoic_compatibilism` restent attribuées et disputées. Le dog-cart reste une `analogy`, sans Cléanthe, sans locus primaire actif, avec Hippolyte seulement comme témoin candidat en attente de recollation. Son évaluation reste suspendue et sa prémisse P2 dit que consentir sous nécessité ne prouve pas une issue alternative.

Verdict: **PASS**.

### 6.4 Manifestations 1980/1983

Le noeud publication reste un objet intellectuel sans publisher, place ou ISBN work-level. Les manifestations Duckworth 1980, Cornell 1980, première Cornell paperback 1983 et Chicago 2006 restent séparées. Le tirage local est `unknown_not_inferred`.

Verdict: **PASS**.

### 6.5 Transaction et hard-crash recovery

Les tests ciblés couvrent la dérive pré-commit, `BaseException`, échec de remplacement, échec de fsync, échec de rollback suivi d'un second recovery, états `prepared`, `committing` et `committed`, ainsi que le stage orphelin. Le report BibTeX est bien inclus dans les outputs et Snapshot A.

Verdict mécanique: **PASS**. Cette robustesse ne rend pas licites les 89 mutations hors périmètre.

### 6.6 E2 rights

Le preview conserve `runtime_exposure=internal_audit_only`, `reuse_status=unverified_do_not_republish` et `legacy_quotes_status=retained_in_place_not_duplicated`. Les neuf champs `quote_verbatim*` historiques ne sont dupliqués ni dans la quarantine ni dans les evidence units. Le dossier 2017 reste distinct et ses cinq arêtes sont byte-identiques.

Verdict: **PASS**.

## 7. Tests et commandes sans écriture de données

### Dry-run v3

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/apply_2026_08_24_sorabji_p0_repair.py --json
```

Résultat sur le tuple gelé: code 0; preview byte-identique à `/tmp/sorabji-v3-final.json`; `write_performed=false`.

### Suite v3 ciblée

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider \
  tests/test_sorabji_p0_repair.py \
  tests/test_export_publications_bibtex.py
```

Résultat: **30 passed**, un warning de configuration pytest sans effet sur les assertions. Le PASS de cette suite ne détectait pas la mutation globale des nodes: elle comparait les compteurs déclarés et les IDs prévus, mais pas le diff réel de tous les records.

### Suite globale

La commande globale de 28 tests a aussi retourné **28 passed**. Elle n'est pas utilisée pour étendre le verdict au-delà du tuple gelé, car la préparation concurrente de la v4 avait commencé avant le contrôle final de ses hashes. Le blocker P0 repose sur le diff et la reproduction effectués pendant que les quatre hashes v3 étaient encore gelés.

### Absence de write

À la clôture, les chemins suivants sont absents:

- `data/audit/2026-08-24_sorabji_p0_repair.json`;
- `data/audit/2026-08-24_sorabji_p0_quarantine.jsonl`;
- `data/audit/.sorabji_p0_transaction.json`;
- `data/audit/.sorabji_p0_transaction_backups`.

Les tests ont utilisé leurs répertoires temporaires. Aucun `--write` Sorabji n'a été appelé.

## 8. Correctif et gates requis pour une v4

Le correctif doit rendre l'exporteur fonctionnellement pur, par exemple en copiant metadata avant toute valeur par défaut. La nouvelle revue doit au minimum vérifier:

1. deep equality des nodes avant et après `publication_entries_to_bibtex`, `build_publication_export` et `build_companion_report`;
2. diff exhaustif de tous les nodes: IDs modifiés exactement égaux à `TOUCHED_NODE_IDS`;
3. lignes hors touched-set byte-identiques;
4. IDs des before-images `kg_node_before` exactement égaux aux IDs réellement modifiés;
5. compteur `kg_nodes_modified` égal au nombre réel de records modifiés;
6. arêtes: exactement deux suppressions, aucun ajout ou changement;
7. mêmes invariants registry `41 -> 41`, BibTeX/report `543/543`, transaction et recovery;
8. nouveaux hashes pour exporteur, tests et preview.

## 9. Conclusion

La v3 corrige bien les deux blockers P0 de la v2: elle n'ajoute aucune erreur au schéma normatif et rend le report BibTeX exact, reproductible et transactionnel. Les six familles savantes et fail-closed précédemment validées ne régressent pas.

Elle ne peut cependant pas être appliquée. Le calcul du report BibTeX modifie silencieusement 89 publication nodes hors du touched-set, tandis que les compteurs, before-hashes record-level et quarantine n'en déclarent que 11.

Décision: **FAIL - NO APPLY**.

Le présent artefact n'est ni une autorisation de `--write`, ni un review PASS, ni un adversarial ou human signoff du registry, ni une vérification des sources antiques. Une v4 doit être revue sur un nouveau tuple complet.
