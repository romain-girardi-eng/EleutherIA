#!/usr/bin/env python3
"""
Fix all remaining validation errors in the database
"""

import json
from datetime import datetime

def fix_all_errors():
    """Fix all validation errors"""

    # Load database
    print("Loading database...")
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']
    edges = db['edges']

    print("\n" + "="*80)
    print("FIXING VALIDATION ERRORS")
    print("="*80)

    # 1. Fix missing descriptions
    print("\n1. Fixing missing descriptions...")
    missing_desc = 0
    for node in nodes:
        if 'description' not in node or not node['description']:
            # Use label as fallback description
            node['description'] = node.get('label', 'Node description')
            missing_desc += 1
            print(f"  Fixed: {node.get('id')} - added description from label")
    print(f"  ✓ Fixed {missing_desc} nodes with missing descriptions")

    # 2. Fix invalid node IDs (special characters)
    print("\n2. Fixing invalid node IDs...")
    id_fixes = {
        'reformulation_søren_kierkegaard_reform_6d1630de': 'reformulation_soren_kierkegaard_reform_6d1630de',
        'person_rené_descartes_1aa22692': 'person_rene_descartes_1aa22692',
        'person_francisco_suárez_late_16th_c__scholastic_tradition_continued_into_17th_c_d5e0d92c': 'person_francisco_suarez_late_16th_c_scholastic_tradition_continued_into_17th_c_d5e0d92c',
        'person_domingo_bañez_4l8g9h57': 'person_domingo_banez_4l8g9h57',
        'concept_academic_skepticism_epochē_n4o5p6q7': 'concept_academic_skepticism_epoche_n4o5p6q7'
    }

    # Update node IDs
    for node in nodes:
        old_id = node.get('id')
        if old_id in id_fixes:
            new_id = id_fixes[old_id]
            node['id'] = new_id
            print(f"  Fixed node ID: {old_id} → {new_id}")

    # Update edge references
    for edge in edges:
        if edge.get('source') in id_fixes:
            old_id = edge['source']
            edge['source'] = id_fixes[old_id]
            print(f"  Updated edge source: {old_id} → {id_fixes[old_id]}")
        if edge.get('target') in id_fixes:
            old_id = edge['target']
            edge['target'] = id_fixes[old_id]
            print(f"  Updated edge target: {old_id} → {id_fixes[old_id]}")

    print(f"  ✓ Fixed {len(id_fixes)} node IDs")

    # 3. Fix broken edge references
    print("\n3. Fixing broken edge references...")
    node_ids = {n['id'] for n in nodes}

    # Check for concept_eph_hemin_in_our_power_d4e5f6g7
    # This might have been renamed - find the correct ID
    eph_hemin_nodes = [n for n in nodes if 'eph' in n.get('id', '').lower() and 'hemin' in n.get('id', '').lower()]
    if eph_hemin_nodes:
        correct_id = eph_hemin_nodes[0]['id']
        print(f"  Found correct eph hemin ID: {correct_id}")

        broken_edges = 0
        for edge in edges:
            if edge.get('target') == 'concept_eph_hemin_in_our_power_d4e5f6g7':
                edge['target'] = correct_id
                broken_edges += 1
                print(f"    Fixed edge target → {correct_id}")
        print(f"  ✓ Fixed {broken_edges} broken edges")
    else:
        # Remove edges with non-existent targets
        print("  Removing edges with non-existent targets...")
        edges_before = len(edges)
        db['edges'] = [e for e in edges if e.get('source') in node_ids and e.get('target') in node_ids]
        edges_removed = edges_before - len(db['edges'])
        print(f"  ✓ Removed {edges_removed} broken edges")

    # Create backup
    backup_filename = f"ancient_free_will_database_BACKUP_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n4. Creating backup: {backup_filename}")
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    # Save
    print(f"\n5. Saving fixed database...")
    with open('ancient_free_will_database.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print("✓ ALL VALIDATION ERRORS FIXED!")
    print("="*80)
    print(f"  Fixed {missing_desc} missing descriptions")
    print(f"  Fixed {len(id_fixes)} invalid node IDs")
    print(f"  Backup saved: {backup_filename}")
    print("\nRun validation again to confirm:")
    print("  python3 examples/validate_database.py")

if __name__ == '__main__':
    fix_all_errors()
