# C3 : `engages_with` vers le mauvais homonyme — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_c3_person_identity.py` et `scripts/apply_2026_09_24_c3_person_identity.py`.
Décisions : `data/audit/2026-09-24_c3_person_identity_decisions.jsonl` (91 enregistrements). Quarantaine : `data/audit/2026-09-24_c3_person_identity_quarantine.jsonl` (8 arêtes).

## Périmètre et méthode

La file C3 `queue_A_likely_wrong.csv` contient 88 arêtes `engages_with`. Ce sont des liens entre savants, extraits automatiquement, et tous portent encore `needs_review`. Je n'ai pas vérifié l'échange savant lui-même, faute de disposer des bibliographies. J'ai vérifié une seule chose : la personne visée par la note d'extraction est-elle bien celle du nœud cible ? Quand la note prouve qu'il s'agit d'un homonyme, l'arête est déplacée vers le bon nœud s'il existe, et retirée sinon. `engages_with` étant symétrique, l'arête inverse éventuelle suit.

## Résultat

| Verdict | File | Hors file |
|---|---|---|
| `removed` : homonyme sans nœud, ou engagement déclaré non attesté | 7 | 1 |
| `corrected` : arête déplacée vers le bon homonyme | 4 | — |
| `needs_romain` | 5 | 2 |
| `false_positive` : identité cohérente avec la note | 72 | — |

### Arêtes retirées

- **Annie Jaubert → John Martin Fischer.** La note renvoie à *Die apostolischen Väter* (1956), une édition des Pères apostoliques. John Martin Fischer, né en 1952, est un philosophe analytique.
- **Robert M. Grant → Isabelle Koch** (« Pauly-Wissowa, sur Origène »), **Henri Crouzel → Isabelle Koch** (« Koch présente Origène en philosophe ») et, hors file, **Carl Andresen → Isabelle Koch** (« Pronoia und Paideusis »). Ces trois notes visent Hal Koch, auteur de *Pronoia und Paideusis* (1932), étude sur Origène. Le nœud cible décrit Isabelle Koch (Aix-Marseille, Alexandre d'Aphrodise). Hal Koch n'a pas de nœud.
- **Ilaria Ramelli → Susan Wolf.** La note écrit « Marx Wolf 2013 » : c'est une autre personne.
- **T. H. Irwin → William James.** La note cite la formule sur les romans victoriens, « large, loose, baggy monsters ». C'est la formule d'un romancier, pas celle du philosophe.
- **Jean-Louis Labarrière → Richard Taylor.** La note évoque « Taylor (1989) on sources of the self ». Ce livre n'est pas de Richard Taylor, le libertarien de la causalité par l'agent.
- **Alfons Fürst → Susanne Bobzien.** La note dit elle-même « probably engaged … though not explicitly named ».

### Arêtes déplacées

- **Nicholas List, Claire Hall et Kathleen Gibbons → Jonathan Edwards** deviennent **→ Mark J. Edwards** (`scholar_edwards_mark`). Les notes portent respectivement sur l'article « On the Platonic Schooling of Justin Martyr », sur le « directeur de thèse ; travaux sur Origène » et sur la préexistence des intellects chez Origène. Le nœud d'origine est le théologien congrégationaliste du XVIII<sup>e</sup> siècle.
- **Danilo Šuster → Michael Frede** devient **→ Dorothea Frede**. La note porte : « Frede (2003) … cites her survey article on Stoic determinism ».

L'ancienne extrémité est conservée dans `metadata.c3_person_identity_2026_09_24`.

### `needs_romain`

- Gaventa → Peter King (« 2017 on flesh and spirit »).
- Gaventa → Susan Sauvé Meyer (« 2004d, 67-68 », sur Romains 6-7 : un exégète paulinien du nom de Meyer, probablement).
- Ramelli → Michael Frede (« Frede 2009 », postérieur à sa mort en 2007).
- Grgić → Ginet (la note nomme Pećnjak comme auteur citant).
- Kowalski → Kane (« Islamic scholars », sujet douteux).
- Hors file : Gourinat → Michael Frede (« 2003 », probablement Dorothea).
- Hors file : Gibbons → Isabelle Koch (sur Origène : Hal ou Isabelle ?).

## Défaut systémique

La résolution des noms dans l'extraction de mai 2026 se fait sur le seul patronyme. Les homonymes célèbres (Edwards, Koch, Frede, James, Taylor, Wolf, Fischer, Meyer) captent des citations qui ne les concernent pas. Proposition : pour `engages_with`, exiger que l'année citée dans la note soit compatible avec les dates de la personne, et bloquer la résolution quand le patronyme couvre plusieurs nœuds `person` ou `scholar`.

## Contrôles

- Relance : aucune modification.
- Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict`, `check_kg_work_child_canonical`.
