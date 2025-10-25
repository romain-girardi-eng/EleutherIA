#!/usr/bin/env python3
"""
OGL TEI-XML Direct Retrieval System
====================================
Retrieves Patristic texts directly from Open Greek and Latin GitHub:
- CSEL corpus: https://github.com/OpenGreekAndLatin/csel-dev

This gets Augustine, Origen, and other Church Fathers' texts.

NO HALLUCINATION - Direct download of verified TEI-XML files.
"""

import requests
import json
from xml.etree import ElementTree as ET
from pathlib import Path
import time
from typing import Dict, List, Optional

class OGLTEIRetriever:
    """Retrieve TEI-XML texts directly from OGL GitHub"""

    OGL_BASE = "https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev/master/data"

    # TEI namespace (same as Perseus)
    TEI_NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def __init__(self, output_dir='retrieved_texts/ogl_tei'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research - Ancient Free Will Database'
        })

    def download_work_xml(self, stoa_author: str, stoa_work: str,
                          edition: str) -> Optional[ET.Element]:
        """Download XML file from OGL GitHub"""

        # Construct URL: data/{stoa_author}/{stoa_work}/{stoa_author}.{stoa_work}.{edition}.xml
        filename = f"{stoa_author}.{stoa_work}.{edition}.xml"
        url = f"{self.OGL_BASE}/{stoa_author}/{stoa_work}/{filename}"

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
        Extract all books from a work
        OGL uses same TEI structure as Perseus: <div subtype="book"><div subtype="section">
        """

        books = {}

        # Find all book divs - check both type='book' and subtype='book'
        book_divs = root.findall(".//tei:div[@type='textpart'][@subtype='book']", self.TEI_NS)

        if not book_divs:
            # Try simpler format
            book_divs = root.findall(".//tei:div[@subtype='book']", self.TEI_NS)

        if not book_divs:
            # Maybe no book structure - try section divs directly
            section_divs = root.findall(".//tei:div[@type='textpart'][@subtype='section']", self.TEI_NS)
            if not section_divs:
                section_divs = root.findall(".//tei:div[@subtype='section']", self.TEI_NS)

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
        """Retrieve a single work from OGL"""

        print(f"\n{'='*80}")
        print(f"RETRIEVING: {work_info['name']}")
        print(f"{'='*80}")

        # Download XML
        root = self.download_work_xml(
            stoa_author=work_info['stoa_author'],
            stoa_work=work_info['stoa_work'],
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
                'language': 'Latin',
                'source': 'Open Greek and Latin (OGL) CSEL GitHub',
                'source_url': 'https://github.com/OpenGreekAndLatin/csel-dev',
                'file_url': f"{self.OGL_BASE}/{work_info['stoa_author']}/{work_info['stoa_work']}/{work_info['stoa_author']}.{work_info['stoa_work']}.{work_info['edition']}.xml",
                'edition': work_info['edition'],
                'format': 'TEI-XML',
                'urn': f"urn:cts:latinLit:{work_info['stoa_author']}.{work_info['stoa_work']}.{work_info['edition']}",
                'retrieved_date': '2025-10-25',
                'verification_status': 'ogl_github_source',
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
    """Test OGL TEI retrieval with Augustine Confessions"""

    retriever = OGLTEIRetriever()

    # Test with Augustine Confessions
    test_work = {
        'name': 'Augustine, Confessiones',
        'stoa_author': 'stoa0040',
        'stoa_work': 'stoa001',
        'edition': 'opp-lat1',
        'author': 'Augustine',
        'work_title': 'Confessiones',
        'citations': 14  # estimate
    }

    result = retriever.retrieve_work(test_work)

    if result:
        print("\n" + "="*80)
        print("SUCCESS - OGL TEI retrieval works!")
        print("="*80)
        print(f"Passages extracted: {len(result['passages'])}")
        print("\nThis approach can be used for:")
        print("  - Augustine works from CSEL")
        print("  - Other Church Fathers from OGL")
    else:
        print("\n✗ Failed to retrieve")


if __name__ == '__main__':
    main()
