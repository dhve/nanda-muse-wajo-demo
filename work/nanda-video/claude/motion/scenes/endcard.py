"""Endcard: Try it yourself, the guide URL, three prompt chips and the footer.

Voice (scene time): 0.442 "Try it yourself with the short prompts in the guide." 3.675 "Set up,
find (4.40) an agent, and send (5.81) a message." Speech ends at 7.11, then 2 s.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

import gfx
from engine import Sprite, blit, brand, enter

from .base import Scene

CX = 960
TITLE_Y = 400
URL_Y = 492
CHIPS_Y = 642          # chip row center
CHIP_H = 92
CHIP_GAP = 36
FOOTER_Y = 952


def prompt_chip(n: int, label: str) -> Sprite:
    """White card with a numbered circle and a label. Anchor: center of the card body."""
    d = 52
    pad_l, gap, pad_r = 22, 18, 32
    size = 40
    lw = brand.text_width(label, size, 600, -0.005)
    w = math.ceil(pad_l + d + gap + lw + pad_r)
    w += w % 2
    h = CHIP_H
    sh, m = brand.soft_shadow(w, h, brand.RADIUS_CARD, blur=14, opacity=0.55)
    out = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 8))
    out.alpha_composite(gfx.box_image(w, h, brand.RADIUS_CARD, "surface_light", "line"), (m, m))
    cimg = gfx.circle(d, "brand_200")
    brand.draw_text(ImageDraw.Draw(cimg), d / 2, d / 2, str(n), 30, 600, brand.rgba("brand_600"), 0.0, "mc")
    out.alpha_composite(cimg, (m + pad_l, m + (h - d) // 2))
    cap = brand.metrics(size, 600)["cap"]
    brand.draw_text(ImageDraw.Draw(out), m + pad_l + d + gap, m + h / 2 + cap / 2, label, size, 600,
                    brand.rgba("navy"), -0.005, "ls")
    return Sprite(out, m + w // 2, m + h // 2, w)


class Endcard(Scene):
    name = "endcard"
    nominal = 9.109
    beats = {
        "title": 0.40,     # "Try it yourself" ("Try" at 0.44)
        "url": 0.70,       # my.nandaindex.org/demo
        "footer": 1.10,    # NANDA Index - Federated Agent Discovery
        "prompt1": 3.65,   # "Set up" (3.68)
        "prompt2": 4.40,   # "find an agent" (4.40)
        "prompt3": 5.80,   # "send a message" (5.81)
    }
    params = {
        "title": "Try it yourself",
        "url": "my.nandaindex.org/demo",
        "footer": "NANDA Index - Federated Agent Discovery",
        "prompt1": "Set up",
        "prompt2": "Find an agent",
        "prompt3": "Send a message",
    }

    def settle_time(self) -> float:
        b = self.b
        return max(b[k] for k in self.beats) + brand.ENTER_S

    def build(self):
        p = self.p
        self.title = gfx.text(p["title"], 104, 600, "navy", -0.02, "m")
        self.url = gfx.text(p["url"], 52, 500, "blue", 0.0, "m")
        self.footer = gfx.text(p["footer"], 32, 500, "ink_weak", 0.01, "m")
        self.chips = [prompt_chip(i + 1, p[f"prompt{i + 1}"]) for i in range(3)]
        total = sum(c.adv for c in self.chips) + CHIP_GAP * 2
        x = CX - total / 2
        self.chip_x = []
        for c in self.chips:
            self.chip_x.append(round(x + c.adv / 2))
            x += c.adv + CHIP_GAP

    def render(self, canvas, t):
        b = self.b
        a, d = enter(t, b["title"])
        blit(canvas, self.title, CX, TITLE_Y + d, a)
        a, d = enter(t, b["url"])
        blit(canvas, self.url, CX, URL_Y + d, a)
        for i, (c, x) in enumerate(zip(self.chips, self.chip_x)):
            a, d = enter(t, b[f"prompt{i + 1}"])
            blit(canvas, c, x, CHIPS_Y + d, a)
        a, d = enter(t, b["footer"])
        blit(canvas, self.footer, CX, FOOTER_Y + d, a)
