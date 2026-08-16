# Vague 6 — assainissement de la couche dialectique et des passages-synthèses

**Statut : PLANIFIÉ, NON APPLIQUÉ.** Scripts livrés :
`scripts/data_2026_08_17_dialectical_repairs.py` (données + preuves),
`scripts/apply_2026_08_17_dialectical_repairs.py` (`--dry-run` par défaut),
règle **R16** ajoutée à `scripts/check_ingestion_rules.py`.

```bash
python3 scripts/apply_2026_08_17_dialectical_repairs.py            # dry-run
python3 scripts/apply_2026_08_17_dialectical_repairs.py --write    # application
```

Résultat du `--dry-run` sur le graphe actuel :

```
lot 2 detector: {"identity_key_groups": 436, "identity_key_nodes": 2968,
                 "detected_syntheses": 57, "ambiguous": 0}
--- check_ingestion_rules.py --new-only (created records) ---
ingestion-rules: delta of 1 nodes / 1 edges
  [WARN] R3b_work_without_canonical_id: 1
BLOCK: 0   WARN: 1

nodes 20122 -> 20123   edges 54167 -> 54120   citations 19917 -> 19917
  fix_node_claim: 1        g5_delete: 4          g5_flag_unverified: 2
  g5_keep_attested: 15     g5_retype: 4          lot2_classify: 57
  tert_create_work: 1      tert_drop_part_of: 3  tert_mark_emptied: 3
  tert_reattribute: 44     tert_rename_propagated: 1
invariants: OK
```

Idempotence vérifiée en bac à sable (copie hors dépôt) : la seconde exécution en
`--write` ne modifie rien (`nodes 20123 -> 20123, edges 54120 -> 54120`).

---

## Lot 1 — les 21 arêtes dialectiques du lot `g5_deep_2026_06_15`

Le lot g5 compte 32 arêtes, dont **21** portent une relation dialectique
(`opposes` / `agrees_with` / `critiques`). Aucune ne portait `attested_by`.
Les 11 autres (`discusses`, `responds_to`, `precedes`) sortent du périmètre de
la règle R16 et ne sont pas modifiées. Il n'y a **aucun `supports`** dans le lot
g5 : le seul `supports` fautif signalé par l'audit vient d'une autre provenance
(voir 1.c).

Chaque arête a été relue contre les deux nœuds qu'elle joint **et** contre le
texte du chercheur lorsqu'un exemplaire est sur disque. Verdicts :
**13 conservées + attestées, 4 retypées, 2 signalées invérifiables, 2 supprimées.**

### 1.a Tableau des 21 verdicts

| # | edge_id | Arête | Verdict | Preuve / motif |
|---|---------|-------|---------|----------------|
| 1 | `d2b269d5` | Inwood → Bobzien `agrees_with` | **conserver** (conf. 0,75) `relation_basis: convergence` | Inwood 1985, p. 97 : « there is in Stoicism no traditional Kantian or existentialist "will" as a distinct power and faculty in the human soul » ; pp. 89-90, Alexandre juge les stoïciens sur un τὸ ἐφ' ἡμῖν bilatéral « He knows that this is not what the Stoics mean » — même diagnostic que Bobzien treize ans plus tôt. Inwood 1985 précède Bobzien 1998 : convergence de thèses, pas acte d'adhésion. `proposition` restreinte à l'absence de *faculté* de volonté. Le texte intégral ne contient **aucune** thèse générale « les Anciens n'avaient pas le libre arbitre » : ne pas surinterpréter. |
| 3 | `ebc3a02a` | Inwood `critiques` concept *bilatéralité de τὸ ἐφ' ἡμῖν* | **conserver** (conf. 0,70) | Inwood 1985, pp. 89-90. `scope_note` : la critique porte sur le critère bilatéral **appliqué aux stoïciens par Alexandre**, non sur la lecture aristotélicienne de Sauvé Meyer (Destrée 2014), postérieure. Mériterait un nœud propre pour le critère d'Alexandre. |
| 4 | `c6393385` | Salles → Bobzien `agrees_with` | **RETYPER en `opposes`** (conf. 0,95) | **Le signe était inversé.** Salles 2005, p. 78 : « (ii) such an incompatibilist position only arose with this Aristotle scholar, not earlier… I agree with (i). But I now want to show that (ii) is wrong » — n. 29 vise nommément *Determinism and Freedom* 359 et « The inadvertent conception… » §§ 6-7. P. 81 : « This rebuts the claim that Chrysippus could not have been the author of the theory because the position it rejects only arose later in antiquity. » P. 80 n. 35 : Bobzien défend la lecture d'Aristote qu'il rejette. Supprimer aurait effacé un désaccord réel et documenté. |
| 6 | `e9a05566` | Brennan → Bobzien `agrees_with` | **RETYPER en `engages_with`** (conf. 0,80) | Brennan 2005, p. 240 : « I could not have written this part… without Bobzien (1998a)… **I have also not hesitated to disagree with her on many points of interpretation**. » P. 289 : il concède le contraste ; pp. 292-293 : « I think these historical investigations would be misguided, however, because I think the contrast between the two conceptions is somewhat obscured in Bobzien's formulation. » L'accord est faux, l'engagement est attesté. **Suite à donner** : la thèse propre de Brennan (rétrécissement du soi, Platon → Épictète mal lu → néoplatonisme → Augustin, pp. 294-302) n'a pas de nœud ; tant qu'elle n'en a pas, le désaccord de fond ne peut pas être porté au niveau des propositions. |
| 7 | `9fba7de0` | Brennan `critiques` Bobzien (réponse d'Origène à l'Argument paresseux) | **SIGNALER `unverified_g5`**, conf. 0,95 → 0,30 | Bobzien 1998a p. 173 porte bien sur l'Argument paresseux, mais Brennan 2005 ne discute nulle part *Contre Celse* II 20. Son désaccord déclaré (p. 240) est général et ne peut être rattaché à ce point. Rien trouvé dans un sens ni dans l'autre : signalée, ni supprimée ni inventée. |
| 8 | `cd75c8b6` | Karamanolis → Bobzien `agrees_with` | **conserver** (conf. 0,95) | **L'audit est réfuté par l'imprimé.** Karamanolis 2021, ch. 4 n. 15 : « In this respect I side with Bobzien (1998a, 1998b) and Frede (2011) against Dihle (1982). » L'audit tenait « d'accord avec Bobzien ET avec Frede, qui s'opposent » pour une preuve d'incohérence ; Karamanolis dit exactement cela en une phrase. Bobzien et Frede divergent sur *où* apparaît une notion de volonté, ils convergent sur « ce n'est pas une invention d'Augustin » — c'est cette proposition-là qui est enregistrée. |
| 9 | `eecd644f` | Karamanolis → Frede `agrees_with` | **conserver** (conf. 0,95) | Même note 15 ; n. 14 : « I am especially indebted to Frede's account here. » |
| 10 | `c51a0f90` | Karamanolis `critiques` Dihle | **conserver** (conf. 0,95) | Même note 15 : « …against Dihle (1982). » |
| 13 | `d319ccd0` | Sorabji (quatre brins de la volonté) `critiques` Frede | **SIGNALER `unverified_g5`**, conf. 0,90 → 0,50 | Le nœud source renvoie à Sorabji 2017, « Freedom and Will: Graeco-Roman Origins » (OUP, ISBN 978-0-19-877725-0), pp. 49-66 : **absent du disque** (la bibliothèque locale n'a que Sorabji 1980 et *Aristotle Transformed* 1990). La date rend une critique de Frede 2011 possible, et la thèse des quatre brins est en tension avec l'origine unique chez Épictète — mais une tension n'est pas une citation. |
| 14 | `a39ea0a6` | Kahn → Frede `agrees_with` | **conserver** (conf. 0,85) `relation_basis: convergence` | Kahn 1988, p. 250 : « It seems clear that Epictetus has used this rather old-fashioned term [prohairesis] to express a fundamentally new idea, much the same idea that Seneca had recently expressed by *voluntas*. » Kahn 1988 précède Frede 2011 de 23 ans : convergence, pas adhésion. |
| 15 | `b01bc633` | Irwin `opposes` Frede | **conserver** (conf. 0,80) `relation_basis: propositional_conflict` | Irwin 1992, p. 455 : « We ought not to infer, however, that the earlier philosophers have no concept of the will… it may be reasonable to attribute a concept of the will to Greek philosophers. » Irwin 1992 ne cite pas Frede (2011) : conflit de propositions, pas acte de critique. |
| 16 | `df2df6bf` | Irwin `opposes` Dihle | **conserver** (conf. 0,90) | Irwin 1992, n. 5 : la thèse « Augustin sous influence hébraïque et chrétienne » « is defended at length by A. Dihle, *The Theory of the Will in Classical Antiquity* (1982) » ; n. 7 : « Dihle's failure to identify the relevant issues is justly remarked in C. A. Kirwan's review, *Classical Review* 34 (1984), pp. 335-6. » Cible nommée, désaccord explicite. |
| 19 | `ac0529aa` | Frede `critiques` Bobzien (Alexandre = première attestation) | **RETYPER en `discusses`** (conf. 0,60) | Frede 2011 ne cite Bobzien 1998 que trois fois, en notes probatoires (nn. 10, 12, 14), et n'engage jamais sa thèse sur Alexandre ; son propre placement d'Alexandre (pp. 91-95 : « our evidence… is extremely meager until we come to Alexander of Aphrodisias ») lui est largement consonant. `critiques` affirme un acte que le livre n'accomplit pas. Le lien topique est réel : on rétrograde plutôt que de supprimer. Le vrai désaccord Frede/Bobzien reste porté par `8c34b2dc` et par l'arête attestée `99e418a3` (recension de Frede par Bobzien). |
| 21 | `c5e3815d` | Sharples 2008 `agrees_with` Sharples 2008 | **RETYPER en `extends`** (conf. 0,90) | **La prémisse de l'audit est réfutée.** Les deux nœuds ne sont pas des doublons : ils portent deux affirmations différentes du **même** article — la méthodologique p. 285 (« les explications historiques ne peuvent être entièrement déterministes ») et la substantielle pp. 289-301 (le problème quasi moderne chez Alexandre est une « coïncidence »). Quatre nœuds au total viennent de cet article, chacun avec son ancre de page. Ce qui est fautif, c'est la relation : `agrees_with` est une relation entre positions de chercheurs, et c'est une erreur de catégorie appliquée à un auteur d'accord avec lui-même dans un seul article. `extends` dit la dépendance réelle. **Aucune fusion** : fusionner quatre affirmations distinctes détruirait la citabilité à la page. |
| 23 | `905f4fb6` | Inwood `critiques` concept *ἐλεύθερον καὶ αὐτεξούσιον* | **SUPPRIMER** | La cible est la formule patristique du IIᵉ s., attestée d'abord chez Théophile, *Ad Autolycum* II.27. Inwood 1985 est une étude de l'éthique stoïcienne ancienne ; la recherche plein texte n'y trouve ni Théophile, ni αὐτεξούσιον, ni la formule. Thèses sans rapport, comme Amand/Ramelli — pas une imprécision. |
| 27 | `8c34b2dc` | Frede `opposes` Bobzien | **conserver** (conf. 0,90) `relation_basis: propositional_conflict` | Bobzien 1998b, p. 172 : « The Stoics did not require a concept of free-will… Alexander had no free-will problem either » ; p. 174 : « Alexander stops short of a concept of free will. » Frede 2011, ch. 3 : la notion naît chez Épictète. Désaccord attesté **du côté de Bobzien** (sa recension de Frede 2011, déjà portée par `99e418a3`) ; `scope_note` enregistre que l'attestation est unidirectionnelle. |
| 28 | `4bd99485` | Blackson `opposes` Frede | **conserver** (conf. 0,95) | **L'audit est réfuté par la conclusion de l'article.** L'audit jugeait l'opposition « imprécise », Blackson ne contestant que l'objet du choix. Blackson 2025, p. 100 : « Because, however, the early Stoics probably believed E too, **Frede is very likely wrong** that "the first time we have any notion of a will" (p. 46) is in the time of late Stoicism » ; et « In this case, Frede is wrong about both Epictetus and the early Stoics. » L'arête visait juste ; il ne lui manquait que sa proposition et sa citation. |
| 29 | `526b2160` | Frede `opposes` Dihle | **conserver** (conf. 0,95) | Frede 2011, Introduction, pp. 5-7 : « we should query the phrase "our modern notion of will"… he hardly seems entitled to the assumption that there is one notion of a will, and a free will at that, which we all share… **But my aim is completely different from Dihle's.** » Le graphe porte déjà `pub_frede_2011_free_will -critiques-> scholar_albrecht_dihle`. |
| 30 | `9a26acd5` | Kahn `opposes` Dihle (positions) | **conserver** (conf. 0,85), proposition restreinte au **lieu** d'émergence | Kahn 1988, pp. 258-259 : « we return to Dihle's thesis about the biblical and theological origins of the concept of will. **That does not apply, however**, to what we found in Chrysippus's theory of assent, in Lucretius's and Seneca's discussions of *voluntas*, or in Epictetus's doctrine of *prohairesis* » ; p. 259 : « Dihle has documented in detail what we always suspected… **But there were other conditions as well.** » |
| 31 | `0a7b02a6` | Sorabji `opposes` Bobzien (origine du problème) | **conserver** (conf. 0,90) `relation_basis: propositional_conflict` | **L'audit est réfuté par l'imprimé.** Sorabji 1980, p. 246 : « **It misrepresents the situation to suggest that Aristotle was merely not yet in a position to appreciate the problem**; he would not have agreed that the problem was one for believers in voluntariness » (cibles listées p. 243 n. 1) ; p. 247 : « The new development was that Diodorus and the Stoics persisted in endorsing determinism in a context where many people, Aristotle included, had already become aware of the clash. » Contre Bobzien 1998b, p. 144 : « Aristotle's concept of what depends on us does not entail indeterminism… nor is he concerned with fate or causal determinism. » Désaccord frontal sur la charnière même de la thèse de la naissance tardive. |
| 32 | `af6d44fa` | Amand de Mendieta `opposes` Ramelli | **SUPPRIMER** | Confirmé, et renforcé : Ramelli **ne s'oppose pas** à Amand, elle s'appuie sur lui. Ramelli 2014, n. 88 : « See Amand 1945 » à l'appui de la réception par Origène de l'objection carnéadienne au fatalisme (l'ἀργὸς λόγος) ; *Fatalisme et liberté dans l'antiquité grecque* figure dans sa bibliographie. Les deux thèses portent sur des canaux de transmission différents et peuvent être vraies ensemble. |

### 1.b Triangle Kahn / Dihle / Frede (DAS-093) — niveau personne

Ces trois arêtes ne sont pas du lot g5 mais relèvent du même constat.

| edge_id | Arête | Verdict | Motif |
|---------|-------|---------|-------|
| `0494ed6b` | Dihle `agrees_with` Kahn | **SUPPRIMER** | Les Sather Lectures de Dihle datent de 1974, publiées en 1982 ; l'essai de Kahn est de 1988. Dihle ne peut pas être d'accord avec Kahn. C'est la moitié redondante de la paire symétrique signalée par l'audit, et celle qui remonte le temps. |
| `e9c1ce27` | Kahn `agrees_with` Dihle | **conserver + proposition** | Accord **partiel et sur une seule proposition** : « the concept of the will as we find it developed in Augustine and Aquinas presupposes biblical religious experience as one of its indispensable conditions » (Kahn 1988, p. 259). Le désaccord sur le brin païen est porté, séparément, par l'arête `9a26acd5` au niveau des positions. |
| `727f9c54` | Kahn `agrees_with` Frede | **conserver + proposition** `relation_basis: convergence` | Convergence de thèses ; Kahn 1988 précède Frede 2011. |

**La contradiction relevée par l'audit se dissout sans qu'on tranche pour
personne** : les cinq arêtes ne portaient pas sur la même proposition. Kahn
souscrit à la conclusion augustinienne de Dihle et dissent sur le brin stoïcien
— ce qu'il appelle lui-même « Major historical developments are always
overdetermined » (p. 259). Chaque arête porte désormais sa proposition.

### 1.c `supports` mal ciblés

| edge_id | Arête | Verdict | Motif |
|---------|-------|---------|-------|
| `24874839` | CAFMA V (futilité de la piété) `supports` *Niveaux de providence (proclienne)* | **SUPPRIMER** (DAS-098 confirmé) | Faux deux fois. Chronologiquement : l'argument moral carnéadien est du IIᵉ s. av. J.-C. (Amand 1945 ch. III ; rapporté en Eusèbe, *Prép. év.* VI.6.19, que ce nœud cite déjà) et ne peut soutenir une hiérarchie proclienne du Vᵉ s. ap. J.-C. Substantiellement : l'argument nie que la piété et la prière aient un sens sous le destin — il ne *soutient* aucune doctrine de la providence. Le reciblage proposé par l'audit est impossible : le graphe n'a pas de nœud pour la providence en général, seulement le nœud proclien ; en créer un relève d'une ingestion, pas d'une réparation. |

**Reportés, enregistrés dans `DEFERRED_SUPPORTS_FINDINGS` :** DAS-099 (Locke
`supports` `concept_autonomy`, dont la description est strictement l'αὐτονομία
politique grecque) et DAS-097 (Dihle `opposes` **la personne** Michael Frede).
Les deux exigent une décision curatoriale — élargir une définition de concept,
ou choisir le nœud canonique de la thèse de Dihle — que la famille de thèses
dupliquées (DAS-001) doit trancher d'abord.

### 1.d Découverte incidente : un nœud qui contredit son propre chercheur

`scholarly_position_sorabji_aristotle_indeterminist` affirmait que Sorabji
« did not have a doctrine of libertarian human agency » pour Aristote. **Sorabji
soutient l'inverse.** *Necessity, Cause and Blame* (1980), p. 139 : « In Chapter
Fourteen, I shall further deny that Aristotle's account of action is
deterministic » ; p. 242 : « my case against deterministic interpretations, by
denying that Aristotle's treatment of action is wholly deterministic… Aristotle
is an indeterminist in the sense defined in the Introduction, but not in the
more radical sense suggested by others » ; p. 232 n. 9 : « **In the very same
circumstances, the child could have acted in the other way.** »

Ce qu'il refuse à Aristote, ce n'est pas l'agentivité indéterminée mais la
machinerie libertarienne qu'on y attache d'ordinaire — les « fresh starts » de
Ross, Furley et Hardie, causes incausées et faculté de volonté (pp. 26 n. 1,
229). Il n'emploie jamais « free will » en son nom propre. La description est
réécrite, avec les pages en `attested_by`.

---

## Lot 2 — passages typés `passage` qui sont des synthèses éditoriales anglaises

### 2.a Le détecteur naïf et son taux de faux positifs

`docs/development/ingestion-rules.md` enregistre la dette ainsi : « ~2 774
passage nodes share a locus with another node (661 groups) ». C'est le décompte
des nœuds partageant la clé d'identité R2 `(cts_urn, passage_role)`. Re-mesuré
sur le graphe actuel : **436 groupes / 2 968 nœuds**.

**Échantillon de 30 groupes tirés au hasard (graine 2026), classés à la main :**

| Classe | Groupes | Ce que c'est réellement |
|--------|---------|-------------------------|
| **Vrai positif pur** (tous les membres = primaire + sa/ses synthèses) | **2** | Aristote *EN* III.10 (`_en_` / `_ne_`), Épictète *Diss.* IV.12.12 |
| **Vrai positif mixte** (une vraie paire + des intrus dus à l'URN) | **4** | Augustin *De lib. arb.* 1.12.25, 1.7.17, 1.5.11, 2.19.50 |
| **Faux positif** | **24** | voir ci-dessous |
| | | **Précision au niveau groupe : 6,7 % (pure) / 20,0 % (mixtes comprises)** |
| | | **Taux de faux positifs : 80,0 % — 93,3 % si les mixtes comptent comme échecs** |

**Les trois classes de faux positifs** — chacune est un *autre* défaut, que la
politique du lot 2 aggraverait :

1. **URN mal construite (11/30).** Des passages réellement différents sont
   forcés sur une seule URN. Augustin, *De libero arbitrio* est le pire cas :
   1.3.8, 2.3.8 et 3.3.8 portent tous
   `urn:cts:latinLit:stoa0040.stoa003:2.3.8`, l'URN ayant été bâtie sur le seul
   numéro de section, le livre perdu. La même forme produit les groupes
   géants : **les 1 335 passages de Plotin** portent
   `urn:cts:greekLit:tlg2000.tlg001.perseus-grc1:1`, les 258 de la *Consolatio*
   `urn:cts:latinLit:lat7127.011.perseus-lat1:1`, plus Méthode (97), Augustin
   *De nat. boni* (39), Plutarque *De fato* (38+16), Évodius (36), Augustin
   *Adv. Fulg.* (26). **Leur appliquer `citable_as_primary: false` aurait
   retiré de la citation la plus grande partie du corpus.**
2. **Double ingestion, les deux porteurs du texte primaire (8/30).** Sénèque,
   *De providentia* : `passage_sen_prov_1_3_14` et `passage_sen_prov_3_14`
   portent le **même** latin, l'un nu, l'autre préfixé « Latin : » sous un titre
   éditorial. Aucun n'est un résumé. Idem Boèce, *Consolatio*. Il faut
   dédoublonner, pas marquer un rôle.
3. **Double ingestion de traductions (7/30).** Épictète :
   `passage_epict_44_en` (extrait de phrases-clés) et `passage_epict_44_s44_en`
   (bloc plus long) sont deux traductions anglaises du même lieu ; il n'y a
   **aucun** jumeau primaire dans le groupe.
4. **URN grossière, pas un défaut (2/30).** Tatien, *Or. ad Gr.* 15.1, 15.2,
   15.3 partagent l'URN de chapitre `…perseus-grc1:15`, faute de sous-référence.
   Trois sections réellement différentes, correctement ingérées.

### 2.b Préconditions retenues et volume planifié

Sept préconditions, chacune motivée par une classe ci-dessus (détail dans
`LOT2_PRECONDITIONS`). Les deux décisives :

- **P4 — la synthèse doit CITER son primaire** : un fragment normalisé d'au
  moins 40 caractères de langue ancienne pris dans la synthèse doit être une
  sous-chaîne du primaire. C'est ce qui élimine la classe « URN mal
  construite » : un passage différent ne cite pas celui-ci.
- **P5 — la citation couvre au plus 50 % du primaire.** C'est ce qui élimine
  Sénèque et Boèce, dont la « synthèse » reproduit le primaire *intégralement*,
  ainsi que les nœuds bilingues de Plutarque.

**Volume planifié : 57 nœuds** (0 ambigu), tous vérifiés comme vrais positifs
sur un contrôle manuel de 12 d'entre eux :

| Préfixe synthèse | → primaire | n |
|---|---|---|
| `passage_aug_lib_arb_*` | `passage_aug_dla_*` | 33 |
| `passage_arist_en_*` | `passage_arist_ne_*` | 12 |
| `passage_ma_med_*` | `passage_marc_aur_*` | 7 |
| `passage_justin_1apol_*` | `passage_just_apol1_*` | 2 |
| `passage_plut_fat_N` | `passage_plut_fat_N_sN` | 2 |
| `passage_plotinus_enn_*` | `passage_plotinus_iv_*` | 1 |

Le détecteur est **rejoué à l'application** (jamais de liste figée), et
l'applier refuse de tourner si la population s'écarte de plus de 25 % de 57.

### 2.c Politique appliquée

Pas de fusion. Une synthèse est un objet éditorial réel ; ce qui change, c'est
qu'elle cesse d'être citable comme si elle était l'auteur antique :

- `passage_role: editorial_synthesis`
- `citable_as_primary: false`
- `metadata.primary_node_id` → le jumeau primaire
- `metadata.synthesis_of_urn` ← l'URN, retirée de `cts_urn` **parce que c'est
  elle qui crée la collision** ; le lieu reste résolvable par `primary_node_id`.
  Une URN qui ne crée pas de collision n'est pas touchée.
- `metadata.quote_coverage_of_primary` — la part du primaire effectivement citée.

Effet mesuré en bac à sable : `R2_duplicate_identity` passe de **2 987 à 2 909**.

### 2.d Dette explicitement transmise, non traitée ici

La ligne « ~2 774 nœuds » de `ingestion-rules.md` confond trois défauts. Ce que
cette vague **ne** touche **pas**, enregistré dans `LOT2_DEBT_HANDED_ON` :

| Défaut | Volume | Traitement requis |
|---|---|---|
| URN de travail partagée par tous les passages (`:1`, `:1.1`), ou livre perdu | ~2 600 nœuds | reconstruire l'URN depuis `canonical_ref` |
| Double ingestion du même texte primaire (Sénèque, Boèce) | ~150 nœuds | dédoublonner avec choix canonique |
| Extrait curaté + bloc complet, tous deux `translation` (Épictète) | ~120 nœuds | décider du canonique, ou créer un rôle « extrait » |

---

## Lot 3 — 44 passages de Tertullien à identité contradictoire

Les 44 nœuds portaient **deux** parents `part_of` : une œuvre juste et une
fausse. Deux amas, tous deux tranchés **par le texte**.

### 3.a Amas A — 13 nœuds : ni *Adversus Marcionem*, ni *De monogamia*

`passage_tert_adv_marc_1` … `_13` → **`passage_tert_exhort_cast_1` … `_13`**

- L'**id** et `canonical_ref` disaient *Adversus Marcionem* (« Adv. Marc. N »).
- Le **label**, posé par une vague antérieure, disait *De monogamia*.
- **Les deux sont faux.** Le texte est ***De exhortatione castitatis***.

Collation contre **Sources Chrétiennes 319** (sur disque,
`02_Corpus/SCO_brepols/Tertullianus/SCO_Tertullianus_De_exhortatione_castitatis_source.txt`) :
**11 des 13 incipits correspondent verbatim et dans l'ordre** après
normalisation accents / u-v / i-j ; les deux restants correspondent dès qu'on
admet une variante graphique dans la copie du graphe. Preuve structurelle
indépendante : *De exhortatione castitatis* a **treize** chapitres,
*De monogamia* dix-sept — et l'amas en compte exactement treize.

| ch. | Incipit dans le graphe | Position SC 319 |
|-----|------------------------|-----------------|
| 1 | « Non dubito, frater, te post uxorem in pace praemissam ad **conpositionem** animi conversum… » | I, 1 — SC lit *compositionem* (variante graphique) |
| 2 | « Quam denique modesta illa vox est: Dominus dedit, dominus abstulit… » | ✔ |
| 3 | « Quae enim in manifesto, scimus omnes, eaque ipsa qualiter in manifesto sint… » | ✔ |
| 4 | « Ceterum de secundo matrimonio scimus plane apostolum pronuntiasse… » | ✔ |
| 5 | « Ad legem semel nubendi dirigendam ipsa **erigo** humani generis patrocinatur… » | V, 1 — SC lit *origo* (corruption dans le graphe) |
| 6 | « Sed et benedicti, inquis, patriarchae non modo pluribus uxoribus… » | ✔ |
| 7 | « Cur autem de pristinis exemplis non ea potius agnoscamus… » | ✔ |
| 8 | « Liceat nunc denuo nubere, si omne quod licet bonum est… » | ✔ |
| 9 | « Si penitus sensus eius interpretemur, non aliud dicendum erit secundum matrimonium quam **species stupri** » | ✔ |
| 10 | « Renuntiemus carnalibus, ut aliquando spiritalia fructificemus… » | ✔ |
| 11 | « Duplex enim rubor est, quia in secundo matrimonio duae uxores eundem circumstant maritum… » | ✔ |
| 12 | « Scio, quibus causationibus coloremus insatiabilem carnis cupiditatem… » | ✔ |
| 13 | « Ad hanc meam **cohortationem**, frater dilectissime, accedunt etiam saecularia exempla… » | ✔ (chapitre final) |

Actions : création du nœud `work_tertullian_de_exhortatione_castitatis`
(+ son arête `authored_by` vers `person_tertullian_d220`, sans quoi R14 bloque),
reparentage des 13 passages, suppression des deux `part_of` faux, réécriture de
`canonical_ref`/`label`/`work_title`, renommage des ids et propagation.
Les deux variantes graphiques sont **signalées** (`text_collation_variants`),
**pas corrigées** : on ne réécrit pas de texte ancien.

### 3.b Amas B — 31 nœuds : *Adversus Praxean*, pas *De anima*

`passage_tert_de_anima_1` … `_31` → **`passage_tert_adv_prax_1` … `_31`**

- **Preuve négative décisive :** aucun des 31 incipits n'apparaît dans le
  *De anima* de Tertullien, collationné contre **SC 601** sur disque
  (`SCO_Tertullianus_De_anima_source.txt`) — **0/31**. Le *De anima* commence
  « De solo censu animae congressus Hermogeni… » ; ces passages commencent
  « Varie diabolus aemulatus est veritatem… ».
- **Preuve positive :** le contenu des 31 chapitres est une polémique
  monarchienne. Le ch. 2 énonce la thèse praxéenne elle-même : « post tempus
  pater natus **et pater passus**, ipse deus, dominus omnipotens, Iesus Christus
  praedicatur » ; les ch. 5-31 argumentent la distinction Père/Fils, le *sermo*
  et la *trinitas*. *Adversus Praxean* compte exactement 31 chapitres.
- Le **label** disait déjà « Adversus Praxean » : une vague antérieure avait vu
  juste, mais avait laissé derrière elle l'id, `canonical_ref`, `work_title` et
  `work_canonical_id`.

**Réserve enregistrée** (`text_collation_pending`) : aucune édition critique de
l'*Adversus Praxean* n'est sur disque — le fonds Brepols local a *De anima*,
*Adv. Marcionem* I-III, *Adv. Hermogenem*, *Adv. Valentinianos*,
*De exhortatione castitatis*, mais pas celle-ci. L'attribution repose sur la
preuve négative, le contenu et le compte de chapitres — solide, mais non
collationnée verbatim.

### 3.c Effets de bord traités et signalés

- `work_canonical_id` et `cts_urn` des 44 passages sont **effacés**, non
  re-devinés (conservés sous `*_removed_by_dialectical_repairs_2026_08_17`).
- Trois œuvres perdent tous leurs passages et sont marquées
  `needs_text_ingestion: true`, exactement comme
  `work_origen_exhortation_martyrdom` en vague 4 :
  `work_tertullian_de_anima` (SC 601 **est** sur disque et peut être ingéré),
  `work_tertullian_adv_marcionem` (livres I-III sur disque),
  `work_tertullian_de_monogamia`.
- Le renommage est propagé dans `nodes.jsonl`, `edges.jsonl` et
  `data/corpus/citations.jsonl` (31 + 13 références) **dans la même
  transaction**.
- **Signalé, non corrigé** (`TERTULLIAN_IDENTIFIER_CONFLICT`) :
  `work_tertullian_de_monogamia` porte `cts_urn: urn:cts:latinLit:stoa0275.stoa015`
  et `work_tertullian_adv_marcionem` porte le **même** identifiant en
  `work_canonical_id`. L'un des deux est faux (R2/R3b). Non tranché : inventer
  un numéro *stoa* est exactement ce que R5 et R10 existent pour empêcher.

---

## Lot 4 — R16, la porte dialectique

### 4.a Diff

`scripts/check_ingestion_rules.py` :

```python
EARLIER_SOURCE = {"influences", "teaches", "precedes"}
CHRONO_TOLERANCE = 60

+# Relations that assert one scholar's stance towards another's claim. R16 makes
+# these cite their evidence.
+DIALECTICAL_RELATIONS = {"opposes", "agrees_with", "critiques"}
```

```python
+    # ---- R16 a dialectical edge must cite its evidence --------------------
+    # Incident: every measured error in the graph's dialectical layer came from
+    # one batch. The 2026-08-16 audit sampled the COMPLETE populations of
+    # `opposes` (14) and `agrees_with` (13) and 30 of 177 `supports`, and found
+    # clear errors at 14.3% / 23.1% / 6.7%. All of them carried
+    # `provenance: g5_deep_2026_06_15`; none carried `attested_by`. Every edge
+    # that did carry `attested_by` was correct in the sample. Re-verification
+    # against the print later added a defect the audit had missed: an
+    # `agrees_with` pointing the wrong way — Salles 2005, pp. 78-81 argues
+    # AGAINST the Bobzien thesis he was recorded as agreeing with. An
+    # unattested dialectical edge is a claim about what a scholar thinks, made
+    # by nobody.
+    for e in gated_edges:
+        if e.get("relation") not in DIALECTICAL_RELATIONS:
+            continue
+        md = e.get("metadata") or {}
+        if isinstance(md, str):
+            try:
+                md = json.loads(md)
+            except json.JSONDecodeError:
+                md = {}
+        if not isinstance(md, dict):
+            md = {}
+        attested = md.get("attested_by")
+        if attested and (not isinstance(attested, (str, list)) or not attested):
+            attested = None
+        if attested:
+            continue
+        fail(
+            "R16_dialectic_unattested",
+            BLOCK if new_edges is not None else WARN,
+            e.get("edge_id", "?"),
+            f"{e.get('source')} -[{e.get('relation')}]-> {e.get('target')} carries no "
+            "metadata.attested_by: cite the page or locus that shows the relation holds, "
+            "or do not assert it",
+        )
```

`docs/development/ingestion-rules.md` : une ligne R16 au tableau des règles,
avec l'incident qui la motive (comme toutes les autres).

### 4.b Comportement mesuré

- **`--new-only` : BLOCK.** Toute nouvelle arête `opposes`/`agrees_with`/`critiques`
  sans `metadata.attested_by` arrête l'ingestion.
- **Graphe entier : WARN, 297 arêtes en dette** avant la vague, **275 après**
  (mesuré en bac à sable). L'écart correspond aux 3 arêtes dialectiques
  supprimées, aux 3 retypées hors du périmètre R16, et aux 15 désormais
  attestées ; les 2 arêtes signalées `unverified_g5` restent, à dessein, en
  dette — c'est ce qu'elles sont.
- `supports` n'entre **pas** dans R16. L'audit a mesuré 6,7 % d'erreur claire
  sur 30 des 177 `supports`, contre 14,3 % et 23,1 % pour `opposes` et
  `agrees_with`, et `supports` est largement employé entre un argument et un
  concept, où l'exigence de citation aurait un autre sens. À réévaluer quand la
  dette `supports` (177 arêtes, **0** justifiée) sera traitée.

---

## Ce que cette vague ne fait pas

- **Elle ne tranche aucun débat savant.** Là où deux chercheurs divergent, les
  deux positions restent et l'arête enregistre la proposition sur laquelle ils
  divergent. Le triangle Kahn/Dihle/Frede est résolu en *distinguant les
  propositions*, pas en supprimant un côté.
- **Elle ne génère ni grec ni latin.** Les deux variantes graphiques du
  *De exhortatione castitatis* sont signalées pour une collation, pas corrigées.
- **Elle n'invente aucun identifiant.** `work_canonical_id`, `cts_urn` et
  numéros *stoa* sont effacés ou laissés absents plutôt que devinés ; le nœud
  d'œuvre créé accepte un WARN R3b, enregistré.
- **Elle ne fusionne aucun nœud.** Ni les quatre nœuds Sharples 2008, ni les 57
  synthèses avec leur primaire.

## Suites à donner

1. **Créer un nœud pour la thèse de Brennan** sur l'origine du problème moderne
   (*The Stoic Life*, pp. 294-302) ; sans lui, le désaccord Brennan/Bobzien ne
   peut pas être porté au niveau des propositions.
2. **Acquérir Sorabji 2017**, « Freedom and Will: Graeco-Roman Origins »,
   pp. 49-66, pour lever le drapeau `unverified_g5` sur `d319ccd0`.
3. **Vérifier `9fba7de0`** (Brennan sur la réponse d'Origène à l'Argument
   paresseux) — supprimer ou attester.
4. **Reconstruire les URN** de la classe « URN mal construite » (~2 600 nœuds) :
   c'est le plus gros défaut de citabilité restant, et il est mécanique.
5. **Trancher `stoa0275.stoa015`** entre *De monogamia* et *Adversus Marcionem*
   contre le registre Perseus.
6. **Ingérer les trois œuvres vidées** depuis les éditions déjà sur disque
   (SC 601 pour le *De anima* ; Brepols I-III pour l'*Adversus Marcionem*).
7. **Traiter la dette `supports`** (177 arêtes, aucune justifiée) puis décider
   si R16 doit l'englober.
