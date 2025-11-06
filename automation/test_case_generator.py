import os
import json
import requests
from datetime import datetime
from llm_client import LLMClient
from utils import Utils

# ===== Load global config =====
global_config = Utils.read_config()

# ===== Shared OpenAPI info =====
OPENAPI_URL = global_config["api"]["schema"]
BASE_URL = global_config["api"]["base_url"]

# ===== Test case generator agent config =====
script_name = Utils.get_script_name(__file__)
agent_config = Utils.get_agent_config(global_config, script_name)

OUTPUT_DIR = agent_config.get("output_dir", "testcases")
LLM_VENDOR = agent_config.get("llm_vendor", "anthropic")
LLM_MODEL = agent_config.get("llm_model", "claude-3")
TEMPERATURE = agent_config.get("temperature", 0)
MAX_TOKENS = agent_config.get("max_tokens", 4096)

# Load test case generator prompt from file
TEST_PROMPT = Utils.read_prompt(script_name)

# ===== Initialize LLM client =====
# Validation happens inside LLMClient constructor
client = LLMClient(vendor=LLM_VENDOR, model=LLM_MODEL, temperature=TEMPERATURE)

# ===== Planner function: generate test cases =====
def generate_tests(openapi_url=OPENAPI_URL, output_dir=OUTPUT_DIR, base_url=BASE_URL, test_type=None):
    """
    Planner Agent: Generate test cases from OpenAPI schema

    Args:
        openapi_url: URL to fetch the OpenAPI schema from
        output_dir: Base directory to save generated test cases
        base_url: Base URL for the API endpoints
        test_type: Type of test to generate (integration, component, sanity, system, regression)
                   If None or "all", generates for all test types
    """
    # Supported test types
    SUPPORTED_TEST_TYPES = ["integration", "component", "sanity", "system", "regression"]

    # Determine which test types to generate
    if test_type is None or test_type == "all":
        test_types_to_generate = SUPPORTED_TEST_TYPES
        print(f"🧠 Planner Agent: Generating test cases for all test types")
    elif test_type in SUPPORTED_TEST_TYPES:
        test_types_to_generate = [test_type]
        print(f"🧠 Planner Agent: Generating test cases for {test_type} tests")
    else:
        raise ValueError(f"Invalid test_type: {test_type}. Must be one of {SUPPORTED_TEST_TYPES} or None/all")

    print(f"🧠 Planner Agent: Fetching OpenAPI schema from {openapi_url}")

    # Fetch OpenAPI JSON
    schema = requests.get(openapi_url).json()

    # Prompt LLM to generate test cases (only once)
    print(f"🧠 Test Case Generator Agent: Generating test cases using {LLM_VENDOR}/{LLM_MODEL}")

    response_text = client.generate(
        system_prompt=TEST_PROMPT,
        user_message=json.dumps(schema),
        max_tokens=MAX_TOKENS
    )

    # Try to extract JSON from markdown code blocks if present
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        response_text = response_text[start:end].strip()
    elif "```" in response_text:
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        response_text = response_text[start:end].strip()
    else:
        # Try to find JSON array or object in the response
        # Look for the first [ or { character
        json_start = -1
        for i, char in enumerate(response_text):
            if char in '[{':
                json_start = i
                break

        if json_start != -1:
            response_text = response_text[json_start:]

    # Try to parse JSON with better error handling
    try:
        test_plan = json.loads(response_text)
    except json.JSONDecodeError as e:
        # Save the problematic response for debugging
        debug_file = os.path.join(output_dir, "llm_response_debug.txt")
        with open(debug_file, "w") as f:
            f.write(f"JSON Parse Error: {str(e)}\n")
            f.write(f"Error at line {e.lineno}, column {e.colno}\n\n")
            f.write("=" * 80 + "\n")
            f.write("Raw LLM Response:\n")
            f.write("=" * 80 + "\n")
            f.write(response_text)

        print(f"❌ JSON parsing failed: {str(e)}")
        print(f"📝 Debug info saved to: {debug_file}")
        print(f"\n💡 Tip: The LLM may have generated invalid JSON. Check the debug file for details.")
        raise

    # Process each test type
    total_added = 0
    total_updated = 0
    total_unchanged = 0
    total_deleted = 0

    for current_test_type in test_types_to_generate:
        # Create test type directory
        test_type_dir = os.path.join(output_dir, current_test_type)
        os.makedirs(test_type_dir, exist_ok=True)

        print(f"\n{'='*80}")
        print(f"📂 Processing {current_test_type.upper()} test cases")
        print(f"{'='*80}")

        # Get list of existing test files for this test type
        existing_files = set()
        if os.path.exists(test_type_dir):
            existing_files = {f for f in os.listdir(test_type_dir) if f.endswith('.json')}

        # Track which files we're keeping/creating
        new_files = set()
        added_count = 0
        updated_count = 0
        unchanged_count = 0

        # Process each endpoint's test cases
        for ep in test_plan:
            # Generate clean filename from endpoint path
            endpoint_path = ep["endpoint"]
            # Remove curly braces from path parameters
            clean_path = endpoint_path.replace("{", "").replace("}", "")
            # Replace slashes with underscores and strip leading/trailing underscores
            filename = clean_path.replace("/", "_").strip("_")
            # Add method to make it unique if multiple methods for same endpoint
            method = ep.get("method", "").lower()
            if method:
                filename = f"{filename}_{method}.json"
            else:
                filename = f"{filename}.json"

            new_files.add(filename)
            file_path = os.path.join(test_type_dir, filename)

            # Check if file exists and compare content
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_content = json.load(f)

                # Compare new vs existing content
                if existing_content == ep:
                    unchanged_count += 1
                    print(f"   ⏭️  Unchanged: {filename}")
                else:
                    updated_count += 1
                    print(f"   ♻️  Updated: {filename}")
                    with open(file_path, "w") as f:
                        json.dump(ep, f, indent=2)
            else:
                added_count += 1
                print(f"   ➕ Added: {filename}")
                with open(file_path, "w") as f:
                    json.dump(ep, f, indent=2)

        # Delete obsolete test files (files that exist but are not in new test plan)
        deleted_count = 0
        obsolete_files = existing_files - new_files
        for obsolete_file in obsolete_files:
            deleted_count += 1
            print(f"   ➖ Deleted: {obsolete_file}")
            os.remove(os.path.join(test_type_dir, obsolete_file))

        # Update totals
        total_added += added_count
        total_updated += updated_count
        total_unchanged += unchanged_count
        total_deleted += deleted_count

        # Per test type summary
        print(f"   📊 {current_test_type.upper()} Summary: {added_count} added, {updated_count} updated, {unchanged_count} unchanged, {deleted_count} deleted")

    # Overall summary
    print(f"\n{'='*80}")
    print(f"✅ Test cases managed in '{output_dir}' directory.")
    print(f"   📊 Overall Summary: {total_added} added, {total_updated} updated, {total_unchanged} unchanged, {total_deleted} deleted")
    print(f"{'='*80}")

    return output_dir

# ===== Run when executed directly =====
if __name__ == "__main__":
    generate_tests()

