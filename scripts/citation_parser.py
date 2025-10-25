#!/usr/bin/env python3
"""
Citation Parser and Classifier
===============================
Analyzes all citations in the database and classifies them by:
- Source type (CTS, OGL, Biblical, Other)
- Citation format (Simple sections, Bekker pages, Book.Chapter, etc.)
- Retrieval strategy

This creates the master work queue for systematic retrieval.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from pathlib import Path

class CitationParser:
    """Parse and classify database citations"""

    # Known CTS works
    CTS_WORKS = {
        'Cicero, De Fato': 'urn:cts:latinLit:phi0474.phi054',
        'Cicero, Academica': 'urn:cts:latinLit:phi0474.phi006',
        'Cicero, De Natura Deorum': 'urn:cts:latinLit:phi0474.phi038',
        'Cicero, De Divinatione': 'urn:cts:latinLit:phi0474.phi024',
        'Lucretius, De Rerum Natura': 'urn:cts:latinLit:phi0550.phi001',
        'Aristotle, Nicomachean Ethics': 'urn:cts:greekLit:tlg0086.tlg010',
        'Aristotle, De Interpretatione': 'urn:cts:greekLit:tlg0086.tlg013',
        'Aristotle, Eudemian Ethics': 'urn:cts:greekLit:tlg0086.tlg011',
        'Alexander of Aphrodisias, De Fato': 'urn:cts:greekLit:tlg0085.tlg014',
        'Epictetus, Discourses': 'urn:cts:greekLit:tlg0557.tlg001',
        'Plutarch, De Stoicorum Repugnantiis': 'urn:cts:greekLit:tlg0007.tlg096',
        'Plotinus, Enneads': 'urn:cts:greekLit:tlg0062.tlg001',
        'Aulus Gellius, Noctes Atticae': 'urn:cts:latinLit:phi1254.phi001',
    }

    # Patristic works in OGL
    PATRISTIC_WORKS = [
        'Origen', 'Augustine', 'Eusebius', 'Nemesius', 'Justin',
        'Clement', 'Athanasius', 'Basil', 'Gregory', 'Ambrose',
        'Jerome', 'Tertullian', 'Cyprian'
    ]

    # Biblical books
    BIBLICAL_BOOKS = [
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Romans', 'Galatians', 'Corinthians', 'Ephesians', 'Philippians',
        'Colossians', 'Thessalonians', 'Timothy', 'Titus', 'Philemon',
        'Hebrews', 'James', 'Peter', 'John', 'Jude', 'Revelation',
        'Matthew', 'Mark', 'Luke', 'Acts',
        'Sirach', 'Wisdom', 'Ezra', 'Hebrew Bible', 'Septuagint', 'LXX'
    ]

    def __init__(self, db_path='ancient_free_will_database.json'):
        self.db_path = db_path
        self.citations = []
        self.parsed_citations = []
        self.stats = defaultdict(int)

    def load_citations(self):
        """Extract all citations from database"""
        with open(self.db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)

        for node in db['nodes']:
            for field in ['ancient_sources', 'primary_sources']:
                if field in node and node[field]:
                    for citation in node[field]:
                        self.citations.append({
                            'citation': citation,
                            'node_id': node['id'],
                            'node_label': node['label'],
                            'node_type': node['type']
                        })

        for edge in db['edges']:
            if 'ancient_source' in edge and edge['ancient_source']:
                self.citations.append({
                    'citation': edge['ancient_source'],
                    'edge_source': edge['source'],
                    'edge_target': edge['target'],
                    'relation': edge.get('relation', '')
                })

        print(f"Loaded {len(self.citations)} citation instances")

    def classify_citation(self, citation_text: str) -> Dict:
        """Classify a single citation"""
        result = {
            'citation': citation_text,
            'work': None,
            'source_type': 'UNKNOWN',
            'citation_format': 'UNKNOWN',
            'retrieval_strategy': 'MANUAL',
            'cts_urn': None,
            'passages': [],
            'confidence': 'low'
        }

        # Extract work name
        match = re.match(r'^([^,\(]+(?:,\s*[^,\(]+)?)', citation_text)
        if match:
            result['work'] = match.group(1).strip()

        # Check if CTS-available
        if result['work'] in self.CTS_WORKS:
            result['source_type'] = 'CTS'
            result['cts_urn'] = self.CTS_WORKS[result['work']]
            result['retrieval_strategy'] = 'CTS_AUTO'
            result['confidence'] = 'high'

        # Check if Patristic
        elif any(name in citation_text for name in self.PATRISTIC_WORKS):
            result['source_type'] = 'PATRISTIC'
            result['retrieval_strategy'] = 'OGL_OR_PG'
            result['confidence'] = 'medium'

        # Check if Biblical
        elif any(book in citation_text for book in self.BIBLICAL_BOOKS):
            result['source_type'] = 'BIBLICAL'
            result['retrieval_strategy'] = 'BIBLEHUB_OR_SEFARIA'
            result['confidence'] = 'high'

        # Detect citation format
        self._detect_format(citation_text, result)

        return result

    def _detect_format(self, text: str, result: Dict):
        """Detect citation format patterns"""

        # Simple sections: "De Fato 28-33", "De Fato 43"
        if re.search(r'\b\d+(?:-\d+)?\s*$', text):
            result['citation_format'] = 'SIMPLE_SECTIONS'
            matches = re.findall(r'\b(\d+)(?:-(\d+))?', text)
            if matches:
                for match in matches:
                    start = int(match[0])
                    end = int(match[1]) if match[1] else start
                    result['passages'].extend(range(start, end+1))

        # Bekker pages: "1113b", "1109b30-1111b3"
        elif re.search(r'\b\d{4}[ab](?:\d+)?', text):
            result['citation_format'] = 'BEKKER_PAGES'
            bekker_refs = re.findall(r'(\d{4}[ab](?:\d+)?)', text)
            result['passages'] = bekker_refs

        # Book.Chapter: "III.5", "VII.2", "I.1"
        elif re.search(r'\b[IVX]+\.\d+', text):
            result['citation_format'] = 'BOOK_CHAPTER'
            book_chapter = re.findall(r'([IVX]+)\.(\d+)', text)
            result['passages'] = [f"{b}.{c}" for b, c in book_chapter]

        # Book with line numbers: "Book II, 216-293"
        elif re.search(r'Book\s+[IVX]+.*?\d+', text, re.IGNORECASE):
            result['citation_format'] = 'BOOK_LINES'

        # Chapter:Verse (Biblical): "Romans 9:19"
        elif re.search(r'\b\d+:\d+', text):
            result['citation_format'] = 'CHAPTER_VERSE'
            cv_refs = re.findall(r'(\d+):(\d+(?:-\d+)?)', text)
            result['passages'] = [f"{c}:{v}" for c, v in cv_refs]

        # Generic "(complete text)"
        elif '(complete' in text.lower():
            result['citation_format'] = 'COMPLETE_TEXT'

    def parse_all(self):
        """Parse and classify all citations"""
        print("\nParsing and classifying citations...")

        for item in self.citations:
            parsed = self.classify_citation(item['citation'])
            parsed.update(item)
            self.parsed_citations.append(parsed)

            # Update stats
            self.stats[parsed['source_type']] += 1
            self.stats[f"format_{parsed['citation_format']}"] += 1
            self.stats[f"strategy_{parsed['retrieval_strategy']}"] += 1

        print(f"Parsed {len(self.parsed_citations)} citations")

    def print_stats(self):
        """Print classification statistics"""
        print("\n" + "="*80)
        print("CITATION CLASSIFICATION STATISTICS")
        print("="*80)

        print("\n📊 BY SOURCE TYPE:")
        for source_type in ['CTS', 'PATRISTIC', 'BIBLICAL', 'UNKNOWN']:
            count = self.stats.get(source_type, 0)
            pct = (count / len(self.citations) * 100) if len(self.citations) > 0 else 0
            print(f"  {source_type:15s} {count:5d} ({pct:5.1f}%)")

        print("\n📋 BY CITATION FORMAT:")
        formats = [k for k in self.stats.keys() if k.startswith('format_')]
        for fmt in sorted(formats):
            count = self.stats[fmt]
            pct = (count / len(self.citations) * 100) if len(self.citations) > 0 else 0
            print(f"  {fmt[7:]:20s} {count:5d} ({pct:5.1f}%)")

        print("\n🎯 BY RETRIEVAL STRATEGY:")
        strategies = [k for k in self.stats.keys() if k.startswith('strategy_')]
        for strat in sorted(strategies):
            count = self.stats[strat]
            pct = (count / len(self.citations) * 100) if len(self.citations) > 0 else 0
            print(f"  {strat[9:]:25s} {count:5d} ({pct:5.1f}%)")

    def save_results(self, output='citation_analysis.json'):
        """Save parsed citations"""
        with open(output, 'w', encoding='utf-8') as f:
            json.dump({
                'total_citations': len(self.parsed_citations),
                'statistics': dict(self.stats),
                'citations': self.parsed_citations
            }, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved analysis to: {output}")

    def generate_work_queue(self):
        """Generate prioritized work queue"""
        # Group by work
        by_work = defaultdict(list)
        for cite in self.parsed_citations:
            if cite['work']:
                by_work[cite['work']].append(cite)

        # Sort by citation count
        work_queue = []
        for work, cites in sorted(by_work.items(), key=lambda x: len(x[1]), reverse=True):
            work_queue.append({
                'work': work,
                'citation_count': len(cites),
                'source_type': cites[0]['source_type'],
                'retrieval_strategy': cites[0]['retrieval_strategy'],
                'cts_urn': cites[0].get('cts_urn'),
                'citations': cites
            })

        # Save work queue
        with open('retrieval_work_queue.json', 'w', encoding='utf-8') as f:
            json.dump(work_queue, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Generated work queue: {len(work_queue)} unique works")
        print(f"  Top 10 works account for {sum(w['citation_count'] for w in work_queue[:10])} citations")

        return work_queue


def main():
    """Run citation analysis"""
    parser = CitationParser()

    print("="*80)
    print("CITATION PARSER AND CLASSIFIER")
    print("="*80)

    parser.load_citations()
    parser.parse_all()
    parser.print_stats()
    parser.save_results()
    work_queue = parser.generate_work_queue()

    print("\n" + "="*80)
    print("TOP 20 WORKS FOR RETRIEVAL:")
    print("="*80)
    for i, work in enumerate(work_queue[:20], 1):
        print(f"{i:2d}. {work['work']:50s} ({work['citation_count']:3d} citations) [{work['source_type']}]")

    print("\n✓ Citation analysis complete")
    print("✓ Ready for systematic retrieval")


if __name__ == '__main__':
    main()
