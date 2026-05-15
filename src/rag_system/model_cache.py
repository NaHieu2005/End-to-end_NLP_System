from __future__ import annotations

import os
from pathlib import Path


def default_cache_dir() -> Path:
    return Path(__file__).resolve().parents[2] / ".hf_cache"


def configure_hf_cache(cache_dir: str | Path | None = None) -> Path:
    target = Path(cache_dir) if cache_dir else default_cache_dir()
    target.mkdir(parents=True, exist_ok=True)

    # Set before loading Hugging Face libraries so model weights stay on drive F.
    os.environ.setdefault("HF_HOME", str(target))
    os.environ.setdefault("HF_HUB_CACHE", str(target / "hub"))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(target / "sentence_transformers"))
    return target
