#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

LANGS = ("ja", "en", "zh-cn", "zh-tw")
SLUGS = ("samurai", "kyudo", "kendo", "iaido", "karate", "chado", "taiko", "bonseki", "kado", "takigyo")


# Every experience is a list of (label key, amount) rows, in display order.
# A list - rather than a fixed adult/child pair - is what lets kado keep its
# group-size tiers and lets takigyo have no child row at all, instead of the
# generator inventing rows that the pages never showed.
#
# "per_person" swaps the tax note for the per-person variant, which is the
# markup kado uses because its tiers are per-head rates.
PRICES = {
    "samurai": {"rows": [("adult", 35000), ("child", 17500)]},
    "kyudo": {"rows": [("adult", 15000), ("child", 7500)]},
    "kendo": {"rows": [("adult", 15000), ("child", 7500)]},
    "iaido": {"rows": [("adult", 15000), ("child", 7500)]},
    "karate": {"rows": [("adult", 15000), ("child", 7500)]},
    "chado": {"rows": [("adult", 10000), ("child", 5000)]},
    "taiko": {"rows": [("adult", 12000), ("child", 6000)]},
    "bonseki": {"rows": [("adult", 12000), ("child", 6000)]},
    "kado": {
        "rows": [("adult_1", 22500), ("adult_2_3", 22500), ("adult_4_8", 12500)],
        "per_person": True,
    },
    "takigyo": {"rows": [("adult", 5000)]},
}

# Row labels per language. zh-tw needs its own entry: falling through to a
# default used to put Japanese ("大人" / "子ども") on the Traditional Chinese
# pages.
LABELS = {
    "ja": {
        "adult": "大人（1名）",
        "child": "子ども（8歳〜11歳）",
        "adult_1": "大人（1名）",
        "adult_2_3": "大人（2名〜3名）",
        "adult_4_8": "大人（4名〜8名）",
    },
    "en": {
        "adult": "Adult (1 guest)",
        "child": "Child (ages 8–11)",
        "adult_1": "Adult (1 guest)",
        "adult_2_3": "Adults (2–3 guests)",
        "adult_4_8": "Adults (4–8 guests)",
    },
    "zh-cn": {
        "adult": "成人（1名）",
        "child": "儿童（8〜11岁）",
        "adult_1": "成人（1名）",
        "adult_2_3": "成人（2〜3名）",
        "adult_4_8": "成人（4〜8名）",
    },
    "zh-tw": {
        "adult": "成人（1名）",
        "child": "兒童（8〜11歲）",
        "adult_1": "成人（1名）",
        "adult_2_3": "成人（2〜3名）",
        "adult_4_8": "成人（4〜8名）",
    },
}

TAX_NOTE = {"ja": "税込", "en": "Tax included", "zh-cn": "含税", "zh-tw": "含稅"}
PER_PERSON_NOTE = {
    "ja": "（税込）/１名",
    "en": "(inc. tax) / per person",
    "zh-cn": "（含税）/1名",
    "zh-tw": "（含稅）/1名",
}


def adult_price(slug: str) -> int:
    """The headline rate, used on the experience list cards."""
    return PRICES[slug]["rows"][0][1]


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
    return (LABELS[lang]["adult"], LABELS[lang]["child"])


def pricing_note(lang: str, slug: str | None = None) -> str:
    if slug is not None and PRICES[slug].get("per_person"):
        return PER_PERSON_NOTE[lang]
    return TAX_NOTE[lang]


def build_pricing_grid(lang: str, slug: str) -> str:
    per_person = bool(PRICES[slug].get("per_person"))
    note_class = "price-per-person" if per_person else "note"
    note = pricing_note(lang, slug)

    items = []
    for key, amount in PRICES[slug]["rows"]:
        items.append(
            "                    <div class=\"pricing-item\">\n"
            f"                        <h3>{LABELS[lang][key]}</h3>\n"
            f"                        <div class=\"price\">{fmt_yen(amount)}</div>\n"
            f"                        <div class=\"{note_class}\">{note}</div>\n"
            "                    </div>"
        )
    return "\n".join(items)


PRICING_GRID_RE = re.compile(
    r"(?P<open><div class=\"pricing-grid\">\s*\n)(?P<body>[\s\S]*?)(?P<close>\n\s*</div>\s*\n\s*<div class=\"pricing-details\">)",
    re.MULTILINE,
)


def patch_detail_pricing(html: str, lang: str, slug: str) -> str:
    """Rewrite the visible pricing grid from PRICES.

    Regenerating a page that already matches PRICES is a no-op; the grid is
    rebuilt row for row from PRICES[slug]["rows"], so tiers, row counts and the
    per-person note all survive.
    """
    m = PRICING_GRID_RE.search(html)
    if not m:
        return html
    new_body = build_pricing_grid(lang, slug)
    return html[: m.start("body")] + new_body + html[m.end("body") :]


def patch_experiences_index_cards(html: str, lang: str) -> str:
    # Update all experience cards prices based on href to each slug.
    for slug in SLUGS:
        new_price = card_price_text(lang, adult_price(slug))

        # Replace first price span inside the anchor card block for this slug.
        # Keep it conservative: anchor includes href to slug, then find first price span inside.
        pattern = re.compile(
            rf'(<a[^>]+href="[^"]*{re.escape(slug)}/"[^>]*>[\s\S]*?<span class="detail-value price">)([^<]+)(</span>)',
            re.MULTILINE,
        )
        html = pattern.sub(lambda m, p=new_price: f"{m.group(1)}{p}{m.group(3)}", html, count=1)

    # Samurai featured block uses same span class.
    sam_adult = card_price_text(lang, adult_price("samurai"))
    html = re.sub(
        r'(<a[^>]+class="samurai-featured[^"]*"[^>]*>[\s\S]*?<span class="detail-value price">)([^<]+)(</span>)',
        lambda m, p=sam_adult: f"{m.group(1)}{p}{m.group(3)}",
        html,
        count=1,
        flags=re.MULTILINE,
    )
    return html



# ---------------------------------------------------------------------------
# Service JSON-LD for the experience detail pages.
#
# The offers are read back out of each page's rendered pricing grid rather than
# straight from PRICES. PRICES still drives that grid, so the chain stays
# PRICES -> visible price -> structured data; reading the last link off the
# page guarantees the markup can never advertise a price the visitor is not
# shown, which is what Google requires. It also keeps the pages that carry a
# shape PRICES cannot express (kado's group tiers) correct.
# ---------------------------------------------------------------------------

SERVICE_START = "<!-- MEIHODO-SERVICE-JSONLD -->"
SERVICE_END = "<!-- /MEIHODO-SERVICE-JSONLD -->"

BRAND = {"ja": "鳴鳳堂", "en": "Meihodo", "zh-cn": "鸣凤堂", "zh-tw": "鳴鳳堂"}
AREA_SERVED = {"ja": "阿蘇市", "en": "Aso", "zh-cn": "阿苏市", "zh-tw": "阿蘇市"}

# Fallback only; the real link is read off each page so the two cannot diverge.
ASOVIEW = {
    "ja": "https://www.asoview.com/channel/activities/ja/meihodo/offices/4369/courses?language_type=ja",
    "en": "https://www.asoview.com/channel/activities/ja/meihodo/offices/4369/courses?language_type=en",
    "zh-cn": "https://www.asoview.com/channel/activities/ja/meihodo/offices/4369/courses?language_type=zh-CN",
    "zh-tw": "https://www.asoview.com/channel/activities/ja/meihodo/offices/4369/courses?language_type=zh-TW",
}

TITLE_RE = re.compile(r"<title>\s*(.*?)\s*</title>", re.S)
SUBTITLE_RE = re.compile(r'<p class="[a-z-]*subtitle"[^>]*>\s*([^<]{10,400}?)\s*</p>', re.S)
ASOVIEW_RE = re.compile(r"https://www\.asoview\.com/[^\"']*courses\?language_type=[A-Za-z-]+")
PRICING_ITEM_RE = re.compile(
    r'<div class="pricing-item">\s*<h3>(?P<label>.*?)</h3>\s*<div class="price">(?P<price>.*?)</div>',
    re.S,
)
# The leading indentation is part of the match: leaving it behind made every
# re-run insert the fresh block after the old block's whitespace, walking the
# marker four spaces further right each time.
SERVICE_BLOCK_RE = re.compile(
    r"[ \t]*" + re.escape(SERVICE_START) + r".*?" + re.escape(SERVICE_END) + r"\n?", re.S
)


def _flat(text: str) -> str:
    return " ".join(text.split())


def service_type(html: str) -> str | None:
    """The experience name, taken from the page <title> so it tracks the page."""
    title = TITLE_RE.search(html)
    if not title:
        return None
    name = _flat(title.group(1))
    for sep in (" | ", " - ", " – "):
        if sep in name:
            name = name.split(sep)[0]
            break
    return name.strip() or None


def service_description(html: str) -> str | None:
    m = SUBTITLE_RE.search(html)
    return _flat(m.group(1)) if m else None


def booking_url(html: str, lang: str) -> str:
    m = ASOVIEW_RE.search(html)
    return m.group(0) if m else ASOVIEW[lang]


def rendered_offers(html: str, url: str) -> list:
    """Every priced row of the page's own pricing grid, as schema.org Offers."""
    offers = []
    for m in PRICING_ITEM_RE.finditer(html):
        label = _flat(m.group("label"))
        amount = re.sub(r"[^0-9]", "", m.group("price"))
        if not amount:
            # A row rendered as "-" carries no price (e.g. takigyo has no
            # child rate); advertising one would misstate the offer.
            continue
        offers.append(
            {
                "@type": "Offer",
                "name": label,
                "price": amount,
                "priceCurrency": "JPY",
                "availability": "https://schema.org/InStock",
                "url": url,
            }
        )
    return offers


def build_service_jsonld(html: str, lang: str, slug: str) -> str | None:
    name = service_type(html)
    desc = service_description(html)
    if not name or not desc:
        return None
    url = booking_url(html, lang)
    offers = rendered_offers(html, url)
    if not offers:
        return None
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": name,
        "name": f"{name} - {BRAND[lang]}",
        "url": f"https://www.meihodo.com/{lang}/experiences/{slug}/",
        "description": desc,
        "provider": {
            "@type": "LodgingBusiness",
            "@id": "https://www.meihodo.com/#lodgingbusiness",
            "name": BRAND[lang],
            "url": "https://www.meihodo.com/",
        },
        "areaServed": {"@type": "City", "name": AREA_SERVED[lang]},
        "availableLanguage": ["ja", "en", "zh-Hans", "zh-Hant"],
        "offers": offers,
    }
    body = json.dumps(data, ensure_ascii=False, indent=2)
    body = "\n".join("    " + ln for ln in body.split("\n"))
    return (
        f"    {SERVICE_START}\n"
        '    <script type="application/ld+json">\n'
        f"{body}\n"
        "    </script>\n"
        f"    {SERVICE_END}\n"
    )


def patch_service_jsonld(html: str, lang: str, slug: str) -> str:
    block = build_service_jsonld(html, lang, slug)
    if block is None or "</head>" not in html:
        return html
    html = SERVICE_BLOCK_RE.sub("", html)
    return html.replace("</head>", block + "</head>", 1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--jsonld-only",
        action="store_true",
        help=(
            "Only refresh the Service JSON-LD; leave the visible pricing grid "
            "untouched. Use this until build_pricing_grid matches the pages "
            "again - see the note on patch_detail_pricing."
        ),
    )
    args = ap.parse_args(argv)
    updated = 0

    # Patch experience list pages
    for lang in LANGS:
        p = REPO / lang / "experiences" / "index.html"
        if not p.exists():
            continue
        if args.jsonld_only:
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
            out = src if args.jsonld_only else patch_detail_pricing(src, lang, slug)
            out = patch_service_jsonld(out, lang, slug)
            if out != src:
                p.write_text(out, encoding="utf-8")
                updated += 1

    print(f"Updated {updated} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

