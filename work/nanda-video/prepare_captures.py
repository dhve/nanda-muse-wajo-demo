from pathlib import Path
import subprocess,json,concurrent.futures
B=Path(__file__).resolve().parent; C=B/'captures'
G=C/'guide-and-index-raw.webm'; L=C/'live-messages-raw.webm'
specs=[
('cap01_guide_copy',G,9.0,5.0,(55,450,670,650)),
('cap02_muse_setup',G,22.0,7.0,(425,450,1210,740)),
('cap03_wajo_setup',G,62.0,11.0,(695,490,725,335)),
('cap04_code_entry',G,82.5,8.0,(55,520,675,455)),
('cap05_muse_connect',G,90.0,11.5,(50,520,1860,710)),
('cap06_indexed_address',G,110.0,10.0,(330,470,1175,325)),
('cap07_index_search',G,245.0,11.0,(610,630,1400,300)),
('cap08_prompt_part',G,123.0,4.7,(55,535,670,500)),
('cap08_sent_part',L,440.0,6.8,(430,420,1330,495)),
('cap09_muse_check_reply',L,20.0,10.0,(380,480,1240,550)),
('cap10_wajo_reply',L,115.0,16.0,(430,420,1325,495)),
]
def run(s):
 name,src,start,dur,box=s;x,y,w,h=box;w=w//2*2;h=h//2*2
 vf=f'crop={w}:{h}:{x}:{y},fps=30,setsar=1,format=yuv420p'
 if name.startswith('cap08_'):
  vf+=",scale=1760:820:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf5f8fd"
 args=['ffmpeg','-v','error','-y','-ss',str(start),'-i',str(src),'-t',str(dur),'-vf',vf,'-an','-c:v','libx264','-preset','fast','-crf','14','-movflags','+faststart',str(C/(name+'.mp4'))]
 subprocess.run(args,check=True);print(name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,specs))
subprocess.run(['ffmpeg','-v','error','-y','-i',str(C/'cap08_prompt_part.mp4'),'-i',str(C/'cap08_sent_part.mp4'),'-filter_complex','[0:v][1:v]xfade=transition=fade:duration=0.4:offset=4.3[v]','-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','14','-pix_fmt','yuv420p','-movflags','+faststart',str(C/'cap08_wajo_hello.mp4')],check=True)
(C/'capture-selections.json').write_text(json.dumps([{'file':n+'.mp4','source':str(src),'source_start':st,'source_duration':du,'crop':box} for n,src,st,du,box in specs],indent=2))
edl=json.loads((B/'claude/edit/edl.json').read_text())
for s in edl['segments']:
 if s['kind']!='capture':continue
 s['privacy_check']='done';s['src_in']=0;s['crop']=None;s['fit']='frame';s['redact']=[]
 s['notes']='Recorded real guide or live app evidence; credentials and one-time codes are excluded by the crop. The current preview includes the recorded automation pointer; a native system cursor pass is pending an unlocked Mac.'
 if s['id']=='cap07':s['callout']={'text':'nandaindex.org','at':90,'dur':8}
 if s['id']=='cap08':s['fit']='fill'
edl['outputs']['final']='out/final/muse-wajo-preview.mp4'
(B/'edit-final.json').write_text(json.dumps(edl,indent=2))
print('All capture slots prepared; native cursor pass pending.')
