"""Example: Configuring production OpenTelemetry trace provider."""

from aegis.providers import OpenTelemetryConfig
from aegis.providers.production import OpenTelemetryTraceProvider


def main() -> None:
    # 1. OpenTelemetry / Jaeger HTTP API configuration
    config = OpenTelemetryConfig(
        base_url="http://jaeger-query.monitoring.svc.cluster.local:16686",
        timeout_seconds=10.0,
        verify_ssl=True,
    )

    # 2. Instantiate provider
    provider = OpenTelemetryTraceProvider(config)
    print(f"Initialized {type(provider).__name__} for {config.base_url}")
    print("Provider conforms to TraceProvider protocol.")


if __name__ == "__main__":
    main()
