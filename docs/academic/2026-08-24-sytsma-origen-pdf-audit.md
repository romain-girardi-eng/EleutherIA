# Audit PDF integral - Sytsma 2018 sur Origene, liberte et providence

Date : 2026-08-24  
Mode : lecture savante et audit visuel en lecture seule  
Artefact : `data/literature_acquisition/sytsma_2018_dissertation_origen.pdf`  
Statut : **audit secondaire complet, aucune verification primaire antique**

## Verdict executif

Le fichier local est un PDF complet, lisible et continu de la dissertation de Lee W. Sytsma, soutenue a Marquette University en 2018. Les 262 pages PDF ont ete rendues et inspectees visuellement. La pagination arabe est stable : `page PDF = page imprimee + 9`, de la page imprimee 1 a 253. Le fichier permet donc de verifier exactement ce que Sytsma soutient et ou il le soutient.

Il ne permet pas, a lui seul, de verifier les textes antiques que Sytsma cite. Cette limite est decisive parce que son argument principal est une reconstruction moderne. Sytsma reconnait qu'aucun passage conserve d'Origene n'enonce directement les trois types de prescience ni la preselection par Dieu d'une unique suite de choix libres conduisant a l'apocatastase. Les textes antiques qu'il rassemble soutiennent des briques distinctes ; leur combinaison en une theorie de type « middle knowledge » est sa these.

Trois blockers P0 ressortent de la comparaison avec le depot :

1. Le manifeste d'acquisition local attribue le PDF a `David Sytsma` et lui donne un titre qui n'apparait pas dans le document. L'auteur visible est **Lee W. Sytsma** et le titre exact est **Reconciling Universal Salvation and Freedom of Choice in Origen of Alexandria**.
2. Les douze arguments Sytsma du KG sont attaches au livre Gorgias 2020, alors que toutes les pages ont ete verifiees dans la dissertation 2018. La dissertation et la monographie doivent redevenir deux publications/manifestations distinctes.
3. Les douze arguments portent tous un statut generique `citation_verified: true`; 24 citations les relient a 12 passages antiques, dont plusieurs traductions francaises sous identite `_grc`, faux CTS `tlg2042.tlg028`, notes editoriales mixtes ou duplications de granularite. L'issue critique Origene deja ouverte doit rester **OPEN**.

Conclusion de publication : la dissertation peut etre enregistree comme source secondaire integralement lue, avec droits non determines et reutilisation interdite. Ses theses peuvent etre publiees comme **positions attribuees a Sytsma**, `discoverable_only`, `disputed` ou `needs_evidence` selon le cas. Elles ne doivent pas etre publiees comme doctrine primaire d'Origene ni comme consensus.

## 1. Identite bibliographique et empreinte

| Champ | Resultat verifie |
|---|---|
| Auteur visible | Lee W. Sytsma, B.A., M.T.S. |
| Titre | *Reconciling Universal Salvation and Freedom of Choice in Origen of Alexandria* |
| Nature | Dissertation, Doctor of Philosophy, Theology |
| Institution | Marquette University, Milwaukee, Wisconsin |
| Date | May 2018 ; notice institutionnelle : Spring 2018 |
| Numero de depot | *Dissertations (1934 -)*, no 769 |
| Directeur | Michel Barnes ; la notice institutionnelle donne Barnes, Michael R. |
| Comite remercie dans le PDF | Mickey Mattox, Michael Cover, Aaron Pidel |
| Notice autorite | [e-Publications@Marquette, dissertation 769](https://epublications.marquette.edu/dissertations_mu/769/) |
| SHA-256 PDF | `23aec043358f2f192fb959ae3f5cd3918b6d6095092040d34b5f7d967f3cc6c4` |
| MD5 PDF | `a3f78407d88b976b55dd4ee2a24025c9` |
| Taille | `2,175,765` octets |
| Format | PDF 1.7, Letter 612 x 792 pt, non chiffre, balise |
| Nombre de pages | 262 selon Poppler, PyPDF et le rendu visuel |
| Couche texte | texte natif ; 262 sauts de page, aucune OCR necessaire |
| Extraction de navigation | `pdftotext -layout`, 785,639 octets, SHA-256 `e644b005a1fc44320def6a84ec2032d26d50d4705ca75b093dc37ff75bc72f02` |

Le champ de creation du PDF indique 2025 et les logiciels Appligent/Prince. Il decrit le conteneur telecharge ou recompose, pas la date de la dissertation. La page PDF 1 est une page de depot e-Publications@Marquette ajoutee devant le document academique.

`file(1)` annonce a tort « 6 pages ». Ce resultat est rejete : `pdfinfo` et PyPDF lisent 262 pages, `pdftotext` produit 262 sauts de page et 262 rendus distincts ont ete controles. Le document n'est pas incomplet.

## 2. Droits et reutilisation

Aucune licence Creative Commons ni autorisation de republication n'est visible dans le PDF ou dans la notice de la dissertation. La [FAQ officielle d'e-Publications@Marquette](https://epublications.marquette.edu/faq.html) precise que les documents sont en principe sous copyright lorsqu'aucune licence n'est indiquee, que le depot ne detient pas necessairement le copyright et qu'il ne peut pas accorder de licence de reutilisation.

Decision fail-closed :

- `reuse_status = unverified_do_not_republish` ;
- stockage du PDF local autorise pour l'audit interne ;
- pas de republication de pages, de longues citations ou d'extraits ;
- nouveaux enregistrements limites a des paraphrases courtes et a des locators de pages ;
- tout usage au-dela de la citation academique demande l'autorisation du titulaire des droits.

## 3. Concordance pagination PDF / pagination imprimee

| Segment | Pagination imprimee | Pages PDF, base 1 | Verification visuelle |
|---|---:|---:|---|
| Page de depot Marquette | aucune | 1 | titre, auteur, collection, citation recommandee |
| Page de titre | aucune | 2 | titre exact, PhD, Marquette, May 2018 |
| Abstract | aucune | 3 | resume de la these |
| Acknowledgements | i-ii | 4-5 | continu |
| Abbreviations | iii-iv | 6-7 | continu |
| Table des matieres | v-vi | 8-9 | continu |
| Introduction | 1-13 | 10-22 | `PDF = imprimee + 9` |
| Chapitre 1, State of the Question | 14-43 | 23-52 | idem |
| Chapitre 2, Moral Autonomy | 44-106 | 53-115 | idem |
| Chapitre 3, Stages of Salvation-History | 107-133 | 116-142 | idem |
| Chapitre 4, Apocatastasis | 134-181 | 143-190 | idem |
| Chapitre 5, Future Voluntary Possibilities | 182-224 | 191-233 | idem |
| Conclusion | 225-235 | 234-244 | idem |
| Bibliographie | 236-253 | 245-262 | idem |

Il n'y a pas d'index. Les labels PDF internes `1..262` ne reproduisent pas la pagination imprimee et ne doivent pas servir de locators academiques.

## 4. Structure complete

### Introduction, imprimees 1-13 / PDF 10-22

Sytsma pose la compatibilite entre une restauration universelle foreordonnee et l'autonomie morale. Il annonce une synthese de l'ensemble d'Origene, tout en reconnaissant les problemes de transmission. Il explique pourquoi il utilise a la fois le grec conserve et le latin de Rufin.

### Chapitre 1, imprimees 14-43 / PDF 23-52

Etat de la question et histoire de la reception moderne : Bigg, Molland, Danielou, Sachs et Keith voient une tension ou une incoherence ; Chadwick, Babcock, Crouzel, Blosser et Ware reduisent souvent l'universalisme a une esperance ; Scott maintient l'universalisme mais parle de paradoxe ; Tzamalikos, Ramelli et Jacobsen cherchent une harmonie. Sytsma signale tardivement les proximites avec Benjamins et Gibbons.

### Chapitre 2, imprimees 44-106 / PDF 53-115

Contexte anti-gnostique et anti-predestinarien ; justice et bonte de Dieu ; vocabulaire `τὸ ἐφ' ἡμῖν` / `τὸ αὐτεξούσιον` ; comparaison Epictete / Alexandre ; modele representation-assentiment-impulsion ; reconstruction tripartite esprit-ame-corps ; habitudes, progres moral, responsabilite, louange et blame.

### Chapitre 3, imprimees 107-133 / PDF 116-142

Six etapes de l'histoire du salut : creation, chute, monde pedagogique, progres avant et apres la mort, purification et restauration. Ce chapitre fournit la charpente providentialiste dont Sytsma se sert ensuite ; plusieurs etapes sont explicitement disputees dans la litterature.

### Chapitre 4, imprimees 134-181 / PDF 143-190

Textes apparemment universalistes et textes contraires ; explication pastorale de la reserve d'Origene ; salut du diable comme destruction de l'inimitie plutot que de la substance ; debat sur la permanence ; « predetermination teleologique » ; identification de la providence a la grace salvifique.

### Chapitre 5, imprimees 182-224 / PDF 191-233

Distinction certitude / necessite ; prescience non causale ; trois types de prescience ; comparaison anachronique avec la connaissance moyenne ; selection de situations possibles ; lecture de l'endurcissement de Pharaon comme strategie therapeutique et salvifique.

### Conclusion, imprimees 225-235 / PDF 234-244

Sytsma revendique une correction de l'historiographie, limite la portee de l'autonomie origennienne, renforce la providence/grace, et propose un antecedent d'une partie du molinisme. Ces theses de reception sont des propositions de Sytsma, pas des consensus acquis.

### Bibliographie, imprimees 236-253 / PDF 245-262

La bibliographie distingue les editions et traductions effectivement employees, notamment Crouzel-Simonetti, Butterworth, Bammel, Junod, Lewis, Koetschau, Greer, Chadwick et Scheck.

## 5. Inventaire des pages relues

### Controle integral du conteneur

Les 262 pages ont ete rendues en vignettes et verifiees sur 14 planches : PDF 1-20, 21-40, 41-60, 61-80, 81-100, 101-120, 121-140, 141-160, 161-180, 181-200, 201-220, 221-240, 241-260 et 261-262. Aucun blanc inattendu, page manquante, rotation, rognage ou changement de format n'a ete observe.

### Lecture rapprochee

- liminaires et table : PDF 1-9 ;
- introduction et methodologie : imprimees 1-13 / PDF 10-22 ;
- reception moderne : imprimees 14-43 / PDF 23-52 ;
- autonomie morale : imprimees 44-106 / PDF 53-115 ;
- histoire du salut : structure complete 107-133 / PDF 116-142, avec lecture rapprochee des pages 107-110, 113-117, 122-133 ;
- apocatastase/providence : imprimees 134-181 / PDF 143-190 ;
- prescience et synthese : imprimees 182-224 / PDF 191-233 ;
- conclusion : imprimees 225-235 / PDF 234-244 ;
- bibliographie : imprimees 236-253 / PDF 245-262.

### Deuxieme passe visuelle, haute resolution

Pages imprimees controlees individuellement sur le rendu 160 dpi : `5, 7-11, 44-45, 64-65, 79-80, 88-91, 101, 104-106, 134, 137-141, 150-152, 155-156, 164, 167-169, 171-172, 180-182, 184-185, 188, 191-200, 203-210, 212-214, 216-226, 233-235`. Pour chacune, la page PDF est la page imprimee plus 9.

La couche texte a servi a rechercher et naviguer. Les titres, locators, notes de methode et claims retenus ont ete controles sur les rendus.

## 6. Frontieres des temoins et des traductions

| Objet cite par Sytsma | Manifestation effectivement utilisee | Ce qu'elle peut prouver | Limite |
|---|---|---|---|
| *De principiis / Peri Archon* | Crouzel-Simonetti, SC 252/268 ; grec transmis en extraits, latin de Rufin ; anglais Butterworth | texte/latin/grec selon le locus et commentaire moderne | pas un temoin grec continu ; chaque locus doit porter sa langue et son transmetteur |
| *Philocalia* 21 | anthologie de Basile et Gregoire transmettant *De princ.* III.1 ; grec edite avec SC 268 | texte grec indirect de III.1 | ne pas encoder comme manuscrit direct ou comme SC 226 local |
| *Philocalia* 23 | grec de l'anthologie ; source principale : livre III du *Commentaire sur la Genese* perdu ; 23.12-13 reprend *Contra Celsum* II | prescience, astrologie, possibilites, causalite | source origennienne indirecte ; les passages locaux francais ne sont pas le grec |
| *Philocalia* 25 | extrait du livre I du *Commentaire sur Romains* sur Rom 1.1 | possibilite sans necessitation, selon l'extrait grec | ne pas confondre avec les loci latins du livre VII de Rufin |
| *Philocalia* 27 | anthologie ; sources diverses ; 27.13 est donne comme *Commentaire sur le Cantique* II | pedagogie et soins adaptes selon les sections | 27.1-12 ne doit pas recevoir une oeuvre-source unique sans collation |
| *Commentarii in Romanos* | grec original largement perdu ; traduction/abrege latin de Rufin ; edition Bammel ; anglais Scheck | latin de Rufin et traduction moderne pour les loci cites | les papyri de Tura ne couvrent pas automatiquement chaque locus ; aucune page Scheck ne devient grec direct |
| *Contra Celsum* | grec, SC/Borret ; anglais Chadwick | voix grecque directe pour les loci conserves | les duplications SVF/Philocalia sont des transmissions, pas des corroborations independantes |
| *De oratione* | grec GCS/Koetschau ; anglais Greer | prescience non causale et ordre providentiel | le dossier local actuel est une note mixte a recollationner avant runtime |
| Lettre aux amis d'Alexandrie | preservee en parallele par Jerome et Rufin | reception d'une denegation du « salut du diable » | pas un autographe ; l'interpretation « diable qua diable » est moderne |

Sytsma admet lui-meme, imprimees 7-11 / PDF 16-20, que Rufin a abrege et modifie des textes. Il adopte ensuite la position selon laquelle Rufin reste largement fiable pour l'autonomie morale et l'apocatastase. Ce choix methodologique est une position secondaire ; il ne remplace pas la collation grec/latin locus par locus.

## 7. Claims atomiques

Les paraphrases suivantes disent seulement ce que Sytsma soutient. `Direct` signifie que Sytsma rattache le point a un locus antique identifiable ; cela ne signifie pas que le depot a deja verifie ce locus.

| ID | Claim prudemment paraphrase | Imprimees / PDF | Type | Statut d'ingestion |
|---|---|---:|---|---|
| SY01 | Les categories vagues de « free will » doivent etre remplacees par une analyse du vocabulaire et des conditions de l'autonomie. | abstract ; 79-80 / 88-89 | these methodologique | position secondaire, publiable avec attribution |
| SY02 | `τὸ αὐτεξούσιον` ne nomme pas chez Origene une faculte volitive autonome separee de la raison. | 79-80 / 88-89 | attribution Bugár/Bobzien + Sytsma | plausible, mais attribution secondaire |
| SY03 | Sytsma reconstruit deux conditions : mouvement de l'ame elle-meme et presence d'alternatives morales. | 101, 104-105 / 110, 113-114 | reconstruction | `disputed`, pas definition primaire |
| SY04 | Origene decrit les actions responsables en lien avec louange/blame et avec la justice de Dieu. | 44-45, 64-65 / 53-54, 73-74 | Direct, *PArch* III.1 et preface | candidat primaire apres collation |
| SY05 | Origene emploie un modele de representation, jugement, assentiment et impulsion proche du stoicisme tardif. | 82-91 / 91-100 | reconstruction historique | attribuer a Sytsma ; comparer Frede/van der Eijk |
| SY06 | Sytsma superpose a ce modele une anthropologie esprit-ame-corps et une structure binaire des motivations. | 69-78, 92-101 / 78-87, 101-110 | reconstruction contestee | `disputed` |
| SY07 | La permanence d'une motivation spirituelle positive rend toujours le progres possible, sans le garantir. | 97-106 / 106-115 | synthese | position Sytsma, pas fait primaire |
| SY08 | Le mot `ἀποκατάστασις` est rare chez Origene ; le dossier ne se reduit pas au lexeme. | 134 / 143 | inventaire de loci | candidat bibliographique |
| SY09 | Sytsma lit *PArch*, *ComJn*, *Contra Celsum* et *ComRm* comme soutenant une restauration universelle. | 137-140 / 146-149 | synthese multi-temoins | `disputed`, recollation necessaire |
| SY10 | Il reconnait des textes contraires : exclusion, feu et absence de conversion du diable. | 140-143 / 149-152 | Direct + reception | conserver la contradiction, ne pas harmoniser en amont |
| SY11 | Il explique ces contradictions par une pedagogie pastorale reservee aux lecteurs avances. | 144-152 / 153-161 | interpretation | `disputed`; pas de statut consensus |
| SY12 | Il distingue la substance du dernier ennemi et son orientation hostile pour maintenir une restauration finale. | 137-150 / 146-159 | interpretation Heine/Scott/Sytsma | `disputed` |
| SY13 | Il soutient une apocatastase permanente et un terme meilleur que le commencement. | 152-166 / 161-175 | interpretation de *ComRm* V.10 et *PArch* | `disputed`; texte latin/grec a separer |
| SY14 | Il nomme « predetermination teleologique » la certitude du telos universel sans necessitation de chaque choix. | 167-172 / 176-181 | categorie moderne | position Sytsma uniquement |
| SY15 | Il identifie toute providence origennienne a la grace salvifique, y compris punition et abandon. | 172-180 / 181-189 | synthese apres Drewery/Koch | `disputed`, atomiser les exemples |
| SY16 | Il reconnait qu'aucun passage conserve ne formule directement son argument complet. | 184 / 193 | disclosure methodologique | **obligatoire dans toute reutilisation** |
| SY17 | L'assentiment salvifique doit etre volontaire et n'est pas directement cause par Dieu. | 185-186 / 194-195 | Direct, *Cels* VI.57 | candidat primaire |
| SY18 | *PArch* II.1.2 associe harmonie, ordre du monde et mouvements des volontes sans force. | 186-188 / 195-197 | Direct, latin de Rufin | candidat latin, pas preuve du systeme complet |
| SY19 | *Philocalia* 23 distingue l'evenement certain de l'evenement necessite ou force. | 191-196 / 200-205 | Direct, temoin grec indirect | priorite primaire apres reingestion grecque |
| SY20 | *Philocalia* 23 attribue a Dieu la connaissance des deux possibilites pour Judas et de celle qui se realisera. | 198-202 / 207-211 | Direct, Phil 23.8-9 | soutient types 1-2, pas encore type 3 |
| SY21 | Les « trois types » sont la numerotation de Sytsma ; Origene ne les enumere pas. | 198, 203-205 / 207, 212-214 | reconstruction explicite | `needs_evidence`, jamais doctrine directe |
| SY22 | Le type 3 est rapproche de la connaissance moyenne et des contrefactuels de liberte. | 203-209 / 212-218 | comparaison moderne | `disputed`; aucun label moliniste antique |
| SY23 | Phil 27, *Cels* VII.44 et *ComRm* IX.3 montrent, selon Sytsma, des soins adaptes a des reponses possibles. | 205-209 / 214-218 | faisceau de loci | atomiser chaque oeuvre et manifestation |
| SY24 | La preselection d'une unique histoire conduisant toutes les ames a la restauration est la synthese propre de Sytsma. | 210-215 / 219-224 | reconstruction centrale | `discoverable_only`, `disputed` |
| SY25 | Le fragment de *PArch* II.9.1 transmis par Justinien est utilise pour une speculation sur un nombre limite de creatures. | 215-216 / 224-225 | temoin hostile + speculation | ne pas ingerer sans recollation du fragment |
| SY26 | *De oratione* 6-7 affirme que Dieu ordonne l'economie a partir de sa prescience des choix ; l'universalisme n'y est pas explicite. | 216-219 / 225-228 | Direct + inference | separer texte et extrapolation |
| SY27 | *PArch* III.1.13-17 presente l'abandon et l'endurcissement de Pharaon comme traitement retarde ; Sytsma en deduit une garantie universelle. | 219-224 / 228-233 | Direct + inference forte | texte candidat ; conclusion `disputed` |
| SY28 | La comparaison avec Molina et l'antériorite historique d'Origene sont proposees comme implication de la recherche. | 233-235 / 242-244 | reception | demande une etude de reception autonome |

## 8. Loci antiques prioritaires cites par Sytsma

| Locus | Usage chez Sytsma | Imprimees / PDF | Temoignage a demander au depot |
|---|---|---:|---|
| *PArch* pref. 5 ; III.1.1-6 | responsabilite, commandes, louange/blame, autexousion | 45, 65, 79-90 / 54, 74, 88-99 | grec Philocalia 21/SC 268 separe du latin de Rufin |
| *PArch* III.1.13-17 | Pharaon, abandon, traitement lent, providence | 219-224 / 228-233 | sections grecques exactes 13-17 |
| *PArch* II.1.2 ; III.5.8 | ordre des mouvements libres vers une fin commune | 186-190, 212 / 195-199, 221 | latin Rufin, avec statut de traduction/adaptation |
| *PArch* I.6 ; III.6 | apocatastase, dernier ennemi, permanence | 137-139, 151-166 / 146-148, 160-175 | distinguer Latin, grec fragmentaire et inference |
| *Philocalia* 23.7-11 | prescience, certitude, possibilites, causes externes | 191-203 / 200-212 | grec exact `tlg019`, non les lignes francaises `_grc` |
| *Philocalia* 25.2 | possibilite et non-necessitation | 195 / 204 | extrait grec du *ComRm* I, non le Latin du livre VII |
| *Philocalia* 27.4, 27.11 | soins adaptes, Tyr/Sidon | 205-208 / 214-217 | grec exact et attribution de l'oeuvre-source |
| *De oratione* 6-7 | prescience non causale, ordre de l'economie | 195, 216-219 / 204, 225-228 | grec GCS exact, passage atomique |
| *Cels* VI.57 | persuasion reciproque et assentiment non cause par Dieu | 185 / 194 | grec SC 147 |
| *Cels* VIII.72 | toute nature rationnelle et choix volontaire | 139, 196 / 148, 205 | grec, corriger le faux `canonical_ref=1.72` |
| *ComRm* V.10 | amour et permanence | 140, 155-157 / 149, 164-166 | latin Rufin/Bammel + anglais Scheck ; pas grec direct affirme |
| *ComRm* VII.6 | prescience/predestination dans le sens scripturaire | 191, 202 / 200, 211 | latin Rufin ; ne pas substituer les loci SC 543 VII.14 |
| *ComRm* IX.3 | grace distribuee selon le benefice futur | 207 / 216 | latin Rufin/Bammel, traduction Scheck |

## 9. Reception moderne cartographiee

Sytsma organise le debat en familles, mais ne produit pas un sondage exhaustif de consensus :

- incoherence/tension : Bigg, Molland, Danielou, Sachs, Keith ;
- universalisme reduit a une esperance ou a une offre : Chadwick, Babcock, Crouzel, Blosser, Ware ;
- universalisme maintenu mais relation a la liberte encore paradoxale : Scott ;
- propositions d'harmonie : Tzamalikos, Ramelli, Jacobsen ;
- antecedents proches de la these Sytsma : Benjamins et Gibbons, signales tardivement ;
- permanence et salut du diable : Heine, Scott, Holliday, Daley, Edwards, Crouzel et d'autres positions concurrentes.

Le rapport recommande de modeliser ces positions comme des arguments attribues, non comme deux camps exhaustifs. La dissertation elle-meme est une intervention dans ce debat.

## 10. Crosswalk avec l'etat du depot

### 10.1 Empreintes de l'etat lu

```text
e1a5c1bf0ed25615005c9cd3107f3be25235b535faa563e5fa847eb5e9522933  data/literature_acquisition/manifest.jsonl
d6519cf1192db6ae3dccb5ebc25599c145f5c472b88e2da4d821c4761333f9f6  scripts/build_literature_acquisition_manifest.py
b4a95eb53ac26a6a5b55c0d88c646e939231f952838aff7ba761d62bf345a9ec  data/kg/acquisition_patches/sytsma.json
92a0cd13dcab0d1749119e8ef0b772392e7920177096213deca2906e88821817  data/kg/nodes.jsonl
b1ce4f5e594d846c0d64ad1a33b4e0b0970230c11641010df8ea9b58e8ebfd2a  data/kg/edges.jsonl
e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3  data/corpus/passages.jsonl
5bd6657adb6aa006bc12a33285c399e00fc7ab467932b603369e119bdc9e089a  data/corpus/citations.jsonl
2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e  data/corpus/manifest.jsonl
3e21f88fe06e9e61d7444f724d66a1eabdadd2af27ec42dca22bd8651e94b825  data/kg/publications.bib
bba25a9d4d57dd9f82fe1eeb4b410f262312050345fb27fc9fb4b7cce2478e69  data/kg/publications_bibtex_report.json
c16553ff02c6cfdcd8402551bcd128fcf8cf0f6d5855a7b38d0be670fbe2a42e  data/scholarly_sources/manifest.jsonl
```

### 10.2 Manifeste d'acquisition

La ligne `lit_sytsma_2018_dissertation_origen` a le bon fichier, hash, nombre de pages et statut de reutilisation, mais deux champs factuels sont faux :

- `creators = ["David Sytsma"]` doit devenir `Lee W. Sytsma` ;
- `title = "Origen's Theory of Free Will and Universal Salvation"` doit devenir le titre exact de la dissertation.

Les memes erreurs sont codees dans `scripts/build_literature_acquisition_manifest.py`, donc corriger seulement le JSON serait non reproductible.

### 10.3 Publication 2018 / livre 2020

Le KG a supprime le noeud dissertation distinct `pub_sytsma_2018_reconciling_universal_salvation_and_freedom_of_choice_in_origen` et l'a fusionne dans `pub_sytsma_2020_universal_salvation_origen`. Cette fusion est impropre aux preuves de pages.

Le livre Gorgias existe bien comme publication distincte : [notice officielle Gorgias Press](https://www.gorgiaspress.com/universal-salvation-and-freedom-of-choice-according-to-origen-of-alexandria), serie 74, ISBN imprime `978-1-4632-3950-3`. Mais aucun exemplaire local de ce livre n'a ete collate dans cette vague. Les pages de la dissertation ne peuvent donc pas etre appelees pages du livre 2020, meme si le livre derive de la recherche doctorale et reprend la meme these generale.

La bibliographie actuelle exporte seulement le livre 2020. Une entree de dissertation 2018 distincte manque.

### 10.4 Touched-set Sytsma actuel

Les 14 noeuds directement issus du patch sont :

```text
scholar_sytsma_lee
pub_sytsma_2020_universal_salvation_origen
scholarly_argument_sytsma_critique_of_modern_critique
scholarly_argument_sytsma_autexousion_technical_term
scholarly_argument_sytsma_autexousion_not_a_faculty_of_will
scholarly_argument_sytsma_two_requirements_moral_autonomy
scholarly_argument_sytsma_origen_adopts_stoic_impression_assent
scholarly_argument_sytsma_anti_determinism_idle_argument_deprinc_iii
scholarly_argument_sytsma_permanent_apokatastasis
scholarly_argument_sytsma_universalism_as_teleological_predetermination
scholarly_argument_sytsma_three_types_foreknowledge
scholarly_argument_sytsma_preselection_prearrangement_thesis
scholarly_argument_sytsma_god_manufactures_circumstances
scholarly_argument_sytsma_providence_is_saving_grace
```

Ils touchent 64 aretes : 35 `discusses`, 12 `created_by`, 12 `advanced_in`, 1 `authored_by`, et 4 aretes dialectiques (`opposes`, `agrees_with`, `critiques`, `extends`). Ils touchent 24 citations de corpus : 18 `discussion`, 4 `testimonium`, 2 `direct_quote`, reparties sur 12 passages.

Tous les douze noeuds d'argument ont `citation_verified: true`, `citation_verdict: verified` et `confidence: high`. Cette typologie ne distingue pas :

- page secondaire verifiee ;
- exactitude de l'interpretation de Sytsma ;
- exactitude du texte antique ;
- accord ou desaccord de la recherche.

### 10.5 Les douze passages antiques actuellement relies

| Passage ID | Etat actuel | Decision fail-closed |
|---|---|---|
| `067fa9b9-4368-5eaa-a0ba-7514c671491b` | Phil 23.10 francais sous `_grc`, faux `tlg028` | retirer du chemin primaire ; remapper au grec exact |
| `1fbc7c6f-4045-5edc-a8b2-530871858ce5` | Phil 23.11 francais sous `_grc`, faux `tlg028` | idem |
| `3d4ccd1d-ed30-5443-9364-942aeea01bca` | Phil 23.8 francais sous `_grc`, faux `tlg028` | idem |
| `59b5fa87-a703-5adb-b8ce-2f9e5796d728` | Phil 23.9 francais sous `_grc`, faux `tlg028` | idem |
| `ef292c39-0828-5950-8591-4d549b39f48d` | titres et extraits francais concaténes, pseudo-locus `titulus` | quarantaine / scission |
| `3e767176-490c-58a3-a173-c7e10e5d85a9` | note editoriale anglaise + citation grecque, faux CTS `tlg001` | quarantaine, rejouer sur III.1.3 exact |
| `dc6ff8bc-31d6-52a9-a0c8-416df4587c99` | traduction francaise de la version latine de Rufin | typer comme traduction publiee, pas grec direct |
| `baa51e4b-9ad7-54a1-a971-74de1631661e` | ancien doublon granulaire III.1.1 | ne pas compter comme temoin independant |
| `a343b50a-6de2-55be-b2d7-80e1c89133e5` | gros conteneur grec III.1, granularite dupliquee | remapper aux sections exactes, pas corroboration |
| `42e49678-0557-44ef-9341-0a1f22f6efa6` | grec de *Cels* VIII.72 mais `canonical_ref=1.72` | corriger le locus avant reutilisation |
| `8a7ecc77-2a73-5d39-8470-46b65ff495e0` | SVF II.957 transmet *Cels* II.20 | encoder l'indirection, pas un second temoin independant |
| `4bf277af-bdd7-55d0-b50b-113e788ec5f7` | dossier mixte grec/anglais sur *De oratione* 6 | remplacer par un passage grec atomique recollationne |

### 10.6 Registre SOTA et issue Origene ouverte

Il n'existe pas encore de source/evidence/issue Sytsma propre dans le registre. L'issue `issue_origen_manifestation_language_and_witness_conflation` est **OPEN** et couvre explicitement les neuf cohortes restantes *De principiis*, *Philocalia* et *Commentaire sur Romains*. Son etat ne doit pas changer du fait de cette dissertation.

Source IDs deja pertinents :

- `src_anc_origen_de_principiis` ;
- `src_anc_origen_philocalia` ;
- `src_anc_origen_commentary_romans`.

Concepts et arguments de rapprochement a ne pas ecraser :

- `concept_autexousion_christian_freedom_u1v2w3x4` ;
- `concept_divine_prescience` ;
- `concept_apocatastasis` ;
- `concept_synkatathesis_stoic_assent` ;
- `concept_grace_freedom_synergy` ;
- `argument_origen_prescience_causality` ;
- `argument_origen_anti_astrological` ;
- `argument_origen_argos_logos` ;
- `argument_origen_free_will_theodicy_6f9d8a3c` ;
- `argument_origen_witness_diss_problem1_prescience_amand1945`.

La dissertation apporte une position secondaire sur ces objets. Elle ne justifie pas de remplacer leur ontologie globale par la theorie de Sytsma. Plusieurs descriptions generiques contiennent d'ailleurs des assertions plus fortes ou contradictoires et demandent leur propre vague de correction.

## 11. Contradictions et risques

1. **Thèse 2018 / livre 2020.** Le record actuel fusionne deux publications ; les pages sont celles de la dissertation seulement.
2. **Statut de preuve.** La verification visuelle prouve que Sytsma fait un claim, pas que le claim est vrai d'Origene.
3. **Synthese systematique.** Sytsma assume qu'une synthese coherente d'Origene est possible ; cette hypothese est discutee des imprimees 6-7 / PDF 15-16.
4. **Rufin.** Sytsma defend sa fiabilite globale pour les themes etudies, mais reconnait ses omissions, lissage et abrege. Une confiance generale ne remplace pas la collation.
5. **Trois presciences.** La numerotation est moderne et explicite ; le troisieme type est une inference.
6. **Molinisme.** « Middle knowledge » est un outil comparatif anachronique, pas un terme d'Origene.
7. **Apocatastase permanente.** Sytsma harmonise des textes contradictoires ; la dissertation seule ne ferme pas le debat.
8. **Providence = grace.** C'est une these de synthese, en partie appuyee sur Drewery/Koch, non une definition explicite d'Origene.
9. **Temoin hostile.** L'argument speculative des imprimees 215-216 utilise un fragment transmis par Justinien ; il ne doit pas etre promu sans controle du temoin.
10. **Philocalia.** Une anthologie du IVe siecle preserve des extraits de plusieurs oeuvres ; `authored_by Origen` au niveau de l'anthologie est insuffisant.
11. **Commentaire sur Romains.** Latin de Rufin, abrege ; les locus Scheck/Bammel ne doivent pas recevoir automatiquement un statut grec.
12. **Copyright.** Les longues `quote_verbatim` du patch et des noeuds ne doivent pas etre dupliquees dans de nouveaux records.

## 12. Ce que la dissertation peut et ne peut pas fermer

### Peut etre ferme avec ce PDF

- identite bibliographique de la dissertation 2018 ;
- auteur, titre, institution, date et numero 769 ;
- hash, taille, nombre de pages et concordance imprimee/PDF ;
- table des matieres et bibliographie ;
- droits : absence de licence visible et politique de reutilisation fail-closed ;
- pages exactes ou Sytsma formule chacune de ses theses ;
- disclosure que le coeur du chapitre 5 est une reconstruction non enoncee dans un passage unique ;
- distinction bibliographique avec le livre Gorgias 2020.

### Doit rester ouvert

- verification primaire de chaque grec/latin cite ;
- exactitude de la reconstruction des trois types ;
- permanence et universalite de l'apocatastase ;
- salut du diable et interpretation de la lettre aux amis ;
- equivalence globale providence/grace ;
- fiabilite de Rufin locus par locus ;
- attribution exacte des extraits Philocalia 27.1-12 ;
- concordance de pages dissertation 2018 / livre 2020 ;
- antecedence historique par rapport a Molina ;
- toute pretention de consensus de reception.

## 13. Proposition de vague P0 fail-closed

Cette section est un plan, pas une autorisation d'ecriture.

### P0-A - Identite et manifestations

1. Corriger de maniere reproductible `scripts/build_literature_acquisition_manifest.py` et `data/literature_acquisition/manifest.jsonl` : Lee W. Sytsma, titre exact, dissertation 2018, hash et 262 pages PDF.
2. Reconstituer le noeud distinct `pub_sytsma_2018_reconciling_universal_salvation_and_freedom_of_choice_in_origen`.
3. Conserver `pub_sytsma_2020_universal_salvation_origen` comme livre Gorgias distinct, publisher-bound, non collate localement.
4. Creer deux entrees BibTeX distinctes et regenerer atomiquement `publications.bib` et son rapport.
5. Ne pas deduire un mapping de pages entre les deux publications.

### P0-B - Douze positions secondaires

Pour chacun des douze noeuds `scholarly_argument_sytsma_*` :

- rattacher les pages a la dissertation 2018 ;
- ajouter `source_artifact_sha256` et locators imprimes/PDF ;
- remplacer `citation_verified: true` par des statuts types tels que `page_support_checked`, `citability=discoverable_only`, `interpretive_status=attributed_secondary_position` ;
- marquer `three_types`, `preselection`, `manufactures_circumstances`, `permanent_apokatastasis`, `teleological_predetermination` et `providence_is_saving_grace` comme `disputed` ou `needs_evidence` ;
- conserver explicitement la phrase methodologique de p. 184 sous forme paraphrasee : aucun passage unique ne formule la synthese ;
- supprimer ou quarantainer les longues `quote_verbatim`, sans les recopier.

### P0-C - Aretes et citations

1. Rebrancher les 12 aretes `advanced_in` vers la dissertation 2018.
2. Garder les aretes `discusses` seulement comme relations thematiques attribuees.
3. Conserver les quatre aretes dialectiques comme positions de Sytsma, avec locators secondaires et statut dispute.
4. Quarantainer puis rejouer les 24 citations contre les bonnes manifestations antiques.
5. Les lignes francaises Philocalia ne doivent plus servir de `testimonium` grec ; les duplications III.1 ne doivent pas compter comme temoins independants.
6. Ne modifier aucun texte antique dans cette vague ; la reingestion primaire reste une transaction separee.

### P0-D - Registre

Creer :

- `src_sec_sytsma_2018_origen_dissertation` avec coverage `full_secondary_read`, droits `unverified_do_not_republish` ;
- un evidence atom bibliographique pour PDF 1-3 ;
- des evidence atoms distincts pour methodologie/witnesses (imprimees 5-11), autonomie (79-106), apocatastase (134-181), prescience/reconstruction (182-224) ;
- `issue_sytsma_2018_2020_manifestation_and_evidence_overclaim`, statut **OPEN**, lie a `issue_origen_manifestation_language_and_witness_conflation` ;
- aucune verification independante ou adversariale fictive.

### P0-E - Transaction et tests

- before-images exactes des 14 noeuds, 64 aretes, 24 citations, patch Sytsma, manifeste/builder, BibTeX/report et records registre ;
- touched-set exact et drift fail-closed ;
- quarantaine durable ; lock, journal, rollback, crash recovery et idempotence ;
- schema registre normatif : zero nouvelle erreur ;
- passages/corpus/manifest antique byte-identiques dans cette vague ;
- snapshot, corpus, parity, work-child, registry, BibTeX/report et runtime citability gates ;
- test explicite : aucune page de la dissertation ne doit etre attribuee au livre 2020 ;
- test explicite : aucun des douze arguments n'a un booleen generique `citation_verified=true` ;
- test explicite : l'issue Origene et la nouvelle issue Sytsma restent ouvertes.

## 14. Decision finale

La dissertation est une source secondaire de haute valeur pour cartographier une reconstruction coherente et tres explicite de l'autonomie, de la providence et de la prescience chez Origene. Elle est aussi une source excellente pour identifier les loci que le corpus doit recollationner.

Elle ne doit pas devenir une autorite primaire de substitution. L'ingestion sure consiste a enregistrer « Sytsma soutient X, a telle page », a separer la dissertation du livre 2020, et a maintenir toutes les affirmations antiques fortes en etat dispute ou needs-evidence jusqu'a collation des manifestations grecques, latines et traduites correspondantes.

Seul ce rapport Markdown a ete ajoute. Aucun noeud, arete, citation, passage, manifeste, bibliographie ou record de registre n'a ete modifie.
