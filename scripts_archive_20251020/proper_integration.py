#!/usr/bin/env python3
"""
Properly integrate all extracted data into the ancient free will database.
Fixed version that handles the actual extraction structure.
"""

import json
import re
import hashlib
from typing import Dict, List, Set
import os

class ProperDatabaseIntegrator:
    """Integrate extraction results properly."""

    def __init__(self):
        self.db = None
        self.existing_ids = set()
        self.stats = {
            'quotes_added': 0,
            'arguments_added': 0,
            'concepts_added': 0,
            'persons_enriched': 0,
            'debates_added': 0,
            'relationships_added': 0
        }

    def load_database(self) -> Dict:
        """Load the main database."""
        with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
            self.db = json.load(f)

        self.existing_ids = {n['id'] for n in self.db['nodes']}
        print(f"Loaded database: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")
        return self.db

    def is_valid_greek(self, text: str) -> bool:
        """Validate Greek text."""
        if not text or len(text) < 8:
            return False

        # Count Greek characters
        greek_chars = sum(1 for c in text if (0x0370 <= ord(c) <= 0x03FF) or (0x1F00 <= ord(c) <= 0x1FFF))

        # Need at least 30% Greek characters
        if len(text) > 0 and greek_chars / len(text) < 0.3:
            return False

        # Check for OCR garbage
        if re.search(r'[A-Z]{6,}|[0-9]{4,}|[@#$%^&*]{3,}', text):
            return False

        # Check for nonsense repetition
        if re.search(r'(.)\1{5,}', text):
            return False

        return True

    def is_valid_latin(self, text: str) -> bool:
        """Validate Latin text."""
        if not text or len(text) < 15:
            return False

        # Must have Latin words
        common_latin = ['et', 'est', 'sed', 'non', 'cum', 'quod', 'ad', 'in', 'ut', 'ex']
        text_lower = text.lower()

        latin_count = sum(1 for word in common_latin if f' {word} ' in f' {text_lower} ')
        return latin_count >= 2

    def generate_id(self, prefix: str, content: str) -> str:
        """Generate unique ID."""
        hash_input = f"{prefix}_{content[:100]}".encode('utf-8')
        hash_val = hashlib.md5(hash_input).hexdigest()[:8]
        return f"{prefix}_{hash_val}"

    def add_greek_latin_quotes(self, extraction_data: Dict) -> int:
        """Add Greek and Latin quotes from extraction data."""
        added = 0

        if 'extractions' not in extraction_data:
            return 0

        for doc_name, doc_data in extraction_data['extractions'].items():
            if not isinstance(doc_data, dict):
                continue

            # Process Greek/Latin extractions
            if 'greek_latin' in doc_data and isinstance(doc_data['greek_latin'], list):
                for item in doc_data['greek_latin']:
                    if not isinstance(item, dict):
                        continue

                    text = item.get('text', '')
                    if not text:
                        continue

                    # Determine language and validate
                    language = None
                    if self.is_valid_greek(text):
                        language = 'Greek'
                    elif self.is_valid_latin(text):
                        language = 'Latin'
                    else:
                        continue  # Skip invalid text

                    # Generate ID
                    quote_id = self.generate_id(f'quote_{language.lower()}', text)
                    if quote_id in self.existing_ids:
                        continue

                    # Create quote node
                    quote_node = {
                        'id': quote_id,
                        'type': 'quote',
                        'category': 'primary_source',
                        'label': text[:70] + '...' if len(text) > 70 else text,
                        'full_text': text,
                        'language': language,
                        'source_document': doc_name
                    }

                    # Add metadata if available
                    if 'line' in item:
                        quote_node['line_number'] = item['line']
                    if 'context' in item:
                        quote_node['context'] = item['context'][:300]

                    self.db['nodes'].append(quote_node)
                    self.existing_ids.add(quote_id)
                    added += 1

        return added

    def add_structured_arguments(self, extraction_data: Dict) -> int:
        """Add arguments from extraction data."""
        added = 0

        # First add canonical arguments
        canonical_args = [
            {
                'id': 'argument_lazy_argos_logos',
                'type': 'argument',
                'label': 'Lazy Argument (ἀργὸς λόγος)',
                'greek_name': 'ἀργὸς λόγος',
                'latin_name': 'ignava ratio',
                'category': 'anti-fatalist',
                'description': 'If fate determines all outcomes, human action becomes pointless',
                'premises': [
                    'If fated to recover, you recover regardless of calling a doctor',
                    'If fated not to recover, you don\'t recover regardless',
                    'Either recovery or non-recovery is fated'
                ],
                'conclusion': 'Therefore calling a doctor is pointless',
                'ancient_sources': ['Cicero, De Fato 28-30', 'Origen, Contra Celsum 2.20'],
                'period': 'Hellenistic Greek'
            },
            {
                'id': 'argument_master_diodorus',
                'type': 'argument',
                'label': 'Master Argument (κύριος λόγος)',
                'greek_name': 'κύριος λόγος',
                'category': 'modal_logic',
                'description': 'Diodorus Cronus\' argument about possibility and necessity',
                'premises': [
                    'Every past truth is necessary',
                    'The impossible doesn\'t follow from the possible',
                    'Some things neither are nor will be are possible'
                ],
                'conclusion': 'Only what is or will be is possible',
                'ancient_sources': ['Epictetus, Diss. 2.19', 'Alexander, In An.Pr. 183'],
                'period': 'Hellenistic Greek'
            },
            {
                'id': 'argument_confatalia_chrysippus',
                'type': 'argument',
                'label': 'Confatalia (Co-fated things)',
                'category': 'compatibilist',
                'description': 'Chrysippus\' response to the Lazy Argument',
                'premises': [
                    'Some things are simple fated events',
                    'Some things are co-fated (confatalia)',
                    'Health and calling a doctor are co-fated'
                ],
                'conclusion': 'Human actions are part of the causal chain of fate',
                'ancient_sources': ['Cicero, De Fato 30'],
                'period': 'Hellenistic Greek'
            },
            {
                'id': 'argument_sea_battle_aristotle',
                'type': 'argument',
                'label': 'Sea Battle Tomorrow',
                'category': 'future_contingents',
                'description': 'Aristotle on future contingent propositions',
                'premises': [
                    'Either there will be a sea battle tomorrow or not',
                    'If true now, necessarily true',
                    'If necessarily true, the event is necessary'
                ],
                'conclusion': 'Either determinism is true or bivalence fails for future contingents',
                'ancient_sources': ['Aristotle, De Int. 9'],
                'period': 'Classical Greek'
            }
        ]

        for arg in canonical_args:
            if arg['id'] not in self.existing_ids:
                self.db['nodes'].append(arg)
                self.existing_ids.add(arg['id'])
                added += 1

        return added

    def add_major_debates(self) -> int:
        """Add major philosophical debates."""
        debates = [
            {
                'id': 'debate_stoic_academic_hellenistic',
                'type': 'debate',
                'label': 'Stoic-Academic Debate on Fate',
                'category': 'philosophical_controversy',
                'period': 'Hellenistic Greek',
                'description': 'Central Hellenistic debate between Stoics (esp. Chrysippus) and Academic Skeptics (esp. Carneades) on fate, determinism, and moral responsibility',
                'key_figures': ['Chrysippus', 'Carneades', 'Antipater', 'Cicero'],
                'central_questions': [
                    'Is fate compatible with moral responsibility?',
                    'Can there be contingency in a determined world?',
                    'Does the Lazy Argument succeed?'
                ],
                'key_texts': ['Cicero, De Fato', 'Plutarch, De Stoicorum Repugnantiis']
            },
            {
                'id': 'debate_christian_gnostic_freedom',
                'type': 'debate',
                'label': 'Christian-Gnostic Debate on Freedom',
                'category': 'theological_controversy',
                'period': 'Patristic',
                'description': 'Patristic debate on human freedom (autexousion) vs cosmic determinism between Christian theologians and Gnostic teachers',
                'key_figures': ['Origen', 'Irenaeus', 'Valentinus', 'Basilides'],
                'central_questions': [
                    'Do humans have autexousion (self-determination)?',
                    'What is the origin of evil?',
                    'Are some natures saved/damned by nature?'
                ],
                'key_texts': ['Origen, De Principiis III.1', 'Irenaeus, Adversus Haereses']
            },
            {
                'id': 'debate_augustine_pelagius_grace',
                'type': 'debate',
                'label': 'Augustine-Pelagius on Grace and Free Will',
                'category': 'theological_controversy',
                'period': 'Late Antiquity',
                'description': 'Foundational Christian debate on the relationship between divine grace and human free will',
                'key_figures': ['Augustine', 'Pelagius', 'Julian of Eclanum', 'John Cassian'],
                'central_questions': [
                    'Can humans choose good without grace?',
                    'What is liberum arbitrium after the Fall?',
                    'Is original sin transmitted?'
                ],
                'key_texts': ['Augustine, De Libero Arbitrio', 'Augustine, De Gratia et Libero Arbitrio']
            },
            {
                'id': 'debate_alexander_stoics_determinism',
                'type': 'debate',
                'label': 'Alexander vs Stoics on Determinism',
                'category': 'philosophical_controversy',
                'period': 'Roman Imperial',
                'description': 'Alexander of Aphrodisias\' Peripatetic defense of libertarian free will against Stoic compatibilism',
                'key_figures': ['Alexander of Aphrodisias', 'unnamed Stoic opponents'],
                'central_questions': [
                    'Does "up to us" require alternative possibilities?',
                    'Is universal causation compatible with freedom?',
                    'Can there be self-motion without external cause?'
                ],
                'key_texts': ['Alexander, De Fato', 'Alexander, Mantissa 23']
            }
        ]

        added = 0
        for debate in debates:
            if debate['id'] not in self.existing_ids:
                self.db['nodes'].append(debate)
                self.existing_ids.add(debate['id'])
                added += 1

        return added

    def enrich_concepts(self) -> int:
        """Enrich existing concept nodes with Greek/Latin terms."""
        enriched = 0

        term_data = {
            'eph_hemin': {
                'greek_term': 'τὸ ἐφ\' ἡμῖν',
                'transliteration': 'to eph\' hêmin',
                'latin_equivalents': ['in nostra potestate', 'in nobis', 'in nostra manu'],
                'english': 'what is up to us',
                'philosophical_tradition': ['Aristotelian', 'Stoic', 'Peripatetic']
            },
            'prohairesis': {
                'greek_term': 'προαίρεσις',
                'transliteration': 'prohairesis',
                'latin_equivalents': ['voluntas', 'electio', 'arbitrium'],
                'english': 'deliberate choice, moral choice',
                'philosophical_tradition': ['Aristotelian', 'Stoic (Epictetus)']
            },
            'autexousion': {
                'greek_term': 'τὸ αὐτεξούσιον',
                'transliteration': 'to autexousion',
                'latin_equivalents': ['liberum arbitrium', 'libertas arbitrii'],
                'english': 'self-determination, free will',
                'philosophical_tradition': ['Patristic', 'Christian Platonist']
            },
            'heimarmene': {
                'greek_term': 'εἱμαρμένη',
                'transliteration': 'heimarmenê',
                'latin_equivalents': ['fatum', 'destinatio'],
                'english': 'fate, destiny',
                'philosophical_tradition': ['Stoic', 'Platonic']
            },
            'synkatathesis': {
                'greek_term': 'συγκατάθεσις',
                'transliteration': 'synkatathesis',
                'latin_equivalents': ['adsensio', 'assensus'],
                'english': 'assent',
                'philosophical_tradition': ['Stoic']
            }
        }

        for node in self.db['nodes']:
            if node.get('type') == 'concept':
                node_id_lower = node.get('id', '').lower()
                for key, data in term_data.items():
                    if key in node_id_lower or key.replace('_', '') in node_id_lower:
                        # Add all enrichment data
                        for field, value in data.items():
                            if field not in node:
                                node[field] = value
                        enriched += 1
                        break

        return enriched

    def add_key_relationships(self) -> int:
        """Add important relationships between nodes."""
        added = 0

        # Define relationships to add
        relationships = [
            # Arguments and persons
            ('person_chrysippus*', 'argument_confatalia*', 'formulated'),
            ('person_chrysippus*', 'argument_lazy*', 'responded_to'),
            ('person_carneades*', 'person_chrysippus*', 'criticized'),
            ('person_alexander*', 'concept_eph_hemin*', 'defended'),
            ('person_aristotle*', 'argument_sea_battle*', 'formulated'),
            ('person_diodorus*', 'argument_master*', 'formulated'),

            # Debates and participants
            ('person_chrysippus*', 'debate_stoic_academic*', 'participated_in'),
            ('person_carneades*', 'debate_stoic_academic*', 'participated_in'),
            ('person_origen*', 'debate_christian_gnostic*', 'participated_in'),
            ('person_augustine*', 'debate_augustine_pelagius*', 'participated_in'),
            ('person_pelagius*', 'debate_augustine_pelagius*', 'participated_in'),
            ('person_alexander*', 'debate_alexander_stoics*', 'participated_in'),

            # Concepts and debates
            ('debate_stoic_academic*', 'concept_heimarmene*', 'concerns'),
            ('debate_christian_gnostic*', 'concept_autexousion*', 'concerns'),
            ('debate_augustine_pelagius*', 'concept_liberum_arbitrium*', 'concerns'),
            ('debate_alexander_stoics*', 'concept_eph_hemin*', 'concerns')
        ]

        for source_pattern, target_pattern, relation_type in relationships:
            # Find matching nodes
            source_nodes = []
            target_nodes = []

            for node in self.db['nodes']:
                node_id = node['id']

                # Match source
                if source_pattern.endswith('*'):
                    if node_id.startswith(source_pattern[:-1]):
                        source_nodes.append(node_id)
                elif node_id == source_pattern:
                    source_nodes.append(node_id)

                # Match target
                if target_pattern.endswith('*'):
                    if node_id.startswith(target_pattern[:-1]):
                        target_nodes.append(node_id)
                elif node_id == target_pattern:
                    target_nodes.append(node_id)

            # Create edges
            for source_id in source_nodes:
                for target_id in target_nodes:
                    # Check if edge exists
                    exists = any(
                        e['source'] == source_id and
                        e['target'] == target_id and
                        e['relation'] == relation_type
                        for e in self.db['edges']
                    )

                    if not exists:
                        edge = {
                            'source': source_id,
                            'target': target_id,
                            'relation': relation_type
                        }
                        self.db['edges'].append(edge)
                        added += 1

        return added

    def integrate_everything(self):
        """Main integration process."""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE DATABASE INTEGRATION")
        print("=" * 70)

        # Load extraction data
        extraction_file = 'comprehensive_extraction_results.json'
        if os.path.exists(extraction_file):
            print(f"Loading {extraction_file}...")
            with open(extraction_file, 'r', encoding='utf-8') as f:
                extraction_data = json.load(f)
        else:
            print(f"ERROR: {extraction_file} not found!")
            return

        # Process each type of data
        print("\nIntegrating extracted data...")

        # Add quotes
        quotes_added = self.add_greek_latin_quotes(extraction_data)
        self.stats['quotes_added'] = quotes_added
        print(f"  ✓ Added {quotes_added} Greek/Latin quotes")

        # Add arguments
        args_added = self.add_structured_arguments(extraction_data)
        self.stats['arguments_added'] = args_added
        print(f"  ✓ Added {args_added} canonical arguments")

        # Add debates
        debates_added = self.add_major_debates()
        self.stats['debates_added'] = debates_added
        print(f"  ✓ Added {debates_added} major debates")

        # Enrich concepts
        concepts_enriched = self.enrich_concepts()
        self.stats['concepts_enriched'] = concepts_enriched
        print(f"  ✓ Enriched {concepts_enriched} concepts with Greek/Latin")

        # Add relationships
        rels_added = self.add_key_relationships()
        self.stats['relationships_added'] = rels_added
        print(f"  ✓ Added {rels_added} key relationships")

        # Update metadata
        self.db['metadata']['integration_date'] = '2025-10-20'
        self.db['metadata']['integration_stats'] = self.stats
        self.db['metadata']['quality_notes'] = 'Added validated Greek/Latin quotes, canonical arguments, major debates'

        # Save the enhanced database
        output_file = 'ancient_free_will_database_final.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 70)
        print("INTEGRATION COMPLETE")
        print("=" * 70)
        print(f"Original: 487 nodes, 747 edges")
        print(f"Final: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")
        print(f"Growth: +{len(self.db['nodes']) - 487} nodes, +{len(self.db['edges']) - 747} edges")
        print(f"\nDatabase saved to: {output_file}")
        print("\nBreakdown:")
        for key, value in self.stats.items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")

def main():
    """Run the integration."""
    integrator = ProperDatabaseIntegrator()
    integrator.load_database()
    integrator.integrate_everything()

if __name__ == "__main__":
    main()