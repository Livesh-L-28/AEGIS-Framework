# Incident Lifecycle & Investigation Workflow

The AEGIS Framework defines a rigorous, deterministic lifecycle for incident detection, evidence collection, causal reasoning, policy evaluation, and safe remediation execution.

```text
       +-----------------------+
       |   1. Incident Created |
       +-----------------------+
                   |
                   v
       +-----------------------+
       | 2. EvidenceEngine     | <--- MetricsProvider, LogProvider,
       |    Collection         |      TraceProvider, DeploymentProvider
       +-----------------------+
                   |
                   v
       +-----------------------+
       | 3. Chronological      |
       |    Timeline Built     |
       +-----------------------+
                   |
                   v
       +-----------------------+
       | 4. ReasoningEngine    | <--- Causal rule matching & ModelProvider
       |    & Grounding        |
       +-----------------------+
                   |
                   v
       +-----------------------+
       | 5. PolicyEngine       | <--- Data classification & risk checks
       |    Evaluation         |
       +-----------------------+
                   |
                   v
       +-----------------------+
       | 6. RemediationPlanner | ---> Blast Radius, Risk Score,
       |    Proposal           |      ValidationPlan, RollbackPlan
       +-----------------------+
                   |
                   v
       +-----------------------+
       | 7. AutonomyEngine     | ---> LEVEL_0 / LEVEL_1 / LEVEL_2 / LEVEL_3
       |    & Approval Gate    |      (LEVEL_4 is permanently unavailable)
       +-----------------------+
                   |
                   v
       +-----------------------+
       | 8. Typed Remediation  | <--- InMemoryRemediationProvider
       |    Execution          |      (Strictly no arbitrary shell)
       +-----------------------+
                   |
                   v
       +-----------------------+
       | 9. Incident Resolved  |
       +-----------------------+
```

---

## Lifecycle Steps

### Step 1: Incident Creation
An incident represents a detected or suspected degradation. Incidents track lifecycle status (`OPEN`, `INVESTIGATING`, `MITIGATING`, `RESOLVED`, `CLOSED`), severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), affected service, and contextual metadata.

### Step 2: Evidence Collection
The `EvidenceEngine` queries all configured providers across the incident time window. Each returned signal is normalized into a strongly typed `Evidence` record containing:
- `evidence_type` (`METRIC`, `LOG`, `TRACE`, `DEPLOYMENT`, etc.)
- `signal` and `content`
- `severity` and `confidence`
- `provenance` (reproducible trace or query reference)
- Calculated `relevance_score`

### Step 3: Chronological Timeline
The engine orders deduplicated evidence into a structured `TimelineEntry` chain, linking observed anomalies to their exact evidence IDs.

### Step 4: Causal Reasoning & Grounding
The `ReasoningEngine` evaluates the evidence against causal heuristic rules (e.g. database connection starvation, deployment regression, cache breakdown) and optional LLM augmentation via `ModelProvider`.
Each candidate hypothesis is scored, checked for contradicting evidence, and verified for grounding.

### Step 5: Deterministic Policy Gate
The `PolicyEngine` enforces strict deterministic security rules:
- Unredacted credentials or secrets are blocked immediately.
- Only authorized AI models on the whitelist may be queried.
- High and medium risk operations require human approval.
- Separation of duties is enforced: an author cannot approve their own remediation proposal.

### Step 6: Remediation Planning
The `RemediationPlanner` generates a comprehensive `RemediationPlan` including:
- Concrete typed actions (`SERVICE_RESTART`, `CACHE_INVALIDATION`, `SCALING`, `DEPLOYMENT`, `ROLLBACK`)
- Deterministic plan fingerprint / hash
- Blast radius estimation
- Declarative `ValidationPlan` (health check endpoints, success criteria)
- Declarative `RollbackPlan`

### Step 7: Autonomy Tiers & Approvals
The `AutonomyEngine` checks if the plan is authorized to execute:
- `LEVEL_0`: Observe only; all auto-execution is disabled.
- `LEVEL_1`: Recommend only; human approval is mandatory.
- `LEVEL_2`: Auto-execute low-risk actions only.
- `LEVEL_3`: Auto-execute approved medium-risk single-service actions.
- `LEVEL_4`: **Permanently disabled** by architecture design.
- Emergency kill-switch immediately halts any autonomous action.

### Step 8: Safe Typed Remediation
The `RemediationProvider` executes only typed actions. Arbitrary subprocesses, `os.system`, `subprocess.Popen`, Docker sockets, and SSH commands are strictly forbidden.
