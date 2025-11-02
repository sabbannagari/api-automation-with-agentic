import os
import json
import requests
from datetime import datetime
from anthropic import Anthropic
from utils import Utils

# ===== Load global config =====
global_config = Utils.read_config()

# ===== Shared OpenAPI info =====
OPENAPI_URL = global_config["api"]["schema"]
BASE_URL = global_config["api"]["base_url"]

# ===== Planner agent config =====
script_name = Utils.get_script_name(__file__)
agent_config = Utils.get_agent_config(global_config, script_name)

OUTPUT_DIR = agent_config.get("output_dir", "testcases")
LLM_MODEL = agent_config.get("llm_model", "claude-3")
TEMPERATURE = agent_config.get("temperature", 0)

# Load planner prompt from file
TEST_PROMPT = Utils.read_prompt(script_name)

# ===== Initialize Anthropic client =====
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ===== Planner function: generate test cases =====
def generate_tests(openapi_url=OPENAPI_URL, output_dir=OUTPUT_DIR, base_url=BASE_URL):
    """
    Planner Agent: Generate test cases from OpenAPI schema

    Args:
        openapi_url: URL to fetch the OpenAPI schema from
        output_dir: Directory to save generated test cases
        base_url: Base URL for the API endpoints
    """
    print(f"🧠 Planner Agent: Fetching OpenAPI schema from {openapi_url}")

    # Fetch OpenAPI JSON
    schema = requests.get(openapi_url).json()

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Prompt LLM to generate test cases
    print(f"🧠 Planner Agent: Generating test cases using {LLM_MODEL}")

    resp = client.messages.create(
        model=LLM_MODEL,
        max_tokens=4096,
        system=TEST_PROMPT,
        messages=[
            {"role": "user", "content": json.dumps(schema)}
        ],
        temperature=TEMPERATURE
    )

    # Parse generated test plan
    response_text = resp.content[0].text

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

    test_plan = json.loads(response_text)

    # Get list of existing test files
    existing_files = set()
    if os.path.exists(output_dir):
        existing_files = {f for f in os.listdir(output_dir) if f.endswith('.json')}

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
        file_path = os.path.join(output_dir, filename)

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
        os.remove(os.path.join(output_dir, obsolete_file))

    # Summary
    print(f"\n✅ Test cases managed in '{output_dir}' directory.")
    print(f"   📊 Summary: {added_count} added, {updated_count} updated, {unchanged_count} unchanged, {deleted_count} deleted")

    return output_dir

# ===== Run when executed directly =====
if __name__ == "__main__":
    generate_tests()

