from __future__ import annotations

import argparse
import html
import json
import random
import re
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


SEED_URLS = [
    "https://uet.vnu.edu.vn/",
    "https://uet.vnu.edu.vn/gioi-thieu/",
    "https://uet.vnu.edu.vn/dao-tao",
    "https://uet.vnu.edu.vn/tuyen-sinh/",
    "https://uet.vnu.edu.vn/co-cau-to-chuc/",
    "https://tuyensinh.uet.vnu.edu.vn/",
    "https://tuyensinh.uet.vnu.edu.vn/category/tin-tuyen-sinh/",
    "https://www.vnu.edu.vn/home/",
    "https://www.vnu.edu.vn/home/?C1707/N61/TRuoNG-daI-HoC-CoNG-NGHe-(VNU-UET).htm=",
    "https://vi.wikipedia.org/wiki/Tr%C6%B0%E1%BB%9Dng_%C4%90%E1%BA%A1i_h%E1%BB%8Dc_C%C3%B4ng_ngh%E1%BB%87,_%C4%90%E1%BA%A1i_h%E1%BB%8Dc_Qu%E1%BB%91c_gia_H%C3%A0_N%E1%BB%99i",
    "https://vi.wikipedia.org/wiki/%C4%90%E1%BA%A1i_h%E1%BB%8Dc_Qu%E1%BB%91c_gia_H%C3%A0_N%E1%BB%99i",
    "https://en.wikipedia.org/wiki/VNU_University_of_Engineering_and_Technology",
    "https://en.wikipedia.org/wiki/Vietnam_National_University,_Hanoi",
]

NEWS_URLS = [
    "https://vnexpress.net/khoa-cong-nghe-thong-tin-truong-dai-hoc-cong-nghe-nhan-bang-khen-4965071.html",
    "https://vnexpress.net/nhung-diem-nhan-cua-chuong-trinh-a-i-thuc-chien-4986997.html",
    "https://vietnamnet.vn/truong-dh-cong-nghe-dhqghn-them-2-to-hop-xet-tuyen-moi-nam-2025-co-mon-tin-2413655.html",
    "https://vietnam.vn/en/nu-sinh-tro-thanh-thu-khoa-tot-nghiep-loai-xuat-sac-truong-cong-nghe",
]

ALLOWED_DOMAINS = {
    "uet.vnu.edu.vn",
    "www.uet.vnu.edu.vn",
    "uet.edu.vn",
    "tuyensinh.uet.vnu.edu.vn",
    "www.fit.uet.vnu.edu.vn",
    "fit.uet.vnu.edu.vn",
    "www.vnu.edu.vn",
    "vnu.edu.vn",
    "vnexpress.net",
    "vietnamnet.vn",
    "vietnam.vn",
    "vi.wikipedia.org",
    "en.wikipedia.org",
}

OFFICIAL_DOMAINS = {
    "uet.vnu.edu.vn",
    "www.uet.vnu.edu.vn",
    "uet.edu.vn",
    "tuyensinh.uet.vnu.edu.vn",
    "www.fit.uet.vnu.edu.vn",
    "fit.uet.vnu.edu.vn",
    "www.vnu.edu.vn",
    "vnu.edu.vn",
}

KEYWORDS = [
    "uet",
    "vnu",
    "dhqghn",
    "đhqghn",
    "đại học công nghệ",
    "dai-hoc-cong-nghe",
    "đại học quốc gia hà nội",
    "dai-hoc-quoc-gia-ha-noi",
    "tuyen-sinh",
    "tuyển sinh",
    "dao-tao",
    "đào tạo",
    "hoa-lac",
    "hòa lạc",
    "2024",
    "2025",
    "2026",
]

SKIP_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".zip",
    ".rar",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".pdf",
    ".ppt",
    ".pptx",
    ".mp4",
}

GENERIC_TITLES = {
    "tin tức",
    "homepage - vnu-uet",
}


@dataclass
class Document:
    source: str
    source_type: str
    title: str
    url: str
    domain: str
    published: str
    description: str
    text: str


def fetch(url: str, timeout: int = 8) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 uet-vnu-rag-dataset-builder/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_url(url: str) -> str:
    url = urldefrag(url)[0].strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return ""
    return url


def is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc.lower() not in ALLOWED_DOMAINS:
        return False
    suffix = Path(parsed.path).suffix.lower()
    return suffix not in SKIP_EXTENSIONS


def source_type_for(domain: str) -> str:
    if domain in OFFICIAL_DOMAINS:
        return "official"
    if "wikipedia.org" in domain:
        return "wiki"
    return "news"


def source_name_for(domain: str) -> str:
    if domain.endswith("wikipedia.org"):
        return "Wikipedia"
    if "vnexpress.net" in domain:
        return "VnExpress"
    if "vietnamnet.vn" in domain:
        return "VietNamNet"
    if "vietnam.vn" in domain:
        return "Vietnam.vn"
    if "vnu.edu.vn" in domain and "uet" not in domain:
        return "Đại học Quốc gia Hà Nội"
    return "Trường Đại học Công nghệ - ĐHQGHN"


def meta_content(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        node = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if node and node.get("content"):
            return clean_text(str(node["content"]))
    return ""


def page_date(soup: BeautifulSoup, text: str) -> str:
    published = meta_content(
        soup,
        "article:published_time",
        "article:modified_time",
        "date",
        "pubdate",
        "DC.date.issued",
    )
    if published:
        return published
    time_node = soup.find("time")
    if time_node:
        return clean_text(time_node.get("datetime") or time_node.get_text(" "))
    patterns = [
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        r"\b\d{1,2}-\d{1,2}-\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}\b",
        r"\bTháng\s+\d{1,2},\s+\d{4}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return ""


def extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links: list[str] = []
    for node in soup.find_all("a", href=True):
        url = normalize_url(urljoin(base_url, str(node["href"])))
        if url and is_allowed(url):
            links.append(url)
    return links


def link_priority(url: str) -> int:
    lower = url.lower()
    score = 0
    for keyword in KEYWORDS:
        if keyword in lower:
            score += 1
    if any(year in lower for year in {"2024", "2025", "2026"}):
        score += 2
    return score


def extract_document(url: str, content: bytes) -> tuple[Document | None, list[str]]:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "form", "iframe", "svg"]):
        tag.decompose()

    domain = urlparse(url).netloc.lower()
    title_node = soup.select_one("h1") or soup.select_one("title")
    title = clean_text(title_node.get_text(" ")) if title_node else meta_content(soup, "og:title")
    description = meta_content(soup, "og:description", "description")

    content_node = (
        soup.select_one(".content-detail")
        or soup.select_one(".maincontent")
        or soup.select_one(".entry-content")
        or soup.select_one(".post-content")
        or soup.select_one(".detail-content")
        or soup.select_one("#mw-content-text")
        or soup.select_one("article")
        or soup.select_one("main")
        or soup.body
        or soup
    )
    for tag in content_node(["header", "nav", "footer", "aside", "script", "style", "form"]):
        tag.decompose()
    text = clean_text(content_node.get_text(" "))
    if len(text.split()) < 80:
        return None, extract_links(soup, url)

    document = Document(
        source=source_name_for(domain),
        source_type=source_type_for(domain),
        title=title or url,
        url=url,
        domain=domain,
        published=page_date(soup, text),
        description=description,
        text=text,
    )
    return document, extract_links(soup, url)


def should_follow(url: str) -> bool:
    domain = urlparse(url).netloc.lower()
    if domain not in OFFICIAL_DOMAINS:
        return False
    return link_priority(url) > 0


def crawl(max_pages: int, delay: float) -> list[Document]:
    queue = deque(SEED_URLS + NEWS_URLS)
    seen: set[str] = set()
    documents: list[Document] = []

    while queue and len(documents) < max_pages:
        url = normalize_url(queue.popleft())
        if not url or url in seen or not is_allowed(url):
            continue
        seen.add(url)
        try:
            document, links = extract_document(url, fetch(url))
        except Exception as exc:  # noqa: BLE001 - keep data collection robust
            print(f"skip {url}: {exc}", flush=True)
            continue
        if document:
            if document.title.strip().lower() in GENERIC_TITLES:
                print(f"skip generic {document.url}: {document.title}", flush=True)
            else:
                documents.append(document)
                print(f"saved {len(documents)}: {document.url}", flush=True)

        prioritized = sorted((link for link in links if link not in seen and should_follow(link)), key=link_priority, reverse=True)
        for link in prioritized[:20]:
            queue.append(link)
        time.sleep(delay)
    return documents


def document_context(document: Document) -> str:
    summary = document.description or first_sentence(document.text)
    return clean_text(
        "\n".join(
            [
                f"Nguồn: {document.source}",
                f"Loại nguồn: {document.source_type}",
                f"Tên miền: {document.domain}",
                f"URL: {document.url}",
                f"Ngày đăng/cập nhật: {document.published}",
                f"Tiêu đề: {document.title}",
                f"Tóm tắt: {summary}",
                f"Nội dung: {document.text}",
            ]
        )
    )


def first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return parts[0].strip() if parts else text.strip()


def body_sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
        if 8 <= len(sentence.split()) <= 80
    ]


# QA generation removed to rely on manual curated QA.


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def load_documents(path: Path) -> list[Document]:
    documents: list[Document] = []
    if not path.exists():
        return documents
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            document = Document(**json.loads(line))
            if document.url.lower().endswith(".pdf") or document.text.startswith("%PDF"):
                continue
            documents.append(document)
    return documents


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/raw/uet_vnu")
    parser.add_argument("--metadata-dir", default="data/uet_vnu")
    parser.add_argument("--train-dir", default="data/train")
    parser.add_argument("--test-dir", default="data/test")
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--target-qa", type=int, default=1000)
    parser.add_argument("--train-ratio", type=float, default=0.85)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reuse-documents", action="store_true")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    metadata_dir = Path(args.metadata_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    articles_path = metadata_dir / "documents.jsonl"
    documents = load_documents(articles_path) if args.reuse_documents else []
    if documents:
        print(f"Reusing {len(documents)} documents from {articles_path}", flush=True)
    else:
        documents = crawl(args.max_pages, args.delay)
    documents = sorted(documents, key=lambda doc: (doc.source_type != "official", doc.domain, doc.title))

    contexts = [document_context(document) for document in documents]
    corpus = "\n\n".join(contexts)
    (raw_dir / "corpus_long.txt").write_text(corpus + "\n", encoding="utf-8")

    articles_path.write_text(
        "\n".join(json.dumps(document.__dict__, ensure_ascii=False) for document in documents) + "\n",
        encoding="utf-8",
    )

    print(f"Crawl completed. Please use write_manual_curated_qa.py to generate QA splits.", flush=True)

    source_counts: dict[str, int] = {}
    for document in documents:
        source_counts[document.source_type] = source_counts.get(document.source_type, 0) + 1
    write_json(
        metadata_dir / "metadata.json",
        {
            "source": "Public UET/VNU official pages, Wikipedia pages, and recent related news pages",
            "seed_urls": SEED_URLS,
            "news_urls": NEWS_URLS,
            "documents": len(documents),
            "source_type_counts": source_counts,
            "corpus_words": len(corpus.split()),
            "qa_examples": 0,
            "train_examples": 0,
            "test_examples": 0,
        },
    )

    print(f"Wrote {len(documents)} documents to {articles_path}", flush=True)
    print(f"Wrote corpus with {len(corpus.split())} words", flush=True)


if __name__ == "__main__":
    main()
