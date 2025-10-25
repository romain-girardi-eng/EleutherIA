#!/usr/bin/env python3
"""
Complete Classical Works Retrieval
===================================
Retrieves all available classical works from Perseus GitHub repositories.

NO HALLUCINATION - Direct TEI-XML parsing from verified sources.
"""

import sys
import time
from retrieve_github_tei import GitHubTEIRetriever
import json

def main():
    """Batch retrieve all available classical works"""

    retriever = GitHubTEIRetriever()

    print("="*80)
    print("COMPLETE CLASSICAL WORKS RETRIEVAL")
    print("="*80)
    print("\nRetrieving all available works from Perseus GitHub...")

    # Extended list of classical works to retrieve
    works = [
        # Already done: Aristotle NE, Epictetus, Plotinus, Gellius, Cicero De Fato, Lucretius

        # More Aristotle
        {
            'name': 'Aristotle, De Interpretatione',
            'language': 'greek',
            'tlg_code': 'tlg0086',
            'work_code': 'tlg013',
            'edition': 'perseus-grc2',
            'author': 'Aristotle',
            'work_title': 'De Interpretatione',
            'citations': 14
        },
        {
            'name': 'Aristotle, De Anima',
            'language': 'greek',
            'tlg_code': 'tlg0086',
            'work_code': 'tlg012',
            'edition': 'perseus-grc2',
            'author': 'Aristotle',
            'work_title': 'De Anima',
            'citations': 6
        },
        {
            'name': 'Aristotle, Eudemian Ethics',
            'language': 'greek',
            'tlg_code': 'tlg0086',
            'work_code': 'tlg011',
            'edition': 'perseus-grc2',
            'author': 'Aristotle',
            'work_title': 'Eudemian Ethics',
            'citations': 15
        },

        # Plutarch
        {
            'name': 'Plutarch, De Stoicorum Repugnantiis',
            'language': 'greek',
            'tlg_code': 'tlg0007',
            'work_code': 'tlg096',
            'edition': 'perseus-grc2',
            'author': 'Plutarch',
            'work_title': 'De Stoicorum Repugnantiis',
            'citations': 16
        },

        # More Cicero
        {
            'name': 'Cicero, Academica',
            'language': 'latin',
            'tlg_code': 'phi0474',
            'work_code': 'phi006',
            'edition': 'perseus-lat2',
            'author': 'Cicero',
            'work_title': 'Academica',
            'citations': 13
        },
        {
            'name': 'Cicero, De Natura Deorum',
            'language': 'latin',
            'tlg_code': 'phi0474',
            'work_code': 'phi038',
            'edition': 'perseus-lat2',
            'author': 'Cicero',
            'work_title': 'De Natura Deorum',
            'citations': 8
        },
        {
            'name': 'Cicero, De Divinatione',
            'language': 'latin',
            'tlg_code': 'phi0474',
            'work_code': 'phi024',
            'edition': 'perseus-lat2',
            'author': 'Cicero',
            'work_title': 'De Divinatione',
            'citations': 8
        },

        # Boethius
        {
            'name': 'Boethius, Consolation of Philosophy',
            'language': 'latin',
            'tlg_code': 'phi0824',
            'work_code': 'phi001',
            'edition': 'perseus-lat2',
            'author': 'Boethius',
            'work_title': 'Consolation of Philosophy',
            'citations': 14
        },

        # Sextus Empiricus
        {
            'name': 'Sextus Empiricus, Adversus Mathematicos',
            'language': 'greek',
            'tlg_code': 'tlg0544',
            'work_code': 'tlg004',
            'edition': 'perseus-grc2',
            'author': 'Sextus Empiricus',
            'work_title': 'Adversus Mathematicos',
            'citations': 5
        },

        # Diogenes Laertius
        {
            'name': 'Diogenes Laertius, Lives of Eminent Philosophers',
            'language': 'greek',
            'tlg_code': 'tlg0004',
            'work_code': 'tlg001',
            'edition': 'perseus-grc2',
            'author': 'Diogenes Laertius',
            'work_title': 'Lives of Eminent Philosophers',
            'citations': 5
        },
    ]

    results = []
    total_citations = 0
    successful_citations = 0

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
                text_preview = passages[key]['text'][:80] if passages[key].get('text') else "NO TEXT"
                print(f"  {key}: {text_preview}...")

            # Build metadata
            work_data = {
                'metadata': {
                    'work': work_info['work_title'],
                    'author': work_info['author'],
                    'language': 'Greek' if work_info['language'] == 'greek' else 'Latin',
                    'source': f"Perseus canonical-{work_info['language']}Lit GitHub",
                    'source_url': 'https://github.com/PerseusDL/canonical-greekLit' if work_info['language'] == 'greek' else 'https://github.com/PerseusDL/canonical-latinLit',
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
                'file': str(output_file),
                'success': True
            })

            total_citations += work_info['citations']
            successful_citations += work_info['citations']

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
    print(f"✓ Total passages extracted: {sum(r.get('passages', 0) for r in successful)}")

    if successful:
        print("\n✅ Successful retrievals:")
        for r in successful:
            print(f"  ✓ {r['name']:55s} {r['citations']:3d} citations, {r['passages']:4d} passages")

    if failed:
        print("\n❌ Failed retrievals:")
        for r in failed:
            print(f"  ✗ {r['name']:55s} {r.get('error', 'Unknown error')[:40]}")

    # Calculate cumulative progress
    print("\n" + "="*80)
    print("CUMULATIVE PROGRESS")
    print("="*80)

    # Previous retrievals
    previous = 268  # From session so far
    new_total = previous + successful_citations

    print(f"Previous retrievals: {previous} citations")
    print(f"New retrievals: {successful_citations} citations")
    print(f"TOTAL: {new_total} / 2494 citations ({new_total/2494*100:.1f}%)")

    print("\n✓ All retrieved texts saved to: retrieved_texts/github_tei/")


if __name__ == '__main__':
    main()
