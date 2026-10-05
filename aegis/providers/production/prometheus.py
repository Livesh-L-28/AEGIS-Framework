"""Production-grade Prometheus / Mimir metrics provider implementing MetricsProvider."""

from datetime import datetime
from typing import Any

from aegis.providers.config import PrometheusConfig
from aegis.providers.errors import ProviderInvalidResponseError
from aegis.providers.http import ResilientHTTPClient


class PrometheusMetricsProvider:
    """Production metrics provider querying Prometheus / Mimir HTTP API."""

    def __init__(self, config: PrometheusConfig) -> None:
        self.config = config
        self.client = ResilientHTTPClient(config, provider_name="prometheus")

    async def query_metric(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query time series data points from Prometheus / Mimir."""
        # 1. Build Prometheus PromQL expression
        label_matchers: list[str] = []
        if service_name:
            label_matchers.append(f'service="{service_name}"')
        if labels:
            for k, v in labels.items():
                label_matchers.append(f'{k}="{v}"')

        matcher_str = f"{{{','.join(label_matchers)}}}" if label_matchers else ""
        query_expr = f"{metric_name}{matcher_str}"

        # 2. Query range API
        params = {
            "query": query_expr,
            "start": str(start_time.timestamp()),
            "end": str(end_time.timestamp()),
            "step": self.config.default_step,
            "timeout": f"{int(self.config.query_timeout_seconds)}s",
        }

        data = await self.client.get_json("api/v1/query_range", params=params)

        if not isinstance(data, dict) or data.get("status") != "success":
            err_msg = data.get("error", "Unknown Prometheus query error") if isinstance(data, dict) else "Invalid response"
            raise ProviderInvalidResponseError(
                f"Prometheus query failed: {err_msg}",
                provider_name="prometheus",
            )

        result_data = data.get("data", {})
        results: list[dict[str, Any]] = []

        for matrix_item in result_data.get("result", []):
            item_metric = matrix_item.get("metric", {})
            values = matrix_item.get("values", [])
            for ts, val in values:
                try:
                    f_val = float(val)
                except (ValueError, TypeError):
                    f_val = 0.0

                results.append(
                    {
                        "metric_name": metric_name,
                        "value": f_val,
                        "timestamp": datetime.fromtimestamp(float(ts), tz=start_time.tzinfo),
                        "service_name": service_name or item_metric.get("service") or item_metric.get("job"),
                        "labels": item_metric,
                        "signal": metric_name,
                        "provenance": f"prometheus:{metric_name}",
                    }
                )

        return results


__all__ = ["PrometheusMetricsProvider"]
