import os
import json
import argparse
from datetime import datetime
from utils import Utils

# ===== Validate authentication early =====
# Validate all LLM vendor API keys used in config
Utils.validate_llm_auth()

# ===== Load global config =====
global_config = Utils.read_config()

# ===== Master agent config =====
script_name = Utils.get_script_name(__file__)


def main():
    """
    Master Agent: Single entry point for the automation framework

    Master delegates all tasks to the Decomposer agent, which intelligently
    decomposes tasks and orchestrates specialized agents.
    """
    parser = argparse.ArgumentParser(
        description="Master Agent - Single entry point for API test automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute existing test cases
  python master.py --task "execute testcases"

  # Create and run tests in one go
  python master.py --task "create and run tests"

  # Just create test cases
  python master.py --task "create tests"

  # Future examples (when agents are implemented):
  python master.py --task "run tests and create jira tickets for failures"
  python master.py --task "generate test report"
        """
    )

    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help="Task description (e.g., 'execute testcases', 'create and run tests')"
    )

    args = parser.parse_args()

    print("\n" + "="*80)
    print("🎯 MASTER AGENT - API Test Automation Framework")
    print("="*80)
    print(f"📋 Task: {args.task}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    # Delegate to Decomposer agent
    print("📤 Master Agent: Delegating to Decomposer Agent...")
    print()

    from decomposer import decompose_and_execute

    # Execute task via decomposer
    summary = decompose_and_execute(args.task)

    # Save execution summary
    summary_file = f"master_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Final summary
    print("\n" + "="*80)
    print("✅ MASTER AGENT - Execution Complete")
    print("="*80)
    print(f"📊 Task: {args.task}")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = summary.get("results", [])
    if results:
        print(f"\n   Agents executed: {len(results)}")
        for result in results:
            agent_name = result.get("agent", "unknown")
            status = result.get("status", "unknown")
            symbol = "✅" if status == "completed" else "❌"
            print(f"   {symbol} {agent_name}: {status}")

    print(f"\n💾 Execution summary saved to: {summary_file}")
    print("="*80 + "\n")

    return 0


# ===== Run when executed directly =====
if __name__ == "__main__":
    exit(main())
