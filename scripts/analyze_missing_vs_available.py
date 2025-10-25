#!/usr/bin/env python3
"""
Analyze Missing Texts vs. Available TLG Codes
==============================================
Cross-reference what we NEED (from critical_citation_gaps.csv)
with what's AVAILABLE (in First1KGreek TLG codes).

This implements the user's reversed approach:
Look at what we're MISSING, then search for it in OGL.
"""

import csv
import requests
from collections import defaultdict

# Read available TLG codes from First1KGreek
def get_first1k_authors():
    """Get ALL TLG codes available in First1KGreek"""
    url = "https://api.github.com/repos/OpenGreekAndLatin/First1KGreek/contents/data"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return [item['name'] for item in resp.json() if item['type'] == 'dir']
    except:
        pass
    return []

# TLG code mappings for authors we need
TLG_MAPPINGS = {
    'Aristotle': 'tlg0086',
    'Plato': 'tlg0059',
    'Plotinus': 'tlg0062',  # Actually Lucian is 0062, Plotinus is different
    'Epictetus': 'tlg0557',
    'Sextus Empiricus': 'tlg0544',
    'Origen': 'tlg2018',
    'Alexander of Aphrodisias': 'tlg0732',
    'Aulus Gellius': 'tlg1254',
    'Augustine': 'augustine',  # Latin, in OGL CSEL
    'Cicero': 'cicero',  # Latin
    'Lucretius': 'lucretius',  # Latin
    'Philo': 'tlg0018',
    'Athanasius': 'tlg2035',
    'Gregory of Nyssa': 'tlg2022',
    'Eusebius': 'tlg2042',
    'Nemesius': 'tlg2050',
    'Plutarch': 'tlg0007',
    'Clement': 'tlg0555',
    'Irenaeus': 'tlg1447',
    'Justin Martyr': 'tlg0645',
    'Cyril of Alexandria': 'tlg4090',
    'Theodoret': 'tlg4089',
    'Epiphanius': 'tlg2021',
    'Simplicius': 'tlg4013',
    'Porphyry': 'tlg2034',
    'Iamblichus': 'tlg2462',
    'Proclus': 'tlg4036',
    'Galen': 'tlg0057',
    'Hippocrates': 'tlg0627',
    'Strabo': 'tlg0099',
    'Diogenes Laertius': 'tlg0004',
    'Themistius': 'tlg2001',
    'Basil of Caesarea': 'tlg2040',
    'John Chrysostom': 'tlg2062',
    'Maximus of Tyre': 'tlg0583',
    'Dio Chrysostom': 'tlg0612',
    'Lucian': 'tlg0062',
    'Marcus Aurelius': 'tlg0566',
}

def main():
    print("="*80)
    print("MISSING TEXTS vs. AVAILABLE TLG CODES ANALYSIS")
    print("="*80)

    # Get available TLG codes from First1KGreek
    print("\nFetching available TLG codes from First1KGreek...")
    available_codes = set(get_first1k_authors())
    print(f"✓ Found {len(available_codes)} TLG codes in First1KGreek")

    # Read critical gaps
    print("\nAnalyzing critical_citation_gaps.csv...")
    needs = []
    with open('critical_citation_gaps.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Status'] == 'NEED':
                needs.append(row)

    print(f"✓ Found {len(needs)} categories of missing texts")

    # Match needs to available TLG codes
    print("\n" + "="*80)
    print("MATCHING ANALYSIS")
    print("="*80)

    matches = []
    no_matches = []

    for need in needs:
        work = need['Work']
        citations = int(need['Citation_Count'])

        # Try to extract author from work field
        matched_tlg = None
        for author, tlg_code in TLG_MAPPINGS.items():
            if author in work or author.lower() in work.lower():
                if tlg_code in available_codes:
                    matched_tlg = tlg_code
                    matches.append({
                        'work': work,
                        'citations': citations,
                        'author': author,
                        'tlg_code': tlg_code
                    })
                    break

        if not matched_tlg:
            no_matches.append({
                'work': work,
                'citations': citations
            })

    # Print matches
    print(f"\n✅ AVAILABLE in First1KGreek ({len(matches)} categories):")
    print("-" * 80)
    matches_sorted = sorted(matches, key=lambda x: x['citations'], reverse=True)
    for m in matches_sorted:
        print(f"  {m['work'][:50]:50s} | {m['citations']:4d} cit | {m['tlg_code']}")

    # Print no matches
    print(f"\n❌ NOT AVAILABLE in First1KGreek ({len(no_matches)} categories):")
    print("-" * 80)
    no_matches_sorted = sorted(no_matches, key=lambda x: x['citations'], reverse=True)
    for m in no_matches_sorted[:20]:  # Top 20 only
        print(f"  {m['work'][:60]:60s} | {m['citations']:4d} cit")

    # Summary
    total_available_cit = sum(m['citations'] for m in matches)
    total_unavailable_cit = sum(m['citations'] for m in no_matches)
    total_cit = total_available_cit + total_unavailable_cit

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total missing citations: {total_cit}")
    print(f"  Available in First1KGreek: {total_available_cit} ({total_available_cit/total_cit*100:.1f}%)")
    print(f"  NOT in First1KGreek: {total_unavailable_cit} ({total_unavailable_cit/total_cit*100:.1f}%)")

    # What we should retrieve
    print("\n" + "="*80)
    print("RECOMMENDATION: RETRIEVE THESE FROM FIRST1KGREEK")
    print("="*80)
    print("\nHigh-priority authors still available:")
    for m in matches_sorted[:10]:
        print(f"  - {m['author']:25s} (tlg{m['tlg_code'][3:]}) - {m['citations']} citations")

if __name__ == '__main__':
    main()
