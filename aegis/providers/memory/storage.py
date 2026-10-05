"""In-memory key-value artifact and report storage provider."""

from typing import Any


class InMemoryStorageProvider:
    """Stores binary payloads and artifacts in memory without external blob stores."""

    def __init__(self) -> None:
        self.storage: dict[str, dict[str, Any]] = {}

    async def save(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Store binary payload in memory and return URI."""
        self.storage[key] = {
            "data": data,
            "content_type": content_type,
            "size": len(data),
        }
        return f"memory://{key}"

    async def get(self, key: str) -> bytes | None:
        """Retrieve binary payload from memory."""
        item = self.storage.get(key)
        if item is None:
            return None
        data = item["data"]
        return bytes(data) if isinstance(data, (bytes, bytearray)) else None

    def list_keys(self) -> list[str]:
        """List all stored keys."""
        return list(self.storage.keys())


__all__ = ["InMemoryStorageProvider"]
