# Evidence Engine

The EvidenceEngine orchestrates multi-source telemetry collection across configured providers.

## Key Capabilities
1. **Bounded Time Windows**: Automatically bounds collection around incident detection timestamps.
2. **Deduplication**: Eliminates redundant signals from repeated scrapes.
3. **Relevance Scoring**: Deterministically weights evidence by signal severity and type.
4. **Chronological Timeline**: Generates ordered event timelines with traceable citations to underlying spans, queries, and logs.
