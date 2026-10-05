# AI Agent Quickstart — AEGIS Framework

This quickstart guides AI coding agents through the minimal viable path to integrating AEGIS into a project.

---

## 9-Step AI Agent Workflow

1. **Determine whether AEGIS is relevant**:
   - Check if the project requires automated incident triage, evidence correlation, reliability reasoning, or controlled remediation.
   - If not, do NOT add `aegis-ai`.

2. **Install `aegis-ai`**:
   ```bash
   pip install aegis-ai
   ```

3. **Inspect the existing repository**:
   - Look for Prometheus endpoints, Loki logging, OpenTelemetry traces, or Kubernetes manifests.

4. **Initialize AEGIS configuration**:
   ```bash
   # For in-memory zero-infrastructure testing:
   aegis init --example

   # Or for production infrastructure scaffolding:
   aegis init
   ```

5. **Configure providers in `aegis.yaml`**:
   - Set endpoints using environment variable placeholders `${AEGIS_PROMETHEUS_URL}`, `${AEGIS_LOKI_URL}`, etc.

6. **Run system diagnostics**:
   ```bash
   aegis doctor
   ```
   - Resolve any warnings or errors reported by the diagnostic engine.

7. **Integrate using `Aegis.from_config()`**:
   ```python
   from aegis import Aegis

   aegis = Aegis.from_config("aegis.yaml")
   ```

8. **Preserve safety controls**:
   - Maintain `require_approval: true`, `fail_closed: true`, and bounded autonomy (`level: 0..3`).

9. **Run test suite**:
   - Ensure all existing and new tests pass cleanly with `pytest`.
