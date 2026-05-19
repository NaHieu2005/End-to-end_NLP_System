from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rag_system.qa import DEFAULT_QA_MODEL, ExtractiveRAG
from rag_system.retrieval import DEFAULT_RERANKER_MODEL, Retriever


def build_rag(args: argparse.Namespace) -> ExtractiveRAG:
    retriever = Retriever.load(args.index)
    reranker_model = None if args.no_reranker else args.reranker_model
    return ExtractiveRAG(
        retriever,
        qa_model=args.qa_model,
        top_k=args.top_k,
        reranker_model=reranker_model,
        rerank_top_k=args.rerank_top_k,
    )


def print_sources(rag: ExtractiveRAG, question: str, top_n: int) -> None:
    retrieved = rag.retriever.retrieve(question, top_k=rag.top_k)
    if rag.reranker:
        retrieved = rag.reranker.rerank(question, retrieved, top_k=rag.rerank_top_k)
    print("\nNguồn liên quan:")
    for idx, (chunk, score) in enumerate(retrieved[:top_n], 1):
        preview = " ".join(chunk.text.split()[:35])
        print(f"{idx}. {chunk.source} | score={score:.4f}")
        print(f"   {preview}...")


def answer_once(rag: ExtractiveRAG, question: str, show_sources: bool, source_top_n: int) -> None:
    answer = rag.answer(question)
    print(f"\nTrả lời: {answer}")
    if show_sources:
        print_sources(rag, question, source_top_n)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="data/processed/index.pkl")
    parser.add_argument("--qa-model", default=DEFAULT_QA_MODEL)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--reranker-model", default=DEFAULT_RERANKER_MODEL)
    parser.add_argument("--rerank-top-k", type=int, default=4)
    parser.add_argument("--no-reranker", action="store_true")
    parser.add_argument("--question", help="Ask one question and exit.")
    parser.add_argument("--show-sources", action="store_true")
    parser.add_argument("--source-top-n", type=int, default=3)
    args = parser.parse_args()

    print("Đang load RAG model/index. Lần đầu có thể mất vài phút...")
    rag = build_rag(args)

    if args.question:
        answer_once(rag, args.question, args.show_sources, args.source_top_n)
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
        answer_once(rag, question, args.show_sources, args.source_top_n)
        print()


if __name__ == "__main__":
    main()
