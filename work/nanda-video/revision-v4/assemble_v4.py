"""Assemble the animation render and extract guide stills from that same footage."""
from pathlib import Path
import argparse, subprocess, json, hashlib, shutil
P=Path(__file__).resolve().parent
OUT=P.parents[2]/'outputs/nanda-demo-v4'
parser=argparse.ArgumentParser();parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--start',type=float,required=True);parser.add_argument('--crop',required=True,help='width:height:x:y in source pixels');args=parser.parse_args()
for folder in [OUT/'video',OUT/'screenshots',P/'recording']:folder.mkdir(parents=True,exist_ok=True)
video=OUT/'video/muse-wajo-demo-v4.mp4'
subprocess.run(['ffmpeg','-y','-v','warning','-ss',str(args.start),'-i',str(args.raw),'-i',str(P/'narration.wav'),'-i',str(P/'captions.srt'),'-filter_complex',f"[0:v]crop={args.crop},fps=30,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[v]",'-map','[v]','-map','1:a:0','-map','2:0','-t','178','-c:v','libx264','-preset','medium','-crf','18','-c:a','aac','-b:a','160k','-c:s','mov_text','-metadata:s:s:0','language=eng','-disposition:s:0','0','-movflags','+faststart',str(video)],check=True)
visual=P/'recording/recorded-visuals.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-i',str(video),'-map','0:v:0','-c','copy',str(visual)],check=True)
frames=[('screenshots/connect-alice.jpg',21.5),('screenshots/connect-bob.jpg',33),('screenshots/verify.jpg',47.5),('screenshots/ready.jpg',58),('screenshots/discover.jpg',72.5),('screenshots/card.jpg',102.8),('screenshots/ask.jpg',120.5),('screenshots/reply.jpg',130),('video/muse-wajo-demo-v4-poster.jpg',13)]
rows=[]
for filename,t in frames:
 path=OUT/filename
 subprocess.run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2',str(path)],check=True)
 rows.append({'file':filename,'video_time':t,'raw_time':args.start+t,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
subprocess.run(['ffmpeg','-y','-v','error','-ss','175','-i',str(video),'-frames:v','1','-q:v','2',str(P/'recording/qr-final-frame.jpg')],check=True)
manifest={'source':'Frame-accurate render of the animated HTML walkthrough without desktop or cursor','raw_file':args.raw.name,'raw_sha256':hashlib.sha256(args.raw.read_bytes()).hexdigest(),'trim_start':args.start,'crop_pixels':args.crop,'final_duration':178,'final_video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'frames':rows}
(P/'recording/screenshot-provenance.json').write_text(json.dumps(manifest,indent=2))
shutil.copy2(P/'captions.vtt',OUT/'video/muse-wajo-demo-v4.vtt')
for file in [video,OUT/'video/muse-wajo-demo-v4.vtt',P/'captions.srt']:
 name='muse-wajo-demo-v4.srt' if file.suffix=='.srt' else file.name
 shutil.copy2(file,OUT.parent/'nanda-demo-video'/name)
print(json.dumps({'video':str(video),'frames':len(rows)},indent=2))
