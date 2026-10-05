"""In-memory vector embedding and similarity search providers without external databases."""

import math
from collections.abc import Sequence
from typing import Any


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class InMemoryEmbeddingProvider:
    """Deterministic in-memory embedding generator for tests and examples."""

    def __init__(self, dimensions: int = 8) -> None:
        self.dimensions = dimensions

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Compute deterministic vector embeddings for strings."""
        embeddings: list[list[float]] = []
        for text in texts:
            # Deterministic pseudo-embedding from characters
            vec = [0.0] * self.dimensions
            for i, ch in enumerate(text):
                vec[i % self.dimensions] += (ord(ch) % 31) / 31.0
            # Normalize vector
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0.0:
                vec = [round(x / norm, 4) for x in vec]
            embeddings.append(vec)
        return embeddings


class InMemoryVectorIndexProvider:
    """Pure in-memory vector similarity index without PostgreSQL/pgvector dependencies."""

    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a document vector into the memory index."""
        self.documents.append(
            {
                "id": doc_id,
                "content": content,
                "embedding": embedding,
                "metadata": metadata or {},
            }
        )

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search top-k matching documents by cosine similarity."""
        scored: list[tuple[float, dict[str, Any]]] = []

        for doc in self.documents:
            # Check metadata filters
            if filters:
                doc_meta = doc.get("metadata", {})
                if not all(doc_meta.get(k) == v for k, v in filters.items()):
                    continue

            sim = _cosine_similarity(query_vector, doc.get("embedding", []))
            doc_copy = {
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": round(sim, 4),
            }
            scored.append((sim, doc_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]


__all__ = [
    "InMemoryEmbeddingProvider",
    "InMemoryVectorIndexProvider",
]
