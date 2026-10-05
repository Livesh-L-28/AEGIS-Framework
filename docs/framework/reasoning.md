# Causal Reasoning Engine

The ReasoningEngine formulates, scores, and validates causal root cause hypotheses.

## Architectural Safeguards
- **Grounding Verification**: Ensures hypotheses cite observed evidence artifacts.
- **Deterministic Heuristics**: Evaluates architectural fault signatures (DB saturation, cache invalidation, deployment regression) independently of LLM availability.
- **Fail-Safe Fallback**: If an LLM backend fails, deterministic reasoning continues uninterrupted.
