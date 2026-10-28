"""Turn a GitHub issue (from an Actions event payload) into entries/<number>.json.

Usage: python3 scripts/post.py "$GITHUB_EVENT_PATH"
"""
import json
import mimetypes
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from drinks import CATEGORIES

ENTRIES = Path(__file__).resolve().parent.parent / "entries"
UA = {"User-Agent": "tasting-room (+https://github.com)"}


def sections(body):
    """Issue forms render as '### Label' followed by the answer."""
    parts = re.split(r"^### (.+?)\s*$", body.replace("\r\n", "\n"), flags=re.M)
    return {k: v.strip() for k, v in zip(parts[1::2], parts[2::2])
            if v.strip() not in ("", "_No response_", "None")}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "untitled"


def parse(issue):
    labels = {label["name"] for label in issue.get("labels", [])}
    cat = next((c for c in CATEGORIES if c["key"] in labels), None)
    if not cat:
        sys.exit(f"Issue #{issue['number']} needs one of these labels: {', '.join(c['key'] for c in CATEGORIES)}")
    s = sections(issue.get("body") or "")
    url = lambda text: (re.search(r"https?://[^\s)\"'<>\]]+", text or "") or [None])[0]
    return {
        "number": issue["number"],
        "title": issue["title"].strip(),
        "category": cat["key"],
        "date": issue["created_at"][:10],
        "rating": int(s["Rating"][0]) if s.get("Rating", "")[:1].isdigit() else None,
        "details": {label: s[label] for label, _ in cat["fields"] if label in s},
        "profile": {axis: int(s[axis]) for axis, _ in cat["axes"] if s.get(axis, "").isdigit()},
        # Markdown for now; render() swaps these for HTML.
        "notes": s.get("Tasting notes", ""),
        "ingredients": s.get("Ingredients", ""),
        "method": s.get("Method", ""),
        "image": url(s.get("Photo")),
        "link": url(s.get("Link")),
    }


def fetch(url, data=None, headers=None, limit=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(limit), r.headers.get_content_type()


def markdown(text, repo):
    """Render with GitHub's own renderer so the page matches the issue preview."""
    if not text:
        return ""
    headers = {"Accept": "application/vnd.github+json", "Content-Type": "application/json"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    body = json.dumps({"text": text, "mode": "gfm", "context": repo}).encode()
    return fetch("https://api.github.com/markdown", body, headers)[0].decode()


class OpenGraph(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        key = a.get("property") or a.get("name") or ""
        if tag == "meta" and key.startswith("og:") and a.get("content"):
            self.meta.setdefault(key[3:], a["content"].strip())


def reference(link):
    """Best effort: many sites (Untappd included) block bots, so a bare link is fine."""
    try:
        page = OpenGraph()
        page.feed(fetch(link, limit=500_000)[0].decode("utf-8", "replace"))
        return {k: page.meta[k] for k in ("title", "description", "site_name") if k in page.meta}
    except Exception as e:
        print(f"Could not read {link}: {e}")
        return {}


def save_image(entry):
    """Copy the issue attachment into the repo so the page doesn't depend on it."""
    for old in (ENTRIES / "images").glob(f"{entry['number']}.*"):
        old.unlink()
    try:
        data, kind = fetch(entry["image"])
        ext = {"image/jpeg": ".jpg"}.get(kind) or mimetypes.guess_extension(kind) or ".jpg"
        path = ENTRIES / "images" / f"{entry['number']}{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"images/{path.name}"
    except Exception as e:
        print(f"Could not download {entry['image']}, linking to it instead: {e}")
        return entry["image"]


def unique_slug(entry):
    slug = slugify(entry["title"])
    for f in ENTRIES.glob("*.json"):
        other = json.loads(f.read_text())
        if other["number"] != entry["number"] and other["category"] == entry["category"] and other["slug"] == slug:
            return f"{slug}-{entry['number']}"
    return slug


def main(event_path):
    event = json.loads(Path(event_path).read_text())
    repo = event["repository"]["full_name"]
    entry = parse(event["issue"])
    for key in ("notes", "ingredients", "method"):
        entry[key] = markdown(entry[key], repo)
    if entry["image"]:
        entry["image"] = save_image(entry)
    entry["ref"] = reference(entry["link"]) if entry["link"] else {}
    entry["slug"] = unique_slug(entry)
    ENTRIES.mkdir(exist_ok=True)
    (ENTRIES / f"{entry['number']}.json").write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
    path = f"{entry['category']}/{entry['slug']}.html"
    print(f"Wrote entry #{entry['number']} for {path}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as out:
            out.write(f"path={path}\n")


if __name__ == "__main__":
    main(sys.argv[1])
