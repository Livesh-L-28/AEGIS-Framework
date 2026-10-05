# Contributing to AEGIS Framework

Thank you for your interest in contributing to AEGIS Framework! We welcome contributions to enhance autonomous reliability, AI reasoning, and incident engineering capabilities.

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Development Setup

### Prerequisites
- Python 3.12 or later
- Git

### Initializing Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/Livesh-L-28/AEGIS-Framework.git
   cd AEGIS-Framework
   ```

2. Create and activate an isolated virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install in editable mode with development dependencies:
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

---

## Formatting, Linting & Type Checking

We maintain strict code quality standards using `ruff` and `mypy`:

```bash
# Check code style and common errors
ruff check .

# Automatically apply safe fixes
ruff check --fix .

# Format code
ruff format .

# Static type checking
mypy aegis
```

---

## Running Tests

All unit tests must pass before submitting contributions:

```bash
# Run test suite
pytest

# Run tests with coverage report
pytest --cov=aegis
```

---

## Pull Request Workflow

1. **Branching**: Create a feature or bugfix branch off `main` (e.g., `git checkout -b feat/evidence-normalizer`).
2. **Atomic Commits**: Keep commits concise and descriptively titled.
3. **Tests**: Add unit tests for all new modules, classes, and helper functions.
4. **Validation**: Ensure `ruff check .`, `mypy aegis`, and `pytest` pass cleanly.
5. **PR Submission**: Open a Pull Request detailing the problem solved, design decisions, and any configuration changes.

---

## Security-Sensitive Changes

Any modifications involving:
- LLM boundary guards or firewalls
- Prompt sanitization or injection defenses
- Tool execution sandboxing or permission checks
- Autonomy tier thresholds (`LEVEL_0` through `LEVEL_3`)
- Human approval bypass rules or emergency stop kill switches

Must be explicitly flagged in the pull request description as **Security-Sensitive**. These changes require extra review to ensure fail-closed security invariants are never violated.

---

## Provider Contributions

AEGIS Framework is designed to be extensible across diverse LLM, observability, and vector backends:
- All new providers must inherit from base interface protocols in `aegis.providers`.
- Provider dependencies must remain optional rather than core requirements.
- External API calls in unit tests must be mocked.
