#!/usr/bin/env python3
"""
Systematic extraction of ALL Greek, Latin, and Hebrew quotes from M1 Memoir
Processes all 688 lines with complete context
"""

import json
import re
from collections import defaultdict
from pathlib import Path

# Unicode ranges
GREEK_PATTERN = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]+')
HEBREW_PATTERN = re.compile(r'[\u0590-\u05FF]+')
# Latin is harder - we'll use context clues

def extract_all_quotes(filepath):
    """Read entire file and extract ALL instances of Greek, Latin, Hebrew"""

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result = {
        "document_stats": {
            "total_lines": len(lines),
            "greek_instances": 0,
            "latin_instances": 0,
            "hebrew_instances": 0,
            "greek_lines": [],
            "hebrew_lines": [],
            "latin_lines": []
        },
        "josephus_quotes": [],
        "qumran_texts": [],
        "biblical_greek": [],
        "biblical_hebrew": [],
        "ben_sirah": [],
        "philosophical_terms": [],
        "patristic_quotes": [],
        "complete_passages": []
    }

    # Process every single line
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()

        # Check for Greek
        greek_matches = GREEK_PATTERN.findall(line)
        if greek_matches:
            result["document_stats"]["greek_instances"] += len(greek_matches)
            result["document_stats"]["greek_lines"].append(i)

            # Get context (3 lines before and after)
            context_start = max(0, i-4)
            context_end = min(len(lines), i+3)
            context = ''.join(lines[context_start:context_end])

            entry = {
                "line_number": i,
                "greek_text": ' '.join(greek_matches),
                "full_line": line_stripped,
                "context": context.strip()
            }

            # Categorize by content
            if 'Josephus' in context or 'Josèphe' in context or 'Antiquit' in context:
                result["josephus_quotes"].append(entry)
            elif 'Sirah' in context or 'Ben Sirah' in context or 'Si.' in context or 'Si ' in context:
                result["ben_sirah"].append(entry)
            elif any(book in context for book in ['Rm', 'Cor', 'Gal', 'Phil', 'Eph', 'Col', 'Thess']):
                result["biblical_greek"].append(entry)
            elif 'LXX' in context or 'Septante' in context:
                result["biblical_greek"].append(entry)
            else:
                result["complete_passages"].append(entry)

        # Check for Hebrew
        hebrew_matches = HEBREW_PATTERN.findall(line)
        if hebrew_matches:
            result["document_stats"]["hebrew_instances"] += len(hebrew_matches)
            result["document_stats"]["hebrew_lines"].append(i)

            context_start = max(0, i-4)
            context_end = min(len(lines), i+3)
            context = ''.join(lines[context_start:context_end])

            entry = {
                "line_number": i,
                "hebrew_text": ' '.join(hebrew_matches),
                "full_line": line_stripped,
                "context": context.strip()
            }

            if 'Qumran' in context or '1QS' in context or '1QH' in context or 'Community Rule' in context:
                result["qumran_texts"].append(entry)
            elif 'Gen' in context or 'Gn' in context or 'Genesis' in context or 'Genèse' in context:
                result["biblical_hebrew"].append(entry)
            else:
                result["biblical_hebrew"].append(entry)

        # Check for Latin terms (common ones)
        latin_terms = [
            'peccatum originale', 'in nostra potestate', 'eph\'hemin',
            'sola gratia', 'sola fide', 'liberum arbitrium',
            'compatibilismus', 'determinismus', 'autexousion'
        ]

        line_lower = line_stripped.lower()
        for term in latin_terms:
            if term.lower() in line_lower:
                result["document_stats"]["latin_instances"] += 1
                result["document_stats"]["latin_lines"].append(i)
                result["philosophical_terms"].append({
                    "line_number": i,
                    "term": term,
                    "full_line": line_stripped,
                    "context": line_stripped
                })

    return result

def extract_specific_passages(filepath):
    """Extract specific known passages"""

    passages = {
        "genesis_6_5": {
            "reference": "Genesis 6:5",
            "hebrew": None,
            "greek_lxx": None,
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        },
        "genesis_8_21": {
            "reference": "Genesis 8:21",
            "hebrew": None,
            "greek_lxx": None,
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        },
        "josephus_ant_13_171_173": {
            "reference": "Josephus, Antiquities 13.171-173",
            "greek": None,
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        },
        "josephus_war_2_162_164": {
            "reference": "Josephus, War 2.162-164",
            "greek": None,
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        },
        "ben_sirah_15_11_20": {
            "reference": "Ben Sirah 15:11-20",
            "greek": None,
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        },
        "romans_5_12": {
            "reference": "Romans 5:12",
            "greek": None,
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        },
        "philippians_2_12_13": {
            "reference": "Philippians 2:12-13",
            "greek": None,
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        },
        "romans_7": {
            "reference": "Romans 7 (multiple verses)",
            "greek_passages": [],
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        },
        "romans_9": {
            "reference": "Romans 9 (multiple verses)",
            "greek_passages": [],
            "translation": None,
            "line_numbers": [],
            "full_context": ""
        }
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Search for each passage
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Genesis 6:5
        if '6 :5' in line or '6:5' in line or 'Gn. 6' in line:
            context_start = max(0, i-2)
            context_end = min(len(lines), i+10)
            context = ''.join(lines[context_start:context_end])

            hebrew_match = HEBREW_PATTERN.search(context)
            greek_match = GREEK_PATTERN.search(context)

            if hebrew_match or greek_match:
                passages["genesis_6_5"]["line_numbers"].append(i+1)
                passages["genesis_6_5"]["full_context"] = context.strip()
                if hebrew_match:
                    passages["genesis_6_5"]["hebrew"] = context.strip()
                if greek_match:
                    passages["genesis_6_5"]["greek_lxx"] = context.strip()

        # Genesis 8:21
        if '8 :21' in line or '8:21' in line:
            context_start = max(0, i-2)
            context_end = min(len(lines), i+10)
            context = ''.join(lines[context_start:context_end])

            hebrew_match = HEBREW_PATTERN.search(context)
            greek_match = GREEK_PATTERN.search(context)

            if hebrew_match or greek_match:
                passages["genesis_8_21"]["line_numbers"].append(i+1)
                passages["genesis_8_21"]["full_context"] = context.strip()
                if hebrew_match:
                    passages["genesis_8_21"]["hebrew"] = context.strip()
                if greek_match:
                    passages["genesis_8_21"]["greek_lxx"] = context.strip()

        # Josephus Antiquities 13.171-173
        if '171-173' in line or 'XIII' in line and 'Josèphe' in lines[max(0,i-5):i+5]:
            context_start = max(0, i-3)
            context_end = min(len(lines), i+15)
            context = ''.join(lines[context_start:context_end])

            if GREEK_PATTERN.search(context):
                passages["josephus_ant_13_171_173"]["line_numbers"].append(i+1)
                passages["josephus_ant_13_171_173"]["full_context"] = context.strip()
                passages["josephus_ant_13_171_173"]["greek"] = context.strip()

        # Ben Sirah 15:11-20
        context_start = max(0, i-3)
        context_end = min(len(lines), i+20)
        context = ''.join(lines[context_start:context_end])

        if 'Si' in line and ('15' in line or 'Sirah' in context):

            if GREEK_PATTERN.search(context):
                passages["ben_sirah_15_11_20"]["line_numbers"].append(i+1)
                passages["ben_sirah_15_11_20"]["full_context"] = context.strip()
                passages["ben_sirah_15_11_20"]["greek"] = context.strip()

        # Romans 5:12
        if 'Rm' in line and '5' in line and ('12' in line or ':12' in line):
            context_start = max(0, i-3)
            context_end = min(len(lines), i+15)
            context = ''.join(lines[context_start:context_end])

            if GREEK_PATTERN.search(context):
                passages["romans_5_12"]["line_numbers"].append(i+1)
                passages["romans_5_12"]["full_context"] = context.strip()
                passages["romans_5_12"]["greek"] = context.strip()

        # Philippians 2:12-13
        if 'Ph' in line or 'Phil' in line:
            if '2' in line and ('12' in line or '13' in line):
                context_start = max(0, i-3)
                context_end = min(len(lines), i+15)
                context = ''.join(lines[context_start:context_end])

                if GREEK_PATTERN.search(context):
                    passages["philippians_2_12_13"]["line_numbers"].append(i+1)
                    passages["philippians_2_12_13"]["full_context"] = context.strip()
                    passages["philippians_2_12_13"]["greek"] = context.strip()

        i += 1

    return passages

def main():
    """Main extraction process"""

    filepath = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/Mémoire M1_chunk_000.txt")

    print("Starting comprehensive extraction of M1 Memoir...")
    print(f"Processing {filepath}")

    # Extract all quotes
    print("\n[1/2] Extracting all Greek, Latin, Hebrew instances...")
    all_quotes = extract_all_quotes(filepath)

    # Extract specific passages
    print("[2/2] Extracting specific known passages...")
    specific_passages = extract_specific_passages(filepath)

    # Combine results
    final_result = {
        "metadata": {
            "source_file": str(filepath),
            "extraction_date": "2025-10-19",
            "total_lines_processed": 688,
            "extraction_method": "systematic_line_by_line"
        },
        "statistics": all_quotes["document_stats"],
        "josephus_quotes": all_quotes["josephus_quotes"],
        "qumran_texts": all_quotes["qumran_texts"],
        "biblical_greek": all_quotes["biblical_greek"],
        "biblical_hebrew": all_quotes["biblical_hebrew"],
        "ben_sirah": all_quotes["ben_sirah"],
        "philosophical_terms": all_quotes["philosophical_terms"],
        "patristic_quotes": all_quotes["patristic_quotes"],
        "complete_passages": all_quotes["complete_passages"],
        "specific_passages": specific_passages
    }

    # Save results
    output_file = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/complete_m1_greek_latin_extraction.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Extraction complete!")
    print(f"  - Greek instances: {final_result['statistics']['greek_instances']}")
    print(f"  - Hebrew instances: {final_result['statistics']['hebrew_instances']}")
    print(f"  - Latin instances: {final_result['statistics']['latin_instances']}")
    print(f"  - Josephus quotes: {len(final_result['josephus_quotes'])}")
    print(f"  - Ben Sirah quotes: {len(final_result['ben_sirah'])}")
    print(f"  - Biblical Greek: {len(final_result['biblical_greek'])}")
    print(f"  - Biblical Hebrew: {len(final_result['biblical_hebrew'])}")
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
