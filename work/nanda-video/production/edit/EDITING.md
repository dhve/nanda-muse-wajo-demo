# Editing the Muse and Wajo demo

Run every command from `claude/` (the folder that holds CONTRACT.md). `python3` means
`/opt/homebrew/bin/python3`. Paths inside `edit/edl.json` are relative to `claude/`.

```
python3 edit/assemble.py --dry-run      # timeline, sources, and what a final render would refuse
python3 edit/assemble.py --mode test    # about 2 minutes, placeholders allowed
python3 edit/qa.py                      # checks out/test/muse-wajo-test.mp4
```

| File | Purpose |
|---|---|
| `edit/edl.json` | The edit: 19 segments with absolute output times, capture settings, callouts. |
| `edit/assemble.py` | Renders each segment, joins them, muxes the narration and captions. |
| `edit/qa.py` | Checks an output, writes `qa_report.json` and `contact_sheet.png` next to it. |
| `out/test/`, `out/final/` | The MP4 plus `.srt`, `.vtt` and `.manifest.json` (what each segment used). |
| `build/edit/segments/` | Cached segments `NN_<id>.mp4`. `build/edit/logs/` has every command and its output. |

## 1. Drop in a capture

1. Put the recording in `../captures/`. Any container ffmpeg reads works (.mp4, .mov, .webm,
   .mkv, .m4v), at any resolution and with a variable frame rate.
2. Name it after its slot, for example `cap09_muse_check_reply.mov` (any of those extensions), or
   point the segment's `"file"` at it. One long take can feed several slots with different `src_in`.
3. Run the dry run. The source column changes from `PLACEHOLDER` to `capture file`.

| Segment | Slot | Output time (s) | Length | Evidence |
|---|---|---|---|---|
| cap01 | `cap01_guide_copy` | 26.380 to 30.962 | 4.58 s | setup |
| cap02 | `cap02_muse_setup` | 30.962 to 37.055 | 6.09 s | setup |
| cap03 | `cap03_wajo_setup` | 37.055 to 46.753 | 9.70 s | setup |
| cap04 | `cap04_code_entry` | 49.753 to 57.299 | 7.55 s | setup, verification |
| cap05 | `cap05_muse_connect` | 57.299 to 68.550 | 11.25 s | setup, connection |
| cap06 | `cap06_indexed_address` | 71.550 to 89.380 | 17.83 s | indexed, agent_box_address |
| cap07 | `cap07_index_search` | 89.380 to 99.478 | 10.10 s | discovery_listing |
| cap08 | `cap08_wajo_hello` | 99.478 to 110.544 | 11.07 s | discovery_lookup, greeting_sent |
| cap09 | `cap09_muse_check_reply` | 113.544 to 122.521 | 8.98 s | greeting_received, reply_sent |
| cap10 | `cap10_wajo_reply` | 125.521 to 140.308 | 14.79 s | reply_received |

Each segment's `notes` says what the shot must show, and `say` lists the narration under it.
Setup and verification already happened, so cap02 to cap05 are real walkthroughs of the existing
guide and chat history (scrolling through what already happened). No new submissions, no duplicate
accounts, no replayed codes or credentials. Record with the native cursor; never add a drawn one.

## 2. Fit the capture to its slot

Fields on each capture segment:

- `src_in`: the source time (seconds from the first frame, as QuickTime shows it) that appears at
  the segment start. The clip plays at normal speed from there. If it runs out, the last frame holds.
  Speed is never changed.
- `crop`: `[x, y, w, h]` in source pixels, or `null` for the whole frame. Crop away browser chrome
  (tabs, address bar, a "started debugging this browser" banner, profile chips) and make the UI
  large enough to read. Retina recordings are 2x, so measure on the recording itself.
- `fit`: `auto` (default) picks `fill` for a 16:9 crop and `frame` otherwise. `fill` scales to
  cover 1920x1080 and trims the overflow. `frame` fits the footage inside 1760x990 on the page
  background with rounded corners, a hairline border and a soft shadow.
- `redact`: boxes `{"x", "y", "w", "h", "t0", "t1"}` in source pixels and source seconds. Leave
  out `t0` and `t1` to cover the whole clip. Each box is heavily box blurred and runs 0.1 s early
  and late. Cover six-digit codes, personal email addresses, any part of a credential, inbox
  contents and unrelated chats. The guide's own screenshots also show demo email addresses.
- `callout`: `{"text", "at", "dur"}`, with `at` in absolute output seconds. A navy chip appears at
  the bottom left with 0.3 s fades. cap09 shows "Wajo → Muse" at 117.777 ("Here's the greeting
  from Wajo.") and cap10 shows "Muse → Wajo" at 128.044 ("The reply from Muse has arrived.").
- `privacy_check`: `pending` on cap02 to cap05. Watch the rendered segment, add redact boxes as
  needed, then set it to `done`. A final render refuses `pending`.
- `evidence`: tags that QA uses to prove the setup, public discovery listing, greeting sent,
  greeting received, reply sent and reply received are real footage. Keep them.

Measure coordinates and check boxes on a real frame:

```
python3 edit/assemble.py --grid cap04 12.5   # build/edit/grid/cap04_12.50s.png
```

That writes the source frame at 12.5 s with a grid labeled in source pixels, the crop in blue and
the redact boxes active at that moment in red. Then render just that segment and watch it:

```
python3 edit/assemble.py --only cap04        # build/edit/segments/08_cap04.mp4
```

Example:

```json
"file": "../captures/cap04_code_entry.mov",
"src_in": 3.2,
"crop": [0, 180, 2880, 1620],
"fit": "auto",
"redact": [{"x": 940, "y": 1210, "w": 380, "h": 70, "t0": 4.0, "t1": 9.5}],
"privacy_check": "done"
```

Keep segment `start` and `end` as they are. They come from the final narration
(`../audio/timeline.json` and caption starts), and frame `n` is `floor(seconds * 30 + 0.5)`.

## 3. Motion

Motion segments call `motion/render.py SCENE --duration D --beats ... --param k=v --out PATH`
automatically. If that fails they fall back to `motion/out/<name>.mp4`, and in test mode to a
"MOTION PENDING" stub. `beats` are seconds from the segment start and must use names that
`python3 motion/render.py --list` declares (others are dropped with a note). They sit on caption
starts or spoken words. Any change under `motion/` re-renders the motion segments on the next run.

## 4. Render

- Test: `python3 edit/assemble.py --mode test` writes `out/test/muse-wajo-test.mp4`.
- Final: `python3 edit/assemble.py --mode final` writes `out/final/muse-wajo-demo.mp4`. It refuses
  to start while a capture file is missing, a motion segment would be a stub, a `privacy_check` is
  pending, the timeline does not match the narration, or the narration WAV no longer matches the
  md5 in the EDL.
- Segments are cached by a hash of the segment JSON plus input sizes and mtimes, so a rerun only
  rebuilds what changed. `--force` rebuilds everything, `--jobs N` sets parallel renders.
- Picture: 1920x1080, 30 fps constant, H.264 High, yuv420p, BT.709. Crossfades of 0.5 s are
  centered on every boundary, except the straight cut from intro to roles. Total 4987 frames.
- Sound: `../audio/narration-final.wav` untouched, only encoded to AAC 48 kHz 256 kb/s with the
  mono channel copied to both channels at unity gain (`pan=stereo|c0=c0|c1=c0`; a plain `-ac 2`
  would lower it by 3 dB). No loudness, gain, tempo or trim changes.
- Captions: a mov_text soft subtitle track (off by default), plus an identical `.srt` and a `.vtt`.

## 5. QA

```
python3 edit/qa.py                                          # test output
python3 edit/qa.py out/final/muse-wajo-demo.mp4 --mode final
```

It checks the EDL timeline, duration (180 s maximum, within 2 frames of the narration), the
streams, a full decode, captions and narration text (no banned word, no em or en dashes), onscreen
text in the EDL and the motion scenes, placeholders and stubs, evidence footage, privacy checks,
the narration itself (aligned against the WAV: lag, correlation, gain, residual, length, so any
trim, tempo, gain or filter fails), loudness and true peak, the longest silent gap, a whisper-cli
transcript (`--no-whisper` skips it), and draws `contact_sheet.png` with one labeled frame per
segment. Test mode reports placeholders, evidence and privacy as WARN; final mode as FAIL. The exit
code is 1 on any FAIL. Look at the contact sheet and watch the whole file before sharing it.

## Troubleshooting

- A segment failed: read `build/edit/logs/NN_<id>.log`.
- "source ends X s before the slot needs it, last frame held": use an earlier `src_in` or a longer
  take, or accept the hold.
- Colors look off on one capture: tagged sources use their own color tags; untagged HD sources are
  read as BT.709.
