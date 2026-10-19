# Bakery video revision plan

> Execute the authorized revision continuously. Use the existing Claude Mac production session for the player and root for narration, guide and recording.

**Goal:** Make a clear animated bakery walkthrough that addresses every relevant suggestion in the supplied chat.

**Architecture:** One canonical prompt file feeds the animated player and reading guide. One scene file supplies narration and timing. Record the player with the native Mac cursor, then use frames from that recording for the guide.

**Tech stack:** HTML, CSS, SVG, JavaScript, native macOS screen capture, FFmpeg and ElevenLabs Vedh voice.

**Spec:** ../../../feedback.md, ../../../animation-brief.md, ../../../scenes.json and ../../../prompts.json.

## Constraints

- The user chose a clearly labeled animated walkthrough. No live Muse/Wajo messages or new accounts.
- Alice uses Muse, left in blue. Bob uses Wajo, right in green.
- Illustrative addresses are alice@bakery.com and bob@gmail.com.
- Exact prompts match the guide. Credentials remain masked in the secure field.
- Index above for discovery and hosted card lookup. AgentBox horizontal for bidirectional delivery.
- Native cursor, calm pacing, legible text, 1920 by 1080, under 180 seconds.
- Personal Vedh voice. No spoken Nanda. On-screen branding is allowed.
- Preserve v3. Keep the source chat and unrelated private information out of the deliverable and public repo.

## Tasks

- [x] Read complete feedback and inspect supplied references. Save all relevant changes in feedback.md.
- [x] Resolve format conflict with user. Write canonical prompts, scene copy and narration.
- [x] Build the animated player in Claude. Check each scene and screen layout against the feedback checklist.
- [x] Generate narration with Vedh in ElevenLabs. Align every paragraph, pace it naturally within 178 seconds, and create captions.
- [x] Build matching reading guide with app, exact input, expected result and clear illustrative disclosure.
- [ ] Record player with actual cursor. Extract screenshots from the recording and assemble final MP4.
- [ ] Verify duration, text and prompt readability, direction of messages, card lookup, no forbidden spoken name, captions, QR, and complete feedback coverage.
- [ ] Deliver the new video and guide separately from v3, with reviewed production files available for archive.

## Review focus

Check that illustrative addresses and responses are never presented as live evidence. Check the Index pointer is distinguished from the hosted card and message delivery. Check small captions and labels remain legible after export. Check no prompt differs between player and guide. Check narration and visual timing remain aligned after pacing changes.
