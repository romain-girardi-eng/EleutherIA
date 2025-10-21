#!/usr/bin/env python3
"""
Comprehensive Period Vocabulary Correction Script
Fixes all 360 nodes with invalid period values using extended controlled vocabulary
"""

import json
import re
from datetime import datetime

# Extended controlled vocabulary
VALID_PERIODS = {
    # Ancient (core focus)
    "Presocratic",
    "Classical Greek",
    "Hellenistic Greek",
    "Roman Republican",
    "Roman Imperial",
    "Patristic",
    "Late Antiquity",
    # Medieval
    "Early Medieval",
    "High Medieval",
    "Late Medieval",
    # Early Modern
    "Renaissance",
    "Reformation",
    "Counter-Reformation",
    "Early Modern Rationalism",
    "Early Modern Empiricism",
    "Enlightenment",
    # Modern/Contemporary
    "19th Century",
    "20th Century Analytic",
    "20th Century Continental",
    "21st Century",
    # Special categories (use sparingly)
    "Second Temple Judaism",
    "Rabbinic Judaism"
}

# Direct mappings (simple cases)
DIRECT_MAPPINGS = {
    "Ancient Greek (Classical)": "Classical Greek",
    "Hellenistic": "Hellenistic Greek",
    "Early Christian": "Patristic",
    "Late Antique": "Late Antiquity",
    "Late Patristic": "Patristic",
    "Presocratic, Classical Greek": "Classical Greek",
    "Modern": "19th Century",
    # Special cases
    "Patristic (Late Antiquity)": "Late Antiquity",
    "Late Antiquity (Patristic)": "Late Antiquity",
    "Late Ancient (Early Christian Era)": "Late Antiquity",
    "Late Ancient": "Late Antiquity",
    "Late Antiquity (1st-6th century CE)": "Late Antiquity",
    "Patristic/Medieval transition": "Late Antiquity",
    # Biblical
    "Deuterocanonical/Apocrypha": "Second Temple Judaism",
    "Biblical": "Second Temple Judaism",
    "Biblical - Exodus": "Second Temple Judaism",
    "Biblical - Exilic": "Second Temple Judaism",
    "Biblical/Medieval Hebrew": "Rabbinic Judaism",
    "Biblical/Rabbinic Hebrew": "Second Temple Judaism",
    "Dead Sea Scrolls": "Second Temple Judaism",
    "Dead Sea Scrolls / Qumran": "Second Temple Judaism",
    "Hebrew Bible": "Second Temple Judaism",
    "Hebrew Bible - Prophetic": "Second Temple Judaism",
    "Hebrew Bible - Wisdom": "Second Temple Judaism",
    "Hellenistic Judaism": "Roman Imperial",  # Philo et al.
    "Second Temple Judaism / Rabbinic": "Second Temple Judaism",
    "Second Temple Judaism (modern scholarly category)": "Second Temple Judaism",
    "Rabbinic Judaism (post-70 CE; earlier roots)": "Rabbinic Judaism",
    # Presocratic
    "Classical Greek (Pre-Socratic)": "Presocratic",
    "Presocratic": "Presocratic",
    # Combined periods - choose primary
    "Ancient Greek/Hellenistic": "Hellenistic Greek",
    "Hellenistic/Roman": "Hellenistic Greek",
    "Hellenistic/Roman/Patristic": "Roman Imperial",
    "Hellenistic Greek, Roman": "Hellenistic Greek",
    "Hellenistic Greek, Roman Imperial": "Roman Imperial",
    "Ancient Greek/Roman": "Roman Imperial",
    "Roman Imperial (Late Antiquity)": "Late Antiquity",
    "Hellenistic, Roman Imperial, Patristic (4th BCE - 6th CE)": "Roman Imperial",
    # Medieval
    "Medieval (Early Scholasticism)": "Early Medieval",
    "Medieval (High Scholasticism)": "High Medieval",
    "Medieval (Late Scholasticism)": "Late Medieval",
    "Medieval (13th-14th c.)": "High Medieval",
    # Early Modern
    "Early Modern (17th century)": "Early Modern Rationalism",
    "Early Modern (17th-18th century)": "Early Modern Empiricism",
    "Early Modern (Counter-Reformation)": "Counter-Reformation",
    "Early Modern (Renaissance/Counter-Reformation)": "Counter-Reformation",
    "Renaissance/Reformation": "Renaissance",
    "Late Scholastic/Counter-Reformation": "Counter-Reformation",
    "Late Scholastic/Early Modern": "Counter-Reformation",
    "Scholastic/Early Modern": "Early Modern Rationalism",
    "Counter-Reformation": "Counter-Reformation",
    "Medieval (Islamic), Early Modern (Cartesian)": "Early Modern Rationalism",
    # Contemporary
    "Contemporary (20th-21st c.)": "20th Century Analytic",
    "Early Modern/Contemporary": "20th Century Analytic",
    # Transhistorical (keep as-is or map to most relevant period)
    "Transhistorical (Ancient-Contemporary)": "Classical Greek",  # Concepts that span all periods - use origin
    "Ancient-Medieval": "Classical Greek",
    "Patristic-Contemporary": "Patristic",
}

# Date-based mappings for "Ancient Greek", "Medieval", "Early Modern", "Contemporary"
DATE_PATTERNS = {
    # BCE patterns
    r'(?:c\.\s*)?(\d+)\s*-\s*(\d+)\s*BCE': 'bce_range',
    r'(?:c\.\s*)?(\d+)\s*BCE': 'bce_single',
    r'(\d+)th\s+c\.\s+BCE': 'bce_century',
    # CE patterns
    r'(?:c\.\s*)?(\d+)\s*-\s*(\d+)\s*CE': 'ce_range',
    r'(?:c\.\s*)?(\d+)\s*CE': 'ce_single',
    r'(\d+)th\s+c(?:entury)?\s+CE': 'ce_century',
    # Modern dates
    r'(\d{4})\s*-\s*(\d{4})': 'modern_range',
    r'(\d{4})': 'modern_single',
}

def extract_date_number(date_str):
    """Extract the primary date from a date string"""
    if not date_str or date_str == 'N/A':
        return None

    # Try each pattern
    for pattern, pattern_type in DATE_PATTERNS.items():
        match = re.search(pattern, date_str)
        if match:
            if pattern_type == 'bce_range':
                return -int(match.group(1))  # Use start date, negative for BCE
            elif pattern_type == 'bce_single':
                return -int(match.group(1))
            elif pattern_type == 'bce_century':
                century = int(match.group(1))
                return -(century * 100 - 50)  # Middle of century
            elif pattern_type == 'ce_range':
                return int(match.group(1))  # Use start date
            elif pattern_type == 'ce_single':
                return int(match.group(1))
            elif pattern_type == 'ce_century':
                century = int(match.group(1))
                return century * 100 - 50  # Middle of century
            elif pattern_type == 'modern_range':
                return int(match.group(1))  # Use start year
            elif pattern_type == 'modern_single':
                return int(match.group(1))

    return None

def map_by_date(date_num):
    """Map a date number to correct period"""
    if date_num is None:
        return None

    # BCE dates (negative)
    if date_num < -400:
        return "Presocratic"
    elif -400 <= date_num < -323:
        return "Classical Greek"
    elif -323 <= date_num < -31:
        return "Hellenistic Greek"
    elif -200 <= date_num < -27:
        return "Roman Republican"
    # CE dates
    elif -27 <= date_num < 284:
        return "Roman Imperial"
    elif 100 <= date_num < 450:
        return "Patristic"
    elif 300 <= date_num < 600:
        return "Late Antiquity"
    elif 600 <= date_num < 1050:
        return "Early Medieval"
    elif 1050 <= date_num < 1300:
        return "High Medieval"
    elif 1300 <= date_num < 1500:
        return "Late Medieval"
    elif 1400 <= date_num < 1600:
        return "Renaissance"
    elif 1517 <= date_num < 1648:
        return "Reformation"
    elif 1545 <= date_num < 1700:
        return "Counter-Reformation"
    elif 1600 <= date_num < 1750:
        return "Early Modern Rationalism"
    elif 1650 <= date_num < 1800:
        return "Early Modern Empiricism"
    elif 1700 <= date_num < 1800:
        return "Enlightenment"
    elif 1800 <= date_num < 1900:
        return "19th Century"
    elif 1900 <= date_num < 2000:
        return "20th Century Analytic"  # Default to analytic
    elif date_num >= 2000:
        return "21st Century"

    return None

def determine_period(node):
    """Determine correct period for a node"""
    current_period = node.get('period', '')
    date_str = node.get('date', 'N/A')
    node_id = node.get('id', '')
    label = node.get('label', '')

    # First try direct mapping
    if current_period in DIRECT_MAPPINGS:
        return DIRECT_MAPPINGS[current_period]

    # For "Ancient Greek", "Medieval", "Early Modern", "Contemporary" - use dates
    if current_period in ["Ancient Greek", "Medieval", "Early Modern", "Contemporary", "Enlightenment", "Reformation"]:
        date_num = extract_date_number(date_str)
        if date_num is not None:
            mapped = map_by_date(date_num)
            if mapped:
                return mapped

        # Fallback for specific periods without dates
        if current_period == "Medieval":
            # Default to High Medieval unless context suggests otherwise
            if 'scotus' in node_id or 'ockham' in node_id or 'buridan' in node_id:
                return "Late Medieval"
            elif 'aquinas' in node_id or 'bonaventure' in node_id:
                return "High Medieval"
            elif 'anselm' in node_id:
                return "Early Medieval"
            return "High Medieval"  # Default

        elif current_period == "Early Modern":
            # Determine based on keywords
            if any(x in node_id.lower() for x in ['molina', 'suarez', 'jansen', 'baňez']):
                return "Counter-Reformation"
            elif any(x in node_id.lower() for x in ['descartes', 'spinoza', 'leibniz', 'malebranche']):
                return "Early Modern Rationalism"
            elif any(x in node_id.lower() for x in ['hobbes', 'locke', 'hume', 'berkeley', 'reid', 'cudworth']):
                return "Early Modern Empiricism"
            return "Early Modern Rationalism"  # Default

        elif current_period == "Contemporary":
            # Check if continental or analytic
            if any(x in label.lower() or x in node_id.lower() for x in ['sartre', 'camus', 'heidegger', 'merleau']):
                return "20th Century Continental"
            return "20th Century Analytic"

        elif current_period == "Enlightenment":
            return "Enlightenment"

        elif current_period == "Reformation":
            return "Reformation"

    # If we get here and period is already valid, keep it
    if current_period in VALID_PERIODS:
        return current_period

    # Last resort - return original and log warning
    return current_period

def fix_periods():
    """Main function to fix all period values"""

    # Load database
    print("Loading database...")
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']

    # Track changes
    changes = []
    invalid_remaining = []

    print(f"\nProcessing {len(nodes)} nodes...")

    for node in nodes:
        old_period = node.get('period')
        if not old_period:
            continue

        # Skip if already valid
        if old_period in VALID_PERIODS:
            continue

        new_period = determine_period(node)

        if new_period != old_period:
            changes.append({
                'id': node['id'],
                'label': node.get('label', 'N/A'),
                'date': node.get('date', 'N/A'),
                'old_period': old_period,
                'new_period': new_period
            })
            node['period'] = new_period

        # Check if still invalid
        if new_period not in VALID_PERIODS:
            invalid_remaining.append({
                'id': node['id'],
                'label': node.get('label', 'N/A'),
                'date': node.get('date', 'N/A'),
                'period': new_period
            })

    # Print summary
    print("\n" + "=" * 80)
    print("PERIOD CORRECTION SUMMARY")
    print("=" * 80)
    print(f"Total changes made: {len(changes)}")
    print(f"Invalid periods remaining: {len(invalid_remaining)}")

    # Print changes by old period
    if changes:
        print("\n" + "=" * 80)
        print("CHANGES BY OLD PERIOD")
        print("=" * 80)

        changes_by_old = {}
        for change in changes:
            old = change['old_period']
            if old not in changes_by_old:
                changes_by_old[old] = []
            changes_by_old[old].append(change)

        for old_period in sorted(changes_by_old.keys()):
            period_changes = changes_by_old[old_period]
            print(f"\n'{old_period}' ({len(period_changes)} nodes)")
            print("-" * 80)

            # Group by new period
            by_new = {}
            for change in period_changes:
                new = change['new_period']
                if new not in by_new:
                    by_new[new] = []
                by_new[new].append(change)

            for new_period, items in sorted(by_new.items()):
                print(f"  → '{new_period}': {len(items)} nodes")
                for item in items[:5]:  # Show first 5 examples
                    print(f"      • {item['id']} ({item['date']})")
                if len(items) > 5:
                    print(f"      ... and {len(items) - 5} more")

    # Print remaining invalid
    if invalid_remaining:
        print("\n" + "=" * 80)
        print("INVALID PERIODS REMAINING (need manual review)")
        print("=" * 80)
        for item in invalid_remaining:
            print(f"  • {item['id']}")
            print(f"    Period: {item['period']}, Date: {item['date']}")

    # Save corrected database
    backup_filename = f"ancient_free_will_database_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n" + "=" * 80)
    print(f"Creating backup: {backup_filename}")
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"Saving corrected database...")
    with open('ancient_free_will_database.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print("\n✓ Period corrections complete!")
    print(f"  Backup saved: {backup_filename}")
    print(f"  Changes made: {len(changes)}")
    print(f"  Invalid remaining: {len(invalid_remaining)}")

    return changes, invalid_remaining

if __name__ == '__main__':
    changes, invalid = fix_periods()
