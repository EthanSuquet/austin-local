# The Austin Local (YMAU Austin Blog)

**What it is (2026-11-10):** a static blog site, **The Austin Local**, for the YMAU account (Asana job
`26394 Austin Blog Design`, Harley's design). It's built from two PSDs in `~/Downloads/`:
`YMAU_AustinBlog_LP-00.psd` (landing page, 1920 × 7220) and `YMAU_AustinBlog_InteriorStory-01.psd`
(story template, 1920 × 5251). It's a **GitHub Pages demo**; Ethan will sort out the domain later.

- Repo: `EthanSuquet/austin-local` (**public**, so Pages works on the free plan; Ethan OK'd it 2026-11-10).
  Pages is built from branch **`demo`** by GitHub Actions (`.github/workflows/build.yml`, since 2026-11-12): every
  push to `demo`, plus a daily 11:00 UTC run, runs `build.py --check` then `build.py` and deploys the result. Pages'
  source is "GitHub Actions", so the committed `index.html`/`stories/` are only a local preview; the live site is
  always rebuilt from `content/`. `noindex` is on every page while it's a demo.
- The first four articles came as Word files ("Grok Articles Round 1 (Rewrite)", updated 2026-11-10 with a
  byline, a photo credit and one CC-licensed photo each; Moonlight Tower, Sweet Home and Front Market came again
  later that day with 2–3 more credited photos each). Their text is in `content/*.md`, verbatim. Each photo sits in
  the layout slot nearest its spot in the Word file, with its credit as a caption.

## How it's built
- **Edit `content/`, `templates/home.html`, `build.py` or `css/`; never the generated `index.html` or
  `stories/*/index.html`.** Run `python3 build.py` after any change (it validates first and writes nothing if a
  story is invalid; `python3 build.py --check` validates only). Pushing to `demo` publishes within ~2 minutes.
- One `.md` per story. Its front matter sets the homepage tab (`category`), kicker, card title and images.
  The body format (`##` sections, `::pair`, `::band`, `::wide`) is documented at the top of `build.py`.
- **Tabs keep the PSD's names; the weekly Austin Blog sheet's categories map onto them one-to-one** (Ethan,
  2026-11-10; `SHEET_TO_TAB` in `build.py`): Weird → What's Happening · Eat + Drink → Eat + Drink · Health & Wellness →
  Culture + Community · Things to Do → The Future · People → People · Real Estate/Business → The Austin Vibe.
  Article file prefixes follow the sheet (WRD, BIZ, PPL, TODO). A new story's `category:` is the PSD tab name.
- Homepage tab order is `CATEGORIES` in `build.py` (the PSD's). **Which story a tab shows comes from front matter**
  (2026-11-12): the story in that `category:` with `feature: true`, else the newest by `date:` (undated = 2026-11-10,
  ties go to the later file name). `feature: false` keeps a story off the tabs. Stories that own no tab are still
  built and listed in a "More Stories" block under the calendar (reuses the calendar's row styles; it only appears
  when there's such a story, so the PSD layout is untouched otherwise). `category:` also accepts the sheet's names.
  The Escuela feature ("Room to Grow") lives in `templates/home.html`, because the PSD lays it out by hand; its card
  (`ESCUELA_CARD`) holds the Eat + Drink tab until an Eat + Drink story is pinned or dated after 2026-11-10.
- New article: add `content/<slug>.md` and its photos (`img/<slug>-*.jpg`), push to `demo`. No code edit.
  Deleting the `.md` removes its page on the next build.

## Bot publishing (2026-11-12)
Publishing is fully automatic (Ethan's decision): once a story passes fact check, Swish's bot (gh as EthanSuquet,
on its own computer) commits it **straight to `demo`**; the Action validates, builds and deploys it, and the bot
confirms the live page before telling Ethan. Unpublish = delete the story's `.md` (or `git revert` its commit).

**The bot only touches:**
- `content/<slug>.md`: one story (new, corrected, or deleted). Its events ride in its own front matter.
- `img/<slug>-*.jpg` (or .png/.webp): that story's photos, always prefixed with its slug.
- `content/events.txt`: standalone events only.

**The bot never touches** `templates/`, `css/`, `js/`, `build.py`, `.github/workflows/`, `CLAUDE.md`, the
generated `index.html` / `stories/*/index.html`, or another story's files. Those are Ethan's (Claude Code). The bot
runs `python3 build.py --check` before every push, pulls (rebase) before pushing, and never force-pushes.
If branch protection is ever added to `demo`, allow EthanSuquet or give the bot a fine-grained token scoped to this
repo (Contents read/write).

**Sample story** (`content/zilker-kite-fest.md`; every field; `#` lines in front matter are comments):
```
---
slug: zilker-kite-fest
# a PSD tab name, or a weekly-sheet name (Things to Do -> The Future)
category: The Future
kicker: Zilker Park
title: The sky over Zilker fills up again
card_title: The Sky Over Zilker Fills Up Again
# optional; if present it is the lede instead of the first paragraph
dek: The kite festival is back for its 97th year
byline: Micah Solano
# lead photo + its credit (shown as "Photo: ..."); or `hero:` for an uncredited lead image instead
photo: zilker-kite-fest-1.jpg
photo_credit: Larry D. Moore / CC BY 4.0
card_image: zilker-kite-fest-card.jpg
hero_alt: Kites over the Zilker Park lawn
# optional, default true: card's first paragraph in italics
card_lead_italic: true
# publish date; the newest story in a category takes its tab
date: 2026-11-16
# optional: true pins it to its tab, false keeps it off the tabs ("More Stories" only)
feature: true
source: TODO-9-kite-fest-article.docx
# repeatable; date | title | location | text | image | alt [| link, default this story]
event: 2027-03-07 | Zilker Kite Festival | Zilker Park, 2100 Barton Springs Road | Free, 10 a.m. to 5 p.m. | zilker-kite-fest-1.jpg | Kites over Zilker Park
---

First paragraph: the bold lede (unless `dek:` is set).

More opening paragraphs before the first heading are the intro.

::pair

## First of two side-by-side sections

Text. An image inside a section, with its credit in quotes:

![Kites tangled in a live oak](zilker-kite-fest-2.jpg "Jane Doe / CC BY-SA 4.0")

## Second of the pair

- a list item
- another

::band zilker-kite-fest-3.jpg | A kite maker at work | Jane Doe / CC BY 4.0

## A full-width sage band with the photo on the left

Text.

::wide zilker-kite-fest-4.jpg | The lawn at dusk | Carol M. Highsmith / public domain

## A plain section after a full-column image

Text.

::band

## A sage band with no photo (good for "If You Go")

Text.
```
`python3 build.py --check` fails (exit 1, every problem listed) on: missing front matter or required fields, a slug
that isn't lowercase-hyphenated or doesn't match its file name, a duplicate slug, an unknown category, a bad date or
`feature`, any missing image (photo, card, inline, band, wide, event), a malformed event, an unknown `::` directive,
or a body that won't render. A failed check fails the Action, and the live site stays as it was.

## Rules
- **Match the PSD** (house rule). PSD pixel positions are commented in `css/site.css`. At 1920 every
  homepage section sits within ~6px of the PSD; the page is 380px shorter only because the calendar has 4 rows, not 5.
- **Font: Stevie Sans via Adobe Fonts web project "The Austin Local", ID `rqk0gvx`** (created 2026-11-10 in the
  Adobe account Chrome is signed in to, Swish's). Five styles: Light 300, Light Italic, Book 400, Regular 500,
  Medium 600. Set in `build.py` (`ADOBE_KIT`), which adds `.has-stevie` to `<body>`; the overrides are the
  "Stevie Sans" block in `css/site.css`. At the PSD's own sizes (body 16/21, H1 66px) it matches the PSD's line
  widths within 1%. Clearing `ADOBE_KIT` falls back to Hanken Grotesk, already calibrated. Don't self-host Stevie:
  Adobe Fonts covers web projects only.
- The hero background `img/escuela-hero.jpg` is **rendered from the PSD layers** (photo + its masked
  black fill). Don't re-crop the raw photo; the PSD's uneven darkening won't match with a CSS overlay.
- Motion: hero zoom-out, 22px fade-ups that replay, accordion width animation. Every class that hides
  content is added by JS; reduced motion gets a plain page.

## Open (2026-11-10)
- **Culture + Community** (= the sheet's Health & Wellness) has no story yet ("Stories coming soon"); the 11/2 sheet confirmed none.
- **About copy** is Ethan's (2026-11-10), in `about()` in `build.py`.
- **Calendar of events:** dated, upcoming events from the articles, as `event:` lines in each story's front matter
  (standalone events: `content/events.txt`; same `date | title | location | text | image | alt [| link]` format; the
  weekday is derived). **Past events drop off automatically** (Ethan, 2026-11-10): the build skips any event dated before
  today in Austin time, and `js/site.js` removes them in the browser the morning after, so the live page stays
  right without a rebuild. With none left it shows "More events coming soon." Test with `?today=YYYY-MM-DD`.
  Sweet Home's Sunday worship was taken off (it'd be past by launch).
- Image rights to confirm before this leaves demo: the Hotel Trinity bar, room and seafood images look
  AI-generated ("Illuminated Octopus Bar Lounge.png" etc.) but show as the real hotel. The Sweet Home tab
  photo is `Sweethome-Missionary-04-Bud-Franck.jpg` (likely Austin Chronicle). The Escuela photos have no credit.
- `escuela-dish.jpg` is only 800px wide in the PSD (shown at 1,125). It needs the original.

## Preview
`.claude/launch.json` → `austin-local` (python http.server on 127.0.0.1:8791). For full-page 1920
screenshots use puppeteer from `Teeej Design/server2/node_modules` with the puppeteer
`chrome-headless-shell` in `~/.cache/puppeteer` (never `/Applications/Google Chrome`).
