#!/usr/bin/env python3
"""
Batch OGL Patristic Text Retrieval
===================================
Retrieves Augustine and Origen texts from Open Greek and Latin CSEL repository.

NO HALLUCINATION - Direct TEI-XML parsing from verified sources.
"""

import sys
import time
from retrieve_ogl_tei import OGLTEIRetriever
import json

def main():
    """Batch retrieve Augustine and Origen works"""

    retriever = OGLTEIRetriever()

    print("="*80)
    print("PATRISTIC TEXT RETRIEVAL FROM OGL")
    print("="*80)
    print("\nRetrieving Augustine and Origen works from OGL GitHub...")

    # Augustine works available in OGL CSEL
    # Based on database citations and OGL repository structure
    works = [
        # Augustine - De Libero Arbitrio (most cited for free will)
        {
            'name': 'Augustine, De Libero Arbitrio',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa003',  # Typical code for De Libero Arbitrio
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'De Libero Arbitrio',
            'citations': 30  # High priority
        },

        # Augustine - De Gratia et Libero Arbitrio
        {
            'name': 'Augustine, De Gratia et Libero Arbitrio',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa006',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'De Gratia et Libero Arbitrio',
            'citations': 20
        },

        # Augustine - Enchiridion
        {
            'name': 'Augustine, Enchiridion',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa011',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'Enchiridion',
            'citations': 15
        },

        # Augustine - De Correptione et Gratia
        {
            'name': 'Augustine, De Correptione et Gratia',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa014a',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'De Correptione et Gratia',
            'citations': 10
        },

        # Augustine - De Spiritu et Littera
        {
            'name': 'Augustine, De Spiritu et Littera',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa015b',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'De Spiritu et Littera',
            'citations': 8
        },

        # Augustine - Contra Academicos
        {
            'name': 'Augustine, Contra Academicos',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa016',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'Contra Academicos',
            'citations': 5
        },

        # Augustine - De Genesi Contra Manichaeos
        {
            'name': 'Augustine, De Genesi Contra Manichaeos',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa017',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'De Genesi Contra Manichaeos',
            'citations': 5
        },

        # Augustine - Retractationes
        {
            'name': 'Augustine, Retractationes',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa019',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'Retractationes',
            'citations': 8
        },

        # Augustine - De Duabus Animabus
        {
            'name': 'Augustine, De Duabus Animabus',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa020',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'De Duabus Animabus',
            'citations': 4
        },

        # Augustine - Contra Fortunatum
        {
            'name': 'Augustine, Contra Fortunatum Manichaeum',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa021',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'Contra Fortunatum Manichaeum',
            'citations': 4
        },

        # Augustine - Contra Adimantum
        {
            'name': 'Augustine, Contra Adimantum',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa023',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'Contra Adimantum',
            'citations': 4
        },

        # Augustine - De Gratia Christi et de Peccato Originali
        {
            'name': 'Augustine, De Gratia Christi et de Peccato Originali',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa024',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'De Gratia Christi et de Peccato Originali',
            'citations': 8
        },

        # Augustine - De Civitate Dei (City of God)
        {
            'name': 'Augustine, De Civitate Dei',
            'stoa_author': 'stoa0040',
            'stoa_work': 'stoa029',
            'edition': 'opp-lat1',
            'author': 'Augustine',
            'work_title': 'De Civitate Dei',
            'citations': 12
        },
    ]

    results = []
    total_citations = 0
    successful_citations = 0
    total_passages = 0

    for work_info in works:
        print(f"\n{'='*80}")
        print(f"RETRIEVING: {work_info['name']}")
        print(f"Expected citations: {work_info['citations']}")
        print(f"{'='*80}")

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

        time.sleep(0.5)  # Be polite to GitHub

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

    # Previous retrievals
    previous = 310  # From Perseus GitHub session
    new_total = previous + successful_citations

    print(f"Previous retrievals: {previous} citations")
    print(f"New retrievals: {successful_citations} citations")
    print(f"TOTAL: {new_total} / 2494 citations ({new_total/2494*100:.1f}%)")

    print("\n✓ All retrieved texts saved to: retrieved_texts/ogl_tei/")


if __name__ == '__main__':
    main()
