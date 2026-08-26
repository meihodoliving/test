#!/usr/bin/env python3
"""Inject Accommodation JSON-LD into the six lodging-building pages.

Each building gets a booking link (offers.url) pointing at the room's own deep
link into the hpdsp reservation system, mirroring how the experience pages point
at asoview. The link is read off the page so the two cannot drift apart.

No price is published. The pages state the rates are "1室8名様利用時の1名様の価格"
and seasonal, so a bare price/lowPrice would misstate what a visitor is quoted.

schema.org's Accommodation descends from Place and has no offers property, so
each building is typed as both Accommodation and Product; that is what makes
offers valid here.

Idempotent: an existing block is replaced, not duplicated.
Run: python3 scripts/add_accommodation_jsonld.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = "https://www.meihodo.com"

LANGS = ("ja", "en", "zh-cn", "zh-tw")
# seiseikan/ is deliberately absent: vercel.json 301s it to seiseisya, so a
# block there would never be served.
ROOMS = ("geihinkan", "korokan", "edokan", "bunshinkan", "seiseisya", "hinokinoma")

BRAND = {"ja": "鳴鳳堂", "en": "Meihodo", "zh-cn": "鸣凤堂", "zh-tw": "鳴鳳堂"}

START = "<!-- MEIHODO-ACCOMMODATION-JSONLD -->"
END = "<!-- /MEIHODO-ACCOMMODATION-JSONLD -->"

TITLE_RE = re.compile(r"<title>\s*(.*?)\s*</title>", re.S)
# Only the ja pages spell the capacity out in a parseable way; occupancy is a
# property of the building, so the ja value is reused for every language.
OCCUPANCY_RE = re.compile(r"最大[^0-9]{0,12}([0-9]{1,2})\s*名様")
DEEP_LINK_RE = re.compile(
    r"https://www\.hpdsp\.net/[^\"']*hww3201init\.do\?[^\"']*roomTypeCd=[0-9]+[^\"']*"
)
GENERAL_LINK_RE = re.compile(r"https://www\.hpdsp\.net/[^\"']*hww3101\.do\?yadNo=[0-9]+")
BLOCK_RE = re.compile(r"[ \t]*" + re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)


def page_name(html: str) -> str | None:
    m = TITLE_RE.search(html)
    if not m:
        return None
    name = " ".join(m.group(1).split())
    for sep in (" | ", " - ", " – "):
        if sep in name:
            name = name.split(sep)[0]
            break
    return name.strip() or None


def booking_url(html: str) -> str | None:
    """Prefer the room's own deep link over the property-wide booking page."""
    m = DEEP_LINK_RE.search(html) or GENERAL_LINK_RE.search(html)
    return m.group(0) if m else None


def occupancy_for(room: str) -> int | None:
    ja = REPO / "ja" / room / "index.html"
    if not ja.exists():
        return None
    m = OCCUPANCY_RE.search(ja.read_text(encoding="utf-8"))
    return int(m.group(1)) if m else None


def build_block(html: str, lang: str, room: str, max_guests: int | None) -> str | None:
    name = page_name(html)
    url = booking_url(html)
    if not name or not url:
        return None
    data = {
        "@context": "https://schema.org",
        "@type": ["Accommodation", "Product"],
        "@id": f"{BASE}/{lang}/{room}/#accommodation",
        "name": name,
        "url": f"{BASE}/{lang}/{room}/",
        "containedInPlace": {
            "@type": "LodgingBusiness",
            "@id": f"{BASE}/#lodgingbusiness",
            "name": BRAND[lang],
            "url": f"{BASE}/",
        },
        "offers": {
            "@type": "Offer",
            "priceCurrency": "JPY",
            "availability": "https://schema.org/InStock",
            "url": url,
        },
    }
    if max_guests:
        data["occupancy"] = {
            "@type": "QuantitativeValue",
            "maxValue": max_guests,
            "unitText": "person",
        }
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
    for room in ROOMS:
        max_guests = occupancy_for(room)
        for lang in LANGS:
            path = REPO / lang / room / "index.html"
            if not path.exists():
                print(f"  missing: {lang}/{room}")
                continue
            src = path.read_text(encoding="utf-8")
            block = build_block(src, lang, room, max_guests)
            if block is None or "</head>" not in src:
                print(f"  skipped (no title/booking link): {lang}/{room}")
                continue
            out = BLOCK_RE.sub("", src)
            out = out.replace("</head>", block + "</head>", 1)
            if out != src:
                path.write_text(out, encoding="utf-8")
                updated += 1
    print(f"Updated {updated} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
