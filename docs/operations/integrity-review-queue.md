# Integrity Review Queue

Unified, item-by-item review workflow for every deferred/pending finding from
the corpus & KG integrity audits (June 2026 waves). One consolidated queue, one
CLI, one human decision per finding — **no bulk operations, ever**.

## Components

| Piece | Path |
|---|---|
| Queue builder | `scripts/audit_queue/build_queue.py` |
| Consolidated queue | `data/audit/review_queue.jsonl` |
| CLI | `eleutheria audit-queue list / show / adjudicate` (`cli/audit_queue.py`) |
| Flagging SQL generator | `scripts/audit_queue/generate_flag_sql.py` |
| SQL shape template | `scripts/audit_queue/flag_integrity_status.sql.template` |
| Tests | `tests/test_audit_queue.py` |

## Sources consumed (read-only)

`build_queue.py` normalizes the **pending/deferred** findings in `data/audit/`
into one schema. Originals are never modified.

| Source file | Category | Notes |
|---|---|---|
| `greek_insertions_deferred.jsonl` | `greek_fabrication` | Confirmed fabricated Greek; the deferral concerns verifying the *replacement* text against an edition, so entries carry `evidence.verdict = "confirmed"` |
| `greek_unmatched.jsonl` | `greek_unverified` | Greek runs not matched to any corpus passage — unverified, not (yet) judged fabricated |
| `cite_fix_deferred.jsonl`, `cite_descfix_deferred.jsonl` | `citation_fix` | Repoint/remove citation ops below the auto-apply confidence bar, and non-surgical description rewrites |
| `wave1_deferred.jsonl`, `wave3_deferred.jsonl`, `wave1_greek_deferred.jsonl`, `wave2_anach_deferred.jsonl` | by `dimension`: `J1_false_fact` → `false_fact`, `J2_greek` → `greek_fabrication`, `J3_biblio` → `bibliographic`, `J4_anachronism` → `anachronism` | Wave-style scholarly deferred items |
| `mechanical_findings.jsonl` | `mechanical` | Scanner output (`cts_urn_format`, `uncited_claim_node`, `duplicate_node_candidate`, `isolated_claim_node`). Some may already have been fixed by waves 1–3 — adjudicate those as `fixed` during review |

**Not** ingested: `*_changelog.jsonl` (already-applied fixes), `strata.jsonl`
(node inventory, not findings), `coverage_fair_results.json` / `fair_baseline.json`
(benchmarks), `*.txt` worklists, `wf_*.js` (workflow scripts), per-node
subdirectories (`wave1/`, `wave2/`, `wave3/`, `cite_fix/`, …: raw audit artifacts
whose verdicts are already summarized in the deferred/changelog files).

## Unified entry schema

```json
{
  "id": "rq_<sha1(source_file:source_line)[:12]>",
  "source_file": "greek_unmatched.jsonl",
  "source_line": 42,
  "category": "greek_unverified",
  "node_id": "concept_...",
  "passage_id": null,
  "summary": "…",
  "evidence": { "verbatim subset of the source record": "…" },
  "proposed_action": "…",
  "status": "pending",
  "adjudicated_by": null,
  "adjudicated_at": null,
  "resolution": null,
  "note": null
}
```

Ids are a stable hash of `(source_file, source_line)`: rebuilding the queue is
idempotent and **never clobbers adjudications** — re-runs preserve `status`,
`resolution`, `note`, `adjudicated_by`, `adjudicated_at` for existing ids.

## Workflow

```bash
# 1. (Re)build the queue from data/audit/ (safe to re-run any time)
python3 scripts/audit_queue/build_queue.py

# 2. Browse
eleutheria audit-queue list --category greek_fabrication --status pending
eleutheria audit-queue list -c greek_unverified -n 200

# 3. Inspect ONE finding in full (evidence + proposed action)
eleutheria audit-queue show rq_ab12cd34ef56

# 4. Verify it yourself (corpus query, critical edition, DOCTORAT library…),
#    then adjudicate THAT ONE item:
eleutheria audit-queue adjudicate rq_ab12cd34ef56 \
    --resolution accepted --note "checked Otto/TLG Orat. 7.1 — fabricated run confirmed"
```

Resolutions: `accepted` (finding is correct, fix to be applied),
`rejected` (finding is wrong / false positive), `fixed` (already corrected,
e.g. by a previous wave). Adjudication updates **only**
`data/audit/review_queue.jsonl`.

### The no-bulk rule

Per project policy (zero hallucination, no auto-fix): **every item is verified
and adjudicated individually**. The CLI deliberately has no `apply-all`,
no multi-id adjudication, no filter-based adjudication. The `--note` flag is
mandatory: record what you actually verified. Do not script loops around
`adjudicate`.

## Flagging `metadata.integrity_status` (generated SQL — reviewed, never auto-run)

```bash
python3 -m scripts.audit_queue.generate_flag_sql --output /tmp/flag_integrity.sql
```

From the **greek categories only** (`greek_fabrication`, `greek_unverified`),
the generator emits one `UPDATE` per node — each on its own line with a
comment carrying the queue id(s) — setting `metadata.integrity_status`:

| Value | When |
|---|---|
| `fabrication_confirmed_pending_fix` | entry adjudicated `accepted`, or source audit verdict was already `confirmed` |
| `greek_unverified` | entry still pending, no confirmed verdict |
| *(no statement)* | entry adjudicated `rejected` or `fixed` |

If a node appears in multiple entries, `fabrication_confirmed_pending_fix` wins.
The statement shape is documented in
`scripts/audit_queue/flag_integrity_status.sql.template`.

**Execution is manual and selective**: read the generated file, run the
statements you accept one at a time (psql against the target DSN), delete the
rest. The generator itself never connects to any database. Re-generate after
each adjudication session — flags follow the queue state (a `rejected`
adjudication drops the node's UPDATE on the next generation; clear any
previously applied flag by hand with
`metadata = metadata - 'integrity_status'`).

## How GraphRAG consumes `integrity_status`

The GraphRAG context-pack filter (added concurrently in
`graphrag/src/eleutheria_graphrag/agents/graph_nodes.py`) reads
`metadata.integrity_status` when assembling synthesis context:

- nodes flagged `fabrication_confirmed_pending_fix` are **excluded** from the
  context pack (their fabricated Greek must never reach the LLM as evidence);
- nodes flagged `greek_unverified` are demoted/annotated so the synthesis
  prompt never presents their Greek as verified quotation.

Once a node's description is actually corrected (the "pending fix" lands), the
flag should be cleared in the same reviewed migration that applies the fix.
