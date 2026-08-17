# Remappage des références de Plotin — plan et résultat du dry-run

Date : 2026-08-17  
Périmètre : 709 nœuds `passage_plotinus_vi_9_*`  
Statut : **livrables dry-run uniquement ; aucune application à `data/kg/` ni à `data/corpus/`**

## Résultat

Les 709 descriptions grecques ont été localisées dans `TLG2000.TXT` et les
citations ont été reconstruites à la précision
`ennead.treatise.chapter`. Il n'y a **aucun nœud irrésoluble** et **aucune
discontinuité d'offset**. Les descriptions ne figurent pas dans la charge utile
et ne sont jamais réécrites par l'applicateur ; leur SHA-256 sert au contraire
de précondition.

La précision est enregistrée **pour chaque nœud**, dans
`derived_citation.reference_precision` dans la charge utile et dans
`metadata.reference_precision` après application. Distribution :
`ennead.treatise.chapter` = 709 ; `ennead.treatise` = 0 ; sans précision = 0.

Les trois séquences contiguës obtenues sont :

| Ennéade | indices de fragment | nœuds | enveloppe TLG, octets `[start,end)` | première → dernière référence dominante | irrésolus | discontinuités start/end |
|---|---:|---:|---:|---|---:|---:|
| IV | 1–117 | 117 | 733 557–864 569 | `Enn. IV.4.34` → `Enn. IV.9.5` | 0 | 0 |
| V | 118–276 | 159 | 864 573–1 051 064 | `Enn. V.1.1` → `Enn. V.9.14` | 0 | 0 |
| VI | 277–709 | 433 | 1 051 070–1 548 750 | `Enn. VI.1.1` → `Enn. VI.9.11` | 0 | 0 |
| **Total** | 1–709 | **709** | 733 557–1 548 750 | IV.4.34 → VI.9.11 | **0** | **0** |

Le remappage intégral précise donc que l'Ennéade VI commence dès le fragment
277. Le fragment 305 était le premier échantillon VI de la vague antérieure,
pas une borne : l'exigence « 305 et suivants = VI » demeure intégralement
satisfaite.

## Lecture de `TLG2000.IDT`

`TLG2000.IDT` fait 2 048 octets. Il ne contient pas le texte : il décrit la
hiérarchie et donne l'état de citation à chaque bloc de 8 192 octets du TXT.

1. Le descripteur de l'œuvre 001 donne quatre enregistrements `0x11`, avec le
   niveau puis la longueur ASCII :

   ```text
   11 03 06 45 6e 6e 65 61 64       -> niveau 3 : Ennead
   11 02 07 63 68 61 70 74 65 72    -> niveau 2 : chapter
   11 01 07 73 65 63 74 69 6f 6e    -> niveau 1 : section
   11 00 04 6c 69 6e 65             -> niveau 0 : line
   ```

   Dans la référence canonique plotinienne, `Ennead/chapter/section` correspond
   à `ennéade/traité/chapitre`. Les niveaux utiles sont donc `w/x/y`, le niveau
   `z` étant la ligne Henry-Schwyzer.

2. Le marqueur `03 00 00 08` commence à `0x5a`; l'index commence à `0x5e`.
   Il contient exactement 190 entrées, une par bloc du TXT. Les entrées 0–188
   finissent par `0x0a`, la dernière par `0x09`.

3. Un octet de type `0x8*`, `0x9*`, `0xA*`, `0xB*` met respectivement à jour
   `z`, `y`, `x`, `w`. Le demi-octet bas est la commande : `0` incrémente,
   `1`–`7` posent un petit littéral, `8` lit un entier 7 bits, `B` un entier
   14 bits ; les autres formes avec suffixe ASCII sont également implémentées.
   Les échappements `0xE*` portent notamment l'auteur (`a`) et l'œuvre (`b`).
   Une modification d'un niveau supérieur réinitialise les niveaux inférieurs,
   conformément à la hiérarchie.

4. L'index IDT porte l'état immédiatement **avant** la frontière de bloc ; le
   snapshot redondant placé au début du bloc TXT porte la première ligne du
   bloc. Les 190 frontières concordent : 183 restent dans le même chapitre
   (ligne TXT = ligne IDT + 1, sauf le premier bloc), et 7 sont exactement une
   ouverture de chapitre (chapitre suivant, ligne TXT 1).

   Exemple de contrôle : l'entrée IDT du bloc 108 contient
   `98 88 88 8a`, soit V.1.8 ligne 10. À l'octet `0xd8000`, le TXT porte
   `... b5 98 88 88 8b`, soit V.1.8 ligne 11. L'update inline `0x90` à
   l'octet 885 913 incrémente ensuite le chapitre canonique vers V.1.9.

5. Après cette validation globale, tous les updates inline du TXT sont lus :
   la citation est donc connue à chaque lettre du texte, et non plus seulement
   à 8 192 octets près. Aucun mode hybride n'a été nécessaire.

Empreintes des sources effectivement parsées :

```text
TLG2000.TXT sha256  0e1be0d923b39818f387651c9a2fa4c52c1947a2273073e89362756445c40651
TLG2000.IDT sha256  217447870fc7db073904a044e5f5e1462323d66642312beea281a35165710f4f
```

## Alignement des 709 descriptions

La normalisation est celle de `scripts/tlg_search.py`, resserrée aux seules
lettres grecques de base translittérées en beta-code. Les accents, esprits,
ponctuations, espaces et césures de ligne ne participent donc pas au score ;
aucun caractère grec n'est produit ni corrigé.

Pour chaque nœud :

1. recherche d'ancres uniques de 32 lettres, tous les 16 caractères ;
2. estimation séquentielle de la position par la médiane des ancres ;
3. vérification locale par `difflib.SequenceMatcher` ;
4. enveloppe `[start,end)` de la première à la dernière lettre exactement
   appariée ;
5. comptage des lettres exactement appariées dans chaque chapitre IDT et choix
   du chapitre qui en porte le plus.

Les métriques observées sont :

| mesure | minimum | médiane | maximum |
|---|---:|---:|---:|
| part de lettres exactement appariées | 90,9535 % | 99,5680 % | 100 % |
| ancres uniques de 32 lettres | 2 | 38 | 54 |
| part du chapitre dominant | 50,0876 % | 100 % | 100 % |

Les fragments étant des tranches de taille fixe et non des unités de citation,
265 franchissent une frontière de chapitre, 23 une frontière de traité et 2 une
frontière d'Ennéade. La charge utile conserve pour chacun la citation de début,
la citation de fin et tous les votes par chapitre. Un chapitre dominant est un
résultat du comptage exact, pas une inférence thématique. Une égalité aurait
produit `unresolvable`; aucune ne s'est présentée.

Les deux bornes de chaque enveloppe sont strictement croissantes avec
`source_fragment_index` dans chacune des trois séquences IV, V et VI. Liste des
discontinuités : **aucune**.

## Points fixes obligatoires

| contrôle | résultat |
|---|---|
| nœud 1 | `Enn. IV.4.34`, octets 733 557–734 814 : Ennéade IV |
| nœud 50 | `Enn. IV.6.2`, octets 788 375–789 594 : Ennéade IV |
| nœud 136 | `Enn. V.1.9`, octets 885 840–886 886 ; 92,4883 % des lettres exactes en V.1.9 |
| nœuds 305–709 | 405/405 en Ennéade VI ; le nœud 305 est `Enn. VI.1.14` |

Le nœud 136 commence par une très courte fin de V.1.8, puis porte la
doxographie de V.1.9. Le comptage exact donne V.1.9 très nettement et reproduit
le point fixe indépendant.

## Dix vérifications contre une référence imprimée

Contrôle indépendant de l'IDT contre le TEI local de l'édition imprimée de
Richard Volkmann, *Plotini Enneades*, Teubner, 1883–1884 :
`data/audit/primary_fetch/plotinus_plotinus_enneads/tlg2000.tlg001.1st1K-grc1.xml`.
Les notes éditoriales sont exclues avant normalisation. `ancre 32` compte les
positions du nœud dont 32 lettres consécutives sont retrouvées dans la section
Volkmann citée.

| nœud | incipit du nœud | citation dérivée | ouverture de la section Volkmann | ancre 32 |
|---:|---|---|---|---:|
| 1 | « ἡμᾶς δὲ διδόντας τὸ μέρος αὑτῶν εἰς τὸ πάσχειν… » | `Enn. IV.4.34` | « ἡμᾶς δὲ διδόντας τὸ μέρος αὑτῶν εἰς τὸ πάσχειν… » | 793 |
| 50 | « τὸν αὐτὸν δὴ τρόπον καὶ ἐπ̓ ἀκοῆς δεῖ νομίζειν… » | `Enn. IV.6.2` | « εἰ οὖν μὴ οὕτως, τίς ὁ τρόπος; ἢ λέγει… » | 581 |
| 117 | « μὴ δή τις ἀπιστείτω: καὶ γὰρ ἡ ἐπιστήμη ὅλη… » | `Enn. IV.9.5` | « πῶς οὖν οὐσία μία ἐν πολλαῖς; ἢ γὰρ ἡ μία… » | 627 |
| 118 | « ἐπιστήσας γοῦν ὁ ἐπιστήμων ἐπάγει τὰ ἄλλα… » | `Enn. V.1.1` | « Τί ποτε ἄρα ἐστὶ τὸ πεποιηκὸς τὰς ψυχὰς… » | 418 |
| **136** | « καὶ σύμφωνος οὕτως… Ἀναξαγόρας δὲ νοῦν καθαρὸν… » | **`Enn. V.1.9`** | **« Ἀναξαγόρας δὲ νοῦν καθαρὸν καὶ ἀμιγῆ λέγων… »** | 499 |
| 200 | « καὶ τὸ εἶναι δὲ τοῦτο ἀπὸ τοῦ ἓν… » | `Enn. V.5.5` | « ἀλλ̓ ἐπ’ ἐκεῖνο ἐπανιτέον λέγουσιν, ὅτι μένει τὸ πρῶτον… » | 563 |
| 277 | « ὅσα δὲ ἐξετάσαντες τὰ ἐκείνων ἔθεντο ἐν γένεσιν… » | `Enn. VI.1.1` | « Περὶ τῶν ὄντων πόσα καὶ τίνα ἐζήτησαν… » | 682 |
| 305 | « εἰ δέ, ὅταν λέγωσι χθές… ἐν χρόνῳ παρεληλυθότι… » | `Enn. VI.1.14` | « τὸ δὲ ποῦ οἷον ἐν Λυκείῳ καὶ ἐν Ἀκαδημίᾳ… » | 340 |
| 500 | « καὶ πάντη μὲν στερισκόμενον ἐν τῇ χύσει τοῦ ἑνὸς… » | `Enn. VI.6.1` | « Ἆῤ ἐστὶ τὸ πλῆθος ἀπόστασις τοῦ ἑνός… » | 719 |
| 709 | « εἴ τις οὖν τοῦτο αὑτὸν γενόμενον ἴδοι… » | `Enn. VI.9.11` | « τοῦτο δὴ ἐθέλον δηλοῦν τὸ τῶν μυστηρίων… » | 325 |

Le contrôle demandé sur V.1.9 est particulièrement net : l'ouverture imprimée
est bien Anaxagore, suivie dans le nœud par Héraclite et Empédocle.

## Nœuds irrésolubles

**Aucun (0/709).** Le constructeur aurait conservé le flag et enregistré la
raison pour toute absence d'ancre, couverture exacte inférieure à 90 %, absence
d'état IDT ou égalité des votes. Ces branches n'ont pas été déclenchées.

## Effet prévu de l'applicateur

Pour chaque nœud résolu, et seulement après vérification de
`needs_reference_remapping: true`, de l'index, du SHA-256 de la description, de
l'URN d'œuvre et du stamp linguistique :

- `metadata.canonical_ref` devient `Enn. <Romain>.<traité>.<chapitre>` ;
- `metadata.cts_urn` devient
  `urn:cts:greekLit:tlg2000.tlg001:<ennéade>.<traité>.<chapitre>` ;
- `metadata.reference_precision` devient `ennead.treatise.chapter` ;
- `label` reprend la référence corrigée ;
- l'ancre TLG et l'évidence de dérivation sont ajoutées ;
- `needs_reference_remapping` est retiré et le stamp
  `plotinus_remap_2026_08_17` est posé.

Ni `description`, ni aucun fichier du corpus ne sont modifiés. L'applicateur ne
charge d'ailleurs aucun chemin sous `data/corpus/`.

## Vérifications exécutées

### Reproduction depuis les sources

```text
$ python3 scripts/data_2026_08_17_plotinus_remap.py --verify-source
records: 709
unresolvable: 0
IDT/TXT blocks: 190/190 citation-state matches
offset discontinuities: 0
Ennead coverage: IV=117, V=159, VI=433
source verification: OK (709/709 records reproduced byte-for-byte)
```

### Dry-run obligatoire sur le dépôt

Commande relancée sur l'état courant du graphe, après l'ajout des nouveaux
nœuds de littérature ; les 709 nœuds Plotin satisfont toujours toutes les
préconditions.

```text
$ python3 scripts/apply_2026_08_17_plotinus_remap.py
mode: dry-run
records: 709
resolvable: 709
unresolvable: 0
nodes done: 709
already applied: 0
precondition blocked: 0
descriptions changed: 0
invariants: OK (unique ids=19796; dangling=0; split endpoints=0; duplicate triples=0; remapped=709; unresolvable=0; description changes=0; offset discontinuities=0)
write: disabled (--dry-run default)
```

### Écriture sandbox et idempotence

Répertoire hors dépôt : `/tmp/plotinus-remap-current.HyZEoP` (résolu par macOS
en `/private/tmp/plotinus-remap-current.HyZEoP`). Il contient une copie de
l'état courant de `nodes.jsonl` et `edges.jsonl`.

```text
first --write:
mode: write
records: 709
resolvable: 709
unresolvable: 0
nodes done: 709
already applied: 0
precondition blocked: 0
descriptions changed: 0
invariants: OK (unique ids=19796; dangling=0; split endpoints=0; duplicate triples=0; remapped=709; unresolvable=0; description changes=0; offset discontinuities=0)
wrote: /private/tmp/plotinus-remap-current.HyZEoP/kg/nodes.jsonl
backup: /private/tmp/plotinus-remap-current.HyZEoP/kg/nodes.jsonl.bak-plotinus_remap

second --write (idempotence):
mode: write
records: 709
resolvable: 709
unresolvable: 0
nodes done: 0
already applied: 709
precondition blocked: 0
descriptions changed: 0
invariants: OK (unique ids=19796; dangling=0; split endpoints=0; duplicate triples=0; remapped=709; unresolvable=0; description changes=0; offset discontinuities=0)
write: no-op (0 changes)

backup equals original: OK
TARGETS=709 STAMPED=709 FLAGGED=0
```

SHA-256 du `nodes.jsonl` original et de sa sauvegarde sandbox :
`e000c8515a4abf312fbc1a10e709c1b6ab3d8e13aa48edf51761539cb73452bf`.
Le stamp contrôlé sur les 709 nœuds vaut exactement
`plotinus_remap_2026_08_17: canonical_reference_derived_from_tlg2000_idt`.

## Liste des livrables

La liste finale est produite sans Git, par `ls -l`, et doit contenir uniquement :

```text
scripts/data_2026_08_17_plotinus_remap.py
scripts/apply_2026_08_17_plotinus_remap.py
data/audit/2026-08-17_plotinus_remap_plan.md
```
