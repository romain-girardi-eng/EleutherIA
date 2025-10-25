#!/usr/bin/env python3
"""
Classical Text Retrieval System
================================
Retrieves ancient Greek and Latin texts from Perseus Digital Library
with full provenance tracking and verification.

NO HALLUCINATION POLICY:
- Only retrieves texts from authoritative sources (Perseus Digital Library)
- Documents complete provenance for every text
- Tracks verification status
- Flags missing or uncertain texts for manual review
"""

import requests
import time
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys

class PerseuTextRetriever:
    """Retrieve texts from Perseus Digital Library with verification"""

    BASE_URL = "http://www.perseus.tufts.edu/hopper/text"

    # Perseus work IDs for major works cited in the database
    WORK_IDS = {
        'Cicero_De_Fato': 'Perseus:text:2007.01.0035',
        'Aristotle_Nicomachean_Ethics': 'Perseus:text:1999.01.0053',  # Greek
        'Aristotle_Nicomachean_Ethics_EN': 'Perseus:text:1999.01.0054',  # English
        'Alexander_De_Fato': 'Perseus:text:2008.01.0451',  # If available
        'Lucretius_De_Rerum_Natura': 'Perseus:text:1999.02.0131',
        'Cicero_Academica': 'Perseus:text:2007.01.0024',
        'Epictetus_Discourses': 'Perseus:text:1999.01.0236',
        'Origen_De_Principiis': None,  # Not in Perseus, needs alternative source
        'Plutarch_De_Stoicorum_Repugnantiis': 'Perseus:text:2008.01.0398',
    }

    def __init__(self, delay=0.5):
        """
        Initialize retriever

        Args:
            delay: Delay between requests in seconds (be respectful to Perseus)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research Bot - Ancient Free Will Database (romain.girardi@univ-cotedazur.fr)'
        })

    def retrieve_section(self, work_id: str, section: str, lang='original') -> Optional[str]:
        """
        Retrieve a single section of a work

        Args:
            work_id: Perseus text identifier (e.g., 'Perseus:text:2007.01.0035')
            section: Section number or identifier
            lang: 'original' for Greek/Latin, 'english' for translation

        Returns:
            Cleaned text or None if retrieval failed
        """
        url = f"{self.BASE_URL}?doc={work_id}:section={section}&lang={lang}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            text_div = soup.find('div', class_='text')

            if not text_div:
                return None

            # Remove navigation elements
            for elem in text_div.find_all(['div', 'span'], class_=['header', 'context']):
                elem.decompose()

            # Extract and clean text
            text = text_div.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\[\s*\d+\s*\]', '', text)  # Remove section markers
            text = re.sub(r'\[p\.\s*\d+\]', '', text)  # Remove page markers

            return text.strip() if text.strip() else None

        except Exception as e:
            print(f"  ERROR retrieving {section}: {e}", file=sys.stderr)
            return None

    def retrieve_complete_work(
        self,
        work_id: str,
        work_name: str,
        author: str,
        language: str,
        section_range: range,
        edition: str = "Unknown"
    ) -> Dict:
        """
        Retrieve complete work with all sections

        Args:
            work_id: Perseus text identifier
            work_name: Human-readable work name
            author: Author name
            language: 'Latin', 'Greek', etc.
            section_range: Range of sections to retrieve (e.g., range(1, 49) for 1-48)
            edition: Edition information

        Returns:
            Dictionary with metadata and all sections
        """
        print(f"\n{'='*80}")
        print(f"Retrieving: {author}, {work_name}")
        print(f"Language: {language} | Sections: {section_range.start}-{section_range.stop-1}")
        print(f"{'='*80}\n")

        work_data = {
            'metadata': {
                'work': work_name,
                'author': author,
                'language': language,
                'source': 'Perseus Digital Library',
                'perseus_id': work_id,
                'edition': edition,
                'retrieved_date': datetime.now().isoformat(),
                'total_sections': len(section_range),
                'retrieval_status': 'in_progress'
            },
            'sections': {}
        }

        failed_sections = []
        success_count = 0

        for section in section_range:
            print(f"Section {section:3d}/{section_range.stop-1} ", end='', flush=True)

            # Get original language
            original = self.retrieve_section(work_id, section, 'original')
            time.sleep(self.delay)

            if original:
                work_data['sections'][str(section)] = {
                    language.lower(): original,
                    'url': f"{self.BASE_URL}?doc={work_id}:section={section}&lang=original",
                    'verification_status': 'retrieved_from_perseus',
                    'needs_review': False
                }
                success_count += 1
                print(f"✓ ({len(original)} chars)")
            else:
                failed_sections.append(section)
                print("✗ FAILED")

        work_data['metadata']['retrieval_status'] = 'completed'
        work_data['metadata']['sections_retrieved'] = success_count
        work_data['metadata']['sections_failed'] = failed_sections

        print(f"\n{'='*80}")
        print(f"✓ Retrieved {success_count}/{len(section_range)} sections")
        if failed_sections:
            print(f"✗ Failed sections: {failed_sections}")
        print(f"{'='*80}\n")

        return work_data

    def save_work(self, work_data: Dict, filename: str):
        """Save retrieved work to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(work_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to: {filename}\n")


def main():
    """Main retrieval script"""
    retriever = PerseusTextRetriever(delay=0.4)

    # Priority works based on citation frequency
    retrieval_queue = [
        {
            'work_id': 'Perseus:text:2007.01.0035',
            'work_name': 'De Fato',
            'author': 'Marcus Tullius Cicero',
            'language': 'Latin',
            'sections': range(1, 49),
            'edition': 'C. F. W. Müller, Leipzig: Teubner, 1915',
            'output': 'retrieved_texts/cicero_de_fato.json'
        },
        {
            'work_id': 'Perseus:text:1999.01.0053',
            'work_name': 'Nicomachean Ethics',
            'author': 'Aristotle',
            'language': 'Greek',
            'sections': range(1, 11),  # Books I-X (will need book-chapter structure)
            'edition': 'I. Bywater, Oxford: Oxford University Press, 1894',
            'output': 'retrieved_texts/aristotle_nicomachean_ethics.json'
        },
        # Add more works as needed
    ]

    # Retrieve first work as demonstration
    work_config = retrieval_queue[0]
    work_data = retriever.retrieve_complete_work(
        work_id=work_config['work_id'],
        work_name=work_config['work_name'],
        author=work_config['author'],
        language=work_config['language'],
        section_range=work_config['sections'],
        edition=work_config['edition']
    )

    retriever.save_work(work_data, work_config['output'])


if __name__ == '__main__':
    main()
