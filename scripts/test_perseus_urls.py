#!/usr/bin/env python3
"""
Perseus URL Pattern Tester
===========================
Tests different URL patterns to discover which works are available in Old Perseus
and what their citation format is.

NO HALLUCINATION - Only tests actual availability.
"""

import requests
import time
from typing import Optional

class PerseusURLTester:
    """Test Perseus URL patterns"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research - Ancient Free Will Database'
        })

    def test_url_patterns(self, work_name: str, author: str, patterns: list):
        """Test multiple URL patterns for a work"""

        print(f"\n{'='*80}")
        print(f"TESTING: {author}, {work_name}")
        print(f"{'='*80}")

        results = {
            'work': work_name,
            'author': author,
            'working_patterns': [],
            'failed_patterns': []
        }

        for i, pattern_info in enumerate(patterns, 1):
            base_url = pattern_info['base_url']
            test_ref = pattern_info['test_ref']
            full_url = f"{base_url}{test_ref}"

            print(f"\n{i}. Testing: {pattern_info['name']}")
            print(f"   URL: {full_url}")

            try:
                response = self.session.get(full_url, timeout=10)
                time.sleep(0.3)  # Be polite

                # Check if we got actual content
                if response.status_code == 200:
                    # Look for text content indicators
                    content_lower = response.text.lower()

                    if ('no files found' in content_lower or
                        'not found' in content_lower or
                        'error' in content_lower or
                        len(response.text) < 500):
                        print(f"   ✗ FAILED - No content or error page")
                        results['failed_patterns'].append(pattern_info)
                    else:
                        print(f"   ✓ SUCCESS - Got {len(response.text)} chars")
                        results['working_patterns'].append({
                            **pattern_info,
                            'test_url': full_url,
                            'content_length': len(response.text)
                        })
                else:
                    print(f"   ✗ HTTP {response.status_code}")
                    results['failed_patterns'].append(pattern_info)

            except Exception as e:
                print(f"   ✗ ERROR: {str(e)[:60]}")
                results['failed_patterns'].append(pattern_info)

        return results


def main():
    """Test Perseus URL patterns for priority works"""

    tester = PerseusURLTester()

    print("="*80)
    print("PERSEUS URL PATTERN TESTER")
    print("="*80)

    # Test cases for high-priority works
    test_works = [
        {
            'name': 'Nicomachean Ethics',
            'author': 'Aristotle',
            'patterns': [
                {
                    'name': 'Old Perseus - Book number',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0053:book=',
                    'test_ref': '3'  # Book III where our citations are
                },
                {
                    'name': 'Old Perseus - Bekker page',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0053:bekker%20page=',
                    'test_ref': '1109b'
                },
                {
                    'name': 'Old Perseus - Section',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0053:section=',
                    'test_ref': '1'
                }
            ]
        },
        {
            'name': 'Noctes Atticae',
            'author': 'Aulus Gellius',
            'patterns': [
                {
                    'name': 'Old Perseus - Book.Chapter',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2007.01.0072:book=',
                    'test_ref': '7:chapter=2'
                },
                {
                    'name': 'Old Perseus - Book only',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2007.01.0072:book=',
                    'test_ref': '7'
                }
            ]
        },
        {
            'name': 'De Fato',
            'author': 'Alexander of Aphrodisias',
            'patterns': [
                {
                    'name': 'Old Perseus - Chapter',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2008.01.0458:chapter=',
                    'test_ref': '1'
                },
                {
                    'name': 'Old Perseus - Section',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2008.01.0458:section=',
                    'test_ref': '1'
                }
            ]
        },
        {
            'name': 'Discourses',
            'author': 'Epictetus',
            'patterns': [
                {
                    'name': 'Old Perseus - Book.Chapter',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0236:book=',
                    'test_ref': '1:chapter=1'
                },
                {
                    'name': 'Old Perseus - Text reference',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0236:text=',
                    'test_ref': 'Diss.%201.1'
                }
            ]
        },
        {
            'name': 'Enneads',
            'author': 'Plotinus',
            'patterns': [
                {
                    'name': 'Old Perseus - Ennead.Tractate',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0241:tractate=',
                    'test_ref': '1'
                },
                {
                    'name': 'Old Perseus - Text reference',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0241:text=',
                    'test_ref': '3.1'
                }
            ]
        },
        {
            'name': 'Academica',
            'author': 'Cicero',
            'patterns': [
                {
                    'name': 'Old Perseus - Section',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2007.01.0030:section=',
                    'test_ref': '1'
                },
                {
                    'name': 'Old Perseus - Book.Section',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2007.01.0030:book=',
                    'test_ref': '1:section=1'
                }
            ]
        },
        {
            'name': 'De Stoicorum Repugnantiis',
            'author': 'Plutarch',
            'patterns': [
                {
                    'name': 'Old Perseus - Section',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2008.01.0397:section=',
                    'test_ref': '1'
                },
                {
                    'name': 'Old Perseus - Chapter',
                    'base_url': 'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2008.01.0397:chapter=',
                    'test_ref': '1'
                }
            ]
        }
    ]

    all_results = []

    for work_info in test_works:
        result = tester.test_url_patterns(
            work_info['name'],
            work_info['author'],
            work_info['patterns']
        )
        all_results.append(result)

        # Summary
        print(f"\n{'─'*80}")
        if result['working_patterns']:
            print(f"✓ FOUND WORKING PATTERN(S):")
            for pattern in result['working_patterns']:
                print(f"  - {pattern['name']}: {pattern['test_url'][:80]}...")
        else:
            print(f"✗ NO WORKING PATTERNS FOUND")

    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")

    for result in all_results:
        status = "✓" if result['working_patterns'] else "✗"
        count = len(result['working_patterns'])
        print(f"{status} {result['author']}, {result['work']:40s} {count} working pattern(s)")

    print("\n✓ Pattern testing complete")


if __name__ == '__main__':
    main()
