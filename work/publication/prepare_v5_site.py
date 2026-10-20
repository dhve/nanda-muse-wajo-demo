"""Add the revised walkthrough while preserving the existing demo page."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'work/nanda-messagebox-skill'
PAGE = SITE / 'demo/index.html'
SOURCE = ROOT / 'outputs/nanda-demo-v5'
baseline = subprocess.check_output(['git', 'show', 'HEAD:demo/index.html'], cwd=SITE).decode()
assert PAGE.read_text() == baseline, 'Existing demo page has unreviewed changes'
assert 'BEGIN KNOWN ID VIDEO V5' not in baseline
block = '''  <!-- BEGIN KNOWN ID VIDEO V5 -->
  <figure class="player" aria-labelledby="known-id-video-caption">
    <h2 style="font-size:24px;margin-bottom:16px">Connect agents using a known ID</h2>
    <div class="player-frame">
      <video controls preload="metadata" playsinline width="1920" height="1080" poster="v5/video/muse-wajo-demo-v5-poster.jpg">
        <source src="v5/video/muse-wajo-demo-v5.mp4" type="video/mp4">
        <track kind="captions" src="v5/video/muse-wajo-demo-v5.vtt" srclang="en" label="English">
        <p>Your browser cannot play this video. <a href="v5/video/muse-wajo-demo-v5.mp4">Download the revised walkthrough (MP4)</a>.</p>
      </video>
    </div>
    <figcaption id="known-id-video-caption">Revised animated bakery walkthrough, 2:28. A known agent ID resolves to its contact details, and the bakery can contact Bob later with his permission. Screens and addresses are illustrative. <a href="v5/">Follow the matching guide with prompts and screenshots</a>.</figcaption>
  </figure>
  <!-- END KNOWN ID VIDEO V5 -->

'''
anchor = '  <!-- BEGIN BAKERY VIDEO -->'
assert baseline.count(anchor) == 1
updated = baseline.replace(anchor, block + anchor, 1)
assert updated.replace(block, '', 1) == baseline
shutil.copytree(SOURCE, SITE / 'demo/v5', dirs_exist_ok=True)
PAGE.write_text(updated)
report = {
    'baseline_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SITE).decode().strip(),
    'baseline_page_sha256': hashlib.sha256(baseline.encode()).hexdigest(),
    'original_page_preserved': updated.replace(block, '', 1) == baseline,
    'new_guide': 'https://my.nandaindex.org/demo/v5/',
    'new_video': 'https://my.nandaindex.org/demo/v5/video/muse-wajo-demo-v5.mp4',
    'copied_files': len([p for p in SOURCE.rglob('*') if p.is_file()]),
}
(ROOT / 'work/publication/v5-site-preservation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
