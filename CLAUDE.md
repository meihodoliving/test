# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ Live site comes first — read this every session

This site is **in production**. Every push to `main` deploys to both
- Vercel: `https://www.meihodo.com` (custom domain; `meihodo.com` apex redirects to `www`)
- GitHub Pages: `https://meihodoliving.github.io/test/`

**The deployed site must stay rendering correctly at all times.** A broken deploy is the most expensive kind of failure here, because real visitors see it. Optimize every change around this priority.

### Before acting on any prompt

1. **Read the user's prompt twice.** If the request is bulk/mechanical — "delete X", "rename Y", "remove all Z", "rewrite paths", "consolidate", "move everything to …" — pause and ask yourself: *does the thing I'm about to remove or change exist for a reason that local testing won't surface?* This repo has at least three foot-guns that look harmless locally and break only on Vercel (see "Deployment invariants" below). When in doubt, **ask the user** before making the change. A 10-second clarification is cheaper than a broken production site.
2. **Pre-flight audit** before any bulk edit to HTML, CSS, or directory structure:
   ```bash
   grep -rn '/public/' --include='*.html' .                       # must be empty
   grep -rn 'href="\.\./[a-z]' --include='*.html' */experiences/   # must be empty
   [ -d public ] && echo BAD || echo OK                            # must say OK
   ```
3. **Never** run destructive commands (`rm -rf`, `git rm`, mass `sed`) without first proving the targets are safe to remove. Move-then-verify-then-delete, not delete-then-hope.

### Before pushing to main

1. `git diff --stat origin/main..HEAD` — eyeball the file count and which trees are touched. If a change you didn't expect appears, investigate before pushing.
2. Re-run the pre-flight audits above. They must still be clean after your edits.
3. If the change touches HTML structure or assets, push and then **curl-verify the live site** before walking away:
   ```bash
   curl -sL https://www.meihodo.com/en/experiences/samurai | grep -c 'class="experience-hero"'    # > 0
   curl -sI https://www.meihodo.com/en/experiences/components.css | head -1                       # 200, not 404
   curl -sI https://www.meihodo.com/styles.css | grep -i content-length                           # 156000+ bytes
   ```
4. If GitHub Pages goes red, fix it immediately. Check with `GH_TOKEN=<token> gh run list --repo meihodoliving/test --limit 3`. The most common failure is a deprecated `actions/*` version.

### Why local "works" ≠ deployed works

Local servers (`live-server`, `python http.server`) do NOT replicate Vercel's behavior:
- They don't auto-treat `public/` as a static-asset root.
- They don't strip trailing slashes (Vercel's `cleanUrls: true` does).
- They serve every file in the working tree without honoring `.vercelignore`.

A page can render perfectly locally and be completely broken on Vercel. **Trust the deployed-site curl checks, not local rendering, when verifying a fix is real.**

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
/index.html        ← the Japanese TOP page. Its only canonical URL is "/".
/ja/  /en/  /zh-cn/  /zh-tw/
```

**There is no `/ja/index.html`.** The Japanese top page lives at the repo root and is
published at `/` only; `vercel.json` 301s the exact paths `/ja`, `/ja/` and
`/ja/index.html` to `/`. Do not recreate `ja/index.html` — it would resurrect the
duplicate the redirect exists to kill. Japanese **sub** pages keep their `/ja/...`
URLs (`/ja/information/`, `/ja/campaign/aso-fukkou/`, `/ja/experiences/...`), and the
language switcher only sends Japanese *top-page* switches to `/`.

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

### SEO / structured data — generated, do not hand-edit

`npm run seo` (`python3 scripts/build_seo.py`) owns every page's `<head>` SEO block and JSON-LD. `npm run seo:check` reports without writing. Both are idempotent.

**Do not hand-edit anything between these markers — the next run overwrites it:**

```
<!-- MEIHODO-SEO-META -->  …canonical, hreflang, description, OG, Twitter…  <!-- /MEIHODO-SEO-META -->
<!-- MEIHODO-JSONLD -->    …one @graph per page…                            <!-- /MEIHODO-JSONLD -->
```

To change what they emit, edit the source instead:

- [seo_config.py](scripts/seo_config.py) — every fact (address, phone, hours, building and experience names, `sameAs`, `knowsAbout`) plus the page registry that decides canonical URLs, hreflang sets and sitemap membership. **Nothing may be added here that a visitor cannot read on the site.** Unverifiable facts go in [AEO_CONTENT_RECOMMENDATIONS.md](AEO_CONTENT_RECOMMENDATIONS.md) as a request to the operator.
- [build_jsonld.py](scripts/build_jsonld.py) — the `@graph`. Entity `@id`s are language-neutral (`#meihodo`, `#kyudo`, `#edokan`) so all four language trees describe one entity; document nodes (`#webpage`, `#breadcrumb`, `#faq`) are per-URL.
- [build_head_meta.py](scripts/build_head_meta.py) — canonical/hreflang/OG/Twitter. Also warns about non-`ja` pages still showing Japanese body copy.
- [build_sitemap.py](scripts/build_sitemap.py) — `sitemap.xml` + `robots.txt`. `lastmod` comes from git history, never from the clock.

Two rules the generators encode, worth not re-breaking:

1. **Canonical URLs carry no trailing slash and no `.html`.** Vercel's `cleanUrls: true` + `trailingSlash: false` means `/ja/restaurant/` 308-redirects to `/ja/restaurant`. A canonical pointing at the slash form points at a redirect. (Internal `href`s still use the slash form; that is a separate, deliberate non-change — see AEO recommendations P2-5.)
2. **Never invent a fact to fill a schema property.** No `aggregateRating`, no `dateModified` stamped at build time, no price the site does not publish. Missing markup is recoverable; markup that lies is not.

After running it, re-check the deployed pages per "Before pushing to main" — this touches every HTML file in the repo.

### Shared front-end pieces

- [styles.css](styles.css) at the repo root is the single shared stylesheet (~7k lines). Language pages reference it as `../styles.css`.
- [lang-switcher.js](lang-switcher.js) is included as `<script src="/lang-switcher.js" defer>` on every page that has a `#lang-btn` / `#lang-dropdown`. It infers the current language from the URL prefix and rewrites the path to switch.
- Experience pages under `/ja/experiences/<slug>/` share [ja/experiences/components.css](ja/experiences/components.css) and follow the layout documented in [ja/experiences/README.md](ja/experiences/README.md). Use [ja/experiences/kyudo/](ja/experiences/kyudo/) as the reference implementation; [UPDATE_SUMMARY.md](UPDATE_SUMMARY.md) records the standardization pattern.

## Deployment

Two deploy targets are wired up. Both serve the repo root.

- **Vercel** — [vercel.json](vercel.json) sets `framework: null`, `outputDirectory: "."`, `cleanUrls: true`, no install/build. [.vercelignore](.vercelignore) excludes `node_modules`, `meihodo-rebuild`, `scripts`, `.claude`, `portfolio`.
- **GitHub Pages** — [.github/workflows/deploy.yml](.github/workflows/deploy.yml) uploads the entire repo as the Pages artifact on push to `main`.

Because `cleanUrls: true` is set on Vercel, prefer linking to `/ja/about/` rather than `/ja/about/index.html` for new internal links (existing links use `index.html` and still work).

### Deployment invariants — DO NOT VIOLATE

Each rule below corresponds to a real outage that has hit this repo. The pattern in every case was the same: the change looked fine locally, was pushed, and broke production. **Don't reopen any of these.**

1. **No `public/` directory. Ever.** Vercel auto-treats `public/` as a static-asset root and silently shadows the repo-root `styles.css` / `index.html` with whatever's inside `public/` — even when `outputDirectory: "."` is set. Local servers don't do this, so the disparity is invisible until deploy. If you're about to create `public/anything`, stop — put the files at the repo root (`/images/`, `/styles.css`, etc.). Caused outages: `d079a20` (first fix), and again post-`fa5b0eb` (full removal).
2. **All image references are absolute from the repo root: `/images/...`.** Never `/public/images/...`, never `./images/...`, never `../images/...`. Absolute paths resolve identically at every URL depth, in every language tree, on both deploy targets. Caused outage: 216 stale `/public/images/...` refs across 72 files after `public/` was deleted.
3. **Cross-directory links from sub-pages must be absolute, not `..`-relative.** Vercel runs `cleanUrls: true` + `trailingSlash: false`, which canonicalizes `/en/experiences/iaido/` → `/en/experiences/iaido` (no trailing slash). The browser then treats `iaido` as a *filename* in `/en/experiences/`, so `../components.css` resolves to `/en/components.css` (**404**), not `/en/experiences/components.css`. Local servers preserve the trailing slash and don't hit this, so the page renders fine locally and totally unstyled on Vercel. Concrete rules:
   - Cross-directory: use absolute. `<link href="/en/experiences/components.css">`, `<a href="/en/experiences/chado/">`.
   - Up-to-root: relative is fine as long as you have *enough* `..`s to clamp at `/`. From a page at depth N, use N `..`s (or more — extras clamp harmlessly). E.g. `<link href="../../../styles.css">` from `/en/experiences/<slug>/index.html` works because three `..`s clamp to `/`.
   - **Anything in between is broken on Vercel.** A single `..` from depth ≥ 2 is the trap.
   - Audit with: `grep -rn 'href="\.\./[a-z]' --include='*.html' */experiences/` — must be empty. Caused outage: every experience page was unstyled because `<link href="../components.css">` 404'd silently.
4. **Never deploy without verifying the live site.** After pushing a change that touches HTML/CSS/assets, curl the deployed page and grep for the styles you expect to see. The "Before pushing to main" section above has the exact commands.

If the deployed site looks visually broken but local is fine, your first three checks are:
- `grep -rn '/public/' --include='*.html' .` → must be empty (rule 1+2)
- `ls public/` → must say "No such file" (rule 1)
- `grep -rn 'href="\.\./[a-z]' --include='*.html' */experiences/` → must be empty (rule 3)

## Conventions

- **Internal links: absolute paths rooted at language.** `href="/ja/experiences/"`, not relative `../`. Two reasons: (a) the mirror scripts depend on it — relative paths break the `s/\/ja\//\/zh-tw\//` rewrite; (b) `..` from a sub-page breaks under Vercel `cleanUrls` (see Deployment invariant 3).
- **Image `src`/`srcset`: absolute from repo root.** `src="/images/top/top.webp"`. See Deployment invariant 2.
- **The only safe relative path is up-to-root.** `<link href="../styles.css">` from `/ja/index.html`, `<link href="../../../styles.css">` from a depth-3 page — both clamp at `/styles.css`. Everything else must be absolute.
- **When editing structure under `/ja/`, propagate to the other three language trees** (or run the mirror scripts in `scripts/`) so the language switcher does not 404.
- **Prices, room names, and other cross-page facts that have a generator script in [scripts/](scripts/) should be edited in the script, not in HTML.**
