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
- Homepage tab order and which story each tab shows: `CATEGORIES` in `build.py`. The Escuela feature
  ("Room to Grow") lives in `templates/home.html`, because the PSD lays it out by hand.
- New article: add `content/<slug>.md`, put its photo in `img/`, add the slug to `CATEGORIES` if it
  should own a tab, then rebuild.

## Rules
- **Match the PSD** (house rule). PSD pixel positions are commented in `css/site.css`. At 1920 the
  homepage renders 7,207px tall against the PSD's 7,220.
- **Font:** the PSDs use **Stevie Sans** (Adobe Fonts). Hanken Grotesk stands in, calibrated to the PSD's
  line widths (H1 68px, body 16/21 at weight 240). The CSS stack already lists `"stevie-sans"` first;
  to switch, add the Adobe Fonts kit `<link>` in `build.py` (`FONTS`). The kit's CSS family name is unverified.
- The hero background `img/escuela-hero.jpg` is **rendered from the PSD layers** (photo + its masked
  black fill). Don't re-crop the raw photo; the PSD's uneven darkening won't match with a CSS overlay.
- Motion: hero zoom-out, 22px fade-ups that replay, accordion width animation. Every class that hides
  content is added by JS; reduced motion gets a plain page.

## Open (2026-11-10)
- **Moonlight Tower sits in "The Future" tab** as a stand-in. Ethan hasn't picked its tab. "People" is
  empty ("Stories coming soon").
- About copy and the five calendar events are **lorem ipsum in the PSD**, and on the site.
- Image rights to confirm before this leaves demo: the Hotel Trinity bar, room and seafood images look
  AI-generated ("Illuminated Octopus Bar Lounge.png" etc.) but show as the real hotel. The Sweet Home tab
  photo is `Sweethome-Missionary-04-Bud-Franck.jpg` (likely Austin Chronicle). The Escuela photos have no credit.
- `escuela-dish.jpg` is only 800px wide in the PSD (shown at 1,125). It needs the original.

## Preview
`.claude/launch.json` → `austin-local` (python http.server on 127.0.0.1:8791). For full-page 1920
screenshots use puppeteer from `Teeej Design/server2/node_modules` with the puppeteer
`chrome-headless-shell` in `~/.cache/puppeteer` (never `/Applications/Google Chrome`).
