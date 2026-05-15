from __future__ import annotations

from rag_system.model_cache import configure_hf_cache

HF_CACHE_DIR = configure_hf_cache()

from transformers import pipeline

from rag_system.retrieval import DEFAULT_RERANKER_MODEL, Reranker, Retriever

DEFAULT_QA_MODEL = "letrunglinh/qa_pnc"


class ExtractiveRAG:
    def __init__(
        self,
        retriever: Retriever,
        qa_model: str = DEFAULT_QA_MODEL,
        top_k: int = 8,
        reranker_model: str | None = DEFAULT_RERANKER_MODEL,
        rerank_top_k: int = 4,
    ):
        self.retriever = retriever
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k
        self.reranker = Reranker(reranker_model) if reranker_model else None
        self.reader = pipeline(
            "question-answering",
            model=qa_model,
            tokenizer=qa_model,
        )

    def answer(self, question: str) -> str:
        retrieved = self.retriever.retrieve(question, top_k=self.top_k)
        if self.reranker:
            retrieved = self.reranker.rerank(question, retrieved, top_k=self.rerank_top_k)
        context = "\n\n".join(chunk.text for chunk, _score in retrieved)
        if not context.strip():
            return ""
        result = self.reader(question=question, context=context)
        return str(result.get("answer", "")).strip()
