# Registre SOTA d'exhaustivité savante

Ce répertoire est la source de vérité **machine-readable** de la boucle
d'exhaustivité d'EleutherIA. Les rapports historiques de `data/audit/`, le
manifeste de `data/scholarly_sources/`, les fichiers du KG et les notes de
lecture restent des preuves d'entrée ; aucun d'eux ne suffit, isolément, à
déclarer le corpus exact ou exhaustif.

Le mot « exhaustif » a ici un sens opérationnel et daté. Un univers
bibliographique ouvert ne permet pas de prouver qu'aucune publication future
ou inconnue n'existe. Le registre peut seulement atteindre l'état
`operationally_exhaustive_as_of` lorsque le protocole de clôture est satisfait.
Toute nouvelle édition, publication, variante textuelle ou objection savante
rouvre automatiquement la cellule concernée.

## Fichiers canoniques

- `scope.json` fixe les bornes, règles d'inclusion, facettes obligatoires,
  cellules de recherche et protocole de saturation.
- `registry/sources/*.jsonl` inventorie les œuvres anciennes, leurs témoins et
  éditions, ainsi que la bibliographie secondaire. Un fichier par vague est
  préféré pour permettre le travail parallèle sans conflit.
- `registry/evidence/*.jsonl` porte les unités atomiques : une proposition,
  un locus ou un empan de pages, ses cibles KG et son statut de publication.
- `registry/issues/*.jsonl` porte erreurs, risques factuels, variantes et
  arbitrages. Une issue résolue conserve la décision et ses preuves.
- `registry/verifications/*.jsonl` est un journal append-only. Les anciennes
  vérifications ne sont jamais réécrites ; une révision est un nouvel événement.
- `registry/waves/*.jsonl` décrit la file priorisée. Une seule vague est `next`.
- `exit_gates.json` définit les conditions cumulatives de sortie.
- `registry.schema.json` est le contrat JSON Schema 2020-12 des enregistrements.

Les identifiants sont stables et ne codent pas un statut mutable : `src_*`,
`ev_*`, `issue_*`, `ver_*`, `wave_*`, `cell_*`, `gate_*`.

## Invariants anti-hallucination

1. Une entrée `candidate` n'est jamais ingérable dans le KG.
2. Une source ancienne abstraite doit être distinguée de son témoin ou de
   son édition. L'absence dans le corpus n'est jamais une preuve de fabrication.
3. Une unité ancienne exige un locus canonique et un témoin nommé. Une citation
   verbatim exige aussi un hash du texte collationné ou un identifiant de
   passage corpus ; aucune restitution grecque ou latine n'est produite par le
   registre.
4. Une affirmation secondaire exige les pages imprimées. La pagination PDF
   est enregistrée séparément et la correspondance doit être vérifiée
   visuellement.
5. `verified` ou `published` exige deux vérificateurs distincts, appartenant à
   deux groupes d'indépendance distincts, plus une passe adversariale.
   Relire deux fois le même OCR, ou employer deux agents issus du même prompt
   et de la même extraction, ne constitue pas deux preuves indépendantes.
6. Une issue factuelle ouverte bloque la sortie, quelle que soit sa sévérité.
   `adjudicated` ne ferme l'issue qu'avec une décision, des preuves et une double
   revue indépendante.
7. Les pourcentages de couverture ne sont jamais saisis à la main. L'audit les
   dérive du registre et du snapshot KG courant.
8. « Zéro erreur » signifie « zéro erreur factuelle connue après les gates
   définis », jamais une garantie métaphysique d'infaillibilité.

## Cycle de travail persistant

1. **Discover** — exécuter les recherches documentées de chaque cellule,
   conserver requêtes, dates, index consultés, résultats et exclusions.
2. **Register** — ajouter chaque source, même inaccessible, avec une décision
   de périmètre explicite. Les doublons sont reliés, jamais effacés en silence.
3. **Acquire and fingerprint** — identifier l'édition exacte, archiver ou
   référencer l'artefact licite, enregistrer SHA-256 et carte des pages.
4. **Read atomically** — créer une unité par claim/locus/empan, en distinguant
   texte transmis, paraphrase, reconstruction et interprétation moderne.
5. **Verify twice** — collation textuelle ou lecture de page, puis vérification
   indépendante de l'identité, du sens, de l'attribution et de la portée.
6. **Refute** — une passe adversariale cherche activement le contre-témoignage,
   les variantes, les homonymes, les anachronismes et les glissements de page.
7. **Stage, test, publish** — le KG n'est modifié qu'après les gates locaux ;
   les cibles publiées sont ensuite re-lues depuis le snapshot déployable.
8. **Recompute** — l'audit choisit la prochaine vague non bloquée au score le
   plus haut. Si tous les gates passent, deux signataires humains datent la
   clôture ; tout trigger de réouverture relance l'étape 1.

## Audit en lecture seule

```bash
python3 scripts/audit_sota_registry.py
python3 scripts/audit_sota_registry.py --format json
python3 scripts/audit_sota_registry.py --require-exit-gates
```

Le premier appel retourne 0 si le registre est structurellement valide, même
s'il reste du travail. `--require-exit-gates` retourne 2 tant que la clôture
SOTA n'est pas démontrée. Une erreur de structure ou de référence retourne 1.
Le script ne modifie aucun fichier et ne lance aucun audit externe.

Tests ciblés :

```bash
python3 -m pytest tests/test_audit_sota_registry.py
```

## Règles de contribution multi-agent

- Créer un nouveau shard au nom de la vague ou de l'agent ; ne pas réécrire
  le shard d'un autre agent pendant qu'il travaille.
- Enregistrer le constat avant toute mutation du KG.
- Ne jamais passer soi-même une unité de `candidate` à `verified` : les
  événements de vérification sont les preuves, l'audit calcule l'éligibilité.
- Tout conflit savant devient une issue `disputed_interpretation`; il n'est pas
  aplati en un unique « fait ». Le KG doit attribuer chaque position.
- Une correction invalide les vérifications dont les hashes ou locators ne
  correspondent plus et exige une nouvelle passe.

