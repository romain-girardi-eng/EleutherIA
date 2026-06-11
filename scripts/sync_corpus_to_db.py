#!/usr/bin/env python3
"""Replace the live corpus tables with the git-tracked corpus mirror.

The mirror (data/corpus/passages.jsonl + citations.jsonl + manifest.jsonl) is
canonical after the 2026-06 audit campaigns; the DB corpus was a partial
derivation from KG passage nodes. This script rebuilds free_will.ancient_works,
free_will.passages and free_will.passage_citations from the mirror, inside one
transaction.

Usage:
  set -a; source .env; set +a
  .venv/bin/python scripts/sync_corpus_to_db.py            # dry run (counts)
  .venv/bin/python scripts/sync_corpus_to_db.py --commit
"""
import argparse
import asyncio
import json
import os
import re
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GREEK = re.compile(r'[Ͱ-Ͽἀ-῿]')


def p(*a):
    return os.path.join(ROOT, *a)


def loadl(path):
    with open(p(path)) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def infer_language(wcid: str, sample_text: str) -> str:
    if wcid.endswith('_eng'):
        return 'eng'
    if wcid.endswith('_lat') or 'latinlit' in wcid:
        return 'lat'
    if GREEK.search(sample_text or ''):
        return 'grc'
    return 'lat'


def work_uuid(canonical_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'eleutheria:work:{canonical_id}'))


async def main(commit: bool):
    import asyncpg
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise SystemExit('DATABASE_URL not set (set -a; source .env; set +a)')

    manifest = {m['canonical_id']: m for m in loadl('data/corpus/manifest.jsonl')}
    passages = list(loadl('data/corpus/passages.jsonl'))
    citations = list(loadl('data/corpus/citations.jsonl'))

    works = {}
    for row in passages:
        wcid = row.get('work_canonical_id') or 'unknown_work'
        if wcid not in works:
            man = manifest.get(wcid, {})
            works[wcid] = {
                'work_id': work_uuid(wcid),
                'canonical_id': wcid,
                'title': man.get('title') or wcid,
                'author': man.get('author') or 'Unknown',
                'language': infer_language(wcid, row.get('text_content') or ''),
                'period': man.get('period'),
                'source': man.get('source'),
                'cts_urn': (man.get('cts_urn') or None) or None,
                'n': 0,
            }
        works[wcid]['n'] += 1

    pids = {r['passage_id'] for r in passages}
    kept_cit = [c for c in citations if c.get('passage_id') in pids]
    print(f'mirror: works={len(works)} passages={len(passages)} '
          f'citations={len(citations)} (linkable {len(kept_cit)})')
    if not commit:
        print('dry run — pass --commit to apply')
        return

    conn = await asyncio.wait_for(asyncpg.connect(url), timeout=30)
    try:
        # TRUNCATE in its own transaction so space is reclaimed before the
        # bulk load (a single transaction doubles storage and can fill the
        # project disk).
        await conn.execute(
            'TRUNCATE free_will.passage_citations, free_will.passages, '
            'free_will.ancient_works CASCADE')
        if True:
            await conn.executemany(
                '''INSERT INTO free_will.ancient_works
                   (work_id, canonical_id, title, author, language, period,
                    source, cts_urn, total_divisions)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)''',
                [(w['work_id'], w['canonical_id'], w['title'], w['author'],
                  w['language'], w['period'], w['source'], w['cts_urn'], w['n'])
                 for w in works.values()])
            rows = []
            for i, r in enumerate(passages):
                txt = r.get('text_content') or ''
                seq = r.get('sequence_number')
                try:
                    seq = int(seq)
                except (TypeError, ValueError):
                    seq = i + 1
                urn = r.get('cts_urn')
                if urn in ('None', 'null', ''):
                    urn = None
                rows.append((
                    r['passage_id'],
                    works[r.get('work_canonical_id') or 'unknown_work']['work_id'],
                    r.get('canonical_ref') or f'#{seq}',
                    urn, seq, txt, len(txt), len(txt.split()), 'original'))
            await conn.executemany(
                '''INSERT INTO free_will.passages
                   (passage_id, work_id, canonical_ref, cts_urn,
                    sequence_number, text_content, char_length, word_count,
                    passage_role)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)''', rows)
            crows = []
            seen = set()
            for c in kept_cit:
                key = (c['passage_id'], c.get('kg_node_id'))
                if key in seen:
                    continue
                seen.add(key)
                conf = c.get('confidence')
                try:
                    conf = float(conf) if conf is not None else None
                except (TypeError, ValueError):
                    conf = None
                crows.append((
                    str(uuid.uuid5(uuid.NAMESPACE_URL,
                                   f'eleutheria:cit:{key[0]}:{key[1]}')),
                    c['passage_id'], c.get('kg_node_id'),
                    c.get('citation_type'), conf, c.get('notes')))
            await conn.executemany(
                '''INSERT INTO free_will.passage_citations
                   (citation_id, passage_id, kg_node_id, citation_type,
                    confidence, notes)
                   VALUES ($1,$2,$3,$4,$5,$6)''', crows)
        for t in ('ancient_works', 'passages', 'passage_citations'):
            print(t, await conn.fetchval(
                f'select count(*) from free_will.{t}'))
    finally:
        await conn.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true')
    asyncio.run(main(ap.parse_args().commit))
