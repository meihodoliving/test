#!/usr/bin/env python3
"""Keep the shared marketing footer in sync across each language tree.

WHY THIS EXISTS
---------------
The live site is plain static HTML with no build step, so the footer is
physically duplicated in every page. Editing the footer by hand on one page
(e.g. /ja/index.html) silently drifts from the rest. This script makes one
page per language the single source of truth and copies its footer to the
other pages that use the same footer.

CANONICAL SOURCE (per language)
-------------------------------
    ja     -> ja/index.html
    en     -> en/index.html
    zh-tw  -> zh-tw/index.html
    zh-cn  -> zh-cn/index.html
The repository-root /index.html is treated as part of the ja group.

WHICH PAGES ARE SYNCED
----------------------
Only pages whose <footer> already contains `experience-menu-columns` — i.e.
the main marketing footer (鳴鳳堂 / 体験 / 宿泊 / お問い合わせ). This deliberately
leaves alone the intentionally different footers under:
    restaurant/   (営業時間-led restaurant footer, no 鳴鳳堂 block)
    location/     (撮影利用-led footer)
    stay/         (Quick Links footer)
    faq/          (simple brand + contact footer)
…and any experience pages that still use the older single-column experience
footer (they lack `experience-menu-columns`). Converting those is a separate,
deliberate decision — not something this sync should do silently.

Because every footer link is absolute (`/ja/...`), the identical footer HTML
is valid on every page in a language tree regardless of directory depth.

USAGE
-----
    python3 scripts/sync_footer.py            # dry-run: list out-of-sync files
    python3 scripts/sync_footer.py --diff      # dry-run + show unified diffs
    python3 scripts/sync_footer.py --apply     # write the changes

Always run the dry-run (ideally with --diff) and eyeball it before --apply.
After --apply, follow CLAUDE.md: re-run the pre-flight audits and curl-verify
the live site once deployed.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["ja", "en", "zh-tw", "zh-cn"]
FOOTER_RE = re.compile(r"<footer\b.*?</footer>", re.S)
MARKER = "experience-menu-columns"


def extract_footer(text: str) -> str | None:
    m = FOOTER_RE.search(text)
    return m.group(0) if m else None


def targets_for(lang: str) -> list[Path]:
    files = sorted((ROOT / lang).glob("**/*.html"))
    if lang == "ja":
        files = [ROOT / "index.html"] + files
    return files


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default: dry-run, no files touched)")
    ap.add_argument("--diff", action="store_true",
                    help="print a unified diff for each out-of-sync file")
    args = ap.parse_args()

    total_changed = 0
    total_skipped = 0
    for lang in LANGS:
        src = ROOT / lang / "index.html"
        if not src.exists():
            print(f"!! {lang}: missing source {src}", file=sys.stderr)
            continue
        canonical = extract_footer(src.read_text(encoding="utf-8"))
        if not canonical:
            print(f"!! {lang}: no <footer> found in {src}", file=sys.stderr)
            continue

        for f in targets_for(lang):
            if f.resolve() == src.resolve():
                continue
            text = f.read_text(encoding="utf-8")
            cur = extract_footer(text)
            if not cur or MARKER not in cur:
                total_skipped += 1  # not a marketing-footer page -> leave alone
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
    print(f"--- {total_changed} file(s) {verb}; "
          f"{total_skipped} non-marketing footer(s) left untouched ---")


if __name__ == "__main__":
    main()
