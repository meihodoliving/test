#!/usr/bin/env python3
"""Generate sitemap.xml and robots.txt at the repo root.

The site had neither: https://www.meihodo.com/sitemap.xml and /robots.txt both
answered 404, so nothing told a crawler which of the four language trees to
read, and the 301/308 stubs were as discoverable as the real pages.

Every URL emitted is the URL Vercel actually serves 200 for (cleanUrls strips
".html", trailingSlash:false drops the slash). Redirect stubs, orphan
duplicates and the pre-migration Chinese pages are excluded - they are exactly
what a sitemap must not advertise.

lastmod comes from git's last commit touching each file. It is never stamped
with "now": a sitemap that claims every page changed today teaches a crawler to
distrust the field.

Run: python3 scripts/build_sitemap.py [--check]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

import seo_config as C

SITEMAP = C.REPO / "sitemap.xml"
ROBOTS = C.REPO / "robots.txt"

# Search and answer-engine crawlers that index public pages. The site is a
# public marketing site, so the whole of it is open to them; the crawler-
# specific groups exist so a future disallow can be scoped rather than
# accidentally global.
SEARCH_AGENTS = (
    "Googlebot",
    "Googlebot-Image",
    "Google-Extended",
    "Bingbot",
    "Slurp",
    "DuckDuckBot",
    "Applebot",
    "Applebot-Extended",
    "OAI-SearchBot",
    "ChatGPT-User",
    "GPTBot",
    "PerplexityBot",
    "Perplexity-User",
    "ClaudeBot",
    "Claude-User",
    "Claude-SearchBot",
    "Amazonbot",
    "CCBot",
    "Bytespider",
    "meta-externalagent",
)


def last_modified(path: str) -> str | None:
    """Author date of the last commit that touched this file, as YYYY-MM-DD."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", path],
            cwd=C.REPO, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out or None


def sitemap_xml() -> str:
    pages = [p for p in C.build_registry() if p.in_sitemap]
    # A stable order keeps the diff readable: language root first, then path.
    pages.sort(key=lambda p: (p.canonical.count("/"), p.canonical))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]

    for page in pages:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(page.canonical)}</loc>")
        # xhtml:link alternates repeat the page's hreflang set, which is what
        # lets a crawler discover the other three languages from the sitemap
        # alone.
        alts = C.alternates_for(page)
        for tag, url in alts.items():
            lines.append(
                f'    <xhtml:link rel="alternate" hreflang="{tag}" href="{escape(url)}"/>'
            )
        if alts:
            lines.append(
                '    <xhtml:link rel="alternate" hreflang="x-default" '
                f'href="{escape(alts.get("ja", page.canonical))}"/>'
            )
        lastmod = last_modified(page.path)
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")

    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def robots_txt() -> str:
    lines = [
        "# https://www.meihodo.com/ - 鳴鳳堂 / Meihodo, Aso, Kumamoto, Japan",
        "# The whole site is public marketing content and is open to search and",
        "# answer engines. Named groups exist so any future restriction can be",
        "# scoped to one crawler instead of applying to all of them.",
        "",
    ]
    for agent in SEARCH_AGENTS:
        lines += [f"User-agent: {agent}", "Allow: /", ""]
    lines += [
        "User-agent: *",
        "Allow: /",
        "",
        "# Pre-migration stubs kept only so old inbound links resolve. They are",
        "# 301/308 redirects or duplicates of a canonical page, and are left out",
        "# of the sitemap for the same reason.",
        "Disallow: /zh-hans/",
        "Disallow: /zh-hant/",
        "",
        f"Sitemap: {C.BASE}/sitemap.xml",
        "",
    ]
    return "\n".join(lines)


def write(path: Path, content: str, check: bool) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return False
    if not check:
        path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args()

    sm = sitemap_xml()
    changed = []
    if write(SITEMAP, sm, args.check):
        changed.append("sitemap.xml")
    if write(ROBOTS, robots_txt(), args.check):
        changed.append("robots.txt")

    urls = sm.count("<loc>")
    verb = "would write" if args.check else "wrote"
    print(f"build_sitemap: {urls} URLs; {verb} {', '.join(changed) or 'nothing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
