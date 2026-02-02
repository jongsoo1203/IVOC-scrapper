from __future__ import annotations


def parse_keywords(raw: str) -> list[str]:
    raw = (raw or "").strip()
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


def matches_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    t = text.lower()
    return any(k.lower() in t for k in keywords)
