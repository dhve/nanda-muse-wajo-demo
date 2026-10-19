from pathlib import Path
import json, subprocess, wave, re, difflib, hashlib
import numpy as np

P = Path(__file__).resolve().parent
A = P / 'audio'
rate, tempo = 48000, .94
scene_data = json.loads((P / 'scenes.json').read_text())
scenes = scene_data['scenes']
paras = json.loads((A / 'paragraph-alignment.json').read_text())
words = json.loads((A / 'words.json').read_text())
source = A / 'vedh-original.mp3'
norm = lambda x: re.sub('[^a-z0-9]', '', x.lower())
def duration(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)]))
def token_words(path):
    out = []
    for segment in json.loads(path.read_text())['transcription']:
        for token in segment['tokens']:
            t = token['text']
            if t.startswith('[_'): continue
            if t.startswith(' ') or not out:
                out.append({'word': t.strip(), 'start': token['offsets']['from']/1000, 'end': token['offsets']['to']/1000})
            else:
                out[-1]['word'] += t
                out[-1]['end'] = token['offsets']['to']/1000
    return out

source_duration = duration(source)
bounds = [0] + [(a['end'] + b['start']) / 2 for a, b in zip(paras, paras[1:])] + [source_duration]
chunks, timeline, caps, matches = [], [], [], []
for s, p, a, b in zip(scenes, paras, bounds, bounds[1:]):
    clip = source
    voice_words = [w for w in words if w['start'] >= p['start'] - .001 and w['end'] <= p['end'] + .001]
    if s['id'] == 'verify':
        clip = A / 'verify-original.mp3'
        a, b = 0, duration(clip)
        voice_words = token_words(A / 'verify-transcript.json')
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(a), '-t', str(b-a), '-i', str(clip), '-af', f'atempo={tempo}', '-ar', str(rate), '-ac', '1', '-f', 's16le', '-'])
    samples = np.frombuffer(raw, dtype='<i2').copy()
    lead, size = int(.5 * rate), s['duration'] * rate
    assert len(samples) + lead < size, (s['id'], len(samples)/rate, s['duration'])
    fade = min(240, len(samples)//2)
    samples[:fade] = (samples[:fade] * np.linspace(0, 1, fade)).astype('<i2')
    samples[-fade:] = (samples[-fade:] * np.linspace(1, 0, fade)).astype('<i2')
    chunk = np.zeros(size, dtype='<i2')
    chunk[lead:lead+len(samples)] = samples
    chunks.append(chunk)
    row = {'id': s['id'], 'start': s['start'], 'duration': s['duration'], 'source_file': clip.name, 'source_start': a, 'source_end': b, 'narration_start': s['start']+.5, 'narration_end': s['start']+.5+len(samples)/rate, 'tempo': tempo, 'text': s['narration']}
    timeline.append(row)
    ws = s['narration'].split()
    sm = difflib.SequenceMatcher(None, [norm(w) for w in ws], [norm(w['word']) for w in voice_words], autojunk=False)
    assert sm.ratio() > .98, (s['id'], sm.ratio(), voice_words)
    mapping = {a+k: b+k for a, b, n in sm.get_matching_blocks() for k in range(n)}
    matches.append({'scene': s['id'], 'ratio': sm.ratio()})
    i = 0
    while i < len(ws):
        j, line = i, []
        while j < len(ws) and len(line) < 11 and (not line or len(' '.join(line+[ws[j]])) <= 67):
            line.append(ws[j]); j += 1
            if line[-1].endswith(('.', '?', '!')): break
        hits = [mapping[k] for k in range(i, j) if k in mapping]
        start = row['narration_start'] + (voice_words[hits[0]]['start']-a)/tempo
        end = min(s['start']+s['duration']-.1, row['narration_start'] + (voice_words[hits[-1]]['end']-a)/tempo+.08)
        if len(' '.join(line)) > 43:
            k = min(range(1, len(line)), key=lambda n: abs(len(' '.join(line[:n]))-len(' '.join(line[n:]))))
            text = ' '.join(line[:k]) + '\n' + ' '.join(line[k:])
        else: text = ' '.join(line)
        caps.append({'start': max(s['start'], start), 'end': end, 'text': text}); i = j

with wave.open(str(A / 'narration-raw.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(np.concatenate(chunks).tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(A/'narration-raw.wav'), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', str(rate), str(P/'narration.wav')], check=True)
for a, b in zip(caps, caps[1:]): a['end'] = min(a['end'], b['start']-.01)
def stamp(t, sep=','):
    ms = round(t*1000); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02}{sep}{ms:03}'
(P/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(caps))+'\n')
(P/'captions.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f"{stamp(c['start'],'.')} --> {stamp(c['end'],'.')}\n{c['text']}" for c in caps)+'\n')
(A/'timeline.json').write_text(json.dumps({'duration': 178, 'scenes': timeline, 'captions': caps}, indent=2))
(P/'voice-provenance.json').write_text(json.dumps({'service': 'ElevenLabs', 'voice': 'Vedh', 'model': 'Eleven v4', 'sources': [{'file': f.name, 'duration': duration(f), 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in [source, A/'verify-original.mp3']], 'final_duration': 178, 'tempo': tempo, 'scene_word_matches': matches, 'forbidden_spoken_word_found': any('nanda' in w['word'].lower() for w in words + token_words(A/'verify-transcript.json'))}, indent=2))
print({'duration': duration(P/'narration.wav'), 'captions': len(caps), 'scene_matches': matches})
