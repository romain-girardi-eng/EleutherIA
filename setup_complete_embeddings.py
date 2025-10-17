#!/usr/bin/env python3
"""
Complete Multi-Modal Embeddings Setup for Ancient Free Will Database

This script sets up the complete embedding system:
1. Generates Knowledge Graph embeddings with maximum dimensions (3072)
2. Integrates KG embeddings with PostgreSQL database
3. Demonstrates multi-modal semantic search capabilities

Author: Romain Girardi
Date: 2025-01-17
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompleteEmbeddingsSetup:
    """Complete setup for multi-modal embeddings system."""
    
    def __init__(self):
        self.project_root = Path("/Users/romaingirardi/Documents/Ancient Free Will Database")
        self.kg_embeddings_path = self.project_root / "kg_embeddings.json"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        logger.info("🔍 Checking prerequisites...")
        
        # Check Gemini API key
        if not os.getenv('GEMINI_API_KEY'):
            logger.error("❌ GEMINI_API_KEY environment variable not set!")
            logger.error("   Please set your Gemini API key:")
            logger.error("   export GEMINI_API_KEY='your-api-key-here'")
            return False
        logger.info("✅ Gemini API key found")
        
        # Check Knowledge Graph file
        kg_path = self.project_root / "ancient_free_will_database.json"
        if not kg_path.exists():
            logger.error(f"❌ Knowledge Graph file not found: {kg_path}")
            return False
        logger.info("✅ Knowledge Graph file found")
        
        # Check if PostgreSQL is running
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "-q", "postgres"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if not result.stdout.strip():
                logger.error("❌ PostgreSQL container not running!")
                logger.error("   Please run: docker compose up -d")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking Docker: {e}")
            return False
        logger.info("✅ PostgreSQL container is running")
        
        return True
        
    def install_dependencies(self) -> bool:
        """Install required Python dependencies."""
        logger.info("📦 Installing Python dependencies...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "google-generativeai",
                "asyncpg",
                "numpy",
                "python-dotenv"
            ], check=True)
            logger.info("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
            
    async def generate_kg_embeddings(self) -> bool:
        """Generate Knowledge Graph embeddings with maximum dimensions."""
        logger.info("🧠 Generating Knowledge Graph embeddings (3072 dimensions)...")
        
        try:
            # Import and run the embedding generator
            from generate_kg_embeddings import KnowledgeGraphEmbeddingGenerator
            
            generator = KnowledgeGraphEmbeddingGenerator()
            await generator.run_generation()
            
            # Verify embeddings were created
            if self.kg_embeddings_path.exists():
                logger.info("✅ Knowledge Graph embeddings generated successfully")
                return True
            else:
                logger.error("❌ Embeddings file not created")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to generate KG embeddings: {e}")
            return False
            
    async def integrate_embeddings(self) -> bool:
        """Integrate KG embeddings with PostgreSQL database."""
        logger.info("🔗 Integrating Knowledge Graph embeddings with PostgreSQL...")
        
        try:
            # Import and run the integrator
            from integrate_kg_embeddings import KGEmbeddingsIntegrator
            
            async with KGEmbeddingsIntegrator() as integrator:
                await integrator.run_integration()
                
            logger.info("✅ Embeddings integration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to integrate embeddings: {e}")
            return False
            
    async def demonstrate_capabilities(self) -> bool:
        """Demonstrate multi-modal search capabilities."""
        logger.info("🎯 Demonstrating multi-modal search capabilities...")
        
        try:
            # Import and run the demo
            from multimodal_search_demo import MultiModalSemanticSearch
            
            async with MultiModalSemanticSearch() as searcher:
                await searcher.display_system_overview()
                await searcher.demonstrate_search_capabilities()
                
            logger.info("✅ Multi-modal search demonstration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to demonstrate capabilities: {e}")
            return False
            
    async def run_complete_setup(self) -> None:
        """Run the complete embeddings setup process."""
        logger.info("🚀 COMPLETE MULTI-MODAL EMBEDDINGS SETUP")
        logger.info("=" * 80)
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                logger.error("❌ Prerequisites check failed. Exiting.")
                return
                
            # Install dependencies
            if not self.install_dependencies():
                logger.error("❌ Dependency installation failed. Exiting.")
                return
                
            # Generate KG embeddings
            if not await self.generate_kg_embeddings():
                logger.error("❌ KG embeddings generation failed. Exiting.")
                return
                
            # Integrate embeddings
            if not await self.integrate_embeddings():
                logger.error("❌ Embeddings integration failed. Exiting.")
                return
                
            # Demonstrate capabilities
            if not await self.demonstrate_capabilities():
                logger.error("❌ Capabilities demonstration failed. Exiting.")
                return
                
            # Success summary
            logger.info("=" * 80)
            logger.info("🎉 COMPLETE EMBEDDINGS SETUP SUCCESSFUL!")
            logger.info("=" * 80)
            logger.info("🧠 Knowledge Graph embeddings: 3072 dimensions")
            logger.info("🗄️ PostgreSQL integration: Complete")
            logger.info("🔍 Vector Database: Multi-modal semantic search")
            logger.info("🎯 Cross-modal capabilities: Active")
            logger.info("=" * 80)
            logger.info("🚀 ELEUTHERIA - The Ancient Free Will Database:")
            logger.info("   Where Knowledge Graphs meet Full-Text Search meets Semantic AI!")
            logger.info("   Now with MAXIMUM 3072-dimensional embeddings! 🎯")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Complete setup failed: {e}")
            raise


async def main():
    """Main function to run the complete setup."""
    setup = CompleteEmbeddingsSetup()
    await setup.run_complete_setup()


if __name__ == "__main__":
    asyncio.run(main())
