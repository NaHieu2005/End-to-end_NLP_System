from __future__ import annotations

import re
import unicodedata

from rag_system.model_cache import avoid_windows_platform_wmi_probe, configure_hf_cache

HF_CACHE_DIR = configure_hf_cache()
avoid_windows_platform_wmi_probe()

from transformers import pipeline

from rag_system.retrieval import DEFAULT_RERANKER_MODEL, Reranker, Retriever

DEFAULT_QA_MODEL = "letrunglinh/qa_pnc"


def _normalize_for_rules(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    return re.sub(r"\s+", " ", text).strip()


def _clean_answer(answer: str) -> str:
    answer = answer.strip()
    answer = answer.strip(" \t\r\n,.;:()[]{}\"'“”‘’")
    answer = re.sub(r"^\bngày\s+", "", answer, flags=re.IGNORECASE)
    return answer.strip()


def _postprocess_answer(answer: str) -> str:
    return _clean_answer(answer)


def _quoted_title(question: str) -> str | None:
    match = re.search(r'"([^"]{8,})"', question)
    return match.group(1) if match else None


def _article_window_for_title(context: str, title: str) -> str:
    compact = re.sub(r"\s+", " ", context).strip()
    position = compact.lower().find(title.lower())
    if position == -1:
        return compact
    start = compact.rfind("Nguồn:", 0, position)
    if start == -1:
        start = max(0, position - 500)
    next_source = compact.find("Nguồn:", position + len(title))
    end = next_source if next_source != -1 else min(len(compact), position + 5000)
    return compact[start:end].strip()


def _field_value(article_text: str, field: str) -> str:
    fields = ["Nguồn", "Chuyên mục", "Tên miền", "URL", "Ngày đăng", "Tiêu đề", "Tóm tắt", "Nội dung"]
    next_fields = "|".join(re.escape(name) for name in fields if name != field)
    match = re.search(rf"{re.escape(field)}:\s*(.*?)(?=\s+(?:{next_fields}):|$)", article_text)
    return _clean_answer(match.group(1)) if match else ""


def _sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
        if sentence.strip()
    ]


def _fast_article_answer(question: str, context: str) -> str | None:
    title = _quoted_title(question)
    if not title:
        return None
    article_text = _article_window_for_title(context, title)
    q = _normalize_for_rules(question)

    if "nguồn" in q:
        return _field_value(article_text, "Nguồn") or None
    if "chuyên mục" in q:
        return _field_value(article_text, "Chuyên mục") or None
    if "tên miền" in q:
        return _field_value(article_text, "Tên miền") or None
    if "url" in q:
        return _field_value(article_text, "URL") or None
    if "ngày đăng" in q or "được đăng ngày" in q:
        return _field_value(article_text, "Ngày đăng") or None
    if "tóm tắt" in q or "nội dung chính" in q:
        return _field_value(article_text, "Tóm tắt") or None

    body = _field_value(article_text, "Nội dung")
    if not body:
        return None
    sentences = _sentences(body)
    if "bắt đầu bằng những từ" in q:
        return " ".join(body.split()[:12]) or None
    if "mở đầu" in q or "mở đầu bằng" in q:
        return sentences[0] if sentences else None
    if "thông tin thứ hai" in q:
        return sentences[1] if len(sentences) > 1 else None
    if "thông tin thứ ba" in q:
        return sentences[2] if len(sentences) > 2 else None
    if "kết thúc" in q:
        return sentences[-1] if sentences else None
    return None


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
        self.qa_model = qa_model
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k
        self.reranker = Reranker(reranker_model) if reranker_model else None
        self.reader = None

    def answer(self, question: str) -> str:
        retrieved = self.retriever.retrieve(question, top_k=self.top_k)
        if self.reranker:
            retrieved = self.reranker.rerank(question, retrieved, top_k=self.rerank_top_k)
        context = "\n\n".join(chunk.text for chunk, _score in retrieved)
        if not context.strip():
            return ""
        fast_answer = _fast_article_answer(question, context)
        if fast_answer:
            return fast_answer
        if self.reader is None:
            self.reader = pipeline(
                "question-answering",
                model=self.qa_model,
                tokenizer=self.qa_model,
                model_kwargs={"cache_dir": str(HF_CACHE_DIR)},
                tokenizer_kwargs={"cache_dir": str(HF_CACHE_DIR)},
            )
        result = self.reader(question=question, context=context)
        answer = str(result.get("answer", "")).strip()
        return _postprocess_answer(answer)
