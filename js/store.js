/* ═══════════════════════════════════════════════════════════
   {{BRAND}} — data layer (US English frame)

   Screens call only this file. data.js is a pipeline artifact and is never
   hand-edited. Study history piles up only in this browser — localStorage
   `te.<subject key>.v1` · settings `te.pref.v1` · theme `te.skin`
   (★ prefix is "te." so it never collides with the sister apps' "tj.",
   "jg.", "mj." prefixes — served from the same github.io, browser storage
   would otherwise mix).

   Carries over the design settled on by the sister apps (Korean, Japanese) —
     · Never make the learner choose. Home shows exactly one thing: "today's work."
     · Workload is stated in **time**, not question count (10/15/20/30 min a day).
     · A verdict is confidence × correctness (judge.js). Confidence is asked before the answer.
     · Spaced review comes before new sentences.
   ═══════════════════════════════════════════════════════════ */
(function () {
  "use strict";
  var T = window.TREE, QB = window.QBANK || {}, PR = window.PAIRS || [];
  if (!T) { console.error("data.js must be loaded first"); return; }

  var KEY = "te." + (T.key || T.subject) + ".v1", PREF = "te.pref.v1", SKIN = "te.skin";

  function read(k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function write(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }

  var S = read(KEY, null) || {};
  S.ans = S.ans || {}; S.days = S.days || {}; S.pairs = S.pairs || {};
  var P = read(PREF, null) || {};
  function save() { S.at = Date.now(); write(KEY, S); }
  function savePref() { write(PREF, P); }

  /* ── dates — a day starts at local midnight ── */
  function ymd(d) {
    d = d || new Date();
    return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
  }
  function dayNo(s) { var d = s ? new Date(s + "T00:00:00") : new Date(); d.setHours(0, 0, 0, 0); return Math.round(d / 86400000); }
  var TODAY = ymd(), TODAYN = dayNo();

  /* ── indexes ── */
  var NODE = {}, CH = {}, PART = {}, ITEM = {};
  T.nodes.forEach(function (n) {
    NODE[n.no] = n;
    n.chkey = n.part + "-" + (n.ch < 10 ? "0" + n.ch : n.ch);
  });
  T.chs.forEach(function (c) { CH[c.key] = c; });
  T.parts.forEach(function (p) { PART[p.no] = p; });
  Object.keys(QB).forEach(function (no) {
    QB[no].forEach(function (q) { q.n = +no; ITEM[q.i] = q; });
  });
  PR.forEach(function (p, i) { p.id = "P" + i; });
  var PR_BY = {};
  PR.forEach(function (p) { (PR_BY[p.n] = PR_BY[p.n] || []).push(p); });

  function qs(no) { return QB[String(no)] || []; }
  function item(id) { return ITEM[id]; }
  function pairs(no) { return no == null ? PR : (PR_BY[no] || []); }
  function pair(id) { return PR[+String(id).slice(1)]; }

  /* ── exam · series · subject ──
     Exam list lives in catalog.js. Learner settings — P.exam (exam id) ·
     P.series (series id) · P.subs (subject id list) · P.cur (current subject). */
  var C = window.CATALOG;
  function exam() { return (C && C.exam(P.exam)) || (C && C.EXAMS[0]) || { id: "", name: "", date: null }; }
  function setExam(id, sid) {
    P.exam = id; P.series = sid || null;
    P.subs = C ? C.subsOf(id, sid) : [];
    if (!P.goalMine) P.goal = exam().date;
    savePref();
  }
  function subs() { return (P.subs && P.subs.length) ? P.subs.slice() : [T.key || "_sample"]; }
  function cur() { return window.TJ_CUR || T.key; }
  function setCur(id) { P.cur = id; savePref(); }
  function seriesName() { var s = C && C.series(P.exam, P.series); return s ? s.name : ""; }
  /* legacy alias — some screens still call track() */
  function track() { var e = exam(); return { id: e.id, name: e.name + (seriesName() ? " " + seriesName() : ""), exam: e.name, date: e.date }; }
  function setTrack(id) { setExam(id, P.series); }
  function goal() { return P.goal || exam().date || TODAY; }
  function goalMark() { return P.goalMine ? "custom" : "default"; }
  function setGoal(d, mine) { P.goal = d || null; P.goalMine = !!mine; savePref(); }
  function dday() { return dayNo(goal()) - TODAYN; }

  function minutes() { return P.minutes || 15; }
  function setMinutes(m) { P.minutes = m; savePref(); delete S.today; save(); }
  function name() { return P.name || ""; }
  function setName(v) { P.name = String(v || "").trim().slice(0, 12); savePref(); }
  function onboarded() { return !!P.onboarded; }
  function setOnboarded() { P.onboarded = ymd(); savePref(); }

  /* ── history · spaced review ──
     Boxes 0-5, next-review gaps [0,1,3,7,14,30] days.
     A confident correct answer moves up one box; a half-sure/guessed
     correct answer stays at box 1; any miss resets to box 0 (seen again today). */
  var GAP = [0, 1, 3, 7, 14, 30];
  function answer(id, ok, x) {
    x = x || {};
    var a = S.ans[id] || { n: 0, box: 0 };
    a.n = (a.n || 0) + 1;
    a.ok = !!ok; a.at = Date.now(); a.conf = x.conf || null; a.ms = x.ms || 0;
    if (ok) a.box = x.conf === "sure" ? Math.min(5, (a.box || 0) + 1) : Math.max(1, Math.min(a.box || 0, 1));
    else a.box = 0;
    a.due = TODAYN + GAP[a.box];
    if (x.kind) a.kind = x.kind;
    S.ans[id] = a;
    var d = S.days[TODAY] || (S.days[TODAY] = { n: 0, ok: 0, ms: 0 });
    d.n++; if (ok) d.ok++; d.ms += Math.min(x.ms || 0, 60000);
    save();
    return a;
  }
  function pairAnswer(pid, ok) {
    S.pairs[pid] = { ok: !!ok, at: Date.now() };
    var d = S.days[TODAY] || (S.days[TODAY] = { n: 0, ok: 0, ms: 0 });
    d.n++; if (ok) d.ok++;
    save();
  }
  function answered(id) { return S.ans[id] || null; }
  function reset() { S = { ans: {}, days: {}, pairs: {} }; save(); }

  /* ── mastery — same formula as the sister apps: 55 for how much you've done + 45 for how well ── */
  function nodeStat(no) {
    var list = qs(no), solved = 0, correct = 0, last = null;
    for (var i = 0; i < list.length; i++) {
      var a = S.ans[list[i].i];
      if (a) { solved++; if (a.ok) correct++; if (!last || a.at > last) last = a.at; }
    }
    var n = list.length;
    var pct = solved ? Math.round(correct / solved * 100) : null;
    var prog = n ? Math.round(solved / n * 100) : 0;
    /* ★ the accuracy weight is damped until 10 sentences are solved — otherwise one correct answer alone reads as 46% mastery */
    var achieve = n ? Math.round(prog * 0.55 + (pct === null ? 0 : pct) * 0.45 * Math.min(1, solved / 10)) : 0;
    return { no: no, n: n, solved: solved, correct: correct, pct: pct, prog: prog, achieve: achieve, lastAt: last,
             mastery: solved ? correct / solved : null,
             state: !n ? "empty" : achieve >= 80 ? "done" : solved ? "wip" : "none" };
  }
  function agg(nos) {
    var n = 0, solved = 0, correct = 0, ach = 0, cnt = 0, last = null, vol = 0;
    nos.forEach(function (no) {
      var st = nodeStat(no), nd = NODE[no];
      n += st.n; solved += st.solved; correct += st.correct; ach += st.achieve; cnt++; vol += (nd ? nd.vol : 0);
      if (st.lastAt && (!last || st.lastAt > last)) last = st.lastAt;
    });
    return { n: n, solved: solved, correct: correct, nodes: cnt, vol: vol,
             pct: solved ? Math.round(correct / solved * 100) : null,
             prog: n ? Math.round(solved / n * 100) : 0, achieve: cnt ? Math.round(ach / cnt) : 0, lastAt: last };
  }
  function chStat(key) { return agg((CH[key] || { nodes: [] }).nodes); }
  function partNodes(no) {
    var acc = [];
    (PART[no] || { chs: [] }).chs.forEach(function (k) { acc = acc.concat(CH[k].nodes); });
    return acc;
  }
  function partStat(no) { return agg(partNodes(no)); }
  function overall() {
    var o = agg(T.nodes.map(function (n) { return n.no; }));
    o.done = T.nodes.filter(function (n) { return nodeStat(n.no).state === "done"; }).length;
    o.started = T.nodes.filter(function (n) { return nodeStat(n.no).solved > 0; }).length;
    o.total = T.nodes.length;
    return o;
  }

  /* ── choosing sentences ──
     For the same topic, surface **this learner's own exam series → most
     recent year → most confidently assigned item** first. */
  function rank(q) {
    var s = 0;
    if (q.e === exam().name) s += 4;
    s += Math.max(0, (q.y || 2015) - 2015) * 0.3;
    if (q.c === "A") s += 1;
    return s;
  }
  function freshOf(no, k) {
    return qs(no).filter(function (q) { return !S.ans[q.i]; })
      .sort(function (a, b) { return rank(b) - rank(a); }).slice(0, k);
  }
  /* today's review — items whose due date has arrived. Misses (box 0) come first */
  function dueList() {
    return Object.keys(S.ans).filter(function (id) {
      var a = S.ans[id]; return ITEM[id] && a.due != null && a.due <= TODAYN && !(a.at && ymd(new Date(a.at)) === TODAY && a.ok);
    }).sort(function (a, b) { return (S.ans[a].box - S.ans[b].box) || (S.ans[a].at - S.ans[b].at); });
  }
  function wrongList() {
    return Object.keys(S.ans).filter(function (id) { return ITEM[id] && !S.ans[id].ok; })
      .sort(function (a, b) { return S.ans[b].at - S.ans[a].at; });
  }

  /* today's focus topics — lots of past questions (q), still not mastered. Weak areas from the placement test get extra weight */
  function focusNodes(k) {
    var weakPart = (S.place && S.place.weakPart) || null;
    return T.nodes.filter(function (n) { return n.q > 0 && freshOf(n.no, 1).length; })
      .map(function (n) {
        var st = nodeStat(n.no), left = 1 - st.prog / 100;
        var w = Math.sqrt(n.q) * (0.35 + left) * (st.mastery != null && st.mastery < 0.6 ? 1.4 : 1)
              * (weakPart && n.part === weakPart ? 1.3 : 1) * (st.solved && st.prog < 100 ? 1.25 : 1);
        return { n: n, w: w };
      })
      .sort(function (a, b) { return b.w - a.w; }).slice(0, k || 3).map(function (x) { return x.n; });
  }

  /* ── today's work ──
     ★ Workload is time. One True/False sentence — confidence + answer +
       reading the verdict — is budgeted at about 20 seconds (an estimate,
       not yet measured; the screen labels it "about"). 15 min ≈ 45 sentences.
     ★ Decided once a day and saved. If it changed on every reload the
       learner could never see an end in sight. */
  var SEC_PER = 20, SEC_MC = 60;
  function today() {
    if (S.today && S.today.date === TODAY && S.today.min === minutes()) return decorate(S.today);
    /* ★ workload is filled by time (seconds) — one True/False sentence is about 20s, a past
       question (source + 4-5 choices) is about 60s (estimate, not yet measured).
       For a subject that is nothing but "solve past questions," assigning 45 items to
       a 15-minute budget would never let the learner reach the end. */
    function secondsFor(id) { var q = ITEM[id]; return q && q.mc ? SEC_MC : SEC_PER; }
    var budget = minutes() * 60, used = 0;
    var due = [];
    dueList().forEach(function (id) { if (used + secondsFor(id) <= budget * 0.5) { due.push(id); used += secondsFor(id); } });
    var foci = focusNodes(3), fresh = [], seen = {};
    function fill(no, cap) {
      freshOf(no, 60).some(function (q) {
        if (used + secondsFor(q.i) > cap || seen[q.i]) return used + SEC_PER > cap;
        fresh.push(q.i); seen[q.i] = 1; used += secondsFor(q.i); return false;
      });
    }
    var share = (budget - 40 - used) / Math.max(1, foci.length);   /* reserve 40s for pairs */
    foci.forEach(function (n, i) { fill(n.no, used + share); });
    if (used < budget - 60) focusNodes(12).slice(3).forEach(function (n) { if (used < budget - 60) fill(n.no, budget - 40); });
    /* 2 confusable pairs — from today's focus topics, not yet answered */
    var ps = [];
    foci.forEach(function (n) { pairs(n.no).forEach(function (p) { if (!S.pairs[p.id] && ps.length < 2) ps.push(p.id); }); });
    if (ps.length < 2) PR.forEach(function (p) { if (!S.pairs[p.id] && ps.length < 2) ps.push(p.id); });
    /* order — review first, pairs interleaved between new sentences */
    var seq = due.map(function (id) { return { k: "ox", id: id, re: 1 }; });
    fresh.forEach(function (id, i) {
      seq.push({ k: "ox", id: id });
      if (ps.length && (i === Math.floor(fresh.length / 3) || i === Math.floor(fresh.length * 2 / 3))) seq.push({ k: "pair", id: ps.shift() });
    });
    ps.forEach(function (id) { seq.push({ k: "pair", id: id }); });
    S.today = { date: TODAY, min: minutes(), seq: seq, foci: foci.map(function (n) { return n.no; }), pos: 0 };
    save();
    return decorate(S.today);
  }
  function decorate(t) {
    var done = 0;
    t.seq.forEach(function (s) { if (s.done) done++; });
    return { date: t.date, min: t.min, seq: t.seq, foci: t.foci.map(function (no) { return NODE[no]; }),
             total: t.seq.length, done: done, re: t.seq.filter(function (s) { return s.re; }).length,
             finished: done >= t.seq.length };
  }
  function markToday(i) { if (S.today && S.today.seq[i]) { S.today.seq[i].done = 1; save(); } }

  /* ── streak · calendar ── */
  function streak() {
    var n = 0, d = new Date();
    if (!S.days[ymd(d)]) d.setDate(d.getDate() - 1);   /* count from yesterday if today has nothing yet */
    while (S.days[ymd(d)]) { n++; d.setDate(d.getDate() - 1); }
    return n;
  }
  /* ── tier — shield badge.
     Determined by what share of the subject's sentences are "held long-term"
     (spaced-review box 3 or higher, i.e. survived past the 7-day gap). */
  var TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"], TIER_CUT = [0, 0.05, 0.15, 0.3, 0.5];
  function tier() {
    var n = 0, held = 0;
    Object.keys(QB).forEach(function (k) { n += QB[k].length; });
    Object.keys(S.ans).forEach(function (id) { if (ITEM[id] && S.ans[id].box >= 3) held++; });
    var r = n ? held / n : 0, t = 0;
    for (var i = 0; i < TIER_CUT.length; i++) if (r >= TIER_CUT[i]) t = i;
    var lo = TIER_CUT[t], hi = TIER_CUT[t + 1] || 1, step = (r - lo) / (hi - lo);
    var div = t === 4 ? "" : step < 1 / 3 ? " III" : step < 2 / 3 ? " II" : " I";
    return { name: TIERS[t] + div, rank: t, held: held, n: n };
  }
  /* ★ tier badges default to hidden — no exam category is set as "show by
     default" yet. Add the logic here once real exam categories warrant it. */
  function tierOn() { return P.tierOn != null ? !!P.tierOn : false; }
  function setTierOn(v) { P.tierOn = !!v; savePref(); }
  function days() { return S.days; }
  function todayCount() { return (S.days[TODAY] || { n: 0 }).n; }

  /* ── 20-question placement test ──
     One question from each of 20 topics — favoring topics with more past
     questions, spread evenly across areas. Only sentences short enough to
     read in the time allowed (≤90 characters). Mixed by date so the same
     set doesn't repeat every day. */
  function placementSet(k) {
    k = k || 20;
    var byPart = {};
    T.nodes.filter(function (n) { return n.q >= 8; }).sort(function (a, b) { return b.q - a.q; })
      .forEach(function (n) { (byPart[n.part] = byPart[n.part] || []).push(n); });
    var picks = [], parts = Object.keys(byPart), r = 0;
    while (picks.length < k && r < 40) {
      parts.forEach(function (p) { if (picks.length < k && byPart[p][r]) picks.push(byPart[p][r]); });
      r++;
    }
    var seed = TODAYN;
    /* ★ balance True and False — the pool skews True, so a naive pick lets learners ace it by answering "True" every time */
    return picks.map(function (n, i) {
      var want = i % 2 ? "X" : "O";
      var c = qs(n.no).filter(function (q) { return q.c === "A" && !q.sa && !q.mc && q.t.length <= 90 && q.t.length >= 25; });
      if (!c.length) c = qs(n.no).filter(function (q) { return !q.mc; });
      if (!c.length) return null;            /* subjects that are nothing but past-question solving skip the placement test */
      var w = c.filter(function (q) { return q.ox === want; });
      if (w.length) c = w;
      return c[(seed + n.no * 7) % c.length];
    }).filter(Boolean);
  }
  function setPlacement(rec) {
    /* rec = [{id, ok, ms, to}] */
    var per = {};
    rec.forEach(function (r) {
      var q = ITEM[r.id]; if (!q) return;
      var p = NODE[q.n].part;
      per[p] = per[p] || { n: 0, ok: 0 }; per[p].n++; if (r.ok) per[p].ok++;
    });
    var weak = Object.keys(per).sort(function (a, b) { return per[a].ok / per[a].n - per[b].ok / per[b].n; })[0];
    S.place = { at: Date.now(), n: rec.length, ok: rec.filter(function (r) { return r.ok; }).length,
                per: per, weakPart: weak ? +weak : null };
    delete S.today;
    save();
    return S.place;
  }

  /* ── where two sentences diverge ──
     Finds the shared prefix from the start and the shared suffix from the
     end, character by character, and highlights only the mismatched span
     in between with <mark>. A trap sentence is usually identical before
     and after a single changed phrase, so this simple approach works well
     enough in practice. */
  function markDiff(a, b) {
    a = a || ""; b = b || "";
    var i = 0, la = a.length, lb = b.length;
    while (i < la && i < lb && a[i] === b[i]) i++;
    var j = 0, maxTail = Math.min(la - i, lb - i);
    while (j < maxTail && a[la - 1 - j] === b[lb - 1 - j]) j++;
    function paint(s) {
      var head = s.slice(0, i), mid = s.slice(i, s.length - j), tail = s.slice(s.length - j);
      return esc(head) + (mid ? "<mark>" + esc(mid) + "</mark>" : "") + esc(tail);
    }
    return [paint(a), paint(b)];
  }

  /* ── theme ── */
  var SKINS = [
    { v: "white", n: "White", c: "#FFFFFF" },
    { v: "jelly", n: "Jelly", c: "#FFD3E6" },
    { v: "night", n: "Night", c: "#0B0D11" }
  ];
  function skin() { try { return localStorage.getItem(SKIN) || "white"; } catch (e) { return "white"; } }
  function setSkin(v) {
    try { localStorage.setItem(SKIN, v); } catch (e) {}
    document.documentElement.dataset.skin = v;
    window.dispatchEvent(new CustomEvent("terra:skin"));
  }

  /* ── nav — 4 items. bottom tab bar on phone ── */
  var ICON = {
    home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/></svg>',
    tree: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><ellipse cx="12" cy="12" rx="10" ry="5"/><circle cx="21" cy="11" r="1.2" fill="currentColor"/></svg>',
    drill: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L4 14h7l-1 8 9-12h-7z"/></svg>',
    set: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg>'
  };
  var PAGES = [["index.html", "Home", "home"], ["skilltree.html", "Skill Tree", "tree"],
               ["drill.html", "Training", "drill"], ["settings.html", "Settings", "set"]];
  function mountNav(here) {
    /* first-time visitors go to setup first — but never redirect an automated test agent (webdriver) */
    if (!onboarded() && here !== "start.html" && !navigator.webdriver && !/[?&]nostart/.test(location.search)) {
      location.replace("start.html"); return;
    }
    var nav = document.createElement("div");
    nav.className = "nav";
    nav.innerHTML = '<div class="in"><a class="logo" href="index.html"><i></i>' + esc(window.BRAND || T.brand) +
      '<span class="sub">' + esc(T.subject) + "</span></a>" +
      '<nav class="navlinks">' + PAGES.map(function (p) {
        return '<a href="' + p[0] + '"' + (p[0] === here ? ' class="on"' : "") + ">" + p[1] + "</a>";
      }).join("") + "</nav></div>";
    document.body.insertBefore(nav, document.body.firstChild);
    var tab = document.createElement("nav");
    tab.className = "tabbar";
    tab.innerHTML = PAGES.map(function (p) {
      return '<a href="' + p[0] + '"' + (p[0] === here ? ' class="on"' : "") + ">" + ICON[p[2]] + "<span>" + p[1] + "</span></a>";
    }).join("");
    document.body.appendChild(tab);
  }
  function mountNext() {}   /* called by the old skill tree screen; left empty since Home does the recommending here */

  function esc(t) {
    return String(t == null ? "" : t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function num(n) { return (n || 0).toLocaleString("en-US"); }
  function src(q) { return (q.y ? q.y + " " : "") + (q.e || "") + (q.qn ? " Q" + q.qn : "") + (q.m ? " " + q.m : ""); }

  function exportData() { return JSON.stringify({ v: 1, pref: P, rec: S }); }
  function importData(txt) {
    var o = JSON.parse(txt);
    if (!o || !o.rec) throw new Error("That doesn't look like a backup file.");
    S = o.rec; P = o.pref || P; save(); savePref();
  }

  window.GB = {
    T: T, Q: QB, subject: T.subject, brand: window.BRAND || T.brand,
    NODE: NODE, CH: CH, PART: PART, nodes: T.nodes, chs: T.chs, parts: T.parts,
    node: function (no) { return NODE[no]; }, ch: function (k) { return CH[k]; }, part: function (n) { return PART[n]; },
    nodesOf: function (k) { return (CH[k] || { nodes: [] }).nodes.map(function (n) { return NODE[n]; }); },
    chsOf: function (p) { return (PART[p] || { chs: [] }).chs.map(function (k) { return CH[k]; }); },
    partNodes: partNodes,
    qs: qs, item: item, pairs: pairs, pair: pair, markDiff: markDiff,
    nodeStat: nodeStat, chStat: chStat, partStat: partStat, overall: overall,
    answer: answer, pairAnswer: pairAnswer, answered: answered, reset: reset,
    dueList: dueList, wrongList: wrongList, focusNodes: focusNodes, freshOf: freshOf,
    today: today, markToday: markToday, streak: streak, todayCount: todayCount, tier: tier, tierOn: tierOn, setTierOn: setTierOn, days: days, SEC_PER: SEC_PER,
    placementSet: placementSet, setPlacement: setPlacement, placement: function () { return S.place || null; },
    track: track, setTrack: setTrack, exam: exam, setExam: setExam, subs: subs, cur: cur, setCur: setCur, seriesName: seriesName, goal: goal, goalMark: goalMark, setGoal: setGoal, dday: dday,
    minutes: minutes, setMinutes: setMinutes, name: name, setName: setName,
    onboarded: onboarded, setOnboarded: setOnboarded,
    skin: skin, setSkin: setSkin, SKINS: SKINS,
    mountNav: mountNav, mountNext: mountNext,
    esc: esc, num: num, src: src, ymd: ymd,
    exportData: exportData, importData: importData,
    state: function () { return S; }
  };
})();
