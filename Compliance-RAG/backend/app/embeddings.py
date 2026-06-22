from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod

import httpx

from app.config import settings

EMBEDDING_DIMENSION = 1024

# --- Jina (kept for reference; superseded by Gemini for the free tier) ---------
JINA_EMBEDDINGS_URL = "https://api.jina.ai/v1/embeddings"
JINA_MODEL = "jina-embeddings-v3"
JINA_BATCH_SIZE = 100

# --- Google Gemini -------------------------------------------------------------
GEMINI_MODEL = "models/gemini-embedding-001"
GEMINI_EMBED_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:embedContent"
)
GEMINI_REQUEST_DELAY_S = 0.35
GEMINI_MAX_RETRIES = 5


class Embedder(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


class GeminiEmbedder(Embedder):
    """Embeddings via Google Gemini (free tier). Multilingual; output dimensionality
    is pinned to EMBEDDING_DIMENSION so it matches the pgvector schema. Vectors are
    L2-normalized (Google recommends this for non-default dimensions)."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.google_api_key

    def _embed_one(
        self,
        client: httpx.Client,
        headers: dict[str, str],
        text: str,
        task_type: str,
    ) -> list[float]:
        payload = {
            "model": GEMINI_MODEL,
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
            "outputDimensionality": EMBEDDING_DIMENSION,
        }
        for attempt in range(GEMINI_MAX_RETRIES):
            response = client.post(GEMINI_EMBED_URL, headers=headers, json=payload)
            if response.status_code not in {429, 503}:
                response.raise_for_status()
                return _l2_normalize(response.json()["embedding"]["values"])
            if attempt == GEMINI_MAX_RETRIES - 1:
                response.raise_for_status()
            time.sleep(2**attempt)
        raise RuntimeError("unreachable")

    def _embed_batch(self, texts: list[str], task_type: str) -> list[list[float]]:
        if not texts:
            return []

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        embeddings: list[list[float]] = []

        with httpx.Client(timeout=60.0) as client:
            for index, text in enumerate(texts):
                embeddings.append(self._embed_one(client, headers, text, task_type))
                if index + 1 < len(texts):
                    time.sleep(GEMINI_REQUEST_DELAY_S)

        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text], task_type="RETRIEVAL_QUERY")[0]


class JinaEmbedder(Embedder):
    """Embeddings via Jina (requires paid balance). Retained behind the Embedder
    interface in case we switch back."""

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
                    json={"model": JINA_MODEL, "task": task, "input": batch},
                )
                response.raise_for_status()
                data = response.json()["data"]
                embeddings.extend(item["embedding"] for item in data)

        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_batch(texts, task="retrieval.passage")

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text], task="retrieval.query")[0]


def get_embedder() -> Embedder:
    """Return the configured default embedder. Swap providers here in one place."""
    return GeminiEmbedder()
