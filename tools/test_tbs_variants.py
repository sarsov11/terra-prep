# -*- coding: utf-8 -*-
"""Check that the browser engine (js/tbs.js) and the Python sources of truth agree, for REG and FAR.

    py tools/build_tbs.py --no-fetch     (data/tbs_reg.js and data/tbs_far.js must be current)
    py tools/test_tbs_variants.py [n_variants=50]

REG: tools/src/TBS/tbs_lib.py.  FAR: tools/src/TBS/tbs_far_lib.py (journal-entry cells, decimal formats, annuity functions,
ASC/GASB numbers).  For every TBS and n seeds: Python picks the variant numbers and renders the full TBS; the browser renders
the same numbers with TBSEngine.render and everything must match: filled texts, exhibits, answers, trap values, dropdown
answers, citation lists, journal-entry lines/mistake rules/hints. Grading (incl. carry-forward and line-by-line journal
credit) is compared with the Python grade on mixed right/wrong entries. Also: the browser's own seeded picker must satisfy
every guard, and a perfect entry must score full marks. Needs Playwright + Edge (no Node). Exit code 0 = pass.
"""
import json, os, random, sys, copy, re
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "src", "TBS")
sys.path.insert(0, SRC)
from tbs_lib import variant as reg_variant, grade as reg_grade, norm_cite
import tbs_far_lib as FL
import tbs_items_1, tbs_items_3, tbs_items_4, tbs_items_5
from playwright.sync_api import sync_playwright

N = int(sys.argv[1]) if len(sys.argv) > 1 else 50
REG_RAW = {t["id"]: t for m in (tbs_items_1, tbs_items_3, tbs_items_4, tbs_items_5) for t in m.ITEMS}
REG_BASE = {t["id"]: t for t in json.load(open(os.path.join(SRC, "tbs_reg.json"), encoding="utf-8"))["items"]}
FAR_JSON = json.load(open(os.path.join(SRC, "tbs_far.json"), encoding="utf-8"))
FAR_BASE = {t["id"]: t for t in FAR_JSON["items"]}
FAR_RAW = {}
for t in FAR_JSON["items"]:                      # raw template form = item with its "template" fields put back
    r = dict(t)
    r.update(t["template"])
    FAR_RAW[t["id"]] = r


def digest(v, far):
    """Comparable view of a rendered TBS (option order and wrong-message keys ignored)."""
    cells = []
    for c in v["cells"]:
        d = {"id": c["id"], "kind": c["kind"], "label": c["label"], "why": c["why"], "steps": c["steps"], "hints": c["hints"]}
        if c["kind"] == "number":
            d.update(answer=c["answer"], tol=c["tol"], deps=c["deps"], traps=[[t["value"], t["msg"]] for t in c["traps"]])
            if far:
                d["fmt"] = c["fmt"]
        elif c["kind"] == "dropdown":
            d.update(answer=c["answer"], options=sorted(c["options"]), wrong=sorted(c["wrong_msgs"].values()))
        elif c["kind"] == "je":
            d.update(ask=c["ask"], accounts=c["accounts"], tol=c["tol"], points=c["points"],
                     lines=[[l["s"], l["a"], l["v"], l["why"], l["alt"], l["deps"]] for l in c["lines"]],
                     mist=[[m["k"], m["a"], m.get("b"), m.get("v"), m["msg"]] for m in c["mist"]])
        else:
            d.update(accept=c["accept"], partial=c["partial"])
            if far:
                d.update(ask=c["ask"], norm=c.get("norm", ""), link=c.get("link", ""))
        cells.append(d)
    return {"title": v["title"], "scenario": v["scenario"], "task": v["task"], "exhibits": v["exhibits"], "cells": cells}


# ───────────── REG entries (as before) ─────────────
def reg_entries(v, rng):
    e = {}
    for c in v["cells"]:
        r = rng.random()
        if c["kind"] == "number":
            if r < .35: e[c["id"]] = str(c["answer"])
            elif r < .6: e[c["id"]] = str(c["answer"] + rng.choice([-1000, -1, 1, 7, 250]))
            elif r < .75: e[c["id"]] = ""
            else: e[c["id"]] = str(rng.choice([0, 100, 5000, -300]))
        elif c["kind"] == "dropdown":
            e[c["id"]] = c["answer"] if r < .5 else rng.choice(c["options"])
        else:
            pool = ["IRC §" + c["accept"][0], "Sec. " + c["accept"][0], c["accept"][0].upper(), "IRC 9999", "26 U.S.C. " + c["accept"][0]] + (["§" + c["partial"][0]] if c["partial"] else [])
            e[c["id"]] = rng.choice(pool)
    return e


# ───────────── FAR entries ─────────────
def far_fmt(v, fmt):
    d = FL.DEC[fmt]
    return ("%.*f" % (d, v)) if d else str(int(v))


def far_entries(v, p, rng):
    """Mixed right / off / carried-forward entries for every cell kind, with plain numbers (unit suffixes are tested separately)."""
    e, loc = {}, FL.build_ns(p, v["derived"])
    for c in v["cells"]:
        r = rng.random()
        cid = c["id"]
        if c["kind"] == "number":
            tol = c["tol"]
            if r < .3:
                x = c["answer"]
            elif r < .45:
                x = c["answer"] + rng.choice([-tol, tol, tol * 0.5, 1000, -1000, 7])
            elif r < .6 and c["deps"]:
                try:
                    x = FL.rd(FL._ev(c["expr"], loc), FL.DEC[c["fmt"]])          # follows from the learner's earlier values (ECF)
                except Exception:
                    x = c["answer"]
            elif r < .7:
                e[cid] = ""
                loc[cid] = c["answer"]
                continue
            elif r < .8 and c["traps"]:
                x = rng.choice(c["traps"])["value"]
            else:
                x = rng.choice([0, 100, 5000, -300, 12.5])
            s = far_fmt(x, c["fmt"]) if isinstance(x, (int, float)) and rng.random() < .5 else str(x)
            e[cid] = s
            pv = FL.parse_num(s)
            loc[cid] = c["answer"] if pv != pv else pv
        elif c["kind"] == "dropdown":
            e[cid] = c["answer"] if r < .5 else rng.choice(c["options"])
        elif c["kind"] == "citation":
            a = c["accept"][0]
            pool = ["ASC " + a, "FASB ASC Topic " + a, "topic " + a, a.upper(), a + "-10-25", "GASB Statement No. " + a, "GASB " + a, "ASC 9999", "§" + a, a + "-1b"]
            if c["partial"]:
                pool += ["ASC " + c["partial"][0], c["partial"][0]]
            e[cid] = rng.choice(pool)
        else:
            e[cid] = je_rows(c, loc, rng)
    return e


def je_rows(c, loc, rng):
    ids = list(FL.COA)
    if rng.random() < .25:
        return []
    rows = []
    for l in c["lines"]:
        r = rng.random()
        a, s, amt = l["a"], l["s"], l["v"]
        if r < .1:
            s = "C" if s == "D" else "D"
        elif r < .22:
            amt = amt + rng.choice([1, 500, 10000])
        elif r < .3:
            a = rng.choice(ids)
        elif r < .38:
            continue
        elif r < .5 and l["deps"]:
            amt = max(1, FL.rnd(FL._ev(l["expr"], loc)))                               # ECF path: amount from the learner's earlier cells
        elif r < .56:
            rows.append({"a": l["a"], "d": amt if s == "D" else 0, "c": amt if s == "C" else 0})
            amt = max(1, amt // 2)
        elif r < .62 and l["alt"]:
            a = l["alt"][0]
        rows.append({"a": a, "d": amt if s == "D" else 0, "c": amt if s == "C" else 0})
    if rng.random() < .3:
        rows.append({"a": rng.choice(ids), "d": 100, "c": 0})
    if rng.random() < .08:
        rows.append({"a": None, "d": 0, "c": 50})
    if rng.random() < .5:
        rng.shuffle(rows)
    return rows


def far_perfect(v):
    out = {}
    for c in v["cells"]:
        if c["kind"] == "number": out[c["id"]] = far_fmt(c["answer"], c["fmt"])
        elif c["kind"] == "dropdown": out[c["id"]] = c["answer"]
        elif c["kind"] == "citation": out[c["id"]] = c["accept"][0]
        else: out[c["id"]] = FL.answer_rows(c)
    return out


reg_cases, far_cases, base_cases = [], [], []
rng = random.Random(7)
for tid, raw in REG_RAW.items():
    b = REG_BASE[tid]
    base_cases.append({"id": tid, "params": b["params"], "exp": digest(b, False), "opts": [c["options"] for c in b["cells"] if c["kind"] == "dropdown"]})
    for seed in range(N):
        v, p = reg_variant(raw, seed)
        ent = reg_entries(v, rng)
        v2 = copy.deepcopy(v)
        v2["params"] = p
        # tbs_lib.grade treats an unentered earlier cell as 0 when re-solving (ECF); the browser keeps the correct value for it.
        filled = {k: x for k, x in ent.items() if x != ""}
        for c in v["cells"]:
            if c["kind"] == "number" and c["id"] not in filled:
                filled[c["id"]] = str(c["answer"])
        py_res = reg_grade(v2, filled)
        for c in v["cells"]:
            if ent[c["id"]] == "":
                py_res[c["id"]] = 0.0
        reg_cases.append({"id": tid, "seed": seed, "params": p, "exp": digest(v, False), "entries": ent,
                          "credit": {c["id"]: py_res[c["id"]] for c in v["cells"]},
                          "perfect": {c["id"]: (str(c["answer"]) if c["kind"] != "citation" else c["accept"][0]) if c["kind"] != "dropdown" else c["answer"] for c in v["cells"]}})
for tid, raw in FAR_RAW.items():
    b = FAR_BASE[tid]
    base_cases.append({"id": tid, "params": b["params"], "exp": digest(b, True), "opts": [c["options"] for c in b["cells"] if c["kind"] == "dropdown"]})
    for seed in range(N):
        v, p = FL.variant(raw, seed)
        ent = far_entries(v, p, rng)
        v2 = copy.deepcopy(v)
        v2["params"] = p  # like REG: grade() re-solves with v["params"], which variant() leaves at the base numbers
        res = FL.grade(v2, ent)
        far_cases.append({"id": tid, "seed": seed, "params": p, "exp": digest(v, True), "entries": ent,
                          "credit": {k: x[0] for k, x in res.items()}, "kind": {k: x[1] for k, x in res.items()}, "perfect": far_perfect(v)})
print("python: REG %d x %d + FAR %d x %d = %d cases" % (len(REG_RAW), N, len(FAR_RAW), N, len(reg_cases) + len(far_cases)))

JS = r"""
async ({regCases, farCases, baseCases, n}) => {
  const E = window.TBSEngine, items = {}; ['REG', 'FAR'].forEach(k => TBS_SETS[k].items.forEach(t => items[t.id] = t));
  const bad = [];
  const dig = (v, far) => ({title: v.title, scenario: v.scenario, task: v.task, exhibits: v.exhibits, cells: v.cells.map(c => {
    const d = {id: c.id, kind: c.kind, label: c.label, why: c.why, steps: c.steps, hints: c.hints};
    if (c.kind === 'number') { d.answer = c.answer; d.tol = c.tol; d.deps = c.deps; d.traps = c.traps.map(t => [t.value, t.msg]); if (far) d.fmt = c.fmt; }
    else if (c.kind === 'dropdown') { d.answer = c.answer; d.options = c.options.slice().sort(); d.wrong = Object.values(c.wrong).sort(); }
    else if (c.kind === 'je') { d.ask = c.ask; d.accounts = c.accounts; d.tol = c.tol; d.points = c.points;
      d.lines = c.lines.map(l => [l.s, l.a, l.v, l.why, l.alt, l.deps]); d.mist = c.mist.map(m => [m.k, m.a, m.b === undefined ? null : m.b, m.v === undefined ? null : m.v, m.msg]); }
    else { d.accept = c.accept; d.partial = c.partial; if (far) { d.ask = c.ask; d.norm = c.norm; d.link = c.link; } }
    return d; })});
  const cmp = (tag, a, b) => { const x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) { let i = 0; while (x[i] === y[i]) i++; bad.push(tag + ' @' + i + ' js=' + x.slice(Math.max(0, i - 40), i + 60) + ' | py=' + y.slice(Math.max(0, i - 40), i + 60)); } };
  let nGrade = 0, nCells = 0, nJe = 0;
  for (const b of baseCases) {
    const far = items[b.id].exam === 'FAR';
    const r = E.render(items[b.id], items[b.id].params, 0);
    cmp('base ' + b.id, dig(r, far), b.exp);
    cmp('base opts ' + b.id, r.cells.filter(c => c.kind === 'dropdown').map(c => c.options), b.opts);
  }
  const all = regCases.map(c => Object.assign({far: false}, c)).concat(farCases.map(c => Object.assign({far: true}, c)));
  for (const c of all) {
    const it = items[c.id], tag = c.id + ' seed ' + c.seed;
    let r; try { r = E.render(it, c.params, c.seed + 1); } catch (e) { bad.push(tag + ' render error ' + e.message); continue; }
    cmp(tag, dig(r, c.far), c.exp);
    for (const cell of r.cells) {
      nCells++;
      const g = E.gradeCell(r, cell, c.entries);
      nGrade++; if (cell.kind === 'je') nJe++;
      if (Math.abs(g.credit - c.credit[cell.id]) > 1e-9) bad.push(tag + ' grade ' + cell.id + ' js=' + g.credit + ' py=' + c.credit[cell.id] + ' entry=' + JSON.stringify(c.entries[cell.id]) + ' all=' + JSON.stringify(c.entries) + ' params=' + JSON.stringify(c.params));
      if (c.far && cell.kind !== 'je' && c.kind[cell.id] !== g.kind) bad.push(tag + ' kind ' + cell.id + ' js=' + g.kind + ' py=' + c.kind[cell.id]);
      if (c.far && cell.kind === 'je' && ((c.kind[cell.id] === 'ok') !== (g.kind === 'ok'))) bad.push(tag + ' je perfect flag ' + cell.id + ' js=' + g.kind + ' py=' + c.kind[cell.id]);
      const pg = E.gradeCell(r, cell, c.perfect);
      if (pg.credit !== 1) bad.push(tag + ' perfect entry not 1: ' + cell.id + ' ' + JSON.stringify(c.perfect[cell.id]));
    }
  }
  // browser's own picker: guards hold, perfect entries score full marks, no leftover placeholders, ledger lines balance
  let own = 0, balanced = 0;
  for (const id in items) {
    const it = items[id], far = it.exam === 'FAR';
    for (let s = 1; s <= n; s++) {
      const p = E.pickParams(it, s * 7919 + 3), ns = E.buildNs(p, it.derived, far);
      if (!it.guards.every(g => E.ev(g, ns))) bad.push('own guard ' + id + ' ' + s);
      const r = E.render(it, p, s);
      if (/\{[a-z_0-9]+(:,|:[0-9])?\}/i.test(JSON.stringify(r))) bad.push('placeholder left ' + id + ' ' + s);
      const perfect = {};
      r.cells.forEach(c => { perfect[c.id] = c.kind === 'number' ? String(c.answer) : c.kind === 'dropdown' ? c.answer : c.kind === 'citation' ? c.accept[0] :
        c.lines.map(l => ({a: l.a, d: l.s === 'D' ? l.v : 0, c: l.s === 'C' ? l.v : 0})); });
      r.cells.forEach(c => {
        if (c.kind === 'je') { const dr = c.lines.filter(l => l.s === 'D').reduce((a, l) => a + l.v, 0), cr = c.lines.filter(l => l.s === 'C').reduce((a, l) => a + l.v, 0); if (Math.abs(dr - cr) > 1) bad.push('unbalanced je ' + id + ' ' + c.id + ' ' + s); else balanced++; }
        if (E.gradeCell(r, c, perfect).credit !== 1) bad.push('own perfect ' + id + ' ' + c.id + ' ' + s);
      });
      own++;
    }
  }
  const cites = [['IRC §6694(a)', '6694(a)'], ['Sec. 6694 (a)', '6694(a)'], ['26 U.S.C. 6694(a)', '6694(a)'], ['Internal Revenue Code section 6694(a)', '6694(a)'], ['31 CFR §10.29', '10.29'], ['Circular 230 § 10.29', '10.29'], ['IRC 1367(a)(2).', '1367(a)(2)'], ['§ 280A(d)(1)', '280a(d)(1)'], ['1012(a)', '1012(a)'], ['IRC 1012(a)', '1012(a)'], ['§1012(a)', '1012(a)']];
  cites.forEach(([a, b]) => { if (E.normCite(a) !== b) bad.push('normCite ' + a + ' -> ' + E.normCite(a)); });
  const std = [['FASB ASC Topic 260', '260'], ['ASC 205-20-45-1B', '205-20-45-1b'], ['GASB Statement No. 34', '34'], ['GASB 34', '34'], ['ASC 606-10-25-1', '606-10-25-1'], ['Topic 842', '842'], ['ASC §230–10', '230-10']];
  std.forEach(([a, b]) => { if (E.normStd(a) !== b) bad.push('normStd ' + a + ' -> ' + E.normStd(a)); });
  // unit suffixes typed by the learner (p1 percent, x2 ratio) and the 1e-9 tolerance edge
  const far1 = Object.values(items).filter(t => t.exam === 'FAR');
  let unitsSeen = 0;
  far1.forEach(it => { const r = E.render(it, it.params, 0); r.cells.forEach(c => {
    if (c.kind !== 'number' || (c.fmt !== 'p1' && c.fmt !== 'x2')) return;
    const txt = c.fmt === 'p1' ? c.answer.toFixed(1) + '%' : c.answer.toFixed(2) + 'x', e = {}; e[c.id] = txt;
    if (E.gradeCell(r, c, e).credit !== 1) bad.push('unit entry ' + it.id + ' ' + c.id + ' ' + txt); unitsSeen++; }); });
  return {bad, nGrade, nCells, nJe, own, balanced, unitsSeen};
}
"""

# Python side of the citation tables
for s, exp in [("IRC §6694(a)", "6694(a)"), ("Sec. 6694 (a)", "6694(a)"), ("26 U.S.C. 6694(a)", "6694(a)"), ("31 CFR §10.29", "10.29"), ("§1012(a)", "1012(a)"), ("IRC 1012(a)", "1012(a)")]:
    assert norm_cite(s) == exp, (s, norm_cite(s))
for s, exp in [("FASB ASC Topic 260", "260"), ("ASC 205-20-45-1B", "205-20-45-1b"), ("GASB Statement No. 34", "34"), ("GASB 34", "34"), ("ASC 606-10-25-1", "606-10-25-1"), ("Topic 842", "842"), ("ASC §230–10", "230-10")]:
    assert FL.norm_std(s) == exp, (s, FL.norm_std(s))

with sync_playwright() as pw:
    br = pw.chromium.launch(channel="msedge")
    pg = br.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.set_content("<!doctype html><html><body></body></html>")
    for f in ("data/tbs_reg.js", "data/tbs_far.js", "js/jegrade.js", "js/tbs.js"):
        pg.add_script_tag(path=os.path.join(ROOT, f))
    out = pg.evaluate(JS, {"regCases": reg_cases, "farCases": far_cases, "baseCases": base_cases, "n": N})
    # no br.close(): closing Edge can drop the driver connection on this PC; leaving the with-block stops it

print("browser: %d cells graded (%d journal-entry cells), %d own-picker variants, %d balanced entries, %d unit entries" % (out["nCells"], out["nJe"], out["own"], out["balanced"], out["unitsSeen"]))
for b in out["bad"][:40]:
    print("FAIL", b)
for e in errs:
    print("PAGEERROR", e)
if out["bad"] or errs:
    print("FAILED: %d mismatches" % len(out["bad"]))
    sys.exit(1)
print("PASS: JS and Python agree on %d variants x (%d REG + %d FAR) TBS (texts, answers, traps, hints, journal lines, grading incl. carry-forward)" % (N, len(REG_RAW), len(FAR_RAW)))
