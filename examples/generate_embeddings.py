#!/usr/bin/env python3
"""
Generate Embeddings - EleutherIA Ancient Free Will Database
===========================================================

Generate vector embeddings for all nodes in the database using various AI models.
Supports Google Gemini, OpenAI, Cohere, and sentence-transformers.

Usage:
    python generate_embeddings.py --model gemini --api-key YOUR_KEY
    python generate_embeddings.py --model openai --api-key YOUR_KEY
    python generate_embeddings.py --model sentence-transformers
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingGenerator:
    """Generate embeddings for EleutherIA database nodes."""
    
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
            
        elif self.model == "cohere":
            if not COHERE_AVAILABLE:
                raise ImportError("cohere not installed. Run: pip install cohere")
            if not self.api_key:
                raise ValueError("API key required for Cohere")
            self.client = cohere.Client(self.api_key)
            
        elif self.model == "sentence-transformers":
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
            # Use a model that supports Greek text
            self.client = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
        else:
            raise ValueError(f"Unsupported model: {self.model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if self.model == "gemini":
            result = self.client.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
            
        elif self.model == "openai":
            response = self.client.Embedding.create(
                input=text,
                model="text-embedding-3-large"
            )
            return response['data'][0]['embedding']
            
        elif self.model == "cohere":
            response = self.client.embed(
                texts=[text],
                model="embed-multilingual-v3.0"
            )
            return response.embeddings[0]
            
        elif self.model == "sentence-transformers":
            return self.client.encode(text).tolist()
    
    def prepare_text(self, node: Dict) -> str:
        """Prepare text for embedding by combining relevant fields."""
        text_parts = []
        
        # Add label
        text_parts.append(node['label'])
        
        # Add description
        if 'description' in node:
            text_parts.append(node['description'])
        
        # Add ancient sources (first 3)
        if 'ancient_sources' in node and node['ancient_sources']:
            sources = node['ancient_sources'][:3]  # Limit to first 3
            text_parts.append("Sources: " + "; ".join(sources))
        
        # Add modern scholarship (first 3)
        if 'modern_scholarship' in node and node['modern_scholarship']:
            scholarship = node['modern_scholarship'][:3]  # Limit to first 3
            text_parts.append("Scholarship: " + "; ".join(scholarship))
        
        # Add key concepts
        if 'key_concepts' in node and node['key_concepts']:
            concepts = "; ".join(node['key_concepts'])
            text_parts.append(f"Concepts: {concepts}")
        
        # Add school/period context
        if 'school' in node and node['school']:
            text_parts.append(f"School: {node['school']}")
        
        if 'period' in node and node['period']:
            text_parts.append(f"Period: {node['period']}")
        
        return " | ".join(text_parts)
    
    def generate_embeddings(self, nodes: List[Dict], batch_size: int = 10) -> List[Dict]:
        """Generate embeddings for all nodes with progress tracking."""
        total_nodes = len(nodes)
        processed_nodes = []
        
        print(f"Generating embeddings for {total_nodes} nodes using {self.model}...")
        print(f"Batch size: {batch_size}")
        print()
        
        start_time = time.time()
        
        for i, node in enumerate(nodes):
            try:
                # Prepare text for embedding
                text = self.prepare_text(node)
                
                # Generate embedding
                embedding = self.generate_embedding(text)
                
                # Add embedding to node
                node_with_embedding = node.copy()
                node_with_embedding['embedding'] = embedding
                node_with_embedding['embedding_model'] = self.model
                node_with_embedding['embedding_text'] = text
                
                processed_nodes.append(node_with_embedding)
                
                # Progress tracking
                if (i + 1) % batch_size == 0 or (i + 1) == total_nodes:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    eta = (total_nodes - i - 1) / rate if rate > 0 else 0
                    
                    print(f"Progress: {i + 1}/{total_nodes} ({((i + 1)/total_nodes)*100:.1f}%) "
                          f"- Rate: {rate:.1f} nodes/sec - ETA: {eta:.0f}s")
                
                # Rate limiting for API calls
                if self.model in ["gemini", "openai", "cohere"]:
                    time.sleep(0.1)  # 100ms delay between API calls
                    
            except Exception as e:
                print(f"Error processing node {node.get('id', 'unknown')}: {e}")
                # Add node without embedding
                processed_nodes.append(node)
        
        total_time = time.time() - start_time
        print(f"\nCompleted in {total_time:.1f} seconds")
        print(f"Average rate: {total_nodes/total_time:.1f} nodes/second")
        
        return processed_nodes


def load_database(db_path: str) -> Dict:
    """Load the EleutherIA database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    print(f"Loading database from {db_path}...")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    print(f"Loaded {len(db['nodes'])} nodes and {len(db['edges'])} edges")
    return db


def save_database(db: Dict, output_path: str):
    """Save the database with embeddings."""
    print(f"Saving database with embeddings to {output_path}...")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    
    print(f"Database saved successfully")


def get_api_key(model: str) -> Optional[str]:
    """Get API key from environment variables or user input."""
    env_vars = {
        "gemini": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY", 
        "cohere": "COHERE_API_KEY"
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
        description="Generate embeddings for EleutherIA database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_embeddings.py --model gemini --api-key YOUR_KEY
  python generate_embeddings.py --model openai --api-key YOUR_KEY
  python generate_embeddings.py --model sentence-transformers
  python generate_embeddings.py --model cohere --api-key YOUR_KEY

Environment Variables:
  GOOGLE_API_KEY    - Google Gemini API key
  OPENAI_API_KEY    - OpenAI API key
  COHERE_API_KEY    - Cohere API key
        """
    )
    
    parser.add_argument(
        "--model",
        choices=["gemini", "openai", "cohere", "sentence-transformers"],
        required=True,
        help="Embedding model to use"
    )
    
    parser.add_argument(
        "--api-key",
        help="API key for the embedding service (can also use environment variables)"
    )
    
    parser.add_argument(
        "--input",
        default="ancient_free_will_database.json",
        help="Input database file (default: ancient_free_will_database.json)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file (default: eleutheria_with_embeddings_{model}.json)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing (default: 10)"
    )
    
    parser.add_argument(
        "--subset",
        type=int,
        help="Process only first N nodes (for testing)"
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or get_api_key(args.model)
    
    # Set output file
    if not args.output:
        args.output = f"eleutheria_with_embeddings_{args.model}.json"
    
    try:
        # Load database
        db = load_database(args.input)
        
        # Get nodes to process
        nodes = db['nodes']
        if args.subset:
            nodes = nodes[:args.subset]
            print(f"Processing subset: {len(nodes)} nodes")
        
        # Generate embeddings
        generator = EmbeddingGenerator(args.model, api_key)
        nodes_with_embeddings = generator.generate_embeddings(nodes, args.batch_size)
        
        # Update database
        db['nodes'] = nodes_with_embeddings
        
        # Add metadata about embeddings
        if 'embedding_metadata' not in db:
            db['embedding_metadata'] = {}
        
        db['embedding_metadata'][args.model] = {
            'model': args.model,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_nodes': len(nodes_with_embeddings),
            'nodes_with_embeddings': sum(1 for n in nodes_with_embeddings if 'embedding' in n),
            'batch_size': args.batch_size
        }
        
        # Save database
        save_database(db, args.output)
        
        # Summary
        nodes_with_embeddings_count = sum(1 for n in nodes_with_embeddings if 'embedding' in n)
        print(f"\nSummary:")
        print(f"  Model: {args.model}")
        print(f"  Total nodes: {len(nodes_with_embeddings)}")
        print(f"  Nodes with embeddings: {nodes_with_embeddings_count}")
        print(f"  Output file: {args.output}")
        
        if nodes_with_embeddings_count < len(nodes_with_embeddings):
            failed_count = len(nodes_with_embeddings) - nodes_with_embeddings_count
            print(f"  Failed embeddings: {failed_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
