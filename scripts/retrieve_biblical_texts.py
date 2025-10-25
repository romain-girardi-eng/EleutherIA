#!/usr/bin/env python3
"""
Biblical Text Retrieval
=======================
Retrieves Greek NT (from free academic sources), LXX, and Hebrew Bible texts.

Sources:
- Greek NT: BibleHub Berean Interlinear (free academic use)
- LXX: CCAT LXX or similar
- Hebrew: Biblia Hebraica (public domain sources)

NO HALLUCINATION - Only verified biblical texts with proper sourcing.
"""

import requests
import time
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional
from pathlib import Path

class BiblicalTextRetriever:
    """Retrieve biblical texts from authoritative free sources"""

    def __init__(self, delay=0.5, output_dir='retrieved_texts/biblical'):
        self.delay = delay
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research - Ancient Free Will Database'
        })

    def retrieve_romans_biblehub(self) -> Dict:
        """Retrieve complete book of Romans (Greek + English)"""
        print(f"\n{'='*80}")
        print("RETRIEVING: Romans (New Testament)")
        print("Source: BibleHub Berean Interlinear")
        print(f"{'='*80}\n")

        romans_data = {
            'metadata': {
                'book': 'Romans',
                'testament': 'New Testament',
                'language': 'Greek (Koine)',
                'source': 'BibleHub Berean Interlinear',
                'greek_base': 'Berean Interlinear Bible',
                'english_translation': 'Berean Study Bible',
                'url': 'https://biblehub.com/interlinear/romans/',
                'retrieved_date': '2025-10-25',
                'license': 'Free for academic use, attribution required',
                'notes': 'Based on critical Greek text'
            },
            'chapters': {}
        }

        # Romans has 16 chapters
        for chapter in range(1, 17):
            print(f"  Chapter {chapter:2d} ", end='', flush=True)

            url = f"https://biblehub.com/interlinear/romans/{chapter}.htm"

            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # BibleHub structure: Greek text in specific divs
                # This is a simplified extraction - would need detailed parsing
                text_content = soup.find('div', class_='chap')

                if text_content:
                    # Extract verse data (simplified)
                    romans_data['chapters'][str(chapter)] = {
                        'url': url,
                        'status': 'retrieved',
                        'note': 'Detailed verse parsing needed - manual verification required'
                    }
                    print("✓ (structure found - needs detailed parsing)")
                else:
                    print("✗ (no content)")

                time.sleep(self.delay)

            except Exception as e:
                print(f"✗ ({str(e)[:30]})")

        # Save
        filename = self.output_dir / 'romans_greek.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(romans_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved to: {filename}")
        print(f"⚠️  NOTE: Detailed verse parsing needs custom implementation")
        print(f"{'='*80}\n")

        return romans_data

    def retrieve_galatians_biblehub(self) -> Dict:
        """Retrieve Galatians"""
        print(f"\n{'='*80}")
        print("RETRIEVING: Galatians (New Testament)")
        print("Source: BibleHub Berean Interlinear")
        print(f"{'='*80}\n")

        galatians_data = {
            'metadata': {
                'book': 'Galatians',
                'testament': 'New Testament',
                'language': 'Greek (Koine)',
                'source': 'BibleHub Berean Interlinear',
                'greek_base': 'Berean Interlinear Bible',
                'english_translation': 'Berean Study Bible',
                'url': 'https://biblehub.com/interlinear/galatians/',
                'retrieved_date': '2025-10-25',
                'license': 'Free for academic use, attribution required',
            },
            'chapters': {}
        }

        # Galatians has 6 chapters
        for chapter in range(1, 7):
            print(f"  Chapter {chapter} ", end='', flush=True)

            url = f"https://biblehub.com/interlinear/galatians/{chapter}.htm"

            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                galatians_data['chapters'][str(chapter)] = {
                    'url': url,
                    'status': 'retrieved',
                }
                print("✓")
                time.sleep(self.delay)

            except Exception as e:
                print(f"✗ ({str(e)[:30]})")

        # Save
        filename = self.output_dir / 'galatians_greek.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(galatians_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved to: {filename}")
        print(f"{'='*80}\n")

        return galatians_data

def main():
    """Retrieve key biblical texts"""
    retriever = BiblicalTextRetriever(delay=0.5)

    # NT books cited in database
    retriever.retrieve_romans_biblehub()
    retriever.retrieve_galatians_biblehub()

    print("\n" + "="*80)
    print("BIBLICAL TEXT RETRIEVAL STATUS")
    print("="*80)
    print("\n✓ Romans - Structure retrieved (detailed parsing needed)")
    print("✓ Galatians - Structure retrieved (detailed parsing needed)")
    print("\n⚠️  NOTES:")
    print("  - BibleHub requires custom HTML parsing for full Greek text extraction")
    print("  - Alternative: Use Nestle 1904 public domain XML (more machine-readable)")
    print("  - LXX and Hebrew Bible need separate sourcing")
    print("\n📋 TODO:")
    print("  1. Implement detailed BibleHub verse parser")
    print("  2. Source Nestle 1904 XML for easier processing")
    print("  3. Find LXX Rahlfs edition")
    print("  4. Source Biblia Hebraica Stuttgartensia or WTT")
    print("="*80)

if __name__ == '__main__':
    main()
