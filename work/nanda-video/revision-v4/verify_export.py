from pathlib import Path
import json, subprocess, re, hashlib
from html.parser import HTMLParser
P=Path(__file__).resolve().parent
OUT=P.parents[2]/'outputs/nanda-demo-v4'
video=OUT/'video/muse-wajo-demo-v4.mp4'
data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
v=next(s for s in data['streams'] if s['codec_type']=='video')
a=next(s for s in data['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'])==(1920,1080)
assert v['avg_frame_rate']=='30/1'
assert 177.9<=float(data['format']['duration'])<180
assert a['codec_name']=='aac'
subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True)
class Assets(HTMLParser):
 def __init__(self):super().__init__();self.paths=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  for key in ['src','poster','data-image']:
   if key in attrs:self.paths.append(attrs[key])
parser=Assets();parser.feed((OUT/'index.html').read_text())
missing=[s for s in parser.paths if not s.startswith(('https:','data:')) and not (OUT/s).is_file()]
assert not missing,missing
captions=json.loads((P/'audio/timeline.json').read_text())['captions']
for c in captions:assert 0<=c['start']<c['end']<=178,c
for first,second in zip(captions,captions[1:]):assert first['end']<=second['start']
manifest=json.loads((P/'recording/screenshot-provenance.json').read_text())
for row in manifest['frames']:
 f=OUT/row['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']
report={'video':str(video.relative_to(P.parents[2])),'duration':float(data['format']['duration']),'resolution':[v['width'],v['height']],'fps':v['avg_frame_rate'],'audio_codec':a['codec_name'],'full_decode':'passed','missing_guide_assets':missing,'captions':len(captions),'screenshot_provenance_verified':len(manifest['frames']),'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest()}
(P/'export-qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
