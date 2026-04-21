#!/usr/bin/env python3
"""Replace display text Iaido/居合道 with Tameshigiri/試し切り/etc. Keep URL paths /iaido/ unchanged."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def lang_of(path: Path) -> str:
    parts = path.relative_to(ROOT).parts
    if not parts:
        return "ja"
    first = parts[0]
    if first in ("en", "ja", "zh-cn", "zh-tw"):
        return first
    return "ja"


def patch_en(text: str) -> str:
    # Longer phrases first (display text only — paths use lowercase iaido/)
    phrases = [
        ("Rates and practical information for the iaido experience",
         "Rates and practical information for the tameshigiri experience"),
        ("Book the iaido experience", "Book the tameshigiri experience"),
        ("Highlights of the iaido session", "Highlights of the tameshigiri session"),
        ("Learn safe, respectful handling of the katana as you explore iaido.",
         "Learn safe, respectful handling of the katana as you explore tameshigiri."),
        ("Iaido Experience", "Tameshigiri Experience"),
        ("Iaidō — sword drawing", "Tameshigiri — test cutting with the katana"),
        ("Iaidō", "Tameshigiri"),
        ("Iaido", "Tameshigiri"),
    ]
    for old, new in phrases:
        text = text.replace(old, new)
    # Macron form in body copy (not in URL paths, which use plain "iaido")
    text = text.replace("iaidō", "tameshigiri")
    # Lowercase prose leftovers
    text = re.sub(r"\biaido experience\b", "tameshigiri experience", text, flags=re.I)
    text = re.sub(r"\biaido session\b", "tameshigiri session", text, flags=re.I)
    text = re.sub(r"\bexplore iaido\b", "explore tameshigiri", text, flags=re.I)
    text = re.sub(r"\bthe iaido experience\b", "the tameshigiri experience", text, flags=re.I)
    return text


def patch_ja(text: str) -> str:
    text = text.replace("居合道", "試し切り")
    text = text.replace("弓道・居合・", "弓道・試し切り・")
    text = text.replace("日本刀の居合術", "日本刀の試し切り")
    text = text.replace("居合術", "試し切り")
    return text


def patch_zh_cn(text: str) -> str:
    text = text.replace("居合道", "试斩")
    text = text.replace("弓道、居合、", "弓道、试斩、")
    return text


def patch_zh_tw(text: str) -> str:
    text = text.replace("居合道", "試斬")
    text = text.replace("弓道、居合、", "弓道、試斬、")
    text = text.replace("日本刀居合術", "日本刀試斬")
    return text


def patch_file(path: Path) -> bool:
    lang = lang_of(path)
    raw = path.read_text(encoding="utf-8")
    original = raw

    if lang == "en":
        raw = patch_en(raw)
        raw = raw.replace("居合道", "試し切り")
    elif lang == "ja":
        raw = patch_ja(raw)
    elif lang == "zh-cn":
        raw = patch_zh_cn(raw)
    elif lang == "zh-tw":
        raw = patch_zh_tw(raw)

    if raw != original:
        path.write_text(raw, encoding="utf-8")
        return True
    return False


def main() -> int:
    count = 0
    for path in ROOT.rglob("*.html"):
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            continue
        if "node_modules" in rel.parts:
            continue
        if patch_file(path):
            count += 1
    print(f"Updated {count} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
