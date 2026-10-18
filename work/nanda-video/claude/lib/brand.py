"""Shared brand tokens and drawing helpers for the Muse and Wajo demo video.

Palette and type follow the demo guide (outputs/nanda-demo/index.html), which
uses the NANDA Index theme. Both the motion renderer (motion/) and the edit
pipeline (edit/) import this module so every frame uses the same colors, font,
kerning and chip style.

Text is shaped with HarfBuzz (the hb-shape CLI) so Inter gets its real GPOS
kerning, then drawn glyph by glyph with Pillow at sub-pixel positions. If
hb-shape is missing, layout falls back to plain Pillow advances.

The font file has no arrow or check mark glyphs, so those are drawn as vector
shapes. Use rich_text_image() for strings such as "Wajo -> Muse" written with
the Unicode arrows (U+2192, U+2190, U+2194).

Only Pillow and numpy are required. No browser rendering.
"""

from __future__ import annotations

import functools
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent  # .../nanda-video/claude
FONT_TTF = ROOT / "assets" / "fonts" / "Inter-Variable.ttf"
FONT_WOFF2 = ROOT.parent.parent.parent / "outputs" / "nanda-demo" / "fonts" / "inter-latin.woff2"

# Video format shared by every asset.
W, H, FPS = 1920, 1080, 30

# Color tokens. The first three are the primary palette for this video.
COLORS = {
    "surface": "#f5f8fd",          # pale blue page background
    "navy": "#00142b",             # headline ink (guide --color-ink-strong)
    "blue": "#187adc",             # brand accent (guide --color-brand-500)
    "surface_light": "#fbfcfe",    # card fill
    "surface_strong": "#eff3fc",   # quiet panel fill
    "surface_tag": "#e3eafa",      # tag fill
    "ink": "#3c4551",              # body text
    "ink_medium": "#59616b",       # secondary text
    "ink_weak": "#777d85",         # eyebrow text (use at 30px or larger)
    "line": "#d5dff7",             # hairlines and card borders
    "line_strong": "#c8d5f5",
    "brand_200": "#e8f1ff",        # step number circle fill
    "brand_600": "#0051af",        # step number ink, links
    "brand_700": "#004ba8",
    "brand_800": "#0d274d",        # NANDA Index node fill
    "teal": "#dff1f5",             # Agent Box delivery fill
    "teal_ink": "#0f6e85",         # Agent Box delivery ink
    "white": "#ffffff",
    "shadow": "#c8d5f5",           # card shadow tint (guide uses rgba(200,213,245,.33))
}

# Type scale at 1920x1080. Sizes are pixels. Nothing on screen goes below MIN_TEXT_PX.
TYPE = {
    "display": {"size": 104, "weight": 600, "tracking": -0.02},
    "title": {"size": 84, "weight": 600, "tracking": -0.015},
    "heading": {"size": 60, "weight": 600, "tracking": -0.01},
    "subhead": {"size": 46, "weight": 500, "tracking": -0.005},
    "body": {"size": 40, "weight": 400, "tracking": 0.0},
    "label": {"size": 32, "weight": 600, "tracking": 0.01},
    "caption": {"size": 40, "weight": 500, "tracking": 0.0},
}
MIN_TEXT_PX = 28

# Layout and motion tokens.
SAFE_X, SAFE_Y = 120, 84           # keep text inside this margin
RADIUS_CARD = 20                   # guide uses 8px at 16px body; scaled for video
RADIUS_CONTROL = 12
BORDER_W = 2
ENTER_S = 0.6                      # fade and rise duration for an entering element
RISE_PX = 18                       # entering elements rise this far
STAGGER_S = 0.12


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb(name: str) -> tuple[int, int, int]:
    return hex_rgb(COLORS.get(name, name))


def rgba(name: str, alpha: float = 1.0) -> tuple[int, int, int, int]:
    r, g, b = rgb(name)
    return (r, g, b, max(0, min(255, round(alpha * 255))))


# Easing. All motion should use these curves. No bounce, no overshoot.

def clamp01(t: float) -> float:
    return 0.0 if t <= 0 else 1.0 if t >= 1 else t


def ease_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_in_cubic(t: float) -> float:
    t = clamp01(t)
    return t ** 3


def ease_in_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_in_out_sine(t: float) -> float:
    t = clamp01(t)
    return -(math.cos(math.pi * t) - 1) / 2


def progress(t: float, start: float, duration: float) -> float:
    """Linear 0..1 progress of time t through [start, start + duration]."""
    if duration <= 0:
        return 1.0 if t >= start else 0.0
    return clamp01((t - start) / duration)


# Fonts and shaping.

def font_path() -> Path:
    return FONT_TTF if FONT_TTF.exists() else FONT_WOFF2


@functools.lru_cache(maxsize=256)
def get_font(size: float, weight: int = 400) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(font_path()), size, layout_engine=ImageFont.Layout.BASIC)
    try:
        font.set_variation_by_axes([float(weight)])
    except Exception:
        pass
    return font


_HB_SHAPE = shutil.which("hb-shape")


@functools.lru_cache(maxsize=4096)
def _shape_units(text: str, weight: int) -> tuple[tuple[str, float, float, float], ...]:
    """Shape text at 1000 units per em. Returns (chars, x_advance, x_offset, y_offset)
    per cluster, with kerning applied."""
    if not text:
        return ()
    if _HB_SHAPE and FONT_TTF.exists():
        try:
            out = subprocess.run(
                [_HB_SHAPE, f"--font-file={FONT_TTF}", "--font-size=1000",
                 f"--variations=wght={weight}", "--features=-calt",
                 "--output-format=json", "--no-glyph-names"],
                input=text, capture_output=True, text=True, check=True, timeout=20,
            ).stdout
            glyphs = json.loads(out.strip().splitlines()[0])
            clusters: list[list] = []
            for g in glyphs:
                cl = g["cl"]
                if clusters and clusters[-1][0] == cl:
                    clusters[-1][1] += g["ax"]
                else:
                    clusters.append([cl, float(g["ax"]), float(g.get("dx", 0)), float(g.get("dy", 0))])
            result = []
            for i, (cl, ax, dx, dy) in enumerate(clusters):
                end = clusters[i + 1][0] if i + 1 < len(clusters) else len(text)
                result.append((text[cl:end], ax, dx, dy))
            return tuple(result)
        except Exception:
            pass
    font = get_font(1000, weight)
    return tuple((ch, float(font.getlength(ch)), 0.0, 0.0) for ch in text)


def layout(text: str, size: float, weight: int = 400, tracking: float = 0.0):
    """Glyph positions for one line. tracking is in em (e.g. -0.01).

    Returns (positions, width) where positions is a list of (chars, x, y_offset)
    in pixels relative to the pen start on the baseline."""
    scale = size / 1000.0
    track_px = tracking * size
    x = 0.0
    positions = []
    shaped = _shape_units(text, int(weight))
    for i, (chars, ax, dx, dy) in enumerate(shaped):
        positions.append((chars, x + dx * scale, -dy * scale))
        x += ax * scale
        if i < len(shaped) - 1:
            x += track_px
    return positions, x


def text_width(text: str, size: float, weight: int = 400, tracking: float = 0.0) -> float:
    return layout(text, size, weight, tracking)[1]


def metrics(size: float, weight: int = 400) -> dict:
    """Vertical metrics in pixels: ascent, descent (positive), cap height, x height."""
    font = get_font(size, weight)
    ascent, descent = font.getmetrics()
    cap = -font.getbbox("H", anchor="ls")[1]
    xh = -font.getbbox("x", anchor="ls")[1]
    return {"ascent": ascent, "descent": descent, "cap": cap, "x": xh}


def draw_text(draw: ImageDraw.ImageDraw, x: float, y: float, text: str, size: float,
              weight: int = 400, fill=(0, 0, 0, 255), tracking: float = 0.0,
              anchor: str = "ls") -> tuple[float, float, float, float]:
    """Draw one line with kerning. Anchor: first letter l/m/r (left, middle, right),
    second letter s/c/t (baseline, cap middle, cap top). Returns the box
    (x0, cap_top, x1, baseline)."""
    font = get_font(size, weight)
    positions, width = layout(text, size, weight, tracking)
    m = metrics(size, weight)
    h_anchor, v_anchor = anchor[0], anchor[1]
    x0 = x - (width / 2 if h_anchor == "m" else width if h_anchor == "r" else 0)
    if v_anchor == "c":
        base = y + m["cap"] / 2
    elif v_anchor == "t":
        base = y + m["cap"]
    else:
        base = y
    if isinstance(fill, str):
        fill = rgba(fill)
    for chars, px, py in positions:
        if chars.strip():
            draw.text((x0 + px, base + py), chars, font=font, fill=fill, anchor="ls")
    return (x0, base - m["cap"], x0 + width, base)


@functools.lru_cache(maxsize=512)
def text_image(text: str, size: float, weight: int = 400, color: str = "navy",
               tracking: float = 0.0, alpha: float = 1.0) -> tuple[Image.Image, float]:
    """One line of text on a transparent RGBA sprite.

    Returns (image, baseline_y). The sprite spans the full ascent and descent, and its
    width is the shaped advance plus a small pad. Treat the result as read-only (cached)."""
    m = metrics(size, weight)
    pad = math.ceil(size * 0.08)
    width = text_width(text, size, weight, tracking)
    img = Image.new("RGBA", (math.ceil(width) + 2 * pad, m["ascent"] + m["descent"] + 2 * pad), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    baseline = pad + m["ascent"]
    draw_text(draw, pad, baseline, text, size, weight, rgba(color, alpha), tracking, "ls")
    return img, float(baseline)


# Vector shapes. Draw at 4x and reduce for clean anti-aliased edges.

SS = 4


def _reduce(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    return img.resize(size, Image.Resampling.LANCZOS)


def rounded_box(w: int, h: int, radius: float, fill="surface_light", outline=None,
                outline_w: float = BORDER_W) -> Image.Image:
    """Anti-aliased rounded rectangle sprite (RGBA, exactly w x h)."""
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    fill_c = rgba(fill) if isinstance(fill, str) else fill
    if outline:
        out_c = rgba(outline) if isinstance(outline, str) else outline
        d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=radius * SS, fill=out_c)
        inset = outline_w * SS
        d.rounded_rectangle((inset, inset, w * SS - 1 - inset, h * SS - 1 - inset),
                            radius=max(0, (radius - outline_w) * SS), fill=fill_c)
    else:
        d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=radius * SS, fill=fill_c)
    return _reduce(big, (w, h))


def soft_shadow(w: int, h: int, radius: float, blur: float = 18, color: str = "shadow",
                opacity: float = 0.55, spread: int = 0) -> tuple[Image.Image, int]:
    """Blurred shadow sprite for a w x h rounded box. Returns (sprite, margin).
    Paste the sprite at (box_x - margin, box_y - margin + y_offset)."""
    margin = math.ceil(blur * 3) + spread
    img = Image.new("RGBA", (w + 2 * margin, h + 2 * margin), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((margin - spread, margin - spread, margin + w + spread, margin + h + spread),
                        radius=radius + spread, fill=rgba(color, opacity))
    return img.filter(ImageFilter.GaussianBlur(blur)), margin


def arrow_sprite(length: float, size: float, color: str = "navy", direction: str = "right",
                 stroke: float | None = None, alpha: float = 1.0) -> Image.Image:
    """Vector arrow sized to sit inline with text of the given font size.
    direction: right, left, or both."""
    stroke = stroke or max(2.0, size * 0.075)
    head = size * 0.26
    h = math.ceil(head * 2 + stroke * 2)
    w = math.ceil(length)
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = rgba(color, alpha)
    cy = h * SS / 2
    s = stroke * SS
    hd = head * SS
    x0, x1 = s / 2, w * SS - s / 2
    d.line((x0 + (hd * 0.4 if direction in ("left", "both") else 0), cy,
            x1 - (hd * 0.4 if direction in ("right", "both") else 0), cy), fill=c, width=round(s))
    def chevron(tip_x: float, sign: int):
        pts = [(tip_x - sign * hd, cy - hd), (tip_x, cy), (tip_x - sign * hd, cy + hd)]
        d.line(pts, fill=c, width=round(s), joint="curve")
        for px, py in (pts[0], pts[2]):
            d.ellipse((px - s / 2, py - s / 2, px + s / 2, py + s / 2), fill=c)
        d.ellipse((tip_x - s / 2, cy - s / 2, tip_x + s / 2, cy + s / 2), fill=c)
    if direction in ("right", "both"):
        chevron(x1, 1)
    if direction in ("left", "both"):
        chevron(x0, -1)
    return _reduce(big, (w, h))


def check_sprite(size: float, color: str = "teal_ink", stroke: float | None = None,
                 alpha: float = 1.0) -> Image.Image:
    """Vector check mark inside a size x size box."""
    stroke = stroke or max(2.0, size * 0.12)
    n = math.ceil(size)
    big = Image.new("RGBA", (n * SS, n * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = rgba(color, alpha)
    s = stroke * SS
    pts = [(0.18 * n * SS, 0.53 * n * SS), (0.41 * n * SS, 0.75 * n * SS), (0.82 * n * SS, 0.28 * n * SS)]
    d.line(pts, fill=c, width=round(s), joint="curve")
    for px, py in (pts[0], pts[2]):
        d.ellipse((px - s / 2, py - s / 2, px + s / 2, py + s / 2), fill=c)
    return _reduce(big, (n, n))


def envelope_sprite(width: float, color: str = "white", stroke: float | None = None,
                    alpha: float = 1.0) -> Image.Image:
    """Outline envelope icon, width x (0.72 * width)."""
    w = math.ceil(width)
    h = math.ceil(width * 0.72)
    stroke = stroke or max(2.0, width * 0.085)
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = rgba(color, alpha)
    s = stroke * SS
    inset = s / 2
    d.rounded_rectangle((inset, inset, w * SS - inset, h * SS - inset), radius=w * SS * 0.1,
                        outline=c, width=round(s))
    d.line([(inset + s * 0.6, inset + s * 0.9), (w * SS / 2, h * SS * 0.56),
            (w * SS - inset - s * 0.6, inset + s * 0.9)], fill=c, width=round(s), joint="curve")
    return _reduce(big, (w, h))


def rich_text_image(text: str, size: float, weight: int = 400, color: str = "navy",
                    tracking: float = 0.0, arrow_color: str | None = None,
                    alpha: float = 1.0) -> tuple[Image.Image, float]:
    """Like text_image, but U+2192, U+2190 and U+2194 become vector arrows."""
    arrows = {"→": "right", "←": "left", "↔": "both"}
    parts: list[tuple[str, str]] = []
    buf = ""
    for ch in text:
        if ch in arrows:
            if buf:
                parts.append(("text", buf))
                buf = ""
            parts.append(("arrow", arrows[ch]))
        else:
            buf += ch
    if buf:
        parts.append(("text", buf))
    m = metrics(size, weight)
    pad = math.ceil(size * 0.08)
    arrow_len = size * 0.95
    gap = size * 0.12
    pieces = []
    total = 0.0
    for kind, value in parts:
        if kind == "text":
            wpx = text_width(value, size, weight, tracking)
            pieces.append((kind, value, total))
            total += wpx
        else:
            total += gap
            pieces.append((kind, value, total))
            total += arrow_len + gap
    img = Image.new("RGBA", (math.ceil(total) + 2 * pad, m["ascent"] + m["descent"] + 2 * pad), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    baseline = pad + m["ascent"]
    for kind, value, x in pieces:
        if kind == "text":
            draw_text(draw, pad + x, baseline, value, size, weight, rgba(color, alpha), tracking, "ls")
        else:
            spr = arrow_sprite(arrow_len, size, arrow_color or color, value, alpha=alpha)
            cy = baseline - m["cap"] / 2
            img.alpha_composite(spr, (round(pad + x), round(cy - spr.height / 2)))
    return img, float(baseline)


def chip(text: str, size: float = 32, weight: int = 600, fg: str = "white", bg: str = "navy",
         pad_x: float | None = None, pad_y: float | None = None, radius: float | None = None,
         outline: str | None = None, bg_alpha: float = 1.0, icon: Image.Image | None = None,
         shadow: bool = True) -> Image.Image:
    """Pill label used for callouts on captured footage, e.g. "Wajo -> Muse".
    Returns an RGBA sprite that includes its own soft shadow margin."""
    label, baseline = rich_text_image(text, size, weight, fg)
    m = metrics(size, weight)
    pad_x = pad_x if pad_x is not None else size * 0.75
    pad_y = pad_y if pad_y is not None else size * 0.5
    icon_w = (icon.width + size * 0.4) if icon else 0
    inner_w = label.width - 2 * math.ceil(size * 0.08) + icon_w
    w = math.ceil(inner_w + 2 * pad_x)
    h = math.ceil(m["cap"] + 2 * pad_y)
    radius = radius if radius is not None else h / 2
    bg_c = rgba(bg, bg_alpha)
    box = rounded_box(w, h, radius, bg_c, outline)
    margin = 0
    if shadow:
        sh, margin = soft_shadow(w, h, radius, blur=14, opacity=0.6)
        out = Image.new("RGBA", sh.size, (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 6))
    else:
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(box, (margin, margin))
    x = margin + pad_x
    if icon:
        out.alpha_composite(icon, (round(x), round(margin + (h - icon.height) / 2)))
        x += icon_w
    text_top = margin + pad_y + m["cap"] - baseline  # place baseline at cap bottom
    out.alpha_composite(label, (round(x - math.ceil(size * 0.08)), round(text_top)))
    return out


def canvas(color: str = "surface") -> Image.Image:
    """Full-frame RGBA canvas in a brand color."""
    return Image.new("RGBA", (W, H), rgba(color))


def specimen(path: Path) -> Path:
    """Render a quick visual check of type, colors and chips."""
    img = canvas()
    d = ImageDraw.Draw(img)
    y = 170
    for key in ("display", "title", "heading", "subhead", "body", "label"):
        t = TYPE[key]
        draw_text(d, SAFE_X, y, f"{key} {t['size']}px  Wajo To Muse AV", t["size"], t["weight"],
                  "navy", t["tracking"])
        y += t["size"] * 1.45
    x = SAFE_X
    for name in ("surface", "navy", "blue", "brand_800", "brand_200", "teal", "teal_ink", "line"):
        img.alpha_composite(rounded_box(150, 90, RADIUS_CONTROL, name, "line"), (x, 860))
        draw_text(d, x, 990, name, 28, 500, "ink_medium")
        x += 190
    img.alpha_composite(chip("Wajo → Muse", 34), (1240, 690))
    img.alpha_composite(chip("Agent Box delivery", 34, fg="teal_ink", bg="teal", shadow=False), (1240, 790))
    img.alpha_composite(arrow_sprite(160, 60, "blue", "both"), (1650, 150))
    img.alpha_composite(check_sprite(80, "teal_ink"), (1700, 260))
    img.alpha_composite(envelope_sprite(80, "blue"), (1700, 380))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path)
    return path


if __name__ == "__main__":
    print(specimen(ROOT / "build" / "brand_specimen.png"))
