# AEO / E-E-A-T content recommendations

What the structured-data work could **not** fix, because the fix is content a
human has to write or verify — not markup.

The JSON-LD now says everything the site actually supports. Everything below is
a claim Meihodo could credibly make but currently has no page to back up, or a
fact on the site that needs a human to confirm before it can be published as
structured data.

Ground rule used throughout the implementation: **if a visitor cannot read it on
the page, it is not in the JSON-LD.** Several items below exist precisely
because honouring that rule left a gap.

Priorities: **P0** now · **P1** strongly recommended · **P2** medium term.

---

## P0 — needed now

### P0-1. 17 pages advertise a translation they do not have

`npm run seo` prints this list on every run. These pages sit under a non-Japanese
URL and carry `hreflang` / `inLanguage` for that language, but their body copy is
still Japanese:

| Page | Declared | Actual body |
|---|---|---|
| `zh-tw/restaurant/*.html` (all 12) | Traditional Chinese | Japanese |
| `zh-tw/experiences/takigyo/index.html` | Traditional Chinese | Japanese |
| `zh-tw/location/terms.html` | Traditional Chinese | Japanese |
| `zh-tw/stay/geihinkan.html` | Traditional Chinese | Japanese |
| `en/location/terms.html` | English | Japanese |
| `zh-cn/location/terms.html` | Simplified Chinese | Japanese |

Why it matters: a Traditional-Chinese speaker who arrives from search gets a page
they cannot read, and an answer engine asked "阿蘇有懷石料理嗎" finds a page
labelled Traditional Chinese whose content it must translate anyway — so it will
prefer a competitor's genuinely localised page.

The markup was deliberately **not** relabelled as Japanese to paper over this.
The tags describe what these URLs are meant to be; the fix is to translate the
copy. Once translated, re-run `npm run seo` and the warning clears by itself.

### P0-2. The chef profile cannot be marked up as a Person until it is verified

`*/restaurant/chef.html` names a head chef (料理長 田中 正義) with a dated
career history: 1999 training in Tokyo, 2005 in Kyoto, 2010 independent in
Kumamoto, 2020 joining Meihodo, "25 years' experience".

No `Person` entity was created for this, on purpose. The résumé reads like
template copy — the milestones are round-numbered and name no employer — and
publishing an unverified named individual with a fabricated work history as
structured data is exactly the failure mode that gets a site's markup
distrusted.

**Action:** confirm whether this person and this history are real.
- If real: say which restaurants, and the JSON-LD can add a `Person` with
  `jobTitle`, `worksFor` → `#restaurant`, and `knowsAbout`.
- If placeholder: remove or rewrite the page. It is live at
  `https://www.meihodo.com/ja/restaurant/chef` today.

### P0-3. Confirm the coordinates

`geo` publishes `32.923696, 131.012587`, carried over from the JSON-LD that was
already deployed. Nobody in this repo's history verified it against the actual
entrance. A wrong `geo` sends guests to the wrong turning on a mountain road.

Check it against the estate's real entrance and correct `LATITUDE` / `LONGITUDE`
in `scripts/seo_config.py`.

### P0-4. No operator / responsible-party information anywhere on the site

There is no 運営会社 page, no 会社概要, no 特定商取引法に基づく表記, and no
privacy policy. For a business taking lodging and experience bookings from
overseas visitors this is both a trust gap and, for the 特商法 notice, a legal
requirement in Japan.

This is the single biggest E-E-A-T gap on the site. "Who is behind this?" is a
question every answer engine weighs and this site currently cannot answer.

**Create `/ja/company/` (mirrored to all four languages)** with: legal entity
name, representative, registered address, telephone, contact email, business
registration, and the lodging licence (旅館業法 / 住宅宿泊事業法) number the
estate operates under.

Once it exists, `#organization` can carry `legalName`, `foundingDate`,
`founder`, `vatID`/`taxID` and a `contactPoint` for each function.

### P0-5. Dedicated Open Graph images

`og:image` currently reuses each page's first content image. That works, but
those images are not sized or composed for a 1200×630 share card, so links
shared to LINE, Facebook or X crop unpredictably.

The two OG images the old markup referenced — `og-image-restaurant.jpg` and
`restaurant-hero.jpg` — **404 on the live site**; the new generator no longer
points at them. Produce a 1200×630 card for the home page, the restaurant, the
experiences index and the lodging index, put them under `/images/og/`, and wire
them into `seo_config.py`.

---

## P1 — strongly recommended

### P1-1. Instructor and cultural-practitioner profiles

Every experience page says "指導者が丁寧に指導します" — an instructor, unnamed.
Nowhere does the site say who teaches kyudo, what rank they hold, or which
school they belong to.

This is the highest-value authority content the site could add. "Where in
Kumamoto can I learn kyudo from a qualified instructor?" is exactly the question
Meihodo should win, and right now the site gives an answer engine nothing to
cite.

**Create `/ja/instructors/`** with one profile per practitioner: name, discipline,
rank (段位), school/lineage (流派), years teaching, languages taught in, and a
photograph. Publish only what the person will stand behind publicly.

Once live, each becomes a `Person` with `knowsAbout`, `hasCredential`
(`EducationalOccupationalCredential` for a dan rank), `worksFor` →
`#organization`, and `performerIn` / `provider` on the matching `Service`. The
generator has a natural place for this — `EXPERIENCES` in `seo_config.py`.

### P1-2. Per-experience practical detail

The pages give duration and price. They do not consistently give:

- minimum / maximum group size
- minimum age (the child rate says ages 8–11, which implies a floor — state it)
- what to wear and what is provided
- whether the session runs in English without a separate interpreter
- how far ahead to book
- what happens in rain (an outdoor waterfall session especially)

The FAQ answers some of this generically. Answer engines quote the specific
page, not the general FAQ, so these belong on each experience page. They map
directly onto `Offer.eligibleQuantity`, `typicalAgeRange` and
`availableLanguage`.

### P1-3. A page about Meihodo's cultural-preservation work

`/ja/about` describes the buildings well but says almost nothing about *why* the
estate exists — who assembled the collection of Buddhist statuary, why a
56,000 m² Edo-style estate was built in Aso, what is being preserved.

The 活動報告 timeline on `/ja/about` already hints at it: the 大太鼓 provided to
南阿蘇復興太鼓 in 2021, three years of 茶会・桜を愛でる会, two 鳴鳳堂文化祭,
the 弓道場開き in 2024. That is a real record of cultural activity buried in a
bullet list.

Give it its own page with dates and outcomes. This is what separates "a venue
that sells samurai experiences" from "a cultural institution" in an answer
engine's judgement.

### P1-4. Surface the media coverage as citable content

`/ja/about` lists press and broadcast appearances — 秋田犬新聞 (2020, 2021),
KAB「アサデス。」(2024) — as plain text with no links.

Give them a `/ja/press/` page with outlet, date, headline and a link where one
exists. Third-party coverage is the strongest external corroboration the site
has, and right now it is invisible to a crawler as anything but prose. It then
becomes `subjectOf` on `#meihodo`.

### P1-5. Publish a review path you actually control

`aggregateRating` was deliberately **not** emitted: the site publishes no
first-party reviews, and lifting a rating off an OTA and presenting it as the
facility's own is both a Google structured-data violation and dishonest.

If ratings matter for visibility, collect reviews on a page Meihodo owns, then
mark up the genuine aggregate. Until then, no rating is the correct output.

### P1-6. FAQ additions

The existing 40-question FAQ is well built and every entry is in the JSON-LD.
Questions it does not yet answer, all of which show up in AI queries about this
kind of facility:

- What exactly is Meihodo — is it a hotel, a museum, or a school?
- Can I visit for an experience without staying overnight?
- Can I stay overnight without booking an experience?
- How far is it from Kumamoto Airport / Aso Station / Kumamoto Station, in minutes?
- Is the site wheelchair accessible? Which buildings are, and which are not?
- Is an English-speaking instructor always available, or by arrangement?
- What is the smallest group you accept? Can one person book?
- Is there an onsen, and if not, what bathing is available?
- Can dietary restrictions be accommodated at the restaurant with notice?
- Which seasons are best, and what closes in winter?

The first three matter most: they are the identity questions, and Meihodo not
being a standard hotel is precisely what an answer engine gets wrong about it.

---

## P2 — medium term

### P2-1. Per-page "last reviewed" dates

`dateModified` is intentionally absent from the JSON-LD. The only available
source was the build timestamp, and stamping every page with the current date on
each deploy — making the whole site look freshly updated when nothing changed —
is the anti-pattern the brief explicitly ruled out.

`sitemap.xml` does carry a real `lastmod`, taken from the last git commit that
touched each file, which is honest.

If a visible "最終更新: 2026-XX-XX" is added to the pages whose content genuinely
changes (prices, hours, experience details), `dateModified` can be read from that
and published.

### P2-2. Building-level detail for the lodging pages

The six building pages give a description and a capacity. No nightly rate is
published anywhere on the site — the pages state rates are per person at full
occupancy and vary by season — so each building carries a `ReserveAction` with
the booking deep link and no `Offer` at all. That is deliberate: reaching
`offers` from an `Accommodation` requires co-typing it as `Product`, and Google
then requires `offers.price`, which this site cannot honestly supply.

Publishing a starting rate would let each building carry a real `Offer` with
`priceSpecification`. Floor area, bed configuration, bathing arrangement and a
"what's included" list would add `floorSize`, `numberOfRooms`, `bed` and
`amenityFeature` on top.

### P2-3. Content depth on each discipline

Each experience page is roughly one screen. A visitor asking "what is bonseki?"
gets two sentences.

Meihodo teaches these practices — writing 600–1,000 words on each (what it is,
its history, what a beginner actually does in the session, what they take away)
would make the site the best answer on the open web for several low-competition
queries, and give an answer engine something substantial to cite rather than a
marketing blurb. This compounds with P1-1: an instructor's byline turns an
article into expertise.

### P2-4. Consolidate the duplicate and legacy pages

Handled defensively in markup, but worth cleaning up properly:

- `*/stay/geihinkan.html` — an orphan duplicate of `*/geihinkan/`. Nothing links
  to it except its own language switcher. It now canonicalises onto the real
  page and is out of the sitemap; it could be 301'd in `vercel.json` and deleted.
- `zh-hans/restaurant.html`, `zh-hant/restaurant.html` — pre-migration stubs.
  They were standing up a second, unrelated `Restaurant` entity in the graph;
  they now reference the canonical one. Same treatment: 301 and delete.
- `*/seiseikan/` — already 301'd in `vercel.json`; the files could go.

Each of these is a deletion, so verify the redirect works on Vercel *before*
removing the file, per the deployment invariants in `CLAUDE.md`.

### P2-5. Internal links still point at trailing-slash URLs

Internal `href`s use `/ja/experiences/kyudo/`, which Vercel 308-redirects to
`/ja/experiences/kyudo`. Everything works, but every internal click costs a
redirect hop and crawlers spend budget on it.

Not changed here: it is a bulk rewrite across 155 files and carries exactly the
kind of risk `CLAUDE.md` warns about, for a modest gain. Worth doing
deliberately, on its own, with a full pre-flight audit — not folded into an SEO
pass.

---

## What was deliberately not done

For the record, so nobody "fixes" these later by adding them back:

| Not emitted | Why |
|---|---|
| `aggregateRating` / `Review` | No first-party reviews exist. OTA ratings are not Meihodo's to publish. |
| `Person` for the head chef | Résumé unverified — see P0-2. |
| `dateModified` | No real source. Build-time stamping is dishonest. |
| Nightly `price` on buildings | Site publishes no nightly rate; any figure would misquote a guest. Buildings use `ReserveAction`, not `Offer`. |
| `Product` co-type on buildings | Only needed to make `offers` legal, and Google then requires a price we do not have. |
| `award`, `hasCredential` | Nothing on the site substantiates either. |
| OTA links in `sameAs` | `sameAs` means "the same entity". Booking listings are `subjectOf` / `Offer.url`. |
| Partner businesses in `sameAs` | 山水家 and ここりらく are partners (提携), separate entities. |
| `openingHoursSpecification` on `#meihodo` | Only the restaurant publishes hours. The estate's are unstated. |
| Keyword-stuffed `knowsAbout` | Limited to subjects with a page behind them. |
