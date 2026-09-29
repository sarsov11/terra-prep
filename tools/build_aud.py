# -*- coding: utf-8 -*-
"""Builds the AUD (Auditing and Attestation) data files from SPEC-schema question JSON (AUD Blueprint Areas I-IV).

  py tools/build_aud.py                    ship status=verified items only (default)
  py tools/build_aud.py --include-draft    also ship status=draft items
  py tools/build_aud.py --src DIR          read another source folder (same file names)

Reads    tools/src/AUD/aud_area1_mcq.json .. aud_area4_mcq.json (item Area = the Area of its file)
Writes   data/aud_area<N>_<name>.js        window.TREE / window.QBANK / window.PAIRS  (one file per Area)
         data/ready.js                     aud_* entries (REG, FAR and CFA entries are kept as they are)
         js/catalog.js                     AUD subject list between the BEGIN/END AUD markers
         sw.js                             file list + version
Same helpers and same unit layout as build_reg.py (Blueprint Group = chapter, topic = unit), see tools/reg_common.py.
Citation display: as written when verify.cite_ok is true, otherwise cut back to the topic (C.aud_cite). Standard numbers in stems/options are rejected by tools/check_reg.py.
"""
import argparse, collections, hashlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import reg_common as C

ap = argparse.ArgumentParser()
ap.add_argument("--src", default=C.AUD_DEFAULT_SRC)
ap.add_argument("--include-draft", action="store_true")
a = ap.parse_args()

DATA = os.path.join(C.ROOT, "data")
R = C.read_ready()
for k in list(R):
    if k.startswith("aud_"):
        del R[k]                                  # AUD entries are rebuilt below; REG, FAR and CFA entries stay

report, shipped = [], {}
for ar in C.AUD_AREAS:
    key, disp, color = C.AUD_SUBJECTS[ar]
    meta, items = C.load_area(a.src, ar, "AUD")
    old = os.path.join(DATA, key + ".js")
    if meta is None or not items:
        report.append("Area %-3s no source items — not built" % ar)
        if os.path.exists(old): os.remove(old)
        continue
    keep = C.accepted(items, a.include_draft)
    dropped = collections.Counter(i.get("status") for i in items if i not in keep)
    if not keep:
        report.append("Area %-3s 0 shipped (%s) — not built" % (ar, ", ".join("%s %d" % kv for kv in dropped.items()) or "empty"))
        if os.path.exists(old): os.remove(old)
        continue
    gn = C.group_names(ar, meta, items, "AUD")
    groups = sorted({i["group"] for i in keep})
    Q, nodes, chs = {}, [], []
    no = 0
    for gi, g in enumerate(groups, 1):
        tops = []
        for i in keep:
            if i["group"] == g and i["topic"] not in tops:
                tops.append(i["topic"])
        node_nos = []
        for tp in tops:
            no += 1
            lst = [C.question(i) for i in keep if i["group"] == g and i["topic"] == tp]
            Q[str(no)] = lst
            node_nos.append(no)
            nodes.append({"no": no, "part": 1, "ch": gi, "title": tp, "name": tp, "vol": len(lst), "q": len(lst), "cs": 0, "law": 0, "grp": g})
        chs.append({"key": "1-%02d" % gi, "part": 1, "no": gi, "name": gn[g], "grp": g, "nodes": node_nos})
    T = {"subject": disp, "key": key, "brand": "Terra Prep", "area": ar, "law_asof": max((i.get("law_asof") or "") for i in keep),
         "parts": [{"no": 1, "name": disp, "chs": [c["key"] for c in chs], "color": color}], "chs": chs, "nodes": nodes,
         "stat": {"parts": 1, "chs": len(chs), "nodes": len(nodes), "q": sum(len(v) for v in Q.values())}}
    out = os.path.join(DATA, key + ".js")
    C.dump_js(out, T, Q, "build_aud.py")
    R[key] = {"name": disp, "n": T["stat"]["q"], "v": hashlib.md5(open(out, "rb").read()).hexdigest()[:8], "area": ar, "w": C.AUD_WEIGHT[ar]}
    shipped[ar] = T["stat"]["q"]
    sk = collections.Counter(i["skill"] for i in keep)
    report.append("Area %-3s %3d shipped, %d not shipped (%s) | units %d | %s" % (
        ar, len(keep), sum(dropped.values()), ", ".join("%s %d" % kv for kv in dropped.items()) or "-", len(nodes),
        ", ".join("%s %d" % (k2.split()[0], v) for k2, v in sk.items())))

C.write_ready(R)
C.write_catalog("AUD")
line = C.write_sw("build_aud.py")
if line:
    report.append(line)
print(chr(10).join(report))
print("total shipped:", sum(shipped.values()), "| include_draft:", a.include_draft)
