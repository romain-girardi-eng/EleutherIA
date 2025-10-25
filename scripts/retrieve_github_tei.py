#!/usr/bin/env python3
"""
GitHub TEI-XML Direct Retrieval System
=======================================
Retrieves texts directly from Perseus GitHub repositories:
- canonical-greekLit: https://github.com/PerseusDL/canonical-greekLit
- canonical-latinLit: https://github.com/PerseusDL/canonical-latinLit

This bypasses Scaife's incomplete API and gets texts directly from the source.

NO HALLUCINATION - Direct download of verified TEI-XML files.
"""

import requests
import json
from xml.etree import ElementTree as ET
from pathlib import Path
import time
from typing import Dict, List, Optional

class GitHubTEIRetriever:
    """Retrieve TEI-XML texts directly from Perseus GitHub"""

    GREEK_LIT_BASE = "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data"
    LATIN_LIT_BASE = "https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data"

    # TEI namespace
    TEI_NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def __init__(self, output_dir='retrieved_texts/github_tei'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research - Ancient Free Will Database'
        })

    def download_work_xml(self, language: str, tlg_code: str, work_code: str,
                          edition: str) -> Optional[ET.Element]:
        """Download XML file from GitHub"""

        if language == 'greek':
            base_url = self.GREEK_LIT_BASE
        elif language == 'latin':
            base_url = self.LATIN_LIT_BASE
        else:
            raise ValueError(f"Unknown language: {language}")

        # Construct URL
        filename = f"{tlg_code}.{work_code}.{edition}.xml"
        url = f"{base_url}/{tlg_code}/{work_code}/{filename}"

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

    def extract_passage_by_book_chapter(self, root: ET.Element, book: str,
                                       chapter: str = None) -> Optional[Dict]:
        """
        Extract passage from TEI-XML using Book.Chapter citation

        TEI structure typically:
        <text>
          <body>
            <div type="book" n="3">
              <div type="chapter" n="1">
                <p>Text content...</p>
              </div>
            </div>
          </body>
        </text>
        """

        # Find the book div
        book_divs = root.findall(f".//tei:div[@type='book'][@n='{book}']", self.TEI_NS)

        if not book_divs:
            # Try without type attribute
            book_divs = root.findall(f".//tei:div[@n='{book}']", self.TEI_NS)

        if not book_divs:
            return None

        book_div = book_divs[0]

        # If chapter specified, find it
        if chapter:
            chapter_divs = book_div.findall(f".//tei:div[@type='chapter'][@n='{chapter}']", self.TEI_NS)
            if not chapter_divs:
                chapter_divs = book_div.findall(f".//tei:div[@n='{chapter}']", self.TEI_NS)

            if not chapter_divs:
                return None

            target_div = chapter_divs[0]
        else:
            target_div = book_div

        # Extract text
        text_parts = []
        for p in target_div.findall('.//tei:p', self.TEI_NS):
            text = ''.join(p.itertext()).strip()
            if text:
                text_parts.append(text)

        if not text_parts:
            # Try direct text
            text = ''.join(target_div.itertext()).strip()
            if text:
                text_parts = [text]

        return {
            'book': book,
            'chapter': chapter,
            'text': ' '.join(text_parts) if text_parts else None
        }

    def extract_all_books(self, root: ET.Element) -> Dict:
        """Extract all books from a work"""

        books = {}

        # Find all book divs - check both type='book' and subtype='book'
        book_divs = root.findall(".//tei:div[@type='book']", self.TEI_NS)

        if not book_divs:
            # Try subtype='book' (Perseus TEI format)
            book_divs = root.findall(".//tei:div[@subtype='book']", self.TEI_NS)

        if not book_divs:
            # Maybe no book structure - try chapter divs
            chapter_divs = root.findall(".//tei:div[@type='chapter']", self.TEI_NS)
            if not chapter_divs:
                chapter_divs = root.findall(".//tei:div[@subtype='section']", self.TEI_NS)

            if chapter_divs:
                print(f"  Found {len(chapter_divs)} sections (no book structure)")
                for chap_div in chapter_divs:
                    chap_n = chap_div.get('n', '')
                    if chap_n:
                        text = ' '.join(chap_div.itertext()).strip()
                        books[chap_n] = {'section': chap_n, 'text': text}
                return books

        print(f"  Found {len(book_divs)} books")

        for book_div in book_divs:
            book_n = book_div.get('n', '')
            if not book_n:
                continue

            # Find sections/chapters in this book - try both
            chapter_divs = book_div.findall(".//tei:div[@type='chapter']", self.TEI_NS)
            if not chapter_divs:
                chapter_divs = book_div.findall(".//tei:div[@subtype='section']", self.TEI_NS)

            if chapter_divs:
                for chap_div in chapter_divs:
                    chap_n = chap_div.get('n', '')
                    if chap_n:
                        key = f"{book_n}.{chap_n}"
                        text_parts = []
                        for p in chap_div.findall('.//tei:p', self.TEI_NS):
                            text = ''.join(p.itertext()).strip()
                            if text:
                                text_parts.append(text)

                        books[key] = {
                            'book': book_n,
                            'chapter': chap_n,
                            'text': ' '.join(text_parts) if text_parts else ''.join(chap_div.itertext()).strip()
                        }
            else:
                # No chapters - whole book is one passage
                text = ' '.join(book_div.itertext()).strip()
                books[book_n] = {'book': book_n, 'text': text}

        return books

    def retrieve_aristotle_ne(self):
        """Test case: Retrieve Aristotle Nicomachean Ethics"""

        print("="*80)
        print("RETRIEVING: Aristotle, Nicomachean Ethics")
        print("="*80)

        # Download XML
        root = self.download_work_xml(
            language='greek',
            tlg_code='tlg0086',
            work_code='tlg010',
            edition='perseus-grc2'
        )

        if not root:
            print("✗ Failed to download")
            return None

        # Extract all passages
        print("\nExtracting passages...")
        passages = self.extract_all_books(root)

        print(f"✓ Extracted {len(passages)} passages")

        # Show samples
        print("\nSample passages:")
        for key in list(passages.keys())[:5]:
            text_preview = passages[key]['text'][:100] if passages[key]['text'] else "NO TEXT"
            print(f"  {key}: {text_preview}...")

        # Save
        work_data = {
            'metadata': {
                'work': 'Nicomachean Ethics',
                'author': 'Aristotle',
                'language': 'Greek',
                'source': 'Perseus canonical-greekLit GitHub',
                'source_url': 'https://github.com/PerseusDL/canonical-greekLit',
                'file_url': f"{self.GREEK_LIT_BASE}/tlg0086/tlg010/tlg0086.tlg010.perseus-grc2.xml",
                'edition': 'perseus-grc2',
                'format': 'TEI-XML',
                'urn': 'urn:cts:greekLit:tlg0086.tlg010.perseus-grc2',
                'retrieved_date': '2025-10-25',
                'verification_status': 'github_source',
                'passages_extracted': len(passages)
            },
            'passages': passages
        }

        output_file = self.output_dir / 'aristotle_nicomachean_ethics.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(work_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved to: {output_file}")

        return work_data


def main():
    """Test GitHub TEI retrieval"""

    retriever = GitHubTEIRetriever()

    # Test with Aristotle NE
    result = retriever.retrieve_aristotle_ne()

    if result:
        print("\n" + "="*80)
        print("SUCCESS - GitHub TEI retrieval works!")
        print("="*80)
        print(f"Passages extracted: {len(result['passages'])}")
        print("\nThis approach can be used for:")
        print("  - All works in canonical-greekLit")
        print("  - All works in canonical-latinLit")
        print("  - Bypasses Scaife's incomplete coverage")
    else:
        print("\n✗ Failed to retrieve")


if __name__ == '__main__':
    main()
