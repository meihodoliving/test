#!/usr/bin/env python3
"""
Scan /images/{folder}/ and inject <div class="gallery-grid"> contents
into ja|en|zh-cn|zh-tw/{room}/index.html for each guest room page.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parent.parent
IMAGE_ROOT = REPO / "images"

# page directory name (under lang) -> subdirectory of /images/
ROOM_TO_DIR: dict[str, str] = {
    "bunshinkan": "bunsinkan",
    "edokan": "edokan",
    "geihinkan": "geihinkan",
    "hinokinoma": "hinokinoma",
    "korokan": "kourokan",
    "seiseikan": "seiseisya",
}

LANGS = ("ja", "en", "zh-cn", "zh-tw")

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".JPG", ".JPEG", ".PNG"}

# Overlay h4 labels (numbered) per language
def overlay_label(lang: str, index: int) -> str:
    labels = {
        "ja": "写真 {}",
        "en": "Photo {}",
        "zh-cn": "图 {}",
        "zh-tw": "圖 {}",
    }
    return labels[lang].format(index)


def alt_prefix(lang: str, room: str) -> str:
    """Room name fragment for img alt."""
    meta = ALT_PREFIX.get((lang, room), ALT_PREFIX.get(("en", room), {}))
    return meta.get("alt", room)


ALT_PREFIX = {
    ("ja", "bunshinkan"): {"alt": "文心館"},
    ("ja", "edokan"): {"alt": "江戸館"},
    ("ja", "geihinkan"): {"alt": "迎賓館"},
    ("ja", "hinokinoma"): {"alt": "檜の間"},
    ("ja", "korokan"): {"alt": "光籟館"},
    ("ja", "seiseikan"): {"alt": "清静舎"},
    ("en", "bunshinkan"): {"alt": "Bunshinkan"},
    ("en", "edokan"): {"alt": "Edokan"},
    ("en", "geihinkan"): {"alt": "Geihinkan"},
    ("en", "hinokinoma"): {"alt": "Hinokinoma"},
    ("en", "korokan"): {"alt": "Korokan"},
    ("en", "seiseikan"): {"alt": "Seiseikan"},
    ("zh-cn", "bunshinkan"): {"alt": "文心馆"},
    ("zh-cn", "edokan"): {"alt": "江户馆"},
    ("zh-cn", "geihinkan"): {"alt": "迎宾馆"},
    ("zh-cn", "hinokinoma"): {"alt": "桧木间"},
    ("zh-cn", "korokan"): {"alt": "光籁馆"},
    ("zh-cn", "seiseikan"): {"alt": "清静舍"},
    ("zh-tw", "bunshinkan"): {"alt": "文心館"},
    ("zh-tw", "edokan"): {"alt": "江戶館"},
    ("zh-tw", "geihinkan"): {"alt": "迎賓館"},
    ("zh-tw", "hinokinoma"): {"alt": "檜之間"},
    ("zh-tw", "korokan"): {"alt": "光籟館"},
    ("zh-tw", "seiseikan"): {"alt": "清靜舎"},
}


def list_image_files(folder: Path) -> list[str]:
    if not folder.is_dir():
        return []
    names = []
    for p in folder.iterdir():
        if not p.is_file():
            continue
        if p.suffix in EXTS or p.name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            names.append(p.name)
    # Case-sensitive lex order (matches typical DSC* before _* since 'D' < '_')
    return sorted(names)


def image_url_web(image_dir: str, filename: str) -> str:
    enc = quote(filename, safe="")
    return f"/images/{image_dir}/{enc}"


def build_grid_html(lang: str, room: str, image_dir: str, files: list[str]) -> str:
    lines = []
    for i, fn in enumerate(files, start=1):
        url = image_url_web(image_dir, fn)
        ap = alt_prefix(lang, room)
        alt = f"{ap} — {fn}"
        h4 = overlay_label(lang, i)
        lines.append(
            f'                <div class="gallery-item">\n'
            f'                    <img src="{url}" alt="{alt}" loading="lazy">\n'
            f'                    <div class="gallery-overlay">\n'
            f'                        <h4>{h4}</h4>\n'
            f"                    </div>\n"
            f"                </div>"
        )
    return "\n".join(lines)


def replace_gallery_grid(html: str, new_inner: str) -> str | None:
    """Replace inner HTML of first <div class="gallery-grid">...</div>."""
    token = '<div class="gallery-grid">'
    start = html.find(token)
    if start == -1:
        return None
    inner_start = start + len(token)
    depth = 1
    i = inner_start
    n = len(html)
    while i < n and depth > 0:
        if html.startswith("</div>", i):
            depth -= 1
            if depth == 0:
                return html[:inner_start] + "\n" + new_inner + "\n            " + html[i:]
            i += 6
            continue
        if html.startswith("<div", i) and (i + 4 < n and html[i + 4] in " \t\n>/"):
            depth += 1
            gt = html.find(">", i)
            if gt == -1:
                return None
            i = gt + 1
            continue
        i += 1
    return None


def process_file(path: Path, lang: str, room: str, image_dir: str, files: list[str]) -> bool:
    html = path.read_text(encoding="utf-8")
    inner = build_grid_html(lang, room, image_dir, files)
    new_html = replace_gallery_grid(html, inner)
    if new_html is None:
        print(f"SKIP (no gallery-grid): {path}", file=sys.stderr)
        return False
    path.write_text(new_html, encoding="utf-8")
    return True


def main() -> int:
    missing_dirs: list[str] = []
    updated = 0
    for room, img_dir in ROOM_TO_DIR.items():
        folder = IMAGE_ROOT / img_dir
        files = list_image_files(folder)
        if not files:
            missing_dirs.append(img_dir)
            continue
        for lang in LANGS:
            page = REPO / lang / room / "index.html"
            if not page.is_file():
                print(f"MISSING PAGE: {page}", file=sys.stderr)
                continue
            if process_file(page, lang, room, img_dir, files):
                updated += 1
                print(f"OK {lang}/{room}: {len(files)} images")

    if missing_dirs:
        print(f"WARN: no image files in: {missing_dirs}", file=sys.stderr)

    print(f"Updated {updated} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
