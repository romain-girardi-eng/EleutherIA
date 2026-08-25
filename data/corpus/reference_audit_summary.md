# EleutherIA Corpus Reference Audit

Audit date: 2026-05-24

## Overall Totals

| Metric | Count |
|--------|-------|
| Total passages | 16,629 |
| Total works | 171 |
| Verifiable works (GitHub TEI found) | 51 |
| Unverifiable works (no GitHub edition / SC / no URN) | 120 |
| Passages in verifiable works | 7,907 |
| Passages in unverifiable works | 8,722 |

### Classification of passages in verifiable works

| Class | Count | Meaning |
|-------|-------|---------|
| match | 3,724 | Text ≥ 0.98 similarity or normalised-equal |
| minor_diff | 167 | 0.85–0.98 similarity (edition/formatting differences) |
| divergent | 583 | < 0.85 similarity (likely wrong text/edition) |
| ref_not_in_edition | 3,427 | Passage URN absent from authoritative edition |

## Root-Cause Analysis of Major Flags

The 4,010 flagged entries decompose into distinct categories, most of which are NOT wrong-text errors:

| Root cause | Works affected | Passages flagged | Severity |
|-----------|---------------|-----------------|----------|
| **Oracle coverage gap** — GitHub TEI only has books 1–20 of Seneca Ep.; corpus has all 124 | phi1017_phi015_lat | ~2,130 ref_missing | False positive |
| **URN encoding bug** — underscore separator (1_1) instead of dot (1.1) in Epictetus Discourses | tlg0645_tlg003_grc | 750 ref_missing | REAL BUG (URN fixable) |
| **Granularity mismatch** — stored uses Stephanus letter-sub-pages (227a,b,c…) that GitHub TEI does not expose | tlg0059_tlg002/012_grc | 386 ref_missing | False positive |
| **Granularity mismatch** — stored = 25-line chunks; auth = single lines (Lucretius DRN) | phi0550_phi001_lat | 299 divergent | False positive |
| **Granularity mismatch** — stored uses 2-level depth; auth 1-level (Aristotle De Interp.) | tlg0086_tlg017 | 29 ref_missing | False positive |
| **Wrong work_canonical_id** — work ID says tlg004 but passage URNs say tlg003 (Plato Crito) | tlg0059_tlg004_grc | 59 ref_missing | REAL BUG |
| **Genuine text divergence** — different ms/editorial readings vs. Perseus GitHub (Diogenes Laertius Vitae) | tlg0004_tlg001_grc | 110 divergent | REAL — needs review |
| **Duplicate URN bug** — 98 passages share only 42 unique refs (Tatian Oratio) | tlg1766_tlg001_grc | 88 divergent | REAL BUG |
| **Language mismatch** — English translations stored under Greek CTS URNs | tlg0732_tlg014_eng, tlg1766_eng, tlg0562_eng | ~58 divergent | REAL BUG |
| **SVF source-header contamination** — doxographic citation headers prepended to fragment text | tlg1269_tlg002 | 45 flagged | REAL BUG |
| **Metadata error** (not caught by text audit) — phi0474.phi041 titled "De Natura Deorum" in manifest but is actually *Orator*; stored text correctly matches Orator | phi0474_phi041_lat | 0 text flags | REAL — title/URN mislabel |

**Genuine high-priority bugs requiring fixes:**
1. `tlg0645_tlg003_grc` — fix underscore separators to dots in 750 passage URNs
2. `tlg0059_tlg004_grc` — fix work_canonical_id (should be tlg003, not tlg004)
3. `tlg0004_tlg001_grc` — manually review 110 divergent passages against the Marcianus ms
4. `tlg1766_tlg001_grc` — deduplicate the 56 extra passages sharing URN refs
5. `tlg0732_tlg014_eng` / `urn_cts_greeklit_tlg1766_tlg001_eng` / `urn_cts_greeklit_tlg0562_tlg001_eng` — English translations must not use Greek CTS URNs
6. `tlg1269_tlg002` — strip source-citation headers from SVF passage texts
7. `phi0474_phi041_lat` in manifest — wrong title; also missing De Natura Deorum entirely

## Top Problem Works (by flagged passage count)

| Work | Passages | ref_missing | divergent | minor_diff | match | Work URN |
|------|----------|-------------|-----------|-----------|-------|----------|
| `urn_cts_latinlit_phi1017_phi015_lat` | 2135 | 2130 | 5 | 0 | 0 | `urn:cts:latinLit:phi1017.phi015.perseus-lat2` |
| `urn_cts_greeklit_tlg0645_tlg003_grc` | 750 | 750 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0645.tlg003.perseus-grc2` |
| `urn_cts_latinlit_phi0550_phi001_lat` | 300 | 1 | 299 | 0 | 0 | `urn:cts:latinLit:phi0550.phi001.perseus-lat1` |
| `urn_cts_greeklit_tlg0059_tlg012_grc` | 261 | 261 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0059.tlg012.perseus-grc2` |
| `urn_cts_greeklit_tlg0059_tlg002_grc` | 125 | 125 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0059.tlg002.perseus-grc2` |
| `urn_cts_greeklit_tlg0004_tlg001_grc` | 1211 | 0 | 110 | 124 | 977 | `urn:cts:greekLit:tlg0004.tlg001.perseus-grc2` |
| `urn_cts_greeklit_tlg1766_tlg001_grc` | 98 | 0 | 88 | 5 | 5 | `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1` |
| `urn_cts_greeklit_tlg0059_tlg004_grc` | 59 | 59 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0059.tlg003.perseus-grc2` |
| `tlg1269_tlg002_1st1k_grc1_grc` | 51 | 39 | 6 | 5 | 1 | `urn:cts:greekLit:tlg1269.tlg002.1st1K-grc1` |
| `tlg0732_tlg014_eng` | 39 | 0 | 39 | 0 | 0 | `urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1` |
| `first1k_tlg0086_tlg017_1st1k_grc1_grc` | 29 | 29 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0086.tlg017.1st1K-grc1` |
| `urn_cts_greeklit_tlg0562_tlg001_eng` | 19 | 0 | 16 | 0 | 0 | `urn:cts:greekLit:tlg0562.tlg001.perseus-grc2` |
| `tlg2018_tlg001_1st1k_grc1_grc` | 222 | 15 | 0 | 1 | 206 | `urn:cts:greekLit:tlg2018.tlg001.1st1K-grc1` |
| `urn_cts_greeklit_tlg0093_tlg001_grc` | 9 | 9 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0093.tlg001.1st1K-grc1` |
| `oga_tlg0086_tlg031_1st1k_grc1_grc` | 71 | 0 | 4 | 6 | 61 | `urn:cts:greekLit:tlg0086.tlg031.1st1K-grc1` |
| `urn_cts_greeklit_tlg0645_tlg003_eng` | 4 | 4 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0645.tlg003.perseus-grc2` |
| `urn_cts_greeklit_tlg0057_tlg010_grc` | 3 | 3 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0057.tlg010.1st1K-grc1` |
| `urn_cts_greeklit_tlg1766_tlg001_eng` | 3 | 0 | 3 | 0 | 0 | `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1` |
| `alexander_of_aphrodisias_de_fato_eng` | 2 | 0 | 2 | 0 | 0 | `urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1` |
| `alexander_of_aphrodisias_de_fato_grc` | 2 | 0 | 2 | 0 | 0 | `urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1` |

## All Verified Works

| Work | Passages | match | minor_diff | divergent | ref_missing | Work URN |
|------|----------|-------|-----------|-----------|-------------|----------|
| `alexander_of_aphrodisias_de_fato_eng` | 2 | 0 | 0 | 2 | 0 | `urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1` |
| `alexander_of_aphrodisias_de_fato_grc` | 2 | 0 | 0 | 2 | 0 | `urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1` |
| `aspasius_in_en_cag_grc` | 6 | 6 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0615.tlg001.1st1K-grc1` |
| `first1k_tlg0086_tlg002_1st1k_grc1_grc` | 30 | 30 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0086.tlg002.1st1K-grc1` |
| `first1k_tlg0086_tlg017_1st1k_grc1_grc` | 29 | 0 | 0 | 0 | 29 | `urn:cts:greekLit:tlg0086.tlg017.1st1K-grc1` |
| `first1k_tlg0086_tlg022_1st1k_grc1_grc` | 434 | 434 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0086.tlg022.1st1K-grc1` |
| `oga_tlg0086_tlg009_perseus_grc2_grc` | 41 | 39 | 2 | 0 | 0 | `urn:cts:greekLit:tlg0086.tlg009.perseus-grc2` |
| `oga_tlg0086_tlg025_perseus_grc2_grc` | 142 | 138 | 4 | 0 | 0 | `urn:cts:greekLit:tlg0086.tlg025.perseus-grc2` |
| `oga_tlg0086_tlg031_1st1k_grc1_grc` | 71 | 61 | 6 | 4 | 0 | `urn:cts:greekLit:tlg0086.tlg031.1st1K-grc1` |
| `tlg0732_tlg014_eng` | 39 | 0 | 0 | 39 | 0 | `urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1` |
| `tlg0732_tlg014_grc` | 39 | 39 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1` |
| `tlg1264_tlg001_1st1k_grc1_grc` | 88 | 88 | 0 | 0 | 0 | `urn:cts:greekLit:tlg1264.tlg001.1st1K-grc1` |
| `tlg1269_tlg002_1st1k_grc1_grc` | 51 | 1 | 5 | 6 | 39 | `urn:cts:greekLit:tlg1269.tlg002.1st1K-grc1` |
| `tlg2018_tlg001_1st1k_grc1_grc` | 222 | 206 | 1 | 0 | 15 | `urn:cts:greekLit:tlg2018.tlg001.1st1K-grc1` |
| `urn_cts_greeklit_tlg0004_tlg001_grc` | 1211 | 977 | 124 | 110 | 0 | `urn:cts:greekLit:tlg0004.tlg001.perseus-grc2` |
| `urn_cts_greeklit_tlg0007_tlg135_grc` | 6 | 6 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0007.tlg135.perseus-grc2` |
| `urn_cts_greeklit_tlg0007_tlg136_grc` | 47 | 40 | 7 | 0 | 0 | `urn:cts:greekLit:tlg0007.tlg136.perseus-grc2` |
| `urn_cts_greeklit_tlg0057_tlg010_grc` | 3 | 0 | 0 | 0 | 3 | `urn:cts:greekLit:tlg0057.tlg010.1st1K-grc1` |
| `urn_cts_greeklit_tlg0059_tlg002_grc` | 125 | 0 | 0 | 0 | 125 | `urn:cts:greekLit:tlg0059.tlg002.perseus-grc2` |
| `urn_cts_greeklit_tlg0059_tlg004_grc` | 59 | 0 | 0 | 0 | 59 | `urn:cts:greekLit:tlg0059.tlg003.perseus-grc2` |
| `urn_cts_greeklit_tlg0059_tlg012_grc` | 261 | 0 | 0 | 0 | 261 | `urn:cts:greekLit:tlg0059.tlg012.perseus-grc2` |
| `urn_cts_greeklit_tlg0059_tlg030_grc` | 278 | 273 | 5 | 0 | 0 | `urn:cts:greekLit:tlg0059.tlg030.perseus-grc2` |
| `urn_cts_greeklit_tlg0059_tlg034_grc` | 327 | 327 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0059.tlg034.perseus-grc2` |
| `urn_cts_greeklit_tlg0086_tlg003_grc` | 69 | 68 | 1 | 0 | 0 | `urn:cts:greekLit:tlg0086.tlg003.1st1K-grc1` |
| `urn_cts_greeklit_tlg0093_tlg001_grc` | 9 | 0 | 0 | 0 | 9 | `urn:cts:greekLit:tlg0093.tlg001.1st1K-grc1` |
| `urn_cts_greeklit_tlg0562_tlg001_eng` | 19 | 0 | 0 | 16 | 0 | `urn:cts:greekLit:tlg0562.tlg001.perseus-grc2` |
| `urn_cts_greeklit_tlg0562_tlg001_grc` | 580 | 573 | 3 | 1 | 0 | `urn:cts:greekLit:tlg0562.tlg001.perseus-grc2` |
| `urn_cts_greeklit_tlg0645_tlg001_eng` | 2 | 0 | 0 | 2 | 0 | `urn:cts:greekLit:tlg0645.tlg001.1st1K-grc1` |
| `urn_cts_greeklit_tlg0645_tlg001_grc` | 68 | 66 | 0 | 2 | 0 | `urn:cts:greekLit:tlg0645.tlg001.1st1K-grc1` |
| `urn_cts_greeklit_tlg0645_tlg002_grc` | 15 | 15 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0645.tlg002.perseus-grc2` |
| `urn_cts_greeklit_tlg0645_tlg003_eng` | 4 | 0 | 0 | 0 | 4 | `urn:cts:greekLit:tlg0645.tlg003.perseus-grc2` |
| `urn_cts_greeklit_tlg0645_tlg003_grc` | 750 | 0 | 0 | 0 | 750 | `urn:cts:greekLit:tlg0645.tlg003.perseus-grc2` |
| `urn_cts_greeklit_tlg1766_tlg001_eng` | 3 | 0 | 0 | 3 | 0 | `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1` |
| `urn_cts_greeklit_tlg1766_tlg001_grc` | 98 | 5 | 5 | 88 | 0 | `urn:cts:greekLit:tlg1766.tlg001.perseus-grc1` |
| `urn_cts_greeklit_tlg2022_tlg007_grc` | 9 | 9 | 0 | 0 | 0 | `urn:cts:greekLit:tlg2022.tlg007.1st1K-grc1` |
| `urn_cts_greeklit_tlg2022_tlg008_grc` | 31 | 30 | 1 | 0 | 0 | `urn:cts:greekLit:tlg2022.tlg008.1st1K-grc1` |
| `urn_cts_greeklit_tlg2022_tlg009_grc` | 21 | 21 | 0 | 0 | 0 | `urn:cts:greekLit:tlg2022.tlg009.1st1K-grc1` |
| `urn_cts_greeklit_tlg2022_tlg010_grc` | 21 | 20 | 1 | 0 | 0 | `urn:cts:greekLit:tlg2022.tlg010.1st1K-grc1` |
| `urn_cts_greeklit_tlg2022_tlg011_grc` | 33 | 33 | 0 | 0 | 0 | `urn:cts:greekLit:tlg2022.tlg011.1st1K-grc1` |
| `urn_cts_greeklit_tlg2034_tlg009_grc` | 35 | 35 | 0 | 0 | 0 | `urn:cts:greekLit:tlg2034.tlg005.1st1K-grc1` |
| `urn_cts_latinlit_phi0474_phi041_lat` | 22 | 22 | 0 | 0 | 0 | `urn:cts:latinLit:phi0474.phi041.perseus-lat1` |
| `urn_cts_latinlit_phi0474_phi042_lat` | 100 | 99 | 1 | 0 | 0 | `urn:cts:latinLit:phi0474.phi042.perseus-lat1` |
| `urn_cts_latinlit_phi0550_phi001_eng` | 2 | 0 | 0 | 2 | 0 | `urn:cts:latinLit:phi0550.phi001.perseus-lat1` |
| `urn_cts_latinlit_phi0550_phi001_lat` | 300 | 0 | 0 | 299 | 1 | `urn:cts:latinLit:phi0550.phi001.perseus-lat1` |
| `urn_cts_latinlit_phi1017_phi015_lat` | 2135 | 0 | 0 | 5 | 2130 | `urn:cts:latinLit:phi1017.phi015.perseus-lat2` |
| `urn_cts_latinlit_phi1254_phi001_vii_2_lat` | 16 | 13 | 1 | 2 | 0 | `urn:cts:latinLit:phi1254.phi001.perseus-lat2` |
| `urn_cts_latinlit_stoa0275_stoa007_lat` | 31 | 31 | 0 | 0 | 0 | `urn:cts:latinLit:stoa0275.stoa007.opp-lat1` |
| `urn_cts_latinlit_stoa0275_stoa015_lat` | 13 | 13 | 0 | 0 | 0 | `urn:cts:latinLit:stoa0275.stoa015.opp-lat1` |
| `work_clement_stromateis_grc` | 6 | 6 | 0 | 0 | 0 | `urn:cts:greekLit:tlg0555.tlg004.perseus-grc2` |
| `work_republic_plato_c380bce_c3d4e5f6_eng` | 1 | 0 | 0 | 0 | 1 | `urn:cts:greekLit:tlg0059.tlg030.perseus-grc2` |
| `work_republic_plato_c380bce_c3d4e5f6_grc` | 1 | 0 | 0 | 0 | 1 | `urn:cts:greekLit:tlg0059.tlg030.perseus-grc2` |

## Unverifiable Works

These works could not be checked against a GitHub authoritative edition.
They require manual verification (Sources Chrétiennes, local DOCTORAT corpus, non-Perseus editions).

| Work | Passages | Reason |
|------|----------|--------|
| `urn_cts_greeklit_tlg2000_tlg001_grc` | 1355 | fetch_failed_or_empty |
| `sc_origenes_contra_celsum_grc` | 987 | unresolved |
| `sc_origenes_contra_celsum_eng` | 971 | unresolved |
| `urn_cts_greeklit_tlg0544_grc` | 534 | fetch_failed_or_empty |
| `sc464_pamphilus_apologia_pro_origene_eng` | 265 | unresolved |
| `sc464_pamphilus_apologia_pro_origene_lat` | 265 | unresolved |
| `urn_cts_greeklit_tlg0557_grc` | 235 | ambiguous |
| `usener_epicurus_grc` | 193 | ambiguous |
| `urn_cts_greeklit_tlg0557_eng` | 187 | ambiguous |
| `urn_cts_greeklit_tlg0018_tlg001_grc` | 172 | fetch_failed_or_empty |
| `urn_cts_latinlit_stoa0040_stoa003_lat` | 171 | fetch_failed_or_empty |
| `urn_cts_latinlit_stoa0040_stoa003_eng` | 170 | fetch_failed_or_empty |
| `urn_cts_latinlit_stoa0040_stoa001_v_xii_xiv_lat` | 158 | fetch_failed_or_empty |
| `work_epictetus_discourses_eng` | 137 | fetch_failed_or_empty |
| `urn_cts_latinlit_phi2089_phi002_eng` | 129 | fetch_failed_or_empty |
| `urn_cts_latinlit_phi2089_phi002_lat` | 129 | fetch_failed_or_empty |
| `work_new_testament_grc` | 119 | unresolved |
| `oga_tlg0086_tlg010_perseus_grc2_grc` | 116 | ambiguous |
| `sc53bis_hermas_pastor_eng` | 114 | unresolved |
| `sc53bis_hermas_pastor_grc` | 114 | unresolved |
| `sc123_melito_peri_pascha_eng` | 109 | unresolved |
| `sc123_melito_peri_pascha_grc` | 109 | unresolved |
| `urn_cts_greeklit_tlg2959_tlg001_grc` | 97 | fetch_failed_or_empty |
| `sc172_epistula_barnabae_grc` | 88 | unresolved |
| `sc172_epistula_barnabae_eng` | 87 | unresolved |
| `sc167_clemens_epistula_ad_corinthios_eng` | 84 | unresolved |
| `sc167_clemens_epistula_ad_corinthios_grc` | 83 | unresolved |
| `sc507_iustinus_apologia_i_eng` | 83 | unresolved |
| `sc507_iustinus_apologia_i_grc` | 83 | unresolved |
| `sc20_theophilus_ad_autolycum_eng` | 82 | unresolved |
| `sc20_theophilus_ad_autolycum_grc` | 82 | unresolved |
| `urn_cts_greeklit_tlg0059_tlg031_grc` | 76 | fetch_failed_or_empty |
| `urn_cts_latinlit_stoa0255_stoa012_eng` | 68 | fetch_failed_or_empty |
| `urn_cts_latinlit_stoa0255_stoa012_lat` | 68 | fetch_failed_or_empty |
| `urn_cts_greeklit_tlg2042_tlg007_grc` | 51 | fetch_failed_or_empty |
| `sc379_athenagoras_legatio_eng` | 48 | unresolved |
| `urn_cts_latinlit_phi0474_phi049_eng` | 48 | fetch_failed_or_empty |
| `urn_cts_latinlit_phi0474_phi049_lat` | 48 | fetch_failed_or_empty |
| `urn_cts_latinlit_stoa0040_stoa054_lat` | 39 | fetch_failed_or_empty |
| `sc379_athenagoras_legatio_grc` | 38 | unresolved |
| `cpl_evodius_de_fide_lat` | 36 | fetch_failed_or_empty |
| `work_origen_philocalia_grc` | 30 | fetch_failed_or_empty |
| `sc10bis_martyrium_polycarpi_eng` | 27 | unresolved |
| `sc10bis_martyrium_polycarpi_grc` | 27 | unresolved |
| `sc470_aristides_apologia_grc` | 27 | unresolved |
| `urn_cts_latinlit_stoa0040_adv_fulg_lat` | 26 | fetch_failed_or_empty |
| `sc79_chrysostomus_de_providentia_eng` | 25 | unresolved |
| `sc79_chrysostomus_de_providentia_grc` | 25 | unresolved |
| `urn_cts_latinlit_stoa0040_stoa044_eng` | 25 | fetch_failed_or_empty |
| `urn_cts_latinlit_stoa0040_stoa044_lat` | 25 | fetch_failed_or_empty |
| `sc470_aristides_apologia_eng` | 24 | unresolved |
| `work_de_principiis_origen_230s_v2w3x4y5_eng` | 24 | fetch_failed_or_empty |
| `sc10bis_ignatius_ad_ephesios_eng` | 22 | unresolved |
| `sc10bis_ignatius_ad_ephesios_grc` | 22 | unresolved |
| `urn_cts_latinlit_stoa0040_stoa045_lat` | 21 | fetch_failed_or_empty |
| `work_origen_philocalia_eng` | 21 | fetch_failed_or_empty |
| `urn_cts_greeklit_tlg0007_tlg099_eng` | 19 | fetch_failed_or_empty |
| `urn_cts_greeklit_tlg0007_tlg099_grc` | 19 | fetch_failed_or_empty |
| `oga_tlg0086_tlg010_perseus_grc2_eng` | 18 | ambiguous |
| `sc10bis_ignatius_ad_magnesios_eng` | 16 | unresolved |
| `sc10bis_ignatius_ad_magnesios_grc` | 16 | unresolved |
| `sc10bis_ignatius_ad_trallianos_eng` | 14 | unresolved |
| `sc10bis_ignatius_ad_trallianos_grc` | 14 | unresolved |
| `sc10bis_ignatius_ad_philadelphenos_eng` | 12 | unresolved |
| `sc10bis_ignatius_ad_philadelphenos_grc` | 12 | unresolved |
| `sc10bis_ignatius_ad_smyrnaeos_eng` | 12 | unresolved |
| `sc10bis_ignatius_ad_smyrnaeos_grc` | 12 | unresolved |
| `sc10bis_ignatius_ad_romanos_eng` | 11 | unresolved |
| `sc10bis_ignatius_ad_romanos_grc` | 11 | unresolved |
| `urn_cts_greeklit_tlg2000_tlg001_iii_1_grc` | 10 | fetch_failed_or_empty |
| `sc10bis_ignatius_ad_polycarpum_eng` | 9 | unresolved |
| `sc10bis_ignatius_ad_polycarpum_grc` | 9 | unresolved |
| `phi1471_phi001_lat` | 7 | fetch_failed_or_empty |
| `urn_cts_greeklit_tlg2959_tlg001_eng` | 7 | fetch_failed_or_empty |
| `urn_cts_greeklit_tlg1311_tlg001_grc` | 6 | fetch_failed_or_empty |
| `urn_cts_latinlit_stoa0040_stoa001_v_xii_xiv_eng` | 6 | fetch_failed_or_empty |
| `digiliblt_dlt000607_lat` | 5 | superseded 2026-08-24 placeholder slot; DLT000607 is a genuine distinct later-edition record, while the current text is the fingerprinted `stoa0071b.stoa001` CHMTL/Wrobel cohort |
| `sc528_pseudo_iustinus_cohortatio_eng` | 5 | unresolved |
| `sc528_pseudo_iustinus_cohortatio_grc` | 5 | unresolved |
| `sc123_melito_apologia_ad_antoninum_eng` | 4 | unresolved |
| `sc123_melito_apologia_ad_antoninum_grc` | 4 | unresolved |
| `sc268_origenes_peri_archon_eng` | 4 | unresolved |
| `sc268_origenes_peri_archon_grc` | 4 | unresolved |
| `augustine_of_hippo_confessions_viii_eng` | 2 | unresolved |
| `cicero_cicero_de_fato_eng` | 2 | unresolved |
| `sc123_apollinaris_peri_pascha_eng` | 2 | unresolved |
| `sc123_apollinaris_peri_pascha_grc` | 2 | unresolved |
| `sc123_melito_de_anima_et_corpore_eng` | 2 | unresolved |
| `sc123_melito_de_anima_et_corpore_grc` | 2 | unresolved |
| `sc123_melito_eclogae_eng` | 2 | unresolved |
| `sc123_melito_eclogae_grc` | 2 | unresolved |
| `sc31_melito_peri_pascha_iv_eng` | 2 | unresolved |
| `sc31_melito_peri_pascha_iv_grc` | 2 | unresolved |
| `titus_lucretius_carus_lucretius_de_rerum_natura_eng` | 2 | unresolved |
| `work_melito_peri_pascha_eng` | 2 | fetch_failed_or_empty |
| `work_melito_peri_pascha_grc` | 2 | fetch_failed_or_empty |
| `work_origen_commentary_romans_eng` | 2 | unresolved |
| `work_origen_commentary_romans_grc` | 2 | unresolved |
| `alexander_of_aphrodisias_alexander_of_aphrodisias_de_fato` | 1 | unresolved |
| `aristotle_of_stagira_nicomachean_ethics_iii_1` | 1 | unresolved |
| `boethius_anicius_manlius_severinus_boethius_simultaneous_and_perfect_possession_o` | 1 | unresolved |
| `epictetus_of_hierapolis_epictetus_discourses` | 1 | unresolved |
| `origen_of_alexandria_origen_de_principiis_peri_archon` | 1 | unresolved |
| `plotinus_enneades_iv_4_30_self_determining_principle_english` | 1 | fetch_failed_or_empty |
| `plotinus_plotinus_enneads` | 1 | unresolved |
| `plotinus_plotinus_enneads_iii_1_on_fate` | 1 | unresolved |
| `plotinus_plotinus_enneads_vi_8` | 1 | unresolved |
| `urn_cts_greeklit_tlg0059_tlg031_eng` | 1 | fetch_failed_or_empty |
| `urn_cts_greeklit_tlg0720_tlg001` | 1 | fetch_failed_or_empty |
| `urn_cts_latinlit_phi1254_phi001` | 1 | fetch_failed_or_empty |
| `work_de_principiis_origen_230s_v2w3x4y5_grc` | 1 | unresolved |
| `work_irenaeus_adversus_haereses_book3_eng` | 1 | unresolved |
| `work_irenaeus_adversus_haereses_book3_grc` | 1 | unresolved |
| `work_irenaeus_adversus_haereses_book4_eng` | 1 | unresolved |
| `work_irenaeus_adversus_haereses_book4_grc` | 1 | unresolved |
| `work_origen_de_oratione_eng` | 1 | unresolved |
| `work_origen_de_oratione_grc` | 1 | unresolved |
| `work_septuagint` | 1 | unresolved |
| `work_theophilus_ad_autolycum_book2_eng` | 1 | unresolved |
| `work_theophilus_ad_autolycum_book2_grc` | 1 | unresolved |
