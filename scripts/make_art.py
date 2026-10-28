"""Generate the animated SVGs used in the profile README.

The look follows danielrajakumar.com: charcoal cards, one green accent,
Poppins type, and the short green bar under headings.

Run from the repo root: python3 scripts/make_art.py
Writes, for each theme: assets/hero-*.svg (with the current New Jersey time
in its status pill), card-<project>-*.svg, link-<name>-*.svg, about-*.svg,
tools-*.svg, and outside-*.svg. Every piece is the same glass panel, so the
whole README reads as one design.
"""

import base64
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
        # Glass: a frosted fill, a bright top edge, a soft shadow, and a passing sheen.
        "glass_top": 0.10,
        "glass_bot": 0.025,
        "edge": "#FFFFFF",
        "edge_hi": 0.45,
        "edge_lo": 0.07,
        "shadow_op": 0.45,
        "sheen": 0.07,
        "spec": 0.55,
        "ink": "#FFFFFF",
        "wash": 0.035,
        "line": 0.12,
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
        "glass_top": 0.85,
        "glass_bot": 0.55,
        "edge": "#000000",
        "edge_hi": 0.10,
        "edge_lo": 0.04,
        "shadow_op": 0.12,
        "sheen": 0.5,
        "spec": 0.9,
        "ink": "#000000",
        "wash": 0.02,
        "line": 0.10,
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
        "about": "Answers Ramapo questions on dining, events, transit, and housing, citing a source for every answer. Tuned on 2,200+ scored queries.",
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
        "slug": "vc370",
        "name": "VC370",
        "tagline": "Assembler and emulator",
        "about": "Two-pass assembler and emulator for a 13-opcode simulated computer, with assemble-time and runtime error checks.",
        "tags": ["C++17", "Make"],
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


def glass(t: dict, x: float, y: float, w: float, h: float, rx: float, delay: float = 0) -> tuple[str, str, str, str]:
    """An Apple-style glass panel, as (defs, styles, layers under the content, layers over it).

    The shadow is masked out under the panel so the glass stays clear, and a
    soft band of light sweeps across it every few seconds.
    """
    defs = f"""
    <linearGradient id="glassFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="{t['glass_top']}"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="{t['glass_bot']}"/>
    </linearGradient>
    <linearGradient id="glassEdge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['edge']}" stop-opacity="{t['edge_hi']}"/>
      <stop offset="0.45" stop-color="{t['edge']}" stop-opacity="{t['edge_lo']}"/>
      <stop offset="1" stop-color="{t['edge']}" stop-opacity="{t['edge_hi'] * 0.5:g}"/>
    </linearGradient>
    <linearGradient id="glassSpec" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="0.3" stop-color="#FFFFFF" stop-opacity="{t['spec']}"/>
      <stop offset="0.7" stop-color="#FFFFFF" stop-opacity="{t['spec']}"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="glassSheen" x1="0" y1="0" x2="1" y2="0.35">
      <stop offset="0.35" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="{t['sheen']}"/>
      <stop offset="0.65" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <filter id="glassShadow" x="-10%" y="-10%" width="120%" height="140%">
      <feGaussianBlur stdDeviation="10"/>
    </filter>
    <mask id="glassOutside">
      <rect x="-5000" y="-5000" width="10000" height="10000" fill="#FFF"/>
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="#000"/>
    </mask>
    <clipPath id="glassClip"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath>"""
    style = f"""
      .sheen {{ animation: sheen 9s ease-in-out infinite; animation-delay: {delay:g}s; }}
      @keyframes sheen {{ 0%, 55% {{ transform: translateX(-{w:g}px) }} 100% {{ transform: translateX({w:g}px) }} }}"""
    under = f"""
  <rect x="{x}" y="{y + 6}" width="{w}" height="{h}" rx="{rx}" fill="#000" fill-opacity="{t['shadow_op']}" filter="url(#glassShadow)" mask="url(#glassOutside)"/>
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#glassFill)"/>
  <g clip-path="url(#glassClip)"><rect class="sheen" x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#glassSheen)"/></g>"""
    over = f"""
  <rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="url(#glassEdge)"/>
  <rect x="{x + rx}" y="{y + 0.5}" width="{w - 2 * rx}" height="1" fill="url(#glassSpec)"/>"""
    return defs, style, under, over


def hero(t: dict, status: str) -> str:
    status_w = round(len(status) * 8.2 + 34)
    g_defs, g_style, g_under, g_over = glass(t, 16, 10, 1168, 372, 24)
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
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['green']}"/><stop offset="1" stop-color="{t['green2']}"/>
    </linearGradient>
    <radialGradient id="sun" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['green']}" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="{t['green']}" stop-opacity="0"/>
    </radialGradient>
    <!-- Fades the grid out toward the text without painting a background color. -->
    <linearGradient id="fadeL" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000"/><stop offset="0.45" stop-color="#FFF"/>
    </linearGradient>
    <mask id="fade"><rect x="16" y="10" width="1168" height="372" fill="url(#fadeL)"/></mask>
    <clipPath id="inner"><rect x="16" y="10" width="1168" height="372" rx="24"/></clipPath>
    <filter id="blob" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>{g_defs}
    <style>
      .grid line {{ stroke: {t['green']}; stroke-opacity: {t['grid_op']}; stroke-width: 1; }}
      .floor {{ animation: roll 1.8s linear infinite; }}
      @keyframes roll {{ from {{ transform: translateY(0) }} to {{ transform: translateY(12px) }} }}
      .glow {{ animation: breathe 6s ease-in-out infinite; transform-origin: 900px 260px; }}
      @keyframes breathe {{ 0%,100% {{ opacity: .75; transform: scale(1) }} 50% {{ opacity: 1; transform: scale(1.06) }} }}
      .drift {{ animation: drift 14s ease-in-out infinite alternate; }}
      @keyframes drift {{ from {{ transform: translate(0, 0) }} to {{ transform: translate(140px, -40px) }} }}{g_style}
      .hello {{ font: 500 18px {SANS}; fill: {t['dim']}; letter-spacing: 3px; }}
      .name {{ font: 600 60px {SANS}; fill: {t['text']}; letter-spacing: .5px; }}
      .bar {{ fill: url(#bar); animation: grow 3s ease-out infinite alternate; transform-origin: 64px 0; }}
      @keyframes grow {{ from {{ transform: scaleX(.55) }} to {{ transform: scaleX(1) }} }}
      .role {{ font: 400 {ROLE_SIZE}px {MONO}; fill: {t['muted']}; }}
      .prompt {{ font: 600 {ROLE_SIZE}px {MONO}; fill: {t['green']}; }}
      .cursor {{ fill: {t['green']}; }}
      .pill {{ fill: {t['green']}; fill-opacity: .08; stroke: {t['green']}; stroke-opacity: .45; }}
      .pilltext {{ font: 500 15px {SANS}; fill: {t['green']}; }}
      .status {{ fill: {t['ink']}; fill-opacity: {t['wash'] * 1.6:g}; stroke: {t['ink']}; stroke-opacity: {t['line']}; }}
      .statustext {{ font: 500 15px {SANS}; fill: {t['muted']}; }}
      .dot {{ fill: {t['green']}; }}
      .ping {{ fill: {t['green']}; transform-origin: 86px 318px; animation: ping 1.8s ease-out infinite; }}
      @keyframes ping {{ from {{ transform: scale(1); opacity: .6 }} to {{ transform: scale(2.8); opacity: 0 }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>

{g_under}
  <g clip-path="url(#inner)">
    <circle class="drift" cx="240" cy="330" r="130" fill="{t['green']}" fill-opacity="{t['glow'] * 0.4:g}" filter="url(#blob)"/>
  </g>
  <g clip-path="url(#inner)" mask="url(#fade)">
    <circle class="glow" cx="900" cy="260" r="230" fill="url(#sun)"/>
    <g class="grid"><g class="floor">{''.join(grid_lines)}</g></g>
  </g>

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
{g_over}
</svg>
"""


def card(p: dict, t: dict) -> str:
    """A project card shaped like the cards on danielrajakumar.com.

    The card is a pane of glass, so it sits on GitHub's dark, dimmed, or
    light page without looking like a separate block.
    """
    g_defs, g_style, g_under, g_over = glass(t, 12, 8, 396, 212, 20, delay=PROJECTS.index(p) * 1.5)
    about = textwrap.wrap(p["about"], 50)
    assert len(about) <= 3, f"{p['name']}: the description needs more than 3 lines"
    about_lines = "".join(
        f'<text class="about" x="34" y="{112 + i * 21}">{html.escape(line)}</text>' for i, line in enumerate(about)
    )
    tags, x = [], 34
    for tag in p["tags"]:
        w = round(len(tag) * 6.7 + 20)
        tags.append(
            f'<rect class="tag" x="{x}" y="178" width="{w}" height="26" rx="13"/>'
            f'<text class="tagtext" x="{x + w / 2:g}" y="195.5" text-anchor="middle">{html.escape(tag)}</text>'
        )
        x += w + 6
    live = (
        '<circle class="ping" cx="382" cy="38" r="4.5"/><circle class="dot" cx="382" cy="38" r="4.5"/>'
        '<text class="livetext" x="368" y="43" text-anchor="end">Live</text>'
        if p["live"]
        else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 236" width="420" height="236" role="img" aria-label="{html.escape(p['name'])}: {html.escape(p['tagline'])}">
  <title>{html.escape(p['name'])}</title>
  <defs>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['green']}"/><stop offset="1" stop-color="{t['green2']}"/>
    </linearGradient>{g_defs}
    <style>{g_style}
      .name {{ font: 600 22px {SANS}; fill: {t['text']}; }}
      .tagline {{ font: 500 13px {SANS}; fill: {t['green']}; }}
      .about {{ font: 400 14px {SANS}; fill: {t['muted']}; }}
      .tag {{ fill: {t['ink']}; fill-opacity: {t['wash'] * 1.6:g}; stroke: {t['ink']}; stroke-opacity: {t['line']}; }}
      .tagtext {{ font: 500 12px {SANS}; fill: {t['muted']}; }}
      .livetext {{ font: 500 12px {SANS}; fill: {t['green']}; }}
      .dot {{ fill: {t['green']}; }}
      .ping {{ fill: {t['green']}; transform-origin: 382px 38px; animation: ping 1.8s ease-out infinite; }}
      @keyframes ping {{ from {{ transform: scale(1); opacity: .6 }} to {{ transform: scale(2.8); opacity: 0 }} }}
      .bar {{ fill: url(#bar); animation: grow 3s ease-out infinite alternate; transform-origin: 34px 0; }}
      @keyframes grow {{ from {{ transform: scaleX(.55) }} to {{ transform: scaleX(1) }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>
{g_under}
  <text class="name" x="34" y="46">{html.escape(p['name'])}</text>
  {live}
  <text class="tagline" x="34" y="70">{html.escape(p['tagline'])}</text>
  <rect class="bar" x="34" y="82" width="36" height="4" rx="2"/>
  {about_lines}
  {''.join(tags)}
{g_over}
</svg>
"""


LINKS = [
    {"slug": "website", "label": "danielrajakumar.com", "icon": "globe"},
    {"slug": "rockygpt", "label": "RockyGPT", "icon": "live"},
    {"slug": "linkedin", "label": "LinkedIn", "icon": "in"},
    {"slug": "email", "label": "Email", "icon": "mail"},
]

ABOUT = {
    "intro": "I build full-stack web apps in TypeScript and Next.js, lately with a focus on retrieval systems and the tests that keep them honest.",
    "points": [
        ("🎓", "B.S. in Computer Science, Ramapo College of New Jersey (2026)"),
        ("💼", "Software engineering intern at dsm-firmenich, where I built and launched an internal assessment platform as the sole developer"),
        ("🤖", "Building RockyGPT, a campus assistant for Ramapo that answers with linked sources"),
    ],
}

OUTSIDE = [
    ("🚀", "Led Ramapo's Google Developer Student Club and organized the college's first DevFest"),
    ("🧑‍💻", "Founded Ramapo's Computer Science Club"),
]

# Wide panels share the banner's 1200-unit width, so their text is sized to match the cards on screen.
WIDE = 1200
WIDE_TEXT = 21
WIDE_WRAP = 100


def icon(kind: str, t: dict, cx: float, cy: float) -> str:
    g = t["green"]
    if kind == "globe":
        return (f'<circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="{g}" stroke-width="2"/>'
                f'<ellipse cx="{cx}" cy="{cy}" rx="4" ry="9" fill="none" stroke="{g}" stroke-width="1.6"/>'
                f'<line x1="{cx - 9}" y1="{cy}" x2="{cx + 9}" y2="{cy}" stroke="{g}" stroke-width="1.6"/>')
    if kind == "live":
        return (f'<circle class="ping" cx="{cx}" cy="{cy}" r="6" style="transform-origin:{cx}px {cy}px"/>'
                f'<circle class="dot" cx="{cx}" cy="{cy}" r="6"/>')
    if kind == "in":
        return (f'<rect x="{cx - 10}" y="{cy - 10}" width="20" height="20" rx="5" fill="{g}"/>'
                f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" style="font: 700 13px {SANS}; fill: {t["text"] if t["ink"] == "#000000" else "#121212"}">in</text>')
    return (f'<rect x="{cx - 10}" y="{cy - 7}" width="20" height="14" rx="3" fill="none" stroke="{g}" stroke-width="2"/>'
            f'<path d="M{cx - 9} {cy - 6} L{cx} {cy + 1} L{cx + 9} {cy - 6}" fill="none" stroke="{g}" stroke-width="2"/>')


def link_pill(link: dict, t: dict, index: int) -> str:
    """One glass link button for the row under the banner."""
    w, h = 300, 92
    g_defs, g_style, g_under, g_over = glass(t, 10, 8, w - 20, h - 26, 33, delay=index * 0.8)
    label = html.escape(link["label"])
    text_w = len(link["label"]) * 11.5
    start = (w - (text_w + 32)) / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">
  <title>{label}</title>
  <defs>{g_defs}
    <style>{g_style}
      .label {{ font: 600 21px {SANS}; fill: {t['text']}; }}
      .dot {{ fill: {t['green']}; }}
      .ping {{ fill: {t['green']}; animation: ping 1.8s ease-out infinite; }}
      @keyframes ping {{ from {{ transform: scale(1); opacity: .6 }} to {{ transform: scale(2.6); opacity: 0 }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>{g_under}
  {icon(link['icon'], t, start + 10, 41)}
  <text class="label" x="{start + 32:g}" y="48">{label}</text>{g_over}
</svg>
"""


def text_panel(t: dict, title: str, intro: str | None, points: list[tuple[str, str]], delay: float) -> str:
    """A wide glass panel of text: an optional intro line, then emoji-led points."""
    # Each block is the intro or one point; lines in a block sit closer than blocks do.
    blocks = []
    if intro:
        blocks.append(("intro", "", textwrap.wrap(intro, WIDE_WRAP)))
    for emoji, text in points:
        blocks.append(("point", emoji, textwrap.wrap(text, WIDE_WRAP - 6)))
    y, rows = 62, []
    for kind, emoji, wrapped in blocks:
        if emoji:
            rows.append(f'<text class="emoji" x="54" y="{y}">{emoji}</text>')
        x = 54 if kind == "intro" else 92
        for line in wrapped:
            rows.append(f'<text class="{kind}" x="{x}" y="{y}">{html.escape(line)}</text>')
            y += 30
        y += 14 if kind == "intro" else 8
    h = y + 14
    g_defs, g_style, g_under, g_over = glass(t, 16, 8, WIDE - 32, h - 24, 24, delay=delay)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDE} {h}" width="{WIDE}" height="{h}" role="img" aria-label="{html.escape(title)}">
  <title>{html.escape(title)}</title>
  <defs>{g_defs}
    <style>{g_style}
      .intro {{ font: 500 {WIDE_TEXT + 1}px {SANS}; fill: {t['text']}; }}
      .point {{ font: 400 {WIDE_TEXT}px {SANS}; fill: {t['muted']}; }}
      .emoji {{ font: 400 {WIDE_TEXT}px 'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji',sans-serif; }}
    </style>
  </defs>{g_under}
  {''.join(rows)}{g_over}
</svg>
"""


def tools_panel(t: dict) -> str:
    """The skill icons (scripts/skillicons.svg, from skillicons.dev) on a wide glass panel."""
    icons = (Path(__file__).resolve().parent / "skillicons.svg").read_bytes()
    data = base64.b64encode(icons).decode()
    h, icon_w = 120, 860
    icon_h = icon_w * 256 / 3556
    g_defs, g_style, g_under, g_over = glass(t, 16, 8, WIDE - 32, h - 24, 24, delay=2)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDE} {h}" width="{WIDE}" height="{h}" role="img" aria-label="TypeScript, JavaScript, Python, C++, Java, Next.js, React, FastAPI, PostgreSQL, Redis, Docker, AWS">
  <title>Tools I use</title>
  <defs>{g_defs}
    <style>{g_style}</style>
  </defs>{g_under}
  <image x="{(WIDE - icon_w) / 2:g}" y="{8 + (h - 24 - icon_h) / 2:g}" width="{icon_w}" height="{icon_h:g}" href="data:image/svg+xml;base64,{data}"/>{g_over}
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
        for i, link in enumerate(LINKS):
            (root / f"link-{link['slug']}-{name}.svg").write_text(link_pill(link, theme, i))
        (root / f"about-{name}.svg").write_text(text_panel(theme, "About me", ABOUT["intro"], ABOUT["points"], 1))
        (root / f"tools-{name}.svg").write_text(tools_panel(theme))
        (root / f"outside-{name}.svg").write_text(text_panel(theme, "Outside of code", None, OUTSIDE, 3))


if __name__ == "__main__":
    main()
