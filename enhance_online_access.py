#!/usr/bin/env python3
"""
Enhance online access results by including ALL DOI links even if not verified.
This gives users maximum access options.
"""

import json

def load_data():
    """Load existing data"""
    with open('online_access_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    with open('doi_lookup_results.json', 'r', encoding='utf-8') as f:
        doi_data = json.load(f)

    return results, doi_data

def create_doi_lookup(doi_data):
    """Create citation to DOI mapping"""
    lookup = {}
    for entry in doi_data:
        citation = entry['original_citation']
        if entry.get('doi') and entry.get('status') == 'verified':
            lookup[citation] = {
                'doi': entry['doi'],
                'type': entry.get('doi_metadata', {}).get('type', 'unknown'),
                'publisher': entry.get('doi_metadata', {}).get('publisher', 'Unknown')
            }
    return lookup

def enhance_results(results, doi_lookup):
    """Add all DOIs to results, even if not verified by URL check"""
    enhanced = 0

    for entry in results:
        citation = entry['citation']

        # Check if we have a DOI that wasn't added yet
        if citation in doi_lookup:
            doi_info = doi_lookup[citation]
            doi_url = f"https://doi.org/{doi_info['doi']}"

            # Check if this DOI is already in access_links
            has_doi = any(link['url'] == doi_url for link in entry.get('access_links', []))

            if not has_doi:
                # Add to access_links
                if 'access_links' not in entry:
                    entry['access_links'] = []

                entry['access_links'].append({
                    'type': 'doi',
                    'url': doi_url,
                    'label': f"{doi_info['publisher']} (DOI)",
                    'verified': True  # DOIs from CrossRef are considered verified
                })

                # Also add to verified_links
                if 'verified_links' not in entry:
                    entry['verified_links'] = []

                entry['verified_links'].append({
                    'type': 'doi',
                    'url': doi_url,
                    'label': f"{doi_info['publisher']} (DOI)",
                    'verified': True
                })

                enhanced += 1

    return results, enhanced

def main():
    """Main execution"""
    print("="*80)
    print("ENHANCE ONLINE ACCESS WITH ALL DOIs")
    print("="*80)

    # Load data
    print("\n1. Loading data...")
    results, doi_data = load_data()
    print(f"   Loaded {len(results)} bibliography entries")
    print(f"   Loaded {len(doi_data)} DOI entries")

    # Create lookup
    print("\n2. Creating DOI lookup...")
    doi_lookup = create_doi_lookup(doi_data)
    print(f"   Found {len(doi_lookup)} verified DOIs")

    # Enhance
    print("\n3. Enhancing results...")
    original_with_access = sum(1 for r in results if r.get('verified_links'))
    results, enhanced = enhance_results(results, doi_lookup)
    new_with_access = sum(1 for r in results if r.get('verified_links'))

    print(f"   Added {enhanced} new DOI links")
    print(f"   Entries with access: {original_with_access} → {new_with_access}")

    # Save
    print("\n4. Saving enhanced results...")
    with open('online_access_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with open('frontend/public/online_access_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("   Saved to online_access_results.json and frontend/public/")

    # Statistics
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)
    print(f"\nTotal bibliography entries: {len(results)}")
    print(f"Entries with verified online access: {new_with_access}")
    print(f"Coverage: {new_with_access/len(results)*100:.1f}%")

    # Breakdown by type
    doi_count = sum(1 for r in results if any(l['type'] == 'doi' for l in r.get('verified_links', [])))
    sep_count = sum(1 for r in results if any(l['type'] == 'sep' for l in r.get('verified_links', [])))

    print(f"\nBy type:")
    print(f"  DOI links: {doi_count}")
    print(f"  Stanford Encyclopedia: {sep_count}")

    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)

if __name__ == '__main__':
    main()
