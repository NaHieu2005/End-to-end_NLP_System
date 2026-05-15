from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rag_system.io_utils import read_lines, write_lines
from rag_system.qa import ExtractiveRAG
from rag_system.retrieval import Retriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="data/test/questions.txt")
    parser.add_argument("--index", default="data/processed/index.pkl")
    parser.add_argument("--out", default="system_outputs/system_output_1.txt")
    parser.add_argument("--qa-model", default="deepset/xlm-roberta-base-squad2")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    retriever = Retriever.load(args.index)
    rag = ExtractiveRAG(retriever, qa_model=args.qa_model, top_k=args.top_k)
    answers = [rag.answer(question) for question in read_lines(args.questions)]
    write_lines(args.out, answers)
    print(f"Wrote {len(answers)} answers to {args.out}")


if __name__ == "__main__":
    main()
