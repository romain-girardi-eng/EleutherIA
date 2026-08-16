# Vague de fusions sémantiques — plan du 2026-08-17

**Statut : rédigé, NON APPLIQUÉ.** Le script d'application n'a été exécuté qu'en
`--dry-run` et dans une copie jetable du graphe. Rien n'a été écrit dans
`data/kg/`, `data/corpus/` ni `knowledge graph/ontology/`.

- Décisions et preuves : `scripts/data_2026_08_17_semantic_merges.py`
- Exécution : `scripts/apply_2026_08_17_semantic_merges.py` (`--dry-run` par
  défaut ; il faut `--apply` pour écrire)
- Constats d'origine : `data/audit/2026-08-16_deep_audit_semantic.jsonl`,
  `data/audit/2026-08-16_deep_audit_structural.jsonl`

## Résultat du `--dry-run`

```
nœuds  20 122 -> 19 750      (-372)
arêtes 54 167 -> 53 455      (-712)
nœuds absorbés : 371 (+ 1 nœud « éditeurs » supprimé après éclatement)
invariants : OK
```

| opération | nombre |
|---|---|
| fusions lot 1 (Destrée 2014) | 22 |
| fusions lot 2 (Boèce) | 129 |
| fusion lot 3a (work De libero arbitrio) | 1 |
| suppressions lot 3c (copies `_en` sans information) | 170 |
| fusions lot 4 (publications) | 16 |
| fusions lot 5 (CAFMA) | 4 |
| fusions lot 6 (double extraction) | 29 |
| arêtes `same_thesis_as` créées | 54 |
| arêtes recâblées | 489 |
| arêtes dédoublonnées (triplet déjà présent) | 761 |
| arêtes supprimées avec motif | 8 |
| arêtes retypées (conformité ontologique après fusion) | 4 |
| textes latins de Boèce désencapsulés | 129 |
| URN corrigées (`passage_aug_lib_arb_*`) | 93 |
| `passage_role` → `summary` | 116 |
| pointeurs `primary_text_node_id` posés | 170 |
| lignes de `citations.jsonl` recâblées | 303 |

Effet sur `scripts/check_ingestion_rules.py` (mode graphe entier), mesuré avant
et après application dans une copie :

| règle | avant | après |
|---|---|---|
| R2 identité dupliquée (BLOCK) | 2 987 | 2 520 |
| R3b work sans identifiant canonique (WARN) | 145 | 139 |
| R16 arête dialectique non attestée (WARN) | 297 | 294 |
| R13, R8, R9 | inchangé | inchangé |

Aucune catégorie de violation nouvelle. `citations.jsonl` : 0 référence
pendante avant, 0 après. Deuxième exécution : 0 nœud, 0 arête modifiés
(idempotence vérifiée).

---

## Garanties du script d'application

- `--dry-run` par défaut ; il faut passer `--apply` pour écrire.
- **Aucune fusion n'est appliquée depuis une liste d'ids.** Chaque paire est
  relue et la propriété qui en fait un doublon est re-vérifiée à l'exécution :
  même chapitre (lot 1), même `canonical_ref` + même `cts_urn` + même uuid de
  passage en base + latin identique après désencapsulation (lot 2), même auteur
  et présence d'un CTS URN sur le survivant (lot 3a), rôle + identité
  octet-à-octet + traduction présente chez le parent (lot 3c), même savant +
  même publication + pages compatibles (lot 6), `role: editorial_group` et
  présence des trois personnes (lot 7). Tout écart produit un `SKIPPED` journalisé
  et la fusion n'a pas lieu.
- Sauvegardes `.bak-semantic_merges` sur `nodes.jsonl`, `edges.jsonl`,
  `citations.jsonl` et `edge_types.json`.
- Assertions d'invariants avant écriture : 0 arête pendante, 0 triplet
  `(source, relation, target)` dupliqué, `source == source_id` et
  `target == target_id`, 0 boucle, 0 id de nœud dupliqué.
- Les métadonnées sérialisées en chaîne JSON sont reparsées et re-sérialisées à
  l'identique.
- Après fusion, remappage récursif de **toutes** les valeurs de métadonnées
  (nœuds et arêtes) et de `data/corpus/citations.jsonl`, en épargnant les clés
  d'historique (`merged_from`, `previous_node_id`, `*_remapped_*`, `*_before`,
  `*_pre_AAAA*`…) : elles enregistrent ce qu'un id **était** et doivent le rester.
- Rapport écrit dans `data/audit/2026-08-17_semantic_merges_applied.md`.

Politique de fusion : le survivant garde son propre contenu ; les métadonnées
absentes chez lui sont reprises (`citation_verdict`, `cited_in`,
`verified_reference`, `page_range`, `bibtex_key`, `doi`, `isbn`, `source_file`) ;
une description absorbée plus longue est conservée sous
`semantic_merges_2026_08_17_absorbed_description` plutôt que perdue ; toutes les
arêtes du nœud absorbé sont reportées, les triplets dupliqués fusionnés et les
boucles supprimées ; `merged_from` + motif sont écrits dans les métadonnées du
survivant.

---

## Lot 1 — Destrée / Salles / Zingano 2014 : 22 fusions

L'audit annonçait 19 paires ; la re-vérification en trouve **22**. L'heuristique
de l'audit ratait `frede_d`, `sauve_meyer` et `frede_michael`, dont le slug fait
deux tokens. Les 23 nœuds `synthesis_destree2014_*` se répartissent en 22
chapitres + l'introduction.

Les deux familles ont été créées **dans la même passe d'ingestion** (`created_at`
identique à la microseconde près sur les 45 nœuds). Pour chaque chapitre il
existe exactement un `synthesis_destree2014_chNN_*` (« Summary of ch. N (Auteur,
p. a-b) : … ») et un `argument_<auteur>_2014_*` (« <Auteur>'s scholarly argument
(Destrée 2014 ch. N …) »). Même chapitre, même thèse, deux types de nœud.

**Survivant : le nœud `argument_*`, dans les 22 cas.** La famille `synthesis_*` a
**zéro arête entrante** dans tout le graphe et ne porte que `discusses` +
`authored_by` ; la famille `argument_*` porte le câblage dialectique
(`responds_to`, `supports`, `critiques`), les `cites_primary_source` et les
`advanced_in`.

Apport net : le survivant récupère la pagination du chapitre, qu'il n'avait pas
(`page_range` était nul sur les 22). Mais les fourchettes annoncées par les
syntheses ne sont pas toutes fiables :

- ch02→ch15 forment une **chaîne parfaitement contiguë** (38→39, 58→59, 74→75,
  90→91, 106→107, 120→121, 140→141, 150→151, 168→169, 182→183, 198→199, 220→221,
  234→235) et deux d'entre elles sont corroborées indépendamment par les
  métadonnées des savants (Destrée « p. 25-38 » = ch02 ; Zingano « p. 199-220 » =
  ch13). → écrites dans `page_range`.
- ch01 (7-30) chevauche ch02 (25-38), et ch16→ch22 se contredisent entre elles
  (ch16 301-322 vs ch19 295-310 vs ch20 311-328). → **non écrites** ;
  enregistrées sous `destree2014_chapter_pages_claimed` +
  `needs_page_verification`.

`synthesis_destree2014_introduction_overview` n'a pas de jumeau : conservé (voir
lot 7 pour sa signature).

---

## Lot 2 — Boèce, *Consolatio* : 129 fusions

129 paires, 1:1, appariées sur le numéro puis re-vérifiées à l'exécution sur
`canonical_ref`, `cts_urn` **et** l'uuid du passage en base
(`db_passage_id` de la famille courte == `passage_id` de la famille longue).

Le latin est le même dans les deux familles mais **pas octet-à-octet** : la
description de `passage_boethius_cons_*` l'enveloppe en
`"Latin: <texte>\n\nBoethius, De consolatione philosophiae <n>"`. Les 129 paires
sont identiques après retrait de cette enveloppe (vérifié sur les 129).

**Survivant : `passage_boethius_cons_*`.** Contrairement à ce que suggérait
l'audit (« garder la famille aux URN/metadata les plus propres »), les deux
familles portent le **même** CTS URN ; le départage se fait sur les arêtes :

| famille | arêtes | relations |
|---|---|---|
| `passage_boeth_cons_*` (129) | 258 | `authored_by` 129, `part_of` 129 — rien d'autre |
| `passage_boethius_cons_*` (129) | 604 | + `discusses` 50, `source_for` 41, `cites_primary_source` 29, `evidenced_by` 28, et les 129 enfants `_en` |

Les 258 arêtes de la famille courte sont toutes des doublons de triplets déjà
présents. Aucune information n'est perdue.

**Normalisation de texte incluse.** Le préfixe `Latin: ` et la ligne
d'auto-citation finale sont du chrome éditorial dans le champ servi au lecteur.
Ils sont retirés du survivant **uniquement quand le résultat est identique
octet pour octet à la description du jumeau supprimé** — cette égalité est la
précondition. Aucun latin n'est édité, seulement désencapsulé (129/129).

Les 129 `passage_boethius_cons_*_en` ne sont **pas** touchés : 99 sont des
traductions réelles, 30 ont été requalifiées `untranslated_duplicate` par la
vague du 2026-08-16. Les deux états sont préservés, comme demandé.

---

## Lot 3 — Augustin, *De libero arbitrio*

### 3a. Les deux nœuds `work` — FUSION (1)

`work_augustine_de_libero_arbitrio` → `work_de_libero_arbitrio` (DAS-087). Le
survivant porte le CTS URN `urn:cts:latinLit:stoa0040.stoa054` et les 759 arêtes
`part_of` des passages ; l'absorbé n'a aucun passage et pour seul contenu propre
son bloc `editions`. Sont reportés : `editions`, `genre`, `author_id`,
`date_composed`, `original_language`, `frede_2011_role`, `frede_2011_treatment`.
`kg_work_id`, qui pointait sur l'id en train de disparaître, est réécrit vers le
survivant plutôt que reporté tel quel.

### 3b. `passage_aug_dla_*` vs `passage_aug_lib_arb_*` — FUSION ÉCARTÉE

L'audit bibliographique concluait à 170/170 de recouvrement de `canonical_ref`
et en déduisait un doublon. Le recouvrement est réel ; la déduction est fausse.
Les deux nœuds ne portent pas le même objet :

- `passage_aug_dla_1_10_20` : le paragraphe latin **continu** (médiane 1 388
  caractères sur la famille), `passage_role: original`, CTS URN correcte
  (170/170 : le suffixe de l'URN est exactement le `canonical_ref`).
- `passage_aug_lib_arb_1_10_20` : un **appareil éditorial** — résumé anglais,
  puis `Latin:` avec un extrait *elliptique* (« … »), puis `Translation:` avec
  une traduction anglaise, puis `Key terms:` avec un glossaire. CTS URN fausse
  dans 93 cas sur 170 (appariée sur le seul numéro de paragraphe : `…:3.7.20`
  pour un `canonical_ref` de `1.10.20`).

Supprimer la famille `lib_arb` détruirait **la seule traduction anglaise
existante de ces 170 loci**. Replier sa description dans `dla` mettrait de la
prose éditoriale à l'intérieur du texte de l'auteur ancien — précisément le
défaut que `docs/development/ingestion-rules.md` nomme comme dette connue :
« un nœud porte le texte primaire, l'autre un résumé éditorial anglais … demande
une classification, pas une fusion mécanique ». La fusion est donc écartée.

Sont appliquées à la place trois corrections vérifiables :

1. **URN (93 nœuds)** — l'URN est reprise du jumeau `dla`, sous réserve que
   l'URN de ce jumeau se termine bien par son propre `canonical_ref` (vérifié à
   l'exécution). L'ancienne valeur est conservée sous
   `semantic_merges_2026_08_17_cts_urn_before`.
2. **`passage_role` (116 nœuds)** — `original` → `summary`. 54 nœuds de la
   famille portaient déjà `summary` : la famille se normalise sur sa propre
   moitié correcte. Un appareil ne doit pas pouvoir être cité comme l'auteur
   ancien.
3. **`primary_text_node_id` (170 nœuds)** — pointeur explicite vers le nœud qui
   porte le texte.

### 3c. `passage_aug_lib_arb_*_en` — SUPPRESSION (170)

Les 170 sont **octet pour octet identiques** à leur parent, et les 170 parents
contiennent déjà un bloc `Translation:`. Le drapeau `needs_translation` qu'ils
portent est donc faux : il n'y a rien à traduire. Ils n'ont aucune arête propre
(340 arêtes structurelles dupliquant celles du parent, plus 4
`cites_primary_source` recâblées vers le parent, qui porte exactement le même
texte).

C'est le seul endroit où cette vague déroge à la décision du 2026-08-16 de
*garder* les `untranslated_duplicate` pour que l'arriéré reste visible : ici
l'arriéré est fictif.

---

## Lot 4 — publications en double : 16 fusions, 1 rejet, 5 déjà faites

Sur les 22 paires de DAS-089, **5 avaient déjà été exécutées** par les vagues
précédentes (re-vérifié absent le 2026-08-17) : Long 1996, Wolfson (id 1947
supprimé, 1942 conservé), Crouzel (`orig_ne` supprimé), Jewett (`_hermeneia_series`
supprimé), Salles (`work_…_2008` supprimé, 2005 conservé).

**Règle par défaut : garder le `pub_*`.** Il porte la description bibliographique
complète et le `citation_verdict`, et la table de remappage de l'audit structurel
montre que `pub_*` est le namespace vivant (`pub_eliasson_*`, `pub_karamanolis_*`,
`pub_sharples_*`, `pub_voelke_*`, `pub_destree_*` y sont les nœuds « live »).

**Règle pour les types mixtes : le survivant est toujours le nœud typé
`publication`**, quel que soit son degré. Une monographie moderne rangée dans le
catalogue `work` gonfle le compte des œuvres antiques et viole R3. Effet
mesurable : R3b passe de 145 à 139.

| survivant | absorbé | motif |
|---|---|---|
| `pub_frede_2011_free_will` | `work_frede_free_will_2011` | même livre (Sather 68, UCP 2011) |
| `scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso` | `work_bobzien_determinism_freedom_1998` | même monographie OUP, typée deux fois |
| `scholarly_work_frankfurt_1969_alternate_possibilities` | `work_frankfurt_alternate_possibilities_1969` | même article JPhil 1969 |
| `scholarly_work_kane_1996_significance_free_will` | `work_significance_of_free_will_kane_1i2j3k4l` | même monographie OUP 1996 |
| `scholarly_work_van_inwagen_1983_essay_free_will` | `work_essay_on_free_will_van_inwagen_8f9g0h1i` | même monographie OUP 1983 |
| `pub_belcastro_predestinazione_origene` | `scholarly_work_belcastro_2016_…` | même étude 2016 |
| `pub_craig_1991_divine_foreknowledge_human_freedom` | `scholarly_work_craig_1991_…` | même monographie ; les deux nœuds s'accordent désormais sur 1991 |
| `pub_byerly_2017_freewill_theodicies_theological_determinists` | `scholarly_work_byerly_2017_…` | même étude 2017 |
| `pub_hick_1966_evil_god_of_love` | `scholarly_work_hick_1966_…` | même monographie Macmillan 1966 |
| `pub_skarsaune_proof_from_prophecy` | `scholarly_work_skarsaune_1987_…` | même monographie Brill 1987 |
| `pub_hausmann_noller_2021_free_will_perspectives` | `scholarly_work_hausmann_2021_…` | même volume collectif 2021 |
| `pub_nadelhoffer_monroe_2022_exp_phil_free_will` | `scholarly_work_nadelhoffer_2022_…` | même volume collectif 2022 |
| `pub_still_wilhite_2024_apologists_paul` | `scholarly_work_still_2024_…` | même volume collectif 2024 |
| `pub_frankfurt_1971_freedom_will_person` | `scholarly_work_frankfurt_1971_…` | même article JPhil 1971 |

### Les deux exceptions à « garder le `pub_*` »

**Timpe / Vicens.** `pub_timpe_2023_christianity_problem_free_will` porte dans son
id le nom de Timpe alors que son label, sa description et son contenu sont ceux
de Leigh Vicens. L'id est la surface d'attribution publique (URL, clé BibTeX) :
c'est `scholarly_work_vicens_2023_christianity_and_the_problem_of_free_wil` qui
survit, et la description riche est reportée. Cela résout aussi DAS-090.

**Pouderon.** Années contradictoires pour la même monographie. La valeur
**vérifiée** est 1989 : les `verification_notes` du nœud `pub_pouderon_2000_*`
disent elles-mêmes « Théologie historique 82 … is the 1989 Beauchesne first
edition ; the '2000' traces to a libgen file's mislabel, and no distinct 2000
edition is attested in standard catalogues » — alors que son id **et** son
`metadata.year` disent toujours 2000. C'est donc
`scholarly_work_pouderon_1989_ath_nagore_d_ath_nes_philosophe_chr_tien`
(ISBN 2-7010-1190-6) qui survit, description riche reportée. Le fichier source
du nœud 1989 (`… (2000, Beauchesne).md`) est du reste le fichier libgen mal
étiqueté que la note incrimine.

### `scholarly_work_gill_2014_…` — diagnostic

Ce n'est **pas** un doublon et il ne doit surtout pas être fusionné dans
`pub_frede_2011_free_will`. C'est le **compte rendu par Christopher Gill** du
livre de Frede : *The European Legacy* 19.6 (2014) 797-798, DOI
10.1080/10848770.2014.949953 — son `verified_reference` le dit déjà correctement.
Le défaut est réel mais cosmétique : `title`, `label` et `description` sont le
titre du livre recensé avec « (review) » ajouté, si bien qu'un lecteur voit Gill
comme l'auteur du livre de Frede. Correction appliquée : titre et label réécrits
en « Review of M. Frede, *A Free Will*… », description explicite. Le nœud, son
auteur et ses cinq arguments restent.

### Bobichon 2003 — FUSION ÉCARTÉE

L'audit structurel donnait la paire pour « near-certain merge ». **Faux positif.**
Leurs `verified_reference` les distinguent explicitement : « vol. 2, coll.
Paradosis 47/2 » et « vol. 1 (Introduction, texte grec, traduction), coll.
Paradosis 47/1 ». Ce sont les deux volumes d'une même édition critique. Les
labels sont désambiguïsés (`vol. 1` / `vol. 2`) au lieu d'être fusionnés.

### Réparations d'arêtes induites par le lot 4

Sortir une monographie moderne du namespace `work` laisse sept arêtes dont la
relation n'est pas déclarée pour une extrémité `publication`. Aucune n'est
supprimée en silence :

| arête | traitement |
|---|---|
| `argument_consequence_argument_… -cites_primary_source-> van Inwagen 1983` | retypée `advanced_in` (l'*Essay on Free Will* est où l'argument des conséquences est avancé, ce n'est pas une source primaire) |
| `argument_frankfurt_cases_… -cites_primary_source-> Frankfurt 1969` | retypée `advanced_in` |
| `Frankfurt 1969 -contains-> argument_frankfurt_cases_…` | retournée en `argument -advanced_in-> publication` |
| `Frankfurt 1969 -contains-> concept_principle_alternative_possibilities` | retypée `discusses` (l'affirmation minimale vraie) |
| `argument_bobzien_2014_… -discusses-> Bobzien 1998` | retypée `extends` — la description du nœud dit littéralement « Extends Bobzien 1998 (chapter on Aristotle) » |
| `pub_bobzien_1998_inadvertent -precedes-> Bobzien 1998 (monographie)` | **supprimée** : aucune relation de l'ontologie n'exprime publication-précède-publication |
| `pub_bobzien_1998_inadvertent -responds_to-> pub_frede_2011_free_will` | **supprimée** : R13, un article de 1998 ne peut répondre à un livre de 2011 ; non retournée par conjecture |

---

## Lot 5 — CAFMA / Amand 1945 : l'arbitrage

### Le livre a été retrouvé et lu

`~/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/01_Philosophie_antique/`
`Fatalisme et liberté dans l'antiquité grecque; recherches -- Amand de Mendieta, Emmanuel -- 1973 -- Amsterdam, A_M_ Hakkert -- …pdf`
(644 p., + extraction `.md` conservant la pagination). Réimpression anastatique
Hakkert 1973 de l'édition de Louvain 1945 ; avant-propos signé « DAVID AMAND /
Maredsous, le 6 décembre 1944 ». Décalage vérifié : page imprimée + 32 = page PDF.

### Verdict : les deux paginations sont CORRECTES

Table analytique des matières, verbatim :

> « **CONCLUSION — RECONSTITUTION CONJECTURALE DE L'ARGUMENTATION DE CARNÉADE** … 571-586
> Introduction … 571-573
> **I. Les arguments carnéadiens dans les « textes témoins » … 573-581**
> **II. Reconstitution conjecturale et fragmentaire de la contexture de
> l'argumentation morale antifataliste de Carnéade … 581-584**
> **Thème général et cinq arguments reconstitués.**
> III. De quelques arguments attestés par Alexandre d'Aphrodise … 584-586 »

Les deux séries ne se contredisent donc pas : **p. 573-581 = section I**, le
dossier synoptique des témoins ; **p. 581-584 = section II**, la même série
exposée en synthèse reconstituée. La citation entre guillemets du nœud-cadre
(« Thème général et cinq arguments reconstitués ») est verbatim exacte de cette
table. Il n'y a **rien à re-paginer**.

Les six titres d'Amand (section I), avec leur reprise en section II :

| n° | titre (verbatim, section I) | témoins | synthèse |
|---|---|---|---|
| 1 | THÈME GÉNÉRAL DE L'ARGUMENTATION | 573-574 | 582 |
| 2 | … LA LÉGISLATION ET LA RÉPRESSION PÉNALE SONT INUTILES … | 574-576 | 582 |
| 3 | … LA VERTU ET LE VICE, LA LOUANGE ET LE BLÂME SONT INUTILES … | 576-577 | 582-583 |
| 4 | … ENCOURAGEMENTS ET RÉCOMPENSES, REPROCHES, RÉPRIMANDES ET CHATIMENTS SONT INUTILES … | 577-578 | 583 |
| 5 | … TOUTE ACTION, MORALE OU NON, DEVIENT INUTILE … | 578-580 | 583-584 |
| 6 | LE FATALISME ABSOLU RUINE LA PIÉTÉ À L'ÉGARD DE LA DIVINITÉ … | 580-581 | 584 |

Règle de fer d'Amand, p. 573 : « Est censé carnéadien tout argument attesté par
3 témoins au moins sur 6. »

La série `argument_carneadean_*_amand1945` reproduit ces six titres **item par
item et page par page, sans exception**. C'est elle qui survit.

### Les vrais défauts, et ce qui est fait

**(a) La numérotation de la série `cafma_*` est fausse.** Le nœud
`argument_cafma_futility_of_effort_8c3d5f21` se contredit dans sa propre
description (« Amand reconstructs it as argument no. 5 ») contre son label
« Argument I ». Trois fusions en découlent, chacune corroborée par les mêmes
témoins eusébiens :

| absorbé | survivant | corroboration |
|---|---|---|
| `argument_cafma_futility_of_effort_8c3d5f21` (« I ») | `argument_carneadean_action_futility_amand1945` (Amand 5) | tous deux citent *PE* VI.6.8-10 |
| `argument_cafma_futility_of_legislation_9d4e6g32` (« II ») | `argument_carneadean_legislation_amand1945` (Amand 2) | tous deux citent *PE* VI.6.18 |
| `argument_cafma_futility_of_piety_2g7h9j65` (« V ») | `argument_carneadean_piety_amand1945` (Amand 6) | tous deux citent *PE* VI.6.19 |

**(b) `argument_cafma_character_contradiction_1f6g8i54` n'appartient pas à la
série d'Amand.** Il ne figure ni parmi les six titres de la section I ni parmi
les six items reconstitués de la section II ; la recherche plein texte sur l'OCR
(« changement de caractère », « du vice à la vertu », « passent successivement »)
ne donne aucune occurrence pertinente. C'est un argument **antiastrologique**
(horoscope natal). Il entre en outre en collision avec la liste interne du
nœud-cadre, où « (IV) » désigne les encouragements et châtiments. Traitement :
nœud **conservé**, relabellisé (« Anti-astrological argument: moral character
changes, the natal horoscope cannot fix it »), numérotation CAFMA retirée,
`amand_1945_series_member: false` avec la preuve, et suppression de la seule
arête qui affirmait son appartenance (`contains -> framework_cafma_5a7b9e12`).
Il conserve 6 arêtes : aucun orphelin.

**(c) `argument_cafma_futility_of_sanctions_0e5f7h43` chevauche deux têtes.** Son
label vise la tête III (vertu/vice, louange/blâme, p. 576-577), ses citations
(*PE* VI.6.12-16) la tête IV (encouragements et châtiments, p. 577-578) — dont
Amand dit lui-même qu'elle « n'est qu'un cas particulier du précédent » (p. 577
n. 1). Une fusion devrait trancher. **Non fusionné** : arête `same_thesis_as`
vers la tête IV (4 de ses 5 citations) + drapeau `needs_scholarly_split`.

**(d) La liste des « textes témoins » du nœud-cadre est fausse.** Elle annonce
« ps.-Plutarch, Alexander of Aphrodisias, Firmicus Maternus, Eusebius, Nemesius,
John Chrysostom, Bardesanes ». Les six témoins d'Amand, verbatim p. 571-572,
sont : Philon d'Alexandrie (*De prov.* I, 79-83), Alexandre d'Aphrodise,
Firmicus Maternus (*Mathesis* I, 2, 5-11), Eusèbe (*PE* VI, 6, 4-21), Jean
Chrysostome (hom. *post concionem presbyteri Gothi* 6) et le Ps.-Chrysostome
(*De fato et providentia* V). **Philon est omis, ps.-Plutarque ajouté à tort** ;
Bardesane, Basile, Némésios et le commentateur arien sont chez Amand des
confirmations « cf. », pas des témoins (« En plus de ces six textes témoins, nous
ferons état à l'occasion, à titre de confirmation… »). La liste vérifiée, la
règle de fer et le tableau des six têtes sont écrits sur le survivant ; la
description fautive n'est pas reportée.

### Les deux nœuds-cadres — FUSION (1)

`framework_cafma_5a7b9e12` (type `argument_framework`, 20 arêtes) et
`argument_cafma_carneades_m3n4o5p6` (type `argument`, 24 arêtes) décrivent le
même objet et se partagent 44 arêtes.

**Survivant : `argument_cafma_carneades_m3n4o5p6`.** Motif technique, explicite :
les 20 arêtes du cadre sont **toutes** légales sur un nœud `argument`, alors que
garder le cadre ferait perdre 9 arêtes illégales pour le type
`argument_framework` — dont **les 8 `cites_primary_source`**, c'est-à-dire tout
l'ancrage aux passages d'Eusèbe et de Cicéron. Le survivant porte aussi le
tableau des prémisses P1-P5.

Conséquence assumée : le type `argument_framework` n'a plus d'instance. Il
rejoint les sept types déjà inoccupés recensés par l'audit structurel ; il faudra
soit le marquer `reserved`, soit lui réattribuer un usage. Cela défait en partie
le renommage cosmétique du 2026-08-16 (`argument_cafma_framework_*` →
`framework_cafma_*`), qui portait sur le préfixe d'id, pas sur le fond.

### Arête supprimée

`argument_cafma_futility_of_piety_2g7h9j65 -supports->
concept_pronoia_levels_proclus_a6d8c9b4` (DAS-098) : un argument carnéadien du
IIe s. av. J.-C. ne peut soutenir la providence hiérarchisée de Proclus (Ve s.
ap. J.-C.). Supprimée plutôt que reciblée par conjecture.

### Hors périmètre, signalé

`scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0` (la thèse
d'Amand lui-même, couche secondaire) est **conservé** : ce n'est pas un doublon
des arguments carnéadiens, c'est ce qu'Amand en dit. Il porte encore l'arête
`opposes` fautive vers Ramelli (DAS-092), qui n'est pas traitée ici.

---

## Lot 6 — `same_thesis_as` et double extraction

### 6a. Le type d'arête

`same_thesis_as` est ajouté à `knowledge graph/ontology/edge_types.json` — **la
seule écriture hors `scripts/` autorisée par cette vague, et elle est faite par
l'applier, pas à la main.** Diff :

```json
"same_thesis_as": {
  "description": "Source and target carry the same scholarly thesis at different granularity or in different namespaces (chapter synthesis vs pinpoint argument vs concept shell). Symmetric; stored one way only. Not a merge: the nodes remain distinct because they are not interchangeable.",
  "category": "semantic",
  "inverse": "same_thesis_as",
  "source_types": ["argument", "concept", "position", "synthesis"],
  "target_types": ["argument", "concept", "position", "synthesis"],
  "status": "active"
}
```

Inséré après `parallel_to`, parmi ses voisins sémantiques. La symétrie s'exprime
dans cette ontologie par `inverse == <soi-même>` (comme `related_to`,
`contrasts_with`, `parallel_to`, `contemporary_of`, `engages_with`) ; une seule
direction est stockée, conformément à la remarque de l'audit structurel sur les
paires réciproques matérialisées deux fois. `version` 3.0.0 → 3.1.0.

### 6b. Règle de fusion, appliquée sans exception

Deux `scholarly_argument_*` fusionnent **si et seulement si** :

1. même savant (`scholar_id` / `author_id`), **et**
2. leurs `source_file` résolvent vers la **même publication** — le même ouvrage
   extrait deux fois : texte intégral vs `.summary.md`, `.md` vs `.txt`, OCR vs
   non-OCR, **et**
3. leurs `page_range` se chevauchent ou s'emboîtent.

(2) sépare la double extraction de deux affirmations distinctes ; (3) empêche de
fusionner une thèse portant sur un chapitre avec une thèse portant sur un autre
chapitre du même livre. Les deux conditions sont re-vérifiées à l'exécution.

**29 fusions retenues**, réparties sur 27 groupes : Bobzien 1998 (7 nœuds
absorbés), Bobzien 2001 (1), Frede 2011 (5), D. Frede 1982 (2), Dihle 1982 (2),
Sharples 2008 (1), Ramelli 2014 (2), Double (1), Minns (1), Pouderon (2),
Eliasson (1), Belcastro (1), Byerly (1), Telfer (1), Hick (1).

Arête supprimée au passage : `scholarly_argument_sharples_accident_of_determinism_2008
-agrees_with-> scholarly_argument_sharples_free_will_and_determinism_in_a_1`
(DAS-094) — une relation dialectique posée entre deux nœuds du même article du
même auteur. Remplacée par `same_thesis_as`.

### 6c. Écartées, avec la preuve qui les sépare

| famille | pourquoi ce n'est pas un doublon |
|---|---|
| Crouzel | deux **livres différents** : *Théologie de l'image de Dieu chez Origène* (Théologie 34, Aubier 1956) et *Origène et la philosophie* (1962) |
| Bobichon (arguments) | l'édition critique du *Dialogue* vol. 2 et l'étude séparée sur le manuscrit : deux publications |
| Fitzmyer | deux sections d'un même commentaire (Rm 9:1-5 et 9:6-29) |
| Gaventa | trois sections d'un même commentaire (Rm 5, Rm 8, Rm 9–10:21) |
| Dettwiler | trois publications distinctes sur Colossiens (p. 26-28, p. 308, p. 287-288) ; rien n'établit que deux d'entre elles soient le même imprimé |
| Boys-Stones | même article, mais loci disjoints et objets différents : « Justin Martyr as Middle Platonist on fate » (p. 434 n.9) vs « Middle Platonist theory of fate » (p. 431-433) |
| 11 paires Bobzien | même publication mais `page_range` disjointes ou non analysables (« Chapter 3 » vs « 97-143 ») : fusionner reviendrait à choisir un locus contre l'autre |

Toutes reçoivent une arête `same_thesis_as` au lieu d'une fusion.

**Cinq `page_range` manifestement fausses** sont marquées `needs_page_verification`
plutôt que corrigées à l'aveugle : `375-412` pour un article paginé 133-175
(Bobzien 1998 = *Phronesis* 43) ; et quatre valeurs à quatre chiffres
(`2770-2779`, `3855-3924`, `4158-4175`, `3054-3057, 3110-3127`) dans des livres
d'environ 200 pages — ce sont des décalages de caractères ou de lignes, pas des
pages.

### 6d. Les 54 arêtes `same_thesis_as`

Construites à partir des clusters de l'audit dont le `verdict` est **exactement
`same`** (les verdicts `overlapping` et `same_or_overlapping` sont écartés :
affirmer l'identité de thèse sur un verdict d'« recouvrement » serait une
surenchère). Deux garde-fous supplémentaires :

- **Une seule arête par paire de namespaces.** Pour chaque cluster, un
  représentant par namespace (`scholarly_argument_`, `argument_`, `synthesis_`,
  `concept_`, `scholar_position_`) : le plus riche. C'est exactement le problème
  de DAS-001 (« la même thèse est portée par 2 à 5 nœuds de namespaces
  différents »). À l'intérieur d'un namespace, deux nœuds sont soit des doublons
  (fusionnés), soit des affirmations distinctes (laissées telles quelles).
- **Étoile, pas clique**, autour du `best_member` de l'audit s'il survit, sinon
  du nœud de plus haut degré : 54 arêtes au lieu de 186.
- Les clusters **CAFMA** et **Destrée/Salles** sont exclus explicitement : leurs
  membres sont six arguments *distincts* d'Amand pour l'un, et des paires déjà
  fusionnées pour l'autre. Une étoile y affirmerait que les six têtes de Carnéade
  portent la même thèse.

Aucune arête n'est créée si l'une des deux extrémités a disparu.

---

## Lot 7 — micro-lots structurels

### `scholar_destr_e_p_salles_zingano_eds`

Nœud typé `person` représentant trois personnes (DAS-091). Il n'a **aucune**
arête sortante et exactement trois arêtes entrantes. Sa métadonnée `members`
liste par ailleurs `scholar_salles_ricardo`, qui n'existe plus (fusionné dans
`person_salles_ricardo_contemporary`).

1. `pub_destree_salles_zingano_2014_what_is_up_to_us -authored_by-> eds`
   → **`edited_by`** vers chacun des trois. Le volume porte
   `metadata.type: edited_volume` et `metadata.editors` nomme exactement ces
   trois personnes ; l'ontologie déclare `edited_by` (publication → person) et
   l'audit structurel demande qu'elle « absorbe les cas éditeur-comme-auteur ».
   Les **trois arêtes `authored_by` individuelles déjà présentes** sur le volume
   sont retypées `edited_by` du même coup : éditer n'est pas écrire.
2. `synthesis_destree2014_introduction_overview -authored_by-> eds`
   → `authored_by` vers chacun des trois. L'introduction du volume (p. 1-6) est
   bien signée des trois éditeurs.
3. `scholar_frede_michael -influences-> eds` → **supprimée**. Métadonnées vides,
   aucune attestation, et une cible qui n'est pas une personne. L'éclater en
   trois affirmations d'influence individuelles serait une inférence, pas un
   report. DAS-100 identifie précisément les arêtes dialectiques non attestées
   comme la classe fautive.

Le nœud est ensuite supprimé : plus aucune arête ne le référence.

### Fusions « déclarées jamais exécutées » — vérification

Toutes ont bien été faites par les vagues précédentes ; il n'y a rien à
rattraper. Vérifié absent le 2026-08-17 : `pub_long_1996_stoic_studies` (la
fusion que R2 cite en exemple d'incident), `scholarly_work_crouzel_1962_orig_ne_et_la_philosophie`,
`scholarly_work_wolfson_1947_…`, `scholarly_work_jewett_2007_…_hermeneia_series`,
`work_salles_stoics_determinism_2008`.

---

## Découvertes imprévues

1. **L'audit sous-comptait le lot 1** : 22 paires Destrée 2014, pas 19. Son
   heuristique d'appariement ratait les slugs de savants en deux tokens.
2. **Le désaccord de pagination CAFMA n'existe pas.** Le livre montre que les
   deux séries citent deux sections successives de la même conclusion. Le vrai
   défaut est ailleurs : une numérotation fausse, un argument étranger à la
   série, et une liste de témoins qui omet Philon et invente ps.-Plutarque.
3. **La famille `passage_aug_lib_arb_*` n'est pas un doublon** mais un appareil
   éditorial contenant l'unique traduction anglaise de 170 loci augustiniens. La
   fusion demandée aurait détruit du contenu ; l'audit bibliographique avait
   raisonné sur le recouvrement de `canonical_ref` seul.
4. **La paire Bobichon 2003 est un faux positif** de l'audit structurel : ce sont
   les volumes 1 et 2 d'une même édition critique, ce que disent leurs propres
   `verified_reference`.
5. **`scholarly_work_gill_2014_…` n'est pas à fusionner** : c'est un compte rendu
   par Gill du livre de Frede, correctement documenté dans son
   `verified_reference` mais mal titré.
6. **Le nœud Pouderon `pub_*` contredit sa propre note de vérification** : ses
   `verification_notes` établissent 1989, son id et son `metadata.year` disent
   toujours 2000.
7. **Onze paires Bobzien portent des `page_range` incompatibles issues du même
   livre**, dont cinq manifestement corrompues (valeurs à quatre chiffres, ou
   hors de la pagination de l'article). Elles ont bloqué autant de fusions et
   sont désormais tracées.
8. **La fusion des deux nœuds-cadres CAFMA vide le type `argument_framework`.**
   Décision de typage à prendre séparément.
9. **Les descriptions de Boèce contiennent du chrome éditorial** (`Latin: ` +
   auto-citation finale) dans le champ servi au lecteur. Le jumeau supprimé en
   fournit la version propre attestée, ce qui rend le nettoyage vérifiable.

---

## Restes connus, non traités par cette vague

- Les 78 `scholarly_argument_*` sans `page_range` (R8 WARN) : inchangé.
- `scholarly_argument_amand_de_mendieta_… -opposes-> scholarly_argument_ramelli_…`
  (DAS-092), le triangle Kahn/Dihle/Frede (DAS-093) et les arêtes `agrees_with`
  douteuses (DAS-095/096/097) : hors périmètre.
- Les 883 labels tronqués (DAS-084) et les 718 ids tronqués (DAS-085) : hors
  périmètre, et l'audit recommande de ne pas renommer les ids.
- Les 20 ids dont le patronyme contredit l'auteur attribué : toujours ouverts,
  en attente de confirmation bibliographique externe.
- Les 294 arêtes dialectiques sans `attested_by` (R16) : traitées par une autre
  vague.
