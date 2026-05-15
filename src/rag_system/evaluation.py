from __future__ import annotations

import re
import string
from collections import Counter

from rag_system.io_utils import split_references


def normalize_answer(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    text = "".join(ch for ch in text if ch not in string.punctuation)
    return " ".join(text.split())


def exact_match(prediction: str, references: list[str]) -> float:
    pred = normalize_answer(prediction)
    return float(any(pred == normalize_answer(ref) for ref in references))


def f1_score(prediction: str, reference: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    ref_tokens = normalize_answer(reference).split()
    common = Counter(pred_tokens) & Counter(ref_tokens)
    overlap = sum(common.values())
    if not pred_tokens or not ref_tokens:
        return float(pred_tokens == ref_tokens)
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def best_f1(prediction: str, references: list[str]) -> float:
    return max((f1_score(prediction, ref) for ref in references), default=0.0)


def answer_recall(prediction: str, references: list[str]) -> float:
    pred = normalize_answer(prediction)
    return float(any(normalize_answer(ref) in pred for ref in references))


def evaluate(predictions: list[str], reference_lines: list[str]) -> dict[str, float]:
    if len(predictions) != len(reference_lines):
        raise ValueError("Number of predictions must match number of references.")

    refs = [split_references(line) for line in reference_lines]
    total = len(predictions) or 1
    return {
        "exact_match": sum(exact_match(pred, ref) for pred, ref in zip(predictions, refs)) / total,
        "f1": sum(best_f1(pred, ref) for pred, ref in zip(predictions, refs)) / total,
        "answer_recall": sum(answer_recall(pred, ref) for pred, ref in zip(predictions, refs)) / total,
    }
