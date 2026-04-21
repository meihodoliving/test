#!/usr/bin/env python3
"""Set header Access nav links to language-specific /{lang}/access/ root paths."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Replace longer / more specific href strings first (substring order).
HREF_NEEDLES = (
    "/zh-cn/index.html#access",
    "/zh-tw/index.html#access",
    "/ja/index.html#access",
    "/en/index.html#access",
    "../../../../index.html#access",
    "../../../index.html#access",
    "../../index.html#access",
    "../index.html#access",
    "index.html#access",
    "#access",
)


def access_target_for(html_path: Path) -> str:
    rel = html_path.relative_to(REPO)
    parts = rel.parts
    if not parts:
        return "/ja/access/"
    top = parts[0]
    if top in ("ja", "en", "zh-cn", "zh-tw"):
        return f"/{top}/access/"
    if top == "zh-hans":
        return "/zh-cn/access/"
    if top == "zh-hant":
        return "/zh-tw/access/"
    if parts == ("index.html",):
        return "/ja/access/"
    if top == "public":
        return "/ja/access/"
    return "/ja/access/"


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "#access" not in text and "index.html#access" not in text:
        return False
    target = access_target_for(path)
    orig = text
    for needle in HREF_NEEDLES:
        text = text.replace(f'href="{needle}"', f'href="{target}"')
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    n = 0
    for path in REPO.rglob("*.html"):
        if "node_modules" in path.parts:
            continue
        if patch_file(path):
            n += 1
            print(path.relative_to(REPO))
    print(f"Patched {n} files.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
