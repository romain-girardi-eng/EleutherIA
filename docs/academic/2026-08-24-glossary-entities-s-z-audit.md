# Audit factuel du glossaire S-Z (entrees 19-27)

Date: 2026-08-24  
Portee: entrees 19 a 27 de `frontend/src/content/glossary.json`, de
`Liberum Arbitrium` a `Voluntas`.  
Mode: lecture seule; aucun edit du glossaire, du KG, du corpus, des registres
ou des manifestes.

## 1. Resultat executif

Le fichier audite est toujours byte-identique au SHA-256
`4bff80bc4173c44f3ef5f2cf2fad4c1fafc44d9a067891358614c0a1ce100dd6`.

| Entree | Terme | Verdict | Motif principal |
|---:|---|---|---|
| 19 | Liberum Arbitrium | **BLOCK** | Tertullien II.6.3 n'est pas le locus de l'equivalence grecque explicite; priorite non demontree |
| 20 | PAP | **BLOCK** | Frankfurt nomme et attaque un principe deja recu; le Consequence Argument ne defend pas PAP |
| 21 | Prohairesis | **REVISE** | choix transforme en capacite; definition et objet de la deliberation a resserrer |
| 22 | Providentia | **REVISE** | systematisation providence/fatum attribuee directement a Seneque |
| 23 | Summum Bonum | **REVISE** | noyau boecien juste; genealogie plotinienne non etablie par les loci cites |
| 24 | Synkatathesis | **REVISE** | Ciceron et Aulu-Gelle fusionnes en un mecanisme chrysippeen univoque |
| 25 | To Endechomenon | **BLOCK** | solution aristotelicienne disputee; modalite stoicienne faussement reduite a l'epistemique |
| 26 | Tyche | **REVISE** | locus `De Fato 89-100` faux et causalite accidentelle simplifiee |
| 27 | Voluntas | **REVISE** | histoire transperiodique et statut de faculte insuffisamment attribues |

Bilan: **0 approved, 6 revise, 3 block**.

## 2. Autorites et manifestations controlees

| Artefact | SHA-256 | Pages/loci controles | Usage |
|---|---|---|---|
| Corpus JSONL courant | `e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3` | Aristote EN III.2-3; Seneque; SVF; Boece routes | texte local, avec statut de chaque manifestation conserve |
| Origene, SC 268, extrait local | `a6ee091dee71829b7ca241eff50fa2b8786964ed3b0cf7c106f5277c82a2e0e5` | *De principiis* III.1 / *Philocalia* 21.1, grec 16/18, francais 17/19 | comparaison `autexousion` / Rufin |
| Frankfurt, *The Importance of What We Care About* | `a621de1bc43b36ad8e7a6d6335038c97edf694d4756ac543d48898f5f782425c` | chapitre 1, imprimees 1-2/PDF 13-14 et 6-8/PDF 18-20 | texte de 1969 repris en 1988; rendu visuel |
| van Inwagen, *An Essay on Free Will* | `17425130447fea86d59f20bd2007e3cb66cdf0d622649c87381cd1bbe23995e2` | imprimees 14-16/PDF 11; 162-164/PDF 85-86; 180-183/PDF 94-95 | Consequence Argument et traitement de Frankfurt/PAP; rendu visuel aux pages decisives |
| Long-Sedley, vol. 2 | `af6fc6f55d30f1896d59e2898e989016043990a498f8ff8cd5e8850bbb5e84a8` | sections 20, 33, 38, 55, 62 | assentiment, modalite, destin; lecture visuelle deja doublee aux loci prioritaires |
| Sharples, *Alexander De Fato* | `7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638` | imprimees 48-51/PDF 29-30; Bruns 172.17-174.28 | chance et causalite accidentelle; rendu visuel |
| Sorabji, *Necessity, Cause and Blame* | `be1f8fce483503d04504c73da30dc9bbcd52f5f8c04bd0e520cbd42fd4a3d500` | dossiers Aristote/Stoiciens deja page-mappes | controle secondaire attribue |
| Boece, XML Perseus | `264afebaca0d6ac351d8f185837ff1b28d19444af5ce37383b820382221d7f94` | *Consolatio* III.2-12 | souverain bien et beatitude |

Les rendus temporaires Frankfurt, van Inwagen et Sharples ont ete supprimes.
Les OCR, lorsqu'ils existaient, ont servi uniquement a la navigation.

Autorites web complementaires:

- [Tertullien, Adversus Marcionem II, texte Evans](https://www.tertullian.org/articles/evans_marc/evans_marc_05book2.htm);
- [Tertullien, De anima](https://tertullian.org/latin/de_anima.htm);
- [Ciceron, Tusculanae disputationes IV.12](https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Aabo%3Aphi%2C0474%2C049%3A4%3A12);
- [SEP, Diodorus Cronus](https://plato.stanford.edu/entries/diodorus-cronus/);
- [SEP, Medieval Theories of Future Contingents](https://plato.stanford.edu/entries/medieval-futcont/);
- [Scaife, Boethius, Consolatio](https://scaife.perseus.org/library/urn%3Acts%3AlatinLit%3Astoa0058.stoa001/).

## 3. Adjudication entree par entree

### 19. Liberum Arbitrium - BLOCK

Tertullien emploie bien le champ lexical de la liberte du choix dans
*Adversus Marcionem* II.5-7. En II.6.3 il parle d'un etre cree `liberi
arbitrii et suae potestatis`; ce passage n'est toutefois pas une traduction
d'un texte grec et n'y nomme pas `autexousion`. L'equivalence explicite entre
le grec et `libera arbitrii potestas` est *De anima* 21.6. L'entree confond donc
premiere attestation d'une famille latine, premier usage technique et traduction
explicite du grec.

Les choix de Rufin doivent etre cites par oeuvre et passage, puisque sa version
latine recompose parfois le grec d'Origene. Enfin la position anti-pelagienne
d'Augustin ne se resume pas a une capacite naturelle simplement `restricted`:
le libre choix demeure pertinent pour l'imputation, tandis que vouloir et agir
salutairement dependent de la grace qui guerit et libere.

Remplacement exact propose:

> Liberum arbitrium is a Latin family of expressions for free judgment or choice whose meaning changes across authors. Tertullian uses the language of arbitrii libertas and liberi arbitrii in Adversus Marcionem II.5-7; his explicit gloss of Greek autexousion as libera arbitrii potestas occurs instead at De anima 21.6. Rufinus frequently uses liberum arbitrium when translating Origen, but each equivalence must remain witness-specific rather than being treated as a single lexical event. Augustine gives the phrase a major role in responsibility and grace; in his anti-Pelagian works free choice remains imputable, while salvific willing and action require healing and liberating grace.

Champ `period` propose: `Patristic` plutot que `Medieval` seul.

### 20. Principle of Alternative Possibilities - BLOCK

Frankfurt n'introduit pas PAP comme une doctrine personnelle. La premiere page
de son article de 1969 dit qu'il appellera ainsi un principe deja dominant et
largement tenu pour vrai, puis annonce qu'il est faux. Il en donne la formule
canonique et construit ses contre-exemples; il ne faut donc pas ecrire qu'il l'a
`formulated` sans cette distinction historique.

La faute la plus importante concerne van Inwagen. Le Consequence Argument,
presente pp. 14-15, defend l'incompatibilite du determinisme et du libre arbitre;
il ne defend pas PAP. Au chapitre V, pp. 162-163 et suivantes, van Inwagen
accepte la force des contre-exemples de Frankfurt contre PAP et cherche d'autres
principes pour relier responsabilite et libre arbitre.

Remplacement exact propose:

> The Principle of Alternate Possibilities says that moral responsibility for an action requires the ability to have done otherwise. Frankfurt's 1969 article names and states this already influential principle in order to reject it, using cases in which an inactive counterfactual intervener would have ensured the same result. Van Inwagen's Consequence Argument supports incompatibilism between determinism and free will, not PAP; in An Essay on Free Will chapter V he accepts Frankfurt-style counterexamples to PAP and develops different principles connecting responsibility with freedom. Fischer and Ravizza later defend semicompatibilism through reasons-responsive guidance control, which does not require access to alternatives.

### 21. Prohairesis - REVISE

`Prohairesis` est d'abord un choix ou une decision deliberee, non une `capacity`
separee. EN III.2 etablit qu'elle est volontaire mais plus etroite que le
volontaire; enfants et animaux participent au second, non a la premiere. La
definition `deliberative desire of things up to us` appartient exactement a
EN III.3, 1113a10-11. Aristote delibere sur `ta pros ta tele`, les choses qui
conduisent aux fins, formulation plus precise que le raccourci moderne `means`.

La ligne grecque locale EN III.3, passage
`aa06ed04-ba9d-4a55-9701-3f8826c977d5`, a le SHA-256 NFC
`5ca72c9777869892adbc33932e43a2b66ea210db1723bbfde9b93553f020de29`.

Remplacement exact propose:

> Prohairesis is Aristotle's term for deliberate choice or decision. Nicomachean Ethics III.2 distinguishes it from the broader voluntary: children and non-rational animals act voluntarily but do not exercise prohairesis. At III.3, 1113a10-11, Aristotle characterizes choice as deliberative desire concerning things up to us; deliberation concerns the things that contribute toward an end, not the end itself. Prohairesis therefore joins desire and deliberative reasoning and is especially revealing of character, without being a separately named faculty.

### 22. Providentia - REVISE

Le noyau de *De providentia* est correct. Seneque affirme un ordre cosmique,
compare Dieu a un pere exigeant, soutient que les adversites exterieures ne sont
pas de vrais maux pour l'homme bon et reserve le mal moral aux vices. Mais la
distinction nette `providence = rational ordering / fate = causal execution` est
une schematisation moderne du stoicisme, non une definition formulee ainsi par
Seneque. *De providentia* 5.7-8 relie bien les causes en chaine et le destin,
sans offrir cette paire terminologique abstraite.

Remplacement exact propose:

> In Seneca's De providentia, providentia is the rational divine governance invoked to explain why apparent adversities befall good people. Seneca compares divine care to a demanding father's training, argues that external hardships do not constitute moral evil for a good person, and reserves genuine evil for vice. In 5.7-8 he also describes fate as an ordered chain of causes binding human and divine events. Treating providence as the plan and fate as its execution is a useful modern Stoic synthesis, not Seneca's explicit definition in this treatise.

### 23. Summum Bonum - REVISE

Le raisonnement principal de *Consolatio* III.2-12 est solide: les biens
partiels ne suffisent pas, la beatitude parfaite ne manque de rien, le souverain
bien est identifie a Dieu. En revanche, l'entree transforme un contexte
neoplatonicien plausible en genealogie textuelle directe depuis l'Un plotinien,
avec descente dans la multiplicite et retour par la philosophie. Les loci cites
ne demontrent pas cette chaine. Le metre III.9 invoque plus directement le
*Timee* et l'ordonnancement cosmique.

Remplacement exact propose:

> In Boethius's Consolation III, the supreme Good is the unified and self-sufficient good sought through every partial good, and perfect happiness is participation in or attainment of that Good. Wealth, honour, power, fame, and pleasure fail when treated separately because none supplies the complete state that lacks nothing. In III.10 Boethius identifies perfect happiness and the highest Good with God. The argument belongs to a late antique Platonist context, but a specific derivation from Plotinus's One and a descent-return scheme requires separate evidence.

### 24. Synkatathesis - REVISE

L'assentiment a une impression est bien central dans la psychologie stoicienne
de l'action. Mais l'entree fusionne deux transmissions. Ciceron, *De fato*
39-43 (LS 62C, imprimees 383-384/PDF 391-392), distingue la cause antecedente
proche de la cause complete ou principale et dit l'assentiment dans notre
pouvoir. Aulu-Gelle 7.2.6-13 (LS 62D, 384-385/PDF 392-393) rattache le mouvement
a la constitution de l'agent et transmet l'analogie du cylindre. Aucun de ces
passages, pris seul, ne formule tout le mecanisme moderne ni ne demontre son
succes moral.

Remplacement exact propose:

> Synkatathesis is the Stoic act of assenting to an impression and is central to Stoic accounts of rational action. Cicero, De fato 39-43, distinguishes the external antecedent condition from a complete or principal causal role and places assent in our power; Aulus Gellius 7.2.6-13 separately transmits the cylinder analogy and appeals to the agent's constitution. These sources help explain how fated impressions and agent-dependent assent were distinguished, but the modal and moral success of the resulting modern “compatibilist” reconstruction remains disputed.

### 25. To Endechomenon - BLOCK

L'entree presente comme acquise une lecture contestee de *De interpretatione*
9. Aristote montre les consequences fatalistes d'une necessitation des enonces
sur les futurs singuliers et donne une reponse notoirement ambigue en 19a23-39;
il n'est pas acquis qu'il nie simplement toute verite ou faussete determinee a
l'avance. `Endechomenon` et `dynaton` ont en outre plusieurs usages selon les
traites.

Diodore Cronos restreint bien le possible a ce qui est ou sera vrai, mais il ne
faut pas attribuer ce systeme a tous les Megariques. Surtout, la Stoa n'accepte
pas seulement une contingence epistemique: la reconstruction de la modalite
chrysippeenne permet que des evenements soient a la fois fates, possibles et non
necessaires. Enfin le clinamen epicurien ouvre une indetermination physique dans
certains temoignages; il n'est ni la definition generale du contingent ni une
cause suffisante et verifiee de l'action libre.

Remplacement exact propose:

> Aristotle uses endechomenon and related modal vocabulary in context-dependent ways for what can be or can be otherwise. In De interpretatione 9 he rejects the inference from statements about singular future events to the necessity of those events, but the exact status he gives their present truth values is disputed. Diodorus Cronus's Master Argument supports his restrictive account of possibility; this should not be generalized to every Dialectician or Megarian. Chrysippean modality does not reduce contingency to ignorance, since its categories can treat some fated events as possible and non-necessary. Alexander later defends two-way contingency against determinism, while the Epicurean swerve belongs to a separate and disputed physical argument.

### 26. Tyche - REVISE

Le locus actuel `De Fato 89-100` est faux. Le dossier est *De fato* VIII,
Bruns 172.17-174.28, traduction Sharples imprimees 48-51/PDF 29-30. Alexandre
decrit un resultat inattendu qui survient a une action poursuivant une autre fin:
trouver un tresor en creusant pour autre chose, ou rencontrer un debiteur au
marche. Il parle d'absence de cause `per se` et de cause `per accidens`, puis
precise que creuser ou aller au marche sont des conditions causales claires mais
ni propres ni principales relativement au resultat fortuit. `Lack primary
causation` doit donc rester qualifie, et les exemples sont herites du dossier
aristotelicien de *Physique* II.4-6.

Remplacement exact propose:

> In De fato VIII (Bruns 172.17-174.28), Alexander describes luck and the fortuitous as unexpected outcomes that supervene on actions directed toward other ends. Digging may accidentally result in finding treasure, and going to the marketplace for another purpose may result in collecting a debt. The prior action is a clear causal condition of the result but not its proper or primary cause; Alexander therefore contrasts per se and per accidens causation rather than making chance wholly uncaused. Such outcomes occur rarely relative to the regular results of prior activities, in an account indebted to Aristotle, Physics II.4-6.

### 27. Voluntas - REVISE

Ciceron *Tusculanes* IV.12 propose explicitement `voluntas` pour la `boulesis`
stoicienne, definie dans ce contexte comme une aspiration conforme a la raison
et reservee au sage. Cela n'etablit pas une equivalence intemporelle entre tout
usage latin de `voluntas` et la `boulesis`, ni une faculte distincte.

Les usages moraux de Seneque et le statut augustinien doivent rester des lectures
attribuees. La these d'une invention augustinienne de la faculte de volonte est
precisement contestee par les historiens modernes; elle ne peut servir de
description neutre. Le champ `period: Medieval` date enfin trop tard une entree
qui commence avec Ciceron et Seneque et traverse l'Antiquite tardive.

Remplacement exact propose:

> Voluntas is a Latin term whose meanings range across wish, intention, consent, and willing. In Tusculan Disputations IV.12 Cicero proposes voluntas as the Latin rendering of the Stoic boulēsis in that specific taxonomy: a rational aspiration attributed to the sage. Seneca gives voluntas important moral uses, but whether these amount to a distinct faculty should remain a scholarly interpretation. Augustine makes voluntas and liberum arbitrium central to responsibility, sin, and grace; whether this is an invention of “the will” or a transformation of Greek and Stoic materials is the disputed question addressed differently by Dihle and Frede.

Champ `period` propose: `Roman / Late Antique / Medieval` ou `Cross-period Latin`.

## 4. Gaps fail-closed et plan de correction

1. Bloquer les entrees 19, 20 et 25 jusqu'au remplacement complet de leur
   definition; leurs erreurs portent sur les ancres historiques centrales.
2. Appliquer les six remplacements `REVISE` sans promouvoir les analogies en
   genealogies directes.
3. Conserver separement auteur doctrinal, transmetteur antique et reconstruction
   moderne pour les entrees stoiciennes 24-25.
4. Pour les PDF proteges Frankfurt, van Inwagen, Long-Sedley, Sharples et
   Sorabji, ne conserver dans le produit que les paraphrases, loci et hashes.
5. Apres une future edition du JSON, revalider la syntaxe, les IDs lies, le rendu
   UI et le nouveau hash; ne propager aucune correction au KG ou au registre sans
   transaction separee.

Etat final: aucun edit de `glossary.json` et aucun data write pendant cet audit.
