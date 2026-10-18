"""Closing: discovery versus delivery.

Voice (scene time): 0.337 "The index is the neutral bridge (1.41) for discovery (2.64) across
agent ecosystems." 5.918 "Agent Box handles delivery (7.06) in this demo." 8.988 "Together,
they let agents in different apps find each other and communicate." Speech ends at 13.81.

Layout: tall Muse and Wajo cards at the sides span two lanes. The top lane is
discovery (NANDA Index, dashed blue two way links); the bottom lane is delivery
(Agent Box, solid teal links). Wajo looks up Muse through the Index ("Find Muse",
resolved back as "Muse found"), then a Greeting goes Wajo to Agent Box to Muse,
then a Reply goes Muse to Agent Box to Wajo. Each pill fades in at the sender's
card edge, settles on the hub for 0.5 s while the hub brightens, and fades out
at the receiver's card edge as "Received" appears.
"""

from __future__ import annotations

import gfx
from engine import blit, brand, enter, fade

from .base import Scene
from .diagram import Link, Node, Route, draw_route, message_pill, received_chip, swap_pill

CARD_W = 290
MUSE_CX = 100 + CARD_W // 2            # card spans 100..390, text stays inside the safe area
WAJO_CX = brand.W - 100 - CARD_W // 2  # card spans 1530..1820
MUSE_R = MUSE_CX + CARD_W // 2
WAJO_L = WAJO_CX - CARD_W // 2
CX = 960
CENTER_W = 440
CENTER_H = 128
CENTER_L = CX - CENTER_W // 2
CENTER_R = CX + CENTER_W // 2

L1 = 400                  # discovery lane
L2 = 720                  # delivery lane
CARD_TOP = L1 - 120
CARD_H = (L2 + 120) - CARD_TOP
CARD_CY = CARD_TOP + CARD_H // 2
HEADER_Y = 172
TAG_DY = -108             # tag center relative to its lane
CAPTION_DY = 114          # caption baseline relative to its lane
CHIP_Y = CARD_TOP + CARD_H + 22 + 29

LINK_S = 0.7
HEADS_S = 0.35
LEG_S = 1.3
SETTLE_S = 0.5
LOOK_SETTLE_S = 0.6       # a little longer on the Index, where the label changes


class Closing(Scene):
    name = "closing"
    nominal = 16.808
    beats = {
        "build": 0.40,          # Muse and Wajo cards enter
        "index": 0.80,          # NANDA Index node and "Discovery" tag
        "discovery_links": 1.25,
        "bridge": 1.60,         # "Neutral bridge across ecosystems" ("neutral bridge" at 1.41)
        "index_caption": 2.35,  # "NANDA Index finds and resolves the agent" ("discovery" at 2.64)
        "lookup": 2.60,         # "Find Muse" Wajo to Index, settles, returns as "Muse found"
        "agent_box": 5.92,      # Agent Box node, "Delivery" tag, teal links ("Agent Box" at 5.92)
        "greeting": 6.75,       # Greeting Wajo to Agent Box to Muse, then "Received" at Muse
        "box_caption": 7.00,    # "Agent Box delivers the message" ("delivery" at 7.06)
        "reply": 10.05,         # Reply Muse to Agent Box to Wajo, then "Received" at Wajo
    }
    params = {
        "header": "Neutral bridge across ecosystems",
        "index_caption": "NANDA Index finds and resolves the agent",
        "box_caption": "Agent Box delivers the message",
        "show_header": True,
    }

    def configure(self):
        b = self.b
        # Pill centers start and end on the card edges (half over the card), hubs at the center.
        self.look = Route(WAJO_L, CX, WAJO_L, b["lookup"], LEG_S, LOOK_SETTLE_S)
        self.greet_route = Route(WAJO_L, CX, MUSE_R, b["greeting"], LEG_S, SETTLE_S)
        self.reply_route = Route(MUSE_R, CX, WAJO_L, b["reply"], LEG_S, SETTLE_S)

    def settle_time(self) -> float:
        b = self.b
        ends = [
            b["build"] + 0.12 + brand.ENTER_S, b["index"] + 0.1 + brand.ENTER_S,
            b["discovery_links"] + LINK_S - 0.2 + HEADS_S, b["bridge"] + brand.ENTER_S,
            b["index_caption"] + brand.ENTER_S, self.look.end + 0.45,
            b["agent_box"] + 0.3 + LINK_S, b["agent_box"] + 0.1 + brand.ENTER_S,
            b["box_caption"] + brand.ENTER_S,
            self.greet_route.end - 0.2 + brand.ENTER_S, self.greet_route.t2 + 0.45,
            self.reply_route.end - 0.2 + brand.ENTER_S, self.reply_route.t2 + 0.45,
        ]
        return max(ends)

    def build(self):
        p = self.p
        self.muse = Node("agent", "Muse", "Agent in Muse", CARD_W, CARD_H)
        self.wajo = Node("agent", "Wajo", "Agent in Wajo", CARD_W, CARD_H)
        self.index = Node("index", "NANDA Index", None, CENTER_W, CENTER_H)
        self.abox = Node("box", "Agent Box", None, CENTER_W, CENTER_H)
        self.d_l = Link(MUSE_R, CENTER_L, "discovery")
        self.d_r = Link(CENTER_R, WAJO_L, "discovery")
        self.t_l = Link(MUSE_R, CENTER_L, "delivery")
        self.t_r = Link(CENTER_R, WAJO_L, "delivery")
        self.tag_d = gfx.pill("Discovery", 32, 600, "brand_600", "surface_tag", h=52, pad_x=20,
                              radius=brand.RADIUS_CONTROL)
        self.tag_t = gfx.pill("Delivery", 32, 600, "teal_ink", "teal", outline="#bfdfe7", h=52, pad_x=20,
                              radius=brand.RADIUS_CONTROL)
        self.header = gfx.text(p["header"], 40, 500, "ink_medium", 0.0, "m")
        self.cap_i = gfx.text(p["index_caption"], 38, 500, "ink", 0.0, "m")
        self.cap_b = gfx.text(p["box_caption"], 38, 500, "ink", 0.0, "m")
        self.look_body, (self.find, self.found) = swap_pill([("Find Muse", "search"), ("Muse found", "check")])
        self.greet = message_pill("Greeting")
        self.reply = message_pill("Reply")
        self.received = received_chip()

    def render(self, canvas, t):
        b = self.b
        am, dm = enter(t, b["build"])
        aw, dw = enter(t, b["build"] + brand.STAGGER_S)
        ai, di = enter(t, b["index"])
        atd, dtd = enter(t, b["index"] + 0.1)
        ab, db = enter(t, b["agent_box"])
        att, dtt = enter(t, b["agent_box"] + 0.1)
        rev_d = brand.ease_in_out_cubic(brand.progress(t, b["discovery_links"], LINK_S))
        heads = fade(t, b["discovery_links"] + LINK_S - 0.2, HEADS_S)
        rev_t = brand.ease_in_out_cubic(brand.progress(t, b["agent_box"] + 0.3, LINK_S))
        swap = self.look.swap(t)
        lit_i = 0.6 * self.look.lit(t)
        lit_b = 0.85 * max(self.greet_route.lit(t), self.reply_route.lit(t))
        text_i = self.look.hub_text(t, self.look_body.adv, self.index.name.adv)
        text_b = min(self.greet_route.hub_text(t, self.greet.adv, self.abox.name.adv),
                     self.reply_route.hub_text(t, self.reply.adv, self.abox.name.adv))

        # Shadows.
        self.muse.draw_shadow(canvas, MUSE_CX, CARD_CY + dm, am)
        self.wajo.draw_shadow(canvas, WAJO_CX, CARD_CY + dw, aw)
        self.index.draw_shadow(canvas, CX, L1 + di, ai)
        self.abox.draw_shadow(canvas, CX, L2 + db, ab)
        # Links.
        self.d_l.draw(canvas, L1, rev_d, grow="left", heads=heads)
        self.d_r.draw(canvas, L1, rev_d, grow="right", heads=heads)
        self.t_l.draw(canvas, L2, rev_t, grow="left")
        self.t_r.draw(canvas, L2, rev_t, grow="right")
        # Bodies.
        self.muse.draw_body(canvas, MUSE_CX, CARD_CY + dm, am)
        self.wajo.draw_body(canvas, WAJO_CX, CARD_CY + dw, aw)
        self.index.draw_body(canvas, CX, L1 + di, ai, lit=lit_i, text_alpha=ai * text_i)
        self.abox.draw_body(canvas, CX, L2 + db, ab, lit=lit_b, text_alpha=ab * text_b)
        # Tags, header, captions.
        blit(canvas, self.tag_d, CX, L1 + TAG_DY + dtd, atd)
        blit(canvas, self.tag_t, CX, L2 + TAG_DY + dtt, att)
        if self.p["show_header"]:
            ah, dh = enter(t, b["bridge"])
            blit(canvas, self.header, CX, HEADER_Y + dh, ah)
        aci, dci = enter(t, b["index_caption"])
        blit(canvas, self.cap_i, CX, L1 + CAPTION_DY + dci, aci)
        acb, dcb = enter(t, b["box_caption"])
        blit(canvas, self.cap_b, CX, L2 + CAPTION_DY + dcb, acb)
        # Received chips at the receivers, as each pill fades out at the card edge.
        a1, d1 = enter(t, self.greet_route.end - 0.2)
        blit(canvas, self.received, MUSE_CX, CHIP_Y + d1, a1)
        a2, d2 = enter(t, self.reply_route.end - 0.2)
        blit(canvas, self.received, WAJO_CX, CHIP_Y + d2, a2)
        # Moving pills, above everything. The lookup changes its label while on the Index.
        # The lookup keeps one pill body; its label changes from "Find Muse" to "Muse found" on the Index.
        draw_route(canvas, self.look_body, self.look, t, L1)
        draw_route(canvas, self.find, self.look, t, L1, 1.0 - brand.ease_in_out_sine(min(1.0, 2 * swap)))
        draw_route(canvas, self.found, self.look, t, L1, brand.ease_in_out_sine(max(0.0, 2 * swap - 1)))
        draw_route(canvas, self.greet, self.greet_route, t, L2)
        draw_route(canvas, self.reply, self.reply_route, t, L2)
