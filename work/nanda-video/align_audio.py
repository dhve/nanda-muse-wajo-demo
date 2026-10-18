from pathlib import Path
import json,re,difflib
b=Path(__file__).parent
paras=(b/'narration.txt').read_text().strip().split('\n\n')
words=[w for s in json.loads((b/'audio/transcript.json').read_text()) for w in s['words']]
norm=lambda x: re.sub(r'[^a-z0-9]','',x.lower())
a=[norm(w) for p in paras for w in p.split()]
c=[norm(w['word']) for w in words]
sm=difflib.SequenceMatcher(None,a,c,autojunk=False)
mapping={}
for block in sm.get_matching_blocks():
 for k in range(block.size):mapping[block.a+k]=block.b+k
out=[];offset=0
for i,p in enumerate(paras):
 matches=[mapping[j] for j in range(offset,offset+len(p.split())) if j in mapping]
 out.append({'id':i+1,'text':p,'start':words[matches[0]]['start'],'end':words[matches[-1]]['end']})
 offset+=len(p.split())
for p in out:print(p['id'],p['start'],p['end'],p['text'][:70])
(b/'audio/paragraph-alignment.json').write_text(json.dumps(out,indent=2))
