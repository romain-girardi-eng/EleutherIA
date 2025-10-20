#!/usr/bin/env python3
"""
Process Amand 1973 separately (French text on Greek fatalism)
"""

import json
import re
from pathlib import Path

# Import the DocumentProcessor from the main extraction system
import sys
sys.path.append('/Users/romaingirardi/Documents/Ancient Free Will Database')

# Simplified version for Amand
def process_amand():
    amand_path = Path('/Users/romaingirardi/Documents/Ancient Free Will Database/.archive_20251019/01_pdf_text_chunks/Fatalisme et liberté dans l\'antiquité grecque; recherches -- Amand de Mendieta, Emmanuel -- 1973 -- Amsterdam, A_M_ Hakkert -- 9789025606466 -- 3c64633f447ac624971f36e9943a04b4 -- Anna\'s Archive_text.txt')

    print(f"Processing: {amand_path.name}")

    GREEK_PATTERN = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]+(?:\s+[\u0370-\u03FF\u1F00-\u1FFF]+)*')

    results = {
        'greek_extractions': [],
        'concept_mentions': 0,
        'total_lines': 0
    }

    with open(amand_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    results['total_lines'] = len(lines)

    for i, line in enumerate(lines):
        # Extract Greek
        greek_matches = GREEK_PATTERN.findall(line)
        for greek in greek_matches:
            if len(greek) > 3:
                results['greek_extractions'].append({
                    'text': greek,
                    'line': i,
                    'context': line.strip()
                })

        # Count concept mentions
        if any(term in line.lower() for term in ['fatum', 'destin', 'liberté', 'libre arbitre', 'nécessité']):
            results['concept_mentions'] += 1

    print(f"\nAmand 1973 Results:")
    print(f"  Total lines: {results['total_lines']}")
    print(f"  Greek extractions: {len(results['greek_extractions'])}")
    print(f"  Concept mentions: {results['concept_mentions']}")

    # Save
    output_path = Path('/Users/romaingirardi/Documents/Ancient Free Will Database/AMAND_EXTRACTION.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")

    return results

if __name__ == '__main__':
    process_amand()
