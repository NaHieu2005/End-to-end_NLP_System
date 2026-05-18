# News Fine-tuning Dataset

This folder is ready to upload as a Kaggle Dataset.

Contents:

- `corpus_long.txt`: Vietnamese news corpus with 50,000 words.
- `raw/articles.jsonl`: crawled public article metadata and cleaned article text.
- `qa_squad_train.json`: SQuAD-style training split.
- `qa_squad_valid.json`: SQuAD-style validation split.
- `qa_squad_test.json`: SQuAD-style held-out test split.
- `metadata.json`: source feeds and split counts.

Current split:

- Articles: 90
- QA examples: 535
- Train: 374
- Validation: 80
- Test: 81

Source: public VnExpress RSS feeds and article pages from education, science, and technology categories.
