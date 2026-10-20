from pathlib import Path
import subprocess,json,hashlib,shutil
P=Path(__file__).resolve().parent;ROOT=P.parents[2];OUT=ROOT/'outputs/nanda-demo-v5';V=OUT/'video';S=OUT/'screenshots';V.mkdir(exist_ok=True);S.mkdir(exist_ok=True)
video=V/'muse-wajo-demo-v5.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(P/'recording/direct-render.mp4'),'-i',str(P/'narration.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(video)],check=True)
for ext in ['vtt','srt']:shutil.copy2(P/f'captions.{ext}',V/f'muse-wajo-demo-v5.{ext}')
scenes=json.loads((P/'scenes.json').read_text())['scenes'];shots=[]
for s in scenes:
 ratio=.17 if s['id']=='verify' else .85
 t=s['start']+s['duration']*ratio;dest=S/(s['id']+'.jpg')
 subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2',str(dest)],check=True)
 shots.append({'scene':s['id'],'video_time_seconds':round(t,6),'file':dest.relative_to(OUT).as_posix(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
shutil.copy2(S/'resolve.jpg',V/'muse-wajo-demo-v5-poster.jpg')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));vs=next(s for s in probe['streams'] if s['codec_type']=='video');aud=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert vs['width']==1920 and vs['height']==1080 and vs['r_frame_rate']=='30/1';assert float(probe['format']['duration'])<180;assert aud['codec_name']=='aac'
metadata={'video':video.relative_to(OUT).as_posix(),'duration':float(probe['format']['duration']),'width':vs['width'],'height':vs['height'],'fps':30,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'screenshots':shots,'source':'Screenshots extracted directly from final exported MP4; no separate recreation.'}
(OUT/'screenshot-provenance.json').write_text(json.dumps(metadata,indent=2)+'\n');(P/'export-qa.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps({k:v for k,v in metadata.items() if k!='screenshots'},indent=2))
