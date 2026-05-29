from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rag_system.evaluation import evaluate
from rag_system.io_utils import read_lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", default="system_outputs/system_output_1.txt")
    parser.add_argument("--references", default="data/test/reference_answers.txt")
    args = parser.parse_args()

    preds = [line.strip() for line in Path(args.predictions).read_text(encoding="utf-8").splitlines()]
    refs = [line.strip() for line in Path(args.references).read_text(encoding="utf-8").splitlines()]
    metrics = evaluate(preds, refs)
    for name, value in metrics.items():
        print(f"{name}: {value:.4f}")


if __name__ == "__main__":
    main()
