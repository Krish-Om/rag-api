#!/bin/bash

# RAG API Docker Deployment Script
set -e

echo "🚀 RAG API Docker Deployment Helper"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_status "Docker is installed"

if ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not available. Please ensure Docker with Compose plugin is installed."
    exit 1
fi
print_status "Docker Compose is available"

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi
print_status "Docker daemon is running"

# Parse command line arguments
COMMAND=${1:-"help"}

case $COMMAND in
    "build")
        echo "🔨 Building RAG API Docker image..."
        docker build -t rag-api:latest .
        print_status "RAG API image built successfully"
        ;;
    
    "up")
        echo "🚀 Starting all services with Docker Compose..."
        docker compose up -d
        
        echo "⏳ Waiting for migration to complete..."
        # Wait for migration container to finish
        timeout=120  # 2 minutes timeout for migration
        elapsed=0
        while [ $elapsed -lt $timeout ]; do
            if docker compose ps migrate | grep -q "Exit 0"; then
                print_status "Database migration completed successfully"
                break
            elif docker compose ps migrate | grep -q "Exit"; then
                print_error "Database migration failed! Check logs: docker compose logs migrate"
                exit 1
            fi
            sleep 2
            elapsed=$((elapsed + 2))
        done
        
        if [ $elapsed -ge $timeout ]; then
            print_error "Migration timeout! Check logs: docker compose logs migrate"
            exit 1
        fi
        
        echo "⏳ Waiting for services to be healthy..."
        sleep 30
        
        # Check if Ollama model needs to be pulled
        echo "📥 Checking Ollama model..."
        if ! docker exec rag-ollama ollama list | grep -q llama3.2:1b; then
            echo "⬇️ Pulling llama3.2:1b model (this may take a while)..."
            docker exec rag-ollama ollama pull llama3.2:1b
        fi
        print_status "Ollama model ready"
        
        echo ""
        echo "🎉 All services are running!"
        echo ""
        echo "📊 Service URLs:"
        echo "  • RAG API: http://localhost:8000"
        echo "  • API Docs: http://localhost:8000/docs"
        echo "  • Qdrant UI: http://localhost:6333/dashboard"
        echo "  • PostgreSQL: localhost:5433"
        echo "  • Redis: localhost:6379"
        echo "  • Ollama: http://localhost:11434"
        ;;
    
    "down")
        echo "🛑 Stopping all services..."
        docker compose down
        print_status "All services stopped"
        ;;
    
    "restart")
        echo "🔄 Restarting all services..."
        docker compose down
        docker compose up -d
        print_status "All services restarted"
        ;;
    
    "logs")
        SERVICE=${2:-"api"}
        echo "📋 Showing logs for $SERVICE..."
        docker compose logs -f $SERVICE
        ;;
    
    "status")
        echo "📊 Service Status:"
        docker compose ps
        ;;
    
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        read -p "This will remove all containers, images, and volumes. Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v
            docker rmi rag-api:latest 2>/dev/null || true
            docker system prune -f
            print_status "Docker resources cleaned"
        else
            echo "Operation cancelled"
        fi
        ;;
    
    "shell")
        SERVICE=${2:-"api"}
        echo "🐚 Opening shell in $SERVICE container..."
        docker compose exec $SERVICE /bin/bash
        ;;
    
    "test")
        echo "🧪 Running API health checks..."
        
        # Check if API is running
        if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
            print_status "API health check passed"
        else
            print_error "API health check failed"
        fi
        
        # Test document upload
        echo "📄 Testing document upload..."
        if curl -X POST "http://localhost:8000/api/v1/upload" \
             -H "Content-Type: multipart/form-data" \
             -F "file=@README.md" >/dev/null 2>&1; then
            print_status "Document upload test passed"
        else
            print_warning "Document upload test failed (this is expected if no test file exists)"
        fi
        ;;
    
    "migrate")
        echo "🗄️ Running database migration..."
        if docker compose up -d postgres; then
            echo "⏳ Waiting for PostgreSQL to be ready..."
            sleep 10
            docker compose run --rm migrate
            print_status "Migration completed"
        else
            print_error "Failed to start PostgreSQL"
        fi
        ;;
    
    "help"|*)
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  build    Build the RAG API Docker image"
        echo "  up       Start all services with Docker Compose"
        echo "  down     Stop all services"
        echo "  restart  Restart all services"
        echo "  logs     Show logs for a service (default: api)"
        echo "  status   Show status of all services"
        echo "  clean    Clean up Docker resources (removes all data)"
        echo "  shell    Open shell in a container (default: api)"
        echo "  test     Run basic health checks"
        echo "  migrate  Run database migration manually"
        echo "  help     Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 up                    # Start all services"
        echo "  $0 logs api              # Show API logs"
        echo "  $0 logs postgres         # Show PostgreSQL logs"
        echo "  $0 shell redis           # Open shell in Redis container"
        echo "  $0 migrate               # Run database migration"
        ;;
esac