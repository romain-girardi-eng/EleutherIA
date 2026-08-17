# Plan d’import Origenality — couche secondaire sur Origène — 17 août 2026

## Statut et périmètre

Ce livrable est strictement préparatoire : le delta n’a pas été appliqué. Il porte la tranche des notices dont `themes` contient `anthropology.free-will` ou `cosmos.providence-and-evil` et dont `relevance` vaut `core` ou `section`.

La vague fournie contient **260 notices dans cette tranche**, toutes classées `core`; elle ne contient aucune valeur `section` (le vocabulaire observé est `core|partial|marginal|none`). L’estimation « ~283 » n’est donc pas reproduite par l’état exact des fichiers du 17 août 2026. Aucune pertinence n’a été réinterprétée ni adjugée.

## Jointure `notice_id` → grappe bibliographique

`semantic/tag_notices.py::notice_identifier` prend `origenality_id` en priorité. `semantic/tags_io.py::read_tags` impose la dernière occurrence pour un même `notice_id`; la vague courante compte 21104 lignes, 21104 identifiants uniques et 0 ligne périmée. `semantic/remap_tag_ids.py` confirme que les reports ultérieurs réécrivent `notice_id` vers l’`origenality_id` successeur.

Résultat de réconciliation : **21104/21104 tags** trouvent leur grappe dans `data/merged/corpus.jsonl`; dans la tranche, **260/260**. Pour l’année et la langue, le plan reprend les fonctions fédérales `pipeline/fields.py::norm_year` (`year`, puis plus ancienne `year_bib_parsed`, puis `publication_date`) et `norm_lang`.

## Résultat de la déduplication et plan d’action

- Notices de tranche : **260**.
- Correspondances KG certaines : **14 notices vers 10 nœuds existants**; aucun nouveau nœud pour elles.
- Doublons internes résiduels du corpus, regroupés avant création : **6 notices excédentaires dans 6 groupes**.
- Publications nouvelles proposées : **198**.
- Enrichissements proposés : **10**.
- Cas `needs_review` sans création : **42**, dont 2 correspondances limites.
- Arêtes proposées : **440**; aucune arête dialectique.

Le score compare uniquement des candidats de même année et de patronyme normalisé compatible. Une correspondance est certaine à partir de 0.92; la bande [0.65, 0.92[ est laissée en revue. Les enrichissements ajoutent les identifiants Origenality, les tags et les mesures de citation disponibles. Un résumé ne serait ajouté à un nœud existant que si sa description est vide ou équivalente au titre; ce cas concerne **2** cible ici.

### Correspondances certaines avec le KG

| Nœud existant | origenality_id | similarité titre |
| --- | --- | --- |
| pub_belcastro_predestinazione_origene | OR13587ab49523 | 1.00 |
| pub_benjamins_1994_eingeordnete_freiheit | ORa8ca0484bcc3, ORea5a44fdbd35 | 1.00, 1.00 |
| pub_furst_2019_concepts_origenism_ad13 | OR4bfc6e4113c6 | 1.00 |
| pub_furst_2022_wege_freiheit | OR1460103d8053, OR907a03c8b43a | 1.00, 1.00 |
| pub_hengstermann_2016_freiheitsmetaphysik | OR009fce0fde5e, ORb1b61c0ae365 | 1.00, 1.00 |
| pub_koch_1932_pronoia | OR08f634210511, OR283fb95266e3 | 1.00, 1.00 |
| pub_schockenhoff_1990_fest_freiheit | ORd08c32c5b654 | 1.00 |
| pub_sytsma_2020_universal_salvation_origen | OR88257bc3c4d9 | 1.00 |
| scholarly_work_gibbons_2016_human_autonomy_and_its_limits_in_the_tho | ORd60f75289777 | 1.00 |
| scholarly_work_hall_2021_origen_and_prophecy_fate_authority_alleg | OR4d90beaaf27b | 1.00 |

### Doublons internes regroupés

| origenality_id regroupés | résultat |
| --- | --- |
| OR1d21036b44bc, ORc00aef8de00e | 1 publication nouvelle |
| OR1f25087db93b, ORfa23e60a3954 | 1 publication nouvelle |
| OR5285735a81f3, OR5a485c1c4a15 | 1 publication nouvelle |
| OR72a6237a4cda, ORec7335aaa934 | 1 publication nouvelle |
| ORacacab5d9cf7, ORe5b425889db6 | 1 publication nouvelle |
| ORcf88d1555f09, ORe02a0b497750 | 1 publication nouvelle |

## Comptages de la tranche avant déduplication

Les appartenances thématiques se chevauchent : 23 notices portent les deux thèmes.

| Dimension | Valeur | Nombre |
| --- | --- | --- |
| Thème (appartenance, chevauchement permis) | anthropology.free-will | 206 |
| Thème (appartenance, chevauchement permis) | cosmos.providence-and-evil | 77 |
| Pertinence | core | 260 |
| Décennie | 1890s | 1 |
| Décennie | 1930s | 4 |
| Décennie | 1960s | 1 |
| Décennie | 1970s | 8 |
| Décennie | 1980s | 6 |
| Décennie | 1990s | 32 |
| Décennie | 2000s | 38 |
| Décennie | 2010s | 71 |
| Décennie | 2020s | 86 |
| Décennie | indéterminée | 13 |
| Langue harmonisée | ? | 56 |
| Langue harmonisée | cs | 1 |
| Langue harmonisée | de | 36 |
| Langue harmonisée | el | 1 |
| Langue harmonisée | en | 76 |
| Langue harmonisée | es | 4 |
| Langue harmonisée | fr | 48 |
| Langue harmonisée | hr | 1 |
| Langue harmonisée | it | 27 |
| Langue harmonisée | ja | 1 |
| Langue harmonisée | la | 2 |
| Langue harmonisée | nl | 1 |
| Langue harmonisée | no | 1 |
| Langue harmonisée | pl | 1 |
| Langue harmonisée | pt | 1 |
| Langue harmonisée | ru | 1 |
| Langue harmonisée | sv | 1 |
| Langue harmonisée | tr | 1 |

## Modèle des nœuds et honnêteté épistémique

Chaque publication nouvelle porte `citation_verdict: bibliographic_import` et le `source_rank` obligatoire « unread bibliographic record imported from the Origenality federation — metadata verified against the source catalogues, content not yet read ». La description reprend seulement le résumé attribué de la base donatrice, ou à défaut le titre bibliographique; aucune thèse savante, lecture, adjudication ni texte grec/latin n’est produit. Les tags techniques `source_model`, `auto_generated` et les justifications de classification ne sont pas importés.

Le champ `authors` suffit lorsque l’auteur ne correspond pas exactement et sans ambiguïté à un nœud savant existant. Aucun nœud de personne n’est créé. Les seules arêtes `authored_by` sont fondées sur une égalité exacte des noms normalisés vers un unique nœud `scholar_*` existant : **27 liens vers 13 savants** (scholar_benjamins_hendrik_s, scholar_furst_alfons, scholar_gibbons_k, scholar_hall_c, scholar_hengstermann_christian, scholar_jacobsen_a, scholar_kobusch_theo, scholar_louth_a, scholar_muller_j, scholar_perrone_l, scholar_ramelli_ilaria, scholar_rist_john, scholar_sytsma_lee).

## Arêtes et table explicite thème → concept

Chaque publication nouvelle discute `person_origen_alexandria_185_254ce_s9t0u1v2` (« Origen of Alexandria »). Les deux seules projections conceptuelles sont :

| Thème Origenality | Identifiant KG vérifié | Libellé KG |
| --- | --- | --- |
| anthropology.free-will | concept_autexousion_christian_freedom_u1v2w3x4 | Autexousion (Αὐτεξούσιον) - Christian Free Will |
| cosmos.providence-and-evil | concept_theodicy_christian | Christian Theodicy |

Pour `cosmos.providence-and-evil`, le KG ne possède pas de concept générique neutre « Providence » : les autres candidats sont propres au judaïsme, à Clément, au stoïcisme, à Boèce ou à Proclus. `concept_theodicy_christian` est donc le seul concept chrétien général qui couvre explicitement le problème providence/mal sans ajouter une tradition particulière. Aucune arête `opposes`, `agrees_with`, `critiques` ou autre relation dialectique n’est créée.

## Résumés, droits et provenance

Les faits bibliographiques sont repris comme métadonnées. Tout résumé conservé porte simultanément :

- le nom lisible de la base dans `abstract_source` et son code dans `abstract_source_id`;
- `abstract_rights` inchangé;
- un `abstract_url` résolu selon la table de `DATA_POLICY.md` vers la notice donatrice;
- les catalogues et identifiants sources dans `metadata.provenance.source_records`.

Les 148 résumés portés par les nouveaux nœuds se répartissent ainsi :

| Base donatrice | Résumés |
| --- | --- |
| GIROTA / Adamantius | 20 |
| BIBP — Université Laval | 5 |
| Crossref | 10 |
| ISIDORE (Huma-Num) | 7 |
| Index Theologicus (IxTheo / K10plus) | 11 |
| OpenAlex | 90 |
| Semantic Scholar | 4 |
| theses.fr | 1 |

Les percentiles disponibles (`cohort_rank`) sont portés comme `citation_percentile` avec le détail de cohorte, sans transformer la mesure en jugement de contenu : **118 publications nouvelles** et **6 enrichissements** en disposent.

## Huit exemples du delta

| origenality_id | Nœud/action | Auteur | Année | Titre | Thème de tranche | Langue | Source du résumé |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OR7aae5b708182 | pub_achternkamp_2019_natural_law_in_origen_anthropology | Achternkamp, Anne | 2019 | Natural Law in Origen's Anthropology | anthropology.free-will | en | Index Theologicus (IxTheo / K10plus) |
| OR9f3fdc608a5d | pub_alviar_2022_origen_theological_anthropology | J. José Alviar | 2022 | Origen’s Theological Anthropology | anthropology.free-will | en | Crossref |
| OR411d3ea68cd1 | pub_arfe_2009_servano_da_segni_gen_14_la_confutazione_del_fatalismo_astrologic | Pasquale Arfé | 2009 | “E servano da segni” (Gen. 1,14). La confutazione del fatalismo astrologico nel Commento a Genesi di Origene | anthropology.free-will | it | OpenAlex |
| OR00e328cdfb35 | pub_aubineau_1978_origene_philocalie_21_27_sur_le_libre_arbitre_introduction_texte | Michel Aubineau | 1978 | Origène. Philocalie 21-27 : Sur le Libre arbitre. Introduction, Texte, Traduction et Notes par E. Junod (Sources Chrétiennes, 226) | anthropology.free-will | fr | OpenAlex |
| OR3ecd5e5f49b8 | pub_arruzza_2009_le_refus_du_bonheur_negligence_et_chute_dans_la_pensee_origene | Cinzia Arruzza | 2009 | Le refus du bonheur : négligence et chute dans la pensée d'Origène | cosmos.providence-and-evil | fr | OpenAlex |
| OR29af50b40a37 | pub_barilli_2012_lexis_paidike_infanzia_in_origene | Chiara Barilli | 2012 | Lexis paidike. L'infanzia in Origene | anthropology.free-will, cosmos.providence-and-evil | it | OpenAlex |
| OR96b92b419c2d | pub_benjamins_1993_eingeordnete_freiheit_freiheit_und_vorsehung_bei_origenes | Benjamins, Hendrik S | 1993 | Eingeordnete Freiheit : Freiheit und Vorsehung bei Origenes | anthropology.free-will, cosmos.providence-and-evil | de | — |
| OR5aec92f77151 | pub_bennett_1997_the_origin_of_evil_didymus_the_blind_contra_manichaeos_and_its_d | Bennett, John Byard | 1997 | The origin of evil : Didymus the Blind's "Contra Manichaeos" and its debt to Origen's theology and exegesis | cosmos.providence-and-evil | en | — |

## `needs_review` — aucune création

| origenality_id | Auteur(s) | Année | Titre | Motif |
| --- | --- | --- | --- | --- |
| OR07275b84268e | Arnold, Johannes | — | Zur Frage nach dem Ursprung des Bösen im Menschen bei Origenes vor dem Hintergrund mittelplatonischer Philosophie / Johannes Arnold | année bibliographique absente; R10 interdit de l'inventer |
| OR0ca916bb5ee8 | — | 2002 | Libre arbitre et notion origénienne du Logos | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR0deb1d253d2c | Fernández Eyzaguirre, Samuel | — | Objeciones al Libre Albedrío según Orígenes en De principiis 3., 1 / Samuel Fernández E. | année bibliographique absente; R10 interdit de l'inventer |
| OR1f7be03021b8 | Foucault, Michel | — | Origène. La responsabilité des pasteurs | année bibliographique absente; R10 interdit de l'inventer |
| OR210533e56a6e | Osborn, Eric | — | Causality in Plato and Origen / Eric Osborn | année bibliographique absente; R10 interdit de l'inventer |
| OR24e8ed2a1f63 | Kolloquien zum Nachleben des Origenes | 2019 | Origen's philosophy of freedom in early modern times : debates about free will and apokatastasis in 17th-century England and Europe / edited by Alfons Fürst | collectivité de colloque encodée comme auteur; identité à revoir |
| OR30307bef8c50 | Kobusch, Theo | — | Die Idee der Freiheit : Origenes und der neuzeitliche Freiheitsgedanke / Theo Kobusch. | année bibliographique absente; R10 interdit de l'inventer |
| OR33a224a2f287 | Hengstermann, Christian | — | Die Seele zwischen Tier und Gott : die origeneische Freiheitsanthropologie bei Erasmus von Rotterdam / Christian Hengstermann. | année bibliographique absente; R10 interdit de l'inventer |
| OR3bc405d73f56 | Fürst, Alfons | — | Autonomie und Menschenwürde : Die origeneische Tradition / Alfons Fürst. | année bibliographique absente; R10 interdit de l'inventer |
| OR421a3ee9f7e5 | — | 2020 | CHAPTER THREE. ORIGEN’S STAGES OF SALVATION-HISTORY | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR427ae7d46130 | — | 2020 | BIBLIOGRAPHY | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR4ddfce09bad7 | Буланов Станислав Леонидович | 2019 | ТРАКТАТ «О НАЧАЛАХ» КАК ОПЫТ ТЕОДИЦЕИ | nom non latin sans translittération attestée; aucun patronyme ASCII n'est inventé pour l'identifiant |
| OR4e67951f8e4c | — | 2017 | Origen of Alexandria | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR50b27f675db6 | Schockenhoff, Eberhard | — | Zum Fest der Freiheit : Theologie des christlichen Handelns bei Origenes / Eberhard Schockenhoff | année bibliographique absente; R10 interdit de l'inventer |
| OR51b0616bfd73 | Kolloquien zum Nachleben des Origenes | 2019 | Freedom as a key category in Origen and in modern philosophy and theology / edited by Alfons Fürst | collectivité de colloque encodée comme auteur; identité à revoir |
| OR555cd42d7049 | Franchi, Roberta | — | L' influenza di Origene nel De libero arbitrio e nel De creatis di Metodio d'Olimpo / Roberta Franchi | année bibliographique absente; R10 interdit de l'inventer |
| OR574f0b0a7cdd | 一雄 多井 | 1975 | Origenesにおけるτο αυτεξουσιονに関する一考察 | nom non latin sans translittération attestée; aucun patronyme ASCII n'est inventé pour l'identifiant |
| OR595d366828bd | — | 2011 | Origenes Theologie der Freiheit | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR5f2e2d3f0e70 | — | 2026 | 421The Legacy of Origen in Gregory of Nyssa’s Theology of Freedom | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR644bb889c5f0 | Hal Koch | 1932 | Kap. I. πρόνοια und παίδευσις bei Origenes | correspondance KG limite → pub_koch_1932_pronoia (score 0.7500) |
| OR64bf6b8fdb78 | — | 2011 | § 3. Die Erziehung als Leitmotiv in Origenes' Äußerungen zur Pronoia Gottes? Ansätze des Origenes zur richterlich-distributiv verstandenen Pronoia. Teil 2 | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR6560670d9b03 | — | 2020 | INDEX | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR7344876f75bc | — | 2001 | Reviews | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| OR7ebfceddc55f | Fürst, Alfons | — | Origen's legacy to modern thinking about freedom and autonomy / Alfons Fürst | année bibliographique absente; R10 interdit de l'inventer |
| OR804ebaaa5e16 | 안수배 | 2024 | Origen's Thoughts on Human 'Free Will’: In Relation to Gnosticism and God's Providence | nom non latin sans translittération attestée; aucun patronyme ASCII n'est inventé pour l'identifiant |
| OR825424ed1a4b | Solheid, John C. | — | Freedom and Constraint : Emergent Properties from Origen's School in Caesarea Maritima / John C. Solheid | année bibliographique absente; R10 interdit de l'inventer |
| OR86ee1c17be16 | — | 2002 | Libre arbitre et notion origénienne de la volonté | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORb59954dfaf02 | — | 2020 | CHAPTER FIVE. GOD’S PROVIDENTIAL ARRANGEMENT OF FUTURE VOLUNTARY POSSIBILITIES | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORb994ae77324c | — | 1977 | Review | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORbc6dd11d5f49 | — | 2020 | CHAPTER ONE. THE CONTEXT OF ORIGEN’S MORAL AUTONOMY POLEMICS | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORbd2c69518186 | Fürst, Alfons | — | Vernunft und Freiheit : Pico della Mirandolas Verteidigung der Origenes / Alfons Fürst | année bibliographique absente; R10 interdit de l'inventer |
| ORc34061e84407 | Hengstermann, Christian | — | Der Kosmos als Freiheit und Geschichte : Picos Origenismus in Heptaplus / Christian Hengstermann | année bibliographique absente; R10 interdit de l'inventer |
| ORcff89958d434 | — | 2002 | Libre arbitre et notion origénienne de corporéité | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORd4dc0036903e | — | 2014 | “Evil is not a Nature” : Origen on Evil and the Devil | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORdb41c1f01a38 | — | 2020 | CHAPTER FOUR. ORIGEN’S VISION OF THE APOCATASTASIS | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORdf55b0ec8fb0 | Haley Benjamins | 1994 | ENTSCHEIDUNGSFREIHEIT UND VORSEHUNG BEI ORIGENES UND DEN GRIECHISCHEN PHILOSOPHEN | correspondance KG limite → pub_benjamins_1994_eingeordnete_freiheit (score 0.7027) |
| ORe50bad462b54 | — | 2020 | INTRODUCTION | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORf035d8de4789 | — | 2012 | Autonomie und Menschenwürde : Origenes in der Philosophie der Neuzeit / herausgegeben von Alfons Fürst und Christian Hengstermann | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORf76563df6732 | — | 2020 | CHAPTER TWO. ORIGEN’S UNDERSTANDING OF MORAL AUTONOMY | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORfa58a77c0771 | — | 2019 | Chapter Seven An Early Christian View on a Free Will: Origen | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORfb89bfb23568 | — | 2020 | TABLE OF CONTENTS | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |
| ORfde013082517 | — | 2011 | § 3. Die Erziehung als Leitmotiv in Origenes' Äußerungen zur Pronoia Gottes? Ansätze des Origenes zur richterlich-distributiv verstandenen Pronoia. Teil 1 | auteur absent ou seulement collectivité/rôle non auteur; impossible de former l'identité R2 |

## Appliqueur et invariants

`scripts/ingest_2026_08_17_origenality_import.py` est en dry-run par défaut. `--apply` est la seule voie d’écriture. Avant toute écriture il : vérifie les préconditions `type`, `label` et `metadata.year` de chaque cible d’enrichissement; refuse les collisions d’identifiants; résout toutes les extrémités; contrôle les doublons de triplets; vérifie les marqueurs d’honnêteté et l’attribution de chaque résumé; construit le sous-ensemble réellement nouveau; exécute `check_ingestion_rules.py --new-only`; refuse tout `BLOCK`; prépare les deux fichiers complets; puis seulement crée les sauvegardes `.bak-origenality` et remplace les JSONL. Une seconde exécution reconnaît les nœuds, arêtes et enrichissements déjà présents et les saute.

## Vérifications obligatoires

### Gate R1–R17 sur le sous-ensemble nouveau

```text
À renseigner après exécution.
```

### Dry-run de l’appliqueur

```text
À renseigner après exécution.
```

### Périmètre des écritures, intégrité des graphes et lecture seule de la source

```text
À renseigner après vérification finale.
```
