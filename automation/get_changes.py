#!/usr/bin/env python3
"""
Get Changed Files - LLM-Optimized Change Detection

Creates structured, LLM-friendly format for intelligent agent analysis and learning.

Usage:
    python get_changes.py
"""

import subprocess
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class LLMOptimizedChangeFormatter:
    """
    Formats changes in a way that's easy for LLMs to understand and learn from
    """

    @staticmethod
    def format_for_llm(changes: List[Dict]) -> Dict:
        """
        Format changes in LLM-friendly structure

        Returns structured data optimized for:
        1. Easy parsing by LLM
        2. Clear context
        3. Learning from patterns
        4. Action determination
        """
        formatted = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_changes": len(changes),
                "commit_info": LLMOptimizedChangeFormatter._get_commit_info()
            },
            "changes_summary": LLMOptimizedChangeFormatter._create_summary(changes),
            "detailed_changes": LLMOptimizedChangeFormatter._create_detailed_changes(changes),
            "llm_context": LLMOptimizedChangeFormatter._create_llm_context(changes)
        }

        return formatted

    @staticmethod
    def _get_commit_info() -> Dict:
        """Get commit information"""
        try:
            # Get commit message
            message = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                capture_output=True, text=True
            ).stdout.strip()

            # Get commit author
            author = subprocess.run(
                ['git', 'log', '-1', '--pretty=%an'],
                capture_output=True, text=True
            ).stdout.strip()

            # Get commit hash
            commit_hash = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True
            ).stdout.strip()

            return {
                "hash": commit_hash[:8],
                "message": message,
                "author": author
            }
        except:
            return {}

    @staticmethod
    def _create_summary(changes: List[Dict]) -> str:
        """Create human-readable summary for LLM context"""
        if not changes:
            return "No changes detected."

        summary_parts = [f"Total of {len(changes)} file(s) changed:"]

        # Group by type
        by_type = {}
        for change in changes:
            change_type = change.get('change_type', 'modified')
            by_type[change_type] = by_type.get(change_type, 0) + 1

        for change_type, count in by_type.items():
            summary_parts.append(f"- {count} file(s) {change_type}")

        # Categorize by artifact type
        categories = {"openapi": 0, "functional": 0, "code": 0, "other": 0}
        for change in changes:
            category = LLMOptimizedChangeFormatter._classify_file(change['file'])
            categories[category] += 1

        summary_parts.append("\nBy artifact type:")
        for category, count in categories.items():
            if count > 0:
                summary_parts.append(f"- {count} {category} file(s)")

        return "\n".join(summary_parts)

    @staticmethod
    def _create_detailed_changes(changes: List[Dict]) -> List[Dict]:
        """Create detailed, structured changes for LLM"""
        detailed = []

        for change in changes:
            filename = change['file']
            category = LLMOptimizedChangeFormatter._classify_file(filename)

            # Create structured change object
            detailed_change = {
                "file_info": {
                    "path": filename,
                    "name": os.path.basename(filename),
                    "extension": os.path.splitext(filename)[1],
                    "artifact_type": category
                },
                "change_info": {
                    "type": change.get('change_type', 'modified'),
                    "lines_added": change.get('lines_added', 0),
                    "lines_removed": change.get('lines_removed', 0),
                    "impact_score": LLMOptimizedChangeFormatter._calculate_impact_score(change)
                },
                "content": {
                    "current_content": change.get('content', ''),
                    "diff": change.get('diff', ''),
                    "key_changes": LLMOptimizedChangeFormatter._extract_key_changes(change)
                },
                "agent_hints": LLMOptimizedChangeFormatter._generate_agent_hints(change, category)
            }

            detailed.append(detailed_change)

        return detailed

    @staticmethod
    def _create_llm_context(changes: List[Dict]) -> Dict:
        """Create rich context for LLM analysis"""
        return {
            "analysis_questions": [
                "What features or functionality are affected by these changes?",
                "What endpoints, functions, or components were modified?",
                "What types of tests need to be generated, updated, or deleted?",
                "Are there security implications in these changes?",
                "Are there performance implications in these changes?",
                "Which specialized agents should be spawned to handle these changes?"
            ],
            "expected_actions": [
                "generate_new_tests",
                "update_existing_tests",
                "delete_obsolete_tests",
                "spawn_security_agent",
                "spawn_performance_agent",
                "spawn_functional_agent"
            ],
            "learning_hints": {
                "patterns_to_learn": [
                    "Which artifact types require which specialized agents",
                    "Which changes typically require security testing",
                    "Which changes require performance testing",
                    "Common patterns in API endpoint changes",
                    "Common patterns in functional spec changes"
                ],
                "success_metrics": [
                    "Test coverage percentage",
                    "Test pass rate",
                    "Time to generate tests",
                    "Cost efficiency"
                ]
            }
        }

    @staticmethod
    def _classify_file(filename: str) -> str:
        """Classify file into artifact type"""
        filename_lower = filename.lower()

        # OpenAPI/Swagger
        if any(pattern in filename_lower for pattern in ['openapi', 'swagger']) and \
           any(filename_lower.endswith(ext) for ext in ['.json', '.yaml', '.yml']):
            return "openapi"

        # Functional specs
        if any(pattern in filename_lower for pattern in ['functional', 'spec', 'requirement', 'feature']) and \
           any(filename_lower.endswith(ext) for ext in ['.md', '.txt', '.pdf', '.doc']):
            return "functional"

        # Code files
        if any(filename_lower.endswith(ext) for ext in ['.py', '.js', '.java', '.go', '.ts', '.cpp', '.c', '.rs']):
            return "code"

        return "other"

    @staticmethod
    def _calculate_impact_score(change: Dict) -> str:
        """Calculate impact score: critical, high, medium, low"""
        lines_added = change.get('lines_added', 0)
        lines_removed = change.get('lines_removed', 0)
        total_changes = lines_added + lines_removed

        if total_changes > 100:
            return "critical"
        elif total_changes > 50:
            return "high"
        elif total_changes > 10:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _extract_key_changes(change: Dict) -> List[str]:
        """Extract key changes from diff (readable summary)"""
        diff = change.get('diff', '')
        if not diff:
            return []

        key_changes = []

        # Extract added lines (+ prefix)
        added_lines = [line[1:].strip() for line in diff.split('\n')
                      if line.startswith('+') and not line.startswith('+++') and line.strip() != '+']

        # Extract removed lines (- prefix)
        removed_lines = [line[1:].strip() for line in diff.split('\n')
                        if line.startswith('-') and not line.startswith('---') and line.strip() != '-']

        # Summarize
        if added_lines:
            key_changes.append(f"Added {len(added_lines)} line(s)")
        if removed_lines:
            key_changes.append(f"Removed {len(removed_lines)} line(s)")

        # Look for specific patterns
        diff_lower = diff.lower()
        if 'def ' in diff or 'function' in diff_lower or 'class ' in diff:
            key_changes.append("Code structure changed (functions/classes)")
        if 'path' in diff_lower and any(x in diff_lower for x in ['get', 'post', 'put', 'delete']):
            key_changes.append("API endpoints modified")
        if 'security' in diff_lower or 'auth' in diff_lower:
            key_changes.append("Security-related changes detected")

        return key_changes[:5]  # Limit to top 5

    @staticmethod
    def _generate_agent_hints(change: Dict, category: str) -> Dict:
        """Generate hints for which agents should handle this change"""
        hints = {
            "recommended_agents": [],
            "reasoning": []
        }

        # Based on artifact type
        if category == "openapi":
            hints["recommended_agents"].extend([
                "openapi_functional_agent",
                "openapi_security_agent",
                "openapi_contract_agent"
            ])
            hints["reasoning"].append("OpenAPI changes typically require functional, security, and contract tests")

        elif category == "functional":
            hints["recommended_agents"].extend([
                "functional_feature_agent",
                "functional_integration_agent"
            ])
            hints["reasoning"].append("Functional spec changes require feature and integration tests")

        elif category == "code":
            hints["recommended_agents"].extend([
                "code_unit_agent",
                "code_integration_agent"
            ])
            hints["reasoning"].append("Code changes require unit and integration tests")

        # Check for security indicators
        content = (change.get('content') or '') + (change.get('diff') or '')
        if any(keyword in content.lower() for keyword in ['auth', 'password', 'token', 'security', 'permission']):
            if "openapi_security_agent" not in hints["recommended_agents"]:
                hints["recommended_agents"].append("openapi_security_agent")
            hints["reasoning"].append("Security-related keywords detected")

        # Check for performance indicators
        if any(keyword in content.lower() for keyword in ['performance', 'cache', 'optimize', 'slow', 'fast']):
            hints["recommended_agents"].append("performance_agent")
            hints["reasoning"].append("Performance-related keywords detected")

        return hints


def get_changed_files() -> List[Dict]:
    """Get changed files and their diffs from git"""
    print("\n" + "="*80)
    print("🔍 DETECTING CHANGES FROM GIT")
    print("="*80)

    # Get changed files
    result = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
        capture_output=True,
        text=True,
        check=True
    )

    changed_files = [f for f in result.stdout.strip().split('\n') if f]

    print(f"Files changed: {len(changed_files)}")

    if not changed_files:
        return []

    # Get diffs for each file
    changes = []
    for file in changed_files:
        print(f"  📄 {file}")

        # Get diff
        diff_result = subprocess.run(
            ['git', 'diff', 'HEAD~1', 'HEAD', file],
            capture_output=True,
            text=True
        )
        diff = diff_result.stdout

        # Get status
        status_result = subprocess.run(
            ['git', 'diff', '--name-status', 'HEAD~1', 'HEAD', file],
            capture_output=True,
            text=True
        )
        status_line = status_result.stdout.strip()
        status = status_line.split()[0] if status_line else 'M'

        status_map = {'A': 'added', 'M': 'modified', 'D': 'deleted', 'R': 'renamed'}
        change_type = status_map.get(status, 'modified')

        # Read file content
        file_content = None
        if os.path.exists(file) and change_type != 'deleted':
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()
            except:
                pass

        # Count lines
        added_lines = len([line for line in diff.split('\n') if line.startswith('+') and not line.startswith('+++')])
        removed_lines = len([line for line in diff.split('\n') if line.startswith('-') and not line.startswith('---')])

        changes.append({
            "file": file,
            "change_type": change_type,
            "diff": diff,
            "content": file_content,
            "lines_added": added_lines,
            "lines_removed": removed_lines
        })

    return changes


def categorize_changes(changes: List[Dict]) -> Dict:
    """Categorize changes by artifact type"""
    categorized = {
        "code": [],
        "openapi": [],
        "functional": [],
        "security": [],
        "performance": [],
        "other": []
    }

    for change in changes:
        file_path = change.get("file", "")

        # Determine artifact type
        if file_path.endswith(('.py', '.js', '.java', '.go', '.ts', '.cpp', '.c')):
            categorized["code"].append(change)
        elif 'openapi' in file_path.lower() or 'swagger' in file_path.lower():
            categorized["openapi"].append(change)
        elif 'functional' in file_path.lower() or 'spec' in file_path.lower() or 'requirements' in file_path.lower():
            categorized["functional"].append(change)
        elif 'security' in file_path.lower() or 'threat' in file_path.lower():
            categorized["security"].append(change)
        elif 'performance' in file_path.lower() or 'load' in file_path.lower():
            categorized["performance"].append(change)
        else:
            categorized["other"].append(change)

    return categorized


def print_summary(changes: List[Dict], categorized: Dict):
    """Print summary of changes"""
    print("\n" + "="*80)
    print("📊 CHANGES SUMMARY")
    print("="*80)

    total_added = sum(c.get("lines_added", 0) for c in changes)
    total_removed = sum(c.get("lines_removed", 0) for c in changes)

    print(f"Total files changed: {len(changes)}")
    print(f"Lines added: {total_added}")
    print(f"Lines removed: {total_removed}")
    print()

    for artifact_type, files in categorized.items():
        if files:
            print(f"  {artifact_type.upper()}: {len(files)} file(s)")

    print("="*80)


def export_changes(changes: List[Dict]) -> str:
    """Export changes to JSON file for LLM processing"""
    formatter = LLMOptimizedChangeFormatter()
    llm_formatted = formatter.format_for_llm(changes)

    # Export
    os.makedirs("logs", exist_ok=True)
    output_path = "logs/llm_ready_changes.json"

    with open(output_path, 'w') as f:
        json.dump(llm_formatted, f, indent=2)

    print(f"\n💾 Changes exported to: {output_path}")
    return output_path


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("🚀 LLM-OPTIMIZED CHANGE DETECTOR")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # Get changes
        changes = get_changed_files()

        if not changes:
            print("\n✅ No changes detected")
            return 0

        # Categorize changes
        categorized = categorize_changes(changes)

        # Print summary
        print_summary(changes, categorized)

        # Export
        export_path = export_changes(changes)

        print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Git command failed: {e}")
        print("Make sure you're in a git repository with at least 2 commits")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
