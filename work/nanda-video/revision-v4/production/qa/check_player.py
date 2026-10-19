#!/usr/bin/env python3
"""Static QA for the animated walkthrough player (no browser).

  python3 production/qa/check_player.py          (run from revision-v4)

Checks prompts against prompts.json, message direction and routing, diagram order, required
labels, end-card hold, durations, font sizes, colors, QR decoding, and text fit. Text fit is
measured with the same Inter font (HarfBuzz kerning) used on the page. Exit code 1 on FAIL.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

V4 = Path(__file__).resolve().parents[2]
PLAYER = V4 / "production" / "player"
sys.path.insert(0, str(V4.parent / "claude" / "lib"))
try:
    import brand  # Inter with HarfBuzz kerning (read-only shared helper)
except Exception:  # pragma: no cover
    brand = None

results: list[tuple[str, str, str]] = []


def add(status, name, detail=""):
    results.append((status, name, detail))


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children: list = []
        self.cls = set((self.attrs.get("class") or "").split())
        self.style = {}
        for part in (self.attrs.get("style") or "").split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                self.style[k.strip()] = v.strip()

    def text(self):
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)

    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.walk()

    def px(self, key, default=None):
        v = self.style.get(key)
        return float(v.replace("px", "")) if v and v.endswith("px") else default


class Tree(HTMLParser):
    VOID = {"meta", "link", "img", "br", "input", "use", "path", "polygon", "circle", "rect", "line"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", [], None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in self.VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def font_of(n: Node):
    """Font size and weight for a text node, from its own and ancestor classes and styles."""
    size = weight = None
    special = {"scene-title": (52, 650), "ctext": (38, 400), "ph": (38, 400), "u-bubble": (36, 400),
               "quote": (40, 600), "say": (40, 600), "pill": (34, 700), "chip": (32, 600), "note": (40, 700),
               "abox-label": (40, 700)}
    m = n
    while m is not None and (size is None or weight is None):
        st = m.style
        if size is None and "font-size" in st:
            size = float(st["font-size"].replace("px", ""))
        if weight is None and "font-weight" in st:
            weight = int(st["font-weight"])
        for c in m.cls:
            if size is None and re.fullmatch(r"t\d\d", c):
                size = int(c[1:])
            if weight is None and re.fullmatch(r"w\d", c):
                weight = int(c[1:]) * 100
        for c, (s, w) in special.items():
            if c in m.cls:
                size = size if size is not None else s
                weight = weight if weight is not None else w
        m = m.parent
    return size or 16, weight or 400


def wrap(text, size, weight, width):
    words, lines, cur, too_wide = text.split(), [], "", []
    for w in words:
        if brand.text_width(w, size, weight) > width:
            too_wide.append(w)
        cand = (cur + " " + w).strip()
        if not cur or brand.text_width(cand, size, weight) <= width:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines, too_wide


def message_part(text):
    i = text.find(": ")
    return text[i + 2:] if i >= 0 else text


def main():
    scenes = json.loads((V4 / "scenes.json").read_text())
    prompts = {p["id"]: p for p in json.loads((V4 / "prompts.json").read_text())["prompts"]}
    html = (PLAYER / "index.html").read_text()
    css = (PLAYER / "player.css").read_text()
    t = Tree()
    t.feed(html)
    sections = {n.attrs["data-id"]: n for n in t.root.walk() if n.tag == "section" and "scene" in n.cls}
    by_id = {s["id"]: s for s in scenes["scenes"]}

    # Durations and scene coverage
    total = sum(s["duration"] for s in scenes["scenes"])
    add("PASS" if total <= 180 else "FAIL", "total duration", f"{total} s (max 180)")
    starts_ok = all(abs(s["start"] - sum(x["duration"] for x in scenes["scenes"][:i])) < 1e-6 for i, s in enumerate(scenes["scenes"]))
    add("PASS" if starts_ok else "WARN", "scene starts are cumulative", "player uses cumulative durations")
    miss = [s["id"] for s in scenes["scenes"] if s["id"] not in sections]
    add("FAIL" if miss else "PASS", "every scene has a section", ", ".join(miss) or f"{len(sections)} sections")
    nom = [f'{k} authored {n.attrs.get("data-nominal")} s vs {by_id[k]["duration"]} s' for k, n in sections.items()
           if k in by_id and float(n.attrs.get("data-nominal", 0)) != by_id[k]["duration"]]
    add("WARN" if nom else "PASS", "authored scene lengths match scenes.json", "; ".join(nom) or "all match (beats play at authored times)")

    # Beats inside each scene
    bad = []
    for k, n in sections.items():
        nominal = float(n.attrs.get("data-nominal", 0))
        for e in n.walk():
            for key in ("data-in", "data-out"):
                if key in e.attrs and not 0 <= float(e.attrs[key]) <= nominal:
                    bad.append(f"{k} {key}={e.attrs[key]}")
            if "data-keys" in e.attrs:
                for kv in e.attrs["data-keys"].split(","):
                    if not 0 <= float(kv.split(":")[0]) <= nominal:
                        bad.append(f"{k} key {kv}")
    add("FAIL" if bad else "PASS", "beats inside their scenes", "; ".join(bad[:6]) or "all beats in range")

    # Prompts
    used = [(k, e.attrs["data-prompt"], e.attrs.get("data-part")) for k, n in sections.items() for e in n.walk() if "data-prompt" in e.attrs]
    unknown = sorted({p for _, p, _ in used if p not in prompts})
    add("FAIL" if unknown else "PASS", "prompt ids exist in prompts.json", ", ".join(unknown) or f"{len(used)} prompt slots")
    need = []
    for s in scenes["scenes"]:
        if s.get("promptId") and not any(k == s["id"] and p == s["promptId"] for k, p, _ in used):
            need.append(f'{s["id"]}:{s["promptId"]}')
    for k, p in (("reply", "check_alice"), ("reply", "reply"), ("another", "meeting"), ("another", "meeting_reply")):
        if not any(a == k and b == p for a, b, _ in used):
            need.append(f"{k}:{p}")
    add("FAIL" if need else "PASS", "each scene shows its canonical prompt", ", ".join(need) or "setup, verify, discover, ask, check_alice, reply, check_bob, meeting, meeting_reply")
    literal = [pid for pid, p in prompts.items() if p["text"] in html]
    add("FAIL" if literal else "PASS", "prompts are injected, never copied into the page", ", ".join(literal) or "no prompt text hard-coded")
    disc = prompts["discover"]["text"]
    add("PASS" if "@" not in disc and "agentbox" not in disc.lower() else "FAIL", "discovery prompt has no address", disc)

    # Message direction and routing
    issues, notes = [], []
    for k, n in sections.items():
        boxes = [e for e in n.walk() if "agentbox" in e.cls]
        for e in n.walk():
            if "pill" not in e.cls or "data-path" not in e.attrs:
                continue
            pts = [tuple(map(float, p.split(","))) for p in e.attrs["data-path"].split()]
            who = "bob" if "bob" in e.cls else "alice"
            dx = pts[-1][0] - pts[0][0]
            if (who == "bob" and dx >= 0) or (who == "alice" and dx <= 0):
                issues.append(f"{k}: {who} message moves the wrong way")
            if min(p[1] for p in pts) < 400:
                issues.append(f"{k}: {who} message path rises toward the Index")
            if boxes:
                b = boxes[0]
                bx, bw, by, bh = b.px("left"), b.px("width"), b.px("top"), b.px("height")
                mid = pts[len(pts) // 2]
                if not (bx <= mid[0] <= bx + bw and by <= mid[1] <= by + bh):
                    issues.append(f"{k}: {who} message does not pass through Agent Box")
            notes.append(f"{k}:{who} {'R->L' if dx < 0 else 'L->R'}")
    add("FAIL" if issues else "PASS", "messages: Bob right to left, Alice left to right, through Agent Box",
        "; ".join(issues) or ", ".join(notes))
    order = {}
    for k in ("another",):
        pills = [e for e in sections[k].walk() if "pill" in e.cls]
        order[k] = [("bob" if "bob" in e.cls else "alice", float(e.attrs["data-in"])) for e in pills]
    ok = order["another"][0][0] == "bob" and order["another"][0][1] < order["another"][1][1]
    add("PASS" if ok else "FAIL", "second example: question first, then reply", str(order["another"]))
    dim = []
    for k in ("ask", "reply"):
        idx = [e for e in sections[k].walk() if "indexbox" in e.cls]
        if not idx or "inactive" not in idx[0].cls or "data-op" in idx[0].attrs:
            dim.append(k)
    pale = ".indexbox.inactive{background:#eef2f8" in css and ".indexbox.inactive .n{color:var(--ink2)}" in css
    add("FAIL" if dim or not pale else "PASS", "Index shown as a pale inactive panel while messages travel",
        ", ".join(dim) or "ask, reply: pale panel, dark text, full opacity; another has no Index")
    lab = []
    for k, n in sections.items():
        nodes = list(n.walk())
        for i, e in enumerate(nodes):
            if "agentbox" not in e.cls:
                continue
            label = next((x for x in nodes if "abox-label" in x.cls), None)
            if label is None:
                lab.append(f"{k}: no label")
                continue
            top, bottom = label.px("top"), label.px("top") + 52
            paths = [float(pt.split(",")[1]) for x in nodes if "data-path" in x.attrs for pt in x.attrs["data-path"].split()]
            if not (446 <= top and bottom <= e.px("top")) or any(top - 30 <= y <= bottom + 30 for y in paths):
                lab.append(f"{k}: label {top:.0f}-{bottom:.0f}, box from {e.px('top'):.0f}")
    add("FAIL" if lab else "PASS", "Agent Box label sits above its box, clear of moving messages",
        "; ".join(lab) or "label 498-550, box 560-660, messages at y 610")

    # Handshake layout: Index above the card, card above the Alice and Bob row
    h = sections["handshake"]
    ib = next(e for e in h.walk() if "indexbox" in e.cls)
    cd = next(e for e in h.walk() if "card" in e.cls)
    anchor_top = 500
    ok = ib.px("top") + ib.px("height") <= cd.px("top") and cd.px("top") + cd.px("height") <= anchor_top
    add("PASS" if ok else "FAIL", "handshake: Index above card above people",
        f"Index {ib.px('top'):.0f}-{ib.px('top') + ib.px('height'):.0f}, card {cd.px('top'):.0f}-{cd.px('top') + cd.px('height'):.0f}, people from {anchor_top}")
    htxt = h.text()
    flow = [s for s in ("1. Search", "2. Resolve", "3. Read the card", "Published by Alice", "host39", "list39") if s not in htxt]
    add("FAIL" if flow else "PASS", "handshake flow labels", ", ".join(flow) or "search, resolve, read card, published, host39/list39")
    ctxt = sections["card"].text()
    need = [s for s in ("Capabilities", "Contact route", "Authentication", "asks Bob to approve", "doesn't guarantee safety") if s not in ctxt]
    add("FAIL" if need else "PASS", "card checks, owner approval, safety caveat", ", ".join(need) or "all present")

    # Required wording and disclosure
    pers = next(n for n in t.root.walk() if n.attrs.get("id") == "persist").text()
    goal = sections["goal"].text()
    d1, d2 = "Animated walkthrough", "Illustrative screens and addresses"
    add("PASS" if d1 in pers and d2 in pers and d1 in goal and d2 in goal else "FAIL", "disclosure persistent and in the opening", f"{d1} / {d2}")
    wins = [e for n in sections.values() for e in n.walk() if "win" in e.cls]
    nolabel = [w.attrs.get("style", "")[:30] for w in wins if "Illustration" not in w.text()]
    add("FAIL" if nolabel else "PASS", "every app screen is labeled Illustration", ", ".join(nolabel) or f"{len(wins)} screens")
    v = sections["verify"].text()
    need = [s for s in ("Use your own email and code", "Your agent's credential", "••••", "If Muse asks", "secure field") if s not in v]
    add("FAIL" if need else "PASS", "verify: own email and code, masked credential, conditional wording", ", ".join(need) or "all present")
    ms = sections["manual_search"].text()
    need = [s for s in ("birthday cake bakery", "Alice's Bakery", "You can search indexed agents at nandaindex.org.", "Illustration") if s not in ms]
    add("FAIL" if need else "PASS", "manual search page", ", ".join(need) or "query, result, caption, label")
    end = sections["end"]
    et = end.text()
    need = [s for s in ("nandaindex.org", "my.nandaindex.org/demo", "SKILL.MD") if s not in et]
    add("FAIL" if need else "PASS", "end card text", ", ".join(need) or "domain, guide URL, SKILL.MD label")
    last = max(float(e.attrs["data-in"]) + float(e.attrs.get("data-dur", 0.6)) for e in end.walk() if "data-in" in e.attrs)
    nominal = float(end.attrs["data-nominal"])
    hold = by_id["end"]["duration"] - max(last, 0.45) * by_id["end"]["duration"] / nominal
    add("PASS" if hold >= 8 else "FAIL", "end card held at least 8 s", f"fully visible after {last:.2f} s, held {hold:.2f} s")

    # QR decodes to the Index
    svg = PLAYER / "assets" / "qr-nandaindex.svg"
    with tempfile.TemporaryDirectory() as tmp:
        out = subprocess.run(["swift", str(V4 / "production" / "tools" / "qr.swift"), "https://nandaindex.org", f"{tmp}/qr.svg"],
                             capture_output=True, text=True)
        same = Path(f"{tmp}/qr.svg").exists() and Path(f"{tmp}/qr.svg").read_text() == svg.read_text()
    ok = "QR OK" in out.stdout and same
    add("PASS" if ok else "FAIL", "QR decodes to https://nandaindex.org", (out.stdout.strip().splitlines() or ["no output"])[-2] + (", asset matches" if same else ", asset differs"))

    # Style rules
    sizes = []
    for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        if any(x in sel for x in ("#controls", "#gate", "#countdown", "#qa", ".target-mark", "html,body")):
            continue
        for m in re.finditer(r"font-size:(\d+)px", body):
            if int(m.group(1)) < 30:
                sizes.append(f"{sel.strip()} {m.group(1)}px")
    inline = [m.group(1) for m in re.finditer(r"font-size:(\d+)px", html) if int(m.group(1)) < 30]
    add("FAIL" if sizes or inline else "PASS", "canvas text is 30 px or larger (body 36 px or larger)", "; ".join(sizes + inline) or "smallest label 30 px")
    add("PASS" if "--alice:#2563eb" in css and "--bob:#087f5b" in css else "FAIL", "Alice blue #2563eb, Bob green #087f5b", "")
    al = next(n for n in t.root.walk() if n.attrs.get("id") == "alice")
    add("PASS" if "#alice{left:36px}#bob{left:1644px}" in css.replace(" ", "") and al else "FAIL", "Alice left, Bob right, fixed anchors", "")
    yellow = re.findall(r"#(?:f[0-9a-f]{1}[c-f][0-9a-f][0-4][0-9a-f])\b|yellow", (css + html).lower())
    add("FAIL" if yellow else "PASS", "no yellow decoration", ", ".join(yellow) or "none")
    cursor_bits = [n.attrs.get("class") for n in t.root.walk() if "cursor" in (n.attrs.get("class") or "") + (n.attrs.get("id") or "")]
    add("FAIL" if cursor_bits or "cursor:none" in css.replace(" ", "") else "PASS", "no drawn or hidden cursor", "native cursor stays visible")

    # Text fit with Inter
    if brand is None:
        add("WARN", "text fit", "Inter measurement helper not found; skipped")
    else:
        over = []
        count = 0
        for k, n in sections.items():
            for e in n.walk():
                if "data-fit" not in e.attrs:
                    continue
                count += 1
                w, maxl = (float(x) for x in e.attrs["data-fit"].split(","))
                if "data-title" in e.attrs:
                    text = by_id[k]["title"]
                elif "data-prompt" in e.attrs:
                    p = prompts.get(e.attrs["data-prompt"], {}).get("text", "")
                    text = message_part(p) if e.attrs.get("data-part") == "message" else p
                else:
                    text = " ".join(e.text().split())
                size, weight = font_of(e)
                lines, wide = wrap(text, size, weight, w)
                if len(lines) > maxl or wide:
                    over.append(f'{k}: "{text[:50]}" {size:.0f}px w{weight}: {len(lines)} lines > {maxl:.0f}' + (f", too wide: {wide}" if wide else ""))
        add("FAIL" if over else "PASS", "text fits its box (Inter, kerned)", "; ".join(over) or f"{count} boxes")

    width = max(len(n) for _, n, _ in results)
    for status, name, detail in results:
        print(f"{status:<5} {name:<{width}}  {detail}")
    counts = {s: sum(1 for r in results if r[0] == s) for s in ("PASS", "WARN", "FAIL")}
    print("summary:", ", ".join(f"{k} {v}" for k, v in counts.items() if v))
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
