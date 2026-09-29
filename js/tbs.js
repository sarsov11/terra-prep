/* TBS (task-based simulation) engine + screen.
   Engine (window.TBSEngine): safe formula evaluator, render/variant, grading with carry-forward (ECF), citation normalizer.
   It mirrors tools/src/TBS/tbs_lib.py (REG) and tbs_far_lib.py (FAR); tools/test_tbs_variants.py checks both against each other.
   FAR adds: journal-entry cells (kind "je", graded by js/jegrade.js), decimal formats, annuity functions, ASC/GASB number matching.
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
  /* FAR: half-up rounding to d decimals (twin of tbs_far_lib.rd) and the annuity helpers */
  function rd(x, d) { var m = Math.pow(10, d || 0); return Math.floor(x * m + 0.5 + 1e-9) / m; }
  function pvann(r, n, pmt, fv) { fv = fv || 0; if (r === 0) return pmt * n + fv; var d = Math.pow(1 + r, -n); return pmt * (1 - d) / r + fv * d; }
  function pvdue(r, n, pmt, fv) { fv = fv || 0; if (r === 0) return pmt * n + fv; var d = Math.pow(1 + r, -n); return pmt * (1 + r) * (1 - d) / r + fv * d; }
  function pmtann(r, n, pv) { return r === 0 ? pv / n : pv * r / (1 - Math.pow(1 + r, -n)); }
  function iff(c, a, b) { return c ? a : b; }
  var FNF = { rnd: function (x) { return rd(x, 0); }, min: Math.min, max: Math.max, abs: Math.abs, pvann: pvann, pvdue: pvdue, pmtann: pmtann, iff: iff };
  var DEC = { "$": 0, "n": 0, "$2": 2, "x2": 2, "p1": 1 };   /* FAR fmt -> decimals */

  /* Formula parser: numbers, names, + - * / // % **, comparisons, and/or/not, calls to FN only. No eval(). */
  var cache = {};   /* key: mode letter + source (FAR and REG use different rnd) */
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
  function compile(src, far) {
    var ck = (far ? "F" : "R") + src, FNS = far ? FNF : FN;
    if (cache[ck]) return cache[ck];
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
          if (!Object.prototype.hasOwnProperty.call(FNS, name)) throw new Error("function not allowed: " + name);
          var f = FNS[name];
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
    cache[ck] = fn;
    return fn;
  }
  /* the name "$far" cannot be typed in a formula, so it is a safe mode flag inside the namespace */
  function ev(expr, ns) { return compile(expr, !!ns["$far"])(ns); }

  function buildNs(params, derived, far) {
    var ns = {}, k;
    if (far) ns["$far"] = true;
    for (k in params) ns[k] = params[k];
    (derived || []).forEach(function (d) { ns[d[0]] = ev(d[1], ns); });
    return ns;
  }
  function isFar(item) { return item.exam === "FAR"; }
  function solve(item, params) {
    var far = isFar(item), ns = buildNs(params || item.params, item.derived, far), vals = {};
    item.cells.forEach(function (c) {
      if (c.kind === "number") {
        var v = ev(c.expr, ns);
        v = far ? rd(v, DEC[c.fmt] || 0) : (c.fmt === "%dec" ? v : rnd(v));
        vals[c.id] = v; ns[c.id] = v;
      } else if (c.kind === "je") {
        vals[c.id] = c.lines.map(function (l) { return rd(ev(l.expr, ns), 0); });
      }
    });
    return { ns: ns, vals: vals };
  }
  function group(s) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  /* spec: falsy = plain, true or ":," = thousands separators, ":N" = N decimals (tbs_far_lib.fmtval) */
  function fmtVal(v, spec) {
    if (typeof spec === "string" && /^:[0-9]$/.test(spec)) return v.toFixed(+spec.charAt(1));
    var comma = !!spec;
    if (!comma) return String(v);
    var neg = v < 0, s = String(Math.abs(v)), i = s.indexOf(".");
    var ip = i < 0 ? s : s.slice(0, i), fp = i < 0 ? "" : s.slice(i);
    return (neg ? "-" : "") + group(ip) + fp;
  }
  function fill(s, ns) {
    if (typeof s === "string") {
      return s.replace(/\{([A-Za-z_][A-Za-z_0-9]*)(:,|:[0-9])?\}/g, function (m, name, c) {
        if (!Object.prototype.hasOwnProperty.call(ns, name)) throw new Error("missing " + name);
        return fmtVal(ns[name], c || false);
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
    var far = isFar(item);
    var out = {
      id: item.id, exam: item.exam || "REG", area: item.area, format: item.format, difficulty: item.difficulty, est_minutes: item.est_minutes,
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
        o.traps = (c.traps || []).map(function (t) { return { expr: t.expr, value: far ? rd(ev(t.expr, ns), DEC[c.fmt] || 0) : rnd(ev(t.expr, ns)), msg: fill(t.msg, ns) }; });
      } else if (c.kind === "je") {
        o.ask = fill(c.ask || "", ns); o.accounts = c.accounts.slice(); o.tol = c.tol || 1; o.ecf = true;
        o.lines = c.lines.map(function (l, i) {
          return { s: l.s, a: l.a, v: sv.vals[c.id][i], why: fill(l.why, ns), alt: (l.alt || []).slice(), deps: uniq(l.expr.match(/\bc\d+\b/g) || []), expr: l.expr };
        });
        o.mist = (c.mist || []).map(function (m) {
          var m2 = { k: m.k, a: m.a, msg: fill(m.msg, ns) };
          if (m.b) m2.b = m.b;
          if (m.expr) { m2.expr = m.expr; m2.v = rd(ev(m.expr, ns), 0); }
          return m2;
        });
        if (!o.hints.length) o.hints = jeHints(o.lines);
        o.points = c.lines.length;
      } else if (c.kind === "dropdown") {
        o.options = fill(c.options, ns); o.answer = fill(c.answer, ns);
        o.wrong = {};
        for (var k in (c.wrong_msgs || {})) o.wrong[fill(k, ns)] = fill(c.wrong_msgs[k], ns);
        if (rng) shuffle(o.options, rng);
        else if (c.opts0 && sameParams(params, item.params)) o.options = fill(c.opts0, ns);
      } else {
        o.ask = fill(c.ask || "", ns); o.accept = c.accept; o.partial = c.partial || []; o.norm = c.norm || "";
      }
      out.cells.push(o);
    });
    return out;
  }
  var COA = {}, JEG = null;
  function coaSet(list) { COA = {}; JEG = null; list.forEach(function (a) { COA[a.id] = a; }); }
  /* twin of tbs_far_lib.je_hints: affected accounts -> increase/decrease -> debit/credit (no amounts) */
  function jeHints(lines) {
    function nm(l) { return COA[l.a].name; }
    var byName = lines.slice().sort(function (x, y) { return nm(x) < nm(y) ? -1 : nm(x) > nm(y) ? 1 : 0; });
    return ["Accounts: " + byName.map(nm).join(", "),
      byName.map(function (l) { return nm(l) + " " + (l.s === COA[l.a].n ? "increases" : "decreases"); }).join("; "),
      lines.map(function (l) { return nm(l) + ": " + (l.s === "D" ? "Debit" : "Credit"); }).join("; ")];
  }
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function sameParams(a, b) { for (var k in b) if (a[k] !== b[k]) return false; return true; }
  function pickParams(item, seed) {
    var rng = mulberry32((hash(item.id) ^ Math.imul(seed, 2246822519)) >>> 0);
    for (var n = 0; n < 200; n++) {
      var p = {}, k;
      for (k in item.params) p[k] = item.params[k];
      for (k in item.vary) { var ch = item.vary[k]; p[k] = ch[Math.floor(rng() * ch.length)]; }
      var ns = buildNs(p, item.derived, isFar(item));
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
  /* FAR ASC/GASB numbers: "FASB ASC Topic 260" -> "260"; "ASC 205-20-45-1B" -> "205-20-45-1b"; "GASB Statement No. 34" -> "34" (twin: norm_std) */
  function normStd(s) {
    s = String(s).toLowerCase().trim().replace(/§/g, " ").replace(/–/g, "-").replace(/—/g, "-");
    s = s.replace(/\b(fasb|asc|gasb|codification|topic|subtopic|statement|standards?|no|number|section|sec|paragraph|para)\b/g, " ");
    s = s.replace(/[#.,;:]/g, " ");
    return s.replace(/\s+/g, "");
  }
  function isBlank(e) {
    if (e === undefined || e === null) return true;
    if (Array.isArray(e)) return !e.some(function (r) { return r && (r.a || (r.tx && String(r.tx).trim()) || String(r.d || "").trim() || String(r.c || "").trim()); });
    return String(e).trim() === "";
  }
  function jeGrader() {
    if (!JEG) { if (!window.JEGrade) throw new Error("js/jegrade.js missing"); JEG = window.JEGrade.make(COA); }
    return JEG;
  }
  function amt(x) { var v = parseNum(x); return isNaN(v) || v < 0 ? 0 : v; }
  /* Grade one cell. entries: {cid: raw input}. Returns {credit, kind: ok|ecf|half|wrong|blank, msg, entry}.
     ECF: recompute the formula with the learner's entries for every number cell (others keep the correct value). */
  function gradeCell(r, cell, entries, ecfCredit) {
    if (ecfCredit === undefined) ecfCredit = 0.5;
    var e = entries[cell.id];
    if (isBlank(e)) return { credit: 0, kind: "blank", msg: "" };
    if (cell.kind === "je") return gradeJe(r, cell, e, entries);
    if (cell.kind === "dropdown") {
      if (e === cell.answer) return { credit: 1, kind: "ok" };
      return { credit: 0, kind: "wrong", msg: cell.wrong[e] || "" };
    }
    if (cell.kind === "citation" && cell.norm === "std") {
      var ns2 = normStd(e);
      if (cell.accept.some(function (a) { return ns2 === a || ns2.indexOf(a + "-") === 0; })) return { credit: 1, kind: "ok" };
      if ((cell.partial || []).some(function (a) { return ns2 === a; })) return { credit: 0.5, kind: "half", msg: "" };
      return { credit: 0, kind: "wrong", msg: "" };
    }
    if (cell.kind === "citation") {
      var n = normCite(e);
      if (cell.accept.some(function (a) { return a.toLowerCase() === n; })) return { credit: 1, kind: "ok" };
      if (cell.partial.some(function (a) { return a.toLowerCase() === n; })) return { credit: 0.5, kind: "half", msg: "" };
      return { credit: 0, kind: "wrong", msg: "" };
    }
    var v = parseNum(unit(e, cell.fmt));
    if (isNaN(v)) return { credit: 0, kind: "wrong", msg: "" };
    if (Math.abs(v - cell.answer) <= cell.tol + 1e-9) return { credit: 1, kind: "ok" };
    var trap = "";
    cell.traps.forEach(function (t) { if (!trap && Math.abs(v - t.value) <= cell.tol + 1e-9) trap = t.msg; });
    if (cell.ecf && cell.deps.length) {
      var loc = learnerNs(r, entries);
      var alt = null;
      try { alt = ev(cell.expr, loc); } catch (x) { alt = null; }
      if (alt !== null && Math.abs(v - alt) <= cell.tol + 1e-9) return { credit: ecfCredit, kind: "ecf", msg: trap };
    }
    return { credit: 0, kind: "wrong", msg: trap };
  }
  function e0(x, fmt) { return isBlank(x) ? NaN : parseNum(unit(x, fmt)); }
  /* FAR entry units: "12.5%" for p1, "1.25x" for x2 */
  function unit(e, fmt) {
    if (fmt === "p1") return String(e).replace(/%/g, "");
    if (fmt === "x2") return String(e).replace(/\s*[x×]\s*$/i, "");
    return e;
  }
  /* namespace with the learner's own numbers for every number cell (blank or unreadable keeps the correct value) */
  function learnerNs(r, entries) {
    var loc = buildNs(r.params, r.derived, r.exam === "FAR");
    r.cells.forEach(function (c) {
      if (c.kind !== "number") return;
      var pv = e0(entries[c.id], c.fmt);
      loc[c.id] = isNaN(pv) ? c.answer : pv;
    });
    return loc;
  }
  /* journal-entry cell: line-by-line credit (js/jegrade.js). Earlier-cell errors carry forward at 0.75 per line. */
  function gradeJe(r, cell, rows, entries) {
    var loc = null;
    var lines = cell.lines.map(function (l) {
      var o = { a: l.a, s: l.s, v: l.v, alt: l.alt };
      if (l.deps.length) {
        if (!loc) loc = learnerNs(r, entries);
        try { o.av = rd(ev(l.expr, loc), 0); } catch (x) { o.av = null; }
      }
      return o;
    });
    var rr = (rows || []).map(function (x) { return { a: x.a || null, tx: x.tx || "", d: amt(x.d), c: amt(x.c) }; });
    var g = jeGrader().grade({ lines: lines }, cell.mist, cell.tol, rr);
    var det = {
      lines: g.lines.map(function (u) { return { a: u.a, tx: u.tx || "", s: u.s, v: u.v, status: u.status, msg: u.msg || "", note: u.note || "", c: u.c ? { a: u.c.a, s: u.c.s, v: u.c.v } : null }; }),
      missing: g.missing.map(function (m) { return { a: m.c.a, s: m.c.s, v: m.c.v, msg: m.msg }; }),
      allFlip: g.allFlip
    };
    return { credit: g.score, kind: g.perfect ? "ok" : (g.score > 0 ? "partial" : "wrong"), msg: "", detail: det };
  }

  window.TBSEngine = { rnd: rnd, rd: rd, ev: ev, buildNs: buildNs, solve: solve, render: render, build: build, pickParams: pickParams, gradeCell: gradeCell,
    normCite: normCite, normStd: normStd, unit: unit, parseNum: parseNum, fill: fill, setCoa: coaSet, jeHints: jeHints };

  if (window.TBS_SETS && window.TBS_SETS.FAR && window.TBS_SETS.FAR.coa) coaSet(window.TBS_SETS.FAR.coa);

  /* ───────────── screen ───────────── */
  var root = document.getElementById("tbs-app");
  if (!root) return;
  /* Sections: window.TBS_SETS.REG (data/tbs_reg.js) and .FAR (data/tbs_far.js). The list shows one section at a time. */
  var SETS = window.TBS_SETS || {};
  var ITEMS = [], BYID = {}, SECS = [];
  ["REG", "FAR"].forEach(function (k) {
    if (!SETS[k]) return;
    SECS.push(k);
    SETS[k].items.forEach(function (t) { t.exam = t.exam || k; ITEMS.push(t); BYID[t.id] = t; });
  });
  var KEY = "te.tbs.v1", EXAM_SECS = 18 * 60, TODAY = new Date().toISOString().slice(0, 10);
  var FMT = { numeric_table: "Numeric table", document_review: "Document review", research: "Research", dropdown_judgment: "Judgment", journal_entry: "Journal entry" };

  function read() { try { var v = localStorage.getItem(KEY); return v ? JSON.parse(v) : null; } catch (e) { return null; } }
  var S = read() || {};
  S.pref = S.pref || { mode: "practice", area: "", fmt: "", diff: "" };
  S.items = S.items || {};
  S.live = S.live || {};
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  /* Section of the list: ?sec= from the home screen, else the last choice here, else the section the app is set to (te.pref.v1). */
  function appSec() {
    try {
      var p = JSON.parse(localStorage.getItem("te.pref.v1")) || {}, e = window.CATALOG && window.CATALOG.exam(p.exam);
      return e && e.sec === "FAR" ? "FAR" : "REG";
    } catch (x) { return "REG"; }
  }
  var SEC = (function () {
    var q = new URLSearchParams(location.search).get("sec");
    if (q && SETS[q]) { S.pref.sec = q; return q; }
    if (S.pref.sec && SETS[S.pref.sec]) return S.pref.sec;
    var a = appSec();
    return SETS[a] ? a : (SECS[0] || "REG");
  })();
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function $(sel, el) { return (el || root).querySelector(sel); }
  function $$(sel, el) { return Array.prototype.slice.call((el || root).querySelectorAll(sel)); }
  /* answer text by format: $ and $2 with a dollar sign, n plain, x2 with x, p1 with % */
  function numTxt(v, d) {
    var neg = v < 0, a = Math.abs(v), s = d ? a.toFixed(d) : fmtVal(a, true);
    if (d) { var i = s.indexOf("."); s = group(s.slice(0, i)) + s.slice(i); }
    return (neg ? "-" : "") + s;
  }
  function money(v, fmt) {
    var s = numTxt(Math.abs(v), DEC[fmt] || 0), neg = v < 0 ? "-" : "";
    if (fmt === "x2") return neg + s + "x";
    if (fmt === "p1") return neg + s + "%";
    return fmt === "n" ? neg + s : neg + "$" + s;
  }
  function mmss(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); }
  function dots(n) { return "●".repeat(n) + "○".repeat(3 - n); }
  function num(n) { return Math.round(n * 100) / 100; }
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
    var P = S.pref, mine = ITEMS.filter(function (t) { return t.exam === SEC; });
    function opts(arr, cur, all) { return '<option value="">' + all + "</option>" + arr.map(function (a) { return '<option value="' + esc(a[0]) + '"' + (String(cur) === String(a[0]) ? " selected" : "") + ">" + esc(a[1]) + "</option>"; }).join(""); }
    var areas = ["I", "II", "III", "IV", "V"].filter(function (a) { return mine.some(function (t) { return t.area === a; }); });
    var fmts = Object.keys(FMT).filter(function (k) { return mine.some(function (t) { return t.format === k; }); });
    if (P.area && areas.indexOf(P.area) < 0) P.area = "";
    if (P.fmt && fmts.indexOf(P.fmt) < 0) P.fmt = "";
    var rows = mine.filter(function (t) {
      return (!P.area || t.area === P.area) && (!P.fmt || t.format === P.fmt) && (!P.diff || String(t.difficulty) === String(P.diff));
    });
    var done = mine.filter(function (t) { return S.items[t.id] && S.items[t.id].done; }).length;
    var pcts = mine.map(function (t) { return S.items[t.id] && S.items[t.id].done ? S.items[t.id].best : null; }).filter(function (x) { return x !== null; });
    var avg = pcts.length ? Math.round(pcts.reduce(function (a, b) { return a + b; }, 0) / pcts.length) : null;
    root.innerHTML =
      '<div class="tb-wrap"><div class="tb-bar"><a class="back" href="index.html">← Home</a><h1>TBS</h1>' +
      (SECS.length > 1 ? '<div class="tb-seg" role="group" aria-label="Section">' + SECS.map(function (k) { return '<button data-sec="' + k + '" aria-pressed="' + (SEC === k) + '">' + k + "</button>"; }).join("") + "</div>" : "") +
      '<div class="tb-seg" role="group" aria-label="Mode"><button data-mode="practice" aria-pressed="' + (P.mode === "practice") + '">Practice</button><button data-mode="exam" aria-pressed="' + (P.mode === "exam") + '">Exam</button></div></div>' +
      '<div class="tb-chips"><select id="fa" aria-label="Area">' + opts(areas.map(function (a) { return [a, "Area " + a]; }), P.area, "All areas") + "</select>" +
      '<select id="ff" aria-label="Format">' + opts(fmts.map(function (k) { return [k, FMT[k]]; }), P.fmt, "All formats") + "</select>" +
      '<select id="fd" aria-label="Difficulty">' + opts([[1, "Difficulty 1"], [2, "Difficulty 2"], [3, "Difficulty 3"]], P.diff, "All levels") + "</select></div>" +
      '<div class="tb-sum">' + done + " / " + mine.length + " done" + (avg !== null ? " → best avg " + avg + "%" : "") + "</div>" +
      '<ul class="tb-list">' + rows.map(function (t) {
        var st = S.items[t.id], live = S.live[t.id] && !S.live[t.id].done;
        var right = st && st.done ? '<span class="s done">' + st.best + "%<small>Done ×" + st.done + "</small></span>" : live ? '<span class="s">In progress</span>' : '<span class="s"><small>—</small></span>';
        var lawFuture = t.testable_from > TODAY ? '<span class="badge">Practice only</span>' : "";
        return '<li><a href="#/' + t.id + '"><span class="t">' + esc(t.title) + lawFuture + "</span>" + right +
          '<span class="m">Area ' + t.area + " → " + FMT[t.format] + ' → <span class="dots">' + dots(t.difficulty) + "</span> → " + t.est_minutes + " min" + (Object.keys(t.vary).length ? " → variants" : "") + "</span></a></li>";
      }).join("") + "</ul></div>" + '<div class="toast" id="toast" hidden></div>';
    $$("[data-mode]").forEach(function (b) { b.onclick = function () { S.pref.mode = b.dataset.mode; save(); listView(); }; });
    $$("[data-sec]").forEach(function (b) { b.onclick = function () { SEC = b.dataset.sec; S.pref.sec = SEC; S.pref.area = ""; S.pref.fmt = ""; save(); listView(); }; });
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
    SEC = item.exam; S.pref.sec = SEC;
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
  function isExam() { return A.mode === "exam"; }
  function locked(c) { var r = A.res[c.id]; return A.submitted || A.done && !retryable(c) || (r && r.kind === "ok") || (r && A.shown[c.id]); }
  function retryable(c) { var r = A.res[c.id]; return !isExam() && r && r.kind !== "ok" && !A.shown[c.id]; }
  function isDone(kind) { return kind === "ok" ? "ok" : (kind === "ecf" || kind === "half" || kind === "partial") ? "half" : "bad"; }

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

  /* ── journal-entry cell: account autocomplete + debit/credit lines ── */
  var ACC = null;
  function acctIndex() {
    if (ACC) return ACC;
    var norm = window.JEGrade.norm;
    ACC = { list: [], byName: {} };
    Object.keys(COA).forEach(function (id) {
      var a = COA[id], names = [a.name].concat(a.syn || []).map(function (x) { var n = norm(x); return { raw: x, n: n, k: n.replace(/ /g, ""), w: n.split(" ") }; });
      ACC.list.push({ id: id, names: names });
      names.forEach(function (x) { if (!ACC.byName[x.n]) ACC.byName[x.n] = id; if (!ACC.byName[x.k]) ACC.byName[x.k] = id; });
    });
    return ACC;
  }
  function resolveAcct(text) {
    var n = window.JEGrade.norm(text); if (!n) return null;
    var ix = acctIndex();
    return ix.byName[n] || ix.byName[n.replace(/ /g, "")] || null;
  }
  /* candidates of the cell first; typing also finds other accounts (a wrong pick is graded as an extra line) */
  function searchAcct(q, cell, limit) {
    var ix = acctIndex(), norm = window.JEGrade.norm, n = norm(q), cand = cell.accounts || [];
    if (!n) return cand.map(function (id) { return { id: id, name: COA[id].name, alias: "" }; }).sort(function (a, b) { return a.name < b.name ? -1 : 1; });
    var toks = n.split(" "), out = [];
    ix.list.forEach(function (e) {
      var best = 0, via = 0;
      e.names.forEach(function (x, i) {
        var sc = 0;
        if (x.n === n) sc = 100;
        else if (x.n.indexOf(n) === 0) sc = 85;
        else if (toks.every(function (t) { return x.w.some(function (w) { return w.indexOf(t) === 0; }); })) sc = 65;
        else if (x.n.indexOf(n) >= 0) sc = 40;
        else if (n.length > 2 && x.k.indexOf(n.replace(/ /g, "")) >= 0) sc = 30;
        if (i === 0 && sc) sc += 3;
        if (sc > best) { best = sc; via = i; }
      });
      if (best) out.push({ id: e.id, sc: best + (cand.indexOf(e.id) >= 0 ? 20 : 0), via: via, e: e });
    });
    out.sort(function (a, b) { return b.sc - a.sc || COA[a.id].name.length - COA[b.id].name.length; });
    return out.slice(0, limit || 8).map(function (o) { return { id: o.id, name: COA[o.id].name, alias: o.via > 0 ? o.e.names[o.via].raw : "" }; });
  }
  function jeRowHtml(k) {
    return '<div class="jl" data-r>' +
      '<div class="jl-a"><input class="jl-acct" type="text" role="combobox" aria-autocomplete="list" aria-expanded="false" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="Account" aria-label="Account, line ' + k + '">' +
      '<button type="button" class="jl-rm" aria-label="Remove line ' + k + '" tabindex="-1">×</button></div>' +
      '<label class="jl-m"><span>Debit</span><input class="jl-amt jl-d" type="text" inputmode="decimal" autocomplete="off" aria-label="Debit, line ' + k + '"></label>' +
      '<label class="jl-m"><span>Credit</span><input class="jl-amt jl-c" type="text" inputmode="decimal" autocomplete="off" aria-label="Credit, line ' + k + '"></label></div>';
  }
  function jeHtml(c) {
    return '<div class="jecell" data-c="' + c.id + '" data-je><div class="jl-head" aria-hidden="true"><span>Account</span><span>Debit</span><span>Credit</span></div>' +
      '<div class="jl-rows"></div><div class="jl-foot"><button type="button" class="tb-btn sm" data-add>+ Line</button><span class="jl-bal" aria-live="polite"></span></div></div>';
  }
  function jeFill(box, c) {
    var rows = A.vals[c.id], rw = $(".jl-rows", box), n = rows && rows.length ? rows.length : c.lines.length + 2, h = "";
    for (var i = 0; i < n; i++) h += jeRowHtml(i + 1);
    rw.innerHTML = h;
    if (rows) $$(".jl", rw).forEach(function (row, i) {
      var r = rows[i]; if (!r) return;
      var ai = $(".jl-acct", row);
      if (r.a && COA[r.a]) { ai.value = COA[r.a].name; ai.dataset.id = r.a; } else ai.value = r.tx || "";
      $(".jl-d", row).value = r.d || ""; $(".jl-c", row).value = r.c || "";
    });
    jeBal(box);
  }
  function jeRead(box) {
    return $$(".jl", box).map(function (row) {
      var ai = $(".jl-acct", row);
      return { a: ai.dataset.id || resolveAcct(ai.value) || "", tx: ai.value.trim(), d: $(".jl-d", row).value.trim(), c: $(".jl-c", row).value.trim() };
    });
  }
  function jeBal(box) {
    var d = 0, c = 0;
    $$(".jl", box).forEach(function (row) {
      var x = amt($(".jl-d", row).value), y = amt($(".jl-c", row).value);
      d += x; c += y;
      row.classList.toggle("cr", !!y && !x);
    });
    var el = $(".jl-bal", box), M = window.JEGrade.fmtNum;
    if (!d && !c) { el.textContent = "Debit $0 | Credit $0"; el.className = "jl-bal"; return; }
    if (Math.abs(d - c) < 0.005) { el.textContent = "Balanced $" + M(d); el.className = "jl-bal ok"; return; }
    el.textContent = "Debit $" + M(d) + " | Credit $" + M(c) + " → diff $" + M(Math.abs(d - c)); el.className = "jl-bal off";
  }
  var dd = null, ddIn = null, ddSel = -1, ddItems = [], ddCell = null;
  function ddClose() { if (dd) dd.hidden = true; if (ddIn) ddIn.setAttribute("aria-expanded", "false"); ddIn = null; ddSel = -1; ddItems = []; }
  function ddOpen(input, cell) {
    if (!dd) { dd = document.createElement("div"); dd.className = "jl-dd"; dd.setAttribute("role", "listbox"); dd.hidden = true; }
    ddIn = input; ddCell = cell;
    ddItems = searchAcct(input.value, cell, input.value.trim() ? 8 : 12); ddSel = ddItems.length ? 0 : -1;
    if (!ddItems.length) { dd.hidden = true; return; }
    dd.innerHTML = ddItems.map(function (x, i) {
      return '<div role="option" class="jl-opt' + (i === 0 ? " on" : "") + '" data-i="' + i + '">' + esc(x.name) + (x.alias ? "<small>" + esc(x.alias) + "</small>" : "") + "</div>";
    }).join("");
    input.parentNode.appendChild(dd);
    dd.hidden = false; input.setAttribute("aria-expanded", "true");
  }
  function ddPick(i) {
    var x = ddItems[i], input = ddIn; if (!x || !input) return;
    input.value = x.name; input.dataset.id = x.id; ddClose();
    var row = input.closest(".jl"), d = $(".jl-d", row);
    jeSync(input.closest("[data-je]"));
    if (d) d.focus();
  }
  function ddMove(dir) {
    if (!dd || dd.hidden || !ddItems.length) return;
    ddSel = (ddSel + dir + ddItems.length) % ddItems.length;
    $$(".jl-opt", dd).forEach(function (o, i) { o.classList.toggle("on", i === ddSel); });
    var on = $(".jl-opt.on", dd); if (on && on.scrollIntoView) on.scrollIntoView({ block: "nearest" });
  }
  function jeSync(box) {
    var cid = box.dataset.c;
    A.vals[cid] = jeRead(box); A.cur = cid;
    persist(); paintStones(); barUpdate();
  }
  function focusField(el) { var f = $("[data-c]", el); if (f && !f.matches("input,select")) f = $("input", f); if (f) f.focus(); }

  function cellHtml(c, i) {
    var inp;
    if (c.kind === "number") {
      var pre = c.fmt === "n" || c.fmt === "x2" || c.fmt === "p1" ? "" : '<span class="pre">$</span>', suf = c.fmt === "p1" ? '<span class="pre">%</span>' : c.fmt === "x2" ? '<span class="pre">x</span>' : "";
      inp = '<span class="fld">' + pre + '<input data-c="' + c.id + '" inputmode="decimal" autocomplete="off" aria-labelledby="l-' + c.id + '">' + suf + "</span>";
    } else if (c.kind === "dropdown") inp = '<select data-c="' + c.id + '" aria-labelledby="l-' + c.id + '"><option value="">Select</option>' + c.options.map(function (o) { return '<option value="' + esc(o) + '">' + esc(o) + "</option>"; }).join("") + "</select>";
    else if (c.kind === "je") inp = jeHtml(c);
    else inp = '<span class="fld txt"><input data-c="' + c.id + '" autocomplete="off" spellcheck="false" placeholder="' + (c.norm === "std" ? "ASC 260" : "§1012(a)") + '" aria-labelledby="l-' + c.id + '"></span>';
    return '<article class="cell' + (c.kind === "je" ? " je" : "") + '" id="cell-' + c.id + '"><div class="cl"><span class="n">' + (i + 1) + '</span><label id="l-' + c.id + '">' + esc(c.label) + (c.kind === "je" ? '<span class="pts">' + c.points + " lines</span>" : "") + "</label></div>" +
      '<div class="in">' + inp + "</div>" + (c.kind === "citation" || c.kind === "je" ? '<div class="ask">' + esc(c.ask) + "</div>" : "") +
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
      if (c.kind === "je") { jeWire(el, c); return; }
      if (A.vals[c.id] !== undefined) el.value = A.vals[c.id];
      var onIn = function () { A.vals[c.id] = el.value; persist(); paintStones(); barUpdate(); };
      el.addEventListener("input", onIn); el.addEventListener("change", onIn);
      if (c.kind === "number") {
        el.addEventListener("blur", function () {
          var v = parseNum(unit(el.value, c.fmt));
          if (!isNaN(v) && el.value.trim() !== "") { el.value = numTxt(v, DEC[c.fmt] || 0); A.vals[c.id] = el.value; persist(); }
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
  /* wire one journal-entry cell: rows, autocomplete, balance, add/remove */
  function jeWire(box, c) {
    jeFill(box, c);
    box.addEventListener("input", function (e) {
      var t = e.target;
      if (t.classList.contains("jl-acct")) { delete t.dataset.id; ddOpen(t, c); }
      else if (t.classList.contains("jl-amt")) {
        var row = t.closest(".jl"), other = t.classList.contains("jl-d") ? $(".jl-c", row) : $(".jl-d", row);
        if (t.value && other.value) other.value = "";
        jeBal(box);
      }
      jeSync(box);
    });
    box.addEventListener("focusin", function (e) {
      var t = e.target; A.cur = c.id;
      if (t.classList.contains("jl-acct")) ddOpen(t, c);
    });
    box.addEventListener("focusout", function (e) {
      var t = e.target;
      if (t.classList.contains("jl-acct")) {
        setTimeout(function () { if (ddIn === t) ddClose(); }, 150);
        if (!t.dataset.id) { var id = resolveAcct(t.value); if (id) { t.dataset.id = id; t.value = COA[id].name; } }
        jeSync(box);
      } else if (t.classList.contains("jl-amt")) {
        var n = amt(t.value); if (n) t.value = n.toLocaleString("en-US", { maximumFractionDigits: 2 });
        jeBal(box); jeSync(box);
      }
    });
    box.addEventListener("keydown", function (e) {
      var t = e.target;
      if (t.classList.contains("jl-acct") && dd && !dd.hidden && ddIn === t) {
        if (e.key === "ArrowDown") { e.preventDefault(); ddMove(1); return; }
        if (e.key === "ArrowUp") { e.preventDefault(); ddMove(-1); return; }
        if (e.key === "Enter") { e.preventDefault(); ddPick(ddSel); return; }
        if (e.key === "Escape") { ddClose(); return; }
      }
      if (t.classList.contains("jl-amt") && e.key === "Enter") {
        e.preventDefault();
        var row = t.closest(".jl"), next = row.nextElementSibling;
        if (!next) { row.parentNode.insertAdjacentHTML("beforeend", jeRowHtml(row.parentNode.children.length + 1)); next = row.nextElementSibling; }
        $(".jl-acct", next).focus();
      }
    });
    box.addEventListener("click", function (e) {
      var b = e.target.closest("button"); if (!b) return;
      if (b.hasAttribute("data-add")) {
        var rw = $(".jl-rows", box); rw.insertAdjacentHTML("beforeend", jeRowHtml(rw.children.length + 1));
        $(".jl-acct", rw.lastElementChild).focus(); jeSync(box); return;
      }
      if (b.classList.contains("jl-rm")) {
        var row = b.closest(".jl"), rs = row.parentNode;
        if (rs.children.length > 2) row.remove(); else $$("input", row).forEach(function (i) { i.value = ""; delete i.dataset.id; });
        jeBal(box); jeSync(box);
      }
    });
    box.addEventListener("pointerdown", function (e) {
      var o = e.target.closest && e.target.closest(".jl-opt");
      if (o) { e.preventDefault(); ddPick(+o.dataset.i); }
    });
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
    if (r) return isDone(r.kind);
    return isBlank(A.vals[c.id]) ? "" : "fill";
  }
  function paintStones() {
    var s = $("#stones"); if (!s) return;
    s.innerHTML = R.cells.map(function (c, i) {
      return '<button role="listitem" class="' + stoneClass(c) + (A.cur === c.id ? " cur" : "") + '" data-s="' + c.id + '" aria-label="Cell ' + (i + 1) + '"></button>';
    }).join("");
    $$("[data-s]", s).forEach(function (b) {
      b.onclick = function () { setTab("task"); var el = $("#cell-" + b.dataset.s); el.scrollIntoView({ block: "center" }); focusField(el); };
    });
  }
  /* journal-entry feedback: one row per entered line (wrong part struck through, right value after the arrow), then missing lines */
  var JSTAT = { ok: ["Correct", "ok"], ecf: ["½ Carried forward", "half"], amount: ["Amount", "no"], flip: ["Reversed", "no"], acct: ["Account", "no"], extra: ["Extra", "no"], unknown: ["Unknown", "no"], noamt: ["No amount", "no"] };
  function sideTxt(s) { return s === "D" ? "Debit" : "Credit"; }
  function jeFb(c, r) {
    var d = r.d; if (!d) return "";
    var M = window.JEGrade.fmtNum, h = "";
    if (d.allFlip) h += '<p class="jr-note">Every line is reversed: debits and credits are swapped.</p>';
    h += '<div class="jrs">';
    d.lines.forEach(function (u) {
      var st = JSTAT[u.status] || ["", "no"], nm = u.a ? COA[u.a].name : (u.tx || "(blank)");
      var acct = esc(nm), amtT = u.s ? "$" + M(u.v) : "", side = u.s ? sideTxt(u.s) : "";
      if (u.status === "acct" && u.c) acct = "<del>" + esc(nm) + "</del> → <ins>" + esc(COA[u.c.a].name) + "</ins>";
      if ((u.status === "amount" || u.status === "ecf") && u.c) amtT = "<del>" + amtT + "</del> → <ins>$" + M(u.c.v) + "</ins>";
      if (u.status === "flip" && u.c) side = "<del>" + side + "</del> → <ins>" + sideTxt(u.c.s) + "</ins>";
      var msg = u.msg || (u.status === "ecf" ? "Follows from your earlier entries. This line’s own amount differs." : u.note) || "";
      h += '<div class="jr ' + st[1] + " " + u.status + '"><span class="tag">' + st[0] + '</span><span class="ac">' + acct + '</span><span class="sd">' + side + '</span><b class="am">' + amtT + "</b>" + (msg ? '<p class="msg">' + esc(msg) + "</p>" : "") + "</div>";
    });
    d.missing.forEach(function (m) {
      h += '<div class="jr no miss"><span class="tag">Missing</span><span class="ac">' + esc(COA[m.a].name) + '</span><span class="sd">' + sideTxt(m.s) + '</span><b class="am">$' + M(m.v) + "</b>" + (m.msg ? '<p class="msg">' + esc(m.msg) + "</p>" : "") + "</div>";
    });
    if (!d.lines.length && !d.missing.length) h += '<div class="jr no"><span class="tag">Blank</span></div>';
    return h + "</div>";
  }
  function fbHtml(c, r, v) {
    var h = "";
    if (c.kind === "je") {
      var pts = num(r.credit * c.points);
      h = r.kind === "ok" ? '<span class="st ok">✓ Correct</span>' : r.kind === "blank" ? '<span class="st bad">✗ No entry</span>' :
        '<span class="st ' + (r.credit > 0 ? "half" : "bad") + '">' + (r.credit > 0 ? "½ " : "✗ ") + pts + " of " + c.points + " lines</span>";
      if (r.kind !== "blank") h += jeFb(c, r);
      if (r.rc !== undefined && r.kind !== "ok") h += '<div class="msg">Retry: ✗</div>';
      return h;
    }
    if (r.kind === "ok") return '<span class="st ok">✓ Correct</span>';
    var shown = c.kind === "number" ? (isNaN(parseNum(unit(v, c.fmt))) ? esc(v) : esc(money(parseNum(unit(v, c.fmt)), c.fmt))) : esc(v);
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
    if (c.kind === "je") return c.lines.map(function (l) { return (l.s === "D" ? "Dr " : "Cr ") + COA[l.a].name + " " + window.JEGrade.fmtNum(l.v); }).join("; ");
    return c.accept.map(function (a) { return c.norm === "std" ? a.toUpperCase() : "§" + a; }).join(" → ");
  }
  function explText(c) {
    return c.label + "\nAnswer: " + (c.kind === "je" ? "\n" + c.lines.map(function (l) { return (l.s === "D" ? "  Dr " : "    Cr ") + COA[l.a].name + "  " + window.JEGrade.fmtNum(l.v); }).join("\n") : answerText(c)) + "\n" + c.why +
      (c.kind === "je" ? "\n" + c.lines.map(function (l) { return "- " + COA[l.a].name + ": " + l.why; }).join("\n") : "") +
      (c.steps.length ? "\n" + c.steps.map(function (s, i) { return (i + 1) + ". " + s; }).join("\n") : "") +
      (c.cite ? "\nSource: " + c.cite : "") + (c.link ? "\n" + c.link : "");
  }
  function jeAnswerHtml(c) {
    var M = window.JEGrade.fmtNum;
    return '<table class="jl-ans"><thead><tr><th>Account</th><th>Debit</th><th>Credit</th></tr></thead><tbody>' + c.lines.map(function (l) {
      return "<tr" + (l.s === "C" ? ' class="cr"' : "") + "><td>" + esc(COA[l.a].name) + "</td><td>" + (l.s === "D" ? M(l.v) : "") + "</td><td>" + (l.s === "C" ? M(l.v) : "") + "</td></tr>" +
        '<tr class="why"><td colspan="3">' + esc(l.why) + "</td></tr>";
    }).join("") + "</tbody></table>";
  }
  function linkHtml(c) {
    if (c.link) {
      var host = ""; try { host = new URL(c.link).hostname; } catch (e) { host = ""; }
      return '<div class="lnk">Source: <a href="' + esc(c.link) + '" target="_blank" rel="noopener noreferrer">' + esc(c.cite || host || "Open") + " ↗</a></div>";
    }
    return c.cite ? '<div class="lnk">Source: ' + esc(c.cite) + "</div>" : "";
  }
  function paintCell(c) {
    var el = $("#cell-" + c.id), r = A.res[c.id];
    el.className = "cell" + (c.kind === "je" ? " je" : "") + (r ? " " + isDone(r.kind) : "");
    var lock = A.submitted || !!(r && (r.kind === "ok" || A.shown[c.id])) || (A.done && !retryable(c));
    if (c.kind === "je") $$("input,button", $(".jecell", el)).forEach(function (x) { x.disabled = lock; });
    else $("[data-c]", el).disabled = lock;
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
      ex.innerHTML = (c.kind === "je" ? "<div>Answer</div>" + jeAnswerHtml(c) : "<div>Answer <ins>" + esc(answerText(c)) + "</ins></div>") + "<p style=\"margin:6px 0\">" + esc(c.why) + "</p>" +
        (c.steps.length ? "<ol>" + c.steps.map(function (s) { return "<li>" + esc(s) + "</li>"; }).join("") + "</ol>" : "") +
        linkHtml(c) + '<div class="cp"><button class="tb-btn sm" data-a="cp">Copy</button></div>';
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
  function mkRes(g, raw, h) { return { kind: g.kind, credit: g.credit, msg: g.msg, v: raw, t: A.secs, h: h || 0, d: g.detail || null }; }
  function checkCell(cid, quiet) {
    var c = cellById(cid), prev = A.res[cid], raw = A.vals[cid];
    if (isBlank(raw)) { if (!quiet) toast("No entry"); return false; }
    var g = gradeCell(R, c, A.vals);
    if (prev) {
      if (prev.kind === "ok" || isExam()) return true;
      prev.kind = g.kind; prev.msg = g.msg; prev.v = raw; prev.stale = false; prev.d = g.detail || null;
      prev.rc = Math.max(prev.rc || 0, g.credit * 0.5);
    } else {
      A.res[cid] = mkRes(g, raw, A.hints[cid]);
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
      if (isBlank(A.vals[c.id])) A.res[c.id] = { kind: "blank", credit: 0, msg: "", v: "", t: A.secs, h: A.hints[c.id] || 0 };
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
    if (first) { setTab("task"); var el = $("#cell-" + first.id); el.scrollIntoView({ block: "center" }); focusField(el); }
  }
  function wrongCount() { return R.cells.filter(function (c) { var r = A.res[c.id]; return r && r.kind !== "ok" && !A.shown[c.id]; }).length; }
  function answeredCount() { return R.cells.filter(function (c) { return !isBlank(A.vals[c.id]); }).length; }
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
      if (isBlank(raw)) { A.res[c.id] = { kind: "blank", credit: 0, msg: "", v: "", t: A.secs, h: 0 }; return; }
      A.res[c.id] = mkRes(gradeCell(R, c, A.vals), raw, 0);
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
  function srcText(cite) {
    return (cite || []).map(function (x) { return typeof x === "string" ? x : x.src + " " + x.ref; }).join(" → ");
  }
  function showResult() {
    var res = $("#res"); res.hidden = false;
    var sc = score(), pct = Math.round(sc.s / sc.max * 100), hints = sum(A.hints);
    var h = '<div class="big">' + num(sc.s) + " / " + sc.max + "<small>" + pct + "%</small></div><dl>";
    h += "<dt>Time</dt><dd>" + mmss(A.secs) + " → est " + item.est_minutes + " min → exam avg 18 min</dd>";
    if (!isExam()) h += "<dt>Hints</dt><dd>" + hints + "</dd>";
    if (sc.s2 > sc.s) h += "<dt>After retry</dt><dd>" + num(sc.s2) + " / " + sc.max + "</dd>";
    h += "<dt>Mode</dt><dd>" + (isExam() ? "Exam" : "Practice") + (A.seed ? " → variant #" + A.seed : "") + "</dd>";
    if (item.exam === "FAR" && item.cite && item.cite.length) h += "<dt>Sources</dt><dd>" + esc(srcText(item.cite)) + "</dd>";
    h += "</dl>";
    h += '<ul class="cellrows">' + R.cells.map(function (c, i) {
      var r = A.res[c.id]; var k = isDone(r.kind), mark = k === "ok" ? "✓" : k === "half" ? "½" : "✗";
      var lab = c.label.length > 70 ? c.label.slice(0, 68) + "…" : c.label;
      var pts = c.kind === "je" ? '<span class="rp">' + num(r.credit * c.points) + "/" + c.points + "</span>" : "";
      return '<li><b>' + (i + 1) + "</b><span class=\"" + (k === "bad" ? "bad" : "") + '">' + mark + "</span><span>" + esc(lab) + "</span>" + pts + "</li>";
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
    ddClose();
    var m = /^#\/([^\/]+)(?:\/(\d+))?(?:\/(new))?$/.exec(location.hash);
    if (!m) { listView(); return; }
    var seed = m[2] === undefined ? null : +m[2];
    openItem(m[1], seed, m[3] === "new");
    if (m[3]) history.replaceState(null, "", "#/" + m[1] + "/" + seed);
  }
  window.addEventListener("hashchange", route);
  window.addEventListener("beforeunload", function () { if (A) save(); });
  window.TBSApp = { get S() { return S; }, get A() { return A; }, get R() { return R; }, get SEC() { return SEC; }, checkCell: checkCell };
  route();
})();
