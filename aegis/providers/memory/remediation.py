"""In-memory safe remediation provider operating exclusively on typed actions.

CRITICAL SAFETY INVARIANT:
This provider NEVER executes shell commands, subprocesses, SSH, kubectl,
or Docker sockets. It simulates state changes in memory strictly on typed framework actions.
"""

from datetime import UTC, datetime
from typing import Any, ClassVar

from aegis.remediation import RemediationActionType


class InMemoryRemediationProvider:
    """Simulates state changes in memory strictly on typed framework actions."""

    ALLOWED_ACTIONS: ClassVar[set[str]] = {
        RemediationActionType.SERVICE_RESTART.value,
        RemediationActionType.CONFIG_CHANGE.value,
        RemediationActionType.CACHE_INVALIDATION.value,
        RemediationActionType.SCALING.value,
        RemediationActionType.DEPLOYMENT.value,
        RemediationActionType.ROLLBACK.value,
    }

    def __init__(self) -> None:
        self.service_states: dict[str, dict[str, Any]] = {}
        self.execution_history: list[dict[str, Any]] = []

    def set_service_state(self, target: str, state: dict[str, Any]) -> None:
        """Initialize simulated service state."""
        self.service_states[target] = dict(state)

    def get_service_state(self, target: str) -> dict[str, Any]:
        """Fetch current simulated service state."""
        return self.service_states.get(target, {})

    async def execute_action(
        self,
        action_type: str,
        target: str,
        parameters: dict[str, Any],
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        """Execute a typed remediation action in memory."""
        # 1. Enforce allowed typed actions only
        if action_type not in self.ALLOWED_ACTIONS:
            raise ValueError(
                f"Action type '{action_type}' is not supported by InMemoryRemediationProvider. "
                f"Only typed actions are permitted: {self.ALLOWED_ACTIONS}"
            )

        # 2. Simulate state change based on action type
        current_state = self.service_states.setdefault(target, {"status": "HEALTHY", "instances": 1})
        record = {
            "action_type": action_type,
            "target": target,
            "parameters": dict(parameters),
            "executed_at": datetime.now(UTC).isoformat(),
            "status": "COMPLETED",
        }

        if action_type == RemediationActionType.SERVICE_RESTART.value:
            current_state["status"] = "RESTARTED"
            current_state["restarted_at"] = record["executed_at"]
            record["output"] = f"Service {target} gracefully restarted in memory."

        elif action_type == RemediationActionType.CACHE_INVALIDATION.value:
            current_state["cache_flushed_at"] = record["executed_at"]
            record["output"] = f"Cache keys invalidated on target {target}."

        elif action_type == RemediationActionType.SCALING.value:
            replicas = parameters.get("replicas", current_state.get("instances", 1) + 1)
            current_state["instances"] = replicas
            record["output"] = f"Target {target} scaled to {replicas} replicas."

        elif action_type in (RemediationActionType.ROLLBACK.value, RemediationActionType.DEPLOYMENT.value):
            target_version = parameters.get("version", "previous-stable")
            current_state["version"] = target_version
            record["output"] = f"Target {target} rolled back / updated to {target_version}."

        elif action_type == RemediationActionType.CONFIG_CHANGE.value:
            current_state.setdefault("config", {}).update(parameters.get("config", {}))
            record["output"] = f"Target {target} configuration updated."

        self.execution_history.append(record)
        return record


__all__ = ["InMemoryRemediationProvider"]
