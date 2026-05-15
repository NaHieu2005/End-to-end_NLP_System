from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


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
        self.model = SentenceTransformer(model_name)

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
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[idx], float(scores[idx])) for idx in top_indices]


def build_retriever(
    chunks: list[DocumentChunk],
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
) -> Retriever:
    model = SentenceTransformer(model_name)
    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True)
    return Retriever(model_name, chunks, np.asarray(embeddings))
