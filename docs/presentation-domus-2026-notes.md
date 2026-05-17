# Notes de presentation - DOMUS 2026

Ces notes sont faites pour accompagner les slides, pas pour les lire. L'idee est de prendre 1 ou 2 phrases fortes par slide, puis de garder le reste comme filet de securite.

## Slide 1 - Titre

- Ouvrir en disant que je ne presente pas seulement un outil numerique, mais une tentative de repondre a un vrai probleme de recherche en philosophie antique.
- Poser tout de suite la these centrale : EleutherIA sert a relier trois choses qui sont d'habitude separees, a savoir les textes, les concepts et le raisonnement de l'IA.
- Dire que le sujet est le libre arbitre antique, mais que l'enjeu de fond est plus large : comment faire travailler une IA sur des sources anciennes sans perdre la rigueur philologique.

## Slide 2 - Plan

- Expliquer que la presentation suit un mouvement simple : d'abord pourquoi ce projet a ete possible maintenant, ensuite quel probleme savant il traite, puis comment l'infrastructure y repond.
- Annoncer que la demo n'arrive pas comme un gadget final : elle sert a montrer que les choix methodologiques ont une traduction concrete dans l'interface.
- Dire que la conclusion ouvrira sur la portabilite, parce que l'interet d'EleutherIA n'est pas limite au libre arbitre.

## Slide 3 - Le tweet de Karpathy

- Ne pas presenter ce slide comme une citation d'autorite, mais comme un symptome d'un changement de regime technique.
- Dire que ce tweet m'interesse parce qu'il formule une intuition tres simple : on peut decrire une intention en langage naturel et deleguer une partie de l'implementation a la machine.
- Ajouter que, pour un chercheur en sciences humaines, cela change l'acces meme a la fabrication d'outils complexes.

## Slide 4 - Ce que ce tweet change vraiment

- Dire que chaque grande etape de l'histoire de l'informatique a remonte le niveau d'abstraction : assembleur, langages de haut niveau, puis ici langage naturel.
- Preciser que cela ne veut pas dire que le code disparait, mais que la formulation du probleme devient une partie centrale du travail.
- Faire le lien personnel : EleutherIA est aussi une preuve par l'exemple qu'un doctorant en philosophie peut construire une vraie infrastructure s'il peut travailler avec ces nouveaux outils.
- Insister sur le fait que l'enjeu n'est pas seulement "faire un site", mais articuler base de donnees, graphe, moteur GraphRAG, tests et deploiement.

## Slide 5 - Le probleme

- Partir du point de vue du chercheur : pour repondre a une question simple en apparence, il faut traverser des siecles, des langues et des traditions savantes.
- Dire que le vrai probleme n'est pas seulement l'abondance de sources, mais leur dispersion et l'absence de vue d'ensemble.
- Ajouter que les LLM generalistes aggravent un risque majeur pour notre domaine : ils produisent volontiers du grec ou du latin plausibles mais faux.
- Formuler la promesse d'EleutherIA en une phrase : reunifier les sources, rendre visibles les connexions, et interdire la citation inventee.

## Slide 6 - Trois piliers

- Expliquer que le projet repose sur trois couches complementaires et qu'aucune ne suffit seule.
- Le corpus fournit la matiere textuelle verifiable.
- Le graphe fournit la structure intellectuelle : qui repond a qui, quel argument appartient a quel debat, quel concept traverse quelles traditions.
- Le GraphRAG sert a transformer cette masse organisee en parcours d'enquete plutot qu'en simple liste de resultats.

## Slide 7 - 1 200 ans de philosophie

- Dire que l'interet du corpus est sa profondeur diachronique : on peut suivre un probleme des Presocratiques jusqu'a l'Antiquite tardive.
- Ajouter que cette amplitude change la nature des questions possibles : on ne cherche plus seulement un passage, on peut suivre des continuites, des ruptures et des relectures.
- Faire comprendre que le projet traite un debat historique long, pas une collection de citations isolees.

## Slide 8 - Les ecoles philosophiques

- Expliquer que le libre arbitre antique n'est pas une doctrine unique, mais un champ de positions souvent incompatibles.
- Utiliser ce slide pour montrer pourquoi un graphe est utile : il faut relier doctrines, arguments, auteurs et objections plutot que classer les textes en silos.
- Dire que comparer stoiciens, epicuriens, peripateticiens ou Peres de l'Eglise demande une representation explicite des positions et des controverses.

## Slide 9 - Le corpus de textes

- Insister sur le passage a l'echelle du passage et non seulement de l'oeuvre entiere.
- Expliquer que chaque unite textuelle est identifiee par un CTS URN, lemmatisee, et reliee au graphe.
- Dire que la traduction anglaise n'est pas la source, mais une couche d'accessibilite qui permet la recherche semantique et la navigation multilingue.
- Ajouter que cela permet de passer d'une requete a un passage exact, avec reference canonique exploitable par un chercheur.

## Slide 10 - Zero hallucination

- Dire clairement que c'est la regle non negociable du projet.
- Formuler le principe de maniere simple : l'IA peut raisonner sur les sources, mais elle n'a jamais le droit d'inventer la source.
- Ajouter que, s'il manque un texte, le systeme doit le dire ; s'il y a doute, il doit paraphraser plutot que fabriquer.
- Faire comprendre que cette contrainte est a la fois technique, methodologique et ethique.

## Slide 11 - Noeuds et aretes

- Expliquer le graphe avec un exemple simple : un auteur, un concept, une oeuvre, et les relations qui les lient.
- Dire qu'un graphe de connaissances n'est pas juste une visualisation elegante ; c'est une facon de formaliser les objets de recherche et leurs liens.
- Ajouter que cela permet ensuite a l'IA de raisonner sur des chemins intellectuels, pas seulement sur des mots proches.

## Slide 12 - Architecture a deux couches

- Dire que c'est un choix methodologique central du projet.
- Expliquer que les notions antiques comme `to eph' hemin`, `autexousion` ou `prohairesis` ne se laissent pas rabattre sans reste sur la categorie moderne de "free will".
- Donc le graphe separe la couche primaire des sources antiques et la couche secondaire des reconstructions modernes.
- Ajouter que cela permet de distinguer ce qu'un auteur antique dit, de ce qu'un historien moderne pense qu'il dit.

## Slide 13 - Types de noeuds

- Ne pas enumerer les 24 types un par un ; dire plutot que l'ontologie est assez fine pour representer non seulement des personnes et des oeuvres, mais aussi des arguments, des positions, des debats et des passages.
- Insister sur le fait qu'un projet comme celui-ci ne peut pas etre seulement bibliographique.
- Le point important est que les objets manipulables par le moteur correspondent a de vrais objets savants.

## Slide 14 - Types de relations

- Expliquer que la richesse du graphe vient surtout des relations : refute, repond a, cite, appartient a, interprete, etc.
- Dire que ces relations servent a encoder des formes differentes de lien intellectuel, pas un simple "est lie a".
- Ajouter que c'est ce qui rend possible la navigation multi-sauts dans les questions complexes.

## Slide 15 - Le graphe en chiffres

- Utiliser les chiffres comme indication d'echelle, mais dire tout de suite que le chiffre le plus important n'est pas le nombre de noeuds.
- Le vrai chiffre cle, c'est le volume de citations verifiees reliant le graphe aux passages.
- Dire que l'objectif n'etait pas de produire un gros graphe abstrait, mais un graphe suffisamment ancre dans des textes.
- Eventuellement ajouter que la taille est deja suffisante pour rendre visibles des communautes et des chemins de recherche qui seraient tres difficiles a reconstruire a la main.

## Slide 16 - Le defi

- Lire la question une seule fois, puis dire qu'elle est interessante parce qu'elle oblige a combiner plusieurs niveaux.
- Montrer que repondre exige de relier un argument stoicien, une critique academicienne, plusieurs textes antiques et une reconstruction moderne.
- Dire que ce n'est pas un cas marginal : c'est exactement le type de question que posent les chercheurs.
- Conclure que ni le moteur de recherche classique ni le chatbot generique ne savent bien faire cela.

## Slide 17 - Pipeline GraphRAG agentique

- Expliquer que le systeme ne saute pas directement a la redaction.
- Dire qu'il commence par explorer largement, puis il construit un carnet de recherche, puis il etablit un plan de lecture.
- Presenter cela comme une simulation d'un bon geste savant : d'abord cadrer, ensuite lire, ensuite seulement synthetiser.
- Faire sentir que l'agenticite ici n'est pas un effet de mode, mais une organisation du travail intellectuel.

## Slide 18 - Du dossier de preuves a la reponse

- Dire que la sortie du systeme n'est pas une "reponse magique", mais un dossier de preuves assemble a partir de passages exacts.
- Ajouter que ce dossier garde ensemble l'original, la traduction liee et la reference canonique.
- Expliquer que la derniere couche est une couche critique : elle controle phrase par phrase si la synthese est effectivement soutenue par les passages charges.
- C'est la qu'on voit la difference entre generation libre et generation sous contrainte documentaire.

## Slide 19 - Un GraphRAG agentique, en pratique

- Expliquer que l'agent n'est pas le modele seul, mais l'architecture complete.
- Le chef d'orchestre garde l'etat et empeche l'improvisation.
- L'analyste formule des hypotheses et produit les notes de lecture.
- La bibliotheque donne acces au corpus, au graphe, aux embeddings et a la structure des oeuvres.
- Le carnet vivant memorise les decisions de recherche.
- Le secretaire critique refuse ce qui n'est pas prouve.

## Slide 20 - Le signal cle : `passage_citations`

- Dire que s'il fallait resumer l'originalite technique du projet en une table, ce serait celle-ci.
- Expliquer simplement : chaque noeud du graphe peut etre relie a un ou plusieurs passages qui le fondent, avec un score de confiance.
- Ajouter que ce score permet de distinguer l'attestation explicite, l'appui contextuel fort, l'inference savante et l'attribution provisoire.
- Insister sur le fait que ce lien structurel entre graphe et texte est ce qui empeche EleutherIA de se reduire a un simple chatbot branche sur une base.

## Slide 21 - Le raisonnement devient observable

- Dire que pour un chercheur, une bonne reponse sans trajectoire visible reste insuffisante.
- Expliquer que l'interface montre le dossier de recherche en cours : etapes, appels d'outils, decisions de lecture, preuves retenues, contre-preuves.
- Ajouter que cela change le statut epistemique de la sortie : on peut auditer, critiquer et reproduire le chemin.
- Formuler la these forte de ce slide : on passe d'un agent conversationnel a un instrument de recherche.

## Slide 22 - Retrouver les sources

- Expliquer que la recherche combine trois logiques qui compensent chacune les angles morts des autres.
- Le plein texte retrouve les correspondances exactes.
- La recherche lemmatique permet de ne pas perdre les variations morphologiques du grec et du latin.
- La recherche semantique en vecteurs permet de retrouver des proximites de sens.
- La fusion RRF sert ensuite a recombiner ces signaux au lieu de parier sur une seule methode.

## Slide 23 - Principes FAIR

- Dire que FAIR n'est pas ici un habillage institutionnel ajoute a la fin.
- Montrer comment cela se traduit concretement : DOI Zenodo, identifiants CTS, API ouverte, formats standards, licence CC BY.
- Ajouter que la reutilisabilite depend aussi de la modularite du code : corpus, graphe et GraphRAG existent comme briques distinctes.
- Dire en une phrase que l'objectif est de produire un objet de recherche qui puisse etre cite, interroge et repris.

## Slide 24 - Architecture technique

- Presenter ce slide comme une coupe transversale, pas comme un inventaire d'outils.
- Dire que l'interface React sert a rendre visibles le graphe, les sources et le raisonnement.
- FastAPI orchestre les services Python.
- PostgreSQL stocke les textes, les relations tabulaires, les citations et les index de recherche; la couche GraphRAG actuelle est sans vecteurs et les modeles sont distribues selon les taches.
- Ajouter que l'interet de cette architecture est sa modularite : on peut faire evoluer une couche sans tout refaire.

## Slide 25 - L'effort d'ingenierie

- Utiliser ce slide pour objectiver le projet : on n'est pas devant une maquette de conference faite en surface.
- Dire que ce qui compte ici n'est pas de celebrer les chiffres, mais de montrer qu'il y a eu un vrai travail d'ingenierie, de tests, de schema, de nettoyage de donnees et de deploiement.
- Faire le lien avec l'ouverture : oui, ce projet a ete rendu possible par l'IA, mais il a demande en retour une discipline de conception tres forte.
- Tu peux conclure sur l'idee que le changement de paradigme ne supprime pas l'effort ; il deplace l'effort vers la specification, la verification et l'architecture.

## Slide 26 - Demo graphe

- Commencer la demo par quelque chose de simple et lisible, par exemple un philosophe, un concept ou une ecole connue.
- Montrer que le graphe n'est pas seulement un decor : on peut chercher, cliquer, filtrer, et faire apparaitre des voisinages intellectuels.
- Si possible, illustrer une transition entre une vue large et un noeud precis pour faire sentir le passage du macro au micro.
- Ne pas rester trop longtemps sur la beaute visuelle ; l'important est l'utilite hermeneutique.

## Slide 27 - Demo query

- Poser une question qui force vraiment le systeme a articuler plusieurs sources.
- Pendant la demo, commenter moins la reponse finale que le processus visible dans le panneau droit.
- Montrer ou apparaissent les passages, les decisions de lecture et les references canoniques.
- Le message a faire passer est que la valeur du systeme tient autant a la transparence du parcours qu'a la qualite du paragraphe final.

## Slide 28 - Ce que cela change

- Reprendre les trois transformations majeures.
- Premierement, l'ancrage textuel : on peut demander beaucoup a l'IA, mais elle reste tenue par les passages.
- Deuxiemement, la visibilite des connexions : le graphe rend observables des reseaux que la lecture lineaire laisse souvent implicites.
- Troisiemement, la bonne place de l'IA : elle assiste la lecture et la synthese, elle ne remplace pas le jugement savant.

## Slide 29 - Perspectives

- Dire qu'EleutherIA n'est pas un systeme clos ; l'architecture appelle l'extension.
- Mentionner l'extension du corpus, l'interoperabilite avec les outils DH, les agents specialises et l'ouverture aux contributions savantes.
- Ajouter que les prochaines etapes ne consistent pas seulement a "mettre plus de donnees", mais a raffiner les controles, les connecteurs et les usages de recherche.

## Slide 30 - Une infrastructure portable

- Dire clairement que le libre arbitre est ici un cas d'usage exigeant, presque un stress test.
- L'architecture generale reste la meme : un corpus, une couche de structuration, puis un moteur de raisonnement contraint par les sources.
- Utiliser les exemples DOMUS pour montrer que cette logique peut servir des editions critiques, de l'archeologie, de l'histoire religieuse ou de l'histoire des savoirs.
- Conclure que la vraie question n'est donc pas "faut-il un chatbot pour mon projet ?", mais "comment construire une IA qui lise a partir de mes sources et de mes categories savantes ?"

## Slide 31 - Merci

- Terminer en revenant a une formule simple : EleutherIA n'est pas une machine a reponses, c'est une infrastructure de lecture augmentee.
- Inviter a tester la plateforme, regarder le DOI, ou venir discuter de la portabilite a d'autres corpus.
- Si tu veux finir sur une phrase un peu plus forte : l'enjeu n'est pas de faire parler l'IA a la place des textes anciens, mais de lui apprendre a nous y reconduire.
