/* Journal-entry grader shared by the Journal Drill (js/je.js) and the TBS journal-entry cell (js/tbs.js).
   JEGrade.make(COA) -> { grade(set, mist, tol, rows), near, norm, fmtNum }.
   set.lines: [{a, s: "D"|"C", v, alt?, av?}]. rows: [{a, tx?, d, c}] (d, c numbers).
   Optional line.av = the amount recomputed from the learner's earlier answers (TBS carry-forward). When the entered
   amount misses v but matches av, the line counts JE_ECF (0.75) and is marked "ecf". Without av the behavior is the
   plain drill grader. Python twin for TBS: tbs_far_lib.py grade_je(). */
(function () {
  "use strict";
  var JE_ECF = 0.75;
  function norm(s) {
    return String(s || "").toLowerCase().replace(/&/g, " and ").replace(/[^a-z0-9$ ]+/g, " ").replace(/\s+/g, " ").trim();
  }
  function commas(s) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  function fmtNum(v) {
    if (Math.abs(v - Math.round(v)) < 1e-9) return (v < 0 ? "-" : "") + commas(String(Math.floor(Math.abs(v) + 0.5)));
    var s = Math.abs(v).toFixed(2).split("."); return (v < 0 ? "-" : "") + commas(s[0]) + "." + s[1];
  }
  function fmtMoney(v) { return "$" + fmtNum(v); }
  function near(a, b, tol) { return Math.abs(a - b) <= Math.max(tol, Math.abs(b) * 0.0001) + 1e-9; }
  function sideWord(s) { return s === "D" ? "debit" : "credit"; }

  function make(COA) {
    function findRule(mist, k, a, b, val, tol) {
      for (var i = 0; i < mist.length; i++) {
        var m = mist[i]; if (m.k !== k) continue;
        if (a !== undefined && m.a !== a) continue;
        if (b !== undefined && m.b !== b) continue;
        if (val !== undefined && !(m.v !== undefined && near(m.v, val, tol))) continue;
        return m;
      }
      return null;
    }
    function grade(set, mist, tol, rows) {
      mist = mist || []; tol = tol || 1;
      var corr = set.lines.map(function (l, i) { return { i: i, a: l.a, s: l.s, v: l.v, alt: l.alt || [], av: (l.av === undefined || l.av === null) ? null : l.av, done: false }; });
      var uls = [], byKey = {};
      rows.forEach(function (r, ri) {
        var has = r.a || r.tx || r.d || r.c;
        if (!has) return;
        var parts = [];
        if (r.d) parts.push(["D", r.d]);
        if (r.c) parts.push(["C", r.c]);
        if (!parts.length) { uls.push({ rows: [ri], a: r.a, tx: r.tx, s: null, v: 0, status: "noamt", done: true }); return; }
        parts.forEach(function (p) {
          var key = (r.a || "?" + norm(r.tx)) + "|" + p[0];
          if (byKey[key]) { byKey[key].v += p[1]; byKey[key].rows.push(ri); }
          else { var u = { rows: [ri], a: r.a, tx: r.tx, s: p[0], v: p[1], status: null, done: false }; byKey[key] = u; uls.push(u); }
        });
      });
      function pair(u, c, status, extra) {
        u.done = true; if (c) c.done = true; u.c = c; u.status = status;
        if (extra) for (var k in extra) u[k] = extra[k];
      }
      /* 1) accounts posted on both sides in the answer may be entered as one netted line */
      var sameAcct = {};
      corr.forEach(function (c) { (sameAcct[c.a] = sameAcct[c.a] || []).push(c); });
      Object.keys(sameAcct).forEach(function (a) {
        var cs = sameAcct[a]; if (cs.length < 2) return;
        var net = cs.reduce(function (t, c) { return t + (c.s === "D" ? c.v : -c.v); }, 0);
        var mine = uls.filter(function (u) { return !u.done && u.a === a; });
        if (mine.length === 1 && mine[0].s === (net >= 0 ? "D" : "C") && near(mine[0].v, Math.abs(net), tol)) {
          pair(mine[0], cs[0], "ok", { note: "Net of the two lines accepted" }); cs.forEach(function (c) { c.done = true; });
        }
      });
      /* 2) same account, same side */
      corr.forEach(function (c) {
        if (c.done) return;
        var acc = [c.a].concat(c.alt);
        for (var i = 0; i < uls.length; i++) {
          var u = uls[i];
          if (u.done || !u.a || u.s !== c.s || acc.indexOf(u.a) < 0) continue;
          var alt = u.a !== c.a ? "Accepted alternative: " + COA[u.a].name : "";
          if (Math.abs(u.v - c.v) < 0.005) pair(u, c, "ok", { note: alt });
          else if (near(u.v, c.v, tol)) pair(u, c, "ok", { note: (alt ? alt + ". " : "") + "Within rounding" });
          else if (c.av !== null && near(u.v, c.av, tol)) pair(u, c, "ecf", { note: alt });
          else {
            var rule = findRule(mist, "amt", c.a, undefined, u.v, tol);
            pair(u, c, "amount", { msg: rule ? rule.msg : "Right account and side. Amount is off by " + fmtMoney(Math.abs(u.v - c.v)) + "." });
          }
          return;
        }
      });
      /* 3) same account, opposite side */
      corr.forEach(function (c) {
        if (c.done) return;
        var acc = [c.a].concat(c.alt);
        for (var i = 0; i < uls.length; i++) {
          var u = uls[i];
          if (u.done || !u.a || u.s === c.s || acc.indexOf(u.a) < 0) continue;
          var rule = findRule(mist, "swap", c.a);
          var inc = c.s === COA[c.a].n;
          pair(u, c, "flip", { msg: rule ? rule.msg : COA[c.a].name + " " + (inc ? "increases" : "decreases") + " here, so it is a " + sideWord(c.s) + "." });
          return;
        }
      });
      /* 4) another account on the same side: substitution (rule first, else equal amount) */
      corr.forEach(function (c) {
        if (c.done) return;
        var pick = -1;
        for (var i = 0; i < uls.length; i++) {
          var u = uls[i];
          if (u.done || !u.a || u.s !== c.s) continue;
          if (findRule(mist, "sub", c.a, u.a)) { pick = i; break; }
        }
        if (pick < 0) for (var j = 0; j < uls.length; j++) {
          var w = uls[j];
          if (!w.done && w.a && w.s === c.s && near(w.v, c.v, tol)) { pick = j; break; }
        }
        if (pick >= 0) {
          var u2 = uls[pick], rule = findRule(mist, "sub", c.a, u2.a);
          pair(u2, c, "acct", { msg: rule ? rule.msg : "Different account expected on this line." });
        }
      });
      /* 5) leftovers */
      uls.forEach(function (u) {
        if (u.done) return;
        u.done = true;
        if (!u.a) { u.status = "unknown"; u.msg = "Account not recognized. Pick from the list."; return; }
        var rule = findRule(mist, "extra", u.a);
        u.status = "extra"; u.msg = rule ? rule.msg : "Not part of this entry.";
      });
      var missing = [];
      corr.forEach(function (c) {
        if (c.done) return;
        var rule = findRule(mist, "miss", c.a);
        missing.push({ c: c, msg: rule ? rule.msg : "Missing line." });
      });
      var pts = 0, extras = 0, allOk = true, flips = 0, paired = 0;
      uls.forEach(function (u) {
        if (u.status === "ok") pts += 1;
        else if (u.status === "ecf") { pts += JE_ECF; allOk = false; }
        else if (u.status === "amount") { pts += 0.5; allOk = false; }
        else if (u.status === "noamt") { /* ignored */ }
        else { allOk = false; if (u.status === "extra" || u.status === "unknown") extras++; }
        if (u.status === "flip") flips++;
        if (u.c) paired++;
      });
      /* an entry with several netted correct lines counts every answer line it covers */
      var covered = corr.filter(function (c) { return c.done; }).length;
      var okLines = uls.filter(function (u) { return u.status === "ok"; }).length;
      if (covered > paired) pts += (covered - paired);   /* netted pairs credit the extra covered line */
      var score = Math.max(0, pts - 0.5 * extras) / corr.length;
      if (score > 1) score = 1;
      var perfect = allOk && missing.length === 0 && extras === 0 && Math.abs(score - 1) < 1e-9;
      return { lines: uls, missing: missing, score: score, perfect: perfect, allFlip: flips > 0 && flips === uls.filter(function (u) { return u.status !== "noamt"; }).length && missing.length === 0, n: corr.length, okLines: okLines };
    }
    return { grade: grade, near: near, norm: norm, fmtNum: fmtNum, fmtMoney: fmtMoney, findRule: findRule };
  }
  window.JEGrade = { make: make, JE_ECF: JE_ECF, near: near, norm: norm, fmtNum: fmtNum };
})();
