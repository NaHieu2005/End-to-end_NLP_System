# End-to-end NLP System

Retrieval Augmented Generation (RAG) project for factual question answering over a public Vietnamese news corpus.

## Submission Files

- `github_url.txt`: repository URL.
- `contributions.md`: contribution summary.
- `reports/report.md`: project report source.
- `data/raw/news/corpus_long.txt`: raw public knowledge resource.
- `data/train/questions.txt` and `data/train/reference_answers.txt`: training/development QA set.
- `data/test/questions.txt` and `data/test/reference_answers.txt`: annotated test QA set.
- `system_outputs/system_output_1.txt`: generated answers for the test questions.

## Data

The current dataset was built from public VnExpress RSS/article pages:

- 90 articles from `giao_duc`, `khoa_hoc`, and `so_hoa`.
- 76,213 words in the raw corpus.
- 1,000 QA examples in total.
- 850 train/development examples and 150 test examples.

Questions are direct article-title questions, for example:

```text
Chuyen muc cua bai viet "Thay tro thi hai xoai, thu hoach nua tan sau 20 phut" la gi?
```

The raw corpus stores article metadata and body text in a plain text format, and `data/processed/corpus.jsonl` stores the cleaned chunks used by the retriever.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The implementation uses open-source Hugging Face models:

- embedding: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- optional reranker: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- Vietnamese extractive QA reader: `letrunglinh/qa_pnc`

Model files are cached under `.hf_cache/` in this project directory.

## Rebuild

Generate the news data again:

```bash
python scripts/prepare_news_rag_data.py --max-articles 90 --target-qa 1000
```

Build the cleaned corpus and retrieval index:

```bash
python scripts/build_corpus.py --raw-dir data/raw/news --out data/processed/corpus.jsonl
python scripts/build_index.py --corpus data/processed/corpus.jsonl --out data/processed/index.pkl
```

`data/processed/index.pkl` is ignored by git because it is a generated binary file.

## Run

Generate answers for the test set:

```bash
python scripts/run_rag.py ^
  --questions data/test/questions.txt ^
  --index data/processed/index.pkl ^
  --out system_outputs/system_output_1.txt ^
  --no-reranker
```

Interactive single-question mode:

```bash
python scripts/chat_rag.py --question "Chuyen muc cua bai viet \"Thay tro thi hai xoai, thu hoach nua tan sau 20 phut\" la gi?" --no-reranker
```

## Evaluate

```bash
python scripts/evaluate.py ^
  --predictions system_outputs/system_output_1.txt ^
  --references data/test/reference_answers.txt
```

Latest local evaluation on the annotated test set:

```text
exact_match: 0.9067
f1: 0.9332
answer_recall: 0.9133
```
