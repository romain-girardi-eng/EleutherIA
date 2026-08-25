# Audit P0 — concaténations de limites chez Sextus Empiricus

Date de l'audit : 2026-08-24

Mode : recherche en lecture seule ; aucune mutation du KG, du corpus, des citations, du manifeste ou des registres

Base Git observée : `c8bd221e098cbd8eb6cfef87ceeda82f1d5aeff5` avec arbre de travail concurrent non propre

Autorité principale : OpenGreekAndLatin/First1KGreek, commit immuable
`7881c563436f52fb3550e6daa6df94be1b83b0e3`

## Verdict exécutif

Le signalement est **confirmé** et doit être traité comme un P0 factuel.

`passage_sext_420` / `15a4749c-9555-45e7-b11f-829a1d5029f3` n'est pas un passage homogène :

1. il commence au milieu d'*Adversus Mathematicos* XI §254 ;
2. il poursuit jusqu'à la conclusion de XI §257 ;
3. après le titre `ΠΡΟΣ ΜΑΘΗΜΑΤΙΚΟΥΣ`, il reprend *Adversus Mathematicos* I
   §§1–3 et le début de I §4.

Son `part_of` pointe en outre vers *Pyrrhoniae Hypotyposes*, alors que **tous** ses caractères
appartiennent à *Adversus Mathematicos*. Le `work_canonical_id` du passage de corpus est lui aussi
celui de PH. Le CTS de départ (`tlg0544.tlg002:11.254`) décrit correctement le premier fragment,
mais ne peut décrire le fragment de livre I contenu dans le même objet.

Un second P0 plus grave encore est confirmé : `passage_sext_137` concatène la fin de
*Pyrrhoniae Hypotyposes* III §§279–281 avec le début d'*Adversus Mathematicos* VII §§1–3.
Il franchit donc deux **œuvres CTS distinctes**, `tlg0544.tlg001` puis `tlg0544.tlg002`.

Le balayage des 534 anciens chunks `passage_sext_*` a trouvé :

- **12 objets qui franchissent une limite de livre ou d'œuvre** ;
- **1 objet supplémentaire** qui franchit un titre interne au livre I ;
- **6 CTS invalides** utilisant le pseudo-livre éditorial `Pr.` alors que le schéma CTS OGL place
  ces paragraphes dans le livre `1` ;
- un manifeste qui confond le compte de l'ancien snapshot mixte avec PH et le compte d'une
  ingestion exacte limitée à AM IX–X.

Aucune correction de texte ne doit être faite en scindant simplement les chaînes historiques :
l'audit local du 17 août a montré que les 24 chunks Sextus échantillonnés sont des
« sous-séquences trouées » de l'autorité, avec des omissions internes. La voie sûre est une
réingestion depuis le TEI OGL épinglé, à granularité de section CTS.

## 1. Autorités et identités CTS

Les catalogues OGL et le catalogue Scaife distinguent sans ambiguïté les deux œuvres :

| Œuvre | Work URN | Edition grecque | Description OGL |
|---|---|---|---|
| *Pyrrhoniae Hypotyposes* | `urn:cts:greekLit:tlg0544.tlg001` | `urn:cts:greekLit:tlg0544.tlg001.1st1K-grc1` | Mutschmann, *Sexti Empiricii Opera*, vol. 1, Leipzig, 1912 |
| *Adversus Mathematicos* | `urn:cts:greekLit:tlg0544.tlg002` | `urn:cts:greekLit:tlg0544.tlg002.1st1K-grc1` | Mutschmann–Mau, *Sexti Empiricii Opera*, vols 2–3, 1912–1954 |

Sources primaires/catalogues :

- [catalogue CTS OGL de PH](https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/7881c563436f52fb3550e6daa6df94be1b83b0e3/data/tlg0544/tlg001/__cts__.xml) ;
- [TEI grec OGL de PH](https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/7881c563436f52fb3550e6daa6df94be1b83b0e3/data/tlg0544/tlg001/tlg0544.tlg001.1st1K-grc1.xml) ;
- [catalogue CTS OGL d'AM](https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/7881c563436f52fb3550e6daa6df94be1b83b0e3/data/tlg0544/tlg002/__cts__.xml) ;
- [TEI grec OGL d'AM](https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/7881c563436f52fb3550e6daa6df94be1b83b0e3/data/tlg0544/tlg002/tlg0544.tlg002.1st1K-grc1.xml) ;
- [catalogue d'auteur Scaife/Perseus](https://atlas.perseus.tufts.edu/library/urn:cts:greekLit:tlg0544/).

Empreintes des quatre fichiers effectivement relus :

| Fichier | SHA-256 |
|---|---|
| PH `__cts__.xml` | `f13598c93c843c9de4e71639c480c6d8f11bcecd2aa601a1818e60c179db79b6` |
| PH TEI grec | `6aa8ff81867ed4fa78b8681ff38cb3305a47a76cd1f61209da9f66ddb88a9ddc` |
| AM `__cts__.xml` | `e8532aec4b64b6f2cf8b09dfc3cafde5662b93f9bdb6930884642faff7ce0659` |
| AM TEI grec | `342c8623d25ef987af187ebe5053dbd8cd83dbd48e18711e8ef5c9dc22cf9278` |

Le TEI AM contient exactement onze `div[@subtype="book"]`, numérotés `1` à `11`. Leurs
titres sont, dans l'ordre : `ΠΡΟΣ ΜΑΘΗΜΑΤΙΚΟΥΣ`, `ΠΡΟΣ ΡΗΤΟΡΑΣ`, `ΠΡΟΣ ΓΕΩΜΕΤΡΑΣ`,
`ΠΡΟΣ ΑΡΙΘΜΗΤΙΚΟΥΣ`, `ΠΡΟΣ ΑΣΤΡΟΛΟΓΟΥΣ`, `ΠΡΟΣ ΜΟΥΣΙΚΟΥΣ`, deux livres `ΠΡΟΣ ΛΟΓΙΚΟΥΣ`,
deux livres `ΠΡΟΣ ΦΥΣΙΚΟΥΣ`, puis `ΠΡΟΣ ΗΘΙΚΟΥΣ`.

Un scan d'édition imprimée n'est pas nécessaire pour trancher cette identité ou ces limites :
le catalogue CTS, la structure TEI `book/section` et le texte grec concordent. Un scan resterait
utile seulement pour arbitrer une leçon critique, ce qui n'est pas l'objet de cette mutation
structurelle.

## 2. Preuve textuelle précise pour `passage_sext_420`

### 2.1 Avant la rupture

Le préfixe du passage correspond à la fin d'AM XI §§254–257. OGL XI §257 conclut le livre et
l'ensemble de cette séquence par :

> τὴν σύμπασαν τῆς σκεπτικῆς ἀγωγῆς διέξοδον ἀπαρτίζομεν

Le corpus local porte la même clôture, puis immédiatement le titre `ΠΡΟΣ ΜΑΘΗΜΑΤΙΚΟΥΣ`.

### 2.2 Après la rupture

Le TEI OGL place ce titre en tête du **livre 1**. Sa section I §1 commence par :

> Τὴν πρὸς τοὺς ἀπὸ τῶν μαθημάτων ἀντίρρησιν

Le suffixe local commence exactement par le même titre puis cette phrase. Il poursuit I §§1–3
et s'arrête au cours de I §4 ; `passage_sext_421` reprend au milieu de I §4. Ce n'est donc ni un
titre de collection ni une note d'apparat : c'est une limite de livre réelle incorporée dans un
chunk d'environ 2 000 caractères.

### 2.3 Empreinte locale de la rupture

Dans le `text_content` actuel, le titre commence à l'offset Unicode 834 :

```text
passage_id = 15a4749c-9555-45e7-b11f-829a1d5029f3
full_len = 1907
full_sha256 = de1350d85d406ff0e9a7d05bf1b6d71feccdda62c3b83d14c2c1548e5965b76e
prefix = text[:834].rstrip()
prefix_len = 833
prefix_sha256 = 50c15093d8094787b9d8d91e637bbe4baabc9e1a981550c2a60c053c346086be
suffix = text[834:].lstrip()
suffix_len = 1073
suffix_sha256 = 656d1e841d5fa057cbc3d6ea949980f21752aed6b2f3237d31b29d626b23a416
```

Ces offsets et hashes portent sur le passage de corpus normalisé actuellement stocké, pas sur la
`description` du nœud KG. Celle-ci porte la même concaténation mais conserve davantage de bruit OCR
(`\n`, accents notés par antislash, césures) et n'est pas byte-identique au corpus.

## 3. Localisation complète des objets directement liés

Les numéros de ligne sont des repères de l'arbre de travail observé ; les identifiants sont les
clés stables à utiliser pour toute migration.

Les deux nœuds d'œuvre parents sont `work_sextus_adversus_mathematicos`
(`data/kg/nodes.jsonl:19462`, CTS `tlg0544.tlg002`) et
`work_sextus_outlines_pyrrhonism_f9a7c8e4` (`data/kg/nodes.jsonl:19463`, CTS
`tlg0544.tlg001`). Leur identité est correcte ; le défaut réside dans les unités mixtes et, pour
420, dans l'affectation au mauvais parent.

### `passage_sext_420`

| Couche | Localisation et constat |
|---|---|
| KG node | `data/kg/nodes.jsonl:13928`, `node_id=passage_sext_420`; label mixte et CTS de départ AM XI.254 |
| Corpus | `data/corpus/passages.jsonl:8180`, UUID `15a4749c-9555-45e7-b11f-829a1d5029f3`; `work_canonical_id=...tlg001...` erroné |
| Snapshot citation | `data/corpus/citations.jsonl:1746`; unique citation directe, type `snapshot_passage_node` |
| `authored_by` | `data/kg/edges.jsonl:29380`, edge `4deb59c4-1b91-45a8-8401-a5bb7884311f` |
| `part_of` | `data/kg/edges.jsonl:29381`, edge `97366330-f2e6-412c-9b04-e55ef5de0637`, cible PH **erronée** |
| Voisins | `passage_sext_419` finit au milieu de XI.254 ; `passage_sext_421` reprend au milieu de I.4 |

Le placement physique du passage de corpus à la ligne 8180, entre les lignes PH 137 et AM 138,
résulte de son `work_canonical_id` PH erroné ; son `sequence_number` reste 420.

### `passage_sext_137`

| Couche | Localisation et constat |
|---|---|
| KG node | `data/kg/nodes.jsonl:13613`, `node_id=passage_sext_137` |
| Corpus | `data/corpus/passages.jsonl:8179`, UUID `8ba2c92f-8830-4864-a4d7-22099ba2e79f` |
| Snapshot citation | `data/corpus/citations.jsonl:10515`; unique citation directe |
| `authored_by` | `data/kg/edges.jsonl:28748`, edge `92407027-3faa-4679-bfc3-76e1545ab14b` |
| `part_of` | `data/kg/edges.jsonl:28749`, edge `881095e3-30dc-4dc3-a9e7-36b3fafd8e2f`, cible PH correcte pour le préfixe seulement |
| Voisins | `passage_sext_136` contient le début de PH III.279 ; `passage_sext_138` reprend AM VII.4 |

Son titre interne `ΠΡΟΣ ΛΟΓΙΚΟΥΣ` se trouve à l'offset 1205. L'empreinte complète du
corpus est `fb0b865577af7a81255357474fe5692ea788e958522b9ef91b1133723dbec96b` ; les fragments
avant/après la rupture ont respectivement les SHA-256
`bea0f030a32c0ca60375282f9d7ada01346cf6651d887a839c12673fdf85981b` et
`532e488cdaaf3b38d4f85faa3784347b2ed4f03028a2e843853ad909f95f12a6`.

Aucun argument, claim ou evidence edge supplémentaire ne cite directement ces deux nœuds dans le
snapshot ; chacun a une citation `snapshot_passage_node`, un `authored_by` et un `part_of`.

## 4. Balayage systématique des concaténations voisines

### Méthode

1. Sélection des 534 passages de l'ancien snapshot par `sequence_number=1..534` et famille Sextus.
2. Recherche des titres de livres grecs présents dans le TEI OGL.
3. Contrôle des `canonical_ref` qui changent de livre de part et d'autre du tiret.
4. Lecture du passage précédent et suivant pour écarter un simple libellé de rubrique.
5. Contrôle de la hiérarchie `book/section` dans les deux TEI épinglés.

Le scan positif par titres aurait manqué PH I→II, car la structure de PH n'emploie pas les mêmes
titres `ΠΡΟΣ ...`; le contrôle indépendant des loci a trouvé `passage_sext_41`. PH II→III tombe,
lui, proprement entre `passage_sext_86` et `passage_sext_87` et n'est pas concaténé.

### Résultats

| Node | UUID de corpus | Ref actuelle | Limite réelle contenue | Corpus / node / citation / `part_of` lines | Classe |
|---|---|---|---|---|---|
| `passage_sext_41` | `756fcdf3-76ca-46f0-8598-404b99a10835` | `PH 1.241-2.4` | PH I.241 → PH II.toc,1–4 | 8083 / 13916 / 8842 / 29357 | livre→livre |
| `passage_sext_137` | `8ba2c92f-8830-4864-a4d7-22099ba2e79f` | `PH 3.279-281` | PH III.279–281 → AM VII.1–3 | 8179 / 13613 / 10515 / 28749 | **œuvre→œuvre** |
| `passage_sext_205` | `e05e9f3b-4f79-4039-a0a1-785fb314cfbc` | `M. 7.440-446` | AM VII → AM VIII | 8248 / 13689 / 16897 / 28903 | livre→livre, ref incomplète |
| `passage_sext_276` | `e43a781c-a23d-44ff-a486-b7138856c89f` | `M. 8.480-9.3` | AM VIII → AM IX | 8319 / 13767 / 17211 / 29059 | livre→livre |
| `passage_sext_336` | `44b70018-ac64-4f82-a8c8-92c53389f871` | `M. 9.438-10.3` | AM IX → AM X | 8379 / 13834 / 5183 / 29193 | livre→livre |
| `passage_sext_385` | `98aee426-b925-4105-ae3f-44ad05a94ad3` | `M. 10.351-11.5` | AM X → AM XI | 8428 / 13888 / 11532 / 29301 | livre→livre |
| `passage_sext_420` | `15a4749c-9555-45e7-b11f-829a1d5029f3` | `M. 11.254-Pr.4` | AM XI.254–257 → AM I.1–4 | 8180 / 13928 / 1746 / 29381 | livre XI→I + parent faux |
| `passage_sext_472` | `ab979092-c896-4797-bb8d-832a3e92a045` | `M. 1.316-2.2` | AM I → AM II | 8514 / 13985 / 12979 / 29495 | livre→livre |
| `passage_sext_489` | `7e3aebbf-1def-4151-a313-a77ee512d08b` | `M. 2.111-3.5` | AM II → AM III | 8531 / 14003 / 9492 / 29531 | livre→livre |
| `passage_sext_506` | `ff2129c9-9681-4eeb-98d4-0859e0a78faa` | `M. 3.115-4.4` | AM III → AM IV | 8548 / 14023 / 19392 / 29571 | livre→livre |
| `passage_sext_511` | `8b6f9802-daf2-4ed0-8824-5dd296964148` | `M. 4.34-5.6` | AM IV → AM V | 8553 / 14029 / 10489 / 29583 | livre→livre |
| `passage_sext_525` | `fa1f8fe6-42c5-44de-a70f-c4d8664da768` | `M. 5.105-6.6` | AM V → AM VI | 8567 / 14044 / 18985 / 29613 | livre→livre |
| `passage_sext_426` | `f42291b0-ad00-4378-94de-4ddd093d1f12` | `M. Pr.37-1.42` | AM I.37–40 → titre interne → I.41–42 | 8468 / 13934 / 18496 / 29393 | pas un nouveau livre ; CTS faux |

Les douze premières lignes sont des concaténations de livres ou d'œuvres. La treizième est
structurellement différente : `ΠΡΟΣ ΓΡΑΜΜΑΤΙΚΟΥΣ` est un titre interne au livre I entre §40
et §41, et non un nouveau livre CTS.

### Empreintes des autres ruptures

Format : `node | offset | SHA(full) | SHA(prefix.rstrip) | SHA(suffix.lstrip)`.

```text
passage_sext_41  |  167 | 29b58876b03f35535d3664e156cc4ceedc52af9c4af3639b58ea474be0b5be5f | f4903041deaab77472bb5c8cd4c0678c9c8aad201a5b8e8995d68f1dc8677412 | 37977f5875a42da9f7b612e5b3a8e8f0f8a4beda0a3f7b5396efb22d53fb9517
passage_sext_137 | 1205 | fb0b865577af7a81255357474fe5692ea788e958522b9ef91b1133723dbec96b | bea0f030a32c0ca60375282f9d7ada01346cf6651d887a839c12673fdf85981b | 532e488cdaaf3b38d4f85faa3784347b2ed4f03028a2e843853ad909f95f12a6
passage_sext_205 | 1813 | 5e82431e61a9007ab5e0dd2072a00c124acc0c7496d396aba65828922169d556 | be90ed497cd3cfa308d79c407a417fa663755519f10fe0e49b45cb3d29e977ae | 79057aedec1024656c6b7afc687a7f84d52c9f4a98d3a3176ee5b94f321af78a
passage_sext_276 |  828 | efc4974bbe5369746c905a107b1d9247c453fdc46b2f6fafd1aaaa0fd41f0103 | c823a8eab1fb355c6903417fe380de3b29d53227285a1ca1b4aac50f5a71ccb1 | 3a75f27395d9f73345a87087f38234a9d0aad6b73871f1a25698c353920f96f0
passage_sext_336 |  430 | caa0d18d462004c4cc74865d382629533757baaacbe84937a9ec941322edb0b0 | 0095c71dabe22dc9a68f362606df7ee88dabdc2c5aa7da250fadfcebd9aacc5c | 406f5afaf89e4fb8cad40556fe580d6b2fdc528cf77920f7595e0d0e46ef72bb
passage_sext_385 |  182 | 4b31993b48b272f486d91f734f9496193cac9568e707cf80c74032610665afb5 | d45d078ad23e1dd9b3c6edd27a51d77ff8dcecc9f4bfdf688134b3790e563d8e | 6e2381ff2bbbccc8125eaf82c89a692febb3c7b9ea1e56548e9781e248203765
passage_sext_420 |  834 | de1350d85d406ff0e9a7d05bf1b6d71feccdda62c3b83d14c2c1548e5965b76e | 50c15093d8094787b9d8d91e637bbe4baabc9e1a981550c2a60c053c346086be | 656d1e841d5fa057cbc3d6ea949980f21752aed6b2f3237d31b29d626b23a416
passage_sext_426 | 1410 | 3480b8aed83e3886a7e74d490babbd5a835b5a95775f8520aa06073710c51faf | 281dd03835aa74596d283047d226c9b453f82484e51540f695cacd62d8c7112d | 4dcfe438c2a63983a730d718384f71ca979afe08e65235c68bcd0bb751295f81
passage_sext_472 | 1301 | 86caf6cb416a2f740cb4bc9d4b5daed24a4ceec9cffb425233c0faaacff7ee33 | 44260ae18f5698d31f1ecd699c8a3384f845fc7a7ce7b9c18207aa14117b1ef7 | cde730933deee51402577f7d8d902eecf2bbf064604a6b878700ff1fa921fd46
passage_sext_489 |  622 | 9bf6dde79bc569869ad5684dcd8ce87406868a1ef7b6dba45a290f6b1b2a1e69 | a65b91d61486baac3b3d5069b9b4a2a698569a63f9908de877ee35f70b3129d5 | 1a956af8b015301a4bbf900ba58505ff6693543345eb36225faaf3b1369bf108
passage_sext_506 |  575 | cdc325c5f4f31cc04beb066e272d765ba9d3a9f4282baf6ab0864f4b6a7b5c85 | dd699f6a72fb9688150fad8627c6f027b70f233ffae7e3e69acbcba71fa29cdc | 6c2a16c4a79badd220a65622aa2337854b15d50424fec0414ea5da245c7cf68a
passage_sext_511 |  199 | 1d9aa001b7feb55f610875f7d22714f1c170452a2431b5fc18398ff104179642 | de7172815c46fb7836e566a308a16a3454a9f41944f0ef15b032c5f0f0f2de46 | 1f3c0a5b4ab1523e4b1ef18c7151bb87cfb0464a52a283b047933726b039f35d
passage_sext_525 |  454 | eefe3d79ea755e803de2a3eda21f0119ca64f33ca819941413cac2eec0c394de | f1f018bcb812230bf69f0b6c46340bff3af640aa2cc193f2443127ab75effc68 | 3967b213febffb223119318075e8d35a6d542e436a8f9baa7444210c352417e8
```

Pour `passage_sext_41`, l'offset vise le titre de PH II `ΠΥΡΡΩΝΕΙΩΝ ΥΠΟΤΥΠΩΣΕΩΝ`.
Pour les autres, il vise le titre grec de la seconde unité. Les longueurs/hashes sont des
before-images de contrôle, non une invitation à conserver les fragments OCR comme texte exact.

## 5. Le pseudo-livre `Pr.` n'existe pas dans le CTS OGL

OGL encode le proœme général d'AM dans le livre `1`, sections `1` à `40`. La rubrique
`ΠΡΟΣ ΓΡΑΜΜΑΤΙΚΟΥΣ` commence à I §41, toujours dans le même `div` de livre 1. Les six objets suivants
emploient donc un passage component non conforme à l'édition déclarée :

| Node | UUID | Corpus / node / citation / `part_of` lines | CTS actuel | Mapping CTS de livre sûr |
|---|---|---|---|---|
| `passage_sext_421` | `ba493f69-6a3b-490e-9648-85c970030e23` | 8463 / 13929 / 14104 / 29383 | `...tlg002:Pr.4` | livre `1`, autour de I.4–9 |
| `passage_sext_422` | `8175072b-5bb6-462f-8bc1-f0bfa446a6ca` | 8464 / 13930 / 9755 / 29385 | `...tlg002:Pr.9` | livre `1`, autour de I.9–16 |
| `passage_sext_423` | `03ca2fc9-6698-4e72-89fb-2663e3e78654` | 8465 / 13931 / 322 / 29387 | `...tlg002:Pr.17` | livre `1`, autour de I.17–25 |
| `passage_sext_424` | `3b7c64e5-60e5-4a55-95dd-b404117c1b09` | 8466 / 13932 / 4556 / 29389 | `...tlg002:Pr.25` | livre `1`, autour de I.25–30 |
| `passage_sext_425` | `d94aa017-6d2e-40bd-acf4-4ab978cb9061` | 8467 / 13933 / 16359 / 29391 | `...tlg002:Pr.30` | livre `1`, autour de I.30–36 |
| `passage_sext_426` | `f42291b0-ad00-4378-94de-4ddd093d1f12` | 8468 / 13934 / 18496 / 29393 | `...tlg002:Pr.37` | livre `1`, I.37–42 |

Les mentions « autour de » sont intentionnelles : les chunks commencent et finissent souvent au milieu
d'une section. Le script de migration ne doit pas convertir aveuglément `Pr.X` en `1.X` tout en
conservant le texte historique ; il doit réingérer les sections entières.

## 6. Manifeste et population réelle

Les entrées actuelles sont :

- `data/corpus/manifest.jsonl:38` : PH, `passages=534`, source générique
  `scaife:urn:cts:greekLit:tlg0544` ;
- `data/corpus/manifest.jsonl:39` : AM, titre limité à IX–X, `passages=791`, source vide.

Le décompte réel par lecture JSONL est :

| Cohorte | Compte | Observation |
|---|---:|---|
| anciens chunks `sequence_number=1..534` | 534 | 138 classés PH et 396 AM ; la ligne PH parasite est `passage_sext_420` |
| passages sous canonical ID PH | 138 | 137 vrais chunks PH + le chunk AM 420 mal classé |
| passages sous canonical ID AM | 1187 | 396 chunks historiques + 791 sections exactes OGL |
| sections exactes OGL AM IX | 440 | CTS d'édition `...1st1K-grc1:9.X` |
| sections exactes OGL AM X | 351 | CTS d'édition `...1st1K-grc1:10.X` |

Ainsi, `534` décrit l'ancien snapshot Sextus **mixte** PH + AM, et non PH. `791` décrit bien la
cohorte exacte IX–X, mais l'identifiant canonique de travail est aussi partagé avec 396 chunks AM
historiques couvrant VII–XI puis I–VI. Le manifeste ne documente ni cette coexistence ni la
provenance des 396 chunks.

Le rapport antérieur `data/audit/2026-08-17_span_recollation.md` fournit une preuve indépendante
contre une correction superficielle : 24/24 chunks Sextus relus y contiennent des omissions
internes par rapport à First1KGreek, et huit bornes de chunks Sextus coupent un mot. Les
concaténations documentées ici sont un défaut supplémentaire, pas une explication de ces omissions.

## 7. Mapping sûr et migration proposée — non exécutée

### Principe de conservation

Ne pas modifier un CTS seulement, ne pas couper la chaîne OCR et ne jamais qualifier le résultat
d'`exact`. Conserver chaque ancien objet comme before-image quarantinée, puis reconstruire depuis
les TEI épinglés avec le parseur canonique d'ingestion.

### Cas `passage_sext_420`

1. Quarantainer le nœud, le passage, sa citation snapshot et ses deux edges.
2. Retirer l'ancien objet des surfaces factuelles et de recherche exactes.
3. Ingest PH/AM à la section CTS, ou au minimum créer des spans bornés dans un seul livre :
   - `urn:cts:greekLit:tlg0544.tlg002.1st1K-grc1:11.254-11.257`, parent AM ;
   - `urn:cts:greekLit:tlg0544.tlg002.1st1K-grc1:1.1-1.3`, parent AM ;
   - I.4 doit être ingérée une seule fois comme section entière, car les chunks 420 et 421 la
     partagent actuellement.
4. Si la compatibilité impose de conserver `passage_sext_420`, le réutiliser seulement comme alias
   déprécié vers les nouvelles unités, jamais comme passage cit-able.

### Cas `passage_sext_137`

1. Quarantainer l'objet mixte.
2. Reconstruire PH III.279–281 sous
   `urn:cts:greekLit:tlg0544.tlg001.1st1K-grc1:3.279-3.281`, parent PH.
3. Reconstruire AM VII.1–3 sous
   `urn:cts:greekLit:tlg0544.tlg002.1st1K-grc1:7.1-7.3`, parent AM.
4. Revoir les voisins 136 et 138 pour supprimer les partages de sections aux bornes.

### Reste de la famille

- Reconstruire chaque livre PH/AM en sections CTS atomiques ; une ligne de corpus ne doit jamais
  franchir un `div[@subtype="book"]`.
- Remplacer tous les components `Pr.*` par des sections exactes du livre 1 issues du TEI, et non par
  un search/replace de métadonnées.
- Rendre les `work_canonical_id` des nœuds spécifiques à `tlg001` ou `tlg002` ; supprimer le titre
  agrégé « Against the Professors and Outlines of Pyrrhonism » des nouvelles unités.
- Chaque nouvelle unité doit avoir exactement un `authored_by`, un `part_of` vers la bonne œuvre et
  une citation snapshot bijective.
- Le manifeste doit séparer explicitement les manifestations/cohortes : PH complet exact, AM
  complet exact, et éventuel legacy quarantiné. Son compte doit être recalculé, pas copié.

### Script de migration attendu

Un futur script doit être `--dry-run` par défaut, idempotent et fail-closed. Il doit :

1. vérifier le commit OGL et les quatre SHA ci-dessus ;
2. vérifier les SHA before-image des cibles ;
3. écrire une quarantaine append-only comportant nœud, corpus, citation et tous les edges incidents ;
4. parser le TEI en excluant explicitement apparat, notes, numéros de page et titres du texte
   courant, tout en conservant le titre comme métadonnée structurelle ;
5. produire les passages exacts et leurs hashes de source ;
6. reconstruire liens et comptes de manifeste en une seule transaction logique ;
7. prouver que le second run ne change aucun octet ;
8. prouver l'invariance de toutes les lignes non ciblées.

## 8. Quarantaine proposée — non créée

P0 immédiat : exclure des usages factuels `passage_sext_137` et `passage_sext_420`.

Quarantaine structurelle suivante : les dix autres concaténations de livres
`41, 205, 276, 336, 385, 472, 489, 506, 511, 525`.

Quarantaine CTS : `passage_sext_421` à `passage_sext_426` pour toute opération qui suppose un URN
résolvable dans l'édition déclarée. `passage_sext_426` doit aussi être reconstruite autour de la
rubrique interne I.41.

La future quarantaine devrait être un JSONL dédié, par exemple
`data/audit/2026-08-24_sextus_boundary_concat_quarantine.jsonl`, mais **ce fichier n'a pas été
créé par cet audit read-only**.

## 9. Tests et gates requis

### Autorité et texte

- le catalogue PH résout `tlg001` et le catalogue AM résout `tlg002` ;
- les quatre fichiers OGL correspondent aux SHA épinglés ;
- le parseur trouve 3 livres PH et 11 livres AM ;
- chaque texte exact correspond au texte de sa ou ses sections TEI selon une politique
  d'extraction documentée ;
- aucun texte exact ne contient une note ou une entrée d'apparat.

### Structure KG/corpus

- aucun passage cit-able ne traverse deux work URNs ;
- aucun passage cit-able ne traverse deux `book` TEI ;
- aucun CTS Sextus ne contient `:Pr.` ;
- chaque CTS de passage contient l'edition URN `.1st1K-grc1` ;
- le work déduit du CTS est identique au `work_canonical_id` et à la cible `part_of` ;
- `passage_sext_420` ne peut jamais être retrouvé comme preuve PH ;
- une citation snapshot correspond à un seul passage et un seul nœud ;
- aucun ancien UUID quarantiné ne reste actif dans l'index exact.

### Exhaustivité et déploiement

- les comptes de manifeste sont recomptés par cohorte et par work URN ;
- la cohorte exacte IX–X reste 440 + 351 = 791 jusqu'à son remplacement planifié ;
- la réingestion complète ne laisse ni trou ni doublon de section ;
- le script est idempotent et son dry-run liste exactement les objets ciblés ;
- la quarantaine contient les before-images et hashes attendus ;
- les gates snapshot, work-child, corpus/citation bijection et non-target invariance passent avant
  publication.

## 10. Limites de cet audit

- Aucun fichier KG/corpus/citation/manifeste/registre n'a été modifié.
- Aucun texte n'a été déclaré exact à partir du seul legacy OCR.
- Les positions de lignes peuvent bouger avec les travaux concurrents ; les IDs et SHA sont les
  ancrages de migration.
- Le scan des 534 chunks couvre les limites structurelles visibles dans les loci et les titres.
  L'audit de recollation antérieur reste l'autorité pour les omissions internes et les mots coupés.
- L'anomalie voisine `passage_sext_105`, libellée `PH 3.92-3` alors que le passage suivant commence
  à `PH 3.99`, ressemble à une troncature de ref (`3.92-98`) mais n'a pas été corrigée ni
  promue au même niveau de certitude sans recollation ciblée.

## Conclusion

La correction minimale sûre n'est pas de renommer `Pr.` ou de changer un seul edge. Les objets
420 et 137 démontrent que le chunker historique a produit des unités qui ne respectent ni l'œuvre
ni le livre, tandis que l'audit du 17 août démontre que leur texte est aussi incomplet. Le correctif
SOTA est donc une réingestion sectionnelle, épinglée et hashée, avec quarantaine des before-images,
reconstruction atomique des liens et gates fail-closed.
