from __future__ import annotations

from transformers import pipeline

from rag_system.retrieval import Retriever


class ExtractiveRAG:
    def __init__(
        self,
        retriever: Retriever,
        qa_model: str = "deepset/xlm-roberta-base-squad2",
        top_k: int = 5,
    ):
        self.retriever = retriever
        self.top_k = top_k
        self.reader = pipeline("question-answering", model=qa_model, tokenizer=qa_model)

    def answer(self, question: str) -> str:
        retrieved = self.retriever.retrieve(question, top_k=self.top_k)
        context = "\n\n".join(chunk.text for chunk, _score in retrieved)
        if not context.strip():
            return ""
        result = self.reader(question=question, context=context)
        return str(result.get("answer", "")).strip()
