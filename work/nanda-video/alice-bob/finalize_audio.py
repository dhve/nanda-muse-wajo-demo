from pathlib import Path
import json,subprocess,wave,re,difflib
import numpy as np
b=Path(__file__).parent
pars=json.loads((b/'audio/paragraph-alignment.json').read_text())
words=[w for s in json.loads((b/'audio/transcript.json').read_text()) for w in s['words']]
speed=.86; sr=48000
ends=[(pars[i]['end']+pars[i+1]['start'])/2 for i in range(len(pars)-1)]+[119.066063]
starts=[0]+ends[:-1]
chunks=[np.zeros(int(sr*1.2),dtype='<i2')];elapsed=1.2;timeline=[]
for i,(p,start,end) in enumerate(zip(pars,starts,ends)):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(start),'-t',str(end-start),'-i',str(b/'audio/vedh-original.mp3'),'-af',f'atempo={speed}','-ar',str(sr),'-ac','1','-f','s16le','-'])
 a=np.frombuffer(raw,dtype='<i2');dur=len(a)/sr
 pad=3 if i<len(pars)-1 else 2
 timeline.append({'id':i+1,'timeline_start':elapsed,'timeline_end':elapsed+dur+pad,'source_start':start,'source_end':end,'audio_duration':dur,'pause_after':pad,'text':p['text']})
 chunks.extend([a,np.zeros(int(sr*pad),dtype='<i2')]);elapsed+=dur+pad
with wave.open(str(b/'audio/narration-timed-raw.wav'),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(np.concatenate(chunks).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',str(b/'audio/narration-timed-raw.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar',str(sr),str(b/'audio/narration-final.wav')],check=True)
(b/'audio/timeline.json').write_text(json.dumps({'duration':elapsed,'speed':speed,'lead_in':1.2,'sections':timeline},indent=2))
# Canonical captions aligned to recognized word times, supplied separately for playback.
norm=lambda x:re.sub(r'[^a-z0-9]','',x.lower())
canonical=[w for p in pars for w in p['text'].split()]
sm=difflib.SequenceMatcher(None,[norm(w) for w in canonical],[norm(w['word']) for w in words],autojunk=False)
mapping={a+k:b+k for a,b,n in sm.get_matching_blocks() for k in range(n)}
def stamp(t):
 ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
cap=[];offset=0
for sec in timeline:
 ws=sec['text'].split();j=0
 while j<len(ws):
  k=j;line=[]
  while k<len(ws) and (not line or len(' '.join(line+[ws[k]]))<=65) and len(line)<11:
   line.append(ws[k]);k+=1
   if ws[k-1].endswith(('.', '?','!')):break
  hits=[mapping[q] for q in range(offset+j,offset+k) if q in mapping]
  if hits:
   t0=sec['timeline_start']+(words[hits[0]]['start']-sec['source_start'])/speed
   t1=sec['timeline_start']+(words[hits[-1]]['end']-sec['source_start'])/speed+.12
   if len(' '.join(line))>43:
    split=min(range(1,len(line)),key=lambda z:abs(len(' '.join(line[:z]))-len(' '.join(line[z:]))))
    txt=' '.join(line[:split])+'\n'+' '.join(line[split:])
   else:txt=' '.join(line)
   cap.append((t0,t1,txt))
  j=k
 offset+=len(ws)
(b/'audio/captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(s)} --> {stamp(e)}\n{t}' for i,(s,e,t) in enumerate(cap))+'\n')
print('Duration',elapsed,'seconds; captions',len(cap))
for x in timeline:print(x['id'],round(x['timeline_start'],2),round(x['timeline_end'],2),x['text'][:45])
