# Cohérence CTS œuvre-enfants (2026-08-18)

## Problème

Le gate R3 vérifiait que les passages d'une même œuvre ne se répartissaient
pas entre plusieurs identifiants canoniques. Il ne comparait pas cet identifiant
unanime avec le CTS déclaré par le nœud œuvre. Trois parents pouvaient donc
contredire 100 % de leurs propres enfants sans faire échouer la CI.

## Corrections appliquées

| Nœud œuvre | Ancien CTS du parent | CTS corrigé | Enfants concordants | Autorité corpus |
|---|---|---|---:|---|
| `work_de_fato_alexander_c200ce_o6p7q8r9` | `urn:cts:greekLit:tlg2018.tlg005` | `urn:cts:greekLit:tlg0732.tlg014` | 78/78 | manifeste, Alexandre, *De Fato* |
| `work_de_interpretatione_aristotle_c350bce_e4f6g8h0` | `urn:cts:greekLit:tlg0086.tlg038` | `urn:cts:greekLit:tlg0086.tlg017` | 29/29 | manifeste, Aristote, *De interpretatione* |
| `work_de_libero_arbitrio` | `urn:cts:latinLit:stoa0040.stoa054` | `urn:cts:latinLit:stoa0040.stoa003` | 340/340 | manifeste, Augustin, *De Libero Arbitrio* |

Chaque nœud conserve l'ancien identifiant, le nouvel identifiant, le nombre
d'enfants attestants et l'autorité du manifeste dans le stamp
`work_canonical_repair_2026_08_18`.

## Nouveau gate

`scripts/check_kg_work_child_canonical.py` :

1. suit uniquement les arêtes `passage -part_of-> work` ;
2. normalise les formes CTS, First1KGreek et les slugs historiques ;
3. n'impose une comparaison que si chaque passage enfant possède un
   `work_canonical_id` explicite, parsable directement ou via un alias unique
   du manifeste, et que tous convergent vers une seule identité canonique ;
4. compare cette identité aux champs canoniques du parent ;
5. exige une unique autorité de manifeste `in_corpus`, non vide et dont tous
   les identifiants parsables convergent vers la même œuvre ;
6. compare séparément chaque champ canonique du parent, afin qu'un champ juste
   ne puisse pas masquer un second champ faux ;
7. échoue sur tout mismatch nouveau.

Le gate est branché dans `.github/workflows/ci.yml` avec ses tests unitaires.

## Ambiguïté Plutarque résolue

L'adjudication source a établi que `tlg135` est l'*Epitome libri de animae
procreatione in Timaeo*, tandis que `tlg138` est bien le *De communibus
notitiis*. Les six passages ont été rattachés à un nouveau nœud œuvre `tlg135`,
le manifeste a été corrigé, et l'ancienne entrée d'allowlist supprimée. Le gate
œuvre-enfants rapporte désormais zéro mismatch.

## Résultats

```text
avant : 4 mismatches (3 nouveaux + 1 ambiguïté connue)
après : 1 ambiguïté connue, 0 mismatch nouveau
idempotence : seconde application, 0 changement et checksum identique
tests unitaires du nouveau gate : 10 réussis
```

Sauvegarde pré-correction :
`data/kg/nodes.jsonl.bak-work_canonical_repair_2026_08_18`.
