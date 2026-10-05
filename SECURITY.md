# Security Policy

## Responsible Disclosure

The AEGIS Framework team takes security vulnerabilities seriously. We appreciate responsible disclosures that allow us to remediate issues before they can be exploited.

If you believe you have discovered a vulnerability, please report it via private security advisory on GitHub or email the maintainers at security@aegis-framework.org. Please do **NOT** open public issues or pull requests for undisclosed vulnerabilities.

### What to Include in a Report
- Description of the vulnerability and attack vector
- Reproduction steps or proof of concept (PoC)
- Potential impact on workloads or environments
- Any proposed mitigations or fixes

---

## Core Security Invariants

AEGIS Framework is engineered around **fail-closed AI security**. The framework is designed for autonomous reliability engineering, which means software agents must never be permitted to act unpredictably or execute unverified commands.

### 1. No Secrets in Issues or PRs
Never commit tokens, passwords, API keys, certificates, or proprietary data to pull requests or issues. Any PR containing active credentials will be immediately rejected and redacted.

### 2. Fail-Closed Boundary Execution
Any security check failure (firewall validation, policy constraint, signature verification) must default to aborting execution rather than failing open.

### 3. Prompt Injection Defense
AI agents consuming untrusted telemetry (e.g., incident descriptions, application logs, third-party error traces) must treat all ingested inputs as untrusted data planes. Instructions embedded inside log strings or error messages must never override agent behavioral instructions.

### 4. Arbitrary Command Execution
Under no circumstance may agentic workflows construct or run arbitrary shell commands without parameterized validation, whitelisting, and strict sandboxing.

### 5. Multi-Tenant Isolation
Tenant boundaries, workspace IDs, and organizational context must be cryptographically or structurally partitioned across evidence stores, reasoning contexts, and vector retrieval indices.

### 6. Autonomy Safety & Human-in-the-Loop
Autonomous operations follow deterministic autonomy tiers (`LEVEL_0` through `LEVEL_3`). High-risk remediations (such as service restarts, rollbacks, traffic draining, or infrastructure mutations) require non-bypassable human approval gates, hard execution timeouts, and an immediate emergency stop kill switch.
