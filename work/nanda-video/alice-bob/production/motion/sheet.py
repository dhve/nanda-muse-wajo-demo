"""Development helper: render a grid of scene frames (straight from the renderer) to a PNG.

  python3 motion/sheet.py SCENE OUT.png t1 t2 ... [--cols 3] [--scale 0.5] [--param k=v]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "lib"), str(HERE)]

from PIL import Image, ImageDraw  # noqa: E402

import brand  # noqa: E402
import engine  # noqa: E402
import scenes  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("out")
    ap.add_argument("times", nargs="+", type=float)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--param", action="append", default=[])
    a = ap.parse_args()
    params = dict(p.split("=", 1) for p in a.param)
    sc = scenes.build(a.scene, None, None, params)
    w, h = int(1920 * a.scale), int(1080 * a.scale)
    rows = (len(a.times) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.cols * w + (a.cols - 1) * 8, rows * (h + 40) - 8 + 40), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(a.times):
        c = engine.new_canvas(sc.background)
        sc.draw(c, t)
        im = Image.fromarray(engine.to_rgb8(c)).resize((w, h), Image.Resampling.LANCZOS)
        x, y = (i % a.cols) * (w + 8), (i // a.cols) * (h + 40)
        sheet.paste(im, (x, y + 40))
        brand.draw_text(d, x + 8, y + 30, f"{a.scene} t={t:.2f}s", 26, 500, (235, 235, 235, 255))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
