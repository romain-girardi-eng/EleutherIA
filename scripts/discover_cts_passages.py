#!/usr/bin/env python3
"""
CTS Passage Discovery Tool
===========================
Uses CTS GetValidReff API to discover the actual passage structure for each work.

The CTS protocol provides a GetValidReff endpoint that returns all valid passage
references for a given URN. This lets us discover:
- What citation format the work uses (Book.Chapter, Bekker pages, simple sections)
- What passages are actually available
- The hierarchical structure

NO GUESSING - We query the actual CTS catalog.
"""

import requests
import re
import json
from pathlib import Path
from xml.etree import ElementTree as ET

class CTSPassageDiscoverer:
    """Discover available passages via CTS GetValidReff"""

    # Scaife uses a different API structure - let's try the CTS API directly
    CTS_API_BASE = "https://scaife-cts-api.perseus.org/api/cts"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research - Ancient Free Will Database'
        })

    def get_text_structure(self, urn_base: str) -> dict:
        """
        Try to discover text structure via CTS API

        Strategy:
        1. Try GetValidReff to get all passage references
        2. Try GetCapabilities to get citation scheme
        3. Manual exploration via common patterns
        """

        print(f"\n{'='*80}")
        print(f"DISCOVERING: {urn_base}")
        print(f"{'='*80}")

        result = {
            'urn_base': urn_base,
            'api_responses': {},
            'sample_passages': [],
            'inferred_format': None,
            'error': None
        }

        # Try CTS GetValidReff
        try:
            reff_url = f"{self.CTS_API_BASE}?request=GetValidReff&urn={urn_base}"
            print(f"\nTrying GetValidReff...")
            print(f"URL: {reff_url}")

            response = self.session.get(reff_url, timeout=15)
            result['api_responses']['GetValidReff'] = {
                'status': response.status_code,
                'url': reff_url,
                'content_sample': response.text[:500] if response.status_code == 200 else None
            }

            if response.status_code == 200:
                print(f"✓ Got response ({len(response.text)} chars)")
                # Try to parse XML
                try:
                    root = ET.fromstring(response.content)
                    result['api_responses']['GetValidReff']['xml_parsed'] = True
                    # Look for valid references
                    refs = root.findall('.//{http://chs.harvard.edu/xmlns/cts}urn')
                    if refs:
                        result['sample_passages'] = [ref.text for ref in refs[:10]]
                        print(f"✓ Found {len(refs)} valid references")
                        print(f"  Sample: {result['sample_passages'][:5]}")
                except Exception as e:
                    result['api_responses']['GetValidReff']['parse_error'] = str(e)
                    print(f"✗ XML parse error: {e}")
            else:
                print(f"✗ Status {response.status_code}")

        except Exception as e:
            result['error'] = str(e)
            print(f"✗ Request failed: {e}")

        # Try manual exploration - test common citation patterns
        print(f"\nTrying manual pattern exploration...")
        patterns = self._generate_test_patterns()

        for pattern in patterns[:10]:  # Test first 10 patterns
            test_urn = f"{urn_base}:{pattern}"
            try:
                # Try to fetch passage
                passage_url = f"https://scaife.perseus.org/library/{test_urn}/cts-api-xml/"
                response = self.session.get(passage_url, timeout=5)

                if response.status_code == 200 and len(response.text) > 500:
                    print(f"  ✓ {pattern:15s} - SUCCESS ({len(response.text):5d} chars)")
                    result['sample_passages'].append(pattern)
                    if len(result['sample_passages']) >= 5:
                        break
                else:
                    print(f"  ✗ {pattern:15s} - Failed")
            except Exception as e:
                print(f"  ✗ {pattern:15s} - Error: {str(e)[:30]}")

        # Infer format from successful patterns
        if result['sample_passages']:
            result['inferred_format'] = self._infer_format(result['sample_passages'])
            print(f"\n✓ Inferred format: {result['inferred_format']}")
        else:
            print(f"\n✗ Could not discover valid passages")

        return result

    def _generate_test_patterns(self):
        """Generate common citation patterns to test"""
        patterns = []

        # Simple numbers
        patterns.extend([str(i) for i in range(1, 11)])

        # Book.Chapter Roman numerals
        for book in ['1', '2', '3', 'I', 'II', 'III']:
            for chapter in ['1', '2', '3']:
                patterns.append(f"{book}.{chapter}")

        # Bekker pages (Aristotle)
        for page in range(1094, 1105):
            patterns.append(f"{page}a")
            patterns.append(f"{page}b")

        # Just book numbers
        patterns.extend(['preface', 'pr', 'proem'])

        return patterns

    def _infer_format(self, passages: list) -> str:
        """Infer citation format from successful passages"""

        if not passages:
            return "UNKNOWN"

        # Check patterns
        sample = passages[0]

        if re.match(r'^\d+$', sample):
            return "SIMPLE_SECTIONS"
        elif re.match(r'^\d{4}[ab]', sample):
            return "BEKKER_PAGES"
        elif re.match(r'^[IVX]+\.\d+', sample):
            return "BOOK_ROMAN.CHAPTER"
        elif re.match(r'^\d+\.\d+', sample):
            return "BOOK.CHAPTER"
        else:
            return f"CUSTOM: {sample}"

    def discover_multiple(self, urns: dict):
        """Discover passage structures for multiple works"""

        results = {}

        for name, urn in urns.items():
            result = self.get_text_structure(urn)
            results[name] = result

        # Save results
        output_file = 'cts_passage_discovery.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*80}")
        print(f"DISCOVERY COMPLETE")
        print(f"{'='*80}")
        print(f"✓ Saved to: {output_file}")

        # Summary
        print(f"\nSUMMARY:")
        for name, result in results.items():
            passages_found = len(result.get('sample_passages', []))
            fmt = result.get('inferred_format', 'UNKNOWN')
            print(f"  {name:40s} {passages_found:3d} passages | Format: {fmt}")

        return results


def main():
    """Discover passage formats for priority works"""

    print("="*80)
    print("CTS PASSAGE DISCOVERY TOOL")
    print("="*80)

    # Priority works from our gap analysis
    priority_urns = {
        'Aristotle, Nicomachean Ethics': 'urn:cts:greekLit:tlg0086.tlg010.perseus-grc1',
        'Aulus Gellius, Noctes Atticae': 'urn:cts:latinLit:phi1254.phi001.perseus-lat1',
        'Alexander of Aphrodisias, De Fato': 'urn:cts:greekLit:tlg0085.tlg014.perseus-grc1',
        'Epictetus, Discourses': 'urn:cts:greekLit:tlg0557.tlg001.perseus-grc1',
        'Plotinus, Enneads': 'urn:cts:greekLit:tlg0062.tlg001.perseus-grc1',
        'Aristotle, De Interpretatione': 'urn:cts:greekLit:tlg0086.tlg013.perseus-grc1',
        'Plutarch, De Stoicorum Repugnantiis': 'urn:cts:greekLit:tlg0007.tlg096.perseus-grc1',
    }

    discoverer = CTSPassageDiscoverer()
    results = discoverer.discover_multiple(priority_urns)

    print("\n✓ Discovery complete - check cts_passage_discovery.json for details")


if __name__ == '__main__':
    main()
