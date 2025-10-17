#!/usr/bin/env python3
"""
Export Cytoscape - EleutherIA Ancient Free Will Database
========================================================

Export the EleutherIA database to Cytoscape-compatible CSV files.
Creates nodes.csv and edges.csv files for import into Cytoscape.

Usage:
    python export_cytoscape.py --input ancient_free_will_database.json
    python export_cytoscape.py --output-prefix eleutheria --include-descriptions
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


class CytoscapeExporter:
    """Export EleutherIA database to Cytoscape format."""
    
    def __init__(self, db: Dict):
        self.db = db
    
    def export_nodes(self, 
                     output_file: str = 'nodes.csv',
                     include_descriptions: bool = False,
                     include_sources: bool = False) -> None:
        """Export nodes to CSV format."""
        
        # Define CSV columns
        columns = [
            'id',
            'label', 
            'type',
            'category',
            'period',
            'school',
            'dates'
        ]
        
        if include_descriptions:
            columns.append('description')
        
        if include_sources:
            columns.append('ancient_sources')
            columns.append('modern_scholarship')
        
        # Additional useful columns
        columns.extend([
            'key_concepts',
            'position_on_free_will',
            'historical_importance'
        ])
        
        print(f"Exporting {len(self.db['nodes'])} nodes to {output_file}...")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            
            for node in self.db['nodes']:
                row = []
                
                for column in columns:
                    value = node.get(column, '')
                    
                    # Handle list fields
                    if isinstance(value, list):
                        if column in ['ancient_sources', 'modern_scholarship']:
                            # Limit to first 3 items for CSV
                            value = '; '.join(value[:3])
                        elif column == 'key_concepts':
                            value = '; '.join(value)
                        else:
                            value = '; '.join(str(v) for v in value)
                    
                    # Truncate long descriptions
                    if column == 'description' and len(str(value)) > 500:
                        value = str(value)[:500] + "..."
                    
                    row.append(str(value))
                
                writer.writerow(row)
        
        print(f"Nodes exported successfully to {output_file}")
    
    def export_edges(self, 
                    output_file: str = 'edges.csv',
                    include_descriptions: bool = False) -> None:
        """Export edges to CSV format."""
        
        # Define CSV columns
        columns = [
            'source',
            'target',
            'relation',
            'type'
        ]
        
        if include_descriptions:
            columns.append('description')
        
        columns.append('ancient_source')
        
        print(f"Exporting {len(self.db['edges'])} edges to {output_file}...")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            
            for edge in self.db['edges']:
                row = []
                
                for column in columns:
                    value = edge.get(column, '')
                    
                    # Truncate long descriptions
                    if column == 'description' and len(str(value)) > 300:
                        value = str(value)[:300] + "..."
                    
                    row.append(str(value))
                
                writer.writerow(row)
        
        print(f"Edges exported successfully to {output_file}")
    
    def export_metadata(self, output_file: str = 'metadata.txt') -> None:
        """Export database metadata and instructions."""
        
        metadata = self.db.get('metadata', {})
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("EleutherIA Ancient Free Will Database - Cytoscape Export\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("Database Information:\n")
            f.write(f"Title: {metadata.get('title', 'Unknown')}\n")
            f.write(f"Version: {metadata.get('version', 'Unknown')}\n")
            f.write(f"Author: {metadata.get('author', {}).get('primary', 'Unknown')}\n")
            f.write(f"Date: {metadata.get('date_created', 'Unknown')}\n\n")
            
            f.write("Statistics:\n")
            stats = metadata.get('statistics', {})
            f.write(f"Total nodes: {stats.get('total_nodes', len(self.db['nodes']))}\n")
            f.write(f"Total edges: {stats.get('total_edges', len(self.db['edges']))}\n\n")
            
            f.write("Node Types:\n")
            node_types = {}
            for node in self.db['nodes']:
                node_type = node.get('type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {node_type}: {count}\n")
            
            f.write("\nEdge Relations:\n")
            edge_relations = {}
            for edge in self.db['edges']:
                relation = edge.get('relation', 'unknown')
                edge_relations[relation] = edge_relations.get(relation, 0) + 1
            
            for relation, count in sorted(edge_relations.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {relation}: {count}\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("CYTOSCAPE IMPORT INSTRUCTIONS\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("1. Import Nodes:\n")
            f.write("   - File → Import → Network from File\n")
            f.write("   - Select 'nodes.csv'\n")
            f.write("   - Map columns:\n")
            f.write("     * id → Node ID\n")
            f.write("     * label → Node Label\n")
            f.write("     * type → Node Type\n")
            f.write("     * period → Period\n")
            f.write("     * school → School\n")
            f.write("   - Click OK\n\n")
            
            f.write("2. Import Edges:\n")
            f.write("   - File → Import → Network from File\n")
            f.write("   - Select 'edges.csv'\n")
            f.write("   - Map columns:\n")
            f.write("     * source → Source Node\n")
            f.write("     * target → Target Node\n")
            f.write("     * relation → Edge Type\n")
            f.write("   - Click OK\n\n")
            
            f.write("3. Styling Recommendations:\n")
            f.write("   - Node Colors by Type:\n")
            f.write("     * person: Red (#FF6B6B)\n")
            f.write("     * concept: Teal (#4ECDC4)\n")
            f.write("     * argument: Blue (#45B7D1)\n")
            f.write("     * work: Green (#96CEB4)\n")
            f.write("     * debate: Yellow (#FECA57)\n")
            f.write("     * controversy: Pink (#FF9FF3)\n")
            f.write("     * reformulation: Purple (#54A0FF)\n")
            f.write("     * event: Dark Purple (#5F27CD)\n")
            f.write("     * school: Cyan (#00D2D3)\n")
            f.write("     * group: Orange (#FF6348)\n")
            f.write("     * argument_framework: Dark Green (#2ED573)\n\n")
            
            f.write("   - Edge Colors by Relation:\n")
            f.write("     * influenced: Red (#FF6B6B)\n")
            f.write("     * refutes: Dark Red (#FF4757)\n")
            f.write("     * supports: Green (#2ED573)\n")
            f.write("     * formulated: Blue (#5352ED)\n")
            f.write("     * authored: Purple (#5F27CD)\n")
            f.write("     * opposes: Orange (#FF6348)\n")
            f.write("     * Other relations: Gray (#999999)\n\n")
            
            f.write("4. Layout Recommendations:\n")
            f.write("   - Force Atlas 2: Good for general exploration\n")
            f.write("     * Repulsion: 2000\n")
            f.write("     * Attraction: 10\n")
            f.write("     * Iterations: 1000\n\n")
            
            f.write("   - Hierarchical: Good for influence chains\n")
            f.write("     * Direction: Top to Bottom\n")
            f.write("     * Node spacing: 100\n\n")
            
            f.write("   - Circular: Good for overview\n")
            f.write("     * Node spacing: 100\n\n")
            
            f.write("5. Filtering:\n")
            f.write("   - Filter by type: Column: type, Value: person\n")
            f.write("   - Filter by school: Column: school, Value: Stoic\n")
            f.write("   - Filter by period: Column: period, Value: Hellenistic Greek\n\n")
            
            f.write("6. Analysis:\n")
            f.write("   - Tools → Network Analyzer → Analyze Network\n")
            f.write("   - Tools → Cluster → MCL Cluster\n")
            f.write("   - Tools → Filter → Create Filter\n\n")
            
            f.write("For more information, visit:\n")
            f.write("https://github.com/romain-girardi-eng/EleutherIA\n")
        
        print(f"Metadata and instructions exported to {output_file}")
    
    def create_style_file(self, output_file: str = 'eleutheria_style.xml') -> None:
        """Create Cytoscape style file."""
        
        style_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<cy:cyStyle xmlns:cy="http://www.cytoscape.org" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.cytoscape.org http://www.cytoscape.org/cyStyle.xsd">
  <cy:title>EleutherIA Style</cy:title>
  <cy:applies-to>
    <cy:view>all</cy:view>
  </cy:applies-to>
  
  <!-- Node Styles -->
  <cy:defaults>
    <cy:node>
      <cy:visualProperty name="NODE_SIZE" value="50"/>
      <cy:visualProperty name="NODE_FILL_COLOR" value="#4ECDC4"/>
      <cy:visualProperty name="NODE_BORDER_WIDTH" value="2"/>
      <cy:visualProperty name="NODE_BORDER_COLOR" value="#FFFFFF"/>
      <cy:visualProperty name="NODE_LABEL_COLOR" value="#000000"/>
      <cy:visualProperty name="NODE_LABEL_FONT_SIZE" value="10"/>
    </cy:node>
    <cy:edge>
      <cy:visualProperty name="EDGE_WIDTH" value="1"/>
      <cy:visualProperty name="EDGE_COLOR" value="#999999"/>
      <cy:visualProperty name="EDGE_LINE_TYPE" value="SOLID"/>
    </cy:edge>
  </cy:defaults>
  
  <!-- Node Type Colors -->
  <cy:mappings>
    <cy:mapping name="nodeTypeColor" type="discrete" attributeName="type">
      <cy:discreteMapping>
        <cy:discrete value="person">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#FF6B6B"/>
        </cy:discrete>
        <cy:discrete value="concept">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#4ECDC4"/>
        </cy:discrete>
        <cy:discrete value="argument">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#45B7D1"/>
        </cy:discrete>
        <cy:discrete value="work">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#96CEB4"/>
        </cy:discrete>
        <cy:discrete value="debate">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#FECA57"/>
        </cy:discrete>
        <cy:discrete value="controversy">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#FF9FF3"/>
        </cy:discrete>
        <cy:discrete value="reformulation">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#54A0FF"/>
        </cy:discrete>
        <cy:discrete value="event">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#5F27CD"/>
        </cy:discrete>
        <cy:discrete value="school">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#00D2D3"/>
        </cy:discrete>
        <cy:discrete value="group">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#FF6348"/>
        </cy:discrete>
        <cy:discrete value="argument_framework">
          <cy:visualProperty name="NODE_FILL_COLOR" value="#2ED573"/>
        </cy:discrete>
      </cy:discreteMapping>
    </cy:mapping>
    
    <!-- Node Size by Degree -->
    <cy:mapping name="nodeSize" type="continuous" attributeName="degree">
      <cy:continuousMapping>
        <cy:continuousMappingPoint value="0">
          <cy:visualProperty name="NODE_SIZE" value="20"/>
        </cy:continuousMappingPoint>
        <cy:continuousMappingPoint value="10">
          <cy:visualProperty name="NODE_SIZE" value="100"/>
        </cy:continuousMappingPoint>
      </cy:continuousMapping>
    </cy:mapping>
    
    <!-- Edge Colors by Relation -->
    <cy:mapping name="edgeColor" type="discrete" attributeName="relation">
      <cy:discreteMapping>
        <cy:discrete value="influenced">
          <cy:visualProperty name="EDGE_COLOR" value="#FF6B6B"/>
        </cy:discrete>
        <cy:discrete value="refutes">
          <cy:visualProperty name="EDGE_COLOR" value="#FF4757"/>
        </cy:discrete>
        <cy:discrete value="supports">
          <cy:visualProperty name="EDGE_COLOR" value="#2ED573"/>
        </cy:discrete>
        <cy:discrete value="formulated">
          <cy:visualProperty name="EDGE_COLOR" value="#5352ED"/>
        </cy:discrete>
        <cy:discrete value="authored">
          <cy:visualProperty name="EDGE_COLOR" value="#5F27CD"/>
        </cy:discrete>
        <cy:discrete value="opposes">
          <cy:visualProperty name="EDGE_COLOR" value="#FF6348"/>
        </cy:discrete>
      </cy:discreteMapping>
    </cy:mapping>
  </cy:mappings>
</cy:cyStyle>'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(style_xml)
        
        print(f"Cytoscape style file exported to {output_file}")


def load_database(db_path: str) -> Dict:
    """Load the EleutherIA database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    print(f"Loading database from {db_path}...")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    print(f"Loaded {len(db['nodes'])} nodes and {len(db['edges'])} edges")
    return db


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Export EleutherIA database to Cytoscape format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export_cytoscape.py --input ancient_free_will_database.json
  python export_cytoscape.py --output-prefix eleutheria --include-descriptions
  python export_cytoscape.py --style-file --metadata
        """
    )
    
    parser.add_argument(
        "--input",
        default="ancient_free_will_database.json",
        help="Input database file (default: ancient_free_will_database.json)"
    )
    
    parser.add_argument(
        "--output-prefix",
        default="cytoscape",
        help="Prefix for output files (default: cytoscape)"
    )
    
    parser.add_argument(
        "--include-descriptions",
        action="store_true",
        help="Include descriptions in CSV files"
    )
    
    parser.add_argument(
        "--include-sources",
        action="store_true",
        help="Include ancient sources and modern scholarship"
    )
    
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="Export metadata and import instructions"
    )
    
    parser.add_argument(
        "--style-file",
        action="store_true",
        help="Create Cytoscape style file"
    )
    
    args = parser.parse_args()
    
    try:
        # Load database
        db = load_database(args.input)
        
        # Initialize exporter
        exporter = CytoscapeExporter(db)
        
        # Export nodes
        nodes_file = f"{args.output_prefix}_nodes.csv"
        exporter.export_nodes(
            output_file=nodes_file,
            include_descriptions=args.include_descriptions,
            include_sources=args.include_sources
        )
        
        # Export edges
        edges_file = f"{args.output_prefix}_edges.csv"
        exporter.export_edges(
            output_file=edges_file,
            include_descriptions=args.include_descriptions
        )
        
        # Export metadata
        if args.metadata:
            metadata_file = f"{args.output_prefix}_metadata.txt"
            exporter.export_metadata(output_file=metadata_file)
        
        # Export style file
        if args.style_file:
            style_file = f"{args.output_prefix}_style.xml"
            exporter.create_style_file(output_file=style_file)
        
        print("\n" + "="*60)
        print("EXPORT COMPLETE")
        print("="*60)
        print(f"Files created:")
        print(f"  • {nodes_file} - Node data")
        print(f"  • {edges_file} - Edge data")
        
        if args.metadata:
            print(f"  • {metadata_file} - Metadata and instructions")
        
        if args.style_file:
            print(f"  • {style_file} - Cytoscape style file")
        
        print("\nTo import into Cytoscape:")
        print("1. File → Import → Network from File")
        print("2. Select the CSV files")
        print("3. Map the columns as described in the metadata file")
        print("4. Apply the style file if created")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
