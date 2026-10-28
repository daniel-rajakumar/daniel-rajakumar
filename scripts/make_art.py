"""Generate the animated SVGs used in the profile README.

Run from the repo root: python3 scripts/make_art.py
Writes assets/hero-{dark,light}.svg.
"""

from pathlib import Path

ROLES = [
    "Software Engineer",
    "Building RockyGPT",
    "Retrieval systems + evals",
    "Next.js · TypeScript · Python",
]
CYCLE = 16  # seconds for one pass through every role
CHAR_W = 0.6  # monospace character width, as a share of the font size
ROLE_SIZE = 28

THEMES = {
    "dark": {
        "bg": "#070B16",
        "bg2": "#0D1430",
        "grid": "#2A3B8F",
        "text": "#E6ECFF",
        "muted": "#8EA0D6",
        "a": "#22D3EE",
        "b": "#A855F7",
        "c": "#F472B6",
        "ok": "#34D399",
        "pill": "#0F1A3A",
        "name_filter": ' filter="url(#glow)"',
    },
    "light": {
        "bg": "#F5F7FF",
        "bg2": "#E6ECFF",
        "grid": "#B7C3F2",
        "text": "#0B1020",
        "muted": "#4B5A8C",
        "a": "#0891B2",
        "b": "#7C3AED",
        "c": "#DB2777",
        "ok": "#059669",
        "pill": "#FFFFFF",
        "name_filter": "",
    },
}


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
        width_values = []
        for t in width_times:
            width_values.append(f"{width:.1f}" if typed <= t <= held else "0")
        cursor_x = [f"{(v and float(v)) + 0:.1f}" for v in width_values]
        kt = ";".join(f"{t:.4f}" for t in width_times)
        out.append(f"""
    <clipPath id="clip{i}"><rect x="0" y="-40" height="60" width="0">
      <animate attributeName="width" dur="{CYCLE}s" repeatCount="indefinite"
        keyTimes="{kt}" values="{';'.join(width_values)}"/>
    </rect></clipPath>
    <g clip-path="url(#clip{i})"><text class="role" x="0" y="0">{role}</text></g>
    <rect class="cursor" x="0" y="-26" width="3" height="32" opacity="0">
      <animate attributeName="x" dur="{CYCLE}s" repeatCount="indefinite"
        keyTimes="{kt}" values="{';'.join(cursor_x)}"/>
      <animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" calcMode="discrete"
        keyTimes="0;{start:.4f};{end:.4f}" values="0;1;0"/>
    </rect>""")
    return "".join(out)


def hero(t: dict) -> str:
    grid_lines = []
    # Receding floor grid: horizontal lines bunch up toward the horizon.
    for k in range(1, 13):
        y = 300 + (k * k) * 1.6
        grid_lines.append(f'<line x1="0" y1="{y:.1f}" x2="1200" y2="{y:.1f}"/>')
    for k in range(-14, 15):
        x2 = 600 + k * 130
        grid_lines.append(f'<line x1="600" y1="300" x2="{x2}" y2="560"/>')
    stars = []
    for k in range(16):
        x = (k * 317) % 1200
        y = (k * 89) % 230 + 10
        r = 0.8 + (k % 3) * 0.5
        d = 2 + (k % 5)
        stars.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" class="star" style="animation-duration:{d}s;animation-delay:-{k % 7}s"/>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400" role="img" aria-label="Daniel Rajakumar, software engineer">
  <title>Daniel Rajakumar</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['bg']}"/><stop offset="1" stop-color="{t['bg2']}"/>
    </linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['a']}"><animate attributeName="stop-color" dur="6s" repeatCount="indefinite" values="{t['a']};{t['b']};{t['c']};{t['a']}"/></stop>
      <stop offset="0.5" stop-color="{t['b']}"><animate attributeName="stop-color" dur="6s" repeatCount="indefinite" values="{t['b']};{t['c']};{t['a']};{t['b']}"/></stop>
      <stop offset="1" stop-color="{t['c']}"><animate attributeName="stop-color" dur="6s" repeatCount="indefinite" values="{t['c']};{t['a']};{t['b']};{t['c']}"/></stop>
    </linearGradient>
    <radialGradient id="sun" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['b']}" stop-opacity="0.55"/><stop offset="1" stop-color="{t['b']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['bg2']}" stop-opacity="1"/><stop offset="0.35" stop-color="{t['bg2']}" stop-opacity="0"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-50%" width="140%" height="200%">
      <feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="card"><rect width="1200" height="400" rx="24"/></clipPath>
    <style>
      .star {{ fill: {t['text']}; animation: twinkle ease-in-out infinite; }}
      @keyframes twinkle {{ 0%,100% {{ opacity: .15 }} 50% {{ opacity: .9 }} }}
      .grid line {{ stroke: {t['grid']}; stroke-width: 1; }}
      .floor {{ animation: roll 1.6s linear infinite; }}
      @keyframes roll {{ from {{ transform: translateY(0) }} to {{ transform: translateY(14px) }} }}
      .name {{ font: 800 68px 'SF Pro Display','Segoe UI',Inter,Helvetica,Arial,sans-serif; letter-spacing: 6px; fill: url(#name); }}
      .hello {{ font: 600 22px 'SF Mono',Menlo,Consolas,monospace; fill: {t['muted']}; letter-spacing: 4px; }}
      .role {{ font: 500 {ROLE_SIZE}px 'SF Mono',Menlo,Consolas,'Liberation Mono',monospace; fill: {t['text']}; }}
      .prompt {{ font: 500 {ROLE_SIZE}px 'SF Mono',Menlo,Consolas,monospace; fill: {t['a']}; }}
      .cursor {{ fill: {t['a']}; }}
      .pill {{ fill: {t['pill']}; stroke: {t['grid']}; }}
      .pilltext {{ font: 600 16px 'SF Pro Text','Segoe UI',Helvetica,Arial,sans-serif; fill: {t['text']}; }}
      .dot {{ fill: {t['ok']}; }}
      .ping {{ fill: {t['ok']}; transform-origin: 46px 330px; animation: ping 1.8s ease-out infinite; }}
      @keyframes ping {{ from {{ transform: scale(1); opacity: .7 }} to {{ transform: scale(3); opacity: 0 }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>
  <g clip-path="url(#card)">
    <rect width="1200" height="400" fill="url(#bg)"/>
    {''.join(stars)}
    <circle cx="600" cy="300" r="260" fill="url(#sun)"/>
    <g class="grid"><g class="floor">{''.join(grid_lines)}</g></g>
    <rect y="290" width="1200" height="110" fill="url(#fade)"/>

    <text class="hello" x="60" y="92">HI, I'M</text>
    <text class="name" x="56" y="170"{t['name_filter']}>DANIEL RAJAKUMAR</text>

    <g transform="translate(60 248)">
      <text class="prompt" x="0" y="0">&gt;</text>
      <g transform="translate(34 0)">{role_groups()}
      </g>
    </g>

    <rect class="pill" x="28" y="312" width="350" height="36" rx="18"/>
    <circle class="ping" cx="46" cy="330" r="6"/>
    <circle class="dot" cx="46" cy="330" r="6"/>
    <text class="pilltext" x="62" y="336">Online · New Jersey · Ramapo CS '26</text>
  </g>
</svg>
"""


def main() -> None:
    root = Path(__file__).resolve().parent.parent / "assets"
    root.mkdir(exist_ok=True)
    for name, theme in THEMES.items():
        (root / f"hero-{name}.svg").write_text(hero(theme))


if __name__ == "__main__":
    main()
