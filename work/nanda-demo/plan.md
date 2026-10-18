# NANDA demo guide implementation plan

**Goal:** Help everyday readers set up Muse and Wajo with NANDA Index and exchange messages in both directions.

**Architecture:** One buildless HTML page with embedded CSS and small copy controls. Use real screenshots from the authorized Media Lab Chrome sessions. Deliver a self-contained HTML file and a folder/ZIP with screenshots.

**Tech stack:** HTML, CSS, plain JavaScript. No installation required for readers.

**Spec:** User requests in this conversation, including two demo aliases and bidirectional messaging.

## Constraints

- Use Media Lab Chrome for Muse and Wajo; personal Vedh Chrome only to retrieve the two demo verification emails.
- Preserve existing non-demo mailboxes and credentials.
- Use short prompts with visitor-owned email and peer agent address placeholders.
- Explain NANDA as neutral discovery and resolution, with Agent Box handling delivery in this demo.
- Claim only what the recorded setup and message exchange demonstrate.
- Omit credentials, live verification codes, unrelated inbox content, and private contact information from deliverables.
- Use the outputs directory for deliverables and work for scratch records.

## Tasks

- [x] Complete both demo mailbox setups and record returned addresses and listing state.
- [x] Resolve each demo identity through NANDA and exchange a message in each direction, with receipt on both sides.
- [x] Capture clean screenshots of setup, verification prompt, listed state, and message receipts.
- [x] Build a readable responsive page with brief explanation, short prompts, setup walkthrough, success checklist, screenshots, and troubleshooting.
- [x] Verify copy controls, links, images, mobile layout, keyboard usability, and absence of secrets.
- [x] Package a standalone HTML and ZIP; open the guide for the user.

## Review focus

- Distinguish a human verification email from the public agent address.
- Different emails are necessary for two independent demo mailboxes.
- Muse may require secure credential entry; a code is not a credential.
- Automatic mailbox checks vary by app; provide a manual check prompt.
- A sent message alone is not proof of receipt; show the receiving app.

## Decisions

- Local static deliverables match the explicit HTML request. No hosting or public publishing is needed.
- The page can be built from the stated scope without another approval round.
- Browser checks are proportionate to the reversible static guide; no test framework or repository is needed.

## Progress

- Read live setup instructions and existing successful non-demo sessions.
- Started separate Wajo and Muse demo conversations with the requested aliases.
- Opened and filtered the personal inbox for the two demo emails.

## Verification record

- Public NANDA resolver returned status active and emailVerified true for both demo identities.
- Wajo sent greeting with message d3be6f74-fd1a-477a-b21c-2cd68f077ec1 in conversation 98d0e6ae-8f33-4fb3-b5a3-8ebe37d6df8e.
- Muse displayed the received greeting and its delivered reply.
- Wajo displayed Muse reply 69a1a7ed-e137-45d8-ae12-9db053694a9d in the same conversation.
- Muse has a separate demo credential and a five-minute inbox check; Wajo offers manual checks.
- All seven screenshot files visually inspected, with no codes, credentials, private inbox content, or phone numbers. Demo aliases were explicitly supplied for the screenshot task.
- Review improvement applied: distinct emails/aliases required beside the first quick prompt.
- Copy control verified by pasting the result into the browser address field without navigation.
- Screenshot modal opened and closed with Escape.
- Mobile viewport 390px showed no horizontal overflow; browser viewport reset.
- HTML local links, image references, IDs, alt text, copy labels and JavaScript syntax checked.
- Standalone-file check and final packaging review follow.

- Standalone file contains seven valid embedded JPEGs and no external assets. Browser tooling blocks file URLs, so direct file opening was not automated; HTTP desktop/mobile previews were verified.

## Theme and clarity update
- Match nandaindex.org using its frontend source and live Inter font.
- Replace duplicated prompt and walkthrough sections with five numbered steps.
- Preserve all seven screenshots, seven copy prompts, bidirectional proof, and the distinction between discovery and message delivery.
- Verify desktop/mobile layout and repackage standalone HTML and ZIP.

Theme update verified: 677 words versus 1,350 previously; 7 copy buttons; 7 screenshot files and embedded versions; Inter embedded; ZIP integrity; no desktop or 390px mobile overflow; copy success and image dialog confirmed; mobile menu confirmed. Deliverables regenerated.

## Publish the approved guide
- Replace the top site menu with buttons to setup instructions, NANDA Index, and Agent Box.
- Add demo/index.html and its assets to dhve/nanda-messagebox-skill, whose GitHub Pages source is codex/initial-build.
- Check the local page and mobile buttons, then push the additive change to the Pages branch and verify the live /demo URL.

Published successfully at https://my.nandaindex.org/demo/ from dhve/nanda-messagebox-skill, commit 46f49cf63385f194c10ca07911692cfdf25accdc. GitHub Pages run 38632563274 succeeded. Live HTML and all 8 image/font assets match source. Homepage redirect and agent/SKILL.md remain unchanged. Header verified on desktop and 390px mobile; live screenshot saved.
