# Plutarch `tlg135` / `tlg138` source adjudication (2026-08-18)

## Status

Adjudication and application are complete. The six `tlg135` passages are now
attached to their own work, the `tlg138` family remains intact, the exact
ambiguity allowlist entry is gone, and the global work/child gate reports zero
mismatches.

The result is not an edition-level ambiguity. The two CTS identifiers denote
two different, neighbouring works:

| CTS work | Correct title | Moralia locus | Corpus sections |
|---|---|---:|---:|
| `urn:cts:greekLit:tlg0007.tlg135` | *Epitome libri de animae procreatione in Timaeo* | 1030d-1032f | 6 |
| `urn:cts:greekLit:tlg0007.tlg138` | *De communibus notitiis adversus Stoicos* | 1058e-1086b | 50 |

The six `tlg135` texts are correctly identified by their CTS URNs but were
given the `tlg138` title and attached to the `tlg138` KG work. The honest
repair is therefore to split the graph parentage and correct the labels. The
existing `work_plutarch_de_communibus_notitiis` remains `tlg138`.

## Independent source evidence

### Local TLG E catalogue

`TLG0007.IDT` (20,480 bytes; SHA-256
`c07ad80734df042f6f9d361a17cb984550871c7f306721d26691058a45712d22`)
decodes to the following consecutive work table:

```text
134  De animae procreatione in Timaeo (1012b-1030c)
135  Epitome libri de animae procreatione in Timaeo (1030d-1032f)
136  De Stoicorum repugnantiis (1033a-1057b)
137  Stoicos absurdiora poetis dicere (1057c-1058e)
138  De communibus notitiis adversus Stoicos (1058e-1086b)
```

The neighbouring entries rule out both an off-by-one reading and an inference
from title alone.

### Local TLG E text

`TLG0007.TXT` (8,609,792 bytes; SHA-256
`d868b60d4bd911ee6b32c2309fe49935a19bf9184d6c9ff4671b3d52cb29891d`)
contains two distinct headings and incipits:

| Byte offset | Probe | Identity |
|---:|---|---|
| 7,961,190 | `EPITOME TOU PERI TES EN TOI ... TIMAIOI PSYCHOGONIAS` | `tlg135` title |
| 7,961,635 | `LEGEI DE TEN HULEN DIAMORPHOTHENAI...` | `tlg135` section 2, matching the six-section family |
| 8,071,619 | `PERI TON KOINON ENNOION...` | `tlg138` title |
| 8,071,739 | `SOI MEN EIKOS, O DIADOUMENE...` | `tlg138` dialogue incipit |

### Perseus CTS catalogue and TEI

The independently maintained Perseus source agrees at commit
[`d07c21b`](https://github.com/PerseusDL/canonical-greekLit/tree/d07c21b26a14bb945b5291ecd34ee3e45f55a7b3/data/tlg0007):

- [`tlg135/__cts__.xml`](https://github.com/PerseusDL/canonical-greekLit/blob/d07c21b26a14bb945b5291ecd34ee3e45f55a7b3/data/tlg0007/tlg135/__cts__.xml)
  names the work *Epitome libri de animae procreatione in Timaeo* and its
  Greek edition `Ἐπιτομὴ τοῦ περὶ τῆς ἐν τῷ Τιμαίῳ ψυχογονίας`;
- [`tlg135.perseus-grc2`](https://github.com/PerseusDL/canonical-greekLit/blob/d07c21b26a14bb945b5291ecd34ee3e45f55a7b3/data/tlg0007/tlg135/tlg0007.tlg135.perseus-grc2.xml)
  starts at Moralia 1030d and contains exactly sections 1-6 used locally;
- [`tlg138/__cts__.xml`](https://github.com/PerseusDL/canonical-greekLit/blob/d07c21b26a14bb945b5291ecd34ee3e45f55a7b3/data/tlg0007/tlg138/__cts__.xml)
  names *De communibus notitiis adversus Stoicos*;
- [`tlg138.perseus-grc2`](https://github.com/PerseusDL/canonical-greekLit/blob/d07c21b26a14bb945b5291ecd34ee3e45f55a7b3/data/tlg0007/tlg138/tlg0007.tlg138.perseus-grc2.xml)
  opens with Lamprias addressing Diadumenus and is the source of the local
  50-section family.

The four pinned source hashes are embedded in
`scripts/data_2026_08_18_plutarch_split.py`.

## Content adjudication

The six local `tlg135` passages are about Plato's *Timaeus*, psychogony,
world-soul, matter, number, and harmonic proportion. Section 1 explicitly
opens `ὁ περὶ τῆς ἐν τῷ Τιμαίῳ ψυχογονίας ἐπιγεγραμμένος λόγος...`;
section 3 discusses Posidonius' account of soul and mathematical limits. They
contain no Lamprias/Diadumenus dialogue labels.

The 50 `tlg138` passages form the different dialogue against Stoic common
conceptions. All 50 contain a Lamprias or Diadumenus speaker marker in the
local extraction. There is no exact text overlap between the six- and
50-section families.

This evidence rejects three tempting mechanical repairs:

1. changing the existing parent from `tlg138` to `tlg135` would falsify its
   title, description, Moralia locus, and verified 50-section corpus source;
2. rewriting the six child URNs to `tlg138` would falsify both their source
   text and the Perseus CTS catalogue;
3. merging the two corpus families as editions would conflate distinct works.

## Exact affected family

Stable passage and edge identifiers are retained so existing citations do not
break:

| Section | KG passage | Corpus passage | Existing `part_of` edge |
|---:|---|---|---|
| 1 | `passage_plut_cn_1` | `c0460502-4859-4a25-ad61-3e7723937953` | `182f9a45-1b5d-4630-9950-0810a1e4f47c` |
| 2 | `passage_plut_cn_2` | `cbea7bff-8674-4b2a-9e91-2be555ae40c9` | `150dd402-a5cc-427c-b026-4bc49e3c1370` |
| 3 | `passage_plut_cn_3` | `2236e0eb-3fdb-473f-8053-da7a4d2c042d` | `071d871c-23a0-44f8-b017-bae375dc70c2` |
| 4 | `passage_plut_cn_4` | `1491dca2-426f-486a-9340-e1340ce64110` | `fdcbe4a6-4289-48a4-aa9d-481368784f23` |
| 5 | `passage_plut_cn_5` | `06aa0904-ec48-4d51-a70f-f92548670896` | `bf9531cb-0ca9-48d0-8ec1-cfecb4c0b27d` |
| 6 | `passage_plut_cn_6` | `693256f2-5aa2-4a9e-9cda-6fc00136963a` | `abcb4124-bc15-4817-b7d9-5b55a74946e8` |

The legacy `passage_plut_cn_*` names are historical identifiers, not current
scholarly labels. Renaming them would create needless referential churn; the
human-readable label and metadata carry the corrected identity.

## Projected repair

Running the applier with `--apply` will:

1. create `work_plutarch_epitome_animae_procreatione_timaeo` with CTS
   `tlg0007.tlg135`, exact source provenance, and one `authored_by` edge to
   Plutarch;
2. redirect only the six listed `part_of` edges to that work;
3. correct the six KG labels, `work_title`, and `canonical_ref` values while
   preserving their Greek text, passage IDs, CTS URNs, and citation links;
4. correct the six corpus `canonical_ref` values on the same loci;
5. correct the `tlg135` manifest title and fill its work-level `cts_urn`;
6. leave the `tlg138` work, manifest row, and 50 corpus passages unchanged;
7. remove only the exact
   `work_plutarch_de_communibus_notitiis` entry from
   `kg_work_child_canonical_known_ambiguities.json`;
8. regenerate `data/stats.json` and `data/stats.md` from the projected data.

These operations were applied successfully. The seven one-time backups carry
the suffix `.bak-plutarch_split_2026_08_18`; the second application reported
`changed=false` with identical byte hashes. Together with the global parity
package, this repair removed the final six parity violations.

Projected counts from the 2026-08-18 checkpoint:

| Metric | Before | After |
|---|---:|---:|
| KG nodes | 20,271 | 20,272 |
| KG edges | 50,169 | 50,170 |
| KG work nodes | 250 | 251 |
| Corpus passages | 21,158 | 21,158 |
| `tlg135` / `tlg138` corpus sections | 6 / 50 | 6 / 50 |
| Work/child canonical mismatches | 1 | 0 |
| Locus-parity violations in this six-passage family | 6 | 0 |

The six parity removals are coordinated with the global parity repair and are
owned by this source-specific package so the wrong old title cannot be copied
back into the graph.

## Safety and reproducibility

The applier is dry-run by default:

```bash
.venv/bin/python scripts/apply_2026_08_18_plutarch_split.py
.venv/bin/python scripts/apply_2026_08_18_plutarch_split.py --apply
```

Before any write it requires:

- exact source-file hashes and exact TLG work-table neighbours;
- exact local text-probe offsets;
- the exact six UUIDs, node IDs, edge IDs, CTS loci, and text hashes;
- exactly 6 `tlg135` and 50 `tlg138` corpus passages;
- the exact pre-repair labels, edge targets, manifest row, and allowlist entry;
- current statistics that already agree with the canonical files;
- no projected work/child mismatch or new work-ID collision;
- exact KG/corpus locus parity for the corrected family;
- R1-R18 `BLOCK 0 / WARN 0` for the new work and authorship edge;
- a complete projected-state re-read classified as `applied`.

Each changed canonical file receives a one-time sibling backup ending in
`.bak-plutarch_split_2026_08_18`. Unchanged JSONL lines are preserved byte for
byte. A second application recognizes the applied state and writes nothing.

## Verification performed

```text
read-only evidence/source gate              PASS
default applier dry-run                     PASS
projected work/child mismatches             0
projected work-ID collisions                0
projected six-passage locus parity           0 violations
R1-R18 new-node/new-edge gate               BLOCK 0 / WARN 0
isolated full --apply                       PASS; all seven backups created
isolated second --apply                     changed=false
isolated second-run byte hashes             identical
Ruff                                        All checks passed
Python bytecode compilation                 PASS
git diff --check                            PASS
```

The isolated write test used copies of the seven prospective canonical files;
the workspace's canonical data remained untouched.
