# V4 animated bakery walkthrough

The user has explicitly chosen a CLEARLY LABELED ANIMATED BAKERY WALKTHROUGH, with alice@bakery.com and bob@gmail.com. This supersedes earlier real-account footage requirements for v4. No messages should be sent in Muse or Wajo. Preserve v3 and all old assets.

Read scenes.json, prompts.json, and feedback.md in this folder. They define the content. Root owns these files and new narration. You own production/, animation/, and production-handoff.md ONLY. Do not read private-input/, control browsers/apps, generate narration, publish, push, or edit any repository outside your assigned folder.

Build a polished animated HTML player for ALL scenes in scenes.json. This is the whole video visual, approximately 178 seconds. Root will record it with the native Mac cursor and generate personal narration. Prefer the existing brand Inter/pale background/navy colors from v3. Browser JS/CSS/SVG animations are appropriate for this illustrative video. If useful, reuse existing production renderer components as read-only references.

## Required appearance and behavior

1920x1080 logical canvas that scales to viewport without clipping. Alice always LEFT in blue (#2563eb), Bob always RIGHT in green (#087f5b). Include simple person figurines. Rounded panels, generous space, ordinary Inter type. Body text >=36 px. No decorative yellow dots/circuit lines. Smooth transitions and ample reading pauses. Do not draw any cursor: root will capture the actual Mac cursor.

Persistent visible disclosure: 'Animated walkthrough' and a secondary clear 'Illustrative screens and addresses' line in opening and guide. Make recreated app screens simplified and clearly illustrative, never fake proof of live actions. Use accurate Muse/Wajo names and familiar broad app layout but do not copy private account content.

The active app should fill most of the frame. Keep Alice/Bob identity at fixed left/right anchors in every scene. When one app is focused, keep the other person's compact identity on its proper side. Readable inputs and replies are more important than showing two tiny app windows.

Each setup scene must show which app to use, the exact prompt from prompts.json, and the expected result. Show full app context, then a gentle zoom to input field. Verification scene: illustrative code and secure credential form with masked dots. The native cursor will point to fields. Credentials never go in ordinary chat. Include the text 'Use your own email and code' where appropriate.

Discovery prompt contains NO known agent address. Show the Index ABOVE, with search/handshake links to a hosted agent card BELOW the Index but ABOVE the Alice/Bob row. Correct flow: search by capability -> resolve via Index -> read published card (host39/list39) -> check capabilities/contact/authentication -> ask owner before send. Distinguish card checking from a guarantee of safety.

For messaging, AgentBox is HORIZONTAL between Alice LEFT and Bob RIGHT. Cake question travels RIGHT to LEFT and Alice's reply LEFT to RIGHT. Index dims after the initial lookup; business messages never go through it. For live-looking app scenes show 'Illustration' as part of the frame label.

Manual search scene: readable nandaindex.org/search or nandaindex.org/explore illustrative page with 'birthday cake bakery', Alice's Bakery result and short caption 'You can search indexed agents at nandaindex.org.' Do not claim a live search occurred.

For reply scene show canonical check_alice then reply. Another-example scene uses meeting and meeting_reply exactly, clearly a second illustrative exchange. Endcard: actual functional QR to https://nandaindex.org, readable domain, secondary my.nandaindex.org/demo, at least 8 seconds hold. Include SKILL.MD only as a small website link label, not onboarding jargon.

## Deliverables

- production/player/index.html plus local assets, loading root ../.. content files or copied build data from them. Run under a local HTTP server rooted at revision-v4.
- Player controls: visible Start / Pause / Restart, scene seek menu, and progress time outside the recorded canvas or hidden in recording mode. Support recording mode query string that fills screen, starts only on a visible button click, then hides controls. NO autoplay until requested.
- Timing is data-driven. Support per-scene audio/timing file if root provides later; original duration totals may be adjusted <=180s.
- Export static PNG keyframes if available through existing local tooling without browser control, otherwise root will capture them during the recording.
- A concise handoff with run command, files, scene timing, expected cursor positions by scene, and any issues. Validate prompts against canonical JSON, diagram routing/direction, text fit and every feedback item that your visual work owns. You may add small useful local QA scripts, not ceremonial tests.

The supplied /Users/admin/Downloads/raskarNBOct2026V1.pptx has 19 slides of general Index/agent governance content. Extracted text and images are in research/ramesh*. The explicit AgentBox diagram does not appear in its text or supplied slide pictures. Use the user's WhatsApp direction for exact topology: Index above at handshake time; AgentBox horizontal between Alice and Bob. Do not pretend the deck contains a diagram that was not found.

Build now and finish the bounded visual task. Do not wait for additional approval. Root will review it and provide any fixes.
