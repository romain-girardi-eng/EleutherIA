#!/usr/bin/env python3
"""
Batch First1KGreek Text Retrieval
==================================
Retrieves Sextus, Proclus, Origen, Gregory, and other works from First1KGreek.

NO HALLUCINATION - Direct TEI-XML parsing from verified sources.
"""

import sys
import time
from retrieve_first1k_tei import First1KGreekRetriever
import json

def main():
    """Batch retrieve First1KGreek works"""

    retriever = First1KGreekRetriever()

    print("="*80)
    print("FIRST1KGREEK BATCH RETRIEVAL")
    print("="*80)
    print("\nRetrieving Sextus, Proclus, Origen, Gregory...")

    # Works to retrieve based on exploration
    works = [
        # Sextus Empiricus - both major works
        {
            'name': 'Sextus Empiricus, Adversus Mathematicos',
            'tlg_code': 'tlg0544',
            'work_code': 'tlg002',
            'edition': '1st1K-grc1',
            'author': 'Sextus Empiricus',
            'work_title': 'Adversus Mathematicos',
            'citations': 16
        },

        # Proclus
        {
            'name': 'Proclus, Work tlg001',
            'tlg_code': 'tlg4036',
            'work_code': 'tlg001',
            'edition': '1st1K-grc1',
            'author': 'Proclus',
            'work_title': 'Work tlg001',
            'citations': 15
        },

        # Origen - try multiple works
        {
            'name': 'Origen, Work tlg001',
            'tlg_code': 'tlg2018',
            'work_code': 'tlg001',
            'edition': '1st1K-grc1',
            'author': 'Origen',
            'work_title': 'Work tlg001',
            'citations': 10
        },
        {
            'name': 'Origen, Work tlg002',
            'tlg_code': 'tlg2018',
            'work_code': 'tlg002',
            'edition': '1st1K-grc1',
            'author': 'Origen',
            'work_title': 'Work tlg002',
            'citations': 10
        },
        {
            'name': 'Origen, Work tlg003',
            'tlg_code': 'tlg2018',
            'work_code': 'tlg003',
            'edition': '1st1K-grc1',
            'author': 'Origen',
            'work_title': 'Work tlg003',
            'citations': 10
        },
        {
            'name': 'Origen, Work tlg005',
            'tlg_code': 'tlg2018',
            'work_code': 'tlg005',
            'edition': '1st1K-grc1',
            'author': 'Origen',
            'work_title': 'Work tlg005',
            'citations': 5
        },
        {
            'name': 'Origen, Work tlg007',
            'tlg_code': 'tlg2018',
            'work_code': 'tlg007',
            'edition': '1st1K-grc1',
            'author': 'Origen',
            'work_title': 'Work tlg007',
            'citations': 5
        },

        # Gregory of Nyssa
        {
            'name': 'Gregory of Nyssa, Work tlg001',
            'tlg_code': 'tlg2022',
            'work_code': 'tlg001',
            'edition': '1st1K-grc1',
            'author': 'Gregory of Nyssa',
            'work_title': 'Work tlg001',
            'citations': 10
        },
    ]

    results = []
    total_citations = 0
    successful_citations = 0
    total_passages = 0

    for work_info in works:
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
                print(f"✗ Failed to retrieve {work_info['name']}")
                results.append({
                    'name': work_info['name'],
                    'citations': work_info['citations'],
                    'success': False,
                    'error': 'Retrieval failed'
                })
                total_citations += work_info['citations']

        except Exception as e:
            print(f"\n✗ ERROR retrieving {work_info['name']}: {e}")
            results.append({
                'name': work_info['name'],
                'citations': work_info['citations'],
                'success': False,
                'error': str(e)
            })
            total_citations += work_info['citations']

        time.sleep(0.5)

    # Final summary
    print("\n" + "="*80)
    print("BATCH RETRIEVAL COMPLETE")
    print("="*80)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    print(f"\n✓ Successfully retrieved: {len(successful)}/{len(works)} works")
    print(f"✓ Citations retrieved: {successful_citations}/{total_citations}")
    print(f"✓ Total passages extracted: {total_passages}")

    if successful:
        print("\n✅ Successful retrievals:")
        for r in successful:
            print(f"  ✓ {r['name']:60s} {r['citations']:3d} citations, {r['passages']:4d} passages")

    if failed:
        print("\n❌ Failed retrievals:")
        for r in failed:
            print(f"  ✗ {r['name']:60s} {r.get('error', 'Unknown error')[:40]}")

    # Calculate cumulative progress
    print("\n" + "="*80)
    print("CUMULATIVE PROGRESS")
    print("="*80)

    previous = 479  # After Sextus Pyrrhoniae Hypotyposes
    new_total = previous + successful_citations

    print(f"Previous retrievals: {previous} citations")
    print(f"New retrievals: {successful_citations} citations")
    print(f"TOTAL: {new_total} / 2494 citations ({new_total/2494*100:.1f}%)")

    print("\n✓ All retrieved texts saved to: retrieved_texts/first1k_tei/")


if __name__ == '__main__':
    main()
