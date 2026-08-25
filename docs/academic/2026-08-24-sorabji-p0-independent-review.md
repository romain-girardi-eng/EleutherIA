# Revue indépendante et adversariale du P0 Sorabji

Date: 2026-08-24  
Portée: revue indépendante, en lecture seule, de la proposition `scripts/apply_2026_08_24_sorabji_p0_repair.py`; aucun `--write`, aucune mutation du KG, du corpus, des registres, des manifestes ou du BibTeX.  
Autorité visuelle pour Sorabji 1980: `data/literature_acquisition/sorabji_1980_necessity_cause_blame.pdf`.  
Usage de l'OCR: navigation seulement.  
Verdict global: **FAIL - NO APPLY**.

## 1. Verdict exécutable

La collation savante de la plupart des claims est solide. L'identité Cornell, la séparation Duckworth/Cornell/Chicago, la distinction scan/OCR, la relation cause-nécessitation, les trois lectures du cylindre, Diodore, le clinamen, `eph' hêmin`, la différence 1980/2017 et les pages sur le volontaire sont confirmés.

La proposition ne doit pourtant pas être appliquée. Les blockers sont:

1. `EIGHT_STRATEGIES` contient **sept** éléments, car les stratégies 1 et 2 sont fusionnées dans une entrée `1-2`. Le registre affirme néanmoins que l'ordre exact de huit stratégies est stocké, et une vérification `pass` est créée pour ce faux état.
2. Les neuf noeuds interprétatifs restent `citable` dans la policy runtime. `needs_evidence=true` et les nouveaux `citation_verdict` ne sont pas compris par `evidence_policy`; un verdict inconnu retombe sur `CITABLE`.
3. Les descriptions publiques de `concept_eph_hemin...` et `debate_stoic_compatibilism` conservent les sur-affirmations que les nouvelles métadonnées déclarent disputées. Le noeud dog-cart conserve aussi des champs hérités incompatibles avec la correction.
4. `year_edition_used=1980` est faux selon la sémantique documentée du manifest: le fichier OCRisé est un Cornell Paperback, édition inaugurée en 1983; seul le tirage exact reste inconnu.
5. Une panne pendant le rollback efface le journal et les sauvegardes tout en laissant un état partiellement écrit. Le défaut a été reproduit en répertoire temporaire.
6. Le CLI dry-run peut annoncer `ready_for_second_root_review` et sortir avec code 0 alors que le registre global est structurellement invalide.
7. Les neuf champs E2 `quote_verbatim*` hérités, soit environ 948 mots, ne sont pas dupliqués par le plan mais restent sans drapeau explicite `internal_only` / `unverified_do_not_republish`.
8. Le changement BibTeX n'est pas reproductible par l'exporteur canonique, laisse un `@book` sans éditeur, et n'est pas conservé record-by-record dans la quarantine.

## 2. Indépendance, source et intégrité

Je n'ai utilisé le rapport initial que comme inventaire de claims à tester, jamais comme preuve. Je n'ai communiqué avec aucun agent Sorabji antérieur avant ce verdict.

| Contrôle | Résultat indépendant | Verdict |
|---|---|---|
| Scan source | SHA-256 `be1f8fce483503d04504c73da30dc9bbcd52f5f8c04bd0e520cbd42fd4a3d500`; MD5 `fad1922c52969d334243888e0f9856a6`; 35,334,906 octets | PASS |
| Dérivé OCR | SHA-256 `022e9c6440f7a5e43f89c72205795165853ae85b97389b167027a3bf0e38b007`; MD5 `e474ab26adb4f127a0445f1e2628ae28`; 79,185,903 octets | PASS |
| Pages | 344 pour le scan et 344 pour l'OCR | PASS |
| Images source | 344 images, une et une seule par page | PASS |
| Syntaxe PDF | `qpdf --check` sans erreur sur les deux fichiers | PASS |
| Autorité | scan image comme autorité; OCR comme navigation | PASS |
| Carte arabe | pour p. 3-326, `PDF = page imprimée + 17` | PASS |
| Réutilisation des PDF | `reuse_status=unverified_do_not_republish` dans le manifest d'acquisition | PASS |

Le producteur technique et les dates 2026 du conteneur ne sont pas des dates d'édition.

## 3. Pages rendues et relues

Les 87 pages obligatoires ont toutes été rendues depuis le scan source à 180 dpi et relues visuellement. Des pages supplémentaires ont été rendues pour les claims E2 et la distinction 1980/2017.

| Objet contrôlé | Pages imprimées | Pages PDF | Verdict |
|---|---:|---:|---|
| Titre et copyright | sans folio | 4-5 | PASS |
| Cause sans nécessitation | 26-32 | 43-49 | PASS |
| Principe causal stoïcien | 64-69 | 81-86 | PASS |
| Huit retraits, cylindre, dog-cart, clinamen, `eph' hêmin` | 70-88 | 87-105 | PASS source; FAIL encodage des huit |
| Diodore et Maître Argument | 104-110 | 121-127 | PASS |
| Action, origine interne, indéterminisme | 228-248 | 245-265 | PASS |
| Volontaire, ignorance, tentation, négligence | 257-281 | 274-298 | PASS |
| Clinamen supplémentaire | 18-19 | 35-36 | PASS |
| Bataille navale / preuve registry | 91-103 | 108-120 | PASS |
| `eph' hêmin` stoïcien supplémentaire | 252 | 269 | PASS |
| Couvertures Cornell Paperbacks | sans folio | 1 et 344 | PASS |
| Sorabji 2017, claim Cicéron/Lucrèce | 53 | PDF 66 du volume 2017 | PASS |

## 4. Claims savants

Toutes les formulations ci-dessous sont des paraphrases brèves de Sorabji, pas des validations indépendantes des sources antiques.

| Claim | Preuve visuelle exacte | Résultat |
|---|---|---|
| Des effets et décisions peuvent être causés ou expliqués sans être nécessités. | p. 26-32 / PDF 43-49 | PASS |
| La répétition de toutes les circonstances est reliée par la reconstruction stoïcienne au même effet et à la nécessité. | p. 64-69 / PDF 81-86 | PASS, comme reconstruction de Sorabji |
| Sorabji distingue huit retraits stoïciens. | p. 71 et résumé p. 85 / PDF 88 et 102 | PASS dans le livre; FAIL dans la constante à sept entrées |
| Stratégie 1: Cléanthe refuse la nécessité de toute vérité passée. | p. 72 / PDF 89 | PASS |
| Stratégie 2: Chrysippe refuse que l'impossible ne puisse suivre du possible. | p. 72 / PDF 89 | PASS |
| Stratégie 3: la nécessité ne se transmet pas sans restriction de l'antécédent au conséquent. | p. 72-74 / PDF 89-91 | PASS |
| Stratégie 4: cas astrologiques reformulés comme implications matérielles. | p. 74-78 / PDF 91-95 | PASS |
| Stratégie 5: possibilité philonienne comme aptitude malgré les obstacles. | p. 78-79 / PDF 95-96 | PASS, avec les réserves de Sorabji |
| Stratégie 6: causes internes/externes et cylindre. | p. 79-83 / PDF 96-100 | PASS |
| Stratégie 7: possibilité épistémique par ignorance des empêchements. | p. 83-84 / PDF 100-101 | PASS |
| Stratégie 8: non-nécessité supposée parce que la proposition future cesse d'être vraie. | p. 84-85 / PDF 101-102 | PASS |
| Les trois lectures du cylindre sont celles d'Augustin, Donini et Frede; aucune n'est canonisée. | p. 80-83 / PDF 97-100 | PASS |
| Le dog-cart combine consentement et nécessité; il ne montre pas une alternative ouverte. | p. 70 / PDF 87 | PASS |
| Diodore est dit dialecticien; le classement mégarique catégorique est rejeté; les reconstructions détaillées restent incertaines. | p. 64, 104-110 / PDF 81, 121-127 | PASS |
| Le clinamen est relié à la liberté dans l'exposé latin de Lucrèce; le motif n'est pas établi par un texte survivant explicite d'Épicure. | p. 18-19 et 86 / PDF 35-36 et 103 | PASS |
| Chez Sorabji, l'`eph' hêmin` aristotélicien humain implique une possibilité bilatérale. | p. 233-235 / PDF 250-252 | PASS comme lecture disputée de Sorabji |
| La position stoïcienne rapportée permet `par nous` et selon l'impulsion sans alternative réellement ouverte. | p. 86 et 252 / PDF 103 et 269 | PASS comme rapport secondaire |
| L'origine interne n'est pas une cause non causée; l'action peut rester causée sans avoir été nécessaire depuis toujours. | p. 228-238 / PDF 245-255 | PASS |
| L'enfant et le jouet est un exemple construit par Sorabji. | p. 232 et p. 248 / PDF 249 et 265 | PASS |
| La nouveauté hellénistique est la persistance de Diodore et des Stoïciens, non l'invention du déterminisme ou du conflit moral. | p. 247 / PDF 264 | PASS comme thèse historiographique de Sorabji |
| Les analyses de `EE` II, `NE` V et `NE` III ne sont pas une doctrine harmonisée unique. | p. 257-261 et 272-275 / PDF 274-278 et 289-292 | PASS |
| La classification de `NE` V 8 comporte quatre degrés et rend décisive la description de l'acte. | p. 278-281 / PDF 295-298 | PASS |

## 5. Sorabji 1980 contre Sorabji 2017

La séparation proposée est correcte.

- Le volume de 1980, p. 18-19 / PDF 35-36, fournit le cadre Lucrèce/clinamen et l'objection d'aléatoire. Il ne formule pas le claim précis que Cicéron reprend le vocabulaire de Lucrèce.
- Sorabji 2017, p. 53 / PDF 66 du volume *Selfhood and the Soul*, formule explicitement la relation Cicéron-Lucrèce.
- Les cinq arêtes `advanced_in` vers `scholarly_work_sorabji_2017_freedom_and_will_graeco_roman_origins` restent byte-identiques dans le preview. C'est correct.
- Dans E2, `publication_id` du claim Cicéron passe à 2017 et `background_publication_id` à 1980. C'est correct.

Verdict 1980/2017: **PASS**.

## 6. Manifestations Cornell, Duckworth et Chicago

Les pages visuelles et catalogues se recoupent:

- PDF 4: titre, auteur, Cornell University Press, Ithaca.
- PDF 5: copyright 1980; première publication Cornell 1980; premier Cornell Paperback 1983; ISBN cloth `0-8014-1162-9`; ISBN paper `0-8014-9244-0`.
- PDF 1 et 344: couverture et quatrième Cornell Paperbacks.
- [CiNii Duckworth BA04347273](https://ci.nii.ac.jp/ncid/BA04347273): London, Duckworth, 1980, ISBN `0715613723` et `0715615491`; le catalogue ne résout pas sûrement chaque ISBN vers un binding distinct.
- [CiNii Cornell BA37345728](https://ci.nii.ac.jp/ncid/BA37345728): Ithaca, Cornell University Press, 1980, ISBN `0801411629`, `xv, 326 p., [1] leaf of plates`.
- [BiblioVault Chicago](https://www.bibliovault.org/BV.book.epl?ISBN=9780226768243): University of Chicago Press, 2006, paper ISBN `978-0-226-76824-3`.

L'objet intellectuel 1980, les manifestations Duckworth et Cornell, la première édition Cornell paperback de 1983, le tirage local inconnu et Chicago 2006 ne doivent pas être fondus.

Verdict des trois manifestations intégrées au noeud publication: **PASS**, sous réserve du manifest d'ingestion signalé ci-dessous.

## 7. Revue des 11 node transforms

Le verdict `runtime` tient compte de la policy réelle: dans le preview actuel, les onze noeuds sont tous classés `citable`. Les neuf noeuds interprétatifs devraient être `discoverable_only` tant que l'issue est ouverte.

| Noeud | Fond proposé | Défaut résiduel | Verdict |
|---|---|---|---|
| `person_sorabji_richard_contemporary` | Remplace Bristol par Duckworth/Cornell/Chicago et enlève les booléens génériques. | `citation_verdict=verified` et le vieux `verified_reference` Duckworth seul restent incohérents avec la correction, mais le fait bibliographique minimal est vrai. | PASS avec nettoyage P2 |
| `pub_sorabji_1980_necessity_cause_blame` | Sépare objet intellectuel et trois manifestations; enlève publisher/place/ISBN du niveau abstrait. | Aucun blocker sémantique dans ce noeud. | PASS |
| `scholarly_position_sorabji_aristotle_indeterminist` | Pages, attribution, absence de `fresh start`, causalité non nécessitante correctes. | Toujours `citable` malgré `needs_evidence` et statut disputé. | FAIL runtime |
| `argument_chrysippus_causal_taxonomy` | Corrige l'auxiliary-only et ajoute les trois lectures. | Toujours `citable`. | FAIL runtime |
| `argument_cylinder_analogy_chrysippus_k1l2m3n4` | Description et conclusion deviennent prudemment disputées. | Toujours `citable`; plusieurs prémisses antiques restent hors recollation. | FAIL runtime |
| `concept_cylinder_analogy_chrysippus_e5f6g7h8` | Supprime l'affirmation fatal-mais-non-nécessaire et ajoute trois lectures. | Toujours `citable`. | FAIL runtime |
| `argument_the_dog_and_cart_argument_9ba60714` | Description et témoin candidat sont bien rétrécis. | Conserve `formulator="Zeno of Citium or Cleanthes"`, `targets`, `argument_form="modus_tollens"`, `legacy_premises`, un `validity_assessment` affirmatif et un `verified_reference`; toujours `citable`. | FAIL |
| `argument_the_master_argument_kurieuon_logos_355f4d3f` | Dialecticien, non-Mégarique catégorique, reconstructions incertaines. | Toujours `citable`. | FAIL runtime |
| `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6` | Distingue Lucrèce, Cicéron et l'absence de texte explicite d'Épicure. | Toujours `citable`. | FAIL runtime |
| `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` | `typed_readings` est utile et correctement paginé. | La description publique non modifiée affirme encore une doctrine composite et dit qu'Aristote est bilatéral mais non indéterministe; `verified_reference` survit; toujours `citable`. | FAIL |
| `debate_stoic_compatibilism` | Ajoute les trois lectures et le `perhaps` de Sorabji. | La description publique continue de présenter causal taxonomy, assentiment et `eph' hêmin` unilatéral comme synthèse établie; `verified_reference` survit; toujours `citable`. | FAIL |

### Correctif de citabilité exact

Le set minimal à rendre `discoverable_only` est:

- `scholarly_position_sorabji_aristotle_indeterminist`
- `argument_chrysippus_causal_taxonomy`
- `argument_cylinder_analogy_chrysippus_k1l2m3n4`
- `concept_cylinder_analogy_chrysippus_e5f6g7h8`
- `argument_the_dog_and_cart_argument_9ba60714`
- `argument_the_master_argument_kurieuon_logos_355f4d3f`
- `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6`
- `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7`
- `debate_stoic_compatibilism`

Ajouter `metadata.citability="discoverable_only"` est le correctif local minimal. Une correction plus générale ferait de la policy une whitelist fail-closed, ou lui apprendrait `needs_evidence` et les verdicts disputés. Le test requis est, pour les neuf IDs, `evidence_policy(after_node).tier == DISCOVERABLE_ONLY`.

### Remplacement précis pour `concept_eph_hemin...`

Conserver le court paragraphe étymologique, puis remplacer le reste de `description` par une formulation de ce type:

> Cross-period concept node. In Sorabji's 1980 reading, Aristotelian human eph' hemin implies a two-way possibility. The Stoic position he reports through Alexander and Nemesius permits action through us and according to impulse without an open alternative. Later one-sided and two-sided reconstructions remain disputed; this node states no single ancient doctrine or consensus.

Retirer ou renommer `verified_reference` en `reference_bundle_pending_recollation`. Ne pas garder sans attribution les phrases actuelles selon lesquelles le concept implique trois propriétés fixes ou qu'Aristote serait bilatéral mais non indéterministe.

### Remplacement précis pour `debate_stoic_compatibilism`

Remplacer la description synthétique par une description de débat, par exemple:

> Modern analytical debate node, not a single ancient doctrine. Sorabji 1980 distinguishes Augustine, Donini and Frede readings of the cylinder, says the soft reply appears perhaps with Chrysippus, and judges the eight retreats unsuccessful. Compatibilism, one-sided eph' hemin and the moral success of the cylinder remain disputed pending primary recollation.

Retirer ou renommer `verified_reference` comme ci-dessus.

### Nettoyage précis pour dog-cart

- Remplacer `formulator="Zeno of Citium or Cleanthes"` par une attribution secondaire structurée à Zénon et Chrysippe, avec statut `pending_primary_recollation`, ou supprimer le champ.
- Remplacer `argument_form="modus_tollens"` par `argument_form="analogy"`.
- Récrire `targets` comme simple portée: consentement/résistance sous un résultat nécessaire, sans alternative démontrée.
- Retirer ou quarantainer `legacy_premises`.
- Réduire `validity_assessment` à un statut `not_assessed_pending_primary_recollation`.
- Retirer ou renommer `verified_reference`; le témoin direct reste seulement candidat.
- Dans P2, préférer `combines consent with necessity` à `preserves its own agency`.

## 8. Les deux edge removals

| Edge | État avant | Décision | Verdict |
|---|---|---|---|
| `0615cd5b-95aa-4e00-9d2c-264f8fae0c3c` | dog-cart `cites_primary_source` Epictetus Enchiridion | Suppression: Épictète n'est pas le témoin direct du dog-cart. | PASS |
| `69f8b629-1c14-4281-83f7-68c6ebaeb820` | Enchiridion `source_for` dog-cart | Suppression pour la même raison. | PASS |

Les cinq arêtes Sorabji 2017 restent inchangées: **PASS**.

## 9. E2, registry, issues, wave et verifications

### E2

PASS partiels:

- scan et OCR deviennent deux artefacts distincts avec les bons hashes;
- le MD5 OCR n'est plus attribué au scan;
- les statuts OCR sont déplacés sous `legacy_ocr_review`;
- les pages des huit patches sont justes;
- cylindre et 1980/2017 sont correctement réattribués.

FAIL:

- `strategy_order` a sept éléments;
- aucune validation n'exige `len(EIGHT_STRATEGIES) == 8`;
- neuf champs `quote_verbatim*`, environ 5,900 caractères / 948 mots, restent inchangés;
- ces citations ne sont pas dupliquées dans la quarantine ou les nouveaux evidence records, ce qui est bon, mais E2 ne porte aucun drapeau explicite de non-exposition et non-republication.

Avant apply, ajouter au minimum des champs top-level du type:

- `runtime_exposure="internal_audit_only"`
- `reuse_status="unverified_do_not_republish"`
- `legacy_quotes_status="retained_in_place_not_duplicated"`

et un test assurant qu'aucun consommateur runtime actif ne charge E2. Ne pas recopier les citations dans un autre artefact.

Verdict E2: **FAIL**.

### Evidence registry

| Evidence | Pages | Verdict |
|---|---|---|
| `ev_sec_sorabji_sea_battle_pp91_103` | 91-103 / PDF 108-120 | PASS |
| `ev_sec_sorabji_ignorance_pp272_275` | 272-275 / PDF 289-292 | PASS |
| `ev_sec_sorabji_bibliographic_manifestations_pdf4_5` | PDF 4-5 + catalogues | PASS |
| `ev_sec_sorabji_eight_retreats_pp71_85` | 71-85 / PDF 88-102 | FAIL: `exact stored order` est faux tant que la liste a sept éléments |
| `ev_sec_sorabji_cylinder_three_readings_pp80_83` | 80-83 / PDF 97-100 | PASS |
| `ev_sec_sorabji_caused_not_necessitated_pp26_32` | 26-32 / PDF 43-49 | PASS |
| `ev_sec_sorabji_aristotle_action_pp228_238` | 228-238 / PDF 245-255 | PASS |

Les claims restent `in_review`, paraphrase-only, sans `primary_source_verified` ni consensus: **PASS**.

### Issues et wave

Les deux issues sont bien ouvertes et bloquent la wave: **PASS**. L'issue interprétative doit explicitement inclure le défaut runtime de citabilité et les champs dog-cart résiduels.

Le rôle `audit_report` attribué à `data/kg/e2_patches/sorabji.json` est sémantiquement faux: c'est un patch de curation/legacy evidence. Le schéma devrait ajouter un rôle `curation_patch` ou `legacy_evidence_patch`. Le rôle `stage="primary"` des vérifications est en revanche acceptable: il signifie première revue de l'unité de preuve secondaire, et `target_type`, `evidence_kind` et les notes empêchent la confusion avec une source antique.

### Verifications

Sept des huit nouveaux passages/identity reviews décrivent correctement le travail du premier auditeur. `ver_sorabji_eight_retreats_primary_20260824` ne peut pas être `pass` tant que l'état stocké n'a que sept éléments.

Verdict verifications: **FAIL partiel**.

## 10. Scholarly manifest

Le README définit `year_edition_used` comme l'année de l'édition réellement OCRisée. Le preview propose:

- `year_original=1980`: correct;
- `year_edition_used=1980`: incorrect;
- `edition_used` mentionne simultanément Cornell 1980, Cornell Paperbacks 1983 et le tirage inconnu.

Correction attendue:

- `year_original=1980`
- `year_edition_used=1983`
- `edition_used="Cornell Paperbacks, Cornell University Press, Ithaca, first paperback edition 1983; exact printing unknown"`
- un champ séparé `local_printing_year=null` ou équivalent si le schéma l'autorise.

Le statut d'ingestion `partial`, les hashes, la distinction OCR et les comptes OCR marqués non fiables sont corrects.

Verdict scholarly manifest: **FAIL** jusqu'à correction de l'année/rôle.

## 11. BibTeX et quarantine

La suppression de l'ISBN Chicago 2006 du record 1980 est correcte. Le nouvel artefact présente toutefois trois problèmes:

1. Un `@book` réutilisable devrait disposer d'une manifestation citée et de son éditeur. L'entrée abstraite ne contient plus aucun `publisher`.
2. `scripts/export_publications_bibtex.py` appliqué au noeud transformé produit une note différente de `NEW_BIB_ENTRY`; le changement manuel n'est donc pas reproductible.
3. La quarantine ne contient aucun `bib_entry_before`; seul le hash global avant est conservé, contrairement à la promesse de préserver les records changés.

Options sûres:

- produire des entrées de manifestation distinctes Duckworth 1980, Cornell 1980/1983 et Chicago 2006; ou
- si un record abstrait est indispensable, utiliser un type/export explicitement work-level et rendre l'exporteur canonique reproductible.

Ajouter une quarantine courte du record BibTeX avant ne pose aucun problème de copyright.

Verdict BibTeX/quarantine: **FAIL**.

## 12. Transaction, drift et dry-run

### Rollback destructeur

Dans `transactional_replace`, le bloc d'exception appelle `restore_from_journal`, puis exécute toujours `cleanup_transaction_files` dans un `finally`. Si le rollback échoue, les sauvegardes et le journal sont donc détruits.

Reproduction en répertoire temporaire:

- échec injecté au remplacement de la seconde cible;
- échec injecté pendant sa restauration;
- état final: première cible en bytes `after`, seconde en bytes `before`;
- journal absent;
- backup absent.

Correction: ne nettoyer le journal et les backups qu'après un rollback complètement réussi. En cas d'échec de restauration, laisser le matériel durable intact pour `recover_transaction`.

Verdict transaction: **FAIL P0**.

### Registre global invalide mais statut ready

Au moment du test, deux références registry pointaient vers un artefact externe au scope Sorabji devenu absent: `scripts/apply_2026_08_24_aristotle_en_iii_5_locus_repair.py`. Résultat:

- `pytest`: 18 tests passés, 1 échec;
- `measured_baseline.registry.structurally_valid=false`;
- le CLI dry-run imprime néanmoins `status=ready_for_second_root_review` et sort avec code 0.

Même si l'artefact manquant est réparé ailleurs, le P0 Sorabji doit échouer fermé quand le baseline global est invalide. `build_plan` ou `main` doit bloquer sur `structurally_valid != true`, ainsi que sur toute nouvelle dette block/warn.

### Dry-run zéro écriture

Le test CLI ne surveille que les cibles planifiées et report/quarantine, pas tout le workspace. Le script importe des modules Python sans désactiver les `.pyc`; un vrai contrat zéro écriture devrait positionner `sys.dont_write_bytecode = True` avant les imports différés, ou définir précisément que seuls les fichiers de données sont couverts.

Verdict dry-run: **FAIL fail-closed**, malgré l'absence de mutation de données observée pendant cette revue.

## 13. Tests adversariaux à ajouter

1. `len(EIGHT_STRATEGIES) == 8`, avec huit numéros distincts dans l'ordre 1-8.
2. Le review `eight_retreats` ne peut pas passer si le tableau n'a pas huit éléments.
3. Les neuf noeuds interprétatifs previewés sont `discoverable_only` dans la policy runtime réelle.
4. Les descriptions eph-hemin et compatibilisme ne contiennent plus les formulations non attribuées signalées ci-dessus.
5. Le dog-cart n'a plus `modus_tollens`, Cleanthes comme formulator du dog, `legacy_premises` ni `verified_reference` actif.
6. `year_original=1980`, `year_edition_used=1983`, tirage local inconnu.
7. E2 est internal-only et do-not-republish; aucun runtime actif ne le consomme.
8. Le BibTeX preview est exactement celui produit par l'exporteur canonique et sa manifestation est explicite.
9. La quarantine comporte un record avant pour le BibTeX; les citations E2 longues ne sont pas dupliquées.
10. Une panne pendant le rollback conserve journal et backups et permet un second recovery.
11. Un registre global invalide force statut bloqué et code non nul.
12. Le dry-run surveille un snapshot complet des chemins autorisés ou désactive toute écriture bytecode/cache.

## 14. Portée de l'approbation après correction

Après correction des blockers, l'approbation pourra porter seulement sur:

- l'identité et le page-map du scan Cornell;
- la séparation scan/OCR et des manifestations;
- les paraphrases secondaires visuellement collationnées;
- l'attribution à Sorabji des reconstructions disputées;
- la mise en découverte seule des noeuds en attente.

Elle ne pourra pas valider:

- les sources antiques comme directement recollées;
- un consensus sur Aristote, Chrysippe, Épicure ou Alexandre;
- le tirage exact du paperback local;
- la republication du scan, de l'OCR ou des longs extraits E2;
- les quatre strands de 2017 comme présents dans le livre de 1980;
- une clôture des deux issues ouvertes ou un human signoff.

## 15. Conclusion

Le contenu secondaire est suffisamment bien collationné pour servir de base à une réparation. La proposition actuelle n'est toutefois pas transactionnellement ni sémantiquement fail-closed. Le minimum avant nouvel audit est: huit entrées réelles, citabilité `discoverable_only`, descriptions résiduelles corrigées, dog-cart nettoyé, manifest 1983, drapeaux rights E2, BibTeX reproductible/quarantiné, rollback durable et gate structurel du dry-run.

**Décision: FAIL - NO APPLY.**
