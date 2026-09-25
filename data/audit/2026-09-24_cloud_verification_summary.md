# Vérification savante du KG (campagne Jev du 2026-09-24) — synthèse

Branche : `claude/nifty-tesla-pjrfgr`, depuis `34ea208`. Chaque lot compte une paire de scripts `scripts/data_2026_09_24_*.py` / `scripts/apply_2026_09_24_*.py` rejouables et idempotents, un rapport `data/audit/2026-09-24_<lot>_applied.md`, un fichier de décisions `…_decisions.jsonl` (un enregistrement par item, avec `item_id`, `queue`, `claim_checked`, `verdict`, `evidence`, `source`, `method`, `jev` et `change`) et, le cas échéant, une quarantaine `…_quarantine.jsonl` qui contient chaque enregistrement retiré, tel quel.

Après chaque lot, les portes suivantes sont au vert :

- `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate` ;
- `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict` (13 978 paires, 0 violation), `check_kg_work_child_canonical`.

`check_snapshot_passage_integrity --strict` échouait déjà sur le commit de base, avec 66 violations. L'ensemble des violations est resté identique à celui de la base après chaque lot. Aucun grec ni aucun latin n'a été composé : tout texte ancien introduit vient mot pour mot d'un TEI d'édition critique dont le hachage est épinglé.

## 1. Décomptes

### Par verdict (2 288 décisions)

| Verdict | N |
|---|---|
| `corrected` | 916 |
| `removed` | 608 (dont 28 doublons de décision : lignes Fédou revues deux fois) |
| `merged` | 7 |
| `false_positive` | 379 |
| `needs_romain` | 378 (dont 3 défauts documentés sans correction, lot C1 « quality flags ») |

### Par priorité

| Priorité | Lots | Décisions | Corr. / retr. / fus. | FP | Romain |
|---|---|---|---|---|---|
| 1. Texte, loci, traductions, arêtes de citation | Plotin, Justin, C2 ×2, langue éditoriale, C1 « quality flags », C3 citations | 1 576 | 1 302 | 197 | 77 |
| 2. Attributions, doublons | Fédou, C4 fusions, C3 homonymes, C2 identité | 161 | 77 | 77 | 7 |
| 3. Arêtes sémantiques | C3 `discusses`, C3 autres, C1 contradictions | 402 | 134 | 105 | 163 |
| 4. Hygiène du texte public | notes de curation, échappements | 149 | 18 | 0 | 131 |
| 5. Ajouts | — | 0 | — | — | — |

Bilan net sur le graphe :

- 412 nœuds retirés : 29 lignes Fédou et 383 traductions machine ;
- 7 fusions ;
- environ 900 nœuds corrigés, dont 627 textes de Plotin, 197 nœuds de Justin et 46 changements de langue ;
- 1 381 arêtes retirées : 1 149 avec les traductions retirées, 58 avec les lignes Fédou, 164 arêtes sémantiques ou de citation, et 10 lors des fusions ;
- 485 citations et 383 passages retirés du corpus ;
- 7 arêtes déplacées vers la bonne cible.

Tout est en quarantaine.

## 2. Corrections, avec leurs sources

- **Plotin, décalage des loci** (`plotinus_locus_drift`) : 644 des 646 nœuds `passage_plotinus_<ennéade>_<traité>_<chapitre>` portaient le texte d'un autre chapitre. Le texte stocké sous VI.8.1, *Sur le volontaire*, était IV.4.26 ; celui de III.1.7 était II.3.9. Pour 627 nœuds, le texte a été rétabli à l'identique à partir de Volkmann (Teubner 1883-1884, TEI First1KGreek `tlg2000.tlg001.1st1K-grc1`), sur le nœud comme sur son jumeau de corpus. Les 19 autres sont bloqués : chapitre avec `<gap>` ou absent de la division de Volkmann (III.9.4-9). Une synthèse anglaise citant III.2.10 (« ἀρχαὶ δὲ καὶ ἄνθρωποι… », « les hommes aussi sont des principes… ») sous l'étiquette IV.4.30 a été ramenée à III.2.10.
- **Justin, *Dialogue avec Tryphon*** (`justin_tryph_entities`) : 197 nœuds et 196 passages contenaient `&#45;` à la place du trait d'union. Correction contrôlée contre Archambault 1909 (TEI First1KGreek `tlg0645.tlg003.perseus-grc2`).
- **Traductions machine** (`c2_misaligned_translations`, `c2_translation_followup`) : 383 traductions retirées. Soit elles ne rendent pas leur original (décalage d'un verset chez Méliton, Barnabé et Théophile), soit ce sont des pseudo-traductions hybrides (*Contre Celse* V-VI) ou des synopsis à la voix de l'éditeur (*Pasteur*). Onze synopsis sont requalifiés `machine_paraphrase`. Méthode : lecture de l'original et de la traduction, contrôlée sur les sections voisines.
- **Langue des passages éditoriaux** (`editorial_passage_language`) : 46 synthèses anglaises étaient déclarées `grc` ou `lat` ; elles sont requalifiées `eng`, avec `quoted_language`.
- **Arêtes de citation C3** (`c3_citation_edges`) : 26 arêtes retirées, dont les suivantes.
  - Des arêtes contredites par leur propre nœud : l'argument « sur le seul témoignage d'Alexandre » était ancré dans Eusèbe.
  - Une mauvaise œuvre : Frede sur Alexandre pointait vers le *De fato* de Cicéron.
  - Des balayages terminologiques sur Boèce : *declinantes* ou *indeclinabilem* pris pour *clinamen*.
  - Des câblages automatiques : Athénagore, Tertullien, *Adv. Prax.*, ou encore les Pharisiens reliés à la vie de Thalès.
  - Des « meilleurs substituts disponibles » avoués par leur propre justification.

  Trois arguments du Pseudo-Chrysostome (PG 50, 765-768) sont déplacés de SC 79 vers `work_pseudo_chrysostom_de_fato_providentia`.
- **Fédou 2026** (`fedou_bulletin_withdrawal`) : 29 lignes de bulletin, contaminées par des étendues bibliographiques d'autres notices, sont retirées avec leurs 58 arêtes `discusses`.
- **Doublons C4** (`c4_duplicate_merges`) : 7 fusions (Méliton, Bardesane, Athénagore, Linjamaa, Irénée *Epideixis*, Aristide, Tomberlin/Plantinga), avec redirection des arêtes et des pointeurs et conservation de `previous_node_id`.
- **Homonymes** (`c3_person_identity`) : Mark J. Edwards avait été pris pour Jonathan Edwards (trois arêtes, dont un « directeur de thèse » mort en 1758), et Dorothea Frede pour Michael Frede. Des citations de Hal Koch (*Pronoia und Paideusis*, 1932), de Marx-Wolf et d'autres homonymes étaient rattachées à Isabelle Koch, Susan Wolf, William James, Richard Taylor et J. M. Fischer. Bilan : 4 arêtes déplacées et 8 retirées.
- **`discusses`** (`c3_discusses_edges`) : 124 arêtes retirées.
  - *De libero arbitrio* III était relié en bloc à la prescience, que le livre ne traite qu'en III.2.4-4.11.
  - La preuve de Dieu du livre II était reliée en bloc à *voluntas*.
  - 13 liens `period_match` rattachaient des savants au principe des possibilités alternatives.
  - 15 auto-liens venaient d'un mot égaré : « Manuel » a été pris pour le *Manuel* d'Épictète, « martyr » pour Justin, « De providentia » pour SC 79.
- **Contradictions C1** (`c1_contradictions`) : les chapitres d'Alexandre sont testés sur le chapitre complet de Bruns (TEI First1KGreek `tlg0732.tlg014`). Un lien n'est retiré que si sa justification nomme un terme absent du chapitre.
- **Hygiène** :
  - 14 arguments savants dont la description n'était qu'une note de vérification ; la position enregistrée dans `metadata.stance` devient la description, et 9 d'entre eux passent en `discoverable_only` d'après l'audit du 2026-08-29 ;
  - `scholar_wolfson_h` était tronqué par une consigne d'édition ;
  - un chemin de fichier privé figurait dans une description publique ;
  - le résumé OpenAlex de Cohen 2010 était en fait la réclame d'un commentaire constitutionnel allemand ;
  - deux notices contenaient des échappements `&#13;` et `\n` littéraux.

## 3. Faux positifs de Jev

Jev pénalise surtout l'écart entre un résumé moderne et un texte ancien. Ce n'est pas un signe d'erreur. Les cas conservés sont les suivants :

- **C2 (169).** Des traductions fidèles mais partielles (152), débordant sur les versets suivants (10), ou dont on a seulement ôté une note entre crochets (6), plus une paire qui n'en est pas une. Au-dessus de p = 0,7, l'échantillon relu ne contenait que des traductions fidèles.
- **C3 (172).**
  - Des arêtes de citation avec `attested_by` et pages imprimées ; des citations au niveau de l'œuvre déjà marquées `evidence_pending`.
  - 72 liens `engages_with` dont l'identité de la cible est cohérente avec la note.
  - Des ouvrages savants reliés aux figures qu'ils étudient (Frede 2011 → Galien, Tatien, Porphyre…).
  - Les chapitres d'Alexandre qui contiennent le terme annoncé (τύχη, κύριος).
- **C1 (33).** Les liens dont le radical figure dans le chapitre complet, ainsi que *EN* III.1 et III.5 comme loci canoniques du volontaire et de l'involontaire.
- **C4 (1).** La paire Bobzien PHILOPATOR, déjà reliée par `same_thesis_as`.

## 4. `needs_romain`, par source

- **Plotin (19).** Chapitres de Volkmann avec `<gap>`, et III.9.4-9, absents de sa division. Il faut les ré-ingérer depuis l'imprimé, de préférence Henry-Schwyzer, et choisir une édition de référence : le corpus porte désormais Volkmann pour la série corrigée et le TLG E pour les fragments VI.9.x.
- **Amand 1945 et la vague `wave_h_anchoring_chrysippe_carneade_cicero_2026_05_16`** (C3, 25 environ). Le chapitre visé est juste (Aulu-Gelle, *NA* VII.2 ; Cicéron, *Fat.* 23-25, 39-41 ; Diogène Laërce VII), mais le choix de la section n'est pas donné. S'y ajoutent Eusèbe, *PE* VI.6 et VI.7.35-41 (nœud absent), et la Philocalie 23.4.
- **Fürst 2022, Frede 2011.** Pages à consigner pour les renvois à Cic. *Fat.* 23-25 et 39-41. Pour « Frede 2009 », Michael ou Dorothea ?
- **Destrée-Salles-Zingano 2014.** Correspondance chapitre → œuvre tirée de la table des matières.
- **Alexandre, *De fato*.**
  - C3 : 7 rattachements de chapitres générés automatiquement, dont le pari rattaché au ch. 36 alors qu'il est daté des ch. 20-21.
  - C1 : 45 liens sans justification (ἐνδεχόμενον, ἐφ' ἡμῖν, εἱμαρμένη) et 16 liens conceptuels (cylindre, ἡγεμονικόν, λόγος κριτής…).
  - C3 `discusses` : 7 chapitres.
- **Augustin, *De libero arbitrio*.** 43 liens restants vers *voluntas*, II.16.43, et deux extraits trop courts (→ concupiscence).
- **Épictète, *Diatribes*.** 28 liens vers ἐφ' ἡμῖν et προαίρεσις. Les nœuds ne portent que des extraits glosés : il faut relire les chapitres entiers.
- **Lots de mars 2026 (`kg_manual_review_batch_05`, `kg_provenance_batch_04`).** 10 liens de type « meilleure source dans le KG », sans locus.
- **Liens `engages_with` et d'influence** (16). Gaventa → King et Gaventa → Meyer ; Ramelli → Frede 2009 ; Gourinat → Frede 2003 ; Gibbons → Koch ; Grgić → Ginet ; Kowalski → Kane ; Sextus → G. Strawson ; Tatien → apocatastase ; Épictète → Frankfurt ; Esséniens → nomisme d'alliance ; câblages `wave_i`, etc.
- **Notes de curation mêlées à la prose** (130). Avertissements de formulation, « NOT HELD LOCALLY », « to be checked » et mentions internes (« Volume majeur pour la thèse Romain »).
- **Fédou.**
  - Barth, *Destin et idée dans la théologie* : OpenAlex W7143270037.
  - Junod (dir.), *L'affaire Origène* : OpenAlex W7147037525.
- **C4.**
  - Pages contradictoires de la paire Bobzien PHILOPATOR.
  - McGuinness, coauteur de Tomberlin 1977, n'a pas de nœud personne.
- **Magna Moralia (TLG E).** Crochets à vérifier.
- **Sénèque, *Ep.* 99.25.** Citation grecque en Beta Code brut.
- **Cohen 2010.** `language: de` pour un article dont le titre est anglais.

## 5. Défauts systémiques et propositions

1. **Traductions machine.** Il en reste 2 349 dans le même lot (`translation_source = "AI batch: claude-opus-4-6"`). Les défauts relevés sont des défauts de lot. Proposition : les marquer toutes `citation_blocked` et les remplacer par des traductions publiées (Hall pour Méliton, Chadwick pour *Contre Celse*, etc.).
2. **Découpage de Plotin.** La série de tranches produite par l'ancien découpage de Perseus a glissé chapitre après chapitre. Proposition : ajouter une porte qui localise chaque passage grec dans son TEI de référence et compare le locus trouvé au locus déclaré, étendue à toutes les œuvres dont le TEI est disponible.
3. **Générateurs d'arêtes sans lecture.** Six générateurs sont en cause :
   - `terminology_scan` ;
   - `passage_to_concept` à confiance 0,5, sur l'œuvre entière ;
   - `auto_linked_from_description` sur un seul mot ;
   - `period_match` ;
   - `orphan_wiring` par mot-clé ;
   - « best available KG proxy ».

   Proposition : exiger `attested_by` avec locus ou page sur `cites_primary_source`, `evidenced_by` et `source_for` (sur le modèle de R16), et marquer `citability: discoverable_only` les arêtes non lues de ces générateurs.
4. **Résolution des noms sur le seul patronyme.** Proposition : bloquer la résolution quand le patronyme couvre plusieurs nœuds, et vérifier que l'année citée est compatible avec les dates de la personne.
5. **Texte stocké.**
   - 105 passages grecs contiennent des `<bibl>` ou des `<note>` de Perseus insérés dans le texte ;
   - les 129 passages de Boèce partagent une URN non résoluble et portent un texte OCR : il faut les ré-ingérer depuis `stoa0058.stoa001.perseus-lat2` ;
   - d'autres groupes partagent une même URN : Méthode `tlg2959.tlg002` (97), `aug_nat_bon` (39), Évodius (36), `aug_fulg` (26).
6. **Chemins privés.** La balise `[local-path]` subsiste dans les métadonnées d'environ 1 400 nœuds. Il faut la filtrer à l'export si l'API expose les métadonnées.

## 6. Non atteint

- **C1** : `queue_new_high_conf` (110), `queue_uncertain` (336), `work_level_edges` (61), `queue_language_mismatch` (4).
- **C2** : `queue_a_partial_coverage` (777, en dehors des œuvres déjà relues), `queue_a_identical_text` (35), `queue_b_layer_conflicts` (23), `queue_b_non_english` (371).
- **C3** : `queue_A_weak` (1 829).
- **C4** : `queue_ambiguous_pairs` (1 536), `queue_part_of_relations` (110), `queue_school_conflicts` (42), `queue_school_fill_in` (864), `queue_school_undetermined` (211).
- **Priorité 5 (ajouts)** : rien.
