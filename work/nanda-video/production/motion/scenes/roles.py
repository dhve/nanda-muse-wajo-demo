"""Roles: continues from the intro's last frame.

Voice (scene time): 0.383 "The index helps agents find each other across different apps."
5.128 "Agent Box gives them an address (6.20) and delivers (7.27) their messages."
9.244 "You can keep using the app you already know." Speech ends at 12.26.
"""

from __future__ import annotations

import gfx
from engine import blit, brand, enter, fade

from .base import Scene, ease_move
from .diagram import Link, Node, Route, draw_route, message_pill
from .opening import (CARD_TOP, CENTER_L, CENTER_R, CENTER_W, CX, L1, L2, MUSE_CX, MUSE_R, NODE_H,
                      ROLES_CARD_H, ROW_Y_INTRO, SCROLL, WAJO_CX, WAJO_L, OpeningParts)
from .intro import Intro

SCROLL_S = 1.1
GROW_S = 0.9
LINK_S = 0.7
LEG_S = 1.3
SETTLE_S = 0.5
HALO = 14


class Roles(Scene):
    name = "roles"
    nominal = 12.257
    beats = {
        "clear": 0.30,        # title block fades out, the row moves up
        "index_focus": 1.25,  # soft highlight on NANDA Index plus "Finds agents across apps"
        "agent_box": 5.13,    # cards grow, Agent Box rises in below center, teal links draw
        "address": 6.20,      # "Agent Box address" chip under each agent
        "hop": 7.00,          # one message hop Wajo to Agent Box to Muse ("delivers" at 7.27)
        "own_app": 9.30,      # "Keep using the app you already know."
    }
    params = {
        "caption": "Finds agents across apps",
        "message": "Message",
        "line": "Keep using the app you already know.",
        **Intro.params,
    }

    def configure(self):
        # The pill leaves Wajo's card edge, settles on Agent Box, and fades out at Muse's card edge.
        self.route = Route(WAJO_L, CX, MUSE_R, self.b["hop"], LEG_S, SETTLE_S)

    def settle_time(self) -> float:
        b = self.b
        return max(b["clear"] + SCROLL_S, b["index_focus"] + 0.15 + brand.ENTER_S,
                   b["agent_box"] + 0.8 + LINK_S, b["agent_box"] + GROW_S, b["agent_box"] - 0.2 + 0.6,
                   b["address"] + 0.12 + brand.ENTER_S, self.route.end, self.route.t2 + 0.45,
                   b["own_app"] + brand.ENTER_S)

    def build(self):
        self.parts = OpeningParts(self.p["eyebrow"], self.p["title"], self.p["subtitle"])
        self.abox = Node("box", "Agent Box", "Address and delivery", CENTER_W, NODE_H)
        self.dlink_l = Link(MUSE_R, CENTER_L, "delivery")
        self.dlink_r = Link(CENTER_R, WAJO_L, "delivery")
        self.halo = gfx.box(CENTER_W + 2 * HALO, NODE_H + 2 * HALO, brand.RADIUS_CARD + HALO, "brand_200", None)
        self.ring = gfx.ring(CENTER_W + 2 * HALO, NODE_H + 2 * HALO, brand.RADIUS_CARD + HALO, 3, "blue")
        self.caption = gfx.text(self.p["caption"], 38, 500, "ink", 0.0, "m")
        self.line = gfx.text(self.p["line"], 52, 600, "navy", -0.01, "m")
        self.chip = gfx.pill("Agent Box address", 32, 600, "teal_ink", "teal", outline="#bfdfe7",
                             outline_w=2, h=58, pad_x=22)
        self.msg = message_pill(self.p["message"])

    def render(self, canvas, t):
        b, P = self.b, self.parts
        s = ease_move(t, b["clear"], SCROLL_S) * SCROLL
        row = ROW_Y_INTRO - s                       # discovery row center
        row2 = row + (L2 - L1)                      # delivery row center
        # Title block leaves with the scroll.
        ta = 1.0 - fade(t, b["clear"], 0.55)
        if ta > 0:
            P.draw_title(canvas, -s, (ta, ta, ta))
        # Cards grow down to span both rows.
        g = ease_move(t, b["agent_box"], GROW_S)
        card_h = NODE_H + (ROLES_CARD_H - NODE_H) * g
        hi = round(card_h)
        top = row - NODE_H / 2
        card_cy = top + hi / 2
        text_cy = top + card_h / 2
        # Index focus, faded back when Agent Box arrives.
        focus = fade(t, b["index_focus"], 0.6) * (1.0 - fade(t, b["agent_box"] - 0.2, 0.6))
        ac, dc = enter(t, b["index_focus"] + 0.15)
        aa, da = enter(t, b["agent_box"] + 0.25)
        reveal2 = brand.ease_in_out_cubic(brand.progress(t, b["agent_box"] + 0.8, LINK_S))
        lit = 0.85 * self.route.lit(t)
        text_b = self.route.hub_text(t, self.msg.adv, self.abox.sub.adv)

        # Shadows.
        P.muse.draw_shadow(canvas, MUSE_CX, card_cy, 1.0, hi)
        P.wajo.draw_shadow(canvas, WAJO_CX, card_cy, 1.0, hi)
        P.index.draw_shadow(canvas, CX, row)
        self.abox.draw_shadow(canvas, CX, row2 + da, aa)
        # Index highlight.
        if focus > 0:
            blit(canvas, self.halo, CENTER_L - HALO, row - NODE_H / 2 - HALO, focus)
            blit(canvas, self.ring, CENTER_L - HALO, row - NODE_H / 2 - HALO, 0.9 * focus)
        # Links.
        P.link_l.draw(canvas, row)
        P.link_r.draw(canvas, row)
        self.dlink_l.draw(canvas, row2, reveal2, grow="left")
        self.dlink_r.draw(canvas, row2, reveal2, grow="right")
        # Bodies.
        P.muse.draw_body(canvas, MUSE_CX, card_cy, 1.0, hi, text_cy=text_cy)
        P.wajo.draw_body(canvas, WAJO_CX, card_cy, 1.0, hi, text_cy=text_cy)
        P.index.draw_body(canvas, CX, row)
        self.abox.draw_body(canvas, CX, row2 + da, aa, lit=lit, text_alpha=aa * text_b)
        # Captions and chips.
        blit(canvas, self.caption, CX, row + NODE_H / 2 + 76 + dc, ac)
        chip_y = top + ROLES_CARD_H + 24 + 29
        for i, cx in enumerate((MUSE_CX, WAJO_CX)):
            a, d = enter(t, b["address"] + i * brand.STAGGER_S)
            blit(canvas, self.chip, cx, chip_y + d, a)
        al, dl = enter(t, b["own_app"])
        blit(canvas, self.line, CX, 870 + dl, al)
        # The message pill, above everything.
        draw_route(canvas, self.msg, self.route, t, row2)
