# Réparations linguistiques — plan de la vague 6

**Date** : 2026-08-17 · **Statut** : rédigé, **non appliqué** (`--dry-run` uniquement)
**Source** : `data/audit/2026-08-16_deep_audit_linguistic.jsonl` (1 589 constats)
**Scripts** : `scripts/data_2026_08_17_linguistic_repairs.py` (données + preuves),
`scripts/apply_2026_08_17_linguistic_repairs.py` (applier)

```bash
python3 scripts/apply_2026_08_17_linguistic_repairs.py           # dry run (défaut)
python3 scripts/apply_2026_08_17_linguistic_repairs.py --apply   # écrit + backups .bak-linguistic
```

## Règle de travail

Aucun mot de grec ou de latin n'a été composé. Chaque remplacement de texte
ancien est le décodage mécanique d'une plage d'octets du disque TLG E, et la
plage est enregistrée avec le texte pour qu'un relecteur relise les mêmes octets.
Quand la source n'a pas pu être fixée avec certitude, l'item est **signalé, pas
réécrit**. C'est la seule issue acceptable pour une leçon non vérifiée.

L'applier ne fait confiance à aucune liste figée : chaque écriture est précédée
d'une précondition évaluée sur les données vivantes (la corruption est-elle
encore là ? l'URN porte-t-il encore le mauvais identifiant TLG ? la langue
détectée maintenant contredit-elle encore la langue déclarée ?). C'est cette
règle qui a fait tomber 215 des 221 constats du lot 5a.

## Résultat du `--dry-run` complet

```
nodes 20122 -> 20113   edges 54167 -> 54149   corpus 21112 -> 21103
  flag_clement_protrepticus: 1
  flag_needs_reingestion: 1
  flag_plotinus_fragment_refs: 709
  flag_pre_unicode_font: 7        (+ 13 lignes corpus listées, non modifiables)
  flag_simplicius_work: 1
  mark_apparatus_gcs: 82
  mark_composite_latin: 198
  normalise_nfc: 45
  reattribute_exhortatio: 51      (+ 102 arêtes repointées)
  remove_theophrastus_misfiling: 9 nœuds, 18 arêtes, 9 lignes corpus
  repair_magna_moralia: 38        (+ 36 jumeaux corpus, 2 sautés)
  repair_tokens: 4
  requalify_en__already_fixed: 121
  requalify_grc: 72               (8 sautés — faux positifs)
  requalify_lat: 5                (18 sautés)
  rewrite_cts_urn: 225 nœuds sur 4 familles
invariants: OK
```

---

## Lot 1 — Magna Moralia : grec OCR corrompu, restauré depuis TLG E

**38 corrigés · 1 signalé · 395 documentés sans y toucher.**

Les 434 nœuds `passage_arist_mm_*` portent
`urn:cts:greekLit:tlg0086.tlg022.1st1K-grc1`, URN que `TLG0086.IDT` confirme
(« 022 Magna moralia »). Leur texte est un mauvais OCR de cette œuvre. 39 nœuds
affichent la corruption (`??`, `**`) ; le même OCR a aussi substitué
silencieusement des lettres partout ailleurs.

**Méthode** : un alignement séquentiel de l'œuvre entière, pas une devinette par
nœud. Les 434 nœuds triés par `canonical_ref` (1.1.1 → 2.17.2), chacun réduit à
ses lettres de base sans accents, sa première fenêtre propre de 4 mots cherchée
dans la même réduction de `TLG0086.TXT` en avançant depuis la position du nœud
précédent. **433/434 s'ancrent**, les positions sont strictement croissantes, et
le rapport longueur d'empan / longueur du nœud a une **médiane de 1,01**. Les
bornes sont ensuite affinées par `difflib` puis calées sur des frontières de mot,
et la plage d'octets est décodée par `beta_code`.

**Contrôles** : texte de sortie ≥ 92,9 % de lettres grecques, rapport
nouveau/ancien de longueur de médiane 1,005, aucun `?` résiduel, aucun trait
d'union de fin de ligne, sigma final rétabli devant crochet.

### Preuves (4 exemples sur 38)

| nœud | ancre TLG0086 | ancien | nouveau |
|---|---|---|---|
| `passage_arist_mm_1_1_10` | octets 3099211-3099637 | `ἀγαθὸν τ?? τέλος … τῆς βελσίστης … ὠλλὰ μ??ν γε π??λισικὴ βελείστη` | `ἀγαθὸν τὸ τέλος … τῆς βελτίστης … ἀλλὰ μὴν ἥ γε πολιτικὴ βελτίστη` |
| `passage_arist_mm_2_11_1` | octets 3241075-3241355 | `ἐφ' ἄπασι δὲ τ??πς ὑπὸρ φιλίας ἀναυχαῖόν ἔσαιν εἰπεν` | `Ἐφ' ἅπασι δὲ τούτοις ὑπὲρ φιλίας ἀναγκαῖόν ἐστιν εἰπεῖν` |
| `passage_arist_mm_2_11_6` | octets 3242749-3243140 | `ἐιοριστέον ἄ εὔη ὑ??ὲρ πλίας … οὐκ ὀρθῶρ … τὴν γὰρ φmίαυ` | `διοριστέον ἂν εἴη ὑπὲρ φιλίας … οὐκ ὀρθῶς … τὴν γὰρ φιλίαν` |
| `passage_arist_mm_1_2_1` | octets 3106225-3106752 | `τὰ μὲν τέμια, τὰ δ' ἐπαινι??ά, τὰ δὲ δ??νάμες` | `τὰ μὲν τίμια, τὰ δ' ἐπαινετά, τὰ δὲ δυνάμεις` |

### Signalé, non réécrit

`passage_arist_mm_2_11_5` — aucune fenêtre propre de 4 mots ne survit de façon
unique dans TLG0086 : sa position dans le traité n'a pas pu être fixée avec
certitude. `needs_reingestion: true`, texte inchangé.

### Découverte à porter au passif

Les **395 autres nœuds Magna Moralia** portent le même OCR sans le montrer :
`βελσίστης` pour `βελτίστης`, `ὠλλὰ` pour `ἀλλὰ`, `αὐτῇς` pour `αὐτῆς`,
`ἔικεν` pour `ἔοικεν`. Ils ne sont **pas** touchés ici : réécrire 395 passages en
bloc est une ré-ingestion, pas une réparation. La chaîne d'alignement construite
pour ce lot les traiterait tous — c'est le travail d'une vague dédiée, décidée
comme telle.

### Réparations chirurgicales (lot 1b)

Trois nœuds sont par ailleurs fidèles à une bonne édition (rapport `difflib`
contre TLG ≥ 0,99) et portent des guillemets et marques d'élision éditoriales
qu'il serait dommage de perdre. Seul le token corrompu est remplacé :

- `passage_just_apol1_40` — `(??) αρέστησαν` → **`παρέστησαν`** et
  `ἐν τρ (??) μῳ` → **`ἐν τρόμῳ`** (Ps. 2,2 et 2,11 LXX cités par Justin ;
  TLG0645 octets 61989-65745).
- `passage_plotinus_vi_9_136` — `ʽ??’αιρεῖ` → **`διαιρεῖ`** et `τοσἁ??’τα` →
  **`τοσαῦτα`** (TLG2000 octets 885839-886887, Enn. V.1.9).

`passage_meth_dla_41`, rangé par l'audit avec ce groupe, **n'est pas du grec
corrompu** : c'est l'apparat critique GCS en allemand (« u. verb. », « nach
Gifford », « mit dem Vorhergehenden », sigles C D E S Ph). Traité au lot 5d.
`passage_simpl_in_ench_1` et `_6` sont supprimés par le lot 2 et ne sont donc pas
réparés.

---

## Lot 2 — neuf passages « Simplicius » qui sont Théophraste

**9 nœuds supprimés · 18 arêtes · 9 lignes corpus · 1 œuvre signalée.**

`passage_simpl_in_ench_1..9` sont étiquetés « Simplicius, In Epicteti Enchiridion
Commentarius » et portent `urn:cts:greekLit:tlg0093.tlg001…`. `TLG0093.IDT` :
auteur TLG0093 = **Theophrastus**, œuvre 001 = **Historia plantarum**. L'URN est
honnête ; c'est l'étiquette qui ment.

**Preuves** (vérifiées avant suppression) :

- `_1` : `Τῶν φυτῶν τὰς διαφορὰς καὶ τὴν ἄλλην φύσιν ληπτέον…` — HP I.1.1,
  TLG0093 octet 100, sous l'en-tête `ΘΕΟΦΡΑΣΤΟΥ ΠΕΡΙ ΦΥΤΩΝ ΙΣΤΟΡΙΑΣ Α`.
- `_6` : `Περὶ μὲν οὖν δένδρων καὶ θάμνων εἴρηται πρότερον…` — HP VI.1.1,
  TLG0093 octet 324364, sous le marqueur de livre `Ζ`.
- `_1` cite `Μενέστωρ`, botaniste du V<sup>e</sup> s. av. J.-C. que seul
  Théophraste transmet.

L'applier ne supprime pas sur la foi de la liste : il exige que chaque nœud
contienne du vocabulaire botanique (`φυτ|δένδρ|θάμν|καρπ|φύλλ|ῥίζ|σπέρμ|βλαστ|φλοι`)
et que les arêtes touchées soient exactement les 18 attendues.

`work_simplicius_in_enchiridion` reste sans aucun passage → `needs_text_ingestion`.
Le vrai texte est l'édition d'I. Hadot (CAG / Brill 1996 ; SC 500-503 pour le
français). **Non ingéré ici.**

---

## Lot 3 — identifiants TLG faux dans les CTS URN

**225 URN réécrites sur 4 familles.** Chaque identifiant a été vérifié dans
`AUTHTAB.DIR` et dans les tables d'œuvres `TLG****.IDT`, pas de mémoire.

| id | ce que dit le disque |
|---|---|
| `tlg9857` | **absent d'AUTHTAB.DIR** — cet auteur TLG n'existe pas |
| `tlg0094` | Pseudo-Plutarchus — mais `TLG0094.IDT` ne contient que *De fluviis*, *De musica*, *Placita philosophorum* : **pas** le *De fato* |
| `tlg0007` | Plutarchus — `TLG0007.IDT` : **« 108  De fato [Sp.] (568b-574f) »** |
| `tlg0338` | Sosiphanes, Trag. |
| `tlg0555` | Clemens Alexandrinus |
| `tlg2042` | Origenes |
| `tlg2959` | absent du disque TLG E ; identifiant canonique déjà employé par ce graphe |

### 3a. Pseudo-Plutarque, *De fato* — 57 nœuds

`tlg9857.tlg062.perseus-grc1` → **`tlg0007.tlg108`**.

La proposition de l'audit (`tlg0094`) est **réfutée par la table d'œuvres** :
TLG0094 ne contient pas le *De fato*. Le traité est classé parmi les *Moralia* de
Plutarque, marqué `[Sp.]`. Le numéro d'œuvre 108 est lu dans les octets de
`TLG0007.IDT` et corroboré par ses voisins (067 = *De liberis educandis* [Sp.],
107 = *De sera numinis vindicta*, 109 = *De genio Socratis*), tous conformes aux
numéros publiés du canon TLG.

**Attestation du texte** : `passage_plut_fat_1` lit
`…εἱμαρμένη διχῶς καὶ λέγεται καὶ νοεῖται· ἡ μὲν γάρ ἐστιν ἐνέργεια ἡ δ' οὐσία`,
trouvé **une seule fois** dans TLG0007, à l'octet 6323294, dans la section *De fato*.

Le suffixe `perseus-grc1` est abandonné : il faisait partie de l'URN inventée et
aucune édition Perseus de `tlg0007.tlg108` n'a pu être vérifiée sur disque. Mieux
vaut une URN au niveau de l'œuvre qui résout qu'une URN de version qui ment.

### 3b. Méthode d'Olympe — 97 + 14 nœuds

`tlg0338.tlg307.perseus-grc1` (Sosiphanes le tragique ; et une œuvre n° 307 pour
un tragique est en soi impossible) → **`tlg2959.tlg002`**.
`tlg2042.tlg014` = Origène, *Fragmenta in librum primum Regnorum* → même cible.

**Contrôle de contenu** : `passage_meth_dla_1` ouvre sur
`Ὁ μὲν Ἰθακήσιος γέρων κατὰ τὸν τῶν Ἑλλήνων μῦθον, τῆς Σειρήνων βουλόμενος
ἀκοῦσαι ᾠδῆς…` — le proème d'Ulysse et des Sirènes du *De autexousio*. Le graphe
porte déjà `tlg2959.tlg002` sur `work_methodius_de_libero_arbitrio` et sur trois
nœuds passage.

### 3c. Origène, *Philocalie* — 57 nœuds (**ajout à la liste de l'audit**)

`tlg2042.tlg028` = `TLG2042.IDT` : « Commentariorum series in evangelium
Matthaei ». La Philocalie est **`tlg2042.tlg019`**, « Philocalia sive Ecloga de
operibus Origenis a Basilio et Gregorio Nazianzeno facta (cap. 1-27) ». L'auteur
était bon, le numéro d'œuvre non.

### 3d. ⚠ L'audit avait celui-ci à l'envers — Clément / Origène

L'audit demandait de réécrire **51 nœuds `passage_clement_*` vers `tlg0555`**.
Cela aurait **détruit une URN correcte**. Consigne non exécutée.

`passage_clement_protr_1` lit :
`…Ἀμβρόσιε θεοσεβέστατε καὶ Πρωτόκτητε εὐσεβέστατε…`

Ambroise et Protoctète sont les dédicataires de l'*Exhortatio ad martyrium*
d'**Origène**. La formule se trouve **une seule fois dans tout TLG2042**, à
l'octet 2355789. `passage_clement_protr_26` est l'épisode des martyrs Maccabées
devant Antiochus (*Exh. mart.* 22-27) ; `passage_clement_protr_51` est la clausule
`Ταῦτά μοι κατὰ τὸ δυνατὸν … πρὸς τὸν παρόντα ἀγῶνα χρήσιμα` — et l'*Exhortatio*
compte exactement **51 chapitres**, un par nœud.

`TLG2042.IDT` : œuvre 007 = *Exhortatio ad martyrium*. **L'URN `tlg2042.tlg007`
est juste.** Ce qui est faux, c'est l'identifiant, le label, l'auteur, le titre
d'œuvre et les deux arêtes, qui disent tous « Clément, Protreptique ».

C'est l'incident consigné dans `docs/development/ingestion-rules.md` sous R3b —
consigné **dans le sens inverse**. Le texte tranche.

**Correction appliquée** : `author` → Origen of Alexandria, `work_title` →
Exhortatio ad martyrium, `label` → « Origen, Exhortation to Martyrdom N »,
`canonical_ref` → « Exh. mart. N », 51 arêtes `authored_by` repointées vers
`person_origen_alexandria_185_254ce_s9t0u1v2` et 51 arêtes `part_of` vers
`work_origen_exhortation_martyrdom` (102 au total).
`work_clement_protrepticus` reste vide → `needs_text_ingestion` : le
*Protreptique* de Clément (TLG0555.tlg001) n'est plus représenté dans le corpus.

**Dette assumée** : les 51 identifiants restent `passage_clement_protr_*` alors
qu'ils portent Origène. C'est un WARN R9, pas un BLOCK. Le renommage toucherait
51 nœuds et 102 extrémités d'arêtes et **aucune autre référence** (vérifié : la
chaîne n'apparaît nulle part ailleurs dans `nodes.jsonl`, `edges.jsonl` ou
`passages.jsonl`), mais il change des clés primaires que la production sert déjà.
La dette est enregistrée dans `metadata.id_debt` de chaque nœud.

---

## Lot 4 — polices grecques pré-Unicode : **20 signalés, 0 écrit**

7 nœuds KG + 13 lignes corpus (Boèce *Cons.*, Lactance *Div. Inst.*, Cassien
*Conl.* 13) où une police grecque héritée a été OCRisée en pseudo-latin :

> `Nonne adulescentulus dvo πίϑους, xbv ukv eva xαxωv, tdv ds ἔτεϱοv έἀωv in Iovis limine…`

**`regreek` 0.7.2 a été testé et ne s'applique pas.** Ses décodeurs transposent un
flux d'octets *uniformément* encodé dans une police héritée ; ici l'entrée est un
débris post-OCR où le latin environnant est du vrai latin. Son propre détecteur
n'arrive pas à les séparer :

```
>>> regreek.detect_encoding("Nonne adulescentulus dvo πίϑους, xbv ukv eva …")
[graeca 0.678, graeca2 0.678, odyssea 0.678, symbolgreek2 0.678]   # égalité à 4
>>> regreek.decode_text(même_texte, "graeca").text
'Νοννε αδυλεσχεντυλυς δό πίϑους ξβ́ ύκ έα xαxωv τδ́ δς ἔτεϱοv έἀωv ιν Ιόις λιμινε'
```

— le latin a été grécisé et le grec est toujours faux.

L'attestation par édition a échoué aussi : aucune édition critique de la
*Consolatio*, des *Divinae Institutiones* ou des *Conlationes* sous
`~/Desktop/DOCTORAT/Doctorat SHAL/`, et aucun des trois auteurs n'est sur le
disque TLG E (ils écrivent en latin).

**Action** : `pre_unicode_font: true` + `needs_reocr: true` sur les 7 nœuds KG,
sans écrire une lettre de grec. Les 13 lignes corpus n'ont pas de colonne
metadata : elles sont listées dans le module de données pour la file de re-OCR.

---

## Lot 5 — passages qui mentent sur leur langue

### 5a. « 221 nœuds `lat` sans latin » → **215 sont un faux positif de l'audit**

Mesure sur les 221 identifiants de l'audit, sur les données vivantes : **215
contiennent du latin**. Leur forme est

> `<amorce en anglais>. LATIN TEXT (verified from database, passage_id: …): <latin>`

Le détecteur de l'audit, ne lisant que la tête du champ, a vu de l'anglais.
`language: lat` est juste pour ces 215 ; ce qui leur manque, c'est une marque de
champ composite — `content_kind: commentary_plus_text` (198 posées, les autres
n'étant pas de type `passage`).

**5 seulement** (tous de type `passage`) n'ont aucun latin →
`language: eng` + `needs_text_ingestion` :
`passage_aug_gla_1_13`, `_1_14`, `_1_21`, `_1_25`, `passage_aug_lib_arb_1_11_21`.
18 sautés, dont `person_seneca_4bce_65ce_a1b2c3d4` : sur un nœud `person`,
`metadata.language` nomme la langue dans laquelle l'auteur écrit, pas celle de la
description — ce n'est pas un défaut.

*C'est précisément cette différence entre la liste figée et la re-détection au
moment de l'application qui a évité 215 mauvaises écritures.*

### 5b. « 121 nœuds `_en` portant la source non traduite » → **déjà corrigé, no-op**

Les 121 portent déjà `passage_role: untranslated_duplicate` et la langue de leur
original, posés par `apply_2026_08_16_deep_audit_structural.py`. Vérification
vivante : 118 `language=lat` + 3 `language=grc`, **0 déclarant encore `eng`**.
L'audit les a re-signalés d'après le suffixe `_en`, pas d'après les métadonnées
courantes. Consigné pour ne pas rouvrir le dossier.

### 5c. « 86 nœuds `grc` sans grec » → 72 requalifiés, 8 faux positifs, 6 vers 5d

| sous-ensemble | n | action |
|---|---|---|
| `passage_origen_philocalia_2[3-7]_*` — français (traduction SC), `grc` | 47 | `language: fra`, `content_kind: modern_translation`, `needs_text_ingestion` |
| `passage_origen_pa_3_1_*` — français (SC), `grc-lat` | 23 | `language: fra`, `passage_role: translation`, `original_node_id` résolu |
| `passage_origen_com_rm_7_16*` — latin (Rufin) | 2 | `language: lat` |
| `passage_meth_dla_*` — allemand (apparat GCS) | 6 | traités par 5d |
| divers | 8 | **sautés** : contiennent 26 à 41 caractères grecs — faux positif |

Le rattachement des 23 nœuds *De principiis* III.1 n'est **pas** une paire codée
en dur : le graphe porte `passage_origen_philocalia_21_1..24` avec la **CTS URN
identique** (`urn:cts:greekLit:tlg2042.tlg002:3.1.N`) et du grec réel ; l'applier
apparie sur l'URN, exige que la cible soit en `grc`, contienne du grec et diffère
du texte français. **23/23 appariés.** R7 est satisfaite.

Les 47 nœuds Philocalie 23-27 n'ont pas de jumeau grec dans le graphe. Leur poser
`passage_role: translation` créerait un **nouveau BLOCK R7** (traduction dont
l'original ne résout pas) : ils gardent `original`, reçoivent la langue honnête
`fra`, et sont marqués `modern_translation` + `needs_text_ingestion`.

### 5d. L'apparat critique GCS ingéré comme s'il était Méthode — **82 nœuds**

`passage_meth_dla_41` est représentatif :

> `…κακὸς ὑπάρχει < D Ι κακὸς < C ι ἡ ἐνέργεια C Ι ἃ δὲ … S 13 λαμβάνειν S u. verb. ἤρξατο mit dem Vorhergehenden κἀκεῖνος] ἐκεῖνος S …`

C'est l'*apparatus criticus* de Bonwetsch (GCS) : sigles C D E S Ph,
abréviations éditoriales allemandes, témoins arménien (Ezn) et slavon.

L'audit en avait trouvé 22. Une règle exigeant ≥ 3 mots-outils allemands **et**
un marqueur d'apparat (`»…«`, ` < `, `u. `, `wohl`, `Ezn`, un sigle collé à un
numéro de ligne) en trouve **82 des 97** nœuds `passage_meth_dla_N`. Une
quinzaine seulement portent du contenu réel.

Action : `content_kind: apparatus_gcs`, `passage_role: apparatus`,
`language: deu`, `needs_text_ingestion: true`. **Découverte imprévue majeure** :
le *De autexousio* de Méthode est, aux quatre cinquièmes, un apparat critique
présenté comme le texte de l'auteur ; la recherche pouvait renvoyer une entrée
d'apparat comme si c'était Méthode.

### 5e. Lots volontairement laissés de côté

- **279** « grc mais majoritairement anglais » et **30** « grc mais français » :
  nœuds multilingues structurés (`**Reference:** … **Original Greek:** … `). Ils
  **contiennent** le grec qu'ils annoncent. Réécrire `language` serait faux ; ce
  qu'il leur faut est un `content_kind: structured_multilingual`, décision de
  schéma hors du périmètre de cette vague.
- **76** nœuds coquilles `person`/`work` déclarés `language: Greek` : sur ces
  types, le champ nomme la langue d'écriture de l'auteur. Pas un défaut. Reste
  une dérive de vocabulaire (`Greek` vs `grc`), signalée, non corrigée.

---

## Lot 6 — encodage

**6a. NFC : 45 lignes de `edges.jsonl` normalisées.** Les 45 portent le défaut
dans un seul champ, `metadata.provenance.source`, et il s'agit des 45 occurrences
de la même chaîne bibliographique (« Jean Voelke - L'idée de volonté… ») dont les
caractères accentués sont stockés décomposés. Aucun grec n'est concerné.
*(Le brief visait `matched_label` ; ce champ n'est pas en cause.)*

**6b. Apostrophe d'élision grecque : rien à faire.** Un balayage de **tous** les
champs texte de **toutes** les arêtes trouve **U+2019 uniquement** — 63
`metadata.provenance.source`, 8 `metadata.original_citation`, 4 `metadata.note`,
1 `metadata.furst_source`, 1 `metadata.scope` — et **zéro** occurrence de U+1FBD
(coronis), U+1FBF (esprit doux) ou U+02BC. L'élision est déjà unifiée. Aucune
écriture, donc aucun risque de toucher un esprit doux légitime.

---

## Lot 7 — Plotin : 709 numéros de fragment présentés comme des citations

**Défaut intact** — aucune vague antérieure n'y a touché. Les 709 nœuds
`passage_plotinus_vi_9_N` portent tous :

```
cts_urn        urn:cts:greekLit:tlg2000.tlg001.perseus-grc1:1
canonical_ref  Enn. VI.9.N          (N = 1 … 709)
work_title     Enneades
```

c'est-à-dire que chacun prétend être *Enn.* VI.9, un traité de 11 chapitres.

**Ce qu'ils sont réellement** : des tranches consécutives des *Ennéades* dans
l'ordre de lecture. Dix d'entre eux ont été ancrés dans TLG2000 par recherche de
texte unique ; les octets croissent régulièrement avec N, et l'Ennéade lue sur le
bloc de citation TLG le plus proche donne :

| nœud | octet TLG2000 | Ennéade |
|---|---|---|
| 1 | 733 557 | IV |
| 50 | 788 447 | IV |
| **136** | 885 857 | **V** (texte = *Enn.* V.1.9, doxographie d'Anaxagore, Héraclite, Empédocle) |
| 200 | 960 741 | V |
| **305** | 1 083 694 | **VI** |
| 306 | 1 084 660 | VI |
| 400 | 1 193 081 | VI |
| 500 | 1 306 440 | VI |
| 600 | 1 423 586 | VI |
| 709 | 1 548 122 | VI |

Le texte est donc de l'authentique Plotin, la tranche court de l'Ennéade IV à la
fin de la VI, et `canonical_ref` est un index courant qui n'a jamais été une
citation. Le n° 305 bascule bien en Ennéade VI, comme l'annonçait l'audit.

**La vraie référence est-elle reconstituable ?** Partiellement, et cela ne suffit
pas :

- Le **numéro d'Ennéade** l'est dès maintenant, par les blocs de citation TLG —
  mais ces blocs ne tombent qu'aux frontières de 8 192 octets (190 blocs pour un
  fichier de 1,5 Mo, soit environ un bloc pour 3 à 4 nœuds). La résolution est
  l'Ennéade, jamais le traité ni le chapitre.
- Traité et chapitre vivent dans les octets de niveau des mêmes blocs, qu'il
  faudrait décoder contre la spécification du format TLG — et l'on resterait à
  8 Ko près.

Écrire « *Enn.* V » là où le lecteur attend « *Enn.* V.1.9 » remplace une fausse
citation précise par une vraie citation vague : toujours pas une citation.

**Conclusion : ré-ingestion mappée nécessaire.** Ce qu'il faudrait :
ré-ingérer les *Ennéades* depuis une édition porteuse de citations (le XML
Perseus `tlg2000.tlg001.perseus-grc1`, ou Henry-Schwyzer), puis aligner les 709
tranches existantes sur ce texte — l'alignement séquentiel construit pour le lot 1
s'y transpose directement, l'ancrage des dix échantillons montre qu'il tiendra.

**Ce que fait cette vague, faute de mieux** : retirer les affirmations fausses
sans en inventer une nouvelle.
`canonical_ref` → `null`, l'index conservé dans `source_fragment_index`,
`cts_urn` ramenée à l'URN d'œuvre `urn:cts:greekLit:tlg2000.tlg001` (le `:1`
prétendait Ennéade I), `needs_reference_remapping: true`. **709 nœuds.**

---

## Garanties de l'applier

- `--dry-run` par défaut ; `--apply` est explicite.
- Idempotent : tampon `linguistic_repairs_2026_08_17` en metadata, relu avant
  chaque écriture ; le second passage ne fait rien.
- `metadata` sérialisée en chaîne JSON relue et réécrite dans la même forme.
- Sauvegardes `.bak-linguistic` des trois fichiers avant toute écriture.
- Invariants vérifiés **avant** sauvegarde, y compris en dry-run :
  identifiants de nœuds uniques, 0 arête pendante, `source == source_id` et
  `target == target_id`, 0 triplet dupliqué, 0 boucle, `passage_id` de corpus
  uniques, aucun nœud réparé ne contenant encore `??`, aucun nœud réparé
  descendu sous 80 % de grec.
- Rapport de ce qui a été fait **et** de ce qui a été sauté, avec le motif.

## Reste à décider (hors périmètre de cette vague)

1. **395 nœuds Magna Moralia** au même OCR silencieux → vague de ré-ingestion
   dédiée (la chaîne d'alignement existe).
2. **709 nœuds Plotin** → ré-ingestion mappée depuis une édition citée.
3. **~82 nœuds Méthode** réduits à l'apparat GCS → le texte du *De autexousio*
   reste à ingérer.
4. Renommage des **51 identifiants** `passage_clement_protr_*` (R9).
5. `content_kind: structured_multilingual` sur les **309** nœuds composites.
6. Normalisation du vocabulaire de `metadata.language` (`Greek`/`Latin` → `grc`/`lat`).
