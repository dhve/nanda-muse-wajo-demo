# Muse and Wajo demo archive

This repository contains the videos, prompts, guides, screenshots, narration, animation code, editing files, and production notes from the Muse and Wajo demo.

Alice uses Muse. Bob uses Wajo. Their agents discover each other through NANDA Index and exchange messages through Agent Box.

[Watch the current demo and follow the guide](https://my.nandaindex.org/demo/).

## Start here

| Item | File |
| --- | --- |
| Current Alice and Bob video, 2:58 | [muse-wajo-demo-v3.mp4](outputs/nanda-demo-video/muse-wajo-demo-v3.mp4) |
| Earlier exact-prompt version | [muse-wajo-demo-v2.mp4](outputs/nanda-demo-video/muse-wajo-demo-v2.mp4) |
| Original version | [muse-wajo-demo.mp4](outputs/nanda-demo-video/muse-wajo-demo.mp4) |
| Exact demo prompts | [prompts/demo-prompts.txt](prompts/demo-prompts.txt) |
| Current guide, video, and screenshots | [outputs/nanda-demo-v3](outputs/nanda-demo-v3) |
| Downloadable guide package | [nanda-demo-v3.zip](outputs/nanda-demo-v3.zip) |
| Final narration script | [narration.txt](work/nanda-video/alice-bob/narration.txt) |
| Captions | [SRT](outputs/nanda-demo-video/muse-wajo-demo-v3.srt), [VTT](outputs/nanda-demo-video/muse-wajo-demo-v3.vtt) |
| Production brief and changes | [docs/production-brief.md](docs/production-brief.md) |
| Edit sources and recording details | [docs/production.md](docs/production.md) |

GitHub may show a download link for larger videos. The live guide has a video player.

## Contents

- `outputs/` contains the delivered videos, guides, screenshots, captions, and guide ZIPs.
- `work/nanda-video/alice-bob/` contains the final edit, prepared capture clips, narration audio, animation source, screenshot sources, and validation records.
- `work/nanda-video/retake/` contains the previous exact-prompt edit and its prepared clips.
- `work/nanda-video/production/` and `work/nanda-video/claude/` contain the earlier renderer, motion assets, draft exports, and editing records.
- `work/nanda-video/captures/` contains the prepared capture clips for the original version.
- `work/nanda-demo/` contains the original guide source and theme work.
- `website/demo/` contains the deployed guide source, assets, and page checker.
- `docs/archive-manifest.json` lists the 957 copied files with sizes and SHA-256 hashes.

The archive includes 184 MP4 files and 25 audio files. Those counts include draft exports, individual clips, rendered segments, and copies kept with each deliverable. Historical notes describe the state when they were written; some refer to assets that were still pending at that time.

## Run the guide locally

From the repository root:

```sh
python3 -m http.server 8765 --directory website
```

Open <http://localhost:8765/demo/>. Serving over HTTP lets the browser load the caption track.

## Rebuild the final video

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

Two close-ups in the final video repeat prompt insertion without sending again. The sent messages and receipts are from the completed exchange. [The recording notes](outputs/nanda-demo-video/recording-notes-v3.txt) and [clip selections](work/nanda-video/alice-bob/clip-selections.json) document the sources, times, crops, and masks.

## Related repositories

- [nanda-messagebox-skill](https://github.com/dhve/nanda-messagebox-skill) hosts the live guide. This archive contains the deployed demo at commit `8d3084181a0ca7d79644eda78a503c08ebdb42cf`.
- [projnanda/nanda-index-v2](https://github.com/projnanda/nanda-index-v2) supplied the site theme reference, checked out at `fa65834d3dc074afbe3fddb8cd30a9eff25ab926` during production. The unmodified reference checkout is linked rather than duplicated.

Existing font and theme license notices are retained with their assets. Publishing this archive does not add a new license for the personal voice or third-party app branding.
