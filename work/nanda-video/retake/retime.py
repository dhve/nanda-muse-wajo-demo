from pathlib import Path
import hashlib
import json
import re
import wave

B = Path(__file__).resolve().parent.parent
R = B / 'retake'
PAUSES = [(36.85, 2.0), (117.5, 2.0), (122.52, 4.0)]

def shifted(t):
    return t + sum(d for at, d in PAUSES if t >= at)

with wave.open(str(B / 'audio/narration-final.wav'), 'rb') as f:
    params = f.getparams()
    source = f.readframes(f.getnframes())
stride = params.nchannels * params.sampwidth
parts = []
cursor = 0
for at, duration in PAUSES:
    end = round(at * params.framerate) * stride
    parts += [source[cursor:end], bytes(round(duration * params.framerate) * stride)]
    cursor = end
parts.append(source[cursor:])
with wave.open(str(R / 'narration.wav'), 'wb') as f:
    f.setparams(params)
    f.writeframes(b''.join(parts))

def time_s(s):
    h, m, sec, ms = map(int, re.split('[:,]', s))
    return 3600*h + 60*m + sec + ms/1000

def srt_time(t):
    ms = round(t*1000)
    return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'

srt = (B / 'audio/captions.srt').read_text()
srt = re.sub(r'\d\d:\d\d:\d\d,\d{3}', lambda m: srt_time(shifted(time_s(m[0]))), srt)
(R / 'captions.srt').write_text(srt)

edl = json.loads((B / 'edit-final.json').read_text())
edl['narration']['file'] = '../retake/narration.wav'
edl['narration']['md5'] = hashlib.md5((R / 'narration.wav').read_bytes()).hexdigest()
edl['narration']['duration'] += 8
edl['captions']['srt'] = '../retake/captions.srt'
for s in edl['segments']:
    s['start'], s['end'] = round(shifted(s['start']), 3), round(shifted(s['end']), 3)
    if s.get('callout'):
        s['callout']['at'] = round(shifted(s['callout']['at']), 3)
    if s['kind'] == 'capture' and s['id'] != 'cap01':
        s['file'] = '../retake/clips/' + s['slot'] + '.mp4'
        s['fit'] = 'fill'
        s['notes'] = ('Actual live app interactions from the fresh VideoOct14 demo. '
                      'Published prompt wording is unchanged except bracketed values. '
                      'Native macOS recording and system cursor; waits are edited out. '
                      'Reading holds preserve real recorded frames. Secrets are excluded or masked.')
        s['privacy_check'] = 'pending'
        s['callout'] = None
edl['segments'][4]['notes'] += ' Two seconds of narration pause added for reading.'
(B / 'edit-retake.json').write_text(json.dumps(edl, indent=2))
print('Retimed video duration:', edl['narration']['duration'])
