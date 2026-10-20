# Known ID resolution video revision

Spec: User's October 19 feedback and the existing demo requirements.

## Constraints

Use known IDs only. Alice is a business using Muse; Bob is a consumer using Wajo. Show a direct published business endpoint and a later business-initiated message resolved through Index to Bob's hosted card. Separate resolution from message delivery and permissions. Keep the animation clearly illustrative, readable, gently transitioned, under three minutes and narrated with the saved Vedh voice. Never speak Nanda. Use canonical prompts in the video, guide and review document. Preserve the historical live guide and videos. Publish only reviewed deliverables and source, never private inputs.

## Tasks

1. Research the paper and official Poppy demo. Draft canonical narration, prompts and a numbered review script. Create and visually inspect DOCX; import as a Google Doc when Drive is connected.
2. Adapt the existing deterministic player. Replace discovery scenes with known-ID resolution and a later bakery-to-consumer update. Match narration timing to the visuals.
3. Render the video, inspect frames and transitions, verify runtime and transcript, and extract guide screenshots from the final export.
4. Add the new video and a separate matching guide to the existing site; archive source and artifacts publicly. Verify live URLs and provide the Google Doc link.

## Validation

Readability: large text, no clipped boxes, stable Alice-left/Bob-right identities.
Content: no search UI or capability query, known ID to hosted card to endpoint, new business-to-consumer contact, permission check, bidirectional exchange.
Media: under 180 seconds, no spoken Nanda, captions aligned, no long padded pauses, 0.9-second dissolves.
Prompts: exact equality across canonical data, player and reading guide.
Preservation: existing live page content retained; new video and guide link added only.

## Execution notes

Artifact revision is outside a Git repository until packaging; source lives in a new revision-v5 folder. Existing render engine is reused. Verification will focus on artifact content, exported media and live deployment rather than tests that mirror static prose.
