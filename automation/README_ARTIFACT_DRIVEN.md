# Master Test Case Generator - Artifact-Driven

An intelligent, artifact-driven test case generation system that automatically detects different types of artifacts (OpenAPI specs, functional documents, code, security docs, etc.) and generates comprehensive test cases using specialized AI agents.

## 🎯 Overview

This system revolutionizes test case generation by:
- **Automatic artifact detection** - Scans `test_case_artifacts/` directory
- **Dynamic agent spawning** - Launches appropriate agents based on artifact type
- **Prompt-driven execution** - No hardcoded logic, everything driven by prompts
- **Smart test management** - Creates, modifies, or marks tests as obsolete
- **Parallel execution** - Runs multiple agents concurrently
- **Cost tracking** - Reports tokens used and cost per agent

## 📁 Architecture

```
test_case_genrator/
├── automation/
│   ├── master.py                    # Main orchestrator
│   ├── artifact_detector.py         # Detects and classifies artifacts
│   ├── agent_executor.py            # Unified agent execution engine
│   ├── config.json                  # Agent configurations
│   ├── prompts/
│   │   ├── openapi_test_generator.txt
│   │   ├── functional_test_generator.txt
│   │   ├── security_test_generator.txt
│   │   ├── performance_test_generator.txt
│   │   └── code_test_generator.txt
│   └── ...
├── test_case_artifacts/             # Put your artifacts here
│   ├── openapi.json
│   ├── functional_spec.md
│   ├── security_requirements.pdf
│   └── app.py
└── test_cases/                      # Generated test cases
    ├── integration/
    ├── component/
    ├── system/
    ├── regression/
    └── all/
```

## 🚀 Quick Start

### 1. Add Artifacts

Place your artifacts in `test_case_artifacts/` directory:

```bash
cd automation
mkdir -p ../test_case_artifacts
cp /path/to/openapi.json ../test_case_artifacts/
cp /path/to/functional_spec.md ../test_case_artifacts/
```

### 2. Run Master

Generate test cases by test type:

```bash
# Generate integration tests
python master.py -test-case-type integration

# Generate all types
python master.py -test-case-type all

# Generate component tests
python master.py -test-case-type component
```

### 3. View Results

Check the tabular output:

```
+------------+-----------+-----------+----------+----------+--------+----------+
| Agent Type | Test Type | Generated | Modified | Obsolete | Tokens | Cost ($) |
+------------+-----------+-----------+----------+----------+--------+----------+
| OPENAPI    | INTEGRATION| 15       | 3        | 2        | 12000  | 0.1800   |
| FUNCTIONAL | INTEGRATION| 8        | 1        | 0        | 8500   | 0.1275   |
| SECURITY   | INTEGRATION| 12       | 0        | 1        | 9800   | 0.1470   |
+------------+-----------+-----------+----------+----------+--------+----------+
| TOTAL      |           | 35       | 4        | 3        | 30300  | 0.4545   |
+------------+-----------+-----------+----------+----------+--------+----------+
```

## 📦 Supported Artifact Types

### 1. OpenAPI/Swagger Specifications
**Patterns:** `*.json`, `openapi.json`, `swagger.json`, `*openapi*.json`, `*swagger*.json`
**Agent:** `openapi_test_generator`
**Generates:** API endpoint tests, HTTP method tests, request/response validation

### 2. Functional Specifications
**Patterns:** `*functional*.md`, `*functional*.pdf`, `*spec*.md`, `*requirements*.md`
**Agent:** `functional_test_generator`
**Generates:** Business logic tests, user workflow tests, acceptance criteria tests

### 3. Security Documents
**Patterns:** `*security*.md`, `*security*.pdf`, `*threat*.md`, `*owasp*.md`
**Agent:** `security_test_generator`
**Generates:** OWASP Top 10 tests, injection tests, authentication tests

### 4. Performance Specifications
**Patterns:** `*performance*.md`, `*performance*.pdf`, `*load*.md`, `*benchmark*.md`
**Agent:** `performance_test_generator`
**Generates:** Load tests, stress tests, response time tests

### 5. Source Code
**Patterns:** `*.py`, `*.js`, `*.java`, `*.go`, `*.ts`, `*.cpp`, `*.c`
**Agent:** `code_test_generator`
**Generates:** Flow-based functional tests, method integration tests, code path tests

## 🧠 Smart Test Management

The system intelligently manages test cases:

### When Running for First Time
- ✅ Generates all new test cases
- Sets `enabled: true` and `status: "active"` by default

### When Running Again (with existing tests)
- ✅ **Keeps** existing valid test cases unchanged
- ✏️ **Modifies** test cases that need updates
- ➕ **Adds** new test cases for new functionality
- ❌ **Marks obsolete** irrelevant tests with `enabled: false, status: "obsolete"`

## 📝 Test Case Structure

Each generated test case includes:

```json
{
  "name": "Test Name",
  "description": "What this test validates",
  "endpoint": "/api/endpoint",
  "method": "POST",
  "requestBody": { "field": "value" },
  "params": { "param": "value" },
  "expectedStatusCode": 200,
  "enabled": true,
  "status": "active",
  "flowDescription": "method1() → method2() → method3()",
  "methodsCalled": ["method1", "method2", "method3"]
}
```

## ⚙️ Configuration

### config.json Structure

```json
{
  "artifacts": {
    "base_dir": "test_case_artifacts",
    "mappings": {
      "openapi": {
        "patterns": ["*.json", "openapi.json"],
        "agent": "openapi_test_generator"
      }
    }
  },
  "test_types": {
    "integration": {
      "output_dir": "test_cases/integration"
    }
  },
  "agents": {
    "openapi_test_generator": {
      "llm_vendor": "anthropic",
      "llm_model": "claude-sonnet-4-5-20250929",
      "temperature": 0,
      "max_tokens": 16000,
      "prompt_file": "prompts/openapi_test_generator.txt"
    }
  }
}
```

## 🎨 Customization

### Add New Artifact Type

1. **Update config.json:**
```json
{
  "artifacts": {
    "mappings": {
      "database": {
        "patterns": ["*schema*.sql", "*.ddl"],
        "agent": "database_test_generator"
      }
    }
  },
  "agents": {
    "database_test_generator": {
      "llm_vendor": "anthropic",
      "llm_model": "claude-sonnet-4-5-20250929",
      "temperature": 0,
      "max_tokens": 16000,
      "prompt_file": "prompts/database_test_generator.txt"
    }
  }
}
```

2. **Create prompt file:**
```bash
touch automation/prompts/database_test_generator.txt
```

3. **Done!** Master will automatically detect and use your new agent.

### Modify Agent Behavior

Simply edit the prompt file in `automation/prompts/`:
- No code changes needed
- Instant effect on next run
- Fully prompt-driven

## 💰 Cost Tracking

The system tracks token usage and costs:

**Pricing (per 1M tokens):**
- Claude Sonnet 4.5: $3.00 (input) / $15.00 (output)
- Claude Haiku 4.5: $0.80 (input) / $4.00 (output)

Costs are automatically calculated and displayed in the summary table.

## 🔧 Advanced Usage

### Parallel Execution Control

Control the number of parallel agents:

```bash
python master.py -test-case-type integration --max-workers 5
```

### Test Type Reference

- `integration` - Tests component interactions
- `component` - Tests individual components
- `system` - End-to-end system tests
- `regression` - Tests for existing functionality
- `all` - Generate all types

## 📊 Output

### Generated Files

1. **Test Cases:**
   - `test_cases/{test_type}/{artifact}_{agent}_tests.json`

2. **Execution Summary:**
   - `logs/master_execution_{timestamp}.json`

### Execution Summary JSON

```json
{
  "timestamp": "2025-11-10T15:30:00",
  "test_case_type": "integration",
  "total_generated": 35,
  "total_modified": 4,
  "total_obsolete": 3,
  "total_tokens": 30300,
  "total_cost": 0.4545,
  "results": [...]
}
```

## 🐛 Troubleshooting

### No artifacts detected
- Ensure artifacts are in `test_case_artifacts/` directory
- Check file naming matches patterns in config.json
- Run `python artifact_detector.py` to test detection

### Agent execution failed
- Check `logs/master_execution_*.json` for error details
- Verify prompt file exists in `prompts/` directory
- Ensure LLM API keys are set correctly

### Prompt not working as expected
- Edit the prompt file directly in `prompts/`
- No code changes needed
- Test with a small artifact first

## 📚 Examples

### Example 1: OpenAPI Specification

Place `openapi.json` in `test_case_artifacts/`:

```bash
python master.py -test-case-type integration
```

Output:
- Generates tests for all API endpoints
- Covers GET, POST, PUT, DELETE methods
- Includes success and error scenarios

### Example 2: Mixed Artifacts

Place multiple artifacts:
```
test_case_artifacts/
├── openapi.json
├── functional_spec.md
└── app.py
```

```bash
python master.py -test-case-type integration
```

Master automatically:
- Detects 3 different artifact types
- Spawns 3 specialized agents in parallel
- Generates comprehensive test suite
- Reports individual and total costs

## 🎯 Key Features

✅ **Fully Prompt-Driven** - No hardcoded test logic
✅ **Smart Test Management** - Create, modify, obsolete
✅ **Parallel Execution** - Fast test generation
✅ **Cost Tracking** - Know your LLM costs
✅ **Extensible** - Add new artifact types easily
✅ **Type-Safe** - Structured JSON output
✅ **Automatic Detection** - No manual configuration
✅ **Flow Analysis** - Understands code execution paths

## 📝 Notes

- All test cases have `enabled: true` by default
- Obsolete tests are marked `enabled: false, status: "obsolete"`
- Active tests have `status: "active"`
- Existing tests are preserved unless changes detected
- Token usage is estimated (4 chars ≈ 1 token)

## 🤝 Contributing

To add support for new artifact types:
1. Update `config.json` mappings
2. Create prompt template
3. No code changes needed!

---

**Questions?** Check the logs in `logs/` directory for detailed execution information.
