# Réingestion complète de la *Magna Moralia* — plan dry-run du 17 août 2026

## Statut et périmètre

Cette vague est prête mais **n'a pas été appliquée au dépôt**. Elle couvre les
434 nœuds grecs `passage_arist_mm_*` et leurs 434 jumeaux de corpus identifiés
par `db_passage_id`. Aucun nœud `_en` n'existe dans cette famille et aucun texte
anglais n'est donc ciblé.

La source unique des remplacements est `TLG0086.TXT`, œuvre
`tlg0086.tlg022` (*Magna moralia*), sur le disque TLG E local. La plage complète
est `[3095923, 3270279)` en octets, avec des bornes demi-ouvertes. Les données
sont livrées dans `scripts/data_2026_08_17_mm_reingest.py`; l'application reste
dry-run par défaut dans `scripts/apply_2026_08_17_mm_reingest.py`.

## Méthode

1. Les 434 nœuds ont été triés numériquement par `canonical_ref`, de `1.1.1` à
   `2.17.2`. Les 434 UUID de corpus sont présents et uniques; toutes les langues
   déclarées sont `grc`.
2. Le grec OCR et le beta-code du TLG ont été réduits aux lettres de base et aux
   limites de mots. L'alignement global porte sur 23 528 mots OCR et 23 981 mots
   TLG. `difflib.SequenceMatcher` place 422 débuts de passage à l'intérieur d'un
   bloc de correspondance exact.
3. Les douze autres débuts tombent dans un écart OCR de seulement 1 à 3 mots.
   Chaque frontière a été testée localement avec les deux passages adjacents;
   deux erreurs de segmentation OCR ont demandé un décalage unique d'un mot
   (`1.20.3` et `2.16.2`).
4. Les 38 débuts enregistrés par la vague `linguistic_repairs_2026_08_17` sont
   reproduits exactement (38/38). Après conversion des anciennes fins inclusives
   en fins exclusives, 34/38 fins coïncident. Quatre fins anciennes ont été
   resserrées parce qu'elles incluaient du formatage ou le passage suivant:
   `1.1.23`, `1.1.26`, `1.4.2`, `1.28.1`. Le cas `1.1.23` contenait notamment
   `Ἀλλ'` tout en chevauchant le début de `1.1.24`; la partition globale retire
   cette duplication.
5. Le décodeur de la vague précédente est réutilisé: suppression des codes de
   formatage TLG, réunion des mots coupés par un trait de fin de ligne et un
   octet de contrôle, décodage par `beta_code`, restauration du sigma final
   devant `]`, normalisation NFC. Aucun caractère grec n'a été composé, corrigé
   ou complété hors de ce décodage.
6. Chaque enregistrement conserve le texte grec décodé, l'id du nœud, l'UUID du
   corpus, les deux octets, l'incipit attendu, le rapport de longueur, la
   similarité en lettres de base et les bornes des voisins. Le payload compacté
   est protégé par SHA-256 et est exposé à l'import sous forme de 434
   dictionnaires ordinaires.

À l'application, toutes les métadonnées existantes sont conservées sauf les
champs dérivés ou explicitement remplacés: `tlg_anchor` devient
`{start_byte, end_byte}`, `text_source` vaut `TLG0086 (TLG E disk)`, les longueurs
sont recalculées, le drapeau devenu caduc de `2.11.5` est retiré et le stamp
`mm_reingest_2026_08_17` est ajouté. Le nœud n'est modifié que si sa référence et
son UUID sont encore ceux attendus et si sa description commence par l'ancien
incipit enregistré, ou si elle porte le stamp de la vague linguistique.

## Résumé de l'ancrage

| Contrôle | Nombre | Résultat |
|---|---:|---|
| Frontières dans un bloc global exact | 422 | validées |
| Écarts OCR d'un mot | 8 | optimisation locale; un décalage de segmentation |
| Écarts OCR de deux mots | 3 | optimisation locale; un décalage de segmentation |
| Écart OCR de trois mots (`2.11.5`) | 1 | fenêtre locale unique et voisins concordants |
| Checkpoints de la vague précédente | 38 | 38 débuts reproduits exactement |
| Ordre des spans | 434 | `end(i) < start(i+1)`, écart minimal 1 octet |
| Rapport `len(TLG)/len(OCR)` | 434 | min. 0,974093; médiane 1,000000; max. 1,248889 |
| Similarité en lettres de base | 434 | min. 0,853933; médiane 1,000000; max. 1,000000 |
| `?` dans les remplacements | 0 | conforme |
| Passages non ancrés | 0 | aucun texte laissé en OCR |

Aucune justification hors seuil n'est nécessaire: les 434 rapports sont dans
l'intervalle demandé `[0,8 ; 1,25]`.

### Cas `passage_arist_mm_2_11_5`

Le passage est désormais ancré en `[3242506, 3242746)`. La fenêtre
`τὰ τοιαῦτα ἀπορεῖται` est unique dans le cadre strict formé par les frontières
de `2.11.4` et `2.11.6`; son début extrapolé concorde avec l'optimisation globale.
Le remplacement, entièrement décodé du TLG, commence:

> Ἔτι δὲ καὶ τὰ τοιαῦτα ἀπορεῖται, πότερον ἔσται ὁ σπουδαῖος τῷ φαύλῳ φίλος;

Le drapeau `needs_reingestion` peut donc être retiré. Il ne reste aucun nœud à
signaler comme non ancré.

## Dix échantillons avant/après

Les extraits sont tronqués pour la lisibilité; les remplacements complets sont
dans le fichier de données.

| Référence et octets | Avant (OCR courant) | Après (TLG0086 décodé) |
|---|---|---|
| `1.1.1` `[3095923,3096323)` | `πρῶτον ἄν εἴη… τὸ ἦθος ὡς μὲν… εἰπτεῖν, δόξειεν 〈ἂν〉` | `πρῶτον ἂν εἴη… τὸ ἦθος. ὡς μὲν… εἰπεῖν, δόξειεν [ ἂν]` |
| `1.1.10` `[3099211,3099638)` | `…τῆς βελτίστης… ἀλλὰ μὴν… αὐτῆς… ἔοικεν…` (déjà réparé) | même lecture TLG, réancrée avec la nouvelle convention de fin exclusive |
| `1.10.1` `[3126154,3126648)` | `— ἔτι δ᾿ ἄν τις… οἷον τὸ δένδρον ἐκ τοῦ σπέρματος` | `Ἔτι δ' ἄν τις… οἷον τὸ δένδρον ἐκ τοῦ σπέρματος·` |
| `1.20.3` `[3144011,3144488)` | `τούτωρντοίνυν… σκεππτέον ἂνεἴη… οὗτοι γὰρ σἴδσι` | `Τούτων τοίνυν… σκεπτέον ἂν εἴη… οὗτοι γὰρ οἴδασι` |
| `1.33.8` `[3161121,3161482)` | `ἑπεὶ… ἡ δικκιοσύνη καὶ τὸ δίκαρον…` | `Ἐπεὶ… ἡ δικαιοσύνη καὶ τὸ δίκαιον…` |
| `1.34.18` `[3181915,3182372)` | `τῷ δυνατὸς βουλεύεσθαι 〈εἶναι〉…` | `τῷ δυνατὸς βουλεύεσθαι [ εἶναι]…` |
| `2.8.11` `[3236279,3236661)` | `ἔσπτιν… πραγιάτων… εὐτνχία… πρές… εὐδαμονίαν` | `ἔστιν… πραγμάτων… εὐτυχία… πρός… εὐδαιμονίαν` |
| `2.11.5` `[3242506,3242746)` | `ἔ??ι δὲκαὶ… πότρρον ἔσταε ὁ σχο??δαῖος… φέλος` | `Ἔτι δὲ καὶ… πότερον ἔσται ὁ σπουδαῖος… φίλος` |
| `2.11.44` `[3255037,3255467)` | `τὰ δὴ τοιαῦτα…` (suite OCR plus courte) | `Τὰ δὴ τοιαῦτα…` avec la suite TLG complète; rapport 1,218978 |
| `2.16.2` `[3268884,3269080)` | `ἐλλείπ των… ἀλλ’ τῷ γε λόγῳ· ἧ δὲ φιλία` | `ἐλλείπων… ἀλλ' ἢ τῷ γε λόγῳ· ἡ δὲ φιλία` |

## Garanties de l'appliqueur

- dry-run par défaut; seule l'option `--write` écrit;
- choix d'un répertoire sandbox par `--data-dir` ou
  `MM_REINGEST_DATA_DIR`;
- application atomique par paire nœud/corpus et préconditions relues au moment
  de l'exécution;
- sauvegardes `*.bak-mm_reingest` des trois fichiers sélectionnés;
- idempotence par le stamp `mm_reingest_2026_08_17`;
- unicité des ids nœuds et UUID corpus, zéro arête pendante, égalité
  `source==source_id` et `target==target_id`, zéro triplet dupliqué;
- au moins 90 % de caractères grecs dans chaque description réécrite, après
  exclusion des espaces, chiffres et ponctuations;
- zéro `?`, zéro jumeau divergent et exclusion explicite des ids `_en`.

## Sorties de vérification

### Dry-run demandé

Commande:

```text
python3 scripts/apply_2026_08_17_mm_reingest.py
```

Sortie:

```text
mode: dry-run
records: 434
nodes done: 434
corpus done: 388
total changes: 822
skipped/reasons:
  corpus already replacement: 46
invariants: OK (unique ids=19753; dangling=0; split endpoints=0; duplicate triples=0; rewritten=434; under 90% Greek=0; question marks=0; different twins=0)
write: disabled (--dry-run default)
```

Les 46 jumeaux signalés comme déjà identiques ne sont pas omis: leur contenu est
déjà exactement le remplacement TLG; les 434 paires sont identiques après le
dry-run en mémoire.

### Écriture sandbox hors dépôt et idempotence

Répertoire créé par `mktemp`: `/private/tmp/mm-reingest-release.XHTkJ2`. Les trois
fichiers ont été copiés avant exécution.

Première exécution `--write`:

```text
mode: write
records: 434
nodes done: 434
corpus done: 388
total changes: 822
skipped/reasons:
  corpus already replacement: 46
invariants: OK (unique ids=19753; dangling=0; split endpoints=0; duplicate triples=0; rewritten=434; under 90% Greek=0; question marks=0; different twins=0)
wrote: /private/tmp/mm-reingest-release.XHTkJ2/nodes.jsonl
wrote: /private/tmp/mm-reingest-release.XHTkJ2/passages.jsonl
backups: /private/tmp/mm-reingest-release.XHTkJ2/nodes.jsonl.bak-mm_reingest, /private/tmp/mm-reingest-release.XHTkJ2/edges.jsonl.bak-mm_reingest, /private/tmp/mm-reingest-release.XHTkJ2/passages.jsonl.bak-mm_reingest
```

Seconde exécution `--write`:

```text
mode: write
records: 434
nodes done: 0
corpus done: 0
total changes: 0
skipped/reasons:
  corpus already replacement: 434
  node already applied: 434
invariants: OK (unique ids=19753; dangling=0; split endpoints=0; duplicate triples=0; rewritten=434; under 90% Greek=0; question marks=0; different twins=0)
write: no-op (0 changes)
```

Comparaison des sauvegardes sandbox avec les sources non modifiées du dépôt:

```text
nodes backup == repository source: OK
edges backup == repository source: OK
passages backup == repository source: OK
```

### Trois recherches TLG sur les cinq premiers mots

Les recherches ont été limitées à l'auteur `0086`, qui est précisément la
source demandée.

```text
$ python3 scripts/tlg_search.py search "Ἐπειδὴ προαιρούμεθα λέγειν ὑπὲρ ἠθικῶν" --authors 0086 --max 3
# needle(beta-base): 'epeidh proairoumeqa legein uper hqikwn'
TLG0086 (...) @byte 3095925
# total hits: 1

$ python3 scripts/tlg_search.py search "Ἔτι δὲ καὶ τὰ τοιαῦτα" --authors 0086 --max 3
# needle(beta-base): 'eti de kai ta toiauta'
TLG0086 (...) @byte 3242509
TLG0086 (...) @byte 5565567
TLG0086 (...) @byte 7174312
# stopped at --max 3

$ python3 scripts/tlg_search.py search "ἐν δὲ ἀνίσοις φίλοις οὐκ" --authors 0086 --max 3
# needle(beta-base): 'en de anisois filois ouk'
TLG0086 (...) @byte 3269822
# total hits: 1
```

Les trois requêtes touchent donc `TLG0086`; la deuxième retrouve bien le passage
visé à l'octet 3242509, même si ces cinq mots seuls existent aussi dans deux
autres œuvres du même auteur-fichier.

### Qualité Python

```text
$ ruff check --no-cache scripts/data_2026_08_17_mm_reingest.py scripts/apply_2026_08_17_mm_reingest.py
All checks passed!
```

### Périmètre des fichiers

La commande `git status --porcelain` n'a pas été exécutée, car la consigne
« no git commands » l'interdit explicitement. Le contrôle non-Git des écritures
de cette mission donne exactement les trois nouveaux fichiers suivants et
aucune écriture dans `data/kg/` ou `data/corpus/`:

```text
scripts/data_2026_08_17_mm_reingest.py
scripts/apply_2026_08_17_mm_reingest.py
data/audit/2026-08-17_mm_reingest_plan.md
```
