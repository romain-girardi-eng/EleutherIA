# Alexander / Sharples global P0 preview

Date: 2026-08-24  
Mode: dry-run only; **no data write**.  
Status: `ready_for_independent_review_no_apply`.

## Frozen inputs

- post-Sorabji+Long KG nodes:
  `57fb90da476ebdf98bc59f4a0cb4bad0c4871d5d829c0dc05063b4752b6c8664`;
- post-Sorabji+Long KG edges:
  `22efd267ac194d67d23ffd9985d2c68d93e1cfb4129e1a91cc3fda4871fadd70`;
- corpus citations:
  `3fa555efad53ad2795f04fb28959442e42630b4f33187c1c7a1b78890af0d248`;
- Sharples source scan:
  `7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638`;
- Sharples OCR derivative:
  `ec154e4d3607f887299ac3faf6ec1853b0a4da117eaa464d70331d7c55727ebb`;
- pinned Bruns/OGL TEI:
  `184b01f38061cfa00b276ed8d9580f3f842f564856851e4bcc124adcc2edbb2f`;
- scholarly audit:
  `b540d7ef297c9b4d6bc876729f457e673e02aac5fc25ce04349ea0b9131afabe`.

The scan is 17,913,871 bytes and 161 PDF spreads/pages. It is an internal,
all-rights-reserved verification artifact. The verified Arabic-page rule is
`PDF page = floor(printed page / 2) + 5`. OCR is navigation-only.

## Exact bounded delta

### Nodes

Exactly fifteen nodes change:

- eleven strong legacy argument reconstructions;
- `work_de_fato_alexander_c200ce_o6p7q8r9`;
- `pub_sharples_1983_alexander_fate`;
- the non-exact Greek/English `passage_alexander_de_fato_15*` pair.

`argument_agent_causation_alex` remains byte-identical as the locally exact
De fato 12/20 result. All six Sorabji/Long overlap nodes remain byte-identical.
Every strong duplicate becomes `discoverable_only`; its public label says
`Legacy reconstruction`, direct Alexander candidate loci, hostile/reported
Stoic material, Sharples taxonomy and modern reconstruction are separately
typed, and no premise/conclusion asserts an uncaused ultimate substance-agent
as direct text.

### Edges and citations

- 55 over-strong `cites_primary_source` / `source_for` or false-composite
  grounding edges are removed;
- the single Sharples-publication/work edge is retained and corrected to
  translation/commentary with photographic Bruns facsimile;
- 31 corpus citations are downgraded from `source_for` to
  `related_passage_non_exact`;
- two false exact snapshots for the legacy De fato 15 composites are removed.

Frozen cohort digests:

- edges before (56):
  `ef35bc8267196b2edc20b683c243a4732b516fe2e08b8d4f0f5cc39c92af4d3b`;
- applied retained edge cohort (1):
  `4a1378e7a7ef5cf186cf9081a69edf28605267fd71af6ffd46e2ec1c9d558901`;
- citations before (33):
  `68f2d38c8762209531165fa77f670aa3e41eb3082201945e0000ac9c5846f2d0`;
- applied related citations (31):
  `af39f0bb5e358d1b7203afa280ed9b9a61e9c2e5579d30363622bfb4f6812250`.

No corpus passage or corpus manifest is an output of this wave. De fato 8/11
textual/OCR debt is registered as a separate open issue.

## Sharples manifestation and bibliography

`pub_sharples_1983_alexander_fate` becomes a concrete Duckworth 1983 book:

- *Alexander of Aphrodisias on Fate: Text, Translation and Commentary*;
- Gerald Duckworth & Co. Ltd., London;
- ISBN `0-7156-1589-0` cased and `0-7156-1739-7` paper;
- translation/commentary with photographic Bruns facsimile and textual notes;
- explicitly not a newly constituted critical edition.

A distinct scholarly-manifest row and
`src_sec_sharples_1983_alexander_on_fate` are added. The ancient source keeps
only its Bruns/OGL TEI artifact. Fourteen page-level, paraphrase-only evidence
records remain `in_review`.

BibTeX and its companion report are transformed atomically with the pure
canonical exporter. Preview hashes:

- `data/kg/publications.bib`:
  `2c30e5b067936fedc814fc0e1e6ea46f29807d68ede0f95e9a2740bc92fb58b6`;
- companion report:
  `b24d34a99e42b1afa68807079d9974221fc4d603d57acd17a936e7ca93b2b0cd`.

## Registry and open issues

Two issues remain open:

- `issue_alexander_global_reconstruction_overclosure_20260824`;
- `issue_alexander_de_fato_8_11_text_recollation_20260824`.

The earlier `issue_alexander_agent_causation_reconstruction` is preserved as a
local 12/20 adjudication, not global closure. A new blocked wave records the
follow-up. No independent, adversarial or human PASS is created.

Normative Draft7 validation of the actual registry schema gives 41 inherited
errors before and 41 after: zero new and zero removed. The custom registry audit
is structurally valid. Strict ingestion debt decreases from 1155 BLOCK / 768
WARN to 1154 / 767, with no new debt.

## Preview output hashes

| Path | SHA-256 preview |
|---|---|
| `data/kg/nodes.jsonl` | `7741406ffb843a1fc7df468a63e8998c3acb8f36633fe066eff4210d25c65135` |
| `data/kg/edges.jsonl` | `e614d6151a59e9db1cbeca19bb88e05169640d0d3be83b36867dbc896d706205` |
| `data/corpus/citations.jsonl` | `38c1a647bb37bedc74e52f930efec76faf764eca32a999613d3277624d3ade93` |
| `data/kg/publications.bib` | `2c30e5b067936fedc814fc0e1e6ea46f29807d68ede0f95e9a2740bc92fb58b6` |
| `data/kg/publications_bibtex_report.json` | `b24d34a99e42b1afa68807079d9974221fc4d603d57acd17a936e7ca93b2b0cd` |
| `data/scholarly_sources/manifest.jsonl` | `0c7efe6cafa045fe625b0957c19f1535a35d25fda4223595d462103769432e09` |
| registry sources | `77605ecaad1d0658094ace1f2d7276b30ca9523230158c091d3d8c0d361df3c2` |
| registry evidence | `91693dd44b0f18c22a36d78988c765261428d204d261fb48e1d74babbed9fa96` |
| registry issues | `fda16eebbd848739bc0da96cc9dc4c00d1674eb221707a921a1f7b25e7a52545` |
| blocked wave | `76d3182a9c027e6272e46d6ed9a8c3a1b235e688963e4c05f38c0479ff264405` |

The dry-run JSON is
`/tmp/2026-08-24-alexander-sharples-global-p0-preview.json`, SHA-256
`60a35fcff302ca13e7d48f3a37f4237ddde23b2b9ea6cb8f4b45a4522446d0f7`.

## Verification

- targeted Alexander/Sharples suite: 20 PASS;
- current global plus local 12/20 gates: 35 PASS;
- ruff: PASS;
- exact node/edge/citation/file touched-set: PASS;
- true runtime citability policy: PASS;
- normative schema zero-new: PASS;
- prospective snapshot/corpus/parity/work-ID no-growth: PASS;
- idempotent full apply on a temporary copy: PASS;
- precommit drift, hard-crash recovery, rollback-failure durability and second
  recovery: PASS.

This preview is ready only for independent/adversarial review. No data write or
deployment is authorized or performed.
