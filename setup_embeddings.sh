#!/bin/bash

# Complete Multi-Modal Embeddings Setup for Ancient Free Will Database
# This script sets up the complete embedding system with maximum 3072 dimensions

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting Complete Multi-Modal Embeddings Setup"
echo "=================================================="
echo "🧠 Knowledge Graph + 🗄️ PostgreSQL + 🔍 Vector DB"
echo "🎯 MAXIMUM 3072-dimensional Gemini embeddings!"
echo "=================================================="

# Set up environment configuration
echo "🔧 Setting up environment configuration..."
python3 setup_environment.py --api-key AIzaSyDB_n4uxyXFIijMeN0imzZ3cbNjR-w3hrw

# Load environment variables
source .env 2>/dev/null || echo "⚠️  .env file not found, using system environment"

# Check if Gemini API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY environment variable not set!"
    echo "   Please run: python3 setup_environment.py --api-key your_key"
    exit 1
fi
echo "✅ Gemini API key found"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi
echo "✅ Docker is running"

# Check if PostgreSQL container is running
if ! docker compose ps -q db > /dev/null 2>&1 || [ -z "$(docker compose ps -q db)" ]; then
    echo "❌ PostgreSQL container not running!"
    echo "   Starting PostgreSQL container..."
    docker compose up -d --build
    
    echo "⏳ Waiting for PostgreSQL to be ready..."
    until docker compose exec db pg_isready -U free_will_user -d ancient_free_will_db; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 5
    done
    echo "PostgreSQL is up and running!"
    
    # Give it a little more time for init.sql to complete
    echo "⏳ Waiting a bit more for PostgreSQL to be ready..."
    sleep 10
else
    echo "✅ PostgreSQL container is running"
fi

# Check if Knowledge Graph file exists
KG_PATH="/Users/romaingirardi/Documents/Ancient Free Will Database/ancient_free_will_database.json"
if [ ! -f "$KG_PATH" ]; then
    echo "❌ Knowledge Graph file not found at $KG_PATH"
    exit 1
fi
echo "✅ Knowledge Graph file found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run the complete embeddings setup
echo "🧠 Running complete embeddings setup..."
echo "   • Generating Knowledge Graph embeddings (3072 dimensions)"
echo "   • Integrating with PostgreSQL database"
echo "   • Setting up Qdrant vector database"
echo "   • Demonstrating multi-modal search capabilities"
echo ""

python3 setup_complete_embeddings.py

# Run Qdrant integration
echo "🔍 Running Qdrant vector database integration..."
python3 integrate_qdrant.py

echo ""
echo "🎉 COMPLETE EMBEDDINGS SETUP FINISHED!"
echo "=================================================="
echo "🧠 Knowledge Graph embeddings: 3072 dimensions"
echo "🗄️ PostgreSQL integration: Complete"
echo "🔍 Qdrant Vector Database: Production-grade performance"
echo "🎯 Cross-modal capabilities: Active"
echo ""
echo "🚀 ELEUTHERIA - The Ancient Free Will Database:"
echo "   Where Knowledge Graphs meet Full-Text Search meets Semantic AI!"
echo "   Now with MAXIMUM 3072-dimensional embeddings + Qdrant! 🎯"
echo ""
echo "Available scripts:"
echo "  • generate_kg_embeddings.py - Generate KG embeddings only"
echo "  • integrate_kg_embeddings.py - Integrate embeddings with PostgreSQL"
echo "  • integrate_qdrant.py - Integrate with Qdrant vector database"
echo "  • multimodal_search_demo.py - Demonstrate search capabilities"
echo "  • setup_complete_embeddings.py - Complete setup process"
echo ""
echo "Services running:"
echo "  • PostgreSQL: localhost:5433"
echo "  • Qdrant HTTP: localhost:6333"
echo "  • Qdrant gRPC: localhost:6334"
echo "  • PgAdmin: localhost:8080"
echo "=================================================="
