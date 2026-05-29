from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


URLS = [
    "https://www.is.vnu.edu.vn/truong-quoc-te-thong-bao-thong-tin-du-kien-tuyen-sinh-dhcq-nam-2026/",
    "https://vju.vnu.edu.vn/ttts2026/",
    "https://tuyensinh.hus.vnu.edu.vn/dai-hoc",
    "https://ueb.edu.vn/Tin-Tuc/UEB/thong-tin-tuyen-sinh-dai-hoc-chinh-quy-nam-2026-cua-truong-dai-hoc-kinh-te-dhqghn/46202",
    "https://ueb.edu.vn/Tin-Tuc/UEB/thong-bao-thong-tin-tuyen-sinh-dai-hoc-nam-2026/45862",
    "https://ussh.vnu.edu.vn/vi/tuyen-sinh/tuyen-sinh-dai-hoc-chinh-quy/",
    "https://ussh.vnu.edu.vn/vi/news/dao-tao/thong-tin-tuyen-sinh-dh-nam-2026-cua-truong-dh-khxh-nv-thu-hut-su-quan-tam-lon-cua-hoc-sinh-23866.html",
    "https://ussh.vnu.edu.vn/vi/news/thong-bao/thong-bao-tuyen-sinh-thac-si-dot-1-nam-2026-24062.html",
    "https://ulis.vnu.edu.vn/tap-huan-chuyen-mon-cong-tac-tuyen-sinh-dai-hoc-chinh-quy-nam-2026/",
    "https://vnu.edu.vn/quy-che-tuyen-sinh-dai-hoc-chinh-quy-tai-dhqghn-post36586.html",
    "https://vnu.edu.vn/dhqghn-ban-hanh-quy-che-tuyen-sinh-dai-hoc-nam-2026-voi-nhieu-diem-doi-moi-post39567.html",
]


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


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 vnu-wide-rag-data/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5",
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read()


def source_name(domain: str) -> str:
    if "is.vnu.edu.vn" in domain:
        return "Trường Quốc tế - ĐHQGHN"
    if "vju.vnu.edu.vn" in domain:
        return "Trường Đại học Việt Nhật - ĐHQGHN"
    if "hus.vnu.edu.vn" in domain:
        return "Trường Đại học Khoa học Tự nhiên - ĐHQGHN"
    if "ueb.edu.vn" in domain:
        return "Trường Đại học Kinh tế - ĐHQGHN"
    if "ussh.vnu.edu.vn" in domain:
        return "Trường Đại học Khoa học Xã hội và Nhân văn - ĐHQGHN"
    if "ulis.vnu.edu.vn" in domain:
        return "Trường Đại học Ngoại ngữ - ĐHQGHN"
    return "Đại học Quốc gia Hà Nội"


def parse_document(url: str, raw: bytes) -> Document:
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript"]):
        tag.decompose()
    title = ""
    if soup.find("h1"):
        title = clean_text(soup.find("h1").get_text(" "))
    if not title and soup.title:
        title = clean_text(soup.title.get_text(" "))
    description = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        description = clean_text(meta["content"])
    text = clean_text(soup.get_text(" "))
    domain = urlparse(url).netloc.lower()
    return Document(
        source=source_name(domain),
        source_type="official",
        title=title,
        url=url,
        domain=domain,
        published="",
        description=description,
        text=text,
    )


def main() -> None:
    path = Path("data/uet_vnu/documents.jsonl")
    existing = []
    seen_urls = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            existing.append(item)
            seen_urls.add(item.get("url"))

    added = []
    for url in URLS:
        if url in seen_urls:
            continue
        try:
            doc = parse_document(url, fetch(url))
        except Exception as exc:
            print(f"skip {url}: {exc}")
            continue
        if len(doc.text.split()) < 80:
            print(f"skip short {url}")
            continue
        added.append(asdict(doc))
        print(f"added: {doc.title} | {url}")

    all_docs = existing + added
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(doc, ensure_ascii=False) for doc in all_docs) + "\n",
        encoding="utf-8",
    )
    print(f"documents={len(all_docs)} added={len(added)}")


if __name__ == "__main__":
    main()
