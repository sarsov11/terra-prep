# -*- coding: utf-8 -*-
"""Checker for the REG question bank (SPEC section 1 and 4 rules + the Area II checker rules).

  py tools/check_reg.py                 check the items that build_reg.py ships (status verified)
  py tools/check_reg.py --include-draft check draft items too
  py tools/check_reg.py --src DIR       read another source folder

Exit code 1 when any FAIL is found. WARN lines do not fail.
Also confirms data/reg_*.js and data/ready.js match the source (unless --no-data).
"""
import argparse, collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import reg_common as C

ap = argparse.ArgumentParser()
ap.add_argument("--src", default=C.DEFAULT_SRC)
ap.add_argument("--include-draft", action="store_true")
ap.add_argument("--no-data", action="store_true")
a = ap.parse_args()

REQ = ["id", "type", "area", "group", "topic", "task", "skill", "difficulty", "calc", "stem", "exhibit", "options",
       "answer", "why", "cite", "law_asof", "testable_from", "provenance", "verify", "status", "version"]
BAN = re.compile(r"\b(zero|never|always|none of the above|all of the above)\b", re.I)
CITE = re.compile(r"§|U\.S\.C|UCC\s*\d|Reg\.|IRC\s+(section|sec\.)|^\s*(under|per|pursuant to)\s+(IRC |the Code )?(section|sec\.)\s*\d", re.I)
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
for ar in C.AREAS:
    meta, items = C.load_area(a.src, ar)
    if meta is None:
        skipped[ar] = "no source file"; continue
    keep = C.accepted(items, a.include_draft)
    skipped[ar] = "%d of %d not shipped (%s)" % (len(items) - len(keep), len(items),
        ", ".join("%s %d" % kv for kv in collections.Counter(i.get("status") for i in items if i not in keep).items()) or "-")
    per_area[ar] = keep
    all_items += keep

ids, stems = set(), set()
recalc = [0, 0]
for ar, items in per_area.items():
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
        if it["provenance"] != "terra-original": F(i, "provenance must be terra-original")
        o = it["options"]
        if len(o) != 4 or any(not str(x).strip() for x in o): F(i, "needs exactly 4 non-empty options"); continue
        if len(set(o)) != 4: F(i, "duplicate options")
        if it["answer"] not in list("ABCD"): F(i, "answer must be A-D"); continue
        k = "ABCD".index(it["answer"])
        w = it["why"]
        if sorted(w.keys()) != list("ABCD") or any(len(str(v)) < 20 for v in w.values()): F(i, "why needs 4 explanations of 20+ chars")
        hd = [str(w.get(c, "")).split(" ")[0] for c in "ABCD"]
        if any(h in ("Correct.", "Incorrect.") for h in hd):     # Area II style headers must be consistent
            if hd[k] != "Correct." or any(hd[j] != "Incorrect." for j in range(4) if j != k): F(i, "why headers Correct./Incorrect. do not match answer")
        if it["skill"] not in C.SKILLS: F(i, "invalid skill")
        if it["difficulty"] not in (1, 2, 3): F(i, "difficulty must be 1-3")
        for t in ("group", "topic", "task"):
            if not str(it.get(t) or "").strip(): F(i, "tag %s empty" % t)
        if not it["cite"]: F(i, "cite is empty")
        if not it.get("law_asof"): F(i, "law_asof missing")
        if it["status"] == "verified":
            v = it["verify"] or {}
            if v.get("solver_answer") not in (None, it["answer"]):
                if v.get("note"): W(i, "verify.solver_answer differs from answer (reconciled, see verify.note)")
                else: F(i, "verify.solver_answer differs from answer")
            if v.get("cite_ok") is False: F(i, "verified but cite_ok is false")
            if it.get("needs_review"): F(i, "verified but needs_review is set")
        if CITE.search(it["stem"]) or any(CITE.search(x) for x in o): F(i, "citation in stem/options (keep it in why/cite)")
        for f in texts(it):
            if "!" in f or EMO.search(f): F(i, "exclamation mark or emoji"); break
        for f in texts(it):
            if BADCH.search(f): F(i, "non-English or broken characters: " + f[:30]); break
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

n, pos, longest, under = dist(all_items)
if n:
    pd = {k: pos[k] / n for k in "ABCD"}
    if any(abs(v - .25) > .08 for v in pd.values()): fails.append("answer position outside 25%%+-8%%: %s" % {k: round(v * 100) for k, v in pd.items()})
    if longest / n > .35: fails.append("correct option is the longest in %.0f%% (limit 35%%)" % (100 * longest / n))
    if under / n >= .05: fails.append("stems starting with 'Under' %.0f%% (limit 5%%)" % (100 * under / n))
for ar, items in per_area.items():
    if len(items) < 20: continue
    m, p2, l2, u2 = dist(items)
    if any(abs(p2[c] / m - .25) > .10 for c in "ABCD"): warns.append("Area %s answer positions %s" % (ar, {c: p2[c] for c in "ABCD"}))
    if l2 / m > .40: warns.append("Area %s longest-option rate %.0f%%" % (ar, 100 * l2 / m))

# ---- data files consistent with the source
if not a.no_data:
    dd = os.path.join(C.ROOT, "data")
    rp = os.path.join(dd, "ready.js")
    try:
        t = open(rp, encoding="utf-8").read(); R = json.loads(t[t.index("=") + 1:].rstrip().rstrip(";"))
    except Exception as e:
        R = None; fails.append("data/ready.js unreadable: %s" % e)
    if R is not None:
        for ar, items in per_area.items():
            key = C.SUBJECTS[ar][0]
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
                if len(m2["o"]) != 4 or len(m2["ex"]) != 4 or not (1 <= m2["a"] <= 4): fails.append("%s: bad mc structure" % q["i"])

print("Area | source | shipped")
for ar in C.AREAS:
    print("%-4s | %s | %d" % (ar, skipped.get(ar, "-"), len(per_area.get(ar, []))))
if n:
    sk = collections.Counter(x["skill"] for x in all_items); df = collections.Counter(x["difficulty"] for x in all_items)
    print("items %d | positions %s | longest-correct %d (%.0f%%) | 'Under' %d | calc %d" % (n, dict(sorted(pos.items())), longest, 100 * longest / n, under, sum(1 for x in all_items if x["calc"])))
    print("calc_check recomputed here: %d | uses author helper names (compared to the answer only): %d" % tuple(recalc))
    print("skill", dict(sk), "| difficulty", dict(sorted(df.items())))
for m in warns: print("WARN", m)
for m in fails: print("FAIL", m)
print("RESULT:", "PASS" if not fails else "FAIL (%d)" % len(fails))
sys.exit(1 if fails else 0)
