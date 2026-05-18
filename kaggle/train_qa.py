from __future__ import annotations

import argparse
import os
import json
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoModelForQuestionAnswering,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


def latest_checkpoint(output_dir: Path) -> str | None:
    checkpoints = [path for path in output_dir.glob("checkpoint-*") if path.is_dir()]
    if not checkpoints:
        return None
    return str(max(checkpoints, key=lambda path: int(path.name.split("-")[-1])))


def load_squad(path: str) -> Dataset:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for article in payload["data"]:
        title = article.get("title", "")
        for paragraph in article["paragraphs"]:
            context = paragraph["context"]
            for qa in paragraph["qas"]:
                rows.append(
                    {
                        "id": qa["id"],
                        "title": title,
                        "context": context,
                        "question": qa["question"],
                        "answers": {
                            "text": [answer["text"] for answer in qa["answers"]],
                            "answer_start": [answer["answer_start"] for answer in qa["answers"]],
                        },
                    }
                )
    return Dataset.from_list(rows)


def preprocess_train(examples, tokenizer, max_length: int, stride: int):
    questions = [question.strip() for question in examples["question"]]
    tokenized = tokenizer(
        questions,
        examples["context"],
        truncation="only_second",
        max_length=max_length,
        stride=stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding=False,
    )

    sample_mapping = tokenized.pop("overflow_to_sample_mapping")
    offset_mapping = tokenized.pop("offset_mapping")
    start_positions = []
    end_positions = []

    for feature_idx, offsets in enumerate(offset_mapping):
        input_ids = tokenized["input_ids"][feature_idx]
        cls_index = input_ids.index(tokenizer.cls_token_id)
        sequence_ids = tokenized.sequence_ids(feature_idx)
        sample_idx = sample_mapping[feature_idx]
        answers = examples["answers"][sample_idx]

        if len(answers["answer_start"]) == 0:
            start_positions.append(cls_index)
            end_positions.append(cls_index)
            continue

        start_char = answers["answer_start"][0]
        end_char = start_char + len(answers["text"][0])

        token_start = 0
        while sequence_ids[token_start] != 1:
            token_start += 1
        token_end = len(input_ids) - 1
        while sequence_ids[token_end] != 1:
            token_end -= 1

        if offsets[token_start][0] > start_char or offsets[token_end][1] < end_char:
            start_positions.append(cls_index)
            end_positions.append(cls_index)
        else:
            while token_start < len(offsets) and offsets[token_start][0] <= start_char:
                token_start += 1
            start_positions.append(token_start - 1)

            while offsets[token_end][1] >= end_char:
                token_end -= 1
            end_positions.append(token_end + 1)

    tokenized["start_positions"] = start_positions
    tokenized["end_positions"] = end_positions
    return tokenized


def preprocess_eval(examples, tokenizer, max_length: int, stride: int):
    questions = [question.strip() for question in examples["question"]]
    tokenized = tokenizer(
        questions,
        examples["context"],
        truncation="only_second",
        max_length=max_length,
        stride=stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding=False,
    )

    sample_mapping = tokenized.pop("overflow_to_sample_mapping")
    tokenized["example_id"] = []
    for feature_idx in range(len(tokenized["input_ids"])):
        sample_idx = sample_mapping[feature_idx]
        tokenized["example_id"].append(examples["id"][sample_idx])
        sequence_ids = tokenized.sequence_ids(feature_idx)
        tokenized["offset_mapping"][feature_idx] = [
            offset if sequence_ids[token_idx] == 1 else None
            for token_idx, offset in enumerate(tokenized["offset_mapping"][feature_idx])
        ]
    return tokenized


def postprocess_predictions(examples, features, predictions, n_best: int = 20, max_answer_length: int = 40):
    start_logits, end_logits = predictions
    example_to_features: dict[str, list[int]] = {}
    for idx, feature in enumerate(features):
        example_to_features.setdefault(feature["example_id"], []).append(idx)

    predicted_answers = []
    for example in examples:
        example_id = example["id"]
        context = example["context"]
        best_answer = {"text": "", "score": -1e9}

        for feature_idx in example_to_features.get(example_id, []):
            offsets = features[feature_idx]["offset_mapping"]
            start_logit = start_logits[feature_idx]
            end_logit = end_logits[feature_idx]
            start_indexes = np.argsort(start_logit)[-1 : -n_best - 1 : -1]
            end_indexes = np.argsort(end_logit)[-1 : -n_best - 1 : -1]

            for start_index in start_indexes:
                for end_index in end_indexes:
                    if offsets[start_index] is None or offsets[end_index] is None:
                        continue
                    if end_index < start_index or end_index - start_index + 1 > max_answer_length:
                        continue
                    start_char, _ = offsets[start_index]
                    _, end_char = offsets[end_index]
                    score = start_logit[start_index] + end_logit[end_index]
                    if score > best_answer["score"]:
                        best_answer = {"text": context[start_char:end_char], "score": score}

        predicted_answers.append({"id": example_id, "prediction_text": best_answer["text"]})
    return predicted_answers


def exact_match(prediction: str, references: list[str]) -> float:
    pred = prediction.strip().lower()
    return float(any(pred == ref.strip().lower() for ref in references))


def token_f1(prediction: str, reference: str) -> float:
    pred_tokens = prediction.lower().split()
    ref_tokens = reference.lower().split()
    common = set(pred_tokens) & set(ref_tokens)
    if not pred_tokens or not ref_tokens:
        return float(pred_tokens == ref_tokens)
    if not common:
        return 0.0
    precision = sum(min(pred_tokens.count(tok), ref_tokens.count(tok)) for tok in common) / len(pred_tokens)
    recall = sum(min(pred_tokens.count(tok), ref_tokens.count(tok)) for tok in common) / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def compute_eval_metrics(examples, features, predictions):
    predicted = postprocess_predictions(examples, features, predictions)
    references = {item["id"]: item["answers"]["text"] for item in examples}
    em = []
    f1 = []
    for item in predicted:
        refs = references[item["id"]]
        em.append(exact_match(item["prediction_text"], refs))
        f1.append(max(token_f1(item["prediction_text"], ref) for ref in refs))
    return {"exact_match": float(np.mean(em)), "f1": float(np.mean(f1))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-file", default="/kaggle/input/news-finetune-data/qa_squad_train.json")
    parser.add_argument("--valid-file", default="/kaggle/input/news-finetune-data/qa_squad_valid.json")
    parser.add_argument("--test-file", default="/kaggle/input/news-finetune-data/qa_squad_test.json")
    parser.add_argument("--model-name", default="xlm-roberta-base")
    parser.add_argument("--output-dir", default="/kaggle/working/uet-qa-checkpoints")
    parser.add_argument("--final-dir", default="/kaggle/working/uet-qa-final")
    parser.add_argument("--max-length", type=int, default=384)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=3e-5)
    parser.add_argument("--save-steps", type=int, default=50)
    parser.add_argument("--eval-steps", type=int, default=50)
    args = parser.parse_args()

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = DatasetDict(
        {
            "train": load_squad(args.train_file),
            "validation": load_squad(args.valid_file),
            "test": load_squad(args.test_file) if args.test_file else load_squad(args.valid_file),
        }
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    model = AutoModelForQuestionAnswering.from_pretrained(args.model_name)

    train_dataset = raw["train"].map(
        lambda examples: preprocess_train(examples, tokenizer, args.max_length, args.stride),
        batched=True,
        remove_columns=raw["train"].column_names,
    )
    valid_for_loss = raw["validation"].map(
        lambda examples: preprocess_train(examples, tokenizer, args.max_length, args.stride),
        batched=True,
        remove_columns=raw["validation"].column_names,
    )
    eval_examples = raw["validation"]
    eval_features = eval_examples.map(
        lambda examples: preprocess_eval(examples, tokenizer, args.max_length, args.stride),
        batched=True,
        remove_columns=raw["validation"].column_names,
    )

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=5,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        weight_decay=0.01,
        logging_steps=10,
        report_to="none",
        fp16=torch.cuda.is_available(),
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_for_loss,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
    )

    checkpoint = latest_checkpoint(output_dir)
    trainer.train(resume_from_checkpoint=checkpoint)
    trainer.save_model(args.final_dir)
    tokenizer.save_pretrained(args.final_dir)

    predictions = trainer.predict(eval_features.remove_columns(["example_id", "offset_mapping"]))
    metrics = compute_eval_metrics(eval_examples, eval_features, predictions.predictions)
    print({"validation": metrics})
    (Path(args.final_dir) / "eval_metrics.json").write_text(str(metrics), encoding="utf-8")

    test_examples = raw["test"]
    test_features = test_examples.map(
        lambda examples: preprocess_eval(examples, tokenizer, args.max_length, args.stride),
        batched=True,
        remove_columns=raw["test"].column_names,
    )
    test_predictions = trainer.predict(test_features.remove_columns(["example_id", "offset_mapping"]))
    test_metrics = compute_eval_metrics(test_examples, test_features, test_predictions.predictions)
    print({"test": test_metrics})
    (Path(args.final_dir) / "test_metrics.json").write_text(str(test_metrics), encoding="utf-8")


if __name__ == "__main__":
    main()
