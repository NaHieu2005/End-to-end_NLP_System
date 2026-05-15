from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections import deque
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


ALLOWED_HOSTS = {
    "uet.vnu.edu.vn",
    "www.uet.vnu.edu.vn",
    "handbook.uet.vnu.edu.vn",
    "fit.uet.vnu.edu.vn",
    "www.fit.uet.vnu.edu.vn",
    "fat.uet.vnu.edu.vn",
}

DEFAULT_START_URLS = [
    "https://uet.vnu.edu.vn/",
    "https://uet.vnu.edu.vn/about/",
    "https://uet.vnu.edu.vn/khoa-cong-nghe-thong-tin/",
    "https://handbook.uet.vnu.edu.vn/",
    "https://www.fit.uet.vnu.edu.vn/",
    "https://fat.uet.vnu.edu.vn/",
]

SKIP_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".css",
    ".js",
    ".ico",
    ".zip",
    ".rar",
    ".7z",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
}


def normalize_url(url: str) -> str:
    clean, _fragment = urldefrag(url)
    parsed = urlparse(clean)
    if parsed.scheme not in {"http", "https"}:
        return ""
    path = re.sub(r"/{2,}", "/", parsed.path)
    quoted_path = quote(path, safe="/%")
    quoted_query = quote(parsed.query.strip(), safe="=&?/%")
    return parsed._replace(path=quoted_path, query=quoted_query).geturl()


def is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    suffix = Path(parsed.path.lower()).suffix
    if parsed.netloc.lower() not in ALLOWED_HOSTS:
        return False
    if suffix in SKIP_EXTENSIONS:
        return False
    if any(part in parsed.path.lower() for part in ("/wp-login", "/wp-admin", "/feed")):
        return False
    return True


def fetch(url: str, timeout: int = 20) -> tuple[bytes, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 UET-RAG-assignment-crawler/1.0",
            "Accept": "text/html,application/pdf,text/plain;q=0.9,*/*;q=0.5",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        return response.read(), content_type


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_html(content: bytes, url: str) -> tuple[str, list[str], str]:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "form"]):
        tag.decompose()

    title = clean_text(soup.title.get_text(" ")) if soup.title else ""
    text = clean_text(soup.get_text(" "))

    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        next_url = normalize_url(urljoin(url, anchor["href"]))
        if next_url and is_allowed(next_url):
            links.append(next_url)
    return title, sorted(set(links)), text


def extract_pdf(content: bytes, temp_path: Path) -> str:
    if PdfReader is None:
        return ""
    temp_path.write_bytes(content)
    reader = PdfReader(str(temp_path))
    return clean_text("\n".join(page.extract_text() or "" for page in reader.pages))


def safe_filename(url: str) -> str:
    parsed = urlparse(url)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", f"{parsed.netloc}{parsed.path}")[:90].strip("-")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{slug}-{digest}.txt"


def iter_start_urls(extra_urls: Iterable[str]) -> list[str]:
    urls = [normalize_url(url) for url in DEFAULT_START_URLS]
    urls.extend(normalize_url(url) for url in extra_urls)
    return [url for url in urls if url and is_allowed(url)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/raw/uet")
    parser.add_argument("--max-pages", type=int, default=250)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--start-url", action="append", default=[])
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.jsonl"
    temp_pdf = out_dir / "_tmp_download.pdf"

    queue = deque(iter_start_urls(args.start_url))
    seen: set[str] = set()
    saved = 0

    with manifest_path.open("w", encoding="utf-8") as manifest:
        while queue and len(seen) < args.max_pages:
            url = queue.popleft()
            if url in seen or not is_allowed(url):
                continue
            seen.add(url)

            try:
                content, content_type = fetch(url)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                print(f"skip {url}: {exc}", file=sys.stderr)
                continue

            parsed = urlparse(url)
            is_pdf = ".pdf" in parsed.path.lower() or "application/pdf" in content_type.lower()
            title = ""
            links: list[str] = []
            if is_pdf:
                text = extract_pdf(content, temp_pdf)
                title = Path(parsed.path).name
            else:
                title, links, text = extract_html(content, url)
                queue.extend(link for link in links if link not in seen)

            if len(text) < 200:
                continue

            file_path = out_dir / safe_filename(url)
            file_path.write_text(text, encoding="utf-8")
            manifest.write(
                json.dumps(
                    {
                        "url": url,
                        "title": title,
                        "path": str(file_path),
                        "content_type": content_type,
                        "characters": len(text),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            manifest.flush()
            saved += 1
            print(f"saved {saved}: {url}")
            time.sleep(args.delay)

    if temp_pdf.exists():
        temp_pdf.unlink()
    print(f"Saved {saved} documents to {out_dir}")


if __name__ == "__main__":
    main()
