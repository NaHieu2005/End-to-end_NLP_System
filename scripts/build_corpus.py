from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix in {".html", ".htm"}:
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(" ")
    if suffix == ".pdf":
        if PdfReader is None:
            return ""
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return ""


def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    words = clean_text(text).split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        next_start = end - overlap
        start = next_start if next_start > start else end
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--out", default="data/processed/corpus.jsonl")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, str]] = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        text = read_document(path)
        for idx, chunk in enumerate(chunk_text(text)):
            records.append({"doc_id": f"{path.stem}-{idx}", "source": str(path), "text": chunk})

    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} chunks to {output}")


if __name__ == "__main__":
    main()
