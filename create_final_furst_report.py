#!/usr/bin/env python3
"""
Create final comprehensive report on Fürst 2022 extraction.
Focus on actual ancient source citations and substantial quotes.
"""

import json
import re

def load_data():
    with open('furst_2022_complete_extraction.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_ancient_authors(context):
    """Extract ancient author references from context."""
    authors = {
        'Homer': ['Homer', 'Homère', 'Il\\.', 'Iliad', 'Iliade', 'Od\\.', 'Odyssey'],
        'Plato': ['Platon', 'Plato', 'Staat', 'République', 'Phaid', 'Gorg\\.', 'Tim\\.'],
        'Aristotle': ['Aristoteles', 'Aristote', 'eth\\. Nic\\.', 'Éth\\. Nic\\.', 'eth\\. Eud\\.'],
        'Chrysippus': ['Chrysippus', 'Chrysippe'],
        'Epicurus': ['Epicur', 'Épicure'],
        'Epictetus': ['Epikt', 'Épictète', 'Diss\\.', 'Ench\\.'],
        'Marcus Aurelius': ['Marcus? Aurel', 'Marc Aurèle'],
        'Origen': ['Origen', 'Origène', 'Origenes'],
        'Plotinus': ['Plotin', 'Enn\\.'],
        'Justin': ['Justin'],
        'Philo': ['Philo', 'Philon']
    }

    found = []
    for author, patterns in authors.items():
        for pattern in patterns:
            if re.search(pattern, context, re.IGNORECASE):
                found.append(author)
                break

    return list(set(found))

def find_verbatim_quotes(data):
    """Find quotes that appear to be verbatim ancient citations."""
    quotes = data['greek_quotes']
    verbatim = []

    for quote in quotes:
        # Criteria for verbatim quote:
        # 1. Has 4+ Greek words
        # 2. Context mentions ancient author
        # 3. Or has explicit citation

        word_count = quote.get('word_count', 0)
        context = quote.get('context', '')
        citation = quote.get('citation', '')

        if word_count >= 4:
            authors = extract_ancient_authors(context)

            if authors or citation:
                quote['identified_authors'] = authors
                verbatim.append(quote)

    return verbatim

def analyze_by_author(verbatim_quotes):
    """Group quotes by ancient author."""
    by_author = {}

    for quote in verbatim_quotes:
        authors = quote.get('identified_authors', ['Unknown'])
        for author in authors:
            if author not in by_author:
                by_author[author] = []
            by_author[author].append(quote)

    return by_author

def main():
    data = load_data()

    print('FINAL COMPREHENSIVE REPORT: FÜRST 2022 GREEK EXTRACTION')
    print('=' * 70)
    print()

    print('SOURCE WORK:')
    print(f'  {data["metadata"]["source_work"]}')
    print(f'  Publisher: {data["metadata"]["publisher"]}')
    print()

    print('EXTRACTION STATISTICS:')
    print(f'  Total Greek segments: {data["metadata"]["total_greek_segments"]}')
    print(f'  Segments with citations: {data["statistics"]["with_citations"]}')
    print()

    # Find verbatim quotes
    verbatim = find_verbatim_quotes(data)
    print(f'  Substantial quotes (4+ words): {len(verbatim)}')

    # Analyze by author
    by_author = analyze_by_author(verbatim)

    print()
    print('=' * 70)
    print('QUOTES BY ANCIENT AUTHOR:\n')

    for author in sorted(by_author.keys(), key=lambda x: -len(by_author[x])):
        quotes = by_author[author]
        print(f'{author}: {len(quotes)} quotes')

    print()
    print('=' * 70)
    print('KEY PHILOSOPHICAL TERMS IDENTIFIED:\n')

    key_terms = {
        'αὐτεξούσιον': 'autexousion - self-determination, autonomy',
        'ἐφ᾽ ἡμῖν': "eph' hêmin - what is up to us, in our power",
        'προαίρεσις': 'proairesis - deliberate choice, rational preference',
        'εἱμαρμένη': 'heimarmenê - fate, destiny',
        'ἐλευθερία': 'eleutheria - freedom, liberty',
        'ἑκούσιος': 'hekousion - voluntary',
        'ἀνάγκη': 'anankê - necessity',
        'βούλησις': 'boulêsis - wish, rational desire',
        'ὁρμή': 'hormê - impulse, inclination',
        'λόγος': 'logos - reason, rational principle'
    }

    all_text = ' '.join([q['text'] for q in data['greek_quotes']])
    for greek, translation in key_terms.items():
        count = all_text.count(greek)
        if count > 0:
            print(f'  {greek:15s} - {translation:40s} ({count} occurrences)')

    print()
    print('=' * 70)
    print('SAMPLE VERBATIM ANCIENT QUOTES:\n')

    # Show best examples by author
    for author in ['Plato', 'Aristotle', 'Epictetus', 'Origen']:
        if author in by_author:
            print(f'\n{author.upper()}:')
            print('-' * 70)
            for i, quote in enumerate(by_author[author][:3], 1):
                print(f'{i}. {quote["text"]}')
                if quote.get('citation'):
                    print(f'   Citation: {quote["citation"]}')
                print(f'   Context: {quote["context"][:200]}...')
                print()

    # Save final report
    final_output = {
        'metadata': data['metadata'],
        'summary': {
            'total_segments': len(data['greek_quotes']),
            'substantial_quotes': len(verbatim),
            'authors_identified': list(by_author.keys()),
            'key_terms': key_terms
        },
        'verbatim_quotes': verbatim,
        'quotes_by_author': {author: quotes for author, quotes in by_author.items()},
        'all_segments': data['greek_quotes']
    }

    with open('furst_2022_final_report.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print('=' * 70)
    print('✓ Final report saved to: furst_2022_final_report.json')
    print()
    print('FILES CREATED:')
    print('  1. furst_2022_complete_extraction.json - All Greek segments')
    print('  2. furst_2022_refined_extraction.json  - Categorized analysis')
    print('  3. furst_2022_final_report.json        - Verbatim quotes by author')

if __name__ == '__main__':
    main()
