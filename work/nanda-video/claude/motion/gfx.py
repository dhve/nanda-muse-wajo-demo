"""Sprite factories for the motion scenes. All text and colors come from lib/brand.py.

Vector shapes are drawn at 4x and reduced with Lanczos for clean edges. Every
factory returns an engine.Sprite with a meaningful anchor (documented per call).
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from engine import Sprite, brand

SS = 4
LANCZOS = Image.Resampling.LANCZOS


def _c(color, alpha: float = 1.0):
    if isinstance(color, tuple):
        return color if len(color) == 4 else (*color, round(alpha * 255))
    return brand.rgba(color, alpha)


# Text.

def text(s: str, size: float, weight: int = 400, color="navy", tracking: float = 0.0,
         align: str = "l", alpha: float = 1.0) -> Sprite:
    """One line of text. Anchor: baseline, at the left, middle or right of the advance."""
    img, baseline = brand.text_image(s, size, weight, color, tracking, alpha)
    pad = math.ceil(size * 0.08)
    width = brand.text_width(s, size, weight, tracking)
    ox = pad + {"l": 0.0, "m": width / 2, "r": width}[align]
    return Sprite(img, ox, baseline, width)


def rich(s: str, size: float, weight: int = 400, color="navy", tracking: float = 0.0,
         align: str = "l", arrow_color=None) -> Sprite:
    """Text where U+2192, U+2190 and U+2194 become vector arrows. Anchor as text()."""
    img, baseline = brand.rich_text_image(s, size, weight, color, tracking, arrow_color)
    pad = math.ceil(size * 0.08)
    width = img.width - 2 * pad
    ox = pad + {"l": 0.0, "m": width / 2, "r": width}[align]
    return Sprite(img, ox, baseline, width)


# Boxes, shadows, rings.

def box_image(w: int, h: int, radius: float, fill, outline=None, outline_w: float = brand.BORDER_W) -> Image.Image:
    return brand.rounded_box(int(w), int(h), radius, _c(fill), _c(outline) if outline else None, outline_w)


def box(w: int, h: int, radius: float = brand.RADIUS_CARD, fill="surface_light", outline="line",
        outline_w: float = brand.BORDER_W) -> Sprite:
    """Rounded box. Anchor: top left corner."""
    return Sprite(box_image(w, h, radius, fill, outline, outline_w))


def shadow(w: int, h: int, radius: float = brand.RADIUS_CARD, blur: float = 16, opacity: float = 0.5,
           dy: float = 10, color="shadow") -> Sprite:
    """Soft shadow for a w x h box. Anchor: the box's top left corner (offset dy is built in)."""
    img, m = brand.soft_shadow(int(w), int(h), radius, blur=blur, color=color, opacity=opacity)
    return Sprite(img, m, m - dy)


def stretch_v(tall: Sprite, inner_h_tall: int, inner_h: int) -> Sprite:
    """Build a shorter version of a vertically uniform sprite (box or shadow) by
    joining its top and bottom halves. inner_h_tall is the box height the tall
    sprite was made for; inner_h is the new box height. The anchor is kept."""
    extra = tall.h - inner_h_tall
    total = int(inner_h) + extra
    if total >= tall.h:
        return tall
    top = total // 2
    bot = total - top
    pm = np.concatenate([tall.pm[:top], tall.pm[tall.h - bot:]], axis=0)
    return Sprite(np.ascontiguousarray(pm), tall.ox, tall.oy, tall.adv)


def ring(w: float, h: float, radius: float, stroke: float = 3.0, color="blue", alpha: float = 1.0) -> Sprite:
    """Rounded outline of outer size w x h. Anchor: top left corner."""
    wi, hi = math.ceil(w), math.ceil(h)
    big = Image.new("RGBA", (wi * SS, hi * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=radius * SS, outline=_c(color, alpha),
                        width=round(stroke * SS))
    return Sprite(big.resize((wi, hi), LANCZOS))


def circle(d: float, fill="brand_200", outline=None, outline_w: float = 2.0) -> Image.Image:
    n = math.ceil(d)
    big = Image.new("RGBA", (n * SS, n * SS), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    if outline:
        dr.ellipse((0, 0, d * SS - 1, d * SS - 1), fill=_c(outline))
        inset = outline_w * SS
        dr.ellipse((inset, inset, d * SS - 1 - inset, d * SS - 1 - inset), fill=_c(fill))
    else:
        dr.ellipse((0, 0, d * SS - 1, d * SS - 1), fill=_c(fill))
    return big.resize((n, n), LANCZOS)


def number_circle(d: float, numeral: str, size: float, fill="brand_200", ink="brand_600",
                  weight: int = 600, outline=None) -> Sprite:
    """Numbered circle like the guide's step number. Anchor: center."""
    img = circle(d, fill, outline)
    dr = ImageDraw.Draw(img)
    brand.draw_text(dr, d / 2, d / 2, numeral, size, weight, _c(ink), 0.0, "mc")
    return Sprite(img, d / 2, d / 2)


# Lines and arrowheads.

def hline(length: float, thick: float = 4.0, color="teal_ink", dash: float | None = None,
          gap: float = 12.0, alpha: float = 1.0) -> Sprite:
    """Horizontal line with round caps, solid or dashed. Dashes are spread so the
    line starts and ends on a dash. Anchor: left end, vertical center."""
    pad = 2
    w = math.ceil(length) + 2 * pad
    h = math.ceil(thick) + 2 * pad
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = _c(color, alpha)
    cy = h * SS / 2
    r = thick * SS / 2
    if dash:
        n = max(1, int((length + gap) // (dash + gap)))
        g = (length - n * dash) / (n - 1) if n > 1 else 0.0
        for i in range(n):
            x0 = (pad + i * (dash + g)) * SS
            d.rounded_rectangle((x0, cy - r, x0 + dash * SS, cy + r), radius=r, fill=c)
    else:
        d.rounded_rectangle((pad * SS, cy - r, (pad + length) * SS, cy + r), radius=r, fill=c)
    return Sprite(big.resize((w, h), LANCZOS), pad, h / 2)


def chevron(size: float = 15.0, thick: float = 4.0, color="blue", direction: str = "right",
            alpha: float = 1.0) -> Sprite:
    """Open arrowhead. Anchor: the tip. size is the half height of the head."""
    dx = size * 0.8
    pad = thick
    w = math.ceil(dx + 2 * pad)
    h = math.ceil(2 * size + 2 * pad)
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = _c(color, alpha)
    s = thick * SS
    cy = h * SS / 2
    if direction == "right":
        tip = (w - pad) * SS
        pts = [(tip - dx * SS, cy - size * SS), (tip, cy), (tip - dx * SS, cy + size * SS)]
    else:
        tip = pad * SS
        pts = [(tip + dx * SS, cy - size * SS), (tip, cy), (tip + dx * SS, cy + size * SS)]
    d.line(pts, fill=c, width=round(s), joint="curve")
    for px, py in pts:
        d.ellipse((px - s / 2, py - s / 2, px + s / 2, py + s / 2), fill=c)
    img = big.resize((w, h), LANCZOS)
    return Sprite(img, (w - pad) if direction == "right" else pad, h / 2)


# Icons (beyond brand.py's arrow, check and envelope).

def magnifier(size: float = 30.0, color="brand_600", stroke: float | None = None) -> Image.Image:
    n = math.ceil(size)
    stroke = stroke or max(2.0, size * 0.11)
    big = Image.new("RGBA", (n * SS, n * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = _c(color)
    s = stroke * SS
    cx = cy = 0.41 * n * SS
    r = 0.30 * n * SS
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=round(s))
    a = (cx + r * 0.72, cy + r * 0.72)
    b = (0.88 * n * SS, 0.88 * n * SS)
    d.line([a, b], fill=c, width=round(s * 1.15))
    for px, py in (a, b):
        d.ellipse((px - s * 0.58, py - s * 0.58, px + s * 0.58, py + s * 0.58), fill=c)
    return big.resize((n, n), LANCZOS)


# Pills and chips.

def pill_parts(label: str, size: float = 32, weight: int = 600, fg="white", bg="blue",
               icon: Image.Image | None = None, outline=None, outline_w: float = 2.0, h: float = 60,
               pad_x: float = 24, gap: float = 12, radius: float | None = None, shadow_opacity: float = 0.0,
               icon_dy: float = 0.0, min_w: float = 0.0) -> tuple[Sprite, Sprite]:
    """A pill as two sprites, both anchored at the center of the body: the body (with
    its optional soft shadow) and the content (icon plus label, centered). Splitting
    them lets a pill change its label without the body blinking."""
    m = brand.metrics(size, weight)
    label_w = brand.text_width(label, size, weight)
    icon_w = (icon.width + gap) if icon is not None else 0
    content_w = icon_w + label_w
    w = math.ceil(max(2 * pad_x + content_w, min_w))
    w += w % 2
    hi = math.ceil(h)
    radius = hi / 2 if radius is None else radius
    body = box_image(w, hi, radius, bg, outline, outline_w)
    margin = 0
    if shadow_opacity > 0:
        sh, margin = brand.soft_shadow(w, hi, radius, blur=10, opacity=shadow_opacity)
        body_img = Image.new("RGBA", sh.size, (0, 0, 0, 0))
        body_img.alpha_composite(sh, (0, 5))
    else:
        body_img = Image.new("RGBA", (w, hi), (0, 0, 0, 0))
    body_img.alpha_composite(body, (margin, margin))
    content = Image.new("RGBA", (w, hi), (0, 0, 0, 0))
    x = (w - content_w) / 2
    if icon is not None:
        content.alpha_composite(icon, (round(x), round((hi - icon.height) / 2 + icon_dy)))
        x += icon_w
    brand.draw_text(ImageDraw.Draw(content), x, hi / 2 + m["cap"] / 2, label, size, weight, _c(fg), 0.0, "ls")
    return (Sprite(body_img, margin + w // 2, margin + hi // 2, w), Sprite(content, w // 2, hi // 2, w))


def pill(label: str, size: float = 32, weight: int = 600, fg="white", bg="blue", icon: Image.Image | None = None,
         outline=None, outline_w: float = 2.0, h: float = 60, pad_x: float = 24, gap: float = 12,
         radius: float | None = None, shadow_opacity: float = 0.0, icon_dy: float = 0.0,
         min_w: float = 0.0) -> Sprite:
    """Pill with an optional leading icon. Anchor: center of the pill body.
    With shadow_opacity > 0 a soft shadow is baked in below the body."""
    body, content = pill_parts(label, size, weight, fg, bg, icon, outline, outline_w, h, pad_x, gap, radius,
                               shadow_opacity, icon_dy, min_w)
    out = body.pm.copy()
    ox, oy = round(body.ox - content.ox), round(body.oy - content.oy)
    region = out[oy:oy + content.h, ox:ox + content.w]
    region *= 1.0 - content.pm[..., 3:4]
    region += content.pm
    return Sprite(out, body.ox, body.oy, body.adv)
