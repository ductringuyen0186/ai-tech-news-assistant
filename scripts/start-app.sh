#!/bin/bash
# ===================================================================
# AI Tech News Assistant - Unix/Linux/macOS Startup Script
# Intelligently starts backend and frontend with dependency checking
# ===================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WITH_AI=true
SKIP_DEPS=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-ai)
            WITH_AI=false
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --help)
            echo "AI Tech News Assistant - Startup Script"
            echo ""
            echo "Usage: ./start-app.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-ai       Disable AI features (faster startup, no Ollama required)"
            echo "  --skip-deps   Skip dependency installation check"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./start-app.sh                 # Start with AI features"
            echo "  ./start-app.sh --no-ai         # Start without AI"
            echo "  ./start-app.sh --skip-deps     # Skip dependency checks"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Header
echo ""
echo "========================================"
echo " AI Tech News Assistant - Local Startup"
echo "========================================"
echo ""

# Display configuration
echo "Configuration:"
echo "- AI Features: $WITH_AI"
echo "- Skip Dependency Check: $SKIP_DEPS"
echo ""

# ===================================================================
# STEP 1: Check System Prerequisites
# ===================================================================
echo -e "${BLUE}[1/7] Checking system prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed${NC}"
    echo "Please install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}  ✓ Python: $PYTHON_VERSION${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}  ✓ Node.js: $NODE_VERSION${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}[ERROR] npm is not installed${NC}"
    echo "Please ensure Node.js installation includes npm"
    exit 1
fi
NPM_VERSION=$(npm --version)
echo -e "${GREEN}  ✓ npm: $NPM_VERSION${NC}"

# Check Ollama if AI is enabled
if [ "$WITH_AI" = true ]; then
    echo ""
    echo "Checking for Ollama AI engine..."
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Ollama: Running${NC}"
    else
        echo -e "${YELLOW}[WARNING] Ollama is not running or not installed${NC}"
        echo ""
        echo "AI features will be disabled. To enable:"
        echo "1. Install Ollama from https://ollama.com"
        echo "2. Run: ollama pull llama3.2:1b"
        echo "3. Restart this script"
        echo ""
        WITH_AI=false
        sleep 3
    fi
fi

echo ""

# ===================================================================
# STEP 2: Setup Backend
# ===================================================================
echo -e "${BLUE}[2/7] Setting up backend...${NC}"
cd "$SCRIPT_DIR/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo "  Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to activate virtual environment${NC}"
    exit 1
fi

# Check if dependencies need to be installed
if [ "$SKIP_DEPS" = false ]; then
    echo "  Checking Python dependencies..."

    # Check if requirements are already installed
    if ! python -c "import fastapi" 2>/dev/null; then
        echo "  Installing Python dependencies (this may take a few minutes)..."
        pip install -q -r requirements.txt
        if [ $? -ne 0 ]; then
            echo -e "${RED}[ERROR] Failed to install Python dependencies${NC}"
            exit 1
        fi
        echo -e "${GREEN}  ✓ Dependencies installed successfully${NC}"
    else
        echo "  - Dependencies already installed (checking for updates...)"
        pip install -q -r requirements.txt --upgrade
    fi
else
    echo "  - Skipping dependency check"
fi

# Setup environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "  Creating .env file from template..."
    cp .env.example .env

    echo ""
    echo -e "${YELLOW}[IMPORTANT] Generated .env file with default settings${NC}"
    echo "Please edit backend/.env and set a secure SECRET_KEY"
    echo ""
    echo "Run this to generate a secure key:"
    echo "  openssl rand -hex 32"
    echo ""
    sleep 3
fi

echo -e "${GREEN}  ✓ Backend setup complete!${NC}"
cd "$SCRIPT_DIR"
echo ""

# ===================================================================
# STEP 3: Setup Frontend
# ===================================================================
echo -e "${BLUE}[3/7] Setting up frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists
if [ "$SKIP_DEPS" = false ]; then
    if [ ! -d "node_modules" ]; then
        echo "  Installing npm dependencies (this may take a few minutes)..."
        npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}[ERROR] Failed to install npm dependencies${NC}"
            exit 1
        fi
    else
        echo "  - Dependencies already installed"
    fi
else
    echo "  - Skipping dependency check"
fi

echo -e "${GREEN}  ✓ Frontend setup complete!${NC}"
cd "$SCRIPT_DIR"
echo ""

# ===================================================================
# STEP 4: Initialize Database
# ===================================================================
echo -e "${BLUE}[4/7] Checking database...${NC}"
cd "$SCRIPT_DIR/backend"
source venv/bin/activate

if [ ! -f "news_production.db" ]; then
    echo "  Database not found, will be created on first run..."
else
    echo -e "${GREEN}  ✓ Database exists${NC}"
fi

cd "$SCRIPT_DIR"
echo ""

# ===================================================================
# STEP 5: Display Startup Information
# ===================================================================
echo -e "${BLUE}[5/7] Starting application services...${NC}"
echo ""
echo "========================================"
echo " Services Starting"
echo "========================================"
echo ""
echo "Backend API:     http://localhost:8001"
echo "Frontend:        http://localhost:5173"
echo "API Docs:        http://localhost:8001/docs"
echo "Health Check:    http://localhost:8001/health"
echo ""
if [ "$WITH_AI" = true ]; then
    echo -e "${GREEN}AI Features:     ENABLED${NC}"
else
    echo -e "${YELLOW}AI Features:     DISABLED${NC}"
fi
echo ""
echo "Press Ctrl+C to stop all services"
echo ""
sleep 2

# ===================================================================
# Function to cleanup on exit
# ===================================================================
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ===================================================================
# STEP 6: Start Backend
# ===================================================================
echo -e "${BLUE}[6/7] Starting backend server...${NC}"
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
python production_main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Backend failed to start${NC}"
    echo "Check logs/backend.log for details"
    exit 1
fi
echo -e "${GREEN}  ✓ Backend started (PID: $BACKEND_PID)${NC}"

# ===================================================================
# STEP 7: Start Frontend
# ===================================================================
echo -e "${BLUE}[7/7] Starting frontend server...${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 2

# Check if frontend is running
if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Frontend failed to start${NC}"
    echo "Check logs/frontend.log for details"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi
echo -e "${GREEN}  ✓ Frontend started (PID: $FRONTEND_PID)${NC}"

cd "$SCRIPT_DIR"

# ===================================================================
# Final Status
# ===================================================================
echo ""
echo "========================================"
echo " Startup Complete!"
echo "========================================"
echo ""
echo "Services are running in the background."
echo ""
echo "Next Steps:"
echo "1. Wait 10-15 seconds for services to fully start"
echo "2. Open http://localhost:5173 in your browser"
echo "3. Check http://localhost:8001/docs for API documentation"
echo ""
if [ "$WITH_AI" = false ]; then
    echo -e "${YELLOW}Note: AI features are disabled. Articles will use simple summarization.${NC}"
    echo "To enable AI, install Ollama and run: ./start-app.sh"
    echo ""
fi
echo "Logs:"
echo "  Backend:  logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo "To view logs:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for processes
wait
