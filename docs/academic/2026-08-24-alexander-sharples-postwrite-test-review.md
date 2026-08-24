# Mini-revue du delta test-only Sharples postwrite

Date: 2026-08-24  
Portee: diff test-only apres application autorisee du P0 Sharples; aucune
ecriture de donnees pendant cette revue.  
Verdict: **PASS**.

## Tuple controle

| Artefact | SHA-256 |
|---|---|
| Test avant | `daa919764e6cd0bd65c40e4a71e84f20734ddc84ec7b6b2899fd5877781be31d` |
| Test apres | `81aca8d231234ff927aa121c36a4eaf4de036c1f916349dcc9f8f333289c18aa` |
| Applier inchange | `1e740dbbec59ccac951468ecee6ec6f7016ea57e72c3c6e71fc96f48780ba6dd` |
| Report applique | `98b9b76ebe1a6f2f608ef52cdc6f7b0d7c96bfb675a0087656859fbba2a6733b` |
| Quarantine appliquee | `bc6fa40a1cd461dfe13550d26a03d750aa42c41233c316af608fa3c0ff7d8d63` |

Une reconstruction byte-exacte du test avant a ete controlee au hash attendu.
Le diff exact `/tmp/sharples-test-postwrite-daa919-to-81aca8.patch` a 19 lignes
et le SHA-256
`5160c0780f33a586a2fdaa71f47c6092c5fdf1e537bbbed388ab7a69c1027033`.

## Delta exact

La seule modification est dans `make_shadow_repo()`:

- le report et la quarantine Sharples persistants sont identifies comme les
  deux artefacts d'audit de l'etat `after`;
- ils sont copies dans la shadow postwrite au lieu d'etre omis avec le lock,
  le journal et les backups;
- tous les autres enfants de `data/audit` gardent la politique precedente;
- le lock, le journal et les backups demeurent exclus.

Aucun compteur, ID attendu, touched-set, hash before/after, page map, gate de
schema, gate corpus/snapshot/parity/work, contrat transactionnel ou assertion de
review n'a ete modifie. Le changement fournit seulement a la copie `after` les
deux artefacts que `build_plan()` exige legitiment pour reconnaitre
`already_applied`.

## Verification

```text
tests/test_alexander_sharples_global_p0.py  25 passed
ruff check test file                       PASS
```

Les hashes data postwrite controles restent ceux du tuple applique: nodes
`92a0cd13...21817`, edges `b1ce4f5e...bfd2a`, citations
`5bd6657a...e089a`, BibTeX `3e21f88f...b825` et rapport BibTeX
`bba25a9d...8e69`.

Decision: **PASS** pour le delta test-only `daa919... -> 81aca8...`. Aucun
fichier data, applier, registre ou manifeste n'a ete modifie par cette revue.
