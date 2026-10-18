# Muse and Wajo demo video: shared build contract

This file is the agreement between the motion work (motion/), the edit work (edit/) and the
integrator. Paths below are relative to this folder:
`/Users/admin/Documents/Codex/2026-10-14/giv/work/nanda-video/claude` (called `claude/`).

## 1. Ground rules (everyone)

- Write only inside `claude/`, and only inside the folders you own (section 3). Never write elsewhere.
- No git commands of any kind. `/Users/admin` is a parent git repo; do not run git, do not scan the home tree.
- No GUI or browser. Do not use computer-use or browser tools, `open`, `osascript`, `screencapture`, QuickTime, or any app.
- Never generate a substitute voice. No text to speech of any kind (including macOS `say`). Test audio is the real
  voice file `../audio/vedh-original.mp3`, or silence.
- Never fabricate UI evidence or a cursor. No mock app screens, no imitation Muse or Wajo chat bubbles, no drawn mouse
  pointer. Abstract diagrams with labeled nodes are fine. A missing capture becomes an obvious placeholder slate that the
  final QA rejects.
- Never modify or publish the guide in `../../../outputs/nanda-demo/`. Read it only.
- Spoken narration and captions never contain "Nanda" in any case, including URLs. Onscreen graphics may say
  "NANDA Index" and show `my.nandaindex.org/demo`.
- No em dashes or en dashes anywhere (onscreen text, captions, file contents, comments). Use " - " or a comma.
- Tools: `/opt/homebrew/bin/python3` (3.14) with Pillow 12 and numpy only. No pip installs. CLI tools: ffmpeg and
  ffprobe 8.1 (this build has NO drawtext, NO subtitles or ass filters; it has xfade, overlay, fade, loudnorm,
  ebur128, silencedetect, boxblur, tpad), sox (tempo with pitch preserved), whisper-cli (model
  `~/.whisper-models/ggml-small.en.bin`), hb-shape.
- All text goes through `lib/brand.py` (the guide's own Inter, HarfBuzz kerning). The font has no arrow or check
  glyphs; use `brand.rich_text_image`, `brand.arrow_sprite`, `brand.check_sprite`, `brand.envelope_sprite`.

## 2. Format

- Video: 1920x1080, 30 fps constant, H.264 High, yuv420p, BT.709. When piping RGB frames into ffmpeg, convert with
  `-vf scale=out_color_matrix=bt709:out_range=tv,format=yuv420p` and tag
  `-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv`.
- Intermediates: libx264 `-preset medium -crf 14`, no audio, exact frame count `round(duration * 30)`.
- Final: libx264 `-preset slow -crf 18`, `-movflags +faststart`, AAC 48 kHz stereo 256 kb/s.
- Duration: 166.225 s, set by the final narration (section 5). Hard maximum 180 s. Calm pacing, no music.
- Audio: the final narration WAV, untouched. No loudness or gain changes.

## 3. Folder ownership

| Path | Owner | Notes |
|---|---|---|
| `lib/brand.py`, `assets/` | integrator | Shared tokens, font, text, chips. Read only for agents; request changes in your report. |
| `motion/` | motion agent | Renderer, scenes, default renders in `motion/out/`. |
| `edit/` | editorial agent | EDL, assembler, narration, captions, QA. |
| `build/motion/` | motion agent | Scratch. |
| `build/edit/` | editorial agent | Scratch and intermediates. |
| `out/` | editorial agent | Test renders and QA reports (`out/test/`). |
| `CONTRACT.md`, `status.txt` | integrator | |

## 4. Motion renderer interface

The motion agent implements, the editorial agent calls:

```
python3 motion/render.py --list
python3 motion/render.py SCENE --out PATH.mp4 [--duration SEC] [--beats '{"name": sec}'] [--param key=value ...]
python3 motion/render.py SCENE --still SEC --out PATH.png [same options]
python3 motion/render.py --all            # default renders into motion/out/
```

- `--list` prints JSON: `{scene: {"nominal": s, "min": s, "max": s, "beats": {name: s}, "params": {name: default}}}`.
- `--duration` stretches or compresses. Extra time goes into holds (mostly the final hold), never into faster or
  slower motion. Compression is allowed down to `min`.
- `--beats` overrides named beat times (seconds from scene start) so visuals can land on narration words.
- Output: exactly `round(duration * 30)` frames, no audio, format from section 2.
- `intro`, `step`, `closing`, `endcard` start on the plain surface background or close to it. `roles` starts on the
  exact final frame of `intro` (it is a continuation). Every scene ends on a settled hold with no fade out; the editor
  adds the crossfades.

Scenes and default copy (all onscreen text; keep it exactly unless a line does not fit):

| Scene | Nominal | Purpose and copy |
|---|---|---|
| `intro` | 8 s | Eyebrow "Muse + Wajo demo". Title "Connect Muse and Wajo". Subtitle "Find each other through NANDA Index, then send a message and a reply." Then the diagram: Muse card, NANDA Index node, Wajo card, two-way links. Node sublabels "Agent in Muse", "Discovery", "Agent in Wajo". |
| `roles` | 10 s | Continues intro. Index focus with "Finds agents across apps". Agent Box node appears ("Agent Box", "Address and delivery"), each agent gets an "Agent Box address" chip, one short message hop through Agent Box, then "Keep using the app you already know." |
| `step` | 2.6 s | Params `number`, `total` (5), `title`, `subtitle`. Eyebrow "Step N of 5". Big numbered circle in the guide style. |
| `closing` | 10 s | Discovery versus delivery. Lanes "Discovery" (NANDA Index, "NANDA Index finds and resolves the agent") and "Delivery" (Agent Box, "Agent Box delivers the message"). Wajo looks up Muse through the Index, then a "Greeting" message moves Wajo to Agent Box to Muse ("Received"), then a "Reply" moves Muse to Agent Box to Wajo ("Received"). Optional small label "Neutral bridge across ecosystems". |
| `endcard` | 7 s | "Try it yourself", URL `my.nandaindex.org/demo`, three prompts "Set up", "Find an agent", "Send a message", footer "NANDA Index - Federated Agent Discovery". |

Step card copy:

| N | title | subtitle |
|---|---|---|
| 1 | Set up both agents | In Muse and Wajo |
| 2 | Verify each email | Send each code back in its app |
| 3 | Find Muse and say hello | Discover through NANDA Index |
| 4 | Read and reply in Muse | Wajo → Muse |
| 5 | See the reply in Wajo | Muse → Wajo |

## 5. Narration (final, do not alter)

- Use `../audio/narration-final.wav` exactly as delivered (48 kHz mono PCM, 166.225 s). No tempo, gain, loudness,
  trims or edits. Only encode it to AAC for the MP4.
- Times come from `../audio/timeline.json` (11 sections: speech, then a 3 s pause; 2 s after the last) and the
  sentence-level captions `../audio/captions.srt` (43 entries). Picture follows these times. The voice already starts
  at 1.200 s.
- The captions are already clean of the banned word. Use them as the sidecar and as a soft subtitle track.

## 6. Default edit, timed to the final narration (seconds on the output timeline)

| Segment | Start | End | Kind | Narration and notes |
|---|---|---|---|---|
| intro | 0.000 | 11.123 | motion `intro` | Section 1: speech 1.200 to 8.123, then pause. |
| roles | 11.123 | 23.380 | motion `roles` | Section 2 speech. Cut from intro, no dissolve. Beats on caption starts (Agent Box at 16.251, own app at 20.367). |
| step1 | 23.380 | 26.380 | motion `step` 1 | Pause before section 3. |
| cap01, cap02, cap03 | 26.380 | 46.753 | captures | Section 3. Split at caption starts: guide copy from 26.380, Muse paste from 30.962, Wajo and SKILL.md from 37.055. |
| step2 | 46.753 | 49.753 | motion `step` 2 | Pause. |
| cap04, cap05 | 49.753 | 68.550 | captures | Section 4. Muse Connect part starts at the "In Muse, you may also see a Connect button" caption. Redact codes and the credential. |
| step3 | 68.550 | 71.550 | motion `step` 3 | Pause. |
| cap06 | 71.550 | 89.380 | capture | Section 5 plus its pause. Indexed, address copied. |
| cap07 | 89.380 | 99.478 | capture | Section 6 plus pause. Both agents on the index website (reading time in the pause). |
| cap08 | 99.478 | 110.545 | capture | Section 7 speech. Wajo finds Muse and says hello. |
| step4 | 110.545 | 113.545 | motion `step` 4 | Pause. |
| cap09 | 113.545 | 122.521 | capture | Section 8 speech. Greeting from Wajo visible in Muse. Callout chip "Wajo → Muse". Reply sent. |
| step5 | 122.521 | 125.521 | motion `step` 5 | Pause. |
| cap10 | 125.521 | 140.308 | capture | Section 9 plus pause. Reply from Muse visible in Wajo. Callout chip "Muse → Wajo". |
| closing | 140.308 | 157.116 | motion `closing` | Section 10 plus pause. Beats on its caption starts. |
| endcard | 157.116 | 166.225 | motion `endcard` | Section 11 plus 2 s end. |

These slot lengths override the nominal scene durations in section 4 (step cards are 3.0 s). Crossfades of about
0.5 s are centered on boundaries, except intro to roles which is a straight cut.

## 7. Capture slots (real footage from the operator, arriving in `../captures/`)

| Slot | Suggested file | Shows |
|---|---|---|
| cap01_guide_copy | `cap01_guide_copy.mp4` | Demo guide open, Copy clicked on the setup prompt. |
| cap02_muse_setup | `cap02_muse_setup.mp4` | Real walkthrough of the existing Muse chat: the setup prompt and the agent's confirmation. |
| cap03_wajo_setup | `cap03_wajo_setup.mp4` | Real walkthrough of the existing Wajo chat: its setup prompt, SKILL.md steps, confirmation. |
| cap04_code_entry | `cap04_code_entry.mp4` | Real walkthrough of the existing chat where the code was sent and accepted (code redacted). |
| cap05_muse_connect | `cap05_muse_connect.mp4` | Real walkthrough of Muse's Connect step and its confirmation (credential never readable). |
| cap06_indexed_address | `cap06_indexed_address.mp4` | Agents report indexed; Muse agent's Agent Box address copied. |
| cap07_index_search | `cap07_index_search.mp4` | Index website search showing both demo agents. |
| cap08_wajo_hello | `cap08_wajo_hello.mp4` | Wajo asked to find the Muse agent and say hello; lookup and send. |
| cap09_muse_check_reply | `cap09_muse_check_reply.mp4` | Muse checks its Agent Box, greeting from Wajo visible, reply sent. |
| cap10_wajo_reply | `cap10_wajo_reply.mp4` | Wajo checks replies; Muse's reply visible. |

Setup and verification already happened, so cap02 to cap05 are real recordings of the existing guide and chat
confirmations, not fresh submit actions. No duplicate accounts, no replayed credentials, no mock UI.

Any container ffmpeg reads is fine (.mp4 or .mov, any resolution, variable frame rate). The EDL maps each slot to a
file, so other names work.

## 8. Required QA

Banned word scan of narration and captions (text, plus a whisper-cli transcript of the final audio). Duration window.
Stream format. Full decode without errors. Loudness and true peak. Longest silent gap. No placeholders in final mode.
Every evidence beat present as real footage: setup, public discovery listing, Wajo greeting sent, Muse receipt and
reply, Wajo reply receipt. No em or en dashes in onscreen text or captions. Contact sheet of representative frames.
