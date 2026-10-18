# Muse and Wajo demo video implementation plan

> For agentic workers: execute the bounded animation and editing tasks through Claude Code with Opus 5.5 Max. The main agent handles browser capture and ElevenLabs.

Goal: Deliver a calm, readable screen recording with restrained animations and Vedh's existing ElevenLabs voice, under 180 seconds.
Architecture: Real browser clips with native macOS cursor, short animated chapter cards, explanatory discovery and delivery diagram, voiceover and optional subtitles. 1920x1080, 30fps H.264/AAC MP4.
Spec: User request in this chat; source guide in outputs/nanda-demo/index.html.

Constraints:
- Never say Nanda in spoken audio, including URLs. Onscreen branding may use NANDA.
- Show actual setup evidence, public discovery, Wajo greeting, Muse receipt/reply, Wajo reply receipt.
- No fabricated UI, responses, or cursor. Trim waiting time without speeding up reading.
- Large readable UI crop, slow purposeful transitions, ≤180 seconds.
- Index discovers and resolves identities. Agent Box delivers messages in this demo.
- No secrets, personal inbox contents, or unrelated chats in output.

Review focus: Duration, all text readable, spoken name restriction, genuine cursor and evidence, synchronization and full bidirectional exchange.

Tasks:
- [x] Locate source guide and confirmed messages.
- [x] Set Claude Code to Opus 5.5 Max.
- [ ] Delegate animation assets and editing scaffolding to Claude subagents.
- [ ] Generate narration with existing personal voice in ElevenLabs kanos.biz account.
- [ ] Record real demo screens with native cursor, verify test capture first.
- [ ] Assemble clips, narration, animations and subtitles.
- [ ] Inspect representative frames and transitions; listen to narration; verify MP4 duration/decoding.
- [ ] Deliver MP4, transcript, and optional captions in outputs/nanda-demo-video.
