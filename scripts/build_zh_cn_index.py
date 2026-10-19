#!/usr/bin/env python3
"""RETIRED - this script no longer writes anything.

It used to regenerate zh-cn/index.html from ja/index.html by string
replacement.

Why it was retired (2026-10):
- ja/index.html no longer exists (the Japanese top page is the root
  index.html, published only at "/"), so the script crashed on start.
- zh-cn/index.html is translated by hand; regenerating it from the Japanese
  page would revert that copy, including the 2026-10 brand-concept text.

zh-cn/index.html is now maintained by hand, like every other translated page. Edit it
directly, then run `python3 scripts/build_seo.py` for its <head> SEO block and
JSON-LD.

The last working version is in git history:
    git show d66e6cc:scripts/build_zh_cn_index.py
"""
import sys

sys.exit(
    "build_zh_cn_index.py is retired: it would overwrite the hand-maintained zh-cn/index.html. "
    "Edit that file directly instead (see the docstring of this script)."
)
