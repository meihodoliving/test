#!/usr/bin/env python3
"""Regenerate every JSON-LD block on the site as one connected @graph per page.

Replaces the previous arrangement - a standalone LodgingBusiness copied onto 73
pages, plus unlinked Service / Accommodation / Restaurant / FAQPage islands with
no WebSite, Organization, WebPage or BreadcrumbList around them - with a single
marker-delimited @graph per page whose nodes reference each other by @id.

Everything emitted here is either read off the page being processed or comes
from seo_config.py. No fact is invented: if a page does not state a price, a
duration or a capacity, the corresponding property is omitted rather than
guessed.

Idempotent. Any pre-existing ld+json block, marked or not, is removed first, so
re-running never duplicates or drifts.

Run: python3 scripts/build_jsonld.py [--check]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import seo_config as C
from update_experience_prices import LABELS, PRICES

START = "<!-- MEIHODO-JSONLD -->"
END = "<!-- /MEIHODO-JSONLD -->"

MARKED_RE = re.compile(r"[ \t]*" + re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)
ANY_LD_RE = re.compile(
    r"[ \t]*(?:<!--\s*/?MEIHODO-[A-Z-]*JSONLD\s*-->\s*)*"
    r'<script[^>]*type="application/ld\+json"[^>]*>.*?</script>\s*'
    r"(?:<!--\s*/MEIHODO-[A-Z-]*JSONLD\s*-->)?\n?",
    re.S,
)

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.I)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
IMG_RE = re.compile(r'<img[^>]+src="(/images/[^"]+)"')
P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S)
STRIP_RE = re.compile(r"<(script|style|nav|footer)\b.*?</\1>", re.S)
FAQ_RE = re.compile(
    r'<h3 class="faq-item__question">(.*?)</h3>\s*'
    r'<p class="faq-item__answer">(.*?)</p>',
    re.S,
)
DURATION_RE = re.compile(r"所要時間[：:]\s*(?:<[^>]+>\s*)*([0-9.]+)\s*(時間|分)")
OCCUPANCY_RE = re.compile(r"最大[^0-9]{0,12}([0-9]{1,2})\s*名様")
EXPERIENCE_LINK_RE = re.compile(r'href="/[a-z-]+/experiences/([a-z]+)/"')
DEEP_LINK_RE = re.compile(
    r"https://www\.hpdsp\.net/[^\"']*hww3201init\.do\?[^\"']*roomTypeCd=[0-9]+[^\"']*"
)


# ---------------------------------------------------------------------------
# Page-content readers
# ---------------------------------------------------------------------------
def text_of(fragment: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment))).strip()


def body_of(src: str) -> str:
    return STRIP_RE.sub("", src)


def page_title(src: str, lang: str) -> str:
    m = TITLE_RE.search(src)
    if not m:
        return C.BRAND[lang]
    return clean_title(text_of(m.group(1)), lang)


def clean_title(title: str, lang: str) -> str:
    """Collapse the "X - 鳴鳳堂 鳴鳳堂" duplication some pages carry."""
    brand = C.BRAND[lang]
    while title.endswith(f"{brand} {brand}"):
        title = title[: -(len(brand) + 1)]
    return title.strip()


def entity_name(src: str, lang: str) -> str:
    """The subject of the page, without the brand suffix."""
    t = page_title(src, lang)
    for sep in (" | ", " - ", " – ", " — "):
        if sep in t:
            t = t.split(sep)[0]
            break
    return t.strip() or C.BRAND[lang]


def page_description(src: str, path: str | None = None) -> str | None:
    """The page's own meta description, else its first substantial paragraph.

    An entry in C.PAGE_DESCRIPTIONS wins over both: it is the editor's summary
    of that page, and reading it from the config rather than from the generated
    block is what stops a regenerate from drifting back to the prose.
    """
    if path and path in C.PAGE_DESCRIPTIONS:
        return C.PAGE_DESCRIPTIONS[path]
    m = DESC_RE.search(src)
    if m and m.group(1).strip():
        return html.unescape(m.group(1)).strip()
    body = body_of(src)
    for raw in P_RE.findall(body):
        t = text_of(raw)
        if len(t) >= 30:
            return t[:300]
    m = H1_RE.search(body)
    return text_of(m.group(1)) if m else None


def page_image(src: str) -> str | None:
    body = body_of(src)
    m = IMG_RE.search(body)
    if not m:
        return None
    path = m.group(1)
    # Nav/utility icons are not representative page images.
    if re.search(r"/(Home|taiken|tatemono|pictogram)", path):
        for cand in IMG_RE.findall(body):
            if not re.search(r"/(Home|taiken|tatemono|pictogram)", cand):
                path = cand
                break
        else:
            return None
    return C.BASE + path


def faq_pairs(src: str) -> list[tuple[str, str]]:
    """Only Q&A a visitor can actually read on the page."""
    return [(text_of(q), text_of(a)) for q, a in FAQ_RE.findall(src)]


def iso_duration(slug: str) -> str | None:
    """Session length, read off the ja page.

    The length is a property of the session, identical in every language, and
    only the ja markup states it in one parseable form ("所要時間：60分"), so
    the ja value is reused rather than re-parsed out of four phrasings.
    """
    p = C.REPO / "ja" / "experiences" / slug / "index.html"
    if not p.exists():
        return None
    m = DURATION_RE.search(p.read_text(encoding="utf-8"))
    if not m:
        return None
    value, unit = float(m.group(1)), m.group(2)
    minutes = int(round(value * 60)) if unit == "時間" else int(round(value))
    h, mm = divmod(minutes, 60)
    return "PT" + (f"{h}H" if h else "") + (f"{mm}M" if mm else "")


def building_occupancy(slug: str) -> int | None:
    """Capacity is a property of the building; only the ja pages spell it out."""
    p = C.REPO / "ja" / slug / "index.html"
    if not p.exists():
        return None
    m = OCCUPANCY_RE.search(p.read_text(encoding="utf-8"))
    return int(m.group(1)) if m else None


def booking_url(src: str) -> str | None:
    m = DEEP_LINK_RE.search(src)
    return m.group(0) if m else C.BOOKING_URL


# ---------------------------------------------------------------------------
# Shared graph nodes
# ---------------------------------------------------------------------------
def node_website(lang: str) -> dict:
    return {
        "@type": "WebSite",
        "@id": C.ID_WEBSITE,
        "url": f"{C.BASE}/",
        "name": C.BRAND[lang],
        "alternateName": C.ALT_NAMES[lang],
        "inLanguage": [C.LANG_TAG[l] for l in C.LANGS],
        "publisher": {"@id": C.ID_ORG},
    }


def node_address(lang: str) -> dict:
    a = C.ADDRESS[lang]
    return {
        "@type": "PostalAddress",
        "streetAddress": a["street"],
        "addressLocality": a["locality"],
        "addressRegion": a["region"],
        "postalCode": C.POSTAL_CODE,
        "addressCountry": "JP",
    }


def node_organization(lang: str) -> dict:
    return {
        "@type": "Organization",
        "@id": C.ID_ORG,
        "name": C.BRAND[lang],
        "alternateName": C.ALT_NAMES[lang],
        "url": f"{C.BASE}/",
        "logo": {"@type": "ImageObject", "url": C.LOGO},
        "image": C.DEFAULT_IMAGE,
        "description": C.FACILITY_DESCRIPTION[lang],
        "telephone": C.TELEPHONE,
        "email": C.EMAIL,
        "address": node_address(lang),
        "sameAs": C.SAME_AS,
        "knowsAbout": C.KNOWS_ABOUT,
        "location": {"@id": C.ID_MEIHODO},
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "reservations",
            "telephone": C.TELEPHONE,
            "email": C.EMAIL,
            "availableLanguage": [C.LANG_TAG[l] for l in C.LANGS],
        },
    }


def node_meihodo(lang: str, full: bool) -> dict:
    """The estate itself.

    Typed LodgingBusiness + Resort + TouristAttraction: Resort (a
    LodgingBusiness subtype) is what a 56,000 sqm site that lodges guests and
    runs its own restaurant and activity programme actually is, and
    TouristAttraction carries the half that day visitors come for. Hotel would
    be wrong - nothing here is let by the room.

    LodgingBusiness is listed alongside Resort even though Resort is already a
    subtype of it. It is redundant to a consumer that resolves the schema.org
    hierarchy, and load-bearing for one that string-matches the type - which is
    what "is this an accommodation?" checks tend to do.
    """
    base = {
        "@type": ["LodgingBusiness", "Resort", "TouristAttraction"],
        "@id": C.ID_MEIHODO,
        "name": C.BRAND[lang],
        # Carried on the stub as well as the full node: "Meihodo" and "鳴鳳堂"
        # are how the estate is named off-site, and a page that only ever says
        # one of them gives an entity resolver nothing to match on.
        "alternateName": C.ALT_NAMES[lang],
        "url": f"{C.BASE}/" if lang == "ja" else f"{C.BASE}/{lang}",
        "telephone": C.TELEPHONE,
        "address": node_address(lang),
        "image": C.DEFAULT_IMAGE,
    }
    if not full:
        return base

    base.update({
        "description": C.FACILITY_DESCRIPTION[lang],
        "image": [
            C.DEFAULT_IMAGE,
            f"{C.BASE}/images/top/ryotei.webp",
            f"{C.BASE}/images/top/satuei.webp",
        ],
        "logo": C.LOGO,
        "email": C.EMAIL,
        "geo": {"@type": "GeoCoordinates", "latitude": C.LATITUDE, "longitude": C.LONGITUDE},
        "hasMap": C.HAS_MAP,
        "sameAs": C.SAME_AS,
        "parentOrganization": {"@id": C.ID_ORG},
        "availableLanguage": [C.LANG_TAG[l] for l in C.LANGS],
        "areaServed": {
            "@type": "AdministrativeArea",
            "name": f"{C.CITY[lang]}, {C.REGION[lang]}",
        },
        "knowsAbout": C.KNOWS_ABOUT,
        "amenityFeature": [
            {"@type": "LocationFeatureSpecification", "name": n, "value": True}
            for n in C.AMENITIES[lang]
        ],
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": {"ja": "敷地面積", "en": "Site area", "zh-cn": "占地面积", "zh-tw": "佔地面積"}[lang],
                "value": C.SITE_AREA_SQM,
                "unitCode": "MTK",
            },
            {
                "@type": "PropertyValue",
                "name": {"ja": "棟数", "en": "Number of buildings", "zh-cn": "建筑数量", "zh-tw": "建築數量"}[lang],
                "value": C.BUILDING_COUNT,
            },
        ],
        "containsPlace": (
            [{"@id": C.entity_id(b)} for b in C.BUILDINGS] + [{"@id": C.ID_RESTAURANT}]
        ),
        "makesOffer": [
            {
                "@type": "Offer",
                "itemOffered": {"@id": C.entity_id(s)},
                "url": C.ACTIVITY_URL[lang],
            }
            for s in C.EXPERIENCES
        ],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": C.CRUMB["experiences"][lang],
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@id": C.entity_id(s)}}
                for s in C.EXPERIENCES
            ],
        },
        # The booking systems are third-party listings of Meihodo, not other
        # names for it, so they are subjectOf - never sameAs.
        "subjectOf": [
            {"@type": "WebPage", "name": C.BOOKING_LABEL[lang], "url": C.BOOKING_URL},
            {"@type": "WebPage", "name": C.ACTIVITY_LABEL[lang], "url": C.ACTIVITY_URL[lang]},
        ],
    })
    # priceRange is only asserted where the site itself frames the tier; the
    # buildings publish no nightly rate, so nothing more precise is claimed.
    return base


def node_webpage(page, src: str, name: str, description: str | None,
                 image: str | None, about_id: str | None, main_id: str | None) -> dict:
    n = {
        "@type": "WebPage",
        "@id": f"{page.canonical}#webpage",
        "url": page.canonical,
        "name": name,
        "isPartOf": {"@id": C.ID_WEBSITE},
        "inLanguage": C.LANG_TAG[page.lang],
    }
    if description:
        n["description"] = description
    if image:
        n["primaryImageOfPage"] = {"@type": "ImageObject", "url": image}
    n["about"] = {"@id": about_id or C.ID_MEIHODO}
    if main_id:
        n["mainEntity"] = {"@id": main_id}
    if page.kind != "home":
        n["breadcrumb"] = {"@id": f"{page.canonical}#breadcrumb"}
    return n


def node_breadcrumb(page, leaf_name: str) -> dict | None:
    if page.kind == "home":
        return None
    items = []
    for i, (label, url) in enumerate(page.crumbs, start=1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "name": label if label else leaf_name,
            "item": url,
        })
    return {
        "@type": "BreadcrumbList",
        "@id": f"{page.canonical}#breadcrumb",
        "itemListElement": items,
    }


# ---------------------------------------------------------------------------
# Page-specific nodes
# ---------------------------------------------------------------------------
def node_experience(page, src: str, name: str, description, image) -> dict:
    """A bookable, instructor-led session -> Service.

    Not Course / EducationalOccupationalProgram: the pages describe a one-off
    visitor experience with a duration and a price, not enrolment in a
    programme of instruction.
    """
    slug = page.slug
    n = {
        "@type": "Service",
        "@id": C.entity_id(slug),
        "name": name,
        "alternateName": C.EXPERIENCE_ALT[slug],
        "serviceType": name,
        "category": C.EXPERIENCE_CATEGORY[slug],
        "url": page.canonical,
        "provider": {"@id": C.ID_MEIHODO},
        "areaServed": {
            "@type": "AdministrativeArea",
            "name": f"{C.CITY[page.lang]}, {C.REGION[page.lang]}",
        },
        "mainEntityOfPage": {"@id": f"{page.canonical}#webpage"},
    }
    if description:
        n["description"] = description
    if image:
        n["image"] = image

    # availableLanguage is declared on ServiceChannel, not on Service, so the
    # languages a session can be run in hang off the booking channel.
    n["availableChannel"] = {
        "@type": "ServiceChannel",
        "serviceUrl": C.ACTIVITY_URL[page.lang],
        "availableLanguage": [C.LANG_TAG[l] for l in C.LANGS],
    }

    # schema.org gives Service no duration property and declares
    # additionalProperty on Offer rather than Service, so the session length the
    # page advertises rides on each Offer - which is also where it belongs: it
    # describes what the guest is buying.
    duration = iso_duration(slug)
    duration_prop = [{
        "@type": "PropertyValue",
        "name": {"ja": "所要時間", "en": "Duration", "zh-cn": "所需时间", "zh-tw": "所需時間"}[page.lang],
        "value": duration,
    }] if duration else None

    rows = PRICES.get(slug, {}).get("rows", [])
    labels = LABELS.get(page.lang, LABELS["ja"])
    offers = []
    for key, amount in rows:
        offer = {
            "@type": "Offer",
            "name": labels.get(key, key),
            "price": str(amount),
            "priceCurrency": "JPY",
            "availability": "https://schema.org/InStock",
            "url": C.ACTIVITY_URL[page.lang],
            "itemOffered": {"@id": C.entity_id(slug)},
        }
        if duration_prop:
            offer["additionalProperty"] = duration_prop
        offers.append(offer)
    if offers:
        n["offers"] = offers
    return n


def node_building(page, src: str, name: str, description, image) -> dict:
    """Whole-building private lets -> House, not HotelRoom.

    Deliberately NOT co-typed as Product. Accommodation has no offers property,
    so reaching offers means claiming Product - and Google's Product validation
    then requires offers.price, which this site cannot supply: the buildings
    publish no nightly rate (rates are per person at full occupancy and vary by
    season). Declaring Product without a price trades a validation error for a
    booking link.

    The booking link is expressed as a ReserveAction instead, which is what it
    actually is - "you can reserve this here" - and needs no price to be valid.
    """
    n = {
        "@type": ["House", "Accommodation"],
        "@id": C.entity_id(page.slug),
        "name": name,
        "url": page.canonical,
        "containedInPlace": {"@id": C.ID_MEIHODO},
        "mainEntityOfPage": {"@id": f"{page.canonical}#webpage"},
    }
    if description:
        n["description"] = description
    if image:
        n["image"] = image
    occ = building_occupancy(page.slug)
    if occ:
        n["occupancy"] = {"@type": "QuantitativeValue", "maxValue": occ, "unitText": "person"}
    url = booking_url(src)
    if url:
        n["potentialAction"] = {
            "@type": "ReserveAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": url,
                "actionPlatform": [
                    "https://schema.org/DesktopWebPlatform",
                    "https://schema.org/MobileWebPlatform",
                ],
            },
            "result": {"@type": "LodgingReservation", "name": name},
        }
    return n


def node_restaurant(lang: str, description, image, full: bool) -> dict:
    """The on-site kaiseki restaurant.

    The compact form - used on the home page and the restaurant sub-pages -
    still carries name, address, telephone, cuisine, price range and hours.
    A bare {@id, name} reference would merge correctly by @id, but a validator
    (or a crawler) looking at one sub-page in isolation would see a Restaurant
    with no address and report it incomplete. Only the page-derived description,
    image and menu link are held back for the restaurant page itself.
    """
    n = {
        "@type": "Restaurant",
        "@id": C.ID_RESTAURANT,
        "name": C.RESTAURANT_NAME[lang],
        "url": C.canonical_for(f"{lang}/restaurant/index.html"),
        "containedInPlace": {"@id": C.ID_MEIHODO},
        "parentOrganization": {"@id": C.ID_ORG},
        "address": node_address(lang),
        "telephone": C.TELEPHONE,
        "servesCuisine": {"ja": "会席料理", "en": "Japanese (kaiseki)",
                          "zh-cn": "日本料理（会席）", "zh-tw": "日本料理（會席）"}[lang],
        "priceRange": "¥¥¥",
        "currenciesAccepted": "JPY",
        "acceptsReservations": True,
        "openingHoursSpecification": [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday",
                              "Friday", "Saturday", "Sunday"],
                "opens": opens,
                "closes": closes,
            }
            for opens, closes in C.RESTAURANT_HOURS
        ],
    }
    if not full:
        return n
    n["description"] = description
    n["image"] = image or C.RESTAURANT_IMAGE
    n["hasMenu"] = C.canonical_for(f"{lang}/restaurant/kaiseki.html")
    return n


def node_campaign(page) -> dict:
    """The 阿蘇ふっこう割 promotion itself, as an entity separate from the article.

    Typed SaleEvent: it is a dated, organiser-run offer period, and giving it
    its own @id is what lets the article say "this article is *about* this
    campaign" and the campaign say "鳴鳳堂 is a participant" - rather than
    leaving a search engine to infer the connection from prose alone.
    """
    a = C.CAMPAIGN_ARTICLE
    return {
        "@type": "SaleEvent",
        "@id": C.ID_CAMPAIGN,
        "name": a["campaign_name"][page.lang],
        "alternateName": a["campaign_alt"][page.lang],
        "description": C.PAGE_DESCRIPTIONS[page.path],
        "url": page.canonical,
        "startDate": a["campaign_start"],
        "endDate": a["campaign_end"],
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "organizer": {
            "@type": "GovernmentOrganization",
            "name": a["organizer"][page.lang],
        },
        # 鳴鳳堂 is a 対象宿泊施設 of the campaign: the qualifying stay happens
        # here, and the campaign is about this estate. Those two properties are
        # the machine-readable half of the sentence the page opens with.
        # (Not performer - that expects a Person or PerformingGroup, and a
        # wrong type is worse than a missing one.)
        "location": {"@id": C.ID_MEIHODO},
        "about": {"@id": C.ID_MEIHODO},
    }


def node_campaign_article(page, image: str | None) -> dict:
    """The campaign page as a dated announcement.

    NewsArticle rather than a bare WebPage: the page is an announcement with a
    publication date and a subject, and the properties Google documents for
    Article (headline / image / datePublished / dateModified / author /
    publisher / mainEntityOfPage) only have somewhere to live on an Article.
    """
    a = C.CAMPAIGN_ARTICLE
    return {
        "@type": "NewsArticle",
        "@id": f"{page.canonical}#article",
        "headline": a["headline"][page.lang],
        "alternativeHeadline": a["alternativeHeadline"][page.lang],
        "description": C.PAGE_DESCRIPTIONS[page.path],
        "datePublished": a["datePublished"],
        "dateModified": a["dateModified"],
        "inLanguage": C.LANG_TAG[page.lang],
        "url": page.canonical,
        "mainEntityOfPage": {"@id": f"{page.canonical}#webpage"},
        "isPartOf": {"@id": f"{page.canonical}#webpage"},
        # 鳴鳳堂 wrote and publishes this announcement about its own
        # participation; the organiser of the campaign is on the SaleEvent node.
        "author": {"@id": C.ID_ORG},
        "publisher": {"@id": C.ID_ORG},
        "image": [image or a["image"]],
        "keywords": a["keywords"][page.lang],
        "articleSection": C.CRUMB["information"][page.lang],
        "about": [{"@id": C.ID_CAMPAIGN}, {"@id": C.ID_MEIHODO}],
        "mentions": [{"@id": C.ID_CAMPAIGN}, {"@id": C.ID_MEIHODO}],
    }


def node_nakadake() -> dict:
    """阿蘇山・中岳 as an entity, so the article has a subject to point at.

    Name and alternate names only. The article states no coordinates, no
    boundaries and no current activity status, so nothing more is claimed here
    - 鳴鳳堂 is not the authority on the volcano, the 気象台 is.
    """
    return {
        "@type": "Mountain",
        "@id": C.ID_NAKADAKE,
        "name": "阿蘇山 中岳",
        "alternateName": ["中岳", "阿蘇中岳", "阿蘇山", "Mount Aso Nakadake"],
    }


def node_news_article(page, image: str | None) -> dict:
    """A dated 鳴鳳堂 announcement under /ja/information/.

    Same reasoning as node_campaign_article: an announcement with a
    publication date and a subject is an Article, not a bare WebPage. The
    subject is the volcano and the estate, which is what lets an answer engine
    connect "阿蘇山の噴火警戒レベルは今どうなっているか" to a page that says so
    without having to parse the prose.
    """
    a = C.NEWS_ALERT_ARTICLE
    return {
        "@type": "NewsArticle",
        "@id": f"{page.canonical}#article",
        "headline": a["headline"][page.lang],
        "alternativeHeadline": a["alternativeHeadline"][page.lang],
        "description": C.PAGE_DESCRIPTIONS[page.path],
        "datePublished": a["datePublished"],
        "dateModified": a["dateModified"],
        "inLanguage": C.LANG_TAG[page.lang],
        "url": page.canonical,
        "mainEntityOfPage": {"@id": f"{page.canonical}#webpage"},
        "isPartOf": {"@id": f"{page.canonical}#webpage"},
        # 鳴鳳堂 publishes the announcement; the alert level itself was issued
        # by 福岡管区気象台, which the article names in its own prose. That
        # body is not given an entity node here because the site publishes
        # nothing else about it.
        "author": {"@id": C.ID_ORG},
        "publisher": {"@id": C.ID_ORG},
        "keywords": a["keywords"][page.lang],
        "articleSection": a["section"][page.lang],
        "about": [{"@id": C.ID_NAKADAKE}, {"@id": C.ID_MEIHODO}],
        "mentions": [{"@id": C.ID_NAKADAKE}, {"@id": C.ID_MEIHODO}],
        **({"image": [image]} if image else {}),
    }


def node_faqpage(page, pairs) -> dict:
    return {
        "@type": "FAQPage",
        "@id": f"{page.canonical}#faq",
        "url": page.canonical,
        "inLanguage": C.LANG_TAG[page.lang],
        "isPartOf": {"@id": C.ID_WEBSITE},
        "about": {"@id": C.ID_MEIHODO},
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in pairs
        ],
    }


def node_itemlist(page, ids: list[str], name: str) -> dict:
    return {
        "@type": "ItemList",
        "@id": f"{page.canonical}#list",
        "name": name,
        "itemListElement": [
            {"@type": "ListItem", "position": i, "item": {"@id": _id}}
            for i, _id in enumerate(ids, start=1)
        ],
    }


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------
def building_ref(lang: str, slug: str) -> dict:
    """Compact node for a building described in full on its own page.

    Carries the same @type list as the full node so the two cannot merge into a
    contradictory union when a consumer joins them by @id.
    """
    return {
        "@type": ["House", "Accommodation"],
        "@id": C.entity_id(slug),
        "name": C.BUILDING_NAMES[slug][lang],
        "containedInPlace": {"@id": C.ID_MEIHODO},
        "url": C.canonical_for(f"{lang}/{slug}/index.html"),
    }


def build_graph(page, src: str) -> list[dict]:
    lang = page.lang
    name = entity_name(src, lang)
    title = page_title(src, lang)
    is_home = page.kind == "home"
    if is_home:
        # The home pages open with a hero video whose control labels are the
        # first text in the document, so the generic reader picks those up.
        description = C.FACILITY_DESCRIPTION[lang]
        image = C.DEFAULT_IMAGE
    else:
        description = page_description(src, page.path)
        image = page_image(src)

    graph = [node_website(lang), node_organization(lang), node_meihodo(lang, full=is_home)]

    about_id = C.ID_MEIHODO
    main_id = None
    extra: list[dict] = []

    if is_home:
        main_id = C.ID_MEIHODO
        extra.append(node_restaurant(lang, None, None, full=False))
        for slug in C.EXPERIENCES:
            extra.append({
                "@type": "Service",
                "@id": C.entity_id(slug),
                "name": experience_name(lang, slug),
                "provider": {"@id": C.ID_MEIHODO},
                "url": C.canonical_for(f"{lang}/experiences/{slug}/index.html"),
            })
        for slug in C.BUILDINGS:
            extra.append(building_ref(lang, slug))

    elif page.kind == "experience":
        node = node_experience(page, src, name, description, image)
        extra.append(node)
        about_id = main_id = C.entity_id(page.slug)

    elif page.kind in ("building", "duplicate"):
        node = node_building(page, src, C.BUILDING_NAMES[page.slug][lang], description, image)
        extra.append(node)
        about_id = main_id = C.entity_id(page.slug)

    elif page.kind == "restaurant":
        extra.append(node_restaurant(lang, description, image, full=True))
        about_id = main_id = C.ID_RESTAURANT

    elif page.kind in ("restaurant-sub", "legacy"):
        extra.append(node_restaurant(lang, None, None, full=False))
        about_id = C.ID_RESTAURANT

    elif page.kind == "campaign":
        # The announcement, the promotion it announces, and the estate that
        # takes part in it - three nodes cross-referenced by @id, so the fact
        # "鳴鳳堂 is a 対象宿泊施設 of 阿蘇ふっこう割" is readable without parsing
        # the Japanese prose.
        extra.append(node_campaign(page))
        extra.append(node_campaign_article(page, image))
        main_id = f"{page.canonical}#article"

    elif page.kind == "news":
        # The announcement plus the volcano it is about, cross-referenced by
        # @id - the same two-node shape the campaign page uses.
        extra.append(node_nakadake())
        extra.append(node_news_article(page, image))
        main_id = f"{page.canonical}#article"

    elif page.kind == "faq":
        pairs = faq_pairs(src)
        if pairs:
            extra.append(node_faqpage(page, pairs))
            main_id = f"{page.canonical}#faq"

    elif page.kind == "experiences":
        ids = [C.entity_id(s) for s in C.EXPERIENCES]
        for slug in C.EXPERIENCES:
            extra.append({
                "@type": "Service",
                "@id": C.entity_id(slug),
                "name": experience_name(lang, slug),
                "alternateName": C.EXPERIENCE_ALT[slug],
                "category": C.EXPERIENCE_CATEGORY[slug],
                "provider": {"@id": C.ID_MEIHODO},
                "url": C.canonical_for(f"{lang}/experiences/{slug}/index.html"),
            })
        extra.append(node_itemlist(page, ids, C.CRUMB["experiences"][lang]))
        main_id = f"{page.canonical}#list"

    elif page.kind == "things-to-do":
        # The stay-and-experience guide. It describes no new real-world thing -
        # it is a route into the experiences that already have their own nodes -
        # so it contributes an ItemList over them and nothing else. Which
        # experiences it covers is read off the page's own links rather than
        # hardcoded, so the markup and the graph cannot drift apart.
        slugs = [s for s in dict.fromkeys(EXPERIENCE_LINK_RE.findall(src))
                 if s in C.EXPERIENCES]
        for slug in slugs:
            extra.append({
                "@type": "Service",
                "@id": C.entity_id(slug),
                "name": experience_name(lang, slug),
                "alternateName": C.EXPERIENCE_ALT[slug],
                "category": C.EXPERIENCE_CATEGORY[slug],
                "provider": {"@id": C.ID_MEIHODO},
                "url": C.canonical_for(f"{lang}/experiences/{slug}/index.html"),
            })
        if slugs:
            extra.append(node_itemlist(page, [C.entity_id(s) for s in slugs],
                                       C.CRUMB["things-to-do"][lang]))
            main_id = f"{page.canonical}#list"

    elif page.kind == "accommodations":
        ids = [C.entity_id(b) for b in C.BUILDINGS]
        for slug in C.BUILDINGS:
            extra.append(building_ref(lang, slug))
        extra.append(node_itemlist(page, ids, C.CRUMB["accommodations"][lang]))
        main_id = f"{page.canonical}#list"

    graph.append(node_webpage(page, src, title, description, image, about_id, main_id))
    crumb = node_breadcrumb(page, name)
    if crumb:
        graph.append(crumb)
    graph.extend(extra)
    return graph


_EXPERIENCE_NAME_CACHE: dict[tuple[str, str], str] = {}


def experience_name(lang: str, slug: str) -> str:
    """The experience's name in `lang`, taken from that language's own page."""
    key = (lang, slug)
    if key not in _EXPERIENCE_NAME_CACHE:
        p = C.REPO / lang / "experiences" / slug / "index.html"
        src = p.read_text(encoding="utf-8")
        _EXPERIENCE_NAME_CACHE[key] = entity_name(src, lang)
    return _EXPERIENCE_NAME_CACHE[key]


def render(graph: list[dict]) -> str:
    payload = {"@context": "https://schema.org", "@graph": graph}
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    # JSON-LD lives in a raw-text element: the only sequence that can end it
    # early is "</script". ensure_ascii=False keeps CJK readable, and json.dumps
    # already escapes quotes and backslashes.
    body = body.replace("</", "<\\/")
    return f'{START}\n<script type="application/ld+json">\n{body}\n</script>\n{END}\n'


def process(path: Path, page, check: bool) -> bool:
    src = path.read_text(encoding="utf-8")
    stripped = MARKED_RE.sub("", src)
    stripped = ANY_LD_RE.sub("", stripped)

    block = render(build_graph(page, stripped))
    if "</head>" not in stripped:
        print(f"  SKIP (no </head>): {page.path}")
        return False
    new = stripped.replace("</head>", block + "</head>", 1)

    if new == src:
        return False
    if not check:
        path.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args()

    changed = 0
    for page in C.build_registry():
        p = C.REPO / page.path
        if process(p, page, args.check):
            changed += 1
    verb = "would change" if args.check else "updated"
    print(f"build_jsonld: {verb} {changed} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
