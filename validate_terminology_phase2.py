#!/usr/bin/env python3
"""
Phase 2 Validation: Verify terminology coverage is appropriate for each concept
"""

import json

def validate_phase2():
    """Validate that terminology coverage is appropriate"""

    # Load database
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']
    concepts = [n for n in nodes if n.get('type') == 'concept']

    print("=" * 80)
    print("PHASE 2 VALIDATION REPORT")
    print("=" * 80)
    print(f"\nTotal concept nodes: {len(concepts)}")

    # Categorize by period
    ancient_greek_periods = {'Presocratic', 'Classical Greek', 'Hellenistic Greek', 'Roman Republican'}
    ancient_roman_periods = {'Roman Imperial', 'Patristic', 'Late Antiquity'}
    medieval_periods = {'Early Medieval', 'High Medieval', 'Late Medieval'}
    early_modern_periods = {'Renaissance', 'Reformation', 'Counter-Reformation',
                            'Early Modern Rationalism', 'Early Modern Empiricism', 'Enlightenment'}
    modern_periods = {'19th Century', '20th Century Analytic', '20th Century Continental', '21st Century'}
    jewish_periods = {'Second Temple Judaism', 'Rabbinic Judaism'}

    # Validation categories
    validation = {
        'ancient_greek_correct': [],  # Should have Greek+Latin
        'ancient_greek_missing': [],
        'patristic_correct': [],  # Should have Greek and/or Latin
        'patristic_missing': [],
        'medieval_correct': [],  # Should have Latin only
        'medieval_missing': [],
        'jewish_correct': [],  # Should have Hebrew
        'jewish_missing': [],
        'modern_correct': [],  # Should have English only (no Greek/Latin)
        'modern_unnecessary': [],  # Modern concepts with Greek/Latin (probably wrong)
    }

    for concept in concepts:
        period = concept.get('period')
        has_greek = bool(concept.get('greek_term'))
        has_latin = bool(concept.get('latin_term'))
        has_hebrew = bool(concept.get('hebrew_term'))

        # Ancient Greek concepts (should have Greek + Latin)
        if period in ancient_greek_periods:
            if has_greek and has_latin:
                validation['ancient_greek_correct'].append(concept)
            else:
                validation['ancient_greek_missing'].append(concept)

        # Ancient Roman/Patristic (should have Greek and/or Latin)
        elif period in ancient_roman_periods:
            if has_greek or has_latin:
                validation['patristic_correct'].append(concept)
            else:
                validation['patristic_missing'].append(concept)

        # Medieval (should have Latin)
        elif period in medieval_periods or period in early_modern_periods:
            if has_latin:
                validation['medieval_correct'].append(concept)
            else:
                validation['medieval_missing'].append(concept)

        # Jewish (should have Hebrew)
        elif period in jewish_periods:
            if has_hebrew:
                validation['jewish_correct'].append(concept)
            else:
                validation['jewish_missing'].append(concept)

        # Modern (should have English only - no Greek/Latin)
        elif period in modern_periods or period is None:
            if not has_greek and not has_latin:
                validation['modern_correct'].append(concept)
            else:
                validation['modern_unnecessary'].append(concept)

    # Print results
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS BY CATEGORY")
    print("=" * 80)

    print("\n--- ANCIENT GREEK CONCEPTS (need Greek + Latin) ---")
    print(f"✓ Correct: {len(validation['ancient_greek_correct'])}")
    print(f"✗ Missing terminology: {len(validation['ancient_greek_missing'])}")
    if validation['ancient_greek_missing']:
        for c in validation['ancient_greek_missing']:
            greek = "✓" if c.get('greek_term') else "✗"
            latin = "✓" if c.get('latin_term') else "✗"
            print(f"  [Greek:{greek} Latin:{latin}] {c['id']} - {c.get('label')}")

    print("\n--- PATRISTIC/ROMAN IMPERIAL (need Greek and/or Latin) ---")
    print(f"✓ Correct: {len(validation['patristic_correct'])}")
    print(f"✗ Missing terminology: {len(validation['patristic_missing'])}")
    if validation['patristic_missing']:
        for c in validation['patristic_missing']:
            print(f"  {c['id']} - {c.get('label')}")

    print("\n--- MEDIEVAL/EARLY MODERN (need Latin) ---")
    print(f"✓ Correct: {len(validation['medieval_correct'])}")
    print(f"✗ Missing Latin: {len(validation['medieval_missing'])}")
    if validation['medieval_missing']:
        for c in validation['medieval_missing']:
            print(f"  {c['id']} - {c.get('label')}")

    print("\n--- JEWISH CONCEPTS (need Hebrew) ---")
    print(f"✓ Correct: {len(validation['jewish_correct'])}")
    print(f"✗ Missing Hebrew: {len(validation['jewish_missing'])}")
    if validation['jewish_missing']:
        for c in validation['jewish_missing']:
            print(f"  {c['id']} - {c.get('label')}")

    print("\n--- MODERN CONCEPTS (English only - no ancient languages) ---")
    print(f"✓ Correct (English only): {len(validation['modern_correct'])}")
    print(f"⚠ Has unnecessary Greek/Latin: {len(validation['modern_unnecessary'])}")
    if validation['modern_unnecessary']:
        for c in validation['modern_unnecessary']:
            greek = "Greek" if c.get('greek_term') else ""
            latin = "Latin" if c.get('latin_term') else ""
            print(f"  {c['id']} has {greek} {latin}")

    # Overall statistics
    total_correct = (len(validation['ancient_greek_correct']) +
                    len(validation['patristic_correct']) +
                    len(validation['medieval_correct']) +
                    len(validation['jewish_correct']) +
                    len(validation['modern_correct']))

    total_missing = (len(validation['ancient_greek_missing']) +
                    len(validation['patristic_missing']) +
                    len(validation['medieval_missing']) +
                    len(validation['jewish_missing']))

    print("\n" + "=" * 80)
    print("OVERALL PHASE 2 RESULTS")
    print("=" * 80)
    print(f"Concepts with appropriate terminology: {total_correct}/{len(concepts)} ({total_correct/len(concepts)*100:.1f}%)")
    print(f"Concepts missing appropriate terminology: {total_missing}/{len(concepts)} ({total_missing/len(concepts)*100:.1f}%)")
    print(f"Modern concepts (correctly English-only): {len(validation['modern_correct'])}")

    # Quality score calculation
    print("\n" + "=" * 80)
    print("QUALITY SCORE ESTIMATION")
    print("=" * 80)

    # Phase 1 gave us 45/100 (period vocabulary)
    phase1_score = 45

    # Phase 2 contribution:
    # - Terminology coverage: 30 points max
    # - Current: {total_correct}/{len(concepts)} coverage = {total_correct/len(concepts)} * 30
    terminology_score = (total_correct / len(concepts)) * 30

    estimated_total = phase1_score + terminology_score

    print(f"Phase 1 (Period vocabulary):    {phase1_score}/100")
    print(f"Phase 2 (Terminology coverage): {terminology_score:.1f}/30")
    print(f"Estimated total score:          {estimated_total:.1f}/100")

    if estimated_total >= 65:
        print("\n✓ TARGET ACHIEVED: Quality score ≥ 65/100!")
    else:
        print(f"\n⚠ Need {65 - estimated_total:.1f} more points to reach target 65/100")

    return validation

if __name__ == '__main__':
    validate_phase2()
