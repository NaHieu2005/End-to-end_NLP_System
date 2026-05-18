# Kaggle Fine-tuning Workflow

Upload the contents of `data/news_finetune/` as a Kaggle Dataset named `news-finetune-data`.

Expected dataset files:

- `corpus_long.txt`
- `qa_squad_train.json`
- `qa_squad_valid.json`
- `qa_squad_test.json`
- `metadata.json`
- `raw/articles.jsonl`

Install dependencies in a Kaggle notebook:

```bash
pip install -q -r /kaggle/input/<repo-or-uploaded-code>/kaggle/requirements.txt
```

Train from a Hugging Face base model:

```bash
python /kaggle/input/<repo-or-uploaded-code>/kaggle/train_qa.py \
  --train-file /kaggle/input/news-finetune-data/qa_squad_train.json \
  --valid-file /kaggle/input/news-finetune-data/qa_squad_valid.json \
  --test-file /kaggle/input/news-finetune-data/qa_squad_test.json \
  --model-name xlm-roberta-base \
  --output-dir /kaggle/working/uet-qa-checkpoints \
  --final-dir /kaggle/working/uet-qa-final \
  --epochs 3 \
  --batch-size 4 \
  --save-steps 50 \
  --eval-steps 50
```

Resume after interruption:

```bash
python /kaggle/input/<repo-or-uploaded-code>/kaggle/train_qa.py \
  --train-file /kaggle/input/news-finetune-data/qa_squad_train.json \
  --valid-file /kaggle/input/news-finetune-data/qa_squad_valid.json \
  --test-file /kaggle/input/news-finetune-data/qa_squad_test.json \
  --output-dir /kaggle/working/uet-qa-checkpoints \
  --final-dir /kaggle/working/uet-qa-final
```

The script automatically resumes from the latest `checkpoint-*` directory in `--output-dir`.

Load the trained model:

```python
from transformers import pipeline

qa = pipeline("question-answering", model="/kaggle/working/uet-qa-final", tokenizer="/kaggle/working/uet-qa-final")
qa(question="UET thuộc đại học nào?", context="Trường Đại học Công nghệ thuộc Đại học Quốc gia Hà Nội.")
```
