"""Generate the animated SVGs used in the profile README.

The look follows danielrajakumar.com: charcoal cards, one green accent,
Poppins type, and the short green bar under headings.

Run from the repo root: python3 scripts/make_art.py
Writes assets/hero-{dark,light}.svg (with the current New Jersey time in its
status pill) and assets/card-<project>-{dark,light}.svg.
"""

import html
import textwrap
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROLES = [
    "Software Engineer",
    "Building RockyGPT",
    "Retrieval systems + evals",
    "Next.js · TypeScript · Python",
]
CYCLE = 16  # seconds for one pass through every role
CHAR_W = 0.6  # monospace character width, as a share of the font size
ROLE_SIZE = 26

# Poppins is the site's font. SVGs shown as images can't load web fonts, so
# viewers without Poppins installed get the nearest geometric sans instead.
SANS = "Poppins,'Avenir Next',Avenir,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark": {
        "page": "#121212",
        "card": "#202022",
        "card_hi": "#2D2D2E",
        "border": "#383838",
        "grid": "#2B2B2C",
        "text": "#FAFAFA",
        "muted": "#D6D6D6",
        "dim": "#8A8A8A",
        "green": "#1DB954",
        "green2": "#279B59",
        "pill": "#1E1E1F",
        "glow": 0.30,
        "grid_op": 0.22,
    },
    "light": {
        "page": "#F4F4F5",
        "card": "#FFFFFF",
        "card_hi": "#F7F7F8",
        "border": "#E4E4E7",
        "grid": "#E4E4E7",
        "text": "#121212",
        "muted": "#3F3F46",
        "dim": "#71717A",
        "green": "#16A34A",
        "green2": "#15803D",
        "pill": "#F0FDF4",
        "glow": 0.16,
        "grid_op": 0.25,
    },
}


# What the banner says at each hour in New Jersey: (first hour, emoji, doing).
STATUSES = [
    (0, "🌙", "probably debugging"),
    (3, "😴", "asleep, hopefully"),
    (7, "☕", "morning coffee"),
    (9, "☀️", "shipping"),
    (12, "🥪", "lunch break"),
    (13, "⚡", "building RockyGPT"),
    (18, "🌆", "side projects"),
    (22, "🌙", "late-night commits"),
]

PROJECTS = [
    {
        "slug": "rockygpt",
        "name": "RockyGPT",
        "tagline": "Campus AI assistant",
        "about": "Answers Ramapo questions on dining, events, transit, and housing, and cites a source for every answer. Tuned against 2,200+ scored queries.",
        "tags": ["Next.js", "TypeScript", "PostgreSQL", "pgvector"],
        "live": True,
    },
    {
        "slug": "bubble-poppar",
        "name": "Bubble PoppAR",
        "tagline": "Runner-up · HackRamapo 2026",
        "about": "Two-player webcam game you play with hand and eye gestures, with real-time matches and server-checked scoring.",
        "tags": ["TypeScript", "MediaPipe", "Three.js", "Socket.IO"],
        "live": False,
    },
    {
        "slug": "canoga",
        "name": "Canoga Game",
        "tagline": "Dice-and-strategy board game",
        "about": "Web, command-line, and Android versions of the same game, each with a computer opponent.",
        "tags": ["JavaScript", "C++", "Java"],
        "live": True,
    },
    {
        "slug": "vc370",
        "name": "VC370",
        "tagline": "Assembler and emulator",
        "about": "Two-pass assembler and emulator for a 13-opcode simulated computer, with assemble-time and runtime error checks.",
        "tags": ["C++17", "Make"],
        "live": False,
    },
    {
        "slug": "image-splitter",
        "name": "Image Splitter",
        "tagline": "Grid maker for Instagram",
        "about": "Cuts one image into a grid of tiles for carousels, profile grids, and posters, with pinch-to-zoom on phones.",
        "tags": ["JavaScript"],
        "live": True,
    },
    {
        "slug": "photography",
        "name": "Photography",
        "tagline": "My photo gallery",
        "about": "Swipe through my photos with filters and the camera details for each shot. Installs like an app.",
        "tags": ["Next.js", "TypeScript"],
        "live": True,
    },
]


def nj_status(now: datetime) -> str:
    """The banner's status line for a moment in New Jersey, e.g. '☀️ 10 AM in NJ · shipping'."""
    emoji, doing = next((e, d) for h, e, d in reversed(STATUSES) if now.hour >= h)
    return f"{emoji} {now.strftime('%-I %p')} in NJ · {doing}"


def role_groups() -> str:
    """One <g> per role: it types in, holds, deletes, and hides until its turn comes back."""
    slot = CYCLE / len(ROLES)
    out = []
    for i, role in enumerate(ROLES):
        width = len(role) * ROLE_SIZE * CHAR_W + 4
        # Times are shares of the whole cycle: type 30%, hold 45%, delete 15% of this role's slot.
        start = i * slot / CYCLE
        typed = start + 0.30 * slot / CYCLE
        held = start + 0.75 * slot / CYCLE
        gone = start + 0.90 * slot / CYCLE
        end = (i + 1) * slot / CYCLE
        width_times = sorted({0.0, start, typed, held, gone, end, 1.0})
        width_values = [f"{width:.1f}" if typed <= t <= held else "0" for t in width_times]
        kt = ";".join(f"{t:.4f}" for t in width_times)
        out.append(f"""
    <clipPath id="clip{i}"><rect x="0" y="-40" height="60" width="0">
      <animate attributeName="width" dur="{CYCLE}s" repeatCount="indefinite"
        keyTimes="{kt}" values="{';'.join(width_values)}"/>
    </rect></clipPath>
    <g clip-path="url(#clip{i})"><text class="role" x="0" y="0">{role}</text></g>
    <rect class="cursor" x="0" y="-23" width="3" height="29" opacity="0">
      <animate attributeName="x" dur="{CYCLE}s" repeatCount="indefinite"
        keyTimes="{kt}" values="{';'.join(width_values)}"/>
      <animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" calcMode="discrete"
        keyTimes="0;{start:.4f};{end:.4f}" values="0;1;0"/>
    </rect>""")
    return "".join(out)


def hero(t: dict, status: str) -> str:
    status_w = round(len(status) * 8.2 + 34)
    # A receding floor grid on the right half, fading toward the text.
    grid_lines = []
    for k in range(1, 12):
        y = 260 + (k * k) * 1.4
        grid_lines.append(f'<line x1="560" y1="{y:.1f}" x2="1180" y2="{y:.1f}"/>')
    for k in range(-9, 10):
        x2 = 900 + k * 90
        grid_lines.append(f'<line x1="900" y1="260" x2="{x2}" y2="440"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400" role="img" aria-label="Daniel Rajakumar, software engineer">
  <title>Daniel Rajakumar</title>
  <defs>
    <linearGradient id="card" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['card_hi']}"/><stop offset="1" stop-color="{t['card']}"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['border']}"/><stop offset="0.5" stop-color="{t['border']}" stop-opacity="0.35"/>
    </linearGradient>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['green']}"/><stop offset="1" stop-color="{t['green2']}"/>
    </linearGradient>
    <radialGradient id="sun" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['green']}" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="{t['green']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="fadeL" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['card']}"/><stop offset="0.45" stop-color="{t['card']}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fadeT" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['card']}"/><stop offset="0.4" stop-color="{t['card']}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="inner"><rect x="16" y="16" width="1168" height="368" rx="20"/></clipPath>
    <style>
      .grid line {{ stroke: {t['green']}; stroke-opacity: {t['grid_op']}; stroke-width: 1; }}
      .floor {{ animation: roll 1.8s linear infinite; }}
      @keyframes roll {{ from {{ transform: translateY(0) }} to {{ transform: translateY(12px) }} }}
      .glow {{ animation: breathe 6s ease-in-out infinite; transform-origin: 900px 260px; }}
      @keyframes breathe {{ 0%,100% {{ opacity: .75; transform: scale(1) }} 50% {{ opacity: 1; transform: scale(1.06) }} }}
      .hello {{ font: 500 18px {SANS}; fill: {t['dim']}; letter-spacing: 3px; }}
      .name {{ font: 600 60px {SANS}; fill: {t['text']}; letter-spacing: .5px; }}
      .bar {{ fill: url(#bar); animation: grow 3s ease-out infinite alternate; transform-origin: 64px 0; }}
      @keyframes grow {{ from {{ transform: scaleX(.55) }} to {{ transform: scaleX(1) }} }}
      .role {{ font: 400 {ROLE_SIZE}px {MONO}; fill: {t['muted']}; }}
      .prompt {{ font: 600 {ROLE_SIZE}px {MONO}; fill: {t['green']}; }}
      .cursor {{ fill: {t['green']}; }}
      .pill {{ fill: {t['pill']}; stroke: {t['green']}; stroke-opacity: .45; }}
      .pilltext {{ font: 500 15px {SANS}; fill: {t['green']}; }}
      .status {{ fill: {t['pill']}; stroke: {t['border']}; }}
      .statustext {{ font: 500 15px {SANS}; fill: {t['muted']}; }}
      .dot {{ fill: {t['green']}; }}
      .ping {{ fill: {t['green']}; transform-origin: 86px 318px; animation: ping 1.8s ease-out infinite; }}
      @keyframes ping {{ from {{ transform: scale(1); opacity: .6 }} to {{ transform: scale(2.8); opacity: 0 }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>

  <rect x="16" y="16" width="1168" height="368" rx="20" fill="url(#card)"/>
  <g clip-path="url(#inner)">
    <circle class="glow" cx="900" cy="260" r="230" fill="url(#sun)"/>
    <g class="grid"><g class="floor">{''.join(grid_lines)}</g></g>
    <rect x="16" y="16" width="1168" height="368" fill="url(#fadeL)"/>
  </g>
  <rect x="16.5" y="16.5" width="1167" height="367" rx="20" fill="none" stroke="url(#edge)"/>

  <text class="hello" x="64" y="92">HI, I'M</text>
  <text class="name" x="62" y="160">Daniel Rajakumar</text>
  <rect class="bar" x="64" y="180" width="64" height="6" rx="3"/>

  <g transform="translate(64 246)">
    <text class="prompt" x="0" y="0">&gt;</text>
    <g transform="translate(30 0)">{role_groups()}
    </g>
  </g>

  <rect class="pill" x="64" y="298" width="296" height="40" rx="20"/>
  <circle class="ping" cx="86" cy="318" r="5"/>
  <circle class="dot" cx="86" cy="318" r="5"/>
  <text class="pilltext" x="102" y="323">Open to New Grad SWE Roles</text>

  <rect class="status" x="376" y="298" width="{status_w}" height="40" rx="20"/>
  <text class="statustext" x="394" y="323">{html.escape(status)}</text>
</svg>
"""


def card(p: dict, t: dict) -> str:
    """A project card shaped like the cards on danielrajakumar.com."""
    about = textwrap.wrap(p["about"], 52)[:3]
    about_lines = "".join(
        f'<text class="about" x="28" y="{112 + i * 21}">{html.escape(line)}</text>' for i, line in enumerate(about)
    )
    tags, x = [], 28
    for tag in p["tags"]:
        w = round(len(tag) * 7.1 + 22)
        tags.append(
            f'<rect class="tag" x="{x}" y="186" width="{w}" height="26" rx="13"/>'
            f'<text class="tagtext" x="{x + w / 2:g}" y="203.5" text-anchor="middle">{html.escape(tag)}</text>'
        )
        x += w + 8
    live = (
        '<circle class="ping" cx="378" cy="38" r="4.5"/><circle class="dot" cx="378" cy="38" r="4.5"/>'
        '<text class="livetext" x="364" y="43" text-anchor="end">Live</text>'
        if p["live"]
        else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 236" width="420" height="236" role="img" aria-label="{html.escape(p['name'])}: {html.escape(p['tagline'])}">
  <title>{html.escape(p['name'])}</title>
  <defs>
    <linearGradient id="card" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['card_hi']}"/><stop offset="1" stop-color="{t['card']}"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['border']}"/><stop offset="0.5" stop-color="{t['border']}" stop-opacity="0.35"/>
    </linearGradient>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['green']}"/><stop offset="1" stop-color="{t['green2']}"/>
    </linearGradient>
    <style>
      .name {{ font: 600 22px {SANS}; fill: {t['text']}; }}
      .tagline {{ font: 500 13px {SANS}; fill: {t['green']}; }}
      .about {{ font: 400 14px {SANS}; fill: {t['muted']}; }}
      .tag {{ fill: {t['pill']}; stroke: {t['border']}; }}
      .tagtext {{ font: 500 12px {SANS}; fill: {t['muted']}; }}
      .livetext {{ font: 500 12px {SANS}; fill: {t['green']}; }}
      .dot {{ fill: {t['green']}; }}
      .ping {{ fill: {t['green']}; transform-origin: 378px 38px; animation: ping 1.8s ease-out infinite; }}
      @keyframes ping {{ from {{ transform: scale(1); opacity: .6 }} to {{ transform: scale(2.8); opacity: 0 }} }}
      .bar {{ fill: url(#bar); animation: grow 3s ease-out infinite alternate; transform-origin: 28px 0; }}
      @keyframes grow {{ from {{ transform: scaleX(.55) }} to {{ transform: scaleX(1) }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>
  <rect x="4" y="4" width="412" height="228" rx="18" fill="url(#card)"/>
  <rect x="4.5" y="4.5" width="411" height="227" rx="18" fill="none" stroke="url(#edge)"/>
  <text class="name" x="28" y="46">{html.escape(p['name'])}</text>
  {live}
  <text class="tagline" x="28" y="70">{html.escape(p['tagline'])}</text>
  <rect class="bar" x="28" y="82" width="36" height="4" rx="2"/>
  {about_lines}
  {''.join(tags)}
</svg>
"""


def main() -> None:
    root = Path(__file__).resolve().parent.parent / "assets"
    root.mkdir(exist_ok=True)
    status = nj_status(datetime.now(ZoneInfo("America/New_York")))
    for name, theme in THEMES.items():
        (root / f"hero-{name}.svg").write_text(hero(theme, status))
        for p in PROJECTS:
            (root / f"card-{p['slug']}-{name}.svg").write_text(card(p, theme))


if __name__ == "__main__":
    main()
