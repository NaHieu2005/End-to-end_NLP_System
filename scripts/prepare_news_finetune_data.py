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
            "User-Agent": "Mozilla/5.0 news-finetune-dataset-builder/1.0",
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


def article_context(article: dict[str, str]) -> str:
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
    context = article_context(article)
    domain = urlparse(article["url"]).netloc
    sentences = body_sentences(article["body"])
    candidates = [
        (f"Bài báo số {index} được đăng trên nguồn nào?", article["source"]),
        (f"Nguồn của bài báo số {index} là gì?", article["source"]),
        (f"Bài báo số {index} thuộc chuyên mục nào?", article["feed"]),
        (f"Chuyên mục của bài báo số {index} là gì?", article["feed"]),
        (f"Bài báo số {index} nằm trên tên miền nào?", domain),
        (f"URL của bài báo số {index} là gì?", article["url"]),
        (f"Tiêu đề của bài báo số {index} là gì?", article["title"]),
    ]
    if article["published"]:
        candidates.append((f"Bài báo số {index} được đăng ngày nào?", article["published"]))
        candidates.append((f"Ngày đăng của bài báo số {index} là gì?", article["published"]))
    if article["description"]:
        candidates.append((f"Tóm tắt của bài báo số {index} là gì?", article["description"]))
        candidates.append((f"Bài báo số {index} được tóm tắt như thế nào?", article["description"]))
    if sentences:
        candidates.append((f"Câu mở đầu phần nội dung của bài báo số {index} là gì?", sentences[0]))
        candidates.append((f"Câu đầu tiên trong nội dung bài báo số {index} là gì?", sentences[0]))
    if len(sentences) > 1:
        candidates.append((f"Câu thứ hai trong nội dung bài báo số {index} là gì?", sentences[1]))
    if len(sentences) > 2:
        candidates.append((f"Câu thứ ba trong nội dung bài báo số {index} là gì?", sentences[2]))
    if len(sentences) > 3:
        candidates.append((f"Câu cuối cùng trong nội dung bài báo số {index} là gì?", sentences[-1]))
    opening_words = first_words(article["body"], 12)
    if opening_words:
        candidates.append((f"12 từ đầu tiên trong nội dung bài báo số {index} là gì?", opening_words))

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


def to_squad(records: list[dict], title: str) -> dict:
    return {
        "version": "news-squad-1.0",
        "data": [
            {
                "title": title,
                "paragraphs": [
                    {
                        "context": record["context"],
                        "qas": [
                            {
                                "id": record["id"],
                                "question": record["question"],
                                "answers": [
                                    {
                                        "text": record["answers"]["text"][0],
                                        "answer_start": record["answers"]["answer_start"][0],
                                    }
                                ],
                                "is_impossible": False,
                            }
                        ],
                    }
                    for record in records
                ],
            }
        ],
    }


def split_records(records: list[dict], seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    rng = random.Random(seed)
    shuffled = records[:]
    rng.shuffle(shuffled)
    train_end = int(len(shuffled) * 0.7)
    valid_end = int(len(shuffled) * 0.85)
    return shuffled[:train_end], shuffled[train_end:valid_end], shuffled[valid_end:]


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/news_finetune")
    parser.add_argument("--max-articles", type=int, default=90)
    parser.add_argument("--target-words", type=int, default=50000)
    parser.add_argument("--target-qa", type=int, default=1000)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

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

    article_jsonl = raw_dir / "articles.jsonl"
    article_jsonl.write_text(
        "\n".join(json.dumps(article, ensure_ascii=False) for article in articles) + "\n",
        encoding="utf-8",
    )

    corpus_parts: list[str] = []
    word_count = 0
    for article in articles:
        text = article_context(article)
        words = text.split()
        remaining = args.target_words - word_count
        if remaining <= 0:
            break
        corpus_parts.append(" ".join(words[:remaining]))
        word_count += min(len(words), remaining)
    corpus = "\n\n".join(corpus_parts)
    (out_dir / "corpus_long.txt").write_text(corpus + "\n", encoding="utf-8")

    qa_records: list[dict] = []
    for idx, article in enumerate(articles, 1):
        qa_records.extend(make_qa(article, idx))
    if len(qa_records) > args.target_qa:
        rng = random.Random(args.seed)
        rng.shuffle(qa_records)
        qa_records = qa_records[: args.target_qa]
    train, valid, test = split_records(qa_records, args.seed)

    write_json(out_dir / "qa_squad_train.json", to_squad(train, "Vietnamese news train"))
    write_json(out_dir / "qa_squad_valid.json", to_squad(valid, "Vietnamese news validation"))
    write_json(out_dir / "qa_squad_test.json", to_squad(test, "Vietnamese news test"))
    write_json(
        out_dir / "metadata.json",
        {
            "source": "VnExpress public RSS/article pages",
            "feeds": RSS_FEEDS,
            "articles": len(articles),
            "corpus_words": len(corpus.split()),
            "qa_examples": len(qa_records),
            "train_examples": len(train),
            "valid_examples": len(valid),
            "test_examples": len(test),
        },
    )

    print(f"Wrote {len(articles)} articles to {article_jsonl}")
    print(f"Wrote corpus with {len(corpus.split())} words")
    print(f"Wrote QA splits: train={len(train)}, valid={len(valid)}, test={len(test)}")


if __name__ == "__main__":
    main()
