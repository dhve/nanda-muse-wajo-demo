#!/usr/bin/env python3
"""Verify the default motion renders in motion/out/.

- ffprobe: H.264 High, 1920x1080, 30 fps, yuv420p, BT.709 tags, exact frame count.
- Extracts stills at key beats from the encoded MP4s (BT.709 decode) into
  build/motion/stills/ and builds one contact sheet per scene in build/motion/.
- Checks that the intro's last frame equals the roles first frame, that each
  scene's last frame equals its settle frame, and the encoded seam difference.

  python3 motion/verify.py [--no-stills]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT / "lib"), str(HERE)]

from PIL import Image, ImageDraw  # noqa: E402

import brand  # noqa: E402
import engine  # noqa: E402
import scenes  # noqa: E402
from render import DEFAULTS, OUT_DIR  # noqa: E402

BUILD = ROOT / "build" / "motion"
STILLS = BUILD / "stills"

KEY_TIMES = {
    "intro": [0.2, 1.0, 2.65, 3.3, 4.9, 5.6, 6.25, 7.5, 11.1],
    "roles": [0.0, 0.85, 2.2, 5.6, 6.6, 7.7, 8.55, 9.5, 12.2],
    "step1": [0.0, 0.35, 2.9], "step2": [2.9], "step3": [2.9], "step4": [0.35, 2.9], "step5": [2.9],
    "closing": [0.2, 1.1, 2.1, 3.3, 4.25, 5.2, 6.4, 7.4, 8.4, 9.3, 9.9, 11.0, 11.7, 12.6, 13.6, 16.7],
    "endcard": [0.2, 0.8, 2.0, 3.95, 4.8, 6.2, 9.0],
}


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,pix_fmt,"
         "color_space,color_primaries,color_transfer,color_range,nb_read_frames",
         "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    s = data["streams"][0]
    s["duration"] = float(data["format"]["duration"])
    s["has_audio"] = bool(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
         str(path)], capture_output=True, text=True).stdout.strip())
    return s


def check_stream(name: str, path: Path, expect_frames: int) -> list[str]:
    s = probe(path)
    problems = []
    want = {"codec_name": "h264", "profile": "High", "width": 1920, "height": 1080, "r_frame_rate": "30/1",
            "pix_fmt": "yuv420p", "color_space": "bt709", "color_primaries": "bt709", "color_transfer": "bt709",
            "color_range": "tv"}
    for k, v in want.items():
        if s.get(k) != v:
            problems.append(f"{k}={s.get(k)!r} (want {v!r})")
    if int(s["nb_read_frames"]) != expect_frames:
        problems.append(f"frames={s['nb_read_frames']} (want {expect_frames})")
    if s["has_audio"]:
        problems.append("has an audio stream")
    status = "OK" if not problems else "FAIL: " + "; ".join(problems)
    print(f"{name:8s} {s['nb_read_frames']:>4} frames  {s['duration']:.3f}s  {s['codec_name']} {s['profile']} "
          f"{s['width']}x{s['height']} {s['r_frame_rate']} {s['pix_fmt']} "
          f"{s['color_space']}/{s['color_primaries']}/{s['color_transfer']}/{s['color_range']}  {status}")
    return problems


def decode_frames(path: Path, frames: list[int]) -> list[np.ndarray]:
    """Decode exact frame numbers with a BT.709 limited range conversion to RGB."""
    sel = "+".join(f"eq(n\\,{n})" for n in frames)
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf",
         f"select='{sel}',scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24",
         "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (1920 * 1080 * 3)
    arr = np.frombuffer(raw, np.uint8).reshape(n, 1080, 1920, 3)
    return [arr[i] for i in range(n)]


def contact_sheet(name: str, images: list[tuple[str, Image.Image]], cols: int = 3) -> Path:
    scale = 0.4
    w, h = int(1920 * scale), int(1080 * scale)
    rows = (len(images) + cols - 1) // cols
    head = 34
    sheet = Image.new("RGB", (cols * w + (cols + 1) * 10, rows * (h + head) + (rows + 1) * 10), (32, 34, 38))
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(images):
        x = 10 + (i % cols) * (w + 10)
        y = 10 + (i // cols) * (h + head + 10)
        brand.draw_text(d, x, y + 24, label, 24, 500, (230, 232, 236, 255))
        sheet.paste(im.resize((w, h), Image.Resampling.LANCZOS), (x, y + head))
    out = BUILD / f"{name}_contact.png"
    sheet.save(out)
    return out


def render_frame(scene, t: float) -> np.ndarray:
    c = engine.new_canvas(scene.background)
    scene.draw(c, t)
    return engine.to_rgb8(c)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-stills", action="store_true")
    args = ap.parse_args()
    STILLS.mkdir(parents=True, exist_ok=True)
    failures = 0
    print("Streams")
    for out_name, scene_name, dur, params in DEFAULTS:
        path = OUT_DIR / f"{out_name}.mp4"
        if not path.exists():
            print(f"{out_name:8s} MISSING")
            failures += 1
            continue
        failures += bool(check_stream(out_name, path, round(dur * 30)))

    print("\nSeams and holds (renderer, exact pixels)")
    intro = scenes.build("intro", 11.123)
    roles = scenes.build("roles", 12.257)
    a = render_frame(intro, (round(11.123 * 30) - 1) / 30)
    b = render_frame(roles, 0.0)
    diff = int(np.abs(a.astype(int) - b.astype(int)).max())
    print(f"intro last frame vs roles first frame: max diff {diff}  {'OK' if diff == 0 else 'FAIL'}")
    failures += diff != 0
    for out_name, scene_name, dur, params in DEFAULTS:
        sc = scenes.build(scene_name, dur, None, params)
        n = round(dur * 30)
        settle_idx = min(n - 1, int(np.ceil(sc.settle_time() * 30)))
        f1 = render_frame(sc, settle_idx / 30)
        f2 = render_frame(sc, (n - 1) / 30)
        f0 = render_frame(sc, 0.0)
        d = int(np.abs(f1.astype(int) - f2.astype(int)).max())
        bg = np.array(brand.rgb("surface"))
        start_dev = int(np.abs(f0.astype(int) - bg).max())
        print(f"{out_name:8s} settle {sc.settle_time():6.3f}s, settle frame vs last frame diff {d} "
              f"{'OK' if d == 0 else 'FAIL'}; first frame vs plain surface max diff {start_dev}")
        failures += d != 0

    if not args.no_stills:
        print("\nStills and contact sheets")
        enc_a = decode_frames(OUT_DIR / "intro.mp4", [round(11.123 * 30) - 1])[0]
        enc_b = decode_frames(OUT_DIR / "roles.mp4", [0])[0]
        print(f"encoded seam intro last vs roles first: max diff "
              f"{int(np.abs(enc_a.astype(int) - enc_b.astype(int)).max())}, mean "
              f"{np.abs(enc_a.astype(float) - enc_b.astype(float)).mean():.3f}")
        sheets = {}
        for out_name, scene_name, dur, params in DEFAULTS:
            times = KEY_TIMES.get(out_name, [])
            frames = [min(round(dur * 30) - 1, round(t * 30)) for t in times]
            imgs = decode_frames(OUT_DIR / f"{out_name}.mp4", sorted(set(frames)))
            by_frame = dict(zip(sorted(set(frames)), imgs))
            group = "step" if scene_name == "step" else out_name
            for t, fno in zip(times, frames):
                im = Image.fromarray(by_frame[fno])
                im.save(STILLS / f"{out_name}_{fno:04d}_{t:05.2f}s.png")
                sheets.setdefault(group, []).append((f"{out_name}  t={t:.2f}s  frame {fno}", im))
        for group, items in sheets.items():
            print(contact_sheet(group, items))
    print("\nFAILURES:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
