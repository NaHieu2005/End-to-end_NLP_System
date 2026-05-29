from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rag_system.io_utils import read_lines, write_lines
from rag_system.qa import DEFAULT_GENERATIVE_MODEL, DEFAULT_QA_MODEL, GenerativeRAG, ExtractiveRAG
from rag_system.retrieval import DEFAULT_RERANKER_MODEL, Retriever


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="data/test/questions.txt")
    parser.add_argument("--index", default="data/processed/index.pkl")
    parser.add_argument("--out", default="system_outputs/system_output_1.txt")
    parser.add_argument("--model", default=DEFAULT_GENERATIVE_MODEL,
                        help="Generative model name (default: Qwen2.5-7B-Instruct)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--reranker-model", default=DEFAULT_RERANKER_MODEL)
    parser.add_argument("--rerank-top-k", type=int, default=3)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--max-context-chars", type=int, default=3500)
    parser.add_argument("--no-reranker", action="store_true")
    parser.add_argument("--extractive", action="store_true",
                        help="Use extractive QA instead of generative")
    parser.add_argument("--qa-model", default=DEFAULT_QA_MODEL,
                        help="Extractive QA model (only used with --extractive)")
    args = parser.parse_args()

    retriever = Retriever.load(args.index)
    reranker_model = None if args.no_reranker else args.reranker_model

    if args.extractive:
        rag = ExtractiveRAG(
            retriever,
            qa_model=args.qa_model,
            top_k=args.top_k,
            reranker_model=reranker_model,
            rerank_top_k=args.rerank_top_k,
        )
    else:
        rag = GenerativeRAG(
            retriever,
            model_name=args.model,
            top_k=args.top_k,
            reranker_model=reranker_model,
            rerank_top_k=args.rerank_top_k,
            max_new_tokens=args.max_new_tokens,
            max_context_chars=args.max_context_chars,
        )

    questions = read_lines(args.questions)
    answers = []
    for i, question in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {question[:60]}...")
        answer = rag.answer(question)
        answers.append(answer)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(answers) + "\n")
    print(f"\nWrote {len(answers)} answers to {args.out}")


if __name__ == "__main__":
    main()
