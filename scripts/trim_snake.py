"""Remove the score bar that Platane/snk draws under the snake.

The bar is the set of `.u` rects below the contribution grid. This hides them
and crops the empty space they leave, keeping room for the snake to pass under
the last row.

Usage: python3 scripts/trim_snake.py generated/snake-dark.svg generated/snake-light.svg
"""

import re
import sys

BAR_TOP = 130  # the grid ends at y=110 and the snake can dip one cell below it


def trim(svg: str) -> str:
    match = re.search(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"', svg)
    if not match:
        raise ValueError("no viewBox found")
    x, y, w, h = (float(v) for v in match.groups())
    new_h = BAR_TOP - y
    if new_h >= h:
        return svg  # nothing below the grid to crop
    svg = svg.replace(match.group(0), f'viewBox="{x:g} {y:g} {w:g} {new_h:g}"', 1)
    svg = re.sub(r'(<svg[^>]*?) height="[\d.]+"', rf'\1 height="{new_h:g}"', svg, count=1)
    return svg.replace("<style>", "<style>.u{display:none}", 1)


def main() -> None:
    for path in sys.argv[1:]:
        with open(path) as f:
            svg = f.read()
        with open(path, "w") as f:
            f.write(trim(svg))


if __name__ == "__main__":
    main()
