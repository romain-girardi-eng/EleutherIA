# Ré-ingestion de Méthode d’Olympe, *De autexousio* — plan bloqué par la source

## Verdict

La ré-ingestion grecque demandée ne peut pas être produite à partir du disque
fourni. Les deux fichiers nommément requis, `TLG2959.TXT` et `TLG2959.IDT`,
sont absents de `~/Desktop/Romain/TLGE`; `TLG2959` est également absent de
`AUTHTAB.DIR`. Le plan linguistique antérieur documentait déjà ce fait à la
section 3 (« `tlg2959` | absent du disque TLG E »).

En conséquence, ce lot ne contient **aucun texte grec de remplacement, aucun
ancrage TLG et aucune citation IDT prétendument vérifiée**. Cela respecte
l’interdiction de générer ou corriger le grec. Le seul delta produit est
conservatoire : les 82 nœuds déjà qualifiés `apparatus_gcs` reçoivent
`needs_locus_mapping: true` et la raison exacte de l’absence de source. Leur
description, leur langue `deu`, leur rôle `apparatus`, leur
`content_kind: apparatus_gcs` et `needs_text_ingestion: true` restent intacts.

## Inventaire et identification de l’œuvre

- Répertoire examiné : `~/Desktop/Romain/TLGE`.
- Fichiers d’auteurs : 1 823 `.TXT` et 1 823 `.IDT`.
- `TLG2959.TXT` : absent.
- `TLG2959.IDT` : absent.
- Entrée littérale `TLG2959` dans `AUTHTAB.DIR` : absente.
- SHA-256 d’`AUTHTAB.DIR` :
  `8457a0cbe7943d148157a4ec8fb001c5412cc6ee5655e1c6bac14a818ed5e731`.

Le graphe et le plan antérieur proposent `tlg2959.tlg002`, mais, sans l’IDT,
le numéro d’œuvre 002 n’est pas ré-attestable sur le disque. Il est donc noté
comme **candidat hérité**, non comme identification accomplie. Il serait
mensonger d’annoncer ici que l’IDT identifie *De autexousio*.

## État de la famille

La famille contient 111 nœuds :

| État | Nombre |
|---|---:|
| `apparatus_gcs` / `apparatus` / `deu` / `needs_text_ingestion` | 82 |
| autres nœuds `grc` déclarés originaux | 22 |
| traductions anglaises | 7 |

Les 82 cibles possèdent un `canonical_ref` de forme `PG 18.N`, mais `N` est le
numéro de fragment du lot (1 à 107 avec lacunes), pas une citation canonique
TLG. Les descriptions sont des tranches séquentielles de l’édition GCS : elles
peuvent commencer ou finir au milieu de l’apparat et contiennent parfois un
segment grec de la page éditée. Sans le flux TLG2959, ces indices ne suffisent
pas à fixer honnêtement des bornes source.

## Méthode prévue après restauration de TLG2959

Le module de données conserve le décodeur d’index binaire éprouvé sur Plotin :
état hiérarchique des niveaux, opcodes d’incrément/valeur/suffixe et blocs de
8 192 octets. Il sait aussi extraire les numéros et titres d’œuvre des en-têtes
IDT. Lorsque les fichiers seront disponibles, il faudra :

1. identifier *De autexousio* dans l’IDT, sans reprendre aveuglément `tlg002` ;
2. valider chaque état de bloc IDT contre l’instantané de bloc TXT ;
3. isoler le flux de l’œuvre et le décoder mécaniquement depuis le bêta-code ;
4. tenter l’alignement séquentiel des seuls caractères grecs conservés dans
   les 82 tranches GCS, avec ancres uniques et contrôle local ;
5. accepter un remplacement seulement si ses deux bornes, sa citation et la
   continuité avec les voisins sont attestées ;
6. sinon, créer des nœuds neufs par chapitre IDT, reliés par `part_of` au nœud
   `work_methodius_de_libero_arbitrio`, puis relier les anciens nœuds d’apparat
   par métadonnées, sans leur attribuer de chapitre par conjecture.

Lors d’un vrai remplacement, la description GCS devra être copiée dans
`metadata.apparatus_gcs_content`, puis la description recevra uniquement le
grec décodé de `TLG2959.TXT`, `language: grc`, `passage_role: original`,
`content_kind: primary_text`, les bornes TLG demi-ouvertes et la citation IDT.
`needs_text_ingestion` ne sera supprimé qu’à ce moment-là.

## Huit contrôles avant/après

Le présent delta ne modifie aucun contenu. Ces huit exemples montrent donc le
seul avant/après autorisé en l’absence de TLG2959 :

| Nœud | Avant | Après proposé | Ancre TLG |
|---|---|---|---|
| `passage_meth_dla_1` | apparat GCS dans `description`; ingestion requise | description inchangée; `needs_locus_mapping: true` | impossible : TXT/IDT absents |
| `passage_meth_dla_10` | idem | idem | impossible : TXT/IDT absents |
| `passage_meth_dla_20` | idem | idem | impossible : TXT/IDT absents |
| `passage_meth_dla_41` | idem | idem | impossible : TXT/IDT absents |
| `passage_meth_dla_60` | idem | idem | impossible : TXT/IDT absents |
| `passage_meth_dla_80` | idem | idem | impossible : TXT/IDT absents |
| `passage_meth_dla_100` | idem | idem | impossible : TXT/IDT absents |
| `passage_meth_dla_107` | idem | idem | impossible : TXT/IDT absents |

## Liste non mappable

Les 82 nœuds `apparatus_gcs` sont tous non mappables dans l’état actuel, pour
la même raison contrôlée : absence de `TLG2959.TXT`, de `TLG2959.IDT` et de
l’entrée d’auteur dans `AUTHTAB.DIR`. Liste exacte, sous forme compacte :

`passage_meth_dla_` +
`1, 2, 3, 6–12, 14, 15, 17, 19–24, 26–45, 49–52, 55, 57–62, 65–69, 73–78, 80, 81, 83–89, 91, 94, 95, 98, 100–107`.

Cette liste de 82 identifiants est aussi portée explicitement par
`APPARATUS_NODE_IDS` dans le module de données et validée contre le graphe au
moment du dry-run. Aucune supposition de locus n’est faite.

## Vérifications

### Inventaire de source

```text
authtab_exists: true
authtab_has_tlg2959: false
authtab_sha256: 8457a0cbe7943d148157a4ec8fb001c5412cc6ee5655e1c6bac14a818ed5e731
idt_exists: false
idt_file_count: 1823
source_available: false
source_fully_indexed: false
txt_exists: false
txt_file_count: 1823
blocked records: 82
Greek replacement records: 0
```

Le parseur préparatoire a en outre été contrôlé sur `TLG2042.IDT` : il extrait
81 œuvres, dont `002 = De principiis` et `019 = Philocalia…`. Cela valide la
lecture des en-têtes IDT, mais ne remplace évidemment pas l’IDT manquant de
Méthode.

### Dry-run sur le graphe courant

Commande :
`python3 scripts/apply_2026_08_17_methodius_reingest.py`

```text
mode: dry-run
source: BLOCKED
records: 82 metadata-only locus blockers
Greek replacement records: 0
nodes done: 82
descriptions changed: 0
corpus changes: 0
skipped/reasons:
  none: 0
invariants: OK (unique ids=19796; dangling=0; split endpoints=0; duplicate triples=0; blocked=82; changed descriptions=0; rewritten=0; under 90% Greek=0; question marks=0; missing apparatus copies=0)
write: disabled (--dry-run default)
```

Les trois invariants de remplacement sont volontairement vacants : zéro
description a été réécrite, donc zéro description sous 90 % de grec, zéro `?`
et zéro copie d’apparat manquante. Ils ne constituent pas une validation du
texte grec, lequel n’a pas été produit.

### Double `--write` hors dépôt

Une copie de `nodes.jsonl` et `edges.jsonl` a été placée sous
`/tmp/methodius-reingest.fin35w`.

Premier passage :

```text
mode: write
source: BLOCKED
records: 82 metadata-only locus blockers
Greek replacement records: 0
nodes done: 82
descriptions changed: 0
corpus changes: 0
invariants: OK (... blocked=82; changed descriptions=0; rewritten=0; under 90% Greek=0; question marks=0; missing apparatus copies=0)
wrote: /private/tmp/methodius-reingest.fin35w/nodes.jsonl
backups: .../nodes.jsonl.bak-methodius, .../edges.jsonl.bak-methodius
```

Second passage :

```text
nodes done: 0
skipped/reasons:
  already applied: 82
invariants: OK (... blocked=82; changed descriptions=0; rewritten=0; under 90% Greek=0; question marks=0; missing apparatus copies=0)
write: no-op (0 changes)
sandbox_blocked_stamp_count=82
```

Le SHA-256 de `nodes.jsonl.bak-methodius` est identique à celui du
`data/kg/nodes.jsonl` source :
`2a2c699b83ffa106ee571649adb018cb326bcd2e9ef43c5910be859f4269069c`.
La sauvegarde des arêtes est également identique à sa source. Aucun fichier de
`data/corpus/` n’a été copié ni écrit.

### Trois ré-attestations demandées

Les trois commandes ont bien été exécutées avec `--authors 2959`; elles ne
peuvent pas « hit TLG2959 » puisque le fichier d’auteur n’existe pas. Les trois
échecs sont conservés comme preuve négative et ne sont pas transformés en faux
succès.

```text
search "Ὁ μὲν Ἰθακήσιος γέρων" --authors 2959
# needle(beta-base): 'o men iqakhsios gerwn'
# total hits: 0
exit=1

search "πόθεν τὰ κακὰ καὶ τίς ὁ τούτων ποιητής" --authors 2959
# needle(beta-base): 'poqen ta kaka kai tis o toutwn poihths'
# total hits: 0
exit=1

search "Φημὶ τοιγαροῦν πολλὰς ὑποθέσεις" --authors 2959
# needle(beta-base): 'fhmi toigaroun pollas upoqeseis'
# total hits: 0
exit=1
```

### Fichiers ajoutés par ce lot

```text
data/audit/2026-08-17_methodius_reingest_plan.md
scripts/apply_2026_08_17_methodius_reingest.py
scripts/data_2026_08_17_methodius_reingest.py
```

## Portée des livrables

- `scripts/data_2026_08_17_methodius_reingest.py` : inventaire de source,
  décodeur IDT préparatoire et 82 records conservatoires.
- `scripts/apply_2026_08_17_methodius_reingest.py` : dry-run par défaut,
  `--write`, préconditions, stamp idempotent, sauvegardes `.bak-methodius` et
  invariants, sans écriture de `data/corpus/`.
- ce rapport.

Le script d’application refuse le delta conservatoire dès que les deux fichiers
source `TXT` et `IDT` deviennent disponibles, même si la table `AUTHTAB` reste
incomplète : dans ce cas, il faut reconstruire le vrai delta grec plutôt que
conserver un diagnostic devenu périmé.
