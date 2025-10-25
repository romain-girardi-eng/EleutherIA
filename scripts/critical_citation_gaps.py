#!/usr/bin/env python3
"""
Critical Citation Gaps Analysis
================================
Analyzes which high-value citations we already have vs. what we need to retrieve.

This cross-references:
1. All citations in database
2. Retrieved texts we already have
3. Generates priority retrieval queue for gaps

ZERO HALLUCINATION - Analysis only.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

def load_database_citations():
    """Load all citations from database"""
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    citations = []
    for node in db['nodes']:
        for field in ['ancient_sources', 'primary_sources']:
            if field in node and node[field]:
                for citation in node[field]:
                    citations.append(citation)

    for edge in db['edges']:
        if 'ancient_source' in edge and edge['ancient_source']:
            citations.append(edge['ancient_source'])

    return citations

def load_existing_retrievals():
    """Check what we've already retrieved"""
    retrieved = {}

    # Check Cicero De Fato
    cicero_file = Path('cicero_de_fato_complete.json')
    if cicero_file.exists():
        with open(cicero_file) as f:
            data = json.load(f)
            retrieved['Cicero, De Fato'] = {
                'sections': list(range(1, 49)),
                'file': str(cicero_file),
                'coverage': 'Complete (1-48)'
            }

    # Check Lucretius
    lucretius_file = Path('retrieved_texts/lucretius_drn.json')
    if lucretius_file.exists():
        with open(lucretius_file) as f:
            data = json.load(f)
            retrieved['Lucretius, De Rerum Natura'] = {
                'books': 'I-VI',
                'file': str(lucretius_file),
                'coverage': 'Complete (all 6 books, 46 passages)'
            }

    # Check Scaife CTS retrievals
    scaife_dir = Path('retrieved_texts/scaife_cts')
    if scaife_dir.exists():
        for json_file in scaife_dir.glob('*.json'):
            with open(json_file) as f:
                data = json.load(f)
                work_name = data['metadata']['work']
                author = data['metadata'].get('author', '')
                full_name = f"{author}, {work_name}" if author else work_name
                retrieved[full_name] = {
                    'sections': data['metadata'].get('sections_retrieved', 0),
                    'file': str(json_file),
                    'coverage': f"{data['metadata'].get('sections_retrieved', 0)} sections"
                }

    return retrieved

def classify_citation(citation_text, retrieved):
    """Classify whether we have this citation"""

    # Check for Cicero De Fato
    if 'Cicero' in citation_text and 'De Fato' in citation_text:
        if 'Cicero, De Fato' in retrieved:
            return 'HAVE', 'Cicero, De Fato', retrieved['Cicero, De Fato']
        return 'NEED', 'Cicero, De Fato', None

    # Check for Lucretius
    if 'Lucretius' in citation_text and 'De Rerum Natura' in citation_text:
        if 'Lucretius, De Rerum Natura' in retrieved:
            return 'HAVE', 'Lucretius, De Rerum Natura', retrieved['Lucretius, De Rerum Natura']
        return 'NEED', 'Lucretius, De Rerum Natura', None

    # Check for Aristotle NE
    if 'Aristotle' in citation_text and 'Nicomachean Ethics' in citation_text:
        return 'NEED', 'Aristotle, Nicomachean Ethics', None

    # Check for Aulus Gellius
    if 'Aulus Gellius' in citation_text or 'Gellius' in citation_text:
        return 'NEED', 'Aulus Gellius, Noctes Atticae', None

    # Check for Alexander De Fato
    if 'Alexander' in citation_text and 'De Fato' in citation_text:
        return 'NEED', 'Alexander of Aphrodisias, De Fato', None

    # Check for Plotinus
    if 'Plotinus' in citation_text or 'Enneads' in citation_text:
        return 'NEED', 'Plotinus, Enneads', None

    # Check for Epictetus
    if 'Epictetus' in citation_text:
        return 'NEED', 'Epictetus, Discourses', None

    # Check for Augustine
    if 'Augustine' in citation_text:
        return 'NEED', 'Augustine (various)', None

    # Check for Origen
    if 'Origen' in citation_text:
        return 'NEED', 'Origen (various)', None

    # Check for Biblical
    if any(book in citation_text for book in ['Romans', 'Galatians', 'Corinthians',
                                                 'Genesis', 'Exodus', 'Deuteronomy',
                                                 'Hebrew Bible', 'Septuagint']):
        return 'NEED', 'Biblical texts', None

    return 'NEED', 'Other', None

def main():
    print("=" * 80)
    print("CRITICAL CITATION GAPS ANALYSIS")
    print("=" * 80)

    # Load data
    print("\nLoading database citations...")
    citations = load_database_citations()
    print(f"✓ Found {len(citations)} citation instances")

    print("\nChecking existing retrievals...")
    retrieved = load_existing_retrievals()
    print(f"✓ Found {len(retrieved)} already retrieved works")
    for work, info in retrieved.items():
        print(f"  - {work}: {info['coverage']}")

    # Classify all citations
    print("\nClassifying citations...")
    have = defaultdict(list)
    need = defaultdict(list)

    for citation in citations:
        status, work, info = classify_citation(citation, retrieved)
        if status == 'HAVE':
            have[work].append(citation)
        else:
            need[work].append(citation)

    # Statistics
    have_count = sum(len(cites) for cites in have.values())
    need_count = sum(len(cites) for cites in need.values())
    total = have_count + need_count

    print("\n" + "=" * 80)
    print("COVERAGE STATISTICS")
    print("=" * 80)
    print(f"✅ HAVE: {have_count}/{total} citations ({have_count/total*100:.1f}%)")
    print(f"❌ NEED: {need_count}/{total} citations ({need_count/total*100:.1f}%)")

    if have:
        print("\n✅ Already Retrieved:")
        for work in sorted(have.keys()):
            print(f"  {work:50s} {len(have[work]):4d} citations")

    print("\n❌ PRIORITY GAPS (Need Retrieval):")
    sorted_needs = sorted(need.items(), key=lambda x: len(x[1]), reverse=True)

    for i, (work, cites) in enumerate(sorted_needs[:30], 1):
        print(f"{i:3d}. {work:50s} {len(cites):4d} citations")

    # Export gaps to CSV
    print("\n" + "=" * 80)
    print("Exporting detailed gap analysis...")

    with open('critical_citation_gaps.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Status', 'Work', 'Citation_Count', 'Priority', 'Sample_Citations'])

        # Already have
        for work, cites in sorted(have.items(), key=lambda x: len(x[1]), reverse=True):
            sample = '; '.join(list(set(cites))[:3])
            writer.writerow(['HAVE', work, len(cites), 'DONE', sample])

        # Need to retrieve
        for work, cites in sorted_needs:
            unique_cites = list(set(cites))
            priority = 'HIGH' if len(cites) >= 10 else 'MEDIUM' if len(cites) >= 5 else 'LOW'
            sample = '; '.join(unique_cites[:3])
            writer.writerow(['NEED', work, len(cites), priority, sample])

    print("✓ Saved to: critical_citation_gaps.csv")

    # Summary
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(f"Current coverage: {have_count}/{total} ({have_count/total*100:.1f}%)")
    print(f"\nTop 10 gaps account for: {sum(len(cites) for work, cites in sorted_needs[:10])} citations")
    print(f"Top 30 gaps account for: {sum(len(cites) for work, cites in sorted_needs[:30])} citations")
    print("\nRetrieve these high-value works next:")
    for i, (work, cites) in enumerate(sorted_needs[:10], 1):
        print(f"  {i}. {work} ({len(cites)} citations)")

    print("\n✓ Gap analysis complete")


if __name__ == '__main__':
    main()
