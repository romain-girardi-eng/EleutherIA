#!/usr/bin/env python3
"""
Find online access links for bibliography entries.
This script searches for freely accessible versions of scholarly works via:
- DOI links (from existing doi_lookup_results.json)
- Google Scholar
- Archive.org
- Publisher websites
- Open access repositories
"""

import json
import time
import re
import requests
from urllib.parse import quote_plus, urljoin
from typing import Dict, List, Optional, Tuple

def load_existing_doi_data():
    """Load existing DOI lookup results"""
    try:
        with open('doi_lookup_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_database():
    """Load the main database"""
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_bibliography():
    """Extract all modern scholarship references from database"""
    db = load_database()
    bib_set = set()

    for node in db['nodes']:
        if 'modern_scholarship' in node and isinstance(node['modern_scholarship'], list):
            for ref in node['modern_scholarship']:
                if ref and ref.strip():
                    bib_set.add(ref.strip())

    return sorted(list(bib_set))

def check_url_accessible(url: str, timeout: int = 10) -> Tuple[bool, int]:
    """Check if a URL is accessible"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(url, timeout=timeout, headers=headers, allow_redirects=True)
        return response.status_code == 200, response.status_code
    except Exception as e:
        print(f"   Error checking {url}: {str(e)[:100]}")
        return False, 0

def get_doi_url(citation: str, doi_data: List[Dict]) -> Optional[str]:
    """Get DOI URL from existing DOI data"""
    for entry in doi_data:
        if entry['original_citation'] == citation and entry.get('doi'):
            doi = entry['doi']
            return f"https://doi.org/{doi}"
    return None

def search_google_scholar(citation: str) -> Optional[str]:
    """
    Generate Google Scholar search URL.
    Note: We can't scrape Google Scholar directly, but we can provide a search URL.
    """
    # Clean citation for search
    search_query = re.sub(r'\[.*?\]', '', citation)  # Remove bracketed notes
    search_query = re.sub(r'\(.*?\)', '', search_query)  # Remove parentheses
    search_query = ' '.join(search_query.split()[:10])  # First 10 words

    encoded = quote_plus(search_query)
    return f"https://scholar.google.com/scholar?q={encoded}"

def search_archive_org(citation: str) -> Optional[str]:
    """Search archive.org for the work"""
    # Extract title and author
    parts = citation.split('.')
    if len(parts) >= 2:
        search_query = parts[0] + ' ' + parts[1]
        search_query = re.sub(r'\(.*?\)', '', search_query)
        search_query = ' '.join(search_query.split()[:8])

        encoded = quote_plus(search_query)
        return f"https://archive.org/search?query={encoded}"
    return None

def extract_year(citation: str) -> Optional[int]:
    """Extract publication year from citation"""
    match = re.search(r'\b(19\d{2}|20\d{2})\b', citation)
    return int(match.group(0)) if match else None

def categorize_publication(citation: str) -> str:
    """Categorize the type of publication"""
    citation_lower = citation.lower()

    if 'stanford encyclopedia' in citation_lower or 'sep' in citation_lower:
        return 'sep'
    elif 'journal' in citation_lower or re.search(r'\d+\(\d+\)', citation):
        return 'journal'
    elif 'trans.' in citation or 'translation' in citation_lower:
        return 'translation'
    elif 'ed.' in citation or 'eds.' in citation or 'edited' in citation_lower:
        return 'edited_volume'
    else:
        return 'monograph'

def get_sep_url(citation: str) -> Optional[str]:
    """Get Stanford Encyclopedia of Philosophy URL"""
    # Extract topic from citation
    match = re.search(r"'([^']+)'", citation)
    if match:
        topic = match.group(1).lower()
        topic = topic.replace(' ', '-').replace('.', '')
        return f"https://plato.stanford.edu/entries/{topic}/"
    return None

def find_online_access(citation: str, doi_data: List[Dict]) -> Dict:
    """Find all possible online access points for a citation"""

    result = {
        'citation': citation,
        'type': categorize_publication(citation),
        'year': extract_year(citation),
        'access_links': [],
        'verified_links': [],
        'search_links': []
    }

    # 1. Check for DOI
    doi_url = get_doi_url(citation, doi_data)
    if doi_url:
        result['access_links'].append({
            'type': 'doi',
            'url': doi_url,
            'label': 'Publisher (DOI)',
            'verified': False  # Will verify below
        })

    # 2. Stanford Encyclopedia of Philosophy
    if result['type'] == 'sep':
        sep_url = get_sep_url(citation)
        if sep_url:
            result['access_links'].append({
                'type': 'sep',
                'url': sep_url,
                'label': 'Stanford Encyclopedia',
                'verified': False
            })

    # 3. Google Scholar search
    scholar_url = search_google_scholar(citation)
    if scholar_url:
        result['search_links'].append({
            'type': 'google_scholar',
            'url': scholar_url,
            'label': 'Search Google Scholar'
        })

    # 4. Archive.org search
    archive_url = search_archive_org(citation)
    if archive_url:
        result['search_links'].append({
            'type': 'archive_org',
            'url': archive_url,
            'label': 'Search Archive.org'
        })

    return result

def verify_links(result: Dict, verify_all: bool = False) -> Dict:
    """Verify that links are accessible"""

    if not verify_all:
        # Only verify DOI and SEP links (not search links)
        for link in result['access_links']:
            if link['type'] in ['doi', 'sep']:
                print(f"   Verifying {link['type']}: {link['url']}")
                accessible, status_code = check_url_accessible(link['url'])
                link['verified'] = accessible
                link['status_code'] = status_code

                if accessible:
                    result['verified_links'].append(link)
                    print(f"   ✓ Verified ({status_code})")
                else:
                    print(f"   ✗ Not accessible ({status_code})")

                time.sleep(1)  # Rate limiting

    return result

def main():
    """Main execution"""
    print("="*80)
    print("ONLINE ACCESS FINDER FOR BIBLIOGRAPHY")
    print("="*80)

    # Load data
    print("\n1. Loading data...")
    doi_data = load_existing_doi_data()
    bibliography = extract_bibliography()

    print(f"   Loaded {len(doi_data)} DOI entries")
    print(f"   Found {len(bibliography)} unique bibliography entries")

    # Process each citation
    print("\n2. Finding online access links...")
    results = []

    for i, citation in enumerate(bibliography, 1):
        print(f"\n[{i}/{len(bibliography)}] Processing: {citation[:80]}...")

        result = find_online_access(citation, doi_data)
        result = verify_links(result, verify_all=False)
        results.append(result)

        # Show summary
        access_count = len(result['access_links'])
        verified_count = len(result['verified_links'])
        search_count = len(result['search_links'])

        print(f"   → {access_count} direct access links, {verified_count} verified, {search_count} search links")

        # Rate limiting
        if i % 10 == 0:
            time.sleep(2)

    # Save results
    print("\n3. Saving results...")
    with open('online_access_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"   Saved to online_access_results.json")

    # Statistics
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)

    total_with_access = sum(1 for r in results if r['access_links'])
    total_with_verified = sum(1 for r in results if r['verified_links'])
    total_with_doi = sum(1 for r in results if any(l['type'] == 'doi' for l in r['access_links']))
    total_sep = sum(1 for r in results if r['type'] == 'sep')

    print(f"\nTotal entries: {len(results)}")
    print(f"With direct access links: {total_with_access} ({total_with_access/len(results)*100:.1f}%)")
    print(f"With verified links: {total_with_verified} ({total_with_verified/len(results)*100:.1f}%)")
    print(f"With DOI: {total_with_doi} ({total_with_doi/len(results)*100:.1f}%)")
    print(f"Stanford Encyclopedia: {total_sep}")

    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)

if __name__ == '__main__':
    main()
