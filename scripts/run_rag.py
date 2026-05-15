from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rag_system.io_utils import read_lines, write_lines
from rag_system.qa import DEFAULT_QA_MODEL, ExtractiveRAG
from rag_system.retrieval import DEFAULT_RERANKER_MODEL, Retriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="data/test/questions.txt")
    parser.add_argument("--index", default="data/processed/index.pkl")
    parser.add_argument("--out", default="system_outputs/system_output_1.txt")
    parser.add_argument("--qa-model", default=DEFAULT_QA_MODEL)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--reranker-model", default=DEFAULT_RERANKER_MODEL)
    parser.add_argument("--rerank-top-k", type=int, default=4)
    parser.add_argument("--no-reranker", action="store_true")
    args = parser.parse_args()

    retriever = Retriever.load(args.index)
    reranker_model = None if args.no_reranker else args.reranker_model
    rag = ExtractiveRAG(
        retriever,
        qa_model=args.qa_model,
        top_k=args.top_k,
        reranker_model=reranker_model,
        rerank_top_k=args.rerank_top_k,
    )
    answers = [rag.answer(question) for question in read_lines(args.questions)]
    write_lines(args.out, answers)
    print(f"Wrote {len(answers)} answers to {args.out}")


if __name__ == "__main__":
    main()
