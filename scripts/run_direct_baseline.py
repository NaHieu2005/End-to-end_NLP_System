from __future__ import annotations

import argparse
from pathlib import Path

from rag_system.io_utils import read_lines
from rag_system.qa import NO_INFORMATION, _direct_answer


def main() -> None:
    parser = argparse.ArgumentParser(description="Run closed-book direct-answer baseline.")
    parser.add_argument("--questions", default="data/test/questions.txt")
    parser.add_argument("--out", default="system_outputs/system_output_3.txt")
    args = parser.parse_args()

    questions = read_lines(Path(args.questions))
    outputs = []
    for i, question in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {question[:60]}...")
        outputs.append(_direct_answer(question) or NO_INFORMATION)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(outputs) + "\n", encoding="utf-8")
    print(f"Wrote {len(outputs)} answers to {out_path}")


if __name__ == "__main__":
    main()
