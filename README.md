# Muse and Wajo demo archive

This repository contains the videos, prompts, guides, screenshots, narration, animation code, editing files, and production notes from the Muse and Wajo demo.

Alice uses Muse. Bob uses Wajo. The current walkthrough resolves a known agent ID to its hosted Agent Card and contact details, then uses AgentBox to exchange messages.

Version 5 is a clearly labeled animated bakery walkthrough. Bob contacts a bakery he knows. Later, with his permission, the bakery starts a new message to Bob's registered ID. It uses illustrative addresses and replies, a direct HTML animation render, and Vedh narration. Version 4 is the earlier bakery animation. Version 3 preserves the live account demo.

[Watch the current demo and follow its matching guide](https://my.nandaindex.org/demo/v5/). The [original page](https://my.nandaindex.org/demo/) shows the revised video above the earlier live account demo and guide. Version 4 remains in this archive.

## Start here

| Item | File |
| --- | --- |
| Current known agent ID walkthrough, 2:28 | [muse-wajo-demo-v5.mp4](outputs/nanda-demo-v5/video/muse-wajo-demo-v5.mp4) |
| Current guide, exact prompts, and video screenshots | [outputs/nanda-demo-v5](outputs/nanda-demo-v5) |
| Numbered script for review | [bakery-demo-script-v5.docx](outputs/nanda-demo-v5/bakery-demo-script-v5.docx) |
| Current canonical prompts | [prompts.json](work/nanda-video/revision-v5/prompts.json) |
| Current narration and captions | [narration.txt](work/nanda-video/revision-v5/narration.txt), [SRT](outputs/nanda-demo-v5/video/muse-wajo-demo-v5.srt), [VTT](outputs/nanda-demo-v5/video/muse-wajo-demo-v5.vtt) |
| Current animation, audio, timing, and checks | [revision-v5](work/nanda-video/revision-v5) |
| Earlier animated bakery walkthrough, 2:58 | [muse-wajo-demo-v4.mp4](outputs/nanda-demo-video/muse-wajo-demo-v4.mp4) |
| Earlier Alice and Bob account demo | [muse-wajo-demo-v3.mp4](outputs/nanda-demo-video/muse-wajo-demo-v3.mp4) |
| Earlier exact-prompt version | [muse-wajo-demo-v2.mp4](outputs/nanda-demo-video/muse-wajo-demo-v2.mp4) |
| Original version | [muse-wajo-demo.mp4](outputs/nanda-demo-video/muse-wajo-demo.mp4) |
| Bakery walkthrough prompts | [prompts.json](work/nanda-video/revision-v4/prompts.json) |
| Earlier live demo prompts | [prompts/demo-prompts.txt](prompts/demo-prompts.txt) |
| Separate bakery reading guide, video, and screenshots | [outputs/nanda-demo-v4](outputs/nanda-demo-v4) |
| Downloadable guide package | [nanda-demo-v4.zip](outputs/nanda-demo-v4.zip) |
| Version 4 narration script | [narration.txt](work/nanda-video/revision-v4/narration.txt) |
| Version 4 captions | [SRT](outputs/nanda-demo-video/muse-wajo-demo-v4.srt), [VTT](outputs/nanda-demo-video/muse-wajo-demo-v4.vtt) |
| Bakery animation, source and feedback checklist | [revision-v4](work/nanda-video/revision-v4) |
| Production brief and earlier changes | [docs/production-brief.md](docs/production-brief.md) |
| Edit sources and recording details | [docs/production.md](docs/production.md) |

GitHub may show a download link for larger videos. The live guide has a video player.

## Contents

- `outputs/` contains the delivered videos, guides, screenshots, captions, and guide ZIPs.
- `work/nanda-video/revision-v5/` contains the known-ID bakery player, canonical prompts, final audio timing, voice sources, rendering scripts, and validation records.
- `work/nanda-video/revision-v4/` contains the bakery player, canonical prompts, scene timing, voice sources, capture instructions, rendered footage, and validation records.
- `work/nanda-video/alice-bob/` contains the earlier live demo edit, prepared capture clips, narration audio, animation source, screenshot sources, and validation records.
- `work/nanda-video/retake/` contains the previous exact-prompt edit and its prepared clips.
- `work/nanda-video/production/` and `work/nanda-video/claude/` contain the earlier renderer, motion assets, draft exports, and editing records.
- `work/nanda-video/captures/` contains the prepared capture clips for the original version.
- `work/nanda-demo/` contains the original guide source and theme work.
- `website/demo/` contains the deployed guide source, assets, and page checker.
- `docs/archive-manifest.json` lists archived project files with sizes and SHA-256 hashes.

The archive includes draft exports, individual clips, rendered segments, and copies kept with each deliverable. Historical notes describe the state when they were written; some refer to assets that were still pending at that time.

## Run the guide locally

From the repository root:

```sh
python3 -m http.server 8765 --directory website
```

Open <http://localhost:8765/demo/>. Serving over HTTP lets the browser load the caption track.

## Rebuild the videos

For version 5, follow the [current rebuild instructions](work/nanda-video/revision-v5/README.md). The HTML player loads the same prompt file used to build the reading guide. The screenshots are extracted directly from the final MP4, with timestamps and hashes recorded in the output folder.

For version 4, follow the [earlier bakery recording and assembly instructions](work/nanda-video/revision-v4/README.md).

The commands below rebuild the earlier version 3.

Install FFmpeg and Python with NumPy and Pillow. The original environment used FFmpeg 8.1.2, Python 3.14.6, NumPy 2.4.6, and Pillow 12.3.0.

On a Mac with `/opt/homebrew/bin/python3`, the original renderer uses that interpreter for animation subprocesses, even inside a virtual environment. Make NumPy and Pillow available to that interpreter and use it for the commands below. The archived production scripts are unchanged.

```sh
python3 -m pip install numpy Pillow
cd work/nanda-video/alice-bob/production
python3 edit/assemble.py --edl ../edit-v3.json --mode final --dry-run
python3 edit/assemble.py --edl ../edit-v3.json --mode final
```

The renderer uses the included prepared clips and narration. It writes `work/nanda-video/alice-bob/out/muse-wajo-demo-v3.mp4`. See [production details](docs/production.md) for the other versions and validation commands.

## What stays local

Uncropped desktop recordings, signup and inbox screenshots, private source inspection frames, and account credentials are not public. The archive contains the cropped and masked footage used in the edits. Downloaded speech models, installed Python dependencies, bytecode, and compiled helpers are also omitted; the helper source is included.

[The omission list](docs/omitted-files.json) records each omitted project file and its reason. No original local file was deleted or changed.

Two close-ups in version 3 repeat prompt insertion without sending again. The sent messages and receipts are from the completed exchange. [The recording notes](outputs/nanda-demo-video/recording-notes-v3.txt) and [clip selections](work/nanda-video/alice-bob/clip-selections.json) document the sources, times, crops, and masks.

## Related repositories

- [nanda-messagebox-skill](https://github.com/dhve/nanda-messagebox-skill) hosts the live guide. The archive retains earlier guide versions alongside the current bakery walkthrough.
- [projnanda/nanda-index-v2](https://github.com/projnanda/nanda-index-v2) supplied the site theme reference, checked out at `fa65834d3dc074afbe3fddb8cd30a9eff25ab926` during production. The unmodified reference checkout is linked rather than duplicated.

Existing font and theme license notices are retained with their assets. Publishing this archive does not add a new license for the personal voice or third-party app branding.
