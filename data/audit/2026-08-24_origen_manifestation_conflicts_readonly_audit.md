# Audit read-only P0 — conflits de manifestations origéniennes

Date de constat : 2026-08-24 (Europe/Paris)  
Périmètre : `De principiis / Peri Archon`, `Philocalia`, `Commentarii in Romanos`, `Exhortatio ad martyrium` et la collision `Clement / Protrepticus`.  
Statut : **audit seulement**. Aucun fichier KG, corpus, manifeste, bibliographie ou registre n'a été modifié. Ce rapport est l'unique écriture de cette tâche.

## Verdict exécutif

Le texte grec de l'`Exhortatio ad martyrium` est sain, mais son manifeste reste attribué à Clément. Les trois autres ensembles sont impropres à une publication « sans erreur » dans leur état actuel parce que les identités de l'œuvre, les langues, les témoins et les traductions sont confondus.

| Dossier | Texte actuellement récupérable | Verdict de publication | Priorité |
|---|---|---:|---:|
| `Exhortatio ad martyrium` | 51/51 chapitres grecs exactement égaux après NFC au fichier OGL/Perseus épinglé | Texte **PASS** ; manifeste et deux work nodes **FAIL** | P0-a |
| `De principiis` III.1 grec | 24 sections grecques propres, collationnées antérieurement contre TLG-E/SC 268 | Texte **PASS conditionnel** ; témoin indirect, snapshots et identités **FAIL** | P0-b |
| `De principiis` « `_eng` » | 23 traductions françaises de la **version latine de Rufin**, plus une note anglaise | Manifestation **FAIL** | P0-b |
| `Philocalia` | 51 passages de corpus, tous français malgré `_eng`/`_grc`; aucun lot grec propre pour 23/25-27 | Manifestations **FAIL** ; textes français récupérables après re-collation | P0-c |
| `Commentarii in Romanos` | Deux loci latins SC 543 désormais verbatim dans le corpus | Latin **PASS** ; manifeste/CTS/snapshots/notes anglaises **FAIL** | P0-d |

Les quatre identifiants à ne plus confondre sont établis par les métadonnées CTS du dépôt OpenGreekAndLatin épinglé au commit `7881c563436f52fb3550e6daa6df94be1b83b0e3` :

| Identifiant | Autorité | Identité sûre |
|---|---|---|
| `tlg2042.tlg007` | [OGL `__cts__.xml`](https://github.com/OpenGreekAndLatin/First1KGreek/blob/7881c563436f52fb3550e6daa6df94be1b83b0e3/data/tlg2042/tlg007/__cts__.xml) | Origène, `Exhortatio ad martyrium`, grec, Koetschau 1899 |
| `tlg2042.tlg019` | [OGL `__cts__.xml`](https://github.com/OpenGreekAndLatin/First1KGreek/blob/7881c563436f52fb3550e6daa6df94be1b83b0e3/data/tlg2042/tlg019/__cts__.xml) | `Philocalia`, édition grecque Robinson 1893 |
| `tlg2042.tlg028` | [OGL `__cts__.xml`](https://github.com/OpenGreekAndLatin/First1KGreek/blob/7881c563436f52fb3550e6daa6df94be1b83b0e3/data/tlg2042/tlg028/__cts__.xml) | `Commentariorum Series in Evangelium Matthaei (Mt 22.34–27.63)`, traduction latine ; **pas la Philocalia** |
| `tlg2042.tlg012` | [OGL `__cts__.xml`](https://github.com/OpenGreekAndLatin/First1KGreek/blob/7881c563436f52fb3550e6daa6df94be1b83b0e3/data/tlg2042/tlg012/__cts__.xml) | `Fragmentum in Lamentationes`; **pas le Commentaire sur Romains** |

`tlg2042.tlg002` est bien le numéro TLG de `De principiis` dans le disque TLG-E local, mais il n'existe pas comme édition OGL/Scaife dans le dépôt First1KGreek audité. Il peut rester un identifiant d'autorité TLG ; il ne doit pas être présenté comme une source `scaife:` résoluble sans preuve supplémentaire.

## Empreinte exacte de l'état audité

Les numéros de lignes ci-dessous décrivent ces blobs et ne doivent pas être appliqués comme coordonnées de patch sans revalidation :

```text
6146820c459b2d7c95accd9bb0b71ff2506bb8c7a13cc369cd6b46a484ff0608  data/kg/nodes.jsonl
6aec3c3021f1463a0be9eba6f1f3df06be66c6efa50b6ff383db9a738c676541  data/kg/edges.jsonl
621a159fce7523626ab676e581165df45c513a5941bd7903748a7b133be7fc17  data/corpus/passages.jsonl
d3477df6a714a3b7455a315230a4e9b723cf7ec99a5ab6972c4ffed36293fe5f  data/corpus/citations.jsonl
af18f905c77c15e7bd1f3dcb684947d321f60030b1e42be1c0686fd06eb9d884  data/corpus/manifest.jsonl
09f29e367d7c7337ead88387481d7125312baaa68c554545bd4fa856c96c5fb6  data/scholarly_sources/manifest.jsonl
```

Autorités téléchargées sans écriture dans le dépôt :

```text
cc1a2aed4c7807ae514dd155c3a3bac0afe7f4b745df51a4d167373f598229c0  tlg007/__cts__.xml
dedb6ae89519545a0ab274061c858a0549760bb3ac97223a5f744130c13fb83b  tlg007/tlg2042.tlg007.perseus-grc1.xml
169b09024d5ccd690f1d6c5d4fae1ac82a3972fcaf1ae2e38a38a7a61e25c6ed  tlg012/__cts__.xml
85d8d0ec4953163002ff198af7d46149866bc0c4aac6d64d32b08ff79d48d0ea  tlg019/__cts__.xml
449753df2a7363a4b63cd08e9dab0a06efecfc6e5abc800e9dfb4ee6d8773348  tlg019/tlg2042.tlg019.1st1K-grc1.xml
b1d0b38eaadc261a4ad0264bfa6bd3468c2c225901cc27f078699279893eeef8  tlg028/__cts__.xml
```

## Sources et éditions relues

### SC 268, `Traité des principes`, livres III-IV

PDF local : `(Sources Chrétiennes 268) Origène - Traité des principes, Livres III et IV, tome III-Cerf (1980).pdf`, SHA-256 `aa3f94057f39e545b1addba32ccf8d071735a26516589b5fd1a5bc6aa864576a`.

Contrôle visuel effectué sur la page de titre, l'introduction, la préface de Rufin et les premières doubles pages du texte. Les faits décisifs sont :

1. La page de titre décrit explicitement le volume comme « introduction, texte critique de la Philocalie et de la version de Rufin, traduction » par Henri Crouzel et Manlio Simonetti.
2. L'introduction explique que Philocalia 21 transmet `De princ.` III.1, alors que l'ensemble de l'œuvre n'est conservé que par le latin de Rufin. Le grec et le latin sont imprimés ensemble parce qu'ils ont chacun des lacunes et permettent de juger la fidélité de Rufin.
3. La préface de Rufin dit expressément qu'il omet ce qu'il juge contraire à la foi et abrège certaines répétitions. Le témoin latin ne peut donc jamais être silencieusement fusionné avec les fragments grecs.
4. La double page imprimée 16-17 montre en haut le grec de Philocalia 21 avec sa traduction française, et en bas le latin de Rufin avec une **autre** traduction française.
5. L'introduction imprimée p. 8 précise que SC 226 étudie Philocalia 21 **sans l'éditer**, parce que l'édition est donnée dans SC 268. Les scripts qui décrivent SC 226 comme l'édition principale du grec de Philocalia 21, ou SC 268 comme une simple « reconstruction de Junod », doivent être corrigés.

La [notice BnF de SC 268](https://catalogue.bnf.fr/ark:/12148/cb346339432) confirme : Crouzel-Simonetti, Paris, Cerf, 1980, SC 268, textes grec et latin et traductions françaises en regard. La [notice du Cerf](https://www.editionsducerf.fr/librairie/sc-268-traite-des-principes-iii/) confirme les contributeurs et l'ISBN `9782204015387`.

### SC 226, `Philocalie 21-27`

Source locale : RTF `SC 226 - Origène, Philocalie 21-27 (Sur le libre arbitre).rtf`, SHA-256 `ab241804fc96b73d06414ed1a2d623e5d7cc1a6dad1863cca2def13337bb38b7` ; conversion lue via `textutil -convert txt -stdout`, sans produire de fichier dans le dépôt.

Le RTF détenu commence au chapitre 23 et contient le grec et la traduction française Junod pour les chapitres 23, 25, 26 et 27. Ce n'est pas une preuve que le volume imprimé « a perdu » le chapitre 21 : SC 268 explique qu'il n'y est volontairement pas réédité. La [notice du Cerf](https://www.editionsducerf.fr/librairie/sc-226-philocalie-21-27-sur-le-libre-arbitre/) attribue introduction, annotations, traduction et texte critique à Éric Junod ; l'édition originale est de 1976, la réimpression corrigée de 2006.

Les rubriques de la source imposent les attributions suivantes :

| Philocalia | Source ancienne indiquée par la rubrique |
|---|---|
| ch. 21 | `De principiis` III.1 ; édition du grec à traiter par SC 268/Koetschau, pas par le RTF SC 226 détenu |
| ch. 23.1-11, 14-21 | `Commentaire sur la Genèse`, tome III ; 23.12-13 est explicitement tiré de `Contra Celsum` II ; 23.22 transmet un extrait pseudo-clémentin |
| ch. 25 | `Commentaire sur l'Épître aux Romains`, tome I, sur Rom 1.1 ; **pas Contra Celsum** |
| ch. 26 | `Commentaire sur le Psaume 4` ; **pas Commentaire sur Romains** |
| ch. 27.13 | explicitement `Commentaire sur le Cantique`, tome II |
| ch. 27.1-12 | la rubrique locale donne le thème de l'endurcissement de Pharaon mais pas, dans les pages relues, une œuvre-source unique : **laisser ouvert** |

Le XML OGL `tlg019` est une autorité sûre pour l'identité et la hiérarchie CTS, mais pas une base textuelle à ingérer aveuglément : il contient de nombreux résidus OCR littéraux (`U+03F2`, caractères substitués et mots corrompus). Sa hiérarchie est `book.chapter.section`, avec le corps principal sous `book=2`; les citations d'édition sont donc de la forme `...tlg019.1st1K-grc1:2.23.1`, non `...tlg019:23.1`. Il ne possède pas de pseudo-section CTS `titulus`.

### SC 543 et FOTC 104, `Commentarii in Romanos`

Sources locales relues :

- `SC543_Origenes_Commentaire_Romains_livre_7_bilingue.txt`, texte latin Hammond Bammel et français Brésard-Fédou ;
- `Scheck_2002_Origen_CommRom_FOTC104.pdf`, SHA-256 `cf7083c2c571a009c42c4c370b1a4529e37bd5b5011657ecbe5da9c45490c2de` ; texte extrait et pages imprimées 113-118 contrôlées visuellement.

La concordance sûre est :

| SC 543 | FOTC 104 | Contenu |
|---|---|---|
| VII.14.2-3, pages SC 384-386 | VII.16.4-5, pages imprimées 114-116 | personne du contradicteur ; objection selon laquelle l'homme n'a pas `libertas arbitrii` |
| VII.14.5, pages SC 392-394 | VII.16.8, pages imprimées 117-118 | Pharaon s'endurcit en refusant d'obéir à la patience divine |

`VII.16` n'est donc pas absolument « faux » : c'est la numérotation FOTC/Scheck. Dès qu'une citation annonce SC 543, elle doit toutefois employer `VII.14`. Le schéma de numérotation doit être stocké avec le locus.

La [notice BnF de SC 543](https://catalogue.bnf.fr/ark:/12148/cb42487237p) identifie le texte comme la traduction latine de Rufin, texte critique Hammond Bammel, traduction et notes Brésard-Fédou, 2011. La [notice du Cerf](https://www.editionsducerf.fr/librairie/sc-543-commentaire-sur-lepitre-aux-romains-iii/) date prudemment l'œuvre vers 243 et la traduction de Rufin de 405-406. La [notice CUAPress de FOTC 104](https://www.cuapress.org/9780813220215/commentary-on-the-epistle-to-the-romans-books-6-10/) décrit l'anglais de Scheck comme traduction de la version latine de Rufin.

## Recensement exhaustif par manifestation actuelle

Les « citations » comptées ici sont les lignes de `data/corpus/citations.jsonl`, pas les simples arêtes KG. Une citation `snapshot_passage_node` doit être un miroir exact du passage après normalisation Unicode NFC ; les autres citations relient le passage à un concept ou à un argument.

| `work_canonical_id` actuel | Corpus (lignes) | Passages | Citations | Snapshots | Langue réelle | Loci | Manifeste | Décision |
|---|---:|---:|---:|---:|---|---|---|---|
| `urn_cts_greeklit_tlg2042_tlg007_grc` | 12792-12842 | 51 | 51 | 51 | grec | `Exh. mart. 1-51` | ligne 47, faux auteur/titre | conserver les 51 UUID/textes ; corriger identité |
| `work_de_principiis_origen_230s_v2w3x4y5_eng` | 17440-17463 | 24 | 28 | 24 | 23 français + 1 anglais éditorial | III.1.1-2, 4-24 ; note hors série | ligne 67, faux Scaife/anglais | scinder ; quarantainer la note |
| `work_de_principiis_origen_230s_v2w3x4y5_grc` | 17464 + 21047-21070 | 25 | 32 | 25 | 24 grec + 1 mixte anglais/grec | III.1.1-24 + note III.1.3 | ligne 89 partiellement honnête | garder 24 Grecs comme témoin Philocalia ; quarantainer la note |
| `origen_of_alexandria_origen_de_principiis_peri_archon` | 940 | 1 | 3 | 1 | grec | III.1.1 | absent | fusion/alias, pas preuve indépendante |
| `sc268_origenes_peri_archon_grc` | 1946-1949 | 4 | 13 | 4 | grec | III.1 entier, IV.1-3 entiers | absent | garder comme conteneurs de lecture, dédupliquer à l'évaluation |
| `sc268_origenes_peri_archon_eng` | 1942-1945 | 4 | 8 | 4 | anglais IA | mêmes chapitres | absent | manifestation générée, jamais « édition publiée » |
| `work_origen_commentary_romans_grc` | 17731-17732 | 2 | 5 | 2 | latin | SC 543 VII.14.5 et VII.14.2-3 | ligne 71, titre/langue faux | renommer manifestation latine ; refaire snapshots |
| `work_origen_commentary_romans_eng` | 17729-17730 | 2 | 2 | 2 | anglais éditorial | deux résumés anciens | ligne 70 | quarantaine, ne pas publier comme texte primaire |
| `work_origen_philocalia_grc` | 17756-17785 | 30 | 88 | 30 | français | ch. 23 + quatre extraits ch. 21 | absent | scinder traduction SC 226 / traduction SC 268 ; corriger rôles |
| `work_origen_philocalia_eng` | 17735-17755 | 21 | 21 | 21 | français | 25.1-4; 26.1-8; 27.1-8,12 | ligne 73, auteur/source/langue faux | renommer manifestation française SC 226 |

### Exhortatio / collision Clément

- Les 51 textes grecs du corpus ont été comparés chapitre par chapitre au XML OGL épinglé : **51/51 égaux après NFC**, sans différence lexicale.
- Les 51 snapshots sont `passage_clement_protr_1` … `_51`, mais leurs labels, leur auteur, leur CTS et leurs 51 arêtes `part_of` indiquent déjà Origène / `work_origen_exhortation_martyrdom`.
- Le manifeste demeure pourtant `author=Clement of Alexandria`, `title=Protrepticus`, source `tlg2042.tlg007`.
- `work_origen_exhortation_martyrdom` prétend à tort que les 51 enfants sont Clément et que le texte n'est pas ingéré.
- `work_clement_protrepticus` prétend encore que son `work_canonical_id` est `tlg2042.tlg007`, tout en disant ailleurs que son texte est absent. Son vrai identifiant est `tlg0555.tlg001` ([Scaife Atlas](https://atlas.perseus.tufts.edu/library/urn%3Acts%3AgreekLit%3Atlg0555.tlg001/)).
- Les trois arêtes modernes `cites_primary_source -> work_clement_protrepticus` ne prouvent pas une ingestion de Clément et ne doivent pas être déplacées automatiquement : elles requièrent leur propre adjudication sémantique.

Décision sûre : préserver les 51 UUID et textes ; corriger le manifeste et les deux work nodes ; renommer les IDs `passage_clement_*` seulement via une table d'alias atomique couvrant les 51 nœuds, 51 citations et tous les endpoints. Aucun passage ne doit rester enfant de Clément.

### De principiis / Peri Archon

#### Grec

Les 24 passages `21047-21070` sont du grec ancien propre, `De princ.` III.1.1-24. Leur source déclarée TLG-E/Koetschau et la collation SC 268 sont documentées dans `data/audit/2026-08-16_de_princ_iii_1_acquisition.md`. Ils ne sont toutefois pas un manuscrit grec direct et continu du traité : ils sont le texte d'Origène **transmis par l'anthologie Philocalia 21**. `passage_role=original` est insuffisant ; le rôle sûr est `ancient_authorial_text / indirect_anthology_witness`.

Les 24 citations snapshot pointent vers `passage_origen_philocalia_21_1..24`, dont les descriptions sont des dossiers Markdown mêlant référence, grec et français. Résultat : 0/24 snapshot exact. Il faut séparer le texte grec citable du dossier analytique.

L'ancienne ligne `3e767176-490c-58a3-a173-c7e10e5d85a9` est un résumé anglais contenant une courte citation grecque, avec faux CTS `tlg2042.tlg001`; elle porte à elle seule sept citations sémantiques. Elle doit être mise en quarantaine comme note analytique non citable, puis ses six cibles conceptuelles/savantes doivent être recollationnées contre les vrais §§ 1-3.

Le passage orphelin `baa51e4b-9ad7-54a1-a971-74de1631661e` et le gros passage `a343b50a-6de2-55be-b2d7-80e1c89133e5` répètent III.1.1/III.1 dans d'autres granularités. Ils peuvent servir à la lecture, mais le moteur ne doit pas les compter comme témoins indépendants.

#### Latin de Rufin et français

Les 23 passages français de `work_de_principiis_..._eng` ont été comparés section par section aux deux faces de SC 268 : **23/23 donnent une similarité normalisée de 1,0000 avec la traduction française de la version latine de Rufin, et non avec la traduction française du grec**. Le §3 manque de ce lot. Ce résultat tranche l'ambiguïté actuelle.

La manifestation correcte est donc :

```text
Origène (auteur de l'œuvre grecque)
  -> Rufin (traducteur/adaptateur latin, témoin ancien, c. 398 pour De principiis)
    -> Crouzel-Simonetti, SC 268 (édition critique du latin + traduction française, 1980)
```

Le latin de Rufin est disponible localement dans le fichier bilingue SC 268, mais n'a pas de lot propre dans le corpus. Tant qu'il n'est pas ingéré, les passages français sont des traductions d'un témoin non résolu dans le graphe ; ils ne doivent pas être présentés comme traductions du grec.

La ligne anglaise `1179f51b-4108-51ac-be4a-f3e9c0f70e7d` est une paraphrase éditoriale, porte `tlg2042.tlg001` (`Contra Celsum`) et doit être quarantainée.

### Philocalia

Les 51 passages de corpus sous les deux suffixes `_eng`/`_grc` sont **tous français** :

- 26 passages du chapitre 23, dont quatre titres éditoriaux séparés ;
- 21 passages des chapitres 25-27 ;
- quatre traductions françaises de Philocalia 21 / `De princ.` III.1.

Les 47 nœuds de 23/25-27 annoncent `language=fra` mais gardent `passage_role=original`; le rôle correct est `published_translation`. Les quatre nœuds du ch. 21 sont des dossiers mixtes, pas des snapshots. Le corpus porte encore `tlg2042.tlg028` partout, alors que plusieurs nœuds ont déjà été partiellement corrigés vers `tlg2042.tlg019`. Les CTS de type `23.titulus.12` sont inventés et ne correspondent pas à la hiérarchie OGL.

Les 58 citations sémantiques rattachées au lot `_grc` ciblent 20 nœuds Amand/Sytsma/works. Leur contenu n'est pas automatiquement faux, mais leur statut probatoire est surévalué : elles sont aujourd'hui reliées à une **traduction française** sous une identité `_grc`. Elles doivent être remappées après création du passage grec exact, ou marquées `discussion/translation_witness`, jamais `direct_quote` grec.

L'arête `work_origen_philocalia --authored_by--> Origen` est trop grossière. L'œuvre est une anthologie traditionnellement attribuée à Basile de Césarée et Grégoire de Nazianze ; les extraits sont d'Origène. Il faut encoder `compiled_by` au niveau de l'anthologie, `authored_by` au niveau de l'œuvre-source/extrait, et `preserves_excerpt_of` pour chaque locus. L'arête globale `contains -> De principiis` doit être limitée à Philocalia 21.

### Commentaire sur Romains

Les deux passages latins actuels sont récupérables :

- `f53cf750-135d-5313-b9c8-e7fe218f6e38` = SC 543 VII.14.2-3 ;
- `77133ff1-b633-5c4d-a136-1eebf8762c2b` = SC 543 VII.14.5.

Mais :

1. le lot s'appelle `_grc`, son manifeste a le titre `Contra Celsum` et le CTS `tlg2042.tlg012` est celui d'un fragment des Lamentations ;
2. les deux nœuds snapshot latins `passage_origen_com_rm_7_16` et `_sun` conservent les anciens résumés anglais avec des pseudo-citations latines ; 0/2 snapshot exact ;
3. les deux passages `_eng` du corpus sont précisément ces résumés éditoriaux anciens ; leurs nœuds snapshot contiennent désormais de véritables traductions anglaises générées des loci latins, donc 0/2 snapshot exact ;
4. les chaînes `fingere sibi ex adverso personam`, `ad destruendum liberum arbitrium`, `permittit ut ipse se induret peccando` et `non causa sed occasio` ne sont pas dans SC 543 VII.14. Les idées d'un contradicteur et de `libertas arbitrii` sont authentiques, mais les formulations actuelles sont des reconstructions ;
5. l'analogie solaire et `non causa sed occasio` appartiennent au dossier `De principiis` III.1, pas à ce locus du Commentaire sur Romains. L'arête `passage_origen_com_rm_7_16_sun --employs--> concept_non_causa_sed_occasio` doit être quarantinée.

Le nœud `argument_origen_diatribe_inversion` est sauvable après atomisation :

| Élément actuel | Décision |
|---|---|
| Paul introduit un contradicteur/persona | direct, SC 543 VII.14.1-2 / FOTC VII.16.3-4 |
| l'objection vise à nier `libertas arbitrii` | direct, SC 543 VII.14.3 / FOTC VII.16.4 |
| les formulations latines actuellement entre guillemets | retirer comme citations directes ; non attestées |
| le terme moderne `prosōpopoiia` | taxonomie moderne/reconstruction, sauf preuve secondaire exacte |
| « Rom 9.19ff est la réfutation » et l'étendue exacte de la voix | reconstruction interprétative ; conserver comme contestée |
| influence sur Diodore/Théodore/Cyrille | secondaire, hors preuve des deux passages ; exiger citation secondaire |

Le work node doit dire : œuvre grecque d'Origène, conservée principalement dans la traduction/abrégé latin de Rufin ; pour les loci audités, le témoin est Rufin. Éviter « Greek lost » sans qualification : aucune version grecque de VII.14/16 n'a été trouvée dans les possessions auditées, mais des fragments grecs d'autres parties du commentaire existent.

## Matrice de décisions sûre

| Objet | Garder | Modifier lors de la migration | Quarantaine | Inconnu explicite |
|---|---|---|---|---|
| 51 textes `Exh. mart.` | UUID, texte, ref 1-51, CTS work/passages | manifeste, IDs de nœuds, deux work nodes | aucune ligne textuelle | renommer les IDs seulement avec alias transactionnel |
| 24 Grecs `De princ.` III.1 | texte Koetschau/TLG-E, sections | manifestation « grec via Philocalia 21 », snapshots exacts, provenance SC268 | ligne mixte `3e767...` | `tlg002` non résolu sur Scaife |
| 23 Français `De princ.` | texte SC268 français de Rufin | suffixe `fra`, `translation_of` Latin Rufin, édition/pages | note `1179...` | §3 français de Rufin absent |
| Latin Rufin `De princ.` | fichier local comme source candidate | ingérer en manifestation distincte après double collation | — | concordance intégrale grec/latin non présumée |
| Philocalia 23/25-27 français | texte comme traduction publiée après re-collation | `fra`, SC226/Junod, pages, source-work de chaque extrait | pseudo-CTS/tituli | source unique de 27.1-12 non établie |
| Philocalia grec | identité `tlg019` | ingérer depuis édition collationnée, CTS versionné `2.ch.sec` | XML OGL brut non corrigé comme source finale | corriger OCR avant publication |
| Comm. Rom. latin | deux textes SC543 actuels | lot `_lat`, work interne, snapshots exacts, Rufin traducteur | `tlg012`, ancien titre | aucun CTS latin public établi |
| Comm. Rom. anglais | traductions générées des deux loci latins, si revalidées | nouveau lot `eng_generated`, source Latin explicite | deux anciens résumés de corpus | licence/publication : ne pas les attribuer à Scheck |

## Plan de migration fail-closed

### Wave 0.1 — geler et mettre en quarantaine

1. Créer un applier unique, `--dry-run` par défaut, avec préconditions sur les hashes/valeurs des seuls objets listés ici.
2. Produire un audit JSON et une quarantaine JSONL append-only : ancien objet complet, raison, autorité, décision, date, hash.
3. Refuser l'application si un passage, un snapshot ou un manifeste a changé depuis le dry-run.
4. Marquer temporairement non citables : deux notes `De princ.` mixtes, deux résumés anglais `Comm. Rom.`, quatre snapshots Romans, tous les pseudo-CTS `tlg028/tlg012` et l'arête solaire.

### Wave 0.2 — Exhortatio, changement le moins ambigu

1. Corriger le manifeste en Origène / `Exhortatio ad martyrium`, source exacte `urn:cts:greekLit:tlg2042.tlg007.perseus-grc1`.
2. Corriger `work_origen_exhortation_martyrdom` (`needs_text_ingestion=false`, 51 enfants) et rendre `work_clement_protrepticus` textuellement vide avec `tlg0555.tlg001`.
3. Conserver tous les UUID de corpus ; renommer les 51 IDs de nœuds seulement avec alias/remap complet.

### Wave 0.3 — Commentaire sur Romains

1. Renommer la manifestation latine sans CTS grec ; enregistrer Origène comme auteur de l'œuvre et Rufin comme traducteur/abréviateur du témoin.
2. Réécrire les deux snapshots latins avec le texte corpus exact et les refs SC 543 VII.14.2-3 / VII.14.5.
3. Recréer, si désiré, deux traductions anglaises distinctes avec statut `generated_translation`, source Latin, modèle et revue humaine ; ne pas reprendre les deux résumés faux.
4. Atomiser `argument_origen_diatribe_inversion` selon la matrice ci-dessus ; supprimer/quarantainer l'arête solaire.

### Wave 0.4 — Philocalia

1. Créer une vraie manifestation grecque `tlg019.1st1K-grc1`, mais n'ingérer que les passages recollationnés contre SC 226/SC 268 ; ne jamais copier aveuglément les `U+03F2` OGL.
2. Créer une manifestation française Junod SC 226 pour 23/25-27 et une manifestation française Crouzel-Simonetti SC 268 pour ch. 21.
3. Remplacer `cts_urn` des traductions par `source_cts_urn`; seul le texte grec reçoit un CTS d'édition. Utiliser la hiérarchie `2.chapter.section` et intégrer les rubriques aux sections officielles plutôt que créer des `titulus` CTS.
4. Encoder les rôles `compiled_by`, `preserves_excerpt_of`, `translated_by`, `edited_by`; corriger ch. 25 et ch. 26 selon leurs rubriques.
5. Rejouer les 58 citations sémantiques : directes seulement contre grec exact ; traduction française = témoin de traduction/discussion.

### Wave 0.5 — De principiis

1. Conserver les 24 Grecs atomiques, mais les relier simultanément à `De principiis III.1.n` et au témoin `Philocalia 21`; ne pas les appeler manuscrit direct.
2. Remplacer leurs 24 snapshots Markdown par des snapshots textuels NFC exacts ; déplacer les dossiers Markdown en nœuds d'analyse non citables.
3. Ingérer les 24 sections latines de Rufin depuis SC 268, puis relier les 23 traductions françaises existantes ; laisser le §3 français ouvert jusqu'à extraction.
4. Mettre en alias l'orphelin `baa51...` et les conteneurs de chapitre SC268 ; interdire leur comptage comme corroboration indépendante.
5. Corriger toutes les mentions « Junod SC226 édite Philocalia 21 » en « SC268 édite le grec de Philocalia 21 ; SC226 le traite sans le rééditer ».

### Wave 0.6 — bibliographie et registre

Le KG ne possède pas de publication primaire distincte pour Koetschau GCS 22, Robinson 1893, Junod SC 226, Crouzel-Simonetti SC 268, Hammond Bammel/SC 543 ou Scheck FOTC 104. Les entrées BibTeX actuelles autour de SC 226 sont surtout des comptes rendus, pas l'édition elle-même. Ajouter chaque édition comme publication avec rôle exact, ISBN/année, droits et fichier local ; ne pas substituer un compte rendu à l'édition.

Le registre SOTA ne possède qu'une entrée globale `src_anc_origen_de_principiis`, qui note correctement la coexistence grec/latin mais ne distingue pas les manifestations. Créer des sources/enjeux séparés pour chaque témoin et relier l'adjudication présente.

## Tests obligatoires

### Identité et autorité

- Assert épinglé : `tlg007 == Exhortatio`, `tlg019 == Philocalia`, `tlg028 == Comm. Matthew latin`, `tlg012 == Fragmentum in Lamentationes`.
- Assert négatif : zéro Philocalia avec `tlg028`; zéro Comm. Rom. avec `tlg012`; zéro De princ. avec `tlg001`.
- Un identifiant de source `scaife:` doit résoudre une **édition** existante, pas seulement ressembler à un URN CTS.

### Langue, rôle et témoin

- Classifieur de script + métadonnées : `grc`, `lat`, `fra`, `eng` doivent concorder.
- `passage_role=translation` exige `source_passage_id`, `source_language`, traducteur et manifestation source.
- `content_kind=modern_translation` interdit `passage_role=original`.
- Rufin, Junod, Crouzel-Simonetti et Scheck doivent avoir des rôles distincts (`ancient_translator`, `modern_translator`, `editor`).

### Snapshot et citabilité

- Pour chaque `snapshot_passage_node`, `NFC(node.description) == NFC(corpus.text_content)`.
- Un snapshot ne contient ni rubrique Markdown, ni résumé éditorial, ni deux langues.
- Assert négatif contre les pseudo-citations Romans : les quatre chaînes non attestées listées plus haut ne peuvent avoir `attestation=direct`.
- Un passage traduit peut soutenir une discussion, mais une citation grecque directe exige le passage grec recollationné.

### Structure et déduplication

- 51/51 Exhortatio `part_of -> work_origen_exhortation_martyrdom`; 0 vers Clément.
- Philocalia 23 -> Comm. Gen. III ; 25 -> Comm. Rom. I ; 26 -> Comm. Ps. 4 ; 27.13 -> Comm. Cant. II.
- Les 24 sections grecques `De princ.` ont une relation de témoin via Philocalia 21.
- Les mêmes caractères grecs à granularité section/chapitre ne comptent jamais comme deux témoins indépendants dans les scores GraphRAG.

### Applier et adversarial

- Dry-run sans écriture ; second run zéro mutation ; quarantaine append-only déterministe.
- Fixture négative pour chaque mauvais URN/langue/titre et pour un snapshot décalé.
- Fixture adversariale : remplacer `tlg019` par `tlg028`, `lat` par `grc`, ou SC `VII.14` par `VII.16` sans schéma doit faire échouer le gate.
- Vérifier passages/citations sans dangling IDs, work-child, alias, manifeste/snapshot, registry issue/adjudication et absence de régression globale.

## Inconnues à ne pas fermer artificiellement

1. Le dépôt OGL ne fournit pas de manifestation Scaife de `tlg2042.tlg002`; la résolvabilité publique doit rester `unverified`.
2. La source œuvre unique de Philocalia 27.1-12 n'est pas établie par la rubrique relue ; ne pas la déduire de parallèles thématiques.
3. Aucune version grecque des loci Comm. Rom. VII.14/16 n'est dans les possessions auditées ; ne pas généraliser en « tout le grec du Commentaire est perdu ».
4. Les dates du Commentaire varient entre « vers 243 » (Cerf) et « 244-246 » (Scheck) : encoder `c. 243-246`, pas une année exacte.
5. Les traductions anglaises actuelles des deux loci Romans sont générées et non l'anglais publié de Scheck ; leur exactitude doit être revue sans les attribuer à FOTC 104.
6. Les droits de SC 226/268/543 et FOTC 104 ne sont pas des licences ouvertes constatées. Ne pas publier les textes intégraux sous une fausse licence. Le grec OGL, lui, porte CC BY-SA 4.0 dans son en-tête TEI.

## Ordre recommandé et gate de sortie

Ordre strict : **Exhortatio → Romans latin → Philocalia → De principiis → bibliographie/registre → revue indépendante → revue adversariale**.

Le dossier Origène ne peut être déclaré publiable que lorsque :

1. toutes les manifestations ont langue, auteur, transmetteur, éditeur et rôle exacts ;
2. tous les snapshots sont NFC-exacts ;
3. les faux URN et pseudo-citations ont disparu des chemins citables ;
4. chaque citation sémantique a été rejouée contre le bon témoin ;
5. l'évaluation ne compte plus les duplications de granularité comme corroborations indépendantes ;
6. deux revues indépendantes, dont une adversariale, ont validé les mêmes sorties de tests.
