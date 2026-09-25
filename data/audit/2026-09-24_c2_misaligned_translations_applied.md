# Traductions désalignées (C2, file `queue_a_misaligned`) — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_c2_misaligned_translations.py` (470 décisions, une ligne commentée par paire) et `scripts/apply_2026_09_24_c2_misaligned_translations.py`.
Décisions : `data/audit/2026-09-24_c2_misaligned_translations_decisions.jsonl`. Enregistrements retirés : `data/audit/2026-09-24_c2_misaligned_translations_quarantine.jsonl`.

## Point de départ

La file contient les 470 paires `translation_of` que Jev juge « même contenu » avec p ≤ 0,3. **Les 470 traductions anglaises sortent d’un seul lot machine** (`translation_source = "AI batch: claude-opus-4-6"`, `translation_type = machine`). J’ai lu chaque paire : l’original tel que le nœud le stocke (grec ou latin), puis l’anglais. Pour Contre Celse V-VI et le *Pasteur*, j’ai aussi lu les sections voisines afin d’identifier ce que l’anglais rend réellement.

## Résultat

| Verdict | N | Action |
|---|---|---|
| Désalignée : rend un autre passage, résume un autre chapitre, ou ajoute des phrases absentes de l’original | 361 | nœud retiré avec ses 3 arêtes (`translation_of`, `authored_by`, `part_of`), son jumeau du corpus et sa citation, le tout en quarantaine |
| Alignée, couverture partielle (faux positif de Jev) | 90 | conservée, estampillée `c2_translation_review_2026_09_24 = aligned_partial` |
| Alignée, mais déborde sur les versets suivants | 7 | conservée, signalée (`aligned_exceeds_locus`) |
| Alignée, suivie d’un résumé éditorial entre crochets dans le texte | 6 | crochet déplacé en métadonnée, texte du corpus rogné à l’identique |
| Synopsis du même passage à la voix de l’éditeur | 5 | conservée, requalifiée `translation_type = machine_paraphrase` |
| Original `vocabulary_gloss` (pas une paire) | 1 | aucun changement |

Par œuvre, pour les retraits : Méliton, *Peri Pascha* 65/65 ; Hermas, *Pasteur* 91/94 ; Origène, *Contre Celse* 156/211 ; Barnabé 34/43 ; Théophile, *À Autolycus* 13/18 ; Sénèque, *De providentia* 2/3.

Bilan : −361 nœuds, 108 nœuds modifiés, −1 083 arêtes, −361 passages et −361 citations du corpus, 6 passages du corpus modifiés.

## Ce que montre la lecture : des défauts de lot, pas des erreurs isolées

1. **Méliton, *Peri Pascha* : décalage systématique.** L’anglais de `chapN_en` rend un autre chapitre. Exemple : l’anglais de 29 (“For instead of the lamb there was a Son”) correspond au grec de 5 ; celui de 54 (“the human being, by nature capable of receiving both good and evil”) correspond au grec de 48. Le grec de 48, « Ὁ δὲ ἄνθρωπος φύσει δεκτικὸς ὢν ἀγαθοῦ καὶ πονη-ροῦ », qui est le locus clé pour le libre arbitre, avait donc pour « traduction » une phrase sur l’héritage étroit.
2. ***Contre Celse* V-VII : pseudo-traductions.** Au livre V, l’anglais est un commentaire libre prêté à Origène (“Origen notes an example of the humanity of Jewish law … without parallel in the ancient world”). Aux livres V-VI, il est hybride : la première phrase traduit l’ouverture du grec, la dernière ajoute une conclusion absente. En V.61 (`v_par61_a`) l’ajout porte même sur le libre arbitre (“every rational soul was created with free will (autexousion)”), sans appui dans cette section. Au livre VII, l’anglais est entièrement composé : aucune phrase ne rend le grec.
3. **Hermas, *Pasteur* : synopsis d’autres chapitres.** Ce ne sont pas des traductions mais des résumés à la voix de l’éditeur (“The ninth parable continues …”), presque tous d’un autre chapitre que le grec du nœud.
4. **Barnabé et Théophile : décalage d’un à plusieurs versets ou chapitres** (l’anglais du livre I d’*À Autolycus* rend d’autres chapitres du même livre).
5. **À l’inverse, *Contre Celse* I-IV, Clément de Rome, Boèce, Aristide, Athénagore, Pamphile** : traductions fidèles mais tronquées. Jev les juge désalignées parce qu’elles ne couvrent que l’ouverture du passage. **Ce sont des faux positifs** (voir les 90 + 7 + 6).

## Défaut structurel et correction proposée

Le lot machine compte encore **2 349 traductions** (Contre Celse 831, Grégoire de Nysse `tlg0557` 324, Pamphile 265…). La file Jev ne voit que p ≤ 0,3 : les défauts ci-dessus existent très probablement aussi entre 0,3 et 0,7 (par exemple les 44 chapitres de Méliton non retirés, ou *Contre Celse* VII hors file). Proposition, à décider par Romain :

- marquer tout le lot `translation_source = "AI batch: claude-opus-4-6"` comme non citable (`citation_blocked`, comme le précédent Tatien du 24 août) jusqu’à revue ;
- lancer une vérification déterministe de l’alignement (comparaison aux traductions publiées disponibles) plutôt qu’un seuil Jev ;
- remplacer à terme ces textes par des traductions publiées et nommées (Hall pour Méliton, Chadwick pour *Contre Celse*, etc.).

## Contrôles

Préconditions (source machine, `original_node_id` inchangé, arête `translation_of` présente), estampille, idempotence vérifiée par une relance (0 action). Invariants avant écriture. Portes : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity`, `check_kg_work_child_canonical`, `check_scholarly_sources_manifest` OK. `check_snapshot_passage_integrity --strict` échoue, **mais déjà avant ce lot** : les mêmes 66 « nouvelles » violations, identiques, existent sur `34ea208`, le commit de départ. La dette totale descend de 5 931 à 5 570. Stats et BibTeX régénérés.

Toutes les citations grecques et latines de ce dossier sont copiées du nœud par le script. Les gloses entre ‹ › dans le fichier de données sont mes rendus anglais, pas des citations.
