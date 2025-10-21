#!/usr/bin/env python3
"""
Comprehensive Terminology Addition Script
Adds appropriate Greek/Latin/Hebrew terms to all concept nodes based on historical accuracy
"""

import json
from datetime import datetime

# Priority 1: Greek concepts needing Latin equivalents (Greek→Latin transmission)
GREEK_TO_LATIN = {
    'concept_pithanotes_7v2w4y10': {
        'latin_term': 'probabile',
        'description_addition': 'Latin: probabile (Cicero, Academica)'
    },
    'concept_perfect_vs_antecedent_causes_8w3x5z21': {
        'latin_term': 'causa perfecta et principalis / causa antecedens et procatarctica',
        'description_addition': 'Latin: causa perfecta (perfect cause), causa antecedens (antecedent cause)'
    },
    'concept_genethlialogia_9x4y6a32': {
        'latin_term': 'genethliacus',
        'description_addition': 'Latin: genethliacus (from Greek)'
    },
    'concept_apotelesmatic_0y5z7b43': {
        'latin_term': 'apotelesmatica',
        'description_addition': 'Latin: apotelesmatica (from Greek)'
    },
    'concept_hypomnema_school_handbooks_1z6a8c54': {
        'latin_term': 'commentarii',
        'description_addition': 'Latin: commentarii (handbooks, commentaries)'
    },
    'concept_conditional_fate_9a5c8b4d': {
        'latin_term': 'fatum condicionatum',
        'description_addition': 'Latin: fatum condicionatum (conditional fate)'
    },
    'concept_pronoia_levels_proclus_a6d8c9b4': {
        'latin_term': 'providentia (gradibus)',
        'description_addition': 'Latin: providentia (providence in degrees/levels)'
    },
    'concept_synergism': {
        'latin_term': 'synergia / cooperatio',
        'description_addition': 'Latin: synergia (transliteration) or cooperatio (cooperation with grace)'
    },
    'concept_theosis': {
        'latin_term': 'deificatio / divinisatio',
        'description_addition': 'Latin: deificatio or divinisatio (deification, becoming divine)'
    },
    'concept_tripartite_soul_plato_e5f6g7h8': {
        'latin_term': 'anima tripartita',
        'description_addition': 'Latin: anima tripartita (tripartite soul)'
    },
    'concept_socratic_intellectualism_f6g7h8i9': {
        'latin_term': 'virtus est scientia',
        'description_addition': 'Latin: virtus est scientia (virtue is knowledge)'
    },
}

# Priority 2: Latin Patristic concepts with possible Greek equivalents
LATIN_TO_GREEK = {
    'concept_gratia_praeveniens': {
        'greek_term': 'χάρις προηγουμένη (charis proêgoumenê)',
        'description_addition': 'Greek equivalent: χάρις προηγουμένη (prevenient/preceding grace)'
    },
    'concept_gratia_operans': {
        'greek_term': 'χάρις ἐνεργοῦσα (charis energousa)',
        'description_addition': 'Greek equivalent: χάρις ἐνεργοῦσα (operating/energizing grace)'
    },
    'concept_gratia_cooperans': {
        'greek_term': 'χάρις συνεργοῦσα (charis synerg ousa)',
        'description_addition': 'Greek equivalent: χάρις συνεργοῦσα (cooperating grace)'
    },
    'concept_original_sin': {
        'greek_term': 'προπατορικὸν ἁμάρτημα (propatôrikon hamartêma)',
        'description_addition': 'Greek equivalent: προπατορικὸν ἁμάρτημα (ancestral sin - Eastern terminology differs from Western original sin)'
    },
    'concept_predestination_augustinian': {
        'greek_term': 'πρόγνωσις / προορισμός (prognôsis / proorismos)',
        'description_addition': 'Greek: πρόγνωσις (foreknowledge) or προορισμός (predetermination/predestination)'
    },
    'concept_concupiscence': {
        'greek_term': 'ἐπιθυμία (epithumia)',
        'description_addition': 'Greek: ἐπιθυμία (desire, concupiscence - but with different theological valence in Eastern tradition)'
    },
}

# Priority 3: Medieval/Early Modern Latin concepts
MEDIEVAL_LATIN = {
    'concept_liberum_arbitrium_u3v4w5x6': {
        'latin_term': 'liberum arbitrium',
    },
    'concept_voluntas_y7z8a9b0': {
        'latin_term': 'voluntas',
    },
    'concept_intellectus_c1d2e3f4': {
        'latin_term': 'intellectus',
    },
    'concept_synderesis_g5h6i7j8': {
        'latin_term': 'synderesis / synteresis',
    },
    'concept_potentia_absoluta_ordinata_k9l0m1n2': {
        'latin_term': 'potentia absoluta et ordinata',
    },
    'concept_synchronic_contingency_s7t8u9v0': {
        'latin_term': 'contingentia synchronica',
        'description_addition': 'Latin scholastic: contingentia synchronica (modern scholarly term for Scotist position)'
    },
    'concept_diachronic_contingency_w1x2y3z4': {
        'latin_term': 'contingentia diachronica',
        'description_addition': 'Latin scholastic: contingentia diachronica (modern scholarly term for Thomist position)'
    },
    'concept_occasionalism_a5b6c7d8': {
        'latin_term': 'occasionalismus',
        'description_addition': 'Latin: occasionalismus (17th c. philosophical term)'
    },
    'concept_kasb_acquisition_e9f0g1h2': {
        'arabic_term': 'كسب (kasb) / اكتساب (iktisāb)',
        'description_addition': 'Arabic: كسب (kasb) - acquisition'
    },
    'concept_intellectualism_medieval_i3j4k5l6': {
        'latin_term': 'intellectualismus',
    },
    'concept_voluntarism_medieval_m7n8o9p0': {
        'latin_term': 'voluntarismus',
    },
    'concept_bondage_of_will_1c5x6y24': {
        'latin_term': 'servum arbitrium',
    },
    'concept_scientia_media_2d6y7z35': {
        'latin_term': 'scientia media',
    },
    'concept_praemotio_physica_3e7z8a46': {
        'latin_term': 'praemotio physica',
    },
    'concept_libertas_indifferentiae_4f8a9b57': {
        'latin_term': 'libertas indifferentiae',
    },
    'concept_libertas_spontaneitatis_5g9b0c68': {
        'latin_term': 'libertas spontaneitatis',
    },
    'concept_pelagianism': {
        'latin_term': 'Pelagianismus',
    },
    'concept_semi_pelagianism': {
        'latin_term': 'Semi-Pelagianismus',
    },
}

# Priority 4: Hebrew/Jewish concepts
HEBREW_CONCEPTS = {
    'concept_yetzer_ha_ra_u3v4w5x6': {
        'hebrew_term': 'יֵצֶר הָרָע (yetzer ha-ra)',
        'transliteration': 'yetzer ha-ra',
    },
    'concept_yetzer_ha_tov_y7z8a9b0': {
        'hebrew_term': 'יֵצֶר הַטּוֹב (yetzer ha-tov)',
        'transliteration': 'yetzer ha-tov',
    },
    'concept_bechirah_c1d2e3f4': {
        'hebrew_term': 'בְּחִירָה (bechirah)',
        'transliteration': 'bechirah',
    },
    'concept_ratzon_g5h6i7j8': {
        'hebrew_term': 'רָצוֹן (ratzon)',
        'transliteration': 'ratzon',
    },
    'concept_hashgachah_o3p4q5r6': {
        'hebrew_term': 'הַשְׁגָּחָה (hashgachah)',
        'transliteration': 'hashgachah',
    },
    'concept_two_spirits_doctrine_s7t8u9v0': {
        'hebrew_term': 'שְׁנֵי רוּחוֹת (shnei ruchot)',
        'transliteration': 'shnei ruchot',
        'description_addition': 'Hebrew: שְׁנֵי רוּחוֹת (two spirits)'
    },
    'concept_covenant_nomism_k9l0m1n2': {
        # This is E.P. Sanders' English term - no Hebrew needed
        'description_addition': 'Modern scholarly term (E.P. Sanders, 1977) - no ancient Hebrew equivalent'
    },
}

# Additional concepts that need terminology updates
ADDITIONAL_UPDATES = {
    'concept_incompatibilism_ancient_o5p6q7r8': {
        'greek_term': 'ἀσύμβατον (asumbaton)',
        'latin_term': 'incompatibilitas',
        'description_addition': 'Modern philosophical term for ancient position; Greek: ἀσύμβατον (incompatible)'
    },
    'concept_terminology_evolution_greek_latin_y5z6a7b8': {
        # This is a meta-concept about terminology - no specific term needed
        'description_addition': 'Meta-linguistic concept - tracks evolution of vocabulary itself'
    },
    'concept_ancient_free_will_debate_structure_z6a7b8c9': {
        # Meta-concept about debate structure
        'description_addition': 'Meta-philosophical concept - describes debate structure across traditions'
    },
}

def add_terminology():
    """Add all appropriate terminology to concept nodes"""

    # Load database
    print("Loading database...")
    with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    nodes = db['nodes']

    # Track changes
    changes = {
        'priority1_greek_to_latin': 0,
        'priority2_latin_to_greek': 0,
        'priority3_medieval_latin': 0,
        'priority4_hebrew': 0,
        'additional_updates': 0
    }

    print("\n" + "=" * 80)
    print("ADDING TERMINOLOGY TO CONCEPT NODES")
    print("=" * 80)

    # Priority 1: Greek→Latin
    print("\n--- Priority 1: Adding Latin to Greek concepts ---")
    for node in nodes:
        node_id = node.get('id')
        if node_id in GREEK_TO_LATIN:
            updates = GREEK_TO_LATIN[node_id]
            if 'latin_term' in updates:
                node['latin_term'] = updates['latin_term']
                print(f"✓ {node_id}: Added Latin '{updates['latin_term']}'")
                changes['priority1_greek_to_latin'] += 1

    # Priority 2: Latin→Greek (Patristic)
    print("\n--- Priority 2: Adding Greek to Latin Patristic concepts ---")
    for node in nodes:
        node_id = node.get('id')
        if node_id in LATIN_TO_GREEK:
            updates = LATIN_TO_GREEK[node_id]
            if 'greek_term' in updates:
                node['greek_term'] = updates['greek_term']
                print(f"✓ {node_id}: Added Greek '{updates['greek_term']}'")
                changes['priority2_latin_to_greek'] += 1

    # Priority 3: Medieval Latin
    print("\n--- Priority 3: Adding Latin to medieval concepts ---")
    for node in nodes:
        node_id = node.get('id')
        if node_id in MEDIEVAL_LATIN:
            updates = MEDIEVAL_LATIN[node_id]
            if 'latin_term' in updates:
                node['latin_term'] = updates['latin_term']
                print(f"✓ {node_id}: Added Latin '{updates['latin_term']}'")
                changes['priority3_medieval_latin'] += 1
            if 'arabic_term' in updates:
                node['arabic_term'] = updates['arabic_term']
                print(f"✓ {node_id}: Added Arabic '{updates['arabic_term']}'")
                changes['priority3_medieval_latin'] += 1

    # Priority 4: Hebrew
    print("\n--- Priority 4: Adding Hebrew to Jewish concepts ---")
    for node in nodes:
        node_id = node.get('id')
        if node_id in HEBREW_CONCEPTS:
            updates = HEBREW_CONCEPTS[node_id]
            if 'hebrew_term' in updates:
                node['hebrew_term'] = updates['hebrew_term']
                print(f"✓ {node_id}: Added Hebrew '{updates['hebrew_term']}'")
                changes['priority4_hebrew'] += 1
            if 'transliteration' in updates and 'transliteration' not in node:
                node['transliteration'] = updates['transliteration']

    # Additional updates
    print("\n--- Additional concept updates ---")
    for node in nodes:
        node_id = node.get('id')
        if node_id in ADDITIONAL_UPDATES:
            updates = ADDITIONAL_UPDATES[node_id]
            if 'greek_term' in updates:
                node['greek_term'] = updates['greek_term']
                print(f"✓ {node_id}: Added Greek '{updates['greek_term']}'")
            if 'latin_term' in updates:
                node['latin_term'] = updates['latin_term']
                print(f"✓ {node_id}: Added Latin '{updates['latin_term']}'")
            changes['additional_updates'] += 1

    # Print summary
    print("\n" + "=" * 80)
    print("TERMINOLOGY ADDITION SUMMARY")
    print("=" * 80)
    print(f"Priority 1 (Greek→Latin):     {changes['priority1_greek_to_latin']} concepts updated")
    print(f"Priority 2 (Latin→Greek):     {changes['priority2_latin_to_greek']} concepts updated")
    print(f"Priority 3 (Medieval Latin):  {changes['priority3_medieval_latin']} concepts updated")
    print(f"Priority 4 (Hebrew):          {changes['priority4_hebrew']} concepts updated")
    print(f"Additional updates:           {changes['additional_updates']} concepts updated")
    print(f"\nTotal concepts updated:       {sum(changes.values())}")

    # Create backup
    backup_filename = f"ancient_free_will_database_BACKUP_terminology_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n" + "=" * 80)
    print(f"Creating backup: {backup_filename}")
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    # Save updated database
    print(f"Saving updated database...")
    with open('ancient_free_will_database.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print("\n✓ All terminology additions complete!")
    print(f"  Backup saved: {backup_filename}")

    return changes

if __name__ == '__main__':
    changes = add_terminology()
