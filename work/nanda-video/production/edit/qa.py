#!/opt/homebrew/bin/python3
"""QA for an assembled Muse and Wajo MP4, checked against edit/edl.json (CONTRACT section 8).

Usage (from claude/):

  python3 edit/qa.py                                        checks out/test/muse-wajo-test.mp4
  python3 edit/qa.py out/final/muse-wajo-demo.mp4 --mode final
  python3 edit/qa.py --no-whisper                           skip the speech transcript

Checks: EDL timeline, duration and frame count, stream format, full decode, captions (banned
word, dashes, embedded track), narration text, onscreen text dashes, placeholders and stubs,
evidence footage, privacy review, narration identity (decoded output audio against the source
WAV: lag, correlation, gain, residual), loudness and true peak, longest silent gap, an optional
whisper-cli transcript, and a contact sheet with one labeled frame per segment midpoint.

Writes qa_report.json and contact_sheet.png next to the checked MP4. Exit code 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assemble as asm  # noqa: E402  (shared EDL plan, paths and probes)

brand = asm.brand
ROOT, FPS, W, H = asm.ROOT, asm.FPS, asm.W, asm.H
FFMPEG, FFPROBE = asm.FFMPEG, asm.FFPROBE
QA_WORK = asm.BUILD / "qa"
WHISPER_MODEL = Path("~/.whisper-models/ggml-small.en.bin").expanduser()
DASHES = {"\u2012": "figure dash", "\u2013": "en dash", "\u2014": "em dash", "\u2015": "horizontal bar"}
BANNED = "nanda"


class Report:
    def __init__(self):
        self.checks: list[dict] = []

    def add(self, name: str, status: str, detail: str, **data) -> None:
        self.checks.append({"name": name, "status": status, "detail": detail, "data": data})
        print(f"  {status:4}  {name:18} {detail}", flush=True)

    def overall(self) -> str:
        states = {c["status"] for c in self.checks}
        return "FAIL" if "FAIL" in states else "WARN" if "WARN" in states else "PASS"


def sh(cmd: list[str], timeout: float | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def parse_srt(text: str) -> list[dict]:
    cues = []
    for block in re.split(r"\n\s*\n", text.strip().replace("\r\n", "\n")):
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1])
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        cues.append({"start": g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
                     "end": g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000,
                     "text": " ".join(x.strip() for x in lines[2:])})
    return cues


def parse_vtt(text: str) -> list[dict]:
    body = re.sub(r"^WEBVTT[^\n]*\n", "", text.strip().replace("\r\n", "\n"))
    return parse_srt(body)


def text_issues(text: str, banned: bool = True) -> list[str]:
    out = []
    if banned and BANNED in text.lower():
        out.append(f"contains '{BANNED}'")
    for ch, name in DASHES.items():
        if ch in text:
            out.append(f"contains an {name}")
    return out


def all_strings(obj, path="") -> list[tuple[str, str]]:
    if isinstance(obj, str):
        return [(path, obj)]
    if isinstance(obj, dict):
        return [x for k, v in obj.items() for x in all_strings(v, f"{path}.{k}" if path else k)]
    if isinstance(obj, list):
        return [x for i, v in enumerate(obj) for x in all_strings(v, f"{path}[{i}]")]
    return []


def decode_audio(path: Path, channels: int) -> np.ndarray:
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-map", "0:a:0", "-f", "f32le",
                          "-acodec", "pcm_f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").reshape(-1, channels)


def best_lag(ref: np.ndarray, sig: np.ndarray, max_lag: int) -> int:
    """Lag (samples) that best aligns sig to ref, from an FFT cross-correlation."""
    n = min(len(ref), len(sig))
    a, b = ref[:n].astype(np.float64), sig[:n].astype(np.float64)
    size = 1 << (2 * n - 1).bit_length()
    xc = np.fft.irfft(np.fft.rfft(b, size) * np.conj(np.fft.rfft(a, size)), size)
    lags = np.concatenate([xc[: max_lag + 1], xc[-max_lag:]])
    idx = int(np.argmax(lags))
    return idx if idx <= max_lag else idx - (2 * max_lag + 1)


def narration_metrics(src: np.ndarray, out: np.ndarray, sr: int = 48000) -> dict:
    """Compare decoded output audio (n x 2) with the source narration (mono) after aligning them.
    AAC at 256 kb/s leaves a residual near -42 dB; any trim, tempo, gain or filter shows up
    as a lag, a length change, a lower correlation, a gain offset or a larger residual."""
    lag = best_lag(src, out[:, 0], sr // 2)
    s0, o0 = (-lag, 0) if lag < 0 else (0, lag)      # out[n + lag] lines up with src[n]
    n = min(len(src) - s0, len(out) - o0)
    sl = src[s0:s0 + n].astype(np.float64)
    left = out[o0:o0 + n, 0].astype(np.float64)
    right = out[o0:o0 + n, 1].astype(np.float64)
    rms = lambda x: float(np.sqrt(np.mean(x ** 2)))
    db = lambda x: 20 * math.log10(max(1e-12, x))
    rms_s = rms(sl)
    return {
        "lag_samples": int(lag),
        "correlation": float(min(np.corrcoef(sl, left)[0, 1], np.corrcoef(sl, right)[0, 1])),
        "gain_db": max((db(rms(left) / rms_s), db(rms(right) / rms_s)), key=abs),
        "residual_db": max(db(rms(left - sl) / rms_s), db(rms(right - sl) / rms_s)),
        "left_minus_right_db": db(rms(left - right) / rms_s),  # the two AAC copies differ by codec noise only
        "length_diff_ms": (len(out) - len(src)) / sr * 1000,
    }


def narration_verdict(m: dict) -> tuple[str, str]:
    """PASS for an untouched narration encoded to AAC, FAIL for any real edit."""
    limits = [
        (abs(m["lag_samples"]) <= 48, "lag above 1 ms"),
        (m["correlation"] >= 0.999, "correlation below 0.999"),
        (abs(m["gain_db"]) <= 0.1, "gain changed by more than 0.1 dB"),
        (m["residual_db"] <= -30.0, "residual above -30 dB"),
        (m["left_minus_right_db"] <= -40.0, "left and right differ"),
        (abs(m["length_diff_ms"]) <= 2000 / FPS, "length differs by more than 2 frames"),
    ]
    failed = [why for ok, why in limits if not ok]
    detail = (f"lag {m['lag_samples']} samples, correlation {m['correlation']:.5f}, gain {m['gain_db']:+.3f} dB, "
              f"residual {m['residual_db']:.1f} dB, left minus right {m['left_minus_right_db']:.1f} dB, "
              f"length {m['length_diff_ms']:+.1f} ms")
    return ("FAIL", "; ".join(failed) + " (" + detail + ")") if failed else ("PASS", detail)


def ebur128(path: Path, dualmono: bool = False) -> dict:
    af = "ebur128=peak=true" + (":dualmono=true" if dualmono else "")
    out = sh([FFMPEG, "-nostats", "-hide_banner", "-i", str(path), "-map", "0:a:0", "-af", af,
              "-f", "null", "-"]).stderr
    summary = out[out.rfind("Summary:"):]
    i = re.search(r"I:\s*(-?[\d.]+|-inf)\s*LUFS", summary)
    lra = re.search(r"LRA:\s*(-?[\d.]+)\s*LU", summary)
    tp = re.search(r"True peak:\s*Peak:\s*(-?[\d.]+|-inf)\s*dBFS", summary, re.S)
    f = lambda m: float(m.group(1)) if m and m.group(1) != "-inf" else None
    return {"integrated_lufs": f(i), "lra_lu": f(lra), "true_peak_dbtp": f(tp)}


def silences(path: Path, noise_db: float = -50.0, min_d: float = 0.3) -> list[tuple[float, float]]:
    out = sh([FFMPEG, "-nostats", "-hide_banner", "-i", str(path), "-map", "0:a:0", "-af",
              f"silencedetect=noise={noise_db}dB:d={min_d}", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?[\d.]+)", out)]
    pairs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        pairs.append((max(0.0, s), e))
    return pairs


def grab_frame(mp4: Path, t: float, size: tuple[int, int]) -> Image.Image:
    out = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.4f}", "-i", str(mp4), "-frames:v", "1",
                          "-vf", f"scale={size[0]}:{size[1]}:flags=area", "-f", "image2pipe",
                          "-vcodec", "png", "-"], capture_output=True)
    if out.returncode != 0 or not out.stdout:
        img = Image.new("RGB", size, (60, 0, 0))
        ImageDraw.Draw(img).text((10, 10), "frame grab failed", fill=(255, 255, 255))
        return img
    return Image.open(io.BytesIO(out.stdout)).convert("RGB")


def label(img: Image.Image, text: str, x: float, baseline: float, size: float, weight: int, color: str):
    spr, base = brand.rich_text_image(text, size, weight, color)
    img.alpha_composite(spr, (round(x - math.ceil(size * 0.08)), round(baseline - base)))


def contact_sheet(mp4: Path, plan: list, kinds: dict, out_png: Path, title: str) -> Path:
    cols, cw, chh, lab, gap, head = 4, 464, 261, 70, 16, 96
    rows = math.ceil(len(plan) / cols)
    sheet = Image.new("RGBA", (cols * cw + (cols + 1) * gap, head + rows * (chh + lab + gap) + gap),
                      brand.rgba("surface"))
    label(sheet, title, gap + 4, 58, 32, 600, "navy")
    for i, s in enumerate(plan):
        mid = (s.f0 + s.f1) // 2
        frame = grab_frame(mp4, mid / FPS + 0.001, (cw, chh))
        x = gap + (i % cols) * (cw + gap)
        y = head + (i // cols) * (chh + lab + gap)
        sheet.alpha_composite(brand.rounded_box(cw + 4, chh + 4, 6, "line_strong"), (x - 2, y - 2))
        sheet.paste(frame, (x, y))
        kind = kinds.get(s.id, s.kind)
        color = "brand_600" if kind in ("capture", "motion_render", "motion_prerender") else "ink_medium"
        label(sheet, f"{s.idx:02d}  {s.id}  ({kind})", x, y + chh + 30, 24, 600, color)
        label(sheet, f"{s.data['start']:.3f} to {s.data['end']:.3f} s, frame at {mid / FPS:.2f} s",
              x, y + chh + 60, 22, 500, "ink_medium")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_png)
    return out_png


def banned_like(words: list[str]) -> list[str]:
    hits = []
    norm = [re.sub(r"[^a-z]", "", w.lower()) for w in words]
    for i, w in enumerate(norm):
        if not w:
            continue
        if BANNED in w or difflib.SequenceMatcher(None, w, BANNED).ratio() >= 0.8:
            hits.append(words[i])
        if i + 1 < len(norm) and norm[i + 1]:
            pair = w + norm[i + 1]
            if pair == BANNED or (len(pair) <= 7 and difflib.SequenceMatcher(None, pair, BANNED).ratio() >= 0.9):
                hits.append(f"{words[i]} {words[i + 1]}")
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="QA an assembled MP4 against the EDL.")
    ap.add_argument("mp4", nargs="?", help="output to check (default: the EDL test output)")
    ap.add_argument("--mode", choices=["test", "final"], help="default: from the manifest")
    ap.add_argument("--edl", default=str(asm.DEFAULT_EDL))
    ap.add_argument("--no-whisper", action="store_true", help="skip the whisper-cli transcript")
    ap.add_argument("--whisper-timeout", type=float, default=420.0)
    args = ap.parse_args(argv)

    edl_path = Path(args.edl).resolve()
    edl = asm.load_edl(edl_path)
    mp4 = Path(args.mp4).resolve() if args.mp4 else asm.rpath(edl["outputs"]["test"])
    if not mp4.exists():
        print(f"no such file: {mp4}")
        return 2
    manifest_path = mp4.with_suffix(".manifest.json")
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    mode = args.mode or (manifest or {}).get("mode") or ("final" if "final" in mp4.parts else "test")
    final = mode == "final"
    out_dir = mp4.parent
    QA_WORK.mkdir(parents=True, exist_ok=True)
    rep = Report()
    t_start = time.time()
    print(f"QA for {asm.show(mp4)} (mode {mode})")

    # EDL timeline -----------------------------------------------------------------------
    narration = asm.rpath(edl["narration"]["file"])
    nar_dur = asm.probe_audio_duration(narration)
    plan = asm.build_plan(edl)
    total = plan[-1].f1
    max_dur = float((edl.get("format") or {}).get("max_duration", 180.0))
    problems = []
    if abs(total - nar_dur * FPS) > 1.0:
        problems.append(f"timeline {total} frames vs narration {nar_dur * FPS:.2f}")
    for s in plan:
        if abs(s.data["start"] * FPS - s.f0) > 0.5 + 1e-6 or abs(s.data["end"] * FPS - s.f1) > 0.5 + 1e-6:
            problems.append(f"{s.id} boundary not on the nearest frame")
    rep.add("edl_timeline", "FAIL" if problems else "PASS",
            "; ".join(problems) or f"{len(plan)} contiguous segments, {total} frames, "
                                    f"{sum(s.trans_in.startswith('xfade') for s in plan)} crossfades, "
                                    f"{sum(s.trans_in == 'cut' for s in plan)} cut",
            frames=total, narration_frames=round(nar_dur * FPS, 3))
    if manifest:
        same = manifest.get("edl_sha256") == hashlib.sha256(edl_path.read_bytes()).hexdigest()
        rep.add("manifest", "PASS" if same else "WARN",
                "manifest matches the current EDL" if same else "the EDL changed after this render, rerun assemble",
                manifest=asm.show(manifest_path))
    else:
        rep.add("manifest", "FAIL" if final else "WARN", f"no manifest next to the MP4 ({manifest_path.name})")

    # Duration and streams ----------------------------------------------------------------
    pr = json.loads(sh([FFPROBE, "-v", "error", "-show_entries",
                        "format=duration:stream=index,codec_type,codec_name,profile,width,height,pix_fmt,"
                        "r_frame_rate,avg_frame_rate,sample_rate,channels,bit_rate,duration,color_space,"
                        "color_primaries,color_transfer,color_range,sample_aspect_ratio:stream_tags=language",
                        "-of", "json", str(mp4)]).stdout)
    streams = pr.get("streams", [])
    v = next((s for s in streams if s["codec_type"] == "video"), {})
    a = next((s for s in streams if s["codec_type"] == "audio"), {})
    sub = next((s for s in streams if s["codec_type"] == "subtitle"), {})
    fmt_dur = float(pr.get("format", {}).get("duration", 0))
    v_frames = asm.count_frames(mp4)
    v_dur = v_frames / FPS
    ok = fmt_dur <= max_dur and abs(v_dur - nar_dur) <= 2 / FPS + 1e-9 and v_frames == total
    rep.add("duration", "PASS" if ok else "FAIL",
            f"file {fmt_dur:.3f} s (max {max_dur:g}), video {v_frames} frames = {v_dur:.3f} s, "
            f"narration {nar_dur:.3f} s, difference {(v_dur - nar_dur) * 1000:+.1f} ms, expected {total} frames",
            file_s=fmt_dur, video_frames=v_frames, narration_s=nar_dur)
    want_v = {"codec_name": "h264", "width": W, "height": H, "pix_fmt": "yuv420p",
              "r_frame_rate": f"{FPS}/1", "avg_frame_rate": f"{FPS}/1"}
    bad = [f"{k}={v.get(k)}" for k, val in want_v.items() if v.get(k) != val]
    if v.get("profile") not in ("High", "high"):
        bad.append(f"profile={v.get('profile')}")
    color = [v.get("color_space"), v.get("color_primaries"), v.get("color_transfer"), v.get("color_range")]
    if color != ["bt709", "bt709", "bt709", "tv"]:
        bad.append(f"color={color}")
    rep.add("video_stream", "FAIL" if bad else "PASS", ", ".join(bad) or
            f"h264 {v.get('profile')} {W}x{H} yuv420p 30 fps CFR, BT.709 tv", stream=v)
    bad = []
    if a.get("codec_name") != "aac":
        bad.append(f"codec={a.get('codec_name')}")
    if str(a.get("sample_rate")) != "48000":
        bad.append(f"rate={a.get('sample_rate')}")
    if a.get("channels") != 2:
        bad.append(f"channels={a.get('channels')}")
    rate = int(a.get("bit_rate") or 0)
    rep.add("audio_stream", "FAIL" if bad else "PASS", ", ".join(bad) or
            f"aac 48 kHz stereo, {rate / 1000:.0f} kb/s", stream=a)
    rep.add("subtitle_stream", "PASS" if sub.get("codec_name") == "mov_text" else "FAIL",
            f"{sub.get('codec_name', 'missing')} ({(sub.get('tags') or {}).get('language', 'no language')})",
            stream=sub)

    # Full decode -------------------------------------------------------------------------
    t0 = time.time()
    dec = sh([FFMPEG, "-v", "error", "-i", str(mp4), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"])
    errs = (dec.stderr or "").strip()
    rep.add("decode", "FAIL" if errs or dec.returncode else "PASS",
            (errs.splitlines()[0] if errs else "no decoder errors") + f" ({time.time() - t0:.1f} s)")

    # Captions and narration text ---------------------------------------------------------
    srt_src = asm.rpath(edl["captions"]["srt"])
    src_cues = parse_srt(srt_src.read_text(encoding="utf-8"))
    issues = []
    for i, c in enumerate(src_cues, 1):
        for p in text_issues(c["text"]):
            issues.append(f"source cue {i} {p}")
    side_srt, side_vtt = mp4.with_suffix(".srt"), mp4.with_suffix(".vtt")
    if not side_srt.exists() or asm.md5_file(side_srt) != asm.md5_file(srt_src):
        issues.append("sidecar .srt missing or not identical to the source captions")
    if side_vtt.exists():
        vtt_cues = parse_vtt(side_vtt.read_text(encoding="utf-8"))
        if [(c["start"], c["end"], c["text"]) for c in vtt_cues] != \
                [(c["start"], c["end"], c["text"]) for c in src_cues]:
            issues.append("sidecar .vtt cues differ from the source")
    else:
        issues.append("sidecar .vtt missing")
    emb = sh([FFMPEG, "-v", "error", "-i", str(mp4), "-map", "0:s:0", "-f", "srt", "-"])
    emb_cues = parse_srt(emb.stdout) if emb.returncode == 0 else []
    if [c["text"] for c in emb_cues] != [c["text"] for c in src_cues]:
        issues.append(f"embedded track has {len(emb_cues)} cues, text differs from the source")
    else:
        drift = max(abs(e["start"] - s["start"]) for e, s in zip(emb_cues, src_cues))
        if drift > 0.002:
            issues.append(f"embedded cue starts drift by up to {drift * 1000:.0f} ms")
    for i, c in enumerate(emb_cues, 1):
        for p in text_issues(c["text"]):
            issues.append(f"embedded cue {i} {p}")
    rep.add("captions", "FAIL" if issues else "PASS", "; ".join(issues[:4]) or
            f"{len(src_cues)} cues, no '{BANNED}', no em or en dashes; sidecar srt identical, vtt and "
            f"embedded mov_text match", cues=len(src_cues), issues=issues)
    nar_txt = ROOT.parent / "narration.txt"
    if nar_txt.exists():
        p = text_issues(nar_txt.read_text(encoding="utf-8"))
        rep.add("narration_text", "FAIL" if p else "PASS", ", ".join(p) or f"{asm.show(nar_txt)} clean")

    # Onscreen text -----------------------------------------------------------------------
    bad = [f"{k}: {', '.join(text_issues(s, banned=False))}" for k, s in all_strings(edl)
           if text_issues(s, banned=False)]
    listing = asm.Context(edl, mode).motion_list()
    n_motion = 0
    if listing:
        for k, s in all_strings(listing):
            n_motion += 1
            if text_issues(s, banned=False):
                bad.append(f"motion --list {k}: {', '.join(text_issues(s, banned=False))}")
    bad += [f"{s.id} say: contains '{BANNED}'" for s in plan if BANNED in (s.data.get("say") or "").lower()]
    rep.add("onscreen_text", "FAIL" if bad else "PASS", "; ".join(bad[:4]) or
            f"no em or en dashes in {len(all_strings(edl))} EDL strings"
            + (f" or {n_motion} motion scene strings" if listing else ""), issues=bad)

    # Placeholders, evidence, privacy -----------------------------------------------------
    if manifest:
        ph = [s["id"] for s in manifest["segments"] if s["source_kind"] == "capture_placeholder"]
        st = [s["id"] for s in manifest["segments"] if s["source_kind"] == "motion_stub"]
        pre = [s["id"] for s in manifest["segments"] if s["source_kind"] == "motion_prerender"]
        status = "PASS" if not ph and not st else ("FAIL" if final else "WARN")
        detail = f"{len(ph)} capture placeholders, {len(st)} motion stubs"
        if ph:
            detail += f" ({', '.join(ph)})"
        if st:
            detail += f"; stubs: {', '.join(st)}"
        if pre:
            detail += f"; prerendered motion (beats not applied): {', '.join(pre)}"
        rep.add("placeholders", status, detail, placeholders=ph, stubs=st, prerendered=pre)
    else:
        rep.add("placeholders", "FAIL" if final else "WARN", "unknown, no manifest")
    caps = [s for s in plan if s.kind == "capture"]
    tag_files: dict[str, list[str]] = {}
    missing = []
    for s in caps:
        f = asm.find_capture(s)
        for tag in s.data.get("evidence") or []:
            tag_files.setdefault(tag, [])
            if f:
                tag_files[tag].append(f"{s.id}:{asm.show(f)}")
            else:
                missing.append(f"{tag} ({s.id})")
    required = edl.get("evidence_required") or []
    uncovered = [t for t in required if not tag_files.get(t)]
    status = "PASS" if not missing and not uncovered else ("FAIL" if final else "WARN")
    rep.add("evidence", status,
            (f"required tags without footage: {', '.join(uncovered)}" if uncovered else "every required tag has footage")
            + (f"; {len(missing)} tag(s) point at missing files" if missing else ""),
            files=tag_files, missing=missing, uncovered=uncovered)
    pending = [s.id for s in caps if s.data.get("privacy_check", "done") != "done"]
    boxes = {s.id: len(s.data.get("redact") or []) for s in caps if s.data.get("privacy_check")}
    rep.add("privacy", "PASS" if not pending else ("FAIL" if final else "WARN"),
            ("privacy_check pending on " + ", ".join(pending)) if pending else "all privacy checks done",
            redact_boxes=boxes)

    # Narration identity ------------------------------------------------------------------
    want_md5 = edl["narration"].get("md5")
    have_md5 = asm.md5_file(narration)
    rep.add("narration_source", "PASS" if have_md5 == want_md5 else "FAIL",
            f"md5 {have_md5}" + ("" if have_md5 == want_md5 else f" (EDL expects {want_md5})"))
    try:
        m = narration_metrics(decode_audio(narration, 1)[:, 0], decode_audio(mp4, 2))
        status, detail = narration_verdict(m)
        rep.add("narration_match", status, detail, **m)
    except Exception as e:  # noqa: BLE001
        rep.add("narration_match", "FAIL", f"could not compare audio: {e}")

    src_l = ebur128(narration, dualmono=True)
    out_l = ebur128(mp4)
    di = (out_l["integrated_lufs"] or 0) - (src_l["integrated_lufs"] or 0)
    tp = out_l["true_peak_dbtp"]
    status = "FAIL" if abs(di) > 0.5 else "WARN" if abs(di) > 0.2 or (tp is not None and tp > -1.0) else "PASS"
    rep.add("loudness", status,
            f"output {out_l['integrated_lufs']} LUFS (source as dual mono {src_l['integrated_lufs']} LUFS, "
            f"difference {di:+.2f} LU), true peak {tp} dBTP (source {src_l['true_peak_dbtp']}), "
            f"LRA {out_l['lra_lu']} LU", output=out_l, source_dualmono=src_l)
    gaps = silences(mp4)
    longest = max(((e if e is not None else fmt_dur) - s, s) for s, e in gaps) if gaps else (0.0, 0.0)
    rep.add("silence", "WARN" if longest[0] > 4.5 else "PASS",
            f"longest silent gap {longest[0]:.2f} s at {longest[1]:.2f} s ({len(gaps)} gaps of 0.3 s or more "
            f"below -50 dBFS)", longest_s=longest[0], at_s=longest[1], gaps=len(gaps))

    # Spoken words (optional) --------------------------------------------------------------
    whisper = shutil.which("whisper-cli")
    if args.no_whisper:
        rep.add("spoken_words", "SKIP", "skipped (--no-whisper)")
    elif not whisper or not WHISPER_MODEL.exists():
        rep.add("spoken_words", "SKIP", "whisper-cli or the model is not available")
    else:
        wav = QA_WORK / "whisper_16k.wav"
        base = QA_WORK / f"whisper_{mp4.stem}"
        try:
            subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(mp4), "-map", "0:a:0", "-ac", "1", "-ar",
                            "16000", "-c:a", "pcm_s16le", str(wav)], check=True)
            t0 = time.time()
            wr = subprocess.run([whisper, "-m", str(WHISPER_MODEL), "-f", str(wav), "-l", "en", "-nt", "-np",
                                 "-otxt", "-of", str(base)], capture_output=True, text=True,
                                timeout=args.whisper_timeout)
            text = base.with_suffix(".txt").read_text(encoding="utf-8") if wr.returncode == 0 else ""
            words = text.split()
            hits = banned_like(words)
            script = nar_txt.read_text(encoding="utf-8").split() if nar_txt.exists() else []
            norm = lambda ws: [re.sub(r"[^a-z0-9]", "", w.lower()) for w in ws]
            sim = difflib.SequenceMatcher(None, norm(script), norm(words), autojunk=False).ratio() if script else 0
            if wr.returncode != 0:
                rep.add("spoken_words", "WARN", f"whisper-cli failed (exit {wr.returncode})")
            else:
                rep.add("spoken_words", "FAIL" if hits else "PASS",
                        (f"nanda-like words heard: {', '.join(hits)}" if hits else f"no {BANNED}-like word heard")
                        + f"; {len(words)} words, {sim:.0%} word match to narration.txt ({time.time() - t0:.0f} s)",
                        hits=hits, similarity=sim, transcript=str(base.with_suffix(".txt")))
        except subprocess.TimeoutExpired:
            rep.add("spoken_words", "SKIP", f"whisper-cli took longer than {args.whisper_timeout:.0f} s, skipped")
        except Exception as e:  # noqa: BLE001
            rep.add("spoken_words", "WARN", f"whisper check failed: {e}")

    # Contact sheet -----------------------------------------------------------------------
    kinds = {s["id"]: s["source_kind"] for s in (manifest or {}).get("segments", [])}
    sheet = contact_sheet(mp4, plan, kinds, out_dir / "contact_sheet.png",
                          f"{mp4.name}   mode {mode}   {total} frames   one frame per segment midpoint")
    rep.add("contact_sheet", "PASS", asm.show(sheet))

    overall = rep.overall()
    counts = {k: sum(c["status"] == k for c in rep.checks) for k in ("PASS", "WARN", "FAIL", "SKIP")}
    report = {"output": asm.show(mp4), "mode": mode, "created": time.strftime("%Y-%m-%d %H:%M:%S"),
              "overall": overall, "counts": counts, "seconds": round(time.time() - t_start, 1),
              "checks": rep.checks}
    report_path = out_dir / "qa_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")
    print(f"Overall: {overall} ({counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['PASS']} PASS, "
          f"{counts['SKIP']} SKIP) in {report['seconds']:.0f} s")
    print(f"Report: {asm.show(report_path)}")
    print(f"Contact sheet: {asm.show(sheet)}")
    return 1 if overall == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
