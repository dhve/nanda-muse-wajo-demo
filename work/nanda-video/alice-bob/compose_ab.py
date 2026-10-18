"""Compose the Alice and Bob capture clips (cap01 to cap10) and the website stills.

Same framing and style as retake/compose.py: actual recorded pixels are cropped and scaled
onto the pale canvas, with an app label, step count, title, note and footer. Nothing in the
app UI or the pointer is drawn; codes are covered with solid boxes before cropping.

  python3 compose_ab.py            render every clip into clips/
  python3 compose_ab.py cap04      render one slot
  python3 compose_ab.py --stills   export the five website screenshots into website-assets/
"""
from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

AB = Path(__file__).resolve().parent
C = AB.parent / 'captures'
OUT = AB / 'clips'
PARTS = AB / 'parts'
STILLS = AB / 'website-assets'
for p in (OUT, PARTS, STILLS): p.mkdir(exist_ok=True)
FONT = AB / 'production/assets/fonts/Inter-Variable.ttf'
BG = '#f5f8fd'; NAVY = '#00142b'; BLUE = '#187adc'; GRAY = '#3c4551'
MASK = '0x12283d'
ALICE, BOB = 'Alice in Muse', 'Bob in Wajo'
CONT, SETUP = 'ab_continuous.mov', 'ab_cap02_muse_setup_clean.mov'
FINAL, REPLY = 'ab_final_exchange.mov', 'ab_reply_prompt_closeup.mov'
SENT = 'ab_sent_confirmation.mov'
ALICE_CODE = [912, 957, 92, 46]   # the six digits in Muse's composer
BOB_CODE = [718, 893, 113, 44]     # the six digits in Wajo's composer


def font(size, weight=450):
    f = ImageFont.truetype(str(FONT), size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f


def shot(name, src, start, dur, crop, app, title, note='', step=1, **kw):
    return dict(name=name, source=src, start=start, duration=dur, crop=crop,
                app=app, title=title, note=note, step=step, **kw)


S = {
'cap01_guide_copy': [
 shot('guide_copy', CONT, 489.4, 4.5, [44, 536, 684, 292], 'Demo guide', 'Copy the setup prompt',
      'One prompt for both apps.', 1, live=3.3, light=True)],
'cap02_muse_setup': [
 shot('alice_setup_paste', SETUP, 9.3, 2.4, [640, 905, 1400, 140], ALICE, 'Alice pastes it into Muse',
      'Only [my email] is replaced: alice7qx@yahoo.com'),
 shot('alice_setup_sent', SETUP, 34.7, 3.8, [640, 640, 1400, 405], ALICE, 'Sent to Muse',
      'The agent follows the steps in SKILL.MD.')],
'cap03_wajo_setup': [
 shot('bob_setup_paste', CONT, 271.6, 3.0, [420, 840, 1300, 130], BOB, 'Bob pastes the same prompt into Wajo',
      'With his own email: bob7qx@gmail.com'),
 shot('bob_setup_progress', CONT, 316.0, 4.0, [420, 220, 1300, 420], BOB, 'Each agent needs a different email',
      'Wajo follows the same steps.'),
 shot('bob_setup_result', CONT, 424.0, 5.75, [420, 270, 1300, 560], BOB, 'Wajo creates Bob’s Agent Box',
      'Bob’s agent: bob7qxgmailcom@agentboxnanda.org')],
'cap04_code_entry': [
 shot('alice_code_ask', CONT, 36.0, 2.6, [640, 190, 1400, 670], ALICE, 'Check each email for a six-digit code',
      'Muse asks for the code sent to Alice’s email.', 2),
 shot('alice_code_paste', CONT, 43.5, 2.6, [650, 930, 1390, 110], ALICE, 'Paste the code into the same chat',
      'Codes are hidden in this video.', 2, redactions=[ALICE_CODE]),
 shot('bob_code_paste', CONT, 579.4, 2.85, [420, 840, 1300, 130], BOB, 'Bob returns his code to Wajo',
      'Codes are hidden in this video.', 2, redactions=[BOB_CODE])],
'cap05_muse_connect': [
 shot('connect_click', CONT, 96.2, 2.7, [640, 380, 700, 260], ALICE, 'In Muse, you may see a Connect button',
      'Follow the connection steps.', 2),
 shot('connect_continue', CONT, 140.0, 3.0, [520, 470, 1020, 560], ALICE, 'Continue',
      'Connect, then Continue.', 2),
 shot('api_empty', CONT, 165.5, 3.0, [520, 325, 1020, 409], ALICE, 'Paste the credential into the API key field',
      'It comes from the same email as the code.', 2),
 shot('api_filled', CONT, 186.0, 3.5, [520, 325, 1020, 409], ALICE, 'Keep that credential private',
      'The field masks it. Then select Add.', 2)],
'cap06_indexed_address': [
 shot('bob_indexed', CONT, 856.6, 5.0, [430, 400, 1310, 420], BOB, 'Wait until both agents are indexed',
      'Bob’s agent is live and listed.', 3),
 shot('alice_indexed', CONT, 392.0, 14.1, [650, 110, 1390, 360], ALICE, 'Copy Alice’s agent address from Muse',
      'Use the agent address, not her email address.', 3)],
'cap07_index_search': [
 shot('index_results', CONT, 724.0, 10.25, [40, 170, 1960, 480], 'NANDA Index', 'You can also search the index website',
      'Here are Alice and Bob’s agents.', 3, light=True)],
'cap08_wajo_hello': [
 shot('find_paste', CONT, 909.7, 3.0, [420, 754, 1300, 216], BOB, 'Bob asks Wajo to find Alice’s agent',
      'Only [Muse’s agent address] is replaced.', 3),
 shot('find_sent', CONT, 945.6, 3.5, [430, 220, 1300, 520], BOB, 'Wajo looks up the agent through the index',
      'Discovery through NANDA Index.', 3),
 shot('hello_sent', SENT, 41.0, 4.85, [425, 330, 1310, 470], BOB, 'Then it sends the hello',
      'Delivery through Agent Box.', 3)],
'cap09_muse_check_reply': [
 shot('check_paste', CONT, 1103.1, 2.5, [650, 930, 1390, 110], ALICE, 'Alice asks Muse to check its Agent Box',
      'The prompt from the guide.', 4),
 shot('check_sent', CONT, 1124.6, 2.0, [650, 630, 1390, 410], ALICE, 'Sent to Muse', '', 4),
 shot('greeting', CONT, 1172.0, 5.6, [650, 120, 1390, 430], ALICE, 'Here’s the greeting from Bob’s agent',
      'From Bob to Alice, through Agent Box.', 4),
 shot('reply_paste', REPLY, 18.3, 2.4, [650, 930, 1390, 110], ALICE, 'Alice asks Muse to reply',
      'The reply prompt from the guide.', 4, repeated_insertion=True),
 shot('reply_sent', FINAL, 56.0, 2.65, [650, 600, 1390, 270], ALICE, 'Reply sent',
      'From Alice to Bob, through Agent Box.', 4)],
'cap10_wajo_reply': [
 shot('reply_check_paste', FINAL, 22.4, 3.0, [420, 840, 1300, 130], BOB, 'Bob checks Wajo for replies',
      'The last prompt from the guide.', 5, repeated_insertion=True),
 shot('reply_received', FINAL, 4.0, 11.7, [425, 260, 1310, 420], BOB, 'Alice’s reply has arrived',
      'A message in each direction.', 5)],
}

# Website screenshots: single frames from inside the shots above, full recorded resolution.
STILL_SHOTS = {
    'step-1-setup.jpg': (CONT, 37.0, [640, 176, 1400, 684], 'alice_code_ask'),
    'step-2-verify.jpg': (CONT, 188.0, [520, 325, 1020, 409], 'api_filled'),
    'step-3-hello.jpg': (SENT, 48.0, [425, 330, 1310, 470], 'hello_sent'),
    'step-4-reply.jpg': (FINAL, 56.0, [650, 600, 1390, 270], 'reply_sent'),
    'step-5-reply-received.jpg': (FINAL, 8.0, [425, 260, 1310, 420], 'reply_received'),
}
MIN_STILL_WIDTH = 1248


def layout(s):
    _, _, cw, ch = s['crop']
    scale = min(1660 / cw, 570 / ch, 1.4)
    sw = int(cw * scale) // 2 * 2; sh = int(ch * scale) // 2 * 2
    x = (1920 - sw) // 2; y = 610 - sh // 2
    return sw, sh, x, y


def make_bg(s):
    sw, sh, x, y = layout(s)
    im = Image.new('RGB', (1920, 1080), BG)
    d = ImageDraw.Draw(im)
    d.text((100, 88), s['app'].upper(), font=font(30, 650), fill=BLUE)
    d.text((1820, 88), f"{s['step']} / 5", font=font(30, 500), fill=GRAY, anchor='ra')
    d.text((100, 150), s['title'], font=font(58, 650), fill=NAVY)
    d.text((100, 235), s['note'], font=font(31, 430), fill=GRAY)
    left = max(74, x - 30); right = min(1846, x + sw + 30)
    top = y - 28; bottom = y + sh + 28
    shadow = Image.new('RGBA', im.size)
    sd = ImageDraw.Draw(shadow); sd.rounded_rectangle((left, top + 14, right, bottom + 14), 24, fill=(0, 20, 43, 24))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    im = Image.alpha_composite(im.convert('RGBA'), shadow)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((left, top, right, bottom), 24, fill='#ffffff' if s.get('light') else '#121212')
    d.line((100, 972, 1820, 972), fill='#dce5ef', width=2)
    d.text((100, 995), 'my.nandaindex.org/demo', font=font(27, 450), fill=GRAY)
    d.text((1820, 995), 'Waits shortened', font=font(27, 450), fill=GRAY, anchor='ra')
    path = PARTS / (s['name'] + '-layout.png'); im.convert('RGB').save(path)
    return path


def render(s):
    out = PARTS / (s['name'] + '.mp4')
    source = C / s['source']; sw, sh, x, y = layout(s); cx, cy, cw, ch = s['crop']
    signature = hashlib.sha256(json.dumps(s, sort_keys=True).encode() + str(source.stat().st_mtime_ns).encode()
                               + Path(__file__).read_bytes()).hexdigest()
    marker = out.with_suffix('.hash')
    if out.exists() and marker.exists() and marker.read_text() == signature: return s['name']
    bg = make_bg(s)
    filters = [f'drawbox=x={rx}:y={ry}:w={rw}:h={rh}:color={MASK}:t=fill' for rx, ry, rw, rh in s.get('redactions', [])]
    filters += [f'crop={cw}:{ch}:{cx}:{cy}', 'setpts=PTS-STARTPTS', 'fps=30']
    if s.get('live'):
        filters += [f'trim=end={s["live"]}', 'setpts=PTS-STARTPTS']
    filters += [f'scale={sw}:{sh}:flags=lanczos', 'setsar=1', f'tpad=stop_mode=clone:stop_duration={s["duration"]}']
    chain = '[0:v]' + ','.join(filters) + '[clip];[1:v][clip]overlay=' + str(x) + ':' + str(y) + ':shortest=1,format=yuv420p[v]'
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(s['start']), '-i', str(source), '-loop', '1', '-framerate', '30',
           '-i', str(bg), '-filter_complex', chain, '-map', '[v]', '-frames:v', str(round(s['duration'] * 30)), '-an',
           '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-threads', '2',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', str(out)]
    subprocess.run(cmd, check=True)
    marker.write_text(signature)
    print(s['name'], flush=True)
    return s['name']


def stills():
    for name, (src, t, (cx, cy, cw, ch), from_shot) in STILL_SHOTS.items():
        tmp = STILLS / (name + '.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(C / src), '-frames:v', '1',
                        '-vf', f'crop={cw}:{ch}:{cx}:{cy}', str(tmp)], check=True)
        im = Image.open(tmp).convert('RGB')
        if im.width < MIN_STILL_WIDTH:  # scale recorded pixels only, never add content
            im = im.resize((MIN_STILL_WIDTH, round(im.height * MIN_STILL_WIDTH / im.width)), Image.Resampling.LANCZOS)
        im.save(STILLS / name, quality=90, optimize=True, progressive=True)
        tmp.unlink()
        print(name, im.size, 'from', src, t, 'shot', from_shot, flush=True)


if __name__ == '__main__':
    if '--stills' in sys.argv:
        stills(); sys.exit()
    selected = {k: v for k, v in S.items() if not sys.argv[1:] or any(k.startswith(a) for a in sys.argv[1:])}
    allshots = [s for v in selected.values() for s in v]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: list(pool.map(render, allshots))
    for slot, shots in selected.items():
        listing = PARTS / (slot + '.txt')
        listing.write_text(''.join("file '" + str(PARTS / (s['name'] + '.mp4')) + "'\n" for s in shots))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(listing), '-c', 'copy',
                        '-movflags', '+faststart', str(OUT / (slot + '.mp4'))], check=True)
    (AB / 'clip-selections.json').write_text(json.dumps({
        'recording': 'Native macOS screencapture with the actual system pointer, 2058x1068 pixels',
        'region_points': [0, 126, 1029, 534],
        'first_submit_sources': [CONT, SETUP],
        'after_the_fact_sources': {
            FINAL: 'Recorded after the real exchange: the real sent reply and delivery confirmation in Muse, the real reply receipt in Wajo, and a repeated, unsent insertion of the reply-check prompt.',
            REPLY: 'Recorded after the real exchange: a repeated, unsent insertion of the reply prompt for the close-up.',
            SENT: 'Recorded after the real exchange: a native scroll of the existing Wajo chat to its real Found and Done confirmations. No message was entered.'},
        'repeated_insertion_shots': ['reply_paste', 'reply_check_paste'],
        'note': 'Only recorded pixels are cropped and scaled. Codes are covered before cropping. No app UI or pointer is synthesized. Identity preparation messages, headers with account details, sidebars and old demo identities are outside every crop.',
        'clips': S, 'website_stills': {k: {'source': v[0], 'time': v[1], 'crop': v[2], 'shot': v[3]} for k, v in STILL_SHOTS.items()},
    }, indent=2))
    print('Prepared', len(selected), 'clips', flush=True)
