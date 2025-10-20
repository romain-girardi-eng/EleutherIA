#!/usr/bin/env python3
"""
Comprehensive Extraction System for Ancient Free Will Database
Processes all 10 source documents to extract:
- Greek and Latin text with context
- Philosophical arguments with premises/conclusions
- Debates and controversies
- Person mentions with biographical details
- Work citations
- Concept definitions and evolution
- Relationships between ideas
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import unicodedata

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class GreekLatinExtraction:
    """Greek or Latin text with full context"""
    language: str  # 'greek' or 'latin'
    text: str
    transliteration: str
    translation: str
    context: str  # surrounding paragraph
    source_document: str
    page_reference: str
    ancient_source: str  # e.g., "Aristotle, EN III.5"
    modern_discussion: str  # scholarly commentary

@dataclass
class PhilosophicalArgument:
    """Structured philosophical argument"""
    argument_id: str
    label: str
    proponent: str  # philosopher who made the argument
    opponents: List[str]  # philosophers who refuted it
    premises: List[str]
    conclusion: str
    context: str
    period: str
    school: str
    source_document: str
    ancient_sources: List[str]
    modern_scholarship: List[str]
    related_concepts: List[str]

@dataclass
class Debate:
    """Philosophical debate or controversy"""
    debate_id: str
    label: str
    participants: List[str]
    positions: Dict[str, str]  # person -> their position
    central_question: str
    historical_context: str
    period: str
    source_document: str
    ancient_sources: List[str]
    modern_scholarship: List[str]

@dataclass
class PersonMention:
    """Person mentioned in text with details"""
    name: str
    dates: str
    school: str
    period: str
    role: str  # e.g., "formulator", "critic", "synthesizer"
    positions: List[str]  # their philosophical positions
    works_mentioned: List[str]
    context: str
    source_document: str

@dataclass
class WorkCitation:
    """Ancient or modern work citation"""
    title: str
    author: str
    date: str
    citation_format: str  # e.g., "EN III.5", "De Fato 40"
    quoted_passage: str
    context: str
    source_document: str

@dataclass
class ConceptDefinition:
    """Concept with definition and evolution"""
    concept_id: str
    label: str
    greek_term: str
    latin_term: str
    english_term: str
    definition: str
    historical_development: List[str]  # chronological evolution
    related_concepts: List[str]
    period: str
    source_document: str
    ancient_sources: List[str]
    modern_scholarship: List[str]

@dataclass
class Relationship:
    """Relationship between ideas/persons/concepts"""
    source_id: str
    target_id: str
    relation_type: str
    context: str
    source_document: str
    evidence: str

# ============================================================================
# PATTERN RECOGNITION
# ============================================================================

class PatternExtractor:
    """Extract patterns from text using sophisticated regex and context analysis"""

    # Greek text detection (Unicode range for Greek and Coptic)
    GREEK_PATTERN = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]+(?:\s+[\u0370-\u03FF\u1F00-\u1FFF]+)*')

    # Latin text detection (classical Latin with macrons)
    LATIN_PATTERN = re.compile(r'\b[A-ZĀĒĪŌŪa-zāēīōū]+(?:\s+[A-ZĀĒĪŌŪa-zāēīōū]+)*\b')

    # Citation patterns
    ARISTOTLE_CITATION = re.compile(r'(EN|EE|Phys\.|Metaph\.|De Int\.|Cat\.|Top\.|An\. Post\.|An\. Pr\.|Rhet\.|Poet\.|Pol\.|De An\.)\s+([IVX]+)\.(\d+)(?:,\s*(\d+[ab]?\d*))?')
    STOIC_CITATION = re.compile(r'SVF\s+([IVX]+)\s+(\d+)')
    CICERO_CITATION = re.compile(r'(De Fato|De Nat\. Deor\.|De Fin\.|Tusc\.)\s+(\d+)(?:\.(\d+))?')
    ALEXANDER_CITATION = re.compile(r'In De Fato\s+(\d+)(?:,\s*(\d+))?')

    # Argument indicators
    PREMISE_INDICATORS = [
        r'if\s+',
        r'since\s+',
        r'given\s+that',
        r'assuming\s+',
        r'suppose\s+',
        r'premiss[e]?\s+\d+:',
        r'\(\d+\)',
    ]

    CONCLUSION_INDICATORS = [
        r'therefore',
        r'thus',
        r'hence',
        r'it follows that',
        r'we conclude that',
        r'conclusion:',
    ]

    # Philosophical terms
    CORE_CONCEPTS = {
        'free_will': [r'ἐφ\' ἡμῖν', r'in nostra potestate', r'liberum arbitrium', r'free will', r'free choice'],
        'fate': [r'εἱμαρμένη', r'fatum', r'fate', r'destiny', r'heimarmene'],
        'determinism': [r'determinism', r'necessity', r'ἀνάγκη', r'necessitas'],
        'responsibility': [r'responsibility', r'moral agency', r'imputation'],
        'causation': [r'αἰτία', r'causa', r'causation', r'causal'],
        'contingency': [r'ἐνδεχόμενον', r'contingens', r'contingent', r'possible'],
        'assent': [r'συγκατάθεσις', r'assensus', r'assent'],
        'impulse': [r'ὁρμή', r'impetus', r'impulse', r'horme'],
    }

    @classmethod
    def extract_greek_text(cls, line: str, context: str) -> List[str]:
        """Extract all Greek text from a line"""
        return cls.GREEK_PATTERN.findall(line)

    @classmethod
    def extract_latin_text(cls, line: str, context: str) -> List[str]:
        """Extract Latin text (requires context to distinguish from English)"""
        # This is a simplified version - real implementation needs more context
        matches = cls.LATIN_PATTERN.findall(line)
        # Filter out common English words
        latin_words = []
        for match in matches:
            if cls._is_likely_latin(match, context):
                latin_words.append(match)
        return latin_words

    @classmethod
    def _is_likely_latin(cls, text: str, context: str) -> bool:
        """Heuristic to determine if text is Latin vs English"""
        # Latin indicators
        latin_indicators = [
            '-que', '-ve', 'orum', 'arum', 'ibus', 'um', 'ae', 'is',
            'atur', 'antur', 'etur', 'entur'
        ]
        # Check for Latin endings
        for indicator in latin_indicators:
            if text.endswith(indicator):
                return True
        # Check if in italics context (common for Latin in modern scholarship)
        if '_' in context or '*' in context:  # markdown italics
            return True
        return False

    @classmethod
    def extract_citations(cls, line: str) -> List[Dict[str, str]]:
        """Extract ancient source citations"""
        citations = []

        # Aristotle
        for match in cls.ARISTOTLE_CITATION.finditer(line):
            citations.append({
                'type': 'aristotle',
                'work': match.group(1),
                'book': match.group(2),
                'chapter': match.group(3),
                'section': match.group(4) if match.group(4) else '',
                'full': match.group(0)
            })

        # Stoic fragments
        for match in cls.STOIC_CITATION.finditer(line):
            citations.append({
                'type': 'stoic_fragment',
                'volume': match.group(1),
                'number': match.group(2),
                'full': match.group(0)
            })

        # Cicero
        for match in cls.CICERO_CITATION.finditer(line):
            citations.append({
                'type': 'cicero',
                'work': match.group(1),
                'book': match.group(2),
                'section': match.group(3) if match.group(3) else '',
                'full': match.group(0)
            })

        # Alexander of Aphrodisias
        for match in cls.ALEXANDER_CITATION.finditer(line):
            citations.append({
                'type': 'alexander',
                'work': 'In De Fato',
                'chapter': match.group(1),
                'section': match.group(2) if match.group(2) else '',
                'full': match.group(0)
            })

        return citations

    @classmethod
    def detect_argument_structure(cls, text: str) -> Dict[str, Any]:
        """Detect premises and conclusions in text"""
        lines = text.split('\n')
        premises = []
        conclusion = None

        for i, line in enumerate(lines):
            # Check for premise indicators
            for pattern in cls.PREMISE_INDICATORS:
                if re.search(pattern, line, re.IGNORECASE):
                    premises.append(line.strip())
                    break

            # Check for conclusion indicators
            for pattern in cls.CONCLUSION_INDICATORS:
                if re.search(pattern, line, re.IGNORECASE):
                    conclusion = line.strip()
                    break

        return {
            'premises': premises,
            'conclusion': conclusion,
            'has_structure': len(premises) > 0 or conclusion is not None
        }

    @classmethod
    def extract_concepts(cls, text: str) -> Dict[str, List[str]]:
        """Extract philosophical concept mentions"""
        concepts = defaultdict(list)

        for concept_name, patterns in cls.CORE_CONCEPTS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    concepts[concept_name].append(match.group(0))

        return dict(concepts)

# ============================================================================
# DOCUMENT PROCESSOR
# ============================================================================

class DocumentProcessor:
    """Process individual documents line by line"""

    def __init__(self, file_path: Path, source_name: str):
        self.file_path = file_path
        self.source_name = source_name
        self.extractor = PatternExtractor()

    def process(self) -> Dict[str, List[Any]]:
        """Process document and extract all relevant content"""
        results = {
            'greek_latin': [],
            'arguments': [],
            'debates': [],
            'persons': [],
            'works': [],
            'concepts': [],
            'relationships': []
        }

        print(f"\n{'='*80}")
        print(f"Processing: {self.source_name}")
        print(f"{'='*80}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        context_window = []

        for i, line in enumerate(lines):
            if i % 1000 == 0:
                print(f"Progress: {i}/{total_lines} lines ({100*i/total_lines:.1f}%)")

            # Maintain context window (previous 5 lines)
            context_window.append(line)
            if len(context_window) > 5:
                context_window.pop(0)

            context = '\n'.join(context_window)

            # Extract Greek text
            greek_texts = self.extractor.extract_greek_text(line, context)
            for greek in greek_texts:
                if len(greek) > 3:  # Filter out single characters
                    results['greek_latin'].append({
                        'language': 'greek',
                        'text': greek,
                        'context': context,
                        'source': self.source_name,
                        'line_number': i
                    })

            # Extract citations
            citations = self.extractor.extract_citations(line)
            for citation in citations:
                results['works'].append({
                    'citation': citation,
                    'context': context,
                    'source': self.source_name,
                    'line_number': i
                })

            # Extract concepts
            concepts = self.extractor.extract_concepts(line)
            if concepts:
                results['concepts'].append({
                    'concepts': concepts,
                    'context': context,
                    'source': self.source_name,
                    'line_number': i
                })

        # Post-process: extract arguments from paragraphs
        results['arguments'] = self._extract_arguments(lines)

        # Post-process: extract person mentions
        results['persons'] = self._extract_persons(lines)

        # Post-process: extract debates
        results['debates'] = self._extract_debates(lines)

        print(f"\nExtraction complete:")
        print(f"  - Greek/Latin texts: {len(results['greek_latin'])}")
        print(f"  - Citations: {len(results['works'])}")
        print(f"  - Concept mentions: {len(results['concepts'])}")
        print(f"  - Arguments: {len(results['arguments'])}")
        print(f"  - Persons: {len(results['persons'])}")
        print(f"  - Debates: {len(results['debates'])}")

        return results

    def _extract_arguments(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract philosophical arguments from text"""
        arguments = []

        # Process text in paragraphs
        paragraphs = self._split_into_paragraphs(lines)

        for para_num, paragraph in enumerate(paragraphs):
            arg_structure = self.extractor.detect_argument_structure(paragraph)
            if arg_structure['has_structure']:
                arguments.append({
                    'paragraph_number': para_num,
                    'premises': arg_structure['premises'],
                    'conclusion': arg_structure['conclusion'],
                    'full_text': paragraph,
                    'source': self.source_name
                })

        return arguments

    def _extract_persons(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract person mentions with details"""
        persons = []

        # Common philosopher names
        philosopher_names = [
            'Aristotle', 'Plato', 'Socrates',
            'Chrysippus', 'Zeno', 'Cleanthes', 'Posidonius',
            'Epicurus', 'Lucretius',
            'Carneades', 'Philo', 'Antiochus',
            'Cicero', 'Seneca', 'Epictetus', 'Marcus Aurelius',
            'Alexander of Aphrodisias', 'Plotinus', 'Porphyry',
            'Origen', 'Augustine', 'Boethius', 'Gregory of Nyssa'
        ]

        for i, line in enumerate(lines):
            for name in philosopher_names:
                if name in line:
                    context = self._get_context(lines, i, window=3)
                    persons.append({
                        'name': name,
                        'context': context,
                        'line_number': i,
                        'source': self.source_name
                    })

        return persons

    def _extract_debates(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract debates and controversies"""
        debates = []

        # Debate indicators
        debate_patterns = [
            r'debate\s+(?:between|among)',
            r'controversy\s+(?:between|over)',
            r'disagreement\s+(?:between|about)',
            r'(\w+)\s+(?:argues|claims|maintains)\s+.*\s+(?:while|whereas)\s+(\w+)\s+(?:argues|claims|maintains)',
        ]

        for i, line in enumerate(lines):
            for pattern in debate_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    context = self._get_context(lines, i, window=5)
                    debates.append({
                        'indicator': pattern,
                        'context': context,
                        'line_number': i,
                        'source': self.source_name
                    })

        return debates

    def _split_into_paragraphs(self, lines: List[str]) -> List[str]:
        """Split lines into paragraphs"""
        paragraphs = []
        current_para = []

        for line in lines:
            if line.strip():
                current_para.append(line)
            else:
                if current_para:
                    paragraphs.append('\n'.join(current_para))
                    current_para = []

        if current_para:
            paragraphs.append('\n'.join(current_para))

        return paragraphs

    def _get_context(self, lines: List[str], line_num: int, window: int = 3) -> str:
        """Get context around a line"""
        start = max(0, line_num - window)
        end = min(len(lines), line_num + window + 1)
        return '\n'.join(lines[start:end])

# ============================================================================
# MAIN EXTRACTION SYSTEM
# ============================================================================

class ComprehensiveExtractionSystem:
    """Orchestrate extraction from all documents"""

    def __init__(self, archive_dir: Path):
        self.archive_dir = archive_dir
        self.documents = self._discover_documents()

    def _discover_documents(self) -> Dict[str, Path]:
        """Discover all text files to process"""
        docs = {}

        # Map simplified names to actual files
        file_mapping = {
            'girardi_m1': 'Mémoire M1_text.txt',
            'girardi_m2': 'Mémoire M2_text.txt',
            'girardi_phd': 'Manuscrit thèse_text.txt',
            'frede_2011': '[Sather Classical Lectures, Vol. 68] Michael Frede, A. A. Long, David Sedley - A Free Will_ Origins of the Notion in Ancient Thought (2011, University of California Press) - libgen.li_text.txt',
            'dihle_1982': 'Albrecht Dihle - The Theory of Will in Classical Antiquity (Sather Classical Lectures) (1982, University of California Press)_text.txt',
            'bobzien_1998': 'Bobzien - 1998 - The Inadvertent Conception and Late Birth of the F_text.txt',
            'bobzien_2001': 'Bobzien - 2001 - Determinism and Freedom in Stoic Philosophy_text.txt',
            'amand_1973': "Fatalisme et liberté dans l'antiquité grecque; recherches -- Amand de Mendieta, Emmanuel -- 1973 -- Amsterdam, A_M_ Hakkert -- 9789025606466 -- 3c64633f447ac624971f36e9943a04b4 -- Anna's Archive_text.txt",
            'furst_2022': 'Alfons Fürst - Wege zur Freiheit_ Menschliche Selbstbestimmung von Homer bis Origenes-Mohr Siebeck (2022)_Français_text.txt',
            'brouwer_2020': 'Brouwer et Vimercati - 2020 - Fate, Providence and Free Will Philosophy and Religion in Dialogue in the Early Imperial Age_text.txt'
        }

        for name, filename in file_mapping.items():
            file_path = self.archive_dir / filename
            if file_path.exists():
                docs[name] = file_path
                print(f"✓ Found: {name}")
            else:
                print(f"✗ Missing: {name} ({filename})")

        return docs

    def process_all(self) -> Dict[str, Any]:
        """Process all documents and aggregate results"""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE EXTRACTION SYSTEM")
        print(f"{'='*80}")
        print(f"Found {len(self.documents)} documents to process\n")

        all_results = {
            'metadata': {
                'extraction_date': '2025-10-20',
                'documents_processed': list(self.documents.keys()),
                'total_documents': len(self.documents)
            },
            'extractions': {}
        }

        for doc_name, doc_path in self.documents.items():
            processor = DocumentProcessor(doc_path, doc_name)
            results = processor.process()
            all_results['extractions'][doc_name] = results

        # Generate summary statistics
        all_results['summary'] = self._generate_summary(all_results['extractions'])

        return all_results

    def _generate_summary(self, extractions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            'total_greek_latin': 0,
            'total_arguments': 0,
            'total_debates': 0,
            'total_persons': 0,
            'total_works': 0,
            'total_concepts': 0,
            'by_document': {}
        }

        for doc_name, doc_results in extractions.items():
            doc_summary = {
                'greek_latin': len(doc_results.get('greek_latin', [])),
                'arguments': len(doc_results.get('arguments', [])),
                'debates': len(doc_results.get('debates', [])),
                'persons': len(doc_results.get('persons', [])),
                'works': len(doc_results.get('works', [])),
                'concepts': len(doc_results.get('concepts', []))
            }
            summary['by_document'][doc_name] = doc_summary

            summary['total_greek_latin'] += doc_summary['greek_latin']
            summary['total_arguments'] += doc_summary['arguments']
            summary['total_debates'] += doc_summary['debates']
            summary['total_persons'] += doc_summary['persons']
            summary['total_works'] += doc_summary['works']
            summary['total_concepts'] += doc_summary['concepts']

        return summary

    def save_results(self, results: Dict[str, Any], output_path: Path):
        """Save extraction results to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*80}")
        print(f"Results saved to: {output_path}")
        print(f"{'='*80}")
        print(f"\nSUMMARY:")
        print(f"  Total Greek/Latin extractions: {results['summary']['total_greek_latin']}")
        print(f"  Total arguments: {results['summary']['total_arguments']}")
        print(f"  Total debates: {results['summary']['total_debates']}")
        print(f"  Total persons: {results['summary']['total_persons']}")
        print(f"  Total works: {results['summary']['total_works']}")
        print(f"  Total concepts: {results['summary']['total_concepts']}")
        print(f"\nDetailed breakdown by document saved in JSON file.")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    archive_dir = Path('/Users/romaingirardi/Documents/Ancient Free Will Database/.archive_20251019/01_pdf_text_chunks')
    output_path = Path('/Users/romaingirardi/Documents/Ancient Free Will Database/COMPREHENSIVE_EXTRACTION_RESULTS.json')

    system = ComprehensiveExtractionSystem(archive_dir)
    results = system.process_all()
    system.save_results(results, output_path)

    print("\n✓ Extraction complete!")
    print(f"\nNext steps:")
    print(f"1. Review extracted content in: {output_path}")
    print(f"2. Verify Greek/Latin extractions")
    print(f"3. Validate argument structures")
    print(f"4. Integrate into knowledge graph")

if __name__ == '__main__':
    main()
