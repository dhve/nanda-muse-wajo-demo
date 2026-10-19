# Animated bakery walkthrough

This version uses illustrated screens and sample addresses. Alice runs a bakery and uses Muse. Bob uses Wajo to find the bakery, check its agent card, and exchange messages through AgentBox.

The Index appears above the agents during discovery and card lookup. AgentBox appears between the agents during message delivery. The sample email addresses, verification code, and replies are illustrative.

## Files

- `prompts.json` contains the exact prompts used in the video and guide.
- `scenes.json` contains the scene timing and narration.
- `production/player/` contains the animated HTML player built with Claude Code in the Claude Mac app.
- `narration.wav` contains the 178-second Vedh voice track generated with ElevenLabs.
- `captions.srt` and `captions.vtt` contain synchronized captions.
- `prepare_audio.py` rebuilds the voice track from the included audio sources.
- `build_guide.py` creates the matching reading guide.
- `verify_content.py` checks the guide prompts and narration.
- `render_direct.cjs` renders each animation frame at its exact video timestamp.
- `assemble_v4.py` adds audio and captions and extracts guide screenshots.
- `verify_export.py` checks the exported video and screenshot provenance.
- `feedback.md` maps the requested video changes to their evidence.

## Preview the animation

Run from this folder:

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

Open `http://127.0.0.1:8766/production/player/` in a browser.

## Render and assemble

The delivered video is rendered directly from the HTML player. The user removed the native cursor requirement. No desktop, cursor, user browser profile or live app is included in the final capture.

Install Playwright, FFmpeg, and Python with NumPy and Pillow. Keep the local server running on port 8766, then run:

```sh
npm install playwright
node render_direct.cjs
python3 assemble_v4.py --raw recording/direct-render.mp4 --start 0 --crop 1920:1080:0:0
```

The renderer uses an isolated headless Chrome process and writes `recording/direct-render.mp4`. Set `RENDER_CHROME` if Chrome is installed elsewhere. It captures 5,340 frames at 30 fps, using frame number divided by frame rate as the animation clock. CSS focus transitions use that same clock. Browser loading time is excluded, and narration starts at zero.

`verify_content.py`, `production/qa/check_player.py`, and `verify_export.py` check the prompts, narration, scene layout, final video and screenshots. `production/qa/check_timing.cjs` checks visible actions against spoken cues. `production/qa/check_export_sync.py` compares exported cue frames with the player and measures the audio offset at the beginning, middle and end.

The guide images are extracted from the delivered video, with their timestamps and hashes saved in the provenance file. The timing correction keeps the 178-second narration and all prompts unchanged.

`capture.html` and `record_cursor.py` preserve the earlier native recording approach. That approach is not used in the final video. Its desktop recording remains private.

The video illustrates a workflow. It is not evidence that messages were sent to the sample addresses. The live site retains the existing guide and earlier video, with the new video added above it. The separate v4 reading guide is archived here.

## Sources

The architecture follows [How the Index works](https://nandaindex.org/how-it-works) and the current [SKILL.MD](https://my.nandaindex.org/agent/SKILL.md). The revision incorporates video feedback from the supplied team chat. The private chat export and the reference slide deck are not included in the public package.
