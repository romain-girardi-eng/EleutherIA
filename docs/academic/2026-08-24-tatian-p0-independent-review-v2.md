# Revue indépendante et adversariale du P0 Tatien - v2

Date: 2026-08-24  
Portée: revue contradictoire en lecture seule du successeur v2; aucune mutation du
KG, du corpus, des registres, des manifestes ou des artefacts du candidat. Les
seules écritures de diagnostic ont eu lieu dans des répertoires temporaires.  
Verdict global: **FAIL - NO APPLY**.

Le v2 corrige les cinq blockers documentés dans la revue v1 au niveau des gates
annoncés. Trois blockers résiduels apparaissent toutefois sous ces gates: un
evidence atom 15.9 est relié au mauvais segment TEI, deux noeuds publics touchés
conservent un booléen de vérification générique vrai, et le rollback écrase une
dérive concurrente détectée entre deux remplacements.

## 1. Tuple v2 effectivement revu

Le tuple gelé transmis a été vérifié au début puis à la fin de la revue:

| Artefact | SHA-256 attendu et constaté |
|---|---|
| `scripts/apply_2026_08_24_tatian_p0_repair.py` | `9d3db316befcf8e37581464bb183467bcf53c502a67527ce9a968d1de537c553` |
| `tests/test_tatian_p0_repair.py` | `ddfe4c44e89642cb12ce2b9172caea38423a9ae00cbbca55ae40bfb93aaa5f63` |
| `tests/fixtures/tatian_otto1851_release_1.1.32401591783.json` | `3b42d40eea45a71b72e7dad495336c1dcdefc56ae652a84e116a5898b02e6657` |
| `/tmp/2026-08-24-tatian-p0-v2-preview.json` | `d0ab19fb54e0638e74bbf70ef6295c2c4f42c6ebfc9232c20d23343597a3590d` |

La revue v1 contre laquelle le correctif a été contrôlé est
`docs/academic/2026-08-24-tatian-p0-independent-review.md`, SHA-256
`701f3ded7724dd39dc528d5aa3b50f820882b864f711cbcdbc7e55fa82829a3f`.
Le rapport savant courant est
`docs/academic/2026-08-24-tatian-sapere28-pdf-audit.md`, SHA-256
`8952855ac632d2b6ad935293e71fe5f9d5a59e3ed017ea1652097844eb018024`.

Snapshot-A correspond exactement à la base post-Sorabji et post-Long fournie:

- `nodes.jsonl`: `57fb90da476ebdf98bc59f4a0cb4bad0c4871d5d829c0dc05063b4752b6c8664`;
- `edges.jsonl`: `22efd267ac194d67d23ffd9985d2c68d93e1cfb4129e1a91cc3fda4871fadd70`;
- les neuf surfaces mutables correspondent toutes aux hashes `snapshot_a_sha256`
  du preview.

## 2. Autorité OGL/Scaife et preuve visuelle SAPERE

Le contrôle a été refait depuis les endpoints officiels, sans prendre le fixture
comme autorité suffisante:

- le tag annoté `1.1.32401591783` résout vers l'objet
  `1c0e443edec985b9834db888b21d73cde35315ec` et le commit pelé
  `78f9df37d694a9e0e92de2963f2fa8852e49efb6`;
- le TEI officiel frais contient 150 510 octets et a le SHA-256
  `bfe1671160c9155552055a24bd86345d2efb5392cd03e70a947d4a7a9ce00e4a`;
- le CTS de l'oeuvre a le SHA-256
  `df7b14a2b0db327787fea20a6a659104808f87a07e8c9017fec0e7a5775579d8`;
- le CTS auteur a le SHA-256
  `65050ac3fb4abe4c73f89eacac3b177a1edba1843049e34561c4cbf2c5e1f995`;
- l'identité est Tatien, *Oratio ad Graecos*, Otto, Jena, Mauke, 1851,
  `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1`, licence CC BY-SA 4.0;
- le TEI contient exactement 42 divisions de chapitre.

Le PDF SAPERE local a de nouveau été contrôlé visuellement, jamais utilisé comme
manifestation Otto:

- SHA-256 `33f355b55cb446273498b2557022e52c3e83a1f75aea84ec136eb31ea5aea4db`;
- 3 063 004 octets, 345 pages, Mohr Siebeck 2016, droits réservés;
- règle de pagination `PDF = imprimée + 11` confirmée;
- loci contrôlés aux PDF 59 (7.2-7.3), 61 (8.1), 63 (9.3), 67-69
  (11.4) et 77 (15.9);
- pages secondaires contrôlées aux PDF 244-245 (Strutwolf/Lakmann) et
  289-292 (Timotin).

Les nouveaux records ne republient pas de longue traduction ou citation du
volume SAPERE.

## 3. Blocker v1-A fermé: jointure TEI block-aware exacte

Une extraction indépendante a normalisé chaque `seg` numéroté séparément, puis
joint les blocs par un espace ASCII. Le résultat concorde byte-for-byte avec le
fixture v2 et avec le dry-run:

| Chapitre | Blocs TEI | Longueur | SHA-256 NFC/collapse-whitespace |
|---:|---:|---:|---|
| 7 | 2 | 1 625 | `10d5f5de95045e8c9754a2c431cbfa14042a72b1f87b6fa9ab277f5079c3b4fd` |
| 8 | 5 | 2 686 | `9194a6ddb13cec8fcf74d4d20392688a5787d1aff18c29872a738205e10bdb6f` |
| 11 | 2 | 1 369 | `65be1c120ed652dfc6e6bc4d0d94a86bd23d32fb76b12821d411c64ddaaffd20` |

Les quatre frontières anciennement fusionnées sont corrigées: une au chapitre
7, deux au chapitre 8 et une au chapitre 11. Les blocs inline (`milestone`,
`pb`, `lb`) conservent leurs tails documentaires; aucun espace n'est inventé à
l'intérieur d'un bloc. Le fixture est désormais hash-gaté par l'applier et le
TEI officiel intégral produit `authority_mode=full_tei_verified`.

Dans la projection, seuls les textes des chapitres 7, 8 et 11 changent. Les
bytes textuels des 39 premiers segments restent identiques; leurs lignes sont
seulement enrichies de provenance et de la qualification honnête
`exact_first_tei_segment_legacy_chapter_excerpt`.

## 4. Blockers v1-B à v1-E fermés au niveau des gates annoncés

### Registre normatif

Une validation indépendante Draft7 a été exécutée avec les vrais `$defs` de
`data/goals/sota/registry.schema.json`, SHA-256
`829d39c081b4b4cbeaaf1c5381870a91ae350b086e78043979856d1d9d85129a`:

- baseline: 41 erreurs héritées;
- projection: 41 erreurs;
- nouvelles: 0;
- supprimées: 0;
- 13 records touchés, 0 erreur sur ces records.

L'auditeur structurel custom passe également sur une copie appliquée. L'issue
Tatien reste `open`, sévérité `critical`; les huit evidence records restent
`in_review`; aucun fichier de verifications n'est transigé.

### Politique runtime et snapshots

La vraie policy
`graphrag/src/eleutheria_graphrag/agents/citability.py`, SHA-256
`3f47589b89f29b643c699903aa57c8db784f0ef49fcf411a985d779a9b4ec3cd`,
renvoie:

- `DISCOVERABLE_ONLY` pour les deux arguments;
- `BLOCKED` pour les trois traductions machine;
- `DISCOVERABLE_ONLY` pour la synthèse 8-9;
- `CITABLE` pour les trois nœuds grecs exacts 7, 8 et 11.

La projection possède 42 snapshots bijectifs: 42 UUID de corpus distincts, 42
nœuds distincts, aucun snapshot machine ou synthétique. Quatre faux snapshots
sont supprimés, deux sont revalidés et le snapshot exact du chapitre 8 est créé.

### Arêtes

Le diff indépendant confirme exactement 7 suppressions:

```text
1d8e8b3b-8ce5-4f31-8188-99132eab9138
3d77ec6c-0c99-4523-b86e-fdb48785f536
78428983-9305-49f6-81d2-a848e5ff8f05
8cb6fd24-023e-4199-af8b-a4f823589cce
origen-lit-005
reading-a-124
reading-a-127
```

Il confirme aussi 2 ajouts et 11 modifications. Aucune relation active
`cites_primary_source` ne vise la synthèse 8-9 et aucune relation
`authored_by` ne part de cette synthèse.

### Portée exacte et quarantine

Le preview est reproductible: le rapport projeté et le `touched_set` recalculé
sont exactement égaux à ceux du JSON gelé. Les 11 chemins sont:

| Chemin | SHA-256 projeté |
|---|---|
| `audit/2026-08-24_tatian_p0_quarantine.jsonl` | `d23a389533f13e1d38e75d402598a16105ac99d55acc78b98dd81f362d675461` |
| `audit/2026-08-24_tatian_p0_repair.json` | `296dabb1c84a878f87547008f57ab90be18c8ee42b2e830b7b0128a334f360e3` |
| `corpus/citations.jsonl` | `1c8cc71b9535a5917a7a7b0927bf2fb7034c01ab9e4dedf11f3fe15859d7643f` |
| `corpus/manifest.jsonl` | `2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e` |
| `corpus/passages.jsonl` | `e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3` |
| `goals/sota/registry/evidence/seed_priority_20260824.jsonl` | `93a5a4380089dd01a9698d71ea6e6f5d5e3dde8fe061646da01d14bce49b2033` |
| `goals/sota/registry/issues/seed_known_20260824.jsonl` | `5c102d494bd322d91e1adaec5f0d156beed50b270b6e5bb468adb4062e7d183b` |
| `goals/sota/registry/sources/seed_priority_20260824.jsonl` | `4608ac673393cd796979a94b20cf42e65175f9e970a5b61b61ecbd8457c429a7` |
| `goals/sota/registry/waves/priority_20260824.jsonl` | `541458784dc8ff6f04d7e19e0aa93a65af9918b4b49826bfb841ba540f646bae` |
| `kg/edges.jsonl` | `e7d6569898a4b8f882ae342f5abb4ff6e216eea93bce4eb9fcdc03014d0519f5` |
| `kg/nodes.jsonl` | `c1308768f075209fff6b1ff6fe2aa79ca4109465083148e6f0f9220ced0c0dc6` |

Les lignes JSONL hors changed-record set sont byte-identiques. Le diff exact est:

| Surface | Ajouts | Modifications | Suppressions |
|---|---:|---:|---:|
| nodes | 1 | 16 | 0 |
| edges | 2 | 11 | 7 |
| passages | 0 | 42 | 0 |
| citations | 2 | 2 | 4 |
| manifest | 0 | 1 | 0 |
| registry sources | 2 | 1 | 0 |
| registry evidence | 7 | 1 | 0 |
| registry issues | 1 | 0 | 0 |
| registry waves | 0 | 1 | 0 |

Les 101 entrées de quarantine ont toutes un before-hash valide. Répartition:
42 passages, 18 arêtes existantes, 16 nœuds existants, 6 citations existantes,
7 absences evidence, 2 absences citation, 2 absences edge, 2 absences source,
et une entrée pour chacune des catégories manifest, absence node, source,
evidence, absence issue et wave.

## 5. Blocker résiduel P0-A: l'evidence 15.9 hash le segment 15.1

Le record projeté `ev_anc_tatian_orat_15_9_demonic_law` affirme une attestation
directe à *Oratio* 15.9. Son objet `quotation` porte:

- `status=collated`;
- `corpus_passage_ids=[fdefee1b-2430-4ed0-acc2-88f48f2fc875]`;
- `text_sha256=a25f6608a4c94e539509c1285ce35bc2a2156fcd6c9be54d7cf948e4a590b632`;
- cible KG `passage_tatian_15_1`.

Or le TEI officiel divise le chapitre 15 en trois `seg`, numérotés 24, 25 et
26. L'UUID `fdef...` et le nœud `passage_tatian_15_1` contiennent uniquement le
premier bloc `n=24`, long de 751 caractères et hashé `a25f...`; ce texte ne
contient ni le locus 15.9 ni les mots correspondants sur les lois de mort.

Le locus 15.9 est dans le troisième bloc `n=26`, long de 436 caractères,
SHA-256 NFC/collapse-whitespace
`c1c7d081eb9fed87d936019df642d1b6bdbae222eed64a7e6ad855d0ce6e6730`.
La séquence pertinente commence dans ce bloc par l'attribution aux démons,
selon leur autonomie, de lois de mort. Le contrôle visuel PDF 77 / imprimée 66
confirme cette localisation.

Le statut `in_review` et la note générale sur les premiers segments ne rendent
pas correcte une relation `quotation.corpus_passage_ids` vers un texte qui ne
contient pas le claim. Cela contredit aussi le plan de l'audit, qui exige des
evidence units atomiques avec extrait court hashé.

Correction requise: soit créer une unité exacte 15.9/`seg n=26` avec son propre
texte, hash et provenance, soit retirer du P0 ce `corpus_passage_id`, ce hash et
cette cible et laisser l'evidence explicitement non alignée/à recoller. Il ne
faut pas étendre silencieusement la ligne de corpus 15 dans cette vague.

## 6. Blocker résiduel P0-B: deux booléens génériques prétendent encore une vérification

Les deux nœuds publics modifiés suivants conservent dans leur metadata:

```text
person_tatian       citation_verdict=verified  citation_verified=true
work_tatian_oratio  citation_verdict=verified  citation_verified=true
```

Ces booléens sont hérités, mais le v2 réécrit les descriptions auxquelles ils
s'appliquent. Ils deviennent donc des assertions non typées sur un état
prospectif qui conserve explicitement une issue critique ouverte, des evidence
records `in_review` et un sign-off indépendant/adversarial/humain pending. Le
fait qu'aucun record de `registry/verifications` ne soit ajouté ne neutralise pas
ces flags runtime/génériques.

Correction requise: retirer ces deux bundles génériques ou les mettre à faux,
puis conserver uniquement des statuts typés et bornés, par exemple identité
bibliographique, locus/page et support textuel contrôlés. Aucun PASS indépendant
ou consensus ne doit être déduit.

## 7. Blocker résiduel P0-C: le rollback écrase une dérive inter-window

Les scénarios fournis passent pour crash dur, échec de `replace`, échec de
`fsync`, échec de rollback suivi d'une seconde récupération, état prepared,
état committed, idempotence et dérive préexistante de chaque surface.

Un test adversarial supplémentaire sur copie a toutefois produit la séquence
suivante:

1. le premier output (`quarantine`) est remplacé;
2. avant le gate de `corpus/citations.jsonl`, une écriture étrangère modifie ce
   fichier;
3. le gate immédiat détecte correctement la dérive et lève
   `Tatian target drift immediately before replace`;
4. `_restore_entries()` restaure aveuglément toutes les backups, y compris la
   cible jamais remplacée mais désormais étrangère;
5. les bytes concurrents sont perdus, Snapshot-A est rétabli et le journal est
   supprimé.

Résultat observé:

```text
foreign_drift_injected=true
citation_final_equals_foreign=false
citation_final_equals_snapshot_A=true
journal_survives=false
```

La détection n'est donc pas fail-closed: elle précède une écriture destructive
qui efface précisément la dérive détectée. Le lock Tatien est spécifique à ce
script et n'empêche pas un autre applier de toucher les mêmes fichiers.

Correction requise: avant toute restauration, chaque cible doit encore avoir un
hash appartenant à l'état transactionnel attendu (`before` si non remplacée,
`after` si remplacée). Une cible étrangère doit arrêter la restauration, laisser
journal et backups durables et exiger une récupération explicite. Ajouter un
test inter-window qui exige la conservation des bytes étrangers et du matériel
de recovery.

## 8. Commandes et résultats

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q \
  tests/test_tatian_p0_repair.py
39 passed

PYTHONDONTWRITEBYTECODE=1 python3 \
  scripts/apply_2026_08_24_tatian_p0_repair.py \
  --dry-run --data-root data \
  --authority-xml /tmp/tatian-otto-1851-release-1.1.32401591783.xml
exit 0; state planned; authority full_tei_verified; quarantine 101

ruff check scripts/apply_2026_08_24_tatian_p0_repair.py \
  tests/test_tatian_p0_repair.py
PASS

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q \
  tests/test_zero_debt_gates.py \
  tests/test_snapshot_passage_integrity.py \
  tests/test_check_kg_corpus_locus_parity.py \
  tests/test_check_kg_work_child_canonical.py \
  tests/test_audit_sota_registry.py
26 passed
```

Le test supplémentaire d'alignement sémantique retrouve le marqueur attendu
dans cinq evidence targets sur six; seul 15.9 échoue. Le test transactionnel
inter-window reproduit l'écrasement décrit en section 7.

## 9. Verdict exécutable

**FAIL - NO APPLY.** Les corrections v1 sur frontières TEI, schéma normatif,
policy runtime, arêtes, portée exacte et recovery standard sont confirmées.
L'application reste interdite jusqu'à correction simultanée des trois blockers
résiduels, production d'un nouveau tuple gelé et nouvelle revue indépendante.

Aucun write de données n'a été effectué pendant cette revue.
