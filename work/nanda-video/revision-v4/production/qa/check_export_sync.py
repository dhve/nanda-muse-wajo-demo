"""Compare exported cue frames with the player and verify the audio start/clock."""
from pathlib import Path
import io, json, os, subprocess, tempfile
import numpy as np
from PIL import Image

P=Path(__file__).resolve().parents[2]
VIDEO=P.parents[2]/'outputs/nanda-demo-v4/video/muse-wajo-demo-v4.mp4'
# Regions isolate the visible action at independently reviewed narration cues.
CUES=[
 (0.8,'opening title',(72,36,1072,100)),
 (23.5,'Alice setup runs',(420,528,1460,620)),
 (34.0,'Bob has an address',(528,524,1460,700)),
 (40.2,'verification prompt',(420,848,1540,948)),
 (43.8,'credential source in email',(460,160,1460,740)),
 (46.4,'credential in secure field',(500,400,1300,800)),
 (71.2,'search before result',(528,468,1460,620)),
 (73.0,'bakery found',(528,524,1460,720)),
 (114.0,'Bob approves',(528,544,908,616)),
 (129.9,'reply before sending',(420,642,1460,697)),
 (131.1,'reply sent',(420,642,1460,697)),
 (150.0,'tasting introduction',(260,550,1660,670)),
 (151.7,'Bob asks Tuesday',(260,550,1660,670)),
 (153.8,'Alice replies with a time',(260,550,1660,670)),
]

with tempfile.TemporaryDirectory(prefix='nanda-sync-') as tmp:
 script=r'''
 const {chromium}=require('playwright');
 (async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.RENDER_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 await page.goto('http://127.0.0.1:8766/production/player/?frame=0');
 await page.waitForFunction(()=>window.player&&document.fonts.status==='loaded');
 for(const t of TIMES){await page.evaluate(t=>player.seek(t),t);await page.screenshot({path:OUT+'/'+t+'.png',animations:'disabled'});}
 await browser.close();
 })().catch(e=>{console.error(e);process.exit(1)});
 '''.replace('TIMES',json.dumps([x[0] for x in CUES])).replace('OUT',json.dumps(tmp))
 subprocess.run(['node','-e',script],check=True)
 rows=[]
 for t,name,box in CUES:
  png=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(VIDEO),'-frames:v','1','-f','image2pipe','-vcodec','png','-'])
  actual=np.asarray(Image.open(io.BytesIO(png)).convert('RGB').crop(box)).astype(float)
  expected=np.asarray(Image.open(Path(tmp)/f'{t:g}.png').convert('RGB').crop(box)).astype(float)
  error=float(np.mean(np.abs(actual-expected)))
  rows.append({'time':t,'cue':name,'mean_pixel_error':round(error,3),'pass':error<5.0})

def pcm(file):
 return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(file),'-vn','-ac','1','-ar','2400','-f','f32le','-']),dtype='<f4')
source=pcm(P/'narration.wav');export=pcm(VIDEO)
audio=[]
for start in (2,80,160):
 # Correlate four seconds within a +/-100 ms search window.
 i=start*2400;n=4*2400;radius=240
 correlation=np.correlate(export[i-radius:i+n+radius],source[i:i+n],mode='valid')
 lag=(int(correlation.argmax())-radius)/2400
 audio.append({'time':start,'lag_ms':round(lag*1000,3),'pass':abs(lag)<0.02})
report={'visual_cues':rows,'audio_alignment':audio,'passed':all(r['pass'] for r in rows+audio)}
(P/'export-sync-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if not report['passed']:raise SystemExit(1)
