# Revue indépendante et adversariale du P0 Tatien - v4 rebase

Date: 2026-08-24  
Portée: revue contradictoire en lecture seule du rebase post-Hildebrandt; aucune
mutation du KG, du corpus, des registres, des manifestes ou des artefacts du
candidat. Les tests transactionnels ont écrit uniquement dans des copies
temporaires.  
Verdict global: **PASS - NO APPLY PERFORMED**.

Le v4 conserve byte-for-byte la sélection sémantique approuvée en v3. Il rebase
Snapshot-A sur l'application Hildebrandt et recalcule la seule before-image
sémantiquement partagée, `wave_00_known_factual_blockers`. Aucun record
Hildebrandt, BibTeX/report, builder d'acquisition ou manifeste littérature/savant
n'entre dans les outputs Tatien.

## 1. Tuple gelé effectivement revu

| Artefact | SHA-256 attendu et constaté |
|---|---|
| `scripts/apply_2026_08_24_tatian_p0_repair.py` | `d3c1e4f0fd5829692bff23d318d0937ca021d6a987cbaae06e045b319e88cede` |
| `tests/test_tatian_p0_repair.py` | `29c5580b54152c775b8a47c07a8b22d139d1d6bc25c0f007b0ee40915a71167b` |
| fixture OGL/TEI | `3c3234a87671514c2a6a70c6908df07a82c361f9305a0e17a2a37a4b12d0f1b6` |
| `/tmp/2026-08-24-tatian-p0-v4-rebase-preview.json` | `bdd0211b69aa4fbd008b5a83022f2a3aa15cea64a12ad7def4857f2f19ed2f73` |

Le PASS v3 contrôlé est
`docs/academic/2026-08-24-tatian-p0-independent-review-v3.md`, SHA-256
`88446b45a065e4fafcf6a1ee2382d847faa28a380b5a050b9c4688b68c04db96`.

## 2. Snapshot-A post-Hildebrandt

Les neuf surfaces live concordent exactement avec les constantes v4:

```text
nodes              07adbfa2826e4c23a15f95dcae1504e1f2a0ac228433cee5835f1fe14b046e4d
edges              31ac588b16faacf6de7b6fd1d23d247e790c3bea1d3655a91dacea3cc8ccda2c
passages           4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec
citations          07f0ff46bc162fe69e86b7187f28653886e0bdcf3e863b0790e9f016b13c25ee
manifest           aa4d446f32b5d47d4fb3d002dec3b49398862f8f3f8515b6076655ea8e414cd6
registry sources   54b02bc1ce94680f18b8e22e92f6a2aa4a21f0dd48a71e9a9eac168d9fd80d1e
registry evidence  0d360b28689f260c00717462778a48c124d2992521a87165733df4044304f1e0
registry issues    e265e74f274d3d62cb1b411bfe939229d88682859a0554349c30658e50738818
registry waves     2cf060fc4aa38a0a6c7f17c01030c22e81e3e8b29cc4acb68989be9f1b432989
```

Le rapport Hildebrandt est présent et hash-gaté:

```text
data/audit/2026-08-24_hildebrandt_p0_repair.json
cb30674aff6f4a6012cbb4a6266b9d1b49138da615c14147837f29820dfec59c
```

Surfaces post-Hildebrandt explicitement gelées et exclues des outputs:

| Surface | SHA-256 |
|---|---|
| `data/kg/publications.bib` | `e4cc9a15bdbe756446518a09f9a97f9405c98a7b54886de39afc07892941c44a` |
| `data/kg/publications_bibtex_report.json` | `7612db557443d1c6c27507a130aa283a115e8a765075b297a7c019ef6104b68a` |
| `scripts/build_literature_acquisition_manifest.py` | `d6519cf1192db6ae3dccb5ebc25599c145f5c472b88e2da4d821c4761333f9f6` |
| `data/literature_acquisition/manifest.jsonl` | `e1a5c1bf0ed25615005c9cd3107f3be25235b535faa563e5fa847eb5e9522933` |
| `data/scholarly_sources/manifest.jsonl` | `33f304aee1a3882c75f47e212bae778e64c23da6cb9f39cda0790416f0c9e9b6` |
| quarantine Hildebrandt | `3f35c44a02a000db342097a274e50a0398b822c363fb13c59ce0a03a1cbb7714` |

## 3. Équivalence sémantique v3 → v4

Comparaison directe des deux previews gelés:

```text
selected payload                    byte-identical
record_diff_ids                     identical
record diffs hors registry_waves    identical
record digests hors registry_waves  identical
```

Les textes exacts 7/8/11, l'evidence 15.9 `seg n=26`, les flags person/work,
les arguments, les nœuds machine/synthèse, les sept suppressions d'arêtes et les
42 snapshots ont donc exactement la sémantique approuvée en v3.

La seule différence record-level légitime est la wave partagée:

| État | Canonical record hash |
|---|---|
| before post-Hildebrandt | `82c027aa24d32984b5bec52d6747f854ebbc5d11ff4713558aa338df04f9c0c3` |
| after Tatien projeté | `78f9f45e8e95fa827344459247fa80978173e320dd04e5aea947e499d734aac4` |

Le digest complet du diff wave est
`511757bd468c1a30cad138f6f5de095d63cd8df6f9e2ef74dfb9ae8a3ad0b0c7`,
égal à la constante gelée.

## 4. Autorité officielle et corrections v3 conservées

Le dry-run a lu le TEI officiel épinglé, SHA-256
`bfe1671160c9155552055a24bd86345d2efb5392cd03e70a947d4a7a9ce00e4a`,
et retourne `authority=full_tei_verified`.

Contrôles hérités et revalidés:

- chapitres complets 7, 8 et 11 block-aware exacts;
- 39 autres textes inchangés et honnêtement typés premiers segments;
- chapitre 15 `seg n=26`, hash
  `c1c7d081eb9fed87d936019df642d1b6bdbae222eed64a7e6ad855d0ce6e6730`,
  unique porteur du marqueur de 15.9;
- P06 sans lien vers l'UUID/nœud 15.1, cible work-level seulement;
- aucun `citation_verified`/`verified_reference` générique sur person/work;
- arguments `DISCOVERABLE_ONLY`, traductions machine `BLOCKED`, synthèse 8-9
  `DISCOVERABLE_ONLY`, trois nœuds grecs exacts `CITABLE`;
- issue critique OPEN, evidence `in_review`, aucun PASS humain/consensus inventé.

## 5. Portée exacte, outputs et quarantine

Le rapport et le touched-set recalculés sont exactement égaux au preview v4.
Les onze outputs sont:

| Chemin | SHA-256 projeté |
|---|---|
| `audit/2026-08-24_tatian_p0_quarantine.jsonl` | `906013db5a2201252e67e2ff5b13ca88af1419c21c970a1cdddb9c5ad89963c7` |
| `audit/2026-08-24_tatian_p0_repair.json` | `b832d77849e1de9a767457afd1cb773609adf58a3d0165d47a9489743f9ee98c` |
| `corpus/citations.jsonl` | `3aea9ad22b6fe42c78429ce68fbb041c57d532e530463a01b18353d7c11a9c64` |
| `corpus/manifest.jsonl` | `2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e` |
| `corpus/passages.jsonl` | `e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3` |
| registry evidence | `90aaa8fab0d4c5fbbb830b60f38d992514b6d5a512a0698397042cc090aa2307` |
| registry issues | `5dca524033ebe628d5d9cd3431ebeddd9e8830314e430440d057a22e73d8ef17` |
| registry sources | `cc34488366f86d56726e99c1113195f2e8c128f2f44f2b1535d0dabdcd8cf7ac` |
| registry waves | `6083cf65579d935441200440160d0a1d398a74c792c1b0bde869d65d9cf5db1c` |
| `kg/edges.jsonl` | `2e417ac429988f1df282fbb0576f34b51e327479d0043738b9cf073715de6b72` |
| `kg/nodes.jsonl` | `60082c52cddfa3e5441a2ae491af2d9c00c386f4f9ed8a8c4b836390a4e24f83` |

Les record IDs sont ceux du v3: 1 node ajouté/16 modifiés, 2 edges ajoutés/11
modifiés/7 supprimés, 42 passages enrichis, 2 citations ajoutées/2 modifiées/4
supprimées, 1 manifest modifié et les mêmes 13 records registry touchés.

La quarantine contient exactement 101 entrées. Ses before-images et absences
sont recalculées sur la base post-Hildebrandt; aucun record hors cohortes n'est
réécrit.

## 6. Schéma, snapshots et recovery

Validation normative Draft7 indépendante:

```text
baseline errors       41
preview errors        41
new errors             0
removed errors         0
touched records       13
touched record errors  0
```

Snapshot integrity passe de 5 950 à 5 941 violations héritées, sans nouveau
fingerprint. Corpus, parité, work-child et work-ID n'acquièrent aucune dette.

Simulation étrangère indépendante sur copie:

```text
foreign bytes preserved=true
journal state=recovery_blocked_foreign_drift
backups durable=true
repeat recovery blocked=true
operator restores expected bytes
recovery=partial_commit_rolled_back
transaction clean=true
Snapshot-A restored=true
```

## 7. Suites rejouées

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q \
  tests/test_tatian_p0_repair.py
41 passed

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q \
  tests/test_zero_debt_gates.py \
  tests/test_snapshot_passage_integrity.py \
  tests/test_check_kg_corpus_locus_parity.py \
  tests/test_check_kg_work_child_canonical.py \
  tests/test_audit_sota_registry.py
26 passed

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q \
  tests/test_check_corpus_invariants.py \
  tests/test_snapshot_passage_integrity.py \
  tests/test_check_kg_corpus_locus_parity.py \
  tests/test_check_kg_work_id_uniqueness.py \
  tests/test_derive_corpus_manifest.py \
  tests/test_literature_acquisition_manifest.py \
  tests/test_scholarly_sources_manifest.py \
  tests/test_audit_sota_registry.py \
  tests/test_export_publications_bibtex.py
32 passed

ruff check scripts/apply_2026_08_24_tatian_p0_repair.py \
  tests/test_tatian_p0_repair.py
PASS
```

## 8. Dettes maintenues OPEN

- 39 lignes restent des premiers segments, non des chapitres complets;
- collation exhaustive des variantes incomplète;
- aucune traduction humaine autorisée enregistrée;
- interprétations secondaires `in_review`;
- sign-off humain pending.

## 9. Verdict

**PASS - NO APPLY PERFORMED.** Le rebase post-Hildebrandt satisfait les gates
examinés et peut être remis à root pour décision d'application. Ce rapport ne
réalise ni n'autorise lui-même aucun write, aucun déploiement et aucune clôture
des issues savantes.

Aucun artefact Tatien de production n'a été créé pendant cette revue.
