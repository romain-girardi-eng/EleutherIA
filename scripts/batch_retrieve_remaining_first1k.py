#!/usr/bin/env python3
"""
Remaining First1KGreek Retrieval
=================================
Retrieves Philo, Athanasius, Nemesius, more Plutarch, more Eusebius, etc.

NO HALLUCINATION - Direct TEI-XML parsing from verified sources.
"""

import sys
import time
from retrieve_first1k_tei import First1KGreekRetriever
import json
import requests

def get_available_works(tlg_code, max_works=15):
    """Check what works are actually available"""
    url = f"https://api.github.com/repos/OpenGreekAndLatin/First1KGreek/contents/data/{tlg_code}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            works = [item['name'] for item in resp.json() if item['type'] == 'dir']
            return works[:max_works]
    except:
        pass
    return []

def main():
    """Batch retrieve remaining First1KGreek works"""

    retriever = First1KGreekRetriever()

    print("="*80)
    print("REMAINING FIRST1KGREEK RETRIEVAL")
    print("="*80)
    print("\nRetrieving Philo, Athanasius, Nemesius, more Plutarch/Eusebius...")

    works = []

    # PHILO - 31 works available, high priority!
    print("\nChecking Philo works (31 available)...")
    philo_works = get_available_works('tlg0018', max_works=15)
    for work_code in philo_works:
        works.append({
            'name': f'Philo, {work_code}',
            'tlg_code': 'tlg0018',
            'work_code': work_code,
            'edition': '1st1K-grc1',
            'author': 'Philo',
            'work_title': f'Work {work_code}',
            'citations': 3
        })

    # ATHANASIUS - 6 works
    print("Checking Athanasius works (6 available)...")
    athanasius_works = get_available_works('tlg2035', max_works=6)
    for work_code in athanasius_works:
        works.append({
            'name': f'Athanasius, {work_code}',
            'tlg_code': 'tlg2035',
            'work_code': work_code,
            'edition': '1st1K-grc1',
            'author': 'Athanasius',
            'work_title': f'Work {work_code}',
            'citations': 3
        })

    # NEMESIUS - 1 work
    print("Checking Nemesius works (1 available)...")
    nemesius_works = get_available_works('tlg2050', max_works=1)
    for work_code in nemesius_works:
        works.append({
            'name': f'Nemesius, {work_code}',
            'tlg_code': 'tlg2050',
            'work_code': work_code,
            'edition': '1st1K-grc1',
            'author': 'Nemesius',
            'work_title': f'Work {work_code}',
            'citations': 5
        })

    # More PLUTARCH - 2 works total
    print("Checking remaining Plutarch works...")
    plutarch_works = get_available_works('tlg0007', max_works=2)
    for work_code in plutarch_works:
        # Skip if we already have it
        if work_code != 'tlg096':  # We already got this one
            works.append({
                'name': f'Plutarch, {work_code}',
                'tlg_code': 'tlg0007',
                'work_code': work_code,
                'edition': '1st1K-grc1',
                'author': 'Plutarch',
                'work_title': f'Work {work_code}',
                'citations': 4
            })

    # More EUSEBIUS - 47 total, get more
    print("Checking more Eusebius works (47 available, getting 10 more)...")
    eusebius_works = get_available_works('tlg2042', max_works=15)
    # Skip ones we already tried
    tried = ['tlg001', 'tlg005', 'tlg006', 'tlg007', 'tlg008']
    for work_code in eusebius_works:
        if work_code not in tried:
            works.append({
                'name': f'Eusebius, {work_code}',
                'tlg_code': 'tlg2042',
                'work_code': work_code,
                'edition': '1st1K-grc1',
                'author': 'Eusebius',
                'work_title': f'Work {work_code}',
                'citations': 2
            })

    # More ARISTOTLE - 41 total, get more
    print("Checking more Aristotle works (41 available, getting 10 more)...")
    aristotle_works = get_available_works('tlg0086', max_works=20)
    # Skip ones we already got
    tried_arist = ['tlg001', 'tlg002', 'tlg003', 'tlg004', 'tlg005', 'tlg006',
                   'tlg007', 'tlg008', 'tlg011', 'tlg012']
    for work_code in aristotle_works:
        if work_code not in tried_arist:
            works.append({
                'name': f'Aristotle, {work_code}',
                'tlg_code': 'tlg0086',
                'work_code': work_code,
                'edition': '1st1K-grc1',
                'author': 'Aristotle',
                'work_title': f'Work {work_code}',
                'citations': 2
            })

    # Try PROCLUS again with different approach
    print("Checking Proclus work...")
    proclus_works = get_available_works('tlg4036', max_works=1)
    for work_code in proclus_works:
        works.append({
            'name': f'Proclus, {work_code}',
            'tlg_code': 'tlg4036',
            'work_code': work_code,
            'edition': '1st1K-grc1',
            'author': 'Proclus',
            'work_title': f'Work {work_code}',
            'citations': 15
        })

    print(f"\n✓ Found {len(works)} works to retrieve")

    results = []
    total_citations = 0
    successful_citations = 0
    total_passages = 0

    for i, work_info in enumerate(works, 1):
        print(f"\n[{i}/{len(works)}] {work_info['name']}...")

        try:
            result = retriever.retrieve_work(work_info)

            if result:
                results.append({
                    'name': work_info['name'],
                    'citations': work_info['citations'],
                    'passages': len(result['passages']),
                    'success': True
                })

                total_citations += work_info['citations']
                successful_citations += work_info['citations']
                total_passages += len(result['passages'])
            else:
                results.append({
                    'name': work_info['name'],
                    'citations': work_info['citations'],
                    'success': False,
                    'error': 'Retrieval failed'
                })
                total_citations += work_info['citations']

        except Exception as e:
            print(f"✗ ERROR: {e}")
            results.append({
                'name': work_info['name'],
                'citations': work_info['citations'],
                'success': False,
                'error': str(e)[:60]
            })
            total_citations += work_info['citations']

        time.sleep(0.3)

    # Final summary
    print("\n" + "="*80)
    print("REMAINING RETRIEVAL COMPLETE")
    print("="*80)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    print(f"\n✓ Successfully retrieved: {len(successful)}/{len(works)} works")
    print(f"✓ Citations retrieved: {successful_citations}/{total_citations}")
    print(f"✓ Total passages extracted: {total_passages}")

    if successful:
        print(f"\n✅ Successful: {len(successful)} works")
        by_author = {}
        for r in successful:
            author = r['name'].split(',')[0]
            if author not in by_author:
                by_author[author] = []
            by_author[author].append(r)

        for author in sorted(by_author.keys()):
            works_list = by_author[author]
            total_cit = sum(w['citations'] for w in works_list)
            total_pass = sum(w['passages'] for w in works_list)
            print(f"  {author}: {len(works_list)} works, {total_cit} citations, {total_pass} passages")

    # Cumulative progress
    print("\n" + "="*80)
    print("CUMULATIVE PROGRESS")
    print("="*80)

    previous = 615
    new_total = previous + successful_citations

    print(f"Previous: {previous} citations")
    print(f"New: {successful_citations} citations")
    print(f"TOTAL: {new_total} / 2494 citations ({new_total/2494*100:.1f}%)")


if __name__ == '__main__':
    main()
