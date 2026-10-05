"""Example: Managing safe Kubernetes workloads without arbitrary shell access."""

import asyncio

from aegis.providers import KubernetesConfig
from aegis.providers.production import KubernetesProvider


async def main() -> None:
    # 1. Kubernetes configuration with read_only=False for controlled actions
    config = KubernetesConfig(
        default_namespace="production",
        read_only=False,
    )
    k8s = KubernetesProvider(config)
    k8s.register_workload("payment-service", "production", replicas=3)

    # 2. Query status (Read-Only)
    status = await k8s.get_deployment_status("payment-service", "production")
    print(f"Current deployment status: {status}")

    # 3. Execute typed restart (Safe, typed action only — NO arbitrary shell)
    res = await k8s.execute_action(
        action_type="SERVICE_RESTART",
        target="payment-service",
        parameters={"namespace": "production"},
    )
    print(f"Action executed: {res['message']}")


if __name__ == "__main__":
    asyncio.run(main())
