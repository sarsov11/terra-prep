# FAR TBS 공용 라이브러리: 셀 헬퍼(number/dropdown/citation/je), 변형 생성, 렌더, 채점 참고 구현.
# REG 의 tbs_lib.py 와 같은 틀. FAR 에서 추가된 것: 분개 칸(je), 소수 자릿수(fmt), 연금현가 함수, ASC/GASB 번호 정규화.
# 식 언어 = tbs.js 의 파서가 받는 부분집합(사칙, %, **, 비교, and/or/not, 함수: rnd min max abs pvann pvdue pmtann iff). 삼항·리스트·점 표기 금지.
import math, re, random, copy, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
COA = {a["id"]: a for a in json.load(open(os.path.join(HERE, "je_coa.json"), encoding="utf-8"))["coa"]}

# ---------- 수치 ----------
def rd(x, d=0):
    """사사오입(양의 무한대 방향 half-up). d=소수 자릿수. JS 쌍둥이: Math.floor(x*m+0.5+1e-9)/m"""
    m = 10 ** d
    v = math.floor(x * m + 0.5 + 1e-9) / m
    return int(v) if d == 0 else v

def rnd(x):
    return rd(x, 0)

def pvann(r, n, pmt, fv=0):
    """보통연금 현가 + 일시금 현가"""
    if r == 0:
        return pmt * n + fv
    d = (1 + r) ** (-n)
    return pmt * (1 - d) / r + fv * d

def pvdue(r, n, pmt, fv=0):
    """선급연금(기초 지급) 현가"""
    if r == 0:
        return pmt * n + fv
    d = (1 + r) ** (-n)
    return pmt * (1 + r) * (1 - d) / r + fv * d

def pmtann(r, n, pv):
    return pv / n if r == 0 else pv * r / (1 - (1 + r) ** (-n))

def iff(c, a, b):
    return a if c else b

NS_BASE = {"rnd": rnd, "min": min, "max": max, "abs": abs, "pvann": pvann, "pvdue": pvdue, "pmtann": pmtann, "iff": iff}
FN_NAMES = set(NS_BASE)
DEC = {"$": 0, "n": 0, "$2": 2, "x2": 2, "p1": 1}          # fmt -> 소수 자릿수
TOL = {"$": 1, "n": 0, "$2": 0.01, "x2": 0.01, "p1": 0.1}   # fmt 별 기본 허용오차

_cc = {}
def _ev(expr, ns):
    c = _cc.get(expr)
    if c is None:
        c = _cc[expr] = compile(expr, "<expr>", "eval")
    return eval(c, {"__builtins__": {}}, ns)

def build_ns(params, derived):
    ns = dict(NS_BASE)
    ns.update(params)
    for name, expr in derived:
        ns[name] = _ev(expr, ns)
    return ns

# ---------- 셀 헬퍼 ----------
def N(id, label, expr, why, steps, hints, traps=None, fmt="$", tol=None, ecf=True):
    return {"id": id, "kind": "number", "label": label, "expr": expr, "fmt": fmt, "tol": TOL[fmt] if tol is None else tol,
            "why": why, "steps": steps, "hints": hints, "traps": [{"expr": e, "msg": m} for e, m in (traps or [])], "ecf": ecf}

def D(id, label, options, answer, why, hints, wrong=None):
    assert answer in options, (id, answer)
    return {"id": id, "kind": "dropdown", "label": label, "options": list(options), "answer": answer,
            "why": why, "steps": [], "hints": hints, "wrong_msgs": wrong or {}}

def C(id, label, accept, why, hints, ask, partial=None, link="https://asc.fasb.org/"):
    """ASC/GASB 번호 입력 칸. accept/partial 은 norm_std 정규형. 링크는 FASB Codification 기본 화면(GASB 는 gasb.org)."""
    return {"id": id, "kind": "citation", "norm": "std", "label": label, "ask": ask, "accept": accept, "partial": partial or [],
            "link": link, "why": why, "steps": [], "hints": hints}

def J(id, label, accounts, lines, why, steps=None, hints=None, mist=None, tol=1, ask="Enter the journal entry. Choose accounts from the list; enter each amount in the Debit or Credit column."):
    """분개 칸. lines=[(차대 'D'|'C', 계정 id, 금액식, 줄 해설, [대체 인정 계정])]. 채점 점수 = 줄 단위(JE_SPEC 4절). points = 정답 줄 수."""
    ls = []
    for ln in lines:
        s, a, e, w = ln[:4]
        ls.append({"s": s, "a": a, "expr": e, "why": w, "alt": list(ln[4]) if len(ln) > 4 else []})
    return {"id": id, "kind": "je", "label": label, "ask": ask, "accounts": list(accounts), "lines": ls, "mist": mist or [],
            "tol": tol, "why": why, "steps": steps or [], "hints": hints or [], "ecf": True}

def M(k, a, msg, b=None, expr=None):
    """분개 흔한 실수 규칙(JE_SPEC 3절). k = sub|swap|amt|extra|miss"""
    m = {"k": k, "a": a, "msg": msg}
    if b:
        m["b"] = b
    if expr:
        m["expr"] = expr
    return m

def X(id, title, kind, body):
    return {"id": id, "title": title, "kind": kind, "body": body}

def T(id, area, fmt, title, scenario, task, exhibits, cells, params, blueprint, difficulty, minutes,
      cite=None, vary=None, guards=None, derived=None, law_note="", testable_from="2026-01-01", tags=None):
    for c in cells:
        if c["kind"] == "je":
            for ln in c["lines"]:
                assert ln["a"] in COA, (id, c["id"], ln["a"])
                assert ln["a"] in c["accounts"], (id, c["id"], "accounts 목록에 정답 계정 없음", ln["a"])
                for x in ln["alt"]:
                    assert x in COA and x in c["accounts"], (id, c["id"], "alt", x)
            for a in c["accounts"]:
                assert a in COA, (id, c["id"], a)
    return {"id": id, "type": "tbs", "exam": "FAR", "area": area, "format": fmt, "title": title, "scenario": scenario, "task": task,
            "exhibits": exhibits, "cells": cells, "params": params, "vary": vary or {}, "guards": guards or [],
            "derived": derived or [], "blueprint": blueprint, "difficulty": difficulty, "est_minutes": minutes,
            "testable_from": testable_from, "law_asof": "2026-09-29", "cite": cite or [], "law_note": law_note, "tags": tags or []}

# ---------- 번호 정규화(ASC / GASB) ----------
def norm_std(s):
    """'FASB ASC Topic 260' -> '260'; 'ASC 205-20-45-1B' -> '205-20-45-1b'; 'GASB Statement No. 34' / 'GASB 34' -> '34'."""
    s = s.lower().strip().replace("§", " ").replace("–", "-").replace("—", "-")
    s = re.sub(r"\b(fasb|asc|gasb|codification|topic|subtopic|statement|standards?|no|number|section|sec|paragraph|para)\b", " ", s)
    s = re.sub(r"[#.,;:]", " ", s)
    s = re.sub(r"\s+", "", s)
    return s

def grade_std(cell, text):
    n = norm_std(text)
    for a in cell["accept"]:
        if n == a or n.startswith(a + "-"):
            return 1.0
    if n in cell.get("partial", []):
        return 0.5
    return 0.0

def parse_num(s):
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s if s is not None else "").strip().replace("$", "").replace(",", "").replace(" ", "").replace("−", "-")
    neg = bool(re.match(r"^\(.*\)$", s))
    if neg:
        s = s[1:-1]
    if not re.match(r"^[-+]?(\d+\.?\d*|\.\d+)$", s):
        return float("nan")
    v = float(s)
    return -v if neg else v

# ---------- 채우기 / 렌더 ----------
PHR = re.compile(r"\{([A-Za-z_][A-Za-z_0-9]*)(:,|:[0-9])?\}")

def fmtval(v, spec):
    """spec: None -> 그대로(정수화된 실수는 정수로), ':,' -> 천 단위 쉼표, ':N' -> 소수 N자리 고정"""
    if spec and spec[1] in "0123456789":
        return "%.*f" % (int(spec[1]), v)
    comma = bool(spec)
    if isinstance(v, float) and v == int(v):
        v = int(v)
    if not comma:
        return str(v)
    neg = v < 0
    ip, _, fp = str(abs(v)).partition(".")
    return ("-" if neg else "") + "{:,}".format(int(ip)) + ("." + fp if fp else "")

def fill(s, ns):
    if isinstance(s, str):
        def rep(m):
            if m.group(1) not in ns:
                raise KeyError(m.group(1))
            return fmtval(ns[m.group(1)], m.group(2))
        return PHR.sub(rep, s)
    if isinstance(s, list):
        return [fill(x, ns) for x in s]
    if isinstance(s, dict):
        return {k: fill(v, ns) for k, v in s.items()}
    return s

def _names(acc):
    return [COA[a]["name"] for a in acc]

def je_hints(lines):
    """JE_SPEC 5절: 1단계 영향 계정(이름순, 변 없음) -> 2단계 증감 -> 3단계 차/대. 금액은 알려 주지 않는다."""
    ns_ = sorted(COA[l["a"]]["name"] for l in lines)
    h1 = "Accounts: " + ", ".join(ns_)
    h2 = "; ".join("%s %s" % (COA[l["a"]]["name"], "increases" if l["s"] == COA[l["a"]]["n"] else "decreases")
                   for l in sorted(lines, key=lambda x: COA[x["a"]]["name"]))
    h3 = "; ".join("%s: %s" % (COA[l["a"]]["name"], "Debit" if l["s"] == "D" else "Credit") for l in lines)
    return [h1, h2, h3]

def solve(t, params=None):
    p = dict(t["params"]) if params is None else dict(params)
    ns = build_ns(p, t["derived"])
    vals = {}
    for c in t["cells"]:
        if c["kind"] == "number":
            v = rd(_ev(c["expr"], ns), DEC[c["fmt"]])
            vals[c["id"]] = v
            ns[c["id"]] = v
        elif c["kind"] == "je":
            vals[c["id"]] = [rnd(_ev(l["expr"], ns)) for l in c["lines"]]
    return ns, vals

def render(t, params=None, shuffle_seed=None):
    ns, vals = solve(t, params)
    out = copy.deepcopy(t)
    for k in ("title", "scenario", "task", "exhibits"):
        out[k] = fill(t[k], ns)
    cells = []
    for c in t["cells"]:
        c2 = copy.deepcopy(c)
        for k in ("label", "why", "steps", "hints"):
            c2[k] = fill(c[k], ns)
        if "ask" in c:
            c2["ask"] = fill(c["ask"], ns)
        if c["kind"] == "number":
            c2["answer"] = vals[c["id"]]
            c2["deps"] = sorted(set(re.findall(r"\b(c\d+)\b", c["expr"])))
            c2["traps"] = [{"expr": tr["expr"], "value": rd(_ev(tr["expr"], ns), DEC[c["fmt"]]), "msg": fill(tr["msg"], ns)} for tr in c["traps"]]
        elif c["kind"] == "dropdown":
            c2["options"] = fill(c["options"], ns)
            c2["answer"] = fill(c["answer"], ns)
            c2["wrong_msgs"] = fill(c["wrong_msgs"], ns)
        elif c["kind"] == "je":
            c2["lines"] = []
            for l, v in zip(c["lines"], vals[c["id"]]):
                l2 = {"s": l["s"], "a": l["a"], "v": v, "why": fill(l["why"], ns), "alt": list(l["alt"]),
                      "deps": sorted(set(re.findall(r"\b(c\d+)\b", l["expr"]))), "expr": l["expr"]}
                c2["lines"].append(l2)
            c2["mist"] = []
            for m in c["mist"]:
                m2 = {"k": m["k"], "a": m["a"], "msg": fill(m["msg"], ns)}
                if "b" in m:
                    m2["b"] = m["b"]
                if "expr" in m:
                    m2["expr"] = m["expr"]
                    m2["v"] = rnd(_ev(m["expr"], ns))
                c2["mist"].append(m2)
            if not c2["hints"]:
                c2["hints"] = je_hints(c2["lines"])
            c2["points"] = len(c["lines"])
        cells.append(c2)
    out["cells"] = cells
    rng = random.Random(shuffle_seed or t["id"])
    for c in out["cells"]:
        if c["kind"] == "dropdown":
            rng.shuffle(c["options"])
            # 정답 위치가 특정 자리에 몰리지 않도록 칸마다 시드로 목표 자리를 정해 정답을 그 자리로 옮긴다
            k = rng.randrange(len(c["options"]))
            i = c["options"].index(c["answer"])
            c["options"][i], c["options"][k] = c["options"][k], c["options"][i]
    return out

def variant(t, seed):
    rng = random.Random(seed)
    for _ in range(200):
        p = dict(t["params"])
        for k, choices in t["vary"].items():
            p[k] = rng.choice(choices)
        ns = build_ns(p, t["derived"])
        if all(_ev(g, ns) for g in t["guards"]):
            return render(t, p, shuffle_seed=t["id"] + str(seed)), p
    raise RuntimeError("guards unsatisfiable " + t["id"])

# ---------- 분개 채점(je.js grade 의 파이썬 이식) ----------
def _near(a, b, tol):
    return abs(a - b) <= max(tol, abs(b) * 0.0001) + 1e-9

def _find_rule(mist, k, a=None, b=None, val=None, tol=1):
    for m in mist:
        if m["k"] != k:
            continue
        if a is not None and m["a"] != a:
            continue
        if b is not None and m.get("b") != b:
            continue
        if val is not None and not (m.get("v") is not None and _near(m["v"], val, tol)):
            continue
        return m
    return None

def _side(s):
    return "debit" if s == "D" else "credit"

JE_ECF = 0.75

def grade_je(cell, rows, alt_vals=None):
    """rows=[{'a': 계정 id|None, 'd': 차변 금액, 'c': 대변 금액}]. alt_vals=학생의 앞칸 값으로 다시 계산한 줄별 금액(ECF).
    반환 {score, perfect, lines[{status,...}], missing[], n}. status: ok|ecf|amount|flip|acct|extra|unknown"""
    tol = cell.get("tol", 1)
    mist = cell["mist"]
    corr = []
    for i, l in enumerate(cell["lines"]):
        corr.append({"i": i, "a": l["a"], "s": l["s"], "v": l["v"], "alt": l["alt"], "done": False,
                     "av": (alt_vals[i] if alt_vals and l["deps"] else None)})
    uls, by_key = [], {}
    for ri, r in enumerate(rows):
        a = r.get("a")
        d, c = r.get("d") or 0, r.get("c") or 0
        if not (a or d or c):
            continue
        parts = []
        if d:
            parts.append(("D", d))
        if c:
            parts.append(("C", c))
        if not parts:
            uls.append({"a": a, "s": None, "v": 0, "status": "noamt", "done": True})
            continue
        for s, v in parts:
            key = "%s|%s" % (a or "?", s)
            if key in by_key:
                by_key[key]["v"] += v
            else:
                u = {"a": a, "s": s, "v": v, "status": None, "done": False}
                by_key[key] = u
                uls.append(u)

    def pair(u, c, status, **extra):
        u["done"] = True
        if c is not None:
            c["done"] = True
        u["c"] = c
        u["status"] = status
        u.update(extra)

    same = {}
    for c in corr:
        same.setdefault(c["a"], []).append(c)
    for a, cs in same.items():
        if len(cs) < 2:
            continue
        net = sum(c["v"] if c["s"] == "D" else -c["v"] for c in cs)
        mine = [u for u in uls if not u["done"] and u["a"] == a]
        if len(mine) == 1 and mine[0]["s"] == ("D" if net >= 0 else "C") and _near(mine[0]["v"], abs(net), tol):
            pair(mine[0], cs[0], "ok", note="net")
            for c in cs:
                c["done"] = True
    for c in corr:
        if c["done"]:
            continue
        acc = [c["a"]] + c["alt"]
        for u in uls:
            if u["done"] or not u["a"] or u["s"] != c["s"] or u["a"] not in acc:
                continue
            if abs(u["v"] - c["v"]) < 0.005 or _near(u["v"], c["v"], tol):
                pair(u, c, "ok")
            elif c["av"] is not None and _near(u["v"], c["av"], tol):
                pair(u, c, "ecf")
            else:
                rule = _find_rule(mist, "amt", c["a"], None, u["v"], tol)
                pair(u, c, "amount", msg=rule["msg"] if rule else "Right account and side. Amount is off by $%s." % format(int(abs(u["v"] - c["v"])), ","))
            break
    for c in corr:
        if c["done"]:
            continue
        acc = [c["a"]] + c["alt"]
        for u in uls:
            if u["done"] or not u["a"] or u["s"] == c["s"] or u["a"] not in acc:
                continue
            rule = _find_rule(mist, "swap", c["a"])
            inc = c["s"] == COA[c["a"]]["n"]
            pair(u, c, "flip", msg=rule["msg"] if rule else "%s %s here, so it is a %s." % (COA[c["a"]]["name"], "increases" if inc else "decreases", _side(c["s"])))
            break
    for c in corr:
        if c["done"]:
            continue
        pick = None
        for u in uls:
            if u["done"] or not u["a"] or u["s"] != c["s"]:
                continue
            if _find_rule(mist, "sub", c["a"], u["a"]):
                pick = u
                break
        if pick is None:
            for u in uls:
                if not u["done"] and u["a"] and u["s"] == c["s"] and _near(u["v"], c["v"], tol):
                    pick = u
                    break
        if pick is not None:
            rule = _find_rule(mist, "sub", c["a"], pick["a"])
            pair(pick, c, "acct", msg=rule["msg"] if rule else "Different account expected on this line.")
    for u in uls:
        if u["done"]:
            continue
        u["done"] = True
        if not u["a"]:
            u["status"] = "unknown"
            continue
        rule = _find_rule(mist, "extra", u["a"])
        u["status"] = "extra"
        u["msg"] = rule["msg"] if rule else "Not part of this entry."
    missing = []
    for c in corr:
        if not c["done"]:
            rule = _find_rule(mist, "miss", c["a"])
            missing.append({"a": c["a"], "msg": rule["msg"] if rule else "Missing line."})
    pts, extras, all_ok, paired = 0.0, 0, True, 0
    for u in uls:
        st = u["status"]
        if st == "ok":
            pts += 1
        elif st == "ecf":
            pts += JE_ECF
            all_ok = False
        elif st == "amount":
            pts += 0.5
            all_ok = False
        elif st == "noamt":
            pass
        else:
            all_ok = False
            if st in ("extra", "unknown"):
                extras += 1
        if u.get("c") is not None:
            paired += 1
    covered = sum(1 for c in corr if c["done"])
    if covered > paired:
        pts += covered - paired
    score = min(1.0, max(0.0, pts - 0.5 * extras) / len(corr))
    perfect = all_ok and not missing and extras == 0 and abs(score - 1) < 1e-9
    return {"score": score, "perfect": perfect, "lines": uls, "missing": missing, "n": len(corr)}

def answer_rows(cell):
    """정답 줄을 입력 행으로 변환(만점 채점 시험용)"""
    return [{"a": l["a"], "d": l["v"] if l["s"] == "D" else 0, "c": l["v"] if l["s"] == "C" else 0} for l in cell["lines"]]

# ---------- 전체 채점 ----------
def grade(r, entries, ecf_credit=0.5):
    """entries={칸 id: 입력}. number/dropdown/citation 은 문자열, je 는 행 목록. 반환 {칸 id: (credit 0..1, kind)}"""
    res = {}
    base = build_ns(r["params"], r["derived"])
    loc = dict(base)
    for c in r["cells"]:
        if c["kind"] == "number":
            pv_ = parse_num(entries.get(c["id"]))
            loc[c["id"]] = c["answer"] if pv_ != pv_ else pv_          # NaN 이면 정답값 유지
    for c in r["cells"]:
        e = entries.get(c["id"])
        blank = e is None or (isinstance(e, str) and e.strip() == "") or (isinstance(e, list) and not e)
        if blank:
            res[c["id"]] = (0.0, "blank")
            continue
        if c["kind"] == "dropdown":
            res[c["id"]] = (1.0, "ok") if e == c["answer"] else (0.0, "wrong")
        elif c["kind"] == "citation":
            g = grade_std(c, e)
            res[c["id"]] = (g, "ok" if g == 1 else "half" if g else "wrong")
        elif c["kind"] == "number":
            v = parse_num(e)
            if v != v:
                res[c["id"]] = (0.0, "wrong")
            elif abs(v - c["answer"]) <= c["tol"] + 1e-9:
                res[c["id"]] = (1.0, "ok")
            elif c["ecf"] and c["deps"]:
                try:
                    alt = _ev(c["expr"], loc)
                except Exception:
                    alt = None
                res[c["id"]] = (ecf_credit, "ecf") if alt is not None and abs(v - alt) <= c["tol"] + 1e-9 else (0.0, "wrong")
            else:
                res[c["id"]] = (0.0, "wrong")
        else:
            alt_vals = [rnd(_ev(l["expr"], loc)) if l["deps"] else None for l in c["lines"]]
            g = grade_je(c, e, alt_vals)
            res[c["id"]] = (g["score"], "ok" if g["perfect"] else "partial")
    return res
