"""Example: Building and injecting a custom LogProvider."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from aegis import Aegis
from aegis.providers import LogProvider


class CustomElasticsearchStyleLogProvider:
    """Demonstrates custom LogProvider querying an internal log aggregator."""

    def __init__(self) -> None:
        self.logs: list[dict[str, Any]] = []

    def add_log(self, service: str, level: str, msg: str, ts: datetime) -> None:
        self.logs.append({
            "service": service,
            "service_name": service,
            "level": level,
            "message": msg,
            "timestamp": ts,
            "signal": "custom_log",
            "provenance": "elasticsearch:query",
        })

    async def query_logs(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return [
            entry for entry in self.logs
            if (service_name is None or entry["service_name"] == service_name)
        ][:limit]


assert isinstance(CustomElasticsearchStyleLogProvider(), LogProvider)


async def main() -> None:
    now = datetime.now(UTC)
    custom_logs = CustomElasticsearchStyleLogProvider()
    custom_logs.add_log("auth-service", "ERROR", "OAuth token validation timeout", now)

    aegis = Aegis(log_provider=custom_logs)
    inc = aegis.create_incident(title="Auth timeouts", service_name="auth-service")
    res = await aegis.investigate(inc)
    print(f"Investigation completed with custom log provider: {res.summary}")


if __name__ == "__main__":
    asyncio.run(main())
