#!/usr/bin/env python3
"""
Network Analysis - EleutherIA Ancient Free Will Database
========================================================

Perform network analysis on the EleutherIA knowledge graph.
Calculate centrality measures, detect communities, and visualize the network.

Usage:
    python network_analysis.py --input ancient_free_will_database.json
    python network_analysis.py --centrality --community-detection --visualize
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Optional imports with error handling
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class NetworkAnalyzer:
    """Network analysis for EleutherIA knowledge graph."""
    
    def __init__(self, db: Dict):
        self.db = db
        self.G = self._build_graph()
    
    def _build_graph(self) -> nx.Graph:
        """Build NetworkX graph from database."""
        G = nx.Graph()
        
        # Add nodes with attributes
        for node in self.db['nodes']:
            G.add_node(node['id'], **node)
        
        # Add edges with attributes
        for edge in self.db['edges']:
            G.add_edge(edge['source'], edge['target'], **edge)
        
        return G
    
    def basic_statistics(self) -> Dict:
        """Calculate basic network statistics."""
        stats = {
            'nodes': self.G.number_of_nodes(),
            'edges': self.G.number_of_edges(),
            'density': nx.density(self.G),
            'average_clustering': nx.average_clustering(self.G),
            'is_connected': nx.is_connected(self.G),
            'number_of_components': nx.number_connected_components(self.G),
            'average_degree': sum(dict(self.G.degree()).values()) / self.G.number_of_nodes()
        }
        
        if stats['is_connected']:
            stats['diameter'] = nx.diameter(self.G)
            stats['radius'] = nx.radius(self.G)
            stats['average_shortest_path_length'] = nx.average_shortest_path_length(self.G)
        
        return stats
    
    def degree_centrality(self) -> Dict[str, float]:
        """Calculate degree centrality for all nodes."""
        return nx.degree_centrality(self.G)
    
    def betweenness_centrality(self) -> Dict[str, float]:
        """Calculate betweenness centrality for all nodes."""
        return nx.betweenness_centrality(self.G)
    
    def closeness_centrality(self) -> Dict[str, float]:
        """Calculate closeness centrality for all nodes."""
        return nx.closeness_centrality(self.G)
    
    def eigenvector_centrality(self) -> Dict[str, float]:
        """Calculate eigenvector centrality for all nodes."""
        try:
            return nx.eigenvector_centrality(self.G, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            print("Warning: Eigenvector centrality failed to converge")
            return {}
    
    def pagerank(self) -> Dict[str, float]:
        """Calculate PageRank for all nodes."""
        return nx.pagerank(self.G)
    
    def community_detection(self, algorithm: str = 'louvain') -> Dict[str, int]:
        """Detect communities in the network."""
        if algorithm == 'louvain':
            try:
                import community as community_louvain
                communities = community_louvain.best_partition(self.G)
                return communities
            except ImportError:
                print("Warning: python-louvain not installed. Using greedy modularity instead.")
                algorithm = 'greedy'
        
        if algorithm == 'greedy':
            communities = nx.community.greedy_modularity_communities(self.G)
            # Convert to node -> community mapping
            community_dict = {}
            for i, community in enumerate(communities):
                for node in community:
                    community_dict[node] = i
            return community_dict
        
        return {}
    
    def find_most_central_nodes(self, 
                               centrality: Dict[str, float], 
                               top_k: int = 10) -> List[Tuple[str, float, Dict]]:
        """Find most central nodes with their attributes."""
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for node_id, centrality_score in sorted_nodes[:top_k]:
            node_attrs = self.G.nodes[node_id]
            results.append((node_id, centrality_score, node_attrs))
        
        return results
    
    def analyze_by_type(self) -> Dict[str, Dict]:
        """Analyze network properties by node type."""
        type_stats = {}
        
        for node_id in self.G.nodes():
            node_attrs = self.G.nodes[node_id]
            node_type = node_attrs.get('type', 'unknown')
            
            if node_type not in type_stats:
                type_stats[node_type] = {
                    'count': 0,
                    'total_degree': 0,
                    'avg_clustering': 0,
                    'nodes': []
                }
            
            type_stats[node_type]['count'] += 1
            type_stats[node_type]['total_degree'] += self.G.degree(node_id)
            type_stats[node_type]['nodes'].append(node_id)
        
        # Calculate averages
        for node_type in type_stats:
            count = type_stats[node_type]['count']
            type_stats[node_type]['avg_degree'] = type_stats[node_type]['total_degree'] / count
            
            # Calculate average clustering for this type
            nodes = type_stats[node_type]['nodes']
            clustering_values = [nx.clustering(self.G, node) for node in nodes]
            type_stats[node_type]['avg_clustering'] = np.mean(clustering_values)
        
        return type_stats
    
    def find_bridges(self) -> List[Tuple[str, str]]:
        """Find bridge edges (edges whose removal increases components)."""
        return list(nx.bridges(self.G))
    
    def find_cut_nodes(self) -> List[str]:
        """Find cut nodes (nodes whose removal increases components)."""
        return list(nx.articulation_points(self.G))
    
    def shortest_paths(self, source: str, target: str) -> List[List[str]]:
        """Find shortest paths between two nodes."""
        try:
            return list(nx.all_shortest_paths(self.G, source, target))
        except nx.NetworkXNoPath:
            return []
    
    def visualize_network(self, 
                         output_file: str = 'network_visualization.png',
                         layout: str = 'spring',
                         node_size_factor: float = 100,
                         show_labels: bool = False,
                         color_by: str = 'type') -> None:
        """Visualize the network."""
        
        # Set up the plot
        plt.figure(figsize=(15, 12))
        
        # Choose layout
        if layout == 'spring':
            pos = nx.spring_layout(self.G, k=1, iterations=50)
        elif layout == 'circular':
            pos = nx.circular_layout(self.G)
        elif layout == 'random':
            pos = nx.random_layout(self.G)
        else:
            pos = nx.spring_layout(self.G, k=1, iterations=50)
        
        # Color mapping
        if color_by == 'type':
            type_colors = {
                'person': '#FF6B6B',
                'concept': '#4ECDC4', 
                'argument': '#45B7D1',
                'work': '#96CEB4',
                'debate': '#FECA57',
                'controversy': '#FF9FF3',
                'reformulation': '#54A0FF',
                'event': '#5F27CD',
                'school': '#00D2D3',
                'group': '#FF6348',
                'argument_framework': '#2ED573'
            }
            
            node_colors = []
            for node_id in self.G.nodes():
                node_type = self.G.nodes[node_id].get('type', 'unknown')
                node_colors.append(type_colors.get(node_type, '#999999'))
        
        elif color_by == 'degree':
            degrees = dict(self.G.degree())
            max_degree = max(degrees.values())
            node_colors = [degrees[node] / max_degree for node in self.G.nodes()]
        
        else:
            node_colors = '#4ECDC4'  # Default color
        
        # Node sizes based on degree
        degrees = dict(self.G.degree())
        node_sizes = [degrees[node] * node_size_factor for node in self.G.nodes()]
        
        # Draw the network
        nx.draw_networkx_nodes(
            self.G, pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.8
        )
        
        nx.draw_networkx_edges(
            self.G, pos,
            alpha=0.3,
            edge_color='gray'
        )
        
        if show_labels:
            # Only show labels for high-degree nodes
            high_degree_nodes = [node for node, degree in degrees.items() if degree > 5]
            labels = {node: self.G.nodes[node].get('label', node) for node in high_degree_nodes}
            nx.draw_networkx_labels(self.G, pos, labels, font_size=8)
        
        plt.title(f"EleutherIA Knowledge Graph\n({self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges)")
        plt.axis('off')
        
        # Add legend for type coloring
        if color_by == 'type':
            legend_elements = []
            for node_type, color in type_colors.items():
                if any(self.G.nodes[node].get('type') == node_type for node in self.G.nodes()):
                    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                                   markerfacecolor=color, markersize=10, label=node_type))
            plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Network visualization saved to {output_file}")
    
    def export_statistics(self, output_file: str = 'network_statistics.csv') -> None:
        """Export network statistics to CSV."""
        if not PANDAS_AVAILABLE:
            print("Warning: pandas not available. Cannot export to CSV.")
            return
        
        # Calculate all centrality measures
        degree_cent = self.degree_centrality()
        betweenness_cent = self.betweenness_centrality()
        closeness_cent = self.closeness_centrality()
        eigenvector_cent = self.eigenvector_centrality()
        pagerank_scores = self.pagerank()
        
        # Create DataFrame
        data = []
        for node_id in self.G.nodes():
            node_attrs = self.G.nodes[node_id]
            data.append({
                'node_id': node_id,
                'label': node_attrs.get('label', ''),
                'type': node_attrs.get('type', ''),
                'school': node_attrs.get('school', ''),
                'period': node_attrs.get('period', ''),
                'degree': self.G.degree(node_id),
                'degree_centrality': degree_cent.get(node_id, 0),
                'betweenness_centrality': betweenness_cent.get(node_id, 0),
                'closeness_centrality': closeness_cent.get(node_id, 0),
                'eigenvector_centrality': eigenvector_cent.get(node_id, 0),
                'pagerank': pagerank_scores.get(node_id, 0)
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        print(f"Network statistics exported to {output_file}")


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
        description="Network analysis for EleutherIA database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python network_analysis.py --input ancient_free_will_database.json
  python network_analysis.py --centrality --community-detection --visualize
  python network_analysis.py --export-csv --output-stats network_stats.csv
        """
    )
    
    parser.add_argument(
        "--input",
        default="ancient_free_will_database.json",
        help="Input database file (default: ancient_free_will_database.json)"
    )
    
    parser.add_argument(
        "--centrality",
        action="store_true",
        help="Calculate centrality measures"
    )
    
    parser.add_argument(
        "--community-detection",
        action="store_true",
        help="Perform community detection"
    )
    
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Create network visualization"
    )
    
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export statistics to CSV"
    )
    
    parser.add_argument(
        "--output-stats",
        default="network_statistics.csv",
        help="Output file for statistics (default: network_statistics.csv)"
    )
    
    parser.add_argument(
        "--output-viz",
        default="network_visualization.png",
        help="Output file for visualization (default: network_visualization.png)"
    )
    
    parser.add_argument(
        "--layout",
        choices=["spring", "circular", "random"],
        default="spring",
        help="Layout algorithm for visualization (default: spring)"
    )
    
    parser.add_argument(
        "--color-by",
        choices=["type", "degree"],
        default="type",
        help="Color nodes by type or degree (default: type)"
    )
    
    parser.add_argument(
        "--show-labels",
        action="store_true",
        help="Show node labels in visualization"
    )
    
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of top nodes to show (default: 10)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load database
        db = load_database(args.input)
        
        # Initialize analyzer
        analyzer = NetworkAnalyzer(db)
        
        # Basic statistics
        print("\n" + "="*60)
        print("NETWORK STATISTICS")
        print("="*60)
        
        stats = analyzer.basic_statistics()
        for key, value in stats.items():
            print(f"{key:30s}: {value}")
        
        # Centrality analysis
        if args.centrality:
            print("\n" + "="*60)
            print("CENTRALITY ANALYSIS")
            print("="*60)
            
            # Degree centrality
            degree_cent = analyzer.degree_centrality()
            top_degree = analyzer.find_most_central_nodes(degree_cent, args.top_k)
            
            print(f"\nTop {args.top_k} nodes by degree centrality:")
            for i, (node_id, centrality, attrs) in enumerate(top_degree, 1):
                print(f"{i:2d}. {attrs.get('label', node_id)} ({attrs.get('type', 'unknown')}) - {centrality:.3f}")
            
            # Betweenness centrality
            betweenness_cent = analyzer.betweenness_centrality()
            top_betweenness = analyzer.find_most_central_nodes(betweenness_cent, args.top_k)
            
            print(f"\nTop {args.top_k} nodes by betweenness centrality:")
            for i, (node_id, centrality, attrs) in enumerate(top_betweenness, 1):
                print(f"{i:2d}. {attrs.get('label', node_id)} ({attrs.get('type', 'unknown')}) - {centrality:.3f}")
            
            # Closeness centrality
            closeness_cent = analyzer.closeness_centrality()
            top_closeness = analyzer.find_most_central_nodes(closeness_cent, args.top_k)
            
            print(f"\nTop {args.top_k} nodes by closeness centrality:")
            for i, (node_id, centrality, attrs) in enumerate(top_closeness, 1):
                print(f"{i:2d}. {attrs.get('label', node_id)} ({attrs.get('type', 'unknown')}) - {centrality:.3f}")
        
        # Community detection
        if args.community_detection:
            print("\n" + "="*60)
            print("COMMUNITY DETECTION")
            print("="*60)
            
            communities = analyzer.community_detection()
            if communities:
                # Count communities
                community_counts = Counter(communities.values())
                print(f"Found {len(community_counts)} communities")
                
                # Show largest communities
                for community_id, count in community_counts.most_common(5):
                    community_nodes = [node for node, comm in communities.items() if comm == community_id]
                    print(f"\nCommunity {community_id} ({count} nodes):")
                    
                    # Show top nodes in this community
                    community_degrees = [(node, analyzer.G.degree(node)) for node in community_nodes]
                    community_degrees.sort(key=lambda x: x[1], reverse=True)
                    
                    for node_id, degree in community_degrees[:5]:
                        node_attrs = analyzer.G.nodes[node_id]
                        print(f"  • {node_attrs.get('label', node_id)} ({node_attrs.get('type', 'unknown')}) - degree {degree}")
        
        # Type analysis
        print("\n" + "="*60)
        print("ANALYSIS BY NODE TYPE")
        print("="*60)
        
        type_stats = analyzer.analyze_by_type()
        for node_type, stats in sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"\n{node_type.upper()}:")
            print(f"  Count: {stats['count']}")
            print(f"  Average degree: {stats['avg_degree']:.2f}")
            print(f"  Average clustering: {stats['avg_clustering']:.3f}")
        
        # Visualization
        if args.visualize:
            print("\n" + "="*60)
            print("CREATING VISUALIZATION")
            print("="*60)
            
            analyzer.visualize_network(
                output_file=args.output_viz,
                layout=args.layout,
                color_by=args.color_by,
                show_labels=args.show_labels
            )
        
        # Export statistics
        if args.export_csv:
            print("\n" + "="*60)
            print("EXPORTING STATISTICS")
            print("="*60)
            
            analyzer.export_statistics(args.output_stats)
        
        print("\nAnalysis complete!")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
