# The Austin Local (YMAU Austin Blog)

**What it is (2026-11-10):** a static blog site, **The Austin Local**, for the YMAU account (Asana job
`26394 Austin Blog Design`, Harley's design). It's built from two PSDs in `~/Downloads/`:
`YMAU_AustinBlog_LP-00.psd` (landing page, 1920 × 7220) and `YMAU_AustinBlog_InteriorStory-01.psd`
(story template, 1920 × 5251). It's a **GitHub Pages demo**; Ethan will sort out the domain later.

- Repo: `EthanSuquet/austin-local` (**public**, so Pages works on the free plan; Ethan OK'd it 2026-11-10).
  Pages serves branch **`demo`**. `noindex` is on every page while it's a demo.
- The first four articles came as Word files ("Grok Articles Round 1 (Rewrite)", updated 2026-11-10 with a
  byline, a photo credit and one CC-licensed photo each). Their text is in `content/*.md`, verbatim.

## How it's built
- **Edit `content/`, `templates/home.html`, `build.py` or `css/`; never the generated `index.html` or
  `stories/*/index.html`.** Run `python3 build.py` after any change.
- One `.md` per story. Its front matter sets the homepage tab (`category`), kicker, card title and images.
  The body format (`##` sections, `::pair`, `::band`, `::wide`) is documented at the top of `build.py`.
- **Tabs keep the PSD's names; the weekly Austin Blog sheet's categories map onto them one-to-one** (Ethan,
  2026-11-10; `SHEET_TO_TAB` in `build.py`): Weird → What's Happening · Eat + Drink → Eat + Drink · Health & Wellness →
  Culture + Community · Things to Do → The Future · People → People · Real Estate/Business → The Austin Vibe.
  Article file prefixes follow the sheet (WRD, BIZ, PPL, TODO). A new story's `category:` is the PSD tab name.
- Homepage tab order and which story each tab shows: `CATEGORIES` in `build.py`; a story's own label is `category:` in its `.md`. The Escuela feature
  ("Room to Grow") lives in `templates/home.html`, because the PSD lays it out by hand.
- New article: add `content/<slug>.md`, put its photo in `img/`, add the slug to `CATEGORIES` if it
  should own a tab, then rebuild.

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
- About copy is still **lorem ipsum** (as in the PSD).
- **Calendar of events (2026-11-10):** the PSD's five lorem rows are replaced by the four dated, upcoming events the
  articles state (Sweet Home Sunday worship 11/15, Front Market 11/21–22, Zilker tree lighting 11/29). They're in
  `EVENTS` in `build.py`. They go stale: drop past dates when new articles land.
- Image rights to confirm before this leaves demo: the Hotel Trinity bar, room and seafood images look
  AI-generated ("Illuminated Octopus Bar Lounge.png" etc.) but show as the real hotel. The Sweet Home tab
  photo is `Sweethome-Missionary-04-Bud-Franck.jpg` (likely Austin Chronicle). The Escuela photos have no credit.
- `escuela-dish.jpg` is only 800px wide in the PSD (shown at 1,125). It needs the original.

## Preview
`.claude/launch.json` → `austin-local` (python http.server on 127.0.0.1:8791). For full-page 1920
screenshots use puppeteer from `Teeej Design/server2/node_modules` with the puppeteer
`chrome-headless-shell` in `~/.cache/puppeteer` (never `/Applications/Google Chrome`).
