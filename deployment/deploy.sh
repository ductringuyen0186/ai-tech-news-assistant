#!/bin/bash
# AI Tech News Assistant - Production Deployment Script

set -e

echo "🚀 Starting AI Tech News Assistant Deployment..."

# Configuration
PROJECT_NAME="ai-tech-news-assistant"
REGISTRY="your-registry"  # Replace with your container registry
VERSION=${1:-"latest"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Build images
build_images() {
    log_info "Building Docker images..."
    
    # Build backend
    log_info "Building backend image..."
    docker build -t ${PROJECT_NAME}-backend:${VERSION} ./backend
    
    # Build frontend
    log_info "Building frontend image..."
    docker build -t ${PROJECT_NAME}-frontend:${VERSION} ./frontend
    
    log_info "Images built successfully ✓"
}

# Deploy with Docker Compose
deploy_local() {
    log_info "Deploying locally with Docker Compose..."
    
    # Create necessary directories
    mkdir -p ./data ./logs ./backups
    
    # Stop existing services
    docker-compose down --remove-orphans
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Health check
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_info "Backend is healthy ✓"
    else
        log_error "Backend health check failed"
        docker-compose logs backend
        exit 1
    fi
    
    if curl -f http://localhost:3000/health &>/dev/null; then
        log_info "Frontend is healthy ✓"
    else
        log_warn "Frontend health check failed (may be normal if using external hosting)"
    fi
    
    log_info "Deployment completed successfully! 🎉"
    log_info "Backend: http://localhost:8000"
    log_info "Frontend: http://localhost:3000"
    log_info "API Docs: http://localhost:8000/docs"
}

# Push images to registry
push_images() {
    if [ -z "$REGISTRY" ] || [ "$REGISTRY" = "your-registry" ]; then
        log_warn "Registry not configured, skipping image push"
        return
    fi
    
    log_info "Pushing images to registry..."
    
    # Tag and push backend
    docker tag ${PROJECT_NAME}-backend:${VERSION} ${REGISTRY}/${PROJECT_NAME}-backend:${VERSION}
    docker push ${REGISTRY}/${PROJECT_NAME}-backend:${VERSION}
    
    # Tag and push frontend
    docker tag ${PROJECT_NAME}-frontend:${VERSION} ${REGISTRY}/${PROJECT_NAME}-frontend:${VERSION}
    docker push ${REGISTRY}/${PROJECT_NAME}-frontend:${VERSION}
    
    log_info "Images pushed successfully ✓"
}

# Production deployment (for cloud services)
deploy_production() {
    log_info "Preparing production deployment files..."
    
    # Create production docker-compose override
    cat > docker-compose.prod.yml << EOF
version: '3.8'
services:
  backend:
    image: ${REGISTRY}/${PROJECT_NAME}-backend:${VERSION}
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
  frontend:
    image: ${REGISTRY}/${PROJECT_NAME}-frontend:${VERSION}
EOF
    
    log_info "Production files created ✓"
    log_info "To deploy to production:"
    log_info "1. Copy docker-compose.prod.yml to your production server"
    log_info "2. Set up your .env.production file"
    log_info "3. Run: docker-compose -f docker-compose.prod.yml up -d"
}

# Cleanup old images
cleanup() {
    log_info "Cleaning up old images..."
    docker image prune -f
    log_info "Cleanup completed ✓"
}

# Show logs
show_logs() {
    docker-compose logs -f
}

# Show status
show_status() {
    docker-compose ps
}

# Main execution
case "${2:-deploy}" in
    "deploy")
        check_prerequisites
        build_images
        deploy_local
        ;;
    "build")
        check_prerequisites
        build_images
        ;;
    "push")
        push_images
        ;;
    "prod")
        check_prerequisites
        build_images
        push_images
        deploy_production
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 [version] [deploy|build|push|prod|logs|status|cleanup]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Build and deploy locally (default)"
        echo "  build   - Build Docker images only"
        echo "  push    - Push images to registry"
        echo "  prod    - Build, push, and prepare production deployment"
        echo "  logs    - Show service logs"
        echo "  status  - Show service status"
        echo "  cleanup - Clean up old Docker images"
        echo ""
        echo "Examples:"
        echo "  $0                    # Deploy latest version locally"
        echo "  $0 v1.0.0 deploy      # Deploy specific version"
        echo "  $0 latest prod        # Prepare production deployment"
        ;;
esac
