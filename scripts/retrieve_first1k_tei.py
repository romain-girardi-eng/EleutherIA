#!/usr/bin/env python3
"""
First1KGreek TEI-XML Retrieval System
======================================
Retrieves texts from OpenGreekAndLatin First1KGreek repository:
- Repository: https://github.com/OpenGreekAndLatin/First1KGreek

NO HALLUCINATION - Direct TEI-XML parsing from verified sources.
"""

import requests
import json
from xml.etree import ElementTree as ET
from pathlib import Path
import time
from typing import Dict, List, Optional

class First1KGreekRetriever:
    """Retrieve TEI-XML texts from First1KGreek repository"""

    FIRST1K_BASE = "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/data"

    # TEI namespace (same as Perseus/OGL)
    TEI_NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def __init__(self, output_dir='retrieved_texts/first1k_tei'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research - Ancient Free Will Database'
        })

    def download_work_xml(self, tlg_code: str, work_code: str,
                          edition: str) -> Optional[ET.Element]:
        """Download XML file from First1KGreek GitHub"""

        # Construct URL: data/{tlg}/{work}/{tlg}.{work}.{edition}.xml
        filename = f"{tlg_code}.{work_code}.{edition}.xml"
        url = f"{self.FIRST1K_BASE}/{tlg_code}/{work_code}/{filename}"

        print(f"\nDownloading: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            print(f"✓ Downloaded {len(response.content):,} bytes")

            # Parse XML
            root = ET.fromstring(response.content)
            return root

        except Exception as e:
            print(f"✗ Failed: {e}")
            return None

    def extract_all_books(self, root: ET.Element) -> Dict:
        """
        Extract all books/sections from a work
        Same structure as Perseus/OGL: <div subtype="book"><div subtype="section">
        """

        books = {}

        # Find all book divs
        book_divs = root.findall(".//tei:div[@type='textpart'][@subtype='book']", self.TEI_NS)

        if not book_divs:
            book_divs = root.findall(".//tei:div[@subtype='book']", self.TEI_NS)

        if not book_divs:
            # Maybe no book structure - try section divs directly
            section_divs = root.findall(".//tei:div[@type='textpart'][@subtype='section']", self.TEI_NS)
            if not section_divs:
                section_divs = root.findall(".//tei:div[@subtype='section']", self.TEI_NS)

            if not section_divs:
                # Try chapter
                section_divs = root.findall(".//tei:div[@subtype='chapter']", self.TEI_NS)

            if section_divs:
                print(f"  Found {len(section_divs)} sections (no book structure)")
                for sect_div in section_divs:
                    sect_n = sect_div.get('n', '')
                    if sect_n:
                        text_parts = []
                        for p in sect_div.findall('.//tei:p', self.TEI_NS):
                            text = ''.join(p.itertext()).strip()
                            if text:
                                text_parts.append(text)

                        books[sect_n] = {
                            'section': sect_n,
                            'text': ' '.join(text_parts) if text_parts else ''.join(sect_div.itertext()).strip()
                        }
                return books

        print(f"  Found {len(book_divs)} books")

        for book_div in book_divs:
            book_n = book_div.get('n', '')
            if not book_n:
                continue

            # Find sections in this book
            section_divs = book_div.findall(".//tei:div[@type='textpart'][@subtype='section']", self.TEI_NS)
            if not section_divs:
                section_divs = book_div.findall(".//tei:div[@subtype='section']", self.TEI_NS)

            if not section_divs:
                section_divs = book_div.findall(".//tei:div[@subtype='chapter']", self.TEI_NS)

            if section_divs:
                for sect_div in section_divs:
                    sect_n = sect_div.get('n', '')
                    if sect_n:
                        key = f"{book_n}.{sect_n}"
                        text_parts = []
                        for p in sect_div.findall('.//tei:p', self.TEI_NS):
                            text = ''.join(p.itertext()).strip()
                            if text:
                                text_parts.append(text)

                        books[key] = {
                            'book': book_n,
                            'section': sect_n,
                            'text': ' '.join(text_parts) if text_parts else ''.join(sect_div.itertext()).strip()
                        }
            else:
                # No sections - whole book is one passage
                text_parts = []
                for p in book_div.findall('.//tei:p', self.TEI_NS):
                    text = ''.join(p.itertext()).strip()
                    if text:
                        text_parts.append(text)

                books[book_n] = {
                    'book': book_n,
                    'text': ' '.join(text_parts) if text_parts else ''.join(book_div.itertext()).strip()
                }

        return books

    def retrieve_work(self, work_info: Dict) -> Optional[Dict]:
        """Retrieve a single work from First1KGreek"""

        print(f"\n{'='*80}")
        print(f"RETRIEVING: {work_info['name']}")
        print(f"{'='*80}")

        # Download XML
        root = self.download_work_xml(
            tlg_code=work_info['tlg_code'],
            work_code=work_info['work_code'],
            edition=work_info['edition']
        )

        if not root:
            print(f"✗ Failed to download {work_info['name']}")
            return None

        # Extract passages
        print("\nExtracting passages...")
        passages = self.extract_all_books(root)

        print(f"✓ Extracted {len(passages)} passages")

        # Show samples
        print("\nSample passages:")
        for key in list(passages.keys())[:3]:
            text_preview = passages[key].get('text', 'NO TEXT')[:80] if passages[key].get('text') else "NO TEXT"
            print(f"  {key}: {text_preview}...")

        # Build metadata
        work_data = {
            'metadata': {
                'work': work_info['work_title'],
                'author': work_info['author'],
                'language': 'Greek',
                'source': 'OpenGreekAndLatin First1KGreek GitHub',
                'source_url': 'https://github.com/OpenGreekAndLatin/First1KGreek',
                'file_url': f"{self.FIRST1K_BASE}/{work_info['tlg_code']}/{work_info['work_code']}/{work_info['tlg_code']}.{work_info['work_code']}.{work_info['edition']}.xml",
                'edition': work_info['edition'],
                'format': 'TEI-XML',
                'urn': f"urn:cts:greekLit:{work_info['tlg_code']}.{work_info['work_code']}.{work_info['edition']}",
                'retrieved_date': '2025-10-25',
                'verification_status': 'first1k_github_source',
                'passages_extracted': len(passages),
                'database_citations': work_info.get('citations', 0)
            },
            'passages': passages
        }

        # Save
        safe_name = work_info['name'].lower().replace(' ', '_').replace(',', '').replace('.', '').replace('(', '').replace(')', '')
        output_file = self.output_dir / f'{safe_name}.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(work_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved to: {output_file}")

        return work_data


def main():
    """Test First1KGreek retrieval with Sextus Empiricus"""

    retriever = First1KGreekRetriever()

    # Test with Sextus Empiricus Pyrrhoniae Hypotyposes
    test_work = {
        'name': 'Sextus Empiricus, Pyrrhoniae Hypotyposes',
        'tlg_code': 'tlg0544',
        'work_code': 'tlg001',
        'edition': '1st1K-grc1',
        'author': 'Sextus Empiricus',
        'work_title': 'Pyrrhoniae Hypotyposes',
        'citations': 16
    }

    result = retriever.retrieve_work(test_work)

    if result:
        print("\n" + "="*80)
        print("SUCCESS - First1KGreek retrieval works!")
        print("="*80)
        print(f"Passages extracted: {len(result['passages'])}")
    else:
        print("\n✗ Failed to retrieve")


if __name__ == '__main__':
    main()
