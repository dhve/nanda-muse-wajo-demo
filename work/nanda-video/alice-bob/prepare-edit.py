"""Prepare this revision's narration timing and draft edit without substituting old footage."""
from pathlib import Path
import hashlib, json, re, wave

R = Path(__file__).resolve().parent
timing = json.loads((R/'audio/timeline.json').read_text())
sections = timing['sections']

def at(section, source_time):
    s = sections[section-1]
    return s['timeline_start'] + (source_time-s['source_start'])/timing['speed']

# Reading holds in existing speech gaps: Alice's email, inbox prompt, reply confirmation.
pauses = [(at(3,25.26),2), (at(8,85.16),3), (sections[7]['timeline_end']-3.1,2)]
def shift(t): return t + sum(d for p,d in pauses if t >= p)

with wave.open(str(R/'audio/narration-final.wav'),'rb') as f:
    params=f.getparams(); source=f.readframes(f.getnframes())
stride=params.nchannels*params.sampwidth
chunks=[]; cursor=0
for point,duration in pauses:
    end=round(point*params.framerate)*stride
    chunks.extend([source[cursor:end],bytes(round(duration*params.framerate)*stride)])
    cursor=end
chunks.append(source[cursor:])
with wave.open(str(R/'narration.wav'),'wb') as f:
    f.setparams(params);f.writeframes(b''.join(chunks))

def seconds(value):
    h,m,s,ms=map(int,re.split('[:,]',value))
    return h*3600+m*60+s+ms/1000
def stamp(t):
    ms=round(t*1000)
    return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
srt=re.sub(r'\d\d:\d\d:\d\d,\d{3}',lambda m:stamp(shift(seconds(m[0]))),(R/'audio/captions.srt').read_text())
# Trim the source captions' small tail padding when the next cue begins.
# Two cues must not compete for the same screen time during continuous speech.
blocks = srt.strip().split('\n\n')
for i in range(len(blocks)-1):
    lines = blocks[i].splitlines()
    start, end = lines[1].split(' --> ')
    following = seconds(blocks[i+1].splitlines()[1].split(' --> ')[0])
    if seconds(end) > following:
        lines[1] = start + ' --> ' + stamp(following - 0.02)
        blocks[i] = '\n'.join(lines)
srt = '\n\n'.join(blocks) + '\n'
(R/'captions.srt').write_text(srt)

ends=[s['timeline_end'] for s in sections]
windows={
 'intro':(0,ends[0]), 'roles':(ends[0],ends[1]-3),
 'step1':(ends[1]-3,ends[1]),
 'cap01':(ends[1],at(3,21.91)),
 'cap02':(at(3,21.91),at(3,25.26)),
 'cap03':(at(3,25.26),ends[2]-3),
 'step2':(ends[2]-3,ends[2]),
 'cap04':(ends[2],at(4,42.67)),
 'cap05':(at(4,42.67),ends[3]-3),
 'step3':(ends[3]-3,ends[3]),
 'cap06':(ends[3],ends[4]), 'cap07':(ends[4],ends[5]),
 'cap08':(ends[5],ends[6]-3), 'step4':(ends[6]-3,ends[6]),
 'cap09':(ends[6],ends[7]-3), 'step5':(ends[7]-3,ends[7]),
 'cap10':(ends[7],ends[8]), 'closing':(ends[8],ends[9]),
 'endcard':(ends[9],ends[10]),
}
edl=json.loads((R/'edit-draft.json').read_text())
for segment in edl['segments']:
    segment['start'],segment['end']=[round(shift(x),6) for x in windows[segment['id']]]
    if segment['id']=='intro': segment['beats']={'muse':1.85,'wajo':3.20}
edl['narration']={'file':'../narration.wav','mode':'track',
    'md5':hashlib.md5((R/'narration.wav').read_bytes()).hexdigest(),
    'duration':timing['duration']+sum(d for _,d in pauses)}
edl['reading_holds']=[{'at_before_retime':p,'seconds':d} for p,d in pauses]
assert edl['narration']['duration'] < 180
assert all(a['end']==b['start'] for a,b in zip(edl['segments'],edl['segments'][1:]))
assert all(s['end']>s['start'] for s in edl['segments'])
(R/'edit-draft.json').write_text(json.dumps(edl,indent=2))
print('Prepared',round(edl['narration']['duration'],3),'seconds with readable prompt holds.')
for s in edl['segments']: print(s['id'],round(s['start'],3),round(s['end'],3))
