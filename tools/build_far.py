# -*- coding: utf-8 -*-
"""Builds the FAR data files from SPEC-schema question JSON (FAR Blueprint Areas I-III).

  py tools/build_far.py                    ship status=verified items only (default)
  py tools/build_far.py --include-draft    also ship status=draft items
  py tools/build_far.py --src DIR          read another source folder (same file names)

Reads    tools/src/FAR/far_area1_mcq.json  far_area2_mcq.json  far_area3_mcq.json   (far_area<N>*_mcq.json)
Writes   data/far_area<N>_<name>.js        window.TREE / window.QBANK / window.PAIRS  (one file per Area)
         data/ready.js                     far_* entries (REG and CFA entries are kept as they are)
         js/catalog.js                     FAR subject list between the BEGIN/END FAR markers
         sw.js                             file list + version

Same helpers as build_reg.py (tools/reg_common.py). One Blueprint Group = one unit (chapter with a single node), because FAR topic titles are unique per question. A source file that does not exist yet (Area I) or holds no
verified item builds nothing, and the Area shows "Coming soon" in the app. Run it again when a file arrives.
The FAR journal entry drill (je.html, data/je_far.js) is built by tools/build_je.py and is not touched here.
"""
import argparse, collections, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import reg_common as C

ap = argparse.ArgumentParser()
ap.add_argument("--src", default=C.FAR_DEFAULT_SRC)
ap.add_argument("--include-draft", action="store_true")
a = ap.parse_args()

DATA = os.path.join(C.ROOT, "data")
R = C.read_ready()
for k in list(R):
    if k.startswith("far_"):
        del R[k]                                  # FAR entries are rebuilt below; REG and CFA entries stay

report, shipped = [], {}
for ar in C.FAR_AREAS:
    key, disp, color = C.FAR_SUBJECTS[ar]
    meta, items = C.load_area(a.src, ar, "FAR")
    old = os.path.join(DATA, key + ".js")
    if meta is None:
        report.append("Area %-3s no source file — not built" % ar)
        if os.path.exists(old): os.remove(old)
        continue
    keep = C.accepted(items, a.include_draft)
    dropped = collections.Counter(i.get("status") for i in items if i not in keep)
    if not keep:
        report.append("Area %-3s 0 shipped (%s) — not built" % (ar, ", ".join("%s %d" % kv for kv in dropped.items()) or "empty"))
        if os.path.exists(old): os.remove(old)
        continue
    gn = C.group_names(ar, meta, items, "FAR")
    groups = sorted({i["group"] for i in keep})
    Q, nodes, chs = {}, [], []
    no = 0
    for gi, g in enumerate(groups, 1):
        # FAR topics are per question (each item has its own title), so a unit = one Blueprint Group (its task line)
        lst = [C.question(i) for i in keep if i["group"] == g]
        no += 1
        Q[str(no)] = lst
        nodes.append({"no": no, "part": 1, "ch": gi, "title": gn[g], "name": gn[g], "vol": len(lst), "q": len(lst), "cs": 0, "law": 0, "grp": g})
        node_nos = [no]
        chs.append({"key": "1-%02d" % gi, "part": 1, "no": gi, "name": gn[g], "grp": g, "nodes": node_nos})
    T = {"subject": disp, "key": key, "brand": "Terra Prep", "area": ar, "law_asof": max((i.get("law_asof") or "") for i in keep),
         "parts": [{"no": 1, "name": disp, "chs": [c["key"] for c in chs], "color": color}], "chs": chs, "nodes": nodes,
         "stat": {"parts": 1, "chs": len(chs), "nodes": len(nodes), "q": sum(len(v) for v in Q.values())}}
    out = os.path.join(DATA, key + ".js")
    C.dump_js(out, T, Q, "build_far.py")
    R[key] = {"name": disp, "n": T["stat"]["q"], "v": hashlib.md5(open(out, "rb").read()).hexdigest()[:8], "area": ar, "w": C.FAR_WEIGHT[ar]}
    shipped[ar] = T["stat"]["q"]
    sk = collections.Counter(i["skill"] for i in keep)
    report.append("Area %-3s %3d shipped, %d not shipped (%s) | units %d | %s" % (
        ar, len(keep), sum(dropped.values()), ", ".join("%s %d" % kv for kv in dropped.items()) or "-", len(nodes),
        ", ".join("%s %d" % (k2.split()[0], v) for k2, v in sk.items())))

C.write_ready(R)
C.write_catalog("FAR")
line = C.write_sw("build_far.py")
if line:
    report.append(line)
print(chr(10).join(report))
print("total shipped:", sum(shipped.values()), "| include_draft:", a.include_draft)
