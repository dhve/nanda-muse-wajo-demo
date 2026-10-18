"""One-off generator for edit/edl.json (scratch helper, not part of the pipeline).

Derives segment times from ../audio/timeline.json and ../audio/captions.srt.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # claude/
AUDIO = ROOT.parent / "audio"

tl = json.loads((AUDIO / "timeline.json").read_text())
sec = {s["id"]: s for s in tl["sections"]}


def parse_srt(text):
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().splitlines()
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", lines[1])
        g = [int(x) for x in m.groups()]
        t0 = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        t1 = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append({"n": int(lines[0]), "start": t0, "end": t1, "text": " ".join(lines[2:])})
    return cues


cues = parse_srt((AUDIO / "captions.srt").read_text())
cue = {c["n"]: c for c in cues}


words = [w for s in json.loads((AUDIO / "transcript.json").read_text()) for w in s["words"]]


def out_time(src):
    for s in tl["sections"]:
        if s["source_start"] - 1e-6 <= src < s["source_end"] + 1e-6:
            return s["timeline_start"] + (src - s["source_start"]) / tl["speed"]
    raise ValueError(src)


def word_at(word, after, before):
    for w in words:
        t = out_time(w["start"])
        if after <= t < before and re.sub(r"[^A-Za-z]", "", w["word"]) == word:
            return t
    raise KeyError(word)


def speech_end(i):
    return sec[i]["timeline_end"] - sec[i]["pause_after"]


r = lambda t: round(t + 1e-9, 3)

# Boundaries on the output timeline.
B = {
    "intro": (0.0, sec[2]["timeline_start"]),
    "roles": (sec[2]["timeline_start"], speech_end(2)),
    "step1": (speech_end(2), sec[3]["timeline_start"]),
    "cap01": (sec[3]["timeline_start"], cue[7]["start"]),
    "cap02": (cue[7]["start"], cue[9]["start"]),
    "cap03": (cue[9]["start"], speech_end(3)),
    "step2": (speech_end(3), sec[4]["timeline_start"]),
    "cap04": (sec[4]["timeline_start"], cue[15]["start"]),
    "cap05": (cue[15]["start"], speech_end(4)),
    "step3": (speech_end(4), sec[5]["timeline_start"]),
    "cap06": (sec[5]["timeline_start"], sec[6]["timeline_start"]),
    "cap07": (sec[6]["timeline_start"], sec[7]["timeline_start"]),
    "cap08": (sec[7]["timeline_start"], speech_end(7)),
    "step4": (speech_end(7), sec[8]["timeline_start"]),
    "cap09": (sec[8]["timeline_start"], speech_end(8)),
    "step5": (speech_end(8), sec[9]["timeline_start"]),
    "cap10": (sec[9]["timeline_start"], sec[10]["timeline_start"]),
    "closing": (sec[10]["timeline_start"], sec[11]["timeline_start"]),
    "endcard": (sec[11]["timeline_start"], tl["duration"]),
}


W = {
    "Muse": word_at("Muse", 1.2, 4.0), "Wajo": word_at("Wajo", 4.0, 6.0),
    "address": word_at("address", 16.0, 19.0), "delivers": word_at("delivers", 16.0, 19.0),
    "Set": word_at("Set", 160.0, 162.0), "find": word_at("find", 160.0, 163.0),
    "send": word_at("send", 160.0, 164.0),
}


def say(start, end):
    """Caption text whose start falls inside [start, end)."""
    parts = [c["text"] for c in cues if start - 1e-6 <= c["start"] < end - 1e-6]
    text = " ".join(parts)
    return re.sub(r"\s+", " ", text).strip()


def rel(t, seg):
    return r(t - B[seg][0])


steps = {
    1: ("Set up both agents", "In Muse and Wajo"),
    2: ("Verify each email", "Send each code back in its app"),
    3: ("Find Muse and say hello", "Discover through NANDA Index"),
    4: ("Read and reply in Muse", "Wajo → Muse"),
    5: ("See the reply in Wajo", "Muse → Wajo"),
}


def motion(seg_id, scene, params=None, beats=None, notes=""):
    s, e = B[seg_id]
    d = {"id": seg_id, "kind": "motion", "scene": scene, "params": params or {}}
    if beats:
        d["beats"] = beats
    d["notes"] = notes
    d["say"] = say(s, e) or "(pause)"
    d["start"] = r(s)
    d["end"] = r(e)
    return d


def step(n):
    title, subtitle = steps[n]
    sid = f"step{n}"
    return motion(sid, "step", {"number": n, "total": 5, "title": title, "subtitle": subtitle},
                  notes=f"Step card {n} of 5 in the 3 s pause before the next section.")


def capture(seg_id, slot, notes, evidence, callout=None, privacy=None):
    s, e = B[seg_id]
    d = {
        "id": seg_id,
        "kind": "capture",
        "slot": slot,
        "file": f"../captures/{slot}.mp4",
        "src_in": 0.0,
        "crop": None,
        "fit": "auto",
        "redact": [],
        "callout": callout,
        "evidence": evidence,
        "notes": notes,
    }
    if privacy:
        d["privacy_check"] = privacy
    d["say"] = say(s, e)
    d["start"] = r(s)
    d["end"] = r(e)
    return d


segments = [
    motion("intro", "intro",
           beats={"muse": rel(W["Muse"], "intro"), "wajo": rel(W["Wajo"], "intro")},
           notes="Section 1: speech 1.200 to 8.123, then the 3 s pause. Title, then the Muse, NANDA Index and Wajo diagram. Beats (seconds from segment start) land the Muse and Wajo cards on the spoken names."),
    motion("roles", "roles",
           beats={"agent_box": rel(cue[4]["start"], "roles"), "address": rel(W["address"], "roles"),
                  "hop": rel(W["delivers"], "roles"), "own_app": rel(cue[5]["start"], "roles")},
           notes="Section 2 speech. Straight cut from intro (continuation). Beats are seconds from segment start: Agent Box and own app on caption starts, address and hop on the words address and delivers."),
    step(1),
    capture("cap01", "cap01_guide_copy",
            "Real recording of the demo guide in the browser with the native cursor. Copy is clicked on the setup prompt and the copied state is visible.",
            ["setup"]),
    capture("cap02", "cap02_muse_setup",
            "Real walkthrough of the existing Muse chat (setup already happened earlier): scroll to the setup prompt that was pasted with an email alias, and the agent's confirmation that it started setup. No new submission. Blur a personal email address if one is readable.",
            ["setup"], privacy="pending"),
    capture("cap03", "cap03_wajo_setup",
            "Real walkthrough of the existing Wajo chat: the setup prompt pasted earlier with a different email alias, and the SKILL.md steps the agent followed. No new submission. Blur a personal email address if one is readable.",
            ["setup"], privacy="pending"),
    step(2),
    capture("cap04", "cap04_code_entry",
            "Real walkthrough of the existing chat history where the six-digit code was pasted back into the chat that asked for it, and the agent confirmed. No replayed codes. Redact every readable code with redact boxes.",
            ["setup", "verification"], privacy="pending"),
    capture("cap05", "cap05_muse_connect",
            "Real walkthrough of the existing Muse connection: the Connect button, the Continue step, the secure API key field and Add, as already completed. No replayed credentials. The credential must never be readable; redact any part of it that shows.",
            ["setup", "connection"], privacy="pending"),
    step(3),
    capture("cap06", "cap06_indexed_address",
            "Both agents report that they are indexed. The Muse agent's public Agent Box address is visible and gets copied. Show the agent address, not a personal email.",
            ["indexed", "agent_box_address"]),
    capture("cap07", "cap07_index_search",
            "The index website search showing both demo agents in the results. Hold still during the pause so the listing can be read.",
            ["discovery_listing"]),
    capture("cap08", "cap08_wajo_hello",
            "In Wajo, the request to find the Muse agent and say hello, then the lookup through the index and the message sent through Agent Box.",
            ["discovery_lookup", "greeting_sent"]),
    step(4),
    capture("cap09", "cap09_muse_check_reply",
            "In Muse, the request to check its Agent Box, the greeting from Wajo visible and readable, then the request to reply hello back and the reply sent.",
            ["greeting_received", "reply_sent"],
            callout={"text": "Wajo → Muse", "at": r(cue[31]["start"]), "dur": 4.0}),
    step(5),
    capture("cap10", "cap10_wajo_reply",
            "In Wajo, the request to check for replies, and the reply from Muse visible and readable. Hold through the pause.",
            ["reply_received"],
            callout={"text": "Muse → Wajo", "at": r(cue[34]["start"]), "dur": 4.5}),
    motion("closing", "closing",
           beats={"agent_box": rel(cue[39]["start"], "closing")},
           notes="Section 10 plus pause. Discovery lane (NANDA Index) versus delivery lane (Agent Box). The agent_box beat sits on the caption start of Agent Box handles delivery; the other beats keep the scene defaults."),
    motion("endcard", "endcard",
           beats={"prompt1": rel(W["Set"], "endcard"), "prompt2": rel(W["find"], "endcard"),
                  "prompt3": rel(W["send"], "endcard")},
           notes="Section 11 plus the 2 s end. Try it yourself, my.nandaindex.org/demo, three prompts, each landing on its spoken words."),
]

wav = AUDIO / "narration-final.wav"
md5 = hashlib.md5(wav.read_bytes()).hexdigest()

edl = {
    "version": 1,
    "title": "Muse and Wajo demo",
    "paths_relative_to": "claude/ (the folder that holds CONTRACT.md)",
    "outputs": {"test": "out/test/muse-wajo-test.mp4", "final": "out/final/muse-wajo-demo.mp4"},
    "format": {
        "width": 1920, "height": 1080, "fps": 30, "pix_fmt": "yuv420p", "color": "bt709 tv",
        "frame_rounding": "frame = floor(seconds * 30 + 0.5)",
        "max_duration": 180.0,
        "intermediate": {"codec": "libx264", "preset": "medium", "crf": 14},
        "test": {"codec": "libx264", "preset": "medium", "crf": 18},
        "final": {"codec": "libx264", "preset": "slow", "crf": 18},
        "audio": {"codec": "aac", "sample_rate": 48000, "channels": 2, "bitrate": "256k",
                  "note": "mono narration copied to both channels at unity gain, no other processing"},
    },
    "transitions": {
        "default": {"type": "crossfade", "duration": 0.5, "align": "center"},
        "boundaries": [{"after": "intro", "type": "cut", "why": "roles continues the intro, no dissolve"}],
    },
    "narration": {"file": "../audio/narration-final.wav", "mode": "track", "md5": md5,
                  "duration": round(tl["duration"], 6)},
    "captions": {"srt": "../audio/captions.srt", "embed": "mov_text", "language": "eng", "sidecars": ["srt", "vtt"]},
    "evidence_required": ["setup", "discovery_listing", "greeting_sent", "greeting_received", "reply_sent", "reply_received"],
    "segments": segments,
}

out = ROOT / "edit" / "edl.json"
out.write_text(json.dumps(edl, indent=2, ensure_ascii=False) + "\n")
print(out)
for s in segments:
    print(f"{s['id']:8s} {s['start']:8.3f} {s['end']:8.3f} {s['end'] - s['start']:7.3f}  {s.get('say', '')[:70]}")
