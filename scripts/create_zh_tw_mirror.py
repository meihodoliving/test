#!/usr/bin/env python3
"""RETIRED - this script no longer writes anything.

It used to copy every ja/**/*.html over zh-tw/ with only lang/href
rewrites, so the switcher would find a page at every path.

Why it was retired (2026-10):
- Every zh-tw page now exists and is translated. A run replaced all 43
  translated pages with Japanese copy.
- To add a new page, copy the single ja/ file to zh-tw/ by hand, change
  lang="ja" to lang="zh-TW" and /ja/ links to /zh-tw/, then translate it.

zh-tw/ tree is now maintained by hand, like every other translated page. Edit it
directly, then run `python3 scripts/build_seo.py` for its <head> SEO block and
JSON-LD.

The last working version is in git history:
    git show d66e6cc:scripts/create_zh_tw_mirror.py
"""
import sys

sys.exit(
    "create_zh_tw_mirror.py is retired: it would overwrite the hand-maintained zh-tw/ tree. "
    "Edit that file directly instead (see the docstring of this script)."
)
