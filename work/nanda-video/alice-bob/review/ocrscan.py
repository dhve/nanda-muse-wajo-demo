"""OCR a crop of a source recording across a time window (read only on the source).

  python3 ocrscan.py SOURCE x y w h START END STEP
Prints one line per sampled time: the time and the recognized text (rows joined with ' | ').
"""
import json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = HERE.parents[1] / "captures"


def scan(src, box, start, end, step):
    x, y, w, h = box
    with tempfile.TemporaryDirectory() as tmp:
        n = int(round((end - start) / step)) + 1
        times = [round(start + i * step, 3) for i in range(n)]
        files = []
        for i, t in enumerate(times):
            out = f"{tmp}/f{i:04d}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(CAP / src),
                            "-frames:v", "1", "-vf", f"crop={w}:{h}:{x}:{y}", out], check=True)
            files.append(out)
        res = subprocess.run([str(HERE / "ocr"), *files], capture_output=True, text=True, check=True)
        texts = {Path(j["file"]).name: j["text"] for j in map(json.loads, res.stdout.splitlines())}
        return [(t, texts.get(Path(f).name, "").replace("\n", " | ")) for t, f in zip(times, files)]


if __name__ == "__main__":
    src = sys.argv[1]
    box = [int(v) for v in sys.argv[2:6]]
    for t, text in scan(src, box, float(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8])):
        print(f"{t:9.3f}  {text}")
