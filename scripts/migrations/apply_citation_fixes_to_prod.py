#!/usr/bin/env python3
"""Apply citation remove/repoint changelog to free_will.passage_citations.

Guarded + idempotent: a remove only deletes a row that still exists; a repoint
updates the old row's passage_id, falling back to delete-old if the new target
row already exists (avoids unique-constraint violation). Prod may have diverged
from the mirror — mismatched rows are simply skipped, never forced.

Usage: .venv/bin/python scripts/migrations/apply_citation_fixes_to_prod.py [--commit]
"""
import json, os, asyncio, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def p(*a): return os.path.join(ROOT, *a)
def db_url():
    for l in open(p('.env')):
        if l.startswith('DATABASE_URL='):
            return l.split('=', 1)[1].strip().strip('"').strip("'")
    raise SystemExit('no DATABASE_URL')

async def run(commit):
    import asyncpg
    rows = [json.loads(l) for l in open(p('data/audit/cite_fix_changelog.jsonl')) if l.strip()]
    print(f"citation ops: {len(rows)} (mode: {'COMMIT' if commit else 'dry-run'})")
    c = await asyncio.wait_for(asyncpg.connect(db_url()), timeout=20)
    tx = c.transaction(); await tx.start()
    removed = repointed = skipped = 0
    try:
        for r in rows:
            nid = r['kg_node_id']
            if r['op'] == 'remove':
                res = await c.execute(
                    "DELETE FROM free_will.passage_citations WHERE kg_node_id=$1 AND passage_id=$2",
                    nid, r['passage_id'])
                if int(res.split()[-1]): removed += 1
                else: skipped += 1
            elif r['op'] == 'repoint':
                old, new = r['old_passage_id'], r['new_passage_id']
                exists_new = await c.fetchval(
                    "SELECT 1 FROM free_will.passage_citations WHERE kg_node_id=$1 AND passage_id=$2", nid, new)
                if exists_new:
                    res = await c.execute(
                        "DELETE FROM free_will.passage_citations WHERE kg_node_id=$1 AND passage_id=$2", nid, old)
                else:
                    res = await c.execute(
                        "UPDATE free_will.passage_citations SET passage_id=$3 WHERE kg_node_id=$1 AND passage_id=$2",
                        nid, old, new)
                if int(res.split()[-1]): repointed += 1
                else: skipped += 1
        print(f"removed: {removed}  repointed: {repointed}  skipped(drift/idempotent): {skipped}")
        if commit: await tx.commit(); print("COMMITTED")
        else: await tx.rollback(); print("rolled back (dry-run)")
    except Exception:
        await tx.rollback(); raise
    finally:
        await c.close()

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--commit', action='store_true')
    asyncio.run(run(ap.parse_args().commit))
