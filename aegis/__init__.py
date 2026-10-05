"""AEGIS Framework — Open-source Autonomous Reliability Engineering Framework.

AEGIS Framework is a developer-facing library for building AI-powered incident investigation,
evidence engineering, root-cause reasoning, remediation, policy enforcement, and autonomous
reliability workflows.

Reference Platform:
    The full enterprise flagship platform is maintained in AEGIS AI.
"""

from aegis.autonomy import AutonomyDecision, AutonomyLevel
from aegis.config import AegisProjectConfig
from aegis.core import Aegis, AegisConfig
from aegis.evidence import Evidence, EvidenceSeverity, EvidenceType
from aegis.incidents import Incident, IncidentSeverity, IncidentSource, IncidentStatus
from aegis.policy import DataClassification, DeclarativePolicy, PolicyDecisionResult, PolicyEngine
from aegis.reasoning import Hypothesis, HypothesisStatus, ReasoningResult
from aegis.remediation import RemediationAction, RemediationActionType, RemediationPlan
from aegis.security import FirewallDecisionAction, SecurityRiskLevel

__version__ = "0.1.0"

__all__ = [
    "Aegis",
    "AegisConfig",
    "AegisProjectConfig",
    "AutonomyDecision",
    "AutonomyLevel",
    "DataClassification",
    "DeclarativePolicy",
    "Evidence",
    "EvidenceSeverity",
    "EvidenceType",
    "FirewallDecisionAction",
    "Hypothesis",
    "HypothesisStatus",
    "Incident",
    "IncidentSeverity",
    "IncidentSource",
    "IncidentStatus",
    "PolicyDecisionResult",
    "PolicyEngine",
    "ReasoningResult",
    "RemediationAction",
    "RemediationActionType",
    "RemediationPlan",
    "SecurityRiskLevel",
    "__version__",
]
