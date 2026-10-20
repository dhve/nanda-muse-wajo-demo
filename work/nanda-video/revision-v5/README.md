# Known agent ID walkthrough

Version 5 is a 2:28 animated bakery walkthrough. Alice uses Muse and Bob uses Wajo. Bob contacts a bakery he already knows. Later, after an order and Bob's permission, Alice starts a new message to Bob's registered ID.

The Index resolves a known ID to its authorized hosted Agent Card. The sender reads the card's current endpoint and access requirements. AgentBox delivers the messages. Domain publication, email account proof, and permission are separate parts of the flow.

The screens, addresses, code, and replies are illustrative. This version contains no search or capability discovery. Earlier videos remain in the archive and on the original demo page.

## Files

- `prompts.json` is the canonical prompt text used by the player and guide.
- `scenes.json` contains final narration and audio timing for all 14 scenes.
- `narration.txt` contains the spoken script. The saved Vedh voice does not say Nanda.
- `audio/vedh-original.mp3` is the generated voice source. `audio/transcript.json` and `audio/timeline.json` record alignment.
- `narration.wav` is the final timed narration.
- `production/player/` contains the HTML animation, with 0.9-second overlapping scene transitions.
- `recording/direct-render.mp4` is the silent, frame-accurate animation render.
- `../../../outputs/nanda-demo-v5/` contains the final video, captions, guide, review document, and screenshots extracted from that video.
- `qa/`, `doc-qa/`, and `export-qa.json` record checks and visual review.

## Rebuild from the saved sources

Use Python, FFmpeg, Node.js, Playwright, and Chrome. Python document generation also needs `python-docx`. Make the Playwright package available to Node. Set `RENDER_CHROME` if Chrome is installed at a different path.

From this directory, start the player server in one terminal:

```sh
python3 -m http.server 8767
```

In another terminal, render and export:

```sh
node render_direct.cjs
python3 export_video.py
python3 build_guide.py
```

The saved final timing and audio are sufficient for an identical content rebuild. `build_content.py` is the authoring source and writes provisional durations. If changing the script, run it first, regenerate or replace the narration, transcribe the new audio, then run `prepare_audio.py` before rendering. Do not rerun it alone over the final timing.

`build_player.py` uses the archived version 4 engine as its base. `build_review_doc.py` creates the numbered script document. The public archive includes both versions and the scripts they reference.

## Checks

The export is 1920×1080 at 30 fps, H.264 with AAC audio. Narration matched the written text after normalization. Player layouts and the guide were checked at desktop and phone widths. Each guide prompt matches its canonical text, and every screenshot has a frame time and hash in `screenshot-provenance.json`.

The final video runs 148.4 seconds. The longest between-scene silence is under one second; the ending holds for reading. No desktop capture or cursor is used.

## Primary references

- [Federated resolution of known agent identities](https://datatracker.ietf.org/doc/html/draft-raskar-agentic-web-federated-resolution-01)
- [Sierra's Poppy introduction](https://sierra.ai/blog/poppy)
- [Personal Agent Protocol specification](https://personalagentprotocol.org/docs/0.2/spec)
- [Official Muse, Redfin, and Rocket demo](https://x.com/SierraPlatform/status/2108245197440307584)

Poppy informed the simple request, permission, and visible-result sequence. This video does not claim that Poppy and ARD are the same protocol.
