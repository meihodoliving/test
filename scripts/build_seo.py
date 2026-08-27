#!/usr/bin/env python3
"""Run the whole SEO/AEO pipeline in the order the generators expect.

  1. build_jsonld      - the @graph block on every page
  2. build_head_meta   - canonical / hreflang / description / OG / Twitter
  3. build_sitemap     - sitemap.xml + robots.txt

Order matters: build_head_meta anchors its block immediately above the JSON-LD
block, so the JSON-LD has to exist first. Each step is idempotent, and running
the pipeline twice is a no-op.

Run: python3 scripts/build_seo.py [--check]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_head_meta
import build_jsonld
import build_sitemap

STEPS = (build_jsonld, build_head_meta, build_sitemap)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args()

    argv = sys.argv
    for step in STEPS:
        sys.argv = [step.__name__] + (["--check"] if args.check else [])
        rc = step.main()
        if rc:
            sys.argv = argv
            return rc
    sys.argv = argv
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
