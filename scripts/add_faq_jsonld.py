#!/usr/bin/env python3
"""Inject FAQPage JSON-LD into the four /faq/ pages.

Every question and answer is read out of the page's own markup, so the
structured data cannot state anything the visitor is not shown - and no new
copy is written. The pages already carry 40 Q&As each in a uniform
faq-item / faq-item__question / faq-item__answer shape.

Idempotent: an existing block is replaced, not duplicated.
Run: python3 scripts/add_faq_jsonld.py
"""
from __future__ import annotations

import html as html_mod
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = "https://www.meihodo.com"

LANGS = {"ja": "ja", "en": "en", "zh-cn": "zh-Hans", "zh-tw": "zh-Hant"}
BRAND = {"ja": "鳴鳳堂", "en": "Meihodo", "zh-cn": "鸣凤堂", "zh-tw": "鳴鳳堂"}

START = "<!-- MEIHODO-FAQ-JSONLD -->"
END = "<!-- /MEIHODO-FAQ-JSONLD -->"

ITEM_RE = re.compile(
    r'<div class="faq-item">\s*'
    r'<h3 class="faq-item__question">(?P<q>.*?)</h3>\s*'
    r'<p class="faq-item__answer">(?P<a>.*?)</p>\s*'
    r"</div>",
    re.S,
)
ITEM_COUNT_RE = re.compile(r'class="faq-item"')
PAGE_TITLE_RE = re.compile(r'<h1[^>]*class="faq-page-title"[^>]*>(.*?)</h1>', re.S)
BLOCK_RE = re.compile(r"[ \t]*" + re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)


def text(raw: str) -> str:
    return html_mod.unescape(" ".join(raw.split()))


def build_block(page: str, lang: str) -> str | None:
    pairs = [(text(m.group("q")), text(m.group("a"))) for m in ITEM_RE.finditer(page)]
    if not pairs:
        return None
    # Refuse to publish a partial list: if the page holds faq-item blocks the
    # pattern did not match, the markup shape changed and needs a look.
    if len(pairs) != len(ITEM_COUNT_RE.findall(page)):
        raise SystemExit(
            f"{lang}: matched {len(pairs)} of {len(ITEM_COUNT_RE.findall(page))} faq-items"
        )

    title = PAGE_TITLE_RE.search(page)
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": f"{BASE}/{lang}/faq/#faqpage",
        "url": f"{BASE}/{lang}/faq/",
        "inLanguage": LANGS[lang],
        "publisher": {
            "@type": "LodgingBusiness",
            "@id": f"{BASE}/#lodgingbusiness",
            "name": BRAND[lang],
            "url": f"{BASE}/",
        },
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in pairs
        ],
    }
    if title:
        data["name"] = text(title.group(1))

    body = json.dumps(data, ensure_ascii=False, indent=2)
    body = "\n".join("    " + ln for ln in body.split("\n"))
    return (
        f"    {START}\n"
        '    <script type="application/ld+json">\n'
        f"{body}\n"
        "    </script>\n"
        f"    {END}\n"
    )


def main() -> int:
    updated = 0
    for lang in LANGS:
        path = REPO / lang / "faq" / "index.html"
        if not path.exists():
            print(f"  missing: {lang}/faq")
            continue
        src = path.read_text(encoding="utf-8")
        block = build_block(src, lang)
        if block is None or "</head>" not in src:
            print(f"  skipped: {lang}/faq")
            continue
        out = BLOCK_RE.sub("", src).replace("</head>", block + "</head>", 1)
        if out != src:
            path.write_text(out, encoding="utf-8")
            updated += 1
    print(f"Updated {updated} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
