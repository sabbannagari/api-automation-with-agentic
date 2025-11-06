import os
import sys
import json
import requests
from requests.auth import HTTPBasicAuth


class Utils:
    """Utility class for common operations across agents"""

    @staticmethod
    def validate_anthropic_auth():
        """
        DEPRECATED: Use validate_llm_auth() instead

        Validate that ANTHROPIC_API_KEY is set in environment

        Exits the program with error message if not set

        Returns:
            str: The API key if valid
        """
        # Delegate to the new multi-vendor validation for backward compatibility
        return Utils.validate_llm_auth(vendor="anthropic")

    @staticmethod
    def validate_llm_auth(vendor: str = None, config_path: str = "config.json"):
        """
        Validate that required API key(s) are set for LLM vendors used in config

        Args:
            vendor: Specific vendor to validate (optional). If None, validates all vendors in config
            config_path: Path to config.json

        Exits the program with error message if any required key is not set

        Returns:
            dict: Dictionary of vendor -> API key mappings
        """
        # Load LLM vendors configuration
        llm_vendors_path = os.path.join(os.path.dirname(__file__), "llm_vendors.json")
        with open(llm_vendors_path, 'r') as f:
            vendors_config = json.load(f)

        # If specific vendor provided, validate only that one
        if vendor:
            vendors_to_check = {vendor.lower(): vendors_config.get(vendor.lower())}
            if not vendors_to_check[vendor.lower()]:
                print(f"\n❌ Unknown vendor: {vendor}")
                print(f"   Supported vendors: {', '.join(vendors_config.keys())}\n")
                sys.exit(1)
        else:
            # Load config and collect all vendors used by agents
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except FileNotFoundError:
                print(f"\n❌ Configuration file not found: {config_path}\n")
                sys.exit(1)

            vendors_to_check = {}
            for agent_name, agent_config in config.get("agents", {}).items():
                agent_vendor = agent_config.get("llm_vendor")
                if agent_vendor and agent_vendor.lower() in vendors_config:
                    vendors_to_check[agent_vendor.lower()] = vendors_config[agent_vendor.lower()]

        # Validate API keys for each vendor
        validated_keys = {}
        missing_vendors = []

        for vendor_name, vendor_info in vendors_to_check.items():
            primary_key = vendor_info["env_var"]
            api_key = os.getenv(primary_key)

            if not api_key or api_key.strip() == "":
                missing_vendors.append({
                    "vendor": vendor_name,
                    "env_var": primary_key,
                    "console_url": vendor_info["console_url"],
                    "additional_vars": vendor_info.get("additional_env_vars", [])
                })
            else:
                # Check additional env vars if required (e.g., Azure)
                if "additional_env_vars" in vendor_info:
                    missing_additional = []
                    for var in vendor_info["additional_env_vars"]:
                        if not os.getenv(var):
                            missing_additional.append(var)

                    if missing_additional:
                        missing_vendors.append({
                            "vendor": vendor_name,
                            "env_var": None,
                            "missing_additional": missing_additional,
                            "console_url": vendor_info["console_url"]
                        })
                    else:
                        validated_keys[vendor_name] = api_key
                else:
                    validated_keys[vendor_name] = api_key

        # If any vendors have missing keys, show error and exit
        if missing_vendors:
            print("\n" + "="*80)
            print("❌ LLM AUTHENTICATION ERROR")
            print("="*80)
            print("🔑 Missing required API keys for the following LLM vendors:\n")

            for missing in missing_vendors:
                vendor = missing["vendor"].upper()

                if missing.get("env_var"):
                    # Missing primary key
                    print(f"   {vendor}:")
                    print(f"   - Missing: {missing['env_var']}")
                    print(f"   - Get your key from: {missing['console_url']}")

                    if missing.get("additional_vars"):
                        print(f"   - Also required: {', '.join(missing['additional_vars'])}")
                    print()
                elif missing.get("missing_additional"):
                    # Has primary key but missing additional vars
                    print(f"   {vendor}:")
                    print(f"   - Missing additional variables: {', '.join(missing['missing_additional'])}")
                    print(f"   - See documentation: {missing['console_url']}")
                    print()

            print("📝 Set the required environment variables using one of these methods:\n")
            print("   Option 1 - Export in current session:")
            for missing in missing_vendors:
                if missing.get("env_var"):
                    print(f"   export {missing['env_var']}='your-api-key-here'")
                if missing.get("missing_additional"):
                    for var in missing["missing_additional"]:
                        print(f"   export {var}='your-value-here'")

            print("\n   Option 2 - Add to .env file in project root:")
            for missing in missing_vendors:
                if missing.get("env_var"):
                    print(f"   {missing['env_var']}=your-api-key-here")
                if missing.get("missing_additional"):
                    for var in missing["missing_additional"]:
                        print(f"   {var}=your-value-here")

            print("\n" + "="*80 + "\n")
            sys.exit(1)

        return validated_keys if not vendor else validated_keys.get(vendor.lower())

    @staticmethod
    def read_config(config_path="config.json"):
        """
        Read and parse the global configuration file

        Args:
            config_path: Path to the config JSON file (default: config.json)

        Returns:
            dict: Parsed configuration dictionary
        """
        with open(config_path, "r") as f:
            return json.load(f)

    @staticmethod
    def read_prompt(script_name, prompts_dir="prompts"):
        """
        Read the prompt file for a given agent/script

        Args:
            script_name: Name of the script/agent (e.g., 'master', 'planner')
            prompts_dir: Directory containing prompt files (default: prompts)

        Returns:
            str: Content of the prompt file
        """
        prompt_path = os.path.join(prompts_dir, f"{script_name}.prompt")
        with open(prompt_path, "r") as f:
            return f.read()

    @staticmethod
    def get_script_name(file_path):
        """
        Extract script name from file path

        Args:
            file_path: The __file__ variable from the calling script

        Returns:
            str: Script name without extension
        """
        return os.path.splitext(os.path.basename(file_path))[0]

    @staticmethod
    def get_agent_config(global_config, agent_name):
        """
        Extract specific agent configuration from global config

        Args:
            global_config: The global configuration dictionary
            agent_name: Name of the agent (e.g., 'planner', 'executor')

        Returns:
            dict: Agent-specific configuration

        Raises:
            ValueError: If agent configuration is not found
        """
        agent_config = global_config.get("agents", {}).get(agent_name)
        if not agent_config:
            raise ValueError(f"No configuration found for agent '{agent_name}' in global config")
        return agent_config

    @staticmethod
    def get_auth_headers(auth_type=None):
        """
        Get authentication headers/auth object based on auth type

        Args:
            auth_type: Type of authentication ('basic', 'bearer', 'token', or None)

        Returns:
            tuple: (headers dict, auth object) for requests
        """
        headers = {}
        auth = None

        if auth_type is None:
            # No authentication
            return headers, auth

        auth_type_lower = auth_type.lower()

        if auth_type_lower == "basic":
            # HTTP Basic Auth - get credentials from environment
            username = os.getenv("API_USERNAME")
            password = os.getenv("API_PASSWORD")
            if username and password:
                auth = HTTPBasicAuth(username, password)
            else:
                raise ValueError("API_USERNAME and API_PASSWORD environment variables required for basic auth")

        elif auth_type_lower in ["bearer", "token"]:
            # Bearer token authentication
            token = os.getenv("API_TOKEN")
            if token:
                headers["Authorization"] = f"Bearer {token}"
            else:
                raise ValueError("API_TOKEN environment variable required for bearer/token auth")

        return headers, auth

    @staticmethod
    def execute_get(base_url, endpoint, params=None, auth_type=None):
        """
        Execute GET request with smart authentication

        Args:
            base_url: Base URL of the API
            endpoint: API endpoint path
            params: Query parameters (optional)
            auth_type: Authentication type ('basic', 'bearer', 'token', or None)

        Returns:
            Response object
        """
        url = f"{base_url}{endpoint}"
        headers, auth = Utils.get_auth_headers(auth_type)
        return requests.get(url, params=params, headers=headers, auth=auth)

    @staticmethod
    def execute_post(base_url, endpoint, request_body=None, auth_type=None):
        """
        Execute POST request (Create) with smart authentication

        Args:
            base_url: Base URL of the API
            endpoint: API endpoint path
            request_body: JSON body for the request
            auth_type: Authentication type ('basic', 'bearer', 'token', or None)

        Returns:
            Response object
        """
        url = f"{base_url}{endpoint}"
        headers, auth = Utils.get_auth_headers(auth_type)
        return requests.post(url, json=request_body, headers=headers, auth=auth)

    @staticmethod
    def execute_put(base_url, endpoint, request_body=None, auth_type=None):
        """
        Execute PUT request (Update/Replace) with smart authentication

        Args:
            base_url: Base URL of the API
            endpoint: API endpoint path
            request_body: JSON body for the request
            auth_type: Authentication type ('basic', 'bearer', 'token', or None)

        Returns:
            Response object
        """
        url = f"{base_url}{endpoint}"
        headers, auth = Utils.get_auth_headers(auth_type)
        return requests.put(url, json=request_body, headers=headers, auth=auth)

    @staticmethod
    def execute_patch(base_url, endpoint, request_body=None, auth_type=None):
        """
        Execute PATCH request (Partial Update) with smart authentication

        Args:
            base_url: Base URL of the API
            endpoint: API endpoint path
            request_body: JSON body for the request
            auth_type: Authentication type ('basic', 'bearer', 'token', or None)

        Returns:
            Response object
        """
        url = f"{base_url}{endpoint}"
        headers, auth = Utils.get_auth_headers(auth_type)
        return requests.patch(url, json=request_body, headers=headers, auth=auth)

    @staticmethod
    def execute_delete(base_url, endpoint, auth_type=None):
        """
        Execute DELETE request with smart authentication

        Args:
            base_url: Base URL of the API
            endpoint: API endpoint path
            auth_type: Authentication type ('basic', 'bearer', 'token', or None)

        Returns:
            Response object
        """
        url = f"{base_url}{endpoint}"
        headers, auth = Utils.get_auth_headers(auth_type)
        return requests.delete(url, headers=headers, auth=auth)

    @staticmethod
    def execute_request(base_url, method, endpoint, request_body=None, params=None, auth_type=None):
        """
        Smart method to execute the appropriate HTTP request based on method type

        Args:
            base_url: Base URL of the API
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint path
            request_body: Request body for POST/PUT/PATCH
            params: Query parameters for GET
            auth_type: Authentication type ('basic', 'bearer', 'token', or None)

        Returns:
            Response object

        Raises:
            ValueError: If method is not supported
        """
        method = method.upper()

        if method == "GET":
            return Utils.execute_get(base_url, endpoint, params, auth_type)
        elif method == "POST":
            return Utils.execute_post(base_url, endpoint, request_body, auth_type)
        elif method == "PUT":
            return Utils.execute_put(base_url, endpoint, request_body, auth_type)
        elif method == "PATCH":
            return Utils.execute_patch(base_url, endpoint, request_body, auth_type)
        elif method == "DELETE":
            return Utils.execute_delete(base_url, endpoint, auth_type)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    @staticmethod
    def save_json_report(test_results, test_type, testcases_dir="testcases"):
        """
        Save test results as JSON in the appropriate test type's reports directory

        Args:
            test_results: Dictionary containing test results
            test_type: Type of test (integration, system, component, regression, sanity)
            testcases_dir: Base testcases directory

        Returns:
            str: Path to the saved JSON report
        """
        from datetime import datetime

        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(testcases_dir, test_type, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        filepath = os.path.join(reports_dir, filename)

        # Save JSON report
        with open(filepath, 'w') as f:
            json.dump(test_results, f, indent=2)

        return filepath

    @staticmethod
    def save_html_report(test_results, test_type, testcases_dir="testcases"):
        """
        Save test results as interactive HTML dashboard in the appropriate test type's reports directory

        Args:
            test_results: Dictionary containing test results
            test_type: Type of test (integration, system, component, regression, sanity)
            testcases_dir: Base testcases directory

        Returns:
            str: Path to the saved HTML report
        """
        from datetime import datetime

        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(testcases_dir, test_type, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        # Extract data
        summary = test_results.get('summary', {})
        results = test_results.get('results', [])
        timestamp = test_results.get('timestamp', '')

        # Group results by endpoint
        endpoints = {}
        for result in results:
            endpoint_key = f"{result['method']} {result['endpoint']}"
            if endpoint_key not in endpoints:
                endpoints[endpoint_key] = {
                    'method': result['method'],
                    'endpoint': result['endpoint'],
                    'tests': [],
                    'passed': 0,
                    'failed': 0
                }
            endpoints[endpoint_key]['tests'].append(result)
            if result['passed']:
                endpoints[endpoint_key]['passed'] += 1
            else:
                endpoints[endpoint_key]['failed'] += 1

        # Load historical data
        history_data = Utils.load_test_history(test_type, testcases_dir)

        # Generate HTML content
        html_content = Utils._generate_html_dashboard(
            summary, results, endpoints, timestamp, test_type, history_data
        )

        # Generate filename with timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp_str}.html"
        filepath = os.path.join(reports_dir, filename)

        # Save HTML report
        with open(filepath, 'w') as f:
            f.write(html_content)

        return filepath

    @staticmethod
    def load_test_history(test_type, testcases_dir="testcases", limit=10):
        """
        Load historical test results for trend analysis

        Args:
            test_type: Type of test (integration, system, component, regression, sanity)
            testcases_dir: Base testcases directory
            limit: Maximum number of historical reports to load

        Returns:
            list: List of historical test results
        """
        reports_dir = os.path.join(testcases_dir, test_type, "reports")

        if not os.path.exists(reports_dir):
            return []

        # Get all JSON report files
        json_files = sorted(
            [f for f in os.listdir(reports_dir) if f.startswith('test_results_') and f.endswith('.json')],
            reverse=True
        )[:limit]

        history = []
        for json_file in json_files:
            try:
                with open(os.path.join(reports_dir, json_file), 'r') as f:
                    data = json.load(f)
                    history.append({
                        'timestamp': data.get('timestamp', ''),
                        'summary': data.get('summary', {}),
                        'filename': json_file
                    })
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")
                continue

        return history

    @staticmethod
    def _generate_html_dashboard(summary, results, endpoints, timestamp, test_type, history_data):
        """
        Generate HTML dashboard content

        Args:
            summary: Test summary statistics
            results: List of test results
            endpoints: Grouped endpoint data
            timestamp: Timestamp of test run
            test_type: Type of test
            history_data: Historical test data

        Returns:
            str: HTML content
        """
        from datetime import datetime as dt

        # Load HTML template
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'test_report.html')
        with open(template_path, 'r') as f:
            template = f.read()

        # Prepare historical data for charts
        history_labels = []
        history_passed = []
        history_failed = []

        for hist in reversed(history_data):
            if hist.get('timestamp'):
                try:
                    dt_obj = dt.fromisoformat(hist['timestamp'])
                    history_labels.append(dt_obj.strftime('%m/%d %H:%M'))
                except:
                    history_labels.append(hist['filename'][:15])
            hist_summary = hist.get('summary', {})
            history_passed.append(hist_summary.get('passed', 0))
            history_failed.append(hist_summary.get('failed', 0))

        # Format timestamp
        if timestamp:
            try:
                formatted_timestamp = dt.fromisoformat(timestamp).strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_timestamp = 'N/A'
        else:
            formatted_timestamp = 'N/A'

        # Replace template variables
        html_content = template.replace('{{test_type}}', test_type.upper())
        html_content = html_content.replace('{{formatted_timestamp}}', formatted_timestamp)
        html_content = html_content.replace('{{total_tests}}', str(summary.get('total', 0)))
        html_content = html_content.replace('{{passed_tests}}', str(summary.get('passed', 0)))
        html_content = html_content.replace('{{failed_tests}}', str(summary.get('failed', 0)))
        html_content = html_content.replace('{{pass_rate}}', summary.get('pass_rate', '0%'))

        # Escape JSON for safe embedding in HTML <script> tags
        # json.dumps already properly escapes strings for JSON, but we need to escape script tags
        def escape_for_js(obj):
            json_str = json.dumps(obj)
            # Escape script tags to prevent them from breaking out of the script block
            # The browser HTML parser will see </script> even inside JSON strings
            json_str = json_str.replace('</script>', '<\\/script>')
            json_str = json_str.replace('<script>', '<\\script>')
            return json_str

        html_content = html_content.replace('{{test_data}}', escape_for_js(results))
        html_content = html_content.replace('{{endpoint_data}}', escape_for_js(list(endpoints.values())))
        html_content = html_content.replace('{{history_labels}}', escape_for_js(history_labels))
        html_content = html_content.replace('{{history_passed}}', escape_for_js(history_passed))
        html_content = html_content.replace('{{history_failed}}', escape_for_js(history_failed))

        return html_content
