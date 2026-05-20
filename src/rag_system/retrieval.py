from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from rag_system.model_cache import avoid_windows_platform_wmi_probe, configure_hf_cache

HF_CACHE_DIR = configure_hf_cache()
avoid_windows_platform_wmi_probe()

from sentence_transformers import CrossEncoder, SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
DEFAULT_RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


@dataclass
class DocumentChunk:
    doc_id: str
    source: str
    text: str


class Retriever:
    def __init__(self, model_name: str, chunks: list[DocumentChunk], embeddings: np.ndarray):
        self.model_name = model_name
        self.chunks = chunks
        self.embeddings = embeddings
        self.model = SentenceTransformer(model_name, cache_folder=str(HF_CACHE_DIR))

    @classmethod
    def load(cls, path: str | Path) -> "Retriever":
        with Path(path).open("rb") as file:
            payload = pickle.load(file)
        return cls(payload["model_name"], payload["chunks"], payload["embeddings"])

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as file:
            pickle.dump(
                {
                    "model_name": self.model_name,
                    "chunks": self.chunks,
                    "embeddings": self.embeddings,
                },
                file,
            )

    def retrieve(self, question: str, top_k: int = 5) -> list[tuple[DocumentChunk, float]]:
        query_embedding = self.model.encode([question], normalize_embeddings=True)
        scores = cosine_similarity(query_embedding, self.embeddings)[0]
        title_match = re.search(r'"([^"]{8,})"', question)
        if title_match:
            title = title_match.group(1).lower()
            scores = scores.copy()
            for idx, chunk in enumerate(self.chunks):
                if title in chunk.text.lower():
                    scores[idx] += 1.0
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[idx], float(scores[idx])) for idx in top_indices]


class Reranker:
    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL):
        self.model_name = model_name
        self.model = CrossEncoder(model_name, model_kwargs={"cache_dir": str(HF_CACHE_DIR)})

    def rerank(
        self,
        question: str,
        candidates: list[tuple[DocumentChunk, float]],
        top_k: int,
    ) -> list[tuple[DocumentChunk, float]]:
        if not candidates:
            return []
        pairs = [(question, chunk.text) for chunk, _score in candidates]
        scores = self.model.predict(pairs)
        ranked = sorted(
            ((chunk, float(score)) for (chunk, _old_score), score in zip(candidates, scores)),
            key=lambda item: item[1],
            reverse=True,
        )
        return ranked[:top_k]


def build_retriever(
    chunks: list[DocumentChunk],
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> Retriever:
    model = SentenceTransformer(model_name, cache_folder=str(HF_CACHE_DIR))
    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True)
    return Retriever(model_name, chunks, np.asarray(embeddings))
