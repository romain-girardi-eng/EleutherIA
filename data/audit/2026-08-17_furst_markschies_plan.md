# Plan d’ingestion — Fürst / Markschies (PDF), 17 août 2026

## Résultat

Le delta proposé remplit les trois coquilles de publication existantes sans les recréer et sans modifier le graphe :

- `pub_furst_2019_concepts_origenism_ad13` : 9 nouveaux nœuds d’argument ;
- `pub_markschies_2007_origenes_erbe` : 6 nouveaux nœuds d’argument ;
- `pub_furst_2021_perspectives_origen_ad21` : 10 nouveaux nœuds d’argument.

Le delta contient au total **27 nœuds** (25 arguments et 2 auteurs de chapitres absents du graphe) et **126 arêtes**. Il réutilise les personnes et publications existantes conformément à R2. Aucun fichier de `data/kg/` ou `data/corpus/` n’a été écrit.

Les descriptions des arguments dans le delta sont en anglais. Les formulations grecques ou latines n’ont pas été générées : les rares termes anciens sont des translittérations ou des reprises littérales des PDF. Les réserves et verdicts suspendus sont conservés comme tels.

## Identités réutilisées et ajoutées

Identités réutilisées :

- `scholar_furst_alfons`
- `scholar_markschies_christoph`
- `scholar_jacobsen_a`
- `scholar_kobusch_theo`
- `pub_furst_2019_concepts_origenism_ad13`
- `pub_furst_2021_perspectives_origen_ad21`
- `pub_markschies_2007_origenes_erbe`

Deux auteurs de chapitres n’avaient aucun nœud de personne après recherche dans `data/kg/nodes.jsonl` ; le delta propose donc :

- `scholar_moller_morten_kock` — Morten Kock Møller ;
- `scholar_scarponi_ilaria` — Ilaria Scarponi.

Le volume `pub_furst_2021_perspectives_origen_ad21` conserve son identifiant corrigé de 2021 ; aucun ancien identifiant `pub_furst_2019_*` n’est recréé.

## 1. Alfons Fürst, 2019 — *Concepts of Origenism from Late Antiquity to Modern Times*

### Source et pages lues

PDF :

`/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/05_Origene/fuerst_2019_concepts_of_origenism_adamantiana13_intro.pdf`

Lecture intégrale des pages imprimées **11–44**. Contrôle visuel effectué notamment aux pages imprimées 13 et 44.

### Carte argumentative

| Pages | Nœud | Argument retenu |
|---|---|---|
| 11–12 | `scholarly_argument_furst_2019_preexistence_apokatastasis_remain_hypotheses` | La préexistence et la restauration universelle ne sont pas durcies en doctrines fixes ; le sort du diable demeure expressément non tranché. |
| 13–16 | `scholarly_argument_furst_2019_freedom_is_origenian_systematic_center` | L’autodétermination constitue le centre systématique de l’anthropologie et de la métaphysique origéniennes, en lien avec responsabilité et pédagogie providentielle. |
| 14–17 | `scholarly_argument_furst_2019_late_antique_origenism_displaced_freedom` | L’origénisme polémique tardif transforme des corollaires disputés en marqueurs identitaires et fait disparaître la liberté de l’image reçue. |
| 17–20 | `scholarly_argument_furst_2019_humanists_restore_anthropology_of_freedom` | Pico et Érasme rétablissent l’anthropologie de la liberté tout en sélectionnant certains éléments du système. |
| 21–25 | `scholarly_argument_furst_2019_rust_retains_freedom_under_pressure_from_necessity` | Chez Rust, la liberté subit la pression d’une nécessité quasi fatale, mais Fürst précise que cela ne l’abolit pas automatiquement. |
| 27–33 | `scholarly_argument_furst_2019_cambridge_origenists_diverge_on_libertarian_core` | Les Cambridge Origenists divergent ; Cudworth rétablit le noyau libertarien et la responsabilité en rejetant le déterminisme cyclique stoïcien. |
| 34–37 | `scholarly_argument_furst_2019_huet_makes_unrestricted_freedom_source_of_error` | Huet inverse cette lecture constructive et fait de la liberté illimitée une source d’erreurs. |
| 38–41 | `scholarly_argument_furst_2019_petersen_narrows_origen_to_restoration` | Petersen réduit l’héritage à la restauration universelle et au salut du diable, sans remettre la liberté au centre. |
| 42–44 | `scholarly_argument_furst_2019_modern_scholarship_recenters_freedom_with_caution` | Fürst approuve le recentrage moderne sur la liberté, tout en prévoyant prudemment la persistance de l’ancienne image. |

### Arêtes dialectiques

- `humanists_restore_anthropology_of_freedom --critiques--> late_antique_origenism_displaced_freedom`, attestée par Fürst 2019, pp. 17–20.
- `cambridge_origenists_diverge_on_libertarian_core --opposes--> huet_makes_unrestricted_freedom_source_of_error`, attestée par Fürst 2019, pp. 27–37. La métadonnée précise qu’il s’agit de la juxtaposition historiographique de deux modèles incompatibles, non d’un dialogue direct entre auteurs.

Ces deux relations portent `metadata.attested_by` conformément à R16.

### Exclusions

Aucune section n’a été exclue : l’article entier est directement pertinent pour la liberté, la responsabilité, la providence et la réception de l’anthropologie d’Origène.

## 2. Christoph Markschies, 2007 — *Origenes und sein Erbe*

### Source et pages lues

PDF :

`/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/05_Origene/markschies_2007_origenes_erbe.pdf`

Pages imprimées lues : **8–12, 79–86, 91–105 et 127–141**. Contrôle visuel effectué notamment aux pages imprimées 10 et 81.

### Carte argumentative

| Pages | Nœud | Argument retenu |
|---|---|---|
| 9–10 | `scholarly_argument_markschies_fall_is_freedom_and_providence` | La chute différenciée est simultanément réalisation de la liberté et signe de la providence : « Jener Fall der geistigen Entitäten ist eine Realisierung ihrer Freiheit und doch zugleich ein Zeichen göttlicher Vorsehung. » |
| 10–11 | `scholarly_argument_markschies_rejects_determinism_yet_requires_christ` | Origène rejette le déterminisme de l’action humaine sans faire de la purification le résultat du seul effort : le Christ demeure nécessaire. |
| 10–12 | `scholarly_argument_markschies_apokatastasis_is_consequence_but_not_settled_verdict` | L’apocatastase est une conséquence systématique, mais Origène traite une question « über die er sich selbst unsicher war » ; le delta maintient cette incertitude. |
| 81–85 | `scholarly_argument_markschies_romans_persona_preserves_free_will_framework` | La lecture prosopographique de Romains 7 préserve le cadre de liberté et de perfection possible ; Markschies refuse toutefois d’étendre sans nuance le modèle dramatique à toute l’épître. |
| 100–104 | `scholarly_argument_markschies_biblical_anthropology_resists_simple_synergist_label` | Le vocabulaire biblique interdit de réduire l’anthropologie à l’étiquette simple de « synergisme » : le Verbe meut réellement l’humain sans effacer la liberté. |
| 135–141 | `scholarly_argument_markschies_celsus_misidentification_shapes_providence_frame` | La providence guide *Contra Celsum*, mais dans un cadre anti-épicurien produit par une identification erronée et progressivement reconnue comme inadéquate. |

### Arêtes dialectiques

Aucune arête `agrees_with`, `opposes` ou `critiques` n’a été ajoutée à l’intérieur de cette publication : les tensions relevées par Markschies sont des qualifications internes et non des désaccords entre deux arguments modernes distincts. Elles sont enregistrées dans les descriptions plutôt que transformées artificiellement en conflit.

### Exclusions motivées

Le volume est un recueil. Après triage du sommaire et lecture des plages pertinentes :

- pp. 15–62, ascèse, prédication et public des homélies : histoire sociale et pastorale sans thèse autonome nécessaire sur la liberté ou la responsabilité ;
- pp. 107–126, Saint-Esprit dans le commentaire de Jean : pneumatologie, hors du périmètre ciblé ;
- pp. 155–238, gnose valentinienne, terminologie de l’essence, Ambroise et Eusèbe : réception et histoire doctrinale sans apport direct distinct à la question libre arbitre–providence ;
- pp. 239–265, histoire des éditions berlinoises : histoire éditoriale, hors sujet.

Ces chapitres ne sont pas force-fit dans le graphe.

## 3. Alfons Fürst (dir.), 2021 — *Perspectives on Origen and the History of His Reception*

### Source et pages lues

PDF :

`/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/05_Origene/fuerst_2021_perspectives_origen_adamantiana21.pdf`

Pages imprimées lues :

- introduction de Fürst : **13–27** ;
- Anders-Christian Jacobsen : **31–44** ;
- Alfons Fürst, *Readings of Origen in Late Antiquity* : **103–114** ;
- Morten Kock Møller : **193–214** ;
- Ilaria Scarponi : **215–234** ;
- Theo Kobusch : **335–343**.

Contrôle visuel effectué notamment aux pages imprimées 41 et 335, ainsi que sur les titres et pages de texte des chapitres de Møller et Scarponi.

### Attribution

Les arguments sont attribués à l’auteur du chapitre qui les avance. Fürst n’est utilisé comme auteur que pour son introduction et son propre chapitre ; il n’est jamais substitué à Jacobsen, Møller, Scarponi ou Kobusch du seul fait de son rôle d’éditeur.

### Carte argumentative

| Pages | Auteur et nœud | Argument retenu |
|---|---|---|
| 18, 24–25 | Fürst — `scholarly_argument_furst_2021_libertarian_reading_is_influential_but_disputed` | La lecture de Münster fait d’Origène un innovateur libertarien à l’intérieur de la providence et de la grâce ; Fürst dit explicitement que cette classification reste disputée. |
| 103–108 | Fürst — `scholarly_argument_furst_2021_pamphilus_preserves_suspended_judgments` | Pamphile conserve le caractère zététique et les verdicts suspendus ; Athanase en resserre la fonction. Aucun choix caché n’est attribué à Origène. |
| 110–112 | Fürst — `scholarly_argument_furst_2021_philocalia_pairs_hermeneutics_and_freedom` | La structure de la *Philocalie* associe herméneutique et liberté comme principes organisateurs du système. |
| 31–43 | Jacobsen — `scholarly_argument_jacobsen_body_limits_and_enables_freedom` | Le corps limite la liberté mais fournit aussi l’espace pédagogique des choix et du retour vers la perfection. |
| 43–44 | Jacobsen — `scholarly_argument_jacobsen_eschatological_body_verdict_suspended` | Jacobsen déclare ne pas parvenir à une conclusion sûre sur le corps final et la rechute ; sa préférence pour l’hypothèse incorporelle reste une tendance, non un verdict. |
| 203–208 | Møller — `scholarly_argument_moller_origen_propositum_compatibilizes_foreknowledge_and_choice` | Les lectures humaine et divine du *propositum* peuvent toutes deux préserver l’agence si l’élection répond aux choix prévus ; le commentaire laisse le lecteur choisir. |
| 209–214 | Møller — `scholarly_argument_moller_augustine_target_plausible_not_decisive` | Une cible origénienne de la réfutation augustinienne est plausible, mais indécidable en raison de sources multiples ; le contraste sur la coopération avec la grâce reste net. |
| 215–225, 232–234 | Scarponi — `scholarly_argument_scarponi_de_induratione_reuses_origen_against_determinism` | *De induratione* réemploie des solutions origéniennes pour défendre le choix contre une lecture déterministe, tout en les recontextualisant dans la polémique anti-augustinienne. |
| 227–234 | Scarponi — `scholarly_argument_scarponi_corrective_punishment_selective_reception` | Les châtiments sont pédagogiques et révèlent la dureté volontaire ; la réception demeure sélective, car *De induratione* écarte l’apocatastase et admet le châtiment éternel. |
| 335–338 | Kobusch — `scholarly_argument_kobusch_image_freedom_unlosable_likeness_losable` | L’image désigne la liberté et la dignité métaphysiques, inaliénables ; la ressemblance morale dépend de leur exercice et peut être perdue. |

### Arête dialectique

- `moller_augustine_target_plausible_not_decisive --opposes--> moller_origen_propositum_compatibilizes_foreknowledge_and_choice`, attestée par Møller 2021, pp. 213–214.

L’arête encode l’opposition doctrinale explicitement reconstruite entre l’Augustin anti-pélagien et le modèle origénien de coopération. La métadonnée conserve séparément le verdict suspendu de Møller sur la dépendance textuelle directe.

### Exclusions motivées

Le triage est fondé sur le sommaire et les incipits ; les plages ci-dessous ne sont pas présentées comme intégralement lues :

- Pollmann, pp. 47–66, Klöckener, pp. 67–80, et Contini, pp. 81–100 : modèles, « soft power », dignité et rhétorique des Juges ; liens indirects mais pas de thèse plus structurante que les arguments anthropologiques retenus ;
- Ip, Edwards, Carlson, Edsall et Hermanin de Reichenfeld, pp. 117–192 : théologie trinitaire, sens littéral, traduction de Rufin, liturgie et Jean 4,24 ; hors du noyau liberté–providence–responsabilité ;
- Martens, Karfíková et Rapetti, pp. 237–296 : réception médiévale et janséniste, sans argument distinct requis pour cette vague ;
- Lewis et Bellucci, pp. 297–334 : cas Hallywell et Petersen déjà représentés structurellement par l’article de Fürst 2019 dans ce même delta ; ne pas les dupliquer évite de transformer un recoupement historiographique en nouveaux arguments artificiels ;
- Kobusch, pp. 338–343 : prolongement sur la réception de la personne et de l’acte ; intéressant, mais secondaire par rapport à la distinction image–ressemblance directement pertinente.

## Sources primaires et concepts

Les arêtes `cites_primary_source` visent seulement des œuvres déjà présentes dans le graphe et effectivement citées dans les pages concernées, notamment :

- `work_de_principiis_origen_230s_v2w3x4y5`
- `work_origen_commentary_romans`
- `work_origen_contra_celsum_sc132`
- `work_origen_philocalia`

Les loci et pages justificatives sont portés par `metadata.attested_by`. Aucun nouveau locus grec ou latin n’a été fabriqué.

Les arguments sont reliés, selon leur contenu, aux concepts et débats existants sur l’autexousion, la métaphysique de la liberté, l’anthropologie dynamique, la synergie grâce–liberté, l’apocatastase, la responsabilité, la prescience et la controverse Augustin–Pélage.

## Vérification obligatoire

Commande :

```text
python3 scripts/check_ingestion_rules.py --new-only scripts/data_2026_08_17_furst_markschies.json
```

Sortie :

```text
ingestion-rules: delta of 27 nodes / 126 edges
  no violations

BLOCK: 0   WARN: 0
```

Commande :

```text
python3 scripts/ingest_2026_08_17_furst_markschies.py
```

Sortie :

```text
delta: 27 nodes / 126 edges
novel: 27 nodes / 126 edges (skipped existing: 0 nodes, 0 edges)
BLOCK: 0   WARN: 0
dry-run: nothing written (use --apply)
```

Le script n’a pas été lancé avec `--apply`.

