#!/usr/bin/env python3
"""
Phase 2: Semantic Enrichment and Deep Analysis
Processes the initial extraction results to:
1. Enrich Greek/Latin extractions with translations and ancient sources
2. Structure arguments more precisely
3. Identify key debates and philosophical positions
4. Map concepts to their historical evolution
5. Extract relationships for knowledge graph integration
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

class SemanticEnricher:
    """Enrich extracted content with semantic information"""

    # Key philosophical terms with their historical context
    PHILOSOPHICAL_LEXICON = {
        'ἐφ᾽ ἡμῖν': {
            'transliteration': "eph' hêmin",
            'translation': 'in our power',
            'latin_equivalent': 'in nostra potestate',
            'first_attested': 'Aristotle',
            'period': 'Classical Greek',
            'related_concepts': ['free_will', 'voluntary', 'choice']
        },
        'εἱμαρμένη': {
            'transliteration': 'heimarmenê',
            'translation': 'fate, destiny',
            'latin_equivalent': 'fatum',
            'first_attested': 'Pre-Socratic',
            'period': 'Classical Greek',
            'related_concepts': ['determinism', 'necessity', 'providence']
        },
        'προαίρεσις': {
            'transliteration': 'proairesis',
            'translation': 'choice, decision',
            'latin_equivalent': 'electio',
            'first_attested': 'Aristotle',
            'period': 'Classical Greek',
            'related_concepts': ['deliberation', 'voluntary', 'practical_wisdom']
        },
        'ἑκούσιον': {
            'transliteration': 'hekousion',
            'translation': 'voluntary',
            'latin_equivalent': 'voluntarium',
            'first_attested': 'Aristotle',
            'period': 'Classical Greek',
            'related_concepts': ['involuntary', 'responsibility', 'blame']
        },
        'ἀκούσιον': {
            'transliteration': 'akousion',
            'translation': 'involuntary',
            'latin_equivalent': 'involuntarium',
            'first_attested': 'Aristotle',
            'period': 'Classical Greek',
            'related_concepts': ['voluntary', 'compulsion', 'ignorance']
        },
        'συγκατάθεσις': {
            'transliteration': 'synkatathesis',
            'translation': 'assent',
            'latin_equivalent': 'assensus',
            'first_attested': 'Zeno of Citium',
            'period': 'Hellenistic Greek',
            'related_concepts': ['impression', 'impulse', 'stoic_psychology']
        },
        'ὁρμή': {
            'transliteration': 'hormê',
            'translation': 'impulse',
            'latin_equivalent': 'impetus',
            'first_attested': 'Zeno of Citium',
            'period': 'Hellenistic Greek',
            'related_concepts': ['assent', 'impression', 'action']
        },
        'φαντασία': {
            'transliteration': 'phantasia',
            'translation': 'impression',
            'latin_equivalent': 'visum',
            'first_attested': 'Stoics',
            'period': 'Hellenistic Greek',
            'related_concepts': ['kataleptic_impression', 'assent', 'perception']
        },
        'αἰτία': {
            'transliteration': 'aitia',
            'translation': 'cause, explanation',
            'latin_equivalent': 'causa',
            'first_attested': 'Pre-Socratic',
            'period': 'Classical Greek',
            'related_concepts': ['causation', 'four_causes', 'responsibility']
        },
        'ἀνάγκη': {
            'transliteration': 'anankê',
            'translation': 'necessity',
            'latin_equivalent': 'necessitas',
            'first_attested': 'Pre-Socratic',
            'period': 'Classical Greek',
            'related_concepts': ['determinism', 'compulsion', 'logical_necessity']
        },
        'ἐνδεχόμενον': {
            'transliteration': 'endechomenon',
            'translation': 'possible, contingent',
            'latin_equivalent': 'contingens',
            'first_attested': 'Aristotle',
            'period': 'Classical Greek',
            'related_concepts': ['contingency', 'modality', 'future_contingents']
        },
        'τύχη': {
            'transliteration': 'tychê',
            'translation': 'chance, fortune',
            'latin_equivalent': 'fortuna',
            'first_attested': 'Homer',
            'period': 'Archaic Greek',
            'related_concepts': ['spontaneity', 'luck', 'randomness']
        },
        'αὐτεξούσιον': {
            'transliteration': 'autexousion',
            'translation': 'self-determining, free will',
            'latin_equivalent': 'liberum arbitrium',
            'first_attested': 'Patristic',
            'period': 'Late Antiquity',
            'related_concepts': ['free_will', 'self_determination', 'grace']
        }
    }

    # Key arguments in the free will debate
    CANONICAL_ARGUMENTS = {
        'lazy_argument': {
            'label': 'Lazy Argument (Argos Logos)',
            'proponent': 'Stoics (opponents)',
            'period': 'Hellenistic Greek',
            'structure': 'If everything is fated, deliberation is pointless',
            'stoic_response': 'Confatalia - some things are co-fated'
        },
        'master_argument': {
            'label': 'Master Argument (Kyrieuôn Logos)',
            'proponent': 'Diodorus Cronus',
            'period': 'Hellenistic Greek',
            'structure': 'Fatalism from modal logic',
            'key_premise': 'What is possible must at some time be actual'
        },
        'carneades_fatalism': {
            'label': 'Carneades Against Fatalism (CAFMA)',
            'proponent': 'Carneades',
            'period': 'Hellenistic Greek',
            'structure': 'Attack on Stoic determinism via causeless assents',
            'key_claim': 'Some assents have no antecedent causes'
        },
        'sea_battle': {
            'label': 'Sea Battle Argument',
            'proponent': 'Aristotle',
            'period': 'Classical Greek',
            'structure': 'Future contingents and bivalence',
            'key_text': 'De Interpretatione 9'
        },
        'reaper_argument': {
            'label': 'Reaper Argument (Therizôn)',
            'proponent': 'Epicurus',
            'period': 'Hellenistic Greek',
            'structure': 'Attack on fatalism',
            'key_claim': 'If all is fated, deliberation is pointless'
        },
        'four_causes': {
            'label': 'Four Causes Theory',
            'proponent': 'Aristotle',
            'period': 'Classical Greek',
            'structure': 'Material, formal, efficient, final causes',
            'relevance': 'Grounds for agent causation'
        },
        'cylinder_cone': {
            'label': 'Cylinder and Cone Analogy',
            'proponent': 'Chrysippus',
            'period': 'Hellenistic Greek',
            'structure': 'External causes vs. internal natures',
            'key_claim': 'Assent depends on internal nature, not just external impression'
        }
    }

    # Key debates
    MAJOR_DEBATES = {
        'stoic_academic': {
            'label': 'Stoic-Academic Debate on Fate and Responsibility',
            'participants': ['Chrysippus', 'Carneades', 'Cicero'],
            'period': 'Hellenistic Greek',
            'central_question': 'Can universal causal determinism be compatible with moral responsibility?',
            'key_texts': ['Cicero De Fato', 'Alexander In De Fato']
        },
        'epicurean_stoic': {
            'label': 'Epicurean-Stoic Debate on Determinism',
            'participants': ['Epicurus', 'Chrysippus'],
            'period': 'Hellenistic Greek',
            'central_question': 'Is the universe governed by necessity or does chance exist?',
            'key_concepts': ['atomic_swerve', 'fate', 'void']
        },
        'augustine_pelagius': {
            'label': 'Augustinian-Pelagian Controversy',
            'participants': ['Augustine', 'Pelagius', 'Julian of Eclanum'],
            'period': 'Patristic',
            'central_question': 'Can humans choose good without divine grace?',
            'key_concepts': ['original_sin', 'grace', 'free_will']
        },
        'originist_controversy': {
            'label': 'Originist Controversy on Free Will',
            'participants': ['Origen', 'Gregory of Nyssa', 'Jerome'],
            'period': 'Patristic',
            'central_question': 'How do we reconcile human freedom with divine foreknowledge?',
            'key_concepts': ['apokatastasis', 'providence', 'freedom']
        }
    }

    def __init__(self, extraction_results: Dict[str, Any]):
        self.results = extraction_results
        self.enriched_data = {
            'greek_latin_enriched': [],
            'arguments_structured': [],
            'debates_identified': [],
            'concepts_mapped': [],
            'relationships': [],
            'knowledge_graph_nodes': [],
            'knowledge_graph_edges': []
        }

    def enrich_greek_latin(self):
        """Enrich Greek and Latin extractions with linguistic and historical data"""
        print("\n" + "="*80)
        print("ENRICHING GREEK/LATIN EXTRACTIONS")
        print("="*80)

        all_extractions = []

        for doc_name, doc_data in self.results['extractions'].items():
            for item in doc_data['greek_latin']:
                text = item['text']

                # Match against lexicon
                enrichment = {
                    'original_text': text,
                    'source_document': doc_name,
                    'context': item['context'],
                    'line_number': item['line_number'],
                    'lexicon_match': None,
                    'identified_terms': []
                }

                # Check for lexicon matches
                for term, info in self.PHILOSOPHICAL_LEXICON.items():
                    if term in text:
                        enrichment['lexicon_match'] = info
                        enrichment['identified_terms'].append(term)

                all_extractions.append(enrichment)

        self.enriched_data['greek_latin_enriched'] = all_extractions
        print(f"✓ Enriched {len(all_extractions)} Greek/Latin extractions")

    def structure_arguments(self):
        """Structure philosophical arguments more precisely"""
        print("\n" + "="*80)
        print("STRUCTURING PHILOSOPHICAL ARGUMENTS")
        print("="*80)

        structured_args = []

        for doc_name, doc_data in self.results['extractions'].items():
            for arg in doc_data['arguments']:
                # Try to match against canonical arguments
                matched_canonical = None
                for arg_key, arg_info in self.CANONICAL_ARGUMENTS.items():
                    if arg_info['label'].lower() in arg['full_text'].lower():
                        matched_canonical = arg_info
                        break

                structured = {
                    'source_document': doc_name,
                    'paragraph_number': arg['paragraph_number'],
                    'premises': arg['premises'],
                    'conclusion': arg['conclusion'],
                    'full_text': arg['full_text'],
                    'canonical_argument': matched_canonical,
                    'extracted_philosophers': self._extract_philosophers(arg['full_text']),
                    'extracted_concepts': self._extract_concepts(arg['full_text'])
                }

                structured_args.append(structured)

        self.enriched_data['arguments_structured'] = structured_args
        print(f"✓ Structured {len(structured_args)} arguments")

    def identify_debates(self):
        """Identify and classify philosophical debates"""
        print("\n" + "="*80)
        print("IDENTIFYING DEBATES")
        print("="*80)

        debates = []

        for doc_name, doc_data in self.results['extractions'].items():
            for debate_item in doc_data['debates']:
                # Try to match against major debates
                matched_debate = None
                for debate_key, debate_info in self.MAJOR_DEBATES.items():
                    for participant in debate_info['participants']:
                        if participant.lower() in debate_item['context'].lower():
                            matched_debate = debate_info
                            break
                    if matched_debate:
                        break

                debate_entry = {
                    'source_document': doc_name,
                    'context': debate_item['context'],
                    'line_number': debate_item['line_number'],
                    'matched_debate': matched_debate,
                    'extracted_participants': self._extract_philosophers(debate_item['context'])
                }

                debates.append(debate_entry)

        self.enriched_data['debates_identified'] = debates
        print(f"✓ Identified {len(debates)} debates")

    def map_concepts(self):
        """Map concepts to their historical evolution"""
        print("\n" + "="*80)
        print("MAPPING CONCEPTS")
        print("="*80)

        concept_map = defaultdict(lambda: {
            'occurrences': [],
            'documents': set(),
            'contexts': []
        })

        for doc_name, doc_data in self.results['extractions'].items():
            for concept_item in doc_data['concepts']:
                for concept_type, mentions in concept_item['concepts'].items():
                    concept_map[concept_type]['occurrences'].extend(mentions)
                    concept_map[concept_type]['documents'].add(doc_name)
                    concept_map[concept_type]['contexts'].append(concept_item['context'])

        # Convert to list format
        mapped_concepts = []
        for concept_type, data in concept_map.items():
            mapped_concepts.append({
                'concept_type': concept_type,
                'total_occurrences': len(data['occurrences']),
                'unique_documents': list(data['documents']),
                'sample_contexts': data['contexts'][:5]  # Keep first 5
            })

        self.enriched_data['concepts_mapped'] = mapped_concepts
        print(f"✓ Mapped {len(mapped_concepts)} concept types")

    def extract_relationships(self):
        """Extract relationships for knowledge graph"""
        print("\n" + "="*80)
        print("EXTRACTING RELATIONSHIPS")
        print("="*80)

        relationships = []

        # Relationship patterns
        patterns = {
            'refutes': r'(\w+)\s+(?:refutes|attacks|criticizes|opposes)\s+(\w+)',
            'supports': r'(\w+)\s+(?:supports|defends|agrees with)\s+(\w+)',
            'influenced': r'(\w+)\s+(?:influenced|shaped|inspired)\s+(\w+)',
            'developed': r'(\w+)\s+(?:developed|formulated|created)\s+(?:the\s+)?(\w+)',
        }

        for doc_name, doc_data in self.results['extractions'].items():
            # Check arguments
            for arg in doc_data['arguments']:
                text = arg['full_text']
                for rel_type, pattern in patterns.items():
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        relationships.append({
                            'source': match.group(1),
                            'target': match.group(2),
                            'relation': rel_type,
                            'evidence': text[:200],
                            'document': doc_name
                        })

        self.enriched_data['relationships'] = relationships
        print(f"✓ Extracted {len(relationships)} relationships")

    def _extract_philosophers(self, text: str) -> List[str]:
        """Extract philosopher names from text"""
        philosophers = [
            'Aristotle', 'Plato', 'Socrates', 'Chrysippus', 'Zeno', 'Cleanthes',
            'Epicurus', 'Carneades', 'Cicero', 'Seneca', 'Epictetus',
            'Alexander of Aphrodisias', 'Plotinus', 'Origen', 'Augustine',
            'Boethius', 'Gregory of Nyssa', 'Diodorus', 'Philo'
        ]

        found = []
        for phil in philosophers:
            if phil.lower() in text.lower():
                found.append(phil)
        return found

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract concept mentions from text"""
        concepts = []
        for concept_type, patterns in PatternExtractor.CORE_CONCEPTS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    concepts.append(concept_type)
                    break
        return concepts

    def generate_knowledge_graph_nodes(self):
        """Generate node proposals for knowledge graph integration"""
        print("\n" + "="*80)
        print("GENERATING KNOWLEDGE GRAPH NODES")
        print("="*80)

        nodes = []

        # From structured arguments
        for arg in self.enriched_data['arguments_structured']:
            if arg['canonical_argument']:
                nodes.append({
                    'type': 'argument',
                    'label': arg['canonical_argument']['label'],
                    'proponent': arg['canonical_argument']['proponent'],
                    'period': arg['canonical_argument']['period'],
                    'description': arg['canonical_argument']['structure'],
                    'source_documents': [arg['source_document']]
                })

        # From debates
        for debate in self.enriched_data['debates_identified']:
            if debate['matched_debate']:
                nodes.append({
                    'type': 'debate',
                    'label': debate['matched_debate']['label'],
                    'participants': debate['matched_debate']['participants'],
                    'period': debate['matched_debate']['period'],
                    'description': debate['matched_debate']['central_question'],
                    'source_documents': [debate['source_document']]
                })

        self.enriched_data['knowledge_graph_nodes'] = nodes
        print(f"✓ Generated {len(nodes)} knowledge graph node proposals")

    def process_all(self):
        """Run all enrichment processes"""
        self.enrich_greek_latin()
        self.structure_arguments()
        self.identify_debates()
        self.map_concepts()
        self.extract_relationships()
        self.generate_knowledge_graph_nodes()

        return self.enriched_data

class PatternExtractor:
    """Import from original extractor"""
    CORE_CONCEPTS = {
        'free_will': [r'ἐφ\' ἡμῖν', r'in nostra potestate', r'liberum arbitrium', r'free will', r'free choice'],
        'fate': [r'εἱμαρμένη', r'fatum', r'fate', r'destiny', r'heimarmene'],
        'determinism': [r'determinism', r'necessity', r'ἀνάγκη', r'necessitas'],
        'responsibility': [r'responsibility', r'moral agency', r'imputation'],
        'causation': [r'αἰτία', r'causa', r'causation', r'causal'],
        'contingency': [r'ἐνδεχόμενον', r'contingens', r'contingent', r'possible'],
        'assent': [r'συγκατάθεσις', r'assensus', r'assent'],
        'impulse': [r'ὁρμή', r'impetus', r'impulse', r'horme'],
    }

def main():
    """Main execution"""
    print("="*80)
    print("PHASE 2: SEMANTIC ENRICHMENT")
    print("="*80)

    # Load Phase 1 results
    results_path = Path('/Users/romaingirardi/Documents/Ancient Free Will Database/COMPREHENSIVE_EXTRACTION_RESULTS.json')
    output_path = Path('/Users/romaingirardi/Documents/Ancient Free Will Database/PHASE2_ENRICHED_RESULTS.json')

    with open(results_path, 'r', encoding='utf-8') as f:
        phase1_results = json.load(f)

    # Enrich
    enricher = SemanticEnricher(phase1_results)
    enriched = enricher.process_all()

    # Save
    final_output = {
        'metadata': {
            'phase': 2,
            'description': 'Semantically enriched extraction results',
            'source_phase1': str(results_path)
        },
        'enriched_data': enriched,
        'summary': {
            'greek_latin_enriched': len(enriched['greek_latin_enriched']),
            'arguments_structured': len(enriched['arguments_structured']),
            'debates_identified': len(enriched['debates_identified']),
            'concepts_mapped': len(enriched['concepts_mapped']),
            'relationships': len(enriched['relationships']),
            'kg_nodes': len(enriched['knowledge_graph_nodes'])
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print("PHASE 2 COMPLETE")
    print("="*80)
    print(f"\nResults saved to: {output_path}")
    print(f"\nSUMMARY:")
    for key, value in final_output['summary'].items():
        print(f"  {key:30s}: {value:6d}")

if __name__ == '__main__':
    main()
