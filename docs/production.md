# Production files

The directory layout preserves the original relative paths so the prepared clips, narration, captions, and renderer remain together. Some historical notes and capture scripts contain paths from the original Mac. The final assembly reads its inputs relative to the production directory and does not need those private recordings.

The original assembly scripts prefer `/opt/homebrew/bin/python3` for animation subprocesses if it exists. On that Mac setup, use the same interpreter for assembly and dependency installation. An unrelated virtual environment will not override the original interpreter preference. The source is preserved as used during production.

## Final Alice and Bob edit

| File or folder | Purpose |
| --- | --- |
| `work/nanda-video/alice-bob/edit-v3.json` | Final edit timeline and narration timings |
| `work/nanda-video/alice-bob/clips/` | Ten prepared capture clips |
| `work/nanda-video/alice-bob/parts/` | Individual masked shots, layouts, and concatenation records |
| `work/nanda-video/alice-bob/production/motion/` | Animation renderer and scenes |
| `work/nanda-video/alice-bob/production/edit/` | Assembly and video validation scripts |
| `work/nanda-video/alice-bob/narration.wav` | Final prepared narration |
| `work/nanda-video/alice-bob/audio/` | Narration takes, alignment, and intermediate audio |
| `work/nanda-video/alice-bob/captions.srt` | Final caption timings |
| `work/nanda-video/alice-bob/website-assets/` | Five screenshots and the video poster |
| `work/nanda-video/alice-bob/clip-selections.json` | Recording sources, timestamps, crops, masks, and repeated insertions |
| `work/nanda-video/alice-bob/out/qa_report.json` | Video validation report |
| `work/nanda-video/alice-bob/deployment-verification.json` | Live asset verification from deployment |

`compose_ab.py` documents how the private raw recordings were cropped and masked. Re-running that preparation step requires the original private footage. Rebuilding the finished video starts from the prepared clips already included here.

From `work/nanda-video/alice-bob/production`, run:

```sh
python3 edit/assemble.py --edl ../edit-v3.json --mode final --dry-run
python3 edit/assemble.py --edl ../edit-v3.json --mode final
python3 edit/qa.py ../out/muse-wajo-demo-v3.mp4 --mode final --edl ../edit-v3.json --no-whisper
```

The last command skips a new speech transcription. The archive includes the original transcription and validation records. The original final review passed 19 video checks; the website passed 21 checks.

## Earlier versions

The first edit uses `work/nanda-video/edit-final.json`, the prepared clips in `captures/`, and the narration in `audio/`.

The second edit uses `work/nanda-video/edit-retake.json`, `retake/clips/`, and `retake/narration.wav`. Its composition script, retiming script, prompt checks, captions, and final review records are in `retake/`.

The renderer copies in `claude/` and `production/` and their build files preserve the earlier animation, draft, and assembly work. Draft renders may contain labeled placeholders and should be read as production history.

## Validate the guide

From the repository root:

```sh
cd website
python3 demo/tools/check_page.py --publish
```

The checker validates the exact prompts, navigation, captions, video, screenshots, and page structure. The source snapshot matches the deployed guide at commit `8d3084181a0ca7d79644eda78a503c08ebdb42cf` of `dhve/nanda-messagebox-skill`.

## Recording provenance

The final video is 1920 by 1080 at 30 frames per second and runs for 178.5 seconds. Its screens come from native macOS recordings with the actual cursor. Recorded pixels are cropped and scaled; app responses and the cursor are not synthesized.

The reply-prompt and reply-check insertion close-ups were recorded after the exchange and were not sent again. The sent reply and received reply are from the real exchange. Both the guide screenshots and final capture clips use those recordings.

Credentials and verification codes are excluded or masked in the prepared clips. The private raw files and private inspection frames are listed in `omitted-files.json`. Safe inspection frames of the demo guide are retained.
