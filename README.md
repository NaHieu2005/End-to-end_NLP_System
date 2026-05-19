# End-to-end NLP System

Retrieval Augmented Generation (RAG) project for factual question answering.

The system follows the assignment format:

- input questions: `data/test/questions.txt`
- reference answers: `data/test/reference_answers.txt`
- generated answers: `system_outputs/system_output_1.txt`
- train data: `data/train/questions.txt` and `data/train/reference_answers.txt`

## Project Structure

```text
.
├── data/
│   ├── raw/                  # Public source documents: HTML/PDF/TXT
│   ├── processed/            # Cleaned text chunks and retrieval index
│   ├── train/
│   │   ├── questions.txt
│   │   └── reference_answers.txt
│   └── test/
│       ├── questions.txt
│       └── reference_answers.txt
├── scripts/
│   ├── build_corpus.py       # Clean raw documents into chunks
│   ├── build_index.py        # Embed chunks and build retrieval index
│   ├── run_rag.py            # Generate answers for questions
│   └── evaluate.py           # Exact match / F1 / answer recall
├── src/
│   └── rag_system/
│       ├── __init__.py
│       ├── evaluation.py
│       ├── io_utils.py
│       ├── qa.py
│       └── retrieval.py
├── system_outputs/
│   └── system_output_1.txt
├── contributions.md
├── github_url.txt
└── reports/
    └── report.md
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The default implementation uses open-source Hugging Face accessible models:

- embedding: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- reranker: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- extractive Vietnamese QA reader: `letrunglinh/qa_pnc`

You can change these with command-line flags.

Model files are cached under `.hf_cache/` in this project directory on drive F, not under the default user cache on drive C.

## Prepare Data

Place public source documents in `data/raw/`. Supported extensions:

- `.txt`
- `.html`, `.htm`
- `.pdf`

Build the cleaned corpus and retrieval index:

```bash
python scripts/build_corpus.py --raw-dir data/raw --out data/processed/corpus.jsonl
python scripts/build_index.py --corpus data/processed/corpus.jsonl --out data/processed/index.pkl
```

## Run RAG

```bash
python scripts/run_rag.py ^
  --questions data/test/questions.txt ^
  --index data/processed/index.pkl ^
  --out system_outputs/system_output_1.txt
```

Each output line contains one concise answer for the corresponding input question.

## Ask Interactively

Load the RAG system once, then type questions in the terminal:

```bash
python scripts/chat_rag.py
```

Ask one question and exit:

```bash
python scripts/chat_rag.py --question "UET tuyển sinh đại học chính quy năm 2026 theo mã trường nào?"
```

Show retrieved sources:

```bash
python scripts/chat_rag.py --show-sources
```

If your machine runs out of memory, disable reranking:

```bash
python scripts/run_rag.py ^
  --questions data/test/questions.txt ^
  --index data/processed/index.pkl ^
  --out system_outputs/system_output_1.txt ^
  --no-reranker
```

## Evaluate

```bash
python scripts/evaluate.py ^
  --predictions system_outputs/system_output_1.txt ^
  --references data/test/reference_answers.txt
```

Metrics reported:

- exact match
- token F1
- answer recall

## Fine-tuning on Kaggle

The repo includes a separate extractive QA fine-tuning dataset built from public Vietnamese news articles:

- dataset folder: `data/news_finetune/`
- upload zip: `data/news_finetune.zip`
- Kaggle training code: `kaggle/train_qa.py`
- Kaggle instructions: `kaggle/README.md`

Dataset summary:

- 90 public news articles
- 50,000-word long corpus
- 535 SQuAD-style QA examples
- train/validation/test split: 374 / 80 / 81

Generate the dataset again:

```bash
python scripts/prepare_news_finetune_data.py --out-dir data/news_finetune --max-articles 90 --target-words 50000
```

## Submission Checklist

- `report.pdf` or report source in `reports/`
- `github_url.txt`
- `contributions.md`
- `data/train/questions.txt`
- `data/train/reference_answers.txt`
- `data/test/questions.txt`
- `data/test/reference_answers.txt`
- `system_outputs/system_output_1.txt`
