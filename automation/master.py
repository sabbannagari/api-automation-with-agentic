#!/usr/bin/env python3
"""
Master Test Case Generator - Artifact-Driven Test Generation

This script orchestrates test case generation based on artifacts found in test_case_artifacts directory.
It dynamically detects artifacts, spawns appropriate agents, and generates test cases in parallel.

Usage:
    python master.py -test-case-type <type>

Arguments:
    -test-case-type: Type of test cases to generate
                     Options: integration, component, system, regression, all

Examples:
    python master.py -test-case-type integration
    python master.py -test-case-type all
"""

import os
import sys
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from artifact_detector import ArtifactDetector
from agent_executor import AgentExecutor
from utils import Utils
import get_changes
import code_analyzer_agent
import planner_agent


# ===== Validate authentication early =====
Utils.validate_llm_auth()

# ===== Load global config =====
global_config = Utils.read_config()


def print_table(headers: List[str], rows: List[List], col_widths: List[int] = None):
    """
    Print a formatted table

    Args:
        headers: List of header names
        rows: List of rows (each row is a list of values)
        col_widths: Optional list of column widths
    """
    if not col_widths:
        # Auto-calculate column widths
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


def execute_specialized_agent(
    agent_task: Dict,
    test_type: str,
    config: Dict
) -> Dict:
    """
    Execute a specialized agent from Planner's execution plan

    Args:
        agent_task: Agent task from planner (with agent_type, target_files, etc.)
        test_type: Type of test to generate
        config: Global configuration

    Returns:
        Dictionary with execution results
    """
    agent_type = agent_task.get("agent_type")
    target_files = agent_task.get("target_files", [])
    target_features = agent_task.get("target_features", [])
    priority = agent_task.get("priority", "medium")

    print(f"\n{'='*80}")
    print(f"🤖 Specialized Agent: {agent_type}")
    print(f"🎯 Target Files: {', '.join(target_files)}")
    print(f"🏆 Priority: {priority.upper()}")
    print(f"📋 Features: {', '.join(target_features)}")
    print(f"{'='*80}")

    # Get output directory from config
    test_types = config.get("test_types", {})
    test_type_config = test_types.get(test_type, {})
    output_dir = test_type_config.get("output_dir", f"test_cases/{test_type}")

    # Execute the appropriate specialized agent
    try:
        if agent_type == "code_unit_agent":
            import code_unit_agent
            return code_unit_agent.generate_unit_tests(
                target_files=target_files,
                target_features=target_features,
                test_type=test_type,
                output_dir=output_dir
            )
        elif agent_type == "code_security_agent":
            import code_security_agent
            return code_security_agent.generate_security_tests(
                target_files=target_files,
                target_features=target_features,
                test_type=test_type,
                output_dir=output_dir
            )
        elif agent_type == "code_integration_agent":
            # Not implemented yet
            print(f"⚠️  Agent '{agent_type}' not yet implemented")
            return {
                "agent": agent_type,
                "target_files": target_files,
                "target_features": target_features,
                "test_type": test_type,
                "status": "pending_implementation",
                "error": f"Agent {agent_type} not yet implemented",
                "generated": 0,
                "modified": 0,
                "obsolete": 0,
                "tokens_used": 0,
                "cost": 0.0
            }
        else:
            print(f"⚠️  Unknown agent type: '{agent_type}'")
            return {
                "agent": agent_type,
                "target_files": target_files,
                "target_features": target_features,
                "test_type": test_type,
                "status": "failed",
                "error": f"Unknown agent type: {agent_type}",
                "generated": 0,
                "modified": 0,
                "obsolete": 0,
                "tokens_used": 0,
                "cost": 0.0
            }

    except Exception as e:
        print(f"❌ Error executing {agent_type}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "agent": agent_type,
            "target_files": target_files,
            "target_features": target_features,
            "test_type": test_type,
            "status": "failed",
            "error": str(e),
            "generated": 0,
            "modified": 0,
            "obsolete": 0,
            "tokens_used": 0,
            "cost": 0.0
        }


def execute_single_agent(
    executor: AgentExecutor,
    artifact: Dict,
    test_type: str,
    config: Dict
) -> Dict:
    """
    Execute a single agent for an artifact

    Args:
        executor: AgentExecutor instance
        artifact: Artifact information
        test_type: Type of test to generate
        config: Global configuration

    Returns:
        Dictionary with execution results
    """
    agent_name = artifact.get("agent")
    artifact_path = artifact.get("path")
    artifact_filename = artifact.get("filename")

    print(f"\n{'='*80}")
    print(f"🤖 Agent: {agent_name}")
    print(f"📄 Artifact: {artifact_filename}")
    print(f"🧪 Test Type: {test_type}")
    print(f"{'='*80}")

    if not agent_name:
        print(f"❌ No agent configured for this artifact type")
        return {
            "agent": "unknown",
            "artifact": artifact_filename,
            "status": "failed",
            "error": "No agent configured",
            "generated": 0,
            "modified": 0,
            "obsolete": 0,
            "tokens_used": 0,
            "cost": 0.0
        }

    # Get output directory for test type
    test_types = config.get("test_types", {})
    test_type_config = test_types.get(test_type, {})
    output_dir = test_type_config.get("output_dir", f"test_cases/{test_type}")

    # Execute the agent
    try:
        result = executor.execute_agent(
            agent_name=agent_name,
            artifact_path=artifact_path,
            test_type=test_type,
            output_dir=output_dir
        )

        print(f"✅ Agent execution completed")
        return result

    except Exception as e:
        print(f"❌ Agent execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "agent": agent_name,
            "artifact": artifact_filename,
            "test_type": test_type,
            "status": "failed",
            "error": str(e),
            "generated": 0,
            "modified": 0,
            "obsolete": 0,
            "tokens_used": 0,
            "cost": 0.0
        }


def execute_specialized_agents(
    agent_tasks: List[Dict],
    test_type: str,
    config: Dict,
    max_workers: int = 3
) -> List[Dict]:
    """
    Execute specialized agents from Planner's execution plan

    Args:
        agent_tasks: List of agent tasks from planner
        test_type: Type of test to generate
        config: Global configuration
        max_workers: Maximum number of parallel workers

    Returns:
        List of execution results
    """
    results = []

    if not agent_tasks:
        print("   ℹ️  No specialized agents recommended by planner")
        return results

    print(f"\n🚀 Executing {len(agent_tasks)} specialized agent(s) from execution plan...")
    print(f"   Max workers: {max_workers}\n")

    # Execute agents in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor_pool:
        futures = {
            executor_pool.submit(
                execute_specialized_agent,
                agent_task,
                test_type,
                config
            ): agent_task
            for agent_task in agent_tasks
        }

        for future in as_completed(futures):
            agent_task = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Unexpected error processing {agent_task.get('agent_type')}: {e}")
                results.append({
                    "agent": agent_task.get("agent_type"),
                    "status": "failed",
                    "error": str(e),
                    "generated": 0,
                    "modified": 0,
                    "obsolete": 0,
                    "tokens_used": 0,
                    "cost": 0.0
                })

    return results


def execute_agents_parallel(
    artifacts: List[Dict],
    test_type: str,
    config: Dict,
    max_workers: int = 3
) -> List[Dict]:
    """
    Execute multiple agents in parallel

    Args:
        artifacts: List of detected artifacts
        test_type: Type of test to generate
        config: Global configuration
        max_workers: Maximum number of parallel workers

    Returns:
        List of execution results
    """
    results = []
    executor = AgentExecutor()

    # Filter out unknown artifacts
    valid_artifacts = [a for a in artifacts if a.get("agent") is not None]

    if not valid_artifacts:
        print("⚠️  No valid artifacts found to process")
        return results

    print(f"\n🚀 Executing {len(valid_artifacts)} agent(s) in parallel (max workers: {max_workers})...")

    # Execute agents in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor_pool:
        futures = {
            executor_pool.submit(
                execute_single_agent,
                executor,
                artifact,
                test_type,
                config
            ): artifact
            for artifact in valid_artifacts
        }

        for future in as_completed(futures):
            artifact = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Unexpected error processing {artifact.get('filename')}: {e}")
                results.append({
                    "agent": artifact.get("agent"),
                    "artifact": artifact.get("filename"),
                    "status": "failed",
                    "error": str(e),
                    "generated": 0,
                    "modified": 0,
                    "obsolete": 0,
                    "tokens_used": 0,
                    "cost": 0.0
                })

    return results


def main():
    """
    Main entry point for the artifact-driven test case generator
    """
    parser = argparse.ArgumentParser(
        description="Master Test Case Generator - Artifact-Driven",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate integration tests from all artifacts
  python master.py -test-case-type integration

  # Generate all types of tests
  python master.py -test-case-type all

  # Generate component tests
  python master.py -test-case-type component
        """
    )

    parser.add_argument(
        "--task",
        dest="task",
        type=str,
        required=True,
        help="Type of test cases to generate"
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum number of parallel agent workers (default: 3)"
    )

    args = parser.parse_args()

    # Print header
    print("\n" + "="*80)
    print("🎯 MASTER TEST CASE GENERATOR - TDAG (Task Decomposition + Agent Generation)")
    print("="*80)
    print(f"Task: {args.task}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Step 0: Detect changes from git
    print("\n🔍 Step 0: Detecting Changes from Git...")
    changes = get_changes.get_changed_files()

    if changes:
        categorized = get_changes.categorize_changes(changes)
        get_changes.print_summary(changes, categorized)
        changes_file = get_changes.export_changes(changes)

        # Step 0.5: Analyze code changes intelligently
        print("\n🤖 Step 0.5: Analyzing Code Changes (Code Analyzer Agent)...")
        analysis = code_analyzer_agent.analyze_all_changes(changes_file)

        if analysis.get("aggregate_analysis"):
            print("   ✅ Code analysis complete")

            # Step 0.75: Create execution plan (Planner Agent)
            print("\n🎯 Step 0.75: Creating Execution Plan (Planner Agent)...")
            execution_plan = planner_agent.create_execution_plan(analysis)

            # Step 0.9: Execute specialized agents from plan
            specialized_results = []
            if execution_plan.get("agent_tasks"):
                print(f"   ✅ Execution plan ready: {len(execution_plan['agent_tasks'])} specialized agent(s)")

                print(f"\n⚙️  Step 0.9: Executing Specialized Agents from Plan...")
                specialized_results = execute_specialized_agents(
                    agent_tasks=execution_plan.get("agent_tasks", []),
                    test_type=args.task,
                    config=global_config,
                    max_workers=args.max_workers
                )
            else:
                print("   ℹ️  No specialized agents recommended")
    else:
        print("   ℹ️  No changes detected, using existing artifacts")
        specialized_results = []

    # Step 1: Detect artifacts
    print("\n📦 Step 1: Detecting Artifacts...")
    detector = ArtifactDetector()
    artifacts = detector.detect_artifacts()

    if not artifacts:
        print("\n⚠️  No artifacts found in test_case_artifacts/ directory")
        print("\nSupported artifact types:")
        for artifact_type, config in detector.mappings.items():
            print(f"  • {artifact_type}: {config.get('description')}")
            print(f"    Patterns: {', '.join(config.get('patterns', []))}")

        # Check if we have specialized agents to run
        if not specialized_results:
            print("\n❌ No specialized agents and no artifacts found. Nothing to do.")
            return 1
        else:
            print(f"\n✅ Proceeding with {len(specialized_results)} specialized agent(s) from execution plan")
            results = []
    else:
        # Print detection summary
        detector.print_detection_summary(artifacts)

        # Step 2: Execute artifact-based agents
        print(f"\n⚙️  Step 2: Generating {args.task.upper()} Test Cases from Artifacts...")
        results = execute_agents_parallel(
            artifacts=artifacts,
            test_type=args.task,
            config=global_config,
            max_workers=args.max_workers
        )

    # Step 3: Print summary in tabular format
    print("\n" + "="*80)
    print("📊 EXECUTION SUMMARY - TABULAR REPORT")
    print("="*80 + "\n")

    # Combine specialized and artifact-based results
    all_results = specialized_results + results

    # Prepare table data
    headers = ["Agent Type", "Test Type", "Generated", "Modified", "Obsolete", "Tokens", "Cost ($)"]
    table_rows = []

    total_generated = 0
    total_modified = 0
    total_obsolete = 0
    total_tokens = 0
    total_cost = 0.0

    successful = [r for r in all_results if r.get("status") == "success"]
    failed = [r for r in all_results if r.get("status") == "failed"]
    pending = [r for r in all_results if r.get("status") == "pending_implementation"]

    # Add successful agents to table
    for result in successful:
        agent_short = result.get("agent", "").replace("_test_generator", "").upper()
        test_type = result.get("test_type", "").upper()
        generated = result.get("generated", 0)
        modified = result.get("modified", 0)
        obsolete = result.get("obsolete", 0)
        tokens = result.get("tokens_used", 0)
        cost = result.get("cost", 0.0)

        table_rows.append([
            agent_short,
            test_type,
            str(generated),
            str(modified),
            str(obsolete),
            str(tokens),
            f"{cost:.4f}"
        ])

        total_generated += generated
        total_modified += modified
        total_obsolete += obsolete
        total_tokens += tokens
        total_cost += cost

    # Add failed agents to table
    for result in failed:
        agent_short = result.get("agent", "").replace("_test_generator", "").upper()
        test_type = result.get("test_type", "").upper()
        table_rows.append([
            agent_short,
            test_type,
            "FAILED",
            "FAILED",
            "FAILED",
            "0",
            "0.0000"
        ])

    # Add pending agents to table (not yet implemented)
    for result in pending:
        agent_short = result.get("agent", "").replace("_agent", "").upper()
        test_type = result.get("test_type", "").upper()
        table_rows.append([
            agent_short,
            test_type,
            "PENDING",
            "PENDING",
            "PENDING",
            "0",
            "0.0000"
        ])

    # Add total row
    table_rows.append([
        "TOTAL",
        "",
        str(total_generated),
        str(total_modified),
        str(total_obsolete),
        str(total_tokens),
        f"{total_cost:.4f}"
    ])

    # Print the table
    print_table(headers, table_rows)

    # Print additional details
    print(f"\n📈 Summary:")
    print(f"   Total Agents Executed: {len(all_results)}")
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ❌ Failed: {len(failed)}")
    print(f"   ⏳ Pending Implementation: {len(pending)}")

    if pending:
        print(f"\n⏳ Pending Agents (not yet implemented):")
        for result in pending:
            print(f"   • {result.get('agent')}")
            print(f"     Target: {', '.join(result.get('target_features', []))}")

    if failed:
        print(f"\n❌ Failed Agents:")
        for result in failed:
            artifact_name = result.get('artifact', '') or ', '.join(result.get('target_files', []))
            print(f"   • {result.get('agent')} - {os.path.basename(artifact_name) if artifact_name else 'N/A'}")
            print(f"     Error: {result.get('error')}")

    # Save execution summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "test_case_type": args.task,
        "artifacts_processed": len(artifacts),
        "specialized_agents": len(specialized_results),
        "successful": len(successful),
        "failed": len(failed),
        "pending_implementation": len(pending),
        "total_generated": total_generated,
        "total_modified": total_modified,
        "total_obsolete": total_obsolete,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "specialized_results": specialized_results,
        "artifact_results": results
    }

    summary_file = f"master_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary_path = os.path.join("logs", summary_file)
    os.makedirs("logs", exist_ok=True)

    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n💾 Execution summary saved to: {summary_path}")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    return 0 if len(failed) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
