#!/bin/bash

# Ancient Free Will Database - PostgreSQL Setup Script
# This script automates the setup process

set -e  # Exit on any error

echo "🚀 Starting Ancient Free Will Database PostgreSQL Setup"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Check if Sematika database exists
SEMATIKA_DB="/Users/romaingirardi/SematikaData/library.db"
if [ ! -f "$SEMATIKA_DB" ]; then
    echo "❌ Sematika MVP database not found at: $SEMATIKA_DB"
    echo "Please ensure the Sematika MVP database is available."
    exit 1
fi

echo "✅ Sematika MVP database found"

# Start PostgreSQL with Docker Compose
echo "🐘 Starting PostgreSQL with Docker Compose..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check if PostgreSQL is healthy
if ! docker-compose ps | grep -q "healthy"; then
    echo "⏳ Waiting a bit more for PostgreSQL to be ready..."
    sleep 10
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run the database setup script
echo "🔧 Running database setup script..."
python3 setup_database.py

# Run database tests
echo "🧪 Running database tests..."
python3 test_database.py

# Run search demo
echo "🔍 Running search capabilities demo..."
python3 search_demo.py

echo ""
echo "🎉 Setup completed successfully!"
echo "=================================================="
echo "Database connection details:"
echo "  Host: localhost"
echo "  Port: 5433"
echo "  Database: ancient_free_will_db"
echo "  User: free_will_user"
echo "  Password: free_will_password"
echo ""
echo "PgAdmin web interface:"
echo "  URL: http://localhost:8080"
echo "  Email: admin@ancientfreewill.org"
echo "  Password: admin123"
echo ""
echo "To stop the services:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs postgres"
echo "  docker-compose logs pgadmin"
