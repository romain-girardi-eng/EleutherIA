# English-under-Greek-URN Re-home Assessment

## Works assessed

| canonical_id | Title | Passages | Citations |
|---|---|---|---|
| `tlg0732_tlg014_eng` | Alexander of Aphrodisias, *De Fato* (English) | 39 | 45 |
| `urn_cts_greeklit_tlg1766_tlg001_eng` | Tatian, *Oration to the Greeks* (English) | 3 | 3 |

Both carry Greek-namespace `cts_urn`s despite being English translations.

---

## tlg0732_tlg014_eng — Alexander De Fato (English)

### Greek sibling

`tlg0732_tlg014_grc` exists: 39 passages, same `cts_urn` space, same canonical_refs
(`De Fato 1` … `De Fato 39`).

### Ref alignment

**39/39 canonical_refs match exactly** between the English and Greek works
(both use `De Fato 1`, `De Fato 2`, …, `De Fato 39` and identical
`cts_urn`s of the form `urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1:<n>`).

### Feasibility of re-homing

**FEASIBLE.** Every English passage has a Greek counterpart with the same `cts_urn`
and `canonical_ref`. Re-homing means:

1. For each of the 45 citations on English passages, find the Greek passage with the
   same `canonical_ref` (or `cts_urn`), then `UPDATE passage_citations SET passage_id = <grc_id>`.
2. Verify 0 citations remain on English passage_ids.
3. Delete the 39 English passages and the `tlg0732_tlg014_eng` work row.

**Caveat:** Some of the 45 citations are `evidenced_by` links to KG argument nodes
(e.g. `argument_alexander_witness2_ch20_conclusion_amand1945`). These scholarly
argument nodes were built from the English translation. After re-homing them to Greek
passage_ids, the citation still resolves correctly to the same location in the text.
The KG nodes themselves may need description updates to note that the Greek source is
now the anchor, but that is a scholarly review task, not a data integrity issue.

**Status: FEASIBLE — no structural impediment.**

---

## urn_cts_greeklit_tlg1766_tlg001_eng — Tatian Oration (English)

### Greek sibling

`urn_cts_greeklit_tlg1766_tlg001_grc` exists: 98 passages (pre-dedup) / 42 unique
`cts_urn`s (post-dedup).

### Ref alignment

The 3 English passages use `canonical_ref` values `Orat. 7.1`, `Orat. 8.1`,
`Orat. 11.1`. Their `cts_urn`s are:

- `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1:7`
- `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1:8`
- `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1:11`

The Greek work has multiple duplicate passages per cts_urn (see B1 dedup plan). After
dedup, the Greek work will have exactly one passage per cts_urn. Matching on cts_urn:

- `:7` → Greek `a36c2d9d` (kept passage, `Orat. 7.1`)
- `:8` → Greek `8ac4c3f3` (kept passage, `Orat. 8.1`)
- `:11` → Greek `f8ceab87` (kept passage, `Orat. 11.1`)

All 3 English passages have a matching Greek passage at the same `cts_urn`.

### Feasibility of re-homing

**FEASIBLE — but contingent on B1 dedup executing first.**

The re-home must happen after B1 dedup, because the cts_urn ambiguity in the Greek
work (multiple passage_ids per cts_urn) must be resolved before re-pointing citations
to "the Greek passage." Once dedup is done, the mapping is unambiguous.

Steps after B1 dedup:
1. `UPDATE passage_citations SET passage_id = <grc_kept_id> WHERE passage_id = <eng_id>`
   (3 rows, one per English passage, using the kept passage_id from B1).
2. Verify 0 citations remain on the 3 English passage_ids.
3. `DELETE FROM free_will.passages WHERE work_id = (SELECT work_id FROM … WHERE canonical_id = 'urn_cts_greeklit_tlg1766_tlg001_eng')`.
4. `DELETE FROM free_will.ancient_works WHERE canonical_id = 'urn_cts_greeklit_tlg1766_tlg001_eng'`.

**Status: FEASIBLE after B1 dedup. Blocked until B1 is executed.**

---

## Summary

| Work | Greek sibling exists | Ref alignment | Re-home feasible | Blocker |
|------|----------------------|---------------|------------------|---------|
| Alexander eng (39 passages, 45 cits) | Yes | 39/39 exact match | Yes | None |
| Tatian eng (3 passages, 3 cits) | Yes | 3/3 cts_urn match | Yes | B1 dedup must run first |

Both re-homes are structurally straightforward. Neither requires fabricating text or
creating new passages — citations are simply redirected to the existing Greek passage
that covers the same location.
