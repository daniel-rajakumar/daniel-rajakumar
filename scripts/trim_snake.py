"""Tidy the snake that Platane/snk draws and set it in a glass panel.

Removes the score bar (the `.u` rects below the contribution grid), crops the
space it used, and wraps the graph in the same glass panel as the rest of the
profile. The theme comes from the file name (snake-dark.svg / snake-light.svg).

Usage: python3 scripts/trim_snake.py generated/snake-dark.svg generated/snake-light.svg
"""

import re
import sys

from make_art import THEMES, glass

BAR_TOP = 130  # the grid ends at y=110 and the snake can dip one cell below it
PAD_X, PAD_TOP, PAD_BOTTOM = 30, 24, 40  # room around the graph, plus the panel's shadow


def trim(svg: str, theme: dict) -> str:
    match = re.search(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"', svg)
    if not match:
        raise ValueError("no viewBox found")
    x, y, w, h = (float(v) for v in match.groups())
    h = min(h, BAR_TOP - y)

    # Grow the canvas around the graph and put a glass panel behind it.
    nx, ny, nw, nh = x - PAD_X, y - PAD_TOP, w + 2 * PAD_X, h + PAD_TOP + PAD_BOTTOM
    g_defs, g_style, g_under, g_over = glass(theme, nx + 10, ny + 8, nw - 20, nh - 8 - 22, 24, delay=4)
    svg = svg.replace(match.group(0), f'viewBox="{nx:g} {ny:g} {nw:g} {nh:g}"', 1)
    svg = re.sub(r'(<svg[^>]*?) width="[\d.]+"', rf'\1 width="{nw:g}"', svg, count=1)
    svg = re.sub(r'(<svg[^>]*?) height="[\d.]+"', rf'\1 height="{nh:g}"', svg, count=1)
    svg = svg.replace("<style>", "<style>.u{display:none}", 1)
    opening = re.search(r"<svg[^>]*>", svg).group(0)
    svg = svg.replace(opening, f"{opening}<defs>{g_defs}<style>{g_style}</style></defs>{g_under}", 1)
    return svg.replace("</svg>", f"{g_over}</svg>", 1)


def main() -> None:
    for path in sys.argv[1:]:
        theme = THEMES["light" if "light" in path else "dark"]
        with open(path) as f:
            svg = f.read()
        with open(path, "w") as f:
            f.write(trim(svg, theme))


if __name__ == "__main__":
    main()
