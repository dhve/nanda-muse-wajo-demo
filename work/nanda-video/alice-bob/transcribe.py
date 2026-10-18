from faster_whisper import WhisperModel
from pathlib import Path
import json, subprocess
import numpy as np
base=Path(__file__).parent
m=WhisperModel('base.en', device='cpu', compute_type='int8', download_root=str(base.parent/'models'))
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(base/'audio/vedh-original.mp3'),'-f','f32le','-ac','1','-ar','16000','-'])
audio=np.frombuffer(raw,dtype=np.float32)
segments,info=m.transcribe(audio,word_timestamps=True,beam_size=5,initial_prompt='Alice. Bob. Muse. Wajo. Agent Box. The index. Skill dot M D.')
out=[]
for s in segments:
 d={'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word,'probability':w.probability} for w in s.words]}
 out.append(d)
 print(round(s.start,2),round(s.end,2),s.text,flush=True)
(base/'audio/transcript.json').write_text(json.dumps(out,indent=2))
