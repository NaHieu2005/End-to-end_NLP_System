from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rag_system.retrieval import DEFAULT_EMBEDDING_MODEL, DocumentChunk, build_retriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/processed/corpus.jsonl")
    parser.add_argument("--out", default="data/processed/index.pkl")
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    args = parser.parse_args()

    chunks: list[DocumentChunk] = []
    with Path(args.corpus).open("r", encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            chunks.append(DocumentChunk(**row))

    if not chunks:
        raise SystemExit("No chunks found. Add public documents to data/raw and run build_corpus.py first.")

    retriever = build_retriever(chunks, model_name=args.embedding_model)
    retriever.save(args.out)
    print(f"Wrote retrieval index with {len(chunks)} chunks to {args.out}")


if __name__ == "__main__":
    main()
