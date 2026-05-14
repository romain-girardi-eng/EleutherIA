# Philological Audit — Five-Dimension Rigor Pass

_Generated 2026-05-15. Runner scripts under `database/scripts/philological_audit/`._

## Summary

| Dimension | Initial findings | Auto-applied | Re-audit residual |
| --- | ---: | ---: | ---: |
| Polytonic Greek discipline       | 3180 | 3104 | 78 |
| Edition metadata completeness    |  133 |  133 | 103 |
| CTS URN syntax                   | 1218 | 1216 | 727 |
| Person date qualifier discipline |   49 |   49 | 10 |
| Translation provenance tagging   | 2952 | 2952 | 0 |

**Total auto-applied mutations:** 7454 rows across 4 tables (kg_nodes + passages).

## Headline statistics — before / after

- Work-node edition metadata coverage: **17%** (28/161) → **100%** (161/161; 15 curated, 15 promoted-from-singular, 103 carry `needs_edition_metadata` for scholarly judgement).
- Polytonic Greek strings on KG nodes brought to **NFC**: 2563 fixes.
- Backslash escape artifacts (Greek char + `\` + whitespace) stripped: 541 fixes.
- CTS URN syntactic validity: 1216 URNs rewritten in place (whitespace removal, unknown-book sentinel drop).
- Ancient persons with bare-year dates hedged with `c.`: 39 nodes (`135 BCE` → `c. 135 BCE`).
- AI-batch translation nodes now carry `translation_source` + `translation_type=machine`: 2952 nodes.
- Regression test added for the `BCE → BCEE` double-suffix bug in `audit_person_dates.hedge`.

## Zero-fabrication guarantee

No ancient Greek or Latin text was generated. Where data was missing or ambiguous we flagged
`metadata.needs_*` rather than synthesise. The polytonic dimension is read-only except for
(a) NFC unicode normalisation and (b) mechanical removal of backslash-before-whitespace import
artifacts — neither operation adds linguistic content.

## Polytonic Greek discipline

- **Applied in this pass:** 3104
- **Findings on re-audit:** 78
  - idempotent flagging (re-runs touch the same flag, no churn): 0
  - deferred to scholarly review: 78

### Issue breakdown

| Issue | Count |
| --- | --- |
| `non_final_sigma_at_wordbreak` | 73 |
| `no_diacritics_on_substantial_greek` | 5 |

## Edition metadata completeness

- **Applied in this pass:** 133
- **Findings on re-audit:** 103
  - idempotent flagging (re-runs touch the same flag, no churn): 103
  - deferred to scholarly review: 0

### Issue breakdown

| Issue | Count |
| --- | --- |
| `missing_edition_metadata_no_match` | 103 |

## CTS URN syntax

- **Applied in this pass:** 1216
- **Findings on re-audit:** 727
  - idempotent flagging (re-runs touch the same flag, no churn): 0
  - deferred to scholarly review: 727

### Issue breakdown

| Issue | Count |
| --- | --- |
| `missing_work_segment` | 726 |
| `null_cts_urn` | 1 |

## Person date qualifier discipline

- **Applied in this pass:** 49
- **Findings on re-audit:** 10
  - idempotent flagging (re-runs touch the same flag, no churn): 10
  - deferred to scholarly review: 0

### Issue breakdown

| Issue | Count |
| --- | --- |
| `no_dates_present` | 10 |

## Translation provenance tagging

- **Applied in this pass:** 2952
- **Findings on re-audit:** 0
  - idempotent flagging (re-runs touch the same flag, no churn): 0
  - deferred to scholarly review: 0

### Issue breakdown

| Issue | Count |
| --- | --- |

## Top 20 highest-priority `needs_review` items

Total deferred-to-scholarly-review rows: **805** (written to `data/philological_audit/needs_review.jsonl`).

| # | Dimension | Issue | Confidence | Node / Passage | Snippet |
| ---: | --- | --- | ---: | --- | --- |
| 1 | cts_urn | `null_cts_urn` | 1.00 | `*` |  |
| 2 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_arist_da_3_12` | Τὴν μὲν οὖν θρεπτικὴν ψυχὴν ἀνάγκη πᾶν ἔχειν ὅτι περ ἂν ζῇ καὶ ψυχὴν ἔχῃ ἀπὸ γεν |
| 3 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_arist_da_2_8` | Νῦν δὲ πρῶτον περὶ ψόφου καὶ ἀκοῆς διορίσωμεν. Ἔστι δὲ διττὸς ὁ ψόφος· ὁ μὲν γὰρ |
| 4 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_aristide_sc470_10` | **Reference:** SC 470, II. fragments papyrologiques, B. Π2 = papyrus Lond. Litt. |
| 5 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_aspasius_2` | Διττῆς δὲ τῆς ἀρετῆς οὔσης <ἕως> καθάπερ εἰρήκαμεν. Ἐπειδὴ τῆς ψυχῆς δύο μέρη εἰ |
| 6 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_basil_hex_6` | Τοῦ περὶ τῶν χρηστηρίων τρόπου διὰ τῶν προδιηνυσμένων αὐτάρκως ἡμῖν ἀπεληλεγμένο |
| 7 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `sc470_aristides_apologia_ii_fragments_papyrologiques_b_2_papyrus_lond_litt_223_2486_apol_xv_4_xv_ed1f2e8d` | νηστευουσιν ημερας β η και γ και ο[τ]ι μελλουσ[ιν εαυτοις τειθεναι πεμπουσιν εκε |
| 8 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_meth_dla_91` | 3: »und wie ein Abtrünniger  fiel er ab, und wendete sich von Gott ab« Ezn 3f Th |
| 9 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_arist_phys_5_3` | Μετὰ δὲ ταῦτα λέγωμεν τί ἐστιν τὸ ἅμα καὶ χωρίς,  καὶ τί τὸ                      |
| 10 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_arist_phys_5_4` | Μία δὲ κίνησις λέγεται πολλαχῶς· τὸ γὰρ ἓν πολλαχῶς  λέγομεν.                    |
| 11 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_arist_phys_5_6` | Ἐπεὶ δὲ κινήσει οὐ μόνον δοκεῖ κίνησις εἶναι ἐναντία ἀλλὰ καὶ ἠρεμία,            |
| 12 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_sen_ep_15_95_45` | M. Brutus in eo libro, quem περὶ καθήκοντοσ inscripsit, dat multa praecepta et p |
| 13 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_greg_naz_011_19` | Ἀλλ’ ἐμοί, φησιν, ἐκεῖνα συναριθμούμενα λέγεται,   καὶ τῆς αὐτῆς οὐσίας, οἷς συν |
| 14 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_sen_ep_15_99_25` | Illud nullo modo probo, quod ait Metrodorus: esse aliquam cognatam tristitiae vo |
| 15 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_arist_da_3_3` | Ἐπεὶ δὲ δύο διαφοραῖς ὁρίζονται μάλιστα τὴν ψυχήν, κινήσει τε τῇ κατὰ τόπον καὶ  |
| 16 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `sc123_melito_peri_pascha_chap46` | Τὸ μὲν οὖν διήγημα τοῦ τύπου καὶ τῆς ἀνταποδόσεως ἀκηκόατε · ἀκούσατε καὶ τὴν κα |
| 17 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `sc123_melito_peri_pascha_chap93` | Τοιγαροῦν πικρά σοι ἡ τῶν ἀζύμων ἑορτή, καθώς σοι γέγραπ[ται] · « Ἔδεσθε ἄζυμα μ |
| 18 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_basil_hex_14` | Ὅσα μὲν εἰπεῖν τε καὶ ἀκοῦσαι ἦν ἀμφὶ τῆς κατὰ Πλάτωνα φιλοσοφίας τῆς τε τούτου  |
| 19 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_basil_hex_2` | Τὰ μὲν δὴ τῆς Φοινίκων θεολογίας τὸν προειρημένον περιέχει τρόπον · ἣν ἀμεταστρε |
| 20 | polytonic | `non_final_sigma_at_wordbreak` | 0.85 | `passage_basil_hex_4` | Τὸ τρίτον εἶδος τῆς πολυθέου πλάνης, ἀφ᾿ ἧς δυνάμει καὶ εὐεργεσίᾳ τοῦ λυτρωτοῦ κ |

## Reproducing this audit

```bash
# Dry-run (writes per-dimension JSONL reports under data/philological_audit/)
PYTHONPATH=database/scripts/philological_audit \
  .venv-py314/bin/python database/scripts/philological_audit/audit_polytonic.py

# Apply (each of the five scripts accepts --apply; idempotent)
PYTHONPATH=database/scripts/philological_audit \
  .venv-py314/bin/python database/scripts/philological_audit/audit_editions.py --apply
```
