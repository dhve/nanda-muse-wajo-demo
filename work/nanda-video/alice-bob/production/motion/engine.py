"""Frame compositing and encoding for the motion scenes.

Sprites are premultiplied float32 RGBA numpy arrays. A frame is a float32 RGB
array that starts as the flat surface color. Sprites are placed with a bilinear
sub-pixel shift, so slow eases never step by whole pixels.

Frames are rendered in a pool of worker processes and piped as rgb24 into
ffmpeg (libx264, BT.709, exact frame count). Frames after a scene's settle time
are identical, so they are rendered once and repeated.
"""

from __future__ import annotations

import math
import multiprocessing as mp
import os
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT / "lib") not in sys.path:
    sys.path.insert(0, str(ROOT / "lib"))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import brand  # noqa: E402

W, H, FPS = brand.W, brand.H, brand.FPS


# Sprites and compositing.

class Sprite:
    """Premultiplied RGBA sprite with an anchor point (ox, oy) in sprite pixels.

    blit(canvas, sprite, x, y) puts the anchor at canvas position (x, y)."""

    __slots__ = ("pm", "w", "h", "ox", "oy", "adv")

    def __init__(self, img, ox: float = 0.0, oy: float = 0.0, adv: float = 0.0):
        if isinstance(img, Image.Image):
            arr = np.asarray(img.convert("RGBA"), dtype=np.float32) * (1.0 / 255.0)
            arr[..., :3] *= arr[..., 3:4]
            self.pm = np.ascontiguousarray(arr)
        else:
            self.pm = img
        self.h, self.w = self.pm.shape[:2]
        self.ox, self.oy = float(ox), float(oy)
        self.adv = float(adv)

    def with_anchor(self, ox: float, oy: float) -> "Sprite":
        s = Sprite(self.pm, ox, oy, self.adv)
        return s


def _shifted(pm: np.ndarray, fx: float, fy: float) -> np.ndarray:
    """Bilinear sub-pixel shift of a premultiplied sprite by (fx, fy) in [0, 1)."""
    h, w = pm.shape[:2]
    sx = fx > 1e-3
    sy = fy > 1e-3
    if not sx and not sy:
        return pm
    if sx and not sy:
        out = np.zeros((h, w + 1, 4), np.float32)
        out[:, :w] = pm * (1.0 - fx)
        out[:, 1:] += pm * fx
        return out
    if sy and not sx:
        out = np.zeros((h + 1, w, 4), np.float32)
        out[:h] = pm * (1.0 - fy)
        out[1:] += pm * fy
        return out
    out = np.zeros((h + 1, w + 1, 4), np.float32)
    out[:h, :w] = pm * ((1.0 - fx) * (1.0 - fy))
    out[:h, 1:] += pm * (fx * (1.0 - fy))
    out[1:, :w] += pm * ((1.0 - fx) * fy)
    out[1:, 1:] += pm * (fx * fy)
    return out


def blit(canvas: np.ndarray, spr: Sprite, x: float, y: float, alpha: float = 1.0) -> None:
    """Composite a sprite (source over) with its anchor at (x, y)."""
    if spr is None or alpha <= 0.002:
        return
    X = x - spr.ox
    Y = y - spr.oy
    ix = math.floor(X)
    iy = math.floor(Y)
    src = _shifted(spr.pm, X - ix, Y - iy)
    h, w = src.shape[:2]
    ch, cw = canvas.shape[:2]
    x0, y0 = max(ix, 0), max(iy, 0)
    x1, y1 = min(ix + w, cw), min(iy + h, ch)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - iy:y1 - iy, x0 - ix:x1 - ix]
    dst = canvas[y0:y1, x0:x1]
    if alpha >= 0.999:
        dst *= 1.0 - s[..., 3:4]
        dst += s[..., :3]
    else:
        dst *= 1.0 - alpha * s[..., 3:4]
        dst += alpha * s[..., :3]


def column_window(spr: Sprite, a: float, b: float) -> Sprite | None:
    """Copy of a sprite with only columns in [a, b) (sprite pixels) visible.
    Edges use exact area coverage, so a growing window reveals smoothly."""
    if b <= a:
        return None
    c = np.arange(spr.w, dtype=np.float32)
    cover = np.clip(np.minimum(c + 1.0, b) - np.maximum(c, a), 0.0, 1.0)
    if cover.min() >= 1.0:
        return spr
    pm = spr.pm * cover[None, :, None]
    return Sprite(pm, spr.ox, spr.oy, spr.adv)


def row_window(spr: Sprite, a: float, b: float) -> Sprite | None:
    """Same as column_window, for rows."""
    if b <= a:
        return None
    r = np.arange(spr.h, dtype=np.float32)
    cover = np.clip(np.minimum(r + 1.0, b) - np.maximum(r, a), 0.0, 1.0)
    if cover.min() >= 1.0:
        return spr
    pm = spr.pm * cover[:, None, None]
    return Sprite(pm, spr.ox, spr.oy, spr.adv)


def mix(a: Sprite, b: Sprite, k: float) -> Sprite:
    """Cross-fade two same-size sprites (k = 0 gives a, 1 gives b)."""
    if k <= 0.0:
        return a
    if k >= 1.0:
        return b
    return Sprite(a.pm * (1.0 - k) + b.pm * k, a.ox, a.oy, a.adv)


def new_canvas(color: str = "surface") -> np.ndarray:
    c = np.array(brand.rgb(color), np.float32) / 255.0
    canvas = np.empty((H, W, 3), np.float32)
    canvas[:] = c
    return canvas


def to_rgb8(canvas: np.ndarray) -> np.ndarray:
    out = canvas * 255.0
    out += 0.5
    np.clip(out, 0.0, 255.0, out=out)
    return out.astype(np.uint8)


# Timing helpers.

def enter(t: float, start: float, dur: float = brand.ENTER_S, rise: float = brand.RISE_PX):
    """Fade plus rise entrance. Returns (alpha, dy) where dy is added to y."""
    p = brand.ease_out_cubic(brand.progress(t, start, dur))
    return p, rise * (1.0 - p)


def fade(t: float, start: float, dur: float, ease=brand.ease_in_out_sine) -> float:
    return ease(brand.progress(t, start, dur))


def lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


# Rendering and encoding.

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def ffmpeg_cmd(out_path: Path, n_frames: int) -> list[str]:
    return [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-frames:v", str(n_frames),
        # setparams makes the frames carry BT.709 primaries and transfer, so the stream tags stick.
        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,"
               "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
        "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        "-an", "-movflags", "+faststart",
        str(out_path),
    ]


_WORKER = None


def _init_worker(spec):
    global _WORKER
    import scenes  # noqa: F401  (imported in the worker)
    _WORKER = scenes.build(*spec)


def _render_frame(i: int) -> bytes:
    canvas = new_canvas(_WORKER.background)
    _WORKER.draw(canvas, i / FPS)
    return to_rgb8(canvas).tobytes()


def render_still(scene, t: float, out_path: Path) -> Path:
    canvas = new_canvas(scene.background)
    scene.draw(canvas, t)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(to_rgb8(canvas), "RGB").save(out_path)
    return out_path


def render_video(spec, scene, out_path: Path, workers: int | None = None, log=print) -> dict:
    """Render a scene to MP4. spec is the (name, duration, beats, params) tuple
    used to rebuild the same scene inside each worker process."""
    n_frames = round(scene.duration * FPS)
    settle = scene.settle_time()
    # Frames from settle_idx on are identical to frame settle_idx.
    settle_idx = min(n_frames - 1, max(0, math.ceil(settle * FPS)))
    unique = settle_idx + 1
    workers = workers or max(2, min(12, (os.cpu_count() or 4) - 4))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.stem + ".partial" + out_path.suffix)
    t0 = time.time()
    proc = subprocess.Popen(ffmpeg_cmd(tmp, n_frames), stdin=subprocess.PIPE)
    ctx = mp.get_context("spawn")
    last = None
    try:
        with ctx.Pool(workers, initializer=_init_worker, initargs=(spec,)) as pool:
            window: deque = deque()
            nxt = 0
            while nxt < unique or window:
                while nxt < unique and len(window) < 3 * workers:
                    window.append(pool.apply_async(_render_frame, (nxt,)))
                    nxt += 1
                last = window.popleft().get()
                proc.stdin.write(last)
        for _ in range(n_frames - unique):
            proc.stdin.write(last)
        proc.stdin.close()
        rc = proc.wait()
    except BaseException:
        proc.kill()
        raise
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed with code {rc}")
    tmp.replace(out_path)
    secs = time.time() - t0
    info = {"out": str(out_path), "frames": n_frames, "unique_frames": unique,
            "duration": n_frames / FPS, "render_seconds": round(secs, 1)}
    log(f"{scene.name}: {n_frames} frames ({unique} unique) -> {out_path} in {secs:.1f}s")
    return info
