from pathlib import Path
import json,re,difflib,subprocess,wave,hashlib,math
import numpy as np
P=Path(__file__).resolve().parent;A=P/'audio'; data=json.loads((P/'scenes.json').read_text());scenes=data['scenes'];source=A/'vedh-original.mp3';tempo=.94;rate=48000
words=[]
for s in json.loads((A/'transcript.json').read_text())['transcription']:
 for token in s['tokens']:
  t=token['text']
  if t.startswith('[_'):continue
  if t.startswith(' ') or not words:words.append({'word':t.strip(),'start':token['offsets']['from']/1000,'end':token['offsets']['to']/1000})
  else:words[-1]['word']+=t;words[-1]['end']=max(words[-1]['end'],token['offsets']['to']/1000)
def norm(x):
 x=x.lower().replace('bakery dot com','bakery.com').replace('gmail dot com','gmail.com').replace('bob at gmail','bob@gmail').replace('two p.m.','2 p.m.')
 return re.sub('[^a-z0-9]','',x)
script=''.join(norm(s['narration']) for s in scenes); actual=''.join(norm(w['word']) for w in words)
sm=difflib.SequenceMatcher(None,script,actual,autojunk=False);print('Normalized transcript match:',sm.ratio());assert sm.ratio()>.995
mapping={i+k:j+k for i,j,n in sm.get_matching_blocks() for k in range(n)}
chars=[]
for i,w in enumerate(words):chars += [i]*len(norm(w['word']))
offset=0;aligned=[]
for s in scenes:
 n=len(norm(s['narration']));hits=[chars[mapping[k]] for k in range(offset,offset+n) if k in mapping];offset+=n
 aligned.append({'id':s['id'],'start':words[hits[0]]['start'],'end':words[hits[-1]]['end'],'first_word':hits[0],'last_word':hits[-1]})
chunks=[];timeline=[];captions=[];clock=0
source_duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(source)]))
for i,(s,a) in enumerate(zip(scenes,aligned)):
 start=max(0,a['start']-.06);end=min(source_duration,a['end']+.08,aligned[i+1]['start']-.05 if i+1<len(aligned) else source_duration)
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(start),'-t',str(end-start),'-i',str(source),'-af',f'atempo={tempo}','-ar',str(rate),'-ac','1','-f','s16le','-'])
 samples=np.frombuffer(raw,dtype='<i2').copy();lead=.12;tail=.14;dur=math.ceil((len(samples)/rate+lead+tail)*30)/30
 if s['id']=='end':dur=max(8,dur)
 # Fade only the clip edges to prevent clicks; preserve the natural spoken rhythm.
 fade=min(240,len(samples)//2);samples[:fade]=(samples[:fade]*np.linspace(0,1,fade)).astype('<i2');samples[-fade:]=(samples[-fade:]*np.linspace(1,0,fade)).astype('<i2')
 chunk=np.zeros(round(dur*rate),dtype='<i2');lead_n=round(lead*rate);chunk[lead_n:lead_n+len(samples)]=samples;chunks.append(chunk)
 s.update(start=round(clock,6),duration=round(dur,6))
 row={**a,'scene_start':clock,'scene_duration':dur,'source_start':start,'source_end':end,'narration_start':clock+lead,'narration_end':clock+lead+len(samples)/rate,'tempo':tempo};timeline.append(row)
 ws=words[a['first_word']:a['last_word']+1];j=0
 while j<len(ws):
  k=j+1
  while k<len(ws) and k-j<10 and len(' '.join(w['word'] for w in ws[j:k+1]))<66 and not re.search(r'[.!?][\"\x27]?$',ws[k-1]['word']):k+=1
  text=' '.join(w['word'] for w in ws[j:k]);text=text.replace('agent box','AgentBox').replace('Agent box','AgentBox')
  captions.append({'start':clock+lead+(ws[j]['start']-start)/tempo,'end':min(clock+dur-.03,clock+lead+(ws[k-1]['end']-start)/tempo+.05),'text':text});j=k
 clock+=dur
assert clock<180,clock
with wave.open(str(A/'narration-raw.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(np.concatenate(chunks).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',str(A/'narration-raw.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar',str(rate),str(P/'narration.wav')],check=True)
for a,b in zip(captions,captions[1:]):a['end']=min(a['end'],b['start']-.01)
def stamp(t,sep):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000);return f'{h:02}:{m:02}:{s:02}{sep}{n:03}'
for ext,sep in [('srt',','),('vtt','.')]:
 (P/f'captions.{ext}').write_text(('WEBVTT\n\n' if ext=='vtt' else '')+'\n\n'.join((f'{i+1}\n' if ext=='srt' else '')+f"{stamp(c['start'],sep)} --> {stamp(c['end'],sep)}\n{c['text']}" for i,c in enumerate(captions))+'\n')
data['timing']='Aligned to generated narration, .94 playback speed; minimal scene-boundary padding';(P/'scenes.json').write_text(json.dumps(data,indent=2)+'\n')
(A/'words.json').write_text(json.dumps(words,indent=2));(A/'timeline.json').write_text(json.dumps({'duration':clock,'scenes':timeline,'captions':captions},indent=2))
(P/'voice-provenance.json').write_text(json.dumps({'service':'ElevenLabs','voice':'Vedh','model':'Eleven v4','generation':1,'source_file':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_duration':source_duration,'final_duration':clock,'tempo':tempo,'normalized_transcript_match':sm.ratio(),'spoken_nanda_found':'nanda' in actual},indent=2))
print('Duration:',clock);print([(s['id'],s['duration']) for s in scenes])
