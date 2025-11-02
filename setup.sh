#!/bin/bash

# Test Automation Framework - Complete Setup Script
# This script will set up the entire project from scratch
# Run this after cloning the repository on a new machine

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Test Automation Framework Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to compare version
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check prerequisites
echo -e "${BLUE}[1/6] Checking prerequisites...${NC}"
echo ""

# Check Python
if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo -e "${YELLOW}Please install Python 3.8 or higher from https://www.python.org/${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python 3 found: $PYTHON_VERSION${NC}"

# Check Node.js
if ! command_exists node; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo -e "${YELLOW}Please install Node.js 16+ from https://nodejs.org/${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js found: $NODE_VERSION${NC}"

# Check npm
if ! command_exists npm; then
    echo -e "${RED}✗ npm is not installed${NC}"
    echo -e "${YELLOW}Please install npm (usually comes with Node.js)${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm found: $NPM_VERSION${NC}"

# Check pip
if ! command_exists pip3; then
    echo -e "${RED}✗ pip3 is not installed${NC}"
    echo -e "${YELLOW}Please install pip3${NC}"
    exit 1
fi

echo -e "${GREEN}✓ pip3 found${NC}"
echo ""

# Create necessary directories
echo -e "${BLUE}[2/6] Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p automation/testcases/integration/reports
mkdir -p automation/testcases/system/reports
mkdir -p automation/testcases/component/reports
mkdir -p automation/testcases/regression/reports
mkdir -p automation/testcases/sanity/reports
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Set up Python virtual environment
echo -e "${BLUE}[3/6] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists, skipping creation${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install Python dependencies for API
echo -e "${BLUE}[4/6] Installing Python dependencies...${NC}"
echo ""
echo -e "${YELLOW}Installing API dependencies...${NC}"
pip3 install --upgrade pip
pip3 install -r report_api/requirements.txt
echo -e "${GREEN}✓ API dependencies installed${NC}"
echo ""

echo -e "${YELLOW}Installing Automation dependencies...${NC}"
pip3 install -r automation/requirements.txt
echo -e "${GREEN}✓ Automation dependencies installed${NC}"
echo ""

# Install Node.js dependencies for dashboard
echo -e "${BLUE}[5/6] Installing Node.js dependencies...${NC}"
cd reports-dashboard
npm install
cd "$SCRIPT_DIR"
echo -e "${GREEN}✓ Dashboard dependencies installed${NC}"
echo ""

# Create a .env template if it doesn't exist
echo -e "${BLUE}[6/6] Finalizing setup...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Environment Configuration
# Copy this file and customize as needed

# API Configuration
API_PORT=8000
REPORT_API_PORT=5001
DASHBOARD_PORT=5173

# Test Configuration
BASE_URL=http://localhost:8000
EOF
    echo -e "${GREEN}✓ Created .env template${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists, skipping${NC}"
fi
echo ""

# Deactivate virtual environment for display purposes
deactivate 2>/dev/null || true

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Project Structure:${NC}"
echo -e "  📁 api/               - Backend API servers"
echo -e "  📁 automation/        - Test automation scripts"
echo -e "  📁 reports-dashboard/ - React frontend dashboard"
echo -e "  📁 logs/              - Server logs"
echo -e "  📁 venv/              - Python virtual environment"
echo ""
echo -e "${BLUE}Quick Start Guide:${NC}"
echo ""
echo -e "${YELLOW}1. Start all servers:${NC}"
echo -e "   ${GREEN}./startup.sh${NC}"
echo ""
echo -e "${YELLOW}2. Access the services:${NC}"
echo -e "   📡 Main API:          ${GREEN}http://localhost:8000${NC}"
echo -e "   📊 Report API:        ${GREEN}http://localhost:5001${NC}"
echo -e "   🌐 Dashboard:         ${GREEN}http://localhost:5173${NC}"
echo ""
echo -e "${YELLOW}3. Run tests:${NC}"
echo -e "   ${GREEN}source venv/bin/activate${NC}"
echo -e "   ${GREEN}cd automation${NC}"
echo -e "   ${GREEN}python run_tests.py --test-type integration${NC}"
echo ""
echo -e "${YELLOW}4. Stop all servers:${NC}"
echo -e "   ${GREEN}./stop.sh${NC}"
echo ""
echo -e "${BLUE}API Documentation:${NC}"
echo -e "  Main API docs:   ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Report API docs: ${GREEN}http://localhost:5001/docs${NC}"
echo ""
echo -e "${BLUE}Note:${NC} The virtual environment is located at ${GREEN}./venv${NC}"
echo -e "      Activate it with: ${GREEN}source venv/bin/activate${NC}"
echo ""
echo -e "${YELLOW}Ready to start! Run ./startup.sh to begin.${NC}"
echo ""
