# The Austin Local

Static demo of The Austin Local blog, built from Storyhaus's PSDs.

```
python3 build.py                              # regenerate index.html and stories/
python3 -m http.server 8791 --bind 127.0.0.1  # preview at http://127.0.0.1:8791
```

Stories live in `content/*.md`; the format is documented at the top of `build.py`.
Generated HTML is committed so GitHub Pages can serve it as-is.
