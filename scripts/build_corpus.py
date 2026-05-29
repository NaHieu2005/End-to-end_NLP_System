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
    """Remove wiki markup, URLs, emails, contact info and other noise."""
    text = re.sub(r"\{\{.*?\}\}", " ", text)
    text = re.sub(r"\[\s*\d+\s*\]", " ", text)
    text = re.sub(r"\^\s*\"[^\"]+\"\s*\.?", " ", text)
    text = re.sub(r"\bsửa\s*\|\s*sửa mã nguồn\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bQuản lý CS1:[^.]+\.?", " ", text)
    text = re.sub(r"\bChú thích web\b", " ", text)
    text = re.sub(r"\|\s*\w+\s*=", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", " ", text)
    text = re.sub(r"[\u2191\u2022\u25cf\u25aa\u25c6\u25aa\u25b8\u25b6\u25ba\u25b7\u2713\u2714\u2605\u2606]", " ", text)
    # Remove zero-width characters and invisible formatting characters
    text = re.sub(r"[\u200B-\u200D\uFEFF\u200E\u200F]", "", text)
    # Remove control characters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    
    # Fix corrupted text (mojibake)
    fixes = {
        "Công nghềE": "Công nghệ ",
        "công nghềE": "công nghệ ",
        "tềEhợp": "tổ hợp",
        "trí tuềE": "trí tuệ ",
        "tuềE": "tuệ ",
        "vềE": "vị ",
        "viềE thông": "viễn thông",
        "chủ đềE": "chủ đề ",
        "bềEchềEtiêu": "bộ chỉ tiêu",
        "nāE": "năm ",
        "NāE": "Năm ",
        "mềEcổng": "mở cổng",
        "ĐāEG KÁE": "ĐĂNG KÝ",
        "đăng ký": "đăng ký",
        "hềEsơ": "hồ sơ",
        "chứng chềE": "chứng chỉ ",
        "đềE": "để ",
        "tềEchức": "tổ chức",
        "sềE": "số ",
        "Đại học Công nghềE": "Đại học Công nghệ",
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
        
    # Remove contact info blocks
    for marker in ["Thông tin liên hệ:", "Thông tin liên hệ", "Liên hệ:"]:
        if marker in text:
            text = text.split(marker, 1)[0]
    text = re.sub(
        r"\b(Điện thoại|E-mail|Email|Website|Facebook|Form)\s*:\s*[^.]+\.?",
        " ", text, flags=re.IGNORECASE,
    )
    # Remove metadata labels that might be in the raw corpus
    text = re.sub(r"^(Nguồn|Loại nguồn|Tên miền|URL|Ngày đăng/cập nhật|Ngày đăng):\s*.*$",
                  "", text, flags=re.MULTILINE)
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


def extract_title_and_content(text: str) -> tuple[str, str]:
    """Extract title and content from a structured document block."""
    title_match = re.search(r"Tiêu đề:\s*(.+?)(?:\n|Tóm tắt:|Nội dung:)", text)
    content_match = re.search(r"Nội dung:\s*(.+)", text, re.DOTALL)
    
    title = title_match.group(1).strip() if title_match else ""
    content = content_match.group(1).strip() if content_match else text.strip()
    return title, content


def split_structured_documents(text: str) -> list[str]:
    """Split text into individual documents based on double-newline + Nguồn: pattern,
    or by title lines for the clean format."""
    # Try splitting by the old metadata format
    parts = [part.strip() for part in re.split(r"\n\s*\n(?=Nguồn:|[^\n]{5,}\n[^\n]{20,})", text) if part.strip()]
    if len(parts) > 1:
        return parts
    # Try splitting by double newlines for clean title+content format
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip() and len(part.strip()) > 50]
    return parts or [text]


def is_noisy_document(text: str) -> bool:
    lower = text.lower()
    noisy_markers = [
        "vnpost ensures uninterrupted public services",
        "temperatures exceeding 40",
        "follow vietnam.vn on",
        "top interests newest",
    ]
    return any(marker in lower for marker in noisy_markers)


def chunk_text(text: str, size: int = 800, overlap: int = 150) -> list[str]:
    words = clean_text(text).split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        if chunk and len(chunk.split()) >= 20:  # Skip very short chunks
            chunks.append(chunk)
        next_start = end - overlap
        start = next_start if next_start > start else end
    return chunks


def structured_chunks(text: str) -> list[str]:
    """Create clean chunks: title + content only, no metadata."""
    title, content = extract_title_and_content(text)
    if not content or len(content.split()) < 20:
        # Fallback: just chunk the whole text
        cleaned = clean_text(text)
        if len(cleaned.split()) < 20:
            return []
        return chunk_text(cleaned)
    
    prefix = f"{title}. " if title else ""
    return [clean_text(f"{prefix}{chunk}") for chunk in chunk_text(content)]


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
        for doc_idx, document_text in enumerate(split_structured_documents(text)):
            if is_noisy_document(document_text):
                continue
            for idx, chunk in enumerate(structured_chunks(document_text)):
                if chunk.strip():
                    records.append({
                        "doc_id": f"{path.stem}-{doc_idx}-{idx}",
                        "source": str(path),
                        "text": chunk,
                    })

    with output.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} chunks to {output}")


if __name__ == "__main__":
    main()
