#!/bin/bash

# Startup script for Test Automation Framework
# This script starts all required servers in background:
# 1. Main API server (port 8000)
# 2. Report API server (port 5001)
# 3. React Dashboard (port 5173)
#
# All servers run as background processes and persist after script exits.

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Starting Test Automation Framework${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
    echo -e "${GREEN}✓ Using virtual environment${NC}"
else
    PYTHON_CMD="python3"
    echo -e "${YELLOW}⚠ Virtual environment not found, using system Python${NC}"
    echo -e "${YELLOW}  Run ./setup.sh first for proper setup${NC}"
fi
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for server to start
wait_for_server() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0

    echo -e "${YELLOW}Waiting for $name to start...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    echo -e "${YELLOW}⚠ Warning: $name may not have started properly${NC}"
    return 1
}

echo -e "${BLUE}[2/3] Starting Report API Server...${NC}"
if check_port 5001; then
    echo -e "${YELLOW}⚠ Port 5001 already in use. Skipping Report API Server.${NC}"
else
    cd report_api
    nohup $PYTHON_CMD report_api.py > "$SCRIPT_DIR/logs/report_api.log" 2>&1 &
    REPORT_API_PID=$!
    echo $REPORT_API_PID > "$SCRIPT_DIR/logs/report_api.pid"
    disown
    echo -e "${GREEN}✓ Report API Server started in background (PID: $REPORT_API_PID)${NC}"
    cd "$SCRIPT_DIR"
fi
echo ""

# 3. Start React Dashboard (port 5173)
echo -e "${BLUE}[3/3] Starting React Dashboard...${NC}"
if check_port 5173; then
    echo -e "${YELLOW}⚠ Port 5173 already in use. Skipping React Dashboard.${NC}"
else
    cd reports-dashboard
    nohup npm run dev > "$SCRIPT_DIR/logs/dashboard.log" 2>&1 &
    DASHBOARD_PID=$!
    echo $DASHBOARD_PID > "$SCRIPT_DIR/logs/dashboard.pid"
    disown
    echo -e "${GREEN}✓ React Dashboard started in background (PID: $DASHBOARD_PID)${NC}"
    cd "$SCRIPT_DIR"
fi
echo ""

# Wait a moment for servers to initialize
echo -e "${YELLOW}Waiting for servers to initialize...${NC}"
sleep 3
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ All servers started in background!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Available Services (starting up):${NC}"
echo -e "  📊 Report API Server:   ${GREEN}http://localhost:5001${NC}"
echo -e "     └─ API Docs:         ${GREEN}http://localhost:5001/docs${NC}"
echo -e "     └─ Summary:          ${GREEN}http://localhost:5001/api/reports/summary${NC}"
echo -e "  🌐 React Dashboard:     ${GREEN}http://localhost:5173${NC}"
echo ""
echo -e "${BLUE}Logs (tail -f to monitor):${NC}"
echo -e "  Report API:   logs/report_api.log"
echo -e "  Dashboard:    logs/dashboard.log"
echo ""
echo -e "${BLUE}Process IDs:${NC}"
if [ -f "logs/report_api.pid" ]; then
    echo -e "  Report API:   $(cat logs/report_api.pid)"
fi
if [ -f "logs/dashboard.pid" ]; then
    echo -e "  Dashboard:    $(cat logs/dashboard.pid)"
fi
echo ""
echo -e "${YELLOW}Servers are running in background. Close this terminal safely.${NC}"
echo -e "${YELLOW}To stop all servers, run:${NC} ./stop.sh"
echo ""
