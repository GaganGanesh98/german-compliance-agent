from abc import ABC, abstractmethod

import httpx

from app.config import settings

JINA_EMBEDDINGS_URL = "https://api.jina.ai/v1/embeddings"
JINA_MODEL = "jina-embeddings-v3"
JINA_BATCH_SIZE = 100
EMBEDDING_DIMENSION = 1024


class Embedder(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError


class JinaEmbedder(Embedder):
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.jina_api_key

    def _embed_batch(self, texts: list[str], task: str) -> list[list[float]]:
        if not texts:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        embeddings: list[list[float]] = []

        with httpx.Client(timeout=60.0) as client:
            for start in range(0, len(texts), JINA_BATCH_SIZE):
                batch = texts[start : start + JINA_BATCH_SIZE]
                response = client.post(
                    JINA_EMBEDDINGS_URL,
                    headers=headers,
                    json={
                        "model": JINA_MODEL,
                        "task": task,
                        "input": batch,
                    },
                )
                response.raise_for_status()
                data = response.json()["data"]
                embeddings.extend(item["embedding"] for item in data)

        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_batch(texts, task="retrieval.passage")

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text], task="retrieval.query")[0]
