#!/usr/bin/env python3
"""
Create /zh-tw/ pages by mirroring /ja/ with identical structure.

- Copies every ja/**/*.html → zh-tw/**/*.html (same relative path)
- Keeps layout/HTML structure identical
- Mechanical adjustments only:
  - <html lang="ja"> → <html lang="zh-TW">
  - href="/ja/..." → href="/zh-tw/..." (ONLY this exact pattern)

This script does NOT translate text; it only ensures the parallel zh-tw files exist
so language switching can navigate to real pages.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "ja"
DST_DIR = ROOT / "zh-tw"


def main() -> None:
    src_files = sorted(SRC_DIR.glob("**/*.html"))
    if not src_files:
        raise SystemExit("No ja/**/*.html files found.")

    n_written = 0
    for src in src_files:
        rel = src.relative_to(SRC_DIR)
        dst = DST_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        text = src.read_text(encoding="utf-8")
        text = text.replace('<html lang="ja">', '<html lang="zh-TW">')
        text = text.replace('href="/ja/', 'href="/zh-tw/')

        # Write (always overwrite to stay in sync with ja structure)
        dst.write_text(text, encoding="utf-8")
        n_written += 1

    print(f"Mirrored {n_written} files to {DST_DIR}")


if __name__ == "__main__":
    main()

