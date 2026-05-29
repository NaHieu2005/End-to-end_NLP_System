from __future__ import annotations

import os
import platform
from collections import namedtuple
from pathlib import Path


def default_cache_dir() -> Path:
    return Path(__file__).resolve().parents[2] / ".hf_cache"


def configure_hf_cache(cache_dir: str | Path | None = None) -> Path:
    target = Path(cache_dir) if cache_dir else default_cache_dir()
    target.mkdir(parents=True, exist_ok=True)

    # Set before loading Hugging Face libraries so model weights stay on drive F.
    os.environ["HF_HOME"] = str(target)
    os.environ["HF_HUB_CACHE"] = str(target / "hub")
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(target / "sentence_transformers")
    os.environ["TRITON_CACHE_DIR"] = str(target / "triton")
    os.environ["PIP_CACHE_DIR"] = str(target / "pip")
    return target


def avoid_windows_platform_wmi_probe() -> None:
    """Avoid a PyTorch import hang when Windows WMI queries stall."""
    if os.name == "nt":
        uname_type = namedtuple("uname_result", "system node release version machine processor")
        safe_uname = uname_type("Windows", "", "", "", "AMD64", "AMD64")
        platform.system = lambda: "Windows"  # type: ignore[assignment]
        platform.machine = lambda: "AMD64"  # type: ignore[assignment]
        platform.processor = lambda: "AMD64"  # type: ignore[assignment]
        platform.uname = lambda: safe_uname  # type: ignore[assignment]
