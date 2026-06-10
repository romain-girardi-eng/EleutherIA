# Canonical Reference Style Guide

Rules for `canonical_ref` on corpus passages and KG citations. Goal: every ref is
short, unambiguous, machine-matchable, and follows the abbreviation a scholar
would use. The CTS URN carries the machine-precise locus; `canonical_ref` is the
human-facing citation.

## General rules

1. **Abbreviated work title + arabic locus**: `Diss. 1.7.16`, `PH 3.269`,
   `De Fato 14`, `Curatio 6.14`. No author name (the work id carries it), no
   "Book/Section" prose, no volume/edition info (edition belongs in the work's
   `metadata.edition`).
2. **Arabic numerals everywhere**, including book numbers (`Diss. 3.22`, not
   `Diss. III.22`). Exception: works conventionally cited by Roman book +
   chapter in modern scholarship may keep it when the whole work already uses
   it consistently (De Civitate Dei `V.IX.3`).
3. **Ranges** with a hyphen, repeating only the changing level: `PH 3.269-273`,
   `Diss. 3.18.8-3.20.10`.
4. **Edition-page citations** (CAG, Bruns, SVF, Stephanus, Bekker) state the
   unit: `Mantissa p. 169`, `Quaest. p. 23`, `Soph. 237a`, `SVF I 537`.
5. **No fabricated loci.** A sequence/chunk number is not a locus. If the true
   locus is unknown, say so (`metadata.cts_urn_note`) instead of inventing one
   — see the 2026-06-11 Sextus/Epictetus remap in
   `data/audit/primary_wave/chunk_locus_changelog.jsonl`.
6. **Special parts**: prologue `prol.`, pinax/table of contents `pin.`,
   chapter title `tit.`, fragment `fr. N`.

## Per-corpus abbreviations in use

| Work | Style |
|---|---|
| Epictetus Dissertationes / Enchiridion | `Diss. 1.1.3` / `Ench. 20` |
| Sextus PH / Adversus mathematicos | `PH 1.13` / `M. 9.49` |
| Plotinus | `Enn. VI.8.1` (Roman ennead is the scholarly convention) |
| Plato (Stephanus) | `Soph. 237a`, `Rep. 617e` |
| Alexander | `De Fato 14`, `Mantissa p. 169`, `Quaest. p. 23`, `Eth. Probl. p. 120` |
| Ammonius | `In De Int. 131` (CAG page) |
| Theodoret | `Curatio 6.14`, prologue `Curatio prol.1` |
| John of Damascus | `Exp. fid. 39` (Kotter continuous section) |
| Augustine De Civ. Dei | `V.IX.3` (existing corpus convention) |
| Justin Dialogue | bare `41.1` (existing corpus convention) |
| LXX/NT books | `Wis. 1.1`, `4 Macc. 18.16` |

When adding a new work, follow the abbreviation of its standard critical
edition or LSJ/OCD conventions, and keep ONE style for all passages of the work
(`scripts/check_greek_gate.py` guards text authenticity; ref-style drift is
caught by the per-work style survey in the audit tooling).
