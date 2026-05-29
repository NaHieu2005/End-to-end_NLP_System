from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rag_system.qa import DEFAULT_GENERATIVE_MODEL, DEFAULT_QA_MODEL, GenerativeRAG, ExtractiveRAG
from rag_system.retrieval import DEFAULT_RERANKER_MODEL, Retriever


def build_rag(args: argparse.Namespace):
    retriever = Retriever.load(args.index)
    reranker_model = None if args.no_reranker else args.reranker_model
    if args.extractive:
        return ExtractiveRAG(
            retriever,
            qa_model=args.qa_model,
            top_k=args.top_k,
            reranker_model=reranker_model,
            rerank_top_k=args.rerank_top_k,
        )
    return GenerativeRAG(
        retriever,
        model_name=args.model,
        top_k=args.top_k,
        reranker_model=reranker_model,
        rerank_top_k=args.rerank_top_k,
        max_new_tokens=args.max_new_tokens,
        max_context_chars=args.max_context_chars,
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="data/processed/index.pkl")
    parser.add_argument("--model", default=DEFAULT_GENERATIVE_MODEL)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--reranker-model", default=DEFAULT_RERANKER_MODEL)
    parser.add_argument("--rerank-top-k", type=int, default=3)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--max-context-chars", type=int, default=3500)
    parser.add_argument("--no-reranker", action="store_true")
    parser.add_argument("--extractive", action="store_true")
    parser.add_argument("--qa-model", default=DEFAULT_QA_MODEL)
    parser.add_argument("--question", help="Ask one question and exit.")
    args = parser.parse_args()

    print("Đang load RAG model/index...")
    rag = build_rag(args)

    if args.question:
        answer = rag.answer(args.question)
        print(f"\nTrả lời: {answer}")
        return

    print("Nhập câu hỏi. Gõ 'exit' hoặc 'q' để thoát.\n")
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
        answer = rag.answer(question)
        print(f"Trả lời: {answer}\n")


if __name__ == "__main__":
    main()
