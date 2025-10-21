#!/usr/bin/env python3
"""
Analyze Greek/Latin terminology coverage in concept nodes
Identify which concepts need trilingual (Greek-Latin-English) completion
"""

import json
from collections import defaultdict

def analyze_terminology():
    """Analyze Greek/Latin terminology coverage"""

    # Load database
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']

    # Filter concept nodes only
    concepts = [n for n in nodes if n.get('type') == 'concept']

    print("=" * 80)
    print("GREEK/LATIN TERMINOLOGY ANALYSIS")
    print("=" * 80)
    print(f"\nTotal concept nodes: {len(concepts)}")

    # Categorize concepts
    has_greek = []
    has_latin = []
    has_both = []
    has_neither = []
    has_greek_only = []
    has_latin_only = []

    for concept in concepts:
        greek = concept.get('greek_term')
        latin = concept.get('latin_term')

        if greek:
            has_greek.append(concept)
        if latin:
            has_latin.append(concept)

        if greek and latin:
            has_both.append(concept)
        elif greek and not latin:
            has_greek_only.append(concept)
        elif latin and not greek:
            has_latin_only.append(concept)
        else:
            has_neither.append(concept)

    # Print summary
    print("\n" + "=" * 80)
    print("TERMINOLOGY COVERAGE SUMMARY")
    print("=" * 80)
    print(f"Concepts with Greek term:       {len(has_greek)} ({len(has_greek)/len(concepts)*100:.1f}%)")
    print(f"Concepts with Latin term:       {len(has_latin)} ({len(has_latin)/len(concepts)*100:.1f}%)")
    print(f"Concepts with BOTH:             {len(has_both)} ({len(has_both)/len(concepts)*100:.1f}%)")
    print(f"Concepts with Greek ONLY:       {len(has_greek_only)} ({len(has_greek_only)/len(concepts)*100:.1f}%)")
    print(f"Concepts with Latin ONLY:       {len(has_latin_only)} ({len(has_latin_only)/len(concepts)*100:.1f}%)")
    print(f"Concepts with NEITHER:          {len(has_neither)} ({len(has_neither)/len(concepts)*100:.1f}%)")

    # Concepts needing work
    needs_work = len(has_greek_only) + len(has_latin_only) + len(has_neither)
    print(f"\n{'='*80}")
    print(f"CONCEPTS NEEDING TERMINOLOGY: {needs_work} ({needs_work/len(concepts)*100:.1f}%)")
    print(f"{'='*80}")

    # Analyze by period
    print("\n" + "=" * 80)
    print("MISSING TERMINOLOGY BY PERIOD")
    print("=" * 80)

    missing_by_period = defaultdict(list)
    for concept in has_greek_only + has_latin_only + has_neither:
        period = concept.get('period', 'No period')
        missing_by_period[period].append(concept)

    for period in sorted(missing_by_period.keys()):
        concepts_list = missing_by_period[period]
        print(f"\n{period}: {len(concepts_list)} concepts")
        print("-" * 80)
        for c in concepts_list[:5]:
            greek = "✓" if c.get('greek_term') else "✗"
            latin = "✓" if c.get('latin_term') else "✗"
            print(f"  [Greek:{greek} Latin:{latin}] {c['id']}")
            print(f"    Label: {c.get('label', 'N/A')}")
        if len(concepts_list) > 5:
            print(f"  ... and {len(concepts_list) - 5} more")

    # Detailed lists
    print("\n" + "=" * 80)
    print("CONCEPTS WITH GREEK ONLY (need Latin)")
    print("=" * 80)
    for concept in has_greek_only:
        print(f"\n{concept['id']}")
        print(f"  Label: {concept.get('label', 'N/A')}")
        print(f"  Greek: {concept.get('greek_term')}")
        print(f"  Period: {concept.get('period', 'N/A')}")

    print("\n" + "=" * 80)
    print("CONCEPTS WITH LATIN ONLY (need Greek)")
    print("=" * 80)
    for concept in has_latin_only:
        print(f"\n{concept['id']}")
        print(f"  Label: {concept.get('label', 'N/A')}")
        print(f"  Latin: {concept.get('latin_term')}")
        print(f"  Period: {concept.get('period', 'N/A')}")

    print("\n" + "=" * 80)
    print("CONCEPTS WITH NEITHER (need both or appropriate term)")
    print("=" * 80)
    for concept in has_neither:
        print(f"\n{concept['id']}")
        print(f"  Label: {concept.get('label', 'N/A')}")
        print(f"  Period: {concept.get('period', 'N/A')}")
        print(f"  Description: {concept.get('description', 'N/A')[:100]}...")

    # Export to JSON for processing
    export_data = {
        'summary': {
            'total_concepts': len(concepts),
            'has_greek': len(has_greek),
            'has_latin': len(has_latin),
            'has_both': len(has_both),
            'needs_work': needs_work
        },
        'needs_latin': [
            {
                'id': c['id'],
                'label': c.get('label'),
                'greek_term': c.get('greek_term'),
                'period': c.get('period'),
                'description': c.get('description', '')[:200]
            } for c in has_greek_only
        ],
        'needs_greek': [
            {
                'id': c['id'],
                'label': c.get('label'),
                'latin_term': c.get('latin_term'),
                'period': c.get('period'),
                'description': c.get('description', '')[:200]
            } for c in has_latin_only
        ],
        'needs_both': [
            {
                'id': c['id'],
                'label': c.get('label'),
                'period': c.get('period'),
                'description': c.get('description', '')[:200]
            } for c in has_neither
        ]
    }

    with open('terminology_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("Analysis exported to: terminology_analysis.json")
    print("=" * 80)

    return export_data

if __name__ == '__main__':
    analyze_terminology()
