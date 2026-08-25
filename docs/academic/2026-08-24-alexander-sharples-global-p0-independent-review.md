# Revue indépendante et contradictoire du candidat P0 Alexander-Sharples global

Date: 2026-08-24  
Réviseur: agent `/root/aristotle_en_manifest_gap`  
Groupe d'indépendance: `alexander_sharples_global_p0_independent_20260824`  
Portée: lecture indépendante du PDF, audit du code, des deltas, des tests et de la transaction. Aucune donnée n'a été appliquée ou modifiée.

## Verdict signé

**FAIL - NO APPLY.**

Le coeur sémantique du repair est prudent et une grande partie du dispositif est solide, mais le tuple exact ne satisfait pas les gates P0 de pagination et de transaction. Toute application doit attendre un nouveau tuple, un nouveau preview et une nouvelle revue indépendante.

Signature de verdict: `alexander_sharples_global_p0_independent_20260824:FAIL_NO_APPLY`.

## Tuple contrôlé

| Artefact | SHA-256 |
|---|---|
| `scripts/apply_2026_08_24_alexander_sharples_global_p0.py` | `d56360266c0b13621047a6d470949c2d25dd93b34bb46a0ca4e9db9aaf050701` |
| `tests/test_alexander_sharples_global_p0.py` | `86341308f1e7038e4c16aeebe40eb8b7a8000eea9475a44ea16fdb96b4c141cf` |
| `docs/data-audit/2026-08-24-alexander-sharples-global-p0-preview.md` | `9cb9375b145536a8c181c18b75c28c522f633060f7bae0d5c2eaee6aa8d43798` |
| `/tmp/2026-08-24-alexander-sharples-global-p0-preview.json` | `60a35fcff302ca13e7d48f3a37f4237ddde23b2b9ea6cb8f4b45a4522446d0f7` |
| audit savant Sharples | `b540d7ef297c9b4d6bc876729f457e673e02aac5fc25ce04349ea0b9131afabe` |
| scan Sharples source | `7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638` |
| dérivé OCR | `ec154e4d3607f887299ac3faf6ec1853b0a4da117eaa464d70331d7c55727ebb` |
| TEI Bruns/OGL | `184b01f38061cfa00b276ed8d9580f3f842f564856851e4bcc124adcc2edbb2f` |

Le dry-run indépendant frais reproduit le JSON gelé byte pour byte avec SHA-256 `60a35f...d0f7`. Les hashes data sont restés inchangés.

## Contrôles qui passent

### Identité, matérialité et droits

La lecture visuelle fraîche confirme:

- couverture: *Alexander of Aphrodisias on Fate*, R. W. Sharples, Duckworth;
- page de titre: *Text, translation and commentary*;
- copyright: Gerald Duckworth & Co. Ltd., London, 1983;
- ISBN cased `0-7156-1589-0`, ISBN paper `0-7156-1739-7`;
- formule tous droits réservés, sans permission de republication;
- préface: traduction anglaise et commentaire, puis reproduction photographique de Bruns, les divergences de lecture étant signalées et traitées dans les notes textuelles;
- 161 pages PDF, de la couverture à la p. imprimée 310 et au verso final blanc.

Le candidat décrit donc correctement Sharples comme traduction/commentaire avec fac-similé Bruns et non comme nouvelle édition critique. Le scan et l'OCR sont séparés; le TEI Bruns/OGL reste l'artefact de la source ancienne.

### Prudence sémantique

Les onze reconstructions fortes deviennent `discoverable_only`, perdent leurs prémisses directes et séparent quatre couches:

- locus alexandrin candidat;
- position stoïcienne rapportée par un témoin hostile ou partiel;
- interprétation Sharples 1983;
- reconstruction moderne contestée.

Le noeud local `argument_agent_causation_alex` reste byte-identique et citable. Les six noeuds partagés Sorabji/Long restent byte-identiques. Les deux composites De fato 15 perdent leurs snapshots exacts; l'anglais machine devient bloqué.

La lecture visuelle des p. imprimées 8-24, 144-165 et 168-169 confirme les qualifications essentielles: vocabulaire moderne `libertarian`, témoin stoïcien hostile, dilemme causal non résolu, critique des arguments pratiques, régression du caractère et prescience seulement du pouvoir de choisir.

### Touched-set, provenance et reviews

Les deltas correspondent au preview:

- 15 noeuds modifiés;
- 55 arêtes de grounding fort supprimées;
- 1 arête publication/work corrigée;
- 31 citations `source_for` rétrogradées à `related_passage_non_exact`;
- 2 snapshots composites supprimés;
- manifestation savante Sharples distincte;
- source ancienne réduite au TEI Bruns/OGL dans `acquisition.artifacts`;
- source secondaire Sharples avec scan et OCR;
- 14 evidence units `in_review` et paraphrase-only;
- 2 issues OPEN et un wave bloqué;
- aucun PASS indépendant, adversarial ou humain ajouté.

Les cohortes gelées, les hashes de noeuds et les dix hashes de sortie correspondent au JSON. Le BibTeX et son rapport sont cohérents et reproductibles.

### Tests exécutés

```text
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_alexander_sharples_global_p0.py
# 20 passed

PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/test_alexander_agent_causation_recollation.py \
  tests/test_long_sedley_vol2_p0_repair.py
# 28 passed

ruff check scripts/apply_2026_08_24_alexander_sharples_global_p0.py \
  tests/test_alexander_sharples_global_p0.py
# All checks passed
```

Ces PASS ne compensent pas les blockers ci-dessous, car les tests encodent certains locateurs erronés comme valeurs attendues.

## Blocker 1 - locateurs PDF inexacts

Le candidat déclare comme règle vérifiée:

```text
PDF page = floor(printed page / 2) + 5
```

Les pages rendues confirment cette règle sur les folios concernés. Plusieurs evidence units ne la respectent pourtant pas:

| Evidence | Pages imprimées | PDF candidat | PDF exact |
|---|---:|---:|---:|
| `ev_sec_sharples_1983_sha01` | 19-21 | 14-16 | 14-15 |
| `ev_sec_sharples_1983_sha06` | 146-149 | 78-80 | 78-79 |
| `ev_sec_sharples_1983_sha09` | 146-149 | 78-80 | 78-79 |
| `ev_sec_sharples_1983_sha12` | 152-153 | 81-82 | 81 |

La couche Sharples de `argument_deliberation_alex` contient également:

```text
printed 56-60 -> PDF 32-34
```

alors que les rendus établissent:

- PDF 32 = imprimé 54-55;
- PDF 33 = imprimé 56-57;
- PDF 34 = imprimé 58-59;
- PDF 35 = imprimé 60-61.

La plage exacte est donc PDF 33-35. Ce n'est pas une simple préférence de forme: les enregistrements sont présentés comme page-mapped et `visually_verified`. Les ranges actuels incluent des spreads étrangers au claim et, pour la délibération, omettent la p. imprimée 60 tout en incluant 54-55.

Remédiation requise:

1. corriger l'audit source lorsque ses tables portent les mêmes erreurs;
2. corriger `ARGUMENT_SPECS` et `EVIDENCE_SPECS`;
3. recalculer hashes de noeuds, registre, preview et rapport;
4. ajouter un test générique qui dérive chaque intervalle PDF depuis la règle, au lieu de recopier deux constantes susceptibles d'être fausses ensemble.

## Blocker 2 - Snapshot-A ne couvre pas les dépendances corpus déclarées immuables

`build_plan()` définit les chemins `data/corpus/passages.jsonl` et `data/corpus/manifest.jsonl`, mais ne lit ni ne hashe leurs bytes dans `before_bytes`. La transaction `snapshot_gate()` ne contrôle que les fichiers de sortie.

Conséquences:

- une modification concurrente du corpus, y compris des loci 12/20, entre plan et commit ne provoque pas d'abort;
- `post_validate()` relance `build_plan()`, mais `measured_baseline()` ne relance pas les gates corpus/snapshot/parité/work-child/work-id;
- le test prospectif exécute ces gates une fois, hors de la transaction, et ne les rend pas invariants du commit.

Cela contredit le handoff qui demande l'immuabilité Long et 12/20 ainsi qu'une transaction fail-closed. Les noeuds Long et `argument_agent_causation_alex` sont protégés indirectement par le snapshot complet de `nodes.jsonl`, mais les passages corpus sous-jacents ne le sont pas.

Remédiation requise:

1. ajouter les hashes gelés de `passages.jsonl` et `manifest.jsonl`, ou les inclure comme dépendances read-only dans Snapshot-A;
2. vérifier ces dépendances à pre-stage et pre-commit;
3. relancer les gates corpus/snapshot/parité/work-child/work-id dans `post_validate()`;
4. ajouter un test de drift concurrent sur une dépendance corpus, pas seulement sur un fichier cible générique.

## Blocker 3 - suite non robuste après application et contrat `--write` contradictoire

La suite annonce accepter l'état appliqué, mais au moins deux tests supposent toujours l'état before:

- `test_source_fixture_hashes_and_post_long_snapshot_are_frozen` exige les hashes before de nodes/edges/citations;
- `test_citations_exactly_downgrade_31_remove_two_and_preserve_every_other_row` exige toujours une cohorte legacy de 33 citations.

Après une application réelle, ces assertions échoueraient alors même que `build_plan()` retournerait `already_applied`. La copie transactionnelle prouve l'idempotence de l'applier, pas la robustesse de la suite postwrite.

En outre, le docstring affirme que `--write` est intentionnellement indisponible jusqu'à une modification ultérieure du code, tandis que `main()` et `locked_write()` autorisent déjà `--write --production-write-approved`. Le mécanisme d'approbation est raisonnable, mais le contrat utilisateur doit dire exactement ce que le code permet.

Remédiation requise:

1. reconstruire Snapshot-A depuis les raw before-images persistées, ou brancher explicitement les assertions before/after;
2. conserver un vrai test de transformation, rollback et idempotence même lorsque les données live sont after;
3. aligner le docstring, le CLI et les messages de preview sur une seule politique d'écriture.

## Observations non bloquantes

- La limite terminale du fac-similé grec comporte des pages de séparation/blanches autour de 229-231; le candidat borne prudemment la règle aux folios arabes vérifiés. Les claims secondaires prioritaires ne dépendent pas de cette limite.
- `measured_baseline.registry` audite le registre live avant transformation; la validité du registre candidat est toutefois exercée par l'application sur copie et sa post-validation. Le futur rapport gagnerait à distinguer explicitement baseline et preview.
- Les before-images sémantiques sont présentes, mais les raw lines ne sont pas toutes persistées; une future suite postwrite gagnerait à les conserver pour reconstruire exactement Snapshot-A sans dupliquer les fichiers entiers.

## Condition de nouvelle revue

Un nouveau verdict exige un tuple complet rehashé comprenant au minimum:

- audit Sharples corrigé;
- applier corrigé;
- tests prospectifs et postwrite corrigés;
- preview Markdown corrigé;
- JSON dry-run corrigé;
- preuves que tous les hashes data live sont restés inchangés.

Jusqu'à ce nouveau tuple: **NO APPLY, NO DEPLOY**.

