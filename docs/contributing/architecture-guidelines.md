# Architecture Guidelines

1. **Protocol Separation**: External systems must implement Protocols defined in `aegis.providers`.
2. **Zero Inherent DB Lock-in**: Framework core never assumes SQL or Redis.
3. **Fail-Closed Security**: AI safety and LLM Firewalls fail closed.
4. **Pure Typed Actions**: Subprocesses, arbitrary shells, and kubectl shell commands are strictly forbidden.
