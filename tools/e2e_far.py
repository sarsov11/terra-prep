# -*- coding: utf-8 -*-
"""Browser walk-through of the FAR section (needs Playwright + Edge).

  py tools/e2e_far.py [port]      serve the folder on 127.0.0.1:<port> first, e.g.  py -m http.server 18472 --bind 127.0.0.1

A  new learner: start -> FAR -> placement check -> home -> practice + explanation -> mock exam -> journal entry drill
B  learner with saved REG history: switch to FAR from Home, then back to REG; REG date, hours, placement and answers stay
Runs at desktop and phone width. Screenshots go to tools/screens/far_*.png. Exits 1 on any console error or failed check.
"""
import datetime, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "18472"
BASE = "http://127.0.0.1:%s/" % PORT
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens")
os.makedirs(OUT, exist_ok=True)
errors, checks = [], []


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
    pg.screenshot(path=os.path.join(OUT, "far_%s_%s.png" % (tag, name)), full_page=True)


def part_a(br, tag, viewport, mobile):
    ctx, pg = new_page(br, viewport, mobile, tag + "-A")
    pg.goto(BASE + "start.html")
    pg.click("#n")                                             # intro
    pg.wait_for_selector("#op button")
    labels = pg.locator("#op button").all_inner_texts()
    check(tag + " exam list has REG, FAR, TCP, AUD, CFA", len(labels) == 5 and "FAR" in labels[1] and "TCP" in labels[2], labels[1][:60])
    shot(pg, tag, "1_choose_exam")
    pg.click('#op button[data-v="cpa_far"]')
    pg.wait_for_selector("text=what you’ll cover")
    txt = pg.inner_text("#scr")
    check(tag + " subjects step lists the three FAR Areas with 150/180/150 questions", "Area I · Financial Reporting" in txt and "Area II · Select Balance Sheet Accounts" in txt and "Area III · Select Transactions" in txt and txt.count("150 questions") == 2 and txt.count("180 questions") == 1, txt[100:300])
    pg.click("#n"); pg.fill("#nm", "Tester"); pg.click("#n")   # subs -> name
    pg.click("#later")                                         # date
    pg.click('#op button[data-v="15"]')                        # minutes
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
    check(tag + " placement check has 20 FAR questions", n == 20, n)
    check(tag + " placement draws from Area I, II and III", areas == {"Area I", "Area II", "Area III"}, areas)
    pg.wait_for_selector(".perpart")
    shot(pg, tag, "3_placement_done")
    pg.click("#n")
    pg.wait_for_selector("#todo")
    body = pg.inner_text("body")
    check(tag + " home shows section switch with FAR selected", pg.locator('#secs a.on').inner_text() == "FAR" and pg.locator("#secs a").count() == 4)
    alt = pg.locator("#alt .row b").all_inner_texts()
    check(tag + " journal entry drill is the first extra row", alt and alt[0] == "Journal entry drill", alt)
    check(tag + " no REG-only rows on FAR home", "Task-based simulations" not in body and "Concept cards" not in body)
    subs = pg.locator("#subs").inner_text()
    check(tag + " Area chips: all three FAR Areas ready", "Area I · Financial Reporting" in subs and "Area III · Select Transactions" in subs and "Coming soon" not in subs, subs)
    shot(pg, tag, "4_home")

    # practice + explanation
    pg.goto(BASE + "ox.html")
    pg.wait_for_selector("#oxb")
    pg.click('#oxb [data-a="1"]')
    pg.wait_for_selector("#after .verdict")
    check(tag + " explanation shown for every choice", pg.locator("#after .exs .exi").count() >= 2, pg.locator("#after .exs .exi").count())
    shot(pg, tag, "5_explanation")

    # mock exam: 12 questions
    pg.goto(BASE + "exam.html")
    pg.wait_for_selector("#go:not([disabled])")
    note = pg.inner_text("#note")
    check(tag + " mock exam note: 480 questions in 3 Areas, nothing missing", "480 questions in 3 Areas" in note and "No questions yet" not in note, note[-160:])
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
    check(tag + " exam results by FAR Area", "Area I · Financial Reporting" in res and "Area II · Select Balance Sheet Accounts" in res and "Area III · Select Transactions" in res, res[:160])
    weights = pg.evaluate("() => ['far_area1_financial_reporting', 'far_area2_balance_sheet', 'far_area3_transactions'].map(k => CATALOG.weight(k)).join('/')")
    check(tag + " FAR Blueprint weights 35/35/30", weights == "35/35/30", weights)
    share = pg.evaluate("() => { var a = {}; GB.loadPool(function (p) { var s = GB.mockSet(p, 72, 5), c = {}; s.forEach(function (x) { c[x.area] = (c[x.area] || 0) + 1; }); window.__mix = c; }); return 1; }")
    pg.wait_for_function("() => window.__mix")
    mix = pg.evaluate("() => window.__mix")
    check(tag + " 72-question mock follows the Blueprint mix (25/25/22)", mix == {"I": 25, "II": 25, "III": 22} or mix == {"I": 26, "II": 25, "III": 21} or mix == {"I": 25, "II": 26, "III": 21}, mix)
    check(tag + " exam history stored under the FAR key", pg.evaluate("() => !!localStorage.getItem('te.far.exams.v1') && !localStorage.getItem('te.exams.v1')"))
    shot(pg, tag, "7_exam_result")

    for page, sel, name in (("insights.html", "#rd", "8_insights"), ("plan.html", "#out", "9_plan"), ("method.html", "h2", "10_method"), ("drill.html", "#ls", "11_more")):
        pg.goto(BASE + page)
        pg.wait_for_selector(sel)
        if page == "insights.html":
            t = pg.inner_text("#rd")
            check(tag + " insights lists FAR Areas with weights", "Select Balance Sheet Accounts" in t and "Select Transactions" in t and "of 3 Areas" in t and "without questions yet" not in t, t[:200])
        if page == "drill.html":
            check(tag + " More list starts with the journal entry drill", pg.locator("#ls .row b").first.inner_text() == "Journal entry drill")
        shot(pg, tag, name)
    pg.goto(BASE + "je.html")
    pg.wait_for_timeout(1200)
    check(tag + " journal entry drill opens", "Journal" in pg.inner_text("body"), pg.inner_text("body")[:80])
    shot(pg, tag, "12_je")
    ctx.close()


def part_b(br, tag, viewport, mobile):
    ctx, pg = new_page(br, viewport, mobile, tag + "-B")
    goal = (datetime.date.today() + datetime.timedelta(days=40)).isoformat()
    pg.goto(BASE + "index.html?nostart")
    pg.evaluate("""g => {
      localStorage.setItem("te.pref.v1", JSON.stringify({exam:"cpa",onboarded:"x",subs:CATALOG.subsOf("cpa"),cur:"reg_area4_individuals",goal:g,goalMark:true,goalMine:true,hours:10,
        place:{at:1700000000000,n:20,ok:12,per:{IV:{n:5,ok:2}},weakArea:"IV"}}));
      localStorage.setItem("te.reg_area4_individuals.v1", JSON.stringify({ans:{"REG-IV-A-0001":{n:1,ok:true,box:1,at:1700000000000,due:1},"REG-IV-A-0002":{n:1,ok:false,box:0,at:1700000000000,due:1}},days:{"2026-09-01":{n:2,ok:1,ms:1000}},pairs:{},flags:{},wlog:[],notes:{},cards:{}}));
    }""", goal)
    pg.goto(BASE + "index.html?nostart")
    pg.wait_for_selector("#todo")
    d0 = pg.inner_text("#ed")
    body = pg.inner_text("body")
    check(tag + " REG home: switch shows REG selected", pg.locator("#secs a.on").inner_text() == "REG")
    check(tag + " REG home: TBS and concept cards kept, no direct drill link", "Task-based simulations" in body and "Concept cards" in body and pg.locator('#alt a[href="je.html"]').count() == 0)
    check(tag + " REG home: FAR switch note in place of the drill", "FAR section → switch to FAR" in body)
    shot(pg, tag, "20_reg_home_before")
    pg.click('#secs a[data-x="cpa_far"]')
    pg.wait_for_selector("#scr")
    check(tag + " first switch to FAR opens the test date step", "step=date" in pg.url and "Test date" in pg.inner_text("#scr"), pg.url)
    check(tag + " FAR starts without the REG test date", pg.evaluate("() => GB.goalMark()") == "default")
    pg.click("#later"); pg.click('#op button[data-v="15"]')
    pg.wait_for_selector("#oxb", timeout=20000)
    pg.click("#sk"); pg.click("#sk")                          # skip twice: armed, then confirmed
    pg.wait_for_selector("#n", timeout=8000)
    pg.click("#n")
    pg.wait_for_selector("#todo")
    check(tag + " FAR home after switch", pg.locator("#secs a.on").inner_text() == "FAR" and "Test date not set" in pg.inner_text("#ed"), pg.inner_text("#ed"))
    pref = pg.evaluate("() => JSON.parse(localStorage.getItem('te.pref.v1'))")
    check(tag + " REG settings parked under sec.cpa", pref.get("sec", {}).get("cpa", {}).get("hours") == 10 and pref["sec"]["cpa"].get("place", {}).get("n") == 20, json.dumps(pref.get("sec"))[:160])
    check(tag + " REG history key untouched", pg.evaluate("() => Object.keys(JSON.parse(localStorage.getItem('te.reg_area4_individuals.v1')).ans).length") == 2)
    pg.click('#secs a[data-x="cpa"]')
    pg.wait_for_selector("#todo")
    check(tag + " back on REG (no setup screen)", pg.url.endswith("index.html") and pg.locator("#secs a.on").inner_text() == "REG", pg.url)
    check(tag + " REG test date kept", pg.inner_text("#ed") == d0, (d0, pg.inner_text("#ed")))
    pref = pg.evaluate("() => JSON.parse(localStorage.getItem('te.pref.v1'))")
    check(tag + " REG hours, placement and Area restored", pref.get("hours") == 10 and pref.get("place", {}).get("n") == 20 and pref.get("cur") == "reg_area4_individuals", json.dumps({k: pref.get(k) for k in ("hours", "cur")}))
    check(tag + " REG answers still counted", pg.evaluate("() => GB.readiness().n") == 2, pg.evaluate("() => GB.readiness().n"))
    check(tag + " REG Area chips unchanged (5 Areas)", pg.locator("#subs a").count() == 5)
    shot(pg, tag, "21_reg_home_after")
    pg.goto(BASE + "exam.html?nostart")
    pg.wait_for_selector("#go:not([disabled])", timeout=15000)
    check(tag + " REG mock exam still draws 5 Areas", "questions in 5 Areas" in pg.inner_text("#note"), pg.inner_text("#note")[-70:])
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
