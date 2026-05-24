# Corpus Foundation & Backup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the EleutherIA corpus recoverable from git and integrity-checked — a git-tracked manifest (scope-of-truth + rebuild recipe), a git-tracked snapshot of the current corpus (passages + citations), and a CI gate that fails on dangling citations.

**Architecture:** This is Plan 1 of 4 from the corpus design spec (`docs/superpowers/specs/2026-05-24-corpus-recovery-passage-grounding-design.md`). It builds the *foundation* layers (manifest + git backing + invariants gate) without yet ingesting new text. Phase 0 (manifest) and the Phase 4 backup/gate scaffolding live here; Plans 2–4 cover full-work ingestion, citation reconciliation, and overlay curation. All scripts follow the repo convention: dry-run by default, `--commit` to write, deterministic sorted JSONL.

**Tech Stack:** Python 3.14, `asyncpg` (Supabase Postgres via `DATABASE_URL` in `.env`), pytest, deterministic JSONL (sorted keys, compact separators). Mirrors `scripts/export_kg_snapshot.py` and `scripts/deploy_kg_to_supabase.py`.

---

## File Structure

- Create `scripts/corpus_lib.py` — shared helpers: canonical JSONL serialization, manifest/passage/citation row schemas, JSONL read/write. One responsibility: corpus data (de)serialization + schema.
- Create `scripts/derive_corpus_manifest.py` — Phase 0: derive in-scope works from the git KG → `data/corpus/manifest.jsonl`.
- Create `scripts/export_corpus_snapshot.py` — pull `passages` + `passage_citations` from Supabase → `data/corpus/passages.jsonl` + `data/corpus/citations.jsonl`.
- Create `scripts/check_corpus_invariants.py` — gate: 0 dangling citations; report orphans. Reads the git snapshot.
- Create `tests/test_corpus_lib.py`, `tests/test_derive_corpus_manifest.py`, `tests/test_check_corpus_invariants.py`.
- Modify `.github/workflows/ci.yml` — add a "Corpus invariants gate" job step.
- Create `data/corpus/` (holds `manifest.jsonl`, `passages.jsonl`, `citations.jsonl`).

---

## Task 1: Shared corpus serialization library

**Files:**
- Create: `scripts/__init__.py` (empty — makes `scripts/` an importable package so `from scripts.corpus_lib import …` and `python -m scripts.<name>` work)
- Create: `scripts/corpus_lib.py`
- Test: `tests/test_corpus_lib.py`

> **Convention note:** existing scripts are loaded by importlib-by-path and run as `python scripts/foo.py`. The corpus scripts instead share `corpus_lib`, so they form a package and are ALWAYS run from the repo root as `python -m scripts.<name>` (running `python scripts/foo.py` would break the `from scripts.corpus_lib` import). pytest finds them because `tests/` has `__init__.py`, so pytest puts the repo root on `sys.path`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_corpus_lib.py
import json
from pathlib import Path

from scripts.corpus_lib import canonical_dumps, read_jsonl, write_jsonl


def test_canonical_dumps_is_sorted_and_compact():
    assert canonical_dumps({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_canonical_dumps_preserves_unicode():
    # Greek diacritics must survive verbatim, not be \u-escaped
    assert canonical_dumps({"t": "προαίρεσις"}) == '{"t":"προαίρεσις"}'


def test_write_then_read_roundtrip(tmp_path: Path):
    rows = [{"id": "b"}, {"id": "a"}]
    p = tmp_path / "out.jsonl"
    write_jsonl(p, rows)
    # written file ends with a single trailing newline, one row per line
    assert p.read_text(encoding="utf-8") == '{"id":"b"}\n{"id":"a"}\n'
    assert read_jsonl(p) == rows
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_corpus_lib.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.corpus_lib'`

- [ ] **Step 3: Create the package marker, then the implementation**

First make `scripts/` a package: `touch scripts/__init__.py`

```python
# scripts/corpus_lib.py
"""Shared (de)serialization + schema helpers for the EleutherIA corpus layer.

Deterministic JSONL (sorted keys, compact separators, unicode preserved) so
git diffs stay clean and round-trips are byte-stable. Mirrors the conventions in
scripts/export_kg_snapshot.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Column order is documentation only; canonical_dumps sorts keys anyway.
MANIFEST_FIELDS = ("canonical_id", "label", "author", "period", "cts_urn",
                   "source", "status", "expected_passages")
PASSAGE_FIELDS = ("passage_id", "work_canonical_id", "cts_urn", "canonical_ref",
                  "sequence_number", "text_content")
CITATION_FIELDS = ("passage_id", "kg_node_id", "citation_type", "confidence")


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(canonical_dumps(row))
            f.write("\n")
    tmp.replace(path)


def read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_corpus_lib.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/__init__.py scripts/corpus_lib.py tests/test_corpus_lib.py
git commit -m "feat(corpus): shared deterministic JSONL lib for corpus layer"
```

---

## Task 2: Derive the corpus manifest from the git KG (Phase 0)

**Files:**
- Create: `scripts/derive_corpus_manifest.py`
- Test: `tests/test_derive_corpus_manifest.py`

Context: in-scope works are derived from `data/kg/nodes.jsonl`. A work is in scope if (a) it is a node of `type == "work"`, or (b) it is referenced as `work_canonical_id` in a `type == "passage"` node's metadata. Author comes from an `authored_by` edge (work → person) in `data/kg/edges.jsonl`; the person's label is looked up in nodes. `cts_urn` and `source` are proposed from the work node's metadata when present, else left empty with `status="needs_source"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_derive_corpus_manifest.py
from scripts.derive_corpus_manifest import derive_manifest


def test_derive_includes_work_nodes_and_passage_referenced_works():
    nodes = [
        {"id": "work_de_int", "type": "work", "label": "De Interpretatione",
         "period": "Classical", "metadata": {"cts_urn": "urn:cts:greekLit:tlg0086.tlg028"}},
        {"id": "person_aristotle", "type": "person", "label": "Aristotle"},
        {"id": "pass_1", "type": "passage", "label": "DI 9",
         "metadata": {"work_canonical_id": "work_de_int"}},
        # a work only referenced by a passage, no work node of its own
        {"id": "pass_2", "type": "passage", "label": "EN III.5",
         "metadata": {"work_canonical_id": "work_en"}},
    ]
    edges = [
        {"source": "work_de_int", "target": "person_aristotle", "relation": "authored_by"},
    ]
    rows = derive_manifest(nodes, edges)
    by_id = {r["canonical_id"]: r for r in rows}

    assert set(by_id) == {"work_de_int", "work_en"}
    assert by_id["work_de_int"]["author"] == "Aristotle"
    assert by_id["work_de_int"]["cts_urn"] == "urn:cts:greekLit:tlg0086.tlg028"
    assert by_id["work_de_int"]["source"] == "scaife:urn:cts:greekLit:tlg0086.tlg028"
    assert by_id["work_de_int"]["status"] == "pending"
    # work with no work node and no urn -> flagged for manual sourcing
    assert by_id["work_en"]["status"] == "needs_source"
    assert by_id["work_en"]["source"] == ""


def test_derive_is_sorted_by_canonical_id():
    nodes = [
        {"id": "work_b", "type": "work", "label": "B"},
        {"id": "work_a", "type": "work", "label": "A"},
    ]
    rows = derive_manifest(nodes, [])
    assert [r["canonical_id"] for r in rows] == ["work_a", "work_b"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_derive_corpus_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.derive_corpus_manifest'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/derive_corpus_manifest.py
"""Phase 0: derive the corpus manifest (in-scope works) from the git KG.

A work is in scope if it is a `type==work` node, or it is referenced via
`work_canonical_id` on a `type==passage` node. The manifest is the curated
scope-of-truth AND the deterministic rebuild recipe; this script proposes rows,
the user then curates `data/corpus/manifest.jsonl` by hand.

Dry-run by default; --commit writes data/corpus/manifest.jsonl (never clobbers
an existing curated manifest unless --force).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.corpus_lib import read_jsonl, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
MANIFEST_PATH = ROOT / "data" / "corpus" / "manifest.jsonl"


def _meta(node: dict) -> dict[str, Any]:
    m = node.get("metadata")
    if isinstance(m, str) and m:
        try:
            return json.loads(m)
        except json.JSONDecodeError:
            return {}
    return m or {}


def derive_manifest(nodes: list[dict], edges: list[dict]) -> list[dict]:
    nodes_by_id = {n["id"]: n for n in nodes}
    # author lookup: work -> person label via authored_by
    author_of: dict[str, str] = {}
    for e in edges:
        if e.get("relation") == "authored_by":
            src, tgt = e.get("source"), e.get("target")
            person = nodes_by_id.get(tgt)
            if src and person:
                author_of[src] = person.get("label", "")

    in_scope: set[str] = set()
    for n in nodes:
        if n.get("type") == "work":
            in_scope.add(n["id"])
        elif n.get("type") == "passage":
            wid = _meta(n).get("work_canonical_id")
            if wid:
                in_scope.add(wid)

    rows: list[dict] = []
    for wid in in_scope:
        work = nodes_by_id.get(wid)
        meta = _meta(work) if work else {}
        cts = meta.get("cts_urn", "") if work else ""
        has_work_node = work is not None
        source = f"scaife:{cts}" if cts else ""
        if has_work_node and cts:
            status = "pending"
        else:
            status = "needs_source"
        rows.append({
            "canonical_id": wid,
            "label": (work.get("label") if work else "") or "",
            "author": author_of.get(wid, ""),
            "period": (work.get("period") if work else "") or "",
            "cts_urn": cts,
            "source": source,
            "status": status,
            "expected_passages": None,
        })
    rows.sort(key=lambda r: r["canonical_id"])
    return rows


def main(commit: bool, force: bool) -> int:
    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    rows = derive_manifest(nodes, edges)
    n_pending = sum(1 for r in rows if r["status"] == "pending")
    n_needs = sum(1 for r in rows if r["status"] == "needs_source")
    print(f"derived {len(rows)} works ({n_pending} pending, {n_needs} needs_source)")
    if not commit:
        print("[DRY-RUN] --commit to write data/corpus/manifest.jsonl")
        return 0
    if MANIFEST_PATH.exists() and not force:
        print(f"REFUSING: {MANIFEST_PATH} exists (curated). Use --force to overwrite.")
        return 1
    write_jsonl(MANIFEST_PATH, rows)
    print(f"wrote {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    raise SystemExit(main(a.commit, a.force))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_derive_corpus_manifest.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Generate the manifest and commit script + manifest**

```bash
.venv/bin/python -m scripts.derive_corpus_manifest            # dry-run, eyeball counts
.venv/bin/python -m scripts.derive_corpus_manifest --commit   # writes data/corpus/manifest.jsonl
git add scripts/derive_corpus_manifest.py tests/test_derive_corpus_manifest.py data/corpus/manifest.jsonl
git commit -m "feat(corpus): derive in-scope works manifest from git KG (Phase 0)"
```

---

## Task 3: Export the live corpus to git (passages + citations snapshot)

**Files:**
- Create: `scripts/export_corpus_snapshot.py`
- (No unit test — this is a thin DB-export operation; correctness is verified by the round-trip + the invariants gate in Task 4. Manual verification step included.)

Context: connects to Supabase via `DATABASE_URL` in `.env` (asyncpg), reads `free_will.passages` and `free_will.passage_citations`, writes deterministic sorted JSONL to `data/corpus/passages.jsonl` and `data/corpus/citations.jsonl`. Text-only: it selects the ancient text columns, never apparatus/commentary (those are not columns in `passages` anyway). This is the immediate git backup of the current corpus.

- [ ] **Step 1: Write the implementation**

```python
# scripts/export_corpus_snapshot.py
"""Export Supabase corpus (passages + passage_citations) to git-tracked JSONL.

The durable, copyright-safe backup of the corpus text (ancient text only — the
passages table holds no apparatus/commentary). Deterministic sorted output so
git diffs are a clean time-series. Reads DATABASE_URL from .env.

Usage:  .venv/bin/python -m scripts.export_corpus_snapshot
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from scripts.corpus_lib import write_jsonl

ROOT = Path(__file__).resolve().parents[1]
PASSAGES_PATH = ROOT / "data" / "corpus" / "passages.jsonl"
CITATIONS_PATH = ROOT / "data" / "corpus" / "citations.jsonl"

PASSAGE_SQL = """
SELECT p.passage_id::text AS passage_id,
       w.canonical_id     AS work_canonical_id,
       p.cts_urn, p.canonical_ref, p.sequence_number, p.text_content
FROM free_will.passages p
JOIN free_will.ancient_works w ON w.work_id = p.work_id
"""
CITATION_SQL = """
SELECT passage_id::text AS passage_id, kg_node_id, citation_type, confidence
FROM free_will.passage_citations
"""


def _db_url() -> str:
    for line in open(ROOT / ".env"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


async def main() -> int:
    import asyncpg

    conn = await asyncio.wait_for(asyncpg.connect(_db_url()), timeout=30)
    try:
        passages = [dict(r) for r in await conn.fetch(PASSAGE_SQL)]
        citations = [dict(r) for r in await conn.fetch(CITATION_SQL)]
    finally:
        await conn.close()

    passages.sort(key=lambda r: (r["work_canonical_id"] or "", r["sequence_number"] or 0, r["passage_id"]))
    citations.sort(key=lambda r: (r["passage_id"], r["kg_node_id"], r.get("citation_type") or ""))

    write_jsonl(PASSAGES_PATH, passages)
    write_jsonl(CITATIONS_PATH, citations)
    print(f"wrote {len(passages)} passages -> {PASSAGES_PATH}")
    print(f"wrote {len(citations)} citations -> {CITATIONS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

- [ ] **Step 2: Run the export and verify counts match the DB**

Run: `.venv/bin/python -m scripts.export_corpus_snapshot`
Expected: prints `wrote 16620 passages` and `wrote 19971 citations` (the known current counts; exact numbers may differ slightly — they must match the DB, confirm with the next command).

Run: `.venv/bin/python -c "from scripts.corpus_lib import read_jsonl; print(len(read_jsonl(__import__('pathlib').Path('data/corpus/passages.jsonl'))), len(read_jsonl(__import__('pathlib').Path('data/corpus/citations.jsonl'))))"`
Expected: two integers matching the export output.

- [ ] **Step 3: Verify integrity (valid JSONL, diacritics intact)**

Run: `.venv/bin/python -c "from scripts.corpus_lib import read_jsonl; from pathlib import Path; rows=read_jsonl(Path('data/corpus/passages.jsonl')); g=[r for r in rows if any(0x370<=ord(c)<=0x3ff for c in (r.get('text_content') or ''))]; print('passages with Greek:', len(g)); print('sample:', (g[0]['text_content'][:60] if g else 'none'))"`
Expected: a non-zero count and a sample line showing intact polytonic Greek.

- [ ] **Step 4: Commit**

```bash
git add scripts/export_corpus_snapshot.py data/corpus/passages.jsonl data/corpus/citations.jsonl
git commit -m "feat(corpus): git-backed snapshot of live corpus (passages + citations)"
```

---

## Task 4: Corpus invariants gate (dangling-citation check)

**Files:**
- Create: `scripts/check_corpus_invariants.py`
- Test: `tests/test_check_corpus_invariants.py`

Context: the gate reads the git snapshot (`data/corpus/passages.jsonl`, `data/corpus/citations.jsonl`) and `data/kg/nodes.jsonl`. It enforces: (1) every citation's `passage_id` exists in passages (no dangling), (2) every citation's `kg_node_id` exists in the KG. It returns a non-zero exit code and a report when violated. It currently EXPECTS dangling citations (the known 19,971 vs 16,620), so the gate is introduced in `--report` mode (always exits 0, prints counts) and is flipped to `--strict` (exit 1 on any dangling) at the end of Plan 3 once reconciliation is done.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_check_corpus_invariants.py
from scripts.check_corpus_invariants import find_violations


def test_no_violations_when_all_resolve():
    passages = [{"passage_id": "p1"}]
    citations = [{"passage_id": "p1", "kg_node_id": "n1"}]
    node_ids = {"n1"}
    v = find_violations(passages, citations, node_ids)
    assert v["dangling_passage"] == []
    assert v["dangling_node"] == []


def test_detects_dangling_passage_and_node():
    passages = [{"passage_id": "p1"}]
    citations = [
        {"passage_id": "p1", "kg_node_id": "n1"},     # ok
        {"passage_id": "pX", "kg_node_id": "n1"},     # passage missing
        {"passage_id": "p1", "kg_node_id": "nX"},     # node missing
    ]
    node_ids = {"n1"}
    v = find_violations(passages, citations, node_ids)
    assert v["dangling_passage"] == [{"passage_id": "pX", "kg_node_id": "n1"}]
    assert v["dangling_node"] == [{"passage_id": "p1", "kg_node_id": "nX"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_check_corpus_invariants.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.check_corpus_invariants'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/check_corpus_invariants.py
"""Corpus integrity gate: every citation must resolve to a passage AND a KG node.

--report (default): print counts, always exit 0 (use while dangling refs are
expected, i.e. before Plan 3 reconciliation).
--strict: exit 1 if any dangling reference exists (flip to this in CI once the
corpus is reconciled).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.corpus_lib import read_jsonl

ROOT = Path(__file__).resolve().parents[1]
PASSAGES_PATH = ROOT / "data" / "corpus" / "passages.jsonl"
CITATIONS_PATH = ROOT / "data" / "corpus" / "citations.jsonl"
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"


def find_violations(passages: list[dict], citations: list[dict],
                    node_ids: set[str]) -> dict[str, list[dict]]:
    passage_ids = {p["passage_id"] for p in passages}
    dangling_passage = [c for c in citations if c.get("passage_id") not in passage_ids]
    dangling_node = [c for c in citations if c.get("kg_node_id") not in node_ids]
    return {"dangling_passage": dangling_passage, "dangling_node": dangling_node}


def main(strict: bool) -> int:
    passages = read_jsonl(PASSAGES_PATH)
    citations = read_jsonl(CITATIONS_PATH)
    node_ids = {json.loads(l)["id"] for l in open(NODES_PATH, encoding="utf-8") if l.strip()}
    v = find_violations(passages, citations, node_ids)
    dp, dn = len(v["dangling_passage"]), len(v["dangling_node"])
    print(f"citations={len(citations)} passages={len(passages)}")
    print(f"dangling citation->passage: {dp}")
    print(f"dangling citation->kg_node: {dn}")
    if strict and (dp or dn):
        print("STRICT: dangling references present -> FAIL")
        return 1
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    raise SystemExit(main(ap.parse_args().strict))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_check_corpus_invariants.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the gate in report mode against the real snapshot**

Run: `.venv/bin/python -m scripts.check_corpus_invariants`
Expected: exit 0; prints the current dangling count (`dangling citation->passage: 3351` order-of-magnitude — confirms the gate sees the known data-loss gap).

- [ ] **Step 6: Commit**

```bash
git add scripts/check_corpus_invariants.py tests/test_check_corpus_invariants.py
git commit -m "feat(corpus): integrity gate for dangling citations (report mode)"
```

---

## Task 5: Wire the corpus gate into CI

**Files:**
- Modify: `.github/workflows/ci.yml` (add a step to the existing `kg-invariants` job, after the SHACL gate step)

Context: the `kg-invariants` job already checks out the repo and sets up Python 3.14. Add a corpus-gate step in `--report` mode (non-blocking now; flips to `--strict` at the end of Plan 3). The gate reads git files only — no DB access needed in CI.

- [ ] **Step 1: Add the CI step**

In `.github/workflows/ci.yml`, inside the `kg-invariants` job, immediately AFTER the existing step `- name: Validate KG invariants and write quality report` (which runs `python scripts/validate_kg_shacl.py --max-examples 100`), insert:

```yaml
      - name: Corpus invariants gate (report)
        run: python -m scripts.check_corpus_invariants
```

- [ ] **Step 2: Verify the workflow YAML is valid and the step runs locally**

Run: `.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok')"`
Expected: `yaml ok`

Run: `.venv/bin/python -m scripts.check_corpus_invariants; echo "exit: $?"`
Expected: `exit: 0`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci(corpus): add corpus invariants gate (report mode)"
```

---

## Self-Review notes (for the implementer)

- The gate is intentionally **report-mode** in Plan 1 — dangling citations are expected until Plan 3 reconciles them. Do not set `--strict` in CI yet.
- `data/corpus/passages.jsonl` may be large (tens of MB once full works are ingested in Plan 2). If it crosses GitHub's 50MB limit, switch it to Git LFS in a dedicated task at that point (out of scope for Plan 1).
- All corpus scripts are run as `python -m scripts.x` from the repo root (Task 1 creates `scripts/__init__.py`). Do not run them as `python scripts/x.py` — the `from scripts.corpus_lib` import requires package context.

---

## Follow-on plans (not in this plan)

- **Plan 2 — Full-work ingestion (Phase 1):** manifest-driven ingestion of full works at passage level from Scaife/Perseus + DOCTORAT critical editions; populate `passages`; re-export snapshot.
- **Plan 3 — Reconcile + overlay curation (Phases 2–3):** relink `passage_citations` by CTS URN; bidirectional curation (add missing citations, demote irrelevant, verify existing against re-ingested text); flip the corpus gate to `--strict`.
- **Plan 4 — Corpus deploy pipeline (Phase 4 finalize):** `deploy_corpus_to_supabase.py` mirroring the KG deploy (idempotent, snapshot, delete-guarded); CI deploy job.
