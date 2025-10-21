#!/usr/bin/env python3
"""
Validate Database - EleutherIA Ancient Free Will Database
=========================================================

Validate the EleutherIA database against schema and perform integrity checks.
Ensures data quality and consistency.

Usage:
    python validate_database.py --input ancient_free_will_database.json
    python validate_database.py --schema schema.json --verbose
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Optional imports with error handling
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class DatabaseValidator:
    """Validate EleutherIA database for schema compliance and data integrity."""
    
    def __init__(self, db: Dict, schema: Optional[Dict] = None):
        self.db = db
        self.schema = schema
        self.errors = []
        self.warnings = []
    
    def validate_schema(self) -> bool:
        """Validate database against JSON schema."""
        if not self.schema:
            self.warnings.append("No schema provided for validation")
            return True
        
        if not JSONSCHEMA_AVAILABLE:
            self.warnings.append("jsonschema not available. Install with: pip install jsonschema")
            return True
        
        try:
            jsonschema.validate(instance=self.db, schema=self.schema)
            return True
        except jsonschema.ValidationError as e:
            self.errors.append(f"Schema validation error: {e.message}")
            return False
        except Exception as e:
            self.errors.append(f"Schema validation failed: {e}")
            return False
    
    def validate_required_fields(self) -> bool:
        """Validate that all required fields are present."""
        valid = True
        
        # Check metadata
        required_metadata = ['title', 'version', 'date_created', 'author', 'license']
        for field in required_metadata:
            if field not in self.db.get('metadata', {}):
                self.errors.append(f"Missing required metadata field: {field}")
                valid = False
        
        # Check nodes
        required_node_fields = ['id', 'label', 'type', 'description']
        for i, node in enumerate(self.db.get('nodes', [])):
            for field in required_node_fields:
                if field not in node:
                    self.errors.append(f"Node {i} missing required field: {field}")
                    valid = False
        
        # Check edges
        required_edge_fields = ['source', 'target', 'relation']
        for i, edge in enumerate(self.db.get('edges', [])):
            for field in required_edge_fields:
                if field not in edge:
                    self.errors.append(f"Edge {i} missing required field: {field}")
                    valid = False
        
        return valid
    
    def validate_node_ids(self) -> bool:
        """Validate node ID format and uniqueness."""
        valid = True
        node_ids = set()
        
        for i, node in enumerate(self.db.get('nodes', [])):
            node_id = node.get('id', '')
            
            # Check format (should be lowercase with underscores)
            if not re.match(r'^[a-z_]+_[a-z0-9_]+$', node_id):
                self.errors.append(f"Node {i} has invalid ID format: {node_id}")
                valid = False
            
            # Check uniqueness
            if node_id in node_ids:
                self.errors.append(f"Duplicate node ID: {node_id}")
                valid = False
            else:
                node_ids.add(node_id)
        
        return valid
    
    def validate_edge_references(self) -> bool:
        """Validate that all edge references point to existing nodes."""
        valid = True
        node_ids = {node['id'] for node in self.db.get('nodes', [])}
        
        for i, edge in enumerate(self.db.get('edges', [])):
            source = edge.get('source', '')
            target = edge.get('target', '')
            
            if source not in node_ids:
                self.errors.append(f"Edge {i} references non-existent source node: {source}")
                valid = False
            
            if target not in node_ids:
                self.errors.append(f"Edge {i} references non-existent target node: {target}")
                valid = False
        
        return valid
    
    def validate_node_types(self) -> bool:
        """Validate node types are valid."""
        valid = True
        valid_types = {
            'person', 'work', 'concept', 'argument', 'debate',
            'controversy', 'reformulation', 'event', 'school',
            'group', 'argument_framework', 'quote', 'conceptual_evolution'
        }

        for i, node in enumerate(self.db.get('nodes', [])):
            node_type = node.get('type', '')
            if node_type not in valid_types:
                self.errors.append(f"Node {i} has invalid type: {node_type}")
                valid = False

        return valid
    
    def validate_edge_relations(self) -> bool:
        """Validate edge relations are valid."""
        # No validation - database supports 228+ distinct relation types
        # All non-empty string relations are valid
        valid = True

        for i, edge in enumerate(self.db.get('edges', [])):
            relation = edge.get('relation', '')
            if not relation or not isinstance(relation, str):
                self.errors.append(f"Edge {i} has missing or invalid relation type")
                valid = False

        return valid
    
    def validate_greek_latin_characters(self) -> bool:
        """Validate Greek and Latin character encoding."""
        valid = True
        
        for i, node in enumerate(self.db.get('nodes', [])):
            # Check label for Greek characters
            label = node.get('label', '')
            if any(ord(char) > 127 for char in label):
                # Contains non-ASCII characters
                try:
                    label.encode('utf-8')
                except UnicodeEncodeError:
                    self.errors.append(f"Node {i} has invalid character encoding in label")
                    valid = False
            
            # Check description
            description = node.get('description', '')
            if any(ord(char) > 127 for char in description):
                try:
                    description.encode('utf-8')
                except UnicodeEncodeError:
                    self.errors.append(f"Node {i} has invalid character encoding in description")
                    valid = False
        
        return valid
    
    def validate_citations(self) -> bool:
        """Validate citation formats."""
        valid = True
        
        for i, node in enumerate(self.db.get('nodes', [])):
            # Check ancient sources
            ancient_sources = node.get('ancient_sources', [])
            for j, source in enumerate(ancient_sources):
                if not isinstance(source, str) or len(source.strip()) == 0:
                    self.errors.append(f"Node {i} has invalid ancient source {j}: {source}")
                    valid = False
            
            # Check modern scholarship
            modern_scholarship = node.get('modern_scholarship', [])
            for j, ref in enumerate(modern_scholarship):
                if not isinstance(ref, str) or len(ref.strip()) == 0:
                    self.errors.append(f"Node {i} has invalid modern scholarship {j}: {ref}")
                    valid = False
        
        return valid
    
    def validate_data_consistency(self) -> bool:
        """Validate data consistency across the database."""
        valid = True
        
        # Check that all nodes have consistent category
        for i, node in enumerate(self.db.get('nodes', [])):
            category = node.get('category', '')
            if category != 'free_will':
                self.warnings.append(f"Node {i} has unexpected category: {category}")
        
        # Check for orphaned nodes (nodes with no connections)
        node_ids = {node['id'] for node in self.db.get('nodes', [])}
        connected_nodes = set()
        
        for edge in self.db.get('edges', []):
            connected_nodes.add(edge.get('source', ''))
            connected_nodes.add(edge.get('target', ''))
        
        orphaned_nodes = node_ids - connected_nodes
        if orphaned_nodes:
            self.warnings.append(f"Found {len(orphaned_nodes)} orphaned nodes: {list(orphaned_nodes)[:5]}...")
        
        return valid
    
    def generate_statistics(self) -> Dict:
        """Generate database statistics."""
        stats = {
            'total_nodes': len(self.db.get('nodes', [])),
            'total_edges': len(self.db.get('edges', [])),
            'node_types': {},
            'edge_relations': {},
            'schools': {},
            'periods': {}
        }
        
        # Count node types
        for node in self.db.get('nodes', []):
            node_type = node.get('type', 'unknown')
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1
        
        # Count edge relations
        for edge in self.db.get('edges', []):
            relation = edge.get('relation', 'unknown')
            stats['edge_relations'][relation] = stats['edge_relations'].get(relation, 0) + 1
        
        # Count schools
        for node in self.db.get('nodes', []):
            school = node.get('school', 'unknown')
            if school:
                stats['schools'][school] = stats['schools'].get(school, 0) + 1
        
        # Count periods
        for node in self.db.get('nodes', []):
            period = node.get('period', 'unknown')
            if period:
                stats['periods'][period] = stats['periods'].get(period, 0) + 1
        
        return stats
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("Running validation checks...")
        
        checks = [
            ("Schema validation", self.validate_schema),
            ("Required fields", self.validate_required_fields),
            ("Node IDs", self.validate_node_ids),
            ("Edge references", self.validate_edge_references),
            ("Node types", self.validate_node_types),
            ("Edge relations", self.validate_edge_relations),
            ("Character encoding", self.validate_greek_latin_characters),
            ("Citations", self.validate_citations),
            ("Data consistency", self.validate_data_consistency)
        ]
        
        all_valid = True
        
        for check_name, check_func in checks:
            print(f"  {check_name}...", end=" ")
            try:
                if check_func():
                    print("✓")
                else:
                    print("✗")
                    all_valid = False
            except Exception as e:
                print(f"✗ (Error: {e})")
                self.errors.append(f"{check_name} failed with error: {e}")
                all_valid = False
        
        return all_valid
    
    def print_report(self, verbose: bool = False):
        """Print validation report."""
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60)
        
        # Statistics
        stats = self.generate_statistics()
        print(f"\nDatabase Statistics:")
        print(f"  Total nodes: {stats['total_nodes']}")
        print(f"  Total edges: {stats['total_edges']}")
        
        print(f"\nNode Types:")
        for node_type, count in sorted(stats['node_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {node_type:20s}: {count:3d}")
        
        print(f"\nEdge Relations:")
        for relation, count in sorted(stats['edge_relations'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {relation:20s}: {count:3d}")
        
        # Errors
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  ✗ {error}")
        else:
            print(f"\n✓ No errors found")
        
        # Warnings
        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        else:
            print(f"\n✓ No warnings")
        
        # Overall status
        if self.errors:
            print(f"\n❌ VALIDATION FAILED")
            return False
        else:
            print(f"\n✅ VALIDATION PASSED")
            return True


def load_database(db_path: str) -> Dict:
    """Load the EleutherIA database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    print(f"Loading database from {db_path}...")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    print(f"Loaded {len(db['nodes'])} nodes and {len(db['edges'])} edges")
    return db


def load_schema(schema_path: str) -> Optional[Dict]:
    """Load JSON schema."""
    if not os.path.exists(schema_path):
        print(f"Schema file not found: {schema_path}")
        return None
    
    print(f"Loading schema from {schema_path}...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    return schema


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate EleutherIA database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_database.py --input ancient_free_will_database.json
  python validate_database.py --schema schema.json --verbose
  python validate_database.py --input db.json --schema schema.json --output report.txt
        """
    )
    
    parser.add_argument(
        "--input",
        default="ancient_free_will_database.json",
        help="Input database file (default: ancient_free_will_database.json)"
    )
    
    parser.add_argument(
        "--schema",
        default="schema.json",
        help="JSON schema file (default: schema.json)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for validation report"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed validation information"
    )
    
    parser.add_argument(
        "--no-schema",
        action="store_true",
        help="Skip schema validation"
    )
    
    args = parser.parse_args()
    
    try:
        # Load database
        db = load_database(args.input)
        
        # Load schema
        schema = None
        if not args.no_schema:
            schema = load_schema(args.schema)
        
        # Initialize validator
        validator = DatabaseValidator(db, schema)
        
        # Run validation
        is_valid = validator.validate_all()
        
        # Print report
        if args.output:
            # Redirect output to file
            with open(args.output, 'w', encoding='utf-8') as f:
                import sys
                original_stdout = sys.stdout
                sys.stdout = f
                validator.print_report(verbose=args.verbose)
                sys.stdout = original_stdout
            print(f"Validation report saved to {args.output}")
        else:
            validator.print_report(verbose=args.verbose)
        
        # Exit with appropriate code
        if is_valid:
            return 0
        else:
            return 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
