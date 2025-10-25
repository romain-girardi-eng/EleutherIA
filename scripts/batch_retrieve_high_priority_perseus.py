#!/usr/bin/env python3
"""
Batch High-Priority Perseus Text Retrieval
===========================================
Retrieves Plato, Sextus Empiricus, Proclus, and additional Aristotle works.

NO HALLUCINATION - Direct TEI-XML parsing from verified sources.
"""

import sys
import time
from retrieve_github_tei import GitHubTEIRetriever
import json

def main():
    """Batch retrieve high-priority Perseus works"""

    retriever = GitHubTEIRetriever()

    print("="*80)
    print("HIGH-PRIORITY PERSEUS TEXT RETRIEVAL")
    print("="*80)
    print("\nRetrieving Plato, Sextus, Proclus, and more Aristotle...")

    # High-priority works based on citation analysis
    works = [
        # Plato - Republic (most cited)
        {
            'name': 'Plato, Republic',
            'language': 'greek',
            'tlg_code': 'tlg0059',
            'work_code': 'tlg030',
            'edition': 'perseus-grc1',
            'author': 'Plato',
            'work_title': 'Republic',
            'citations': 12
        },

        # Plato - Laws
        {
            'name': 'Plato, Laws',
            'language': 'greek',
            'tlg_code': 'tlg0059',
            'work_code': 'tlg034',
            'edition': 'perseus-grc1',
            'author': 'Plato',
            'work_title': 'Laws',
            'citations': 8
        },

        # Plato - Timaeus
        {
            'name': 'Plato, Timaeus',
            'language': 'greek',
            'tlg_code': 'tlg0059',
            'work_code': 'tlg033',
            'edition': 'perseus-grc1',
            'author': 'Plato',
            'work_title': 'Timaeus',
            'citations': 6
        },

        # Plato - Phaedrus
        {
            'name': 'Plato, Phaedrus',
            'language': 'greek',
            'tlg_code': 'tlg0059',
            'work_code': 'tlg012',
            'edition': 'perseus-grc1',
            'author': 'Plato',
            'work_title': 'Phaedrus',
            'citations': 4
        },

        # Plato - Protagoras
        {
            'name': 'Plato, Protagoras',
            'language': 'greek',
            'tlg_code': 'tlg0059',
            'work_code': 'tlg004',
            'edition': 'perseus-grc1',
            'author': 'Plato',
            'work_title': 'Protagoras',
            'citations': 4
        },

        # Plato - Meno
        {
            'name': 'Plato, Meno',
            'language': 'greek',
            'tlg_code': 'tlg0059',
            'work_code': 'tlg006',
            'edition': 'perseus-grc1',
            'author': 'Plato',
            'work_title': 'Meno',
            'citations': 2
        },

        # Plato - Gorgias
        {
            'name': 'Plato, Gorgias',
            'language': 'greek',
            'tlg_code': 'tlg0059',
            'work_code': 'tlg009',
            'edition': 'perseus-grc1',
            'author': 'Plato',
            'work_title': 'Gorgias',
            'citations': 2
        },

        # Sextus Empiricus - Outlines of Pyrrhonism
        {
            'name': 'Sextus Empiricus, Pyrrhoniae Hypotyposes',
            'language': 'greek',
            'tlg_code': 'tlg0544',
            'work_code': 'tlg001',
            'edition': 'perseus-grc1',
            'author': 'Sextus Empiricus',
            'work_title': 'Pyrrhoniae Hypotyposes',
            'citations': 16
        },

        # Sextus Empiricus - Adversus Mathematicos
        {
            'name': 'Sextus Empiricus, Adversus Mathematicos',
            'language': 'greek',
            'tlg_code': 'tlg0544',
            'work_code': 'tlg004',
            'edition': 'perseus-grc2',
            'author': 'Sextus Empiricus',
            'work_title': 'Adversus Mathematicos',
            'citations': 16
        },

        # Aristotle - Metaphysics
        {
            'name': 'Aristotle, Metaphysics',
            'language': 'greek',
            'tlg_code': 'tlg0086',
            'work_code': 'tlg025',
            'edition': 'perseus-grc2',
            'author': 'Aristotle',
            'work_title': 'Metaphysics',
            'citations': 25
        },

        # Aristotle - Physics
        {
            'name': 'Aristotle, Physics',
            'language': 'greek',
            'tlg_code': 'tlg0086',
            'work_code': 'tlg031',
            'edition': 'perseus-grc1',
            'author': 'Aristotle',
            'work_title': 'Physics',
            'citations': 20
        },

        # Aristotle - Posterior Analytics
        {
            'name': 'Aristotle, Posterior Analytics',
            'language': 'greek',
            'tlg_code': 'tlg0086',
            'work_code': 'tlg009',
            'edition': 'perseus-grc2',
            'author': 'Aristotle',
            'work_title': 'Posterior Analytics',
            'citations': 10
        },

        # Aristotle - Categories
        {
            'name': 'Aristotle, Categories',
            'language': 'greek',
            'tlg_code': 'tlg0086',
            'work_code': 'tlg001',
            'edition': 'perseus-grc2',
            'author': 'Aristotle',
            'work_title': 'Categories',
            'citations': 8
        },

        # Proclus - Elements of Theology
        {
            'name': 'Proclus, Elements of Theology',
            'language': 'greek',
            'tlg_code': 'tlg4036',
            'work_code': 'tlg034',
            'edition': 'perseus-grc1',
            'author': 'Proclus',
            'work_title': 'Elements of Theology',
            'citations': 15
        },

        # Proclus - Commentary on Plato's Timaeus
        {
            'name': 'Proclus, In Platonis Timaeum Commentaria',
            'language': 'greek',
            'tlg_code': 'tlg4036',
            'work_code': 'tlg013',
            'edition': 'perseus-grc1',
            'author': 'Proclus',
            'work_title': 'In Platonis Timaeum Commentaria',
            'citations': 14
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
            # Download XML
            root = retriever.download_work_xml(
                language=work_info['language'],
                tlg_code=work_info['tlg_code'],
                work_code=work_info['work_code'],
                edition=work_info['edition']
            )

            if root is None:
                print(f"✗ Failed to download {work_info['name']}")
                results.append({
                    'name': work_info['name'],
                    'citations': work_info['citations'],
                    'success': False,
                    'error': 'Download failed (404)'
                })
                total_citations += work_info['citations']
                continue

            # Extract passages
            print("\nExtracting passages...")
            passages = retriever.extract_all_books(root)

            print(f"✓ Extracted {len(passages)} passages")

            # Show samples
            print("\nSample passages:")
            for key in list(passages.keys())[:3]:
                text_preview = passages[key].get('text', 'NO TEXT')[:80] if passages[key].get('text') else "NO TEXT"
                print(f"  {key}: {text_preview}...")

            # Build metadata
            work_data = {
                'metadata': {
                    'work': work_info['work_title'],
                    'author': work_info['author'],
                    'language': 'Greek' if work_info['language'] == 'greek' else 'Latin',
                    'source': 'Perseus canonical-greekLit GitHub',
                    'source_url': 'https://github.com/PerseusDL/canonical-greekLit',
                    'file_url': f"{retriever.GREEK_LIT_BASE if work_info['language'] == 'greek' else retriever.LATIN_LIT_BASE}/{work_info['tlg_code']}/{work_info['work_code']}/{work_info['tlg_code']}.{work_info['work_code']}.{work_info['edition']}.xml",
                    'edition': work_info['edition'],
                    'format': 'TEI-XML',
                    'urn': f"urn:cts:{'greekLit' if work_info['language'] == 'greek' else 'latinLit'}:{work_info['tlg_code']}.{work_info['work_code']}.{work_info['edition']}",
                    'retrieved_date': '2025-10-25',
                    'verification_status': 'github_source',
                    'passages_extracted': len(passages),
                    'database_citations': work_info['citations']
                },
                'passages': passages
            }

            # Save
            safe_name = work_info['name'].lower().replace(' ', '_').replace(',', '').replace('.', '')
            output_file = retriever.output_dir / f'{safe_name}.json'

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(work_data, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Saved to: {output_file}")

            results.append({
                'name': work_info['name'],
                'citations': work_info['citations'],
                'passages': len(passages),
                'success': True
            })

            total_citations += work_info['citations']
            successful_citations += work_info['citations']
            total_passages += len(passages)

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

    previous = 428  # From previous Perseus + OGL sessions
    new_total = previous + successful_citations

    print(f"Previous retrievals: {previous} citations")
    print(f"New retrievals: {successful_citations} citations")
    print(f"TOTAL: {new_total} / 2494 citations ({new_total/2494*100:.1f}%)")

    print("\n✓ All retrieved texts saved to: retrieved_texts/github_tei/")


if __name__ == '__main__':
    main()
