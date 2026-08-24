# Revue indépendante Hildebrandt P0 - v2

Date: 2026-08-24  
Portée: re-revue contradictoire en lecture seule du successeur code-only du
tuple v1. Aucun `--write` n'a été exécuté; aucune donnée KG, corpus, registre,
manifeste, bibliographie ou audit n'a été modifiée.  
Verdict: **PASS pour ce tuple gelé; aucun blocker résiduel identifié**.

## 1. Tuple exact

| Artefact | SHA-256 contrôlé |
|---|---|
| Applier | `bea75e158dd0417222ea9135479e38db426d49c92d4f864f337996035f4a7b9b` |
| Tests | `90ab962b79b783e0470cdb4e6e3c4a6f57742d8167d5dd402b8cd5022e9c0119` |
| Preview `/tmp/hildebrandt-p0-v2-final.json` | `608339b2008f97ca201b0b40f0ab7c382f110afbc3ac8a449c565fd3d22a01d4` |
| Revue v1 | `e585e44f31cc2bff81a278bbc21cac7ff7cd3167cb1cd8a314181fcf6414cd95` |
| PDF local | `3a632d61028344ffcba880cebdc6678cfaa22ba456956f55715279928c749717` |

La revue v1 reste **FAIL - NO APPLY** pour son ancien tuple
`4c9b18b7...5efdc1` / `41b5c816...f28b`. Le présent PASS est strictement borné
aux hashes ci-dessus et ne réécrit pas ce verdict historique.

## 2. Delta v2 borné et reproductibilité

Les trois seuls défauts v1 étaient statiques. Le successeur applique exactement
les corrections demandées:

1. `dict.fromkeys(POSITION_IDS, SCHOLAR_ID)` remplace la compréhension signalée
   par `C420`;
2. l'import de test `copy` inutilisé signalé par `F401` est supprimé;
3. la comparaison de test signalée par `SIM300` est remise dans l'ordre usuel.

Le dry-run v2 `--json` a le SHA-256
`608339b2008f97ca201b0b40f0ab7c382f110afbc3ac8a449c565fd3d22a01d4`.
Il est byte-identique au preview v1 (`cmp` retourne 0). Il n'existe donc aucun
delta savant, bibliographique, transactionnel, de touched-set ou de bytes de
sortie entre les deux previews. Restent notamment inchangés:

- exactement 10 noeuds, 8 arêtes et 4 citations modifiés;
- aucune ligne de passage corpus modifiée;
- exactement 12 sorties planifiées et 41 entrées de quarantine;
- registre normatif `41 -> 41`, zéro erreur nouvelle;
- zéro record de vérification ajouté;
- revues indépendante, adversariale et sign-off humain non inventés dans les
  données du candidat;
- BibTeX/report, manifestes, before-images, journal, rollback, récupération et
  idempotence identiques au candidat déjà audité.

## 3. Autorité PDF et portée savante reconfirmées

Le fichier local a toujours 343 020 octets, 20 pages A4, PDF 1.6, n'est pas
chiffré et passe `qpdf --check`. Son hash est inchangé. Un nouveau rendu visuel
représentatif des PDF 1, 18 et 20 reconfirme:

- Ronja Hildebrandt et le titre exact *Alexander of Aphrodisias' Lazy Arguments
  against Stoic Determinism*;
- volume 15, pages imprimées 25-44 et DOI `10.12697/spe.2022.15.01`;
- la mention `All Copyright Author`, sans licence explicite de réutilisation;
- la formulation bornée sur l'absence de réponse transmise, puis la continuité
  complète de la bibliographie jusqu'à la page 44.

Ces constats concordent avec la
[notice officielle](https://ojs.utlib.ee/index.php/spe/article/view/22849) et
avec la revue visuelle intégrale v1. Les rendus temporaires v2 ont été supprimés.
Le preview, inchangé, continue donc correctement à supprimer le contact du noeud
public, à dater les affiliations, à conserver les surclaims en revue et à
traiter les droits de façon prudente.

## 4. Gates rejoués

```text
ruff check scripts/apply_2026_08_24_hildebrandt_p0_repair.py \
  tests/test_hildebrandt_p0_repair.py
PASS

PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_hildebrandt_p0_repair.py
18 passed

PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/test_check_corpus_invariants.py \
  tests/test_snapshot_passage_integrity.py \
  tests/test_check_kg_corpus_locus_parity.py \
  tests/test_check_kg_work_id_uniqueness.py \
  tests/test_derive_corpus_manifest.py \
  tests/test_literature_acquisition_manifest.py \
  tests/test_scholarly_sources_manifest.py \
  tests/test_audit_sota_registry.py \
  tests/test_export_publications_bibtex.py
32 passed

PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/test_check_kg_work_child_canonical.py
10 passed
```

Le warning pytest relatif à une option de configuration inconnue est hérité et
n'affecte aucune assertion. Le dry-run live est resté en mode
`ready_for_independent_review_no_apply`, `write_performed=false`.

## 5. Absence de write et décision

Les artefacts Hildebrandt report/quarantine, le lock, le journal et les backups
restent absents du dépôt réel. Le PDF, les douze entrées Snapshot-A et le preview
ont conservé leurs hashes. Les tests d'écriture ont opéré uniquement sur leurs
copies temporaires.

Décision: **PASS** pour le tuple v2 de la section 1. Les trois blockers lint de
la revue v1 sont fermés, le preview est strictement inchangé et aucun nouveau
blocker n'a été trouvé. Ce verdict n'est ni une application des données ni une
autorisation implicite d'étendre la transaction; l'éventuel apply reste une
décision séparée de root.
