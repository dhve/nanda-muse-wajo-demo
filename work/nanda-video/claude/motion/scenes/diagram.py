"""Shared diagram parts for intro, roles and closing.

Draw order inside a diagram: shadows, highlight halos, links, node bodies with
text, chips and captions, then moving message pills on top of everything (so a
pill is never hidden under a card or node, and its label stays readable).
"""

from __future__ import annotations

import math

import gfx
from engine import Sprite, blit, brand, column_window, mix

STYLES = {
    "agent": dict(fill="surface_light", outline="line", name_color="navy", sub_color="ink_medium",
                  name_size=58),
    "index": dict(fill="brand_800", outline=None, name_color="white", sub_color="line_strong",
                  name_size=56, lit_fill="brand_700", lit_outline=None),
    "box": dict(fill="teal", outline="#bfdfe7", name_color="teal_ink", sub_color="teal_ink",
                name_size=56, lit_fill="#f1fafc", lit_outline="teal_ink"),
}

SUB_SIZE = 32
NAME_SUB_GAP = 22


class Node:
    """A diagram node: soft shadow, rounded body, name and optional sublabel.
    Heights can change (cards that grow), using top and bottom halves of a tall sprite."""

    def __init__(self, kind: str, name: str, sub: str | None, w: int, h: int, max_h: int | None = None,
                 radius: float = brand.RADIUS_CARD, name_size: float | None = None):
        st = STYLES[kind]
        self.kind, self.w, self.h = kind, int(w), int(h)
        self.max_h = int(max_h or h)
        self.radius = radius
        self._body = gfx.box(self.w, self.max_h, radius, st["fill"], st["outline"])
        self._shadow = gfx.shadow(self.w, self.max_h, radius, blur=16, opacity=0.55, dy=10)
        self._lit = None
        if "lit_fill" in st:
            self._lit = gfx.box(self.w, self.max_h, radius, st["lit_fill"], st.get("lit_outline"))
        size = name_size or st["name_size"]
        self.name = gfx.text(name, size, 600, st["name_color"], -0.01, "m")
        self.sub = gfx.text(sub, SUB_SIZE, 500, st["sub_color"], 0.0, "m") if sub else None
        cap = brand.metrics(size, 600)["cap"]
        if self.sub is not None:
            sub_cap = brand.metrics(SUB_SIZE, 500)["cap"]
            g = cap + NAME_SUB_GAP + sub_cap
            self.name_dy = round(-g / 2 + cap)
            self.sub_dy = round(g / 2)
        else:
            self.name_dy = round(cap / 2)
            self.sub_dy = 0
        self._cache: dict[int, tuple] = {}

    def _sprites(self, h: float):
        hi = int(round(h))
        if hi not in self._cache:
            if hi >= self.max_h:
                self._cache[hi] = (self._shadow, self._body, self._lit)
            else:
                self._cache[hi] = (
                    gfx.stretch_v(self._shadow, self.max_h, hi),
                    gfx.stretch_v(self._body, self.max_h, hi),
                    gfx.stretch_v(self._lit, self.max_h, hi) if self._lit is not None else None,
                )
        return hi, self._cache[hi]

    def top_left(self, cx: float, cy: float, h: float | None = None):
        hi, _ = self._sprites(self.h if h is None else h)
        return cx - self.w / 2, cy - hi / 2

    def draw_shadow(self, canvas, cx, cy, alpha=1.0, h=None):
        hi, (sh, _, _) = self._sprites(self.h if h is None else h)
        blit(canvas, sh, cx - self.w / 2, cy - hi / 2, alpha)

    def draw_body(self, canvas, cx, cy, alpha=1.0, h=None, lit=0.0, text_alpha=None, text_cy=None):
        hi, (_, body, lit_spr) = self._sprites(self.h if h is None else h)
        spr = mix(body, lit_spr, lit) if (lit_spr is not None and lit > 0) else body
        blit(canvas, spr, cx - self.w / 2, cy - hi / 2, alpha)
        ta = alpha if text_alpha is None else text_alpha
        ty = cy if text_cy is None else text_cy
        blit(canvas, self.name, cx, ty + self.name_dy, ta)
        if self.sub is not None:
            blit(canvas, self.sub, cx, ty + self.sub_dy, ta)


class Link:
    """Horizontal link between x0 (left node edge) and x1 (right node edge).
    discovery: dashed blue with arrowheads at both ends (two way lookups).
    delivery: solid teal ink, tucked under both nodes."""

    def __init__(self, x0: float, x1: float, kind: str = "discovery"):
        self.kind = kind
        if kind == "discovery":
            inset = 12
            self.a, self.b = x0 + inset, x1 - inset
            self.line = gfx.hline(self.b - self.a, 4, "blue", dash=15, gap=11)
            self.head_l = gfx.chevron(13, 4, "blue", "left")
            self.head_r = gfx.chevron(13, 4, "blue", "right")
        else:
            self.a, self.b = x0 - 6, x1 + 6
            self.line = gfx.hline(self.b - self.a, 5, "teal_ink")
            self.head_l = self.head_r = None
        self.length = self.b - self.a

    def draw(self, canvas, y: float, reveal: float = 1.0, grow: str = "right", heads: float = 1.0,
             alpha: float = 1.0):
        """grow: 'right' draws from the left end toward the right, 'left' the reverse."""
        if reveal <= 0 or alpha <= 0:
            return
        pad = self.line.ox
        L = self.length
        if reveal >= 1:
            spr = self.line
        elif grow == "right":
            spr = column_window(self.line, 0, pad + L * reveal)
        else:
            spr = column_window(self.line, pad + L * (1 - reveal), self.line.w)
        blit(canvas, spr, self.a, y, alpha)
        if self.head_l is not None and heads > 0:
            blit(canvas, self.head_l, self.a, y, alpha * heads)
            blit(canvas, self.head_r, self.b, y, alpha * heads)


class Route:
    """A message pill that leaves the sender's card edge, settles on top of a hub
    node (Agent Box, or the Index for a lookup), then goes on to the receiver's
    card edge. Pills are drawn above cards, nodes and lines, with no motion blur.

    Timeline: fade in while leaving x_from; leg to x_hub (ease_in_out_sine);
    settle on the hub while it brightens; leg to x_to; fade out at the edge."""

    def __init__(self, x_from: float, x_hub: float, x_to: float, start: float, leg: float = 1.3,
                 settle: float = 0.5, fade_s: float = 0.3):
        self.x_from, self.x_hub, self.x_to = x_from, x_hub, x_to
        self.leg, self.settle, self.fade_s = leg, settle, fade_s
        self.t0 = start
        self.t1 = start + leg            # arrives on the hub
        self.t2 = self.t1 + settle       # leaves the hub
        self.t3 = self.t2 + leg          # reaches the receiver edge

    @property
    def end(self) -> float:
        return self.t3

    def x(self, t: float) -> float:
        if t < self.t1:
            k = brand.ease_in_out_sine(brand.progress(t, self.t0, self.leg))
            return self.x_from + (self.x_hub - self.x_from) * k
        if t < self.t2:
            return self.x_hub
        k = brand.ease_in_out_sine(brand.progress(t, self.t2, self.leg))
        return self.x_hub + (self.x_to - self.x_hub) * k

    def alpha(self, t: float) -> float:
        if t < self.t0 or t > self.t3:
            return 0.0
        a_in = brand.ease_in_out_sine(brand.progress(t, self.t0, self.fade_s))
        a_out = 1.0 - brand.ease_in_out_sine(brand.progress(t, self.t3 - self.fade_s, self.fade_s))
        return min(a_in, a_out)

    def lit(self, t: float) -> float:
        """Hub brightening, peaking while the pill sits on it."""
        return pulse(t, self.t1 - 0.3, 0.35, self.settle - 0.05, 0.45)

    def swap(self, t: float) -> float:
        """0 to 1 while settled on the hub (used to change a lookup's label)."""
        return brand.ease_in_out_sine(brand.progress(t, self.t1 + 0.08, self.settle - 0.16))

    def _leg_time_at(self, frac: float) -> float:
        """Fraction of a leg (0..1) at which ease_in_out_sine progress reaches frac."""
        frac = min(1.0, max(0.0, frac))
        return math.acos(1.0 - 2.0 * frac) / math.pi

    def hub_text(self, t: float, pill_w: float, text_w: float, fade_s: float = 0.3) -> float:
        """Alpha for the hub's centered label. It fades out so it is gone just before the
        pill reaches it, and comes back once the pill has cleared it, so no clipped
        letters ever peek around the pill."""
        touch = (pill_w + text_w) / 2 + 6
        d1 = abs(self.x_from - self.x_hub)
        d2 = abs(self.x_to - self.x_hub)
        t_in = self.t0 + self.leg * self._leg_time_at(1.0 - touch / d1) if d1 > touch else self.t0
        t_clear = self.t2 + self.leg * self._leg_time_at(touch / d2) if d2 > touch else self.t3
        k_out = brand.ease_in_out_sine(brand.progress(t, t_in - fade_s, fade_s))
        k_back = brand.ease_in_out_sine(brand.progress(t, t_clear, fade_s))
        return 1.0 - k_out * (1.0 - k_back)


def draw_route(canvas, spr: Sprite, route: Route, t: float, y: float, alpha: float = 1.0):
    a = route.alpha(t) * alpha
    if a > 0:
        blit(canvas, spr, route.x(t), y, a)


def pulse(t: float, start: float, rise: float, hold: float, fall: float) -> float:
    """0 -> 1 -> 0 envelope with sine easing."""
    if t <= start or t >= start + rise + hold + fall:
        return 0.0
    if t < start + rise:
        return brand.ease_in_out_sine((t - start) / rise)
    if t < start + rise + hold:
        return 1.0
    return 1.0 - brand.ease_in_out_sine((t - start - rise - hold) / fall)


# Shared pill and chip sprites. Moving pills: 34 px semibold white on blue, 60 px tall.

PILL_SIZE = 34
PILL_H = 60


def _icon(kind: str):
    if kind == "check":
        return brand.check_sprite(32, "white")
    if kind == "search":
        return gfx.magnifier(30, "white")
    return brand.envelope_sprite(34, "white")


def message_pill(label: str, icon: str = "envelope", min_w: float = 0.0) -> Sprite:
    """Moving message pill: white envelope (or other icon) and white label on blue,
    with a thin white edge so it stays crisp on top of the navy and teal nodes."""
    return gfx.pill(label, PILL_SIZE, 600, "white", "blue", icon=_icon(icon), outline="white",
                    outline_w=2.5, h=PILL_H, pad_x=24, gap=12, shadow_opacity=0.5, min_w=min_w)


def swap_pill(items: list[tuple[str, str]]):
    """One pill body sized for the widest of several (label, icon) contents, so the
    label can change while the pill sits still. Returns (body, [contents])."""
    widths = [brand.text_width(label, PILL_SIZE, 600) + _icon(icon).width + 12 for label, icon in items]
    min_w = max(widths) + 2 * 24
    body = None
    contents = []
    for label, icon in items:
        b, c = gfx.pill_parts(label, PILL_SIZE, 600, "white", "blue", icon=_icon(icon), outline="white",
                              outline_w=2.5, h=PILL_H, pad_x=24, gap=12, shadow_opacity=0.5, min_w=min_w)
        body = body or b
        contents.append(c)
    return body, contents


def received_chip() -> Sprite:
    return gfx.pill("Received", 32, 600, "teal_ink", "teal", icon=brand.check_sprite(30, "teal_ink"),
                    outline="#bfdfe7", outline_w=2, h=58, pad_x=22, gap=10)
