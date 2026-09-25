# Retrait des 29 lignes « Fédou 2026 » contaminées — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_fedou_bulletin_withdrawal.py` (décisions) et `scripts/apply_2026_09_24_fedou_bulletin_withdrawal.py` (application).
Décisions : `data/audit/2026-09-24_fedou_bulletin_withdrawal_decisions.jsonl`. Enregistrements retirés, intégralement conservés : `data/audit/2026-09-24_fedou_bulletin_withdrawal_quarantine.jsonl`.

## Ce qui a changé

- 29 nœuds `publication` `pub_fedou_2026_*` retirés de `data/kg/nodes.jsonl`.
- Leurs 58 arêtes retirées de `data/kg/edges.jsonl` : pour chaque nœud, exactement `discusses → concept_autexousion_christian_freedom_u1v2w3x4` et `discusses → person_origen_alexandria_185_254ce_s9t0u1v2`.
- Aucune citation de corpus, aucun pointeur de métadonnées ne visait ces ids (vérifié par le script avant écriture).

## Pourquoi

Chaque ligne a pour titre un livre recensé dans un bulletin bibliographique (Réforme aux Pays-Bas, Levinas, musiciens d’église, accord Poincaré-Cerretti, « Ouvrages analysés », « Pages de fin »…) et pour description le même résumé du *Traité sur la prière* d’Origène dans l’édition Vigne : 28 fois en français, une fois en espagnol. Exemple : titre « Kooi C., La Réforme aux Pays-Bas, 1500-1620 », description « Le Traité sur la prière d’Origène, désormais accessible dans l’édition critique et la traduction de Daniel Vigne… » (“Origen’s Treatise on Prayer, now available in Daniel Vigne’s critical edition and translation…”). Les deux arêtes `discusses` sortent de ce résumé, pas du livre recensé. L’auteur « Michel Fédou » est celui de la notice OpenAlex du bulletin : il n’est pas l’auteur des livres (Barth, Maritain, Teilhard, Taguieff…).

Le cold audit du 17 août (`data/audit/2026-08-17_cold_audit_sol.md`, H-01) les avait déjà jugées « Incorrect » et marquées `integrity_status`, sans toucher au texte public ni aux arêtes. Elles restaient donc servies au lecteur et parcourues par le graphe. Aucune ne peut être réparée sans lire le bulletin lui-même, inaccessible depuis cet environnement : je les retire.

## Contrôles

Préconditions revérifiées à l’exécution (statut d’intégrité, résumé *De oratione* toujours présent, titre non consacré au *De oratione*, arêtes limitées aux deux cibles dérivées). Invariants vérifiés avant écriture. Relance : no-op. Portes : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness` OK. `gen_stats.py` et `export_publications_bibtex.py` régénérés.

Artefact dérivé non régénéré ici : `frontend/src/assets/atlas-full-layout.json` contient encore ces ids (mise en page précalculée). À régénérer au prochain build.

## needs_romain

- Deux des livres recensés concernent le corpus et mériteraient une vraie notice, **si** le bulletin le justifie : K. Barth, *Destin et idée dans la théologie* (Paris, Ad Solem, 2025 ; trad. fr. de « Schicksal und Idee in der Theologie ») et É. Junod (dir.), *L’affaire Origène* (Les Pères dans la foi 113, Paris, Migne-Cerf, 2025). À vérifier : l’auteur réel de chaque recension, la revue, le fascicule et les pages (notices OpenAlex W7143270037 et W7147037525).
