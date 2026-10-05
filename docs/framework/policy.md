# Policy Engine & Guardrails

The PolicyEngine enforces deterministic rules that override all AI outputs.

## Principles
1. **Determinism**: Policy decisions are absolute. An LLM claim of "LOW risk" does not override policy calculation.
2. **Separation of Duties**: An action's author cannot be its approver for MEDIUM or HIGH risk proposals.
3. **Secret Redaction**: Prompts containing unredacted credentials or API keys are rejected immediately.
