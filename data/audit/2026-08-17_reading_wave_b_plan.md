# Plan d'ingestion — reading wave B (TOP 10, items 6-10)

Date : 2026-08-17  
Périmètre : Müller 1926, Nikolaou 1977, Junod 1989, Nascimento 2020, Scheck 2008.  
Livrables : `scripts/data_2026_08_17_reading_wave_b.json`, `scripts/ingest_2026_08_17_reading_wave_b.py`, présent rapport.  
Statut : delta complet et validé dans un miroir temporaire (`BLOCK: 0`, `WARN: 0`) ; dry-run canonique en refus sûr à cause d'une erreur de syntaxe préexistante dans une dépendance du gate, décrite ci-dessous. Aucun fichier du KG ou du corpus n'a été écrit.

## Méthode et règles appliquées

- Lecture préalable de la section 6 de `data/audit/2026-08-17_cold_audit_sol.md` et de R1-R18 dans `docs/development/ingestion-rules.md`.
- Lecture depuis les cinq PDF exacts de `_acquisitions`; chaque argument porte la pagination imprimée et la page PDF physique.
- Extraction textuelle par page depuis les PDF, avec contrôle des images rendues pour les passages décisifs de Nikolaou (imprimé 391 et 394-400) et contrôle visuel des pages de titre/sommaire et des débuts de sections des cinq sources.
- Descriptions et labels argumentatifs rédigés en anglais. Aucun texte grec ou latin ancien n'a été généré ou copié dans le delta.
- R2 : recherche préalable dans `data/kg/nodes.jsonl` par noms, variantes accentuées et titres exacts. Aucun shell exact des cinq auteurs ou publications n'existe. Les mentions d'Éric Junod comme éditeur de la *Philocalie*, la notice Nascimento 2017 et le Jörn Müller 2009 existants sont des identités bibliographiques différentes.
- Réemploi exclusif des nœuds de corridor existants; aucun nœud de passage n'est créé.
- Aucune arête dialectique n'est ajoutée : `opposes=0`, `critiques=0`, `responds_to=0`, `refutes=0`, `contrasts_with=0`, `agrees_with=0`, `supports=0`.
- Chaque argument a `created_by`, `advanced_in` et au moins un `discusses` ou `cites_primary_source`; les 132 arêtes ont toutes `metadata.attested_by` avec page.
- Le JSON contient explicitement `enrichments: []`. Il n'y a aucune promotion à effectuer parce qu'aucun shell exact n'a été trouvé; aucune notice seulement voisine n'a été détournée.

## Bilan du delta

| Élément | Nombre |
|---|---:|
| personnes savantes nouvelles | 5 |
| publications lues nouvelles | 5 |
| arguments savants nouveaux | 43 |
| nœuds au total | 53 |
| arêtes au total | 132 |
| `created_by` | 43 |
| `advanced_in` | 43 |
| `discusses` | 26 |
| `cites_primary_source` | 20 |
| enrichissements/promotions | 0 |
| arêtes `opposes` nouvelles | 0 |

Les cinq publications nouvelles portent `citation_verdict: read_and_extracted`, `citation_verified: true` et un `source_rank` indiquant honnêtement lecture intégrale ou sélective.

## 6. Michael Müller, 1926

Source : `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Mueller_1926_Freiheit_Autonomie_Gnade_ZNW25.pdf`

Lecture : article intégral, imprimé 177-236, PDF physique 1-60. La p. 236 ne contient que la fin de l'article avant le début de l'article suivant; elle a bien été lue. Aucun saut.

Shells créés : `scholar_mueller_michael`; `pub_mueller_1926_freiheit_autonomie_gnade`.

### Carte argumentative (11 nœuds)

| ID | Pages imprimées / PDF | Argument description (English) | Ancrage existant |
|---|---|---|---|
| `scholarly_argument_mueller_method_formal_material_autonomy_grace` | 177-179 / 1-3 | Müller: freedom history must distinguish formal choice, material freedom, and the autonomy-grace polarity. | `concept_liberum_arbitrium_u3v4w5x6` |
| `scholarly_argument_mueller_stoic_freedom_autonomous_self_limitation` | 180-182 / 4-6 | Müller: Stoic freedom joins rational self-limitation to autonomy and excludes divine initiative. | `debate_stoic_compatibilism` |
| `scholarly_argument_mueller_paul_material_freedom_is_gracious_transfer` | 183-189 / 7-13 | Müller: Paul proclaims material freedom as a gracious transfer rather than a theory of free will. | `person_paul_apostle` |
| `scholarly_argument_mueller_pauline_parenesis_does_not_restore_autonomy` | 189-192 / 13-16 | Müller: Pauline exhortation locates responsibility inside enacted grace rather than autonomous power. | `person_paul_apostle` |
| `scholarly_argument_mueller_postpauline_parenesis_prepares_explicit_free_choice` | 195-202 / 19-26 | Müller: post-Pauline paraenesis gradually prepares the explicit doctrine of free choice. | `person_justin_martyr_2c_ce` |
| `scholarly_argument_mueller_apologists_formal_choice_responsibility_and_grace_tension` | 202-207 / 26-31 | Müller: the Apologists borrow formal choice to ground responsibility but do not recover Pauline material freedom. | `person_justin_martyr_2c_ce` |
| `scholarly_argument_mueller_irenaeus_recapitulation_coordinates_choice_and_grace` | 210-217 / 34-41 | Müller: Irenaeus uses recapitulation to coordinate free choice, grace, and salvation history. | `concept_anakephalaiosis_recapitulation` |
| `scholarly_argument_mueller_clement_defines_choice_between_opposites` | 218-221 / 42-45 | Müller: Clement defines free choice as equal power over opposed possibilities. | `person_clement_alexandria` |
| `scholarly_argument_mueller_clement_providence_and_human_cooperation` | 222-227 / 46-51 | Müller: Clement joins universal providence to active human reception without experiencing a paradox. | `concept_grace_freedom_synergy` |
| `scholarly_argument_mueller_clement_love_surpasses_apatheia_as_freedom` | 228-231 / 52-55 | Müller: Clement makes love the freedom to do good for its own sake. | `work_clement_stromateis` |
| `scholarly_argument_mueller_clement_autonomy_as_grace_led_development` | 232-236 / 56-60 | Müller: Clement's autonomy is experienced as grace and developed inwardly through the Logos. | `person_clement_alexandria` |

Décision éditoriale : les jugements très marqués de Müller sur « autonomie » et « catholicité » restent attribués à Müller dans les descriptions. Ils ne sont ni convertis en vérités du KG ni câblés comme désaccords avec des savants ultérieurs.

## 7. Theodor Nikolaou, 1977

Source : `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Nikolaou_1977_Der_Begriff_der_Freiheit_bei_Clemens.pdf`

Lecture : article intégral, imprimé 384-403, PDF physique 4-23; front matter PDF 1-3 vérifié. Contrôle des images imprimées 391 et 394-400 : la définition du choix entre contraires, l'ordre bonté/non-coercition, la distinction providence/prédétermination et la conclusion synergique correspondent à l'extraction. Les p. 401-403 sont le résumé grec de l'article; elles ont été lues pour contrôler la structure, sans en produire de texte dans le KG.

Shells créés : `scholar_nikolaou_theodor`; `pub_nikolaou_1977_willensfreiheit_clement`.

### Carte argumentative (6 nœuds)

| ID | Pages imprimées / PDF | Argument description (English) | Ancrage existant |
|---|---|---|---|
| `scholarly_argument_nikolaou_greek_and_christian_sources_form_one_problem` | 384-390 / 4-10 | Nikolaou: Clement's free-choice teaching synthesizes Greek philosophical and Christian sources. | `person_clement_alexandria` |
| `scholarly_argument_nikolaou_free_choice_requires_genuine_alternatives` | 390-393 / 10-13 | Nikolaou: Clementine free choice is genuine selection between good and evil, not obedience alone. | `concept_liberum_arbitrium_u3v4w5x6` |
| `scholarly_argument_nikolaou_will_primes_intellect_and_action` | 392-395 / 12-15 | Nikolaou: Clement gives willing primacy among the ruling faculty's powers. | `person_clement_alexandria` |
| `scholarly_argument_nikolaou_commands_activate_dispositions_and_virtue` | 394-396 / 14-16 | Nikolaou: commands activate created dispositions but virtue still requires self-moved acquisition. | `work_clement_stromateis` |
| `scholarly_argument_nikolaou_divine_goodness_gives_without_coercion` | 397-398 / 17-18 | Nikolaou: divine goodness offers salvation without using omnipotence to compel acceptance. | `person_clement_alexandria` |
| `scholarly_argument_nikolaou_providence_foreknowledge_and_synergy` | 399-400 / 19-20 | Nikolaou: Clement distinguishes providence from predetermination and ends in grace-first synergy. | `concept_synergism` |

Décision éditoriale : la longue préhistoire philosophique p. 386-390 n'est pas éclatée en nœuds sur chaque école; elle sert uniquement à qualifier la méthode de Nikolaou. Sa comparaison Orient/Occident p. 398-400 est conservée seulement dans la mesure où elle définit sa lecture synergique de Clément.

## 8. Éric Junod, 1989

Source : `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Junod_1989_Des_apologetes_a_Origene_theologie_critique_RTP121.pdf`

Lecture : article intégral, imprimé 149-164, PDF physique 2-17; couverture de dépôt PDF 1 vérifiée. Aucun saut.

Shells créés : `scholar_junod_eric`; `pub_junod_1989_apologetes_origene_theologie_critique`.

### Carte argumentative (6 nœuds)

| ID | Pages imprimées / PDF | Argument description (English) | Ancrage existant |
|---|---|---|---|
| `scholarly_argument_junod_critical_theology_is_historically_bounded` | 149-152 / 2-5 | Junod: patristic critical theology means rational traditional inquiry, not modern foundational critique. | `person_origen_alexandria_185_254ce_s9t0u1v2` |
| `scholarly_argument_junod_apologetic_demonstration_becomes_origenian_examination` | 153-156 / 6-9 | Junod: the Apologists' demonstration becomes examination with Clement and especially Origen. | `person_clement_alexandria` |
| `scholarly_argument_junod_peri_archon_programs_internal_systematic_inquiry` | 156-158 / 9-11 | Junod: the preface to On First Principles programs an internal inquiry into doctrinal coherence. | `work_de_principiis_origen_230s_v2w3x4y5` |
| `scholarly_argument_junod_origenian_theology_answers_gnostic_intellectual_demand` | 158-159 / 11-12 | Junod: Origenian critical theology answers the Gnostic challenge on the terrain of rigorous knowledge. | `debate_christian_gnostic_freedom` |
| `scholarly_argument_junod_origen_critiques_church_through_knowledge_and_holiness` | 159-162 / 12-15 | Junod: Origen relativizes external hierarchy by the internal hierarchy of knowledge and holiness. | `person_origen_alexandria_185_254ce_s9t0u1v2` |
| `scholarly_argument_junod_church_commitment_displaces_civic_program` | 162-164 / 15-17 | Junod: Origen prioritizes building the Church over reforming civil society. | `person_origen_alexandria_185_254ce_s9t0u1v2` |

Décision éditoriale : la mention du libre choix chez les Apologètes p. 155 reste un élément du passage démonstration/examen; elle n'est pas artificiellement transformée en étude doctrinale du libre arbitre. Les deux sections Église/société sont retenues parce qu'elles sont les conséquences explicites de la méthode théologique étudiée par Junod.

## 9. Sidnei Francisco do Nascimento, 2020

Source : `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Nascimento_2020_Livre_arbitrio_Origenes_Hypnos45.pdf`

Lecture : article intégral, imprimé 236-253, PDF physique 1-18. Aucun saut.

Shells créés : `scholar_nascimento_sidnei_francisco_do`; `pub_nascimento_2020_livre_arbitrio_origenes_antignostica`.

### Carte argumentative (5 nœuds)

| ID | Pages imprimées / PDF | Argument description (English) | Ancrage existant |
|---|---|---|---|
| `scholarly_argument_nascimento_anti_gnostic_free_choice_is_moral_not_natural` | 236-239 / 1-4 | Nascimento: Origenian free choice is inseparable from moral action against salvation by nature. | `person_origen_alexandria_185_254ce_s9t0u1v2` |
| `scholarly_argument_nascimento_impressions_do_not_determine_rational_judgment` | 242-243 / 7-8 | Nascimento: external impressions do not determine the rational judgment that depends on us. | `concept_liberum_arbitrium_u3v4w5x6` |
| `scholarly_argument_nascimento_valentinian_natures_displace_moral_deliberation` | 245-247 / 10-12 | Nascimento: Valentinian natural classes displace free choice as rational moral deliberation. | `person_valentinus_gnostic_2c_ce` |
| `scholarly_argument_nascimento_stars_are_signs_not_causes` | 247-249 / 12-14 | Nascimento: Origen treats stars as signs rather than causes and makes fatalism self-defeating. | `work_origen_philocalia` |
| `scholarly_argument_nascimento_inner_conflict_foreknowledge_and_providence` | 249-251 / 14-16 | Nascimento: inner conflict locates choice in the soul while foreknowledge remains non-causal. | `work_de_principiis_origen_230s_v2w3x4y5` |

Pages lues mais non modélisées : 240-241 donnent le cadre platonicien/stoïcien général sans thèse atomique supplémentaire pour le corridor; 251-252 développent la réception hérésiologique tardive et plusieurs généralisations sur Nicée et la première crise origéniste, qui exigeraient une enquête distincte; 253 est la bibliographie. Ce choix évite une pertinence forcée.

## 10. Thomas P. Scheck, 2008

Source : `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Scheck_2008_Origen_History_of_Justification.pdf`

Lecture principale : introduction imprimée 1-12 (PDF 14-25) et chapitre 1 intégral 13-62 (PDF 26-75).  
Lectures ciblées supplémentaires : 66-74 (PDF 79-87), 96-103 (PDF 109-116), 123-126 (PDF 136-139).  
Le titre, l'ISBN et le sommaire ont été contrôlés sur les PDF 1-7.

Shells créés : `scholar_scheck_thomas_p`; `pub_scheck_2008_origen_history_justification`.

### Carte argumentative (15 nœuds)

| ID | Pages imprimées / PDF | Argument description (English) | Ancrage existant |
|---|---|---|---|
| `scholarly_argument_scheck_commentary_unique_justification_source` | 13-20 / 26-33 | Scheck: Origen's Commentary on Romans is the exceptional sustained patristic source on justification. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_judgment_entails_freedom_merit_without_boasting` | 20-23 / 33-36 | Scheck: anti-Gnostic polemic makes freedom and recompense follow from just judgment without licensing boasting. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_marcion_polemic_unites_goodness_judgment_and_works` | 23-29 / 36-42 | Scheck: Origen's anti-Marcion polemic unites divine goodness, just judgment, and the value of works. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_romans_salvation_history_and_jew_gentile_equality` | 30-32 / 43-45 | Scheck: Origen reads Romans through salvation history and the equal need of Jews and Gentiles for mercy. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_justification_is_indwelling_trinitarian_grace` | 32-35 / 45-48 | Scheck: Origen conceives justification as indwelling, Trinitarian, transformative grace. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_grace_forgives_fulfills_law_and_sanctifies` | 35-38 / 48-51 | Scheck: justifying grace forgives past sins, fulfills the law in the believer, and sanctifies the soul. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_christ_redemption_precedes_faith_baptism_and_can_be_rejected` | 38-42 / 51-55 | Scheck: Christ's independent redemptive act grounds justification received by faith and baptism. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_postbaptismal_works_merit_under_christ_blood` | 41-45 / 54-58 | Scheck: faith-alone examples exclude prior works, while later meritorious works remain subordinate to Christ's blood. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_faith_root_works_fruit_justification_process` | 45-48 / 58-61 | Scheck: Origen relates faith and works organically as root and fruit in a progressive justification. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_works_of_law_not_moral_renewal` | 48-53 / 61-66 | Scheck: Origen excludes ceremonial works of the law, not moral renewal, from justification. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_grace_free_choice_tension_resists_simple_semipelagian_label` | 53-58 / 66-71 | Scheck: Origen's grace and free-choice texts form a real tension that resists a simple semi-Pelagian label. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_merit_is_not_strict_debt` | 59-62 / 72-75 | Scheck: Origenian merit is fitness for further gift, not strict debt owed by God. | `work_origen_commentary_romans` |
| `scholarly_argument_scheck_pelagius_receives_origen_free_choice_with_historical_caveat` | 66-74 / 79-87 | Scheck: Pelagius receives Origen's free-choice exegesis, but omission of grace is not by itself a denial. | `work_origen_commentary_romans`; `person_pelagius_d420` |
| `scholarly_argument_scheck_augustine_selectively_receives_commentary_faith_works` | 96-103 / 109-116 | Scheck: Augustine selectively receives Origen's faith-and-works exegesis while diverging on Romans 5, 7, and 9. | `work_origen_commentary_romans`; `person_augustine_hippo_d430` |
| `scholarly_argument_scheck_william_inserts_prevenient_grace_into_origen` | 123-126 / 136-139 | Scheck: William of St. Thierry inserts prevenient grace into Origen's free-choice exegesis. | `work_origen_commentary_romans`; `concept_gratia_praeveniens` |

### Sections sautées et raisons

- Chapitre 2, 63-65 et 75-85 : introduction au dossier de Pélage, transmission du péché et synthèse générale; hors du sous-dossier demandé après lecture ciblée de 66-74.
- Chapitre 3, 86-95 : traçage textuel de l'usage d'Origène par Augustin; hors du noyau grâce/mérite après lecture ciblée de 96-103.
- Chapitre 4, 104-122 et 127-128 : réception médiévale générale et péché originel; seule la section explicite « Grace and the Free Choice of the Will », 123-126, a été retenue.
- Chapitre 5, 129-172 : réception par Érasme; hors corridor demandé.
- Chapitre 6, 173-204 : Luther et Melanchthon; utile pour une future histoire de la réception, mais non nécessaire pour extraire les positions de Scheck sur le *Commentaire sur Romains*, le libre choix, la grâce et le mérite.
- Chapitre 7, 205-216 : controverses post-réformées; même motif.
- Conclusion 217-220 et appareils 221-fin : utilisés seulement pour navigation et contrôle bibliographique; aucune nouvelle unité argumentative du corridor.

Cette sélection est enregistrée dans `metadata.reading_scope` et `metadata.skipped_sections` de la publication; elle ne prétend pas à une lecture intégrale de la monographie.

## Câblage au corridor et passages existants

Nœuds anciens ou conceptuels réutilisés notamment :

- `person_clement_alexandria`, `work_clement_stromateis`;
- `person_origen_alexandria_185_254ce_s9t0u1v2`, `work_de_principiis_origen_230s_v2w3x4y5`, `work_origen_philocalia`, `work_origen_commentary_romans`;
- `person_paul_apostle`, `person_justin_martyr_2c_ce`, `person_irenaeus_d202`, `person_tatian`, `person_valentinus_gnostic_2c_ce`, `person_marcion_sinope_2c_ce` lorsque les pages l'attestent;
- `concept_liberum_arbitrium_u3v4w5x6`, `concept_grace_freedom_synergy`, `concept_synergism`, `concept_gratia_praeveniens`, `debate_christian_gnostic_freedom`, `debate_divine_foreknowledge_235f2530`, `debate_stoic_compatibilism`.

Contrôle des loci du *Commentaire sur Romains* présents dans le KG :

- `passage_origen_com_rm_7_16` et sa traduction anglaise;
- `passage_origen_com_rm_7_16_sun` et sa traduction anglaise.

Ce sont les seules unités passage reliées à `work_origen_commentary_romans`. Les analyses de Scheck embrassent de nombreux autres loci de Romains 1-12, et sa discussion de Romains 7/9 n'est pas réductible aux deux unités VII.16 existantes. Par honnêteté, les arêtes pointent donc vers l'œuvre `work_origen_commentary_romans`, jamais vers un passage approximatif. Aucun passage n'est créé.

## Promotions et enrichissements

Résultat R2 : aucune publication exacte avec `citation_verdict: bibliographic_import` n'a été trouvée pour les cinq titres. Donc :

- promotions `bibliographic_import -> read_and_extracted` : 0;
- réécritures `source_rank` sur nœud existant : 0;
- `enrichments` : tableau vide explicite.

La notice `pub_do_2017_comentario_de_origenes_espistola_aos_romanos_origen_commentary_o` est un article différent de Nascimento (2017) et reste intacte. Les notices de comptes rendus de la *Philocalie* mentionnant Junod ne sont pas l'article Junod 1989 et restent intactes. Le `scholar_muller_j` existant est Jörn Müller, non Michael Müller.

## Vérifications et sorties

### Structure locale

```text
$ python3 -m py_compile scripts/ingest_2026_08_17_reading_wave_b.py
[exit 0]

$ python3 -m json.tool scripts/data_2026_08_17_reading_wave_b.json
[exit 0]

$ jq -e 'all(.nodes[]; .id == .node_id and (.metadata.provenance.source|endswith(".pdf"))) and all(.edges[]; .source == .source_id and .target == .target_id)' scripts/data_2026_08_17_reading_wave_b.json
true
```

### Gate R1-R18 sur miroir temporaire

Le gate canonique importe `graphrag/src/eleutheria_graphrag/agents/dialectical_relations.py`. Ce fichier préexistant contient actuellement à la ligne 42 `except TypeError, ValueError:`, syntaxe invalide sous Python 3. Pour distinguer l'état du delta de ce défaut externe, une copie temporaire du gate et de cette dépendance a été exécutée avec l'unique correction syntaxique `except (TypeError, ValueError):`; les données, ontologies et fichiers KG sont restés ceux du dépôt par liens en lecture seule.

```text
$ python3 /tmp/eleutheria-reading-wave-b-gate.../scripts/check_ingestion_rules.py --new-only /tmp/eleutheria-reading-wave-b-gate.../subset.json
ingestion-rules: delta of 53 nodes / 132 edges
  no violations

BLOCK: 0   WARN: 0
```

### Dry-run canonique

```text
$ python3 scripts/ingest_2026_08_17_reading_wave_b.py
delta: 53 nodes / 132 edges / 0 enrichments
novel: 53 nodes / 132 edges (skipped existing: 0 nodes, 0 edges)
enrichments: enrichable=0, already-applied=0
opposes: current=21, novel=0, post-apply=21, g6-pin-check=not-required
Traceback ...
  File "graphrag/src/eleutheria_graphrag/agents/dialectical_relations.py", line 42
    except TypeError, ValueError:
SyntaxError: multiple exception types must be parenthesized
FATAL: ingestion gate failed - nothing written
```

Le refus est le comportement attendu du script : aucun write n'est possible si le gate canonique ne s'exécute pas. La règle « fichiers additifs seulement » interdit à cette vague de corriger la dépendance existante. Dès que cette ligne sera réparée par son propriétaire, le dry-run canonique devra reproduire `BLOCK: 0 / WARN: 0` avant toute application.

### Dry-run complet sur miroir temporaire

Le même applier a été copié dans le miroir temporaire avec le même JSON, les mêmes données live et les mêmes ontologies. Seule la dépendance syntaxiquement invalide du gate y porte les parenthèses Python requises.

```text
$ python3 /tmp/eleutheria-reading-wave-b-gate.../scripts/ingest_2026_08_17_reading_wave_b.py
delta: 53 nodes / 132 edges / 0 enrichments
novel: 53 nodes / 132 edges (skipped existing: 0 nodes, 0 edges)
enrichments: enrichable=0, already-applied=0
opposes: current=21, novel=0, post-apply=21, g6-pin-check=not-required
ingestion-rules: delta of 53 nodes / 132 edges
  no violations

BLOCK: 0   WARN: 0
dry-run: nothing written (use --apply)
```

## État d'écriture et sécurité

- Aucun `--apply` exécuté.
- Aucun fichier sous `data/kg` ou `data/corpus` modifié.
- Aucun fichier de la vague A touché.
- Aucun `git` exécuté.
- Fichiers ajoutés uniquement : le JSON, l'applier et ce plan.
- Compteur G6 : 21 `opposes` existants, 0 nouveau, 21 après application hypothétique; aucune modification du pin n'est requise. Si un futur amendement ajoute un `opposes`, l'applier lit le pin et refuse `--apply` tant que le compte post-application ne lui correspond pas.
