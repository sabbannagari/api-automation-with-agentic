#!/usr/bin/env python3
"""
Planner Agent - Creates execution plan for spawning specialized agents

Called by master.py to determine which agents to spawn based on code analysis.
"""

import os
import json
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


# ===== Load config =====
global_config = Utils.read_config()
agent_config = Utils.get_agent_config(global_config, "planner_agent")

LLM_MODEL = agent_config.get("llm_model", "claude-sonnet-4-5-20250929")
TEMPERATURE = agent_config.get("temperature", 0.2)

# Load prompt
SYSTEM_PROMPT = Utils.read_prompt("planner_agent")

# ===== Initialize client =====
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def create_execution_plan(analysis_data: dict) -> dict:
    """
    Create execution plan from code analysis

    Args:
        analysis_data: Code analysis results

    Returns:
        Execution plan with agent tasks
    """
    print("\n🎯 Planner Agent: Creating execution plan...")

    aggregate = analysis_data.get("aggregate_analysis", {})

    # Build user prompt
    user_prompt = f"""Create an execution plan for test generation.

CODE ANALYSIS:
{json.dumps(aggregate, indent=2)}

Create a plan that spawns the right specialized agents based on this analysis."""

    try:
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=TEMPERATURE
        )

        response_text = resp.content[0].text.strip()

        # Parse JSON
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        else:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            response_text = response_text[json_start:json_end]

        plan = json.loads(response_text)

        # Print summary in tabular format
        print(f"\n{'='*80}")
        print("🎯 EXECUTION PLAN - TABULAR REPORT")
        print(f"{'='*80}\n")

        # Prepare table data
        headers = ["Agent Type", "Priority", "Mode", "Target Features", "Est. Cost ($)"]
        rows = []

        for task in plan.get("agent_tasks", []):
            agent_type = task.get('agent_type', 'unknown').replace('_agent', '').upper()
            priority = task.get('priority', 'medium').upper()
            mode = task.get('execution_mode', 'parallel')

            features = ', '.join(task.get('target_features', [])[:2])
            if len(task.get('target_features', [])) > 2:
                features += f" (+{len(task.get('target_features', [])) - 2})"

            cost = f"{task.get('estimated_cost', 0):.2f}"

            rows.append([agent_type, priority, mode, features, cost])

        # Print table
        print_table(headers, rows)

        # Overall summary
        exec_plan = plan.get('execution_plan', {})
        print(f"\n📈 Plan Summary:")
        print(f"   Strategy: {exec_plan.get('strategy', 'unknown')}")
        print(f"   Total Agents: {len(plan.get('agent_tasks', []))}")
        print(f"   Estimated Total Cost: ${exec_plan.get('estimated_total_cost', 0):.2f}")
        print(f"   Estimated Time: {exec_plan.get('estimated_time_minutes', 0)} minutes")
        print(f"{'='*80}\n")

        return plan

    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return {"error": str(e)}
