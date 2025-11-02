"""
Report API Server
Serves test reports via REST API for React frontend
Runs on port 5000 (separate from main API on port 8000)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

app = FastAPI(
    title="Test Reports API",
    description="API for serving automated test reports",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the script directory and set testcases path relative to it
SCRIPT_DIR = Path(__file__).parent.resolve()
TESTCASES_DIR = os.path.join(SCRIPT_DIR.parent, "automation", "testcases")
TEST_TYPES = ['integration', 'system', 'component', 'regression', 'sanity']


def get_reports_for_type(test_type: str, limit: int = 10) -> List[Dict]:
    """Get reports for a specific test type"""
    reports_dir = os.path.join(TESTCASES_DIR, test_type, "reports")

    if not os.path.exists(reports_dir):
        return []

    # Get all JSON reports, sorted by timestamp (newest first)
    json_files = sorted(
        glob.glob(os.path.join(reports_dir, "test_results_*.json")),
        reverse=True
    )[:limit]

    reports = []
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                filename = os.path.basename(json_file)
                html_filename = filename.replace('test_results_', 'test_report_').replace('.json', '.html')

                reports.append({
                    'id': filename.replace('test_results_', '').replace('.json', ''),
                    'timestamp': data.get('timestamp', ''),
                    'test_type': test_type,
                    'summary': data.get('summary', {}),
                    'json_file': filename,
                    'html_file': html_filename,
                    'total_results': len(data.get('results', []))
                })
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
            continue

    return reports


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Test Reports API",
        "version": "1.0.0",
        "endpoints": {
            "summary": "/api/reports/summary",
            "all_reports": "/api/reports",
            "by_type": "/api/reports/{test_type}",
            "specific_report": "/api/reports/{test_type}/{report_id}",
            "html_report": "/api/reports/{test_type}/{report_id}/html"
        }
    }


@app.get("/api/reports/summary")
def get_summary():
    """Get summary of all test types with latest results"""
    summary = {}

    for test_type in TEST_TYPES:
        reports = get_reports_for_type(test_type, limit=1)
        if reports:
            latest = reports[0]
            all_reports = get_reports_for_type(test_type, limit=100)

            summary[test_type] = {
                'latest': latest,
                'total_reports': len(all_reports),
                'has_reports': True
            }
        else:
            summary[test_type] = {
                'latest': None,
                'total_reports': 0,
                'has_reports': False
            }

    return summary


@app.get("/api/reports")
def get_all_reports(limit: int = 10):
    """Get reports from all test types"""
    all_reports = {}

    for test_type in TEST_TYPES:
        reports = get_reports_for_type(test_type, limit)
        if reports:
            all_reports[test_type] = reports

    return all_reports


@app.get("/api/reports/{test_type}")
def get_reports_by_type(test_type: str, limit: int = 10):
    """Get reports for a specific test type"""
    if test_type not in TEST_TYPES:
        raise HTTPException(status_code=404, detail=f"Test type '{test_type}' not found")

    reports = get_reports_for_type(test_type, limit)

    return {
        'test_type': test_type,
        'reports': reports,
        'total': len(reports)
    }


@app.get("/api/reports/{test_type}/history")
def get_test_history(test_type: str, limit: int = 20):
    """Get historical data for charts (summary only)"""
    if test_type not in TEST_TYPES:
        raise HTTPException(status_code=404, detail=f"Test type '{test_type}' not found")

    reports = get_reports_for_type(test_type, limit)

    # Reverse to show oldest to newest for trend charts
    history = []
    for report in reversed(reports):
        try:
            timestamp = datetime.fromisoformat(report['timestamp'])
            history.append({
                'timestamp': report['timestamp'],
                'formatted_time': timestamp.strftime('%m/%d %H:%M'),
                'summary': report['summary']
            })
        except:
            continue

    return {
        'test_type': test_type,
        'history': history
    }


@app.get("/api/reports/{test_type}/{report_id}/html")
def get_html_report(test_type: str, report_id: str):
    """Get HTML report file"""
    if test_type not in TEST_TYPES:
        raise HTTPException(status_code=404, detail=f"Test type '{test_type}' not found")

    html_file = os.path.join(TESTCASES_DIR, test_type, "reports", f"test_report_{report_id}.html")

    if not os.path.exists(html_file):
        raise HTTPException(status_code=404, detail=f"HTML report '{report_id}' not found")

    return FileResponse(html_file, media_type="text/html")


@app.get("/api/reports/{test_type}/{report_id}")
def get_specific_report(test_type: str, report_id: str):
    """Get a specific report with full details"""
    if test_type not in TEST_TYPES:
        raise HTTPException(status_code=404, detail=f"Test type '{test_type}' not found")

    json_file = os.path.join(TESTCASES_DIR, test_type, "reports", f"test_results_{report_id}.json")

    if not os.path.exists(json_file):
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

    with open(json_file, 'r') as f:
        data = json.load(f)

    return data


@app.get("/api/stats")
def get_stats():
    """Get overall statistics"""
    stats = {
        'total_reports': 0,
        'by_type': {},
        'overall_summary': {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'pass_rate': '0%'
        }
    }

    total_tests = 0
    total_passed = 0
    total_failed = 0

    for test_type in TEST_TYPES:
        reports = get_reports_for_type(test_type, limit=1)
        if reports:
            latest = reports[0]
            stats['by_type'][test_type] = latest['summary']
            stats['total_reports'] += 1

            # Accumulate totals
            summary = latest['summary']
            total_tests += summary.get('total', 0)
            total_passed += summary.get('passed', 0)
            total_failed += summary.get('failed', 0)

    # Calculate overall stats
    stats['overall_summary']['total_tests'] = total_tests
    stats['overall_summary']['passed'] = total_passed
    stats['overall_summary']['failed'] = total_failed

    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        stats['overall_summary']['pass_rate'] = f"{pass_rate:.1f}%"

    return stats


if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("🚀 Starting Test Reports API Server")
    print("=" * 80)
    print(f"📂 Serving reports from: {os.path.abspath(TESTCASES_DIR)}")
    print(f"🌐 API Server: http://localhost:5001")
    print(f"📚 API Docs: http://localhost:5001/docs")
    print(f"📊 Summary: http://localhost:5001/api/reports/summary")
    print("=" * 80)
    print("\nPress Ctrl+C to stop the server\n")

    uvicorn.run(app, host="0.0.0.0", port=5001)
