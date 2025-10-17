#!/usr/bin/env python3
"""
Knowledge Graph Embeddings Generator for Ancient Free Will Database

This script generates Gemini embeddings for all Knowledge Graph nodes (persons, works, 
concepts, arguments) to enable semantic search and similarity matching across the 
graph structure.

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import json
import logging
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
KG_PATH = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/ancient_free_will_database.json")
EMBEDDINGS_OUTPUT_PATH = Path("/Users/romaingirardi/Documents/Ancient Free Will Database/kg_embeddings.json")

# Gemini configuration from environment
GEMINI_MODEL = os.getenv('EMBEDDING_MODEL', 'gemini-embedding-001')
EMBEDDING_DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', '3072'))


class KnowledgeGraphEmbeddingGenerator:
    """Generates embeddings for Knowledge Graph nodes using Gemini."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the embedding generator."""
        self.api_key = api_key
        self.genai_client = None
        self.embeddings_cache = {}
        self.processed_count = 0
        self.total_count = 0
        
    def configure_gemini(self) -> None:
        """Configure Gemini API client."""
        if not self.api_key:
            # Get from environment
            self.api_key = os.getenv('GEMINI_API_KEY')
            
        if not self.api_key:
            logger.error("Gemini API key not found. Please set GEMINI_API_KEY environment variable.")
            logger.error("Run: python3 setup_environment.py --api-key your_key")
            raise ValueError("Gemini API key required")
            
        genai.configure(api_key=self.api_key)
        self.genai_client = genai.GenerativeModel('gemini-pro')
        
        logger.info("Gemini API configured successfully")
        
    def load_knowledge_graph(self) -> Dict:
        """Load the Knowledge Graph from JSON file."""
        logger.info("Loading Knowledge Graph...")
        
        with open(KG_PATH, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)
            
        logger.info(f"Loaded Knowledge Graph with {len(kg_data.get('nodes', []))} nodes and {len(kg_data.get('edges', []))} edges")
        return kg_data
        
    def create_node_text(self, node: Dict) -> str:
        """Create comprehensive text representation of a node for embedding."""
        node_type = node.get('type', '')
        label = node.get('label', '')
        
        # Base text with label and type
        text_parts = [f"{node_type.title()}: {label}"]
        
        # Add description if available
        if 'description' in node and node['description']:
            text_parts.append(f"Description: {node['description']}")
            
        # Add key concepts for concept nodes
        if node_type == 'concept' and 'key_concepts' in node:
            concepts = node['key_concepts']
            if isinstance(concepts, list):
                text_parts.append(f"Key concepts: {', '.join(concepts)}")
                
        # Add position for argument nodes
        if node_type == 'argument' and 'position_on_free_will' in node:
            text_parts.append(f"Position: {node['position_on_free_will']}")
            
        # Add historical importance
        if 'historical_importance' in node and node['historical_importance']:
            text_parts.append(f"Historical importance: {node['historical_importance']}")
            
        # Add ancient sources
        if 'ancient_sources' in node and node['ancient_sources']:
            sources = node['ancient_sources']
            if isinstance(sources, list):
                text_parts.append(f"Ancient sources: {', '.join(sources[:3])}")  # Limit to first 3
                
        # Add modern scholarship
        if 'modern_scholarship' in node and node['modern_scholarship']:
            scholarship = node['modern_scholarship']
            if isinstance(scholarship, list):
                # Extract author names from citations
                authors = []
                for ref in scholarship[:2]:  # Limit to first 2
                    if isinstance(ref, str) and '(' in ref:
                        author = ref.split('(')[0].strip()
                        authors.append(author)
                if authors:
                    text_parts.append(f"Modern scholarship: {', '.join(authors)}")
                    
        # Add dates and period for persons
        if node_type == 'person':
            if 'dates' in node and node['dates']:
                text_parts.append(f"Dates: {node['dates']}")
            if 'period' in node and node['period']:
                text_parts.append(f"Period: {node['period']}")
            if 'school' in node and node['school']:
                text_parts.append(f"School: {node['school']}")
                
        # Add dates and period for works
        if node_type == 'work':
            if 'dates' in node and node['dates']:
                text_parts.append(f"Dates: {node['dates']}")
            if 'period' in node and node['period']:
                text_parts.append(f"Period: {node['period']}")
                
        return " | ".join(text_parts)
        
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for given text using Gemini."""
        try:
            # Create hash for caching
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            
            # Check cache first
            if text_hash in self.embeddings_cache:
                return self.embeddings_cache[text_hash]
                
            # Generate embedding with maximum dimensions
            result = genai.embed_content(
                model=GEMINI_MODEL,
                content=text,
                task_type="retrieval_document",
                output_dimensionality=3072
            )
            
            embedding = result['embedding']
            
            # Cache the result
            self.embeddings_cache[text_hash] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
            
    async def process_nodes(self, nodes: List[Dict]) -> Dict[str, Dict]:
        """Process all nodes and generate embeddings."""
        logger.info(f"Processing {len(nodes)} nodes for embedding generation...")
        
        self.total_count = len(nodes)
        self.processed_count = 0
        
        node_embeddings = {}
        
        for i, node in enumerate(nodes):
            try:
                # Create text representation
                node_text = self.create_node_text(node)
                
                # Generate embedding
                embedding = self.generate_embedding(node_text)
                
                if embedding:
                    node_embeddings[node['id']] = {
                        'node_id': node['id'],
                        'node_type': node.get('type', ''),
                        'label': node.get('label', ''),
                        'text_representation': node_text,
                        'embedding': embedding,
                        'embedding_model': GEMINI_MODEL,
                        'embedding_dimensions': EMBEDDING_DIMENSIONS,
                        'text_hash': hashlib.md5(node_text.encode('utf-8')).hexdigest(),
                        'generated_at': time.time()
                    }
                    
                self.processed_count += 1
                
                # Progress logging
                if self.processed_count % 10 == 0:
                    logger.info(f"Processed {self.processed_count}/{self.total_count} nodes ({self.processed_count/self.total_count*100:.1f}%)")
                    
                # Rate limiting - Gemini has rate limits
                await asyncio.sleep(0.1)  # 100ms delay between requests
                
            except Exception as e:
                logger.error(f"Error processing node {node.get('id', 'unknown')}: {e}")
                continue
                
        logger.info(f"Completed processing {self.processed_count}/{self.total_count} nodes")
        return node_embeddings
        
    def save_embeddings(self, embeddings: Dict[str, Dict]) -> None:
        """Save embeddings to JSON file."""
        logger.info(f"Saving {len(embeddings)} embeddings to {EMBEDDINGS_OUTPUT_PATH}")
        
        output_data = {
            'metadata': {
                'total_embeddings': len(embeddings),
                'embedding_model': GEMINI_MODEL,
                'embedding_dimensions': EMBEDDING_DIMENSIONS,
                'generated_at': time.time(),
                'generated_by': 'KnowledgeGraphEmbeddingGenerator',
                'description': 'Gemini embeddings for Ancient Free Will Database Knowledge Graph nodes'
            },
            'embeddings': embeddings
        }
        
        with open(EMBEDDINGS_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Embeddings saved successfully to {EMBEDDINGS_OUTPUT_PATH}")
        
    async def generate_edge_embeddings(self, edges: List[Dict], node_embeddings: Dict[str, Dict]) -> Dict[str, Dict]:
        """Generate embeddings for edges based on connected nodes."""
        logger.info(f"Generating embeddings for {len(edges)} edges...")
        
        edge_embeddings = {}
        
        for edge in edges:
            try:
                source_id = edge.get('source')
                target_id = edge.get('target')
                relation = edge.get('relation', '')
                description = edge.get('description', '')
                
                # Get source and target node embeddings
                source_embedding = node_embeddings.get(source_id, {}).get('embedding')
                target_embedding = node_embeddings.get(target_id, {}).get('embedding')
                
                if source_embedding and target_embedding:
                    # Create edge text representation
                    edge_text = f"Relationship: {relation} | Description: {description}"
                    
                    # Generate embedding for the edge
                    edge_embedding = self.generate_embedding(edge_text)
                    
                    if edge_embedding:
                        edge_embeddings[edge['id']] = {
                            'edge_id': edge['id'],
                            'source_id': source_id,
                            'target_id': target_id,
                            'relation': relation,
                            'description': description,
                            'text_representation': edge_text,
                            'embedding': edge_embedding,
                            'embedding_model': GEMINI_MODEL,
                            'embedding_dimensions': EMBEDDING_DIMENSIONS,
                            'text_hash': hashlib.md5(edge_text.encode('utf-8')).hexdigest(),
                            'generated_at': time.time()
                        }
                        
            except Exception as e:
                logger.error(f"Error processing edge {edge.get('id', 'unknown')}: {e}")
                continue
                
        logger.info(f"Generated {len(edge_embeddings)} edge embeddings")
        return edge_embeddings
        
    async def run_generation(self) -> None:
        """Run the complete embedding generation process."""
        logger.info("🚀 Starting Knowledge Graph Embedding Generation")
        logger.info("=" * 60)
        
        try:
            # Configure Gemini
            self.configure_gemini()
            
            # Load Knowledge Graph
            kg_data = self.load_knowledge_graph()
            
            # Process nodes
            node_embeddings = await self.process_nodes(kg_data.get('nodes', []))
            
            # Process edges
            edge_embeddings = await self.generate_edge_embeddings(kg_data.get('edges', []), node_embeddings)
            
            # Save all embeddings
            all_embeddings = {
                'nodes': node_embeddings,
                'edges': edge_embeddings
            }
            
            self.save_embeddings(all_embeddings)
            
            # Summary
            logger.info("=" * 60)
            logger.info("✅ EMBEDDING GENERATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"📊 Node embeddings: {len(node_embeddings)}")
            logger.info(f"📊 Edge embeddings: {len(edge_embeddings)}")
            logger.info(f"📊 Total embeddings: {len(node_embeddings) + len(edge_embeddings)}")
            logger.info(f"📊 Embedding model: {GEMINI_MODEL}")
            logger.info(f"📊 Embedding dimensions: {EMBEDDING_DIMENSIONS}")
            logger.info(f"📊 Output file: {EMBEDDINGS_OUTPUT_PATH}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise


async def main():
    """Main function to run embedding generation."""
    generator = KnowledgeGraphEmbeddingGenerator()
    await generator.run_generation()


if __name__ == "__main__":
    asyncio.run(main())
