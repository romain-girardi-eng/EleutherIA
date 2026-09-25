# C2 : descriptions qui ne portent pas sur leur entité — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_identity_mismatch.py` et `scripts/apply_2026_09_24_identity_mismatch.py`.
Décisions : `data/audit/2026-09-24_identity_mismatch_decisions.jsonl` (33 enregistrements).

## Résultat

| Verdict | N |
|---|---|
| `removed` : lignes du bulletin Fédou 2026, déjà retirées par le lot `fedou_bulletin_withdrawal` | 28 |
| `corrected` | 1 |
| `false_positive` | 4 |

**`pub_cohen_2010_sabbath_law_and_mishnah_shabbat_in_origen_de_principiis`.** OpenAlex avait fourni comme résumé de cet article du *Jewish Studies Quarterly* (DOI 10.1628/094457010791339792) le texte de promotion d'un commentaire de la Loi fondamentale allemande : « Besseres lässt sich von einem Verfassungskommentar nicht sagen », Staatsanzeiger für das Land Hessen 2018 (« On ne peut rien dire de mieux d'un commentaire constitutionnel »). Ce texte passe dans `metadata.abstract_rejected_2026_09_24`. La description est reconstruite uniquement à partir des champs bibliographiques vérifiés de la notice : auteur, titre, revue, année et DOI.

Un contrôle sur les 120 résumés importés n'a trouvé aucun autre cas. Aucun résumé n'est partagé entre deux notices, et aucun ne ressemble à une réclame d'éditeur.

`needs_romain` : la notice Cohen porte `language: de` et une cohorte de citation « de », alors que le titre est en anglais. C'est à vérifier.

## Contrôles

- Relance : aucune modification.
- Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict`, `check_kg_work_child_canonical`.
