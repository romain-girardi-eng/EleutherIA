# Re-review indépendante et contradictoire du candidat P0 Alexander-Sharples v2

Date: 2026-08-24  
Réviseur: agent `/root/aristotle_en_manifest_gap`  
Groupe d'indépendance: `alexander_sharples_global_p0_independent_v2_20260824`  
Portée: vérification du tuple v2 contre le FAIL v1, sans écriture sur les données live.

## Verdict signé

- Verdict sémantique: **PASS**.
- Verdict transactionnel: **PASS** sur la base gelée pré-Hildebrandt.
- Applicabilité sur la racine actuelle: **FAIL - BASE STALE - NO APPLY UNTIL REBASE**.

Signature: `alexander_sharples_global_p0_independent_v2_20260824:SEMANTIC_PASS:TRANSACTION_PASS:BASE_STALE_NO_APPLY`.

Le tuple v2 corrige les trois familles de blockers du rapport v1. Il ne peut toutefois plus être appliqué tel quel, car Hildebrandt v2 a été appliqué entre-temps sur huit de ses douze surfaces gelées. Le refus live est exact et fail-closed; un rebase final doit préserver les deltas Hildebrandt et produire de nouveaux hashes before/after, un nouveau JSON et une revue finale bornée.

## Tuple v2 contrôlé

| Artefact | SHA-256 |
|---|---|
| applier | `9a611ddecfb1c2e31782954c1174bd3b40e752ac124553bc5607269270f961e5` |
| tests ciblés | `14a3d460063b4bab425f8aecc62ebb3e63f1e123b0e8b6ed8d8f08bd30e9eab1` |
| audit savant corrigé | `7c1fbfcbabb5904c0a35818c5927c8f92913b05feaaf75fe19bbd9ad415efce0` |
| preview Markdown v2 | `fdba937bc972c84c2f49a7b6a88ad6ba68fcb0879e55107b9621fd0cd2d32b76` |
| JSON dry-run v2 | `07b37b03d10dca1b1b75e7f3312860b98f70ffe51978ed5aaaef0d21a34b1cae` |

Le FAIL v1 de référence est
`docs/academic/2026-08-24-alexander-sharples-global-p0-independent-review.md`,
SHA-256 `44d55137e40aafc86ba7f0007313a1b049e9d2005cd1167727d423bc76296858`.

## 1. Page maps - PASS

La source visuelle et la règle vérifiée restent:

```text
PDF = floor(page imprimée / 2) + 5
```

Les cinq erreurs v1 sont corrigées ensemble dans l'audit, les specs, les evidence units et les hashes:

| Record | Imprimé | PDF v2 exact |
|---|---:|---:|
| SHA-01 | 19-21 | 14-15 |
| SHA-06 | 146-149 | 78-79 |
| SHA-09 | 146-149 | 78-79 |
| SHA-12 | 152-153 | 81 |
| couche traduction de `argument_deliberation_alex` | 56-60 | 33-35 |

Les rendus indépendants établissent notamment:

- PDF 32 = imprimé 54-55;
- PDF 33 = imprimé 56-57;
- PDF 34 = imprimé 58-59;
- PDF 35 = imprimé 60-61;
- PDF 78 = imprimé 146-147;
- PDF 79 = imprimé 148-149;
- PDF 80 = imprimé 150-151;
- PDF 81 = imprimé 152-153.

`validate_page_maps()` dérive et contrôle 14 intervalles evidence et 24 intervalles argument. Le test ne compare plus deux constantes recopiées: il recalcule chaque plage depuis la règle.

Verdict pagination: **PASS**.

## 2. Sémantique et provenance - PASS

Le scope savant reste celui validé en v1:

- 15 noeuds modifiés, exactement;
- 11 reconstructions fortes `discoverable_only`;
- 55 arêtes de grounding fort supprimées, 1 arête publication/work corrigée;
- 31 citations rétrogradées vers `related_passage_non_exact`;
- 2 faux snapshots De fato 15 supprimés;
- publication Sharples typée traduction/commentaire avec fac-similé photographique Bruns;
- source ancienne Bruns/OGL et source secondaire Sharples séparées;
- 14 evidence units `in_review`, paraphrase-only;
- 2 issues OPEN et aucun PASS indépendant, adversarial ou humain fabriqué.

`argument_agent_causation_alex` et les six noeuds Sorabji/Long sont byte-identiques. Aucun agent ultime, non causé ou substance-cause n'est exposé comme texte direct d'Alexandre.

Les corrections de page n'ont changé aucune conclusion savante; seul le hash after de `argument_deliberation_alex`, le registre evidence, l'audit et les rapports dérivés changent par rapport au v1.

Verdict sémantique/provenance: **PASS**.

## 3. Snapshot-A et gates - PASS sur la base gelée

Le v2 gèle douze surfaces:

1. nodes;
2. edges;
3. citations;
4. corpus passages, read-only;
5. corpus manifest, read-only;
6. BibTeX;
7. rapport BibTeX;
8. manifeste savant;
9. registry sources;
10. registry evidence;
11. registry issues;
12. wave Sharples dédiée, absente before.

Les dépendances corpus conservent:

- `passages.jsonl`: `4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec`;
- `manifest.jsonl`: `aa4d446f32b5d47d4fb3d002dec3b49398862f8f3f8515b6076655ea8e414cd6`.

Elles sont contrôlées à pre-stage et pre-commit sans devenir des outputs. Chaque `build_plan()`, before comme after, exécute:

- corpus invariant no-growth;
- snapshot no-new-fingerprint;
- locus parity;
- work-child canonical;
- work-ID uniqueness;
- strict ingestion delta;
- audit structurel du registre.

Reproduction indépendante sur une reconstruction byte-exacte de la base pré-Hildebrandt:

```text
status = ready_for_independent_review_no_apply
page-map = 14 evidence + 24 argument intervals
new snapshot fingerprints = 0
new corpus violations = 0
parity shared checked = 13841
parity violations = 0
work-child mismatches = 0
work-ID collisions = 0
```

Le JSON reconstruit est byte-identique au JSON v2 gelé, SHA-256
`07b37b03d10dca1b1b75e7f3312860b98f70ffe51978ed5aaaef0d21a34b1cae`.

Verdict Snapshot-A/gates: **PASS** sur la base revue.

## 4. Transaction, foreign drift et postwrite - PASS

La transaction contrôle désormais l'état de chaque cible immédiatement avant son remplacement. Au rollback, chaque cible est classée `before`, `after` ou `foreign`.

- Les bytes foreign ne sont jamais écrasés.
- Si une dérive étrangère apparaît entre deux remplacements, le premier remplacement et les bytes étrangers sont conservés, ainsi que le journal et les backups pour récupération explicite.
- La dérive d'une dépendance corpus read-only abort avant commit et reste intacte.
- Hard crash, échec de replace/fsync, échec de rollback et seconde récupération sont exercés.

Une application intégrale sur la copie pré-Hildebrandt a été rejouée pendant cette revue:

```text
SHADOW_APPLY = PASS
second build_plan = already_applied
counts = {}
input_state = after
quarantine records = 126
journal/backups après succès = absents
```

Les douze hashes after correspondent au preview. Le postvalidate rejoue les gates d'intégrité.

La suite est branchée before/after et réutilise la quarantaine persistée pour rejouer les transformations principales après application. Le contrat CLI est aligné: dry-run par défaut, `--write` local revu, double flag obligatoire sur la racine.

Verdict transaction/postwrite/CLI: **PASS**.

## 5. Vérifications reproduites

Avant l'application Hildebrandt, le tuple v2 exact a produit:

```text
tests/test_alexander_sharples_global_p0.py: 25 passed
tests Alexander local 12/20 + Long/Sedley: 28 passed
ruff: PASS
```

La présente re-review a en plus:

- recalculé les cinq page maps visuellement et par formule;
- reconstruit les douze bytes before depuis la quarantaine Hildebrandt;
- reproduit le JSON v2 byte pour byte;
- appliqué le plan sur copie;
- vérifié l'état after, les gates et l'idempotence;
- confirmé l'absence de tout artefact transactionnel Sharples sur la racine live.

## 6. Base live stale après Hildebrandt

Le dry-run v2 sur la racine actuelle retourne correctement:

```text
status = blocked_precondition_failed
write_performed = false
```

Artefact du contrôle stale:
`/tmp/sharples-v2-post-hilde-stale-check.json`, SHA-256
`80e769f9543b5b004246b9da066e6e48c59ce886ff523f792d9a846a5b3b48e3`.

Hildebrandt a légitimement changé neuf surfaces Sharples gelées:

- nodes;
- edges;
- citations;
- BibTeX;
- rapport BibTeX;
- manifeste savant;
- registry sources;
- registry evidence;
- registry issues.

Corpus passages, corpus manifest et wave Sharples restent inchangés/absente.

Le guard refuse aussi bien les anciens hashes before que les hashes after Sharples; aucune écriture n'est possible sans rebase. C'est le comportement attendu.

## 7. Rebase final requis

Le rebase doit:

1. prendre les hashes post-Hildebrandt comme nouveau before;
2. préserver byte pour byte tous les records Hildebrandt hors touched-set Sharples;
3. recalculer les dix outputs Sharples et les douze hashes after/read-only;
4. régénérer le rapport BibTeX sans perdre l'entrée Hildebrandt;
5. conserver la manifestation et les records registry Hildebrandt;
6. relancer page maps, gates, transaction, tests before/after et ruff;
7. produire un nouveau JSON et un nouveau preview Markdown;
8. recevoir une dernière revue indépendante hash-bornée.

Jusqu'à ce rebase: **NO APPLY, NO DEPLOY**.
