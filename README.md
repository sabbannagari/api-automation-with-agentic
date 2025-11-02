# Automated API Testing Framework With AI AGENTS 

Complete test automation framework with API, test execution engine, and interactive React dashboard for viewing test results and historical trends.

## 🚀 Installation

### Prerequisites
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **npm** (comes with Node.js)

### Setup (First Time Only)

After cloning the repository, run the setup script:

```bash
./setup.sh
```

This will:
1. Check for Python 3 and Node.js
2. Create a Python virtual environment
3. Install all Python dependencies (API & automation)
4. Install all Node.js dependencies (React dashboard)
5. Create necessary directories for logs and reports

## 🎯 Quick Start

### Start All Servers
```bash
./startup.sh
```

This will start:
- **Main API Server** on port 8000
- **Report API Server** on port 5001
- **React Dashboard** on port 5173

### Stop All Servers
```bash
./stop.sh
```

## ⚙️ Configuration

Before running tests, configure the framework in `automation/config.json`:

### API Configuration

```json
{
  "api": {
    "base_url": "http://localhost:8000",
    "schema": "http://localhost:8000/openapi.json",
    "auth_type": null
  }
}
```

**Configuration Fields:**

- **`base_url`**: Base URL of your API server (e.g., `http://localhost:8000`, `https://api.example.com`)
- **`schema`**: URL to your OpenAPI/Swagger specification (e.g., `http://localhost:8000/openapi.json`, `http://localhost:8000/swagger.json`)
- **`auth_type`**: Authentication method - `null` (no auth), `"basic"`, `"bearer"`, or `"token"`

**Authentication Setup:**

If your API requires authentication, set environment variables:

```bash
# For Basic Authentication
export API_USERNAME="your_username"
export API_PASSWORD="your_password"

# For Bearer/Token Authentication
export API_TOKEN="your_token_here"
```

Then update `auth_type` in config.json:
```json
{
  "api": {
    "auth_type": "basic"  // or "bearer" or "token"
  }
}
```

**LLM Configuration:**

The framework requires an Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

## 🤖 Running the Master Agent

The Master Agent is the **single entry point** for the automation framework. It intelligently decomposes tasks and orchestrates specialized agents.

Navigate to the automation directory:
```bash
cd automation
```

### Test Types Available

| Test Type | Description | Use Case |
|-----------|-------------|----------|
| **Integration** | Verify integration between components | Testing API endpoints work together |
| **System** | End-to-end system verification | Complete user workflows |
| **Component** | Individual component testing | Isolated endpoint testing |
| **Regression** | Prevent fixed bugs from returning | Stability checks after changes |
| **Sanity** | Basic smoke tests | Quick health checks |

### Basic Usage

```bash
# Execute existing test cases (all types)
python master.py --task "execute testcases"

# Create test cases from OpenAPI spec
python master.py --task "create tests"

# Create and execute tests in one command
python master.py --task "create and run tests"
```

### Running Specific Test Types

```bash
# Execute only integration tests
python master.py --task "execute integration tests"

# Execute only system tests
python master.py --task "execute system tests"

# Execute only component tests
python master.py --task "execute component tests"

# Execute only regression tests
python master.py --task "execute regression tests"

# Execute only sanity tests
python master.py --task "execute sanity tests"
```

### Advanced Examples

```bash
# Generate tests and run only integration tests
python master.py --task "create tests and run integration tests"

# Run multiple test types
python master.py --task "execute integration and system tests"

# Create comprehensive test suite
python master.py --task "generate comprehensive test cases from API schema"

# Execute all tests and generate reports
python master.py --task "run all tests and create reports"
```

### How It Works

The Master Agent will:
1. **Parse** your task description
2. **Delegate** to the Decomposer Agent
3. **Orchestrate** specialized agents:
   - **Test Case Generator**: Creates tests from OpenAPI specification
   - **Test Case Executor**: Runs tests and generates reports
4. **Generate** an execution summary JSON file

### Master Agent Output

After execution, you'll find:
- **Execution Summary**: `master_execution_YYYYMMDD_HHMMSS.json` - Contains details of all agents executed and their status
- **Test Cases**: Generated in `automation/testcases/{test_type}/testcases/` (if created)
- **Test Reports**: Generated in `automation/testcases/{test_type}/reports/` (if executed)

### Example Output

```
🎯 MASTER AGENT - API Test Automation Framework
================================================================================
📋 Task: create and run tests
⏰ Started: 2025-11-01 14:30:00
================================================================================

📤 Master Agent: Delegating to Decomposer Agent...
🧠 Decomposer Agent: Starting task decomposition
   Task: 'create and run tests'

📋 Task Decomposition:
   Reasoning: Task requires test generation and execution
   Execution Mode: sequential
   Agents to execute: test_case_generator, test_case_executor

🚀 Decomposer Agent: Executing 2 agent(s)

================================================================================
🤖 Decomposer Agent: Invoking test_case_generator
   Test case generator agent - generates test cases from OpenAPI specifications
================================================================================
[Test generation output...]

================================================================================
🤖 Decomposer Agent: Invoking test_case_executor
   Test case executor agent - executes test cases and generates reports
================================================================================
[Test execution output...]

✅ MASTER AGENT - Execution Complete
================================================================================
📊 Task: create and run tests
⏰ Completed: 2025-11-01 14:32:30

   Agents executed: 2
   ✅ test_case_generator: completed
   ✅ test_case_executor: completed

💾 Execution summary saved to: master_execution_20251101_143230.json
================================================================================
```

## 📊 Servers and Services

### 1. Report API Server (port 5001)
API for serving test reports to the React dashboard.

- **Location:** `report_api/report_api.py`
- **URL:** http://localhost:5001
- **API Docs:** http://localhost:5001/docs
- **Endpoints:**
  - GET /api/reports/summary - Summary of all test types
  - GET /api/reports - All reports across test types
  - GET /api/reports/{test_type} - Reports for specific test type
  - GET /api/reports/{test_type}/{report_id} - Specific report details
  - GET /api/reports/{test_type}/{report_id}/html - HTML report
  - GET /api/reports/{test_type}/history - Historical data for charts
  - GET /api/stats - Overall statistics

### 2. React Dashboard (port 5173)
Interactive web dashboard for browsing test results and analytics.

- **Location:** `automation/reports-dashboard/`
- **URL:** http://localhost:5173
- **Features:**
  - Overall statistics across all test types
  - Test type cards showing latest results
  - Historical trend charts (using Recharts)
  - Detailed test reports with pass/fail metrics
  - Links to view individual HTML reports

## 📊 View Dashboards

### Dashboard URLs

- **Main Dashboard**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **Report API Documentation**: http://localhost:5001/docs

### Viewing Reports

After running tests, view results:
- **Dashboard**: Browse all test results at http://localhost:5173
- **HTML Reports**: Located in `automation/testcases/{test_type}/reports/`
- **JSON Reports**: Raw data in same reports directory

## 📁 Test Cases Structure

### Directory Organization

```
automation/testcases/
├── integration/testcases/     # Integration test JSON files
├── system/testcases/          # System test JSON files
├── component/testcases/       # Component test JSON files
├── regression/testcases/      # Regression test JSON files
└── sanity/testcases/          # Sanity test JSON files
```

## Reports

After running tests, reports are generated in two formats:

### 1. JSON Reports
- Location: `automation/testcases/{test_type}/reports/test_results_*.json`
- Contains complete test results including request/response data
- Used by the Report API

### 2. HTML Reports
- Location: `automation/testcases/{test_type}/reports/test_report_*.html`
- Interactive standalone HTML reports
- Includes charts, filters, and detailed test information
- Can be viewed directly in browser or through dashboard

## Logs

All server logs are stored in the `logs/` directory:
- `logs/main_api.log` - Main API server logs
- `logs/report_api.log` - Report API server logs
- `logs/dashboard.log` - React dashboard logs

### View Logs
```bash
# Main API logs
tail -f logs/main_api.log

# Report API logs
tail -f logs/report_api.log

# Dashboard logs
tail -f logs/dashboard.log
```

## Troubleshooting

### Ports Already in Use
If you get "address already in use" errors:
```bash
./stop.sh
./startup.sh
```

### Check Running Services
```bash
# Check port 8000 (Main API)
curl http://localhost:8000/users

# Check port 5001 (Report API)
curl http://localhost:5001/api/reports/summary

# Check port 5173 (Dashboard)
curl http://localhost:5173
```

### Manually Kill Processes on Ports
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5001
lsof -ti:5001 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

## Development

### Dependencies

**Python (for API servers):**
```bash
pip install fastapi uvicorn
```

**Node.js (for React dashboard):**
```bash
cd automation/reports-dashboard
npm install
```

### Manual Server Startup

**Report API:**
```bash
cd report_api
python report_api.py
```

**React Dashboard:**
```bash
cd automation/reports-dashboard
npm run dev
```

## Features

### Test Execution Engine
- Execute tests by type (integration, system, component, regression, sanity)
- Automatic JSON and HTML report generation
- Historical tracking of all test runs
- Support for various HTTP methods
- Request/response validation
- Path and query parameter substitution
- Comprehensive error handling and logging

### Interactive Dashboard
- Real-time statistics across all test types
- Historical trend charts (line charts showing pass/fail over time)
- Detailed test result tables
- Pass/fail metrics with visual indicators
- Color-coded test type cards
- Links to full HTML reports
- Responsive design with Tailwind CSS

### API Features
- RESTful endpoints for all test data
- CORS enabled for frontend access
- Automatic report discovery and parsing
- Historical data aggregation
- OpenAPI/Swagger documentation
- Comprehensive error handling

## Contributing

1. Add test cases in `automation/testcases/{test_type}/testcases/`
2. Run tests: `python test_case_executor.py --test-type {type}`
3. View results in dashboard: http://localhost:5173

## License

Generated with Claude Code
