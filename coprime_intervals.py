#!/usr/bin/env python3
"""Coprime pairs, the rays they leave, and the musical intervals they make.

    python3 coprime_intervals.py            # writes images/ and prints the ranking table

Two pictures of one fact. A pair (x, y) is coprime when gcd(x, y) = 1; written
as a fraction x/y in lowest terms it is a ratio, and between 1 and 2 those
ratios are the intervals inside one octave.

  images/grid-3840x2160.png   one pixel per pair, (1,1) top-left, coprime white
  images/grid-100.png         100 x 100 pairs in 20px blocks, rays drawn solid
  images/number-line.png      every coprime p/q in [1, 2], height 1/(p^2 + q^2),
                              the musical intervals named

Images are saved through Pillow with no metadata at all (no pHYs, no text).
"""
import colorsys
import io
import math
from math import gcd
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullLocator
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "images"

# Rays from the corner: step p over, q down, coprime, max <= 7 and min <= 4.
RAYS = [(p, q) for p in range(1, 8) for q in range(1, 8) if gcd(p, q) == 1 and min(p, q) <= 4]

# Just-intonation intervals inside one octave, with their traditional class.
INTERVALS = [
    (1, 1, "unison", "perfect"),
    (16, 15, "minor 2nd", "dissonant"),
    (9, 8, "major 2nd", "dissonant"),
    (6, 5, "minor 3rd", "imperfect"),
    (5, 4, "major 3rd", "imperfect"),
    (4, 3, "perfect 4th", "perfect"),
    (7, 5, "septimal tritone", "septimal"),
    (45, 32, "tritone", "dissonant"),
    (3, 2, "perfect 5th", "perfect"),
    (8, 5, "minor 6th", "imperfect"),
    (5, 3, "major 6th", "imperfect"),
    (7, 4, "harmonic 7th", "septimal"),
    (16, 9, "minor 7th", "dissonant"),
    (9, 5, "minor 7th", "dissonant"),
    (15, 8, "major 7th", "dissonant"),
    (2, 1, "octave", "perfect"),
]
# Categorical slots 1-4 of the dataviz reference palette, validated for CVD.
CLASS_COLOUR = {"perfect": "#2a78d6", "imperfect": "#eb6834",
                "dissonant": "#1baf7a", "septimal": "#eda100"}
CLASS_NAME = {"perfect": "perfect consonance", "imperfect": "imperfect consonance",
              "dissonant": "dissonance", "septimal": "septimal (7-limit)"}


def save_png(img, name):
    """Save a Pillow image with nothing but pixels."""
    img = img.convert("RGB")
    clean = Image.new("RGB", img.size)
    clean.paste(img)
    clean.save(OUT / name, optimize=True)


def save_fig(fig, name):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    save_png(Image.open(buf), name)


def ray_colour(p, q):
    """Hue by angle; the 1:1 diagonal is pure red."""
    hue = ((math.degrees(math.atan2(q, p)) - 45) / 90 * 0.8) % 1
    return tuple(round(255 * c) for c in colorsys.hsv_to_rgb(hue, 1, 1))


def grid(w, h):
    """RGB array, row y-1 and column x-1: coprime white, the rest black, rays coloured."""
    x, y = np.arange(1, w + 1), np.arange(1, h + 1)
    g = np.where(np.gcd.outer(y, x) == 1, 255, 0).astype(np.uint8)
    rgb = np.stack([g] * 3, axis=-1)
    for p, q in RAYS:
        k = np.arange(2, min(w // p, h // q) + 1)
        rgb[k * q - 1, k * p - 1] = ray_colour(p, q)
    return rgb


def grid_screen():
    rgb = grid(3840, 2160)
    save_png(Image.fromarray(rgb), "grid-3840x2160.png")


def grid_blocks(n=100, s=20, a=4):
    """Blocks of s px, rays as solid lines through the block centres (drawn at a x, then reduced)."""
    rgb = grid(n, n)
    big = Image.fromarray(rgb.repeat(s * a, 0).repeat(s * a, 1))
    d = ImageDraw.Draw(big)
    centre = lambda x, y: ((x - 0.5) * s * a, (y - 0.5) * s * a)
    for p, q in sorted(RAYS, key=lambda r: -max(r)):        # 1:1 drawn last, on top
        k = n // max(p, q)
        d.line([centre(2 * p, 2 * q), centre(k * p, k * q)], fill=ray_colour(p, q), width=6 * a)
    save_png(big.resize((n * s, n * s), Image.LANCZOS), "grid-100.png")


def number_line(qmax=60):
    pts = [(p / q, 1 / (p * p + q * q)) for q in range(1, qmax + 1)
           for p in range(q, 2 * q + 1) if gcd(p, q) == 1]
    floor = 1 / 20000
    fig, ax = plt.subplots(figsize=(22, 10.5), dpi=150)
    ax.set_yscale("log")
    ax.vlines([x for x, _ in pts], floor, [h for _, h in pts], color="#b8b7b2", linewidth=0.6)
    for p, q, name, cls in INTERVALS:
        x, h = p / q, 1 / (p * p + q * q)
        ax.vlines(x, floor, h, color=CLASS_COLOUR[cls], linewidth=2.2)
        ax.annotate(f"{name}\n{p}:{q}", (x, h), xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9.5, color="#0b0b0b")
    dens = [2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
    ax.yaxis.set_major_locator(FixedLocator([1 / d for d in dens]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticklabels([f"1/{d}" for d in dens])
    ax.set_ylim(floor, 1.2)
    ax.set_xlim(0.97, 2.03)
    ax.set_xticks([1, 1.25, 4 / 3, 1.5, 5 / 3, 1.75, 2], ["1", "5/4", "4/3", "3/2", "5/3", "7/4", "2"])
    ax.set_xlabel("p / q   (coprime, 1 ≤ p/q ≤ 2: one octave)")
    ax.set_ylabel("height = 1 / (p² + q²)   (log scale)")
    ax.set_title(f"Every coprime fraction between 1 and 2 (denominators up to {qmax}), "
                 "the just-intonation intervals coloured by class")
    for cls, col in CLASS_COLOUR.items():
        ax.plot([], [], color=col, linewidth=2.2, label=CLASS_NAME[cls])
    ax.plot([], [], color="#b8b7b2", linewidth=1, label="other coprime fractions")
    ax.legend(loc="upper center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.07))
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    save_fig(fig, "number-line.png")


def euler_gradus(n):
    """Euler's gradus suavitatis: 1 + sum of (prime - 1) over the prime factors of n."""
    g, d = 1, 2
    while n > 1:
        while n % d == 0:
            g += d - 1
            n //= d
        d += 1
    return g


def ranking_table():
    """Each interval's score and rank under four rules; equal scores share a rank."""
    rules = {"p²+q²": lambda p, q: p * p + q * q,
             "p+q (Pythagorean)": lambda p, q: p + q,
             "p·q (Tenney)": lambda p, q: p * q,
             "Euler gradus": lambda p, q: euler_gradus(p * q)}
    seen, rows = set(), []
    for p, q, name, _ in INTERVALS:
        if (p, q) not in seen:
            seen.add((p, q))
            rows.append((p, q, name))
    ranks = {}
    for rule, f in rules.items():
        scores = sorted({f(p, q) for p, q, _ in rows})
        ranks[rule] = {(p, q): (f(p, q), 1 + sum(s < f(p, q) for s in scores)) for p, q, _ in rows}
    rows.sort(key=lambda r: rules["p²+q²"](r[0], r[1]))
    head = "| Interval | Ratio | " + " | ".join(rules) + " |"
    print(head)
    print("|" + "---|" * (2 + len(rules)))
    for p, q, name in rows:
        cells = " | ".join(f"{ranks[r][p, q][0]} ({ranks[r][p, q][1]})" for r in rules)
        print(f"| {name} | {p}:{q} | {cells} |")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    grid_screen()
    grid_blocks()
    number_line()
    ranking_table()
