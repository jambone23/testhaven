import json
import re
import sys
import os
import glob
import importlib.util
import argparse

# ANSI color codes for output formatting
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def load_test_case(path):
    """Load a test case from JSON or YAML file, upgrading old formats to new schema."""
    with open(path, "r") as f:
        if path.endswith((".yaml", ".yml")):
            try:
                import yaml
            except ImportError:
                raise RuntimeError("YAML support requires PyYAML to be installed")
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    # Handle legacy: if this is a list of single-turn tests (JSON array)
    if isinstance(data, list):
        return {"description": f"Multiple tests in {os.path.basename(path)}", "steps": data}

    # Handle legacy single-turn format (no steps)
    if "steps" not in data:
        legacy = data
        return {
            "description": legacy.get("description", "Legacy single-turn test"),
            "memory": legacy.get("memory", {}),
            "steps": [{
                "input": legacy.get("input", ""),
                "assert": legacy.get("assert", {}),
                "expected": legacy.get("expected", None),
            }]
        }

    return data

def get_nested(memory, path):
    """Get nested value from memory dict using dot-path (e.g. 'booking.status')."""
    parts = path.split(".")
    for p in parts:
        if isinstance(memory, dict) and p in memory:
            memory = memory[p]
        else:
            return None
    return memory

def normalize_tools(tools_val):
    """Convert tools_used value to a flat list of strings."""
    if isinstance(tools_val, list):
        names = []
        for t in tools_val:
            if isinstance(t, str):
                names.append(t)
            elif isinstance(t, dict) and "name" in t:
                names.append(t["name"])
            else:
                names.append(str(t))
        return names
    return [str(tools_val)]

def run_assertions(output, tools, memory, asserts):
    passed = True
    passed_checks = 0
    total_checks = 0
    tools_list = normalize_tools(tools)

    for key, expected in asserts.items():
        total_checks += 1
        if key.startswith("output.equals"):
            status = "PASS" if output == expected else "FAIL"
            if status == "FAIL":
                print(f"  {RED}{status:<5}{RESET} output.equals: expected \"{expected}\", got \"{output}\"")
            else:
                print(f"  {GREEN}{status:<5}{RESET} output.equals: \"{expected}\"")
                passed_checks += 1
        elif key.startswith("output.includes"):
            status = "PASS" if expected in output else "FAIL"
            if status == "FAIL":
                print(f"  {RED}{status:<5}{RESET} output.includes: \"{expected}\" (output was: \"{output}\")")
            else:
                print(f"  {GREEN}{status:<5}{RESET} output.includes: \"{expected}\"")
                passed_checks += 1
        elif key.startswith("output.matches"):
            matched = bool(re.search(expected, output))
            status = "PASS" if matched else "FAIL"
            if status == "FAIL":
                print(f"  {RED}{status:<5}{RESET} output.matches: /{expected}/ (output was: \"{output}\")")
            else:
                print(f"  {GREEN}{status:<5}{RESET} output.matches: /{expected}/")
                passed_checks += 1
        elif key.startswith("tools_used"):
            expected_list = expected if isinstance(expected, list) else [expected]
            status = "PASS" if expected_list == tools_list else "FAIL"
            if status == "FAIL":
                print(f"  {RED}{status:<5}{RESET} tools_used expected: {expected_list}, got: {tools_list}")
            else:
                print(f"  {GREEN}{status:<5}{RESET} tools_used: {expected_list}")
                passed_checks += 1
        elif key.startswith("memory."):
            path = key[len("memory."):]
            actual_value = get_nested(memory, path)
            status = "PASS" if actual_value == expected else "FAIL"
            if status == "FAIL":
                print(f"  {RED}{status:<5}{RESET} memory.{path}: expected {expected}, got {actual_value}")
            else:
                print(f"  {GREEN}{status:<5}{RESET} memory.{path} = {expected}")
                passed_checks += 1
        else:
            print(f"  {RED}FAIL {RESET} Unknown assert key: {key}")
            passed = False
            continue

        if status == "FAIL":
            passed = False

    summary_msg = f"  Summary: {passed_checks} passed / {total_checks} total"
    print(f"{GREEN if passed else RED}{summary_msg}{RESET}")
    return passed

def assert_case(test, agent_func):
    """Run a multi-step test case with memory propagation."""
    description = test.get("description", "<Unnamed test>")
    memory = test.get("memory", {})
    steps = test.get("steps", [])

    print(f"{BOLD}Test: {description}{RESET}")
    all_pass = True
    for i, step in enumerate(steps):
        input_text = step.get("input", "")
        print(f"Step {i+1}: {input_text}")

        result = agent_func(input_text, memory)
        output = result.get("output", "")
        tools_used = result.get("tools_used", [])
        memory = result.get("memory", {})

        # Support both 'assert' (granular) and 'expected' (strict) styles
        if "assert" in step:
            passed = run_assertions(output, tools_used, memory, step["assert"])
        elif "expected" in step:
            passed = True
            expected = step["expected"]
            if output != expected.get("output"):
                print(f"  {RED}FAIL {RESET} output mismatch: expected \"{expected.get('output')}\", got \"{output}\"")
                passed = False
            if normalize_tools(tools_used) != normalize_tools(expected.get("tools_used", [])):
                print(f"  {RED}FAIL {RESET} tools_used mismatch: expected {expected.get('tools_used')}, got {tools_used}")
                passed = False
            if memory != expected.get("memory", {}):
                print(f"  {RED}FAIL {RESET} memory mismatch:\n  expected: {expected.get('memory')}\n  got: {memory}")
                passed = False
            if passed:
                print(f"{GREEN}  All expected fields matched.{RESET}")
        else:
            print(f"{YELLOW}  No assertions or expected block provided.{RESET}")
            passed = True

        all_pass = all_pass and passed
        print()
    return all_pass

def run_single_test(test_file, agent_path):
    spec = importlib.util.spec_from_file_location("agent_module", agent_path)
    agent_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent_module)

    test = load_test_case(test_file)
    return assert_case(test, agent_module.agent)

def run_all_tests(test_dir_pattern, agent_path):
    if os.path.isdir(test_dir_pattern):
        test_files = glob.glob(os.path.join(test_dir_pattern, "*.test.json")) \
                   + glob.glob(os.path.join(test_dir_pattern, "*.test.yaml")) \
                   + glob.glob(os.path.join(test_dir_pattern, "*.test.yml"))
    else:
        test_files = glob.glob(test_dir_pattern)
    test_files = sorted(test_files)

    print(f"\nRunning {len(test_files)} test file(s) from {test_dir_pattern}\n" + "-" * 40)
    total = len(test_files)
    passed = 0

    for tf in test_files:
        result = run_single_test(tf, agent_path)
        if result:
            passed += 1

    print("-" * 40)
    if passed == total:
        print(f"{GREEN}ALL TESTS PASSED ({passed}/{total}){RESET}")
        return True
    else:
        print(f"{RED}{total - passed} test(s) FAILED ({passed}/{total} passed){RESET}")
        return False

def main():
    parser = argparse.ArgumentParser(description="TestHaven CLI - Agent Testing Framework")
    parser.add_argument("--run-all", action="store_true", help="Run all test files in a directory (or pattern)")
    parser.add_argument("test_path", help="Path to test file or directory")
    parser.add_argument("agent_path", help="Path to agent Python file")
    args = parser.parse_args()

    if args.run_all:
        success = run_all_tests(args.test_path, args.agent_path)
    else:
        success = run_single_test(args.test_path, args.agent_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()


