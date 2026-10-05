"""In-memory deployment and release provider for correlation analysis."""

from datetime import datetime
from typing import Any


class InMemoryDeploymentProvider:
    """Stores and queries deployment records in memory."""

    def __init__(self, initial_deployments: list[dict[str, Any]] | None = None) -> None:
        self.deployments: list[dict[str, Any]] = list(initial_deployments or [])

    def record_deployment(
        self,
        deployment_id: str,
        service: str,
        version: str,
        commit_sha: str,
        timestamp: datetime,
        status: str = "SUCCESS",
        author: str = "deploy-bot",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a deployment event into memory."""
        self.deployments.append(
            {
                "deployment_id": deployment_id,
                "service": service,
                "service_name": service,
                "version": version,
                "commit_sha": commit_sha,
                "timestamp": timestamp,
                "status": status,
                "author": author,
                "metadata": metadata or {},
            }
        )

    async def list_recent_deployments(
        self,
        service_name: str | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """List deployment events and releases within timeframe."""
        results: list[dict[str, Any]] = []
        for d in self.deployments:
            svc = d.get("service") or d.get("service_name")
            if service_name is not None and svc is not None and svc != service_name:
                continue

            ts = d.get("timestamp")
            if isinstance(ts, datetime):
                if ts.tzinfo is not None and start_time.tzinfo is None:
                    ts_cmp = ts.replace(tzinfo=None)
                elif ts.tzinfo is None and start_time.tzinfo is not None:
                    ts_cmp = ts.replace(tzinfo=start_time.tzinfo)
                else:
                    ts_cmp = ts
                if ts_cmp < start_time or ts_cmp > end_time:
                    continue

            results.append(dict(d))

        return results


__all__ = ["InMemoryDeploymentProvider"]
