import json  
import re  
import sys  
import os  
import glob  
import importlib.util

# ANSI color codes for output formatting
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def load_test_case(path):
    """Load a test case from JSON or YAML file."""
    with open(path, "r") as f:
        if path.endswith((".yaml", ".yml")):
            try:
                import yaml
            except ImportError:
                raise RuntimeError("YAML support requires PyYAML to be installed")
            return yaml.safe_load(f)
        else:
            return json.load(f)

def get_nested(memory, path):
    """Utility to get nested value from memory dict using dot-path (e.g. "last_booking.destination")."""
    parts = path.split(".")
    for p in parts:
        if isinstance(memory, dict) and p in memory:
            memory = memory[p]
        else:
            return None
    return memory

def assert_case(test, agent_func):
    """Run a single test case (already loaded as dict) against the agent function."""
    input_text = test["input"]
    memory = test.get("memory", {})
    result = agent_func(input_text, memory)

    actual_output = result.get("output", "")
    actual_memory = result.get("memory", {})
    actual_tools = result.get("tools_used", [])

    # Print test description
    description = test.get("description", "<Unnamed test>")
    print(f"{BOLD}Test: {description}{RESET}")

    passed_checks = 0
    total_checks = 0
    passed = True

    # Normalize actual_tools to a list of tool names (in case agent provided objects)
    if isinstance(actual_tools, list):
        actual_tool_names = []
        for t in actual_tools:
            if isinstance(t, str):
                actual_tool_names.append(t)
            elif isinstance(t, dict) and "name" in t:
                actual_tool_names.append(t["name"])
            else:
                actual_tool_names.append(str(t))
        actual_tools_list = actual_tool_names
    else:
        # If a single tool or other type is returned, make it a list
        actual_tools_list = [actual_tools]

    # Check each assertion
        for key, expected in test["assert"].items():
        total_checks += 1
        if key.startswith("output.equals"):
            status = "PASS" if actual_output == expected else "FAIL"
            if status == "FAIL":
                print(f'  {RED}{status:<5}{RESET} output.equals: expected exactly "{expected}", got "{actual_output}"')
                passed = False
            else:
                print(f'  {GREEN}{status:<5}{RESET} output.equals: "{expected}"')
                passed_checks += 1

        elif key.startswith("output.includes"):
            status = "PASS" if expected in actual_output else "FAIL"
            if status == "FAIL":
                print(f'  {RED}{status:<5}{RESET} output.includes: "{expected}" (output was: "{actual_output}")')
                passed = False
            else:
                print(f'  {GREEN}{status:<5}{RESET} output.includes: "{expected}"')
                passed_checks += 1

        elif key.startswith("output.matches"):
            pattern = expected
            matched = bool(re.search(pattern, actual_output))
            status = "PASS" if matched else "FAIL"
            if status == "FAIL":
                print(f'  {RED}{status:<5}{RESET} output.matches: /{pattern}/ (output was: "{actual_output}")')
                passed = False
            else:
                print(f'  {GREEN}{status:<5}{RESET} output.matches: /{pattern}/')
                passed_checks += 1

        elif key.startswith("tools_used"):
            expected_list = expected if isinstance(expected, list) else [expected]
            status = "PASS" if expected_list == actual_tools_list else "FAIL"
            if status == "FAIL":
                print(f'  {RED}{status:<5}{RESET} tools_used expected: {expected_list}, got: {actual_tools_list}')
                passed = False
            else:
                print(f'  {GREEN}{status:<5}{RESET} tools_used: {expected_list}')
                passed_checks += 1

        elif key.startswith("memory."):
            path = key[len("memory."):]
            actual_value = get_nested(actual_memory, path)
            status = "PASS" if actual_value == expected else "FAIL"
            if status == "FAIL":
                print(f'  {RED}{status:<5}{RESET} memory.{path}: expected {expected}, got {actual_value}')
                passed = False
            else:
                print(f'  {GREEN}{status:<5}{RESET} memory.{path} = {expected}')
                passed_checks += 1

        else:
            status = "FAIL"
            print(f'  {RED}{status:<5}{RESET} Unknown assert key: {key}')
            passed = False

    summary_msg = f"  Summary: {passed_checks} passed / {total_checks} total"
    if passed:
        print(f'{GREEN}{summary_msg}{RESET}')
    else:
        print(f'{RED}{summary_msg}{RESET}')
    return all_passed



def main():
parser = argparse.ArgumentParser(
        description="TestHaven CLI – Run structured tests on agent outputs.",
        epilog="""
Usage Examples:
  testhaven my_test.test.json agent.py
  testhaven --run-all tests/ agent.py

Options:
  --run-all    Run all test files in a directory or glob
  --help       Show this help message
""".strip()
    )
    args = parser.parse_args()
    parser.add_argument("testfile", nargs="?", help="Path to test file (JSON or YAML)")
    parser.add_argument("--run-all", metavar="PATTERN", help="Run all test files in directory or glob pattern")
    parser.add_argument("agentfile", help="Path to agent Python file")

    if args.run_all and args.testfile:
        print("ERROR: Cannot specify both a test file and --run-all", file=sys.stderr)
        sys.exit(1)

    if args.run_all:
        all_passed = run_all_tests(args.run_all, args.agentfile)
        sys.exit(0 if all_passed else 1)
    elif args.testfile:
        passed = run_single_test(args.testfile, args.agentfile)
        sys.exit(0 if passed else 1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
