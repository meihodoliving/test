#!/usr/bin/env python3
"""Set bottom-right 「簡」 language switch to the parallel /zh-cn/… page for each HTML file."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# `<a href="..." class="lang-btn" data-lang="zh-cn">…</a>` (href first — repo convention)
RE_ANCHOR_HREF_FIRST = re.compile(
    r'<a\s+href="[^"]*"\s+class="lang-btn"\s+data-lang="zh-cn">\s*([简簡])\s*</a>'
)
RE_BUTTON_ZH_CN = re.compile(
    r'<button\s+class="lang-btn"\s+data-lang="zh-cn">\s*([简簡])\s*</button>'
)
RE_BUTTON_SIMPLIFIED = re.compile(
    r'<button\s+class="lang-btn"\s+data-lang="simplified">\s*簡\s*</button>'
)


def zh_cn_url_for(source: Path) -> str | None:
    """Absolute site path /zh-cn/… parallel to this file (same path under zh-cn/)."""
    try:
        rel = source.relative_to(ROOT)
    except ValueError:
        return None

    parts = rel.parts
    if not parts:
        return None

    if parts[0] == "ja":
        remainder = Path(*parts[1:])
    elif parts[0] == "en":
        remainder = Path(*parts[1:])
    elif parts[0] == "zh-cn":
        remainder = Path(*parts[1:])
    elif parts[0] in ("zh-hans", "zh-hant"):
        remainder = Path(*parts[1:])
    elif len(parts) == 1 and parts[0] == "index.html":
        remainder = Path("index.html")
    else:
        return None

    url = "/zh-cn/" + remainder.as_posix()
    target_file = ROOT / "zh-cn" / remainder
    if not target_file.is_file():
        print(f"WARNING: missing parallel file {target_file}", file=sys.stderr)
    return url


def patch_content(raw: str, url: str) -> str:
    """Replace 簡/简 control with <a href=url>. Preserve 简 vs 簡 label."""
    text = raw

    def rep_anchor(m: re.Match[str]) -> str:
        label = m.group(1)
        return f'<a href="{url}" class="lang-btn" data-lang="zh-cn">{label}</a>'

    text, n_anchor = RE_ANCHOR_HREF_FIRST.subn(rep_anchor, text, count=1)
    if n_anchor:
        return text

    text, n_btn = RE_BUTTON_ZH_CN.subn(
        lambda m: f'<a href="{url}" class="lang-btn" data-lang="zh-cn">{m.group(1)}</a>',
        text,
        count=1,
    )
    if n_btn:
        return text

    text, n_sim = RE_BUTTON_SIMPLIFIED.subn(
        f'<a href="{url}" class="lang-btn" data-lang="zh-cn">簡</a>',
        text,
        count=1,
    )
    if n_sim:
        return text

    return raw


def _has_zh_switcher(raw: str) -> bool:
    return bool(
        RE_ANCHOR_HREF_FIRST.search(raw)
        or RE_BUTTON_ZH_CN.search(raw)
        or RE_BUTTON_SIMPLIFIED.search(raw)
    )


def process_file(path: Path) -> bool:
    url = zh_cn_url_for(path)
    if url is None:
        return False
    raw = path.read_text(encoding="utf-8")
    new = patch_content(raw, url)
    if new != raw:
        path.write_text(new, encoding="utf-8")
        print(f"updated: {path.relative_to(ROOT)} -> {url}")
        return True
    if _has_zh_switcher(raw):
        print(f"unchanged (already {url}): {path.relative_to(ROOT)}")
    else:
        print(f"skip (no 「簡」 control): {path.relative_to(ROOT)}", file=sys.stderr)
    return False


def main() -> None:
    paths: list[Path] = []
    paths.extend(sorted(ROOT.glob("ja/**/*.html")))
    paths.extend(sorted(ROOT.glob("en/**/*.html")))
    paths.extend(sorted(ROOT.glob("zh-cn/**/*.html")))
    paths.extend(sorted(ROOT.glob("zh-hans/**/*.html")))
    paths.extend(sorted(ROOT.glob("zh-hant/**/*.html")))
    idx = ROOT / "index.html"
    if idx.is_file():
        paths.append(idx)

    seen: set[Path] = set()
    n = 0
    for p in paths:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        if process_file(rp):
            n += 1
    print(f"Done. {n} files changed.")


if __name__ == "__main__":
    main()
