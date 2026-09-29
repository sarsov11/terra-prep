/* TBS (task-based simulation) engine + screen.
   Engine (window.TBSEngine): safe formula evaluator, render/variant, grading with carry-forward (ECF), citation normalizer.
   It mirrors tools/src/TBS/tbs_lib.py; tools/test_tbs_variants.py checks both against each other.
   Screen: runs only when the page has #tbs-app (tbs.html). Storage: "te.tbs.v1" (prefix "te." as in js/store.js + "tbs."). */
(function () {
  "use strict";

  /* ───────────── engine ───────────── */
  function rnd(x) { return Math.floor(x + 0.5); }
  var SINGLE = [[12400, .10], [50400, .12], [105700, .22], [201775, .24], [256225, .32], [640600, .35], [null, .37]];
  function tax(ti) {
    ti = Math.max(0, ti);
    var t = 0, lo = 0;
    for (var i = 0; i < SINGLE.length; i++) {
      var top = SINGLE[i][0], r = SINGLE[i][1];
      var hi = top === null ? ti : Math.min(ti, top);
      if (hi > lo) t += (hi - lo) * r;
      if (top === null || ti <= top) break;
      lo = top;
    }
    return t;
  }
  function se_tax(net, base) {
    if (base === undefined) base = 184500;
    var e = net * 0.9235;
    return 0.124 * Math.min(e, base) + 0.029 * e;
  }
  function dual_basis(price, gain_basis, loss_basis) {
    if (price > gain_basis) return price - gain_basis;
    if (price < loss_basis) return price - loss_basis;
    return 0;
  }
  function ltcg_tax(ordinary_ti, gain, zero_top, fifteen_top) {
    var lo = ordinary_ti, hi = ordinary_ti + gain;
    var f = Math.max(0, Math.min(hi, fifteen_top) - Math.max(lo, zero_top));
    var t = Math.max(0, hi - Math.max(lo, fifteen_top));
    return f * 0.15 + t * 0.20;
  }
  var FN = { rnd: rnd, min: Math.min, max: Math.max, abs: Math.abs, tax_s: tax, se_tax: se_tax, dual_basis: dual_basis, ltcg_tax: ltcg_tax };

  /* Formula parser: numbers, names, + - * / // % **, comparisons, and/or/not, calls to FN only. No eval(). */
  var cache = {};
  function tokenize(s) {
    var out = [], re = /\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)|([A-Za-z_][A-Za-z_0-9]*)|(\*\*|\/\/|<=|>=|==|!=|[-+*\/%(),<>]))/y, m, pos = 0;
    s = String(s);
    while (pos < s.length) {
      re.lastIndex = pos;
      m = re.exec(s);
      if (!m) { if (/^\s*$/.test(s.slice(pos))) break; throw new Error("bad formula: " + s); }
      pos = re.lastIndex;
      if (m[1] !== undefined) out.push({ t: "n", v: parseFloat(m[1]) });
      else if (m[2] !== undefined) out.push({ t: "i", v: m[2] });
      else out.push({ t: "o", v: m[3] });
    }
    return out;
  }
  function compile(src) {
    if (cache[src]) return cache[src];
    var tk = tokenize(src), p = 0;
    function peek() { return tk[p]; }
    function isOp(v) { var t = tk[p]; return t && t.t === "o" && t.v === v; }
    function isKw(v) { var t = tk[p]; return t && t.t === "i" && t.v === v; }
    function orE() { var l = andE(); while (isKw("or")) { p++; var r = andE(); l = (function (a, b) { return function (n) { return a(n) || b(n); }; })(l, r); } return l; }
    function andE() { var l = notE(); while (isKw("and")) { p++; var r = notE(); l = (function (a, b) { return function (n) { return a(n) && b(n); }; })(l, r); } return l; }
    function notE() { if (isKw("not")) { p++; var e = notE(); return function (n) { return !e(n); }; } return cmpE(); }
    function cmpE() {
      var l = addE(), t = peek();
      while (t && t.t === "o" && (t.v === "<" || t.v === ">" || t.v === "<=" || t.v === ">=" || t.v === "==" || t.v === "!=")) {
        p++;
        var r = addE(), op = t.v;
        l = (function (a, b, o) {
          return function (n) { var x = a(n), y = b(n); return o === "<" ? x < y : o === ">" ? x > y : o === "<=" ? x <= y : o === ">=" ? x >= y : o === "==" ? x === y : x !== y; };
        })(l, r, op);
        t = peek();
      }
      return l;
    }
    function addE() {
      var l = mulE();
      while (isOp("+") || isOp("-")) {
        var o = tk[p++].v, r = mulE();
        l = (function (a, b, o2) { return o2 === "+" ? function (n) { return a(n) + b(n); } : function (n) { return a(n) - b(n); }; })(l, r, o);
      }
      return l;
    }
    function mulE() {
      var l = unE();
      while (isOp("*") || isOp("/") || isOp("//") || isOp("%")) {
        var o = tk[p++].v, r = unE();
        l = (function (a, b, o2) {
          return function (n) {
            var x = a(n), y = b(n);
            return o2 === "*" ? x * y : o2 === "/" ? x / y : o2 === "//" ? Math.floor(x / y) : x - y * Math.floor(x / y);
          };
        })(l, r, o);
      }
      return l;
    }
    function unE() {
      if (isOp("-")) { p++; var e = unE(); return function (n) { return -e(n); }; }
      if (isOp("+")) { p++; return unE(); }
      return powE();
    }
    function powE() {
      var b = atom();
      if (isOp("**")) { p++; var e = unE(); return function (n) { return Math.pow(b(n), e(n)); }; }
      return b;
    }
    function atom() {
      var t = tk[p++];
      if (!t) throw new Error("unexpected end: " + src);
      if (t.t === "n") { var v = t.v; return function () { return v; }; }
      if (t.t === "o" && t.v === "(") { var e = orE(); if (!isOp(")")) throw new Error("missing ) in " + src); p++; return e; }
      if (t.t === "i") {
        var name = t.v;
        if (isOp("(")) {
          p++;
          var args = [];
          if (!isOp(")")) { args.push(orE()); while (isOp(",")) { p++; args.push(orE()); } }
          if (!isOp(")")) throw new Error("missing ) in " + src);
          p++;
          if (!Object.prototype.hasOwnProperty.call(FN, name)) throw new Error("function not allowed: " + name);
          var f = FN[name];
          return function (n) { return f.apply(null, args.map(function (a) { return a(n); })); };
        }
        if (name === "True") return function () { return true; };
        if (name === "False") return function () { return false; };
        return function (n) {
          if (!Object.prototype.hasOwnProperty.call(n, name)) throw new Error("unknown name " + name + " in " + src);
          return n[name];
        };
      }
      throw new Error("syntax error in " + src);
    }
    var fn = orE();
    if (p < tk.length) throw new Error("trailing tokens in " + src);
    cache[src] = fn;
    return fn;
  }
  function ev(expr, ns) { return compile(expr)(ns); }

  function buildNs(params, derived) {
    var ns = {}, k;
    for (k in params) ns[k] = params[k];
    (derived || []).forEach(function (d) { ns[d[0]] = ev(d[1], ns); });
    return ns;
  }
  function solve(item, params) {
    var ns = buildNs(params || item.params, item.derived), vals = {};
    item.cells.forEach(function (c) {
      if (c.kind === "number") {
        var v = ev(c.expr, ns);
        v = c.fmt === "%dec" ? v : rnd(v);
        vals[c.id] = v; ns[c.id] = v;
      }
    });
    return { ns: ns, vals: vals };
  }
  function group(s) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  function fmtVal(v, comma) {
    if (!comma) return String(v);
    var neg = v < 0, s = String(Math.abs(v)), i = s.indexOf(".");
    var ip = i < 0 ? s : s.slice(0, i), fp = i < 0 ? "" : s.slice(i);
    return (neg ? "-" : "") + group(ip) + fp;
  }
  function fill(s, ns) {
    if (typeof s === "string") {
      return s.replace(/\{([A-Za-z_][A-Za-z_0-9]*)(:,)?\}/g, function (m, name, c) {
        if (!Object.prototype.hasOwnProperty.call(ns, name)) throw new Error("missing " + name);
        return fmtVal(ns[name], !!c);
      });
    }
    if (Array.isArray(s)) return s.map(function (x) { return fill(x, ns); });
    if (s && typeof s === "object") { var o = {}; for (var k in s) o[k] = fill(s[k], ns); return o; }
    return s;
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function shuffle(arr, rng) {
    for (var i = arr.length - 1; i > 0; i--) { var j = Math.floor(rng() * (i + 1)), t = arr[i]; arr[i] = arr[j]; arr[j] = t; }
    return arr;
  }
  function uniq(a) { var s = {}; return a.filter(function (x) { return s[x] ? false : (s[x] = 1); }).sort(); }
  /* Fill a template with params. seed 0/undefined + base params keeps the original dropdown order (opts0). */
  function render(item, params, seed) {
    var sv = solve(item, params), ns = sv.ns;
    var out = {
      id: item.id, area: item.area, format: item.format, difficulty: item.difficulty, est_minutes: item.est_minutes,
      testable_from: item.testable_from, law_note: item.law_note, cite: item.cite, blueprint: item.blueprint,
      params: params, derived: item.derived, title: fill(item.title, ns), scenario: fill(item.scenario, ns), task: fill(item.task, ns), exhibits: fill(item.exhibits, ns), cells: []
    };
    var rng = seed ? mulberry32((hash(item.id) + seed * 2654435761) >>> 0) : null;
    item.cells.forEach(function (c) {
      var o = { id: c.id, kind: c.kind, label: fill(c.label, ns), why: fill(c.why, ns), steps: fill(c.steps || [], ns), hints: fill(c.hints || [], ns),
        link: c.link || "", cite: c.cite || "", points: c.points || 1 };
      if (c.kind === "number") {
        o.answer = sv.vals[c.id]; o.tol = c.tol; o.fmt = c.fmt; o.ecf = !!c.ecf; o.expr = c.expr;
        o.deps = uniq(c.expr.match(/\bc\d+\b/g) || []);
        o.traps = (c.traps || []).map(function (t) { return { expr: t.expr, value: rnd(ev(t.expr, ns)), msg: fill(t.msg, ns) }; });
      } else if (c.kind === "dropdown") {
        o.options = fill(c.options, ns); o.answer = fill(c.answer, ns);
        o.wrong = {};
        for (var k in (c.wrong_msgs || {})) o.wrong[fill(k, ns)] = fill(c.wrong_msgs[k], ns);
        if (rng) shuffle(o.options, rng);
        else if (c.opts0 && sameParams(params, item.params)) o.options = fill(c.opts0, ns);
      } else {
        o.ask = c.ask; o.accept = c.accept; o.partial = c.partial || [];
      }
      out.cells.push(o);
    });
    return out;
  }
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function sameParams(a, b) { for (var k in b) if (a[k] !== b[k]) return false; return true; }
  function pickParams(item, seed) {
    var rng = mulberry32((hash(item.id) ^ Math.imul(seed, 2246822519)) >>> 0);
    for (var n = 0; n < 200; n++) {
      var p = {}, k;
      for (k in item.params) p[k] = item.params[k];
      for (k in item.vary) { var ch = item.vary[k]; p[k] = ch[Math.floor(rng() * ch.length)]; }
      var ns = buildNs(p, item.derived);
      if (item.guards.every(function (g) { return !!ev(g, ns); })) return p;
    }
    throw new Error("guards unsatisfiable " + item.id);
  }
  function build(item, seed) {
    if (!seed || !Object.keys(item.vary || {}).length) return render(item, item.params, 0);
    return render(item, pickParams(item, seed), seed);
  }

  /* number entry: "$1,234", "(5,000)", "-5000", "−5000" */
  function parseNum(s) {
    if (typeof s === "number") return s;
    s = String(s == null ? "" : s).trim().replace(/[\$,\s]/g, "").replace(/−/g, "-");
    var neg = /^\(.*\)$/.test(s);
    if (neg) s = s.slice(1, -1);
    if (!/^[-+]?(\d+\.?\d*|\.\d+)$/.test(s)) return NaN;
    var v = parseFloat(s);
    return neg ? -v : v;
  }
  function normCite(s) {
    s = String(s).toLowerCase().trim();
    s = s.replace(/§/g, " ");
    s = s.replace(/internal revenue code|i\.?r\.?c\.?|u\.?s\.?c\.?|26 usc|section|sec\.?|treas\.? ?reg\.?|reg\.?|circular 230|31 ?c\.?f\.?r\.?|26 ?c\.?f\.?r\.?|part 10|title 26|title 31/g, " ");
    s = s.replace(/\b(26|31)\b(?=\s+\d)/g, " ");
    s = s.replace(/[\s.,;]+$/, "");
    s = s.replace(/\s+/g, "");
    return s;
  }
  /* Grade one cell. entries: {cid: raw input}. Returns {credit, kind: ok|ecf|half|wrong|blank, msg, entry}.
     ECF: recompute the formula with the learner's entries for every number cell (others keep the correct value). */
  function gradeCell(r, cell, entries, ecfCredit) {
    if (ecfCredit === undefined) ecfCredit = 0.5;
    var e = entries[cell.id];
    if (e === undefined || e === null || String(e).trim() === "") return { credit: 0, kind: "blank", msg: "" };
    if (cell.kind === "dropdown") {
      if (e === cell.answer) return { credit: 1, kind: "ok" };
      return { credit: 0, kind: "wrong", msg: cell.wrong[e] || "" };
    }
    if (cell.kind === "citation") {
      var n = normCite(e);
      if (cell.accept.some(function (a) { return a.toLowerCase() === n; })) return { credit: 1, kind: "ok" };
      if (cell.partial.some(function (a) { return a.toLowerCase() === n; })) return { credit: 0.5, kind: "half", msg: "" };
      return { credit: 0, kind: "wrong", msg: "" };
    }
    var v = parseNum(e);
    if (isNaN(v)) return { credit: 0, kind: "wrong", msg: "" };
    if (Math.abs(v - cell.answer) <= cell.tol) return { credit: 1, kind: "ok" };
    var trap = "";
    cell.traps.forEach(function (t) { if (!trap && Math.abs(v - t.value) <= cell.tol) trap = t.msg; });
    if (cell.ecf && cell.deps.length) {
      var loc = buildNs(r.params, r.derived);
      r.cells.forEach(function (c) {
        if (c.kind !== "number") return;
        var pv = e0(entries[c.id]);
        loc[c.id] = isNaN(pv) ? c.answer : pv;
      });
      var alt = null;
      try { alt = ev(cell.expr, loc); } catch (x) { alt = null; }
      if (alt !== null && Math.abs(v - alt) <= cell.tol) return { credit: ecfCredit, kind: "ecf", msg: trap };
    }
    return { credit: 0, kind: "wrong", msg: trap };
  }
  function e0(x) { return x === undefined || x === null || String(x).trim() === "" ? NaN : parseNum(x); }

  window.TBSEngine = { rnd: rnd, ev: ev, buildNs: buildNs, solve: solve, render: render, build: build, pickParams: pickParams, gradeCell: gradeCell,
    normCite: normCite, parseNum: parseNum, fill: fill };

  /* ───────────── screen ───────────── */
  var root = document.getElementById("tbs-app");
  if (!root) return;
  var DATA = window.TBS_DATA || { items: [] };
  var ITEMS = DATA.items, BYID = {};
  ITEMS.forEach(function (t) { BYID[t.id] = t; });
  var KEY = "te.tbs.v1", EXAM_SECS = 18 * 60, TODAY = new Date().toISOString().slice(0, 10);
  var FMT = { numeric_table: "Numeric table", document_review: "Document review", research: "Research", dropdown_judgment: "Judgment" };
  var AREAS = ["I", "II", "III", "IV", "V"];

  function read() { try { var v = localStorage.getItem(KEY); return v ? JSON.parse(v) : null; } catch (e) { return null; } }
  var S = read() || {};
  S.pref = S.pref || { mode: "practice", area: "", fmt: "", diff: "" };
  S.items = S.items || {};
  S.live = S.live || {};
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function $(sel, el) { return (el || root).querySelector(sel); }
  function $$(sel, el) { return Array.prototype.slice.call((el || root).querySelectorAll(sel)); }
  function money(v, fmt) { return (fmt === "n" ? "" : v < 0 ? "-$" : "$") + fmtVal(Math.abs(v), true); }
  function mmss(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); }
  function dots(n) { return "●".repeat(n) + "○".repeat(3 - n); }
  function num(n) { return Math.round(n * 10) / 10; }
  var timerId = null, toastT = null;
  function toast(msg) {
    var t = $("#toast"); if (!t) return;
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastT); toastT = setTimeout(function () { t.hidden = true; }, 1600);
  }
  function stopTimer() { if (timerId) { clearInterval(timerId); timerId = null; } }

  /* ── list ── */
  function listView() {
    stopTimer();
    document.title = "TBS";
    var P = S.pref;
    function opts(arr, cur, all) { return '<option value="">' + all + "</option>" + arr.map(function (a) { return '<option value="' + esc(a[0]) + '"' + (String(cur) === String(a[0]) ? " selected" : "") + ">" + esc(a[1]) + "</option>"; }).join(""); }
    var rows = ITEMS.filter(function (t) {
      return (!P.area || t.area === P.area) && (!P.fmt || t.format === P.fmt) && (!P.diff || String(t.difficulty) === String(P.diff));
    });
    var done = ITEMS.filter(function (t) { return S.items[t.id] && S.items[t.id].done; }).length;
    var pcts = ITEMS.map(function (t) { return S.items[t.id] && S.items[t.id].done ? S.items[t.id].best : null; }).filter(function (x) { return x !== null; });
    var avg = pcts.length ? Math.round(pcts.reduce(function (a, b) { return a + b; }, 0) / pcts.length) : null;
    root.innerHTML =
      '<div class="tb-wrap"><div class="tb-bar"><a class="back" href="index.html">← Home</a><h1>TBS</h1>' +
      '<div class="tb-seg" role="group" aria-label="Mode"><button data-mode="practice" aria-pressed="' + (P.mode === "practice") + '">Practice</button><button data-mode="exam" aria-pressed="' + (P.mode === "exam") + '">Exam</button></div></div>' +
      '<div class="tb-chips"><select id="fa" aria-label="Area">' + opts(AREAS.map(function (a) { return [a, "Area " + a]; }), P.area, "All areas") + "</select>" +
      '<select id="ff" aria-label="Format">' + opts(Object.keys(FMT).map(function (k) { return [k, FMT[k]]; }), P.fmt, "All formats") + "</select>" +
      '<select id="fd" aria-label="Difficulty">' + opts([[1, "Difficulty 1"], [2, "Difficulty 2"], [3, "Difficulty 3"]], P.diff, "All levels") + "</select></div>" +
      '<div class="tb-sum">' + done + " / " + ITEMS.length + " done" + (avg !== null ? " → best avg " + avg + "%" : "") + "</div>" +
      '<ul class="tb-list">' + rows.map(function (t) {
        var st = S.items[t.id], live = S.live[t.id] && !S.live[t.id].done;
        var right = st && st.done ? '<span class="s done">' + st.best + "%<small>Done ×" + st.done + "</small></span>" : live ? '<span class="s">In progress</span>' : '<span class="s"><small>—</small></span>';
        var lawFuture = t.testable_from > TODAY ? '<span class="badge">Practice only</span>' : "";
        return '<li><a href="#/' + t.id + '"><span class="t">' + esc(t.title) + lawFuture + "</span>" + right +
          '<span class="m">Area ' + t.area + " → " + FMT[t.format] + ' → <span class="dots">' + dots(t.difficulty) + "</span> → " + t.est_minutes + " min" + (Object.keys(t.vary).length ? " → variants" : "") + "</span></a></li>";
      }).join("") + "</ul></div>" + '<div class="toast" id="toast" hidden></div>';
    $$("[data-mode]").forEach(function (b) { b.onclick = function () { S.pref.mode = b.dataset.mode; save(); listView(); }; });
    $("#fa").onchange = function () { S.pref.area = this.value; save(); listView(); };
    $("#ff").onchange = function () { S.pref.fmt = this.value; save(); listView(); };
    $("#fd").onchange = function () { S.pref.diff = this.value; save(); listView(); };
  }

  /* ── solver ── */
  var A, R, item, viewed, tab;
  function newAttempt(id, seed, mode) {
    return { id: id, seed: seed || 0, mode: mode, secs: 0, vals: {}, res: {}, hints: {}, shown: {}, submitted: false, done: false, started: Date.now(), exh: 0 };
  }
  function openItem(id, seed, restart) {
    item = BYID[id];
    if (!item) { location.hash = ""; return; }
    var live = S.live[id];
    if (!restart && live && (seed === null || seed === live.seed)) A = live;
    else A = newAttempt(id, seed || 0, S.pref.mode);
    S.live[id] = A; save();
    R = build(item, A.seed);
    tab = "task";
    viewed = {};
    solverView();
  }
  function cellById(cid) { return R.cells.filter(function (c) { return c.id === cid; })[0]; }
  function entries() { return A.vals; }
  function isExam() { return A.mode === "exam"; }
  function locked(c) { var r = A.res[c.id]; return A.submitted || A.done && !retryable(c) || (r && r.kind === "ok") || (r && A.shown[c.id]); }
  function retryable(c) { var r = A.res[c.id]; return !isExam() && r && r.kind !== "ok" && !A.shown[c.id]; }

  function exhibitHtml(x) {
    var k = { email: "Email", memo: "Memo", return_excerpt: "Tax return excerpt", contract: "Contract", table: "Table", notes: "Notes", statute_note: "Law excerpt" }[x.kind] || x.kind;
    var h = '<div class="kind">' + k + "</div><h3>" + esc(x.title) + "</h3>";
    if (Array.isArray(x.body)) {
      var rows = x.body, head = x.kind === "table" && rows.length > 1 ? rows[0] : null, bodyRows = head ? rows.slice(1) : rows;
      h += '<table class="ex-tbl">' + (head ? "<thead><tr>" + head.map(function (c) { return "<th>" + esc(c) + "</th>"; }).join("") + "</tr></thead>" : "") +
        "<tbody>" + bodyRows.map(function (r) { return "<tr>" + r.map(function (c) { return "<td>" + esc(c) + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table>";
    } else {
      var lines = String(x.body).split("\n"), hd = [];
      if (x.kind === "email") while (lines.length && /^(From|To|Cc|Subject|Date|Re):/i.test(lines[0])) hd.push(lines.shift());
      if (hd.length) h += '<div class="ex-mail"><div class="hd">' + hd.map(function (l) { var i = l.indexOf(":"); return "<div><b>" + esc(l.slice(0, i)) + "</b>" + esc(l.slice(i + 1).trim()) + "</div>"; }).join("") + "</div></div>";
      var cls = x.kind === "statute_note" || x.kind === "notes" ? "ex-txt ex-note" : "ex-txt";
      h += '<div class="' + cls + '">' + lines.filter(function (l, i, a) { return !(l === "" && (i === 0 || a[i - 1] === "")); }).map(function (l) { return l === "" ? "" : "<p>" + esc(l) + "</p>"; }).join("") + "</div>";
    }
    return h;
  }

  function cellHtml(c, i) {
    var inp;
    if (c.kind === "number") inp = '<span class="fld">' + (c.fmt === "n" ? "" : '<span class="pre">$</span>') + '<input data-c="' + c.id + '" inputmode="decimal" autocomplete="off" aria-labelledby="l-' + c.id + '"></span>';
    else if (c.kind === "dropdown") inp = '<select data-c="' + c.id + '" aria-labelledby="l-' + c.id + '"><option value="">Select</option>' + c.options.map(function (o) { return '<option value="' + esc(o) + '">' + esc(o) + "</option>"; }).join("") + "</select>";
    else inp = '<span class="fld txt"><input data-c="' + c.id + '" autocomplete="off" spellcheck="false" placeholder="§1012(a)" aria-labelledby="l-' + c.id + '"></span>';
    return '<article class="cell" id="cell-' + c.id + '"><div class="cl"><span class="n">' + (i + 1) + '</span><label id="l-' + c.id + '">' + esc(c.label) + '</label></div>' +
      '<div class="in">' + inp + "</div>" + (c.kind === "citation" ? '<div class="ask">' + esc(c.ask) + "</div>" : "") +
      '<div class="acts"></div><div class="hintbox" hidden></div><div class="fb" hidden></div><div class="exp" hidden></div></article>';
  }

  function solverView() {
    document.title = item.title + " – TBS";
    var future = item.testable_from > TODAY;
    root.innerHTML =
      '<div class="tb-wrap"><div class="tb-bar"><a class="back" href="#/">← TBS</a><h1>' + esc(item.title) +
      (future ? '<span class="badge">Practice only</span>' : "") + '</h1>' +
      '<span class="tb-mode" id="mode"></span><span class="tb-timer" id="tmr" aria-live="off">0:00</span>' +
      '<button class="tb-btn sm" id="var"></button><button class="tb-btn sm" id="org">Original numbers</button><button class="tb-btn sm" id="rst">Restart</button></div>' +
      '<div class="stones" id="stones" role="list"></div>' +
      '<div class="tb-tabs" role="tablist"><button data-t="exh">Exhibits</button><button data-t="task">Task</button><button data-t="res">Result</button></div>' +
      '<div class="tb-split" id="split" data-tab="task">' +
      '<section class="pane exh" aria-label="Exhibits"><div class="ex-tabs" role="tablist" id="extabs"></div><div class="ex-body" id="exbody"></div></section>' +
      '<section class="pane task" aria-label="Task"><p class="sc">' + esc(R.scenario) + '</p><p class="tk">' + esc(R.task) + "</p>" +
      (item.law_note ? '<details class="lawnote"><summary>Law note</summary><p>' + esc(item.law_note) + "</p></details>" : "") +
      '<div id="cells">' + R.cells.map(cellHtml).join("") + '</div><div class="bar-act" id="bar"></div><div id="cf"></div></section>' +
      '<section class="pane res" id="res" hidden></section>' +
      '<div class="mfab"><button id="seex">Exhibits</button></div></div></div><div class="toast" id="toast" hidden></div>';
    // exhibits
    var tabs = $("#extabs");
    tabs.innerHTML = R.exhibits.map(function (x, i) { return '<button role="tab" data-x="' + i + '" class="unseen">' + esc(x.title.length > 28 ? x.title.slice(0, 26) + "…" : x.title) + "</button>"; }).join("");
    $$("[data-x]").forEach(function (b) { b.onclick = function () { showExh(+b.dataset.x); }; });
    showExh(Math.min(A.exh || 0, R.exhibits.length - 1));
    $$(".tb-tabs [data-t]").forEach(function (b) { b.onclick = function () { setTab(b.dataset.t); }; });
    $("#seex").onclick = function () { setTab("exh"); window.scrollTo(0, 0); };
    setTab("task");
    // inputs
    R.cells.forEach(function (c) {
      var el = $('[data-c="' + c.id + '"]');
      if (A.vals[c.id] !== undefined) el.value = A.vals[c.id];
      var onIn = function () { A.vals[c.id] = el.value; persist(); paintStones(); barUpdate(); };
      el.addEventListener("input", onIn); el.addEventListener("change", onIn);
      if (c.kind === "number") {
        el.addEventListener("blur", function () {
          var v = parseNum(el.value);
          if (!isNaN(v) && el.value.trim() !== "") { el.value = fmtVal(v, true); A.vals[c.id] = el.value; persist(); }
        });
        el.addEventListener("focus", function () { A.cur = c.id; paintStones(); });
      } else el.addEventListener("focus", function () { A.cur = c.id; paintStones(); });
      el.addEventListener("keydown", function (ev) { if (ev.key === "Enter" && !isExam()) { ev.preventDefault(); checkCell(c.id); } });
    });
    $("#var").onclick = function () { newNumbers(); };
    $("#org").onclick = function () { location.hash = "#/" + item.id + "/0/new"; };
    if (!A.seed) $("#org").style.display = "none";
    $("#rst").onclick = function () { openItem(item.id, A.seed, true); };
    var varBtn = $("#var");
    if (Object.keys(item.vary).length) { varBtn.textContent = "New numbers"; } else varBtn.style.display = "none";
    $("#mode").textContent = isExam() ? "Exam" : "Practice";
    R.cells.forEach(paintCell);
    paintStones(); barUpdate();
    if (A.done) showResult();
    stopTimer();
    tick();
    timerId = setInterval(tick, 1000);
  }
  function setTab(t) {
    tab = t;
    $("#split").dataset.tab = t;
    $$(".tb-tabs [data-t]").forEach(function (b) { b.setAttribute("aria-selected", String(b.dataset.t === t)); });
    var rb = $('.tb-tabs [data-t="res"]'); if (rb) rb.style.opacity = A.done || A.submitted ? "1" : ".4";
  }
  function showExh(i) {
    A.exh = i; viewed[i] = true;
    $$("[data-x]").forEach(function (b) { b.setAttribute("aria-selected", String(+b.dataset.x === i)); b.classList.toggle("unseen", !viewed[+b.dataset.x] && +b.dataset.x !== i); });
    $("#exbody").innerHTML = exhibitHtml(R.exhibits[i]);
    $("#exbody").scrollTop = 0;
  }
  var pt = null;
  function persist() { clearTimeout(pt); pt = setTimeout(save, 300); }
  function tick() {
    if (document.hidden || A.done && !isExam() || A.submitted) { renderTimer(); return; }
    A.secs += 1;
    renderTimer();
    if (isExam() && !A.submitted && A.secs >= EXAM_SECS) submitExam(true);
    if (A.secs % 5 === 0) save();
  }
  function renderTimer() {
    var t = $("#tmr"); if (!t) return;
    t.textContent = isExam() && !A.submitted ? mmss(EXAM_SECS - A.secs) : mmss(A.secs);
  }

  function stoneClass(c) {
    var r = A.res[c.id];
    if (r) return r.kind === "ok" ? "ok" : (r.kind === "ecf" || r.kind === "half") ? "half" : "bad";
    var v = A.vals[c.id];
    return v !== undefined && String(v).trim() !== "" ? "fill" : "";
  }
  function paintStones() {
    var s = $("#stones"); if (!s) return;
    s.innerHTML = R.cells.map(function (c, i) {
      return '<button role="listitem" class="' + stoneClass(c) + (A.cur === c.id ? " cur" : "") + '" data-s="' + c.id + '" aria-label="Cell ' + (i + 1) + '"></button>';
    }).join("");
    $$("[data-s]", s).forEach(function (b) {
      b.onclick = function () { setTab("task"); var el = $("#cell-" + b.dataset.s); el.scrollIntoView({ block: "center" }); var f = $("[data-c]", el); if (f) f.focus(); };
    });
  }
  function fbHtml(c, r, v) {
    var h = "";
    if (r.kind === "ok") return '<span class="st ok">✓ Correct</span>';
    var shown = c.kind === "number" ? (isNaN(parseNum(v)) ? esc(v) : esc(money(parseNum(v), c.fmt))) : esc(v);
    if (r.kind === "ecf") h = '<span class="st half">½ Carried forward</span> <del class="mute">' + shown + '</del><div class="msg">Follows from your earlier entries. This cell’s own answer differs.</div>';
    else if (r.kind === "half") h = '<span class="st half">½ Partial match</span> <del class="mute">' + shown + "</del>";
    else if (r.kind === "blank") h = '<span class="st bad">✗ No entry</span>';
    else h = '<span class="st bad">✗ Incorrect</span> <del>' + shown + "</del>";
    if (r.msg) h += '<div class="msg">' + esc(r.msg) + "</div>";
    if (r.rc !== undefined && r.kind !== "ok") h += '<div class="msg">Retry: ✗</div>';
    return h;
  }
  function answerText(c) {
    if (c.kind === "number") return money(c.answer, c.fmt);
    if (c.kind === "dropdown") return c.answer;
    return c.accept.map(function (a) { return "§" + a; }).join(" → ");
  }
  function explText(c) {
    return c.label + "\nAnswer: " + answerText(c) + "\n" + c.why + (c.steps.length ? "\n" + c.steps.map(function (s, i) { return (i + 1) + ". " + s; }).join("\n") : "") +
      (c.cite ? "\nSource: " + c.cite : "") + (c.link ? "\n" + c.link : "");
  }
  function paintCell(c) {
    var el = $("#cell-" + c.id), r = A.res[c.id], inp = $("[data-c]", el);
    var cls = "cell" + (r ? (r.kind === "ok" ? " ok" : (r.kind === "ecf" || r.kind === "half") ? " half" : " bad") : "");
    el.className = cls;
    var lock = A.submitted || !!(r && (r.kind === "ok" || A.shown[c.id])) || (A.done && !retryable(c));
    inp.disabled = lock;
    var acts = $(".acts", el), hb = $(".hintbox", el), fb = $(".fb", el), ex = $(".exp", el);
    var hn = A.hints[c.id] || 0, maxh = c.hints.length + (c.steps.length ? 1 : 0);
    var btns = "";
    if (!isExam() && !lock) btns += '<button class="tb-btn sm" data-a="chk">Check</button>';
    if (!isExam() && !lock && maxh) btns += '<button class="tb-btn sm" data-a="hint"' + (hn >= maxh ? " disabled" : "") + ">Hint " + Math.min(hn + 1, maxh) + "/" + maxh + "</button>";
    var canExp = (r && !isExam()) || A.submitted;
    if (canExp) btns += '<button class="tb-btn sm" data-a="exp">' + (A.open && A.open[c.id] ? "Hide explanation" : "Show explanation") + "</button>";
    acts.innerHTML = btns;
    hb.hidden = !(hn && !isExam());
    if (!hb.hidden) {
      var lines = c.hints.slice(0, Math.min(hn, c.hints.length)).map(function (h) { return "<li>" + esc(h) + "</li>"; });
      var stepsOn = hn > c.hints.length;
      hb.innerHTML = "<ol>" + lines.join("") + "</ol>" + (stepsOn ? "<b>Steps</b><ol>" + c.steps.map(function (s) { return "<li>" + esc(s) + "</li>"; }).join("") + "</ol>" : "");
    }
    fb.hidden = !r || !!r.stale;
    if (r) fb.innerHTML = fbHtml(c, r, r.v);
    ex.hidden = !(A.open && A.open[c.id]);
    if (!ex.hidden) {
      ex.innerHTML = "<div>Answer <ins>" + esc(answerText(c)) + "</ins></div><p style=\"margin:6px 0\">" + esc(c.why) + "</p>" +
        (c.steps.length ? "<ol>" + c.steps.map(function (s) { return "<li>" + esc(s) + "</li>"; }).join("") + "</ol>" : "") +
        (c.link ? '<div class="lnk">Source: <a href="' + esc(c.link) + '" target="_blank" rel="noopener noreferrer">' + esc(c.cite || "law.cornell.edu") + " ↗</a></div>" : (c.cite ? '<div class="lnk">Source: ' + esc(c.cite) + "</div>" : "")) +
        '<div class="cp"><button class="tb-btn sm" data-a="cp">Copy</button></div>';
    }
    $$("[data-a]", el).forEach(function (b) {
      b.onclick = function () {
        var a = b.dataset.a;
        if (a === "chk") checkCell(c.id);
        else if (a === "hint") { A.hints[c.id] = (A.hints[c.id] || 0) + 1; save(); paintCell(c); }
        else if (a === "exp") { toggleExp(c); }
        else if (a === "cp") { copy(explText(c)); }
      };
    });
  }
  function toggleExp(c) {
    A.open = A.open || {};
    A.shown[c.id] = true;
    A.open[c.id] = !A.open[c.id];
    save();
    paintCell(c); paintStones(); barUpdate();
  }
  function copy(text) {
    function ok() { toast("Copied"); }
    try { navigator.clipboard.writeText(text).then(ok, function () { fallback(); }); } catch (e) { fallback(); }
    function fallback() {
      var t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select();
      try { document.execCommand("copy"); ok(); } catch (e) { toast("Copy failed"); }
      document.body.removeChild(t);
    }
  }

  /* grading */
  function checkCell(cid, quiet) {
    var c = cellById(cid), prev = A.res[cid], raw = A.vals[cid];
    if (raw === undefined || String(raw).trim() === "") { if (!quiet) toast("No entry"); return false; }
    var g = gradeCell(R, c, A.vals);
    if (prev) {
      if (prev.kind === "ok" || isExam()) return true;
      prev.kind = g.kind; prev.msg = g.msg; prev.v = raw; prev.stale = false;
      prev.rc = Math.max(prev.rc || 0, g.credit * 0.5);
    } else {
      A.res[cid] = { kind: g.kind, credit: g.credit, msg: g.msg, v: raw, t: A.secs, h: A.hints[cid] || 0 };
    }
    A.cur = cid;
    paintCell(c); paintStones(); barUpdate();
    checkDone();
    if (A.done) showResult();
    save();
    return true;
  }
  function checkAll() {
    R.cells.forEach(function (c) {
      var r = A.res[c.id];
      if (r && r.kind === "ok") return;
      if (r) { checkCell(c.id, true); return; }
      var raw = A.vals[c.id];
      if (raw === undefined || String(raw).trim() === "") A.res[c.id] = { kind: "blank", credit: 0, msg: "", v: "", t: A.secs, h: A.hints[c.id] || 0 };
      else checkCell(c.id, true);
    });
    R.cells.forEach(paintCell); paintStones(); barUpdate(); checkDone(); save();
  }
  function retryWrong() {
    var first = null;
    R.cells.forEach(function (c) {
      var r = A.res[c.id];
      if (r && r.kind !== "ok" && !A.shown[c.id]) { r.stale = true; if (!first) first = c; paintCell(c); }
    });
    if (first) { setTab("task"); var el = $("#cell-" + first.id); el.scrollIntoView({ block: "center" }); $("[data-c]", el).focus(); }
  }
  function wrongCount() { return R.cells.filter(function (c) { var r = A.res[c.id]; return r && r.kind !== "ok" && !A.shown[c.id]; }).length; }
  function answeredCount() { return R.cells.filter(function (c) { var v = A.vals[c.id]; return v !== undefined && String(v).trim() !== ""; }).length; }
  function score() {
    var s = 0, s2 = 0, max = 0;
    R.cells.forEach(function (c) {
      var r = A.res[c.id]; max += c.points;
      if (!r) return;
      s += r.credit * c.points;
      s2 += Math.max(r.credit, r.rc || 0) * c.points;
    });
    return { s: s, s2: s2, max: max };
  }
  function barUpdate() {
    var b = $("#bar"); if (!b) return;
    var n = R.cells.length, ans = answeredCount(), wr = wrongCount();
    var h = '<span class="grow" style="font-weight:700;color:var(--ink-3)">' + ans + " / " + n + " answered</span>";
    if (isExam() && !A.submitted) h += '<button class="tb-btn pri" id="sub">Submit</button>';
    else if (!isExam() && !A.done) h += '<button class="tb-btn pri" id="chkall">Check all</button>';
    if (!isExam() && wr) h += '<button class="tb-btn rwb" id="rw">Retry wrong (' + wr + ")</button>";
    b.innerHTML = h;
    var s;
    if ((s = $("#sub"))) s.onclick = confirmSubmit;
    if ((s = $("#chkall"))) s.onclick = checkAll;
    if ((s = $("#rw"))) s.onclick = retryWrong;
  }
  function confirmSubmit() {
    var un = R.cells.length - answeredCount();
    var cf = $("#cf");
    cf.innerHTML = '<div class="confirm"><span>' + (un ? "Unanswered " + un + " → " : "") + 'Grading is final</span><button class="tb-btn pri sm" id="yes">Submit</button><button class="tb-btn sm" id="no">Cancel</button></div>';
    $("#yes").onclick = function () { submitExam(false); };
    $("#no").onclick = function () { cf.innerHTML = ""; };
  }
  function submitExam() {
    if (A.submitted) return;
    $("#cf").innerHTML = "";
    R.cells.forEach(function (c) {
      var raw = A.vals[c.id];
      if (raw === undefined || String(raw).trim() === "") { A.res[c.id] = { kind: "blank", credit: 0, msg: "", v: "", t: A.secs, h: 0 }; return; }
      var g = gradeCell(R, c, A.vals);
      A.res[c.id] = { kind: g.kind, credit: g.credit, msg: g.msg, v: raw, t: A.secs, h: 0 };
    });
    A.submitted = true;
    R.cells.forEach(paintCell); paintStones();
    finish();
  }
  function checkDone() {
    if (A.done || isExam()) return;
    if (R.cells.every(function (c) { return A.res[c.id]; })) finish();
  }
  function finish() {
    A.done = true;
    var sc = score(), pct = Math.round(sc.s / sc.max * 100);
    var st = S.items[item.id] = S.items[item.id] || { done: 0, best: 0, hist: [] };
    st.done += 1; st.best = Math.max(st.best, pct); st.last = Date.now();
    st.hist.push({ at: Date.now(), seed: A.seed, mode: A.mode, pct: pct, secs: A.secs, hints: sum(A.hints) });
    st.hist = st.hist.slice(-20);
    A.pct = pct;
    save();
    barUpdate();
    R.cells.forEach(paintCell);
    showResult();
    setTab("res");
    var rb = $("#res"); if (rb && window.matchMedia("(min-width:768px)").matches) rb.scrollIntoView({ block: "nearest" });
  }
  function sum(o) { var t = 0; for (var k in o) t += o[k]; return t; }
  function showResult() {
    var res = $("#res"); res.hidden = false;
    var sc = score(), pct = Math.round(sc.s / sc.max * 100), hints = sum(A.hints);
    var h = '<div class="big">' + num(sc.s) + " / " + sc.max + "<small>" + pct + "%</small></div><dl>";
    h += "<dt>Time</dt><dd>" + mmss(A.secs) + " → est " + item.est_minutes + " min → exam avg 18 min</dd>";
    if (!isExam()) h += "<dt>Hints</dt><dd>" + hints + "</dd>";
    if (sc.s2 > sc.s) h += "<dt>After retry</dt><dd>" + num(sc.s2) + " / " + sc.max + "</dd>";
    h += "<dt>Mode</dt><dd>" + (isExam() ? "Exam" : "Practice") + (A.seed ? " → variant #" + A.seed : "") + "</dd></dl>";
    h += '<ul class="cellrows">' + R.cells.map(function (c, i) {
      var r = A.res[c.id]; var mark = r.kind === "ok" ? "✓" : r.kind === "ecf" || r.kind === "half" ? "½" : "✗";
      return '<li><b>' + (i + 1) + "</b><span class=\"" + (r.kind === "ok" ? "" : r.kind === "ecf" || r.kind === "half" ? "" : "bad") + '">' + mark + "</span><span>" + esc(c.label.length > 70 ? c.label.slice(0, 68) + "…" : c.label) + "</span></li>";
    }).join("") + "</ul>";
    var wr = isExam() ? 0 : wrongCount();
    h += '<div class="bar-act">' + (wr ? '<button class="tb-btn pri rwb" id="rw2">Retry wrong (' + wr + ")</button>" : "") + (Object.keys(item.vary).length ? '<button class="tb-btn" id="nn">New numbers</button>' : '<button class="tb-btn" id="again">Restart</button>') + '<a class="tb-btn" style="text-decoration:none;display:inline-flex;align-items:center" href="#/">List</a></div>';
    res.innerHTML = h;
    var b;
    if ((b = $("#nn"))) b.onclick = newNumbers;
    if ((b = $("#rw2"))) b.onclick = retryWrong;
    if ((b = $("#again"))) b.onclick = function () { openItem(item.id, 0, true); };
    var rbtn = $('.tb-tabs [data-t="res"]'); if (rbtn) rbtn.style.opacity = "1";
  }
  function newNumbers() {
    var seed = 1 + Math.floor(Math.random() * 900000);
    location.hash = "#/" + item.id + "/" + seed + "/new";
  }

  /* ── router ── */
  function route() {
    var m = /^#\/([^\/]+)(?:\/(\d+))?(?:\/(new))?$/.exec(location.hash);
    if (!m) { listView(); return; }
    var seed = m[2] === undefined ? null : +m[2];
    openItem(m[1], seed, m[3] === "new");
    if (m[3]) history.replaceState(null, "", "#/" + m[1] + "/" + seed);
  }
  window.addEventListener("hashchange", route);
  window.addEventListener("beforeunload", function () { if (A) save(); });
  window.TBSApp = { get S() { return S; }, get A() { return A; }, get R() { return R; }, checkCell: checkCell };
  route();
})();
