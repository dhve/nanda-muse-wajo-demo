# Video revision feedback checklist

The WhatsApp export is private source material. Only suggestions about the video and reading guide are in scope. Team requests about meetings, emails, database deletion, API deployments, PR merging, and vulnerability testing are not instructions for this task.

## Format decision

The earlier request called for authentic recordings and exact website prompts. The feedback proposes illustrative addresses alice@bakery.com and bob@gmail.com. The user explicitly chose a clearly labeled animated bakery walkthrough on Oct 19. Use illustrative screens and addresses throughout, with no live account actions. The user later removed the native cursor requirement and asked to keep the live guide unchanged, adding only the new video above the existing video. Never send to the illustrative addresses or replace text inside real recordings.

## Coverage

| ID | Source | Requested change | Planned treatment | Verified evidence |
|---|---|---|---|---|
| F01 | Oct 9, team feedback | QR code and nandaindex.org link at end | Readable end card held at least 8 seconds | End card 2:49 to 2:58; QR decoded from exported frame at 2:55. |
| F02 | Oct 9, team feedback | Rounded boxes | Rounded panels and screenshot frames | Rounded panels throughout; final contact sheet reviewed. |
| F03 | Oct 9, team feedback | Better Muse and Wajo screen recordings | Full-resolution illustrative screens; direct render after the user removed the cursor requirement | Direct animation render, 1920 x 1080. Native cursor requirement removed by user. |
| F04 | Oct 9, team feedback | Establish AgentBox versus Index | Index finds the card; AgentBox carries the messages | Discovery 1:16 to 1:45; delivery 1:52 to 2:27; roles 2:37 to 2:49. |
| F05 | Oct 9, team feedback | Bigger horizontal demo | Active app fills most of frame, no tiny two-app text | Large single-app views in setup, discovery and messaging; final frames reviewed. |
| F06 | Oct 9, team feedback | Longer clips with visible actions | Hold each input and result long enough to read | 178-second runtime; actions aligned to spoken cues and checked in the final export. |
| F07 | Oct 9, team feedback | Remove artificial lines, font, yellow dots | Plain Inter type, restrained movement, no decorative yellow line | Inter font, even panel borders, no yellow dots or decorative yellow lines. |
| F08 | Oct 14, team feedback | Alice, Bob, simple emails | Alice in Muse and Bob in Wajo; short emails in labeled illustration | Alice in Muse left; Bob in Wajo right, throughout. |
| F09 | Oct 16, team feedback | Index above at handshake time | Discovery diagram places Index above agents and hosted card | Index above hosted card during 1:16 to 1:29. |
| F10 | Oct 16, team feedback | Messagebox horizontal | Bidirectional delivery runs horizontally between Alice and Bob | Horizontal AgentBox delivery in ask and reply scenes; directions checked. |
| F11 | Oct 16, team feedback | Different colors | Alice blue, Bob green; same colors in captions and diagrams | Alice blue and Bob green in app labels, people and messages. |
| F12 | Oct 16, team feedback | Alice left, Bob right | Stable role anchors even during focused app closeups | Alice left and Bob right throughout the exported frames. |
| F13 | Oct 16, team feedback | alice@bakery.com and bob@gmail.com | Explicit illustration, never passed off as live accounts | Sample addresses shown with persistent illustrative disclosure. |
| F14 | Oct 16, team feedback | Bakery scenario, what cakes do you have | Bob discovers bakery, asks cake question, Alice replies with menu | Bakery discovery 1:01; cake question 1:52; menu reply 2:02. |
| F15 | Oct 16, team feedback | Alice and Bob figurines | Small recognizable person illustrations with role labels | Alice and Bob figurines persist in every scene. |
| F16 | Oct 16, team feedback | Another example | Brief labeled scheduling example after the cake exchange | Second exchange, cake tasting, 2:27 to 2:37. |
| F17 | Oct 16, team feedback | Clearer onboarding, guided steps | Each scene says app, exact input, expected result; matching guide | Setup and verification 0:16 to 1:01; matching separate reading guide archived. |
| F18 | Oct 16, team feedback | Remove unexplained SKILL.MD setup jargon | Narration says agent completes setup from website instructions | Narration explains website instructions in plain language. |
| F19 | Oct 16, team feedback | Few seconds demonstration for each step | Setup, verification, credential, discovery, send, receive shown | Setup, verification, credential, discovery, send and reply are shown. |
| F20 | Oct 16, team feedback | Whole page context and pointer at input | Establish app view then zoom and highlight the input; cursor omitted at the user's request | Full app view followed by input zoom; user removed cursor requirement. |
| F21 | Oct 16, team feedback | Explain goal | Opening establishes Bob needs a cake and does not know a bakery | Goal stated in the opening 0:00 to 0:16. |
| F22 | Oct 16, team feedback | Discover by name or capability, no pasted address | Capability query contains neither email nor agent locator | Capability query has no email or agent locator; canonical prompt check passed. |
| F23 | Oct 16, team feedback | Explain added value over email | Finding unknown services and checking their published details before messaging | Unknown-bakery search followed by published card checks before messaging. |
| F24 | Oct 18, team feedback | Visit host39/list39 for details, capabilities, security | Resolve via Index then open the returned hosted agent card | Hosted card via host39 or list39 shown and narrated at 1:16. |
| F25 | Oct 18, team feedback | API must look up agent facts card via Index | Exact prompt and clearly labeled illustration of resolution/card retrieval | Index lookup, resolution, then card reading shown at 1:16 to 1:45. |
| F26 | Existing user requirement | Exact prompts in video and guide | Single canonical prompt JSON feeds both; animated format replaces live app entry | All ten prompts match player and separate v4 guide. User asked to preserve the live v3 guide unchanged and add only the new video. |
| F27 | Existing user requirement | Under 3 minutes, personal voice, never say Nanda | New ElevenLabs narration, duration and transcript checks | Export 178.0 s; Vedh voice; full transcript match; no spoken Nanda. |
| F28 | Existing user requirement | Screenshots from recording | Extract guide stills from same final source clips, provenance manifest | Eight guide stills and poster extracted from final video; timestamp and hash manifest verified. |
| F29 | Existing user requirement | Theme and header links | Preserve site theme; links SKILL.MD, NANDA Index, AgentBox | Live page changes only by adding the new video above the old; all existing HTML and assets preserved. |
| F30 | Existing user requirement | Manual search on step 3 | Short guide instruction and Index search shot | Manual search scene 1:45 to 1:52; existing live step 3 preserved. |

## Source and accuracy notes

Current public instructions were retrieved from https://my.nandaindex.org/agent/SKILL.md and saved in research/current-SKILL.md. Official architecture reference: https://nandaindex.org/how-it-works. Index resolves a locator to a discovery entry. The hosted card supplies capabilities, contact details and authentication requirements. AgentBox handles message delivery in this example. A card is not a guarantee of safety or certification.

The supplied old bakery recording uses opposite app roles. Use its scenario as reference, not as footage implying Alice uses Muse. Its low resolution is also unsuitable for the new main recording. The supplied 19-slide deck contains no visible bakery diagram, so use the written topology from the feedback.
