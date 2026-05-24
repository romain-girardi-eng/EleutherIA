# Corpus Ingestion — Scaife Full Works (Plan 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the **58 Scaife-resolvable** lean-core works (of the 75 in `data/corpus/manifest.jsonl`) to **full-work passage coverage** — backfill their work-level CTS URNs, fetch the complete text from the Perseus/Scaife CTS API, and upsert the missing (non-cited) passages without disturbing the cited ones — then re-export the git snapshot.

**Architecture:** Plan 2 of 4 from `docs/superpowers/specs/2026-05-24-corpus-recovery-passage-grounding-design.md`. The corpus already holds the *cited* passages of each work; this fills each Scaife work out to its complete text. Reuses the existing `database/scripts/fetch_scaife_work.py` (CTS fetch + TEI strip) and the `passages`/`ancient_works` schema; adds a manifest-driven runner so ingestion is batch + idempotent instead of per-work-manual. The 17 Sources-Chrétiennes/DOCTORAT works (no Scaife URN) and 3 ambiguous-URN works are out of scope here → Plan 2b.

**Tech Stack:** Python 3.14, `asyncpg` (Supabase via `DATABASE_URL` in `.env`), the Perseus/Scaife CTS API, pytest. Reuses `scripts/corpus_lib.py` (deterministic JSONL) and `database/scripts/fetch_scaife_work.py`. Run corpus scripts as `python -m scripts.<name>` from the repo root.

---

## Preconditions

- `data/corpus/manifest.jsonl` exists (75 lean works; `cts_urn`/`source` blank).
- `data/corpus/passages.jsonl` exists (16,620 passages; each has `work_canonical_id` + `cts_urn`).
- Academic integrity (non-negotiable): ingest **ancient text only** — never apparatus, commentary, introductions, or modern translations. Critical/openly-licensed editions only. Preserve diacritics byte-for-byte. Never fabricate or "fill" missing text.

## File Structure

- Create `scripts/corpus_urn.py` — work-level CTS-URN derivation from passage URNs.
- Create `scripts/backfill_manifest_urns.py` — write derived URNs + ingest classification into the manifest.
- Create `scripts/corpus_ingest_merge.py` — pure merge logic: given existing + fetched passages, compute the rows to insert (dedup by CTS URN).
- Create `scripts/ingest_corpus_work.py` — manifest-driven runner: fetch one Scaife work, merge, upsert into Supabase.
- Create `tests/test_corpus_urn.py`, `tests/test_corpus_ingest_merge.py`.
- Reuse: `database/scripts/fetch_scaife_work.py`, `scripts/corpus_lib.py`, `scripts/export_corpus_snapshot.py`.

---

## Task 1: Work-level CTS-URN derivation

**Files:**
- Create: `scripts/corpus_urn.py`
- Test: `tests/test_corpus_urn.py`

A passage URN like `urn:cts:greekLit:tlg0086.tlg028:9.18a` has the work URN `urn:cts:greekLit:tlg0086.tlg028` (first 4 colon-fields). A work is *resolvable* if all its passage URNs share one work URN; *ambiguous* if there are several; *unresolved* if none have a valid URN.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_corpus_urn.py
from scripts.corpus_urn import derive_work_urn


def test_single_work_urn():
    urns = ["urn:cts:greekLit:tlg0086.tlg028:9.18a",
            "urn:cts:greekLit:tlg0086.tlg028:9.19b"]
    assert derive_work_urn(urns) == ("urn:cts:greekLit:tlg0086.tlg028", "resolved")


def test_ambiguous_when_multiple_work_urns():
    urns = ["urn:cts:greekLit:tlg0086.tlg028:9",
            "urn:cts:greekLit:tlg0086.tlg010:1"]
    urn, status = derive_work_urn(urns)
    assert status == "ambiguous"
    assert urn is None


def test_unresolved_when_no_valid_urn():
    assert derive_work_urn(["", "chap.1.par.2", None]) == (None, "unresolved")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_corpus_urn.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'scripts.corpus_urn'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/corpus_urn.py
"""Derive a work-level CTS URN from a work's passage URNs."""
from __future__ import annotations


def work_urn_of(passage_urn: str | None) -> str | None:
    if not passage_urn:
        return None
    parts = passage_urn.split(":")
    if len(parts) < 5 or not parts[3]:
        return None  # need urn:cts:<corpus>:<work>:<ref>
    return ":".join(parts[:4])


def derive_work_urn(passage_urns: list[str | None]) -> tuple[str | None, str]:
    found = {w for u in passage_urns if (w := work_urn_of(u))}
    if not found:
        return None, "unresolved"
    if len(found) > 1:
        return None, "ambiguous"
    return next(iter(found)), "resolved"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_corpus_urn.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/corpus_urn.py tests/test_corpus_urn.py
git commit -m "feat(corpus): work-level CTS-URN derivation"
```

---

## Task 2: Backfill the manifest with URNs + ingest classification

**Files:**
- Create: `scripts/backfill_manifest_urns.py`
- (No new unit test — composes Task 1 + corpus_lib, both tested; verified by the run + counts.)

For each manifest work, gather its passages' URNs from `data/corpus/passages.jsonl`, derive the work URN, and set `cts_urn`, `source` (`scaife:<urn>` when resolved), and `ingest_class` (`scaife` | `manual_source` | `ambiguous`). Writes the manifest back (deterministic).

- [ ] **Step 1: Write the implementation**

```python
# scripts/backfill_manifest_urns.py
"""Backfill work-level CTS URNs + ingest classification into the corpus manifest.

ingest_class: 'scaife' (resolved URN -> fetchable), 'manual_source' (no URN,
needs a DOCTORAT/SC edition), 'ambiguous' (>1 work URN, needs disambiguation).
Dry-run by default; --commit writes data/corpus/manifest.jsonl.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from scripts.corpus_lib import read_jsonl, write_jsonl
from scripts.corpus_urn import derive_work_urn

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "corpus" / "manifest.jsonl"
PASSAGES = ROOT / "data" / "corpus" / "passages.jsonl"


def main(commit: bool) -> int:
    urns_by_work: dict[str, list[str]] = defaultdict(list)
    for p in read_jsonl(PASSAGES):
        urns_by_work[p["work_canonical_id"]].append(p.get("cts_urn"))

    manifest = read_jsonl(MANIFEST)
    counts = {"scaife": 0, "manual_source": 0, "ambiguous": 0}
    for w in manifest:
        urn, status = derive_work_urn(urns_by_work.get(w["canonical_id"], []))
        if status == "resolved":
            w["cts_urn"] = urn
            w["source"] = f"scaife:{urn}"
            w["ingest_class"] = "scaife"
        elif status == "ambiguous":
            w["ingest_class"] = "ambiguous"
        else:
            w["ingest_class"] = "manual_source"
        counts[w["ingest_class"]] += 1

    print(f"scaife: {counts['scaife']}  manual_source: {counts['manual_source']}  ambiguous: {counts['ambiguous']}")
    if not commit:
        print("[DRY-RUN] --commit to write manifest")
        return 0
    write_jsonl(MANIFEST, sorted(manifest, key=lambda w: w["canonical_id"]))
    print(f"wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    raise SystemExit(main(ap.parse_args().commit))
```

- [ ] **Step 2: Run dry-run, confirm the expected split (~58 scaife / ~17 manual / ~3 ambiguous)**

Run: `.venv/bin/python -m scripts.backfill_manifest_urns`
Expected: `scaife: 58  manual_source: 17  ambiguous: 3` (numbers may shift ±a few; confirm they're in this range).

- [ ] **Step 3: Apply + commit**

```bash
.venv/bin/python -m scripts.backfill_manifest_urns --commit
git add scripts/backfill_manifest_urns.py data/corpus/manifest.jsonl
git commit -m "feat(corpus): backfill work CTS URNs + ingest classification into manifest"
```

---

## Task 3: Pure passage-merge logic (full-work without clobbering cited passages)

**Files:**
- Create: `scripts/corpus_ingest_merge.py`
- Test: `tests/test_corpus_ingest_merge.py`

Given the existing passages for a work (already in the corpus, some cited) and the freshly-fetched full set from Scaife, compute which fetched passages are NEW (by CTS URN). Existing passages are never modified or duplicated — full-work coverage is achieved purely by *adding* the missing ones. Returns the new rows in canonical schema.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_corpus_ingest_merge.py
from scripts.corpus_ingest_merge import passages_to_insert


def test_only_new_urns_are_inserted():
    existing = [{"cts_urn": "urn:cts:x:w:1", "text_content": "a"}]
    fetched = [
        {"cts_urn": "urn:cts:x:w:1", "text_content": "a"},   # already present
        {"cts_urn": "urn:cts:x:w:2", "text_content": "b"},   # new
        {"cts_urn": "urn:cts:x:w:3", "text_content": "c"},   # new
    ]
    new = passages_to_insert(existing, fetched, work_canonical_id="w", start_seq=10)
    assert [p["cts_urn"] for p in new] == ["urn:cts:x:w:2", "urn:cts:x:w:3"]
    assert [p["sequence_number"] for p in new] == [10, 11]
    assert all(p["work_canonical_id"] == "w" for p in new)


def test_empty_text_is_skipped_never_fabricated():
    existing = []
    fetched = [{"cts_urn": "urn:cts:x:w:1", "text_content": "   "},
               {"cts_urn": "urn:cts:x:w:2", "text_content": "real"}]
    new = passages_to_insert(existing, fetched, work_canonical_id="w", start_seq=0)
    assert [p["cts_urn"] for p in new] == ["urn:cts:x:w:2"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_corpus_ingest_merge.py -v`
Expected: FAIL `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/corpus_ingest_merge.py
"""Compute which fetched passages are new to a work (dedup by CTS URN).

Full-work coverage is achieved by ADDING missing passages only; existing
(possibly cited) passages are never modified. Empty/whitespace text is skipped —
we never fabricate or store blank ancient text.
"""
from __future__ import annotations


def passages_to_insert(existing: list[dict], fetched: list[dict],
                       work_canonical_id: str, start_seq: int) -> list[dict]:
    have = {p.get("cts_urn") for p in existing}
    out: list[dict] = []
    seq = start_seq
    for f in fetched:
        urn = f.get("cts_urn")
        text = (f.get("text_content") or "").strip()
        if not urn or urn in have or not text:
            continue
        have.add(urn)
        out.append({
            "work_canonical_id": work_canonical_id,
            "cts_urn": urn,
            "canonical_ref": urn.split(":")[-1] if ":" in urn else urn,
            "sequence_number": seq,
            "text_content": f.get("text_content"),
        })
        seq += 1
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_corpus_ingest_merge.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/corpus_ingest_merge.py tests/test_corpus_ingest_merge.py
git commit -m "feat(corpus): passage-merge logic (add missing, never clobber cited)"
```

---

## Task 4: Manifest-driven Scaife ingestion runner

**Files:**
- Create: `scripts/ingest_corpus_work.py`
- (No unit test — network + DB orchestration; verified by per-work coverage checks in Task 5. It composes the tested Tasks 1–3 + `fetch_scaife_work.py`.)

For one manifest work with `ingest_class == "scaife"`: derive its work URN, fetch the full work via the existing `database/scripts/fetch_scaife_work.py` (use its `--discover` + passage-fetch functions — import them; do not shell out), normalize fetched sections to `{cts_urn, text_content}`, compute new passages via `passages_to_insert`, and INSERT them into `free_will.passages` for the work's `work_id` inside one transaction. Dry-run by default; `--commit` writes. Idempotent: a second run finds 0 new passages.

- [ ] **Step 1: Implement the runner**

Read `database/scripts/fetch_scaife_work.py` first to import its fetch/parse helpers (`build_library_reffs_url`, `build_library_passage_url`, `_fetch_xml`, and the section-extraction function). Then implement `scripts/ingest_corpus_work.py` that:
  1. Loads `data/corpus/manifest.jsonl`, selects the work by `--canonical-id`; asserts `ingest_class == "scaife"`.
  2. Resolves `work_id` from `free_will.ancient_works WHERE canonical_id = $1`.
  3. Loads existing passages for that `work_id` (cts_urn, max sequence_number).
  4. Fetches the full work text from Scaife by work URN (reuse the fetch helpers).
  5. `new = passages_to_insert(existing, fetched, canonical_id, start_seq=max_seq+1)`.
  6. Prints `would insert N passages (existing M, fetched F)`; on `--commit`, inserts in one transaction.

Use the exact insert columns of `free_will.passages`: `work_id, canonical_ref, cts_urn, sequence_number, text_content, passage_role` (`'original'`). Set `char_length`/`word_count` from the text.

- [ ] **Step 2: Dry-run on one small work (e.g. Aristotle *De Interpretatione*)**

Run: `.venv/bin/python -m scripts.ingest_corpus_work --canonical-id <de_int_canonical_id>`
Expected: prints existing/fetched/would-insert counts; fetched count ≈ the Scaife reff count for De Int. (≈ a few dozen). No DB write.

- [ ] **Step 3: Commit the runner**

```bash
git add scripts/ingest_corpus_work.py
git commit -m "feat(corpus): manifest-driven Scaife full-work ingestion runner"
```

---

## Task 5: Run ingestion in batches + verify coverage + re-export

**Files:** none new — operational. Modifies `data/corpus/passages.jsonl` (via re-export) and the Supabase `passages` table.

- [ ] **Step 1: Ingest in small batches, dry-run then commit, highest-value works first**

For each `scaife` work (start with the thesis-central ones — Aristotle EN/De Int., Alexander *De Fato*, Cicero *De Fato*/*De Div.*, Plotinus *Enn.* III.1, Plato *Republic*/*Laws*): run the runner dry, eyeball the would-insert count against the known Scaife reff count, then `--commit`. Stop and investigate any work whose fetched count is 0 or wildly off (Scaife URN wrong / edition missing).

```bash
.venv/bin/python -m scripts.ingest_corpus_work --canonical-id <id>            # dry
.venv/bin/python -m scripts.ingest_corpus_work --canonical-id <id> --commit   # write
```

- [ ] **Step 2: Verify per-work coverage**

After each batch, confirm passage counts grew and the cited passages are intact (none lost):

```bash
.venv/bin/python -m scripts.check_corpus_invariants
```
Expected: `dangling citation->passage: 0` still holds (we only added passages). Investigate if it rises.

- [ ] **Step 3: Re-export the git snapshot + commit**

```bash
.venv/bin/python -m scripts.export_corpus_snapshot
git add data/corpus/passages.jsonl data/corpus/citations.jsonl
git commit -m "feat(corpus): full-work Scaife ingestion — <N> works, +<M> passages"
```

If `data/corpus/passages.jsonl` crosses ~50MB after ingestion, add a follow-up task to move it to Git LFS.

---

## Self-Review notes

- Tasks 1–3 are TDD (deterministic). Tasks 4–5 are operational ETL — verified by coverage + the invariants gate, not unit tests (network fetches and per-work Scaife quirks can't be meaningfully unit-tested).
- **Never clobber cited passages:** `passages_to_insert` only adds new CTS URNs; existing passages (and their `passage_citations`) are untouched. Confirm the dangling-citation count stays 0 after every batch.
- **Integrity:** spot-check a few ingested passages against the critical edition; confirm diacritics intact and no apparatus/translation leaked.
- **Ambiguous (3 works):** excluded here; they need manual work-URN disambiguation (likely multi-edition or mixed refs) — handle in Plan 2b.

## Follow-on plans

- **Plan 2b — DOCTORAT/SC ingestion:** the 17 `manual_source` works (Sources Chrétiennes editions already partly in the corpus) + the 3 ambiguous works. Verify completeness against the SC editions on disk; assign stable non-CTS canonical refs.
- **Plan 3 — Reconcile + overlay curation:** fix the 187 citations→missing-KG-nodes; bidirectional grounding pass; flip the corpus gate to `--strict`.
- **Plan 4 — Corpus deploy pipeline:** `git → Supabase` for the corpus, mirroring the KG deploy.
