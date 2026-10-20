"""Archive the reviewed version 5 assets without private inputs or desktop captures."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'work/nanda-muse-wajo-demo'
SOURCE = ROOT / 'work/nanda-video/revision-v5'
manifest = json.loads((DEST / 'docs/archive-manifest.json').read_text())
entries = {row['path']: row for row in manifest['files']}
omitted = json.loads((DEST / 'docs/omitted-files.json').read_text())
omissions = {row['path']: row for row in omitted['files']}
copied = []

def copy(source, target, purpose):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    relative = target.relative_to(DEST).as_posix()
    entries[relative] = {
        'source': source.relative_to(ROOT).as_posix(),
        'path': relative,
        'bytes': target.stat().st_size,
        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'purpose': purpose,
    }
    copied.append(relative)

for source in sorted(SOURCE.rglob('*')):
    if not source.is_file():
        continue
    relative = source.relative_to(SOURCE)
    if any(part in {'private-input', 'research', '__pycache__', '.impeccable'} for part in relative.parts) or source.name == '.DS_Store':
        key = source.relative_to(ROOT).as_posix()
        omissions[key] = {'path': key, 'bytes': source.stat().st_size, 'reason': 'Private reference material or generated development cache'}
        continue
    copy(source, DEST / source.relative_to(ROOT), 'Version 5 animation, prompt, narration, editing source or validation record')

for source in sorted((ROOT / 'outputs/nanda-demo-v5').rglob('*')):
    if source.is_file():
        copy(source, DEST / source.relative_to(ROOT), 'Delivered version 5 video, guide, script, caption or extracted screenshot')

site = ROOT / 'work/nanda-messagebox-skill/demo'
copy(site / 'index.html', DEST / 'website/demo/index.html', 'Published page with revised video above historical videos')
for source in sorted((site / 'v5').rglob('*')):
    if source.is_file():
        copy(source, DEST / 'website/demo' / source.relative_to(site), 'Published version 5 guide and assets')

for name in ('package_v5.py', 'prepare_v5_site.py', 'qa_v5_site.cjs', 'v5-site-preservation.json', 'v5-site-qa.json', 'v5-live-verification.json'):
    source = ROOT / 'work/publication' / name
    if source.exists():
        copy(source, DEST / source.relative_to(ROOT), 'Version 5 publication source or validation record')

(DEST / 'docs/archive-manifest.json').write_text(json.dumps({'files': sorted(entries.values(), key=lambda row: row['path'])}, indent=2) + '\n')
omitted['files'] = sorted(omissions.values(), key=lambda row: row['path'])
(DEST / 'docs/omitted-files.json').write_text(json.dumps(omitted, indent=2) + '\n')
report = {'copied_files': len(copied), 'manifest_files': len(entries), 'copied_bytes': sum(entries[path]['bytes'] for path in copied), 'largest_copied_file_bytes': max(entries[path]['bytes'] for path in copied)}
print(json.dumps(report, indent=2))
