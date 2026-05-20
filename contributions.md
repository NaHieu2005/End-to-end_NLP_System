# Contributions

## Data Collection And Processing

- NaHieu2005: collected public VnExpress RSS/article data from the `giao_duc`, `khoa_hoc`, and `so_hoa` feeds.
- NaHieu2005: cleaned article metadata and body text into `data/raw/news/corpus_long.txt`.
- NaHieu2005: implemented corpus chunking into `data/processed/corpus.jsonl`.

## Data Annotation

- NaHieu2005: generated and validated 1,000 article-grounded QA pairs from the collected corpus.
- NaHieu2005: split the QA data into 850 training/development examples and 150 test examples.
- NaHieu2005: checked that questions use public-document evidence and that test references are aligned with the article fields or body text.

## Modeling And Evaluation

- NaHieu2005: implemented dense retrieval, optional reranking, extractive QA, and evaluation scripts.
- NaHieu2005: ran the final test-set generation and reported exact match, token F1, and answer recall.
- NaHieu2005: prepared README, report source, repository structure, and final system output.
