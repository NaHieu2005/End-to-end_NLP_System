from __future__ import annotations

import argparse
from pathlib import Path

from rag_system.io_utils import read_lines
from rag_system.qa import ExtractiveRAG
from rag_system.retrieval import Retriever


def answer_with_retrieval_only(retriever: Retriever, question: str, top_k: int) -> str:
    retrieved = retriever.retrieve(question, top_k=top_k)
    context = "\n\n".join(chunk.text for chunk, _score in retrieved)
    return ExtractiveRAG._best_sentence(question, context)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run retrieval-only baseline for QA.")
    parser.add_argument("--questions", default="data/test/questions.txt")
    parser.add_argument("--index", default="data/processed/index.pkl")
    parser.add_argument("--out", default="system_outputs/system_output_2.txt")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    questions = read_lines(Path(args.questions))
    retriever = Retriever.load(args.index)

    outputs = []
    for i, question in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {question[:60]}...")
        outputs.append(answer_with_retrieval_only(retriever, question, top_k=args.top_k))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(outputs) + "\n", encoding="utf-8")
    print(f"Wrote {len(outputs)} answers to {out_path}")


if __name__ == "__main__":
    main()
