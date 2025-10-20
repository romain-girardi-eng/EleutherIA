#!/usr/bin/env python3
"""
Comprehensive extraction of ancient Greek and Latin quotes from Amand 1973.
Processes the entire 30,000+ line file systematically.
"""

import json
import re
from typing import List, Dict, Tuple
from collections import defaultdict

# Greek Unicode character ranges - using Unicode property for Greek script
GREEK_PATTERN = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]+')  # Greek and Greek Extended

# Common ancient source citation patterns
CITATION_PATTERNS = [
    # Homer
    re.compile(r'\b(Il(?:iad)?|Od(?:yssey)?)\s+([IVX]+|\d+)[.,\s]*(\d+)', re.IGNORECASE),
    # SVF (Stoicorum Veterum Fragmenta)
    re.compile(r'\bSVF\s+([IVX]+)\s*[.,]?\s*(\d+[a-z]?)', re.IGNORECASE),
    # Diels-Kranz (Vorsokratiker)
    re.compile(r'\b(DK|Diels[-\s]?Kranz)\s+(\d+[A-Z]\d+)', re.IGNORECASE),
    # Generic ancient author citations
    re.compile(r'\b([A-Z][a-z]+)\s+([IVX]+|\d+)[.,\s]*(\d+)', re.IGNORECASE),
]

# Page number patterns
PAGE_PATTERN = re.compile(r'\[(\d+)\]')

def contains_greek(text: str) -> bool:
    """Check if text contains Greek characters."""
    return bool(GREEK_PATTERN.search(text))

def extract_greek_text(text: str) -> List[str]:
    """Extract all Greek text fragments from a string."""
    return GREEK_PATTERN.findall(text)

def find_citations(text: str) -> List[str]:
    """Find ancient source citations in text."""
    citations = []
    for pattern in CITATION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            citations.extend([' '.join(str(m) for m in match if m) for match in matches])
    return citations

def extract_page_number(text: str) -> str:
    """Extract page number from text."""
    match = PAGE_PATTERN.search(text)
    return match.group(1) if match else ""

def is_likely_latin_quote(line: str, context: List[str]) -> bool:
    """
    Heuristic to identify Latin quotes from ancient sources.
    Latin quotes often appear in italics or with specific markers.
    """
    # Check for common Latin words/patterns
    latin_indicators = [
        r'\b(et|sed|quia|quod|cum|si|ut|ne|aut|vel|ac|atque)\b',
        r'\b(est|sunt|esse|erit|fuit|erat)\b',
        r'\b(deus|dei|homo|natura|causa|ratio)\b',
        r'\b(libertas|fatum|providentia|necessitas)\b'
    ]

    text_lower = line.lower()
    for pattern in latin_indicators:
        if re.search(pattern, text_lower):
            # Check if it's in a quotation context
            if '"' in line or '«' in line or '»' in line:
                return True
            # Check surrounding context
            for ctx in context:
                if 'dit' in ctx or 'écrit' in ctx or 'affirme' in ctx:
                    return True
    return False

def process_file(filepath: str) -> Dict:
    """Process the entire file and extract quotes."""

    print(f"Opening file: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"Total lines to process: {total_lines}")

    quotes = []
    current_page = ""

    for i, line in enumerate(lines):
        # Update progress every 1000 lines
        if i % 1000 == 0:
            print(f"Processing line {i}/{total_lines} ({i*100//total_lines}%)")

        # Extract page number if present
        page_match = PAGE_PATTERN.search(line)
        if page_match:
            current_page = page_match.group(1)

        # Check for Greek text
        if contains_greek(line):
            # Get context (2 lines before and after)
            context_start = max(0, i - 2)
            context_end = min(total_lines, i + 3)
            context_lines = lines[context_start:context_end]
            context = ' '.join(l.strip() for l in context_lines)

            # Extract Greek fragments
            greek_fragments = GREEK_PATTERN.findall(line)

            # Find citations in line and surrounding context
            citations = find_citations(line)
            for ctx_line in lines[max(0, i-3):min(total_lines, i+4)]:
                citations.extend(find_citations(ctx_line))
            citations = list(set(citations))  # Remove duplicates

            quote_entry = {
                "quote_text": line.strip(),
                "greek_fragments": greek_fragments,
                "source": ", ".join(citations) if citations else "citation not found",
                "page": current_page,
                "line_number": i + 1,
                "context": context[:500],  # Limit context length
                "quote_type": "Greek"
            }
            quotes.append(quote_entry)

        # Check for Latin quotes
        elif is_likely_latin_quote(line, lines[max(0, i-2):i]):
            context_start = max(0, i - 2)
            context_end = min(total_lines, i + 3)
            context_lines = lines[context_start:context_end]
            context = ' '.join(l.strip() for l in context_lines)

            citations = find_citations(line)
            for ctx_line in lines[max(0, i-3):min(total_lines, i+4)]:
                citations.extend(find_citations(ctx_line))
            citations = list(set(citations))

            quote_entry = {
                "quote_text": line.strip(),
                "source": ", ".join(citations) if citations else "citation not found",
                "page": current_page,
                "line_number": i + 1,
                "context": context[:500],
                "quote_type": "Latin"
            }
            quotes.append(quote_entry)

    print(f"\nExtraction complete!")
    print(f"Total quotes found: {len(quotes)}")

    # Statistics
    greek_count = sum(1 for q in quotes if q['quote_type'] == 'Greek')
    latin_count = sum(1 for q in quotes if q['quote_type'] == 'Latin')

    result = {
        "metadata": {
            "source": "Amand de Mendieta, Emmanuel. 1973. Fatalisme et liberté dans l'antiquité grecque. Amsterdam: A.M. Hakkert.",
            "total_lines_processed": total_lines,
            "total_quotes_found": len(quotes),
            "greek_quotes": greek_count,
            "latin_quotes": latin_count,
            "extraction_complete": True,
            "extraction_date": "2025-10-19"
        },
        "ancient_quotes": quotes
    }

    return result

def main():
    import os
    import glob

    # Change to the correct directory and find the file
    base_dir = "/Users/romaingirardi/Documents/Ancient Free Will Database"
    os.chdir(base_dir)

    # Use glob to find the file
    files = glob.glob("*Fatalisme*text.txt")
    if not files:
        print("ERROR: Could not find Amand text file!")
        return

    filepath = files[0]
    print("="*80)
    print("AMAND 1973 - COMPREHENSIVE QUOTE EXTRACTION")
    print("="*80)
    print(f"Processing file: {filepath}")

    result = process_file(filepath)

    # Save results
    output_file = "amand_1973_complete_extraction.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print("EXTRACTION SUMMARY")
    print('='*80)
    print(f"Total lines processed: {result['metadata']['total_lines_processed']}")
    print(f"Total quotes found: {result['metadata']['total_quotes_found']}")
    print(f"  - Greek quotes: {result['metadata']['greek_quotes']}")
    print(f"  - Latin quotes: {result['metadata']['latin_quotes']}")
    print(f"\nResults saved to: {output_file}")
    print('='*80)

if __name__ == "__main__":
    main()
