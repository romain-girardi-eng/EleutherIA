# Audit factuel du glossaire J-R (entrees 10-18)

Date: 2026-08-24  
Portee: entrees 10 a 18 de `frontend/src/content/glossary.json`, de
`Divine Prescience` a `Libertas Spontaneitatis`.  
Mode: lecture seule des donnees; rendus PDF temporaires uniquement; aucun edit du
glossaire, du KG, du corpus, des registres ou des manifestes.

## 1. Resultat executif

Le fichier audite a le SHA-256
`4bff80bc4173c44f3ef5f2cf2fad4c1fafc44d9a067891358614c0a1ce100dd6`.

| Entree | Terme | Verdict | Motif principal |
|---:|---|---|---|
| 10 | Divine Prescience | **BLOCK** | faux locus/verbatim Origen; `nunc stans` presente comme formule de Boece |
| 11 | Eph' Hemin | **REVISE** | lecture bilaterale et controle rationnel transformes en definition non disputee |
| 12 | Exercitatio | **REVISE** | theme reifie en doctrine; numerotation Seneca dependante de l'edition |
| 13 | Fortuna | **REVISE** | confusion legere entre Fortuna, hasard technique et gouvernement providentiel |
| 14 | Hegemonikon | **REVISE** | rationalite humaine et `inner citadel` sur-generalisees |
| 15 | Heimarmene | **REVISE** | periode fausse et definition de SVF II.1000 attribuee a SVF II.916 |
| 16 | Hekousion | **APPROVED** | definition et distinctions conformes aux loci aristoteliciens |
| 17 | Libertas Indifferentiae | **BLOCK** | la Quatrieme Meditation est renversee: Descartes dit le degre le plus bas |
| 18 | Libertas Spontaneitatis | **REVISE** | categorie moderne projetee comme genealogie antique directe |

Bilan: **1 approved, 6 revise, 2 block**. Les remplacements ci-dessous sont des
paraphrases originales, sans reprise longue de texte protege.

## 2. Autorites et manifestations controlees

| Artefact | SHA-256 | Pages/loci controles | Usage |
|---|---|---|---|
| Corpus JSONL courant | `e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3` | Aristote EN III.1, III.2, III.5; Seneque; SVF II.916/1000 | texte primaire local ou route de controle, selon le statut de chaque ligne |
| Long-Sedley, vol. 2 | `af6fc6f55d30f1896d59e2898e989016043990a498f8ff8cd5e8850bbb5e84a8` | imprimees 314, 337, 340-341, 383-385; PDF 322, 345, 348-349, 391-393 | dossiers stoiciens; rendu visuel |
| Sharples, *Alexander De Fato* | `7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638` | traduction imprimee 80-81/PDF 45; commentaire 164-165/PDF 87 | Alexandre, *De fato* 30; rendu visuel |
| OCR Sharples | `ec154e4d3607f887299ac3faf6ec1853b0a4da117eaa464d70331d7c55727ebb` | navigation seulement | jamais autorite visuelle |
| TEI Alexandre, *De fato* | `184b01f38061cfa00b276ed8d9580f3f842f564856851e4bcc124adcc2edbb2f` | Bruns 200.12-201.30 | texte grec structure local |
| Sytsma, dissertation Origen | `23aec043358f2f192fb959ae3f5cd3918b6d6095092040d34b5f7d967f3cc6c4` | imprimees 193, 217; PDF 202, 226 | controle secondaire et routage vers les primaires |
| Sorabji, *Necessity, Cause and Blame* | `be1f8fce483503d04504c73da30dc9bbcd52f5f8c04bd0e520cbd42fd4a3d500` | imprimees 80-86, 228-238; PDF 97-103, 245-255 | lectures stoiciennes et aristoteliciennes attribuees |
| Hadot, *La citadelle interieure* | `840f49723ee69b36019207aa6dd8d0e829adc4f4f94fb2b00ab39e09f5d4af32` | imprimees 136-137/PDF 68 | statut moderne de l'etiquette `inner citadel`; rendu visuel |
| Bobzien 1998, article Phronesis | `7afa65d208b9213aa90b0525c8b9d240d71804cf7863db4d8aac9ae395b3bbf9` | imprimees 139-145/PDF 7-13 | distinction causative/potestative et EN III.5; rendu visuel |
| Boece, XML Perseus | `264afebaca0d6ac351d8f185837ff1b28d19444af5ce37383b820382221d7f94` | *Consolatio* II.2, III.10, V.6 | texte latin structure local |

Les pages Long-Sedley 345, 392 et 393 ont ete rendues a nouveau; les pages
decisives Sharples, Sorabji, Hadot et Bobzien ont egalement ete controlees
visuellement. Tous les rendus temporaires ont ete supprimes ou places dans la
Corbeille. `qpdf` n'a signale aucun defaut sur les PDF locaux utilises.

Autorites web complementaires:

- [PTA/BBAW, Origen, De oratione](https://pta.bbaw.de/en/reader/pta0007.pta008.pta-grc1);
- [Perseus, Seneca, De providentia](https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A2007.01.0012%3Abook%3D1);
- [Scaife, Boethius, Consolatio](https://scaife.perseus.org/library/urn%3Acts%3AlatinLit%3Astoa0058.stoa001/);
- [Hume Texts Online, Treatise 2.3.2](https://davidhume.org/texts/t/2/3/2);
- [Descartes, Quatrieme Meditation](https://fr.wikisource.org/wiki/M%C3%A9ditations_m%C3%A9taphysiques/M%C3%A9ditation_quatri%C3%A8me);
- [SEP, Descartes' Ethics](https://plato.stanford.edu/entries/descartes-ethics/);
- [SEP, Hume on Free Will](https://plato.stanford.edu/entries/hume-freewill/).

## 3. Adjudication entree par entree

### 10. Divine Prescience - BLOCK

Le probleme general est correctement identifie, mais trois precisions centrales
sont impropres a la publication en l'etat.

1. La phrase anglaise mise entre guillemets n'est pas *De oratione* 6.2.
   *De oratione* 6.3, GCS Orig. 2 p. 313, soutient bien que la prescience
   divine ne cause pas les futurs issus du `eph' hemin`, mais avec une autre
   formulation. La formule latine correspondant directement au verbatim est
   transmise par Rufin dans *Commentaire sur Romains* VII.6.5, SC 543 p. 318
   latin/319 francais. Le syntagme grec court correspondant est *Philocalia*
   25.3, SC 226 p. 226 grec/227 francais, et non *De oratione* 6.2. Le grec du
   passage rufinien est perdu et ne doit pas etre retroverti.
2. Alexandre, *De fato* 30, autorise hypothetquement une connaissance des
   contingents comme contingents. Le commentaire de Sharples avertit que cette
   connaissance peut seulement porter sur la capacite bilaterale, non sur
   l'option qui sera effectivement choisie.
3. Boece, *Consolatio* V.6, emploie `tota simul` et decrit un etat de presence
   immobile. `Nunc stans` est un raccourci scolastique posterieur, pas le
   libelle de la *Consolatio*.

Remplacement exact propose:

> Divine prescience (prognosis / praescientia) is divine knowledge of future events, including acts attributed to human choice, and raises the question whether infallible knowledge makes those events necessary. In De fato 30 Alexander argues, hypothetically, that foreknowledge can track contingent things without converting them into necessities; this need not include definite knowledge of which option an agent will choose. Origen, De oratione 6.3, argues that divine foreknowledge is not the cause of future acts arising from what is up to us; the converse-causation formula should instead be cited witness-specifically to Rufinus, Commentary on Romans VII.6.5, or to the Greek parallel at Philocalia 25.3. In Consolation V.6 Boethius treats all times as present to divine intelligence and distinguishes an event's own modality from the conditional necessity of its being known; “nunc stans” is later shorthand, not Boethius's wording there.

### 11. Eph' Hemin - REVISE

Le noyau aristotelicien est reel: EN III.5, 1113b6-14, relie vertu et vice a ce
qui depend de nous et formule une reciprocite entre agir et ne pas agir;
1114a-b relie ensuite le caractere aux conduites volontaires anterieures. Mais
la definition actuelle fusionne comme implications necessaires l'alternative,
l'origine interne et le controle rationnel. Elle gomme ainsi la controverse
modale et importe dans `eph' hemin` des criteres appartenant aussi au volontaire
et a la deliberation.

Bobzien 1998, pp. 139-145, analyse l'usage aristotelicien comme bilateral a un
niveau generique tout en precisant qu'il n'entraine, a lui seul, ni determinisme
ni indeterminisme. Sa distinction entre lecture causative unilaterale et lecture
potestative bilaterale doit rester une reconstruction attribuee. Le locus grec
local 1113b7-8 a le SHA-256 NFC
`79d48db2ff6d48f90778c18952aab781242e11d2b4c4cd5914e179a66d61c347`.

Remplacement exact propose:

> To eph' hemin (to eph' hemin, what is up to us) marks the range of actions that Aristotle connects with deliberation, voluntary action, praise, and blame. In Nicomachean Ethics III.5, 1113b6-14, he states that virtue and vice are up to us and gives a reciprocal relation between acting and not acting; 1114a-b then connects responsibility for character with earlier voluntary conduct. This does not by itself establish causally undetermined alternatives. Bobzien analyses Aristotle's usage as two-sided at a generic level while stressing that it entails neither determinism nor indeterminism, and contrasts it with a one-sided causative reconstruction of Stoic usage.

### 12. Exercitatio - REVISE

L'argument est correctement decrit, mais `exercitatio` doit designer ici un
theme de *De providentia*, non une doctrine stoicienne officielle et univoque.
Seneque presente l'adversite apparente comme entrainant, eprouvant et manifestant
la vertu; il ne transforme pas pour autant tout dommage apparent en bien.

La numerotation varie selon les editions. La maxime sur la vertu sans adversaire
est 2.4 chez Reynolds/Basore mais se rattache a 2.3 dans la segmentation
Perseus/CTS. La comparaison du feu et de l'or clot 5.9 chez Reynolds mais est
rattachee a 5.10 dans Perseus/CTS et d'autres editions. Un locus nu donne donc
une fausse precision.

Remplacement exact propose:

> Exercitatio designates Seneca's argument in De providentia 2-5 that apparent adversity can train, test, and display the virtue of a good person rather than constitute a genuine moral evil. Seneca develops the point through athletic competition, paternal discipline, military service, and the distinction between what one undergoes and how one bears it. The two quoted maxims should be located as De providentia 2.3-4 and 5.9-10 unless a specific edition and its paragraph segmentation are named.

### 13. Fortuna - REVISE

La roue, la mutabilite des biens exterieurs et l'identification du souverain bien
a Dieu sont correctes. Deux distinctions suffisent: la Fortuna personnifiee du
livre II n'est pas le `casus` techniquement analyse en V.1, et sa roue represente
les renversements des conditions mondaines sans etre l'ultime gouvernement du
monde, attribue a la providence.

Remplacement exact propose:

> In Book II of Boethius's Consolation, Fortuna personifies worldly instability and reversals of prosperity and adversity; she is not identical with the technical account of chance (casus) in V.1. Her wheel represents the rise and fall of external conditions, and riches, honours, and power are revocable loans rather than secure possessions. Philosophy argues that mutable externals cannot constitute beatitudo, while III.10 identifies perfect happiness and the highest Good with God.

### 14. Hegemonikon - REVISE

Le dossier fonctionnel est solide: Aetius 4.21.1, repris en LS 53H p. 314/PDF
322, place impressions, assentiments, sensations, impulsions et raisonnement
dans le `hegemonikon`; Diogene Laerce 7.159 confirme plusieurs de ces fonctions.
Mais les animaux non rationnels possedent eux aussi un `hegemonikon` dans la
psychologie stoicienne: chez l'humain, c'est sa forme rationnelle qui importe.

Marc Aurele VIII.48 dit que le principe directeur peut se recueillir en lui-meme
et compare une pensee liberee des passions a une citadelle; IV.3 recommande
separement un retrait en soi. `Inner citadel` est la synthese moderne de Hadot,
non une locution technique de Marc Aurele. L'ancre plus directe pour ce qui
depend de nous est VIII.7.

Remplacement exact propose:

> The hegemonikon is the Stoic commanding faculty, the chief part of the soul in which impressions, assent, sensation, impulses, and reasoning are coordinated. In human beings it is rational and therefore central to responsible agency, but Stoic accounts also assign a hegemonikon to non-rational animals. Marcus Aurelius VIII.48 says that the ruling faculty can gather into itself and compares a mind free from passions to a citadel; IV.3 separately recommends retreat into one's own soul. “Inner citadel” is Hadot's modern synthesis, while Marcus's explicit restriction of desire and aversion to what is up to us is better anchored at VIII.7.

### 15. Heimarmene - REVISE

La doctrine vise Chrysippe et la Stoa hellenistique; `period: Roman Imperial`
date les transmetteurs plutot que le concept et doit devenir `Hellenistic`.

Surtout, la formulation de l'ordre naturel et inviolable imprimee dans la
definition est transmise par Aulu-Gelle 7.2.3 et classee SVF II.1000, non SVF
II.916. Le fragment 916, transmis par Theodoret et Aetius/Stobee, parle plutot
d'un mouvement eternel, continu et ordonne et rapproche destin et necessite.
Les lignes locales distinctes confirment que les deux numeros ne sont pas
interchangeables.

La responsabilite doit aussi rester multi-temoin: Ciceron *De fato* 39-43
distingue des roles causaux; Aulu-Gelle 7.2.6-13 fait intervenir la constitution
de l'agent; Ciceron 28-30 transmet les co-destines. Ces elements n'etablissent
pas un compatibilisme stoicien unique ni une justification incontestee du blame.

Remplacement exact propose:

> Heimarmene (fate) names the Stoic order that links events in an everlasting causal sequence governed by divine reason. Chrysippus's definition as a natural and inviolable ordering of the whole is transmitted by Aulus Gellius, Noctes Atticae 7.2.3 (= SVF II.1000), not SVF II.916. Stoic attempts to preserve responsibility are transmitted through different arguments: Cicero distinguishes causal roles, Gellius appeals to the agent's constitution, and Cicero also reports co-fated outcomes. Whether these materials amount to a successful or unified compatibilism remains disputed.

Champ `period` propose: `Hellenistic`.

### 16. Hekousion - APPROVED

La definition correspond a EN III.1, 1111a22-24: origine dans l'agent et
connaissance des circonstances particulieres. Le lien avec louange et blame
vient de 1109b30-35. EN III.2, 1111b6-10, confirme que le volontaire est plus
large que la `prohairesis`, puisque les enfants et les autres animaux partagent
le premier sans partager la seconde.

Le locus grec local 1111a22-24, passage
`61f93a32-769e-498b-968d-de545a9bd124`, a le SHA-256 NFC
`899abcaca2ccb8617e66c086d58ce175a01c834944effccb318617b34ed58d92`.
Le texte actuel peut etre conserve. Une precision facultative pourrait rappeler
que la simple ignorance ne suffit pas toujours a l'excuse: Aristote distingue
l'acte commis par ignorance et l'acte dont l'agent regrette les consequences.

### 17. Libertas Indifferentiae - BLOCK

L'attribution a Descartes inverse le texte primaire. Dans la Quatrieme
Meditation, AT VII 57-58, l'indifference due a l'absence de raison est le degre
le plus bas de la liberte et marque un manque de connaissance; une connaissance
plus claire accroit la liberte. Les lettres a Mesland de 1644-1645 compliquent
ensuite le tableau en distinguant indifference negative et puissance positive
de se determiner, mais elles ne transforment pas la formule de la Meditation en
`highest degree`.

La definition actuelle assimile en outre toute `libertas indifferentiae` a une
decision sans raisons ni caractere, alors que l'histoire du terme distingue
absence d'inclination, non-necessitation et puissance bilaterale. Les references
a Scot et au paradoxe traditionnellement associe a Buridan doivent etre
presentees comme antecedents reconstruits, non comme occurrences du meme terme.

Remplacement exact propose:

> Liberty of indifference is a family of later scholastic and early modern views on a will that is not necessitated to one alternative; it should not be defined uniformly as choice without reasons. Medieval accounts of synchronic contingency may be treated as antecedents only with explicit attribution. In the Fourth Meditation (AT VII 57-58), Descartes calls reasonless indifference the lowest grade of freedom, while his later correspondence with Mesland distinguishes this negative state from a positive two-way power of the will. Descartes therefore cannot be cited as endorsing indifference as the highest degree of freedom.

### 18. Libertas Spontaneitatis - REVISE

Le noyau correspond a la distinction scolaire attestee chez Hume,
*Treatise* 2.3.2.1/SBN 407-408: liberte de spontaneite opposee a la violence,
par contraste avec liberte d'indifference comprise comme negation de necessite
et de causes. *Enquiry* 8.23 definit ensuite une liberte hypothetique d'agir ou
de ne pas agir selon la determination de la volonte. Cela soutient un modele
compatibiliste classique, mais non une definition transhistorique unique.

L'`hekousion` aristotelicien offre une analogie structurelle; il n'atteste pas le
latin `libertas spontaneitatis`. De meme, la causalite de l'assentiment stoicien
ne doit pas etre presentee comme une adaptation historique directe sans source.
Enfin Leibniz, *Theodicee* 288, ne reduit pas la liberte a la spontaneite: il lui
joint intelligence et contingence.

Remplacement exact propose:

> Liberty of spontaneity is the school distinction, explicitly reported by Hume in Treatise 2.3.2.1, for freedom to act according to one's will without external violence or obstruction; it contrasts with liberty of indifference understood there as absence of necessity and causes. This form of freedom can be compatible with causal determination, but different early modern authors add different conditions. Aristotle's hekousion and Stoic accounts of assent are useful structural comparisons, not attestations of the Latin term or proof of a direct historical adaptation.

## 4. Gaps fail-closed et plan de correction

1. Remplacer integralement les entrees 10 et 17 avant toute publication; ne pas
   corriger seulement leur locus ou un adjectif.
2. Appliquer les six remplacements `REVISE` tels quels ou avec une redaction
   semantiquement equivalente, puis faire relire les liens `relatedIds` sans en
   deduire de nouvelles genealogies.
3. Conserver l'entree 16; ajouter seulement les loci si le schema du glossaire
   accepte un champ de provenance.
4. Ne pas recopier dans le glossaire le record local *Philocalia* 25.2 comme
   temoin grec: cette ligne contient une traduction francaise concatenee,
   `content_kind=modern_translation`, et reste `needs_text_ingestion=true`.
   Pour la formule grecque courte d'Origene, la route sure est SC 226,
   *Philocalia* 25.3, p. 226-227.
5. Conserver les distinctions de manifestation: OCR Sharples navigation-only;
   Long-Sedley vol. 2 preuve editoriale secondaire; Bobzien 1998 source moderne;
   textes antiques recoles par leur transmetteur et leur locus.
6. Apres edition future du JSON, revalider syntaxe, IDs/`relatedIds`, rendu UI et
   hash du fichier. Cet audit n'autorise aucun changement KG ou registre.

Etat final de ce travail: `glossary.json` est reste byte-identique au hash de la
section 1; aucun data write n'a ete effectue.
