#!/usr/bin/env python3
"""RETIRED - this script no longer writes anything.

It used to regenerate en/index.html from the Japanese root index.html by
string replacement.

Why it was retired (2026-10):
- en/index.html had already drifted from it by ~300 body lines (static hero
  image instead of the video, English news section, revised copy), so a run
  silently reverted months of hand edits.
- The 2026-10 brand-concept copy (concept block, "About staying at Meihodo")
  was written per language, not derived from the Japanese text.

en/index.html is now maintained by hand, like every other translated page. Edit it
directly, then run `python3 scripts/build_seo.py` for its <head> SEO block and
JSON-LD.

The last working version is in git history:
    git show d66e6cc:scripts/build_en_index.py
"""
import sys

sys.exit(
    "build_en_index.py is retired: it would overwrite the hand-maintained en/index.html. "
    "Edit that file directly instead (see the docstring of this script)."
)
