"""Frame review helper for the Alice and Bob recordings (read only on the sources).

  python3 frames.py sheet SOURCE OUT.png COLS WIDTH T1 T2 ...   labeled contact sheet
  python3 frames.py grab SOURCE OUT.png T [x y w h]              full-res frame, optional crop, pixel grid
"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CAP = Path(__file__).resolve().parents[2] / "captures"
FONT = Path(__file__).resolve().parents[1] / "production/assets/fonts/Inter-Variable.ttf"


def frame(src, t):
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(CAP / src),
                        "-frames:v", "1", tmp.name], check=True)
        return Image.open(tmp.name).convert("RGB")


def sheet(src, out, cols, width, times):
    font = ImageFont.truetype(str(FONT), 22)
    tiles = []
    for t in times:
        im = frame(src, t)
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.Resampling.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 118, 30), fill=(0, 20, 43))
        d.text((8, 3), f"{t:.2f}s", font=font, fill="white")
        tiles.append(im)
    rows = (len(tiles) + cols - 1) // cols
    th = tiles[0].height
    out_im = Image.new("RGB", (cols * width + (cols - 1) * 6, rows * th + (rows - 1) * 6), "white")
    for i, im in enumerate(tiles):
        out_im.paste(im, ((i % cols) * (width + 6), (i // cols) * (th + 6)))
    out_im.save(out)


def grab(src, out, t, box=None):
    im = frame(src, t)
    if box:
        x, y, w, h = box
        im = im.crop((x, y, x + w, y + h))
        ox, oy = x, y
    else:
        ox = oy = 0
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(str(FONT), 18)
    step = 100
    for gx in range((ox // step + 1) * step, ox + im.width, step):
        d.line((gx - ox, 0, gx - ox, 8), fill=(255, 0, 0)); d.text((gx - ox + 2, 8), str(gx), font=font, fill=(255, 0, 0))
    for gy in range((oy // step + 1) * step, oy + im.height, step):
        d.line((0, gy - oy, 8, gy - oy), fill=(255, 0, 0)); d.text((10, gy - oy - 9), str(gy), font=font, fill=(255, 0, 0))
    im.save(out)


if __name__ == "__main__":
    mode, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "sheet":
        sheet(src, out, int(sys.argv[4]), int(sys.argv[5]), [float(t) for t in sys.argv[6:]])
    else:
        t = float(sys.argv[4])
        box = [int(v) for v in sys.argv[5:9]] if len(sys.argv) >= 9 else None
        grab(src, out, t, box)


def strip(src, out, box, times, scale=0.5, cols=2, label=""):
    """Crop the same box from several times and tile them, labeled with the time."""
    font = ImageFont.truetype(str(FONT), 20)
    tiles = []
    for t in times:
        im = frame(src, t).crop(box)
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.Resampling.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 92, 24), fill=(200, 0, 0)); d.text((4, 1), f"{t}", font=font, fill="white")
        tiles.append(im)
    w, h = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    s = Image.new("RGB", (cols * (w + 4), rows * (h + 4)), "white")
    for i, im in enumerate(tiles):
        s.paste(im, ((i % cols) * (w + 4), (i // cols) * (h + 4)))
    s.save(out)
    return out
