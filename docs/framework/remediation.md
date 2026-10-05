# Remediation Planning

Remediation proposals are structured, declarative plans.

## Required Plan Elements
- **Typed Actions Only**: `SERVICE_RESTART`, `CACHE_INVALIDATION`, `SCALING`, `DEPLOYMENT`, `ROLLBACK`.
- **Deterministic SHA-256 Hash**: Cryptographically fingerprints actions and parameters.
- **Blast Radius**: Explicitly bounds affected microservices.
- **Validation Criteria**: Health check endpoints and success metrics.
- **Rollback Strategy**: Pre-computed rollback plan in case validation fails.
