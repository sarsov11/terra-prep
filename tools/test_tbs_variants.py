# -*- coding: utf-8 -*-
"""Check that the browser engine (js/tbs.js) and the Python source of truth (tools/src/TBS/tbs_lib.py) agree.

    py tools/build_tbs.py --no-fetch     (data/tbs_reg.js must be current)
    py tools/test_tbs_variants.py [n_variants=50]

For every TBS and n seeds: Python picks the variant numbers (tbs_lib.variant) and renders the full TBS;
the browser renders the same numbers with TBSEngine.render and everything must match: filled texts, exhibits,
answers, trap values, dropdown answers, citation lists. Grading (incl. carry-forward) is compared with tbs_lib.grade
on mixed right/wrong entries. Also: the browser's own seeded picker must satisfy every guard, and a perfect entry
must score full marks. Needs Playwright + Edge. Exit code 0 = pass.
"""
import json, os, random, sys, copy
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "src", "TBS")
sys.path.insert(0, SRC)
from tbs_lib import variant, render, grade, norm_cite, solve
import tbs_items_1, tbs_items_3, tbs_items_4, tbs_items_5
from playwright.sync_api import sync_playwright

N = int(sys.argv[1]) if len(sys.argv) > 1 else 50
RAW = {t["id"]: t for m in (tbs_items_1, tbs_items_3, tbs_items_4, tbs_items_5) for t in m.ITEMS}
data = json.load(open(os.path.join(SRC, "tbs_reg.json"), encoding="utf-8"))
BASE = {t["id"]: t for t in data["items"]}


def digest(v):
    """Comparable view of a rendered TBS (option order and wrong-message keys ignored)."""
    cells = []
    for c in v["cells"]:
        d = {"id": c["id"], "kind": c["kind"], "label": c["label"], "why": c["why"], "steps": c["steps"], "hints": c["hints"]}
        if c["kind"] == "number":
            d.update(answer=c["answer"], tol=c["tol"], deps=c["deps"], traps=[[t["value"], t["msg"]] for t in c["traps"]])
        elif c["kind"] == "dropdown":
            d.update(answer=c["answer"], options=sorted(c["options"]), wrong=sorted(c["wrong_msgs"].values()))
        else:
            d.update(accept=c["accept"], partial=c["partial"])
        cells.append(d)
    return {"title": v["title"], "scenario": v["scenario"], "task": v["task"], "exhibits": v["exhibits"], "cells": cells}


def make_entries(v, rng):
    """Mixed entries: right / off / scaled numbers, right or wrong choices, cite variants."""
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


cases, base_cases = [], []
rng = random.Random(7)
for tid, raw in RAW.items():
    # original numbers: compare with the rendered copy stored in tbs_reg.json (exact option order too)
    b = BASE[tid]
    base_cases.append({"id": tid, "params": b["params"], "exp": digest(b), "opts": [c["options"] for c in b["cells"] if c["kind"] == "dropdown"]})
    for seed in range(N):
        v, p = variant(raw, seed)
        ent = make_entries(v, rng)
        v2 = copy.deepcopy(v)
        v2["params"] = p  # tbs_lib.grade re-solves with v["params"]; a variant must use its own numbers
        # tbs_lib.grade treats an unentered earlier cell as 0 when re-solving (ECF); the browser uses the correct value
        # for it (no invented credit for a blank). Compare on that basis: fill blank number cells with their answers
        # for the Python run and expect 0 for the blank cells themselves.
        filled = {k: x for k, x in ent.items() if x != ""}
        for c in v["cells"]:
            if c["kind"] == "number" and c["id"] not in filled:
                filled[c["id"]] = str(c["answer"])
        py_res = grade(v2, filled)
        for c in v["cells"]:
            if ent[c["id"]] == "":
                py_res[c["id"]] = 0.0
        cases.append({"id": tid, "seed": seed, "params": p, "exp": digest(v), "entries": ent,
                      "credit": {c["id"]: py_res[c["id"]] for c in v["cells"]}, "perfect": {c["id"]: (str(c["answer"]) if c["kind"] != "citation" else c["accept"][0]) if c["kind"] != "dropdown" else c["answer"] for c in v["cells"]}})
print("python: %d TBS x %d variants = %d cases" % (len(RAW), N, len(cases)))

JS = r"""
async ({cases, baseCases, n}) => {
  const E = window.TBSEngine, items = {}; window.TBS_DATA.items.forEach(t => items[t.id] = t);
  const bad = [];
  const dig = (v) => ({title: v.title, scenario: v.scenario, task: v.task, exhibits: v.exhibits, cells: v.cells.map(c => {
    const d = {id: c.id, kind: c.kind, label: c.label, why: c.why, steps: c.steps, hints: c.hints};
    if (c.kind === 'number') { d.answer = c.answer; d.tol = c.tol; d.deps = c.deps; d.traps = c.traps.map(t => [t.value, t.msg]); }
    else if (c.kind === 'dropdown') { d.answer = c.answer; d.options = c.options.slice().sort(); d.wrong = Object.values(c.wrong).sort(); }
    else { d.accept = c.accept; d.partial = c.partial; }
    return d; })});
  const cmp = (tag, a, b) => { const x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) { let i = 0; while (x[i] === y[i]) i++; bad.push(tag + ' @' + i + ' js=' + x.slice(Math.max(0, i - 40), i + 60) + ' | py=' + y.slice(Math.max(0, i - 40), i + 60)); } };
  let nGrade = 0, nCells = 0;
  for (const b of baseCases) {
    const r = E.render(items[b.id], items[b.id].params, 0);
    cmp('base ' + b.id, dig(r), b.exp);
    cmp('base opts ' + b.id, r.cells.filter(c => c.kind === 'dropdown').map(c => c.options), b.opts);
  }
  for (const c of cases) {
    const it = items[c.id], tag = c.id + ' seed ' + c.seed;
    let r; try { r = E.render(it, c.params, c.seed + 1); } catch (e) { bad.push(tag + ' render error ' + e.message); continue; }
    cmp(tag, dig(r), c.exp);
    for (const cell of r.cells) {
      nCells++;
      const g = E.gradeCell(r, cell, c.entries);
      nGrade++;
      if (Math.abs(g.credit - c.credit[cell.id]) > 1e-9) bad.push(tag + ' grade ' + cell.id + ' js=' + g.credit + ' py=' + c.credit[cell.id] + ' entry=' + JSON.stringify(c.entries[cell.id]));
      const pg = E.gradeCell(r, cell, c.perfect);
      if (pg.credit !== 1) bad.push(tag + ' perfect entry not 1: ' + cell.id);
    }
  }
  // browser's own picker: guards hold, perfect entries score full marks, text has no leftover placeholders
  let own = 0;
  for (const id in items) {
    const it = items[id];
    for (let s = 1; s <= n; s++) {
      const p = E.pickParams(it, s * 7919 + 3), ns = E.buildNs(p, it.derived);
      if (!it.guards.every(g => E.ev(g, ns))) bad.push('own guard ' + id + ' ' + s);
      const r = E.render(it, p, s);
      if (/\{[a-z_0-9]+(:,)?\}/i.test(JSON.stringify(r))) bad.push('placeholder left ' + id + ' ' + s);
      own++;
    }
  }
  const cites = [['IRC §6694(a)', '6694(a)'], ['Sec. 6694 (a)', '6694(a)'], ['26 U.S.C. 6694(a)', '6694(a)'], ['Internal Revenue Code section 6694(a)', '6694(a)'], ['31 CFR §10.29', '10.29'], ['Circular 230 § 10.29', '10.29'], ['IRC 1367(a)(2).', '1367(a)(2)'], ['§ 280A(d)(1)', '280a(d)(1)'], ['1012(a)', '1012(a)'], ['IRC 1012(a)', '1012(a)'], ['§1012(a)', '1012(a)']];
  cites.forEach(([a, b]) => { if (E.normCite(a) !== b) bad.push('normCite ' + a + ' -> ' + E.normCite(a)); });
  return {bad, nGrade, nCells, own};
}
"""

# python side of the same citation table
for s, exp in [("IRC §6694(a)", "6694(a)"), ("Sec. 6694 (a)", "6694(a)"), ("26 U.S.C. 6694(a)", "6694(a)"), ("31 CFR §10.29", "10.29"), ("§1012(a)", "1012(a)"), ("IRC 1012(a)", "1012(a)")]:
    assert norm_cite(s) == exp, (s, norm_cite(s))

with sync_playwright() as pw:
    br = pw.chromium.launch(channel="msedge")
    pg = br.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.set_content("<!doctype html><html><body></body></html>")
    pg.add_script_tag(path=os.path.join(ROOT, "data", "tbs_reg.js"))
    pg.add_script_tag(path=os.path.join(ROOT, "js", "tbs.js"))
    out = pg.evaluate(JS, {"cases": cases, "baseCases": base_cases, "n": N})
    br.close()

print("browser: %d cells graded, %d own-picker variants" % (out["nCells"], out["own"]))
for b in out["bad"][:40]:
    print("FAIL", b)
for e in errs:
    print("PAGEERROR", e)
if out["bad"] or errs:
    print("FAILED: %d mismatches" % len(out["bad"]))
    sys.exit(1)
print("PASS: JS and Python agree on %d variants x 24 TBS (texts, answers, traps, grading incl. carry-forward)" % N)
