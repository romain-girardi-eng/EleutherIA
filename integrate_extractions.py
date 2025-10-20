#!/usr/bin/env python3
"""
Integrate all extracted data into the ancient free will database.
This will add quotes, arguments, concepts, and relationships.
"""

import json
import re
import hashlib
from typing import Dict, List, Set
import os

class DatabaseIntegrator:
    """Integrate extraction results into the main database."""

    def __init__(self):
        self.db = None
        self.existing_ids = set()
        self.added_nodes = 0
        self.added_edges = 0

    def load_database(self) -> Dict:
        """Load the main database."""
        with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
            self.db = json.load(f)

        # Track existing IDs
        self.existing_ids = {n['id'] for n in self.db['nodes']}
        print(f"Loaded database: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")
        return self.db

    def is_valid_greek(self, text: str) -> bool:
        """Validate Greek text quality."""
        if not text or len(text) < 10:
            return False

        # Count Greek characters
        greek_chars = sum(1 for c in text if 0x0370 <= ord(c) <= 0x03FF or 0x1F00 <= ord(c) <= 0x1FFF)
        if greek_chars < len(text) * 0.5:  # At least 50% Greek
            return False

        # Check for OCR garbage
        if re.search(r'[0-9]{3,}|[A-Z]{5,}|[@#$%^&*]{3,}', text):
            return False

        # Must have common Greek words or be substantial
        common_greek = ['καὶ', 'τὸ', 'τὴν', 'τῆς', 'τοῦ', 'εἰς', 'ἐν', 'δὲ', 'γὰρ', 'ὁ']
        if len(text) > 30:  # Longer texts are likely valid
            return True
        return any(word in text for word in common_greek)

    def is_valid_latin(self, text: str) -> bool:
        """Validate Latin text quality."""
        if not text or len(text) < 15:
            return False

        # Check for common Latin words
        common_latin = ['et', 'in', 'est', 'non', 'sed', 'cum', 'quod', 'ut', 'ad', 'ex']
        text_lower = text.lower()
        latin_words = sum(1 for word in common_latin if word in text_lower.split())

        return latin_words >= 2

    def generate_id(self, prefix: str, text: str) -> str:
        """Generate unique ID."""
        content = text[:100].encode('utf-8')
        hash_val = hashlib.md5(content).hexdigest()[:8]
        return f"{prefix}_{hash_val}"

    def add_quote_nodes(self, extraction_data: Dict) -> int:
        """Add quote nodes from extraction."""
        added = 0

        if 'sources' in extraction_data:
            for source_name, source_data in extraction_data['sources'].items():
                if 'quotes' in source_data:
                    for quote in source_data['quotes']:
                        # Validate quote
                        if quote.get('language') == 'Greek':
                            text = quote.get('greek_text', '')
                            if not self.is_valid_greek(text):
                                continue
                        elif quote.get('language') == 'Latin':
                            text = quote.get('latin_text', '')
                            if not self.is_valid_latin(text):
                                continue
                        else:
                            continue

                        # Generate ID
                        quote_id = self.generate_id('quote', text)
                        if quote_id in self.existing_ids:
                            continue

                        # Create quote node
                        quote_node = {
                            'id': quote_id,
                            'type': 'quote',
                            'category': 'primary_source',
                            'label': text[:60] + '...' if len(text) > 60 else text,
                            'full_text': text,
                            'language': quote['language'],
                            'source_file': source_name,
                            'line_number': quote.get('line_number')
                        }

                        # Add context if available
                        if quote.get('author'):
                            quote_node['author'] = quote['author']
                        if quote.get('context_before'):
                            quote_node['context'] = quote['context_before'][:200]

                        self.db['nodes'].append(quote_node)
                        self.existing_ids.add(quote_id)
                        added += 1

        return added

    def add_argument_nodes(self) -> int:
        """Add canonical argument nodes."""
        canonical_arguments = [
            {
                'id': 'argument_lazy_argument_canonical',
                'type': 'argument',
                'label': 'The Lazy Argument (ἀργὸς λόγος)',
                'greek_name': 'ἀργὸς λόγος',
                'latin_name': 'ignava ratio',
                'category': 'anti_fatalist',
                'description': 'Argument that if fate determines outcomes, human action is pointless',
                'premises': [
                    'If it is fated you will recover, you will recover whether you call a doctor or not',
                    'If it is fated you will not recover, you will not recover whether you call a doctor or not',
                    'Either recovery or non-recovery is fated'
                ],
                'conclusion': 'Therefore calling a doctor is pointless',
                'ancient_sources': ['Cicero, De Fato 28-30', 'Origen, Contra Celsum 2.20'],
                'responses': {
                    'chrysippus': 'Confatalia doctrine - some things are co-fated',
                    'carneades': 'Fate does not eliminate causation'
                }
            },
            {
                'id': 'argument_master_argument_diodorus',
                'type': 'argument',
                'label': 'The Master Argument (κύριος λόγος)',
                'greek_name': 'κύριος λόγος',
                'category': 'modal_logic',
                'description': 'Diodorus Cronus argument about possibility and necessity',
                'premises': [
                    'Every past truth is necessary',
                    'The impossible does not follow from the possible',
                    'What neither is nor will be is possible'
                ],
                'conclusion': 'Only what is or will be is possible',
                'ancient_sources': ['Epictetus, Diss. 2.19', 'Alexander, In An.Pr. 183-184']
            },
            {
                'id': 'argument_sea_battle_tomorrow',
                'type': 'argument',
                'label': 'Tomorrow\'s Sea Battle',
                'category': 'future_contingents',
                'description': 'Aristotle\'s argument about future contingent propositions',
                'premises': [
                    'Either there will be a sea battle tomorrow or not',
                    'If "there will be a sea battle" is true now, it is necessarily true',
                    'If necessarily true, the battle is inevitable'
                ],
                'conclusion': 'Either all events are necessary or bivalence fails for future contingents',
                'ancient_sources': ['Aristotle, De Int. 9']
            }
        ]

        added = 0
        for arg in canonical_arguments:
            if arg['id'] not in self.existing_ids:
                self.db['nodes'].append(arg)
                self.existing_ids.add(arg['id'])
                added += 1

        return added

    def add_debate_nodes(self) -> int:
        """Add major historical debates."""
        debates = [
            {
                'id': 'debate_stoic_academic_fate',
                'type': 'debate',
                'label': 'Stoic-Academic Debate on Fate',
                'category': 'historical_debate',
                'period': 'Hellenistic Greek',
                'description': 'Central debate between Stoics and Academic Skeptics on fate, determinism, and moral responsibility',
                'key_participants': ['Chrysippus', 'Carneades', 'Cicero'],
                'central_issues': [
                    'Compatibility of fate and responsibility',
                    'The Lazy Argument',
                    'Possibility of contingency'
                ],
                'ancient_sources': ['Cicero, De Fato', 'Plutarch, De Stoicorum Repugnantiis']
            },
            {
                'id': 'debate_christian_gnostic_free_will',
                'type': 'debate',
                'label': 'Christian-Gnostic Debate on Free Will',
                'category': 'historical_debate',
                'period': 'Patristic',
                'description': 'Debate between Christian theologians and Gnostics on human freedom vs cosmic determinism',
                'key_participants': ['Origen', 'Irenaeus', 'Valentinus'],
                'central_issues': [
                    'Nature of autexousion',
                    'Origin of evil',
                    'Cosmic determinism vs moral choice'
                ],
                'ancient_sources': ['Origen, De Principiis', 'Irenaeus, Adversus Haereses']
            },
            {
                'id': 'debate_grace_free_will_augustine',
                'type': 'debate',
                'label': 'Grace vs Free Will (Augustine-Pelagius)',
                'category': 'historical_debate',
                'period': 'Late Antiquity',
                'description': 'Foundational Christian debate on divine grace and human freedom',
                'key_participants': ['Augustine', 'Pelagius', 'John Cassian'],
                'central_issues': [
                    'Liberum arbitrium',
                    'Role of grace',
                    'Original sin',
                    'Human capacity for good'
                ],
                'ancient_sources': ['Augustine, De Libero Arbitrio', 'Augustine, De Gratia']
            },
            {
                'id': 'debate_peripatetic_stoic_freedom',
                'type': 'debate',
                'label': 'Peripatetic-Stoic Debate on Freedom',
                'category': 'historical_debate',
                'period': 'Roman Imperial',
                'description': 'Alexander of Aphrodisias defending libertarian free will against Stoic compatibilism',
                'key_participants': ['Alexander of Aphrodisias', 'Stoic opponents'],
                'central_issues': [
                    'Alternative possibilities',
                    'Self-determination',
                    'Critique of Stoic fate'
                ],
                'ancient_sources': ['Alexander, De Fato', 'Alexander, Mantissa']
            }
        ]

        added = 0
        for debate in debates:
            if debate['id'] not in self.existing_ids:
                self.db['nodes'].append(debate)
                self.existing_ids.add(debate['id'])
                added += 1

        return added

    def enrich_existing_concepts(self) -> int:
        """Enrich existing concept nodes with Greek/Latin terms."""
        enrichments = {
            'eph_hemin': {
                'greek_term': 'τὸ ἐφ\' ἡμῖν',
                'transliteration': 'to eph\' hêmin',
                'latin_equivalents': ['in nostra potestate', 'in nobis'],
                'semantic_field': ['autonomy', 'self-determination', 'moral responsibility']
            },
            'prohairesis': {
                'greek_term': 'προαίρεσις',
                'transliteration': 'prohairesis',
                'latin_equivalents': ['voluntas', 'electio'],
                'semantic_field': ['choice', 'moral choice', 'deliberate choice']
            },
            'autexousion': {
                'greek_term': 'τὸ αὐτεξούσιον',
                'transliteration': 'to autexousion',
                'latin_equivalents': ['liberum arbitrium', 'sui potestas'],
                'semantic_field': ['self-determination', 'free will', 'autonomy']
            },
            'heimarmene': {
                'greek_term': 'εἱμαρμένη',
                'transliteration': 'heimarmenê',
                'latin_equivalents': ['fatum', 'destinatio'],
                'semantic_field': ['fate', 'destiny', 'causal determination']
            }
        }

        enriched = 0
        for node in self.db['nodes']:
            if node.get('type') == 'concept':
                for key, data in enrichments.items():
                    if key in node.get('id', '').lower():
                        for field, value in data.items():
                            if field not in node:
                                node[field] = value
                        enriched += 1
                        break

        return enriched

    def add_relationships(self) -> int:
        """Add relationships between entities."""
        relationships = [
            # Chrysippus and arguments
            {'source': 'person_chrysippus*', 'target': 'argument_lazy_argument*', 'relation': 'responded_to'},
            {'source': 'person_chrysippus*', 'target': 'concept_confatalia*', 'relation': 'formulated'},

            # Carneades and arguments
            {'source': 'person_carneades*', 'target': 'argument_lazy_argument*', 'relation': 'reformulated'},
            {'source': 'person_carneades*', 'target': 'person_chrysippus*', 'relation': 'refuted'},

            # Alexander and freedom
            {'source': 'person_alexander*', 'target': 'concept_eph_hemin*', 'relation': 'defended'},
            {'source': 'person_alexander*', 'target': 'debate_peripatetic_stoic*', 'relation': 'participated_in'},

            # Debates and concepts
            {'source': 'debate_stoic_academic*', 'target': 'concept_heimarmene*', 'relation': 'concerned'},
            {'source': 'debate_christian_gnostic*', 'target': 'concept_autexousion*', 'relation': 'concerned'},
            {'source': 'debate_grace_free_will*', 'target': 'concept_liberum_arbitrium*', 'relation': 'concerned'}
        ]

        added = 0
        for rel in relationships:
            # Find matching source and target
            source_id = None
            target_id = None

            for node in self.db['nodes']:
                if rel['source'].endswith('*'):
                    if node['id'].startswith(rel['source'][:-1]):
                        source_id = node['id']
                elif node['id'] == rel['source']:
                    source_id = node['id']

                if rel['target'].endswith('*'):
                    if node['id'].startswith(rel['target'][:-1]):
                        target_id = node['id']
                elif node['id'] == rel['target']:
                    target_id = node['id']

            if source_id and target_id:
                # Check if edge already exists
                exists = any(e['source'] == source_id and e['target'] == target_id
                           for e in self.db['edges'])
                if not exists:
                    edge = {
                        'source': source_id,
                        'target': target_id,
                        'relation': rel['relation']
                    }
                    self.db['edges'].append(edge)
                    added += 1

        return added

    def integrate_all_extractions(self):
        """Main integration process."""
        print("\n" + "=" * 60)
        print("INTEGRATING EXTRACTIONS INTO DATABASE")
        print("=" * 60)

        # Load extraction results
        extraction_files = [
            'comprehensive_extraction_results.json',
            'COMPREHENSIVE_EXTRACTION_RESULTS.json',
            'PHASE2_ENRICHED_RESULTS.json',
            'AMAND_EXTRACTION.json'
        ]

        all_extractions = {}
        for file in extraction_files:
            if os.path.exists(file):
                print(f"Loading {file}...")
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_extractions[file] = data

        # Add quotes
        total_quotes = 0
        for file, data in all_extractions.items():
            if 'comprehensive' in file.lower():
                quotes_added = self.add_quote_nodes(data)
                total_quotes += quotes_added
                print(f"Added {quotes_added} quote nodes from {file}")

        # Add canonical arguments
        args_added = self.add_argument_nodes()
        print(f"Added {args_added} canonical argument nodes")

        # Add debates
        debates_added = self.add_debate_nodes()
        print(f"Added {debates_added} debate nodes")

        # Enrich concepts
        concepts_enriched = self.enrich_existing_concepts()
        print(f"Enriched {concepts_enriched} concept nodes")

        # Add relationships
        rels_added = self.add_relationships()
        print(f"Added {rels_added} relationships")

        # Update metadata
        self.db['metadata']['last_integration'] = '2025-10-20'
        self.db['metadata']['integration_stats'] = {
            'quotes_added': total_quotes,
            'arguments_added': args_added,
            'debates_added': debates_added,
            'concepts_enriched': concepts_enriched,
            'relationships_added': rels_added
        }

        # Save enhanced database
        output_file = 'ancient_free_will_database_enhanced_5k.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print("INTEGRATION COMPLETE")
        print("=" * 60)
        print(f"Final database: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")
        print(f"Growth: {len(self.db['nodes']) - 487} new nodes")
        print(f"Saved to: {output_file}")

def main():
    """Run the integration."""
    integrator = DatabaseIntegrator()
    integrator.load_database()
    integrator.integrate_all_extractions()

if __name__ == "__main__":
    main()