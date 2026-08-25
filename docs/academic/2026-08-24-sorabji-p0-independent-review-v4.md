# Revue indépendante Sorabji P0 v4

Date: 2026-08-24  
Portée: revue indépendante et adversariale de la proposition Sorabji P0 v4, sans écriture de données. Aucun `--write` n'a été exécuté. Aucun fichier KG, corpus, registre, manifeste, BibTeX ou audit data n'a été modifié par cette revue.  
Verdict: **PASS - NO APPLY PERFORMED**.

## 1. Tuple exact revu

Le verdict est borné au tuple complet suivant. L'applier importe dynamiquement l'exporteur; son hash ne constitue donc pas seul une identité exécutable suffisante.

| Artefact | SHA-256 revu |
|---|---|
| Applier Sorabji | `984225f5083fd0fb0241441f9a55405c60187899cf0ab89590df1e51f319ad1f` |
| Exporteur BibTeX pur v4 | `65166dcc664f73cd7e4e6c83442e8ee9ef485ac38053702003a2e9bb17a32162` |
| Tests Sorabji | `b046fb5ffb43dfbccb1e412a6581102daedf1a178aa6ac5da474ca83c4e12599` |
| Tests exporteur | `cfc01095e8b66d6b3b7638f4694ee485a45b6dfd9d376162b012d9fef92b344a` |
| Preview `/tmp/sorabji-v4-final.json` | `272233ba740486247446cc93588938d5cd7829c3309dd021509a949c326e1c13` |
| Schéma normatif registry | `829d39c081b4b4cbeaaf1c5381870a91ae350b086e78043979856d1d9d85129a` |
| Report BibTeX baseline | `137076a4635826407b5454a8b9fe6611b5548c736138e85930b2917c3fd80325` |
| Scan Sorabji | `be1f8fce483503d04504c73da30dc9bbcd52f5f8c04bd0e520cbd42fd4a3d500` |

Les quatre fichiers code/tests ont été rehashés après le dry-run et les suites de tests; les empreintes sont restées identiques. Le dry-run est byte-identique au preview v4 et retourne `write_performed=false`, `status=ready_for_independent_re_review_no_apply`.

## 2. Verdict synthétique

| Gate | Résultat indépendant | Verdict |
|---|---|---|
| Pureté exporteur | zéro mutation sur 23 246 nodes à travers les trois couches d'export | PASS |
| Diff nodes | exactement les 11 IDs déclarés; toutes les autres lignes byte-identiques | PASS |
| Diff edges | exactement 2 suppressions; aucun ajout ou changement retenu | PASS |
| Touched-set | exactement 11 sorties data; aucun corpus ou citation | PASS |
| Quarantine | 36 records; before-images et absences exactes | PASS |
| Transaction/recovery | 13 cibles avec report et quarantine; Snapshot A exact; recovery testé | PASS |
| Schéma normatif registry | `41 -> 41`, nouvelles erreurs `0`, 19 records Sorabji valides | PASS |
| BibTeX/report | `540/538 -> 543/543`; 543 clés uniques; report exact | PASS |
| Six familles savantes v2 | aucune régression | PASS |
| Tests | 32 ciblés et 28 globaux PASS; ruff PASS | PASS |

Aucun blocker P0 résiduel n'a été trouvé sur ce tuple.

## 3. Correction du blocker v3: pureté de l'exporteur

La v3 échouait parce que l'exporteur retournait le dictionnaire metadata du caller puis y appliquait `setdefault("title", ...)`. Le report compagnon mutait ainsi 89 publication nodes hors périmètre.

La v4 copie maintenant profondément:

- un dictionnaire metadata fourni directement;
- un dictionnaire metadata obtenu par parsing JSON;
- chaque manifestation BibTeX avant héritage des champs.

### 3.1 Contrôle indépendant de non-mutation

Les trois couches ont été appelées successivement sur les 23 246 nodes previewables, dont 540 publications:

1. `publication_entries_to_bibtex` sur chaque publication;
2. `build_publication_export` sur la liste complète;
3. `build_companion_report` sur la liste complète et le BibTeX candidat.

Résultats:

- nodes profondément égaux avant/après: oui;
- IDs des objets rows inchangés: oui;
- IDs des objets metadata inchangés: oui;
- nombre de records mutés: `0`;
- résultats identiques sur un clone profond: oui pour les trois couches;
- résultat de `normalize_mapping` profondément égal mais distinct du dictionnaire source: oui;
- sous-dictionnaires et listes imbriqués distincts: oui.

Le report candidat reste exactement recomputable après cette correction. La pureté ne change donc pas les bytes bibliographiques attendus.

Verdict pureté: **PASS**.

## 4. Diff exhaustif des nodes et edges

### 4.1 Nodes

| Mesure | Baseline | Preview v4 |
|---|---:|---:|
| Records | 23 246 | 23 246 |
| Records ajoutés | 0 | 0 |
| Records supprimés | 0 | 0 |
| Records JSON modifiés | - | 11 |
| Lignes brutes modifiées | - | 11 |

Les deux ensembles de 11 IDs sont identiques à `TOUCHED_NODE_IDS`:

- `argument_chrysippus_causal_taxonomy`;
- `argument_cylinder_analogy_chrysippus_k1l2m3n4`;
- `argument_the_dog_and_cart_argument_9ba60714`;
- `argument_the_master_argument_kurieuon_logos_355f4d3f`;
- `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6`;
- `concept_cylinder_analogy_chrysippus_e5f6g7h8`;
- `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7`;
- `debate_stoic_compatibilism`;
- `person_sorabji_richard_contemporary`;
- `pub_sorabji_1980_necessity_cause_blame`;
- `scholarly_position_sorabji_aristotle_indeterminist`.

Les 23 235 lignes hors set sont byte-identiques. L'ordre des nodes est inchangé. Les 11 before-hashes correspondent exactement à `NODE_BEFORE_HASHES`, et les 11 after-hashes à `NODE_AFTER_HASHES`. Le fichier nodes preview corrigé a le SHA-256 `ef792eb6373ac0252a5d6bba5bde2c57d03178d8c1ca2e10e14f10817865a31f`.

### 4.2 Edges

| Mesure | Baseline | Preview v4 |
|---|---:|---:|
| Records | 55 792 | 55 790 |
| Ajouts | 0 | 0 |
| Modifications de records retenus | 0 | 0 |
| Suppressions | - | 2 |

Les suppressions exactes sont:

- `0615cd5b-95aa-4e00-9d2c-264f8fae0c3c`;
- `69f8b629-1c14-4281-83f7-68c6ebaeb820`.

Toutes les lignes retenues sont byte-identiques. Les cinq arêtes `advanced_in` Sorabji 2017 conservent leurs hashes attendus.

Verdict diff KG: **PASS**.

## 5. Outputs, quarantine et transaction

### 5.1 Touched-set fichier

Le plan contient exactement 11 sorties data:

- `data/kg/nodes.jsonl`;
- `data/kg/edges.jsonl`;
- `data/kg/publications.bib`;
- `data/kg/publications_bibtex_report.json`;
- `data/kg/e2_patches/sorabji.json`;
- `data/scholarly_sources/manifest.jsonl`;
- les cinq shards registry source, evidence, issues, wave et verifications.

Il ne contient aucun chemin `data/corpus`, passage ou citation. Les 11 hashes `output_sha256_preview` correspondent aux bytes recomputés.

### 5.2 Quarantine

Les 36 records se répartissent exactement ainsi:

| Type | Nombre |
|---|---:|
| `kg_node_before` | 11 |
| `kg_edge_removed` | 2 |
| `e2_patch_before_summary` | 1 |
| `scholarly_manifest_absence_before` | 1 |
| `registry_source_before` | 1 |
| `registry_evidence_before` | 2 |
| `registry_evidence_absence_before` | 5 |
| `registry_issue_absence_before` | 2 |
| `registry_wave_before` | 1 |
| `registry_verification_absence_before` | 8 |
| `bib_entry_before` | 1 |
| `bibtex_report_before_summary` | 1 |

Les 11 before-images de nodes ont exactement les IDs réellement modifiés et leurs hashes correspondent à `NODE_BEFORE_HASHES`. Les deux arêtes et leurs hashes correspondent exactement aux suppressions réelles.

### 5.3 Snapshot A et recovery

`apply_plan` ajoute le report d'application et la quarantine aux 11 sorties data. Les 13 cibles transactionnelles sont exactement les 13 entrées Snapshot A.

Le report BibTeX possède:

- before-image complète SHA-256 `137076a4635826407b5454a8b9fe6611b5548c736138e85930b2917c3fd80325`;
- desired image SHA-256 `66355e056418b9c446a278e9d29b0119d60628504f73bc10af08d73d155b6f72`;
- résumé de quarantine avec comptes et hash des IDs manquants.

Les tests couvrent dérive pré-commit, `BaseException`, échec de remplacement, échec de fsync, échec de rollback et second recovery, ainsi que les états `prepared`, `committing`, `committed` et le stage orphelin. Journal et backups ne sont supprimés qu'après restauration ou commit durable complet. La post-validation reconstruit le plan et exige l'idempotence.

Verdict transactionnel: **PASS**.

## 6. Schéma normatif registry

La validation indépendante Draft 7 a chargé tous les shards et les `$defs` normatifs.

| Type | Erreurs baseline | Erreurs preview |
|---|---:|---:|
| source | 11 | 11 |
| evidence | 21 | 21 |
| issue | 9 | 9 |
| verification | 0 | 0 |
| wave | 0 | 0 |
| **Total** | **41** | **41** |

- nouvelles erreurs: `0`;
- erreurs retirées: `0`;
- records Sorabji touchés ou ajoutés: `19`;
- erreurs sur ces 19 records: `0`.

Les sept evidence units restent `in_review` et `paraphrase_only`. Les deux issues restent `open`. Les huit verifications sont une `identity` et sept `primary`; aucun stage `independent`, `adversarial` ou `human_signoff` n'est créé. La wave reste bloquée par les deux issues.

L'auditeur registry complet retourne `structurally_valid=true`, `errors=[]`, `exit_ready=false`. La dette stricte reste `block=1155`, `warn=768` avant et après preview.

Verdict registry: **PASS**.

## 7. BibTeX et report compagnon

| Mesure | Baseline | Preview v4 |
|---|---:|---:|
| Entrées BibTeX réelles | 540 | 543 |
| `entries_written` | 538 | 543 |
| Ecart | 2 | 0 |
| Clés uniques | 540 | 543 |

Le BibTeX preview a le SHA-256 `2bf6ea54d93bb86249997a076e73dde025b8e765e1edcab59f641ad77c5f4dcc`. La liste ordonnée des 543 clés a le SHA-256 `a9bd6ea98e9748562d1dc62f0cca1ba5bfe262fb14c94acb0bfc4c8cfd965d7e`.

Le report:

- correspond exactement à une recomputation de `build_companion_report`;
- contient les 543 clés dans l'ordre de l'artefact;
- contient le bon hash BibTeX;
- compte 540 publication nodes et 175 records `missing`;
- explicite les deux clés Bobzien artefact-only et les deux clés canoniques longues correspondantes;
- conserve le hash du BibTeX baseline.

La transaction ne prétend pas que l'ensemble historique est byte-identique à un export canonique. Elle décrit exactement l'artefact chirurgical préservé et son delta canonique.

Verdict BibTeX/report: **PASS**.

## 8. Régression des six familles savantes

### 8.1 Huit stratégies

La liste contient exactement huit entrées numérotées `1` à `8`, identiques à `EIGHT_STRATEGIES`. Cléanthe et Chrysippe occupent respectivement les positions 1 et 2.

Verdict: **PASS**.

### 8.2 Citabilité runtime

La policy réelle retourne `discoverable_only` pour les neuf noeuds interprétatifs. Aucun des onze noeuds touchés ne conserve `verified`, `citation_verified` ou `verified_reference`.

Verdict: **PASS**.

### 8.3 Descriptions et dog-cart

Les descriptions `eph' hemin` et compatibilisme restent attribuées et disputées. Le dog-cart est une `analogy`, sans attribution à Cléanthe ni locus primaire actif. Hippolyte reste un témoin candidat en attente de recollation, et la validité reste non évaluée.

Verdict: **PASS**.

### 8.4 Manifestations

Le work Sorabji est `intellectual_publication` et ne porte aucun publisher, place ou ISBN work-level. Duckworth 1980, Cornell 1980, première Cornell paperback 1983 et Chicago 2006 sont séparés. Le tirage local reste `unknown_not_inferred`.

Verdict: **PASS**.

### 8.5 Recovery

Le mécanisme transactionnel et les tests de hard-crash restent inchangés et passent. Le nouveau report BibTeX est bien couvert.

Verdict: **PASS**.

### 8.6 E2 rights

E2 reste `internal_audit_only` et `unverified_do_not_republish`. Les neuf champs historiques `quote_verbatim*` ne sont dupliqués ni dans la quarantine ni dans les evidence units. Le fichier E2 preview conserve le SHA-256 `d84f98c3bce2859cc5ec36b9ea5785f5aa92240a05bb902bb6b970261f84e660`.

Verdict: **PASS**.

La chaîne visuelle Sorabji ne change pas en v4: scan, applier, 11 after-hashes savants et E2 sont identiques à ceux relus aux étapes précédentes. La correction v4 ne touche que la pureté de l'exporteur et ses tests; elle ne modifie aucune claim ou page map.

## 9. Tests exécutés sans data write

### Dry-run

```text
PYTHONDONTWRITEBYTECODE=1 python3 \
  scripts/apply_2026_08_24_sorabji_p0_repair.py --json
```

Résultat: code 0; stdout byte-identique à `/tmp/sorabji-v4-final.json`; `write_performed=false`.

### Suite ciblée

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider \
  tests/test_sorabji_p0_repair.py \
  tests/test_export_publications_bibtex.py
```

Résultat: **32 passed**, un warning de configuration pytest sans effet sur les assertions.

### Suite globale

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider \
  tests/test_zero_debt_gates.py \
  tests/test_snapshot_passage_integrity.py \
  tests/test_check_kg_corpus_locus_parity.py \
  tests/test_check_kg_work_child_canonical.py \
  tests/test_scholarly_sources_manifest.py \
  tests/test_audit_sota_registry.py
```

Résultat: **28 passed**, le même warning de configuration sans effet.

### Lint

```text
ruff check --no-cache \
  scripts/apply_2026_08_24_sorabji_p0_repair.py \
  scripts/export_publications_bibtex.py \
  tests/test_sorabji_p0_repair.py \
  tests/test_export_publications_bibtex.py
```

Résultat: **All checks passed**.

### Absence d'application

Après tous les contrôles, les chemins suivants restent absents:

- `data/audit/2026-08-24_sorabji_p0_repair.json`;
- `data/audit/2026-08-24_sorabji_p0_quarantine.jsonl`;
- `data/audit/.sorabji_p0_transaction.json`;
- `data/audit/.sorabji_p0_transaction_backups`.

## 10. Portée du PASS

Ce PASS signifie que le tuple v4 est cohérent, borné, reproductible et transactionnel, sans blocker P0 identifié par cette revue. Il ne ferme pas les deux issues savantes, ne rend pas les evidence units citables, et ne remplace pas la recollation des sources antiques, l'adversarial review ou le human signoff encore requis.

Décision: **PASS - NO APPLY PERFORMED**.

Toute modification ultérieure d'un fichier du tuple, du preview ou de la base exige un nouveau contrôle des préconditions. L'application reste une action séparée qui requiert l'autorisation explicite de root.
