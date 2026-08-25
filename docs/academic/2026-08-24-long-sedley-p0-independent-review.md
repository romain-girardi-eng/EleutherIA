# Revue indépendante et adversariale du candidat P0 Long-Sedley volume 2

Date: 2026-08-24  
Portée: revue indépendante, visuelle et adversariale du candidat seulement. Aucune donnée du KG, du corpus, des manifestes ou du registre n'a été appliquée ou réécrite pendant cette revue.

## Verdict

**PASS indépendant et adversarial, limité au tuple hashé ci-dessous.**

Le candidat est admissible à une application contrôlée par le mainteneur. Ce PASS ne ferme aucun des trois nouveaux issues, ne transforme aucun témoin antique en preuve primaire recollée, ne vérifie pas la thèse de priorité d'Épicure et ne vaut pas sign-off humain. Toute modification d'un composant du tuple, d'une précondition Snapshot-A ou du PDF annule ce verdict et exige une nouvelle revue.

Bloqueur d'application trouvé: **aucun**.

## Tuple revu

| Artefact | SHA-256 contrôlé |
|---|---|
| `scripts/apply_2026_08_24_long_sedley_vol2_p0_repair.py` | `326b9c5070301eb315f74b6fe7f141d880d5e7346c005053ae8267d16fa58f0c` |
| `tests/test_long_sedley_vol2_p0_repair.py` | `9f6c9e277394e105364b0c0d9782403f4056cddefe44577a3dc35e43795d7380` |
| `/tmp/long-sedley-vol2-p0-final.json` | `865a44fb696e7f568cba577f142af2203e286043cbd8285095a3ac14189c403b` |
| `docs/academic/2026-08-24-long-sedley-volume2-pdf-audit.md` | `accfa4129672f0ae80a35f08ff4d315f2b3df306f7f2ef8124dda3da2392579c` |
| PDF local volume 2 | `af6fc6f55d30f1896d59e2898e989016043990a498f8ff8cd5e8850bbb5e84a8` |

Le dry-run indépendant frais a reproduit l'artefact JSON gelé byte pour byte, avec le même SHA-256 `865a44...403b`.

## Contrôle visuel indépendant du PDF

Le fichier de 24 371 131 octets comporte 520 pages, 520 images raster, n'est ni chiffré ni balisé et passe `qpdf --check`. Son MD5 est `d8c95fb77d88c968463786dbe3cb6dfa`.

Les pages rendues ont été lues visuellement, sans prendre l'OCR pour autorité:

- PDF 1: titre d'ensemble, volume 2, sous-titre *Greek and Latin texts with notes and bibliography*, A. A. Long, D. N. Sedley, Cambridge University Press;
- PDF 2: copyright Cambridge University Press 1987, première publication 1987, réimpression 1988, première édition paperback 1989, réimpressions 1992, 1995 et 1998, ISBN hardback `0-521-25562-7`, ISBN paperback `0-521-27557-1`;
- PDF 7-8: le volume 2 est explicitement auxiliaire des traductions et commentaires du volume 1; il fournit les originaux, notes et apparat sélectif;
- PDF 112-121, soit imprimé 104-113: section 20 complète;
- PDF 340-349, soit imprimé 332-341: section 55 complète;
- PDF 390-397, soit imprimé 382-389: section 62 complète;
- PDF 497, soit imprimé 489: bibliographie de la section 20, avec Sedley [260] pour la réfutation du déterminisme et Huby [262] pour l'importance historique d'Épicure.

La manifestation est correctement décrite comme portant une ligne de réimpression jusqu'en 1998, sans inférer reliure ni tirage exact. Dans le manifeste savant candidat, `year_edition_used=1998` n'est acceptable qu'avec les champs simultanés `local_printing_year=null`, `local_printing_status=reprint_line_through_1998_exact_printing_unknown` et `binding_status=unknown_cover_absent`; il ne doit jamais être relu comme preuve d'un exemplaire identifié avec certitude à la réimpression 1998.

Le droit d'auteur visible est celui de Cambridge University Press. Aucune licence de réutilisation n'est établie. Le candidat conserve `reuse_status=unverified_do_not_republish` et `quotation_policy=internal_pointers_and_paraphrases_only`.

## Labels LS et cibles KG

Les labels et plages utilisés par le candidat concordent avec les pages visibles:

| Unité | Locus visible | Page imprimée / PDF | Cible candidate |
|---|---|---|---|
| 20A | Épicure, *Ep. Men.* 133-134 | 104 / 112 | `passage_dl_lives_10_1_133`, `_134` |
| 20E | Cicéron, *De fato* 21-25 | 108-110 / 116-118 | `passage_cic_fat_21`, `_24`, `_25`, plus les `_22`, `_23` déjà présents |
| 55K | Aulu-Gelle 7.2.3 | 337 / 345 | `passage_gellius_na_vii_2_7_2_3` |
| 55N | Alexandre, *De fato* 191.30-192.28 | 338-339 / 346-347 | l'ancienne cible `passage_alex_fat_2` est retirée; aucune cible primaire nouvelle n'est inventée |
| 55S | Cicéron, *De fato* 28-30 | 340-341 / 348-349 | ajout de `passage_cic_fat_29`, avec `_28` et `_30` déjà présents |
| 62C | Cicéron, *De fato* 39-43 | 383-384 / 391-392 | les cinq cibles existantes sont conservées |
| 62D | Aulu-Gelle 7.2.6-13 | 384-385 / 392-393 | seuls les paragraphes 6-13 restent; 1-5 et 14-15 ne sont plus membres exacts |
| 62G | Alexandre, *De fato* 181.13-182.20 | 386-387 / 394-395 | `passage_alex_fat_13` existant conservé |

Après transformation, le sous-graphe `collection_ls` pour les préfixes 20, 55 et 62 ne contient que les correspondances exactes ci-dessus. Les unités non modélisées restent explicitement des pistes dans l'issue de recollation; aucun noeud SVF ou passage absent n'est créé par déduction.

## Touched-set du graphe

Le diff JSON et le diff brut concordent sur exactement 39 noeuds. Les autres lignes de `nodes.jsonl` sont byte-identiques.

Neuf noeuds de structure ou d'interprétation sont concernés:

- `scholarly_work_long_sedley_1987_hellenistic_philosophers`;
- `collection_ls`;
- `scholarly_position_long_sedley_epicurus_first_freewill`;
- `argument_chrysippus_causal_taxonomy`;
- `argument_cylinder_analogy_chrysippus_k1l2m3n4`;
- `concept_cylinder_analogy_chrysippus_e5f6g7h8`;
- `argument_the_dog_and_cart_argument_9ba60714`;
- `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6`;
- `debate_stoic_compatibilism`.

Trente noeuds de routage LS sont concernés:

- `passage_alex_fat_2`;
- `passage_cic_fat_12`, `_21`, `_24`, `_25`, `_29`, `_34`, `_39`, `_41`, `_42`, `_48`;
- `passage_dl_lives_10_1_129`, `_133`, `_134`;
- `passage_dl_lives_7_1_79`, `_82`, `_99`, `_104`, `_116`, `_121`, `_156`;
- `passage_gellius_na_vii_2_7_2_1`, `_2`, `_3`, `_4`, `_5`, `_6`, `_13`, `_14`, `_15`.

Pour ces trente noeuds de passage, tous les champs hors `metadata` et `updated_at` restent identiques, notamment identifiant, label, description et texte. Les corrections retirent seulement les faux sigles, ajoutent les sept correspondances exactes et enregistrent le statut `editorial_mapping_only_primary_recollation_pending`.

Les six noeuds interprétatifs existants et la position de priorité sont `citability=discoverable_only`. Les six portent `primary_source_status=ancient_loci_leads_not_primary_verified`; la position attribue la priorité au dossier volume 1/Huby encore à auditer et borne le clinamen à une condition au plus nécessaire, non suffisante ni cause directe démontrée de chaque volition. Aucun texte public des six noeuds partagés avec le repair Sorabji n'est réécrit.

## Arêtes

Le diff comporte exactement:

- 13 suppressions, toutes présentes dans la liste visuelle de faux membres exacts;
- 1 modification, `deepaudit-passage_gellius_na_vii_2_7_2_3-partof-collection_ls`, remappée de 62D vers 55K;
- 7 ajouts: six routages exacts manquants et `long-sedley-vol2-work-authored-by-sedley`.

Les six nouveaux routages sont:

- `passage_dl_lives_10_1_133` et `_134` vers 20A;
- `passage_cic_fat_21`, `_24`, `_25` vers 20E;
- `passage_cic_fat_29` vers 55S.

L'arête Sedley va du work vers `scholar_sedley_david` avec la relation directionnelle `authored_by`. Le work a donc exactement Long et Sedley comme auteurs. Aucun nouveau `created_by` n'est ajouté. La position de priorité conserve seulement son ancien `created_by` vers Long, car le volume 2 ne prouve pas une attribution conjointe de cette thèse à Sedley.

`ag_026_advanced_in` est byte-identique et garde le hash canonique `095a6da3d6c6f5d31306322e14d3b532cc667dff48d3401f7e1863909a2c62bf`; sa référence au volume 1 n'est ni validée ni réécrite par ce repair volume 2.

## Manifestes, builder et registre

Le diff du builder comporte un seul hunk, limité à l'entrée Long-Sedley: 5 lignes retirées, 19 ajoutées. L'exécution en mémoire du builder candidat régénère le manifeste d'acquisition et ne change qu'un seul `artifact_id`, `lit_long_sedley_1987_hellenistic_philosophers_vol2`. Tous les autres identifiants et objets du manifeste sont identiques.

La séparation est explicite:

- oeuvre abstraite en deux volumes;
- volume intellectuel 2 avec rôle original-language texts, notes, apparat et bibliographie;
- scan local de 520 pages, contenu savant principal complet de la page de titre à la bibliographie mais objet physique incomplet;
- ISBN `9780521275569` borné au paperback du volume 1;
- ISBN volume 2 `0521255627` hardback et `0521275571` paperback;
- carte du corps imprimé `PDF = printed + 8`.

Le manifeste savant reste `kg_ingestion_status=partial`. Les trois evidence units LS20, LS55 et LS62 restent `claim_status=in_review`, paraphrase-only et demandent encore revue indépendante, adversariale et recollation. Les trois nouveaux issues restent OPEN:

- `issue_long_sedley_vol2_local_manifestation_unknown_20260824`;
- `issue_long_sedley_first_freewill_priority_20260824`;
- `issue_long_sedley_ancient_loci_recollation_20260824`.

Le candidat ajoute quatre PASS réels et bornés de la première lecture visuelle: un stage `identity` et trois stages `primary` portant sur le sourcebook moderne. Aucun stage `independent`, `adversarial` ou `human_signoff` n'est fabriqué. Le terme `primary` dans ces quatre lignes désigne la première inspection du PDF Long-Sedley, pas une vérification primaire des textes antiques.

L'audit structurel complet du registre sur la copie candidate est vert. Le gate normatif conserve les 41 dettes préexistantes et n'en ajoute aucune: `baseline_errors=41`, `preview_errors=41`, `new_errors=0`, `touched_record_errors=0`. Le repair ne prétend donc pas que le registre global est exempt de dette normative.

## Immutabilité hors scope

Le dry-run frais a laissé les empreintes réelles inchangées. Les artefacts explicitement hors scope restent byte-identiques:

| Fichier | SHA-256 |
|---|---|
| `data/kg/publications.bib` | `2bf6ea54d93bb86249997a076e73dde025b8e765e1edcab59f641ad77c5f4dcc` |
| `data/kg/publications_bibtex_report.json` | `66355e056418b9c446a278e9d29b0119d60628504f73bc10af08d73d155b6f72` |
| `data/kg/e2_patches/cary.json` | `1fb574160b21f3b035dc29a818f4f0858664512a084ffc0b7834b255b001182e` |
| `data/kg/e2_patches/sorabji.json` | `d84f98c3bce2859cc5ec36b9ea5785f5aa92240a05bb902bb6b970261f84e660` |
| `data/corpus/passages.jsonl` | `4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec` |
| `data/corpus/citations.jsonl` | `3fa555efad53ad2795f04fb28959442e42630b4f33187c1c7a1b78890af0d248` |
| `data/corpus/manifest.jsonl` | `aa4d446f32b5d47d4fb3d002dec3b49398862f8f3f8515b6076655ea8e414cd6` |

L'export BibTeX canonique calculé avant/après à partir des noeuds reste identique. Cary conserve sa référence explicite au volume 1, p. 102-112; elle n'est pas remappée vers le PDF volume 2.

## Quarantaine et transaction

Les 77 enregistrements de quarantaine correspondent exactement au diff: 39 before-images de noeuds, 13 arêtes supprimées, 1 arête modifiée, 7 absences d'arêtes, les before-images ou absences des lignes de manifestes/registre, et un résumé hashé du bloc builder. La quarantaine ne copie aucune page du PDF, aucun extrait Long-Sedley, aucun corpus passage/citation, aucun patch E2 et aucun artefact BibTeX. Le builder y est représenté par ses hashes, pas par une copie intégrale.

Les tests sur copie établissent:

- Snapshot-A contrôlé avant staging et avant commit;
- stages et backups fsyncés;
- journal durable;
- rollback après abort injecté;
- reprise après échec de rollback;
- nettoyage des états prepared et committed;
- préservation d'un écrivain externe lors d'une dérive pré-commit;
- idempotence après application sur copie;
- second `--write` truthful en `already_applied` sans écriture;
- refus du mélange d'états before/after et des hashes non reconnus.

La dette `check_ingestion_rules` reste strictement identique avant/après: 1155 BLOCK et 768 WARN. Le candidat n'en crée aucune nouvelle.

## Commandes exécutées

```text
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_long_sedley_vol2_p0_repair.py
# 20 passed

PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/test_literature_acquisition_manifest.py \
  tests/test_scholarly_sources_manifest.py \
  tests/test_audit_sota_registry.py \
  tests/test_export_publications_bibtex.py
# 14 passed

PYTHONDONTWRITEBYTECODE=1 python \
  scripts/apply_2026_08_24_long_sedley_vol2_p0_repair.py --json
# dry-run, byte-identique au preview gelé, aucune écriture
```

Une passe-oracle indépendante, avec les ensembles attendus codés séparément du candidat, a confirmé 39 noeuds modifiés, 13 arêtes supprimées, 1 modifiée et 7 ajoutées, ainsi que l'absence de nouveaux `created_by`, la direction Sedley et les états fail-closed.

## Conditions du PASS

1. Appliquer uniquement le tuple hashé ci-dessus depuis le Snapshot-A gelé.
2. Ne pas promouvoir les claims Long-Sedley ou les témoins antiques après l'application.
3. Garder les trois issues OPEN et le wave bloqué jusqu'aux audits volume 1/Huby, recollations primaires et sign-off humain.
4. Refaire cette revue si un hash data, script, test, audit ou PDF dérive.
5. Ne pas interpréter ce document comme une autorisation de déploiement distant.

