# The Austin Local

Static demo of The Austin Local blog, built from Storyhaus's PSDs.

```
python3 build.py --check                      # validate content/ only
python3 build.py                              # validate, then regenerate index.html and stories/
python3 -m http.server 8791 --bind 127.0.0.1  # preview at http://127.0.0.1:8791
```

Stories live in `content/*.md`; the format is documented at the top of `build.py`.
Publishing: every push to `demo` (and a daily run) builds the site in GitHub Actions
(`.github/workflows/build.yml`) and deploys it to Pages; see "Bot publishing" in `CLAUDE.md`.
The committed HTML is a local preview only; the live site is always rebuilt from `content/`.
