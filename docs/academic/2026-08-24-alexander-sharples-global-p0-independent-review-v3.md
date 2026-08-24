# Revue independante finale du P0 Alexander-Sharples v3

Date: 2026-08-24  
Relecteur: agent `/root/long_sedley_pdf_audit`, distinct de l'auteur du rebase.  
Portee: revue contradictoire du tuple v3 post-Hildebrandt et post-Tatien,
strictement sans ecriture des donnees.  
Verdict: **PASS - READY FOR ROOT DECISION; NO APPLY PERFORMED**.

## 1. Tuple exact revu

| Artefact | SHA-256 controle |
|---|---|
| Applier | `1e740dbbec59ccac951468ecee6ec6f7016ea57e72c3c6e71fc96f48780ba6dd` |
| Tests cibles | `daa919764e6cd0bd65c40e4a71e84f20734ddc84ec7b6b2899fd5877781be31d` |
| Audit savant corrige | `7c1fbfcbabb5904c0a35818c5927c8f92913b05feaaf75fe19bbd9ad415efce0` |
| Revue semantique v2 | `1dada7cdccd0f4384c21d33dd7cb24969cb9781507d6355aebe448281b1c7f25` |
| Preview Markdown v3 | `11cea6220b85371aec28f0881f82ca7c91d7f737e44ea079eaa116a32805c0f0` |
| JSON dry-run v3 | `a503f6a0f7393875d49cafdc2a1faa3dedf387d3697463ce7faac74e5ee7b317` |

Le dry-run live `--json`, rejoue pendant cette revue, est byte-identique au JSON
gele, sans sortie stderr. Son statut est
`ready_for_independent_review_no_apply`, `write_performed=false`.

La source visuelle reste le scan Sharples SHA-256
`7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638`.
L'OCR `ec154e4d...27ebb` n'a servi qu'a la navigation. Le TEI Bruns/OGL a le
SHA-256 `184b01f3...bb2f`.

## 2. Base post-Hildebrandt et post-Tatien - PASS

La racine live correspond exactement aux douze before-images v3:

| Surface | SHA-256 before |
|---|---|
| nodes | `60082c52cddfa3e5441a2ae491af2d9c00c386f4f9ed8a8c4b836390a4e24f83` |
| edges | `2e417ac429988f1df282fbb0576f34b51e327479d0043738b9cf073715de6b72` |
| citations | `3aea9ad22b6fe42c78429ce68fbb041c57d532e530463a01b18353d7c11a9c64` |
| passages, read-only | `e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3` |
| corpus manifest, read-only | `2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e` |
| BibTeX | `e4cc9a15bdbe756446518a09f9a97f9405c98a7b54886de39afc07892941c44a` |
| rapport BibTeX | `7612db557443d1c6c27507a130aa283a115e8a765075b297a7c019ef6104b68a` |
| manifeste savant | `33f304aee1a3882c75f47e212bae778e64c23da6cb9f39cda0790416f0c9e9b6` |
| registry sources | `cc34488366f86d56726e99c1113195f2e8c128f2f44f2b1535d0dabdcd8cf7ac` |
| registry evidence | `90aaa8fab0d4c5fbbb830b60f38d992514b6d5a512a0698397042cc090aa2307` |
| registry issues | `5dca524033ebe628d5d9cd3431ebeddd9e8830314e430440d057a22e73d8ef17` |
| wave dediee | absente |

Les rapports et quarantaines Hildebrandt/Tatien sont hash-gates et restent
hors outputs. Les quatre empreintes durables correspondent au preview. Aucun
record de ces vagues n'est absorbe silencieusement par le rebase.

## 3. Egalite semantique v2/v3 - PASS

La comparaison independante des JSON v2 et v3 donne une egalite exacte pour:

- les 13 compteurs;
- les 15 IDs de noeuds touches;
- les 56 IDs d'aretes touches, soit 55 suppressions et 1 modification;
- les 33 cles de citations touchees, soit 31 retrogradations et 2 suppressions;
- tous les after-record hashes;
- les 14 intervalles evidence et 24 intervalles argument;
- les 10 chemins de sortie;
- les 2 issues ouvertes, les statuts de revue et les 126 before-images de
  quarantine.

Le digest canonique de cette projection semantique est identique v2/v3/live:
`c01cad11903eba7e8265e7ef6254f425384831ce5da008ef6154d329d59fc8c2`.
Les seuls champs top-level differents sont les six familles attendues d'un
rebase: before-record hashes, outputs globaux, dependances read-only, metriques
d'integrite, baseline mesuree et artefacts de provenance.

Lignes JSONL hors cohorte Sharples: byte-identiques. La recomputation trouve
exactement 15 lignes nodes changees, 56 lignes edges touchees et, parce qu'une
modification de `citation_type` change aussi la cle brute, 64 operations de
ligne correspondant aux 33 citations semantiques declarees.

Les six noeuds Long/Sorabji et `argument_agent_causation_alex` sont raw-byte
identiques avant/projection. Les digests de preservation calcules pendant la
sous-revue sont egalement identiques pour 34 identites Hildebrandt et 57
identites Tatien. L'entree BibTeX et la ligne de manifeste Hildebrandt restent
inchangees.

Verdict rebase: **PASS**.

## 4. Portee savante - PASS

La correction conserve exactement la portee deja approuvee en v2:

- 11 reconstructions fortes deviennent `discoverable_only`;
- les noeuds de texte direct, de position stoicienne rapportee et de taxonomie
  moderne Sharples restent separes;
- les 55 groundings forts non soutenus sont retires;
- les 31 citations non exactes deviennent `related_passage_non_exact` et deux
  faux snapshots de *De fato* 15 disparaissent;
- Sharples reste une traduction/commentaire Duckworth 1983 avec fac-simile
  photographique Bruns, non une nouvelle edition critique;
- 14 evidence records restent `in_review` et `paraphrase_only`;
- deux issues restent `OPEN`, la wave dediee reste `blocked`;
- aucun agent ultime non cause, substance-cause ou conclusion libertarienne
  forte n'est promu en attestation directe d'Alexandre;
- aucun PASS independant, adversarial ou humain n'est invente dans le registre.

Le present rapport est une revue independante reelle du tuple; le fait que le
preview n'ajoute aucun record de verification reste donc correct et fail-closed.

## 5. Page maps et controle visuel - PASS

La regle du scan a doubles pages est bien:

```text
PDF = floor(page imprimee / 2) + 5
```

Elle derive, plutot que recopier, 14 intervalles evidence et 24 intervalles
argument. Les pages decisives ont ete rendues de nouveau a partir du scan:

| Dossier | Imprimees | PDF | Controle |
|---|---:|---:|---|
| SHA-01 | 19-21 | 14-15 | identite et analyse introductive |
| couche deliberation | 56-60 | 33-35 | traduction continue *De fato* XII-XIV |
| SHA-06 / SHA-09 | 146-149 | 78-79 | commentaire sur origine, causalite et responsabilite |
| transition | 150-151 | 80 | continuite intermediaire |
| SHA-12 | 152-153 | 81 | commentaire causal de *De fato* XXII |

Les numeros imprimes visibles correspondent exactement aux plages annoncees;
aucun OCR n'a ete traite comme autorite. Les rendus temporaires ont ete
supprimes.

## 6. Outputs, schema et gates - PASS

Les outputs sont exactement dix:

| Sortie prospective | SHA-256 |
|---|---|
| nodes | `92a0cd13dcab0d1749119e8ef0b772392e7920177096213deca2906e88821817` |
| edges | `b1ce4f5e594d846c0d64ad1a33b4e0b0970230c11641010df8ea9b58e8ebfd2a` |
| citations | `5bd6657adb6aa006bc12a33285c399e00fc7ab467932b603369e119bdc9e089a` |
| BibTeX | `3e21f88fe06e9e61d7444f724d66a1eabdadd2af27ec42dca22bd8651e94b825` |
| rapport BibTeX | `bba25a9d4d57dd9f82fe1eeb4b410f262312050345fb27fc9fb4b7cce2478e69` |
| manifeste savant | `c16553ff02c6cfdcd8402551bcd128fcf8cf0f6d5855a7b38d0be670fbe2a42e` |
| registry sources | `511a4550dd3d61c36e5fa2b85fb0e0ad66f055141ba5ee4829256b62ea2e7d46` |
| registry evidence | `165e13fb58e951c76b2efbdcfa17c1938166677af8f60b1d8e2fa5390d84c23c` |
| registry issues | `188a746de924bf4086ecf66bbd812a332095e7c03e4b6f4d7b72034a93c0c509` |
| wave dediee | `76d3182a9c027e6272e46d6ed9a8c3a1b235e688963e4c05f38c0479ff264405` |

Les passages et le manifeste corpus sont deux dependances read-only, jamais des
outputs. Le registre normatif reste `41 -> 41`, zero erreur nouvelle, zero
erreur supprimee et zero erreur sur les nouveaux records. Le registre custom
reste structurellement valide.

Gates prospectifs:

```text
new snapshot fingerprints  0
new corpus violations      0
parity shared checked      13844
parity violations          0
work-child mismatches      0
work-ID collisions         0
strict debt before         1152 BLOCK / 760 WARN
strict debt after          1151 BLOCK / 759 WARN
new strict debt            0
```

## 7. Transaction et postwrite - PASS

Les tests et l'inspection du code confirment:

- gates Snapshot-A avant staging et avant commit;
- verification immediate de chaque cible avant remplacement;
- dependances corpus recontrolees sans devenir outputs;
- classification `before` / `after` / `foreign` avant restauration;
- refus d'ecraser les bytes etrangers, avec journal/backups durables;
- hard crash apres remplacement et rollback de reprise;
- echec de rollback conservant le materiel, puis seconde recuperation;
- full shadow apply aux hashes after, postvalidation complete, second plan
  `already_applied`, puis repeat write byte-noop;
- double approbation obligatoire pour un write sur la racine.

Les suites exactes rejouees sur ce tuple sont:

```text
tests/test_alexander_sharples_global_p0.py                  25 passed
global corpus/snapshot/parity/work/registry                 36 passed
tests/test_alexander_agent_causation_recollation.py          7 passed
ruff                                                        PASS
```

Le warning pytest sur une option de configuration inconnue est herite et
n'affecte aucune assertion.

## 8. Dette Long-Sedley externe

`tests/test_long_sedley_vol2_p0_repair.py` est stale apres les vagues
Hildebrandt et Tatien parce qu'il exige encore d'anciens hashes whole-file pour
edges et BibTeX. Cette dette de harness est reproduite et deja reservee pour une
correction test-only composable. Elle n'affecte ni le touched-set Sharples, ni
les records Long effectivement preserves, ni les gates Sharples. Elle n'est
donc **pas** un blocker du present tuple et ne justifie aucun relachement de ses
preconditions.

## 9. Absence de write et decision

Sur la racine live restent absents:

- rapport et quarantine Sharples appliques;
- lock, journal et backups Sharples;
- wave Sharples dediee.

Tous les hashes du tuple de la section 1 sont restes stables apres les tests.
Aucun `--write`, deploiement ou mutation distante n'a ete execute.

Decision finale: **PASS** pour ce tuple v3 exactement. L'application eventuelle
reste une decision distincte de root et ne doit utiliser aucun tuple anterieur.
