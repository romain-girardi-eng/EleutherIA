# Revue indépendante et adversariale du P0 Tatien

Date: 2026-08-24  
Portée: revue indépendante en lecture seule; aucune mutation du KG, du corpus,
du registre, des manifestes ou des artefacts d'audit du candidat.  
Verdict global: **FAIL - NO APPLY**.

## 1. Tuple effectivement revu

La revue a commencé en vérifiant byte-for-byte le tuple transmis:

| Artefact | SHA-256 attendu et constaté au début de revue |
|---|---|
| `scripts/apply_2026_08_24_tatian_p0_repair.py` | `daabd391169c2a56b80524b4cae58efb0ae1636a5b3c73210fdd908f03f6825e` |
| `tests/test_tatian_p0_repair.py` | `5ff207544eb6da7b16ac699d7e2a5d5b06a6613c50b1de05cae513125c66c4f5` |
| `tests/fixtures/tatian_otto1851_release_1.1.32401591783.json` | `742cfe0f7be7302b87ae2157b0ca2cbb6c347848e6bca85cd0e4c59ed996d4b9` |
| `/tmp/2026-08-24-tatian-p0-preview.json` | `9718eda219501d0375536255bc275568cbe0fe503283390aa20466bd9d7f7a3d` |

L'audit savant utilisé comme route de contrôle, jamais comme preuve unique, est
`docs/academic/2026-08-24-tatian-sapere28-pdf-audit.md`, SHA-256
`69582cc1cb84b6185936949aa36ec58770ff55a890b17d66a42197e7e2ae2293`.

Le tuple a dérivé pendant la revue. Au dernier contrôle, le script courant avait
le SHA-256 `543ae37dba05275554bd454cd21bfd177cad703885da8bf75876ebd684a92cd8`
et le fixture courant `8358e5e4e5c3f3bbd6bd235513e93313f152c4e21a782e8c29f7b802f924420e`,
tandis que les tests et le preview avaient encore leurs hashes du tuple. Ces
nouveaux octets constituent un successeur **non revu**; ils ne modifient pas le
verdict du tuple ci-dessus. Ils sont en outre incohérents entre eux: le test avec
le TEI officiel échoue actuellement sur le chapitre 7.

## 2. Autorité OGL/Scaife vérifiée indépendamment

Le contrôle a été refait depuis les services officiels, sans prendre le fixture
comme autorité:

- `git ls-remote --tags` sur le dépôt officiel
  [OpenGreekAndLatin/First1KGreek](https://github.com/OpenGreekAndLatin/First1KGreek)
  renvoie le tag annoté `1c0e443edec985b9834db888b21d73cde35315ec` et son
  commit pelé `78f9df37d694a9e0e92de2963f2fa8852e49efb6` pour
  `1.1.32401591783`;
- le [TEI officiel épinglé](https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/1.1.32401591783/data/tlg1766/tlg001/tlg1766.tlg001.perseus-grc1.xml)
  a le SHA-256 `bfe1671160c9155552055a24bd86345d2efb5392cd03e70a947d4a7a9ce00e4a`;
- le [catalogue CTS de l'oeuvre](https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/1.1.32401591783/data/tlg1766/tlg001/__cts__.xml)
  a le SHA-256 `df7b14a2b0db327787fea20a6a659104808f87a07e8c9017fec0e7a5775579d8`;
- le CTS donne `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1`, Tatien,
  *Oratio ad Graecos*, Johann Carl Theodor Otto, Jena, Mauke, 1851;
- le header TEI déclare explicitement la licence
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/);
- la [route Scaife](https://scaife.perseus.org/library/urn%3Acts%3AgreekLit%3Atlg1766.tlg001/)
  et son lecteur confirment l'identité CTS de l'oeuvre et de la version.

Le TEI contient exactement 42 `div` de chapitre. Leur distribution en blocs
`seg` est: 21 chapitres à 2 segments, 14 à 3, 5 à 1, un à 4 et un à 5. Les
seuls chapitres mono-segment sont 24, 28, 30, 38 et 42. Les 42 hashes de
premier segment et les 42 numéros de premier segment du fixture correspondent
au TEI frais. Cette partie du fixture est **PASS**.

## 3. Contrôle visuel indépendant de SAPERE 28

Le PDF local a été rendu depuis la source, sans utiliser son texte comme
manifestation Otto:

- SHA-256 `33f355b55cb446273498b2557022e52c3e83a1f75aea84ec136eb31ea5aea4db`;
- 3,063,004 octets; 345 pages; PDF 1.7, non chiffré;
- titre, responsables, Mohr Siebeck, 2016, ISBN et eISBN confirmés aux PDF 4-5;
- la page de copyright interdit notamment reproduction, traduction et
  intégration électronique hors limites légales;
- les PDF 59, 61, 63, 67-69 et 77 confirment respectivement les loci 7.2-7.3,
  8.1, 9.3, 11.4 et 15.9, avec la règle `PDF = page imprimée + 11`;
- les PDF 244-245 confirment l'interprétation attribuée à Strutwolf/Lakmann et
  son aporie;
- les PDF 289-292 confirment que Timotin ne nie pas toute efficacité astrale,
  mais subordonne l'influence au cadre démonologique et religieux.

Le bornage Otto/Nesselrath proposé est substantiellement correct. Le candidat
conserve les leçons Otto dans la manifestation épinglée et marque les leçons
SAPERE dans des records de collation distincts. Il ne republie pas de long texte
allemand dans les nouveaux evidence records.

## 4. Blocker P0-A: faux assemblage des chapitres complets

Le fixture du tuple et `parse_authority_xml()` fabriquent les trois chapitres
complets par concaténation brute du descendant textuel. Or les `seg` adjacents
sont des blocs sémantiques et n'ont aucun `tail` XML. La concaténation produit
donc notamment:

- chapitre 7: `τρόπον.Ἡ`;
- chapitre 8: `ἀπογεννήματα·πᾶσα`, `Ὅμηρος,Ἄσβεστος`,
  `ἐγίνετο.Ταύτην`, `ὤνατο.Λεγέτω`;
- chapitre 11: `περιγίνεται.Τί`.

L'égalité de hash entre le fixture et cet algorithme ne prouve pas un texte
sémantiquement exact; elle prouve seulement qu'ils partagent la même erreur.
Un assemblage déterministe block-aware doit normaliser chaque `seg`, puis les
joindre par un espace unique. Les hashes NFC/collapse-whitespace attendus sont:

| Chapitre | Longueur tuple | SHA-256 tuple | Longueur block-aware | SHA-256 block-aware |
|---:|---:|---|---:|---|
| 7 | 1624 | `db3c5f88bd6f820cd9527f3b05467204347761f2ac505b6249b5c0acd3c48ca5` | 1625 | `10d5f5de95045e8c9754a2c431cbfa14042a72b1f87b6fa9ab277f5079c3b4fd` |
| 8 | 2684 | `fecabd2a915ec4de3788ed6160e31841b763e0da49067b650c946476ad368470` | 2686 | `9194a6ddb13cec8fcf74d4d20392688a5787d1aff18c29872a738205e10bdb6f` |
| 11 | 1368 | `ca33d2ba0600e7cbdd0a5cc4b67e9aeff2fb0bad95638730e1a96935a77b90b4` | 1369 | `65be1c120ed652dfc6e6bc4d0d94a86bd23d32fb76b12821d411c64ddaaffd20` |

Cela invalide les trois textes prospectifs, leurs hashes, les trois exact-node
descriptions, les evidence hashes correspondants, les hashes de fichiers du
preview et le rapport. Le script, fixture, tests et preview doivent tous être
rehashés ensemble.

Le successeur apparu pendant la revue ajoute bien un join block-aware au script,
mais son fixture n'a pas encore été réécrit: le test avec le TEI officiel donne
`RuntimeError: authority full-chapter drift at chapter 7`. Il n'est donc pas une
correction exécutable de ce blocker.

## 5. Blocker P0-B: +53 erreurs contre le schéma registry normatif

Le candidat teste uniquement l'auditeur custom, qui ne fait pas respecter toutes
les contraintes `additionalProperties` et enums. Une validation Draft7 de chaque
`$defs` du vrai `data/goals/sota/registry.schema.json` (SHA-256
`829d39c081b4b4cbeaaf1c5381870a91ae350b086e78043979856d1d9d85129a`)
donne sur le registre complet:

- baseline: 41 erreurs normatives héritées;
- preview: 94;
- **nouvelles: 53**;
- supprimées: 0.

Répartition des 53 nouvelles erreurs:

- 41 sur les huit evidence records;
- 9 sur les trois sources;
- 3 sur l'issue.

Exemples systématiques:

- rôles d'artefact non admis: `source_tei`, `authority_record`, `source_pdf`;
- propriétés source non admises: `rights` et
  `coverage.corpus_manifestation_ids`;
- propriétés locator/quotation non admises: `edition_scope_note`, `rights`,
  `text_scope`;
- statuts quotation non admis:
  `collated_hash_only_no_sapere_republication` et
  `not_captured_copyright_bounded_paraphrase_only`;
- `page_map_status=visually_verified_against_sapere_collation` hors enum;
- required-verification hors enum: `edition_identity`, `human_signoff`;
- issue type `source_text_contamination` hors enum;
- propriétés issue non admises: `open_debt`, `affected_corpus_ids`.

La réparation doit employer le vocabulaire normatif existant ou déplacer les
caveats dans des champs autorisés (`notes`, `summary`, `resolution_criteria`),
puis prouver `new normative errors == 0`. Il ne faut ni élargir le schéma pour
faire passer ce candidat, ni affaiblir l'auditeur.

## 6. Blocker P0-C: les deux arguments restent citables au runtime

Le candidat met `citation_verified=false` et un verdict `in_review`, mais la
policy runtime réelle ne comprend pas ces marqueurs comme un blocage. Testée
contre `graphrag/src/eleutheria_graphrag/agents/citability.py`, SHA-256
`3f47589b89f29b643c699903aa57c8db784f0ef49fcf411a985d779a9b4ec3cd`,
elle renvoie encore `CITABLE` pour:

- `argument_tatian_above_fate`;
- `argument_tatian_freewill_paradox`.

Le contenu est mieux atomisé, mais les secondary claims sont `in_review` et les
reconstructions ne sont pas adjudiquées. Les deux noeuds doivent porter
`metadata.citability="discoverable_only"`, avec un test utilisant la vraie
`evidence_policy`. Les trois nœuds machine sont correctement `BLOCKED`, le
nœud synthétique est correctement `DISCOVERABLE_ONLY`, et les trois vrais
noeuds grecs seraient `CITABLE` une fois le blocker des frontières corrigé.

## 7. Blocker P0-D: relations primaires toujours dirigées vers la synthèse

Le candidat annote certains edges connectés à
`passage_tatian_orat_8_9` comme `citable_as_primary=false`, mais conserve trois
relations actives `cites_primary_source` vers ce record éditorial:

- `origen-lit-005` depuis l'argument Secord;
- `reading-a-124` depuis l'argument Crawford sur l'instruction illicite;
- `reading-a-127` depuis l'argument Crawford sur l'efficacité du destin astral.

La sémantique runtime est portée d'abord par la relation, pas garantie par ces
nouveaux champs libres. Ces edges doivent être rétrogradés en `discusses` /
`related` ou recâblés vers des unités exactes seulement après contrôle de leurs
propres artefacts et locators. Les deux edges Justin `parallel_to` peuvent rester
discovery-only avec caveat. L'edge `authored_by` de la synthèse éditoriale vers
Tatien mérite aussi d'être supprimé ou remplacé par une provenance éditoriale.

Les suppressions des quatre faux snapshots, la revalidation de deux snapshots,
la création du snapshot exact du chapitre 8 et la bijection finale de 42
snapshots sont par ailleurs correctes dans la logique du candidat.

## 8. Blocker P0-E: touched-set et drift insuffisamment fail-closed

Le rapport énumère onze fichiers et 101 records de quarantine, mais les tests ne
prouvent pas l'exact changed-record set. Ils vérifient seulement que les chemins
ne contiennent pas `eval`, `sorabji`, `long` ou `deploy`.

Plus important, le transform ne porte pas de before-hashes revus pour les 16
nœuds modifiés, les 18 edges modifiés/supprimés, les 6 citations remplacées ou
les records registry. Le snapshot A détecte une écriture *après* lecture, mais
n'empêche pas d'écraser silencieusement un record déjà divergent au début du
run. Quelques préconditions lexicales et les 39 hashes de segments ne couvrent
pas ce risque global.

Avant apply, il faut:

1. figer hashes/IDs/digests before et after des cohortes exactes;
2. tester que tout nœud/edge/citation hors cohortes reste canonically et
   byte-identique;
3. faire échouer un drift préexistant sur chaque surface touchée;
4. vérifier les 101 types/IDs de quarantine, pas seulement leur nombre.

Le fixture lui-même n'est pas hash-gaté par l'applier. En mode par défaut, un
fixture modifié peut changer les trois chapitres tout en conservant les champs
d'identité sélectionnés. Le write doit vérifier le SHA-256 du fixture annoncé
(`742c...f4b9`) ou exiger le TEI officiel hashé; la fonction réseau actuellement
définie n'est appelée nulle part.

## 9. Contrôles qui passent dans le tuple

Sous réserve des blockers ci-dessus, les points suivants sont bien conçus:

- identité release/tag/commit/TEI/CTS/licence externe;
- conservation des UUID, CTS et séquences des trois corpus rows;
- immobilité des bytes textuels des 39 autres rows;
- déclaration honnête `exact_first_tei_segment_legacy_chapter_excerpt` et
  couverture partielle;
- séparation des variantes Otto et Nesselrath dans les nœuds fins;
- blocage des trois traductions machine et démotion de la synthèse 8-9;
- structure directe / secondary-in-review / reconstruction des deux arguments;
- issue critique `OPEN`, evidence `in_review`, aucune nouvelle verification PASS;
- bornage copyright SAPERE et absence de longue republication dans les nouveaux
  evidence records;
- transaction avec snapshot A, lock, journal, backups, rollback et récupération
  après crash simulé;
- idempotence sur copie;
- 101 records de quarantine avec before-images.

Commandes exécutées sur le tuple initial:

```text
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_tatian_p0_repair.py
15 passed

PYTHONDONTWRITEBYTECODE=1 python3 scripts/apply_2026_08_24_tatian_p0_repair.py \
  --dry-run --data-root data \
  --authority-xml /tmp/tatian-otto-1851-release-1.1.32401591783.xml
exit 0; state planned; authority full_tei_verified; quarantine 101

ruff check scripts/apply_2026_08_24_tatian_p0_repair.py \
  tests/test_tatian_p0_repair.py
PASS

PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/test_zero_debt_gates.py tests/test_snapshot_passage_integrity.py \
  tests/test_check_kg_corpus_locus_parity.py \
  tests/test_check_kg_work_child_canonical.py tests/test_audit_sota_registry.py
26 passed
```

Le preview fourni était reproductible contre le tuple initial: 11 chemins, 101
quarantine records et les hashes `after` annoncés. Cette reproductibilité portait
toutefois sur les textes à frontières fusionnées et ne compense pas les erreurs
normatives/runtime.

## 10. Transaction: réserves adversariales restantes

Le test de crash dur après un remplacement et la récupération du journal passent.
La suite fournie ne teste pas séparément:

- échec de restauration après un échec de commit;
- échec de `fsync` pendant commit/rollback;
- conservation obligatoire du journal et des backups si le rollback échoue;
- drift préexistant record-level.

Ces cas doivent être ajoutés avant production. Ils ne sont pas la cause première
du verdict, mais font partie du gate transactionnel demandé.

## 11. Verdict exécutable

**FAIL - NO APPLY.** Aucun write de données n'a été effectué pendant cette revue.

Minimum avant nouvelle revue indépendante:

1. assemblage block-aware des chapitres 7/8/11, nouveaux hashes et nouveau
   preview complet;
2. zéro nouvelle erreur contre le schéma registry normatif;
3. `discoverable_only` réel pour les deux arguments;
4. aucune relation `cites_primary_source` vers la synthèse 8-9;
5. before/after preconditions et exact touched-set tests record-level;
6. fixture/TEI authority gate obligatoire et tests de rollback dégradé;
7. nouveau tuple stable: script, tests, fixture et preview tous rehashés ensemble.

