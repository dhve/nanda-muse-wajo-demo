from pathlib import Path
from html.parser import HTMLParser
import json,re,difflib,subprocess
P=Path(__file__).resolve().parent
class Prompts(HTMLParser):
    def __init__(self): super().__init__(); self.active=None; self.prompts={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='p' and a.get('id','').startswith('p-'): self.active=a['id'][2:]; self.prompts[self.active]=''
    def handle_data(self,t):
        if self.active: self.prompts[self.active]+=t
    def handle_endtag(self,tag):
        if tag=='p': self.active=None
parser=Prompts();parser.feed((P.parents[2]/'outputs/nanda-demo-v4/index.html').read_text())
canonical={p['id']:p['text'] for p in json.loads((P/'prompts.json').read_text())['prompts']}
assert parser.prompts==canonical, (parser.prompts, canonical)
scenes=json.loads((P/'scenes.json').read_text())['scenes'];script=(P/'narration.txt').read_text();assert script.strip()=='\n\n'.join(s['narration'] for s in scenes)
heard=' '.join(s['text'].strip() for s in json.loads((P/'audio/final-transcript.json').read_text())['transcription'])
def normalize(text):
    text=re.sub(r'\s+',' ',text.lower())
    text=text.replace('host39','host thirty-nine').replace('list39','list thirty-nine')
    return re.sub('[^a-z0-9 ]','',text).split()
a,b=normalize(script),normalize(heard);sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
report={'duration_seconds':float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(P/'narration.wav')])),'canonical_transcript_word_match':sm.ratio(),'normalization':'Whitespace, punctuation, and ASR numerals host39/list39 normalized to spoken words.','forbidden_spoken_word_found':any('nanda' in w for w in b),'changes':[{'expected':a[i:j],'heard':b[k:l]} for op,i,j,k,l in sm.get_opcodes() if op!='equal'],'captions':len(json.loads((P/'audio/timeline.json').read_text())['captions']),'guide_prompts_exact':len(canonical)}
assert report['duration_seconds']<180 and not report['forbidden_spoken_word_found']
assert sm.ratio()>.99, report
(P/'audio/narration-qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
