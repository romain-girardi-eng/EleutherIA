#!/usr/bin/env python3
"""
Fix the remaining 40 nodes with invalid periods
Mostly reformulation nodes marked "Ancient Greek" without dates
"""

import json
from datetime import datetime

# Manual mappings for remaining problematic nodes
REFORMULATION_PERIOD_MAP = {
    # Stoic reformulations
    'reformulation_chrysippus_reform_1f5d3806': 'Hellenistic Greek',
    'reformulation_cleanthes_stoic_reform_c576fe67': 'Hellenistic Greek',
    'reformulation_chrysippus_stoic_reform_ddff96ae': 'Hellenistic Greek',
    'reformulation_stoics_reform_f734ea75': 'Hellenistic Greek',
    'reformulation_cleanthes_reform_4128938b': 'Hellenistic Greek',

    # Epicurean reformulations
    'reformulation_epicureans_reform_9b771ca1': 'Hellenistic Greek',
    'reformulation_epicurus_reform_6fa6ecf5': 'Hellenistic Greek',
    'reformulation_lucretius_reform_d144b3da': 'Roman Republican',
    'reformulation_diogenes_of_oenoanda_reform_8fad58cc': 'Roman Imperial',

    # Academic Skeptic reformulations
    'reformulation_carneades_reform_e0c2db9c': 'Hellenistic Greek',
    'reformulation_philo_the_dialectician_reform_e7c46946': 'Hellenistic Greek',

    # Roman reformulations
    'reformulation_cicero_reform_156df2f5': 'Roman Republican',
    'reformulation_aulus_gellius_reform_01ef18e6': 'Roman Imperial',
    'reformulation_seneca_reform_2f1a5d99': 'Roman Imperial',

    # Commentator reformulations
    'reformulation_aspasius_reform_6afe87ac': 'Roman Imperial',
    'reformulation_aristotle_reform_bfee6d58': 'Classical Greek',

    # Presocratic reformulations
    'reformulation_melissus_of_samos_reform_e1359785': 'Presocratic',
    'reformulation_zeno_of_elea_reform_8d876b50': 'Presocratic',

    # Neoplatonist reformulations
    'reformulation_neoplatonists_plotinus_proclus_reform_98f42f33': 'Late Antiquity',
    'reformulation_plotinus_reform_b06e63cb': 'Late Antiquity',
    'reformulation_porphyry_reform_7c9edeb4': 'Late Antiquity',
    'reformulation_proclus_reform_59f4bb4f': 'Late Antiquity',

    # Patristic reformulations
    'reformulation_origen_reform_e1e2458e': 'Patristic',
    'reformulation_christian_church_fathers_reform_1fd435f1': 'Patristic',

    # Medieval reformulation
    'reformulation_medieval_scholastics_aquinas_reform_ad897818': 'High Medieval',
    'reformulation_thomas_aquinas_reform_24cffd94': 'High Medieval',

    # Marcus Aurelius reformulation
    'reformulation_marcus_aurelius_reform_d0f5561d': 'Roman Imperial',

    # Plutarch reformulation
    'reformulation_plutarch_reform_5724dac6': 'Roman Imperial',
}

PERSON_PERIOD_MAP = {
    # These are all Roman Imperial period figures
    'person_sextus_empiricus_c160_210ce_d4f8a2b1': 'Roman Imperial',  # c. 160-210 CE
    'person_plutarch_45_120ce_b9c2a8f3': 'Roman Imperial',  # 45-120 CE
    'person_alcinous_c150ce_a7b5c4d2': 'Roman Imperial',  # c. 150 CE
}

CONCEPT_PERIOD_MAP = {
    # Academic Skeptic concepts
    'concept_pithanotes_7v2w4y10': 'Hellenistic Greek',  # Carneades
    'concept_pithanon_8f3a6d2c': 'Hellenistic Greek',  # Carneades
    'concept_isostheneia_4b7e9c3a': 'Hellenistic Greek',  # Skeptic concept

    # Stoic concepts
    'concept_conditional_fate_9a5c8b4d': 'Hellenistic Greek',  # Stoic concept
}

ARGUMENT_PERIOD_MAP = {
    # Lazy Argument - Hellenistic period argument against Stoics
    'argument_the_lazy_argument_argos_logos_702a77ed': 'Hellenistic Greek',  # Before 3rd c. BCE = Hellenistic

    # Sextus Empiricus argument
    'argument_sextus_equipollence_argument_7d4b9e2a': 'Roman Imperial',

    # Plutarch argument
    'argument_plutarch_providence_cooperation_8c5a9d3f': 'Roman Imperial',
}

# Nodes that already have valid periods but different format
PERIOD_CLEANUP = {
    'concept_exousia_power_alexander_c87942af': 'Roman Imperial',  # "Roman Imperial (2nd-3rd c. CE)" → "Roman Imperial"
    'concept_epi_ison_in_equal_parts_9e1e47f1': 'Roman Imperial',  # "Roman Imperial (1st-3rd c. CE)" → "Roman Imperial"
}

def fix_remaining_periods():
    """Fix the remaining 40 nodes with invalid periods"""

    # Load database
    print("Loading database...")
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']

    # Combine all mappings
    all_mappings = {
        **REFORMULATION_PERIOD_MAP,
        **PERSON_PERIOD_MAP,
        **CONCEPT_PERIOD_MAP,
        **ARGUMENT_PERIOD_MAP,
        **PERIOD_CLEANUP
    }

    # Track changes
    changes = []
    not_found = []

    print(f"\nProcessing {len(nodes)} nodes...")
    print(f"Attempting to fix {len(all_mappings)} specific nodes...")

    for node in nodes:
        node_id = node['id']
        old_period = node.get('period', '')

        if node_id in all_mappings:
            new_period = all_mappings[node_id]
            if new_period != old_period:
                changes.append({
                    'id': node_id,
                    'label': node.get('label', 'N/A'),
                    'type': node.get('type', 'N/A'),
                    'old_period': old_period,
                    'new_period': new_period
                })
                node['period'] = new_period

    # Verify all mappings were found
    fixed_ids = {change['id'] for change in changes}
    for mapped_id in all_mappings:
        if mapped_id not in fixed_ids:
            not_found.append(mapped_id)

    # Print summary
    print("\n" + "=" * 80)
    print("REMAINING PERIOD FIXES")
    print("=" * 80)
    print(f"Nodes fixed: {len(changes)}")
    print(f"Mappings not found: {len(not_found)}")

    if changes:
        print("\n" + "=" * 80)
        print("CHANGES MADE")
        print("=" * 80)

        # Group by type
        by_type = {}
        for change in changes:
            node_type = change['type']
            if node_type not in by_type:
                by_type[node_type] = []
            by_type[node_type].append(change)

        for node_type in sorted(by_type.keys()):
            type_changes = by_type[node_type]
            print(f"\n{node_type.upper()} ({len(type_changes)} nodes)")
            print("-" * 80)

            for change in type_changes:
                print(f"  • {change['id']}")
                print(f"    '{change['old_period']}' → '{change['new_period']}'")

    if not_found:
        print("\n" + "=" * 80)
        print("WARNING: Mapped IDs not found in database")
        print("=" * 80)
        for node_id in not_found:
            print(f"  • {node_id}")

    # Save corrected database
    backup_filename = f"ancient_free_will_database_BACKUP_remaining_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n" + "=" * 80)
    print(f"Creating backup: {backup_filename}")
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"Saving corrected database...")
    with open('ancient_free_will_database.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print("\n✓ Remaining period fixes complete!")
    print(f"  Backup saved: {backup_filename}")
    print(f"  Changes made: {len(changes)}")

    return changes

if __name__ == '__main__':
    changes = fix_remaining_periods()
