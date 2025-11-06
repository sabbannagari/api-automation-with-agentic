import os
import json
from datetime import datetime
from llm_client import LLMClient
from utils import Utils

# ===== Load global config =====
global_config = Utils.read_config()

# ===== Decomposer agent config =====
script_name = Utils.get_script_name(__file__)
agent_config = Utils.get_agent_config(global_config, script_name)

LLM_VENDOR = agent_config.get("llm_vendor", "anthropic")
LLM_MODEL = agent_config.get("llm_model", "claude-3-haiku-20240307")
TEMPERATURE = agent_config.get("temperature", 0)

# Load decomposer prompt from file
DECOMPOSER_PROMPT = Utils.read_prompt(script_name)

# ===== Initialize LLM client =====
# Validation happens inside LLMClient constructor
client = LLMClient(vendor=LLM_VENDOR, model=LLM_MODEL, temperature=TEMPERATURE)


def get_available_agents():
    """
    Fetch available agents from config.json

    Returns:
        dict: Available agents with their metadata
    """
    available_agents = {}

    for agent_name, agent_config in global_config.get("agents", {}).items():
        # Skip master and decomposer (not executable agents)
        if agent_name in ["master", "decomposer"]:
            continue

        # Only include agents that have module and function defined
        if "module" in agent_config and "function" in agent_config:
            available_agents[agent_name] = {
                "description": agent_config.get("description", "No description"),
                "module": agent_config.get("module"),
                "function": agent_config.get("function"),
                "capabilities": agent_config.get("capabilities", [])
            }

    return available_agents


def decompose_and_execute(task_description):
    """
    Decomposer Agent: Main function that decomposes task and executes agents

    This follows the same framework pattern as other agents (test_case_generator, test_case_executor)

    Args:
        task_description: High-level task description from master

    Returns:
        dict: Execution summary with results from all agents
    """
    print(f"🧠 Decomposer Agent: Starting task decomposition")
    print(f"   Task: '{task_description}'")
    print(f"{'='*80}\n")

    # Step 1: Use LLM to decompose the task into a plan
    plan = decompose_task_with_llm(task_description)

    # Step 2: Execute the plan by running agents sequentially
    results = execute_plan(plan)

    # Step 3: Return summary
    print(f"\n{'='*80}")
    print(f"✅ Decomposer Agent: Task completed")
    print(f"{'='*80}")

    return {
        "task": task_description,
        "plan": plan,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


def decompose_task_with_llm(task_description):
    """
    Use LLM to intelligently decompose task into subtasks

    Args:
        task_description: High-level task description

    Returns:
        dict: Plan with agents to execute, execution mode, and reasoning
    """
    print(f"🤔 Decomposer Agent: Analyzing task with LLM...")

    # Get available agents from config
    available_agents = get_available_agents()

    # Prepare context for LLM
    context = {
        "task": task_description,
        "available_agents": {
            name: {
                "description": info["description"],
                "capabilities": info["capabilities"]
            }
            for name, info in available_agents.items()
        },
        "config": {
            "api_base_url": global_config["api"]["base_url"],
            "api_schema_url": global_config["api"]["schema"],
            "testcases_directory": global_config["agents"]["test_case_generator"]["output_dir"],
            "auth_type": global_config["api"].get("auth_type", None)
        }
    }

    try:
        # Ask LLM to decompose the task
        response_text = client.generate(
            system_prompt=DECOMPOSER_PROMPT,
            user_message=json.dumps(context, indent=2),
            max_tokens=2048
        ).strip()

        # Parse LLM response
        plan = parse_llm_response(response_text)

        # Display the plan
        print(f"\n📋 Task Decomposition:")
        print(f"   Reasoning: {plan.get('reasoning', 'N/A')}")
        print(f"   Execution Mode: {plan.get('execution_mode', 'sequential')}")
        print(f"   Agents to execute: {', '.join(plan.get('agents', []))}")

        if plan.get('subtasks'):
            print(f"\n   Planned Subtasks:")
            for idx, subtask in enumerate(plan['subtasks'], 1):
                agent = subtask.get('agent', 'unknown')
                task = subtask.get('task', 'N/A')
                print(f"      {idx}. [{agent}] {task}")
        print()

        return plan

    except Exception as e:
        error_msg = str(e)

        # Check if it's an authentication error - fail immediately
        if "authentication" in error_msg.lower() or "api_key" in error_msg.lower() or "auth_token" in error_msg.lower():
            print(f"❌ Authentication Error: {error_msg}")
            print(f"   Please set the ANTHROPIC_API_KEY environment variable")
            raise SystemExit(1)

        # For other errors, use fallback
        print(f"⚠️  LLM decomposition failed: {error_msg}")
        print(f"   Using fallback heuristic...")
        return fallback_decompose(task_description)


def parse_llm_response(response_text):
    """Parse LLM response and extract JSON plan"""
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
        # Try to find JSON object
        json_start = -1
        for i, char in enumerate(response_text):
            if char == '{':
                json_start = i
                break
        if json_start != -1:
            response_text = response_text[json_start:]

    return json.loads(response_text)


def fallback_decompose(task_description):
    """Fallback heuristic if LLM fails"""
    task_lower = task_description.lower()

    if ("create" in task_lower or "generate" in task_lower) and ("run" in task_lower or "execute" in task_lower):
        return {
            "reasoning": "Fallback: Detected create + execute keywords",
            "agents": ["test_case_generator", "test_case_executor"],
            "execution_mode": "sequential",
            "subtasks": [
                {"agent": "test_case_generator", "task": "Generate test cases", "depends_on": None},
                {"agent": "test_case_executor", "task": "Execute test cases", "depends_on": ["test_case_generator"]}
            ]
        }
    elif "execute" in task_lower or "run" in task_lower:
        return {
            "reasoning": "Fallback: Detected execute keyword",
            "agents": ["test_case_executor"],
            "execution_mode": "sequential",
            "subtasks": [{"agent": "test_case_executor", "task": "Execute test cases", "depends_on": None}]
        }
    elif "create" in task_lower or "generate" in task_lower:
        return {
            "reasoning": "Fallback: Detected create keyword",
            "agents": ["test_case_generator"],
            "execution_mode": "sequential",
            "subtasks": [{"agent": "test_case_generator", "task": "Generate test cases", "depends_on": None}]
        }
    else:
        return {
            "reasoning": "Fallback: No matching keywords",
            "agents": [],
            "execution_mode": "sequential",
            "subtasks": []
        }


def execute_plan(plan):
    """
    Execute the decomposed plan by running agents in sequence

    Args:
        plan: Decomposed plan with agents list

    Returns:
        list: Results from each agent execution
    """
    agents_to_run = plan.get("agents", [])
    subtasks = plan.get("subtasks", [])

    if not agents_to_run:
        print("⚠️  No agents to execute")
        return []

    print(f"🚀 Decomposer Agent: Executing {len(agents_to_run)} agent(s)\n")

    results = []

    for i, agent_name in enumerate(agents_to_run):
        # Get corresponding subtask for this agent
        subtask = None
        for st in subtasks:
            if st.get("agent") == agent_name:
                subtask = st
                break

        result = execute_agent(agent_name, subtask)
        results.append(result)

        # Stop if agent fails
        if result.get("status") == "error":
            print(f"\n❌ Stopping execution due to {agent_name} failure")
            break

    return results


def execute_agent(agent_name, subtask=None):
    """
    Execute a specific specialized agent

    Args:
        agent_name: Name of the agent to execute
        subtask: Subtask info containing task description and parameters

    Returns:
        dict: Execution result
    """
    # Get available agents from config
    available_agents = get_available_agents()

    if agent_name not in available_agents:
        return {
            "agent": agent_name,
            "status": "error",
            "error": f"Unknown agent: {agent_name}"
        }

    agent_info = available_agents[agent_name]
    module_name = agent_info["module"]
    function_name = agent_info["function"]

    print(f"\n{'='*80}")
    print(f"🤖 Decomposer Agent: Invoking {agent_name}")
    print(f"   {agent_info['description']}")
    print(f"{'='*80}")

    try:
        # Dynamically import and execute
        module = __import__(module_name)
        agent_function = getattr(module, function_name)

        # Extract params from subtask if provided
        if agent_name == "test_case_executor" and subtask:
            params = subtask.get("params", {})
            test_type = params.get("test_type")

            # Call with test_type parameter if provided
            if test_type:
                result = agent_function(test_type=test_type)
            else:
                result = agent_function()
        else:
            result = agent_function()

        return {
            "agent": agent_name,
            "status": "completed",
            "result": result
        }

    except Exception as e:
        print(f"❌ Error executing {agent_name}: {str(e)}")
        return {
            "agent": agent_name,
            "status": "error",
            "error": str(e)
        }


# ===== Run when executed directly (for testing) =====
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = "create and run tests"

    summary = decompose_and_execute(task)
    print(f"\n📊 Summary: {json.dumps(summary, indent=2)}")
