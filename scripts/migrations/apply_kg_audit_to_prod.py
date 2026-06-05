#!/usr/bin/env python3
"""Apply a KG-audit changelog to the live Supabase mirror (free_will.kg_nodes).

Idempotent + guarded: every UPDATE carries a WHERE clause matching the OLD value,
so re-running is safe and a row that already changed (or drifted) is skipped, not
clobbered. Reads .env for DATABASE_URL (never prints it). Deferred until prod is
reachable; harmless to run repeatedly.

Usage: .venv/bin/python scripts/migrations/apply_kg_audit_to_prod.py --wave wave1 [--commit]
Without --commit it runs read-only (counts what WOULD change).
"""
import json, os, re, sys, asyncio, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def p(*a): return os.path.join(ROOT, *a)

def db_url():
    for l in open(p('.env')):
        if l.startswith('DATABASE_URL='):
            return l.split('=', 1)[1].strip().strip('"').strip("'")
    raise SystemExit('no DATABASE_URL in .env')

async def run(wave, commit):
    import asyncpg
    rows = [json.loads(l) for l in open(p('data/audit', f'{wave}_changelog.jsonl')) if l.strip()]
    print(f"changelog entries: {len(rows)}  (mode: {'COMMIT' if commit else 'dry-run'})")
    c = await asyncio.wait_for(asyncpg.connect(db_url()), timeout=20)
    tx = c.transaction(); await tx.start()
    applied = skipped = 0
    try:
        for r in rows:
            nid, field, old, new, kind = r['node_id'], r['field'], r.get('old'), r['new'], r['kind']
            if kind == 'metadata':
                key = field.split('.', 1)[1]
                # only update when the live value still equals the recorded OLD
                res = await c.execute(
                    "UPDATE free_will.kg_nodes "
                    "SET metadata = jsonb_set(COALESCE(metadata,'{}'::jsonb), $2, to_jsonb($3::text)) "
                    "WHERE id=$1 AND COALESCE(metadata->>$4, '') = COALESCE($5,'')",
                    nid, [key], new, key, (str(old) if old is not None else None))
            elif kind == 'attr':
                res = await c.execute(
                    f"UPDATE free_will.kg_nodes SET {field}=$2 WHERE id=$1 AND {field} IS NOT DISTINCT FROM $3",
                    nid, new, old)
            elif kind == 'desc_surgical':
                res = await c.execute(
                    "UPDATE free_will.kg_nodes SET description = replace(description, $2, $3) "
                    "WHERE id=$1 AND position($2 in description) > 0",
                    nid, old, new)
            else:
                print("  skip unknown kind:", kind); continue
            n = int(res.split()[-1])
            if n: applied += 1
            else: skipped += 1
        print(f"would apply: {applied}  skipped(idempotent/drift): {skipped}")
        if commit:
            await tx.commit(); print("COMMITTED")
        else:
            await tx.rollback(); print("rolled back (dry-run)")
    except Exception:
        await tx.rollback(); raise
    finally:
        await c.close()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--wave', default='wave1')
    ap.add_argument('--commit', action='store_true')
    a = ap.parse_args()
    asyncio.run(run(a.wave, a.commit))
