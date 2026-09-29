/* ═══════════════════════════════════════════════════════════
   {{BRAND}} — data layer (US English frame)

   Screens call only this file. data.js is a pipeline artifact and is never
   hand-edited. Study history piles up only in this browser — localStorage
   `te.<subject key>.v1` · settings `te.pref.v1` · theme `te.skin`
   (★ prefix is "te." so it never collides with the sister apps' "tj.",
   "jg.", "mj." prefixes — served from the same github.io, browser storage
   would otherwise mix).

   Learning features (all in this file, all local - nothing is sent anywhere):
     - wrong-choice cause tags (data: mc.wt, built by tools/build_reg.py) -> S.wlog, cause picker
     - next-question score (FORMULA below, shown on method.html)  - readiness range (Wilson)
     - study plan re-spread from what is left  - notes and flashcards (S.notes, S.cards)
   New keys live inside the existing `te.<subject key>.v1` object (wlog, notes, cards) and in
   `te.pref.v1` (hours, planToday) - no new top-level localStorage keys.

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
  S.ans = S.ans || {}; S.days = S.days || {}; S.pairs = S.pairs || {}; S.flags = S.flags || {};
  S.wlog = S.wlog || []; S.notes = S.notes || {}; S.cards = S.cards || {};
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
  /* Section switch (REG / FAR / TCP / AUD / CFA): the per-exam settings are parked under P.sec[<exam id>] and the target exam's own
     are restored, so each section keeps its own test date, weekly hours, placement result, today's split and current Area.
     Settings saved before sections existed sit at the top level and belong to the exam that was active (REG). Question
     history is stored per subject (te.<subject key>.v1), so REG, FAR, TCP and AUD history never mix. */
  var SEC_KEYS = ["goal", "goalMine", "hours", "place", "planToday", "cur"];
  function setExam(id, sid) {
    var from = P.exam || (P.onboarded ? exam().id : null);
    if (from && from !== id) {
      P.sec = P.sec || {};
      var parked = {};
      SEC_KEYS.forEach(function (k) { if (P[k] != null) parked[k] = P[k]; delete P[k]; });
      P.sec[from] = parked;
      var back = P.sec[id] || {};
      SEC_KEYS.forEach(function (k) { if (back[k] != null) P[k] = back[k]; });
    }
    P.exam = id; P.series = sid || null;
    P.subs = C ? C.subsOf(id, sid) : [];
    if (!P.goalMine) P.goal = exam().date;
    savePref();
  }
  /* Home switch: returns {setup: true} the first time a section is opened (the caller sends the learner to test date + placement check) */
  function switchSection(id) {
    var e = C && C.exam(id);
    if (!e || P.exam === id) return { setup: false };
    var fresh = !(P.sec && P.sec[id]);
    setExam(id, null);
    var ok = subs().filter(function (k) { return !window.READY || window.READY[k]; });
    if (!P.cur || subs().indexOf(P.cur) < 0) P.cur = ok[0] || subs()[0];
    savePref();
    return { setup: fresh };
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
  function applyAnswer(St, id, ok, x) {
    x = x || {};
    var a = St.ans[id] || { n: 0, box: 0 };
    a.n = (a.n || 0) + 1;
    a.ok = !!ok; a.at = Date.now(); a.conf = x.conf || null; a.ms = x.ms || 0;
    if (x.pick != null) a.pick = x.pick;
    if (ok) a.box = x.conf === "sure" ? Math.min(5, (a.box || 0) + 1) : Math.max(1, Math.min(a.box || 0, 1));
    else a.box = 0;
    a.due = TODAYN + GAP[a.box];
    if (x.kind) a.kind = x.kind;
    St.ans[id] = a;
    St.days = St.days || {};
    var d = St.days[TODAY] || (St.days[TODAY] = { n: 0, ok: 0, ms: 0 });
    d.n++; if (ok) d.ok++; d.ms += Math.min(x.ms || 0, 60000);
    /* every wrong pick is logged (S.ans only keeps the last attempt): which choice, its auto cause tag, confidence */
    if (!ok && x.pick != null) {
      var wt = x.wt || (ITEM[id] && ITEM[id].mc && ITEM[id].mc.wt) || null;
      St.wlog = St.wlog || [];
      St.wlog.push({ id: id, at: Date.now(), day: TODAY, pick: x.pick, auto: (wt && wt[x.pick]) || "unclassified", conf: x.conf || null });
      if (St.wlog.length > 400) St.wlog = St.wlog.slice(-400);
    }
    return a;
  }
  function answer(id, ok, x) { var a = applyAnswer(S, id, ok, x); save(); return a; }
  /* Write to another subject's saved history (the mock exam and placement check span every Area) */
  function curKey() { return T.key || T.subject; }
  function stateOf(key) {
    if (!key || key === curKey()) return S;
    var o = read("te." + key + ".v1", null) || {};
    o.ans = o.ans || {}; o.days = o.days || {}; o.pairs = o.pairs || {}; o.flags = o.flags || {};
    o.wlog = o.wlog || []; o.notes = o.notes || {}; o.cards = o.cards || {};
    return o;
  }
  function commit(key, St) { if (St === S) { save(); return; } St.at = Date.now(); write("te." + key + ".v1", St); }
  function answerIn(key, id, ok, x) { var St = stateOf(key), a = applyAnswer(St, id, ok, x); commit(key, St); return a; }
  /* flag — the learner's own mark on a question */
  function flagged(id, key) { var St = stateOf(key); return !!(St.flags && St.flags[id]); }
  function setFlag(id, on, key) {
    var St = stateOf(key);
    St.flags = St.flags || {};
    if (on) St.flags[id] = Date.now(); else delete St.flags[id];
    commit(key || curKey(), St);
  }
  function flagList() {
    return Object.keys(S.flags || {}).filter(function (id) { return ITEM[id]; }).sort(function (a, b) { return S.flags[b] - S.flags[a]; });
  }
  function pairAnswer(pid, ok) {
    S.pairs[pid] = { ok: !!ok, at: Date.now() };
    var d = S.days[TODAY] || (S.days[TODAY] = { n: 0, ok: 0, ms: 0 });
    d.n++; if (ok) d.ok++;
    save();
  }
  function answered(id) { return S.ans[id] || null; }
  function reset() { S = { ans: {}, days: {}, pairs: {}, flags: {}, wlog: [], notes: {}, cards: {} }; delete P.planToday; savePref(); save(); }

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
    var rec = list.filter(function (q) { return S.ans[q.i]; }).sort(function (a, b) { return S.ans[b.i].at - S.ans[a.i].at; }).slice(0, 20);
    var acc = rec.length ? Math.round(rec.filter(function (q) { return S.ans[q.i].ok; }).length / rec.length * 100) : null;
    return { no: no, n: n, solved: solved, correct: correct, pct: pct, acc: acc, prog: prog, achieve: achieve, lastAt: last,
             mastery: solved ? correct / solved : null,
             state: !n ? "empty" : achieve >= 80 ? "done" : solved ? "wip" : "none" };
  }
  /* accuracy by skill level across this subject's answered questions */
  function skillStats() {
    var out = {};
    Object.keys(QB).forEach(function (no) {
      QB[no].forEach(function (q) {
        var a = S.ans[q.i]; if (!a || !q.mc || !q.mc.tags) return;
        var k = q.mc.tags.skill, o = out[k] || (out[k] = { n: 0, ok: 0 });
        o.n++; if (a.ok) o.ok++;
      });
    });
    return out;
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
  /* True/False sentences are not part of the REG bank any more (concept checks only) — REG sessions are multiple choice */
  function usable(q) { return !(q.ox && /^(reg|far|tcp|aud)_/.test(T.key || "")); }
  function freshOf(no, k) {
    return qs(no).filter(function (q) { return usable(q) && !S.ans[q.i]; })
      .sort(function (a, b) { return rank(b) - rank(a); }).slice(0, k);
  }
  /* today's review — items whose due date has arrived. Misses (box 0) come first */
  function dueList() {
    return Object.keys(S.ans).filter(function (id) {
      var a = S.ans[id]; return ITEM[id] && usable(ITEM[id]) && a.due != null && a.due <= TODAYN && !(a.at && ymd(new Date(a.at)) === TODAY && a.ok);
    }).sort(function (a, b) { return (S.ans[a].box - S.ans[b].box) || (S.ans[a].at - S.ans[b].at); });
  }
  function wrongList() {
    return Object.keys(S.ans).filter(function (id) { return ITEM[id] && !S.ans[id].ok; })
      .sort(function (a, b) { return ((ITEM[b].mc ? 1 : 0) - (ITEM[a].mc ? 1 : 0)) || (S.ans[b].at - S.ans[a].at); });
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
    var budget = budgetSec();
    if (S.today && S.today.date === TODAY && S.today.bud === budget) return decorate(S.today);
    /* workload is filled by time (seconds) - a past question (source + 4-5 choices) is about 60s
       (an estimate, not yet measured). Questions are the highest-scoring ones from scoreOf() (see FORMULA):
       weak topic + repeated wrong-choice type + review due. */
    function secondsFor(id) { var q = ITEM[id]; return q && q.mc ? SEC_MC : SEC_PER; }
    var used = 0, picked = [], perNode = {}, skipped = [];
    ranked(null).forEach(function (c) {
      if (used + secondsFor(c.q.i) > budget) return;
      if ((perNode[c.q.n] || 0) >= FORMULA.perNode) { skipped.push(c); return; }
      picked.push(c); perNode[c.q.n] = (perNode[c.q.n] || 0) + 1; used += secondsFor(c.q.i);
    });
    skipped.forEach(function (c) { if (used + secondsFor(c.q.i) <= budget) { picked.push(c); used += secondsFor(c.q.i); } });
    var byNode = {};
    picked.forEach(function (c) { byNode[c.q.n] = (byNode[c.q.n] || 0) + c.score; });
    var foci = Object.keys(byNode).sort(function (a, b) { return byNode[b] - byNode[a]; }).slice(0, 3).map(Number);
    var ps = [];
    if (PR.length && budget - used >= 40) foci.forEach(function (no) { pairs(no).forEach(function (p) { if (!S.pairs[p.id] && ps.length < 2) ps.push(p.id); }); });
    var seq = picked.map(function (c) { return { k: "ox", id: c.q.i, re: c.due ? 1 : 0 }; });
    ps.forEach(function (id, i) { seq.splice(Math.min(seq.length, Math.floor(seq.length * (i + 1) / 3)), 0, { k: "pair", id: id }); });
    S.today = { date: TODAY, min: Math.round(budget / 60), bud: budget, seq: seq, foci: foci, pos: 0 };
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

  /* === next-question score ===
     score(q) = 100 x ( wTopic*T + wType*E + wDue*D )   - all three parts are 0..1
       T  weak topic          = 1 - (correct + prior*priorN) / (answered + priorN)   over the question's Topic (last attempt per question).
                                No answers yet -> 1 - prior = 0.4, so an untouched topic ranks below a topic you are missing.
       E  repeated error type = min(1, sum share(type) * count(type in q) / typeFull)
                                share = that type's share of your last typeWindow wrong answers (cause you set, else the auto tag;
                                "unclassified" and "guessed" are left out). A type counts only after it shows up typeMin times.
                                count(type in q) = how many of the question's 3 wrong choices carry that tag (mc.wt).
       D  review due          = 0 for a new question; for an answered one whose spaced-review date has arrived:
                                min(1, dueBase + dueStep * days overdue). (Gaps by box: 0, 1, 3, 7, 14, 30 days.)
     Candidates are new questions plus questions due for review; ties fall back to recency of the exam series.
     At most perNode questions from one Topic go into a day's set unless nothing else fits. */
  var FORMULA = { wTopic: 0.45, wType: 0.30, wDue: 0.25, prior: 0.6, priorN: 2, typeWindow: 30, typeMin: 2, typeFull: 2,
                  dueBase: 0.5, dueStep: 0.1, perNode: 8, gaps: GAP };
  var CAUSES = [
    { v: "concept", n: "Concept error", d: "The rule itself was misread or a different rule was applied." },
    { v: "calc", n: "Calculation slip", d: "The rule was right but a number or step went wrong." },
    { v: "trap", n: "Trap wording", d: "A tempting phrase or an absolute word pulled you off the rule." },
    { v: "limit", n: "Limit or threshold mix-up", d: "A dollar limit, percentage, day count or year count was confused." },
    { v: "guess", n: "Guessed", d: "You did not know it and picked one." },
    { v: "unclassified", n: "Unclassified", d: "The explanation did not clearly fit one type." }
  ];
  var CAUSE_NAME = {}; CAUSES.forEach(function (c) { CAUSE_NAME[c.v] = c.n; });
  function causeName(v) { return CAUSE_NAME[v] || CAUSE_NAME.unclassified; }
  function effCause(e) { return e.cause || e.auto || "unclassified"; }

  function typeShares(St) {
    St = St || S;
    var w = (St.wlog || []).slice(-FORMULA.typeWindow), c = {};
    w.forEach(function (e) { var t = effCause(e); if (t === "unclassified" || t === "guess") return; c[t] = (c[t] || 0) + 1; });
    var out = {};
    Object.keys(c).forEach(function (t) { if (c[t] >= FORMULA.typeMin) out[t] = c[t] / Math.max(1, w.length); });
    return out;
  }
  function topicWeak(no) {
    var st = nodeStat(no);
    return 1 - (st.correct + FORMULA.prior * FORMULA.priorN) / (st.solved + FORMULA.priorN);
  }
  function dueDays(id) {
    var a = S.ans[id];
    if (!a || a.due == null || a.due > TODAYN) return null;
    if (a.at && ymd(new Date(a.at)) === TODAY && a.ok) return null;
    return TODAYN - a.due;
  }
  function scoreOf(q, ctx) {
    ctx = ctx || { shares: typeShares(), weak: {} };
    if (ctx.weak[q.n] == null) ctx.weak[q.n] = topicWeak(q.n);
    var T = ctx.weak[q.n], E = 0, D = 0, types = [];
    if (q.mc && q.mc.wt) {
      var cnt = {};
      q.mc.wt.forEach(function (t) { if (t && t !== "unclassified") cnt[t] = (cnt[t] || 0) + 1; });
      Object.keys(cnt).forEach(function (t) { if (ctx.shares[t]) { E += ctx.shares[t] * cnt[t] / FORMULA.typeFull; types.push(t); } });
      E = Math.min(1, E);
    }
    var dd = dueDays(q.i), due = dd != null;
    if (due) D = Math.min(1, FORMULA.dueBase + FORMULA.dueStep * dd);
    var total = 100 * (FORMULA.wTopic * T + FORMULA.wType * E + FORMULA.wDue * D);
    return { q: q, T: T, E: E, D: D, due: due, types: types, score: total };
  }
  /* new questions + questions whose review date arrived, best score first. `no` limits to one Topic. */
  function ranked(no, exclude) {
    var ctx = { shares: typeShares(), weak: {} }, out = [], nos = no != null ? [String(no)] : Object.keys(QB);
    nos.forEach(function (k) {
      qs(k).forEach(function (q) {
        if (!usable(q) || (exclude && exclude[q.i])) return;
        if (S.ans[q.i] && dueDays(q.i) == null) return;
        out.push(scoreOf(q, ctx));
      });
    });
    return out.sort(function (a, b) { return (b.score - a.score) || (rank(b.q) - rank(a.q)) || (a.q.i < b.q.i ? -1 : 1); });
  }
  function pickNext(k, excludeIds, no) {
    var ex = {}; (excludeIds || []).forEach(function (id) { ex[id] = 1; });
    return ranked(no, ex).slice(0, k || 1).map(function (c) { return c.q; });
  }
  /* why a question was chosen - chips on the question card */
  function reasonOf(id) {
    var q = ITEM[id]; if (!q) return [];
    var c = scoreOf(q), r = [];
    if (c.due) r.push("Review due");
    if (c.T >= 0.5) r.push("Weak topic");
    if (c.types.length) r.push("Repeated: " + c.types.map(causeName).join(", "));
    return r;
  }

  /* === wrong-answer causes === */
  function setCause(id, tag, key) {
    var St = stateOf(key), l = St.wlog || [];
    for (var i = l.length - 1; i >= 0; i--) if (l[i].id === id) { l[i].cause = tag; break; }
    if (St.ans[id]) St.ans[id].cause = tag;
    commit(key || curKey(), St);
  }
  function lastWrong(id, key) {
    var l = stateOf(key).wlog || [];
    for (var i = l.length - 1; i >= 0; i--) if (l[i].id === id) return l[i];
    return null;
  }
  function allStates() { return subs().filter(function (k) { return !window.READY || window.READY[k]; }).map(function (k) { return { key: k, st: stateOf(k) }; }); }
  function weekStart(ms) { var d = new Date(ms); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d; }
  /* weekly report - wrong answers per week by cause (yours if set, else the auto tag) + confident-and-wrong count */
  function weeklyReport(weeks) {
    weeks = weeks || 6;
    var start = weekStart(Date.now()), rows = [], idx = {};
    for (var i = 0; i < weeks; i++) {
      var d = new Date(start); d.setDate(d.getDate() - 7 * i);
      var r = { start: ymd(d), t0: d.getTime(), n: 0, sure: 0, by: {} };
      rows.push(r); idx[r.t0] = r;
    }
    var tot = { n: 0, sure: 0, by: {} };
    allStates().forEach(function (x) {
      (x.st.wlog || []).forEach(function (e) {
        var row = idx[weekStart(e.at).getTime()], t = effCause(e);
        tot.n++; tot.by[t] = (tot.by[t] || 0) + 1; if (e.conf === "sure") tot.sure++;
        if (!row) return;
        row.n++; row.by[t] = (row.by[t] || 0) + 1; if (e.conf === "sure") row.sure++;
      });
    });
    return { rows: rows, total: tot };
  }

  /* === readiness range ===
     Per Area: Wilson score interval (z = 1.645, 90%) for the share answered correctly, using each question's
     latest attempt. Range = sum weight*lo ... sum weight*hi over the Areas, weights = Blueprint midpoints. An Area with no
     answers counts as 0-100, so the range is wide until every Area has been tried. This is a % correct on questions
     you chose to practise - not a scaled exam score and not a pass prediction. */
  var READY_Z = 1.645, READY_MIN = 10;
  function wilson(k, n, z) {
    if (!n) return { p: 0.5, lo: 0, hi: 1 };
    var p = k / n, z2 = z * z, d = 1 + z2 / n, c = (p + z2 / (2 * n)) / d, h = z * Math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / d;
    return { p: p, lo: Math.max(0, c - h), hi: Math.min(1, c + h) };
  }
  function areaWeight(k) { var C0 = window.CATALOG, w = C0 && C0.weight(k); return w || AREA_W[C0 && C0.area(k)] || 10; }
  function readiness() {
    var per = [], W = 0, lo = 0, hi = 0, N = 0, touched = 0;
    subs().forEach(function (k) {
      if (window.READY && !window.READY[k]) return;
      var st = stateOf(k), n = 0, ok = 0;
      Object.keys(st.ans).forEach(function (id) { n++; if (st.ans[id].ok) ok++; });
      var w = wilson(ok, n, READY_Z), wt = areaWeight(k);
      per.push({ key: k, name: window.CATALOG ? CATALOG.name(k) : k, area: window.CATALOG ? CATALOG.area(k) : "", w: wt, n: n, ok: ok,
                 pct: n ? Math.round(ok / n * 100) : null, lo: Math.round(w.lo * 100), hi: Math.round(w.hi * 100) });
      W += wt; lo += wt * w.lo; hi += wt * w.hi; N += n; if (n) touched++;
    });
    return { of: subs().length, ready: N >= READY_MIN, lo: W ? Math.round(lo / W * 100) : 0, hi: W ? Math.round(hi / W * 100) : 100, n: N, areas: per, touched: touched, z: READY_Z, min: READY_MIN };
  }

  /* === study plan ===
     Needs weekly hours (P.hours) and a test date. Pool per Area = questions never answered + questions last answered wrong.
     One question ~ 1 minute (SEC_MC = 60 s, an estimate). Minutes per day = hours x 60 / 7.
     Each day's set is split across Areas by  weight = Blueprint weight x (0.5 + weak),  weak = 1 - (correct + prior*priorN)/(answered + priorN)
     (largest-remainder rounding, capped by what is left in the Area). Only today's split is stored (frozen for the day):
     tomorrow the plan is rebuilt from what is actually left, so missed days and new results re-spread automatically.
     A new placement check clears today's split and re-spreads. */
  function planOn() { return !!(P.hours && P.goalMine && P.goal && dayNo(P.goal) - TODAYN > 0); }
  function setHours(h) { P.hours = h ? Math.max(1, Math.min(60, +h)) : null; delete P.planToday; savePref(); delete S.today; save(); }
  function hours() { return P.hours || 0; }
  function poolOf(k) {
    var st = stateOf(k), n = (window.READY && window.READY[k] && window.READY[k].n) || 0, seen = 0, ok = 0, wrong = 0;
    Object.keys(st.ans).forEach(function (id) { seen++; if (st.ans[id].ok) ok++; else wrong++; });
    var weak = 1 - (ok + FORMULA.prior * FORMULA.priorN) / (seen + FORMULA.priorN);
    return { key: k, name: window.CATALOG ? CATALOG.name(k) : k, left: Math.max(0, n - seen) + wrong, fresh: Math.max(0, n - seen), wrong: wrong, weak: weak, w: areaWeight(k) };
  }
  function spread(N, pools, left) {
    var alloc = {}, rem = N, guard = 0;
    pools.forEach(function (p) { alloc[p.key] = 0; });
    while (rem > 0 && guard++ < 8) {
      var open = pools.filter(function (p) { return left[p.key] - alloc[p.key] > 0; });
      if (!open.length) break;
      var tw = open.reduce(function (t, p) { return t + p.w * (0.5 + p.weak); }, 0), given = 0, fr = [];
      open.forEach(function (p) {
        var e = rem * p.w * (0.5 + p.weak) / tw, room = left[p.key] - alloc[p.key], g = Math.min(room, Math.floor(e));
        alloc[p.key] += g; given += g; fr.push({ p: p, r: e - Math.floor(e) });
      });
      fr.sort(function (a, b) { return b.r - a.r; }).forEach(function (f) {
        if (given < rem && left[f.p.key] - alloc[f.p.key] > 0) { alloc[f.p.key]++; given++; }
      });
      rem -= given; if (!given) break;
    }
    return alloc;
  }
  function plan() {
    if (!P.hours) return { on: false, why: "hours" };
    if (!P.goalMine || !P.goal) return { on: false, why: "date" };
    var D = dayNo(P.goal) - TODAYN;
    if (D <= 0) return { on: false, why: "passed" };
    var perDay = Math.max(1, Math.round(P.hours * 60 / 7)), pools = subs().filter(function (k) { return !window.READY || window.READY[k]; }).map(poolOf);
    var left = {}; pools.forEach(function (p) { left[p.key] = p.left; });
    var pt = P.planToday, place = (P.place && P.place.at) || 0, keys = pools.map(function (p) { return p.key; }).join();
    if (!pt || pt.date !== TODAY || pt.hours !== P.hours || pt.goal !== P.goal || pt.place !== place || pt.keys !== keys) {
      pt = { date: TODAY, hours: P.hours, goal: P.goal, place: place, keys: keys, alloc: spread(perDay, pools, left), left: JSON.parse(JSON.stringify(left)) };
      P.planToday = pt; savePref();
    }
    var sim = JSON.parse(JSON.stringify(pt.left)), days = [], total = 0, doneOn = null, now = new Date();
    Object.keys(pt.left).forEach(function (k) { total += pt.left[k]; });
    for (var d = 0; d < D; d++) {
      var a = d === 0 ? pt.alloc : spread(perDay, pools, sim), sum = 0, rest = 0;
      Object.keys(a).forEach(function (k) { sim[k] -= a[k]; sum += a[k]; });
      days.push({ date: ymd(new Date(now.getFullYear(), now.getMonth(), now.getDate() + d)), total: sum, alloc: a });
      Object.keys(sim).forEach(function (k) { rest += Math.max(0, sim[k]); });
      if (!rest && doneOn == null) doneOn = d;
    }
    var rest2 = 0; Object.keys(sim).forEach(function (k) { rest2 += Math.max(0, sim[k]); });
    var need = Math.ceil(total / D);
    return { on: true, days: D, perDay: perDay, hours: P.hours, goal: P.goal, pools: pools, today: pt.alloc, list: days, total: total,
             short: rest2, needPerDay: need, needHours: Math.ceil(need * 7 / 60 * 10) / 10, finishDay: doneOn };
  }
  /* seconds budget for today's set in the current Area */
  function budgetSec() {
    if (planOn()) { var pl = plan(); if (pl.on) return (pl.today[curKey()] || 0) * SEC_MC; }
    return minutes() * 60;
  }

  /* === notes, copy, flashcards === */
  function note(id, key) { var n = stateOf(key).notes[id]; return n ? n.t : ""; }
  function setNote(id, text, key) {
    var St = stateOf(key); text = String(text || "").slice(0, 2000);
    if (text.trim()) St.notes[id] = { t: text, at: Date.now() }; else delete St.notes[id];
    commit(key || curKey(), St);
  }
  function noteCount() { var n = 0; allStates().forEach(function (x) { n += Object.keys(x.st.notes).length; }); return n; }
  function letter(i) { return "ABCDE"[i]; }
  function cleanWhy(t) { return String(t || "").replace(/^(Correct|Incorrect)\.\s*/, ""); }
  /* plain-text explanation for the clipboard */
  function explainText(q, pick) {
    var mc = q.mc, a = mc.a - 1, out = [mc.s];
    if (mc.d) out.push(mc.d);
    if (mc.tb) out.push(mc.tb.map(function (r) { return r.join(" | "); }).join("\n"));
    out.push(mc.o.map(function (o, i) { return letter(i) + ". " + o; }).join("\n"));
    out.push("Correct answer: " + letter(a) + (pick != null && pick !== a ? " (you chose " + letter(pick) + ")" : ""));
    if (mc.ex) out.push(mc.o.map(function (o, i) { return letter(i) + " - " + cleanWhy(mc.ex[i]); }).join("\n"));
    if (mc.steps && mc.steps.length) out.push("Solution\n" + mc.steps.map(function (t, i) { return (i + 1) + ". " + t; }).join("\n"));
    if (mc.cite) out.push("Basis: " + mc.cite);
    return out.join("\n\n");
  }
  /* copy - clipboard API, then execCommand; callback(false) when both fail so the screen can show the text selected */
  function copyText(text, cb) {
    function fallback() {
      var ta = document.createElement("textarea"); ta.value = text; ta.setAttribute("readonly", "");
      ta.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0"; document.body.appendChild(ta); ta.select();
      var ok = false; try { ok = document.execCommand("copy"); } catch (e) {}
      ta.remove(); cb(ok);
    }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) navigator.clipboard.writeText(text).then(function () { cb(true); }, fallback);
      else fallback();
    } catch (e) { fallback(); }
  }
  function summarize(t, n) {
    t = String(t || "").replace(/\s+/g, " ").trim();
    if (t.length <= n) return t;
    var c = t.slice(0, n), sp = c.lastIndexOf(" ");
    return (sp > n * 0.6 ? c.slice(0, sp) : c) + "\u2026";
  }
  function hasCard(id, key) { return !!stateOf(key).cards[id]; }
  function makeCard(id) {
    var q = ITEM[id]; if (!q || !q.mc) return null;
    if (S.cards[id]) return S.cards[id];
    var mc = q.mc, a = mc.a - 1, nd = NODE[q.n];
    S.cards[id] = { id: id, key: curKey(), topic: nd ? nd.name : "", front: mc.rl ? mc.rl : summarize(mc.s, 170),
                    ans: letter(a) + ". " + mc.o[a], rule: mc.rat || "", why: cleanWhy(mc.ex ? mc.ex[a] : ""), cite: mc.cite || "",
                    at: Date.now(), box: 0, due: TODAYN, n: 0 };
    save(); return S.cards[id];
  }
  function dropCard(id, key) { var St = stateOf(key); delete St.cards[id]; commit(key || curKey(), St); }
  function cardList() {
    var out = [];
    allStates().forEach(function (x) { Object.keys(x.st.cards).forEach(function (id) { var c = x.st.cards[id]; c.key = x.key; out.push(c); }); });
    return out;
  }
  function dueCards() { return cardList().filter(function (c) { return c.due <= TODAYN; }).sort(function (a, b) { return (a.box - b.box) || (a.due - b.due); }); }
  function gradeCard(key, id, ok) {
    var St = stateOf(key), c = St.cards[id]; if (!c) return;
    c.n = (c.n || 0) + 1; c.last = Date.now();
    c.box = ok ? Math.min(5, (c.box || 0) + 1) : 0;
    c.due = ok ? TODAYN + GAP[c.box] : TODAYN;      /* a missed card stays due today */
    commit(key, St);
  }

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

  /* ── multi-subject helpers ──
     Each data file defines window.TREE / QBANK; the current subject is already loaded. To draw questions from
     every ready Area (placement check, mock exam) the other files are loaded one by one and snapshotted. */
  var POOL = null;
  function loadPool(cb) {
    if (POOL) return cb(POOL);
    var R = window.READY || {}, keys = Object.keys(R).filter(function (k) { return /^(reg|far|tcp|aud)_/.test(k) && (!window.CATALOG || CATALOG.subsOf(P.exam, P.series).indexOf(k) >= 0); });
    if (!keys.length) keys = [curKey()];
    var out = [], saved = { T: window.TREE, Q: window.QBANK, P: window.PAIRS }, i = 0;
    function done() { window.TREE = saved.T; window.QBANK = saved.Q; window.PAIRS = saved.P; POOL = out; cb(out); }
    function next() {
      if (i >= keys.length) return done();
      var k = keys[i++];
      if (k === curKey()) { out.push({ key: k, tree: T, qbank: QB }); return next(); }
      var el = document.createElement("script");
      el.src = "data/" + k + ".js?v=" + ((R[k] && R[k].v) || "");
      el.onload = function () { out.push({ key: k, tree: window.TREE, qbank: window.QBANK }); next(); };
      el.onerror = function () { next(); };
      document.head.appendChild(el);
    }
    next();
  }
  function poolItems(pool) {
    var all = [];
    pool.forEach(function (p) {
      Object.keys(p.qbank).forEach(function (no) {
        var node = p.tree.nodes.filter(function (n) { return n.no === +no; })[0];
        p.qbank[no].forEach(function (q) { if (q.mc) all.push({ key: p.key, area: p.tree.area || "", no: +no, q: q, node: node, subject: p.tree.subject }); });
      });
    });
    return all;
  }
  function seededShuffle(a, seed) {
    var s2 = seed || 1;
    for (var i = a.length - 1; i > 0; i--) { s2 = (s2 * 9301 + 49297) % 233280; var j = Math.floor(s2 / 233280 * (i + 1)); var x = a[i]; a[i] = a[j]; a[j] = x; }
    return a;
  }
  /* Blueprint-weighted draw: n questions spread over the ready Areas by weight (largest remainder),
     mixing skill levels inside an Area. The same seed gives the same set. */
  var AREA_W = { I: 15, II: 20, III: 10, IV: 27, V: 28 };
  function weightedSet(pool, n, seed, only) {
    var all = poolItems(pool).filter(function (x) { return !only || only(x); }), byA = {};
    all.forEach(function (x) { (byA[x.area] = byA[x.area] || []).push(x); });
    /* weight per Area: the catalog weight of the subject the questions come from (each CPA section numbers its own Areas from I) */
    var aw = {};
    all.forEach(function (x) { aw[x.area] = (window.CATALOG && CATALOG.weight(x.key)) || AREA_W[x.area] || 10; });
    var areas = Object.keys(byA), tot = areas.reduce(function (t, k) { return t + aw[k]; }, 0), alloc = {}, used = 0;
    areas.forEach(function (k) { var e = n * aw[k] / tot; alloc[k] = { c: Math.floor(e), r: e - Math.floor(e) }; used += alloc[k].c; });
    areas.slice().sort(function (a, b) { return alloc[b].r - alloc[a].r; }).forEach(function (k) { if (used < n) { alloc[k].c++; used++; } });
    var pick = [];
    areas.forEach(function (k) {
      var l = seededShuffle(byA[k].slice(), seed + k.charCodeAt(k.length - 1) * 31 + k.length);
      var by = {}; l.forEach(function (x) { var sk = x.q.mc.tags ? x.q.mc.tags.skill : "-"; (by[sk] = by[sk] || []).push(x); });
      var ks = Object.keys(by), got = [], r = 0;
      while (got.length < Math.min(alloc[k].c, l.length) && r < 1000) { ks.forEach(function (sk) { if (got.length < alloc[k].c && by[sk][r]) got.push(by[sk][r]); }); r++; }
      pick = pick.concat(got);
    });
    return seededShuffle(pick, seed + 7);
  }
  /* ── placement check ──
     A short check across every ready Area: 4-choice questions without exhibit tables, mixed by date. */
  function placementSet(pool, k) {
    return weightedSet(pool, k || 20, TODAYN, function (x) { return x.q.mc.o.length === 4 && !x.q.mc.tb && x.q.mc.s.length <= 420; });
  }
  function mockSet(pool, n, seed) { return weightedSet(pool, n, seed || (Date.now() % 100000)); }
  function setPlacement(rec) {
    /* rec = [{id, key, area, ok, ms, to}] — kept in the shared preferences (it spans every Area) */
    var per = {};
    rec.forEach(function (r) {
      var o = per[r.area] || (per[r.area] = { n: 0, ok: 0 }); o.n++; if (r.ok) o.ok++;
    });
    var weak = Object.keys(per).sort(function (a, b) { return per[a].ok / per[a].n - per[b].ok / per[b].n; })[0];
    P.place = { at: Date.now(), n: rec.length, ok: rec.filter(function (r) { return r.ok; }).length, per: per, weakArea: weak || null };
    var C2 = window.CATALOG, wk = null;
    if (C2 && weak) C2.subsOf(P.exam, P.series).forEach(function (k) { if (C2.area(k) === weak && window.READY && window.READY[k]) wk = k; });
    if (wk) P.cur = wk;                      /* home opens on the weakest Area */
    delete P.planToday; delete S.today;
    savePref();
    return P.place;
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
  /* chip text: "Area IV · Application" for Terra Prep questions; older sentence data keeps its own source label */
  function src(q) {
    var t = q.mc && q.mc.tags;
    if (t) return "Area " + t.area + " · " + t.skill;
    return (q.y ? q.y + " " : "") + (q.e || "") + (q.qn ? " Q" + q.qn : "") + (q.m ? " " + q.m : "");
  }
  function confOn() { return P.conf != null ? !!P.conf : false; }
  function setConf(v) { P.conf = !!v; savePref(); }
  function placement() { return P.place || null; }

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
    placementSet: placementSet, setPlacement: setPlacement, placement: placement,
    loadPool: loadPool, mockSet: mockSet, poolItems: poolItems, answerIn: answerIn, stateOf: stateOf,
    flagged: flagged, setFlag: setFlag, flagList: flagList, skillStats: skillStats, confOn: confOn, setConf: setConf,
    track: track, setTrack: setTrack, exam: exam, setExam: setExam, switchSection: switchSection, subs: subs, cur: cur, setCur: setCur, seriesName: seriesName, goal: goal, goalMark: goalMark, setGoal: setGoal, dday: dday,
    minutes: minutes, setMinutes: setMinutes, name: name, setName: setName,
    onboarded: onboarded, setOnboarded: setOnboarded,
    skin: skin, setSkin: setSkin, SKINS: SKINS,
    mountNav: mountNav, mountNext: mountNext,
    esc: esc, num: num, src: src, ymd: ymd,
    exportData: exportData, importData: importData,
    state: function () { return S; },
    FORMULA: FORMULA, CAUSES: CAUSES, causeName: causeName, effCause: effCause, scoreOf: scoreOf, ranked: ranked, pickNext: pickNext, reasonOf: reasonOf, typeShares: typeShares,
    setCause: setCause, lastWrong: lastWrong, weeklyReport: weeklyReport, allStates: allStates,
    readiness: readiness, wilson: wilson,
    plan: plan, planOn: planOn, setHours: setHours, hours: hours, SEC_MC: SEC_MC,
    note: note, setNote: setNote, noteCount: noteCount, explainText: explainText, copyText: copyText,
    hasCard: hasCard, makeCard: makeCard, dropCard: dropCard, cardList: cardList, dueCards: dueCards, gradeCard: gradeCard
  };
})();
