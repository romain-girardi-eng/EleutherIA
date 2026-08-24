# Revue bornée des tests postwrite Tatien

Date: 2026-08-24  
Portée: delta test-only après application Tatien; aucune révision de l'applier,
du fixture, des données ou de la sémantique approuvée.  
Verdict: **PASS - NO DATA WRITE**.

## 1. Tuple et before-image du test

| Artefact | SHA-256 |
|---|---|
| applier inchangé | `d3c1e4f0fd5829692bff23d318d0937ca021d6a987cbaae06e045b319e88cede` |
| fixture inchangé | `3c3234a87671514c2a6a70c6908df07a82c361f9305a0e17a2a37a4b12d0f1b6` |
| test revu v4 | `29c5580b54152c775b8a47c07a8b22d139d1d6bc25c0f007b0ee40915a71167b` |
| test postwrite courant | `340149bdd25214c408d99ada40fe64178d73332587e95a7094b9179ef13ef1b6` |
| diff exact 29c558 -> 340149 | `fe8291a2b2274caa22b8d69646cdca93e2de7fd9438a82ee23e54ed9f97b3015` |

Before-image et patch reproduits:

```text
/tmp/test_tatian_p0_repair-29c5580b.py
/tmp/tatian-test-postwrite-29c5580b-to-340149bd.patch
```

Le patch a 229 lignes. Il ne modifie aucune assertion savante existante, aucun
expected ID, aucun digest, aucun hash after et aucun chemin d'output.

## 2. Delta exact

Le delta contient seulement:

1. séparation `LIVE_DATA` / `DATA`;
2. helper `_reconstruct_postwrite_snapshot_a()`;
3. fixture session autouse `_use_prospective_snapshot_a_postwrite()`;
4. redirection des anciens tests prospectifs vers une copie before reconstruite;
5. nouveau test `test_live_postwrite_is_exact_already_applied_noop`;
6. usage explicite de `LIVE_DATA` pour les symlinks read-only et le gate de
   production-write.

Les seules lignes anciennes remplacées hors ajout du test sont:

- `DATA = ROOT / "data"` devient `LIVE_DATA = ROOT / "data"; DATA = LIVE_DATA`;
- les sources symlinkées par `_link_unmodified_repo_inputs()` viennent toujours
  du live, même quand les inputs mutables prospectifs viennent de la copie;
- le test d'approbation production cible explicitement `LIVE_DATA`.

Il n'y a aucune suppression ou relaxation d'une assertion du tuple revu.

## 3. Reconstruction de Snapshot-A

Le helper:

- copie les neuf fichiers d'input et le sous-arbre SOTA live dans un répertoire
  pytest temporaire;
- lit les 101 entrées de la quarantine appliquée;
- rétablit les before-images `node`, `edge`, `passage`, `citation`, `manifest`,
  `source`, `evidence` et `wave`;
- retire les records dont la quarantine atteste l'absence before;
- ne touche jamais les fichiers live.

Le mapping des types est complet pour le plan Tatien:

| Surface | Before-image | Absence before |
|---|---|---|
| nodes | `kg_node_before` | `kg_node_absence_before` |
| edges | `kg_edge_before` | `kg_edge_absence_before` |
| passages | `corpus_passage_before` | aucune addition |
| citations | `corpus_citation_before` | `corpus_citation_absence_before` |
| manifest | `corpus_manifest_before` | aucune addition |
| registry sources | `registry_source_before` | `registry_source_absence_before` |
| registry evidence | `registry_evidence_before` | `registry_evidence_absence_before` |
| registry issues | aucun record modifié | `registry_issue_absence_before` |
| registry wave | `registry_wave_before` | aucune addition |

La reconstruction ne prétend pas retrouver l'ordre byte-exact de lignes
supprimées puis réinsérées. Pour cette raison seulement, la fixture substitue
temporairement dans le module de test les neuf hashes whole-file before par les
hashes de la copie reconstruite. Cette substitution:

- reste confinée au processus pytest;
- est restaurée en `finally`;
- ne modifie pas `INPUT_AFTER_SHA256`;
- ne modifie pas les before/after hashes canoniques de records;
- ne modifie pas `EXPECTED_RECORD_DIFF_IDS` ni
  `EXPECTED_RECORD_DIFF_DIGESTS`;
- ne modifie pas les onze chemins permis.

Ce n'est donc pas un assouplissement du contrat de production. L'applier sur
disque conserve les constantes revues.

## 4. Gates prospectifs toujours stricts

Sur la copie reconstruite, les tests réexercent notamment:

- identité et hash du fixture;
- TEI block-aware et segment exact 15.9;
- 3 chapitres complets / 39 premiers segments;
- bijection des 42 snapshots;
- vraie policy runtime;
- variantes Otto/SAPERE séparées;
- arguments atomisés et reviews OPEN;
- 7 suppressions d'arêtes;
- exact changed-record IDs;
- exact record-diff digests;
- bytes des lignes hors touched-set;
- onze output paths et les neuf `INPUT_AFTER_SHA256`;
- inventaire et hashes des 101 before-images;
- schéma normatif 41 -> 41 sans dette nouvelle;
- transaction idempotente sur copie;
- Snapshot-A drift, hard crash, replace failure, fsync failure, rollback failure,
  foreign drift durable, prepared/committed/orphan recovery.

Les assertions critiques restent littéralement présentes:

```text
result.validation["record_diff_ids"] == EXPECTED_RECORD_DIFF_IDS
result.validation["record_diff_digests"] == EXPECTED_RECORD_DIFF_DIGESTS
set(outputs relative paths) == EXPECTED_OUTPUT_RELATIVES
sha256(output[label]) == INPUT_AFTER_SHA256[label]
len(quarantine) == 101
```

## 5. État live postwrite

Avant et après la suite, les neuf fichiers live correspondent exactement à
`INPUT_AFTER_SHA256`:

```text
nodes              60082c52cddfa3e5441a2ae491af2d9c00c386f4f9ed8a8c4b836390a4e24f83
edges              2e417ac429988f1df282fbb0576f34b51e327479d0043738b9cf073715de6b72
passages           e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3
citations          3aea9ad22b6fe42c78429ce68fbb041c57d532e530463a01b18353d7c11a9c64
manifest           2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e
registry sources   cc34488366f86d56726e99c1113195f2e8c128f2f44f2b1535d0dabdcd8cf7ac
registry evidence  90aaa8fab0d4c5fbbb830b60f38d992514b6d5a512a0698397042cc090aa2307
registry issues    5dca524033ebe628d5d9cd3431ebeddd9e8830314e430440d057a22e73d8ef17
registry waves     6083cf65579d935441200440160d0a1d398a74c792c1b0bde869d65d9cf5db1c
```

Le nouveau test live prouve:

- `transform(...).mode == already_applied`;
- `changes == {}`;
- `quarantine == []`;
- `build_outputs(...) == {}`;
- report/quarantine existants valides;
- CLI dry-run affiche `already_applied`, `changes: {}` et n'écrit rien;
- 101 records dans la quarantine persistée;
- aucune transaction pendante.

Artefacts persistés inchangés:

```text
repair report  b832d77849e1de9a767457afd1cb773609adf58a3d0165d47a9489743f9ee98c
quarantine     906013db5a2201252e67e2ff5b13ca88af1419c21c970a1cdddb9c5ad89963c7
```

## 6. Exécution

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q \
  tests/test_tatian_p0_repair.py
42 passed

ruff check tests/test_tatian_p0_repair.py
PASS
```

Après la suite:

```text
live hashes == INPUT_AFTER_SHA256  true
repair report unchanged            true
quarantine unchanged               true
transaction exists                 false
lock exists                        false
```

## 7. Limite de portée

Le nouveau test live est intentionnellement postwrite: sur une base before, il
n'aurait pas vocation à prouver `already_applied`. Les 41 anciens tests restent
rejouables sur before; la présente suite de 42 est le contrat de régression de
l'état appliqué demandé dans cette vague.

## 8. Verdict

**PASS - NO DATA WRITE.** Le delta test-only ne relâche aucun invariant revu. Il
ajoute une preuve effective de l'état live appliqué et conserve la totalité des
tests prospectifs/rollback grâce à une reconstruction temporaire depuis les
before-images persistées.
