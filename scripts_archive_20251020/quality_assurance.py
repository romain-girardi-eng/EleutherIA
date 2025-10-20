#!/usr/bin/env python3
"""
Quality assurance and validation for the final database.
Ensures academic standards and data integrity.
"""

import json
import re
from typing import Dict, List, Set, Tuple
import hashlib

class QualityAssurance:
    """Validate and clean the final database."""

    def __init__(self):
        self.db = None
        self.issues = []
        self.fixes_applied = 0

    def load_database(self, filepath: str = 'ancient_free_will_database_final.json') -> Dict:
        """Load database for validation."""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.db = json.load(f)
        print(f"Loaded database: {len(self.db['nodes'])} nodes, {len(self.db['edges'])} edges")
        return self.db

    def validate_required_fields(self) -> int:
        """Ensure all nodes have required fields."""
        issues = 0
        required_fields = ['id', 'type', 'label']

        for node in self.db['nodes']:
            for field in required_fields:
                if field not in node:
                    self.issues.append(f"Node missing {field}: {node.get('id', 'NO_ID')}")
                    issues += 1
                    # Fix by adding default
                    if field == 'type':
                        node['type'] = 'unknown'
                    elif field == 'label':
                        node['label'] = node.get('id', 'Unknown')[:50]

        return issues

    def validate_node_types(self) -> int:
        """Validate node types against controlled vocabulary."""
        valid_types = [
            'person', 'argument', 'concept', 'work', 'quote',
            'debate', 'controversy', 'reformulation', 'event',
            'school', 'group', 'argument_framework', 'conceptual_evolution'
        ]

        issues = 0
        for node in self.db['nodes']:
            if node.get('type') not in valid_types:
                self.issues.append(f"Invalid node type: {node['type']} for {node['id']}")
                issues += 1

        return issues

    def validate_edges(self) -> int:
        """Validate all edges point to existing nodes."""
        node_ids = {n['id'] for n in self.db['nodes']}
        invalid_edges = []
        issues = 0

        for i, edge in enumerate(self.db['edges']):
            if edge['source'] not in node_ids:
                self.issues.append(f"Edge source not found: {edge['source']}")
                invalid_edges.append(i)
                issues += 1
            if edge['target'] not in node_ids:
                self.issues.append(f"Edge target not found: {edge['target']}")
                invalid_edges.append(i)
                issues += 1

        # Remove invalid edges
        for i in reversed(invalid_edges):
            del self.db['edges'][i]
            self.fixes_applied += 1

        return issues

    def deduplicate_nodes(self) -> int:
        """Remove duplicate nodes."""
        seen_ids = set()
        unique_nodes = []
        duplicates = 0

        for node in self.db['nodes']:
            if node['id'] not in seen_ids:
                seen_ids.add(node['id'])
                unique_nodes.append(node)
            else:
                duplicates += 1
                self.issues.append(f"Duplicate node removed: {node['id']}")

        self.db['nodes'] = unique_nodes
        self.fixes_applied += duplicates
        return duplicates

    def clean_greek_text(self) -> int:
        """Clean and validate Greek text in quotes."""
        cleaned = 0

        for node in self.db['nodes']:
            if node.get('type') == 'quote' and node.get('language') == 'Greek':
                text = node.get('full_text', '')

                # Remove obvious OCR errors
                original = text
                # Remove isolated Latin letters in Greek text
                text = re.sub(r'\b[A-Z]\b', '', text)
                # Remove excessive spaces
                text = re.sub(r'\s{2,}', ' ', text)
                # Remove standalone numbers
                text = re.sub(r'\b\d{2,}\b', '', text)

                if text != original:
                    node['full_text'] = text.strip()
                    node['label'] = text[:70] + '...' if len(text) > 70 else text
                    cleaned += 1

        return cleaned

    def enrich_metadata(self) -> int:
        """Add missing metadata where possible."""
        enriched = 0

        # Add categories to nodes missing them
        type_to_category = {
            'person': 'historical_figure',
            'argument': 'philosophical_argument',
            'concept': 'philosophical_concept',
            'work': 'ancient_text',
            'quote': 'primary_source',
            'debate': 'historical_controversy'
        }

        for node in self.db['nodes']:
            if 'category' not in node and node.get('type') in type_to_category:
                node['category'] = type_to_category[node['type']]
                enriched += 1

        # Add descriptions to arguments missing them
        for node in self.db['nodes']:
            if node.get('type') == 'argument' and not node.get('description'):
                if 'lazy' in node.get('id', '').lower():
                    node['description'] = 'Argument that if fate determines outcomes, action is pointless'
                elif 'master' in node.get('id', '').lower():
                    node['description'] = 'Modal logic argument about possibility and necessity'
                elif 'sea' in node.get('id', '').lower():
                    node['description'] = 'Argument about future contingent propositions'
                enriched += 1

        return enriched

    def calculate_statistics(self) -> Dict:
        """Calculate database statistics."""
        stats = {
            'total_nodes': len(self.db['nodes']),
            'total_edges': len(self.db['edges']),
            'node_types': {},
            'languages': {},
            'periods': {},
            'avg_edges_per_node': 0
        }

        # Count node types
        for node in self.db['nodes']:
            node_type = node.get('type', 'unknown')
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1

        # Count languages in quotes
        for node in self.db['nodes']:
            if node.get('type') == 'quote':
                lang = node.get('language', 'unknown')
                stats['languages'][lang] = stats['languages'].get(lang, 0) + 1

        # Count periods
        for node in self.db['nodes']:
            if 'period' in node:
                period = node['period']
                stats['periods'][period] = stats['periods'].get(period, 0) + 1

        # Calculate average edges per node
        if stats['total_nodes'] > 0:
            stats['avg_edges_per_node'] = round(stats['total_edges'] * 2 / stats['total_nodes'], 2)

        return stats

    def generate_quality_report(self) -> str:
        """Generate comprehensive quality report."""
        stats = self.calculate_statistics()

        report = []
        report.append("=" * 70)
        report.append("QUALITY ASSURANCE REPORT")
        report.append("=" * 70)
        report.append("")

        # Database size
        report.append("DATABASE SIZE")
        report.append(f"  Total nodes: {stats['total_nodes']:,}")
        report.append(f"  Total edges: {stats['total_edges']:,}")
        report.append(f"  Avg edges/node: {stats['avg_edges_per_node']}")
        report.append("")

        # Node types breakdown
        report.append("NODE TYPES")
        for node_type, count in sorted(stats['node_types'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_nodes']) * 100
            report.append(f"  {node_type:20} {count:6,} ({percentage:5.1f}%)")
        report.append("")

        # Languages
        if stats['languages']:
            report.append("QUOTE LANGUAGES")
            for lang, count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {lang:10} {count:6,}")
            report.append("")

        # Issues found
        if self.issues:
            report.append(f"ISSUES FOUND: {len(self.issues)}")
            for issue in self.issues[:10]:  # Show first 10
                report.append(f"  • {issue}")
            if len(self.issues) > 10:
                report.append(f"  ... and {len(self.issues) - 10} more")
            report.append("")

        # Fixes applied
        report.append(f"FIXES APPLIED: {self.fixes_applied}")
        report.append("")

        # Quality metrics
        report.append("QUALITY METRICS")
        nodes_with_desc = sum(1 for n in self.db['nodes'] if n.get('description'))
        nodes_with_category = sum(1 for n in self.db['nodes'] if n.get('category'))
        quotes_with_context = sum(1 for n in self.db['nodes']
                                if n.get('type') == 'quote' and n.get('context'))

        report.append(f"  Nodes with descriptions: {nodes_with_desc:,} ({nodes_with_desc*100//stats['total_nodes']}%)")
        report.append(f"  Nodes with categories: {nodes_with_category:,} ({nodes_with_category*100//stats['total_nodes']}%)")
        if stats['node_types'].get('quote'):
            report.append(f"  Quotes with context: {quotes_with_context:,} ({quotes_with_context*100//stats['node_types']['quote']}%)")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

    def run_full_qa(self):
        """Run complete quality assurance process."""
        print("\n" + "=" * 70)
        print("RUNNING QUALITY ASSURANCE")
        print("=" * 70)

        # Run validations
        print("\nValidating database structure...")
        self.validate_required_fields()
        self.validate_node_types()
        self.validate_edges()

        print("Cleaning data...")
        self.deduplicate_nodes()
        self.clean_greek_text()

        print("Enriching metadata...")
        self.enrich_metadata()

        # Update database metadata
        self.db['metadata']['qa_completed'] = '2025-10-20'
        self.db['metadata']['qa_issues_found'] = len(self.issues)
        self.db['metadata']['qa_fixes_applied'] = self.fixes_applied

        # Save cleaned database
        output_file = 'ancient_free_will_database_qa_validated.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)

        # Generate and save report
        report = self.generate_quality_report()
        print(report)

        with open('QA_REPORT.txt', 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✓ Validated database saved to: {output_file}")
        print(f"✓ QA report saved to: QA_REPORT.txt")

def main():
    """Run quality assurance."""
    qa = QualityAssurance()
    qa.load_database()
    qa.run_full_qa()

if __name__ == "__main__":
    main()