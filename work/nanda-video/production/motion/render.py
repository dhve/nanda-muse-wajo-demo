#!/usr/bin/env python3
"""Motion renderer for the Muse and Wajo demo video (CONTRACT.md section 4).

  python3 motion/render.py --list
  python3 motion/render.py SCENE --out PATH.mp4 [--duration SEC] [--beats '{"name": sec}'] [--param key=value ...]
  python3 motion/render.py SCENE --still SEC --out PATH.png [same options]
  python3 motion/render.py --all            # default renders into motion/out/

Durations: extra time goes into the final hold; compression is allowed down to
the scene's "min" (settle time plus a short hold). --beats moves named beats
(seconds from scene start). --param lead=SEC delays every beat by SEC, which
adds a hold at the start (useful for crossfade handles at the head).
--beats also accepts @path/to/file.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (str(HERE.parent / "lib"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import engine  # noqa: E402
import scenes  # noqa: E402

OUT_DIR = HERE / "out"

# (output name, scene, duration, params) for --all. Durations are the slot lengths in CONTRACT section 6.
DEFAULTS = [
    ("intro", "intro", 11.123, {}),
    ("roles", "roles", 12.257, {}),
    *[(f"step{n}", "step", 3.0, {"number": n}) for n in range(1, 6)],
    ("closing", "closing", 16.808, {}),
    ("endcard", "endcard", 9.109, {}),
]


def parse_params(items: list[str]) -> dict:
    out = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--param expects key=value, got {item!r}")
        k, v = item.split("=", 1)
        out[k.strip()] = v
    return out


def parse_beats(value: str | None) -> dict:
    if not value:
        return {}
    if value.startswith("@"):
        value = Path(value[1:]).read_text()
    data = json.loads(value)
    if not isinstance(data, dict):
        raise SystemExit("--beats must be a JSON object of name: seconds")
    return {str(k): float(v) for k, v in data.items()}


def listing() -> dict:
    out = {}
    for name, cls in scenes.SCENES.items():
        out[name] = cls.describe()
    return out


def render_one(scene_name: str, out: Path, duration=None, beats=None, params=None, still=None,
               workers=None) -> dict:
    scene = scenes.build(scene_name, duration, beats, params)
    if still is not None:
        engine.render_still(scene, float(still), out)
        print(f"{scene_name}: still at {still}s -> {out}")
        return {"out": str(out)}
    desc = type(scene).describe()
    lead = float(scene.p.get("lead", 0.0))
    settle = scene.settle_time()
    if scene.duration + 1e-6 < settle:
        print(f"warning: {scene_name} duration {scene.duration:.3f}s is shorter than its settle time "
              f"{settle:.3f}s (min {desc['min'] + lead:.3f}s); the last motion will be cut", file=sys.stderr)
    spec = (scene_name, duration, beats, params)
    return engine.render_video(spec, scene, out, workers)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene", nargs="?", help=f"one of: {', '.join(scenes.SCENES)}")
    ap.add_argument("--list", action="store_true", help="print scenes, durations, beats and params as JSON")
    ap.add_argument("--all", action="store_true", help="render every default into motion/out/")
    ap.add_argument("--out", help="output .mp4 (or .png with --still)")
    ap.add_argument("--duration", type=float, help="seconds; extra time goes into the final hold")
    ap.add_argument("--beats", help='JSON object, e.g. \'{"agent_box": 5.2}\', or @file.json')
    ap.add_argument("--param", action="append", default=[], help="key=value (repeatable)")
    ap.add_argument("--still", type=float, help="render one frame at this time (seconds) to a PNG")
    ap.add_argument("--workers", type=int, help="render processes (default: CPU count minus 4, max 12)")
    args = ap.parse_args(argv)

    if args.list:
        print(json.dumps(listing(), indent=2))
        return 0

    if args.all:
        t0 = time.time()
        report = []
        for out_name, scene_name, dur, params in DEFAULTS:
            info = render_one(scene_name, OUT_DIR / f"{out_name}.mp4", dur, {}, params, workers=args.workers)
            report.append({"name": out_name, **info})
        (OUT_DIR / "renders.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"all done in {time.time() - t0:.1f}s")
        return 0

    if not args.scene:
        ap.error("give a SCENE, --list or --all")
    if not args.out:
        ap.error("--out is required")
    beats = parse_beats(args.beats)
    params = parse_params(args.param)
    try:
        render_one(args.scene, Path(args.out).resolve(), args.duration, beats, params, args.still, args.workers)
    except KeyError as e:
        print(f"error: {e.args[0]}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
