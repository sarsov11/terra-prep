# TBS 공용 라이브러리: 계산 함수, 셀 정의 헬퍼, 렌더러, 변형 생성기, 인용 정규화.
# 작성 스크립트와 검산 스크립트가 같이 쓴다. 발문의 세율표·한도는 전시물로 주어지는 가정치.
import math, re, random, copy

def rnd(x):
    return int(math.floor(x + 0.5))

def d(x):
    return "${:,}".format(rnd(x))

# 2026 세율표(Rev. Proc. 2025-32 기준, area4_lib.py 와 동일) -- 전시물에 표로 제시한다
SINGLE = [(12400, .10), (50400, .12), (105700, .22), (201775, .24), (256225, .32), (640600, .35), (None, .37)]

def tax(ti, sched=SINGLE):
    ti = max(0, ti)
    t, lo = 0.0, 0
    for top, r in sched:
        hi = ti if top is None else min(ti, top)
        if hi > lo:
            t += (hi - lo) * r
        if top is None or ti <= top:
            break
        lo = top
    return t

def tax_s(ti):
    return tax(ti, SINGLE)

def se_tax(net, base=184500):
    e = net * 0.9235
    return 0.124 * min(e, base) + 0.029 * e

def dual_basis(price, gain_basis, loss_basis):
    """증여받은 자산의 이중 기준가액(§1015(a)): 이익이면 gain_basis, 손실이면 loss_basis, 사이면 0"""
    if price > gain_basis:
        return price - gain_basis
    if price < loss_basis:
        return price - loss_basis
    return 0

def ltcg_tax(ordinary_ti, gain, zero_top, fifteen_top):
    """순장기자본이득 세액: 0% / 15% / 20% 구간(과세소득 위치 기준)"""
    lo = ordinary_ti
    hi = ordinary_ti + gain
    z = max(0, min(hi, zero_top) - lo)
    f = max(0, min(hi, fifteen_top) - max(lo, zero_top))
    t = max(0, hi - max(lo, fifteen_top))
    return z * 0 + f * 0.15 + t * 0.20

NS_BASE = {"rnd": rnd, "min": min, "max": max, "abs": abs, "tax_s": tax_s, "se_tax": se_tax,
           "dual_basis": dual_basis, "ltcg_tax": ltcg_tax}

# ---------- 셀 정의 헬퍼 ----------
def N(id, label, expr, why, steps, hints, traps=None, tol=1, fmt="$", ecf=True):
    """숫자 입력 칸. expr 은 파라미터·파생값·앞선 칸 id 를 쓰는 파이썬 식. traps=[(식, 메시지)]"""
    return {"id": id, "kind": "number", "label": label, "expr": expr, "fmt": fmt, "tol": tol,
            "why": why, "steps": steps, "hints": hints, "traps": [{"expr": e, "msg": m} for e, m in (traps or [])],
            "ecf": ecf}

def D(id, label, options, answer, why, hints, wrong=None):
    """드롭다운 칸. answer 는 options 안의 문자열. wrong={선택지: 왜 틀렸는지}"""
    assert answer in options, (id, answer)
    return {"id": id, "kind": "dropdown", "label": label, "options": list(options), "answer": answer,
            "why": why, "steps": [], "hints": hints, "wrong_msgs": wrong or {}}

def C(id, label, accept, why, hints, link, partial=None, ask="IRC section (and subsection if asked)"):
    """인용 입력 칸. accept/partial 은 정규화된 문자열 목록(정규화 규칙은 norm_cite)."""
    return {"id": id, "kind": "citation", "label": label, "ask": ask, "accept": accept, "partial": partial or [],
            "link": link, "why": why, "steps": [], "hints": hints}

def X(id, title, kind, body):
    """전시물 한 개. kind: email | memo | return_excerpt | contract | table | notes | statute_note"""
    return {"id": id, "title": title, "kind": kind, "body": body}

def T(id, area, fmt, title, scenario, task, exhibits, cells, params, blueprint, difficulty, minutes,
      testable_from="2026-01-01", cite=None, vary=None, guards=None, derived=None, law_note="", tags=None):
    return {"id": id, "type": "tbs", "area": area, "format": fmt, "title": title, "scenario": scenario, "task": task,
            "exhibits": exhibits, "cells": cells, "params": params, "vary": vary or {}, "guards": guards or [],
            "derived": derived or [], "blueprint": blueprint, "difficulty": difficulty, "est_minutes": minutes,
            "testable_from": testable_from, "law_asof": "2026-09-29", "cite": cite or [], "law_note": law_note}

# ---------- 인용 정규화 ----------
def norm_cite(s):
    """'IRC § 6694(a)', 'Sec. 6694(a)', '26 USC 6694(a)', 'Internal Revenue Code section 6694 (a)' -> '6694(a)'
    Circular 230: '31 CFR 10.29', 'Circular 230 §10.29' -> '10.29'.  Reg: 'Reg. 1.1031(d)-2' -> '1.1031(d)-2'"""
    s = s.lower().strip()
    s = s.replace("§", " ").replace("§", " ")
    s = re.sub(r"internal revenue code|i\.?r\.?c\.?|u\.?s\.?c\.?|26 usc|section|sec\.?|treas\.? ?reg\.?|reg\.?|circular 230|31 ?c\.?f\.?r\.?|26 ?c\.?f\.?r\.?|part 10|title 26|title 31", " ", s)
    s = re.sub(r"\b(26|31)\b(?=\s+\d)", " ", s)
    s = re.sub(r"[\s\.,;]+$", "", s)
    s = re.sub(r"\s+", "", s)
    s = s.replace("(a)(", "(a)(")  # no-op, 형식 유지
    return s

def grade_cite(cell, text):
    n = norm_cite(text)
    if n in [a.lower() for a in cell["accept"]]:
        return 1.0
    if n in [a.lower() for a in cell.get("partial", [])]:
        return 0.5
    return 0.0

# ---------- 평가 / 렌더 ----------
def _ev(expr, ns):
    return eval(expr, {"__builtins__": {}}, ns)

def build_ns(params, derived, cells=None, answers=None):
    ns = dict(NS_BASE)
    ns.update(params)
    for name, expr in derived:
        ns[name] = _ev(expr, ns)
    return ns

def solve(t, params=None):
    """정답 계산: 파생값과 각 숫자 칸의 값을 반환 (칸 id -> 값)"""
    p = dict(t["params"]) if params is None else dict(params)
    ns = build_ns(p, t["derived"])
    vals = {}
    for c in t["cells"]:
        if c["kind"] == "number":
            v = _ev(c["expr"], ns)
            v = rnd(v) if c.get("fmt") != "%dec" else v
            vals[c["id"]] = v
            ns[c["id"]] = v
    return ns, vals

class _F(dict):
    def __missing__(self, k):
        raise KeyError(k)

def fill(s, ns):
    if isinstance(s, str):
        return s.format_map(_F(ns))
    if isinstance(s, list):
        return [fill(x, ns) for x in s]
    if isinstance(s, dict):
        return {k: fill(v, ns) for k, v in s.items()}
    return s

TEXT_KEYS = ("title", "scenario", "task", "exhibits", "label", "why", "steps", "hints", "msg", "body", "options", "answer", "wrong_msgs")

def render(t, params=None, shuffle_seed=None):
    """템플릿 t 를 params 로 채운 완성 TBS 를 만든다(정답 값·허용오차·ECF 식 포함)."""
    ns, vals = solve(t, params)
    out = copy.deepcopy(t)
    for k in ("title", "scenario", "task", "exhibits"):
        out[k] = fill(t[k], ns)
    cells = []
    for c in t["cells"]:
        c2 = copy.deepcopy(c)
        for k in ("label", "why", "steps", "hints"):
            c2[k] = fill(c[k], ns)
        if c["kind"] == "number":
            c2["answer"] = vals[c["id"]]
            deps = [x for x in re.findall(r"\b(c\d+)\b", c["expr"])]
            c2["deps"] = sorted(set(deps))
            c2["traps"] = [{"expr": tr["expr"], "value": rnd(_ev(tr["expr"], ns)), "msg": fill(tr["msg"], ns)} for tr in c["traps"]]
        elif c["kind"] == "dropdown":
            c2["options"] = fill(c["options"], ns)
            c2["answer"] = fill(c["answer"], ns)
            c2["wrong_msgs"] = fill(c["wrong_msgs"], ns)
        cells.append(c2)
    out["cells"] = cells
    # 드롭다운 보기 순서: id 기반 고정 셔플(정답 위치 단서 제거)
    rng = random.Random(shuffle_seed or t["id"])
    for c in out["cells"]:
        if c["kind"] == "dropdown":
            rng.shuffle(c["options"])
    return out

def variant(t, seed):
    """숫자를 바꾼 변형: vary={파라미터: [후보값]} 에서 무작위로 골라 guards 를 만족할 때까지 재추출."""
    rng = random.Random(seed)
    for _ in range(200):
        p = dict(t["params"])
        for k, choices in t["vary"].items():
            p[k] = rng.choice(choices)
        ns = build_ns(p, t["derived"])
        if all(_ev(g, ns) for g in t["guards"]):
            return render(t, p, shuffle_seed=t["id"] + str(seed)), p
    raise RuntimeError("guards unsatisfiable " + t["id"])

# ---------- 채점(참고 구현) ----------
def grade(t_rendered, entries, ecf_credit=0.5):
    """entries={칸 id: 입력}. 숫자 칸은 정답±tol 이면 1, 앞선 칸 입력으로 다시 계산한 값(ECF)과 같으면 ecf_credit."""
    res, ns = {}, {}
    for c in t_rendered["cells"]:
        if c["kind"] == "number" and c["id"] in entries:
            try:
                ns[c["id"]] = float(entries[c["id"]])
            except ValueError:
                pass
    base = build_ns(t_rendered["params"], t_rendered["derived"])
    for c in t_rendered["cells"]:
        e = entries.get(c["id"])
        if e is None or e == "":
            res[c["id"]] = 0.0
            continue
        if c["kind"] == "number":
            v = float(e)
            if abs(v - c["answer"]) <= c["tol"]:
                res[c["id"]] = 1.0
            elif c.get("ecf") and c["deps"]:
                loc = dict(base)
                loc.update({k: ns[k] for k in c["deps"] if k in ns})
                for k in c["deps"]:
                    loc.setdefault(k, 0)
                # 정답 칸 값으로 채운 뒤 학생 입력으로 덮어써 학생 논리대로 재계산
                for k in [x["id"] for x in t_rendered["cells"] if x["kind"] == "number"]:
                    loc.setdefault(k, next(y["answer"] for y in t_rendered["cells"] if y["id"] == k))
                    if k in ns:
                        loc[k] = ns[k]
                try:
                    alt = _ev(c["expr"], loc)
                except Exception:
                    alt = None
                res[c["id"]] = ecf_credit if alt is not None and abs(v - alt) <= c["tol"] else 0.0
            else:
                res[c["id"]] = 0.0
        elif c["kind"] == "dropdown":
            res[c["id"]] = 1.0 if e == c["answer"] else 0.0
        else:
            res[c["id"]] = grade_cite(c, e)
    return res
