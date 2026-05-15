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

The implementation uses open-source Hugging Face accessible models:

- embedding: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- extractive QA reader: `deepset/xlm-roberta-base-squad2`

You can change these with command-line flags.

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

## Submission Checklist

- `report.pdf` or report source in `reports/`
- `github_url.txt`
- `contributions.md`
- `data/train/questions.txt`
- `data/train/reference_answers.txt`
- `data/test/questions.txt`
- `data/test/reference_answers.txt`
- `system_outputs/system_output_1.txt`
