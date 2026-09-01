#!/usr/bin/env python3
"""Regenerate canonical, hreflang, description and social metadata on every page.

Before this ran, 104 of 155 pages had no canonical, no hreflang, no meta
description and no Open Graph tags at all; the pages that did have them pointed
at URLs that 308-redirect (Vercel runs cleanUrls + trailingSlash:false, so
"/ja/restaurant/" is never the served URL), every zh-tw restaurant page
canonicalised itself onto the Japanese page, and the og:image files
(og-image-restaurant.jpg, restaurant-hero.jpg) 404.

This writes one marker-delimited block per page and strips the pre-existing
loose tags it replaces, so the two can never disagree.

Descriptions are the page's own meta description when it already had a usable
one, otherwise its first substantial paragraph. Nothing is written that a
visitor cannot read on the page.

Idempotent. Run: python3 scripts/build_head_meta.py [--check]
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import seo_config as C
from build_jsonld import START as JSONLD_START
from build_jsonld import page_description, page_image, page_title

START = "<!-- MEIHODO-SEO-META -->"
END = "<!-- /MEIHODO-SEO-META -->"

MARKED_RE = re.compile(r"[ \t]*" + re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)

# Loose tags this generator now owns. Removed wherever they sit in <head> so a
# stale canonical or a 404 og:image cannot survive alongside the managed block.
OWNED_RE = re.compile(
    r'[ \t]*<link[^>]+rel="canonical"[^>]*>\n?'
    r'|[ \t]*<link[^>]+rel="alternate"[^>]+hreflang="[^"]*"[^>]*>\n?'
    r'|[ \t]*<meta[^>]+(?:property|name)="og:[^"]*"[^>]*>\n?'
    r'|[ \t]*<meta[^>]+name="twitter:[^"]*"[^>]*>\n?'
    r'|[ \t]*<meta[^>]+name="description"[^>]*>\n?'
    r'|[ \t]*<meta[^>]+name="robots"[^>]*>\n?',
    re.I,
)

TITLE_TAG_RE = re.compile(r"(<title>)(.*?)(</title>)", re.S)

OG_LOCALE = {"ja": "ja_JP", "en": "en_US", "zh-cn": "zh_CN", "zh-tw": "zh_TW"}


def esc(value: str) -> str:
    """Escape for an HTML double-quoted attribute."""
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def trim(text: str, limit: int = 300) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def build_block(page, src: str) -> str:
    lang = page.lang
    title = page_title(src, lang)
    if page.kind == "home":
        # The home pages lead with a hero video whose control labels ("音声オン
        # /音声オフ") are the first text on the page, and their first paragraph
        # is a mood line rather than a summary. Use the facility description,
        # which is condensed from what /about says in this same language.
        description = C.FACILITY_DESCRIPTION[lang]
        image = C.DEFAULT_IMAGE
    else:
        description = page_description(src, page.path)
        image = page_image(src) or C.DEFAULT_IMAGE

    lines = [START]

    if description:
        lines.append(f'<meta name="description" content="{esc(trim(description))}">')

    lines.append(f'<link rel="canonical" href="{esc(page.canonical)}">')

    alts = C.alternates_for(page)
    for tag, url in alts.items():
        lines.append(f'<link rel="alternate" hreflang="{tag}" href="{esc(url)}">')
    if alts:
        # x-default points at the Japanese edition: it is the source of truth
        # for the mirror (see CLAUDE.md) and the URL the brand publishes.
        lines.append(
            f'<link rel="alternate" hreflang="x-default" href="{esc(alts.get("ja", page.canonical))}">'
        )

    og_type = "website" if page.kind == "home" else "article"
    lines += [
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{esc(C.BRAND[lang])}">',
        f'<meta property="og:locale" content="{OG_LOCALE[lang]}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:url" content="{esc(page.canonical)}">',
        f'<meta property="og:image" content="{esc(image)}">',
    ]
    if description:
        lines.append(f'<meta property="og:description" content="{esc(trim(description))}">')

    lines += [
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        f'<meta name="twitter:image" content="{esc(image)}">',
    ]
    if description:
        lines.append(f'<meta name="twitter:description" content="{esc(trim(description))}">')

    lines.append(END)
    return "".join(f"    {line}\n" for line in lines)


def fix_title(src: str, lang: str) -> str:
    """Collapse the "X - 鳴鳳堂 鳴鳳堂" duplication on the pages that carry it.

    Operates on the raw markup and never unescapes it: several English titles
    contain "&amp;", and decoding that on the way through would write a bare
    ampersand back into the document.
    """
    def repl(m):
        cleaned = re.sub(r"\s+", " ", m.group(2)).strip()
        brand = C.BRAND[lang]
        while cleaned.endswith(f"{brand} {brand}"):
            cleaned = cleaned[: -(len(brand) + 1)].strip()
        return m.group(1) + cleaned + m.group(3)

    return TITLE_TAG_RE.sub(repl, src, count=1)


def process(path: Path, page, check: bool) -> bool:
    src = path.read_text(encoding="utf-8")
    if "</head>" not in src:
        print(f"  SKIP (no </head>): {page.path}")
        return False

    head, sep, rest = src.partition("</head>")
    head = MARKED_RE.sub("", head)
    head = OWNED_RE.sub("", head)
    head = fix_title(head, page.lang)

    block = build_block(page, src)
    # Anchor the block immediately above the JSON-LD block rather than at the
    # end of <head>. build_jsonld.py re-inserts its block just before </head>,
    # so appending here too would leave the two generators swapping places on
    # every alternating run.
    anchor = head.find(JSONLD_START)
    if anchor == -1:
        new = head.rstrip("\n") + "\n" + block + sep + rest
    else:
        line_start = head.rfind("\n", 0, anchor) + 1
        new = head[:line_start] + block + head[line_start:] + sep + rest

    if new == src:
        return False
    if not check:
        path.write_text(new, encoding="utf-8")
    return True


# Kana are unique to Japanese; Han characters alone cannot separate the three
# languages, so this only flags the unambiguous case - a non-ja page whose body
# is still Japanese.
KANA_RE = re.compile(r"[぀-ゟ゠-ヿ]")


def untranslated(page, src: str) -> bool:
    """True when a non-Japanese page is still showing Japanese body copy."""
    if page.lang == "ja":
        return False
    body = src.partition("</head>")[2]
    body = re.sub(r"<(script|style)\b.*?</\1>", "", body, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", body)
    return len(KANA_RE.findall(text)) > 40


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args()

    changed = 0
    stale: list[str] = []
    for page in C.build_registry():
        path = C.REPO / page.path
        if untranslated(page, path.read_text(encoding="utf-8")):
            stale.append(page.path)
        if process(path, page, args.check):
            changed += 1
    verb = "would change" if args.check else "updated"
    print(f"build_head_meta: {verb} {changed} file(s)")
    if stale:
        # Reported, not silently patched: hreflang and inLanguage describe what
        # the page is meant to be, and the fix is to translate the copy, not to
        # relabel the page as Japanese.
        print(f"\n  WARNING: {len(stale)} non-ja page(s) still show Japanese body copy.")
        print("  hreflang/inLanguage advertise a translation these pages do not have.")
        print("  See AEO_CONTENT_RECOMMENDATIONS.md P0-1.")
        for p in stale:
            print(f"    {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
