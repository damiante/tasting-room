"""Build the static site from entry files into _site/.

Usage: python3 scripts/build.py [entries-dir]   (default: entries)
"""
import hashlib
import json
import math
import shutil
import sys
from datetime import date
from html import escape
from pathlib import Path

from drinks import CATEGORIES

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
SITE = "The Tasting Room"
# Changes whenever the stylesheet does, so browsers never keep a stale copy.
CSS_VERSION = hashlib.md5((ROOT / "static" / "style.css").read_bytes()).hexdigest()[:8]


def page(title, body, depth, current=None):
    up = "../" * depth
    nav = "".join(
        f'<a href="{up}{c["key"]}/"{" aria-current=page" if c["key"] == current else ""}>{c["name"]}</a>'
        for c in CATEGORIES)
    full = SITE if title == SITE else f"{escape(title)} | {SITE}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,18,400;1,18,400&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..600&display=swap">
<link rel="stylesheet" href="{up}style.css?v={CSS_VERSION}">
</head>
<body>
<header class="masthead">
  <a class="house" href="{up}./">{SITE}</a>
  <nav aria-label="Shelves">{nav}</nav>
</header>
<main>
{body}
</main>
</body>
</html>
"""


def rating(n, colour):
    if not n:
        return ""
    dots = "".join(f'<span{" class=on" if i < n else ""}></span>' for i in range(5))
    return f'<span class="rating" style="--c:{colour}" role="img" aria-label="Rated {n} out of 5">{dots}</span>'


def nice_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def radar(axes, profile, colour):
    """Inline SVG radar chart, scale 0-5, first axis at twelve o'clock."""
    n, r = len(axes), 100

    def point(i, v):
        a = 2 * math.pi * i / n - math.pi / 2
        return r * v / 5 * math.cos(a), r * v / 5 * math.sin(a)

    pts = lambda vals: " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, v) for i, v in enumerate(vals)))
    rings = "".join(f'<polygon class="ring" points="{pts([lvl] * n)}"/>' for lvl in range(1, 6))
    spokes = "".join(f'<line class="spoke" x1="0" y1="0" x2="{x:.1f}" y2="{y:.1f}"/>'
                     for x, y in (point(i, 5) for i in range(n)))
    labels = ""
    for i, (axis, _) in enumerate(axes):
        x, y = point(i, 6.1)
        anchor = "middle" if abs(x) < 1 else ("start" if x > 0 else "end")
        labels += f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="{anchor}">{escape(axis)}</text>'
    values = [profile.get(axis, 0) for axis, _ in axes]
    summary = ", ".join(f"{axis} {v} of 5" for (axis, _), v in zip(axes, values))
    return f"""<figure class="radar" style="--c:{colour}">
<svg viewBox="-175 -140 350 280" role="img" aria-label="Flavour profile: {escape(summary)}">
{rings}{spokes}<polygon class="shape" points="{pts(values)}"/>{labels}
</svg>
</figure>"""


def menu_line(e, cat, up):
    sub = ", ".join(escape(v) for v in list(e["details"].values())[:2])
    return f"""<li>
  <a href="{up}{cat['key']}/{e['slug']}.html">
    <span class="line"><span class="name">{escape(e['title'])}</span><span class="leader"></span>{rating(e['rating'], cat['colour'])}</span>
    <span class="sub">{sub}</span>
  </a>
</li>"""


def landing(shelves):
    rows = ""
    for cat in CATEGORIES:
        entries = shelves[cat["key"]]
        if entries:
            e = max(entries, key=lambda e: (e["date"], e["number"]))
            recent = (f'<p class="latest">Most recently <a href="{cat["key"]}/{e["slug"]}.html">{escape(e["title"])}</a>, '
                      f'one of {len(entries)} tried.</p>' if len(entries) > 1 else
                      f'<p class="latest">So far just <a href="{cat["key"]}/{e["slug"]}.html">{escape(e["title"])}</a>.</p>')
        else:
            recent = '<p class="latest empty">Nothing poured yet.</p>'
        rows += f"""<li class="shelf" style="--c:{cat['colour']}">
  <h2><a href="{cat['key']}/">{cat['name']}</a></h2>
  <div class="shelf-notes">
    <p>{cat['blurb']}</p>
    {recent}
  </div>
</li>"""
    body = f"""<section class="welcome">
  <h1>Pull up a stool.</h1>
  <p>This is where I keep track of what I've been drinking: the beers, drams and cocktails worth remembering,
  with a note on how each one tasted and where I found it. Take a look along the shelves.</p>
</section>
<ul class="shelves">{rows}</ul>"""
    return page(SITE, body, 0)


def catalogue(cat, entries):
    items = sorted(entries, key=lambda e: e["title"].lower())
    listing = (f'<ul class="menu" style="--c:{cat["colour"]}">{"".join(menu_line(e, cat, "../") for e in items)}</ul>'
               if items else '<p class="empty">Nothing on this shelf yet.</p>')
    body = f"""<section class="shelf-head" style="--c:{cat['colour']}">
  <h1>{cat['name']}</h1>
  <p>{cat['blurb']}</p>
</section>
{listing}"""
    return page(cat["name"], body, 1, cat["key"])


def item(cat, e):
    img = e.get("image") or ""
    if img and not img.startswith("http"):
        img = "../" + img
    photo = f'<img class="photo" src="{escape(img)}" alt="">' if img else ""
    details = "".join(f"<dt>{escape(k)}</dt><dd>{escape(v)}</dd>" for k, v in e["details"].items())
    recipe = ""
    if e.get("ingredients") or e.get("method"):
        recipe = f"""<section class="recipe">
  <div><h2>Ingredients</h2>{e.get('ingredients', '')}</div>
  <div><h2>Method</h2>{e.get('method', '')}</div>
</section>"""
    ref = ""
    if e.get("link"):
        meta = e.get("ref") or {}
        host = e["link"].split("/")[2].removeprefix("www.")
        desc = f"<p>{escape(meta['description'])}</p>" if meta.get("description") else ""
        ref = f"""<aside class="reference">
  <a href="{escape(e['link'])}" rel="noopener">
    <span class="where">Find it on {escape(meta.get('site_name') or host)}</span>
    <span class="what">{escape(meta.get('title') or e['title'])}</span>
  </a>
  {desc}
</aside>"""
    body = f"""<article class="entry" style="--c:{cat['colour']}">
  <a class="back" href="./">{cat['name']}</a>
  {photo}
  <header>
    <h1>{escape(e['title'])}</h1>
    <p class="tasted">{rating(e['rating'], cat['colour'])} Tasted {nice_date(e['date'])}</p>
  </header>
  <div class="profile">
    <dl>{details}</dl>
    {radar(cat['axes'], e['profile'], cat['colour'])}
  </div>
  {recipe}
  <section class="notes">{e.get('notes', '')}</section>
  {ref}
</article>"""
    return page(e["title"], body, 1, cat["key"])


def main(src):
    entries = [json.loads(f.read_text()) for f in sorted(Path(src).glob("*.json"))]
    shelves = {c["key"]: [e for e in entries if e["category"] == c["key"]] for c in CATEGORIES}
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    shutil.copy(ROOT / "static" / "style.css", OUT)
    if (Path(src) / "images").is_dir():
        shutil.copytree(Path(src) / "images", OUT / "images")
    (OUT / "index.html").write_text(landing(shelves))
    for cat in CATEGORIES:
        (OUT / cat["key"]).mkdir()
        (OUT / cat["key"] / "index.html").write_text(catalogue(cat, shelves[cat["key"]]))
        for e in shelves[cat["key"]]:
            (OUT / cat["key"] / f"{e['slug']}.html").write_text(item(cat, e))
    print(f"Built {len(entries)} entries into {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "entries")
