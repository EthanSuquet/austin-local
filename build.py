#!/usr/bin/env python3
"""Build The Austin Local demo site.

    python3 build.py           validate, then build (stops with errors if a story is invalid)
    python3 build.py --check   validate only (front matter, images, slugs, events); exit 1 on any error

Reads content/*.md (one file per story) plus content/events.txt (standalone events) and writes:
    index.html                     the landing page (YMAU_AustinBlog_LP-00.psd)
    stories/<slug>/index.html      one page per story (YMAU_AustinBlog_InteriorStory-01.psd)

Edit content/ and this file. Never edit the generated .html; the next build overwrites it.

Story file format: front matter between --- lines, then the body.
    ## Heading           a section
    - item               a list item
    ![alt](img.jpg "credit")  an image inside the current section (credit optional)
    ::pair               the next two sections sit side by side
    ::band [img | alt [| credit]]   the next section is a full-width sage band (image on the left if given)
    ::wide img | alt [| credit]   a full-column image between sections
The first paragraph (or the `dek`, if there is one) is the bold lede.

Front matter (one `key: value` per line):
    slug          required; lowercase letters, digits, hyphens; must match the file name (content/<slug>.md)
    category      required; a homepage tab name (CATEGORIES) or a weekly-sheet name (SHEET_TO_TAB keys)
    kicker, title, card_title, byline, card_image, hero_alt   required
    photo         required unless `hero` is set: the story's lead photo; `photo_credit` is its caption
    hero          optional: a lead image with no credit (overrides photo as the page's hero)
    dek           optional: the lede, instead of the first paragraph
    card_lead_italic   optional, true/false (default true): the card's first paragraph in italics
    date          optional, YYYY-MM-DD publish date (stories without one count as 2026-11-10)
    feature       optional: true = pin this story to its tab; false = never take the tab (archive only)
    source        optional: the Word file it came from
    event         optional, repeatable; one calendar event per line:
                  event: YYYY-MM-DD | title | location | text | image | alt [| link]
                  (link defaults to this story's page)

Homepage tabs: each tab shows its pinned story (feature: true), else the newest story (by `date`, then file
name) in that category. Stories bumped off a tab stay built and are listed under "More stories".
"""
import html
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"

# Homepage accordion: the PSD's tab names, in PSD order. Each tab shows one story; None = nothing there yet.
# The weekly Austin Blog sheet (Austin-Blog-Weekly-Sheet-2026-11-02, v5) uses its own category names; they map
# one-to-one onto these tabs (Ethan, 2026-11-10, keeping the stories where the PSD placed them). Article file
# prefixes follow the sheet: WRD = Weird, BIZ = Real Estate/Business, PPL = People, TODO = Things to Do.
SHEET_TO_TAB = {
    "Weird": "What's Happening",
    "Eat + Drink": "Eat + Drink",
    "Health & Wellness": "Culture + Community",
    "Things to Do": "The Future",
    "People": "People",
    "Real Estate/Business": "The Austin Vibe",
}
# Tab order is fixed (the PSD's). Which story a tab shows comes from the stories' own front matter (see the top
# of this file): pinned (`feature: true`), else the newest in that category. A new story claims its tab with no
# code edit here.
CATEGORIES = ["What's Happening", "Eat + Drink", "Culture + Community", "The Future", "People", "The Austin Vibe"]
DEFAULT_OPEN = "What's Happening"  # the open tab in the PSD
# The Escuela feature is laid out by hand in templates/home.html; its card holds the Eat + Drink tab until an
# Eat + Drink story is pinned or dated after it.
HOUSE_CARDS = {"Eat + Drink": "escuela"}

ESCUELA_CARD = {
    "slug": "escuela",
    "kicker": "Oak Hill",
    "card_title": "Room to Grow",
    "card_image": "escuela-sign.jpg",
    "card_alt": "The Escuela Oak Hill mosaic sign",
    "href": "#story",
    "date": "2026-11-10",
    "excerpt": [
        ("em", "A 1923 Oak Hill schoolhouse gets a second life as a farm-to-table Tex-Mex restaurant. We went to see if it makes the grade."),
        ("p", "If you've headed out toward Dripping Springs, you've likely passed a low, nondescript limestone building tucked behind a stand of heritage oaks, right where the 290 and 71 split. For half a century it was the site of Oak Hill Elementary. Since September it's been Escuela, Oak Hill's buzzed-about farm-to-table Tex-Mex arrival, and another reminder that some of this city’s best new places stem from our deepest roots."),
    ],
}

# Adobe Fonts web project for Stevie Sans (fonts.adobe.com/fonts/stevie-sans; CSS name "stevie-sans").
# Paste the project ID (the "abc1def" in use.typekit.net/abc1def.css) here and rebuild. Empty = Hanken Grotesk stand-in.
ADOBE_KIT = "rqk0gvx"  # "The Austin Local" web project, created 2026-11-10 on the Storyhaus Adobe account

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet">')
if ADOBE_KIT:
    FONTS = f'<link rel="preconnect" href="https://use.typekit.net" crossorigin><link rel="stylesheet" href="https://use.typekit.net/{ADOBE_KIT}.css">'


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


# Calendar of events: dated, upcoming things the articles themselves state. They live with their story, as
# `event:` lines in its front matter, or (for events with no story) in content/events.txt, one per line:
#     YYYY-MM-DD | title | location | text | image | alt [| link]
# Each event drops off the calendar once its date has passed in Austin (America/Chicago) time, twice over:
#   - here, at build time (a past event isn't written into index.html at all), and
#   - in js/site.js, in the visitor's browser, from each row's data-date, so it disappears the next morning
#     even if nobody rebuilds. If no events are left, "More events coming soon." shows instead.
# The weekday and day number come from the date.
EVENTS_FILE = CONTENT / "events.txt"
DEFAULT_DATE = "2026-11-10"  # stories (and the Escuela feature) without a `date:` count as this old


def parse_event(line, default_link=""):
    """'date | title | location | text | image | alt [| link]' -> tuple, or raise ValueError."""
    f = [x.strip() for x in line.split("|")]
    if len(f) not in (6, 7):
        raise ValueError(f"needs 6 or 7 |-separated fields (date | title | location | text | image | alt [| link]), got {len(f)}")
    date.fromisoformat(f[0])
    if not all(f[:6]):
        raise ValueError("date, title, location, text, image and alt can't be empty")
    link = f[6] if len(f) == 7 and f[6] else default_link
    return (f[0], f[1], f[2], f[3], f[4], f[5], link)


def load_events(stories):
    events = []
    for s in stories:
        for line in s.get("events", []):
            events.append(parse_event(line, f"stories/{s['slug']}/"))
    if EVENTS_FILE.exists():
        for line in EVENTS_FILE.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                events.append(parse_event(line))
    return events


def austin_today():
    return datetime.now(ZoneInfo("America/Chicago")).date()


def events_html(events):
    today = austin_today()
    rows = []
    for iso, title, loc, text, img, alt, link in sorted(events):
        d = date.fromisoformat(iso)
        if d < today:
            continue
        rows.append(
            f'    <li class="event reveal" data-date="{iso}"><p class="event-date"><span>{d:%a}</span><b>{d.day}</b></p>'
            f'<img src="img/{img}" alt="{attr(alt)}" loading="lazy" width="1016" height="606">'
            f'<div class="event-text"><h3>{esc(title)}</h3><p class="label">{esc(loc)}</p><p>{esc(text)}</p></div>'
            + (f'<a class="event-link" href="{attr(link)}" aria-label="Read the story: {attr(title)}"><img src="img/arrow.svg" alt="" width="40" height="40"></a>' if link else '')
            + '</li>')
    empty = "" if rows else " is-shown"
    return "\n".join(rows), empty


# ---------------------------------------------------------------- parsing
def parse(path):
    raw = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    if not m:
        raise ValueError("no front matter (the file must start with a --- line and close it with another ---)")
    meta = {"events": [], "_file": path.name}
    for n, line in enumerate(m.group(1).splitlines(), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        k, sep, v = line.partition(":")
        if not sep or not k.strip():
            raise ValueError(f"front matter line {n} isn't `key: value`: {line!r}")
        k, v = k.strip(), v.strip()
        if k == "event":
            meta["events"].append(v)
        elif k in meta:
            raise ValueError(f"front matter key `{k}` appears twice")
        else:
            meta[k] = v
    blocks = []
    for chunk in re.split(r"\n\s*\n", m.group(2).strip()):
        lines = chunk.strip().splitlines()
        if all(l.startswith("- ") for l in lines):
            blocks.append(("ul", [l[2:] for l in lines]))
        elif chunk.startswith("## "):
            blocks.append(("h", chunk[3:].strip()))
        elif chunk.startswith("::"):
            name, _, arg = chunk[2:].partition(" ")
            blocks.append(("dir", name, [a.strip() for a in arg.split("|")] if arg.strip() else []))
        elif mi := re.fullmatch(r'!\[(.*?)\]\((\S+?)(?:\s+"(.*?)")?\)', chunk.strip()):
            blocks.append(("img", mi.group(2), mi.group(1), mi.group(3) or ""))
        else:
            blocks.append(("p", " ".join(lines)))
    meta["blocks"] = blocks
    meta["category"] = SHEET_TO_TAB.get(meta.get("category", ""), meta.get("category", ""))
    meta["card_lead_italic"] = meta.get("card_lead_italic", "true") == "true"
    return meta


def lede_and_intro(story):
    pre = []
    for b in story["blocks"]:
        if b[0] != "p":
            break
        pre.append(b[1])
    if story.get("dek"):
        return story["dek"], pre
    return pre[0], pre[1:]


def card_excerpt(story, words=110):
    lede, intro = lede_and_intro(story)
    out = [("em" if story["card_lead_italic"] else "p", lede)]
    n = len(lede.split())
    for p in intro:
        if n >= words:
            break
        out.append(("p", p))
        n += len(p.split())
    return out


# ---------------------------------------------------------------- shared chrome
def head(title, desc, prefix):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{esc(title)}</title>
<meta name="description" content="{attr(desc)}">
<link rel="icon" href="{prefix}img/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="{prefix}css/site.css">
<script>document.documentElement.classList.add('js')</script>
</head>"""


def about(prefix):
    # About copy from Ethan, 2026-11-10 (replaces the PSD's lorem ipsum).
    paras = [
        "Austin changes fast. Restaurants open and close, buildings change hands, and whole blocks look different "
        "from one year to the next. Plenty of people cover what's new. Fewer stick around long enough to explain "
        "what it means for the people who live here.",
        "The Austin Local covers the center of the city: downtown, Clarksville, Bouldin Creek, Zilker and the "
        "neighborhoods around them. We stay inside a small area on purpose, because you only notice how a "
        "neighborhood is changing if you keep coming back to it. You see the same corners, the same institutions "
        "and the same people over months and years.",
        "Change is easy to talk about in big numbers, like new towers, rising rents and record crowds. We'd rather "
        "look at it at street level. We cover the new places and the old ones that make room for them, and the people "
        "who left but keep coming back. We also look at the plans being made now for blocks that will look different "
        "in ten years.",
    ]
    copy = "".join(f"<p>{esc(x)}</p>" for x in paras)
    return f"""
<footer class="about" id="about">
  <p class="label label--line">About</p>
  <div class="about-band">
    <a class="about-logo" href="{prefix}index.html" aria-label="The Austin Local, home"><img src="{prefix}img/logo-gray.svg" alt="The Austin Local" width="345" height="117"></a>
    <div class="about-text reveal">{copy}</div>
    <div class="about-img"><img src="{prefix}img/about-mural.jpg" alt="Sunlight across a painted mural on a brick wall" loading="lazy" width="1298" height="1310"></div>
  </div>
</footer>"""


def page(title, desc, prefix, body_class, body):
    return f"""{head(title, desc, prefix)}
<body class="{body_class}{' has-stevie' if ADOBE_KIT else ''}">
<div class="page">
{body}
{about(prefix)}
</div>
<script src="{prefix}js/site.js" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- story page
def render_blocks(blocks, prefix):
    out = []
    for b in blocks:
        if b[0] == "p":
            out.append(f"<p>{esc(b[1])}</p>")
        elif b[0] == "ul":
            out.append("<ul>" + "".join(f"<li>{esc(i)}</li>" for i in b[1]) + "</ul>")
        elif b[0] == "img":
            cap = f"<figcaption>Photo: {esc(b[3])}</figcaption>" if b[3] else ""
            out.append(f'<figure class="inline-fig reveal"><img src="{prefix}img/{b[1]}" alt="{attr(b[2])}" loading="lazy">{cap}</figure>')
    return "\n".join(out)


def section_html(title, blocks, prefix, cls="sec"):
    return f'<section class="{cls} reveal"><h2>{esc(title)}</h2>\n{render_blocks(blocks, prefix)}\n</section>'


def figure(src, alt, credit, prefix, cls):
    cap = f"<figcaption>Photo: {esc(credit)}</figcaption>" if credit else ""
    return f'<figure class="{cls} reveal"><img src="{prefix}img/{src}" alt="{attr(alt)}" loading="lazy">{cap}</figure>'


def story_body(s, prefix):
    lede, intro = lede_and_intro(s)
    blocks = s["blocks"]
    i = 0
    while i < len(blocks) and blocks[i][0] == "p":
        i += 1
    # group the rest into sections, carrying directives
    items, pending = [], None
    cur = None
    for b in blocks[i:]:
        if b[0] == "dir":
            if b[1] == "wide":
                cur = None
                a = b[2] + ["", ""]
                items.append(("wide", a[0], a[1], a[2]))
            else:
                pending = b
            continue
        if b[0] == "h":
            cur = {"title": b[1], "blocks": [], "dir": pending}
            pending = None
            items.append(("sec", cur))
            continue
        cur["blocks"].append(b)

    parts = []
    k = 0
    while k < len(items):
        it = items[k]
        if it[0] == "wide":
            parts.append(f'<div class="col">{figure(it[1], it[2], it[3], prefix, "wide-fig")}</div>')
            k += 1
            continue
        sec = it[1]
        d = sec["dir"]
        if d and d[1] == "pair" and k + 1 < len(items) and items[k + 1][0] == "sec":
            other = items[k + 1][1]
            parts.append('<div class="col pair">' + section_html(sec["title"], sec["blocks"], prefix)
                         + section_html(other["title"], other["blocks"], prefix) + "</div>")
            k += 2
            continue
        if d and d[1] == "band":
            args = d[2]
            if args:
                cap = f"<figcaption>Photo: {esc(args[2])}</figcaption>" if len(args) > 2 and args[2] else ""
                img = (f'<figure class="band-img"><img src="{prefix}img/{args[0]}" alt="{attr(args[1] if len(args) > 1 else "")}" loading="lazy">{cap}</figure>')
                parts.append(f'<div class="band band--img">{img}<div class="band-text">'
                             + section_html(sec["title"], sec["blocks"], prefix) + "</div></div>")
            else:
                parts.append('<div class="band band--text"><div class="col">'
                             + section_html(sec["title"], sec["blocks"], prefix, "sec sec--box") + "</div></div>")
            k += 1
            continue
        parts.append('<div class="col">' + section_html(sec["title"], sec["blocks"], prefix) + "</div>")
        k += 1

    hero_src = s.get("hero") or s["photo"]
    hero_credit = "" if s.get("hero") else s.get("photo_credit", "")
    hero_alt = s.get("hero_alt", "")
    intro_html = "\n".join(f"<p>{esc(p)}</p>" for p in intro)
    return f"""
<header class="story-head">
  <a class="story-logo" href="{prefix}index.html" aria-label="The Austin Local, home"><img src="{prefix}img/logo-gray.svg" alt="The Austin Local" width="273" height="92"></a>
  <p class="label">{esc(s['category'])}</p>
  <h1>{esc(s['title'])}</h1>
  <p class="byline">By {esc(s['byline'])}</p>
</header>
<main class="story">
  <figure class="story-hero"><img src="{prefix}img/{hero_src}" alt="{attr(hero_alt)}" width="1643" height="831" fetchpriority="high">{f'<figcaption>Photo: {esc(hero_credit)}</figcaption>' if hero_credit else ''}</figure>
  <div class="col"><p class="lede reveal">{esc(lede)}</p></div>
  <div class="col intro reveal">
{intro_html}
  </div>
{chr(10).join(parts)}
  <p class="col back"><a href="{prefix}index.html#categories">← More from The Austin Local</a></p>
</main>"""


# ---------------------------------------------------------------- homepage
def tab_panel(label, card, idx, open_):
    pid = f"cat-{idx}"
    is_open = "true" if open_ else "false"
    tab = (f'<button class="cat-tab" id="{pid}-tab" aria-expanded="{is_open}" aria-controls="{pid}">'
           f'<span>{esc(label)}</span></button>')
    if card is None:
        body = f'<div class="cat-empty"><p class="label">{esc(label)}</p><p class="cat-title">Stories coming soon.</p></div>'
    else:
        ex = "".join(f"<p><em>{esc(t)}</em></p>" if k == "em" else f"<p>{esc(t)}</p>" for k, t in card["excerpt"])
        body = (f'<div class="cat-img"><img src="img/{card["card_image"]}" alt="{attr(card.get("card_alt", ""))}" loading="lazy"></div>'
                f'<div class="cat-text"><p class="label">{esc(card["kicker"])}</p>'
                f'<h3 class="cat-title">{esc(card["card_title"])}</h3>'
                f'<div class="cat-excerpt">{ex}</div>'
                f'<a class="btn" href="{card["href"]}">Read More</a></div>')
    panel = (f'<div class="cat-panel" id="{pid}" role="region" aria-labelledby="{pid}-tab"{"" if open_ else " hidden"}>'
             f'<div class="cat-inner">{body}</div></div>')
    return f'<div class="cat{" is-open" if open_ else ""}">{tab}{panel}</div>'


def tab_owners(stories):
    """{tab: story slug or house card slug or None}, plus the stories that own no tab (newest first)."""
    owners = {}
    for tab in CATEGORIES:
        cands = [s for s in stories if s["category"] == tab and s.get("feature") != "false"]
        key = lambda s: (s.get("date") or DEFAULT_DATE, s["_file"])
        pinned = [s for s in cands if s.get("feature") == "true"]
        best = max(pinned or cands, key=key, default=None)
        house = HOUSE_CARDS.get(tab)
        if house and (best is None or (not pinned and key(best)[0] <= ESCUELA_CARD["date"])):
            owners[tab] = house
        else:
            owners[tab] = best["slug"] if best else None
    taken = set(owners.values())
    rest = sorted((s for s in stories if s["slug"] not in taken),
                  key=lambda s: (s.get("date") or DEFAULT_DATE, s["_file"]), reverse=True)
    return owners, rest


def more_stories_html(rest):
    """Stories bumped off (or kept off) the tabs. Empty when every story has a tab, so the PSD layout is untouched."""
    if not rest:
        return ""
    rows = []
    for s in rest:
        lede, _ = lede_and_intro(s)
        rows.append(
            f'    <li class="event reveal"><img src="img/{s["card_image"]}" alt="{attr(s.get("hero_alt", ""))}" loading="lazy" width="1016" height="606">'
            f'<div class="event-text"><h3>{esc(s["card_title"])}</h3><p class="label">{esc(s["category"])} · {esc(s["kicker"])}</p><p>{esc(lede)}</p></div>'
            f'<a class="event-link" href="stories/{s["slug"]}/" aria-label="Read the story: {attr(s["card_title"])}"><img src="img/arrow.svg" alt="" width="40" height="40"></a></li>')
    return ('\n\n<section class="events more-stories" id="more-stories" aria-labelledby="more-h">\n'
            '  <h2 class="label events-h" id="more-h">More Stories</h2>\n  <ol class="event-list">\n'
            + "\n".join(rows) + '\n  </ol>\n</section>')


def home(stories, events):
    cards = {"escuela": ESCUELA_CARD}
    for s in stories:
        cards[s["slug"]] = {
            "kicker": s["kicker"], "card_title": s["card_title"], "card_image": s["card_image"],
            "card_alt": s.get("hero_alt", ""), "href": f"stories/{s['slug']}/", "excerpt": card_excerpt(s),
        }
    owners, rest = tab_owners(stories)
    tabs = "\n".join(tab_panel(label, cards.get(owners[label]) if owners[label] else None, i, label == DEFAULT_OPEN)
                     for i, label in enumerate(CATEGORIES))
    tpl = (ROOT / "templates" / "home.html").read_text()
    rows, empty = events_html(events)
    return (tpl.replace("{{categories}}", tabs).replace("{{events}}", rows).replace("{{events_empty}}", empty)
            .replace("{{more_stories}}", more_stories_html(rest)))


# ---------------------------------------------------------------- validation
REQUIRED = ["slug", "category", "kicker", "title", "card_title", "byline", "card_image", "hero_alt"]
DIRECTIVES = {"pair", "band", "wide"}


def check():
    """Return (stories, events, errors). Nothing is written."""
    errors, stories, seen = [], [], {}
    img = ROOT / "img"

    def need_img(where, name):
        if not name:
            errors.append(f"{where}: image name is empty")
        elif "/" in name or not (img / name).is_file():
            errors.append(f"{where}: image img/{name} not found")

    for path in sorted(CONTENT.glob("*.md")):
        f = f"content/{path.name}"
        try:
            s = parse(path)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{f}: {e}")
            continue
        n = len(errors)
        for k in REQUIRED:
            if not s.get(k):
                errors.append(f"{f}: missing `{k}:`")
        if not (s.get("photo") or s.get("hero")):
            errors.append(f"{f}: needs `photo:` (or `hero:`)")
        slug = s.get("slug", "")
        if slug and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            errors.append(f"{f}: slug `{slug}` must be lowercase letters, digits and hyphens")
        if slug and slug != path.stem:
            errors.append(f"{f}: slug `{slug}` must match the file name ({path.stem})")
        if slug in seen or slug == "escuela":
            errors.append(f"{f}: slug `{slug}` is already used by {seen.get(slug, 'the Escuela feature')}")
        seen[slug] = f
        if s.get("category") and s["category"] not in CATEGORIES:
            errors.append(f"{f}: category `{s['category']}` isn't a tab ({', '.join(CATEGORIES)}) or a sheet name ({', '.join(SHEET_TO_TAB)})")
        if s.get("date"):
            try:
                date.fromisoformat(s["date"])
            except ValueError:
                errors.append(f"{f}: date `{s['date']}` must be YYYY-MM-DD")
        for k in ("feature",):
            if k in s and s[k] not in ("true", "false"):
                errors.append(f"{f}: `{k}:` must be true or false")
        for k in ("photo", "hero", "card_image"):
            if s.get(k):
                need_img(f"{f} `{k}:`", s[k])
        for b in s.get("blocks", []):
            if b[0] == "img":
                need_img(f"{f} inline image", b[1])
            elif b[0] == "dir":
                if b[1] not in DIRECTIVES:
                    errors.append(f"{f}: unknown directive ::{b[1]} (use ::pair, ::band or ::wide)")
                elif b[1] == "wide" and not b[2]:
                    errors.append(f"{f}: ::wide needs `img | alt [| credit]`")
                elif b[1] in ("band", "wide") and b[2]:
                    need_img(f"{f} ::{b[1]}", b[2][0])
        for line in s.get("events", []):
            try:
                ev = parse_event(line, f"stories/{slug}/")
                need_img(f"{f} event {ev[0]}", ev[4])
            except ValueError as e:
                errors.append(f"{f}: event `{line[:40]}...`: {e}")
        if len(errors) == n:
            try:
                lede_and_intro(s)
                story_body(s, "../../")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{f}: body doesn't render ({type(e).__name__}: {e}). It needs an opening paragraph "
                              "(or `dek:`), and every ::pair/::band must sit right before a ## heading")
                continue
            stories.append(s)
    events = []
    if EVENTS_FILE.exists():
        for n, line in enumerate(EVENTS_FILE.read_text().splitlines(), 1):
            if line.strip() and not line.lstrip().startswith("#"):
                try:
                    ev = parse_event(line)
                    need_img(f"content/events.txt line {n}", ev[4])
                except ValueError as e:
                    errors.append(f"content/events.txt line {n}: {e}")
    if not errors:
        events = load_events(stories)
        try:
            home(stories, events)
        except Exception as e:  # noqa: BLE001
            errors.append(f"homepage doesn't render: {type(e).__name__}: {e}")
    return stories, events, errors


def main():
    stories, events, errors = check()
    if errors:
        print(f"build.py: {len(errors)} problem(s); nothing was written:", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        sys.exit(1)
    if "--check" in sys.argv[1:]:
        owners, rest = tab_owners(stories)
        print(f"ok: {len(stories)} stories, {len(events)} events")
        for tab in CATEGORIES:
            print(f"  tab {tab!r}: {owners[tab] or '(coming soon)'}")
        if rest:
            print("  more stories:", ", ".join(s["slug"] for s in rest))
        return
    for s in stories:
        out = ROOT / "stories" / s["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        lede, _ = lede_and_intro(s)
        out.write_text(page(f"{s['title']} | The Austin Local", lede, "../../", "is-story", story_body(s, "../../")))
        print("wrote", out.relative_to(ROOT))
    # a story whose .md was deleted loses its page (only folders holding nothing but a generated index.html)
    slugs = {s["slug"] for s in stories}
    for d in sorted((ROOT / "stories").glob("*/")):
        if d.name not in slugs and [x.name for x in d.iterdir()] == ["index.html"]:
            shutil.rmtree(d)
            print("removed", d.relative_to(ROOT))
    (ROOT / "index.html").write_text(page(
        "The Austin Local",
        "Stories, food, culture and events from around Austin.",
        "", "is-home", home(stories, events)))
    print("wrote index.html")


if __name__ == "__main__":
    main()
