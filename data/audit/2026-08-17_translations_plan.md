# Plan de traduction anglaise — vague du 17 août 2026

## Résultat

Ce livrable est strictement préparatoire : aucun fichier de `data/kg/` ou de `data/corpus/` n'a été modifié. Le plan contient exactement **170 enregistrements** avec le SHA-256 figé de la description actuelle :

| État prévu | `lat` | `grc` | Total |
|---|---:|---:|---:|
| Traduction anglaise complète | 152 | 8 | 160 |
| `translation_blocked_ocr` | 1 | 1 | 2 |
| `translation_blocked_source_not_original` | 0 | 8 | 8 |
| **Total audité** | **153** | **17** | **170** |

Les codes de langue ci-dessus sont ceux des métadonnées actuelles. Cinq nœuds classés `grc` ont en réalité un témoin latin dans leur description (`Commentarii in Romanos` de Rufin et trois chapitres d'Hermas).

Pour les 160 traductions applicables, le script prévoit exactement les conventions déjà utilisées par les traductions automatiques réelles du graphe :

- `language: "eng"` ;
- `passage_role: "translation"` ;
- `auto_generated: true` ;
- `source_model: "gpt-5.6-sol"` ;
- `original_node_id` et `source_passage_id` vers le jumeau original ;
- suppression de `needs_translation` ;
- suffixe de libellé `(translation pending)` remplacé par `(English)` ;
- estampille d'idempotence `translation_wave_2026_08_17: "applied"`.

Le graphe existant emploie systématiquement `original_node_id` et `source_passage_id` pour cette classe de traductions; le plan n'ajoute donc pas un champ concurrent `translation_of`. Les 164 métadonnées sérialisées sous forme de chaîne JSON restent des chaînes, et les 6 objets JSON natifs restent des objets.

## Sources et décisions philologiques

Les 170 jumeaux originaux existent dans le graphe. Aucun ajout de `metadata.original_text` n'est donc requis.

Une anomalie supplémentaire a été détectée : les descriptions des nœuds augustiniens `passage_aug_gla_1_1` à `passage_aug_gla_1_25` sont des notices anglaises, non le latin ancien annoncé. Les citations locales conduisent cependant sans ambiguïté aux instantanés latins complets de `data/corpus/passages.jsonl`. Les sections 1–24 ont été traduites intégralement depuis ces instantanés, sans écrire dans le corpus. La section 25 n'est qu'une fin d'index biblique suivie de métadonnées binaires Microsoft Word corrompues; elle est bloquée.

Les notices composites contenant déjà un bloc latin ou grec et une traduction de travail ont été ramenées à une traduction anglaise continue du seul passage ancien. Les amorces ou fins tronquées dans les découpages de Boèce sont conservées comme fragments avec points de suspension; les simples césures typographiques d'OCR ont été résolues sans modifier le jumeau source.

## Six échantillons en regard

Les extraits ci-dessous sont représentatifs; les enregistrements Python contiennent les traductions intégrales.

| Nœud | Original | Anglais |
|---|---|---|
| `passage_aug_civ_12_6_en` | *Proinde causa beatitudinis angelorum bonorum ea uerissima reperitur, quod ei adhaerent qui summe est. Cum uero causa miseriae malorum angelorum quaeritur, ea merito occurrit, quod ab illo, qui summe est, auersi ad se ipsos conuersi sunt, qui non summe sunt.* | “Accordingly, the truest cause of the blessedness of the good angels is found in this: that they cleave to him who supremely is. But when the cause of the misery of the evil angels is sought, what rightly presents itself is that they turned away from him who supremely is and turned toward themselves, who do not supremely exist.” |
| `passage_lucretius_2_275_en` | *quare in seminibus quoque idem fateare necessest, / esse aliam praeter plagas et pondera causam / motibus, unde haec est nobis innata potestas* | “Therefore, you must acknowledge that in the seeds too there is another cause of motions besides blows and weight, from which this power innate in us arises.” |
| `passage_plut_fat_13_en` | *καὶ τὰ μὲν ἐντὸς τῆς εἱμαρμένης … ἃ δὴ πάντα περιέχει μὲν ἡ εἱμαρμένη, οὐδὲν δʼ αὐτῶν ἐστι καθʼ εἱμαρμένην.* | “Such, then, are the things within fate: the contingent and the possible, choice and what is up to us, chance and the spontaneous … Fate encompasses them all, but none of them is according to fate.” |
| `passage_sen_prov_2_3_en` | *Athletas videmus … caedi se vexarique patiuntur et si non inveniunt singulos pares, pluribus simul obiciuntur. Marcet sine adversario virtus.* | “We see athletes … allow themselves to be struck and harried, and, if they do not find single opponents who are their equals, they are matched against several at once. Virtue languishes without an opponent.” |
| `sc464_pamphilus_apologia_pro_origene_par106_en` | *Vnigenitus ergo Deus Saluator noster solus a Patre generatus natura et non adoptione Filius est. Natus autem est ex ipsa Patris mente sicut uoluntas ex mente.* | “The only-begotten God, therefore, our Savior, alone begotten from the Father, is Son by nature and not by adoption. He was born from the Father’s very mind, as will is born from mind.” |
| `sc53bis_hermas_pastor_chap110_en` | *Haec omnia, quae supra scripta sunt, ego pastor nuntius paenitentiae ostendi et locutus sum dei servis. Si credideritis ergo et audieritis verba mea et ambulaveritis in his et correxeritis itinera vestra, vivere poteritis.* | “All these things written above I, the Shepherd, the messenger of repentance, have shown and spoken to God’s servants. If, therefore, you believe and hear my words, walk in them, and correct your ways, you will be able to live.” |

## Nœuds sautés

### OCR irrécupérable

- `passage_aristide_sc470_5_en` — fragment papyrologique disloqué de 13 formes (`μιαιροις … ειρετα λλους ν αν νυμε …`), sans syntaxe reconstructible.
- `passage_aug_gla_1_25_en` — l'instantané lié ne contient aucun passage ancien, seulement la fin d'un index de références puis des métadonnées binaires Microsoft Word corrompues.

### Source ancienne intégrale absente

- `passage_epict_110_en` — résumé anglais et trois lemmes grecs seulement, pas *Diss.* 3.22.50–62.
- `passage_epict_148_en` — résumé anglais et un syntagme grec seulement, pas *Diss.* 4.6.29–4.7.5.
- `passage_epict_149_en` — résumé anglais et trois lemmes grecs seulement, pas *Diss.* 4.7.5–18.
- `passage_epict_159_en` — résumé anglais et un incipit grec seulement, pas *Diss.* IV.11.
- `passage_epict_160_en` — résumé anglais et le lemme `προσοχή` seulement, pas *Diss.* IV.12.
- `passage_epict_3_en` — commentaire anglais et deux extraits grecs, pas le passage intégral.
- `passage_irenaeus_ah_3_20_en` — notice anglaise et brèves citations grecques, pas *Adversus Haereses* III.20.3.
- `passage_melito_pasch_47_49_en` — résumé anglais et une proposition grecque, pas *Peri Pascha* 47–49.

Ces dix nœuds gardent leur description, leur langue, leur rôle et `needs_translation: true`. Le script n'ajoute que le drapeau de blocage, sa raison et l'estampille de vague; il ne les présente pas comme des traductions.

## Dry-run obligatoire sur le graphe réel

Commande :

```text
python3 scripts/apply_2026_08_17_translations.py
```

Sortie :

```text
mode=DRY-RUN
nodes=/Users/romaingirardi/Projects/EleutherIA/data/kg/nodes.jsonl
records=170
translations=160
blocked_ocr=2
blocked_source_not_original=8
changed=170
already_applied=0
languages_current={'grc': 17, 'lat': 153}
metadata_representations={'dict': 6, 'str': 164}
source_twins_reachable=170
source_texts_unchanged=170
input_sha256=d1545850c9bd811fcc35e83bc54d9b6dae0e01070f6a2fb3050cdf8313876637
simulated_output_sha256=f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888
invariants=PASS
```

## Écriture en bac à sable et idempotence

Une copie de `nodes.jsonl` a été placée hors dépôt dans `/private/tmp/eleutheria-translations-6ejwYx/`. Premier `--write` :

```text
mode=WRITE
nodes=/private/tmp/eleutheria-translations-6ejwYx/nodes.jsonl
records=170
translations=160
blocked_ocr=2
blocked_source_not_original=8
changed=170
already_applied=0
languages_current={'grc': 17, 'lat': 153}
metadata_representations={'dict': 6, 'str': 164}
source_twins_reachable=170
source_texts_unchanged=170
input_sha256=d1545850c9bd811fcc35e83bc54d9b6dae0e01070f6a2fb3050cdf8313876637
simulated_output_sha256=f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888
invariants=PASS
write_performed=yes
backup=/private/tmp/eleutheria-translations-6ejwYx/nodes.jsonl.bak-translations
```

Second `--write` sur la même copie :

```text
mode=WRITE
nodes=/private/tmp/eleutheria-translations-6ejwYx/nodes.jsonl
records=170
translations=160
blocked_ocr=2
blocked_source_not_original=8
changed=0
already_applied=170
languages_current={'eng': 160, 'grc': 9, 'lat': 1}
metadata_representations={'dict': 6, 'str': 164}
source_twins_reachable=170
source_texts_unchanged=170
input_sha256=f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888
simulated_output_sha256=f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888
invariants=PASS
write_performed=no (idempotent)
```

Contrôles complémentaires :

```text
backup_cmp_original=PASS
stamped=170
roles={'untranslated_duplicate': 10, 'translation': 160}
blocked_flags=10
needs_translation_present=10
sandbox_sha256=f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888
```

La sauvegarde est byte-identique au `nodes.jsonl` réel avant simulation. La seconde exécution ne crée aucune modification. Les 170 jumeaux restent présents et leur description reste strictement inchangée : **zéro texte source perdu**.

## Fichiers livrés

```text
scripts/data_2026_08_17_translations.py
scripts/apply_2026_08_17_translations.py
data/audit/2026-08-17_translations_plan.md
```

