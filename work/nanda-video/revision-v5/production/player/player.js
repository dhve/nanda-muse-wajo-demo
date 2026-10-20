/* Animated bakery walkthrough player.
 *
 * Content: ../../scenes.json (scene order, titles, durations) and ../../prompts.json (exact
 * prompts), loaded at run time so the player never carries its own copy of a prompt.
 * Every element is drawn as a pure function of time, so pause, seek and retiming are exact.
 *
 * Query options (combine freely):
 *   record=1        recording mode: canvas fills the window, visible Start button, 3-2-1
 *                   countdown, then plays with controls hidden (Esc shows them)
 *   audio=1         play ../../narration.wav on the same clock (or audio=path/to/file.wav)
 *   timing=path     per-scene durations: {"scenes":[{"id","duration"}]} or {"goal":16,...}
 *   t=SECONDS       start position; scene=ID starts at that scene
 *   frame=SECONDS   still frame with controls hidden (for keyframe capture)
 *   countdown=N     countdown length in recording mode (default 3)
 *   qa=1            report text that overflows its box (development only)
 *   targets=1       show cursor target markers for rehearsal (never in recording mode)
 */
(() => {
  'use strict';
  const W = 1920, H = 1080, DISSOLVE = 0.9, ENTRY_FRAME = 0.65;
  const qs = new URLSearchParams(location.search);
  const RECORD = qs.has('record');
  const FRAME = qs.has('frame') ? Number(qs.get('frame')) : null;
  const QA = qs.has('qa');
  const TARGETS = qs.has('targets') && !RECORD && FRAME == null;
  const BASE = qs.get('base') || '../../';
  const COUNT = qs.has('countdown') ? Math.max(0, Number(qs.get('countdown'))) : 3;

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const ease = p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const prog = (t, a, d) => (d > 0 ? clamp((t - a) / d, 0, 1) : t >= a ? 1 : 0);
  const lerp = (p, q, f) => [p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f];
  const fmt = s => { s = Math.max(0, s); const m = Math.floor(s / 60); return m + ':' + (s % 60).toFixed(1).padStart(4, '0'); };

  const stage = $('#stage'), viewport = $('#viewport'), persist = $('#persist');
  const ui = { play: $('#play'), restart: $('#restart'), sel: $('#sceneSel'), time: $('#time'), info: $('#info'), audio: $('#audioToggle') };
  let scenes = [], prompts = {}, total = 0, scale = 1, current = -1, focusMode = '';
  let audio = null, ended = false;
  const clock = { playing: false, t0: 0, wall0: 0 };
  const marks = [];

  if (RECORD || FRAME != null) document.body.classList.add('record');

  async function getJSON(url) {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(`${url} returned ${r.status}`);
    return r.json();
  }

  // Message text inside a prompt, e.g. "Ask Alice's Bakery: What cakes do you have?" -> "What cakes do you have?"
  function messagePart(text) { const i = text.indexOf(': '); return i >= 0 ? text.slice(i + 2) : text; }
  const parseKeys = s => s.split(',').map(p => p.split(':').map(Number));
  function keyed(keys, t) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [t1, v1] = keys[i], [t0, v0] = keys[i - 1];
      if (t <= t1) return v0 + (v1 - v0) * ease(prog(t, t0, t1 - t0));
    }
    return keys[keys.length - 1][1];
  }

  function collect(sec) {
    return $$('[data-in],[data-anim]', sec).map(el => {
      const d = el.dataset, type = d.anim || 'rise';
      const a = {
        el, type, tin: Number(d.in || 0),
        dur: d.dur != null ? Number(d.dur) : type === 'draw' ? 1 : type === 'move' ? 2 : 0.6,
        tout: d.out != null ? Number(d.out) : null, odur: d.odur != null ? Number(d.odur) : 0.35,
        op: d.op != null ? Number(d.op) : 1,
      };
      if (type === 'zoom' || type === 'height') a.keys = parseKeys(d.keys);
      if (type === 'move') { a.pts = d.path.trim().split(/\s+/).map(p => p.split(',').map(Number)); a.pause = Number(d.pause || 0); }
      if (type === 'hl') {
        a.wins = (d.windows || '').split(',').filter(Boolean).map(w => w.split('-').map(Number));
        a.target = d.hlFor === 'prev' ? el.previousElementSibling : el;
      }
      return a;
    });
  }

  function measure() {
    scenes.forEach(s => s.anims.forEach(a => {
      if (a.type === 'draw') { a.len = a.el.getTotalLength(); a.el.style.strokeDasharray = String(a.len); }
      if (a.type === 'move') { a.w = a.el.offsetWidth; a.h = a.el.offsetHeight; }
    }));
  }

  function along(a, t) {
    const p = a.pts;
    if (p.length === 3 && a.pause > 0) {
      const leg = (a.dur - a.pause) / 2;
      if (t < a.tin + leg) return lerp(p[0], p[1], ease(prog(t, a.tin, leg)));
      if (t < a.tin + leg + a.pause) return p[1];
      return lerp(p[1], p[2], ease(prog(t, a.tin + leg + a.pause, leg)));
    }
    const segs = [];
    let len = 0;
    for (let i = 1; i < p.length; i++) { const l = Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); segs.push(l); len += l; }
    let d = ease(prog(t, a.tin, a.dur)) * len;
    for (let i = 0; i < segs.length; i++) {
      if (d <= segs[i] || i === segs.length - 1) return lerp(p[i], p[i + 1], segs[i] ? Math.min(1, d / segs[i]) : 1);
      d -= segs[i];
    }
    return p[p.length - 1];
  }

  function apply(a, t) {
    const s = a.el.style;
    const pin = ease(prog(t, a.tin, a.dur));
    const pout = a.tout != null ? ease(prog(t, a.tout, a.odur)) : 0;
    switch (a.type) {
      case 'zoom': s.transform = `scale(${keyed(a.keys, t)})`; return;
      case 'height': s.height = keyed(a.keys, t) + 'px'; return;
      case 'hl': a.target && a.target.classList.toggle('on', a.wins.some(([x, y]) => t >= x && t < y)); return;
      case 'draw':
        s.strokeDashoffset = String(a.len * (1 - pin));
        s.opacity = String((t >= a.tin ? 1 : 0) * (1 - pout) * a.op);
        return;
      case 'move': {
        s.opacity = String(ease(prog(t, a.tin, 0.25)) * (1 - pout) * a.op);
        const [x, y] = along(a, t);
        s.transform = `translate(${(x - a.w / 2).toFixed(2)}px, ${(y - a.h / 2).toFixed(2)}px)`;
        return;
      }
      case 'fade': s.opacity = String(pin * (1 - pout) * a.op); return;
      case 'dissolve': {
        const p = prog(t, a.tin, a.dur);
        s.opacity = String(p * p * (3 - 2 * p) * (1 - pout) * a.op);
        return;
      }
      case 'pop': s.opacity = String(pin * (1 - pout) * a.op); s.transform = `scale(${0.8 + 0.2 * pin})`; return;
      default:
        s.opacity = String(pin * (1 - pout) * a.op);
        s.transform = pin < 1 ? `translateY(${((1 - pin) * 22).toFixed(2)}px)` : '';
    }
  }

  function setFocus(mode) {
    if (mode === focusMode) return;
    focusMode = mode;
    const al = $('#alice'), bo = $('#bob');
    al.classList.toggle('focus', mode === 'alice');
    bo.classList.toggle('focus', mode === 'bob');
    al.classList.toggle('compact', mode === 'bob' || mode === 'none');
    bo.classList.toggle('compact', mode === 'alice' || mode === 'none');
  }

  function render(t) {
    t = clamp(t, 0, total);
    let i = scenes.findIndex(s => t < s.start + s.dur);
    if (i < 0) i = scenes.length - 1;
    const incoming = scenes.findIndex((s, k) => k > 0 && t >= s.start - DISSOLVE / 2 && t < s.start + DISSOLVE / 2);
    const outgoing = incoming - 1;
    const p = incoming > 0 ? prog(t, scenes[incoming].start - DISSOLVE / 2, DISSOLVE) : 0;
    const mix = p * p * (3 - 2 * p);
    persist.style.opacity = String(ease(prog(t, 0, 0.6)));
    scenes.forEach((s, k) => {
      const show = incoming > 0 ? k === outgoing || k === incoming : k === i;
      s.el.style.visibility = show ? 'visible' : 'hidden';
      if (!show) return;
      // Keep the previous scene solid beneath the incoming scene. Each scene has
      // its own canvas background, so the dissolve cannot flash to empty space.
      s.el.style.opacity = String(incoming > 0 ? k === incoming ? mix : 1 : k === 0 ? ease(prog(t, 0, 0.6)) : 1);
      const lt = Math.max(k > 0 ? ENTRY_FRAME : 0, clamp(t - s.start, 0, s.dur));
      const nt = (lt * s.nominal) / s.dur; // authored time inside the scene
      s.anims.forEach(a => apply(a, nt));
      // Change headings in sequence instead of superimposing two lines of text.
      const title = $('[data-title]', s.el);
      if (title) title.style.opacity = String(incoming > 0 ? k === outgoing ? 1 - ease(prog(p, 0, 0.45)) : ease(prog(p, 0.55, 0.45)) : 1);
    });
    // Focus follows the logical scene once, even while two scenes are visible.
    const active = scenes[i], nt = clamp(t - active.start, 0, active.dur) * active.nominal / active.dur;
    let mode = 'both';
    for (const [ft, m] of active.focus) if (nt >= ft) mode = m;
    setFocus(mode);
    if (TARGETS) placeMarks(active, nt);
    if (i !== current) { current = i; ui.sel.value = String(i); }
    ui.time.textContent = `${fmt(t)} / ${fmt(total)}`;
  }

  // Clock: the narration audio is the master clock while it plays.
  function now() {
    if (audio && clock.playing && !audio.paused) return audio.currentTime;
    return clock.playing ? clock.t0 + (performance.now() - clock.wall0) / 1000 : clock.t0;
  }
  function seek(t) {
    clock.t0 = clamp(t, 0, total); clock.wall0 = performance.now();
    if (audio) { try { audio.currentTime = clock.t0; } catch (_) { /* not loaded yet */ } }
    render(clock.t0);
  }
  function play() {
    if (clock.t0 >= total - 0.01) seek(0);
    ended = false;
    clock.playing = true; clock.wall0 = performance.now();
    if (audio) { audio.currentTime = clock.t0; audio.play().catch(err => note('Narration could not play: ' + err.message)); }
    ui.play.textContent = 'Pause';
  }
  function pause() {
    clock.t0 = now(); clock.playing = false;
    if (audio) audio.pause();
    ui.play.textContent = clock.t0 > 0 && clock.t0 < total ? 'Resume' : 'Start';
  }
  function tick() {
    if (clock.playing) {
      const t = now();
      if (t >= total) { clock.t0 = total; clock.playing = false; ended = true; if (audio) audio.pause(); ui.play.textContent = 'Start'; render(total); }
      else render(t);
    }
    requestAnimationFrame(tick);
  }

  function fit() {
    const vw = viewport.clientWidth, vh = viewport.clientHeight;
    scale = Math.min(vw / W, vh / H);
    stage.style.transform = `translate(${((vw - W * scale) / 2).toFixed(2)}px, ${((vh - H * scale) / 2).toFixed(2)}px) scale(${scale})`;
  }

  function note(msg) { ui.info.textContent = msg; console.info('[player]', msg); }

  function loadAudio(src) {
    audio = new Audio(src);
    audio.preload = 'auto';
    audio.addEventListener('loadedmetadata', () => {
      const diff = Math.abs(audio.duration - total);
      note(diff > 0.5 ? `Narration is ${audio.duration.toFixed(2)} s; visuals are ${total.toFixed(2)} s` : `Narration loaded (${audio.duration.toFixed(2)} s)`);
    });
    audio.addEventListener('error', () => note('Narration not found: ' + src));
  }

  // Rehearsal markers: where the native cursor should point, from data-target attributes.
  function buildMarks() {
    scenes.forEach(s => $$('[data-target]', s.el).forEach(el => {
      const [a, b] = (el.dataset.targetAt || '0-999').split('-').map(Number);
      const m = document.createElement('div');
      m.className = 'target-mark';
      m.innerHTML = '<span></span>';
      m.querySelector('span').textContent = el.dataset.target;
      m.style.display = 'none';
      $('#marks').appendChild(m);
      marks.push({ scene: s, el, a, b, m });
    }));
  }
  function placeMarks(s, nt) {
    const sr = stage.getBoundingClientRect();
    marks.forEach(k => {
      const on = k.scene === s && nt >= k.a && nt <= k.b;
      k.m.style.display = on ? 'block' : 'none';
      if (!on) return;
      const r = k.el.getBoundingClientRect();
      k.m.style.left = ((r.left + r.width / 2 - sr.left) / scale).toFixed(0) + 'px';
      k.m.style.top = ((r.top + r.height / 2 - sr.top) / scale).toFixed(0) + 'px';
    });
  }
  function listTargets() {
    const sr = stage.getBoundingClientRect(), rows = [];
    marks.forEach(k => {
      const saved = clock.t0;
      render(k.scene.start + ((k.a + k.b) / 2) * (k.scene.dur / k.scene.nominal));
      const r = k.el.getBoundingClientRect();
      rows.push({ scene: k.scene.id, target: k.el.dataset.target, from: k.a, to: k.b,
        x: Math.round((r.left + r.width / 2 - sr.left) / scale), y: Math.round((r.top + r.height / 2 - sr.top) / scale) });
      render(saved);
    });
    console.table(rows);
    return rows;
  }

  // Development check: text that does not fit its box.
  function qaFit() {
    const issues = [];
    scenes.forEach(s => {
      s.el.style.visibility = 'visible';
      $$('[data-fit]', s.el).forEach(el => {
        const [w, lines] = el.dataset.fit.split(',').map(Number);
        const lh = parseFloat(getComputedStyle(el).lineHeight) || 1;
        const n = Math.round(el.offsetHeight / lh);
        const wide = el.scrollWidth > el.clientWidth + 1;
        if (n > lines || wide) issues.push(`${s.id}: "${el.textContent.trim().slice(0, 60)}" uses ${n} line(s), max ${lines}${wide ? ', wider than its box' : ''}`);
      });
    });
    render(clock.t0);
    const box = $('#qa');
    box.style.display = 'block';
    box.textContent = issues.length ? 'Text fit issues:\n' + issues.join('\n') : 'Text fit: all boxes OK';
    return issues;
  }

  function startRecording() {
    $('#gate').style.display = 'none';
    const cd = $('#countdown'), n = $('.n', cd);
    let k = COUNT;
    const step = () => {
      if (k <= 0) { cd.style.display = 'none'; play(); return; }
      cd.style.display = 'flex'; n.textContent = String(k); k -= 1; setTimeout(step, 1000);
    };
    step();
  }

  async function init() {
    let sceneData, promptData;
    try {
      [sceneData, promptData] = await Promise.all([getJSON(BASE + 'scenes.json'), getJSON(BASE + 'prompts.json')]);
    } catch (err) {
      note('Could not load scenes.json and prompts.json. Serve the revision-v5 folder over HTTP, for example: python3 -m http.server 8642, then open http://localhost:8642/production/player/');
      console.error(err);
      return;
    }
    promptData.prompts.forEach(p => { prompts[p.id] = p; });

    let durations = {};
    if (qs.get('timing')) {
      try {
        const tj = await getJSON(qs.get('timing'));
        const list = Array.isArray(tj) ? tj : Array.isArray(tj.scenes) ? tj.scenes : null;
        if (list) list.forEach(x => { durations[x.id] = Number(x.duration); });
        else durations = tj;
      } catch (err) { note('Timing file not loaded: ' + err.message); }
    }

    const sections = $$('section.scene');
    let start = 0;
    scenes = sceneData.scenes.map(sd => {
      const el = sections.find(x => x.dataset.id === sd.id);
      if (!el) throw new Error('No section for scene ' + sd.id);
      const dur = Number(durations[sd.id] || sd.duration);
      const s = { id: sd.id, title: sd.title, start, dur, nominal: Number(el.dataset.nominal || sd.duration), el,
        focus: (el.dataset.focus || '0:both').split(',').map(p => { const [t, m] = p.split(':'); return [Number(t), m]; }) };
      start += dur;
      return s;
    });
    total = start;
    if (total > 180) note(`Warning: total ${total.toFixed(2)} s is over 180 s`);

    const missing = [];
    scenes.forEach(s => {
      $$('[data-title]', s.el).forEach(h => { h.textContent = s.title; });
      $$('[data-prompt]', s.el).forEach(el => {
        const p = prompts[el.dataset.prompt];
        if (!p) { missing.push(el.dataset.prompt); el.textContent = '[missing prompt ' + el.dataset.prompt + ']'; return; }
        el.textContent = el.dataset.part === 'message' ? messagePart(p.text) : p.text;
      });
      s.anims = collect(s.el);
    });
    if (missing.length) note('Missing prompts: ' + missing.join(', '));

    scenes.forEach((s, k) => {
      const o = document.createElement('option');
      o.value = String(k);
      o.textContent = `${fmt(s.start).replace(/\.\d$/, '')}  ${s.title}`;
      ui.sel.appendChild(o);
    });

    await document.fonts.ready;
    measure();
    fit();
    addEventListener('resize', fit);
    if (TARGETS) buildMarks();

    const wantAudio = qs.has('audio') && qs.get('audio') !== '0';
    if (wantAudio) { loadAudio(qs.get('audio') && qs.get('audio') !== '1' ? qs.get('audio') : BASE + 'narration.wav'); ui.audio.checked = true; }
    ui.audio.addEventListener('change', () => {
      if (ui.audio.checked && !audio) loadAudio(BASE + 'narration.wav');
      if (!ui.audio.checked && audio) { audio.pause(); audio = null; }
    });

    let t0 = 0;
    if (qs.has('scene')) { const s = scenes.find(x => x.id === qs.get('scene')); if (s) t0 = s.start; }
    if (qs.has('t')) t0 = Number(qs.get('t')) || 0;
    if (FRAME != null) t0 = FRAME;
    seek(t0);
    if (!missing.length && !ui.info.textContent.startsWith('Warning')) note(`${scenes.length} scenes, ${fmt(total)}. Press Start, or Space.`);

    ui.play.addEventListener('click', () => (clock.playing ? pause() : play()));
    ui.restart.addEventListener('click', () => { seek(0); if (!clock.playing) ui.play.textContent = 'Start'; });
    ui.sel.addEventListener('change', () => seek(scenes[Number(ui.sel.value)].start));
    addEventListener('keydown', e => {
      if (e.key === 'Escape' && RECORD) { document.body.classList.toggle('show-controls'); return; }
      if (e.target.tagName === 'SELECT') return;
      if (e.key === ' ') { e.preventDefault(); clock.playing ? pause() : play(); }
      else if (e.key === 'r' || e.key === 'R') seek(0);
      else if (e.key === 'ArrowRight') seek(scenes[Math.min(scenes.length - 1, current + 1)].start);
      else if (e.key === 'ArrowLeft') seek(scenes[Math.max(0, current - 1)].start);
    });

    if (RECORD) { $('#gate').style.display = 'flex'; $('#gateStart').addEventListener('click', startRecording, { once: true }); }
    if (QA) qaFit();
    window.player = { play, pause, seek, render, listTargets, qaFit, get time() { return now(); }, get total() { return total; }, scenes };
    requestAnimationFrame(tick);
  }

  init().catch(err => { note('Player error: ' + err.message); console.error(err); });
})();
