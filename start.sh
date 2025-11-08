#!/bin/bash

# Budget Planner - Quick Start Script

echo "🚀 Starting Budget Planner..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and Docker Compose first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Start Docker Compose
echo "📦 Building and starting services..."
docker-compose up --build

echo ""
echo "✓ Budget Planner is running!"
echo "📱 Open your browser: http://localhost:3000"
echo "📡 API: http://localhost:5000/api"
