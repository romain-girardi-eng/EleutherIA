# Notes de curation dans les descriptions publiques — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_curator_notes.py` et `scripts/apply_2026_09_24_curator_notes.py`.
Décisions : `data/audit/2026-09-24_curator_notes_decisions.jsonl` (146 enregistrements).

## Périmètre

La file C2 `queue_b_curator_notes.csv` signale 141 descriptions qui se lisent comme des notes de curation. Je n'ai appliqué que les corrections possibles sans réécrire de prose savante. Aucune note n'est supprimée : chaque texte retiré d'une description est conservé tel quel dans `metadata.curator_note_2026_09_24`.

## Corrections (16 nœuds, dont 5 hors file présentant le même défaut)

- **14 arguments savants dont toute la description était une note de vérification.** Ces descriptions commençaient par « Not verifiable in the fonds… », « Faithful as written; only the page… », « No corresponding argument in Dunn… » ou « [pending-acquisition: …] ». La position du savant, déjà présente dans `metadata.stance`, devient la description. Pour les 9 nœuds dont l'audit savant du 2026-08-29 conclut `NOT_FOUND`, `SOURCE_ABSENT` ou `DISTORTED`, la position est marquée `citability: discoverable_only`, pour qu'elle ne soit plus citée comme preuve. Ce sont les nœuds Engberg-Pedersen (3), Wolfson (4), Bobichon et Dunn.
- **`scholar_wolfson_h`.** Une modification tronquée avait laissé dans la description un fragment de consigne (« …') and clutters the scholarly content; it should ] »). La description est ramenée à son préfixe intact, identique à `metadata.specialty`.
- **`pub_lienemann_2012_review_frede`.** La description publique se terminait par un chemin de fichier privé (« Texte intégral acquis : [local-path] … »). Cette phrase passe en métadonnée.

## `needs_romain` (130)

Dans les 130 autres descriptions, les remarques de curation sont mêlées à la prose savante. On y trouve :

- des avertissements de formulation (« WORDING WARNING »), des « (sic …) » et des « NOT HELD LOCALLY » ;
- des remarques sur l'état du PDF, des loci « to be checked » et des mentions internes (« Volume majeur pour la thèse Romain »).

Les séparer oblige à réécrire le texte, ce qui revient à l'auteur.

## Défaut systémique

La balise `[local-path]` subsiste dans les métadonnées de 1391 nœuds (`source_file`, `source_files`). Si l'API expose les métadonnées, il faudrait les filtrer à l'export plutôt que dans les données.

## Contrôles

- Relance : aucune modification.
- Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict`, `check_kg_work_child_canonical`.
- `check_snapshot_passage_integrity` : ensemble des violations identique à celui du commit de base.
