#!/usr/bin/env python3
"""Convert every experience-page footer to the canonical homepage footer.

WHY THIS EXISTS
---------------
The experience pages under `<lang>/experiences/<slug>/` historically shipped an
older, hand-written footer that drifted from the homepage:
  * a structural bug (a doubled, unclosed `<div class="footer-section">`),
  * a single-column 体験/Experiences list with an incomplete link set,
  * no 宿泊/Accommodations section,
  * stale contact info (熊本県阿蘇市 / +81 967-34-1234 / info@asocultural.jp).
This made the footer render misaligned and inconsistent with the rest of the
site. This script replaces each experience page's <footer> block with the
canonical homepage footer for the same language.

Because every footer link is absolute (`/ja/...`) and all footer styling lives
in the shared root `styles.css`, the homepage footer HTML is valid and renders
identically at the experience pages' directory depth — on both PC and mobile.

After this runs, the experience footers contain `experience-menu-columns`, so
`scripts/sync_footer.py` will keep them in sync with the homepage going forward.

USAGE
-----
    python3 scripts/convert_experience_footers.py            # dry-run
    python3 scripts/convert_experience_footers.py --diff     # dry-run + diffs
    python3 scripts/convert_experience_footers.py --apply    # write changes
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["ja", "en", "zh-tw", "zh-cn"]
FOOTER_RE = re.compile(r"[ \t]*<footer\b.*?</footer>", re.S)


def extract_footer(text: str) -> str | None:
    m = FOOTER_RE.search(text)
    return m.group(0) if m else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default: dry-run, no files touched)")
    ap.add_argument("--diff", action="store_true",
                    help="print a unified diff for each out-of-sync file")
    args = ap.parse_args()

    total_changed = 0
    for lang in LANGS:
        src = ROOT / lang / "index.html"
        if not src.exists():
            print(f"!! {lang}: missing source {src}", file=sys.stderr)
            continue
        canonical = extract_footer(src.read_text(encoding="utf-8"))
        if not canonical:
            print(f"!! {lang}: no <footer> found in {src}", file=sys.stderr)
            continue

        # Both the experiences landing page (experiences/index.html) and every
        # per-slug detail page (experiences/<slug>/index.html).
        for f in sorted((ROOT / lang / "experiences").glob("**/index.html")):
            text = f.read_text(encoding="utf-8")
            cur = extract_footer(text)
            if cur is None:
                print(f"!! no <footer> in {f.relative_to(ROOT)}", file=sys.stderr)
                continue
            if cur == canonical:
                continue
            total_changed += 1
            rel = f.relative_to(ROOT)
            print(("APPLY " if args.apply else "DRIFT ") + str(rel))
            if args.diff and not args.apply:
                for line in difflib.unified_diff(
                    cur.splitlines(), canonical.splitlines(),
                    fromfile=str(rel), tofile=str(src.relative_to(ROOT)),
                    lineterm="", n=1,
                ):
                    print("    " + line)
            if args.apply:
                f.write_text(text.replace(cur, canonical, 1), encoding="utf-8")

    verb = "updated" if args.apply else "out of sync"
    print(f"--- {total_changed} file(s) {verb} ---")


if __name__ == "__main__":
    main()
