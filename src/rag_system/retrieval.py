from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from rag_system.model_cache import avoid_windows_platform_wmi_probe, configure_hf_cache

HF_CACHE_DIR = configure_hf_cache()
avoid_windows_platform_wmi_probe()

try:
    from sentence_transformers import CrossEncoder, SentenceTransformer
except Exception:  # pragma: no cover - allows a TF-IDF fallback when torch DLLs fail
    CrossEncoder = None
    SentenceTransformer = None
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
DEFAULT_RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


def _loose_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _is_metadata_question(question: str) -> bool:
    q = _loose_text(question)
    metadata_terms = [
        "url",
        "ten mien",
        "nguon",
        "chuyen muc",
        "email",
        "e mail",
        "dien thoai",
        "dia chi",
        "lien he",
        "website",
        "facebook",
    ]
    return any(term in q for term in metadata_terms)


def _metadata_penalty(text: str) -> float:
    lowered = text.lower()
    signals = [
        "thong tin lien he",
        "dien thoai",
        "e-mail",
        "email",
        "website",
        "facebook",
        "dia chi",
        "url:",
        "ten mien",
    ]
    if any(signal in lowered for signal in signals):
        return 0.6
    if "http" in lowered or "@" in lowered:
        return 0.4
    return 0.0


@dataclass
class DocumentChunk:
    doc_id: str
    source: str
    text: str


class Retriever:
    def __init__(
        self,
        model_name: str,
        chunks: list[DocumentChunk],
        embeddings: Any,
        vectorizer: TfidfVectorizer | None = None,
    ):
        self.model_name = model_name
        self.chunks = chunks
        self.embeddings = embeddings
        self.vectorizer = vectorizer
        self.model = None
        if self.vectorizer is None:
            if SentenceTransformer is None:
                raise RuntimeError("sentence_transformers is not available and no TF-IDF vectorizer was saved.")
            self.model = SentenceTransformer(model_name, cache_folder=str(HF_CACHE_DIR))

    @classmethod
    def load(cls, path: str | Path) -> "Retriever":
        with Path(path).open("rb") as file:
            payload = pickle.load(file)
        return cls(
            payload["model_name"],
            payload["chunks"],
            payload["embeddings"],
            payload.get("vectorizer"),
        )

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as file:
            pickle.dump(
                {
                    "model_name": self.model_name,
                    "chunks": self.chunks,
                    "embeddings": self.embeddings,
                    "vectorizer": self.vectorizer,
                },
                file,
            )

    def retrieve(self, question: str, top_k: int = 5) -> list[tuple[DocumentChunk, float]]:
        if self.vectorizer is not None:
            query_embedding = self.vectorizer.transform([question])
        else:
            query_embedding = self.model.encode([question], normalize_embeddings=True)
        scores = cosine_similarity(query_embedding, self.embeddings)[0]
        title_match = re.search(r'"([^"]{3,})"', question)
        prefix_match = re.search(r'bắt đầu bằng\s+"([^"]{8,})"', question, flags=re.IGNORECASE)
        if title_match:
            title = title_match.group(1).lower()
            scores = scores.copy()
            for idx, chunk in enumerate(self.chunks):
                text = chunk.text.lower()
                if f"tiêu đề: {title}" in text:
                    scores[idx] += 2.5
                elif title in text:
                    scores[idx] += 0.6
        if prefix_match:
            prefix = _loose_text(prefix_match.group(1))
            scores = scores.copy()
            for idx, chunk in enumerate(self.chunks):
                if prefix and prefix in _loose_text(chunk.text):
                    scores[idx] += 5.0
        if not _is_metadata_question(question):
            scores = scores.copy()
            for idx, chunk in enumerate(self.chunks):
                scores[idx] -= _metadata_penalty(chunk.text)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[idx], float(scores[idx])) for idx in top_indices]


class Reranker:
    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL):
        if CrossEncoder is None:
            raise RuntimeError("sentence_transformers CrossEncoder is not available.")
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
    texts = [chunk.text for chunk in chunks]
    if not model_name.lower().startswith("tfidf") and SentenceTransformer is not None:
        try:
            model = SentenceTransformer(model_name, cache_folder=str(HF_CACHE_DIR))
            embeddings = model.encode(texts, normalize_embeddings=True)
            return Retriever(model_name, chunks, np.asarray(embeddings))
        except Exception as exc:  # noqa: BLE001 - fall back in constrained local envs
            print(f"Falling back to TF-IDF retriever because dense model failed: {exc}")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        max_features=50000,
        token_pattern=r"(?u)\b\w+\b",
    )
    embeddings = vectorizer.fit_transform(texts)
    return Retriever("tfidf-word-ngram", chunks, embeddings, vectorizer)
