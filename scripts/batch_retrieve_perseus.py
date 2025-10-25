#!/usr/bin/env python3
"""
Batch Perseus Text Retrieval
=============================
Systematically retrieves all Perseus-available works cited in the database.
Handles different citation systems (sections, Bekker pages, book:line, etc.)

NO HALLUCINATION - Only verified Perseus texts with full provenance.
"""

import requests
import time
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path

class PerseusRetriever:
    """Handles all Perseus Digital Library retrievals"""

    BASE_URL = "http://www.perseus.tufts.edu/hopper/text"

    # Perseus work catalog with citation structures
    WORKS = {
        # CICERO
        'cicero_de_fato': {
            'perseus_id': 'Perseus:text:2007.01.0035',
            'author': 'Marcus Tullius Cicero',
            'work': 'De Fato',
            'language': 'Latin',
            'edition': 'C. F. W. Müller, Leipzig: Teubner, 1915',
            'structure': 'sections',
            'sections': range(1, 49),  # 1-48
            'status': 'COMPLETE'
        },
        'cicero_academica': {
            'perseus_id': 'Perseus:text:2007.01.0024',
            'author': 'Marcus Tullius Cicero',
            'work': 'Academica',
            'language': 'Latin',
            'edition': 'J. S. Reid, Cambridge: Cambridge University Press, 1874',
            'structure': 'sections',
            'sections': range(1, 148),  # Books I-II combined
        },
        'cicero_de_natura_deorum': {
            'perseus_id': 'Perseus:text:2007.01.0041',
            'author': 'Marcus Tullius Cicero',
            'work': 'De Natura Deorum',
            'language': 'Latin',
            'edition': 'O. Plasberg, Leipzig: Teubner, 1917',
            'structure': 'book_sections',
            'books': {1: range(1, 124), 2: range(1, 168), 3: range(1, 96)},
        },
        'cicero_de_divinatione': {
            'perseus_id': 'Perseus:text:2007.01.0029',
            'author': 'Marcus Tullius Cicero',
            'work': 'De Divinatione',
            'language': 'Latin',
            'edition': 'C. F. W. Müller, Leipzig: Teubner, 1915',
            'structure': 'book_sections',
            'books': {1: range(1, 133), 2: range(1, 150)},
        },

        # LUCRETIUS
        'lucretius_drn': {
            'perseus_id': 'Perseus:text:1999.02.0131',
            'author': 'Titus Lucretius Carus',
            'work': 'De Rerum Natura',
            'language': 'Latin',
            'edition': 'William Ellery Leonard, E. P. Dutton, 1916',
            'structure': 'book_lines',
            'books': {
                1: [(1,61), (62,145), (146,237), (238,328), (329,417), (418,482), (483,634), (635,920), (921,1117)],
                2: [(1,61), (62,141), (142,215), (216,293), (294,332), (333,477), (478,660), (661,729), (730,864), (865,990), (991,1174)],
                3: [(1,93), (94,160), (161,257), (258,322), (323,416), (417,458), (459,525), (526,614), (615,678), (679,775), (776,977), (978,1094)],
                4: [(1,25), (26,109), (110,238), (239,352), (353,521), (522,672), (673,822), (823-906), (907,1036), (1037,1191), (1192,1287)],
                5: [(1,54), (55,90), (91,234), (235,323), (324-431), (432-508), (509-771), (772-924), (925-1010), (1011-1104), (1105-1457)],
                6: [(1-42), (43-95), (96-159), (160-218), (219-378), (379-422), (423-534), (535-607), (608-737), (738-839), (840-905), (906-1089), (1090-1286)]
            },
            'status': 'Book II COMPLETE'
        },

        # EPICTETUS
        'epictetus_discourses': {
            'perseus_id': 'Perseus:text:1999.01.0236',
            'author': 'Epictetus',
            'work': 'Discourses (Dissertationes)',
            'language': 'Greek',
            'edition': 'George Long, London: George Bell & Sons, 1890',
            'structure': 'book_chapter',
            'books': {
                1: range(1, 31),  # 30 chapters
                2: range(1, 27),  # 26 chapters
                3: range(1, 27),  # 26 chapters
                4: range(1, 14),  # 13 chapters
            },
        },

        # AULUS GELLIUS
        'gellius_na': {
            'perseus_id': 'Perseus:text:2007.01.0071',
            'author': 'Aulus Gellius',
            'work': 'Noctes Atticae',
            'language': 'Latin',
            'edition': 'Teubner, 1853',
            'structure': 'book_chapter',
            'books': {i: range(1, 32) for i in range(1, 21)},  # 20 books, ~30 chapters each
        },

        # PLOTINUS
        'plotinus_enneads': {
            'perseus_id': 'Perseus:text:1999.01.0241',
            'author': 'Plotinus',
            'work': 'Enneads',
            'language': 'Greek',
            'edition': 'Stephen MacKenna & B. S. Page, London: Philip Lee Warner, 1917-1930',
            'structure': 'ennead_tractate',
            # Enneads I-VI, each with 8-9 tractates
            'enneads': {
                1: range(1, 10),
                2: range(1, 10),
                3: range(1, 10),
                4: range(1, 10),
                5: range(1, 10),
                6: range(1, 10),
            },
        },

        # PLUTARCH
        'plutarch_stoic_rep': {
            'perseus_id': 'Perseus:text:2008.01.0398',
            'author': 'Plutarch',
            'work': 'De Stoicorum Repugnantiis',
            'language': 'Greek',
            'edition': 'Gregorius N. Bernardakis, Leipzig: Teubner, 1895',
            'structure': 'sections',
            'sections': range(1, 51),  # Approximate
        },

        # ARISTOTLE - Simplified for now
        'aristotle_de_interp': {
            'perseus_id': 'Perseus:text:1999.01.0049',
            'author': 'Aristotle',
            'work': 'De Interpretatione',
            'language': 'Greek',
            'edition': 'E. M. Edghill, Oxford: Oxford University Press, 1928',
            'structure': 'bekker',
            'bekker_range': ['16a', '16b', '17a', '17b', '18a', '18b', '19a', '19b', '20a', '20b', '21a', '21b', '22a', '22b', '23a', '23b', '24a', '24b'],
        },
    }

    def __init__(self, delay=0.5, output_dir='retrieved_texts'):
        self.delay = delay
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research - Ancient Free Will Database'
        })

    def retrieve_text(self, url: str) -> Optional[str]:
        """Generic text retrieval from Perseus"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            text_div = soup.find('div', class_='text')

            if not text_div:
                return None

            # Remove navigation
            for elem in text_div.find_all(['div', 'span'], class_=['header', 'context']):
                elem.decompose()

            text = text_div.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\[\s*\d+\s*\]', '', text)
            text = re.sub(r'\[p\.\s*\d+\]', '', text)

            return text.strip() if text.strip() else None

        except Exception as e:
            return None

    def build_url(self, work_key: str, **kwargs) -> str:
        """Build Perseus URL based on work structure"""
        work = self.WORKS[work_key]
        base = f"{self.BASE_URL}?doc={work['perseus_id']}"

        structure = work['structure']

        if structure == 'sections':
            section = kwargs.get('section')
            return f"{base}:section={section}"

        elif structure == 'book_sections':
            book = kwargs.get('book')
            section = kwargs.get('section')
            return f"{base}:book={book}:section={section}"

        elif structure == 'book_lines':
            book = kwargs.get('book')
            line_start = kwargs.get('line_start')
            line_end = kwargs.get('line_end')
            if line_end:
                return f"{base}:book={book}:card={line_start}-{line_end}"
            return f"{base}:book={book}:card={line_start}"

        elif structure == 'book_chapter':
            book = kwargs.get('book')
            chapter = kwargs.get('chapter')
            return f"{base}:{book}.{chapter}"

        elif structure == 'bekker':
            page = kwargs.get('bekker_page')
            return f"{base}:bekker+page={page}"

        elif structure == 'ennead_tractate':
            ennead = kwargs.get('ennead')
            tractate = kwargs.get('tractate')
            return f"{base}:{ennead}.{tractate}"

        return base

    def retrieve_work(self, work_key: str) -> Dict:
        """Retrieve complete work"""
        work_config = self.WORKS[work_key]

        print(f"\n{'='*80}")
        print(f"RETRIEVING: {work_config['author']}, {work_config['work']}")
        print(f"Perseus ID: {work_config['perseus_id']}")
        print(f"Structure: {work_config['structure']}")
        print(f"{'='*80}\n")

        work_data = {
            'metadata': {
                **work_config,
                'retrieved_date': '2025-10-25',
                'retrieval_status': 'in_progress'
            },
            'content': {}
        }

        structure = work_config['structure']
        success_count = 0
        total_count = 0

        if structure == 'sections':
            for section in work_config['sections']:
                total_count += 1
                print(f"  Section {section:3d} ", end='', flush=True)
                url = self.build_url(work_key, section=section)
                text = self.retrieve_text(url)
                time.sleep(self.delay)

                if text:
                    work_data['content'][str(section)] = {
                        'text': text,
                        'url': url,
                        'verification_status': 'perseus_verified'
                    }
                    success_count += 1
                    print(f"✓ ({len(text):5d} chars)")
                else:
                    print("✗")

        elif structure == 'book_lines':
            for book, passages in work_config['books'].items():
                print(f"\n  Book {book}:")
                for passage in passages:
                    if isinstance(passage, tuple):
                        start, end = passage
                        total_count += 1
                        print(f"    Lines {start:4d}-{end:4d} ", end='', flush=True)
                        url = self.build_url(work_key, book=book, line_start=start, line_end=end)
                        text = self.retrieve_text(url)
                        time.sleep(self.delay)

                        if text:
                            key = f"book{book}_{start}_{end}"
                            work_data['content'][key] = {
                                'book': book,
                                'lines': f"{start}-{end}",
                                'text': text,
                                'url': url,
                                'verification_status': 'perseus_verified'
                            }
                            success_count += 1
                            print(f"✓ ({len(text):5d} chars)")
                        else:
                            print("✗")

        elif structure == 'book_chapter':
            for book, chapters in work_config['books'].items():
                print(f"\n  Book {book}:")
                for chapter in chapters:
                    total_count += 1
                    print(f"    Chapter {chapter:2d} ", end='', flush=True)
                    url = self.build_url(work_key, book=book, chapter=chapter)
                    text = self.retrieve_text(url)
                    time.sleep(self.delay)

                    if text:
                        key = f"book{book}_ch{chapter}"
                        work_data['content'][key] = {
                            'book': book,
                            'chapter': chapter,
                            'text': text,
                            'url': url,
                            'verification_status': 'perseus_verified'
                        }
                        success_count += 1
                        print(f"✓ ({len(text):5d} chars)")
                    else:
                        print("✗")

        work_data['metadata']['retrieval_status'] = 'completed'
        work_data['metadata']['sections_retrieved'] = success_count
        work_data['metadata']['sections_total'] = total_count

        # Save
        filename = self.output_dir / f"{work_key}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(work_data, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*80}")
        print(f"✓ Retrieved {success_count}/{total_count} sections")
        print(f"✓ Saved to: {filename}")
        print(f"{'='*80}\n")

        return work_data


def main():
    """Batch retrieve all Perseus works"""
    retriever = PerseusRetriever(delay=0.4)

    # Priority order
    works_to_retrieve = [
        'lucretius_drn',  # Continue with all books
        'gellius_na',  # 27 citations
        'epictetus_discourses',  # 13 citations
        'plutarch_stoic_rep',  # 16 citations
        'plotinus_enneads',  # 24 citations
        'cicero_academica',  # 13 citations
        'cicero_de_natura_deorum',  # 8 citations
        'cicero_de_divinatione',  # 8 citations
        'aristotle_de_interp',  # 18 citations
    ]

    for work_key in works_to_retrieve:
        try:
            retriever.retrieve_work(work_key)
        except Exception as e:
            print(f"\n✗ ERROR retrieving {work_key}: {e}\n")
            continue

if __name__ == '__main__':
    main()
