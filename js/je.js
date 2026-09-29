/* Journal-entry drill — engine (variant generator, grader, hints, T-accounts) and screens.
   Data: data/je_far.js (window.JE_DATA), built by tools/build_je.py from the transaction-type templates.
   Storage: one key, "te.je.v1" (the app's "te." prefix). Nothing else is written. */
(function () {
  "use strict";
  var DATA = window.JE_DATA;
  if (!DATA) { document.body.innerHTML = '<p style="padding:24px">Data file missing.</p>'; return; }

  /* ═══════════════ expression engine (same language as the Python twin) ═══════════════ */
  var FN = {
    ROUND: function (x, n) { n = n || 0; var m = Math.pow(10, n); return Math.floor(x * m + 0.5) / m; },
    FLOOR: Math.floor, CEIL: Math.ceil,
    MIN: Math.min, MAX: Math.max, ABS: Math.abs, POW: Math.pow,
    MOD: function (a, b) { return a - b * Math.floor(a / b); },
    IF: function (c, a, b) { return c ? a : b; },
    AND: function () { for (var i = 0; i < arguments.length; i++) if (!arguments[i]) return false; return true; },
    OR: function () { for (var i = 0; i < arguments.length; i++) if (arguments[i]) return true; return false; },
    PV: function (r, n, pmt, fv) {
      fv = fv || 0; if (r === 0) return pmt * n + fv;
      var d = Math.pow(1 + r, -n); return pmt * (1 - d) / r + fv * d;
    },
    PVD: function (r, n, pmt, fv) {
      fv = fv || 0; if (r === 0) return pmt * n + fv;
      var d = Math.pow(1 + r, -n); return pmt * (1 + r) * (1 - d) / r + fv * d;
    },
    PMT: function (r, n, pv) { return r === 0 ? pv / n : pv * r / (1 - Math.pow(1 + r, -n)); }
  };
  var FNAMES = Object.keys(FN), FVALS = FNAMES.map(function (k) { return FN[k]; });
  var cache = {};
  function ev(e, env) {
    if (typeof e === "number") return e;
    var names = Object.keys(env), key = e + "#" + names.join(",");
    var f = cache[key];
    if (!f) f = cache[key] = new Function(FNAMES.concat(names).join(","), "return (" + e + ");");
    return f.apply(null, FVALS.concat(names.map(function (n) { return env[n]; })));
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function r6(x) { return Math.floor(x * 1e6 + 0.5) / 1e6; }
  function r2(x) { return Math.floor(x * 100 + 0.5) / 100; }
  function commas(s) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  function fmtNum(v) {
    if (Math.abs(v - Math.round(v)) < 1e-9) return (v < 0 ? "-" : "") + commas(String(Math.floor(Math.abs(v) + 0.5)));
    var s = Math.abs(v).toFixed(2).split("."); return (v < 0 ? "-" : "") + commas(s[0]) + "." + s[1];
  }
  function fmtVal(v, f) {
    if (f === "$") return "$" + fmtNum(v);
    if (f === "n") return fmtNum(v);
    if (f === "%") {
      var s = (v * 100).toFixed(4);
      if (s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
      return s + "%";
    }
    if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v));
    return v.toFixed(6).replace(/0+$/, "").replace(/\.$/, "");
  }
  function fill(text, env) {
    return text.replace(/\{([^{}]+)\}/g, function (m, body) {
      var f = "r", i = body.lastIndexOf("|");
      if (i >= 0) { f = body.slice(i + 1).trim(); body = body.slice(0, i); }
      return fmtVal(ev(body.trim(), env), f);
    });
  }

  /* ═══════════════ data indexes ═══════════════ */
  var COA = {}, TPL = {}, TOPIC = {};
  DATA.coa.forEach(function (a) { COA[a.id] = a; });
  DATA.tpls.forEach(function (t) { TPL[t.id] = t; });
  DATA.topics.forEach(function (t) { TOPIC[t.id] = t; });

  function generate(t, seed) {
    var rnd = mulberry32(seed);
    for (var attempt = 0; attempt < 300; attempt++) {
      var env = {};
      for (var i = 0; i < t.vars.length; i++) {
        var v = t.vars[i];
        if (v.pick) env[v.n] = v.pick[Math.floor(rnd() * v.pick.length)];
        else if (v.min !== undefined) {
          var lo = ev(v.min, env), hi = ev(v.max, env), st = ev(v.step, env);
          var cnt = Math.floor((hi - lo) / st + 1e-9) + 1; if (cnt < 1) cnt = 1;
          env[v.n] = r6(lo + Math.floor(rnd() * cnt) * st);
        } else env[v.n] = ev(v.e, env);
      }
      var ok = true;
      for (var c = 0; c < (t.cons || []).length; c++) if (!ev(t.cons[c], env)) { ok = false; break; }
      if (!ok) continue;
      var out = realize(t, env, seed);
      if (out) return out;
    }
    return null;
  }
  function baseEnv(t) {
    var env = {}, b = t.base || {};
    t.vars.forEach(function (v) {
      if (v.pick) env[v.n] = b[v.n] !== undefined ? b[v.n] : v.pick[0];
      else if (v.min !== undefined) {
        var lo = ev(v.min, env), hi = ev(v.max, env), st = ev(v.step, env);
        env[v.n] = b[v.n] !== undefined ? b[v.n] : r6(lo + Math.floor(Math.floor((hi - lo) / st + 1e-9) / 2) * st);
      } else env[v.n] = ev(v.e, env);
    });
    return env;
  }
  function realize(t, env, seed) {
    var sets = [];
    for (var i = 0; i < t.sets.length; i++) {
      var s = t.sets[i], ls = [], dr = 0, cr = 0;
      for (var j = 0; j < s.lines.length; j++) {
        var l = s.lines[j], amt = r2(ev(l.v, env));
        if (amt === 0) continue;
        var d = { s: l.s, a: l.a, v: amt, why: fill(l.why, env) };
        if (l.alt) d.alt = l.alt;
        ls.push(d); if (l.s === "D") dr += amt; else cr += amt;
      }
      if (Math.abs(dr - cr) > 0.004 || ls.length < 2) return null;   /* never shown: an unbalanced variant is discarded */
      sets.push({ date: fill(s.date, env), prompt: fill(s.prompt, env), lines: ls });
    }
    var mist = (t.mist || []).map(function (m) {
      var d = {}; for (var k in m) d[k] = m[k];
      d.msg = fill(m.msg, env); if (d.v !== undefined) d.v = r2(ev(d.v, env)); return d;
    });
    return { tid: t.id, seed: seed, text: fill(t.text, env), sets: sets, mist: mist, key: t.key ? fill(t.key, env) : "", tol: t.tol || 1 };
  }

  /* ═══════════════ accounts: normalize, resolve, search ═══════════════ */
  function norm(s) {
    return String(s || "").toLowerCase().replace(/&/g, " and ").replace(/[^a-z0-9$ ]+/g, " ").replace(/\s+/g, " ").trim();
  }
  var IDX = DATA.coa.map(function (a) {
    var names = [a.name].concat(a.syn || []).map(function (x) { return { raw: x, n: norm(x) }; });
    names.forEach(function (x) { x.k = x.n.replace(/ /g, ""); x.w = x.n.split(" "); });
    return { id: a.id, names: names };
  });
  var BYNAME = {};
  IDX.forEach(function (e) { e.names.forEach(function (x) { if (!BYNAME[x.n]) BYNAME[x.n] = e.id; if (!BYNAME[x.k]) BYNAME[x.k] = e.id; }); });
  function resolve(text) {
    var n = norm(text); if (!n) return null;
    return BYNAME[n] || BYNAME[n.replace(/ /g, "")] || null;
  }
  function search(q, limit) {
    var n = norm(q); if (!n) return [];
    var toks = n.split(" "), out = [];
    IDX.forEach(function (e) {
      var best = 0, via = null;
      e.names.forEach(function (x, ix) {
        var sc = 0;
        if (x.n === n) sc = 100;
        else if (x.n.indexOf(n) === 0) sc = 85;
        else {
          var all = toks.every(function (t) { return x.w.some(function (w) { return w.indexOf(t) === 0; }); });
          if (all) sc = 65; else if (x.n.indexOf(n) >= 0) sc = 40;
          else if (x.k.indexOf(n.replace(/ /g, "")) >= 0 && n.length > 2) sc = 30;
        }
        if (ix === 0 && sc) sc += 3;
        if (sc > best) { best = sc; via = ix; }
      });
      if (best) out.push({ id: e.id, sc: best, via: via });
    });
    out.sort(function (a, b) { return b.sc - a.sc || COA[a.id].name.length - COA[b.id].name.length; });
    return out.slice(0, limit || 8).map(function (o) {
      return { id: o.id, name: COA[o.id].name, alias: o.via > 0 ? IDX.filter(function (e) { return e.id === o.id; })[0].names[o.via].raw : "" };
    });
  }

  /* ═══════════════ grader ═══════════════ */
  /* The line-by-line grader lives in js/jegrade.js (shared with the TBS journal-entry cell). */
  var GR = window.JEGrade.make(COA);
  function grade(v, si, rows) { return GR.grade(v.sets[si], v.mist, v.tol || 1, rows); }
  function fmtMoney(v) { return "$" + fmtNum(v); }

  /* ═══════════════ hints and T-accounts ═══════════════ */
  var CLS = { asset: "asset", liability: "liability", equity: "equity", revenue: "revenue", expense: "expense", gain: "gain", loss: "loss",
              "contra-asset": "contra-asset", "contra-liability": "contra-liability", "contra-equity": "contra-equity", "contra-revenue": "contra-revenue" };
  function hintLines(set, lv) {
    var names = set.lines.map(function (l) { return { n: COA[l.a].name, l: l }; }).sort(function (a, b) { return a.n < b.n ? -1 : 1; });
    if (lv === 1) return "Accounts: " + names.map(function (x) { return x.n; }).join(", ");
    if (lv === 2) return set.lines.map(function (l) {
      var a = COA[l.a]; return a.name + " " + (l.s === a.n ? "↑" : "↓") + " (" + CLS[a.cls] + ")";
    });
    return set.lines.map(function (l) { return COA[l.a].name + " → " + (l.s === "D" ? "Debit" : "Credit"); });
  }
  function tAccounts(items) {
    /* items: [{a, s, v, si}] → [{a, dr:[{v,si}], cr:[...], net}] in first-appearance order */
    var order = [], map = {};
    items.forEach(function (it) {
      if (!map[it.a]) { map[it.a] = { a: it.a, dr: [], cr: [] }; order.push(it.a); }
      (it.s === "D" ? map[it.a].dr : map[it.a].cr).push({ v: it.v, si: it.si });
    });
    return order.map(function (a) {
      var t = map[a], d = t.dr.reduce(function (x, y) { return x + y.v; }, 0), c = t.cr.reduce(function (x, y) { return x + y.v; }, 0);
      t.d = d; t.c = c; t.net = d - c; return t;
    });
  }
  function tHTML(items, multi) {
    return tAccounts(items).map(function (t) {
      var acc = COA[t.a], inc = (t.net >= 0 ? "D" : "C") === acc.n, amt = Math.abs(t.net);
      function col(list) {
        return list.map(function (e) { return '<div class="je-te">' + (multi ? '<i>(' + (e.si + 1) + ')</i>' : "") + "<span>" + fmtNum(e.v) + "</span></div>"; }).join("");
      }
      return '<div class="je-t"><div class="je-th">' + esc(acc.name) + '<small>' + CLS[acc.cls] + "</small></div>" +
        '<div class="je-tb"><div class="je-tl">' + col(t.dr) + '</div><div class="je-tr">' + col(t.cr) + "</div></div>" +
        '<div class="je-tt"><span>' + (t.net >= 0 ? "Dr " : "Cr ") + fmtMoney(amt) + "</span><b>" + (inc ? "↑ increase" : "↓ decrease") + "</b></div></div>";
    }).join("");
  }

  /* ═══════════════ storage: mastery + spaced repetition ═══════════════ */
  var KEY = "te.je.v1";
  var ST = (function () {
    var o = {};
    try { o = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) {}
    o.v = 1; o.t = o.t || {}; o.sp = o.sp || {}; o.pref = o.pref || {}; o.day = o.day || {};
    return o;
  })();
  function save() { try { localStorage.setItem(KEY, JSON.stringify(ST)); } catch (e) {} }
  var INTERVAL = [0, 1, 2, 4, 8, 16, 32];
  function ymd(d) { d = d || new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
  function addDays(n) { var d = new Date(); d.setDate(d.getDate() + n); return ymd(d); }
  function stOf(tid) { return ST.t[tid] || { n: 0, ok: 0, box: 0, due: "", best: 0 }; }
  function level(tid) {
    var s = stOf(tid); if (!s.n) return 0;
    if (s.box >= 5) return 3; if (s.box >= 3) return 2; return 1;
  }
  var LV = ["New", "Learning", "Familiar", "Mastered"];
  function isDue(tid) { var s = stOf(tid); return s.n > 0 && s.due && s.due <= ymd(); }
  function record(tid, score, perfect, hints, ms) {
    var s = ST.t[tid] || { n: 0, ok: 0, box: 0, due: "", best: 0 };
    s.n++; if (perfect) s.ok++;
    if (perfect && !hints) s.box = Math.min(6, s.box + 1);
    else if (perfect) s.box = Math.max(s.box, 1);
    else if (score >= 0.5) s.box = Math.max(0, s.box - 1);
    else s.box = 0;
    s.due = addDays(perfect && !hints ? INTERVAL[s.box] : (score >= 0.5 ? 1 : 0));
    s.last = Math.round(ms / 1000);
    if (perfect && !hints && (!s.best || s.last < s.best)) s.best = s.last;
    ST.t[tid] = s;
    var d = ymd(); if (ST.day.d !== d) ST.day = { d: d, n: 0, ok: 0 };
    ST.day.n++; if (perfect) ST.day.ok++;
    save();
  }
  function poolFor(topic) {
    if (!topic || topic === "all") return DATA.tpls.map(function (t) { return t.id; });
    return TOPIC[topic] ? TOPIC[topic].ids.slice() : DATA.tpls.map(function (t) { return t.id; });
  }
  function pickNext(pool, avoid) {
    var cand = pool.filter(function (t) { return t !== avoid; }); if (!cand.length) cand = pool;
    var due = cand.filter(isDue).sort(function (a, b) { return stOf(a).due < stOf(b).due ? -1 : 1; });
    var fresh = cand.filter(function (t) { return !stOf(t).n; });
    var r = Math.random();
    if (due.length && (r < 0.7 || !fresh.length)) return due[0];
    if (fresh.length) return fresh[Math.floor(Math.random() * fresh.length)];
    cand.sort(function (a, b) { return stOf(a).box - stOf(b).box || (stOf(a).due < stOf(b).due ? -1 : 1); });
    return cand[Math.floor(Math.random() * Math.min(5, cand.length))];
  }

  /* ═══════════════ helpers ═══════════════ */
  function esc(t) { return String(t == null ? "" : t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function parseAmt(s) {
    s = String(s || "").replace(/[$,\s]/g, ""); if (!s) return 0;
    var n = Number(s); return isFinite(n) && n > 0 ? n : NaN;
  }
  function tmr(ms) { var s = Math.floor(ms / 1000); return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); }
  function newSeed() { return Math.floor(Math.random() * 2147483647) + 1; }
  var root = $("#je");

  /* ═══════════════ screens ═══════════════ */
  var S = { view: "home", topic: ST.pref.topic || "all", mode: ST.pref.mode || "practice", v: null, sub: false, hints: [], hintN: 0, t0: 0, res: null, sp: null, hist: [], tview: "ans", tid: null };
  var timerId = 0;
  function stopTimer() { if (timerId) { clearInterval(timerId); timerId = 0; } }
  function startTimer() {
    stopTimer(); S.t0 = Date.now();
    timerId = setInterval(function () {
      var el = $("#je-clock"); if (el) el.textContent = tmr(Date.now() - S.t0);
    }, 500);
  }
  function setView(v) { S.view = v; window.scrollTo(0, 0); render(); }

  function totals() {
    var m = 0, due = 0;
    DATA.tpls.forEach(function (t) { if (level(t.id) === 3) m++; if (isDue(t.id)) due++; });
    return { m: m, due: due, n: DATA.tpls.length, today: (ST.day.d === ymd() ? ST.day.n : 0) };
  }
  function topicStat(tp) {
    var m = 0, due = 0, seen = 0;
    tp.ids.forEach(function (id) { var l = level(id); if (l === 3) m++; if (l > 0) seen++; if (isDue(id)) due++; });
    return { m: m, due: due, seen: seen, n: tp.ids.length };
  }

  function homeHTML() {
    var T = totals();
    var h = '<header class="je-hd"><a class="je-back" href="index.html" aria-label="Back to home">←</a><h1>Journal Drill</h1></header>';
    h += '<div class="je-stats"><div><b>' + T.m + "/" + T.n + '</b><span>Mastered</span></div><div><b>' + T.due + '</b><span>Due</span></div><div><b>' + T.today + '</b><span>Today</span></div></div>';
    h += '<div class="je-sec"><h2>Mode</h2><div class="je-seg" role="group" aria-label="Mode">' +
      seg("practice", "Practice") + seg("speed", "Speed 5") + seg("review", "Review " + T.due) + "</div></div>";
    h += '<div class="je-sec"><h2>Topic</h2><div class="je-topics">' +
      topicCard("all", "All topics", T.n, T.m, T.due) +
      DATA.topics.map(function (tp) { var s = topicStat(tp); return topicCard(tp.id, tp.name, s.n, s.m, s.due, s.seen); }).join("") + "</div></div>";
    h += '<div class="je-go"><button type="button" class="btn block" id="je-start">' + (S.mode === "speed" ? "Start sprint" : S.mode === "review" ? "Start review" : "Start") + "</button></div>";
    var tp = TOPIC[S.topic];
    if (tp) {
      h += '<div class="je-sec"><h2>Types → ' + esc(tp.name) + "</h2><div class=\"je-types\">" +
        tp.ids.map(function (id) {
          var t = TPL[id], l = level(id);
          return '<button type="button" class="je-type" data-t="' + id + '"><span class="je-lv l' + l + '" title="' + LV[l] + '"></span><span class="tt">' + esc(t.title) + '</span><small>' + esc(t.asc) + (isDue(id) ? " → due" : "") + "</small></button>";
        }).join("") + "</div></div>";
    }
    return h;
  }
  function seg(k, label) { return '<button type="button" data-mode="' + k + '" aria-pressed="' + (S.mode === k) + '">' + label + "</button>"; }
  function topicCard(id, name, n, m, due, seen) {
    var pct = n ? Math.round(m / n * 100) : 0;
    return '<button type="button" class="je-tc" data-topic="' + id + '" aria-pressed="' + (S.topic === id) + '"><b>' + esc(name) + '</b><span>' + n + ' types' + (due ? " → " + due + " due" : "") +
      '</span><div class="bar"><i style="width:' + pct + '%"></i></div></button>';
  }

  /* ---- drill ---- */
  function rowHTML(k) {
    return '<div class="je-row" data-r>' +
      '<div class="je-a"><input class="je-acct" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="Account" aria-label="Account"><button type="button" class="je-rm" aria-label="Remove line" tabindex="-1">×</button></div>' +
      '<input class="je-amt je-d" type="text" inputmode="decimal" autocomplete="off" placeholder="Debit" aria-label="Debit">' +
      '<input class="je-amt je-c" type="text" inputmode="decimal" autocomplete="off" placeholder="Credit" aria-label="Credit">' +
      "</div>";
  }
  function setHTML(si) {
    var set = S.v.sets[si], n = Math.max(3, Math.min(6, set.lines.length + 1));
    var h = '<section class="je-set" data-si="' + si + '">';
    h += '<div class="je-sh"><span class="je-dt">' + esc(set.date) + "</span><span class=\"je-pr\">" + esc(set.prompt) + "</span></div>";
    h += '<div class="je-cols" aria-hidden="true"><span>Account</span><span>Debit</span><span>Credit</span></div>';
    h += '<div class="je-rows">'; for (var i = 0; i < n; i++) h += rowHTML(); h += "</div>";
    h += '<div class="je-foot"><button type="button" class="btn ghost sm" data-add>+ Line</button><span class="je-bal" aria-live="polite">Debit $0 | Credit $0</span>' +
      (S.mode === "speed" ? "" : '<button type="button" class="btn ghost sm" data-hint>Hint 1/3</button>') + "</div>";
    h += '<div class="je-hint" hidden></div></section>';
    return h;
  }
  function stonesHTML() {
    var h = '<div class="stones" aria-label="Progress">';
    if (S.sp) {
      for (var i = 0; i < S.sp.list.length; i++) {
        var r = S.sp.res[i]; h += '<i class="' + (i === S.sp.i ? "now" : r ? (r.perfect ? "ok" : "no") : "") + '"></i>';
      }
      h += '<span class="left">' + (S.sp.list.length - S.sp.i - (S.sub ? 1 : 0)) + " left</span>";
    } else {
      var last = S.hist.slice(-9);
      last.forEach(function (x) { h += '<i class="' + (x ? "ok" : "no") + '"></i>'; });
      h += '<i class="now"></i><span class="left">' + S.hist.length + " done</span>";
    }
    return h + "</div>";
  }
  function drillHTML() {
    var t = TPL[S.v.tid], tp = TOPIC[t.topic];
    var h = '<header class="je-hd"><button type="button" class="je-back" id="je-quit" aria-label="Back to topics">←</button><h1>' + esc(t.title) + '</h1><span class="je-clock num" id="je-clock">0:00</span></header>';
    h += '<div class="je-meta"><span class="chip">' + esc(tp.name) + '</span><span class="chip">' + esc(t.asc) + '</span><span class="chip">Level ' + t.lvl + "</span></div>";
    h += stonesHTML();
    h += '<div class="je-stmt"><p>' + esc(S.v.text) + "</p></div>";
    h += '<div id="je-sets">'; for (var i = 0; i < S.v.sets.length; i++) h += setHTML(i); h += "</div>";
    h += '<div id="je-after"></div>';
    h += '<div class="je-act" id="je-act"><button type="button" class="btn" id="je-check">Check</button><button type="button" class="btn ghost" id="je-skip">Skip</button></div>';
    return h;
  }
  function beginProblem(tid) {
    S.tid = tid; S.v = null;
    for (var k = 0; k < 20 && !S.v; k++) S.v = generate(TPL[tid], newSeed());
    S.sub = false; S.hints = S.v.sets.map(function () { return 0; }); S.hintN = 0; S.res = null; S.tview = "ans";
    S.view = "drill"; render(); startTimer();
    var first = $(".je-acct"); if (first && !("ontouchstart" in window)) first.focus();
  }

  /* ---- reading the entry table ---- */
  function readRows(setEl) {
    return $$(".je-row", setEl).map(function (row) {
      var ai = $(".je-acct", row), d = parseAmt($(".je-d", row).value), c = parseAmt($(".je-c", row).value);
      var id = ai.dataset.id || resolve(ai.value);
      return { a: id, tx: ai.value.trim(), d: isNaN(d) ? 0 : d, c: isNaN(c) ? 0 : c, bad: isNaN(d) || isNaN(c) };
    });
  }
  function updateBal(setEl) {
    var d = 0, c = 0;
    $$(".je-row", setEl).forEach(function (row) {
      var x = parseAmt($(".je-d", row).value), y = parseAmt($(".je-c", row).value);
      if (!isNaN(x)) d += x; if (!isNaN(y)) c += y;
      row.classList.toggle("cr", !!y && !x);
    });
    var el = $(".je-bal", setEl);
    if (!d && !c) { el.textContent = "Debit $0 | Credit $0"; el.className = "je-bal"; return; }
    if (Math.abs(d - c) < 0.005) { el.textContent = "Balanced " + fmtMoney(d); el.className = "je-bal ok"; return; }
    el.textContent = "Out of balance: Debit " + fmtMoney(d) + " | Credit " + fmtMoney(c) + " → diff " + fmtMoney(Math.abs(d - c));
    el.className = "je-bal off";
  }

  /* ---- account dropdown ---- */
  var dd = null, ddIn = null, ddSel = -1, ddItems = [];
  function ddClose() { if (dd) dd.hidden = true; ddIn = null; ddSel = -1; ddItems = []; }
  function ddOpen(input) {
    if (!dd) { dd = document.createElement("div"); dd.id = "je-dd"; dd.setAttribute("role", "listbox"); dd.hidden = true; document.body.appendChild(dd); }
    ddIn = input;
    var q = input.value, list = q.trim() ? search(q, 8) : [];
    ddItems = list; ddSel = list.length ? 0 : -1;
    if (!list.length) { dd.hidden = true; return; }
    dd.innerHTML = list.map(function (x, i) {
      return '<div role="option" class="je-opt' + (i === 0 ? " on" : "") + '" data-i="' + i + '">' + esc(x.name) + (x.alias ? "<small>" + esc(x.alias) + "</small>" : "") + "</div>";
    }).join("");
    var r = input.getBoundingClientRect();
    dd.style.left = (r.left + window.scrollX) + "px";
    dd.style.top = (r.bottom + window.scrollY + 2) + "px";
    dd.style.width = Math.max(r.width, 220) + "px";
    dd.hidden = false;
  }
  function ddPick(i) {
    var x = ddItems[i], input = ddIn; if (!x || !input) return;
    input.value = x.name; input.dataset.id = x.id; ddClose();
    var row = input.closest(".je-row"), d = $(".je-d", row);
    if (d) d.focus();
  }
  function ddMove(dir) {
    if (dd.hidden || !ddItems.length) return;
    ddSel = (ddSel + dir + ddItems.length) % ddItems.length;
    $$(".je-opt", dd).forEach(function (o, i) { o.classList.toggle("on", i === ddSel); });
  }

  /* ---- results ---- */
  var STAT = {
    ok: ["Correct", "ok"], amount: ["Amount", "no"], flip: ["Reversed", "no"], acct: ["Account", "no"], extra: ["Extra", "no"], unknown: ["Unknown", "no"], noamt: ["No amount", "no"]
  };
  function resultRow(u, v, si) {
    var st = STAT[u.status], nm = u.a ? COA[u.a].name : (u.tx || "(blank)");
    var acct = esc(nm), amt = u.s ? fmtNum(u.v) : "", side = u.s;
    if (u.status === "acct" && u.c) acct = "<s>" + esc(nm) + "</s> → " + esc(COA[u.c.a].name);
    if (u.status === "amount" && u.c) amt = "<s>" + fmtNum(u.v) + "</s> → " + fmtNum(u.c.v);
    var sideTxt = side ? (side === "D" ? "Debit" : "Credit") : "";
    if (u.status === "flip" && u.c) sideTxt = "<s>" + sideTxt + "</s> → " + (u.c.s === "D" ? "Debit" : "Credit");
    var msg = u.msg || u.note || "";
    return '<div class="je-rr ' + st[1] + " " + u.status + '"><div class="l1"><span class="tag">' + st[0] + '</span><span class="ac' + (side === "C" ? " cr" : "") + '">' + acct + '</span></div>' +
      '<div class="l2"><span>' + sideTxt + '</span><b class="num">' + (amt ? "$" + amt : "") + "</b></div>" + (msg ? '<p class="msg">' + esc(msg) + "</p>" : "") + "</div>";
  }
  function answerTable(set, si, showWhy) {
    var dr = 0, cr = 0;
    var body = set.lines.map(function (l) {
      if (l.s === "D") dr += l.v; else cr += l.v;
      return '<tr class="' + (l.s === "C" ? "cr" : "") + '"><td>' + esc(COA[l.a].name) + '</td><td class="r num">' + (l.s === "D" ? fmtNum(l.v) : "") + '</td><td class="r num">' + (l.s === "C" ? fmtNum(l.v) : "") + "</td></tr>" +
        (showWhy ? '<tr class="why"><td colspan="3">' + esc(l.why) + "</td></tr>" : "");
    }).join("");
    return '<div class="tblwrap"><table class="tbl je-ans"><thead><tr><th>Account</th><th class="r">Debit</th><th class="r">Credit</th></tr></thead><tbody>' + body +
      '<tr class="tot"><td>Total</td><td class="r num">' + fmtNum(dr) + '</td><td class="r num">' + fmtNum(cr) + "</td></tr></tbody></table></div>";
  }
  function showResults() {
    var v = S.v, res = [], allRows = [];
    $$(".je-set").forEach(function (setEl, si) {
      var rows = readRows(setEl); allRows.push(rows);
      var r = grade(v, si, rows); res.push(r);
      var h = '<div class="je-sh"><span class="je-dt">' + esc(v.sets[si].date) + '</span><span class="je-pr">' + esc(v.sets[si].prompt) + "</span>" +
        '<span class="je-sc ' + (r.perfect ? "ok" : "no") + '">' + Math.round(r.score * 100) + "%</span></div>";
      if (r.allFlip) h += '<p class="je-flipall">Every line is reversed: debits and credits are swapped.</p>';
      h += '<div class="je-rrs">';
      if (!r.lines.length) h += '<div class="je-rr no"><div class="l1"><span class="tag">Blank</span><span class="ac">No entry</span></div></div>';
      r.lines.forEach(function (u) { h += resultRow(u, v, si); });
      r.missing.forEach(function (m) {
        h += '<div class="je-rr no miss"><div class="l1"><span class="tag">Missing</span><span class="ac' + (m.c.s === "C" ? " cr" : "") + '">' + esc(COA[m.c.a].name) + '</span></div><div class="l2"><span>' + (m.c.s === "D" ? "Debit" : "Credit") + '</span><b class="num">$' + fmtNum(m.c.v) + '</b></div><p class="msg">' + esc(m.msg) + "</p></div>";
      });
      h += "</div>";
      h += '<h3 class="je-h3">Correct entry</h3>' + answerTable(v.sets[si], si, false);
      h += '<div class="je-why" hidden>' + answerTable(v.sets[si], si, true) + "</div>";
      setEl.innerHTML = h; setEl.classList.add("done");
    });
    S.res = res; S.rows = allRows;
    var pts = 0, max = 0, perfect = true;
    res.forEach(function (r) { pts += r.score * r.n; max += r.n; if (!r.perfect) perfect = false; });
    var score = max ? pts / max : 0, ms = Date.now() - S.t0;
    stopTimer();
    record(S.tid, score, perfect, S.hintN, ms);
    S.hist.push(perfect);
    if (S.sp) { S.sp.res[S.sp.i] = { tid: S.tid, perfect: perfect, score: score, ms: ms, hints: 0 }; }
    S.sub = true;
    var t = TPL[S.tid], ac = $("#je-after");
    ac.innerHTML = '<div class="je-sum ' + (perfect ? "ok" : "no") + '"><b>' + (perfect ? "Correct" : "Score " + Math.round(score * 100) + "%") + '</b><span>' + tmr(ms) + (S.hintN ? " → " + S.hintN + " hint" + (S.hintN > 1 ? "s" : "") : "") + '</span></div>' +
      '<div class="je-row2"><button type="button" class="btn ghost sm" id="je-why-b" aria-expanded="false">Show explanation</button><button type="button" class="btn ghost sm" id="je-t-b" aria-expanded="false">T-accounts</button></div>' +
      '<div id="je-expl" hidden>' + (v.key ? '<p class="je-key">' + esc(v.key) + "</p>" : "") + '<p class="je-asc">' + esc(t.asc) + "</p></div>" +
      '<div id="je-tpanel" hidden></div>';
    var act = $("#je-act");
    if (S.sp) {
      var last = S.sp.i >= S.sp.list.length - 1;
      act.innerHTML = '<button type="button" class="btn" id="je-next">' + (last ? "Finish" : "Next") + "</button>";
    } else {
      act.innerHTML = '<button type="button" class="btn" id="je-next">Next type</button><button type="button" class="btn ghost" id="je-again">New numbers</button>';
    }
    var st = $(".stones"); if (st) st.outerHTML = stonesHTML();
    $("#je-after").scrollIntoView({ behavior: "smooth", block: "start" });
  }
  function tPanel(kind) {
    var v = S.v, items = [];
    if (kind === "ans") v.sets.forEach(function (s, si) { s.lines.forEach(function (l) { items.push({ a: l.a, s: l.s, v: l.v, si: si }); }); });
    else S.res.forEach(function (r, si) { r.lines.forEach(function (u) { if (u.a && u.s) items.push({ a: u.a, s: u.s, v: u.v, si: si }); }); });
    var multi = v.sets.length > 1;
    return '<div class="je-seg2"><button type="button" data-tv="ans" aria-pressed="' + (kind === "ans") + '">Answer</button><button type="button" data-tv="you" aria-pressed="' + (kind === "you") + '">Yours</button></div>' +
      '<div class="je-ts">' + (items.length ? tHTML(items, multi) : '<p class="muted">No lines entered.</p>') + "</div>";
  }

  /* ---- hints ---- */
  function giveHint(si, btn) {
    if (S.sub) return;
    var lv = S.hints[si]; if (lv >= 3) return;
    lv++; S.hints[si] = lv; S.hintN++;
    var set = S.v.sets[si], el = $('.je-set[data-si="' + si + '"] .je-hint');
    var out = [];
    for (var k = 1; k <= lv; k++) {
      var x = hintLines(set, k);
      out.push('<div class="hl"><b>' + k + "</b>" + (Array.isArray(x) ? "<ul>" + x.map(function (s) { return "<li>" + esc(s) + "</li>"; }).join("") + "</ul>" : "<p>" + esc(x) + "</p>") + "</div>");
    }
    el.innerHTML = out.join(""); el.hidden = false;
    btn.textContent = lv >= 3 ? "Hint 3/3" : "Hint " + (lv + 1) + "/3";
    if (lv >= 3) btn.disabled = true;
  }

  /* ---- speed sprint ---- */
  function startSprint() {
    var pool = poolFor(S.topic), list = [];
    var tmp = pool.slice();
    while (list.length < 5 && tmp.length) {
      var id = pickNext(tmp, list[list.length - 1]);
      list.push(id); tmp.splice(tmp.indexOf(id), 1);
    }
    S.sp = { list: list, i: 0, res: [], t0: Date.now() };
    S.hist = [];
    beginProblem(list[0]);
  }
  function sprintDone() {
    var sp = S.sp, ok = sp.res.filter(function (r) { return r && r.perfect; }).length;
    var total = Date.now() - sp.t0, key = "n" + sp.list.length, best = ST.sp[key];
    var isBest = ok === sp.list.length && (!best || total < best.ms);
    if (isBest) { ST.sp[key] = { ms: total, at: ymd() }; save(); }
    S.spSum = { ok: ok, n: sp.list.length, ms: total, res: sp.res, best: ST.sp[key], isBest: isBest };
    S.sp = null; S.view = "sprint"; stopTimer(); render();
  }
  function sprintHTML() {
    var s = S.spSum;
    var h = '<header class="je-hd"><button type="button" class="je-back" id="je-quit" aria-label="Back to topics">←</button><h1>Sprint result</h1></header>';
    h += '<div class="je-stats"><div><b>' + s.ok + "/" + s.n + "</b><span>Correct</span></div><div><b>" + tmr(s.ms) + "</b><span>Total</span></div><div><b>" + tmr(s.ms / s.n) + "</b><span>Per entry</span></div></div>";
    h += '<p class="je-bestline">' + (s.isBest ? "New best: " + tmr(s.ms) : (s.best ? "Best: " + tmr(s.best.ms) + " (all correct)" : "Best: none yet, needs all correct")) + "</p>";
    h += '<div class="je-types">' + s.res.map(function (r) {
      var t = TPL[r.tid];
      return '<div class="je-type static"><span class="je-lv ' + (r.perfect ? "l3" : "bad") + '"></span><span class="tt">' + esc(t.title) + "</span><small>" + tmr(r.ms) + (r.perfect ? "" : " → " + Math.round(r.score * 100) + "%") + "</small></div>";
    }).join("") + "</div>";
    h += '<div class="je-act"><button type="button" class="btn" id="je-more">Sprint again</button><button type="button" class="btn ghost" id="je-quit2">Topics</button></div>';
    return h;
  }

  function render() {
    ddClose();
    if (S.view === "home") root.innerHTML = homeHTML();
    else if (S.view === "drill") root.innerHTML = drillHTML();
    else if (S.view === "sprint") root.innerHTML = sprintHTML();
  }

  /* ═══════════════ events ═══════════════ */
  root.addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    if (b.dataset.mode) { S.mode = b.dataset.mode; ST.pref.mode = S.mode; save(); render(); return; }
    if (b.dataset.topic) { S.topic = b.dataset.topic; ST.pref.topic = S.topic; save(); render(); return; }
    if (b.dataset.t && b.classList.contains("je-type")) { S.sp = null; S.hist = []; beginProblem(b.dataset.t); return; }
    if (b.id === "je-start") {
      if (S.mode === "speed") return startSprint();
      S.sp = null; S.hist = [];
      var pool = S.mode === "review" ? poolFor(S.topic).filter(isDue) : poolFor(S.topic);
      if (!pool.length) { b.textContent = "Nothing due"; return; }
      return beginProblem(pickNext(pool));
    }
    if (b.id === "je-quit" || b.id === "je-quit2") { stopTimer(); S.sp = null; S.view = "home"; render(); return; }
    if (b.hasAttribute("data-add")) {
      var rows = b.closest(".je-set").querySelector(".je-rows"); rows.insertAdjacentHTML("beforeend", rowHTML());
      var last = rows.lastElementChild; $(".je-acct", last).focus(); return;
    }
    if (b.classList.contains("je-rm")) {
      var row = b.closest(".je-row"), rs = row.parentNode;
      if (rs.children.length > 2) { row.remove(); updateBal(rs.closest(".je-set")); }
      else { $$("input", row).forEach(function (i) { i.value = ""; delete i.dataset.id; }); updateBal(rs.closest(".je-set")); }
      return;
    }
    if (b.hasAttribute("data-hint")) return giveHint(+b.closest(".je-set").dataset.si, b);
    if (b.id === "je-check") return showResults();
    if (b.id === "je-skip") {
      if (S.sp) { S.sp.res[S.sp.i] = { tid: S.tid, perfect: false, score: 0, ms: Date.now() - S.t0 }; return nextInSprint(); }
      return beginProblem(pickNext(poolFor(S.topic), S.tid));
    }
    if (b.id === "je-next") {
      if (S.sp) return nextInSprint();
      var pl = S.mode === "review" ? poolFor(S.topic).filter(isDue) : poolFor(S.topic);
      if (!pl.length) { S.view = "home"; render(); return; }
      return beginProblem(pickNext(pl, S.tid));
    }
    if (b.id === "je-again") return beginProblem(S.tid);
    if (b.id === "je-more") return startSprint();
    if (b.id === "je-why-b") {
      var open = b.getAttribute("aria-expanded") !== "true";
      b.setAttribute("aria-expanded", open); b.textContent = open ? "Hide explanation" : "Show explanation";
      $("#je-expl").hidden = !open; $$(".je-why").forEach(function (w) { w.hidden = !open; });
      $$(".je-set.done > .tblwrap").forEach(function (w) { w.hidden = open; }); return;
    }
    if (b.id === "je-t-b") {
      var o2 = b.getAttribute("aria-expanded") !== "true";
      b.setAttribute("aria-expanded", o2); var p = $("#je-tpanel"); p.hidden = !o2;
      if (o2) { S.tview = "ans"; p.innerHTML = tPanel("ans"); }
      return;
    }
    if (b.dataset.tv) { S.tview = b.dataset.tv; $("#je-tpanel").innerHTML = tPanel(S.tview); return; }
  });
  function nextInSprint() {
    S.sp.i++;
    if (S.sp.i >= S.sp.list.length) return sprintDone();
    beginProblem(S.sp.list[S.sp.i]);
  }
  root.addEventListener("input", function (e) {
    var t = e.target;
    if (t.classList.contains("je-acct")) { delete t.dataset.id; ddOpen(t); return; }
    if (t.classList.contains("je-amt")) {
      var row = t.closest(".je-row"), other = t.classList.contains("je-d") ? $(".je-c", row) : $(".je-d", row);
      if (t.value && other.value) other.value = "";
      updateBal(t.closest(".je-set"));
    }
  });
  root.addEventListener("focusin", function (e) { if (e.target.classList.contains("je-acct") && e.target.value) ddOpen(e.target); });
  root.addEventListener("focusout", function (e) {
    var t = e.target;
    if (t.classList.contains("je-acct")) {
      setTimeout(function () { if (ddIn === t) ddClose(); }, 120);
      if (!t.dataset.id) { var id = resolve(t.value); if (id) { t.dataset.id = id; t.value = COA[id].name; } }
    } else if (t.classList.contains("je-amt")) {
      var n = parseAmt(t.value); if (n && !isNaN(n)) t.value = n.toLocaleString("en-US", { maximumFractionDigits: 2 });
    }
  });
  root.addEventListener("keydown", function (e) {
    var t = e.target;
    if (t.classList.contains("je-acct") && dd && !dd.hidden && ddIn === t) {
      if (e.key === "ArrowDown") { e.preventDefault(); ddMove(1); return; }
      if (e.key === "ArrowUp") { e.preventDefault(); ddMove(-1); return; }
      if (e.key === "Enter") { e.preventDefault(); ddPick(ddSel); return; }
      if (e.key === "Escape") { ddClose(); return; }
    }
    if (t.classList.contains("je-amt") && e.key === "Enter") {
      e.preventDefault();
      var row = t.closest(".je-row"), next = row.nextElementSibling;
      if (!next) { row.parentNode.insertAdjacentHTML("beforeend", rowHTML()); next = row.nextElementSibling; }
      $(".je-acct", next).focus();
    }
  });
  document.addEventListener("pointerdown", function (e) {
    var o = e.target.closest && e.target.closest(".je-opt");
    if (o && dd && dd.contains(o)) { e.preventDefault(); ddPick(+o.dataset.i); }
  });
  window.addEventListener("scroll", function () { if (ddIn && dd && !dd.hidden) { var r = ddIn.getBoundingClientRect(); dd.style.top = (r.bottom + window.scrollY + 2) + "px"; } }, { passive: true });

  /* test hooks (also used by tools/e2e_je.py) */
  window.JE = { generate: generate, baseEnv: baseEnv, realize: realize, grade: grade, search: search, resolve: resolve, COA: COA, TPL: TPL, data: DATA, mulberry32: mulberry32, state: S, store: ST };

  /* deep link: je.html?t=FAR-BOND-06 or ?topic=leases */
  var q = new URLSearchParams(location.search);
  if (q.get("topic") && TOPIC[q.get("topic")]) S.topic = q.get("topic");
  if (q.get("t") && TPL[q.get("t")]) { S.topic = TPL[q.get("t")].topic; beginProblem(q.get("t")); }
  else render();
})();
