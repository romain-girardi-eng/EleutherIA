# Revue indépendante Sorabji P0 v2

Date: 2026-08-24  
Portée: revue indépendante, adversariale et en lecture seule des données proposées par `scripts/apply_2026_08_24_sorabji_p0_repair.py`. Aucun `--write` n'a été exécuté. Aucun fichier KG, corpus, registre, manifeste, BibTeX ou audit data n'a été modifié.  
Autorité visuelle: `data/literature_acquisition/sorabji_1980_necessity_cause_blame.pdf`.  
OCR: navigation seulement.  
Verdict: **FAIL - NO APPLY**.

## 1. Périmètre exact et empreintes revues

| Artefact | SHA-256 contrôlé |
|---|---|
| Script P0 v2 | `d05332a7e870107821e1178c940dfc0468ffd256682f0fe8be8895b3a20c794c` |
| Tests P0 v2 | `db246d29c96c9c1d1ff5d696c09d2cf482395f65d42fad54f03e4c754d195d87` |
| Rapport FAIL v1 | `59bd36d9ebe64994a9921cc4961da12d659a82d45888652ce8d0c3e666094e3b` |
| Preview `/tmp/sorabji-v2-final.json` | `1d2fe3c894152ddc33b5b2c62f755d029dafeb1fd8194e9c7663c9955920b8` |
| Scan Sorabji | `be1f8fce483503d04504c73da30dc9bbcd52f5f8c04bd0e520cbd42fd4a3d500` |
| Dérivé OCR | `022e9c6440f7a5e43f89c72205795165853ae85b97389b167027a3bf0e38b007` |

Le dry-run produit par le script portant l'empreinte `d05332a7e870107821e1178c940dfc0468ffd256682f0fe8be8895b3a20c794c` est byte-identique au preview `/tmp/sorabji-v2-final.json`. Le présent verdict ne s'applique qu'à ces empreintes. Toute correction du script, des tests ou du preview exige une nouvelle revue. Lors du contrôle de clôture, le worktree contenait déjà une version intermédiaire non revue du script portant l'empreinte `3e5c30f51ebb0e96f829c7bb3027d52a7ba99b3db38d6d2761607fea97586681`; aucune conclusion du présent rapport ne s'étend à cette version ni à la future v3.

## 2. Verdict des huit blockers v1

| Blocker v1 | Résultat v2 | Verdict |
|---|---|---|
| Huit stratégies réellement séparées | huit entrées numérotées 1 à 8, avec Cléanthe et Chrysippe séparés | PASS |
| Citabilité runtime des neuf noeuds interprétatifs | `metadata.citability=discoverable_only` et policy runtime réelle contrôlée | PASS |
| Descriptions publiques, champs hérités et références actives | descriptions réécrites; booléens génériques et `verified_reference` retirés ou typés; dog-cart nettoyé | PASS |
| Manifestation 1980/1983 et tirage local | objet intellectuel 1980; première édition Cornell paperback 1983; tirage local inconnu | PASS |
| Rollback, journal et reprise après panne | matériel durable conservé si le rollback échoue; second recovery vérifié | PASS |
| Registry fail-closed et absence de revues inventées | auditeur ad hoc et reviews bornées corrects, mais le preview accroît la dette du schéma normatif | **FAIL** |
| E2 rights et exposition | `internal_audit_only`, `unverified_do_not_republish`, aucun consommateur runtime actif | PASS |
| BibTeX reproductible et before-image | bloc Sorabji canonique et before-image présents, mais le rapport BibTeX compagnon devient plus périmé | **FAIL** |

Six familles sont donc corrigées. Deux blockers P0 subsistent.

## 3. Relecture visuelle indépendante

Les pages suivantes ont été rendues depuis le scan source et relues pour cette v2:

| Objet | Pages imprimées | Pages PDF | Résultat |
|---|---:|---:|---|
| Couverture Cornell Paperbacks | sans folio | 1 | PASS |
| Titre Cornell | sans folio | 4 | PASS |
| Copyright, première publication et ISBN | sans folio | 5 | PASS |
| Dog-cart et nécessité stoïcienne | 70 | 87 | PASS |
| Annonce des huit tentatives | 71 | 88 | PASS |
| Stratégies 1 et 2 | 72 | 89 | PASS |
| Stratégie 3 | 72-74 | 89-91 | PASS |
| Stratégie 4 | 74-78 | 91-95 | PASS |
| Stratégie 5 | 78-79 | 95-96 | PASS |
| Stratégie 6 et trois lectures du cylindre | 79-83 | 96-100 | PASS |
| Stratégie 7 | 83-84 | 100-101 | PASS |
| Stratégie 8 et résumé | 84-85 | 101-102 | PASS |
| Quatrième Cornell Paperbacks | sans folio | 344 | PASS |

La séquence imprimée confirme bien huit tentatives distinctes. La première répond au Maître Argument par Cléanthe; la deuxième par Chrysippe. La sixième est le dossier des causes internes et externes, avec trois interprétations modernes distinguées. Le résumé p. 85 conclut que les tentatives stoïciennes n'échappent pas à la nécessité.

La page de copyright établit une première publication Cornell en 1980 et une première édition Cornell Paperbacks en 1983. Les couvertures identifient la famille paperback, mais aucun numéro d'impression ne permet de dater le tirage local. Le preview `year_original=1980`, `year_edition_used=1983`, `local_printing_year=null` est donc correct.

## 4. Familles corrigées: preuves de PASS

### 4.1 Huit stratégies

`EIGHT_STRATEGIES` contient huit éléments distincts, préfixés exactement `1:` à `8:`. `validate_eight_strategies` impose la cardinalité et l'ordre. `verification_records` refuse de produire le review concerné si la liste retombe à sept éléments. Le test adversarial remplace la liste par sept entrées et obtient l'échec attendu.

Verdict: **PASS**.

### 4.2 Citabilité runtime

Les neuf IDs suivants ont été passés à la policy runtime réelle de `graphrag/src/eleutheria_graphrag/agents/citability.py`:

- `scholarly_position_sorabji_aristotle_indeterminist`
- `argument_chrysippus_causal_taxonomy`
- `argument_cylinder_analogy_chrysippus_k1l2m3n4`
- `concept_cylinder_analogy_chrysippus_e5f6g7h8`
- `argument_the_dog_and_cart_argument_9ba60714`
- `argument_the_master_argument_kurieuon_logos_355f4d3f`
- `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6`
- `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7`
- `debate_stoic_compatibilism`

Pour les neuf, le marqueur est `citability=discoverable_only` et la décision runtime est `DISCOVERABLE_ONLY`. Les noeuds personne et publication restent bibliographiquement citables.

Verdict: **PASS**.

### 4.3 Descriptions et dog-cart

Les descriptions publiques de `concept_eph_hemin...` et `debate_stoic_compatibilism` sont désormais attribuées et signalent explicitement la dispute. Les onze noeuds touchés ne conservent aucun booléen générique `verified` ou `citation_verified`, ni aucun `verified_reference` actif.

Pour dog-cart:

- le témoin reste candidat et en attente de recollation d'Hippolyte;
- Cléanthe n'est plus présenté comme formulator du dog-cart;
- `modus_tollens` est remplacé par `analogy`;
- `targets`, `legacy_premises`, le faux locus primaire et la référence vérifiée active disparaissent;
- le raisonnement porte sur consentement ou résistance sous un résultat nécessaire, sans alternative démontrée;
- l'évaluation de validité est suspendue jusqu'à recollation primaire.

Verdict: **PASS**.

### 4.4 Manifestations et année 1983

Le noeud publication sépare l'objet intellectuel et les manifestations Duckworth 1980, Cornell 1980, première édition Cornell paperback 1983 et Chicago 2006. Le publisher, le lieu et l'ISBN ne restent pas au niveau abstrait. Le scholarly manifest emploie 1983 pour l'édition effectivement représentée et conserve le tirage local comme inconnu.

Verdict: **PASS**.

### 4.5 Transaction et hard-crash recovery

La correction du rollback v1 est réelle. `transactional_replace` ne nettoie journal et backups qu'après une restauration complète. Si une restauration échoue, le journal et les before-images survivent. Un second `recover_transaction` restaure ensuite les bytes initiaux.

Les tests couvrent:

- dérive avant commit sans écrasement du writer concurrent;
- `BaseException` après premier remplacement;
- échec de remplacement pendant commit;
- échec de fsync;
- échec du rollback suivi d'une seconde reprise;
- journal `committing` partiellement appliqué;
- journal `prepared` avec dérive externe;
- journal `committed` avec nettoyage interrompu;
- stage orphelin avant journal.

Verdict: **PASS**.

### 4.6 E2 rights et source 1980/2017

Le preview E2 ajoute:

- `runtime_exposure=internal_audit_only`;
- `reuse_status=unverified_do_not_republish`;
- `legacy_quotes_status=retained_in_place_not_duplicated`.

Les neuf longs champs historiques restent en place mais ne sont recopiés ni dans la quarantine ni dans les nouvelles evidence units. Une recherche indépendante dans `backend`, `frontend/src`, `graphrag/src` et `knowledge graph/src` n'a trouvé aucun consommateur actif de `e2_patches` ou du fichier Sorabji.

La relation explicite Cicéron-Lucrèce reste rattachée au work Sorabji 2017; Sorabji 1980 n'est plus que le background page-mapped. Les cinq arêtes 2017 restent byte-identiques.

Verdict: **PASS**.

## 5. Blocker résiduel 1: croissance de dette du schéma registry

Le script valide le preview avec `scripts/audit_sota_registry.py`, mais cet auditeur ne fait pas respecter `additionalProperties: false` du fichier normatif `data/goals/sota/registry.schema.json`.

Une validation Draft 7 des mêmes records contre les sous-schémas normatifs donne:

| Type | Erreurs avant | Erreurs après preview | Nouvelle dette |
|---|---:|---:|---:|
| source | 4 | 6 | +2 |
| evidence | 6 | 13 | +7 |
| issue | 2 | 7 | +5 |
| wave | 0 | 1 | +1 |
| **Total** | **12** | **27** | **+15** |

Les quinze erreurs nouvelles viennent uniquement de la proposition Sorabji:

1. `src_sec_sorabji_1980_necessity` ajoute un stamp top-level interdit et trois propriétés interdites dans `acquisition`: `fingerprint_status`, `visual_page_map_status`, `verification_scope`.
2. Les sept evidence units Sorabji ajoutent chacune le stamp top-level `sorabji_p0_2026_08_24`, non déclaré dans le schéma.
3. Les deux issues ajoutent chacune ce stamp top-level. L'artefact du FAIL initial ajoute aussi `verdict`; l'artefact E2 ajoute `notes`. Ces propriétés ne sont pas permises dans un `artifact`.
4. La wave ajoute le même stamp top-level interdit.

Le fait que le registry possède déjà douze erreurs normatives n'autorise pas une croissance. Le preview crée quinze erreurs supplémentaires tout en annonçant zéro nouvelle dette. Ce résultat est fail-open parce que la métrique utilisée n'observe pas le schéma normatif.

### Correctif requis

- Retirer les stamps top-level des records registry. L'idempotence peut reposer sur les hashes AFTER et l'égalité du record désiré.
- Conserver dans `acquisition` uniquement `status`, `manifest_publication_dirs` et `artifacts`; déplacer les qualifications supplémentaires dans le champ `notes` autorisé du source record.
- Retirer `verdict` et `notes` des objets artefacts. Le verdict du rapport initial peut être porté par le résumé ou les critères de résolution de l'issue.
- Ajouter un test comparant la dette normative avant/après et exigeant zéro nouvelle erreur de schéma.
- Si l'intention est d'étendre le schéma, cette extension doit être explicite, revue et testée dans la même transaction; elle ne peut pas être simulée par un auditeur plus permissif.

Verdict blocker registry: **FAIL P0**.

## 6. Blocker résiduel 2: rapport BibTeX compagnon périmé

Le bloc Sorabji lui-même est maintenant reproductible:

- il est produit par `publication_entries_to_bibtex`;
- quatre entrées concrètes ont toutes un publisher et une année;
- l'ancien bloc est remplacé chirurgicalement;
- la quarantine conserve exactement `bib_entry_before` et son hash.

Mais `data/kg/publications_bibtex_report.json` reste hors touched-set.

Mesure indépendante:

| Etat | Entrées réelles dans `publications.bib` | `entries_written` dans le report | Ecart |
|---|---:|---:|---:|
| Avant | 540 | 538 | 2 |
| Preview Sorabji | 543 | 538 | 5 |

La transaction ajoute donc trois entrées réelles sans mettre à jour le rapport compagnon. Elle accroît de trois une dette générée existante.

Le problème n'est pas que l'ensemble de `publications.bib` soit actuellement régénérable byte pour byte: des corrections manuelles Bobzien/Carter empêchent cette hypothèse. Le problème est que la transaction revendique une réparation BibTeX canonique tout en laissant son rapport déterministe trois unités plus faux.

### Correctif requis

Deux solutions sont admissibles:

1. Ajouter `data/kg/publications_bibtex_report.json` au touched-set, calculer son état désiré depuis les noeuds previewés avec l'exporteur canonique, préserver son before-image et vérifier que les comptes et la liste `missing` sont reproductibles; ou
2. Conserver une seule entrée bibliographique tant qu'une transaction globale du couple BibTeX/report n'est pas autorisée, et stocker les autres manifestations uniquement dans le noeud publication.

Un test doit au minimum imposer que la différence `nombre réel d'entrées BibTeX - entries_written` ne croisse pas. Le meilleur gate impose l'égalité.

Verdict blocker BibTeX/report: **FAIL P0**.

## 7. Registry reviews et absence de PASS inventé

Indépendamment du défaut de schéma, la sémantique de revue est correctement fail-closed:

- les sept evidence units restent `in_review`;
- les quotations nouvelles sont `paraphrase_only`;
- les deux issues restent `open` et bloquent la wave;
- huit verifications seulement sont créées: une `identity`, sept `primary`;
- les notes bornent les PASS aux pages et au texte secondaire de Sorabji;
- aucun stage `independent`, `adversarial` ou `human_signoff` n'est inventé;
- le FAIL indépendant v1 reste attaché et la v2 n'est pas présentée comme un PASS.

Ce sous-contrôle est **PASS**, mais il ne compense pas la croissance de dette normative du registry.

## 8. Commandes exécutées sans écriture de données

### Dry-run et concordance du preview

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/apply_2026_08_24_sorabji_p0_repair.py --json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/apply_2026_08_24_sorabji_p0_repair.py --json | cmp -s - /tmp/sorabji-v2-final.json
```

Résultat: code 0; preview identique byte pour byte; `write_performed=false`.

### Tests ciblés

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider \
  tests/test_sorabji_p0_repair.py \
  tests/test_export_publications_bibtex.py \
  tests/test_audit_sota_registry.py \
  tests/test_scholarly_sources_manifest.py
```

Résultat: **37 passed**, un warning de configuration pytest sans effet sur les assertions.

### PDF

```text
qpdf --check data/literature_acquisition/sorabji_1980_necessity_cause_blame.pdf
qpdf --check data/literature_acquisition/sorabji_1980_necessity_cause_blame_ocr.pdf
```

Résultat: aucun défaut de syntaxe ou d'encodage de flux détecté.

### Registry actuel

```text
python3 scripts/audit_sota_registry.py --format json
```

Résultat avant application: `structurally_valid=true`, `exit_ready=false`, aucune erreur de l'auditeur ad hoc.

### Contrôles adversariaux supplémentaires

- policy runtime réelle sur les neuf noeuds: neuf décisions `discoverable_only`;
- validation normative du registry avant/après: quinze erreurs nouvelles;
- nombre d'entrées BibTeX avant/après contre le report: écart 2 puis 5;
- recherche runtime `e2_patches|sorabji.json`: zéro consommateur actif;
- neuf champs E2 historiques: 5 900 caractères, environ 960 mots, non dupliqués.

## 9. Conclusion exécutable

La v2 corrige les six principaux défauts savants, runtime, bibliographiques et transactionnels de la proposition initiale. Le contenu Sorabji est prudemment attribué, les neuf noeuds interprétatifs sont réellement non citables comme preuve, le dog-cart est nettoyé, l'édition paperback 1983 est correctement distinguée, E2 est internal-only et le rollback est durable.

L'application reste néanmoins interdite. Le preview accroît la dette du schéma normatif du registry de quinze erreurs et accroît de trois l'écart entre le BibTeX et son rapport compagnon.

Décision: **FAIL - NO APPLY**.

Après correction de ces deux blockers, une nouvelle revue indépendante v3 devra contrôler de nouveaux hashes. Le présent rapport ne constitue ni un review PASS, ni une autorisation de `--write`, ni une verification des sources antiques, ni un adversarial/human signoff.
