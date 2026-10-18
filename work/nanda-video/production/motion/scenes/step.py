"""Step card: numbered circle, "Step N of 5", title, subtitle and a quiet progress bar.

Everything is in by about 0.8 s, then it holds. Subtitles use rich text so
"Wajo → Muse" gets a vector arrow.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

import gfx
from engine import Sprite, blit, brand, enter

from .base import Scene

STEPS = {
    1: ("Set up both agents", "In Muse and Wajo"),
    2: ("Verify each email", "Send each code back in its app"),
    3: ("Find Muse and say hello", "Discover through NANDA Index"),
    4: ("Read and reply in Muse", "Wajo → Muse"),
    5: ("See the reply in Wajo", "Muse → Wajo"),
}

GX = 236                 # left edge of the group
CIRCLE_D = 168
TEXT_X = GX + CIRCLE_D + 64
EYEBROW_SIZE, TITLE_SIZE, SUB_SIZE = 32, 88, 46
SEG_W, SEG_H, SEG_GAP = 96, 10, 12
STAGGER = 0.06
ENTER = 0.55


def progress_bar(n: int, total: int) -> Sprite:
    w = total * SEG_W + (total - 1) * SEG_GAP
    img = Image.new("RGBA", (w, SEG_H), (0, 0, 0, 0))
    for i in range(total):
        if i + 1 == n:
            fill = brand.rgba("blue")
        elif i + 1 < n:
            fill = brand.rgba("blue", 0.45)
        else:
            fill = brand.rgba("line")
        seg = gfx.box_image(SEG_W, SEG_H, SEG_H / 2, fill)
        img.alpha_composite(seg, (i * (SEG_W + SEG_GAP), 0))
    return Sprite(img, 0, 0, w)


class Step(Scene):
    name = "step"
    nominal = 3.0
    beats = {"enter": 0.05}   # start of the staggered entrance
    params = {"number": 1, "total": 5, "title": "", "subtitle": ""}
    min_hold = 0.4

    def configure(self):
        n = int(self.p["number"])
        title, sub = STEPS.get(n, ("", ""))
        self.title_text = self.p["title"] or title
        self.sub_text = self.p["subtitle"] or sub

    def settle_time(self) -> float:
        return self.b["enter"] + 4 * STAGGER + ENTER

    def build(self):
        n, total = int(self.p["number"]), int(self.p["total"])
        self.circle = gfx.number_circle(CIRCLE_D, str(n), 84, "brand_200", "brand_600", 600, outline="line")
        self.eyebrow = gfx.text(f"Step {n} of {total}", EYEBROW_SIZE, 600, "ink_weak", 0.025, "l")
        self.title = gfx.text(self.title_text, TITLE_SIZE, 600, "navy", -0.015, "l")
        self.sub = gfx.rich(self.sub_text, SUB_SIZE, 400, "ink_medium", 0.0, "l", arrow_color="blue")
        self.bar = progress_bar(n, total)
        e_cap = brand.metrics(EYEBROW_SIZE, 600)["cap"]
        t_cap = brand.metrics(TITLE_SIZE, 600)["cap"]
        s_cap = brand.metrics(SUB_SIZE, 400)["cap"]
        # Vertical rhythm, then center the whole group on the frame.
        e_base = e_cap
        t_base = e_base + 34 + t_cap
        s_base = t_base + 42 + s_cap
        bar_top = s_base + 54
        bottom = bar_top + SEG_H
        off = round(brand.H / 2 - bottom / 2)
        self.e_y, self.t_y, self.s_y, self.bar_y = e_base + off, t_base + off, s_base + off, bar_top + off
        self.circle_cy = round(off + (t_base - t_cap / 2) * 0.5 + (s_base - s_cap / 2) * 0.5)

    def render(self, canvas, t):
        s = self.b["enter"]
        a, d = enter(t, s, ENTER)
        blit(canvas, self.circle, GX + CIRCLE_D / 2, self.circle_cy + d, a)
        a, d = enter(t, s + STAGGER, ENTER)
        blit(canvas, self.eyebrow, TEXT_X, self.e_y + d, a)
        a, d = enter(t, s + 2 * STAGGER, ENTER)
        blit(canvas, self.title, TEXT_X, self.t_y + d, a)
        a, d = enter(t, s + 3 * STAGGER, ENTER)
        blit(canvas, self.sub, TEXT_X, self.s_y + d, a)
        a, d = enter(t, s + 4 * STAGGER, ENTER)
        blit(canvas, self.bar, TEXT_X, self.bar_y + d, a)
