#!/usr/bin/env python3
"""
Comprehensive extraction system for ancient free will database.
This will extract ALL quotes, arguments, concepts from 10 source documents.
"""

import json
import re
import hashlib
from typing import Dict, List, Tuple, Optional
import os

class ComprehensiveExtractor:
    """Extract everything from all sources systematically."""

    def __init__(self):
        self.quotes = []
        self.arguments = []
        self.concepts = []
        self.persons = []
        self.works = []
        self.debates = []
        self.relationships = []

    def detect_greek(self, text: str) -> List[Tuple[str, int, int]]:
        """Detect Greek text segments with positions."""
        greek_segments = []
        # Greek Unicode range: 0x0370-0x03FF, 0x1F00-0x1FFF (extended)
        pattern = r'[\u0370-\u03FF\u1F00-\u1FFF][\u0370-\u03FF\u1F00-\u1FFF\s\u0300-\u036F]*[\u0370-\u03FF\u1F00-\u1FFF]'

        for match in re.finditer(pattern, text):
            if len(match.group()) > 5:  # Minimum meaningful length
                greek_segments.append((match.group(), match.start(), match.end()))

        return greek_segments

    def detect_latin(self, text: str) -> List[Tuple[str, int, int]]:
        """Detect Latin text segments."""
        latin_segments = []
        # Common Latin patterns
        latin_words = ['esse', 'est', 'sunt', 'fuit', 'quod', 'quia', 'sed', 'autem',
                      'enim', 'ergo', 'igitur', 'itaque', 'voluntas', 'liberum',
                      'arbitrium', 'gratia', 'peccatum', 'natura']

        # Look for sequences with multiple Latin words
        lines = text.split('\n')
        for i, line in enumerate(lines):
            latin_count = sum(1 for word in latin_words if word in line.lower())
            if latin_count >= 2 and len(line) > 20:
                # Check it's not modern language
                if not any(modern in line.lower() for modern in ['the', 'and', 'pour', 'dans', 'with']):
                    latin_segments.append((line.strip(), i, i))

        return latin_segments

    def extract_quote_context(self, lines: List[str], quote_line: int, window: int = 3) -> Dict:
        """Extract quote with surrounding context."""
        start = max(0, quote_line - window)
        end = min(len(lines), quote_line + window + 1)

        context_before = ' '.join(lines[start:quote_line])
        context_after = ' '.join(lines[quote_line+1:end])

        # Try to extract author/work references
        author = None
        work = None

        # Look for patterns like "Chrysippus", "According to X", "X says"
        author_patterns = [
            r'(?:According to |Selon |D\'après |From )\s*([A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+(?:says|writes|argues|dit|écrit)',
            r'(?:chez|apud|in)\s+([A-Z][a-z]+)'
        ]

        for pattern in author_patterns:
            match = re.search(pattern, context_before + ' ' + context_after)
            if match:
                author = match.group(1)
                break

        return {
            'context_before': context_before,
            'context_after': context_after,
            'author': author,
            'work': work
        }

    def generate_id(self, prefix: str, text: str) -> str:
        """Generate unique ID for any entity."""
        hash_val = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        return f"{prefix}_{hash_val}"

    def extract_from_text(self, text: str, source_name: str) -> Dict:
        """Extract all entities from a text."""
        lines = text.split('\n')
        extraction_result = {
            'source': source_name,
            'quotes': [],
            'arguments': [],
            'concepts': [],
            'persons': [],
            'works': []
        }

        # Extract Greek quotes
        for line_num, line in enumerate(lines):
            greek_segments = self.detect_greek(line)
            for greek_text, start, end in greek_segments:
                context = self.extract_quote_context(lines, line_num)
                quote = {
                    'id': self.generate_id('quote_greek', greek_text),
                    'type': 'quote',
                    'language': 'Greek',
                    'greek_text': greek_text,
                    'line_number': line_num,
                    'source_file': source_name,
                    **context
                }
                extraction_result['quotes'].append(quote)

        # Extract Latin quotes
        latin_segments = self.detect_latin(text)
        for latin_text, start_line, end_line in latin_segments:
            context = self.extract_quote_context(lines, start_line)
            quote = {
                'id': self.generate_id('quote_latin', latin_text),
                'type': 'quote',
                'language': 'Latin',
                'latin_text': latin_text,
                'line_number': start_line,
                'source_file': source_name,
                **context
            }
            extraction_result['quotes'].append(quote)

        # Extract concepts (Greek and Latin terms)
        concept_patterns = [
            # Greek terms with transliteration
            (r'([\u0370-\u03FF\u1F00-\u1FFF]+)\s*\(([a-z\s\'-]+)\)', 'Greek'),
            # Latin terms in italics or quotes
            (r'[«"]([a-z\s]+)[»"]', 'Latin'),
            # Technical terms
            (r'\b(liberum arbitrium|prohairesis|autexousion|heimarmene|eph\s*hemin)\b', 'Technical')
        ]

        for pattern, lang in concept_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                term = match.group(1)
                if len(term) > 3:  # Skip very short matches
                    concept = {
                        'id': self.generate_id('concept', term),
                        'type': 'concept',
                        'term': term,
                        'language': lang,
                        'line_number': text[:match.start()].count('\n'),
                        'source_file': source_name
                    }
                    if lang == 'Greek' and match.lastindex > 1:
                        concept['transliteration'] = match.group(2)

                    extraction_result['concepts'].append(concept)

        return extraction_result

    def process_source_file(self, filepath: str) -> Dict:
        """Process a single source file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

            source_name = os.path.basename(filepath)
            return self.extract_from_text(text, source_name)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return None

    def process_all_sources(self) -> Dict:
        """Process all 10 source documents."""
        sources = {
            'girardi_m1': './.archive_20251019/01_pdf_text_chunks/Mémoire M1_text.txt',
            'girardi_m2': './.archive_20251019/01_pdf_text_chunks/Mémoire M2_text.txt',
            'girardi_phd': './.archive_20251019/01_pdf_text_chunks/Manuscrit thèse_text.txt',
            'frede_2011': './.archive_20251019/01_pdf_text_chunks/[Sather Classical Lectures, Vol. 68] Michael Frede, A. A. Long, David Sedley - A Free Will_ Origins of the Notion in Ancient Thought (2011, University of California Press) - libgen.li_text.txt',
            'dihle_1982': './.archive_20251019/01_pdf_text_chunks/Albrecht Dihle - The Theory of Will in Classical Antiquity (Sather Classical Lectures) (1982, University of California Press)_text.txt',
            'bobzien_1998': './.archive_20251019/01_pdf_text_chunks/Bobzien - 1998 - The Inadvertent Conception and Late Birth of the F_text.txt',
            'bobzien_2001': './.archive_20251019/01_pdf_text_chunks/Bobzien - 2001 - Determinism and Freedom in Stoic Philosophy_text.txt',
            'amand_1973': './.archive_20251019/01_pdf_text_chunks/Fatalisme et liberté dans l\'antiquité grecque; recherches -- Amand de Mendieta, Emmanuel -- 1973 -- Amsterdam, A_M_ Hakkert -- 9789025606466 -- 3c64633f447ac624971f36e9943a04b4 -- Anna\'s Archive_text.txt',
            'furst_2022': './.archive_20251019/01_pdf_text_chunks/Alfons Fürst - Wege zur Freiheit_ Menschliche Selbstbestimmung von Homer bis Origenes-Mohr Siebeck (2022)_Français_text.txt',
            'brouwer_2020': './.archive_20251019/01_pdf_text_chunks/Brouwer et Vimercati - 2020 - Fate, Providence and Free Will Philosophy and Religion in Dialogue in the Early Imperial Age_text.txt'
        }

        all_results = {
            'metadata': {
                'extraction_date': '2025-10-20',
                'sources_processed': len(sources),
                'extractor_version': '2.0'
            },
            'sources': {}
        }

        for source_id, filepath in sources.items():
            if os.path.exists(filepath):
                print(f"Processing {source_id}...")
                result = self.process_source_file(filepath)
                if result:
                    all_results['sources'][source_id] = result
                    print(f"  - Extracted {len(result['quotes'])} quotes")
                    print(f"  - Extracted {len(result['concepts'])} concepts")
            else:
                print(f"Source file not found: {filepath}")

        # Aggregate all extractions
        all_quotes = []
        all_concepts = []
        for source_data in all_results['sources'].values():
            all_quotes.extend(source_data['quotes'])
            all_concepts.extend(source_data['concepts'])

        all_results['summary'] = {
            'total_quotes': len(all_quotes),
            'total_concepts': len(all_concepts),
            'greek_quotes': sum(1 for q in all_quotes if q.get('language') == 'Greek'),
            'latin_quotes': sum(1 for q in all_quotes if q.get('language') == 'Latin')
        }

        return all_results

def main():
    """Main extraction process."""
    print("=" * 60)
    print("COMPREHENSIVE EXTRACTION SYSTEM")
    print("=" * 60)

    extractor = ComprehensiveExtractor()
    results = extractor.process_all_sources()

    # Save results
    with open('comprehensive_extraction_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Total quotes extracted: {results['summary']['total_quotes']}")
    print(f"  - Greek: {results['summary']['greek_quotes']}")
    print(f"  - Latin: {results['summary']['latin_quotes']}")
    print(f"Total concepts: {results['summary']['total_concepts']}")
    print("\nResults saved to: comprehensive_extraction_results.json")

if __name__ == "__main__":
    main()