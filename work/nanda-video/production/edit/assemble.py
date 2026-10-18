#!/opt/homebrew/bin/python3
"""Assemble the Muse and Wajo demo video from edit/edl.json.

Usage (from claude/, the folder that holds CONTRACT.md):

  python3 edit/assemble.py --dry-run          print the timeline table and source status
  python3 edit/assemble.py --mode test        placeholders allowed, writes out/test/muse-wajo-test.mp4
  python3 edit/assemble.py --mode final       refuses missing captures, placeholders and stubs
  python3 edit/assemble.py --only cap09       re-render one segment (forced), no join
  python3 edit/assemble.py --force            rebuild every segment
  python3 edit/assemble.py --grid cap04 12.5  capture frame at source 12.5 s with a pixel grid,
                                              the crop and the redaction boxes drawn on it

How it works:
  1. Every EDL segment is rendered to build/edit/segments/NN_<id>.mp4 at its exact slot
     length plus crossfade handles (1920x1080, 30 fps CFR, yuv420p, BT.709, exact frames).
     Motion comes from motion/render.py, else motion/out/<name>.mp4, else a stub slate.
     Captures are normalized from any container or frame rate; a missing capture becomes an
     obvious placeholder slate. Segments are cached by a hash of the segment JSON plus input
     file sizes and mtimes, so a rerun only rebuilds what changed.
  2. A small numpy compositor reads the segments frame by frame, blends the crossfades
     (centered on boundaries) or cuts, and pipes the frames into one final encode.
  3. The final encode muxes ../audio/narration-final.wav untouched (AAC 48 kHz 256 kb/s, the
     mono channel copied to both channels at unity gain, no other filters) and the captions
     as a mov_text soft subtitle track. The .srt and a converted .vtt go next to the output.

Only Python 3 stdlib, Pillow, numpy and the ffmpeg/ffprobe CLIs are used.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import math
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

EDIT_DIR = Path(__file__).resolve().parent
ROOT = EDIT_DIR.parent                          # claude/
sys.path.insert(0, str(ROOT / "lib"))
import brand  # noqa: E402  (shared palette, Inter with HarfBuzz kerning, chips)

BUILD = ROOT / "build" / "edit"
SEG_DIR = BUILD / "segments"
WORK = BUILD / "work"
LOGS = BUILD / "logs"
DEFAULT_EDL = EDIT_DIR / "edl.json"
MOTION_DIR = ROOT / "motion"
MOTION_RENDER = MOTION_DIR / "render.py"
MOTION_OUT = MOTION_DIR / "out"

PY = "/opt/homebrew/bin/python3" if Path("/opt/homebrew/bin/python3").exists() else sys.executable
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"

W, H, FPS = brand.W, brand.H, brand.FPS
FRAME_BYTES = W * H * 3 // 2                    # one yuv420p frame
FRAME_BOX = (1760, 990)                          # "frame" fit: footage fits inside this box
CAPTURE_EXTS = (".mp4", ".mov", ".m4v", ".webm", ".mkv")
RENDER_VERSION = "edit-3"                        # bump to invalidate every cached segment
COLOR_TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
              "-color_range", "tv"]
TO_709 = "scale=out_color_matrix=bt709:out_range=tv"   # explicit RGB to BT.709 limited range
CHIP_SIZE = 40
CHIP_FADE = 0.3
REDACT_PAD_S = 0.1                               # redaction boxes start early and end late by this
PLACEHOLDER_KINDS = {"capture_placeholder", "motion_stub"}


class EditError(RuntimeError):
    pass


# Small helpers ------------------------------------------------------------------------------

def frame_of(t: float) -> int:
    """Output frame index for a time in seconds (round half up, stable for 3 decimals)."""
    return int(math.floor(float(t) * FPS + 0.5 + 1e-6))


def rpath(p: str | Path) -> Path:
    """EDL paths are relative to claude/."""
    q = Path(p).expanduser()
    return q if q.is_absolute() else (ROOT / q).resolve()


def show(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        try:
            return "../" + str(p.resolve().relative_to(ROOT.parent))
        except ValueError:
            return str(p)


def fingerprint(path: Path) -> dict:
    st = path.stat()
    return {"path": str(path), "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], log: Path, cwd: Path | None = None, timeout: float | None = None) -> int:
    """Run a command, appending the command line and its output to a log file."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write("\n$ " + " ".join(_q(c) for c in cmd) + "\n")
        f.flush()
        try:
            proc = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired:
            f.write(f"\nTIMEOUT after {timeout} s\n")
            return 124
        f.write(f"[exit {proc.returncode}]\n")
        return proc.returncode


def _q(s: str) -> str:
    return s if re.fullmatch(r"[\w@%+=:,./-]+", s) else "'" + s.replace("'", "'\\''") + "'"


def tail(log: Path, n: int = 12) -> str:
    try:
        return "\n".join(log.read_text(errors="replace").splitlines()[-n:])
    except OSError:
        return ""


def probe(path: Path) -> dict:
    """Video stream facts. Duration falls back to packet timestamps (MediaRecorder webm has none)."""
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,pix_fmt,color_space,color_range,r_frame_rate,avg_frame_rate,duration"
         ":format=duration,start_time", "-of", "json", str(path)],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise EditError(f"ffprobe failed on {path}: {out.stderr.strip()}")
    data = json.loads(out.stdout or "{}")
    streams = data.get("streams") or []
    if not streams:
        raise EditError(f"no video stream in {path}")
    s = streams[0]
    dur = None
    for v in (s.get("duration"), (data.get("format") or {}).get("duration")):
        try:
            dur = float(v)
            break
        except (TypeError, ValueError):
            continue
    if dur is None:
        pk = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                             "packet=pts_time,duration_time", "-of", "csv=p=0", str(path)],
                            capture_output=True, text=True)
        best = 0.0
        for line in pk.stdout.splitlines():
            parts = line.split(",")
            try:
                end = float(parts[0]) + (float(parts[1]) if len(parts) > 1 and parts[1] else 0.0)
                best = max(best, end)
            except ValueError:
                continue
        dur = best or None
    return {"width": int(s["width"]), "height": int(s["height"]), "pix_fmt": s.get("pix_fmt", ""),
            "color_space": s.get("color_space", ""), "color_range": s.get("color_range", ""),
            "duration": dur}


def count_frames(path: Path) -> int:
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-count_packets",
                          "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    try:
        return int(out.stdout.strip().split(",")[0])
    except ValueError:
        return -1


def enc_args(frames: int, fmt: dict) -> list[str]:
    inter = fmt.get("intermediate", {})
    return ["-frames:v", str(frames), "-fps_mode", "cfr", "-r", str(FPS), "-an", "-sn", "-dn",
            "-c:v", "libx264", "-preset", str(inter.get("preset", "medium")),
            "-crf", str(inter.get("crf", 14)), "-pix_fmt", "yuv420p", "-profile:v", "high",
            *COLOR_TAGS]


# Text and sprites (all text goes through lib/brand.py) ---------------------------------------

def text_w(text: str, size: float, weight: int) -> float:
    spr, _ = brand.rich_text_image(text, size, weight)
    return spr.width - 2 * math.ceil(size * 0.08)


def paste_text(img: Image.Image, text: str, x: float, baseline: float, size: float,
               weight: int = 400, color: str = "navy", anchor: str = "l") -> None:
    spr, base = brand.rich_text_image(text, size, weight, color)
    pad = math.ceil(size * 0.08)
    width = spr.width - 2 * pad
    x0 = x - (width / 2 if anchor == "m" else width if anchor == "r" else 0) - pad
    img.alpha_composite(spr, (round(x0), round(baseline - base)))


def wrap(text: str, size: float, weight: int, max_w: float, max_lines: int = 6) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if not cur or text_w(trial, size, weight) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,") + " ..."
    return lines


def hatch(c0: str, c1: str, stripe: int = 34) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W]
    band = ((xx + yy) // stripe) % 2
    a = np.array(brand.hex_rgb(c0), dtype=np.uint8)
    b = np.array(brand.hex_rgb(c1), dtype=np.uint8)
    arr = np.where(band[..., None] == 0, a, b).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def slate_png(path: Path, kind: str, title: str, lines: list[tuple[str, int, int, str]]) -> Path:
    """Unmistakable test slate: diagonal hatch, a navy title band and plain detail lines.

    kind "capture" uses amber caution stripes, kind "motion" uses blue stripes. Nothing here
    resembles app UI and there is no cursor."""
    if kind == "capture":
        img = hatch("#fff4d6", "#f6dc9a")
    else:
        img = hatch(brand.COLORS["brand_200"], brand.COLORS["line_strong"])
    band_y, band_h = 250, 190
    img.alpha_composite(Image.new("RGBA", (W, band_h), brand.rgba("navy")), (0, band_y))
    paste_text(img, title, W / 2, band_y + band_h / 2 + brand.metrics(96, 700)["cap"] / 2, 96, 700,
               "white", "m")
    tag = brand.chip("TEST RENDER ONLY, NOT FINAL", 30, 600, fg="white", bg="navy", shadow=False)
    img.alpha_composite(tag, (brand.SAFE_X, brand.SAFE_Y))
    panel_top = band_y + band_h
    panel = Image.new("RGBA", (W, H - panel_top - 90), brand.rgba("surface_light", 0.94))
    img.alpha_composite(panel, (0, panel_top))
    y = panel_top + 92
    for text, size, weight, color in lines:
        for line in wrap(text, size, weight, W - 2 * brand.SAFE_X - 80, 4):
            paste_text(img, line, W / 2, y, size, weight, color, "m")
            y += round(size * 1.42)
        y += round(size * 0.35)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path)
    return path


def chip_png(text: str) -> tuple[Path, int, int]:
    """Callout chip sprite plus its top-left position (bottom left, inside the safe margin)."""
    spr = brand.chip(text, CHIP_SIZE)
    margin = math.ceil(14 * 3)                   # brand.chip shadow blur 14
    key = hashlib.sha1(f"{text}|{CHIP_SIZE}".encode()).hexdigest()[:10]
    path = WORK / f"chip_{key}.png"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        spr.save(path)
    x = brand.SAFE_X - margin
    y = H - brand.SAFE_Y - spr.height + margin
    return path, x, y


def frame_decor(cw: int, ch: int) -> tuple[Path, int, int, int, int]:
    """Decoration for the "frame" fit: surface background, soft shadow, rounded corners and a
    hairline border, transparent where the footage shows. Returns (png, x, y, w, h)."""
    s = min(FRAME_BOX[0] / cw, FRAME_BOX[1] / ch)
    w = max(2, int(round(cw * s / 2)) * 2)
    h = max(2, int(round(ch * s / 2)) * 2)
    x = (W - w) // 2 // 2 * 2
    y = (H - h) // 2 // 2 * 2
    path = WORK / f"decor_{w}x{h}_{x}_{y}.png"
    if not path.exists():
        r = brand.RADIUS_CARD
        bg = brand.canvas("surface")
        sh, m = brand.soft_shadow(w, h, r, blur=22, opacity=0.6)
        bg.alpha_composite(sh, (x - m, y - m + 10))
        inside = Image.new("L", (W, H), 0)
        inside.paste(brand.rounded_box(w, h, r, (255, 255, 255, 255)).getchannel("A"), (x, y))
        bg.putalpha(Image.eval(inside, lambda v: 255 - v))
        ring = brand.rounded_box(w, h, r, (0, 0, 0, 0), outline="line_strong", outline_w=2)
        bg.alpha_composite(ring, (x, y))
        path.parent.mkdir(parents=True, exist_ok=True)
        bg.save(path)
    return path, x, y, w, h


# Plan -----------------------------------------------------------------------------------------

@dataclass
class Seg:
    idx: int
    data: dict
    f0: int
    f1: int
    h_in: int = 0
    h_out: int = 0
    trans_in: str = "start"
    trans_out: str = "end"
    source: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.data["id"]

    @property
    def kind(self) -> str:
        return self.data["kind"]

    @property
    def frames(self) -> int:
        return self.f1 - self.f0

    @property
    def ff0(self) -> int:
        return self.f0 - self.h_in

    @property
    def ff1(self) -> int:
        return self.f1 + self.h_out

    @property
    def file_frames(self) -> int:
        return self.ff1 - self.ff0

    @property
    def path(self) -> Path:
        return SEG_DIR / f"{self.idx:02d}_{self.id}.mp4"

    @property
    def stamp(self) -> Path:
        return SEG_DIR / f"{self.idx:02d}_{self.id}.json"

    @property
    def log(self) -> Path:
        return LOGS / f"{self.idx:02d}_{self.id}.log"


def load_edl(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise EditError(f"{path} is not valid JSON: {e}") from e


def build_plan(edl: dict) -> list[Seg]:
    segs_in = edl.get("segments") or []
    if not segs_in:
        raise EditError("EDL has no segments")
    ids = [s.get("id") for s in segs_in]
    if len(set(ids)) != len(ids) or not all(ids):
        raise EditError("segment ids must be present and unique")
    plan = []
    for i, s in enumerate(segs_in, 1):
        if s.get("kind") not in ("motion", "capture"):
            raise EditError(f"{s['id']}: kind must be motion or capture")
        f0, f1 = frame_of(s["start"]), frame_of(s["end"])
        if f1 <= f0:
            raise EditError(f"{s['id']}: end must be after start")
        plan.append(Seg(i, s, f0, f1))
    if plan[0].f0 != 0:
        raise EditError("the first segment must start at 0")
    for a, b in zip(plan, plan[1:]):
        if a.f1 != b.f0:
            raise EditError(f"gap or overlap between {a.id} (ends frame {a.f1}) and {b.id} "
                            f"(starts frame {b.f0})")
    tr = edl.get("transitions") or {}
    default = tr.get("default") or {"type": "crossfade", "duration": 0.5}
    overrides = {b.get("after"): b for b in tr.get("boundaries") or []}
    for a, b in zip(plan, plan[1:]):
        t = dict(default)
        t.update(overrides.get(a.id) or {})
        if t.get("type", "crossfade") == "cut":
            h, name = 0, "cut"
        else:
            d = float(t.get("duration", 0.5))
            h = max(1, round(d * FPS) // 2)
            name = f"xfade {d:g}s"
        a.h_out = b.h_in = h
        a.trans_out = b.trans_in = name
    for s in plan:
        if s.frames < s.h_in + s.h_out + 1:
            raise EditError(f"{s.id} is too short for its crossfades")
    return plan


def prerender_path(seg: Seg) -> Path:
    if seg.data.get("prerender"):
        return rpath(seg.data["prerender"])
    scene = seg.data.get("scene", seg.id)
    if scene == "step":
        return MOTION_OUT / f"step{(seg.data.get('params') or {}).get('number', '')}.mp4"
    return MOTION_OUT / f"{scene}.mp4"


def find_capture(seg: Seg) -> Path | None:
    p = rpath(seg.data.get("file") or f"../captures/{seg.data.get('slot', seg.id)}.mp4")
    if p.is_file():
        return p
    for ext in CAPTURE_EXTS:                    # same name with another container
        q = p.with_suffix(ext)
        if q.is_file():
            return q
    return None


def motion_files() -> list[dict]:
    """Fingerprints of the motion renderer's own files (code and assets, not its renders)."""
    files = [p for p in sorted(MOTION_DIR.rglob("*")) if p.is_file()
             and "__pycache__" not in p.parts and MOTION_OUT not in p.parents
             and not p.name.startswith(".")]
    return [fingerprint(p) for p in files]


def resolve_source(seg: Seg) -> dict:
    if seg.kind == "motion":
        if MOTION_RENDER.exists():
            return {"kind": "motion_render", "path": show(MOTION_RENDER)}
        pre = prerender_path(seg)
        if pre.exists():
            return {"kind": "motion_prerender", "path": show(pre)}
        return {"kind": "motion_stub", "reason": f"no motion/render.py and no {show(pre)}"}
    src = find_capture(seg)
    expected = seg.data.get("file") or f"../captures/{seg.data.get('slot', seg.id)}.mp4"
    if src:
        return {"kind": "capture", "path": show(src)}
    return {"kind": "capture_placeholder", "reason": f"missing {expected}"}


def seg_key(seg: Seg) -> str:
    src = seg.source
    if src["kind"] == "motion_render":
        inputs = motion_files()
    elif src["kind"] in ("motion_prerender", "capture"):
        inputs = [fingerprint(rpath(src["path"]))]
    else:
        inputs = [src.get("reason", "")]
    payload = {
        "v": RENDER_VERSION, "segment": seg.data, "frames": [seg.f0, seg.f1, seg.h_in, seg.h_out],
        "source": src["kind"], "inputs": inputs,
        "brand": fingerprint(Path(brand.__file__)), "font": fingerprint(brand.font_path()),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:24]


# Rendering ------------------------------------------------------------------------------------

class Context:
    def __init__(self, edl: dict, mode: str):
        self.edl = edl
        self.mode = mode
        self.fmt = edl.get("format") or {}
        self._motion_list = None
        self._listed = False
        self._lock = threading.Lock()
        self.motion_lock = threading.Lock()     # render.py runs one scene at a time

    def motion_list(self) -> dict | None:
        """Parsed `motion/render.py --list`, or None when it is missing or fails."""
        with self._lock:
            return self._motion_list_locked()

    def _motion_list_locked(self) -> dict | None:
        if self._listed:
            return self._motion_list
        self._listed = True
        if not MOTION_RENDER.exists():
            return None
        try:
            out = subprocess.run([PY, str(MOTION_RENDER), "--list"], cwd=ROOT, capture_output=True,
                                 text=True, timeout=180)
            text = out.stdout
            data = json.loads(text[text.index("{"): text.rindex("}") + 1])
            self._motion_list = data if isinstance(data, dict) else None
        except Exception as e:  # noqa: BLE001 (a broken renderer must not stop the edit)
            print(f"  note: motion/render.py --list failed ({e.__class__.__name__}); "
                  "rendering without scene limits")
            self._motion_list = None
        return self._motion_list


def overlay_chip(seg: Seg, chain: list[str], label: str, inputs: list[str], n_in: int) -> tuple[str, int]:
    """Add the callout chip (alpha fades) to a filter graph. Times in the EDL are absolute."""
    co = seg.data.get("callout")
    if not co or not co.get("text"):
        return label, n_in
    png, cx, cy = chip_png(co["text"])
    a = float(co["at"]) - seg.ff0 / FPS
    b = a + float(co.get("dur", 4.0))
    fade = min(CHIP_FADE, (b - a) / 2)
    inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(png)]
    chain.append(f"[{n_in}:v]format=rgba,fade=t=in:st={a:.4f}:d={fade:.3f}:alpha=1,"
                 f"fade=t=out:st={b - fade:.4f}:d={fade:.3f}:alpha=1,{TO_709},format=yuva444p[chip]")
    chain.append(f"[{label}][chip]overlay={cx}:{cy}:format=yuv444:"
                 f"enable='between(t,{a:.4f},{b:.4f})'[withchip]")
    return "withchip", n_in + 1


def render_slate(seg: Seg, ctx: Context, png: Path) -> None:
    inputs = ["-loop", "1", "-framerate", str(FPS), "-i", str(png)]
    chain = [f"[0:v]format=rgb24,{TO_709},format=yuv444p[base]"]
    label, _ = overlay_chip(seg, chain, "base", inputs, 1)
    chain.append(f"[{label}]format=yuv420p[out]")
    cmd = [FFMPEG, "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chain), "-map", "[out]",
           *enc_args(seg.file_frames, ctx.fmt), str(seg.path)]
    if run(cmd, seg.log) != 0:
        raise EditError(f"{seg.id}: slate encode failed\n{tail(seg.log)}")


def placeholder_png(seg: Seg) -> Path:
    d = seg.data
    expected = d.get("file") or f"../captures/{d.get('slot', seg.id)}.mp4"
    lines = [
        (f"{d.get('slot', seg.id)}   (segment {seg.id})", 54, 600, "navy"),
        (f"Slot {d['start']:.3f} to {d['end']:.3f} s, {d['end'] - d['start']:.2f} s", 34, 500, "ink_medium"),
        (d.get("notes", ""), 36, 400, "ink"),
        ("Evidence: " + (", ".join(d.get("evidence") or []) or "none"), 32, 600, "brand_600"),
        (f"Expected file: {expected}", 32, 500, "ink_medium"),
    ]
    key = hashlib.sha1(json.dumps([lines, "capture"], sort_keys=True).encode()).hexdigest()[:10]
    return slate_png(WORK / f"placeholder_{seg.id}_{key}.png", "capture", "CAPTURE PENDING", lines)


def stub_png(seg: Seg, reason: str) -> Path:
    d = seg.data
    params = d.get("params") or {}
    detail = ", ".join(f"{k}: {v}" for k, v in params.items()) or "default copy"
    beats = ", ".join(f"{k} at {v:g} s" for k, v in (d.get("beats") or {}).items()) or "default beats"
    lines = [
        (f"Segment {seg.id}", 54, 600, "navy"),
        (f"Slot {d['start']:.3f} to {d['end']:.3f} s, {d['end'] - d['start']:.2f} s", 34, 500, "ink_medium"),
        (detail, 36, 500, "ink"),
        (f"Beats: {beats}", 32, 500, "ink_medium"),
        (reason, 30, 500, "ink_medium"),
    ]
    key = hashlib.sha1(json.dumps([lines, "motion"], sort_keys=True).encode()).hexdigest()[:10]
    title = f"MOTION PENDING: {d.get('scene', seg.id)}"
    return slate_png(WORK / f"stub_{seg.id}_{key}.png", "motion", title, lines)


def normalize_clip(seg: Seg, ctx: Context, src: Path, core_frames: int | None = None) -> None:
    """Fit a 30 fps clip to the slot: trim or hold (clone) to the slot length, then add the
    crossfade handles by cloning the first and last frames. No speed change."""
    info = probe(src)
    core = seg.frames if core_frames is None else core_frames
    conv = ""
    if (info["width"], info["height"]) != (W, H) or info["pix_fmt"] != "yuv420p":
        conv = (f"scale={W}:{H}:flags=lanczos:{color_in(info)}:out_color_matrix=bt709:out_range=tv,"
                "format=yuv420p,")
    vf = (f"fps={FPS},{conv}trim=end_frame={core},setpts=PTS-STARTPTS,"
          f"tpad=start={seg.h_in}:start_mode=clone:stop=-1:stop_mode=clone,setsar=1")
    cmd = [FFMPEG, "-y", "-v", "error", "-i", str(src), "-map", "0:v:0", "-vf", vf,
           *enc_args(seg.file_frames, ctx.fmt), str(seg.path)]
    if run(cmd, seg.log) != 0:
        raise EditError(f"{seg.id}: normalize failed\n{tail(seg.log)}")


def render_motion(seg: Seg, ctx: Context) -> dict:
    d = seg.data
    scene = d.get("scene", seg.id)
    params = d.get("params") or {}
    beats = dict(d.get("beats") or {})
    notes: list[str] = []
    if MOTION_RENDER.exists():
        slot = seg.frames / FPS
        dur = slot
        listing = ctx.motion_list()
        spec = (listing or {}).get(scene)
        if listing is not None and spec is None:
            notes.append(f"scene {scene} is not in render.py --list")
        if isinstance(spec, dict):
            allowed = set((spec.get("beats") or {}).keys())
            dropped = sorted(set(beats) - allowed)
            if dropped:
                notes.append("beats not declared by the scene, not sent: " + ", ".join(dropped))
                beats = {k: v for k, v in beats.items() if k in allowed}
            lo, hi = spec.get("min"), spec.get("max")
            if isinstance(hi, (int, float)) and dur > hi + 1e-6:
                notes.append(f"slot {slot:.3f} s is above the scene max {hi} s, last frame held")
                dur = float(hi)
            if isinstance(lo, (int, float)) and dur < lo - 1e-6:
                notes.append(f"slot {slot:.3f} s is below the scene min {lo} s, tail trimmed")
                dur = float(lo)
        raw = WORK / f"motion_{seg.idx:02d}_{seg.id}.mp4"
        raw.unlink(missing_ok=True)
        cmd = [PY, str(MOTION_RENDER), scene, "--duration", f"{dur:.6f}", "--out", str(raw)]
        if beats:
            cmd += ["--beats", json.dumps(beats)]
        for k, v in params.items():
            cmd += ["--param", f"{k}={v}"]
        with ctx.motion_lock:
            rc = run(cmd, seg.log, cwd=ROOT, timeout=3600)
        got = count_frames(raw) if rc == 0 and raw.exists() else -1
        if got > 0:
            want = round(dur * FPS)
            if got != want:
                notes.append(f"render.py gave {got} frames, expected {want}; padded or trimmed")
            normalize_clip(seg, ctx, raw)
            return {"source_kind": "motion_render", "source": show(MOTION_RENDER), "notes": notes,
                    "command": " ".join(_q(c) for c in cmd)}
        notes.append(f"render.py failed for {scene} (exit {rc}), see {show(seg.log)}")
    pre = prerender_path(seg)
    if pre.exists():
        normalize_clip(seg, ctx, pre)
        notes.append("prerendered clip, beats not applied")
        return {"source_kind": "motion_prerender", "source": show(pre), "notes": notes}
    reason = notes[-1] if notes else f"no motion/render.py and no {show(pre)}"
    if ctx.mode == "final":
        raise EditError(f"{seg.id}: no motion available ({reason})")
    render_slate(seg, ctx, stub_png(seg, reason))
    return {"source_kind": "motion_stub", "source": None, "notes": notes + [reason]}


def color_in(info: dict) -> str:
    """Input color options for scale. Untagged YUV screen footage at HD or above is treated
    as BT.709 (the convention players use), tagged footage uses its own tags."""
    pf = info["pix_fmt"]
    if pf.startswith(("rgb", "bgr", "argb", "abgr", "gbr", "rgba", "bgra")):
        return "in_range=auto"
    cs = info.get("color_space") or ""
    if cs in ("", "unknown", "reserved") and info["height"] >= 720:
        return "in_color_matrix=bt709:in_range=auto"
    return "in_color_matrix=auto:in_range=auto"


def render_capture(seg: Seg, ctx: Context) -> dict:
    d = seg.data
    src = find_capture(seg)
    if src is None:
        if ctx.mode == "final":
            raise EditError(f"{seg.id}: capture file missing ({d.get('file')})")
        render_slate(seg, ctx, placeholder_png(seg))
        return {"source_kind": "capture_placeholder", "source": None,
                "notes": [f"missing {d.get('file')}"]}
    info = probe(src)
    sw, sh = info["width"], info["height"]
    notes: list[str] = []
    src_in = float(d.get("src_in") or 0.0)
    seek = src_in - seg.h_in / FPS
    pre = 0
    if seek < 0:
        pre = round(-seek * FPS)
        seek = 0.0
    need = src_in + (seg.frames + seg.h_out) / FPS
    if info["duration"] is not None:
        if src_in >= info["duration"]:
            raise EditError(f"{seg.id}: src_in {src_in} s is past the end of {show(src)} "
                            f"({info['duration']:.3f} s)")
        if info["duration"] < need - 1e-3:
            notes.append(f"source ends {need - info['duration']:.2f} s before the slot needs it, "
                         "last frame held")
    # Crop in source pixels, clamped to the frame.
    crop = d.get("crop")
    if crop:
        cx, cy, cw, ch = (int(round(v)) for v in crop)
        cx, cy = max(0, min(cx, sw - 2)), max(0, min(cy, sh - 2))
        cw, ch = max(2, min(cw, sw - cx)), max(2, min(ch, sh - cy))
    else:
        cx, cy, cw, ch = 0, 0, sw, sh
    fit = d.get("fit") or "auto"
    if fit == "auto":
        fit = "fill" if abs((cw / ch) / (W / H) - 1) < 0.01 else "frame"
    inputs: list[str] = []
    if seek > 0:
        inputs += ["-noaccurate_seek", "-ss", f"{seek:.6f}"]
    inputs += ["-i", str(src)]
    chain = [f"[0:v:0]setpts=PTS+{seek:.6f}/TB,fps={FPS}:start_time={seek:.6f},"
             f"scale={color_in(info)}:out_color_matrix=bt709:out_range=tv,format=yuv444p[s0]"]
    label = "s0"
    # Redaction in source pixels and source seconds (t is source time here), box blur.
    for i, box in enumerate(d.get("redact") or []):
        x0 = max(0, int(math.floor(float(box["x"]))))
        y0 = max(0, int(math.floor(float(box["y"]))))
        x1 = min(sw, int(math.ceil(float(box["x"]) + float(box["w"]))))
        y1 = min(sh, int(math.ceil(float(box["y"]) + float(box["h"]))))
        bw, bh = x1 - x0, y1 - y0
        if bw < 2 or bh < 2:
            notes.append(f"redact box {i} is outside the frame, skipped")
            continue
        t0 = float(box.get("t0", 0.0)) - REDACT_PAD_S
        t1 = float(box.get("t1", 1e6)) + REDACT_PAD_S
        small_w, small_h = max(2, bw // 16), max(2, bh // 16)
        smooth = min(2, min(bw, bh) // 2 - 1)
        chain.append(f"[{label}]split=2[m{i}][r{i}]")
        chain.append(f"[r{i}]crop={bw}:{bh}:{x0}:{y0},scale={small_w}:{small_h}:flags=area,"
                     f"boxblur=1:1,scale={bw}:{bh}:flags=bicubic"
                     + (f",boxblur={smooth}:1" if smooth >= 1 else "") + f"[b{i}]")
        chain.append(f"[m{i}][b{i}]overlay={x0}:{y0}:format=yuv444:"
                     f"enable='between(t,{t0:.3f},{t1:.3f})'[s{i + 1}]")
        label = f"s{i + 1}"
    geo = [f"[{label}]setpts=PTS-STARTPTS"]
    if (cx, cy, cw, ch) != (0, 0, sw, sh):
        geo.append(f"crop={cw}:{ch}:{cx}:{cy}")
    if fit == "fill":
        s = max(W / cw, H / ch)
        tw, th = max(W, math.ceil(cw * s)), max(H, math.ceil(ch * s))
        geo.append(f"scale={tw}:{th}:flags=lanczos")
        if (tw, th) != (W, H):
            geo.append(f"crop={W}:{H}:{(tw - W) // 2}:{(th - H) // 2}")
    else:
        decor, fx, fy, fw, fh = frame_decor(cw, ch)
        geo.append(f"scale={fw}:{fh}:flags=lanczos")
    geo.append("setsar=1")
    geo.append(f"tpad=start={pre}:start_mode=clone:stop=-1:stop_mode=clone")
    if fit == "frame":
        geo.append(f"pad={W}:{H}:{fx}:{fy}")
    chain.append(",".join(geo) + "[g]")
    label, n_in = "g", 1
    if fit == "frame":
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(decor)]
        chain.append(f"[1:v]format=rgba,{TO_709},format=yuva444p[decor]")
        chain.append("[g][decor]overlay=0:0:format=yuv444[framed]")
        label, n_in = "framed", 2
    label, n_in = overlay_chip(seg, chain, label, inputs, n_in)
    chain.append(f"[{label}]format=yuv420p[out]")
    cmd = [FFMPEG, "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chain), "-map", "[out]",
           *enc_args(seg.file_frames, ctx.fmt), str(seg.path)]
    if run(cmd, seg.log, timeout=7200) != 0:
        raise EditError(f"{seg.id}: capture render failed\n{tail(seg.log)}")
    notes.append(f"{sw}x{sh} source, crop {cw}x{ch} at {cx},{cy}, fit {fit}, src_in {src_in:.3f} s")
    return {"source_kind": "capture", "source": show(src), "notes": notes, "fit": fit}


def render_one(seg: Seg, ctx: Context, force: bool) -> dict:
    key = seg_key(seg)
    if not force and seg.path.exists() and seg.stamp.exists():
        try:
            st = json.loads(seg.stamp.read_text())
            if st.get("key") == key and st.get("source_kind") == seg.source["kind"]:
                st["cached"] = True
                return st
        except (OSError, json.JSONDecodeError):
            pass
    SEG_DIR.mkdir(parents=True, exist_ok=True)
    seg.log.parent.mkdir(parents=True, exist_ok=True)
    seg.log.write_text(f"segment {seg.id} key {key}\n")
    t0 = time.time()
    info = render_motion(seg, ctx) if seg.kind == "motion" else render_capture(seg, ctx)
    got = count_frames(seg.path)
    if got != seg.file_frames:
        raise EditError(f"{seg.id}: rendered {got} frames, expected {seg.file_frames}")
    info.update({"key": key, "frames": got, "path": show(seg.path), "seconds": round(time.time() - t0, 1),
                 "cached": False})
    if info["source_kind"] == seg.source["kind"]:
        seg.stamp.write_text(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        seg.stamp.unlink(missing_ok=True)       # fallbacks are never cached, retried next run
    return info


# Join -----------------------------------------------------------------------------------------

class Reader:
    """Sequential yuv420p frame reader for one segment file."""

    def __init__(self, seg: Seg, log):
        self.seg = seg
        self.proc = subprocess.Popen([FFMPEG, "-v", "error", "-i", str(seg.path), "-map", "0:v:0",
                                      "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                                     stdout=subprocess.PIPE, stderr=log, bufsize=FRAME_BYTES)
        self.buf = bytearray(FRAME_BYTES)
        self.count = 0

    def read(self) -> bytearray:
        view = memoryview(self.buf)
        got = 0
        while got < FRAME_BYTES:
            n = self.proc.stdout.readinto(view[got:])
            if not n:
                raise EditError(f"{self.seg.id}: segment ended after {self.count} frames, "
                                f"expected {self.seg.file_frames}")
            got += n
        self.count += 1
        return self.buf

    def close(self) -> None:
        self.proc.stdout.close()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def join(plan: list[Seg], ctx: Context, out_mp4: Path) -> None:
    edl, fmt = ctx.edl, ctx.fmt
    enc = fmt.get(ctx.mode) or {}
    aud = fmt.get("audio") or {}
    narration = rpath(edl["narration"]["file"])
    srt = rpath(edl["captions"]["srt"])
    total = plan[-1].f1
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_mp4.with_name(out_mp4.stem + ".partial.mp4")
    log_path = LOGS / f"join_{ctx.mode}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [FFMPEG, "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", str(FPS),
           *COLOR_TAGS, "-thread_queue_size", "64", "-i", "-",
           "-i", str(narration), "-i", str(srt),
           "-map", "0:v:0", "-map", "1:a:0", "-map", "2:s:0",
           "-c:v", "libx264", "-preset", str(enc.get("preset", "slow")), "-crf", str(enc.get("crf", 18)),
           "-profile:v", "high", "-pix_fmt", "yuv420p", *COLOR_TAGS, "-frames:v", str(total),
           # Mono narration copied to both channels at unity gain. (Plain -ac 2 would lower each
           # channel by 3 dB, which counts as altering the narration.) No other audio filters.
           "-af", "pan=stereo|c0=c0|c1=c0",
           "-c:a", "aac", "-b:a", str(aud.get("bitrate", "256k")), "-ar", str(aud.get("sample_rate", 48000)),
           "-c:s", "mov_text", "-metadata:s:s:0", f"language={edl['captions'].get('language', 'eng')}",
           "-metadata:s:a:0", "language=eng", "-disposition:s:0", "0",
           "-movflags", "+faststart", str(tmp)]
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("$ " + " ".join(_q(c) for c in cmd) + "\n")
        log.flush()
        encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log)
        readers: dict[int, Reader] = {}
        t0 = time.time()
        try:
            for n in range(total):
                active = [s for s in plan if s.ff0 <= n < s.ff1]
                frames = []
                for s in active:
                    if s.idx not in readers:
                        readers[s.idx] = Reader(s, log)
                    frames.append(readers[s.idx].read())
                if len(active) == 1:
                    encoder.stdin.write(frames[0])
                elif len(active) == 2:
                    a, b = active
                    h = b.h_in
                    dd = 2 * h + 1
                    k = n - b.f0 + h + 1          # 1..2h, centered on the boundary
                    fa = np.frombuffer(frames[0], dtype=np.uint8).astype(np.uint16)
                    fb = np.frombuffer(frames[1], dtype=np.uint8).astype(np.uint16)
                    mixed = (fa * (dd - k) + fb * k + dd // 2) // dd
                    encoder.stdin.write(mixed.astype(np.uint8).tobytes())
                else:
                    raise EditError(f"frame {n}: {len(active)} segments active, check the EDL")
                for s in active:
                    if n == s.ff1 - 1:
                        readers.pop(s.idx).close()
                if n % 600 == 0 or n == total - 1:
                    el = time.time() - t0
                    print(f"  join {n + 1}/{total} frames ({100 * (n + 1) / total:4.1f}%), {el:5.0f} s",
                          flush=True)
            encoder.stdin.close()
            rc = encoder.wait()
        except BrokenPipeError:
            rc = encoder.wait()
            raise EditError(f"final encoder stopped early (exit {rc}), see {show(log_path)}\n{tail(log_path)}")
        except BaseException:
            encoder.kill()
            for r in readers.values():
                r.proc.kill()
            raise
    if rc != 0:
        raise EditError(f"final encode failed (exit {rc}), see {show(log_path)}\n{tail(log_path)}")
    got = count_frames(tmp)
    if got != total:
        raise EditError(f"output has {got} frames, expected {total}")
    tmp.replace(out_mp4)


def srt_to_vtt(text: str) -> str:
    out = ["WEBVTT", ""]
    for block in re.split(r"\n\s*\n", text.strip().replace("\r\n", "\n")):
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        out += [lines[0], lines[1].replace(",", "."), *lines[2:], ""]
    return "\n".join(out)


def grid_frame(seg: Seg, t: float | None) -> Path:
    """Write one source frame with a labeled pixel grid, the crop (blue) and the redaction boxes
    active at that time (red), so crop and redact values can be read off in source pixels."""
    src = find_capture(seg)
    if src is None:
        raise EditError(f"{seg.id}: no capture file yet ({seg.data.get('file')})")
    t = float(seg.data.get("src_in") or 0.0) if t is None else float(t)
    cmd = [FFMPEG, "-v", "error"] + (["-noaccurate_seek", "-ss", f"{t:.6f}"] if t > 0 else [])
    cmd += ["-i", str(src), "-map", "0:v:0", "-vf", f"setpts=PTS+{t:.6f}/TB,fps={FPS}:start_time={t:.6f}",
            "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
    out = subprocess.run(cmd, capture_output=True)
    if out.returncode != 0 or not out.stdout:
        raise EditError(f"could not read a frame at {t} s from {show(src)}")
    img = Image.open(io.BytesIO(out.stdout)).convert("RGBA")
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for x in range(0, img.width, 100):
        d.line([(x, 0), (x, img.height)], fill=(24, 122, 220, 150 if x % 500 == 0 else 70), width=1)
    for y in range(0, img.height, 100):
        d.line([(0, y), (img.width, y)], fill=(24, 122, 220, 150 if y % 500 == 0 else 70), width=1)
    crop = seg.data.get("crop")
    if crop:
        x, y, w, h = crop
        d.rectangle([x, y, x + w, y + h], outline=(24, 122, 220, 255), width=4)
    for box in seg.data.get("redact") or []:
        if float(box.get("t0", 0)) - REDACT_PAD_S <= t <= float(box.get("t1", 1e6)) + REDACT_PAD_S:
            d.rectangle([box["x"], box["y"], box["x"] + box["w"], box["y"] + box["h"]],
                        outline=(220, 30, 30, 255), width=4)
    img.alpha_composite(over)
    for x in range(0, img.width, 200):
        tag = brand.chip(str(x), 22, 600, fg="white", bg="blue", shadow=False)
        img.alpha_composite(tag, (min(x + 4, img.width - tag.width), 4))
    for y in range(200, img.height, 200):
        tag = brand.chip(str(y), 22, 600, fg="white", bg="blue", shadow=False)
        img.alpha_composite(tag, (4, min(y + 4, img.height - tag.height)))
    path = BUILD / "grid" / f"{seg.id}_{t:.2f}s.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path)
    return path


# CLI ------------------------------------------------------------------------------------------

def table(plan: list[Seg]) -> str:
    rows = [f"{'#':>2}  {'id':8} {'kind':8} {'source':21} {'start':>8} {'end':>8} {'dur':>7} "
            f"{'frames':>6} {'in':>3}/{'out':<3} {'transition in':14} detail"]
    for s in plan:
        d = s.data
        src = s.source
        label = {"motion_render": "render.py", "motion_prerender": "prerendered",
                 "motion_stub": "STUB (pending)", "capture": "capture file",
                 "capture_placeholder": "PLACEHOLDER"}[src["kind"]]
        if s.kind == "motion":
            p = d.get("params") or {}
            detail = d.get("scene", "") + (f" {p.get('number')}: {p.get('title')}" if p.get("title") else "")
            if d.get("beats"):
                detail += "  beats " + ", ".join(f"{k}@{v:g}" for k, v in d["beats"].items())
        else:
            detail = src.get("path") or src.get("reason", "")
            if d.get("callout"):
                detail += f"  callout '{d['callout']['text']}' at {d['callout']['at']:.3f}"
        rows.append(f"{s.idx:02d}  {s.id:8} {s.kind:8} {label:21} {d['start']:8.3f} {d['end']:8.3f} "
                    f"{d['end'] - d['start']:7.3f} {s.frames:6d} {s.h_in:3d}/{s.h_out:<3d} "
                    f"{s.trans_in:14} {detail}")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Assemble the Muse and Wajo demo video from the EDL.")
    ap.add_argument("--mode", choices=["test", "final"], default="test")
    ap.add_argument("--edl", default=str(DEFAULT_EDL))
    ap.add_argument("--out", help="override the output MP4 path")
    ap.add_argument("--dry-run", action="store_true", help="print the timeline table and exit")
    ap.add_argument("--only", metavar="ID", help="re-render one segment (forced) and skip the join")
    ap.add_argument("--force", action="store_true", help="ignore the segment cache")
    ap.add_argument("--no-join", action="store_true", help="render segments only")
    ap.add_argument("--jobs", type=int, default=3, help="segments rendered in parallel (default 3)")
    ap.add_argument("--grid", nargs="+", metavar=("ID", "SECONDS"),
                    help="write a capture frame with a pixel grid, crop and redact boxes, then exit")
    args = ap.parse_args(argv)

    edl_path = Path(args.edl).resolve()
    edl = load_edl(edl_path)
    plan = build_plan(edl)
    for s in plan:
        s.source = resolve_source(s)
    if args.grid:
        seg = next((s for s in plan if s.id == args.grid[0] and s.kind == "capture"), None)
        if seg is None:
            print(f"no capture segment with id {args.grid[0]}")
            return 2
        path = grid_frame(seg, float(args.grid[1]) if len(args.grid) > 1 else None)
        print(f"Grid frame: {show(path)} (source pixels; blue = crop, red = redact boxes active then)")
        return 0
    narration = rpath(edl["narration"]["file"])
    srt = rpath(edl["captions"]["srt"])
    total = plan[-1].f1
    nar_dur = float(edl["narration"].get("duration") or probe_audio_duration(narration))
    out_mp4 = Path(args.out).resolve() if args.out else rpath(edl["outputs"][args.mode])

    print(f"EDL {show(edl_path)}: {len(plan)} segments, {total} frames = {total / FPS:.3f} s "
          f"(narration {nar_dur:.3f} s = {nar_dur * FPS:.2f} frames), mode {args.mode}")
    print(table(plan))
    pending = [s for s in plan if s.source["kind"] in PLACEHOLDER_KINDS]
    print(f"Placeholders: {sum(s.source['kind'] == 'capture_placeholder' for s in plan)} captures, "
          f"{sum(s.source['kind'] == 'motion_stub' for s in plan)} motion stubs (before render).")

    blockers = []                               # stop any render
    if abs(total - nar_dur * FPS) > 1.0:
        blockers.append(f"timeline is {total} frames but the narration is {nar_dur * FPS:.2f} frames")
    if total / FPS > float((edl.get("format") or {}).get("max_duration", 180)):
        blockers.append("timeline is longer than the maximum duration")
    if not narration.exists():
        blockers.append(f"narration missing: {narration}")
    if not srt.exists():
        blockers.append(f"captions missing: {srt}")
    want_md5 = edl["narration"].get("md5")
    if narration.exists() and want_md5 and md5_file(narration) != want_md5:
        blockers.append("narration md5 does not match the EDL (the WAV changed)")
    final_blockers = []                         # stop a final render only
    for s in pending:
        final_blockers.append(f"{s.id}: {s.source.get('reason', s.source['kind'])}")
    for s in plan:
        if s.kind == "capture" and s.data.get("privacy_check", "done") != "done":
            final_blockers.append(f"{s.id}: privacy_check is '{s.data.get('privacy_check')}' (review the "
                                  "footage, add redact boxes, then set it to done)")
    if args.mode == "final":
        blockers += final_blockers
    elif final_blockers:
        print(f"Final mode would refuse {len(final_blockers)} item(s); test mode continues.")
    for p in blockers:
        print(f"  BLOCKER: {p}")
    if blockers:
        print("Final render would be refused." if args.dry_run else "Refusing to render.")
        return 2
    if args.dry_run:
        return 0

    ctx = Context(edl, args.mode)
    targets = plan
    if args.only:
        targets = [s for s in plan if s.id == args.only]
        if not targets:
            print(f"no segment with id {args.only}")
            return 2
    print(f"Rendering {len(targets)} segment(s) into {show(SEG_DIR)} ...")
    results: dict[str, dict] = {}
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futs = {pool.submit(render_one, s, ctx, args.force or bool(args.only)): s for s in targets}
        for fut in concurrent.futures.as_completed(futs):
            s = futs[fut]
            try:
                r = fut.result()
                results[s.id] = r
                state = "cached" if r.get("cached") else f"{r.get('seconds', 0):.1f} s"
                print(f"  {s.idx:02d} {s.id:8} {r['source_kind']:20} {r['frames']:5d} frames  {state}")
                for note in r.get("notes") or []:
                    print(f"       note: {note}")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{s.id}: {e}")
                print(f"  {s.idx:02d} {s.id:8} FAILED: {e}")
    if errors:
        print("Segment errors, not joining.")
        return 1
    if args.only:
        print(f"Segment ready: {show(targets[0].path)}")
        return 0
    used = [results[s.id]["source_kind"] for s in plan]
    n_pending = sum(k in PLACEHOLDER_KINDS for k in used)
    if args.mode == "final" and n_pending:
        print(f"Refusing final join: {n_pending} placeholder or stub segments.")
        return 2
    if args.no_join:
        return 0

    print(f"Joining {total} frames into {show(out_mp4)} ...")
    t0 = time.time()
    join(plan, ctx, out_mp4)
    srt_out = out_mp4.with_suffix(".srt")
    shutil.copyfile(srt, srt_out)
    out_mp4.with_suffix(".vtt").write_text(srt_to_vtt(srt.read_text(encoding="utf-8")), encoding="utf-8")
    manifest = {
        "output": show(out_mp4), "mode": args.mode, "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "edl": show(edl_path), "edl_sha256": hashlib.sha256(edl_path.read_bytes()).hexdigest(),
        "frames": total, "fps": FPS, "duration": total / FPS,
        "narration": {"file": show(narration), "md5": md5_file(narration), "duration": nar_dur},
        "captions": {"srt": show(srt_out), "vtt": show(out_mp4.with_suffix(".vtt"))},
        "placeholders": sum(k == "capture_placeholder" for k in used),
        "stubs": sum(k == "motion_stub" for k in used),
        "segments": [{"idx": s.idx, "id": s.id, "kind": s.kind, "source_kind": results[s.id]["source_kind"],
                      "source": results[s.id].get("source"), "start": s.data["start"], "end": s.data["end"],
                      "f0": s.f0, "f1": s.f1, "h_in": s.h_in, "h_out": s.h_out,
                      "transition_in": s.trans_in, "file": show(s.path),
                      "notes": results[s.id].get("notes") or []} for s in plan],
    }
    out_mp4.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Done in {time.time() - t0:.0f} s: {show(out_mp4)} ({total} frames, {total / FPS:.3f} s), "
          f"{manifest['placeholders']} placeholders, {manifest['stubs']} stubs.")
    print(f"Sidecars: {show(srt_out)}, {show(out_mp4.with_suffix('.vtt'))}, "
          f"{show(out_mp4.with_suffix('.manifest.json'))}")
    print(f"Next: python3 edit/qa.py {show(out_mp4)}" + (" --mode final" if args.mode == "final" else ""))
    return 0


def probe_audio_duration(path: Path) -> float:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())


if __name__ == "__main__":
    try:
        sys.exit(main())
    except EditError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
