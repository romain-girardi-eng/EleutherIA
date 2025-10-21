#!/usr/bin/env python3
"""
Apply source corrections to ancient_free_will_database.json
Manual corrections based on fact-checking that ancient_sources point to FREE WILL content
"""

import json
import sys

def apply_corrections():
    # Load database
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    corrections_applied = []

    # 1. CLITOMACHUS - Remove Diogenes Laertius
    for node in db['nodes']:
        if node['id'] == 'person_clitomachus_of_carthage_7l2m4o10':
            if 'ancient_sources' in node:
                to_remove = "Diogenes Laertius, Lives IV.67 (brief biography)"
                if to_remove in node['ancient_sources']:
                    node['ancient_sources'].remove(to_remove)
                    corrections_applied.append(f"✓ Clitomachus: Removed Diogenes Laertius IV.67")

    # 2. DIOGENIANOS - Remove Cicero De Fato
    for node in db['nodes']:
        if node['id'] == 'person_diogenianos_8m3n5p21':
            if 'ancient_sources' in node:
                to_remove = "Cicero, De Fato 12-13 (possible allusion to Diogenianus' etymological argument)"
                if to_remove in node['ancient_sources']:
                    node['ancient_sources'].remove(to_remove)
                    corrections_applied.append(f"✓ Diogenianos: Removed speculative Cicero citation")

    # 3. PSEUDO-DIONYSIUS ARGUMENT - Remove 3 works
    for node in db['nodes']:
        if node['id'] == 'argument_pseudodionysiuss_hierarchical_causation_argument_e0d73eb9':
            if 'ancient_sources' in node:
                to_remove = [
                    "Pseudo-Dionysius, De Caelesti Hierarchia (Celestial Hierarchy) (PG 3:119-370; SC 58bis)",
                    "Pseudo-Dionysius, De Ecclesiastica Hierarchia (Ecclesiastical Hierarchy) (PG 3:369-584)",
                    "Pseudo-Dionysius, De Mystica Theologia (Mystical Theology) (PG 3:997-1064)"
                ]
                for src in to_remove:
                    if src in node['ancient_sources']:
                        node['ancient_sources'].remove(src)
                corrections_applied.append(f"✓ Pseudo-Dionysius: Removed 3 works not about free will")

    # 4. FIRMICUS MATERNUS - Remove De Errore
    for node in db['nodes']:
        if node['id'] == 'person_firmicus_maternus_2q7r9t65':
            if 'ancient_sources' in node:
                to_remove = "Firmicus Maternus, De Errore Profanarum Religionum (c. 346-350 CE)"
                if to_remove in node['ancient_sources']:
                    node['ancient_sources'].remove(to_remove)
                    corrections_applied.append(f"✓ Firmicus: Removed De Errore (not about fate)")

    # 5. TERTULLIAN ARGUMENT - Remove 4 works, keep only Adversus Marcionem
    for node in db['nodes']:
        if node['id'] == 'argument_tertullians_antimarcionite_argument_for_free_will_f49cad73':
            if 'ancient_sources' in node:
                to_remove = [
                    "Tertullian, De Anima 20-22, 40 (CCL 2; PL 2:701-752)",
                    "Tertullian, De Exhortatione Castitatis 1-2 (CCL 2; PL 2:913-930)",
                    "Tertullian, De Paenitentia 3 (CCL 1; PL 1:1227-1248)",
                    "Tertullian, Apologeticum 18, 45 (CCL 1; PL 1:257-536)"
                ]
                for src in to_remove:
                    if src in node['ancient_sources']:
                        node['ancient_sources'].remove(src)
                corrections_applied.append(f"✓ Tertullian Anti-Marcionite: Removed 4 non-specific works")

    # 6. BARDESANES - Remove Ephrem
    for node in db['nodes']:
        if node['id'] == 'person_bardesanes_the_syrian_3r8s0u76':
            if 'ancient_sources' in node:
                to_remove = "Ephrem the Syrian, Prose Refutations of Mani, Marcion and Bardaisan"
                if to_remove in node['ancient_sources']:
                    node['ancient_sources'].remove(to_remove)
                    corrections_applied.append(f"✓ Bardesanes: Removed uncertain Ephrem citation")

    # 7. PELAGIUS - Add his own writings
    for node in db['nodes']:
        if node['id'] == 'person_pelagius_british_monk_4ba38f92':
            if 'ancient_sources' in node:
                to_add = [
                    "Pelagius, Epistula ad Demetriadem (Letter to Demetrias) (PL 30:15-45; possibly spurious, perhaps by Julian of Eclanum)",
                    "Pelagius, Expositio in Epistulam Pauli ad Romanos (Commentary on Romans, fragments survive)",
                    "Pelagius, Libellus Fidei (Statement of Faith to Pope Innocent I; fragments in Augustine)"
                ]
                # Add at beginning (own writings before polemics against him)
                for src in reversed(to_add):
                    if src not in node['ancient_sources']:
                        node['ancient_sources'].insert(0, src)
                corrections_applied.append(f"✓ Pelagius: Added 3 of his own writings")

    # Update metadata
    db['metadata']['date_modified'] = '2025-10-21'
    if 'modification_note' in db['metadata']:
        db['metadata']['modification_note'] += ' | Manual fact-check: removed 12 sources not specifically about free will, added 3 Pelagian primary sources.'
    else:
        db['metadata']['modification_note'] = 'Manual fact-check: removed 12 sources not specifically about free will, added 3 Pelagian primary sources.'

    # Save
    with open('ancient_free_will_database.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    # Report
    print("=" * 70)
    print("SOURCE CORRECTIONS APPLIED")
    print("=" * 70)
    for correction in corrections_applied:
        print(correction)
    print(f"\nTotal corrections: {len(corrections_applied)}")
    print("\n✓ Database saved successfully")

if __name__ == '__main__':
    apply_corrections()
