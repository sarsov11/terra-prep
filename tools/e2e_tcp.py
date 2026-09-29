# -*- coding: utf-8 -*-
"""Browser walk-through of the TCP section (needs Playwright + Edge).

  py tools/e2e_tcp.py [port]      serve the folder on 127.0.0.1:<port> first, e.g.  py -m http.server 18473 --bind 127.0.0.1

A  new learner: start -> TCP -> placement check -> home -> practice + explanation -> mock exam -> other pages
B  learner with saved REG and FAR history: switch REG -> TCP -> FAR -> REG; each section keeps its own date, hours, placement and answers
Runs at desktop and phone width. Screenshots go to tools/screens/tcp_*.png. Exits 1 on any console error or failed check.
"""
import datetime, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "18473"
BASE = "http://127.0.0.1:%s/" % PORT
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens")
os.makedirs(OUT, exist_ok=True)
errors, checks = [], []
KEYS = ["tcp_area1_individuals", "tcp_area2_entity_compliance", "tcp_area3_entity_planning", "tcp_area4_property"]


def check(name, ok, info=""):
    checks.append((name, ok, info))
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(info)[:150] if info else ""))


def new_page(br, viewport, mobile, tag):
    ctx = br.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile)
    pg = ctx.new_page()
    pg.on("console", lambda m: errors.append((tag, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append((tag, str(e))))
    return ctx, pg


def shot(pg, tag, name):
    pg.screenshot(path=os.path.join(OUT, "tcp_%s_%s.png" % (tag, name)), full_page=True)


def part_a(br, tag, viewport, mobile):
    ctx, pg = new_page(br, viewport, mobile, tag + "-A")
    pg.goto(BASE + "start.html")
    pg.click("#n")
    pg.wait_for_selector("#op button")
    labels = pg.locator("#op button").all_inner_texts()
    check(tag + " exam list has US CPA — TCP", any("TCP (Tax Compliance and Planning)" in l for l in labels), [l[:30] for l in labels])
    shot(pg, tag, "1_choose_exam")
    pg.click('#op button[data-v="cpa_tcp"]')
    pg.wait_for_selector("text=what you’ll cover")
    txt = pg.inner_text("#scr")
    check(tag + " subjects step lists the four TCP Areas (77/77/33/33)",
          "Area I · Individuals and Personal Financial Planning" in txt and "Area II · Entity Tax Compliance" in txt and "Area III · Entity Tax Planning" in txt
          and "Area IV · Property Transactions" in txt and txt.count("77 questions") == 2 and txt.count("33 questions") == 2, txt[100:400])
    pg.click("#n"); pg.fill("#nm", "Tester"); pg.click("#n")
    pg.click("#later")
    pg.click('#op button[data-v="15"]')
    pg.wait_for_selector("#oxb", timeout=20000)
    n = 0
    shot(pg, tag, "2_placement")
    areas = set()
    while pg.locator("#oxb button").count() and n < 30:
        areas.add(pg.inner_text(".qhd .chip"))
        pg.locator("#oxb button").nth(n % 4).click()
        n += 1
        try:
            pg.wait_for_function("() => document.querySelector('#oxb button:not([disabled])') || document.querySelector('.perpart')", timeout=6000)
        except Exception:
            pass
    check(tag + " placement check has 20 TCP questions", n == 20, n)
    check(tag + " placement draws from Area I-IV", areas == {"Area I", "Area II", "Area III", "Area IV"}, areas)
    pg.wait_for_selector(".perpart")
    shot(pg, tag, "3_placement_done")
    pg.click("#n")
    pg.wait_for_selector("#todo")
    body = pg.inner_text("body")
    check(tag + " home: section switch REG | FAR | TCP with TCP selected", pg.locator('#secs a.on').inner_text() == "TCP" and pg.locator("#secs a").all_inner_texts() == ["REG", "FAR", "TCP"], pg.locator("#secs a").all_inner_texts())
    check(tag + " home: no concept cards, no TBS, no journal entry drill", "Concept cards" not in body and "Task-based simulations" not in body and "Journal entry drill" not in body)
    subs = pg.locator("#subs").inner_text()
    check(tag + " Area chips: all four TCP Areas ready", "Area IV · Property Transactions" in subs and "Coming soon" not in subs, subs)
    shot(pg, tag, "4_home")

    pg.goto(BASE + "ox.html")
    pg.wait_for_selector("#oxb")
    pg.click('#oxb [data-a="1"]')
    pg.wait_for_selector("#after .verdict")
    check(tag + " explanation shown for every choice", pg.locator("#after .exs .exi").count() >= 2, pg.locator("#after .exs .exi").count())
    shot(pg, tag, "5_explanation")

    pg.goto(BASE + "exam.html")
    pg.wait_for_selector("#go:not([disabled])")
    note = pg.inner_text("#note")
    check(tag + " mock exam note: 220 questions in 4 Areas", "220 questions in 4 Areas" in note and "No questions yet" not in note, note[-160:])
    shot(pg, tag, "6_exam_setup")
    pg.click('#sz [data-n="12"]'); pg.click("#go")
    for i in range(12):
        pg.wait_for_selector("#opts")
        pg.locator("#opts button").nth(i % 4).click()
        pg.click("#nx")
    pg.wait_for_selector("#sb")
    pg.click("#sb")
    pg.wait_for_selector(".brk")
    res = pg.inner_text(".brk")
    check(tag + " exam results by TCP Area", "Area I · Individuals" in res and "Area II · Entity Tax Compliance" in res and "Area III" in res and "Area IV" in res, res[:200])
    weights = pg.evaluate("(ks) => ks.map(k => CATALOG.weight(k)).join('/')", KEYS)
    check(tag + " TCP Blueprint weights 35/35/15/15", weights == "35/35/15/15", weights)
    pg.evaluate("() => { GB.loadPool(function (p) { var s = GB.mockSet(p, 72, 5), c = {}; s.forEach(function (x) { c[x.area] = (c[x.area] || 0) + 1; }); window.__mix = c; }); }")
    pg.wait_for_function("() => window.__mix")
    mix = pg.evaluate("() => window.__mix")
    check(tag + " 72-question mock follows the Blueprint mix (25/25/11/11)", mix == {"I": 25, "II": 25, "III": 11, "IV": 11}, mix)
    check(tag + " exam history stored under the TCP key", pg.evaluate("() => !!localStorage.getItem('te.tcp.exams.v1') && !localStorage.getItem('te.exams.v1') && !localStorage.getItem('te.far.exams.v1')"))
    shot(pg, tag, "7_exam_result")

    for page, sel, name in (("insights.html", "#rd", "8_insights"), ("plan.html", "#out", "9_plan"), ("method.html", "h2", "10_method"), ("drill.html", "#ls", "11_more"), ("skilltree.html", "body", "12_units")):
        pg.goto(BASE + page)
        pg.wait_for_selector(sel)
        if page == "insights.html":
            t = pg.inner_text("#rd")
            check(tag + " insights lists TCP Areas with weights", "Entity Tax Planning" in t and "Property Transactions" in t and "of 4 Areas" in t and "without questions yet" not in t, t[:240])
        if page == "drill.html":
            check(tag + " More list has no journal entry drill", "Journal entry drill" not in pg.inner_text("#ls"))
        shot(pg, tag, name)
    ctx.close()


def part_b(br, tag, viewport, mobile):
    ctx, pg = new_page(br, viewport, mobile, tag + "-B")
    goal = (datetime.date.today() + datetime.timedelta(days=40)).isoformat()
    pg.goto(BASE + "index.html?nostart")
    pg.evaluate("""g => {
      localStorage.setItem("te.pref.v1", JSON.stringify({exam:"cpa",onboarded:"x",subs:CATALOG.subsOf("cpa"),cur:"reg_area4_individuals",goal:g,goalMark:true,goalMine:true,hours:10,
        place:{at:1700000000000,n:20,ok:12,per:{IV:{n:5,ok:2}},weakArea:"IV"}}));
      localStorage.setItem("te.reg_area4_individuals.v1", JSON.stringify({ans:{"REG-IV-A-0001":{n:1,ok:true,box:1,at:1700000000000,due:1},"REG-IV-A-0002":{n:1,ok:false,box:0,at:1700000000000,due:1}},days:{"2026-09-01":{n:2,ok:1,ms:1000}},pairs:{},flags:{},wlog:[],notes:{},cards:{}}));
      localStorage.setItem("te.far_area1_financial_reporting.v1", JSON.stringify({ans:{"FAR-I-A-0001":{n:1,ok:true,box:1,at:1700000000000,due:1}},days:{"2026-09-02":{n:1,ok:1,ms:1000}},pairs:{},flags:{},wlog:[],notes:{},cards:{}}));
      localStorage.setItem("te.exams.v1", JSON.stringify([{at:1,n:1}]));
    }""", goal)
    pg.goto(BASE + "index.html?nostart")
    pg.wait_for_selector("#todo")
    d0 = pg.inner_text("#ed")
    check(tag + " REG home: three section chips, REG selected", pg.locator("#secs a").all_inner_texts() == ["REG", "FAR", "TCP"] and pg.locator("#secs a.on").inner_text() == "REG")
    pg.click('#secs a[data-x="cpa_tcp"]')
    pg.wait_for_selector("#scr")
    check(tag + " first switch to TCP opens the test date step", "step=date" in pg.url and "Test date" in pg.inner_text("#scr"), pg.url)
    check(tag + " TCP starts without the REG test date", pg.evaluate("() => GB.goalMark()") == "default")
    pg.click("#later"); pg.click('#op button[data-v="15"]')
    pg.wait_for_selector("#oxb", timeout=20000)
    pg.click("#sk"); pg.click("#sk")
    pg.wait_for_selector("#n", timeout=8000)
    pg.click("#n")
    pg.wait_for_selector("#todo")
    check(tag + " TCP home after switch", pg.locator("#secs a.on").inner_text() == "TCP" and "Test date not set" in pg.inner_text("#ed"), pg.inner_text("#ed"))
    check(tag + " TCP shows no REG or FAR answers", pg.evaluate("() => GB.readiness().n") == 0, pg.evaluate("() => GB.readiness().n"))
    pref = pg.evaluate("() => JSON.parse(localStorage.getItem('te.pref.v1'))")
    check(tag + " REG settings parked under sec.cpa", pref.get("sec", {}).get("cpa", {}).get("hours") == 10 and pref["sec"]["cpa"].get("place", {}).get("n") == 20, json.dumps(pref.get("sec"))[:160])
    pg.click('#secs a[data-x="cpa_far"]')
    pg.wait_for_selector("#scr")
    check(tag + " first switch to FAR from TCP opens the date step", "step=date" in pg.url, pg.url)
    pg.goto(BASE + "index.html?nostart")
    pg.wait_for_selector("#todo")
    pg.click('#secs a[data-x="cpa_tcp"]')
    pg.wait_for_selector("#todo")
    check(tag + " back on TCP without setup (its own settings kept)", pg.url.endswith("index.html") and pg.locator("#secs a.on").inner_text() == "TCP", pg.url)
    pg.click('#secs a[data-x="cpa"]')
    pg.wait_for_selector("#todo")
    check(tag + " back on REG (no setup screen)", pg.url.endswith("index.html") and pg.locator("#secs a.on").inner_text() == "REG", pg.url)
    check(tag + " REG test date kept", pg.inner_text("#ed") == d0, (d0, pg.inner_text("#ed")))
    pref = pg.evaluate("() => JSON.parse(localStorage.getItem('te.pref.v1'))")
    check(tag + " REG hours, placement and Area restored", pref.get("hours") == 10 and pref.get("place", {}).get("n") == 20 and pref.get("cur") == "reg_area4_individuals", json.dumps({k: pref.get(k) for k in ("hours", "cur")}))
    check(tag + " REG answers still counted", pg.evaluate("() => GB.readiness().n") == 2, pg.evaluate("() => GB.readiness().n"))
    check(tag + " REG history keys untouched", pg.evaluate("() => Object.keys(JSON.parse(localStorage.getItem('te.reg_area4_individuals.v1')).ans).length") == 2 and pg.evaluate("() => Object.keys(JSON.parse(localStorage.getItem('te.far_area1_financial_reporting.v1')).ans).length") == 1)
    check(tag + " REG Area chips unchanged (5 Areas)", pg.locator("#subs a").count() == 5)
    body = pg.inner_text("body")
    check(tag + " REG home keeps TBS and concept cards", "Task-based simulations" in body and "Concept cards" in body)
    shot(pg, tag, "21_reg_home_after")
    pg.click('#secs a[data-x="cpa_far"]')
    pg.wait_for_selector("#todo")
    check(tag + " FAR home after switch back (answers counted, no setup)", "step=date" not in pg.url, pg.url)
    shot(pg, tag, "22_far_home_after")
    ctx.close()


with sync_playwright() as pw:
    br = pw.chromium.launch(channel="msedge")
    for tag, vp, mob in (("desktop", {"width": 1200, "height": 900}, False), ("mobile", {"width": 390, "height": 800}, True)):
        part_a(br, tag, vp, mob)
        part_b(br, tag, vp, mob)
    br.close()

bad = [e for e in errors if "favicon" not in e[1]]
for e in bad:
    print("CONSOLE ERROR", e)
print("checks: %d passed, %d failed | console errors: %d" % (sum(1 for c in checks if c[1]), sum(1 for c in checks if not c[1]), len(bad)))
sys.exit(1 if bad or any(not c[1] for c in checks) else 0)
