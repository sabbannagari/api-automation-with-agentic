#!/bin/bash

# Stop script for Test Automation Framework
# This script stops all running servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🛑 Stopping Test Automation Framework${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to stop server by PID file
stop_by_pid_file() {
    local pid_file=$1
    local server_name=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null || true
            echo -e "${GREEN}✓ Stopped $server_name (PID: $pid)${NC}"
        else
            echo -e "${YELLOW}⚠ $server_name process (PID: $pid) not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠ No PID file found for $server_name${NC}"
    fi
}

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    local server_name=$2

    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✓ Killed processes on port $port ($server_name)${NC}"
    fi
}

# Stop servers by PID files if they exist
if [ -d "logs" ]; then
    echo -e "${BLUE}Stopping servers by PID files...${NC}"
    stop_by_pid_file "logs/main_api.pid" "Main API Server"
    stop_by_pid_file "logs/report_api.pid" "Report API Server"
    stop_by_pid_file "logs/dashboard.pid" "React Dashboard"
    echo ""
fi

# Kill any remaining processes on the ports
echo -e "${BLUE}Ensuring all ports are free...${NC}"
kill_port 8000 "Main API"
kill_port 5001 "Report API"
kill_port 5173 "React Dashboard"
echo ""

# Kill any Python processes running our scripts
echo -e "${BLUE}Cleaning up Python processes...${NC}"
pkill -f "api/main.py" 2>/dev/null && echo -e "${GREEN}✓ Stopped main.py processes${NC}" || true
pkill -f "automation/report_api.py" 2>/dev/null && echo -e "${GREEN}✓ Stopped report_api.py processes${NC}" || true
echo ""

# Kill any Node/Vite processes for the dashboard
echo -e "${BLUE}Cleaning up Node processes...${NC}"
pkill -f "vite" 2>/dev/null && echo -e "${GREEN}✓ Stopped Vite processes${NC}" || true
pkill -f "reports-dashboard" 2>/dev/null && echo -e "${GREEN}✓ Stopped dashboard processes${NC}" || true
echo ""

# Clean up PID files
if [ -d "logs" ]; then
    rm -f logs/*.pid
fi

# Verify ports are free
echo -e "${BLUE}Verifying ports are free...${NC}"
for port in 8000 5001 5173; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}✗ Port $port is still in use${NC}"
    else
        echo -e "${GREEN}✓ Port $port is free${NC}"
    fi
done
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ All servers stopped successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}To start servers again, run:${NC} ./startup.sh"
echo ""
