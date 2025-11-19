#!/usr/bin/env python3
"""
Code Analyzer Agent - Simple intelligent code analysis

Analyzes code changes and identifies features, test requirements, and agents to spawn.

Usage:
    python code_analyzer_agent.py --changes logs/llm_ready_changes.json
"""

import os
import sys
import json
from datetime import datetime
from anthropic import Anthropic
from utils import Utils


def print_table(headers, rows):
    """Print formatted table"""
    if not rows:
        return

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Add padding
    col_widths = [w + 2 for w in col_widths]

    # Print separator
    def print_separator():
        print("+" + "+".join(["-" * w for w in col_widths]) + "+")

    # Print header
    print_separator()
    header_str = "|" + "|".join([f" {h:<{col_widths[i]-1}}" for i, h in enumerate(headers)]) + "|"
    print(header_str)
    print_separator()

    # Print rows
    for row in rows:
        row_str = "|" + "|".join([f" {str(cell):<{col_widths[i]-1}}" for i, cell in enumerate(row)]) + "|"
        print(row_str)

    print_separator()


# ===== Validate authentication early =====
Utils.validate_anthropic_auth()

# ===== Load global config =====
global_config = Utils.read_config()

# ===== Agent config =====
script_name = Utils.get_script_name(__file__)
agent_config = Utils.get_agent_config(global_config, script_name)

LLM_MODEL = agent_config.get("llm_model", "claude-sonnet-4-5-20250929")
TEMPERATURE = agent_config.get("temperature", 0.3)

# Load prompt from file
SYSTEM_PROMPT = Utils.read_prompt("code_analyzer_system")

# ===== Initialize Anthropic client =====
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def analyze_code_change(change_data: dict) -> dict:
    """
    Analyze a single code file change using LLM

    Args:
        change_data: Change data from get_changes.py

    Returns:
        Analysis result with features, test requirements, recommended agents
    """
    file_info = change_data.get("file_info", {})
    content = change_data.get("content", {})

    filename = file_info.get("name", "")
    filepath = file_info.get("path", "")

    print(f"   📄 Analyzing: {filename}")

    # Build user prompt
    # Safely get content
    current_content = (content.get("current_content") or "")[:3000]
    diff_content = (content.get("diff") or "")[:2000]
    key_changes = content.get("key_changes", [])

    user_prompt = f"""Analyze this code change:

FILE INFORMATION:
- Path: {filepath}
- Name: {filename}
- Change Type: {change_data.get("change_info", {}).get("type", "modified")}

CURRENT CODE CONTENT (first 3000 chars):
```
{current_content}
```

GIT DIFF (first 2000 chars):
```
{diff_content}
```

KEY CHANGES DETECTED:
{json.dumps(key_changes, indent=2)}

Analyze this change and provide your assessment in the JSON format specified in the system prompt."""

    try:
        # Call LLM
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE
        )

        response_text = resp.content[0].text.strip()

        # Parse JSON response
        analysis = parse_json_response(response_text)

        print(f"      ✅ Features: {', '.join(analysis.get('affected_features', [])[:2])}")
        print(f"      ✅ Agents: {', '.join(analysis.get('recommended_agents', [])[:2])}")

        return analysis

    except Exception as e:
        print(f"      ⚠️  Error: {e}")
        return {
            "error": str(e),
            "file": filepath
        }


def parse_json_response(response_text: str) -> dict:
    """Parse JSON from LLM response"""
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
            # Find JSON object
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]

        return json.loads(response_text)

    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse JSON: {e}",
            "raw_response": response_text[:500]
        }


def analyze_all_changes(changes_path: str = "logs/llm_ready_changes.json") -> dict:
    """
    Analyze all code changes from get_changes.py output

    Args:
        changes_path: Path to changes JSON file

    Returns:
        Analysis results for all code changes
    """
    print("\n" + "="*80)
    print("🤖 CODE ANALYZER AGENT")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Load changes
    if not os.path.exists(changes_path):
        print(f"\n❌ Changes file not found: {changes_path}")
        print("Run get_changes.py first!")
        return {"error": "Changes file not found"}

    with open(changes_path, 'r') as f:
        changes_data = json.load(f)

    detailed_changes = changes_data.get("detailed_changes", [])

    # Filter code changes
    code_changes = [
        c for c in detailed_changes
        if c.get("file_info", {}).get("artifact_type") == "code"
    ]

    if not code_changes:
        print("\nℹ️  No code changes to analyze")
        return {
            "code_changes": [],
            "analysis": None,
            "analyzed_at": datetime.now().isoformat()
        }

    print(f"\n📋 Found {len(code_changes)} code file(s) to analyze\n")

    # Analyze each code file
    analyses = []
    for change in code_changes:
        analysis = analyze_code_change(change)
        analyses.append({
            "file": change.get("file_info", {}).get("path", ""),
            "filename": change.get("file_info", {}).get("name", ""),
            "analysis": analysis
        })

    # Aggregate analysis
    print(f"\n🧠 Aggregating analysis...")
    aggregate = aggregate_analyses(analyses, changes_data)

    result = {
        "individual_analyses": analyses,
        "aggregate_analysis": aggregate,
        "analyzed_at": datetime.now().isoformat()
    }

    # Export results
    os.makedirs("logs", exist_ok=True)
    output_path = "logs/code_analysis.json"

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n{'='*80}")
    print(f"💾 Analysis saved to: {output_path}")
    print(f"{'='*80}")

    # Print summary in tabular format
    if aggregate:
        print(f"\n{'='*80}")
        print("📊 CODE ANALYSIS SUMMARY - TABULAR REPORT")
        print(f"{'='*80}\n")

        # Prepare table data
        headers = ["File", "Features", "Impact", "Security Risk", "Performance Risk", "Tests Needed"]
        rows = []

        for analysis in analyses:
            llm_analysis = analysis.get('analysis', {})
            filename = analysis.get('filename', 'unknown')
            features = ', '.join(llm_analysis.get('affected_features', [])[:2])
            if len(llm_analysis.get('affected_features', [])) > 2:
                features += f" (+{len(llm_analysis.get('affected_features', [])) - 2})"

            impact = llm_analysis.get('impact_assessment', {}).get('scope', 'N/A')
            security_risk = llm_analysis.get('risk_assessment', {}).get('security_risk', 'N/A')
            perf_risk = llm_analysis.get('risk_assessment', {}).get('performance_risk', 'N/A')

            test_req = llm_analysis.get('test_requirements', {})
            tests_needed = []
            if test_req.get('unit_tests'): tests_needed.append('Unit')
            if test_req.get('security_tests'): tests_needed.append('Security')
            if test_req.get('performance_tests'): tests_needed.append('Perf')
            tests_str = ', '.join(tests_needed) if tests_needed else 'None'

            rows.append([filename, features, impact, security_risk, perf_risk, tests_str])

        # Print table
        print_table(headers, rows)

        # Overall summary
        print(f"📈 Overall Summary:")
        print(f"   Files Analyzed: {len(analyses)}")
        print(f"   Overall Impact: {aggregate.get('overall_impact', {}).get('scope', 'unknown')}")
        all_features = aggregate.get('overall_impact', {}).get('affected_features', [])
        if all_features:
            print(f"   Total Features: {len(all_features)} ({', '.join(all_features[:3])})")

        risk_summary = aggregate.get('risk_summary', {})
        print(f"   Security Risk: {risk_summary.get('overall_security_risk', 'unknown')}")
        print(f"   Performance Risk: {risk_summary.get('overall_performance_risk', 'unknown')}")

    print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    return result


def aggregate_analyses(analyses: list, changes_data: dict) -> dict:
    """
    Aggregate individual analyses into overall assessment

    Args:
        analyses: List of individual file analyses
        changes_data: Original changes data

    Returns:
        Aggregate analysis
    """
    # Load aggregate prompt
    aggregate_prompt_text = Utils.read_prompt("code_analyzer_aggregate")

    # Build user prompt
    user_prompt = aggregate_prompt_text.format(
        commit_info=json.dumps(changes_data.get('metadata', {}), indent=2),
        individual_analyses=json.dumps([a.get('analysis', {}) for a in analyses], indent=2)
    )

    try:
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=4000,
            system="You are a senior Code Analyzer Agent providing aggregate analysis.",
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE
        )

        response_text = resp.content[0].text.strip()
        aggregate = parse_json_response(response_text)

        print(f"   ✅ Aggregate analysis complete")

        return aggregate

    except Exception as e:
        print(f"   ⚠️  Error in aggregation: {e}")
        return {
            "error": str(e),
            "fallback": "aggregation_failed"
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Code Analyzer Agent")
    parser.add_argument(
        "--changes",
        type=str,
        default="logs/llm_ready_changes.json",
        help="Path to changes JSON file from get_changes.py"
    )

    args = parser.parse_args()

    try:
        result = analyze_all_changes(args.changes)

        if result.get("error"):
            return 1

        print("🎯 Next: Pass to Planner Agent!")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
