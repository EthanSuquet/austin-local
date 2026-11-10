#!/usr/bin/env python3
"""Build The Austin Local demo site.

    python3 build.py

Reads content/*.md (one file per story) and writes:
    index.html                     the landing page (YMAU_AustinBlog_LP-00.psd)
    stories/<slug>/index.html      one page per story (YMAU_AustinBlog_InteriorStory-01.psd)

Edit content/ and this file. Never edit the generated .html; the next build overwrites it.

Story file format: front matter between --- lines, then the body.
    ## Heading           a section
    - item               a list item
    ![alt](img.jpg)      an image inside the current section
    ::pair               the next two sections sit side by side
    ::band [img | alt]   the next section is a full-width sage band (image on the left if given)
    ::wide img | alt [| credit]   a full-column image between sections
The first paragraph (or the `dek`, if there is one) is the bold lede.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"

# Homepage accordion, in PSD order. Each tab shows one story; None = no story yet.
CATEGORIES = [
    ("What's Happening", "front-market"),
    ("Eat + Drink", "escuela"),          # the homepage feature, defined below
    ("Culture + Community", "sweet-home"),
    ("The Future", "moonlight-tower"),
    ("People", None),
    ("The Austin Vibe", "hotel-trinity"),
]
DEFAULT_OPEN = "What's Happening"  # the open tab in the PSD

ESCUELA_CARD = {
    "slug": "escuela",
    "kicker": "Oak Hill",
    "card_title": "Room to Grow",
    "card_image": "escuela-sign.jpg",
    "card_alt": "The Escuela Oak Hill mosaic sign",
    "href": "#story",
    "excerpt": [
        ("em", "A 1923 Oak Hill schoolhouse gets a second life as a farm-to-table Tex-Mex restaurant. We went to see if it makes the grade."),
        ("p", "If you've headed out toward Dripping Springs, you've likely passed a low, nondescript limestone building tucked behind a stand of heritage oaks, right where the 290 and 71 split. For half a century it was the site of Oak Hill Elementary. Since September it's been Escuela, Oak Hill's buzzed-about farm-to-table Tex-Mex arrival, and another reminder that some of this city’s best new places stem from our deepest roots."),
    ],
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet">')


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- parsing
def parse(path):
    raw = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
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
        elif mi := re.fullmatch(r'!\[(.*?)\]\((\S+?)\)', chunk.strip()):
            blocks.append(("img", mi.group(2), mi.group(1)))
        else:
            blocks.append(("p", " ".join(lines)))
    meta["blocks"] = blocks
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
    lorem = ("Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et "
             "dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex "
             "ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu "
             "fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
             "mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium "
             "doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto "
             "beatae vitae dicta sunt explicabo. Nemo")
    return f"""
<footer class="about" id="about">
  <p class="label label--line">About</p>
  <div class="about-band">
    <a class="about-logo" href="{prefix}index.html" aria-label="The Austin Local, home"><img src="{prefix}img/logo-gray.svg" alt="The Austin Local" width="345" height="117"></a>
    <p class="about-text reveal">{lorem}</p>
    <div class="about-img"><img src="{prefix}img/about-mural.jpg" alt="Sunlight across a painted mural on a brick wall" loading="lazy" width="1298" height="1310"></div>
  </div>
</footer>"""


def page(title, desc, prefix, body_class, body):
    return f"""{head(title, desc, prefix)}
<body class="{body_class}">
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
            out.append(f'<figure class="inline-fig reveal"><img src="{prefix}img/{b[1]}" alt="{attr(b[2])}" loading="lazy"></figure>')
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
                img = (f'<div class="band-img"><img src="{prefix}img/{args[0]}" alt="{attr(args[1] if len(args) > 1 else "")}" loading="lazy"></div>')
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
        body = '<div class="cat-empty"><p class="label">People</p><p class="cat-title">Stories coming soon.</p></div>'
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


def home(stories):
    by_slug = {s["slug"]: s for s in stories}
    cards = {"escuela": ESCUELA_CARD}
    for s in stories:
        cards[s["slug"]] = {
            "kicker": s["kicker"], "card_title": s["card_title"], "card_image": s["card_image"],
            "card_alt": s.get("hero_alt", ""), "href": f"stories/{s['slug']}/", "excerpt": card_excerpt(s),
        }
    tabs = "\n".join(tab_panel(label, cards.get(slug) if slug else None, i, label == DEFAULT_OPEN)
                     for i, (label, slug) in enumerate(CATEGORIES))
    tpl = (ROOT / "templates" / "home.html").read_text()
    return tpl.replace("{{categories}}", tabs)


def main():
    stories = [parse(p) for p in sorted(CONTENT.glob("*.md"))]
    for s in stories:
        out = ROOT / "stories" / s["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        lede, _ = lede_and_intro(s)
        out.write_text(page(f"{s['title']} | The Austin Local", lede, "../../", "is-story", story_body(s, "../../")))
        print("wrote", out.relative_to(ROOT))
    (ROOT / "index.html").write_text(page(
        "The Austin Local",
        "Stories, food, culture and events from around Austin.",
        "", "is-home", home(stories)))
    print("wrote index.html")


if __name__ == "__main__":
    main()
