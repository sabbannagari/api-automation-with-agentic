import os
import json
from datetime import datetime
from anthropic import Anthropic
from utils import Utils

# ===== Load global config =====
global_config = Utils.read_config()

# ===== Shared API info =====
BASE_URL = global_config["api"]["base_url"]
AUTH_TYPE = global_config["api"].get("auth_type", None)

# ===== Executor agent config =====
script_name = Utils.get_script_name(__file__)
agent_config = Utils.get_agent_config(global_config, script_name)

TESTCASES_DIR = global_config["agents"]["test_case_generator"].get("output_dir", "testcases")
LLM_MODEL = agent_config.get("llm_model", "claude-3-haiku-20240307")
TEMPERATURE = agent_config.get("temperature", 0)

# Load executor prompt from file
EXECUTOR_PROMPT = Utils.read_prompt(script_name)

# ===== Initialize Anthropic client =====
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def validate_with_llm(test_case, actual_status, response_body, expected_status):
    """
    Use LLM to intelligently validate test results

    Args:
        test_case: The test case definition
        actual_status: The actual HTTP status code received
        response_body: The actual response body
        expected_status: The expected HTTP status code

    Returns:
        dict: Validation result with 'passed' (bool) and 'details' (str)
    """
    # Prepare context for LLM validation
    validation_context = {
        "test_name": test_case.get("name", ""),
        "test_description": test_case.get("description", ""),
        "request_body": test_case.get("requestBody", {}),
        "expected_status_code": expected_status,
        "actual_status_code": actual_status,
        "actual_response_body": response_body,
    }

    # Ask LLM to validate intelligently
    try:
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=1024,
            system=EXECUTOR_PROMPT,
            messages=[
                {"role": "user", "content": json.dumps(validation_context, indent=2)}
            ],
            temperature=TEMPERATURE
        )

        response_text = resp.content[0].text.strip()

        # Parse LLM response
        # Expected format: {"passed": true/false, "details": "explanation"}
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            else:
                # Try to find JSON object in the response
                json_start = -1
                for i, char in enumerate(response_text):
                    if char == '{':
                        json_start = i
                        break
                if json_start != -1:
                    response_text = response_text[json_start:]

            validation_result = json.loads(response_text)
            return {
                "passed": validation_result.get("passed", False),
                "details": validation_result.get("details", "")
            }
        except json.JSONDecodeError:
            # Fallback: analyze the text response
            passed = actual_status == expected_status and ("pass" in response_text.lower() or "success" in response_text.lower())
            return {
                "passed": passed,
                "details": response_text
            }

    except Exception as e:
        # Fallback to basic status code validation
        status_match = actual_status == expected_status
        return {
            "passed": status_match,
            "details": f"LLM validation error: {str(e)}. Fallback: Status {actual_status} {'matches' if status_match else 'does not match'} expected {expected_status}."
        }


def execute_tests(testcases_dir=TESTCASES_DIR, base_url=BASE_URL, auth_type=AUTH_TYPE, test_type=None):
    """
    Executor Agent: Execute all test cases and validate results

    Args:
        testcases_dir: Directory containing test case JSON files
        base_url: Base URL for the API endpoints
        auth_type: Authentication type ('basic', 'bearer', 'token', or None)
        test_type: Type of tests to run (integration, system, component, regression, sanity) or None for all

    Returns:
        dict: Summary of test execution results with test_type information
    """
    print(f"🚀 Executor Agent: Loading test cases from '{testcases_dir}'")
    print(f"🔐 Authentication: {auth_type if auth_type else 'None'}")

    # Check if testcases directory exists
    if not os.path.exists(testcases_dir):
        print(f"❌ Error: Test cases directory '{testcases_dir}' not found")
        return {"error": "Test cases directory not found"}

    # Determine test types to run
    test_types = []
    if test_type:
        # Run specific test type
        test_type_dir = os.path.join(testcases_dir, test_type, "testcases")
        if os.path.exists(test_type_dir):
            test_types.append((test_type, test_type_dir))
        else:
            print(f"❌ Error: Test type '{test_type}' directory not found")
            return {"error": f"Test type '{test_type}' not found"}
    else:
        # Run all test types
        for tt in ['integration', 'system', 'component', 'regression', 'sanity']:
            tt_dir = os.path.join(testcases_dir, tt, "testcases")
            if os.path.exists(tt_dir) and os.listdir(tt_dir):
                test_types.append((tt, tt_dir))

    if not test_types:
        print(f"❌ Error: No test type directories with test cases found")
        return {"error": "No test cases found"}

    # Track overall results
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    all_results = []
    results_by_type = {}

    # Execute tests for each test type
    for current_test_type, test_type_dir in test_types:
        print(f"\n{'='*80}")
        print(f"📂 Test Type: {current_test_type.upper()}")
        print(f"{'='*80}")

        # Get all test case files for this test type
        test_files = [f for f in os.listdir(test_type_dir) if f.endswith('.json')]

        if not test_files:
            print(f"⚠️  No test cases found for {current_test_type}")
            continue

        print(f"📋 Found {len(test_files)} test case file(s)")

        type_passed = 0
        type_failed = 0
        type_results = []

        # Execute each test file
        for test_file in sorted(test_files):
            file_path = os.path.join(test_type_dir, test_file)
            print(f"\n{'='*80}")
            print(f"📄 Processing: {test_file}")
            print(f"{'='*80}")

            # Load test case
            with open(file_path, 'r') as f:
                test_data = json.load(f)

            endpoint = test_data.get("endpoint", "")
            method = test_data.get("method", "GET").upper()
            test_cases = test_data.get("testCases", [])

            print(f"🔗 Endpoint: {method} {endpoint}")
            print(f"🧪 Test cases: {len(test_cases)}")

            # Execute each test case for this endpoint
            for idx, test_case in enumerate(test_cases, 1):
                total_tests += 1
                test_name = test_case.get("name", f"Test {idx}")
                description = test_case.get("description", "")
                request_body = test_case.get("requestBody", {})
                params = test_case.get("params", None)
                expected_status = test_case.get("expectedStatusCode", 200)

                print(f"\n   🧪 Test {idx}: {test_name}")
                print(f"      Description: {description}")

                # Execute the API request using Utils smart method selection
                try:
                    # Separate path parameters from query parameters
                    actual_endpoint = endpoint
                    query_params = {}

                    if params:
                        for param_name, param_value in params.items():
                            placeholder = f"{{{param_name}}}"
                            if placeholder in actual_endpoint:
                                # This is a path parameter
                                actual_endpoint = actual_endpoint.replace(placeholder, str(param_value))
                            else:
                                # This is a query parameter
                                query_params[param_name] = param_value

                    # Use Utils.execute_request with smart auth handling
                    response = Utils.execute_request(
                        base_url=base_url,
                        method=method,
                        endpoint=actual_endpoint,
                        request_body=request_body if request_body else None,
                        params=query_params if query_params else None,
                        auth_type=auth_type
                    )

                    actual_status = response.status_code

                    # Try to parse response body as JSON
                    try:
                        response_body = response.json()
                    except:
                        response_body = response.text

                    # Validate using LLM for intelligent validation
                    validation_result = validate_with_llm(
                        test_case=test_case,
                        actual_status=actual_status,
                        response_body=response_body,
                        expected_status=expected_status
                    )

                    # Record result
                    test_result = {
                        "file": test_file,
                        "test_name": test_name,
                        "description": description,
                        "endpoint": endpoint,
                        "method": method,
                        "expected_status": expected_status,
                        "actual_status": actual_status,
                        "passed": validation_result["passed"],
                        "details": validation_result["details"],
                        "response_body": response_body
                    }

                    all_results.append(test_result)
                    type_results.append(test_result)

                    # Update counters
                    if validation_result["passed"]:
                        passed_tests += 1
                        type_passed += 1
                        print(f"      ✅ PASSED")
                    else:
                        failed_tests += 1
                        type_failed += 1
                        print(f"      ❌ FAILED")

                    print(f"      Expected: {expected_status}, Got: {actual_status}")
                    if validation_result["details"]:
                        print(f"      Details: {validation_result['details']}")

                except ValueError as e:
                    print(f"      ❌ Error: {str(e)}")
                    failed_tests += 1
                    type_failed += 1
                    all_results.append({
                        "file": test_file,
                        "test_name": test_name,
                        "description": description,
                        "endpoint": endpoint,
                        "method": method,
                        "expected_status": expected_status,
                        "actual_status": None,
                        "passed": False,
                        "details": str(e),
                        "response_body": None
                    })
                except Exception as e:
                    print(f"      ❌ Unexpected error: {str(e)}")
                    failed_tests += 1
                    type_failed += 1
                    all_results.append({
                        "file": test_file,
                        "test_name": test_name,
                        "description": description,
                        "endpoint": endpoint,
                        "method": method,
                        "expected_status": expected_status,
                        "actual_status": None,
                        "passed": False,
                        "details": f"Error: {str(e)}",
                        "response_body": None
                    })

        # Store results for this test type
        results_by_type[current_test_type] = {
            "passed": type_passed,
            "failed": type_failed,
            "total": type_passed + type_failed,
            "results": type_results
        }

    # Print summary
    print(f"\n{'='*80}")
    print(f"📊 Execution Summary")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")

    pass_rate = 0
    if total_tests > 0:
        pass_rate = (passed_tests / total_tests) * 100
        print(f"📈 Pass Rate: {pass_rate:.1f}%")

    # Save results for each test type
    saved_reports = {}
    for test_type_name, type_data in results_by_type.items():
        if type_data['total'] > 0:
            type_pass_rate = (type_data['passed'] / type_data['total']) * 100

            # Prepare test results data
            test_results_data = {
                "timestamp": datetime.now().isoformat(),
                "test_type": test_type_name,
                "summary": {
                    "total": type_data['total'],
                    "passed": type_data['passed'],
                    "failed": type_data['failed'],
                    "pass_rate": f"{type_pass_rate:.1f}%"
                },
                "results": type_data['results']
            }

            # Save JSON report
            json_path = Utils.save_json_report(test_results_data, test_type_name, testcases_dir)
            print(f"\n💾 {test_type_name.upper()} JSON report saved to: {json_path}")

            # Save HTML report
            html_path = Utils.save_html_report(test_results_data, test_type_name, testcases_dir)
            print(f"🌐 {test_type_name.upper()} HTML report saved to: {html_path}")

            saved_reports[test_type_name] = {
                "json": json_path,
                "html": html_path
            }

    return {
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "pass_rate": f"{pass_rate:.1f}%" if total_tests > 0 else "0%",
        "reports": saved_reports,
        "results_by_type": results_by_type
    }


# ===== Run when executed directly =====
if __name__ == "__main__":
    execute_tests()
