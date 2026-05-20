from __future__ import annotations

import argparse
import html
import json
import random
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


RSS_FEEDS = {
    "giao_duc": "https://vnexpress.net/rss/giao-duc.rss",
    "khoa_hoc": "https://vnexpress.net/rss/khoa-hoc.rss",
    "so_hoa": "https://vnexpress.net/rss/so-hoa.rss",
}


def fetch(url: str, timeout: int = 30) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 news-rag-dataset-builder/1.0",
            "Accept": "text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.5",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_rss_items(feed_name: str, url: str) -> list[dict[str, str]]:
    root = ET.fromstring(fetch(url))
    items = []
    for item in root.findall("./channel/item"):
        title = clean_text(item.findtext("title") or "")
        link = clean_text(item.findtext("link") or "")
        published = clean_text(item.findtext("pubDate") or "")
        if title and link:
            items.append({"feed": feed_name, "title": title, "url": link, "published": published})
    return items


def extract_article(item: dict[str, str]) -> dict[str, str] | None:
    soup = BeautifulSoup(fetch(item["url"]), "html.parser")
    title_node = soup.select_one("h1.title-detail") or soup.select_one("h1")
    description_node = soup.select_one("p.description")
    date_node = soup.select_one("span.date")
    paragraphs = [
        clean_text(p.get_text(" "))
        for p in soup.select("p.Normal, article p")
        if len(clean_text(p.get_text(" ")).split()) >= 8
    ]
    title = clean_text(title_node.get_text(" ")) if title_node else item["title"]
    description = clean_text(description_node.get_text(" ")) if description_node else ""
    published = clean_text(date_node.get_text(" ")) if date_node else item["published"]
    body = clean_text(" ".join(paragraphs))
    if len(body.split()) < 120:
        return None
    return {
        "source": "VnExpress",
        "feed": item["feed"],
        "url": item["url"],
        "title": title,
        "published": published,
        "description": description,
        "body": body,
    }


def article_context(article: dict[str, str], index: int | None = None) -> str:
    domain = urlparse(article["url"]).netloc
    return clean_text(
        "\n".join(
            [
                f"Nguồn: {article['source']}",
                f"Chuyên mục: {article['feed']}",
                f"Tên miền: {domain}",
                f"URL: {article['url']}",
                f"Ngày đăng: {article['published']}",
                f"Tiêu đề: {article['title']}",
                f"Tóm tắt: {article['description']}",
                f"Nội dung: {article['body']}",
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
        if 5 <= len(sentence.split()) <= 80
    ]


def first_words(text: str, count: int) -> str:
    words = text.split()
    return " ".join(words[:count]).strip()


def make_qa(article: dict[str, str], index: int) -> list[dict]:
    context = article_context(article, index)
    domain = urlparse(article["url"]).netloc
    sentences = body_sentences(article["body"])
    title = article["title"]
    candidates = [
        (f"Bài viết \"{title}\" được đăng trên nguồn nào?", article["source"]),
        (f"Nguồn đăng bài \"{title}\" là gì?", article["source"]),
        (f"Bài viết \"{title}\" thuộc chuyên mục nào?", article["feed"]),
        (f"Chuyên mục của bài viết \"{title}\" là gì?", article["feed"]),
        (f"Bài viết \"{title}\" nằm trên tên miền nào?", domain),
        (f"URL của bài viết \"{title}\" là gì?", article["url"]),
    ]
    if article["published"]:
        candidates.append((f"Bài viết \"{title}\" được đăng ngày nào?", article["published"]))
        candidates.append((f"Ngày đăng của bài viết \"{title}\" là gì?", article["published"]))
    if article["description"]:
        candidates.append((f"Bài viết \"{title}\" được tóm tắt như thế nào?", article["description"]))
        candidates.append((f"Nội dung chính của bài viết \"{title}\" là gì?", article["description"]))
    if sentences:
        candidates.append((f"Câu mở đầu của bài viết \"{title}\" là gì?", sentences[0]))
        candidates.append((f"Bài viết \"{title}\" mở đầu bằng thông tin nào?", sentences[0]))
    if len(sentences) > 1:
        candidates.append((f"Thông tin thứ hai trong bài viết \"{title}\" là gì?", sentences[1]))
    if len(sentences) > 2:
        candidates.append((f"Thông tin thứ ba trong bài viết \"{title}\" là gì?", sentences[2]))
    if len(sentences) > 3:
        candidates.append((f"Bài viết \"{title}\" kết thúc bằng thông tin nào?", sentences[-1]))
    opening_words = first_words(article["body"], 12)
    if opening_words:
        candidates.append((f"Phần nội dung của bài viết \"{title}\" bắt đầu bằng những từ nào?", opening_words))

    qas = []
    seen_pairs: set[tuple[str, str]] = set()
    for qa_idx, (question, answer) in enumerate(candidates, 1):
        if (question, answer) in seen_pairs:
            continue
        seen_pairs.add((question, answer))
        answer_start = context.find(answer)
        if answer_start == -1:
            continue
        qas.append(
            {
                "id": f"news-{index:04d}-{qa_idx:02d}",
                "title": article["title"],
                "context": context,
                "question": question,
                "answers": {"text": [answer], "answer_start": [answer_start]},
            }
        )
    return qas


def split_records(records: list[dict], seed: int, train_ratio: float) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    shuffled = records[:]
    rng.shuffle(shuffled)
    train_end = int(len(shuffled) * train_ratio)
    return shuffled[:train_end], shuffled[train_end:]


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_qa_split(out_dir: Path, records: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    questions = [record["question"] for record in records]
    answers = [record["answers"]["text"][0] for record in records]
    (out_dir / "questions.txt").write_text("\n".join(questions) + "\n", encoding="utf-8")
    (out_dir / "reference_answers.txt").write_text("\n".join(answers) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/raw/news")
    parser.add_argument("--metadata-dir", default="data/news")
    parser.add_argument("--train-dir", default="data/train")
    parser.add_argument("--test-dir", default="data/test")
    parser.add_argument("--max-articles", type=int, default=90)
    parser.add_argument("--target-words", type=int, default=50000)
    parser.add_argument("--target-qa", type=int, default=1000)
    parser.add_argument("--train-ratio", type=float, default=0.85)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    metadata_dir = Path(args.metadata_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    rss_items: list[dict[str, str]] = []
    for feed_name, feed_url in RSS_FEEDS.items():
        rss_items.extend(parse_rss_items(feed_name, feed_url))

    seen_urls: set[str] = set()
    articles: list[dict[str, str]] = []
    for item in rss_items:
        if item["url"] in seen_urls or urlparse(item["url"]).netloc == "":
            continue
        seen_urls.add(item["url"])
        try:
            article = extract_article(item)
        except Exception as exc:  # noqa: BLE001 - keep crawl robust for public pages
            print(f"skip {item['url']}: {exc}")
            continue
        if article:
            articles.append(article)
            print(f"saved {len(articles)}: {item['url']}")
        if len(articles) >= args.max_articles:
            break
        time.sleep(args.delay)

    article_jsonl = metadata_dir / "articles.jsonl"
    article_jsonl.write_text(
        "\n".join(json.dumps(article, ensure_ascii=False) for article in articles) + "\n",
        encoding="utf-8",
    )

    corpus_parts: list[str] = []
    word_count = 0
    for idx, article in enumerate(articles, 1):
        text = article_context(article, idx)
        words = text.split()
        remaining = args.target_words - word_count
        if remaining <= 0:
            break
        corpus_parts.append(" ".join(words[:remaining]))
        word_count += min(len(words), remaining)
    corpus = "\n\n".join(corpus_parts)
    (raw_dir / "corpus_long.txt").write_text(corpus + "\n", encoding="utf-8")

    qa_records: list[dict] = []
    for idx, article in enumerate(articles, 1):
        qa_records.extend(make_qa(article, idx))
    if len(qa_records) > args.target_qa:
        rng = random.Random(args.seed)
        rng.shuffle(qa_records)
        qa_records = qa_records[: args.target_qa]
    train, test = split_records(qa_records, args.seed, args.train_ratio)

    write_qa_split(Path(args.train_dir), train)
    write_qa_split(Path(args.test_dir), test)
    write_json(
        metadata_dir / "metadata.json",
        {
            "source": "VnExpress public RSS/article pages",
            "feeds": RSS_FEEDS,
            "articles": len(articles),
            "corpus_words": len(corpus.split()),
            "qa_examples": len(qa_records),
            "train_examples": len(train),
            "test_examples": len(test),
        },
    )

    print(f"Wrote {len(articles)} articles to {article_jsonl}")
    print(f"Wrote corpus with {len(corpus.split())} words")
    print(f"Wrote QA splits: train={len(train)}, test={len(test)}")


if __name__ == "__main__":
    main()
