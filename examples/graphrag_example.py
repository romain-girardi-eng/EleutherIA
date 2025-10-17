#!/usr/bin/env python3
"""
GraphRAG Example - EleutherIA Ancient Free Will Database
========================================================

Complete GraphRAG pipeline demonstration using EleutherIA database.
Combines semantic search with graph traversal for comprehensive answers.

Usage:
    python graphrag_example.py --model gemini --query "How did early Christians respond to Stoic determinism?"
    python graphrag_example.py --interactive --model openai
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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


class GraphRAGPipeline:
    """Complete GraphRAG pipeline for EleutherIA database."""
    
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
    
    def semantic_search(self, query: str, nodes: List[Dict], k: int = 10) -> List[Tuple[float, Dict]]:
        """Perform semantic search to find relevant nodes."""
        query_embedding = self.generate_query_embedding(query)
        
        similarities = []
        for node in nodes:
            if 'embedding' in node and 'embedding_model' in node:
                if node['embedding_model'] == self.model:
                    similarity = self.cosine_similarity(query_embedding, node['embedding'])
                    similarities.append((similarity, node))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:k]
    
    def expand_with_graph_traversal(self, 
                                   initial_nodes: List[Dict], 
                                   edges: List[Dict], 
                                   max_depth: int = 2) -> Set[str]:
        """Expand initial nodes using graph traversal."""
        expanded_ids = set()
        
        # Add initial nodes
        for node in initial_nodes:
            expanded_ids.add(node['id'])
        
        # Traverse graph
        current_level = [node['id'] for node in initial_nodes]
        
        for depth in range(max_depth):
            next_level = set()
            
            for node_id in current_level:
                # Find connected nodes
                for edge in edges:
                    if edge['source'] == node_id:
                        next_level.add(edge['target'])
                    elif edge['target'] == node_id:
                        next_level.add(edge['source'])
            
            # Add to expanded set
            expanded_ids.update(next_level)
            current_level = list(next_level)
        
        return expanded_ids
    
    def build_context(self, 
                      expanded_ids: Set[str], 
                      nodes: List[Dict], 
                      max_context: int = 15) -> str:
        """Build context string from expanded nodes."""
        context_parts = ["# Ancient Philosophy Knowledge Base\n"]
        
        # Get nodes by ID
        expanded_nodes = [n for n in nodes if n['id'] in expanded_ids]
        
        # Sort by type and importance
        type_priority = {
            'person': 1,
            'argument': 2,
            'concept': 3,
            'work': 4,
            'debate': 5,
            'controversy': 6,
            'reformulation': 7,
            'event': 8,
            'school': 9,
            'group': 10,
            'argument_framework': 11
        }
        
        expanded_nodes.sort(key=lambda x: type_priority.get(x['type'], 99))
        
        # Limit context size
        expanded_nodes = expanded_nodes[:max_context]
        
        for node in expanded_nodes:
            context_parts.append(f"## {node['label']} ({node['type']})")
            context_parts.append(node['description'])
            
            if 'ancient_sources' in node and node['ancient_sources']:
                sources = "; ".join(node['ancient_sources'][:2])
                context_parts.append(f"**Sources:** {sources}")
            
            if 'school' in node and node['school']:
                context_parts.append(f"**School:** {node['school']}")
            
            if 'period' in node and node['period']:
                context_parts.append(f"**Period:** {node['period']}")
            
            context_parts.append("")  # Empty line
        
        return "\n".join(context_parts)
    
    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM with context."""
        prompt = f"""You are a scholar of ancient philosophy. Answer the following question using ONLY the provided knowledge base. Always cite your sources using the node labels.

Knowledge Base:
{context}

Question: {query}

Answer (with citations):"""

        if self.model == "gemini":
            model = self.client.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            return response.text
            
        elif self.model == "openai":
            response = self.client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a scholar of ancient philosophy. Answer questions using only the provided knowledge base and always cite your sources."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
    
    def answer_question(self, 
                       query: str, 
                       db: Dict, 
                       semantic_k: int = 10,
                       graph_depth: int = 2,
                       max_context: int = 15) -> str:
        """Complete GraphRAG pipeline to answer a question."""
        
        print(f"Question: {query}")
        print("=" * 60)
        
        # Step 1: Semantic search
        print("Step 1: Performing semantic search...")
        semantic_results = self.semantic_search(query, db['nodes'], k=semantic_k)
        
        if not semantic_results:
            return "No relevant information found in the database."
        
        print(f"Found {len(semantic_results)} semantically relevant nodes")
        
        # Step 2: Graph expansion
        print("Step 2: Expanding with graph traversal...")
        initial_nodes = [node for _, node in semantic_results]
        expanded_ids = self.expand_with_graph_traversal(
            initial_nodes, 
            db['edges'], 
            max_depth=graph_depth
        )
        
        print(f"Expanded to {len(expanded_ids)} nodes through graph traversal")
        
        # Step 3: Build context
        print("Step 3: Building context...")
        context = self.build_context(expanded_ids, db['nodes'], max_context)
        
        # Step 4: Generate answer
        print("Step 4: Generating answer with LLM...")
        answer = self.generate_answer(query, context)
        
        return answer


def load_database(db_path: str) -> Dict:
    """Load the EleutherIA database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    print(f"Loading database from {db_path}...")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    print(f"Loaded {len(db['nodes'])} nodes and {len(db['edges'])} edges")
    
    # Check for embeddings
    nodes_with_embeddings = sum(1 for n in db['nodes'] if 'embedding' in n)
    print(f"Nodes with embeddings: {nodes_with_embeddings}")
    
    if nodes_with_embeddings == 0:
        print("Warning: No embeddings found. Run generate_embeddings.py first.")
    
    return db


def interactive_mode(pipeline: GraphRAGPipeline, db: Dict):
    """Interactive GraphRAG interface."""
    print("\n" + "="*60)
    print("EleutherIA GraphRAG - Interactive Mode")
    print("="*60)
    print("Ask questions about ancient free will debates!")
    print("Commands:")
    print("  /help     - Show this help")
    print("  /quit     - Exit")
    print("="*60)
    
    while True:
        try:
            query = input("\nQuestion: ").strip()
            
            if not query:
                continue
            
            # Handle commands
            if query.startswith('/'):
                if query == '/quit':
                    break
                elif query == '/help':
                    print("\nCommands:")
                    print("  /help     - Show this help")
                    print("  /quit     - Exit")
                    print("\nExample questions:")
                    print("  How did early Christians respond to Stoic determinism?")
                    print("  What is the difference between Aristotelian and Stoic views of freedom?")
                    print("  Who influenced Carneades' arguments against determinism?")
                    print("  What is the cylinder analogy in Stoic philosophy?")
                    continue
                else:
                    print("Unknown command. Type /help for available commands.")
                    continue
            
            # Generate answer
            answer = pipeline.answer_question(query, db)
            
            print("\nAnswer:")
            print("-" * 60)
            print(answer)
            print("-" * 60)
            
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
        description="GraphRAG pipeline for EleutherIA database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python graphrag_example.py --model gemini --query "How did early Christians respond to Stoic determinism?"
  python graphrag_example.py --model openai --query "What is Aristotelian eph' hêmin?"
  python graphrag_example.py --interactive --model gemini

Environment Variables:
  GOOGLE_API_KEY    - Google Gemini API key
  OPENAI_API_KEY    - OpenAI API key
        """
    )
    
    parser.add_argument(
        "--model",
        choices=["gemini", "openai"],
        help="LLM model to use (required for non-interactive mode)"
    )
    
    parser.add_argument(
        "--api-key",
        help="API key for the LLM service (can also use environment variables)"
    )
    
    parser.add_argument(
        "--input",
        default="eleutheria_with_embeddings_gemini.json",
        help="Input database file with embeddings (default: eleutheria_with_embeddings_gemini.json)"
    )
    
    parser.add_argument(
        "--query",
        help="Question to answer (required for non-interactive mode)"
    )
    
    parser.add_argument(
        "--semantic-k",
        type=int,
        default=10,
        help="Number of nodes for semantic search (default: 10)"
    )
    
    parser.add_argument(
        "--graph-depth",
        type=int,
        default=2,
        help="Depth for graph traversal (default: 2)"
    )
    
    parser.add_argument(
        "--max-context",
        type=int,
        default=15,
        help="Maximum number of nodes in context (default: 15)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive mode"
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
        
        # Check if we have embeddings
        nodes_with_embeddings = [n for n in db['nodes'] if 'embedding' in n]
        if not nodes_with_embeddings:
            print("Error: No embeddings found in database.")
            print("Run generate_embeddings.py first to create embeddings.")
            sys.exit(1)
        
        # Get API key
        api_key = args.api_key or get_api_key(args.model)
        
        # Initialize pipeline
        pipeline = GraphRAGPipeline(args.model, api_key)
        
        if args.interactive:
            # Interactive mode
            interactive_mode(pipeline, db)
        else:
            # Single question mode
            answer = pipeline.answer_question(
                args.query,
                db,
                semantic_k=args.semantic_k,
                graph_depth=args.graph_depth,
                max_context=args.max_context
            )
            
            print("\nAnswer:")
            print("-" * 60)
            print(answer)
            print("-" * 60)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
