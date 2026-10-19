"""Add reviewed v4 deliverables to the existing archive without copying private captures."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'work/nanda-muse-wajo-demo'
SOURCE=ROOT/'work/nanda-video/revision-v4'
manifest=json.loads((DEST/'docs/archive-manifest.json').read_text())
entries={r['path']:r for r in manifest['files']}
omitted=json.loads((DEST/'docs/omitted-files.json').read_text())
omissions={r['path']:r for r in omitted['files']}
recording={'direct-render.mp4','direct-render.json','recorded-visuals.mp4','screenshot-provenance.json','qr-final-frame.jpg','direct-contact.jpg','guide-contact.jpg'}
copied=[]

def copy(source,target,purpose):
 target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(source,target)
 if source==SOURCE/'feedback.md':
  text=target.read_text()
  target.write_text(re.sub(r'\| Oct (\d+), [^|]+ \|',r'| Oct \1, team feedback |',text))
 relative=target.relative_to(DEST).as_posix()
 entries[relative]={'source':source.relative_to(ROOT).as_posix(),'path':relative,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'purpose':purpose}
 copied.append(relative)

for f in sorted(SOURCE.rglob('*')):
 if not f.is_file():continue
 rel=f.relative_to(SOURCE)
 reason=None
 if rel.parts[0] in {'private-input','research'}:reason='Private feedback attachments, source chat or reference inspection material'
 elif any(part in {'__pycache__','.impeccable'} for part in rel.parts) or f.name=='.DS_Store':reason='Operating-system, development hook or Python cache'
 elif rel.parts[0]=='recording' and f.name not in recording:reason='Private desktop capture or superseded capture intermediate; final animation render included'
 if reason:
  name=f.relative_to(ROOT).as_posix()
  omissions[name]={'path':name,'bytes':f.stat().st_size,'reason':reason}
  entries.pop(name,None)
  continue
 copy(f,DEST/f.relative_to(ROOT),'Animated bakery source, narration, final render or validation record')

# Remove only the obsolete untracked copy created during preparation of this release.
stale=DEST/'work/nanda-video/revision-v4/recording/direct-render.webm'
if stale.exists():
 tracked=subprocess.run(['git','ls-files','--error-unmatch',str(stale.relative_to(DEST))],cwd=DEST,capture_output=True).returncode==0
 assert not tracked,'Refusing to remove a tracked archive file'
 stale.unlink()
 entries.pop(stale.relative_to(DEST).as_posix(),None)

out=ROOT/'outputs/nanda-demo-v4'
for f in sorted(out.rglob('*')):
 if f.is_file():copy(f,DEST/f.relative_to(ROOT),'Delivered bakery guide, final video or extracted screenshot')
for f in [ROOT/'outputs/nanda-demo-v4.zip',*sorted((ROOT/'outputs/nanda-demo-video').glob('muse-wajo-demo-v4.*'))]:
 copy(f,DEST/f.relative_to(ROOT),'Delivered bakery video, captions or guide package')
site=ROOT/'work/nanda-messagebox-skill/demo'
for f in sorted(site.rglob('*')):
 if f.is_file() and '__pycache__' not in f.parts:
  copy(f,DEST/'website/demo'/f.relative_to(site),'Published website source and assets')
copy(Path(__file__),DEST/'work/publication/package_v4.py','Archive packaging source')
(DEST/'docs/archive-manifest.json').write_text(json.dumps({'files':sorted(entries.values(),key=lambda r:r['path'])},indent=2)+'\n')
omitted['files']=sorted(omissions.values(),key=lambda r:r['path'])
(DEST/'docs/omitted-files.json').write_text(json.dumps(omitted,indent=2)+'\n')
print(json.dumps({'copied_files':len(copied),'manifest_files':len(entries),'manifest_bytes':sum(r['bytes'] for r in entries.values()),'largest_file_bytes':max(r['bytes'] for r in entries.values())},indent=2))
