#!/usr/bin/env python3
"""
REFINED extraction of ancient Greek and Latin quotes from Amand 1973.
Filters out noise and focuses on substantive philosophical quotes.
"""

import json
import re
from typing import List, Dict, Tuple

# Greek Unicode character ranges
GREEK_PATTERN = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]+')

# Minimum length for Greek quotes to avoid noise
MIN_GREEK_WORD_LENGTH = 3  # At least 3 Greek characters
MIN_GREEK_WORDS = 2  # At least 2 Greek words in a quote

# Common ancient source citation patterns
CITATION_PATTERNS = [
    # Homeric texts
    re.compile(r'\b(Il(?:iade?)?|Od(?:yss[eé]e)?)[.,\s]+([IVX]+|[A-Z]|\d+)[.,\s]*(\d+)[-\s]*(\d*)', re.IGNORECASE),
    # SVF (Stoicorum Veterum Fragmenta)
    re.compile(r'\bSVF\s+([IVX]+)[.,\s]*(\d+[a-z]?)', re.IGNORECASE),
    # Diels-Kranz
    re.compile(r'\b(DK|Diels[-\s]?Kranz)\s+(\d+[A-Z]\d+)', re.IGNORECASE),
    # Plato dialogues
    re.compile(r'\b(R[eé]p(?:ublique)?|Tim[eé]e|Ph[eé]don|Gorgias|Prot(?:agoras)?)[.,\s]+(\d+[a-e]?)', re.IGNORECASE),
    # Aristotle works
    re.compile(r'\b(EN|EE|Met(?:aph)?|De\s+An(?:ima)?|Phys(?:ique)?)[.,\s]+([IVX]+|\d+)[.,\s]*(\d+[ab]?\d*)', re.IGNORECASE),
    # Generic ancient citations with book/chapter
    re.compile(r'\b([A-Z][a-z]+),?\s+([IVX]+|\d+)[.,\s]+(\d+)[.,\s]*(\d*)', re.IGNORECASE),
]

# Page number patterns
PAGE_PATTERN = re.compile(r'\[(\d+)\]')

def contains_greek(text: str) -> bool:
    """Check if text contains Greek characters."""
    return bool(GREEK_PATTERN.search(text))

def extract_greek_words(text: str) -> List[str]:
    """Extract Greek word fragments that meet minimum length."""
    all_greek = GREEK_PATTERN.findall(text)
    return [g for g in all_greek if len(g) >= MIN_GREEK_WORD_LENGTH]

def is_substantive_greek_quote(text: str) -> bool:
    """
    Determine if a line contains a substantive Greek quote.
    Filters out noise like single letters, page headers, etc.
    """
    greek_words = extract_greek_words(text)

    # Need at least MIN_GREEK_WORDS substantive Greek words
    if len(greek_words) < MIN_GREEK_WORDS:
        return False

    # Total Greek characters should be substantial
    total_greek_chars = sum(len(w) for w in greek_words)
    if total_greek_chars < 10:  # At least 10 Greek characters total
        return False

    # Filter out lines that look like headers or page numbers
    if text.strip().isupper():  # All caps = likely header
        return False

    if len(text.strip()) < 15:  # Very short lines likely not quotes
        return False

    return True

def find_citations(text: str) -> List[str]:
    """Find ancient source citations in text."""
    citations = []
    for pattern in CITATION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            for match in matches:
                # Join match components, filtering empty strings
                citation = ' '.join(str(m).strip() for m in match if m and str(m).strip())
                if citation:
                    citations.append(citation)
    return citations

def extract_page_number(text: str) -> str:
    """Extract page number from text."""
    match = PAGE_PATTERN.search(text)
    return match.group(1) if match else ""

def is_likely_latin_quote(line: str, context: List[str]) -> bool:
    """
    Improved heuristic for Latin quotes from ancient sources.
    """
    # Must be in quotes or have strong markers
    has_quotes = '"' in line or '«' in line or '»' in line

    # Common Latin words (more comprehensive)
    latin_indicators = [
        r'\b(et|sed|quia|quod|cum|si|ut|ne|aut|vel|ac|atque|nam|enim)\b',
        r'\b(est|sunt|esse|erit|erunt|fuit|erat|sint|sit)\b',
        r'\b(deus|dei|homo|hominis|natura|causa|ratio|anima|animae)\b',
        r'\b(liber|libertas|libertatis|fatum|fati|providentia|necessitas)\b',
        r'\b(voluntas|voluntatis|potestas|potestatis)\b',
        r'\b(quod|quia|quoniam|igitur|ergo|autem)\b'
    ]

    line_lower = line.lower()

    # Count Latin indicators
    indicator_count = sum(1 for pattern in latin_indicators if re.search(pattern, line_lower))

    # Strong evidence: quotes + multiple Latin words
    if has_quotes and indicator_count >= 2:
        return True

    # Check context for attribution markers
    context_text = ' '.join(context).lower()
    attribution_markers = ['dit', 'écrit', 'affirme', 'déclare', 'selon', 'chez']
    has_attribution = any(marker in context_text for marker in attribution_markers)

    # Medium evidence: attribution + Latin words
    if has_attribution and indicator_count >= 3:
        return True

    # Must have substantial Latin content
    if indicator_count >= 4 and len(line.strip()) > 30:
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
    greek_count = 0
    latin_count = 0

    for i, line in enumerate(lines):
        # Update progress every 1000 lines
        if i % 1000 == 0:
            print(f"Processing line {i}/{total_lines} ({i*100//total_lines}%) - "
                  f"Greek: {greek_count}, Latin: {latin_count}")

        # Extract page number if present
        page_match = PAGE_PATTERN.search(line)
        if page_match:
            current_page = page_match.group(1)

        # Check for substantive Greek text
        if contains_greek(line) and is_substantive_greek_quote(line):
            # Get context (3 lines before and after)
            context_start = max(0, i - 3)
            context_end = min(total_lines, i + 4)
            context_lines = lines[context_start:context_end]
            context = ' '.join(l.strip() for l in context_lines)

            # Extract Greek fragments
            greek_words = extract_greek_words(line)

            # Find citations in broader context
            citations = []
            for ctx_line in lines[max(0, i-5):min(total_lines, i+6)]:
                citations.extend(find_citations(ctx_line))
            citations = list(set(citations))  # Remove duplicates

            quote_entry = {
                "quote_text": line.strip(),
                "greek_words": greek_words,
                "source": ", ".join(citations) if citations else "citation not found",
                "page": current_page,
                "line_number": i + 1,
                "context": context[:600],  # Limit context length
                "quote_type": "Greek"
            }
            quotes.append(quote_entry)
            greek_count += 1

        # Check for Latin quotes
        elif is_likely_latin_quote(line, lines[max(0, i-2):i]):
            context_start = max(0, i - 3)
            context_end = min(total_lines, i + 4)
            context_lines = lines[context_start:context_end]
            context = ' '.join(l.strip() for l in context_lines)

            citations = []
            for ctx_line in lines[max(0, i-5):min(total_lines, i+6)]:
                citations.extend(find_citations(ctx_line))
            citations = list(set(citations))

            quote_entry = {
                "quote_text": line.strip(),
                "source": ", ".join(citations) if citations else "citation not found",
                "page": current_page,
                "line_number": i + 1,
                "context": context[:600],
                "quote_type": "Latin"
            }
            quotes.append(quote_entry)
            latin_count += 1

    print(f"\nExtraction complete!")
    print(f"Total quotes found: {len(quotes)}")
    print(f"  - Greek: {greek_count}")
    print(f"  - Latin: {latin_count}")

    result = {
        "metadata": {
            "source": "Amand de Mendieta, Emmanuel. 1973. Fatalisme et liberté dans l'antiquité grecque. Amsterdam: A.M. Hakkert.",
            "isbn": "9789025606466",
            "total_lines_processed": total_lines,
            "total_quotes_found": len(quotes),
            "greek_quotes": greek_count,
            "latin_quotes": latin_count,
            "extraction_complete": True,
            "extraction_date": "2025-10-19",
            "filtering": "Refined extraction with noise filtering",
            "min_greek_word_length": MIN_GREEK_WORD_LENGTH,
            "min_greek_words_per_quote": MIN_GREEK_WORDS
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
    print("AMAND 1973 - REFINED QUOTE EXTRACTION")
    print("="*80)
    print(f"Processing file: {filepath}\n")

    result = process_file(filepath)

    # Save results
    output_file = "amand_1973_complete_extraction.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print("EXTRACTION SUMMARY")
    print('='*80)
    print(f"Total lines processed: {result['metadata']['total_lines_processed']:,}")
    print(f"Total quotes found: {result['metadata']['total_quotes_found']:,}")
    print(f"  - Greek quotes: {result['metadata']['greek_quotes']:,}")
    print(f"  - Latin quotes: {result['metadata']['latin_quotes']:,}")
    print(f"\nResults saved to: {output_file}")
    print('='*80)

    # Show a few examples
    print("\nSample Greek quotes:")
    greek_quotes = [q for q in result['ancient_quotes'] if q['quote_type'] == 'Greek'][:5]
    for i, q in enumerate(greek_quotes, 1):
        print(f"\n{i}. Page {q['page']}, Line {q['line_number']}")
        print(f"   {q['quote_text'][:120]}...")
        print(f"   Source: {q['source']}")

    print("\n\nSample Latin quotes:")
    latin_quotes = [q for q in result['ancient_quotes'] if q['quote_type'] == 'Latin'][:5]
    for i, q in enumerate(latin_quotes, 1):
        print(f"\n{i}. Page {q['page']}, Line {q['line_number']}")
        print(f"   {q['quote_text'][:120]}...")
        print(f"   Source: {q['source']}")

if __name__ == "__main__":
    main()
