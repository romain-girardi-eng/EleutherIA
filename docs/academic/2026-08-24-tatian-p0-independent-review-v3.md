# Revue indépendante et adversariale du P0 Tatien - v3

Date: 2026-08-24  
Portée: re-revue contradictoire en lecture seule du tuple v3; aucune mutation du
KG, du corpus, des registres, des manifestes ou des artefacts du candidat. Les
simulations transactionnelles ont utilisé exclusivement des copies temporaires.  
Verdict global: **PASS - NO APPLY PERFORMED**.

Le tuple v3 ferme les trois blockers du rapport v2. L'evidence 15.9 est alignée
sur l'unique bloc TEI exact `seg n=26`, les deux flags génériques de vérification
person/work ont disparu, et le rollback refuse désormais d'écraser des bytes
étrangers. Les dettes savantes et le sign-off humain restent explicitement
ouverts; ce PASS n'affirme ni consensus ni validation humaine.

## 1. Tuple gelé effectivement revu

| Artefact | SHA-256 attendu et constaté |
|---|---|
| `scripts/apply_2026_08_24_tatian_p0_repair.py` | `11e8545f44101aa6889e7f9ec4f27ce3d61ed49ff4d0f930a44c659fb6ddceba` |
| `tests/test_tatian_p0_repair.py` | `aa35018beaa3c5819e1ffa9148b5f58c79939264edf75e9962254120d4943316` |
| `tests/fixtures/tatian_otto1851_release_1.1.32401591783.json` | `3c3234a87671514c2a6a70c6908df07a82c361f9305a0e17a2a37a4b12d0f1b6` |
| `/tmp/2026-08-24-tatian-p0-v3-preview.json` | `456fab8196f6ab462ef5db6f95d2190cd74f724d81e755eed07b84dbd1ce8fb7` |

Le FAIL v2 contrôlé est
`docs/academic/2026-08-24-tatian-p0-independent-review-v2.md`, SHA-256
`303f9bd876c6645625071d0eb06a664106d3c0d46e80ed28cb4900eb7f7ce731`.

Les neuf surfaces live correspondent encore exactement au Snapshot-A before:

```text
nodes              57fb90da476ebdf98bc59f4a0cb4bad0c4871d5d829c0dc05063b4752b6c8664
edges              22efd267ac194d67d23ffd9985d2c68d93e1cfb4129e1a91cc3fda4871fadd70
passages           4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec
citations          3fa555efad53ad2795f04fb28959442e42630b4f33187c1c7a1b78890af0d248
manifest           aa4d446f32b5d47d4fb3d002dec3b49398862f8f3f8515b6076655ea8e414cd6
registry sources   ceba6d9e9ec188d943abdd345f0149dca017b70a82404f7d858774f812bcd650
registry evidence  41683cdb6df1b826dbc625853c08a3fcd66c0579a7ca96883c5e326ecd82cbe7
registry issues    1aa809df5ebfc5f81d31963ce84fa37ab7563a4d61d9007fc7009399819a130a
registry wave      4b9cfecc1c3075900e681c56af5ef0278dc8d19ba66150f0b562cd58712a7bee
```

Les report/quarantine/transaction/lock Tatien de production sont absents.

## 2. Autorité OGL/Scaife et contrôle visuel SAPERE

Le TEI officiel épinglé a de nouveau été utilisé directement au dry-run:

- release `1.1.32401591783`;
- objet de tag annoté `1c0e443edec985b9834db888b21d73cde35315ec`;
- commit pelé `78f9df37d694a9e0e92de2963f2fa8852e49efb6`;
- TEI SHA-256
  `bfe1671160c9155552055a24bd86345d2efb5392cd03e70a947d4a7a9ce00e4a`;
- CTS oeuvre SHA-256
  `df7b14a2b0db327787fea20a6a659104808f87a07e8c9017fec0e7a5775579d8`;
- version `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1`, Otto 1851,
  licence CC BY-SA 4.0;
- exactement 42 chapitres.

Les chapitres complets 7, 8 et 11 restent identiques au contrôle block-aware
v2:

| Chapitre | Longueur | SHA-256 NFC/collapse-whitespace |
|---:|---:|---|
| 7 | 1 625 | `10d5f5de95045e8c9754a2c431cbfa14042a72b1f87b6fa9ab277f5079c3b4fd` |
| 8 | 2 686 | `9194a6ddb13cec8fcf74d4d20392688a5787d1aff18c29872a738205e10bdb6f` |
| 11 | 1 369 | `65be1c120ed652dfc6e6bc4d0d94a86bd23d32fb76b12821d411c64ddaaffd20` |

Le PDF SAPERE local, SHA-256
`33f355b55cb446273498b2557022e52c3e83a1f75aea84ec136eb31ea5aea4db`,
reste un artefact sous copyright employé uniquement pour pagination, collation
et paraphrase attribuée. Le locus 15.9 est visuellement présent à la page
imprimée 66 / PDF 77. Aucun long texte SAPERE n'est ajouté.

## 3. Blocker v2-A fermé: evidence 15.9 sur le bloc exact

Une extraction indépendante du chapitre TEI 15 donne:

| `seg n` | Longueur | SHA-256 | Marqueur 15.9 |
|---:|---:|---|---|
| 24 | 751 | `a25f6608a4c94e539509c1285ce35bc2a2156fcd6c9be54d7cf948e4a590b632` | absent |
| 25 | 1 027 | `af5f5ae665296ccb76d770eca61b49dc2e6d1d4d23f1ad4aa0d64814783d5937` | absent |
| 26 | 436 | `c1c7d081eb9fed87d936019df642d1b6bdbae222eed64a7e6ad855d0ce6e6730` | présent |

Le marqueur `θανάτου νόμους` apparaît dans l'unique `seg n=26`. Le fixture
enregistre exactement chapitre 15, segment 26, hash `c1c7...e6730` et marqueur;
`load_authority(..., authority_xml=...)` vérifie les quatre propriétés contre le
TEI frais.

Le record projeté `ev_anc_tatian_orat_15_9_demonic_law` est maintenant sûr:

- `quotation.text_sha256=c1c7...e6730`;
- aucun `quotation.corpus_passage_ids`;
- cible de découverte bornée au work `work_tatian_oratio`;
- locator Otto/Perseus explicitement `exact TEI seg n=26`;
- note explicite que le corpus chapitre 15 ne contient que le premier segment
  `n=24` et n'est pas relié à cette preuve;
- `claim_status=in_review` et vérifications indépendante/adversariale encore
  requises.

Le faux lien v2 vers l'UUID/nœud 15.1 a donc entièrement disparu sans étendre le
corpus dans cette vague.

## 4. Blocker v2-B fermé: flags publics correctement typés

Les metadata projetées de `person_tatian` et `work_tatian_oratio` ne contiennent
plus ni `citation_verified` ni `verified_reference`.

Elles portent seulement des statuts bornés:

```text
person: citation_verdict=identity_checked_mixed_granularity_claims_in_review
        claim_review_status=...independent_adversarial_human_review_pending
work:   citation_verdict=work_identity_checked_mixed_granularity_claims_in_review
        claim_review_status=partial_corpus_..._review_pending
```

Les deux arguments conservent `citation_verified=false` et la vraie policy
runtime les classe `DISCOVERABLE_ONLY`. Les trois traductions machine sont
`BLOCKED`, la synthèse 8-9 est `DISCOVERABLE_ONLY` et les trois nœuds grecs
exacts sont `CITABLE`.

Aucun record de verification n'est transigé. L'issue critique reste OPEN, les
huit evidence records restent `in_review`, et le rapport projeté déclare
explicitement qu'aucun PASS indépendant, adversarial ou humain n'est asserté.

## 5. Blocker v2-C fermé: foreign drift préservé et recovery durable

La restauration préflight désormais toutes les cibles. Un fichier qui ne
correspond ni au before-hash ni à l'after-hash provoque:

- conservation byte-for-byte de la cible étrangère;
- journal durable en état `recovery_blocked_foreign_drift`;
- conservation du répertoire de backups;
- refus identique lors d'une seconde tentative de recovery;
- aucune fausse suppression du matériel transactionnel.

Simulation indépendante sur copie:

```text
first_error=RuntimeError: Tatian foreign drift blocks rollback
foreign_preserved=true
journal_state=recovery_blocked_foreign_drift
backup_material=true
repeat_recovery=blocked; foreign_preserved=true
operator_restores_expected_before_bytes
recovery=partial_commit_rolled_back
transaction_exists=false
snapshot_restored=true
```

Les scénarios fournis couvrent aussi crash dur, replace failure, fsync failure,
rollback failure avec seconde récupération, prepared, committed, orphan stage,
Snapshot-A drift et idempotence sur copie.

## 6. Portée exacte, output hashes et quarantine

Le rapport et le touched-set du preview gelé sont exactement reproductibles.
Les onze chemins projetés sont:

| Chemin | SHA-256 projeté |
|---|---|
| `audit/2026-08-24_tatian_p0_quarantine.jsonl` | `d23a389533f13e1d38e75d402598a16105ac99d55acc78b98dd81f362d675461` |
| `audit/2026-08-24_tatian_p0_repair.json` | `5196eda83a0f8a96aea71e7706682d006e856968940b90a0cbccc64a15434765` |
| `corpus/citations.jsonl` | `1c8cc71b9535a5917a7a7b0927bf2fb7034c01ab9e4dedf11f3fe15859d7643f` |
| `corpus/manifest.jsonl` | `2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e` |
| `corpus/passages.jsonl` | `e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3` |
| registry evidence | `7088f9256ffb25cb8b7fb4bd0118cf185ac2289b7bb03adba09faa9fee8bf687` |
| registry issues | `c89f35906bfa71ed6cb51d93c5d9ea14b55d5243a339e9e65254600528057c37` |
| registry sources | `bcee36664cd70d2dcc9d819684ec6c67dddf5ad8e224e35189f0fbf23b1d3dd2` |
| registry wave | `541458784dc8ff6f04d7e19e0aa93a65af9918b4b49826bfb841ba540f646bae` |
| `kg/edges.jsonl` | `e7d6569898a4b8f882ae342f5abb4ff6e216eea93bce4eb9fcdc03014d0519f5` |
| `kg/nodes.jsonl` | `fb67ec7a546da72a08243e8246660d952ce049d1185c3610befad845ad726dae` |

Les changements de records restent exactement:

- nodes: 1 ajout, 16 modifications;
- edges: 2 ajouts, 11 modifications, 7 suppressions;
- passages: 42 metadata enrichies, mais seuls les textes 7/8/11 changent;
- citations: 2 ajouts, 2 modifications, 4 suppressions;
- manifest: 1 modification;
- registry: 2 sources ajoutées + 1 modifiée, 7 evidence ajoutées + 1
  modifiée, 1 issue ajoutée et 1 wave modifiée.

Les sept arêtes supprimées sont inchangées par rapport au v2:

```text
1d8e8b3b-8ce5-4f31-8188-99132eab9138
3d77ec6c-0c99-4523-b86e-fdb48785f536
78428983-9305-49f6-81d2-a848e5ff8f05
8cb6fd24-023e-4199-af8b-a4f823589cce
origen-lit-005
reading-a-124
reading-a-127
```

Toutes les lignes JSONL hors changed-record set restent byte-identiques. Les 101
before-images ont des hashes valides et la même distribution contrôlée: 42
passages, 18 arêtes existantes, 16 nœuds existants, 6 citations existantes et
les absences/records registry, manifest, node, edge et citation attendus.

La manifestation garde trois chapitres complets et 39 premiers segments. Les 42
snapshots restent bijectifs, sans nœud machine ni synthèse.

## 7. Registre normatif et gates globaux

Validation Draft7 indépendante contre le vrai
`data/goals/sota/registry.schema.json`:

```text
baseline errors       41
preview errors        41
new errors             0
removed errors         0
touched records       13
touched record errors  0
```

Le dry-run officiel rapporte aussi zéro nouveau fingerprint snapshot, zéro
violation corpus, zéro violation de parité, zéro mismatch work-child et zéro
collision work-ID. Le registre custom est structurellement valide.

## 8. Commandes et résultats

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q \
  tests/test_tatian_p0_repair.py
40 passed

PYTHONDONTWRITEBYTECODE=1 python3 \
  scripts/apply_2026_08_24_tatian_p0_repair.py \
  --dry-run --data-root data \
  --authority-xml /tmp/tatian-otto-1851-release-1.1.32401591783.xml
exit 0; state planned; authority full_tei_verified; quarantine 101

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q \
  tests/test_zero_debt_gates.py \
  tests/test_snapshot_passage_integrity.py \
  tests/test_check_kg_corpus_locus_parity.py \
  tests/test_check_kg_work_child_canonical.py \
  tests/test_audit_sota_registry.py
26 passed

ruff check scripts/apply_2026_08_24_tatian_p0_repair.py \
  tests/test_tatian_p0_repair.py
PASS
```

## 9. Dettes explicitement maintenues

Ce PASS ne ferme pas les dettes suivantes:

- 39 lignes de corpus restent des premiers segments, pas des chapitres complets;
- la collation exhaustive des variantes d'édition reste incomplète;
- aucune traduction humaine autorisée n'est enregistrée;
- les interprétations secondaires restent `in_review`;
- le sign-off humain reste pending.

## 10. Verdict exécutable

**PASS - NO APPLY PERFORMED.** Le tuple v3 satisfait les gates P0 examinés et
peut être remis à root pour décision d'application. Ce rapport ne réalise ni
n'autorise lui-même aucun write, aucun déploiement et aucune clôture des issues
savantes.

Aucun byte de données live n'a été modifié pendant cette revue.
