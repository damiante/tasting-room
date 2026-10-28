# The Tasting Room

A catalogue of drinks I've tried, published to GitHub Pages from GitHub Issues.
Plain Python 3.12+ standard library, no dependencies.

## Adding a drink

1. **New issue**, pick the drink type, and name the issue after the drink.
2. Fill in the details, the flavour profile, notes, and optionally a photo and link.
3. Comment `/post` on the issue. The workflow saves it to `entries/<issue number>.json`,
   rebuilds the site, replies with the page link, and closes the issue.

To change an entry later, edit the issue (open or closed) and comment `/post` again.
Only the repo owner's `/post` on the owner's own issues does anything.

## Running locally

```sh
python3 scripts/build.py              # builds entries/ (or pass another folder of entries)
python3 -m http.server -d _site 8000  # then open http://localhost:8000
python3 scripts/test_post.py          # parser check (run from anywhere)
```

## One-time GitHub setup

- **Settings > Pages > Source:** GitHub Actions.
- Create the labels the issue templates apply (a template's label is ignored if the label doesn't exist):
  ```sh
  for l in beer whiskey gin other-spirits cocktails wine; do gh label create "$l"; done
  ```

## Changing categories or flavour axes

Edit `scripts/drinks.py`, then run `python3 scripts/drinks.py` to regenerate `.github/ISSUE_TEMPLATE/`.
Existing entries keep the scores they were posted with; renamed axes show as 0 until re-posted.
