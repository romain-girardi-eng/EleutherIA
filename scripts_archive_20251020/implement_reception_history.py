#!/usr/bin/env python3
"""
Implement reception history enhancements for the Ancient Free Will Database.
Adds metadata fields, transmission edges, and documents philosophical lineages.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

class ReceptionHistoryEnhancer:
    """Enhance database with reception history documentation."""

    def __init__(self):
        self.db = None
        self.enhancements_made = {
            'fields_added': 0,
            'edges_added': 0,
            'nodes_enriched': 0,
            'reception_documented': 0
        }

    def load_database(self, filepath: str = 'ancient_free_will_database_qa_validated.json') -> Dict:
        """Load the database."""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.db = json.load(f)
        print(f"Loaded database: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")
        return self.db

    def add_reception_metadata_fields(self):
        """Add reception history fields to relevant nodes."""

        # Define reception data for key medieval/modern figures
        reception_data = {
            # Compatibilist line
            'spinoza': {
                'reception_type': 'conceptual_development',
                'ancient_sources': ['Chrysippus', 'Stoics', 'Marcus Aurelius'],
                'transmission_path': ['Stoics', 'Cicero', 'Seneca', 'Spinoza'],
                'conceptual_transformation': 'Transformed Stoic fate into geometric necessity',
                'modern_engagement': 'Neo-Stoic determinism with ethics of joy'
            },
            'frankfurt': {
                'reception_type': 'parallel_development',
                'ancient_sources': ['Chrysippus', 'Epictetus'],
                'transmission_path': ['Stoics', 'Modern philosophy', 'Frankfurt'],
                'conceptual_transformation': 'Hierarchical desires parallel Stoic assent',
                'modern_engagement': 'Compatibilism without alternative possibilities',
                'reception_studies': [
                    {
                        'scholar': 'László Bernáth',
                        'work': 'Stoicism and Frankfurtian Compatibilism',
                        'year': 2018,
                        'finding': 'Identifies crucial differences despite similarities'
                    }
                ]
            },
            'susan_wolf': {
                'reception_type': 'conceptual_development',
                'ancient_sources': ['Aristotle', 'Stoics'],
                'transmission_path': ['Aristotle', 'Aquinas', 'Modern ethics', 'Wolf'],
                'conceptual_transformation': 'Reason View develops Aristotelian rational agency',
                'modern_engagement': 'Responsibility requires acting according to Reason'
            },

            # Libertarian line
            'robert_kane': {
                'reception_type': 'direct_development',
                'ancient_sources': ['Aristotle', 'Alexander of Aphrodisias'],
                'transmission_path': ['Aristotle', 'Alexander', 'Scotus', 'James', 'Kane'],
                'conceptual_transformation': 'Ultimate Responsibility develops Alexander\'s origination',
                'modern_engagement': 'Self-Forming Actions as quantum indeterminacy',
                'reception_studies': [
                    {
                        'scholar': 'Susanne Bobzien',
                        'work': 'The Inadvertent Conception',
                        'year': 1998,
                        'finding': 'Alexander as first incompatibilist'
                    }
                ]
            },
            'duns_scotus': {
                'reception_type': 'conceptual_development',
                'ancient_sources': ['Aristotle', 'Augustine'],
                'transmission_path': ['Aristotle', 'Arabic commentators', 'Aquinas', 'Scotus'],
                'conceptual_transformation': 'Voluntarism against Thomistic intellectualism',
                'modern_engagement': 'Will\'s freedom from intellect'
            },

            # Augustinian line
            'luther': {
                'reception_type': 'direct_engagement',
                'ancient_sources': ['Augustine', 'Paul'],
                'transmission_path': ['Paul', 'Augustine', 'Medieval theology', 'Luther'],
                'conceptual_transformation': 'Radicalized Augustine on bondage of will',
                'modern_engagement': 'De Servo Arbitrio against Erasmus'
            },
            'calvin': {
                'reception_type': 'systematic_development',
                'ancient_sources': ['Augustine', 'Paul'],
                'transmission_path': ['Augustine', 'Luther', 'Calvin'],
                'conceptual_transformation': 'Systematized predestination doctrine',
                'modern_engagement': 'Total depravity and irresistible grace'
            },
            'jonathan_edwards': {
                'reception_type': 'philosophical_development',
                'ancient_sources': ['Augustine', 'Paul'],
                'transmission_path': ['Augustine', 'Calvin', 'Puritans', 'Edwards'],
                'conceptual_transformation': 'Philosophical defense of theological determinism',
                'modern_engagement': 'Necessity compatible with responsibility'
            },

            # Aristotelian line
            'aquinas': {
                'reception_type': 'synthesis',
                'ancient_sources': ['Aristotle', 'Augustine'],
                'transmission_path': ['Aristotle', 'Arabic commentators', 'Aquinas'],
                'conceptual_transformation': 'Synthesized Aristotle with Christian theology',
                'modern_engagement': 'Thomistic free will theory'
            },
            'anscombe': {
                'reception_type': 'revival',
                'ancient_sources': ['Aristotle'],
                'transmission_path': ['Aristotle', 'Aquinas', 'Modern philosophy', 'Anscombe'],
                'conceptual_transformation': 'Revived Aristotelian action theory',
                'modern_engagement': 'Intention and practical reasoning'
            }
        }

        # Apply reception data to nodes
        enriched_count = 0
        for node in self.db['nodes']:
            if node.get('type') == 'person':
                # Check if this person needs reception data
                for key, data in reception_data.items():
                    if key in node.get('id', '').lower() or key in node.get('label', '').lower():
                        # Add reception fields
                        for field, value in data.items():
                            if field not in node:
                                node[field] = value
                                self.enhancements_made['fields_added'] += 1
                        enriched_count += 1
                        break

        self.enhancements_made['nodes_enriched'] = enriched_count
        print(f"Added reception metadata to {enriched_count} nodes")

    def add_transmission_edges(self):
        """Add edges showing philosophical transmission and influence."""

        transmission_edges = [
            # Stoic → Modern Compatibilism
            {'source': 'chrysippus', 'target': 'spinoza', 'relation': 'influenced',
             'description': 'Neo-Stoic determinism'},
            {'source': 'chrysippus', 'target': 'frankfurt', 'relation': 'parallel_development',
             'description': 'Hierarchical compatibilism parallels Stoic assent'},
            {'source': 'epictetus', 'target': 'frankfurt', 'relation': 'conceptual_parallel',
             'description': 'Internal freedom despite external determination'},

            # Aristotelian → Libertarian
            {'source': 'aristotle', 'target': 'alexander', 'relation': 'developed_by',
             'description': 'Incompatibilist interpretation of eph hemin'},
            {'source': 'alexander', 'target': 'robert_kane', 'relation': 'ancient_precedent',
             'description': 'Ultimate origination and undetermined choice'},
            {'source': 'aristotle', 'target': 'aquinas', 'relation': 'synthesized',
             'description': 'Aristotelian philosophy with Christian theology'},
            {'source': 'aristotle', 'target': 'anscombe', 'relation': 'revived_by',
             'description': 'Aristotelian action theory in analytic philosophy'},

            # Augustinian → Reformed
            {'source': 'augustine', 'target': 'luther', 'relation': 'direct_engagement',
             'description': 'De Servo Arbitrio develops Augustinian bondage of will'},
            {'source': 'augustine', 'target': 'calvin', 'relation': 'systematized_by',
             'description': 'Predestination and total depravity'},
            {'source': 'augustine', 'target': 'descartes', 'relation': 'influenced',
             'description': 'Si fallor sum prefigures cogito'},
            {'source': 'calvin', 'target': 'jonathan_edwards', 'relation': 'developed_by',
             'description': 'Philosophical defense of theological determinism'},

            # Skeptical tradition
            {'source': 'carneades', 'target': 'hume', 'relation': 'ancient_precedent',
             'description': 'Skeptical approach to causation and freedom'},
            {'source': 'sextus_empiricus', 'target': 'hume', 'relation': 'influenced',
             'description': 'Pyrrhonian skepticism about determinism'},

            # Medieval transmission
            {'source': 'aristotle', 'target': 'averroes', 'relation': 'commented_on',
             'description': 'Arabic commentary tradition'},
            {'source': 'averroes', 'target': 'aquinas', 'relation': 'transmitted_to',
             'description': 'Aristotle via Arabic philosophy'},
            {'source': 'augustine', 'target': 'anselm', 'relation': 'influenced',
             'description': 'Freedom as power for justice'},
            {'source': 'aquinas', 'target': 'scotus', 'relation': 'opposed_by',
             'description': 'Voluntarism against intellectualism'},

            # Cross-tradition influences
            {'source': 'stoics', 'target': 'spinoza', 'relation': 'school_influenced',
             'description': 'Stoic ethics and determinism'},
            {'source': 'epicurus', 'target': 'william_james', 'relation': 'ancient_precedent',
             'description': 'Indeterminism for freedom'},

            # Contemporary connections
            {'source': 'strawson_peter', 'target': 'strawson_galen', 'relation': 'influenced',
             'description': 'Reactive attitudes to hard incompatibilism'},
            {'source': 'frankfurt', 'target': 'fischer', 'relation': 'developed_by',
             'description': 'Semi-compatibilism'},
        ]

        # Helper function to find node ID
        def find_node_id(search_term: str) -> Optional[str]:
            """Find node ID containing search term."""
            search_lower = search_term.lower()
            for node in self.db['nodes']:
                if search_lower in node['id'].lower() or search_lower in node.get('label', '').lower():
                    return node['id']
            return None

        # Add transmission edges
        added_count = 0
        for edge_data in transmission_edges:
            source_id = find_node_id(edge_data['source'])
            target_id = find_node_id(edge_data['target'])

            if source_id and target_id:
                # Check if edge already exists
                exists = any(
                    e['source'] == source_id and
                    e['target'] == target_id and
                    e['relation'] == edge_data['relation']
                    for e in self.db['edges']
                )

                if not exists:
                    edge = {
                        'source': source_id,
                        'target': target_id,
                        'relation': edge_data['relation']
                    }
                    if 'description' in edge_data:
                        edge['description'] = edge_data['description']

                    self.db['edges'].append(edge)
                    added_count += 1

        self.enhancements_made['edges_added'] = added_count
        print(f"Added {added_count} transmission edges")

    def add_reception_concepts(self):
        """Add modern concepts that develop ancient ones."""

        new_concepts = [
            {
                'id': 'concept_ultimate_responsibility_kane',
                'type': 'concept',
                'label': 'Ultimate Responsibility (UR)',
                'category': 'modern_reception',
                'description': 'Robert Kane\'s development of Aristotelian ultimate origination, requiring that agents be ultimate sources of their actions through self-forming actions (SFAs)',
                'ancient_sources': ['Aristotle NE III', 'Alexander De Fato'],
                'reception_type': 'conceptual_development',
                'modern_formulation': 'Agents have UR for action only if they are responsible for anything that is a sufficient cause or motive for the action'
            },
            {
                'id': 'concept_hierarchical_compatibilism_frankfurt',
                'type': 'concept',
                'label': 'Hierarchical Compatibilism',
                'category': 'modern_reception',
                'description': 'Harry Frankfurt\'s theory that freedom consists in harmony between first-order desires and higher-order volitions, paralleling Stoic assent',
                'ancient_sources': ['Chrysippus', 'Epictetus on prohairesis'],
                'reception_type': 'parallel_development',
                'modern_formulation': 'Freedom requires that first-order desires be endorsed by second-order volitions'
            },
            {
                'id': 'concept_source_incompatibilism',
                'type': 'concept',
                'label': 'Source Incompatibilism',
                'category': 'modern_reception',
                'description': 'The view that determinism is incompatible with being the ultimate source of one\'s actions, developed from Alexander of Aphrodisias',
                'ancient_sources': ['Alexander De Fato 11-14'],
                'reception_type': 'direct_development',
                'modern_proponents': ['Derk Pereboom', 'Eleonore Stump']
            },
            {
                'id': 'concept_reactive_attitudes_strawson',
                'type': 'concept',
                'label': 'Reactive Attitudes',
                'category': 'modern_reception',
                'description': 'P.F. Strawson\'s account of moral responsibility through interpersonal attitudes, engaging with Stoic emotion theory',
                'ancient_parallels': ['Stoic theory of emotions', 'Appropriate feelings'],
                'reception_type': 'conceptual_parallel'
            }
        ]

        # Check which concepts already exist
        existing_ids = {n['id'] for n in self.db['nodes']}
        added = 0

        for concept in new_concepts:
            if concept['id'] not in existing_ids:
                self.db['nodes'].append(concept)
                added += 1

        print(f"Added {added} modern reception concepts")

    def document_reception_studies(self):
        """Add documentation about reception studies scholarship."""

        # Add or update metadata
        if 'reception_studies' not in self.db['metadata']:
            self.db['metadata']['reception_studies'] = {
                'description': 'This database tracks ancient free will debates (4th BCE - 6th CE) and their reception through medieval, modern, and contemporary philosophy',
                'key_scholarship': [
                    {
                        'author': 'Michael Frede',
                        'work': 'A Free Will: Origins of the Notion in Ancient Thought',
                        'year': 2011,
                        'contribution': 'Traces free will concept from Epictetus through Augustine'
                    },
                    {
                        'author': 'Susanne Bobzien',
                        'work': 'Determinism and Freedom in Stoic Philosophy',
                        'year': 1998,
                        'contribution': 'Links ancient Stoic and modern compatibilism'
                    },
                    {
                        'author': 'Richard Sorabji',
                        'work': 'Emotion and Peace of Mind',
                        'year': 2000,
                        'contribution': 'Stoic emotion theory reception'
                    },
                    {
                        'author': 'Ricardo Salles',
                        'work': 'The Stoics on Determinism and Compatibilism',
                        'year': 2008,
                        'contribution': 'Stoic arguments and modern parallels'
                    },
                    {
                        'author': 'László Bernáth',
                        'work': 'Stoicism and Frankfurtian Compatibilism',
                        'year': 2018,
                        'contribution': 'Compares Stoic and Frankfurt approaches'
                    }
                ],
                'transmission_paths': [
                    'Greek → Latin (Cicero, Boethius)',
                    'Greek → Syriac → Arabic → Latin (12th century)',
                    'Ancient → Medieval (Augustine primary)',
                    'Medieval → Modern (via Reformation)',
                    'Ancient → Contemporary (20th century revival)'
                ],
                'last_updated': datetime.now().isoformat()
            }
            self.enhancements_made['reception_documented'] = 1

        print("Added reception studies documentation to metadata")

    def save_enhanced_database(self, output_path: str = 'ancient_free_will_database_reception.json'):
        """Save the enhanced database."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
        print(f"Saved enhanced database to {output_path}")

    def run_enhancements(self):
        """Run all enhancement operations."""
        print("\n" + "=" * 70)
        print("IMPLEMENTING RECEPTION HISTORY ENHANCEMENTS")
        print("=" * 70 + "\n")

        # Run all enhancements
        self.add_reception_metadata_fields()
        self.add_transmission_edges()
        self.add_reception_concepts()
        self.document_reception_studies()

        # Report results
        print("\n" + "=" * 70)
        print("ENHANCEMENT SUMMARY")
        print("=" * 70)
        print(f"Fields added: {self.enhancements_made['fields_added']}")
        print(f"Nodes enriched: {self.enhancements_made['nodes_enriched']}")
        print(f"Edges added: {self.enhancements_made['edges_added']}")
        print(f"Reception documented: {self.enhancements_made['reception_documented']}")
        print(f"Final database: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")

        # Save enhanced database
        self.save_enhanced_database()

def main():
    """Main execution."""
    enhancer = ReceptionHistoryEnhancer()
    enhancer.load_database()
    enhancer.run_enhancements()

if __name__ == "__main__":
    main()