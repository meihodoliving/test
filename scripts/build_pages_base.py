#!/usr/bin/env python3
"""Rewrite root-absolute internal references onto a base path, for GitHub Pages.

WHY THIS IS A BUILD STEP AND NOT A COMMIT
=========================================
The same repo is served by two live targets with different base paths:

  Vercel        https://www.meihodo.com/          -> served at the domain root
  GitHub Pages  https://meihodoliving.github.io/test/  -> served under /test/

so no single set of paths committed to the repo can be correct for both.
Hardcoding "/test/" into the HTML would 404 every image and every nav link on
www.meihodo.com, which is the customer-facing site (CLAUDE.md deployment
invariant 2). Relative paths cannot fix it either: Vercel serves "/ja" with no
trailing slash while Pages serves "/test/ja/" with one, so the same relative
href resolves to two different places (invariant 3).

The repo therefore keeps root-absolute paths - correct for Vercel, and the
documented convention - and this script rewrites them inside the ephemeral CI
checkout just before the Pages artifact is uploaded. Nothing it writes is ever
committed.

WHAT IT REWRITES
================
  href/src/poster="/..."   -> "{base}/..."
  srcset="/a 1x, /b 2x"    -> each candidate prefixed
  url(/...) in CSS files, <style> blocks and inline style="" attributes

WHAT IT LEAVES ALONE
====================
Anything that is already a full URL (https://, http://, //host), and every
in-page reference (#anchor, mailto:, tel:, data:). That is what keeps the SEO
layer intact: canonical, hreflang, og:url, og:image, twitter:image and every
URL inside the JSON-LD are absolute https://www.meihodo.com/... URLs, so no
pattern here can match them. They must keep pointing at the production domain
even in the Pages build - Pages is a mirror, not the canonical home.

It also injects

    <!-- PAGES-BASE-PATH --><script>window.__BASE_PATH__ = "/test/";</script>

as the first thing in <head>, which is how the site's JavaScript learns the
base path. lang-switcher.js and the home-page overlay read it and fall back to
"/" when it is absent, so they behave identically on Vercel.

Run: python3 scripts/build_pages_base.py --base /test
     python3 scripts/build_pages_base.py --base /test --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Trees that are not part of the published site.
EXCLUDE_DIRS = {
    ".git", ".github", "node_modules", "meihodo-rebuild", "portfolio",
    "backup", "scripts", ".vscode", ".claude",
}

# A marker of its own, not the bare identifier: the five index.html pages read
# window.__BASE_PATH__ in their inline isHomePage(), so testing for the
# identifier would see those pages as already injected and silently skip them -
# leaving __BASE_PATH__ undefined there and breaking the language switcher on
# exactly the four language home pages.
MARKER = "<!-- PAGES-BASE-PATH -->"

# A reference we must not touch: already absolute, or not a path at all.
SKIP_PREFIXES = ("http://", "https://", "//", "#", "mailto:", "tel:", "data:", "javascript:")

ATTR_RE = re.compile(r'\b(href|src|poster)="/(?!/)([^"]*)"')
SRCSET_RE = re.compile(r'\bsrcset="([^"]*)"')
# url(/x), url('/x'), url("/x") - in .css files, <style> blocks and style="".
URL_RE = re.compile(r"""url\(\s*(['"]?)/(?!/)([^)'"]*)\1\s*\)""")
HEAD_RE = re.compile(r"(<head\b[^>]*>)", re.I)


def norm_base(base: str) -> str:
    """"/test", "test/", "/test/" -> "/test/". "" or "/" -> "/"."""
    base = "/" + base.strip().strip("/")
    return "/" if base == "/" else base + "/"


def already_based(path: str, base: str) -> bool:
    """True if this value has already been rewritten onto `base`.

    Keeps the rewrite idempotent. Without it a second pass would turn
    "/test/images/x" into "/test/test/images/x".
    """
    return ("/" + path).startswith(base)


def rewrite_attrs(html: str, base: str) -> str:
    # group(2) is the path after the leading slash, so href="/" (empty group)
    # becomes href="{base}" - the site root link, still correct under the base.
    def one(m):
        if already_based(m.group(2), base):
            return m.group(0)
        return f'{m.group(1)}="{base}{m.group(2)}"'

    return ATTR_RE.sub(one, html)


def rewrite_srcset(html: str, base: str) -> str:
    def one(m):
        out = []
        for cand in m.group(1).split(","):
            cand = cand.strip()
            if not cand:
                continue
            if (cand.startswith("/") and not cand.startswith("//")
                    and not already_based(cand[1:], base)):
                cand = base + cand[1:]
            out.append(cand)
        return 'srcset="' + ", ".join(out) + '"'

    return SRCSET_RE.sub(one, html)


def rewrite_urls(text: str, base: str) -> str:
    def one(m):
        if already_based(m.group(2), base):
            return m.group(0)
        return f"url({m.group(1)}{base}{m.group(2)}{m.group(1)})"

    return URL_RE.sub(one, text)


def inject_base(html: str, base: str) -> str:
    if MARKER in html:
        return html
    tag = f'{MARKER}<script>window.__BASE_PATH__ = "{base}";</script>'
    if not HEAD_RE.search(html):
        return html
    return HEAD_RE.sub(lambda m: m.group(1) + "\n    " + tag, html, count=1)


def process_html(text: str, base: str) -> str:
    text = rewrite_attrs(text, base)
    text = rewrite_srcset(text, base)
    text = rewrite_urls(text, base)
    text = inject_base(text, base)
    return text


def walk(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if set(rel.parts) & EXCLUDE_DIRS:
            continue
        if p.suffix.lower() in (".html", ".htm", ".css", ".js"):
            yield p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help='base path, e.g. "/test"')
    ap.add_argument("--root", default=str(REPO), help="tree to rewrite in place")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = norm_base(args.base)
    root = Path(args.root).resolve()

    if base == "/":
        print("build_pages_base: base is '/', nothing to rewrite")
        return 0

    changed = 0
    counts = {"attrs": 0, "srcset": 0, "url": 0, "injected": 0}
    for p in walk(root):
        src = p.read_text(encoding="utf-8")
        if p.suffix.lower() in (".html", ".htm"):
            counts["attrs"] += len(ATTR_RE.findall(src))
            counts["srcset"] += sum(
                1 for m in SRCSET_RE.finditer(src)
                for c in m.group(1).split(",")
                if c.strip().startswith("/") and not c.strip().startswith("//")
            )
            counts["url"] += len(URL_RE.findall(src))
            if MARKER not in src:
                counts["injected"] += 1
            new = process_html(src, base)
        else:
            # .css and .js: only url() needs the prefix. Paths inside JS are
            # handled by the scripts themselves reading __BASE_PATH__, so they
            # are deliberately not string-rewritten here.
            counts["url"] += len(URL_RE.findall(src))
            new = rewrite_urls(src, base)

        if new != src:
            changed += 1
            if not args.dry_run:
                p.write_text(new, encoding="utf-8")

    verb = "would rewrite" if args.dry_run else "rewrote"
    print(f"build_pages_base: base={base}  {verb} {changed} file(s)")
    print(f"  href/src/poster : {counts['attrs']}")
    print(f"  srcset entries  : {counts['srcset']}")
    print(f"  url() refs      : {counts['url']}")
    print(f"  __BASE_PATH__   : injected into {counts['injected']} page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
