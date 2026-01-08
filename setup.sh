#!/bin/bash
# Quick setup script for local development

set -e

echo "🚀 E-Commerce Price Scraper - Local Setup"
echo "=========================================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }

echo "✅ Prerequisites check passed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
    echo "   Especially update passwords and secret keys."
fi

# Create logs directory
mkdir -p logs
echo "✅ Created logs directory"

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run: docker-compose up -d postgres superset"
echo "3. Wait 30-60 seconds for services to initialize"
echo "4. Run: docker-compose up scraper"
echo "5. Access Superset at http://localhost:8088"
echo ""
echo "For more details, see README.md"
