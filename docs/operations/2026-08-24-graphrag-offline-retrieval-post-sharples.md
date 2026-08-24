# GraphRAG offline retrieval diagnostic — post-Sharples identity leg

**Status:** valid dirty-worktree diagnostic, not a release baseline  
**Run:** `eval-2026-08-24-180e81ded29a`  
**Runner:** `snapshot-lexical-v2`  
**Snapshot:** `f3ecd8b778feb68fcd16ea7c7503ce2fb244cf5682513ee5381c05ed2f5432ba`  
**Query/gold:** `aad9b1a3ac9aa221c919ceb09817d1ff56e28998b70a5ecf758300d7d23a67a9`

## Change under test

The lexical node pool previously served entity and work identities from one
mixed top-30 ranking. Dense argument/concept prose could therefore suppress an
explicitly named work; after the correct Sharples declassification, the strict
Alexander case named *De fato* but returned no Alexander work node.

The runner now has a separate three-result lexical work-identity leg. It adds a
bounded author+title conjunction boost (for example `Alexander` + `De fato`) and
does not change passage citability, synthesize graph edges or re-admit any
declassified claim. Work identities are discovery handles; the central policy
still independently excludes blocked/discovery-only passage text.

## Bound snapshot

| File | SHA-256 |
|---|---|
| passages | `e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3` |
| nodes | `92a0cd13dcab0d1749119e8ef0b772392e7920177096213deca2906e88821817` |
| edges | `b1ce4f5e594d846c0d64ad1a33b4e0b0970230c11641010df8ea9b58e8ebfd2a` |
| citations | `5bd6657adb6aa006bc12a33285c399e00fc7ab467932b603369e119bdc9e089a` |
| manifest | `2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e` |

## Measured delta

Both sides use the same post-Sharples data and 56 cases. “Before” is the
unseparated mixed node/work channel; “after” is the three-work identity leg.

| Valid-gold metric | Before | After |
|---|---:|---:|
| entity precision / recall / F1 | .0338 / .4162 / .0616 | .0356 / .4162 / .0645 |
| work precision / recall / F1 | .3646 / .6562 / .3854 | .3125 / .8125 / **.4437** |
| manifestation precision / recall / F1 | .1905 / .6429 / .2837 | .2194 / .7143 / **.3281** |
| passage precision / recall / F1 | .0625 / .2417 / .0968 | .0667 / .2667 / **.1039** |
| complete-evidence-set recall | .2000 | **.2500** |
| p50 / p95 / max retrieval | 10.61 / 24.14 / 27.78 ms | 13.11 / 27.81 / 29.62 ms |

For the seven strictly admitted repair cases, recalls are now:

- entity `.6429`;
- work `.8571`;
- manifestation `.7143`;
- passage `.7143`;
- complete evidence set `.7143`.

The Ps.-Plutarch complete set now passes. Origen Exhortatio and Sextus remain
incomplete. Forbidden-passage hits remain zero.

## Gates and limitations

- Evaluation tests: **104 passed, 1 skipped**.
- Ruff: PASS.
- 56/56 queries execute without error.
- The 29 legacy invalid gold IDs across 20 queries remain explicitly invalid;
  therefore `release_comparable=false` and this artifact cannot certify a
  release.
- This is retrieval-only: generation, abstention, publication safety, quote
  fidelity, token and cost channels are unobserved, not credited as zero.
- The exact JSON remains under `/tmp` because the worktree is dirty. A reviewed
  immutable release must rerun and preserve a separately named baseline.
