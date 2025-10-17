#!/usr/bin/env python3
"""
Semantic Search - EleutherIA Ancient Free Will Database
=======================================================

Perform semantic search across the database using vector embeddings.
Supports interactive queries and metadata filtering.

Usage:
    python semantic_search.py --model gemini --query "arguments against determinism"
    python semantic_search.py --model openai --query "Stoic compatibilism" --filter-school Stoic
    python semantic_search.py --interactive
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Optional imports with error handling
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class SemanticSearcher:
    """Perform semantic search on EleutherIA database."""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model.lower()
        self.api_key = api_key
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the appropriate client based on model."""
        if self.model == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
            if not self.api_key:
                raise ValueError("API key required for Gemini")
            genai.configure(api_key=self.api_key)
            self.client = genai
            
        elif self.model == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai not installed. Run: pip install openai")
            if not self.api_key:
                raise ValueError("API key required for OpenAI")
            openai.api_key = self.api_key
            self.client = openai
            
        else:
            raise ValueError(f"Unsupported model: {self.model}")
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        if self.model == "gemini":
            result = self.client.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
            
        elif self.model == "openai":
            response = self.client.Embedding.create(
                input=query,
                model="text-embedding-3-large"
            )
            return response['data'][0]['embedding']
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def search(self, 
               query: str, 
               nodes: List[Dict], 
               k: int = 10,
               filter_type: Optional[str] = None,
               filter_school: Optional[str] = None,
               filter_period: Optional[str] = None) -> List[Tuple[float, Dict]]:
        """Perform semantic search with optional filtering."""
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)
        
        # Filter nodes if requested
        filtered_nodes = nodes
        
        if filter_type:
            filtered_nodes = [n for n in filtered_nodes if n.get('type') == filter_type]
        
        if filter_school:
            filtered_nodes = [n for n in filtered_nodes if filter_school in n.get('school', '')]
        
        if filter_period:
            filtered_nodes = [n for n in filtered_nodes if n.get('period') == filter_period]
        
        # Calculate similarities
        similarities = []
        
        for node in filtered_nodes:
            if 'embedding' in node and 'embedding_model' in node:
                # Check if embedding was generated with the same model
                if node['embedding_model'] == self.model:
                    similarity = self.cosine_similarity(query_embedding, node['embedding'])
                    similarities.append((similarity, node))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:k]
    
    def format_result(self, similarity: float, node: Dict, show_details: bool = False) -> str:
        """Format search result for display."""
        result = f"[{similarity:.3f}] {node['label']} ({node['type']})"
        
        if node.get('school'):
            result += f" - {node['school']}"
        
        if node.get('period'):
            result += f" - {node['period']}"
        
        if show_details and 'description' in node:
            desc = node['description'][:200] + "..." if len(node['description']) > 200 else node['description']
            result += f"\n  {desc}"
        
        if show_details and 'ancient_sources' in node and node['ancient_sources']:
            sources = "; ".join(node['ancient_sources'][:2])
            result += f"\n  Sources: {sources}"
        
        return result


def load_database(db_path: str) -> Dict:
    """Load the EleutherIA database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    print(f"Loading database from {db_path}...")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    print(f"Loaded {len(db['nodes'])} nodes")
    
    # Check for embeddings
    nodes_with_embeddings = sum(1 for n in db['nodes'] if 'embedding' in n)
    print(f"Nodes with embeddings: {nodes_with_embeddings}")
    
    if nodes_with_embeddings == 0:
        print("Warning: No embeddings found. Run generate_embeddings.py first.")
    
    return db


def interactive_search(searcher: SemanticSearcher, nodes: List[Dict]):
    """Interactive search interface."""
    print("\n" + "="*60)
    print("EleutherIA Semantic Search - Interactive Mode")
    print("="*60)
    print("Commands:")
    print("  /help     - Show this help")
    print("  /filter   - Set filters")
    print("  /clear    - Clear filters")
    print("  /quit     - Exit")
    print("="*60)
    
    # Current filters
    filters = {
        'type': None,
        'school': None,
        'period': None
    }
    
    while True:
        try:
            # Show current filters
            active_filters = [f"{k}={v}" for k, v in filters.items() if v]
            filter_str = f" [Filters: {', '.join(active_filters)}]" if active_filters else ""
            
            query = input(f"\nSearch{filter_str}: ").strip()
            
            if not query:
                continue
            
            # Handle commands
            if query.startswith('/'):
                if query == '/quit':
                    break
                elif query == '/help':
                    print("\nCommands:")
                    print("  /help     - Show this help")
                    print("  /filter   - Set filters")
                    print("  /clear    - Clear filters")
                    print("  /quit     - Exit")
                    continue
                elif query == '/clear':
                    filters = {'type': None, 'school': None, 'period': None}
                    print("Filters cleared.")
                    continue
                elif query == '/filter':
                    print("\nAvailable filters:")
                    print("  type: person, work, concept, argument, debate, controversy, reformulation, event, school, group, argument_framework")
                    print("  school: Stoic, Peripatetic, Academic Skeptic, Epicurean, Patristic, Middle Platonist, etc.")
                    print("  period: Classical Greek, Hellenistic Greek, Roman Republican, Roman Imperial, Patristic, Late Antiquity")
                    
                    filter_type = input("Filter by type (or Enter to skip): ").strip() or None
                    filter_school = input("Filter by school (or Enter to skip): ").strip() or None
                    filter_period = input("Filter by period (or Enter to skip): ").strip() or None
                    
                    filters = {
                        'type': filter_type,
                        'school': filter_school,
                        'period': filter_period
                    }
                    continue
                else:
                    print("Unknown command. Type /help for available commands.")
                    continue
            
            # Perform search
            results = searcher.search(
                query, 
                nodes, 
                k=10,
                filter_type=filters['type'],
                filter_school=filters['school'],
                filter_period=filters['period']
            )
            
            if not results:
                print("No results found.")
                continue
            
            print(f"\nFound {len(results)} results:")
            print("-" * 60)
            
            for i, (similarity, node) in enumerate(results, 1):
                result_text = searcher.format_result(similarity, node, show_details=True)
                print(f"{i:2d}. {result_text}")
                print()
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def get_api_key(model: str) -> Optional[str]:
    """Get API key from environment variables or user input."""
    env_vars = {
        "gemini": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY"
    }
    
    if model in env_vars:
        api_key = os.getenv(env_vars[model])
        if api_key:
            return api_key
        
        # Prompt user for API key
        print(f"API key not found in environment variable {env_vars[model]}")
        api_key = input(f"Enter your {model.upper()} API key: ").strip()
        return api_key if api_key else None
    
    return None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Semantic search for EleutherIA database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python semantic_search.py --model gemini --query "arguments against determinism"
  python semantic_search.py --model openai --query "Stoic compatibilism" --filter-school Stoic
  python semantic_search.py --interactive --model gemini
  python semantic_search.py --model sentence-transformers --query "free will"

Environment Variables:
  GOOGLE_API_KEY    - Google Gemini API key
  OPENAI_API_KEY    - OpenAI API key
        """
    )
    
    parser.add_argument(
        "--model",
        choices=["gemini", "openai"],
        help="Embedding model to use (required for non-interactive mode)"
    )
    
    parser.add_argument(
        "--api-key",
        help="API key for the embedding service (can also use environment variables)"
    )
    
    parser.add_argument(
        "--input",
        default="eleutheria_with_embeddings_gemini.json",
        help="Input database file with embeddings (default: eleutheria_with_embeddings_gemini.json)"
    )
    
    parser.add_argument(
        "--query",
        help="Search query (required for non-interactive mode)"
    )
    
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Number of results to return (default: 10)"
    )
    
    parser.add_argument(
        "--filter-type",
        help="Filter by node type (person, work, concept, argument, etc.)"
    )
    
    parser.add_argument(
        "--filter-school",
        help="Filter by philosophical school (Stoic, Peripatetic, etc.)"
    )
    
    parser.add_argument(
        "--filter-period",
        help="Filter by historical period (Classical Greek, Hellenistic Greek, etc.)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive search mode"
    )
    
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show detailed results with descriptions"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.interactive:
        if not args.model:
            parser.error("--model is required for non-interactive mode")
        if not args.query:
            parser.error("--query is required for non-interactive mode")
    
    try:
        # Load database
        db = load_database(args.input)
        nodes = db['nodes']
        
        # Check if we have embeddings
        nodes_with_embeddings = [n for n in nodes if 'embedding' in n]
        if not nodes_with_embeddings:
            print("Error: No embeddings found in database.")
            print("Run generate_embeddings.py first to create embeddings.")
            sys.exit(1)
        
        # Get API key
        api_key = args.api_key or get_api_key(args.model)
        
        # Initialize searcher
        searcher = SemanticSearcher(args.model, api_key)
        
        if args.interactive:
            # Interactive mode
            interactive_search(searcher, nodes)
        else:
            # Single query mode
            results = searcher.search(
                args.query,
                nodes,
                k=args.k,
                filter_type=args.filter_type,
                filter_school=args.filter_school,
                filter_period=args.filter_period
            )
            
            if not results:
                print("No results found.")
                return
            
            print(f"Search results for: '{args.query}'")
            print("=" * 60)
            
            for i, (similarity, node) in enumerate(results, 1):
                result_text = searcher.format_result(similarity, node, show_details=args.details)
                print(f"{i:2d}. {result_text}")
                print()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
