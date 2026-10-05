"""Unit tests for Incident domain models."""

from aegis.incidents import Incident, IncidentSeverity, IncidentSource, IncidentStatus


def test_incident_creation_defaults() -> None:
    """Incident domain model initializes cleanly without database or orm."""
    incident = Incident(
        title="High error rate in payment gateway",
        severity=IncidentSeverity.HIGH,
        service_name="payment-service",
    )
    assert incident.title == "High error rate in payment gateway"
    assert incident.severity == IncidentSeverity.HIGH
    assert incident.status == IncidentStatus.OPEN
    assert incident.source == IncidentSource.MANUAL
    assert incident.service_name == "payment-service"
    assert incident.resolved_at is None
    assert incident.id is not None
    assert incident.organization_id is not None


def test_incident_lifecycle_transitions() -> None:
    """Incident state transitions work purely in memory."""
    incident = Incident(title="Latency Spike", severity=IncidentSeverity.MEDIUM)
    assert incident.status == IncidentStatus.OPEN

    incident.mark_investigating()
    assert incident.status == IncidentStatus.INVESTIGATING

    incident.mark_resolved()
    assert incident.status == IncidentStatus.RESOLVED
    assert incident.resolved_at is not None
