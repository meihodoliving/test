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
    "things-to-do": {
        "ja": "鳴鳳堂での過ごし方", "en": "Things to Do",
        "zh-cn": "鸣凤堂的度过方式", "zh-tw": "鳴鳳堂的度過方式",
    },
    "restaurant": {"ja": "料亭 鳴鳳堂", "en": "Ryotei Meihodo", "zh-cn": "料亭 鸣凤堂", "zh-tw": "料亭 鳴鳳堂"},
    # The 阿蘇ふっこう割 campaign page now has a translated edition in every
    # language tree, so the label is carried in all four. The promotion is run
    # by 阿蘇市 and its own page states no residency condition - the campaign
    # name is transliterated rather than replaced so a guest can quote it.
    "campaign-aso-fukkou": {
        "ja": "阿蘇ふっこう割（熊本応援キャンペーン）",
        "en": "Aso Fukko-wari (Support Kumamoto Campaign)",
        "zh-cn": "阿苏复兴折扣（熊本应援活动）",
        "zh-tw": "阿蘇復興折扣（熊本應援活動）",
    },
    "information": {"ja": "お知らせ", "en": "News", "zh-cn": "最新消息", "zh-tw": "最新消息"},
    # Breadcrumb leaf for the 阿蘇山・中岳 alert-level article. Shortened from
    # the headline so the trail stays readable; the full headline is the
    # article's own <h1>. Each string is the one its page actually renders in
    # .breadcrumb-current, so the visible trail and the BreadcrumbList agree.
    "news-aso-nakadake-alert-level-2": {
        "ja": "阿蘇山・中岳の噴火警戒レベル引き下げについて",
        "en": "About the Nakadake eruption alert level being lowered",
        "zh-cn": "关于阿苏山中岳喷发警戒等级下调",
        "zh-tw": "關於阿蘇山中岳噴發警戒等級下調",
    },
}


# ---------------------------------------------------------------------------
# The 阿蘇ふっこう割 announcement.
#
# The campaign page is a dated announcement, not a standing description of a
# facility, so it carries an Article node of its own on top of the usual
# WebPage. Every literal here is readable on
# https://www.meihodo.com/ja/campaign/aso-fukkou itself - the headline is the
# page's own <h1>/<title>, the dates are the campaign dates the page states,
# and the image is the banner it shows.
#
# datePublished / dateModified are NOT stamped from the clock: they are the
# dates this page was published and last edited, kept here by hand so a
# regenerate does not silently claim the article is fresher than it is.
# ---------------------------------------------------------------------------
CAMPAIGN_PATH = "ja/campaign/aso-fukkou/index.html"
# The page now exists in four languages. Fields a reader sees - the headline,
# the campaign's name, the organiser - are keyed by language so each edition
# describes itself in its own words; the dates and the image are facts and stay
# shared. The campaign's @id does NOT vary: it is one real-world promotion.
CAMPAIGN_ARTICLE = {
    "headline": {
        "ja": "【阿蘇ふっこう割】阿蘇に泊まって支える！熊本応援キャンペーン｜鳴鳳堂",
        "en": "[Aso Fukko-wari] Stay in Aso and support Kumamoto | Meihodo",
        "zh-cn": "【阿苏复兴折扣】住在阿苏，支援熊本！熊本应援活动｜鸣凤堂",
        "zh-tw": "【阿蘇復興折扣】住在阿蘇，支援熊本！熊本應援活動｜鳴鳳堂",
    },
    "alternativeHeadline": {
        "ja": "鳴鳳堂は阿蘇ふっこう割（熊本応援キャンペーン）の対象宿泊施設です",
        "en": "Meihodo is a participating property in the Aso Fukko-wari (Support Kumamoto Campaign)",
        "zh-cn": "鸣凤堂是阿苏复兴折扣（熊本应援活动）的指定住宿设施",
        "zh-tw": "鳴鳳堂是阿蘇復興折扣（熊本應援活動）的指定住宿設施",
    },
    "datePublished": "2026-09-01",
    "dateModified": "2026-09-01",
    "image": f"{BASE}/images/top/web_banner.png",
    "keywords": {
        "ja": [
            "阿蘇ふっこう割", "熊本応援キャンペーン", "阿蘇に泊まって支える", "阿蘇市",
            "鳴鳳堂", "Meihodo", "対象宿泊施設", "宿泊割引", "地域クーポン", "熊本県阿蘇市",
        ],
        "en": [
            "Aso Fukko-wari", "Support Kumamoto Campaign", "Stay in Aso and support Kumamoto",
            "Aso City", "Meihodo", "participating property", "accommodation discount",
            "local coupons", "Aso Kumamoto",
        ],
        "zh-cn": [
            "阿苏复兴折扣", "熊本应援活动", "住在阿苏支援熊本", "阿苏市", "鸣凤堂", "Meihodo",
            "指定住宿设施", "住宿折扣", "地区优惠券", "熊本县阿苏市",
        ],
        "zh-tw": [
            "阿蘇復興折扣", "熊本應援活動", "住在阿蘇支援熊本", "阿蘇市", "鳴鳳堂", "Meihodo",
            "指定住宿設施", "住宿折扣", "地區優惠券", "熊本縣阿蘇市",
        ],
    },
    # The campaign itself, as an entity the article is about. Its @id is
    # language-neutral like the other real-world entities in the graph.
    "campaign_name": {
        "ja": "阿蘇に泊まって支える！熊本応援キャンペーン（阿蘇ふっこう割）",
        "en": "Stay in Aso and support Kumamoto (Aso Fukko-wari)",
        "zh-cn": "住在阿苏，支援熊本！熊本应援活动（阿苏复兴折扣）",
        "zh-tw": "住在阿蘇，支援熊本！熊本應援活動（阿蘇復興折扣）",
    },
    "campaign_alt": {
        "ja": ["阿蘇ふっこう割", "熊本応援キャンペーン"],
        "en": ["Aso Fukko-wari", "Support Kumamoto Campaign"],
        "zh-cn": ["阿苏复兴折扣", "熊本应援活动"],
        "zh-tw": ["阿蘇復興折扣", "熊本應援活動"],
    },
    "campaign_start": "2026-09-07",
    "campaign_end": "2026-09-30",
    "organizer": {"ja": "阿蘇市", "en": "Aso City", "zh-cn": "阿苏市", "zh-tw": "阿蘇市"},
}

ID_CAMPAIGN = f"{BASE}/#aso-fukkou-campaign"


# ---------------------------------------------------------------------------
# The 阿蘇山・中岳 噴火警戒レベル引き下げ announcement.
#
# Same shape as the campaign entry above: a dated announcement gets an Article
# node on top of the usual WebPage. Every literal is readable on
# https://www.meihodo.com/ja/information/aso-nakadake-alert-level-2 itself -
# the announcing body, the date and time, the two alert levels and the road
# reopening are the facts that page states, and nothing here goes further than
# the page does. In particular nothing asserts that the volcano is safe or
# that activity has ended: 鳴鳳堂 is not the authority on that, and the page
# points at 阿蘇市公式ホームページ for the current situation.
#
# datePublished / dateModified are kept by hand, not stamped from the clock.
# ---------------------------------------------------------------------------
NEWS_ALERT_PATH = "ja/information/aso-nakadake-alert-level-2/index.html"
NEWS_ALERT_ARTICLE = {
    "headline": {
        "ja": "阿蘇山・中岳の噴火警戒レベルが「3」から「2」へ引き下げられました｜鳴鳳堂",
        "en": "Mount Aso Nakadake eruption alert level lowered from 3 to 2 | Meihodo",
        "zh-cn": "阿苏山中岳的喷发警戒等级由「3」下调至「2」｜鸣凤堂",
        "zh-tw": "阿蘇山中岳的噴發警戒等級由「3」下調至「2」｜鳴鳳堂",
    },
    "alternativeHeadline": {
        "ja": "福岡管区気象台が阿蘇山・中岳の噴火警戒レベルを2へ引き下げ、阿蘇山上広場までの通行が再開",
        "en": ("The Fukuoka Regional Headquarters lowered the Nakadake eruption alert level to 2, "
               "and access as far as Aso Sanjo Plaza has reopened"),
        "zh-cn": "福冈管区气象台将阿苏山中岳的喷发警戒等级下调至2，通往阿苏山上广场的道路恢复通行",
        "zh-tw": "福岡管區氣象台將阿蘇山中岳的噴發警戒等級下調至2，通往阿蘇山上廣場的道路恢復通行",
    },
    "datePublished": "2026-09-01",
    "dateModified": "2026-09-01",
    "keywords": {
        "ja": [
            "阿蘇山", "中岳", "噴火警戒レベル", "噴火警戒レベル2", "噴火警戒レベル引き下げ",
            "火口周辺規制", "阿蘇山上広場", "阿蘇観光", "阿蘇市", "鳴鳳堂",
        ],
        "en": [
            "Mount Aso", "Nakadake", "eruption alert level", "eruption alert level 2",
            "alert level lowered", "do not approach the crater", "Aso Sanjo Plaza",
            "Aso sightseeing", "Aso City", "Meihodo",
        ],
        "zh-cn": [
            "阿苏山", "中岳", "喷发警戒等级", "喷发警戒等级2", "喷发警戒等级下调",
            "限制靠近火山口", "阿苏山上广场", "阿苏观光", "阿苏市", "鸣凤堂",
        ],
        "zh-tw": [
            "阿蘇山", "中岳", "噴發警戒等級", "噴發警戒等級2", "噴發警戒等級下調",
            "限制靠近火山口", "阿蘇山上廣場", "阿蘇觀光", "阿蘇市", "鳴鳳堂",
        ],
    },
    # Category shown on the card in each /information/ index - kept here so the
    # JSON-LD articleSection and the visible label cannot drift apart.
    "section": {"ja": "その他", "en": "Other", "zh-cn": "其他", "zh-tw": "其他"},
}

# The volcano the article is about, as an entity of its own. Name and
# alternate names only: the article states no coordinates or boundaries, and a
# guessed geo box would be a fact the site does not publish.
ID_NAKADAKE = f"{BASE}/#aso-nakadake"


# ---------------------------------------------------------------------------
# Meta-description overrides.
#
# build_head_meta.py normally reads a page's own first substantial paragraph.
# Where an editor has written a better summary than the prose yields, it goes
# here - keyed by repo-relative path - so the value survives a regenerate
# instead of having to be re-typed into the generated block every run.
# ---------------------------------------------------------------------------
PAGE_DESCRIPTIONS = {
    "ja/things-to-do/index.html": (
        "熊本県阿蘇市の鳴鳳堂は、泊まりながら弓道・剣道・空手・試し切り・茶道・盆石・"
        "和太鼓などの日本文化体験を楽しめる文化リゾートです。茶道・盆石・剣道・空手は"
        "茶室や大講堂、武道場など屋内で行うため、雨の日の阿蘇観光でも旅の予定を"
        "組み立てやすいのが特徴です。宿泊・食事・文化体験が敷地内で完結する"
        "1日の過ごし方をご紹介します。"
    ),
    "en/things-to-do/index.html": (
        "Meihodo in Aso, Kumamoto is a cultural resort where you stay and take part: "
        "kyudo, kendo, karate, tameshigiri, tea ceremony, bonseki and taiko. Tea "
        "ceremony, bonseki, kendo and karate are held indoors, in the tea house, the "
        "great hall and the martial arts hall, so a rainy day in Aso stays easy to plan "
        "around. Lodging, dining and Japanese culture on one estate."
    ),
    "zh-cn/things-to-do/index.html": (
        "位于熊本县阿苏市的鸣凤堂，是可以一边住宿一边体验弓道、剑道、空手道、试斩、"
        "茶道、盆石、和太鼓等日本文化的文化度假设施。其中茶道、盆石、剑道、空手道在茶室、"
        "大讲堂、武道场等室内举行，即使阿苏遇上雨天也便于安排行程。"
        "住宿、餐饮与文化体验都在同一片园区内完成。"
    ),
    "zh-tw/things-to-do/index.html": (
        "位於熊本縣阿蘇市的鳴鳳堂，是可以一邊住宿一邊體驗弓道、劍道、空手道、試斬、"
        "茶道、盆石、和太鼓等日本文化的文化度假設施。其中茶道、盆石、劍道、空手道於茶室、"
        "大講堂、武道場等室內舉行，即使阿蘇遇上雨天也便於安排行程。"
        "住宿、餐飲與文化體驗都在同一片園區內完成。"
    ),
    CAMPAIGN_PATH: (
        "熊本県阿蘇市の文化リゾート鳴鳳堂は、阿蘇市が実施する"
        "「阿蘇に泊まって支える！熊本応援キャンペーン（阿蘇ふっこう割）」の"
        "対象宿泊施設です。2026年9月7日～9月30日の対象宿泊について、"
        "1名1泊あたり最大5,000円の宿泊割引と2,000円分の地域クーポンを"
        "ご利用いただけます。ご予約はメールまたはお電話での直接予約のみの受付です。"
    ),
    NEWS_ALERT_PATH: (
        "2026年9月1日16時00分、福岡管区気象台は阿蘇山・中岳の噴火警戒レベルを"
        "「3（入山規制）」から「2（火口周辺規制）」へ引き下げました。"
        "9月2日午前9時より阿蘇山上広場までの通行が再開されています。"
        "火口周辺では引き続き規制がありますので、阿蘇観光の際は最新の火山情報・"
        "交通情報をご確認ください。熊本県阿蘇市の鳴鳳堂からのお知らせです。"
    ),

    # The translated editions of the two announcements and of the news index.
    # Each is a rendering of the ja summary above it - same facts, same dates,
    # same figures - so the four language editions cannot drift apart.
    "en/information/index.html": (
        "The latest news from Meihodo in Aso, Kumamoto: announcements about stays, "
        "cultural experiences, the restaurant, events, campaigns and how the estate "
        "is operating."
    ),
    "zh-cn/information/index.html": (
        "熊本县阿苏市鸣凤堂的最新消息。您可在此确认住宿、文化体验、餐厅、活动、"
        "优惠企划与设施营运等相关通知。"
    ),
    "zh-tw/information/index.html": (
        "熊本縣阿蘇市鳴鳳堂的最新消息。您可在此確認住宿、文化體驗、餐廳、活動、"
        "優惠企劃與設施營運等相關通知。"
    ),
    "en/information/aso-nakadake-alert-level-2/index.html": (
        "At 16:00 on 1 September 2026 the Fukuoka Regional Headquarters of the Japan "
        "Meteorological Agency lowered the eruption alert level for Mount Aso's "
        "Nakadake from 3 (do not approach the volcano) to 2 (do not approach the "
        "crater). Access as far as Aso Sanjo Plaza reopened at 9:00 a.m. on "
        "2 September. Restrictions remain around the crater, so please check the "
        "latest volcanic and traffic information when travelling in Aso. An "
        "announcement from Meihodo in Aso, Kumamoto."
    ),
    "zh-cn/information/aso-nakadake-alert-level-2/index.html": (
        "2026年9月1日16时00分，福冈管区气象台将阿苏山中岳的喷发警戒等级由"
        "「3（限制入山）」下调至「2（限制靠近火山口）」。自9月2日上午9时起，"
        "通往阿苏山上广场的道路已恢复通行。火山口周边仍持续设有管制，"
        "前往阿苏观光时请确认最新的火山信息与交通信息。此为熊本县阿苏市鸣凤堂的通知。"
    ),
    "zh-tw/information/aso-nakadake-alert-level-2/index.html": (
        "2026年9月1日16時00分，福岡管區氣象台將阿蘇山中岳的噴發警戒等級由"
        "「3（限制入山）」下調至「2（限制靠近火山口）」。自9月2日上午9時起，"
        "通往阿蘇山上廣場的道路已恢復通行。火山口周邊仍持續設有管制，"
        "前往阿蘇觀光時請確認最新的火山資訊與交通資訊。此為熊本縣阿蘇市鳴鳳堂的通知。"
    ),
    "en/campaign/aso-fukkou/index.html": (
        "Meihodo, a cultural resort in Aso City, Kumamoto, is a participating property "
        "in the \u201cStay in Aso and support Kumamoto\u201d campaign (Aso Fukko-wari) run by "
        "Aso City. For qualifying stays from 7 to 30 September 2026, guests receive up "
        "to \u00a55,000 off per person per night plus \u00a52,000 in local coupons. Bookings are "
        "accepted only as direct bookings by email or phone."
    ),
    "zh-cn/campaign/aso-fukkou/index.html": (
        "熊本县阿苏市的文化度假设施鸣凤堂，是阿苏市推行的「住在阿苏，支援熊本！"
        "熊本应援活动（阿苏复兴折扣）」的指定住宿设施。2026年9月7日～9月30日的"
        "适用住宿，每人每晚最多可享5,000日元的住宿折扣与2,000日元的地区优惠券。"
        "预订仅受理通过电子邮件或电话的直接预订。"
    ),
    "zh-tw/campaign/aso-fukkou/index.html": (
        "熊本縣阿蘇市的文化度假設施鳴鳳堂，是阿蘇市推行的「住在阿蘇，支援熊本！"
        "熊本應援活動（阿蘇復興折扣）」的指定住宿設施。2026年9月7日～9月30日的"
        "適用住宿，每人每晚最多可享5,000日圓的住宿折扣與2,000日圓的地區優惠券。"
        "預約僅受理透過電子郵件或電話的直接預約。"
    ),
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
    # 「鳴鳳堂での過ごし方」 - the stay-and-experience guide. A section page like
    # the rest: one directory per language, one canonical each, in the sitemap.
    "things-to-do",
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

        # The news index and the articles under it. Every language tree now
        # carries all three, so they go through the same loop as the rest and
        # alternates_for() finds a sibling in each language instead of
        # advertising ja alone.
        info_path = f"{lang}/information/index.html"
        pages.append(Page(
            info_path, lang, "information", "information",
            canonical_for(info_path), True,
            _crumb(lang, (CRUMB["information"][lang], canonical_for(info_path)))))

        news_path = f"{lang}/information/aso-nakadake-alert-level-2/index.html"
        pages.append(Page(
            news_path, lang, "news", "aso-nakadake-alert-level-2",
            canonical_for(news_path), True,
            _crumb(lang,
                   (CRUMB["information"][lang], canonical_for(info_path)),
                   (CRUMB["news-aso-nakadake-alert-level-2"][lang], canonical_for(news_path)))))

        # The 阿蘇ふっこう割 announcement. It sits under /campaign/, not under
        # the news index, which is why its trail is home -> campaign rather
        # than home -> news.
        campaign_path = f"{lang}/campaign/aso-fukkou/index.html"
        pages.append(Page(
            campaign_path, lang, "campaign", "aso-fukkou",
            canonical_for(campaign_path), True,
            _crumb(lang, (CRUMB["campaign-aso-fukkou"][lang], canonical_for(campaign_path)))))

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
