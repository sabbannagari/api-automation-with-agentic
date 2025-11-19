#!/usr/bin/env python3
"""
Code Unit Test Agent - Generates unit tests for code functions/classes

Spawned by Planner Agent when code changes are detected.
"""

import os
import json
from datetime import datetime
from anthropic import Anthropic
from utils import Utils


# ===== Validate authentication early =====
Utils.validate_anthropic_auth()

# ===== Load global config =====
global_config = Utils.read_config()

# ===== Agent config =====
agent_config = Utils.get_agent_config(global_config, "code_unit_agent")

LLM_MODEL = agent_config.get("llm_model", "claude-sonnet-4-5-20250929")
TEMPERATURE = agent_config.get("temperature", 0.2)
MAX_TOKENS = agent_config.get("max_tokens", 16000)

# Load prompt from file
SYSTEM_PROMPT = Utils.read_prompt("code_unit_agent")

# ===== Initialize Anthropic client =====
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_unit_tests(
    target_files: list,
    target_features: list,
    test_type: str = "integration",
    output_dir: str = "test_cases/unit"
) -> dict:
    """
    Generate unit tests for specified code files

    Args:
        target_files: List of files to generate tests for
        target_features: List of features being tested
        test_type: Type of test (used for output directory)
        output_dir: Output directory for test cases

    Returns:
        Dictionary with execution results
    """
    print(f"\n🧪 Generating unit tests...")
    print(f"   Target files: {', '.join(target_files)}")
    print(f"   Features: {', '.join(target_features)}")

    # Load code analysis from logs
    analysis_path = "logs/code_analysis.json"
    if os.path.exists(analysis_path):
        with open(analysis_path, 'r') as f:
            analysis = json.load(f)
    else:
        analysis = {}

    # Build user prompt
    user_prompt = f"""Generate comprehensive unit tests for the following code:

TARGET FILES: {', '.join(target_files)}
TARGET FEATURES: {', '.join(target_features)}

CODE ANALYSIS:
{json.dumps(analysis.get('aggregate_analysis', {}), indent=2)}

Generate unit tests following best practices:
1. Test each function/method independently
2. Cover edge cases and error conditions
3. Include positive and negative test cases
4. Mock external dependencies
5. Ensure high code coverage

Output format: JSON array of test cases
"""

    try:
        # Call LLM
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=TEMPERATURE
        )

        response_text = resp.content[0].text.strip()

        # Parse JSON response
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        else:
            # Find JSON array
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]

        try:
            test_cases = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON parsing error, attempting to extract valid JSON...")
            # Try to find first [ and last ]
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]
                test_cases = json.loads(response_text)
            else:
                raise

        # Save test cases
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(
            output_dir,
            f"{'_'.join(target_files)}_unit_tests.json".replace('/', '_')
        )

        with open(output_file, 'w') as f:
            json.dump(test_cases, f, indent=2)

        test_count = len(test_cases) if isinstance(test_cases, list) else 1

        print(f"   ✅ Generated {test_count} unit test(s)")
        print(f"   💾 Saved to: {output_file}")

        # Calculate cost
        input_tokens = resp.usage.input_tokens
        output_tokens = resp.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000

        return {
            "agent": "code_unit_agent",
            "target_files": target_files,
            "target_features": target_features,
            "test_type": test_type,
            "status": "success",
            "generated": test_count,
            "modified": 0,
            "obsolete": 0,
            "tokens_used": total_tokens,
            "cost": cost,
            "output_file": output_file
        }

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

        return {
            "agent": "code_unit_agent",
            "target_files": target_files,
            "status": "failed",
            "error": str(e),
            "generated": 0,
            "modified": 0,
            "obsolete": 0,
            "tokens_used": 0,
            "cost": 0.0
        }
