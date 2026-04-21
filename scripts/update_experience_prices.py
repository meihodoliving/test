#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

LANGS = ("ja", "en", "zh-cn", "zh-tw")
SLUGS = ("samurai", "kyudo", "kendo", "iaido", "karate", "chado", "taiko", "bonseki", "kado", "takigyo")


PRICES = {
    "samurai": {"adult": 35000, "child": 17500},
    "kyudo": {"adult": 15000, "child": 7500},
    "kendo": {"adult": 15000, "child": 7500},
    "iaido": {"adult": 15000, "child": 7500},
    "karate": {"adult": 15000, "child": 7500},
    "chado": {"adult": 10000, "child": 5000},
    "taiko": {"adult": 12000, "child": 6000},
    "bonseki": {"adult": 12000, "child": 6000},
    "kado": {"adult": 22500, "child": 11250},
    "takigyo": {"adult": 5000, "child": None},
}


def fmt_yen(amount: int) -> str:
    return f"¥{amount:,}"


def fmt_ja(amount: int) -> str:
    return f"{amount:,}円"


def fmt_en(amount: int) -> str:
    return fmt_yen(amount)


def fmt_zh_cn(amount: int) -> str:
    return f"{amount:,}日元"


def fmt_zh_tw(amount: int) -> str:
    return f"{amount:,} 日圓"


def card_price_text(lang: str, amount: int) -> str:
    if lang == "ja":
        return fmt_ja(amount)
    if lang == "en":
        return fmt_en(amount)
    if lang == "zh-cn":
        return fmt_zh_cn(amount)
    return fmt_zh_tw(amount)


def pricing_labels(lang: str) -> tuple[str, str]:
    # adult label, child label (8–11)
    if lang == "ja":
        return ("大人（1名）", "子ども（8歳〜11歳）")
    if lang == "en":
        return ("Adult (1 guest)", "Child (ages 8–11)")
    if lang == "zh-cn":
        return ("成人（1名）", "儿童（8〜11岁）")
    return ("大人（1名）", "子ども（8〜11歳）")


def pricing_note(lang: str) -> str:
    if lang == "ja":
        return "税込"
    if lang == "en":
        return "Inc. tax"
    if lang == "zh-cn":
        return "含税"
    return "含稅"


def build_pricing_grid(lang: str, slug: str) -> str:
    adult = PRICES[slug]["adult"]
    child = PRICES[slug]["child"]
    adult_label, child_label = pricing_labels(lang)
    note = pricing_note(lang)

    adult_html = (
        "                    <div class=\"pricing-item\">\n"
        f"                        <h3>{adult_label}</h3>\n"
        f"                        <div class=\"price\">{fmt_yen(adult)}</div>\n"
        f"                        <div class=\"note\">{note}</div>\n"
        "                    </div>"
    )

    if child is None:
        child_price = "-"
    else:
        child_price = fmt_yen(child)

    child_html = (
        "                    <div class=\"pricing-item\">\n"
        f"                        <h3>{child_label}</h3>\n"
        f"                        <div class=\"price\">{child_price}</div>\n"
        f"                        <div class=\"note\">{note}</div>\n"
        "                    </div>"
    )

    return f"{adult_html}\n{child_html}"


PRICING_GRID_RE = re.compile(
    r"(?P<open><div class=\"pricing-grid\">\s*\n)(?P<body>[\s\S]*?)(?P<close>\n\s*</div>\s*\n\s*<div class=\"pricing-details\">)",
    re.MULTILINE,
)


def patch_detail_pricing(html: str, lang: str, slug: str) -> str:
    if slug == "samurai":
        return html
    m = PRICING_GRID_RE.search(html)
    if not m:
        return html
    new_body = build_pricing_grid(lang, slug)
    return html[: m.start("body")] + new_body + html[m.end("body") :]


def patch_experiences_index_cards(html: str, lang: str) -> str:
    # Update all experience cards prices based on href to each slug.
    for slug in SLUGS:
        adult = PRICES[slug]["adult"]
        new_price = card_price_text(lang, adult)

        # Replace first price span inside the anchor card block for this slug.
        # Keep it conservative: anchor includes href to slug, then find first price span inside.
        pattern = re.compile(
            rf'(<a[^>]+href="[^"]*{re.escape(slug)}/"[^>]*>[\s\S]*?<span class="detail-value price">)([^<]+)(</span>)',
            re.MULTILINE,
        )
        html = pattern.sub(lambda m, p=new_price: f"{m.group(1)}{p}{m.group(3)}", html, count=1)

    # Samurai featured block uses same span class.
    sam_adult = card_price_text(lang, PRICES["samurai"]["adult"])
    html = re.sub(
        r'(<a[^>]+class="samurai-featured[^"]*"[^>]*>[\s\S]*?<span class="detail-value price">)([^<]+)(</span>)',
        lambda m, p=sam_adult: f"{m.group(1)}{p}{m.group(3)}",
        html,
        count=1,
        flags=re.MULTILINE,
    )
    return html


def main() -> int:
    updated = 0

    # Patch experience list pages
    for lang in LANGS:
        p = REPO / lang / "experiences" / "index.html"
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        out = patch_experiences_index_cards(src, lang)
        if out != src:
            p.write_text(out, encoding="utf-8")
            updated += 1

    # Patch detail pages
    for lang in LANGS:
        for slug in SLUGS:
            p = REPO / lang / "experiences" / slug / "index.html"
            if not p.exists():
                continue
            src = p.read_text(encoding="utf-8")
            out = patch_detail_pricing(src, lang, slug)
            if out != src:
                p.write_text(out, encoding="utf-8")
                updated += 1

    print(f"Updated {updated} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

