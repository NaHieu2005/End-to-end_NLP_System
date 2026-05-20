from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_OLLAMA_MODEL = "qwen2.5:7b-instruct-lowmem-cpu"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
NO_EVIDENCE_ANSWER = "Không có dữ kiện trong tài liệu."

SYSTEM_PROMPT = f"""Bạn là trợ lý hỏi đáp dựa trên tài liệu.

Luật bắt buộc:
1. Chỉ được dùng thông tin trong phần NGỮ CẢNH.
2. Chỉ trả lời bằng tiếng Việt. Không dùng tiếng Trung. Không dùng tiếng Anh, trừ thuật ngữ/tên riêng xuất hiện trong ngữ cảnh.
3. Không được suy đoán, không dùng kiến thức bên ngoài, không tự bịa số liệu/tên/ngày.
4. Nếu ngữ cảnh không có dữ kiện đủ rõ để trả lời, trả lời đúng câu: "{NO_EVIDENCE_ANSWER}"
5. Có thể dùng dữ kiện tương đương hoặc cách diễn đạt gần nghĩa nếu nó thật sự xuất hiện trong ngữ cảnh.
6. Trả lời ngắn gọn, trực tiếp. Nếu có thể, kèm chỉ mục nguồn dạng [1], [2].
"""


@dataclass
class Chunk:
    source: str
    text: str


class LightweightRetriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.chunk_terms = [Counter(self._tokens(chunk.text)) for chunk in chunks]

    @classmethod
    def from_corpus(cls, path: str | Path) -> "LightweightRetriever":
        chunks: list[Chunk] = []
        with Path(path).open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                chunks.append(Chunk(source=str(row.get("source", "")), text=str(row.get("text", ""))))
        if not chunks:
            raise SystemExit(f"Không có dữ liệu trong corpus: {path}")
        return cls(chunks)

    def retrieve(self, question: str, top_k: int) -> list[tuple[Chunk, float]]:
        query_terms = Counter(self._tokens(question))
        if not query_terms:
            return []
        scores = []
        for idx, terms in enumerate(self.chunk_terms):
            overlap = sum(min(count, terms.get(term, 0)) for term, count in query_terms.items())
            article_bonus = self._article_number_bonus(question, self.chunks[idx].text)
            score = overlap + article_bonus
            if score > 0:
                scores.append((idx, float(score)))
        ranked = sorted(scores, key=lambda item: item[1], reverse=True)[:top_k]
        return [(self.chunks[idx], score) for idx, score in ranked]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[\wÀ-ỹ]+", text.lower(), flags=re.UNICODE)

    @staticmethod
    def _article_number_bonus(question: str, text: str) -> int:
        match = re.search(r"bài báo số\s+(\d+)", question.lower())
        if not match:
            return 0
        return 20 if f"bài báo số {match.group(1)}" in text.lower() else 0


def focused_text(text: str, question: str, max_chars: int) -> str:
    compact = " ".join(text.split())
    match = re.search(r"bài báo số\s+(\d+)", question.lower())
    if match:
        needle = f"bài báo số {match.group(1)}"
        position = compact.lower().find(needle)
        if position >= 0:
            start = max(0, position - 120)
            end = min(len(compact), position + max_chars)
            prefix = "... " if start > 0 else ""
            suffix = " ..." if end < len(compact) else ""
            return prefix + compact[start:end].strip() + suffix
    if len(compact) > max_chars:
        return compact[:max_chars].rsplit(" ", 1)[0] + " ..."
    return compact


def build_context(retrieved: list[tuple[Chunk, float]], question: str, max_chars_per_chunk: int) -> str:
    blocks = []
    for idx, (chunk, score) in enumerate(retrieved, 1):
        text = focused_text(chunk.text, question, max_chars_per_chunk)
        blocks.append(f"[{idx}] Nguồn: {chunk.source} | score={score:.4f}\n{text}")
    return "\n\n".join(blocks)


def ollama_chat(model: str, url: str, question: str, context: str, timeout: int) -> str:
    user_prompt = f"""NGỮ CẢNH:
{context}

CÂU HỎI:
{question}

Hãy trả lời theo đúng luật trong system message."""
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "temperature": 0.0,
            "top_p": 0.2,
            "repeat_penalty": 1.1,
            "num_predict": 96,
        },
    }
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise SystemExit(f"Không gọi được Ollama tại {url}: {exc}") from exc
    return str(result.get("message", {}).get("content", "")).strip()


def answer_question(args: argparse.Namespace, retriever: LightweightRetriever, question: str) -> str:
    retrieved = retriever.retrieve(question, top_k=args.top_k)
    retrieved = retrieved[: args.context_chunks]
    if not retrieved:
        return NO_EVIDENCE_ANSWER
    context = build_context(retrieved, question, args.max_chars_per_chunk)
    if args.show_context:
        print("\n--- NGỮ CẢNH ĐƯA VÀO MODEL ---")
        print(context)
        print("--- HẾT NGỮ CẢNH ---\n")
    answer = ollama_chat(args.model, args.ollama_url, question, context, args.timeout)
    return answer or NO_EVIDENCE_ANSWER


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/processed/corpus.jsonl")
    parser.add_argument("--model", default=DEFAULT_OLLAMA_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--question")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--context-chunks", type=int, default=3)
    parser.add_argument("--max-chars-per-chunk", type=int, default=900)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--show-context", action="store_true")
    args = parser.parse_args()

    print("Đang load corpus...")
    retriever = LightweightRetriever.from_corpus(args.corpus)

    if args.question:
        print(answer_question(args, retriever, args.question))
        return

    print("Nhập câu hỏi. Gõ 'exit', 'quit' hoặc 'q' để thoát.\n")
    while True:
        try:
            question = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoát.")
            break
        if question.lower() in {"exit", "quit", "q"}:
            print("Thoát.")
            break
        if not question:
            continue
        print("Trả lời:", answer_question(args, retriever, question))
        print()


if __name__ == "__main__":
    main()
