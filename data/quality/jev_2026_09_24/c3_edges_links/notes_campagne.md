## Campagne C3 — arêtes sémantiques du KG (validation) et liens manquants vers les concepts

24/09/2026 — via Jev (Vercel AI Gateway, `typesafe-ai/jev`), fenêtre gratuite. Jugements = preuves pour adjudication humaine ultérieure, aucune écriture dans `data/kg/*`.

### Ce qui a été demandé

**Partie A — validation des arêtes existantes.** 23 relations non-structurelles avec ≥ 30 arêtes chacune (`authored_by`, `part_of`, `has_section`, `has_chapter`, `translation_of`, `member_of`, `created_by`, `advanced_in`, `belongs_to_corpus` exclues comme structurelles). Pour chaque arête, deux booléens dans un seul appel : un gabarit littéral propre à la relation (ex. pour `cites_primary_source` : « la cible est une source primaire ancienne dont le texte ou le contenu est explicitement cité comme preuve par la source ») et un booléen générique de comparaison (« la relation, telle que décrite, tient entre les deux entités »).

**Partie B — propositions de liens manquants vers les concepts.** Pour chaque nœud `argument` (1 676), `work` (251), `publication` (419), `person` (401) et `synthesis` (155) avec une description ≥ 60 caractères (2 902 nœuds au total), un booléen contre chacun des 212 concepts du KG, par lots de 55 concepts/appel : « Ce <type>, tel que décrit, traite explicitement du concept : <libellé>. <glose> ». Aucune question sur la position doctrinale (libertarien/compatibiliste/…), uniquement « traite du concept ».

### Couverture et coût — Partie A

- **9 688 / 9 688 arêtes traitées** (100 %), 0 échec net — 104 réponses ont d'abord échoué sur des 429/503 (charge partagée sur la gateway), toutes récupérées par un runner auto-cicatrisant (`heal_edges.sh`, relance jusqu'à convergence).
- **19 376 jugements** (2 par arête). Coût réel : 0 $ (fenêtre gratuite ; `marketCost` cumulé négligeable).
- Latence médiane par appel ≈ 300-500 ms.

Distribution de `p_specific` (le booléen littéral, celui qui compte) par palier de confiance :

| Palier | N | % |
|---|---|---|
| ≥ 0,9 | 3 844 | 39,7 % |
| 0,7–0,9 | 2 555 | 26,4 % |
| 0,3–0,7 | 1 870 | 19,3 % |
| ≤ 0,3 | 1 419 | 14,6 % |

Statistique complète par relation dans `stats_by_relation_A.csv`. Deux points saillants :

- **`engages_with` (person→person, 302 arêtes)** est la relation la plus fragile : moyenne `p_specific` = 0,26, 88 arêtes (29 %) avec les deux booléens ≤ 0,3. En croisant avec les métadonnées de `data/kg/edges.jsonl`, une bonne partie de ces arêtes porte déjà `"needs_review": true` ou vient de vagues d'import bibliographique automatique (`furst_audit_full_2026_05_18`) — le jugement de Jev recoupe un doute déjà enregistré dans le graphe, ce n'est pas un désaccord isolé.
- **`discusses` (5 311 arêtes, la plus grosse relation)** reste globalement solide (moyenne 0,765) mais porte 265 arêtes ≤ 0,3 des deux côtés, concentrées sur les paires `passage → concept` où la balise semble avoir été posée au niveau de l'œuvre entière plutôt que du passage précis (voir exemples ci-dessous).

### Couverture et coût — Partie B

*(complété à la fin du run — voir `results_B.jsonl`, `stats_by_type_B.csv`, `stats_by_concept_B.csv`)*

### Exemples vérifiés (lecture directe du texte, pas seulement le score)

1. **Faux positif net** — `discusses` `passage_aug_lib_arb_2_8_23` (Augustin, *De Libero Arbitrio* 2.8.23) → `concept_voluntas_y7z8a9b0` (Will/Voluntas), p = 0,03/0,09. Le passage lu en entier ne parle que de la loi immuable des ratios mathématiques (« certissima et incommutabili lege », le double de 2 est 4, etc.) — un jalon de la preuve épistémologique du livre II, pas une discussion de la volonté. Même diagnostic pour `passage_aug_lib_arb_2_7_18` (le toucher) et `_2_8_21`/`_2_8_22` (les nombres) : quatre arêtes `discusses → Voluntas` posées sur des passages qui traitent de mathématique/sensation, probablement héritées du tag de l'œuvre entière (*De Libero Arbitrio* porte bien sur la volonté) plutôt que du passage.
2. **Faux positif net** — `evidenced_by` `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` (τὸ ἐφ' ἡμῖν) ← `passage_aristide_sc470_1` (Aristide d'Athènes, *Apologie* SC 470), p = 0,14/0,26. Le passage cité est une critique du polythéisme grec (Aphrodite adultère, etc.) — aucune trace du vocabulaire de l'ἐφ' ἡμῖν.
3. **Arête `engages_with` fabriquée par appariement bibliographique** — `scholar_jaubert_a` (Annie Jaubert, exégèse judéo-chrétienne, Clément de Rome) → `person_fischer_john_martin_3w4x5y6z` (John Martin Fischer, compatibilisme contemporain analytique), p = 0,01/0,08. Deux champs disjoints (patristique du 1er siècle vs. métaphysique analytique du XXe), aucun engagement plausible.
4. **Vrai positif solide, pour contraste** — `cites_primary_source` `argument_agent_causation_alex` → `passage_alex_fat_12` (Alexandre d'Aphrodise, *De Fato* 12), p = 0,98/0,74 : l'argument sur la causation par l'agent cite bien ce chapitre du *De Fato* comme texte source, cohérent avec la description.
5. **`has_position` faible (moyenne 0,437, 49 arêtes)** — relation courte et à surveiller : `debate → position` où le texte de la position ne recoupe pas toujours le débat déclaré ; échantillon dans `queue_A_weak.csv`.

*(exemples Partie B ajoutés ci-dessous après complétion du run.)*

### Limites connues

- Jev est peu fiable sur l'arithmétique, le comptage, les dates, le multi-hop et les questions très larges — aucune question de ce type n'a été posée (uniquement des faits observables et littéraux par arête/nœud).
- Le second booléen générique (« la relation tient ») corrèle avec le booléen spécifique mais pas parfaitement (`discusses` : 0,765 vs 0,625 ; `precedes` : 0,716 vs 0,509) — le générique est plus permissif, le spécifique reste la mesure de référence pour les files de revue.
- Un même nœud passage peut porter une description tronquée à 4 000 caractères (3 000 pour les autres types) : les passages très longs (Eusèbe, certains fragments) sont jugés sur un extrait, pas le texte intégral.
- Les 104 échecs transitoires de la Partie A (429/503, charge partagée sur la gateway pendant que d'autres campagnes tournaient en parallèle) ont tous été récupérés ; même mécanisme prévu pour la Partie B.

### Fichiers livrés (`data/quality/jev_2026_09_24/c3_edges_links/`)

- `build_edges.py`, `build_concepts.py` — construction reproductible des candidats + gabarits de questions.
- `jev_client.py`, `run_edges.py`, `run_concepts.py`, `heal_edges.sh`, `heal_concepts.sh` — appels API (httpx brut, pas de paquet `ai` npm disponible localement) + runners auto-cicatrisants.
- `questions_A.json`, `concepts_B.json` — gabarits exacts.
- `candidates_A.jsonl`, `candidates_B.jsonl` — état source/cible envoyé à Jev.
- `results_A.jsonl`, `results_B.jsonl`, `errors_A.jsonl`, `errors_B.jsonl` — réponses brutes + erreurs.
- `analyze_edges.py`, `analyze_concepts.py` — stats + files de revue.
- `stats_by_relation_A.csv`, `stats_by_concept_B.csv`, `stats_by_type_B.csv`.
- `queue_A_likely_wrong.csv`, `queue_A_weak.csv` — Partie A, triées par score croissant.
- `queue_B_new_high_conf.csv`, `queue_B_contradicted.csv`, `queue_B_uncertain_sample.csv` — Partie B.

### Reste à faire

- Terminer et intégrer la Partie B (en cours, runner auto-cicatrisant `heal_concepts.sh`).
- Adjudication humaine des files `queue_*` — aucune écriture n'a été faite dans le KG.
