"""Draws the difference between a leaderboard display and a map display.

The free-seat numbers are a real moment taken from the simulation after the
train has reached its steady load. The arrows show where the passengers
waiting at the two platform entrances would walk under each design, given a
three-carriage walking limit.
"""

import json
from playwright.sync_api import sync_playwright

INK, MUTE, EDGE, GRID = "#0F172A", "#64748B", "#94A3B8", "#E2E8F0"
GREEN, AMBER, RED = "#16A34A", "#D97706", "#DC2626"

FREE = [21, 0, 0, 2, 35, 42, 10, 21, 33, 63, 94, 100]
ENTRANCES = [3, 8]            # carriage numbers people gather at (1-based)
REACH = 3                     # carriages a passenger will walk

W, PANEL_H = 1900, 620
BOX_W, GAP, X0 = 137, 12, 60


def x_of(i):                  # left edge of carriage i (0-based)
    return X0 + i * (BOX_W + GAP)


def cx_of(i):
    return x_of(i) + BOX_W / 2


def colour(free):
    return RED if free == 0 else AMBER if free < 10 else GREEN


def carriage_row(y, label_free=True):
    """The train itself, drawn the same way in both panels."""
    out = [f"<text x='{X0}' y='{y - 14}' font-size='24' font-weight='600' "
           f"fill='{MUTE}'>The train</text>"]
    for i, free in enumerate(FREE):
        c = colour(free)
        out.append(
            f"<rect x='{x_of(i)}' y='{y}' width='{BOX_W}' height='74' rx='10' "
            f"fill='{c}' fill-opacity='0.10' stroke='{c}' stroke-width='2.5'/>"
            f"<text x='{cx_of(i)}' y='{y + 32}' text-anchor='middle' font-size='26' "
            f"font-weight='700' fill='{INK}'>{i + 1}</text>")
        if label_free:
            out.append(
                f"<text x='{cx_of(i)}' y='{y + 58}' text-anchor='middle' "
                f"font-size='22' fill='{MUTE}'>{free} free</text>")
    return "".join(out)


def crowd(x, y, n, note):
    """A clump of waiting passengers."""
    dots = "".join(
        f"<circle cx='{x - 34 + (k % 5) * 17}' cy='{y + (k // 5) * 18}' r='7' "
        f"fill='{MUTE}'/>" for k in range(n))
    return (dots + f"<text x='{x}' y='{y + 92}' text-anchor='middle' font-size='22' "
                   f"fill='{MUTE}'>{note}</text>")


def arrow(x1, y1, x2, y2, c, w=3):
    mid = (y1 + y2) / 2
    return (f"<path d='M{x1} {y1} C {x1} {mid}, {x2} {mid}, {x2} {y2}' fill='none' "
            f"stroke='{c}' stroke-width='{w}' stroke-opacity='0.75' "
            f"marker-end='url(#ar-{c[1:]})'/>")


def panel_leaderboard(oy):
    ranked = sorted(range(12), key=lambda i: -FREE[i])[:3]
    names = ", ".join(f"Car {i + 1}" for i in ranked)
    s = [f"<text x='{X0}' y='{oy + 40}' font-size='34' font-weight='700' fill='{INK}'>"
         f"A leaderboard: the display names the best carriages</text>"]
    # the sign
    s.append(f"<rect x='{X0 + 430}' y='{oy + 66}' width='920' height='92' rx='14' "
             f"fill='{INK}'/>"
             f"<text x='{X0 + 890}' y='{oy + 102}' text-anchor='middle' font-size='22' "
             f"fill='#94A3B8' letter-spacing='3'>MOST FREE SEATS</text>"
             f"<text x='{X0 + 890}' y='{oy + 138}' text-anchor='middle' font-size='30' "
             f"font-weight='700' fill='white'>{names}</text>")
    s.append(carriage_row(oy + 300, label_free=False))
    # everyone within reach walks to the single best carriage they can reach
    targets = {}
    for e in ENTRANCES:
        reach = [i for i in range(12) if abs(i - (e - 1)) <= REACH]
        best = max(reach, key=lambda i: FREE[i])
        targets[e] = best
        s.append(crowd(cx_of(e - 1), oy + 430, 20, f"waiting at car {e}"))
        s.append(arrow(cx_of(e - 1), oy + 420, cx_of(best), oy + 382, RED))
    busy = max(targets.values(), key=lambda i: list(targets.values()).count(i))
    s.append(f"<text x='{X0}' y='{oy + 560}' font-size='26' fill='{RED}' "
             f"font-weight='700'>Everyone within walking range gets the same answer, "
             f"so each crowd moves as one block.</text>")
    s.append(f"<text x='{X0}' y='{oy + 592}' font-size='24' fill='{MUTE}'>"
             f"Busiest door, averaged over 500 stops: 76 passengers.</text>")
    return "".join(s)


def panel_map(oy):
    s = [f"<text x='{X0}' y='{oy + 40}' font-size='34' font-weight='700' fill='{INK}'>"
         f"A map: every carriage shows its own state, in its own position</text>"]
    # the sign: one tile per carriage, aligned above the carriage it describes
    for i, free in enumerate(FREE):
        c = colour(free)
        s.append(
            f"<rect x='{x_of(i)}' y='{oy + 66}' width='{BOX_W}' height='92' rx='12' "
            f"fill='{c}' stroke='{c}' stroke-width='2.5'/>"
            f"<text x='{cx_of(i)}' y='{oy + 104}' text-anchor='middle' font-size='34' "
            f"font-weight='700' fill='white'>{free}</text>"
            f"<text x='{cx_of(i)}' y='{oy + 134}' text-anchor='middle' font-size='20' "
            f"fill='white' fill-opacity='0.9'>free</text>")
        s.append(f"<line x1='{cx_of(i)}' y1='{oy + 158}' x2='{cx_of(i)}' y2='{oy + 300}' "
                 f"stroke='{GRID}' stroke-width='1.5' stroke-dasharray='5 6'/>")
    s.append(carriage_row(oy + 300, label_free=False))
    for e in ENTRANCES:
        reach = [i for i in range(12) if abs(i - (e - 1)) <= REACH and FREE[i] > 0]
        s.append(crowd(cx_of(e - 1), oy + 430, 20, f"waiting at car {e}"))
        total = sum(FREE[i] for i in reach)
        for i in reach:
            w = 1.5 + 6 * FREE[i] / total
            s.append(arrow(cx_of(e - 1), oy + 420, cx_of(i), oy + 382, GREEN, round(w, 1)))
    s.append(f"<text x='{X0}' y='{oy + 560}' font-size='26' fill='{GREEN}' "
             f"font-weight='700'>Each passenger answers a local question, so one crowd "
             f"splits across the carriages near it.</text>")
    s.append(f"<text x='{X0}' y='{oy + 592}' font-size='24' fill='{MUTE}'>"
             f"Busiest door, averaged over 500 stops: 33 passengers. "
             f"With no display at all it is 39.</text>")
    return "".join(s)


def build():
    defs = "<defs>" + "".join(
        f"<marker id='ar-{c[1:]}' viewBox='0 0 10 10' refX='9' refY='5' "
        f"markerWidth='6' markerHeight='6' orient='auto-start-reverse'>"
        f"<path d='M0 0L10 5L0 10z' fill='{c}'/></marker>" for c in (RED, GREEN)) + "</defs>"
    body = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {2 * PANEL_H + 40}' "
            f"font-family='Arial, Helvetica, sans-serif'>"
            f"<rect width='{W}' height='{2 * PANEL_H + 40}' fill='white'/>{defs}"
            + panel_leaderboard(10)
            + f"<line x1='{X0}' y1='{PANEL_H + 20}' x2='{W - X0}' y2='{PANEL_H + 20}' "
              f"stroke='{GRID}' stroke-width='2'/>"
            + panel_map(PANEL_H + 40) + "</svg>")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": 2 * PANEL_H + 40},
                        device_scale_factor=2)
        pg.set_content(f"<body style='margin:0'>{body}</body>")
        pg.wait_for_timeout(400)
        pg.screenshot(path="results/display_designs.png")
        b.close()
    print("results/display_designs.png")


if __name__ == "__main__":
    build()
