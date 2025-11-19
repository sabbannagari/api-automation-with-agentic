import os
import json
from typing import Dict, Any, List, Tuple
from llm_client import LLMClient
from utils import Utils


class AgentExecutor:
    """
    Unified agent executor that uses prompts from config.json to generate test cases.
    All agents use the same execution logic but different prompts.
    Handles smart test case management: create, modify, obsolete.
    """

    # Pricing per 1M tokens (input, output)
    PRICING = {
        "claude-sonnet-4-5-20250929": (3.00, 15.00),
        "claude-haiku-4-5-20251001": (0.80, 4.00),
        "claude-3-5-sonnet-20241022": (3.00, 15.00),
        "gpt-4": (30.00, 60.00),
        "gpt-3.5-turbo": (0.50, 1.50),
    }

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the agent executor

        Args:
            config_path: Path to the configuration file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)

    def execute_agent(
        self,
        agent_name: str,
        artifact_path: str,
        test_type: str,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Execute an agent to generate test cases with smart management

        Args:
            agent_name: Name of the agent (e.g., 'openapi_test_generator')
            artifact_path: Path to the artifact file
            test_type: Type of test to generate (integration, component, etc.)
            output_dir: Directory to save generated test cases

        Returns:
            Dictionary with execution results including tokens and cost
        """
        # Get agent configuration
        agents = self.config.get("agents", {})
        agent_config = agents.get(agent_name, {})

        if not agent_config:
            raise ValueError(f"Agent '{agent_name}' not found in configuration")

        # Read the prompt template
        prompt_file = agent_config.get("prompt_file")
        if not prompt_file:
            raise ValueError(f"No prompt_file specified for agent '{agent_name}'")

        prompt_template = self._read_prompt(prompt_file)

        # Read the artifact content
        artifact_content = self._read_artifact(artifact_path)

        # Check for existing test cases
        existing_tests_path = self._get_output_path(output_dir, artifact_path, agent_name)
        existing_tests = self._load_existing_tests(existing_tests_path)

        # Build the user prompt
        user_prompt = self._build_user_prompt(
            prompt_template=prompt_template,
            artifact_content=artifact_content,
            artifact_path=artifact_path,
            test_type=test_type,
            existing_tests=existing_tests
        )

        # Get LLM configuration
        llm_vendor = agent_config.get("llm_vendor", "anthropic")
        llm_model = agent_config.get("llm_model", "claude-sonnet-4-5-20250929")
        temperature = agent_config.get("temperature", 0)
        max_tokens = agent_config.get("max_tokens", 16000)

        print(f"   LLM: {llm_vendor}/{llm_model}")
        print(f"   Temperature: {temperature}")
        print(f"   Artifact size: {len(artifact_content)} characters")

        # Calculate input tokens (rough estimate)
        input_tokens = len(user_prompt) // 4  # Rough estimate: 4 chars per token

        # Initialize LLM client
        llm_client = LLMClient(
            vendor=llm_vendor,
            model=llm_model,
            temperature=temperature
        )

        # Generate test cases
        print(f"   🤖 Generating test cases...")
        response = llm_client.generate(
            system_prompt="",
            user_message=user_prompt,
            max_tokens=max_tokens
        )

        # Calculate output tokens
        output_tokens = len(response) // 4

        # Calculate cost
        cost = self._calculate_cost(llm_model, input_tokens, output_tokens)

        # Parse test cases
        new_tests = self._parse_test_cases(response)

        # Merge with existing tests (smart management)
        merged_tests, stats = self._merge_tests(existing_tests, new_tests)

        # Ensure all test cases have required fields
        merged_tests = self._add_required_fields(merged_tests)

        # Save test cases
        output_file = self._save_test_cases(
            test_cases=merged_tests,
            output_path=existing_tests_path
        )

        print(f"   ✅ Test cases saved: {output_file}")
        print(f"   📊 Generated: {stats['generated']}, Modified: {stats['modified']}, Obsolete: {stats['obsolete']}")
        print(f"   💰 Tokens: {input_tokens + output_tokens}, Cost: ${cost:.4f}")

        return {
            "status": "success",
            "agent": agent_name,
            "artifact": artifact_path,
            "test_type": test_type,
            "output_file": output_file,
            "generated": stats['generated'],
            "modified": stats['modified'],
            "obsolete": stats['obsolete'],
            "total_tests": len(merged_tests.get("testCases", [])),
            "tokens_used": input_tokens + output_tokens,
            "cost": cost
        }

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        if model in self.PRICING:
            input_price, output_price = self.PRICING[model]
            cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
            return cost
        return 0.0

    def _read_prompt(self, prompt_file: str) -> str:
        """Read prompt template from file"""
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, 'r') as f:
            return f.read()

    def _read_artifact(self, artifact_path: str) -> str:
        """Read artifact content"""
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Artifact not found: {artifact_path}")

        with open(artifact_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _load_existing_tests(self, output_path: str) -> Dict:
        """Load existing test cases if they exist"""
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _get_output_path(self, output_dir: str, artifact_path: str, agent_name: str) -> str:
        """Generate output file path"""
        artifact_name = os.path.splitext(os.path.basename(artifact_path))[0]
        output_filename = f"{artifact_name}_{agent_name}_tests.json"
        return os.path.join(output_dir, output_filename)

    def _build_user_prompt(
        self,
        prompt_template: str,
        artifact_content: str,
        artifact_path: str,
        test_type: str,
        existing_tests: Dict
    ) -> str:
        """Build the user prompt"""
        user_prompt = prompt_template.replace("{artifact_content}", artifact_content)
        user_prompt = user_prompt.replace("{artifact_path}", artifact_path)
        user_prompt = user_prompt.replace("{test_type}", test_type)
        user_prompt = user_prompt.replace("{artifact_filename}", os.path.basename(artifact_path))

        # Add existing tests context
        if existing_tests and existing_tests.get("testCases"):
            existing_json = json.dumps(existing_tests, indent=2)
            user_prompt += f"\n\nEXISTING TEST CASES:\n{existing_json}\n\n"
            user_prompt += """
IMPORTANT INSTRUCTIONS FOR EXISTING TESTS:
1. If a test case already exists and is still valid - keep it as is (don't regenerate)
2. If a test case needs modifications - update only the necessary fields
3. If a new test case is needed - add it with enabled: true, status: "active"
4. If a test case is no longer relevant - mark it with enabled: false, status: "obsolete"
5. Always include ALL test cases (existing + new + obsolete) in your response
"""

        return user_prompt

    def _parse_test_cases(self, response: str) -> Dict:
        """Parse test cases from LLM response"""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                else:
                    raise ValueError("No JSON found in response")

            return json.loads(json_str)

        except Exception as e:
            print(f"   ⚠️  Error parsing test cases: {e}")
            raise ValueError(f"Failed to parse test cases: {e}")

    def _merge_tests(self, existing: Dict, new: Dict) -> Tuple[Dict, Dict]:
        """
        Smart merge of existing and new test cases

        Returns:
            Tuple of (merged_tests, statistics)
        """
        stats = {
            "generated": 0,
            "modified": 0,
            "obsolete": 0
        }

        # If no existing tests, all are new
        if not existing or not existing.get("testCases"):
            stats["generated"] = len(new.get("testCases", []))
            return new, stats

        # If LLM returned complete merged list, use it
        if new and new.get("testCases"):
            new_tests = new.get("testCases", [])
            existing_tests = existing.get("testCases", [])

            # Count statistics
            for test in new_tests:
                if test.get("status") == "obsolete":
                    stats["obsolete"] += 1
                elif any(self._tests_match(test, et) for et in existing_tests):
                    # Check if modified
                    matching_old = next((et for et in existing_tests if self._tests_match(test, et)), None)
                    if matching_old and not self._tests_identical(test, matching_old):
                        stats["modified"] += 1
                else:
                    stats["generated"] += 1

            new["testCases"] = new_tests
            return new, stats

        return existing, stats

    def _tests_match(self, test1: Dict, test2: Dict) -> bool:
        """Check if two tests match (same test case)"""
        return (test1.get("name") == test2.get("name") and
                test1.get("description") == test2.get("description"))

    def _tests_identical(self, test1: Dict, test2: Dict) -> bool:
        """Check if two tests are identical"""
        return json.dumps(test1, sort_keys=True) == json.dumps(test2, sort_keys=True)

    def _add_required_fields(self, test_cases: Dict) -> Dict:
        """Add required fields to all test cases"""
        if isinstance(test_cases, dict) and "testCases" in test_cases:
            for test_case in test_cases["testCases"]:
                if "enabled" not in test_case:
                    test_case["enabled"] = True
                if "status" not in test_case:
                    test_case["status"] = "active"
                # If marked obsolete, disable it
                if test_case.get("status") == "obsolete":
                    test_case["enabled"] = False

        return test_cases

    def _save_test_cases(self, test_cases: Dict, output_path: str) -> str:
        """Save test cases to file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(test_cases, f, indent=2)

        return output_path
