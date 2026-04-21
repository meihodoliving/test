#!/usr/bin/env python3
"""Mechanical fixes for zh-cn mirror: lang, internal /ja/ -> /zh-cn/, home -> /zh-cn/index.html."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "zh-cn"


def fix_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    orig = text
    text = text.replace('lang="ja"', 'lang="zh-CN"')
    # Internal site links only (not external URLs containing /ja/)
    text = re.sub(r'href="/ja/', 'href="/zh-cn/', text)
    text = text.replace('href="../../index.html"', 'href="/zh-cn/index.html"')
    text = text.replace('href="../../index.html#', 'href="/zh-cn/index.html#')
    text = text.replace('href="/index.html"', 'href="/zh-cn/index.html"')
    # Breadcrumb / nav that pointed to root index with two levels up
    text = text.replace("<a href=\"../../index.html\"", '<a href="/zh-cn/index.html"',)
    text = text.replace("<a href='../../index.html'", "<a href='/zh-cn/index.html'",)
    if text != orig:
        path.write_text(text, encoding="utf-8")


def main() -> None:
    for path in sorted(ZH.rglob("*.html")):
        fix_file(path)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
