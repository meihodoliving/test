#!/usr/bin/env python3
"""
Fix placeholder href="#" links in the footer experience menu across the site.

Every page renders an "Experiences" menu in the footer with eight links, but
they were all left as href="#" stubs. This walks each page, infers the language
from its path, and rewrites the eight links to point at the actual experience
URLs in that language tree.

Idempotent — safe to re-run.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (anchor text on page) -> experience slug under /<lang>/experiences/<slug>/
LANG_LABEL_TO_SLUG: dict[str, dict[str, str]] = {
    "ja": {
        "弓道": "kyudo",
        "試し切り": "iaido",
        "剣道": "kendo",
        "空手": "karate",
        "茶道": "chado",
        "盆石": "bonseki",
        "和太鼓": "taiko",
        "華道": "kado",
    },
    "en": {
        "Kyudo": "kyudo",
        "Kyūdō": "kyudo",
        "Tameshigiri": "iaido",
        "Kendo": "kendo",
        "Kendō": "kendo",
        "Karate": "karate",
        "Tea ceremony": "chado",
        "Bonseki": "bonseki",
        "Taiko": "taiko",
        "Kado": "kado",
        "Kadō": "kado",
        "Ikebana": "kado",
    },
    "zh-cn": {
        "弓道": "kyudo",
        "试斩": "iaido",
        "剑道": "kendo",
        "空手": "karate",
        "空手道": "karate",
        "茶道": "chado",
        "盆石": "bonseki",
        "和太鼓": "taiko",
        "花道": "kado",
    },
    "zh-tw": {
        "弓道": "kyudo",
        "試斬": "iaido",
        "試し切り": "iaido",  # legacy JA label that wasn't translated by the mirror script
        "劍道": "kendo",
        "剣道": "kendo",  # JA legacy
        "空手": "karate",
        "空手道": "karate",
        "茶道": "chado",
        "盆石": "bonseki",
        "和太鼓": "taiko",
        "花道": "kado",
        "華道": "kado",  # JA legacy
    },
}

# Root /index.html (Japanese root) uses the JA labels
LANG_LABEL_TO_SLUG["root"] = LANG_LABEL_TO_SLUG["ja"]

# Match e.g.   <li><a href="#">弓道</a></li>
# Capture: leading whitespace (group1), label (group2)
LINK_RE = re.compile(r'(<li>\s*<a\s+href=")#("\s*>)([^<]+)(</a>\s*</li>)')


def lang_for_path(p: Path) -> str | None:
    """Return language key based on which top-level dir the file lives in."""
    rel = p.relative_to(ROOT).parts
    if not rel:
        return None
    head = rel[0]
    if head in {"ja", "en", "zh-cn", "zh-tw"}:
        return head
    if head == "index.html":
        return "root"
    return None


def url_for(lang: str, slug: str) -> str:
    base_lang = "ja" if lang == "root" else lang
    return f"/{base_lang}/experiences/{slug}/"


def rewrite(html: str, lang: str) -> tuple[str, int]:
    table = LANG_LABEL_TO_SLUG[lang]
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        prefix, suffix, label, tail = match.group(1), match.group(2), match.group(3).strip(), match.group(4)
        slug = table.get(label)
        if not slug:
            return match.group(0)
        count += 1
        return f'{prefix}{url_for(lang, slug)}{suffix}{label}{tail}'

    new_html = LINK_RE.sub(replace, html)
    return new_html, count


def iter_html_files() -> list[Path]:
    files: list[Path] = []
    # Root index
    root_index = ROOT / "index.html"
    if root_index.exists():
        files.append(root_index)
    # Language trees
    for lang in ("ja", "en", "zh-cn", "zh-tw"):
        lang_dir = ROOT / lang
        if not lang_dir.exists():
            continue
        files.extend(lang_dir.rglob("*.html"))
    return files


def main() -> None:
    total_files_changed = 0
    total_links_fixed = 0
    for path in iter_html_files():
        lang = lang_for_path(path)
        if lang is None:
            continue
        html = path.read_text(encoding="utf-8")
        if 'href="#"' not in html:
            continue
        new_html, count = rewrite(html, lang)
        if count == 0:
            continue
        path.write_text(new_html, encoding="utf-8")
        total_files_changed += 1
        total_links_fixed += count
        print(f"  {path.relative_to(ROOT)}: {count} links")
    print(f"\nFixed {total_links_fixed} links across {total_files_changed} files.")


if __name__ == "__main__":
    main()
