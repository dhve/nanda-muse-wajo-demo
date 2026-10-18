from pathlib import Path
import concurrent.futures
import json
import subprocess

B = Path(__file__).resolve().parent
C = B / 'captures'
specs = [
    ('cap01_guide_copy', 'native01', 7, (50, 330, 670, 600)),
    ('cap02_muse_setup', 'native02', 7, (352, 178, 1352, 832)),
    ('cap03_wajo_setup', 'native03', 11, (665, 230, 850, 370)),
    ('cap04_code_entry', 'native04', 9, (50, 208, 670, 360)),
    ('cap05_muse_connect', 'native05', 13, (542, 414, 976, 364)),
    ('cap06_indexed_address', 'native06', 19, (300, 216, 1230, 350)),
    ('cap07_index_search', 'native07', 12, (610, 464, 1400, 278)),
    ('cap08_prompt_part', 'native08prompt', 4.7, (50, 420, 670, 500)),
    ('cap08_sent_part', 'native08sent', 7.0, (430, 140, 1330, 495)),
    ('cap09_muse_check_reply', 'native09', 11, (380, 310, 1230, 550)),
    ('cap10_wajo_reply', 'native10', 16, (430, 248, 1326, 470)),
]

def render(spec):
    name, raw, duration, (x, y, width, height) = spec
    height = height // 2 * 2
    vf = f'crop={width}:{height}:{x}:{y},fps=30,setsar=1,format=yuv420p'
    if name.startswith('cap08_'):
        vf += ',scale=1760:820:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf5f8fd'
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y', '-i', str(C / (raw + '.mov')),
        '-t', str(duration), '-vf', vf, '-an', '-c:v', 'libx264',
        '-preset', 'fast', '-crf', '14', '-movflags', '+faststart',
        str(C / (name + '.mp4')),
    ], check=True)
    print(name, flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(render, specs))

subprocess.run([
    'ffmpeg', '-v', 'error', '-y', '-i', str(C / 'cap08_prompt_part.mp4'),
    '-i', str(C / 'cap08_sent_part.mp4'), '-filter_complex',
    '[0:v][1:v]xfade=transition=fade:duration=0.4:offset=4.3[v]',
    '-map', '[v]', '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '14',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(C / 'cap08_wajo_hello.mp4'),
], check=True)

(C / 'native-selections.json').write_text(json.dumps([
    {'file': name + '.mp4', 'source': raw + '.mov', 'duration': duration, 'crop': crop,
     'recording': 'macOS screencapture, actual system cursor included',
     'region_points': [0, 126, 1029, 534], 'source_pixels': [2058, 1068]}
    for name, raw, duration, crop in specs
], indent=2))

edl = json.loads((B / 'edit-final.json').read_text())
for segment in edl['segments']:
    if segment['kind'] != 'capture':
        continue
    segment['notes'] = (
        'Native macOS screen recording with the actual system cursor. '
        'Cropped for readability; no cursor is composited or replaced. '
        'Setup shots revisit the real demo evidence in the published guide. '
        'Index search and message confirmations use the live websites. '
        'Credentials, verification codes, browser chrome and unrelated windows are excluded.'
    )
    if segment['id'] == 'cap05':
        segment['callout'] = {'text': 'Connect → Continue → API key → Add', 'at': 57.8, 'dur': 9.8}
edl['outputs']['final'] = 'out/final/muse-wajo-demo.mp4'
(B / 'edit-final.json').write_text(json.dumps(edl, indent=2))
print('Native recording clips prepared.', flush=True)
