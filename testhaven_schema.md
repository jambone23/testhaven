# TestHaven Schema Reference

This document describes the structure of TestHaven test files (YAML or JSON), used to validate AI agent behavior across single or multi-turn interactions.

## Top-Level Structure

Each test file must be either:

- A single test object with a `steps` list (recommended)
- A list of legacy single-turn tests (auto-upgraded internally)
- A legacy single-turn test with `input`, `assert`, and optional `memory` (also auto-upgraded)

## Supported Top-Level Fields

| Field         | Type        | Required | Description |
|---------------|-------------|----------|-------------|
| `description` | `string`    | Optional | A brief description of the test case |
| `memory`      | `object`    | Optional | Initial memory passed to the agent before the first step |
| `steps`       | `list`      | Yes      | List of sequential steps to execute (each with input + assertions) |

## Step Structure

Each item in `steps` is an object with:

| Field       | Type      | Required | Description |
|-------------|-----------|----------|-------------|
| `input`     | `string`  | Yes      | Input prompt for the agent in this step |
| `assert`    | `object`  | Optional | Assertions to check after the agent responds |
| `expected`  | `object`  | Optional | An alternative to `assert`, used for strict equality checking |

Only one of `assert` or `expected` should be used per step.

## Assertions (`assert` block)

Assertions validate parts of the agent's response. Supported keys:

### Output Assertions

| Key                | Type     | Description |
|--------------------|----------|-------------|
| `output.includes`  | `string` | Passes if agent output contains the substring |
| `output.matches`   | `string` | Passes if agent output matches a regex (Python `re.search`) |
| `output.equals`    | `string` | Passes if agent output exactly matches the string |

### Tool Assertions

| Key          | Type              | Description |
|---------------|-------------------|-------------|
| `tools_used`  | `list<string>`    | Exact list of tools expected to be used during the step |

### Memory Assertions

| Key Pattern             | Type    | Description |
|-------------------------|---------|-------------|
| `memory.<dot.path>`     | Any     | Checks that the value at a nested path in memory equals the expected value |

Example: `memory.last_booking.destination: "Berlin"`

## Strict Matching (`expected` block)

The `expected` block is an alternative to granular `assert` keys. It requires full equality on all fields.

| Field         | Type         | Description |
|---------------|--------------|-------------|
| `output`      | `string`     | Exact output string expected from the agent |
| `tools_used`  | `list<string>` | Expected tools used |
| `memory`      | `object`     | Full memory state expected after this step |

## Examples

### YAML (Recommended)

```yaml
description: "Book flight to Berlin"
memory:
  preferred_airport: "Gatwick"
steps:
  - input: "Book me a flight to Berlin next week"
    assert:
      output.includes: "Gatwick"
      output.matches: ".*Berlin.*"
      tools_used: ["Skyscanner"]
      memory.last_booking.destination: "Berlin"
      memory.last_booking.departure: "Gatwick"
```

### JSON (Legacy Format)

```json
{
  "description": "Book flight to Tokyo",
  "input": "Book a flight to Tokyo next week",
  "memory": { "preferred_airport": "LAX" },
  "assert": {
    "output.equals": "Booking flight from LAX to Tokyo.",
    "tools_used": ["Skyscanner"],
    "memory.last_booking.destination": "Tokyo",
    "memory.last_booking.departure": "LAX"
  }
}
```

This legacy format is auto-wrapped into a single-step test internally.

---

For questions or schema evolution, see the main README or open a GitHub issue.