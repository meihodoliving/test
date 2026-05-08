# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static multilingual marketing site for **鳴鳳堂 (Meihodo) / Aso Cultural Resort**. Pure HTML + CSS + a tiny vanilla JS file ([lang-switcher.js](lang-switcher.js)). No build step for the live site — files are served as-is.

A separate Next.js 15 / React 19 / Tailwind 4 rewrite lives under [meihodo-rebuild/](meihodo-rebuild/). It is **excluded from the deployed site** (see [.vercelignore](.vercelignore)) and has its own toolchain — treat it as an independent project.

## Common commands

Run from repo root unless noted.

```bash
npm start                      # live-server on :3000 with reload (serves /index.html — the Japanese root)
npm run serve                  # python3 http.server on :8000 (no reload)

npm run lint                   # htmlhint index.html + stylelint styles.css (root files only)

npm run optimize:images:dry    # preview JPG/PNG → WebP conversions
npm run optimize:images        # convert + rewrite references across the repo + delete originals
```

For the Next.js rebuild:

```bash
cd meihodo-rebuild && npm run dev      # next dev --turbopack
cd meihodo-rebuild && npm run lint     # eslint
```

There are no tests in this repo.

## Architecture: the multilingual mirror

The site is published at four language roots that share an identical directory tree:

```
/index.html        ← Japanese root (also reachable as /ja/index.html)
/ja/  /en/  /zh-cn/  /zh-tw/
```

**`/ja/` is the source of truth.** `/en/`, `/zh-cn/`, `/zh-tw/` are structural mirrors of `/ja/` — same file paths, same HTML structure, only text/links translated. When adding a page, add it under `/ja/` first and propagate.

Each language tree contains the same set of sections: `about/`, `access/`, `accommodations/`, `bunshinkan/`, `edokan/`, `experiences/`, `geihinkan/`, `hinokinoma/`, `korokan/`, `location/`, `restaurant/`, `seiseikan/`, `stay/`. Sibling pages exist for `restaurant.html` at the language root.

The bare `/zh-hans/restaurant.html` and `/zh-hant/restaurant.html` are legacy stubs — [lang-switcher.js](lang-switcher.js) normalizes `zh-hans → zh-cn` and `zh-hant → zh-tw` for display, but new content goes under `/zh-cn/` and `/zh-tw/`.

### Scripts that maintain the mirror

The [scripts/](scripts/) directory holds Python utilities that enforce the mirror invariants. They are **not invoked by npm**; run with `python3 scripts/<name>.py` when you need them.

- [create_zh_tw_mirror.py](scripts/create_zh_tw_mirror.py) — copies every `ja/**/*.html` to `zh-tw/`, rewrites `lang="ja"` → `lang="zh-TW"` and `href="/ja/"` → `href="/zh-tw/"`. **Does not translate text.** Run after adding/restructuring pages under `/ja/`.
- [zh_cn_mechanical.py](scripts/zh_cn_mechanical.py) — same mechanical fixups for `/zh-cn/` (also normalizes `../../index.html` paths).
- [build_en_index.py](scripts/build_en_index.py), [build_zh_cn_index.py](scripts/build_zh_cn_index.py) — regenerate the language-root `index.html` from the canonical root [index.html](index.html), with translated copy and adjusted asset paths.
- [build_room_galleries.py](scripts/build_room_galleries.py) — scans `/images/<room>/` and injects `<div class="gallery-grid">` into each language's `<room>/index.html`. Note the directory-name remapping (e.g. page `bunshinkan` ↔ image folder `bunsinkan`, `korokan` ↔ `kourokan`, `seiseikan` ↔ `seiseisya`) defined in `ROOM_TO_DIR`.
- [update_experience_prices.py](scripts/update_experience_prices.py) — single source of truth for experience prices across all four languages. Edit the `PRICES` dict and run; do not hand-edit prices in HTML.
- [fix_lang_zh_cn_links.py](scripts/fix_lang_zh_cn_links.py), [fix_lang_zh_tw_links.py](scripts/fix_lang_zh_tw_links.py), [fix_access_nav_links.py](scripts/fix_access_nav_links.py), [replace_iaido_terms.py](scripts/replace_iaido_terms.py) — targeted post-hoc rewrites; read the script before running.
- [optimize_images.py](scripts/optimize_images.py) — converts JPG/PNG to WebP, rewrites references in `.html`/`.css`/`.js`/etc., deletes originals. Skips `.git` and `node_modules`. Use the `:dry` npm script first.

### Shared front-end pieces

- [styles.css](styles.css) at the repo root is the single shared stylesheet (~7k lines). Language pages reference it as `../styles.css`.
- [lang-switcher.js](lang-switcher.js) is included as `<script src="/lang-switcher.js" defer>` on every page that has a `#lang-btn` / `#lang-dropdown`. It infers the current language from the URL prefix and rewrites the path to switch.
- Experience pages under `/ja/experiences/<slug>/` share [ja/experiences/components.css](ja/experiences/components.css) and follow the layout documented in [ja/experiences/README.md](ja/experiences/README.md). Use [ja/experiences/kyudo/](ja/experiences/kyudo/) as the reference implementation; [UPDATE_SUMMARY.md](UPDATE_SUMMARY.md) records the standardization pattern.
- A duplicate copy of `index.html` and `styles.css` sits under [public/](public/). It is **not** served (Vercel uses `outputDirectory: "."`) — do not edit it expecting changes to ship.

## Deployment

Two deploy targets are wired up. Both serve the repo root, not `public/`.

- **Vercel** — [vercel.json](vercel.json) sets `framework: null`, `outputDirectory: "."`, `cleanUrls: true`, no install/build. [.vercelignore](.vercelignore) excludes `node_modules`, `meihodo-rebuild`, `scripts`, `.claude`.
- **GitHub Pages** — [.github/workflows/deploy.yml](.github/workflows/deploy.yml) uploads the entire repo as the Pages artifact on push to `main`.

Because `cleanUrls: true` is set on Vercel, prefer linking to `/ja/about/` rather than `/ja/about/index.html` for new internal links (existing links use `index.html` and still work).

## Conventions

- Internal links use absolute paths rooted at language: `href="/ja/experiences/"`, not relative `../`. The mirror scripts depend on this — relative paths break the `s/\/ja\//\/zh-tw\//` rewrite.
- When editing structure under `/ja/`, propagate to the other three language trees (or run the mirror scripts) so the language switcher does not 404.
- Prices, room names, and other cross-page facts that have a generator script in [scripts/](scripts/) should be edited in the script, not in HTML.
