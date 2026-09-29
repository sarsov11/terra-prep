"""TBS 검산: (1) 손계산 정답표와 대조 (2) 형식 규칙 (3) 변형 생성 200회 (4) ECF·인용 채점 시험.
사용: py tbs_계산검산.py   (종료코드 0 = 전부 통과)"""
import json, os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
from tbs_lib import *
import tbs_items_1, tbs_items_3, tbs_items_4, tbs_items_5

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "tbs_reg.json"), encoding="utf-8"))
items = data["items"]
RAW = {t["id"]: t for m in (tbs_items_1, tbs_items_3, tbs_items_4, tbs_items_5) for t in m.ITEMS}
errs = []
PH = re.compile(r"\{[a-z_0-9]+(:,)?\}")
def err(i, m): errs.append((i, m))

# ---- (1) 손계산 정답표: 작성 식을 쓰지 않고 손으로 푼 값 ----
HAND = {
 "REG-I-T-001": {"c1": 4, "c2": 2520, "c3": 280, "c4": 2800, "c5": 3150, "c6": 3640},   # 14,000: 4.5%x4, 0.5%x4, 4.5%x5, +0.5%x7
 "REG-III-T-007": {"c1": 42000, "c2": 30000, "c3": 0, "c4": -5000, "c5": 22700, "c6": 37300, "c7": 7000},
 "REG-III-T-008": {"c1": 600000, "c2": 250000, "c3": 80000, "c4": 80000, "c5": 170000, "c6": 350000},
 "REG-IV-T-012": {"c1": 79650, "c2": 74650, "c3": 58550, "c4": 7593, "c5": 1500, "c6": 6093, "c7": 1000, "c8": 3007},
 "REG-IV-T-013": {"c1": 107000, "c2": 15119, "c3": 7559, "c4": 93441, "c5": 77341, "c6": 15468, "c7": 61873, "c8": 8324},
 "REG-IV-T-014": {"c1": 7500, "c2": 40400, "c3": 35000, "c4": 10500, "c5": 93400, "c6": 93400, "c7": 206600},
 "REG-IV-T-015": {"c1": -4000, "c2": -4000, "c3": 3000, "c4": 5000, "c5": 1000, "c6": 4000, "c7": 19400, "c8": 3090},
 "REG-V-T-019": {"c1": 64000, "c2": 56000, "c3": 876000, "c4": 65000, "c5": 300000, "c6": 511000, "c7": 107310},   # 10% 한도 기준 = NOL 이월공제 후 소득(Form 1120 지침 line 19)
 "REG-V-T-020": {"c1": 100000, "c2": 112500, "c3": 72500, "c4": 72500, "c5": 12500, "c6": 0, "c7": 20000},
 "REG-V-T-021": {"c1": 74000, "c2": 16000, "c3": 12000, "c4": 12000, "c5": 10000, "c6": 58000},
}
for tid, exp in HAND.items():
    t = next(x for x in items if x["id"] == tid)
    for c in t["cells"]:
        if c["kind"] == "number":
            if c["id"] not in exp:
                err(tid, "손계산 표에 칸 없음 " + c["id"])
            elif abs(c["answer"] - exp[c["id"]]) > 1:
                err(tid, "손계산 불일치 %s: 식=%s 손=%s" % (c["id"], c["answer"], exp[c["id"]]))

def cell(tid, cid):
    return next(c for t in items if t["id"] == tid for c in t["cells"] if c["id"] == cid)["answer"]
if abs(cell("REG-III-T-008", "c6") - (350000 - 40000 + 80000 - 100000 + 60000)) > 1: err("III-008", "기준가액 교차식 불일치")
if cell("REG-IV-T-015", "c4") != cell("REG-IV-T-015", "c5") + cell("REG-IV-T-015", "c6"): err("IV-015", "이월 합계")
if cell("REG-V-T-021", "c6") != 80000 - 12000 - 10000: err("V-021", "정지손실")

# ---- (2) 형식 규칙 ----
areas = collections.Counter(t["area"] for t in items)
fmts = collections.Counter(t["format"] for t in items)
if dict(areas) != {"I": 3, "II": 3, "III": 5, "IV": 7, "V": 6}: err("전체", "Area 분포 %s" % dict(areas))
if dict(fmts) != {"numeric_table": 10, "document_review": 6, "research": 4, "dropdown_judgment": 4}: err("전체", "형식 분포 %s" % dict(fmts))
if len(items) != 24 or len({t["id"] for t in items}) != 24: err("전체", "개수/ID 중복")
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
    for c in t["cells"]:
        if not c.get("why"): err(i, c["id"] + " 해설 없음")
        if not c.get("hints"): err(i, c["id"] + " 힌트 없음")
        if c["kind"] == "number":
            if not c["steps"]: err(i, c["id"] + " 풀이 단계 없음")
            if len(c["hints"]) < 2: err(i, c["id"] + " 힌트 2단계 미만")
            if c["tol"] not in (0, 1): err(i, c["id"] + " tol")
            for tr in c["traps"]:
                if tr["value"] == c["answer"]: err(i, c["id"] + " 오답 진단값이 정답과 같음 " + tr["expr"])
        elif c["kind"] == "dropdown":
            if c["answer"] not in c["options"] or len(set(c["options"])) != len(c["options"]): err(i, c["id"] + " 보기")
            for o in c["options"]:
                if o != c["answer"] and o not in c["wrong_msgs"]:
                    err(i, c["id"] + " 오답 해설 없음: " + o[:30])
        else:
            if not c["accept"] or not c["link"].startswith("https://www.law.cornell.edu/"): err(i, c["id"] + " 인용 정답/링크")
            for a in c["accept"] + c["partial"]:
                if norm_cite(a) != a.lower(): err(i, c["id"] + " accept 가 정규형 아님 " + a)
    kinds = {c["kind"] for c in t["cells"]}
    fm = t["format"]
    if fm == "numeric_table" and "number" not in kinds: err(i, "숫자 칸 없음")
    if fm == "research" and kinds != {"citation"}: err(i, "인용 칸만이어야 함")
    if fm in ("document_review", "dropdown_judgment") and kinds != {"dropdown"}: err(i, "드롭다운 칸만이어야 함")

pos = collections.Counter()
for t in items:
    for c in t["cells"]:
        if c["kind"] == "dropdown" and len(c["options"]) == 3:
            pos[c["options"].index(c["answer"])] += 1
print("드롭다운(3지) 정답 위치:", dict(pos))
tot = sum(pos.values())
if tot and max(pos.values()) / tot > 0.5: err("전체", "정답 위치 편중 %s" % dict(pos))

sheet = json.load(open(os.path.join(HERE, "tbs_문제지_검산용.json"), encoding="utf-8"))
raw_s = json.dumps(sheet, ensure_ascii=False)
for bad in ('"answer"', '"why"', '"steps"', '"expr"', '"accept"', '"hints"', '"traps"'):
    if bad in raw_s: err("문제지", "정답 관련 키 노출 " + bad)
if len(sheet["items"]) != 24: err("문제지", "개수")

# ---- (3) 변형 생성 ----
nv = 0
for tid, raw in RAW.items():
    for seed in range(200):
        try:
            v, p = variant(raw, seed)
        except Exception as e:
            err(tid, "변형 실패 seed=%d %s" % (seed, e)); break
        body = json.dumps({k: x for k, x in v.items() if k != "template"}, ensure_ascii=False)
        if PH.search(body): err(tid, "변형 미치환 seed=%d" % seed); break
        full = {c["id"]: c["answer"] for c in v["cells"] if c["kind"] == "number"}
        res = grade(v, full)
        if any(x != 1.0 for x in res.values() if True) and any(x != 1.0 for k, x in res.items() if k in full): err(tid, "변형 만점 채점 실패 seed=%d %s" % (seed, res)); break
        nv += 1
print("변형 %d개 생성·채점 완료" % nv)

# ---- (4) ECF 와 인용 채점 시험 ----
t = next(x for x in items if x["id"] == "REG-IV-T-012")
good = {c["id"]: c["answer"] for c in t["cells"]}
bad = dict(good)
bad["c2"] = good["c2"] + 1000
alt_ti = bad["c2"] - t["params"]["std"]
bad["c3"] = alt_ti
bad["c4"] = round(tax_s(alt_ti))
r = grade(t, {k: str(v) for k, v in bad.items()})
if not (r["c2"] == 0 and r["c3"] == 0.5 and r["c4"] == 0.5): err("ECF", "IV-012 채점 %s" % r)
for s, exp in [("IRC §6694(a)", "6694(a)"), ("Sec. 6694 (a)", "6694(a)"), ("26 U.S.C. 6694(a)", "6694(a)"), ("Internal Revenue Code section 6694(a)", "6694(a)"),
               ("31 CFR §10.29", "10.29"), ("Circular 230 § 10.29", "10.29"), ("IRC 1367(a)(2).", "1367(a)(2)"), ("§ 280A(d)(1)", "280a(d)(1)")]:
    if norm_cite(s) != exp: err("norm_cite", "%r -> %r (기대 %r)" % (s, norm_cite(s), exp))
c = next(c for c in next(x for x in items if x["id"] == "REG-I-T-003")["cells"] if c["id"] == "c3")
if not (grade_cite(c, "IRC 6694(a)") == 1 and grade_cite(c, "IRC 6694") == 0.5 and grade_cite(c, "IRC 6662") == 0): err("grade_cite", "6694 채점")

for t in items:
    if t["status"] != "verified" or not t["verify"].get("commit"): err(t["id"], "status/verify 미반영")
cells = sum(len(t["cells"]) for t in items)
nn = sum(1 for t in items for c in t["cells"] if c["kind"] == "number")
print("TBS %d, 칸 %d (숫자 %d), Area %s, 형식 %s" % (len(items), cells, nn, dict(areas), dict(fmts)))
if errs:
    for e in errs[:80]: print("ERR", e)
    print("오류 %d건" % len(errs)); sys.exit(1)
print("전부 통과")
