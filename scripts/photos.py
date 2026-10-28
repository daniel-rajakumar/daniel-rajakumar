"""Build the photo strip from the newest photos on my photography site.

Reads data/photos.json from the photography-website repo, takes the newest
photos that aren't hidden, shrinks them to square thumbnails, and embeds them
in one SVG per theme, styled like the rest of the profile.

Needs Pillow. Run from the repo root: python3 scripts/photos.py
Writes assets/photos-{dark,light}.svg.
"""

import base64
import html
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

from make_art import SANS, THEMES

SOURCE = "https://raw.githubusercontent.com/daniel-rajakumar/photography-website/main"
COUNT = 4
TILE = 270  # thumbnail size in the SVG
PIXELS = 400  # thumbnail size in the embedded JPEG, a bit sharper than TILE
GAP = 16
PAD = 24


def fetch(path: str) -> bytes:
    url = SOURCE + urllib.parse.quote(path)
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def thumbnail(data: bytes) -> str:
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    image = ImageOps.fit(image, (PIXELS, PIXELS), Image.LANCZOS)
    out = io.BytesIO()
    image.save(out, "JPEG", quality=80, optimize=True, progressive=True)
    return base64.b64encode(out.getvalue()).decode()


def newest_photos() -> list[dict]:
    photos = json.loads(fetch("/data/photos.json"))
    visible = [p for p in photos if not p.get("hidden")]
    visible.sort(key=lambda p: p["date"], reverse=True)
    picked = visible[:COUNT]
    for p in picked:
        p["thumb"] = thumbnail(fetch("/public" + p["imagePath"]))
    return picked


def strip(photos: list[dict], t: dict) -> str:
    width = PAD * 2 + COUNT * TILE + (COUNT - 1) * GAP
    height = PAD + TILE + 66
    tiles = []
    for i, p in enumerate(photos):
        x = PAD + i * (TILE + GAP)
        when = datetime.fromisoformat(p["date"].replace("Z", "+00:00")).strftime("%b %Y")
        place = p.get("location", "").split(",")[0]
        tiles.append(f"""
  <g>
    <clipPath id="clip{i}"><rect x="{x}" y="{PAD}" width="{TILE}" height="{TILE}" rx="14"/></clipPath>
    <g clip-path="url(#clip{i})">
      <image class="photo" style="animation-delay:-{i * 3}s;transform-origin:{x + TILE / 2}px {PAD + TILE / 2}px"
        x="{x}" y="{PAD}" width="{TILE}" height="{TILE}" preserveAspectRatio="xMidYMid slice"
        href="data:image/jpeg;base64,{p['thumb']}"/>
    </g>
    <rect x="{x + 0.5}" y="{PAD + 0.5}" width="{TILE - 1}" height="{TILE - 1}" rx="14" fill="none" stroke="{t['border']}"/>
    <text class="title" x="{x + 2}" y="{PAD + TILE + 28}">{html.escape(p['title'])}</text>
    <text class="meta" x="{x + 2}" y="{PAD + TILE + 48}">{html.escape(place)} · {when}</text>
  </g>""")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="My latest photos">
  <title>My latest photos</title>
  <defs>
    <style>
      .title {{ font: 600 15px {SANS}; fill: {t['text']}; }}
      .meta {{ font: 400 12.5px {SANS}; fill: {t['dim']}; }}
      .photo {{ animation: drift 14s ease-in-out infinite alternate; }}
      @keyframes drift {{ from {{ transform: scale(1) }} to {{ transform: scale(1.07) }} }}
      @media (prefers-reduced-motion: reduce) {{ .photo {{ animation: none; }} }}
    </style>
  </defs>{''.join(tiles)}
</svg>
"""


def main() -> None:
    photos = newest_photos()
    root = Path(__file__).resolve().parent.parent / "assets"
    for name, theme in THEMES.items():
        (root / f"photos-{name}.svg").write_text(strip(photos, theme))


if __name__ == "__main__":
    main()
