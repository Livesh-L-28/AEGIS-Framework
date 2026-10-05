"""Example: Building and injecting a custom LLM ModelProvider."""

import asyncio
import json
from typing import Any

from aegis import Aegis
from aegis.providers import ModelProvider
from aegis.providers.memory import InMemoryLogProvider


class CustomAnthropicStyleModelProvider:
    """Demonstrates how to integrate an external LLM into AEGIS via ModelProvider."""

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        system_instruction: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        # Returns structured JSON adhering to AEGIS hypothesis schema
        return json.dumps({
            "title": "Database Connection Pool Saturation",
            "description": "Exhausted connection pool threads under burst traffic",
            "reasoning": "High queue waiting time observed in correlated error logs",
        })


assert isinstance(CustomAnthropicStyleModelProvider(), ModelProvider)


async def main() -> None:
    custom_model = CustomAnthropicStyleModelProvider()
    logs = InMemoryLogProvider()

    aegis = Aegis(
        log_provider=logs,
        model_provider=custom_model,
    )
    inc = aegis.create_incident(title="Checkout freeze", service_name="checkout-svc")
    result = await aegis.investigate(inc)
    print(f"Custom model diagnosed incident: {result.summary}")


if __name__ == "__main__":
    asyncio.run(main())
