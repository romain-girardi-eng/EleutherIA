#!/usr/bin/env python3
"""
Fix the final 7 concepts missing appropriate terminology
"""

import json
from datetime import datetime

FINAL_FIXES = {
    # Meta-concepts (these are ABOUT terminology/debate structure - no specific term needed)
    'concept_terminology_evolution_greek_latin_y5z6a7b8': {
        'note': 'Meta-linguistic concept - correctly has no specific Greek/Latin term'
    },
    'concept_ancient_free_will_debate_structure_z6a7b8c9': {
        'note': 'Meta-philosophical concept - correctly has no specific Greek/Latin term'
    },

    # Kasb - Arabic Islamic concept
    'concept_kasb_acquisition_e9f0g1h2': {
        'arabic_term': 'كسب (kasb) / اكتساب (iktisāb)',
        'note': 'Arabic concept - already has arabic_term field'
    },

    # Kant's concepts - German philosophical terms
    'concept_transcendental_freedom_7i1d2e80': {
        'german_term': 'transzendentale Freiheit',
        'latin_term': 'libertas transcendentalis',
        'note': 'Kantian concept - German primary, Latin secondary'
    },
    'concept_autonomy_8j2e3f91': {
        'german_term': 'Autonomie',
        'greek_term': 'αὐτονομία (autonomia)',
        'latin_term': 'autonomia',
        'note': 'Kantian concept from Greek αὐτονομία (self-law)'
    },
    'concept_categorical_imperative_9k3f4g02': {
        'german_term': 'kategorischer Imperativ',
        'latin_term': 'imperativus categoricus',
        'note': 'Kantian concept - German primary, Latin philosophical term'
    },

    # Covenant Nomism - modern scholarly term (E.P. Sanders)
    'concept_covenant_nomism_k9l0m1n2': {
        'note': 'Modern scholarly term (E.P. Sanders, 1977) - English only is correct'
    },
}

def fix_final_concepts():
    """Fix the final 7 concepts"""

    # Load database
    print("Loading database...")
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']

    print("\n" + "=" * 80)
    print("FIXING FINAL 7 CONCEPTS")
    print("=" * 80)

    fixed = 0
    for node in nodes:
        node_id = node.get('id')
        if node_id in FINAL_FIXES:
            updates = FINAL_FIXES[node_id]
            print(f"\n{node_id}")
            print(f"  Label: {node.get('label')}")

            if 'german_term' in updates:
                node['german_term'] = updates['german_term']
                print(f"  ✓ Added German: {updates['german_term']}")

            if 'greek_term' in updates:
                node['greek_term'] = updates['greek_term']
                print(f"  ✓ Added Greek: {updates['greek_term']}")

            if 'latin_term' in updates:
                node['latin_term'] = updates['latin_term']
                print(f"  ✓ Added Latin: {updates['latin_term']}")

            if 'arabic_term' in updates and 'arabic_term' not in node:
                node['arabic_term'] = updates['arabic_term']
                print(f"  ✓ Added Arabic: {updates['arabic_term']}")

            if 'note' in updates:
                print(f"  Note: {updates['note']}")

            fixed += 1

    print("\n" + "=" * 80)
    print(f"Fixed {fixed} concepts")

    # Create backup
    backup_filename = f"ancient_free_will_database_BACKUP_final7_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\nCreating backup: {backup_filename}")
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    # Save
    print(f"Saving updated database...")
    with open('ancient_free_will_database.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print("\n✓ All fixes complete!")
    print(f"  Backup saved: {backup_filename}")

    return fixed

if __name__ == '__main__':
    fix_final_concepts()
