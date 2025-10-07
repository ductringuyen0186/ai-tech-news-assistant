#!/bin/bash
# ===================================================================
# Development Environment Setup - First Time Setup Only
# Run this once before using start-app.sh
# ===================================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "========================================"
echo " AI Tech News - First Time Setup"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 not found. Install from https://www.python.org/${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js not found. Install from https://nodejs.org/${NC}"
    exit 1
fi

echo -e "${BLUE}[1/4] Setting up backend...${NC}"
cd "$SCRIPT_DIR/backend"

# Create venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "Installing Python packages..."
pip install -q -r requirements.txt

# Setup .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}[ACTION REQUIRED] Please edit backend/.env and set:${NC}"
    echo "  1. SECRET_KEY to a secure random string"
    echo "  2. Other configuration as needed"
    echo ""
    echo "Generate secure key with: openssl rand -hex 32"
    echo ""
fi

cd "$SCRIPT_DIR"

echo ""
echo -e "${BLUE}[2/4] Setting up frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

# Install npm packages
echo "Installing npm packages..."
npm install

cd "$SCRIPT_DIR"

echo ""
echo -e "${BLUE}[3/4] Creating logs directory...${NC}"
mkdir -p logs

echo ""
echo -e "${BLUE}[4/4] Checking Ollama (optional)...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}Ollama detected and running!${NC}"
else
    echo -e "${YELLOW}[INFO] Ollama not detected. AI features will be disabled.${NC}"
    echo "To enable AI:"
    echo "  1. Install from https://ollama.com"
    echo "  2. Run: ollama pull llama3.2:1b"
fi

echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env if needed"
echo "  2. Run: ./start-app.sh"
echo ""
