# Audit factuel des neuf premières entrées du glossaire (A-I)

Date: 2026-08-24  
Fichier audité: `frontend/src/content/glossary.json`  
SHA-256 au début de l'audit:
`4bff80bc4173c44f3ef5f2cf2fad4c1fafc44d9a067891358614c0a1ce100dd6`  
Portée: les neuf premières entrées, de `Akrasia` à `Cylinder Analogy`.  
Mode: audit savant en lecture seule. Aucun changement du glossaire, du KG, du
corpus ou du registre.

## Verdict exécutif

| # | ID | Verdict | Motif principal |
|---:|---|---|---|
| 1 | `concept_akrasia_weakness_of_will` | **revise** | noyau correct, mais projection anachronique d'une faculté de volonté et généralisation stoïcienne |
| 2 | `concept_ananke_necessity_democritus_h8i9j0k1` | **revise** | polysémie aplatie; destin stoïcien présenté à tort comme développement lexical de `ananke` |
| 3 | `concept_ancient_free_will_debate_structure_z6a7b8c9` | **revise** | taxonomie moderne utile mais trop binaire et chronologie erronée |
| 4 | `concept_incompatibilism_ancient_o5p6q7r8` | **block** | faux terme grec technique, Carneade sur-résolu, Alexandre transformé en briseur de chaîne causale |
| 5 | `concept_apocatastasis` | **block** | locus DL VII.134 inadéquat et doctrine origénienne controversée présentée comme univoque |
| 6 | `concept_autexousion_christian_freedom_u1v2w3x4` | **block** | terme faussement déclaré distinctivement chrétien et auto-originaire; généalogie latine non prouvée |
| 7 | `concept_boulesis_rational_desire_ef9f861d` | **revise** | confusion `boulesis` / `bouleusis`; formule stoïcienne attribuée sans preuve à Platon |
| 8 | `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6` | **block** | DL X ne rapporte pas le swerve; motif de liberté attribué trop directement à Épicure |
| 9 | `concept_cylinder_analogy_chrysippus_e5f6g7h8` | **block** | une lecture disputée est publiée comme conclusion chrysippéenne univoque |

Résultat: **0 approved, 4 revise, 5 block**. `Block` signifie que la définition
publique actuelle contient une assertion centrale factuellement non sûre; cela
ne demande pas de supprimer le concept, mais interdit de republier le texte
actuel sans réécriture.

## Méthode et hiérarchie de preuve

1. Les textes primaires locaux ou les TEI officiels ont autorité sur les nœuds
   synthétiques et les anciennes descriptions KG.
2. Les PDF secondaires ont été utilisés pour attribution et limites
   interprétatives, jamais comme substituts d'un texte antique.
3. Les termes modernes `free will`, `compatibilism`, `incompatibilism` et
   `libertarian` sont admis uniquement comme catégories analytiques déclarées.
4. Une absence dans un corpus lacunaire n'est jamais transformée en preuve
   historique d'absence.
5. Les corrections proposées sont de courtes paraphrases; aucune longue citation
   sous copyright n'est reproduite.

## Inventaire des autorités

### Artefacts locaux

| Artefact | Usage | SHA-256 |
|---|---|---|
| `data/literature_acquisition/long_sedley_1987_hellenistic_philosophers_vol2.pdf` | textes et commentaires Epicure/Stoa | `af6fc6f55d30f1896d59e2898e989016043990a498f8ff8cd5e8850bbb5e84a8` |
| `data/literature_acquisition/sorabji_1980_necessity_cause_blame.pdf` | trois lectures du cylindre; catégories modernes | `be1f8fce483503d04504c73da30dc9bbcd52f5f8c04bd0e520cbd42fd4a3d500` |
| `data/literature_acquisition/sharples_1983_alexander_de_fato.pdf` | limites de la reconstruction d'Alexandre | `7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638` |
| `data/literature_acquisition/SAPERE28_Tatian_Rede_an_die_Griechen_2016_OA.pdf` | autexousion chrétien, pagination seulement | `33f355b55cb446273498b2557022e52c3e83a1f75aea84ec136eb31ea5aea4db` |
| `data/audit/primary_fetch/urn_cts_latinlit_phi0474_phi049_lat/Cicero_De_Fato_LAT.perseus-lat1.txt` | Cicéron, *De fato* | `daf3c4a55fb9bb7508c55ef2d81cce75b0806b2d31214d60d2ae7a76aa6b93fe` |
| TEI Bruns/OGL d'Alexandre | *De fato* primaire | `184b01f38061cfa00b276ed8d9580f3f842f564856851e4bcc124adcc2edbb2f` |
| `de_fato_section_14.grc.txt` | `autexousion` païen chez Alexandre | `dfc233b703c68a7501c1d03336c4b6f01f65783825b792b8f5d344bc8f38d7f8` |
| Origen, *De principiis* III.1.1 grec local | autexousion | `a6ee091dee71829b7ca241eff50fa2b8786964ed3b0cf7c106f5277c82a2e0e5` |
| corpus passages JSONL, état lu | lignes antiques citées ci-dessous | `4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec` |

Le PDF Fürst 2019 disponible localement est seulement une table des matières de
deux pages (`content_completeness=toc_only`, SHA-256
`41ac899ddbbc446880fde1213e08678c2dbe95a80573317461c20bfc2f53c921`).
Il ne peut pas prouver les assertions fortes sur l'apocatastase ou la généalogie
du libre arbitre.

### Autorités primaires officielles consultées sans ingestion

| Texte | URL officielle | SHA-256 des bytes consultés |
|---|---|---|
| Platon, *Protagoras* | `https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data/tlg0059/tlg022/tlg0059.tlg022.perseus-grc2.xml` | `1a78b4b0055f083db3c63bdb5c0fddbd77ab377b049eeaa4c74e5dbaa618aed9` |
| Platon, *Timaeus* | `https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data/tlg0059/tlg031/tlg0059.tlg031.perseus-grc2.xml` | `9280b741ab6e430b710d3cea58979e0b2b117b1762074798ece640e099858289` |
| Aristote, *Ethica Nicomachea* | `https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data/tlg0086/tlg010/tlg0086.tlg010.perseus-grc2.xml` | `1589cf781efb47bcf3118beb54e23284a29c5b3a99213fcc12793aaef439c648` |

Ces trois fichiers ont été lus en réseau sans être ajoutés au workspace.

## 1. Akrasia (Weakness of Will)

ID: `concept_akrasia_weakness_of_will`  
Verdict: **revise**.

### Contrôle atomique

- **Sûr:** *Protagoras* 352b-358d examine l'opinion selon laquelle le
  savoir serait dominé par plaisir, douleur, colère ou peur. À 358c-d, Socrate
  ramène l'échec à l'ignorance et nie qu'un agent aille volontairement vers ce
  qu'il tient pour mauvais.
- **Sûr:** Aristote, *EN* VII.1-10, consacre un traitement étendu à
  l'akrasia. VII.7 distingue explicitement `astheneia`: délibérer puis ne pas
  tenir le résultat, et `propeteia`: agir sans attendre la délibération.
- **À corriger:** `acting against one's better judgment` est un bon raccourci,
  mais `whether the will can be overpowered` projette une faculté de volonté que
  ni le passage platonicien ni Aristote ne nomment ainsi.
- **À corriger:** DL VII.110-111 permet de dire que les Stoïciens décrivent les
  passions comme impulsions irrationnelles/excessives et, chez Chrysippe, comme
  jugements. Il ne suffit pas à établir que **toute** action fautive « stems from
  false judgment » au sens unique de l'akrasia aristotélicienne.

### Preuves locales

| Locus | UUID | SHA-256 du texte de ligne |
|---|---|---|
| Aristote, *EN* VII.2 | `611324c1-6c84-47a7-be99-0da09dde9fe6` | `f5eb6551f76704b571aaa23561606cad437bd26b62f5ad9a598f0f4f809a1464` |
| Aristote, *EN* VII.7 | `fa84ef2d-ff47-4176-9f9a-13304915bb54` | `d927b37bd70b5712f5baf68c202747fc725e50d42fce7e41896f5839f9b4bf50` |
| DL VII.110 | `f1f34200-4967-4792-bb77-c1f8d6709062` | `1ccd4e04d7cb1a50ca5e09cfa8be109f2d28cb595d84d3f10a6e2aeb6558ff60` |
| DL VII.111 | `e9158b41-a2ec-41dd-9e72-c5238dc7d7db` | `e007313263aaabb702e5cbe694655db6dd69e663376c78532a92de5f8643df57` |

### Texte de remplacement proposé

> Akrasia is acting contrary to one's standing rational judgment or commitment
> under the influence of appetite or emotion. In Plato's *Protagoras*
> 352b-358d Socrates rejects the popular picture that knowledge is overpowered
> and explains the error through ignorance; this is not yet a theory of a
> faculty called the will. Aristotle, *Nicomachean Ethics* VII.1-10, analyzes
> akrasia and at VII.7 distinguishes weakness, in which agents deliberate but do
> not stand by the result, from impetuosity, in which they act without waiting
> for deliberation. Stoic sources use a different framework, treating passions
> as excessive irrational impulses and, in Chrysippus, as judgments.

## 2. Ananke (Necessity / Determinism)

ID: `concept_ananke_necessity_democritus_h8i9j0k1`  
Verdict: **revise**.

### Contrôle atomique

- **Sûr:** DL IX.45 rapporte que, pour Démocrite, tout advient selon
  nécessité et que le tourbillon est cause de la génération de toutes choses,
  ce qu'il appelle nécessité.
- **Surinterprété:** « necessary laws », « strict causal necessity governing
  all natural processes » et « mechanistic determinism without teleology » sont
  des reconstructions modernes, non le contenu lexical complet de DL IX.45.
- **Sûr:** *Timaeus* 48a dit que le cosmos naît du mélange de l'intellect et de
  la nécessité, l'intellect dominant en persuadant la nécessité de mener la
  plupart des choses vers le meilleur.
- **Faux développement historique:** la `heimarmene` stoïcienne n'est pas une
  transformation lexicale progressive de l'`ananke`; les témoins articulent des
  notions distinctes de destin, nécessité, causes et providence.
- **Sûr mais à séparer:** Épicure, *Ep. Men.* 133-134, oppose nécessité,
  hasard et ce qui dépend de nous. Carneade et Alexandre ne doivent être ajoutés
  qu'avec leurs témoins propres, non comme une classe unitaire.

### Preuves locales

| Locus | UUID | SHA-256 du texte de ligne |
|---|---|---|
| DL IX.45 | `c62b6498-f57f-4c85-bc83-e6b2dcc7814e` | `8155b9b36f8ceb4f4f5a4c73ae489a08390323268f372c0f6be42dc0c3a0abdd` |
| DL X.133 | `3995b2b0-73e2-4e4b-9e3a-3a821f4f485d` | `9ed48cc4882fdd02e939cbf28ec087470f2e39dad55c3097637fcf8c4525bf91` |
| DL X.134 | `ba54d6da-69f9-4a80-8ef5-3d458be11dfb` | `ce2b3cc7a7ec0c6a3b0146ed6b36fcf583eceaeb2b158f847902cd5be969efc5` |

### Texte de remplacement proposé

> Ananke means necessity or constraint, but its role varies by author. Diogenes
> Laertius IX.45 reports that Democritus held that everything occurs according
> to necessity and called the cosmic vortex cause or necessity; talk of
> mechanistic laws is a modern reconstruction. In Plato's *Timaeus* 48a the
> cosmos arises from intellect and necessity, with intellect ruling by
> persuading necessity toward the better. Stoic fate is a separate doctrine,
> not a lexical development of ananke. Epicurus, *Letter to Menoeceus* 133-134,
> distinguishes necessity, chance, and what depends on us.

## 3. Ancient Debate: Compatibilism vs. Incompatibilism

ID: `concept_ancient_free_will_debate_structure_z6a7b8c9`  
Verdict: **revise**.

### Contrôle atomique

- `Compatibilism` et `incompatibilism` sont des catégories modernes. Le texte
  le reconnaît, mais « two positions emerged » les transforme ensuite en camps
  antiques exhaustifs.
- Les témoins chrysippéens associent destin universel, causes antécédentes,
  assentiment, constitution de l'agent et événements co-destinés. Ils ne
  livrent pas un compatibilisme unique et auto-interprété.
- Carneade est connu par des transmetteurs dialectiques, notamment Cicéron; sa
  critique ne doit pas être publiée comme un système positif complet.
- Alexandre est un adversaire du destin stoïcien, mais Sharples souligne que le
  traité reste dialectique et ne résout pas l'analyse causale de l'action.
- Les épicuriens et les auteurs patristiques ne constituent pas un seul camp;
  chaque doctrine doit conserver chronologie, texte et théologie propres.
- `period=Roman Imperial` est faux pour un schéma qui commence au Stoa et au
  Jardin hellénistiques et s'étend aux Pères.

### Repères secondaires contrôlés

- Long-Sedley 62C-D, p. 383-385 / PDF 391-393: noyau causal transmis, non
  doctrine compatibiliste univoque.
- Sorabji p. 87-88 / PDF 104-105: `compatibilism` est sa catégorie moderne et
  son attribution historique à Chrysippe reste prudente.
- Sharples p. 21-22 / PDF 15-16 et p. 146-149 / PDF 78-79: taxonomie moderne
  `libertarian`, mais dette causale non résolue.

### Texte de remplacement proposé

> Compatibilism and incompatibilism are modern comparison categories, not names
> of two ancient schools. Texts attributed to Chrysippus combine universal fate
> with agent-relative assent, character, causal distinctions, and co-fated
> events, but their exact interpretation is disputed. Cicero reports
> Carneadean objections; Alexander polemically attacks Stoic fate; Epicurean
> and Christian accounts differ from one another. The ancient evidence should
> therefore be compared claim by claim rather than divided into two exhaustive
> camps.

## 4. Ancient Incompatibilism

ID: `concept_incompatibilism_ancient_o5p6q7r8`  
Verdict: **block**.

### Blockers

1. `ἀσύμβατον` n'est pas le nom antique attesté d'une doctrine appelée
   incompatibilisme. Le champ `originalTerm` crée un faux équivalent technique.
2. Le raisonnement carnéadien est transmis par Cicéron. *De fato* 23-25 permet
   de distinguer absence de cause extérieure antécédente et absence absolue de
   cause; il ne suffit pas pour la formule actuelle selon laquelle les causes
   internes « are themselves fated ».
3. Alexandre n'établit pas une cause substantielle ultime qui briserait la
   chaîne. Sharples dit expressément que l'agent comme point de départ ne résout
   pas le dilemme déterminisme / événement sans cause et qu'Alexandre ne fournit
   pas l'analyse causale requise.
4. Le clinamen est attesté pour la tradition épicurienne par Lucrèce et les
   critiques antiques; le motif fort ne doit pas être placé sans qualification
   dans la bouche de l'Épicure conservé.

### Preuves

| Locus | UUID | SHA-256 du texte de ligne |
|---|---|---|
| Cicéron, *Fat.* 23 | `e238357f-a294-4df1-92e9-3385b23f6f7b` | `1cbf788e62133fea0fdb8185f39b12497e9b7aa82083431a3b2a68a4953484fd` |
| Cicéron, *Fat.* 24 | `293aecc4-bb8c-4776-8c86-60aaa276c734` | `149e78e3b1965735fab3ca9092d308e306fe89f1df3f46791c74392f8f6e590b` |
| Cicéron, *Fat.* 25 | `8348e48d-c4b4-474d-8638-055abf865bdb` | `ac51b7c8d9a5acb83e43bee430bc7a787c43c6bd174c6454a7f496a8104ccc97` |
| Cicéron, *Fat.* 31 | `7bdfd343-54ca-4e5e-bccd-6fafa8345670` | `f3a12008922dfe60fb930940df3c663a4200ef6b43d61ad0c41f9cfaa9944a09` |
| Alexandre, *Fat.* 14 | `ae88c271-a54c-4da5-8842-fc4eecc661c2` | `a069e8c63b5a0a67266e0b6cb6aa1369e6c9c1297aec517b8e83747ffdb45eee` |

### Réécriture minimale avant déblocage

- Renommer l'entrée `Modern incompatibilist readings of ancient arguments`.
- Supprimer `originalTerm=ἀσύμβατον`.
- Attribuer séparément Cicéron/Carneade, Alexandre/Sharples et
  Lucrèce/tradition épicurienne.
- Remplacer `breaking causal chains` par la dette explicite de Sharples.

### Texte de remplacement proposé

> Modern incompatibilist readings group several ancient arguments against
> universal fate, but no ancient school used this label. Carneades, as reported
> by Cicero, argues that voluntary motion need not have an external antecedent
> cause without being uncaused in every respect. Alexander argues that Stoic
> fate undermines what depends on us, yet Sharples stresses that calling the
> agent a starting point does not solve the causal dilemma. Lucretius and Cicero
> connect the Epicurean swerve with escape from necessity; no surviving text of
> Epicurus makes it a complete theory of free agency.

## 5. Apocatastasis (Restoration)

ID: `concept_apocatastasis`  
Verdict: **block**.

### Blockers

- `ἀποκατάστασις` est un nom général de restauration ou rétablissement, non un
  terme portant seulement deux doctrines opposées. DL X.44 l'emploie même pour
  le rebond/rétablissement atomique après collision.
- DL VII.134 expose les principes actif/passif et l'ekpyrosis; il ne désigne pas
  une récurrence périodique de chaque individu identique. DL VII.142 décrit la
  formation du cosmos. Le locus actuel ne prouve donc pas sa phrase principale.
- Les témoins stoïciens sur récurrence forte/faible doivent être distingués. Le
  renvoi global `SVF II.596-632` n'autorise pas à choisir sans témoin la version
  « every individual recurs identically ».
- Pour Origène, `apocatastasis` est aussi un label doctrinal de réception. La
  portée universelle, l'état final, la succession des âges et la compatibilité
  avec le libre choix sont des questions textuelles et historiographiques
  controversées, compliquées par la transmission grecque/latine de *De
  principiis*.
- Le corpus local III.1 atteste une pédagogie divine qui respecte le concours de
  l'agent; il ne contient pas les livres eschatologiques nécessaires pour
  valider « restoration of all rational beings to original unity ».

### Preuves locales

| Locus | UUID | SHA-256 du texte de ligne | Résultat |
|---|---|---|---|
| DL VII.134 | `290e9562-305f-4ada-a392-4092e5406840` | `d9e93805093eb827f97d1d02856372979751b567405bdc51a375aec1715ff1cb` | pas de récurrence individuelle |
| DL VII.142 | `b8d21580-a51c-4d03-9e49-dbf3bff594d9` | `cf3e96a64a72ae98d9337e73d5c8fe7a7bd2669e1e4580f48505e82049ee88e7` | cosmogonie |
| DL X.44 | `e58368a1-1c20-40d9-886b-083be6b58fba` | `457b741307dc73c474b77752a226e1c686d5c2f68b76fa802e4d4fb25bfd9b79` | restauration après collision atomique |
| Origène, *Princ.* III.1.13 | `48b921b0-5333-51ee-ba88-4478e310a841` | `3728aee7a2a80a584121bc8775bd9155af78c7b51d3b28450496ba27b7ec5de0` | délai pédagogique vers le salut |
| Origène, *Princ.* III.1.15 | `addce4e5-1be3-5a4b-a9fe-8191f02fe841` | `5dc8c092caf7ffd521693390cb427ee39eadfe1256f1591b4c2e72d7399fc6ae` | restauration de la vue, pas doctrine cosmique |

### Condition de déblocage

Collation primaire de *De principiis* I.6 et III.6 dans leurs témoins
grecs/latins, puis séparation de quatre objets: lexème général, reconstitution
cosmique stoïcienne, récurrence, et doctrine origénienne/reception.

### Texte de remplacement proposé après cette collation

> Apokatastasis is a general Greek word for restoration or re-establishment,
> whose meaning depends on context. Stoic conflagration, cosmic
> reconstitution, and recurrence must be distinguished and supported by their
> individual witnesses; Diogenes Laertius VII.134 does not by itself attest
> identical recurrence. "Origenist apokatastasis" is a later doctrinal label
> for disputed readings of eschatological passages in *On First Principles*.
> Origen's account of divine pedagogy and rational agency should not be reduced
> either to automatic predestination or to a simple denial of universal
> restoration.

## 6. Autexousion (Christian Free Will)

ID: `concept_autexousion_christian_freedom_u1v2w3x4`  
Verdict: **block**.

### Blockers

1. Le terme n'est pas « distinctively Christian ». Alexandre, *De fato* 14,
   emploie `autexousion` pour le sens fort de ce qui dépend de nous; la tradition
   épictétéenne emploie aussi l'adjectif dans le vocabulaire de la maîtrise de
   soi.
2. `Autexousion` signifie être sous sa propre autorité / disposer de soi selon
   le contexte; il ne signifie pas de lui-même « cause auto-originaire non
   causée ».
3. Justin, *Apol.* II.6, Tatien 7.2 et Origène, *Princ.* III.1, offrent de bons
   usages chrétiens liés à création, bifurcation morale, éloge/blâme et jugement
   divin. Ils ne constituent pas une théorie patristique unique.
4. La flèche lexicale `autexousion -> liberum arbitrium` et l'affirmation d'un
   terme médiéval standard demandent une étude de traduction et réception. Le
   présent fonds ne la prouve pas.

### Preuves locales

| Locus | UUID | SHA-256 du texte de ligne |
|---|---|---|
| Alexandre, *Fat.* 14 | `ae88c271-a54c-4da5-8842-fc4eecc661c2` | `a069e8c63b5a0a67266e0b6cb6aa1369e6c9c1297aec517b8e83747ffdb45eee` |
| Justin, *Apol.* II.6 | `0b68baff-e316-4734-a491-acb5acdafee3` | `a0017772f8da80cd74c8d1fdc8a6651f99b0daaf7e4fc5a05d6fed5caf54942c` |
| Origène, *Princ.* III.1.1 | `f7520632-f6f5-5d4d-b18f-c81dca177677` | `4bd12664b187cdc4ffa7e0962cee37987c56d721cd3a9dbc8642c799e94bbe3f` |
| Origène, *Princ.* III.1.6 | `a7f70127-b018-5e45-b216-1e2044ce7c4f` | `0e9914397280cd0dc0a00e734817074ae7cd56fd8d4ea706d744d2c94c150aa9` |

Tatian 7.2 est visuellement confirmé à la p. imprimée 48 / PDF 59 du volume
SAPERE, mais le scan n'est pas la manifestation Otto et ne doit pas fournir le
texte public.

### Réécriture minimale avant déblocage

- Titre: `Autexousion (Self-rule / Self-determination)`.
- Période: usage trans-écoles impérial et patristique, pas origine patristique.
- Retirer `self-originating` et la généalogie latine non sourcée.
- Atomiser Justin, Tatien et Origène.

### Texte de remplacement proposé

> Autexousios or autexousion denotes being under one's own authority or
> self-determining, with meaning that varies by context. It is not exclusively
> Christian: pagan authors such as Alexander of Aphrodisias use it in debates
> about what depends on us. Christian authors including Justin, Tatian, and
> Origen apply it to created rational agency, praise and blame, divine judgment,
> and the origin of evil, but their theories are not identical. The term does
> not by itself assert an uncaused or self-originating will, and any direct
> genealogy to Latin *liberum arbitrium* requires separate evidence.

## 7. Boulesis (Rational Desire / Will)

ID: `concept_boulesis_rational_desire_ef9f861d`  
Verdict: **revise**.

### Contrôle atomique

- **Erreur lexicale:** `boulesis` (`βούλησις`) n'est pas `bouleusis`
  (`βούλευσις`). La première est souhait/désir; la seconde délibération.
- Aristote, *EN* III.2, distingue `boulesis` de `prohairesis`: elle peut viser
  l'impossible ou ce que l'agent ne réalisera pas lui-même, et porte plutôt sur
  la fin. III.4 discute si son objet est le bien réel ou apparent.
- DL VII.116 définit la `boulesis` stoïcienne comme `eulogos orexis`, une bonne
  passion opposée au désir irrationnel. Cette définition est stoïcienne; le
  glossaire ne fournit aucune preuve que Platon l'aurait formulée ainsi.
- Dihle 1982 n'est localement présent que comme notice bibliographique, sans
  page ni manifestation lisible. Sa généalogie vers `voluntas` doit rester
  attribuée et page-pinnée, non conclusion de la définition.

### Preuves

- Aristote, *EN* III.2, 1111b20-30 et III.4, 1113a15-b2, dans le TEI officiel
  Perseus hashé `1589cf...c648`.
- DL VII.116, UUID `03809b9a-cc3f-49b2-b5ef-2a932c62d747`, SHA-256 du texte
  `b30e90e4cdfdd315c295b4b5cbcf2107f3ae4895b2e132748af3ce48b50dcf7d`.

### Texte de remplacement proposé

> Boulesis means wish or rational desire, not deliberation; deliberation is
> bouleusis. In Aristotle, *Nicomachean Ethics* III.2, boulesis differs from
> prohairesis: it can concern impossibilities or outcomes not achievable by the
> agent, and it is chiefly directed at the end. III.4 asks whether its object is
> the real or the apparent good. In Stoic terminology, Diogenes Laertius VII.116
> defines boulesis as a well-reasoned desire, an eupathic counterpart to
> irrational appetite. Claims about its relation to Latin *voluntas* are later
> historical interpretations and require explicit secondary attribution.

## 8. Clinamen / Parenklisis (Atomic Swerve)

ID: `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6`  
Verdict: **block**.

### Blockers

- DL X.133-134 distingue nécessité, hasard et ce qui dépend de nous, avec
  blâme et son contraire. Il ne rapporte ni `parenklisis` ni mouvement atomique
  déviant.
- Le swerve est attesté surtout par Lucrèce, *DRN* II.216-293, et Cicéron,
  *De fato* 21-25. Cicéron l'attribue à Épicure dans une polémique; Lucrèce
  relie la déviation à la `voluntas` arrachée au destin.
- « Epicurus introduced it explicitly to ground human freedom and moral
  responsibility » fusionne l'attribution critique de Cicéron, l'argument de
  Lucrèce et *Ep. Men.* 133. Ce n'est pas une proposition conservée d'Épicure.
- Le clinamen ne doit pas être publié comme cause directe, suffisante ou
  explication complète de chaque volition. Long-Sedley le borne au plus comme
  condition nécessaire dans leur lecture.
- `clinamen` est un label latin conventionnel; Lucrèce utilise ici les verbes de
  déviation, Cicéron `declinatio`. Il faut éviter de présenter le nom comme une
  citation technique d'Épicure.

### Preuves locales

| Locus | UUID | SHA-256 du texte de ligne |
|---|---|---|
| Lucrèce II.250-274 | `924a969a-5428-42f7-96a2-2bb094d558bc` | `797b64ded68f48ef5c7c2bfb319a819d3ee6696fe6b0f3f65ecd9b5624aac036` |
| Lucrèce II.275-299 | `dd949fff-90da-4315-a4fc-ae455566b268` | `65ff8de50aaf06f5c1054d8c29968534c56c4a3a7b281840c6a28fdbe9c432da` |
| Cicéron, *Fat.* 22 | `e2fdbfe3-4092-4552-bb6b-aa9255f61959` | `f12ab8c6f6aa12c55a587f6f320675d467287e9717762f450de6ff1d932d6917` |
| Cicéron, *Fat.* 23 | `e238357f-a294-4df1-92e9-3385b23f6f7b` | `1cbf788e62133fea0fdb8185f39b12497e9b7aa82083431a3b2a68a4953484fd` |
| Épicure, *Ep. Men.* 133 | `3995b2b0-73e2-4e4b-9e3a-3a821f4f485d` | `9ed48cc4882fdd02e939cbf28ec087470f2e39dad55c3097637fcf8c4525bf91` |

Long-Sedley 20A-F: p. 104-112 / PDF 112-120; le swerve proprement dit est
20F, p. 110-112 / PDF 118-120. La note p. 111 / PDF 119 refuse une lecture
causale suffisante.

### Texte de remplacement proposé

> The atomic swerve is an Epicurean doctrine attested chiefly by Lucretius,
> *De Rerum Natura* II.216-293, and Cicero, *De Fato* 21-25. Lucretius describes
> a minimal deviation at no fixed place or time and connects it with voluntas;
> Cicero polemically reports that Epicurus introduced declination to avoid
> necessity. Epicurus's surviving *Letter to Menoeceus* 133-134 distinguishes
> necessity, chance, and what depends on us, but does not mention the swerve.
> The swerve should therefore not be presented as Epicurus's surviving,
> sufficient, or complete explanation of free action.

## 9. Cylinder Analogy (Chrysippus)

ID: `concept_cylinder_analogy_chrysippus_e5f6g7h8`  
Verdict: **block**.

### Noyau primaire sûr

- Cicéron, *Fat.* 41-43, attribue à Chrysippe une distinction entre causes
  parfaites/principales et auxiliaires/prochaines. L'impression précède
  l'assentiment comme la poussée initie le cylindre; la suite du mouvement se
  fait selon la force/nature propre du cylindre ou de l'agent.
- Aulu-Gelle VII.2.6-13 transmet que les caractères mentaux reçoivent la force
  extérieure du destin selon leur qualité propre et utilise le cylindre pour
  empêcher que le destin serve d'excuse automatique.

### Sur-résolutions actuelles

1. « external causes and internal nature jointly determine action » est une
   reconstruction possible, non une formulation neutre de tous les témoins.
2. Le texte n'établit pas que la nature de l'esprit est **la** cause principale
   au sens d'une taxonomie simple et exclusive; Cicéron distribue plusieurs
   types de causes et développe une analogie.
3. « Therefore assent is fated but not necessary » canonise l'une des lectures
   disputées. Sorabji distingue au moins trois interprétations historiques:
   échappée à la nécessité; responsabilité compatible avec nécessité; rejet de
   la seule nécessité issue des causes externes.
4. « we are responsible because we are the principal cause » n'est pas une
   conclusion verbatim du témoin. Le noyau sûr est causalité interne/propre et
   refus de l'excuse fataliste, sans alternative ouverte démontrée.
5. Le renvoi Gellius VII.2.11 seul est insuffisant; l'argument couvre
   VII.2.6-13.

### Preuves locales

| Locus | UUID | SHA-256 du texte de ligne |
|---|---|---|
| Cicéron, *Fat.* 41 | `fc50aff8-32e5-443b-950d-35ad89b15d96` | `3bf163bf160f02f19fa40db1a70de2d8372128a7f2cf1e543344de02725e57f4` |
| Cicéron, *Fat.* 42 | `0a1bf1ae-9888-4a9e-8da8-9ff3ae4c8f7e` | `f75ec9b36ce4efe170d7176e4468983bd16a4ba77e33e546d7ecfa478890ca99` |
| Cicéron, *Fat.* 43 | `1812b556-ba17-4407-9998-f0383d158dd2` | `ddc329a9b086acc67fbbf79ef081d30a054ed63bfb5da913378faaf88e2a6fb5` |
| Gellius VII.2.7 | `b0efb6ac-9afa-40fc-9f24-d5337ff6350c` | `ea51e1b171280bb10c3741f427770bca1559ba379c78a054b1bde5bfe27d521d` |
| Gellius VII.2.11 | `fa311a9a-11fc-4c84-837c-a8b1369f8477` | `218c0609d2276fe22608d18382c942d8f997ceb6f325a01e9646fea5cde20c82` |
| Gellius VII.2.12 | `77999bca-438f-44ee-83de-b7359ae699b2` | `60307a0d6b332f91809ecd854d4ac2645cf3baf08d1743e1f94942e49b5988b7` |
| Gellius VII.2.13 | `72d11f9b-8724-4959-921b-31915be779b8` | `2736f73af6a44a62e2884da37fcd9874b4d6085bbd521cb64dbb9a0da529a1e2` |

Long-Sedley 62C-D: p. 383-385 / PDF 391-393. Sorabji: p. 80-83 /
PDF 97-100. Alexandre 62G-H doit rester un témoin critique distinct, non fusionné
avec Chrysippe.

### Texte de remplacement proposé

> The cylinder analogy, attributed to Chrysippus by Cicero and Aulus Gellius,
> contrasts an initiating external push or impression with the way motion
> proceeds according to the cylinder's or agent's own constitution. Cicero
> distinguishes proximate or auxiliary causes from perfect or principal causes;
> Gellius uses the analogy to reject fate as an automatic excuse for wrongdoing.
> These witnesses do not unambiguously establish alternative possibilities or a
> single thesis that assent is fated but not necessary. Sources: Cicero,
> *De Fato* 39-45; Gellius, *Noctes Atticae* VII.2.6-13. Later interpretations
> should be attributed separately.

## Corrections de structure communes

Avant toute réécriture du JSON:

1. Ajouter un champ interne d'audit ou des références structurées; les loci ne
   doivent pas rester enfouis dans une prose non testable.
2. Distinguer `ancient_term`, `modern_analytic_label`, `reported_position` et
   `secondary_interpretation`.
3. Remplacer les périodes uniques par des plages ou par la période de la
   première attestation réellement citée lorsque l'entrée traverse plusieurs
   écoles.
4. Ne jamais utiliser `originalTerm` pour fabriquer un équivalent grec d'un
   isme moderne.
5. Pour chaque définition inter-écoles, séparer des phrases atomiques avec leur
   propre source.

## Lacunes fail-closed

- Pas de manifestation locale complète et paginée de Dihle 1982: sa thèse sur
  `voluntas` reste bibliographique, non vérifiée ici.
- Le fonds local Fürst 2019 est TOC-only: il ne valide pas l'apocatastase.
- Le corpus local d'Origène couvre utilement *De principiis* III.1 mais pas la
  totalité des loci eschatologiques I.6/III.6.
- Le volume 1 de Long-Sedley n'est pas dans l'acquisition locale; aucune thèse de
  priorité historique d'Épicure n'est déduite du volume 2.
- Les témoins du cylindre sont des transmissions postérieures et parfois
  polémiques; aucune formulation autographe de Chrysippe n'est disponible.

## Statut de sortie

- Rapport seulement: **créé**.
- Glossaire: **inchangé**.
- KG/corpus/registre: **inchangés**.
- Entrées publiables sans modification: **aucune parmi les neuf**.
- Entrées révisables directement: **1, 2, 3, 7**.
- Entrées bloquées avant réécriture substantielle: **4, 5, 6, 8, 9**.
