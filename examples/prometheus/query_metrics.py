"""Example: Configuring production Prometheus metrics provider."""

from aegis.providers import PrometheusConfig
from aegis.providers.production import PrometheusMetricsProvider


def main() -> None:
    # 1. Production Prometheus configuration
    config = PrometheusConfig(
        base_url="http://prometheus.monitoring.svc.cluster.local:9090",
        timeout_seconds=15.0,
        verify_ssl=True,
        api_token=None,  # Or injected from os.environ["PROMETHEUS_TOKEN"]
    )

    # 2. Instantiate provider
    provider = PrometheusMetricsProvider(config)
    print(f"Initialized {type(provider).__name__} for {config.base_url}")
    print("Provider conforms to MetricsProvider protocol.")


if __name__ == "__main__":
    main()
