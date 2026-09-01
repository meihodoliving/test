#!/usr/bin/env python3
"""Single source of truth for every SEO / AEO fact the generators emit.

Nothing in this file may be invented. Every literal below is either
 - copied from a page that a visitor can read on www.meihodo.com, or
 - a structural fact about the site (URL shapes, which files exist).

If a value cannot be verified on the live site it belongs in
AEO_CONTENT_RECOMMENDATIONS.md as a request to the operator, not here.

Used by build_jsonld.py, build_head_meta.py and build_sitemap.py.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = "https://www.meihodo.com"

LANGS = ("ja", "en", "zh-cn", "zh-tw")

# BCP-47 tags for hreflang / inLanguage. The directory names are lowercase
# slugs; these are the actual language tags.
LANG_TAG = {"ja": "ja", "en": "en", "zh-cn": "zh-Hans", "zh-tw": "zh-Hant"}
HREFLANG = {"ja": "ja", "en": "en", "zh-cn": "zh-Hans", "zh-tw": "zh-Hant"}

# ---------------------------------------------------------------------------
# Stable entity identifiers.
#
# Physical things (the estate, its buildings, the restaurant) and the services
# offered there are ONE entity each, no matter which language page describes
# them, so their @id carries no language segment. Only the document-layer
# nodes (WebPage / BreadcrumbList / FAQPage) are per-URL.
# ---------------------------------------------------------------------------
ID_WEBSITE = f"{BASE}/#website"
ID_ORG = f"{BASE}/#organization"
ID_MEIHODO = f"{BASE}/#meihodo"
ID_RESTAURANT = f"{BASE}/#restaurant"


def entity_id(slug: str) -> str:
    return f"{BASE}/#{slug}"


# ---------------------------------------------------------------------------
# Verified facts.
#
# Address / phone: ja/restaurant/index.html footer and ja/access/index.html.
# Email: the existing root index.html JSON-LD.
# Coordinates: carried over from the JSON-LD already deployed at the root; see
#   AEO_CONTENT_RECOMMENDATIONS.md P0-3, the operator still has to confirm them.
# ---------------------------------------------------------------------------
POSTAL_CODE = "869-2231"
TELEPHONE = "+81-967-24-5090"
TELEPHONE_DISPLAY = "0967-24-5090"
EMAIL = "meihodoliving@gmail.com"
LATITUDE = "32.923696"
LONGITUDE = "131.012587"
HAS_MAP = "https://www.google.com/maps/search/?api=1&query=" "熊本県阿蘇市永草1943-28"

ADDRESS = {
    "ja": {"street": "永草1943-28", "locality": "阿蘇市", "region": "熊本県"},
    "en": {"street": "1943-28 Nagakusa", "locality": "Aso", "region": "Kumamoto"},
    "zh-cn": {"street": "永草1943-28", "locality": "阿苏市", "region": "熊本县"},
    "zh-tw": {"street": "永草1943-28", "locality": "阿蘇市", "region": "熊本縣"},
}

BRAND = {"ja": "鳴鳳堂", "en": "Meihodo", "zh-cn": "鸣凤堂", "zh-tw": "鳴鳳堂"}
ALT_NAMES = {
    "ja": ["Meihodo", "鳴鳳堂 阿蘇"],
    "en": ["鳴鳳堂", "Meihodo Aso"],
    "zh-cn": ["Meihodo", "鳴鳳堂"],
    "zh-tw": ["Meihodo", "鳴鳳堂"],
}

CITY = {"ja": "阿蘇市", "en": "Aso", "zh-cn": "阿苏市", "zh-tw": "阿蘇市"}
REGION = {"ja": "熊本県", "en": "Kumamoto Prefecture", "zh-cn": "熊本县", "zh-tw": "熊本縣"}

LOGO = f"{BASE}/images/top/top.webp"
DEFAULT_IMAGE = f"{BASE}/images/top/top.webp"

# Only accounts that are linked from the site's own footer, and that are the
# facility itself rather than a listing about it, belong in sameAs.
# hpdsp (booking) and asoview (activity booking) are third-party listings, so
# they are attached as subjectOf / Offer.url instead.
SAME_AS = [
    "https://www.instagram.com/meihodo_aso/",
    "https://www.facebook.com/p/%E9%B3%B4%E9%B3%B3%E5%A0%82-Meihodo-100081920688959/",
]

BOOKING_URL = "https://www.hpdsp.net/meihodo/hw/hwp3100/hww3101.do?yadNo=309467"
ACTIVITY_URL = {
    "ja": "https://www.asoview.com/channel/activities/ja/meihodo/offices/4369/courses?language_type=ja",
    "en": "https://www.asoview.com/channel/activities/ja/meihodo/offices/4369/courses?language_type=en",
    "zh-cn": "https://www.asoview.com/channel/activities/ja/meihodo/offices/4369/courses?language_type=zh-CN",
    "zh-tw": "https://www.asoview.com/channel/activities/ja/meihodo/offices/4369/courses?language_type=zh-TW",
}

# Read off ja/about/index.html: "敷地面積56,000平米、37棟からなる文化施設".
SITE_AREA_SQM = 56000
BUILDING_COUNT = 37

# Facility description, per language, condensed from the page each language
# actually shows (ja/about, en/about, ...).
FACILITY_DESCRIPTION = {
    "ja": "熊本県阿蘇市、敷地面積56,000平米・37棟からなる文化施設。弓道・剣道・空手・試し切りなどの武道体験と、茶道・華道・盆石・和太鼓などの伝統文化体験、一棟貸し切りの宿泊棟、料亭、撮影施設の貸出を行っています。",
    "en": "A cultural estate in Aso, Kumamoto, Japan, spanning 56,000 square meters and 37 buildings. Meihodo offers martial-arts experiences such as kyudo, kendo, karate and tameshigiri, traditional cultural experiences such as tea ceremony, ikebana, bonseki and wadaiko, private whole-building lodging, a kaiseki restaurant, and the estate as a photography location.",
    "zh-cn": "位于熊本县阿苏市、占地56,000平方米、由37栋建筑构成的文化设施。提供弓道、剑道、空手道、试斩等武道体验，茶道、华道、盆石、和太鼓等传统文化体验，以及整栋包租的住宿、料亭与拍摄场地租借。",
    "zh-tw": "位於熊本縣阿蘇市、佔地56,000平方公尺、由37棟建築構成的文化設施。提供弓道、劍道、空手道、試斬等武道體驗，茶道、華道、盆石、和太鼓等傳統文化體驗，以及整棟包租的住宿、料亭與拍攝場地租借。",
}

# knowsAbout: the subject areas the site actually teaches and documents.
# Kept to what has a page behind it - this is an expertise claim, not a
# keyword list.
KNOWS_ABOUT = [
    "Japanese traditional culture",
    "Japanese martial arts",
    "Kyudo (Japanese archery)",
    "Kendo",
    "Karate",
    "Tameshigiri (Japanese sword test cutting)",
    "Samurai culture",
    "Japanese tea ceremony (Sado)",
    "Ikebana (Japanese flower arrangement)",
    "Bonseki",
    "Wadaiko (Japanese drumming)",
    "Takigyo (waterfall meditation)",
    "Japanese architecture",
    "Cultural tourism in Aso, Kumamoto",
]

# Amenities visible on ja/about/index.html's facility map.
AMENITIES = {
    "ja": ["武道場", "弓道場", "茶室（青蓮舎）", "大講堂（柔術堂）", "太鼓堂", "お滝場", "鼓楼", "六角堂", "瞑想空間", "料亭", "無料駐車場", "Wi-Fi"],
    "en": ["Martial arts hall", "Kyudo (archery) range", "Tea house (Seirensha)", "Great hall", "Taiko hall", "Waterfall training site", "Drum tower", "Hexagonal hall", "Meditation space", "Kaiseki restaurant", "Free parking", "Wi-Fi"],
    "zh-cn": ["武道场", "弓道场", "茶室（青莲舍）", "大讲堂", "太鼓堂", "瀑布修行场", "鼓楼", "六角堂", "冥想空间", "料亭", "免费停车场", "Wi-Fi"],
    "zh-tw": ["武道場", "弓道場", "茶室（青蓮舍）", "大講堂", "太鼓堂", "瀑布修行場", "鼓樓", "六角堂", "冥想空間", "料亭", "免費停車場", "Wi-Fi"],
}

# ---------------------------------------------------------------------------
# Restaurant - 料亭 鳴鳳堂
# Hours and phone are printed in the footer of every */restaurant/ page.
# ---------------------------------------------------------------------------
RESTAURANT_NAME = {
    "ja": "料亭 鳴鳳堂",
    "en": "Ryotei Meihodo",
    "zh-cn": "料亭 鸣凤堂",
    "zh-tw": "料亭 鳴鳳堂",
}
RESTAURANT_HOURS = [("07:30", "10:00"), ("17:00", "21:00")]
RESTAURANT_IMAGE = f"{BASE}/images/top/ryotei.webp"

# ---------------------------------------------------------------------------
# Lodging buildings. Each is let as a whole building (一棟貸し), so House is
# the accurate type - HotelRoom would say a room inside a hotel, which these
# are not. Booking is expressed as a ReserveAction rather than an Offer; see
# build_jsonld.node_building for why.
#
# `seiseikan` is deliberately absent: vercel.json 301s it to seiseisya.
# ---------------------------------------------------------------------------
BUILDINGS = ("geihinkan", "korokan", "edokan", "bunshinkan", "seiseisya", "hinokinoma")

BUILDING_NAMES = {
    "geihinkan": {"ja": "迎賓館", "en": "Geihinkan", "zh-cn": "迎宾馆", "zh-tw": "迎賓館"},
    "korokan": {"ja": "鴻臚館", "en": "Korokan", "zh-cn": "鸿胪馆", "zh-tw": "鴻臚館"},
    "edokan": {"ja": "江戸館", "en": "Edokan", "zh-cn": "江户馆", "zh-tw": "江戶館"},
    "bunshinkan": {"ja": "文心館", "en": "Bunshinkan", "zh-cn": "文心馆", "zh-tw": "文心館"},
    "seiseisya": {"ja": "清静舎", "en": "Seiseisha", "zh-cn": "清静舍", "zh-tw": "清靜舍"},
    "hinokinoma": {"ja": "檜の間", "en": "Hinoki no Ma", "zh-cn": "桧之间", "zh-tw": "檜之間"},
}

# ---------------------------------------------------------------------------
# Cultural experiences. Names come from each language's own page title.
# Durations are read out of the pages by build_jsonld.py, not hardcoded.
# ---------------------------------------------------------------------------
EXPERIENCES = ("samurai", "kyudo", "kendo", "iaido", "karate", "chado", "taiko", "bonseki", "kado", "takigyo")

# English romanised names, used as alternateName on every language so an AI
# can join the Japanese and English labels for the same practice.
EXPERIENCE_ALT = {
    "samurai": ["Samurai experience", "侍体験"],
    "kyudo": ["Kyudo", "Japanese archery", "弓道"],
    "kendo": ["Kendo", "Japanese swordsmanship", "剣道"],
    "iaido": ["Tameshigiri", "Japanese sword test cutting", "試し切り"],
    "karate": ["Karate", "空手"],
    "chado": ["Chado", "Sado", "Japanese tea ceremony", "茶道"],
    "taiko": ["Wadaiko", "Japanese drumming", "和太鼓"],
    "bonseki": ["Bonseki", "盆石"],
    "kado": ["Kado", "Ikebana", "Japanese flower arrangement", "華道"],
    "takigyo": ["Takigyo", "Waterfall meditation", "滝行"],
}

# Schema.org category for each experience, so the two families stay separable.
EXPERIENCE_CATEGORY = {
    "samurai": "Japanese martial arts",
    "kyudo": "Japanese martial arts",
    "kendo": "Japanese martial arts",
    "iaido": "Japanese martial arts",
    "karate": "Japanese martial arts",
    "chado": "Japanese traditional culture",
    "taiko": "Japanese traditional culture",
    "bonseki": "Japanese traditional culture",
    "kado": "Japanese traditional culture",
    "takigyo": "Japanese traditional culture",
}

# Labels for the two external booking destinations, copied from each language's
# own fixed booking buttons on the home page.
BOOKING_LABEL = {
    "ja": "宿泊予約", "en": "Book stay", "zh-cn": "住宿预订", "zh-tw": "住宿預約",
}
ACTIVITY_LABEL = {
    "ja": "体験予約", "en": "Book an Experience", "zh-cn": "体验预订", "zh-tw": "體驗預約",
}

RESTAURANT_SUBPAGES = (
    "access", "bbq", "breakfast", "chef", "drinks", "faq",
    "gallery", "kaiseki", "policy", "private-dining", "reservation", "sushi",
)

# ---------------------------------------------------------------------------
# Breadcrumb labels.
# ---------------------------------------------------------------------------
CRUMB = {
    "home": {"ja": "ホーム", "en": "Home", "zh-cn": "首页", "zh-tw": "首頁"},
    "about": {"ja": "施設紹介", "en": "About", "zh-cn": "设施介绍", "zh-tw": "設施介紹"},
    "access": {"ja": "アクセス", "en": "Access", "zh-cn": "交通", "zh-tw": "交通"},
    "accommodations": {"ja": "宿泊", "en": "Stay", "zh-cn": "住宿", "zh-tw": "住宿"},
    "experiences": {"ja": "体験プログラム", "en": "Experiences", "zh-cn": "体验项目", "zh-tw": "體驗項目"},
    "location": {"ja": "撮影施設", "en": "Photography", "zh-cn": "拍摄场地", "zh-tw": "拍攝場地"},
    "faq": {"ja": "よくある質問", "en": "FAQ", "zh-cn": "常见问题", "zh-tw": "常見問題"},
    "restaurant": {"ja": "料亭 鳴鳳堂", "en": "Ryotei Meihodo", "zh-cn": "料亭 鸣凤堂", "zh-tw": "料亭 鳴鳳堂"},
    # The 阿蘇ふっこう割 campaign is a domestic (Japanese) promotion and has no
    # translated edition, so this label only ever needs "ja".
    "campaign-aso-fukkou": {"ja": "阿蘇ふっこう割（熊本応援キャンペーン）"},
}


# ---------------------------------------------------------------------------
# The page registry.
#
# Every entry is (relative file path, canonical path). The canonical path is
# the URL that actually answers 200 on Vercel: cleanUrls strips ".html" and
# "/index.html", trailingSlash:false means no trailing slash. A canonical
# pointing at a trailing-slash URL would point at a 308, which is what the
# pre-existing tags did.
# ---------------------------------------------------------------------------
SECTION_PAGES = (
    "about", "access", "accommodations", "experiences", "location", "faq", "restaurant",
)


def canonical_for(path: str) -> str:
    """Map a repo-relative file path to the URL Vercel serves it at."""
    p = path.replace("\\", "/")
    if p == "index.html":
        return f"{BASE}/"
    p = re.sub(r"/index\.html$", "", p)
    p = re.sub(r"\.html$", "", p)
    # A language root ("ja") is the same document as the site root, which is
    # the URL the brand publishes, so it consolidates there.
    return f"{BASE}/{p}"


class Page:
    """One HTML file plus everything the generators need to know about it."""

    __slots__ = ("path", "lang", "kind", "slug", "canonical", "in_sitemap", "crumbs")

    def __init__(self, path, lang, kind, slug, canonical, in_sitemap, crumbs):
        self.path = path
        self.lang = lang
        self.kind = kind
        self.slug = slug
        self.canonical = canonical
        self.in_sitemap = in_sitemap
        self.crumbs = crumbs

    def __repr__(self):
        return f"<Page {self.path} {self.kind}/{self.slug}>"


def _crumb(lang, *steps):
    """Build a breadcrumb trail. Each step is (label, canonical-url-or-None)."""
    trail = [(CRUMB["home"][lang], f"{BASE}/" if lang == "ja" else f"{BASE}/{lang}")]
    trail.extend(steps)
    return trail


def build_registry() -> list[Page]:
    pages: list[Page] = []

    # The Japanese document is published at both "/" and "/ja". They are the
    # same page, so both carry the root canonical and only "/" enters the
    # sitemap.
    pages.append(Page("index.html", "ja", "home", "home", f"{BASE}/", True, _crumb("ja")))

    for lang in LANGS:
        home = f"{BASE}/" if lang == "ja" else f"{BASE}/{lang}"
        if lang != "ja":
            pages.append(Page(f"{lang}/index.html", lang, "home", "home", home, True, _crumb(lang)))
        else:
            # /ja duplicates "/" - consolidate, and keep it out of the sitemap.
            pages.append(Page("ja/index.html", "ja", "home", "home", f"{BASE}/", False, _crumb("ja")))

        for sec in SECTION_PAGES:
            path = f"{lang}/{sec}/index.html"
            pages.append(Page(path, lang, sec, sec, canonical_for(path), True,
                              _crumb(lang, (CRUMB[sec][lang], canonical_for(path)))))

        for slug in EXPERIENCES:
            path = f"{lang}/experiences/{slug}/index.html"
            pages.append(Page(
                path, lang, "experience", slug, canonical_for(path), True,
                _crumb(lang,
                       (CRUMB["experiences"][lang], canonical_for(f"{lang}/experiences/index.html")),
                       (None, canonical_for(path)))))

        for slug in BUILDINGS:
            path = f"{lang}/{slug}/index.html"
            pages.append(Page(
                path, lang, "building", slug, canonical_for(path), True,
                _crumb(lang,
                       (CRUMB["accommodations"][lang], canonical_for(f"{lang}/accommodations/index.html")),
                       (BUILDING_NAMES[slug][lang], canonical_for(path)))))

        for slug in RESTAURANT_SUBPAGES:
            path = f"{lang}/restaurant/{slug}.html"
            pages.append(Page(
                path, lang, "restaurant-sub", slug, canonical_for(path), True,
                _crumb(lang,
                       (CRUMB["restaurant"][lang], canonical_for(f"{lang}/restaurant/index.html")),
                       (None, canonical_for(path)))))

        # location/terms - a real page, kept in the sitemap.
        path = f"{lang}/location/terms.html"
        pages.append(Page(
            path, lang, "terms", "terms", canonical_for(path), True,
            _crumb(lang,
                   (CRUMB["location"][lang], canonical_for(f"{lang}/location/index.html")),
                   (None, canonical_for(path)))))

        # stay/geihinkan.html is an orphan duplicate of the geihinkan building
        # page - nothing links to it but the language switcher inside itself.
        # It stays reachable, consolidates onto the real page, and stays out of
        # the sitemap.
        path = f"{lang}/stay/geihinkan.html"
        pages.append(Page(
            path, lang, "duplicate", "geihinkan",
            canonical_for(f"{lang}/geihinkan/index.html"), False,
            _crumb(lang,
                   (CRUMB["accommodations"][lang], canonical_for(f"{lang}/accommodations/index.html")),
                   (BUILDING_NAMES["geihinkan"][lang], canonical_for(f"{lang}/geihinkan/index.html")))))

    # Japanese-only campaign page. The 阿蘇ふっこう割 promotion is run by Aso
    # City for the domestic market, so there is no /en, /zh-cn or /zh-tw
    # sibling; alternates_for() skips the languages whose file does not exist,
    # which leaves this page advertising ja alone - correct, not a gap.
    campaign_path = "ja/campaign/aso-fukkou/index.html"
    pages.append(Page(
        campaign_path, "ja", "campaign", "aso-fukkou",
        canonical_for(campaign_path), True,
        _crumb("ja", (CRUMB["campaign-aso-fukkou"]["ja"], canonical_for(campaign_path)))))

    # Pre-migration Chinese stubs. lang-switcher.js normalises zh-hans -> zh-cn
    # and zh-hant -> zh-tw, and CLAUDE.md records these as legacy, so they
    # consolidate onto the live restaurant page rather than standing up a
    # second, unlinked Restaurant entity of their own.
    for legacy, live in (("zh-hans", "zh-cn"), ("zh-hant", "zh-tw")):
        path = f"{legacy}/restaurant.html"
        pages.append(Page(
            path, live, "legacy", "restaurant",
            canonical_for(f"{live}/restaurant/index.html"), False,
            _crumb(live, (CRUMB["restaurant"][live],
                          canonical_for(f"{live}/restaurant/index.html")))))

    return pages


def alternates_for(page: Page) -> dict[str, str]:
    """hreflang map for a page: language tag -> canonical URL in that language.

    Returns {} for pages that must not advertise alternates (duplicates).
    """
    if page.kind in ("duplicate", "legacy"):
        return {}
    out = {}
    for lang in LANGS:
        if page.kind == "home":
            url = f"{BASE}/" if lang == "ja" else f"{BASE}/{lang}"
        else:
            sibling = re.sub(r"^[a-z-]+/", f"{lang}/", page.path)
            if not (REPO / sibling).exists():
                continue
            url = canonical_for(sibling)
        out[HREFLANG[lang]] = url
    return out


if __name__ == "__main__":
    reg = build_registry()
    missing = [p.path for p in reg if not (REPO / p.path).exists()]
    print(f"{len(reg)} pages registered, {len(missing)} missing")
    for m in missing:
        print("  MISSING", m)
