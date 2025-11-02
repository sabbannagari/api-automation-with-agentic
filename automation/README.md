# Test Automation Framework

Automated API testing framework with interactive React dashboard for viewing test results and historical trends.

## Quick Start

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

## Services

### 1. Main API Server (port 8000)
The main API being tested with CRUD operations for users.

- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Endpoints:**
  - GET /users - List all users
  - POST /users - Create a new user
  - GET /users/{user_id} - Get user by ID
  - PUT /users/{user_id} - Update user
  - DELETE /users/{user_id} - Delete user
  - POST /reset-db - Reset database to initial state

### 2. Report API Server (port 5001)
API for serving test reports to the React dashboard.

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

### 3. React Dashboard (port 5173)
Interactive web dashboard for browsing test results.

- **URL:** http://localhost:5173
- **Features:**
  - Overall statistics across all test types
  - Test type cards showing latest results
  - Historical trend charts
  - Detailed test reports with pass/fail metrics
  - Links to view individual HTML reports

## Running Tests

### Execute All Test Types
```bash
python test_case_executor.py
```

### Execute Specific Test Type
```bash
python test_case_executor.py --test-type integration
python test_case_executor.py --test-type system
python test_case_executor.py --test-type component
python test_case_executor.py --test-type regression
python test_case_executor.py --test-type sanity
```

### Test Options
```bash
python test_case_executor.py --help
```

## Test Organization

Tests are organized by type in the following structure:

```
testcases/
├── integration/
│   ├── testcases/          # Test case JSON files
│   └── reports/            # Generated JSON and HTML reports
├── system/
│   ├── testcases/
│   └── reports/
├── component/
│   ├── testcases/
│   └── reports/
├── regression/
│   ├── testcases/
│   └── reports/
└── sanity/
    ├── testcases/
    └── reports/
```

## Test Case Format

Test cases are defined in JSON format:

```json
{
  "test_name": "Get all users",
  "endpoint": "/users",
  "method": "GET",
  "headers": {
    "Content-Type": "application/json"
  },
  "expected_status_code": 200,
  "validate_response": {
    "type": "array",
    "min_length": 1
  }
}
```

## Logs

All server logs are stored in the `logs/` directory:
- `logs/main_api.log` - Main API server logs
- `logs/report_api.log` - Report API server logs
- `logs/dashboard.log` - React dashboard logs

## Troubleshooting

### Ports Already in Use
If you get "address already in use" errors, run:
```bash
./stop.sh
```

Then try starting again:
```bash
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

### View Logs
```bash
# Main API logs
tail -f logs/main_api.log

# Report API logs
tail -f logs/report_api.log

# Dashboard logs
tail -f logs/dashboard.log
```

## Development

### Install Dependencies

**Python (for API servers):**
```bash
pip install fastapi uvicorn
```

**Node.js (for React dashboard):**
```bash
cd reports-dashboard
npm install
```

### Manual Server Startup

**Main API:**
```bash
cd ../api
python main.py
```

**Report API:**
```bash
python report_api.py
```

**React Dashboard:**
```bash
cd reports-dashboard
npm run dev
```

## Features

### Test Execution
- Execute tests by type (integration, system, component, regression, sanity)
- Automatic JSON and HTML report generation
- Historical tracking of all test runs
- Support for various HTTP methods (GET, POST, PUT, DELETE)
- Request/response validation
- Parameter substitution (path and query params)

### Reports Dashboard
- Real-time statistics across all test types
- Interactive charts showing trends over time
- Detailed test result tables
- Pass/fail metrics with visual indicators
- Links to full HTML reports

### API Features
- RESTful endpoints for all test data
- CORS enabled for frontend access
- Automatic report discovery and parsing
- Historical data aggregation
- OpenAPI documentation
