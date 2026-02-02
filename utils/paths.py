from __future__ import annotations
from pathlib import Path


def project_root() -> Path:
    # main.py lives at project root
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    d = project_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d
