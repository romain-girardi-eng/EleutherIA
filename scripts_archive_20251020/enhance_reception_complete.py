#!/usr/bin/env python3
"""
Complete reception history enhancement for the Ancient Free Will Database.
Adds missing scholars, extensive transmission edges, and reception documentation.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

class CompleteReceptionEnhancer:
    """Comprehensive reception history enhancements."""

    def __init__(self):
        self.db = None
        self.enhancements = {
            'scholars_added': 0,
            'edges_added': 0,
            'concepts_added': 0,
            'works_added': 0,
            'metadata_enhanced': 0
        }

    def load_database(self, filepath: str = 'ancient_free_will_database_reception.json') -> Dict:
        """Load the database."""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.db = json.load(f)
        print(f"Loaded database: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")
        return self.db

    def add_reception_scholars(self):
        """Add missing scholars who study reception history."""

        new_scholars = [
            {
                'id': 'person_bobzien_susanne_contemporary',
                'type': 'person',
                'label': 'Susanne Bobzien',
                'category': 'contemporary_scholar',
                'period': 'Contemporary',
                'description': 'Leading scholar on ancient free will debates and their modern reception. Author of "Determinism and Freedom in Stoic Philosophy" (1998) and "The Inadvertent Conception and Late Birth of the Free Will Problem" (1998). Links Alexander of Aphrodisias to modern libertarianism and traces Stoic influence on contemporary compatibilism.',
                'specialization': 'Stoic philosophy, ancient free will, reception studies',
                'key_contributions': [
                    'First to identify Alexander as incompatibilist',
                    'Traces Stoic influence on modern compatibilism',
                    'Shows free will as late ancient concept'
                ]
            },
            {
                'id': 'person_frede_michael_1940_2007',
                'type': 'person',
                'label': 'Michael Frede',
                'category': 'contemporary_scholar',
                'period': 'Contemporary',
                'description': 'Influential historian of ancient philosophy who traced the origins of free will concept. Author of "A Free Will: Origins of the Notion in Ancient Thought" (2011). Argued that the notion of free will first emerges clearly with Epictetus.',
                'specialization': 'Ancient philosophy, concept history',
                'key_contributions': [
                    'Free will emerges with Epictetus',
                    'Traces concept through Augustine',
                    'Reception of ancient concepts'
                ]
            },
            {
                'id': 'person_sorabji_richard_contemporary',
                'type': 'person',
                'label': 'Richard Sorabji',
                'category': 'contemporary_scholar',
                'period': 'Contemporary',
                'description': 'Scholar of ancient philosophy and its reception. Director of the Ancient Commentators Project. Author of "Emotion and Peace of Mind" (2000) on Stoic emotion theory and its modern relevance.',
                'specialization': 'Ancient commentators, Stoic emotions',
                'key_contributions': [
                    'Ancient Commentators Project',
                    'Stoic emotion theory reception',
                    'Aristotelian psychology influence'
                ]
            },
            {
                'id': 'person_salles_ricardo_contemporary',
                'type': 'person',
                'label': 'Ricardo Salles',
                'category': 'contemporary_scholar',
                'period': 'Contemporary',
                'description': 'Scholar of Stoic philosophy and its modern parallels. Author of "The Stoics on Determinism and Compatibilism" (2008), comparing ancient Stoic arguments with contemporary analytical philosophy.',
                'specialization': 'Stoic determinism, modern parallels',
                'key_contributions': [
                    'Stoic arguments and modern parallels',
                    'Chrysippus and contemporary compatibilism',
                    'Ancient-modern dialogue'
                ]
            },
            {
                'id': 'person_inwood_brad_contemporary',
                'type': 'person',
                'label': 'Brad Inwood',
                'category': 'contemporary_scholar',
                'period': 'Contemporary',
                'description': 'Leading Stoic scholar examining ancient ethics in contemporary philosophy. Editor and translator of major Stoic texts. Studies how Stoic concepts inform modern moral philosophy.',
                'specialization': 'Stoic ethics, ancient-modern connections'
            },
            {
                'id': 'person_nussbaum_martha_contemporary',
                'type': 'person',
                'label': 'Martha Nussbaum',
                'category': 'contemporary_scholar',
                'period': 'Contemporary',
                'description': 'Philosopher connecting ancient Stoic and Aristotelian ethics to contemporary issues. Author of "The Therapy of Desire" examining Hellenistic philosophy\'s relevance to modern ethics.',
                'specialization': 'Ancient ethics, modern applications'
            },
            {
                'id': 'person_annas_julia_contemporary',
                'type': 'person',
                'label': 'Julia Annas',
                'category': 'contemporary_scholar',
                'period': 'Contemporary',
                'description': 'Scholar reviving ancient virtue ethics in contemporary philosophy. Author of "The Morality of Happiness" showing how ancient eudaimonism relates to modern ethics.',
                'specialization': 'Virtue ethics revival, ancient eudaimonism'
            },
            {
                'id': 'person_bernath_laszlo_contemporary',
                'type': 'person',
                'label': 'László Bernáth',
                'category': 'contemporary_scholar',
                'period': 'Contemporary',
                'description': 'Scholar comparing Stoic and Frankfurtian approaches to free will. Author of "Stoicism and Frankfurtian Compatibilism" (2018), identifying crucial differences despite surface similarities.',
                'specialization': 'Stoic-Frankfurt comparison',
                'key_work': 'Stoicism and Frankfurtian Compatibilism (2018)'
            }
        ]

        # Add key modern philosophers in reception chain
        modern_philosophers = [
            {
                'id': 'person_frankfurt_harry_1929_2023',
                'type': 'person',
                'label': 'Harry Frankfurt',
                'category': 'modern_philosopher',
                'period': 'Contemporary',
                'description': 'Developed hierarchical compatibilism theory with striking parallels to Stoic assent. Famous for Frankfurt Cases challenging the Principle of Alternative Possibilities (PAP).',
                'reception_type': 'parallel_development',
                'ancient_sources': ['Chrysippus', 'Epictetus'],
                'key_concepts': ['Hierarchical desires', 'Second-order volitions', 'Frankfurt Cases']
            },
            {
                'id': 'person_kane_robert_1938_2022',
                'type': 'person',
                'label': 'Robert Kane',
                'category': 'modern_philosopher',
                'period': 'Contemporary',
                'description': 'Libertarian philosopher developing Ultimate Responsibility (UR) from Aristotelian and Alexandrian precedents. Self-Forming Actions (SFAs) as modern incompatibilism.',
                'reception_type': 'direct_development',
                'ancient_sources': ['Aristotle', 'Alexander of Aphrodisias'],
                'key_concepts': ['Ultimate Responsibility', 'Self-Forming Actions', 'Quantum indeterminacy']
            },
            {
                'id': 'person_wolf_susan_contemporary',
                'type': 'person',
                'label': 'Susan Wolf',
                'category': 'modern_philosopher',
                'period': 'Contemporary',
                'description': 'Developed Reason View of responsibility echoing Stoic and Aristotelian rational agency. Responsibility requires acting according to Reason.',
                'reception_type': 'conceptual_development',
                'ancient_sources': ['Aristotle', 'Stoics'],
                'key_concepts': ['Reason View', 'Deep Self', 'Sane Deep Self']
            },
            {
                'id': 'person_pereboom_derk_contemporary',
                'type': 'person',
                'label': 'Derk Pereboom',
                'category': 'modern_philosopher',
                'period': 'Contemporary',
                'description': 'Hard incompatibilist developing source incompatibilism from Alexander of Aphrodisias. Four-Case Manipulation Argument against compatibilism.',
                'reception_type': 'direct_development',
                'ancient_sources': ['Alexander of Aphrodisias'],
                'key_concepts': ['Hard incompatibilism', 'Source incompatibilism', 'Manipulation Argument']
            },
            {
                'id': 'person_strawson_galen_contemporary',
                'type': 'person',
                'label': 'Galen Strawson',
                'category': 'modern_philosopher',
                'period': 'Contemporary',
                'description': 'Developed Basic Argument against ultimate moral responsibility, engaging with ancient skeptical traditions about free will.',
                'reception_type': 'conceptual_development',
                'ancient_sources': ['Sextus Empiricus', 'Skeptics'],
                'key_concepts': ['Basic Argument', 'Impossibility of ultimate responsibility']
            }
        ]

        # Check existing nodes
        existing_ids = {n['id'] for n in self.db['nodes']}

        # Add new scholars
        for scholar in new_scholars + modern_philosophers:
            if scholar['id'] not in existing_ids:
                self.db['nodes'].append(scholar)
                self.enhancements['scholars_added'] += 1

        print(f"Added {self.enhancements['scholars_added']} new scholars")

    def add_reception_works(self):
        """Add key works on reception studies."""

        reception_works = [
            {
                'id': 'work_frede_free_will_2011',
                'type': 'work',
                'label': 'A Free Will: Origins of the Notion in Ancient Thought',
                'author': 'Michael Frede',
                'year': 2011,
                'category': 'scholarly_work',
                'description': 'Traces the emergence of free will concept from Epictetus through Augustine. Argues free will is a late ancient innovation, not present in classical Greek philosophy.',
                'key_arguments': [
                    'Free will emerges with Epictetus',
                    'Concept absent in Aristotle',
                    'Augustine synthesizes traditions'
                ]
            },
            {
                'id': 'work_bobzien_determinism_freedom_1998',
                'type': 'work',
                'label': 'Determinism and Freedom in Stoic Philosophy',
                'author': 'Susanne Bobzien',
                'year': 1998,
                'category': 'scholarly_work',
                'description': 'Comprehensive analysis of Stoic compatibilism and its influence on modern debates. Links Chrysippus to contemporary compatibilist theories.',
                'key_arguments': [
                    'Stoic compatibilism as sophisticated theory',
                    'Chrysippus anticipates modern arguments',
                    'Alexander as first incompatibilist'
                ]
            },
            {
                'id': 'work_salles_stoics_determinism_2008',
                'type': 'work',
                'label': 'The Stoics on Determinism and Compatibilism',
                'author': 'Ricardo Salles',
                'year': 2008,
                'category': 'scholarly_work',
                'description': 'Examines Stoic arguments in light of contemporary analytical philosophy, showing parallels and differences.',
                'key_arguments': [
                    'Stoic arguments remain relevant',
                    'Modern reformulations of ancient problems',
                    'Continuity of philosophical tradition'
                ]
            },
            {
                'id': 'work_sorabji_emotion_peace_2000',
                'type': 'work',
                'label': 'Emotion and Peace of Mind',
                'author': 'Richard Sorabji',
                'year': 2000,
                'category': 'scholarly_work',
                'description': 'Studies Stoic emotion theory and its reception in modern philosophy of mind and cognitive therapy.',
                'key_themes': ['Stoic therapy', 'Emotion theory', 'Modern applications']
            },
            {
                'id': 'work_bernath_stoicism_frankfurt_2018',
                'type': 'work',
                'label': 'Stoicism and Frankfurtian Compatibilism',
                'author': 'László Bernáth',
                'year': 2018,
                'category': 'scholarly_article',
                'description': 'Compares Stoic and Frankfurt\'s hierarchical theories, finding important differences despite surface similarities.',
                'key_findings': [
                    'Both use hierarchical structure',
                    'Different concepts of self',
                    'Different views on external determination'
                ]
            }
        ]

        # Check existing works
        existing_ids = {n['id'] for n in self.db['nodes']}

        for work in reception_works:
            if work['id'] not in existing_ids:
                self.db['nodes'].append(work)
                self.enhancements['works_added'] += 1

        print(f"Added {self.enhancements['works_added']} reception studies works")

    def add_extensive_transmission_edges(self):
        """Add comprehensive transmission and influence edges."""

        extensive_edges = [
            # Scholarly work on reception
            {'source': 'person_bobzien_susanne_contemporary', 'target': 'work_bobzien_determinism_freedom_1998',
             'relation': 'authored', 'description': 'Comprehensive study of Stoic free will'},
            {'source': 'person_frede_michael_1940_2007', 'target': 'work_frede_free_will_2011',
             'relation': 'authored', 'description': 'Traces origins of free will concept'},
            {'source': 'person_salles_ricardo_contemporary', 'target': 'work_salles_stoics_determinism_2008',
             'relation': 'authored', 'description': 'Stoic arguments in modern context'},
            {'source': 'person_sorabji_richard_contemporary', 'target': 'work_sorabji_emotion_peace_2000',
             'relation': 'authored', 'description': 'Stoic emotion theory reception'},
            {'source': 'person_bernath_laszlo_contemporary', 'target': 'work_bernath_stoicism_frankfurt_2018',
             'relation': 'authored', 'description': 'Compares Stoic and Frankfurt'},

            # Ancient to modern philosopher connections
            {'source': 'person_chrysippus', 'target': 'person_frankfurt_harry_1929_2023',
             'relation': 'ancient_parallel', 'description': 'Hierarchical compatibilism parallel'},
            {'source': 'person_alexander_of_aphrodisias', 'target': 'person_kane_robert_1938_2022',
             'relation': 'ancient_precedent', 'description': 'Ultimate origination to Ultimate Responsibility'},
            {'source': 'person_aristotle', 'target': 'person_wolf_susan_contemporary',
             'relation': 'influenced', 'description': 'Rational agency to Reason View'},
            {'source': 'person_alexander_of_aphrodisias', 'target': 'person_pereboom_derk_contemporary',
             'relation': 'ancient_source', 'description': 'Source incompatibilism origins'},
            {'source': 'person_sextus_empiricus', 'target': 'person_strawson_galen_contemporary',
             'relation': 'ancient_parallel', 'description': 'Skepticism about free will'},

            # Scholar studies of ancient-modern connections
            {'source': 'person_bobzien_susanne_contemporary', 'target': 'person_chrysippus',
             'relation': 'studies', 'description': 'Research on Stoic compatibilism'},
            {'source': 'person_bobzien_susanne_contemporary', 'target': 'person_alexander_of_aphrodisias',
             'relation': 'studies', 'description': 'Identified as first incompatibilist'},
            {'source': 'person_frede_michael_1940_2007', 'target': 'person_epictetus',
             'relation': 'studies', 'description': 'Free will concept emergence'},
            {'source': 'person_sorabji_richard_contemporary', 'target': 'concept_stoic_emotions',
             'relation': 'analyzes', 'description': 'Reception of Stoic emotion theory'},

            # Work analyzes ancient sources
            {'source': 'work_bobzien_determinism_freedom_1998', 'target': 'person_chrysippus',
             'relation': 'analyzes', 'description': 'Stoic determinism and compatibilism'},
            {'source': 'work_frede_free_will_2011', 'target': 'person_epictetus',
             'relation': 'analyzes', 'description': 'Origins of free will notion'},
            {'source': 'work_salles_stoics_determinism_2008', 'target': 'argument_lazy_argument',
             'relation': 'examines', 'description': 'Modern analysis of ancient argument'},

            # Medieval transmission (if nodes exist)
            {'source': 'person_aristotle', 'target': 'person_averroes',
             'relation': 'commented_by', 'description': 'Arabic commentary tradition'},
            {'source': 'person_averroes', 'target': 'person_aquinas',
             'relation': 'transmitted_to', 'description': 'Aristotle via Arabic philosophy'},
            {'source': 'person_augustine', 'target': 'person_anselm',
             'relation': 'influenced', 'description': 'Freedom and divine justice'},

            # Concept evolution
            {'source': 'concept_eph_hemin', 'target': 'concept_ultimate_responsibility_kane',
             'relation': 'develops_into', 'description': 'Ancient "up to us" to modern UR'},
            {'source': 'concept_assent', 'target': 'concept_hierarchical_compatibilism_frankfurt',
             'relation': 'parallels', 'description': 'Stoic assent and Frankfurt\'s hierarchy'},
            {'source': 'concept_prohairesis', 'target': 'concept_reactive_attitudes_strawson',
             'relation': 'relates_to', 'description': 'Choice and moral attitudes'},

            # Argument continuity
            {'source': 'argument_lazy_argument', 'target': 'argument_consequence_van_inwagen',
             'relation': 'reformulated_as', 'description': 'Ancient fatalism to modern determinism'},
            {'source': 'argument_master_argument', 'target': 'debate_modern_modal_logic',
             'relation': 'continues_in', 'description': 'Modal necessity debates'},
            {'source': 'argument_sea_battle', 'target': 'debate_logical_fatalism',
             'relation': 'continues_as', 'description': 'Future contingents problem'},

            # School influences
            {'source': 'school_stoa', 'target': 'person_spinoza',
             'relation': 'influenced', 'description': 'Neo-Stoic philosophy'},
            {'source': 'school_peripatetic', 'target': 'person_anscombe',
             'relation': 'revived_by', 'description': 'Aristotelian action theory'},
            {'source': 'school_academic_skeptic', 'target': 'person_hume',
             'relation': 'influenced', 'description': 'Skeptical tradition on causation'}
        ]

        def find_node_id(search_term: str) -> Optional[str]:
            """Find node ID containing search term."""
            if not search_term:
                return None
            search_lower = search_term.lower()
            for node in self.db['nodes']:
                node_id = node.get('id', '').lower()
                node_label = node.get('label', '').lower()
                if search_lower in node_id or search_lower in node_label:
                    return node['id']
            return None

        # Add edges where both nodes exist
        added = 0
        for edge_data in extensive_edges:
            source_id = find_node_id(edge_data['source'])
            target_id = find_node_id(edge_data['target'])

            if source_id and target_id:
                # Check if edge exists
                exists = any(
                    e.get('source') == source_id and
                    e.get('target') == target_id and
                    e.get('relation') == edge_data['relation']
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
                    added += 1

        self.enhancements['edges_added'] = added
        print(f"Added {added} new transmission edges")

    def add_reception_concepts(self):
        """Add modern concepts that develop ancient ones."""

        modern_concepts = [
            {
                'id': 'concept_frankfurt_cases',
                'type': 'concept',
                'label': 'Frankfurt Cases',
                'category': 'modern_reception',
                'description': 'Thought experiments by Harry Frankfurt challenging the Principle of Alternative Possibilities (PAP). Shows moral responsibility without alternative possibilities, paralleling Stoic compatibilism.',
                'ancient_parallels': ['Stoic compatibilism', 'Chrysippus on assent'],
                'reception_type': 'modern_development',
                'key_example': 'Black ensures Jones will perform action X, but Jones does X on his own'
            },
            {
                'id': 'concept_manipulation_argument',
                'type': 'concept',
                'label': 'Manipulation Argument',
                'category': 'modern_reception',
                'description': 'Modern incompatibilist argument (Pereboom) that manipulated agents lack free will. Develops ancient concerns about external causation.',
                'ancient_sources': ['Stoic externals', 'Alexander on external causes'],
                'reception_type': 'conceptual_development',
                'versions': ['Four-Case Argument', 'Zygote Argument']
            },
            {
                'id': 'concept_consequence_argument',
                'type': 'concept',
                'label': 'Consequence Argument',
                'category': 'modern_reception',
                'description': 'Peter van Inwagen\'s argument that determinism is incompatible with free will. Modern formulation of ancient Lazy Argument concerns.',
                'ancient_precedent': 'Lazy Argument (ἀργὸς λόγος)',
                'formulation': 'No one has power over facts about past and laws of nature',
                'reception_type': 'reformulation'
            },
            {
                'id': 'concept_semicompatibilism',
                'type': 'concept',
                'label': 'Semicompatibilism',
                'category': 'modern_reception',
                'description': 'Fischer and Ravizza\'s view that moral responsibility is compatible with determinism even if free will is not. Develops Stoic themes.',
                'ancient_parallels': ['Stoic moral responsibility', 'Appropriate actions'],
                'reception_type': 'parallel_development',
                'key_features': ['Guidance control', 'Reasons-responsiveness']
            },
            {
                'id': 'concept_source_incompatibilism',
                'type': 'concept',
                'label': 'Source Incompatibilism',
                'category': 'modern_reception',
                'description': 'The view that determinism is incompatible with being the ultimate source of one\'s actions. Directly develops Alexander of Aphrodisias\' position.',
                'ancient_sources': ['Alexander De Fato 11-14'],
                'reception_type': 'direct_development',
                'modern_proponents': ['Derk Pereboom', 'Eleonore Stump', 'Kevin Timpe']
            }
        ]

        # Check existing concepts
        existing_ids = {n['id'] for n in self.db['nodes']}

        for concept in modern_concepts:
            if concept['id'] not in existing_ids:
                self.db['nodes'].append(concept)
                self.enhancements['concepts_added'] += 1

        print(f"Added {self.enhancements['concepts_added']} modern reception concepts")

    def enhance_metadata(self):
        """Enhance metadata with reception studies documentation."""

        # Add reception timeline
        if 'reception_timeline' not in self.db['metadata']:
            self.db['metadata']['reception_timeline'] = {
                'ancient_period': '4th BCE - 6th CE',
                'transmission_phases': [
                    {
                        'phase': 'Greek to Latin',
                        'period': '2nd BCE - 6th CE',
                        'key_figures': ['Cicero', 'Seneca', 'Boethius'],
                        'description': 'Translation and adaptation of Greek concepts'
                    },
                    {
                        'phase': 'Patristic Reception',
                        'period': '2nd - 5th CE',
                        'key_figures': ['Origen', 'Augustine', 'Gregory of Nyssa'],
                        'description': 'Christian engagement with pagan philosophy'
                    },
                    {
                        'phase': 'Arabic Transmission',
                        'period': '8th - 12th CE',
                        'key_figures': ['Al-Kindi', 'Al-Farabi', 'Averroes'],
                        'description': 'Preservation and commentary in Islamic world'
                    },
                    {
                        'phase': 'Scholastic Synthesis',
                        'period': '12th - 14th CE',
                        'key_figures': ['Aquinas', 'Scotus', 'Ockham'],
                        'description': 'Integration with Christian theology'
                    },
                    {
                        'phase': 'Reformation Debates',
                        'period': '16th CE',
                        'key_figures': ['Luther', 'Calvin', 'Erasmus'],
                        'description': 'Augustine\'s influence on grace/will debates'
                    },
                    {
                        'phase': 'Early Modern',
                        'period': '17th - 18th CE',
                        'key_figures': ['Descartes', 'Spinoza', 'Hume'],
                        'description': 'Scientific revolution and free will'
                    },
                    {
                        'phase': 'Contemporary Analytical',
                        'period': '20th - 21st CE',
                        'key_figures': ['Frankfurt', 'Kane', 'van Inwagen'],
                        'description': 'Ancient problems in analytical philosophy'
                    }
                ],
                'continuity_thesis': 'Contemporary free will debates directly continue ancient philosophical problems, with modern positions often unknowingly recreating ancient arguments.'
            }
            self.enhancements['metadata_enhanced'] += 1

        # Add reception bibliography
        if 'reception_bibliography' not in self.db['metadata']:
            self.db['metadata']['reception_bibliography'] = {
                'primary_studies': [
                    'Bobzien, S. (1998). Determinism and Freedom in Stoic Philosophy',
                    'Frede, M. (2011). A Free Will: Origins of the Notion in Ancient Thought',
                    'Sorabji, R. (2000). Emotion and Peace of Mind',
                    'Salles, R. (2008). The Stoics on Determinism and Compatibilism',
                    'Dihle, A. (1982). The Theory of Will in Classical Antiquity'
                ],
                'comparative_studies': [
                    'Bernáth, L. (2018). Stoicism and Frankfurtian Compatibilism',
                    'Long, A.A. (2002). Epictetus: A Stoic and Socratic Guide to Life',
                    'Inwood, B. (2005). Reading Seneca: Stoic Philosophy at Rome',
                    'Annas, J. (1993). The Morality of Happiness'
                ],
                'transmission_studies': [
                    'Marenbon, J. (2003). Boethius',
                    'McGrath, A. (2005). Christian Theology: An Introduction',
                    'Adamson, P. (2007). Al-Kindi',
                    'Pasnau, R. (2002). Thomas Aquinas on Human Nature'
                ]
            }
            self.enhancements['metadata_enhanced'] += 1

        # Update last modified
        self.db['metadata']['last_reception_update'] = datetime.now().isoformat()

        print(f"Enhanced {self.enhancements['metadata_enhanced']} metadata sections")

    def save_database(self, output_path: str = 'ancient_free_will_database_complete_reception.json'):
        """Save the enhanced database."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
        print(f"Saved enhanced database to {output_path}")

    def run_complete_enhancement(self):
        """Run all enhancement operations."""
        print("\n" + "=" * 70)
        print("COMPLETE RECEPTION HISTORY ENHANCEMENT")
        print("=" * 70 + "\n")

        # Run all enhancements
        self.add_reception_scholars()
        self.add_reception_works()
        self.add_extensive_transmission_edges()
        self.add_reception_concepts()
        self.enhance_metadata()

        # Report results
        print("\n" + "=" * 70)
        print("ENHANCEMENT SUMMARY")
        print("=" * 70)
        print(f"Scholars added: {self.enhancements['scholars_added']}")
        print(f"Works added: {self.enhancements['works_added']}")
        print(f"Edges added: {self.enhancements['edges_added']}")
        print(f"Concepts added: {self.enhancements['concepts_added']}")
        print(f"Metadata sections enhanced: {self.enhancements['metadata_enhanced']}")
        print(f"Final database: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")

        # Save enhanced database
        self.save_database()

def main():
    """Main execution."""
    enhancer = CompleteReceptionEnhancer()
    enhancer.load_database()
    enhancer.run_complete_enhancement()

if __name__ == "__main__":
    main()