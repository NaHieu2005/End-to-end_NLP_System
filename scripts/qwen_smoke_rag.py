from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rag_system.qa import DEFAULT_GENERATIVE_MODEL, HF_HUB_CACHE_DIR, USER_PROMPT_TEMPLATE
from rag_system.retrieval import Retriever


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--index", default="data/processed/index.pkl")
    parser.add_argument("--model", default=DEFAULT_GENERATIVE_MODEL)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--max-context-chars", type=int, default=700)
    parser.add_argument("--max-new-tokens", type=int, default=24)
    args = parser.parse_args()

    log(f"python={sys.executable}")
    log("loading retriever")
    retriever = Retriever.load(args.index)
    log("retrieving")
    retrieved = retriever.retrieve(args.question, top_k=args.top_k)
    context = "\n\n".join(chunk.text[: args.max_context_chars] for chunk, _score in retrieved)
    context = context[: args.max_context_chars]
    log(f"context chars={len(context)}")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(4)
    log("loading tokenizer")
    tokenizer = AutoTokenizer.from_pretrained(args.model, cache_dir=str(HF_HUB_CACHE_DIR))
    log("loading model")
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        cache_dir=str(HF_HUB_CACHE_DIR),
        torch_dtype="auto",
        low_cpu_mem_usage=True,
    )
    model.to("cpu")
    log("tokenizing")
    prompt = USER_PROMPT_TEMPLATE.format(context=context, question=args.question)
    text = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer([text], return_tensors="pt")
    log(f"input tokens={inputs.input_ids.shape[-1]}")
    log("generating")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
    answer = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1] :], skip_special_tokens=True)
    log("done")
    print(answer.strip(), flush=True)


if __name__ == "__main__":
    main()
