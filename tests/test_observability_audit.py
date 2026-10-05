"""Tests for framework-native telemetry sink and append-only audit logging."""

from aegis.core import Aegis
from aegis.core.audit import AuditCategory, InMemoryAuditLogger
from aegis.core.observability import FrameworkEvent, TelemetrySink


def test_telemetry_sink_event_emission_and_redaction() -> None:
    """TelemetrySink emits lifecycle events and redacts sensitive parameters."""
    sink = TelemetrySink()
    captured_events: list[FrameworkEvent] = []

    sink.register_handler(lambda ev: captured_events.append(ev))

    ev = sink.emit(
        "custom.test.event",
        service_name="payment-service",
        token="super-secret-jwt-token",
        metrics_count=42,
    )

    assert ev.event_name == "custom.test.event"
    assert ev.payload["metrics_count"] == 42
    assert ev.payload["token"] == "[REDACTED]"
    assert len(captured_events) == 1
    assert len(sink.get_events()) == 1


def test_audit_logger_immutable_records() -> None:
    """InMemoryAuditLogger records categorized audit trails and sanitizes secrets."""
    audit = InMemoryAuditLogger()

    event = audit.record(
        category=AuditCategory.POLICY,
        action="policy.evaluated",
        actor="operator-alice",
        target="order-service",
        outcome="DENIED",
        details={"api_key": "secret-12345", "reason": "Missing secondary approval"},
    )

    assert event.category == AuditCategory.POLICY
    assert event.outcome == "DENIED"
    assert event.details["api_key"] == "[REDACTED]"
    assert audit.count() == 1

    denied = audit.get_events(outcome="DENIED")
    assert len(denied) == 1
    assert denied[0].actor == "operator-alice"


def test_aegis_integration_with_telemetry_and_audit() -> None:
    """Aegis lifecycle automatically emits telemetry events and records audit trails."""
    sink = TelemetrySink()
    audit = InMemoryAuditLogger()
    aegis = Aegis(telemetry=sink, audit_logger=audit)

    aegis.create_incident(title="Test latency incident", service_name="cart-service")

    # Verify telemetry
    inc_events = sink.get_events("incident.created")
    assert len(inc_events) == 1
    assert inc_events[0].service_name == "cart-service"

    # Verify audit
    assert audit.count() == 1
    audit_event = audit.get_events(category=AuditCategory.REASONING)[0]
    assert audit_event.action == "incident.created"
