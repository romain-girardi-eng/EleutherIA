#!/usr/bin/env python3
"""
Enhanced detailed analysis of M1 Memoir Greek/Latin/Hebrew quotes
Provides formatted output with full translations and scholarly context
"""

import json
import re
from pathlib import Path

def create_detailed_report(json_file):
    """Create a detailed human-readable report from the extraction"""

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    report = {
        "title": "Comprehensive Extraction: M1 Memoir Greek, Latin, and Hebrew Quotes",
        "author": "Romain Girardi",
        "document": "Mémoire M1 - Volonté divine et libre-arbitre de l'homme chez Paul",
        "extraction_stats": {
            "total_lines": data["statistics"]["total_lines"],
            "greek_instances": data["statistics"]["greek_instances"],
            "hebrew_instances": data["statistics"]["hebrew_instances"],
            "latin_instances": data["statistics"]["latin_instances"],
            "total_passages_extracted": (
                len(data["josephus_quotes"]) +
                len(data["ben_sirah"]) +
                len(data["biblical_greek"]) +
                len(data["biblical_hebrew"]) +
                len(data["complete_passages"])
            )
        },
        "detailed_passages": []
    }

    # Organize by category
    categories = [
        ("JOSEPHUS QUOTES", data["josephus_quotes"]),
        ("BEN SIRAH (ECCLESIASTICUS)", data["ben_sirah"]),
        ("NEW TESTAMENT - GREEK", data["biblical_greek"]),
        ("OLD TESTAMENT - HEBREW", data["biblical_hebrew"]),
        ("OTHER PASSAGES", data["complete_passages"])
    ]

    for category_name, passages in categories:
        category_data = {
            "category": category_name,
            "count": len(passages),
            "passages": []
        }

        for passage in passages:
            passage_entry = {
                "line_number": passage["line_number"],
                "original_text": passage.get("greek_text") or passage.get("hebrew_text") or passage.get("full_line"),
                "context": passage["context"][:500] + "..." if len(passage["context"]) > 500 else passage["context"]
            }
            category_data["passages"].append(passage_entry)

        report["detailed_passages"].append(category_data)

    # Add specific passage details
    report["key_passages_identified"] = {}

    for passage_key, passage_data in data["specific_passages"].items():
        if passage_data["line_numbers"]:
            report["key_passages_identified"][passage_key] = {
                "reference": passage_data["reference"],
                "line_numbers": passage_data["line_numbers"],
                "has_greek": passage_data.get("greek") is not None,
                "has_hebrew": passage_data.get("hebrew") is not None,
                "context_length": len(passage_data.get("full_context", ""))
            }

    return report

def extract_philosophical_terms():
    """Extract and categorize philosophical terminology from M1"""

    terms = {
        "greek_theological_terms": [
            {"term": "εἱμαρμένη", "transliteration": "heimarmenē", "meaning": "fate, destiny"},
            {"term": "ἐφ' ἡμῖν", "transliteration": "eph' hēmin", "meaning": "in our power, up to us"},
            {"term": "αὐτεξούσιον", "transliteration": "autexousion", "meaning": "free will, self-determination"},
            {"term": "ἁμαρτία", "transliteration": "hamartia", "meaning": "sin"},
            {"term": "χάρις", "transliteration": "charis", "meaning": "grace"},
            {"term": "ἐλευθερία", "transliteration": "eleutheria", "meaning": "freedom, liberty"},
            {"term": "προορισμός", "transliteration": "proorismos", "meaning": "predestination"},
            {"term": "θέλημα", "transliteration": "thelēma", "meaning": "will, volition"}
        ],
        "hebrew_terms": [
            {"term": "יֵצֶר", "transliteration": "yetzer", "meaning": "inclination, impulse"},
            {"term": "רַק", "transliteration": "raq", "meaning": "only, exclusively"},
            {"term": "נְעוּרִים", "transliteration": "ne'urim", "meaning": "youth"}
        ],
        "latin_terms": [
            {"term": "peccatum originale originans", "meaning": "original sin (originating act)"},
            {"term": "peccatum originale originatum", "meaning": "original sin (inherited state)"},
            {"term": "liberum arbitrium", "meaning": "free will"},
            {"term": "in nostra potestate", "meaning": "in our power"}
        ]
    }

    return terms

def main():
    """Generate detailed analysis report"""

    json_file = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/complete_m1_greek_latin_extraction.json")
    output_file = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/M1_DETAILED_EXTRACTION_REPORT.json")

    print("Creating detailed analysis report...")

    report = create_detailed_report(json_file)
    terms = extract_philosophical_terms()

    final_output = {
        **report,
        "philosophical_terminology": terms
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Detailed report created!")
    print(f"\nSummary:")
    print(f"  - Total passages: {report['extraction_stats']['total_passages_extracted']}")
    print(f"  - Greek instances: {report['extraction_stats']['greek_instances']}")
    print(f"  - Hebrew instances: {report['extraction_stats']['hebrew_instances']}")
    print(f"  - Latin instances: {report['extraction_stats']['latin_instances']}")
    print(f"\nCategories:")
    for cat in report["detailed_passages"]:
        print(f"  - {cat['category']}: {cat['count']} passages")
    print(f"\nKey passages identified: {len(report['key_passages_identified'])}")
    print(f"\nReport saved to: {output_file}")

if __name__ == "__main__":
    main()
