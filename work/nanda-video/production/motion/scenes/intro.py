"""Intro: title card, then the Muse, NANDA Index, Wajo discovery row builds.

Voice (scene time): 1.200 to 7.758 "Let's connect an agent in Muse (2.76) with an
agent in Wajo (4.53), and send a message (5.62) in both directions (6.76)."
"""

from __future__ import annotations

from engine import brand, enter, fade

from .base import Scene, ease_move
from .opening import (CX, MUSE_CX, ROW_Y_INTRO, TITLE_CENTER_DY, WAJO_CX, OpeningParts)

LIFT_S = 0.9
LINK_S = 0.8
HEADS_S = 0.35


class Intro(Scene):
    name = "intro"
    nominal = 11.123
    beats = {
        "title": 0.40,    # eyebrow, title, subtitle fade and rise in (0.12 s stagger)
        "lift": 2.20,     # title block moves up to make room
        "muse": 2.90,     # Muse card enters ("Muse" is spoken at 2.76)
        "wajo": 4.45,     # Wajo card enters ("Wajo" at 4.53)
        "index": 5.30,    # NANDA Index node enters ("send a message" at 5.62)
        "links": 5.85,    # two way links draw out from the Index, arrowheads at the end
    }
    params = {
        "eyebrow": "Muse + Wajo demo",
        "title": "Connect Muse and Wajo",
        "subtitle": "Find each other through NANDA Index, then send a message and a reply.",
    }

    def settle_time(self) -> float:
        b = self.b
        return max(b["title"] + 0.24 + brand.ENTER_S, b["lift"] + LIFT_S, b["muse"] + brand.ENTER_S,
                   b["wajo"] + brand.ENTER_S, b["index"] + brand.ENTER_S,
                   b["links"] + LINK_S - 0.2 + HEADS_S)

    def build(self):
        self.parts = OpeningParts(self.p["eyebrow"], self.p["title"], self.p["subtitle"])

    def render(self, canvas, t):
        b, P = self.b, self.parts
        # Title block.
        ent = [enter(t, b["title"] + i * brand.STAGGER_S) for i in range(3)]
        k = ease_move(t, b["lift"], LIFT_S)
        P.draw_title(canvas, (1.0 - k) * TITLE_CENTER_DY, tuple(a for a, _ in ent), tuple(d for _, d in ent))
        # Diagram row.
        y = ROW_Y_INTRO
        am, dm = enter(t, b["muse"])
        aw, dw = enter(t, b["wajo"])
        ai, di = enter(t, b["index"])
        reveal = brand.ease_in_out_cubic(brand.progress(t, b["links"], LINK_S))
        heads = fade(t, b["links"] + LINK_S - 0.2, HEADS_S)
        P.muse.draw_shadow(canvas, MUSE_CX, y + dm, am)
        P.wajo.draw_shadow(canvas, WAJO_CX, y + dw, aw)
        P.index.draw_shadow(canvas, CX, y + di, ai)
        P.link_l.draw(canvas, y, reveal, grow="left", heads=heads)
        P.link_r.draw(canvas, y, reveal, grow="right", heads=heads)
        P.muse.draw_body(canvas, MUSE_CX, y + dm, am)
        P.wajo.draw_body(canvas, WAJO_CX, y + dw, aw)
        P.index.draw_body(canvas, CX, y + di, ai)
