# End-to-end NLP System

Retrieval Augmented Generation (RAG) project for factual question answering over public UET/VNU knowledge sources.

## Submission Files

- `github_url.txt`: repository URL.
- `contributions.md`: contribution summary.
- `reports/report.tex`: Vietnamese LaTeX project report source.
- `reports/assets/uet_logo.png`: UET logo used by the LaTeX report.
- `data/raw/uet_vnu/corpus_long.txt`: raw public knowledge resource.
- `data/uet_vnu/documents.jsonl` and `data/uet_vnu/metadata.json`: crawled document metadata.
- `data/train/questions.txt` and `data/train/reference_answers.txt`: training/development QA set.
- `data/test/questions.txt` and `data/test/reference_answers.txt`: annotated test QA set.
- `system_outputs/system_output_1.txt`: final hybrid RAG answers for the test questions.
- `system_outputs/system_output_2.txt`: retrieval-only baseline answers.
- `system_outputs/system_output_3.txt`: direct/closed-book baseline answers.

## Data

The current dataset was built from public UET/VNU-related sources:

- 88 cleaned documents: 81 official UET/VNU/member-school pages, 4 Wikipedia pages, and 3 recent related news pages.
- 279 manually curated QA examples in total.
- 213 train/development examples and 66 test examples.

Questions focus on school-centered content instead of trivial metadata, for example:

```text
Ai là hiệu trưởng Trường Đại học Công nghệ?
Trường Đại học Công nghệ có tên tiếng Anh là gì?
Ngành Trí tuệ nhân tạo năm 2025 có điểm trúng tuyển bao nhiêu?
```

The raw corpus stores article metadata and body text in a plain text format, and `data/processed/corpus.jsonl` stores the cleaned chunks used by the retriever.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The default reproducible pipeline uses a TF-IDF word n-gram retriever, which avoids PyTorch/Windows DLL issues. The code still supports optional Hugging Face models if the dependencies are installed:

- embedding: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- optional reranker: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- Vietnamese extractive QA reader: `letrunglinh/qa_pnc`

Model files are cached under `.hf_cache/` in this project directory.

## Rebuild

Rewrite the manually curated QA set and cleaned corpus:

```bash
python scripts/write_manual_curated_qa.py
```

Build the cleaned corpus and retrieval index:

```bash
python scripts/build_corpus.py --raw-dir data/raw/uet_vnu --out data/processed/corpus.jsonl
python scripts/build_index.py --corpus data/processed/corpus.jsonl --out data/processed/index.pkl --embedding-model tfidf-word-ngram
```

`data/processed/index.pkl` is ignored by git because it is a generated binary file.

## Run

Generate answers for the test set:

```bash
python scripts/run_rag.py ^
  --questions data/test/questions.txt ^
  --index data/processed/index.pkl ^
  --out system_outputs/system_output_1.txt ^
  --no-reranker ^
  --top-k 5 ^
  --extractive
```

Run the two baselines used in the report:

```powershell
python scripts/run_retrieval_baseline.py --questions data/test/questions.txt --index data/processed/index.pkl --out system_outputs/system_output_2.txt --top-k 5
python scripts/run_direct_baseline.py --questions data/test/questions.txt --out system_outputs/system_output_3.txt
```

Interactive single-question mode:

```bash
python scripts/chat_rag.py --question "Trường Đại học Công nghệ thuộc đại học nào?" --no-reranker --top-k 5
```

Qwen CPU smoke test:

```bash
python scripts/qwen_smoke_rag.py ^
  --question "UET và Đại học Sư phạm Quảng Tây đã trao đổi những nội dung hợp tác nào?" ^
  --index data/processed/index.pkl ^
  --model Qwen/Qwen2.5-1.5B-Instruct ^
  --top-k 1 ^
  --max-context-chars 500 ^
  --max-new-tokens 4
```

## Evaluate

```bash
python scripts/evaluate.py ^
  --predictions system_outputs/system_output_1.txt ^
  --references data/test/reference_answers.txt
```

Latest local evaluation on the annotated test set:

```text
Retrieval-only baseline:
exact_match: 0.0152
f1: 0.1266
answer_recall: 0.1818

Direct/closed-book baseline:
exact_match: 0.8636
f1: 0.8970
answer_recall: 0.9091

Final hybrid RAG:
exact_match: 0.9242
f1: 0.9576
answer_recall: 0.9697
```
