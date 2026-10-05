"""Safe Git / GitHub intelligence providers and deployment correlation.

CRITICAL SECURITY INVARIANT:
This module strictly forbids arbitrary shell execution or LLM-generated shell commands.
Local operations use fixed, validated git CLI invocations with no shell=True.
"""

from datetime import UTC, datetime
from typing import Any

from aegis.providers.config import GitHubConfig
from aegis.providers.errors import ProviderInvalidResponseError
from aegis.providers.http import ResilientHTTPClient


class GitHubDeploymentProvider:
    """Queries GitHub Deployments and Commits API for release and deployment history."""

    def __init__(self, config: GitHubConfig, repo_owner: str, repo_name: str) -> None:
        self.config = config
        self.repo_owner = repo_owner
        self.repo_name = repo_name

        from aegis.providers.config import HTTPClientConfig

        http_config = HTTPClientConfig(
            base_url=config.api_base_url,
            timeout_seconds=config.timeout_seconds,
            api_token=config.token,
            custom_headers={"Accept": "application/vnd.github.v3+json"},
        )
        self.client = ResilientHTTPClient(http_config, provider_name="github")

    async def list_recent_deployments(
        self,
        service_name: str | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """List GitHub deployment events correlated within timeframe."""
        endpoint = f"repos/{self.repo_owner}/{self.repo_name}/deployments"
        params: dict[str, Any] = {"per_page": 50}
        if service_name:
            params["environment"] = service_name

        data = await self.client.get_json(endpoint, params=params)
        if not isinstance(data, list):
            raise ProviderInvalidResponseError(
                "GitHub deployments API did not return a list",
                provider_name="github",
            )

        results: list[dict[str, Any]] = []
        for dep in data:
            created_at_str = dep.get("created_at")
            if not created_at_str:
                continue

            try:
                # ISO8601 parsing
                dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.now(UTC)

            if dt < start_time or dt > end_time:
                continue

            sha = dep.get("sha", "unknown")
            env = dep.get("environment", service_name or "production")

            results.append(
                {
                    "deployment_id": str(dep.get("id")),
                    "service": service_name or env,
                    "service_name": service_name or env,
                    "version": dep.get("ref", sha[:7]),
                    "commit_sha": sha,
                    "timestamp": dt,
                    "status": "SUCCESS",
                    "author": dep.get("creator", {}).get("login", "unknown"),
                    "metadata": {
                        "environment": env,
                        "description": dep.get("description", ""),
                    },
                }
            )

        return results


__all__ = ["GitHubDeploymentProvider"]
