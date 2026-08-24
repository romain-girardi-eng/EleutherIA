# Revue indépendante Hildebrandt P0

Date: 2026-08-24  
Portée: revue contradictoire, sans écriture de données, du preview Hildebrandt P0. Aucun `--write` n'a été exécuté. Aucun fichier KG, corpus, registre, manifeste, BibTeX ou audit data n'a été modifié.  
Verdict: **FAIL - NO APPLY**.

## 1. Tuple exact revu

| Artefact | SHA-256 contrôlé |
|---|---|
| Applier | `4c9b18b7382454ebc40763b850c93f507bc668692eac1ea309783fe5665efdc1` |
| Tests | `41b5c8162cfd2c4cc7bdadfa731d181cd341163d2ead958c85b162efaf83f28b` |
| Preview `/tmp/hildebrandt-p0-final.json` | `608339b2008f97ca201b0b40f0ab7c382f110afbc3ac8a449c565fd3d22a01d4` |
| PDF local | `3a632d61028344ffcba880cebdc6678cfaa22ba456956f55715279928c749717` |
| Audit savant | `e2b262453c105e17694d15742b5eec5dd8055263609de011d2f9812bf6477331` |

Le dry-run du script gelé est byte-identique au preview. Les trois hashes code/tests/preview sont restés identiques après la revue.

## 2. Verdict synthétique

| Gate | Résultat | Verdict |
|---|---|---|
| PDF officiel et intégrité | téléchargement officiel et fichier local: même hash et même taille | PASS |
| Auteur, titre, DOI et pages | Ronja Hildebrandt; titre exact; DOI; volume 15; pp. 25-44 | PASS |
| Droits | accès public séparé de la réutilisation; aucune licence explicite inférée | PASS |
| Contact et affiliations | contact supprimé du noeud public; affiliations datées comme contexte de publication | PASS |
| Surclaims | formulations comparatives, consensus et absence de réponse correctement bornés | PASS |
| Diff KG | exactement 10 nodes et 8 edges modifiés | PASS |
| Citations | exactement 4 citations modifiées; zéro passage corpus modifié | PASS |
| Touched-set | exactement 12 sorties planifiées | PASS |
| Manifeste acquisition et manifeste savant | identité corrigée et builder reproductible | PASS |
| BibTeX et report compagnon | 543 clés uniques; report exactement recomputable | PASS |
| Registry | `41 -> 41`, aucune erreur nouvelle, issues ouvertes | PASS |
| Reviews | aucune verification ou review indépendante/adversariale fictive | PASS |
| Transaction | Snapshot A, journal, rollback, second recovery et idempotence passent | PASS |
| Tests | 18 ciblés et 34 globaux passent | PASS |
| Ruff | trois erreurs statiques sur le tuple gelé | **FAIL** |

Le candidat est fonctionnellement et savamment bien borné. Il ne peut néanmoins pas recevoir un PASS exécutable tant que son propre gate statique échoue.

## 3. Autorité officielle et contrôle visuel

### 3.1 Identité officielle

La [notice officielle de Studia Philosophica Estonica](https://ojs.utlib.ee/index.php/spe/article/view/22849) affiche:

- auteur: Ronja Hildebrandt;
- titre: *Alexander of Aphrodisias' Lazy Arguments against Stoic Determinism*;
- DOI: `10.12697/spe.2022.15.01`;
- volume 15, année 2022, pages 25-44;
- publication le 31 décembre 2022;
- formulation centrale comparative: l'argument est présenté comme plus réussi que les autres, non comme démonstration conclusive.

Le PDF téléchargé depuis la route officielle `article/download/22849/17337` a exactement:

- SHA-256 `3a632d61028344ffcba880cebdc6678cfaa22ba456956f55715279928c749717`;
- 343,020 octets.

Il est donc byte-identique au fichier local audité. `qpdf --check` ne signale aucun défaut de syntaxe ou de flux. `pdfinfo` confirme 20 pages A4, PDF 1.6, non chiffré.

### 3.2 Contrôle visuel

Les 20 pages ont été rendues. Les PDF 1, 3, 6, 9, 13, 15, 17, 18 et 20 ont été inspectées à résolution originale pour les points décisifs:

- PDF 1 / p. 25: titre, byline Ronja, deux affiliations imprimées, résumé, contact dans l'article, DOI, ISSN et droits;
- PDF 3 / p. 27: début des objections ordinaires;
- PDF 6 / p. 30: échec des objections et début des versions traditionnelles;
- PDF 9 / p. 33: co-fatedness et renforcement par le cylindre;
- PDF 13 / p. 37: transition vers la nouvelle version du Lazy Argument;
- PDF 15 / p. 39: asymétrie pratique et agent rationnel moyen;
- PDF 17 / p. 41: extension Brennan et risque sous déterminisme vrai;
- PDF 18 / p. 42: absence bornée de réponse transmise, acknowledgements et période de visiting professor;
- PDF 20 / p. 44: fin continue de la bibliographie.

Le pied de page du PDF 1 porte `© All Copyright Author`. Ni le PDF ni la notice officielle visible ne fournissent un bloc de licence de réutilisation explicite. Le candidat a donc raison de conserver `access_status=open_access`, tout en imposant `license_status=no_explicit_reuse_licence_archived` et `reuse_status=unverified_do_not_republish`.

## 4. Identité, confidentialité et surclaims

### 4.1 Publication

Le noeud publication candidat distingue correctement le label UI et le titre intellectuel exact. Il conserve Ronja Hildebrandt, la revue, le volume, les pages, le DOI, l'ISSN, les 20 pages physiques et la règle `PDF page = printed page - 24`.

Le faux `license=OA` disparaît. Les champs génériques `citation_verified` et `verified_reference` sont retirés. La description attribue à Hildebrandt une comparaison de succès et un argument de risque; elle ne transforme ni l'un ni l'autre en consensus mesuré ou preuve conclusive.

Verdict: **PASS**.

### 4.2 Noeud scholar

Le texte public ne contient plus:

- l'adresse Emil-Figge-Straße;
- le code postal et la ville de contact;
- l'adresse électronique;
- l'identité erronée David Hildebrandt.

Les affiliations sont conservées comme faits imprimés en 2022. La période de visiting professor, novembre 2022 à septembre 2023, est explicitement datée et n'est pas présentée comme affiliation actuelle.

Verdict: **PASS**.

### 4.3 Huit positions

Les huit positions sont toutes:

- `claim_status=in_review`;
- `citability=discoverable_only` dans la policy runtime réelle;
- rattachées à la même publication, source et manifestation;
- page-mappées par pages imprimées et PDF;
- dépourvues de `quote_verbatim` et de faux champ `citation_verified`;
- dotées d'un rôle de preuve secondaire et de caveats de recollation primaire.

Les deux corrections sémantiques prioritaires sont réelles:

1. HIL-01 parle d'une version comparativement plus réussie, sans conclusion absolue ni consensus mesuré par EleutherIA.
2. HIL-09 dit qu'aucune réponse stoïcienne n'est identifiée dans la transmission examinée, sans conclure à une absence historique absolue.

Les extensions sur l'agent rationnel moyen et Brennan sont attribuées à Hildebrandt ou Brennan, non à Alexandre.

Verdict: **PASS**.

## 5. Diffs exacts et touched-set

### 5.1 Nodes

Le diff indépendant donne:

- ajout: `0`;
- suppression: `0`;
- modification JSON: exactement `10`;
- modification de ligne brute: les mêmes `10` IDs;
- toutes les lignes hors set: byte-identiques.

Le set est exactement la publication, le scholar et les huit positions annoncées. Les before et after record hashes correspondent au preview.

### 5.2 Edges

Le diff donne:

- ajout: `0`;
- suppression: `0`;
- modification: exactement les huit `AUTHOR_EDGE_IDS`;
- lignes hors set: byte-identiques.

Les huit arêtes deviennent `position authored_by Ronja Hildebrandt`. Leur metadata les borne comme positions savantes modernes `in_review` et `discoverable_only`; elles ne les convertissent pas en doctrines antiques.

### 5.3 Citations

Quatre citations seulement sont modifiées:

- deux routes Cicéron corrigent le témoin `phi054` et éliminent l'ancien `phi049`;
- De fato 8 reste une `discussion` avec corruption grecque ouverte;
- De fato 11 reste une `paraphrase` avec duplication finale ouverte.

Aucune citation n'est promue en preuve primaire directe. Les bytes de `data/corpus/passages.jsonl` et `data/corpus/manifest.jsonl` restent immuables.

### 5.4 Douze sorties

Les sorties sont exactement:

1. nodes;
2. edges;
3. citations;
4. builder du manifeste d'acquisition;
5. manifeste d'acquisition;
6. manifeste savant;
7. BibTeX;
8. report BibTeX;
9. registry sources;
10. registry evidence;
11. registry issues;
12. registry waves.

Les 12 hashes preview correspondent aux bytes recomputés. Le report annonce 41 records de quarantine, répartis exactement entre 10 nodes, 8 edges, 4 citations, 9 absences evidence, 2 issues, 2 waves, la source, les deux manifestes et le couple BibTeX/report.

Verdict touched-set: **PASS**.

## 6. Manifestes, BibTeX et registre

### 6.1 Manifeste d'acquisition

Le diff du builder touche seulement la curation Hildebrandt. Le builder candidat régénère byte pour byte le manifeste candidat. La seule ligne intellectuelle modifiée est `lit_hildebrandt_2022_alexander_lazy_arguments`.

La ligne corrige David en Ronja, restaure le titre, le DOI, la revue, le volume, les plages 25-44 et 1-20, la règle de page, l'accès, les droits prudents et le SHA-256.

Verdict: **PASS**.

### 6.2 Manifeste savant

La nouvelle manifestation `hildebrandt2022lazyarguments` est `partial`, page-mappée, hashée, paraphrase-only et explicitement en attente de revue indépendante et de recollation primaire. Elle ne prétend pas à une licence absente.

Verdict: **PASS**.

### 6.3 BibTeX et report

Mesure indépendante:

- baseline: 543 clés réelles et `entries_written=543`;
- candidat: 543 clés réelles, 543 uniques et `entries_written=543`;
- publication nodes: 540;
- records `missing`: 175;
- titre et auteur Hildebrandt: exacts;
- hash BibTeX candidat: `e4cc9a15bdbe756446518a09f9a97f9405c98a7b54886de39afc07892941c44a`;
- report candidat: exactement égal à une recomputation de `build_companion_report` avec le mode `hildebrandt_bibliography_surgical_snapshot_transform`.

Le couple BibTeX/report appartient à la même transaction et possède ses before-images.

Verdict: **PASS**.

### 6.4 Registry et reviews

La validation Draft 7 normative donne:

- baseline: 41 erreurs héritées;
- preview: 41;
- nouvelles: 0;
- erreurs sur records Hildebrandt touchés/ajoutés: 0.

Neuf evidence units restent `in_review`, `paraphrase_only` et requièrent encore independent/adversarial review. Deux issues restent ouvertes: revue/droits Hildebrandt, puis corruption De fato 8/11. Les deux waves conservent leurs états non conclusifs.

`verification_records_added=0`. Le résumé porte explicitement:

- `independent=not_performed_not_recorded`;
- `adversarial=not_performed_not_recorded`;
- `human_signoff=not_performed_not_recorded`.

Verdict registry/reviews: **PASS**.

## 7. Transaction et tests

Le plan possède 12 sorties. `apply_plan` ajoute report et quarantine: 14 cibles transactionnelles, exactement les 14 entrées Snapshot A. Le builder et le report BibTeX font partie de cette transaction.

Les tests couvrent:

- first write, dry-run appliqué et repeat write sur copie;
- reconstruction exacte de Snapshot A depuis la quarantine persistée;
- hard-abort après remplacement du report BibTeX;
- dérive pré-commit et préservation du writer externe;
- échec de rollback, conservation journal/backups et seconde récupération;
- idempotence postwrite;
- refus d'un write repository sans autorisation explicite.

Résultats exécutés:

```text
tests/test_hildebrandt_p0_repair.py: 18 passed
tests globaux associés: 34 passed
```

Un warning pytest signale seulement une option de configuration inconnue et n'affecte aucune assertion.

## 8. Blocker résiduel: ruff échoue

Commande:

```text
ruff check --no-cache \
  scripts/apply_2026_08_24_hildebrandt_p0_repair.py \
  tests/test_hildebrandt_p0_repair.py
```

Résultat: **FAIL**, trois erreurs:

1. `C420` dans l'applier, ligne 788: compréhension de dictionnaire remplaçable par `dict.fromkeys`;
2. `F401` dans les tests, ligne 3: import `copy` inutilisé;
3. `SIM300` dans les tests, ligne 471: comparaison de style Yoda.

Ces défauts ne changent pas les bytes du preview et ne révèlent pas une corruption savante ou transactionnelle. Ils empêchent toutefois de certifier que le tuple gelé passe ses gates de livraison. Une revue indépendante ne doit pas corriger silencieusement le code qu'elle juge.

### Correctif minimal requis

- remplacer la compréhension par `dict.fromkeys(POSITION_IDS, SCHOLAR_ID)`;
- supprimer l'import `copy` inutilisé;
- inverser la comparaison du test;
- relancer ruff, les 18 tests ciblés et les 34 tests globaux;
- regeler au minimum les hashes script/tests et confirmer que le preview JSON reste byte-identique, ou publier son nouveau hash s'il change.

## 9. Absence de write et conclusion

Les chemins Hildebrandt report, quarantine, journal et backups restent absents dans le dépôt réel. Les tests transactionnels ont écrit uniquement dans leurs copies temporaires. Les 12 fichiers data/code ciblés conservent leurs hashes Snapshot A.

Décision: **FAIL - NO APPLY**.

Le FAIL est strictement borné au tuple de la section 1 et au gate ruff. Tous les contrôles savants, bibliographiques, de portée, de registre, de droits et de transaction décrits ci-dessus sont PASS. Une v2 code-only peut être revue rapidement, mais exige de nouveaux hashes et ne doit pas être appliquée avant ce recontrôle.
