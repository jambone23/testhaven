# TestHaven

TestHaven is a CLI-first test harness for AI agents, verifying that they produce the expected output, use the correct tools, and maintain the expected memory state.


## Key Features

- Assert on agent output (supports substring matching, regex, or exact match)
- Track tool usage (ensure the agent invoked the expected tools)
- Verify memory state (dot-path assertions on nested memory fields)
- Run standalone or in CI (exit code indicates pass/fail)
- Write tests in JSON or YAML (no coding required)


## Installation

TestHaven is not yet on PyPI. To install from source, run:

```bash
git clone https://github.com/yourname/testhaven.git
cd testhaven
pip install -e .
```

To enable YAML support (optional), install PyYAML:

```bash
pip install pyyaml
```


## Quick Example

**Test file: `tests/flight_booking.test.json`**

```json
{
  "schema_version": "0.1",
  "description": "Flight booking to Berlin via Gatwick",
  "input": "Book me a flight to Berlin next week",
  "memory": {
    "preferred_airport": "Gatwick"
  },
  "assert": {
    "output.includes": "Gatwick",
    "output.matches": ".*Berlin.*",
    "tools_used": ["Skyscanner"],
    "memory.last_booking.destination": "Berlin",
    "memory.last_booking.departure": "Gatwick"
  }
}
```

**Agent function: `example_agent.py`**

```python
def agent(input_text, memory):
    if memory is None:
        memory = {}
    destination = "Unknown Destination"
    idx = input_text.lower().find(" to ")
    if idx != -1:
        dest_part = input_text[idx+4:]
        markers = [" next", " on ", " in ", " at ", " this ", " tomorrow", " today"]
        for marker in markers:
            m_idx = dest_part.lower().find(marker)
            if m_idx != -1:
                dest_part = dest_part[:m_idx]
                break
        destination = dest_part.strip().strip(".,!?") or destination
    departure = memory.get("preferred_airport", "Unknown Airport")
    memory['last_booking'] = {"destination": destination, "departure": departure}
    return {
        "output": f"Booking flight from {departure} to {destination}.",
        "tools_used": ["Skyscanner"],
        "memory": memory
    }
```

**Run the test:**

```bash
testhaven tests/flight_booking.test.json example_agent.py
```

Or run all tests in a folder:

```bash
testhaven --run-all tests/ example_agent.py
```

You can also run:

```bash
testhaven --help
```

To see usage options and flags.


## Test File Schema

Each test file includes:

- `schema_version`: currently `"0.1"`
- `description`: short test description
- `input`: the user prompt or query
- `memory`: initial memory state (optional)
- `assert`: conditions to verify after execution

Supported assertions include:

- `output.includes`: check that output contains a substring
- `output.matches`: check that output matches a regex pattern
- `output.equals`: check that output exactly matches a string
- `tools_used`: check that the agent used the expected tools
- `memory.<path>`: check the value of a nested memory field (using dot-path)


## Continuous Integration

TestHaven is CI-friendly: it exits with code 1 if any test fails.

**GitHub Actions example:**

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e .
      - run: pip install pyyaml  # Optional, for YAML support
      - run: testhaven --run-all tests/ example_agent.py
```


## Contributing to TestHaven

We warmly welcome contributions from everyone in the community. Whether it’s reporting a bug, adding a new feature, or improving documentation, every bit of help counts.

If you’d like to contribute, here are the steps to get started:

1. **Fork and set up the repository:** Fork the TestHaven GitHub repository and clone it to your machine. Install the package in development mode (see the Installation section above for guidance). This will allow you to test your changes locally.
2. **Create a feature branch:** It’s good practice to create a new branch for your work (for example, `feature/new-awesome-thing`).
3. **Make your changes with care:** Implement your bug fix or new feature. Try to follow the coding style of the project for consistency. If you’re adding a feature or fixing a bug, consider writing tests to cover your changes.
4. **Run tests:** Before submitting, run the test suite to ensure everything still passes. This helps maintain quality and makes the review process smoother.
5. **Open an issue (optional but recommended):** If your contribution is a significant change or new feature, please open an issue to discuss it with the maintainers first.
6. **Submit a pull request:** Push your branch to your GitHub fork and open a pull request against TestHaven’s main repository. In the PR description, clearly explain your changes and mention which issue (if any) you’re addressing.

We aim to review pull requests promptly and will provide constructive feedback. Thank you for helping to improve TestHaven!


## Licence

MIT
