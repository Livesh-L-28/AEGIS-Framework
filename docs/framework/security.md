# Security Invariants

AEGIS provides defense-in-depth through mandatory security invariants.

1. **Fail-Closed AI Firewall**: Direct integration with `llmfirewall-core 1.0.0`. If unavailable, fails closed.
2. **Governed Tool Gateway**: Deny-by-default on all tool calls. Mutating actions are blocked on the read-only plane.
3. **No Arbitrary Shell**: Shell execution, `shell=True`, `os.system`, `subprocess`, SSH, and Docker sockets are strictly prohibited.
