"""Production-grade Grafana Loki log provider implementing LogProvider."""

from datetime import datetime
from typing import Any

from aegis.providers.config import LokiConfig
from aegis.providers.errors import ProviderInvalidResponseError
from aegis.providers.http import ResilientHTTPClient


class LokiLogProvider:
    """Production log provider querying Grafana Loki HTTP API via LogQL."""

    def __init__(self, config: LokiConfig) -> None:
        self.config = config
        self.client = ResilientHTTPClient(config, provider_name="loki")

    async def query_logs(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query log streams from Grafana Loki and normalize records."""
        # 1. Build LogQL query
        selector = f'{{service="{service_name}"}}' if service_name else '{job=~".+"}'
        logql_query = selector

        if query and query != "*":
            if "level:" in query.lower():
                lvl = query.split("level:")[1].split()[0]
                logql_query += f' |= "{lvl}"'
            else:
                logql_query += f' |= "{query}"'

        # Convert to nanoseconds for Loki
        start_ns = int(start_time.timestamp() * 1_000_000_000)
        end_ns = int(end_time.timestamp() * 1_000_000_000)

        params = {
            "query": logql_query,
            "start": str(start_ns),
            "end": str(end_ns),
            "limit": str(min(limit, self.config.default_limit)),
            "direction": "BACKWARD",
        }

        data = await self.client.get_json("loki/api/v1/query_range", params=params)

        if not isinstance(data, dict) or data.get("status") != "success":
            raise ProviderInvalidResponseError(
                f"Loki query returned unsuccessful status: {data.get('error', 'unknown error') if isinstance(data, dict) else 'non-dict'}",
                provider_name="loki",
            )

        entries: list[dict[str, Any]] = []
        result_data = data.get("data", {}).get("result", [])

        for stream in result_data:
            stream_labels = stream.get("stream", {})
            values = stream.get("values", [])
            for ts_ns, log_line in values:
                try:
                    ts_float = float(ts_ns) / 1_000_000_000
                    ts_dt = datetime.fromtimestamp(ts_float, tz=start_time.tzinfo)
                except (ValueError, TypeError):
                    ts_dt = start_time

                entries.append(
                    {
                        "service": service_name or stream_labels.get("service") or stream_labels.get("app"),
                        "service_name": service_name or stream_labels.get("service") or stream_labels.get("app"),
                        "level": stream_labels.get("level", "INFO").upper(),
                        "message": str(log_line),
                        "timestamp": ts_dt,
                        "signal": "loki_log_entry",
                        "provenance": f"loki:{logql_query}",
                        "metadata": stream_labels,
                    }
                )

        return entries


__all__ = ["LokiLogProvider"]
