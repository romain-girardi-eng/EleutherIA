# Plotin : texte grec décalé par rapport au locus — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_plotinus_locus_drift.py` (646 items, avec pour chacun le locus revendiqué et l'emplacement réel du texte stocké) et `scripts/apply_2026_09_24_plotinus_locus_drift.py`.
Décisions : `data/audit/2026-09-24_plotinus_locus_drift_decisions.jsonl` (647 enregistrements). Quarantaine : `data/audit/2026-09-24_plotinus_locus_drift_quarantine.jsonl` (1 citation).
Source de contrôle : R. Volkmann, *Plotini Enneades*, Leipzig, Teubner, 1883-1884. Le TEI utilisé est `tlg2000.tlg001.1st1K-grc1` (OpenGreekAndLatin/First1KGreek, commit `8ee111eb`), dont le SHA-256 est épinglé dans le module de données.

## Le défaut

Deux lignes de la file C3 ont conduit au défaut : `concept_plotinian_intellectual_eph_hemin → passage_plotinus_iii_1_8` et `concept_sympatheia_universal_posidonius_nyssa → passage_plotinus_iii_1_7`, avec p = 0,17 et 0,12. Le texte stocké sous « Enn. III.1.7 » n'est pas III.1.7 : c'est la fin de II.3.9.

J'ai localisé dans le TEI de Volkmann les 40 premières et les 40 dernières lettres de chaque nœud de la série `passage_plotinus_<ennéade>_<traité>_<chapitre>` (646 nœuds). La recherche porte sur la suite des lettres, sans accents ni ponctuation. Résultat : 644 nœuds sur 646 portent le texte d'un autre chapitre. Le décalage croît le long de l'œuvre. Quelques exemples :

| Nœud (locus revendiqué) | Texte réellement stocké |
|---|---|
| `passage_plotinus_i_2_1` (I.2.1) | I.1.11 |
| `passage_plotinus_ii_3_7` (II.3.7) | I.8.1 (début du traité *Sur l'origine des maux*) |
| `passage_plotinus_iii_1_7` (III.1.7) | II.3.9 |
| `passage_plotinus_vi_8_1` (VI.8.1, *Sur le volontaire*) | IV.4.26-27 |

La ligne de corpus que chaque nœud cite (`citation_type = snapshot_passage_node`, URN `perseus-grc1`) contient le même texte décalé. Les deux côtés étaient donc cohérents entre eux, mais faux. Sur 21 nœuds, la métadonnée affirmait en outre `text_integrity = reingested_tlge_2026_06_13` et `source = TLG E (Henry-Schwyzer)`. C'est inexact : la ligne TLG E ré-ingérée existe, mais sans citation vers le nœud, et le nœud avait gardé l'ancien texte.

La série de fragments `passage_plotinus_vi_9_1…709` n'est pas touchée. Elle était déjà requalifiée (`source_fragment_index`, ancrage TLG). Contrôlés avec la même méthode, 590 de ses fragments sont dans le chapitre annoncé. Les 119 autres commencent à la fin du chapitre précédent et se terminent dans le chapitre annoncé : ce sont des tranches à cheval sur une frontière, non des erreurs de locus.

## Correction

Pour chaque item, le script procède ainsi :

- Il vérifie d'abord trois préconditions :
  - l'URN est toujours celle du locus revendiqué ;
  - le nœud et sa ligne de corpus ont le même texte ;
  - le texte stocké se trouve toujours à l'emplacement consigné dans le module de données.
- Il remplace le texte, sur le nœud et sur sa ligne de corpus, par le chapitre de Volkmann correspondant au locus revendiqué, copié du TEI tel quel :
  - `<del>` est imprimé entre crochets droits, comme dans le Teubner ;
  - `<pb>` (changement de page) est omis ;
  - `<q>` est rendu comme du texte ;
  - les espaces sont normalisés.

  Un contrôle vérifie qu'aucune lettre du chapitre n'est perdue.
- Il met l'URN à `urn:cts:greekLit:tlg2000.tlg001.1st1K-grc1:<locus>` sur les deux côtés, renseigne `edition` et recalcule `word_count` et `char_length`. L'ancienne URN, l'emplacement réel de l'ancien texte, son SHA-256 et les anciennes valeurs de `text_integrity` et `source` sont conservés dans `metadata.plotinus_locus_repair_2026_09_24`.

Ce n'est pas une correction en bloc : chaque nœud est accepté ou refusé individuellement par ses préconditions, et l'emplacement de l'ancien texte est consigné, item par item, dans le fichier de décisions.

### Cas particulier : IV.4.30 et III.2.10

La ligne étiquetée IV.4.30 contenait en réalité III.2.10. Or une synthèse anglaise (`passage_plotinus_enn_4_4_30`) cite précisément ce texte sous l'étiquette « IV.4.30 », en le donnant dans `greek_verified`. Il s'agit de « ἀρχαὶ δὲ καὶ ἄνθρωποι… ἀρχὴ αὕτη αὐτεξούσιος » (« les hommes aussi sont des principes… ce principe est maître de soi »). Les deux moitiés de la citation se trouvent en III.2.10 chez Volkmann. En conséquence :

- la synthèse passe à `Enn. III.2.10`, avec `primary_node_id = passage_plotinus_iii_2_10` ;
- les citations de corpus rattachées à cette ligne pour ce passage (`concept_autexousion_christian_freedom_u1v2w3x4`, en `discusses` et `evidenced_by`, et `school_neoplatonism`) suivent la citation vers la ligne de III.2.10 ;
- la citation « jumelle » de la synthèse anglaise vers la ligne grecque est retirée (quarantaine). La base de référence d'intégrité la signalait déjà comme éditoriale et non bijective ; le lien vers le texte primaire reste `primary_node_id`.

Un contrôle final vérifie que la citation figure bien dans le nouveau texte de `passage_plotinus_iii_2_10`.

## Résultat

| Verdict | N |
|---|---|
| `corrected` : texte remplacé par le chapitre de Volkmann, URN corrigée | 627 |
| `corrected` : synthèse IV.4.30 ramenée à III.2.10 | 1 |
| `needs_romain` : nœud bloqué (`citation_blocked`, `needs_reference_remapping`) | 19 |

Parmi les 19 nœuds bloqués, 13 correspondent à un chapitre du TEI qui contient un `<gap reason="omitted"/>`, qu'on ne peut rendre sans l'imprimé. Les 6 autres (III.9.4-9) visent des chapitres qui n'existent pas dans la division de Volkmann, lequel ne compte que trois chapitres en III.9. Pour ces 19 nœuds, le texte n'est pas modifié ; la raison du blocage et l'emplacement réel du texte stocké sont consignés dans la métadonnée.

Bilan : 647 nœuds et 627 passages de corpus modifiés ; 3 citations de corpus déplacées et 1 retirée ; aucune arête modifiée.

## Arêtes sémantiques

Dix-sept arêtes sémantiques touchent cette série :

- 11 `evidenced_by` ;
- 3 `cites_primary_source` ;
- 3 `source_for`.

Elles viennent de `argument_plotinus_freedom_argument_7c561972`, `concept_plotinian_intellectual_eph_hemin`, `concept_sympatheia_universal_posidonius_nyssa` et `school_neoplatonism`. Toutes visent III.1 (*Sur le destin*), VI.8 (*Sur le volontaire*) ou I.1.1. Elles ont été posées d'après le locus (`manual_grounding_2026_06_13`, `grounded_by: full_text_read_post_reingest`), et non d'après le texte décalé. Elles deviennent exactes avec le texte rétabli et ne sont pas modifiées. Il en va de même pour les 11 citations de corpus homologues, faites par ces mêmes nœuds. Les deux lignes C3 d'origine reçoivent donc le verdict `corrected` (le texte, non l'arête).

## Contrôles

- Relance : aucune modification.
- Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict` (13 978 paires, 0 violation), `check_kg_work_child_canonical`.
- `check_snapshot_passage_integrity` : l'ensemble des violations est identique à celui du commit de base `34ea208`.
- Stats et BibTeX régénérés.

## Reste à faire (Romain)

- Les 19 nœuds bloqués : ré-ingérer ces chapitres à partir de l'imprimé, idéalement Henry-Schwyzer, puisque la série de fragments VI.9.x est déjà ancrée sur le TLG E.
- Choisir une édition de référence pour Plotin. Le corpus porte désormais Volkmann pour la série corrigée et le TLG E (Henry-Schwyzer) pour les fragments et les 21 lignes ré-ingérées, qui restent en l'état.
