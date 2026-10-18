"""Geometry and sprites shared by the intro and roles scenes.

The intro ends on: title block at the top, Muse card, NANDA Index node and Wajo
card in one row with dashed two way links. Roles starts on exactly that frame,
so both scenes draw it through the same functions here.
"""

from __future__ import annotations

import gfx
from engine import blit, brand

from .diagram import Link, Node

# Row geometry (canvas pixels).
CARD_W = 340
NODE_H = 160
CENTER_W = 440
CX = 960
MUSE_CX = brand.SAFE_X + CARD_W // 2          # 290 (card spans 120..460)
WAJO_CX = brand.W - brand.SAFE_X - CARD_W // 2  # 1630 (card spans 1460..1800)
MUSE_R = MUSE_CX + CARD_W // 2                 # 460
WAJO_L = WAJO_CX - CARD_W // 2                 # 1460
CENTER_L = CX - CENTER_W // 2                  # 740
CENTER_R = CX + CENTER_W // 2                  # 1180

ROW_Y_INTRO = 690          # diagram row center at the end of the intro

# Title block baselines in its final (top) position.
EYEBROW_Y = 220
TITLE_Y = 332
SUBTITLE_Y = 410
TITLE_CENTER_DY = 222      # extra y while the block sits at the screen center

# Roles layout.
L1 = 300                   # discovery row (Index) center
L2 = 600                   # delivery row (Agent Box) center
CARD_TOP = L1 - NODE_H // 2
ROLES_CARD_H = (L2 + NODE_H // 2) - CARD_TOP   # cards grow to span both rows
SCROLL = ROW_Y_INTRO - L1  # how far the intro layout moves up in roles


class OpeningParts:
    def __init__(self, eyebrow: str, title: str, subtitle: str):
        self.eyebrow = gfx.text(eyebrow, 32, 600, "ink_weak", 0.025, "m")
        self.title = gfx.text(title, 104, 600, "navy", -0.02, "m")
        self.subtitle = gfx.text(subtitle, 42, 400, "ink_medium", 0.0, "m")
        self.muse = Node("agent", "Alice", "Muse agent", CARD_W, NODE_H, max_h=ROLES_CARD_H)
        self.wajo = Node("agent", "Bob", "Wajo agent", CARD_W, NODE_H, max_h=ROLES_CARD_H)
        self.index = Node("index", "NANDA Index", "Discovery", CENTER_W, NODE_H)
        self.link_l = Link(MUSE_R, CENTER_L, "discovery")
        self.link_r = Link(CENTER_R, WAJO_L, "discovery")

    def draw_title(self, canvas, dy: float, alphas=(1.0, 1.0, 1.0), rises=(0.0, 0.0, 0.0)):
        blit(canvas, self.eyebrow, CX, EYEBROW_Y + dy + rises[0], alphas[0])
        blit(canvas, self.title, CX, TITLE_Y + dy + rises[1], alphas[1])
        blit(canvas, self.subtitle, CX, SUBTITLE_Y + dy + rises[2], alphas[2])
