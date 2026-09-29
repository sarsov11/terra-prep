"""FAR TBS 검산: (1) 손계산(식과 다른 방식으로 짠 독립 계산) 대조 - 기본값 + 변형 200개 전부
(2) 형식 규칙 (3) 식 문법(tbs.js 파서 호환) (4) 변형 생성 200회·만점 채점·분개 균형 (5) ECF·분개 부분점수·번호 정규화 시험.
사용: py tbs_far_계산검산.py   (종료코드 0 = 전부 통과)"""
import json, os, re, sys, collections, math
sys.stdout.reconfigure(encoding="utf-8")
from tbs_far_lib import *
import tbs_far_items_1, tbs_far_items_2, tbs_far_items_3

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "tbs_far.json"), encoding="utf-8"))
items = data["items"]
RAW = {t["id"]: t for m in (tbs_far_items_1, tbs_far_items_2, tbs_far_items_3) for t in m.ITEMS}
errs = []
def err(i, m): errs.append((i, m))
PH = re.compile(r"\{[A-Za-z_][A-Za-z_0-9]*(:,|:[0-9])?\}")

def R(x, d=0):          # 독립 반올림(사사오입): 문자열 경유로 부동소수 오차를 피한다
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(1).scaleb(-d)
    return float(Decimal(repr(round(x, 9))).quantize(q, rounding=ROUND_HALF_UP)) if d else int(Decimal(repr(round(x, 9))).quantize(Decimal(1), rounding=ROUND_HALF_UP))

# ------------------------------------------------------------------ 손계산: 식과 다른 절차
def h_i001(p):
    # 대차대조표를 맞춰 현금 증감을 따로 구하고, 현금흐름표 합계와 대조한다
    a0 = p["ar0"] + p["inv0"] + p["eq0"] - p["ad0"]
    l0 = p["ap0"] + p["bp0"] + p["cs0"] + p["re0"]
    cash0 = l0 - a0
    eq1 = p["eq0"] + p["buy"] - p["sc"]
    ad1 = p["ad0"] + p["dep"] - p["sad"]
    re1 = p["re0"] + p["ni"] - p["dv"]
    a1 = p["ar1"] + p["inv1"] + eq1 - ad1
    l1 = p["ap1"] + p["bp0"] + p["bpi"] + p["cs0"] + p["csi"] + re1
    cash1 = l1 - a1
    loss = p["sc"] - p["sad"] - p["sp"]
    ops = p["ni"] + p["dep"] + loss
    ops -= p["ar1"] - p["ar0"]
    ops -= p["inv1"] - p["inv0"]
    ops += p["ap1"] - p["ap0"]
    inv = -p["buy"] + p["sp"]
    fin = -p["dv"] + p["bpi"] + p["csi"]
    assert ops + inv + fin == cash1 - cash0, "현금흐름 합계 != 대차대조표 현금 증감"
    return {"c1": p["dep"], "c2": loss, "c3": ops, "c4": -p["buy"], "c5": inv, "c6": -p["dv"], "c7": fin, "c8": cash1 - cash0}

def h_i002(p):
    mon = []
    for mth in range(1, 13):
        n = p["s0"]
        if mth >= 4: n += p["iss"]
        if mth >= 10: n -= p["tr"]
        mon.append(n)
    wa = R(sum(mon) / 12 * (100 + p["sd"]) / 100)
    inc = p["ni"] - p["pd"]
    basic = R(inc / wa, 2)
    rep = p["opt"] * p["strike"] / p["avg"]
    inc_opt = R(p["opt"] - rep)
    bond_int = p["F"] * p["cr"] / 100
    after = R(bond_int * (1 - p["tx"] / 100))
    dil = R((inc + after) / (wa + inc_opt + p["cv"]), 2)
    return {"c1": wa, "c2": inc, "c3": basic, "c4": inc_opt, "c5": after, "c6": dil}

def h_i003(p):
    net_cap = p["capcost"] - p["capad"]
    ltl = -(p["bonds"] + p["accint"] + p["compabs"])
    npos = p["fb"] + net_cap + ltl + p["unav"] + p["isf"]
    chg = p["rev"] - p["exp"] + p["proceeds"]
    cap = p["capout"] - p["dep"]
    debt = p["princ"] - p["proceeds"]
    cnp = chg + cap + debt + p["dunav"] - p["dabs"] + p["isfchg"]
    return {"c1": net_cap, "c2": ltl, "c3": npos, "c4": chg, "c5": cap, "c6": debt, "c7": cnp}

def h_i004(p):
    ca = p["cash"] + p["ms"] + p["ar1"] + p["inv1"] + p["pre"]
    cr = R(ca / p["cl"], 2)
    q = R((p["cash"] + p["ms"] + p["ar1"]) / p["cl"], 2)
    at = R(p["sales"] / ((p["ar0"] + p["ar1"]) / 2), 2)
    days = 365 / (p["sales"] / ((p["ar0"] + p["ar1"]) / 2))
    it = R(p["cogs"] / ((p["inv0"] + p["inv1"]) / 2), 2)
    tie = R((p["ni"] + p["tax"] + p["ie"]) / p["ie"], 2)
    roe = R((p["ni"] - p["pd"]) / ((p["ce0"] + p["ce1"]) / 2) * 100, 1)
    return {"c1": cr, "c2": q, "c3": at, "c4": days, "c5": it, "c6": tie, "c7": roe}

def h_ii001(p):
    life, m = p["life"], p["m"]
    rate = 2 / life
    y1 = R(p["cost"] * rate * m / 12)
    y2 = R((p["cost"] - y1) * rate)
    bv = p["cost"] - y1 - y2
    sl = (p["cost"] - p["sal"]) / life * m / 12
    tot_months = (life + p["dl"]) * 12
    used = m + 12
    y3 = R((bv - p["sal2"]) * 12 / (tot_months - used))
    return {"c1": y1, "c2": y2, "c3": bv, "c4": R(y1 - sl), "c5": y3, "c6": y1 + y2 + y3}

def h_ii002(p):
    p1 = p["p0"] + p["d1"]; p2 = p1 + p["d2"]; p3 = p2 + p["d3"]
    layers = [(p["u0"], p["p0"]), (p["u1"], p1), (p["u2"], p2), (p["u3"], p3)]
    avail = sum(u for u, _ in layers); goods = sum(u * c for u, c in layers)
    eu = avail - p["sold"]
    def take(order, n):
        cost = 0
        for u, c in order:
            t = min(u, n); cost += t * c; n -= t
        return cost
    fifo_end = take(list(reversed(layers)), eu)         # 신규 층부터 남는다
    lifo_end = take(layers, eu)                          # 오래된 층부터 남는다
    return {"c1": eu, "c2": fifo_end, "c3": goods - fifo_end, "c4": R(goods / avail, 2), "c5": goods - lifo_end, "c6": max(0, fifo_end - eu * p["nrv"])}

def h_ii003(p):
    req = 0
    for b, r in ((p["b0"], p["r0"]), (p["b1"], p["r1"]), (p["b2"], p["r2"]), (p["b3"], p["r3"])):
        req += b * r / 100
    req = R(req)
    pre = p["al0"] - p["wo"] + p["rec"]
    tot = p["b0"] + p["b1"] + p["b2"] + p["b3"]
    cash = p["fa"] - p["fa"] * p["fee"] / 100 - p["fa"] * p["hb"] / 100
    return {"c1": req, "c2": pre, "c3": req - pre, "c4": tot - req, "c5": R(cash), "c6": R(p["fa"] * p["fee"] / 100), "c7": R(p["fa"] * p["hb"] / 100)}

def h_ii005(p):
    F, n = p["F"], 10
    cpn = R(F * p["s"] / 200)
    i = p["r"] / 200
    price = R(sum(cpn / (1 + i) ** k for k in range(1, n + 1)) + F / (1 + i) ** n)     # 기간별 할인 합
    cv = price; exp = []
    for k in range(2):
        e = R(cv * i); exp.append(e); cv = cv + e - cpn
        if k == 0: e1 = e
    pay = F * p["p"] / 100
    return {"c1": price, "c2": [("D", "cash", price), ("D", "disc", F - price), ("C", "bondsp", F)],
            "c3": [("D", "intexp", e1), ("C", "cash", cpn), ("C", "disc", e1 - cpn)],
            "c4": sum(exp), "c5": cv,
            "c6": [("D", "bondsp", F), ("D", "lossext", R(pay - cv)), ("C", "disc", F - cv), ("C", "cash", R(pay))]}

def h_ii006(p):
    out_ = p["sh"] - p["tsn"] + p["rin"]
    sd_sh = out_ * p["sdp"] / 100
    after = out_ + sd_sh
    return {"c1": [("D", "ts", p["tsn"] * p["tsp"]), ("C", "cash", p["tsn"] * p["tsp"])],
            "c2": [("D", "cash", p["rin"] * p["rpx"]), ("C", "ts", p["rin"] * p["tsp"]), ("C", "apicts", p["rin"] * (p["rpx"] - p["tsp"]))],
            "c3": out_, "c4": sd_sh,
            "c5": [("D", "re", sd_sh * p["fv"]), ("C", "cs", sd_sh * p["par"]), ("C", "apic", sd_sh * (p["fv"] - p["par"]))],
            "c6": after, "c7": [("D", "re", after * p["dvps"]), ("C", "divpay", after * p["dvps"])]}

def h_ii007(p):
    share = p["na"] * p["pct"] / 100
    cost = share + p["ex"]
    inc = R(p["ni"] * p["pct"] / 100 - p["ex"] / p["life"])
    dv = R(p["div"] * p["pct"] / 100)
    return {"c1": [("D", "invassoc", cost), ("C", "cash", cost)], "c2": inc, "c3": [("D", "invassoc", inc), ("C", "eqinc", inc)],
            "c4": [("D", "cash", dv), ("C", "invassoc", dv)], "c5": cost + inc - dv,
            "c6": [("D", "aoci", p["afc"] - p["afv"]), ("C", "afs", p["afc"] - p["afv"])],
            "c7": [("D", "eqsec", p["eqv"] - p["eqc"]), ("C", "ugl", p["eqv"] - p["eqc"])]}

def h_iii001(p):
    n, r, pmt = p["n"], p["r"] / 100, p["pmt"]
    pv = R(sum(pmt / (1 + r) ** k for k in range(n)))                # 기초 지급: 지급 시점 0..n-1
    bal = pv - pmt
    intr = R(bal * r)
    am = R(pv / n)
    return {"c2": pv, "c3": [("D", "rou", pv), ("C", "leaseliab", pv)], "c4": [("D", "leaseliab", pmt), ("C", "cash", pmt)],
            "c5": intr, "c6": am, "c7": [("D", "intexp", intr), ("C", "leaseliab", intr), ("D", "amortexp", am), ("C", "accamort", am)], "c8": bal + intr}

def h_iii002(p):
    tp = p["sspE"] + p["sspS"]
    e = R(p["P"] * p["sspE"] / tp)
    s = p["P"] - e
    rev = R(e * (100 - p["ret"]) / 100)
    cg = R(p["cost"] * (100 - p["ret"]) / 100)
    earned = R(s * p["m"] / p["N"])
    return {"c1": e, "c2": s, "c3": [("D", "cash", p["P"]), ("C", "rev", rev), ("C", "refundliab", e - rev), ("C", "unearned", s)],
            "c4": [("D", "cogs", cg), ("D", "rrg", p["cost"] - cg), ("C", "inv", p["cost"])], "c5": earned,
            "c6": [("D", "unearned", earned), ("C", "rev", earned)], "c7": s - earned}

def h_iii003(p):
    t = p["t"] / 100
    ti = p["pti"]
    ti += p["wacc"] - p["wpaid"]
    ti -= p["taxdep"] - p["bookdep"]
    ti -= p["muni"]
    ti += p["fines"]
    cur = R(ti * t)
    dtl0 = p["tdb0"] * t; dta0 = p["wl0"] * t
    dtl1 = R((p["tdb0"] + p["taxdep"] - p["bookdep"]) * t)
    dta1 = R((p["wl0"] + p["wacc"] - p["wpaid"]) * t)
    exp = cur + (dtl1 - dtl0) - (dta1 - dta0)
    return {"c1": ti, "c2": cur, "c3": dtl1, "c4": dta1, "c5": exp,
            "c6": [("D", "taxexp", exp), ("D", "dta", dta1 - dta0), ("C", "taxpay", cur), ("C", "dtl", dtl1 - dtl0)],
            "c7": R(exp / p["pti"] * 100, 1)}

def h_iii004(p):
    dep_y = p["cost"] / p["life"]
    acc = sum(dep_y for _ in range(2))          # 1~2년차
    pre = p["cost"] - acc
    tax = R(pre * p["t"] / 100)
    net = pre - tax
    return {"c1": dep_y, "c2": acc, "c3": pre, "c4": tax, "c5": net,
            "c6": [("D", "equip", p["cost"]), ("C", "accdep", acc), ("C", "taxpay", tax), ("C", "re", net)]}

def h_iii005(p):
    exp = p["sales"] * p["wr"] / 100
    return {"c1": exp, "c2": [("D", "warrantyexp", exp), ("C", "warrantyliab", exp)], "c3": [("D", "warrantyliab", p["claims"]), ("C", "cash", p["claims"])],
            "c4": p["wl0"] + exp - p["claims"], "c5": p["lo"], "c6": [("D", "lawloss", p["lo"]), ("C", "lawliab", p["lo"])], "c7": p["hi"] - p["lo"]}

def h_iii006(p):
    c1 = p["est1"] * p["pct1"] / 100
    c2 = p["est2"] * p["pct2"] / 100
    pc1 = c1 / p["est1"] * 100
    rev1 = R(p["price"] * pc1 / 100)
    gp1 = rev1 - c1
    pc2 = c2 / p["est2"] * 100
    rev2 = R(p["price"] * pc2 / 100) - rev1
    loss_total = p["est2"] - p["price"]
    return {"c1": R(pc1, 1), "c2": rev1, "c3": gp1, "c4": R(pc2, 1), "c5": rev2, "c6": -loss_total - gp1}

HAND = {"FAR-I-T-001": h_i001, "FAR-I-T-002": h_i002, "FAR-I-T-003": h_i003, "FAR-I-T-004": h_i004,
        "FAR-II-T-001": h_ii001, "FAR-II-T-002": h_ii002, "FAR-II-T-003": h_ii003, "FAR-II-T-005": h_ii005, "FAR-II-T-006": h_ii006, "FAR-II-T-007": h_ii007,
        "FAR-III-T-001": h_iii001, "FAR-III-T-002": h_iii002, "FAR-III-T-003": h_iii003, "FAR-III-T-004": h_iii004, "FAR-III-T-005": h_iii005, "FAR-III-T-006": h_iii006}

def compare_hand(tid, rendered, params, tag):
    exp = HAND[tid](params)
    for c in rendered["cells"]:
        if c["id"] not in exp:
            continue
        e = exp[c["id"]]
        if c["kind"] == "number":
            tol = c["tol"] if c["id"] != "c4" or tid != "FAR-I-T-004" else 1
            if abs(c["answer"] - e) > tol + 1e-9:
                err(tid, "%s 손계산 불일치 %s: 식=%s 손=%s" % (tag, c["id"], c["answer"], e)); return False
        elif c["kind"] == "je":
            mine = sorted((l["s"], l["a"], l["v"]) for l in c["lines"])
            hand = sorted((s, a, R(v)) for s, a, v in e)
            if len(mine) != len(hand) or any(x[:2] != y[:2] or abs(x[2] - y[2]) > 1 for x, y in zip(mine, hand)):
                err(tid, "%s 분개 손계산 불일치 %s: 식=%s 손=%s" % (tag, c["id"], mine, hand)); return False
    return True

# ------------------------------------------------------------------ (1) 기본값 손계산 + 첫 문서 상수 확인
for t in items:
    if t["id"] in HAND:
        compare_hand(t["id"], t, t["params"], "기본값")

# 알려진 고정 답(손으로 푼 값)
FIXED = {
 "FAR-I-T-001": {"c1": 95000, "c2": 10000, "c3": 285000, "c4": -250000, "c5": -230000, "c6": -40000, "c7": 120000, "c8": 175000},
 "FAR-I-T-002": {"c1": 1265000, "c2": 2250000, "c3": 1.78, "c4": 12000, "c5": 75000, "c6": 1.74},
 "FAR-I-T-003": {"c1": 11700000, "c2": -5315000, "c3": 11115000, "c4": 1500000, "c5": 700000, "c6": -500000, "c7": 1750000},
 "FAR-I-T-004": {"c1": 1.73, "c2": 0.87, "c3": 16.0, "c4": 23, "c5": 6.67, "c6": 8.0, "c7": 23.3},
 "FAR-II-T-001": {"c1": 64000, "c2": 230400, "c3": 345600, "c4": 34000, "c5": 45274, "c6": 339674},
 "FAR-II-T-002": {"c1": 2500, "c2": 31000, "c3": 82000, "c4": 11.3, "c5": 87500, "c6": 3500},
 "FAR-II-T-003": {"c1": 49500, "c2": 26000, "c3": 23500, "c4": 1090500, "c5": 174000, "c6": 6000, "c7": 20000},
 "FAR-II-T-005": {"c1": 918891, "c4": 73782, "c5": 932673},
 "FAR-II-T-006": {"c3": 488000, "c4": 48800, "c6": 536800},
 "FAR-II-T-007": {"c2": 108000, "c5": 978000},
 "FAR-III-T-001": {"c2": 446511, "c5": 20791, "c6": 89302, "c8": 367302},
 "FAR-III-T-002": {"c1": 72000, "c2": 18000, "c5": 4500, "c7": 13500},
 "FAR-III-T-003": {"c1": 735000, "c2": 183750, "c3": 70000, "c4": 17500, "c5": 196250, "c7": 24.5},
 "FAR-III-T-004": {"c1": 24000, "c2": 48000, "c3": 72000, "c4": 18000, "c5": 54000},
 "FAR-III-T-005": {"c1": 60000, "c4": 45000, "c5": 300000, "c7": 200000},
 "FAR-III-T-006": {"c1": 30.0, "c2": 1500000, "c3": 300000, "c4": 60.0, "c5": 1500000, "c6": -800000},
}
for tid, exp in FIXED.items():
    t = next(x for x in items if x["id"] == tid)
    for c in t["cells"]:
        if c["kind"] == "number" and c["id"] in exp and abs(c["answer"] - exp[c["id"]]) > 1e-9:
            err(tid, "고정 정답표 불일치 %s: %s != %s" % (c["id"], c["answer"], exp[c["id"]]))
# 분개 고정 정답(대표 줄)
JEFIX = {
 ("FAR-II-T-005", "c2"): [("D", "cash", 918891), ("D", "disc", 81109), ("C", "bondsp", 1000000)],
 ("FAR-II-T-005", "c3"): [("D", "intexp", 36756), ("C", "cash", 30000), ("C", "disc", 6756)],
 ("FAR-II-T-005", "c6"): [("D", "bondsp", 1000000), ("D", "lossext", 87327), ("C", "disc", 67327), ("C", "cash", 1020000)],
 ("FAR-II-T-006", "c5"): [("D", "re", 1756800), ("C", "cs", 244000), ("C", "apic", 1512800)],
 ("FAR-III-T-003", "c6"): [("D", "taxexp", 196250), ("D", "dta", 7500), ("C", "taxpay", 183750), ("C", "dtl", 20000)],
 ("FAR-III-T-004", "c6"): [("D", "equip", 120000), ("C", "accdep", 48000), ("C", "taxpay", 18000), ("C", "re", 54000)],
 ("FAR-III-T-002", "c3"): [("D", "cash", 90000), ("C", "rev", 68400), ("C", "refundliab", 3600), ("C", "unearned", 18000)],
}
for (tid, cid), exp in JEFIX.items():
    t = next(x for x in items if x["id"] == tid)
    c = next(x for x in t["cells"] if x["id"] == cid)
    if sorted((l["s"], l["a"], l["v"]) for l in c["lines"]) != sorted(exp):
        err(tid, "분개 고정 정답 불일치 " + cid)

# ------------------------------------------------------------------ (2) 형식 규칙
areas = collections.Counter(t["area"] for t in items)
fmts = collections.Counter(t["format"] for t in items)
if dict(areas) != {"I": 8, "II": 8, "III": 8}: err("전체", "Area 분포 %s" % dict(areas))
if dict(fmts) != {"numeric_table": 8, "journal_entry": 8, "document_review": 2, "dropdown_judgment": 2, "research": 4}: err("전체", "형식 분포 %s" % dict(fmts))
if len(items) != 24 or len({t["id"] for t in items}) != 24: err("전체", "개수/ID 중복")
kinds_all = collections.Counter(c["kind"] for t in items for c in t["cells"])
for t in items:
    i = t["id"]
    n = len(t["cells"])
    if not 5 <= n <= 8: err(i, "칸 수 %d" % n)
    if len({c["id"] for c in t["cells"]}) != n: err(i, "칸 id 중복")
    if not t["exhibits"]: err(i, "전시물 없음")
    body = json.dumps({k: v for k, v in t.items() if k != "template"}, ensure_ascii=False)
    m = PH.search(body)
    if m: err(i, "미치환 자리표시자 " + m.group(0))
    for f in ("area", "group", "topic", "task", "skill"):
        if not t["blueprint"].get(f): err(i, "blueprint." + f)
    if t["difficulty"] not in (1, 2, 3): err(i, "난이도")
    if not t.get("testable_from") or not t.get("cite"): err(i, "testable_from/cite")
    for x in t["exhibits"]:
        if not x["body"]: err(i, "전시물 본문 없음 " + x["id"])
        if x["kind"] == "table" and len({len(r) for r in x["body"]}) != 1: err(i, "표 열 수 불일치 " + x["id"])
    prev = -1
    for c in t["cells"]:
        if not c.get("why"): err(i, c["id"] + " 해설 없음")
        if not c.get("hints") or len(c["hints"]) < (1 if c["kind"] in ("dropdown",) else 2): err(i, c["id"] + " 힌트 부족")
        if c["kind"] == "number":
            if not c["steps"]: err(i, c["id"] + " 풀이 단계 없음")
            if c["tol"] not in (0, 1, 0.01, 0.1): err(i, c["id"] + " tol")
            if c["fmt"] not in DEC: err(i, c["id"] + " fmt")
            for tr in c["traps"]:
                if tr["value"] == c["answer"]: err(i, c["id"] + " 오답 진단값이 정답과 같음 " + tr["expr"])
            for d in c["deps"]:
                if not any(x["id"] == d and x["kind"] == "number" for x in t["cells"]): err(i, c["id"] + " 앞칸 아닌 deps " + d)
                elif int(d[1:]) >= int(c["id"][1:]): err(i, c["id"] + " deps 가 뒤 칸 " + d)
        elif c["kind"] == "dropdown":
            if c["answer"] not in c["options"] or len(set(c["options"])) != len(c["options"]): err(i, c["id"] + " 보기")
            for o in c["options"]:
                if o != c["answer"] and o not in c["wrong_msgs"]: err(i, c["id"] + " 오답 해설 없음: " + o[:30])
            if not 3 <= len(c["options"]) <= 7: err(i, c["id"] + " 보기 수")
        elif c["kind"] == "citation":
            if not c["accept"] or (c["link"] and not c["link"].startswith("https://")): err(i, c["id"] + " 인용 정답/링크")
            for a in c["accept"] + c["partial"]:
                if norm_std(a) != a: err(i, c["id"] + " accept 가 정규형 아님 " + a)
        elif c["kind"] == "je":
            if c["points"] != len(c["lines"]): err(i, c["id"] + " points")
            if len(c["lines"]) < 2: err(i, c["id"] + " 줄 수")
            if not c["mist"]: err(i, c["id"] + " 흔한 실수 규칙 없음")
            for l in c["lines"]:
                if l["a"] not in COA or not l.get("why"): err(i, c["id"] + " 줄 계정/해설")
                for d in l["deps"]:
                    if not any(x["id"] == d and x["kind"] == "number" for x in t["cells"]): err(i, c["id"] + " 줄 deps " + d)
            if len(c["accounts"]) < len(c["lines"]) + 2: err(i, c["id"] + " 계정 목록이 너무 짧음")
    kinds = {c["kind"] for c in t["cells"]}
    fm = t["format"]
    if fm == "numeric_table" and "number" not in kinds: err(i, "숫자 칸 없음")
    if fm == "journal_entry" and "je" not in kinds: err(i, "분개 칸 없음")
    if fm == "research" and kinds != {"citation"}: err(i, "인용 칸만이어야 함")
    if fm in ("document_review", "dropdown_judgment") and kinds != {"dropdown"}: err(i, "드롭다운 칸만이어야 함")
pos = collections.Counter()
for t in items:
    for c in t["cells"]:
        if c["kind"] == "dropdown" and len(c["options"]) == 3:
            pos[c["options"].index(c["answer"])] += 1
        if c["kind"] == "dropdown" and len(c["options"]) == 4:
            pos["4:%d" % c["options"].index(c["answer"])] += 1
print("드롭다운 정답 위치:", dict(pos))
d3 = {k: v for k, v in pos.items() if not str(k).startswith("4:")}
d4 = {k: v for k, v in pos.items() if str(k).startswith("4:")}
if d3 and max(d3.values()) / sum(d3.values()) > 0.5: err("전체", "3지 정답 위치 편중 %s" % d3)
if d4 and max(d4.values()) / sum(d4.values()) > 0.45: err("전체", "4지 정답 위치 편중 %s" % d4)
keep = sum(1 for t in items if t["format"] == "document_review" for c in t["cells"] if c["answer"] == "Keep as written")
dr = sum(len(t["cells"]) for t in items if t["format"] == "document_review")
print("문서검토 Keep as written: %d/%d" % (keep, dr))
if not dr * 0.25 <= keep <= dr * 0.5: err("전체", "Keep as written 비율")

sheet = json.load(open(os.path.join(HERE, "tbs_far_문제지_검산용.json"), encoding="utf-8"))
raw_s = json.dumps(sheet, ensure_ascii=False)
for bad in ('"answer"', '"why"', '"steps"', '"expr"', '"accept"', '"hints"', '"traps"', '"lines"', '"mist"', '"wrong_msgs"', '"partial"'):
    if bad in raw_s: err("문제지", "정답 관련 키 노출 " + bad)
if len(sheet["items"]) != 24: err("문제지", "개수")

# ------------------------------------------------------------------ (3) 식 문법: tbs.js 파서가 받는 부분집합인지
TOK = re.compile(r"\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)|([A-Za-z_][A-Za-z_0-9]*)|(\*\*|//|<=|>=|==|!=|[-+*/%(),<>]))")
KW = {"and", "or", "not", "True", "False"}
def check_expr(tid, e, names):
    pos = 0
    toks = []
    while pos < len(e):
        m = TOK.match(e, pos)
        if not m:
            if e[pos:].strip() == "": break
            err(tid, "파서 비호환 문자: %r in %s" % (e[pos:pos + 6], e)); return
        pos = m.end()
        toks.append(m.group(2) if m.group(2) else None)
    for k, m in enumerate(TOK.finditer(e)):
        pass
    idents = [m.group(2) for m in TOK.finditer(e) if m.group(2)]
    for name in idents:
        call = re.search(r"\b%s\s*\(" % re.escape(name), e) is not None
        if call and name in KW: continue
        if call:
            if name not in FN_NAMES: err(tid, "허용되지 않은 함수 %s in %s" % (name, e))
        elif name not in names and name not in KW:
            err(tid, "알 수 없는 이름 %s in %s" % (name, e))
for tid, raw in RAW.items():
    names = set(raw["params"]) | {d[0] for d in raw["derived"]} | {c["id"] for c in raw["cells"]}
    for k, v in raw["vary"].items():
        if k not in raw["params"]: err(tid, "vary 키가 params 에 없음 " + k)
    for nme, e in raw["derived"]: check_expr(tid, e, names)
    for g in raw["guards"]: check_expr(tid, g, names)
    for c in raw["cells"]:
        if c["kind"] == "number":
            check_expr(tid, c["expr"], names)
            for tr in c["traps"]: check_expr(tid, tr["expr"], names)
        if c["kind"] == "je":
            for l in c["lines"]: check_expr(tid, l["expr"], names)
            for m_ in c["mist"]:
                if "expr" in m_: check_expr(tid, m_["expr"], names)
    for nme in list(raw["params"]) + [d[0] for d in raw["derived"]]:
        if nme in FN_NAMES or nme in KW: err(tid, "이름이 함수/예약어와 충돌 " + nme)

# ------------------------------------------------------------------ (4) 변형 200개
nv, nvar = 0, {}
for tid, raw in RAW.items():
    seen = set()
    for seed in range(200):
        try:
            v, p = variant(raw, seed)
        except Exception as e:
            err(tid, "변형 실패 seed=%d %s" % (seed, e)); break
        seen.add(json.dumps(p, sort_keys=True))
        body = json.dumps({k: x for k, x in v.items() if k != "template"}, ensure_ascii=False)
        if PH.search(body): err(tid, "변형 미치환 seed=%d %s" % (seed, PH.search(body).group(0))); break
        if tid in HAND and not compare_hand(tid, v, p, "seed=%d" % seed): break
        entries = {}
        for c in v["cells"]:
            if c["kind"] == "number":
                entries[c["id"]] = str(c["answer"])
            elif c["kind"] == "dropdown":
                entries[c["id"]] = c["answer"]
                if c["answer"] not in c["options"]: err(tid, "변형 보기에 정답 없음 seed=%d" % seed)
                for o in c["options"]:
                    if o != c["answer"] and o not in c["wrong_msgs"]: err(tid, "변형 오답 해설 없음 seed=%d" % seed)
            elif c["kind"] == "citation":
                entries[c["id"]] = "ASC " + c["accept"][0]
            else:
                rows = answer_rows(c)
                dr_ = sum(r["d"] for r in rows); cr_ = sum(r["c"] for r in rows)
                if dr_ != cr_: err(tid, "분개 차대 불일치 %s seed=%d (%s != %s)" % (c["id"], seed, dr_, cr_))
                if any(l["v"] <= 0 for l in c["lines"]): err(tid, "분개 금액 0 이하 %s seed=%d" % (c["id"], seed))
                entries[c["id"]] = rows
        res = grade(v, entries)
        bad = {k: x for k, x in res.items() if x[0] != 1.0}
        if bad: err(tid, "변형 만점 채점 실패 seed=%d %s" % (seed, bad)); break
        for c in v["cells"]:
            if c["kind"] == "number" and c["fmt"] == "$" and not float(c["answer"]).is_integer(): err(tid, "정수 칸에 소수 정답")
        nv += 1
    nvar[tid] = len(seen)
print("변형 %d개 생성·손계산 대조·만점 채점 완료" % nv)
few = {k: v for k, v in nvar.items() if v < 20 and RAW[k]["vary"]}
if few: err("전체", "변형 종류가 적음 %s" % few)
print("TBS별 서로 다른 변형 수(200시드 중):", {k.replace("FAR-", ""): v for k, v in nvar.items()})

# ------------------------------------------------------------------ (5) ECF, 분개 부분점수, 번호 정규화
ecf_tested = 0
for t in items:
    ans = {c["id"]: c["answer"] for c in t["cells"] if c["kind"] == "number"}
    base = build_ns(t["params"], t["derived"])
    for c in t["cells"]:
        if c["kind"] == "number" and c["deps"] and c["ecf"]:
            d0 = c["deps"][0]
            entries = {k: str(v) for k, v in ans.items() if k in c["deps"]}
            entries[d0] = str(ans[d0] + max(1000, abs(ans[d0]) * 0.1)) if DEC[next(x for x in t["cells"] if x["id"] == d0)["fmt"]] == 0 else str(round(ans[d0] * 1.1 + 0.1, 2))
            loc = dict(base)
            for k in ans: loc[k] = ans[k]
            for k, v in entries.items(): loc[k] = float(v)
            alt = eval(c["expr"], {"__builtins__": {}}, loc)
            alt_r = rd(alt, DEC[c["fmt"]])
            entries[c["id"]] = str(alt_r)
            r = grade(t, entries)[c["id"]]
            if abs(alt_r - c["answer"]) > c["tol"]:
                if r[1] != "ecf" or r[0] != 0.5: err(t["id"], "ECF 채점 실패 %s %s" % (c["id"], r))
                else: ecf_tested += 1
            # 정답이 아닌데 ECF 도 아닌 값은 0점
            entries[c["id"]] = str(c["answer"] + 12345)
            if grade(t, entries)[c["id"]][0] != 0.0: err(t["id"], "엉뚱한 값에 점수 부여 " + c["id"])
print("ECF(숫자 칸) 시험 %d건" % ecf_tested)

je_tests = 0
for t in items:
    for c in t["cells"]:
        if c["kind"] != "je": continue
        rows = answer_rows(c)
        g = grade_je(c, rows); je_tests += 1
        if not g["perfect"]: err(t["id"], "분개 만점 실패 " + c["id"])
        # 전부 반대 변
        flip = [{"a": r["a"], "d": r["c"], "c": r["d"]} for r in rows]
        g = grade_je(c, flip)
        if g["score"] != 0 or any(l["status"] != "flip" for l in g["lines"]): err(t["id"], "반대변 채점 " + c["id"])
        # 첫 줄 금액 틀림 -> 0.5점 줄
        wrong = [dict(r) for r in rows]
        k = "d" if wrong[0]["d"] else "c"
        wrong[0][k] += 777
        g = grade_je(c, wrong)
        exp_score = (len(rows) - 1 + 0.5) / len(rows)
        if abs(g["score"] - exp_score) > 1e-9: err(t["id"], "금액 오류 부분점수 %s %.3f != %.3f" % (c["id"], g["score"], exp_score))
        # 한 줄 누락
        miss = rows[1:]
        g = grade_je(c, miss)
        if abs(g["score"] - (len(rows) - 1) / len(rows)) > 1e-9 or len(g["missing"]) != 1: err(t["id"], "누락 줄 채점 " + c["id"])
        # 같은 계정 두 줄 합산 허용(첫 줄을 반쪽 두 줄로)
        split = [dict(rows[0], **{("d" if rows[0]["d"] else "c"): (rows[0]["d"] or rows[0]["c"]) - 100}), dict(rows[0], **{("d" if rows[0]["d"] else "c"): 100})] + rows[1:]
        g = grade_je(c, split)
        if not g["perfect"]: err(t["id"], "동일 계정 합산 " + c["id"])
        # 불필요한 줄 -0.5
        ext = rows + [{"a": next(a for a in c["accounts"] if a not in [l["a"] for l in c["lines"]]), "d": 50, "c": 0}]
        g = grade_je(c, ext)
        if abs(g["score"] - max(0, len(rows) - 0.5) / len(rows)) > 1e-9: err(t["id"], "불필요 줄 감점 " + c["id"])
        # 대체 계정
        for i_, l in enumerate(c["lines"]):
            for al in l["alt"]:
                alt_rows = [dict(r) for r in rows]
                alt_rows[i_]["a"] = al
                if not grade_je(c, alt_rows)["perfect"]: err(t["id"], "대체 계정 인정 실패 %s %s" % (c["id"], al))
        # 흔한 실수 규칙이 실제로 걸리는지(sub/amt)
        for m_ in c["mist"]:
            if m_["k"] == "sub":
                lines = [l for l in c["lines"] if l["a"] == m_["a"]]
                if not lines: err(t["id"], "sub 규칙 대상 줄 없음 %s %s" % (c["id"], m_["a"])); continue
                if any(l["a"] == m_["b"] and l["s"] == lines[0]["s"] for l in c["lines"]):
                    continue                     # 같은 변에 그 계정이 이미 있으면 입력이 합산되어 sub 경로가 아니다
                tst = [dict(r) for r in rows]
                for r in tst:
                    if r["a"] == m_["a"]: r["a"] = m_["b"]
                g = grade_je(c, tst)
                if not any(u.get("msg") == m_["msg"] for u in g["lines"]): err(t["id"], "sub 진단이 걸리지 않음 %s %s->%s" % (c["id"], m_["a"], m_["b"]))
            if m_["k"] == "amt":
                lines = [l for l in c["lines"] if l["a"] == m_["a"]]
                if not lines: err(t["id"], "amt 규칙 대상 줄 없음 %s %s" % (c["id"], m_["a"])); continue
                if abs(m_["v"] - lines[0]["v"]) <= max(c.get("tol", 1), lines[0]["v"] * 0.0001): err(t["id"], "amt 오답값이 정답과 같음 %s %s" % (c["id"], m_["a"])); continue
                tst = [dict(r) for r in rows]
                for r in tst:
                    if r["a"] == m_["a"]:
                        if r["d"]: r["d"] = m_["v"]
                        else: r["c"] = m_["v"]
                g = grade_je(c, tst)
                if not any(u.get("msg") == m_["msg"] for u in g["lines"]): err(t["id"], "amt 진단이 걸리지 않음 %s %s" % (c["id"], m_["a"]))
            if m_["k"] == "swap":
                if not any(l["a"] == m_["a"] for l in c["lines"]): err(t["id"], "swap 규칙 대상 없음 %s" % c["id"])
            if m_["k"] == "miss":
                if not any(l["a"] == m_["a"] for l in c["lines"]): err(t["id"], "miss 규칙 대상 없음 %s" % c["id"])
# 분개 ECF: 앞 숫자 칸을 틀리게 넣었을 때 뒤 분개 줄이 ECF 로 인정되는지(II-005 c3)
t = next(x for x in items if x["id"] == "FAR-II-T-005")
c1 = next(c for c in t["cells"] if c["id"] == "c1")
c3 = next(c for c in t["cells"] if c["id"] == "c3")
wrong_c1 = c1["answer"] + 5000
i_alt = rnd(wrong_c1 * (t["params"]["r"] / 200))
rows = [{"a": "intexp", "d": i_alt}, {"a": "cash", "c": rnd(t["params"]["F"] * t["params"]["s"] / 200)}, {"a": "disc", "c": i_alt - rnd(t["params"]["F"] * t["params"]["s"] / 200)}]
res = grade(t, {"c1": str(wrong_c1), "c3": rows})
if not (res["c1"][0] == 0 and abs(res["c3"][0] - (JE_ECF + 1 + JE_ECF) / 3) < 1e-9): err("ECF", "분개 ECF %s" % (res,))
else: je_tests += 1
print("분개 채점 시험 %d건(줄 단위 부분점수, 반대변, 합산, 대체 계정, 진단 규칙, ECF)" % je_tests)

for s_, exp in [("FASB ASC Topic 260", "260"), ("ASC 205-20", "205-20"), ("asc 205-20-45-1B", "205-20-45-1b"), ("GASB Statement No. 34", "34"), ("GASB 87", "87"),
                ("§ 842-20", "842-20"), ("ASC Topic 842 – 20", "842-20"), ("Statement 68", "68")]:
    if norm_std(s_) != exp: err("norm_std", "%r -> %r (기대 %r)" % (s_, norm_std(s_), exp))
c = next(c for c in next(x for x in items if x["id"] == "FAR-I-T-007")["cells"] if c["id"] == "c2")
if not (grade_std(c, "ASC 205-20") == 1 and grade_std(c, "205-20-45-1B") == 1 and grade_std(c, "205") == 0.5 and grade_std(c, "205-40") == 0 and grade_std(c, "ASC 260") == 0): err("grade_std", "205-20 채점")
c = next(c for c in next(x for x in items if x["id"] == "FAR-I-T-008")["cells"] if c["id"] == "c1")
if not (grade_std(c, "GASB 34") == 1 and grade_std(c, "34") == 1 and grade_std(c, "GASB Statement No. 34") == 1 and grade_std(c, "54") == 0): err("grade_std", "GASB 채점")
if not (parse_num("$1,234") == 1234 and parse_num("(5,000)") == -5000 and parse_num("−5000") == -5000 and parse_num("1.5") == 1.5 and parse_num("x") != parse_num("x")): err("parse_num", "입력 해석")
if not (rd(2.675, 2) == 2.68 and rd(-2.5) == -2 and rd(0.5) == 1 and rd(1.005, 2) == 1.01): err("rd", "반올림 규칙")

for t in items:
    if t["status"] not in ("draft", "verified"): err(t["id"], "status")
cells = sum(len(t["cells"]) for t in items)
print("TBS %d, 칸 %d (종류 %s), Area %s, 형식 %s" % (len(items), cells, dict(kinds_all), dict(areas), dict(fmts)))
if errs:
    for e in errs[:80]: print("ERR", e)
    print("오류 %d건" % len(errs)); sys.exit(1)
print("전부 통과")
