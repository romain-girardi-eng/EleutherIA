#!/usr/bin/env python3
"""
Batch GitHub TEI-XML Retrieval
===============================
Retrieves multiple high-priority works from Perseus GitHub repositories.

NO HALLUCINATION - Direct TEI-XML parsing from verified sources.
"""

import sys
import time
from retrieve_github_tei import GitHubTEIRetriever

def main():
    """Batch retrieve priority works"""

    retriever = GitHubTEIRetriever()

    print("="*80)
    print("BATCH GITHUB TEI-XML RETRIEVAL")
    print("="*80)
    print("\nRetrieving high-priority works from Perseus GitHub...")

    # High-priority works with known structures
    works = [
        # Already done: Aristotle NE

        {
            'name': 'Alexander of Aphrodisias, De Fato',
            'language': 'greek',
            'tlg_code': 'tlg0085',
            'work_code': 'tlg014',
            'edition': 'perseus-grc2',
            'author': 'Alexander of Aphrodisias',
            'work_title': 'De Fato',
            'citations': 65
        },
        {
            'name': 'Epictetus, Discourses',
            'language': 'greek',
            'tlg_code': 'tlg0557',
            'work_code': 'tlg001',
            'edition': 'perseus-grc2',
            'author': 'Epictetus',
            'work_title': 'Discourses',
            'citations': 44
        },
        {
            'name': 'Plotinus, Enneads',
            'language': 'greek',
            'tlg_code': 'tlg0062',
            'work_code': 'tlg001',
            'edition': 'perseus-grc2',
            'author': 'Plotinus',
            'work_title': 'Enneads',
            'citations': 31
        },
        {
            'name': 'Aulus Gellius, Noctes Atticae',
            'language': 'latin',
            'tlg_code': 'phi1254',
            'work_code': 'phi001',
            'edition': 'perseus-lat2',
            'author': 'Aulus Gellius',
            'work_title': 'Noctes Atticae',
            'citations': 34
        },
    ]

    results = []
    total_citations = 0

    for work_info in works:
        print(f"\n{'='*80}")
        print(f"RETRIEVING: {work_info['name']}")
        print(f"Database citations: {work_info['citations']}")
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
                continue

            # Extract passages
            print("\nExtracting passages...")
            passages = retriever.extract_all_books(root)

            print(f"✓ Extracted {len(passages)} passages")

            # Show samples
            print("\nSample passages:")
            for key in list(passages.keys())[:5]:
                text_preview = passages[key]['text'][:100] if passages[key].get('text') else "NO TEXT"
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

            import json
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

        except Exception as e:
            print(f"\n✗ ERROR retrieving {work_info['name']}: {e}")
            results.append({
                'name': work_info['name'],
                'citations': work_info['citations'],
                'success': False,
                'error': str(e)
            })

        time.sleep(1)  # Be polite to GitHub

    # Final summary
    print("\n" + "="*80)
    print("BATCH RETRIEVAL COMPLETE")
    print("="*80)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    print(f"\n✓ Successfully retrieved: {len(successful)}/{len(works)} works")
    print(f"✓ Total citations covered: {total_citations}")
    print(f"✓ Total passages extracted: {sum(r.get('passages', 0) for r in successful)}")

    if successful:
        print("\nSuccessful retrievals:")
        for r in successful:
            print(f"  ✓ {r['name']:50s} {r['citations']:3d} citations, {r['passages']:3d} passages")

    if failed:
        print("\nFailed retrievals:")
        for r in failed:
            print(f"  ✗ {r['name']:50s} {r.get('error', 'Unknown error')}")

    print("\n✓ All retrieved texts saved to: retrieved_texts/github_tei/")


if __name__ == '__main__':
    main()
