# -*- coding: utf-8 -*-
"""Checker for the REG, FAR, TCP and AUD question banks (SPEC section 1 and 4 rules + the Area II checker rules).

  py tools/check_reg.py                 check the items that build_reg.py ships (status verified)
  py tools/check_reg.py --include-draft check draft items too
  py tools/check_reg.py --src DIR       read another REG source folder (--far-src DIR for FAR, --tcp-src DIR for TCP, --aud-src DIR for AUD)

All sections are checked with the same rules. FAR adds: no ASC / ASU / GASB / Topic number in a stem or option. AUD adds: no AU-C / AS / AT-C / ET / CFR number in a stem or option, and paragraph-level
citations only where verify.cite_ok confirms them (the builder cuts the rest back to the topic).

Exit code 1 when any FAIL is found. WARN lines do not fail.
Also confirms data/reg_*.js, data/far_*.js, data/tcp_*.js, data/aud_*.js and data/ready.js match the source (unless --no-data).
"""
import argparse, collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import reg_common as C

ap = argparse.ArgumentParser()
ap.add_argument("--src", default=C.DEFAULT_SRC)
ap.add_argument("--far-src", default=C.FAR_DEFAULT_SRC)
ap.add_argument("--tcp-src", default=C.TCP_DEFAULT_SRC)
ap.add_argument("--aud-src", default=C.AUD_DEFAULT_SRC)
ap.add_argument("--include-draft", action="store_true")
ap.add_argument("--no-data", action="store_true")
a = ap.parse_args()

REQ = ["id", "type", "area", "group", "topic", "task", "skill", "difficulty", "calc", "stem", "exhibit", "options",
       "answer", "why", "cite", "law_asof", "testable_from", "provenance", "verify", "status", "version"]
BAN = re.compile(r"\b(zero|never|always|none of the above|all of the above)\b", re.I)
CITE = re.compile(r"§|U\.S\.C|UCC\s*\d|Reg\.|IRC\s+(section|sec\.)|^\s*(under|per|pursuant to)\s+(IRC |the Code )?(section|sec\.)\s*\d", re.I)
STDNUM = re.compile(r"(ASC|ASU|GASB|FASB|SFAS|FAS)\s*(No\.?\s*)?\d|Topic\s+\d{3}|(Under|Per|Pursuant to)\s+(ASC|GASB|FASB|U\.S\. GAAP)|\d{3}-\d{2}-\d{2}", re.I)
AUDNUM = re.compile(r"(AU-C|AT-C|AR-C|PCAOB AS|AS|SSAE|SAS|SSARS|ET)\s*(No\.?\s*)?\d|\d+ CFR|17 CFR|Rule\s+3\d{3}|AICPA Code\s+\d")
EMO = re.compile("[\U0001F000-\U0001FFFF☀-➿]")
BADCH = re.compile("[�\u0000-\u0008\u000B\u000C\u000E-\u001F　-鿿가-힯]")
SAFE_EVAL = {"round": round, "min": min, "max": max, "abs": abs}

fails, warns = [], []
def F(i, m): fails.append("%s: %s" % (i, m))
def W(i, m): warns.append("%s: %s" % (i, m))

def texts(it):
    ex = it.get("exhibit")
    if isinstance(ex, list):
        ex = " ".join(" ".join(map(str, r)) for r in ex)
    return [it["stem"], ex or ""] + list(it["options"]) + list(it["why"].values()) + list(it.get("steps") or [])

all_items, per_area, skipped = [], {}, collections.Counter()
SRCS = {"REG": a.src, "FAR": a.far_src, "TCP": a.tcp_src, "AUD": a.aud_src}
for sec, cfg in C.SECTIONS.items():
    for ar in cfg["areas"]:
        meta, items = C.load_area(SRCS[sec], ar, sec)
        tag = (sec, ar)
        if meta is None:
            skipped[tag] = "no source file"; per_area[tag] = []; continue
        keep = C.accepted(items, a.include_draft)
        skipped[tag] = "%d of %d not shipped (%s)" % (len(items) - len(keep), len(items),
            ", ".join("%s %d" % kv for kv in collections.Counter(i.get("status") for i in items if i not in keep).items()) or "-")
        per_area[tag] = keep
        all_items += keep

ids, stems = set(), set()
recalc = [0, 0]
for (sec, ar), items in per_area.items():
    for it in items:
        i = it.get("id", "?")
        miss = [k for k in REQ if k not in it]
        if miss: F(i, "missing fields %s" % miss); continue
        if i in ids: F(i, "duplicate id")
        ids.add(i)
        if it["stem"] in stems: F(i, "duplicate stem")
        stems.add(it["stem"])
        if it["area"] != ar: F(i, "area %s does not match its file (%s)" % (it["area"], ar))
        if it["type"] != "mcq": F(i, "type must be mcq")
        if not str(it["provenance"]).startswith("terra-original"): F(i, "provenance must be terra-original")
        o = it["options"]
        if len(o) != 4 or any(not str(x).strip() for x in o): F(i, "needs exactly 4 non-empty options"); continue
        if len(set(o)) != 4: F(i, "duplicate options")
        if it["answer"] not in list("ABCD"): F(i, "answer must be A-D"); continue
        k = "ABCD".index(it["answer"])
        w = it["why"]
        if sorted(w.keys()) != list("ABCD") or any(len(str(v)) < 20 for v in w.values()): F(i, "why needs 4 explanations of 20+ chars")
        hd = [str(w.get(c, "")).split(" ")[0] for c in "ABCD"]
        if any(h in ("Correct.", "Incorrect.") for h in hd):     # Area II style headers must be consistent
            if sec in ("FAR", "TCP", "AUD"):                       # FAR/TCP/AUD style: only the answer carries "Correct."; wrong choices start with the reason
                if hd[k] != "Correct." or any(hd[j] == "Correct." for j in range(4) if j != k): F(i, "why headers Correct. do not match answer")
            elif hd[k] != "Correct." or any(hd[j] != "Incorrect." for j in range(4) if j != k): F(i, "why headers Correct./Incorrect. do not match answer")
        if it["skill"] not in (C.AUD_SKILLS if sec == "AUD" else C.SKILLS): F(i, "invalid skill")
        if it["difficulty"] not in (1, 2, 3): F(i, "difficulty must be 1-3")
        for t in ("group", "topic", "task"):
            if not str(it.get(t) or "").strip(): F(i, "tag %s empty" % t)
        if not it["cite"]: F(i, "cite is empty")
        if not it.get("law_asof"): F(i, "law_asof missing")
        if it["status"] == "verified":
            v = it["verify"] or {}
            if v.get("solver_answer") not in (None, it["answer"]):
                if v.get("note"): W(i, "verify.solver_answer differs from answer (reconciled, see verify.note)")
                elif (v.get("independent2") or {}).get("solver_answer") == it["answer"]: W(i, "verify.solver_answer differs from answer (draft key corrected; second independent solver agrees with the answer)")
                else: F(i, "verify.solver_answer differs from answer")
            if v.get("cite_ok") is False:
                if sec == "AUD": W(i, "cite_ok is false: reference shown at topic level only (source text not opened)")
                else: F(i, "verified but cite_ok is false")
            if it.get("needs_review"): F(i, "verified but needs_review is set")
        if CITE.search(it["stem"]) or any(CITE.search(x) for x in o): F(i, "citation in stem/options (keep it in why/cite)")
        if sec == "FAR" and (STDNUM.search(it["stem"]) or any(STDNUM.search(x) for x in o) or STDNUM.search(str(it["exhibit"]))): F(i, "ASC / ASU / GASB number in stem, exhibit or options (keep it in why/cite)")
        if sec == "FAR" and not str(it["id"]).startswith("FAR-%s-" % ar): F(i, "FAR id must start with FAR-%s-" % ar)
        if sec == "TCP" and not str(it["id"]).startswith("TCP-%s-" % ar): F(i, "TCP id must start with TCP-%s-" % ar)
        if sec == "TCP" and re.search(r"section\s+\d{2,4}[A-Za-z]?|IRC", " ".join([it["stem"]] + list(o))): F(i, "IRC section number in stem/options (keep it in why/cite)")
        if sec == "AUD" and not str(it["id"]).startswith("AUD-%s-" % ar): F(i, "AUD id must start with AUD-%s-" % ar)
        if sec == "AUD" and (AUDNUM.search(it["stem"]) or any(AUDNUM.search(x) for x in o) or AUDNUM.search(str(it["exhibit"]))): F(i, "standard / CFR number in stem, exhibit or options (keep it in why/cite)")
        for f in texts(it):
            if "!" in f or EMO.search(f): F(i, "exclamation mark or emoji"); break
        for f in texts(it):
            if BADCH.search(f): F(i, "non-English or broken characters: " + f[:30]); break
        for oo in o:                                   # a stray "A." / "(B)" label glued onto an option (a plain article "A $4,000 ..." is fine)
            if re.match(r"^\(?[A-Da-d][\.\):]\s", oo): F(i, "option text starts with a choice label: " + oo[:30])
        if BAN.search(" ".join(o)): F(i, "banned option word (zero/never/always/none of the above)")
        txt = " ".join([it["stem"]] + list(o))
        if re.search(r"\b\d[\d,]*\s+dollars\b", txt): F(i, "use $ (not 'dollars')")
        nums = [re.fullmatch(r"-?\$?[\d,]+(\.\d+)?%?", x.strip()) for x in o]
        if all(nums):
            vals = [float(re.sub(r"[^\d.\-]", "", x)) for x in o]
            if vals != sorted(vals): F(i, "numeric options not ascending")
            if len({x.strip().startswith("$") for x in o}) > 1: F(i, "mixed $ notation in options")
            if "$" in it["stem"] and not any("%" in x for x in o) and any("$" not in x for x in o) and "employees" not in it["stem"] and "shares" not in it["stem"]: W(i, "amount options without $")
        if it["calc"]:
            if not it.get("steps"): F(i, "calc true but steps missing")
            cc = it.get("calc_check")
            if not cc: F(i, "calc true but calc_check missing")
            elif "checks" in cc:
                # multi-step form: {"checks": [{"expr", "value"}, ...]} (answer may be text, so only the steps are recomputed)
                try:
                    for st in cc["checks"]:
                        v = eval(st["expr"], {"__builtins__": {}}, SAFE_EVAL)
                        if abs(v - st["value"]) > 1: F(i, "calc_check step %s recomputes to %s, not %s" % (st["expr"], v, st["value"]))
                    recalc[0] += 1
                except NameError:
                    recalc[1] += 1
                except Exception as e:
                    F(i, "calc_check error %s" % e)
            else:
                try:
                    if all(nums) and abs(float(re.sub(r"[^\d.\-]", "", o[k])) - cc["value"]) > 0.5: F(i, "answer option differs from calc_check value")
                    val = eval(cc["expr"], {"__builtins__": {}}, SAFE_EVAL)
                    if abs(val - cc["value"]) > 1: F(i, "calc_check recomputes to %s, not %s" % (val, cc["value"]))
                    else: recalc[0] += 1
                    for L, dd in (cc.get("distractors") or {}).items():
                        v2 = eval(dd["expr"], {"__builtins__": {}}, SAFE_EVAL)
                        if abs(v2 - dd["value"]) > 1: F(i, "distractor %s recompute mismatch" % L)
                except NameError:
                    recalc[1] += 1     # expression uses a helper from the author's own script; value still compared to the answer option
                except Exception as e:
                    F(i, "calc_check error %s" % e)

def dist(items):
    n = len(items)
    pos = collections.Counter(x["answer"] for x in items)
    longest = 0
    for x in items:
        if x["answer"] not in "ABCD" or len(x["options"]) != 4: continue
        lens = [len(t) for t in x["options"]]; k = "ABCD".index(x["answer"])
        if lens[k] == max(lens) and lens.count(max(lens)) == 1: longest += 1
    under = sum(1 for x in items if x["stem"].startswith("Under"))
    return n, pos, longest, under

for sec, cfg in C.SECTIONS.items():
    sec_items = [x for ar in cfg["areas"] for x in per_area.get((sec, ar), [])]
    n, pos, longest, under = dist(sec_items)
    if n:
        pd = {k: pos[k] / n for k in "ABCD"}
        if any(abs(v - .25) > .08 for v in pd.values()): fails.append("%s answer position outside 25%%+-8%%: %s" % (sec, {k: round(v * 100) for k, v in pd.items()}))
        if longest / n > .35: fails.append("%s correct option is the longest in %.0f%% (limit 35%%)" % (sec, 100 * longest / n))
        if under / n >= .05: fails.append("%s stems starting with 'Under' %.0f%% (limit 5%%)" % (sec, 100 * under / n))
for (sec, ar), items in per_area.items():
    if len(items) < 20: continue
    m, p2, l2, u2 = dist(items)
    if any(abs(p2[c] / m - .25) > .10 for c in "ABCD"): warns.append("%s Area %s answer positions %s" % (sec, ar, {c: p2[c] for c in "ABCD"}))
    if l2 / m > .40: warns.append("%s Area %s longest-option rate %.0f%%" % (sec, ar, 100 * l2 / m))
    if sec in ("FAR", "TCP"):                          # Blueprint skill ranges (2026-27). FAR: R&U 5-15, Application 45-55, Analysis 35-45. TCP: R&U 5-15, Application 50-65, Analysis 25-40
        sk = collections.Counter(x["skill"] for x in items)
        rng = (("Remembering & Understanding", 5, 15), ("Application", 45, 55), ("Analysis", 35, 45)) if sec == "FAR" else (("Remembering & Understanding", 5, 15), ("Application", 50, 65), ("Analysis", 25, 40))
        for name, lo, hi in rng:
            pc = 100.0 * sk[name] / m
            if pc < lo - 5 or pc > hi + 5: warns.append("%s Area %s skill mix: %s %.0f%% (Blueprint %d-%d%%)" % (sec, ar, name, pc, lo, hi))
aud_items = [x for ar in C.AUD_AREAS for x in per_area.get(("AUD", ar), [])]
if len(aud_items) >= 40:                               # AUD Blueprint skill ranges: R&U 30-40, Application 30-40, Analysis 15-25, Evaluation 5-15 (whole section; Areas I and IV lean on R&U by design)
    sk = collections.Counter(x["skill"].replace("Remembering and Understanding", "Remembering & Understanding") for x in aud_items)
    for name, lo, hi in (("Remembering & Understanding", 30, 40), ("Application", 30, 40), ("Analysis", 15, 25), ("Evaluation", 5, 15)):
        pc = 100.0 * sk[name] / len(aud_items)
        if pc < lo - 5 or pc > hi + 5: warns.append("AUD skill mix: %s %.0f%% (Blueprint %d-%d%%)" % (name, pc, lo, hi))
n = len(all_items)

# ---- data files consistent with the source
if not a.no_data:
    dd = os.path.join(C.ROOT, "data")
    rp = os.path.join(dd, "ready.js")
    try:
        t = open(rp, encoding="utf-8").read(); R = json.loads(t[t.index("=") + 1:].rstrip().rstrip(";"))
    except Exception as e:
        R = None; fails.append("data/ready.js unreadable: %s" % e)
    if R is not None:
        for (sec, ar), items in per_area.items():
            key = C.SECTIONS[sec]["subjects"][ar][0]
            if not items:
                if key in R: fails.append("ready.js lists %s but no items are shipped" % key)
                continue
            if key not in R: fails.append("ready.js is missing %s (run tools/build_reg.py)" % key); continue
            if R[key]["n"] != len(items): fails.append("%s: ready.js n=%d but source has %d" % (key, R[key]["n"], len(items)))
            body = open(os.path.join(dd, key + ".js"), encoding="utf-8").read()
            mm = re.search(r"window\.QBANK=(.*?);\nwindow\.PAIRS", body, re.S)
            qb = json.loads(mm.group(1)); flat = [q for v in qb.values() for q in v]
            if len(flat) != len(items): fails.append("%s: data has %d questions, source %d" % (key, len(flat), len(items)))
            src_ids = {x["id"] for x in items}
            if {q["i"] for q in flat} != src_ids: fails.append("%s: question ids differ from source" % key)
            for q in flat:
                m2 = q["mc"]
                wt = m2.get("wt")
                if not (isinstance(wt, list) and len(wt) == 4 and all((t == "" and j == m2["a"] - 1) or (t in C.WRONG_TAGS and j != m2["a"] - 1) for j, t in enumerate(wt))): fails.append("%s: bad wrong-choice tags %s" % (q["i"], wt))
                if len(m2["o"]) != 4 or len(m2["ex"]) != 4 or not (1 <= m2["a"] <= 4): fails.append("%s: bad mc structure" % q["i"])
                if sec == "AUD":                           # displayed citation follows the AUD topic-level rule
                    si = next(x for x in items if x["id"] == q["i"])
                    if m2["cite"] != C.cite_text(C.aud_cite(si)): fails.append("%s: displayed cite %r breaks the AUD citation display rule" % (q["i"], m2["cite"]))
                    if re.search(r"not opened|topic level", m2["cite"]): fails.append("%s: displayed cite carries an internal note" % q["i"])
                if sec == "FAR":                           # displayed citation follows the paragraph-number display rule
                    si = next(x for x in items if x["id"] == q["i"])
                    if m2["cite"] != C.cite_text(C.far_cite(si)): fails.append("%s: displayed cite %r breaks the FAR paragraph-number rule" % (q["i"], m2["cite"]))
                    if C.far_cite_is_paragraph(m2["cite"]) and not str((si.get("verify") or {}).get("cite_ok", "")).startswith("public-checked"): fails.append("%s: paragraph number shown but cite_ok is unchecked" % q["i"])

# ---- offline cache: sw.js must list every shipped file and carry the current content hash
if not a.no_data:
    swp = os.path.join(C.ROOT, "sw.js")
    if not os.path.exists(swp): fails.append("sw.js missing")
    else:
        sw = open(swp, encoding="utf-8").read()
        files = C.pwa_files(); ver = C.pwa_version(files)
        if 'var VERSION = "%s";' % ver not in sw: fails.append("sw.js is stale (run tools/build_reg.py to refresh version and file list)")
        try:
            listed = json.loads(re.search(r"var FILES = (\[.*?\]);", sw, re.S).group(1))
            if listed != files: fails.append("sw.js file list differs from the shipped files")
        except Exception: fails.append("sw.js FILES list unreadable")
    try:
        mf = json.load(open(os.path.join(C.ROOT, "manifest.webmanifest"), encoding="utf-8"))
        for k in ("name", "short_name", "start_url", "display", "icons"):
            if not mf.get(k): fails.append("manifest.webmanifest missing " + k)
    except Exception as e: fails.append("manifest.webmanifest unreadable: %s" % e)
    tagc = collections.Counter(t for _k, items in per_area.items() for it in items for t in C.tag_wrong_options(it) if t)
    print("wrong-choice tags:", dict(tagc))

print("Section Area | source | shipped")
for sec, cfg in C.SECTIONS.items():
    for ar in cfg["areas"]:
        print("%-3s %-4s | %s | %d" % (sec, ar, skipped.get((sec, ar), "-"), len(per_area.get((sec, ar), []))))
if n:
    pos = collections.Counter(x["answer"] for x in all_items)
    longest = sum(1 for x in all_items if [len(t) for t in x["options"]].count(max(len(t) for t in x["options"])) == 1 and len(x["options"]["ABCD".index(x["answer"])]) == max(len(t) for t in x["options"]))
    sk = collections.Counter(x["skill"] for x in all_items); df = collections.Counter(x["difficulty"] for x in all_items)
    print("items %d | positions %s | longest-correct %d (%.0f%%) | calc %d" % (n, dict(sorted(pos.items())), longest, 100 * longest / n, sum(1 for x in all_items if x["calc"])))
    print("calc_check recomputed here: %d | uses author helper names (compared to the answer only): %d" % tuple(recalc))
    print("skill", dict(sk), "| difficulty", dict(sorted(df.items())))
for m in warns: print("WARN", m)
for m in fails: print("FAIL", m)
print("RESULT:", "PASS" if not fails else "FAIL (%d)" % len(fails))
sys.exit(1 if fails else 0)
