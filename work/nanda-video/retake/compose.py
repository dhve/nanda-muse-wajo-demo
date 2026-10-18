from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

B = Path(__file__).resolve().parent.parent
R = B/'retake'
C = B/'captures'
OUT = R/'clips'
PARTS = R/'parts'
for p in (OUT, PARTS): p.mkdir(exist_ok=True)
FONT = B/'production/assets/fonts/Inter-Variable.ttf'
BG = '#f5f8fd'; NAVY = '#00142b'; BLUE = '#187adc'; GRAY = '#3c4551'

def font(size, weight=450):
    f=ImageFont.truetype(str(FONT),size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f

def shot(name, src, start, dur, crop, app, title, note='', step=1, **kw):
    return dict(name=name, source=src+'.mov', start=start, duration=dur, crop=crop,
                app=app,title=title,note=note,step=step,**kw)

S={
'cap02_muse_setup':[
 shot('muse_setup_paste','r2_muse_setup',10.3,4.8,[645,872,1390,178],'Muse','Paste the setup prompt','Replace [my email] with your email address.'),
 shot('muse_setup_sent','r2_muse_setup',16.2,3.293,[950,590,1070,160],'Muse','Send it to Muse','The agent follows SKILL.MD.')],
'cap03_wajo_setup':[
 shot('wajo_setup_paste','r2_wajo_setup',6.4,5.0,[428,377,1300,280],'Wajo','Paste the same setup prompt','Use a different email address or alias.'),
 shot('wajo_setup_sent','r2_wajo_setup',15.4,4.698,[680,115,1050,160],'Wajo','Send it to Wajo','Each agent gets its own Agent Box.')],
'cap04_code_entry':[
 shot('muse_code','r2_muse_code_send',9,3.773,[1648,628,380,126],'Muse','Return the code to the same chat','Verification code hidden.',2,redactions=[[1854,672,124,40]]),
 shot('wajo_code','r2_wajo_code',7.3,3.773,[430,844,1300,124],'Wajo','Return its own code to Wajo','Verification code hidden.',2,redactions=[[718,880,118,54]])],
'cap05_muse_connect':[
 shot('connect','r2_muse_connect',10.5,2.6,[665,350,535,230],'Muse','Connect Agent Box','Follow the connection steps in Muse.',2),
 shot('continue','r2_muse_connect',22,1.8,[550,880,956,80],'Muse','Continue to the secure field','Connect, Continue, API key, Add',2),
 shot('api_empty','r2_muse_connect',35.1,3.2,[520,334,1022,402],'Muse','Paste the credential securely','Use the API key field.',2),
 shot('api_filled','r2_muse_connect',37.6,3.651,[520,334,1022,402],'Muse','Add the connection','Keep the credential private.',2,hold=True)],
'cap06_indexed_address':[
 shot('wajo_indexed','r2_wajo_indexed',1,4.5,[430,558,1300,208],'Wajo','Wait until both agents are indexed','Wajo is listed.',3),
 shot('muse_indexed','r2_muse_indexed',0.5,13.33,[666,544,1150,270],'Muse','Copy the Muse agent’s address','Use the public Agent Box address.',3)],
'cap07_index_search':[
 shot('index_results','r2_index_results',0,10.098,[55,280,1948,260],'NANDA Index','You can also search manually','nandaindex.org · Search for your indexed agents.',3,light=True)],
'cap08_wajo_hello':[
 shot('find_blank','r3_wajo_find_paste',6.0,0.8,[430,844,1300,128],'Wajo','Find the Muse agent and say hello','Replace [Muse’s agent address] with the address you copied.',3,retake=True),
 shot('find_paste','r3_wajo_find_paste',7.9,4.6,[430,702,1300,270],'Wajo','Find the Muse agent and say hello','Replace [Muse’s agent address] with the address you copied.',3,retake=True),
 shot('greeting_sent','r2_wajo_sent',0.7,5.666,[430,130,1300,505],'Wajo','Greeting sent','Discovered through NANDA Index. Sent through Agent Box.',3)],
'cap09_muse_check_reply':[
 shot('check_paste','r3_muse_check_paste',6.3,5.2,[650,915,1380,130],'Muse','Check for the greeting','Paste the prompt from the guide.',4,retake=True),
 shot('greeting_received','r2_muse_reply',1.4,3.233,[668,440,1145,230],'Muse','The greeting arrives','Wajo to Muse',4),
 shot('reply_paste','r2_muse_reply_prompt',5.4,3.0,[650,915,1380,130],'Muse','Reply with “Hello back!”','Use the same reply prompt from the guide.',4),
 shot('reply_sent','r2_muse_confirm',1,3.544,[650,630,1380,238],'Muse','Reply sent','Muse to Wajo',4)],
'cap10_wajo_reply':[
 shot('reply_check','r2_wajo_reply_check',9.3,3.0,[430,844,1300,128],'Wajo','Check for replies','Paste the final prompt from the guide.',5),
 shot('reply_received','r2_wajo_received',0.8,11.787,[430,272,1300,500],'Wajo','“Hello back!” has arrived','Messages now go in both directions.',5)]
}

def layout(s):
    _,_,cw,ch=s['crop']
    scale=min(1660/cw,570/ch,1.4)
    sw=int(cw*scale)//2*2; sh=int(ch*scale)//2*2
    x=(1920-sw)//2; y=610-sh//2
    return sw,sh,x,y

def make_bg(s):
    sw,sh,x,y=layout(s)
    im=Image.new('RGB',(1920,1080),BG)
    d=ImageDraw.Draw(im)
    d.text((100,88),s['app'].upper(),font=font(30,650),fill=BLUE)
    d.text((1820,88),f"{s['step']} / 5",font=font(30,500),fill=GRAY,anchor='ra')
    d.text((100,150),s['title'],font=font(58,650),fill=NAVY)
    d.text((100,235),s['note'],font=font(31,430),fill=GRAY)
    # A restrained editorial frame around actual recorded pixels.
    left=max(74,x-30); right=min(1846,x+sw+30)
    top=y-28; bottom=y+sh+28
    shadow=Image.new('RGBA',im.size)
    sd=ImageDraw.Draw(shadow);sd.rounded_rectangle((left,top+14,right,bottom+14),24,fill=(0,20,43,24))
    shadow=shadow.filter(ImageFilter.GaussianBlur(16))
    im=Image.alpha_composite(im.convert('RGBA'),shadow)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((left,top,right,bottom),24,fill='#ffffff' if s.get('light') else '#121212')
    d.line((100,972,1820,972),fill='#dce5ef',width=2)
    d.text((100,995),'my.nandaindex.org/demo',font=font(27,450),fill=GRAY)
    d.text((1820,995),'Waits shortened',font=font(27,450),fill=GRAY,anchor='ra')
    path=PARTS/(s['name']+'-layout.png'); im.convert('RGB').save(path)
    return path

def render(s):
    out=PARTS/(s['name']+'.mp4')
    source=C/s['source'];sw,sh,x,y=layout(s);cx,cy,cw,ch=s['crop']
    signature=hashlib.sha256(json.dumps(s,sort_keys=True).encode()+str(source.stat().st_mtime_ns).encode()+Path(__file__).read_bytes()).hexdigest()
    marker=out.with_suffix('.hash')
    if out.exists() and marker.exists() and marker.read_text()==signature: return s['name']
    bg=make_bg(s)
    filters=[]
    for rx,ry,rw,rh in s.get('redactions',[]):
        filters.append(f'drawbox=x={rx}:y={ry}:w={rw}:h={rh}:color=0x12283d:t=fill')
    filters += [f'crop={cw}:{ch}:{cx}:{cy}','setpts=PTS-STARTPTS','fps=30',f'scale={sw}:{sh}:flags=lanczos','setsar=1']
    filters += [f'tpad=stop_mode=clone:stop_duration={s["duration"]}']
    chain='[0:v]'+','.join(filters)+'[clip];[1:v][clip]overlay='+str(x)+':'+str(y)+':shortest=1,format=yuv420p[v]'
    cmd=['ffmpeg','-v','error','-y','-ss',str(s['start']),'-i',str(source),'-loop','1','-framerate','30','-i',str(bg),'-filter_complex',chain,'-map','[v]','-frames:v',str(round(s['duration']*30)),'-an','-c:v','libx264','-preset','fast','-crf','14','-threads','2','-movflags','+faststart',str(out)]
    subprocess.run(cmd,check=True)
    marker.write_text(signature)
    print(s['name'],flush=True)
    return s['name']

if __name__=='__main__':
    selected={k:v for k,v in S.items() if not sys.argv[1:] or k in sys.argv[1:]}
    allshots=[s for v in selected.values() for s in v]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: list(pool.map(render,allshots))
    for slot,shots in selected.items():
        listing=PARTS/(slot+'.txt')
        listing.write_text(''.join("file '"+str(PARTS/(s['name']+'.mp4'))+"'\n" for s in shots))
        subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(OUT/(slot+'.mp4'))],check=True)
    (R/'selections.json').write_text(json.dumps({'recording':'Native macOS screencapture with actual system cursor','region_points':[0,126,1029,534],'source_pixels':[2058,1068],'retake_note':'Two composer close-ups repeat the exact prompt insertion without re-sending. Matching real submissions and results were recorded in the same completed conversations. No app UI or cursor is synthesized.','clips':S},indent=2))
    print('Prepared',len(selected),'revised clips',flush=True)
