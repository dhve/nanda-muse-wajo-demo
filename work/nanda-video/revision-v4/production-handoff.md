# Production handoff: animated bakery walkthrough player (v4)

Status: ready to record. Static QA 29 of 29 pass; root's browser qa=1 reports all boxes OK. Not rendered in a browser by Claude; visual review is root's.
No apps or browsers controlled, no audio generated, nothing published. v3 and all earlier assets untouched.

## Run

```
cd /Users/admin/Documents/Codex/2026-10-14/giv/work/nanda-video/revision-v4
python3 -m http.server 8642
```

| Purpose | URL (append to http://localhost:8642/production/player/) |
|---|---|
| Review with controls | `index.html` |
| With narration on the same clock | `index.html?audio=1` (loads ../../narration.wav) |
| Recording: visible Start, 3-2-1 countdown, controls hidden | `index.html?record=1` (add `&audio=1` to hear it; `&countdown=5` for longer) |
| Still frame for keyframes | `index.html?frame=SECONDS` |
| Cursor rehearsal markers (never shown in recording) | `index.html?targets=1`, then `player.listTargets()` in the console for exact numbers |
| Text fit report in the page | `index.html?qa=1` |
| Retimed scenes | `index.html?timing=path.json` with `{"goal":16,...}` or `{"scenes":[{"id","duration"}]}`; beats scale linearly |

Keys: Space play or pause, R restart, Left and Right arrows jump scenes, Esc shows controls in recording mode.
The countdown ends exactly at t = 0 (blank pale frame, then the opening fades in). No autoplay.

## Files (all new, all under production/)

- `production/player/index.html`: all 15 scenes as static, absolutely positioned HTML on a 1920x1080 canvas.
- `production/player/player.js`: time-driven engine (pure function of time, so seek and pause are exact), controls, recording mode, audio clock, timing override, QA and rehearsal overlays.
- `production/player/player.css`: theme (Inter, #f5f8fd, navy, Alice #2563eb, Bob #087f5b).
- `production/player/assets/`: `inter-latin.woff2` and `OFL.txt` (same font as the guide), `qr-nandaindex.svg`.
- `production/tools/qr.swift`: makes the QR with CoreImage and verifies it with CoreImage's QR detector.
- `production/qa/check_player.py`: static QA (run from revision-v4). Uses ../claude/lib/brand.py read-only for Inter measurement.

Content is loaded at run time from root's `scenes.json` (titles, order, durations) and `prompts.json` (every prompt and
the message text inside ask, reply, meeting and meeting_reply). The page contains no copy of any prompt.

## Scene timing (from scenes.json, total 178 s) and what is on screen

| Start | Dur | Scene | Visual |
|---|---|---|---|
| 0 | 16 | goal | Large disclosure card; Bob: "I need a birthday cake." "Which bakery?"; Alice's Bakery sign; dashed link |
| 16 | 13 | connect_alice | Muse (Illustration), setup_alice in the message box, gentle zoom, sent, expected result with Agent Box address |
| 29 | 9 | connect_bob | Wajo (Illustration), setup_bob, zoom, sent, expected result |
| 38 | 14 | verify | Setup email with code 123456 and masked "Your agent's credential", "Use your own email and code"; Muse chat "My code is 123456."; secure API key dialog (masked); "If Muse asks, copy ..." line; "Keep it private" |
| 52 | 9 | ready | Index above Alice's listing card: offers, reach it, "Ready to be found" |
| 61 | 15 | discover | Wajo: discover prompt (no address), "No email or agent address needed", search, found Alice's Bakery |
| 76 | 13 | handshake | Index top, hosted card middle, people row: 1 Search, 2 Resolve, 3 Read the card, Published by Alice; host39 or list39 |
| 89 | 16 | card | Card checks: capabilities, contact route, authentication; "Before sending, Wajo asks Bob to approve."; "A listing alone doesn't guarantee safety." |
| 105 | 7 | manual_search | nandaindex.org/explore (Illustration): "birthday cake bakery", Alice's Bakery result, caption |
| 112 | 10 | ask | Wajo: ask prompt, Approve; then the Index as a pale inactive panel ("Not used for messages"), question moves Bob to Alice through Agent Box |
| 122 | 15 | reply | Muse: check_alice, Bob's question, reply prompt; then, with the Index inactive, reply moves Alice to Bob through Agent Box |
| 137 | 10 | received | Wajo: check_bob, Alice's Bakery replied; "Both people stayed in their own apps." |
| 147 | 10 | another | "Second illustrative exchange": meeting card (Bob), meeting_reply card (Alice), question then reply |
| 157 | 12 | roles | Index above (neutral discovery across agent ecosystems), Agent Box between (handles the messages) |
| 169 | 9 | end | Working QR to https://nandaindex.org, nandaindex.org, my.nandaindex.org/demo, small SKILL.MD label; fully visible by 0.8 s, held 8.2 s |

Beats inside each scene follow the aligned captions (for example the cake question leaves Bob on "Agent Box carries
that message"). Alice stays left and Bob right in every scene; the person whose app is shown gets a soft halo and the
other stays compact on their own side.

## Expected cursor positions (canvas pixels, 1920x1080; global time)

| Time (s) | Scene | Point at | x, y |
|---|---|---|---|
| 17.2 to 23.9 | connect_alice | Muse message box (zoom keeps it fixed) | 980, 873 |
| 29.8 to 34.1 | connect_bob | Wajo message box | 960, 865 |
| 38.6 to 40.4 | verify | Code 123456 in the setup email | 683, 420 |
| 39.4 to 40.4 | verify | Masked credential in the email | 818, 576 |
| 40.6 to 42.0 | verify | Muse message box | 980, 898 |
| 44.0 to 50.0 | verify | Secure API key field | 860, 566 |
| 52.6 to 61.0 | ready | Alice's listing card | 1000, 460 |
| 61.8 to 68.7 | discover | Wajo message box | 960, 865 |
| 77.0 to 79.6 | handshake | NANDA Index | 960, 206 |
| 80.4 to 87.0 | handshake | Hosted agent card | 960, 422 |
| 90.6 to 92.0 | card | Capabilities line | 826, 386 |
| 92.0 to 93.6 | card | Contact route line | 866, 506 |
| 93.6 to 96.2 | card | Authentication line | 776, 626 |
| 105.6 to 107.6 | manual_search | Search box | 960, 392 |
| 106.6 to 110.0 | manual_search | Alice's Bakery result | 960, 586 |
| 112.4 to 113.2 | ask | Wajo message box | 960, 865 |
| 114.0 to 115.0 | ask | Approve | 648, 580 |
| 122.5 to 128.6 | reply | Muse message box | 980, 898 |
| 137.5 to 138.8 | received | Wajo message box | 960, 890 |
| 139.9 to 146.0 | received | Alice's reply | 858, 506 |
| 169.5 to 178.0 | end | QR code | 710, 410 |

Values are approximate centers; `?targets=1` shows live markers and `player.listTargets()` prints exact ones.

## Suggested keyframe times (use ?frame=)

8, 21, 35, 45, 58, 72, 86, 101, 109, 118, 133, 144, 154, 166, 175.

## Validation performed

`python3 production/qa/check_player.py` (PASS 29): durations 178 s; every scene has markup and in-range beats;
every scene shows its canonical prompt by id, none copied into the page; discovery prompt has no address; message
direction (Bob right to left, Alice left to right) and midpoint inside Agent Box, never rising to the Index; Index a pale inactive panel with dark text
during messages; Agent Box label above its box and clear of moving messages; handshake order Index (150 to 262) above card (344 to 500) above people (500); flow labels; card checks,
owner approval and safety caveat; disclosure persistent and in the opening; every app screen labeled Illustration;
verify wording, masked credential and "Use your own email and code"; manual search page; end card text and 8.2 s hold;
QR decodes to https://nandaindex.org and matches the asset; no canvas text under 30 px; colors and anchors; no yellow;
no drawn or hidden cursor; 100 text boxes fit with kerned Inter. Also `node --check player.js` and an HTML nesting check.

Fixes from root's review are in: the disclosure pill no longer overlaps its subtitle; the search page shows
nandaindex.org/explore; the inactive Index in ask and reply is a pale panel with dark readable text (no transparency);
the Agent Box label sits just above its delivery box (y 498 to 550, box 560 to 660) in ask, reply, another and roles,
so moving messages never cover it. No timings changed.

## Feedback items covered by the visuals

F01 end card QR and link, 8.2 s hold. F02 rounded panels. F03 full-frame illustrative screens (cursor is root's capture).
F04 and F09 Index finds the card, shown above. F05 active app fills most of the frame. F06 long holds on each input and
result. F07 plain Inter, no yellow or decorative lines. F08, F11, F12, F13 Alice blue left, Bob green right, illustrative
addresses. F10 Agent Box horizontal between them. F14 bakery and cake question. F15 figurines. F16 second example.
F17 and F19 app, exact input and result per step. F18 no SKILL.MD setup jargon (only a small label on the end card).
F20 full app then zoom, cursor targets listed. F21 goal stated first. F22 capability search without an address.
F23 and F24 card check of capabilities, contact and authentication before messaging. F25 resolve and card retrieval
shown as an illustration. F26 prompts come only from prompts.json. F29 guide theme. F30 manual search scene.
F27 and F28 (voice, guide screenshots) are root's.

## Issues and notes

- PNG keyframes were not exported: no non-browser HTML renderer is available. Use `?frame=SECONDS` while capturing.
- Illustrative Agent Box addresses follow the real pattern: alicebakerycom@agentboxnanda.org and bobgmailcom@agentboxnanda.org.
- The card's "OAuth 2.0 required before sending" reflects research/alice-card.json (authentication type oauth2).
- If root retimes scenes, pass a timing file or edit scenes.json; beats scale with each scene's length.
- Agent cards and quoted messages use an even border in the owner's color (Alice blue, Bob green) rather than a thick side accent.
